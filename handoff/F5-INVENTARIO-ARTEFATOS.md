# INVENTÁRIO DE ARTEFATOS — validação de fidelidade da rodada-42 (F5)

> **Para o agente validador de fidelidade.** Este é o mapa COMPLETO dos artefatos do projeto
> `ua-dd-saea` relevantes à sua missão, com função, conteúdo, uso recomendado e score de
> importância (0-10). Leia primeiro o `handoff/F5-VALIDACAO-FIDELIDADE.md` (a missão e a
> doutrina); este inventário é o "onde está cada evidência". Caminhos relativos à raiz
> `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/`.

## Grupo 1 — Missão e doutrina

| Artefato | Função | Conteúdo | Como usar na fidelidade | Score |
|---|---|---|---|---|
| `handoff/F5-VALIDACAO-FIDELIDADE.md` | O handoff da SUA missão: doutrina, protocolo, pipeline, caveats | Doutrina D97/D29/§17.5.1; protocolo de 3 classes (A-mecanismo, B-saúde, C-protocolo) com score 0-10; pipeline em 6 passos; priors já julgados; os 8 caveats anti-falso-alarme (B1 status mascarado, ⑥ sem footer, um-config-uma-máquina, BBOB empírico, c154 ⚪, N provisório…) | LEIA PRIMEIRO, inteiro. É o contrato da tarefa — define o que entregar e as armadilhas que invalidariam sua análise | **10** |
| `CONTRATO_DE_DADOS.md` (raiz) | O dicionário DEFINITIVO de tudo que um run persiste — a "parte da SPEC" consolidada e didática sobre os outputs | As 7 camadas (① real ② pop ③ surrogate+SONDA ④ timing ⑤ manifesto ⑥ jsonl ⑦ __final) coluna a coluna: schema, tipos, semântica, quem grava, quando; a sonda §17.2.2; o jsonl DI-10 evento a evento; sigma_dict; particularidades POR CONFIG (o que cada algoritmo põe em cada camada) | Consulta permanente ao ler qualquer parquet/jsonl: é aqui que você descobre o que cada coluna significa e o que é NULL-por-desenho vs NULL-por-bug | **10** |
| `claude_code_context/SPEC_experimentos_v5.2.md` | A fonte única da verdade do experimento inteiro | §17 (export), **§17.5.1 (o contrato de auditoria: pergunta × campo do log × veredito — o molde do seu método)**, §17.2.2 (sonda), **§L.1-L.19 (a RECEITA exata de cada algoritmo: kernels, acqf, RNG, hazards)**, §20/Anexo J (números-âncora ±3σ), Anexo D (decisões D53-D100), §6.4 (tabelão de parâmetros Balde B), §5 (orçamento/teto), §12-§15 (métricas/análise) | Consulta pontual (NUNCA leitura integral): a receita L.x é o gabarito da Classe A; §17.5.1 é o roteiro da auditoria; Anexo J dá as faixas-guia da Classe B | **9** |
| Bundles `claude_code_context/{10,20,30,40}_*/alg_*.md` (1 por algoritmo) | O checklist de fidelidade POR ALGORITMO, gerado da SPEC | Para cada config: patches de fidelidade K.3 com arquivo:linha, guardas L/N, contratos de RNG/FE, hazards conhecidos, âncoras próprias, classificação D29 (🔴🔵🟠🟣🟢) de cada divergência código×paper JÁ mapeada na implementação | O gabarito da Classe A por config: confirme que cada patch/guarda listado se manifesta nos DADOS (⑥ eventos, ⑤ params) — divergência nova = classificar via D29 e escalar | **10** |
| `handoff/F5-INVENTARIO-ARTEFATOS.md` | Este arquivo | O mapa de evidências | Navegação | 8 |

## Grupo 2 — Os DADOS da rodada-42 (a matéria-prima)

