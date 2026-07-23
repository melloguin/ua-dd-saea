"""Adapter Python do harness (arquitetura A2, §2 / §16.5.3).

Traduz `run(algoritmo, problema_id, semente)` numa chamada à *main OFICIAL* de
cada repositório em `algorithms/` — **nada é reimplementado** (fidelidade §20).
Este arquivo é o **esqueleto** montado na Fase 0 (cartão F0-01-harness): o
catálogo de problemas (fonte única A2) e o contrato do adapter existem; o
**despacho por algoritmo é preenchido nas rodadas** R1 (MATLAB via ponte),
R2 (BoTorch) e R3 (standalone). [R2-00-harness] O despacho é um registro
**LAZY** (`_DISPATCH_LOADERS`): `ALGORITHM_DISPATCH` fica vazio no import (o
módulo segue leve) e `run()` resolve/importa o runner da rodada sob demanda;
algoritmo sem loader levanta `NotImplementedError`.

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

# ── Instâncias NÃO-canônicas p/ a validação MANUAL de fidelidade do autor (D97) ──
# [R1-c217] Fora dos 25 do A2 e do grid: existem só para o autor reproduzir a
# config EXATA do paper de um algoritmo e comparar com a âncora (Anexo J). NÃO
# entram em ALL_PROBLEMS/PROBLEMA_ID (os gates F0 exigem exatamente 25; seeds.json
# == doe.PROBLEMA_ID), nem na bateria. `short → (classe, kwargs)`.
#   DTLZ2_d15: DTLZ2 com n_var=2+13=15, m=3 = a config do paper do c217 PC-SAEA
#   (âncora IGD≈6,9212e-2; a bateria usa o canônico 'DTLZ2' = d=12).
FIDELITY_PROBLEMS: dict[str, tuple[str, dict]] = {
    'DTLZ2_d15': ('DTLZ2', {'k': 13}),
}


def is_known_problem(short_name: str) -> bool:
    return short_name in PROBLEM_CLASSES or short_name in FIDELITY_PROBLEMS


def _instantiate_problem(short_name: str):
    """Instancia a classe do problema pelo short name (A2).

    Import de `src.problems` **lazy** de propósito (puxa pymoo/numpy) — só é
    exigido quando um problema é de fato instanciado (nas rodadas), nunca só
    por importar este módulo. Além dos 25 canônicos, resolve as instâncias de
    FIDELITY_PROBLEMS (não-canônicas, D97) — que NÃO estão em ALL_PROBLEMS.
    """
    from src import problems as _problems_mod  # lazy (pymoo/numpy)
    if short_name in PROBLEM_CLASSES:
        return getattr(_problems_mod, PROBLEM_CLASSES[short_name])()
    if short_name in FIDELITY_PROBLEMS:
        cls, kw = FIDELITY_PROBLEMS[short_name]
        return getattr(_problems_mod, cls)(**kw)
    raise ValueError(f"Problema desconhecido: {short_name!r}. "
                     f"Conhecidos: {ALL_PROBLEMS} (+ fidelidade: {list(FIDELITY_PROBLEMS)})")


# ═══════════════════════════════════════════════════════════════════════════
#  Despacho por algoritmo — registro LAZY, preenchido pelas rodadas.
#  Estrutura (por id): {'stack': 'botorch'|'standalone'|..., 'main': <callable>}.
#  A lista canônica de configs Python está em experiments.py::DEFAULT_ALGORITHMS.
#
#  [R2-00-harness] O registro é LAZY por design: `ALGORITHM_DISPATCH` fica
#  VAZIO no import (o módulo continua leve — importável no `python3` base, e o
#  andaime F0-01 segue verificável) e é populado por `_resolve_dispatch` na
#  PRIMEIRA chamada de `run()` para o algoritmo — só então o módulo pesado da
#  rodada (torch/botorch) é importado. Cada cartão de rodada adiciona a sua
#  linha em `_DISPATCH_LOADERS` (c262/c154 no R2; R3 idem).
# ═══════════════════════════════════════════════════════════════════════════

ALGORITHM_DISPATCH: dict[str, dict] = {}

#: `alg → (módulo, callable, stack)` — resolvido/importado sob demanda.
#: Assinatura padrão do runner: `runner(exp, alg, problema_id, semente, **kw)`.
_DISPATCH_LOADERS: dict[str, tuple[str, str, str]] = {
    # stubpy = run-STUB transversal do R2-00 (prova de encanamento do contrato
    # N.1; NÃO é config do estudo — o token `stub` é o STUB MATLAB do R1-00).
    'stubpy': ('src.botorch_harness', 'run_stubpy', 'botorch'),
    # [R2-c262] qNEHVI (qLogNEHVI, BoTorch OFICIAL 0.18.1) sobre o harness R2-00.
    'c262': ('src.c262_qnehvi', 'run_c262', 'botorch'),
    # [R2-c154] JES (qLBMOJES-LB, BoTorch OFICIAL 0.18.1) sobre o harness R2-00.
    'c154': ('src.c154_jes', 'run_c154', 'botorch'),
    # ── Rodada 3 — standalone de implementação própria (contrato N.2) ──────
    # [R3-00-harness] run-STUB OFFLINE transversal (token distinto de `stub`
    # do R1-00 e `stubpy` do R2-00). NÃO é config do estudo.
    'stubr3': ('src.standalone_harness', 'run_stubr3', 'standalone'),
    # Os 6 configs da R3 entram aqui, 1 linha por cartão. O `stack` é
    # 'standalone' e o env de cada um vem do `envs.json` (D79) — b5r/b5m e
    # c311 rodam em venvs PRÓPRIOS e NUNCA podem ser co-importados (N.1.2):
    # o despacho da bateria usa `standalone_harness.run_in_venv`, que dá um
    # processo por run. Descomente ao fechar o cartão correspondente.
    # [R3-c122] θ-DEA-DP (2 FNNs par-a-par, driver próprio) sobre o harness R3-00.
    'c122':          ('src.c122_thetadeadp', 'run_c122', 'standalone'),
    # [R3-c149] LBN-MOBO (deep ensemble K=10 + HVI-greedy D96) sobre o R3-00.
    'c149':          ('src.c149_lbnmobo',    'run_c149', 'standalone'),
    # [R3-e81] qPOTS (Thompson + NSGA-II + maximin) sobre o R3-00. ⚠ env
    # PRÓPRIO `env_e81_qpots` (botorch 0.16.1 / pymoo 0.6.1.6 — NUNCA misturar
    # com o env-main): o despachante resolve por `envs.json:alg_to_env` e
    # roda em subprocess (D79/N.2).
    'e81':           ('src.e81_qpots',       'run_e81',  'standalone'),
    # [R3-b5] Prob-RVEA (b5r, mode 7) / Prob-MOEA/D (b5m, mode 72), OFFLINE. env
    # PRÓPRIO `env_b5` (sklearn 0.21.3, desdeo VENDORIZADO root-first) — subprocess
    # por venv (D79/N.2); NUNCA co-importar com c311 (N.1.2).
    'b5r':           ('src.b5_prob',         'run_b5r',  'standalone'),
    'b5m':           ('src.b5_prob',         'run_b5m',  'standalone'),
    # [R3-c311] TGPR-MO (treed-GP/GPy), OFFLINE. env PRÓPRIO `env_c311` (py3.8,
    # GPy 1.9.9, desdeo VENDORIZADO root-first) — subprocess por venv (D79/N.2);
    # NUNCA co-importar com b5 (N.1.2 — mesmo nome de pacote, código diferente).
    'c311':          ('src.c311_tgprmo',     'run_c311', 'standalone'),
    # 'moead_media': ('src.piso_offline',    'run_piso_offline', 'standalone'),
}


def _resolve_dispatch(algoritmo: str) -> dict | None:
    """Resolve (e cacheia em `ALGORITHM_DISPATCH`) a entrada de despacho do
    algoritmo, importando o módulo da rodada só agora (import pesado — lazy)."""
    entry = ALGORITHM_DISPATCH.get(algoritmo)
    if entry is None and algoritmo in _DISPATCH_LOADERS:
        import importlib
        mod_name, fn_name, stack = _DISPATCH_LOADERS[algoritmo]
        mod = importlib.import_module(mod_name)
        entry = {'stack': stack, 'main': getattr(mod, fn_name)}
        ALGORITHM_DISPATCH[algoritmo] = entry
    return entry


def run(algoritmo: str, problema_id: str, semente: int, *,
        exp: str = "main", **kwargs):
    """Ponto de entrada lógico do adapter: `run(alg, problema_id, semente)`.

    [R2-00-harness] Corpo real: resolve o despacho (lazy) e chama o runner da
    rodada com a assinatura padrão `runner(exp, alg, problema_id, semente,
    **kwargs)` — `kwargs` repassa `data_root`/`enable_bucket` etc. Erros do
    runner PROPAGAM (o despachante `experiments.py` aplica o retry D23; o
    `BudgetExhausted` nunca chega aqui — o runner o captura no ponto único de
    avaliação, D61). Algoritmo sem loader ⇒ `NotImplementedError` (cartões
    futuros preenchem `_DISPATCH_LOADERS`).
    """
    entry = _resolve_dispatch(algoritmo)
    if entry is None:
        raise NotImplementedError(
            f"Adapter do algoritmo {algoritmo!r} ainda não implementado "
            f"(despacho preenchido pelos cartões R1/R2/R3 em "
            f"_DISPATCH_LOADERS). Problema={problema_id!r}, "
            f"semente={semente}, exp={exp!r}.")

    # [R3-00-harness] ROTEAMENTO OBRIGATÓRIO por venv (D79/N.1.2). b5 e c311
    # vendorizam `desdeo_*` HOMÔNIMOS com código diferente: rodá-los no mesmo
    # processo faz o `sys.modules` entregar as classes erradas SEM ERRO. Isso
    # não pode depender de o operador lembrar de chamar `run_in_venv` — o
    # despachante serial (`experiments.py`, n_jobs=1) e o paralelo (loky, que
    # REUSA workers) chamam `run()` direto. Aqui a regra vira MECANISMO.
    # `_in_child` é posto pelo bootstrap do subprocesso e corta a recursão.
    if not kwargs.pop('_in_child', False):
        from src.standalone_harness import VENV_ONLY_ALGS
        if algoritmo in VENV_ONLY_ALGS:
            from src.standalone_harness import run_in_venv
            r = run_in_venv(algoritmo, problema_id, semente, exp=exp,
                            **kwargs)
            if not r.get('ok'):
                raise RuntimeError(
                    f"run em venv próprio falhou p/ {algoritmo!r} "
                    f"(rc={r.get('returncode')}, env={r.get('env_id')}):\n"
                    f"{r.get('traceback')}")
            return r['result']

    return entry['main'](exp, algoritmo, problema_id, semente, **kwargs)
