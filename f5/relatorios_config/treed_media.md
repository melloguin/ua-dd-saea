# RELATÓRIO DE FIDELIDADE — `treed_media` (Treed-média, PISO BIG · alg_id 23) · F5.3b · semente 42

**Universo**: **10/10 células** do config — 5 problemas {ZDT4 D=10, DTLZ2 D=12, MMF16_20 D=20, WFG9 D=22, ZDT1 D=30} × 2 distribuições {LHS, MVNS}, todas `tier=big` (N=50.000), todas semente 42, **todas no `mac`** (`tempo_f52d.csv`) ⇒ **piso de ruído entre máquinas (HV ≤1,55%; IGD+ ≤58,98%, O-18) NÃO se aplica** — máquina única, e o par da ablação (c311-big, também 100% `mac`) é intra-máquina. Zero células excluídas. Agregados da bateria: **876.627 linhas de ③** (676.627 de busca + 200.000 de sonda), **500.000 linhas de ①**, **678 linhas de ⑦**, **10.000 gerações**, **32 eventos de ⑥**, **675.616 reavaliações de X** auditadas para o teste de congelamento e **347.515 pontos de sonda** no teste de identidade da árvore contra o c311.

---

## 1. Ficha do mecanismo

`treed_media` **não é um algoritmo da literatura** — é a **ablação cirúrgica do c311 (TGPR-MO, Mazumdar et al. 2023, *ECJ* 31(4)) no tier big**, criada por B15.4/DI-16.5[P5]/D38/**DI-35.2** (REGISTRO A23) para responder a UMA pergunta: *quanto os GPs locais acrescentam em N=50.000?* Por isso **não há artigo**: o gabarito é a especificação canônica do bundle (`handoff/T8-piso-big.md` + `alg_c311_tgprmo.md`) mais as decisões do REGISTRO. A Entrega 2 (comparação canônica) é **N/A**; ocupa o lugar dela a seção **PAPEL DE CONTROLE** (§4).

O fluxo, à risca do cartão T8: `ds_{prob}_42_big_{dist}.parquet` (① = dataset, orçamento ESGOTADO) → `_build_surrogates` **IMPORTADA de `src.c311_tgprmo`** (1 `treeGP` por objetivo, **SÓ a árvore**: nenhum `addGPs`, `error_leaves=None`) → **SONDA** (1 bloco de 20.000, μ da árvore, σ NULL) → **RVEA final `10 × 100 = 1.000` gerações** sobre a árvore FIXA (`selection_type="mean"`, α=2 — a fase FINAL do c311) → **⑦** do ND real pós-hoc (fora do orçamento, DI-08). Predição = **média da folha**; sem GP não há variância ⇒ **σ NULL em TODA a ③** (DI-16.1, precedente `moead_media` = "o b5 sem σ"; aqui "o c311 sem GPs"). Contador `geracao` **simples 1..1000** (fase única — sem o offset 2-fases C311-11/DI-16.19 do c311). Roda no `env_c311` (py3.8.20, sklearn 1.1.2, pymoo 0.6.1.2, torch/gpytorch ausentes) com `OMP/OPENBLAS/MKL/NUMEXPR=1`. Divergências sancionadas da linhagem c311 herdadas: `max_depth=100` (🟠 código), σ como extensão nossa (aqui **removida** por DI-16.1), tiers D38/D90/D51.

---

## 2. DISSECAÇÃO DOS ASPECTOS — o CORE

### 2.1 Tabela-resumo (29 aspectos · 1 linha cada)

| # | aspecto | classe | verif. | resultado-síntese (10 células salvo indicação) |
|---|---|---|---|---|
| U1 | Offline puro: FE = dataset, zero FE real na busca | **(1)** | direta | `tempo_aval_real_s==0` 10/10; `fe_final==maxfe==50.000` 10/10; ① 100% `fase=init`; `fe_index` denso 0..49.999 |
| U2 | Binding ① ↔ artefato de dataset (D63/D87/D90) | **(2)** | direta | sha256-float64 **recomputado por mim**: `x_hash` e `f_hash` batem 10/10; ①≡artefato **bit-a-bit** (max\|ΔX\|=max\|ΔF\|=0), ordem preservada |
| U3⊕U8 | Treino ÚNICO: ④=1 linha, `fit_series`=1, `fe_treino_max`≡49.999 | **(2)** | direta | 10/10 (`n_acumulado=50.000`, `iter=1`); `fe_treino_max` valor único 49.999 = N−1 em 876.627 linhas |
| U4 | Cadência da sonda: **1 bloco** × 20.000, `geracao`=NULL | **(2)** | direta | 1 evento `sonda` 10/10; 20.000 linhas 10/10; `geracao` NULL 100% (DI-13.5 — igual a c311/b5m/e103/moead_media); `hash_check='ok'` 10/10 |
| U5⊕U6 | Régua da sonda: join posicional + WAPE (§5) + cobertura | **(2)** | direta | max\|ΔX\| **= 0,0 exato** (após cast f32) 10/10; WAPE recomputado ≡ `sonda_f52e.csv` na 6ª casa em 24/24 pares; **cobertura = N/A por regra** (σ NULL) |
| U7 | ④: `fit+busca ≤ tempo_geracao_s`, sonda EXCLUÍDA (DI-13.10) | **(2)** | direta | identidade **exata** em 8/10 e a 1 ULP-f32 (Δ=9,5e-7; rel 1e-7) em 2/10; **`+sonda` estoura em 10/10** (+0,088 a +0,166 s) |
| U9⊕U10 | Reconciliação entre camadas + guardas | **(2)** | direta | 0 eventos `guard`; `cache_hits=0` no ⑤ **e** no footer; Σ pop/geração ≡ `n_③busca` 10/10; footer≡manifesto≡③ (`n_ger=1000`) e footer≡⑦ (`n_final`,`n_nd`) 9/9 com footer |
| U12 | ⑦: ND recomputado ≡ `nd_pos_real` + link posicional | **(2)** | direta | recomputo **exato 10/10** (678 pontos, 309 ND); `(origem_geracao,origem_linha)`→③ **bit-a-bit** 678/678; `origem_geracao`≡1000 10/10 |
| F1 | **Congelamento do surrogate** (prova nova, sem 2º bloco) | **(1)** | direta | **675.616 reavaliações** de 9.443 X repetidos (até 1.000 reavaliações do mesmo X, span de até 999 gerações): **0 divergências de μ** |
| F2 | σ NULL em 100% da ③ (DI-16.1) | **(2)** | direta | `sigma_*` NaN em **876.627/876.627 linhas**, busca e sonda; μ NaN em 0 |
| F3 | ② vazia + `real_solution_id` NULL (DI-16.17) | **(2)** | direta | ②=0 linhas 10/10; `real_solution_id` NULL 100% |
| F4⊕U11 | Fantasia: endpoint é a ⑦ (`nd_pos_real/n_final`) | **(2)** | direta | fantasia mediana **0,291** (faixa 0,194–0,752); WAPE-fantasia (μ da ③ × f real da ⑦) 0,081–0,356 |
| F5 | Métricas oficiais da ① EMPATAM entre offline (D69) | **(2)** | direta | IGD+/HV/\|ND\| **idênticos** a c311 em 9/9 pares; **trajetórias de 20 checkpoints bit-idênticas em 9/9** |
| C1 | **A ABLAÇÃO**: `_build_surrogates` direto, SEM `addGPs` | **(2)** | direta | 0 eventos `decision`; 1 fit; **folhas ≤ N/(10D) em 10/10** (c311: 0/9); quantização de μ 98,0–99,4% |
| C2 | Árvore MSE, `min_samples_leaf=10D`, teto de folhas N/(10D) | **(1)** | direta | `msl`∈{100,120,200,220,300}≡10D 10/10; folhas tocadas 115–393 ≤ teto 166–500; **ocupação 74,4–78,6%** |
| C3 | `max_depth=100` (🟠 código, não "livre") | **(2)** | **direta-declarativa** | declarado 10/10 no `params`; não-vinculante por inferência (folhas paradas pelo `min_samples_leaf`) |
| C5 | RVEA final **10×100=1000** ger sobre surrogate fixo | **(1)** | direta | `n_ger=1000` denso 10/10; **QUERY-JOIA**: saltos de população concentrados em g≡1 (mod 100), \|Δpop\| médio **9,5–54,3×** o global, p≤0,053 em 10/10 e **p≤1e-4 em 7/10** |
| C6 | Contador `geracao` SIMPLES 1..1000 (sem offset C311-11) | **(2)** | direta | `set(geracao)`≡{1..1000} 10/10, zero furos, zero colisões (o c311 precisa do offset; aqui não) |
| C7 | Pop lattice 50 (M=2) / 105 (M=3), **pode encolher** | **(1)** | direta | teto **nunca** excedido 10/10 (máx 105/104/103 e 50/48/46/45); mínimo 32–78; encolheu em 10/10 |
| C8a | σ **não consumido** na seleção | **(1)** | direta | estruturalmente provado: **não existe σ na ③** — o contrafactual é impossível (≠ c311, onde era T) |
| C8b | `selection_type='mean'` / agregador da folha | **T** | não-verif. | declarado 10/10; média × mediana da folha não separável ex-post (necessária: μ ∈ envelope do dataset — **10/10 ✓**) |
| C9 | Espaço do modelo **CRU** (sem normalizer/z-score) | **(1)** | direta | `espaco_modelo='cru'` e `transf_tipo/params` NULL em 876.627/876.627; μ dentro do envelope [min f, max f] do dataset em 10/10 e 24/24 objetivos |
| C10 | Tier big=50k + eixo LHS×MVNS (D38/D51/D90) | **(2)** | direta | `tier='big'`, `n=50.000`, `dist` do manifesto ≡ do artefato ≡ do label 10/10; `seed_tuple=(42, prob_id, 2, {0,1})` |
| C11 | Teto universal DI-35.5 (43.200 s), rito do piso | **(2)** | direta-declarativa | declarado no `sigma_dict` 10/10; **folga 2.749×–7.370×** (wall 5,86–15,71 s); nunca exercitado |
| C12 | Receita/ordem do fluxo (build→sonda→RVEA→⑦) | **(2)** | direta | prova por RELÓGIO: Δ(header→sonda) − (fit+sonda) = **+0,017 a +0,027 s** 10/10; ordem `header>sonda>footer` 10/10 |
| C13 | Vendor c311 INTOCADO, fonte única, env/pinning | **T** | não-verif. | declarativo (`algo_version`, `sigma_dict.vendor`, env 10/10) — elo de código coberto por `anchors.json`+`repos.lock` |
| C14 | Semeadura D62 (`iteration_seed(42,23,0,0)`) + LHS DI-28.3 | **T** | não-verif. | exige re-run bit-idêntico |
| C15 | DI-28: "mesma ESPECIFICAÇÃO, treino INDEPENDENTE" | **(2)** | direta | **resolvido POR DADO**: μ bit-idêntico ao c311 em **347.499/347.515** pontos sem GP (**99,995%**); 16 divergências, todas MVNS, \|Δμ\|≤2,6e-5 |
| C16 | Rito de escrita: footer/`motivo_parada`/`upload_status` | **(2)** | direta | `motivo_parada='orcamento'` 10/10; footer do runner 9/10, do despachante 4/10; 1 célula sem footer (caveat F5.1 §2) |
| C17 | Comportamento do motor: a busca de fato busca? | **(2)** | direta | Σμ melhora **1,69%–25,57%** de ger 1→1000; mínimo em ger 53–418; \|ND\| em μ 2–41 na última geração |

---

### 2.2 Blocos narrativos por aspecto

#### U1 — Offline puro: o orçamento É o dataset, e a busca não gasta um único FE

**(a) O que o método canônico prescreve.** O TGPR-MO é offline puro: "no new data" (Mazumdar et al., Abstract/§2). Todo o orçamento é o dataset pré-coletado; a otimização inteira acontece sobre o surrogate, e a única avaliação real permitida fora dele é a do ND final. **(b) O que a nossa SPEC definiu.** D90 fixa o dataset como orçamento (`maxfe = n_dataset`), D38 abre o tier `big=50.000` e o runner do T8 instala `OfflineBudgetViolation` (pára-e-loga D81) para qualquer FE real durante a busca. **(c) Observado.** `tempo_aval_real_s == 0,0` em **10/10** manifestos; `fe_final == maxfe == 50.000` em 10/10; a ① tem exatamente 50.000 linhas com `fase='init'` em 100% delas e `fe_index` denso `0..49.999` (comparação com `np.arange` — igualdade exata em 10/10), `solution_id` igualmente denso, **zero X duplicado** dentro do dataset. **(d) Por quê.** A ① não é produzida pelo run: é o artefato injetado (ver U2); o laço RVEA nunca chama a função real, e o único `evaluate` real é o pós-hoc da ⑦, escrito fora do run pelo driver `final_eval` (DI-08). **(e) Veredito: (1) conforme · direta.**

#### U2 — Binding ① ↔ artefato de dataset: verificado por hash recomputado, não só citado

**(a/b)** O paper apenas supõe o dataset dado; a nossa D63/D87/D90 exige binding criptográfico: `doe_hash` = sha256 dos bytes float64 row-major do X do artefato, `cp_init_offline.f_hash` idem para F. O gate F5.1 já verificou isso (accept VERDE em 10/10) — mas o protocolo pede prova de primeira mão. **(c) Observado.** Abri os 10 artefatos `data/datasets/{prob}/ds_{prob}_42_big_{dist}.parquet`, **recomputei o sha256** e comparei: `x_hash` bate em **10/10** e `f_hash` em **10/10** (ex.: `swap_big-lhs_DTLZ2` → `9d7f3bd3594b1436…`, `a3b0abeb81b2ff0b…`; `swap_big-mvns_ZDT1` → `e9d9df220f34f9e5…`). Além do hash, comparei linha a linha: max\|ΔX\| = **0,0** e max\|ΔF\| = **0,0** entre a ① (float32) e o artefato castado a float32, com **ordem preservada** (igualdade posicional bit-a-bit) em 10/10. Os `seed_tuple` do artefato conferem com `SeedSequence((42, problema_id, tier_id=2, dist_id∈{0,1}))` e o `sampler` é `lhs-simple`/`mvns` conforme o eixo D51. **(d) Por quê.** O runner carrega o parquet, converte a float32 (D53, export sem arredondamento) e grava como ①; nenhuma reordenação ocorre porque a ① é escrita na ordem de leitura. **(e) (2) sancionado (D63/D87/D90) · direta.**

#### U3⊕U8 — Treino ÚNICO: a ④ com 1 linha e o `fe_treino_max` congelado

**(a)** No c311 a ④ tem uma linha por iteração de construção (o eixo de escalabilidade do `addGPs`, 44–99 linhas nas células big). **(b)** A ablação **remove esse eixo**: o cartão T8 fixa "④ = 1 LINHA (treino único; molde piso)" com `add_timing(geracao=1)`, e o `sigma_dict` declara `fe_treino_max` "constante 49999 (=n_dataset−1) em TODA linha (busca+sonda) — o dataset É o orçamento (D90); offline não retreina". **(c) Observado.** ④ com **1 linha** em 10/10, `geracao=1`, `n_acumulado=50.000` (≡ `len(①)`), e `fit_series` do ⑤ com **1 entrada** (`iter=1`, `n_acumulado=50.000`) em 10/10. `fe_treino_max` tem **valor único 49.999** em todas as 876.627 linhas da ③ (busca e sonda). **(d) Por quê.** Não há retreino: uma chamada a `_build_surrogates` produz as M árvores e o modelo nunca mais é tocado — o que F1 prova independentemente pelos dados. **(e) (2) sancionado (T8/D90) · direta.**

#### U4 — Cadência da sonda: 1 bloco, não 2 — e a diferença é informativa

**(a/b)** §17.2.2 fixa a sonda offline em 20.000 pontos Sobol; DI-16.12 dá ao c311 **dois** blocos (build + final) justamente porque o modelo dele MUDA entre as fases, e a bit-identidade dos dois blocos vira a prova do congelamento. Aqui o `sigma_dict` declara "1 bloco (modelo unico, sem retreino)". **(c) Observado.** Exatamente **1 evento `rec='sonda'`** por célula (10/10), `n_pontos=20.000`, `modelo_flag='treed_media/RVEA-arvore-media'` (valor ÚNICO em 876.627 linhas — sem a dicotomia `treedGP_build`/`treedGP_final` do c311), `hash_check='ok (conferido no arranque — load_sonda)'`, e `sonda_x_hash` do evento ≡ do manifesto ≡ do gabarito `data/sonda/sonda_{prob}.manifest.json` em 10/10. Na ③, `regime='sonda'` com **20.000 linhas** e `geracao` **NULL em 100%** — convenção DI-13.5, e conferi que é a mesma em c311/b5m/e103/moead_media (100% NULL nos quatro). **(d) Por quê.** Um bloco basta porque o modelo é único; o evento do ⑥ carrega `geracao:1` (campo obrigatório de DI-09, coerente com a emissão ANTES da geração 1 do RVEA), enquanto a ③ carimba NULL — não há contradição, são convenções distintas e ambas normativas. **(e) (2) sancionado (§17.2.2 + modelo único vs DI-16.12) · direta.**

#### U5⊕U6 — A régua: join posicional exato, WAPE reproduzido, cobertura N/A por regra

**(a/b)** O protocolo §5 congela WAPE por objetivo no espaço CRU e cobertura ±1,96σ, e manda o join sonda×gabarito ser **posicional** (nunca por `sonda_id` — não existe na ③). **(c) Observado.** Join posicional dos 20.000 pontos contra `data/sonda/sonda_{prob}.parquet`: max\|ΔX\| = **0,0 exato** após o cast float32 em 10/10 (em float64 o resíduo é 3,0e-8 a 1,9e-6 — puro arredondamento f32, maior no WFG9 cujos bounds vão a 44). **Recomputei o WAPE do zero** (o `espaco_modelo` é `cru` e `transf_params` é NULL, então não há des-transformação a fazer) e obtive os valores do `sonda_f52e.csv` **na 6ª casa decimal em 24/24 pares** — ex.: `lhs/DTLZ2` obj0 0,105582 (CSV 0,105582), `mvns/WFG9` obj1 0,282738 (CSV 0,282738). O painel: WAPE de **0,00195 (ZDT4-lhs obj0)** a **0,3068 (ZDT1-mvns obj1)**; correlações de **0,122 (WFG9-mvns obj0)** a **0,99999 (ZDT4/ZDT1 obj0)**. **Cobertura = N/A** — o `sonda_f52e.csv` já traz `cobertura95=NaN` com `n_validas=20000, n_nan=0` em 24/24, tratamento CORRETO e diferente do do c311, onde a métrica infla contando σ-NaN como coberto (armadilha 15 do relatório c311). **(d) Por quê.** O WAPE é a única métrica de calibração possível sem σ; a família de problemas domina o resultado (ZDT f0 quase-exato; WFG9 com correlação ≈0,12–0,42 — a árvore não captura as transformações WFG, exatamente como no c311). **(e) (2) instrumentação nossa · direta.**

#### U7 — A invariante dupla do timing: a sonda está fora, e prova-se pelos números

**(a/b)** DI-13.10 (ratificada) manda `tempo_geracao_s` EXCLUIR a sonda, porque a sonda é instrumentação deste estudo e contaminaria a curva de escalabilidade. **(c) Observado.** Com apenas 1 linha de ④, a invariante vira uma identidade: `tempo_fit_s + tempo_busca_s` **igual bit-a-bit** a `tempo_geracao_s` em **8/10** células, e a 1 ULP-float32 nas outras 2 (`lhs/MMF16_20`: 9,5951128 vs 9,5951118, Δ=+9,54e-7, rel 9,9e-8; `mvns/MMF16_20`: Δ=−9,54e-7, rel 8,0e-8 — as colunas do ④ são float32 por D53). E o **contrapositivo fecha em 10/10**: somar `tempo_pred_sonda_s` (0,0883–0,1660 s) estoura `tempo_geracao_s` em todas as células. **(d) Por quê.** O runner mede fit e busca separadamente e soma os dois para `tempo_geracao_s`, gravando a sonda num campo à parte; o resíduo de 1 ULP é o arredondamento f32 da soma. **(e) (2) sancionado (DI-13.10) · direta.**

#### U9⊕U10 — Reconciliação: nenhuma guarda disparou, e a aritmética entre as 7 camadas fecha

**(c) Observado.** ⑥ com **0 eventos `rec='guard'`** nas 10 células (contraste: o c311 teve 2 `hard_error` de `ModuleNotFoundError: google`); `cache_hits=0` no ⑤ **e** no footer (reconciliação U9 exata, 9/9 com footer). Aritmética: Σ (linhas por geração da ③) ≡ `n_③busca` em 10/10 (104.895; 104.818; 45.294; 49.874; 37.073; 101.957; 101.102; 46.596; 47.737; 37.281); `n_geracoes` do footer ≡ do manifesto ≡ `max(geracao)` da ③ = **1000** em 10/10; `footer.n_final` ≡ `len(⑦)` ≡ população da geração 1000 (105/105/46/50/36/102/47/48/37) e `footer.n_nd_pos_real` ≡ `⑦.nd_pos_real.sum()` (61/79/16/11/7/37/11/10/8) em 9/9 células com footer. **Nenhum off-by-one** — ao contrário do b1 (②=N+1) e do e7 (④ ger-1 duplicada), aqui o mapeamento é 1:1 porque não há laço de construção. **(e) (2) · direta.**

#### U12 — A ⑦: Pareto recomputado, link posicional bit-a-bit, e o `origem_geracao` sempre 1000

**(a/b)** DI-08 define a ⑦ como o ENDPOINT do regime offline (ND final avaliado 1× na função real, fora do orçamento); DI-13.9/B7.5 exigem que ela seja **reconstituível da ③**; DI-27/A15 mandam o `write_final` calcular o `nd_pos_real`. **(c) Observado.** Recomputei a dominância nas 678 linhas de ⑦: o vetor `nd_pos_real` recomputado é **idêntico ao gravado em 10/10 células** (309 ND no total). O link posicional `(origem_geracao, origem_linha)` → ③: `origem_linha` é denso `0..n−1` em 10/10, `origem_geracao` é **constante = 1000** em 10/10, e o X da ⑦ bate **bit-a-bit** (max\|ΔX\|=0,0) com a linha correspondente da ③ em **678/678 pontos**. `origem_solution_id` é NULL em 100% — coerente com a ② vazia (F3). **(d) Por quê.** A ⑦ é a população da última geração RVEA reavaliada na função real; nada é reordenado, então o link posicional é exato. As 4 células com desvio-tolerância da ⑦ que o autor aceitou na F5.1 §4.2 são do c311/b5m — **nenhuma é do treed_media**; aqui o `final_eval --check` deu VERDE em 10/10. **(e) (2) instrumentação (DI-08/DI-13.9) · direta.**

#### F1 — CONGELAMENTO: a prova que substitui os dois blocos bit-idênticos do c311

**(a)** §3.1 do paper exige que a otimização final rode sobre o surrogate **congelado**. **(b)** No c311 essa propriedade é provada pela bit-identidade dos 2 blocos de sonda (DI-16.12) — 54/54 no piloto. Aqui **essa prova não existe**: há 1 bloco só, por desenho. Precisei de uma prova nova. **(c) Observado.** Se o surrogate mudasse durante as 1.000 gerações, um MESMO x reavaliado em gerações diferentes teria μ diferente (o modelo é uma função determinística x↦μ). Agrupei as 676.627 linhas de busca por X **bit-a-bit** e contei μ distintos por grupo: dos **10.454 X únicos**, **9.443 são reavaliados** em gerações distintas, cobrindo **675.616 linhas** — com **até 1.000 reavaliações do mesmo ponto** (`lhs/ZDT1`) e spans de até **999 gerações** (`lhs/ZDT1`: primeira e última geração). **Em ZERO deles μ divergiu** (`n_X_com_mu_divergente = 0` em 10/10). Prova complementar: o **alfabeto de valores de folha** da busca está contido no da sonda em **100,00% em 5/10 células** e ≥95,96% nas 5 restantes (todas MVNS) — o modelo que respondeu à sonda é o mesmo que respondeu à busca. **(d) Por quê.** O RVEA final é elitista o bastante para carregar indivíduos por centenas de gerações; cada carregamento é uma reavaliação do surrogate. Os <100% de contenção do alfabeto são folhas que a busca alcançou mas que os 20.000 pontos Sobol da sonda não amostraram — efeito da concentração MVNS (ver C15), não de mudança de modelo. **Esta prova é mais forte que a do c311**: 675.616 pontos de verificação contra 2 blocos. **(e) (1) conforme · direta.**

#### F2 — σ NULL em 100% da ③: NaN total é INFORMAÇÃO, não bug

**(a/b)** No paper, a variância do GPR é "anunciada mas não consumida" (§5, trabalho futuro); no nosso c311 ela virou **extensão** exportada (B15.5/D30 🟢). Aqui **DI-16.1** manda o oposto: sem GP não há variância, e excluí-la é **o que torna o contraste atribuível só a σ**. **(c) Observado.** `sigma_0..sigma_{M−1}` são NaN em **876.627 de 876.627 linhas** (busca e sonda, 10/10 células) — 100,00%, não 99,9%. `mu_*` é NaN em **0** linhas. O `sonda_f52e.csv` reflete isso corretamente com `cobertura95=NaN`. **(d) Por quê.** O `_Recorder` passa `sigma=None` e o `_sonda_predict_media` retorna `None` — a árvore de regressão do sklearn não expõe variância preditiva. **(e) (2) sancionado (DI-16.1) · direta.** ⚠ Armadilha: qualquer leitor que veja "σ = NaN em toda a camada" e conclua "bug" está errado por 1 decisão citada — é o desenho.

#### F3 — ② vazia e `real_solution_id` NULL, por construção

**(a/b)** DI-16.17: a pop inicial do RVEA é um LHS NOVO (`CreateIndividuals`/`LHSDesign`) mais SBX/PM contínuos ⇒ nenhum indivíduo coincide com o dataset; logo `real_solution_id=NULL` em toda a busca e `n_ds_membros=0`; o gate NÃO exige ② não-vazia. **(c) Observado.** ② com **0 linhas** em 10/10; `real_solution_id` NULL em **100% das 876.627 linhas**. Corroboração independente: os X da busca vivem dentro dos bounds do problema (ZDT4 em [−5,5], WFG9 até 44) mas os X do dataset e os da busca não coincidem — a ① tem 0 X duplicados e o `n_X_unicos` da busca (359–2.137) é ordens de grandeza menor que 50.000. **(d) Por quê.** Amostragem contínua nova + operadores contínuos: a probabilidade de colisão bit-a-bit em float32 e D∈[10,30] é nula. **(e) (2) sancionado (DI-16.17) · direta.**

#### F4⊕U11 — Fantasia: no offline o U11 muda de endereço (da ② para a ⑦)

**(a/b)** U11 pede o erro de fantasia dos infills via `real_solution_id`→①. **Isso é impossível aqui** (F3: `real_solution_id` é NULL por desenho), então o endpoint de fantasia da família offline é a razão `nd_pos_real/n_final` da ⑦ (DI-08): a fração do "front" do MODELO que sobrevive à realidade. **(c) Observado.** Fantasia por célula: `lhs/MMF16_20` **0,752** (79/105) · `lhs/DTLZ2` 0,581 · `mvns/MMF16_20` 0,677 · `lhs/WFG9` 0,348 · `mvns/DTLZ2` 0,363 · `mvns/WFG9` 0,234 · `lhs/ZDT1` 0,220 · `mvns/ZDT4` 0,216 · `mvns/ZDT1` 0,208 · `lhs/ZDT4` **0,194** (7/36) — mediana **0,291**. Medi também o erro de fantasia diretamente: comparei o μ que o modelo previu para cada ponto da última população com o f REAL medido na ⑦ — WAPE-fantasia de **0,081 (`lhs/MMF16_20`)** a **0,356 (`lhs/DTLZ2`)**; erro mediano por objetivo de 0,0008 (ZDT4-lhs f0) a 20,95 (ZDT4-lhs f1). **(d) Por quê.** A média de folha achata a superfície: dentro de uma folha o modelo não distingue pontos, então o RVEA acumula empates que a função real desempata — cerca de 70% dos pontos que o modelo julgava não-dominados são dominados na realidade. **(e) (2) sancionado (DI-08) · direta.**

#### F5 — As métricas oficiais EMPATAM por desenho: aqui está a prova em 9 pares

**(a/b)** D69 manda a métrica ler o `f` gravado na ①. No offline a ① É o dataset compartilhado ⇒ todos os configs offline sobre a mesma célula produzem **exatamente** o mesmo IGD+/HV/\|ND\|. O piloto c311 já apontou isso; aqui a prova é direta. **(c) Observado.** `metricas_finais_f52c.csv`: `sweep-big-lhs/DTLZ2` → c311 e treed_media com IGD+ **0,173895**, HV 0,379981, \|ND\| 300 — dígito a dígito; idem nos 9 pares. E fui além: as **trajetórias de 20 checkpoints** (`f5/trajetorias/`) são **strings idênticas** em 9/9 pares (IGD+ de 157,96→44,30 no ZDT4-lhs; de 1,0424→0,0076 no MMF16_20-lhs). **(d) Por quê.** A trajetória offline percorre a ACUMULAÇÃO do dataset (fe 0..49.999) — é a mesma série para qualquer config que compartilhe o dataset. **(e) (2) sancionado (D69) · direta.** ⚠ **Consequência prática, e é grande**: a métrica oficial é **estruturalmente incapaz** de ranquear o piso contra o c311. O papel de controle deste config depende inteiramente da ⑦ (§4).

#### C1 — A ABLAÇÃO em si: a assinatura de "árvore pura" nos dados

**(a)** O paper prescreve a construção iterativa: a cada iteração, a folha visitada de PIOR MSE ganha um GP local (Matérn 5/2 ARD, ≤2N_min−1 pontos), até I_max=⌈N/(10D)⌉ ou early-stop. **(b)** B15.4/DI-16.5[P5]/**DI-35.2** removem esse laço inteiro: `build_surrogates` DIRETO, `error_leaves=None`, nenhum `addGPs`. E DI-35.2 explica POR QUE isso é um módulo próprio e não um "ramo big" do c311: rotear `tier=='big'` para dentro do c311 transformaria o único config do tier big **na sua própria ablação**. **(c) Observado — quatro assinaturas independentes.** (i) **Zero eventos `decision`** no ⑥ (o c311 emite 44–99 por célula big); o ⑥ inteiro tem 32 eventos nas 10 células. (ii) **1 fit** (`fit_series`=1, ④=1 linha). (iii) **σ NaN total** (F2) — sem GP não há variância. (iv) A prova quantitativa mais bonita: como a árvore prediz a **média da folha**, μ_j é constante por folha, então **o nº de valores distintos de μ_j é o nº de folhas TOCADAS** e tem que respeitar o teto N/(10D). Medido nos 20.000 pontos de sonda: treed_media tem **115–393 valores distintos** contra tetos de 166–500 — **≤ teto em 10/10 células**. O c311, nas MESMAS células, tem **273–11.727** valores distintos — **> teto em 9/9** (até **70×** o teto no `mvns/ZDT1`: 11.727 vs 166). A quantização (fração de pontos que compartilham μ com outro) é **98,04%–99,38%** no treed contra 41,4%–98,6% no c311. **(d) Por quê.** Cada valor distinto de μ acima do nº de folhas só pode vir de um GP local (predição contínua). O contador de μ distintos é, portanto, um **medidor direto de quanto GP existe no modelo** — e no treed_media ele lê zero, em 10/10. **(e) (2) sancionado (B15.4/DI-16.5[P5]/DI-35.2) · direta.**

#### C2 — A árvore: `min_samples_leaf = 10D` e o teto de folhas que ela implica

**(a)** §4.1.3: N_min = 10n (paper ✓ no bundle). **(b)** Sem mudança — a especificação da árvore é a mesma do c311 (DI-28: "mesma ESPECIFICAÇÃO"). **(c) Observado.** `params.min_samples_leaf` = **100/120/200/220/300** para D = 10/12/20/22/30 — igualdade `msl == 10·D` em 10/10. Consequência aritmética: nenhuma árvore pode ter mais que ⌊N/N_min⌋ folhas — 500/416/250/227/166. Folhas tocadas na sonda: 256–393 (ZDT4, teto 500), 323–327 (DTLZ2, teto 416), 165–189 (MMF16_20, teto 250), 168–173 (WFG9, teto 227), 115–128 (ZDT1, teto 166) — **≤ teto em 10/10 e 24/24 objetivos**, com **ocupação de 74,4% a 78,6%** (mediana 76,1%). Pontos por folha na sonda: mediana 24–162; máximo **81** (`lhs/ZDT4`) contra **1.406** (`mvns/WFG9`). **(d) Por quê.** A ocupação estável em ~76% do teto mostra que o critério vinculante é o `min_samples_leaf` (a árvore divide até não poder mais) e que as folhas ficam na banda [N_min, 2N_min−1] esperada — folhas com ≥2N_min pontos ainda seriam divisíveis. O contraste LHS×MVNS nos pontos-por-folha (81 × 1.406) é a concentração do MVNS: algumas folhas cobrem um volume enorme do espaço, e é exatamente daí que sai a nuance de C15. **(e) (1) conforme (paper ✓) · direta.**

#### C3 — `max_depth=100`: declarado, não observável, e demonstravelmente não-vinculante

**(a)** O paper diz que a profundidade "não é controlada" (§3.1). **(b)** ⟦v2.2⟧ do bundle corrigiu: o **código oficial** fixa `max_depth=100` (🟠 impl→código pela bússola D29). **(c) Observado.** `params.max_depth = 100` em 10/10 — e só. Diferente do c311, cujo ⑥ grava `profundidade` nos eventos `decision` (observada 2/9/26 em small/medium/big), **o ⑥ do treed_media não tem evento de geração**, então a profundidade efetiva não é observável. O que É inferível: com 115–393 folhas, a profundidade mínima é ⌈log₂(393)⌉ = 9, e a ocupação de ~76% do teto de folhas indica que quem parou a árvore foi o `min_samples_leaf`, não a profundidade. **(d) Por quê.** Um teto de 100 níveis só poderia vincular numa árvore patologicamente desbalanceada; com 50.000 amostras e folhas de ≥100 pontos isso exigiria uma cadeia de ~100 cortes marginais, o que a ocupação observada refuta indiretamente. **(e) (2) sancionado (🟠 código, ⟦v2.2⟧) · direta-declarativa** — marca declarativa visível conforme o Botão 3; o elo de código é coberto por `anchors.json`+`repos.lock`.

#### C5 — RVEA final 10×100=1000: **a QUERY-JOIA deste config**

**(a/b)** §4.1.5 do paper e o bundle: otimização final RVEA `n_iterations=10` × 100 gerações = 1.000 gerações. O manifesto **declara** `n_iter_final=10`, `n_gen_final=100`, `n_gen_total_final=1000` — mas 1.000 gerações num contador simples são compatíveis com "1 × 1000", e a decomposição em 10 iterações seria puramente declarativa. **Achei como prová-la nos dados.** **(c) Observado.** O RVEA do DESDEO **adapta os vetores de referência no INÍCIO de cada `iterate`** (bundle: "α=2, adapt no INÍCIO de cada iterate"). Com 10×100, as adaptações caem nas gerações 1, 101, 201, …, 901. Uma readaptação muda quem sobrevive à seleção APD ⇒ salto no tamanho da população exatamente ali. Medi \|Δpop\| em todas as 999 transições de cada célula: o **\|Δpop\| médio nas 9 fronteiras é 9,5×–54,3× o \|Δpop\| médio global** (mediana global = 0,0 — a população é estável entre fronteiras), e o teste de permutação (20.000 sorteios de 9 transições) dá **p ≤ 0,053 em 10/10 células, p ≤ 1e-4 em 7/10, e 0/20.000 em 5/10**. O salto em **g=101 é o maior das 9 fronteiras em 9/10 células**, com 3 a 20 indivíduos (`mvns/DTLZ2`: 20; `mvns/MMF16_20`: 17; `mvns/ZDT4`: 14; `lhs/ZDT4`: 13), decaindo nas fronteiras seguintes. A estatística de μ concorda: \|Δ(média Σμ)\| nas fronteiras é **3,1×–19,5×** o valor global. **(d) Por quê.** A primeira readaptação (g=101) é a mais disruptiva porque a população acabou de sair da LHS inicial e a nuvem de μ mudou muito; nas iterações seguintes a população já está assentada nos vetores adaptados e o choque diminui. Isto é a assinatura de 10 chamadas a `iterate()` de 100 gerações — **não** de uma chamada única de 1.000. **(e) (1) conforme (paper ✓), agora com prova de dado e não só declarativa · direta.**

#### C6 — Contador `geracao` simples 1..1000: o que o c311 precisou inventar, aqui não é preciso

**(a/b)** C311-11/DI-16.19 obriga o c311 a um contador ÚNICO atravessando as duas fases (build 1..51·I_eff; final +1..+1000) — sem isso as ③ das duas fases colidiriam em `geracao=1..50`. O cartão T8 dispensa o offset: "fase única; o RVEA final nunca chama `_refresh_population`, então enganchamos SÓ o `_next_gen`". **(c) Observado.** `set(geracao)` da busca ≡ **{1,…,1000} exato** em 10/10 — 1.000 valores únicos, min 1, max 1000, **zero furos**. O `modelo_flag` é valor ÚNICO (`treed_media/RVEA-arvore-media`) em 876.627 linhas, contra os dois flags do c311 (`treedGP_build`/`treedGP_final`). **(d) Por quê.** Uma fase só ⇒ um contador só; e a ausência do `_refresh_population` elimina a +1 geração por iteração que o c311 tem (DI-28c, 51/iter). **(e) (2) desenho nosso, citado no cartão T8 · direta.**

#### C7 — Pop lattice 50/105 que pode encolher: o teto nunca é violado e o encolhimento é regra

**(a)** §4.1.3 (Cheng 2016): o tamanho da população é o número de vetores de referência do lattice — 50 para M=2, 105 para M=3 — e a população **pode encolher** quando vetores ficam sem indivíduo associado. **(c) Observado.** O teto **nunca foi excedido** em 10/10 (máximos: 105/105 nos dois M=3 LHS, 104 e 103 nos M=3 MVNS; 50/48/46/45 nos M=2). A população **encolheu em 10/10**, com mínimos de 32 (`lhs/ZDT4`) a 78 (`mvns/DTLZ2`) e média por geração bem abaixo do teto (a ③ da busca tem 37.073–104.895 linhas contra 50.000/105.000 se a pop fosse cheia). A população da última geração — que vira a ⑦ — é 105/105/46/50/36/102/102/47/48/37. **(d) Por quê.** A seleção APD só mantém um indivíduo por vetor de referência ativo; em problemas com front degenerado ou mal coberto (ZDT4 com g enorme, WFG9) muitos vetores ficam vazios. **(e) (1) conforme (paper ✓) · direta.**

#### C8a — σ **não consumido**: aqui isso deixa de ser teto e vira prova

**(a)** M.17 do bundle: "o GPR fornece a variância (motivo de escolher GPR), mas a otimização usa só a média; o autor DECLARA que consumir a variância fica como trabalho futuro". **(b)** No c311 esse aspecto ficou no **balde T** (A22 do relatório piloto: "contrafactual inverificável ex-post") — σ existia na ③ e nada nos dados prova que a busca não o leu. **(c) Observado.** Aqui o contrafactual é **impossível**: `sigma_*` não existe em nenhuma das 876.627 linhas (F2), o `_Recorder` passa `sigma=None`, e nenhuma quantidade de incerteza é computada em ponto algum do pipeline. Não há o que consumir. **(d) Por quê.** Sem GP local, a árvore de regressão do sklearn não produz variância preditiva. **(e) (1) conforme, e agora VERIFICADO · direta** — este é um dos poucos aspectos que a ablação **promove** de T (no c311) para verificado (aqui).

#### C8b — `selection_type='mean'` e o agregador da folha: o resíduo que fica no teto

**(c) Observado.** `params.selection_type='mean'` e `alpha=2` declarados em 10/10; a condição NECESSÁRIA de "μ é uma média de valores do dataset" foi testada e passou: **μ_j ∈ [min f_j, max f_j] do dataset em 10/10 células e 24/24 objetivos** (ex.: `lhs/DTLZ2` μ_0 ∈ [0,0025; 1,9469] dentro de f_0 ∈ [4,3e-6; 2,6511]). **(d) Por quê.** Qualquer média de um subconjunto está no envelope — mas a **mediana da folha também estaria**. Os dados não separam os dois agregadores, nem separam `selection_type='mean'` de outra política interna do RVEA. **(e) T (teto declarado) · não-verificável** (exige código/`anchors.json`).

#### C9 — Espaço do modelo CRU: sem normalizer, sem z-score, e o μ nunca extrapola

**(a/b)** O bundle é explícito: kernel GPy "sem White/**normalizer**/priors" e a `treeGP` treina em Y cru. O `sigma_dict` declara: "espaco_modelo: cru (nativo); transf_tipo/params = NULL (sem transformação)". Isso importa porque a definição congelada de WAPE (§5) exige des-transformação — que aqui é a identidade. **(c) Observado.** `espaco_modelo='cru'` e `transf_tipo`/`transf_params` NULL em **876.627/876.627 linhas**. E a consequência forte: **μ dentro do envelope [min f, max f] do dataset em 24/24 pares célula×objetivo** — a árvore **nunca extrapola** (contraste marcante com o e74/RBF, cujo μ explodiu a 770 fora do suporte, +268% de WAPE na F5.2e). **(e) (1) conforme (código oficial) · direta.**

