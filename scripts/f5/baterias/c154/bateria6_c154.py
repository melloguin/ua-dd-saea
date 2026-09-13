#!/usr/bin/env python
"""BATERIA 6 — c154 (JES): (i) prova do DESALINHAMENTO ③-online x acqf_todos_restarts
(aspecto classe 3); (ii) plateau/nao-unicidade do argmax SEM supor alinhamento."""
import json, os, collections
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154"
REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
OUT = os.path.join(REPO, "f5/baterias/c154")
PROBS = sorted([p for p in os.listdir(ROOT) if not p.startswith('.')])

rows = []
ex = []
for prob in PROBS:
    b = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    L = [json.loads(l) for l in open(b + ".jsonl") if l.strip()]
    D = [r for r in L if r.get("rec") == "header"][0]["D"]
    dec = [r for r in L if r.get("rec") == "decision"]
    sur = pq.read_table(b + "__surrogate.parquet").to_pandas()
    on = sur[sur.regime == "online"]
    xc = [f"x{i}" for i in range(D)]
    n_it = n_marc_ultimo = n_tie = 0
    ties = []; ndist = []; idxs = []
    for d in dec:
        a = np.array(d.get("acqf_todos_restarts", []), float)
        if not len(a):
            continue
        n_it += 1
        af = np.where(np.isfinite(a), a, -np.inf)
        mx = af.max()
        k = int(np.isclose(af, mx, rtol=1e-9, atol=0).sum())
        ties.append(k)
        if k >= 2:
            n_tie += 1
        # indice bit-exato do vencedor no array (ordem de restart)
        hit = [i for i, v in enumerate(a) if v == d["acqf_escolhido"]]
        if hit:
            idxs.append(hit[0] / (len(a) - 1))
        blk = on[on.geracao == d["it"]]
        if len(blk) == len(a):
            ndist.append(len(blk[xc].drop_duplicates()))
            m = blk["real_solution_id"].notna().values
            if m.any():
                pos = int(np.flatnonzero(m)[0])
                if pos == len(a) - 1:
                    n_marc_ultimo += 1
                if hit and hit[0] != len(a) - 1 and prob == "MMF1" and len(ex) < 3:
                    ex.append(dict(problema=prob, it=d["it"],
                                   idx_bit_no_array=hit[0], pos_marcada_na_3=pos,
                                   acqf_escolhido=repr(d["acqf_escolhido"]),
                                   x_idx_bit=blk[xc].values[hit[0]].tolist(),
                                   x_marcado=blk[xc].values[pos].tolist()))
    rows.append(dict(problema=prob, D=D, n_it=n_it,
                     marcada_eh_ultima=n_marc_ultimo,
                     n_com_marca=len([1 for d in dec
                                      if len(on[on.geracao == d["it"]]) and
                                      on[on.geracao == d["it"]]["real_solution_id"].notna().any()]),
                     idx_bit_rel_med=float(np.median(idxs)) if idxs else np.nan,
                     its_com_empate=n_tie, pct_empate=100.0 * n_tie / n_it,
                     empates_med=float(np.median(ties)), empates_max=int(np.max(ties)),
                     x_distintos_med=float(np.median(ndist)),
                     x_distintos_min=int(np.min(ndist)) if ndist else 0))
R = pd.DataFrame(rows)
R.to_csv(os.path.join(OUT, "c154_desalinhamento_e_plateau.csv"), index=False)
print("=== DESALINHAMENTO ③-online x ⑥.acqf_todos_restarts + NAO-UNICIDADE do argmax")
print(R.to_string())
print("\nTOTAIS: linha marcada = ULTIMA do bloco em %d/%d (%.1f%%) | "
      "indice bit-exato do vencedor no array: mediana relativa %.2f (uniforme=0,50)"
      % (R.marcada_eh_ultima.sum(), R.n_com_marca.sum(),
         100 * R.marcada_eh_ultima.sum() / R.n_com_marca.sum(),
         np.median(R.idx_bit_rel_med)))
print("iteracoes com >=2 restarts a 1e-9 rel do maximo: %d/%d (%.1f%%)"
      % (R.its_com_empate.sum(), R.n_it.sum(),
         100 * R.its_com_empate.sum() / R.n_it.sum()))
print("\nEXEMPLOS (MMF1) — indice bit-exato != posicao marcada:")
for e in ex:
    print(" ", json.dumps(e, ensure_ascii=False))
