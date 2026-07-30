#!/usr/bin/env python3
# =============================================================================
# censo_bucket.py — censo de uma semente lido DO BUCKET. READ-ONLY.
#
# v2 (2026-07-28): NÃO usa mais o SDK `google.cloud.storage`. Fala com o GCS
# pela CLI do gcloud, então roda em qualquer máquina com gcloud + python3 —
# inclusive no Mac, com o python do sistema, sem instalar nada (D80).
#
# Isso importa: a v1 só rodava na v5, e a v5 está desligada. Com esta versão o
# inventário autoritativo da campanha continua regenerável depois que as VMs
# forem deletadas.
#
# USO
#   python3 censo_bucket.py
#   SEMENTE=42 GCS_ACCOUNT=... GCS_PROJECT=... REPO_DIR=... python3 censo_bucket.py
#
# VARIÁVEIS
#   REPO_DIR      raiz do repo (precisa do runs_matrix.csv). Autodetecta.
#   SEMENTE       default 42
#   GCS_BUCKET    default mestrado_experiments
#   GCS_PROJECT   default skilled-text-480300-d9
#   GCS_ACCOUNT   conta do gcloud. IMPORTANTE no Mac, onde a conta ativa pode
#                 ser outra e o bucket responde 403.
#   CENSO_CACHE   diretório de trabalho (default: temporário, apagado no fim)
#
# O QUE ELE FAZ COM O BUCKET
#   1. `gcloud storage ls -r` — lista os objetos.  (leitura)
#   2. `gcloud storage cp`    — baixa SÓ os .manifest.json para um dir local.
#                               (leitura; escreve apenas em disco local)
#   NADA MAIS. Não escreve no bucket, não apaga, não move, não toca no repo.
#
# SAÍDA
#   tabela no stdout + ~/censo_bucket_{SEMENTE}.csv (uma linha por célula)
# =============================================================================
import csv, json, os, sys, shutil, subprocess, tempfile, collections

BUCKET  = os.environ.get("GCS_BUCKET", "mestrado_experiments")
PROJECT = os.environ.get("GCS_PROJECT", "skilled-text-480300-d9")
ACCOUNT = os.environ.get("GCS_ACCOUNT", "")
SEM     = os.environ.get("SEMENTE", "42")
PREFIXO = "experiments/"

# ── repo (só para ler o runs_matrix.csv e o characteristics.csv) ─────────────
REPO = ""
for c in (os.environ.get("REPO_DIR", ""), os.getcwd(),
          os.path.expanduser("~/ua-dd-saea"),
          os.path.expanduser("~/Documents/python_repos/mestrado/ua-dd-saea"),
          "/home/jupyter/ua-dd-saea"):
    if c and os.path.isdir(os.path.join(c, ".git")):
        REPO = os.path.abspath(c); break
if not REPO:
    sys.exit("FATAL: repo nao encontrado. Passe REPO_DIR=/caminho/do/ua-dd-saea")

if not shutil.which("gcloud"):
    sys.exit("FATAL: gcloud nao esta no PATH. Instale o Google Cloud SDK ou ajuste o PATH.")

def gflags():
    f = ["--project", PROJECT]
    if ACCOUNT: f += ["--account", ACCOUNT]
    return f

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

CAMADAS = [("1", "__real.parquet"), ("2", "__pop.parquet"), ("3", "__surrogate.parquet"),
           ("4", "__timing.parquet"), ("5", ".manifest.json"), ("6", ".jsonl"),
           ("7", "__final.parquet")]
ABORTO = {"teto_wall", "cache_cap"}

# ── ROSTER → máquina. ATENÇÃO: isto é o DONO PLANEJADO, não onde rodou de fato.
# Células do stack MATLAB foram recuperadas no Mac quando a vm3 falhou (O-19):
# main/e7 inteiro, parte de main/c238 e de main/b1. Para atribuição REAL, use os
# done.txt em gs://mestrado_experiments/_logs_lotes/mac/.
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
DONO = {}
for m, ps in ROSTERS.items():
    for p in ps.split():
        DONO[tuple(p.split("/", 1))] = m

A = os.path.join(REPO, "claude_code_context", "artifacts")
with open(os.path.join(A, "runs_matrix.csv"), encoding="utf-8") as fh:
    TODAS = [r for r in csv.DictReader(fh) if r["semente"] == SEM]
if not TODAS:
    sys.exit("FATAL: semente %s nao existe no runs_matrix.csv (sancionadas: 0..28 e 42)" % SEM)
