#!/usr/bin/env python
"""BATERIA 1 e74/CLMEA — censo estrutural das 25 celulas main (semente 42).
U1,U2,U8,U9,U10 + rotacao 1:1:1 + dedup + desalinhamento (DI-07b) + guards + termino.
Escreve: e74_celulas.csv, e74_gen_eventos.csv (todos os e74_gen das 25), e74_guards.csv
"""
import json, os, glob
import pandas as pd, numpy as np

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/e74'
probs = sorted(os.listdir(ROOT))

rows, allgen, allguard, allboot, allsonda = [], [], [], [], []
for pr in probs:
    base = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    man = json.load(open(base + '.manifest.json'))
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r['rec'] == 'header'][0]
    ftr = [r for r in recs if r['rec'] == 'footer']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    boot = [r for r in recs if r['rec'] == 'e74_boot']
    gu = [r for r in recs if r['rec'] == 'guard']
    so = [r for r in recs if r['rec'] == 'sonda']
    D, M = hdr['D'], hdr['M']

    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')

    g = pd.DataFrame(gens); g['problema'] = pr
    allgen.append(g)
    b = pd.DataFrame(boot); b['problema'] = pr; b['D'] = D; b['M'] = M
    allboot.append(b)
    if gu:
        gg = pd.DataFrame(gu); gg['problema'] = pr; allguard.append(gg)
    s = pd.DataFrame(so); s['problema'] = pr; allsonda.append(s)

    n1 = int((g.estrategia == 1).sum()); n2 = int((g.estrategia == 2).sum()); n3 = int((g.estrategia == 3).sum())
    ac = g.groupby('estrategia').aceito.sum().to_dict()
    slot = g.groupby('estrategia').slot_perdido.sum().to_dict()
    g1 = g[g.estrategia == 1]
    des = g1.n_desalinhado.astype(float)
    # ciclos: geracao = 4c-2+(s-1) -> c = (geracao+2-(s-1))//4
    g['ciclo'] = ((g.geracao + 2 - (g.estrategia - 1)) / 4).astype(int)
    ciclos = int(g.ciclo.max())

    # U1
    maxfe_esp = 31 * D - 1
    init_esp = 11 * D - 1
    fe_dense = bool((real.fe_index.values == np.arange(len(real))).all())
    n_init = int((real.fase == 'init').sum())
    n_opt = int((real.fase == 'opt').sum())
    # U10 aritmetica
    pop_gens = int(pop.geracao.nunique()); pop_max = int(pop.geracao.max())
    tim_rows = len(tim)
    # arquivo do pop por geracao == fe corrente
    popsz = pop.groupby('geracao').size()

    rows.append(dict(
        problema=pr, D=D, M=M, status=man['status'], termino=(ftr[0]['termino'] if ftr else None),
        footer_status=(ftr[0]['status'] if ftr else None),
        maxfe=man['maxfe'], maxfe_esp=maxfe_esp, fe_final=man['fe_final'],
        u1_ok=(man['fe_final'] == maxfe_esp == man['maxfe']), fe_index_denso=fe_dense,
        n_init=n_init, init_esp=init_esp, u2_init_ok=(n_init == init_esp),
        n_opt=n_opt, n_opt_esp=maxfe_esp - init_esp,
        doe_hash=man['doe_hash'][:12], algo_version=man['algo_version'],
        n_geracoes=man['n_geracoes'], pop_gens=pop_gens, pop_max=pop_max,
        u10_pop_ok=(pop_gens == pop_max == man['n_geracoes']),
        timing_rows=tim_rows, n_eventos_gen=len(g), u10_tim_ok=(tim_rows == len(g) + len(boot)),
        ciclos=ciclos, n_s1=n1, n_s2=n2, n_s3=n3,
        rot_1a1=(n1 == n2 and n2 - n3 in (0, 1) and n1 - n3 in (0, 1)),
        ac_s1=int(ac.get(1, 0)), ac_s2=int(ac.get(2, 0)), ac_s3=int(ac.get(3, 0)),
        slot_s1=int(slot.get(1, 0)), slot_s2=int(slot.get(2, 0)), slot_s3=int(slot.get(3, 0)),
        boot_aceitos=int(b.aceitos.sum()), boot_rejeitados=int(b.rejeitados.sum()),
        fe_check=(init_esp + int(b.aceitos.sum()) + int(g.aceito.sum()) == man['fe_final']),
        cache_hits_man=man['cache_hits'],
        guard_cache=int(sum(1 for x in gu if x['name'] == 'cache_hit')),
        guard_dedup=int(sum(1 for x in gu if x['name'] == 'dedup_slot_perdido')),
        guard_outros=json.dumps({k: v for k, v in pd.Series([x['name'] for x in gu]).value_counts().to_dict().items()
                                 if k not in ('cache_hit', 'dedup_slot_perdido')}),
        # desalinhamento DI-07b
        desal_soma=float(des.sum()), desal_media=float(des.mean()), desal_mediana=float(des.median()),
        desal_max=float(des.max()), desal_p90=float(des.quantile(.9)),
        desal_frac_media=float((des / 100.0).mean()), desal_zero=int((des == 0).sum()),
        n_ciclos_s1=len(g1),
        count_med=float(g1['count'].astype(float).median()), count_max=float(g1['count'].astype(float).max()),
        count_zero=int((g1['count'].astype(float) == 0).sum()),
        frac_niv1_med=float(g1.frac_nivel1.astype(float).median()),
        flag_copia=int(g1.flag_copia.astype(bool).sum()),
        n_sonda_blocos=len(s), tempo_total=man['timing']['tempo_total_s'],
    ))
    print(pr, 'ok', flush=True)

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/e74_celulas.csv', index=False)
pd.concat(allgen, ignore_index=True).to_csv(f'{OUT}/e74_gen_eventos.csv', index=False)
pd.concat(allboot, ignore_index=True).to_csv(f'{OUT}/e74_boot.csv', index=False)
pd.concat(allguard, ignore_index=True).to_csv(f'{OUT}/e74_guards.csv', index=False)
pd.concat(allsonda, ignore_index=True).to_csv(f'{OUT}/e74_sonda_eventos.csv', index=False)
pd.set_option('display.width', 300)
print(df.to_string())
print('\n=== AGREGADOS ===')
for c in ['u1_ok', 'fe_index_denso', 'u2_init_ok', 'u10_pop_ok', 'u10_tim_ok', 'rot_1a1', 'fe_check']:
    print(c, int(df[c].sum()), '/', len(df))
print('ciclos total', df.ciclos.sum(), 's1', df.n_s1.sum(), 's2', df.n_s2.sum(), 's3', df.n_s3.sum())
print('slots perdidos s1', df.slot_s1.sum(), 's2', df.slot_s2.sum(), 's3', df.slot_s3.sum())
print('desal soma', df.desal_soma.sum(), 'media global', df.desal_soma.sum() / df.n_ciclos_s1.sum())
