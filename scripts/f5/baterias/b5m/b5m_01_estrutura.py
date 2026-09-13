#!/usr/bin/env python
"""BATERIA b5m #1 — inventario estrutural das 45 celulas (semente 42).
Camadas: (1) __real  (2) __pop  (3) __surrogate  (4) __timing  (5) manifest  (6) jsonl  (7) __final.
Saida: b5m_estrutura.csv  (1 linha/celula)
"""
import json, glob, os, sys
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b5m'


def cells():
    for d in sorted(glob.glob(os.path.join(ROOT, '*', '42'))):
        label = os.path.basename(os.path.dirname(d))
        js = glob.glob(os.path.join(d, '*.jsonl'))
        assert len(js) == 1, d
        stem = js[0][:-len('.jsonl')]
        yield label, d, stem


rows = []
for label, d, stem in cells():
    man = json.load(open(stem + '.manifest.json'))
    recs = [json.loads(l) for l in open(stem + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r.get('rec') == 'header'][0]
    dec = [r for r in recs if r.get('rec') == 'decision']
    snd = [r for r in recs if r.get('rec') == 'sonda']
    ftr = [r for r in recs if r.get('rec') == 'footer']
    grd = [r for r in recs if r.get('rec') == 'guard']
    other = [r for r in recs if r.get('rec') not in ('header', 'decision', 'sonda', 'footer', 'guard')]

    c1 = pd.read_parquet(stem + '__real.parquet')
    c2 = pd.read_parquet(stem + '__pop.parquet')
    c3 = pd.read_parquet(stem + '__surrogate.parquet')
    c4 = pd.read_parquet(stem + '__timing.parquet')
    c7 = pd.read_parquet(stem + '__final.parquet')
    fman = json.load(open(stem + '__final.manifest.json'))

    D = hdr['D']; M = hdr['M']; N = hdr['n_dataset']
    xc = [f'x{i}' for i in range(D)]; fc = [f'f{i}' for i in range(M)]

    busca = c3[c3.regime == 'offline']
    sonda = c3[c3.regime == 'sonda']
    gsel = busca.geracao.dropna().astype(int)
    gset = set(gsel.unique())
    n_ger = man['n_geracoes']
    pop_per_gen = busca.groupby(gsel).size()

    sig = [f'sigma_{j}' for j in range(M)]
    mus = [f'mu_{j}' for j in range(M)]

    r = dict(
        label=label, exp=hdr.get('regime'), problema=hdr['problema'], D=D, M=M, N=N,
        tier=hdr.get('tier'), dist=hdr.get('dist'),
        status=man['status'], motivo_parada=man.get('motivo_parada'),
        maxfe=man['maxfe'], fe_final=man['fe_final'], n_geracoes=n_ger,
        # (1)
        c1_rows=len(c1), c1_all_init=bool((c1.fase == 'init').all()),
        c1_feidx_denso=bool((c1.fe_index.values == np.arange(len(c1))).all()),
        c1_sid_denso=bool((np.sort(c1.solution_id.values) == np.arange(len(c1))).all()),
        # (2)
        c2_rows=len(c2),
        # (3)
        c3_rows=len(c3), c3_regimes='|'.join(sorted(c3.regime.unique())),
        c3_busca=len(busca), c3_sonda=len(sonda),
        c3_ger_min=int(gsel.min()), c3_ger_max=int(gsel.max()),
        c3_ger_denso=(gset == set(range(1, n_ger + 1))),
        c3_ger_nunique=len(gset),
        pop_min=int(pop_per_gen.min()), pop_max=int(pop_per_gen.max()),
        pop_const=bool(pop_per_gen.nunique() == 1),
        c3_rsid_null=bool(busca.real_solution_id.isna().all()),
        c3_sonda_ger_null=bool(sonda.geracao.isna().all()),
        c3_fetm=int(c3.fe_treino_max.iloc[0]), c3_fetm_uniq=int(c3.fe_treino_max.nunique()),
        c3_espaco='|'.join(sorted(c3.espaco_modelo.unique().astype(str))),
        c3_transf_null=bool(c3.transf_tipo.isna().all()),
        c3_flag='|'.join(sorted(c3.modelo_flag.unique().astype(str))),
        c3_predtipo='|'.join(sorted(c3.pred_tipo.unique().astype(str))),
        c3_predscore_null=bool(c3.pred_score.isna().all()),
        c3_predconf_null=bool(c3.pred_confianca.isna().all()),
        c3_sigma_nan=int(c3[sig].isna().sum().sum()),
        c3_sigma_min=float(np.nanmin(c3[sig].values)),
        c3_sigma_neg=int((c3[sig].values < 0).sum()),
        # (4)
        c4_rows=len(c4), c4_fit=float(c4.tempo_fit_s.iloc[0]),
        c4_busca=float(c4.tempo_busca_s.iloc[0]),
        c4_sonda=float(c4.tempo_pred_sonda_s.iloc[0]),
        c4_ger=float(c4.tempo_geracao_s.iloc[0]),
        c4_nacum=int(c4.n_acumulado.iloc[0]),
        # (5)
        m_fitseries=len(man.get('fit_series') or []),
        m_cachehits=man.get('cache_hits'),
        m_tempo_total=man['timing']['tempo_total_s'],
        m_aval_real=man['timing']['tempo_aval_real_s'],
        m_sonda_blocos=man['sonda']['n_blocos'], m_sonda_S=man['sonda']['S'],
        m_has_params=('params' in man),
        m_sigma_keys=len(man.get('sigma_dict') or {}),
        # (6)
        j_lines=len(recs), j_dec=len(dec), j_sonda=len(snd), j_footer=len(ftr),
        j_guard=len(grd), j_other=len(other),
        j_dec_gerdenso=(set(r['geracao'] for r in dec) == set(range(1, n_ger + 1))),
        j_caminhos='|'.join(sorted(set(r['caminho'] for r in dec))),
        j_ndsmembros_max=max(r['n_ds_membros'] for r in dec),
        j_fe_uniq=len(set(r['fe'] for r in dec)),
        j_fe_val=dec[0]['fe'],
        j_pwrong_stats=sum(1 for r in dec if 'p_wrong_stats' in r),
        j_hdr_pesos=('pesos' in hdr) or ('vetores' in hdr) or ('reference_vectors' in hdr),
        j_footer_nfinal=ftr[0].get('n_final') if ftr else None,
        j_footer_nnd=ftr[0].get('n_nd_pos_real') if ftr else None,
        j_footer_status=ftr[0].get('status') if ftr else None,
        j_sonda_npontos=snd[0]['n_pontos'] if snd else None,
        j_sonda_hashchk=snd[0].get('hash_check') if snd else None,
        # (7)
        c7_rows=len(c7), c7_nd=int(c7.nd_pos_real.sum()),
        c7_origem_ger='|'.join(str(v) for v in sorted(set(c7.origem_geracao.astype(int)))),
        c7_osid_null=bool(c7.origem_solution_id.isna().all()),
        fman_n=fman.get('n_final') if isinstance(fman, dict) else None,
        # hashes
        doe_hash_eq=(man['doe_hash'] == man['cp_init_offline']['x_hash']),
        sonda_xhash=man['sonda']['x_hash'],
    )
    rows.append(r)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'b5m_estrutura.csv'), index=False)
