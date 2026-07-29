# RELATÓRIO DE FIDELIDADE — nsga3 · NSGA-III (piso online) · F5.3b · 25 células main · semente 42

**Analista de fidelidade nsga3 · 2026-07-29 · protocolo v1.1 congelado · dados READ-ONLY em `resultados_experimentos/nsga3/{problema}/42/` · controle SEM artigo (gabarito = espec canônica do bundle `alg_pisos_online.md` + REGISTRO)**

---

## 1. Ficha do mecanismo

**NSGA-III puro (Deb & Jain, TEVC 2014), built-in do PlatEMO 4.15, `algo_version = piso-NSGAIII-PlatEMO4.15`, ZERO patches por desenho.** É um dos **4 pisos ONLINE** — a *régua* do estudo, cuja função (§3.2) é responder à pergunta que os SA-MOEA não respondem entre si: *"o surrogate compra alguma coisa, afinal?"*. Casamento por princípio de seleção: **NSGA-III → referência/indicador → espelha o e7 (EA-Indicador)** — mesmo motor evolutivo, mesmo DoE, mesmo orçamento, sem surrogate.

Mecânica: lattice de vetores de referência das-Dennis por `UniformPoint(N,M)` (1× por run, **fixo** — é o NSGA-III stock, não o A-NSGA-III adaptativo); seleção ambiental por associação a nicho de vetor + normalização por pontos extremos; operadores stock do Balde C (SBX `proC=1, dis_c=20` + PM `proM=1, dis_m=20`). Protocolo Knowles/ParEGO: **`N = 20` CRAVADO (2026-07-18)** e declarado **PROVISÓRIO até o SUB-varN (DI-39)**; orçamento `maxFE = 31D−1` com hard-stop (D21/D61); DoE `11D−1` do artefato (D63), com a população inicial semeada pelos **N melhores por NDSort + CrowdingDistance (D88)**; duplicata bit-exata **não gasta FE, gasta o slot do infill (D89)**.

**A idiossincrasia que governa metade do grid (DI-18/§6.3):** `UniformPoint(20,3)` arredonda o lattice para baixo → **H=4 → 15 vetores** ⇒ em **M=3 o NSGA-III roda com `N efetivo = 15`**, não 20 (NSGA-II e SMS-EMOA, que não usam vetores, mantêm 20). O `N=20` **não é uniforme entre os 4 pisos**. Camadas: ③ vazia por desenho, sem sonda, sem `sigma_dict`, `fit_series` vazia, ⑥ com registro `pisos` (`decomposicao` + `seeding`).

**Escala auditada:** 25 células · **413 gerações** · **7.200 descendentes** · **10.856 linhas na ①** · **7.620 linhas na ②** · **675 guards** · 25 hard-stops. Todas as 25 células na `vm3` (roster homogêneo).

---

## 2. DISSECAÇÃO DOS ASPECTOS (o CORE)

Verificabilidade: **D**=direta · **DD**=direta-declarativa (config-echo) · **I**=indireta · **NV**=não-verificável. Classe: **(1)** conforme o método canônico · **(2)** desvio sancionado · **(3)** inexplicado 🎯 · **T** teto.

### 2.1 Tabela-resumo (24 aspectos, 1 linha cada)

| # | aspecto | classe | verif. | resultado-síntese (25 células) |
|---|---|---|---|---|
| A1 | Orçamento FE = 31D−1 + hard-stop exato | (2) D21/D61 | D | 25/25 `maxfe=fe_final=|①|=31D−1`; guard `hard_stop` em `fe==maxfe` 25/25 |
| A2 | DoE init 11D−1 bit-a-bit do artefato (ordem preservada) | (2) D63/D88 | D | **25/25 `max|ΔX| = 0,0`**; `doe_hash` sidecar ≡ manifesto 25/25 |
| A3 | `N = 20` CRAVADO (Knowles/ParEGO), PROVISÓRIO até SUB-varN | (2) §3.2/D65/DI-39 | DD | `N_nominal=20` em manifesto+header+footer, 25/25 |
| A4 | **`N efetivo = 15` em M=3** (lattice) | (2) DI-18/§6.3 | D | `|pop|=15` em 6 células M=3 e `20` em 19 células M=2 — **413/413 gerações** |
| A5 | **Lattice `UniformPoint(N,M)` NBI ≡ PlatEMO** | (1) | **D — joia** | **25/25 `max|ΔW| = 0,0` na ORDEM logada**; H₁=4 (M=3) / 19 (M=2) |
| A6 | Vetores fixos, 1× por run (stock ≠ A-NSGA-III) | (1) | D | exatamente 1 registro `decomposicao` por run, 25/25 |
| A7 | **Semeadura D88 = NDSort + CrowdingDistance determinística** | (2) D88 | **D — joia** | **24/25 conjunto IDÊNTICO** ao recomputo independente; DTLZ4 explicado (underflow float32, Monte-Carlo) |
| A8 | `|pop|` constante ≡ N_efetivo | (1) | D | 413/413 gerações; ② com `n_geracoes` grupos em 25/25 |
| A9 | **Descendentes/geração = 2·⌊N/2⌋** (truncagem de N ímpar) | (1) stock | D | **14 em M=3** e 20 em M=2 — fecha a aritmética em 25/25 |
| A10 | **Aritmética ①×②×⑥: descendentes = FE_infill + cache_hits** | (1) | **D — joia** | **25/25 exato**; 7.200 = 6.849 FE + 180 dup + parciais |
| A11 | Dedup D57/D89 (duplicata = 0 FE, 1 slot) | (2) D57/D89 | D | 675 guards = 495 semeadura + 180 descendentes (**2,5%** dos descendentes) |
| A12 | Colisão float32 no export da ① (dedup roda em double) | (2) armadilha pré-registrada | D | 4 linhas colididas em 10.856 (**0,037%**): DTLZ4 ×2, MMF1, MMF4 |
| A13 | Cache-hit de arranque: `|semeadura| = N_ef + 1` | (2) D57 | D | **25/25 exatamente N_ef+1** hits em `fe=init`, com N_ef sids distintos |
| A14 | Sem geração fantasma: ② e ④ têm `n_geracoes` grupos | (1) | D | 25/25 — a geração truncada pelo hard-stop **tem** snapshot |
| A15 | Operadores Balde C: SBX 1/20 + PM 1/D/20 | (2) Balde C | DD | string idêntica em 25/25 headers |
| A16 | Seleção ambiental por nicho de vetor de referência | **T** | I | spacing: rank **1,67/4** em M=3 (melhor dos 4 pisos em 2/6) |
| A17 | Normalização interna / `Zmin` acumulado do NSGA-III | **T** | NV | não exportado (só o ideal da população corrente) |
| A18 | Instrumentação ideal/nadir (semântica de população corrente) | (1) | D | `ideal ≡ f_best` 25/25; **2 não-monotonias em 898** (0,22%) |
| A19 | Ausência TOTAL de surrogate em todas as camadas | (2) §3.2/DI-13.7 | D | ③ 0 linhas 25/25; `fit_series=[]`; sem `sigma_dict`; sonda `nao_se_aplica` |
| A20 | Timing: ④ sem fit/busca/sonda; ④ ≡ ⑥; Σ④ ≤ total | (2) §17.6/DI-13.10 | D | 413/413 NaN nos 3 campos; `max|Δt| = 1,3e-8`; Σ④ = 17,0% do wall |
| A21 | U9 — guards do ⑥ ≡ `cache_hits` do ⑤ | (1) | D | **675 ≡ 675**, célula a célula 25/25 |
| A22 | Contrato do ⑤/⑥ (`params` 12 chaves; footer único; término) | (1) | D | **0 linhas nsga3 no `contrato_f52b`**; `footer.termino='normal'` 25/25 |
| A23 | Elo código→log (`repo_hash` vazio, sem anchors) | **T** | NV | `repo_hash=''` em 25/25 |
| A24 | Fórmula "gerações = 20D ÷ N_efetivo" do manifesto é aproximação | (2) nota | D | real = ⌈(20D+dup)/2⌊N/2⌋⌉; DTLZ2: **18 observadas** vs 16 pela fórmula |

### 2.2 Blocos narrativos

---

