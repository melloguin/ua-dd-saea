#!/usr/bin/env python
"""Parte 3: (a) exposicao do torneio bugado K.3 na celula (ERRATA 10/16 re-medida);
(b) forense da divergencia T11 x rodada-42; (c) cabeca-a-cabeca b1 x b3 no smoke."""
import json, numpy as np, pandas as pd
from collections import Counter

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b1'
T11 = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1/exp_main_b1_MMF1_42'
R42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42/exp_main_b1_MMF1_42'
B3S = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
INIT = 21
R = []
def say(k, v):
    R.append((k, v)); print(f'{k:48s} | {v}')

gen = [json.loads(l) for l in open(T11 + '.jsonl') if l.strip()]
gen = [g for g in gen if g['rec'] == 'b1_gen']
gq = [json.loads(l) for l in open(R42 + '.jsonl') if l.strip()]
gq = [g for g in gq if g['rec'] == 'b1_gen']
G = len(gen)

print('#' * 18, 'K.3 — exposicao do torneio bugado (re-medida no meu config)')
na = np.array([g['n_arquivo'] for g in gen]); nt = np.array([g['n_treino'] for g in gen])
ns = np.array([g['n_subset'] for g in gen]); gp = np.array([g['ga_pop'] for g in gen])
gi = np.array([g['ga_iters'] for g in gen])
vivo = nt < na
say('K3.iters com |PCheby| < |Dec| (bug VIVO)', f'{int(vivo.sum())}/{G} = {vivo.mean():.1%}')
say('K3.1a iteracao com bug vivo', f'{int(np.argmax(vivo))+1} (cap engata em n_arquivo>46)')
say('K3.linhas de Dec inalcancaveis (med/max)', f'{np.median((na-nt)[vivo]):.0f} / {(na-nt).max()}')
# ERRATA 10: so a metade-crossover da 1a geracao interna
cand_tot = int((gp * gi).sum()); cand_bug = int((gp[vivo] / 2).sum())
say('K3.candidatos scorados no ciclo', f'{cand_tot}')
say('K3.candidatos no ramo bugado (1a ger, 1/2)', f'{cand_bug} = {cand_bug/cand_tot:.2%}')
ei = np.array([g['ei_best'] for g in gen])
venceu1 = np.array([abs(g['e0_trace'][0] - g['ei_best']) < 1e-15 for g in gen])
const = np.array([len(set(g['e0_trace'])) == 1 for g in gen])
say('K3.ei_best veio da 1a geracao interna', f'{int(venceu1.sum())}/{G} = {venceu1.mean():.1%}')
say('K3.destes, e0_trace CONSTANTE (degenerado)', f'{int((venceu1&const).sum())}/{int(venceu1.sum())}')
say('K3.1a-ger venceu E o GA melhorou (nao-deg)', f'{int((venceu1&~const).sum())}/{G} = {(venceu1&~const).mean():.1%}')
say('K3.1a-ger venceu E bug vivo', f'{int((venceu1&vivo).sum())}/{G}')
say('K3.1a-ger venceu, bug vivo, nao-degenerado', f'{int((venceu1&vivo&~const).sum())}/{G} = {(venceu1&vivo&~const).mean():.1%}')
say('K3.INERTE (complemento)', f'{G-int((venceu1&vivo).sum())}/{G} = {1-(venceu1&vivo).mean():.1%}')
say('K3.ganho de EI da 1a p/ a ultima ger interna', f'mediana {np.median([abs(g["ei_best"]/g["e0_trace"][0])-1 for g in gen]):.3f}')

