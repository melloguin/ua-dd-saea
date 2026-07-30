#!/usr/bin/env bash
# =============================================================================
# lote42.sh — disparador ÚNICO da rodada-42 (Python + MATLAB) com contador vivo.
#
# Por quê: `experiments.py --n-jobs N` usa joblib com verbose=0 (só imprime o
# placar no fim) e `experiments.m` usa parfor (que engole o stderr e quebra a
# ponte InProcess — DI-34). Este driver inverte os dois: N processos de UMA
# célula cada, controlados por xargs, com barra de progresso a cada 15 s.
#
# NÃO TOCA NO REPO. A grade vem SEMPRE do runs_matrix.csv, nunca digitada.
#
# Três coisas que só existem aqui e que o despachante nativo não faz:
#   1. pino de thread REAL, 1 core por run (D79/O-15) — o caminho joblib divide
#      os núcleos por n_jobs e estoura o pino;
#   2. ordem HÍBRIDA — tudo que dura < 15 min primeiro (barato→caro), o resto
#      depois (caro→barato). Move o contador rápido sem alongar o makespan;
#   3. contador N/M com barra, %, decorrido e ETA ponderada por custo.
#
# USO
#   LOTE_MAQ=v5|v6|vm3|mac   bash lote42.sh          # DRY-RUN: só lista
#   LOTE=CONFIRMA LOTE_MAQ=v5 bash lote42.sh         # dispara
#
# Variáveis
#   LOTE=CONFIRMA     dispara de verdade (sem isso, só lista)
#   LOTE_MAQ          perfil da máquina (obrigatório, salvo se LOTE_PARES)
#   LOTE_JOBS         processos simultâneos (default: o do perfil)
#   LOTE_PARES        "exp/alg exp/alg ..." — sobrepõe o perfil
#   LOTE_SEED=42      semente
#   LOTE_DATA_ROOT=data
#   LOTE_BUCKET       --enable-bucket nas células Python. Default do PERFIL:
#                     1 nas VMs, 0 no mac (os venvs próprios não têm o SDK — D80)
#   LOTE_ORDEM=hibrida|barata|cara
# =============================================================================
set -uo pipefail

SEED="${LOTE_SEED:-42}"
DATA_ROOT="${LOTE_DATA_ROOT:-data}"
# USE_BUCKET é resolvido DEPOIS do perfil (o mac nasce com 0 — ver abaixo)
ORDEM="${LOTE_ORDEM:-hibrida}"
MAQ="${LOTE_MAQ:-}"

# ── perfis (alocação da rodada-42; 75% dos núcleos FÍSICOS) ─────────────────
case "$MAQ" in
  v5)  BUCKET_DEF=1; JOBS_DEF=12; PARES="main/c154" ;;
  v6)  BUCKET_DEF=1; JOBS_DEF=6;  PARES="batch/sobol_batch batch/c149 main/c262 batch/c262" ;;
  vm3) BUCKET_DEF=1; JOBS_DEF=6;  PARES="main/nsga2 main/nsga3 main/moead main/smsemoa
                           main/c141 main/c217 main/b3 main/e74 main/b4 main/b1
                           main/e7 main/c238 off/e103
                           sweep-small-lhs/e103 sweep-small-mvns/e103
                           sweep-medium-lhs/e103 sweep-medium-mvns/e103
                           main/c122 main/c149" ;;
  mac) BUCKET_DEF=0; JOBS_DEF=4;  PARES="off/c311 off/moead_media off/b5r off/b5m
                           main/e81 batch/e81
                           sweep-small-lhs/c311 sweep-small-mvns/c311
                           sweep-medium-lhs/c311 sweep-medium-mvns/c311
                           sweep-big-lhs/c311 sweep-big-mvns/c311
                           sweep-big-lhs/treed_media sweep-big-mvns/treed_media
                           sweep-small-lhs/moead_media sweep-small-mvns/moead_media
                           sweep-medium-lhs/moead_media sweep-medium-mvns/moead_media
                           sweep-small-lhs/b5r sweep-small-mvns/b5r
                           sweep-medium-lhs/b5r sweep-medium-mvns/b5r
                           sweep-small-lhs/b5m sweep-small-mvns/b5m
                           sweep-medium-lhs/b5m sweep-medium-mvns/b5m" ;;
  *)   BUCKET_DEF=1; JOBS_DEF=4;  PARES="" ;;
