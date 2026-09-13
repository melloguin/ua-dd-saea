"""T11/b4 — bateria 5: de ONDE vieram os numeros que o `REGRA_DO_ROTULO` do
sigma_dict cita entre parenteses ("prevalencia real medida 65,5%, acuracia
0,350, AUC 0,716" · "domina >=1 ref -> 0,00%/0,999" · "nao dominado -> 0,40%/
0,995")? Testo 5 leituras candidatas na regua Sobol do smoke (MMF1) e no
agregado da s42. READ-ONLY.
"""
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

SM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4'
ART = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet'

art = pq.read_table(ART).to_pandas()
Fa = art[['f0', 'f1']].values[:2000]
real = pq.read_table(f'{SM}/exp_main_b4_MMF1_42__real.parquet').to_pandas()
Fsid = real.set_index('solution_id')[['f0', 'f1']].astype(float)
sur = pq.read_table(f'{SM}/exp_main_b4_MMF1_42__surrogate.parquet').to_pandas()
gens = {r['geracao']: r for r in map(json.loads, open(f'{SM}/exp_main_b4_MMF1_42.jsonl'))
        if r.get('rec') == 'b4_gen'}


def auc_mw(y, s):
    y = np.asarray(y).astype(int)
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    r = pd.Series(np.asarray(s, float)).rank().values
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)


def R_getoutput(F, R):   # GetOutput.m:18 — AND_j OR_k (f_k <= R_jk)
    o = np.ones(len(F), bool)
    for j in range(len(R)): o &= (F <= R[j]).any(1)
    return o

def R_domina1(F, R):     # domina ESTRITAMENTE >=1 ref (Alg.4 impresso)
    o = np.zeros(len(F), bool)
    for j in range(len(R)): o |= ((F <= R[j]).all(1) & (F < R[j]).any(1))
    return o

def R_naodominado(F, R): # nao e dominado por NENHUMA ref
    o = np.ones(len(F), bool)
    for j in range(len(R)): o &= ~(((R[j] <= F).all(1)) & ((R[j] < F).any(1)))
    return o

def R_fracoq1(F, R):     # <= em TODOS os objetivos p/ >=1 ref (dominancia fraca)
    o = np.zeros(len(F), bool)
    for j in range(len(R)): o |= (F <= R[j]).all(1)
    return o

def R_or_or(F, R):       # OR_j OR_k — "melhor que ALGUMA ref em ALGUM objetivo"
    o = np.zeros(len(F), bool)
    for j in range(len(R)): o |= (F <= R[j]).any(1)
    return o


REGRAS = {'GetOutput (DI-18, a declarada)': R_getoutput, 'domina >=1 ref (estrita)': R_domina1,
          'nao dominado por nenhuma ref': R_naodominado, 'dominancia FRACA >=1 ref': R_fracoq1,
          'OR/OR (melhor em algum obj)': R_or_or}

blk = sur[sur.regime == 'sonda']
print('=== REGUA SOBOL do smoke (main/b4/MMF1/42) — 24 blocos, 48.000 linhas · POOLED ===')
for nome, f in REGRAS.items():
    Y = []; P = []; L = []
    for g, sub in blk.groupby('geracao'):
        R = Fsid.loc[[int(v) for v in gens[int(g)]['ref_ids']]].values
        Y.append(f(Fa[:len(sub)], R))
        P.append(sub.pred_classe.values == 'bom')
        L.append(sub.pred_confianca.values.astype(float))
    Y = np.concatenate(Y); P = np.concatenate(P); L = np.concatenate(L)
    print(f'  {nome:32s} prevalencia={Y.mean() * 100:6.2f}%  acuracia={(Y == P).mean():.4f}  AUC={auc_mw(Y, L):.4f}')

print('\n  declarado no sigma_dict: 65,5% / 0,350 / 0,716  (e 0,00%/0,999 e 0,40%/0,995 p/ as outras 2)')
print('  medido na s42 INTEIRA (25 celulas, 3.166 blocos, F5 b4_sonda_blocos.csv):')
d = pd.read_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b4/b4_sonda_blocos.csv')
print(f'    prevalencia POOLED={(d.base_rate * d.n).sum() / d.n.sum() * 100:.2f}%  '
      f'acuracia POOLED={(d.acc * d.n).sum() / d.n.sum():.4f}  '
      f'AUC media={d.auc.mean():.4f} mediana={d.auc.median():.4f}')
print(f'    faixa de prevalencia por bloco: min={d.base_rate.min() * 100:.2f}% max={d.base_rate.max() * 100:.2f}%'
      f' · blocos com prevalencia>=0,60: {(d.base_rate >= .6).sum()}/{len(d)}')
print(f'    celula com maior prevalencia: '
      + str(d.groupby("problema").apply(lambda x: (x.base_rate * x.n).sum() / x.n.sum(), include_groups=False).idxmax()))
