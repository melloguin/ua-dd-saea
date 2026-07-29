import json, glob, collections
import pandas as pd
import pyarrow.parquet as pq

BASE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/main/b1"
CELLS = ["MMF1", "DTLZ2", "ZDT1"]

for prob in CELLS:
    stem = f"{BASE}/exp_main_b1_{prob}_42"
    print("=" * 100)
    print(f"CELL {prob}")
    # --- manifest ---
    with open(stem + ".manifest.json") as fh:
        man = json.load(fh)
    keys = sorted(man.keys())
    print("MANIFEST keys:", keys)
    for k in ["status", "fe_final", "maxfe", "n_geracoes", "doe_hash", "algo_version", "cache_hits", "fallback_ativado", "n_retries"]:
        print(f"  {k} = {man.get(k)}")
    print("  params =", json.dumps(man.get("params", {}), ensure_ascii=False)[:2000])
    print("  sigma_dict =", json.dumps(man.get("sigma_dict", {}), ensure_ascii=False)[:3000])
    print("  timing =", json.dumps(man.get("timing", {}), ensure_ascii=False)[:800])
    sonda_block = {k: v for k, v in man.items() if "sonda" in k.lower()}
    print("  sonda-related manifest keys:", json.dumps(sonda_block)[:800])

    # --- jsonl ---
    events = collections.Counter()
    gen_fields = None
    header_fields = None
    sonda_ev = None
    guard_motifs = collections.Counter()
    footer = None
    first_gen_ev = None
    with open(stem + ".jsonl") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except Exception:
                continue
            t = ev.get("event", ev.get("tipo", "?"))
            events[t] += 1
            if t == "header" and header_fields is None:
                header_fields = sorted(ev.keys())
            if t.endswith("_gen") and gen_fields is None:
                gen_fields = sorted(ev.keys())
                first_gen_ev = ev
            if t == "sonda" and sonda_ev is None:
                sonda_ev = ev
            if t == "guard":
                guard_motifs[str(ev.get("tipo", ev.get("guard", ev.get("motivo", "?"))))[:60]] += 1
            if t == "footer":
                footer = ev
    print("JSONL event counts:", dict(events))
    print("  header fields:", header_fields)
    print("  <alg>_gen fields:", gen_fields)
    print("  first _gen event sample:", json.dumps(first_gen_ev, ensure_ascii=False)[:1500])
    print("  sonda event sample:", json.dumps(sonda_ev, ensure_ascii=False)[:600])
    print("  guard types:", dict(guard_motifs))
    print("  footer:", json.dumps(footer, ensure_ascii=False)[:800])

    # --- parquet schemas + counts ---
    for layer in ["__real", "__pop", "__surrogate", "__timing"]:
        f = stem + layer + ".parquet"
        try:
            t = pq.read_table(f)
        except Exception as e:
            print(f"  {layer}: ERROR {e}")
            continue
        print(f"  {layer}: {t.num_rows} rows; cols = {t.column_names}")
    print()
