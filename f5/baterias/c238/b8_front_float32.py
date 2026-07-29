#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 8: por que a frente ND recomputada da (1) nao bate com
`n_front` do (6) em 463/7020 geracoes (DTLZ4 240, ZDT6 185, MMF11_L 38) — e por que
isso derruba a identidade EIM SO no ZDT6.

Hipotese: a (1) e exportada em float32 (D53) enquanto o MATLAB computou a frente em
float64. Em problemas cujo mapa objetivo satura/underflowa (DTLZ4 alpha=100 -> x^100;
ZDT6 sin^6(6 pi x)), a quantizacao float32 CRIA empates que nao existiam em float64 ->
a rotina `paretofront` (dominancia fraca) colapsa/mantem pontos diferentes.

Testes:
 (a) censo de empates: linhas f DUPLICADAS exatas em float32 e componentes == 0 exato;
 (b) margem de dominancia: margin_i = min_j max_k (Y_ik - Y_jk); i e ND sse margin_i>0.
     Conta pontos "ambiguos" (|margin| <= tol_f32 = 6e-8 * escala) — os que trocariam de
     lado sob o arredondamento float32;
 (c) reconstrucao dirigida: se nd_weak > n_front_log, remove da frente os (nd_weak -
     n_front_log) pontos de MENOR margem (os menos robustos) e recomputa a identidade EIM.
     Se fecha -> mecanismo PROVADO.
Saidas: front_float32.csv (1 linha/geracao das celulas discordantes) + front_resumo.csv
"""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
import importlib.util

spec = importlib.util.spec_from_file_location(
    "b2", "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238/b2_eim_identidade.py")
b2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b2)

BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"
EPS32 = np.finfo(np.float32).eps          # 1.1920929e-07


def margens(Y):
    """margin_i = min_{j!=i} max_k (Y_ik - Y_jk). >0 => i nao e fracamente dominado."""
    n = len(Y)
    M = np.full(n, np.inf)
    for i in range(n):
        d = (Y[i] - Y).max(1)
        d[i] = np.inf
        M[i] = d.min()
    return M


def do_cell(prob, detalhe):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    recs = [json.loads(l) for l in open(f"{b}.jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    M, D = hdr["M"], hdr["D"]
    gens = [r for r in recs if r.get("rec") == "c238_gen"]
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    F32 = real[[f"f{i}" for i in range(M)]].values          # float32 nativo
    F = F32.astype(np.float64)
    cols = ["regime", "geracao", "real_solution_id"] + [f"mu_{i}" for i in range(M)] + \
           [f"sigma_{i}" for i in range(M)]
    sur = pq.read_table(f"{b}__surrogate.parquet", columns=cols).to_pandas()
    grp = dict(list(sur[sur.regime == "online"].groupby("geracao")))

    # (a) censo de empates no arquivo COMPLETO
    dfF = pd.DataFrame(F)
    n_dup = int(dfF.duplicated().sum())
    n_zero_exato = int((F == 0).sum())
    # menor |f| nao-nulo por objetivo (proximidade do subnormal float32)
    absF = np.abs(F); nz = absF[absF > 0]
    min_abs = float(nz.min()) if nz.size else np.nan

    rows = []
    n_amb_tot = 0
    for r in gens:
        npre = r["n_amostra"]
        Y = F[:npre]
        wk = b2.nd_weak_seq(Y)
        nwk = int(wk.sum())
        nlog = r["n_front"]
        if not detalhe and nwk == nlog:
            continue
        mg = margens(Y)
        esc = float(np.abs(Y).max()) or 1.0
        tol = EPS32 * esc
        n_amb = int((np.abs(mg) <= tol).sum())
        n_amb_tot += n_amb
        # (c) reconstrucao dirigida
        mn = np.array(r["norm_min"], float); rg = np.array(r["norm_range_efetivo"], float)
        sub = grp[r["geracao"]]
        u = sub[[f"mu_{i}" for i in range(M)]].values.astype(np.float64)
        s = sub[[f"sigma_{i}" for i in range(M)]].values.astype(np.float64)
        eb = r["eim_best"]; den = max(abs(eb), 1e-300)
        idx = np.flatnonzero(wk)
        Fr0 = (Y[idx] - mn) / rg
        rel0 = abs(float(b2.eim_euclidean(u, s, Fr0).max()) - eb) / den
        rel1 = np.nan; ndrop = nwk - nlog
        if ndrop > 0:
            ordem = idx[np.argsort(mg[idx])]          # menor margem primeiro
            keep = np.setdiff1d(idx, ordem[:ndrop])
            Fr1 = (Y[keep] - mn) / rg
            rel1 = abs(float(b2.eim_euclidean(u, s, Fr1).max()) - eb) / den
        rows.append(dict(problema=prob, geracao=r["geracao"], n_amostra=npre, M=M,
                         n_front_log=nlog, nd_weak=nwk, delta=nwk - nlog,
                         n_ambiguos=n_amb, margem_min_front=float(mg[idx].min()),
                         tol_f32=tol, rel_weak=rel0, rel_podada=rel1,
                         fecha_weak=rel0 < 1e-5, fecha_podada=(rel1 < 1e-5) if ndrop > 0 else None))
    return rows, dict(problema=prob, M=M, D=D, n_gens=len(gens), n_dup_f32=n_dup,
                      n_f_zero_exato=n_zero_exato, min_abs_f_naonulo=min_abs,
                      n_linhas=len(F))


if __name__ == "__main__":
    allr, res = [], []
    for p in sorted(os.listdir(BASE)):
        rows, s = do_cell(p, detalhe=False)
        allr += rows
        s["n_gens_discordantes"] = len(rows)
        res.append(s)
        print(f"OK {p}: discordantes={len(rows)} dup_f32={s['n_dup_f32']} "
              f"zeros={s['n_f_zero_exato']} min|f|={s['min_abs_f_naonulo']:.3e}", flush=True)
    A = pd.DataFrame(allr); A.to_csv(f"{OUT}/front_float32.csv", index=False)
    R = pd.DataFrame(res); R.to_csv(f"{OUT}/front_resumo.csv", index=False)
    print("\n", R.to_string(index=False))
    if len(A):
        print("\n=== geracoes discordantes ===")
        g = A.groupby("problema")
        print(pd.DataFrame(dict(
            n=g.size(), delta_min=g.delta.min(), delta_max=g.delta.max(),
            delta_med=g.delta.median(), amb_med=g.n_ambiguos.median(),
            cobre_delta=g.apply(lambda x: int((x.n_ambiguos >= x.delta.abs()).sum()),
                                include_groups=False),
            fecha_weak=g.fecha_weak.sum(),
            fecha_podada=g.fecha_podada.sum(),
            rel_weak_med=g.rel_weak.median(), rel_weak_max=g.rel_weak.max(),
            rel_pod_med=g.rel_podada.median(), rel_pod_max=g.rel_podada.max(),
        )).to_string())
