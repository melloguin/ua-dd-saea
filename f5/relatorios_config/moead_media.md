# RELATÓRIO DE FIDELIDADE — `moead_media` (MOEA/D-média · piso offline D77) · F5.3b · semente 42

**Universo**: **45/45 células analisadas** (25 `off` + 20 `sweep` = {small,medium}×{lhs,mvns}×{DTLZ2, MMF16_20, WFG9, ZDT1, ZDT4}) — **zero exclusões**: o config não tem célula REPROVADA na F5.1 nem na F5.2a. **Todas as 45 rodaram no `mac`** (`tempo_f52d.csv`) ⇒ **piso de ruído entre máquinas NÃO se aplica** ao contraste interno nem ao contraste piso×b5m/b5r (também 45/45 `mac`); aplica-se somente ao contraste com `e103` (45/45 `vm3`). Agregados da bateria: **30.165 eventos `decision`**, **2.701.620 linhas de ③**, **1.801.620 avaliações-surrogate**, **900.000 predições de sonda**, **30.120 transições de população**, **855 transições de trajetória**, **104 pares célula×objetivo** de sonda e de fantasia-final. Já verificado e **citado, não refeito**: gates F5.1 verdes (FE exato, binding por hash, ⑦ presente) e F5.2c/e (métricas 664/664, sonda 461 células) — `RELATORIO_F5.md` §4.3/§5.

---

## 1. Ficha do mecanismo

**O que é (D77 / DEF-E3).** Piso do regime offline: um **MOEA/D rodando sobre um surrogate treinado uma única vez no dataset, usando SÓ a média**. Motor: classe `MOEA_D` (**mode 12**, Gen-MOEA/D com decomposição **PBI**) do `desdeo_emo` vendorizado, seleção `MOEAD_select` — **a ablação exata do b5m** (mode 72, `ProbMOEAD_select`, comparação MC pareada `P_wrong>0,5`). Surrogate: `SurrogateKriging` (1 `GaussianProcessRegressor` por objetivo; kernel `C(1,(1e-3,1e3))·RBF(10,(1e-2,1e2))`, `alpha=0`, `n_restarts_optimizer=9`, `normalize_y=False`), treino único no dataset, **independente por config** (DI-28). População = **lattice Das-Dennis herdado do b5m** (50 em M=2 / 105 em M=3 — DI-16.4/D65; a nota "N interno = 100" está SUPERADA). Orçamento interno **40.000 avaliações-surrogate** (ancorado no b5). **Zero FE real na busca**; o endpoint é a ⑦ (`__final.parquet`): a população final avaliada **1×** na função verdadeira e só **depois** filtrada por não-dominância (DI-13.9/DI-08). σ **não é reportado nem consumido** (DI-16.1) — é exatamente o que a ablação remove. Duas instâncias por tier (P5/DI-16.5): **small/medium = `env_b5`** (este relatório); **big = `treed_media`** em `env_c311`. ND final **sem cap** (D68). Divergências sancionadas em jogo: DI-16.1 (σ NULL), DI-16.4 (lattice), DI-16.17 (② vazia), DI-13.5 (sonda com `geracao` NULL), DI-28/DI-28.3 (treino independente + LHS determinístico), DI-30.B2 (`modelo_hp` NULL), DI-30.B3 (⑥ na linha do b5), D90/D51 (tiers/dists), D68 (sem cap).

---

## 2. DISSECAÇÃO DOS ASPECTOS

### 2.1 Tabela-resumo (33 aspectos; 1 linha cada)

| # | aspecto | classe | verif. | resultado-síntese (45 células) |
|---|---|---|---|---|
| U1 | ① = dataset inteiro, 100% `init`, `fe_index` denso | (2) | direta | 45/45 · `n①=maxfe=fe_final` · 100% init · `arange(N)` 45/45 |
| U2 | binding ①↔artefato do dataset + `cp_init_offline` | (1) | direta | **ΔX = 0,0 e Δf = 0,0 bit-a-bit em 45/45**; `doe_hash≡x_hash` 45/45 |
| U3 | ④ = 1 linha ≡ `fit_series` (treino único) | (2) | direta | 45/45; `n_acumulado = n①` 45/45 |
| U4 | sonda: 1 bloco de 20.000; `geracao` NULL na ③ | (2) | direta | 45/45 · 1 evento `sonda` · `hash_check='ok'` 45/45 |
| U5 | join posicional sonda×gabarito | (1) | direta | **max\|ΔX\| = 0,0 em 900.000 pontos**; hashes ≡ manifesto do artefato 45/45 |
| U6 | WAPE no espaço cru; cobertura **N/A** (σ NULL) | (2) | direta | recomputo bate a F5.2e em ≤4,7e-7; `cobertura95` vazia em 104/104 |
| U7 | `fit+busca ≤ tempo_geracao_s`; sonda excluída | (2) | direta | **igualdade** com max\|Δ\|=1,5e-5 s em 45/45; `t_sonda>0` 45/45 |
| U8 | `fe_treino_max` = N−1 constante | (2) | direta | 45/45 (8 valores distintos, 1 por tamanho de dataset) |
| U9 | guards ⑥ ≡ agregados ⑤ | (1) | direta | **0 eventos `guard`**; `cache_hits`=0 no ⑤ e no footer 45/45 |
| U10 | aritmética entre camadas | (1) | direta | ③off = N×n_ger 45/45 · decisões = n_ger 45/45 · geração densa 45/45 |
| U11 | erro de fantasia (μ da pop final × f real) | (2) | direta | **69/104 pares com 100% de otimismo**; WAPE-final mediano 0,985 |
| U12 | ⑦: ND recomputada, link posicional, sem cap | (2) | direta | recomputo **exato 45/45**; link X **bit-a-bit 45/45**; n⑦ = N 45/45 |
| F1 | congelamento do modelo (1 bloco, não 2) | (2) | direta | 1 bloco 45/45 + ④ 1 linha + `fe_treino_max` constante |
| F2 | σ 100% NULL — a ablação materializada | (2) | direta | **2.701.620/2.701.620 linhas com σ NaN**; μ NaN em 0 |
| F3 | ② vazia · `real_solution_id` NULL · `n_ds_membros`=0 | (2) | direta | 0 linhas na ② 45/45; NULL 100% 45/45; 30.165/30.165 eventos |
| C1 | motor MOEA/D mode 12 + PBI | (1) | direta-declarativa | `modelo_flag`/`motivo` uniformes 45/45 + corroboração indireta (C5) |
| C2 | lattice 50/105 herdado do b5m (não 100) | (2) | direta | 50 em 31 células M=2 · 105 em 14 M=3; pop constante 45/45 |
| C3 | 40.000 aval-surrogate + overshoot ≤ 1 geração | (2) | direta | 40.050 (M=2) / 40.005 (M=3); `n_ger = ⌊40000/N⌋+1` 45/45 |
| C4 | Kriging: mesma espec., treino independente; espaço cru; `modelo_hp` NULL | (2) | direta | μ ≡ b5m a ≤1e-5 em **65/104**; `espaco_modelo='cru'` e transf NULL 45/45 |
| C5 | **ablação cirúrgica provada** + custo | (1) | direta | **`n_geracoes`(piso) ≡ `n_geracoes`(b5m) em 45/45**; `t_fit` razão 0,97; `t_busca` 62,5× |
| C6 | 2 instâncias por tier (big ≠ este config) | (2) | direta | 0 células `big`; `env_b5` 45/45; tiers small 35 / medium 10 |
| C7 | **determinismo/RNG provado por re-run** | (1) | direta | ①/③/⑦ **bit-idênticas** entre `off` e `swap_small-lhs` em 5/5 problemas |
| C8 | dinâmica da população (turnover/congelamento) | (1) | direta | 96,9%→9,3% (1ª→último quarto); 7.113/30.120 gerações congeladas |
| C9a | colapso do GPR para a média a priori (μ≡0) | (2) | direta | **28/104 pares** (WAPE=1,000, \|corr\|≤0,015) em 14/45 células |
| C9b | **assimetria da taxa de colapso** piso 26,9% × b5m 8,7% × b5r 4,8% | **(3) 🎯** | direta | χ²=21,6 (gl 2, p<1e-4) sobre o MESMO dataset e a MESMA especificação |
| C10 | extrapolação para fora do suporte | (1) | direta | `f_best` final **abaixo do mínimo do dataset em 95/104** (91,3%) |
| C11 | ⑥ na linha do b5 (DI-30.B3) + ⑤ sem `params` | (2) | direta | conjunto de chaves ≡ b5m/b5r 45/45; 45 linhas no `contrato_f52b` |
| C12 | término e escrita: `motivo_parada`, resíduo de 2 escritores | (2) | direta | `orcamento` 45/45; 1 célula com 1 linha rasgada + 1 footer-resíduo |
| T1 | kernel/otimizador do GPR (`C·RBF`, α=0, 9 restarts, `normalize_y=False`) | **T** | declarativa | declarado 45/45; evidência só indireta (C9a) |
| T2 | rampa θ do PBI = f(fe/40.000) | **T** | não-verif. | não instrumentado no log |
| T3 | parâmetros internos do MOEA/D (vizinhança T, SBX/PM, δ) | **T** | não-verif. | ⑤ sem `params`; não há eco no ⑥ |
| T4 | não-consumo de σ na seleção (contrafactual) | **T** | não-verif. | σ sequer é calculado/exportado; exige código |
| T5 | patches vendorizados inertes no mode 12 | **T** | declarativa | `sigma_dict.patches_vendorizados`; coberto por `anchors.json`+`repos.lock` |

