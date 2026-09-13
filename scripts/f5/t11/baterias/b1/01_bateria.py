#!/usr/bin/env python
"""BATERIA T11 · config b1 (ParEGO) · celula main/b1/MMF1/s42 do smoke MATLAB.
READ-ONLY sobre evidencia_T11 e resultados_experimentos. Escreve so aqui.
"""
import json, sys, numpy as np, pandas as pd
from scipy.special import ndtr, erf

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b1'
T11 = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1/exp_main_b1_MMF1_42'
R42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42/exp_main_b1_MMF1_42'
COM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/b1/exp_main_b1_MMF1_42'
SEM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/experiments/main/b1/exp_main_b1_MMF1_42'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/MMF1/doe_MMF1_42.parquet'
SON = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet'

D, M = 2, 2
INIT, MAXFE, CAP = 11 * D - 1, 31 * D - 1, 11 * D - 1 + 25


def carrega(base):
    r = {}
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    r['recs'] = recs
    r['gen'] = [x for x in recs if x['rec'] == 'b1_gen']
    r['guard'] = [x for x in recs if x['rec'] == 'guard']
    r['sonda'] = [x for x in recs if x['rec'] == 'sonda']
    r['header'] = [x for x in recs if x['rec'] == 'header']
    r['footer'] = [x for x in recs if x['rec'] == 'footer']
    r['man'] = json.load(open(base + '.manifest.json'))
    r['real'] = pd.read_parquet(base + '__real.parquet')
    r['pop'] = pd.read_parquet(base + '__pop.parquet')
    r['sur'] = pd.read_parquet(base + '__surrogate.parquet')
    r['tim'] = pd.read_parquet(base + '__timing.parquet')
    return r


P = carrega(T11)
gen, man, real, pop, sur, tim = P['gen'], P['man'], P['real'], P['pop'], P['sur'], P['tim']
G = len(gen)
R = []


def say(k, v):
    R.append((k, v))
    print(f'{k:44s} | {v}')


print('#' * 20, 'U1 orcamento/termino')
say('U1.len(1)==31D-1', f'{len(real)} == {MAXFE} -> {len(real)==MAXFE}')
say('U1.fe_index denso 0-based', str(list(real.fe_index) == list(range(MAXFE))))
say('U1.solution_id unico', f'{real.solution_id.nunique()}/{len(real)}')
say('U1.fase init', f'{(real.fase=="init").sum()} == {INIT}')
say('U1.manifest fe_final==maxfe', f'{man["fe_final"]}=={man["maxfe"]}')
say('U1.footer termino/cp_init/status', f'{P["footer"][0]["termino"]}/{P["footer"][0]["cp_init"]}/{P["footer"][0]["status"]}')
fes = np.array([g['fe'] for g in gen])
say('U1.incrementos de fe entre iters', str(sorted(set(np.diff(fes).tolist()))))
say('U1.n_retries / fallback', f'{man["n_retries"]} / {man["fallback_ativado"]}')

print('#' * 20, 'U2 DoE')
doe = pd.read_parquet(DOE)
xc = [c for c in doe.columns if c.startswith('x')]
A = doe[xc].to_numpy(np.float64)[:INIT].astype(np.float32)
Bx = real[['x0', 'x1']].to_numpy()[:INIT]
say('U2.max|dX| DoE vs artefato (f32)', f'{np.abs(A-Bx).max():.3e}')
sc = json.load(open(DOE.replace('.parquet', '.manifest.json')))
say('U2.doe_hash manifesto == sidecar', f'{man["doe_hash"][:16]} == {str(sc.get("sha256", sc.get("hash","?")))[:16]}')
say('U2.artefato n_linhas', f'{len(doe)}')

print('#' * 20, 'U3 1 fit/iteracao')
say('U3.len(4)==len(fit_series)==n(b1_gen)', f'{len(tim)} / {len(man["fit_series"])} / {G}')
say('U3.geracao sequencial 1..G', str(list(tim.geracao) == list(range(1, G + 1))))
say('U3.tempo_fit_s nao-nulo', f'{(tim.tempo_fit_s>0).sum()}/{len(tim)}')

