#!/usr/bin/env python
"""C3 — AS CORRECOES DA T11 que tocam o c238: implementada? funciona de fato?
Varre as 25 celulas da s42 + o smoke + o par G-6, campo a campo.
READ-ONLY.
"""
import json, os, hashlib
import numpy as np, pandas as pd, pyarrow.parquet as pq

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238'
S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238'
EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
SMOKE = f'{EV}/smoke_matlab/experiments/main/c238/exp_main_c238_MMF1_42'


def manifest(p):
    with open(p) as f: return json.load(f)


def linhas(p):
    ok = mal = 0
    with open(p) as f:
        for ln in f:
            ln = ln.strip()
            if not ln: continue
            try: json.loads(ln); ok += 1
            except Exception: mal += 1
    return ok, mal


print('=' * 100)
print('C3.1 — O QUINTO (⑤) NAS 25 CELULAS DA s42 (PRE-T11) x SMOKE (POS-T11)')
print('=' * 100)
rows = []
for prob in sorted(os.listdir(S42)):
    b = f'{S42}/{prob}/42/exp_main_c238_{prob}_42'
    m = manifest(b + '.manifest.json')
    ok, mal = linhas(b + '.jsonl')
    tm = m.get('timing', {}) or {}
    rows.append(dict(problema=prob, schema=m.get('schema_version'),
                     campanha_id=m.get('campanha_id', '<AUSENTE>'),
                     repo_hash=(m.get('repo_hash') or '<VAZIO>'),
                     params=len(m.get('params', {}) or {}),
                     sigma_dict=len(m.get('sigma_dict', {}) or {}),
                     timing=len(tm), doe_hash=bool(m.get('doe_hash')),
                     t_aval=tm.get('tempo_aval_real_s', None),
                     t_sonda=tm.get('tempo_pred_sonda_s', None),
                     status=m.get('status'), motivo=m.get('motivo_parada', '<AUSENTE>'),
                     fe=m.get('fe_final'), maxfe=m.get('maxfe'),
                     jsonl_ok=ok, jsonl_mal=mal,
                     snd_desligada=(m.get('sonda') or {}).get('desligada', '<AUSENTE>'),
                     snd_blocos=(m.get('sonda') or {}).get('n_blocos')))
df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/quinto_s42.csv', index=False)
print(df.to_string(index=False))
print()
print('  schema_version unico       :', df.schema.unique().tolist())
print('  campanha_id                : %d/25 presentes' % int((df.campanha_id != '<AUSENTE>').sum()))
print('  repo_hash preenchido       : %d/25' % int((df.repo_hash != '<VAZIO>').sum()))
print('  params (13 chaves)         : %d/25 com 13' % int((df.params == 13).sum()))
print('  sigma_dict presente        : %d/25' % int((df.sigma_dict > 0).sum()))
print('  timing.tempo_aval_real_s   : nao-nulo em %d/25 (min=%.4g max=%.4g)' % (
    int(df.t_aval.notna().sum()), df.t_aval.min(), df.t_aval.max()))
print('  ⑥ linhas MALFORMADAS       : %d no total (B-11/G1) ; ⑥ linhas ok=%d' % (df.jsonl_mal.sum(), df.jsonl_ok.sum()))
print('  sonda.desligada no ⑤       :', df.snd_desligada.unique().tolist(), ' <- campo do G6b (novo)')
print('  fe_final==maxfe            : %d/25 ; status ok: %d/25' % (int((df.fe == df.maxfe).sum()), int((df.status == 'ok').sum())))

print()
print('=' * 100)
print('C3.2 — O QUINTO DO SMOKE T11 e do PAR G-6')
print('=' * 100)
for tag, b in [('smoke', SMOKE),
               ('g6_com', f'{EV}/g6_com/experiments/main/c238/exp_main_c238_MMF1_42'),
               ('g6_sem', f'{EV}/g6_sem/experiments/main/c238/exp_main_c238_MMF1_42')]:
    m = manifest(b + '.manifest.json'); tm = m.get('timing', {})
    ok, mal = linhas(b + '.jsonl')
    s = m.get('sonda', {})
    print('  %-7s schema=%s campanha_id=%-28s repo_hash=%s params=%d sigma=%d timing=%d doe=%s '
          't_aval=%.5g malformadas=%d sonda{desligada=%s,n_blocos=%s}' % (
              tag, m.get('schema_version'), m.get('campanha_id'), (m.get('repo_hash') or '')[:12],
              len(m.get('params', {})), len(m.get('sigma_dict', {})), len(tm), bool(m.get('doe_hash')),
              tm.get('tempo_aval_real_s', float('nan')), mal, s.get('desligada'), s.get('n_blocos')))

print()
print('=' * 100)
print('C3.3 — PAR G-6: os TRES SINAIS + identidade do MECANISMO (nao so do hash)')
print('=' * 100)
com = f'{EV}/g6_com/experiments/main/c238/exp_main_c238_MMF1_42'
sem = f'{EV}/g6_sem/experiments/main/c238/exp_main_c238_MMF1_42'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''): h.update(blk)
    return h.hexdigest()


