#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A25 / controle transversal: o enriquecimento DI-10 ESPECIFICO por config
existe no jsonl (camada 6)? Varre 1 celula por config (a 1a em ordem) e lista
as chaves do header e a UNIAO das chaves dos eventos <alg>_gen.
Saida: a25_controle_di10.csv  (READ-ONLY sobre os dados)
"""
import json, os, sys, csv, collections

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/b5m-A25"

# o que o CONTRATO_DE_DADOS.md 6.1 pede de ESPECIFICO por config (coluna +DI-10)
ESPERADO = {
    "b1":   ["lambda_vetor", "ei_best", "n_pool_ga"],
    "b3":   ["apd_sel", "sigma_sel", "n_vetores_vazios", "adapt_delta_V"],
    "b4":   ["solution_id", "rr", "tr"],
    "e7":   ["n_clusters_efetivo", "cluster", "loss_treino"],
    "c217": ["n_best", "n_worst", "n_pmid"],
    "c141": ["n_por_nivel", "hp_rbf"],
    "e74":  ["n_por_nivel", "k_local_efetivo"],
    "c238": ["eim_mediana_pool"],
    "c262": ["acqf_todos_restarts", "n_baseline", "mll_final"],
    "c154": ["acqf_todos_restarts", "n_baseline", "mll_final"],
    "e81":  ["n_train", "draws"],
    "c149": ["hvi_top5", "std_ensemble_sel"],
    "c122": ["n_acordo", "n_desacordo"],
    "b5m":  ["p_wrong_stats"],
    "b5r":  ["p_wrong_stats"],
    "c311": ["n_folhas", "profundidade"],
    "e103": ["divergencia_modelos", "margem_3sigma"],
    "moead_media": ["ideal", "nadir"],
    "moead": ["ideal", "nadir"], "nsga2": ["ideal", "nadir"],
    "nsga3": ["ideal", "nadir"], "smsemoa": ["ideal", "nadir"],
    "sobol_batch": [],
    "treed_media": ["n_folhas", "profundidade"],
}


def varre(cfg):
    base = os.path.join(ROOT, cfg)
    if not os.path.isdir(base):
        return None
    labels = sorted(d for d in os.listdir(base) if not d.startswith("."))
    for lab in labels:
        d = os.path.join(base, lab, "42")
        if not os.path.isdir(d):
            continue
        js = [f for f in os.listdir(d) if f.endswith(".jsonl")]
        if not js:
            continue
        p = os.path.join(d, js[0])
        hdr_keys, gen_keys, n_gen, recs = [], collections.Counter(), 0, collections.Counter()
        sigma_keys = []
        with open(p) as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    o = json.loads(ln)
                except Exception:
                    continue
                rec = o.get("rec")
                recs[rec] += 1
                if rec == "header":
                    hdr_keys = sorted(o.keys())
                    sd = o.get("sigma_dict") or {}
                    if isinstance(sd, dict):
                        sigma_keys = sorted(sd.keys())
                elif rec == "decision":
                    n_gen += 1
                    for k in o.keys():
                        gen_keys[k] += 1
        return dict(cfg=cfg, label=lab, arquivo=p, n_dec=n_gen,
                    recs=dict(recs), hdr=hdr_keys, sigma=sigma_keys,
                    gen=sorted(gen_keys))
    return None


rows = []
for cfg in sorted(os.listdir(ROOT)):
    if cfg.startswith(".") or cfg.startswith("_"):
        continue
    r = varre(cfg)
    if r is None:
        continue
    esp = ESPERADO.get(cfg, [])
    todas = set(r["hdr"]) | set(r["gen"]) | set(r["sigma"])
    # match por substring (tolerante a renomeacao parcial)
    achadas = [e for e in esp
               if any(e.lower() in k.lower() for k in todas)]
    rows.append(dict(
        config=cfg, celula=r["label"], n_eventos_decision=r["n_dec"],
        di10_esperado=";".join(esp) or "(nenhum)",
        di10_encontrado=";".join(achadas) or "(nenhum)",
        cobertura="%d/%d" % (len(achadas), len(esp)) if esp else "n/a",
        n_chaves_header=len(r["hdr"]), n_chaves_sigma=len(r["sigma"]),
        chaves_gen=";".join(r["gen"]),
        chaves_header=";".join(r["hdr"]),
    ))
    print("%-14s %-22s dec=%-6d DI10 %s  gen_keys=%s"
          % (cfg, r["label"], r["n_dec"],
             "%d/%d" % (len(achadas), len(esp)) if esp else "n/a",
             ";".join(r["gen"])))

with open(os.path.join(OUT, "a25_controle_di10.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("\nOK ->", os.path.join(OUT, "a25_controle_di10.csv"))
