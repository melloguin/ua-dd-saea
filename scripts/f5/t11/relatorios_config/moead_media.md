# RELATÓRIO DE FIDELIDADE T11 — `moead_media` (MOEA/D-média · piso offline D77) · validação da rodada T11 · re-medição sobre s42 + smoke pós-T11

**Universo.** **(A) s42 = 45/45 células** (`resultados_experimentos/moead_media/{label}/42/`, 25 `off` + 20 `sweep`), TODAS re-medidas do zero nesta rodada (não reciclei os CSVs da F5, exceto `sonda_f52e.csv`/`tempo_f52d.csv`/`transversal_offline_camada7.csv`, declarados). Agregados reproduzidos: **2.701.620 linhas de ③** (1.801.620 busca + 900.000 sonda) · **30.165 eventos `decision`** · **30.120 transições de população** · **3.020 linhas de ⑦** · 45 manifestos · 45 `.jsonl`.
**(B) O smoke T11 EXISTE e o briefing está desatualizado.** `evidencia_T11/smoke_python/experiments/off/moead_media/exp_off_moead_media_MMF1_0.*` (7 arquivos, 2026-07-31 10:46) — o `LEIA-ME.md` e o §15.2 do handoff dizem "os smokes PYTHON não estão preservados"; **estão** (11 configs, incl. o par de ablação `b5m/MMF1/s0` no MESMO problema e MESMA semente). Foi o achado que mudou o alcance desta análise: as correções da T11 puderam ser **MEDIDAS**, não só lidas.

---

## 1. Ficha do mecanismo

**O que é (D77/DEF-E3).** Piso do regime offline: **MOEA/D rodando sobre um GP treinado uma única vez no dataset, usando SÓ a média**. Motor `MOEA_D` (**mode 12**, Gen-MOEA/D, decomposição **PBI**) do `desdeo_emo` vendorizado, seleção `MOEAD_select` — a ablação exata do b5m (mode 72, `ProbMOEAD_select`). Surrogate `SurrogateKriging` (1 GPR/objetivo; `C(1,(1e-3,1e3))·RBF(10,(1e-2,1e2))`, `alpha=0`, `n_restarts_optimizer=9`, `normalize_y=False`), treino único, **independente por config** (DI-28). Lattice Das-Dennis herdado do b5m (**50 em M=2 / 105 em M=3**, DI-16.4/D65). Orçamento interno **40.000 avaliações-surrogate**; **zero FE real** na busca; endpoint = ⑦ (`__final.parquet`), avaliada 1× na verdade e filtrada por não-dominância **depois** (DI-13.9/DI-08). σ **nem calculado nem reportado** (DI-16.1). Duas instâncias por tier (P5/DI-16.5): small/medium = `env_b5` (este relatório, 45 células); big = `treed_media`/`env_c311`.

**Divergências sancionadas em jogo:** DI-16.1 (σ NULL) · DI-16.4 (lattice) · DI-16.17 (② vazia) · DI-13.5 (sonda `geracao` NULL) · DI-28/DI-28.3 (treino independente + LHS determinístico) · DI-30 item 3 (degeneração do GP = achado científico, RATIFICADO) · DI-30.B2 (`modelo_hp` NULL) · DI-30.B3 (⑥ na linha do b5) · D68 (sem cap) · D90/D51 (tiers/dists) · D29 🟠 para tudo que é do vendor.
**Divergência sancionada NOVA nomeada nesta rodada:** a **adaptação de vetores de referência de Cheng-2016** (`BaseDecompositionEA.manage_preferences` → `ReferenceVectors.adapt`) — herdada da classe-base do vendor, **não prescrita pelo MOEA/D canônico**, classificada **(2)/🟠** pelo veredito adversarial `b5m-A8`. É o motor da dinâmica deste config (§A20).

---

## 2. DISSECAÇÃO DOS ASPECTOS

### 2.1 Tabela-resumo (25 aspectos + 7 T)

| # | aspecto | classe | verif. | resultado medido (45 células s42, salvo indicação) | vs F5 |
|---|---|---|---|---|---|
| A1 | ① = dataset inteiro, 100% `init`, `fe_index` denso | (2) | direta | 45/45 · `n①=maxfe=fe_final` · init=1,000 · `arange(N)` 45/45 · 8 tamanhos (61…2000) | = |
| A2 | binding ①↔artefato do dataset, bit-a-bit | (1) | direta | **max\|ΔX\|=0,0 e max\|Δf\|=0,0 em 45/45**; `doe_hash≡cp.x_hash` 45/45 | = |
| A3 | ④ = 1 linha ≡ treino único / modelo congelado | (2) | direta | 45/45 · `fit_series`=1 · `n_acum=n①` · `fe_treino_max` único | = |
| A4 | sonda: 1 bloco de 20.000, `geracao` NULL, join posicional | (2) | direta | 20.000 linhas 45/45 · `geracao` NaN 100% · **ΔX=0,0 em 900.000 pontos** | = |
| A5 | WAPE no espaço cru; cobertura **N/A** por regra | (2) | direta | `espaco_modelo='cru'` 100% · `cobertura95` vazia 104/104 · `n_nan`=0 | = |
| A6 | invariante do ④: `fit+busca = tempo_geracao_s` | (2) | direta | max\|Δ\|=**7,6e-06 s** em 45/45; `t_sonda>0` 45/45 | = |
| A7 | `fe_treino_max` constante = N−1 | (2) | direta | 1 valor único por célula 45/45, = `len(①)−1` 45/45 | = |
| A8 | guards zero + aritmética entre camadas fecha | (1) | direta | 0 `guard`, 0 cache, 0 retries 45/45 · ③off=N×n_ger 45/45 · 30.165 decisões = Σn_ger | = |
| A9 | erro de fantasia (μ final × f real) | (2) | direta | 69/104 pares 100% otimistas; WAPE-final mediano 0,985 (F5, citado) | = |
| A10 | ⑦ recomputada, ligada, sem cap | (2) | direta | ND recomputada **exata 45/45** · link X **ΔX=0,0 45/45** · `n⑦`=N 45/45 | = |
| A11 | σ 100% NULL — a ablação materializada | (2) | direta | **2.701.620/2.701.620 σ NaN**; μ NaN em 0 | = |
| A12 | ② vazia · `real_solution_id` NULL · `n_ds_membros`=0 | (2) | direta | 0 linhas 45/45 · NULL 100% · 0 em 30.165 eventos | = |
| A13 | motor mode 12 + PBI | (1) | direta-decl. | `modelo_flag`/`caminho`/`motivo` uniformes 45/45 + `n_ger≡b5m` | = |
| A14 | lattice 50/105 (não 100) | (2) | direta | 50 em 31 células · 105 em 14 · pop constante 45/45 | = |
| A15 | orçamento 40.000 — **REFINADO** por `granularidade_③` | (2) | direta | **passos de seleção × N = 40.000 EXATO em 31/31 (M=2)**; 39.900 em 14/14 | **refinado** |
| A16 | Kriging: mesma espec., treino independente, espaço cru | (2) | direta | μ≡b5m a ≤1e-5 em 65/104 (F5) · `modelo_hp` NULL 45/45 · `t_fit` razão 0,970 | = |
| A17 | ablação cirúrgica — **re-provada no código pós-T11** | (1) | direta | s42: `n_ger`≡b5m 45/45 · **smoke T11: 801≡801, ① ΔX=Δf=0, σ 100%×0% NaN** | **reforçado** |
| A18 | duas instâncias por tier (big = `treed_media`) | (2) | direta | 0 células big; `env_b5` 45/45 | = |
| A19 | determinismo do RNG provado por re-run | (1) | direta | ①③⑦ **bit-idênticas** `off`×`swap_small-lhs` em **5/5** (Δ=0,0) | = |
| A20 | **dinâmica: o congelamento vem do `adapt`, não do ponto fixo** | **(2)** | direta | **748/3.057 adapts (24,5%) com coluna zerada** · 7.113/30.120 congeladas · **r=0,913** | **(1)→(2), causa trocada** |
| A21 | colapso do GPR + assimetria de taxa | (2) | direta | 28/104 pares (26,9%) em 14 células; b5m 8, b5r 4 | (3)→(2) pelo adversarial |
| A22 | extrapolação para fora do suporte | (1) | direta | `f_best` < mínimo do dataset em 95/104 (F5, citado) | = |
| A23 | ⑥ na linha do b5 (DI-30.B3) + **`params` no ⑤ CORRIGIDO** | (2) | direta | s42: `params` ausente 45/45 · **smoke T11: `params` presente, G-7 ⑤ 6/6** | **corrigido** |
| A24 | término + **⑥ blindado (O_TRUNC/B-01)** | (2) | direta | `motivo_parada='orcamento'` 45/45 · 1 célula com resíduo — **impossível hoje** | **corrigido** |
| A25 | **`tempo_aval_real_s` no offline (I-02)** | **(3) 🎯** | direta | s42 `0.0` literal 45/45 → smoke **`0.0001`** = 1,64 µs/FE (online: 25,4 µs/FE) | **NOVO (3)** |
| T1–T7 | teto de verificabilidade | **T** | — | ver §9 (T2/T3 saem do "não-verificável" para "lido em código") | +T6, +T7 |

