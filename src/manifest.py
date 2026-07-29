"""Manifesto por run + esteira idempotente + placar de console.

Um **fragmento de manifesto por run** (`{base}.manifest.json`, D58) — zero lock,
zero corrida: cada task grava o seu. É a fonte-de-verdade do resume (§19):
o despachante pula uma célula cujo run está **pronto** (D58: manifesto ok **E**
as camadas presentes **E** footers válidos).

Campos do manifesto (§17.2 / §17.6 / §17.7 / D23 / D55):
  identidade   run_id, exp, alg, problema, semente, regime, q, tier, dist
  execução     status {ok|retried_ok|failed}, n_retries, stack_trace, timestamp
  orçamento    maxFE, fe_final (D21/D89), n_geracoes
  reprodutib.  doe_hash (SHA256 do array decodificado — D87/D88), repo_hash,
               algo_version, env (libs+versões — D80/N.4)
  tempo        timing {tempo_total_s, fit_surrogate_s, busca_s, aval_real_s},
               fit_series [{iter, n_acumulado, tempo_fit_s}] (§17.6)
  persistência paths {local:{...}, bucket:{...}}, upload_status (§17.7)

Módulo **stdlib puro**. A escrita é atômica (D58, via `src.atomic_io`); a
leitura de footer de parquet (validação profunda) é **opcional** — se o
`pyarrow` não estiver no interpretador, a checagem de footer é pulada com nota
(o encanamento não depende dela para o F0-01, que não gera parquets).
"""

from __future__ import annotations

import functools
import json
import os
import subprocess
from datetime import datetime, timezone

from src import naming
from src.atomic_io import atomic_write_text
from src.audit_log import footer_fechado

#: Status de um run (D23). `failed` = qualquer parada anômala (nunca silenciosa).
STATUSES: tuple[str, ...] = ("ok", "retried_ok", "failed")

#: Versão do schema do manifesto. **v2 = com `campanha_id`** (B-03) — a migração
#: é de WRITE PATH (todo ⑤ novo nasce v2), nunca retroativa em massa: um ⑤ v1 é
#: legível como sempre, só não conta como pronto para a campanha corrente.
MANIFEST_SCHEMA_VERSION = 2

#: [B-03] Variável de ambiente que CRAVA a identidade da campanha. É a forma
#: NORMATIVA de usar o campo: a campanha das 30 sementes leva ~21 dias em 4
#: máquinas, então o default derivado da data (abaixo) mudaria de valor no meio
#: e faria o resume re-rodar tudo. O driver de lote exporta uma vez:
#:     export UA_DD_SAEA_CAMPANHA_ID="$(git rev-parse --short=12 HEAD)_2026-08-01"
#: Os dois stacks leem a MESMA variável (o writer MATLAB em
#: `src/experiment.m:build_manifest`).
CAMPANHA_ENV: str = "UA_DD_SAEA_CAMPANHA_ID"

#: [B-03] Sentinela para quem AUDITA o passado em vez de decidir re-run: o
#: re-gate das 666 células da rodada-42 lê manifestos v1 (sem carimbo), e exigir
#: a campanha corrente ali pintaria o grid inteiro de "não-pronto".
QUALQUER_CAMPANHA: str = "*"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@functools.lru_cache(maxsize=1)
def _repo_hash_curto() -> str:
    """`git rev-parse --short=12 HEAD` (1× por processo; 'sem-git' se falhar)."""
    try:
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out = subprocess.run(['git', 'rev-parse', '--short=12', 'HEAD'],
                             cwd=raiz, capture_output=True, text=True, timeout=10)
        h = out.stdout.strip()
        return h if out.returncode == 0 and h else 'sem-git'
    except (OSError, subprocess.SubprocessError):
        return 'sem-git'


def campanha_id_corrente() -> str:
    """[B-03] A identidade da campanha CORRENTE: `{commit12}_{data}` ou a env.

    Sem este carimbo, `is_run_done` não distinguia uma célula da campanha de uma
    célula de SMOKE ou PRÉ-RETROFIT: as stale de semente **0** (b1 DTLZ2/ZDT1,
    c238 ZDT1, c262 ZDT1, c154 DTLZ2) eram absorvidas como prontas — e a semente
    0 é uma das 30. Medido na rodada-42: 22 células "pulou" únicas nos
    `done.txt`, 9 delas ZDT4.

    A env `CAMPANHA_ENV` tem precedência (é o modo normativo). O default só
    serve para smoke/desenvolvimento — ele MUDA de valor à meia-noite UTC.
    """
    v = os.environ.get(CAMPANHA_ENV, '').strip()
    return v or f"{_repo_hash_curto()}_{datetime.now(timezone.utc):%Y-%m-%d}"


