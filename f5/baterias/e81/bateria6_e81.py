#!/usr/bin/env python
"""bateria6_e81 — o CONTRAFACTUAL G5 operacionalizado POR DADO: se Sigma->0 os caminhos
amostrados colapsariam na media e o rank-0 do NSGA-II interno seria o front de mu.
Mede-se a fracao do front exportado que e nao-dominada em mu (e se o PONTO ESCOLHIDO
e dominado em mu). Mais: reconciliacao footer/manifesto/gates e semantica da 2a camada.

READ-ONLY. Saidas: e81_g5_contrafactual.csv · e81_reconciliacao.csv
"""
import json, os
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
OUT = os.path.join(REPO, "f5", "baterias", "e81")


def nd_mask(F):
    """mascara booleana dos nao-dominados (minimizacao), O(N^2) — N<=2000 aqui."""
    n = len(F)
    keep = np.ones(n, bool)
    for i in range(n):
        if not keep[i]:
            continue
        le = (F <= F[i]).all(axis=1)
        lt = (F < F[i]).any(axis=1)
        if (le & lt).any():
            keep[i] = False
    return keep


def cells():
    out = []
    for lab in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, lab, "42")
        if not os.path.isdir(d):
            continue
        exp = "batch" if lab.startswith("q10_") else "main"
        prob = lab[4:] if lab.startswith("q10_") else lab
        out.append((exp, prob, lab, d))
    return out


rows_g5, rows_rc = [], []
gates = pd.read_csv(f"{REPO}/f5/gates_f51.csv")

for exp, prob, lab, d in cells():
    base = os.path.join(d, f"exp_{exp}_e81_{prob}_42")
    man = json.load(open(base + ".manifest.json"))
    hdr = json.loads(open(base + ".jsonl").readline())
    lines = open(base + ".jsonl").read().splitlines()
    dec = [json.loads(l) for l in lines if '"rec": "decision"' in l]
    foots = [json.loads(l) for l in lines if '"rec": "footer"' in l]
    sur = pd.read_parquet(base + "__surrogate.parquet")
    pop = pd.read_parquet(base + "__pop.parquet")
    D, M = int(hdr["D"]), int(hdr["M"]); q = int(man["q"])
    mus = [f"mu_{j}" for j in range(M)]
    onl = {g: v for g, v in sur[sur["regime"] == "online"].groupby("geracao")}

    fr_nd, esc_dom, n_ok = [], 0, 0
    for o in dec:
        g = o["geracao"]; nfa = int(o["n_front_acq"])
        blk = onl[g]
        if len(blk) != nfa or nfa < 2:
            continue
        F = blk[mus].values.astype(np.float64)
        keep = nd_mask(F)
        fr_nd.append(keep.mean())
        idx = np.array(o["idx_escolhidos"])
        esc_dom += int((~keep[idx]).sum())
        n_ok += len(idx)
    rows_g5.append(dict(label=lab, exp=exp, problema=prob, D=D, M=M, q=q,
                        n_ger_avaliadas=len(fr_nd),
                        frac_nd_mu_med=float(np.median(fr_nd)),
                        frac_nd_mu_min=float(np.min(fr_nd)), frac_nd_mu_max=float(np.max(fr_nd)),
                        gers_front_todo_nd=int(np.sum(np.array(fr_nd) >= 1.0)),
                        escolhidos_dominados_em_mu=esc_dom, escolhidos_total=n_ok,
                        frac_escolhido_dominado=esc_dom / max(1, n_ok)))

    # ── reconciliacao footer/manifesto/decisoes/gates ─────────────────────
    fo, fd = foots[0], foots[1] if len(foots) > 1 else {}
    gz = gates[(gates.get("alg") == "e81") & (gates.get("problema") == prob)] if "alg" in gates.columns else pd.DataFrame()
    rows_rc.append(dict(label=lab, exp=exp, problema=prob,
                        n_footers=len(foots),
                        foot_runner_keys=",".join(sorted(fo.keys())),
                        foot_desp_keys=",".join(sorted(fd.keys())),
                        man_status=man["status"], foot_status=fo.get("status"),
                        man_motivo=man.get("motivo_parada"), foot_motivo=fo.get("motivo_parada"),
                        man_fe=man["fe_final"], foot_fe=fo.get("fe_final"),
                        man_nger=man["n_geracoes"], foot_nger=fo.get("n_geracoes"),
                        man_cache=man.get("cache_hits"), foot_cache=fo.get("cache_hits"),
                        n_retries=man.get("n_retries"), foot_retries=fd.get("n_retries"),
                        stack_trace=str(man.get("stack_trace"))[:40],
                        tempo_total_s=man["timing"]["tempo_total_s"],
                        tempo_desp_s=fd.get("tempo_total_s"),
                        upload=man.get("upload_status"), regime=man.get("regime"),
                        tier=man.get("tier"), dist=man.get("dist"),
                        repo_hash=str(man.get("repo_hash"))[:16],
                        # 2a camada: geracao minima e conteudo
                        pop_gen_min=int(pop["geracao"].min()),
                        pop_gen0_existe=bool((pop["geracao"] == 0).any()),
                        pop_solid_max=int(pop["solution_id"].max()),
                        # header x manifesto
                        hdr_params_igual=bool(json.dumps(hdr.get("params"), sort_keys=True) ==
                                              json.dumps(man.get("params"), sort_keys=True)),
                        hdr_sigma_igual=bool(json.dumps(hdr.get("sigma_dict"), sort_keys=True) ==
                                             json.dumps(man.get("sigma_dict"), sort_keys=True)),
                        hdr_maxfe=hdr.get("maxfe"), hdr_ninit=hdr.get("n_init"),
                        algo_version=man.get("algo_version"),
                        schema_version=man.get("schema_version")))
    print("ok", lab, f"frac_nd_mu_med={np.median(fr_nd):.3f} escolhido_dominado={esc_dom}/{n_ok}", flush=True)

pd.DataFrame(rows_g5).to_csv(f"{OUT}/e81_g5_contrafactual.csv", index=False)
pd.DataFrame(rows_rc).to_csv(f"{OUT}/e81_reconciliacao.csv", index=False)
print("\nescrito em", OUT)