esac
PARES="${LOTE_PARES:-$PARES}"
# [2026-07-26] O Mac NASCE com bucket=0. Os configs de venv próprio (e81/b5*/c311/
# treed_media/moead_media) rodam DENTRO dos venvs deles, que não têm
# google-cloud-storage — e por D80 não se instala. Com --enable-bucket, TODA célula
# do Mac morre em gcs._client com RuntimeError. Nas VMs o dual-write é o desenho
# (DI-32: a VM efêmera do M8 perderia tudo sem ele); no Mac o caminho é local.
USE_BUCKET="${LOTE_BUCKET:-$BUCKET_DEF}"
JOBS="${LOTE_JOBS:-$JOBS_DEF}"
[ -n "$PARES" ] || { echo "FATAL: defina LOTE_MAQ (v5|v6|vm3|mac) ou LOTE_PARES"; exit 2; }

# ── detecção de repo / interpretador / MATLAB ───────────────────────────────
REPO=""
for c in "$HOME/ua-dd-saea" "$HOME/Documents/python_repos/mestrado/ua-dd-saea" \
         "/home/jupyter/ua-dd-saea"; do
  [ -d "$c/.git" ] && REPO="$c" && break
done
[ -n "$REPO" ] || { echo "FATAL: repo nao encontrado"; exit 2; }

PY=""
for c in "$HOME/venvs/env_main/bin/python" "$HOME/python_venvs/env_main/bin/python" \
         "$HOME/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python" \
         "/home/jupyter/python_venvs/env_main/bin/python"; do
  [ -x "$c" ] && PY="$c" && break
done

MAT=""
for c in "/Applications/MATLAB_R2025a.app/bin/matlab" "/usr/local/MATLAB/R2025a/bin/matlab" \
         "$(command -v matlab 2>/dev/null)"; do
  [ -n "$c" ] && [ -x "$c" ] && MAT="$c" && break
done

cd "$REPO" || exit 2

# ── pino de thread: 1 core por run (D79 / envs.json thread_pin / O-15) ──────
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
       NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONHASHSEED=0

OUT="/tmp/lote42_${MAQ:-custom}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT/logs"
GRID="$OUT/grid.txt"; DONE="$OUT/done.txt"; : > "$DONE"

# ── grade a partir do ARTEFATO + ordem híbrida ──────────────────────────────
python3 - "$REPO" "$SEED" "$PARES" "$ORDEM" > "$GRID" <<'PYEOF'
import csv, sys, os, math
repo, seed, pares, ordem = sys.argv[1], sys.argv[2], sys.argv[3].split(), sys.argv[4]
alvo = {tuple(p.split("/", 1)) for p in pares}
A = os.path.join(repo, "claude_code_context", "artifacts")
D = {r["problema"]: int(r["D"]) for r in
     csv.DictReader(open(os.path.join(A, "characteristics.csv"), encoding="utf-8"))}

# ── modelo de custo: interpolação log-log entre os walls MEDIDOS (Mac, R1/R2).
#    Chave = maxFE (=31D-1). Fora do intervalo, extrapola pela inclinação da
#    ponta. Serve SÓ para ordenar a fila e estimar ETA — não entra em resultado.
ANC = {"b1":{61:14,371:165,929:2014}, "b3":{61:4,371:40,929:537},
       "b4":{61:41,371:196,929:883},  "c122":{371:709,929:5054},
       "c141":{61:1,371:18,929:169},  "c149":{61:239,371:2632,929:12107},
       "c154":{61:95,371:52596},      "c217":{371:49,929:132},
       "c238":{61:6,371:610,929:14100},   # 929 = âncora do REGISTRO (D-05)
       "c262":{61:34,371:8972,929:15051}, "e103":{61:7,371:10,929:35},
       "e7":{61:317,371:1818,929:4320},   # 929 = âncora do REGISTRO (D-05)
       "e74":{61:21,371:258,929:469}, "e81":{61:10,371:549,929:7167},
       "moead":{61:1,929:1},"nsga2":{61:1,929:1},"nsga3":{61:1,929:1},
       "smsemoa":{61:1,929:1}}