def new_manifest(exp: str, alg: str, problema: str, semente,
                 *, regime: str | None = None, q: int = 1,
                 tier: str | None = None, dist: str | None = None,
                 status: str = "failed", n_retries: int = 0,
                 maxfe: int | None = None, fe_final: int | None = None,
                 n_geracoes: int | None = None,
                 doe_hash: str | None = None, repo_hash: str | None = None,
                 algo_version: str | None = None,
                 env: dict | None = None,
                 timing: dict | None = None, fit_series: list | None = None,
                 stack_trace: str | None = None,
                 fallback_ativado: bool = False,
                 campanha_id: str | None = None,
                 data_root: str = naming.DEFAULT_DATA_ROOT,
                 bucket: str | None = None) -> dict:
    """Constrói o dicionário de manifesto de um run.

    `status` default = 'failed' (D23/D60: o run só vira 'ok' quando fecha
    limpo; assim uma parada abrupta que nunca reescreve o manifesto NÃO é lida
    como sucesso). `bucket` = nome do bucket GCS quando há espelho (Python);
    `None` no MATLAB (só local — §17.7).
    """
    if status not in STATUSES:
        raise ValueError(f"status inválido: {status!r}. Esperado {STATUSES}.")
    rid = naming.run_id(exp, alg, problema, semente)

    local = {ly: naming.layer_path(exp, alg, problema, semente, ly, data_root)
             for ly in naming.LAYERS}
    local["jsonl"] = naming.jsonl_path(exp, alg, problema, semente, data_root)
    local["manifest"] = naming.manifest_path(exp, alg, problema, semente, data_root)

    if bucket is not None:
        bk = {ly: f"gs://{bucket}/"
                  + naming.blob_path(exp, alg,
                                     naming.layer_filename(exp, alg, problema, semente, ly))
              for ly in naming.LAYERS}
        bk["jsonl"] = (f"gs://{bucket}/"
                       + naming.blob_path(exp, alg,
                                          naming.jsonl_filename(exp, alg, problema, semente)))
        upload_status = {k: "pending" for k in bk}
    else:
        bk = None
        upload_status = None

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        # [B-03] o carimbo da campanha nasce com o ⑤ (write path) — quem
        # re-executa a célula reescreve o ⑤ e o carimbo se atualiza sozinho.
        "campanha_id": campanha_id or campanha_id_corrente(),
        "run_id": rid,
        "exp": exp, "alg": alg, "problema": problema, "semente": semente,
        "regime": regime, "q": q, "tier": tier, "dist": dist,
        "status": status, "n_retries": n_retries, "stack_trace": stack_trace,
        "maxfe": maxfe, "fe_final": fe_final, "n_geracoes": n_geracoes,
        "doe_hash": doe_hash, "repo_hash": repo_hash, "algo_version": algo_version,
        "env": env or {},
        "timing": timing or {
            "tempo_total_s": None, "tempo_fit_surrogate_s": None,
            "tempo_busca_s": None, "tempo_aval_real_s": None,
        },
        "fit_series": fit_series or [],           # §17.6 (cópia leve; ③ canônica em __timing)
        "fallback_ativado": fallback_ativado,     # D78
        "paths": {"local": local, "bucket": bk},
        "upload_status": upload_status,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }


def write_manifest(manifest: dict,
                   data_root: str = naming.DEFAULT_DATA_ROOT) -> str:
    """Grava o fragmento de manifesto atomicamente. Retorna o caminho."""
    path = naming.manifest_path(
        manifest["exp"], manifest["alg"],
        manifest["problema"], manifest["semente"], data_root)
    manifest["updated_at"] = _utcnow_iso()
    atomic_write_text(path, json.dumps(manifest, ensure_ascii=False, indent=2))
    return path