### 2.2 Blocos narrativos

---

**U1 — A ① é o dataset inteiro, 100% `init`, `fe_index` denso.**
(a) O método canônico do piso offline não tem FE real durante a busca: "no offline, MOEA puro é impossível (não há função real para avaliar durante a busca)" (bundle §3.4). A ① existe apenas como registro do dataset precoletado. (b) A SPEC decidiu (D90/D51/DI-13.7) que o dataset offline é um **artefato** com `n = 31D−1` no tier small, 2.000 no medium, 50.000 no big, em LHS ou MVNS, e que a ① do run é a cópia integral desse artefato com `fase='init'`. (c) Query: `len(①) == maxfe == fe_final`, `value_counts(fase)`, `array_equal(fe_index, arange(N))`. Resultado: **45/45** em todas as três checagens; os 8 tamanhos observados (61, 216, 309, 371, 619, 681, 929, 2000) batem exatamente 31D−1 nas 35 células small e 2.000 nas 10 medium; `solution_id` denso 45/45; `tempo_aval_real_s = 0,0` em 45/45. (d) Mecanismo: o runner carrega o parquet do dataset, escreve-o como ① e nunca chama `problems.py` durante a busca — o único uso da função real é a ⑦, pós-hoc e fora do orçamento. (e) **(2)**, direta.

---

**U2 — Binding da ① ao artefato do dataset, bit-a-bit.**
(a) O piso consome "dado precoletado" — a proveniência é o que garante que os 5 offline compartilham a MESMA informação. (b) D63/D87/D90 fixam o artefato `data/datasets/{p}/ds_{p}_42[_{tier}_{dist}].parquet` e o gate F5.1 confere por hash. (c) Fui além do gate e comparei **valor a valor**: `Xa` e `Fa` do artefato contra `X①` e `F①` em float32. Resultado: **max\|ΔX\| = 0,0 e max\|Δf\| = 0,0 em 45/45**; o `tier`/`dist` do manifesto do artefato bate com o do run em 45/45 (small 35 / medium 10; lhs 35 / mvns 10); `doe_hash ≡ cp_init_offline.x_hash` 45/45. Consequência direta: as células `off/{p}` e `swap_small-lhs_{p}` leem **o mesmo arquivo** (`ds_{p}_42.parquet` = tier small, dist lhs) — o que habilita a prova de determinismo do C7. (d) O runner não regenera nada: lê o parquet e o repassa. (e) **(1)**, direta.

---

**U3 — ④ com uma única linha (treino único).**
(a) O offline "não retreina": o surrogate é treinado uma vez sobre o dataset e congelado. (b) O molde do b5 (`sigma_dict.④_1_linha`) define ④ = 1 linha com `n_acumulado = n_dataset`, `tempo_fit_s` = wall do treino e `tempo_busca_s` = wall do laço, porque "o motor é caixa-preta: `iterate()` roda 10 gerações sem gancho por geração". (c) Query: `len(④)`, `len(manifest.fit_series)`, `④.n_acumulado == len(①)`. Resultado: **1 linha em 45/45**, `fit_series` com 1 entrada em 45/45, `n_acumulado` correto em 45/45. Somatórios: 4.215 s de treino, 3.208 s de busca, 294 s de sonda nas 45 células. (d) Um único `fit` ⇒ uma única linha; a granularidade por geração não existe porque o DESDEO não expõe gancho por geração. (e) **(2)**, direta.

---

**U4 — Cadência da sonda: 1 bloco por modelo treinado, `geracao` NULL na ③.**
(a) §17.2.2 fixa a sonda como régua comum: no offline, S = 20.000 pontos Sobol, "1× por modelo treinado". (b) DI-13.5 sanciona `geracao` NULL na ③ (a geração é carimbada pós-hoc no buffer, e `emit_sonda_block` faz `int(geracao)`) — precedente c149/b5. (c) Query: contagem de `regime=='sonda'` na ③, evento `rec=='sonda'` no ⑥, `manifest.sonda`. Resultado: **20.000 linhas de sonda em 45/45**, **1 único evento `sonda`** em 45/45, `n_pontos=20.000` 45/45, `hash_check='ok'` 45/45, `n_blocos=1` no manifesto 45/45, `geracao` NaN em 100% das 900.000 linhas de sonda da ③ (enquanto o evento do ⑥ carimba `geracao: 1`). (d) Como há um único `fit`, há um único bloco — a régua é medida uma vez, no modelo congelado. (e) **(2)**, direta.

---

**U5 — Join posicional sonda × gabarito.**
(a) O gabarito Sobol é o mesmo para todos os configs do problema (`data/sonda/sonda_{p}.parquet`), com ordem de linhas = ordem de geração; o join é **por posição**, nunca por id (não existe `sonda_id`). (b) D87 congelou a convenção de hash (sha256 dos bytes float64 row-major) e o aninhamento Sobol (as S_online primeiras ≡ um bloco de S_online). (c) Query: `max|X_sonda(③) − X_gabarito[:20000]|`. Resultado: **0,0 exato em 45/45 células — 900.000 pontos × D dimensões, diferença nula**; `manifest.sonda.x_hash`/`f_hash` idênticos aos do manifesto do artefato em 45/45. (d) O runner carrega o gabarito, confere o hash no arranque (`hash_check`) e prediz na ordem lida — nenhuma reordenação. (e) **(1)**, direta.

---

**U6 — WAPE por objetivo no espaço cru; cobertura N/A por regra.**
(a) A régua congelada (§5 do protocolo) manda WAPE por objetivo no espaço CRU e cobertura ±1,96σ com nominal ≈0,95. (b) Aqui `espaco_modelo='cru'` e `transf_tipo/transf_params` NULL em 45/45 — **não há des-transformação a fazer** (o piso não transforma f); e a cobertura é **N/A citando a regra**, porque σ é NULL por desenho (DI-16.1), não por falta de folha coberta. (c) Recomputei WAPE e correlação independentemente sobre os 20.000 pontos de cada bloco (`sonda_recomputada.csv`) e conferi contra `sonda_f52e.csv`: **max\|ΔWAPE\| = 4,7e-7 e max\|Δcorr\| = 4,9e-7 nos 104 pares** — a régua da F5.2e é reproduzida exatamente. `cobertura95` vem **vazia em 104/104 linhas** e `n_nan`=0 — ou seja, o CSV da F5.2e tratou corretamente o σ ausente **sem inflar** (contraste com a armadilha nº 15 do c311, onde σ-NaN parcial inflava a cobertura para 1,0000). Como há 1 bloco só, **não há tendência 1º→último bloco a reportar** — o congelamento é provado por outra via (F1). (d) Mecanismo: o `SurrogateKriging` só devolve μ ao exportador do piso; a coluna σ é escrita como NaN. (e) **(2)**, direta.

---

**U7 — Invariante dupla do ④: `fit+busca ≤ tempo_geracao_s` e sonda excluída.**
(a) §17.6/DI-13.10: `tempo_geracao_s` mede o ciclo do algoritmo e **exclui** o custo da sonda (que é instrumentação nossa, não do método). (b) Nosso contrato exige que a violação apareça exatamente onde há sonda; num config de 1 linha, a checagem vira uma **igualdade**. (c) Query: `tempo_fit_s + tempo_busca_s` vs `tempo_geracao_s`. Resultado: **max\|Δ\| = 1,5e-5 s em 45/45** (ex.: BBOB_F1 34,499901 vs 34,499901), com `tempo_pred_sonda_s > 0` em 45/45 (mediana 2,38 s) e `tempo_total_s` do ⑤ ≥ soma das três parcelas em 45/45. (d) O runner cronometra o bloco de sonda separadamente e o subtrai antes de gravar `tempo_geracao_s` — o resíduo de 1,5e-5 s é arredondamento float32 do parquet. (e) **(2)**, direta.

---

**U8 — `fe_treino_max` constante em N−1.**
(a) O campo declara qual o maior índice de FE que o modelo "viu" ao predizer aquela linha. (b) No offline, "o modelo vê o dataset inteiro 1×" ⇒ `fe_treino_max = n_dataset − 1` em **toda** linha (busca e sonda) — desenho D-08. (c) Query: `③.fe_treino_max.unique()`. Resultado: **um único valor por célula em 45/45**, igual a `len(①)−1` em 45/45 (60, 215, 308, 370, 618, 680, 928, 1999). Não há a não-monotonicidade que aparece em b1/b4/c217 (DI-13.15) — aqui é constante por construção. (e) **(2)**, direta.

---