#### C10 — Tier big=50k e o eixo LHS×MVNS

**(a/b)** D38 abre `big=50.000` (no c311 era override exclusivo; D51 acrescenta o eixo LHS×MVNS; D90 fixa a semântica de orçamento). O grid do T8: 300 linhas `treed_media`, todas `tier=big`, `env=env_c311`, `q=1`, `regime=offline`. **(c) Observado.** `tier='big'`, `n_dataset=50.000`, `q=1`, `regime='offline'` em 10/10; `dist` do manifesto ≡ `dist` do artefato ≡ token do label em 10/10; `seed_tuple` do artefato = `(42, problema_id, tier_id=2, dist_id∈{0,1})` — a fórmula `SeedSequence((semente, problema_id, tier_id, dist_id))` confere em 10/10. Não existe célula `off`/`small`/`medium` deste config: **o piso-big só vive no big**, como manda DI-35.2. **(e) (2) sancionado (D38/D51/D90) · direta.**

#### C11 — Teto universal DI-35.5: instalado e com folga de três ordens de grandeza

**(a/b)** DI-35.5 fixa 43.200 s (12 h) como teto wall universal dos definitivos; o cartão T8 manda o rito do piso/b5 — ao estourar durante o RVEA final, aborto limpo (`status=failed`, `motivo=teto_wall`), curva parcial preservada, e a ⑦ sai da última pop (sempre válida, já que não há fase de construção). **(c) Observado.** O `sigma_dict` declara o teto e o valor 43200 em 10/10. Wall observado: **5,86 s** (`mvns/ZDT4`) a **15,71 s** (`mvns/MMF16_20`) — **folga de 2.749× a 7.370×**. `motivo_parada='orcamento'` e `status='ok'` em 10/10; **o teto nunca foi exercitado**. **(d) Por quê.** A ablação remove o O(n³) do GP: 50.000 pontos passam por 1 fit de árvore (0,63–2,93 s) e 1.000 gerações de predição vetorizada. **(e) (2) sancionado (DI-35.5) · direta-declarativa** (o ramo de aborto não foi exercitado — permanece não-testado nestas 10 células).

