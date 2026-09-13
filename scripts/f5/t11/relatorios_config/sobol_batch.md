# RELATÓRIO DE FIDELIDADE T11 — `sobol_batch` · Sobol scrambled (piso do batch) · protocolo v1.1

**Escopo executado.** As **5 células da s42** (`q10_{DTLZ2, MMF16_20, WFG9, ZDT1, ZDT4}`/42 — o config inteiro da rodada-42) **re-medidas do zero**, mais **dois corpora POS-T11 que eu mesmo levantei**: (a) o smoke Python preservado em `evidencia_T11/smoke_python/experiments/batch/sobol_batch/` — que o handoff T11 §15.2, o `LEIA-ME.md` da evidência **e o meu próprio briefing** dizem NÃO existir (**errata 17**, §4.0); (b) um **re-run do runner de hoje (HEAD `9ad0138`) em q=10 nas 5 células, em tempdir**, que fecha a lacuna deixada pelo smoke da campanha (ele rodou **q=1**, regime que não existe no grid). Volumes re-medidos: **11.029 linhas de ①** (1.029 init + 10.000 infills), **1.211.829 de ②**, **0 de ③** (schema 29–49 col.), **1.000 de ④**, **1.015 de ⑥**, **10.000 pontos Sobol recomputados bit-a-bit**, **94 testes KS**, **11.029 avaliações recomputadas na função real**, **421 manifestos online da s42** varridos, **1.000 eventos** do re-run q=10 + **200** do smoke. Config **SEM artigo** ⇒ Entrega 2 = N/A, substituída pelo **PAPEL DE CONTROLE** (§5).

---

## 1. Ficha do mecanismo

`sobol_batch` (**alg_id=22**, D37/D66/DI-33) é o **piso ONLINE do sub-estudo large-batch**: a ablação *"e se lotearmos ao acaso?"*. Por iteração: `seed_it = iteration_seed(seed_base('sobol_batch',42), 22, g, 0, bits32=True)` → `scipy.stats.qmc.Sobol(d=D, scramble=True, seed=seed_it).random(10)` → projeção `x_nat = xl + u·(xu−xl)` → avaliação na função **REAL** via `FEBudget`. Sem surrogate, sem aquisição, sem população: a ② é o arquivo cumulativo, a ③ sai vazia, não há sonda, `tempo_fit_s=NULL`. Início pareado (`doe_{p}_42.parquet`, 11D−1 LHS, D63/D87/D88, nunca regenerado). Orçamento `11D−1 + 200·q = 11D−1 + 2.000` (D66), hard-stop exato (D21/D61). `env_main`, 1 core, threads pinadas (D79). Grid: **150 linhas** (`runs_matrix.csv`), `exp=batch`, **q=10 em 150/150**, 5 problemas × 30 sementes.

**Divergências sancionadas nomeadas:** (i) **DI-33 + `sigma_dict`** — o scrambling de Owen é **por ITERAÇÃO**, enquanto a letra da D37/§V-B.2 diz "por semente" (S5, item de ratificação do D97); (ii) **DI-13.2** — `tempo_fit_s = NULL`, não 0,0; (iii) **CONTRATO §6.1 / DI-16.1** — sem sonda e ③ vazia por desenho; (iv) **DI-08** — sem ⑦; (v) **U10** — ② com 201 gerações (0..200), uma a mais que e81/c149; (vi) **DI-43 (novo na T11)** — checkpoint atômico a cada 25 iterações; (vii) **contrato_61.json (T11-G6)** — o mínimo DI-10 exigível deste config é `{f_best, n_front1}`, com `tempo_fit_s` e `tempo_busca_s` declarados não-aplicáveis.

**A propriedade única no roster:** sendo determinístico dada a semente e sem modelo, a trajetória inteira é **recomputável dos dados** — a query-joia não é identidade parcial, é reconstrução total dos 10.000 pontos.

---

## 2. DISSECAÇÃO DOS ASPECTOS

### 2.1 Tabela-resumo (**28 aspectos** — numeração da F5 preservada para rastreabilidade; S13/S14/S15 já eram um bloco narrativo único; T27–T31 são novos da T11)

| # | aspecto | classe | verificab. | resultado-síntese (re-medido) |
|---|---|---|---|---|
| S1 | Orçamento `11D−1+200·q` + hard-stop | (2) D66/D21/D61 | direta | **5/5** exato (2.109/2.131/2.219/2.241/2.329); `fe_index` e `solution_id` densos e ordenados em 11.029/11.029; `init` prefixo estrito 5/5 |
| S2 | CP-init = DoE do artefato, bit-a-bit | (2) D63/D87/D88 | direta | **5/5** bit-idêntico em float32; Δ_f64 máx **1,907e-6** (WFG9, ULP de f32 em xu=44); `doe_hash` ⑤≡⑥≡sidecar 5/5 |
| **S3** | ★ **QUERY-JOIA: lote Sobol recomputado** | **(1)** | direta | **1.000/1.000 lotes** e 10.000/10.000 pontos bit-idênticos em f32; Δ_f64 máx **2,98e-8** (1,907e-6 WFG9) |
| S4 | Semeadura `iteration_seed(42,22,g,0)` | (2) D62/D91/DI-33 | direta | **1.000/1.000**; 200 seeds distintos/célula; `seed(g=1)=933708677` idêntico nos 5 problemas **e no smoke POS-T11** |
| **S5** | ★ scrambling "por semente" (letra) × "por iteração" (implementado) | (2) DI-33 + `sigma_dict` | direta + contrafactual (F5) | CD **1,19×–6,43×** pior que sequência única; ΔIGD+ +1,8% a +16,0% (mediana +8,2%) — **dentro do piso de ruído** (58,98%) |
| S6 | Scrambling de Owen ATIVO | **(1)** D37 | direta | **2.000/2.000 pontos distintos** por célula (5/5); contrafactual sem scramble ⇒ 10 pontos únicos, 1º na origem |
| S7 | `q=10` ponta a ponta | (2) D36/D66 | direta | ⑤ 5/5, header 5/5, **1.000/1.000** eventos, `fe = 11D−1+10g` em 1.000/1.000 |
| S8 | K=200 e `2000 % q == 0` | (2) D66 | direta | `n_geracoes=200` 5/5; ④ com 200 linhas 5/5; hard-stop parcial **estruturalmente inalcançável** |
| S9 | Projeção [0,1]^D → bounds NATIVOS | **(1)** | direta | fecha nas 2 células de bounds ≠[0,1]; **0 violações** de bound em 11.029 linhas |
| S10 | Uniformidade dos X da fase `opt` | **(1)** | direta | KS: **0 rejeições em 94**; p mín **0,616**; média 0,50001–0,50099; var 0,08319–0,08347 (1/12=0,08333) |
| S11 | Caveat q não-potência-de-2 | (2) declarado no runner | direta (F5) | CD(q=10) melhor que CD(q=8) em **4/5**; q=16 melhor em 5/5 ⇒ o driver é **K**, não a potência |
| S12 | ① é f(x) REAL (oráculo) | **(1)** | direta | 11.029 linhas recomputadas: rel. **mediana ≤4,1e-8**, **máx 4,09e-5** (WFG9), ≥98,4% ≤1e-6 |
| S13 | O "vazio declarado": ③ vazia + sonda `nao_se_aplica` + `tempo_fit_s=NULL` | (2) CONTRATO §6.1 / DI-16.1 / DI-13.2 | direta | ③ 0 linhas × 5 com 29–49 colunas; `sonda.status='nao_se_aplica'` 5/5, **0 recs `sonda`**; `tempo_fit_s` NULL em **1.000/1.000** |
| S16 | Invariante de timing DI-13.10 | (2) DI-13.10 | direta | `busca ≤ tempo_geracao_s` em **1.000/1.000**; inv-2 vácua (0 sondas) |
| S17 | ② = arquivo cumulativo, 201 gerações | (2) U10 | direta | 1.211.829 linhas; tamanho `11D−1+10g` exato em **1.005/1.005** grupos; off-by-one vs e81/c149 |
| S18 | Guardas / dedup D57-D89 | (2) D57/D89 | direta | **0 eventos guard**; `cache_hits=0` ⑤≡⑥ 5/5; **0 X duplicados** em 11.029 |
| S19 | ⑦ ausente por desenho | (2) DI-08 | direta | `upload_status` marca `__final.*` = `absent` 5/5 |
| S20 | Pareamento do DoE | **(1)** D88 | direta | **1 único `doe_hash` por problema** em 18–20 células online/problema (re-varrido) |
| S21 | Ambiente / pins / grid | (2) D79/D80/DI-31/DI-33 | direta-declarativa (corroborada) | 5/5 `env_main`, numpy 2.4.6/scipy 1.17.1; grid 150 linhas, q=10 em 150/150 |
| S22 | Término e mescla do ⑤ | (2) DI-13.1/D23 | direta | `motivo_parada='orcamento'` 5/5; **footer duplo** 10/10 |
| **S23** | 🔧 `n_front1` no evento de geração | **(2) CORRIGIDO** T11-A6/I-03 | direta | s42: **0/1.000**. POS-T11: **1.000/1.000 presente E CORRETO** (NDS recomputado), faixa 5–221 |
| **S24** | 🔧 `tempo_aval_real_s` num runner ONLINE | **(2) CORRIGIDO** T11-G7/I-02 | direta | s42: **0,0 exato em 5/5** (único em 421 células online). POS-T11: **0,0176–1,5387 s**, e **cobre o DoE** |
| **S25** | 🔧 ⑤ sem `params` | **(2) CORRIGIDO** T11-C2/I-07 | direta | s42: ausente 5/5. POS-T11: presente 5/5, 14 chaves derivadas de `q/D/M/maxfe` |
| **T27** | 🆕 Checkpoint atômico periódico (DI-43) | (2) DI-43 | direta | **8 checkpoints/célula** (K=25); custo **0,221–0,293 s** = **12,3%–44,7% do wall** |
| **T28** | 🆕 `campanha_id` + `repo_hash` + schema v2 | (2) B-03/I-09 | direta | s42: schema **1**, sem `campanha_id`, `repo_hash=''`. POS-T11: schema **2**, `9ad0138aa9a4_2026-07-31` 5/5 |
| **T29** | 🆕 Gate G-7 (`contrato_61.json`) discrimina | (2) T11-G6 | direta | **RUIM na s42** (`falta ⑥['n_front1'] ⑤['params']`) × **OK 3/3+6/6 no POS-T11** — controle-positivo fechado |
| **T30** | 🆕 Não-perturbação da instrumentação T11 | **(1)** | direta | ①②④ **bit-idênticas** pré×pós em **5/5** (dX=dF=**0,0**); 1.000/1.000 seeds |
| **T31** | 🆕 `params.nota_potencia_de_2` não derivado de `q` | **(3)** 🎯 | direta | string fixa "q=10 não é potência de 2" com `params.q=1` no smoke |
| S26 | Caminhos de exceção não exercitados | **T** | não-verificável | hard-stop parcial inalcançável; `teto_wall`/`erro_inesperado` nunca disparados |

