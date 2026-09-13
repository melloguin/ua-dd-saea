#!/usr/bin/env python
"""Parte 2: guards (nome correto = 'name'), cadeia F2-cache, F3 nao-greedy sobre o pool,
sonda na regua ESCALAR reconstruida, e a comparacao T11 x rodada-42."""
import json, numpy as np, pandas as pd
from collections import Counter
from scipy.special import ndtr

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b1'
T11 = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1/exp_main_b1_MMF1_42'
R42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42/exp_main_b1_MMF1_42'
SON = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet'
D, M, INIT, MAXFE, CAP, RHO = 2, 2, 21, 61, 46, 0.05


def carrega(base):
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    return dict(recs=recs,
                gen=[x for x in recs if x['rec'] == 'b1_gen'],
                guard=[x for x in recs if x['rec'] == 'guard'],
                sondas=[x for x in recs if x['rec'] == 'sonda'],
                man=json.load(open(base + '.manifest.json')),
                real=pd.read_parquet(base + '__real.parquet'),
                pop=pd.read_parquet(base + '__pop.parquet'),
                sur=pd.read_parquet(base + '__surrogate.parquet'),
                tim=pd.read_parquet(base + '__timing.parquet'))


P = carrega(T11); gen, real, sur, man = P['gen'], P['real'], P['sur'], P['man']
G = len(gen); F = real[['f0', 'f1']].to_numpy(np.float64)
R = []
def say(k, v):
    R.append((k, v)); print(f'{k:46s} | {v}')

print('#' * 18, 'U9 guards (chave = name)')
cn = Counter(g['name'] for g in P['guard'])
say('U9.tipos de guard', str(dict(cn)))
ch = [g for g in P['guard'] if g['name'] == 'cache_hit']
say('U9.cache_hit 6 == manifesto == footer', f'{len(ch)} == {man["cache_hits"]} == {[r for r in P["recs"] if r["rec"]=="footer"][0]["cache_hits"]}')
say('N1.c0 = guards cache com fe==1', f'{sum(1 for g in ch if g["fe"]==1)} (sid={[g["solution_id"] for g in ch if g["fe"]==1]})')
ded = [g for g in P['guard'] if g['name'] == 'dedup_treino']
say('U9.dedup_treino eventos / remocoes', f'{len(ded)} / {sum(g["n"] for g in ded)}')
say('U9.dedup por geracao', str({g['geracao']: g['n'] for g in ded}))
say('U9.cache_hit por fe', str(dict(Counter(g['fe'] for g in ch))))

print('#' * 18, 'F2 cadeia best_sid (2 ramos)')
sid_por_fe = dict(zip(real.fe_index.values, real.solution_id.values))
chfe = {}
for g in ch:
    chfe.setdefault(g['fe'], set()).add(g['solution_id'])
ok_new = ok_c = n_new = n_c = 0; falhas = []
for i, g in enumerate(gen):
    fe = g['fe']; prev = gen[i - 1]['fe'] if i else INIT
    if fe > prev:
        n_new += 1; ok = sid_por_fe.get(fe - 1) == g['best_sid']; ok_new += ok
    else:
        n_c += 1; ok = g['best_sid'] in chfe.get(fe, set()); ok_c += ok
    if not ok: falhas.append((g['geracao'], fe, g['best_sid'], sorted(chfe.get(fe, []))))
say('F2.ramo infill novo', f'{ok_new}/{n_new}')
say('F2.ramo cache-hit', f'{ok_c}/{n_c}')
say('F2.falhas', str(falhas[:6]))

print('#' * 18, 'F3 nao-greedy (EI recomputado no pool online)')
on = sur[sur.regime == 'online']
ngreedy = tot = 0; razoes = []; pct_sel = []; pct_gre = []; match = 0; last_eq_l = []
for g in gen:
    blk = on[on.geracao == g['geracao']]
    mu = blk.mu_0.to_numpy(np.float64); sg = blk.sigma_0.to_numpy(np.float64)
    gb = g['gbest']
    with np.errstate(divide='ignore', invalid='ignore'):
        z = (gb - mu) / sg
    ei = (gb - mu) * ndtr(z) + sg * np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
    ei = np.where(sg > 0, ei, 0.0)
    ia = int(np.argmax(ei)); ig = int(np.argmin(mu))
    m = (abs(mu[ia] - g['mu_best']) <= 1e-6 * max(1, abs(g['mu_best']))) and (abs(sg[ia] - g['sigma_best']) <= 1e-6 * max(1, abs(g['sigma_best'])))
    match += m
    le = abs(g['e0_trace'][-1] - g['ei_best']) < 1e-12
    last_eq_l.append((le, m))
    if m:
        tot += 1
        if ia != ig:
            ngreedy += 1
            razoes.append(sg[ia] / sg[ig] if sg[ig] > 0 else np.nan)
            pct_sel.append((sg < sg[ia]).mean()); pct_gre.append((sg < sg[ig]).mean())