**A1 — Orçamento FE = 31D−1 com hard-stop exato.**
*(a) Canônico:* o NSGA-III stock não tem orçamento próprio — termina por `maxFE` do `Problem`. *(b) Nossa espec:* `maxFE = 31D−1` (§5.1) com **hard-stop exato** (D21/D61) implementado no wrapper de FE, que é a única fonte do orçamento nos 2 stacks (o `obj.FE` nativo do PlatEMO **não** governa o término — HANDOFF/D89). *(c) Observado:* em 25/25 células, `manifest.maxfe == manifest.fe_final == len(①) == 31D−1` exato, com `fe_index` e `solution_id` **densos 0-based** (`R.fe_index ≡ arange(n)` em 25/25). Valores: 61 (D=2), 216 (D=7), 309 (D=10), 371 (D=12), 619 (D=20), 681 (D=22), 929 (D=30). O corte é sempre **no meio de uma geração**: o guard `hard_stop` dispara em `fe == maxfe` nas 25 células, com o `x_key` do descendente recusado registrado (ex.: DTLZ1 `F8B5079FF33DEE3F` em fe=216; DTLZ2 `66F6E21E2CFEC63F` em fe=371). Diferentemente do c217 (onde `hard_stop` foi um guard *único* em 1/25 células), aqui ele é **estrutural: 25/25** — consequência direta de o piso ser guloso (avalia N descendentes por geração e nunca "cabe" no orçamento). *(d) Mecanismo:* orçamento e (população × gerações) são amarrados; com `20D` FE de infill e lotes de 14 ou 20, o resto `20D mod n_off ≠ 0` em todas as 25 células ⇒ o hard-stop sempre corta um lote pela metade. *(e)* **(2) D21/D61 · D.**

---

**A2 — DoE inicial: 11D−1 pontos do artefato, bit-a-bit e em ordem.**
*(a) Canônico:* o NSGA-III inicializa por amostragem aleatória interna (`Problem.Initialization()`). *(b) Nossa espec:* **DoE compartilhado** (§5.2/D63) — os mesmos `11D−1` pontos LHS lidos do artefato `data/doe/{problema}/doe_{problema}_42.parquet`, **nunca regenerados**, para que todos os 21 configs partam do mesmo ponto (é o que torna a régua uma régua). *(c) Observado:* recomputei o bloco `fase=='init'` da ① contra o artefato em todas as 25 células: **`max|ΔX| = 0,0` em 25/25** — não é "dentro de eps-float32", é **igualdade exata**, e a **ordem** das linhas também é preservada (o DoE entra na ① na ordem do artefato, o que permite o join posicional). O `doe_hash` do sidecar bate com o do manifesto e com o do header do ⑥ em **25/25** (ex.: DTLZ2 `e9e359a6…`, ZDT1 `15afa53d…`). Contagens: `(fase=='init').sum() == 11D−1` em 25/25 (21, 76, 109, 131, 219, 241, 329) e `(fase=='opt').sum() == 20D` em 25/25. *(d) Mecanismo:* o `initFcn` injeta o array do artefato; como o DoE é gravado em float32 (D53) e reinjetado, o roundtrip é identidade. *(e)* **(2) D63/D88 · D.** *(Consistente com a F5.1: "13 configs MATLAB + os pisos: zero vermelhos" — cito, não re-verifico.)*

---

**A3 — `N = 20` cravado, e declarado provisório.**
*(a) Canônico:* o paper do NSGA-III usa N = tamanho do lattice (91, 210…) com dezenas de milhares de FE. *(b) Nossa espec:* sob orçamento minúsculo o piso se calibra **reduzindo a população** (precedente Knowles/ParEGO, que varreu 10–50 e elegeu 20). O autor **cravou N=20 em 2026-07-18** para desatar a circularidade (o SUB-varN depende do R1-pisos existir), com justificativa em 4 pontos: precedente canônico · interseção das fontes vivas (~20–25 ∩ {10,20,30,50}) · viabilidade em D=2 (`20 ≤ 11·2−1 = 21`) · densidade de gerações. A **DI-39 (2026-07-25)** declarou o valor **PROVISÓRIO**: se o SUB-varN eleger N≠20, as 100 células de piso da semente 42 são descartadas e re-rodadas. *(c) Observado:* `N_nominal = 20` em 25/25 manifestos (`params.N_nominal`), 25/25 headers do ⑥ (`N_nominal` + `N_origem` com o texto da decisão) e 25/25 footers (`N_nominal`, `N_efetivo`) — o eco é triplo e literal. `N_decisao` no manifesto reproduz a decisão inteira. *(d) Mecanismo:* config-echo puro — o valor é parâmetro de entrada, o log é a prova de que o parâmetro chegou. *(e)* **(2) §3.2/D65/DI-39 · DD.**

---

**A4 — `N efetivo = 15` em M=3: a assinatura DI-18, medida em 413 gerações.**
*(a) Canônico:* o NSGA-III do PlatEMO faz `[Z, Problem.N] = UniformPoint(Problem.N, Problem.M)` — **reatribui `N` ao tamanho do lattice**. Isso é comportamento stock, não patch. *(b) Nossa espec (§6.3, ⟦v5.2.1⟧):* consequência ACEITA e pré-registrada — "com N=20 nos PISOS ONLINE, `UniformPoint(20,3)` dá H=4 → 15 vetores (H=5 → 21 > 20) ⇒ **NSGA-III e MOEA/D rodam com N efetivo = 15 em M=3**; NSGA-II e SMS-EMOA mantêm 20. Como M=3 é metade do grid, o 'N=20' **não é uniforme entre os 4 pisos**." *(c) Observado:* medi `|pop|` por geração nas **413 gerações das 25 células** — via o campo `n_pop` do evento `nsga3_gen` **e**, independentemente, via `groupby('geracao').size()` na ②. As duas fontes concordam e o valor é **constante por célula**: **15 nas 6 células M=3** (DTLZ1, DTLZ2, DTLZ3, DTLZ4, DTLZ7, MMF16_20 — 165+270+270+270+495+450 = 1.920 linhas na ②) e **20 nas 19 células M=2** (5.700 linhas). `nunique(n_pop) == 1` em 25/25. O manifesto declara `N_efetivo` = 15/20 coerente em 25/25, e o footer repete. **Consequência medida no orçamento:** com população menor, o piso M=3 compra mais gerações — DTLZ1 11 (nsga3) vs 8 (nsga2), DTLZ2/3/4 **18 vs 13**, DTLZ7 **33 vs 23**, MMF16_20 **30 vs 21**; ~1,4× mais gerações com 25% menos população. *(d) Mecanismo:* o lattice das-Dennis só existe em cardinalidades `C(H+M−1, M−1)`; com M=3 as opções são 6, 10, 15, 21 — 20 cai entre 15 e 21 e o PlatEMO arredonda para baixo. *(e)* **(2) DI-18/§6.3 · D.** **Confirmado exatamente como pré-registrado.**

---

**A5 — A JOIA nº 1: identidade fechada do lattice `UniformPoint`.**
*(a) Canônico:* Deb & Jain, §IV-A: os vetores são o lattice das-Dennis `{w : Σwᵢ = 1, wᵢ ∈ {0, 1/H, …, 1}}`, com `|Z| = C(H+M−1, M−1)`. O PlatEMO implementa `H1 = 1; while nchoosek(H1+M,M−1) <= N, H1 = H1+1; end;` seguido do gerador combinatório e de `W = max(W, 1e-6)`. *(b) Nossa espec:* nenhuma mudança — mas o run **loga os vetores inteiros** no registro `decomposicao` do ⑥ (`N_nominal`, `N_lattice`, `vetores`, `origem`, `nota`), o que transforma um item que seria teto-T em verificação direta. *(c) Observado:* traduzi literalmente o `UniformPoint(N,M,'NBI')` do PlatEMO 4.15 para Python (`bateria2_nsga3.py::uniformpoint_nbi`) e comparei com a matriz logada, **linha a linha na ordem gravada**, nas 25 células: **`max|ΔW| = 0,0` em 25/25** — igualdade exata, não tolerância. Em M=2: `H₁ = 19` → 20 vetores com componentes `k/19` (0,052632; 0,105263; …); em M=3: `H₁ = 4` → 15 vetores com componentes `{1e-6; 0,25; 0,5; 0,75; 1}`, e `max|Σw − 1| = 2e-6` (exatamente o resíduo dos dois `1e-6` substituídos). O `N_lattice` logado (15/20) bate com `params.N_efetivo` e com `|pop|` observado em 25/25. *(d) Mecanismo:* o lattice é determinístico e não depende de semente — ou bate exato, ou o algoritmo não é o NSGA-III. Bateu exato. **Onde a identidade fecha, o mecanismo de decomposição por referência está PROVADO pelos dados**, no mesmo sentido em que a identidade do EI provou o b1 e a do maximin provou o e81. *(e)* **(1) · D.**