### 2.2 Blocos narrativos

**S1 — Orçamento e hard-stop.** *(a)* A D66 fecha `maxFE_batch = 11D−1 + K·q` com K=200, fonte única `budget.maxfe_por_exp('batch', D, q)`. *(b)* Hard-stop exato (D21/D61): `BudgetExhausted` no wrapper, nunca parada aproximada. *(c)* Re-medido: `maxfe_por_exp` == `manifest.maxfe` == `fe_final` == `len(①)` em **5/5**, nos cinco valores 2.109/2.131/2.219/2.241/2.329; `fe_index` e `solution_id` densos **e em ordem** nas 11.029 linhas; a fase `init` é prefixo estrito de 11D−1 seguida de exatamente 2.000 `opt` em 5/5. *(d)* Como 2.000 = 200×10, o laço `while bud.fe < bud.maxfe` termina naturalmente e o `BudgetExhausted` nunca é levantado — daí `n_geracoes = 200 = K` sem off-by-one. *(e)* **(2) D66/D21/D61 · direta.**

**S2 — CP-init bit-a-bit.** *(a)* D37: "o piso parte do mesmo DoE inicial 11D−1 LHS que os batch-SA … comparação pareada". *(b)* D63/D87/D88 proíbem regenerar; o runner carrega o artefato e **pára-e-loga** (D81) se `shape[0] != bud.n_init` (`sobol_batch.py:105-108`). *(c)* `X[:11D−1]` é bit-idêntico ao artefato em float32 nas 5 células; Δ_f64 máx 2,977e-8 (DTLZ2/MMF16_20/ZDT1), 2,375e-7 (ZDT4), **1,907e-6** (WFG9) — o ULP de f32 na escala de cada problema. `doe_hash` manifesto ≡ header ≡ sidecar em 5/5. *(d)* O artefato é float64 e o export é float32 sem arredondamento (D53): o "desvio" é o roundtrip, não re-geração. *(e)* **(2) · direta.**

**S3 — ★ A QUERY-JOIA.** *(a)* D37/§V-B.2 define o piso como "lote aleatório Sobol de q pontos por iteração"; `src/sobol_batch.py:61-79` (`_sobol_batch01`) é a receita literal. *(b)* Sem modelo nem aquisição, a **decisão inteira** do algoritmo é a semente da iteração — logo `seed_sobol` no ⑥ basta para reconstruir 100% do comportamento. *(c)* Reimplementei a receita à parte e, para cada uma das **1.000 iterações**, gerei o lote do seed recomputado e projetei aos bounds nativos: **1.000/1.000 lotes** e **10.000/10.000 pontos** iguais em float32 com `np.array_equal` estrito (**incluindo a ordem dentro do lote**); Δ_f64 global máx **2,98e-8**. *(d)* `SeedSequence` é estável por contrato do numpy e o scramble de Owen do scipy é determinístico dado o seed; run (VM Linux) e validação (macOS) sob **numpy 2.4.6 / scipy 1.17.1** idênticos. **Não sobra nenhuma decisão não-auditada neste config.** *(e)* **(1) · direta.**

**S4 — Semeadura.** *(a)* D62/D91 mandam `SeedSequence((base, alg_id, iteracao, uso_id))` truncado a 32 bits; `seeds.json` registra `sobol_batch → alg_id=22`, `uso_id=0` (DI-33); D22 não se aplica ⇒ base=42. *(c)* Os 200 `seed_sobol` de cada célula batem bit-a-bit com `H.iteration_seed(base,22,g,0,bits32=True)` em **1.000/1.000**; 200 distintos por célula, 0 colisão; **os mesmos 200 nos 5 problemas** (a tupla não contém o problema). *Novo*: `seed(g=1) = 933708677` aparece igual nas 5 células da s42 (VM, jul/2026) **e no smoke POS-T11 e no re-run q=10 de hoje (Mac)** — a receita de semeadura atravessou a campanha T11 intacta. *(e)* **(2) · direta.**

