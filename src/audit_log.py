"""Log de auditoria de execução por run — `.jsonl` (§17.5 / D18 / D97).

Uma **decisão/evento por linha** (JSON), texto puro greppável. É instrumento de
**QA/fidelidade**: durante o piloto (verbosidade máxima) o autor lê o `.jsonl`
com o Claude e percorre o checklist §17.5.1; na bateria captura parciais/flags
para detecção precoce. **NÃO é fonte de métrica** (as métricas oficiais saem da
camada ① — §12).

⚠ **D97 (limite de escopo):** o log é **gravado em runtime** (as decisões
internas do algoritmo são irrecuperáveis depois), mas a **validação de
fidelidade a partir dele é MANUAL, do autor, a posteriori** — este módulo só
*instrumenta*; não julga fidelidade, não é gate.

Mínimo comum a TODOS os algoritmos (§17.5). Os campos finos por algoritmo
(S.7 / DEF-C5) entram como `**extra` nas chamadas — cada rodada preenche os
seus. O logger é agnóstico ao algoritmo.

Módulo **stdlib puro**. Escrita linha-a-linha SEM buffer de usuário: 1 linha =
1 `os.write` sob `O_APPEND` (B-11), porque o ⑥ tem mais de um escritor por
célula (o despachante + o harness MATLAB/runner) e o formato
**1-JSON-por-linha** é contrato (§17.5 / gate G-2). A prontidão do run é
decidida pelo **manifesto** (D58), não por este log.
"""

from __future__ import annotations

import json
import os
import select
from datetime import datetime, timezone

from src import naming

try:                       # POSIX (Mac + Linux — os únicos alvos do estudo)
    import fcntl
except ImportError:        # pragma: no cover
    fcntl = None


#: [B-11] Teto de linha cujo append o SO garante atômico (`select.PIPE_BUF`:
#: 4096 no Linux, 512 no macOS). Acima dele a escrita é serializada por `flock`.
#: A faixa é grande: no ⑥ de `main/b1/WFG1` (o das 49 linhas spliced) **421 das
#: 931 linhas passam de 512 B**, e a maior linha medida no corpus da rodada-42 é
#: o `header` de `batch/e81/q10_ZDT4` com **6.761 B**.
#: ⚠ ERRATA ao PLANO F5/B-11: ele afirma que o splice ocorreu "nas linhas de
#: header/sigma_dict"; o dado diz outra coisa — o `header` do b1/WFG1 tem 512 B e
#: as 49 malformadas são `b1_gen`/`sonda` (mediana 1.647 B, máx 10.522 B) com um
#: `guard` de ts POSTERIOR sobrescrito no meio. Dois deslocamentos de escrita
#: independentes sobre o mesmo ⑥, não uma linha grande partida.
LIMITE_ATOMICO_B: int = getattr(select, "PIPE_BUF", 4096)


class RunJaFechado(RuntimeError):
    """[B-01] O ⑥ da célula já traz footer de fechamento (`fe_final` não-nulo).

    Reabrir em append empilharia pares header/footer sobre a certidão de um run
    encerrado: foi assim que `batch/e81/q10_ZDT4` acumulou **94 pares
    espúrios** (747→767 linhas, todos com `D`/`maxfe`/`params`/`sigma_dict`
    NULL) e que 34 das 666 células da rodada-42 ficaram com a auditoria de
    término indecidível — todo consumidor que lê o ÚLTIMO footer
    (`scripts/progress.py:95`, `scripts/accept.py:794`) é enganado por eles.
    Quem de fato vai RE-EXECUTAR a célula abre com `append=False`: o dono do
    arquivo o trunca (rito dos runners e do harness MATLAB).
    """


