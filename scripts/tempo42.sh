#!/usr/bin/env bash
# =============================================================================
# tempo42.sh — projeção do que FALTA nesta máquina, calibrada com os walls que
# ELA MESMA já mediu. READ-ONLY; pode rodar com lote em voo.
#
#   TEMPO_JOBS=6 bash tempo42.sh
#   TEMPO_PARES="main/e7 main/c238" TEMPO_JOBS=8 bash tempo42.sh
#
# Sem TEMPO_PARES, o roster é inferido: todo config que tem ao menos um
# manifesto gravado aqui. Sem TEMPO_JOBS, assume 75% dos núcleos físicos.
#
# O modelo NÃO é o do lote42.sh (aquele veio do Mac). Aqui cada algoritmo é
# interpolado em log-log sobre os pontos MEDIDOS NESTA MÁQUINA, indexados por
# maxFE = 31D-1. Algoritmo sem medição local sai marcado como desconhecido.
# =============================================================================
set -uo pipefail

REPO=""
for c in "$HOME/ua-dd-saea" "$HOME/Documents/python_repos/mestrado/ua-dd-saea" \
         "/home/jupyter/ua-dd-saea"; do
  [ -d "$c/.git" ] && REPO="$c" && break
done
[ -n "$REPO" ] || { echo "FATAL: repo nao encontrado"; exit 2; }
PY=""
for c in "$HOME/venvs/env_main/bin/python" "$HOME/python_venvs/env_main/bin/python" \
         "$HOME/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python" \
         "/home/jupyter/python_venvs/env_main/bin/python" "$(command -v python3)"; do
  [ -n "$c" ] && [ -x "$c" ] && PY="$c" && break
done
[ -n "$PY" ] || { echo "FATAL: python nao encontrado"; exit 2; }

if [ "$(uname)" = "Darwin" ]; then FIS=$(sysctl -n hw.physicalcpu)
else FIS=$(lscpu -p=Core,Socket 2>/dev/null | grep -v '^#' | sort -u | wc -l | tr -d ' '); fi
JOBS="${TEMPO_JOBS:-$(( FIS * 3 / 4 ))}"

cd "$REPO" || exit 2
"$PY" - "$REPO" "$JOBS" "${TEMPO_PARES:-}" <<'PYEOF'
import csv, json, glob, math, os, sys, socket, collections
repo, jobs, pares = sys.argv[1], int(sys.argv[2]), sys.argv[3].split()
A = os.path.join(repo, "claude_code_context", "artifacts")
D = {r["problema"]: int(r["D"]) for r in
     csv.DictReader(open(os.path.join(A, "characteristics.csv"), encoding="utf-8"))}
fe_de = lambda p: 31 * D[p] - 1

grade = [r for r in csv.DictReader(open(os.path.join(A, "runs_matrix.csv"), encoding="utf-8"))
         if r["semente"] == "42" and not (r["exp"] == "batch" and r["alg"] == "c154")]

# ── 1. walls MEDIDOS nesta máquina, por (alg, maxFE) ────────────────────────
med = collections.defaultdict(dict)      # alg -> {maxFE: wall}
brutos = collections.defaultdict(list)
tem_man = set()                          # (exp, alg) com algo gravado aqui
for p in glob.glob(os.path.join(repo, "data/experiments/*/*/*_42.manifest.json")):
    try: m = json.load(open(p, encoding="utf-8"))
    except Exception: continue
    exp = p.split(os.sep)[-3]; alg = p.split(os.sep)[-2]
    tem_man.add((exp, alg))
    w = (m.get("timing") or {}).get("tempo_total_s")
    prob = m.get("problema")
    if w and prob in D and m.get("status") in ("ok", "retried_ok") and exp == "main":
        med[alg][fe_de(prob)] = float(w)
        brutos[alg].append(float(w))

def prever(alg, fe):
    a = med.get(alg)
    if not a: return None
    k = sorted(a)
    if len(k) == 1: return a[k[0]] * (fe / k[0]) ** 1.3
    if   fe <= k[0]:  lo, hi = k[0], k[1]
    elif fe >= k[-1]: lo, hi = k[-2], k[-1]
    else:
        i = max(j for j in range(len(k)-1) if k[j] <= fe); lo, hi = k[i], k[i+1]
    if a[hi] <= 0 or a[lo] <= 0 or hi == lo: return a[lo]
    b = (math.log(a[hi]) - math.log(a[lo])) / (math.log(hi) - math.log(lo))
    return a[lo] * (fe / lo) ** b

# ── 2. o que falta ──────────────────────────────────────────────────────────
alvo = {tuple(x.split("/", 1)) for x in pares} if pares else tem_man
falta = collections.defaultdict(list)
for r in grade:
    k = (r["exp"], r["alg"])
    if k not in alvo: continue
    mp = os.path.join(repo, "data/experiments", r["exp"], r["alg"],
                      "exp_%s_%s_%s_42.manifest.json" % (r["exp"], r["alg"], r["problema"]))
    if os.path.exists(mp): continue
    falta[k].append(r["problema"])

print("═══ PROJEÇÃO DO QUE FALTA · %s · %d processos" % (socket.gethostname(), jobs))
if not falta:
    print("    nada pendente no roster considerado."); sys.exit(0)
print()
print("   %-19s %-12s %5s %10s %12s %s" % ("exp", "alg", "cél", "med/cél", "soma", "base"))
tot, desconhecido, maior = 0.0, [], 0.0
for (exp, alg), probs in sorted(falta.items(), key=lambda x: -len(x[1])):
    ws = [prever(alg, fe_de(p)) for p in probs]
    if any(w is None for w in ws):
        desconhecido.append((exp, alg, len(probs)))
        print("   %-19s %-12s %5d %10s %12s %s" % (exp, alg, len(probs), "?", "?", "sem medição local"))
        continue
    s = sum(ws); tot += s; maior = max(maior, max(ws))
    base = "%d pontos medidos" % len(med[alg])
    print("   %-19s %-12s %5d %9.1fm %11.2fh %s" % (exp, alg, len(probs), s/len(ws)/60, s/3600, base))

n = sum(len(v) for v in falta.values())
piso = max(tot/3600/jobs, maior/3600)
print()
print("   %d células pendentes · %.1f h-core projetadas" % (n, tot/3600))
print("   makespan ≈ %.1f h   (h-core/%d = %.1f h · maior célula sozinha = %.1f h)"
      % (piso, jobs, tot/3600/jobs, maior/3600))
if desconhecido:
    print("   ⚠ fora da conta (sem medição local): " +
          ", ".join("%s/%s (%d)" % x for x in desconhecido))
print()
print("   medições locais usadas:")
for alg in sorted(med):
    k = sorted(med[alg])
    print("     %-12s %s" % (alg, "  ".join("FE%d=%.0fs" % (f, med[alg][f]) for f in k)))
PYEOF
