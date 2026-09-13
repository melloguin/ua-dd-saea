#!/usr/bin/env python
"""
F5.4 · b4-A12 — verificacao ADVERSARIAL independente do achado
"Campos p0/p1 do jsonl invertidos em relacao a classe que medem".

Codigo escrito do zero (nao reaproveita nenhuma bateria do analista).
Escreve APENAS em f5/baterias/f54/b4-A12/.
"""
import json, math, os, glob, sys
import numpy as np
import pandas as pd

RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/b4-A12"
os.makedirs(OUT, exist_ok=True)

probs = sorted(os.listdir(RES))
probs = [p for p in probs if os.path.isdir(os.path.join(RES, p))]

rows = []
for pr in probs:
    d = os.path.join(RES, pr, "42")
    jl = glob.glob(os.path.join(d, "*.jsonl"))
    assert len(jl) == 1, (pr, jl)
    hdr = None
    for line in open(jl[0]):
        r = json.loads(line)
        if r.get("rec") == "header":
            hdr = r
        elif r.get("rec") == "b4_gen":
            rows.append(dict(
                prob=pr, D=hdr["D"], M=hdr["M"], maxfe=hdr["maxfe"],
                g=r["geracao"], fe=r["fe"], arquivo=r["arquivo"],
                p0=r.get("p0"), p1=r.get("p1"), rr=r["rr"], tr=r["tr"],
                ramo=r["ramo"], lote=r["lote"],
                L_sel=(r.get("L_sel") if not isinstance(r.get("L_sel"), list) else np.mean(r["L_sel"])),
                L_sel_raw=r.get("L_sel"),
                n_treino=r["n_treino"], n_acum=r["n_acumulado"],
                motivo=r["motivo"],
            ))
G = pd.DataFrame(rows)
# p0/p1 chegam como None quando o MATLAB gravou NaN
G["p0"] = pd.to_numeric(G["p0"], errors="coerce")
G["p1"] = pd.to_numeric(G["p1"], errors="coerce")
print(f"[carga] {len(G)} geracoes b4_gen em {G.prob.nunique()} celulas")

# ---------------------------------------------------------------- T1: NaN
# DataProcess.m:19-20  ->  treino_c = ceil(3/4*n_c);  teste_c = n_c - ceil(3/4*n_c)
# |Arc| = n_treino ; |D1| = rr*|Arc| (racional exato) ; |D0| = |Arc| - |D1|
n_arc = G["n_treino"].to_numpy()
n1 = np.rint(G["rr"].to_numpy() * n_arc).astype(int)
n0 = n_arc - n1
G["n1"], G["n0"] = n1, n0
# checagem de consistencia do proprio n1 (rr racional exato)
resid = np.abs(G["rr"].to_numpy() * n_arc - n1)
print(f"[T1a] max |rr*|Arc| - round| = {resid.max():.3e}  (rr racional exato: {(resid<1e-9).sum()}/{len(G)})")
# checagem: n_acumulado == ceil(3/4 n0)+ceil(3/4 n1)  (valida a leitura de DataProcess)
tr_pred = np.ceil(0.75 * n0).astype(int) + np.ceil(0.75 * n1).astype(int)
print(f"[T1b] n_acumulado == ceil(3/4|D0|)+ceil(3/4|D1|): {(tr_pred==G['n_acum'].to_numpy()).sum()}/{len(G)}")

test1 = n1 - np.ceil(0.75 * n1).astype(int)   # = floor(n1/4)
test0 = n0 - np.ceil(0.75 * n0).astype(int)
G["test1"], G["test0"] = test1, test0

p0nan = G["p0"].isna().to_numpy()
p1nan = G["p1"].isna().to_numpy()
print(f"[T1c] p0 NaN: {p0nan.sum()}   p1 NaN: {p1nan.sum()}")
print(f"[T1d] (test1==0): {(test1==0).sum()}   (test0==0): {(test0==0).sum()}")
print(f"[T1e] p0nan <=> test1==0 : {(p0nan==(test1==0)).sum()}/{len(G)}")
print(f"[T1f] p0nan <=> test0==0 : {(p0nan==(test0==0)).sum()}/{len(G)}")
print(f"[T1g] p1nan <=> test0==0 : {(p1nan==(test0==0)).sum()}/{len(G)}")
print("[T1h] celulas com p0 NaN:", G[p0nan].groupby("prob").size().to_dict())

