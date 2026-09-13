#!/usr/bin/env python
"""T11/c238 · bateria 1 — instrumentacao NOVA (smoke) x s42 (pre-T11) + par G-6.
READ-ONLY. Escreve so em f5/t11/baterias/c238/.
"""
import json, hashlib, os, sys
import pandas as pd, pyarrow.parquet as pq
import numpy as np

OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238"
EV = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11"
S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"

def base(root, prob="MMF1"):
    return f"{root}/experiments/main/c238/exp_main_c238_{prob}_42"

def rd_manifest(p):
    with open(p) as f: return json.load(f)

def rd_jsonl(p):
    recs = []
    with open(p) as f:
        for ln in f:
            ln = ln.strip()
            if not ln: continue
            try: recs.append(json.loads(ln))
            except Exception as e: recs.append({"_MALFORMADA": str(e), "_raw": ln[:80]})
    return recs

def sha(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''): h.update(b)
    return h.hexdigest()

print("="*100)
print("A) MANIFESTO — smoke T11 vs s42 (MMF1)")
print("="*100)
sm = rd_manifest(base(f"{EV}/smoke_matlab")+".manifest.json")
s42m = rd_manifest(f"{S42}/MMF1/42/exp_main_c238_MMF1_42.manifest.json")
ks, k42 = set(sm.keys()), set(s42m.keys())
print("chaves SO no smoke  :", sorted(ks-k42))
print("chaves SO na s42    :", sorted(k42-ks))
print("chaves em comum     :", len(ks & k42))
for k in ["schema_version","campanha_id","repo_hash","status","motivo_parada","fe_final","maxfe","cache_hits","doe_hash"]:
    print(f"  {k:18s} smoke={sm.get(k,'<AUSENTE>')!r:60s} s42={s42m.get(k,'<AUSENTE>')!r}")
print("\n-- params (smoke) --"); print(json.dumps(sm.get("params",{}), indent=1, ensure_ascii=False)[:2500])
print("\n-- params: chaves smoke x s42 --")
ps, p42 = set(sm.get("params",{})), set(s42m.get("params",{}))
print("  so smoke:", sorted(ps-p42), "| so s42:", sorted(p42-ps), "| comum:", len(ps&p42))
for k in sorted(ps&p42):
    if sm["params"][k] != s42m["params"][k]:
        print(f"  DIFERE {k}: smoke={sm['params'][k]!r} s42={s42m['params'][k]!r}")
print("\n-- sigma_dict: chaves --")
sg, sg42 = sm.get("sigma_dict",{}), s42m.get("sigma_dict",{})
print("  so smoke:", sorted(set(sg)-set(sg42)), "| so s42:", sorted(set(sg42)-set(sg)))
for k in sorted(set(sg)&set(sg42)):
    if sg[k]!=sg42[k]: print(f"  DIFERE {k}:\n     smoke={sg[k]!r}\n     s42  ={sg42[k]!r}")
print("\n-- sonda block --"); print(" smoke:", json.dumps(sm.get("sonda"), ensure_ascii=False))
print(" s42  :", json.dumps(s42m.get("sonda"), ensure_ascii=False))
print("\n-- timing --"); print(" smoke:", json.dumps(sm.get("timing"), ensure_ascii=False)[:600])
print(" s42  :", json.dumps(s42m.get("timing"), ensure_ascii=False)[:600])
print("\n-- campos T11 procurados no manifesto --")
for campo in ["REGRA_DO_ROTULO","campanha_id","repo_hash","y_treino_dist","pmid_ids","ref_ids","executable","host"]:
    def deep(d, key):
        if isinstance(d, dict):
            if key in d: return d[key]
            for v in d.values():
                r = deep(v, key)
                if r is not None: return r
        return None
    print(f"  {campo:20s} smoke={str(deep(sm,campo))[:70]:72s} s42={str(deep(s42m,campo))[:60]}")