**U9 — Guards e cache reconciliados.**
(a) O baseline de guards é o "ruído esperado" do config. (b) O piso não tem cache de avaliação (FE real = 0) nem guarda de fallback ativada. (c) Query: `rec=='guard'` no ⑥, `manifest.cache_hits`, `footer.cache_hits`, `fallback_ativado`, `n_retries`, `stack_trace`. Resultado: **0 eventos `guard` nas 45 células**; `cache_hits = 0` no ⑤ **e** no footer em 45/45; `fallback_ativado = False` 45/45; `n_retries = 0` 45/45; `stack_trace = null` 45/45. Baseline de guards deste config = **zero**, e ele é respeitado. (e) **(1)**, direta.

---

**U10 — Aritmética entre camadas fecha exata.**
(a)(b) O off-by-one deste config é o overshoot de ≤1 geração (C3); fora isso, todas as contagens são determinadas por (N, n_ger). (c) Queries: `len(③ offline) == N × n_ger`; `#decision == n_geracoes`; `set(geracao) == {1..n_ger}`; `#header/#sonda/#footer`. Resultado: **45/45** em todas: ③ offline = 40.050 (M=2) ou 40.005 (M=3); **30.165 decisões = Σ n_geracoes = 30.165**; contador denso sem furos em 45/45 (até 801); 1 `header` + 1 `sonda` + 2 `footer` (runner + despachante) em 44/45 — a 45ª tem 3 footers, resíduo de escrita explicado em C12. `fe` constante = `len(①)` nos 30.165 eventos; `len(f_best) == M` nos 30.165. (e) **(1)**, direta.

---

**U11 — Erro de fantasia: o substituto do `real_solution_id`.**
(a) A checagem universal U11 mede o erro do modelo nos infills escolhidos, via `real_solution_id → ①`. (b) Aqui **não existe infill** e `real_solution_id` é NULL por desenho (DI-16.17: a população inicial é LHS novo + SBX/PM contínuos, nenhum indivíduo coincide com o dataset). O substituto legítimo é o par **(μ da ③ na última geração, f real da ⑦)**, ligado pelo link posicional `origem_linha` — exatamente o mesmo par, medido no ponto que importa. (c) Query (`fantasia_final.csv`, `fantasia_comparada.csv`): para cada par célula×objetivo, fração de indivíduos com μ < f_real, viés mediano e WAPE da população final. Resultado: **em 69/104 pares (66,3%) o modelo é otimista em 100% dos indivíduos**; a mediana da fração otimista é **1,000**; o viés mediano é **negativo em 91/104**; o WAPE da população final tem mediana **0,985**. Casos exemplares: `BBOB_F17` obj0 μ mediano −8,90e6 contra f real +1,95e6 (viés −1,09e7); `swap_medium-mvns_DTLZ2` obj1 μ −0,584 contra f real 1,85e-24; `DTLZ3` obj2 μ −339,4 contra f real 7,5e-16. (d) Mecanismo: a decomposição PBI compara escalarizações da **média**; a média do GP fora do suporte tende à média a priori (0) ou a extrapolações negativas, e o motor gasta 40.000 avaliações caminhando na direção que o modelo diz ser melhor — o gradiente da fantasia. É o comportamento **esperado** da ablação, medido. (e) **(2)**, direta.

---

**U12 — ⑦ recomputada, ligada e sem cap.**
(a) DI-13.9/DI-08: avaliar **todos** os finais na função verdadeira e filtrar o não-dominado **depois**; a ⑦ tem de ser reconstituível da ③. D68: ND final sem cap. (b) A ⑦ é escrita/checada por `scripts/final_eval.py` a partir da população que a ③ **registrou** (não da seguinte). (c) Queries: (i) recomputo da máscara ND sobre `f*` da ⑦ vs coluna `nd_pos_real`; (ii) `③[geracao == n_ger].loc[origem_linha, x*]` vs `⑦.x*`; (iii) `n⑦` vs pop da última geração; (iv) footer. Resultado: **recomputo exato em 45/45**; **link posicional bit-a-bit, max\|ΔX\| = 0,0 em 45/45** (3.020 linhas); `origem_linha` denso `arange(n⑦)` 45/45; `origem_geracao` = última geração em 45/45; `origem_solution_id` NULL 45/45; **`n⑦` = N do lattice em 45/45** (50 ou 105 — nenhum cap, nenhum encolhimento, ao contrário do RVEA do c311 que chegou a pop final = 1); `footer.n_final` e `footer.n_nd_pos_real` batem com a ⑦ em 45/45. Razão de fantasia `nd_pos_real/n_final`: mediana **0,360** (off 0,340 · sweep 0,381), mínimo 0,020 (MMF1 e WFG9: 1 de 50) e máximo 1,000 (BBOB_F17, `swap_medium-lhs_DTLZ2`, `swap_medium-mvns_WFG9`, `swap_medium-mvns_ZDT4`). (e) **(2)**, direta.

---

**F1 — O congelamento do modelo, provado sem os "2 blocos bit-idênticos".**
(a) O módulo de família (Etapa 3, offline/treed) usa **2 blocos de sonda bit-idênticos** como prova do congelamento — é o teste do c311/b5r/b5m. (b) Aqui o teste **não se aplica**: `sigma_dict.sonda_offline` declara **1 bloco** porque há um único treino (não há fase de construção seguida de fase final). A prova equivalente tem de vir de três invariantes independentes. (c) Evidência: (i) ④ com **1 linha** e `fit_series` com **1 entrada** em 45/45; (ii) `fe_treino_max` **constante** em toda a ③ — busca e sonda — em 45/45; (iii) `tempo_fit_surrogate_s` do ⑤ ≡ `tempo_fit_s` do ④ em 45/45. Nenhuma linha da ③ é predita por um modelo diferente do único treinado. (d) Mecanismo: `SurrogateKriging.fit` é chamado uma vez, antes do laço; o objeto é passado por referência ao `MOEA_D` e ao emissor da sonda. (e) **(2)**, direta.

---

**F2 — σ 100% NULL: a ablação materializada no dado.**
(a) No módulo de família, σ-NaN é **informação** (no c311 mede cobertura de folhas). (b) Aqui a semântica é outra e está congelada em DI-16.1: *"NULL POR CONSTRUÇÃO — o piso é 'o b5 sem σ'; a incerteza do GPR NÃO é reportada (nem na busca nem na sonda)"*. Não é bug, é a variável que a ablação remove. (c) Query: `③[sigma_*].isna().all(axis=1).mean()` e `③[mu_*].isna().any(axis=1).mean()`. Resultado: **σ NaN em 2.701.620/2.701.620 linhas (100,000%) nas 45 células**, e **μ preenchido em 100%** — exatamente o padrão que a nota do config prevê ("μ preenchido, σ NULL por desenho"). Também: `pred_tipo='valor'` uniforme e `pred_classe`/`pred_score`/`pred_confianca` NULL em 100% (o piso não é classificador). (d) O exportador do piso simplesmente não pede `predict(return_std=True)`. (e) **(2)**, direta.

---

**F3 — ② vazia, `real_solution_id` NULL, `n_ds_membros`=0.**
(a)(b) DI-16.17: a população inicial do motor é LHS **novo** (`create_new_individuals`/`LHSDesign`) com SBX/PM contínuos ⇒ nenhum indivíduo da busca coincide com uma linha do dataset; logo a ② (mapa população→`solution_id`) é vazia por construção e o gate não a exige. (c) Query: `len(②)`, `③.real_solution_id.isna().mean()`, `all(decision.n_ds_membros == 0)`. Resultado: **0 linhas na ② em 45/45**; `real_solution_id` NULL em **100%** das 2,7 M linhas; `n_ds_membros == 0` nos **30.165** eventos de decisão. (d) A prova empírica do desenho: se algum indivíduo coincidisse bit-a-bit com o dataset, `n_ds_membros` seria >0 em pelo menos uma geração — nunca ocorreu em 30.165 gerações. (e) **(2)**, direta.

---

**C1 — Motor MOEA/D mode 12 com decomposição PBI.**
(a) O método canônico do piso (bundle §3.4) é "MOEA/D otimizando sobre um surrogate treinado uma vez no dataset, usando só a média", escolhido porque é "a ablação exata do b5 — Prob-MOEA/D menos a seleção probabilística". (b) A implementação usa a classe `MOEA_D` do `desdeo_emo` vendorizado em **mode 12** com `MOEAD_select` (PBI), e o bundle declara os patches do b5 (`b5-mode72-kde`, `b5-mode7-archive`) **inertes** neste caminho. (c) Evidência declarativa uniforme: `modelo_flag = 'moead_media/MOEAD-PBI+GPR-media'` em 100% das 2,7 M linhas da ③; `caminho='moead_media_gen'` e `motivo='selecao no surrogate (MOEA/D mode 12, PBI; so a media)'` nos **30.165** eventos; `algo_version='piso-off-moead_media-1.0'` 45/45; `env = env_b5` 45/45. Corroboração **indireta forte**: o número de gerações coincide com o do b5m (mode 72, mesmo motor) em **45/45** (C5), o que só ocorre se o laço e o tamanho de população forem os mesmos. (e) **(1)**, **direta-declarativa** (elo com o código coberto por `anchors.json`+`repos.lock`).

---