# ------------------------------------------------- T2: identidade do preditor
# TestOut in {0,1}, TestPre = sigmoid in (0,1)
#   erro na classe 1 = mean(1-pred|1)   ;   erro na classe 0 = mean(pred|0)
# Preditor constante c  =>  (erro_1 + erro_0) == 1 exatamente.
s = (G["p0"] + G["p1"]).dropna()
print(f"[T2] p0+p1: media {s.mean():.4f} mediana {s.median():.4f} min {s.min():.4f} max {s.max():.4f}; "
      f"fracao <1: {(s<1).mean():.4f}")
print(f"[T2b] medias globais: p0={G['p0'].mean():.4f}  p1={G['p1'].mean():.4f}  rr mediana={G['rr'].median():.4f}")

# ---------------------------------------- T3: controle POSITIVO (rr > 0.5)
hi = G[G["rr"] > 0.5]
print(f"[T3] geracoes com rr>0.5: {len(hi)}  -> p0 medio {hi['p0'].mean():.4f}  p1 medio {hi['p1'].mean():.4f}")
for lo_hi, sub in [("rr<0.10", G[G["rr"] < 0.10]), ("0.10-0.30", G[(G["rr"] >= .1) & (G["rr"] < .3)]),
                   ("0.30-0.50", G[(G["rr"] >= .3) & (G["rr"] < .5)]), ("rr>0.50", hi)]:
    if len(sub):
        print(f"      {lo_hi:>10s} n={len(sub):5d}  p0={sub['p0'].mean():.4f}  p1={sub['p1'].mean():.4f}")
from scipy.stats import spearmanr
ok = G["p0"].notna() & G["p1"].notna()
print(f"[T3b] spearman(rr,p0) = {spearmanr(G.loc[ok,'rr'], G.loc[ok,'p0']).statistic:+.4f}")
print(f"[T3c] spearman(rr,p1) = {spearmanr(G.loc[ok,'rr'], G.loc[ok,'p1']).statistic:+.4f}")

# -------------------------- T4: teste ORTOGONAL, sem nome — nivel de saida da rede
# H_A (p0 = erro da CATEGORIA II / rotulo 1):
#     mean(pred) = (1-rr)*p1 + rr*(1-p0)
# H_B (p0 = erro da CATEGORIA I / rotulo 0, i.e. os nomes "corretos"):
#     mean(pred) = (1-rr)*p0 + rr*(1-p1)
rr = G["rr"].to_numpy()
mA = (1 - rr) * G["p1"].to_numpy() + rr * (1 - G["p0"].to_numpy())
mB = (1 - rr) * G["p0"].to_numpy() + rr * (1 - G["p1"].to_numpy())
G["mean_pred_HA"], G["mean_pred_HB"] = mA, mB
print(f"[T4] previsao do nivel medio de saida da rede: H_A {np.nanmean(mA):.4f}  |  H_B {np.nanmean(mB):.4f}")

# instrumento independente 1: L_sel do ramo 4 (1 filho uniformemente sorteado)
r4 = G[(G["ramo"] == 4) & G["L_sel"].notna()]
print(f"[T4a] ramo4 n={len(r4)}  mean L_sel={r4['L_sel'].mean():.4f}  mediana={r4['L_sel'].median():.4f}")
eA = np.abs(r4["L_sel"].to_numpy() - r4["mean_pred_HA"].to_numpy())
eB = np.abs(r4["L_sel"].to_numpy() - r4["mean_pred_HB"].to_numpy())
print(f"[T4b] |L_sel - previsao| ramo4:  H_A MAE={np.nanmean(eA):.4f}   H_B MAE={np.nanmean(eB):.4f}   "
      f"H_A vence em {(eA<eB).sum()}/{np.isfinite(eA).sum()}")

