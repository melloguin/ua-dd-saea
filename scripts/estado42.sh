#!/usr/bin/env bash
# =============================================================================
# estado42.sh — inventário READ-ONLY do que existe em data/experiments NESTA
# máquina, conferido contra o runs_matrix.csv (semente 42).
#
#   bash estado42.sh            # resumo + listas
#   ESTADO_DETALHE=1 bash ...   # + uma linha por célula não-ok
#
# Não escreve nada, não roda experimento, não toca no git. Pode rodar com
# lote em voo.
#
# Classifica cada célula da grade em:
#   ok        · status ok/retried_ok
#   abortou   · failed com motivo_parada=teto_wall (aborto SANCIONADO, DI-38a/40)
#   FALHOU    · failed por outro motivo — é o que precisa de decisão
#   ausente   · sem manifesto (nunca rodou aqui, ou morreu antes de gravar)
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

cd "$REPO" || exit 2
"$PY" - "$REPO" "${ESTADO_DETALHE:-0}" <<'PYEOF'
import csv, json, os, sys, socket, collections
repo, detalhe = sys.argv[1], sys.argv[2] == "1"
A = os.path.join(repo, "claude_code_context", "artifacts")
todas = [r for r in csv.DictReader(open(os.path.join(A, "runs_matrix.csv"), encoding="utf-8"))
         if r["semente"] == "42"]
# DI-40: c154 SAI do roster do batch (5 células) — não são despachadas na rodada-42.
linhas = [r for r in todas if not (r["exp"] == "batch" and r["alg"] == "c154")]
_di40 = len(todas) - len(linhas)

def estado(exp, alg, prob):
    p = os.path.join(repo, "data", "experiments", exp, alg,
                     "exp_%s_%s_%s_42.manifest.json" % (exp, alg, prob))
    if not os.path.exists(p):
        return "ausente", ""
    try:
        m = json.load(open(p, encoding="utf-8"))
    except Exception:
        return "ilegivel", ""
    st = m.get("status")
    if st in ("ok", "retried_ok"):
        return "ok", ""
    mot = str(m.get("motivo_parada") or "")
    if st == "failed" and mot == "teto_wall":
        return "abortou", mot
    tr = (m.get("stack_trace") or "").strip().splitlines()
    return "FALHOU", (tr[-1][:100] if tr else mot or "?")

por_cfg = collections.OrderedDict()
naook = []
for r in linhas:
    k = (r["exp"], r["alg"], r["stack"])
    e, det = estado(r["exp"], r["alg"], r["problema"])
    d = por_cfg.setdefault(k, collections.Counter())
    d[e] += 1
    if e != "ok":
        naook.append((r["exp"], r["alg"], r["problema"], e, det))

print("═══ ESTADO DA RODADA-42 · %s · %s/data/experiments" % (socket.gethostname(), repo))
tot = collections.Counter()
for k, d in por_cfg.items(): tot.update(d)
print("    grade semente 42 = %d células (%d de c154-batch fora, DI-40)"
      % (len(linhas), _di40))
print("    nesta máquina: ok=%d · abortou(sancionado)=%d · FALHOU=%d · ausente=%d"
      % (tot["ok"], tot["abortou"], tot["FALHOU"], tot["ausente"]))
print()
print("── configs com QUALQUER coisa gravada nesta máquina")
print("   %-19s %-12s %-7s %5s %4s %8s %7s %8s" %
      ("exp", "alg", "stack", "total", "ok", "abortou", "FALHOU", "ausente"))
for (exp, alg, stack), d in por_cfg.items():
    n = sum(d.values())
    if d["ausente"] == n:      # nada gravado aqui — sai na outra lista
        continue
    print("   %-19s %-12s %-7s %5d %4d %8d %7d %8d" %
          (exp, alg, stack, n, d["ok"], d["abortou"], d["FALHOU"], d["ausente"]))

falhas = [x for x in naook if x[3] == "FALHOU"]
if falhas:
    print()
    print("── FALHAS NÃO SANCIONADAS (%d) — precisam de decisão" % len(falhas))
    for exp, alg, prob, _, det in falhas:
        print("   %-19s %-12s %-11s  %s" % (exp, alg, prob, det))

vazios = [k for k, d in por_cfg.items() if d["ausente"] == sum(d.values())]
if vazios:
    print()
    print("── configs SEM NADA gravado aqui (%d) — candidatos a redistribuição" % len(vazios))
    for exp, alg, stack in vazios:
        print("   %-19s %-12s %s" % (exp, alg, stack))
    print()
    print("   LOTE_PARES para disparar todos eles numa máquina:")
    print("   LOTE_PARES=\"" + " ".join("%s/%s" % (e, a) for e, a, _ in vazios) + "\"")

parciais = [(k, d) for k, d in por_cfg.items()
            if 0 < d["ausente"] < sum(d.values())]
if parciais:
    print()
    print("── configs PARCIAIS (começaram e faltam células) — %d" % len(parciais))
    for (exp, alg, _), d in parciais:
        print("   %-19s %-12s faltam %d de %d" % (exp, alg, d["ausente"], sum(d.values())))

if detalhe and naook:
    print()
    print("── detalhe: todas as células não-ok (%d)" % len(naook))
    for exp, alg, prob, e, det in naook:
        print("   %-19s %-12s %-11s %-8s %s" % (exp, alg, prob, e, det))
PYEOF
