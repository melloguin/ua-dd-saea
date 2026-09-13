#!/usr/bin/env bash
# =============================================================================
# preflight42.sh — checagem READ-ONLY antes de disparar o lote numa máquina.
# Não instala nada, não escreve no repo, não faz git pull. Só olha e reporta.
#
#   PRE_MAQ=v5|v6|vm3|mac bash preflight42.sh
#
# Verifica, nesta ordem:
#   1. repo + commit + árvore limpa
#   2. env_main encontrado e importável
#   3. MATLAB encontrado (só se o perfil tiver células MATLAB)
#   4. TODOS os venvs que o roster da máquina exige, resolvidos pelo envs.json
#      — é aqui que a alocação quebra se um env não existir (D79/N.1.2)
#   5. núcleos FÍSICOS e RAM, contra o número de processos do perfil
#   6. bucket (cliente Python, que é o caminho que o mirror_run usa)
#   7. o portão do próprio repo (scripts/preflight.py)
# =============================================================================
set -uo pipefail
MAQ="${PRE_MAQ:-}"
[ -n "$MAQ" ] || { echo "FATAL: defina PRE_MAQ=v5|v6|vm3|mac"; exit 2; }

case "$MAQ" in
  v5)  JOBS=12; ALGS="c154";;
  v6)  JOBS=6;  ALGS="c262 c149 sobol_batch";;
  vm3) JOBS=6;  ALGS="c122 c149 nsga2 nsga3 moead smsemoa c141 c217 b3 e74 b4 b1 e7 c238 e103";;
  mac) JOBS=4;  ALGS="e81 b5r b5m moead_media c311 treed_media";;
  *)   echo "FATAL: PRE_MAQ desconhecido"; exit 2;;
esac

RED=$'\033[31m'; GRN=$'\033[32m'; YEL=$'\033[33m'; OFF=$'\033[0m'
ok(){ echo "  ${GRN}✓${OFF} $*"; }
no(){ echo "  ${RED}✗${OFF} $*"; FALHAS=$((FALHAS+1)); }
wr(){ echo "  ${YEL}!${OFF} $*"; }
FALHAS=0

echo "═══ PRÉ-VOO · $MAQ ═══"

# 1 ── repo
REPO=""
for c in "$HOME/ua-dd-saea" "$HOME/Documents/python_repos/mestrado/ua-dd-saea" \
         "/home/jupyter/ua-dd-saea"; do
  [ -d "$c/.git" ] && REPO="$c" && break
done
[ -n "$REPO" ] && ok "repo: $REPO" || { no "repo NÃO encontrado"; exit 2; }
cd "$REPO" || exit 2
echo "     commit: $(git rev-parse --short HEAD)  ($(git log -1 --format=%cd --date=short))"
SUJO="$(git status --porcelain)"
if   [ -z "$SUJO" ]; then ok "árvore limpa"
elif [ -z "$(printf '%s\n' "$SUJO" | grep -v '^??')" ]; then
     ok "código limpo (só arquivos não rastreados, que não afetam a rodada):"
     printf '%s\n' "$SUJO" | head -5 | sed 's/^/       /'
else wr "árvore SUJA — há mudança em arquivo RASTREADO:"; printf '%s\n' "$SUJO" | head -5 | sed 's/^/       /'; fi

# 2 ── env_main
PY=""
for c in "$HOME/venvs/env_main/bin/python" "$HOME/python_venvs/env_main/bin/python" \
         "$HOME/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python" \
         "/home/jupyter/python_venvs/env_main/bin/python"; do
  [ -x "$c" ] && PY="$c" && break
done
if [ -n "$PY" ]; then
  ok "env_main: $PY  ($("$PY" -c 'import sys;print("py"+".".join(map(str,sys.version_info[:3])))' 2>/dev/null))"
  "$PY" -c "import numpy,pandas,pyarrow,pymoo" 2>/dev/null \
    && ok "env_main importa numpy/pandas/pyarrow/pymoo" || no "env_main NÃO importa o núcleo"
else
  no "env_main NÃO encontrado"
fi

# 3 ── MATLAB
PRECISA_MAT=0; case "$MAQ" in vm3) PRECISA_MAT=1;; esac
MAT=""
for c in "/Applications/MATLAB_R2025a.app/bin/matlab" "/usr/local/MATLAB/R2025a/bin/matlab" \
         "$(command -v matlab 2>/dev/null)"; do
  [ -n "$c" ] && [ -x "$c" ] && MAT="$c" && break