---

### 2.2 Blocos narrativos

**A1 — A ① é o dataset inteiro.** (a) No offline não há função real durante a busca (bundle §3.4); a ① é o registro do dataset precoletado. (b) D90/D51/DI-13.7: dataset = artefato de `31D−1` (small) / 2.000 (medium), LHS ou MVNS, copiado integralmente com `fase='init'`. (c) `t1_estrutural_s42.csv`: `len(①)==maxfe==fe_final` em 45/45; `fase=='init'` fração **1,000** em 45/45; `fe_index==arange(N)` e `solution_id==arange(N)` em 45/45; tamanhos {61, 216, 309, 371, 619, 681, 929, 2000} — 31D−1 nas 35 small e 2.000 nas 10 medium. (d) O runner lê o parquet e o repassa; `problems.py` só é chamado na ⑦. (e) **(2)**, direta.

**A2 — Binding bit-a-bit ao artefato.** (a)(b) D63/D87/D90 fixam `data/datasets/{p}/ds_{p}_42[_{tier}_{dist}].parquet`; o gate F5.1 confere por hash. (c) Fui além do hash e comparei valor a valor em float32 nas **45/45**: `t5_binding.csv` → **max\|ΔX\| = 0,0 e max\|Δf\| = 0,0**, artefato localizado em 45/45 (25 sem sufixo, 10 `_small_*`, 10 `_medium_*`). `doe_hash ≡ cp_init_offline.x_hash` 45/45. (d) Sem regeneração em nenhum ponto. (e) **(1)**, direta.

**A3 — ④ com uma linha; o modelo está congelado.** (a) O offline não retreina. (b) `sigma_dict.④_1_linha` (molde b5): 1 linha, `n_acumulado=n_dataset`, `tempo_geracao_s` exclui a sonda, "o motor é caixa-preta: `iterate()` roda 10 gerações sem gancho". (c) `len(④)=1` e `len(fit_series)=1` em 45/45; `n_acumulado == len(①)` 45/45; `fe_treino_max` com **1 valor único** em toda a ③ (busca *e* sonda) em 45/45. Código: `piso_offline.py:372-377` — um `problem.train(SurrogateKriging)`, cronometrado, antes do laço. Somatórios: 4.215 s de fit, 3.208 s de busca, 294 s de sonda. (e) **(2)**, direta.

**A4 — Sonda: 1 bloco, `geracao` NULL, join POSICIONAL.** (a) §17.2.2: régua comum, 20.000 pontos Sobol, "1× por modelo treinado". (b) DI-13.5 sanciona `geracao` NULL (o `emit_sonda_block` faz `int(geracao)`; `piso_offline.py:542-549` completa o buffer). Regra 5/10 do CONTRATO §10: join **por posição**. (c) 20.000 linhas `regime='sonda'` e 1 evento `sonda` no ⑥ em 45/45; `geracao` NaN em **100%** das 900.000 linhas; `t5_binding.csv`: **max\|ΔX\| sonda×gabarito = 0,0 em 900.000 pontos**; `hash_check='ok'` 45/45. Não há bloco `sonda_estratificada` neste config (não é classificador) ⇒ a **regra 12 do CONTRATO não se aplica** e a régua Sobol é o único bloco — comparável entre configs. (e) **(2)**, direta.

**A5 — WAPE cru; cobertura N/A por regra.** (a) §5 do protocolo. (b) `espaco_modelo='cru'`, `transf_tipo/params` NULL em 100% das 2,7 M linhas ⇒ nada a des-transformar; cobertura **N/A** porque σ é NULL por desenho (DI-16.1). (c) `sonda_f52e.csv` filtrado: **`cobertura95` vazia em 104/104** e `n_nan=0` — o CSV tratou o σ ausente **sem inflar** (contraste com a armadilha 15 do c311). 1 bloco ⇒ não há tendência 1º→último. (e) **(2)**, direta.

**A6 — Invariante dupla do ④.** (a) §17.6/DI-13.10: `tempo_geracao_s` exclui a sonda. (b) Com 1 linha, vira igualdade. (c) `max|t_fit + t_busca − t_geracao| = **7,63e-06 s**` em 45/45 (resíduo float32 do parquet); `tempo_pred_sonda_s > 0` em 45/45. Código: `piso_offline.py:484-486` grava `tempo_geracao_s = t_fit + t_busca_total`, com `t_snd` à parte. (e) **(2)**, direta.

**A7 — `fe_treino_max` constante.** (b) O modelo vê o dataset inteiro 1× ⇒ `= n−1` em toda linha (D-08). (c) `nunique()==1` em 45/45 e `== len(①)−1` em 45/45. Não há a não-monotonicidade de b1/b4/c217 (regra 9 do CONTRATO). (e) **(2)**, direta.

**A8 — Guards zero e aritmética fechada.** (c) **0 eventos `guard`** nas 45; `cache_hits=0` no ⑤ e no footer; `fallback_ativado=False`; `n_retries=0`; `stack_trace=null` — 45/45 em todos. Aritmética: ③offline = N×n_ger em 45/45 (40.050 M=2 / 40.005 M=3); `#decision == n_geracoes` em 45/45, somando **30.165**; contador de geração denso `{1..n_ger}` em 45/45; `fe` constante = `len(①)` nos 30.165 eventos; 1 `header` + 1 `sonda` + 2 `footer` (runner + despachante) em 44/45. (e) **(1)**, direta.

**A9 — Erro de fantasia.** (b) Não existe infill; `real_solution_id` é NULL por desenho (DI-16.17). O substituto é (μ da ③ na última geração) × (f real da ⑦), ligado por `origem_linha`. (c) F5 (`fantasia_final.csv`, citado, não recomputado): **69/104 pares (66,3%) com 100% de otimismo**, viés mediano negativo em 91/104, WAPE da população final mediano **0,985**. (d) O PBI compara escalarizações da média; fora do suporte a média do GP vai a 0 ou a valores negativos e o motor caminha para lá. (e) **(2)**, direta.

**A10 — ⑦ reconstituível, sem cap.** (c) Recomputo independente da máscara ND sobre a vista float32 persistida: **idêntico ao `nd_pos_real` em 45/45**; link posicional `③[g=n_ger].loc[origem_linha] → ⑦.x*`: **max\|ΔX\| = 0,0 em 45/45** (3.020 linhas); `origem_linha` denso, `origem_geracao` única e = n_ger, `origem_solution_id` NULL 100%; `n⑦ = N` do lattice em 45/45 (nenhum encolhimento). Razão de fantasia mediana **0,360** (mín 0,020, máx 1,000). ⚠ **A leitura dessa razão está poluída** — ver A20 e §6.3. (e) **(2)**, direta.

**A11 — σ 100% NULL.** (b) DI-16.1: *"NULL POR CONSTRUÇÃO — o piso é 'o b5 sem σ'"*. (c) σ NaN em **2.701.620/2.701.620** linhas (100,000%) e μ preenchido em 100%; `pred_tipo='valor'` uniforme, `pred_classe/score/confianca` NULL 100%. Código: `piso_offline.py:385-389` — `_predict` devolve `(mu, None)`. **No smoke pós-T11 o padrão persiste**: σ NaN 1,0000 no piso × 0,0000 no b5m, na MESMA célula (MMF1/s0). (e) **(2)**, direta.

**A12 — ② vazia.** (b) DI-16.17: pop inicial é LHS novo + SBX/PM contínuos ⇒ nenhum indivíduo coincide com o dataset. (c) 0 linhas na ② em 45/45; `real_solution_id` NULL em 100% das 2,7 M linhas; `n_ds_membros==0` nos 30.165 eventos — a prova empírica do desenho. (e) **(2)**, direta.

