"""T11/c149 — os campos da instrumentacao T11: presentes? com DADO ou SENTINELA?
Procura o padrao do c217 (campo presente, dado sentinela)."""
import json,os,glob,numpy as np,pyarrow.parquet as pq
S='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c149/exp_main_c149_MMF1_0'
R='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149/MMF1/42/exp_main_c149_MMF1_42'
for nome,P in [('SMOKE T11 (s0)',S),('s42 (MMF1)',R)]:
    man=json.load(open(P+'.manifest.json'))
    recs=[json.loads(l) for l in open(P+'.jsonl') if l.strip()]
    sur=pq.read_table(P+'__surrogate.parquet')
    cols=sur.schema.names
    print(f"\n########## {nome} ##########")
    # I-2 REGRA_DO_ROTULO / I-5 y_treino_dist / I-6 sonda_estratificada
    print(f"  I-2 REGRA_DO_ROTULO em ⑤ : {'REGRA_DO_ROTULO' in man or 'REGRA_DO_ROTULO' in man.get('sigma_dict',{})}")
    print(f"  I-5 y_treino_dist        : {'y_treino_dist' in json.dumps(man)}")
    regs=set(sur.column('regime').to_pylist())
    print(f"  I-6 regimes na ③         : {regs}  (sonda_estratificada presente: {'sonda_estratificada' in regs})")
    print(f"  pmid_ids / ref_ids       : {'pmid_ids' in json.dumps(recs)} / {'ref_ids' in json.dumps(recs)}")
    # I-3 tempo_aval_real_s
    ta=[r for r in recs if 'tempo_aval_real_s' in json.dumps(r)]
    t1=pq.read_table(P+'__real.parquet')
    has=('tempo_aval_real_s' in t1.schema.names)
    print(f"  I-3 tempo_aval_real_s na ①: coluna presente={has}", end='')
    if has:
        v=np.array(t1.column('tempo_aval_real_s').to_pylist(),dtype=object)
        nn=np.array([x is not None for x in v])
        vv=np.array([x for x in v if x is not None],dtype=float)
        print(f" | nao-nulos={nn.sum()}/{len(v)} | zeros={int((vv==0).sum())} | mediana={np.median(vv):.3e}s | max={vv.max():.3e}s")
    else: print()
    print(f"  campanha_id              : {man.get('campanha_id')}")
    print(f"  repo_hash                : {(man.get('repo_hash') or '(vazio)')[:16]}")
    print(f"  schema_version           : {man.get('schema_version')}")
    print(f"  colunas da ③             : {len(cols)}")
    ck=[r for r in recs if r['rec']=='checkpoint']
    print(f"  eventos checkpoint (DI-43): {len(ck)}")
