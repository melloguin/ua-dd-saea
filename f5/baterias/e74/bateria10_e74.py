#!/usr/bin/env python
"""BATERIA 10 e74/CLMEA — fechamento: (a) f_best/n_front1 com tolerancia float32;
(b) classe do candidato ESCOLHIDO na s1 (a pre-triagem sobrevive ao desalinhamento?);
(c) a TABELA-CHAVE do DI-07b: regime produtivo (count>0) x regime no-op (count==0);
(d) os 3 slots perdidos FORA do no-op; (e) sonda: sigma/cobertura por desenho;
(f) U8 fe_treino_max por cabeca (semantica do relogio de treino).
Escreve: e74_b10_di07b.csv, e74_b10_cand_classe.csv, e74_b10.txt
"""
import json, os
import pandas as pd, numpy as np

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/e74'
probs = sorted(os.listdir(ROOT))
buf = []


def P(*a):
    s = ' '.join(str(x) for x in a); buf.append(s); print(s, flush=True)


rows, cand, ftm, odd = [], [], [], []
for pr in probs:
    b = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    recs = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r['rec'] == 'header'][0]; D, M = hdr['D'], hdr['M']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    real = pd.read_parquet(b + '__real.parquet')
    sur = pd.read_parquet(b + '__surrogate.parquet')
    so = sur[sur.regime == 'online']; ss = sur[sur.regime == 'sonda']
    fc = [f'f{i}' for i in range(M)]; xc = [f'x{i}' for i in range(D)]
    F = real[fc].to_numpy(np.float64); Xr = real[xc].to_numpy(np.float32)
    blocks = {g: d for g, d in so.groupby('geracao')}

    # (a) f_best relativo
    rel = []
    for ev in gens:
        fbe = np.array(ev['f_best'], float); fbr = F[:ev['arquivo']].min(0)
        rel.append(float((np.abs(fbe - fbr) / np.maximum(np.abs(fbr), 1e-12)).max()))
    # (b) classe do candidato ESCOLHIDO na s1
    for ev in gens:
        if ev['estrategia'] != 1 or ev['aceito'] != 1:
            continue
        blk = blocks.get(ev['geracao'])
        if blk is None:
            continue
        xi = Xr[ev['fe'] - 1]
        Xb = blk[xc].to_numpy(np.float32)
        pos = int(np.argmin(np.abs(Xb - xi).max(1)))
        s0 = blk.sigma_0.to_numpy(float)
        cls = str(blk.pred_classe.iloc[pos])
        cand.append(dict(problema=pr, geracao=ev['geracao'], pos=pos, N=len(blk), classe=cls,
                         cand_classe_ev=ev.get('cand_classe'),
                         eh_nivel1=(cls == 'nivel_1'), sig=float(s0[pos]),
                         sig_max=float(np.nanmax(s0)),
                         rank=int((s0 > s0[pos]).sum() + 1),
                         rank_rel=float(((s0 > s0[pos]).sum() + 1) / len(blk)),
                         count=ev['count'], desal=ev['n_desalinhado'], frac_n1=float(ev['frac_nivel1'])))
    # (c) regimes
    for ev in gens:
        if ev['estrategia'] != 1:
            continue
        rows.append(dict(problema=pr, D=D, M=M, geracao=ev['geracao'], count=ev['count'],
                         regime=('no-op' if ev['count'] == 0 else 'produtivo'),
                         desal=ev['n_desalinhado'], N=None, aceito=ev['aceito'],
                         slot=ev['slot_perdido'], n_cand=ev['n_cand'],
                         flag_copia=bool(ev['flag_copia']), frac_n1=float(ev['frac_nivel1'])))
        if ev['slot_perdido'] == 1 and ev['count'] != 0:
            odd.append(dict(problema=pr, geracao=ev['geracao'], count=ev['count'],
                            desal=ev['n_desalinhado'], flag_copia=ev['flag_copia'],
                            n_cand=ev['n_cand'], cand_dist=ev.get('cand_dist_dec')))
    # (f) U8 por cabeca + sonda sigma
    for mf, bl in ss.groupby('modelo_flag'):
        v = bl.groupby('geracao').fe_treino_max.first().sort_index()
        ftm.append(dict(problema=pr, cabeca=mf, n_blocos=len(v), ftm_min=int(v.min()), ftm_max=int(v.max()),
                        mono=bool((np.diff(v.to_numpy()) >= 0).all()),
                        sig_nan=float(bl.sigma_0.isna().mean()) if 'sigma_0' in bl else np.nan,
                        mu_nan=float(bl.mu_0.isna().mean()),
                        conf_nan=float(bl.pred_confianca.isna().mean()),
                        linhas=len(bl)))
    rows[-1]['fbest_rel_max'] = max(rel)
    print(pr, 'ok', flush=True)

R = pd.DataFrame(rows); R.to_csv(f'{OUT}/e74_b10_di07b.csv', index=False)
CA = pd.DataFrame(cand); CA.to_csv(f'{OUT}/e74_b10_cand_classe.csv', index=False)
FT = pd.DataFrame(ftm)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)

