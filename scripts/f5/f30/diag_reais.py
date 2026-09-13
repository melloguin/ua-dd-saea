#!/usr/bin/env python3
"""DIAGNOSTICO DA ONDA RE21 + ESTOQUE40 — read-only, roda na VM durante o lote.

Responde 4 perguntas, em ordem de urgencia:
  A. A BANDEIRA AMARELA: o piso offline (moead_media/ESTOQUE40) esta MEXENDO,
     ou o length_scale do f2 aterrissou no piso 0,01 e ele congelou de novo?
  B. As celulas que estao saindo passam na bateria de contrato/orcamento?
  C. O RE21 esta numericamente fiel? (reimplementacao independente vs o F gravado)
  D. O c154/ESTOQUE40 esta a caminho do teto de 12h?

Uso na VM:   python3 diag_reais.py [RAIZ]
  RAIZ default = ~/ua-dd-saea/data/experiments
NAO escreve nada. NAO importa nada do harness. NAO invoca experiments.
"""
import sys, os, glob, json, collections
import numpy as np

RAIZ = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/ua-dd-saea/data/experiments")
try:
    import pyarrow.parquet as pq
except ImportError:
    print("!! pyarrow ausente neste interpretador — use o venv do projeto"); sys.exit(1)

def celulas(prob):
    """(exp, alg, seed, prefixo) de todas as celulas do problema."""
    out = []
    for exp in ("main", "off"):
        for m in glob.glob(f"{RAIZ}/{exp}/*/exp_{exp}_*_{prob}_*.manifest.json"):
            if "__final" in m: continue
            b = m[:-len(".manifest.json")]; nome = os.path.basename(b)
            alg = os.path.basename(os.path.dirname(m))
            out.append((exp, alg, nome.rsplit("_", 1)[1], b))
    return sorted(out)

def linhas(b, suf):
    p = b + suf
    return pq.read_table(p).num_rows if os.path.exists(p) else None

def rodape(b):
    f = None
    try:
        for l in open(b + ".jsonl", errors="ignore"):
            if '"footer"' in l: f = json.loads(l.strip())
    except OSError: pass
    return f

print("=" * 78)
print(f"DIAGNOSTICO DA ONDA REAL — raiz {RAIZ}")
print("=" * 78)

# ───────────────────────── A · A BANDEIRA AMARELA ─────────────────────────
print("\n[A] BANDEIRA AMARELA — o piso offline do ESTOQUE40 esta mexendo?")
print("    (D102.19 registrou: 'fit do f2 instavel sob alpha=0, pode aterrissar ls=0,01')")
_off = [c for c in celulas("ESTOQUE40") if c[1] in ("moead_media", "b5r", "b5m", "e103")]
# estratifica por config (senao a ordem alfabetica gasta a cota toda no b5r)
_por = {}
for c in _off: _por.setdefault(c[1], []).append(c)
alvo = [c for cfg in sorted(_por) for c in _por[cfg][:4]]
if not alvo:
    print("    (nenhuma celula offline de ESTOQUE40 ainda — o lote comeca pelos pisos MATLAB)")
for exp, alg, seed, b in alvo:
    p3 = b + "__surrogate.parquet"
    if not os.path.exists(p3):
        print(f"    {alg:12s} s{seed:<3s} (3) ausente"); continue
    t = pq.read_table(p3)
    reg = np.array([str(x) for x in t.column("regime").to_pylist()]) if "regime" in t.column_names else np.array(["?"] * t.num_rows)
    m = reg != "sonda"
    g = np.asarray(t.column("geracao"), int)[m]
    xc = sorted([c for c in t.column_names if c[0] == "x" and c[1:].isdigit()], key=lambda c: int(c[1:]))
    X = np.column_stack([np.asarray(t.column(c), float)[m] for c in xc])
    gs = sorted(set(g.tolist()))
    mud = sum(1 for i in range(1, len(gs))
              if not np.array_equal(np.sort(X[g == gs[i-1]], 0), np.sort(X[g == gs[i]], 0)))
    tot = max(1, len(gs) - 1)
    flag = "CONGELADO !!" if mud == 0 else ("suspeito" if mud / tot < 0.5 else "ok")
    print(f"    {alg:12s} s{seed:<3s} ger {gs[0]}..{gs[-1]} ({len(gs)}) · transicoes com mudanca "
          f"{mud}/{tot} ({100*mud/tot:5.1f}%)  -> {flag}")

# o length_scale: descobre o campo no (6) sem supor o nome
print("\n    length_scale / hiperparametros do GP (varredura dos campos do (6)):")
for exp, alg, seed, b in alvo[:4]:
    achou = {}
    try:
        for l in open(b + ".jsonl", errors="ignore"):
            if '"fit"' not in l and '"decision"' not in l: continue
            d = json.loads(l.strip())
            for k, v in d.items():
                lk = k.lower()
                if any(s in lk for s in ("length", "_ls", "ls_", "theta", "kernel", "hp")):
                    achou.setdefault(k, []).append(v)
    except OSError: pass
    if not achou:
        print(f"    {alg:12s} s{seed:<3s} (nenhum campo de hiperparametro no (6))"); continue
    for k, vs in achou.items():
        try:
            a = np.asarray([x for x in vs if isinstance(x, (int, float))], float)
            if not a.size: continue
            nopiso = int((np.abs(a - 0.01) < 1e-9).sum())
            print(f"    {alg:12s} s{seed:<3s} {k}: n={a.size} min={a.min():.4g} med={np.median(a):.4g} "
                  f"max={a.max():.4g} · no piso 0,01: {nopiso}/{a.size}"
                  + ("   <<< BANDEIRA CONFIRMADA" if nopiso > a.size * 0.5 else ""))
        except Exception:
            print(f"    {alg:12s} s{seed:<3s} {k}: {str(vs[:2])[:90]}")

