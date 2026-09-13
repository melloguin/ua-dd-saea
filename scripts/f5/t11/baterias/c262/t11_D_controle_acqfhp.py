#!/usr/bin/env python
"""T11/c262 — BATERIA D (CONTROLE): o `acqf_hp` logado e o objeto REAL?

O padrao que a torre mandou procurar (c217: campo presente, dado sentinela).
Aqui o teste e mais duro: constroi a acqf com `_make_acqf` (que consome
`**ACQF_HP`) e compara ATRIBUTO A ATRIBUTO com o dict que o manifesto grava,
+ com o `acqf_hp` MEDIDO no smoke T11 preservado.

NAO toca data/. Nao invoca experiments.py. So importa o modulo e constroi um
modelo de brinquedo em memoria.
"""
import json
import sys

sys.path.insert(0, "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
import torch

from src import c262_qnehvi as c

torch.set_default_dtype(torch.float64)
torch.manual_seed(0)
X = torch.rand(8, 3, dtype=torch.float64)
Y = torch.cat([-(X ** 2).sum(-1, keepdim=True), -(1 - X).pow(2).sum(-1, keepdim=True)], -1)
model = c._build_models(X, Y)
acqf = c._make_acqf(model, [-9.0, -9.0], X, h1=123)

logado = dict(c.ACQF_HP)
SMOKE = ("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/"
         "experiments/main/c262/exp_main_c262_MMF1_0.manifest.json")
no_smoke = json.load(open(SMOKE))["params"]["acqf_hp"]

# onde o BoTorch guarda cada hp no objeto construido
sitios = {
    "alpha": ["alpha"],
    "tau_relu": ["tau_relu"],
    "tau_max": ["tau_max"],
    "fat": ["fat"],
    "eta": ["eta"],
    "prune_baseline": ["prune_baseline"],
    "cache_root": ["_cache_root", "cache_root"],
    "cache_pending": ["cache_pending", "_cache_pending"],
    "max_iep": ["max_iep", "_max_iep"],
    "incremental_nehvi": ["incremental_nehvi", "_incremental_nehvi"],
}
print(f"{'hp':20s} {'ACQF_HP':>12s} {'smoke ⑤':>12s} {'objeto botorch':>20s}  veredito")
n_conf = n_ausente = 0
for k, v in logado.items():
    achado, val = None, None
    for at in sitios[k]:
        if hasattr(acqf, at):
            achado, val = at, getattr(acqf, at)
            break
    if isinstance(val, torch.Tensor):
        val = val.item()
    if achado is None:
        ver = "NAO-EXPOSTO no objeto"
        n_ausente += 1
    else:
        bate = (bool(val) == bool(v)) if isinstance(v, bool) else (val == v)
        ver = "CONFIRMA" if bate else f"DIVERGE ({achado})"
        n_conf += bool(bate)
    print(f"{k:20s} {str(v):>12s} {str(no_smoke.get(k)):>12s} "
          f"{str(val):>20s}  {ver}")

print()
print("ACQF_HP (codigo) == acqf_hp (smoke ⑤):", logado == no_smoke)
print(f"hp confirmados no objeto: {n_conf}/{len(logado)} | "
      f"nao-expostos: {n_ausente}/{len(logado)}")
# controle-negativo: a assercao do teste oficial reprova se mudarmos o valor?
print()
print("--- CONTROLE NEGATIVO (o gate reprova?) ---")
acqf2 = c.qLogNEHVI_probe if False else None
import copy
hp_falso = dict(c.ACQF_HP); hp_falso["alpha"] = 0.5
try:
    from botorch.acquisition.multi_objective.logei import (
        qLogNoisyExpectedHypervolumeImprovement as Q)
    from botorch.sampling.normal import SobolQMCNormalSampler
    a2 = Q(model=model, ref_point=[-9.0, -9.0], X_baseline=X,
           sampler=SobolQMCNormalSampler(sample_shape=torch.Size([128]), seed=1),
           **hp_falso)
    print("alpha injetado 0.5 -> objeto expoe:", a2.alpha,
          "| discrimina:", a2.alpha != acqf.alpha)
except Exception as e:
    print("controle negativo falhou:", type(e).__name__, e)
print()
print("prune_baseline e atributo do objeto?",
      hasattr(acqf, "prune_baseline"),
      "-> a assercao `X if hasattr else True` do tests/test_c262.py:125 e",
      "REAL" if hasattr(acqf, "prune_baseline") else "VACUA (sempre passa)")
