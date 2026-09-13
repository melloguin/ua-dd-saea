import json, sys
import pandas as pd
import pyarrow.parquet as pq

BASE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/main/e81"
CELLS = ["MMF1", "DTLZ2", "ZDT1"]

for prob in CELLS:
    stem = f"{BASE}/exp_main_e81_{prob}_42"
    print("=" * 90)
    print(f"### CELL {prob}")
    # --- manifest ---
    with open(stem + ".manifest.json") as fh:
        man = json.load(fh)
    keys = sorted(man.keys())
    print("[manifest keys]", keys)
    for k in ["status", "motivo_parada", "maxfe", "fe_final", "n_geracoes", "regime", "q",
              "doe_hash", "cache_hits", "fallback_ativado", "env", "algo_version", "n_retries"]:
        if k in man:
            print(f"  manifest.{k} = {man[k]}")
    print("  manifest.params =", json.dumps(man.get("params", {}), ensure_ascii=False)[:2000])
    print("  manifest.sigma_dict =", json.dumps(man.get("sigma_dict", {}), ensure_ascii=False)[:3000])
    if "timing" in man:
        print("  manifest.timing =", json.dumps(man["timing"])[:500])
    if "sonda" in man:
        print("  manifest.sonda =", json.dumps(man["sonda"])[:500])

    # --- parquet schemas + counts ---
    for layer in ["__real", "__pop", "__surrogate", "__timing"]:
        f = stem + layer + ".parquet"
        try:
            pf = pq.ParquetFile(f)
            print(f"[{layer}] rows={pf.metadata.num_rows} cols={pf.schema_arrow.names}")
        except Exception as e:
            print(f"[{layer}] ERROR: {e}")

    # --- real layer detail ---
    real = pd.read_parquet(stem + "__real.parquet")
    D = len([c for c in real.columns if c.startswith("x")])
    M = len([c for c in real.columns if c.startswith("f") and c[1:].isdigit()])
    print(f"  [real] D={D} M={M} n_rows={len(real)}  31D-1={31*D-1}  11D-1={11*D-1}")
    print(f"  [real] fase counts: {real['fase'].value_counts().to_dict()}")
    print(f"  [real] fe_index: min={real['fe_index'].min()} max={real['fe_index'].max()} nunique={real['fe_index'].nunique()}")
    print(f"  [real] solution_id nunique={real['solution_id'].nunique()}")

    # --- pop layer ---
    pop = pd.read_parquet(stem + "__pop.parquet")
    print(f"  [pop] gens: n={pop['geracao'].nunique()} min={pop['geracao'].min()} max={pop['geracao'].max()}; rows/gen (first,last)={pop.groupby('geracao').size().iloc[[0,-1]].tolist()}")

    # --- surrogate layer ---
    sur = pd.read_parquet(stem + "__surrogate.parquet")
    print(f"  [sur] rows={len(sur)} regimes={sur['regime'].value_counts().to_dict()}")
    sonda = sur[sur['regime'] == 'sonda']
    busca = sur[sur['regime'] != 'sonda']
    print(f"  [sur] busca rows={len(busca)}; gens min={busca['geracao'].min()} max={busca['geracao'].max()} nunique={busca['geracao'].nunique()}")
    bg = busca.groupby('geracao').size()
    print(f"  [sur] busca rows/gen: min={bg.min()} med={bg.median()} max={bg.max()} (pop 100*D={100*D})")
    if len(sonda):
        sg = sonda.groupby('geracao').size()
        print(f"  [sur] sonda: n_blocks={sonda['geracao'].nunique()} rows/block unique={sorted(sg.unique())} gens={sorted(sonda['geracao'].unique())[:12]}... last={sorted(sonda['geracao'].unique())[-3:]}")
    print(f"  [sur] pred_tipo={sur['pred_tipo'].value_counts().to_dict() if 'pred_tipo' in sur else 'N/A'}")
    for c in ["modelo_flag", "espaco_modelo", "transf_tipo"]:
        if c in sur.columns:
            print(f"  [sur] {c} unique={sur[c].dropna().unique()[:5].tolist()}")
    if "fe_treino_max" in sur.columns:
        print(f"  [sur] fe_treino_max: min={sur['fe_treino_max'].min()} max={sur['fe_treino_max'].max()}")
    if "real_solution_id" in sur.columns:
        nn = sur['real_solution_id'].notna().sum()
        print(f"  [sur] real_solution_id notnull={nn} ({nn/len(sur)*100:.2f}%)")
    sig_nan = sur[[c for c in sur.columns if c.startswith('sigma_')]].isna().all().to_dict() if any(c.startswith('sigma_') for c in sur.columns) else {}
    print(f"  [sur] sigma cols all-NaN? {sig_nan}")

    # --- timing ---
    tim = pd.read_parquet(stem + "__timing.parquet")
    print(f"  [timing] rows={len(tim)} cols={list(tim.columns)}")
    print(f"  [timing] n_acumulado: min={tim['n_acumulado'].min()} max={tim['n_acumulado'].max()}")
    print(f"  [timing] tempo_fit_s med={tim['tempo_fit_s'].median():.3f} tempo_busca_s med={tim['tempo_busca_s'].median():.3f}")
    sys.stdout.flush()