**S5 — ★ "por SEMENTE" (a letra) × "por ITERAÇÃO" (o implementado).** *(a)* D37 (SPEC §V-B.2/Anexo D): *"Scrambling de Owen por semente → cada uma das 30 sementes dá uma sequência Sobol diferente"*; DI-33 repete. A leitura admite (i) uma sequência embaralhada por semente da qual se tiram blocos de 10 — preserva a baixa discrepância **global** — ou (ii) uma sequência nova por iteração. *(b)* A torre escolheu (ii) e **registrou**: `seeds.json` (2026-07-23, DI-33) e o **`sigma_dict` de cada run** (`"lote": "q=10 pontos Sobol SCRAMBLED/Owen por iteração, semeados por iteration_seed(base, 22, iter, 0)"`) — e pela cadeia de precedência do protocolo §0 (dados → `sigma_dict` → bundle → decisões) o `sigma_dict` manda: **desvio SANCIONADO**. Racional: determinismo por-iteração exigido pelo D62/D91 e robustez a hard-stop/resume. *(c)* Medida F5 (`contrafactuais.csv`, não re-rodada nesta bateria e assim marcada): discrepância centrada observada × sequência única — ZDT4 **6,43×**, DTLZ2 **4,11×**, MMF16_20 **1,75×**, WFG9 **1,56×**, ZDT1 **1,19×**; em IGD+ o implementado é pior em 4/5 (+1,8%/+13,4%/+8,2%/+16,0%) e melhor em 1/5 (ZDT1 −8,8%). *(d)* Reinstanciar o motor a cada iteração destrói o balanceamento **entre** blocos; o efeito decai monotonicamente com D (6,43→1,19 para D=10→30). **Calibração honesta:** os ΔIGD+ estão muito abaixo do piso de ruído (58,98%, O-18) e vêm de 1 semente — o que é conclusivo é a CD, determinística. *(e)* **(2) DI-33 + `sigma_dict` · direta + contrafactual.** **Item nº 1 de ratificação do D97** — segue aberto após a T11 (a campanha não o tocou).

**S6 — O scrambling está vivo.** *(a)* D37 justifica pelo negativo: "o Sobol puro daria as 30 repetições idênticas". *(c)* Re-medido: **2.000/2.000 pontos da fase `opt` distintos** (arredondados a 12 casas) em 5/5 células; contrafactual sem scramble (F5) produziria 10 pontos únicos, o 1º na origem em 5/5. *(d)* A evidência direta é o par `cache_hits=0` (⑤≡⑥) e **0 X duplicados em 11.029** (S18): o contador de dedup é, aqui, um **detector de scrambling morto** — ele dispararia ~1.990×/célula no contrafactual. *(e)* **(1) · direta.**

**S7 — q=10 fiado ponta a ponta.** *(b)* O `q` viajar do despachante ao runner foi o **bug crítico nº 1 da DI-34** ("a célula batch rodava q=1 SILENCIOSO … os gates passavam pois liam o q do próprio manifesto"). *(c)* q=10 no ⑤ (5/5), no header (5/5), em **1.000/1.000** eventos, nos 10 footers; ① e ② crescem 10/geração em 1.000/1.000; `n_acumulado = 11D−1+10g` em 1.000/1.000. *(d)* A coerência simultânea de `maxfe`, tamanho do lote e `n_acumulado` fecha em três camadas independentes — aritmética redundante, não config-echo. ⚠ **Este é exatamente o bug que o smoke da T11 reencenou** (rodou q=1) sem que gate algum reclamasse — §4.6. *(e)* **(2) · direta.**

**S8 — K=200 e a divisibilidade que apaga um caminho de código.** `n_geracoes=200` em 5/5; `2000 % 10 == 0` ⇒ o último lote é sempre completo e o `BudgetExhausted` nunca sobe — coerente com **0 eventos guard** no ⑥. O orçamento de infill do batch é `K·q` por construção, logo sempre divisível por q: o caminho de hard-stop parcial é **estruturalmente inalcançável neste grid** (cobertura zero, registrada no teto T). **(2) D66 · direta.**

**S9 — A projeção para bounds nativos.** `xl, xu = H._bounds(problema)`; `lote_nat = xl + lote01·(xu−xl)` (`sobol_batch.py:152`). A reconstrução de S3 **só fecha com a projeção aplicada**, e fecha nas duas células de bounds ≠[0,1] — ZDT4 (x₁..x₉∈[−5,5]) e WFG9 (xᵢ∈[0,2i], até 44) —, onde o Δ é exatamente o ULP de f32 nas escalas 5 e 44. **0 violações de bound em 11.029 linhas.** Se os `u∈[0,1]` crus tivessem sido gravados, o WFG9 teria 2.000 pontos em ~0,05% do domínio; se a projeção fosse errada, o oráculo (S12) não fecharia — duas checagens independentes, ambas fecham. **(1) · direta.**

**S10 — Uniformidade: o piso é mesmo "ao acaso, bem espalhado".** KS de cada coordenada contra U(0,1) nos 2.000 pontos `opt`: **94 testes, 0 rejeições a α=0,05**, p mínimo **0,616** (WFG9); média por célula 0,50001–0,50099; variância 0,08319–0,08347 contra 1/12=0,083333. Razão CD observado/uniforme (F5, `discrepancia.csv`): **0,549** (D=10) → **0,960** (D=30). *(d)* A razão é **monotônica em D**: o piso Sobol é 45% melhor que o aleatório em D=10 e 4% em D=30 — maldição da dimensionalidade do QMC (a vantagem exige n ≫ 2^D). **Consequência para a tese:** em ZDT1 (D=30) o piso é, na prática, **um piso aleatório uniforme**. **(1) · direta.**

**S11 — O caveat do q não-potência-de-2, medido e desmontado.** O scipy avisa que o balanceamento exige n potência de 2; o runner **declara e silencia** o aviso na docstring (`sobol_batch.py:66-78`). Ablação F5 com n=2.000 fixo: q=10 é **melhor** que q=8 (potência de 2) em **4/5** problemas, e q=16 é o melhor em 5/5. O que domina a discrepância global é o **número de blocos independentes**, não o balanceamento interno — que o próprio desenho já destrói ao reinstanciar o motor (S5). Custo do q=10: ≤6% de CD, contra 19–543% do custo do reinício por iteração. **(2) declarado no runner · direta.**

**S12 — O oráculo.** Recomputei `problems.evaluate_problem` para **todas as 11.029 linhas**: desvio relativo mediano **1,27e-12 (ZDT4) a 4,08e-8 (WFG9)**, máximo **5,80e-6/3,67e-5/4,09e-5** (DTLZ2/MMF16_20/WFG9) e ≤6,5e-8 nos dois ZDT; **≥98,4%** das entradas dentro de 1e-6 relativo em 5/5. *(Errata contra a minha F5: eu havia reportado "mediana exatamente 0,0"; a medida correta é ≤4,1e-8 — o máximo, 4,09e-5, confere.)* O resíduo é o roundtrip float32 (D53) amplificado pelo número de condição — o mesmo fenômeno já aceito pelo autor na F5.1 §4.2. Nenhum sinal de avaliação por surrogate, cache indevido ou troca de problema. **(1) · direta.**

**S13 — O "vazio declarado" (③ + sonda + `tempo_fit_s`).** *(a)* `CONTRATO §6.1`, linha "pisos ONLINE (4)": "— NÃO TÊM SONDA (sem modelo)"; DI-13.2: `tempo_fit_s` NULLABLE, "≠ 0.0 que significaria 'treinou e custou zero' e poluiria a média de custo". *(b)* T6-batch §2.6 anexou o `sobol_batch` a `PISOS_ONLINE`; o `sigma_dict` declara tudo. *(c)* ③ com **0 linhas** e schema íntegro (29→49 colunas, `mu_*`/`sigma_*`/`modelo_flag`/`fe_treino_max` presentes) — a marca `VAZIO` de `integridade_f52a.csv`; bloco `sonda={status:'nao_se_aplica', S:0, n_blocos:0}` 5/5 e **0 recs `sonda`**; `tempo_fit_s` NULL em **1.000/1.000** linhas da ④ e nas 1.000 entradas de `fit_series` (verificado também no POS-T11: 200/200 NULL em 5/5). **U3, U4, U5, U6, U8 e U11 são N/A por desenho.** *(d)* `nao_se_aplica` distingue "não tem" de "faltou" — a lição do bug B1, e a razão de o G-1 sair `⚪` e não `⛔`. **(2) · direta.**