| Artefato | Função | Conteúdo | Como usar na fidelidade | Score |
|---|---|---|---|---|
| `data/experiments/{exp}/{alg}/*` (Mac + VMs) | O RESULTADO: as ~666 células ok da semente 42, 7 camadas por run | Por run: `*_real.parquet` (① toda avaliação real X,F float32), `*_pop.parquet` (② populações/geração), `*_surrogate.parquet` (③ μ/σ por geração + blocos de SONDA), `*_timing.parquet` (④ série n×tempo_fit), `*.manifest.json` (⑤ params/sigma_dict/guards/motivo_parada/q/tier), `*.jsonl` (⑥ o filme: eventos por iteração), `*__final.parquet` (⑦ ND final na f real — só offline) | É O OBJETO DA VALIDAÇÃO. Classe A no ⑥+⑤; Classe B na ③-sonda+curvas de ①; Classe C em ①/hash/contagens. ⚠ B1: triar por `motivo_parada`, não por `status`. ⚠ dados de 1 config vêm TODOS da mesma máquina | **10** |
| `data/sonda/` (50 arquivos) | A RÉGUA COMUM entre surrogates: pontos Sobol canônicos + f real deles | Por problema: `sonda_{problema}.parquet` (2000 pts online / 20000 offline, X + f REAL) + sidecar de hashes | O instrumento-mestre da Classe B: junte μ da ③-sonda de cada run com o f real daqui → correlação/RMSE por bloco → a curva "o surrogate aprendeu?" comparável ENTRE algoritmos (mesmos pontos, custo 0 FE) | **10** |
| `gs://mestrado_experiments` (bucket GCS) | Espelho dual-write Python + único lar da ③ dos 5 volumosos | `experiments/{alg}/...` — c154/c122/e81/c149/c262 são **③ bucket-only** (D54/D58); resto = espelho | Para auditar a ③ dos 5 volumosos, baixe do bucket. ⚠ o ⑥ do bucket NUNCA tem footer (upload precede o fechamento) — use o ⑥ local | **8** |
| `data/doe/` (1502 arq.) | O DoE 11D−1 como artefato bit-a-bit (D63) | `doe_{problema}_{semente}.npy` + hashes | Classe C: CP-init — o ① de todo run main/batch deve começar EXATAMENTE com estes pontos (pareamento por hash); accept/auditar já checam, você confere o veredito | **7** |
| `data/datasets/` (1570 arq.) | Os datasets offline (off/sweep) como artefatos determinísticos (D90) | `ds_{problema}_{semente}_{tier}_{dist}.parquet` + manifests com x_hash/f_hash | Classe C offline: o ① do run deve SER o dataset (binding por hash, auditar.py faz); tier/dist do ⑤ deve casar com o nome | **7** |
| `data/bbob_pf_cache/` | Frentes "verdadeiras" EMPÍRICAS dos 7 BBOB (D72/§12.1) | Caches de front ND por problema BBOB | Métricas dos BBOB são RELATIVAS a este cache — HV>1,1 é normal, comparação com literatura NÃO vale. Use para IGD/IGD+ dos BBOB | **7** |

## Grupo 3 — Ferramentas (gates e métrica)

| Artefato | Função | Conteúdo | Como usar na fidelidade | Score |
|---|---|---|---|---|
| `src/metrics.py` | A camada de métrica OFICIAL do estudo | HV/IGD/IGD+/GD/spacing com normalização (ideal,nadir) da S.5 (D69), ref-HV=1,1, smoke-gates `hv_smoke_bbob_f1()`=1,04333 (D92) | NUNCA reimplemente métrica: importe daqui. Rode os 2 smoke-gates ANTES de qualquer conta — se falharem, PARE | **9** |
| `scripts/portao.py` (+`accept.py`, `auditar.py`, `final_eval.py`) | O driver dos gates objetivos por run | portao roteia por config: accept (FE exato, camadas, CP-init, checks dedicados R3) + auditar (sonda/blocos/schema/binding offline) + final_eval --check (⑦) ; `--varredura` = o data/ inteiro | Passo 2 do pipeline: TODA célula que entrar na sua análise passa pelo portão VERDE primeiro. ⚠ rode no env_main do Mac (B3: sem pyarrow o accept dá falso-VERDE) ⚠ B2: aborto por cache aparece errado | **8** |
| `scripts/censo42.py` | O censo da rodada-42 contra o grid | Conta células por exp/status/máquina vs runs_matrix | Passo 1: mapear 666 ok + ~29 não-ok e EXPLICAR cada ausência. ⚠ herda o token errado `cache_cap` (B2) — confira abortos manualmente | **7** |
| `scripts/progress.py` | Tabelas de timing/censo dos manifests | Wall-clock por célula/config | Classe B/custo: a tabela de tempos é o insumo do M7 (dimensionamento) e revela células anômalas (rápidas demais = suspeitas) | **6** |

## Grupo 4 — Priors, registros e análises já feitas

