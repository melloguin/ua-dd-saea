#!/usr/bin/env python
"""b4 / T11 SMOKE — bateria 5: refs x front-1, timing/sonda, contrato do ⑥, trajetoria.
READ-ONLY."""
import json, sys
import numpy as np, pandas as pd
import pyarrow.parquet as pq
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')

B = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4/exp_main_b4_MMF1_42'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4/'
R = {}
L = [json.loads(l) for l in open(B + '.jsonl')]
man = json.load(open(B + '.manifest.json'))
hdr = [x for x in L if x['rec'] == 'header'][0]
gens = {g['geracao']: g for g in L if g['rec'] == 'b4_gen'}
df1 = pq.read_table(B + '__real.parquet').to_pandas().sort_values('fe_index').reset_index(drop=True)
df2 = pq.read_table(B + '__pop.parquet').to_pandas()
df4 = pq.read_table(B + '__timing.parquet').to_pandas()
F1 = df1[['f0', 'f1']].values.astype(np.float64)
sid2row = {int(s): i for i, s in enumerate(df1.solution_id.values)}
arq = {int(g): df2[df2.geracao == g].solution_id.values.astype(int) for g in df2.geracao.unique()}

def front1(F):
    n = len(F); nd = np.ones(n, bool)
    for i in range(n):
        for j in range(n):
            if i != j and (F[j] <= F[i]).all() and (F[j] < F[i]).any():
                nd[i] = False; break
    return nd

rows = []
prev = None
for g, ev in sorted(gens.items()):
    sids = arq[g]; Farq = F1[[sid2row[s] for s in sids]]
    nd = front1(Farq)
    nd_sids = set(sids[nd])
    refs = set(int(x) for x in ev['ref_ids'])
    rows.append(dict(geracao=g, n_arq=len(sids), n_front1_calc=int(nd.sum()),
                     n_front1_log=ev['n_front1'], refs_no_front1=len(refs & nd_sids),
                     mudou=(prev is not None and refs != prev),
                     f_best0=ev['f_best'][0], f_best1=ev['f_best'][1],
                     dist_min=ev.get('dist_min_arquivo')))
    prev = refs
Q = pd.DataFrame(rows); Q.to_csv(OUT + 'b4_t11_refs_front1.csv', index=False)
R['n_front1_log_eq_calc'] = int((Q.n_front1_calc == Q.n_front1_log).sum()), len(Q)
R['refs_no_front1'] = Q.refs_no_front1.value_counts().sort_index().to_dict()
R['refs_mudaram_em'] = int(Q.mudou.sum()), len(Q) - 1
R['f_best_monotono'] = int((np.diff(Q.f_best0) <= 1e-12).sum()), len(Q) - 1
R['n_front1_traj'] = [int(Q.n_front1_log.iloc[0]), int(Q.n_front1_log.iloc[-1]), int(Q.n_front1_log.max())]

# ---------- front final vs pisos rasos: apenas descritivo ----------
ndf = front1(F1)
R['front_final'] = dict(n_nd=int(ndf.sum()), f0_min=float(F1[ndf, 0].min()), f1_min=float(F1[ndf, 1].min()))
R['front_init'] = dict(n_nd=int(front1(F1[:21]).sum()))

# ---------- timing / sonda ----------
sd = [x for x in L if x['rec'] == 'sonda']; se = [x for x in L if x['rec'] == 'sonda_estratificada']
t_sd = sum(x['tempo_pred_sonda_s'] for x in sd); t_se = sum(x['tempo_pred_s'] for x in se)
R['sonda_tempo'] = dict(soma_sonda=t_sd, soma_estrat=t_se, manifesto=man['timing']['tempo_pred_sonda_s'],
                        soma_4=float(df4.tempo_pred_sonda_s.sum()),
                        razao_4_sobre_manifesto=float(df4.tempo_pred_sonda_s.sum() / man['timing']['tempo_pred_sonda_s']))
R['t_total_4_sobre_5'] = float((df4.tempo_fit_s + df4.tempo_busca_s + df4.tempo_pred_sonda_s).sum() / man['timing']['tempo_total_s'])
R['fe_treino_max_sonda_eq_gen'] = int(sum(1 for x in sd if x['fe_treino_max'] == gens[x['geracao']]['fe_treino_max'])), len(sd)
R['sonda_ok_true'] = int(sum(1 for x in sd if x['ok'])), len(sd)
R['sonda_xhash_igual'] = int(sum(1 for x in sd if x['x_hash'] == man['sonda']['x_hash'])), len(sd)
R['estrat_prevalencia_nd_no_bloco'] = [x['prevalencia_nd_no_bloco'] for x in se][:3]
R['estrat_sigma_rel'] = sorted(set(x['sigma_rel'] for x in se))
R['estrat_sementes_distintas'] = len(set(x['semente_bloco'] for x in se)), len(se)
R['estrat_n_arquivo_eq_ntreino'] = int(sum(1 for x in se if x['n_arquivo'] == gens[x['geracao']]['n_treino'])), len(se)

# ---------- contrato do ⑥ ----------
R['header_campos'] = sorted(hdr.keys())
R['header_tem_run_id'] = 'run_id' in hdr
R['header_tem_sigma_dict'] = 'sigma_dict' in hdr
R['manifest_tem_motivo_parada'] = 'motivo_parada' in man
R['footer'] = [x for x in L if x['rec'] == 'footer'][0]
R['manifest_campanha_id'] = man.get('campanha_id'); R['manifest_repo_hash'] = man.get('repo_hash')
R['manifest_schema_version'] = man.get('schema_version')
R['n_retries'] = man.get('n_retries')

print(json.dumps(R, indent=1, default=str))
