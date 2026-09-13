"""t03 — bateria de mecanismo do c141 sobre o smoke T11 (main/c141/MMF1/42).
Reconstroi a cascata MMRAEA a partir da (1) e da (3) e confronta com o (6).
READ-ONLY sobre os dados."""
import json, os, sys
import numpy as np, pandas as pd

sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141')
import lib_c141 as L

STEM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c141/exp_main_c141_MMF1_42'
D, M = 2, 2
out = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)

man = json.load(open(STEM + '.manifest.json'))
ev = [json.loads(l) for l in open(STEM + '.jsonl') if l.strip()]
real = pd.read_parquet(STEM + '__real.parquet')
pop = pd.read_parquet(STEM + '__pop.parquet')
sur = pd.read_parquet(STEM + '__surrogate.parquet')
tim = pd.read_parquet(STEM + '__timing.parquet')
gens = [e for e in ev if e.get('rec') == 'c141_gen']
sondas = [e for e in ev if e.get('rec') == 'sonda']
online = sur[sur.regime == 'online']

xc = [f'x{i}' for i in range(D)]; fc = [f'f{i}' for i in range(M)]; mc = [f'mu_{i}' for i in range(M)]

P('#### U1 orcamento')
P('  maxfe', man['maxfe'], 'fe_final', man['fe_final'], 'len(1)', len(real), '31D-1', 31*D-1)
P('  fe_index denso 0-based:', bool((real.fe_index.values == np.arange(len(real))).all()))
P('  solution_id denso:', bool((real.solution_id.values == np.arange(len(real))).all()))
P('  termino:', [e for e in ev if e.get('rec')=='footer'][0]['termino'], 'status', man['status'])

P('#### U2 DoE')
ini = real[real.fase == 'init']
P('  n_init', len(ini), '11D-1', 11*D-1)
doe = pd.read_parquet('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/MMF1/doe_MMF1_42.parquet') \
    if os.path.exists('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/MMF1/doe_MMF1_42.parquet') else None
if doe is not None:
    cols = [c for c in doe.columns if c.startswith('x')]
    A = ini[xc].values.astype(np.float64); B = doe[cols].values[:len(ini)].astype(np.float64)
    P('  doe cols', cols, 'shape', doe.shape)
    P('  max|dX| float64 =', float(np.abs(A-B).max()))
    P('  bit-exato em float32:', bool((A.astype(np.float32) == B.astype(np.float32)).all()))
else:
    P('  artefato DoE nao encontrado localmente')
P('  doe_hash manifesto', man['doe_hash'][:16], '== header', [e for e in ev if e.get('rec')=='header'][0]['doe_hash'][:16])

P('#### U3 1 retreino por ciclo')
P('  |4|', len(tim), '|c141_gen|', len(gens), '|fit_series|', len(man['fit_series']))
P('  geracao sequencial:', list(tim.geracao.values) == list(range(1, len(tim)+1)))
P('  tempo_fit_s todos > 0:', bool((tim.tempo_fit_s > 0).all()))
P('  n_geracoes manifesto', man['n_geracoes'], '= |gen|+1 ?', man['n_geracoes'] == len(gens)+1)

P('#### U4 sonda: cadencia + join posicional')
gsond = [e['geracao'] for e in sondas]
P('  blocos', len(sondas), 'geracoes', gsond, 'manifest.geracoes', man['sonda']['geracoes'])
P('  linhas por bloco:', sur[sur.regime=='sonda'].groupby('geracao').size().to_dict())
esperado = [g for g in range(1, man['n_geracoes']+1) if g == 1 or g % 2 == 0]
if man['n_geracoes'] % 2 == 1 and man['n_geracoes'] not in esperado:
    esperado.append(man['n_geracoes'])
P('  regra g==1 v g%%2==0 + finalProbe ->', sorted(esperado), ' bate:', sorted(esperado) == sorted(gsond))
P('  motivo do ultimo bloco:', sondas[-1].get('motivo'), ' | todos motivos:', [e.get('motivo') for e in sondas])
P('  n_falhas', man['sonda']['n_falhas'])
gab = pd.read_parquet('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet') \
    if os.path.exists('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet') else None
