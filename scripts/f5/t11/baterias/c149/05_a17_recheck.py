"""T11/c149 — RE-CHECAGEM do A17: |front|<1000. A F5 disse 33; a re-medicao deu 5.
Mede pelas DUAS vias independentes: (i) n_front_acq do ⑥ ; (ii) contagem de linhas da ③ por geracao."""
import json,os,numpy as np,pyarrow.parquet as pq,collections
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149'
tot6=tot3=0; det=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,'42')
    if not os.path.isdir(d): continue
    exp='batch' if lab.startswith('q10_') else 'main'
    prob=lab[4:] if lab.startswith('q10_') else lab
    P=os.path.join(d,f'exp_{exp}_c149_{prob}_42')
    dec=[json.loads(l) for l in open(P+'.jsonl') if l.strip()]
    dec=[r for r in dec if r['rec']=='decision']
    nf6=np.array([r['n_front_acq'] for r in dec])
    t=pq.read_table(P+'__surrogate.parquet',columns=['regime','geracao']).to_pandas()
    c3=t[t.regime=='online'].groupby('geracao').size()
    nf3=c3.reindex(range(1,len(dec)+1)).values
    a=int((nf6<1000).sum()); b=int((nf3<1000).sum())
    tot6+=a; tot3+=b
    concorda=bool((nf6==nf3).all())
    if a or b:
        det.append((exp,prob,len(dec),a,b,int(nf6.min()),int(nf3.min()),concorda))
print(f"{'celula':22s} {'G':>4s} {'<1000(⑥)':>9s} {'<1000(③)':>9s} {'min⑥':>6s} {'min③':>6s}  ⑥≡③")
for e,p,G,a,b,m6,m3,c in det: print(f"{e+'/'+p:22s} {G:4d} {a:9d} {b:9d} {m6:6d} {m3:6d}  {c}")
print(f"\nTOTAL <1000 : via ⑥ n_front_acq = {tot6}/8020 | via contagem de linhas da ③ = {tot3}/8020")
print("As duas vias CONCORDAM." if tot6==tot3 else "AS VIAS DIVERGEM.")
