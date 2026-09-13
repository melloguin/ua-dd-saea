#!/usr/bin/env python
"""BATERIA b5m #2 — DINAMICA DO MECANISMO nas 45 celulas (semente 42).

Le a ③ (busca) inteira por celula (pop x n_ger x [X, mu, sigma]) e mede:
  - turnover (fracao de slots que mudaram entre geracoes consecutivas) -> a
    assinatura da regra de substituicao MOEA/D + da rampa theta;
  - duplicatas por geracao (fingerprint de substituicao multi-vizinho);
  - trajetoria de sigma medio da populacao (o "rejeita incerteza");
  - trajetoria de HV/IGD+ no espaco SURROGATE (mu) e no espaco REAL (f
    verdadeiro recomputado em 20 checkpoints) -> a assinatura Fig.10 do paper;
  - LHS da geracao 1 (estratificacao exata) -> B18.9;
  - ⑦: recomputo do ND, link posicional (ger,linha)->③, metricas do endpoint.

Saidas: b5m_mecanismo.csv (1 linha/celula) + b5m_traj_fig10.csv (checkpoints).
"""
import json, glob, os, sys
import numpy as np, pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
sys.path.insert(0, REPO); os.chdir(REPO)
from src import metrics                                        # noqa: E402
from src import experiment as _exp                             # noqa: E402
from src import problems as _problems                          # noqa: E402

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m'
OUT = os.path.join(REPO, 'f5', 'baterias', 'b5m')
NCK = 20

v = metrics.hv_smoke_bbob_f1()
assert abs(v - 1.04333) < 5e-6, 'GATE D92 FALHOU: %r' % v
print('gate D92 OK: %.5f' % v, flush=True)

_PROB = {}
def prob_obj(p):
    if p not in _PROB:
        _PROB[p] = _exp._instantiate_problem(p)
    return _PROB[p]

_REF = {}
def refnorm(p):
    if p not in _REF:
        _REF[p] = metrics.reference_set(p)
    return _REF[p]


def cells():
    for d in sorted(glob.glob(os.path.join(ROOT, '*', '42'))):
        label = os.path.basename(os.path.dirname(d))
        js = glob.glob(os.path.join(d, '*.jsonl'))[0]
        yield label, js[:-len('.jsonl')]


