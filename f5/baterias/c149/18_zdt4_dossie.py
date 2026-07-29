"""DOSSIE do achado classe (3): ③ de batch/ZDT4 dessincronizada. Evidencia completa p/ F5.4."""
import json,numpy as np,pandas as pd,pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
out={}
for lab,exp,prob in [("q10_ZDT4","batch","ZDT4"),("q10_ZDT1","batch","ZDT1")]:
    p=f"{ROOT}/{lab}/42/exp_{exp}_c149_{prob}_42"
    hdr=json.loads(open(p+".jsonl").readline()); D=hdr["D"];M=hdr["M"]
    dec=[];fits=[]
    for line in open(p+".jsonl"):
        dd=json.loads(line)
        if dd["rec"]=="decision": dec.append(dd)
        elif dd["rec"]=="fit": fits.append(dd)
    tim=pq.read_table(p+"__timing.parquet").to_pandas()
    # ④ x ⑥
    e_fit=np.abs(tim.tempo_fit_s.values-np.array([d["tempo_fit_s"] for d in dec])).max()
    e_bus=np.abs(tim.tempo_busca_s.values-np.array([d["tempo_busca_s"] for d in dec])).max()
    e_nac=np.abs(tim.n_acumulado.values-np.array([f["n_treino"] for f in fits])).max()
    sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","transf_params","mu_0","mu_1","sigma_0","sigma_1"]).to_pandas()
    g1=sur[(sur.regime=="online")&(sur.geracao==1)]
    tp=json.loads(g1.transf_params.iloc[0]); zm=np.array(tp["mean"]);zs=np.array(tp["std"])
    MUz=(g1[["mu_0","mu_1"]].values.astype(float)-zm)/zs; S2z=(g1[["sigma_0","sigma_1"]].values.astype(float)/zs)**2
    out[lab]=dict(
      erro_max_L4vsL6_tempo_fit=float(e_fit),erro_max_L4vsL6_tempo_busca=float(e_bus),erro_max_L4vsL6_n=float(e_nac),
      g1_transf_L3=dict(mean=[round(x,6) for x in zm],std=[round(x,6) for x in zs]),
      g1_transf_L6=dict(mean=fits[0]["z_mean"],std=fits[0]["z_std"]),
      g1_acq_mu_z_min_L3=[round(float(x),6) for x in MUz.min(0)], g1_acq_mu_z_min_L6=dec[0]["acq_resF_mu_z_min"],
      g1_acq_mu_z_max_L3=[round(float(x),6) for x in MUz.max(0)], g1_acq_mu_z_max_L6=dec[0]["acq_resF_mu_z_max"],
      g1_acq_s2_z_max_L3=[round(float(x),6) for x in S2z.max(0)], g1_acq_s2_z_max_L6=dec[0]["acq_resF_sigma2_z_max"],
      g2_transf_L3=dict(mean=[round(x,6) for x in np.array(json.loads(sur[(sur.regime=="online")&(sur.geracao==2)].transf_params.iloc[0])["mean"])]),
      g2_transf_L6=fits[1]["z_mean"],
    )
print(json.dumps(out,indent=1,ensure_ascii=False))
json.dump(out,open(OUT+"/dossie_q10_ZDT4.json","w"),indent=1,ensure_ascii=False)
