# e103-A25 — bateria de refutação (F5.4)

Veredito: **REFUTADO como classe (3)** → rebaixado a **(d) defeito de instrumentação**,
escopo = espelho de leitura da F5 + bucket. Causa do falso-positivo: (i) decisão
**DI-41** já conhecia e corrigiu o bug (`scripts/final_eval.py:121-132`); (ii) a árvore
CANÔNICA (`ua-dd-saea/data/experiments/`) está correta em 45/45 — só o espelho
`resultados_experimentos/` (montado de `_old/_bucket_raw`) carrega o artefato pré-fix;
(iii) o impacto afirmado no relatório (fantasia 0,05 → 0,10) é aritmeticamente falso:
a duplicação é exata 2×, logo ND(200)=2·ND(100) e a razão é INVARIANTE.

Scripts (rodar com `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`):

| script | o que faz | saída |
|---|---|---|
| `01_censo_camada7.py` | recenso independente da ⑦ nas 45 células (cardinalidade, X duplicado, ND recomputado cheio × dedup, link ⑦×③) | `censo_camada7_45celulas.csv` |
| `02_gate_e_metricas.py` | roda `check_final` (gate DI-08 de hoje) e compara as 5 métricas oficiais ⑦-gravada × ⑦-correta | `gate_check_final_hoje.csv`, `impacto_metrico_camada7.csv` |
| `03_espelho_vs_canonico.py` | espelho × árvore canônica, célula a célula (inode, md5, n, sidecar) | `espelho_vs_canonico.csv` |
| `04_raio_de_alcance.py` | raio de alcance: 360 arquivos do e103 + ⑦ dos 6 configs offline | `raio_camada7_todos_configs.csv` |
| `05_fechamento.py` | canônico ≡ reconstrução de hoje; censo do `_bucket_raw`; teorema da invariância + spacing | `censo_bucket_raw_camada7.csv` |

Todos READ-ONLY sobre dados/artefatos; nada foi escrito fora desta pasta.
