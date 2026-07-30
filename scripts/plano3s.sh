#!/usr/bin/env bash
# =============================================================================
# plano3s.sh — operação da rodada de 3 sementes SEM depender de terminal aberto.
#
# Por que existe: o lote3s.sh (como o lote42.sh) é um processo de primeiro plano
# com contador. Se ele morre junto com a sessão SSH, a rodada morre. Este script
# larga o lote DESTACADO (nohup + setsid, log em arquivo) e oferece os verbos de
# operação para serem chamados de fora, um `gcloud compute ssh --command` de cada
# vez. Nenhum dos 4 terminais atuais precisa ser tocado.
#
# VERBOS
#   censo      classifica a semente 42 em (1) ok (2) fila (3) falhou (4) desprio
#   estado     o que está rodando aqui agora (driver antigo, driver novo, runs)
#   parar      mata o lote ANTIGO por inteiro — driver + workers + runs
#   disparar   parar + largar o plano novo destacado   [$2 = horas de prazo, 32]
#   placar     última linha do contador + resumo do done.txt
#   seco       dry-run: mostra a grade que seria rodada, não roda nada
#
# A máquina é detectada pelo hostname; dá para forçar com MAQ=v5 na frente.
#
# CUIDADO DELIBERADO: `parar` usa pkill por padrão de linha de comando. Os
# padrões são ancorados em 'lote42'/'lote3s.sh'/'experiments.py --exp'/
# 'maxNumCompThreads' justamente para não pegar nada do sistema — no macOS,
# 'worker.sh' pegaria o com.apple.mdworker.shared do Spotlight (falso positivo
# já visto nesta operação).
# =============================================================================
set -uo pipefail

ACAO="${1:-ajuda}"

# ── qual máquina ────────────────────────────────────────────────────────────
H=$(hostname -s 2>/dev/null || hostname)
case "${MAQ:-}" in
  v5|v6|vm3|mac) : ;;
  *) case "$H" in
       v5-mestrado*)  MAQ=v5 ;;
       mestrado-v6*)  MAQ=v6 ;;
       matlab-vm3*)   MAQ=vm3 ;;
       *) [ "$(uname)" = "Darwin" ] && MAQ=mac || MAQ="" ;;
     esac ;;
esac
[ -n "$MAQ" ] || { echo "FATAL: nao reconheci o host '$H'. Rode com MAQ=v5|v6|vm3|mac na frente."; exit 2; }

REPO=""
for c in "$HOME/ua-dd-saea" "$HOME/Documents/python_repos/mestrado/ua-dd-saea" \
         "/home/jupyter/ua-dd-saea"; do
  [ -d "$c/.git" ] && REPO="$c" && break
done
[ -n "$REPO" ] || { echo "FATAL: repo nao encontrado (usuario=$(id -un) HOME=$HOME)"; exit 2; }

DRV=""
for c in "$HOME/lote3s.sh" "$REPO/scripts/lote3s.sh" "/home/jupyter/lote3s.sh"; do
  [ -f "$c" ] && DRV="$c" && break
done
[ -n "$DRV" ] || { echo "FATAL: lote3s.sh nao encontrado (procurei em \$HOME e \$REPO/scripts)"; exit 2; }

LOG="$HOME/lote3s_${MAQ}.log"
SEMENTES="${LOTE_SEEDS:-42 1 2}"

# ── o plano de cada máquina ─────────────────────────────────────────────────
# Repetir a mesma passada é de graça: o pré-filtro do lote3s.sh tira da grade
# tudo que já tem manifesto, então a 2ª/3ª passada só recolhe o que ficou
# sem manifesto (no MATLAB, a corrida de licença) e sai em segundos se não
# houver nada. É a rede de segurança para largar rodando 30h sem olhar.
# ── parar tudo que estiver rodando ──────────────────────────────────────────
parar_tudo() {
  echo "── parando o que estiver em voo em $MAQ"
  # 1) drivers primeiro, para não respawnar worker
  pkill -f 'plano3s\.sh __executar'    >/dev/null 2>&1
  pkill -f 'lote42\.sh$'               >/dev/null 2>&1
  pkill -f 'lote3s\.sh$'               >/dev/null 2>&1
  pkill -f '/lote42_.*worker\.sh'      >/dev/null 2>&1
  pkill -f '/lote3s_.*worker\.sh'      >/dev/null 2>&1
  sleep 1
  # 2) os runs de verdade
  pkill -f 'experiments\.py --exp'    >/dev/null 2>&1
  pkill -f 'maxNumCompThreads'        >/dev/null 2>&1
  sleep 3
  pkill -9 -f 'experiments\.py --exp' >/dev/null 2>&1
  pkill -9 -f 'maxNumCompThreads'     >/dev/null 2>&1
  sleep 1
  local n
  n=$(pgrep -f 'experiments\.py --exp' 2>/dev/null | wc -l | tr -d ' ')
  local m
  m=$(pgrep -f 'maxNumCompThreads' 2>/dev/null | wc -l | tr -d ' ')
  echo "   sobrou: $n run(s) python · $m run(s) matlab   (o certo é 0 e 0)"
}

estado() {
  echo "── $MAQ ($H) · usuario=$(id -un) · repo=$REPO"
  printf '   driver antigo (lote42): %s\n' "$(pgrep -f 'lote42\.sh$' 2>/dev/null | wc -l | tr -d ' ')"
  printf '   workers antigos:        %s\n' "$(pgrep -f '/lote42_.*worker\.sh' 2>/dev/null | wc -l | tr -d ' ')"
  printf '   driver novo   (lote3s): %s\n' "$(pgrep -f 'lote3s\.sh$' 2>/dev/null | wc -l | tr -d ' ')"
  printf '   plano destacado:        %s\n' "$(pgrep -f 'plano3s\.sh __executar' 2>/dev/null | wc -l | tr -d ' ')"
  printf '   runs python:            %s\n' "$(pgrep -f 'experiments\.py --exp' 2>/dev/null | wc -l | tr -d ' ')"
  printf '   runs matlab:            %s\n' "$(pgrep -f 'maxNumCompThreads' 2>/dev/null | wc -l | tr -d ' ')"
  [ -f "$LOG" ] && printf '   log: %s (%s bytes)\n' "$LOG" "$(wc -c < "$LOG" | tr -d ' ')"
}

