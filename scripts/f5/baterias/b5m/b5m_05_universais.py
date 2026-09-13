#!/usr/bin/env python
"""BATERIA b5m #5 — fechamento das universais U1-U12 + determinismo + timing.

  U1  FE real = 31D-1 (small) / 2.000 (medium); ① = dataset, 100% `init`, fe_index denso
  U2  doe_hash == hash do artefato do dataset (binding por hash) + dataset_path
  U3  1 fit por config (④ 1 linha; fit_series 1)
  U4  cadencia da sonda: offline = 1 bloco de 20.000 (regime declarado)
  U5  join POSICIONAL sonda x gabarito: max|ΔX| == 0 (bit-a-bit float32)
  U6  WAPE/cobertura no espaco CRU (b5 nao transforma) — reusa f5/sonda_f52e.csv
  U7  ④: fit + busca == tempo_geracao_s (sonda EXCLUIDA) — invariante declarada
  U8  fe_treino_max == N-1 constante em TODA linha (busca + sonda)
  U9  guards do ⑥ == agregados do ⑤ (cache_hits, n_retries)
  U10 aritmetica entre camadas: |③busca| = pop x n_ger; |⑥ decision| = n_ger;
      |⑦| = pop; f_best/n_front1 do ⑥ recomputados da ③
  U11 (offline) real_solution_id NULL — sem infill => sem erro de fantasia por infill
  U12 ⑦: ND recomputado == nd_pos_real; link posicional (ger,linha) -> ③ bit-a-bit
  + DETERMINISMO: off/{P} x swap_small-lhs_{P} devem ser BIT-IDENTICOS (mesmo
    dataset D90 small-lhs, mesma semente) — prova de reprodutibilidade do LHS
    semeado (patch _patch_lhs_seeding) e de todo o pipeline RNG.

Saida: b5m_universais.csv
"""
import glob, json, os, sys
import numpy as np, pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
sys.path.insert(0, REPO); os.chdir(REPO)
OUT = os.path.join(REPO, 'f5', 'baterias', 'b5m')

labs = [os.path.basename(os.path.dirname(d))
        for d in sorted(glob.glob(os.path.join(RES, 'b5m', '*', '42')))]

rows = []
for lab in labs:
    st = glob.glob(os.path.join(RES, 'b5m', lab, '42', '*.jsonl'))[0][:-6]
    man = json.load(open(st + '.manifest.json'))
    recs = [json.loads(l) for l in open(st + '.jsonl') if l.strip()]
    hdr = recs[0]
    dec = [r for r in recs if r.get('rec') == 'decision']
    prob = hdr['problema']; D = hdr['D']; M = hdr['M']; N = hdr['n_dataset']
    xc = [f'x{i}' for i in range(D)]; fc = [f'f{i}' for i in range(M)]
    c1 = pd.read_parquet(st + '__real.parquet')
    c3 = pd.read_parquet(st + '__surrogate.parquet')
    c4 = pd.read_parquet(st + '__timing.parquet')
    c7 = pd.read_parquet(st + '__final.parquet')
    b = c3[c3.regime == 'offline']; s = c3[c3.regime == 'sonda']
    n_ger = int(b.geracao.max()); pop = len(b) // n_ger

    # U2 — binding do dataset por hash (recomputa do arquivo lido)
    dpath = hdr.get('dataset_path')
    ds_ok, ds_dx = None, None
    if dpath and os.path.exists(dpath):
        import hashlib
        dd = pd.read_parquet(dpath)
        xcols = [c for c in dd.columns if c.startswith('x') and c[1:].isdigit()]
        Xa = dd[sorted(xcols, key=lambda c: int(c[1:]))].values.astype(np.float32)
        ds_dx = float(np.abs(Xa - c1[xc].values.astype(np.float32)).max())
        h = hashlib.sha256(np.ascontiguousarray(Xa, dtype=np.float32).tobytes()).hexdigest()
        ds_ok = (h == man['doe_hash']) or (ds_dx == 0.0)

    # U5 — join posicional sonda x gabarito
    sp = os.path.join('data', 'sonda', f'sonda_{prob}.parquet')
    gab = pd.read_parquet(sp)
    gxc = sorted([c for c in gab.columns if c.startswith('x') and c[1:].isdigit()],
                 key=lambda c: int(c[1:]))
    dX = float(np.abs(gab[gxc].values.astype(np.float32)[:len(s)]
                      - s[xc].values.astype(np.float32)).max())

    # U10 — f_best / n_front1 do ⑥ recomputados da ③
    from src.problems import _nds_filter
    mus = b[[f'mu_{j}' for j in range(M)]].values.astype(np.float64).reshape(n_ger, pop, M)
    ok_fb, ok_nf = 0, 0
    for r in dec:
        g = r['geracao'] - 1
        fb = np.asarray(r['f_best'], dtype=np.float64)
        if np.allclose(fb, mus[g].min(axis=0), rtol=0, atol=1e-6):
            ok_fb += 1
        if int(r['n_front1']) == int(len(_nds_filter(mus[g]))):
            ok_nf += 1

    # U12
    F7 = c7[fc].values.astype(np.float64)
    ndre = np.zeros(len(c7), bool)
    ndre[_nds_filter(F7.astype(np.float32).astype(np.float64))] = True
    X = b[xc].values.reshape(n_ger, pop, D)
    gl = c7.origem_geracao.values.astype(int); ll = c7.origem_linha.values.astype(int)

    rows.append(dict(
        label=lab, problema=prob, D=D, M=M, N=N,
        U1_N_formula=(N == 31 * D - 1) or (N in (2000, 50000)),
        U1_maxfe=man['maxfe'] == N, U1_fe_final=man['fe_final'] == N,
        U1_c1=len(c1) == N, U1_init=bool((c1.fase == 'init').all()),
        U1_feidx=bool((c1.fe_index.values == np.arange(N)).all()),
        U2_ds_hash_ok=ds_ok, U2_ds_dx=ds_dx, U2_dpath=os.path.basename(dpath or ''),
        U3_c4_rows=len(c4), U3_fitseries=len(man['fit_series']),
        U4_blocos=man['sonda']['n_blocos'], U4_S=man['sonda']['S'], U4_c3_sonda=len(s),
        U5_maxdX=dX,
        U7_fit=float(c4.tempo_fit_s.iloc[0]), U7_busca=float(c4.tempo_busca_s.iloc[0]),
        U7_ger=float(c4.tempo_geracao_s.iloc[0]),
        U7_soma_ok=bool(abs(float(c4.tempo_fit_s.iloc[0]) + float(c4.tempo_busca_s.iloc[0])
                            - float(c4.tempo_geracao_s.iloc[0])) < 1e-2),
        U7_sonda_excluida=bool(float(c4.tempo_geracao_s.iloc[0])
                               < float(c4.tempo_fit_s.iloc[0]) + float(c4.tempo_busca_s.iloc[0])
                               + float(c4.tempo_pred_sonda_s.iloc[0]) - 1e-9),
        U8_fetm_uniq=int(c3.fe_treino_max.nunique()), U8_fetm=int(c3.fe_treino_max.iloc[0]),
        U8_ok=bool(c3.fe_treino_max.nunique() == 1 and c3.fe_treino_max.iloc[0] == N - 1),
        U9_guards=sum(1 for r in recs if r.get('rec') == 'guard'),
        U9_cache=man.get('cache_hits'), U9_retries=man.get('n_retries'),
        U10_c3=len(b) == pop * n_ger, U10_dec=len(dec) == n_ger,
        U10_c7=len(c7) == pop, U10_fbest=ok_fb, U10_nfront=ok_nf, U10_dec_n=len(dec),
        U11_rsid_null=bool(b.real_solution_id.isna().all()),
        U11_c2=len(pd.read_parquet(st + '__pop.parquet')),
        U12_nd=bool((ndre == c7.nd_pos_real.values).all()),
        U12_link=bool((c7[xc].values == X[gl - 1, ll]).all()),
        U12_ger_ultima=bool((gl == n_ger).all()),
    ))
    print(lab, 'U5dX=%g U10 fbest=%d/%d nfront=%d/%d' %
          (dX, ok_fb, len(dec), ok_nf, len(dec)), flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'b5m_universais.csv'), index=False)
