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

import json
import os
from datetime import datetime, timezone

from src import naming
from src.atomic_io import atomic_write_text

#: Status de um run (D23). `failed` = qualquer parada anômala (nunca silenciosa).
STATUSES: tuple[str, ...] = ("ok", "retried_ok", "failed")

#: Versão do schema do manifesto (para migração futura da análise).
MANIFEST_SCHEMA_VERSION = 1


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
                *, check_footers: bool = True) -> bool:
    """Esteira idempotente (D58): o run está **pronto**?

    Pronto = fragmento de manifesto presente **E** status ∈ {ok, retried_ok}
    **E** `fe_final == maxfe` (D21/D61) **E** as camadas parquet presentes **E**
    (quando `pyarrow` disponível e `check_footers`) footers válidos. Qualquer
    peça faltando ⇒ re-roda.

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
