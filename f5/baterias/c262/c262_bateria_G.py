#!/usr/bin/env python
"""
BATERIA G — c262 qNEHVI: diagnósticos finais. READ-ONLY.

G1 ZDT1: os 277 pares "violadores" do teste F3 são COLAPSO float32 (D53), não
   quebra da hipótese σ — caracterizo a magnitude relativa do Δacqf e onde
   (iteração) os pares aparecem; e mostro que o mesmo bloco tem pares
   float32-idênticos com Δacqf ≈ 0.
G2 células ABORTADAS/FALHAS (⚪/🔴, fora da análise): motivo_parada, progresso,
   e o q do header do batch — para o inventário do teto T.
G3 tempo: perfil fit × busca (o custo O(n³) e a fração da aquisição).
G4 lengthscales: curva de aprendizado (mediana por objetivo, 1ª × última iteração)
   e ARD vivo.
"""
import json, glob, os, collections
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262'
RAW = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/_old/_bucket_raw/experiments'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c262'
PROBS = sorted(os.path.basename(p) for p in glob.glob(f'{ROOT}/*') if os.path.isdir(p))

# ---------------- G1 ----------------
b = f'{ROOT}/ZDT1/42/exp_main_c262_ZDT1_42'
dec = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
hdr = [d for d in dec if d.get('rec') == 'header'][0]
dec = [d for d in dec if d.get('rec') == 'decision']
D = hdr['D']
sur = pd.read_parquet(b + '__surrogate.parquet')
on = sur[sur.regime == 'online'].reset_index(drop=True)
xc = [f'x{i}' for i in range(D)]
dby = {d['it']: d for d in dec}
recs = []
for g, sub in on.groupby('geracao', sort=True):
    d = dby.get(int(g))
    if d is None or len(sub) != 10: continue
    a = np.array(d['acqf_todos_restarts'], float)
    X = sub[xc].values.astype(np.float64)
    sca = max(1.0, abs(a).max())
    best = int(np.argmax(a))
    sig = np.array([i for i in range(10) if i != best] + [best])
    for i in range(10):
        for j in range(i+1, 10):
            if np.array_equal(X[i], X[j]):                 # BIT-idênticos em float32
                da = abs(a[sig[i]] - a[sig[j]])
                recs.append(dict(it=int(g), i=i, j=j, dacqf=da, dacqf_rel=da/sca,
                                 viol=bool(da > 1e-6*sca),
                                 cache_hit=bool(d.get('cache_hit', False)),
                                 dist_min=d['dist_min_arquivo'],
                                 n_train=d.get('n_train')))
G1 = pd.DataFrame(recs); G1.to_csv(f'{OUT}/c262_G1_zdt1_pares.csv', index=False)
v = G1[G1.viol]
print('== G1 ZDT1: pares float32-idênticos ==')
print('pares:', len(G1), '| violadores(>1e-6 rel):', len(v), '(%.2f%%)' % (100*len(v)/len(G1)))
print('Δacqf_rel dos NÃO-violadores: mediana %.3g | máx %.3g'
      % (G1[~G1.viol].dacqf_rel.median(), G1[~G1.viol].dacqf_rel.max()))
print('Δacqf_rel dos violadores: mín %.3g | mediana %.3g | máx %.3g'
      % (v.dacqf_rel.min(), v.dacqf_rel.median(), v.dacqf_rel.max()))
print('iterações distintas com violação:', v.it.nunique(), '| faixa de it:', int(v.it.min()), '-', int(v.it.max()))
print('n_train mediano nos violadores: %.0f (de %d..%d)' % (v.n_train.median(), int(G1.n_train.min()), int(G1.n_train.max())))
print('violadores em iterações de cache-hit:', int(v.cache_hit.sum()), '/', int(G1.cache_hit.sum()))