**A13 — Motor mode 12 + PBI.** (c) `modelo_flag='moead_media/MOEAD-PBI+GPR-media'` em 100% das 2,7 M linhas; `caminho='moead_media_gen'` e `motivo='selecao no surrogate (MOEA/D mode 12, PBI; so a media)'` nos 30.165 eventos; `algo_version='piso-off-moead_media-1.0'`, `env_b5` 45/45. Corroboração indireta forte em A17. Código: `piso_offline.py:152` importa `MOEA_D` de `desdeo_emo.EAs.ProbMOEAD`; `ProbMOEAD.py:120-122` instancia `MOEAD_select(SF_type='PBI')`. (e) **(1)**, **direta-declarativa**.

**A14 — Lattice 50/105.** (b) DI-16.4/D65 superou a nota "N=100" (forçar 100 mediria duas variáveis). (c) 50 em **31/31** células M=2 e 105 em **14/14** M=3; população constante em todas as gerações de 45/45 (`nunique()==1`); `n⑦` = 50/105 em 45/45. (e) **(2)**, direta.

**A15 — 40.000 avaliações: o que a `granularidade_③` da T11 refinou.** (a) Bundle §11: o piso é ancorado no b5 — 40.000 avaliações-surrogate, "porque piso-MOEA/D vs Prob-MOEA/D com o **mesmo orçamento interno** é a ablação cirúrgica". (b) O `sigma_dict` da s42 declarava só o `overshoot` ("a última geração que cruza o teto completa o laço ⇒ overshoot ≤ 1 geração"). A T11 **acrescentou a chave `granularidade_③`** (`piso_offline.py:229-231`): *"ger 1 = pop INICIAL (LHS, PRÉ-seleção); 2..n = PÓS-seleção; passos de seleção = n_geracoes−1; FE conta init+pop"*. (c) **Testei a declaração no dado, e ela é verdadeira em 45/45.** (i) Estratificação de Latin hypercube na geração 1, nos bounds REAIS do problema (`t2_granularidade3.csv`): um LHS de N pontos ocupa exatamente os N estratos de **cada** dimensão ⇒ score 1,0; amostra uniforme qualquer ocuparia ~0,632. Medido: **score médio 1,0000 e score MÍNIMO por dimensão 1,0000 em 45/45 células** — Latin hypercube perfeito, 0 pontos fora dos bounds, 0 duplicatas. Controle: a geração 2 cai para mediana **0,070** e passa a ter mediana de **39 duplicatas** (uma população pós-seleção MOEA/D repete indivíduos entre vetores de peso e não pode ser LHS); 44/45 caem. O smoke pós-T11 repete: ger1 = 1,0000 · ger2 = 0,1100. (ii) **Passos de seleção × N = 40.000 EXATO em 31/31 células M=2** e 39.900 em 14/14 M=3. (d) Código: `Population.__init__` (`Population.py:111`) põe `gen_count=1` e `add()` (`:153-156`) arquiva a população inicial na chave `"1"` antes de incrementar; `MOEA_D._next_gen` (`ProbMOEAD.py:165-171`) arquiva pós-substituição nas chaves 2..n; `BaseDecompositionEA.__init__:194` soma a população inicial ao contador de FE; `continue_iteration` (`BaseEA.py:70-75`) testa `_function_evaluation_count <= 40000` ⇒ para quando ultrapassa. Logo o contador chega a 40.050/40.005 (o overshoot de 50/5 que a F5 reportou) **e** a busca propriamente dita consome exatamente 40.000 (M=2). **A F5 chamou de "overshoot de 1 geração" o que é a população inicial contada.** As duas leituras são compatíveis; a nova declaração diz qual é qual. (e) **(2)**, direta — aspecto **refinado**, não corrigido.

**A16 — Kriging: mesma especificação, treino independente.** (a)(b) Bundle §10 + DI-28 (*"mesma ESPECIFICAÇÃO, treino INDEPENDENTE — nunca 'idêntico'"*) + DI-30.B2 (`modelo_hp` NULL nos dois lados, para não criar assimetria). (c) F5 (citado): μ do piso ≡ μ do b5m a ≤1e-5 em **65/104 pares**, mediana da diferença relativa 1,15e-07 (1 ULP de float32); `modelo_hp` NULL 45/45; `t_fit` razão mediana b5m/piso **0,970** (re-medida agora nos 45 manifestos). Especificação do vendor (`SurrogateKriging.py:23-24`, lida): `C(1,(1e-3,1e3))*RBF(10,(1e-2,1e2))`, `alpha=0`, `n_restarts_optimizer=9`, `normalize_y` ausente ⇒ False, `random_state` ausente ⇒ RNG global. **Um único arquivo, compartilhado pelos dois lados da ablação.** (e) **(2)**, direta.

**A17 — A ablação é cirúrgica — e isso foi RE-PROVADO no código de hoje.** (a) DEF-E3/D77: o contraste mede exatamente o valor de usar σ. (c) **s42:** `n_geracoes`(piso) ≡ `n_geracoes`(b5m) em **45/45** (801/801 nas 31 M=2, 381/381 nas 14 M=3); controle negativo b5r (RVEA) diverge em 45/45 (454–5.548 gerações, população variável). **Smoke pós-T11 (a evidência nova):** `off/moead_media/MMF1/s0` × `off/b5m/MMF1/s0`, mesmo dia, mesmo código — `n_geracoes` **801 ≡ 801**, `fe_final` 61≡61, `doe_hash` idêntico, `sonda.x_hash` idêntico, ① **max\|ΔX\|=0 e max\|Δf\|=0**, ③ com 40.050 linhas de busca + 20.000 de sonda **em ambos**, N=50 em ambos, e **σ NaN em 100% no piso × 0% no b5m**. Custo: `t_busca` **32,11 s (piso) × 2.722,90 s (b5m) = 84,8×** no smoke; na s42 a razão mediana é **62,5×** (faixa 14,1–105,3×), com `t_fit` 0,970× e `t_sonda` 1,052× — **todo o preço de σ está na busca, nada no surrogate**. Wall das 45: **2,18 h (piso) × 37,42 h (b5m)**, mediana por célula 67,2 s × 2.981,9 s = 44,4× (todas as 90 no `mac`, `tempo_f52d.csv` ⇒ piso de ruído entre máquinas **não se aplica**). **Prova negativa adicional (ERRATA 12):** `p_wrong_stats` aparece em **0 dos 30.165 eventos** do piso na s42 e em **0 dos 801** do smoke, enquanto o b5m grava em 800/801 — a maquinaria probabilística está provadamente **ausente** do piso. Ver §4 item 5. (e) **(1)**, direta.

**A18 — Duas instâncias por tier.** (b) P5/DI-16.5: `b5` × `c311` não podem ser co-importados (N.1.2/D79). (c) 0 células `swap_big-*` sob `moead_media`; `env.executable` = `env_b5` em 45/45; tier NULL 25 / small 10 / medium 10, dist NULL 25 / lhs 10 / mvns 10. Consequência de leitura: "45 células do piso offline" **subconta** — são 54 com `treed_media`. (e) **(2)**, direta.

**A19 — Determinismo provado por re-run.** (b) D62 + DI-28.3 (`piso_offline.py:163-190` injeta o `RandomState` global semeado no `lhs` do pyDOE 0.9.1, que senão criaria um `default_rng()` fresco). (c) `off/{p}` e `swap_small-lhs/{p}` consomem o MESMO artefato (provado em A2) em dois processos independentes. `t5_determinismo.csv`: **① Δ=0,0 · ③ Δ=0,0 · ⑦ Δ=0,0 nos 5/5 problemas** (DTLZ2, MMF16_20, WFG9, ZDT1, ZDT4), sobre 60.005/60.050 linhas de ③ cada. (e) **(1)**, direta.

---

**A20 — 🔬 O CONGELAMENTO NÃO É PONTO FIXO DO PBI: É O `adapt` ZERANDO O LATTICE.** *(o bloco central desta rodada — a F5 tinha o FATO certo e a CAUSA errada)*

(a) **O que o método prescreve.** No MOEA/D canônico (Zhang & Li 2007) os vetores de peso são **fixos** ao longo de toda a execução; a decomposição PBI usa θ fixo. Não há readaptação de vetores.

