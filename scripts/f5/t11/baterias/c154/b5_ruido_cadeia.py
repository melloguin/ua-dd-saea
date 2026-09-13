"""B5 — J4: a cadeia causal do RUIDO INFERIDO (achado-de-ouro da F5), re-medida.

Hipotese: em benchmark DETERMINISTICO a MLL tem 2 otimos — modo interpolante
(noise no piso 1e-4) e modo suavizante, que REATRIBUI sinal a ruido: `noise`
sobe e `outputscale` DESCE junto. Como a sigma exportada e VAR-GP (sem ruido),
ela encolhe com o outputscale => o modelo fica MAIS CONFIANTE sem ficar melhor
=> a cobertura +-1.96sigma CAI.
Teste: isolar os saltos de ruido >=5x entre blocos de sonda CONSECUTIVOS e
medir delta(outputscale), delta(sigma), delta(cobertura), delta(WAPE).
READ-ONLY.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

R = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154")
T = Path("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/teto_c154"
         "/experiments/main/c154")
ART = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c154")


def cell(prob, base):
    st = f"exp_main_c154_{prob}_42"
    L = [json.loads(l) for l in open(base / f"{st}.jsonl")]
    hdr = [x for x in L if x.get("rec") == "header"][0]
    M = hdr["M"]
    dec = [x for x in L if x.get("rec") == "decision"]
    hp = {}
    for d in dec:
        for j, o in enumerate((d.get("modelo_hp") or {}).get("por_objetivo", [])):
            hp[(d["it"], j)] = (o.get("noise"), o.get("outputscale"))
    sur = pd.read_parquet(base / f"{st}__surrogate.parquet")
    sn = sur[sur.regime == "sonda"]
    gab = pd.read_parquet(ART / f"sonda_{prob}.parquet")
    F = gab[[f"f{j}" for j in range(M)]].to_numpy()[:2000]
    rows = []
    for g, blk in sn.groupby("geracao"):
        g = int(g)
        mu = blk[[f"mu_{j}" for j in range(M)]].to_numpy()
        sg = blk[[f"sigma_{j}" for j in range(M)]].to_numpy()
        for j in range(M):
            n, o = hp.get((g, j), (None, None))
            err = np.abs(mu[:, j] - F[:, j])
            rows.append(dict(prob=prob, ger=g, obj=j, noise=n, outsc=o,
                             sigma=float(np.median(sg[:, j])),
                             cob=float((err <= 1.96 * sg[:, j]).mean()),
                             wape=float(err.sum() / np.abs(F[:, j]).sum())))
    return pd.DataFrame(rows)


fr = [cell(p, R / p / "42") for p in sorted(x.name for x in R.iterdir()
                                            if x.is_dir())]
fr.append(cell("DTLZ2", T).assign(prob="DTLZ2(teto)"))
df = pd.concat(fr, ignore_index=True).dropna(subset=["noise"])
df.to_csv(OUT / "c154_ruido_cadeia.csv", index=False)

sal = []
for (p, j), g in df.groupby(["prob", "obj"]):
    g = g.sort_values("ger").reset_index(drop=True)
    for i in range(1, len(g)):
        a, b = g.loc[i - 1], g.loc[i]
        if a.noise > 0 and b.noise / a.noise >= 5:
            sal.append(dict(prob=p, obj=j, g0=int(a.ger), g1=int(b.ger),
                            razao=b.noise / a.noise,
                            d_outsc=b.outsc / a.outsc - 1,
                            d_sigma=b.sigma / a.sigma - 1,
                            d_cob=b.cob - a.cob, d_wape=b.wape / a.wape - 1))
S = pd.DataFrame(sal)
S.to_csv(OUT / "c154_saltos_ruido.csv", index=False)

print("=" * 78)
print("J4 — SALTOS DE RUIDO >=5x entre blocos de sonda CONSECUTIVOS")
print("=" * 78)
print(f"n = {len(S)} saltos, em {S.prob.nunique()} celulas / "
      f"{len(S.groupby(['prob','obj']))} celula-objetivo\n")
print(f"{'grandeza':<24}{'cai em':>10}{'mediana':>12}")
for col, nome, mediana_pct in [
        ("d_outsc", "outputscale", True), ("d_sigma", "sigma (mediana)", True),
        ("d_cob", "cobertura (p.p.)", False), ("d_wape", "WAPE", True)]:
    v = S[col]
    cai = int((v < 0).sum())
    med = v.median() * (100 if mediana_pct else 100)
    unid = "%" if mediana_pct else " p.p."
    print(f"{nome:<24}{cai:>4}/{len(S):<5}{med:>10.1f}{unid}")
print(f"\nrazao de ruido: mediana {S.razao.median():.1f}x  max {S.razao.max():.1f}x")
print("\nexemplares (maiores saltos):")
print(S.nlargest(6, "razao")[["prob", "obj", "g0", "g1", "razao", "d_outsc",
                              "d_sigma", "d_cob"]]
      .to_string(index=False, float_format=lambda v: f"{v:.4f}"))

print("\n### piso 1e-4 e amplitude do ruido por celula-objetivo")
z = df.groupby(["prob", "obj"]).agg(
    n=("noise", "size"), piso=("noise", lambda s: int((s <= 1.0001e-4).sum())),
    rmin=("noise", "min"), rmax=("noise", "max"),
    cob_fim=("cob", "last")).reset_index()
z["razao"] = z.rmax / z.rmin
print(z.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