| Artefato | Função | Conteúdo | Como usar na fidelidade | Score |
|---|---|---|---|---|
| `DOSSIE_FIDELIDADE_R1.md` | O dossiê VIVO de fidelidade — o formato do seu entregável | Escopo acordado com o autor; estado por algoritmo; **c217 9/10 e e81 9/10 JÁ ACEITOS**; curvas consolidadas dos 15 (item 1); **notas de comportamento v2 pós-retrofit** (b5r 7,0 · b5m 5,0 c/ flag GP degenerado · c311 7,5…); pontos de atenção por config | Seus PRIORS + seu MOLDE: não parta do zero, atualize este dossiê com a semente 42; as notas v2 mostram o padrão de escrita que o autor espera | **9** |
| `REGISTRO_DECISOES_IMPLEMENTACAO.md` | O cérebro: TODAS as decisões DI-01..DI-40 com o porquê | PARTES A1-A28: cada decisão de implementação, ratificações do autor, bugs achados/corrigidos, caveats declarados (confounders do c154, N provisório DI-39, c154 fora do batch DI-40…) | Quando algo parecer "estranho", cheque aqui ANTES de acusar: muita coisa estranha é DECISÃO DECLARADA (ex.: cache-hit=0 FE, σ extensão nossa). Também: a lista do que virou caveat de análise D97 | **8** |
| `REGISTRO_OPERACAO_RODADA42.md` | O diário operacional O-01..O-18 do disparo | Tropeços de execução com causa provada; **O-16/O-18: validação cruzada entre máquinas** (MATLAB bit-idêntico; Python drift por microarquitetura ~1,5% pior caso; regra um-config-uma-máquina; caveat BBOB_F17) | Contexto para anomalias operacionais (célula lenta, path, symlink) e a BASE da regra cross-machine que você deve respeitar nas comparações | **8** |
| `validacao_cruzada_indicadores.html` | A análise-molde de indicadores (O-18) | 24 células × 5 métricas com fronts ND, trajetórias HV×FE, dispersão entre máquinas, tabelas etiquetadas | O MOLDE do seu passo 3: reuse o método (e o código que o gerou) para as 666 células | **7** |
| Journal da validação final: `~/.claude/projects/-Users-gmello/1dad1ee9-8028-4d8e-a5cf-e0264dcc7966/subagents/workflows/wf_c451718a-b88/journal.jsonl` | Os 32 relatórios fresh-eyes por config/dimensão (linhas `type:result`) | Por config: nota, achados (310, 52 ALTA), e um bloco `comportamento_smoke` (veredito do comportamento nos smokes) | Pré-leitura por config: os achados ALTA do seu config são hipóteses a confirmar/refutar com os dados da 42; os `comportamento_smoke` são um 2º par de olhos | **7** |
| `handoff/*.md` (1+ por cartão: R1-*, R2-*, R3-*, T6-T9) | Os relatórios de implementação/validação de cada algoritmo | O que foi implementado, gates rodados, definições em aberto, números dos pilotos | Contexto por config: como o algoritmo nasceu, o que já foi validado ao vivo na implementação | **7** |
| `HANDOFF_TORRE_COMPLETO.md` | O contexto integral do projeto (filme + regras + mapa) | Cronologia F0→freeze, regras invioláveis, lições, backlog | Onboarding geral se você precisar de contexto além da fidelidade | **7** |
| Kits de leitura: `~/Desktop/kits_escritores/` (22 zips) | OS PAPERS de cada família de algoritmo | 1 zip por família com o(s) artigo(s) em .md + análises | Classe A exige o paper: é contra ELE que o mecanismo se valida (com a bússola D29 e o alg_*.md como guia do que já foi conciliado) | **9** |

## Grupo 5 — Machine-readable (artifacts/)

| Artefato | Função | Conteúdo | Como usar na fidelidade | Score |
|---|---|---|---|---|
| `artifacts/runs_matrix.csv` | O grid completo (20.850 runs; 695 na s42) | run_id, exp, alg, problema, semente, q, tier, dist, stack, env | A LISTA-MESTRA do censo: toda célula da s42 se explica contra ela (ok/⚪/ausente-por-DI-40/falha) | **9** |
| `artifacts/params.json` | Índice rápido dos parâmetros por config (Balde B, §6.4) | model/acqf/optimize_acqf/refit/knobs por config (incl. batch_q10 DI-37) | Classe A: confira o ⑤.params de cada run contra isto (e contra §6.4 em dúvida — a SPEC é a dona) | **7** |
| `artifacts/seeds.json` | O mapa de semeadura D62 | alg_id por config (24), SeedSequence (base, alg_id, iter, uso_id) | Classe C/RNG: explica por que configs diferentes têm streams diferentes na MESMA semente | **7** |
| `artifacts/characteristics.csv` | A matriz 25×8 de características dos problemas (D71/D98) | multimodalidade, separabilidade, geometria da frente etc. por problema | Classe B transversal: agrupe o desempenho por característica (o método da §15) para achar padrões e anomalias | **7** |
| `artifacts/envs.json` | alg→env + pins de thread (D79) | 6 ambientes, threads=1 | Contexto: qual venv produziu cada dado; anomalia de env explica anomalia de dado | **6** |
| `artifacts/decisions.json` | Índice das decisões D53-D100 | id → título/supersedes/seções | Atalho para achar a decisão que explica um comportamento | **6** |
| `artifacts/anchors.json` + `repos.lock` | Âncoras de patch + SHAs dos repos vendorizados | Âncora por patch de fidelidade; SHA por árvore | Prova de que o código validado é o código rodado (Classe C, se necessário) | **5** |
| `RUNBOOK_VALIDACAO_42.md` | O manual do disparo (expectativas oficiais) | Comandos por máquina, custos conhecidos, **§7: expectativa das células ⚪ do c154** | A lista do que É esperado estar ausente/⚪ — antes de classificar ausência como falha | **6** |