**S16 — Invariante de timing DI-13.10.** Com `fit=NULL` e sem sonda resta a inv-1: `busca ≤ tempo_geracao_s` em **1.000/1.000**; inv-2 vácua. O gap `Σ(tempo_geracao_s − tempo_busca_s)` por célula é **0,113 s (ZDT4) a 3,165 s (WFG9)** — o tempo de avaliação real dentro do laço, que sustentava o S24. `tempo_busca_s` mede só a geração dos 10 pontos (0,141–0,268 s por célula inteira: o piso não busca nada). **(2) · direta.**

**S17 — ② cumulativa com off-by-one próprio.** O runner grava `buf.add_pop(0, todos)` após o DoE e `buf.add_pop(g, todos)` a cada iteração. Re-medido: **201 grupos (0..200)** por célula, tamanho `11D−1+10g` exato em **1.005/1.005**; a geração 200 é o dataset inteiro em 5/5. **e81/c149 gravam 200 (1..200)** — qualquer join por geração entre o piso e os SA-batch precisa deslocar. A semântica da ② **continua não declarada no `sigma_dict`** (o e81 declara `selecao`, o c149 `selecao_q1`) — está só no comentário de código (`sobol_batch.py:156`). **(2) U10 · direta.**

**S18 — Guardas e dedup: o zero que informa.** **0 eventos `guard`** no ⑥ das 5 células; `cache_hits=0` no ⑤ **e** no footer 5/5 (U9 fecha exato); **0 X duplicados** entre as 11.029 linhas (chave `float64.tobytes()`, D89). O piso nunca reamostra porque cada iteração usa sequência diferente — ao contrário dos EAs, cujos SBX/PM re-propõem pais (nsga2/ZDT4: 27 cache-hits). **(2) · direta.**

**S19 — ⑦ ausente por desenho.** DI-08 restringe a ⑦ aos 5 offline. Nenhum `__final` nas 5 pastas e `upload_status` marca `exp_batch_sobol_batch_*__final.parquet: "absent"` 5/5 — ausência **declarada**, não silenciosa (a lição dos 44 vermelhos do e103 na F5.1). **(2) · direta.**

**S20 — Pareamento: o mesmo início para 18–20 células por problema.** Re-varri os 421 manifestos online da s42: **1 único `doe_hash` por problema** em 19 (DTLZ2), 18 (MMF16_20), 19 (WFG9), 19 (ZDT1) e 20 (ZDT4) células — cobrindo main (16 configs) e batch (3). Prova métrica: o IGD+ do prefixo init é **numericamente idêntico** nos 3 configs batch em 5/5 (0,448419 · 0,077786 · 0,238715 · 2,095912 · 91,921668). É o D88 funcionando: qualquer diferença de endpoint é atribuível ao infill, não à sorte inicial. **(1) D88 · direta.**

**S21 — Ambiente, pins, roteamento e grid.** 5/5 com `env_main`, Python 3.11.9, numpy 2.4.6, scipy 1.17.1, `OMP/OPENBLAS/MKL/NUMEXPR=1`, `torch_num_threads=1`. `runs_matrix.csv`: **150 linhas**, `exp=batch`, `q=10` em 150/150, 5 problemas × 30 sementes, `alg_id=22`. Config-echo **corroborado**: a versão do scipy declarada é a que reproduziu os 10.000 pontos (S3) — a declaração vira prova para a única biblioteca que importa aqui. **(2) · direta-declarativa corroborada.**

**S22 — Término e mescla do ⑤.** `motivo_parada='orcamento'` em 5/5 e nos 5 primeiros footers; **footer duplo** (runner + despachante) em 5/5, com `n_retries=0`; `tempo_total_despachante_s` > `tempo_total_s` em 5/5. Não existe campo `termino` (esse é dos pisos MATLAB) — confirmando o mapa de término por família. Nenhuma assinatura do B1 (status `ok` com motivo anômalo). **(2) · direta.**

**S23 — 🔧 `n_front1`: de (3) a (2) — CORRIGIDO E VERIFICADO.** Ver §4.1.
**S24 — 🔧 `tempo_aval_real_s`: de (3) a (2) — CORRIGIDO E VERIFICADO.** Ver §4.2.
**S25 — 🔧 `params` no ⑤: de (3) a (2) — CORRIGIDO E VERIFICADO.** Ver §4.3.
**T27 — 🆕 Checkpoint atômico (DI-43).** Ver §4.4. **T28/T29 — 🆕 proveniência e gate.** Ver §4.5. **T30 — 🆕 não-perturbação.** Ver §4.0. **T31 — 🆕 a string que mente fora do grid.** Ver §8.

**S26 — T · Caminhos de exceção não exercitados.** Três saídas anômalas continuam sem dado: `BudgetExhausted` (inalcançável, S8), `teto_wall` (rito (i) da DI-38a, que **se aplica** ao `sobol_batch`; wall de 0,5–6,8 s contra teto de 12 h) e `erro_inesperado`/`write_failed_manifest`. A T11 exercitou o rito de teto **no c154**, não aqui. Cobertura por teste (`tests/test_batch_q10.py`, `tests/test_checkpoint.py:189-235` que roda `run_sobol_batch(..., q=10)` num tempdir e mata o processo), **não por dado**. **T · não-verificável.**

---

## 3. % por classe

**Denominador = 27 aspectos verificáveis (28 total − 1 T).** O T é listado à parte no §9.

| classe | contagem | % |
|---|---|---:|
| **(1)** conforme a especificação canônica | 7 — S3, S6, S9, S10, S12, S20, **T30** | **25,9%** (7/27) |
| **(2)** desvio/adição sancionada (cada um com D-xx/DI-xx) | 19 — S1, S2, S4, S5, S7, S8, S11, S13, S16, S17, S18, S19, S21, S22, **S23, S24, S25**, **T27, T28/T29** | **70,4%** (19/27) |
| **(3)** desvio inexplicado 🎯 | 1 — **T31** | **3,7%** (1/27) |
| **T** teto (não-verificável) | 1 — S26 | fora do denominador |

**Comparação com a F5:** (1) 24,0% → 25,9% · (2) 64,0% → 70,4% · **(3) 12,0% (3 achados) → 3,7% (1 achado, menor e novo)**. Os três (3) da F5 — S23, S24, S25 — migraram para (2) por **correção real e medida**, não por reclassificação. Aspectos `direta-declarativa`: **apenas S21**, e mesmo ele corroborado por dado. **26/27 de verificabilidade direta** — segue sendo a menor superfície declarativa do roster.

---

## 4. 🆕 AS CORREÇÕES DA T11 — implementadas? funcionam de fato?

### 4.0 · ERRATA 17 (minha, contra o handoff e contra o meu próprio briefing): **o smoke Python DESTE config EXISTE**