print('#' * 20, 'U4 cadencia da sonda')
gs = sorted(set(man['sonda']['geracoes']))
esp = sorted(set([1] + [g for g in range(1, G + 1) if g % 2 == 0] + [G]))
say('U4.formula {1}u{pares<=G}u{G}', f'obs={len(gs)} esp={len(esp)} iguais={gs==esp}')
say('U4.eventos sonda no 6 == manifesto', f'{len(P["sonda"])} == {len(gs)}')
sb = sur[sur.regime == 'sonda']
tam = sb.groupby('geracao').size()
say('U4.blocos x 2000 pts', f'{len(tam)} blocos, tamanhos unicos={sorted(set(tam))}')
say('U4.G par? (finalProbe esperado?)', f'G={G} par={G%2==0}')
say('U4.motivos de sonda', str(sorted(set(s.get('motivo', '?') for s in P['sonda']))))
say('U4.regimes na 3', str(sorted(set(sur.regime))))

print('#' * 20, 'U5 NAO-PERTURBACAO (par G-6) *** NOVO T11 ***')
C, S = carrega(COM), carrega(SEM)
rc, rs = C['real'], S['real']
say('U5.linhas 1 com/sem', f'{len(rc)} / {len(rs)}')
eqX = np.array_equal(rc[['x0', 'x1']].to_numpy(), rs[['x0', 'x1']].to_numpy())
eqF = np.array_equal(rc[['f0', 'f1']].to_numpy(), rs[['f0', 'f1']].to_numpy())
eqS = np.array_equal(rc.solution_id.to_numpy(), rs.solution_id.to_numpy())
say('U5.1 X/f/solution_id BIT-IDENTICOS', f'X={eqX} f={eqF} sid={eqS}')
import hashlib
h = lambda df: hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()[:16]
say('U5.sha256(1) com / sem', f'{h(rc)} / {h(rs)}')
say('U5.2 pop identica', str(np.array_equal(C['pop'].to_numpy(), S['pop'].to_numpy())))
say('U5.sonda desligada no SEM', f'{S["man"]["sonda"].get("desligada")} n_blocos={S["man"]["sonda"].get("n_blocos")}')
say('U5.sonda ligada no COM', f'{C["man"]["sonda"].get("desligada")} n_blocos={C["man"]["sonda"].get("n_blocos")}')
say('U5.3 linhas com/sem (encolhe)', f'{len(C["sur"])} / {len(S["sur"])}')
say('U5.3 regimes SEM', str(sorted(set(S['sur'].regime))))
say('U5.n_geracoes/cache com x sem', f'{C["man"]["n_geracoes"]}/{C["man"]["cache_hits"]} x {S["man"]["n_geracoes"]}/{S["man"]["cache_hits"]}')
# COM == smoke principal?
say('U5.COM == smoke principal (1)', str(np.array_equal(rc.to_numpy(), real.to_numpy())))
gc_, gs_ = C['gen'], S['gen']
dif = [i for i in range(min(len(gc_), len(gs_))) if gc_[i]['best_sid'] != gs_[i]['best_sid']]
say('U5.6 best_sid divergentes com x sem', f'{len(dif)} de {min(len(gc_),len(gs_))}')
eib = np.array([g['ei_best'] for g in gc_]) - np.array([g['ei_best'] for g in gs_][:len(gc_)])
say('U5.max|d ei_best| com x sem', f'{np.abs(eib).max():.3e}')

print('#' * 20, 'U7 timing')
d = tim.copy()
say('U7.fit+busca<=geracao (violacoes)', f'{int(((d.tempo_fit_s+d.tempo_busca_s)>d.tempo_geracao_s).sum())}/{len(d)}')
viol = d[(d.tempo_fit_s + d.tempo_busca_s + d.tempo_pred_sonda_s) > d.tempo_geracao_s].geracao.tolist()
say('U7.viola quando soma sonda', f'{len(viol)} geracoes; subset das de sonda={set(viol)<=set(gs)}')
say('U7.conjunto sonda == conjunto violacao', str(sorted(viol) == gs))
say('U7.4 tempo_pred_sonda>0 apenas em sonda', f'{sorted(d[d.tempo_pred_sonda_s>0].geracao.tolist())==gs}')

