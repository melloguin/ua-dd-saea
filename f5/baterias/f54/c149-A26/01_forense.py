import json, numpy as np, pandas as pd, pyarrow.parquet as pq, hashlib, os
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
CELLS={"q10_ZDT4":"exp_batch_c149_ZDT4_42","ZDT4":"exp_main_c149_ZDT4_42",
       "q10_ZDT1":"exp_batch_c149_ZDT1_42","ZDT1":"exp_main_c149_ZDT1_42"}
def load(cell):
    p=f"{R}/{cell}/42/{CELLS[cell]}"
    L1=pq.read_table(p+"__real.parquet").to_pandas()
    L3=pq.read_table(p+"__surrogate.parquet").to_pandas()
    L6=[json.loads(l) for l in open(p+".jsonl")]
    return L1,L3,L6
for cell in ["q10_ZDT4","ZDT4"]:
    L1,L3,L6=load(cell)
    on=L3[L3.regime=="online"]
    ftm=on.groupby("geracao").fe_treino_max.first()
    d=np.diff(ftm.values)
    print(f"[{cell}] L3 online: {len(on)} rows, G={ftm.index.min()}..{ftm.index.max()}")
    print(f"   fe_treino_max: {ftm.values[:5]} ... {ftm.values[-3:]}  | diffs unique={np.unique(d)}")
    fits={r['geracao']:r for r in L6 if r['rec']=='fit'}
    ntr=np.array([fits[g]['n_treino'] for g in sorted(fits)])
    print(f"   L6 fit n_treino: {ntr[:5]} ... {ntr[-3:]} | diffs unique={np.unique(np.diff(ntr))}")
    sb=on[on.real_solution_id.notna()]
    print(f"   L3 flagged rows: {len(sb)} | per gen {sb.groupby('geracao').size().unique()} | sid {sb.real_solution_id.min()}..{sb.real_solution_id.max()}")
    print(f"   L1: {len(L1)} rows, fase init={int((L1.fase=='init').sum())}")
    print()
