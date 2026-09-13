#!/usr/bin/env python3
# f6_qualidade_surrogate.py — 4 graficos de QUALIDADE DO SURROGATE ao longo das
# iteracoes, na regua comum da sonda: 2 REGRESSORES (c262 GP-BO, e7 NN-dropout) e
# 2 CLASSIFICADORES (b4 FNN bom/ruim, c217 PNN par-a-par).
#
# Regressor: WAPE + correlacao + cobertura +-1,96sigma por bloco (mu x f real dos
#   MESMOS 2000 pontos Sobol; des-transformado via transf_params).
# Classificador: precisa do ROTULO VERDADEIRO por construcao. Para o b4 ele e
#   derivavel (o jsonl loga `ref_ids`, as 6 referencias radiais da geracao) =>
#   AUC/acuracia reais. Para o c217 NAO e derivavel dos logs (so `n_Pmid`, o
#   TAMANHO, nunca a identidade de Pmid) => so se pode medir a DISTRIBUICAO do
#   score ternario e a concordancia com um proxy (o f real). Este script mede o
#   que EXISTE e deixa a lacuna explicita no grafico.
import json, os, sys, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
sys.path.insert(0, REPO)
os.chdir(REPO)
import pyarrow.parquet as pq

OUT = os.path.join(REPO, 'f5', 'figuras')
os.makedirs(OUT, exist_ok=True)


