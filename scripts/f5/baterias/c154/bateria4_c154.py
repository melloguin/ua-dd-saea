#!/usr/bin/env python
"""BATERIA 4 — c154 (JES): o achado-de-ouro (ruido inferido x sigma x cobertura),
assinatura exploratoria (fantasia x sonda), decaimento da acqf, maquinas dos rivais."""
import json, os
import numpy as np, pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
OUT = os.path.join(REPO, "f5/baterias/c154")

# ---------- A. sigma da sonda x ruido inferido (o mecanismo causal) ----------
sr = pd.read_csv(os.path.join(OUT, "c154_sonda_recomputada.csv"))
hp = pd.read_csv(os.path.join(OUT, "c154_modelo_hp.csv"))
recs = []
for _, r in sr.iterrows():
    for m in [0, 1, 2]:
        if f"wape{m}" not in sr.columns or pd.isna(r.get(f"wape{m}")):
            continue
        recs.append(dict(problema=r.problema, bloco=int(r.bloco), obj=m,
                         wape=r[f"wape{m}"], cob=r[f"cov{m}"],
                         sigma_med=r[f"sigma_med{m}"], nan_sigma=r[f"nan_sigma{m}"]))
S = pd.DataFrame(recs).merge(
    hp[["problema", "it", "obj", "noise", "ls_med", "ls_min", "ls_max",
        "outputscale", "mll"]],
    left_on=["problema", "bloco", "obj"], right_on=["problema", "it", "obj"],
    how="left")
S.to_csv(os.path.join(OUT, "c154_achado_ouro.csv"), index=False)

print("=== A1. cross-check da minha recomputacao vs sonda_f52e (WAPE e cobertura)")
f52 = pd.read_csv(os.path.join(REPO, "f5/sonda_f52e.csv"))
f = f52[(f52.alg == "c154") & (f52.exp == "main")].copy()
f["bloco"] = f["bloco"].astype(int)
X = S.merge(f[["problema", "bloco", "obj", "wape", "cobertura95"]],
            on=["problema", "bloco", "obj"], suffixes=("_meu", "_f52"))
print("n=%d  |dWAPE|max=%.3e  |dCob|max=%.3e" %
      (len(X), np.abs(X.wape_meu - X.wape_f52).max(),
       np.abs(X.cob - X.cobertura95).max()))

print("\n=== A2. SALTOS de ruido (>=5x entre blocos consecutivos): efeito em sigma/cob/WAPE")
sal = []
for (p, o), sub in S.sort_values("bloco").groupby(["problema", "obj"]):
    sub = sub.dropna(subset=["noise"]).reset_index(drop=True)
    for i in range(1, len(sub)):
        a, b = sub.loc[i - 1], sub.loc[i]
        if b.noise / max(a.noise, 1e-30) >= 5.0:
            sal.append(dict(problema=p, obj=o, bloco_de=int(a.bloco),
                            bloco_para=int(b.bloco),
                            noise_de=a.noise, noise_para=b.noise,
                            razao=b.noise / a.noise,
                            sigma_de=a.sigma_med, sigma_para=b.sigma_med,
                            d_sigma_pct=100 * (b.sigma_med - a.sigma_med) / a.sigma_med,
                            cob_de=a.cob, cob_para=b.cob, d_cob=b.cob - a.cob,
                            wape_de=a.wape, wape_para=b.wape,
                            d_wape_pct=100 * (b.wape - a.wape) / a.wape,
                            outsc_de=a.outputscale, outsc_para=b.outputscale,
                            d_outsc_pct=100 * (b.outputscale - a.outputscale) / a.outputscale,
                            ls_de=a.ls_med, ls_para=b.ls_med))
J = pd.DataFrame(sal)
J.to_csv(os.path.join(OUT, "c154_saltos_ruido.csv"), index=False)
print(J.to_string())
if len(J):
    print("\nSALTOS n=%d | sigma CAI em %d (%.0f%%) | cobertura CAI em %d (%.0f%%) "
          "| WAPE PIORA em %d | outputscale CAI em %d"
          % (len(J), (J.d_sigma_pct < 0).sum(), 100 * (J.d_sigma_pct < 0).mean(),
             (J.d_cob < 0).sum(), 100 * (J.d_cob < 0).mean(),
             (J.d_wape_pct > 0).sum(), (J.d_outsc_pct < 0).sum()))
    print("medianas: d_sigma %.1f%% | d_cob %+.4f | d_wape %+.1f%% | d_outputscale %.1f%%"
          % (J.d_sigma_pct.median(), J.d_cob.median(), J.d_wape_pct.median(),
             J.d_outsc_pct.median()))

