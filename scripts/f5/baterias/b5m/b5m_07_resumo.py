#!/usr/bin/env python
"""BATERIA b5m #7 — consolidacao dos numeros citados no relatorio.
Le os CSVs das baterias 1-6 + os insumos pre-computados da F5.2 e emite
b5m_resumo.csv (metrica, valor, denominador, fonte).
"""
import glob, json, os
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, binomtest

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
B = os.path.join(F5, 'baterias', 'b5m')

est = pd.read_csv(os.path.join(B, 'b5m_estrutura.csv'))
mec = pd.read_csv(os.path.join(B, 'b5m_mecanismo.csv'))
con = pd.read_csv(os.path.join(B, 'b5m_congelamento.csv'))
end = pd.read_csv(os.path.join(B, 'b5m_endpoint7.csv'))
uni = pd.read_csv(os.path.join(B, 'b5m_universais.csv'))
viz = pd.read_csv(os.path.join(B, 'b5m_vizinhanca.csv'))
son = pd.read_csv(os.path.join(F5, 'sonda_f52e.csv')); son = son[son.alg == 'b5m']
tmp = pd.read_csv(os.path.join(F5, 'tempo_f52d.csv'))

R = []
def add(k, v, den='', src=''):
    R.append(dict(metrica=k, valor=v, denominador=den, fonte=src))

add('celulas analisadas', len(est), 45, 'b5m_estrutura.csv')
add('n_ger == floor(40000/pop)+1', int((mec.n_ger == mec.n_ger_esperado).sum()), 45, 'b5m_mecanismo')
add('overshoot FE interno (M=2 / M=3)', '50 / 5', '40000', 'b5m_mecanismo')
add('LHS: dimensoes perfeitamente estratificadas', int((mec.lhs_strat_dims == mec.lhs_strat_tot).sum()), 45, 'b5m_mecanismo')
add('intersecao pop-inicial x dataset', int(mec.inter_ds_g1.sum()), 'ger.1 de 45 celulas', 'b5m_mecanismo')
add('grupos de substituicao', int(viz.grupos.sum()), '', 'b5m_vizinhanca')
add('grupos dentro de UMA vizinhanca de 20', int(viz.contidos.sum()), int(viz.grupos.sum()), 'b5m_vizinhanca')
add('grupos multi-slot (>1)', int(viz.grupos_multi.sum()), int(viz.grupos.sum()), 'b5m_vizinhanca')
add('decisoes ⑥', int(uni.U10_dec_n.sum()), '', 'b5m_universais')
add('f_best identidade (rtol 1e-6)', 30165, 30165, 'b5m_universais (recheck)')
add('n_front1 identidade', 29310, 30165, 'b5m_universais (recheck)')
add('⑦ ND recomputado == nd_pos_real', int(uni.U12_nd.sum()), 45, 'b5m_universais')
add('⑦ link posicional bit-a-bit', int(uni.U12_link.sum()), 45, 'b5m_universais')
add('sonda join posicional max|dX|', float(uni.U5_maxdX.max()), 45, 'b5m_universais')
add('turnover 1a transicao (mediana)', round(float(mec.turn_1.median()), 4), 45, 'b5m_mecanismo')
add('turnover medio por celula (mediana)', round(float(con.b5m_turn_mean.median()), 4), 45, 'b5m_congelamento')
add('turnover medio piso moead_media (mediana)', round(float(con.moead_media_turn_mean.median()), 4), 45, 'b5m_congelamento')
add('spearman(turnover, geracao) mediana', round(float(mec.turn_spearman.median()), 3), 45, 'b5m_mecanismo')
add('sigma_pop final/inicial (mediana)', round(float(mec.sg_ratio.median()), 3), 45, 'b5m_mecanismo')
add('celulas com sigma_pop decrescente', int((mec.sg_ratio < 1).sum()), 45, 'b5m_mecanismo')

s = end.pivot_table(index='label', columns='alg', values='sigma_nn_med')
i = end.pivot_table(index='label', columns='alg', values='igd_plus')
add('ABLACAO D77 sigma(⑦) b5m < piso', int((s.b5m < s.moead_media).sum()), 45, 'b5m_endpoint7')
add('ABLACAO D77 sigma Wilcoxon p', float('%.5f' % wilcoxon(s.b5m, s.moead_media).pvalue), 45, 'b5m_endpoint7')
add('ABLACAO D77 sigma razao mediana b5m/piso', round(float(np.median(s.b5m / s.moead_media)), 3), 45, 'b5m_endpoint7')
add('ABLACAO D77 IGD+(⑦) b5m < piso', int((i.b5m < i.moead_media).sum()), 45, 'b5m_endpoint7')
add('ABLACAO D77 IGD+ Wilcoxon p', float('%.4f' % wilcoxon(i.b5m, i.moead_media).pvalue), 45, 'b5m_endpoint7')
add('IGD+(⑦) mediana b5m / piso', '%.4f / %.4f' % (i.b5m.median(), i.moead_media.median()), 45, 'b5m_endpoint7')
add('fantasia nd_pos_real/n_final (mediana)', round(float(mec.fantasia.median()), 3), 45, 'b5m_mecanismo')
add('HV-surrogate termina abaixo do pico', int((mec.hv_surr_fim < mec.hv_surr_max).sum()), 45, 'b5m_mecanismo (Fig.10a)')
add('IGD+ real melhora inicio->fim', int(mec.fig10_igdp_melhora.sum()), 45, 'b5m_mecanismo (Fig.10b)')
add('sonda pares celula x objetivo', len(son), '', 'sonda_f52e')
add('sonda WAPE mediana', round(float(son.wape.median()), 4), len(son), 'sonda_f52e')
add('sonda corr mediana', round(float(son['corr'].median()), 4), len(son), 'sonda_f52e')
add('sonda cobertura95 mediana', round(float(son.cobertura95.median()), 4), len(son), 'sonda_f52e')
add('sonda sigma-NaN', int(son.n_nan.sum()), len(son), 'sonda_f52e')
deg = ((son.wape.round(6) == 1.0) | (son['corr'].isna()))
add('pares com GP DEGENERADO (WAPE=1 ou corr NaN)', int(deg.sum()), len(son), 'sonda_f52e')
add('geracoes CONGELADAS (0 substituicoes)', int((con.b5m_gers_congeladas - 1).clip(lower=0).sum()), int(con.b5m_n_ger.sum()), 'b5m_congelamento')
add('wall mediano b5m / b5r / piso (s)', '%.0f / %.0f / %.0f' % (
    tmp[tmp.alg == 'b5m'].wall_s.median(), tmp[tmp.alg == 'b5r'].wall_s.median(),
    tmp[tmp.alg == 'moead_media'].wall_s.median()), 45, 'tempo_f52d')
add('h-core b5m 45 celulas (1 semente)', round(float(tmp[tmp.alg == 'b5m'].wall_s.sum() / 3600), 1), 45, 'tempo_f52d')
add('projecao 30 sementes (h-core)', round(float(tmp[tmp.alg == 'b5m'].wall_s.sum() * 30 / 3600)), 45, 'tempo_f52d')
add('p_wrong_stats no ⑥', 0, 30165, 'b5m_estrutura (DI-10 CONTRATO §6.1)')
add('pesos de decomposicao no HEADER', 0, 45, 'b5m_estrutura (DI-10 CONTRATO §6.1)')

df = pd.DataFrame(R)
df.to_csv(os.path.join(B, 'b5m_resumo.csv'), index=False)
pd.set_option('display.width', 200); pd.set_option('display.max_colwidth', 60)
print(df.to_string(index=False))
