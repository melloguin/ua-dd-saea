#!/bin/zsh
# PROVA CAUSAL de e81-B28 — reproduz os pares header/footer espurios em SANDBOX.
# NAO rodar a partir do repo: `data_root="data"` e RELATIVO ao cwd e escreveria
# na celula de PRODUCAO (esse e exatamente o defeito).
SANDBOX=${1:-/tmp/b28sim}
REPO=/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
mkdir -p "$SANDBOX" && cd "$SANDBOX" && rm -rf data
PYTHONPATH=$REPO $PY -m unittest tests.test_batch_q10.TestTetoFiadoPeloDespachante -v
echo "--- arquivos criados no sandbox ---"
find "$SANDBOX" -type f
$PY - <<'PYEOF'
import json,collections
p='data/experiments/batch/e81/exp_batch_e81_ZDT4_42.jsonl'
rs=[json.loads(l) for l in open(p) if l.strip()]
print(len(rs),'linhas',dict(collections.Counter(r['rec'] for r in rs)))
PYEOF