OFF  = {"b5m":2826,"b5r":306,"c311":41,"moead_media":63,"e103":10,"treed_media":9}
TIER = {"small":0.35,"medium":1.10,"big":1.40}
BAT  = {"c149":6972,"e81":2077,"sobol_batch":2,"c262":14400}   # c262 = ESTIMADO
TETO, ABORTO = 43200.0, 22632.0        # teto de wall · trip do projetor (DI-40)

def por_fe(alg, fe):
    a = ANC.get(alg)
    if not a: return 600.0
    p = sorted(a)
    if len(p) == 1: return a[p[0]] * (fe / p[0]) ** 1.5
    if   fe <= p[0]:  lo, hi = p[0], p[1]
    elif fe >= p[-1]: lo, hi = p[-2], p[-1]
    else:
        i = max(j for j in range(len(p) - 1) if p[j] <= fe); lo, hi = p[i], p[i + 1]
    b = (math.log(a[hi]) - math.log(a[lo])) / (math.log(hi) - math.log(lo))
    return a[lo] * (fe / lo) ** b

def custo(exp, alg, prob):
    if exp == "batch":  return BAT.get(alg, 3600.0)
    if exp.startswith("sweep-"):
        tier = exp.split("-")[1]
        return OFF.get(alg, 600.0) * TIER.get(tier, 1.0)
    if exp == "off":    return OFF.get(alg, 600.0)
    fe = 31 * D[prob] - 1
    v = por_fe(alg, fe)
    if alg == "c154" and fe >= 371: v = ABORTO
    return min(v, TETO)

linhas = []
for r in csv.DictReader(open(os.path.join(A, "runs_matrix.csv"), encoding="utf-8")):
    if r["semente"] != seed or (r["exp"], r["alg"]) not in alvo: continue
    linhas.append((custo(r["exp"], r["alg"], r["problema"]),
                   r["exp"], r["alg"], r["problema"], r["stack"]))
LIM = 900.0                              # 15 min
if   ordem == "barata": linhas.sort()
elif ordem == "cara":   linhas.sort(reverse=True)
else:                                    # HÍBRIDA (default)
    linhas = sorted([l for l in linhas if l[0] <  LIM]) + \
             sorted([l for l in linhas if l[0] >= LIM], reverse=True)
for c, e, a, p, st in linhas:
    print(f"{e} {a} {p} {st} {c:.0f}")
PYEOF

TOTAL=$(wc -l < "$GRID" | tr -d ' ')
CUSTO_TOT=$(awk '{s+=$5} END{printf "%.0f", s+0}' "$GRID")
NPY=$(awk '$4=="python"' "$GRID" | wc -l | tr -d ' ')
NML=$(awk '$4=="matlab"' "$GRID" | wc -l | tr -d ' ')

echo "════════════════════════════════════════════════════════════════════════"
echo " LOTE-42 · máquina=${MAQ:-custom} · semente=$SEED · $JOBS processos · ordem=$ORDEM"
echo " repo=$REPO"
echo " python=${PY:-<ausente>}"
echo " matlab=${MAT:-<ausente>}"
echo " células: $TOTAL   (python $NPY · matlab $NML)"
HCORE=$(awk -v c="$CUSTO_TOT" 'BEGIN{printf "%.1f", c/3600}' </dev/null)
MKSP=$(awk -v c="$CUSTO_TOT" -v j="$JOBS" 'BEGIN{printf "%.1f", c/3600/j}' </dev/null)
printf  " custo estimado: %s h-core  ->  makespan previsto ~%s h\n" "$HCORE" "$MKSP"
echo " bucket: $([ "$USE_BUCKET" = 1 ] && echo LIGADO || echo desligado)"
echo " logs: $OUT/logs/"
echo "════════════════════════════════════════════════════════════════════════"
[ "$TOTAL" -gt 0 ] || { echo "grade VAZIA — confira LOTE_MAQ/LOTE_PARES."; exit 1; }
[ "$NPY" -eq 0 ] || [ -n "$PY" ] || { echo "FATAL: há células python e nenhum env_main encontrado."; exit 2; }
[ "$NML" -eq 0 ] || [ -n "$MAT" ] || { echo "FATAL: há células matlab e o MATLAB não foi encontrado."; exit 2; }

