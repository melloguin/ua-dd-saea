import numpy as np
from pymoo.indicators.hv import HV
def nd_mask(F):
    n=len(F); keep=np.ones(n,bool); order=np.lexsort(F.T[::-1]); Fs=F[order]
    for i in range(n):
        if not keep[order[i]]: continue
        d=(Fs[i]<=Fs).all(1)&(Fs[i]<Fs).any(1); keep[order[d]]=False
    return keep
def hvi2d_batch(P,ref,C):
    P=P[(P[:,0]<ref[0])&(P[:,1]<ref[1])]
    if len(P): P=P[nd_mask(P)]; P=P[np.argsort(P[:,0])]
    L=[-np.inf]; lvl=[ref[1]]
    for a,b in P: L.append(a); lvl.append(b)
    L=np.array(L); lvl=np.array(lvl)
    R=np.minimum(np.append(L[1:],ref[0]),ref[0]); Lc=np.minimum(np.maximum(L,-1e18),ref[0])
    w=np.maximum(R-Lc,0.0)
    sw=np.concatenate([np.cumsum(w[::-1])[::-1],[0.0]]); swl=np.concatenate([np.cumsum((w*lvl)[::-1])[::-1],[0.0]])
    a=C[:,0]; b=C[:,1]
    j=np.clip(np.searchsorted(L,a,side="right")-1,0,len(L)-1)
    mb=np.searchsorted(-lvl,-b,side="left")-1
    ok=(a<ref[0])&(b<ref[1])&(mb>=0)
    lo=np.minimum(j+1,mb+1); hi=mb+1
    seg=np.where(ok,(swl[lo]-swl[hi])-b*(sw[lo]-sw[hi]),0.0)
    head=np.where(ok&(j<=mb),np.maximum(R[j]-np.maximum(a,Lc[j]),0.0)*np.maximum(lvl[j]-b,0.0),0.0)
    return np.maximum(np.where(ok,head+seg,0.0),0.0)
from pymoo.indicators.hv import HV
def hvi_md(P,ref,C):
    ind=HV(ref_point=ref); base=ind(P) if len(P) else 0.0; out=np.zeros(len(C))
    for i,c in enumerate(C):
        if (c>=ref).any(): continue
        out[i]=(ind(np.vstack([P,c]))-base) if len(P) else ind(c[None,:])
    return out