---

**A6 — Vetores fixos: é o NSGA-III stock, não o A-NSGA-III adaptativo.**
*(a) Canônico:* o NSGA-III original mantém `Z` **fixo** por todo o run; a variante A-NSGA-III (Jain & Deb, parte II) adapta/injeta vetores a cada geração em fronts degenerados. Confundir os dois é o erro clássico de leitura. *(b) Nossa espec:* `patches: "NENHUM — piso é stock do PlatEMO 4.15 por design"` (manifesto, 25/25). *(c) Observado:* o registro `decomposicao` aparece **exatamente 1 vez por run em 25/25** (`origem: "UniformPoint(N,M) do PlatEMO — determinístico, 1x por run"`), e o `N_lattice` é invariante ao longo das 413 gerações (nenhum evento de re-geração, nenhum `n_pop` mudando). Se houvesse adaptação, o piso M=3 (15 vetores para uma população de 15, em DTLZ1/DTLZ3/DTLZ7 com fronts irregulares) teria disparado injeção. *(d) Mecanismo:* instrumentação posicionada antes do `Solve` — a ausência de um segundo registro é a prova negativa. *(e)* **(1) · D.**

---

**A7 — A JOIA nº 2: a semeadura D88 recomputada independentemente, 24/25 idêntica.**
*(a) Canônico:* nada — o NSGA-III não prescreve semeadura por DoE; inicializa aleatoriamente. *(b) Nossa espec:* §3.2 + **D88** — o piso "parte dos mesmos 11D−1 pontos LHS, iniciando a evolução com os melhores por não-dominância", e o **desempate quando a frente-1 do DoE excede a população é crowding distance, determinístico** (o critério nativo do NSGA-II), "para que dois runs da mesma semente selecionem o mesmo subconjunto". O racional é a comparabilidade: se o piso partisse de outra amostra, a régua deixaria de medir só a seleção. *(c) Observado:* reimplementei em Python, do zero, NDSort (front-filling) + CrowdingDistance do PlatEMO + desempate final por índice crescente, e comparei o **conjunto de `solution_id` da geração 1 da ②** com o recomputo, nas 25 células. **Resultado: conjunto IDÊNTICO em 24/25** — incluindo os 12 casos em que a frente de borda teve de ser cortada por crowding distance (ZDT3 usa 8 da borda, ZDT1 6, ZDT6 6, WFG9 5). Isso **estende para as 25 células (25 problemas)** a verificação adversarial da torre de 2026-07-18, que fechara em 5 runs. O registro `seeding` do ⑥ (`n_doe`, `n_frentes`, `n_frente1`, `frente1_excede_pop`, `criterio`) bate com o meu recomputo em **24/25** (ex.: MMF16_20 `n_frente1 = 50` = calculado 50; WFG5 36 = 36; DTLZ2 40 = 40, `frente1_excede_pop = true`). Todos os `solution_id` da geração 1 caem em `[0, 11D−1)` em 25/25 — i.e., a população inicial é **estritamente** DoE, sem avaliação extra. **A exceção é DTLZ4**, dissecada em A12/abaixo. *(d) Mecanismo:* NDSort + CD são determinísticos e livres de semente; a coincidência bit-a-bit em 24 problemas independentes prova que o critério implementado é literalmente o da D88. *(e)* **(2) D88 · D.**

> **O caso DTLZ4 — por que a 25ª célula não fecha, e por que isso NÃO é infidelidade.** O log diz `n_frentes = 7`, `n_frente1 = 23`; meu recomputo sobre a ① diz `n_frentes = 23`, `n_frente1 = 7` — os dois valores *trocados*, e os 15 selecionados aparecem espalhados por ranks {1×7, 2×2, 5, 6, 8, 10, 12, 16} em vez de formarem uma frente. A causa é aritmética, não algorítmica: DTLZ4 tem **α=100 (x^100)**, o que empurra f₂ e f₃ para a região de **underflow do float32**. Medi: **92 dos 393 valores objetivo do bloco init são exatamente 0,0 (23,4%)**, 16 são denormais (<1,18e-38) e 72 estão abaixo de 1e-20 — o menor não-nulo é 1,12e-44, o denormal mínimo do float32. Em **double** (o que o MATLAB realmente ordenou) esses valores são positivos e distintos, e servem de desempate fino ⇒ frente-1 grande. Em **float32** (o que a ① grava, D53) eles colapsam em 0,0 ⇒ a dominância vira comparação por f₀ apenas ⇒ cadeia longa de frentes unitárias. **Prova por Monte-Carlo** (200 sorteios substituindo os 92 zeros por positivos double na faixa 1e-60…1e-46): **mediana `n_frentes` = 7 — exatamente o valor logado — e mediana `|F1|` = 20, faixa 11–32, contendo o 23 logado**; o par float32 (7, 23) fica **fora** de toda a distribuição. Ou seja: o log está certo, o recomputo é que não é reconstruível a partir da ① nesse problema. É o mesmo mecanismo já sancionado em outros lugares da campanha (F5.1: 4 falsos-vermelhos de tolerância em DTLZ3/DTLZ4/WFG9; b4: 80,3% das linhas de DTLZ4 com um objetivo exatamente 0,0). **Classe (2) com verificabilidade rebaixada a `indireta` nessa única célula** — mecanismo provado, não desvio.

---

**A8 — População constante ≡ N_efetivo, e a ② como filme completo.**
*(a) Canônico:* NSGA-III mantém `|P| = N` fixo (seleção ambiental devolve exatamente N). *(b) Nossa espec:* a ② é o snapshot da população por geração (§17.2). *(c) Observado:* `n_pop` do ⑥ e o tamanho dos grupos da ② são constantes e iguais a `N_efetivo` em **413/413 gerações**; `nunique == 1` por célula em 25/25; `n_grupos(②) == n_geracoes(⑤) == |eventos nsga3_gen|` em 25/25; as gerações são a sequência densa `1..n` (sem buracos) em 25/25; e **100% dos `solution_id` da ② são índices válidos da ①**. Total: 7.620 linhas = Σ(n_ger × N_ef). *(d) Mecanismo:* a seleção ambiental do NSGA-III é exatamente-N por construção; qualquer variação denunciaria um patch. *(e)* **(1) · D.**

---

**A9 — ACHADO NOVO DA ESCALA: com N ímpar o PlatEMO gera 2·⌊N/2⌋ descendentes, não N.**
*(a) Canônico:* o pseudocódigo do NSGA-III gera `N` descendentes por geração. *(b) Nossa espec:* nenhuma — os operadores são o `OperatorGA` stock do Balde C. *(c) Observado:* a taxa de descendentes por geração NÃO é `N_efetivo`. Medi-a por diferença de FE entre eventos consecutivos e ela é **20 (M=2) e 14 (M=3)**, nunca 15. Exemplos: DTLZ2 gen 1→2 consome 14 FE (131→145); ZDT1 gen 1→2 consome 20 (329→349); DTLZ7 tem incrementos de 11–14 com o défice explicado exatamente pelos cache-hits. A hipótese `n_off = 2·⌊N/2⌋` **fecha a aritmética de A10 em 25/25 células**, o que a torna medida, não conjectura. *(d) Mecanismo:* o `OperatorGA`/`GA.m` do PlatEMO faz `Parent1 = Parent(1:floor(end/2),:); Parent2 = Parent(floor(end/2)+1:floor(end/2)*2,:)` e concatena — com 15 pais, usa 7+7 e **descarta o 15º**; com 20 pais, usa 10+10. É comportamento stock do PlatEMO, e o piso é stock por design. *(e)* **(1) — fidelidade ao código canônico · D.** **Consequência para a dissertação:** em M=3 o piso não só tem população 15 (A4) como **taxa de descendentes 14**; a etiqueta "N=20" é nominal em 2 dos 4 pisos e em metade do grid. Isso não altera o orçamento (que é FE, não gerações) mas altera a densidade evolutiva — e é o que explica A24.

