import json,os,glob
import pandas as pd, numpy as np
F5="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
sn=pd.read_csv(f"{F5}/sonda_f52e.csv")
print("colunas sonda:",list(sn.columns))
e=sn[sn.alg=='e7'] if 'alg' in sn.columns else sn[sn.algoritmo=='e7']
print("linhas e7:",len(e),"| celulas:",e.problema.nunique() if 'problema' in e else '?')
print(e.head(3).T)