def read_manifest(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _footer_ok(path: str) -> bool | None:
    """Parquet legível com footer válido? None se `pyarrow` ausente (skip)."""
    try:
        import pyarrow.parquet as pq  # noqa: WPS433 (import local proposital)
    except ImportError:
        return None
    try:
        pq.ParquetFile(path).metadata  # lê o footer
        return True
    except Exception:
        return False


def is_run_done(exp: str, alg: str, problema: str, semente,
                data_root: str = naming.DEFAULT_DATA_ROOT,
                *, check_footers: bool = True,
                campanha_id: str | None = None) -> bool:
    """Esteira idempotente (D58): o run está **pronto**?

    Pronto = fragmento de manifesto presente **E** **o `campanha_id` é o da
    campanha corrente (B-03)** **E** status ∈ {ok, retried_ok} **E**
    `fe_final == maxfe` (D21/D61) **E** as camadas parquet presentes **E**
    (quando `pyarrow` disponível e `check_footers`) footers válidos. Qualquer
    peça faltando ⇒ re-roda.

    **[B-03]** Manifesto **v1** (sem o campo) ou de campanha ANTERIOR ⇒ `False`
    — e isso é o comportamento DESEJADO, não um efeito colateral: é o que impede
    uma célula de smoke ou pré-retrofit de entrar como resultado oficial. Passe
    `campanha_id` explícito para perguntar por outra campanha, ou
    `QUALQUER_CAMPANHA` para auditar o passado (o re-gate das 666).

    **[DI-13.3 · rede de segurança]** A checagem de `fe_final == maxfe` é NOVA.
    Sem ela, um run **abortado pelo teto de tempo** (que não chega a gravar
    `status='failed'`) convivendo com artefatos de uma execução ANTERIOR no
    disco seria lido como PRONTO — um run truncado entraria na bateria como se
    fosse completo, em silêncio. A raiz (o aborto gravar `failed`) é o item (a)
    da DI-13.3; esta é a rede independente do motivo da parada.
    """
    mpath = naming.manifest_path(exp, alg, problema, semente, data_root)
    man = read_manifest(mpath)
    if man is None or man.get("status") not in ("ok", "retried_ok"):
        return False
    # [B-03] antes de qualquer I/O de camada: o carimbo de campanha é O(1).
    if campanha_id != QUALQUER_CAMPANHA and \
            man.get("campanha_id") != (campanha_id or campanha_id_corrente()):
        return False
    # [DI-13.3] o orçamento tem de ter fechado EXATO (hard-stop D21/D61).
    fe_final, maxfe = man.get("fe_final"), man.get("maxfe")
    if fe_final is not None and maxfe is not None and int(fe_final) != int(maxfe):
        return False
    # [D-12/DI-21] os 5 configs OFFLINE também precisam da ⑦ `__final` — é a
    # ÚNICA avaliação real do ND final (§11) e a VM que a segura é efêmera. Sem
    # esta linha, um run offline SEM a ⑦ contava como pronto, a esteira não a
    # gerava, e o dado se perdia sem sintoma (achado A3 da auditoria DI-20).
    camadas = naming.LAYERS + ((naming.FINAL_LAYER,)
                               if alg in OFFLINE_ALGS else ())
    for ly in camadas:
        p = naming.layer_path(exp, alg, problema, semente, ly, data_root)
        if not os.path.exists(p):
            # [D-03/DI-21] resume BUCKET-AWARE: a ③ dos 5 volumosos é podada
            # localmente após o upload (D58/gcs.mirror_run) — na VM, o run
            # completo ficaria "não pronto" PARA SEMPRE e re-executaria os 5
            # configs mais caros do estudo. A D58 já prometia "resume dos
            # bucket-only LISTA O BUCKET"; esta é a promessa cumprida. No Mac
            # (sem lib gcs / sem rede) o fallback falha FECHADO ⇒ False.
            if _bucket_has(exp, alg, problema, semente, ly):
                continue
            return False
        if check_footers and _footer_ok(p) is False:
            return False
    return True


def certidao_do_run(exp: str, alg: str, problema: str, semente,
                    data_root: str = naming.DEFAULT_DATA_ROOT) -> dict | None:
    """A certidão de fim do run, com **fallback para o footer do ⑥** [O-21/E-04].

    O stack MATLAB certifica a própria falha no FOOTER DO ⑥, não no ⑤:
    `main/b1/DTLZ4` fechou com `least squares problem is underdetermined` lá e
    em lugar nenhum mais. Todo verificador que olha só a camada ⑤ (`is_run_done`,
    `censo_bucket.py`, o rito de fechamento por máquina) classifica a célula como
    **SEM-MANIFESTO** e perde o diagnóstico, que está a um `tail` de distância.

    Devolve `{'fonte', 'status', 'fe_final', 'motivo', 'campanha_id', 'raw'}` —
    `fonte ∈ {'manifesto', 'footer_jsonl'}` — ou `None` quando não há nem ⑤ nem
    footer de fechamento (aí sim: a célula não deixou certidão nenhuma).

    ⚠ O campo de término é HETEROGÊNEO por config (`motivo_parada` no ⑤ de
    c122/c149/e81/b5 · `footer.termino` nos 13 MATLAB + e7/e74/nsga3/smsemoa ·
    `footer.motivo` no c311 · `footer.hard_stopped` em c154/c262 — I-08); aqui
    devolve-se o PRIMEIRO não-nulo, e o mapa normativo é o
    `artifacts/mapa_termino.json`.
    """
    man = read_manifest(naming.manifest_path(exp, alg, problema, semente, data_root))
    if man is not None:
        return {'fonte': 'manifesto', 'status': man.get('status'),
                'fe_final': man.get('fe_final'),
                'motivo': _primeiro_motivo(man),
                'campanha_id': man.get('campanha_id'), 'raw': man}
    rec = footer_fechado(naming.jsonl_path(exp, alg, problema, semente, data_root))
    if rec is None:
        return None
    return {'fonte': 'footer_jsonl', 'status': rec.get('status'),
            'fe_final': rec.get('fe_final'), 'motivo': _primeiro_motivo(rec),
            'campanha_id': rec.get('campanha_id'), 'raw': rec}


def _primeiro_motivo(d: dict):
    for k in ('motivo_parada', 'motivo', 'erro', 'termino'):
        v = d.get(k)
        if v not in (None, ''):
            return v
    return None


def limpar_celula(exp: str, alg: str, problema: str, semente,
                  data_root: str = naming.DEFAULT_DATA_ROOT,
                  *, dry_run: bool = False) -> list[str]:
    """[OP-6] Remove os artefatos LOCAIS da célula ANTES de uma re-execução.

    O `--force` re-rodava POR CIMA: as camadas da execução anterior ficavam no
    disco e, se o run novo morresse antes de reescrever todas, a célula passava a
    ter ①②③④ de UMA execução com o ⑤ de OUTRA — a mecânica exata da quimera
    `batch/c149/q10_ZDT4` (③ do Mac de 24/07 com ①④⑤⑥ da v6 de 26/07).

    Só o disco LOCAL: a cópia do BUCKET é a oficial (D58) e nunca é podada
    daqui. Devolve os caminhos removidos (ou que seriam, em `dry_run`).
    """
    alvos = [naming.layer_path(exp, alg, problema, semente, ly, data_root)
             for ly in naming.LAYERS + (naming.FINAL_LAYER,)]
    alvos.append(naming.jsonl_path(exp, alg, problema, semente, data_root))
    alvos.append(naming.manifest_path(exp, alg, problema, semente, data_root))
    removidos = []
    for p in alvos:
        # proibição absoluta da casa: o baseline pré-retrofit é INTOCÁVEL.
        if '_baseline_pre_retrofit' in p:
            raise RuntimeError(f'recusa de escrita em _baseline_pre_retrofit: {p}')
        if not os.path.exists(p):
            continue
        removidos.append(p)
        if not dry_run:
            os.remove(p)
    return removidos


#: [D-12/DI-21] Os 5 configs do regime OFFLINE (fonte: runs_matrix.csv, exp=off)
#: — os únicos cuja ⑦ `__final` é OBRIGATÓRIA no `is_run_done`.
OFFLINE_ALGS: frozenset[str] = frozenset({"e103", "b5r", "b5m", "c311", "treed_media",
                                          "moead_media"})


def _bucket_has(exp: str, alg: str, problema: str, semente, layer: str) -> bool:
    """[D-03/DI-21] A camada `layer` deste run existe no BUCKET? Falha FECHADA:
    qualquer impossibilidade (camada não é bucket-only p/ este alg, lib gcs
    ausente no Mac, rede fora) responde False — nunca um falso 'pronto'."""
    try:
        from src import gcs
        if not gcs.is_bucket_only(alg, layer):
            return False
        fname = naming.layer_filename(exp, alg, problema, semente, layer)
        return bool(gcs.blob_exists(naming.blob_path(exp, alg, fname)))
    except Exception:
        return False


# ── Placar de console corrido (D23 / §17.5) ────────────────────────────────

class Scoreboard:
    """Contagem acumulada de sucessos × falhas, impressa em tempo real.

    O despachante alimenta com o `status` de cada run concluído; o placar dá
    ao operador (e ao Claude, na leitura do console) a saúde da bateria sem
    esperar a análise. `skipped` = células puladas pela esteira (já prontas).
    """

    def __init__(self) -> None:
        self.counts = {s: 0 for s in STATUSES}
        self.skipped = 0
        self.total = 0

    def record(self, status: str) -> None:
        if status not in STATUSES:
            raise ValueError(f"status inválido: {status!r}")
        self.counts[status] += 1
        self.total += 1

    def record_skip(self) -> None:
        self.skipped += 1

    @property
    def ok(self) -> int:
        return self.counts["ok"] + self.counts["retried_ok"]

    @property
    def failed(self) -> int:
        return self.counts["failed"]

    def render(self) -> str:
        c = self.counts
        return (f"[placar] ok={c['ok']} retried_ok={c['retried_ok']} "
                f"failed={c['failed']} skipped={self.skipped} "
                f"| concluídos={self.total}")

    def print(self) -> None:
        print(self.render(), flush=True)
