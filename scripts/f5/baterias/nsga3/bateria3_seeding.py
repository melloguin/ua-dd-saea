"""Bateria 3 — verificacao EXATA do seeding D88 (NDSort + CrowdingDistance, desempate por indice)
   + diagnostico do underflow float32 no DTLZ4. READ-ONLY."""
import json,os
import numpy as np,pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3'
probs=sorted(p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}'))

def ndsort(F):
    n=len(F)
    dom=(F[:,None,:]<=F[None,:,:]).all(2)&(F[:,None,:]<F[None,:,:]).any(2)
    cnt=dom.sum(0); rank=np.zeros(n,int); cur=np.where(cnt==0)[0]; r=1
    while len(cur):
        rank[cur]=r; nxt=[]
        for i in cur:
            for j in np.where(dom[i])[0]:
                cnt[j]-=1
                if cnt[j]==0: nxt.append(j)
        cur=np.array(sorted(set(nxt)),int); r+=1
    return rank

def crowding(F,idx):
    """CrowdingDistance do PlatEMO sobre o subconjunto idx."""
    sub=F[idx]; n,M=sub.shape; cd=np.zeros(n)
    for m in range(M):
        o=np.argsort(sub[:,m],kind='stable'); fm=sub[o,m]
        cd[o[0]]=np.inf; cd[o[-1]]=np.inf
        rng=fm[-1]-fm[0]
        if rng>0:
            cd[o[1:-1]]+=(fm[2:]-fm[:-2])/rng
    return cd

rows=[]
for prob in probs:
    base=f'{ROOT}/{prob}/42/exp_main_nsga3_{prob}_42'
    man=json.load(open(base+'.manifest.json'))
    recs=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    hdr=[r for r in recs if r.get('rec')=='header'][0]
    D,M=hdr['D'],hdr['M']; init=11*D-1; Nef=man['params']['N_efetivo']
    R=pd.read_parquet(base+'__real.parquet')
    F=R.iloc[:init][[f'f{i}' for i in range(M)]].values.astype(np.float64)
    P=pd.read_parquet(base+'__pop.parquet')
    pop1=np.sort(P[P.geracao==1].solution_id.values)
    rk=ndsort(F)
    sel=[]; k=1
    while len(sel)+int((rk==k).sum())<=Nef:
        sel+=list(np.where(rk==k)[0]); k+=1
    borda=np.where(rk==k)[0]; falta=Nef-len(sel)
    if falta>0 and len(borda):
        cd=crowding(F,borda)
        # ordem decrescente de CD, desempate por indice crescente (estavel)
        o=np.lexsort((borda,-cd))
        sel+=list(borda[o[:falta]])
    sel=np.sort(np.array(sel,int))
    igual=(len(sel)==len(pop1)) and bool((sel==pop1).all())
    inter=len(set(sel)&set(pop1.tolist()))
    # underflow diagnostico
    Ff=R.iloc[:init][[f'f{i}' for i in range(M)]].values
    zeros=int((Ff==0).sum()); denorm=int(((np.abs(Ff)>0)&(np.abs(Ff)<1.18e-38)).sum())
    tiny=int(((np.abs(Ff)>0)&(np.abs(Ff)<1e-20)).sum())
    rows.append(dict(prob=prob,M=M,Nef=Nef,init=init,n_f1=int((rk==1).sum()),n_fronts=int(rk.max()),
        frentes_cheias=k-1,n_borda_usada=falta,identico=igual,interseccao=inter,
        zeros_f=zeros,denormais_f=denorm,tiny_f=tiny,frac_zero=round(zeros/(init*M),4)))
S=pd.DataFrame(rows); S.to_csv('seeding_D88_exato.csv',index=False)
pd.set_option('display.width',240); print(S.to_string(index=False))
print('\nIDENTICO em', int(S.identico.sum()),'/25 ; interseccao media',S.interseccao.mean())

# --- Monte Carlo do underflow no DTLZ4 ---
prob='DTLZ4'; D,M=12,3; init=131
R=pd.read_parquet(f'{ROOT}/{prob}/42/exp_main_nsga3_{prob}_42__real.parquet')
F=R.iloc[:init][['f0','f1','f2']].values.astype(np.float64)
mask=(F==0)
rng=np.random.default_rng(0); f1s=[];nfs=[]
for _ in range(200):
    G=F.copy()
    G[mask]=10**rng.uniform(-60,-46,size=mask.sum())   # valores double sub-float32
    rk=ndsort(G); f1s.append(int((rk==1).sum())); nfs.append(int(rk.max()))
print(f'\nDTLZ4 Monte-Carlo (200 sorteios, zeros float32 -> positivos double 1e-60..1e-46):')
print(' |F1| mediana',int(np.median(f1s)),'faixa',min(f1s),'-',max(f1s),' | n_frentes mediana',int(np.median(nfs)),'faixa',min(nfs),'-',max(nfs))
print(' LOG do run  : n_frente1=23  n_frentes=7   | recomputo float32: n_frente1=7 n_frentes=23')
print(' zeros exatos na ① init do DTLZ4:',int(mask.sum()),'de',init*M)
