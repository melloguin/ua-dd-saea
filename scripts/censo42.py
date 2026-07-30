#!/usr/bin/env python3
# =============================================================================
# censo42.py — inventário READ-ONLY dos outputs de uma semente, por máquina.
#
# Responde, contra o runs_matrix.csv (nunca contra lista digitada):
#   quantas células terminaram COM SUCESSO (manifesto ok + todas as camadas)
#   quantas terminaram INCOMPLETAS (manifesto ok, mas falta camada)
#   quantas foram ABORTADAS (motivo_parada sancionado — DI-38a)
#   quantas FALHARAM de verdade (traceback)
#   quantas ficaram SEM MANIFESTO (o processo morreu antes de certificar)
#   quantas ainda estão NA FILA (nada no disco)
#   quantas foram RETIRADAS por decisão (batch/c154 — DI-40)
#
# NÃO escreve nada dentro do repo. NÃO toca em _baseline_pre_retrofit (a varredura
# é dirigida pelo artefato, então nem enxerga esse diretório). Só lê e conta.
#
# USO
#   python3 censo42.py                  # roster desta máquina, semente 42
#   MAQ=v5 python3 censo42.py           # força a máquina
#   ROSTER=todos python3 censo42.py     # as 695 células (árvore consolidada)
#   SEMENTE=1 python3 censo42.py        # outra semente
#
# Sai com o resumo no stdout e uma linha por célula em ~/censo_<maq>_<sem>.csv
# =============================================================================
import csv, os, json, sys, socket, collections

SEM    = os.environ.get("SEMENTE", "42")
DROOT  = os.environ.get("LOTE_DATA_ROOT", "data")
ROSTER = os.environ.get("ROSTER", "")

# ── repo (mesma busca dos demais scripts da operação) ───────────────────────
REPO = ""
for c in (os.environ.get("REPO_DIR", ""), os.getcwd(),
          os.path.expanduser("~/ua-dd-saea"),
          os.path.expanduser("~/Documents/python_repos/mestrado/ua-dd-saea"),
          "/home/jupyter/ua-dd-saea"):
    if c and os.path.isdir(os.path.join(c, ".git")):
        REPO = os.path.abspath(c)
        break
if not REPO:
    sys.exit("FATAL: repo nao encontrado (usuario=%s HOME=%s)"
             % (os.environ.get("USER", "?"), os.path.expanduser("~")))

# ── máquina ────────────────────────────────────────────────────────────────
H = socket.gethostname().split(".")[0]
MAQ = os.environ.get("MAQ", "")
if not MAQ:
    if   H.startswith("v5-mestrado"): MAQ = "v5"
    elif H.startswith("mestrado-v6"): MAQ = "v6"
    elif H.startswith("matlab-vm3"):  MAQ = "vm3"
    elif sys.platform == "darwin":    MAQ = "mac"
if ROSTER == "todos":
    MAQ = MAQ or "todos"
elif not MAQ:
    sys.exit("FATAL: nao reconheci o host '%s'. Rode com MAQ=v5|v6|vm3|mac." % H)