print("\n"+"="*100)
print("B) ⑥ jsonl — censo de rec e campos NOVOS (smoke vs s42)")
print("="*100)
for nome, p in [("smoke", base(f"{EV}/smoke_matlab")+".jsonl"), ("s42", f"{S42}/MMF1/42/exp_main_c238_MMF1_42.jsonl")]:
    rs = rd_jsonl(p)
    mal = [r for r in rs if "_MALFORMADA" in r]
    from collections import Counter
    c = Counter(r.get("rec","<sem rec>") for r in rs)
    print(f"\n[{nome}] n_linhas={len(rs)} malformadas={len(mal)} censo={dict(c)}")
    gens = [r for r in rs if r.get("rec")=="c238_gen"]
    if gens:
        kk = set()
        for g in gens: kk |= set(g.keys())
        print(f"  campos do c238_gen ({len(kk)}): {sorted(kk)}")
        print(f"  exemplo g1: {json.dumps(gens[0], ensure_ascii=False)[:1200]}")
        for campo in ["tempo_aval_real_s","min_dist_infill","eim_best","eim_mediana_pool","criterion","ga_pop","ga_gens","n_front","n_front1","f_best","norm_min","norm_max","modelo_hp","n_eim_nan","n_range0","n_dedup","fe_treino_max"]:
            pres = sum(1 for g in gens if campo in g)
            naonull = sum(1 for g in gens if g.get(campo) is not None)
            print(f"    {campo:22s} presente={pres}/{len(gens)}  nao-nulo={naonull}")
    hdr = [r for r in rs if r.get("rec")=="header"]
    if hdr: print(f"  header: {json.dumps(hdr[0], ensure_ascii=False)[:900]}")
    ftr = [r for r in rs if r.get("rec")=="footer"]
    for f_ in ftr: print(f"  footer: {json.dumps(f_, ensure_ascii=False)[:400]}")

print("\n"+"="*100)
print("C) ③ surrogate — regimes presentes (smoke vs s42)")
print("="*100)
for nome, p in [("smoke", base(f"{EV}/smoke_matlab")+"__surrogate.parquet"), ("s42", f"{S42}/MMF1/42/exp_main_c238_MMF1_42__surrogate.parquet")]:
    t = pq.read_table(p)
    df = t.to_pandas()
    print(f"\n[{nome}] linhas={len(df)} cols={list(df.columns)}")
    print("  regimes:", df["regime"].value_counts().to_dict())
    for c in ["espaco_modelo","transf_tipo","modelo_flag","pred_tipo"]:
        if c in df.columns: print(f"  {c}: {df[c].astype(str).value_counts().to_dict()}")

print("\n"+"="*100)
print("D) PAR G-6 (nao-perturbacao) — c238/MMF1")
print("="*100)
com, sem = base(f"{EV}/g6_com"), base(f"{EV}/g6_sem")
mc, ms = rd_manifest(com+".manifest.json"), rd_manifest(sem+".manifest.json")
print("  COM sonda:", json.dumps(mc.get("sonda"), ensure_ascii=False))
print("  SEM sonda:", json.dumps(ms.get("sonda"), ensure_ascii=False))
print("  fe_final :", mc.get("fe_final"), ms.get("fe_final"), "| status:", mc.get("status"), ms.get("status"))
for lay in ["__real","__pop","__surrogate","__timing"]:
    a, b = com+lay+".parquet", sem+lay+".parquet"
    ea, eb = os.path.exists(a), os.path.exists(b)
    if not (ea and eb):
        print(f"  {lay:12s} existe COM={ea} SEM={eb}"); continue
    ha, hb = sha(a), sha(b)
    na, nb = pq.read_table(a).num_rows, pq.read_table(b).num_rows
    print(f"  {lay:12s} sha256 {'IDENTICO' if ha==hb else 'DIFERE'} | linhas COM={na} SEM={nb} | {ha[:16]} {hb[:16]}")
# comparacao numerica da ①
da = pq.read_table(com+"__real.parquet").to_pandas()
db = pq.read_table(sem+"__real.parquet").to_pandas()
xc = [c for c in da.columns if c.startswith("x")]
fc = [c for c in da.columns if c.startswith("f")]
if len(da)==len(db):
    print(f"  ① max|ΔX| = {np.abs(da[xc].values-db[xc].values).max():.3e} | max|Δf| = {np.abs(da[fc].values-db[fc].values).max():.3e}")
print("\nFIM b1")
