#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A25 / passo 2 — REPRODUCAO INDEPENDENTE da medicao do analista, nas 45/45
celulas do b5m (nao em amostra). Mede:
  - n eventos por rec; chaves do header; chaves do sigma_dict
  - presenca de QUALQUER chave que case p_wrong / prob / peso / weight / vetor
    / lattice / neighbor (busca AMPLA, nao literal — anti falso-positivo por
    renomeacao)
  - o mesmo para b5r e moead_media (o trio desdeo) e para 2 controles
    positivos (c311 e moead) — configs que TEM o DI-10 especifico.
Saida: a25_reproducao.csv + a25_reproducao.txt
"""
import json, os, csv, collections, re

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/b5m-A25"

PADRAO = re.compile(r"p_?wrong|probab|peso|weight|vetor|vector|lattice|"
                    r"neighbor|vizinh|decompos|substitu|replace|selection",
                    re.I)


def achatar(o, pre=""):
    out = {}
    for k, v in o.items():
        kk = pre + str(k)
        out[kk] = v
        if isinstance(v, dict):
            out.update(achatar(v, kk + "."))
    return out


def varre_config(cfg):
    base = os.path.join(ROOT, cfg)
    linhas = []
    for lab in sorted(os.listdir(base)):
        d = os.path.join(base, lab, "42")
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".jsonl"):
                continue
            p = os.path.join(d, f)
            n_rec = collections.Counter()
            hdr, sig = [], []
            gen_keys = collections.Counter()
            hits = collections.Counter()
            n_dec = 0
            with open(p) as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        o = json.loads(ln)
                    except Exception:
                        n_rec["__ilegivel__"] += 1
                        continue
                    r = o.get("rec", "?")
                    n_rec[r] += 1
                    plano = achatar(o)
                    for k in plano:
                        if PADRAO.search(k):
                            hits[r + ":" + k] += 1
                    if r == "header":
                        hdr = sorted(o.keys())
                        sd = o.get("sigma_dict") or {}
                        sig = sorted(sd.keys())
                        for k, v in sd.items():
                            if PADRAO.search(str(v)):
                                hits["header:sigma_dict[%s]~texto" % k] += 1
                    elif r in ("decision", "b5_gen"):
                        n_dec += 1
                        for k in o:
                            gen_keys[k] += 1
            linhas.append(dict(
                config=cfg, celula=lab, arquivo=f,
                n_header=n_rec.get("header", 0), n_decision=n_dec,
                n_sonda=n_rec.get("sonda", 0), n_footer=n_rec.get("footer", 0),
                n_guard=n_rec.get("guard", 0),
                n_chaves_header=len(hdr), n_chaves_sigma=len(sig),
                chaves_header=";".join(hdr),
                chaves_sigma=";".join(sig),
                chaves_decision=";".join(sorted(gen_keys)),
                hits_padrao=";".join(sorted(hits)) or "(NENHUM)",
            ))
    return linhas


todas = []
for cfg in ["b5m", "b5r", "moead_media", "c311", "moead"]:
    ls = varre_config(cfg)
    todas += ls
    n = len(ls)
    dec = sum(l["n_decision"] for l in ls)
    sem_hit = sum(1 for l in ls if l["hits_padrao"] == "(NENHUM)")
    kh = set(l["n_chaves_header"] for l in ls)
    ks = set(l["n_chaves_sigma"] for l in ls)
    kd = set(l["chaves_decision"] for l in ls)
    print("== %-12s celulas=%3d  eventos_gen=%7d  header_keys=%s  sigma_keys=%s"
          % (cfg, n, dec, sorted(kh), sorted(ks)))
    print("   celulas SEM nenhuma chave casando o padrao amplo: %d/%d" % (sem_hit, n))
    for k in sorted(kd):
        print("   chaves_decision (invariante?): %s" % (k or "(vazio)"))
    hs = collections.Counter()
    for l in ls:
        for h in l["hits_padrao"].split(";"):
            hs[h] += 1
    print("   hits do padrao amplo:", dict(hs))
    print()

with open(os.path.join(OUT, "a25_reproducao.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(todas[0].keys()))
    w.writeheader()
    [w.writerow(r) for r in todas]
print("OK ->", os.path.join(OUT, "a25_reproducao.csv"))