---

**A10 — A JOIA nº 3: a aritmética entre camadas fecha exata nas 25 células.**
*(a) Canônico:* cada descendente consome 1 avaliação. *(b) Nossa espec:* **D89** — duplicata bit-exata **não gasta FE, gasta o slot do infill**; o wrapper de FE é a única fonte do orçamento. Logo a identidade correta é `descendentes_gerados = FE_de_infill + cache_hits_de_descendente`. *(c) Observado:* para cada célula computei `off_full = (n_ger − 1) · 2⌊N/2⌋`, `fe_consumido = fe(última geração) − init` e `cache_hits` no intervalo `(init, fe_última]`, e verifiquei `off_full − fe_consumido == cache_hits`. **Fecha exato em 25/25.** Células exemplares: **ZDT1** 30×20 = 600 = 583 FE + 17 dup; **DTLZ7** 32×14 = 448 = 432 + 16; **DTLZ2** 17×14 = 238 = 230 + 8; **MMF1** 2×20 = 40 = 38 + 2; **DTLZ1** 10×14 = 140 = 136 + 4 (com 1 cache-hit adicional já dentro da geração 11 truncada — o único caso em que o hit cai depois do último snapshot, e o filtro correto por `fe ≤ fe_última` é o que evita o falso-alarme). Agregado: **7.200 descendentes = 6.849 FE de infill + 180 duplicatas + parciais do hard-stop**, com o resto do orçamento (`maxfe − fe_última`) sempre `≤ n_off` em 25/25 (a geração truncada nunca "estoura"). *(d) Mecanismo:* três camadas escritas por caminhos independentes (⑥ por evento, ① por avaliação, manifesto por contador) convergindo ao mesmo número em 25 problemas de dimensões 2–30 só é possível se o wrapper de FE, o dedup e o loop evolutivo estiverem os três corretos. *(e)* **(1) · D.**

---

**A11 — Dedup D57/D89: 180 slots de infill perdidos para duplicatas, 2,5%.**
*(a) Canônico:* nenhum MOEA stock deduplica; o PlatEMO reavaliaria. *(b) Nossa espec:* **D57** (`solution_id` = dedup por X bit-a-bit) + **D89** (cache-hit = 0 FE, decisão do autor contra a recomendação inicial da torre: "o catálogo ① torna re-consulta gratuita como na prática real de otimização cara"). O bundle **pré-registra o efeito colateral** (§3.2 item 5): com N pequeno a taxa de duplicata sobe — medido no R1-pisos, ZDT1 semente 0: 182 cache-hits ≈ 23% dos offspring do **MOEA/D**. *(c) Observado no nsga3:* 675 guards `cache_hit` no total, dos quais **495 são da semeadura** (A13) e **180 são descendentes duplicados = 2,5% dos 7.200**. Distribuição por célula: mínimo 1 (BBOB_F17, BBOB_F49, MMF11_L, MMF4), máximo 17 (ZDT1); mediana 5. **O NSGA-III fica muito longe dos 23% do MOEA/D** — porque não tem vizinhança `T = ⌈N/10⌉ = 2` reciclando os mesmos dois pais; a seleção por torneio + nicho amostra a população inteira. *(d) Mecanismo:* SBX/PM com `dis_c = dis_m = 20` produz filhos próximos dos pais; quando a população converge para um canto (bounds clampados), o filho recai exatamente sobre o pai. É o mesmo fenômeno do "canto de Pareto bit-exato" já documentado no b1. *(e)* **(2) D57/D89 · D.**

---

**A12 — Colisão float32 no export da ①: 4 linhas em 10.856, e a regra de join que ela obriga.**
*(a) Canônico:* n/a. *(b) Nossa espec:* export **float32 sem arredondamento** (D53); dedup e orçamento operam em **double**. A armadilha foi **pré-registrada em 2026-07-18** no `ORQUESTRACAO_MESTRE.md` a partir do adversarial dos próprios pisos: *"pontos float64 DISTINTOS podem COLIDIR no cast float32 do export (provado: moead-ZDT1 sids 703/720/737…; 5 runs afetados). O orçamento/dedup D57/D89 operou CERTO (float64). Regra p/ o R4: dedup/joins SEMPRE por `solution_id`, NUNCA pelo X armazenado."* *(c) Observado no nsga3:* varri as 10.856 linhas da ① procurando X bit-idênticos com `solution_id` distintos: **4 ocorrências (0,037%)** — DTLZ4 (sids 263/320 e 299/313, ambos `opt`), MMF1 (17 `init` vs 49 `opt`) e MMF4 (19 `init` vs 30 `opt`). Nas 21 células restantes, **zero**. Note que se fossem falhas de dedup elas teriam virado cache-hit e **não** teriam recebido `solution_id` novo nem consumido FE — o fato de terem consumido prova que os doubles diferiam. *(d) Mecanismo:* SBX/PM produzem doubles a distâncias da ordem de 1e-9 do pai; float32 tem ~7 dígitos significativos ⇒ colisão no cast. Concentra-se em DTLZ4 (α=100, região denormal) e em D=2 (espaço pequeno, muita re-visita). *(e)* **(2) armadilha pré-registrada · D.** **Nada a corrigir; é a razão pela qual a régua do R4 deve juntar por `solution_id`.**

---

**A13 — O arranque: exatamente `N_efetivo + 1` cache-hits em `fe == init`, em 25/25.**
*(a) Canônico:* n/a. *(b) Nossa espec:* o manifesto declara `seeding: "…os N entram como cache-hit (0 FE)"` — os N pontos do DoE re-adicionados à população disparam o dedup por serem já conhecidos. *(c) Observado:* em `fe == init` há **sempre `N_ef + 1` guards `cache_hit`** — 16 nas 6 células M=3, 21 nas 19 células M=2 — mas o número de `solution_id` **distintos** é exatamente `N_ef` (15 / 20) em 25/25. Isto é: **1 hit excedente sistemático**, que é a repetição de um `solution_id` já presente no bloco (DTLZ1: sid 32 / `AD594F08C777EB3F` logado duas vezes, nas posições 1 e 2). *(d) Mecanismo:* é a assinatura do arranque do wrapper — o mesmo fenômeno que no c217 apareceu como "cache-hit de arranque `fe=1/solution_id=0` em 25/25" (armadilha ⑤ daquele config); aqui a forma é `N_ef+1` em vez de `+1` porque a injeção é de um bloco inteiro, não de um ponto. O efeito prático é inflar `cache_hits` em +1 sistemático. *(e)* **(2) D57 · D.** **Armadilha:** quem esperar `cache_hits_semeadura == N` reprova 25/25 falsamente; e quem tratar os 495 hits de semeadura como "duplicatas do algoritmo" superestima a taxa de duplicata em **3,7×** (675 vs 180).

---

**A14 — Não existe geração fantasma: ② e ④ têm `n_geracoes` grupos.**
*(a)/(b)* No c217 o hard-stop produzia uma geração abortada cujo evento existia mas cujas camadas não (`len(④) == n_ger − 1`). *(c) Observado no nsga3:* aqui a contabilidade é diferente e **mais simples**: o evento `nsga3_gen` é emitido **no início** da geração (o `fe` da geração 1 é exatamente `init` em 25/25 — 21, 76, 109, 131, 219, 241, 329), portanto a geração truncada pelo hard-stop **já teve seu snapshot**. Resultado: `n_geracoes (⑤) == |eventos nsga3_gen| == n_grupos(②) == n_linhas(④)` em **25/25**, sem off-by-one. *(d) Mecanismo:* semântica de instrumentação — o snapshot é "estado ao entrar na geração g", não "estado ao sair". *(e)* **(1) · D.** **Armadilha positiva:** o off-by-one do c217 **não** se aplica aqui; testar `②(g) == estado final da geração g` reprova falsamente.

---

