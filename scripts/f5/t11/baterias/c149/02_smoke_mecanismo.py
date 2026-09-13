"""T11/c149 — a bateria de MECANISMO rodada no SMOKE T11 (codigo POS-T11).
Reproduz A14/A15/A18/A20/A21/A24 + U7 + cadencia da sonda + guards.
Celula: main/c149/MMF1/semente 0 (D=2,M=2,maxfe=61,G=40). READ-ONLY."""
import json,os,sys,numpy as np,pandas as pd,pyarrow.parquet as pq
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149')
from _hvlib import nd_mask,hvi2d_batch

P='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c149/exp_main_c149_MMF1_0'
man=json.load(open(P+'.manifest.json'))
recs=[json.loads(l) for l in open(P+'.jsonl') if l.strip()]
hdr=[r for r in recs if r['rec']=='header'][0]
dec=[r for r in recs if r['rec']=='decision']
fit=[r for r in recs if r['rec']=='fit']
snd=[r for r in recs if r['rec']=='sonda']
ckp=[r for r in recs if r['rec']=='checkpoint']
foot=[r for r in recs if r['rec']=='footer']
D,M,q=hdr['D'],hdr['M'],man['q']; n_init=11*D-1; G=len(dec)
print(f"== SMOKE T11 main/c149/MMF1/s0 : D={D} M={M} q={q} G={G} maxfe={man['maxfe']} n_init={n_init}")
print(f"   campanha_id={man['campanha_id']}  repo_hash={man['repo_hash'][:12]}  schema_v={man['schema_version']}")

real=pq.read_table(P+'__real.parquet').to_pandas()
sur =pq.read_table(P+'__surrogate.parquet').to_pandas()
pop =pq.read_table(P+'__pop.parquet').to_pandas()
tim =pq.read_table(P+'__timing.parquet').to_pandas()
R={}

# --- A01 orcamento / U1 ---
R['A01_len1']=(len(real)==31*D-1, f"len(①)={len(real)} esperado={31*D-1}")
R['A01_feidx']=(list(real.fe_index)==list(range(len(real))), "fe_index denso 0-based")
R['A01_parada']=(man['motivo_parada']=='orcamento' and man['fe_final']==man['maxfe'], f"{man['motivo_parada']} fe={man['fe_final']}")
# --- A02 DoE ---
R['A02_init']=((real.fase=='init').sum()==n_init, f"init={(real.fase=='init').sum()} esperado={n_init}")
R['A02_hash']=(man['doe_hash']==hdr['doe_hash'], "doe_hash ⑤≡⑥")
# --- A03/A06 treino ---
nt=[f['n_treino'] for f in fit]
R['A03_fits']=(len(fit)==G==len(dec)==len(tim), f"fit={len(fit)} dec={len(dec)} ④={len(tim)}")
R['A03_ntreino']=(all(n==n_init+q*(g) for g,n in enumerate(nt)), f"n_treino=11D-1+q(g-1) em {sum(n==n_init+q*g for g,n in enumerate(nt))}/{G}")
so=sur[sur.regime=='online']
ftm=so.groupby('geracao').fe_treino_max.first()
R['A06_ftm']=(all(ftm[g]==n_init+q*(g-1)-1 for g in ftm.index), f"fe_treino_max ok em {sum(ftm[g]==n_init+q*(g-1)-1 for g in ftm.index)}/{len(ftm)}; monotonico={bool((np.diff(ftm.values)>=0).all())}")
# --- A04 sonda ---
gs=sorted(set(sur[sur.regime=='sonda'].geracao.dropna().astype(int)))
esp=sorted({1}|{g for g in range(1,G+1) if g%2==0}|{G})
R['A04_cad']=(gs==esp, f"gers sonda={len(gs)} == esperado={len(esp)} : {gs==esp}")
blocos=sur[sur.regime=='sonda'].groupby('geracao').size()
R['A04_2000']=(set(blocos.values)=={2000}, f"blocos={len(blocos)} tamanhos={set(blocos.values)}")
R['A04_man']=(man['sonda']['n_blocos']==len(blocos), f"⑤ n_blocos={man['sonda']['n_blocos']} vs {len(blocos)}")
R['A04_nan']=(int(sur[[c for c in sur.columns if c.startswith(('mu_','sigma_'))]].isna().sum().sum())==0,"0 NaN em mu/sigma")
# --- A05 U7 timing ---
v=(tim.tempo_fit_s+tim.tempo_busca_s > tim.tempo_geracao_s).sum()
gsonda=set(gs)
esp2=tim[(tim.tempo_fit_s+tim.tempo_busca_s+tim.tempo_pred_sonda_s > tim.tempo_geracao_s)]
R['A05_U7']=(v==0, f"violacoes fit+busca>tempo_geracao = {v}/{len(tim)}")
R['A05_esp']=(set(esp2.geracao)<=gsonda, f"{len(esp2)} linhas com +sonda excedendo; todas em ger c/ sonda = {set(esp2.geracao)<=gsonda}")
# --- A07 guards ---
f0=foot[0]
R['A07']=(f0['cache_hits']==man['cache_hits']==0 and f0['n_clamp_sigma2']==0 and f0['n_geracoes']==G,
          f"cache_hits={f0['cache_hits']} clamp={f0['n_clamp_sigma2']} n_ger={f0['n_geracoes']}")
