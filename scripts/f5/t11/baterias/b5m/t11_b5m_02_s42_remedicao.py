"""RE-MEDICAO da s42 (45 celulas) — o corpus principal do MECANISMO.
Confirma os numeros da F5 e mede a AUSENCIA da instrumentacao T11 no dado velho.
READ-ONLY: le resultados_experimentos/b5m/{label}/42/, escreve so em f5/t11/baterias/b5m/.
"""
import os, json, glob, csv
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m"
OUT  = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b5m"
labels = sorted(os.listdir(ROOT))
rows = []
for lab in labels:
    d = os.path.join(ROOT, lab, "42")
    man = [p for p in glob.glob(d + "/*.manifest.json") if "__final" not in p]
    if not man:
        continue
    base = man[0][:-len(".manifest.json")]
    m = json.load(open(man[0]))
    recs = [json.loads(l) for l in open(base + ".jsonl")]
    hdr = [r for r in recs if r.get("rec") == "header"]
    dec = [r for r in recs if r.get("rec") == "decision"]
    son = [r for r in recs if r.get("rec") == "sonda"]
    foo = [r for r in recs if r.get("rec") == "footer"]
    sg  = pq.read_table(base + "__surrogate.parquet").to_pandas()
    busca = sg[sg.regime == "offline"]
    sonda = sg[sg.regime == "sonda"]
    xs = [c for c in sg.columns if c.startswith("x")]
    mus = [c for c in sg.columns if c.startswith("mu_")]
    sis = [c for c in sg.columns if c.startswith("sigma_")]
    g = busca.geracao.dropna().astype(int)
    n_ger = int(g.max()); pops = busca.groupby("geracao").size()
    pop = int(pops.iloc[0])
    fin = pq.read_table(base + "__final.parquet").to_pandas()
    rea = pq.read_table(base + "__real.parquet").to_pandas()
    pop2 = pq.ParquetFile(base + "__pop.parquet").metadata.num_rows
    tim = pq.read_table(base + "__timing.parquet").to_pandas()

    # --- congelamento: turnover por transicao (X exato float32) -------------
    G = {int(k): v[xs].values for k, v in busca.groupby("geracao")}
    ks = sorted(G)
    turn = []
    for a, b in zip(ks, ks[1:]):
        A, B = G[a], G[b]
        sa = set(map(bytes, np.ascontiguousarray(A)))
        novos = sum(1 for r in np.ascontiguousarray(B) if bytes(r) not in sa)
        turn.append(novos / B.shape[0])
    turn = np.array(turn)
    congeladas = int((turn == 0).sum())
    # amplitude mu da ultima geracao
    ampl = float(np.ptp(G_mu := busca[busca.geracao == ks[-1]][mus].values, axis=0).max())

    rows.append(dict(
        label=lab, D=int(m.get("env", {}).get("D", 0) or len(xs)), n_x=len(xs), M=len(mus),
        n_dataset=int(m["fe_final"]), maxfe=int(m["maxfe"]),
        status=m["status"], motivo_parada=m.get("motivo_parada"),
        tempo_aval_real_s=m["timing"].get("tempo_aval_real_s"),
        tempo_total_s=m["timing"].get("tempo_total_s"),
        fit_series_len=len(m.get("fit_series") or []),
        camada4_linhas=len(tim), camada2_linhas=pop2,
        camada1_linhas=len(rea), fase_init=int((rea.fase == "init").sum()),
        n_ger=n_ger, pop=pop, pop_const=int(pops.nunique() == 1),
        ident_nger=int(n_ger == 40000 // pop + 1),
        linhas_busca=len(busca), linhas_sonda=len(sonda),
        sonda_ger_null=int(sonda.geracao.isna().all()) if len(sonda) else -1,
        n_blocos_sonda=len(son),
        sigma_nan=int(sg[sis].isna().sum().sum()),
        real_sol_id_null=int(busca.real_solution_id.isna().all()),
        fe_treino_max_unico=int(sg.fe_treino_max.nunique() == 1),
        fe_treino_max=float(sg.fe_treino_max.iloc[0]),
        x_dentro_bounds=None,
        n_dec=len(dec), n_footer=len(foo), n_hdr_keys=len(hdr[0]) if hdr else -1,
        # ---- a instrumentacao T11 no dado VELHO ----
        t11_p_wrong_stats=sum("p_wrong_stats" in r for r in dec),
        t11_n_substituicoes=sum("n_substituicoes" in r for r in dec),
        t11_flag_vet_deg=sum("flag_vetores_degenerados" in r for r in dec),
        t11_campanha_id=int("campanha_id" in m),
        t11_pesos_header=int(any("peso" in k.lower() or "vetor" in k.lower()
                                 for k in (hdr[0] if hdr else {}))),
        params_no_5=int("params" in m),
        sigma_dict_chaves=len(m.get("sigma_dict") or {}),
        # ---- (7) ----
        c7_linhas=len(fin), c7_nd=int(fin.nd_pos_real.sum()),
        c7_origem_ger_ultima=int((fin.origem_geracao == n_ger).all()),
        c7_origem_sol_null=int(fin.origem_solution_id.isna().all()),
        fantasia=float(fin.nd_pos_real.sum() / len(fin)),
        # ---- congelamento ----
        turn_med=float(np.median(turn)), turn_1a=float(turn[0]),
        n_congeladas=congeladas, ampl_mu_final=ampl,
        spearman_turn=float(pd.Series(turn).corr(pd.Series(np.arange(len(turn))), method="spearman")),
        # ---- tempo ----
        t_fit=float(tim.tempo_fit_s.iloc[0]), t_busca=float(tim.tempo_busca_s.iloc[0]),
        t_ger=float(tim.tempo_geracao_s.iloc[0]), t_sonda=float(tim.tempo_pred_sonda_s.iloc[0]),
    ))
    print("ok", lab, flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "t11_b5m_s42.csv"), index=False)
