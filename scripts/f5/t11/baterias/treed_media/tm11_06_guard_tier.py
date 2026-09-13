#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T11/treed_media — 06: o GUARD DE TIER (DI-42.5/A10) funciona?
Chama `run_treed_media` com `exp` FORA do big. O guard e a PRIMEIRA instrucao da
funcao (treed_media.py:329-335): levanta ANTES de qualquer I/O, de `_import_vendor`
e do AuditLogger. data_root aponta para um tempdir vazio (nada e escrito).
READ-ONLY sobre `data/` — nenhum arquivo do repo e tocado."""
import os, sys, tempfile, traceback
sys.path.insert(0, "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")

from src.treed_media import run_treed_media          # noqa: E402
from src import naming                               # noqa: E402

TD = tempfile.mkdtemp(prefix="tm11_guard_")
print("tempdir (vazio, nada e escrito):", TD)

for exp in ["off", "main", "sweep-small-lhs", "sweep-medium-mvns", "batch",
            "sweep-big-lhs", "sweep-big-mvns"]:
    try:
        tier, dist = naming.parse_sweep(exp)
    except Exception as e:
        tier, dist = "<parse_sweep ERRO: %s>" % type(e).__name__, None
    try:
        run_treed_media(exp, "treed_media", "ZDT4", 42, data_root=TD)
        veredito = "NAO BARROU (rodou/seguiu)"
    except ValueError as e:
        veredito = "BARROU ValueError: %s" % str(e).split("\n")[0][:78]
    except Exception as e:
        veredito = "outro erro (%s) — passou do guard: %s" % (type(e).__name__, str(e)[:70])
    print("  exp=%-18s tier=%-8s -> %s" % (exp, tier, veredito))

# alg errado (guarda que ja existia no T8)
try:
    run_treed_media("sweep-big-lhs", "c311", "ZDT4", 42, data_root=TD)
    print("  alg=c311            -> NAO BARROU")
except ValueError as e:
    print("  alg=c311            -> BARROU ValueError: %s" % str(e)[:70])
except Exception as e:
    print("  alg=c311            -> outro erro (%s)" % type(e).__name__)

print("arquivos criados no tempdir:", sum(len(f) for _, _, f in os.walk(TD)))