# ── rosters: quem é dono de quais pares (exp/alg) ───────────────────────────
# Soma 695 = 50 (v5) + 70 (v6, inclui os 5 de batch/c154 retirados) + 345 (vm3)
# + 230 (mac). Os perfis vêm do lote3s.sh; v5 ganha main/c154 e v6 ganha
# batch/c262 e batch/c154, que rodaram lá mas moram na fase opcional do perfil.
ROSTERS = {
 "v5":  "main/c149 main/c154",
 "v6":  "main/c262 main/c122 batch/c149 batch/sobol_batch batch/c262 batch/c154",
 "vm3": ("main/nsga2 main/nsga3 main/moead main/smsemoa main/c141 main/c217 "
         "main/b3 main/e74 main/b4 main/b1 main/e7 main/c238 off/e103 "
         "sweep-small-lhs/e103 sweep-small-mvns/e103 "
         "sweep-medium-lhs/e103 sweep-medium-mvns/e103"),
 "mac": ("off/c311 off/moead_media off/b5r off/b5m main/e81 batch/e81 "
         "sweep-small-lhs/c311 sweep-small-mvns/c311 "
         "sweep-medium-lhs/c311 sweep-medium-mvns/c311 "
         "sweep-big-lhs/c311 sweep-big-mvns/c311 "
         "sweep-big-lhs/treed_media sweep-big-mvns/treed_media "
         "sweep-small-lhs/moead_media sweep-small-mvns/moead_media "
         "sweep-medium-lhs/moead_media sweep-medium-mvns/moead_media "
         "sweep-small-lhs/b5r sweep-small-mvns/b5r "
         "sweep-medium-lhs/b5r sweep-medium-mvns/b5r "
         "sweep-small-lhs/b5m sweep-small-mvns/b5m "
         "sweep-medium-lhs/b5m sweep-medium-mvns/b5m"),
}
ALVO = None if ROSTER == "todos" else {tuple(p.split("/", 1))
                                       for p in ROSTERS[MAQ].split()}

# ── as 7 camadas do CONTRATO_DE_DADOS ──────────────────────────────────────
CAMADAS = [("1", "__real.parquet"),      ("2", "__pop.parquet"),
           ("3", "__surrogate.parquet"), ("4", "__timing.parquet"),
           ("5", ".manifest.json"),      ("6", ".jsonl"),
           ("7", "__final.parquet")]
# [B-06] FONTE ÚNICA: `artifacts/motivos_parada.json` (era um literal aqui, um no
# accept e um no portão — e em 2026-07-25 o literal foi cravado ERRADO,
# 'cache_cap' em vez de 'cache_hit_travado', DI-41.2).
sys.path.insert(0, os.path.join(REPO, "scripts"))
from gates_proveniencia import _artefato as _art_motivos  # noqa: E402
ABORTO_SANCIONADO = set(_art_motivos("motivos_parada.json")["sancionados"])

A = os.path.join(REPO, "claude_code_context", "artifacts")
with open(os.path.join(A, "runs_matrix.csv"), encoding="utf-8") as fh:
    TODAS = [r for r in csv.DictReader(fh) if r["semente"] == SEM]
if not TODAS:
    sys.exit("FATAL: semente %s nao existe no runs_matrix.csv (0..28 e 42)." % SEM)

# ── varredura ──────────────────────────────────────────────────────────────
reg, fora = [], 0
for r in TODAS:
    exp, alg, prob = r["exp"], r["alg"], r["problema"]
    if ALVO is not None and (exp, alg) not in ALVO:
        fora += 1
        continue
    base = os.path.join(REPO, DROOT, "experiments", exp, alg,
                        "exp_%s_%s_%s_%s" % (exp, alg, prob, SEM))
    assin, nbytes = "", 0
    for tag, suf in CAMADAS:
        try:
            nbytes += os.path.getsize(base + suf)
            assin += tag
        except OSError:
            pass
    det, fe = "", ""
    if exp == "batch" and alg == "c154":
        est = "RETIRADO"
        det = "DI-40 (aborto certo, zero parquet)"
    elif "5" not in assin:
        est = "FILA" if not assin else "SEM-MANIFESTO"
    else:
        try:
            with open(base + ".manifest.json", encoding="utf-8") as fh:
                m = json.load(fh)
        except Exception as e:
            est, m = "ILEGIVEL", {}
            det = "%s: %s" % (type(e).__name__, e)
        else:
            st  = m.get("status")
            mot = str(m.get("motivo_parada") or "")
            fe  = "%s/%s" % (m.get("fe_final"), m.get("maxfe"))
            if st in ("ok", "retried_ok"):
                est = "OK"
            elif mot in ABORTO_SANCIONADO:
                est, det = "ABORTADO", mot
            else:
                tr = (m.get("stack_trace") or "").strip().splitlines()
                est = "FALHOU"
                det = (tr[-1][:110] if tr else (mot or str(st) or "?"))
    reg.append([exp, alg, prob, est, assin, nbytes, fe, det])

