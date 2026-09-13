#!/usr/bin/env python
"""C7 — ESTRUTURA/LEDGER nas 25 celulas da s42: U1 (FE=31D-1), U2 (DoE 11D-1 bit-a-bit
contra o artefato), U4 (cadencia da sonda + finalProbe), U7 (invariante de tempo),
U9 (guards ⑥ ≡ ⑤), U10 (aritmetica entre camadas, c0), E10 (orcamento de aquisicao).
READ-ONLY.
"""
import json, os, hashlib
import numpy as np, pandas as pd, pyarrow.parquet as pq

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238'
S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'

rows = []
for prob in sorted(os.listdir(S42)):
    b = f'{S42}/{prob}/42/exp_main_c238_{prob}_42'
    man = json.load(open(b + '.manifest.json'))
    recs = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r.get('rec') == 'header'][0]
    ftr = [r for r in recs if r.get('rec') == 'footer']
    gl = sorted([r for r in recs if r.get('rec') == 'c238_gen'], key=lambda r: r['geracao'])
    snd = [r for r in recs if r.get('rec') == 'sonda']
    grd = [r for r in recs if r.get('rec') == 'guard']
    M, D = hdr['M'], hdr['D']
    real = pq.read_table(b + '__real.parquet').to_pandas()
    # U1
    u1 = (len(real) == 31 * D - 1) and (man['fe_final'] == man['maxfe'] == 31 * D - 1)
    fe_denso = bool((np.sort(real.fe_index.values) == np.arange(len(real))).all()) if 'fe_index' in real else None
    sid_unico = int(real.solution_id.nunique() == len(real)) if 'solution_id' in real else None
    # U2 — DoE contra o artefato
    init = real[real.fase == 'init'] if 'fase' in real else real.head(11 * D - 1)
    u2_n = len(init) == 11 * D - 1
    dpath = f'{DOE}/{prob}/doe_{prob}_42.parquet'
    dX_f32 = dX_f64 = np.nan; hash_ok = None
    if os.path.exists(dpath):
        d = pq.read_table(dpath).to_pandas()
        xc = [c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
        xd = [c for c in d.columns if c.startswith('x') and c[1:].isdigit()]
        A = init[xc].values.astype(np.float64); B = d[xd].values.astype(np.float64)[:len(A)]
        dX_f64 = float(np.abs(A - B).max())
        dX_f32 = float(np.abs(A - B.astype(np.float32).astype(np.float64)).max())
        h = hashlib.sha256(np.ascontiguousarray(B, dtype='<f8').tobytes()).hexdigest()
        hash_ok = (h == man.get('doe_hash'))
    # U4 — cadencia
    S = man['sonda']
    gs = S['geracoes']; ng = len(gl)
    cad_ok = all((g == 1) or (g % 2 == 0) for g in gs)
    final_ok = (ng in gs)
    blocos_ok = (len(gs) == S['n_blocos'] == len(snd))
    # U7 — invariante de tempo
    viol = sum(1 for r in gl if (r.get('tempo_fit_s', 0) + r.get('tempo_busca_s', 0)) > r.get('tempo_geracao_s', 0) + 1e-12)
    # U9 — guards
    guards = {}
    for r in grd:
        k = r.get('tipo') or r.get('guard') or r.get('motivo') or 'guard'
        guards[k] = guards.get(k, 0) + 1
    # U10 — ledger
    pop = pq.read_table(b + '__pop.parquet').to_pandas()
    g2 = pop.geracao.nunique()
    tam_ok = all(len(pop[pop.geracao == g]) == (11 * D - 1 - 1) + g for g in sorted(pop.geracao.unique()))
    ult = pop[pop.geracao == pop.geracao.max()]
    dup_ult = int(len(ult) - ult.solution_id.nunique()) if 'solution_id' in ult else None
    n_opt = int((real.fase == 'opt').sum()) if 'fase' in real else np.nan
    c0 = n_opt + man.get('cache_hits', 0) - ng
    rows.append(dict(problema=prob, D=D, M=M, n_real=len(real), esperado=31 * D - 1, u1=int(u1),
                     fe_denso=fe_denso, sid_unico=sid_unico,
                     n_init=len(init), init_esperado=11 * D - 1, u2_n=int(u2_n),
                     dX_f32=dX_f32, dX_f64=dX_f64, doe_hash_ok=hash_ok,
                     n_gens=ng, n_blocos=S['n_blocos'], cad_ok=int(cad_ok), final_ok=int(final_ok),
                     blocos_ok=int(blocos_ok), S_lin=S['n_linhas'], n_falhas=S['n_falhas'],
                     viol_tempo=viol, guards=json.dumps(guards), cache_hits=man.get('cache_hits'),
                     g2=g2, g2_esperado=ng + 1, tam2_ok=int(tam_ok), dup_ult=dup_ult,
                     n_opt=n_opt, c0=c0, termino=(ftr[0]['termino'] if ftr else None),
                     status=man['status'], cp_init=(ftr[0].get('cp_init') if ftr else None),
                     aval_aquisicao=10 * D * 200 * ng))
A = pd.DataFrame(rows)
A.to_csv(f'{OUT}/estrutura_s42.csv', index=False)
pd.set_option('display.width', 250)
print(A[['problema', 'D', 'n_real', 'esperado', 'u1', 'n_init', 'init_esperado', 'dX_f32', 'doe_hash_ok',
         'n_gens', 'n_blocos', 'cad_ok', 'final_ok', 'viol_tempo', 'cache_hits', 'g2', 'g2_esperado',
         'tam2_ok', 'dup_ult', 'c0', 'termino']].to_string(index=False))
print()
print('U1  FE == 31D-1 e fe_final==maxfe : %d/25 ; fe_index denso: %d/25 ; solution_id unico: %d/25 ; SOMA FE = %d' % (
    A.u1.sum(), A.fe_denso.sum(), A.sid_unico.sum(), A.n_real.sum()))
print('U2  init == 11D-1 : %d/25 ; max|dX| vs artefato ARREDONDADO p/ float32 = %.3g (EXATO em %d/25)' % (
    A.u2_n.sum(), A.dX_f32.max(), int((A.dX_f32 == 0).sum())))
print('    max|dX| contra o float64 CRU = %.3g (meio-ULP float32) ; doe_hash confere em %d/25' % (
    A.dX_f64.max(), int(A.doe_hash_ok.sum())))
print('U4  cadencia g==1 v g%%2==0 : %d/25 ; finalProbe (ultima geracao coberta): %d/25 ; blocos ⑤≡⑥: %d/25' % (
    A.cad_ok.sum(), A.final_ok.sum(), A.blocos_ok.sum()))
print('    total de blocos = %d ; linhas de sonda = %d ; n_falhas = %d' % (
    A.n_blocos.sum(), A.S_lin.sum(), A.n_falhas.sum()))
print('U7  violacoes de fit+busca<=tempo_geracao : %d em %d geracoes' % (A.viol_tempo.sum(), A.n_gens.sum()))
print('U9  censo de guards do ⑥ :', A.guards.value_counts().to_dict(), '; cache_hits do ⑤ =', A.cache_hits.unique().tolist())
print('U10 ② tem n_gens+1 geracoes : %d/25 ; tamanho (init-1)+g : %d/25 ; duplicatas na ultima ②: %d' % (
    int((A.g2 == A.g2_esperado).sum()), A.tam2_ok.sum(), A.dup_ult.sum()))
print('    ledger n_gens = n_opt + cache_hits - c0  ->  c0 unico = %s' % A.c0.unique().tolist())
print('E10 avaliacoes da aquisicao (10D x 200 x n_gens) = %d' % A.aval_aquisicao.sum())
print('    termino:', A.termino.value_counts().to_dict(), '| status:', A.status.value_counts().to_dict(),
      '| cp_init:', A.cp_init.value_counts().to_dict())