# ───────────────────────── B · CONTRATO E ORCAMENTO ─────────────────────────
print("\n[B] BATERIA DE CONTRATO nas celulas ja fechadas")
for prob in ("RE21", "ESTOQUE40"):
    cs = celulas(prob)
    if not cs:
        print(f"    {prob}: nenhuma celula ainda"); continue
    ok = mal6 = semfoot = orc = falta5 = 0
    fes = []
    for exp, alg, seed, b in cs:
        M = json.load(open(b + ".manifest.json"))
        f = rodape(b)
        if (M.get("status") == "ok") or ((f or {}).get("status") == "ok"): ok += 1
        if f is None: semfoot += 1
        n1 = linhas(b, "__real.parquet")
        if M.get("fe_final") is not None and M.get("maxfe") is not None:
            if M["fe_final"] == M["maxfe"] and n1 == M["fe_final"]: orc += 1
            fes.append((M["fe_final"], M["maxfe"]))
        if not all(M.get(k) for k in ("params", "sigma_dict", "campanha_id", "repo_hash")): falta5 += 1
        try:
            n = sum(1 for l in open(b + ".jsonl", errors="ignore") if l.strip() and not l.strip().startswith("{"))
            mal6 += 1 if n else 0
        except OSError: pass
    mx = collections.Counter(m for _, m in fes)
    print(f"    {prob}: {len(cs)} celulas · ok {ok} · orcamento fecha {orc}/{len(fes)} · "
          f"(6) sem footer {semfoot} · (6) malformadas {mal6} · (5) incompleto {falta5}")
    print(f"           maxfe observado: {dict(mx)}   (esperado RE21=123 · ESTOQUE40=1239)")

# ───────────────────────── C · FIDELIDADE DO RE21 ─────────────────────────
print("\n[C] FIDELIDADE NUMERICA DO RE21 — reimplementacao independente vs o F gravado")
cs = celulas("RE21")
if cs:
    F_, S_, E_, L_ = 10.0, 10.0, 2.0e5, 200.0
    a = F_ / S_
    piores = []
    for exp, alg, seed, b in cs[:40]:
        p1 = b + "__real.parquet"
        if not os.path.exists(p1): continue
        t = pq.read_table(p1)
        xc = sorted([c for c in t.column_names if c[0] == "x" and c[1:].isdigit()], key=lambda c: int(c[1:]))
        if len(xc) != 4: continue
        X = np.column_stack([np.asarray(t.column(c), float) for c in xc])
        Fg = np.column_stack([np.asarray(t.column(c), float) for c in ("f0", "f1")])
        f1 = L_ * (2*X[:,0] + np.sqrt(2.0)*X[:,1] + np.sqrt(X[:,2]) + X[:,3])
        f2 = (F_*L_/E_) * (2.0/X[:,0] + 2.0*np.sqrt(2.0)/X[:,1]
                           - 2.0*np.sqrt(2.0)/X[:,2] + 2.0/X[:,3])
        rel = np.abs(np.column_stack([f1, f2]) - Fg) / np.maximum(1e-30, np.abs(Fg))
        piores.append((rel.max(), alg, seed))
        lo = np.array([a, np.sqrt(2)*a, np.sqrt(2)*a, a]); hi = np.array([3*a]*4)
        viol = int(((X < lo - 3e-8) | (X > hi + 3e-8)).sum())
        if viol: piores.append((9e9, alg + "!CAIXA", seed))
    if piores:
        piores.sort(reverse=True)
        print(f"    {len(piores)} celulas conferidas · erro relativo MAXIMO global: {piores[0][0]:.3e}")
        print(f"    piores 3: " + " · ".join(f"{alg}/s{s} {e:.2e}" for e, alg, s in piores[:3]))
        print(f"    -> {'FIEL (dentro do float32 do export)' if piores[0][0] < 1e-6 else 'INVESTIGAR !!'}")
else:
    print("    (nenhuma celula de RE21 ainda)")

# ───────────────────────── D · O RISCO DO c154 ─────────────────────────
print("\n[D] c154/ESTOQUE40 — a caminho do teto de 12h?")
c154 = [c for c in celulas("ESTOQUE40") if c[1] == "c154"]
if not c154:
    print("    (c154 ainda nao comecou — ele e um dos ultimos da fila)")
for exp, alg, seed, b in c154[:8]:
    M = json.load(open(b + ".manifest.json")); f = rodape(b)
    tt = (M.get("timing") or {}).get("tempo_total_s") or M.get("tempo_total_s")
    print(f"    s{seed:<3s} status={M.get('status')} motivo={M.get('motivo_parada')} "
          f"fe={M.get('fe_final')}/{M.get('maxfe')} tempo={tt}")
print("\n" + "=" * 78)