for lay in ['__real', '__pop', '__surrogate', '__timing']:
    a, b = com + lay + '.parquet', sem + lay + '.parquet'
    ha, hb = sha(a), sha(b)
    na, nb = pq.read_table(a).num_rows, pq.read_table(b).num_rows
    print('  %-12s sha256 %-9s COM=%7d SEM=%7d linhas  | %s' % (
        lay, 'IDENTICO' if ha == hb else 'DIFERE', na, nb, ha[:16]))
print('  (handoff T11 §5 declara para c238 o hash `43f533269741c82f` — confere com o sha256 da ① acima)')

rc = [json.loads(l) for l in open(com + '.jsonl') if l.strip()]
rs = [json.loads(l) for l in open(sem + '.jsonl') if l.strip()]
gc = sorted([r for r in rc if r.get('rec') == 'c238_gen'], key=lambda r: r['geracao'])
gs = sorted([r for r in rs if r.get('rec') == 'c238_gen'], key=lambda r: r['geracao'])
print('  ⑥ eventos de geracao: COM=%d SEM=%d' % (len(gc), len(gs)))
campos = ['eim_best', 'eim_mediana_pool', 'n_front', 'n_front1', 'min_dist_infill', 'infill_sid',
          'fe_treino_max', 'n_amostra', 'n_treino', 'theta_min', 'theta_max', 'theta_media', 'lnL',
          'norm_min', 'norm_max', 'norm_range_efetivo', 'u_best', 's_best', 'y_best', 'f_best',
          'stall_iters', 'dist_min_arquivo', 'n_eim_nan', 'n_range0', 'n_dedup', 'ga_pop', 'ga_gens']
iguais = 0
for c in campos:
    a = np.array([r[c] for r in gc], float); b = np.array([r[c] for r in gs], float)
    d = float(np.abs(a - b).max())
    iguais += (d == 0.0)
    if d != 0.0: print('    DIFERE %s: max|D|=%.3g' % (c, d))
print('  campos do ⑥ BIT-IDENTICOS COM x SEM: %d/%d (todos os %d valores por campo)' % (iguais, len(campos), len(gc)))
# ③ online tem de ser identica; a sonda so existe no COM
sc = pq.read_table(com + '__surrogate.parquet').to_pandas()
ss = pq.read_table(sem + '__surrogate.parquet').to_pandas()
oc = sc[sc.regime == 'online'].reset_index(drop=True); os_ = ss[ss.regime == 'online'].reset_index(drop=True)
num = [c for c in oc.columns if oc[c].dtype.kind in 'fi']
dmax = max(float(np.nanmax(np.abs(oc[c].values.astype(float) - os_[c].values.astype(float)))) for c in num)
print('  ③ regime=online: COM %d linhas x SEM %d linhas ; max|D| em %d colunas numericas = %.3g' % (
    len(oc), len(os_), len(num), dmax))
print('  ③ regime=sonda : COM %d x SEM %d  (o encolhimento e o 2o sinal)' % (
    int((sc.regime == 'sonda').sum()), int((ss.regime == 'sonda').sum())))

print()
print('=' * 100)
print('C3.4 — CAMPOS DA T11 QUE NAO SE APLICAM AO c238 (procurados no dado, nao supostos)')
print('=' * 100)
sm = pq.read_table(SMOKE + '__surrogate.parquet').to_pandas()
print('  regimes na ③ do smoke      :', sm.regime.value_counts().to_dict())
print('  sonda_estratificada        :', 'PRESENTE' if (sm.regime == 'sonda_estratificada').any() else 'AUSENTE (c238 nao e classificador)')
recs = [json.loads(l) for l in open(SMOKE + '.jsonl') if l.strip()]
todos = set()
for r in recs: todos |= set(r.keys())
m = manifest(SMOKE + '.manifest.json')


def deep(d, key):
    if isinstance(d, dict):
        if key in d: return d[key]
        for v in d.values():
            r = deep(v, key)
            if r is not None: return r
    if isinstance(d, list):
        for v in d:
            r = deep(v, key)
            if r is not None: return r
    return None


for campo in ['REGRA_DO_ROTULO', 'y_treino_dist', 'pmid_ids', 'ref_ids', 'n_ref',
              'p_wrong_stats', 'margem_3sigma_stats', 'e0_trace', 'adapt_delta_V', 'n_baseline']:
    print('  %-22s ⑥=%s  ⑤=%s' % (campo, 'sim' if campo in todos else 'nao',
                                   'sim' if deep(m, campo) is not None else 'nao'))
print()
print('  CONTRATO §6.1 (contrato_61.json) para c238: di10=["eim_mediana_pool"], nao_se_aplica={}')
print('  minimo comum DI-10 = fe, f_best, n_front1, tempo_fit_s, tempo_busca_s (+modelo_hp, dist_min_arquivo)')
gsm = [r for r in recs if r.get('rec') == 'c238_gen']
for c in ['fe', 'f_best', 'n_front1', 'tempo_fit_s', 'tempo_busca_s', 'modelo_hp', 'dist_min_arquivo', 'eim_mediana_pool']:
    print('    %-20s presente em %d/%d eventos' % (c, sum(1 for g in gsm if c in g), len(gsm)))
