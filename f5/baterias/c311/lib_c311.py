"""Biblioteca comum das baterias de fidelidade do c311 (TGPR-MO) — F5.3a-v1.1.
READ-ONLY sobre resultados_experimentos/ e data/. Escreve só em f5/baterias/c311/.
"""
import json, os, glob, math
import numpy as np
import pandas as pd

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c311'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c311'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
EXCLUIDA = 'swap_big-mvns_MMF16_20'   # REPROVADA-F5.1 (B1 / gpy_bfgs_linalg)

DIM = {  # D por problema (31D-1 = N do tier small)
}

def celulas():
    """Lista (label, dir, prefixo) das 54 células válidas."""
    out = []
    for label in sorted(os.listdir(RAIZ)):
        d = os.path.join(RAIZ, label, '42')
        if not os.path.isdir(d):
            continue
        if label == EXCLUIDA:
            continue
        mans = [f for f in os.listdir(d) if f.endswith('.manifest.json') and '__final' not in f]
        assert len(mans) == 1, (label, mans)
        pref = mans[0].replace('.manifest.json', '')
        out.append((label, d, pref))
    return out

def carrega(d, pref, camadas=('real','surrogate','timing','final','pop')):
    man = json.load(open(os.path.join(d, pref + '.manifest.json')))
    evs = [json.loads(l) for l in open(os.path.join(d, pref + '.jsonl')) if l.strip()]
    dfs = {}
    for c in camadas:
        p = os.path.join(d, f'{pref}__{c}.parquet')
        dfs[c] = pd.read_parquet(p) if os.path.exists(p) else None
    return man, evs, dfs

def meta(label, man):
    """tier/dist/problema a partir do label + manifesto."""
    if label.startswith('swap_'):
        tok, prob = label[5:].split('_', 1)
        tier, dist = tok.split('-')
        exp = f'sweep-{tier}-{dist}'
    else:
        tier, dist, prob, exp = 'small', 'lhs', label, 'off'
    return dict(label=label, exp=exp, tier=tier, dist=dist, problema=prob)

def gera_int(df):
    return df['geracao'].dropna().astype(int)

def busca(sur):
    return sur[sur['regime'] == 'offline']

def sonda(sur):
    return sur[sur['regime'] == 'sonda']

def mucols(df):
    return sorted([c for c in df.columns if c.startswith('mu_')])

def sigcols(df):
    return sorted([c for c in df.columns if c.startswith('sigma_')])

def xcols(df):
    return sorted([c for c in df.columns if c.startswith('x') and c[1:].isdigit()],
                  key=lambda s: int(s[1:]))

def fcols(df):
    return sorted([c for c in df.columns if c.startswith('f') and c[1:].isdigit()],
                  key=lambda s: int(s[1:]))

def nd_mask(F):
    """máscara não-dominada (minimização) — O(n^2), n<=~200 aqui."""
    n = F.shape[0]
    keep = np.ones(n, bool)
    for i in range(n):
        if not keep[i]:
            continue
        d = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if d.any():
            keep[i] = False
    return keep

def salva(df, nome):
    p = os.path.join(OUT, nome)
    df.to_csv(p, index=False)
    print('->', p, df.shape)
    return p