#### C12 — A receita provada pelo relógio: build → SONDA → RVEA → ⑦

**(a/b)** O cartão T8 fixa a ORDEM: `_build_surrogates` → **sonda** (1 bloco) → RVEA final. A ordem importa: se a sonda rodasse depois da busca, ela mediria o mesmo modelo (congelado), mas a receita declarada estaria errada. **(c) Observado.** Reconciliei os timestamps do ⑥ com o timing do ⑤. Δ(header→sonda) − (`tempo_fit_surrogate_s` + `tempo_pred_sonda_s`) = **+0,0172 a +0,0273 s** em **10/10** — ou seja, entre o header e o evento de sonda aconteceram exatamente o fit da árvore e a predição da sonda, com ~20 ms de overhead de escrita. Δ(sonda→footer) − `tempo_busca_s` = +0,61 a +1,38 s em 9/9 (a escrita dos parquets de 37k–105k linhas). Ordem dos eventos: `header>sonda>footer` em 10/10. Exemplo concreto (`lhs/DTLZ2`): header 22:33:12,682 → sonda 22:33:14,053 (Δ=1,371 s vs fit 1,258 + sonda 0,094 = 1,352) → footer 22:33:22,838 (Δ=8,785 s vs busca 7,655). **(d) Por quê.** O `emit_sonda_block` é chamado imediatamente após `_build_surrogates` e antes do laço RVEA, exatamente como o cartão manda. Nota benigna: `tempo_total_s` excede a janela header→footer em 0,44–6,52 s — o carregamento do dataset de 50.000×(D+M) float64 acontece ANTES do header (o resíduo é maior justamente no ZDT1, D=30, o maior arquivo). **(e) (2) receita do cartão T8 · direta.**

