import json, collections
import pandas as pd
import pyarrow.parquet as pq

BASE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/main/e7/"
CELLS = ["MMF1", "DTLZ2", "ZDT1"]

for prob in CELLS:
    stem = BASE + f"exp_main_e7_{prob}_42"
    print("=" * 90)
    print(f"CELULA: {prob} (semente 42)")
    # ---- manifest ----
    with open(stem + ".manifest.json") as f:
        man = json.load(f)
    keys = list(man.keys())
    print(f"[manifest] chaves: {keys}")
    for k in ["run_id", "status", "n_retries", "maxfe", "fe_final", "n_geracoes", "doe_hash", "regime", "algo_version", "env", "cache_hits", "fallback_ativado", "motivo_parada"]:
        if k in man:
            print(f"  {k} = {man[k]}")
    print(f"  params = {json.dumps(man.get('params', {}), ensure_ascii=False)[:2000]}")
    print(f"  sigma_dict = {json.dumps(man.get('sigma_dict', {}), ensure_ascii=False)}")
    if "timing" in man:
        print(f"  timing = {json.dumps(man['timing'])[:400]}")
    if "sonda" in man:
        print(f"  sonda(bloco manifesto) = {json.dumps(man['sonda'])[:400]}")

    # ---- layers ----
    for layer in ["__real", "__pop", "__surrogate", "__timing"]:
        t = pq.read_table(stem + layer + ".parquet")
        print(f"[{layer}] linhas={t.num_rows} colunas={t.column_names}")

    real = pd.read_parquet(stem + "__real.parquet")
    D = len([c for c in real.columns if c.startswith("x")])
    M = len([c for c in real.columns if c.startswith("f") and c[1:].isdigit()])
    print(f"  D={D} M={M}; 31D-1={31*D-1}; linhas ①={len(real)}; fases={real['fase'].value_counts().to_dict()}")
    print(f"  fe_index: min={real['fe_index'].min()} max={real['fe_index'].max()} nunique={real['fe_index'].nunique()}")
    print(f"  solution_id: nunique={real['solution_id'].nunique()}")

    pop = pd.read_parquet(stem + "__pop.parquet")
    print(f"  ② geracoes: nunique={pop['geracao'].nunique()} min={pop['geracao'].min()} max={pop['geracao'].max()}; tamanho pop por ger (describe): {pop.groupby('geracao').size().describe()[['min','max','mean']].to_dict()}")

    sur = pd.read_parquet(stem + "__surrogate.parquet")
    print(f"  ③ regimes: {sur['regime'].value_counts().to_dict()}")
    sonda = sur[sur['regime'] == 'sonda']
    busca = sur[sur['regime'] != 'sonda']
    print(f"  ③ sonda: blocos(geracoes)={sonda['geracao'].nunique()}, geracoes={sorted(sonda['geracao'].dropna().unique())[:12]}... total_linhas={len(sonda)}")
    print(f"  ③ busca: geracoes nunique={busca['geracao'].nunique()}, linhas/ger describe: {busca.groupby('geracao').size().describe()[['min','max','mean']].to_dict()}")
    print(f"  ③ pred_tipo: {sur['pred_tipo'].value_counts().to_dict()}")
    print(f"  ③ modelo_flag: {sur['modelo_flag'].value_counts().to_dict() if 'modelo_flag' in sur.columns else 'N/A'}")
    print(f"  ③ transf_tipo: {sur['transf_tipo'].value_counts().to_dict() if 'transf_tipo' in sur.columns else 'N/A'}")
    ex = sur[sur['transf_params'].notna()]['transf_params'].iloc[0] if 'transf_params' in sur.columns and sur['transf_params'].notna().any() else None
    print(f"  ③ transf_params exemplo: {str(ex)[:200]}")
    print(f"  ③ fe_treino_max: nunique={sur['fe_treino_max'].nunique()} min={sur['fe_treino_max'].min()} max={sur['fe_treino_max'].max()}")
    print(f"  ③ real_solution_id: notna={sur['real_solution_id'].notna().sum()}")
    sig_cols = [c for c in sur.columns if c.startswith('sigma_')]
    mu_cols = [c for c in sur.columns if c.startswith('mu_')]
    print(f"  ③ mu cols={mu_cols} sigma cols={sig_cols}; sigma NULLs: {{c: int(sur[c].isna().sum()) for c in sig_cols}}")
    print(f"  ③ sigma stats (busca): {busca[sig_cols].describe().loc[['mean','min','max']].to_dict() if sig_cols else 'N/A'}")

    tim = pd.read_parquet(stem + "__timing.parquet")
    print(f"  ④ linhas={len(tim)}; n_acumulado min/max={tim['n_acumulado'].min()}/{tim['n_acumulado'].max()}; tempo_fit_s NULLs={tim['tempo_fit_s'].isna().sum()}")
    print(f"  ④ tempo_fit_s: mean={tim['tempo_fit_s'].mean():.2f} first={tim['tempo_fit_s'].iloc[0]:.2f} rest_mean={tim['tempo_fit_s'].iloc[1:].mean():.2f}")

    # ---- jsonl ----
    events = collections.Counter()
    gen_fields = None
    header = None
    footer = None
    guard_motivos = collections.Counter()
    gen_events = []
    sonda_ev = []
    with open(stem + ".jsonl") as f:
        for line in f:
            try:
                ev = json.loads(line)
            except Exception:
                continue
            et = ev.get("evento") or ev.get("event") or ev.get("tipo")
            events[et] += 1
            if et == "header":
                header = ev
            elif et == "footer":
                footer = ev
            elif et and "gen" in str(et):
                if gen_fields is None:
                    gen_fields = list(ev.keys())
                gen_events.append(ev)
            elif et == "guard":
                guard_motivos[str(ev.get("tipo") or ev.get("motivo") or ev.get("guard"))[:60]] += 1
            elif et == "sonda":
                sonda_ev.append(ev)
    print(f"  ⑥ eventos: {dict(events)}")
    print(f"  ⑥ campos do e7_gen: {gen_fields}")
    if gen_events:
        print(f"  ⑥ e7_gen exemplo (1o): {json.dumps(gen_events[0], ensure_ascii=False)[:1200]}")
        print(f"  ⑥ e7_gen exemplo (ultimo): {json.dumps(gen_events[-1], ensure_ascii=False)[:1200]}")
        flags = collections.Counter(str(g.get('flag', g.get('ramo', '?'))) for g in gen_events)
        print(f"  ⑥ distribuicao de flag/ramo nos e7_gen: {dict(flags)}")
    print(f"  ⑥ guards: {dict(guard_motivos)}")
    if header:
        print(f"  ⑥ header keys: {list(header.keys())}")
        print(f"  ⑥ header.params: {json.dumps(header.get('params', {}), ensure_ascii=False)[:1200]}")
    if footer:
        print(f"  ⑥ footer: {json.dumps(footer, ensure_ascii=False)[:600]}")
    if sonda_ev:
        print(f"  ⑥ sonda evs={len(sonda_ev)}; exemplo: {json.dumps(sonda_ev[0], ensure_ascii=False)[:400]}")
