#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bateria 6 — CAUSA RAIZ do sentinela -1 em `pmid_ids`, provada sem MATLAB.

Cadeia (só leitura de código + o dado do smoke):
  1. CalFitnessPC.m:67-68  Input = [PopDec(idx,:) , Fitness(idx)]   -> D+1 COLUNAS
  2. CalFitnessPC.m:73     Pmid  = Input(a:b, :)                    -> D+1 COLUNAS
  3. c217_instrument.m:201 bud.solutionIdOf(Pmid(i, :))             -> passa D+1 valores
  4. FEBudget.m:167-173    keyOf = hex de typecast(double(x))       -> 16*len(x) chars
  5. FEBudget.m:111-112    isKey(keymap, key)  -> as chaves do mapa têm 16*D chars
  => arity 16*(D+1) != 16*D  ==>  isKey SEMPRE falso  ==>  sid = -1, 100% das linhas.

CONTROLE INTERNO (mesmo arquivo, mesma geração, mesmo `bud`):
  c217_instrument.m:32 usa `TrainIn(i, 1:Problem.D)` — FATIADO — e resolve:
  `fe_treino_max` sai não-nulo em 42/42. TrainIn = Input(K,:) tem as MESMAS D+1
  colunas que Pmid: a ÚNICA diferença é a fatia.
"""
import json, os, re
import numpy as np

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
D_EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
PCS  = os.path.join(REPO, 'algorithms/_PlatEMO/PlatEMO/Algorithms/Multi-objective optimization/PC-SAEA')

def keyOf(x):                      # réplica exata de FEBudget.keyOf
    return np.asarray(x, dtype='<f8').tobytes().hex().upper()

X = [0.3141592653589793, 0.2718281828459045]
FIT = 0.4142135623730951
print('D = 2 (MMF1)')
print('  chave do MAPA      keyOf([x0,x1])      len = %d' % len(keyOf(X)))
print('  chave do pmid_ids  keyOf([x0,x1,Fit])  len = %d' % len(keyOf(X + [FIT])))
print('  prefixo comum: %s' % (keyOf(X) == keyOf(X + [FIT])[:len(keyOf(X))]))
print('  isKey(map, chave-de-3) -> False SEMPRE (comprimento diferente)\n')

for f, pat in [('CalFitnessPC.m', r'Input\s*=\s*\[Input,'),
               ('CalFitnessPC.m', r'Pmid\s*='),
               ('SurrogateAssistedSelectionPC.m', r'Pa\s*=\s*Pa\(:,1:D\)'),
               ('RBFNNPC.m', r'Preference\(mod')]:
    src = open(os.path.join(PCS, f), errors='replace').read().splitlines()
    for i, l in enumerate(src, 1):
        if re.search(pat, l):
            print('  %-32s :%-3d %s' % (f, i, l.strip()[:96]))
print()
src = open(os.path.join(REPO, 'src/c217_instrument.m')).read().splitlines()
for i, l in enumerate(src, 1):
    if 'solutionIdOf' in l:
        print('  %-32s :%-3d %s' % ('c217_instrument.m', i, l.strip()[:96]))

B = os.path.join(D_EV, 'smoke_matlab/experiments/main/c217/exp_main_c217_MMF1_42.jsonl')
gen = [json.loads(l) for l in open(B) if l.strip() and '"c217_gen"' in l]
print('\nDADO (o contraste, na MESMA geração e no MESMO bud):')
print('  pmid_ids  (Pmid(i,:)      , D+1 col) : %d/%d ids == -1'
      % (sum(sum(1 for v in g['pmid_ids'] if v == -1) for g in gen),
         sum(len(g['pmid_ids']) for g in gen)))
print('  fe_treino_max (TrainIn(i,1:D), fatiado): %d/%d gerações NÃO-nulas'
      % (sum(g['fe_treino_max'] is not None for g in gen), len(gen)))
print('\nCORREÇÃO MÍNIMA (1 token, c217_instrument.m:201):')
print('    ids(i) = bud.solutionIdOf(Pmid(i, :));       %  hoje  -> -1')
print('    ids(i) = bud.solutionIdOf(Pmid(i, 1:end-1)); %  fix   -> id real')
print('  (`end-1` porque Input SEMPRE carrega exatamente 1 coluna de Fitness;')
print('   a alternativa explícita é passar Problem.D ao helper, como na linha 32.)')
print('\nUNIVERSALIDADE: CalFitnessPC.m:68 anexa a coluna INCONDICIONALMENTE ⇒')
print('  size(Pmid,2) == D+1 para TODO problema/dimensão ⇒ -1 em 100% das células.')
