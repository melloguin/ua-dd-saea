"""e81: PRE-T11 (data/experiments, s0) x POS-T11 (smoke T11, s0) — MESMA celula.
Prova direta de que a campanha T11 nao perturbou a busca do e81. READ-ONLY."""
import json, hashlib
import numpy as np, pyarrow.parquet as pq
PRE="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/main/e81/exp_main_e81_MMF1_0"
POS="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/e81/exp_main_e81_MMF1_0"
a=json.load(open(PRE+".manifest.json")); b=json.load(open(POS+".manifest.json"))
print("PRE : campanha_id=%s schema=%s repo_hash=%s created=%s" % (a.get("campanha_id","<AUSENTE>"),a.get("schema_version"),a.get("repo_hash"),a.get("created_at")))
print("POS : campanha_id=%s schema=%s repo_hash=%s created=%s" % (b.get("campanha_id","<AUSENTE>"),b.get("schema_version"),b.get("repo_hash"),b.get("created_at")))
print("PRE : status=%s fe_final=%s n_ger=%s doe_hash=%s" % (a.get("status"),a.get("fe_final"),a.get("n_geracoes"),a.get("doe_hash")[:16]))
print("POS : status=%s fe_final=%s n_ger=%s doe_hash=%s" % (b.get("status"),b.get("fe_final"),b.get("n_geracoes"),b.get("doe_hash")[:16]))
print()
for cam,suf in [("① real","__real.parquet"),("② pop","__pop.parquet"),("③ surrogate","__surrogate.parquet"),("④ timing","__timing.parquet")]:
    ta=pq.read_table(PRE+suf); tb=pq.read_table(POS+suf)
    cols=[c for c in ta.column_names if c in tb.column_names]
    ig=[]; dif=[]
    for c in cols:
        va=ta.column(c).to_pylist(); vb=tb.column(c).to_pylist()
        (ig if va==vb else dif).append(c)
    print(f"{cam:14s} linhas {ta.num_rows} x {tb.num_rows} | colunas identicas {len(ig)}/{len(cols)}")
    if dif: print("   DIFEREM:", dif[:12])
# hash das colunas de decisao da ①
xa=pq.read_table(PRE+"__real.parquet").to_pandas(); xb=pq.read_table(POS+"__real.parquet").to_pandas()
print("\ncolunas ①:", list(xa.columns))
com=[c for c in xa.columns if c in xb.columns and c not in ("run_id",)]
h=lambda df: hashlib.sha256(df[com].to_csv(index=False).encode()).hexdigest()
print("sha256 ① (sem run_id):  PRE=%s\n                        POS=%s\n   => %s" % (h(xa),h(xb), "BIT-IDENTICA" if h(xa)==h(xb) else "DIFERE"))