print('#' * 20, 'U8 fe_treino_max')
ftm = np.array([g['fe_treino_max'] for g in gen])
say('U8.nao-monotonico? quedas', f'{int((np.diff(ftm)<0).sum())} quedas; monot={bool((np.diff(ftm)>=0).all())}')
say('U8.faixa fe_treino_max', f'{ftm.min()}..{ftm.max()}')

print('#' * 20, 'U9 guards + ledger')
from collections import Counter
gt = Counter(g.get('tipo', g.get('guard', '?')) for g in P['guard'])
say('U9.tipos de guard', str(dict(gt)))
ch = [g for g in P['guard'] if 'cache' in str(g.get('tipo', ''))]
say('U9.cache_hit 6 == manifesto == footer', f'{len(ch)} == {man["cache_hits"]} == {P["footer"][0]["cache_hits"]}')
n_inf = MAXFE - INIT
say('U9.ledger n_iter = n_infills+cache-c0', f'{G} == {n_inf}+{man["cache_hits"]}-1 = {n_inf+man["cache_hits"]-1}')
say('U9.c0: guards cache com fe==1', f'{sum(1 for g in ch if g.get("fe")==1)}')
say('U9.dedup_treino eventos', f'{sum(1 for g in P["guard"] if "dedup" in str(g.get("tipo","")))}')

print('#' * 20, 'U10 off-by-one da 2')
say('U10.n geracoes na 2', f'{pop.geracao.nunique()} == n_iter+1 = {G+1}')
sz = pop.groupby('geracao').size()
esp2 = pd.Series({g: INIT + (g - 1) for g in sz.index})
say('U10.|2_g| == 11D-1+(g-1)', str(bool((sz == esp2).all())))
g1 = set(pop[pop.geracao == 1].solution_id)
say('U10.2-ger1 == ids do DoE', str(g1 == set(real[real.fase == 'init'].solution_id)))
ult = pop[pop.geracao == pop.geracao.max()]
dupl = len(ult) - ult.solution_id.nunique()
say('U10.dup na ultima 2 == cache-1', f'{dupl} == {man["cache_hits"]-1}')
say('U10.manifest n_geracoes x n_iter', f'{man["n_geracoes"]} x {G} (off-by-one esperado)')

print('#' * 20, 'F1 QUERY-JOIA identidade do EI')
mu = np.array([g['mu_best'] for g in gen]); sg = np.array([g['sigma_best'] for g in gen])
gb = np.array([g['gbest'] for g in gen]); ei = np.array([g['ei_best'] for g in gen])
z = (gb - mu) / sg
EI_erfc = (gb - mu) * ndtr(z) + sg * np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
EI_erf = (gb - mu) * 0.5 * (1 + erf(z / np.sqrt(2))) + sg * np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
rel = np.abs(EI_erfc + ei) / np.maximum(np.abs(ei), 1e-300)
rel2 = np.abs(EI_erf + ei) / np.maximum(np.abs(ei), 1e-300)
say('F1.identidade EI (ndtr) rel<1e-6', f'{int((rel<1e-6).sum())}/{G}  max={rel.max():.3e} mediana={np.median(rel):.3e}')
say('F1.identidade EI (erf ingenuo)', f'{int((rel2<1e-6).sum())}/{G}')
say('F1.faixa de z', f'{z.min():.3f} .. {z.max():.3f}')
say('F1.ei_best negativo (PlatEMO min -EI)', f'{int((ei<0).sum())}/{G}')

print('#' * 20, 'F2 cadeia best_sid <-> 1')
bs = np.array([g['best_sid'] for g in gen])
say('F2.best_sid in 1.solution_id', f'{int(np.isin(bs, real.solution_id.values).sum())}/{G}')
sid_por_fe = dict(zip(real.fe_index.values, real.solution_id.values))
ch_fe = {}
for g in ch:
    ch_fe.setdefault(g.get('fe'), []).append(g.get('solution_id'))
ok_new = ok_cache = n_new = n_cache = 0
for i, g in enumerate(gen):
    fe = g['fe']
    prev = gen[i - 1]['fe'] if i else INIT
    if fe > prev:          # abriu linha nova
        n_new += 1
        ok_new += int(sid_por_fe.get(fe - 1) == g['best_sid'])
    else:
        n_cache += 1
        cand = ch_fe.get(fe, [])
        ok_cache += int(g['best_sid'] in cand)
