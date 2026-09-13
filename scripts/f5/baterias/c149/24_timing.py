"""U7 detalhado + assinatura M.11 (fit ~ LINEAR em n, sem parede n^3) + custo do retreino do zero."""
import json,os,numpy as np,pandas as pd,pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    hdr=json.loads(open(p+".jsonl").readline()); D=hdr["D"];M=hdr["M"]
    son=[json.loads(l) for l in open(p+".jsonl") if '"rec": "sonda"' in l]
    gs=set(d_["geracao"] for d_ in son)
    tim=pq.read_table(p+"__timing.parquet").to_pandas()
    v1=(tim.tempo_fit_s+tim.tempo_busca_s>tim.tempo_geracao_s)
    v2=(tim.tempo_fit_s+tim.tempo_busca_s+tim.tempo_pred_sonda_s>tim.tempo_geracao_s)
    g2=set(tim.geracao[v2].tolist())
    nn=tim.n_acumulado.values.astype(float); tf=tim.tempo_fit_s.values.astype(float)
    tb=tim.tempo_busca_s.values.astype(float)
    A=np.vstack([nn,np.ones_like(nn)]).T; c,_,_,_=np.linalg.lstsq(A,tf,rcond=None)
    r2=1-((tf-A@c)**2).sum()/((tf-tf.mean())**2).sum()
    # razao fit(ultimo)/fit(primeiro) vs razao n(ultimo)/n(primeiro): linear => ~igual; n^3 => cubo
    rz_t=tf[-1]/tf[0]; rz_n=nn[-1]/nn[0]
    rows.append(dict(exp=exp,prob=prob,D=D,M=M,n=len(tim),
        U7_viol_fitbusca=int(v1.sum()),n_soma_com_sonda_excede=int(v2.sum()),
        excedentes_sao_sonda=bool(g2<=gs),n_blocos_sonda=len(gs),
        slope_ms=float(c[0]*1000),r2_lin=float(r2),
        razao_tempo=float(rz_t),razao_n=float(rz_n),expoente=float(np.log(rz_t)/np.log(rz_n)),
        fit_frac=float(tf.sum()/(tf.sum()+tb.sum())),
        busca_med_s=float(np.median(tb)),fit_med_s=float(np.median(tf)),
        fit_por_rede_por_epoca_ms=float(np.median(tf)/10/60*1000)))
df=pd.DataFrame(rows); df.to_csv(OUT+"/timing_c149.csv",index=False)
pd.set_option("display.width",250)
print(df.to_string(index=False))
print("\nU7 violacoes fit+busca>total:",df.U7_viol_fitbusca.sum(),"de",df.n.sum())
print("linhas com fit+busca+sonda>total:",df.n_soma_com_sonda_excede.sum(),"; TODAS em geracao com sonda:",bool(df.excedentes_sao_sonda.all()),"; blocos de sonda totais:",df.n_blocos_sonda.sum())
print("expoente empirico do fit (mediana/min/max): %.2f / %.2f / %.2f  (1=linear, 3=parede n^3)"%(df.expoente.median(),df.expoente.min(),df.expoente.max()))
print("R2 do ajuste LINEAR: mediana %.4f, min %.4f"%(df.r2_lin.median(),df.r2_lin.min()))
print("fracao do wall no fit: mediana %.3f (main %.3f, batch %.3f)"%(df.fit_frac.median(),df[df.exp=='main'].fit_frac.median(),df[df.exp=='batch'].fit_frac.median()))