def footer_fechado(path: str) -> dict | None:
    """O primeiro `footer` com `fe_final` não-nulo do ⑥ em `path` (ou `None`).

    É o discriminador do B-01: `fe_final` só é gravado por quem contabilizou o
    orçamento — o RUNNER, ou o harness MATLAB no footer do ⑥ (O-21) —, nunca
    pelo footer do despachante, e é NULL nos pares espúrios do append cego.
    Linhas malformadas (splice, cauda de crash) são ignoradas: leitura tolerante
    é regra da casa (§17.5). O pré-filtro por substring evita `json.loads` nas
    ~200 mil linhas de evento de um ⑥ grande.
    """
    try:
        with open(path, "rb") as fh:
            for raw in fh:
                if b'"footer"' not in raw:
                    continue
                try:
                    rec = json.loads(raw.decode("utf-8", "replace"))
                except ValueError:
                    continue
                if isinstance(rec, dict) and rec.get("rec") == "footer" \
                        and rec.get("fe_final") is not None:
                    return rec
    except FileNotFoundError:
        return None
    return None


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class AuditLogger:
    """Escreve o `.jsonl` de auditoria de um run (§17.5).

    Use como context manager para garantir o `close()`:

        with AuditLogger.for_run("main", "c217", "DTLZ2", 0) as log:
            log.header(D=15, M=3, maxfe=464, doe_hash="…", env={...})
            log.decision(caminho="estado_1", motivo="p_mais=0.86 > delta=0.80")
            log.partial(fe_index=120, nd_size=14)
            log.guard("cache_hit", x_hash="…")          # D89 (evento)
            log.footer(status="ok", fe_final=464, n_geracoes=37)

    `append=True` (default) é para quem ACRESCENTA a um run em andamento e
    levanta `RunJaFechado` se o ⑥ já estiver fechado (B-01); `append=False` é o
    rito de quem EXECUTA a célula — trunca e assume a autoria do arquivo.
    """

    def __init__(self, path: str, *, append: bool = True) -> None:
        self.path = path
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        if append:
            # [B-01] append CEGO era o default: reabrir um run fechado é sempre
            # poluição (nunca há razão para acrescentar linhas a um run que já
            # certificou o próprio fim).
            fechado = footer_fechado(path)
            if fechado is not None:
                raise RunJaFechado(
                    f"{path}: footer de fechamento preexistente "
                    f"(status={fechado.get('status')!r}, "
                    f"fe_final={fechado.get('fe_final')!r}) — "
                    f"re-execução legítima abre com append=False.")
        # [B-11] O_APPEND em TODA abertura + zero buffer de usuário: o
        # deslocamento é resolvido pelo kernel DENTRO do próprio `os.write`, de
        # modo que dois escritores no mesmo ⑥ (o despachante e o harness, ou
        # dois processos da mesma célula) não podem mais sobrescrever a linha um
        # do outro. O_TRUNC só quando `append=False` (o dono zera e assume).
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if not append:
            flags |= os.O_TRUNC
        self._fd = os.open(path, flags, 0o644)
        self._closed = False

    # -- construção ---------------------------------------------------------
    @classmethod
    def for_run(cls, exp: str, alg: str, problema: str, semente,
                data_root: str = naming.DEFAULT_DATA_ROOT,
                *, append: bool = True) -> "AuditLogger":
        path = naming.jsonl_path(exp, alg, problema, semente, data_root)
        return cls(path, append=append)

    # -- primitiva ----------------------------------------------------------
    def _write(self, rec: str, payload: dict) -> None:
        if self._closed:
            raise RuntimeError("AuditLogger já fechado.")
        line = {"ts": _utcnow_iso(), "rec": rec, **payload}
        self._emitir(json.dumps(line, ensure_ascii=False, default=str) + "\n")

    def _emitir(self, linha: str) -> None:
        """[B-11] Grava a linha em UM `os.write`.

        Fragmentar está fora de questão (1-JSON-por-linha é contrato §17.5), e
        acima de `LIMITE_ATOMICO_B` o SO não garante mais a atomicidade do
        append — nessas linhas (header/sigma_dict) o acesso é serializado por
        `flock`, que é barato porque são poucas por run.
        """
        b = linha.encode("utf-8")
        if len(b) <= LIMITE_ATOMICO_B or fcntl is None:
            self._write_todo(b)
            return
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        try:
            self._write_todo(b)
        finally:
            fcntl.flock(self._fd, fcntl.LOCK_UN)

    def _write_todo(self, b: bytes) -> None:
        # O 1º `os.write` é o que carrega a garantia de atomicidade. O laço só
        # existe para o caso patológico de escrita curta (EINTR/ENOSPC): perder
        # o resto da linha em silêncio seria pior que a corrida que o laço abre.
        while b:
            n = os.write(self._fd, b)
            if not n:
                raise OSError(f"os.write devolveu 0 bytes no ⑥ {self.path}")
            b = b[n:]

    # -- eventos do §17.5 ---------------------------------------------------
    def header(self, **fields) -> None:
        """Cabeçalho do run: run_id, alg(+versão/hash), problema, D, M, semente,
        regime, maxFE, doe_hash, env(libs+versões), timestamp (§17.5)."""
        self._write("header", fields)

    def decision(self, *, caminho: str, motivo: str | None = None, **extra) -> None:
        """A decisão "qual caminho e por quê" por iteração/geração/infill —
        o cerne da auditoria de mecanismo (§17.5.1#1). `caminho` = o ramo
        tomado (ex.: estado 1/2/3, KFlag, cascata 1/2/3); `motivo` = a
        desigualdade/condição que disparou. `**extra` = campos S.7."""
        self._write("decision", {"caminho": caminho, "motivo": motivo, **extra})

    def partial(self, **fields) -> None:
        """Resultados parciais: melhor-até-agora por objetivo, |ND| corrente,
        fe_index, IGD/HV parcial quando barato (§17.5)."""
        self._write("partial", fields)

    def guard(self, name: str, **fields) -> None:
        """Uma guarda que disparou: clamp de bounds (A4), NaN-guard,
        Cholesky/PSD, dedup, retry/erro-duro (A8), hard-stop/overshoot (A2),
        **cache-hit bit-a-bit (D89)** — cada guarda LOGA quando dispara
        (§17.5). Alimenta a taxa de disparo por (alg, característica)."""
        self._write("guard", {"name": name, **fields})

    def timing(self, *, n_acumulado: int, tempo_fit_s: float, **extra) -> None:
        """Evento de retreino do surrogate → série `(n_acumulado, tempo_fit_s)`
        (§17.6). Cross-check do `__timing.parquet` (dado de 1ª classe)."""
        self._write("timing", {"n_acumulado": n_acumulado,
                               "tempo_fit_s": tempo_fit_s, **extra})

    def event(self, kind: str, **fields) -> None:
        """Evento genérico (extensível) — para o que não cai nas categorias
        acima sem inventar um `rec` novo às cegas."""
        self._write(kind, fields)

    def footer(self, *, status: str, **fields) -> None:
        """Rodapé: status {ok|retried_ok|failed} + n_retries + stack trace se
        falhou, FE final, nº de gerações, resumo (§17.5/D23). O mesmo status
        vai ao manifesto (§17.2) e ao placar."""
        self._write("footer", {"status": status, **fields})

    # -- ciclo de vida ------------------------------------------------------
    def close(self) -> None:
        if not self._closed:
            os.close(self._fd)     # [B-11] sem flush: `os.write` não passa por
            self._closed = True    # buffer de usuário — nada fica pendente.

    def __enter__(self) -> "AuditLogger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
