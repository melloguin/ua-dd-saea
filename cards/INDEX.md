# cards/INDEX.md — lista canônica de cartões-sessão (1 sessão = 1 cartão, D83)

> Cada linha é uma sessão de implementação. `depende-de` = o cartão que precisa fechar antes.
> `bundle` = o(s) arquivo(s) de `claude_code_context/` que a sessão lê. `status`: ⬜ a fazer · 🟡 em curso · ✅ feito.
> Ao fechar um cartão, escreva `handoff/{ID}.md`. A próxima sessão começa lendo o handoff anterior.
> Ordem de ataque (D84): **Fase 0 → R1 (MATLAB) ∥ R2 (BoTorch) → R3 (standalone) → sub-estudos → R4**.

## Fase 0 — andaime comum
| ID | Tarefa | depende-de | bundle | status |
|---|---|---|---|---|
| F0-01-harness | Limpar imports mortos; despachantes; esteira idempotente; manifesto+logger §17.5 | — | 00_fundacao/01–05 | ✅ |
| F0-02-doe | `src/doe.py` (LHS-maximin próprio D87 + parquet + hash array-decodificado) + gerador do dataset offline (D90) + `seeds.json` (D91) | F0-01 | 00_fundacao/01,05 | ✅ |
| F0-03-export | Wrapper de FE (cache-hit=0 FE D89) + hard-stop + escrita atômica + schemas 3 tabelas + `src/gcs.py` | F0-01 | 00_fundacao/03 | ✅ |
| F0-04-metrica | Esqueleto da camada de métrica + smoke F1 = **1,0433** (D92) | F0-01 | 00_fundacao/04, 50_analise_R4 | ✅ |

## Rodada 1 — MATLAB/PlatEMO (Mac; ∥ com R2)
| ID | Tarefa | depende-de | bundle | status |
|---|---|---|---|---|
| R1-00-harness | Infra transversal MATLAB: `experiments.m`, `src/experiment.m`, `src/hook_output.m` (contrato N.0) | F0-* | 10_rodada1_matlab/00_contrato | ✅ |
| R1-b1 | ParEGO (injeção DoE D94 :29-30) | R1-00 | …/alg_b1_parego | ✅ |
| R1-b3 | K-RVEA | R1-00 | …/alg_b3_krvea | ✅ |
| R1-b4 | CSEA (cap 109; cpu) | R1-00 | …/alg_b4_csea | ✅ |
| R1-e7 | EDN-ARMOEA (injeção DoE D94 :31-32) | R1-00 | …/alg_e7_ednarmoea | ✅ |
| R1-c217 | PC-SAEA (caso-modelo; 2 guardas) | R1-00 | …/alg_c217_pcsaea | ✅ |
| R1-c141 | MMRAEA (porte 3 linhas) | R1-00 | …/alg_c141_mmraea | ✅ |
| R1-e74 | CLMEA (**árvore 4.1 própria, N.0-4.1 — D95**; worker dedicado) | R1-00 | …/alg_e74_clmea | ✅ |
| R1-c238 | EIM (embrulho classdef N.5) | R1-00 | …/alg_c238_eim | ✅ |
| R1-e103 | IBEA-MS offline (**centros √n_dataset — D93**; worker dedicado) | R1-00 | …/alg_e103_ibeams | ✅ |
| R1-pisos | NSGA-II/III, MOEA/D, SMS-EMOA (MOEAD type=1) | R1-00 | …/alg_pisos_online | ✅ |

## Rodada 2 — BoTorch (VM Vertex; ∥ com R1)
| ID | Tarefa | depende-de | bundle | status |
|---|---|---|---|---|
| R2-00-harness | Infra BoTorch (contrato N.1; dual-write GCS) | F0-* | 20_rodada2_botorch/00_contrato | ✅ |
| R2-c262 | qNEHVI | R2-00 | …/alg_c262_qnehvi | ✅ |
| R2-c154 | JES (B9.5 no piloto) | R2-00 | …/alg_c154_jes | ✅ |

## Rodada 3 — standalone (ordem: c122 → b5 → c311 → c149 → e81)
| ID | Tarefa | depende-de | bundle | status |
|---|---|---|---|---|
| R3-00-harness | Infra standalone (venvs isolados; b5×c311 nunca co-importar) | R2-00 | 30_rodada3_standalone/00_contrato | ✅ |
| R3-c122 | θ-DEA-DP (f_min/f_max pela assinatura) | R3-00 | …/alg_c122_thetadeadp | ✅ (3/3 gates VERDES, 29e8539) |
| R3-b5 | Prob-RVEA/MOEA-D (b5r/b5m; venv env_b5) | R3-00 | …/alg_b5_prob | ⬜ |
| R3-c311 | TGPR-MO (venv env_c311) | R3-00 | …/alg_c311_tgprmo | ⬜ |
| R3-c149 | LBN-MOBO (reconstruir loop; **HVI-greedy D96**) | R3-00 | …/alg_c149_lbnmobo | ✅ (3/3 pilotos VERDES, timebox 6h/10h, a664599; validação da torre DI-23) |
| R3-e81 | qPOTS (env botorch 0.16.1 próprio) | R3-00 | …/alg_e81_qpots | ✅ (18/18 ×3, ZDT1 1,99h<8h, 5bde3db; validação da torre DI-24) |
| R3-piso-off | MOEA/D-média (DESDEO mode 12, D77; env_b5) | R3-b5 | …/alg_piso_offline_moead_media | ⬜ |

## Sub-estudos e análise
| ID | Tarefa | depende-de | bundle | status |
|---|---|---|---|---|
| SUB-batch | Large-batch q=10 (D66) | R2,R3 | 40_subestudos/batch_largebatch | ⬜ |
| SUB-sweep | Sweep offline (tier×dist; run_id sweep-{tier}-{dist}) | R1-e103,R3 | 40_subestudos/sweep_offline | ⬜ |
| SUB-varN | Varredura N dos pisos (D65) | R1-pisos | 40_subestudos/varredura_N_pisos | ⬜ |
| R4-analise | Métricas + testes + análise por característica (camada de análise — **o autor refina/implementa, D100**) | bateria completa | 50_analise_R4 | ⬜ |

**Pré-flight (antes de F0):** `python scripts/preflight.py` — preenche content-hashes do `repos.lock`, valida `anchors.json` contra o código, checa placeholders.
