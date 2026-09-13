"""Bateria 4 — DoE bit-a-bit, dinamica das geracoes, trajetorias, papel de regua. READ-ONLY."""
import json,os,glob,hashlib
import numpy as np,pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
DOE='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
probs=sorted(p for p in os.listdir(f'{ROOT}/nsga3') if os.path.isdir(f'{ROOT}/nsga3/{p}'))

rows=[];dyn=[]
for prob in probs:
    base=f'{ROOT}/nsga3/{prob}/42/exp_main_nsga3_{prob}_42'
    man=json.load(open(base+'.manifest.json'))
    recs=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    hdr=[r for r in recs if r.get('rec')=='header'][0]
    gens=[r for r in recs if r.get('rec')=='nsga3_gen']
    D,M=hdr['D'],hdr['M']; init=11*D-1
    R=pd.read_parquet(base+'__real.parquet'); P=pd.read_parquet(base+'__pop.parquet')
    xc=[f'x{i}' for i in range(D)]
    # --- U2 DoE bit-a-bit
    npy=f'{DOE}/{prob}/doe_{prob}_42.npy'
    dX=np.nan; hsh=None; ok_hash=None
    if os.path.exists(npy):
        A=np.load(npy)
        dX=float(np.abs(A[:init].astype(np.float32)-R.iloc[:init][xc].values).max())
        hsh=hashlib.sha256(np.ascontiguousarray(A).tobytes()).hexdigest()
        ok_hash=(hsh==man['doe_hash'])
    # --- duplicatas na ② (re-add de cache-hit)
    dup=int(P.groupby('geracao')['solution_id'].apply(lambda s:s.duplicated().sum()).sum())
    ids_validos=bool((P.solution_id<len(R)).all() and (P.solution_id>=0).all())
    gsec=sorted(P.geracao.unique())
    seq_ok=(gsec==list(range(1,len(gens)+1)))
    # --- dinamica
    nf1=np.array([g['n_front1'] for g in gens]); npop=np.array([g['n_pop'] for g in gens])
    ideal=np.array([g['ideal'] for g in gens],dtype=float)
    fbest=np.array([g['f_best'] for g in gens],dtype=float)
    nad=np.array([g['nadir_pop'] for g in gens],dtype=float)
    nad1=np.array([g['nadir_front1'] for g in gens],dtype=float)
    viol_ideal=int((np.diff(ideal,axis=0)>1e-12).sum())      # ideal deveria ser nao-crescente
    dyn.append(dict(prob=prob,M=M,ngen=len(gens),
        nf1_ini=int(nf1[0]),nf1_fim=int(nf1[-1]),nf1_med=float(nf1.mean()),
        frac_conv=float((nf1==npop).mean()),
        ideal_eq_fbest=bool(np.abs(ideal-fbest).max()==0),
        viol_ideal=viol_ideal,viol_ideal_pct=round(100*viol_ideal/max(1,(len(gens)-1)*M),2),
        nadir_eq=bool(np.abs(nad-nad1).max()==0),
        nadir_ge_ideal=bool((nad>=ideal-1e-12).all())))
    rows.append(dict(prob=prob,D=D,M=M,doe_dX=dX,doe_hash_ok=ok_hash,
        dup_pop=dup,ids_validos=ids_validos,geracoes_seq=seq_ok,
        n_pop_rows=len(P),esperado=len(gens)*man['params']['N_efetivo'],
        pop_ok=len(P)==len(gens)*man['params']['N_efetivo'],
        fases=str(sorted(R.fase.unique())),n_init=int((R.fase=='init').sum()),
        n_opt=int((R.fase!='init').sum())))
A=pd.DataFrame(rows); Dy=pd.DataFrame(dyn)
A.to_csv('doe_e_camadas.csv',index=False); Dy.to_csv('dinamica_geracoes.csv',index=False)
pd.set_option('display.width',250)
print(A.to_string(index=False)); print(); print(Dy.to_string(index=False))

# --- trajetorias: violacoes de monotonicidade do IGD+
tr=[]
for prob in probs:
    t=json.load(open(f'{F5}/trajetorias/main_nsga3_{prob}_42.json'))
    ig=np.array([c['igd_plus'] for c in t]); nnd=np.array([c['n_nd'] for c in t])
    d=np.diff(ig)
    tr.append(dict(prob=prob,n_cp=len(t),viol=int((d>1e-12).sum()),
        pior_delta=float(d.max()) if len(d) else 0,
        igd0=float(ig[0]),igdF=float(ig[-1]),ganho=float(ig[0]/ig[-1]) if ig[-1]>0 else np.inf,
        nd0=int(nnd[0]),ndF=int(nnd[-1])))
Tr=pd.DataFrame(tr); Tr.to_csv('trajetorias_nsga3.csv',index=False)
print('\n=== trajetorias (20 checkpoints) ==='); print(Tr.to_string(index=False))
print('violacoes totais:',Tr.viol.sum(),'de',int((Tr.n_cp-1).sum()),'transicoes')