O handoff T11 §15.2, o `evidencia_T11/LEIA-ME.md` ("Os smokes PYTHON não estão aqui") e o meu briefing ("smoke T11: NÃO PRESERVADO ⇒ só código") afirmam que os 11 smokes Python se perderam em tempdir. **Falso desde 2026-07-31 10:45:** existe `evidencia_T11/smoke_python/` com **11 células** (sobol_batch, c122, c149, c154, c262, e81, b5m, b5r, c311, moead_media, treed_media), todas com `campanha_id=9ad0138aa9a4_2026-07-31` e `repo_hash=9ad0138…` = **o HEAD atual**. A do meu config é `batch/sobol_batch/exp_batch_sobol_batch_ZDT4_42.*`. Isso muda a força desta análise: as correções deixam de ser "lidas no código" e passam a ser **medidas em artefato**.

**E permitiu a prova que faltava (T30).** Rodei o runner de hoje (HEAD `9ad0138`, com toda a instrumentação T11) nas **5 células em q=10, em tempdir** (`t11_b4_rerun_q10.py`) e comparei com a s42:

| problema | ① X bit-igual | ① F bit-igual | dX máx | dF máx | ② igual | seeds iguais |
|---|:--:|:--:|---:|---:|:--:|---:|
| DTLZ2 · MMF16_20 · WFG9 · ZDT1 · ZDT4 | **5/5 ✅** | **5/5 ✅** | **0,0** | **0,0** | **5/5 ✅** | **1.000/1.000** |

**A busca de hoje é literalmente a busca da rodada-42** — 11.029 linhas de ① e 1.211.829 de ② reproduzidas byte a byte, em **outra máquina, outro SO e outra versão do código**. Isto é mais forte que os pares §3.1 g6 (que comparam com/sem sonda **dentro** da mesma versão) e é a razão formal pela qual o corpus s42 continua válido para fidelidade após a T11 — para *este* config, provado, não assumido. Único resíduo: o `f_best` (float64 no ⑥) difere em **5 de 200 eventos do WFG9**, com Δ absoluto **2,220e-16** e relativo **1,896e-16** = **1 ULP de float64** — diferença de última casa entre x86-Linux e macOS nas transformações íngremes do WFG9, invisível na ① (float32, regra 11 do CONTRATO).

### 4.1 · I-03 / T11-A6 — `n_front1` pelo `minimo_comum_di10` ✅ **FUNCIONA (não é o padrão do c217)**

- **Código** (`src/sobol_batch.py:172-179`, commit `40df11a`): o evento passou a ser montado por `**H.minimo_comum_di10(np.vstack([r.f for r in bud.records]), fe=bud.fe, tempo_fit_s=None, tempo_busca_s=t_busca)`; o `f_best` à mão saiu.
- **Dado (smoke q=1)**: `n_front1` em **200/200** eventos; recomputei o NDS do arquivo cumulativo em cada `fe` — **200/200 corretos**; valores 8–12, **5 distintos**, **0 sentinelas**.
- **Dado (re-run q=10, 5 problemas)**: **1.000/1.000 presentes e corretos**; faixas 42–116 (DTLZ2), 51–221 (MMF16_20), 12–25 (WFG9), 14–27 (ZDT1), 5–11 (ZDT4); 6 a 121 valores distintos por célula; monotonicidade não-decrescente em 178–195 de 199 transições (as quedas são reais: pontos novos podem dominar ND antigos).
- **O teste da armadilha do c217** (campo presente, dado sentinela): **negativo em todos os eixos** — o campo varia, é recomputável e bate 1.000/1.000.
- **Ainda falta:** nada do exigível. `ideal`/`nadir_pop`/`nadir_front1` seguem ausentes, mas o artefato normativo curado da própria T11 (`artifacts/contrato_61.json`, cartão T11-G6) fixa o mínimo deste config em `{f_best, n_front1}` e declara `tempo_fit_s`/`tempo_busca_s` não-aplicáveis. **Resta um doc-sync**: a prosa do `CONTRATO §6.1:335` ("pisos (5) … ideal/nadir da pop por geração") não foi atualizada para dizer que o `sobol_batch` — piso #6, criado depois — está fora dessa linha; os 4 pisos EA emitem 6/10 campos e ele agora emite 4/10 (`fe, f_best, n_front1, tempo_busca_s`). Sem perda: ideal/nadir são recomputáveis da ①.
- **Custo medido do instrumento:** `problems._nds_filter` × 200 gerações = **0,020 s (ZDT4) a 0,051 s (MMF16_20)** por célula = **0,3–1,6% do wall da VM** — o comentário do código afirma exatamente "0,020–0,052 s = 0,3–1,6% do wall" e **é reproduzível**. ⚠ Ele está **fora** de `tempo_geracao_s` (a ④ é fechada antes do `log.decision`), então a ④ continua comparável com a s42.
- **Teste**: `tests/test_a2_c122.py::TestA6SobolBatchENsga3::test_sobol_batch_usa_o_minimo_comum` — assertion **sobre o texto-fonte**, não sobre comportamento. O comportamento é coberto pelo gate G-7 e pelas minhas 1.200 verificações. Nota: o item "string `geracoes_derivadas`" que a tabela §2/A6 do handoff atribui a "sobol_batch + nsga3" é **só do nsga3** (o teste irmão lê `src/experiment.m`); o `params` do sobol_batch não tem nem precisa desse campo.

### 4.2 · I-02 / T11-G7 — `tempo_aval_real_s` ✅ **FUNCIONA, e conserta mais do que prometia**

- **Código** (`src/budget.py:241-251`, commit `83dbdac`): o cronômetro foi para **dentro do `FEBudget.evaluate`** — o portão único por onde toda avaliação real do stack Python passa; `sobol_batch.py:205` passa `tempo_aval_real_s=bud.tempo_aval_real_s`. `budget.py:192-202` devolve **None** quando nenhuma avaliação passou ("não medi" ≠ "custou zero"), e `export.py:559-572` aceita o NULL.
- **Dado (s42, re-varredura das 421 células online / 18 configs)**: `tempo_aval_real_s == 0,0` **exato em 5, todas `sobol_batch`**; **0 NULLs**; medianas por config de 0,0277 s (c154) a 0,2055 s (c217). A alegação do comentário do código — "0 zeros em 416 células alheias" — é **exatamente reproduzível** (421 − 5 = 416).
- **Dado (POS-T11, q=10)**: **0,0176 s (ZDT1/ZDT4) · 0,0295 s (DTLZ2) · 0,0385 s (MMF16_20) · 1,5387 s (WFG9)** = 1,8%–**72,1%** do wall. Não-nulo, não-sentinela, e ordenado pelo custo conhecido dos problemas.
- **Conserta o irrecuperável.** A F5 registrou que o custo do DoE inicial (109–329 avaliações, antes da 1ª linha da ④) era irrecuperável de qualquer camada. Como o laço do DoE (`sobol_batch.py:139-140`) chama `bud.evaluate`, o novo acumulador **o inclui**. Prova numérica: no WFG9 o acumulador (1,5387 s) é **1,085×** o proxy da ④ `Σ(tempo_geracao−tempo_busca)` = 1,4176 s, que cobre só os 2.000 infills — a diferença bate com os 241 pontos do DoE ao custo unitário medido (0,709 ms). Nos outros 4 problemas a razão é 0,17–0,52 porque ali o proxy era dominado por overhead de laço, não por avaliação: o número novo é **mais justo nas duas direções**.
- **⚠ ERRATA 18 (minha, contra o comentário do próprio código T11)**, `sobol_batch.py:200-204`: "o valor real medido é 4,110 s-VM nas 5 — 20,6% do wall, **57,15% no WFG9**". Re-medido: o proxy da ④ dá **3,6889 s = 18,52%** do wall, e com a extrapolação do DoE ao custo unitário médio dá **4,1218 s = 20,70%** (compatível com os dois primeiros números). **O terceiro não fecha**: WFG9 dá **46,41%** (proxy) ou **52,00%** (extrapolado), nunca 57,15%. Número não reproduzível — corrija o comentário ou registre a derivação.
- **Testes**: `tests/test_g7_instrumentacao.py` — comportamentais no `FEBudget` (NULL sem avaliação; cache-hit não soma tempo; arredondamento a 4 casas) **+** um teste textual (`assertNotIn("tempo_aval_real_s=0.0", src)`).