if gab is not None:
    gx = [c for c in gab.columns if c.startswith('x')]
    P('  gabarito shape', gab.shape, 'cols', list(gab.columns)[:8])
    G0 = gab[gx].values[:2000].astype(np.float64)
    mx = 0.0
    for g in gsond:
        Bk = sur[(sur.regime=='sonda') & (sur.geracao==g)][xc].values.astype(np.float64)
        mx = max(mx, float(np.abs(Bk-G0).max()))
    P('  max|dX| join POSICIONAL [0:2000] em todos os blocos =', mx)
    Gl = gab[gx].values[-2000:].astype(np.float64)
    P('  (armadilha) max|dX| contra as 2000 ULTIMAS =',
      float(np.abs(sur[(sur.regime=='sonda')&(sur.geracao==gsond[0])][xc].values.astype(np.float64)-Gl).max()))
P('  x_hash eventos unicos:', set(e.get('x_hash') for e in sondas) == {man['sonda']['x_hash']})

P('#### U6 invariante do timing (DI-13.10)')
v = (tim.tempo_fit_s + tim.tempo_busca_s - tim.tempo_geracao_s)
P('  violacoes fit+busca > geracao (>1e-6):', int((v > 1e-6).sum()), '/', len(tim))
P('  folga mediana s:', float((-v).median()))
v2 = (tim.tempo_fit_s + tim.tempo_busca_s + tim.tempo_pred_sonda_s.fillna(0) - tim.tempo_geracao_s)
P('  violacoes COM sonda:', int((v2 > 1e-6).sum()), ' gerac. logadas com bloco:',
  len([g for g in gsond if g in set(tim.geracao.values)]))
P('  tempo_aval_real_s (I-3):', man['timing'].get('tempo_aval_real_s'))

P('#### U7 fe_treino_max')
ftm = np.array([g['fe_treino_max'] for g in gens])
P('  serie', ftm.tolist(), ' monotonico:', bool((np.diff(ftm) >= 0).all()))
hpn = np.array([g['modelo_hp']['n'] for g in gens])
P('  modelo_hp.n', hpn.tolist(), ' == ftm+1 em', int((hpn == ftm+1).sum()), '/', len(gens))
P('  |(1) com fe_index<=ftm| por ciclo:', [int((real.fe_index<=t).sum()) for t in ftm])

P('#### U8 guards')
from collections import Counter
gs = [e for e in ev if e.get('rec')=='guard']
P('  ', Counter(x.get('name') for x in gs), [(x.get('name'), x.get('fe')) for x in gs])
P('  manifest.cache_hits', man['cache_hits'], 'footer.cache_hits',
  [e for e in ev if e.get('rec')=='footer'][0]['cache_hits'])
ch = [x for x in gs if x.get('name')=='cache_hit']
P('  cache-hit no init (fe <= 11D-1)?', [(x['fe'], x['fe'] <= 11*D-1) for x in ch])
hs = [x for x in gs if x.get('name')=='hard_stop']
P('  hard_stop fe == maxfe:', [(x['fe'], x['fe']==man['maxfe']) for x in hs])

P('#### U9 ledger de FE')
somalote = int(sum(g['lote'] for g in gens))
P('  11D-1 =', 11*D-1, ' Sum lote logado =', somalote, ' cache =', man['cache_hits'])
lote_final = man['fe_final'] - (11*D-1) - somalote + man['cache_hits']
P('  lote_final derivado =', lote_final, ' identidade fecha:',
  (11*D-1) + somalote - man['cache_hits'] + lote_final == man['fe_final'])
P('  lotes:', [g['lote'] for g in gens], ' min', min(g['lote'] for g in gens))
P('  (2) pop: linhas', len(pop), 'grupos geracao', pop.geracao.nunique(),
  'tamanhos', pop.groupby('geracao').size().to_dict())

P('#### U10 erro de fantasia / interpolacao exata')
oc = online[online.real_solution_id.notna()].copy()
oc['rsid'] = oc.real_solution_id.astype(int)
fmap = real.set_index('solution_id')[fc]
oc = oc.join(fmap, on='rsid', rsuffix='_real')
fe_of = real.set_index('solution_id')['fe_index']
oc['fe_of'] = oc.rsid.map(fe_of)
oc['ftm'] = oc.fe_treino_max.astype(float)
err = np.abs(oc[mc].values - oc[fc].values)
oc['err'] = err.max(1)
insample = oc[oc.fe_of <= oc.ftm]
fantasia = oc[oc.fe_of > oc.ftm]
P('  linhas com real_solution_id:', len(oc), ' in-sample:', len(insample), ' fantasia:', len(fantasia))
P('  in-sample |mu-f| max:', float(insample.err.max()) if len(insample) else None,
  ' mediana:', float(insample.err.median()) if len(insample) else None)