say('F3.argmax-EI do pool reproduz (mu,sigma)', f'{match}/{G} = {match/G:.3f}')
say('F3.nao-greedy / pool-consistentes', f'{ngreedy}/{tot} = {ngreedy/max(tot,1):.3f}')
say('F3.sigma_sel > sigma_greedy em', f'{sum(1 for r in razoes if r>1)}/{len(razoes)}')
say('F3.razao sigma_sel/sigma_greedy med/max', f'{np.median(razoes):.3f} / {np.max(razoes):.3f}' if razoes else 'n/a')
say('F3.percentil-sigma escolhido x guloso', f'{np.mean(pct_sel):.3f} x {np.mean(pct_gre):.3f}' if pct_sel else 'n/a')
ct = Counter(last_eq_l)
say('F3/F4.crosstab (last_eq, match)', str(dict(ct)))

print('#' * 18, 'SONDA — regua ESCALAR reconstruida (regra 4 do R4)')
son = pd.read_parquet(SON)
print('  artefato sonda:', son.shape, list(son.columns))
son = son.iloc[:2000]          # regra R4#10: online = linhas 0..1999 do artefato
xg = son[[c for c in son.columns if c.startswith('x')]].to_numpy(np.float64)
fg = son[[c for c in son.columns if c.startswith('f')]].to_numpy(np.float64)
sb = sur[sur.regime == 'sonda']
linhas = []
for gg, blk in sb.groupby('geracao'):
    blk = blk.reset_index(drop=True)
    dX = np.abs(blk[['x0', 'x1']].to_numpy() - xg.astype(np.float32)).max()
    tp = json.loads(blk.transf_params.iloc[0])
    lam = np.array(tp['lambda']); nmin = np.array(tp['min']); nmax = np.array(tp['max'])
    rng = np.where(nmax - nmin == 0, 1.0, nmax - nmin)
    Fn = (fg - nmin) / rng
    pc = (Fn * lam).max(1) + RHO * (Fn * lam).sum(1)
    mu = blk.mu_0.to_numpy(np.float64); sg = blk.sigma_0.to_numpy(np.float64)
    wape = np.abs(mu - pc).sum() / np.abs(pc).sum()
    cob = (np.abs(mu - pc) <= 1.96 * sg).mean()
    corr = np.corrcoef(mu, pc)[0, 1]
    linhas.append(dict(geracao=int(gg), n=len(blk), maxdX=dX, wape=wape, cob=cob, corr=corr,
                       sigma_med=float(np.median(sg)), gbest=tp['gbest'],
                       fe_treino_max=int(blk.fe_treino_max.iloc[0])))
S = pd.DataFrame(linhas).sort_values('geracao')
S.to_csv(f'{OUT}/b1_sonda_blocos.csv', index=False)
say('U5.join posicional max|dX| (todos blocos)', f'{S.maxdX.max():.3e}')
say('U6.WAPE 1o -> ultimo bloco', f'{S.wape.iloc[0]:.4f} -> {S.wape.iloc[-1]:.4f} ({(S.wape.iloc[-1]/S.wape.iloc[0]-1)*100:+.1f}%)')
say('U6.WAPE min/mediana/max', f'{S.wape.min():.4f} / {S.wape.median():.4f} / {S.wape.max():.4f}')
say('F5.cobertura 2sigma 1o -> ultimo', f'{S.cob.iloc[0]:.4f} -> {S.cob.iloc[-1]:.4f}')
say('F5.cobertura min por bloco', f'{S.cob.min():.4f} (g={int(S.loc[S.cob.idxmin(),"geracao"])})')
say('F5.blocos com cobertura < 0.95', f'{int((S.cob<0.95).sum())}/{len(S)}')
say('F5.sigma mediano 1o -> ultimo', f'{S.sigma_med.iloc[0]:.4g} -> {S.sigma_med.iloc[-1]:.4g}')
c0=float(S["corr"].iloc[0]); c1=float(S["corr"].iloc[-1])
say('SONDA.corr 1o -> ultimo', f'{c0:.4f} -> {c1:.4f}')
say('SONDA.blocos / pontos', f'{len(S)} / {int(S.n.sum())}')
say('SONDA.x_hash manifesto == artefato', f'{man["sonda"]["x_hash"][:16]} == (evento) {P["sondas"][0]["x_hash"][:16]}')
say('SONDA.sonda_estratificada presente?', str('sonda_estratificada' in set(sur.regime)))

