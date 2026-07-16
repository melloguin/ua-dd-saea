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

Módulo **stdlib puro**. Escrita append linha-a-linha com flush (stream de
auditoria; um crash deixa no máximo a última linha parcial, tolerada na
leitura). A prontidão do run é decidida pelo **manifesto** (D58), não por este
log.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from src import naming


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
    """

    def __init__(self, path: str, *, append: bool = True) -> None:
        self.path = path
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        self._fh = open(path, "a" if append else "w", encoding="utf-8", buffering=1)
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
        self._fh.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")

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
            self._fh.flush()
            self._fh.close()
            self._closed = True

    def __enter__(self) -> "AuditLogger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