# ---------------- G2 ----------------
g2 = []
for exp, probs in [('main', ['WFG1', 'ZDT3', 'DTLZ7', 'MMF16_20']),
                   ('batch', ['DTLZ2', 'MMF16_20', 'WFG9', 'ZDT1', 'ZDT4'])]:
    for p in probs:
        f = f'{RAW}/{exp}/c262/exp_{exp}_c262_{p}_42.manifest.json'
        if not os.path.exists(f): continue
        m = json.load(open(f))
        jl = f'{RAW}/{exp}/c262/exp_{exp}_c262_{p}_42.jsonl'
        hq = None; nd = 0
        if os.path.exists(jl):
            for l in open(jl):
                if not l.strip(): continue
                try: r = json.loads(l)
                except Exception: continue
                if r.get('rec') == 'header': hq = r.get('params', {}).get('q')
                if r.get('rec') == 'decision': nd += 1
        st = (m.get('stack_trace') or '').strip()
        g2.append(dict(exp=exp, problema=p, status=m['status'],
                       motivo_parada=m.get('motivo_parada'), n_retries=m['n_retries'],
                       maxfe=m['maxfe'], fe_final=m['fe_final'],
                       progresso=(None if not m['maxfe'] else round(100*m['fe_final']/m['maxfe'], 1)),
                       q_header=hq, n_decisoes=nd,
                       wall_s=m['timing']['tempo_total_s'],
                       excerto=st.split('\n')[-1][:150]))
G2 = pd.DataFrame(g2); G2.to_csv(f'{OUT}/c262_G2_abortadas.csv', index=False)
pd.set_option('display.width', 320); pd.set_option('display.max_colwidth', 90)
print('\n== G2 células fora da análise ==')
print(G2.to_string())

# ---------------- G3/G4 ----------------
rows = []
for prob in PROBS:
    bb = f'{ROOT}/{prob}/42'; s = f'exp_main_c262_{prob}_42'
    man = json.load(open(f'{bb}/{s}.manifest.json'))
    tim = pd.read_parquet(f'{bb}/{s}__timing.parquet')
    d = [json.loads(l) for l in open(f'{bb}/{s}.jsonl') if l.strip()]
    d = [x for x in d if x.get('rec') == 'decision']
    fit = tim['tempo_fit_s'].values; bus = tim['tempo_busca_s'].values
    n = np.array([x.get('n_train') or man['fe_final'] for x in d], float)
    ls0 = np.array([[o['lengthscale_med'] for o in d[0]['modelo_hp']['por_objetivo']]])
    ls1 = np.array([[o['lengthscale_med'] for o in d[-1]['modelo_hp']['por_objetivo']]])
    ard = sum(1 for x in d for o in x['modelo_hp']['por_objetivo']
              if o['lengthscale_max'] > o['lengthscale_min'])
    ardt = sum(len(x['modelo_hp']['por_objetivo']) for x in d)
    # expoente empírico do custo de fit: log t = a + b log n
    ok = (fit > 0) & (n > 0)
    bexp = np.polyfit(np.log(n[ok]), np.log(fit[ok]), 1)[0] if ok.sum() > 20 else np.nan
    rows.append(dict(problema=prob, D=man['maxfe'] and (man['maxfe']+1)//31, n_ger=man['n_geracoes'],
                     t_fit=fit.sum(), t_busca=bus.sum(),
                     frac_busca=100*bus.sum()/(fit.sum()+bus.sum()),
                     fit_ini=fit[0], fit_fim=fit[-1], razao_fit=fit[-1]/max(fit[1], 1e-9),
                     expoente_n=bexp, busca_med=np.median(bus),
                     ls_ini=json.dumps([round(v, 4) for v in ls0[0]]),
                     ls_fim=json.dumps([round(v, 4) for v in ls1[0]]),
                     ard_vivo=ard, ard_tot=ardt, wall_h=man['timing']['tempo_total_s']/3600))
G3 = pd.DataFrame(rows); G3.to_csv(f'{OUT}/c262_G3_tempo_hp.csv', index=False)
print('\n== G3/G4 tempo e hiperparâmetros ==')
print(G3.to_string())
print('\nTOTAL wall: %.2f h-core | fração da BUSCA (aquisição): %.1f%% do (fit+busca)'
      % (G3.wall_h.sum(), 100*G3.t_busca.sum()/(G3.t_fit.sum()+G3.t_busca.sum())))
print('ARD vivo: %d/%d | expoente empírico de t_fit vs n: mediana %.2f'
      % (G3.ard_vivo.sum(), G3.ard_tot.sum(), G3.expoente_n.median()))