### 4.3 · I-07 / T11-C2 — `params` no ⑤ ✅ **FUNCIONA**

- **Código** (`src/sobol_batch.py:215-233`, commit `d77a95d`): dicionário de 14 chaves, com `q`, `D`, `M`, `maxfe` **derivados das mesmas fontes que a busca usou** (`bud.maxfe`, `doe['X'].shape[1]`, `prob.n_obj`).
- **Dado**: presente e coerente em **5/5** do re-run (`params.q == manifest.q == 10`, `params.maxfe == manifest.maxfe` nos 5 valores) e no smoke. Fecha a não-conformidade que `contrato_f52b.csv` registra em 5/5 células da s42 (`camada 5 | CHAVES | faltam ['params']`) e o item **6** da torre.
- **Transversal POS-T11**: os **11 configs Python** do `smoke_python` gravam `params` — o "9 de 10" da ERRATA 11 virou 11/11 com este.
- **Fica o resíduo T31** (§8): `nota_potencia_de_2` é literal fixa, não derivada de `q`.
- **Correção ao texto da F5.2b**: o fallback lá anunciado ("recupera de `artifacts/params.json`") continua **não existindo** para este config; agora é irrelevante, porque o dado está na fonte.

### 4.4 · DI-43 / T11-G5 — checkpoint atômico ⚠ **funciona, e cobra caro NESTE config**

`_Checkpointer.talvez_gravar` (`sobol_batch.py:163`) grava as 4 camadas + um ⑤ `failed/checkpoint_em_andamento` a cada **25 iterações ou 30 min**. Medido no re-run q=10: **8 checkpoints em 8/8 células-oportunidade**, custo por checkpoint crescendo linearmente com a ② (0,0064 s → 0,0576 s no ZDT4), **total 0,221–0,293 s por célula = 12,3%–44,7% do `tempo_total_s`**. A causa é estrutural: a ② deste config é o arquivo cumulativo (222.909–267.129 linhas ao fim), reescrita inteira 8×, num run que dura 0,5–2,2 s. Em absoluto é irrelevante (≈37 s nas 150 células do grid); **em relativo, inflaciona o wall do config que é o baseline de custo do sub-estudo (§V-B.3, eixo 2)**. Mitigação já existente: o custo é **logado e subtraível** (`rec='checkpoint'` com `tempo_checkpoint_s`), e `tempo_geracao_s` da ④ o exclui. **Registre-se como armadilha de leitura (§9-l)**, não como defeito. **(2) DI-43 · direta.**

### 4.5 · B-03/I-09 + G-7 — proveniência e o gate que agora discrimina ✅

s42: `schema_version=1`, sem `campanha_id`, `repo_hash=''`. POS-T11: `schema_version=2`, `campanha_id=9ad0138aa9a4_2026-07-31`, `repo_hash=9ad0138a…` em 5/5. E o **controle-positivo do gate**, que é o teste que a T11 exigiu de si mesma ("um gate que nunca reprova é decorativo"), fecha:

| corpus | G-1 | G-2 | G-3 | G-4 | **G-7 contrato_61** | B-15 |
|---|---|---|---|---|---|---|
| **s42** (pré-T11), 3 células testadas | ⚪ n/a | OK | OK/RUIM* | OK | **RUIM** — `falta ⑥['n_front1'] ⑤['params']` | OK |
| **smoke T11** (q=1) | ⚪ n/a | OK | OK | OK | **OK** — ⑥ 3/3 · ⑤ 6/6 | OK |
| **re-run q=10** (5 células) | ⚪ n/a | OK | OK | OK | **OK** — ⑥ 3/3 · ⑤ 6/6 | OK |

\*modo `historico` OK / modo `campanha` RUIM (sem `campanha_id`/`repo_hash`), como deve ser.

### 4.6 · ⚠ O que a campanha T11 **não** verificou neste config — e eu fechei

**O smoke T11 do `sobol_batch` rodou `q=1`** (`manifest.q=1`, `maxfe=309 = 11·10−1+200·1`), o default `Q_PRINCIPAL=1` do runner. O grid tem **q=10 em 150/150 linhas**: o smoke validou um regime que **não existe na campanha** — e é a mesma classe do bug crítico nº 1 da DI-34 ("a célula batch rodava q=1 SILENCIOSO … os gates passavam pois liam o q do próprio manifesto"). Nenhum dos 6 portões acusou, porque todos leem o `q` do próprio manifesto. **Fechei a lacuna** com o re-run q=10 nas 5 células (§4.0), onde as correções continuam válidas. **Recomendação operacional:** a invocação de SMOKE do RUNBOOK deve passar `--q 10` para este config, e o `portao`/`gates_proveniencia` deveriam cruzar `manifest.q` com o `q` do `runs_matrix` do run_id — hoje não cruzam.

---

## 5. PAPEL DE CONTROLE (substitui a comparação canônica — Entrega 2 é **N/A**)

Não há artigo: o `sobol_batch` é construção nossa (D37). A pergunta é: **o piso cumpre a função de régua?** Um controle serve se (i) é derrotável por um método que funcione, (ii) não é trivialmente derrotável, (iii) parte do mesmo lugar. Os três seguem medidos e **inalterados pela T11** (T30 prova que os números são os mesmos).

**(iii) Mesmo ponto de partida:** IGD+ do prefixo init idêntico nos 3 configs batch em 5/5 (S20).

**(i)+(ii) O placar** (`f5/metricas_finais_f52c.csv` + `f5/baterias/sobol_batch/ganho_sobre_doe.csv`):

| problema | D | piso: IGD+ DoE → final | ganho do piso | e81 | c149 | e81 bate? | c149 bate? |
|---|---:|---|---:|---:|---:|:--:|:--:|
| DTLZ2 | 12 | 0,4484 → **0,2994** | **33,2%** | 49,9% | **0,00%** | ✔ 0,2249 | ✘ 0,4484 |
| MMF16_20 | 20 | 0,07779 → **0,02834** | **63,6%** | 85,0% | 43,0% | ✔ 0,01169 | ✘ 0,04437 |
| WFG9 | 22 | 0,23872 → **0,20388** | **14,6%** | 25,1% | 40,5% | ✔ 0,17890 | ✔ 0,14205 |
| ZDT1 | 30 | 2,0959 → **1,8086** | **13,7%** | 64,2% | 96,5% | ✔ 0,74984 | ✔ 0,07368 |
| ZDT4 | 10 | 91,922 → **68,131** | **25,9%** | 55,5% | **0,00%** | ✔ 40,867 | ✘ 91,922 |

**Placar: 7/10 células SA-batch batem o controle em IGD+** (e81 5/5; c149 2/5) e **6/10 em HV**. O controle é derrotável e não é trivial. O resultado mais forte do sub-estudo só existe **porque** o controle existe: no DTLZ2 e no ZDT4 o **c149 termina com IGD+ numericamente idêntico ao do DoE — ganho 0,000000%**, enquanto o mesmo orçamento gasto ao acaso rendeu 33,2% e 25,9%. Sem o piso, "c149 foi mal"; com o piso, **"c149 foi pior que o acaso, com evidência pareada"**.