# ── completo x incompleto: a assinatura MODAL dos OK de cada (exp,alg) é o
#    gabarito. Auto-calibra em vez de eu supor quais camadas cada família grava
#    (os 4 pisos online nao tem surrogate; so o offline tem a camada 7).
# ─────────────────────────────────────────────────────────────────────────---
modal = {}
for exp, alg, prob, est, assin, nb, fe, det in reg:
    if est == "OK":
        modal.setdefault((exp, alg), collections.Counter())[assin] += 1
GAB = {k: max(v.items(), key=lambda kv: (kv[1], kv[0]))[0] for k, v in modal.items()}
for row in reg:
    if row[3] == "OK":
        g = GAB.get((row[0], row[1]), row[4])
        falta = [t for t in g if t not in row[4]]
        if falta:
            row[3] = "OK-INCOMPLETO"
            row[7] = "faltam camadas %s (gabarito %s do config)" % ("".join(falta), g)

# ── saída ──────────────────────────────────────────────────────────────────
ORD = ["OK", "INCOMPL", "ABORT", "FALHOU", "S/MANIF", "ILEGIV", "RETIR", "FILA"]
ROT = {"OK":"OK", "OK-INCOMPLETO":"INCOMPL", "ABORTADO":"ABORT", "FALHOU":"FALHOU",
       "SEM-MANIFESTO":"S/MANIF", "ILEGIVEL":"ILEGIV", "RETIRADO":"RETIR", "FILA":"FILA"}
FAM = lambda e: (e if e in ("main", "off", "batch") else "sweep")
cnt, fam, alv = collections.Counter(), collections.defaultdict(collections.Counter), \
                collections.defaultdict(collections.Counter)
tot_bytes = 0
for exp, alg, prob, est, assin, nb, fe, det in reg:
    cnt[ROT[est]] += 1
    fam[FAM(exp)][ROT[est]] += 1
    alv["%s/%s" % (exp, alg)][ROT[est]] += 1
    tot_bytes += nb

W = "%-30s" + " %6s" * len(ORD)
print("=" * 78)
print(" CENSO · maquina=%s · semente=%s · repo=%s" % (MAQ, SEM, REPO))
print(" roster desta maquina: %d celulas   (fora do roster: %d, sao de outra maquina)"
      % (len(reg), fora))
print(" volume escrito em disco: %.2f GB" % (tot_bytes / 1073741824.0))
print("=" * 78)
print(W % tuple(["familia"] + ORD))
for f in ("main", "off", "sweep", "batch"):
    if fam.get(f):
        print(W % tuple([f] + [fam[f][k] or "." for k in ORD]))
print(W % tuple(["TOTAL"] + [cnt[k] or "." for k in ORD]))
print()
print(" por config:")
print(W % tuple([""] + ORD))
for k in sorted(alv):
    print(W % tuple([k] + [alv[k][x] or "." for x in ORD]))

for rot in ("FALHOU", "OK-INCOMPLETO", "SEM-MANIFESTO", "ILEGIVEL"):
    linhas = [r for r in reg if r[3] == rot]
    if linhas:
        print("\n %s (%d):" % (rot, len(linhas)))
        for exp, alg, prob, est, assin, nb, fe, det in linhas:
            print("   %-22s %-12s camadas=%-7s fe=%-9s %s"
                  % ("%s/%s" % (exp, alg), prob, assin or "-", fe, det))

out = os.path.join(os.path.expanduser("~"), "censo_%s_%s.csv" % (MAQ, SEM))
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["maquina", "exp", "alg", "problema", "semente", "estado",
                "camadas", "bytes", "fe_final_maxfe", "detalhe"])
    for exp, alg, prob, est, assin, nb, fe, det in reg:
        w.writerow([MAQ, exp, alg, prob, SEM, est, assin, nb, fe, det])
print("\n uma linha por celula em: %s" % out)