try:
    with open(os.path.join(A, "characteristics.csv"), encoding="utf-8") as fh:
        DIM = {r["problema"]: int(r["D"]) for r in csv.DictReader(fh)}
except Exception:
    DIM = {}

# ── 1. listar o bucket (leitura) ────────────────────────────────────────────
alvo = "gs://%s/%s**" % (BUCKET, PREFIXO)
print("listando %s ..." % alvo, flush=True)
p = run(["gcloud", "storage", "ls", "-r", alvo] + gflags())
if p.returncode != 0:
    err = (p.stderr or "").strip().splitlines()
    print("FATAL: `gcloud storage ls` falhou (rc=%d)." % p.returncode)
    for l in err[:6]: print("   " + l)
    if any("403" in l for l in err):
        print("\n   403 costuma ser CONTA ERRADA, nao falta de permissao.")
        print("   O bucket vive no projeto %s. Rode com GCS_ACCOUNT=<conta dona>." % PROJECT)
        print("   Veja as contas autenticadas com: gcloud auth list")
    sys.exit(2)

pref = "gs://%s/" % BUCKET
OBJ = set()
for linha in p.stdout.splitlines():
    linha = linha.strip()
    if not linha.startswith(pref) or linha.endswith("/") or linha.endswith(":"):
        continue
    OBJ.add(linha[len(pref):])
print("   %d objetos" % len(OBJ), flush=True)
if not OBJ:
    sys.exit("FATAL: nenhum objeto sob %s — confira BUCKET/PREFIXO." % alvo)

# ── 2. baixar SÓ os manifestos, numa chamada (leitura) ──────────────────────
cache = os.environ.get("CENSO_CACHE", "")
efemero = not cache
if efemero:
    cache = tempfile.mkdtemp(prefix="censo_%s_" % SEM)
os.makedirs(cache, exist_ok=True)

# os nomes de manifesto sao unicos no bucket (incluem exp e alg), entao a
# descida achatada nao colide. `**` nao pega os __final.manifest.json, que
# terminam em "_42__final.manifest.json" e nao em "_42.manifest.json".
padrao = "gs://%s/%s**/*_%s.manifest.json" % (BUCKET, PREFIXO, SEM)
esperados = sorted(o for o in OBJ if o.endswith("_%s.manifest.json" % SEM))
faltando = [o for o in esperados
            if not os.path.exists(os.path.join(cache, os.path.basename(o)))]
if faltando:
    print("baixando %d manifestos (1 chamada, paralela) ..." % len(faltando), flush=True)
    p = run(["gcloud", "storage", "cp", padrao, cache + "/"] + gflags())
    if p.returncode != 0:
        print("AVISO: o cp em lote falhou (rc=%d); caindo para 1-a-1." % p.returncode)
        for o in faltando:
            run(["gcloud", "storage", "cp", "gs://%s/%s" % (BUCKET, o),
                 os.path.join(cache, os.path.basename(o))] + gflags())

