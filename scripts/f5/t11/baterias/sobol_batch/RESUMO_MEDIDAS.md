# sobol_batch · T11 — índice das medidas (todas re-medidas nesta bateria)

| script | o que mede | saída |
|---|---|---|
| `t11_b1_mecanismo.py` | re-medição integral do mecanismo nas 5 células da s42 (orçamento, DoE, query-joia, seeds, KS, oráculo, q, ②, ③, sonda, ④, guards, término, campos T11) | `b1_celulas.csv` (5×70), `b1_geracoes.csv` (1.000), `b1_ks.csv` (94) |
| `t11_b2_correcoes.py` | as correções T11 no smoke POS-T11 preservado (`evidencia_T11/smoke_python`, q=1) + ponte pré×pós | `b2_resumo.json`, `b2_smoke_eventos.csv` (200) |
| `t11_b3_transversal.py` | `tempo_aval_real_s` nas 421 células online da s42; DI-10 por config; pareamento do DoE | `b3_manifestos_s42.csv` (666), `b3_di10_por_config.csv` (18) |
| `t11_b4_rerun_q10.py` | **o smoke que a campanha não fez**: runner de HOJE (HEAD 9ad0138) em q=10, 5/5 problemas, tempdir; bit-identidade ①②④ contra a s42 | `b4_rerun_q10.csv` (5×40) |

Números-âncora: query-joia 1.000/1.000 lotes · `n_front1` 1.000/1.000 correto (q=10) ·
`tempo_aval_real_s` 0,0176–1,5387 s (era 0,0 exato em 5/5) · ①②④ **bit-idênticas**
pré×pós-T11 em 5/5 (dX=dF=0,0) · G-7 RUIM na s42 × OK no pós-T11.

Dados READ-ONLY: `resultados_experimentos/sobol_batch/q10_*/42/` ·
`evidencia_T11/smoke_python/experiments/batch/sobol_batch/` ·
tempdir do re-run: `/var/folders/76/.../T/f5t11_sobol_q10_cgdevkur` (fora do repo).
