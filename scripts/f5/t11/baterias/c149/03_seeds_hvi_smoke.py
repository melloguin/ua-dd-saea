"""T11/c149 — A24 (sementes bit-a-bit) no SMOKE T11 + diagnostico do porque a
query-joia NAO discrimina nesta celula (MMF1/D=2 e 100% degenerada)."""
import json,sys,numpy as np,pyarrow.parquet as pq
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149')
from src.standalone_harness import iteration_seed, seed_base
from _hvlib import nd_mask,hvi2d_batch

P='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c149/exp_main_c149_MMF1_0'
recs=[json.loads(l) for l in open(P+'.jsonl') if l.strip()]
dec=[r for r in recs if r['rec']=='decision']; G=len(dec)
print("seed_base('c149',0) =",seed_base('c149',0))
ok=0; ex=[]
for g in range(1,G+1):
    s=iteration_seed(seed_base('c149',0),12,g,1,bits32=True)
    ok+= (s==dec[g-1]['seed_nsga2'])
    if g in (1,2,40): ex.append((g,s,dec[g-1]['seed_nsga2']))
print(f"A24 seed_nsga2 bit-a-bit: {ok}/{G} | distintas={len(set(d['seed_nsga2'] for d in dec))}/{G}")
for g,a,b in ex: print(f"   g={g:2d} calc={a} log={b} {'OK' if a==b else 'DIFERE'}")

# diagnostico da degenerescencia
real=pq.read_table(P+'__real.parquet').to_pandas()
sur=pq.read_table(P+'__surrogate.parquet').to_pandas(); so=sur[sur.regime=='online']
D,M,q,n_init=2,2,1,21
Fall=real[['f0','f1']].values.astype(np.float64)
nhvi=[];hsel=[];nemp=[]
for g in range(1,G+1):
    sub=so[so.geracao==g]
    MU=sub[['mu_0','mu_1']].values.astype(np.float64)
    A=Fall[:n_init+q*(g-1)];lo=A.min(0);hi=A.max(0);rng=np.where(hi>lo,hi-lo,1.0)
    An=(A-lo)/rng;Pn=An[nd_mask(An)];Cn=(MU-lo)/rng
    H=hvi2d_batch(Pn,np.full(2,1.1),Cn)
    nhvi.append(int((H>0).sum())); hsel.append(float(H.max())); nemp.append(dec[g-1].get('n_empatados'))
print(f"\nDEGENERESCENCIA (o motivo de a query-joia nao discriminar aqui):")
print(f"  gerações com ALGUM candidato de HVI>0 : {sum(n>0 for n in nhvi)}/{G}")
print(f"  max(HVI) sobre os 1000 candidatos     : max global = {max(hsel):.6g}")
print(f"  hvi_escolhido no ⑥                    : todos = {set(d['hvi_escolhido'] for d in dec)}")
print(f"  n_empatados (⑥)                       : {sorted(set(nemp))}")
print(f"  ⇒ HVI ≡ 0 em 40/40: as hipoteses A e B do `ref` sao INDISTINGUIVEIS nesta celula.")
print(f"    A refutacao da hipotese-B pertence a s42 (5.368 iteracoes, 25 celulas main).")
# fracao de coordenadas no bound (A21 geometria)
sel_ids=so.real_solution_id.dropna().astype(int).values
X=real[[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]].values
cam=[d['caminho'].split(':')[1] for d in dec]
import collections
fr=collections.defaultdict(list)
for g,sid in enumerate(sel_ids):
    x=X[sid]; fr[cam[g]].append(float(((x<=0.0)|(x>=1.0)).mean()))
print(f"\nGEOMETRIA (A21): fracao de coordenadas do X escolhido exatamente num bound do box")
for k,v in fr.items(): print(f"   {k:22s} n={len(v):3d}  media={np.mean(v):.3f}")
