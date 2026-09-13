"""T11/c149 — RE-MEDICAO independente da bateria estrutural nas 30 celulas da s42.
Nao reusa nenhum CSV da F5. READ-ONLY."""
import json,os,sys,numpy as np,pandas as pd,pyarrow.parquet as pq,csv
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
from src.standalone_harness import iteration_seed, seed_base
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149'
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,'42')
    if not os.path.isdir(d): continue
    exp='batch' if lab.startswith('q10_') else 'main'
    prob=lab[4:] if lab.startswith('q10_') else lab
    P=os.path.join(d,f'exp_{exp}_c149_{prob}_42')
    man=json.load(open(P+'.manifest.json'))
    recs=[json.loads(l) for l in open(P+'.jsonl') if l.strip()]
    hdr=[r for r in recs if r['rec']=='header'][0]
    dec=[r for r in recs if r['rec']=='decision']; fit=[r for r in recs if r['rec']=='fit']
    foot=[r for r in recs if r['rec']=='footer']
    D,M,q=hdr['D'],hdr['M'],man['q']; n_init=11*D-1; G=len(dec)
    real=pq.read_table(P+'__real.parquet').to_pandas()
    sur=pq.read_table(P+'__surrogate.parquet',columns=['regime','geracao','fe_treino_max','real_solution_id','transf_tipo','espaco_modelo','pred_classe']).to_pandas()
    npop=pq.ParquetFile(P+'__pop.parquet').metadata.num_rows
    ntim=pq.ParquetFile(P+'__timing.parquet').metadata.num_rows
    so=sur[sur.regime=='online']; ss=sur[sur.regime=='sonda']
    maxfe=31*D-1 if exp=='main' else n_init+200*q
    gs=sorted(set(ss.geracao.dropna().astype(int)))
    esp=sorted({1}|{g for g in range(1,G+1) if g%2==0}|{G})
    ftm=so.groupby('geracao').fe_treino_max.first()
    nt=[f['n_treino'] for f in fit]
    seeds_ok=sum(iteration_seed(seed_base('c149',42),12,g,1,bits32=True)==dec[g-1]['seed_nsga2'] for g in range(1,G+1))
    blocos=ss.groupby('geracao').size()
    rows.append(dict(exp=exp,prob=prob,D=D,M=M,q=q,G=G,
        A01_FE=int(len(real)==maxfe), fe=len(real), maxfe=maxfe,
        A01_feidx=int(list(real.fe_index)==list(range(len(real)))),
        A01_parada=int(man['motivo_parada']=='orcamento' and man['fe_final']==man['maxfe']),
        A02_init=int((real.fase=='init').sum()==n_init),
        A02_hash=int(man['doe_hash']==hdr['doe_hash']),
        A03_fits=int(len(fit)==G==ntim),
        A03_ntreino=sum(n==n_init+q*g for g,n in enumerate(nt)),
        A06_ftm=sum(int(ftm[g]==n_init+q*(g-1)-1) for g in ftm.index),
        A06_mono=int(bool((np.diff(ftm.values)>=0).all())),
        A04_cad=int(gs==esp), n_blocos=len(blocos),
        A04_2000=int(set(blocos.values)=={2000}),
        A04_man=int(man['sonda']['n_blocos']==len(blocos)),
        A07_cache=int(foot[0]['cache_hits']==man['cache_hits']==0),
        A07_clamp=int(foot[0]['n_clamp_sigma2']==0),
        A07_nger=int(foot[0]['n_geracoes']==man['n_geracoes']==G),
        A08_pop=int(npop==sum(n_init+q*g for g in range(1,G+1))), npop=npop,
        A08_sur=int(len(so)==sum(x['n_front_acq'] for x in dec)),
        A10_K10=sum(len(f['val_mse'])==10 for f in fit),
        A17_min=min(x['n_front_acq'] for x in dec), A17_sub1000=sum(x['n_front_acq']<1000 for x in dec),
        A24_seeds=seeds_ok, A24_distintas=len(set(x['seed_nsga2'] for x in dec)),
        A18_zs=int(set(so.transf_tipo.unique())=={'zscore'}),
        pred_nula=int(so.pred_classe.isna().all()),
        nfoot=len(foot), status=man['status'],
    ))
    print(f"[{exp}/{prob}] ok",flush=True)
df=pd.DataFrame(rows); df.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c149/s42_estrutural_c149.csv',index=False)
print("\n================ AGREGADO 30 CELULAS ================")
N=len(df); print("celulas:",N," G total:",df.G.sum()," fits:",df.G.sum())
for c in ['A01_FE','A01_feidx','A01_parada','A02_init','A02_hash','A03_fits','A04_cad','A04_2000','A04_man','A06_mono','A07_cache','A07_clamp','A07_nger','A08_pop','A08_sur','A18_zs','pred_nula']:
    print(f"  {c:12s} {int(df[c].sum())}/{N}")
print(f"  A03_ntreino  {int(df.A03_ntreino.sum())}/{int(df.G.sum())} fits")
print(f"  A06_ftm      {int(df.A06_ftm.sum())}/{int(df.G.sum())} geracoes")
print(f"  A10_K10      {int(df.A10_K10.sum())}/{int(df.G.sum())} fits")
print(f"  A24_seeds    {int(df.A24_seeds.sum())}/{int(df.G.sum())} bit-a-bit | distintas em {(df.A24_distintas==df.G).sum()}/{N} celulas")
print(f"  A17          |front|<1000 em {int(df.A17_sub1000.sum())}/{int(df.G.sum())} geracoes; min global={df.A17_min.min()}")
print(f"  blocos sonda totais = {int(df.n_blocos.sum())}  (linhas = {int(df.n_blocos.sum())*2000})")
print(f"  ② total = {int(df.npop.sum())}   ③online total = {int(df.G.sum())}*|front|")
print(f"  footers: {sorted(set(df.nfoot))}  status: {set(df.status)}")
