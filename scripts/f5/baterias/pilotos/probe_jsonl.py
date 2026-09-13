import json, collections

BASE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/main/e7/"
for prob in ["MMF1", "DTLZ2", "ZDT1"]:
    stem = BASE + f"exp_main_e7_{prob}_42"
    events = collections.Counter()
    gen_events, guards, footer = [], [], None
    with open(stem + ".jsonl") as f:
        for line in f:
            ev = json.loads(line)
            rec = ev.get("rec")
            events[rec] += 1
            if rec == "e7_gen":
                gen_events.append(ev)
            elif rec == "guard":
                guards.append(ev)
            elif rec == "footer":
                footer = ev
    print("=" * 90)
    print(prob, "eventos:", dict(events))
    if gen_events:
        print("campos e7_gen:", list(gen_events[0].keys()))
        print("1o e7_gen:", json.dumps(gen_events[0], ensure_ascii=False))
        print("ultimo e7_gen:", json.dumps(gen_events[-1], ensure_ascii=False))
        flags = collections.Counter(g.get("flag") for g in gen_events)
        print("distribuicao flag (diversidade=1?):", dict(flags))
        # ramo por infill
        ramos = collections.Counter()
        for g in gen_events:
            for inf in g.get("infills", []):
                ramos[inf.get("ramo") if isinstance(inf, dict) else str(inf)[:40]] += 1
        print("ramos dos infills:", dict(ramos))
        # Ratio stats
        ratios = [g.get("Ratio") for g in gen_events if g.get("Ratio") is not None]
        print("Ratio: n=%d min=%.4f max=%.4f" % (len(ratios), min(ratios), max(ratios)))
        rold = [g.get("RatioOld") for g in gen_events if g.get("RatioOld") is not None]
        if rold:
            deltas = [ro - r for ro, r in zip(rold, ratios)]
            print("RatioOld-Ratio: min=%.4f max=%.4f, #>0.05: %d" % (min(deltas), max(deltas), sum(1 for d in deltas if d > 0.05)))
        minA = [g.get("min_A_objs") for g in gen_events if g.get("min_A_objs") is not None]
        print("min_A_objs presente em %d eventos; 1o=%s ultimo=%s" % (len(minA), minA[0] if minA else None, minA[-1] if minA else None))
        lt = [g.get("loss_treino") for g in gen_events]
        print("loss_treino valores unicos:", set(str(x)[:20] for x in lt))
        mhp = gen_events[0].get("modelo_hp")
        print("modelo_hp exemplo:", json.dumps(mhp, ensure_ascii=False)[:400] if mhp else mhp)
        print("dup_infill nos e7_gen:", collections.Counter(str(g.get("dup_infill")) for g in gen_events))
    gnames = collections.Counter(g.get("name") for g in guards)
    print("guards por name:", dict(gnames))
    for g in guards[:3]:
        print("  guard ex:", json.dumps(g, ensure_ascii=False)[:300])
    print("footer:", json.dumps(footer, ensure_ascii=False)[:600] if footer else None)