P('#'*100); P('# (a) f_best == min do arquivo POS-FE (erro RELATIVO, ① em float32)'); P('#'*100)
rr = R.dropna(subset=['fbest_rel_max'])
P('  max erro relativo por celula:', {k: float('%.2e' % v) for k, v in zip(rr.problema, rr.fbest_rel_max)})
P('  PIOR global: %.3e' % rr.fbest_rel_max.max(), '| celulas com erro <= 1e-6:', int((rr.fbest_rel_max <= 1e-6).sum()), '/25')

P(''); P('#'*100); P('# (b) O CANDIDATO ESCOLHIDO NA s1 — a pre-triagem sobrevive?'); P('#'*100)
P('  infills s1 analisados:', len(CA))
P('  candidato escolhido tem pred_classe == nivel_1:', int(CA.eh_nivel1.sum()), '/', len(CA),
  '= %.2f%%' % (100 * CA.eh_nivel1.mean()))
P('  cand_classe do EVENTO == 1:', int((CA.cand_classe_ev == 1).sum()), '/', len(CA))
P('  concordancia evento x ③ (cand_classe_ev == classe do bloco):',
  int((CA.cand_classe_ev.astype(str) == CA.classe.str.replace('nivel_', '')).sum()), '/', len(CA))
P('  RANK do escolhido na ordem de incerteza (1 = mais incerto):')
P(CA['rank'].describe().round(2).to_string())
P('  rank relativo (rank/N): mediana %.3f | quartis %.3f/%.3f | uniforme esperaria 0,50' % (
    CA.rank_rel.median(), CA.rank_rel.quantile(.25), CA.rank_rel.quantile(.75)))
P('  argmax exato (rank==1):', int((CA['rank'] == 1).sum()), '= %.2f%%' % (100 * (CA['rank'] == 1).mean()))
P('  entre os 10%% mais incertos:', int((CA.rank_rel <= .1).sum()), '= %.2f%%' % (100 * (CA.rank_rel <= .1).mean()))
P('  por problema:')
P(CA.groupby('problema').agg(n=('rank', 'size'), nivel1=('eh_nivel1', 'sum'),
                             rank_med=('rank', 'median'), rank_rel_med=('rank_rel', 'median'),
                             argmax=('rank', lambda s: int((s == 1).sum()))).round(3).to_string())

P(''); P('#'*100); P('# (c) DI-07b — A TABELA-CHAVE: regime PRODUTIVO x NO-OP'); P('#'*100)
g = R.groupby('regime').agg(ciclos=('desal', 'size'), desal_med=('desal', 'mean'), desal_p50=('desal', 'median'),
                            desal_min=('desal', 'min'), desal_max=('desal', 'max'),
                            slots=('slot', 'sum'), aceitos=('aceito', 'sum'),
                            copia=('flag_copia', 'sum'), frac_n1=('frac_n1', 'median'))
g['pct_ciclos'] = (100 * g.ciclos / len(R)).round(2)
P(g.round(3).to_string())
P('  TOTAL ciclos s1 =', len(R), '| no-op =', int((R.regime == 'no-op').sum()),
  '(%.2f%%)' % (100 * (R.regime == 'no-op').mean()))
P('')
t = R.pivot_table(index='problema', columns='regime', values='desal', aggfunc=['size', 'mean', 'max']).fillna(0)
P(t.round(2).to_string())
P('')
P('  distribuicao do n_desalinhado no regime PRODUTIVO (2.123 ciclos):')
P((R[R.regime == 'produtivo'].desal.describe([.1, .25, .5, .75, .9, .95, .99])).round(2).to_string())
P('  distribuicao no regime NO-OP (326 ciclos):')
P((R[R.regime == 'no-op'].desal.describe([.1, .25, .5, .75, .9, .95, .99])).round(2).to_string())

P(''); P('#'*100); P('# (d) SLOTS PERDIDOS FORA DO NO-OP'); P('#'*100)
P(pd.DataFrame(odd).to_string(index=False) if odd else '  (nenhum)')

P(''); P('#'*100); P('# (e)(f) SONDA: sigma/mu/confianca por cabeca + relogio de treino U8'); P('#'*100)
P(FT.groupby('cabeca').agg(celulas=('problema', 'nunique'), blocos=('n_blocos', 'sum'), linhas=('linhas', 'sum'),
                           mono=('mono', 'sum'), sig_nan=('sig_nan', 'mean'), mu_nan=('mu_nan', 'mean'),
                           conf_nan=('conf_nan', 'mean'), ftm_min=('ftm_min', 'min'),
                           ftm_max=('ftm_max', 'max')).round(4).to_string())
P('  celulas com fe_treino_max NAO-monotonico na RBF-local(s3):',
  FT[(FT.cabeca == 'RBF-local(s3)') & (~FT.mono)].problema.tolist())

open(f'{OUT}/e74_b10.txt', 'w').write('\n'.join(buf))
print('\n[ok] e74_b10_*.csv + e74_b10.txt')
