"""A10/A11 re-verificados em 6 celulas (reconstrucao INDEPENDENTE do lattice e das
vizinhancas de 20) + A3 determinismo (off/{P} x swap_small-lhs_{P} bit-a-bit)."""
import os, glob, json, itertools
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.spatial import distance_matrix
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m"

def lattice(H, M):
    # simplex-lattice Das-Dennis (o _create do ReferenceVectors)
    from itertools import combinations
    idx=list(combinations(range(H+M-1), M-1))
    V=[]
    for c in idx:
        prev=-1; row=[]
        for x in list(c)+[H+M-1]:
            row.append(x-prev-1); prev=x
        V.append(row)
    V=np.asarray(V,float)/H
    return V/np.linalg.norm(V,axis=1,keepdims=True)

alvos=["DTLZ2","ZDT1","WFG9","MMF16_20","BBOB_F1","MMF4"]
tot=0; dentro=0; multi=0; exc2=0; exc3=0; maxg=0
for lab in alvos:
    d=os.path.join(ROOT,lab,"42"); man=[p for p in glob.glob(d+"/*.manifest.json") if "__final" not in p]
    base=man[0][:-len(".manifest.json")]; m=json.load(open(man[0]))
    sg=pq.read_table(base+"__surrogate.parquet").to_pandas(); bu=sg[sg.regime=="offline"]
    xs=[c for c in sg.columns if c.startswith("x")]; M=len([c for c in sg.columns if c.startswith("mu_")])
    G={int(k):np.ascontiguousarray(v[xs].values) for k,v in bu.groupby("geracao")}
    ks=sorted(G); pop=G[ks[0]].shape[0]
    H=49 if M==2 else 13
    V=lattice(H,M); assert V.shape[0]==pop,(V.shape,pop,lab)
    NB=np.argsort(distance_matrix(V,V),axis=1)[:,:20]
    setsNB=[set(r.tolist()) for r in NB]
    for a,b in zip(ks,ks[1:]):
        A,B=G[a],G[b]
        sa=set(map(bytes,A))
        novos={}
        for i in range(pop):
            k=bytes(B[i])
            if k not in sa: novos.setdefault(k,[]).append(i)
        for k,slots in novos.items():
            tot+=1; maxg=max(maxg,len(slots))
            if len(slots)>1: multi+=1
            S=set(slots)
            if any(S<=nb for nb in setsNB): dentro+=1
            else:
                cob=min(len(c) for r in range(1,4)
                        for c in itertools.combinations(range(pop),r)
                        if S<=set().union(*[setsNB[j] for j in c])) if len(slots)<=60 else 99
                if cob==2: exc2+=1
                elif cob==3: exc3+=1
print("A10/A11 em %s"%alvos)
print("grupos de substituicao: %d | contidos em UMA vizinhanca de 20: %d (%.4f%%)"%(tot,dentro,100*dentro/tot))
print("excecoes: %d  (cobertas por 2: %d, por 3: %d)"%(tot-dentro,exc2,exc3))
print("grupos multi-slot (>1): %d (%.2f%%) | tamanho maximo observado: %d"%(multi,100*multi/tot,maxg))

print("\n--- A3 determinismo: off/{P} x swap_small-lhs_{P} ---")
for P in ["DTLZ2","MMF16_20","WFG9","ZDT1","ZDT4"]:
    o=glob.glob(os.path.join(ROOT,P,"42","*__surrogate.parquet"))[0]
    s=glob.glob(os.path.join(ROOT,"swap_small-lhs_"+P,"42","*__surrogate.parquet"))[0]
    A=pq.read_table(o).to_pandas(); B=pq.read_table(s).to_pandas()
    o7=glob.glob(os.path.join(ROOT,P,"42","*__final.parquet"))[0]
    s7=glob.glob(os.path.join(ROOT,"swap_small-lhs_"+P,"42","*__final.parquet"))[0]
    A7=pq.read_table(o7).to_pandas(); B7=pq.read_table(s7).to_pandas()
    cols=[c for c in A.columns if c[0] in "xms" and c!="semente"]
    eq3=A.shape==B.shape and all(np.array_equal(A[c].values,B[c].values) or
        (np.array_equal(np.nan_to_num(A[c].values.astype(float),nan=-9e99),
                        np.nan_to_num(B[c].values.astype(float),nan=-9e99)) if A[c].dtype.kind=="f" else False)
        for c in [c for c in A.columns if c.startswith(("x","mu_","sigma_"))])
    eq7=A7.shape==B7.shape and np.array_equal(A7[[c for c in A7.columns if c.startswith(("x","f"))]].values,
                                              B7[[c for c in B7.columns if c.startswith(("x","f"))]].values)
    print("  %-10s ③ bit-a-bit: %-5s (%d x %d linhas)  ⑦ bit-a-bit: %s"%(P,eq3,len(A),len(B),eq7))
