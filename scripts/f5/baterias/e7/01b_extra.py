import json
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
for p in ["ZDT1","MMF1","DTLZ2","BBOB_F1"]:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    man=json.load(open(base+".manifest.json"))
    ev=[json.loads(l) for l in open(base+".jsonl")]
    g=[e for e in ev if e['rec']=='e7_gen']
    print("==",p,"D?","fit_series:",json.dumps(man.get('fit_series'))[:300])
    print("  env:",json.dumps(man.get('env'))[:300])
    print("  paths:",json.dumps(man.get('paths'))[:400])
    print("  upload:",json.dumps(man.get('upload_status'))[:200])
    print("  g1 tfi:",g[0].get('tempo_fit_inicial_s'),"tf:",g[0].get('tempo_fit_s'),"| g2 tfi:",g[1].get('tempo_fit_inicial_s'),"tf:",g[1].get('tempo_fit_s'))
    print("  g1 dist_min_arquivo:",g[0].get('dist_min_arquivo'),"n_front1:",g[0].get('n_front1'),"RatioOld/Ratio:",g[0]['RatioOld'],g[0]['Ratio'])
    print("  batchsize:",g[0]['modelo_hp']['batchsize'],"neuronN:",g[0]['modelo_hp']['neuronN'])
    t=pd.read_parquet(base+"__timing.parquet")
    print("  timing head:",t.head(3).to_dict('records'))