**C2 — Lattice 50/105 herdado do b5m, não N=100.**
(a) O piso deve rodar "o MESMO motor do b5, sem override de lattice". (b) DI-16.4/D65 v5.2.1 **superou** a antiga listagem "N interno = 100" (resíduo dos pisos ONLINE): forçar N=100 mediria **duas** variáveis (uso de σ **e** estrutura da busca), destruindo o isolamento. `lattice_resolution=None` ⇒ Das-Dennis default: 50 vetores em M=2, 105 em M=3. (c) Query: moda e unicidade das linhas por geração na ③. Resultado: **50 em 31/31 células M=2 e 105 em 14/14 células M=3**; a população é **constante em todas as gerações** de 45/45 (`nunique()==1`) — nunca encolhe nem cresce. Corroboração cruzada: `n⑦` = 50/105 em 45/45. (d) O `BaseDecompositionEA` gera o lattice na construção e o MOEA/D substitui in-place por vetor de peso — o tamanho não pode variar. (e) **(2)**, direta.

---

**C3 — Orçamento interno de 40.000 avaliações-surrogate e o overshoot documentado.**
(a) Bundle §11: piso ancorado no b5 — **40.000 avaliações-surrogate**, "porque piso-MOEA/D vs Prob-MOEA/D com o **mesmo orçamento interno** é a ablação cirúrgica". (b) `sigma_dict.overshoot` sanciona: "terminação por FE (≥40000): a última geração que cruza o teto completa o laço interno de N vetores ⇒ overshoot ≤ 1 geração". `sigma_dict.rampa_theta` acrescenta que 40.000 é obrigatório mesmo com FE real = 0, porque a rampa θ do PBI é função de `fe/total_function_evaluations`. (c) Query: `len(③ offline)` e `n_geracoes` contra a fórmula. Resultado: **40.050 avaliações em 31 células M=2 (801 gerações × 50) e 40.005 em 14 células M=3 (381 × 105)**; ou seja `n_ger = ⌊40000/N⌋ + 1` em **45/45**, e o overshoot é de exatamente **50 avaliações (1 geração) em M=2 e 5 avaliações (0,05 geração) em M=3** — dentro do teto declarado em 45/45. `motivo_parada='orcamento'` em 45/45. (d) O laço testa `fe > 40000` **depois** de completar a geração; com N=50 a igualdade em 40.000 ainda passa no teste e dispara uma última geração — daí o padrão 801/381 ser exato e reprodutível. (e) **(2)**, direta.

---

**C4 — O Kriging: mesma especificação do b5, treino INDEPENDENTE — medido.**
(a) Bundle §10: "o piso treina um GP (Kriging) no dataset e otimiza sobre a média — mesma família dos 3 viáveis. Isola *uma* variável (usar σ vs só a média); RBF/NN introduziria uma segunda diferença". (b) DI-28 é explícito e cauteloso: *"mesma ESPECIFICAÇÃO, treino INDEPENDENTE — nunca 'idêntico'… alg_id 21 vs 18 semeia RNGs distintos; os 9 restarts do GPR podem convergir a μ não idêntico"*. DI-30.B2 ratifica `modelo_hp` NULL ("gravar HP no piso e não no b5m criaria assimetria espúria na ablação"), e o espaço é **cru** (o piso não transforma). (c) Medi a distância entre os μ do piso e os do b5m/b5r nos **mesmos 20.000 pontos Sobol**, célula a célula, objetivo a objetivo (`mu_identidade_piso_vs_b5.csv`): **65/104 pares (62,5%) concordam a ≤1e-5 relativo** — mediana da diferença relativa máxima **1,15e-7**, isto é **1 ULP de float32**: são o *mesmo* GP; **39/104 (37,5%) divergem materialmente**, e destes 21 envolvem o colapso de um dos lados (C9). Confirmações estruturais: `espaco_modelo='cru'` e `transf_tipo/params` NULL em 100% das linhas; `modelo_hp` NULL 45/45; o `sigma_dict.modelo` do piso e o do b5m/b5r declaram **string de kernel idêntica**; e `tempo_fit_surrogate_s` tem razão mediana b5m/piso = **0,97** (o objeto computacional treinado é o mesmo). (d) O `fit` é determinístico dado o estado do RNG global; como as duas configs consomem o stream em pontos diferentes, os 9 restarts partem de inicializações diferentes e a maximização da log-verossimilhança marginal ora cai no mesmo ótimo (62,5%), ora não. É **exatamente** o envelope que DI-28 declarou — agora quantificado. (e) **(2)**, direta.

---

**C5 — A ablação é cirúrgica: prova estrutural + decomposição do custo.**
(a) DEF-E3/D77: "o contraste piso-vs-b5 mede exatamente o valor de usar σ". Para isso, tudo exceto a seleção tem de ser igual. (b) Nenhuma decisão relaxou isso; o piso herda motor, lattice, orçamento e especificação de surrogate do b5m. (c) A prova mais forte que os dados permitem: **`n_geracoes`(piso) ≡ `n_geracoes`(b5m) em 45/45 células** (801/801 nas 31 M=2, 381/381 nas 14 M=3) e `fe_final` idêntico em 45/45 — mesmo motor, mesmo lattice, mesmo teto, mesmo critério de parada. Contraste de controle: b5r (RVEA, mode 7) diverge em **45/45** (454 a 5.548 gerações) e tem população **variável** em 45/45, provando que a coincidência com o b5m não é trivialidade do harness. Somam-se: dataset bit-a-bit idêntico (U2), 20.000 pontos de sonda idênticos (U5), μ idêntico a 1 ULP em 62,5% dos pares (C4). **Decomposição do custo** (`tempo_f52d.csv` + manifestos): `tempo_fit_surrogate_s` razão mediana b5m/piso = **0,97**; `tempo_pred_sonda_s` 2,45 s vs 2,38 s; **`tempo_busca_s` razão mediana 62,5× (faixa 14,1–105,3×)**; wall total das 45 células **2,18 h (piso) contra 37,42 h (b5m)** = 17,2×, mediana por célula **67,2 s contra 2.981,9 s = 44,4×**. (d) Todo o custo extra do b5m está na **busca** — a comparação MC pareada (`compute_probability_wrong_MC`, S=1000 amostras/indivíduo) — e nada no surrogate. Isto é a atribuição limpa do preço de σ. (e) **(1)**, direta.

---

**C6 — Duas instâncias por tier: este config é small/medium; o big é `treed_media`.**
(a)(b) P5/DI-16.5 registra que a rota original era **impossível**: o GP padrão não treina em ~50k (parede O(n³)) e `b5` × `c311` **não podem ser co-importados** (N.1.2/D79 — mesmo nome de pacote, código diferente ⇒ usa as classes erradas **sem erro**). A solução: piso small/medium em `env_b5` (MOEA/D mode 12 + Kriging-média) e piso big em `env_c311` (treed-GP-média), sob o nome `treed_media`. (c) Query: labels existentes e `env.executable`. Resultado: **0 células `swap_big-*` sob `moead_media`** e `env_b5` em 45/45; as 9 células big do piso vivem sob `treed_media` (e já foram usadas na ablação big do adendo F5.5, §B). (d) Um env por processo ⇒ zero colisão de vendor. (e) **(2)**, direta. *(Consequência de leitura: qualquer contagem "45 células do piso offline" é **incompleta** — o piso tem 54 células somando `treed_media`.)*

---

**C7 — Determinismo do RNG PROVADO por um re-run acidental.**
(a)(b) D62 (`SeedSequence((base, alg_id, iter, uso_id))`) e DI-28.3 (o runner injeta o `RandomState` global semeado no `lhs` do `create_new_individuals`, porque o pyDOE 0.9.1 usa `default_rng()` fresco e tornaria a população inicial **não reprodutível**) sustentam a reprodutibilidade. Nos pilotos isso ficou no balde **T** ("só re-run bit-idêntico verifica"). (c) **A campanha contém o re-run**: `off/{p}` e `swap_small-lhs_{p}` consomem o MESMO artefato (`ds_{p}_42.parquet`, tier small/dist lhs — provado em U2) em **dois processos independentes, com horas de diferença** (ex.: ZDT1 — sweep encerrado 11:26:29, off encerrado 11:45:21). Comparei camada a camada nos 5 problemas com par (`determinismo_rerun.csv`): **① max\|Δ\| = 0,0 · ③ max\|Δ\| = 0,0 · ⑦ max\|Δ\| = 0,0 nos 5/5**, `n_geracoes` igual 5/5, `sigma_dict` igual 5/5. Cross-check independente pelo pipeline de métricas: o IGD+ da ⑦ bate na 5ª casa em 5/5 (DTLZ2 0,89040 · MMF16_20 0,30084 · WFG9 0,52707 · ZDT1 0,19782 · ZDT4 210,62735). Só a ④ difere — e só no relógio (Δ de 2,2 a 14,5 s de wall). (d) O determinismo cobre o LHS inicial, os 9 restarts do GPR, os operadores SBX/PM e a ordem de escrita; e prova que o rótulo do experimento **não entra** na semente. (e) **(1)**, **direta** — este aspecto **sai do teto T** (o análogo do que aconteceu com o early-stop do c311).