def le_manifesto(exp, alg, prob):
    nome = "exp_%s_%s_%s_%s.manifest.json" % (exp, alg, prob, SEM)
    caminho = os.path.join(cache, nome)
    if not os.path.exists(caminho):
        return {"__erro__": "manifesto listado no bucket mas nao baixado"}
    try:
        with open(caminho, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        return {"__erro__": "%s: %s" % (type(e).__name__, e)}

# ── 3. classificar ──────────────────────────────────────────────────────────
reg = []
for r in TODAS:
    exp, alg, prob = r["exp"], r["alg"], r["problema"]
    base = "%s%s/%s/exp_%s_%s_%s_%s" % (PREFIXO, exp, alg, exp, alg, prob, SEM)
    assin = "".join(tag for tag, suf in CAMADAS if base + suf in OBJ)
    d = {"exp": exp, "alg": alg, "prob": prob, "D": DIM.get(prob, ""),
         "maq": DONO.get((exp, alg), "?"), "assin": assin,
         "est": "", "fe": "", "det": ""}

    if exp == "batch" and alg == "c154":
        d["est"], d["det"] = "RETIRADO", "DI-40"
    elif "5" not in assin:
        d["est"] = "S/BUCKET" if not assin else "SEM-MANIFESTO"
    else:
        m = le_manifesto(exp, alg, prob)
        if "__erro__" in m:
            d["est"], d["det"] = "ILEGIVEL", m["__erro__"]
        else:
            st = m.get("status")
            mot = str(m.get("motivo_parada") or "")
            d["fe"] = "%s/%s" % (m.get("fe_final"), m.get("maxfe"))
            if st in ("ok", "retried_ok"):
                d["est"] = "OK"
            elif mot in ABORTO:
                d["est"], d["det"] = "ABORTADO", mot
            else:
                tr = (m.get("stack_trace") or "").strip().splitlines()
                d["est"] = "FALHOU"
                d["det"] = tr[-1][:110] if tr else (mot or str(st) or "?")
    reg.append(d)

# gabarito de camadas = assinatura MODAL entre os OK de cada (exp, alg)
modal = collections.defaultdict(collections.Counter)
for d in reg:
    if d["est"] == "OK":
        modal[(d["exp"], d["alg"])][d["assin"]] += 1
GAB = {k: max(v.items(), key=lambda kv: (kv[1], kv[0]))[0] for k, v in modal.items()}
for d in reg:
    if d["est"] == "OK":
        g = GAB.get((d["exp"], d["alg"]), d["assin"])
        falta = [t for t in g if t not in d["assin"]]
        if falta:
            d["est"] = "OK-INCOMPLETO"
            d["det"] = "faltam camadas %s (gabarito %s)" % ("".join(falta), g)

# ── 4. relatório ────────────────────────────────────────────────────────────
ORD = ["OK", "INCOMPL", "ABORT", "FALHOU", "S/MANIF", "ILEGIV", "RETIR", "S/BUCKET"]
ROT = {"OK": "OK", "OK-INCOMPLETO": "INCOMPL", "ABORTADO": "ABORT", "FALHOU": "FALHOU",
       "SEM-MANIFESTO": "S/MANIF", "ILEGIVEL": "ILEGIV", "RETIRADO": "RETIR",
       "S/BUCKET": "S/BUCKET"}
FAM = lambda e: e if e in ("main", "off", "batch") else "sweep"

cnt = collections.Counter()
fam = collections.defaultdict(collections.Counter)
maq = collections.defaultdict(collections.Counter)
alv = collections.defaultdict(collections.Counter)
for d in reg:
    k = ROT[d["est"]]
    cnt[k] += 1; fam[FAM(d["exp"])][k] += 1
    maq[d["maq"]][k] += 1; alv["%s/%s" % (d["exp"], d["alg"])][k] += 1

W = "%-30s" + " %8s" * len(ORD)
print("=" * 104)
print(" CENSO DO BUCKET · gs://%s/%s · semente=%s" % (BUCKET, PREFIXO, SEM))
print(" celulas da grade: %d · objetos no bucket: %d" % (len(reg), len(OBJ)))
print("=" * 104)
print(W % tuple(["por maquina do ROSTER"] + ORD))
for m in ("mac", "vm3", "v5", "v6", "?"):
    if maq.get(m): print(W % tuple([m] + [maq[m][k] or "." for k in ORD]))
print()
print(W % tuple(["por familia"] + ORD))
for f in ("main", "off", "sweep", "batch"):
    if fam.get(f): print(W % tuple([f] + [fam[f][k] or "." for k in ORD]))
print(W % tuple(["TOTAL"] + [cnt[k] or "." for k in ORD]))
print()
print(W % tuple(["por config"] + ORD))
for k in sorted(alv):
    print(W % tuple([k] + [alv[k][x] or "." for x in ORD]))

for rot in ("FALHOU", "OK-INCOMPLETO", "SEM-MANIFESTO", "ILEGIVEL", "S/BUCKET"):
    ls = [d for d in reg if d["est"] == rot]
    if ls:
        print("\n %s (%d):" % (rot, len(ls)))
        for d in ls:
            print("   %-24s %-12s [%s] camadas=%-7s fe=%-11s %s"
                  % ("%s/%s" % (d["exp"], d["alg"]), d["prob"], d["maq"],
                     d["assin"] or "-", d["fe"], d["det"]))

out = os.path.join(os.path.expanduser("~"), "censo_bucket_%s.csv" % SEM)
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["maquina_roster", "exp", "alg", "problema", "D", "semente",
                "estado", "camadas", "fe_final_maxfe", "detalhe"])
    for d in reg:
        w.writerow([d["maq"], d["exp"], d["alg"], d["prob"], d["D"], SEM,
                    d["est"], d["assin"], d["fe"], d["det"]])
print("\n uma linha por celula em: %s" % out)
print(" ATENCAO: a coluna maquina_roster e o dono PLANEJADO, nao onde rodou de fato.")
print(" Atribuicao real: gs://%s/_logs_lotes/mac/*done.txt" % BUCKET)

if efemero:
    shutil.rmtree(cache, ignore_errors=True)
else:
    print(" manifestos em cache: %s" % cache)
