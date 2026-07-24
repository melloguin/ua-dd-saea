"""Wrapper de FE — a ÚNICA fonte do orçamento nos 2 stacks (D21/D61/D89/D57).

O contrato de orçamento do pipeline vive AQUI (no Python) e no `evalFcn` do
MATLAB (`MException('PlatEMO:Termination')`) — **nunca** no `obj.FE` nativo do
PlatEMO (D89). Toda avaliação da função verdadeira passa pelo `FEBudget`:

- **Conta avaliações reais DISTINTAS por X NATIVO bit-a-bit (D89).** A identidade
  de uma solução é o `x` no espaço nativo, comparado **byte a byte**
  (`np.ascontiguousarray(x, '<f8').tobytes()`). Duas X iguais ao último bit são a
  MESMA solução; uma near-duplicata (difere 1 ULP) é OUTRA (paga 1 FE).
- **Cache-hit = 0 FE (D89 — decisão do autor, CONTRÁRIA à recomendação inicial).**
  Re-consultar um X já avaliado é **gratuito** (como na prática real de otimização
  cara: o catálogo ① torna a re-consulta de graça). O cache-hit é **logado** como
  evento no `.jsonl` (§17.5), mas não move o saldo — nem sob orçamento esgotado.
- **`solution_id` = dedup-por-X (D57).** Cada X distinto ganha um id inteiro
  estável (0-based, na ordem de 1ª avaliação). O cache-hit reusa o id existente.
  É a **chave de join** que liga as 3 camadas (§17.1): ① guarda `x/f` por
  `solution_id`; ② é membership `(geracao, solution_id)`; ③ aponta o
  `real_solution_id` quando o candidato foi mesmo avaliado.
- **Hard-stop EXATO em `31D−1` (D21/D61).** O saldo permite exatamente `31D−1`
  avaliações distintas; a `31D`-ésima X **inédita** levanta `BudgetExhausted` no
  ponto único de avaliação → o adapter captura e encerra o run com FE final =
  `31D−1` cravado. (Um cache-hit após o esgotamento continua livre — não é uma
  avaliação nova.)

O `FEBudget` também **acumula o catálogo ①** (as soluções reais distintas) em
**float64** — o dado exato que foi avaliado. A camada ① fica em float32 no
Parquet (D53, `src/export.py`), mas o **hash do CP-init** (`doe_hash` no manifesto
— D87/D88) é computado do array float64 de `init_X()` (as `11D−1` primeiras X, a
fase `init` = o DoE), então bate bit-a-bit com o sidecar float64 do DoE.

Módulo **numpy-dependente** (roda no env-main; import lazy do numpy no topo é ok
porque o wrapper de FE só existe dentro de um run já no env pesado).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


class BudgetExhausted(Exception):
    """Levantada quando uma X INÉDITA é avaliada com o saldo já zerado (D21/D61).

    É o hard-stop exato: o adapter de cada rodada captura esta exceção no ponto
    único de avaliação para encerrar o run com FE final = `31D−1` cravado. O
    espelho no MATLAB é `MException('PlatEMO:Termination')`.
    """

    def __init__(self, maxfe: int):
        self.maxfe = maxfe
        super().__init__(f"orçamento esgotado: {maxfe} avaliações reais distintas "
                         f"consumidas (hard-stop D21/D61).")


@dataclass
class RealEval:
    """Uma linha do Catálogo REAL ① (§17.2) — uma solução real distinta.

    `x`/`f` ficam em **float64** (o valor exato avaliado); a downconversão a
    float32 (D53) é feita só na escrita do Parquet (`src/export.py`).
    """
    solution_id: int
    x: np.ndarray          # (D,) float64 — nativo, exatamente como avaliado
    f: np.ndarray          # (M,) float64 — fitness verdadeira
    fe_index: int          # ordinal da avaliação (0-based)
    fase: str              # 'init' (ponto do DoE) | 'opt' (infill da busca)


def maxfe_for(D: int) -> int:
    """`maxFE = 31D−1` (D21) — o orçamento do experimento PRINCIPAL."""
    return 31 * int(D) - 1


def n_init_for(D: int) -> int:
    """Tamanho do DoE inicial `11D−1` (§5.2/D87)."""
    return 11 * int(D) - 1


#: [T6-batch] Nº de iterações de LOTE do sub-estudo batch (D66/§6). Com q=10 dá
#: os 2.000 infills do contrato. Constante nomeada para o número não virar
#: literal solto em runner/gate.
K_BATCH: int = 200

#: [DI-34] O q CANÔNICO do sub-estudo batch (D66). Fonte ÚNICA do despachante:
#: a auditoria final da torre reproduziu que sem este fio uma célula batch
#: despachada pela bateria rodava SILENCIOSAMENTE em q=1 (FE=11D−1+200, gates
#: passando porque liam o q=1 do próprio manifesto) — o 3º bug da mesma família
#: da camada de lançamento (roster DI-31, transporte E1/T7).
Q_BATCH: int = 10


def maxfe_por_exp(exp: str, D: int, q: int = 1) -> int:
    """[T6-batch] Orçamento de FE por EXPERIMENTO — a fonte única (D66).

    - `main` (e qualquer token não-batch online) ⇒ **31D−1** (D21), inalterado.
    - `batch` ⇒ **11D−1 + K·q** com **K=200** (D66/§6/SPEC:831): o **MESMO DoE
      pareado do principal** (`11D−1`, nunca regenerado) + 2.000 infills de lote.
    - `off` / `sweep-*` ⇒ **NÃO passam por aqui**: no offline "o orçamento É o
      dataset" (D90) e o `maxfe` nasce do `n` lido do artefato
      (`load_offline_budget`). Chamar esta função para um exp offline é erro de
      uso — ela levanta, em vez de devolver um 31D−1 que ninguém deveria usar.

    O `q` só entra no ramo `batch`; nos demais é ignorado (o principal é q=1 por
    construção — D41/§6).
    """
    from src import naming
    D = int(D)
    if exp == "batch":
        return n_init_for(D) + K_BATCH * int(q)
    tier, _ = naming.parse_sweep(exp)
    if exp == "off" or tier is not None:
        raise ValueError(
            f"maxfe_por_exp não se aplica a exp={exp!r}: no regime OFFLINE o "
            f"orçamento É o dataset (D90) e vem do artefato, não de fórmula. "
            f"Use load_offline_budget(). Pára-e-loga (D81).")
    return maxfe_for(D)


@dataclass
class FEBudget:
    """Wrapper de FE: orçamento + dedup-por-X + catálogo ① (D89/D57/D21).

    Uso típico (dentro do adapter de uma rodada)::

        bud = FEBudget(D=prob.n_var, logger=audit_log)
        # 1) injeta o DoE (fase init) — 11D−1 avaliações distintas:
        for x in doe_X:
            f = bud.evaluate(x, true_f)      # fase inferida por fe_index
        # 2) busca (fase opt) até estourar:
        try:
            while True:
                x = algoritmo.propor()
                f = bud.evaluate(x, true_f)  # levanta BudgetExhausted em 31D−1
        except BudgetExhausted:
            pass                              # encerra limpo (FE = 31D−1 exato)

    `evaluate` chama `true_f(x) -> (M,)` só quando o X é INÉDITO; num cache-hit
    devolve a fitness memorizada (0 FE) e loga o evento.
    """

    D: int
    maxfe: int = field(default=None)          # type: ignore[assignment]
    n_init: int = field(default=None)         # type: ignore[assignment]
    logger: object | None = None              # AuditLogger (§17.5) — opcional

    # estado interno
    _by_key: dict[bytes, int] = field(default_factory=dict, init=False)
    _records: list[RealEval] = field(default_factory=list, init=False)
    _fe: int = field(default=0, init=False)
    _cache_hits: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.D = int(self.D)
        if self.maxfe is None:
            self.maxfe = maxfe_for(self.D)
        if self.n_init is None:
            self.n_init = n_init_for(self.D)

    # ── chave de identidade (X nativo bit-a-bit, D89) ──────────────────────
    @staticmethod
    def _key(x: np.ndarray) -> bytes:
        """Bytes canônicos do X nativo: `<f8` contíguo, row-major (D89)."""
        return np.ascontiguousarray(np.asarray(x, dtype="<f8").reshape(-1)).tobytes()

    # ── propriedades ───────────────────────────────────────────────────────
    @property
    def fe(self) -> int:
        """Saldo consumido = nº de avaliações reais DISTINTAS (D89)."""
        return self._fe

    @property
    def remaining(self) -> int:
        return self.maxfe - self._fe

    @property
    def exhausted(self) -> bool:
        return self._fe >= self.maxfe

    @property
    def cache_hits(self) -> int:
        return self._cache_hits

    @property
    def records(self) -> list[RealEval]:
        """As linhas do Catálogo REAL ① (ordem de 1ª avaliação = fe_index)."""
        return self._records

    # ── avaliação (o ponto único de orçamento) ─────────────────────────────
    def _fase(self, fe_index: int) -> str:
        # As `11D−1` primeiras distintas = DoE (init); o resto = infill (opt).
        return "init" if fe_index < self.n_init else "opt"

    def evaluate(self, x: np.ndarray, true_f) -> np.ndarray:
        """Avalia `x` sob o orçamento. Cache-hit = 0 FE (D89); X inédita = 1 FE;
        a `31D`-ésima X inédita levanta `BudgetExhausted` (hard-stop, D21).

        `true_f(x) -> (M,)` só é chamado quando `x` é inédito. Devolve `f`
        (float64) — a fitness verdadeira (memorizada em cache-hit)."""
        x = np.asarray(x, dtype=np.float64).reshape(-1)
        if x.shape[0] != self.D:
            raise ValueError(f"x tem dim {x.shape[0]} != D={self.D}")
        key = self._key(x)

        sid = self._by_key.get(key)
        if sid is not None:
            # Cache-hit: 0 FE (D89). Livre mesmo com o saldo esgotado.
            self._cache_hits += 1
            if self.logger is not None:
                self.logger.guard("cache_hit", solution_id=sid,
                                  x_key=key.hex()[:16], fe=self._fe)  # D89 (evento)
            return self._records[sid].f

        # X inédita → 1 FE. Hard-stop EXATO antes de consumir (D21/D61).
        if self._fe >= self.maxfe:
            if self.logger is not None:
                self.logger.guard("hard_stop", fe=self._fe, maxfe=self.maxfe,
                                  x_key=key.hex()[:16])                # A2 (evento)
            raise BudgetExhausted(self.maxfe)

        f = np.asarray(true_f(x), dtype=np.float64).reshape(-1)
        fe_index = self._fe
        rec = RealEval(solution_id=fe_index, x=x.copy(), f=f.copy(),
                       fe_index=fe_index, fase=self._fase(fe_index))
        self._by_key[key] = fe_index
        self._records.append(rec)
        self._fe += 1
        return f

    # ── suporte ao export/manifesto ────────────────────────────────────────
    def solution_id_of(self, x: np.ndarray) -> int | None:
        """`solution_id` de um X já avaliado (ou None) — p/ montar ②③ sem
        reavaliar (o candidato surrogate que virou infill aponta o id)."""
        return self._by_key.get(self._key(x))

    def init_X(self) -> np.ndarray:
        """As `11D−1` primeiras X distintas (fase `init` = o DoE), em **float64**
        e na ordem de avaliação. Fonte do `doe_hash` do CP-init (D87/D88): seu
        hash bate com o sidecar float64 do DoE, apesar de a ① ir em float32."""
        init = [r.x for r in self._records if r.fase == "init"]
        if not init:
            return np.empty((0, self.D), dtype=np.float64)
        return np.ascontiguousarray(np.vstack(init), dtype=np.float64)

    def n_geracoes_hint(self) -> int:
        """(informativo) nº de avaliações opt — o adapter costuma reportar o nº
        real de gerações; aqui é só um piso trivial p/ manifestos de STUB."""
        return sum(1 for r in self._records if r.fase == "opt")