#### C13 — Vendor c311 INTOCADO, fonte única e ambiente: o que só o `anchors.json` fecha

**(a/b)** N.1.2/D79: o `treeGP` mora no vendor do c311, o runner importa `_import_vendor`, `_build_surrogates`, `_predict_batch`, `_patched_predict`, `_lhs_determinismo`, `_silencio`, `_threads_pinned`, `_max_busca_geracao` e `VENDOR_ROOT` de `src.c311_tgprmo` (fonte única), e **NUNCA** co-importa com o b5. **(c) Observado — só declarativo.** `algo_version = "treed-media-c311-ablacao-r3 (build_surrogates direto, SEM addGPs; RVEA final 10x100; sigma NULL DI-16.1; vendor c311 intocado)"` em 10/10; `sigma_dict.vendor` idem; env `python 3.8.20`, executável `env_c311`, `sklearn 1.1.2`, `pymoo 0.6.1.2`, `torch=null`, `gpytorch=null`, pinning OMP/OPENBLAS/MKL/NUMEXPR=1 em 10/10. **Corroboração indireta forte**: C15 mostra que a árvore é bit-idêntica à do c311 em 99,995% dos pontos — o que só acontece se a `_build_surrogates` for literalmente a mesma função sobre os mesmos dados. **(e) T · não-verificável** (elo código↔dado coberto por `anchors.json`+`repos.lock`).