if [ "${LOTE:-}" != "CONFIRMA" ]; then
  echo; echo "DRY-RUN. Para disparar:  LOTE=CONFIRMA LOTE_MAQ=$MAQ bash $0"
  echo; echo "as 12 PRIMEIRAS da fila (é por elas que o contador começa a andar):"
  head -12 "$GRID" | awk '{printf "      %-19s %-12s %-11s %-7s ~%6.1f min\n",$1,$2,$3,$4,$5/60}'
  echo "      ..."
  echo "as 5 ÚLTIMAS da fila:"
  tail -5  "$GRID" | awk '{printf "      %-19s %-12s %-11s %-7s ~%6.1f min\n",$1,$2,$3,$4,$5/60}'
  echo
  echo "célula mais cara da grade:"
  sort -k5 -n -r "$GRID" | head -1 | awk '{printf "      %-19s %-12s %-11s ~%.1f h\n",$1,$2,$3,$5/3600}'
  exit 0
fi

# ── worker: UMA célula por processo ─────────────────────────────────────────
BFLAG=""; [ "$USE_BUCKET" = "1" ] && BFLAG="--enable-bucket"
cat > "$OUT/worker.sh" <<WEOF
#!/usr/bin/env bash
EXP="\$1"; ALG="\$2"; PROB="\$3"; STACK="\$4"; CUSTO="\$5"
LOG="$OUT/logs/\${EXP}__\${ALG}__\${PROB}.log"
MAN="$DATA_ROOT/experiments/\${EXP}/\${ALG}/exp_\${EXP}_\${ALG}_\${PROB}_${SEED}.manifest.json"
cd "$REPO" || exit 1
_mtime(){                      # mtime portável: GNU (-c %Y) ou BSD/macOS (-f %m)
  _m=\$(stat -c %Y "\$1" 2>/dev/null) || _m=""
  case "\$_m" in ''|*[!0-9]*) _m=\$(stat -f %m "\$1" 2>/dev/null) || _m="";; esac
  case "\$_m" in ''|*[!0-9]*) _m=0;; esac
  printf '%s' "\$_m"; }
ANTES=0; [ -f "\$MAN" ] && ANTES=\$(_mtime "\$MAN")
if [ "\$STACK" = "matlab" ]; then
  "$MAT" -batch "maxNumCompThreads(1); experiments('algorithms',{'\$ALG'},'problems',{'\$PROB'},'seeds',$SEED,'exp','\$EXP','dataRoot','$DATA_ROOT','parallel',false)" > "\$LOG" 2>&1
else
  "$PY" experiments.py --exp "\$EXP" --algorithms "\$ALG" --problems "\$PROB" \\
        --seeds "$SEED" --n-jobs 1 --data-root "$DATA_ROOT" $BFLAG > "\$LOG" 2>&1
fi
DEPOIS=0; [ -f "\$MAN" ] && DEPOIS=\$(_mtime "\$MAN")
if [ ! -f "\$MAN" ]; then
  ST=sem-manifesto
elif [ "\$ANTES" = "\$DEPOIS" ] && [ "\$ANTES" != "0" ]; then
  ST=pulou
