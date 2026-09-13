#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""consolida_moead.py — consolida todos os números citados no relatório de fidelidade."""
import os, json
import numpy as np
import pandas as pd

O = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/moead/'
F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/'
a = pd.read_csv(O + 'moead_aspectos.csv'); j = pd.read_csv(O + 'moead_joias.csv')
e = pd.read_csv(O + 'moead_extras.csv'); s = pd.read_csv(O + 'moead_saude.csv')
sub = pd.read_csv(O + 'moead_substituicoes.csv'); pp = pd.read_csv(O + 'moead_populacao_vs_doe.csv')
ic = pd.read_csv(O + 'moead_clonagem_ic.csv')
out = {}
out['celulas'] = len(a)
out['geracoes'] = int(a.n_ger.sum())
out['linhas_1'] = int((31 * a.D - 1).sum()); out['init_1'] = int((11 * a.D - 1).sum())
out['opt_1'] = out['linhas_1'] - out['init_1']
out['linhas_2'] = int((a.n_ger * a.N_ef).sum()); out['linhas_3'] = 0
out['linhas_4'] = int(a.n_ger.sum())
out['cache_hits_total'] = int(a.ch_jsonl.sum())
out['cache_seeding'] = int((a.N_ef + 1).sum()); out['cache_offspring'] = int(ic.hits.sum())
out['hard_stop'] = int(a.hs_jsonl.sum())
out['tentativas'] = int(e.tentativas.sum())
out['ledger'] = out['opt_1'] + out['cache_offspring'] + out['hard_stop'] - out['tentativas']
out['taxa_clone_global'] = out['cache_offspring'] / out['tentativas']
out['ic_contem_previsao'] = int(ic.ic_contem.sum())
out['subst_total'] = int(sub.subst_total.sum()); out['co_subst'] = int(sub.co_subst_total.sum())
out['frac_co'] = out['co_subst'] / out['subst_total']
out['transicoes'] = int(sub.transicoes.sum())
out['d88_ordem_f64'] = int(s.s1_ordem.sum()); out['d88_conj_f64'] = int(s.s1_conjunto.sum())
out['dX_max'] = float(a.dX_max.max()); out['dF_max'] = float(s.s2_max_dif.max())
out['seed_exc'] = int(a.seed_exc.sum())
out['seed_exc_cells'] = list(a.loc[a.seed_exc, 'problema'])
out['ideal_eq_minpop'] = int(e.ideal_eq_minpop.sum()); out['nadir_eq_maxpop'] = int(e.nadir_eq_maxpop.sum())
out['fbest_e_individuo'] = int(e.fbest_e_individuo.sum())
out['viol_mono_ideal'] = int(j.viol_mono_ideal.sum())
out['celulas_com_ideal_nao_mono'] = int((j.viol_mono_ideal > 0).sum())
out['nf1_ok'] = int(e.nf1_confere.sum()); out['nf1_div'] = out['geracoes'] - out['nf1_ok']
out['traj_viol'] = int(s.traj_viol.sum())
out['razao_arq_doe_med'] = float(s.razao_doe.median())
out['regride_arquivo'] = int(s.regride.sum())
m = pp[pp.alg == 'moead']
out['regride_pop'] = int(m.reg_vs_doe.sum()); out['regride_pop_cells'] = list(m.loc[m.reg_vs_doe, 'problema'])
out['unicos_popF_med'] = float(m.unicos_popF.median())
for alg in ['nsga2', 'nsga3', 'smsemoa']:
    q = pp[pp.alg == alg]
    out['regride_pop_' + alg] = int(q.reg_vs_doe.sum()); out['unicos_popF_' + alg] = float(q.unicos_popF.median())
t = pd.read_csv(F5 + 'tempo_f52d.csv'); t = t[(t.alg == 'moead') & (t.exp == 'main')]
out['tempo_total_s'] = float(t.wall_s.sum()); out['tempo_hcore'] = out['tempo_total_s'] / 3600
out['tempo_med_s'] = float(t.wall_s.median()); out['maquinas'] = list(t.maquina.unique())
out['frac_tempo_geracoes'] = float(e.frac_ger_no_total.median())
out['k_hardstop_min'] = int(e.k_hardstop.min()); out['k_hardstop_max'] = int(e.k_hardstop.max())
out['f_ident_med'] = float(j.f_pares_identicos.median())
out['f_ident_min'] = float(j.f_pares_identicos.min()); out['f_ident_max'] = float(j.f_pares_identicos.max())
out['pares_id_ini_zero'] = int((sub.pares_id_ini == 0).sum())
print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
pd.Series(out).to_csv(O + 'moead_consolidado.csv')