if len(fantasia):
    P('  fantasia |mu-f| mediana:', float(fantasia.err.median()), ' max:', float(fantasia.err.max()))
    otim = (fantasia[mc].values < fantasia[fc].values).mean()
    P('  otimismo (mu < f) fracao:', float(otim))

P('#### C1/C2 N por subpopulacao, pool 2N, wmax')
P('  params.N_subpop', man['params']['N_subpop'], ' min(100,11D-1) =', min(100, 11*D-1))
P('  n_sub1/n_sub2/n_pool por ciclo:', set((g['n_sub1'], g['n_sub2'], g['n_pool']) for g in gens))
P('  (3)-online linhas por geracao:', online.groupby('geracao').size().to_dict())
P('  wmax', man['params']['wmax'])

P('#### C3 u=5 revogado, nivel de saida, batch')
P('  lotes >5:', int(sum(1 for g in gens if g['lote']>5)), ' max lote:', max(g['lote'] for g in gens))
P('  niveis de saida:', Counter(g['nivel'] for g in gens))
P('  ramo_QU True:', sum(1 for g in gens if g['ramo_QU']), '/', len(gens))
P('  n_front2 nos ciclos que NAO sao nivel 3:', [(g['geracao'], g['nivel'], g['n_front2']) for g in gens if g['nivel']!=3])
P('  lote>=1 em todos:', all(g['lote']>=1 for g in gens))

P('#### C6 telemetria DI-10')
campos = ['n_por_nivel','modelo_hp','U_pool_max','dist_min_arquivo','f_best','ramo_QU','motivo',
          'fit1','fit2','fit3','Q','U','n_front1','n_front2','fe_treino_max','tempo_geracao_s']
P('  presentes em todos os', len(gens), 'eventos:',
  {c: sum(1 for g in gens if c in g) for c in campos})
P('  n_por_nivel.entrada == 2N:', all(g['n_por_nivel']['entrada']==2*man['params']['N_subpop'] for g in gens))
P('  nivel1==n_front1 e nivel2==n_front2:',
  all(g['n_por_nivel']['nivel1']==g['n_front1'] and g['n_por_nivel']['nivel2']==g['n_front2'] for g in gens))
P('  selecionados == lote:', sum(1 for g in gens if g['n_por_nivel']['selecionados']==g['lote']), '/', len(gens))

P('#### F7 sigma_0 = U de ranks do pool completo (D45)')
s0 = online.sigma_0.values
P('  inteiro em', float(np.mean(np.abs(s0-np.round(s0))<1e-9)*100), '% das', len(online), 'linhas; NaN:', int(np.isnan(s0).sum()))
Nsub = man['params']['N_subpop']
P('  max sigma_0 =', float(np.nanmax(s0)), ' teto teorico 2(2N-1) =', 2*(2*Nsub-1))
P('  U_pool_max do (6):', [g['U_pool_max'] for g in gens], ' max =', max(g['U_pool_max'] for g in gens))
byg = online.groupby('geracao').sigma_0.max().to_dict()
P('  max sigma_0 por geracao:', {int(k): float(v) for k, v in byg.items()})
P('  U_pool_max == max(sigma_0) por ciclo:',
  sum(1 for g in gens if abs(byg.get(g['geracao'], -1) - g['U_pool_max']) < 1e-9), '/', len(gens))
s1 = online.sigma_1.values
P('  sigma_1 NaN:', int(np.isnan(s1).sum()), ' mediana', float(np.nanmedian(s1)), ' max', float(np.nanmax(s1)))
P('  sigma_2 existe na (3)?', 'sigma_2' in online.columns)
P('  espaco_modelo/transf_tipo:', online.espaco_modelo.unique().tolist(), online.transf_tipo.unique().tolist())
P('  pred_tipo/classe/score/confianca:', online.pred_tipo.unique().tolist(),
  online.pred_classe.unique().tolist(), online.pred_score.unique().tolist()[:3],
  online.pred_confianca.unique().tolist()[:3])
P('  modelo_flag:', online.modelo_flag.unique().tolist())

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't03_mecanismo.txt'), 'w').write('\n'.join(out))