**A15 — Operadores do Balde C (SBX 1/20 + PM 1/D/20).**
*(a) Canônico:* Deb & Jain usam SBX `η_c = 30`, `p_c = 1` e PM `η_m = 20`, `p_m = 1/D`. *(b) Nossa espec:* **Balde C** — "mesmos operadores dos EAs → a única diferença piso×SA-MOEA é o surrogate", com `SBX proC=1 dis_c=20 + PM proM=1 dis_m=20`, os defaults do `OperatorGA`. O desvio de `η_c` (20 vs 30 do paper) é deliberado e transversal: isolar o ganho do surrogate exige operadores idênticos aos dos SA-MOEA, não idênticos ao paper do piso. *(c) Observado:* a string `"Balde C: SBX proC=1 dis_c=20 + PM proM=1 dis_m=20 (defaults OperatorGA do PlatEMO)"` é **idêntica em 25/25 headers** e ecoada em `params.operadores` nos 25 manifestos. Semântica do PlatEMO: `proM` é o **número esperado de variáveis mutadas**, logo `proM=1` ⇒ taxa por variável `1/D` — exatamente a prescrição do paper. *(d) Mecanismo:* config-echo; a grandeza por operação não é exportada. *(e)* **(2) Balde C · DD.**

---

**A16 — A seleção ambiental por nicho: o teto, e a assinatura indireta que sobrou.**
*(a) Canônico:* o núcleo do NSGA-III (§IV-C–E): normalização por pontos extremos + ASF, associação de cada indivíduo ao vetor de referência mais próximo (distância perpendicular), e **niche-preserving** — escolher da última frente o indivíduo associado ao nicho menos povoado. É o que distingue NSGA-III de NSGA-II. *(b) Nossa espec:* nada muda (stock). *(c) Observado:* a associação por indivíduo **não é exportada** (a ② só tem `solution_id`), então o mecanismo não é diretamente verificável — é **T**. O que a escala oferece é uma assinatura indireta: se o nicho estivesse operando, a distribuição final deveria ser mais **uniforme** que a dos pisos sem vetor. Medi `spacing` (F5.2c) entre os 4 pisos: rank médio **nsga3 2,40 · smsemoa 2,12 · nsga2 2,20 · moead 3,28** nos 25 problemas — mas o corte por M é decisivo: **em M=3 o nsga3 tem rank médio de spacing 1,67/4** (melhor dos 4 em DTLZ1 47,6 e DTLZ4 0,203; 2º em DTLZ2, DTLZ3, DTLZ7, MMF16_20) contra **2,63 em M=2**. Complementarmente, `|F1| == |pop|` (população inteiramente não-dominada, o regime em que a seleção por nicho é a única que decide) ocorre em **77,2% das gerações M=3** contra 19,5% em M=2. *(d) Mecanismo:* em M=2 o crowding do NSGA-II já é quase ótimo e os vetores não agregam; em M=3, com 15 nichos para 15 indivíduos, o nicho vira o único critério ativo — e é lá que o spacing do nsga3 lidera. Consistente com a razão de ser do método. *(e)* **T (mecanismo interno) com evidência indireta favorável · I.**

---

**A17 — Normalização interna e `Zmin` acumulado.**
*(a) Canônico:* o NSGA-III normaliza a cada geração com `z_min` (ideal acumulado) e os pontos extremos por ASF, resolvendo o hiperplano de interceptos. *(b)/(c)* Nada disso é exportado — o run loga o `ideal` da **população corrente**, não o `Zmin` acumulado do algoritmo. Verificar interceptos/ASF exigiria instrumentar o `EnvironmentalSelection.m`. *(e)* **T · NV.** (Registrado para o eventual re-run instrumentado da rodada perfeita; não afeta nenhum outro aspecto.)

---

**A18 — Ideal/nadir: 2 não-monotonias em 898 transições, e por que são semântica, não defeito.**
*(a)/(b)* Instrumentação nossa: cada evento `nsga3_gen` carrega `f_best`, `ideal`, `nadir_pop`, `nadir_front1`. *(c) Observado:* `ideal ≡ f_best` (bit-a-bit) em **25/25 células** — os dois campos são redundantes por construção. Sobre a monotonia: das **898 transições-objetivo** (Σ(n_ger−1)×M), apenas **2 pioram** (0,22%): DTLZ1 geração 8, objetivo 2 (0,0 → 0,040003) e DTLZ2 geração 3, objetivo 0 (3,01e-4 → 1,31e-3). `nadir ≥ ideal` em 100% das gerações; `nadir_pop == nadir_front1` exatamente nas células em que a população é inteiramente não-dominada (DTLZ1, DTLZ2, DTLZ4, MMF16_20, WFG4, WFG5). *(d) Mecanismo:* o `ideal` logado é o mínimo componente-a-componente da **população corrente**; a seleção do NSGA-III é *niche-preserving*, não *extreme-preserving-por-objetivo* — ela pode descartar o detentor do mínimo de um objetivo se o nicho dele estiver superpovoado. O `Zmin` **interno** do algoritmo (que é acumulado e monotônico por construção) é outra grandeza, e é o teto A17. Ler a instrumentação como se fosse o `Zmin` produziria um falso-alarme. *(e)* **(1) · D.**

---

**A19 — Ausência total de surrogate, provada em cinco camadas independentes.**
*(a)/(b) Nossa espec:* "Mesmos hooks/export (tabela ③ vazia; série §17.6 vazia — sem surrogate)" (§3.2); o arquivo ③ existe vazio por completude de camadas (DI-13.7). *(c) Observado, em 25/25:* (i) ③ com **0 linhas** (e o schema completo presente — 21 a 49 colunas conforme D e M); (ii) `manifest.fit_series == []`; (iii) **`sigma_dict` ausente** do manifesto; (iv) `manifest.sonda = {status: "nao_se_aplica", motivo: "piso ONLINE = MOEA puro, sem surrogate a sondar (CONTRATO §3.2)", n_blocos: 0, n_linhas: 0}`; (v) `header.surrogate = false` e `header.piso = true`; (vi) `timing.tempo_fit_surrogate_s = tempo_busca_s = tempo_pred_sonda_s = null`. Consequência de contrato: o `integridade_f52a.csv` traz as 25 células com veredito **`VAZIO` (por desenho)** e o `sonda_f52e.csv` tem **0 linhas nsga3** — ambos corretos. **U3, U4, U5, U6, U8, U11 e U12 são N/A por desenho**, com regra citada. *(d) Mecanismo:* o piso compartilha o harness inteiro; o que muda é o adapter não registrar nenhum modelo. Cinco writers independentes concordando é a prova. *(e)* **(2) §3.2/DI-13.7 · D.**

---

**A20 — Timing: o ④ é o filme do loop, e ele fecha com o ⑥.**
*(a)/(b) Nossa espec:* §17.6 (retrofit v5.2.1) exige `tempo_geracao_s` por geração; DI-13.10 dá as invariantes. *(c) Observado:* o ④ tem **`n_geracoes` linhas em 25/25** (413 no total), com `tempo_fit_s`, `tempo_busca_s`, `tempo_pred_sonda_s` e `n_acumulado` **NaN em 413/413** — a invariante `fit + busca ≤ tempo_geracao` de U7 é vacuamente satisfeita e a substituo por duas verificações mais fortes: **(i)** `④.tempo_geracao_s ≡ ⑥.nsga3_gen.tempo_geracao_s` geração a geração, com **`max|Δ| = 1,3e-8`** (ruído de float32) nas 25 células; **(ii)** `Σ④ ≤ manifest.timing.tempo_total_s` em 25/25. Agregados: `tempo_total` = 123,7 s nas 25 células (mediana 4,85 s/célula) dos quais **Σ④ = 20,97 s (17,0%)** e `tempo_aval_real` = 6,62 s (5,4%); os **83% restantes são arranque do MATLAB + I/O**, não o algoritmo. *(d) Mecanismo:* o piso é tão barato que o custo fixo do processo domina — o que valida quantitativamente a afirmação do bundle "**custo trivial (não treina GP)**": os **4 pisos somam 0,143 h-core nas 100 células main contra 257 h-core dos SA — 0,056%**. *(e)* **(2) §17.6/DI-13.10 · D.**

---

