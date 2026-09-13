"""t02 — nao-perturbacao da sonda (par G-6 COM x SEM) + divergencia T11 x R42 na (1).
READ-ONLY."""
import json, hashlib, os
import pandas as pd, numpy as np

B = 'exp_main_c141_MMF1_42'
ROOTS = {
 'smoke': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c141',
 'g6com': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/c141',
 'g6sem': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/experiments/main/c141',
 'r42'  : '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c141/MMF1/42',
}
out=[]
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.append(s)

real={}; man={}; ev={}
for k,r in ROOTS.items():
    real[k]=pd.read_parquet(f'{r}/{B}__real.parquet')
    man[k]=json.load(open(f'{r}/{B}.manifest.json'))
    ev[k]=[json.loads(l) for l in open(f'{r}/{B}.jsonl') if l.strip()]

def sha_real(df):
    cols=['solution_id','x0','x1','f0','f1','fe_index','fase']
    b=df[cols].to_csv(index=False).encode()
    return hashlib.sha256(b).hexdigest()

P('--- sha256 da (1) [solution_id,x,f,fe_index,fase] ---')
for k in ROOTS: P(f'  {k:6s} n={len(real[k]):3d} sha={sha_real(real[k])[:32]}')

P('')
P('--- manifesto: sonda / n_geracoes / batches ---')
for k in ROOTS:
    m=man[k]; s=m['sonda']
    P(f"  {k:6s} n_ger={m['n_geracoes']:3d} fe={m['fe_final']} cache={m['cache_hits']} "
      f"desligada={s.get('desligada')} n_blocos={s['n_blocos']} ger={s.get('geracoes')} "
      f"n_acum={[f['n_acumulado'] for f in m['fit_series']]}")

P('')
P('--- (3) online: linhas por regime ---')
for k in ROOTS:
    sur=pd.read_parquet(f'{ROOTS[k]}/{B}__surrogate.parquet')
    P(f"  {k:6s} {sur['regime'].value_counts().to_dict()}")

P('')
P('--- COM x SEM: (1) bit-a-bit ---')
a,b=real['g6com'],real['g6sem']
P('  shapes', a.shape, b.shape)
for c in ['x0','x1','f0','f1']:
    d=np.abs(a[c].values-b[c].values).max()
    P(f'   max|D{c}| = {d:.3e}')
P('  solution_id identicos:', bool((a['solution_id'].values==b['solution_id'].values).all()))
P('  fase identica:', bool((a['fase'].values==b['fase'].values).all()))
P('  sha iguais:', sha_real(a)==sha_real(b))

P('')
P('--- smoke x g6com: mesma configuracao? ---')
P('  sha smoke == sha g6com:', sha_real(real['smoke'])==sha_real(real['g6com']))

P('')
P('--- T11 x R42: onde diverge a (1)? ---')
t,r=real['smoke'],real['r42']
n=min(len(t),len(r))
dif=np.where((np.abs(t['x0'].values[:n]-r['x0'].values[:n])>0)|(np.abs(t['x1'].values[:n]-r['x1'].values[:n])>0))[0]
P('  primeiro fe_index divergente:', dif[0] if len(dif) else None, ' n_divergentes:', len(dif))
P('  init (fase==init) T11:', (t['fase']=='init').sum(), ' R42:', (r['fase']=='init').sum())
ti=t[t['fase']=='init']; ri=r[r['fase']=='init']
P('  init max|Dx|:', float(np.abs(ti[['x0','x1']].values-ri[['x0','x1']].values).max()))
P('  init max|Df|:', float(np.abs(ti[['f0','f1']].values-ri[['f0','f1']].values).max()))

P('')
P('--- guards no (6) ---')
from collections import Counter
for k in ROOTS:
    g=[e for e in ev[k] if e.get('rec')=='guard']
    P(f'  {k:6s}', Counter(x.get('name') for x in g), [ (x.get('name'),x.get('fe')) for x in g])

P('')
P('--- footer ---')
for k in ROOTS:
    f=[e for e in ev[k] if e.get('rec')=='footer']
    P(f'  {k:6s} n_footer={len(f)}', json.dumps(f[0], ensure_ascii=False)[:400] if f else '')

P('')
P('--- header ---')
for k in ROOTS:
    h=[e for e in ev[k] if e.get('rec')=='header']
    P(f'  {k:6s}', json.dumps(h[0], ensure_ascii=False)[:600] if h else '')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'t02_pares.txt'),'w').write('\n'.join(out))
