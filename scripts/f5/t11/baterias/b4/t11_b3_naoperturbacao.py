"""T11/b4 — bateria 3: NAO-PERTURBACAO em tres eixos, todos MEDIDOS por mim.
  (a) g6_com x g6_sem  — a sonda liga/desliga muda a busca?
  (b) smoke T11 x s42  — o codigo de HOJE (com bloco estratificado NOVO) x o
      codigo que produziu a rodada-42: a MESMA celula, main/b4/MMF1/42.
  (c) confere os hashes que o handoff §5 declara.
READ-ONLY.
"""
import json, hashlib
import numpy as np
import pyarrow.parquet as pq

E = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4/MMF1/42/exp_main_b4_MMF1_42'
PARES = [
    ('g6_com x g6_sem', f'{E}/g6_com/experiments/main/b4/exp_main_b4_MMF1_42',
     f'{E}/g6_sem/experiments/main/b4/exp_main_b4_MMF1_42'),
    ('smokeT11 x s42', f'{E}/smoke_matlab/experiments/main/b4/exp_main_b4_MMF1_42', S42),
    ('g6_com x s42', f'{E}/g6_com/experiments/main/b4/exp_main_b4_MMF1_42', S42),
]
COLS1 = ['solution_id', 'x0', 'x1', 'f0', 'f1', 'fe_index', 'fase']

for nome, A, B in PARES:
    a = pq.read_table(A + '__real.parquet').to_pandas()
    b = pq.read_table(B + '__real.parquet').to_pandas()
    ok = (len(a) == len(b)) and all((a[c].values == b[c].values).all() for c in COLS1)
    ha = hashlib.sha256(np.ascontiguousarray(a[['x0', 'x1', 'f0', 'f1']].values).tobytes()).hexdigest()
    hb = hashlib.sha256(np.ascontiguousarray(b[['x0', 'x1', 'f0', 'f1']].values).tobytes()).hexdigest()
    ma, mb = json.load(open(A + '.manifest.json')), json.load(open(B + '.manifest.json'))
    ga = [x for x in map(json.loads, open(A + '.jsonl')) if x.get('rec') == 'b4_gen']
    gb = [x for x in map(json.loads, open(B + '.jsonl')) if x.get('rec') == 'b4_gen']
    dec = ['ramo', 'lote', 'rr', 'tr', 'fe', 'arquivo', 'n_treino', 'n_acumulado', 'fe_treino_max']
    igual_dec = all(all(x[k] == y[k] for k in dec) for x, y in zip(ga, gb)) and len(ga) == len(gb)
    ref_eq = sum(1 for x, y in zip(ga, gb) if x['ref_ids'] == y['ref_ids'])
    p0d = max(abs(x['p0'] - y['p0']) for x, y in zip(ga, gb) if np.isfinite(x['p0']) and np.isfinite(y['p0']))
    print(f'\n== {nome} ==')
    print(f'  (1) __real: {len(a)} x {len(b)} linhas · BIT-IDENTICA em {COLS1}: {ok}')
    print(f'      sha256(X|F) A={ha[:16]}  B={hb[:16]}  IGUAL={ha == hb}')
    print(f'  ⑥ b4_gen: {len(ga)} x {len(gb)} · campos de DECISAO {dec} identicos: {igual_dec}')
    print(f'      ref_ids identicos em {ref_eq}/{len(ga)} geracoes · max|Δp0| = {p0d:.3e} (float32 ulp)')
    print(f'  manifesto: fe_final {ma["fe_final"]}/{mb["fe_final"]} · n_geracoes {ma["n_geracoes"]}/{mb["n_geracoes"]}'
          f' · cache_hits {ma["cache_hits"]}/{mb["cache_hits"]} · doe_hash igual: {ma["doe_hash"] == mb["doe_hash"]}')
    print(f'      repo_hash A={ma.get("repo_hash", "")!r} B={mb.get("repo_hash", "")!r}'
          f' · campanha_id A={ma.get("campanha_id")!r} B={mb.get("campanha_id")!r}')
    sa = pq.read_table(A + '__surrogate.parquet').to_pandas()
    sb = pq.read_table(B + '__surrogate.parquet').to_pandas()
    print('      ③ por regime  A: ' + str(dict(sa.regime.value_counts())) + '  B: ' + str(dict(sb.regime.value_counts())))

# hash declarado pelo handoff §5 para o b4: 2404320fa6f276b9
print('\n== hash §5 do handoff (b4 = 2404320fa6f276b9) ==')
a = pq.read_table(f'{E}/g6_com/experiments/main/b4/exp_main_b4_MMF1_42__real.parquet').to_pandas()
cands = {
    'sha256(x0,x1,f0,f1 float32 C-order)': hashlib.sha256(np.ascontiguousarray(a[['x0', 'x1', 'f0', 'f1']].values).tobytes()).hexdigest(),
    'sha256(f0,f1 float64)': hashlib.sha256(np.ascontiguousarray(a[['f0', 'f1']].values.astype('float64')).tobytes()).hexdigest(),
    'sha256(x float64)': hashlib.sha256(np.ascontiguousarray(a[['x0', 'x1']].values.astype('float64')).tobytes()).hexdigest(),
    'sha256(x float32)': hashlib.sha256(np.ascontiguousarray(a[['x0', 'x1']].values).tobytes()).hexdigest(),
}
for k, v in cands.items():
    print(f'  {k:40s} {v[:16]}  {"<== BATE" if v[:16] == "2404320fa6f276b9" else ""}')
