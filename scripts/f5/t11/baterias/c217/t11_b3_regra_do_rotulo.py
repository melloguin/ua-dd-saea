# -*- coding: utf-8 -*-
"""T11/c217 — BATERIA 3: TENTAR APLICAR a REGRA_DO_ROTULO.
Passo a passo, e onde ela morre. Depois: quanto IMPORTA a identidade do Pmid
(sensibilidade), e o descasamento semantico do passo (3).
READ-ONLY (le data/sonda/*.parquet e resultados_experimentos/).
"""
import json, glob, os, math
from collections import Counter
import pandas as pd, numpy as np

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
OUT = os.path.join(RAIZ, 'ua-dd-saea/f5/t11/baterias/c217')
SONDA = os.path.join(RAIZ, 'ua-dd-saea/data/sonda')
rng = np.random.default_rng(20260731)

# ---------- passo 1 da regra: ler pmid_ids ----------
print('== PASSO 1 da REGRA: ler `pmid_ids` do evento c217_gen ==')
for rot, pat in [('s42 (25 celulas)', os.path.join(RAIZ, 'resultados_experimentos/c217/*/42/*.jsonl')),
                 ('smoke T11 (1 celula)', os.path.join(RAIZ, 'evidencia_T11/smoke_matlab/experiments/main/c217/*.jsonl'))]:
    tot = pres = neg = 0
    for f in glob.glob(pat):
        for line in open(f, encoding='utf-8'):
            line = line.strip()
            if not line: continue
            d = json.loads(line)
            if d.get('rec') != 'c217_gen': continue
            tot += 1
            if 'pmid_ids' in d:
                pres += 1
                ids = d['pmid_ids'] if isinstance(d['pmid_ids'], list) else [d['pmid_ids']]
                neg += all(v == -1 for v in ids)
    print('  %-22s geracoes=%5d | com o campo=%5d | 100%% sentinela(-1)=%5d | UTILIZAVEIS=%d'
          % (rot, tot, pres, neg, pres - neg))

# ---------- passo 3: precisa do f da referencia via ① ----------
cel = os.path.join(RAIZ, 'resultados_experimentos/c217/MMF1/42')
real = pd.read_parquet(glob.glob(os.path.join(cel, '*__real.parquet'))[0])
print('\n== PASSO 3: `solution_id` validos na ① de MMF1/42: %d..%d ; "-1" existe? %s'
      % (real.solution_id.min(), real.solution_id.max(), bool((real.solution_id == -1).any())))
print('   => a regra termina no passo 3 em 100%% dos blocos: nao ha referencia a avaliar.')

# ---------- controle interno: a chamada IRMA que FUNCIONA ----------
print('\n== CONTROLE INTERNO (o A/B dentro do MESMO arquivo) ==')
for rot, pat in [('s42', os.path.join(RAIZ, 'resultados_experimentos/c217/*/42/*.jsonl')),
                 ('smoke', os.path.join(RAIZ, 'evidencia_T11/smoke_matlab/experiments/main/c217/*.jsonl'))]:
    tot = ftm_ok = 0
    for f in glob.glob(pat):
        for line in open(f, encoding='utf-8'):
            line = line.strip()
            if not line: continue
            d = json.loads(line)
            if d.get('rec') != 'c217_gen': continue
            tot += 1
            ftm_ok += d.get('fe_treino_max') is not None
    print('  %-6s fe_treino_max (solutionIdOf com fatia 1:D) NAO-NULO em %d/%d' % (rot, ftm_ok, tot))

# ---------- sensibilidade: quanto importa a identidade do Pmid? ----------
print('\n== SENSIBILIDADE: a identidade do Pmid muda o rotulo? (proxy aleatorio) ==')
def dom(a, b):
    """+1 se a domina b, -1 se b domina a, 0 incomparavel (minimizacao)."""
    le = np.all(a <= b, axis=-1); lt = np.any(a < b, axis=-1)
    ge = np.all(a >= b, axis=-1); gt = np.any(a > b, axis=-1)
    return np.where(le & lt, 1, np.where(ge & gt, -1, 0))

res = []
for prob in ['MMF1', 'ZDT1', 'BBOB_F37', 'DTLZ2']:
    cel = os.path.join(RAIZ, 'resultados_experimentos/c217/%s/42' % prob)
    sb = glob.glob(os.path.join(cel, '*__surrogate.parquet'))
    if not sb: continue
    sur = pd.read_parquet(sb[0])
    real = pd.read_parquet(sb[0].replace('__surrogate', '__real'))
    art = pd.read_parquet(os.path.join(SONDA, 'sonda_%s.parquet' % prob))
    fcols_a = [c for c in art.columns if c.startswith('f') and c[1:].isdigit()]
    fcols_r = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    Fs = art[fcols_a].to_numpy(float)          # f VERDADEIRO dos 2000 pontos Sobol
    Fr = real[fcols_r].to_numpy(float)         # f dos pontos reais (①)
    jl = glob.glob(os.path.join(cel, '*.jsonl'))[0]
    gens = {}
    for line in open(jl, encoding='utf-8'):
        line = line.strip()
        if not line: continue
        d = json.loads(line)
        if d.get('rec') == 'c217_gen': gens[d['geracao']] = d
    snd = sur[sur.regime == 'sonda']
    for g, blk in list(snd.groupby('geracao'))[:6] + list(snd.groupby('geracao'))[-6:]:
        g = int(g)
        if g not in gens: continue
        ev = gens[g]; nP = ev['n_Pmid']; arc = ev['arc_size']
        pred = blk.pred_score.to_numpy(float)
        N = len(pred)
        Fs = art[fcols_a].to_numpy(float)[:N]      # bloco online = linhas [0:N] do artefato
        pool = np.arange(min(arc, len(Fr)))
        aucs, fr0 = [], []
        for _ in range(60):                                   # 60 sorteios de Pmid-proxy
            idx = rng.choice(pool, size=min(nP, len(pool)), replace=False)
            nref = len(idx)
            ref = Fr[idx[[(j+1) % nref for j in range(N)]]]    # regra: (j+1) mod n, 0-based
            lab = dom(Fs, ref)
            aucs.append(float(np.mean(np.sign(pred) == lab)))
            fr0.append(float(np.mean(lab == 0)))
        res.append(dict(problema=prob, g=g, n_Pmid=nP, arc=arc,
                        acordo_med=np.mean(aucs), acordo_min=np.min(aucs), acordo_max=np.max(aucs),
                        amplitude=np.max(aucs)-np.min(aucs), frac_incomparavel=np.mean(fr0),
                        frac_pred0=float(np.mean(pred == 0))))
R = pd.DataFrame(res)
R.to_csv(os.path.join(OUT, 't11_c217_regra_sensibilidade.csv'), index=False)
print(R.groupby('problema')[['acordo_med', 'amplitude', 'frac_incomparavel', 'frac_pred0']]
      .agg(['mean', 'max']).round(4).to_string())
print('\n  amplitude (max-min do acordo sobre 60 sorteios de Pmid) — mediana global: %.4f ; max: %.4f'
      % (R.amplitude.median(), R.amplitude.max()))
print('  fracao de pares (sonda x referencia) INCOMPARAVEIS por dominancia: mediana %.4f'
      % R.frac_incomparavel.median())
print('  fracao de pred_score==0 (contradicao do modelo): mediana %.4f' % R.frac_pred0.median())