(b) **O que a implementação faz, e por quê.** O `MOEA_D` do vendor herda de `BaseDecompositionEA`, e `iterate()` (`desdeo_emo/EAs/BaseEA.py:55-62`) chama **sempre** `manage_preferences()`, que em `:243-244` executa `self.reference_vectors.adapt(self.population.fitness)` — a adaptação de vetores de **RVEA (Cheng-2016)**, não do MOEA/D. `ReferenceVectors.adapt` (`othertools/ReferenceVectors.py:256-262`) faz `values = initial_values × (max(fitness) − min(fitness))` por objetivo e normaliza; `normalize()` (`:227-236`) troca norma 0 por `eps`. Consequência algébrica: **se a amplitude de um objetivo é exatamente 0, aquela coluna de `values` zera**; se todas zeram, **todo vetor vira o vetor nulo**. E `MOEAD_select.pbi` (`selection/MOEAD_select.py:72-74`) faz `weights/np.linalg.norm(weights)` = **0/0 = NaN**, de onde `np.where(SF_off < SF_cur)` (`:59`) é **vazio** — `NaN < NaN` é False — e a população **nunca mais é substituída**. Nada disso está declarado no `sigma_dict` (20 chaves na s42, 21 no smoke) nem no bundle deste config. A sanção existe por herança: o veredito adversarial **`b5m-A8`** classificou a cadeia como **(2)/(b) comportamento legítimo do código oficial**, bússola **D29 🟠**, com causa-raiz sancionada em **DI-30**.

(c) **O que foi observado — 45 células × 3 configs, `t3_adapt_degenerado.csv`.** `n_gen_per_iter=10` ⇒ o `adapt` roda nas gerações 1, 11, 21, …; medi o `ptp` de cada μ_j na população arquivada nesses pontos.

| medida | `moead_media` | `b5m` | `b5r` |
|---|---:|---:|---:|
| pontos de `adapt` | 3.057 | 3.057 | 5.803 |
| adapts com ≥1 coluna **zerada** | **748 (24,47%)** | 161 (5,27%) | 254 (4,38%) |
| adapts com **TODAS** as colunas zeradas (⇒ PBI NaN) | **246** | 156 | 5 |
| células afetadas | **15/45** | 4/45 | 4/45 |
| transições congeladas (X(g)≡X(g+1) bit-a-bit) | **7.113/30.120 (23,6%)** | 2.058/30.120 (6,8%) | 592/57.791 (1,0%) |
| congelamento **terminal** (a busca morre e não volta) | **4.201 em 16 células** | 1.543 em 5 | **0 em 0** |

Os números terminais **reproduzem exatamente** os do veredito `b5m-A8` (4.201/16 no piso e 1.543/5 no b5m) — medição independente, mesma unidade. **A ligação causal:** Pearson r(adapts com coluna zerada, fração congelada) = **0,9132** nas 45 células do piso; fração congelada **mediana 0,805 nas 15 células com coluna zerada contra 0,016 nas 30 sem** (**50×**); e **4.189 das 4.201 transições terminalmente congeladas (99,7%) estão nas 13 células com vetores degenerados**.

Casos exemplares, com o número exato:
- **`swap_medium-lhs_MMF16_20`** — o `adapt` da geração 1 zera os **3** objetivos; a população congela em g=1 e **380/380 transições são congeladas**. Verifiquei o desfecho: `X(ger 1) == X(ger 381)` bit-a-bit, e a **⑦ é bit-idêntica à população LHS inicial**. Isto é: 39.900 avaliações-surrogate foram gastas e **nenhum indivíduo foi substituído em toda a execução**. E o IGD+⑦ dessa célula é **0,1083 contra 0,9554 do b5m — o piso "vence" 8,8×** com uma busca que literalmente não rodou.
- **`ZDT6`** — 81/81 adapts com 1 objetivo sempre zerado (lattice espremido em 1 eixo), congelado a partir de g=118, 729/800 transições congeladas, ⑦ com **3 X distintos em 50 linhas**. O IGD+⑦ é **0,1078 × 6,6365 do b5m = 62× melhor** — a manchete "remover σ ganha 62× no ZDT6" da §4 do relatório F5 descreve, na verdade, uma busca morta desde a geração 118.
- **`BBOB_F17`** — 75/81 adapts com **todos** os objetivos zerados a partir de g=61; ⑦ com **1 único X distinto replicado 50×**, `nd_pos_real = 50/50`. É a explicação da armadilha 22 da F5 ("fantasia 1,000 não é bom"): a fantasia é 1,000 porque **50 cópias do mesmo ponto não se dominam**.
- **`swap_medium-mvns_WFG9`** — degenera a partir do adapt g=181, 63/81 adapts com tudo zerado, ⑦ com **1 X distinto**. Esta célula **não** está na lista de colapso da sonda (A21): é um **confundidor novo** que a leitura da F5 não capturava.
- **`DTLZ4`** — 2 de 3 objetivos **sempre** zerados nos 39 adapts: o lattice é projetado numa face e morrem exatamente os vetores com suporte nessa face (é o teste geométrico 8/8 que o `b5m-A8` previu) — congelamento **parcial**, 154/380 transições, sem morte terminal.

(d) **O mecanismo, ponta a ponta.** GP treinado com `normalize_y=False`/`alpha=0` cai na bacia da média a priori (A21) ⇒ μ_j fica **constante** na população ⇒ `ptp = 0` ⇒ `adapt` zera a coluna j ⇒ PBI com peso nulo devolve NaN (ou, no caso parcial, ignora o objetivo j) ⇒ `selection` vazia ⇒ zero substituição ⇒ congelamento. A F5 atribuiu o congelamento a "a comparação determinística de escalarizações PBI da média produz um ponto fixo e trava" — isso descreve corretamente as **30 células limpas** (mediana 1,6% de transições congeladas), mas **é falso para as 15 células que respondem por 4.189 das 4.201 transições terminais**. É por isso que este aspecto muda de classe.

(e) **(2)** — desvio sancionado por herança (`b5m-A8` CONFIRMADO(b), bússola D29 🟠, causa-raiz DI-30), **direta**. Reclassificado de **(1) → (2)**; a causa publicada na F5 (§C8) deve ser **substituída**.

---

**A21 — Colapso do GPR e a assimetria de taxa (reclassificada).** (a) O método pressupõe um Kriging informativo. (b) A especificação implementada tem `normalize_y=False` hard-coded, `alpha=0` e kernel isotrópico com bounds fechados ⇒ com alvo de escala grande a verossimilhança marginal tem um ótimo degenerado onde o comprimento de escala vai ao piso e o posterior devolve a média a priori. (c) Re-medi por `sonda_f52e.csv` com o critério congelado (WAPE = 1,000 ± 1e-4 **e** \|corr\| ≤ 0,015 ou NaN): **28/104 pares (26,9%) em 14/45 células** no piso; **8/104** no b5m e **4/104** no b5r (o adversarial obteve 28/9/5 com critério ligeiramente distinto e 28/9/4 com critério invariante a escala — as três medições concordam no piso). Pares sadios (n=76): WAPE mediana **0,1268** (q25 0,0179 · q75 0,2711), correlação mediana **0,9337**. (d) A **assimetria** de taxa (piso 3,1× b5m) foi **REFUTADA** no adversarial `moead_media-C9b.md`: com 1 semente por braço a unidade de aleatorização é a semente, não a célula; subindo a unidade para *paisagem* o χ² cai a 3,50 (p=0,17, n.s.), e o experimento de 27 sementes reproduziu **8/8 braços** a partir de (dataset, semente) num sklearn independente. A decisão **DI-30 item 3** já nomeava o fenômeno e o mecanismo e o ratificava como achado científico legítimo. (e) **(2)** — reclassificado (3)→(2) pelo adversarial, direta. **O par "3,1× · χ²=21,6 · p<1e-4" do relatório F5 deve ser apagado.**

**A22 — Extrapolação para fora do suporte.** (c) F5 (`extrapolacao_fbest.csv`, citado): **95/104 pares (91,3%)** terminam com o melhor μ **abaixo do mínimo real do dataset**; 38/104 com μ negativo em objetivos não-negativos. (d) O PBI recompensa o menor μ; o GP fora do suporte devolve valores que dominam qualquer ponto real. É a razão de ser da ablação. ⚠ Caveat novo: nas 15 células de A20 a "extrapolação" é estática (a busca não anda) — o número deve ser lido nas 30 limpas. (e) **(1)**, direta.