**A21 — U9: reconciliação exata dos contadores de guard.**
*(a)/(b)* O ⑤ mantém `cache_hits` como contador; o ⑥ emite um guard por ocorrência. *(c) Observado:* `manifest.cache_hits == |guards name=='cache_hit'|` **célula a célula em 25/25**, total **675 ≡ 675**; e `|guards name=='hard_stop'| == 1` com `fe == maxfe` em 25/25. Os únicos dois nomes de guard existentes no config são `cache_hit` (675) e `hard_stop` (25) — não há `fallback` (`manifest.fallback_ativado = false` em 25/25) nem `n_retries` (0 em 25/25). *(e)* **(1) · D.**

---

**A22 — Contrato de dados: o config mais limpo do lote.**
*(a)/(b)* CONTRATO §5/§6. *(c) Observado:* **`contrato_f52b.csv` tem 0 linhas nsga3** — nenhuma não-conformidade estrutural, ao contrário dos 7 configs que não gravam `params` no ⑤ (c217, c262, c154, b5r, b5m, moead_media, sobol_batch). O ⑤ do nsga3 tem `params` com **12 chaves em 25/25** (`N_nominal`, `N_efetivo`, `N_decisao`, `N_efetivo_nota`, `seeding`, `geracoes_derivadas`, `operadores`, `parameter`, `surrogate`, `patches`, `principio`, `casamento`) — o manifesto é auto-documentado ao ponto de conter o texto da decisão. Presentes também `run_id`, `env` (`matlab 25.1.0.2973910 (R2025a) Update 1`, `stack matlab-platemo`, `pymoo 0.6.2` — **idênticos em 25/25**, pin R2025a confirmado), `timing`, `status='ok'`, `n_retries=0`. Duas notas de doc-sync, ambas já escaladas no §0 do RELATORIO_F5 (item 5): **(i)** o footer é **1 registro**, não 2 (o "footer = runner + despachante" do protocolo é do idioma MATLAB do c217/b1; aqui o writer é único); **(ii)** o campo de término é **`footer.termino = 'normal'`** (25/25) — `motivo_parada` **não existe** no manifesto do nsga3, então usar `status` ou `motivo_parada` sozinho reprova falsamente (bug B1). O evento de geração é `nsga3_gen`, e há **dois eventos exclusivos do config** não previstos no mapa genérico: `decomposicao` e `seeding`. *(e)* **(1) com 2 notas de doc-sync · D.**

---

**A23 — O elo código→log.**
`repo_hash = ""` em **25/25** manifestos, e não há `anchors.json` para o piso (não há patch a ancorar — A6). Logo, a afirmação "este binário é o NSGA-III do PlatEMO 4.15 sem modificação" é sustentada por `algo_version` + `patches: NENHUM` + as identidades A5/A7/A9/A10, mas **não** por um hash de repositório. *(e)* **T · NV.** É o mesmo teto de todos os configs MATLAB da rodada; registro-o à parte, não desconto.

---

**A24 — A fórmula de gerações derivadas do manifesto é uma aproximação (e agora sabemos a exata).**
*(a)/(b) Nossa espec:* o manifesto declara `geracoes_derivadas: "20D ÷ N_efetivo (o DoE 11D−1 é gasto ANTES do Solve)"`, e §3.2 promete "2 gerações no pior caso (D=2), 12 no DTLZ2 (D=12) e 30 no ZDT1 (D=30)". *(c) Observado:* a contagem real é **sistematicamente maior** em M=3 e ligeiramente maior em M=2, por duas razões cumulativas: os descendentes por geração são `2⌊N/2⌋` (A9) e as duplicatas consomem slot sem consumir FE (A11). A fórmula exata, verificada em 25/25, é `n_ger = ⌈(20D + n_dup) / 2⌊N_ef/2⌋⌉`. Exemplos: **DTLZ2** — fórmula do manifesto 240/15 = 16, observado **18** (17×14 = 238 slots + 8 dup ⇒ a 18ª geração começa); **ZDT1** — 600/20 = 30, observado **31**; **DTLZ7** — 440/15 ≈ 29, observado **33**; **MMF16_20** — 400/15 ≈ 27, observado **30**; **D=2** — 40/20 = 2, observado **3**. Nota de precisão adicional: o bundle cita, do gate, "DTLZ2 D=12, n_ger = 19 e 17 em vez de 13" para NSGA-III e MOEA/D; na rodada-42 medi **18 (nsga3) e 17 (moead)** — o MOEA/D bate exato e o NSGA-III difere em 1 geração, o que é a variabilidade esperada do termo `n_dup` entre sementes (18 vs 19 gerações corresponde a 8 vs ≥12 duplicatas). *(d) Mecanismo:* a fórmula do manifesto ignora a truncagem de N ímpar e o crédito de slot da D89. *(e)* **(2) — refinamento documental, não desvio de comportamento · D.** **Recomendo corrigir a string `geracoes_derivadas` no bundle/manifesto antes do M8** (é o único item deste relatório que pede ação da torre central).

---

## 3. % por classe

**Denominador = total − T = 24 − 3 = 21.** (T listado à parte, com razão.)

| classe | n | % (sobre **21**) | itens |
|---|---|---|---|
| **(1) conforme o método canônico** | **9** | **42,9%** | A5 (lattice), A6 (vetores fixos), A8 (\|pop\|), A9 (2⌊N/2⌋), A10 (aritmética), A14 (sem fantasma), A18 (ideal/nadir), A21 (U9), A22 (contrato) |
| **(2) desvio sancionado** | **12** | **57,1%** | A1 (D21/D61), A2 (D63/D88), A3 (§3.2/D65/DI-39), A4 (DI-18/§6.3), A7 (D88), A11 (D57/D89), A12 (armadilha 2026-07-18), A13 (D57), A15 (Balde C), A19 (§3.2/DI-13.7), A20 (§17.6/DI-13.10), A24 (nota documental) |
| **(3) inexplicado 🎯** | **0** | **0,0%** | — |
| **T (fora do denominador)** | 3 | — | A16 associação a nicho (não exportada; evidência indireta favorável) · A17 normalização/`Zmin` interno (exige instrumentar `EnvironmentalSelection.m`) · A23 `repo_hash` vazio (elo código→log) |

Todos os 12 itens de classe (2) têm decisão citada **nominalmente** na tabela e no bloco narrativo. Nenhum aspecto exigiu invocar "provavelmente é assim".

---

## 4. PAPEL DE CONTROLE (a comparação canônica é N/A — controle sem artigo)

**Pergunta:** o piso cumpre sua função de régua? Uma régua útil precisa (i) não ser trivialmente batida, (ii) não ser inatingível, (iii) discriminar por dimensão/pressão de orçamento e (iv) custar quase nada.

| critério | evidência (25 problemas, main, semente 42) | veredito |
|---|---|---|
| **Não trivial** | SA-MOEA batem o nsga3 em **59,4%** das comparações (mediana 9 de 13 SA por problema); mas em 4 problemas ≤ 2 SA o batem (WFG1 2/10, WFG2 2/12, WFG4 2/12) e em **DTLZ1 nenhum dos 13 SA bate** | ✅ |
| **Atingível** | rank geral médio **9,5 de 17**; nunca 1º nem último no grid | ✅ |
| **Discrimina por D** | SA que batem o **melhor** piso: D=2 **64,1%** · D=7 **0%** · D=10 **64,3%** · D=12 **31,4%** · D=20 **54,5%** · D=22 **34,8%** · D=30 **65,2%** | ✅ (heterogêneo — ver nota) |
| **Custo trivial** | Σ = **123,7 s** (0,0344 h-core) nas 25 células; os 4 pisos = **0,143 h-core** vs **257 h-core** dos SA = **0,056%** | ✅ |
| **Coerente com os outros 3 pisos** | rank médio entre pisos: **nsga2 1,80 · nsga3 2,24 · smsemoa 2,28 · moead 3,68**; nsga3 é o **melhor piso em 6/25** e **nunca o pior (0/25)** | ✅ |
| **Confirma o prior explícito do bundle** | §3.2 item 5 previu "o MOEA/D fica o **pior dos 4 pisos**" — **nsga3 bate moead em 24/25** e o moead tem o pior rank médio | ✅ prior confirmado |
| **Casamento com o e7 (EA-Indicador)** | **e7 melhor que nsga3 em 13/25 (52%)** — moeda ao ar | ⚠️ ver abaixo |

