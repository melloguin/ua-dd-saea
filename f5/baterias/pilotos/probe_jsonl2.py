import json
from collections import Counter

BASE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/main/e81"
for prob in ["MMF1", "DTLZ2", "ZDT1"]:
    evs = [json.loads(l) for l in open(f"{BASE}/exp_main_e81_{prob}_42.jsonl") if l.strip()]
    print("=" * 90)
    print(f"### {prob}: {len(evs)} eventos; tipos:", dict(Counter(e.get("rec", "?") for e in evs)))
    by = {}
    for e in evs:
        by.setdefault(e.get("rec"), []).append(e)
    h = by["header"][0]
    print("  header keys:", sorted(h.keys()))
    print("  header.dtype_check:", h.get("dtype_check"))
    print("  header.n_init:", h.get("n_init"), "| sonda_S:", h.get("sonda_S"))
    fit0 = by["fit"][0]
    print("  fit keys:", sorted(fit0.keys()))
    print("  fit[0]:", json.dumps(fit0, ensure_ascii=False)[:900])
    dec0, decl = by["decision"][0], by["decision"][-1]
    print("  decision keys:", sorted(dec0.keys()))
    print("  decision[0]:", json.dumps(dec0, ensure_ascii=False)[:1600])
    print("  decision[-1]:", json.dumps(decl, ensure_ascii=False)[:1200])
    s0 = by["sonda"][0]
    print("  sonda keys:", sorted(s0.keys()))
    print("  sonda[0]:", json.dumps(s0, ensure_ascii=False)[:400])
    for f in by["footer"]:
        print("  footer:", json.dumps(f, ensure_ascii=False)[:700])
    # decision-level checks
    decs = by["decision"]
    fes = [d.get("fe") for d in decs]
    print("  decision.fe: first,last =", fes[0], fes[-1], "| estritamente crescente:", all(b > a for a, b in zip(fes, fes[1:])))
    if "n_train" in dec0:
        nt = [d["n_train"] for d in decs]
        print("  n_train first,last:", nt[0], nt[-1], "| monotonico:", all(b >= a for a, b in zip(nt, nt[1:])))
    # draws stats fields
    for k in dec0:
        if "draw" in k or "thompson" in k.lower():
            print(f"  campo draws: {k} ->", json.dumps(dec0[k])[:300])