---

**C8 — Dinâmica da população: turnover e congelamento.**
(a) O prior do config diz "turnover ~8,5%/ger (conservador — vs 98% do b5m)". (b) Não há decisão em jogo: é comportamento, e é a assinatura do mecanismo. (c) Medi o turnover **posicional** (fração dos N slots do lattice cujo x mudou entre gerações consecutivas) nas **30.120 transições** das 45 células (`turnover_por_geracao.csv.gz`, `turnover_por_config.csv`): primeira transição **95,6%** (mediana 99,1%); depois decai monotonicamente por faixa de progresso — 0–10%: **57,6%** · 10–25%: 27,6% · 25–50%: 16,2% · 50–75%: 12,0% · **75–100%: 10,0%** (mediana 6%); média global **19,4%**, mediana 12,0%; **7.113/30.120 transições (23,6%) totalmente congeladas**, chegando a 761/800 gerações congeladas em `swap_medium-lhs_ZDT4` e 741/800 em `BBOB_F17`. O teto por célula nunca passa de **39,5%**. Comparação pareada com o b5m (mesmo motor, mesmo lattice, mesmas gerações): média **34,3% vs 19,4%**, último quarto **27,5% vs 9,3% (2,9×)**, congeladas **2.058 vs 7.113 (3,5× mais congelamento sem σ)**, máximo por célula **99,9% vs 39,5%**; b5m supera o piso em 27/45 células e chega a 99,3–99,9% em 4 delas. (d) **Reconciliação dos priors**: os "~8,5%" descrevem o **regime estacionário** do piso (medi 9,3% no último quarto) e os "~98%" descrevem o b5m onde a comparação MC permanece ambígua (`P_wrong≈0,5` ⇒ aceita sempre) — ambos confirmados, em pontos diferentes da curva. O mecanismo: a comparação determinística de escalarizações PBI da média produz um ponto fixo e trava; a comparação probabilística nunca trava enquanto houver incerteza. **Inversão instrutiva**: em DTLZ1/DTLZ3 é o **b5m** que congela (370 e 380 gerações, turnover 0,026 e 0,000) — exatamente as células onde o **GP do b5m** colapsou (C9), fechando o argumento causal pelos dois lados. (e) **(1)**, direta.

---

**C9a — Colapso do GPR para a média a priori (μ ≡ 0).**
(a) O método canônico pressupõe um Kriging informativo. (b) A especificação implementada — sancionada como "MESMA ESPECIFICAÇÃO do b5", bússola D29 🟠 (impl→código do vendor) — tem `normalize_y=False` **hard-coded**, `alpha=0` e um kernel `C(1,(1e-3,1e3))·RBF(10,(1e-2,1e2))` **isotrópico** com bounds fechados. Com média a priori zero e comprimento de escala no limite inferior, o posterior vira um interpolador-delta: μ ≈ 0 em qualquer ponto fora da vizinhança imediata dos dados. (c) Critério operacional: WAPE = 1,000 ± 1e-4 **e** \|corr\| ≤ 0,015 (o WAPE é exatamente 1 quando μ≡0, pois Σ\|0−f\|/Σ\|f\| = 1). Resultado nos 104 pares: **28 pares colapsados (26,9%) em 14/45 células** — `BBOB_F17`(1 obj), `DTLZ1`(2), `DTLZ2`(3), `DTLZ3`(2), `DTLZ4`(2), `ZDT6`(1), `swap_{small,medium}-{lhs,mvns}_DTLZ2`(2–3 cada), `swap_medium-{lhs,mvns}_MMF16_20`(3 cada), `swap_medium-{lhs,mvns}_ZDT4`(1 cada). Em 17 deles μ é **exatamente 0,0 nos 20.000 pontos**; nos outros 11 o máximo de μ fica ≤1,5e-3 da escala de f (resíduo de vizinhança de treino). Correlação nesses pares: −0,006 a +0,015 — informação nula. **O fenômeno não é do piso**: pelo mesmo critério, `b5m` colapsa em **9/104** e `b5r` em **5/104** (`sonda_f52e.csv`), inclusive em células onde o piso **não** colapsa (DTLZ1 obj1, DTLZ3 obj1/obj2, DTLZ4 obj1) — é bidirecional e é uma propriedade da especificação compartilhada. (d) Mecanismo causal completo: sem normalização de y, a verossimilhança marginal de um alvo com escala grande (DTLZ3 chega a 1.750) ou muito concentrada tem um ótimo local degenerado onde o termo de sinal encolhe e o comprimento de escala vai ao piso; a partir daí o posterior devolve a média a priori. (e) **(2)** — desvio da imagem ideal do método, **sancionado** pela cadeia bundle→`sigma_dict`→D29 🟠; verificabilidade **direta** para o efeito, indireta para a causa (os HP não são gravados, DI-30.B2 → ver T1).

---

**C9b — 🎯 A ASSIMETRIA da taxa de colapso entre configs de mesma especificação.**
(a)(b) DI-28 sanciona que "os 9 restarts do GPR podem convergir a μ **não idêntico**" — sanciona **diferença**, não **taxa de degeneração diferente**. Nenhuma decisão do REGISTRO prevê ou explica que o piso degenere sistematicamente mais que o seu par de ablação sobre **o mesmo dataset, com a mesma classe, o mesmo kernel e o mesmo número de restarts**. (c) Medida: **piso 28/104 (26,9%) · b5m 9/104 (8,7%) · b5r 5/104 (4,8%)** — mesmo critério, mesmas 45 células, mesmos 20.000 pontos. Sob uma taxa comum (p̂ = 42/312 = 13,5%), o esperado seria 14 em cada; χ² = 21,6 (gl 2) ⇒ **p < 1e-4**. Efeito prático: em **14/45 células (31,1%)** o contraste piso×b5m **não** é "σ vs μ" — é "GP degenerado vs GP bom" (ou o inverso). Exemplo cirúrgico: em `off/DTLZ2`, os **três** objetivos do piso colapsam (WAPE 1,000/1,000/1,000) enquanto os do b5m estão sadios (0,0915/0,0994/0,0505); o IGD+ da ⑦ nessa célula é 0,8904 (piso) contra 0,0569 (b5m) — 15,6×, e a atribuição a σ é **inválida** ali. (d) Hipótese causal (não confirmável só com dados): a semente efetiva dos restarts vem do `RandomState` global, cujo **estado no instante do `fit`** depende de tudo que o processo consumiu antes; a ordem de construção do `ProbMOEAD` e do `MOEA_D` difere, logo os 9 pontos de partida diferem — mas isso explicaria diferença, não *viés* de 3×. Alternativa concorrente: 1 semente só, azar amostral. (e) **(3) 🎯**, direta → **F5.4** (confirmar em código o ponto exato de consumo do RNG antes do `SurrogateKriging.fit` nos dois configs, e se o piso passa y ao GPR em ordem/escala diferente) e **M8/M9** (re-medir a taxa em 30 sementes: com 1 semente não se separa "mecanismo" de "semente infeliz" — caveat 8 do F5).

---

**C10 — Extrapolação para fora do suporte: para onde a busca μ-only vai.**
(a) O piso, por desenho, "não faz a coisa inteligente": otimiza a média sem penalizar incerteza. A previsão teórica é que ele termine fora do suporte do dataset. (b) Nenhuma decisão altera isso — é a variável medida. (c) Query (`extrapolacao_fbest.csv`): comparei o `f_best` da última geração (melhor μ por objetivo, gravado no ⑥) com o **mínimo real do dataset** na ①. Resultado: **95/104 pares (91,3%) terminam com o melhor μ ABAIXO do mínimo que o dataset comporta**; **38/104 (36,5%) terminam com μ negativo em objetivos que são não-negativos no dataset inteiro**; e 48/104 já extrapolavam na geração 1. Casos exemplares: `BBOB_F17` obj0 — μ vai de −4,66e5 (ger 1) a **−8,90e6** (ger 801) enquanto o mínimo do dataset é +3,26e5 e o f real do melhor final é +1,95e6 (fantasia de ~1,1e7 unidades); `DTLZ1` obj0/obj2 — μ ≈ 5,1e-281 e 1,3e-280 (a média a priori) contra mínimos de 0,0757 e 0,4979 e f reais de 24,4 e 267,9; `swap_small-mvns_MMF16_20` obj0 — μ = −1,4337 contra mínimo 2,8e-17. (d) Mecanismo: a escalarização PBI recompensa o menor μ; o GP fora do suporte devolve valores negativos (ou zero) que **dominam** qualquer ponto real; o motor gasta 40.000 avaliações caminhando para lá e a ⑦ paga a conta. É **a razão de ser da ablação**: mede-se o que σ compraria. (e) **(1)** — comportamento conforme o mecanismo prescrito, direta.

---