**A leitura de controle que importa para a D97.** O nsga3 é a régua *casada* ao e7 (mesmo princípio: seleção por referência/indicador). O resultado é o dado mais eloquente deste relatório: **sob 31D−1, o surrogate do e7 compra 13 vitórias em 25 contra o seu próprio piso** — estatisticamente indistinguível de zero ganho. E o padrão tem estrutura: o e7 ganha nos problemas M=3 e de alta-D estruturada (DTLZ1 1,45×, DTLZ3 1,27×, MMF16_20 1,27×, WFG9 1,41×, WFG2 1,69×) e perde amplamente nos BBOB (F55 0,17×, F5 0,47×, F37 0,61×, F1 0,61×) e no ZDT1 (0,42×). Isso não é veredito sobre o e7 (a análise dele é dele) — é a **prova de que a régua está fazendo exatamente o trabalho que a §3.2 lhe atribuiu**: dar atribuição limpa do ganho ao surrogate, inclusive quando o ganho é nulo.

**Nota metrológica obrigatória (piso de ruído entre máquinas, O-18).** As 25 células nsga3 rodaram **100% na `vm3`** (`tempo_f52d.csv`, coluna já corrigida). Toda comparação acima contra configs de outras máquinas está sujeita ao piso de ruído (HV ≤1,55%; **IGD+ ≤58,98%**) — por isso **não** trato razões dentro de ~1,6× como diferença. As conclusões que sustento acima (moead pior em 24/25; e7 ~50%; nsga3 nunca o pior piso) são todas robustas a esse piso, e as comparações **entre os 4 pisos são imunes** (mesma máquina).

**Nota de comparabilidade interna (DI-18).** A banda dos pisos em M=3 **não** é uma banda a população constante: nsga3 e moead correm com N=15 (e 14 descendentes/geração), nsga2 e smsemoa com N=20. Recomendo que a banda min–máx que os BO-especiais (c154, e81, c149) usarão como referência (D25/DEF-A13) leve essa nota no M8/M9. Empiricamente a assimetria não invalida nada: em M=3 o nsga3 **bate o nsga2 em 4/6** (DTLZ3 236 vs 306, DTLZ4 0,282 vs 0,348, DTLZ7 1,125 vs 1,425, MMF16_20 0,0317 vs 0,0407) — a população menor é compensada pelas ~1,4× gerações a mais.

---

## 5. Veredito de contrato (Entrega 3)

| fonte | achado F5.2 para o nsga3 | interpretação |
|---|---|---|
| `integridade_f52a.csv` | **25 linhas, todas `VAZIO` — `__surrogate.parquet` linhas=0** | **Por-desenho, com regra citada:** §3.2 ("tabela ③ vazia — sem surrogate") + DI-13.7 (arquivo existe vazio por completude de camadas). Faz parte das "105 ③ com 0 linhas = por desenho (4 pisos online × 25 + sobol_batch × 5)" já consolidadas no §5.1 do RELATORIO_F5. **Zero corrupção**: nenhum parquet ilegível, nenhum manifesto ilegível, nenhum ⑥ truncado, nenhuma linha órfã. |
| `contrato_f52b.csv` | **0 linhas nsga3** | **100% conforme.** O nsga3 está fora das 197 células/7 configs com `⑤ sem params`. É o padrão-ouro de contrato do lote. |
| `sonda_f52e.csv` | **0 linhas nsga3** | Correto por desenho (`sonda.status='nao_se_aplica'`). |
| `tempo_f52d.csv` | 25/25 com `wall_s`; máquina `vm3` em 25/25 | Zero buracos de timing; roster homogêneo. |
| F5.1 gates | dentro de "os 13 configs MATLAB + os pisos: zero vermelhos" | cito, não re-verifico. |
| **Achado meu (doc-sync, não defeito)** | footer **único** (não 2 registros) e término em `footer.termino`, sem `motivo_parada` | Alinha-se ao **item 5 do §0** do RELATORIO_F5 (o campo de término varia por config). Registro a variante `nsga3 → footer.termino` para o mapa. |
| **Achado meu (documental, ação)** | `params.geracoes_derivadas = "20D ÷ N_efetivo"` está errado (A24) | **Único item para a torre central**: corrigir a string no bundle/`gen_bundles.py` para `⌈(20D + n_dup)/2⌊N_ef/2⌋⌉`, ou marcá-la explicitamente como estimativa. Zero impacto nos dados. |

**Nenhum defeito de contrato. Nenhuma célula reprovada, nenhuma com ressalva.**

---

## 6. SAÚDE em escala

**Trajetórias (20 checkpoints × 25 células).** IGD+ monotônico não-crescente em **475/475 transições — 0 violações**. Os 4 maiores decréscimos aparentes (MMF16_20 −4,9e-4, WFG9 −1,3e-3, WFG4 −6,5e-4, WFG2 −4,5e-4) são **melhoras**, não regressões. Ganho `IGD+(0)/IGD+(final)`: mediana **5,3×**, máximo **99,0×** (BBOB_F17 2,417 → 0,0244), mínimo **1,34×** (ZDT6 — o pior problema do config, 8,95 → 6,66). `|ND|` cresce de 1 para 5–228 (mediana 20). Isso reproduz o prior v2 ("**monotônico**, 0 regressões nsga3") agora em 25 problemas, não 3.

**Dinâmica interna (413 gerações).** A fração de gerações com população inteiramente não-dominada (`|F1| == |pop|`) é **77,2% em M=3** e **19,5% em M=2** — em M=3 o NSGA-III converge para o regime em que só o nicho decide (DTLZ2 e WFG4/WFG5 ficam em 100% das gerações; MMF16_20 96,7%). Em M=2 a frente-1 flutua (ZDT1 média 11,2/20, ZDT4 5,3/20) — pressão de dominância ainda ativa, como esperado com 2 objetivos e 20 vetores. O ponto ideal é quase-monotônico (2 pioras em 898 transições, A18).

**Duplicatas e saturação.** 180 duplicatas de descendente (2,5%), concentradas nas células de maior D (ZDT1 17, WFG5 16, DTLZ7 16, WFG4 15) — assinatura de convergência local sob SBX/PM com `dis=20`, não de patologia. Muito abaixo dos 23% pré-registrados para o MOEA/D com `T=2`.

**Posição vs pisos (IGD+, `metricas_finais_f52c.csv`).** nsga3 = melhor piso em **6/25** (DTLZ4, DTLZ7, MMF1, MMF11_L, MMF4, WFG9), 2º em 8, 3º em 11, **último em 0**. Rank médio entre pisos **2,24**. Nas 6 células M=3 o rank médio cai para **2,0**. Contra os SA: rank geral médio **9,5/17**; o nsga3 é batido por 0/13 SA no DTLZ1 e por 11/12–13 em BBOB_F55, BBOB_F5, ZDT1, ZDT6.

**Custo.** Σ 123,7 s = **0,0344 h-core** nas 25 células; mediana 4,85 s/célula, sendo **83% arranque do MATLAB** e apenas 17% o loop. Irrelevante para a projeção M8/M9 (os 4 pisos somam 0,14 h-core dos ~10.173 h-core projetados).

**Sonda:** N/A por desenho — a análise de saúde do config é a própria dinâmica de gerações + trajetórias acima, e o **endpoint é a ① do regime online** (não há ⑦; o config é online, não offline).

---

## 7. SCORE e recomendação

### **SCORE: 10/10 — ACEITAR** (sem caveat de fidelidade; 1 item documental para a torre; 1 pendência de pré-registro já declarada)