print('#' * 18, 'T11 x rodada-42 (MESMA celula, MESMA semente)')
Q = carrega(R42); gq, rq = Q['gen'], Q['real']
say('CMP.doe_hash T11 == R42', str(man['doe_hash'] == Q['man']['doe_hash']))
say('CMP.repo_hash T11 / R42', f'{man.get("repo_hash","?")[:12]} / {Q["man"].get("repo_hash","(ausente)")}')
say('CMP.matlab T11 / R42', f'{man["env"].get("matlab")} / {Q["man"]["env"].get("matlab")}')
say('CMP.n_iter T11 / R42', f'{len(gen)} / {len(gq)}')
say('CMP.cache_hits T11 / R42', f'{man["cache_hits"]} / {Q["man"]["cache_hits"]}')
Xa = real[['x0', 'x1']].to_numpy(); Xb = rq[['x0', 'x1']].to_numpy()
say('CMP.1 DoE (21 linhas) identico', str(np.array_equal(Xa[:INIT], Xb[:INIT])))
dif = np.where(np.any(Xa != Xb, axis=1))[0]
say('CMP.1a linha da 1 que difere (fe_index)', f'{dif[0] if len(dif) else "nenhuma"} de {MAXFE}')
say('CMP.linhas da 1 identicas', f'{MAXFE-len(dif)}/{MAXFE}')
say('CMP.lambda g1 T11 / R42', f'{gen[0]["lambda"]} / {gq[0]["lambda"]}')
neq = [g for g in range(min(len(gen), len(gq))) if gen[g]['lambda'] != gq[g]['lambda']]
say('CMP.1a geracao com lambda diferente', f'{neq[0]+1 if neq else "nenhuma"}')
for k in ['gbest', 'mu_best', 'sigma_best', 'ei_best']:
    a = np.array([g[k] for g in gen[:min(len(gen), len(gq))]]); b = np.array([g[k] for g in gq[:len(a)]])
    d = np.where(np.abs(a - b) > 0)[0]
    say(f'CMP.1a geracao com {k} diferente', f'{d[0]+1 if len(d) else "nenhuma"}  (max|d| ate la = {np.abs(a[:d[0]]-b[:d[0]]).max() if len(d) and d[0]>0 else 0:.3e})')
th_a = np.array(gen[0]['modelo_hp']['theta']); th_b = np.array(gq[0]['modelo_hp']['theta'])
say('CMP.theta g1 T11 / R42', f'{th_a} / {th_b}  |d|={np.abs(th_a-th_b).max():.3e}')
say('CMP.gbest g1 T11 / R42', f'{gen[0]["gbest"]:.17g} / {gq[0]["gbest"]:.17g}')
say('CMP.mu_best g1', f'{gen[0]["mu_best"]:.17g} / {gq[0]["mu_best"]:.17g}')
say('CMP.e0_trace[0] g1', f'{gen[0]["e0_trace"][0]:.17g} / {gq[0]["e0_trace"][0]:.17g}')
say('CMP.best_sid g1', f'{gen[0]["best_sid"]} / {gq[0]["best_sid"]}')
say('CMP.tempo_total T11 / R42', f'{man["timing"]["tempo_total_s"]:.2f}s / {Q["man"]["timing"]["tempo_total_s"]:.2f}s')
say('CMP.tempo_aval_real T11 / R42', f'{man["timing"].get("tempo_aval_real_s")} / {Q["man"]["timing"].get("tempo_aval_real_s","AUSENTE")}')
say('CMP.campanha_id T11 / R42', f'{man.get("campanha_id","-")} / {Q["man"].get("campanha_id","AUSENTE")}')
say('CMP.schema_version T11 / R42', f'{man.get("schema_version")} / {Q["man"].get("schema_version","AUSENTE")}')
say('CMP.chaves novas no manifesto T11', str(sorted(set(man) - set(Q['man']))))
say('CMP.chaves perdidas', str(sorted(set(Q['man']) - set(man))))
say('CMP.chaves novas em timing(5)', str(sorted(set(man['timing']) - set(Q['man']['timing']))))

json.dump([{'k': k, 'v': v} for k, v in R], open(f'{OUT}/b1_parte2.json', 'w'), indent=1)
print('\nSALVO', f'{OUT}/b1_parte2.json')
