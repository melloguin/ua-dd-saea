#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 2: a QUERY-JOIA da familia GP-BO.
Recomputa EIM_Euclidean (Apendice A do paper) sobre a pop FINAL do GA (camada 3, DEF-C2)
e confronta com eim_best / eim_mediana_pool / infill logados no (6).
Tambem: bracketing da frente ND sob float32 (nd_std <= n_front <= nd_strict), U11 (erro de
fantasia do infill), clone-share do pool (hazard anti-clustering ausente, B10.7).
Saidas: eim_gens.csv (1 linha/geracao) + eim_celula.csv (1 linha/celula).
"""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.stats import norm

BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"


def nd_std(Y):
    keep = np.ones(len(Y), bool)
    for i in range(len(Y)):
        if ((Y <= Y[i]).all(1) & (Y < Y[i]).any(1)).any():
            keep[i] = False
    return keep


def nd_weak_seq(Y):
    """Semantica do `paretofront` (MATLAB FileExchange 17251) citado no paper §V-B(5)b:
    dominancia FRACA (all <=), varredura sequencial -> duplicatas exatas colapsam na 1a."""
    n = len(Y)
    front = np.ones(n, bool)
    for i in range(n):
        if not front[i]:
            continue
        tail = Y[i + 1:]
        alive = front[i + 1:]
        if len(tail) == 0:
            continue
        d_ij = (Y[i] <= tail).all(1) & alive
        d_ji = (tail <= Y[i]).all(1) & alive
        kill_i = d_ji & ~d_ij
        idx = np.flatnonzero(kill_i)
        if idx.size:
            k = idx[0]
            sel = np.flatnonzero(d_ij[:k])
            front[i + 1 + sel] = False
            front[i] = False
        else:
            sel = np.flatnonzero(d_ij)
            front[i + 1 + sel] = False
    return front


def nd_strict_count(Y):
    keep = np.ones(len(Y), bool)
    for i in range(len(Y)):
        if ((Y < Y[i]).all(1)).any():
            keep[i] = False
    return int(keep.sum())


def eim_euclidean(u, s, Fr):
    """Apendice A: EIM=(F-1*u).*gausscdf(lam)+1*s.*gausspdf(lam); y=min(sqrt(sum(EIM.^2,2)))."""
    lam = (Fr[None, :, :] - u[:, None, :]) / s[:, None, :]
    E = (Fr[None, :, :] - u[:, None, :]) * norm.cdf(lam) + s[:, None, :] * norm.pdf(lam)
    E = np.nan_to_num(E, nan=0.0)          # guard [IMPL] EIM(isnan(EIM))=0
    return np.sqrt((E ** 2).sum(2)).min(1)


def do_cell(prob):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    recs = [json.loads(l) for l in open(f"{b}.jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    M, D = hdr["M"], hdr["D"]
    gens = {r["geracao"]: r for r in recs if r.get("rec") == "c238_gen"}
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    F = real[[f"f{i}" for i in range(M)]].values.astype(np.float64)
    cols = ["regime", "geracao", "real_solution_id"] + [f"mu_{i}" for i in range(M)] + \
           [f"sigma_{i}" for i in range(M)]
    sur = pq.read_table(f"{b}__surrogate.parquet", columns=cols).to_pandas()
    on = sur[sur.regime == "online"]
    grp = dict(list(on.groupby("geracao")))
    rows = []
    for g in sorted(gens):
        r = gens[g]
        npre = r["n_amostra"]
        Y = F[:npre]
        mask = nd_weak_seq(Y)          # rotina do paper (paretofront FEX-17251)
        n_lo = int(nd_std(Y).sum())
        nstrict = nd_strict_count(Y)
        mn = np.array(r["norm_min"], float)
        rg = np.array(r["norm_range_efetivo"], float)
        Fr = (Y[mask] - mn) / rg
        sub = grp[g]
        u = sub[[f"mu_{i}" for i in range(M)]].values.astype(np.float64)
        s = sub[[f"sigma_{i}" for i in range(M)]].values.astype(np.float64)
        v = eim_euclidean(u, s, Fr)
        rsid = sub.real_solution_id.values
        pos = np.where(rsid == r["infill_sid"])[0]
        j = int(pos[0]) if len(pos) else 0
        eb = r["eim_best"]
        den = max(abs(eb), 1e-300)
        vmax = float(v.max())
        # U11 no espaco CRU
        mu_cru = u[j] * rg + mn
        s_cru = s[j] * rg
        f_real = F[int(r["infill_sid"])]
        rows.append(dict(
            problema=prob, geracao=g, D=D, M=M, n_amostra=npre,
            n_front=r["n_front"], nd_weak=int(mask.sum()), nd_std=n_lo, nd_strict=nstrict,
            front_exato=int(mask.sum()) == r["n_front"],
            front_bracket=(min(n_lo, int(mask.sum())) <= r["n_front"] <= nstrict),
            eim_best=eb, eim_rec_max=vmax, eim_rec_infill=float(v[j]),
            rel_max=abs(vmax - eb) / den, rel_infill=abs(v[j] - eb) / den,
            abs_max=abs(vmax - eb),
            argmax_eh_infill=int(np.argmax(v)) == j,
            gap_argmax=(vmax - v[j]) / max(vmax, 1e-300),
            eim_med_rec=float(np.median(v)), eim_med_log=r["eim_mediana_pool"],
            rel_med=abs(np.median(v) - r["eim_mediana_pool"]) / max(abs(r["eim_mediana_pool"]), 1e-300),
            eim_pool_min=float(v.min()), eim_pool_std=float(v.std()),
            pool_clones=int(pd.notna(rsid).sum()) - 1, pool_n=len(sub),
            u11_err=float(np.max(np.abs(mu_cru - f_real))),
            u11_err_rel=float(np.max(np.abs(mu_cru - f_real) / np.maximum(np.abs(f_real), 1e-12))),
            u11_otimista=int((mu_cru < f_real).sum()), u11_M=M,
            u11_cob=int((np.abs(mu_cru - f_real) <= 1.96 * s_cru).sum()),
            s_best_min=float(s[j].min()),
        ))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    allr = []
    for p in sorted(os.listdir(BASE)):
        d = do_cell(p)
        allr.append(d)
        print(f"OK {p}: gens={len(d)} front_exato={d.front_exato.sum()} "
              f"rel_max<1e-5={(d.rel_max<1e-5).sum()} argmax={d.argmax_eh_infill.sum()}", flush=True)
    A = pd.concat(allr)
    A.to_csv(f"{OUT}/eim_gens.csv", index=False)
    g = A.groupby("problema")
    S = pd.DataFrame(dict(
        n_gens=g.size(),
        front_exato=g.front_exato.sum(), front_bracket=g.front_bracket.sum(),
        rel_max_lt1e5=g.apply(lambda x: int((x.rel_max < 1e-5).sum()), include_groups=False),
        rel_max_med=g.rel_max.median(), rel_max_max=g.rel_max.max(),
        rel_inf_lt1e5=g.apply(lambda x: int((x.rel_infill < 1e-5).sum()), include_groups=False),
        rel_inf_med=g.rel_infill.median(),
        argmax_ok=g.argmax_eh_infill.sum(),
        gap_gt1e6=g.apply(lambda x: int((x.gap_argmax > 1e-6).sum()), include_groups=False),
        gap_med=g.gap_argmax.median(), gap_max=g.gap_argmax.max(),
        rel_med_lt1e5=g.apply(lambda x: int((x.rel_med < 1e-5).sum()), include_groups=False),
        clones_tot=g.pool_clones.sum(), pool_n=g.pool_n.first(),
        clone_share=g.apply(lambda x: float(x.pool_clones.sum() / (x.pool_n.sum())), include_groups=False),
        u11_err_med=g.u11_err.median(), u11_err_rel_med=g.u11_err_rel.median(),
        u11_otim_frac=g.apply(lambda x: float(x.u11_otimista.sum() / (x.u11_M.sum())), include_groups=False),
        u11_cob_frac=g.apply(lambda x: float(x.u11_cob.sum() / (x.u11_M.sum())), include_groups=False),
        eim_best_ini=g.eim_best.first(), eim_best_fim=g.eim_best.last(),
        eim_med_ini=g.eim_med_log.first(), eim_med_fim=g.eim_med_log.last(),
        s_best_min=g.s_best_min.min(),
    ))
    S.to_csv(f"{OUT}/eim_celula.csv")
    print(S.to_string())
