"""O desvio de indicador vm3(x86-Linux) x Mac(M1) medido nos smokes — piso O-18 revisitado."""
import sys, json, glob, os, re
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
import numpy as np, pandas as pd
from src import metrics as MT
SM='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments'
RE='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
rows=[]
for man in sorted(glob.glob(SM+'/*/*/*.manifest.json')):
    b=man[:-len('.manifest.json')]; m=json.load(open(man))
    nm=os.path.basename(b).split('_'); alg=m.get('alg') or nm[2]; pb=m.get('problema') or '_'.join(nm[3:-1])
    g=glob.glob(f'{RE}/{alg}/{pb}/42/*__real.parquet')
    if not g: continue
    try: ideal,nadir=MT.reference_bounds(pb); refn=MT.reference_set(pb)
    except Exception as e: continue
    o=[]
    for p in [g[0], b+'__real.parquet']:
        df=pd.read_parquet(p); fs=[c for c in df.columns if re.fullmatch(r'f\d+',c)]
        F=df[fs].values.astype(np.float64); nd=MT.nondominated_front(F)
        Fn=MT.normalize(nd,ideal,nadir); o.append((MT.igd_plus(Fn,refn),MT.hv(Fn),len(nd)))
    (i1,h1,n1),(i2,h2,n2)=o
    rows.append(dict(alg=alg,pb=pb,igd_vm3=i1,igd_mac=i2,d_igd=100*abs(i2-i1)/max(i1,1e-30),
                     hv_vm3=h1,hv_mac=h2,d_hv=100*abs(h2-h1)/max(h1,1e-30),nd_vm3=n1,nd_mac=n2))
d=pd.DataFrame(rows); d=d.sort_values('d_hv',ascending=False)
print(d.to_string())
print()
print('piso O-18 declarado: HV <=1,55%% ; IGD+ ate 58,98%%')
print('MEDIDO agora (mesma semente, mesmo codigo-de-mecanismo, maquinas diferentes):')
print('  d_HV   : mediana %.2f%%  max %.2f%%  ; acima de 1,55%%: %d/%d'%(d.d_hv.median(),d.d_hv.max(),int((d.d_hv>1.55).sum()),len(d)))
print('  d_IGD+ : mediana %.2f%%  max %.2f%%'%(d.d_igd.median(),d.d_igd.max()))
d.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c141/t12_piso_maquina.csv',index=False)