say('F2.ramo infill novo', f'{ok_new}/{n_new}')
say('F2.ramo cache-hit', f'{ok_cache}/{n_cache}')

print('#' * 20, 'F4 3 = pop FINAL do GA + rastreio elitista')
on = sur[sur.regime == 'online']
rpg = on.groupby('geracao').size()
gp = pd.Series({g['geracao']: g['ga_pop'] for g in gen})
npg = pd.Series({g['geracao']: g['n_pool_ga'] for g in gen})
say('F4.linhas 3-online == ga_pop == n_pool_ga', f'{bool((rpg==gp).all())} / {bool((gp==npg).all())}')
e0min = np.array([min(g['e0_trace']) for g in gen])
say('F4.ei_best == min(e0_trace)', f'{int((np.abs(e0min-ei)<1e-12).sum())}/{G}')
mono = [bool(np.all(np.diff(g['e0_trace']) <= 1e-15)) for g in gen]
say('F4.e0_trace monotonico (nao-cresc)', f'{sum(mono)}/{G}')
last_eq = np.array([abs(g['e0_trace'][-1] - g['ei_best']) < 1e-12 for g in gen])
say('F4.ei_best == ultimo(e0_trace)', f'{int(last_eq.sum())}/{G}')
const = np.array([len(set(g['e0_trace'])) == 1 for g in gen])
say('F4/ERRATA16.e0_trace CONSTANTE', f'{int(const.sum())}/{G} = {const.mean():.1%}')
venceu1 = np.array([abs(g['e0_trace'][0] - g['ei_best']) < 1e-15 for g in gen])
say('F4/ERRATA16.1a geracao interna venceu', f'{int(venceu1.sum())}/{G} = {venceu1.mean():.1%}')
say('F4/ERRATA16.venceu1 E constante', f'{int((venceu1&const).sum())} de {int(venceu1.sum())}')
say('F4.len(e0_trace) == ga_iters', f'{sum(1 for g in gen if len(g["e0_trace"])==g["ga_iters"])}/{G}')

print('#' * 20, 'B1 lambda')
lam = np.array([g['lambda'] for g in gen])
say('B1.dim lambda == M', f'{lam.shape}')
say('B1.soma lambda == 1 (max desvio)', f'{np.abs(lam.sum(1)-1).max():.3e}')
say('B1.lambda*99 inteiro (max desvio)', f'{np.abs(lam*99-np.round(lam*99)).max():.3e}')
uni = set(map(tuple, np.round(lam * 99).astype(int)))
say('B1.lambda distintos / N_lambda', f'{len(uni)} de {man["params"]["N_lambda"]}')
cc = Counter(map(tuple, np.round(lam * 99).astype(int)))
say('B1.max repeticoes (com reposicao?)', f'{max(cc.values())}')
say('B1.N_lambda no header/params', f'{P["header"][0]["N_lambda"]} / {man["params"]["N_lambda"]}')

print('#' * 20, 'B2/B3 PCheby + normalizacao')
rho = man['params']['rho']
fcols = ['f0', 'f1']
F = real[fcols].to_numpy(np.float64)
ok_gb = ok_nm = 0; err_gb = []; err_nm = []
janela = []
for i, g in enumerate(gen):
    fe = g['fe']
    for w in (fe - 1, fe):     # regra do cache-hit (armadilha 3 da F5)
        Fa = F[:w]
        nmin, nmax = Fa.min(0), Fa.max(0)
        if np.allclose(nmin, g['norm_min'], rtol=1e-4, atol=1e-9) and np.allclose(nmax, g['norm_max'], rtol=1e-4, atol=1e-9):
            ok_nm += 1; janela.append(w - fe); break
    else:
        err_nm.append(g['geracao'])
    lamv = np.array(g['lambda'])
    Fa = F[:w]
    nmin, nmax = np.array(g['norm_min']), np.array(g['norm_max'])
    rng = np.where(nmax - nmin == 0, 1.0, nmax - nmin)
    Fn = (Fa - nmin) / rng
    pc = (Fn * lamv).max(1) + rho * (Fn * lamv).sum(1)
    e = abs(pc.min() - g['gbest'])
    err_gb.append(e); ok_gb += int(e < 1e-6)