**A23 — ⑥ na linha do b5, e a não-conformidade do ⑤ FECHADA.** (a)(b) DI-30.B3: o `.jsonl` do piso segue a linha **'b5'**, não a linha 'pisos', para permitir ler as duas colunas da ablação lado a lado. (c) Identidade de esquema confirmada: o conjunto de chaves do evento `decision` é `{caminho, f_best, fe, geracao, motivo, n_ds_membros, n_front1, rec, tempo_fit_s, ts}` em **45/45 células da s42** e **idêntico no smoke pós-T11** — a T11 **não acrescentou nenhum campo ao ⑥ deste config** (ver §4 item 4). **A não-conformidade que a F5 registrou como item 6 da torre está CORRIGIDA:** `params` ausente no ⑤ em **45/45 células da s42** (medido) × **presente no ⑤ do smoke T11** (`piso_offline.py:506` → `_params_efetivos`), e o gate G-7 rodado por mim sobre a pasta preservada devolve **`⑤ 6/6 chaves`**. (e) **(2)**, direta.

**A24 — Término e o ⑥ blindado.** (a)(b) O mapa de término deste config é `motivo_parada` no ⑤ (nunca `status` sozinho — bug B1). (c) `motivo_parada='orcamento'` em **45/45**, `status='ok'` 45/45, `footer.status='ok'` 45/45. A única mácula da s42 permanece onde estava: **`swap_small-lhs_ZDT1`** com 1 linha rasgada e **3 footers** (um `failed` de um escritor concorrente morto 2 min antes) — re-medido: `j_malformada=1` e `j_footer=3` em 1/45; as demais 44 têm `footer_status='ok|ok'`. **Dano zero, provado**: as ①③⑦ dessa célula são bit-idênticas às de `off/ZDT1` (A19). **A T11 fechou a causa em código**: `AuditLogger.__init__` agora aplica **`O_TRUNC` quando `append=False`** (`src/audit_log.py:136-138`), e tanto o runner (`piso_offline.py:344-345`) quanto o despachante (`experiments.py:143-144`) abrem assim ⇒ uma reescrita mais curta **não pode** deixar a cauda da anterior. O B-01 (`RunJaFechado`) proíbe append cego em run fechado, e o B-11 serializa por `flock` linhas acima de `PIPE_BUF`. A armadilha 25 da F5 vira histórica. (e) **(2)**, direta.

**A25 — 🎯 `tempo_aval_real_s`: o campo foi corrigido, o número mede a coisa errada.** (a) Não há prescrição de artigo; é instrumentação. (b) O item **I-02 da FASE G7** pôs um cronômetro no portão único de avaliação (`src/budget.py:241-252`) e fez o `export` aceitar **NULL**. A intenção está escrita duas vezes, textualmente: `budget.py:192-202` — *"`None` é o ponto do item: 'não medi' ≠ 'custou zero'. No offline o orçamento nasce ESGOTADO e nenhuma avaliação real acontece no run — gravar 0.0 ali afirmaria que avaliar custou zero"* — e `piso_offline.py:490-495` repete a justificativa. (c) **Medido.** Na s42: `tempo_aval_real_s = 0.0` literal em **45/45**. No smoke pós-T11: **`0.0001`** — não é NULL. A razão está em `standalone_harness.py:655-657`: `load_offline_budget` **passa o dataset inteiro pelo portão** (`bud.evaluate(X[i], lambda _x,_f=F[i]: _f)`), então o contador `_n_avals_cronometradas` é n>0 e a propriedade nunca devolve None. O que ele cronometra é a `lambda` que devolve a linha do artefato. Quantifiquei nos 11 smokes Python: **online 25,41 µs/FE** (mediana; c122 34,4 · c149 24,6 · c154 26,2 · c262 23,0 · e81 26,2 · sobol_batch 12,0) contra **offline 1,14 µs/FE** (b5m 1,64 · moead_media 1,64 · b5r 0,97 · c311 0,97 · treed_media 1,14) — **22,2× de diferença**, a assinatura de que o offline não avalia nada. (d) A correção acertou o alvo global (todo runner Python herda a medida) e errou o caso offline, porque o portão foi projetado como ponto único de avaliação e o offline o usa como ponto de **ingestão**. (e) **(3) 🎯** — nenhuma decisão sanciona o número, e ele **contradiz a docstring do próprio código**. Impacto no mecanismo: **nulo**; impacto na leitura: quem somar `tempo_aval_real_s` para "quanto custou avaliar" nos 5 offline lerá o custo de um `lambda`. Conserto: 1 linha (`bud.tempo_aval_real_s` não deve contar as avaliações de carga, ou o offline passa `None` explicitamente). Detalhe em §8.

---

## 3. Percentuais por classe

**Denominador = 25 aspectos** (os 7 T listados à parte, §9). Consolidei os 33 aspectos da F5 em 25 (fusões: U3+F1→A3, U4+U5→A4, U9+U10→A8, C8+cadeia A8→A20, C9a+C9b→A21, C11+I-07→A23, C12+G1→A24) e acrescentei A15/A25 como aspectos com conteúdo novo.

| classe | contagem | % | quais |
|---|---|---|---|
| **(1)** conforme o método canônico / o gabarito D77 | **6/25** | **24,0%** | A2, A8, A13*, A17, A19, A22 |
| **(2)** desvio sancionado (decisão citada no bloco) | **18/25** | **72,0%** | A1, A3, A4, A5, A6, A7, A9, A10, A11, A12, A14, A15, A16, A18, A20, A21, A23, A24 |
| **(3)** desvio inexplicado 🎯 | **1/25** | **4,0%** | **A25** (`tempo_aval_real_s` no offline) |
| **T** teto (fora do denominador) | 7 | — | T1…T7, §9 |

\* A13 é **direta-declarativa** (Botão 3).

**Comparação honesta com a F5 (9/28 · 18/28 · 1/28 = 32,1 / 64,3 / 3,6%):** o denominador mudou por **consolidação**, não por descoberta — a queda de (1) de 32,1% para 24,0% vem de (i) fusões que absorveram aspectos (1) dentro de blocos (2) (U5 dentro de A4, U9 dentro de A8 sobreviveu, U2 permaneceu) e (ii) de **uma reclassificação substantiva: A20 saiu de (1) e virou (2)**. O item (3) da F5 (C9b) **caiu** no adversarial; o item (3) de hoje é **outro e novo** (A25), nascido da própria T11.

---

## 4. 🆕 AS CORREÇÕES DA T11 — implementada? funciona de fato?

Escopo: os itens da T11 que tocam `moead_media` são **A3** (família b5: I-05, wrapper do `adapt`, `params` no ⑤, `granularidade_③`), **G7** (I-02 cronômetro, I-09 `repo_hash`), **G3** (`campanha_id`), **G1** (⑥ blindado), **G2** (B-02 no-op, B-16 `NO_RETRY`), **G5** (checkpoint), **G6** (gate G-6 e o `contrato_61.json`). Evidência marcada: **[M]** medida no smoke/dado · **[C]** lida em código com arquivo:linha · **[V]** veredito registrado pela T11.

