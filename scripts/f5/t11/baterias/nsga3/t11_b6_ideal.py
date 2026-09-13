"""T11/nsga3 — bateria 6: as nao-monotonias do `ideal` logado (A18), com MAGNITUDE.
A F5 reportou 2/898; esta re-medicao lista TODAS e separa por magnitude relativa.
READ-ONLY. Saida: ideal_nao_monotonias.csv
"""
import json, os, glob
import numpy as np
import pandas as pd

S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga3"

rows, ntr = [], 0
for prob in sorted(os.listdir(S42)):
    d = os.path.join(S42, prob, "42")
    if not os.path.isdir(d):
        continue
    base = glob.glob(os.path.join(d, "*.manifest.json"))[0][:-len(".manifest.json")]
    gens = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    gens = [g for g in gens if g.get("rec") == "nsga3_gen"]
    I = np.array([g["ideal"] for g in gens], dtype=float)
    dif = np.diff(I, axis=0)
    ntr += dif.size
    for (g, m) in zip(*np.where(dif > 0)):
        a, b = I[g, m], I[g + 1, m]
        rows.append(dict(prob=prob, geracao=int(g + 1), obj=int(m), antes=a, depois=b,
                         delta=b - a, rel=(b - a) / max(abs(a), 1e-300)))

df = pd.DataFrame(rows).sort_values("delta", ascending=False)
df.to_csv(os.path.join(OUT, "ideal_nao_monotonias.csv"), index=False)
print("transicoes-objetivo totais: %d · nao-monotonias: %d (%.2f%%)"
      % (ntr, len(df), 100 * len(df) / ntr))
print(df.to_string(index=False))
print()
print("acima de 1e-6 absoluto: %d" % int((df.delta > 1e-6).sum()))
print("acima de 1e-3 absoluto: %d" % int((df.delta > 1e-3).sum()))
print("com 'antes' == 0.0 exato : %d" % int((df.antes == 0).sum()))
