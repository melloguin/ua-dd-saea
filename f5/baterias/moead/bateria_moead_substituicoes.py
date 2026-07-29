#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_moead_substituicoes.py — recupera do DADO o que o DI-10 REJEITOU instrumentar
("contagem de substituições por geração do MOEA/D" — CONTRATO §DI-10, rejeitados).

Método: ②(g) é o snapshot do INÍCIO da geração g (provado: ②(1) == seeding). Logo
`②(g+1) vs ②(g)` posição a posição dá o EFEITO LÍQUIDO da geração g:
  - `subst_liq`      = nº de slots i cujo solution_id mudou
  - `co_subst_par`   = nº de PARES (i, nn(i)) em que AMBOS mudaram para o MESMO sid
                       (a assinatura literal de `Population(P(g_old>=g_new)) = Offspring`
                        com T=2 substituindo os dois vizinhos de uma vez)
  - `novos_clones`   = nº de pares idênticos CRIADOS na geração
Também mede a evolução do nº de indivíduos distintos e da fração ainda vinda do DoE.
"""
import json, os
import numpy as np
import pandas as pd

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = os.path.join(REPO, 'f5', 'baterias', 'moead')
PROBS = sorted(p for p in os.listdir(RAIZ) if not p.startswith('.'))


def vizinhanca(W, T=2):
    d = np.sqrt(((W[:, None, :] - W[None, :, :]) ** 2).sum(-1))
    return np.argsort(d, axis=1, kind='stable')[:, :T]


rows, det = [], []
for prob in PROBS:
    base = os.path.join(RAIZ, prob, '42', 'exp_main_moead_%s_42' % prob)
    man = json.load(open(base + '.manifest.json'))
    evs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    dec = [e for e in evs if e['rec'] == 'decomposicao'][0]
    gens = [e for e in evs if e['rec'] == 'moead_gen']
    pop = pd.read_parquet(base + '__pop.parquet')
    D = hdr['D']; n_doe = 11 * D - 1
    N = man['params']['N_efetivo']
    W = np.array(dec['vetores'], float)
    B = vizinhanca(W, int(np.ceil(len(W) / 10)))
    nn = B[:, 1]
    snaps = [g[1]['solution_id'].to_numpy() for g in sorted(pop.groupby('geracao'), key=lambda t: t[0])]
    S = np.array(snaps)                       # (n_ger, N)
    tot_sub, tot_co, tot_slots = 0, 0, 0
    for g in range(len(S) - 1):
        a, b = S[g], S[g + 1]
        mud = a != b
        co = int(((mud) & (mud[nn]) & (b == b[nn])).sum())
        tot_sub += int(mud.sum()); tot_co += co; tot_slots += N
        det.append(dict(problema=prob, geracao=g + 1, subst=int(mud.sum()),
                        co_subst=co, N=N,
                        pares_id_antes=int((a == a[nn]).sum()),
                        pares_id_depois=int((b == b[nn]).sum()),
                        distintos_antes=int(len(set(a.tolist()))),
                        distintos_depois=int(len(set(b.tolist()))),
                        doe_antes=int((a < n_doe).sum()), doe_depois=int((b < n_doe).sum())))
    dcell = [d for d in det if d['problema'] == prob]
    rows.append(dict(problema=prob, D=D, M=hdr['M'], N=N, n_ger=man['n_geracoes'],
                     transicoes=len(dcell),
                     subst_total=tot_sub, subst_por_ger=tot_sub / max(len(dcell), 1),
                     taxa_subst=tot_sub / max(tot_slots, 1),
                     co_subst_total=tot_co, frac_co=tot_co / max(tot_sub, 1),
                     pares_id_ini=dcell[0]['pares_id_antes'] if dcell else np.nan,
                     pares_id_fim=dcell[-1]['pares_id_depois'] if dcell else np.nan,
                     distintos_ini=dcell[0]['distintos_antes'] if dcell else np.nan,
                     distintos_fim=dcell[-1]['distintos_depois'] if dcell else np.nan,
                     doe_ini=dcell[0]['doe_antes'] if dcell else np.nan,
                     doe_fim=dcell[-1]['doe_depois'] if dcell else np.nan))

df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'moead_substituicoes.csv'), index=False)
pd.DataFrame(det).to_csv(os.path.join(OUT, 'moead_substituicoes_por_geracao.csv'), index=False)
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 40)
print(df.to_string())
print('\nΣ substituições líquidas:', df.subst_total.sum(), ' Σ co-substituições de par:', df.co_subst_total.sum())
print('taxa de substituição por slot: med %.3f (min %.3f max %.3f)' % (df.taxa_subst.median(), df.taxa_subst.min(), df.taxa_subst.max()))
print('fração das substituições que são co-substituição do par: med %.3f' % df.frac_co.median())
print('distintos: início med %.1f  fim med %.1f' % (df.distintos_ini.median(), df.distintos_fim.median()))
