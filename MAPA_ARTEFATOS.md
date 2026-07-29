# MAPA DE ARTEFATOS — ua-dd-saea (auto-contido; para agente SEM contexto)

> **O que é.** O índice de TODO o conhecimento do projeto, com a função de cada artefato e
> QUANDO lê-lo. Se você é um agente novo: leia este mapa, depois siga a ordem de leitura da
> `SPEC_T11_REFINAMENTO_FINAL.md` §1. Caminhos relativos à raiz do repo
> (`/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/`).

## 1. O projeto em 5 linhas

Pipeline experimental de mestrado (defesa ~set/2026): **16 algoritmos SA-MOEA da literatura +
pisos = 24 configs** × **25 problemas** × **30 sementes** × **4 tipos de experimento** (`main`
q=1 · `off` offline · `sweep-{small,medium,big}-{lhs,mvns}` · `batch` q=10) = **20.850 runs**
(`runs_matrix.csv`). Cada run persiste **7 camadas** (①real ②pop ③surrogate+SONDA ④timing
⑤manifesto ⑥jsonl ⑦final-offline). Stacks: 13 configs MATLAB/PlatEMO + 11 Python (BoTorch/
DESDEO/GPy/standalone) em 6 venvs. A rodada-42 (semente 42, 666/695 células OK) foi validada
por DUAS campanhas independentes (143 agentes de código + 38+14 de fidelidade): **zero bugs de
algoritmo**; falta o refinamento final do harness/instrumentação (a campanha T11) antes das 30
sementes (~18.291 h-core).

## 2. ORDEM DE LEITURA para um agente implementador novo

1. `CLAUDE.md` (raiz) → `claude_code_context/CLAUDE.md` — as regras de ouro e a precedência.
2. **`SPEC_T11_REFINAMENTO_FINAL.md`** — a missão atual (o plano supremo do refinamento).
3. **`T11_STATUS.md`** — o que JÁ foi feito da missão (retome do primeiro ☐).
4. `CONTRATO_DE_DADOS.md` — o dicionário das 7 camadas (obrigatório antes de tocar qualquer writer).
5. `f5/PLANO_RODADA_PERFEITA.md` — os defeitos B-01..B-16/I-01..I-13/G-1..G-9 com arquivo:linha,
   número medido e teste de aceitação (a fonte de detalhe nº 1 do T11).
6. `handoff/F5-LAUDO-INSTRUMENTACAO.md` — os 8 itens de instrumentação (I-1..I-8 do laudo).
7. `REGISTRO_DECISOES_IMPLEMENTACAO.md` PARTES **A29-A35** — as decisões DI-41..DI-45 que
   governam o T11 (leia TODAS as 7 partes; o resto do arquivo é histórico p/ consulta).
8. `handoff/T11-PLANO-CONSOLIDADO.md` — a consolidação da torre (vereditos por item + mesa).
9. Por algoritmo, SÓ quando for tocá-lo: `claude_code_context/{10,20,30,40}_*/alg_<X>.md` +
   `f5/relatorios_config/<X>.md` (a dissecação de fidelidade dele).

## 3. Documentos-mestre (raiz)

| Artefato | Função |
|---|---|
| `SPEC_T11_REFINAMENTO_FINAL.md` | **A missão atual** — plano supremo, fases, ordem, aceitação |
| `T11_STATUS.md` | **Rastreador vivo** — checklist do T11; o implementador ATUALIZA a cada item |
| `MAPA_ARTEFATOS.md` | este arquivo |
| `CLAUDE.md` + `claude_code_context/CLAUDE.md` | portas de entrada; regras invioláveis (D81/D97/D29) |
| `CONTRATO_DE_DADOS.md` | dicionário completo das 7 camadas + sonda + jsonl (por config) |
| `REGISTRO_DECISOES_IMPLEMENTACAO.md` | TODAS as decisões DI-01..DI-45 com o porquê (A1-A35) |
| `PROGRESSO.md` / `ORQUESTRACAO_MESTRE.md` | diário do projeto / status board da torre |
| `RUNBOOK_VALIDACAO_42.md` | manual de disparo da rodada-42 (comandos por máquina) |
| `DOSSIE_FIDELIDADE_R1.md` | dossiê D97 (+ **§D9**: as 5 conclusões científicas vinculantes) |
| `HANDOFF_TORRE_COMPLETO.md` | handoff da torre de controle (história completa do projeto) |
| `REGISTRO_OPERACAO_RODADA42.md` | diário operacional O-01..O-18 (tropeços de execução) |
| `FECHAMENTO_semente42.md` + `INVENTARIO_nao_go_semente42.md` | censo final da s42 + as 29 não-go |

## 4. Especificação científica (`claude_code_context/`)

