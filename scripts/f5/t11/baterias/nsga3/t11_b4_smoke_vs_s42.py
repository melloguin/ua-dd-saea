"""T11/nsga3 — bateria 4: o SMOKE T11 (main/nsga3/DTLZ2/42) contra a MESMA celula da s42.
O que a instrumentacao T11 acrescentou, o que mudou, e se o MECANISMO e' identico.
READ-ONLY. Saida: smoke_vs_s42.txt (stdout)
"""
import json, os, glob
import numpy as np
import pandas as pd

S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3/DTLZ2/42"
SMK = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/nsga3"


def carrega(d):
    man = json.load(open(glob.glob(os.path.join(d, "*.manifest.json"))[0]))
    recs = []
    for ln in open(glob.glob(os.path.join(d, "*.jsonl"))[0]):
        ln = ln.strip()
        if not ln:
            continue
        recs.append(json.loads(ln))
    lay = {}
    for k in ["real", "pop", "surrogate", "timing"]:
        p = glob.glob(os.path.join(d, "*__%s.parquet" % k))
        lay[k] = pd.read_parquet(p[0]) if p else None
    return man, recs, lay


ma, ra, la = carrega(S42)
mb, rb, lb = carrega(SMK)

print("=" * 78)
print("A) INVENTARIO DE REGISTROS DO (6)")
from collections import Counter
ca, cb = Counter(r.get("rec") for r in ra), Counter(r.get("rec") for r in rb)
for k in sorted(set(ca) | set(cb)):
    print("  %-14s s42=%-5d smoke=%-5d %s" % (k, ca.get(k, 0), cb.get(k, 0),
                                              "<-- DIFERE" if ca.get(k, 0) != cb.get(k, 0) else ""))

print()
print("B) CAMPOS NOVOS/PERDIDOS por tipo de registro")
for k in sorted(set(ca) & set(cb)):
    fa = set().union(*[set(r) for r in ra if r.get("rec") == k])
    fb = set().union(*[set(r) for r in rb if r.get("rec") == k])
    novo, perd = sorted(fb - fa), sorted(fa - fb)
    if novo or perd:
        print("  %-14s NOVO=%s  PERDIDO=%s" % (k, novo, perd))
    else:
        print("  %-14s (campos identicos)" % k)

print()
print("C) HEADER — diff campo a campo")
ha = [r for r in ra if r.get("rec") == "header"][0]
hb = [r for r in rb if r.get("rec") == "header"][0]
for k in sorted(set(ha) | set(hb)):
    va, vb = ha.get(k, "<AUSENTE>"), hb.get(k, "<AUSENTE>")
    if va != vb:
        print("  %-22s s42=%r\n  %-22s smk=%r" % (k, va, "", vb))
print("  (iguais: %s)" % sorted(k for k in set(ha) & set(hb) if ha[k] == hb[k]))

print()
print("D) FOOTER")
fa = [r for r in ra if r.get("rec") == "footer"]
fb = [r for r in rb if r.get("rec") == "footer"]
print("  n_footer s42=%d smoke=%d" % (len(fa), len(fb)))
for k in sorted(set(fa[0]) | set(fb[0])):
    va, vb = fa[0].get(k, "<AUSENTE>"), fb[0].get(k, "<AUSENTE>")
    print("  %-22s s42=%-30r smk=%r" % (k, va, vb))

print()
print("E) MECANISMO — identidades")
for nome, (m, r, l) in [("s42", (ma, ra, la)), ("smoke", (mb, rb, lb))]:
    dec = [x for x in r if x.get("rec") == "decomposicao"]
    sed = [x for x in r if x.get("rec") == "seeding"]
    gen = [x for x in r if x.get("rec") == "nsga3_gen"]
    gua = [x for x in r if x.get("rec") == "guard"]
    W = np.array(dec[0]["vetores"], dtype=float) if dec else None
    print("  [%s] maxfe=%d fe_final=%d |1|=%d n_ger=%d |2|=%d |4|=%d |3|=%d cache=%d guards=%s"
          % (nome, m["maxfe"], m["fe_final"], len(l["real"]), m["n_geracoes"],
             len(l["pop"]), len(l["timing"]), len(l["surrogate"]), m["cache_hits"],
             dict(Counter(g.get("name") for g in gua))))
    print("       decomposicao=%d seeding=%d N_lattice=%s W.shape=%s"
          % (len(dec), len(sed), dec[0].get("N_lattice") if dec else None,
             None if W is None else W.shape))
    if sed:
        print("       seeding: %s" % {k: v for k, v in sed[0].items() if k not in ("rec", "ts")})
    npop = sorted(set(g.get("n_pop") for g in gen))
    print("       n_pop unicos=%s  fe(gen1)=%s  fe(ultima)=%s"
          % (npop, gen[0]["fe"], gen[-1]["fe"]))

print()
print("F) LATTICE bit-a-bit s42 x smoke")
Wa = np.array([x for x in ra if x.get("rec") == "decomposicao"][0]["vetores"], dtype=float)
Wb = np.array([x for x in rb if x.get("rec") == "decomposicao"][0]["vetores"], dtype=float)
print("  shapes %s %s   max|dW| = %r" % (Wa.shape, Wb.shape, float(np.max(np.abs(Wa - Wb)))))

print()
print("G) BUSCA — a (1) e' a mesma?")
ra_, rb_ = la["real"], lb["real"]
xc = [c for c in ra_.columns if c.startswith("x")]
fc = [c for c in ra_.columns if c.startswith("f") and c[1:].isdigit()]
print("  colunas (1) s42=%d smoke=%d ; iguais=%s" % (len(ra_.columns), len(rb_.columns),
                                                     list(ra_.columns) == list(rb_.columns)))
print("  linhas %d x %d" % (len(ra_), len(rb_)))
n = min(len(ra_), len(rb_))
dx = float(np.max(np.abs(ra_[xc].values[:n] - rb_[xc].values[:n])))
dfv = float(np.max(np.abs(ra_[fc].values[:n] - rb_[fc].values[:n])))
print("  max|dX| = %r   max|df| = %r" % (dx, dfv))
init = 11 * len(xc) - 1
print("  bloco init (%d linhas): max|dX| = %r" % (init,
      float(np.max(np.abs(ra_[xc].values[:init] - rb_[xc].values[:init])))))
print("  doe_hash igual: %s" % (ma["doe_hash"] == mb["doe_hash"]))

print()
print("H) MANIFESTO — params diff")
pa, pb = ma["params"], mb["params"]
for k in sorted(set(pa) | set(pb)):
    va, vb = pa.get(k, "<AUSENTE>"), pb.get(k, "<AUSENTE>")
    if va != vb:
        print("  * %s\n      s42: %r\n      smk: %r" % (k, va, vb))
print("  chaves s42=%d smoke=%d" % (len(pa), len(pb)))
print("  repo_hash s42=%r smoke=%r" % (ma.get("repo_hash"), mb.get("repo_hash")))
print("  campanha_id s42=%r smoke=%r" % (ma.get("campanha_id", "<AUSENTE>"), mb.get("campanha_id")))
print("  schema_version s42=%r smoke=%r" % (ma.get("schema_version"), mb.get("schema_version")))
print("  sigma_dict smoke=%r" % (mb.get("sigma_dict"),))
print("  timing s42=%r" % (ma["timing"],))
print("  timing smk=%r" % (mb["timing"],))
