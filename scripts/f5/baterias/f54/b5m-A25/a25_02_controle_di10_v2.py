#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A25 / controle transversal v2 — agora sobre TODOS os tipos de registro `rec`
(o v1 so olhava rec=='decision' e zerava os configs MATLAB).
Para cada config: 1 celula, uniao das chaves por rec + veredito DI-10 especifico.
"""
import json, os, csv, collections

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/b5m-A25"

ESPERADO = {
    "b1":   ["lambda", "ei_best", "n_pool_ga"],
    "b3":   ["apd_sel", "sigma_sel", "n_vetores_vazios", "adapt_delta_V"],
    "b4":   ["solution_id", "rr", "tr"],
    "e7":   ["n_clusters_efetivo", "cluster", "loss_treino"],
    "c217": ["n_best", "n_worst", "pmid"],
    "c141": ["n_por_nivel", "rbf"],
    "e74":  ["n_por_nivel", "k_local"],
    "c238": ["eim_mediana_pool"],
    "c262": ["acqf_todos_restarts", "n_baseline", "mll_final"],
    "c154": ["acqf_todos_restarts", "n_baseline", "mll_final"],
    "e81":  ["n_train", "draws"],
    "c149": ["hvi_top5", "std_ensemble_sel"],
    "c122": ["n_acordo", "n_desacordo"],
    "b5m":  ["p_wrong", "peso"],
    "b5r":  ["p_wrong"],
    "c311": ["n_folhas", "profundidade"],
    "e103": ["divergencia_modelos", "margem_3sigma"],
    "moead_media": ["ideal", "nadir", "vetor"],
    "moead": ["ideal", "nadir", "vetor"],
    "nsga3": ["ideal", "nadir", "vetor"],
    "nsga2": ["ideal", "nadir"], "smsemoa": ["ideal", "nadir"],
    "treed_media": ["n_folhas", "profundidade"],
    "sobol_batch": [],
}

rows = []
for cfg in sorted(os.listdir(ROOT)):
    if cfg.startswith(".") or cfg.startswith("_"):
        continue
    base = os.path.join(ROOT, cfg)
    if not os.path.isdir(base):
        continue
    alvo = None
    for lab in sorted(os.listdir(base)):
        d = os.path.join(base, lab, "42")
        if not os.path.isdir(d):
            continue
        js = [f for f in os.listdir(d) if f.endswith(".jsonl")]
        if js:
            alvo = (lab, os.path.join(d, js[0]))
            break
    if alvo is None:
        continue
    lab, path = alvo
    per_rec = collections.defaultdict(set)
    n_rec = collections.Counter()
    hdr_all = set()
    with open(path) as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            r = o.get("rec", "?")
            n_rec[r] += 1
            per_rec[r] |= set(o.keys())
            if r == "header":
                def flat(d, pre=""):
                    for k, v in d.items():
                        hdr_all.add(pre + str(k))
                        if isinstance(v, dict):
                            flat(v, pre + str(k) + ".")
                flat(o)
    universo = set()
    for s in per_rec.values():
        universo |= s
    universo |= hdr_all
    esp = ESPERADO.get(cfg, [])
    ach = [e for e in esp if any(e.lower() in k.lower() for k in universo)]
    gen_rec = max(n_rec, key=lambda r: n_rec[r] if r not in ("header",) else -1) \
        if n_rec else "?"
    rows.append(dict(
        config=cfg, celula=lab, recs=";".join("%s=%d" % (k, v) for k, v in sorted(n_rec.items())),
        di10_esperado=";".join(esp) or "(nenhum)",
        di10_encontrado=";".join(ach) or "(NENHUM)",
        cobertura=("%d/%d" % (len(ach), len(esp))) if esp else "n/a",
        n_chaves_universo=len(universo),
        chaves_rec_principal=";".join(sorted(per_rec.get(gen_rec, []))),
    ))
    print("%-13s %-20s DI10=%-5s recs=%s" %
          (cfg, lab, ("%d/%d" % (len(ach), len(esp))) if esp else "n/a",
           ";".join("%s=%d" % (k, v) for k, v in sorted(n_rec.items()))[:110]))
    if esp and len(ach) < len(esp):
        print("      faltam: %s" % [e for e in esp if e not in ach])

with open(os.path.join(OUT, "a25_controle_di10_v2.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    [w.writerow(r) for r in rows]
print("\nOK ->", os.path.join(OUT, "a25_controle_di10_v2.csv"))