else
  ST=\$(python3 -c "
import json,sys
try: print(json.load(open(sys.argv[1],encoding='utf-8')).get('status','?'))
except Exception: print('ilegivel')" "\$MAN")
fi
printf '%s %s %s %s %s\n' "\$EXP" "\$ALG" "\$PROB" "\$ST" "\$CUSTO" >> "$DONE"
WEOF
chmod +x "$OUT/worker.sh"

# ── disparo + contador ao vivo ──────────────────────────────────────────────
T0=$(date +%s)
FIM="$OUT/FIM"; rm -f "$FIM"
( xargs -P "$JOBS" -n5 "$OUT/worker.sh" < "$GRID"; : > "$FIM" ) &
XPID=$!

barra() {  # $1 = fração 0..1   (awk com -v e </dev/null: nunca lê stdin)
  awk -v f="$1" 'BEGIN{n=int(f*28+0.5); s="";
    for(i=0;i<28;i++) s = s (i<n ? "█" : "░"); printf "%s", s}' </dev/null
}
placar() {
  # ATENÇÃO: nada de aspas duplas aninhadas dentro de $( ) — o bash 3.2 do macOS
  # perde as aspas internas, a chave do awk fica exposta e vira brace expansion
  # (`BEGIN{printf "x", y}` → duas palavras), o awk perde o programa e TRAVA lendo
  # stdin. Todo valor entra por -v, todo programa é aspa SIMPLES, todo awk tem
  # </dev/null. Achado no macOS em 2026-07-26.
  D=$(wc -l < "$DONE" | tr -d ' ')
  OK=$(awk '$4=="ok"||$4=="retried_ok"' "$DONE" | wc -l | tr -d ' ')
  FA=$(awk '$4=="failed"' "$DONE" | wc -l | tr -d ' ')
  SK=$(awk '$4=="pulou"' "$DONE" | wc -l | tr -d ' ')
  CF=$(awk '{s+=$5} END{printf "%.0f", s+0}' "$DONE")
  EL=$(( $(date +%s) - T0 ))
  FR=$(awk -v d="$D" -v t="$TOTAL" 'BEGIN{printf "%.4f", (t>0 ? d/t : 0)}' </dev/null)
  PC=$(awk -v d="$D" -v t="$TOTAL" 'BEGIN{printf "%.1f", (t>0 ? 100*d/t : 0)}' </dev/null)
  BA=$(barra "$FR")
  ET="--"
  if [ "${CF:-0}" -gt 0 ] && [ "$EL" -gt 30 ]; then
    ET=$(awk -v tot="$CUSTO_TOT" -v cf="$CF" -v el="$EL" \
         'BEGIN{r=(tot-cf)/cf*el; printf "%02dh%02dm", r/3600, (r%3600)/60}' </dev/null)
  fi
  printf '\r  [%s] %s/%s (%s%%) - ok=%s falhou=%s pulou=%s - %02dh%02dm - ETA ~%s   ' \
    "$BA" "$D" "$TOTAL" "$PC" "$OK" "$FA" "$SK" $((EL/3600)) $(((EL%3600)/60)) "$ET"
}

while : ; do
  placar
  [ -f "$FIM" ] && break
  sleep 15
done
wait "$XPID" 2>/dev/null; placar

D=$(wc -l < "$DONE" | tr -d ' ')
OK=$(awk '$4=="ok"||$4=="retried_ok"' "$DONE" | wc -l | tr -d ' ')
FA=$(awk '$4=="failed"' "$DONE" | wc -l | tr -d ' ')
SK=$(awk '$4=="pulou"' "$DONE" | wc -l | tr -d ' ')
EL=$(( $(date +%s) - T0 ))
printf '\n\n════ FIM · %d/%d · ok=%d falhou=%d pulou=%d · %02dh%02dm\n' \
       "$D" "$TOTAL" "$OK" "$FA" "$SK" $((EL/3600)) $(((EL%3600)/60))
if [ "$FA" -gt 0 ]; then
  echo "── células com status failed (log em $OUT/logs/):"
  awk '$4=="failed"{print "   "$1"/"$2"/"$3}' "$DONE"
  echo "   ⚠ c154 no main: aborto por projeção é o resultado PREVISTO (DI-38a/DI-40), não falha."
fi
echo "detalhe: $DONE"