**Sanidade contra os pisos EA a FEs iguais** (recorte `fe_index ≤ 31D−1`, `comparacao_truncada_31D1.csv`): o Sobol-batch é **pior que o PIOR dos 4 pisos EA em 4/5 problemas** (a exceção é MMF16_20, dentro da faixa EA) e é batido por 11–13 dos 11–13 SA em 4/5. **É o chão do chão** — o que o qualifica como régua absoluta.

**Ressalva obrigatória (S10):** a vantagem QMC decai monotonicamente com D (0,549 em D=10 → 0,960 em D=30). Em ZDT1/D=30 escreva "lotear ao acaso", não "lotear com baixa discrepância".

**Contexto do sub-estudo (inalterado):** dos 5 configs do roster batch (D66) a rodada-42 produziu 3 (sobol_batch, e81, c149); o c262 abortou 5/5 por teto de projeção e o c154 está fora (DI-40/DI-37.iii). **O piso é a única régua absoluta que o sub-estudo tem** — o que eleva o peso deste config no D97.

---

## 6. Saúde (s42 = corpus principal)

| eixo | resultado |
|---|---|
| **Integridade (F5.2a)** | 5 linhas em `integridade_f52a.csv`, todas `__surrogate.parquet VAZIO linhas=0` — **por desenho**. 0 parquets ilegíveis, 0 manifestos ilegíveis, **1.015/1.015 linhas do ⑥ parseiam**, footer duplo 5/5. Nenhuma entrada em `_FONTES.csv` (nenhuma substituição de ⑥) |
| **Contrato (F5.2b)** | 5 linhas `camada 5 · CHAVES · faltam ['params']` — **fechado pela T11** (§4.3). Todo o resto fecha |
| **Trajetórias** (20 checkpoints × 5 = **95 transições**) | **0 violações** de monotonicidade do IGD+ e **0** do HV. ⚠ Honestidade metodológica: aqui a monotonicidade é **estrutural** (métrica sobre arquivo cumulativo) — sanidade do pipeline, não teste discriminante |
| **Curva de progresso** (do **DoE** ao fim, não do checkpoint fe=0) | 33,2% (DTLZ2) · 72,4% (MMF16_20) · 27,6% (WFG9) · 21,2% (ZDT1) · 25,9% (ZDT4); `n_nd` 40→116, 43→221, 17→24, 14→26, 8→7. **Saturação**: ZDT1 satura no checkpoint 4 (fe≈490) e ZDT4 no 8 (fe≈888) — **58% do orçamento não move nada** no ZDT4. *(Errata contra a minha F5: os 81,6%/96,7%/… de lá partiam do checkpoint fe=0, um front de 1 ponto)* |
| **Sonda** | **N/A por desenho** — piso online sem modelo. **Nem régua Sobol nem bloco estratificado**: 0 linhas em `sonda_f52e.csv`, `sonda.status='nao_se_aplica'` 5/5, e o config não aparece nos pares g6_com/g6_sem (⚪ sem sonda, T11 §5). A **regra 12 do CONTRATO é vácua aqui** |
| **Endpoint** | a **①**; sem ⑦/`nd_pos_real`; sem métrica de fantasia (não há μ) |
| **Determinismo** | **provado por reconstrução** (10.000/10.000 pontos, S3) **e por bit-identidade cross-máquina/cross-versão-de-código** (T30) |
| **Tempo** | s42: **19,92 s** nas 5 células (3,16/3,27/3,34/3,34/6,82), máquina **v6** em 5/5 (`tempo_f52d.csv`). POS-T11 no Mac: 0,52–2,20 s/célula, dos quais **0,221–0,293 s são checkpoint** e 0,020–0,051 s são o `n_front1`. Projeção 30 sementes: **≈10 min** para as 150 células |
| **Proveniência** | 4 das células deste config estão na lista dos **58 manifestos forasteiros** (`executable=/home/jupyter/…`, D-E) — **decisão do autor 2026-07-30: ficam intocadas**. Efeito prático: a esteira idempotente pula essas células num disparo local. Não é questão de fidelidade |

---

## 7. SCORE e VEREDITO

### **SCORE: 9,5 / 10 — recomendação: ACEITAR** (caveats de leitura, nenhum de mecanismo)
### **VEREDITO: MELHOROU** (9,0 → 9,5)

**A causa, nomeada — são três, em ordem de peso:**

1. **CORREÇÃO REAL, verificada em comportamento (não em presença de campo).** Os **três** achados classe (3) da F5 foram fechados e eu os verifiquei um a um contra o padrão do c217 (campo presente / dado sentinela): `n_front1` está presente **e correto em 1.000/1.000** eventos q=10 com NDS recomputado (faixa 5–221, até 121 valores distintos por célula, zero sentinelas); `tempo_aval_real_s` saiu de **0,0 exato em 5/5** para 0,0176–1,5387 s **e passou a cobrir o custo do DoE inicial que a F5 declarara irrecuperável** (razão acumulador/proxy = 1,085 no WFG9); `params` está no ⑤ em 5/5 com os valores derivados das mesmas fontes da busca. Classe (3) caiu de **12,0% (3/25) para 3,7% (1/27)**.
2. **EVIDÊNCIA NOVA que não existia na F5.** O corpus POS-T11 deste config existe (errata 17) e, sobretudo, o re-run q=10 provou **bit-identidade ①②④ pré×pós-T11 em 5/5 células** (dX=dF=0,0 sobre 11.029 linhas de ① e 1.211.829 de ②), em outra máquina e outro SO. Nenhum outro config do estudo tem prova de não-perturbação tão forte — e ela é o que autoriza formalmente usar a s42 como corpus de mecanismo depois da T11. Some-se o **controle-positivo do G-7** (RUIM na s42 × OK no pós), que torna a correção auditável por terceiro sem me refazer.
3. **A amostra não mudou** — as mesmas 5 células, os mesmos indicadores, o mesmo papel de régua. O mecanismo **não mudou**: era fiel e continua fiel. O que subiu foi a **auditabilidade**, e é exatamente por isso que o salto é de meio ponto, não de dois: a régua da F5 dá 10 a "tudo (1)/(2), cada (2) ancorado, contrato perfeito, saúde limpa" e 9 a "idem, com (3) menores já investigados e provados benignos".

**Por que não 10.** Restam (i) o achado T31 — `params.nota_potencia_de_2` é literal fixa que **afirma `q=10` enquanto `params.q=1`** no smoke da própria campanha (benigno em 150/150 linhas do grid, mas é um campo de `params` que não é derivado do dado); (ii) o item **S5 de ratificação do D97** — "scrambling por semente" na letra da D37 × "por iteração" no implementado — segue **aberto** (a T11 não o tocou), e é decisão de fidelidade do autor, não da torre, com efeito medido (CD 1,19×–6,43×; ΔIGD+ mediano +8,2%, dentro do ruído); (iii) dois resíduos documentais (§6.1:335 × `contrato_61.json`; semântica da ② fora do `sigma_dict`); (iv) o teto T intacto (S26).

**Caveats informativos (não-fidelidade):** o poder discriminante do piso **decai com D** — em ZDT1/D=30 ele é indistinguível de um piso uniforme; e o sub-estudo batch chegou à análise com **3 dos 5 configs**, o que faz deste controle a única régua absoluta disponível.

---

## 8. Aspecto classe (3) 🎯 — evidência completa

