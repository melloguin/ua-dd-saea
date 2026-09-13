"""T11/moead_media · bateria T4 — a leitura da ablacao com o confundidor CERTO.

A F5 excluia as celulas pelo colapso do GP na SONDA (C9a: 14 celulas).
A cadeia A8 (medida em t3) mostra que o confundidor operacional e outro e maior:
os VETORES DE REFERENCIA DEGENERADOS (a busca para de substituir). Recalculo o
contraste piso x b5m no endpoint (⑦) sob os dois cortes.
"""
import os

import numpy as np
import pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))
F5 = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"

# ⑦ das 25 celulas `off` (F5.5) + das 20 de sweep (bateria b9 da F5)
off = pd.read_csv(os.path.join(F5, "transversal_offline_camada7.csv"))
off = off.rename(columns={"igd_plus_c7": "igd7", "hv_c7": "hv7",
                          "n_nd_pos_real": "n_nd"})
off["label"] = off["problema"]
swp = pd.read_csv(os.path.join(F5, "baterias/moead_media/camada7_sweep.csv"))
cols = ["label", "alg", "problema", "n_final", "n_nd", "fantasia", "igd7", "hv7"]
c7 = pd.concat([off[cols], swp[cols]], ignore_index=True)
c7 = c7[c7.alg.isin(["moead_media", "b5m", "b5r"])]
piv = c7.pivot_table(index="label", columns="alg", values="igd7")
piv = piv.dropna(subset=["moead_media", "b5m"])

deg = pd.read_csv(os.path.join(OUT, "t3_adapt_degenerado.csv"))
deg_piso = set(deg[(deg.config == "moead_media") & (deg.adapt_com_col_zerada > 0)].label)
deg_b5m = set(deg[(deg.config == "b5m") & (deg.adapt_com_col_zerada > 0)].label)
deg_any = deg_piso | deg_b5m

son = pd.read_csv(os.path.join(F5, "sonda_f52e.csv"))
son = son[son.alg.isin(["moead_media", "b5m", "b5r"])]
son["col"] = (son.wape.sub(1.0).abs() <= 1e-4) & (
    son["corr"].abs().le(0.015) | son["corr"].isna())
son["label"] = np.where(son.exp == "off", son.problema,
                        son.exp.str.replace("sweep-", "swap_", regex=False)
                        + "_" + son.problema)
col_any = set(son[son.col].label)

piv["razao"] = piv.moead_media / piv.b5m
piv["deg"] = [i in deg_any for i in piv.index]
piv["colapso_sonda"] = [i in col_any for i in piv.index]
piv.to_csv(os.path.join(OUT, "t4_ablacao_corrigida.csv"))


def bloco(nome, sub):
    v = sub.razao.replace([np.inf, -np.inf], np.nan).dropna()
    print("%-42s n=%-3d piso_vence=%-3d razao_mediana=%.3f  "
          "pen_mediana=%+.1f%%"
          % (nome, len(sub), int((sub.moead_media < sub.b5m).sum()),
             v.median(), 100 * (v.median() - 1)))


print("celulas com vetores degenerados — piso %d, b5m %d, uniao %d"
      % (len(deg_piso), len(deg_b5m), len(deg_any)))
print("celulas com colapso de GP na sonda (qualquer lado): %d" % len(col_any))
print("uniao dos dois confundidores: %d" % len(deg_any | col_any))
print()
bloco("TODAS", piv)
bloco("limpas do confundidor A8 (vetores)", piv[~piv.deg])
bloco("limpas do confundidor C9a (sonda)", piv[~piv.colapso_sonda])
bloco("limpas dos DOIS", piv[~piv.deg & ~piv.colapso_sonda])
bloco("SO as degeneradas", piv[piv.deg])
print()
print(piv.sort_values("razao").to_string())
