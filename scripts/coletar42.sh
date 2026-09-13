#!/usr/bin/env bash
# =============================================================================
# coletar42.sh — centraliza no Mac TODOS os outputs da rodada-42 das 4 máquinas.
#
#   bash coletar42.sh                  # DRY-RUN: só mede o que existe
#   COLETA=CONFIRMA bash coletar42.sh  # baixa de verdade
#
# Estrutura criada em ~/Documents/python_repos/mestrado/resultados_experimentos:
#
#   _maquinas/{mac,v5,v6,vm3}/experiments/...   cópia CRUA de cada máquina
#   data/experiments/...                        árvore MESCLADA (layout nativo —
#                                               use como --data-root)
#   INDICE.csv                                  1 linha por célula: alg, exp,
#                                               problema, semente, máquina,
#                                               status, motivo, wall, camadas
#   DUPLICADAS.csv                              células presentes em >1 máquina
#
# Roda quantas vezes quiser: o rsync é incremental e a mescla é reconstruída.
# NÃO toca no repo, NÃO apaga nada nas máquinas.
# =============================================================================
set -uo pipefail

REPO="$HOME/Documents/python_repos/mestrado/ua-dd-saea"
DEST="$HOME/Documents/python_repos/mestrado/resultados_experimentos"
[ -d "$REPO/.git" ] || { echo "FATAL: repo nao encontrado em $REPO"; exit 2; }

V5=(--zone=us-central1-a --project=skilled-text-480300-d9        --account=gdmello.nunes@gmail.com)
V6=(--zone=us-central1-a --project=project-2aa33d8c-94a7-488b-89e --account=invest.gdmn@gmail.com)
V3=(--zone=us-central1-a --project=project-2aa33d8c-94a7-488b-89e --account=invest.gdmn@gmail.com)

REMOTO_V5="/home/jupyter/ua-dd-saea/data/experiments"
REMOTO_V6="/home/jupyter/ua-dd-saea/data/experiments"
REMOTO_V3="/home/invest_gdmn/ua-dd-saea/data/experiments"

echo "════════════════════════════════════════════════════════════════"
echo " COLETA DA RODADA-42"
echo " origem: 3 VMs + Mac      destino: $DEST"
echo "════════════════════════════════════════════════════════════════"

medir() {  # $1 = rótulo, $2..= comando ssh
  echo -n "  $1: "
  shift
  "$@" 2>/dev/null | tr '\n' ' '
  echo
}
echo "── tamanho na origem"
medir "v5 " gcloud compute ssh v5-mestrado "${V5[@]}" --command="du -sh $REMOTO_V5 2>/dev/null | cut -f1; find $REMOTO_V5 -type f 2>/dev/null | wc -l"
medir "v6 " gcloud compute ssh mestrado-v6 "${V6[@]}" --command="du -sh $REMOTO_V6 2>/dev/null | cut -f1; find $REMOTO_V6 -type f 2>/dev/null | wc -l"
medir "vm3" gcloud compute ssh invest_gdmn@matlab-vm3 "${V3[@]}" --command="du -sh $REMOTO_V3 2>/dev/null | cut -f1; find $REMOTO_V3 -type f 2>/dev/null | wc -l"
echo -n "  mac: "; du -sh "$REPO/data/experiments" 2>/dev/null | cut -f1 | tr -d '\n'
echo "  $(find "$REPO/data/experiments" -type f 2>/dev/null | wc -l | tr -d ' ') arquivos"

if [ "${COLETA:-}" != "CONFIRMA" ]; then
  echo
  echo "DRY-RUN. Para baixar de verdade:  COLETA=CONFIRMA bash $0"
  echo "(o volume acima é o que vai trafegar; o scp mediu ~3,3 MB/s nas VMs)"
  exit 0
fi

mkdir -p "$DEST/_maquinas/mac" "$DEST/_maquinas/v5" "$DEST/_maquinas/v6" "$DEST/_maquinas/vm3"

echo
echo "── 1/4 · Mac (links duros — instantâneo, não duplica os 1,7 GB)"
mkdir -p "$DEST/_maquinas/mac/experiments"
rsync -a --info=stats1 --exclude '_baseline_pre_retrofit' \
      --link-dest="$REPO/data/experiments" \
      "$REPO/data/experiments/" "$DEST/_maquinas/mac/experiments/"

baixar() {  # $1=rótulo $2=nome-remoto $3=caminho-remoto  $4..=flags gcloud
  local rot="$1" host="$2" rem="$3"; shift 3
  echo
  echo "── $rot"
  rm -rf "$DEST/_maquinas/$rot/experiments.parcial"
  if gcloud compute scp --recurse "$@" "$host:$rem" \
       "$DEST/_maquinas/$rot/experiments.parcial"; then
    rm -rf "$DEST/_maquinas/$rot/experiments"
    mv "$DEST/_maquinas/$rot/experiments.parcial" "$DEST/_maquinas/$rot/experiments"
    echo "   ok · $(find "$DEST/_maquinas/$rot/experiments" -type f | wc -l | tr -d ' ') arquivos"
  else
    echo "   ✗ FALHOU — a cópia anterior de $rot (se houver) foi preservada"
  fi
}
echo
echo "── 2/4 · v5-mestrado"
baixar v5  "v5-mestrado"            "$REMOTO_V5" "${V5[@]}"
echo
echo "── 3/4 · mestrado-v6"
baixar v6  "mestrado-v6"            "$REMOTO_V6" "${V6[@]}"
echo
echo "── 4/4 · matlab-vm3"
baixar vm3 "invest_gdmn@matlab-vm3" "$REMOTO_V3" "${V3[@]}"

echo
echo "════ COLETA CONCLUÍDA"
du -sh "$DEST" 2>/dev/null
echo
echo "Agora gere a mescla, o índice e a tabela:"
echo "   python3 $DEST/../ua-dd-saea/scripts/tabela42.py"
