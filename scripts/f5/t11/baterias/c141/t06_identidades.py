"""Re-medicao das identidades de mecanismo F2/F9/F7/U10 na s42 + no smoke T11."""
import sys, os, json
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141')
import numpy as np, pandas as pd
from lib_c141 import load, ROOT, rbf_fit, rbf_pred, front1

def analisa(man,ev,real,sur,tag):
    D=len([c for c in real.columns if c.startswith('x') and c[1:].isdigit()])
    M=len([c for c in real.columns if c.startswith('f') and c[1:].isdigit()])
    xs=[f'x{i}' for i in range(D)]; fsc=[f'f{i}' for i in range(M)]
    mus=[f'mu_{i}' for i in range(M)]
    so=sur[sur.regime=='online'].copy()
    gen=[e for e in ev if e['rec']=='c141_gen']
    # U10/F2: linhas com real_solution_id
    m=so[so.real_solution_id.notna()].copy()
    m['sid']=m.real_solution_id.astype(int)
    fei=dict(zip(real.solution_id,real.fe_index))
    m['fe_do_ponto']=m.sid.map(fei)
    ins=m[m.fe_do_ponto<=m.fe_treino_max]                # ponto JA no treino
    out=m[m.fe_do_ponto> m.fe_treino_max]                # fantasia genuina
    freal=real.set_index('solution_id')[fsc]
    def err(sub):
        if not len(sub): return np.array([])
        return np.abs(sub[mus].values - freal.loc[sub.sid][fsc].values)
    ei=err(ins); eo=err(out)
    # F9: Pb (argmax U) e ponto EXTRA fora da frente ND de (Q,U)?  -> proxy pelo ⑥:
    #     |Pa| = lote-1 quando Pb e extra; usa n_por_nivel.selecionados x lote
    # F7: teto de sigma_0
    N=man['params']['N_subpop']
    return dict(cel=tag,D=D,M=M,
        n_in=len(ins),in_erro_max=float(ei.max()) if len(ei) else np.nan,
        in_erro_zero=int((ei==0).all()) if len(ei) else -1,
        n_out=len(out),out_erro_med=float(np.median(eo)) if len(eo) else np.nan,
        out_otimista=float(np.mean(out[mus].values < freal.loc[out.sid][fsc].values)) if len(out) else np.nan,
        sigma0_teto=int(np.nanmax(so.sigma_0.values)==2*(2*N-1)),
        sigma0_int=int(np.all(np.equal(np.mod(so.sigma_0.values,1),0))),
        ciclos=len(gen))

rows=[]
for pb in sorted(os.listdir(ROOT)):
    if pb.startswith('.'): continue
    man,ev,real,pop,sur,tim=load(pb)
    rows.append(analisa(man,ev,real,sur,pb))
df=pd.DataFrame(rows)
df.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c141/t06_identidades_s42.csv',index=False)
print('=== s42 (25 celulas) ===')
print(df.to_string())
print()
print('F2/U10 in-sample: %d linhas ; erro EXATAMENTE 0 em %d/25 celulas ; max global %g'%(
    df.n_in.sum(),int((df.in_erro_zero==1).sum()),np.nanmax(df.in_erro_max)))
print('U10 fantasia genuina: %d linhas ; otimismo mediano por celula %.3f'%(df.n_out.sum(),np.nanmedian(df.out_otimista)))
print('F7 teto sigma_0 exato: %d/25 ; sigma_0 inteiro: %d/25'%(df.sigma0_teto.sum(),df.sigma0_int.sum()))

# smoke
print()
print('=== smoke T11 (MMF1) ===')
K='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c141/exp_main_c141_MMF1_42'
man=json.load(open(K+'.manifest.json')); ev=[json.loads(l) for l in open(K+'.jsonl') if l.strip()]
real=pd.read_parquet(K+'__real.parquet'); sur=pd.read_parquet(K+'__surrogate.parquet')
r=analisa(man,ev,real,sur,'smoke/MMF1'); print(r)

# F1 kernel — teste discriminativo num ciclo do smoke e num da s42
print()
print('=== F1 kernel: reconstrucao MQ c=1 poly=0 SEM scaling, no smoke ===')
so=sur[sur.regime=='online']
for g in [1,4,8]:
    sub=so[so.geracao==g]; ftm=int(sub.fe_treino_max.iloc[0])
    tr=real[real.fe_index<=ftm]
    X=tr[['x0','x1']].values.astype(np.float64); Y=tr[['f0','f1']].values.astype(np.float64)
    W=rbf_fit(X,Y); P=rbf_pred(sub[['x0','x1']].values.astype(np.float64),X,W)
    e=np.abs(P-sub[['mu_0','mu_1']].values.astype(np.float64))
    esc=np.abs(sub[['mu_0','mu_1']].values).mean()
    print(' g=%2d n_treino=%3d  erro mediano MQ_c1=%.3g  (escala |mu|=%.3g)  rel=%.3g'%(g,len(X),np.median(e),esc,np.median(e)/esc))