print('#' * 18, 'DIVERGENCIA T11 x rodada-42 — forense')
n = min(G, len(gq))
e0a, e0b = gen[0]['e0_trace'], gq[0]['e0_trace']
d = [i for i in range(min(len(e0a), len(e0b))) if e0a[i] != e0b[i]]
say('DIV.len(e0_trace) g1 T11/R42', f'{len(e0a)} / {len(e0b)}')
say('DIV.1a geracao INTERNA de g1 que difere', f'{d[0]+1 if d else "nenhuma"} de {len(e0a)}')
if d:
    i = d[0]
    say('DIV.valor nesse ponto T11 / R42', f'{e0a[i]:.17g} / {e0b[i]:.17g}  |d|={abs(e0a[i]-e0b[i]):.3e}')
    say('DIV.ULP relativo', f'{abs(e0a[i]-e0b[i])/abs(e0b[i]):.3e}')
for k in ['gbest', 'mu_best', 'sigma_best']:
    a = np.array([g[k] for g in gen[:n]]); b = np.array([g[k] for g in gq[:n]])
    rel = np.abs(a - b) / np.maximum(np.abs(b), 1e-300)
    say(f'DIV.{k}: |rel| max nas 3 1as gers', f'{rel[:3].max():.3e}')
bsA = [g['best_sid'] for g in gen[:n]]; bsB = [g['best_sid'] for g in gq[:n]]
dd = [i for i in range(n) if bsA[i] != bsB[i]]
say('DIV.1a geracao com best_sid diferente', f'{dd[0]+1 if dd else "nenhuma"} de {n}')
feA = [g['fe'] for g in gen[:n]]; feB = [g['fe'] for g in gq[:n]]
df = [i for i in range(n) if feA[i] != feB[i]]
say('DIV.1a geracao com fe diferente', f'{df[0]+1 if df else "nenhuma"}')
rA = pd.read_parquet(T11 + '__real.parquet'); rB = pd.read_parquet(R42 + '__real.parquet')
XA = rA[['x0', 'x1']].to_numpy(); XB = rB[['x0', 'x1']].to_numpy()
ig = np.where(np.any(XA != XB, axis=1))[0]
say('DIV.1 linhas identicas (bit-a-bit)', f'{61-len(ig)}/61; 1a divergente fe_index={ig[0] if len(ig) else "-"}')
FA = rA[['f0', 'f1']].to_numpy(np.float64); FB = rB[['f0', 'f1']].to_numpy(np.float64)
say('DIV.max|df| nas linhas comuns', f'{np.abs(FA[:ig[0]]-FB[:ig[0]]).max() if len(ig) else 0:.3e}')
say('DIV.cache_hits T11/R42 (deriva do ledger)', f'{sum(1 for x in np.diff([INIT]+feA) if x==0)+1} / {sum(1 for x in np.diff([INIT]+feB) if x==0)+1}')

print('#' * 18, 'b1 x b3 no MESMO smoke (main/*/MMF1/42)')
def front(F):
    nd = np.ones(len(F), bool)
    for i in range(len(F)):
        if nd[i]:
            dom = np.all(F <= F[i], 1) & np.any(F < F[i], 1)
            if dom.any(): nd[i] = False
    return F[nd]
mb3 = json.load(open(B3S + '.manifest.json'))
r3 = pd.read_parquet(B3S + '__real.parquet')
F3 = r3[['f0', 'f1']].to_numpy(np.float64)
say('b3.maxfe/fe_final/n_geracoes', f'{mb3["maxfe"]}/{mb3["fe_final"]}/{mb3["n_geracoes"]}')
for nome, FF in [('b1', FA), ('b3', F3)]:
    P = front(FF)
    say(f'{nome}.|front nao-dominado| / n_aval', f'{len(P)} / {len(FF)}')
    say(f'{nome}.min f0 / min f1', f'{FF[:,0].min():.5g} / {FF[:,1].min():.5g}')
say('b1.n_front1 final (evento)', f'{gen[-1]["n_front1"]}')

json.dump([{'k': k, 'v': v} for k, v in R], open(f'{OUT}/b1_parte3.json', 'w'), indent=1)
print('\nSALVO', f'{OUT}/b1_parte3.json')
