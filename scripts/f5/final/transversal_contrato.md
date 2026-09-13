```
BATERIA UNIVERSAL — CONFORMIDADE CONTRATUAL FINAL (censo congelado, 16.811 células · 24 configs · 28 problemas)
Método: streaming censo-driven, O-21 (rodapé ⑥ = autoridade), READ-ONLY. Execução: bateria 16.811/16.811 células (129s, 21/08 23:46) + agregação RE-EXECUTADA nesta sessão (22/08) — tabela abaixo reproduzida por recomputação, não copiada. Spot-check bruto de 6 células (classe1-real, teto, quimera, footer-de-outro-run, teto-EST40, sem-rodapé-com-dado-cheio): 6/6 conferem com a bateria.

== TABELA FINAL POR CONFIG (pronta p/ dissertação) ==
config,N,classe1_conforme,classe2_teto_DI4344,classe2_failed_doc,classe3_inexplicado,taxa_plena_pct,taxa_contratual_pct,reais_N,reais_c1,reais_c2,reais_c3,camada7_off
b1,732,731,0,0,1,99.9,99.9,31,31,0,0,-
b3,804,804,0,0,0,100.0,100.0,58,58,0,0,-
b4,791,791,0,0,0,100.0,100.0,53,53,0,0,-
b5m,729,729,0,0,0,100.0,100.0,30,30,0,0,699/729
b5r,836,836,0,0,0,100.0,100.0,90,90,0,0,806/836
c122,798,702,83,0,13,88.0,98.4,60,60,0,0,-
c141,840,839,0,0,1,99.9,99.9,90,90,0,0,-
c149,812,738,50,1,23,90.9,97.2,90,45,25,20,-
c154,698,260,346,78,14,37.2,98.0,60,0,60,0,-
c217,840,839,0,0,1,99.9,99.9,90,90,0,0,-
c238,734,720,0,0,14,98.1,98.1,89,75,0,14,-
c262,782,625,111,31,15,79.9,98.1,90,60,22,8,-
c311,55,48,0,0,7,87.3,87.3,0,0,0,0,55/55
e103,778,778,0,0,0,100.0,100.0,89,89,0,0,45/778
e7,724,724,0,0,0,100.0,100.0,60,60,0,0,-
e74,839,839,0,0,0,100.0,100.0,90,90,0,0,-
e81,811,788,14,0,9,97.2,98.9,82,60,14,8,-
moead,840,840,0,0,0,100.0,100.0,90,90,0,0,-
moead_media,835,835,0,0,0,100.0,100.0,90,90,0,0,805/835
nsga2,835,835,0,0,0,100.0,100.0,85,85,0,0,-
nsga3,840,838,0,0,2,99.8,99.8,90,90,0,0,-
smsemoa,840,840,0,0,0,100.0,100.0,90,90,0,0,-
sobol_batch,8,7,0,1,0,87.5,100.0,0,0,0,0,-
treed_media,10,9,0,0,1,90.0,90.0,0,0,0,0,10/10
TOTAL,16811,15995,604,111,101,95.1,99.4,1597,1426,121,50,2420/3243

TAXA PLENA (classe 1) = 15.995/16.811 = 95,1% · TAXA CONTRATUAL (classe 1 + classe 2 sancionada) = 16.710/16.811 = 99,4% · classe 3 = 101/16.811 = 0,6%.

== O QUE FOI MEDIDO (denominadores) ==
- Cobertura: bateria == censo_final.csv, 16.811/16.811, 0 duplicatas; diretório presente 16.811/16.811.
- Camadas por regime: núcleo ①②③④⑤⑥ presente em 16.790/16.811; as 21 faltas de parquet são TODAS células failed-com-rodapé (classe 2f — "0 parquets ⇒ nada analisável", incapacidade documentada). ⑦ (__final, só regime offline): 2.420/3.243 — ausência NÃO invalida (pós-hoc; D102.9 Processo B; e103 45/778 = F30-C1/T5, D81 já escalada no F30, recuperável via final_eval.py).
- ⑥: header válido 16.811/16.811 · rodapé presente 16.712/16.811 (99 sem rodapé) · malformadas 0 em 1.670/1.670 células escaneadas linha-a-linha (tier3 = 1.597 reais + 73 ondas antigas).
- ⑤ completo: 16.468/16.811; os 343 incompletos são exclusivamente células failed/sem-rodapé ou legado ondas-antigas (campanha_id/params ausentes); nenhuma célula classe 1 moderna tem ⑤ incompleto (verificado por construção: zero falhas "man5" na lista classe 3).
- ①: fe_index DENSO 16.790/16.790 com parquet (0 violações) · ledger init = 11D−1 em 100% dos online com parquet (0 violações; offline: init == todas as linhas) · orçamento 31D−1 exato em 100% das classe 1.
- SINTÉTICOS (delta F30): delta = ∅ — 0 de 15.214 células sintéticas com mtime ⑥ pós-corte F30 (15/08 00:28:53); herdam o veredito F30 integralmente. Exatamente as 1.597 reais são pós-corte.
- REAIS 1.597 (integrais) = DDMOP7 594 · RE21 566 · ESTOQUE40 437:
  · RE21: 566/566 classe 1 (123/123 FE exato, denso, init 43, ⑤ completo, 0 malformadas).
  · DDMOP7: 549 classe 1 (526/526 exato) + 17 ⚪ teto + 14 failed-doc (dacefit, c154) + 14 classe 3 (sem rodapé, todas c149).
  · ESTOQUE40: 311 classe 1 (1239/1239 exato) + 90 ⚪ teto + 36 classe 3 (sem rodapé: c238 14 · c262 8 · e81 8 · c149 6).

== CLASSE 3 (101 = 99 sem rodapé + 1 trunc + 1 failed-override); lista célula-a-célula em conformidade_final_celulas.csv ==
b1 1 (BBOB_F17/8 quimera ⑥≠⑤, laudo b1) · c122 13 · c141 1 · c149 23 · c154 14 · c217 1 · c238 14 (EST40 com dado CHEIO 1239/1239 mas ⑥ sem rodapé — O-21-inválido) · c262 15 · c311 7 · e81 9 (incl. batch/ZDT4/42 trunc não-teto) · nsga3 2 (DTLZ3/17 = rodapé de OUTRO run abortado por licença MATLAB, override por laudo; MMF1/14 sem rodapé) · treed_media 1. Motivos censo: checkpoint_em_andamento 71 · vazio 27 · orcamento 3.

== RECONCILIAÇÕES O-21 (censo × rodapé: 637 divergências, regra aplicada) ==
- motivo teto_wall (615): 604 → classe 2 ⚪ teto (rodapé ok, orçamento parcial, DI-43/44: comparar em FE comum) · 4 → classe 1 (rodapé mostra orçamento COMPLETO; rótulo do manifesto obsoleto) · 7 → classe 2f (rodapé failed).
- failed com rodapé (112): 111 classe 2f (98 sintéticas + 14 DDMOP7/dacefit — motivos: checkpoint_em_andamento 87, vazio 16, teto_wall 7, erro_Forbidden 1) + 1 override classe 3 (nsga3/DTLZ3/17).
- Fora do censo (não entra no denominador): b1/BBOB_F37/15 (⚪ teto sem rodapé, fe 302/309 — regra de leitura no laudo b1); 60 failed do b1 que o despachante excluiu do censo.
- Não medido: re-scan linha-a-linha das 15.141 sintéticas fora do tier3 (sancionado pelo contrato: "sintéticos = só delta"; delta medido = ∅).

== ARQUIVOS ==
- Tabela final: /private/tmp/claude-501/-Users-gmello/16c0ba84-843b-49d1-9ce6-6cecc418b734/scratchpad/conformidade_final_configs.csv (verificada == recomputação, 13/13 colunas × 25/25 linhas)
- Célula-a-célula (classe/o21/falhas): /private/tmp/claude-501/-Users-gmello/16c0ba84-843b-49d1-9ce6-6cecc418b734/scratchpad/conformidade_final_celulas.csv (16.811)
- Bateria bruta: /private/tmp/claude-501/-Users-gmello/16c0ba84-843b-49d1-9ce6-6cecc418b734/scratchpad/bateria_universal_celulas.csv · script: bateria_universal_final.py · agregador: agrega_final2.py (mesmo diretório)
```