**C11 — O ⑥ segue a linha do b5 (DI-30.B3); o ⑤ não tem `params` (item 6 da torre).**
(a)(b) DI-30.B3 decidiu que o `.jsonl` do piso segue a linha **'b5'** do contrato, **não** a linha 'pisos' — porque o piso é um b5 sem σ, e a simetria do log é o que permite ler as duas colunas lado a lado. (c) Prova por identidade de esquema: o conjunto de chaves do evento `decision` do piso é `{caminho, f_best, fe, geracao, motivo, n_ds_membros, n_front1, rec, tempo_fit_s, ts}` — **exatamente** o do b5m e o do b5r (só o valor de `caminho` muda: `moead_media_gen` vs `b5_gen`), em 45/45 células. Contraste: o `e103` (outro offline) tem esquema completamente distinto (`e103_setup`, `e103_gen`, `e103_busca`, `f_best_dataset`). O `header` traz `sigma_dict` completo (20 chaves) em 45/45. **Não-conformidade herdada**: o ⑤ **não tem a chave `params`** em 45/45 (as 45 linhas de `moead_media` no `contrato_f52b.csv`) — o CONTRATO §5 a lista como obrigatória; é o **item 6 para a torre**, compartilhado com 7 configs. Fallback verificado: `claude_code_context/artifacts/params.json → por_config.moead_media = {"impl": "DESDEO mode 12 (D77)", "N": "lattice default (50 M=2 / 105 M=3 — NÃO forçar 100)", "surrogate": "GP-média (tier big: treed-GP-média)"}`, mais as 20 chaves do `sigma_dict` — **nenhum parâmetro do mecanismo se perdeu**, só a sua localização canônica. (e) **(2)**, direta (não-conformidade **explicada e já triada**, não desvio inexplicado).

---

**C12 — Término e integridade de escrita: `motivo_parada`, e o resíduo de dois escritores.**
(a)(b) Etapa 1.2 do protocolo: o mapa de término varia por config e **nunca** se usa `status` sozinho (bug B1). Para esta família o campo é `motivo_parada` no manifesto. (c) Resultado: **`motivo_parada='orcamento'` em 45/45**, `status='ok'` 45/45, `footer.status='ok'` 45/45, `footer.cp_init=true` 45/45. Integridade: `integridade_f52a.csv` traz **1 linha** para o config — `swap_small-lhs_ZDT1`, `JSONL_1LINHA_RASGADA (linhas=807 ruins=1 footer=True)`. Disseguei a célula: a linha 805 (1-based) é a **cauda** de um registro mais longo, contendo texto de operador (`"…Mac o caminho é local; não chame gcs.upload/sync aqui). Pins são decisão do autor (D80): NÃO instalar aqui.')"}`), e a linha 806 é um `footer` **completo e válido** com `status='failed', motivo='erro_RuntimeError'` e **timestamp 11:24:15**, ou seja **anterior** ao footer `ok` (11:26:29) do run bom, cujo header é de 11:24:10. Diagnóstico: **dois escritores na mesma célula** — uma tentativa que morreu em 5 s (RuntimeError com o texto do operador dentro do `stack_trace`) e o run bom, mais **curto**, que reescreveu o arquivo por cima sem truncar, deixando a cauda antiga; o despachante então **anexou** o seu footer (daí `j_footer=3` só nesta célula). (d) **Dano analítico: zero, e isso está provado** — as camadas ①/③/⑦ desta célula são **bit-idênticas** às de `off/ZDT1` (C7), o filme científico está completo (header + sonda + **801 decisões densas** + footer ok) e todas as 40+ invariantes estruturais passam nela. É a mesma assinatura do item **(8)** da torre (writer concorrente no ⑥, caso b1/WFG1) e do item **(7)** (cauda órfã por reescrita mais curta, caso e103×4) — aqui sem consequência. **Armadilha registrada**: quem triar término por "existe footer com status failed" **reprova esta célula por engano**; a regra correta é `motivo_parada` do ⑤. (e) **(2)**, direta.

---

**T1–T5 — o que os dados não alcançam.**
**T1** — kernel e otimizador do GPR (`C(1,(1e-3,1e3))·RBF(10,(1e-2,1e2))`, `alpha=0`, `n_restarts_optimizer=9`, `normalize_y=False`): declarados no `sigma_dict` em 45/45, mas os HP ajustados **não são gravados** (`modelo_hp` NULL por DI-30.B2, ratificada para não criar assimetria com o b5m); a única evidência empírica é indireta (o padrão de colapso do C9a é a assinatura do comprimento de escala no bound inferior). Elo com o código coberto por `anchors.json`+`repos.lock`. **T2** — a rampa θ do PBI como função de `fe/40000` não aparece em nenhuma camada. **T3** — os parâmetros internos do MOEA/D (tamanho de vizinhança T, probabilidade de seleção local, SBX/PM) não têm eco: o ⑤ não tem `params` (C11) e o ⑥ não os declara. **T4** — o **não-consumo** de σ na seleção é contrafactual: σ nem sequer é calculado, então "não foi usado" só se prova lendo o código. **T5** — a inércia dos patches `b5-mode72-kde` e `b5-mode7-archive` no mode 12 é declarativa.

---

## 3. Percentuais por classe

**Denominador = 33 aspectos − 5 T = 28** (T listado à parte, com a razão, em §9).

| classe | contagem | % |
|---|---|---|
| **(1)** conforme o método canônico (bundle/D77) | **9/28** | **32,1%** |
| **(2)** desvio sancionado (decisão citada no bloco) | **18/28** | **64,3%** |
| **(3)** desvio inexplicado 🎯 | **1/28** | **3,6%** |
| **T** teto declarado (fora do denominador) | 5 | T1 kernel/HP · T2 rampa θ · T3 params do MOEA/D · T4 contrafactual de σ · T5 patches inertes |

Aspectos (1): U2, U5, U9, U10, C1*, C5, C7, C8, C10 — *C1 é **direta-declarativa** (Botão 3), marcado na tabela.
Aspecto (3): **C9b** (assimetria da taxa de colapso do GPR).

---

## 4. PAPEL DE CONTROLE (a Entrega 2 é **N/A** — config sem artigo)

Não há artigo: o piso é uma construção nossa (D77) e o gabarito é a especificação canônica do bundle + o REGISTRO. Logo **não há interseção, âncora direcional ou faixa-guia J a computar** — a comparação canônica é substituída pela única pergunta que importa: **o piso funciona como régua?**

**(i) A régua é cirúrgica — provado estruturalmente.** Mesmo motor e mesmo laço (`n_geracoes` ≡ b5m em **45/45**, e ≠ b5r em 45/45), mesmo lattice (50/105, pop constante 45/45), mesmo orçamento (40.000 ± 1 geração, 45/45), mesmo dataset (bit-a-bit, 45/45), mesmos 20.000 pontos de régua (ΔX = 0), mesma especificação de surrogate (μ a 1 ULP em 62,5% dos pares; `t_fit` razão 0,97). **A única diferença executável é a seleção.**

**(ii) A régua discrimina — no endpoint certo.** A métrica oficial da F5.2c é **100% indiscriminante** no offline: verifiquei igualdade **exata** de IGD+ entre `moead_media`, `b5m`, `b5r`, `e103` (e `c311` onde existe) em **45/45 células** — diferença relativa máxima **0,000e+00** (D69 lê o f da ①, que é o mesmo dataset). O endpoint é a ⑦. Nela:

| corte | piso vence b5m | razão IGD+⑦ piso/b5m (mediana) | fora do piso de ruído 58,98% |
|---|---|---|---|
| 25 células `off` | 9/25 | **1,535** | 15/25 |
| 19 células `off` **limpas** (sem colapso de nenhum lado) | 8/19 | **1,351** | 11/19 |
| 20 células `sweep` | 9/20 | **1,344** | 15/20 |
| **45 células** | **18/45** | ~1,4 | 30/45 |

Ou seja: **remover σ custa ~35–54% de IGD+ na mediana** e o piso perde em 27/45 células — mas ganha em 18, com margens grandes onde a incerteza atrapalha o b5m (ZDT6 0,108 vs 6,637 = 62× melhor; ZDT1 0,198 vs 1,136; ZDT3 0,847 vs 1,296; DTLZ7 0,368 vs 0,938). No ranking dos 5 offline pela ⑦ (F5.5 §3) o piso é o **melhor em apenas 1/25** problemas — comportamento de piso.

**(iii) A régua é barata e o preço de σ está atribuído.** 2,18 h contra 37,42 h nas mesmas 45 células (mediana por célula 67 s × 2.982 s = **44,4×**), e **todo** o delta está na busca (`t_busca` 62,5×), nada no surrogate (0,97×). Este é o par custo×benefício que o D97 pede: **σ custa ~62× de busca e compra ~35% de IGD+ na mediana, vencendo em 60% das células**.

**(iv) A régua não é degenerada.** Entrega ND não-vazio em 45/45 (mediana 18 pontos, fantasia mediana 0,360), sonda com WAPE mediana **0,127** e correlação mediana **0,934** nos 76 pares não-colapsados (43/76 com corr > 0,9). Não é "um algoritmo quebrado" — é um otimizador competente sobre um modelo que ele não sabe onde não confiar.

**(v) O caveat que o autor precisa carregar.** Em **14/45 células (31,1%)** o GP de um dos lados colapsou (C9a/C9b) e o contraste ali **não** mede σ. As leituras de ablação da F5.5 devem ser reportadas **duas vezes**: nas 45 e nas 31 limpas (nas 19 `off` limpas a penalidade de remover σ cai de 53,5% para 35,1%).

