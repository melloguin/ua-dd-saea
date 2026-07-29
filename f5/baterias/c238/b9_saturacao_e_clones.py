#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 9: os aspectos que faltavam depois de b1-b8.
(1) f_best ==? min por objetivo do arquivo pre-infill (identidade do ideal point);
(2) saturacao EIM==0 (paper SS IV-D: "s=0 nos amostrados -> EI=0 -> o proximo e qualquer
    um menos os amostrados") — censo por celula, 1a geracao, e o que o algoritmo faz la;
(3) PROVA DE LINHA da propriedade: nas linhas do pool que SAO clones de pontos ja
    amostrados (real_solution_id nao-nulo, X bit-identico), sigma e EIM colapsam?
(4) atribuicao do ruido de eim_best (DI-18): mudanca de RANGE x mudanca de FRENTE x nenhum;
(5) posicao (rank) do infill dentro do pool final + empates;
(6) U2 bit-a-bit: (1)[init] x artefato do DoE + doe_hash x sidecar; U9 guards; censo de rec.
Saidas: sat_clones.csv, ruido_atrib.csv, u2_u9.csv
"""
import hashlib, json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
import importlib.util

spec = importlib.util.spec_from_file_location(
    "b2", "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238/b2_eim_identidade.py")
b2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b2)

BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
DOE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"

sat, ruido, u2 = [], [], []
for prob in sorted(os.listdir(BASE)):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    recs = [json.loads(l) for l in open(f"{b}.jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    M, D = hdr["M"], hdr["D"]
    G = [r for r in recs if r.get("rec") == "c238_gen"]
    guards = [r for r in recs if r.get("rec") == "guard"]
    man = json.load(open(f"{b}.manifest.json"))
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    F = real[[f"f{i}" for i in range(M)]].values.astype(np.float64)
    X = real[[f"x{i}" for i in range(D)]].values
    cols = ["regime", "geracao", "real_solution_id"] + [f"mu_{i}" for i in range(M)] + \
           [f"sigma_{i}" for i in range(M)]
    sur = pq.read_table(f"{b}__surrogate.parquet", columns=cols).to_pandas()
    grp = dict(list(sur[sur.regime == "online"].groupby("geracao")))

    eb = np.array([r["eim_best"] for r in G], float)
    fb = np.array([r["f_best"] for r in G], float)
    nm = np.array([r["norm_min"] for r in G], float)
    nx = np.array([r["norm_max"] for r in G], float)
    nre = np.array([r["norm_range_efetivo"] for r in G], float)
    nf = np.array([r["n_front"] for r in G], int)
    namo = np.array([r["n_amostra"] for r in G], int)
    mind = np.array([r["min_dist_infill"] for r in G], float)
    # (1) ideal point
    ymin = np.array([F[:n].min(0) for n in namo])
    d_fb = float(np.abs(fb - ymin).max())
    d_nm = float(np.abs(nm - ymin).max())
    d_nx = float(np.abs(nx - np.array([F[:n].max(0) for n in namo])).max())

    # (2)+(3)+(5)
    n_zero = int((eb == 0).sum()); n_lt12 = int((eb < 1e-12).sum())
    g_zero1 = int(G[int(np.argmax(eb == 0))]["geracao"]) if n_zero else -1
    rank_inf, empates, clone_sig, clone_eim, base_eim, n_clone = [], [], [], [], [], 0
    for r in G:
        sub = grp[r["geracao"]]
        rsid = sub.real_solution_id.values
        u = sub[[f"mu_{i}" for i in range(M)]].values.astype(np.float64)
        s = sub[[f"sigma_{i}" for i in range(M)]].values.astype(np.float64)
        Y = F[:r["n_amostra"]]
        Fr = (Y[b2.nd_weak_seq(Y)] - np.array(r["norm_min"])) / np.array(r["norm_range_efetivo"])
        v = b2.eim_euclidean(u, s, Fr)
        pos = np.where(rsid == r["infill_sid"])[0]
        j = int(pos[0]) if len(pos) else int(np.argmax(v))
        rank_inf.append(int((v > v[j] + 1e-15).sum()) + 1)
        empates.append(int((np.abs(v - v[j]) <= 1e-15).sum()))
        # clones: linhas com rsid nao-nulo que NAO sao o infill
        cm = pd.notna(rsid); cm[j] = False
        if cm.any():
            n_clone += int(cm.sum())
            clone_sig.append(s[cm].max(1)); clone_eim.append(v[cm])
        base_eim.append(np.median(v))
    rank_inf = np.array(rank_inf); empates = np.array(empates)
    cs = np.concatenate(clone_sig) if clone_sig else np.array([])
    ce = np.concatenate(clone_eim) if clone_eim else np.array([])
    sat.append(dict(problema=prob, D=D, M=M, n_gens=len(G),
                    fbest_eq_ymin=d_fb, normmin_eq_ymin=d_nm, normmax_eq_ymax=d_nx,
                    eim_zero=n_zero, eim_lt1e12=n_lt12, prim_gen_zero=g_zero1,
                    frac_zero=n_zero / len(G),
                    mind_nas_zero=float(mind[eb == 0].min()) if n_zero else np.nan,
                    rank_infill_1=int((rank_inf == 1).sum()),
                    rank_infill_med=float(np.median(rank_inf)), rank_infill_max=int(rank_inf.max()),
                    empate_med=float(np.median(empates)), empate_max=int(empates.max()),
                    n_clones_pool=n_clone,
                    clone_sigma_max=float(cs.max()) if cs.size else np.nan,
                    clone_sigma_med=float(np.median(cs)) if cs.size else np.nan,
                    clone_eim_max=float(ce.max()) if ce.size else np.nan,
                    clone_eim_med=float(np.median(ce)) if ce.size else np.nan,
                    eim_med_pool_med=float(np.median(base_eim)),
                    razao_clone_pool=float(np.median(ce) / max(np.median(base_eim), 1e-300)) if ce.size else np.nan))

    # (4) atribuicao do ruido
    dr = (np.abs(np.diff(nre, axis=0)) > 0).any(1)          # range mudou
    df_ = np.diff(nf) != 0                                   # tamanho da frente mudou
    up = np.diff(eb) > 0
    pct = np.abs(np.diff(eb)) / np.maximum(np.abs(eb[:-1]), 1e-300)
    grande = pct > 1.0                                       # salto > 100%
    ruido.append(dict(problema=prob, n_trans=len(up), subidas=int(up.sum()),
                      range_mudou=int(dr.sum()), frente_mudou=int(df_.sum()),
                      subida_com_range=int((up & dr).sum()),
                      subida_com_frente=int((up & df_).sum()),
                      subida_sem_nada=int((up & ~dr & ~df_).sum()),
                      saltos_gt100pct=int(grande.sum()),
                      salto_grande_com_range=int((grande & dr).sum()),
                      salto_grande_com_frente=int((grande & df_).sum()),
                      salto_grande_sem_nada=int((grande & ~dr & ~df_).sum())))

    # (6) U2 / U9
    dpath = f"{DOE}/{prob}/doe_{prob}_42.parquet"
    doe = pq.read_table(dpath).to_pandas().values.astype(np.float64)
    init = 11 * D - 1
    dx = float(np.abs(X[:init].astype(np.float64) - doe[:init]).max())
    dx32 = float(np.abs(X[:init].astype(np.float64) - doe[:init].astype(np.float32).astype(np.float64)).max())
    h = hashlib.sha256(np.ascontiguousarray(doe, dtype=np.float64).tobytes()).hexdigest()
    side = json.load(open(dpath.replace(".parquet", ".manifest.json")))
    from collections import Counter
    cnt = Counter(r.get("rec") for r in recs)
    gnames = Counter(g.get("name") for g in guards)
    u2.append(dict(problema=prob, D=D, init=init, doe_shape=str(doe.shape),
                   u2_dx_max=dx, u2_dx32_max=dx32,
                   u2_ok=dx32 == 0.0,
                   doe_hash_man=man["doe_hash"][:16], doe_hash_recalc=h[:16],
                   sidecar_hash=str(side.get("doe_hash", ""))[:16],
                   rec_census=json.dumps(dict(cnt)), guard_census=json.dumps(dict(gnames)),
                   man_cache_hits=man["cache_hits"], guard_cache_hits=gnames.get("cache_hit", 0),
                   dup_infill=int(len(real[real.fase == "opt"]) - len(G)),
                   n_opt=int((real.fase == "opt").sum())))
    print("OK", prob, flush=True)

pd.DataFrame(sat).to_csv(f"{OUT}/sat_clones.csv", index=False)
pd.DataFrame(ruido).to_csv(f"{OUT}/ruido_atrib.csv", index=False)
pd.DataFrame(u2).to_csv(f"{OUT}/u2_u9.csv", index=False)
pd.set_option("display.width", 400); pd.set_option("display.max_columns", 100)
print(pd.DataFrame(sat).to_string(index=False))
print(pd.DataFrame(ruido).to_string(index=False))
print(pd.DataFrame(u2).to_string(index=False))
