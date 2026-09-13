"""[T11/c122] EXERCITA a REGRA_DO_ROTULO sobre o smoke preservado.
READ-ONLY: le evidencia_T11 + data/sonda (artefato) + o repo oficial (import).
Nao escreve nada fora de f5/t11/baterias/c122/."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/algorithms/c122_θ-DEA-DP")
from scipy.stats import spearmanr
from deap import tools as dtools
from src import problems as P
from src import standalone_harness as SH
PROB=SH._instantiate("MMF1")

B="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c122/exp_main_c122_MMF1_0"
mf=json.load(open(B+".manifest.json"))
fmin=np.array(mf["params"]["f_min"]); fmax=np.array(mf["params"]["f_max"])
RP=dtools.uniform_reference_points(2,10); print("ref_points:",RP.shape)
recs=[json.loads(l) for l in open(B+".jsonl")]
snd={r["geracao"]:r for r in recs if r.get("rec")=="sonda"}
est={r["geracao"]:r for r in recs if r.get("rec")=="sonda_estratificada"}
real=pd.read_parquet(B+"__real.parquet"); pop=pd.read_parquet(B+"__pop.parquet")
s3=pd.read_parquet(B+"__surrogate.parquet")
gab=pd.read_parquet("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet")
print("gabarito cols:",list(gab.columns),gab.shape, gab.dtypes.to_dict())
F_real=real.set_index("solution_id")[["f0","f1"]].astype(np.float64)

def pbi(F):
    Z=(F-fmin)/(fmax-fmin)
    rn=np.linalg.norm(RP.T,axis=0); zn=np.linalg.norm(Z,axis=1).reshape(-1,1)
    d1=Z.dot(RP.T)/rn; d2=np.sqrt(np.maximum(zn*zn-d1*d1,0))
    k=np.argmin(d2,axis=1)
    return k, d1[np.arange(len(k)),k]+5.0*d2[np.arange(len(k)),k]

def e_true(Fz,Fr):
    kz,pz=pbi(Fz); kr,pr=pbi(Fr)
    le=(Fz[:,None,:]<=Fr[None,:,:]).all(2); lt=(Fz[:,None,:]<Fr[None,:,:]).any(2)
    ep=(le&lt).sum(1)
    et=((kz[:,None]==kr[None,:])&(pz[:,None]<pr[None,:])).sum(1)
    return ep+et, ep, et

# ── (A) ref_ids da sonda x ② (a armadilha do off-by-one) ────────────────────
pg={int(g):set(map(int,v)) for g,v in pop.groupby("geracao")["solution_id"].apply(list).items()}
lin=[]
for g,r in sorted(snd.items()):
    ids=set(map(int,r["ref_ids"]))
    lin.append((g,len(ids),ids==pg.get(g),ids==pg.get(g-1)))
print("\n(A) sonda.ref_ids == ②(g)? / == ②(g-1)?")
print("  g==②(g):",sum(1 for x in lin if x[2]),"/",len(lin),
      " g==②(g-1):",sum(1 for x in lin if x[3]),"/",len(lin))
print("  primeiros:",lin[:5])
mult=[(g,len(r["ref_ids"]),len(set(r["ref_ids"]))) for g,r in sorted(snd.items())]
print("  ref_ids MULTISET (len x distintos):",[m for m in mult if m[1]!=m[2]], "blocos com repetido:",sum(1 for m in mult if m[1]!=m[2]),"/",len(mult))

# ── (B) regua Sobol: e_true vs modelo, por bloco ────────────────────────────
gab=gab.iloc[:2000]  # ONLINE = primeiras S_online=2000 (sidecar)
Fs=gab[["f0","f1"]].to_numpy(np.float64)
Xs=gab[["x0","x1"]].to_numpy(np.float64)
out=[]
for g,r in sorted(snd.items()):
    Fr=F_real.loc[list(map(int,r["ref_ids"]))].to_numpy()
    et,ep,eth=e_true(Fs,Fr)
    blo=s3[(s3.regime=="sonda")&(s3.geracao==g)]
    assert len(blo)==2000
    dX=np.abs(blo[["x0","x1"]].to_numpy(np.float64)-Xs).max()
    m=blo.pred_score.to_numpy(np.float64)
    rho=spearmanr(m,et).correlation
    pos=(et>0)
    auc=np.nan
    if pos.any() and (~pos).any():
        from scipy.stats import rankdata
        rk=rankdata(m); n1=pos.sum(); n0=(~pos).sum()
        auc=(rk[pos].sum()-n1*(n1+1)/2)/(n1*n0)
    out.append(dict(bloco="regua",g=g,n_ref=r["n_ref"],prev_pos=pos.mean(),
                    rho=rho,auc=auc,ez_mod_max=m.max(),ez_true_max=et.max(),
                    ez_mod_mean=m.mean(),ez_true_mean=et.mean(),dX=dX))
# ── (C) bloco estratificado ────────────────────────────────────────────────
for g,r in sorted(est.items()):
    blo=s3[(s3.regime=="sonda_estratificada")&(s3.geracao==g)]
    X=blo[["x0","x1"]].to_numpy(np.float64)
    Fe=np.atleast_2d(np.asarray(P.evaluate_problem(PROB,X),dtype=np.float64))
    Fr=F_real.loc[list(map(int,r["ref_ids"]))].to_numpy()
    et,ep,eth=e_true(Fe,Fr)
    m=blo.mu_0.to_numpy(np.float64)          # ⚠ o score foi gravado em mu_0
    rho=spearmanr(m,et).correlation
    pos=(et>0); auc=np.nan
    if pos.any() and (~pos).any():
        from scipy.stats import rankdata
        rk=rankdata(m); n1=pos.sum(); n0=(~pos).sum()
        auc=(rk[pos].sum()-n1*(n1+1)/2)/(n1*n0)
    out.append(dict(bloco="estratificada",g=g,n_ref=r["n_ref"],prev_pos=pos.mean(),
                    rho=rho,auc=auc,ez_mod_max=m.max(),ez_true_max=et.max(),
                    ez_mod_mean=m.mean(),ez_true_mean=et.mean()))
df=pd.DataFrame(out)
df.to_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c122/regra_do_rotulo.csv",index=False)
print("\n(B/C) RESUMO por tipo de bloco (regra 12: NUNCA na mesma analise):")
print(df.groupby("bloco")[["prev_pos","rho","auc","ez_mod_mean","ez_true_mean","ez_mod_max","ez_true_max"]].describe().T.to_string())
print("\nPor bloco:"); print(df.to_string())
# ND-in-block das duas populacoes de teste (o numero '0,4% x 7,4%' do handoff)
nd_regua=len(P._nds_filter(Fs))/len(Fs)
print("\nND-no-bloco da REGUA Sobol (2000 pts):",nd_regua)
print("ND-no-bloco estratificado (logado):",[est[g]["prevalencia_nd_no_bloco"] for g in sorted(est)])
