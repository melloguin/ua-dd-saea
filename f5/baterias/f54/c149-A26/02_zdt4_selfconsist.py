import json, numpy as np, pandas as pd, pyarrow.parquet as pq
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
XC=[f"x{i}" for i in range(10)]
def zdt4(X):
    X=np.asarray(X,float); f1=X[:,0]
    g=1+10*(X.shape[1]-1)+np.sum(X[:,1:]**2-10*np.cos(4*np.pi*X[:,1:]),axis=1)
    return np.column_stack([f1, g*(1-np.sqrt(f1/g))])
def load(cell,pref):
    p=f"{R}/{cell}/42/{pref}"
    return (pq.read_table(p+"__real.parquet").to_pandas(),
            pq.read_table(p+"__surrogate.parquet").to_pandas(),
            [json.loads(l) for l in open(p+".jsonl")])
L1b,L3b,L6b=load("q10_ZDT4","exp_batch_c149_ZDT4_42")
L1m,L3m,L6m=load("ZDT4","exp_main_c149_ZDT4_42")

print("=== (a) L1 self-consistency: f == ZDT4(x)? ===")
for nm,L1 in [("q10_ZDT4",L1b),("main_ZDT4",L1m)]:
    F=zdt4(L1[XC].values); err=np.abs(F-L1[["f0","f1"]].values)
    rel=err/np.maximum(np.abs(L1[["f0","f1"]].values),1e-12)
    print(f"  {nm}: max abs err={err.max():.3e}  max rel={rel.max():.3e}  | x0 range [{L1.x0.min():.4f},{L1.x0.max():.4f}] x1 range [{L1.x1.min():.4f},{L1.x1.max():.4f}]")

print("\n=== (b) L3 flagged X: in-box? ZDT4-evaluable? ===")
for nm,L3 in [("q10_ZDT4",L3b),("main_ZDT4",L3m)]:
    s=L3[(L3.regime=="online")&(L3.real_solution_id.notna())].sort_values("real_solution_id")
    X=s[XC].values
    print(f"  {nm}: n={len(s)} x0 [{X[:,0].min():.5f},{X[:,0].max():.5f}] xrest [{X[:,1:].min():.5f},{X[:,1:].max():.5f}]")

print("\n=== (c) DoE identical between the two ZDT4 cells? ===")
d1=L1b[L1b.fase=="init"][XC].values; d2=L1m[L1m.fase=="init"][XC].values
print("  shapes",d1.shape,d2.shape,"max|dX|=",np.abs(d1-d2).max())
h1=[json.loads(l) for l in open(f"{R}/q10_ZDT4/42/exp_batch_c149_ZDT4_42.jsonl")][0]
h2=[json.loads(l) for l in open(f"{R}/ZDT4/42/exp_main_c149_ZDT4_42.jsonl")][0]
print("  doe_hash batch",h1["doe_hash"],"| main",h2["doe_hash"],"| sonda_x_hash",h1["sonda_x_hash"]==h2["sonda_x_hash"])

print("\n=== (d) per-generation SET match of flagged X: L3 vs L1 ===")
def setmatch(L1,L3,q):
    s=L3[(L3.regime=="online")&(L3.real_solution_id.notna())]
    ok_id=0; ok_set=0; G=sorted(s.geracao.unique()); maxd=[]
    A1=L1.set_index("solution_id")[XC]
    for g in G:
        sub=s[s.geracao==g].sort_values("real_solution_id")
        sids=sub.real_solution_id.astype(int).values
        X3=sub[XC].values; X1=A1.loc[sids].values
        d=np.abs(X3-X1).max(); maxd.append(d)
        if d<1e-6: ok_id+=1
        # set match ignoring order
        o3=X3[np.lexsort(X3.T[::-1])]; o1=X1[np.lexsort(X1.T[::-1])]
        if np.abs(o3-o1).max()<1e-6: ok_set+=1
    return ok_id,ok_set,len(G),max(maxd)
print("  q10_ZDT4:",setmatch(L1b,L3b,10))
print("  main_ZDT4:",setmatch(L1m,L3m,1))

print("\n=== (e) global membership: is each L1 infill X anywhere in L3 online front? ===")
def membership(L1,L3,tag):
    F=L3[L3.regime=="online"][XC].values.astype(np.float64)
    key=lambda A: {tuple(np.round(r,6)) for r in A}
    KF=key(F)
    inf=L1[L1.fase!="init"][XC].values
    hit=sum(1 for r in inf if tuple(np.round(r,6)) in KF)
    print(f"  {tag}: {hit}/{len(inf)} infill X found in L3 front rows")
membership(L1b,L3b,"q10_ZDT4"); membership(L1m,L3m,"main_ZDT4")

print("\n=== (f) cross-cell: L3(q10_ZDT4) flagged X vs L1(main_ZDT4)? ===")
s=L3b[(L3b.regime=="online")&(L3b.real_solution_id.notna())][XC].values
KM={tuple(np.round(r,6)) for r in L1m[XC].values}
print("  flagged X of q10 L3 found in main L1:",sum(1 for r in s if tuple(np.round(r,6)) in KM),"/",len(s))
KB={tuple(np.round(r,6)) for r in L1b[XC].values}
print("  flagged X of q10 L3 found in q10 L1:",sum(1 for r in s if tuple(np.round(r,6)) in KB),"/",len(s))