# --- A08 aritmetica ---
esp_pop=sum(n_init+q*g for g in range(1,G+1))
R['A08_pop']=(len(pop)==esp_pop, f"②={len(pop)} esperado Σ(11D-1+qg)={esp_pop}")
R['A08_sur']=(len(so)==sum(d['n_front_acq'] for d in dec), f"③online={len(so)} == Σ|front|={sum(d['n_front_acq'] for d in dec)}")
# --- A10 ensemble K=10 ---
R['A10']=(all(len(f['val_mse'])==10 for f in fit), f"val_mse len=10 em {sum(len(f['val_mse'])==10 for f in fit)}/{G} fits")
# --- A17 res.X rank0 ---
nf=[d['n_front_acq'] for d in dec]
R['A17']=(max(nf)<=1000, f"|front| min={min(nf)} max={max(nf)}; <1000 em {sum(x<1000 for x in nf)}/{G}")
# --- A18 z-score: transf_params(③) == z_mean/z_std(⑥.fit) ---
e18=[]
for g in range(1,G+1):
    tp=json.loads(so[so.geracao==g].transf_params.iloc[0])
    e18.append(max(np.abs(np.array(tp['mean'])-np.array(fit[g-1]['z_mean'])).max(),
                   np.abs(np.array(tp['std']) -np.array(fit[g-1]['z_std'])).max()))
R['A18']=(max(e18)<=1e-6, f"max|Δ transf_params vs z_mean/z_std| = {max(e18):.3e} em {G} blocos online")
# --- A14 sigma2 agregada em z ---
e14=[];e15=[]
for g in range(1,G+1):
    sub=so[so.geracao==g]; tp=json.loads(sub.transf_params.iloc[0])
    zm=np.array(tp['mean']); zs=np.array(tp['std'])
    MU=sub[[f'mu_{j}' for j in range(M)]].values.astype(float)
    SG=sub[[f'sigma_{j}' for j in range(M)]].values.astype(float)
    sel=np.where(sub.real_solution_id.notna().values)[0][0]
    s2z=((SG/zs)**2).sum(1)
    e14.append(abs(s2z[sel]-dec[g-1]['sigma2_agg_sel_z']))
    muz=(MU-zm)/zs; s2zc=(SG/zs)**2
    e15.append(max(np.abs(muz.min(0)-np.array(dec[g-1]['acq_resF_mu_z_min'])).max(),
                   np.abs(muz.max(0)-np.array(dec[g-1]['acq_resF_mu_z_max'])).max(),
                   np.abs(s2zc.max(0)-np.array(dec[g-1]['acq_resF_sigma2_z_max'])).max()))