print("\n=== %d celulas ===" % len(df))
print("ident n_ger = floor(40000/pop)+1 :", int(df.ident_nger.sum()), "/", len(df))
print("pop constante                    :", int(df.pop_const.sum()), "/", len(df))
print("tempo_aval_real_s == 0           :", int((df.tempo_aval_real_s == 0).sum()), "/", len(df))
print("maxfe == n_dataset == fe_final   :", int((df.maxfe == df.n_dataset).sum()), "/", len(df))
print("④ = 1 linha                      :", int((df.camada4_linhas == 1).sum()), "/", len(df))
print("② = 0 linhas                     :", int((df.camada2_linhas == 0).sum()), "/", len(df))
print("real_solution_id NULL 100%       :", int(df.real_sol_id_null.sum()), "/", len(df))
print("fe_treino_max unico (busca+sonda):", int(df.fe_treino_max_unico.sum()), "/", len(df))
print("sigma NaN total                  :", int(df.sigma_nan.sum()))
print("sonda: 1 bloco / ger NULL        :", int((df.n_blocos_sonda == 1).sum()), "/",
      int((df.sonda_ger_null == 1).sum()), "/", len(df))
print("⑦ origem_geracao = ultima        :", int(df.c7_origem_ger_ultima.sum()), "/", len(df))
print("gerações arquivadas (soma)       :", int(df.n_ger.sum()))
print("gerações CONGELADAS (turnover 0) :", int(df.n_congeladas.sum()))
print("turnover medio (mediana celulas) :", round(float(df.turn_med.median()), 4))
print("spearman(turnover,ger) mediana   :", round(float(df.spearman_turn.median()), 4),
      " negativa em", int((df.spearman_turn < 0).sum()), "/", len(df))
print("fantasia nd/n (mediana)          :", round(float(df.fantasia.median()), 4))
print("--- T11 no dado VELHO (esperado 0) ---")
for c in ["t11_p_wrong_stats", "t11_n_substituicoes", "t11_flag_vet_deg"]:
    print("  %-24s soma=%d de %d eventos decision" % (c, int(df[c].sum()), int(df.n_dec.sum())))
print("  campanha_id no ⑤        :", int(df.t11_campanha_id.sum()), "/", len(df))
print("  pesos/vetores no header :", int(df.t11_pesos_header.sum()), "/", len(df))
print("  params no ⑤             :", int(df.params_no_5.sum()), "/", len(df))
print("  sigma_dict chaves       :", sorted(df.sigma_dict_chaves.unique()))
print("  n_hdr_keys              :", sorted(df.n_hdr_keys.unique()))
print("  n_footer                :", df.n_footer.value_counts().to_dict())