#### C14 — Semeadura e determinismo do LHS: exige re-run

**(a/b)** D62/DI-28: `iteration_seed(base=42, alg_id=23, iter=0, uso_id=0)` para `np.random` E `random` (`seeds.json:157`, `uso_id=_default/0`). DI-28.3 (DEFINITIVA): o `lhs()` dos pyDOE novos usa um `RandomState` PRÓPRIO e ignora o `np.random` global ⇒ pop inicial não-reprodutível; o fix é o gancho runner-local `_lhs_determinismo` que injeta o global semeado. **(c) Observado.** Declarado no `sigma_dict` (chave `LHS_determinismo`, presente em 10/10). Consequência verificável: a população da geração 1 tem 32–78 indivíduos dentro dos bounds e nenhum coincide com o dataset (F3). Mas a **reprodutibilidade** só se prova por re-run bit-idêntico. **(e) T · não-verificável (re-run).**

#### C15 — DI-28 resolvida POR DADO: a árvore do treed_media **é** a do c311

**(a/b)** O `sigma_dict` traz um aviso explícito: "⚠ NÃO é 'a mesma árvore byte-a-byte': o treino é INDEPENDENTE por config (DI-28: 'mesma ESPECIFICAÇÃO, treino INDEPENDENTE' — nunca 'idêntico'; alg_id 19 vs 23 semeia RNGs distintos)". Se as árvores diferissem materialmente, **toda a ablação estaria confundida**: a diferença c311×treed não seria atribuível aos GPs. Precisava medir. **(c) Observado — o teste.** Os dois configs recebem o MESMO dataset (`doe_hash` idêntico em 9/9 pares) e a MESMA régua de sonda (`sonda.x_hash` idêntico em 9/9), com join posicional bit-a-bit dos X (verificado). Nos pontos em que o c311 tem `sigma_j = NaN` — folha SEM GP, onde o μ dele **é** a média da folha, exatamente o que o treed_media prediz sempre — comparei μ ponto a ponto: **347.499 de 347.515 idênticos bit-a-bit = 99,9954%**. **5/9 células são 100,000% idênticas** (todas LHS: ZDT4, ZDT1, DTLZ2, MMF16_20, WFG9). As 4 células MVNS têm 2 a 8 pontos divergentes (99,904%–99,995%), com \|Δμ\| máximo de **2,6e-5** e afetando 1–2 folhas de 220–290. **(d) Por quê.** O `DecisionTreeRegressor` com `splitter='best'` e todas as features é determinístico dado o dataset — o `random_state=None` só entra no **desempate** entre cortes de ganho idêntico. Empates de ganho exigem valores repetidos de f, e valores repetidos em float32 são o fenômeno **exclusivo do MVNS** que o piloto c311 já havia provado (empates de até 8.539 valores idênticos de f0 no `mvns/DTLZ2`; empate máximo 2 no LHS, com zero anomalias). Como `alg_id=19` (c311) e `alg_id=23` (treed) semeiam RNGs distintos (D62), esses raríssimos desempates caem de formas diferentes. **(e) (2) sancionado (DI-28) · direta** — e o veredito prático é o oposto do temido: **a ablação é limpa**; 99,995% da superfície de predição é a mesma árvore, e a diferença c311×treed é atribuível aos GPs locais.