say('B3.norm_min/max == min/max arquivo', f'{ok_nm}/{G}; janelas fe-1={janela.count(-1)} fe={janela.count(0)}')
say('B2.gbest == min PCheby (abs<1e-6)', f'{ok_gb}/{G}  max|d|={max(err_gb):.3e}')
relg = [e / max(abs(g['gbest']), 1e-300) for e, g in zip(err_gb, gen)]
say('B2.criterio RELATIVO 1e-6 (armadilha)', f'{sum(1 for r in relg if r<1e-6)}/{G}')

print('#' * 20, 'B5 subset + dedup')
ns = np.array([g['n_subset'] for g in gen]); nt = np.array([g['n_treino'] for g in gen])
nd = np.array([g['n_dedup'] for g in gen]); na = np.array([g['n_arquivo'] for g in gen])
say('B5.n_treino == n_subset - n_dedup', f'{int((nt==ns-nd).sum())}/{G}')
say('B5.n_subset == min(n_arquivo, cap)', f'{int((ns==np.minimum(na,CAP)).sum())}/{G} (cap={CAP})')
say('B5.satura no cap (iters)', f'{int((ns==CAP).sum())}/{G}')
say('B5.n_dedup total / max', f'{nd.sum()} / {nd.max()}')
say('B5.n_treino min..max', f'{nt.min()}..{nt.max()}')
say('B5.n_acumulado(4) == n_treino(6)', f'{int((tim.n_acumulado.values==nt).sum())}/{G}')

print('#' * 20, 'B6 guardas P2/P4')
say('B6.sigma_0 < 0', f'{int((sur.sigma_0<0).sum())} de {len(sur)}')
say('B6.sigma_0 NaN / mu_0 NaN', f'{int(sur.sigma_0.isna().sum())} / {int(sur.mu_0.isna().sum())}')
say('B6.sigma_0 == 0 exato', f'{int((sur.sigma_0==0).sum())}; min={sur.sigma_0.min():.3e}')
say('B6.n_mse_neg/n_ei_nan/nan_guard', f'{sum(g["n_mse_neg"] for g in gen)}/{sum(g["n_ei_nan"] for g in gen)}/{sum(bool(g["nan_guard"]) for g in gen)}')

print('#' * 20, 'B7 GA interno')
gi = np.array([g['ga_iters'] for g in gen]); gpv = np.array([g['ga_pop'] for g in gen])
say('B7.ga_iters == ceil(IFEs/ga_pop)', f'{int((gi==np.ceil(10000/gpv)).sum())}/{G}')
say('B7.ga_pop - 2*n_arquivo', f'{sorted(set((gpv-2*na).tolist()))}')
say('B7.ga_iters faixa / ga_pop faixa', f'{gi.min()}..{gi.max()} / {gpv.min()}..{gpv.max()}')
say('B7.IFEs no header', f'{P["header"][0]["IFEs"]}')

print('#' * 20, 'B8 theta')
th = np.concatenate([np.array(g['modelo_hp']['theta']) for g in gen])
say('B8.componentes de theta', f'{len(th)}')
say('B8.violacoes dos bounds [1e-5,20]', f'{int(((th<1e-5)|(th>20)).sum())}')
say('B8.saturados em 20 / em 1e-5', f'{int((th==20).sum())} / {int((th==1e-5).sum())}')
say('B8.theta min/mediana/max', f'{th.min():.4g} / {np.median(th):.4g} / {th.max():.4g}')
say('B8.regr/corr unicos', str(sorted(set((g['modelo_hp']['regr'], g['modelo_hp']['corr']) for g in gen))))
say('B8.modelo_hp completo em', f'{sum(1 for g in gen if set(g["modelo_hp"])>={"theta","n","sigma2","regr","corr"})}/{G}')

print('#' * 20, 'B11 cache-hit / dist_min')
dm = np.array([g['dist_min_arquivo'] for g in gen])
is_ch = np.array([gen[i]['fe'] == (gen[i - 1]['fe'] if i else INIT) for i in range(G)])
say('B11.dist_min==0 <=> cache-hit', f'{int((dm==0).sum())} zeros; iters cache={int(is_ch.sum())}; casam={bool(((dm==0)==is_ch).all())}')
say('B11.dist_min>0: P5/mediana/P95', f'{np.percentile(dm[dm>0],5):.3e} / {np.median(dm[dm>0]):.4g} / {np.percentile(dm[dm>0],95):.4g}')
st = mx = 0
for v in is_ch:
    st = st + 1 if v else 0; mx = max(mx, st)