placar() {
  local d
  d=$(ls -1dt /tmp/lote3s_${MAQ}_* 2>/dev/null | head -1)
  if [ -z "$d" ]; then echo "nenhum lote3s iniciado nesta maquina ainda."; else
    local g t ok fa sm
    g=$(wc -l < "$d/grid.txt" 2>/dev/null | tr -d ' ')
    t=$(wc -l < "$d/done.txt" 2>/dev/null | tr -d ' ')
    ok=$(awk '$5=="ok"||$5=="retried_ok"' "$d/done.txt" 2>/dev/null | wc -l | tr -d ' ')
    fa=$(awk '$5=="failed"'        "$d/done.txt" 2>/dev/null | wc -l | tr -d ' ')
    sm=$(awk '$5=="sem-manifesto"' "$d/done.txt" 2>/dev/null | wc -l | tr -d ' ')
    echo "── passada atual em $MAQ: $d"
    echo "   grade=$g  concluidas=$t  ok=$ok  falhou=$fa  sem-manifesto=$sm"
  fi
  if [ -f "$LOG" ]; then
    echo "── fim do log (o contador escreve com \\r, entao sai numa linha so):"
    tail -c 500 "$LOG" | tr '\r' '\n' | tail -3
  fi
}

# ── executor destacado (chamado por 'disparar', não à mão) ──────────────────
if [ "$ACAO" = "__executar" ]; then
  export LOTE_PRAZO_TS="${2:-0}"
  # sementes extras = as pedidas menos a 42 (usadas na fase opcional do c154)
  EXTRAS=$(echo "$SEMENTES" | tr ' ' '\n' | grep -v '^42$' | tr '\n' ' ')
  case "$MAQ" in vm3) N=3 ;; *) N=2 ;; esac
  echo "=== PLANO 3 SEMENTES · $MAQ · inicio $(date '+%d/%m %H:%M:%S') · prazo_ts=$LOTE_PRAZO_TS"
  echo "=== sementes=$SEMENTES · passadas do perfil=$N"
  i=1
  while [ "$i" -le "$N" ]; do
    echo
    echo "=== passada $i/$N · perfil $MAQ · $(date '+%d/%m %H:%M:%S')"
    LOTE=CONFIRMA LOTE_MAQ="$MAQ" LOTE_SEEDS="$SEMENTES" bash "$DRV"
    i=$((i + 1))
  done
  if [ "$MAQ" = "v5" ] && [ -n "$EXTRAS" ]; then
    i=1
    while [ "$i" -le 2 ]; do
      echo
      echo "=== passada c154 $i/2 · so D<=10 · sementes $EXTRAS · $(date '+%d/%m %H:%M:%S')"
      LOTE=CONFIRMA LOTE_MAQ=v5 LOTE_PARES="main/c154" LOTE_DMAX=10 \
        LOTE_SEEDS="$EXTRAS" bash "$DRV"
      i=$((i + 1))
    done
  fi
  echo
  echo "=== PLANO CONCLUIDO · $(date '+%d/%m %H:%M:%S')"
  exit 0
fi

case "$ACAO" in
  censo)
    CENSO=1 LOTE_MAQ="$MAQ" LOTE_SEEDS="$SEMENTES" bash "$DRV"
    [ "$MAQ" = "v5" ] && { echo; echo "── e o c154 (roda depois, so D<=10):";
      CENSO=1 LOTE_MAQ=v5 LOTE_PARES="main/c154" LOTE_SEEDS="$SEMENTES" bash "$DRV" | sed -n '/CENSO/,/TOTAL/p'; }
    [ "$MAQ" = "v6" ] && { echo; echo "── e o batch/c262 (fora das sementes extras):";
      CENSO=1 LOTE_MAQ=v6 LOTE_PARES="batch/c262" LOTE_SEEDS="$SEMENTES" bash "$DRV" | sed -n '/CENSO/,/TOTAL/p'; }
    ;;
  seco)
    LOTE_MAQ="$MAQ" LOTE_SEEDS="$SEMENTES" bash "$DRV"
    ;;
  estado) estado ;;
  placar) placar ;;
  parar)  parar_tudo; echo; estado ;;
  disparar)
    HORAS="${2:-32}"
    parar_tudo
    FIMTS=$(awk -v t="$(date +%s)" -v h="$HORAS" 'BEGIN{printf "%.0f", t+h*3600}' </dev/null)
    : > "$LOG"
    PRE=""
    command -v setsid    >/dev/null 2>&1 && PRE="setsid"
    # no Mac, 25h de execucao com a tampa aberta nao podem virar sleep
    [ "$MAQ" = "mac" ] && command -v caffeinate >/dev/null 2>&1 && PRE="caffeinate -i"
    echo
    echo "── largando o plano destacado (nada morre se esta sessao cair)"
    # shellcheck disable=SC2086
    nohup $PRE bash "$0" __executar "$FIMTS" >> "$LOG" 2>&1 < /dev/null &
    sleep 3
    echo "   pid=$!  ·  prazo=${HORAS}h  ·  log=$LOG"
    echo
    tr '\r' '\n' < "$LOG" | head -30
    ;;
  *)
    sed -n '2,25p' "$0"
    ;;
esac
