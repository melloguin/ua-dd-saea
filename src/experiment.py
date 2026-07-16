"""Adapter Python do harness (arquitetura A2, §2 / §16.5.3).

Traduz `run(algoritmo, problema_id, semente)` numa chamada à *main OFICIAL* de
cada repositório em `algorithms/` — **nada é reimplementado** (fidelidade §20).
Este arquivo é o **esqueleto** montado na Fase 0 (cartão F0-01-harness): o
catálogo de problemas (fonte única A2) e o contrato do adapter existem; o
**despacho por algoritmo é preenchido nas rodadas** R1 (MATLAB via ponte),
R2 (BoTorch) e R3 (standalone). Por isso `ALGORITHM_DISPATCH` está **vazio** e
`run(...)` levanta `NotImplementedError` — é infraestrutura, sem algoritmo.

> **Descomissionado (§16.5).** A POC antiga (7 algoritmos reimplementados em
> `src/*_runner.py` + `NoisyProblem`/Kriging + toggle de ruído) **não entra no
> experimento** — o único código executado é o dos 16 repos oficiais. Este
> módulo foi **reescrito** para chamar as mains oficiais; o padrão de despacho,
> o logging por geração e a re-avaliação limpa da fitness são reaproveitados
> nas rodadas, não aqui.

Contrato do adapter por (algoritmo, problema) — preenchido nas rodadas (§16.5.3):
  1. Instancia o problema de `src/problems.py` pelo `problema_id` (A2/§2).
  2. Aplica bounds/sinal (§5.5): des-normaliza [0,1]↔nativo p/ BoTorch; nativo
     p/ PlatEMO/EA; devolve −f aos motores que maximizam. Métrica sempre sobre
     o `f` verdadeiro de minimização (CP-bounds/CP-sinal).
  3. Semeia (§5.3): `Generator` próprio p/ o DoE + salvar/restaurar o RNG
     global em volta de `pymoo.minimize`; offset `+1000·semente` p/ e81/c149
     (D22); `SeedSequence` p/ as sementes que o harness cria (D62/D91).
  4. Injeta `maxFE = 31D−1` e o DoE `11D−1` carregado do artefato (D87/D88),
     com hard-stop exato no wrapper de FE (D21/D89).
  5. Chama a main oficial, coleta a trajetória (② população real + ③ surrogate)
     e grava o export §17 (`src/manifest.py`, `src/audit_log.py`, F0-03).
  6. `try/except` + 1 retry (D23) → status ∈ {ok, retried_ok, failed}.

Módulo **leve por design**: o import de `src.problems` (que puxa pymoo/numpy) é
**lazy** — importar `src.experiment` funciona em qualquer interpretador, o que
mantém o despachante e o runner de aceitação rodando no `python3` base.
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════
#  Catálogo de problemas — fonte ÚNICA (A2/§2/§4). 25 classes concretas.
#  MMF16_L3 (d=3) foi REMOVIDO (Anexo D/REF-1); mantém-se só MMF16_20.
#  short name (usado no grid/CLI) → nome da classe em src.problems.
# ═══════════════════════════════════════════════════════════════════════════

PROBLEM_CLASSES: dict[str, str] = {
    'MMF1':     'MMF1',
    'MMF4':     'MMF4',
    'MMF11_L':  'MMF11_L',
    'MMF16_20': 'MMF16_20',
    'ZDT1':     'ZDT1',
    'ZDT3':     'ZDT3',
    'ZDT4':     'ZDT4',
    'ZDT6':     'ZDT6',
    'DTLZ1':    'DTLZ1',
    'DTLZ2':    'DTLZ2',
    'DTLZ3':    'DTLZ3',
    'DTLZ4':    'DTLZ4',
    'DTLZ7':    'DTLZ7',
    'WFG1':     'WFG1',
    'WFG2':     'WFG2',
    'WFG4':     'WFG4',
    'WFG5':     'WFG5',
    'WFG9':     'WFG9',
    'BBOB_F1':    'BBOB_F1_Sphere_Sphere',
    'BBOB_F5':    'BBOB_F5_Sphere_SharpRidge',
    'BBOB_F17':   'BBOB_F17_EllipsoidSeparable_SchafferF7',
    'BBOB_F22':   'BBOB_F22_AttractiveSector_SharpRidge',
    'BBOB_F37':   'BBOB_F37_SharpRidge_Rastrigin',
    'BBOB_F49':   'BBOB_F49_Rastrigin_Gallagher101',
    'BBOB_F55':   'BBOB_F55_Gallagher101_Gallagher101',
}

ALL_PROBLEMS: list[str] = list(PROBLEM_CLASSES)


def is_known_problem(short_name: str) -> bool:
    return short_name in PROBLEM_CLASSES


def _instantiate_problem(short_name: str):
    """Instancia a classe do problema pelo short name (A2).

    Import de `src.problems` **lazy** de propósito (puxa pymoo/numpy) — só é
    exigido quando um problema é de fato instanciado (nas rodadas), nunca só
    por importar este módulo.
    """
    if short_name not in PROBLEM_CLASSES:
        raise ValueError(f"Problema desconhecido: {short_name!r}. "
                         f"Conhecidos: {ALL_PROBLEMS}")
    from src import problems as _problems_mod  # lazy (pymoo/numpy)
    return getattr(_problems_mod, PROBLEM_CLASSES[short_name])()


# ═══════════════════════════════════════════════════════════════════════════
#  Despacho por algoritmo — VAZIO na Fase 0 (preenchido em R1/R2/R3).
#  Estrutura pretendida (por id): {'stack': 'botorch'|'standalone'|..., 'main': <callable>}.
#  A lista canônica de configs Python está em experiments.py::DEFAULT_ALGORITHMS.
# ═══════════════════════════════════════════════════════════════════════════

ALGORITHM_DISPATCH: dict[str, dict] = {}


def run(algoritmo: str, problema_id: str, semente: int, *,
        exp: str = "main", **kwargs):
    """Ponto de entrada lógico do adapter: `run(alg, problema_id, semente)`.

    **Não implementado na Fase 0** — o corpo por algoritmo entra nas rodadas
    (R1 MATLAB, R2 BoTorch, R3 standalone), seguindo o contrato de 6 passos do
    cabeçalho deste módulo. Levantar `NotImplementedError` aqui é o
    comportamento correto do andaime: F0-01 não roda algoritmo nenhum.
    """
    if algoritmo not in ALGORITHM_DISPATCH:
        raise NotImplementedError(
            f"Adapter do algoritmo {algoritmo!r} ainda não implementado "
            f"(Fase 0 = andaime; despacho preenchido em R1/R2/R3). "
            f"Problema={problema_id!r}, semente={semente}, exp={exp!r}.")
    # (Corpo real do despacho — rodadas.)
    raise NotImplementedError("ALGORITHM_DISPATCH populado mas run() não ligado.")
