#!/usr/bin/env python
"""
F5.4 / moead-M16 — POR QUE o recomputo em float64 do analista NAO resgatou estas 16.

Hipotese: a ① grava X em float32 (D53) — nao so F. Nos problemas em que um
objetivo E LITERALMENTE uma coordenada de X (ZDT1/ZDT3: f1 = x1; DTLZ7: f_i = x_i
para i<M; MMF: f1 = x1), a colisao float32 esta no X. Reavaliar em float64 A
PARTIR DA ① reproduz o MESMO empate — a informacao ja foi destruida.
Isso e exatamente a nota registrada na D57 item 3 e a regra R4#1 do CONTRATO.

Contraste: no DTLZ4 a perda e no F (underflow denormal), e F e funcao NAO-LINEAR
de X -> reavaliar restaura a resolucao. Dai o resgate do analista funcionar la e
nao aqui.
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src import problems as P

RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/moead-M16"

PARES = [  # (problema, ger, sid_A, sid_B) — os pares que decidem cada divergencia
    ("ZDT1", 5, 381, 307), ("ZDT1", 6, 399, 307), ("ZDT1", 7, 414, 307),
    ("ZDT1", 8, 427, 307), ("ZDT1", 9, 444, 307), ("ZDT1", 10, 460, 307),
    ("ZDT1", 34, 819, 837), ("ZDT3", 34, 811, 829),
    ("DTLZ7", 30, 621, 625), ("MMF11_L", 3, 2, 38), ("DTLZ3", 18, 340, 351),
    ("ZDT6", 3, 130, None),
]


def ev64(prob, X):
    """reavalia em float64 com o modulo OFICIAL, a partir do X da ①(float32)."""
    fn = P.get_problem(prob) if hasattr(P, "get_problem") else None
    return fn, None


rows = []
for prob in sorted(os.listdir(RES)):
    d = os.path.join(RES, prob, "42"); base = f"exp_main_moead_{prob}_42"
    real = pd.read_parquet(os.path.join(d, base + "__real.parquet"))
    xc = sorted([c for c in real.columns if c.startswith("x") and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    fc = sorted([c for c in real.columns if c.startswith("f") and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    X = real[xc].to_numpy(np.float64)
    F = real[fc].to_numpy(np.float64)
    sid = real["solution_id"].to_numpy()
    # quantos pares de sids distintos colidem em ALGUMA coordenada de X (f32)?
    n = len(X)
    col_x = 0
    for a in range(n):
        eq = (X[a + 1:] == X[a]).any(1)
        col_x += int(eq.sum())
    rows.append(dict(problema=prob, n_sids=n, D=len(xc), M=len(fc),
                     pares_colidem_1coordX_f32=col_x,
                     frac=col_x / (n * (n - 1) / 2)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "r5_colisao_X.csv"), index=False)
print(pd.DataFrame(rows).to_string(index=False))

print("\n=== PARES DECISIVOS: colisao no X (float32) e no F ===")
det = []
for prob, ger, a, b in PARES:
    if b is None:
        continue
    d = os.path.join(RES, prob, "42"); base = f"exp_main_moead_{prob}_42"
    real = pd.read_parquet(os.path.join(d, base + "__real.parquet"))
    xc = sorted([c for c in real.columns if c.startswith("x") and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    fc = sorted([c for c in real.columns if c.startswith("f") and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    r = real.set_index("solution_id")
    xa, xb = r.loc[a, xc].to_numpy(np.float64), r.loc[b, xc].to_numpy(np.float64)
    fa, fb = r.loc[a, fc].to_numpy(np.float64), r.loc[b, fc].to_numpy(np.float64)
    ix = np.where(xa == xb)[0]
    iff = np.where(fa == fb)[0]
    det.append(dict(problema=prob, ger=ger, sidA=a, sidB=b,
                    coordX_identicas_f32=ix.tolist(),
                    obj_identicos_f32=iff.tolist(),
                    X_identico_inteiro=bool(np.array_equal(xa, xb)),
                    F_identico_inteiro=bool(np.array_equal(fa, fb))))
    print(f"{prob:9s} g{ger:<3d} sid {a} vs {b}: coordenadas de X iguais em f32 = "
          f"{ix.tolist()} | objetivos iguais em f32 = {iff.tolist()} | "
          f"X inteiro igual={np.array_equal(xa, xb)} F inteiro igual={np.array_equal(fa, fb)}")
pd.DataFrame(det).to_csv(os.path.join(OUT, "r5_pares_decisivos.csv"), index=False)
