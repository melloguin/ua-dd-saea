"""B03 — mecanismo TGPR-MO: curva de cobertura (n_gps/n_folhas/total_points), banda
[N_min,2N_min-1], early-stop (janela 2 / mínimo 6), profundidade, I_eff x I_max,
população RVEA por geração, f_best."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from lib_c311 import *

it_rows, cel_rows, inc_rows, pop_rows = [], [], [], []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref, camadas=('real', 'surrogate'))
    mt = meta(label, man)
    real, sur = dfs['real'], dfs['surrogate']
    Xc = xcols(real); Fc = fcols(real); D = len(Xc); M = len(Fc); N = len(real)
    Nmin = 10 * D
    bu = busca(sur)
    dec = [e for e in evs if e.get('rec') == 'decision']
    I_eff = len(dec); I_max = math.ceil(N / Nmin)
    prev_tp = None; prev_gps = None
    mono_ok = True; passo_ok = True; gps_le_folhas = True; sat_ok = True
    n_inc_pos = 0; n_inc_banda = 0; fora = []
    for k, e in enumerate(dec):
        tp = np.array(e['total_points_per_model'], float)
        ng = np.array(e['n_gps'], float)
        nf = np.array(e['n_folhas'], float)
        pr = np.array(e['profundidade'], float)
        if prev_tp is not None:
            dtp = tp - prev_tp; dg = ng - prev_gps
            if (dtp < -1e-9).any(): mono_ok = False
            if (dg < -1e-9).any() or (dg > 1 + 1e-9).any(): passo_ok = False
            for j in range(M):
                if dtp[j] > 0:
                    n_inc_pos += 1
                    dentro = (Nmin <= dtp[j] <= 2 * Nmin - 1)
                    n_inc_banda += int(dentro)
                    inc_rows.append(dict(**mt, D=D, M=M, N=N, Nmin=Nmin, iteracao=e.get('iteracao'),
                                         obj=j, dtp=float(dtp[j]), dgps=float(dg[j]),
                                         dentro=bool(dentro), tp=float(tp[j]), ngps=float(ng[j]),
                                         nfolhas=float(nf[j])))
                    if not dentro:
                        fora.append(f"it{e.get('iteracao')}/obj{j}:+{int(dtp[j])}")
        if (ng > nf + 1e-9).any(): gps_le_folhas = False
        if (tp > N + 1e-9).any(): sat_ok = False
        it_rows.append(dict(**mt, D=D, M=M, N=N, Nmin=Nmin, I_eff=I_eff, I_max=I_max,
                            k=k, iteracao=e.get('iteracao'), geracao=e.get('geracao'),
                            n_gps=json.dumps(e['n_gps']), n_folhas=json.dumps(e['n_folhas']),
                            prof_max=float(pr.max()), tp=json.dumps(e['total_points_per_model']),
                            tp_frac=float(tp.mean() / N), delta_total_point=e.get('delta_total_point'),
                            early_stop=e.get('early_stop'), n_front1=e.get('n_front1'),
                            f_best=json.dumps(e.get('f_best')),
                            tempo_fit_s=e.get('tempo_fit_s'), tempo_busca_s=e.get('tempo_busca_s'),
                            motivo=e.get('motivo')))
        prev_tp, prev_gps = tp, ng
    last = dec[-1]
    tpl = np.array(last['total_points_per_model'], float)
    # early-stop
    es = [bool(e.get('early_stop')) for e in dec]
    dtps = [e.get('delta_total_point') for e in dec]
    idx_es = [i + 1 for i, v in enumerate(es) if v]
    # população RVEA por geração
    tam = bu.groupby('geracao').size()
    ger_build_max = 51 * I_eff
    tam_b = tam[tam.index <= ger_build_max]; tam_f = tam[tam.index > ger_build_max]
    pop_teto = 50 if M == 2 else 105
    cel_rows.append(dict(**mt, D=D, M=M, N=N, Nmin=Nmin, I_eff=I_eff, I_max=I_max,
                         I_frac=I_eff / I_max,
                         mono_ok=mono_ok, passo_ok=passo_ok, gps_le_folhas=gps_le_folhas,
                         sat_ok=sat_ok, n_inc_pos=n_inc_pos, n_inc_banda=n_inc_banda,
                         n_inc_fora=n_inc_pos - n_inc_banda, incs_fora=';'.join(fora),
                         n_gps_final=json.dumps(last['n_gps']),
                         n_folhas_final=json.dumps(last['n_folhas']),
                         tp_final=json.dumps(last['total_points_per_model']),
                         cobertura_frac=float(tpl.mean() / N),
                         prof_max=float(max(np.array(e['profundidade'], float).max() for e in dec)),
                         max_folhas=float(max(np.array(e['n_folhas'], float).max() for e in dec)),
                         teto_folhas=math.floor(N / Nmin),
                         early_any=any(es), early_idx=';'.join(map(str, idx_es)),
                         early_na_ultima=bool(es[-1]),
                         corte_antes_Imax=bool(I_eff < I_max),
                         delta_unicos=';'.join(sorted({str(x) for x in dtps})[:5]),
                         delta_ultimo=dtps[-1],
                         pop_teto=pop_teto,
                         pop_max=int(tam.max()), pop_min=int(tam.min()),
                         pop_med_build=float(tam_b.median()), pop_med_final=float(tam_f.median()),
                         pop_ger1=int(tam.loc[1]) if 1 in tam.index else -1,
                         pop_ger50=int(tam.loc[50]) if 50 in tam.index else -1,
                         pop_ultima=int(tam.iloc[-1]),
                         colapso_pre50=bool(tam[tam.index <= 50].min() <= 10),
                         excede_teto=bool(tam.max() > pop_teto),
                         fit_total=float(sum(e.get('tempo_fit_s') or 0 for e in dec)),
                         busca_total=float(sum(e.get('tempo_busca_s') or 0 for e in dec)),
                         tempo_total_s=man['timing']['tempo_total_s']))
    q = tam.reindex(range(1, int(tam.index.max()) + 1))
    for g in [1, 10, 25, 50, 51, 52, 100, ger_build_max, ger_build_max + 1, ger_build_max + 500, ger_build_max + 1000]:
        if g in q.index:
            pop_rows.append(dict(**mt, M=M, geracao=int(g), pop=int(q.loc[g]), teto=pop_teto,
                                 fase=('build' if g <= ger_build_max else 'final')))
    print(label, 'I_eff', I_eff, '/', I_max, 'inc', n_inc_pos, 'fora', n_inc_pos - n_inc_banda)

salva(pd.DataFrame(it_rows), 'b03_iteracoes.csv')
salva(pd.DataFrame(cel_rows), 'b03_celulas.csv')
salva(pd.DataFrame(inc_rows), 'b03_incrementos.csv')
salva(pd.DataFrame(pop_rows), 'b03_populacao.csv')
c = pd.DataFrame(cel_rows)
print('\nmono', c.mono_ok.sum(), 'passo', c.passo_ok.sum(), 'gps<=folhas', c.gps_le_folhas.sum(),
      'sat', c.sat_ok.sum(), '/', len(c))
print('incrementos', c.n_inc_pos.sum(), 'na banda', c.n_inc_banda.sum(), 'fora', c.n_inc_fora.sum())
print('early_any', c.early_any.sum(), 'corte<Imax', c.corte_antes_Imax.sum())
print(c.groupby('tier')[['I_eff', 'I_max', 'I_frac', 'cobertura_frac', 'prof_max', 'pop_max']].median().to_string())
