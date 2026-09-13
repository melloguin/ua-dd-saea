"""ERRATA 12 verificada: `p_wrong_stats` so pode existir no b5m (mode 72).
Cross-check nos smokes T11 irmaos + par de ablacao MMF1/s0 (b5m x moead_media).
"""
import json, glob, os, numpy as np, pandas as pd, pyarrow.parquet as pq
R = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments"
alvos = {"b5m": R+"/off/b5m/exp_off_b5m_MMF1_0",
         "b5r": R+"/off/b5r/exp_off_b5r_BBOB_F22_42",
         "moead_media": R+"/off/moead_media/exp_off_moead_media_MMF1_0",
         "c311": R+"/off/c311/exp_off_c311_BBOB_F17_42",
         "treed_media": R+"/sweep-big-mvns/treed_media/exp_sweep-big-mvns_treed_media_ZDT4_42"}
for alg, b in alvos.items():
    recs=[json.loads(l) for l in open(b+".jsonl")]
    dec=[r for r in recs if r["rec"]=="decision"]
    m=json.load(open(b+".manifest.json"))
    pres = lambda k: sum(k in r for r in dec)
    naonulo = lambda k: sum(r.get(k) is not None for r in dec)
    print("%-12s n_dec=%-5d  p_wrong_stats %d/%d nao-nulo  n_substituicoes %d/%d  "
          "flag_vet_deg %d/%d  | campanha_id=%s params=%s schema=%s" %
          (alg, len(dec), naonulo("p_wrong_stats"), pres("p_wrong_stats"),
           naonulo("n_substituicoes"), pres("n_substituicoes"),
           naonulo("flag_vetores_degenerados"), pres("flag_vetores_degenerados"),
           m.get("campanha_id","AUSENTE")[:8] if m.get("campanha_id") else "AUSENTE",
           "params" in m, m.get("schema_version")))

print("\n=== PAR DE ABLACAO D77 no smoke T11: MMF1 / semente 0 ===")
for alg in ("b5m","moead_media"):
    b=alvos[alg]
    sg=pq.read_table(b+"__surrogate.parquet").to_pandas()
    fin=pq.read_table(b+"__final.parquet").to_pandas()
    bu=sg[sg.regime=="offline"]; so=sg[sg.regime=="sonda"]
    xs=[c for c in sg.columns if c.startswith("x")]
    mus=[c for c in sg.columns if c.startswith("mu_")]; sis=[c for c in sg.columns if c.startswith("sigma_")]
    ks=sorted(bu.geracao.dropna().astype(int).unique())
    g1=bu[bu.geracao==ks[0]]; gl=bu[bu.geracao==ks[-1]]
    print("%-12s n_ger=%-4d pop=%-3d sigma_pop g1=%.5f -> gN=%.5f (razao %.3f)  "
          "|⑦|=%d nd=%d fantasia=%.3f  sonda linhas=%d sigma-NaN=%d"
          % (alg,len(ks),len(g1),g1[sis].values.mean(),gl[sis].values.mean(),
             gl[sis].values.mean()/g1[sis].values.mean(),
             len(fin),int(fin.nd_pos_real.sum()),fin.nd_pos_real.sum()/len(fin),
             len(so),int(sg[sis].isna().sum().sum())))