| # | correção | implementada? | funciona de fato? | evidência |
|---|---|---|---|---|
| 1 | **`params` no ⑤ (I-07/A3)** | ✅ | ✅ **SIM** | [M] s42 `params` ausente 45/45 → smoke **presente**, 9 chaves; gate G-7 `⑤ 6/6`. [C] `piso_offline.py:193-206, 506` |
| 2 | **Identidade de campanha (G3/I-09)** | ✅ | ✅ **SIM** | [M] s42: `schema_version=1`, `campanha_id` ausente, `repo_hash=null` em **45/45** → smoke: `schema_version=2`, `campanha_id='9ad0138aa9a4_2026-07-31'`, `repo_hash='9ad0138a…'`; G-3 OK |
| 3 | **`granularidade_③` no `sigma_dict` (A3/b5r-A30)** | ✅ | ✅ **SIM, e é VERDADEIRA** | [M] chave nova (única diferença entre os 20 do `sigma_dict` da s42 e os 21 do smoke) + **prova no dado**: LHS score 1,0000 na ger 1 em 45/45; ger 2 → 0,070; passos de seleção × N = **40.000 exato** (M=2). [C] `piso_offline.py:229-231` |
| 4 | **I-05 · instrumentação da cadeia `adapt` (o congelamento)** | ❌ **NÃO no meu config** e ⚠ **INERTE no gêmeo** | ❌ **NÃO** | [C] `src/piso_offline.py` tem **zero** ocorrências de `adapt`/`flag_vetores_degenerados`; a instrumentação vive só em `src/b5_prob.py:113-137`. [M] E lá ela **não mede nada**: no smoke do b5m o campo `flag_vetores_degenerados` está presente em **801/801** eventos e é **NULL em 801/801**. [C] A causa: `b5_prob.py:118` lê `evolver.population.problem.reference_vectors.values`, mas os vetores vivem no **EA** (`desdeo_emo/EAs/BaseEA.py:182`) e `desdeo_problem/Problem.py` tem **zero** ocorrências de `reference_vectors` ⇒ `AttributeError` engolido pelo `except Exception: return None` (`:135`). **O padrão do c217, exato: o campo existe, o dado não.** Conserto: 1 token (`evolver.reference_vectors.values`) |
| 5 | **`p_wrong_stats` declarado NÃO-APLICÁVEL (ERRATA 12)** | ✅ | ✅ **SIM, e protege a ablação** | [M] `contrato_61.json → configs.moead_media.nao_se_aplica.p_wrong_stats` traz a justificativa correta ("exigir este campo é INVERTIDO"); [M] 0 ocorrências em 30.165 eventos da s42 e 0 em 801 do smoke, contra 800/801 no b5m ⇒ o piso **não** passa pelo `ProbMOEAD_select` |
| 6 | **⑥ blindado (G1/B-01/B-11)** | ✅ | ✅ **SIM** (fecha o defeito da F5) | [C] `audit_log.py:136-138` `O_TRUNC` se `append=False`; `:120-130` `RunJaFechado`; `:159-172` `flock` acima de PIPE_BUF. [C] runner e despachante abrem com `append=False`. Torna estruturalmente impossível a cauda órfã de `swap_small-lhs_ZDT1` |
| 7 | **I-02 cronômetro de avaliação (G7)** | ✅ | ⚠ **PARCIAL — erra no offline** | [M] ver **A25**: 0.0001 s = 1,64 µs/FE contra 25,41 µs/FE nos online; a docstring do próprio código pede **NULL** |
| 8 | **`NO_RETRY` (G2/B-16)** | ✅ | ✅ (inócuo aqui) | [C] `experiments.py:83-88`, os 3 padrões determinísticos. [M] o piso tem `n_retries=0` e `status='ok'` em 45/45 ⇒ nunca aciona |
| 9 | **Checkpoint periódico (G5)** | ⚪ **fora por desenho** | n/a | [C] `Checkpointer` importado em 8 runners; `piso_offline.py` não. [V] `T11_STATUS.md:52-53`: *"b5r/b5m/moead_media FORA por desenho — a ③ deles nasce no replay pós-laço, um checkpoint no meio gravaria ③ vazia; eles já truncam com dado via `teto_s`"*. Confirmei o rito de teto em código (`piso_offline.py:411-418` + `:498-512`): no `teto_wall` o run **grava as camadas** com `status='failed'` antes de encerrar |
| 10 | **Gate G-6 de não-perturbação** | ✅ | ⚠ **VÁCUO para os 5 offline** | [C] `scripts/naoperturbacao.py:150-165` compara **apenas o sha256 da ①**. No offline a ① **é o dataset**, escrita a partir de `bud.records` que nascem em `load_offline_budget` (`piso_offline.py:334`) **antes** da sonda (`:395`) e da busca (`:409`) ⇒ o hash é idêntico com e sem sonda **por construção**, e o gate não pode reprovar. O selo `moead_media 8e690c81e3f095a5` (T11 §5) é real e é **não-informativo** para este config. A prova correta seria a ③/⑦. Ver T6 |

**Balanço.** 6 correções funcionam e 1 é inaplicável por desenho justificado; **1 está errada no offline (item 7 → o (3) desta rodada)** e **1 — justamente a que a F5.4 pediu para este config — não foi feita e, no gêmeo, foi feita de forma inerte (item 4)**. O pedido nº 1 do veredito `b5m-A8` era textual: *"Instrumentar o gatilho (read-only) em `src/b5_prob.py` **e `src/piso_offline.py`**: um wrapper de `ReferenceVectors.adapt` que loga por iterate `amp_fitness` (float64, M valores), `n_vetores_norma0` e `vetores_degenerados=bool` — captura também o caso PARCIAL"*. Entregue: nenhum wrapper, nenhum `amp_fitness`, nada em `piso_offline.py`, e o `flag_vetores_degenerados` do b5m NULL em 801/801. **A instrumentação foi para o lado da ablação onde o fenômeno é 4,6× menos frequente, e mesmo lá não gravou.**

---

## 5. Comparação canônica — **N/A** (config sem artigo); o que vale é: **o piso funciona como régua?**

Não há paper: o gabarito é a especificação canônica do bundle (D77/DEF-E3) + o REGISTRO. Sem interseção, âncora direcional ou faixa-guia J a computar.

**(i) A régua é cirúrgica — confirmado e agora também no código de hoje.** Ver A17: mesmo motor (`n_ger` ≡ b5m em 45/45 e 801≡801 no smoke pós-T11), mesmo lattice, mesmo orçamento (40.000 exatos de seleção), mesmo dataset (ΔX=Δf=0), mesmos 20.000 pontos de régua (ΔX=0), mesma especificação de surrogate (μ a 1 ULP em 62,5%), `p_wrong_stats` ausente em 100% dos eventos. **A única diferença executável é a seleção.**

**(ii) A régua discrimina — mas o número da F5 estava otimista e o corte estava errado.** A métrica oficial da F5.2c é 100% indiscriminante no offline (lê o f da ①, que é o mesmo dataset). O endpoint é a ⑦ (`t4_ablacao_corrigida.csv`, união de `transversal_offline_camada7.csv` + `camada7_sweep.csv`):

| corte | n | piso vence b5m | razão IGD+⑦ piso/b5m (mediana) | penalidade de remover σ |
|---|---:|---:|---:|---:|
| **todas** | 45 | 18/45 | **1,500** | +50,0% |
| limpas do confundidor da **sonda** (o corte da F5) | 31 | 14/31 | 1,351 | +35,1% |
| **limpas do confundidor A8 (vetores degenerados) — o corte correto** | **30** | **14/30** | **1,220** | **+22,0%** |
| só as 15 degeneradas | 15 | 4/15 | 1,896 | +89,6% |

Duas correções à F5: a mediana das 45 é **1,500** (a F5 escreveu "~1,4"), e o **conjunto de exclusão certo é o A8, não o da sonda** — as 14 células de colapso do GP são um **subconjunto** das 15 com vetores degenerados (união = 15), e o critério A8 é o operacionalmente relevante porque marca "a busca morreu", não apenas "o modelo é ruim". Com o corte certo, **remover σ custa ~22% de IGD+ na mediana** (não 35%) e o piso vence em 14/30.

**(iii) O preço de σ está atribuído.** 2,18 h × 37,42 h nas mesmas 45 células (44,4× por célula); `t_busca` 62,5× e `t_fit` 0,97× ⇒ **σ custa ~62× de busca e compra ~22% de IGD+ na mediana das células limpas**.

**(iv) A régua não é degenerada — nas 30 limpas.** Sonda com WAPE mediana 0,127 e correlação 0,934 nos 76 pares sadios; ND não-vazio em 45/45.

**(v) O caveat ficou MAIOR e mais preciso.** Em **15/45 células (33,3%)** o contraste não mede σ — mede "busca morta × busca viva". Em 4 delas a ⑦ tem **1 ou 2 X distintos**; em 1 delas (`swap_medium-lhs_MMF16_20`) a ⑦ é a **população LHS inicial intacta** e ainda assim "vence" o b5m por 8,8×. As leituras de ablação da F5.5 e do D97 devem ser reportadas **duas vezes: nas 45 e nas 30**.

**Veredito: SIM, o piso cumpre a função de régua — com a ressalva (v) reescrita e ampliada.**

---

## 6. Saúde em escala (corpus principal = s42)

**6.1 Sonda — régua Sobol, 1 bloco por congelamento.** 104 pares célula×objetivo, 900.000 predições. **28 pares (26,9%) colapsados** em 14 células; nos **76 sadios**: WAPE mediana **0,1268** (q25 0,0179 · q75 0,2711), corr mediana **0,9337**. `cobertura95` vazia em 104/104 (correto por regra; σ NULL em 100% dos pontos — contraste com a inflação a 1,0000 do c311). **Não há bloco `sonda_estratificada` neste config** (não é classificador) ⇒ a **regra 12 do CONTRATO §10 não é acionada**; a régua Sobol é o único bloco e é o único comparável entre configs.