def sonda_gabarito(prob):
    t = pq.read_table('data/sonda/sonda_%s.parquet' % prob)
    fc = sorted([c for c in t.column_names if c[0] == 'f' and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    xc = sorted([c for c in t.column_names if c[0] == 'x' and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    return (np.column_stack([np.asarray(t.column(c), float) for c in xc]),
            np.column_stack([np.asarray(t.column(c), float) for c in fc]))


def le_sonda(cfg, label, prob):
    p = glob.glob('%s/%s/%s/42/*__surrogate.parquet' % (RES, cfg, label))[0]
    return pq.read_table(p, filters=[('regime', '=', 'sonda')]).to_pandas()


def destransf(mu, tipo, params):
    if not tipo or tipo in ('cru', 'None'):
        return mu
    p = json.loads(params) if isinstance(params, str) else (params or {})
    if tipo == 'translacao':
        return mu + np.asarray(p['ymin'], float)
    if tipo in ('zscore', 'z'):
        return mu * np.asarray(p['std'], float) + np.asarray(p['mean'], float)
    if tipo == 'minmax':
        return mu * np.asarray(p.get('range', p.get('max')), float) + np.asarray(p['min'], float)
    return mu


# ══ REGRESSORES ═════════════════════════════════════════════════════════════
def fig_regressor(cfg, prob, titulo, arq):
    df = le_sonda(cfg, prob, prob)
    _, Fg = sonda_gabarito(prob)
    M = Fg.shape[1]
    gens, wape, corr, cob = [], [], [], []
    for g, sub in df.groupby(df['geracao'].astype(float)):
        sub = sub.sort_index()
        n = len(sub)
        if n != 2000:
            continue
        tipo = sub['transf_tipo'].dropna().iloc[0] if sub['transf_tipo'].notna().any() else None
        par = sub['transf_params'].dropna().iloc[0] if sub['transf_params'].notna().any() else None
        mu = np.column_stack([sub['mu_%d' % j].to_numpy(float) for j in range(M)])
        mu = destransf(mu, tipo, par)
        sg = None
        if all('sigma_%d' % j in sub.columns for j in range(M)):
            sg = np.column_stack([sub['sigma_%d' % j].to_numpy(float) for j in range(M)])
            if tipo in ('zscore', 'z') and par:
                sg = sg * np.asarray(json.loads(par)['std'] if isinstance(par, str) else par['std'], float)
        F = Fg[:n]
        ok = np.isfinite(mu).all(1)
        w = np.abs(mu[ok] - F[ok]).sum() / max(np.abs(F[ok]).sum(), 1e-12)
        c = np.mean([np.corrcoef(mu[ok, j], F[ok, j])[0, 1] for j in range(M)
                     if np.std(mu[ok, j]) > 0] or [np.nan])
        cv = np.nan
        if sg is not None:
            ok2 = ok & np.isfinite(sg).all(1)
            if ok2.sum() > 10:
                cv = np.mean((np.abs(mu[ok2] - F[ok2]) <= 1.96 * sg[ok2]))
        gens.append(int(g)); wape.append(w); corr.append(c); cob.append(cv)

    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    ax[0].plot(gens, wape, '-o', ms=3, color='#c0392b')
    ax[0].set_title('WAPE (erro global)'); ax[0].set_xlabel('geração'); ax[0].set_yscale('log')
    ax[1].plot(gens, corr, '-o', ms=3, color='#2980b9'); ax[1].set_ylim(-1.05, 1.05)
    ax[1].axhline(0, color='#999', lw=.6)
    ax[1].set_title('correlação μ × f real'); ax[1].set_xlabel('geração')
    if np.isfinite(cob).any():
        ax[2].plot(gens, cob, '-o', ms=3, color='#27ae60')
        ax[2].axhline(0.95, color='#999', ls='--', lw=.8)
        ax[2].set_ylim(0, 1.05); ax[2].set_title('cobertura ±1,96σ (nominal 0,95)')
    else:
        ax[2].text(.5, .5, 'σ não exportado\n(modelo sem incerteza)', ha='center', va='center')
        ax[2].set_title('calibração')
    ax[2].set_xlabel('geração')
    for a in ax:
        a.grid(alpha=.25)
    fig.suptitle(titulo, fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, arq), dpi=130, bbox_inches='tight')
    plt.close(fig)
    print('%-28s blocos=%3d  WAPE %.4f -> %.4f   corr %.3f -> %.3f   cob %.3f -> %.3f'
          % (cfg + '/' + prob, len(gens), wape[0], wape[-1], corr[0], corr[-1],
             cob[0] if np.isfinite(cob[0]) else float('nan'),
             cob[-1] if np.isfinite(cob[-1]) else float('nan')))
    return gens, wape


# ══ CLASSIFICADOR b4 — rotulo VERDADEIRO derivavel (ref_ids no jsonl) ═══════
def fig_b4(prob, arq):
    df = le_sonda('b4', prob, prob)
    _, Fg = sonda_gabarito(prob)
    j = glob.glob('%s/b4/%s/42/*.jsonl' % (RES, prob))[0]
    gens_ev = {}
    for l in open(j, errors='ignore'):
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get('rec') == 'b4_gen':
            gens_ev[int(d['geracao'])] = d
    real = pq.read_table(glob.glob('%s/b4/%s/42/*__real.parquet' % (RES, prob))[0]).to_pandas()
    fc = sorted([c for c in real.columns if c[0] == 'f' and c[1:].isdigit()], key=lambda c: int(c[1:]))
    Freal = {int(r.solution_id): np.array([getattr(r, c) for c in fc], float)
             for r in real.itertuples()}

    gens, auc, acc, frac_bom = [], [], [], []
    for g, sub in df.groupby(df['geracao'].astype(float)):
        g = int(g); sub = sub.sort_index()
        if len(sub) != 2000 or g not in gens_ev:
            continue
        refs = gens_ev[g].get('ref_ids') or []
        R = np.array([Freal[i] for i in refs if i in Freal], float)
        if R.shape[0] < 2:
            continue
        F = Fg[:2000]
        # rotulo do paper (DI-18): 1 <=> NAO estritamente pior que TODAS as K refs
        pior_que_todas = np.all((F[:, None, :] > R[None, :, :]).all(axis=2), axis=1)
        y = (~pior_que_todas).astype(int)
        pred = (sub['pred_classe'].to_numpy() == 'bom').astype(int)
        # pred_confianca E P(classe='bom') — corte exatamente em 0,5 (medido:
        # max ruim=0,4999 / min bom=0,5000). O score do AUC e a propria confianca.
        score = sub['pred_confianca'].to_numpy(float)
        gens.append(g); acc.append(float((pred == y).mean())); frac_bom.append(float(y.mean()))
        if 0 < y.mean() < 1:
            o = np.argsort(score); r = np.empty_like(o, float); r[o] = np.arange(len(score))
            n1, n0 = y.sum(), (1 - y).sum()
            auc.append(float((r[y == 1].sum() - n1 * (n1 - 1) / 2) / (n1 * n0)))
        else:
            auc.append(np.nan)

    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    ax[0].plot(gens, auc, '-o', ms=3, color='#8e44ad'); ax[0].axhline(.5, color='#999', ls='--', lw=.8)
    ax[0].set_ylim(0, 1.05); ax[0].set_title('AUC (discriminação real)')
    ax[1].plot(gens, acc, '-o', ms=3, color='#16a085'); ax[1].set_ylim(0, 1.05)
    ax[1].set_title('acurácia vs rótulo verdadeiro')
    ax[2].plot(gens, frac_bom, '-o', ms=3, color='#d35400'); ax[2].set_ylim(0, 1.05)
    ax[2].set_title('prevalência da classe "bom" (dificuldade)')
    for a in ax:
        a.set_xlabel('geração'); a.grid(alpha=.25)
    fig.suptitle('CLASSIFICADOR · b4 (CSEA, FNN bom/ruim) · %s · rótulo VERDADEIRO derivado das '
                 '%d referências radiais logadas (ref_ids)' % (prob, 6), fontsize=10, y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, arq), dpi=130, bbox_inches='tight'); plt.close(fig)
    a = np.array(auc, float)
    print('%-28s blocos=%3d  AUC %.3f -> %.3f (mediana %.3f)  acc mediana %.3f'
          % ('b4/' + prob, len(gens), a[0], a[-1], np.nanmedian(a), np.median(acc)))


# ══ CLASSIFICADOR c217 — rotulo NAO derivavel (so |Pmid| e logado) ══════════
def fig_c217(prob, arq):
    df = le_sonda('c217', prob, prob)
    gens, fp, fz, fn, conf = [], [], [], [], []
    for g, sub in df.groupby(df['geracao'].astype(float)):
        s = sub['pred_score'].to_numpy(float)
        if len(s) != 2000:
            continue
        gens.append(int(g)); fp.append(float((s > 0).mean()))
        fz.append(float((s == 0).mean())); fn.append(float((s < 0).mean()))
        conf.append(float(sub['pred_confianca'].iloc[0]))
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    ax[0].stackplot(gens, fp, fz, fn, labels=['+1 (melhor)', '0 (empate)', '−1 (pior)'],
                    colors=['#27ae60', '#bdc3c7', '#c0392b'], alpha=.85)
    ax[0].legend(fontsize=7, loc='upper right'); ax[0].set_ylim(0, 1)
    ax[0].set_title('distribuição do score ternário')
    ax[1].plot(gens, conf, '-o', ms=3, color='#2c3e50'); ax[1].set_ylim(-.05, 1.05)
    ax[1].axhline(0.8, color='#c0392b', ls='--', lw=.8)
    ax[1].set_title('pred_confianca = Error1 (δ=0,8)')
    ax[2].axis('off')
    ax[2].text(.02, .5,
               'AUC / acurácia: NÃO CALCULÁVEIS\n\n'
               'O score é relativo à referência Pmid da geração.\n'
               'O ⑥ loga apenas |Pmid| (o TAMANHO), nunca a\n'
               'identidade dos pontos de Pmid.\n\n'
               '⇒ o rótulo verdadeiro não é reconstituível.\n'
               'LACUNA DE INSTRUMENTAÇÃO (ver §2 do laudo):\n'
               'basta logar pmid_ids (≤13 int32/geração).\n\n'
               'Compare com o b4, que loga ref_ids e por isso\n'
               'tem AUC real.', fontsize=8.5, va='center', family='monospace')
    for a in ax[:2]:
        a.set_xlabel('geração'); a.grid(alpha=.25)
    fig.suptitle('CLASSIFICADOR · c217 (PC-SAEA, PNN par-a-par) · %s · o que a sonda PERMITE medir hoje'
                 % prob, fontsize=10, y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, arq), dpi=130, bbox_inches='tight'); plt.close(fig)
    print('%-28s blocos=%3d  score==0 em %.1f%% (mediana) — surrogate inativo (δ=0,8)'
          % ('c217/' + prob, len(gens), 100 * np.median(fz)))


if __name__ == '__main__':
    print('=== REGRESSORES ===')
    fig_regressor('c262', 'ZDT1', 'REGRESSOR · c262 (qNEHVI, GP exato + σ) · ZDT1 · sonda 2.000 pts Sobol',
                  'surrogate_regressor_c262_ZDT1.png')
    fig_regressor('e7', 'DTLZ2', 'REGRESSOR · e7 (EDN-ARMOEA, MC-dropout) · DTLZ2 · sonda 2.000 pts Sobol',
                  'surrogate_regressor_e7_DTLZ2.png')
    print('=== CLASSIFICADORES ===')
    fig_b4('ZDT1', 'surrogate_classificador_b4_ZDT1.png')
    fig_c217('ZDT1', 'surrogate_classificador_c217_ZDT1.png')
    print('\nfiguras em', OUT)