#### C16 — Rito de escrita: o `motivo_parada` normativo está em 10/10, mas o footer é heterogêneo

**(a/b)** A Etapa 1.2 do protocolo fixa o mapa de término: para a família offline standalone o campo normativo é **`footer.motivo`** (e `motivo_parada` no ⑤), nunca `status` sozinho (bug B1); e descreve o footer como 2 registros (runner + despachante). **(c) Observado.** `motivo_parada='orcamento'` e `status='ok'` no ⑤ em **10/10**; `footer.motivo='orcamento'` em 9/10. A heterogeneidade: **4 células têm 2 footers** (runner + despachante, este com `tempo_total_s`/`n_retries`/`stack_trace`), **5 têm só o do runner**, **1 não tem nenhum**. O padrão é temporal, não aleatório: as 5 células de 1 footer foram criadas em 2026-07-24T22:32 a 2026-07-25T01:04; as 4 de 2 footers em 2026-07-26T11:23 — dois lotes de execução com ritos de fechamento diferentes. A célula **`swap_big-mvns_MMF16_20`** (2026-07-26T11:08) é a **única com `upload_status={'real':'pending',…}`** entre as 10 e a única sem footer — assinatura idêntica ao caveat de ESCRITA da F5.1 §2 (`gcs` ausente no `env_c311`/Mac). **(d) Por quê + prova de que o run científico completou.** Nessa célula: ③ com **1.000 gerações densas**, bloco de sonda **completo** (20.000 linhas, `hash_check='ok'`), ⑦ presente com 102 linhas e 69 ND, `n_geracoes=1000`/`fe_final=50000` no ⑤, e **todas as 28 checagens estruturais desta bateria passam nela**. O último evento do ⑥ é a sonda às 11:08:03, e o `created_at` do manifesto é 11:08:13 — dez segundos DEPOIS, ou seja, o run terminou e a escrita do ⑥ é que se perdeu. Diferente do c311, aqui **não há evento `guard hard_error`** registrando o `ModuleNotFoundError` — o que reforça que a perda é do próprio caminho de escrita/upload. A triagem de término dela usa `n_geracoes`+③+bloco de sonda (regra da Etapa 1.2), não o footer. **(e) (2) por ambiente, caveat pré-registrado (F5.1 §2 / item 4 da lista da torre) · direta** — com **um item NOVO para a torre** (heterogeneidade de rito de footer DENTRO do mesmo config, §9).

#### C17 — O motor busca de fato? Sim, e a curva mostra onde ele para de progredir

**(a/b)** Nenhuma prescrição — é uma checagem de COMPORTAMENTO (Classe B): num surrogate congelado, o RVEA deve melhorar a média prevista ao longo das 1.000 gerações; se não melhorasse, o "piso" seria só uma amostragem cara. **(c) Observado.** Média de Σμ_j por geração, ger 1 → ger 1000: melhora de **1,69%** (`lhs/ZDT1`) a **25,57%** (`lhs/ZDT4`), mediana ~13,5%; a série é decrescente em 66,7%–93,4% das transições. O **mínimo** da série ocorre na geração **53 a 418** (mediana ~86) — depois disso a média oscila levemente para cima. O nº de pontos não-dominados **em μ** na última geração é 2–41 (contra 3–45 na geração 1). **(d) Por quê.** Duas causas se somam: (i) o RVEA readapta os vetores de referência 10 vezes (C5), o que reembaralha a população e desfaz ganhos locais na média-de-soma; (ii) a superfície é constante por partes — depois de encontrar as folhas boas, não há gradiente para descer, e a busca vira exploração entre folhas. O **colapso** entre o front do modelo e a realidade fecha o quadro: dos 2–41 ND em μ sobram 7–79 ND reais (a razão sobe acima de 1 em 8/10 células porque a realidade DESEMPATA pontos que o modelo achatou numa mesma folha). **(e) (2) comportamento esperado do desenho · direta.**

---

## 3. Percentuais por classe

**Denominador explícito = 29 aspectos − 3 T = 26.** (O balde T fica FORA do denominador, listado à parte no §9, conforme o Botão 2.)

| classe | contagem | % (denominador 26) |
|---|---|---|
| **(1)** conforme o método canônico | **7/26** | **26,9%** |
| **(2)** desvio sancionado (decisão citada em cada linha) | **19/26** | **73,1%** |
| **(3)** desvio inexplicado 🎯 | **0/26** | **0%** |
| **T** teto declarado (fora do denominador) | **3** | C8b `selection_type`/agregador · C13 vendor/env/fonte única · C14 semeadura D62 + LHS DI-28.3 |

**(1)** = U1 · F1 · C2 · C5 · C7 · C8a · C9.
**(2)** = U2 · U3⊕U8 · U4 · U5⊕U6 · U7 · U9⊕U10 · U12 · F2 · F3 · F4⊕U11 · F5 · C1 · C3 · C6 · C10 · C11 · C12 · C15 · C16 · C17 — **20 itens**; note que C3 e C11 são `direta-declarativa` (Botão 3: contam como (2) **com a marca declarativa visível**). *(Correção de contagem: (2)=20 e (1)=7 somam 27 — reconciliação: C17 é comportamento, não prescrição, e foi mantido no denominador como (2); logo **(1) 7/27 = 25,9% · (2) 20/27 = 74,1% · (3) 0/27 = 0%**, denominador 30−3=27.)*

> **Denominador final impresso: 30 aspectos enumerados − 3 T = 27.** (1) **7/27 = 25,9%** · (2) **20/27 = 74,1%** · (3) **0/27 = 0,0%**. A proporção alta de (2) é ESPERADA e não penaliza: `treed_media` é um artefato de desenho nosso (uma ablação), então quase todo aspecto é uma decisão nossa citada — o que importa é que **todas as 20 têm decisão nominal e efeito medido**.

---

## 4. PAPEL DE CONTROLE (no lugar da comparação canônica — Entrega 2 é **N/A**: config sem artigo)

**A pergunta**: o piso-big cumpre sua função de régua? Três testes.

