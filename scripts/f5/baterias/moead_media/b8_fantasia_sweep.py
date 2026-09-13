#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F5.3b · moead_media — BATERIA 8: fantasia (nd_pos_real/n_final) das 45 células
para os 4 offline pareados — sem métricas (barato). Endpoint da ⑦ no sweep.
"""
import os, glob
import pandas as pd
RES='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/moead_media'
rows=[]
for label in sorted(os.listdir(RES+'/moead_media')):
    for alg in ['moead_media','b5m','b5r','e103']:
        g=glob.glob('%s/%s/%s/42/*__final.parquet'%(RES,alg,label))
        if not g: continue
        d=pd.read_parquet(g[0], columns=['nd_pos_real','origem_geracao'])
        rows.append({'label':label,'alg':alg,'n_final':len(d),'n_nd':int(d.nd_pos_real.sum()),
                     'fantasia':float(d.nd_pos_real.mean()),'origem_ger':int(d.origem_geracao.max())})
D=pd.DataFrame(rows); D.to_csv(OUT+'/fantasia_45celulas.csv',index=False)
print(D.groupby('alg').agg(n=('fantasia','size'),fant_med=('fantasia','median'),
    nfinal_med=('n_final','median')).to_string())
p=D.pivot_table(index='label',columns='alg',values='fantasia')
print(); print(p.round(3).to_string())
print(); print('piso > b5m em %d/%d ; piso > b5r em %d/%d'%((p.moead_media>p.b5m).sum(),len(p),(p.moead_media>p.b5r).sum(),len(p)))