done
if [ "$PRECISA_MAT" = 1 ]; then
  [ -n "$MAT" ] && ok "matlab: $MAT" || no "MATLAB NÃO encontrado (o perfil tem células MATLAB)"
else
  [ -n "$MAT" ] && echo "     matlab: $MAT (não é exigido neste perfil)" || true
fi

# 4 ── venvs exigidos pelo roster (a checagem que decide se a alocação vale)
echo "  ── venvs exigidos pelo roster de $MAQ:"
[ -n "$PY" ] && "$PY" - "$REPO" "$ALGS" "$PY" <<'PYEOF'
import json, os, sys
repo, algs, py_main = sys.argv[1], sys.argv[2].split(), sys.argv[3]
E = json.load(open(os.path.join(repo, "claude_code_context", "artifacts", "envs.json"), encoding="utf-8"))
a2e, envs = E["alg_to_env"], E["provisioning"]["envs"]
falta = 0
for env in sorted({a2e[a]["env"] for a in algs if a in a2e}):
    if env == "env_matlab":
        print(f"       env_matlab      → (MATLAB, sem venv)"); continue
    if env == "env_main":
        itp = py_main                      # já resolvido pela busca do shell
    else:
        v = (envs.get(env) or {}).get("venv", "")
        itp = os.path.join(v, "bin", "python") if v else ""
    marca = "\033[32m✓\033[0m" if itp and os.access(itp, os.X_OK) else "\033[31m✗\033[0m"
    if not (itp and os.access(itp, os.X_OK)): falta += 1
    print(f"       {marca} {env:15} → {itp or '<sem caminho no envs.json>'}")
if falta:
    print(f"       \033[31mFALTAM {falta} venv(s).\033[0m Sem eles, os configs correspondentes")
    print( "       falham em run_in_venv (D79/N.1.2). PARE e reavalie a alocação (D81).")
sys.exit(3 if falta else 0)
PYEOF
[ $? -eq 0 ] || FALHAS=$((FALHAS+1))

# 5 ── núcleos FÍSICOS e RAM
if [ "$(uname)" = "Darwin" ]; then
  FIS=$(sysctl -n hw.physicalcpu); RAM=$(( $(sysctl -n hw.memsize) / 1073741824 ))
else
  FIS=$(lscpu -p=Core,Socket 2>/dev/null | grep -v '^#' | sort -u | wc -l | tr -d ' ')
  RAM=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}')
fi
LIM=$(( FIS * 3 / 4 ))
echo "     núcleos físicos: $FIS   ·   75% = $LIM   ·   perfil pede $JOBS   ·   RAM ${RAM} GiB"
[ "$JOBS" -le "$LIM" ] && ok "processos dentro do teto de 75%" || wr "perfil acima de 75% dos físicos — reduza LOTE_JOBS"
RAMPP=$(awk "BEGIN{printf \"%.1f\", $RAM/$JOBS}")
echo "     RAM por processo: ${RAMPP} GiB"
awk "BEGIN{exit !($RAMPP < 3.0)}" && wr "menos de 3 GiB por processo — células grandes (e7 ~3,3 GiB, batch n=2109) podem estourar" || ok "folga de RAM por processo"

# 6 ── bucket (caminho Python — é o que o mirror_run usa)
if [ -n "$PY" ]; then
  "$PY" - <<'PYEOF' 2>/dev/null && ok "bucket gravável pelo cliente Python" || wr "bucket indisponível — rode com LOTE_BUCKET=0 (não é bloqueio)"
import sys
try:
    from google.cloud import storage
    from src.gcs import BUCKET, PROJECT
    b = storage.Client(project=PROJECT).bucket(BUCKET)
    bl = b.blob("_preflight/probe.txt"); bl.upload_from_string("ok"); bl.delete()
except Exception:
    sys.exit(1)
PYEOF
fi

# 7 ── portão do próprio repo
if [ -n "$PY" ] && [ -f scripts/preflight.py ]; then
  LOG="$HOME/preflight42_${MAQ}.log"; : > "$LOG" 2>/dev/null || LOG="$(mktemp)"
  if "$PY" scripts/preflight.py > "$LOG" 2>&1; then ok "scripts/preflight.py exit 0"
  else no "scripts/preflight.py FALHOU — veja $LOG"; tail -8 "$LOG" | sed 's/^/       /'; fi
fi

echo
if [ "$FALHAS" -eq 0 ]; then
  echo "${GRN}═══ VERDE — pode disparar o lote em $MAQ ═══${OFF}"
else
  echo "${RED}═══ $FALHAS BLOQUEIO(S) — NÃO dispare. Escale (D81). ═══${OFF}"; exit 1
fi