**6.2 Trajetórias.** 45 arquivos × 19 transições = **855 transições, 0 violações de monotonicidade de IGD+** (F5, citado). **Ressalva obrigatória**: no offline a trajetória percorre a *acumulação do dataset*, monótona por construção — não é curva de aprendizado.

**6.3 ⑦ — a descoberta de saúde desta rodada: a ⑦ do piso é 33,8% duplicada.** `t6_camada7_duplicatas.csv`, 45 células × 3 configs:

| config | células com ⑦ duplicada | linhas duplicadas | células com ≤2 X distintos |
|---|---:|---:|---:|
| **moead_media** | **18/45** | **1.020 / 3.020 (33,8%)** | **5** |
| b5m | 31/45 | 508 | 1 |
| b5r | **0/45** | **0** | 0 |

As 4 células com `nd_pos_real/n_final = 1,000` — **BBOB_F17 (1 X ×50), swap_medium-mvns_WFG9 (1 X ×50), swap_medium-lhs_DTLZ2 (1 X ×105), swap_medium-mvns_ZDT4 (2 X ×50)** — são **exatamente** as 4 que a F5 citou como "fantasia máxima", e a causa agora está provada: são cópias do mesmo ponto, e cópias não se dominam. **Consequência dura: `nd_pos_real` e a "razão de fantasia" NÃO são indicadores de qualidade neste config**; o IGD+⑦ é o endpoint, e mesmo ele precisa do corte das 15.

**6.4 Erro de fantasia comparado.** F5 (citado): piso 69/104 pares 100% otimistas × b5m 29/104 × b5r 24/104; WAPE da população final mediana 0,985 (piso) × 0,256 (b5m). Somado a A22, é a prova quantitativa de que σ impede a busca de colonizar a extrapolação — **nas células em que a busca anda**.

**6.5 Contrato e integridade.** 45 linhas em `contrato_f52b.csv` (a única não-conformidade — ⑤ sem `params` — está **CORRIGIDA em código**, §4 item 1) e **1** linha em `integridade_f52a.csv` (`swap_small-lhs_ZDT1`, dano zero provado, causa **fechada em código**, §4 item 6). **0 células reprovadas** nas duas fases.

---

## 7. SCORE, RECOMENDAÇÃO e VEREDITO

### **SCORE: 9,3/10 · RECOMENDAÇÃO: ACEITAR + CAVEAT**
### **VEREDITO: MANTEVE**

**A régua da comparação.** O `scores_f53.csv` registra **9,0**; o veredito adversarial `moead_media-C9b.md` §Impacto item 3 determinou a subida para **9,5** ao derrubar o único (3) da F5. A base honesta de comparação é, portanto, **9,5**, e não 9,0.

**Por que MANTEVE — a causa nomeada, item a item:**

1. **O mecanismo não mudou, e isso está MEDIDO, não presumido.** O `sigma_dict` do smoke pós-T11 é **idêntico** ao da s42 nas 20 chaves de mecanismo (única diferença: a chave nova `granularidade_③`, que é *declaração*, não comportamento). O smoke reproduz a assinatura inteira: `n_geracoes=801`, `fe_final=61`, 40.050 linhas de busca, 20.000 de sonda, N=50, σ NaN 100%, ⑥ com o mesmo conjunto de chaves. A campanha T11 foi, para este config, **read-only sobre o comportamento** — e a s42 continua sendo evidência válida da busca que o código de hoje faria.
2. **O que subiu (+):** a não-conformidade de contrato da F5 (⑤ sem `params`) **fechou** e eu a verifiquei no dado; a causa do único defeito de integridade da F5 (o resíduo de dois escritores) **fechou em código** (`O_TRUNC`); a identidade de campanha (`campanha_id`/`repo_hash`/schema v2) entrou; a `granularidade_③` **converteu um teto de leitura em fato provado** (LHS 1,0000 em 45/45; 40.000 exatos de seleção); e a ERRATA 12 **blindou a ablação** ao declarar `p_wrong_stats` inaplicável com o argumento certo.
3. **O que desceu (−):** nasceu **um (3) novo** (A25, `tempo_aval_real_s` medindo uma `lambda` de ingestão no offline, 22,2× fora da escala dos online, contra a docstring do próprio código); e a correção que a F5.4 pediu **por nome para `src/piso_offline.py`** — o wrapper do `adapt` — **não foi entregue**, enquanto a versão dela no gêmeo grava **NULL em 801/801** por ler o atributo errado. O resultado é que a **cadeia que domina a dinâmica deste config permanece invisível no log** — em 30 sementes serão 450 células com o mesmo buraco.
4. **O que mudou de leitura sem mudar de nota:** A20 saiu de (1) para (2). Não é uma piora do config — é uma **correção da minha análise anterior**: o congelamento não é ponto fixo do PBI, é o `adapt` zerando o lattice, e a evidência (r=0,913; 4.189/4.201 terminais nas 13 células degeneradas; a ⑦ = LHS inicial em `swap_medium-lhs_MMF16_20`) é mais forte do que a que eu tinha. E ela **piora o caveat científico**, não a fidelidade: o corte de exclusão da ablação passa de 14 para 15 células e a penalidade de remover σ cai de +35,1% para **+22,0%**.
5. **Aritmética da nota.** Régua do FRAMEWORK §F5.3b: com **1 item (3) periférico, investigado, causa provada e benigna para o mecanismo**, o teto é **9**; o contrato limpo e os dois "teoremas" (determinismo por re-run e ablação cirúrgica, agora re-provada no código pós-T11) sustentam **9,3**. Não sobe a 9,5+ porque a T11 introduziu um (3) e deixou aberta a instrumentação que a própria F5.4 pediu; não cai abaixo de 9 porque **nenhum aspecto do laço central é (3)** e as ~40 invariantes estruturais fecham 45/45.

*(Se a torre preferir a comparação contra o número impresso no relatório F5 — 9,0 — então o veredito seria "MELHOROU +0,3"; seria enganoso, porque +0,5 desse delta foi ganho pelo adversarial em 2026-07-29 e não pela T11.)*

---

## 8. Aspecto classe (3) 🎯 — evidência completa

**🎯 A25 — `tempo_aval_real_s` no regime offline: campo corrigido, número inválido.**

- **Fato medido (s42, 45 células):** `timing.tempo_aval_real_s = 0.0` **literal** em 45/45 manifestos.
- **Fato medido (smoke pós-T11, `off/moead_media/MMF1/s0`):** `0.0001` — **não** o `None` que o código promete.
- **A promessa, textual, em dois lugares:** `src/budget.py:192-202` (*"`None` é o ponto do item: 'não medi' ≠ 'custou zero'. No offline… gravar 0.0 ali afirmaria que avaliar custou zero"*) e `src/piso_offline.py:490-495` (*"[I-02] NULL, não 0.0… `bud.tempo_aval_real_s` devolve None quando nenhuma avaliação passou pelo portão"*).
- **A causa, em código:** `src/standalone_harness.py:655-657` — `load_offline_budget` empurra as n linhas do dataset **pelo portão** (`bud.evaluate(X[i], lambda _x,_f=F[i]: _f)`), logo `_n_avals_cronometradas = n > 0` e `budget.py:200-202` nunca devolve `None`. O cronômetro de `budget.py:249-251` mede a `lambda`.
- **A prova quantitativa (11 smokes Python, µs por FE):** ONLINE **25,41** mediana (c122 34,43 · c149 24,59 · c154 26,23 · c262 22,95 · e81 26,23 · sobol_batch 11,97) × OFFLINE **1,14** mediana (b5m 1,64 · **moead_media 1,64** · b5r 0,97 · c311 0,97 · treed_media 1,14 sobre 50.000 FE). **Razão 22,2×.** Uma avaliação analítica real não custa 1 µs; um `dict`-lookup custa.
- **Por que é (3) e não (2):** nenhuma decisão do REGISTRO sanciona o valor, e ele **contradiz a especificação escrita do próprio item I-02**. Não é ambiguidade de leitura — é o campo afirmando um fato falso ("avaliar 61 pontos custou 0,1 ms").
- **Impacto no mecanismo:** **zero**. Nenhuma camada, gate, métrica ou invariante deste config consome `tempo_aval_real_s`; o `t_fit`/`t_busca`/`t_sonda` (que sustentam A6 e A17) vêm de outros cronômetros e estão corretos.
- **Impacto na leitura:** afeta **os 5 configs offline** (b5m, b5r, c311, moead_media, treed_media) — em 30 sementes, ~1.600 células com um número que parece medição e não é. E a mesma armadilha da ERRATA 6/13 da própria T11 (procurar o campo em vez de conferir o dado) é o que a produziu.
- **Conserto sugerido (decisão do autor, D81 — NÃO implementar sozinho):** ou `load_offline_budget` ingere fora do cronômetro (`bud._t...` não incrementa na carga), ou o runner offline passa `tempo_aval_real_s=None` explicitamente. **1 linha em 1 dos 2 lugares**, sem re-run.