**🎯 T31 — `params.nota_potencia_de_2` é literal fixa, não derivada de `q`.**
*Regra tocada*: CONTRATO §5 (`params` = a **config EFETIVA** do run) e o racional escrito no próprio código (`sobol_batch.py:212-214`: *"Os valores NÃO são literais soltos: saem das MESMAS fontes que a busca usou"*).
*Evidência medida*: no smoke POS-T11 preservado (`evidencia_T11/smoke_python/.../exp_batch_sobol_batch_ZDT4_42.manifest.json`), `params.q = 1` e `manifest.q = 1`, mas `params.nota_potencia_de_2 = "q=10 não é potência de 2: usamos random(q)…"`. O `sigma_dict` do mesmo manifesto **acerta** (`"lote": "q=1 pontos Sobol SCRAMBLED/Owen por iteração…"`), o que prova que a derivação existe no arquivo ao lado e que a omissão é local. Fonte: `sobol_batch.py:226-228` (f-string ausente).
*Impacto*: **nulo no grid** — `runs_matrix.csv` tem `q=10` em **150/150** linhas, logo em toda célula da campanha a string é verdadeira. O dano é hipotético (um `--q` diferente num diagnóstico) e **de metadado**, nunca de dado.
*Correção*: 1 linha (`f"q={q} não é potência de 2…"` ou condicionar ao `q`).
*Verificabilidade*: **direta**. Não abre trabalho de F5.4; abre um item de higiene antes do M8.

*(Os três (3) da F5 — S23 `n_front1`, S24 `tempo_aval_real_s`, S25 `params` — saem desta seção por correção medida, não por reclassificação: §4.1, §4.2, §4.3.)*

---

## 9. Teto de verificabilidade (T) + armadilhas + o que este corpus NÃO permite

**T (exige código/re-run):**
(i) **Caminhos de exceção** (S26): hard-stop parcial **estruturalmente inalcançável** (2000 % 10 = 0 em 5/5); `teto_wall` (rito (i) da DI-38a, que **se aplica** a este config) e `erro_inesperado`/`write_failed_manifest` nunca disparados (wall ≤ 6,82 s contra teto de 12 h). A T11 exercitou o rito de teto **no c154**, não aqui. Cobertura por teste, não por dado.
(ii) **Estabilidade cross-VERSÃO do scramble de Owen**: a bit-identidade de T30 vale sob **numpy 2.4.6 + scipy 1.17.1 nos dois lados** — a T11 **não** move este teto. O que ela permitiu foi estreitá-lo: hoje está provada a estabilidade **cross-OS/cross-arquitetura** (VM Linux x86 × macOS), com resíduo de **1 ULP de float64** só no WFG9 (5/200 eventos). **Recomendação mantida: pinar o scipy junto com o torch** na `envs.json`/`repos.lock` do disparo em escala.
(iii) **Semântica da ② não declarada no `sigma_dict`** (o e81 declara `selecao`, o c149 `selecao_q1`): "arquivo cumulativo incl. geração 0" segue só no comentário do código.
(iv) **`teto_s` fiado ao runner**: config-echo sem corroboração (nenhuma célula o exercitou).
(v) **1 semente**. Nada aqui separa "mecanismo" de "semente infeliz" em desempenho; os ΔIGD+ do S5 (1,8–16,0%) estão sob o piso de ruído (58,98%).
(vi) **A campanha em escala** (695 células × 30 sementes) é outro regime — concorrência, disco, o custo do checkpoint sobre a ② cumulativa.

**Armadilhas confirmadas (para quem ler estes dados depois):**
(a) **③ com 0 linhas é CORRETO** — marca `VAZIO`, não corrupção; o schema (29–49 col.) está lá com `mu_*`/`sigma_*` que nunca serão preenchidos.
(b) **A ② do piso tem 201 gerações (0..200); e81/c149 têm 200** — todo join por geração precisa deslocar.
(c) **O evento de geração é `rec='decision'`** com `caminho='sobol_batch_gen'` — grep por `rec` errado devolve zero.
(d) 🆕 **`n_front1` existe a partir da T11 e NÃO existe na s42** — a série do piso é comparável com a dos pisos EA **só no dado novo**; na s42, recompute da ①.
(e) 🆕 **`tempo_aval_real_s` mudou de semântica entre corpora**: na s42 é **0,0 = "não medido"** (proxy honesto: `Σ(tempo_geracao_s − tempo_busca_s)` da ④, que **exclui o DoE**); a partir da T11 é medida real e **inclui o DoE**. **Não misture os dois na mesma curva de custo.**
(f) **`tempo_fit_s = NULL ≠ 0,0`** (DI-13.2) — um `fillna(0)` polui a média de custo de fit do estudo inteiro.
(g) **`cache_hits=0` e 0 X duplicados são informação positiva** — o detector de scrambling vivo.
(h) **`f_best` é o ideal do arquivo INTEIRO**, não o melhor da população da geração.
(i) **Os 200 `seed_sobol` são os mesmos nos 5 problemas** — a tupla D62 não contém o problema; o que difere as sequências é D.
(j) **A "vantagem Sobol" some com D** — em ZDT1/D=30 descreva o piso como "aleatório uniforme, na prática".
(k) **`upload_status` marca `__final.*` como `absent`** — ausência declarada da ⑦, não lacuna silenciosa.
(l) 🆕 **O ⑥ pós-T11 tem `rec='checkpoint'`** (8 por célula) e o `tempo_total_s` **inclui 12,3%–44,7% de custo de checkpoint** neste config. Ao comparar wall s42 × M8, subtraia `Σ tempo_checkpoint_s`; a ④ (`tempo_geracao_s`) permanece comparável porque é fechada antes do checkpoint e antes do `n_front1`.
(m) 🆕 **O smoke T11 deste config rodou `q=1`** — se alguém auditar `evidencia_T11/smoke_python/.../sobol_batch`, está lendo um run **fora do grid** (`maxfe=309`); o regime da campanha é q=10, `maxfe=11D−1+2000`.

**O que este corpus NÃO permite verificar:** qualquer coisa sobre **surrogate, incerteza, sonda, WAPE ou cobertura** (não há modelo — U3/U4/U5/U6/U8/U11 são N/A); o comportamento em **escala e sob concorrência**; a **estabilidade cross-versão do scipy**; os três **caminhos de exceção**; e a **variabilidade entre sementes** (1 de 30).

---

**Artefatos desta análise** (todos em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/sobol_batch/`): `RESUMO_MEDIDAS.md` · `t11_b1_mecanismo.py` → `b1_celulas.csv` (5×70 checks), `b1_geracoes.csv` (1.000 lotes), `b1_ks.csv` (94 testes) · `t11_b2_correcoes.py` → `b2_resumo.json`, `b2_smoke_eventos.csv` (200 eventos do smoke POS-T11) · `t11_b3_transversal.py` → `b3_manifestos_s42.csv` (666 manifestos), `b3_di10_por_config.csv` (18 configs) · `t11_b4_rerun_q10.py` → `b4_rerun_q10.csv` (5 células, 40 colunas — a bit-identidade pré×pós).
**Dados READ-ONLY**: `/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/sobol_batch/q10_{DTLZ2,MMF16_20,WFG9,ZDT1,ZDT4}/42/` · `/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/batch/sobol_batch/`.
**Código lido (nunca escrito)**: `src/sobol_batch.py:139-233` · `src/budget.py:145-260` · `src/standalone_harness.py:993-1029` · `src/checkpoint.py` · `src/export.py:549-572` · `claude_code_context/artifacts/contrato_61.json` · `tests/{test_g7_instrumentacao,test_a2_c122,test_gates_g6,test_checkpoint,test_batch_q10}.py`. Commits: `83dbdac` (I-02) · `40df11a` (I-03) · `d77a95d` (I-07); HEAD `9ad0138` = `repo_hash` dos smokes.
**Escritas realizadas**: apenas em `f5/t11/baterias/sobol_batch/` e num tempdir fora do repo (`/var/folders/…/f5t11_sobol_q10_cgdevkur`). `data/experiments` **verificado intocado** (0 arquivos modificados hoje); `experiments.py` nunca invocado.