**Veredito: SIM — o piso cumpre a função de régua**, com a ressalva (v).

---

## 5. Veredito de contrato

`contrato_f52b.csv` e `integridade_f52a.csv` filtrados a `moead_media`: **45 linhas de contrato + 1 de integridade**, ambas já mapeadas. Interpretação regra × defeito:

| achado | ocorrências | veredito |
|---|---|---|
| ⑤ **sem a chave `params`** | 45/45 | **Por-desenho-do-writer, não do mecanismo — mas é não-conformidade real do CONTRATO §5.** Já registrada como **item 6 para a torre** (7 configs, 197 células). Fallback **verificado sem perda**: `artifacts/params.json → por_config.moead_media` (mode 12, lattice 50/105, GP-média) + as 20 chaves do `sigma_dict` no ⑤ **e** no header do ⑥. Nenhum parâmetro do mecanismo é irrecuperável. |
| ⑥ com **1 linha rasgada + 1 footer-resíduo** (`swap_small-lhs_ZDT1`) | 1/45 | **Por-ambiente (dois escritores), não defeito do run.** Prova em §C12: o footer `failed` é de 11:24:15 e o run bom fecha 11:26:29 com 801 decisões densas; e as camadas ①/③/⑦ são **bit-idênticas** às de `off/ZDT1`. Mesma assinatura dos itens **(7)** e **(8)** da torre. Zero perda analítica. |
| ② vazia (45/45) · `real_solution_id` NULL (100%) · σ NULL (100%) · `modelo_hp` NULL (45/45) | 45/45 | **Por-desenho com regra citada**: DI-16.17, DI-16.1, DI-30.B2. O gate não exige ② não-vazia. |
| `cobertura95` vazia no `sonda_f52e.csv` | 104/104 | **Correto por regra** (§5: onde σ é NULL por desenho → N/A). Aqui, ao contrário do c311, **não há inflação** — σ é NULL em 100% dos pontos, então a coluna sai vazia em vez de 1,0000. |
| células REPROVADAS / falsos-vermelhos de tolerância | 0/45 | Nenhuma. `moead_media` passou limpo nas duas fases. |

**Contrato: aprovado, com 1 não-conformidade de writer já triada (item 6) e 1 ressalva de ambiente com dano zero provado.**

---

## 6. Saúde em escala

**6.1 Sonda (a régua, 1 bloco por congelamento).** 104 pares célula×objetivo, 900.000 predições. **28 pares (26,9%) colapsados** (μ ≡ média a priori; WAPE 1,000; \|corr\| ≤ 0,015) em 14 células. Nos **76 pares sadios**: WAPE mediana **0,1268** (q25 0,0179 · q75 0,2711 · máx 2,059 em `DTLZ4` obj1), correlação mediana **0,934**, 43/76 com corr > 0,9 e apenas 3 com corr negativa. Por família de problema:

| família | n | WAPE mediana | corr mediana |
|---|---:|---:|---:|
| ZDT | 21 | **0,0014** | **1,000** |
| DTLZ (sadios) | 9 | 0,0459 | 0,960 |
| BBOB | 13 | 0,0731 | 0,937 |
| MMF | 15 | 0,1582 | 0,945 |
| **WFG** | 18 | **0,2752** | **0,103** |

Leitura: o Kriging isotrópico aprende ZDT quase exatamente (f0 = x0) e falha nas transformações WFG (corr ~0,10) — **o mesmo padrão que o c311 encontrou na sua família**, o que reforça que é característica do *problema*, não do config. Não há tendência 1º→último bloco a reportar (1 bloco por desenho, §F1).

**6.2 Trajetórias (20 checkpoints).** 45 arquivos × 19 transições = **855 transições, 0 violações de monotonicidade de IGD+**. **Ressalva de leitura obrigatória** (herdada do c311, revalidada aqui): no offline a trajetória percorre a **acumulação do dataset** (fe 0…N−1), portanto é monótona **por construção do arquivo ND** — é sinal de sanidade da métrica, **não** curva de aprendizado do algoritmo. Nenhuma trajetória do piso reflete a busca.

**6.3 Posição vs pisos / papel de régua.** Estruturalmente **indiscriminante pela ①**: IGD+ idêntico (diferença relativa 0,000e+00) entre os 4–5 offline em **45/45** células — o piso "bate" e "é batido" por empate em 100% dos casos. O endpoint é a **⑦**, e a leitura está em §4(ii). Aviso metodológico: a razão de fantasia (`nd_pos_real/n_final`) **não** é indicador de qualidade — o piso tem fantasia mediana 0,360 contra 0,380 do b5m (praticamente empatados; piso maior em 20/45), mas o caso `BBOB_F17` mostra o problema: fantasia = **1,000** (todos os 50 finais mutuamente não-dominados) com μ errado por **5,4e6** e IGD+⑦ pior que o do b5m. Fantasia alta pode significar "nuvem espalhada e incomparável", não "modelo honesto". Use IGD+⑦ como endpoint e fantasia como diagnóstico secundário.

**6.4 Erro de fantasia comparado (a assinatura do mecanismo).** Nos mesmos 104 pares, com o par ligado posicionalmente (③ última geração → ⑦):

| config | pares com **100%** de otimismo | otimismo mediano | WAPE da população final (mediana) |
|---|---:|---:|---:|
| **moead_media (μ)** | **69/104** | **1,000** | **0,985** |
| b5m (σ) | 29/104 | 0,719 | 0,256 |
| b5r (σ) | 24/104 | 0,785 | 0,242 |
| e103 | 1/104 | 0,510 | 0,738 |

O piso tem WAPE-final **pior que o b5m em 86/104 pares (82,7%)** e é mais otimista que ele em 64/104 (empate em 28, menos otimista em 12). Somado a C10 (91,3% dos pares terminam abaixo do mínimo do dataset), esta é a prova quantitativa de que **a função do σ na seleção é impedir que a busca colonize a extrapolação do modelo**.

**6.5 Sweep — "mais dado → melhor?" no endpoint certo.** Pela ① a resposta é "sim em 9/10 séries" (F5.5 §4). Pela **⑦** ela se inverte: para o piso, small→medium melhora o IGD+⑦ em apenas **4/10 séries** (melhora: MMF16_20-lhs 0,301→0,108 · WFG9-lhs 0,527→0,472 · ZDT4-lhs 210,6→144,5 · ZDT4-mvns 204,2→144,5; piora: DTLZ2-lhs 0,890→**2,686** · DTLZ2-mvns 0,686→**2,427** · MMF16_20-mvns 0,082→0,427 · WFG9-mvns 0,324→0,388 · ZDT1-mvns 0,196→0,415 · ZDT1-lhs 0,198→0,236). E o **b5m tem exatamente o mesmo placar (4/10)**; medianas por tier: piso 0,425 (small) → 0,450 (medium); b5m 0,290 → 0,658; e103 0,257 → 0,344; só o b5r melhora (0,301 → 0,240). **Insumo transversal para o D97**: o placar "mais dado melhorou em 46 séries" da F5.5 §4 é artefato de a ① *ser* o dataset; no endpoint real, dobrar/triplicar o dataset **não** melhora sistematicamente nenhum offline com surrogate global. Agravante mecanístico deste config: 6 dos 14 colapsos do GP estão no tier medium (n=2.000) — mais dado **aumentou** a incidência de degeneração do Kriging não-normalizado.

---

## 7. SCORE e recomendação

**SCORE: 9,0/10** (prior D77 v2: 9,0 — **a âncora do autor bate exata**) · **RECOMENDAÇÃO: ACEITAR + CAVEAT** (o caveat é científico — as 14 células confundidas —, não de fidelidade do mecanismo).

1. **Perfeição estrutural**: as ~40 invariantes das baterias U + família + config fecham **45/45 células** — 30.165 decisões densas, 2,7 M linhas de ③, ⑦ recomputada e ligada bit-a-bit em 100%, join da sonda com ΔX = 0,0 em 900.000 pontos, ① bit-a-bit com o artefato em 45/45, 0 guards, 0 retries, 0 células reprovadas.
2. **Dois teoremas novos que os pilotos não tinham**: (a) o **determinismo do RNG foi PROVADO por re-run** (`off` × `swap_small-lhs` bit-idênticos em 5/5 problemas) — o item sai do teto T; (b) a **cirurgia da ablação foi PROVADA estruturalmente** (`n_geracoes` ≡ b5m em 45/45, `t_fit` 0,97×, μ a 1 ULP em 62,5%), com o custo de σ atribuído **integralmente à busca** (62,5×).
3. **Zero surpresas nas divergências**: 18/28 aspectos são desvios sancionados com decisão citada (DI-16.1/16.4/16.17, DI-13.5, DI-28/28.3, DI-30.B2/B3, D68, D90/D51, P5/DI-16.5) e 9/28 são conformes.
4. **Um item (3) 🎯 real e material**: a taxa de colapso do GPR é 3,1× a do b5m sobre o mesmo dataset e a mesma especificação (p < 1e-4), confundindo 31% das células da ablação — é o que impede 9,5+.
5. **Contrato limpo o bastante**: a única não-conformidade (⑤ sem `params`) já é item 6 da torre com fallback verificado, e a única ressalva de integridade tem **dano zero provado por bit-identidade**.