---

## 9. Teto de verificabilidade (T) e armadilhas

**T (7 itens, fora do denominador):**
- **T1 · kernel/HP ajustados do GPR** — declarado no `sigma_dict` 45/45; `modelo_hp` NULL por DI-30.B2; a especificação foi **lida** (`SurrogateKriging.py:23-24`) mas os θ ajustados não são gravados. Evidência empírica só indireta (o padrão de colapso de A21). **T mantido.**
- **T2 · rampa θ do PBI** — **sai do "não-verificável" para "lido em código"**: `ProbMOEAD.py:32-33` (`theta_min=0`, `theta_max=500`) e `:161` (`theta_adaptive = θmin + (θmax−θmin)·fe/40000`). Não aparece em nenhuma camada ⇒ **T no dado**.
- **T3 · parâmetros internos do MOEA/D** — **também lidos agora**: `n_neighbors=20` (T canônico), `SF_type='PBI'`, `n_parents=2`, `SBX_xover()` com **ProC=1, DisC(η_c)=30**, `BP_mutation(lb,ub)` com **ProM=1/D, DisM(η_m)=20**, mating **sempre** dentro da vizinhança (δ efetivo = 1,0) e **sem cap `nr`** de substituições — todos defaults do vendor, iguais aos do b5m por construção. ⚠ **O `params` que a T11 acrescentou ao ⑤ NÃO grava nenhum deles** (grava alg/mode/motor/surrogate/sigma/treino/n_dataset/regime/q) ⇒ **T no dado permanece**. É o item mais barato de fechar.
- **T4 · não-consumo de σ na seleção** — contrafactual; `_predict` devolve `(mu, None)` (`piso_offline.py:389`) mas `problem.evaluate` ainda computa `.uncertainity` internamente. Só código prova. **T.**
- **T5 · patches vendorizados inertes no mode 12** — declarativo (`sigma_dict.patches_vendorizados`), coberto por `anchors.json`+`repos.lock`. **T.**
- **T6 · 🆕 não-perturbação da sonda neste config** — o gate G-6 compara **só o sha256 da ①**, e no offline a ① é o dataset, escrito antes da sonda ⇒ **o gate não pode reprovar**. O código sustenta a invariante (`GaussianProcessRegressor.predict` é determinístico e não move RNG; se movesse, o LHS inicial de A15 mudaria e a ③ divergiria inteira), mas **o dado não a prova para os 5 offline**. **T novo.**
- **T7 · 🆕 o gatilho da cadeia A8** — nem o piso nem o b5m gravam a amplitude float64 no instante do `adapt`. Minha medição (§A20) usa o `ptp` da ③ em **float32** (D53) — o veredito `b5m-A8` demonstrou que o float32 **não distingue 6,7e-76 de 0,0** e por isso não resolve o *timing* exato do gatilho, só o seu efeito. Meu r=0,913 e as 15 células são sólidos; o instante preciso em que cada célula degenera **não é verificável neste corpus**. **T novo — e é exatamente o que a correção nº 4 da §4 deveria ter fechado.**

**Saiu do teto:** semeadura/RNG (provada por re-run, A19) e a granularidade da ③ (provada por LHS, A15).

**Armadilhas (continuando a numeração da F5; 20–28 revalidadas, 29–33 novas):**
- **(22) REESCRITA** — "fantasia alta ≠ bom" agora tem causa: as 4 células com `nd_pos_real/n_final = 1,000` têm **1 ou 2 X distintos** replicados. 33,8% das linhas da ⑦ do piso são duplicatas (0% no b5r).
- **(25) HISTÓRICA** — o footer `failed` residual de `swap_small-lhs_ZDT1` não pode mais acontecer (`O_TRUNC`, `audit_log.py:136-138`). A regra de término continua sendo `motivo_parada` do ⑤.
- **(29) 🆕 O congelamento do piso não é "convergência".** Em 15/45 células a busca **morre** por vetores de referência nulos. Ler turnover baixo como "regime estacionário conservador" (o que a F5 fez) é errado nessas células.
- **(30) 🆕 O corte de exclusão da ablação é o A8, não o da sonda.** 15 células (não 14); a de fora do radar da sonda é `swap_medium-mvns_WFG9`. Penalidade de remover σ: **+22,0%**, não +35,1%.
- **(31) 🆕 As "vitórias" mais espetaculares do piso são buscas mortas.** `ZDT6` (62× melhor que o b5m) congela na geração 118 com 3 X distintos; `swap_medium-lhs_MMF16_20` (8,8× melhor) entrega **a população LHS inicial intacta**. Não citar como "onde a incerteza atrapalha o b5m".
- **(32) 🆕 `tempo_aval_real_s` dos 5 offline não é tempo de avaliação** — é o custo do `lambda` de carga (1,14 µs/FE contra 25,41 dos online).
- **(33) 🆕 O selo G-6 dos configs offline é não-informativo** (compara só a ①, que é o dataset). Não citar "não-perturbação provada em 19/19" para b5m/b5r/c311/moead_media/treed_media sem essa ressalva.

**O que este corpus NÃO permite verificar:** (i) o instante exato do gatilho A8 (float32, T7); (ii) os HP ajustados do GPR (T1) e os parâmetros internos do MOEA/D no dado (T3); (iii) a não-perturbação da sonda para este config (T6); (iv) **separar "mecanismo" de "semente infeliz"** em qualquer taxa (colapso do GP, degeneração de vetores, congelamento) — **há 1 semente por braço**, e o adversarial já provou que a unidade de aleatorização é a semente; só M8/M9 (30 sementes) responde; (v) o comportamento sob o **teto** (`teto_wall`) — nenhuma célula da s42 o acionou, e o smoke do rito rodou no c154, não aqui; (vi) o tier **big** do piso (é o `treed_media`, config à parte).

---

### Rodapé — artefatos de evidência

**Escrita (única pasta tocada):** `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/moead_media/`
**Scripts** (READ-ONLY nos dados; interpretador `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`):
`t1_estrutural_s42.py` (re-medição integral das 45 células: ⑤①②③④⑦⑥, ~60 invariantes) · `t2_granularidade3.py` (prova de LHS da geração 1 nos bounds reais + contagem de passos de seleção) · `t3_adapt_degenerado.py` (a cadeia `adapt`→vetores nulos→congelamento, 135 células = 45×3 configs) · `t4_ablacao_corrigida.py` (IGD+⑦ piso×b5m sob os dois cortes de confundidor) · `t5_binding_sonda_determinismo.py` (U2 bit-a-bit, U5 join posicional, C7 re-run).
**CSVs:** `t1_estrutural_s42.csv` (45×~90 colunas) · `t2_granularidade3.csv` · `t3_adapt_degenerado.csv` + `t3_adapt_detalhe.csv` · `t4_ablacao_corrigida.csv` · `t5_binding.csv` + `t5_determinismo.csv` · `t6_camada7_duplicatas.csv`.
**Insumos pré-computados consumidos (não recomputados):** `f5/sonda_f52e.csv` · `f5/tempo_f52d.csv` · `f5/contrato_f52b.csv` · `f5/integridade_f52a.csv` · `f5/transversal_offline_camada7.csv` · `f5/baterias/moead_media/camada7_sweep.csv`.
**Corpora lidos:** `resultados_experimentos/moead_media|b5m|b5r/*/42/` (135 células) · `evidencia_T11/smoke_python/experiments/**` (11 manifestos + ⑥/③/①/⑦ do piso e do b5m) · `ua-dd-saea/src/*.py`, `experiments.py`, `scripts/naoperturbacao.py`, `scripts/gates_proveniencia.py`, `algorithms/b5_Prob-RVEA/desdeo_emo/**` (leitura apenas).
**Nenhuma célula foi executada; `experiments.py` não foi invocado; `data/experiments` não foi tocado.**