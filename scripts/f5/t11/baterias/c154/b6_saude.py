"""B6 — Saude: calibracao NOS INFILLS, trajetorias, escada por degrau,
assinatura exploratoria (J24). s42 + smoke de teto. READ-ONLY."""
import json
import numpy as np
import pandas as pd
from pathlib import Path

R = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154")
T = Path("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/teto_c154"
         "/experiments/main/c154")
TRJ = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/trajetorias")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c154")

alvos = [(p.name, R / p.name / "42") for p in sorted(R.iterdir()) if p.is_dir()]
alvos.append(("DTLZ2", T))

inf, esc, dm = [], [], []
for prob, base in alvos:
    st = f"exp_main_c154_{prob}_42"
    L = [json.loads(l) for l in open(base / f"{st}.jsonl")]
    hdr = [x for x in L if x.get("rec") == "header"][0]
    M = hdr["M"]
    real = pd.read_parquet(base / f"{st}__real.parquet")
    sur = pd.read_parquet(base / f"{st}__surrogate.parquet")
    on = sur[(sur.regime == "online") & sur.real_solution_id.notna()]
    idx = on.real_solution_id.astype(int).to_numpy()
    F = real.loc[idx, [f"f{j}" for j in range(M)]].to_numpy()
    MU = on[[f"mu_{j}" for j in range(M)]].to_numpy()
    SG = on[[f"sigma_{j}" for j in range(M)]].to_numpy()
    for j in range(M):
        e = np.abs(MU[:, j] - F[:, j])
        inf.append(dict(prob=prob, obj=j, n=len(e),
                        cob=float((e <= 1.96 * SG[:, j]).mean()),
                        z_med=float(np.median(e / SG[:, j])),
                        wape_fant=float(e.sum() / np.abs(F[:, j]).sum())))
    # escada por degrau
    for x in L:
        if x.get("rec") == "rs_runtimeerror_fallback" or \
                (x.get("rec") == "guard" and
                 x.get("name") == "rs_runtimeerror_fallback"):
            esc.append(dict(prob=prob, degrau=x.get("degrau", x.get("nivel")),
                            pop=x.get("pop_size"), tries=x.get("max_tries"),
                            it=x.get("it"), s=x.get("amostra", x.get("s")),
                            k=x.get("k_encontrados", x.get("n_encontrados"))))
    for d in [x for x in L if x.get("rec") == "decision"]:
        if d.get("dist_min_arquivo") is not None:
            dm.append(dict(prob=prob, it=d["it"], d=d["dist_min_arquivo"]))

I = pd.DataFrame(inf)
I.to_csv(OUT / "c154_infill_calib.csv", index=False)
print("=" * 78)
print("CALIBRACAO ONDE IMPORTA — os pontos de INFILL escolhidos")
print("=" * 78)
s42 = I[I.prob != "DTLZ2"]
print(f"s42 ({len(s42)} celula-objetivo, {int(s42.n.sum())} predicoes):")
print(f"  cobertura +-1.96sigma: mediana {s42.cob.median():.4f}  "
      f"min {s42.cob.min():.4f} ({s42.loc[s42.cob.idxmin(),'prob']}"
      f"-obj{int(s42.loc[s42.cob.idxmin(),'obj'])})  >=0.90: "
      f"{int((s42.cob>=0.9).sum())}/{len(s42)}")
print(f"  |mu-f|/sigma mediano : {s42.z_med.median():.4f}")
t = I[I.prob == "DTLZ2"]
print(f"teto/DTLZ2 ({len(t)} obj, {int(t.n.sum())} predicoes): cobertura "
      f"{[round(v,4) for v in t.cob]}  z_med {[round(v,3) for v in t.z_med]}")

E = pd.DataFrame(esc)
E.to_csv(OUT / "c154_escada.csv", index=False)
print("\n" + "=" * 78)
print("J10 — ESCADA rs_runtimeerror_fallback por DEGRAU")
print("=" * 78)
print(f"total = {len(E)} disparos")
if len(E):
    print("  campos disponiveis:", [c for c in E.columns
                                    if E[c].notna().any()])
    for c in ["degrau", "pop", "tries"]:
        if E[c].notna().any():
            print(f"  por {c}: {E[c].value_counts(dropna=False).to_dict()}")
    print(f"  por celula: {E.prob.value_counts().to_dict()}")
    if E.k.notna().any():
        print(f"  K encontrados (deficit): "
              f"{E.k.value_counts().sort_index().to_dict()}")
    if E.s.notna().any():
        print(f"  amostra s que falha: "
              f"{E.s.value_counts().sort_index().to_dict()}")

D = pd.DataFrame(dm)
print("\n" + "=" * 78)
print("J24 — dist_min_arquivo do ponto ESCOLHIDO (em [0,1]^D)")
print("=" * 78)
if len(D):
    g = D.groupby("prob").d.agg(["median", "min", "max", "size"])
    print(g.to_string(float_format=lambda v: f"{v:.4f}"))
    print(f"  pontos a distancia ZERO: {int((D.d==0).sum())} de {len(D)}")

print("\n" + "=" * 78)
print("TRAJETORIAS — monotonicidade de IGD+/HV (insumo f5/trajetorias)")
print("=" * 78)
tot = viol = 0
for prob, _ in alvos:
    f = TRJ / f"main_c154_{prob}_42.json"
    if not f.exists():
        print(f"  {prob:10s} SEM arquivo de trajetoria")
        continue
    j = json.load(open(f))
    ser = j.get("igd_plus") or j.get("igd+") or j.get("curva") or []
    if isinstance(ser, dict):
        ser = ser.get("valores", [])
    v = [x for x in ser if isinstance(x, (int, float))]
    d = np.diff(v)
    tot += len(d)
    viol += int((d > 1e-12).sum())
    print(f"  {prob:10s} n={len(v):3d} checkpoints  violacoes IGD+ = "
          f"{int((d>1e-12).sum())}  ({v[0]:.4g} -> {v[-1]:.4g}, "
          f"{100*(v[-1]/v[0]-1):+.1f}%)" if len(v) > 1 else
          f"  {prob:10s} serie vazia/curta")
print(f"  TOTAL: {viol} violacoes em {tot} transicoes")