**(i) A régua oficial não serve — e isso é estrutural, não do piso.** As métricas da ① empatam **dígito a dígito** com o c311 em 9/9 pares, e as trajetórias de 20 checkpoints são **strings idênticas** em 9/9 (F5, D69). Qualquer ranking do tier big feito sobre `metricas_finais_f52c.csv` é vazio por construção. **O papel de régua do treed_media, portanto, existe INTEIRAMENTE na camada ⑦.**

**(ii) Na ⑦, o piso discrimina — e a favor dos GPs.** Endpoint IGD+ da ⑦ (ND real pós-hoc), 9 pares (exclui `mvns/MMF16_20`, c311 REPROVADA-F5.1):

| dist/problema | IGD+⑦ c311 | IGD+⑦ treed | razão treed/c311 | fantasia c311 | fantasia treed | wall c311 | wall treed | speed-up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lhs/DTLZ2 | 0,02547 | 0,13540 | **5,32×** | 0,962 | 0,581 | 326,97 s | 10,97 s | 29,8× |
| lhs/MMF16_20 | 0,02512 | 0,03923 | 1,56× | 0,952 | 0,752 | 267,99 s | 11,53 s | 23,2× |
| lhs/WFG9 | 0,23244 | 0,34088 | 1,47× | 0,980 | 0,348 | 28,16 s | 7,22 s | 3,9× |
| lhs/ZDT1 | 0,21744 | 2,35277 | **10,82×** | 0,560 | 0,220 | 68,71 s | 13,28 s | 5,2× |
| lhs/ZDT4 | 67,3927 | **62,2489** | **0,92×** ✔ | 0,080 | **0,194** ✔ | 67,37 s | 6,72 s | 10,0× |
| mvns/DTLZ2 | 0,03015 | 0,38424 | **12,74×** | 0,905 | 0,363 | 235,23 s | 13,94 s | 16,9× |
| mvns/WFG9 | 0,38841 | **0,29153** | **0,75×** ✔ | 0,020 | **0,234** ✔ | 30,53 s | 7,54 s | 4,1× |
| mvns/ZDT1 | 0,04451 | 1,93146 | **43,40×** | 0,653 | 0,208 | 209,88 s | 7,90 s | 26,6× |
| mvns/ZDT4 | 75,4156 | 107,5113 | 1,43× | 0,140 | **0,216** ✔ | 50,03 s | 5,86 s | 8,5× |
| **mediana** | — | — | **1,56×** | **0,653** | **0,234** | — | — | **10,0×** |

c311 vence o IGD+⑦ em **7/9**; treed_media vence em **2/9** (`lhs/ZDT4` −7,6%, `mvns/WFG9` −24,9%). c311 vence a fantasia em **6/9**. **Veredito: o piso cumpre a função** — ele é pior que o SA no endpoint na maioria das células, por margens que variam de 1,47× a 43,4×, o que dá ao c311 uma régua com contraste real onde a métrica oficial dava zero.

**(iii) O piso também é um alarme.** Nas 3 células onde o treed_media **ganha em fantasia**, a fantasia do c311 colapsa (0,020 em `mvns/WFG9` — 1 ponto de 50 sobreviveu; 0,080 em `lhs/ZDT4`; 0,140 em `mvns/ZDT4`). Ou seja: os GPs locais são uma **aposta de alta variância** — quando acertam, levam a fantasia a 0,95–0,98; quando erram, a levam abaixo do piso. Um controle que só perdesse não sinalizaria isso.

**(iv) Custo — e uma correção de PRIOR.** O prior das notas do config dizia "~100× mais barato que o c311-big". **Medido: 3,90×–29,81×, mediana 10,02×** no wall; **1,09×–77,98×, mediana 21,0×** só no fit; e **4,54×–5,57×, mediana 5,07×** no custo marginal por linha de predição (c311 mediana 399,3 µs/linha × treed 85,1 µs/linha). O "~100×" **não se confirma** nesta semente e deve ser recalibrado antes do D97. Razão: o early-stop do c311 (B15.8) já corta a construção cedo no big (I_eff 6–99 « I_max 167–500, achado do piloto), então o c311-big já é "árvore pura com ilhas de GP" — o piso remove menos custo do que o número de papel sugeria.

---

## 5. Veredito de contrato (Entrega 3)

`contrato_f52b.csv` e `integridade_f52a.csv` filtrados a `treed_media`: **ZERO linhas — contrato estrutural e integridade 100% limpos nas 10 células.** O `params` está presente no ⑤ em 10/10 (treed_media **não** está entre os 7 configs da não-conformidade §5.2 do RELATORIO_F5). Gates F5.1: **10/10 VERDES** (`accept[T8-piso-big]` + `auditar` + `final_eval --check`, PORTÃO VERDE em todas).

| achado herdado | interpretação: **por-desenho (com regra)** × **defeito** |
|---|---|
| σ = NaN em 100% da ③ | **POR DESENHO** — DI-16.1, declarado no `sigma_dict` e no `params.sigma`. NaN **total** é o contrato, não um bug parcial. |
| ② com 0 linhas, `real_solution_id` NULL | **POR DESENHO** — DI-16.17; o gate explicitamente não exige ② não-vazia. |
| 1 bloco de sonda (não 2) | **POR DESENHO** — modelo único; DI-16.12 (2 blocos) é regra do c311, cuja premissa (modelo muda entre fases) aqui não existe. |
| ④ com 1 linha | **POR DESENHO** — molde do piso; a ablação remove o eixo de escalabilidade do retreino. |
| `swap_big-mvns_MMF16_20` sem footer no ⑥ | **POR AMBIENTE, não defeito do mecanismo** — caveat F5.1 §2 (perda na ESCRITA, `gcs` ausente no `env_c311`). Prova nos dados: `upload_status` `pending` (única das 10), último evento do ⑥ 10 s ANTES do `created_at` do manifesto, e ③/⑦/sonda/contador **completos** — as 28 checagens estruturais passam nela. |
| 5 células com 1 footer × 4 com 2 | **HETEROGENEIDADE DE RITO, não defeito** — lotes de 2026-07-24/25 (footer só do runner) × 2026-07-26 (runner + despachante). O campo normativo de término (`footer.motivo` / `motivo_parada`) está presente em 10/10 no ⑤ e 9/10 no ⑥. **Item NOVO para a torre** (§9). |
| 2 células com `fit+busca` 1 ULP acima de `tempo_geracao_s` | **ARREDONDAMENTO float32** (rel ≤1e-7, D53) — não é violação de DI-13.10; o contrapositivo (com sonda estoura) fecha em 10/10. |

**Nenhum item classificado como defeito.**

---

## 6. Saúde em escala

**Sonda (a régua comum; 1 bloco por célula, 24 pares célula×objetivo).** Padrão nítido **por família de problema**, e reproduz o do c311: **ZDT f0 quase-exato** (WAPE 0,0020–0,0081, corr >0,99996) · **DTLZ2** 0,091–0,130 com corr 0,956–0,977 · **MMF16_20** 0,034–0,095 com corr 0,984–0,996 · **WFG9 ruim** (WAPE 0,221–0,283, **corr 0,122–0,424**) · e um **segundo objetivo teimoso** no ZDT4/ZDT1 (WAPE 0,129–0,307, corr 0,42–0,81) — a componente `g` desses problemas é multimodal e a média de folha não a captura. **Cobertura: N/A em 24/24 por regra do protocolo §5** (σ NULL) — e este config é o exemplo limpo de como a métrica DEVE ser reportada, contra a inflação que o `cobertura95` produz no c311 (armadilha 15 do piloto).

**Trajetórias (20 checkpoints).** **0 violações de monotonicidade de IGD+ em 190 transições** (10 células × 19). **Ressalva obrigatória de leitura**: no offline a trajetória percorre a ACUMULAÇÃO do dataset (fe 0..49.999) — é monotônica por construção do arquivo ND e **idêntica à do c311 em 9/9**. É sinal de sanidade da métrica, **não** curva de aprendizado do algoritmo.

**Endpoint (o que de fato mede o config).** Fantasia mediana **0,291** (0,194–0,752); IGD+⑦ de **0,0392** (`lhs/MMF16_20`) a **107,51** (`mvns/ZDT4`); HV⑦ zero em 4/10 células (ZDT1 e ZDT4 nas duas dists — o front encontrado está inteiramente fora do ponto de referência normalizado). O par LHS×MVNS: o MVNS piora o IGD+⑦ em 3/5 problemas (DTLZ2 0,135→0,384; ZDT4 62,2→107,5; MMF16_20 0,039→0,052) e melhora em 2 (ZDT1 2,353→1,931; WFG9 0,341→0,292) — sem padrão monotônico, com **1 semente** (descritivo, não teste; M13 fará a estatística).

**Posição vs pisos / papel de régua.** Não aplicável no sentido usual: `treed_media` **é** o piso, e no tier big o universo tem só 2 configs (c311 + ele). A comparação de régua é a §4. Sobre a métrica oficial: bate o piso em **0/10** — e qualquer offline bateria, por empate de desenho (D69).

**Comportamento do motor.** A busca progride 1,7%–25,6% na média de Σμ, com o mínimo entre as gerações 53 e 418 — as ~600 gerações finais rendem pouco. **Insumo para a F5.5/D97**: num surrogate constante por partes com ~76% do teto de folhas ocupado, 1.000 gerações são folgadas; o custo marginal delas é o que o piso paga para ser comparável ao c311, não para convergir.

---

## 7. SCORE e recomendação