R['A14']=(max(e14)<=1e-5, f"max|Σ(σ/std)² − sigma2_agg_sel_z| = {max(e14):.3e} em {G}/{G}")
R['A15']=(max(e15)<=1e-5, f"max|acq_resF_* reconstituido − ⑥| = {max(e15):.3e} em {G}/{G}")
# --- A20/A21 QUERY-JOIA D96 ---
Fall=real[[f'f{j}' for j in range(M)]].values.astype(np.float64)
okA=argA=0; errA=[]; tie_n=tie_ok=0; okB=argB=0; caminhos={}
for g in range(1,G+1):
    sub=so[so.geracao==g]; d=dec[g-1]
    caminhos[d['caminho']]=caminhos.get(d['caminho'],0)+1
    MU=sub[[f'mu_{j}' for j in range(M)]].values.astype(np.float64)
    SG=sub[[f'sigma_{j}' for j in range(M)]].values.astype(np.float64)
    sel=np.where(sub.real_solution_id.notna().values)[0]
    if len(sel)!=q: continue
    A=Fall[:n_init+q*(g-1)]; lo=A.min(0); hi=A.max(0); rng=np.where(hi>lo,hi-lo,1.0)
    An=(A-lo)/rng; Pn=An[nd_mask(An)]; Cn=(MU-lo)/rng
    tp=json.loads(sub.transf_params.iloc[0]); zs=np.array(tp['std'],float)
    s2z=((SG/zs)**2).sum(1)
    HA=hvi2d_batch(Pn,np.full(M,1.1),Cn)
    refB=np.maximum(1.1*Pn.max(0),1e-9); HB=hvi2d_batch(Pn,refB,Cn)
    hs=HA[sel[0]]; err=abs(hs-d['hvi_escolhido']); errA.append(err)
    okA+= err<=1e-6+1e-4*abs(d['hvi_escolhido']); argA+= hs>=HA.max()-1e-12
    okB+= abs(HB[sel[0]]-d['hvi_escolhido'])<=1e-6+1e-4*abs(d['hvi_escolhido']); argB+= HB[sel[0]]>=HB.max()-1e-12
    top=HA.max(); emp=np.where(HA>=top-1e-12)[0]
    if len(emp)>1 and d['caminho'].endswith('desempate_sigma'):
        tie_n+=1
        if abs(s2z[sel[0]]-s2z[emp].max())<=1e-4*max(1,s2z[emp].max()): tie_ok+=1
R['A20_hvi']=(okA==G, f"hvi_escolhido reproduzido (ref=1,1 literal) {okA}/{G}; err med={np.median(errA):.3e} max={np.max(errA):.3e}")
R['A20_arg']=(argA==G, f"escolhido = argmax global do HVI em {argA}/{G}")
R['A20_refut']=(okB<okA, f"HIPOTESE-B (ref=1,1×nadir do FRONT-ND): {okB}/{G} valor, {argB}/{G} argmax — REFUTADA")
R['A21_tie']=(tie_ok==tie_n, f"desempate σ²-em-z: {tie_ok}/{tie_n}")
print("   caminhos:",caminhos)
# --- A24 sementes ---
try:
    from src.seeds import iteration_seed, seed_base
    ok=0
    for g in range(1,G+1):
        s=iteration_seed(seed_base('c149',0),12,g,1,bits32=True)
        ok+= (s==dec[g-1]['seed_nsga2'])
    R['A24']=(ok==G, f"seed_nsga2 reproduzido bit-a-bit {ok}/{G}; distintas={len(set(d['seed_nsga2'] for d in dec))}/{G}")
except Exception as e:
    R['A24']=(None, f"nao rodou: {type(e).__name__}: {e}")
# --- T11: CHECKPOINT ---
R['T11_ckpt']=(len(ckp)>0, f"{len(ckp)} evento(s) checkpoint: "+json.dumps(ckp))
R['T11_ckpt_custo']=(True, f"custo total={sum(c['tempo_checkpoint_s'] for c in ckp):.4f}s de wall={man['timing']['tempo_total_s']:.1f}s = {100*sum(c['tempo_checkpoint_s'] for c in ckp)/man['timing']['tempo_total_s']:.4f}%")

print()
for k,(ok,det) in R.items():
    print(f"{'✅' if ok else ('⬜' if ok is None else '❌')} {k:16s} {det}")
json.dump({k:[v[0],v[1]] for k,v in R.items()},open('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c149/smoke_mecanismo_c149.json','w'),indent=1,ensure_ascii=False)