---

## 8. Aspectos classe (3) 🎯 — evidência completa (→ F5.4)

**🎯 C9b — Assimetria da taxa de colapso do GPR entre configs de especificação idêntica.**

- **Fato medido**: pelo critério "WAPE = 1,000 ± 1e-4 **e** \|corr\| ≤ 0,015" aplicado aos mesmos 20.000 pontos de sonda, nas mesmas 45 células, sobre os **mesmos datasets bit-a-bit**: `moead_media` **28/104 (26,9%)** · `b5m` **9/104 (8,7%)** · `b5r` **5/104 (4,8%)**. χ² = 21,6 (gl 2) ⇒ p < 1e-4 sob taxa comum.
- **Onde**: `off/{BBOB_F17, DTLZ1, DTLZ2, DTLZ3, DTLZ4, ZDT6}` e `swap_{small,medium}-{lhs,mvns}_{DTLZ2, MMF16_20, ZDT4}` — **14/45 células**.
- **Célula-prova**: `off/DTLZ2` — piso colapsa nos **3** objetivos (WAPE 1,0000/1,0000/1,0000; μ ≡ 0,0 nos 20.000 pontos em obj0 e obj2; corr NaN/0,0038) enquanto o b5m está sadio (0,0915/0,0994/0,0505). IGD+⑦: **0,8904 (piso) × 0,0569 (b5m)** = 15,6×. A atribuição desse fosso a "σ" é **inválida**.
- **Bidirecionalidade** (afasta "bug do piso"): em `off/DTLZ1` obj1 e `off/DTLZ3` obj1/obj2 é o **b5m** que colapsa e o piso não; e o b5m congela a população nessas células (370 e 380 gerações sem mudança).
- **O que está sancionado e o que não está**: DI-28 sanciona μ **não-idêntico** (confirmado: 37,5% dos pares divergem; nos outros 62,5% a diferença é 1 ULP de float32). **Não** há decisão que sancione taxa de degeneração 3× maior.
- **Pedido à F5.4** (verificação adversarial de código, escopo pequeno): (i) localizar o ponto de consumo do `RandomState` global imediatamente antes de `SurrogateKriging.fit` nos runners do piso e do b5m e verificar se diferem; (ii) confirmar que o `y` passado ao GPR é o mesmo array (mesma ordem, mesmo dtype, sem flip) nos dois; (iii) confirmar `normalize_y=False`, `alpha=0` e os bounds `RBF(10,(1e-2,1e2))` no vendor.
- **Pedido à M8/M9**: re-medir a taxa nas 30 sementes. Com 1 semente não se separa "mecanismo" de "semente infeliz" (§5 do protocolo / caveat 8 do F5). **Se a assimetria persistir**, ela vira uma limitação declarada da ablação D77 e a F5.5 deve reportar o contraste **só nas células limpas**.
- **Sugestão à torre (F5.7, não a este config)**: gravar `modelo_hp` (comprimento de escala e amplitude por objetivo) **nos dois lados da ablação** derrubaria este item de "indireto" para "direto" em uma linha de código — a assimetria espúria que DI-30.B2 quis evitar não existe se ambos gravarem.

---

## 9. Teto de verificabilidade (T) e armadilhas confirmadas na escala

**Teto T (5 itens, fora do denominador):** **T1** kernel/HP ajustados do GPR — declarativo (`sigma_dict`), sem `modelo_hp` (DI-30.B2); evidência empírica só indireta pelo padrão de colapso. **T2** rampa θ do PBI = f(fe/40.000) — não instrumentada. **T3** parâmetros internos do MOEA/D (vizinhança T, prob. de seleção local, SBX/PM, δ) — ⑤ sem `params` e sem eco no ⑥. **T4** o não-consumo de σ na seleção — contrafactual: σ não é sequer calculado, só o código prova. **T5** inércia dos patches `b5-mode72-kde`/`b5-mode7-archive` no mode 12 — declarativa, coberta por `anchors.json`+`repos.lock`.
**Saiu do teto**: **semeadura/RNG (D62/DI-28.3)** — nos pilotos era "só re-run bit-idêntico verifica"; a campanha continha o re-run e ele fecha bit-a-bit em 5/5 problemas (§C7).

**Armadilhas confirmadas / novas (numeração continuando a do c311):**
**(20)** O piso offline tem **duas instâncias**: `moead_media` (small+medium, `env_b5`) e `treed_media` (big, `env_c311`) — P5/DI-16.5. Contar "o piso offline" como 45 células **subconta**; são 54.
**(21)** **Métricas oficiais da ① empatam EXATAMENTE (Δrel = 0,000e+00) entre os offline em 45/45** — revalidação independente do achado do c311 (armadilha 16). Nunca ranquear offline pela F5.2c; o endpoint é a ⑦.
**(22)** **Fantasia alta ≠ bom.** `nd_pos_real/n_final = 1,000` em `BBOB_F17` com μ errado por 5,4e6 e IGD+⑦ pior que o do b5m. Fantasia mede incomparabilidade mútua do conjunto final, não qualidade.
**(23)** **WAPE = 1,0000 é assinatura de GP colapsado**, não "erro de 100%": Σ\|0−f\|/Σ\|f\| = 1 identicamente quando μ ≡ 0. Sempre cruzar com a correlação (≈0) e com `mu_min/mu_max` antes de ler o número como desempenho.
**(24)** `cobertura95` do `sonda_f52e.csv` vem **vazia** (não inflada) neste config — porque σ é NULL em **100%** dos pontos. É o comportamento correto por regra (§5) e o **contraste** com a armadilha 15 do c311 (σ-NaN **parcial** inflava a cobertura a 1,0000).
**(25)** **Footer `failed` residual em célula sadia**: `swap_small-lhs_ZDT1` tem 3 footers, um deles `status='failed'` de um escritor concorrente morto 2 min antes. Triar término por footer **reprova a célula por engano**; a regra deste config é `motivo_parada` do ⑤ (`orcamento` em 45/45).
**(26)** `off/{p}` e `swap_small-lhs/{p}` são **o mesmo experimento** (mesmo artefato `ds_{p}_42.parquet`) — 5 pares por config offline. É duplicação de custo no grid (≈5 células/config), **e** é o único re-run bit-a-bit disponível: use-o como teste de determinismo antes de gastar re-runs na F5.7.
**(27)** No offline a **trajetória de 20 checkpoints é a acumulação do dataset**, monótona por construção (0 violações em 855 transições) — revalida a armadilha 17 do c311; não é curva de aprendizado.
**(28)** "Mais dado → melhor" vale na ① e **não vale na ⑦**: 4/10 séries para o piso e 4/10 para o b5m. Conclusões de tier tiradas da F5.2c são artefato.

---

### Rodapé — artefatos de evidência (todos em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/moead_media/`)

**Scripts** (READ-ONLY nos dados; interpretador `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`):
`b1_estrutural.py` (bateria U1–U12 + família + config nas 45 células) · `b2_ablacao.py` (versão integral da ablação; **abandonada por custo de I/O** — substituída por b6/b7/b8/b9) · `b3_trajetorias_determinismo.py` (trajetórias, re-run bit-a-bit, fantasia final) · `b4_fantasia_comparada.py` (μ×f real dos 4 offline) · `b5_extrapolacao.py` (`f_best` × mínimo do dataset) · `b6_ablacao_rapida.py` (versão com projeção de colunas) · `b7_mu_identidade.py` (μ da sonda piso × b5m/b5r) · `b8_fantasia_sweep.py` (fantasia das 45 células × 4 configs) · `b9_turnover_e_sweep7.py` (turnover por config + ⑦ do sweep).

**CSVs de evidência**: `bateria1_estrutural.csv` (45 linhas × 100 colunas — todas as invariantes) · `sonda_recomputada.csv` (104 pares; WAPE/corr recomputados, batem a F5.2e em ≤4,7e-7) · `mu_identidade_piso_vs_b5.csv` (208 comparações posicionais de μ) · `turnover_por_config.csv` + `turnover_por_geracao.csv.gz` (30.120 transições × 3 configs) · `fantasia_final.csv` e `fantasia_comparada.csv` (μ da população final × f real, 4 configs) · `extrapolacao_fbest.csv` (104 pares) · `camada7_sweep.csv` (⑦ das 20 células de sweep × 4 configs — **não existia**: o `transversal_offline_camada7.csv` da F5.5 cobre só as 25 `off`) · `fantasia_45celulas.csv` · `determinismo_rerun.csv` · `trajetorias_moead_media.csv`.

**Insumos pré-computados consumidos (não recomputados)**: `f5/metricas_finais_f52c.csv` · `f5/sonda_f52e.csv` · `f5/contrato_f52b.csv` · `f5/integridade_f52a.csv` · `f5/tempo_f52d.csv` · `f5/trajetorias/*_moead_media_*_42.json` · `f5/transversal_offline_camada7.csv` · `f5/transversais_f55.md`.