| Artefato | Função |
|---|---|
| `SPEC_experimentos_v5.2.md` | FONTE ÚNICA da verdade científica (consulta pontual, NUNCA integral; §5.1 = teto 12h/DI-44; §17 = export; §L.x = receita por algoritmo) |
| `artifacts/` | machine-readable: `runs_matrix.csv` (20.850) · `seeds.json` (24 alg_ids) · `envs.json` · `params.json` · `anchors.json` · `repos.lock` · `decisions.json` · `characteristics.csv` |
| `00_fundacao/ … 50_analise_R4/` | bundles GERADOS da SPEC por `gen_bundles.py` (nunca editar à mão; regenerar após editar a SPEC) |
| `PROMPT_MESTRE.md` / `REGISTRO_DECISOES_pingpong_v5.md` | molde de prompt / porquê das decisões D53-D100 |

## 5. Código

| Onde | O quê |
|---|---|
| `experiments.py` / `experiments.m` | despachantes Python/MATLAB (retry, manifesto, teto `--teto-s`) |
| `src/` núcleo | `audit_log.py` (⑥) · `manifest.py` (⑤/is_run_done) · `export.py`+`atomic_io.py` (parquets) · `budget.py` (FE/cache D89; K_BATCH/Q_BATCH) · `doe.py` · `naming.py` · `gcs.py` (bucket) · `metrics.py` (métrica oficial + smoke D92) · `experiment.py` (dispatch) |
| `src/` harnesses | `botorch_harness.py` (c262/c154) · `standalone_harness.py` (c122/c149/e81/b5/c311/pisos-off) — SnapshotBuffer, write_run_outputs, dual_write, sonda |
| `src/` runners Python | `c262_qnehvi.py` · `c154_jes.py` · `c122_thetadeadp.py` · `c149_lbnmobo.py` · `e81_qpots.py` · `b5_prob.py` (b5r/b5m) · `c311_tgprmo.py` · `piso_offline.py` (moead_media) · `treed_media.py` · `sobol_batch.py` |
| `src/*.m` | `experiment.m` (harness MATLAB) · `FEBudget.m` · `<alg>_instrument.m`/`<alg>_sonda.m` ×13 |
| `algorithms/` | árvores VENDORIZADAS (PlatEMO 4.2/4.1, b5_Prob-RVEA, c311 framework/, e74 CLMEA_Code) — **NUNCA editar sem re-lacre de âncora** (`anchors.json`/`repos.lock`) |
| `scripts/` | gates: `portao.py` (driver) · `accept.py` · `auditar.py` · `final_eval.py` (⑦) · `preflight.py` · `naoperturbacao.py` · `censo42.py` · `progress.py` · `regressao_q1.py` · drivers de operação `lote42.sh` etc. |
| `tests/` | suíte (394; 1 falha ambiental conhecida: `test_di21_contrato` D-03 consulta bucket real — item do T11) |

## 6. Dados e resultados

| Onde | O quê |
|---|---|
| `data/doe/` (git ✓) · `data/datasets/` (git ✓) · `data/sonda/` | artefatos de entrada bit-a-bit (DoE 11D−1; datasets offline **só sementes 0 e 42**; sonda com f real) |
| `data/experiments/` (gitignored) | runs locais; `_baseline_pre_retrofit/` = INTOCÁVEL |
| `gs://mestrado_experiments` | a CÓPIA OFICIAL da rodada-42 (consolidada pelo autor) |
| `~/Documents/python_repos/mestrado/resultados_experimentos/` | layout de análise do autor (666 células) |
| `f5/` | TODA a análise de fidelidade: 24 relatórios/config · 14 adversariais · métricas/sonda/tempo CSVs · transversais · `RELATORIO_FINAL_F5.md` · `PLANO_RODADA_PERFEITA.md` · `tempo_heatmap_30seeds.html` (projeção 10.173 h-core) |
| `requirements/` + `locks/` | envs e pins (lock = a verdade; pins são decisão do AUTOR/D80) |

## 7. Fatos operacionais que um agente novo precisa saber

- Interpretador dos gates/suíte no Mac: `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python` (SEMPRE por caminho completo).
- Envs por config: `envs.json` é a fonte (env_b5 py3.7 · env_c311 py3.8 · env_e81_qpots · env_main). env_b5/env_c311 existem no Mac (micromamba osx-64) e nas VMs.
- Máquinas: Mac A (MATLAB + envs especiais) · VM-1 `v5-mestrado` · VM-2 `mestrado-v6` · `matlab-vm3`.
- `git push`/tag = SÓ o autor. `git add` sempre explícito (NUNCA `-A`). Suíte SEMPRE antes de commit.
- MATLAB roda com `'parallel',false` (O-09); e103 é serial; teto 12h existe SÓ no stack Python (lacuna aceita).
- Célula "pronta" = `is_run_done` (manifesto ok + fe_final==maxfe + camadas); NÃO confie em `status` sem cruzar `motivo_parada` (história do bug B1).
