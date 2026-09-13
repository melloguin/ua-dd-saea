#!/usr/bin/env python
"""T11/nsga2 — o par CROSS-CAMPANHA: smoke T11 (main/nsga2/DTLZ2) x celula s42.
Prova (a) que o codigo de hoje reproduz a busca da s42 BIT-A-BIT e (b) enumera o
delta EXATO de instrumentacao que a T11 acrescentou. READ-ONLY."""
import json, hashlib
import numpy as np, pyarrow.parquet as pq

S = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/nsga2/exp_main_nsga2_DTLZ2_42'
R = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga2/DTLZ2/42/exp_main_nsga2_DTLZ2_42'

def sha(df, cols):
    return hashlib.sha256(np.ascontiguousarray(df[cols].to_numpy()).tobytes()).hexdigest()[:16]

print('== (1) e (2): identidade bit-a-bit ==')
for lay in ('real', 'pop'):
    a = pq.read_table(S + f'__{lay}.parquet').to_pandas()
    b = pq.read_table(R + f'__{lay}.parquet').to_pandas()
    dif = [c for c in a.columns if not (a[c].astype(str) == b[c].astype(str)).all()]
    print(f'  {lay}: linhas {len(a)}/{len(b)} · colunas divergentes: {dif or "NENHUMA"}')
a = pq.read_table(S + '__real.parquet').to_pandas()
b = pq.read_table(R + '__real.parquet').to_pandas()
xc = [f'x{i}' for i in range(12)]; fc = [f'f{i}' for i in range(3)]
print('  sha256[:16] X  smoke/s42:', sha(a, xc), sha(b, xc))
print('  sha256[:16] f  smoke/s42:', sha(a, fc), sha(b, fc))

print('\n== (6): o jsonl, campo a campo (ignorando ts e wall) ==')
def jl(p): return [json.loads(l) for l in open(p) if l.strip()]
ea, eb = jl(S + '.jsonl'), jl(R + '.jsonl')
print('  linhas', len(ea), len(eb))
dif = 0
for x, y in zip(ea, eb):
    xx = {k: v for k, v in x.items() if k not in ('ts', 'tempo_geracao_s')}
    yy = {k: v for k, v in y.items() if k not in ('ts', 'tempo_geracao_s')}
    if xx != yy:
        dif += 1
        print('   DIFERE', x['rec'], {k: (xx.get(k), yy.get(k)) for k in set(xx) | set(yy) if xx.get(k) != yy.get(k)})
print('  registros semanticamente divergentes:', dif, '/', len(ea))

print('\n== (5): o delta EXATO da T11 no manifesto ==')
ma, mb = json.load(open(S + '.manifest.json')), json.load(open(R + '.manifest.json'))
print('  chaves NOVAS no T11:', sorted(set(ma) - set(mb)))
print('  chaves PERDIDAS    :', sorted(set(mb) - set(ma)))
for k in sorted(set(ma) & set(mb)):
    if ma[k] != mb[k] and k not in ('created_at', 'updated_at', 'paths', 'timing'):
        if isinstance(ma[k], dict):
            for kk in ma[k]:
                if ma[k].get(kk) != mb[k].get(kk):
                    print(f'  {k}.{kk}: T11={str(ma[k][kk])[:70]!r} ... s42={str(mb[k].get(kk))[:70]!r}')
        else:
            print(f'  {k}: T11={ma[k]!r} · s42={mb[k]!r}')