rows, traj_rows = [], []
for label, stem in cells():
    man = json.load(open(stem + '.manifest.json'))
    prob = man['problema']
    c3 = pd.read_parquet(stem + '__surrogate.parquet')
    b = c3[c3.regime == 'offline'].copy()
    snd = c3[c3.regime == 'sonda']
    g = b.geracao.astype(int).values
    n_ger = int(g.max())
    pop = len(b) // n_ger
    assert pop * n_ger == len(b)
    hdr = json.loads(open(stem + '.jsonl').readline())
    D, M = hdr['D'], hdr['M']
    xc = [f'x{i}' for i in range(D)]; mc = [f'mu_{i}' for i in range(M)]
    sc = [f'sigma_{i}' for i in range(M)]
    X = b[xc].values.reshape(n_ger, pop, D)
    MU = b[mc].values.astype(np.float64).reshape(n_ger, pop, M)
    SG = b[sc].values.astype(np.float64).reshape(n_ger, pop, M)

    # ── turnover por transicao (bit-a-bit em float32) ────────────────────────
    chg = (X[1:] != X[:-1]).any(axis=2).mean(axis=1)
    idx3 = np.array_split(np.arange(len(chg)), 3)
    # ── duplicatas por geracao (amostra densa: todas) ────────────────────────
    ndist = np.array([len(np.unique(X[i], axis=0)) for i in range(n_ger)])
    # ── sigma medio da populacao por geracao (media sobre objetivos) ─────────
    sg_gen = SG.mean(axis=(1, 2))
    mu_gen = MU.mean(axis=(1, 2))
    # ── LHS gen 1: estratificacao exata em pop faixas por dimensao ───────────
    xl = np.asarray(prob_obj(prob).xl if hasattr(prob_obj(prob), 'xl') else None)
    lo = X[0].min(axis=0); hi = X[0].max(axis=0)
    # normaliza pelos bounds reais do problema
    from src import standalone_harness as SH
    bl, bu = SH._bounds(prob)
    U = (X[0].astype(np.float64) - bl) / (bu - bl)
    strat_ok = int(sum(1 for d_ in range(D)
                       if np.array_equal(np.sort(np.floor(U[:, d_] * pop).astype(int)),
                                         np.arange(pop))))
    dentro_bounds = bool((X >= bl - 1e-6).all() and (X <= bu + 1e-6).all())

    # ── interseccao da pop inicial com o dataset (② vazia) ──────────────────
    c1 = pd.read_parquet(stem + '__real.parquet')
    Xds = c1[xc].values
    set_ds = set(map(tuple, np.round(Xds.astype(np.float64), 12)))
    inter1 = sum(1 for r in np.round(X[0].astype(np.float64), 12) if tuple(r) in set_ds)
    interall = 0
    for gg in range(0, n_ger, max(1, n_ger // 40)):
        interall += sum(1 for r in np.round(X[gg].astype(np.float64), 12) if tuple(r) in set_ds)

    # ── checkpoints: HV surrogate (mu) x HV/IGD+ real ───────────────────────
    cks = np.unique(np.linspace(0, n_ger - 1, NCK).round().astype(int))
    R = refnorm(prob)
    po = prob_obj(prob)
    hv_s, hv_r, igd_r = [], [], []
    for k in cks:
        ms = metrics.metrics_of_set(MU[k], prob, ref_norm=R)
        Fr = np.asarray(_problems.evaluate_problem(po, X[k].astype(np.float64)),
                        dtype=np.float64)
        mr = metrics.metrics_of_set(Fr, prob, ref_norm=R)
        hv_s.append(ms['hv']); hv_r.append(mr['hv']); igd_r.append(mr['igd_plus'])
        traj_rows.append(dict(label=label, problema=prob, ger=int(k) + 1,
                              frac=(k + 1) / n_ger,
                              hv_surr=ms['hv'], igdp_surr=ms['igd_plus'],
                              hv_real=mr['hv'], igdp_real=mr['igd_plus'],
                              nd_real=mr['n_nd'],
                              sigma_med=float(SG[k].mean()),
                              mu_med=float(MU[k].mean())))
    hv_s = np.array(hv_s); hv_r = np.array(hv_r); igd_r = np.array(igd_r)

    # ── ⑦: recomputo ND, link posicional, metricas do endpoint ──────────────
    c7 = pd.read_parquet(stem + '__final.parquet')
    fc = [f'f{i}' for i in range(M)]
    F7 = c7[fc].values.astype(np.float64)
    nd_re = np.zeros(len(c7), bool)
    nd_re[_problems._nds_filter(F7.astype(np.float32).astype(np.float64))] = True
    nd_ok = bool((nd_re == c7.nd_pos_real.values).all())
    gl = c7.origem_geracao.values.astype(int); ll = c7.origem_linha.values.astype(int)
    link_ok = bool((c7[xc].values == X[gl - 1, ll]).all())
    # f real recomputado do X da ⑦ (checagem de consistencia da ⑦)
    F7re = np.asarray(_problems.evaluate_problem(po, c7[xc].values.astype(np.float64)),
                      dtype=np.float64)
    dev = np.abs(F7re - F7); den = np.maximum(np.abs(F7), 1e-30)
    m7 = metrics.metrics_of_set(F7[c7.nd_pos_real.values], prob, ref_norm=R)

    # ── sigma no espaco: sonda como regua (kNN) — preparada p/ ablacao ──────
    Xs = snd[xc].values.astype(np.float64); Ss = snd[sc].values.astype(np.float64).mean(axis=1)

    rows.append(dict(
        label=label, problema=prob, D=D, M=M, N=hdr['n_dataset'], pop=pop, n_ger=n_ger,
        fe_int=pop * n_ger, overshoot=pop * n_ger - 40000,
        n_ger_esperado=40000 // pop + 1,
        turn_1=float(chg[0]), turn_mean=float(chg.mean()),
        turn_t1=float(chg[idx3[0]].mean()), turn_t2=float(chg[idx3[1]].mean()),
        turn_t3=float(chg[idx3[2]].mean()), turn_last=float(chg[-1]),
        turn_min=float(chg.min()), turn_max=float(chg.max()),
        turn_spearman=float(pd.Series(chg).corr(pd.Series(np.arange(len(chg))), method='spearman')),
        ndist_min=int(ndist.min()), ndist_mean=float(ndist.mean()), ndist_last=int(ndist[-1]),
        dup_gens=int((ndist < pop).sum()),
        sg_g1=float(sg_gen[0]), sg_last=float(sg_gen[-1]),
        sg_ratio=float(sg_gen[-1] / sg_gen[0]) if sg_gen[0] > 0 else np.nan,
        sg_spearman=float(pd.Series(sg_gen).corr(pd.Series(np.arange(n_ger)), method='spearman')),
        mu_g1=float(mu_gen[0]), mu_last=float(mu_gen[-1]),
        lhs_strat_dims=strat_ok, lhs_strat_tot=D, dentro_bounds=dentro_bounds,
        inter_ds_g1=inter1, inter_ds_amostra=interall,
        hv_surr_ini=float(hv_s[0]), hv_surr_fim=float(hv_s[-1]),
        hv_surr_max=float(hv_s.max()), hv_surr_argmax=int(cks[hv_s.argmax()]) + 1,
        hv_real_ini=float(hv_r[0]), hv_real_fim=float(hv_r[-1]),
        igdp_real_ini=float(igd_r[0]), igdp_real_fim=float(igd_r[-1]),
        fig10_surr_cai=bool(hv_s[-1] < hv_s[0]), fig10_real_sobe=bool(hv_r[-1] > hv_r[0]),
        fig10_igdp_melhora=bool(igd_r[-1] < igd_r[0]),
        fig10_assinatura=bool(hv_s[-1] < hv_s[0] and hv_r[-1] > hv_r[0]),
        c7_nd_recomputo_ok=nd_ok, c7_link_posicional_ok=link_ok,
        c7_n=len(c7), c7_nd=int(c7.nd_pos_real.sum()),
        fantasia=float(c7.nd_pos_real.sum() / len(c7)),
        c7_maxdev_abs=float(dev.max()), c7_maxdev_rel=float((dev / den).max()),
        end_igdp=m7['igd_plus'], end_hv=m7['hv'], end_igd=m7['igd'], end_gd=m7['gd'],
        end_spacing=m7['spacing'], end_nnd=m7['n_nd'],
        sonda_sigma_med=float(Ss.mean()),
    ))
    print('ok', label, 'turn1=%.3f last=%.3f sgratio=%.3f fig10=%s' %
          (chg[0], chg[-1], rows[-1]['sg_ratio'], rows[-1]['fig10_assinatura']), flush=True)

df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'b5m_mecanismo.csv'), index=False)
pd.DataFrame(traj_rows).to_csv(os.path.join(OUT, 'b5m_traj_fig10.csv'), index=False)
pd.set_option('display.width', 400); pd.set_option('display.max_columns', 200)
print(df.shape)
print(df[['label', 'pop', 'n_ger', 'n_ger_esperado', 'overshoot', 'turn_1', 'turn_t1', 'turn_t3',
          'turn_last', 'sg_g1', 'sg_last', 'sg_ratio', 'lhs_strat_dims', 'lhs_strat_tot',
          'inter_ds_g1', 'fantasia', 'end_igdp']].to_string())
for c in ['c7_nd_recomputo_ok', 'c7_link_posicional_ok', 'dentro_bounds',
          'fig10_surr_cai', 'fig10_real_sobe', 'fig10_igdp_melhora', 'fig10_assinatura']:
    print(c, int(df[c].sum()), '/', len(df))
print('n_ger == esperado:', int((df.n_ger == df.n_ger_esperado).sum()))
print('lhs 100%:', int((df.lhs_strat_dims == df.lhs_strat_tot).sum()))
print('inter_ds total:', int(df.inter_ds_g1.sum()), int(df.inter_ds_amostra.sum()))
