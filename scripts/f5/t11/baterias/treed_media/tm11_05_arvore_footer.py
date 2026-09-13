#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T11/treed_media — 05: (a) identidade da ARVORE treed x c311 (C15, re-medida);
(b) rito de footer / upload_status; (c) projecao do custo do checkpoint. READ-ONLY."""
import json, os, glob
import numpy as np, pandas as pd

R = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = os.path.dirname(os.path.abspath(__file__))

# ---------- (a) a arvore e a mesma? (pontos sonda onde o c311 tem sigma NaN) -------
rows = []
for lab in sorted(os.listdir(os.path.join(R, "treed_media"))):
    dt = os.path.join(R, "treed_media", lab, "42")
    dc = os.path.join(R, "c311", lab, "42")
    if not os.path.isdir(dc):
        rows.append(dict(label=lab, status="SEM PAR c311")); continue
    bt = glob.glob(os.path.join(dt, "*__surrogate.parquet"))[0]
    bc = glob.glob(os.path.join(dc, "*__surrogate.parquet"))[0]
    mt = json.load(open(glob.glob(os.path.join(dt, "*_42.manifest.json"))[0]))
    mc = json.load(open(glob.glob(os.path.join(dc, "*_42.manifest.json"))[0]))
    t = pd.read_parquet(bt); c = pd.read_parquet(bc)
    st = t[t.regime == "sonda"].reset_index(drop=True)
    sc = c[c.regime == "sonda"].reset_index(drop=True)
    M = len([x for x in t.columns if x.startswith("mu_")])
    xc = sorted([x for x in t.columns if x.startswith("x") and x[1:].isdigit()],
                key=lambda s: int(s[1:]))
    # o c311 tem 2 blocos: pega o PRIMEIRO (build) e o ULTIMO (final) por posicao
    nb = len(sc) // len(st)
    tot = ident = 0
    dmax = 0.0
    for b in range(nb):
        blk = sc.iloc[b * len(st):(b + 1) * len(st)].reset_index(drop=True)
        assert np.array_equal(blk[xc].to_numpy(), st[xc].to_numpy()), "X da sonda difere"
        for j in range(M):
            m_nan = blk["sigma_%d" % j].isna().to_numpy()   # folha SEM GP no c311
            a = st["mu_%d" % j].to_numpy()[m_nan]
            bb = blk["mu_%d" % j].to_numpy()[m_nan]
            tot += int(m_nan.sum()); ident += int((a == bb).sum())
            if m_nan.sum() and (a != bb).any():
                dmax = max(dmax, float(np.abs(a - bb)[a != bb].max()))
    rows.append(dict(label=lab, status="ok", n_blocos_c311=nb,
                     doe_igual=(mt["doe_hash"] == mc["doe_hash"]),
                     sonda_hash_igual=(mt["sonda"]["x_hash"] == mc["sonda"]["x_hash"]),
                     pts_sem_GP=tot, identicos=ident,
                     pct=round(100.0 * ident / tot, 4) if tot else None,
                     divergentes=tot - ident, dmax=dmax))
da = pd.DataFrame(rows)
pd.set_option("display.width", 260, "display.max_columns", 40)
print("=== C15 RE-MEDIDO: a arvore do treed_media E a do c311? ===")
print(da.to_string(index=False))
ok = da[da.status == "ok"]
print("TOTAL pts sem GP=%d | identicos=%d (%.4f%%) | divergentes=%d | max|dmu|=%.3g" %
      (ok.pts_sem_GP.sum(), ok.identicos.sum(),
       100.0 * ok.identicos.sum() / ok.pts_sem_GP.sum(),
       ok.pts_sem_GP.sum() - ok.identicos.sum(), ok.dmax.max()))
da.to_csv(os.path.join(OUT, "tm11_arvore_identidade.csv"), index=False)

# ---------- (b) rito de footer / upload_status ----------
rows = []
for lab in sorted(os.listdir(os.path.join(R, "treed_media"))):
    d = os.path.join(R, "treed_media", lab, "42")
    mfp = glob.glob(os.path.join(d, "*_42.manifest.json"))[0]
    m = json.load(open(mfp))
    ev = [json.loads(x) for x in open(glob.glob(os.path.join(d, "*.jsonl"))[0]) if x.strip()]
    ft = [e for e in ev if e.get("rec") == "footer"]
    rows.append(dict(label=lab, n_eventos=len(ev), n_footers=len(ft),
                     footer_motivo=(ft[0].get("motivo") if ft else "<SEM FOOTER>"),
                     motivo_parada=m.get("motivo_parada"), status=m.get("status"),
                     upload=json.dumps(m.get("upload_status"))[:60],
                     created=m.get("created_at"),
                     ultimo_ev_ts=ev[-1]["ts"]))
dfo = pd.DataFrame(rows)
print("\n=== rito de escrita (C16) ===")
print(dfo.to_string(index=False))
dfo.to_csv(os.path.join(OUT, "tm11_footers.csv"), index=False)

# ---------- (c) custo do checkpoint: modelo linear e projecao as 10 celulas ----
SMK = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/sweep-big-mvns/treed_media"
ck = [json.loads(x) for x in open(os.path.join(SMK, "exp_sweep-big-mvns_treed_media_ZDT4_42.jsonl"))
      if x.strip() and json.loads(x).get("rec") == "checkpoint"]
n = np.array([e["n_linhas_terceira"] for e in ck], float)
t = np.array([e["tempo_checkpoint_s"] for e in ck], float)
b, a = np.polyfit(n, t, 1)
print("\n=== custo do checkpoint (DI-43) — regressao sobre os 10 do smoke ===")
print("t_ckpt(s) = %.4f + %.3g * n_linhas_③   (R2=%.4f)" %
      (a, b, 1 - ((t - (a + b * n)) ** 2).sum() / ((t - t.mean()) ** 2).sum()))
proj = []
for _, r in pd.read_csv(os.path.join(OUT, "tm11_mecanismo_s42.csv")).iterrows():
    lab = r["label"]
    d = os.path.join(R, "treed_media", lab, "42")
    r3 = pd.read_parquet(glob.glob(os.path.join(d, "*__surrogate.parquet"))[0])
    bs = r3[r3.regime != "sonda"]
    cum = bs.groupby("geracao").size().cumsum()
    ns = np.array([cum.loc[g] + 20000 for g in range(100, 1001, 100)], float)
    custo = float((a + b * ns).sum())
    proj.append(dict(label=lab, n3=len(r3), wall_s42=r["wall"],
                     custo_ckpt_proj=round(custo, 2),
                     wall_proj=round(r["wall"] + custo, 2),
                     inflacao_pct=round(100 * custo / r["wall"], 1)))
dp = pd.DataFrame(proj)
print(dp.to_string(index=False))
print("MEDIANA inflacao = %.1f%% | soma custo = %.1f s nas 10 celulas" %
      (dp.inflacao_pct.median(), dp.custo_ckpt_proj.sum()))
dp.to_csv(os.path.join(OUT, "tm11_checkpoint_projecao.csv"), index=False)
