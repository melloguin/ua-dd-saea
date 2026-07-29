import json,os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
def nd_mask(Y):
    n=len(Y); dom=np.zeros(n,bool)
    for i in range(n):
        le=(Y<=Y[i]).all(axis=1); lt=(Y<Y[i]).any(axis=1)
        if (le&lt).any(): dom[i]=True
    return ~dom
# (a) DTLZ4: n_front1 x recomputo
for p in ["DTLZ4","DTLZ2"]:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]; D=hdr['D']; M=hdr['M']; n0=11*D-1
    G=[e for e in ev if e['rec']=='e7_gen']
    real=pd.read_parquet(base+"__real.parquet",columns=[f"f{i}" for i in range(M)])
    F=real.to_numpy(np.float64)
    diffs=[]
    for g in G[:8]:
        c=g['geracao']; n=min(n0+3*c,len(F))
        m=nd_mask(F[:n]); dup=len(F[:n])-len(np.unique(F[:n],axis=0))
        diffs.append((c,g['n_front1'],int(m.sum()),dup))
    print(p,"(ciclo, n_front1_log, ND_recomp, dups_no_arquivo):",diffs)
# (b) os 5 real_solution_id "errados" — X duplicado na pop final?
for p in ["MMF1","MMF11_L","MMF4"]:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]; D=hdr['D']; M=hdr['M']; n0=11*D-1
    G=[e for e in ev if e['rec']=='e7_gen']
    xc=[f"x{i}" for i in range(D)]
    real=pd.read_parquet(base+"__real.parquet",columns=xc)
    sur=pd.read_parquet(base+"__surrogate.parquet",columns=['regime','geracao','real_solution_id']+xc)
    on=sur[sur.regime=='online']; Xr=real[xc].to_numpy(np.float32)
    bad=[]
    for g in G:
        c=g['geracao']; blk=on[on.geracao==c].iloc[-100:]
        Xp=blk[xc].to_numpy(np.float32); rs=blk['real_solution_id'].to_numpy()
        for j in range(3):
            s=n0+3*(c-1)+j
            if s>=len(Xr): continue
            hits=[i for i in range(100) if Xp[i].tobytes()==Xr[s].tobytes()]
            if not hits: bad.append((c,s,'nao-achado',None)); continue
            ok=any((not np.isnan(rs[i])) and int(rs[i])==s for i in hits)
            if not ok or len(hits)>1:
                bad.append((c,s,f"n_hits={len(hits)}", [None if np.isnan(rs[i]) else int(rs[i]) for i in hits]))
    print(p,"ocorrencias com X duplicado/ambiguo na pop final:",bad[:12],"total",len(bad))
    # quantas linhas com real_solution_id no bloco online
    print("   linhas online com rsid:",int(on.real_solution_id.notna().sum()),"| esperado 3*C:",3*len(G))
