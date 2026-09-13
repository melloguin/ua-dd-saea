"""T11/b4 — bateria 7: as CORRECOES da campanha, uma a uma.
Pergunta de cada bloco: o campo existe? o DADO dentro dele e real? ele adiciona
informacao que a s42 nao tinha? READ-ONLY.
"""
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

SM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4'
recs = [json.loads(l) for l in open(f'{SM}/exp_main_b4_MMF1_42.jsonl')]
gens = [r for r in recs if r.get('rec') == 'b4_gen']
man = json.load(open(f'{SM}/exp_main_b4_MMF1_42.manifest.json'))

print('=== I-5 · y_treino_dist: campo novo. O dado e INDEPENDENTE ou DERIVADO? ===')
ok_n = ok_n1 = ok_prev = 0
for g in gens:
    y = g['y_treino_dist']
    ok_n += (y['n'] == g['n_treino'])
    ok_n1 += (y['classe_1'] == round(g['rr'] * g['n_treino']))
    ok_prev += (y['prevalencia_classe_1'] == g['rr'])
n = len(gens)
print(f'  n == n_treino:                      {ok_n}/{n}')
print(f'  classe_1 == round(rr * n_treino):   {ok_n1}/{n}   <= identidade EXATA da fonte')
print(f'  prevalencia_classe_1 == rr:         {ok_prev}/{n}  (bit-a-bit)')
print(f'  classe_0 == n - classe_1:           {sum(1 for g in gens if g["y_treino_dist"]["classe_0"] == g["y_treino_dist"]["n"] - g["y_treino_dist"]["classe_1"])}/{n}')
print('  => o campo e uma REESCRITA de (rr, n_treino), ambos ja presentes na s42.')
print('     Valor: ergonomia + a NOTA semantica. Informacao nova: ZERO.')
print('     (b4_instrument.m:196-211 assume; `n1 = round(rr*n)`, linha 204.)')

print('\n=== I-1 · ref_ids: id REAL ou sentinela? (o padrao que reprovou o c217) ===')
ri = [g['ref_ids'] for g in gens]
print(f'  ref_ids presentes: {len(ri)}/{n} · len==6: {sum(1 for x in ri if len(x) == 6)}/{n}')
print(f'  com QUALQUER -1: {sum(1 for x in ri if any(v == -1 for v in x))}/{n}')
print(f'  todos -1 (sentinela do c217): {sum(1 for x in ri if all(v == -1 for v in x))}/{n}')
real = pq.read_table(f'{SM}/exp_main_b4_MMF1_42__real.parquet').to_pandas()
sids = set(real.solution_id.tolist())
print(f'  todo ref_id existe na ①: {sum(1 for x in ri if all(v in sids for v in x))}/{n}')
print(f'  ref_id < |Arc| daquela geracao: {sum(1 for x, g in zip(ri, gens) if max(x) < g["n_treino"])}/{n}')
print(f'  refs DISTINTAS dentro da geracao: {sum(1 for x in ri if len(set(x)) == 6)}/{n}')
print('  (b4_instrument.m:91 inicializa ref_ids = -ones(...); o -1 SOBREVIVE se '
      'solutionIdOf falhar. No b4 nunca sobrevive.)')

print('\n=== I-2 · REGRA_DO_ROTULO: a regra escrita e a regra do codigo? ===')
print('  texto (sigma_dict): "nao e pior que TODAS as 6 referencias"  [DI-18]')
print('  codigo GetOutput.m:16-19: Output = AND_j ( ANY_k  PopObj(:,k) <= RefPoint(j,k) )')
print('  => a prosa e a formula COINCIDEM. Aplicada na bateria 2 sem ambiguidade.')

print('\n=== I-2b · p0_p1: a declaracao NOVA bate com o codigo-fonte? ===')
print('  sigma_dict: "p0 = MAE da categoria II (rotulo 1, CSEA.m:78); p1 = MAE da categoria I (rotulo 0, CSEA.m:79)"')
print('  CSEA.m:77  IndexGood = TestOut==1;')
print('  CSEA.m:78  p0 = sum(|TestOut(IndexGood)-TestPre(IndexGood)|)/sum(IndexGood)   <= rotulo 1')
print('  CSEA.m:79  p1 = ... (~IndexGood) ...                                          <= rotulo 0')
print('  => declaracao CORRETA, e e exatamente o que a F5 provou por dado (A12).')

print('\n=== corte 0,5 de pred_classe (o sigma_dict declara max ruim=0,4999 / min bom=0,5000) ===')
sur = pq.read_table(f'{SM}/exp_main_b4_MMF1_42__surrogate.parquet').to_pandas()
for r in ['online', 'sonda', 'sonda_estratificada']:
    s = sur[sur.regime == r]
    bom = s[s.pred_classe == 'bom'].pred_confianca
    ruim = s[s.pred_classe == 'ruim'].pred_confianca
    print(f'  {r:22s} n={len(s):6d}  min(L|bom)={bom.min() if len(bom) else float("nan"):.7f}  '
          f'max(L|ruim)={ruim.max() if len(ruim) else float("nan"):.7f}  '
          f'consistencia (bom <=> L>=0,5) = {((s.pred_classe == "bom") == (s.pred_confianca >= .5)).mean():.6f}')
print(f'  mu/sigma/pred_score 100% NULL: '
      f'{all(sur[c].isna().all() for c in ["mu_0", "mu_1", "sigma_0", "sigma_1", "pred_score"])}')

print('\n=== I-3 · tempo_aval_real_s (o handoff conta como conquista da T11) ===')
print(f'  smoke: {man["timing"]["tempo_aval_real_s"]:.6f} s (nao-nulo)')
print('  s42:   nao-nulo em 25/25 celulas (min 0,0304 · max 1,4376) — JA FUNCIONAVA antes da T11.')

print('\n=== I-4 · NO_RETRY (experiments.py:84) — aplicavel ao b4? ===')
print(f'  n_retries no smoke = {man["n_retries"]} ; na s42 = {{0}} nas 25 celulas.')
print('  O b4 nunca falhou nem re-tentou: a correcao e real mas INERTE neste config.')

print('\n=== proveniencia: o que a T11 acrescentou ao manifesto ===')
print(f'  campanha_id = {man.get("campanha_id")!r} (s42: AUSENTE em 25/25)')
print(f'  repo_hash   = {man.get("repo_hash")!r} (s42: chave PRESENTE mas VAZIA em 25/25)')
print(f'  schema_version = {man.get("schema_version")} (s42: 2 — inalterado)')