pd.set_option('display.width', 400); pd.set_option('display.max_columns', 200)
print(df.shape)
print(df[['label', 'D', 'M', 'N', 'maxfe', 'fe_final', 'n_geracoes', 'c1_rows', 'c2_rows',
          'c3_busca', 'c3_sonda', 'pop_min', 'pop_max', 'j_dec', 'c7_rows', 'c7_nd',
          'c3_sigma_nan', 'j_pwrong_stats', 'm_sonda_blocos']].to_string())
print()
for col in ['c1_all_init', 'c1_feidx_denso', 'c1_sid_denso', 'c3_ger_denso', 'c3_rsid_null',
            'c3_sonda_ger_null', 'c3_transf_null', 'pop_const', 'j_dec_gerdenso',
            'doe_hash_eq', 'c7_osid_null', 'm_has_params', 'c3_predscore_null']:
    print(col, df[col].sum(), '/', len(df))
print()
print('regimes', df.c3_regimes.value_counts().to_dict())
print('flags', df.c3_flag.value_counts().to_dict())
print('predtipo', df.c3_predtipo.value_counts().to_dict())
print('caminhos', df.j_caminhos.value_counts().to_dict())
print('motivo_parada', df.motivo_parada.value_counts().to_dict())
print('fe_uniq', df.j_fe_uniq.value_counts().to_dict())
print('espaco', df.c3_espaco.value_counts().to_dict())
print('c4_rows', df.c4_rows.value_counts().to_dict())
print('m_fitseries', df.m_fitseries.value_counts().to_dict())
print('j_guard', df.j_guard.value_counts().to_dict(), 'j_other', df.j_other.value_counts().to_dict())
print('j_footer', df.j_footer.value_counts().to_dict())
print('sonda npontos', df.j_sonda_npontos.value_counts().to_dict())
print('hashchk', df.j_sonda_hashchk.value_counts().to_dict())
print('fetm uniq', df.c3_fetm_uniq.value_counts().to_dict())
print('fetm == N-1:', int((df.c3_fetm == df.N - 1).sum()))