pd.set_option('display.width', 400); pd.set_option('display.max_columns', 80)
booleans = [c for c in df.columns if df[c].dtype == bool]
print('\n=== booleanas (contagem VERDADEIRO / 45) ===')
for c in booleans:
    print('%-22s %d/45' % (c, int(df[c].sum())))
print('U2_ds_hash_ok', df.U2_ds_hash_ok.sum(), '/', df.U2_ds_hash_ok.notna().sum(),
      ' maxdX dataset:', df.U2_ds_dx.max())
print('U5 max|dX| global:', df.U5_maxdX.max())
print('U10 f_best fecha:', int((df.U10_fbest == df.U10_dec_n).sum()), '/45  total decisoes',
      int(df.U10_dec_n.sum()), ' fecham', int(df.U10_fbest.sum()))
print('U10 n_front1 fecha:', int((df.U10_nfront == df.U10_dec_n).sum()), '/45  fecham',
      int(df.U10_nfront.sum()))
print('U9 guards total', int(df.U9_guards.sum()), 'cache', int(df.U9_cache.sum()),
      'retries', int(df.U9_retries.sum()))
print('U4 blocos', df.U4_blocos.value_counts().to_dict(), 'S', df.U4_S.value_counts().to_dict())

# ── DETERMINISMO: off/{P} == swap_small-lhs_{P} bit-a-bit ───────────────────
print('\n=== DETERMINISMO off x swap_small-lhs (bit-a-bit) ===')
for p in ['DTLZ2', 'MMF16_20', 'WFG9', 'ZDT1', 'ZDT4']:
    a = glob.glob(os.path.join(RES, 'b5m', p, '42', '*.jsonl'))[0][:-6]
    c = glob.glob(os.path.join(RES, 'b5m', 'swap_small-lhs_' + p, '42', '*.jsonl'))[0][:-6]
    eq = {}
    for lay in ['real', 'surrogate', 'final']:
        A = pd.read_parquet(a + f'__{lay}.parquet')
        B = pd.read_parquet(c + f'__{lay}.parquet')
        cols = [x for x in A.columns if x not in ('algoritmo', 'problema', 'semente')]
        eq[lay] = bool(A.shape == B.shape and
                       A[cols].fillna(-9e9).equals(B[cols].fillna(-9e9)))
    ma = json.load(open(a + '.manifest.json')); mb = json.load(open(c + '.manifest.json'))
    print('%-10s ①=%s ③=%s ⑦=%s  doe_hash igual=%s  n_ger %d/%d' %
          (p, eq['real'], eq['surrogate'], eq['final'],
           ma['doe_hash'] == mb['doe_hash'], ma['n_geracoes'], mb['n_geracoes']))