say('B11.streak maximo de cache', f'{mx}')

print('#' * 20, 'B12 n_arquivo')
say('B12.n_arquivo == 11D-1+(g-1)', f'{int((na==INIT+np.arange(G)).sum())}/{G}')

print('#' * 20, 'B13 duplicatas float32 na 1')
kb = [r.tobytes() for r in real[['x0', 'x1']].to_numpy()]
cnt = Counter(kb)
dup = sum(v - 1 for v in cnt.values() if v > 1)
say('B13.X duplicados em float32', f'{dup}')
if dup:
    for k, v in cnt.items():
        if v > 1:
            idx = [i for i, b in enumerate(kb) if b == k]
            df = real.iloc[idx]
            say('B13.par dup: sid / |df|', f'{list(df.solution_id)} / {np.abs(np.diff(df[fcols].to_numpy(np.float64),axis=0)).max():.3e}')

print('#' * 20, 'B4 mono-output / literais da 3')
say('B4.mu_1 / sigma_1 NULL', f'{int(sur.mu_1.isna().sum())}/{len(sur)} e {int(sur.sigma_1.isna().sum())}/{len(sur)}')
for c in ['pred_tipo', 'modelo_flag', 'espaco_modelo', 'transf_tipo']:
    say(f'B4.literal {c}', str(sorted(set(sur[c].dropna()))))
for c in ['pred_classe', 'pred_score', 'pred_confianca']:
    say(f'B4.{c} NULL', f'{int(sur[c].isna().sum())}/{len(sur)}')
say('B4.sigma_dict presente', str(sorted(man['sigma_dict'].keys())))
say('B4.transf_params exemplo', str(sur.transf_params.iloc[0])[:200])

print('#' * 20, 'U11 erro de fantasia escalar')
sid2f = dict(zip(real.solution_id.values, F))
err = []; otim = []; dentro = []; melhora = 0
for i, g in enumerate(gen):
    f = sid2f[g['best_sid']]
    lamv = np.array(g['lambda']); nmin = np.array(g['norm_min']); nmax = np.array(g['norm_max'])
    rng = np.where(nmax - nmin == 0, 1.0, nmax - nmin)
    fn = (f - nmin) / rng
    pc = (fn * lamv).max() + rho * (fn * lamv).sum()
    err.append(g['mu_best'] - pc); otim.append(g['mu_best'] < pc)
    dentro.append(abs(g['mu_best'] - pc) <= 1.96 * g['sigma_best'])
    melhora += int(pc < g['gbest'])
err = np.array(err)
say('U11.|erro| mediano / max', f'{np.median(np.abs(err)):.4g} / {np.abs(err).max():.4g}')
say('U11.fracao otimista', f'{np.mean(otim):.3f}')
say('U11.dentro de 1.96 sigma (in-sample)', f'{np.mean(dentro):.3f}')
say('U11.infill melhora o incumbente', f'{melhora}/{G} = {melhora/G:.3f}')

print('#' * 20, 'F6 warm-theta / custo do fit')
tf = tim.tempo_fit_s.values
say('F6.1o fit / mediana', f'{tf[0]:.4g} / {np.median(tf):.4g} = {tf[0]/np.median(tf):.2f}x')
say('F6.fracao do tempo em fit', f'{tf.sum()/tim.tempo_geracao_s.sum():.3f}')
say('F6.tempo_total(5)', f'{man["timing"]["tempo_total_s"]:.2f}s; aval_real={man["timing"]["tempo_aval_real_s"]:.4g}s')
say('F6.I-3 tempo_aval_real_s > 0', str(man['timing']['tempo_aval_real_s'] > 0))

json.dump([{'k': k, 'v': v} for k, v in R], open(f'{OUT}/b1_bateria.json', 'w'), indent=1)
print('\nSALVO', f'{OUT}/b1_bateria.json', len(R), 'medidas')