print("\n=== A3. regime alto x baixo ruido por celula-objetivo (mediana de sigma/cob/WAPE)")
reg = []
for (p, o), sub in S.groupby(["problema", "obj"]):
    sub = sub.dropna(subset=["noise"])
    if len(sub) < 10 or sub.noise.max() / sub.noise.min() < 5:
        continue
    thr = np.sqrt(sub.noise.max() * sub.noise.min())
    hi, lo = sub[sub.noise > thr], sub[sub.noise <= thr]
    if len(hi) < 3 or len(lo) < 3:
        continue
    reg.append(dict(problema=p, obj=o, n_hi=len(hi), n_lo=len(lo),
                    noise_hi=hi.noise.median(), noise_lo=lo.noise.median(),
                    sigma_hi=hi.sigma_med.median(), sigma_lo=lo.sigma_med.median(),
                    d_sigma_pct=100 * (hi.sigma_med.median() - lo.sigma_med.median()) /
                    lo.sigma_med.median(),
                    cob_hi=hi.cob.median(), cob_lo=lo.cob.median(),
                    wape_hi=hi.wape.median(), wape_lo=lo.wape.median(),
                    outsc_hi=hi.outputscale.median(), outsc_lo=lo.outputscale.median()))
G = pd.DataFrame(reg)
G.to_csv(os.path.join(OUT, "c154_regimes_ruido.csv"), index=False)
print(G.to_string())
if len(G):
    print("\nregime ALTO ruido: sigma menor em %d/%d | cobertura menor em %d/%d "
          "| WAPE maior em %d/%d"
          % ((G.sigma_hi < G.sigma_lo).sum(), len(G),
             (G.cob_hi < G.cob_lo).sum(), len(G),
             (G.wape_hi > G.wape_lo).sum(), len(G)))

# ---------- B. assinatura exploratoria: erro de fantasia x WAPE da sonda ----------
cel = pd.read_csv(os.path.join(OUT, "c154_celulas.csv"))
son = pd.read_csv(os.path.join(OUT, "c154_sonda_resumo.csv"))
comp = []
for _, c in cel.iterrows():
    for m in range(int(c.M)):
        w = son[(son.problema == c.problema) & (son.obj == m)]
        if not len(w):
            continue
        comp.append(dict(problema=c.problema, obj=m,
                         wape_infill=c[f"U11_fantasia_wape_obj{m}"],
                         wape_sonda_med=(w.wape_1.iloc[0] + w.wape_N.iloc[0]) / 2,
                         wape_sonda_N=w.wape_N.iloc[0],
                         razao=c[f"U11_fantasia_wape_obj{m}"] / w.wape_N.iloc[0]))
C = pd.DataFrame(comp)
C.to_csv(os.path.join(OUT, "c154_fantasia_vs_sonda.csv"), index=False)
print("\n=== B. ERRO DE FANTASIA nos infills x WAPE da sonda (assinatura exploratoria)")
print(C.to_string())
print("razao infill/sonda: mediana %.2f | >1 em %d/%d" %
      (C.razao.median(), (C.razao > 1).sum(), len(C)))

# ---------- C. decaimento da acqf e distancia ao arquivo ----------
dec = pd.read_csv(os.path.join(OUT, "c154_decisoes.csv"))
print("\n=== C. acqf escolhida e dist_min_arquivo — 1o quartil x ultimo quartil")
dd = []
for p, sub in dec.groupby("problema"):
    sub = sub.sort_values("it")
    n = len(sub); q = max(n // 4, 1)
    dd.append(dict(problema=p, n=n,
                   acqf_q1=sub.acqf_escolhido.iloc[:q].median(),
                   acqf_q4=sub.acqf_escolhido.iloc[-q:].median(),
                   queda_pct=100 * (sub.acqf_escolhido.iloc[-q:].median() -
                                    sub.acqf_escolhido.iloc[:q].median()) /
                   abs(sub.acqf_escolhido.iloc[:q].median()),
                   dist_q1=sub.dist_min_arquivo.iloc[:q].median(),
                   dist_q4=sub.dist_min_arquivo.iloc[-q:].median(),
                   acqf_neg=int((sub.acqf_escolhido < 0).sum()),
                   nfront1_fim=sub.n_front1.iloc[-1]))
DD = pd.DataFrame(dd)
DD.to_csv(os.path.join(OUT, "c154_acqf_decaimento.csv"), index=False)
print(DD.to_string())

# ---------- D. maquinas dos rivais nos 11 problemas ----------
tp = pd.read_csv(os.path.join(REPO, "f5/tempo_f52d.csv"))
probs = sorted(cel.problema.unique())
mq = tp[(tp.exp == "main") & (tp.problema.isin(probs))]
piv = mq.pivot_table(index="alg", columns="problema", values="maquina",
                     aggfunc="first")
piv.to_csv(os.path.join(OUT, "c154_maquinas_rivais.csv"))
print("\n=== D. MAQUINA por (alg, problema) nos 11 problemas do c154")
print(piv.to_string())