# instrumento independente 2: media do pred_confianca da sonda (camada 3)
sonda_rows = []
for pr in probs:
    d = os.path.join(RES, pr, "42")
    pqf = glob.glob(os.path.join(d, "*__surrogate.parquet"))[0]
    df = pd.read_parquet(pqf, columns=["geracao", "pred_confianca"])
    ag = df.groupby("geracao")["pred_confianca"].agg(["mean", "median", "size"]).reset_index()
    ag["prob"] = pr
    sonda_rows.append(ag)
S = pd.concat(sonda_rows, ignore_index=True).rename(
    columns={"mean": "L_sonda_mean", "median": "L_sonda_med", "size": "n_sonda", "geracao": "g"})
J = G.merge(S, on=["prob", "g"], how="inner")
print(f"[T4c] join geracao x bloco de sonda: {len(J)} linhas; "
      f"mean L_sonda={J['L_sonda_mean'].mean():.4f} mediana={J['L_sonda_med'].median():.4f}")
eA2 = np.abs(J["L_sonda_mean"] - J["mean_pred_HA"])
eB2 = np.abs(J["L_sonda_mean"] - J["mean_pred_HB"])
print(f"[T4d] |L_sonda - previsao|: H_A MAE={np.nanmean(eA2):.4f}  H_B MAE={np.nanmean(eB2):.4f}  "
      f"H_A vence em {(eA2<eB2).sum()}/{np.isfinite(eA2).sum()}")
print(f"[T4e] spearman(L_sonda_mean, mean_pred_HA) = {spearmanr(J['L_sonda_mean'], J['mean_pred_HA'], nan_policy='omit').statistic:+.4f}")
print(f"[T4f] spearman(L_sonda_mean, mean_pred_HB) = {spearmanr(J['L_sonda_mean'], J['mean_pred_HB'], nan_policy='omit').statistic:+.4f}")

# ------------------- T5: o gate logado bate com o codigo SEM re-nomear nada
a = G["tr"].to_numpy(); b = 1 - a
p0v = G["p0"].to_numpy(); p1v = G["p1"].to_numpy()
pred_ramo = np.where(p0v < 0.4, 1,
             np.where((p1v < a) & (p0v < b), 1,
              np.where((p0v > b) & (p1v < a), 2,
               np.where(p1v > b, 3, 4))))
# NaN em p0 -> nenhuma condicao verdadeira -> else (ramo 4)
pred_ramo = np.where(np.isnan(p0v) | np.isnan(p1v), 4, pred_ramo)
print(f"[T5] ramo reconstruido literalmente de SAS.m:27-57 com p0/p1 COMO LOGADOS: "
      f"{(pred_ramo==G['ramo'].to_numpy()).sum()}/{len(G)}")
# contraprova: e se trocarmos p0<->p1 na expressao?
pred_sw = np.where(p1v < 0.4, 1,
           np.where((p0v < a) & (p1v < b), 1,
            np.where((p1v > b) & (p0v < a), 2,
             np.where(p0v > b, 3, 4))))
pred_sw = np.where(np.isnan(p0v) | np.isnan(p1v), 4, pred_sw)
print(f"[T5b] mesma expressao com p0<->p1 TROCADOS: {(pred_sw==G['ramo'].to_numpy()).sum()}/{len(G)}")

# ------------------- T6: controle negativo — p1 nunca NaN / |D0| nunca esvazia
print(f"[T6] min |D0| = {n0.min()}  min |D1| = {n1.min()}  min test0 = {test0.min()}  min test1 = {test1.min()}")

G.drop(columns=["L_sel_raw"]).to_csv(os.path.join(OUT, "a12_geracoes_indep.csv"), index=False)
J[["prob", "g", "rr", "p0", "p1", "ramo", "L_sel", "L_sonda_mean", "L_sonda_med",
   "mean_pred_HA", "mean_pred_HB"]].to_csv(os.path.join(OUT, "a12_join_sonda.csv"), index=False)
print("[ok] CSVs escritos em", OUT)