1. **Zero aspectos classe (3)** em 24 aspectos × 25 células (413 gerações, 7.200 descendentes, 10.856 linhas de ①, 675 guards). Os 12 desvios têm decisão citada nominalmente; os 9 itens de conformidade incluem **três identidades fechadas** — o lattice `UniformPoint` bate a `max|ΔW| = 0,0` em 25/25, a semeadura D88 recomputada do zero devolve o **conjunto idêntico** em 24/25, e a aritmética `descendentes = FE + cache` fecha **exata em 25/25**. Onde três identidades independentes fecham a zero, o mecanismo está provado por dado, não por leitura de código.
2. **A régua confirma o prior sem recalibração:** a nota v2 dos pisos era **10** ("pisos IMPECÁVEIS: monotonia, turnover real"), o adversarial de 2026-07-18 deu **9,5** com 3/3 CONFIRMED; esta análise **estende a semeadura D88 de 5 runs para 24/25 células**, fecha o único caso residual (DTLZ4) por Monte-Carlo, e não encontra nada que puxe a nota para baixo. O contrato é o mais limpo do lote (0 linhas em `contrato_f52b`), a integridade é perfeita e a saúde é 0/475 violações.
3. **A escala revelou três fatos novos, todos benignos e todos com mecanismo provado:** a truncagem `2⌊N/2⌋` do `OperatorGA` com N ímpar (A9 — que muda a densidade evolutiva do piso M=3 e corrige a fórmula de gerações do próprio manifesto, A24); o arranque `N_ef+1` cache-hits (A13, que infla `cache_hits` em 3,7× se lido ingenuamente); e as 4 colisões float32 na ① (A12, exatamente a armadilha pré-registrada em 2026-07-18).
4. **A DI-18 foi confirmada exatamente como pré-registrada:** `N efetivo = 15` em M=3 medido em 413/413 gerações, com a consequência de orçamento quantificada (1,4× mais gerações que nsga2/smsemoa) e a assimetria da banda dos pisos explicitada para o M8/M9.
5. **Nada a enviar à F5.4.** O que separa este config de qualquer dúvida não é desvio, é teto: a associação a nicho e a normalização interna do NSGA-III (A16/A17) exigiriam instrumentar o `EnvironmentalSelection.m`, e o `repo_hash` está vazio (A23). A única pendência viva é de **pré-registro, não de fidelidade**: o **SUB-varN (DI-39)** — se a varredura eleger N≠20, estas 25 células são descartadas e re-rodadas, conforme já decidido às cegas em 2026-07-25.

---

## 8. Aspectos classe (3) 🎯 → F5.4

**Nenhum.** A verificação adversarial F5.4 não recebe itens do nsga3.

*Confirmação OPCIONAL (não requerida; mecanismo já provado por dado):* a semeadura do **DTLZ4** só é reconstruível em double. O log do MATLAB (`n_frentes = 7`) casa com a mediana do Monte-Carlo (7, faixa 6–9) e o `n_frente1 = 23` cai dentro da faixa (11–32), enquanto o par float32 (7, 23) está fora dela — considero provado. Se a F5.4 quiser fechar a zero, basta um re-run instrumentado de 1 célula gravando os `solution_id` selecionados diretamente no registro `seeding` (custo: ~5 s).

---

## 9. Teto de verificabilidade (T) + armadilhas confirmadas na escala

**T (3 itens, exigem código/re-run):**
1. **Associação a nicho / distância perpendicular / seleção da última frente (A16)** — não exportada por indivíduo. Evidência indireta favorável: spacing rank 1,67/4 em M=3.
2. **Normalização interna, pontos extremos por ASF, hiperplano de interceptos e `Zmin` acumulado (A17)** — não exportados; o `ideal` logado é o da população corrente, grandeza diferente.
3. **Elo código→log (A23)** — `repo_hash = ""` em 25/25 e sem `anchors.json` (não há patch a ancorar). Sustentado por `algo_version = piso-NSGAIII-PlatEMO4.15`, `patches: NENHUM` e pelas identidades A5/A7/A9/A10.

**Promovido para FORA do T pela escala:** o **lattice de vetores de referência** (o registro `decomposicao` grava a matriz inteira → identidade exata, A5) e a **semeadura D88** (o registro `seeding` grava `n_frentes/n_frente1/critério` → recomputo independente, A7). Nos dois casos a instrumentação transformou teto em prova.

**Armadilhas confirmadas na escala (25/25 salvo indicação):**
1. **`N` do manifesto é ambíguo por desenho** — `N_nominal = 20` sempre, `N_efetivo = 15` em M=3. Usar `N_nominal` para prever `|pop|`, gerações ou banda de pisos reprova as 6 células M=3 falsamente (DI-18).
2. **NOVA — os descendentes por geração são `2⌊N/2⌋`, não `N`.** Em M=3 são **14**, não 15. Qualquer aritmética que assuma N descendentes falha em 6/25 células; a que assume `2⌊N/2⌋` fecha em 25/25.
3. **NOVA — o bloco de arranque tem `N_ef + 1` cache-hits, não `N_ef`** (16 ou 21), com `N_ef` `solution_id` distintos. Tratar os 495 hits de semeadura como duplicatas do algoritmo superestima a taxa de duplicata em **3,7×** (675 vs 180).
4. **O `fe` do evento `nsga3_gen` é o do INÍCIO da geração** (gen 1 tem `fe == 11D−1`). Filtrar cache-hits por `fe > init` sem o teto `fe ≤ fe(última geração)` quebra a aritmética em DTLZ1 (o único caso com hit dentro da geração truncada).
5. **NÃO há geração fantasma** (ao contrário do c217): `n_geracoes ≡ |②| grupos ≡ |④| linhas` em 25/25. Aplicar o off-by-one do c217 aqui reprova 25/25 falsamente.
6. **`hard_stop` é estrutural, não excepcional** — 25/25 células, sempre em `fe == maxfe`. É o piso guloso sendo cortado no meio do lote, não anomalia.
7. **Término é `footer.termino`** (`'normal'`, 25/25); **não existe `motivo_parada`** no manifesto e o footer é **1 registro**, não 2. Usar `status` sozinho é o bug B1.
8. **Colisão float32 na ① (A12)** — 4 linhas em 10.856. **Dedup e joins do R4 sempre por `solution_id`, nunca pelo X armazenado** (regra pré-registrada em 2026-07-18).
9. **DTLZ4 não é re-verificável a partir da ① onde há underflow** — 23,4% dos objetivos do bloco init são exatamente 0,0 em float32 (menor não-nulo: 1,12e-44). Recomputar NDSort/dominância a partir da ① nesse problema produz números *trocados* em relação ao que o MATLAB decidiu em double.
10. **A fórmula `20D ÷ N_efetivo` do próprio manifesto subestima as gerações** (A24) — a real é `⌈(20D + n_dup)/2⌊N_ef/2⌋⌉`.
11. **③ vazia, `sigma_dict` ausente, sonda `nao_se_aplica` e 3 campos de timing NULL não são perda de dado** — são a assinatura, em cinco camadas independentes, de que o piso não tem surrogate (§3.2/DI-13.7). U3–U6, U8, U11 e U12 são N/A com regra citada.

---

*Insumos pré-computados usados SEM recomputo: `metricas_finais_f52c.csv` · `trajetorias/main_nsga3_*_42.json` (25) · `contrato_f52b.csv` (0 linhas nsga3) · `integridade_f52a.csv` (25 linhas `VAZIO`) · `tempo_f52d.csv` (máquina `vm3` 25/25) · `sonda_f52e.csv` (0 linhas nsga3, correto por desenho). Gates F5.1 e resultados F5.2 citados, não re-verificados.*

*Scripts da bateria e CSVs de evidência (único local de escrita, diretiva do autor) em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/nsga3/`:*
`bateria_nsga3.py` (censo/estrutura) · `bateria2_nsga3.py` (**lattice literal `UniformPoint` + aritmética de descendentes + seeding**) · `bateria3_seeding.py` (**recomputo exato D88 + Monte-Carlo do underflow DTLZ4**) · `bateria4_saude.py` (dinâmica, trajetórias, camadas) · `bateria5_doe.py` (**U2 bit-a-bit**) · `bateria6_regua.py` (papel de controle) · `bateria7_extras.py` (dedup, ponto ideal, nsga3×nsga2) · `bateria8_niching.py` (spacing/nicho + contrato).
*Evidência:* `ASPECTOS_nsga3.csv` (a tabela-resumo dos 24) · `censo_celulas.csv` · `celulas_aspectos.csv` · `lattice_uniformpoint.csv` · `seeding_D88.csv` · `seeding_D88_exato.csv` · `aritmetica_descendentes.csv` · `u2_doe_bit_a_bit.csv` · `doe_e_camadas.csv` · `dinamica_geracoes.csv` · `violacoes_ideal.csv` · `dedup_e_geracoes.csv` · `trajetorias_nsga3.csv` · `regua_pisos_nsga3.csv` · `pisos_igdplus.csv` · `sa_vs_melhor_piso.csv` · `spacing_pisos.csv` · `spacing_ranks.csv` · `contrato_manifesto.csv` · `gen_events.pkl` · `guards.pkl`.