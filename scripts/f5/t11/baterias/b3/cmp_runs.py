import pandas as pd, numpy as np, hashlib, json, sys
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
S42='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3/MMF1/42'
srcs={
 's42'  : f'{S42}/exp_main_b3_MMF1_42',
 'smoke': f'{B}/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42',
 'g6com': f'{B}/g6_com/experiments/main/b3/exp_main_b3_MMF1_42',
 'g6sem': f'{B}/g6_sem/experiments/main/b3/exp_main_b3_MMF1_42',
}
real={}
for k,p in srcs.items():
    d=pd.read_parquet(p+'__real.parquet')
    real[k]=d
    print(k,'① shape',d.shape,'cols',list(d.columns))
def h(df,cols):
    return hashlib.sha256(np.ascontiguousarray(df[cols].to_numpy())).hexdigest()[:16]
xcols=[c for c in real['s42'].columns if c.startswith('x')]
fcols=[c for c in real['s42'].columns if c.startswith('f') and c!='fase']
print('xcols',xcols,'fcols',fcols)
for k in srcs: print(k,'hashX',h(real[k],xcols),'hashF',h(real[k],fcols))
import itertools
for a,b in itertools.combinations(srcs,2):
    A,B_=real[a],real[b]
    if A.shape!=B_.shape: print(f'{a} vs {b}: SHAPE DIFF {A.shape} {B_.shape}'); continue
    dx=np.abs(A[xcols].to_numpy()-B_[xcols].to_numpy()).max()
    df_=np.abs(A[fcols].to_numpy()-B_[fcols].to_numpy()).max()
    nrow=(~np.isclose(A[xcols].to_numpy(),B_[xcols].to_numpy(),rtol=0,atol=0)).any(1).sum()
    print(f'{a} vs {b}: maxdX={dx:.6g} maxdF={df_:.6g} linhas-X-diferentes={nrow}/{len(A)}')