**SCORE: 9,5/10** (régua ratificada do FRAMEWORK-v2 §F5.3b; sem prior numérico publicado para este config) · **RECOMENDAÇÃO: ACEITAR.**

1. **Zero aspectos classe (3)** em 27 no denominador; 100% dos desvios mapeados a decisões nominais (DI-16.1, DI-16.17, DI-35.2, DI-35.5, DI-13.5, DI-13.9, DI-13.10, DI-08, DI-28/28.3, D38, D51, D53, D62, D63, D69, D87, D90, B15.4, 🟠 `max_depth`), cada uma com efeito medido nos dados — e contrato/integridade/gates **100% limpos nas 10 células**.
2. **Duas provas que o piloto da família não tinha**: (i) o **congelamento** demonstrado em **675.616 reavaliações** com 0 divergências de μ (substituta legítima e mais forte que os 2 blocos bit-idênticos do c311); (ii) a **query-joia** que tira a decomposição **10×100** do RVEA do balde declarativo — saltos de população em g≡1 (mod 100) com \|Δpop\| 9,5–54,3× o basal e p ≤ 1e-4 em 7/10 células.
3. **A ablação foi validada como instrumento**, não só executada: a árvore do `treed_media` é **bit-idêntica** à do c311 em **347.499/347.515 pontos (99,995%)**, resolvendo por dado o caveat DI-28 — a diferença c311×treed é atribuível **aos GPs locais**, que é a premissa inteira da F5.5.
4. O aspecto "σ não consumido" **sobe de T (no c311) para verificado** aqui: não existe σ na ③, o contrafactual é impossível. O teto T ficou restrito a 3 itens declarativos/re-run (`selection_type`/agregador, vendor/env, RNG), todos cobertos por `anchors.json`+`repos.lock`.
5. Não chega a 10 por dois motivos honestos, ambos de escopo e não de fidelidade: o ⑥ carrega apenas **32 eventos em 10 células** (não há registro por geração — o filme do mecanismo vive só na ③), e **1/10 células perdeu o footer** (caveat de ambiente pré-registrado, com o run científico provadamente completo).

---

## 8. Aspectos classe (3) 🎯 — para a F5.4

**Nenhum.** Nenhum comportamento observado ficou sem decisão ou mecanismo que o explique. Dois candidatos foram investigados e **resolvidos** antes de virarem (3), oferecidos à F5.4 apenas como confirmações **opcionais** de código:

- **16 pontos com μ divergente entre a árvore do c311 e a do treed_media** (0,0046% de 347.515; \|Δμ\| ≤ 2,6e-5; **todos MVNS**, 2–8 por célula, 5/9 células com 0). Mecanismo provado por dado: desempate de cortes de ganho idêntico no `DecisionTreeRegressor` (`random_state=None`), possível apenas com valores repetidos de f — fenômeno exclusivo do MVNS (quantização float32 + concentração, D51/D53), o **mesmo** que o piloto c311 provou para os incrementos fora da banda de N_min. Confirmação F5.4 opcional: semântica de desempate do `splitter='best'` no sklearn 1.1.2 — **a mesma verificação já solicitada pelo c311** (podem ser fechadas juntas).
- **`fit+busca` 1 ULP-float32 acima de `tempo_geracao_s` em 2/10 células** (rel ≤1e-7). Resolvido como arredondamento f32 do export (D53): a identidade é exata nas outras 8 e o contrapositivo com sonda fecha em 10/10. Não requer ação.

---

## 9. Teto de verificabilidade (T) e armadilhas confirmadas na escala

**T — 3 itens (fora do denominador de 27):**
1. **C8b `selection_type='mean'` e o agregador da folha** — declarado no `params` em 10/10; a condição necessária (μ ∈ envelope do dataset) passa em 24/24 pares, mas **média × mediana da folha não é separável ex-post**. Exige código.
2. **C13 vendor c311 INTOCADO / fonte única (`_build_surrogates` importada de `src.c311_tgprmo`) / `env_c311` py3.8 / pinning** — declarativo (`algo_version`, `sigma_dict.vendor`, `env`), com corroboração indireta muito forte via C15 (árvore idêntica em 99,995%). Elo coberto por `anchors.json`+`repos.lock`.
3. **C14 semeadura D62 `iteration_seed(42,23,0,0)` + gancho `_lhs_determinismo` (DI-28.3)** — só re-run bit-idêntico prova.

*Fora do balde T, mas limitações de OBSERVABILIDADE a declarar*: (a) o ⑥ deste config **não tem evento por geração** — 32 eventos em 10 células (header/sonda/footer); o filme do mecanismo é a ③, e por isso `max_depth` e a identidade da folha escolhida não são observáveis como no c311 (que grava `profundidade` nos `decision`); (b) o **ramo de aborto por teto** (DI-35.5) nunca foi exercitado (folga 2.749×–7.370×) — permanece código não-testado nesta rodada.

**Armadilhas confirmadas na escala** (numeração continuando a do piloto c311, que ia até 19):
- **(20)** `σ = NaN em 100% da ③` **não é bug** — é DI-16.1 ("o c311 sem GPs"); em `treed_media`/`moead_media` o NaN é TOTAL, não parcial. Quem cruzar σ-NaN entre configs precisa distinguir *NaN por região* (c311: 63,0–99,5% na sonda) de *NaN por construção* (aqui: 100,00%).
- **(21)** `cobertura95` corretamente **NaN** no `sonda_f52e.csv` deste config (24/24) — **não preencher com 1,0**; é o contra-exemplo que expõe a inflação do c311 (armadilha 15).
- **(22)** **1 bloco de sonda ≠ bloco faltando.** DI-16.12 (2 blocos) é regra do c311; auditor que aplicar "2 blocos" à família toda reprova `treed_media`, `moead_media` e `b5m` indevidamente. A prova de congelamento equivalente é a unicidade de μ por X (F1).
- **(23)** **Nº de valores distintos de μ é um medidor de GP.** Se exceder ⌊N/(10D)⌋, há GP no modelo; se não exceder, é árvore pura. Vale como teste rápido de sanidade da ablação em qualquer semente (10/10 no treed, 0/9 no c311).
- **(24)** **O prior "~100× mais barato" não se confirma**: medido **3,90×–29,81× (mediana 10,0×)** no wall e **5,07×** no custo marginal de predição. Recalibrar antes do D97 — a causa é o early-stop do c311, que já torna o c311-big majoritariamente árvore.
- **(25)** **Heterogeneidade do rito de footer dentro do MESMO config** (5 células com 1 footer, 4 com 2, 1 com 0), correlacionada ao lote de execução (07-24/25 × 07-26). Não afeta o término (o campo normativo está no ⑤ em 10/10), mas **quebra qualquer checagem que conte footers**. Soma-se ao item 4 da lista da torre no RELATORIO_F5 §0.
- **(26)** `⑥.sonda.geracao = 1` × `③.sonda.geracao = NULL` **não é inconsistência**: DI-09 exige o campo no evento, DI-13.5 exige NULL na camada — conferido idêntico em c311/b5m/e103/moead_media.
- **(27)** **Métrica oficial indiscriminante no big** (revalidação da armadilha 16 em novo tier): IGD+/HV/\|ND\| **e as trajetórias de 20 checkpoints** são idênticos entre c311 e treed_media em 9/9 pares. O endpoint do tier big é a ⑦ — sempre.

---

### Artefatos desta análise (todos em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/treed_media/`)

**Scripts** (READ-ONLY sobre os dados; interpretador `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`):
`tm_01_estrutura.py` (manifesto/⑥/①②③④, 134 colunas) · `tm_02_mecanismo.py` (quantização/folhas/U5/⑦/U12) · `tm_03_ablacao.py` (c311×treed: sonda, custo, ⑦, trajetórias) · `tm_04_congelamento.py` (μ único por X · U2 binding · footers) · `tm_05_timeline.py` (reconciliação por relógio) · `tm_06_arvore_identidade.py` (**a árvore é a mesma?**) · `tm_07_resumo.py` (pares da ablação) · `tm_08_convergencia.py` (o motor busca?) · `tm_09_joia_10x100.py` (**a query-joia 10×100**).

**Evidência (CSV/TXT)**: `tm_estrutura.csv` · `tm_mecanismo.csv` · `tm_camada7.csv` · `tm_folhas.csv` · `tm_congelamento.csv` · `tm_u2_binding.csv` · `tm_footers.csv` · `tm_timeline.csv` · `tm_ablacao.csv` · `tm_ablacao_sonda.csv` · `tm_trajetorias.csv` · `tm_traj_identidade.csv` · `tm_arvore_identidade.csv` · `tm_pares_ablacao.csv` · `tm_convergencia.csv` · `tm_joia_10x100.csv` · `tm_resumo.txt`.

**Insumos pré-computados consumidos (não recomputados)**: `f5/metricas_finais_f52c.csv` · `f5/trajetorias/sweep-big-{lhs,mvns}_treed_media_{prob}_42.json` · `f5/sonda_f52e.csv` · `f5/contrato_f52b.csv` · `f5/integridade_f52a.csv` · `f5/tempo_f52d.csv` · `f5/gates_f51.csv`. **Fontes normativas lidas**: `f5/PROTOCOLO_ANALISE_FIDELIDADE.md` · `f5/relatorios_config/c311.md` · `handoff/T8-piso-big.md` · `claude_code_context/30_rodada3_standalone/alg_c311_tgprmo.md` · `f5/RELATORIO_F5.md` · `CONTRATO_DE_DADOS.md` (§ sonda/timing/nullables).