import json, collections, datetime as dt, statistics, os
P_CONS='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81/q10_ZDT4/42/exp_batch_e81_ZDT4_42.jsonl'
P_SITE='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/batch/e81/exp_batch_e81_ZDT4_42.jsonl'

def load(p):
    out=[]
    for i,l in enumerate(open(p)):
        l=l.strip()
        if not l: continue
        out.append((i+1,json.loads(l)))
    return out

def parse(ts):
    return dt.datetime.fromisoformat(ts.replace('Z','+00:00'))

for tag,p in (('CONSOLIDADO',P_CONS),('SITIO',P_SITE)):
    recs=load(p)
    c=collections.Counter(d['rec'] for _,d in recs)
    print('==',tag,os.path.basename(p))
    print('  linhas',len(recs),dict(c))
    hf=[(ln,d) for ln,d in recs if d['rec'] in ('header','footer')]
    # separa legitimos x espurios
    leg_h=[(ln,d) for ln,d in hf if d['rec']=='header' and d.get('D') is not None]
    leg_f=[(ln,d) for ln,d in hf if d['rec']=='footer' and 'fe_final' in d]
    esp_h=[(ln,d) for ln,d in hf if d['rec']=='header' and d.get('D') is None]
    esp_f=[(ln,d) for ln,d in hf if d['rec']=='footer' and 'fe_final' not in d]
    print('  header runner=%d  header despachante=%d  footer runner=%d  footer despachante=%d'%(len(leg_h),len(esp_h),len(leg_f),len(esp_f)))
    print('  posicao 1o espurio: linha',esp_h[0][0] if esp_h else None,' ultima linha do arquivo:',recs[-1][0])
    # todos os espurios estao APOS o footer do runner?
    lf=leg_f[0][0]
    print('  todos os espurios apos o footer do runner?',all(ln>lf for ln,_ in esp_h+esp_f))
    ts=[parse(d['ts']) for _,d in esp_h]
    print('  janela espuria:',ts[0].isoformat(),'->',parse(esp_f[-1][1]['ts']).isoformat())
    # rajadas: agrupa headers espurios com gap > 60s
    bursts=[]; cur=[ts[0]]
    for a,b in zip(ts,ts[1:]):
        if (b-a).total_seconds()>60: bursts.append(cur); cur=[b]
        else: cur.append(b)
    bursts.append(cur)
    print('  n_rajadas(gap>60s)=%d  tamanhos=%s'%(len(bursts),collections.Counter(len(x) for x in bursts)))
    tt=[d['tempo_total_s'] for _,d in esp_f]
    print('  tempo_total_s espurio: min=%.4f max=%.4f soma=%.4f mediana=%.4f'%(min(tt),max(tt),sum(tt),statistics.median(tt)))
    st=collections.Counter((d.get('status'),d.get('n_retries'),d.get('stack_trace')) for _,d in esp_f)
    print('  status/n_retries/stack dos espurios:',dict(st))
    # campos NULOS nos headers espurios
    kh=collections.Counter(tuple(sorted(d.keys())) for _,d in esp_h)
    print('  chaves distintas nos headers espurios:',len(kh), list(kh.keys())[0])
    kr=leg_h[0][1]
    print('  campos do header do runner AUSENTES no espurio:',sorted(set(kr)-set(list(kh.keys())[0])))
    print('  run_id/exp/problema/semente/modo_rapido do espurio:',{k:esp_h[0][1].get(k) for k in ('run_id','exp','alg','problema','semente','modo_rapido')})
    # rajadas por dia
    print('  por dia:',dict(collections.Counter(t.date().isoformat() for t in ts)))
