# RELATÓRIO DE FIDELIDADE — `nsga3` · NSGA-III (piso online) · **validação T11** · 25 células s42 + smoke T11 · semente 42

**Analista de fidelidade `nsga3` · 2026-07-31 · protocolo v1.1 · corpus principal = `resultados_experimentos/nsga3/{problema}/42/` (25 células) · corpus da instrumentação = `evidencia_T11/smoke_matlab/.../nsga3/DTLZ2` (1 célula) · READ-ONLY · controle SEM artigo (gabarito = espec canônica do bundle `alg_pisos_online.md` + REGISTRO + o próprio fonte vendorizado do PlatEMO 4.15)**

> **Base de comparação:** `f5/relatorios_config/nsga3.md` (F5.3b, score 10/10, 24 aspectos, 0 classe-(3)).
> **O que mudou de método nesta passada:** além de re-medir os 24 aspectos da F5 sobre as mesmas 25 células, abri **duas fontes que a F5 não usou**: (i) a célula do smoke T11, que é o **mesmo `main/nsga3/DTLZ2/42`** — o que permitiu provar não-perturbação **bit-a-bit** sem precisar do par G-6 (o `nsga3` não tem sonda, logo não está em `g6_com/g6_sem`); (ii) o **fonte vendorizado do PlatEMO** e o `git status` do repo aninhado, que transformaram três declarações em medidas.

---

## 1. Ficha do mecanismo (condensada)

**NSGA-III puro (Deb & Jain, TEVC 2014), built-in do PlatEMO 4.15 vendorizado em `algorithms/_PlatEMO` @`b686ca2`, `algo_version = piso-NSGAIII-PlatEMO4.15`, ZERO patches por desenho.** Um dos **4 pisos ONLINE** — a *régua* (§3.2): responde "o surrogate compra alguma coisa, afinal?". Casamento por princípio de seleção: **NSGA-III → referência/indicador → espelha o e7 (EA-Indicador)**.

Mecânica confirmada no fonte (`NSGAIII.m:23-33`): lattice das-Dennis por `[Z,Problem.N] = UniformPoint(Problem.N,Problem.M)` **1× por run, fixo** (stock, não A-NSGA-III); `MatingPool = TournamentSelection(2,Problem.N,sum(max(0,cons),2))`; `OperatorGA` stock; `EnvironmentalSelection([Population,Offspring],Problem.N,Z,Zmin)` com `Zmin` **acumulado**.

**Divergências sancionadas nomeadas:** `maxFE = 31D−1` com hard-stop (**D21/D61**) · DoE `11D−1` do artefato (**D63**) com semeadura por NDSort+CrowdingDistance (**D88**) · `N = 20` cravado 2026-07-18 e **declarado PROVISÓRIO até o SUB-varN (DI-39** — cartão `40_subestudos/varredura_N_pisos` ainda ⬜ em `cards/INDEX.md:67`, inalterado pelo T11) · duplicata bit-exata = 0 FE, 1 slot (**D57/D89**) · operadores do **Balde C** (η_c=20, não os 30 do paper) · ③ vazia / série §17.6 vazia (**§3.2/DI-13.7**) · export float32 (**D53**).

**A idiossincrasia que governa metade do grid (DI-18/§6.3):** `UniformPoint(20,3)` → H₁=4 → **15 vetores** ⇒ em M=3 o `N efetivo = 15`.

**Escala auditada (s42):** 25 células · **413 gerações** · **7.200 descendentes** (7.028 de gerações completas + 172 do lote truncado) · **10.856 linhas na ①** (3.836 `init` + 7.020 `opt`) · **7.620 linhas na ②** · **1.213 registros no ⑥** (25 header + 25 `decomposicao` + 25 `seeding` + 413 `nsga3_gen` + 700 guards + 25 footer) · 25 hard-stops · 100% na `vm3`.

---

## 2. DISSECAÇÃO DOS ASPECTOS

Verificabilidade: **D**=direta · **DD**=direta-declarativa · **F**=verificada no FONTE vendorizado · **I**=indireta · **NV**=não-verificável. Classe: **(1)** conforme o método canônico · **(2)** desvio sancionado · **(3)** inexplicado 🎯 · **T** teto.

### 2.1 Tabela-resumo (29 aspectos)

| # | aspecto | classe | verif. | resultado-síntese |
|---|---|---|---|---|
| A1 | Orçamento FE=31D−1 + hard-stop exato | (2) D21/D61 | D | 25/25 `maxfe=fe_final=|①|`; `hard_stop` em `fe==maxfe` 25/25; smoke idem |
| A2 | DoE `11D−1` bit-a-bit + `doe_hash` | (2) D63/D88 | D | **`max|ΔX| = 0,0` em 25/25 + smoke**; hash sidecar≡manifesto 26/26 |
| A3 | `N=20` cravado, PROVISÓRIO (SUB-varN) | (2) §3.2/D65/DI-39 | DD | eco triplo 25/25; SUB-varN ⬜ **inalterado pelo T11** |
| A4 | `N efetivo = 15` em M=3 | (2) DI-18/§6.3 | D | 15 nas 6 células M=3 · 20 nas 19 M=2 · **413/413 gerações** |
| A5 | Lattice `UniformPoint` NBI ≡ PlatEMO | (1) | **D — joia** | **`max|ΔW| = 0,0` em 25/25**; s42×smoke também 0,0 |
| A6 | Vetores fixos 1×/run (≠ A-NSGA-III) | (1) | D | 1 registro `decomposicao` em 25/25 + smoke |
| A7 | Semeadura D88 recomputada | (2) D88 | **D — joia** | **conjunto IDÊNTICO 24/25** (exceção DTLZ4, underflow); smoke fecha |
| A8 | `\|pop\|` ≡ `N_efetivo` | (1) | D+F | 413/413 gerações; `EnvironmentalSelection.m:1` devolve exatamente N |
| A9 | Descendentes = `2·⌊N/2⌋` | (1) | **D+F** | moda 14 (M=3)/20 (M=2) 25/25 · **`OperatorGA.m:56-58` confirma** |
| A10 | Aritmética ①×②×⑥ fecha | (1) | **D — joia** | **25/25 exato**: 7.028 = 6.849 FE + 179 dup |
| A11 | Dedup D57/D89 + modelo do operador | (2) D57/D89 | **D+F** | **2,55% medido × 1,91% previsto do fonte**, r=0,81 por célula |
| A12 | Colisão float32 no export da ① | (2) armadilha + **regra 11 nova** | D | 4 linhas em 10.856 (0,037%) |
| A13 | Arranque: `N_ef + 1` cache-hits | (2) D57 | D | 25/25 exato, com `N_ef` sids distintos |
| A14 | Sem geração fantasma | (1) | D | `n_ger ≡ |eventos| ≡ grupos(②) ≡ linhas(④)` 25/25 |
| A15 | Operadores Balde C (SBX 1/20 + PM 1/D/20) | (2) Balde C | **D+F** (era DD) | string 25/25 + **`OperatorGA.m:48 deal(1,20,1,20)`** |
| A16 | Seleção ambiental por nicho | **T** | I+F | não exportada; spacing rank **1,67/4** em M=3; fonte `EnvironmentalSelection.m:55-83` |
| A17 | Normalização / `Zmin` acumulado | **T** | NV+F | não exportado; `NSGAIII.m:25,31` confirma `Zmin` acumulado |
| A18 | Ideal/nadir: semântica de pop corrente | (1) | D | `ideal≡f_best` 25/25; **12/898 não-monotonias, 10 delas ≤1e-17** ⚠ *auto-errata* |
| A19 | Ausência total de surrogate (agora **6** camadas) | (2) §3.2/DI-13.7 | D | ③ 0 linhas 25/25 + `sigma_dict` declarado no smoke |
| A20 | Timing: ④≡⑥, Σ④ ≤ total | (2) §17.6/DI-13.10 | D | `max|Δt| = 1,3e-8`; Σ④ = 20,97 s = **17,0%** do wall |
| A21 | U9 guards ⑥ ≡ `cache_hits` ⑤ | (1) | D | **675 ≡ 675**, célula a célula |
| A22 | Contrato do ⑤/⑥ | (1) | D | **0 linhas nsga3** em `contrato_f52b`; footer único; `termino='normal'` |
| A23 | 🆕 Elo código→log (`repo_hash`) | (2) **T11/I-09** | D | s42 vazio 25/25 → smoke `195f64ed…` = **commit REAL, 45 min antes do run** |
| A24 | 🆕 Fórmula de gerações derivadas | (2) doc | D | T11 corrigiu **0/25 → 25/25**; mas o rótulo "EMERGENTE" é **REFUTADO (100/100)** |
| A25 | 🆕 `sigma_dict` DECLARADO (T11-P0/G-7) | (2) G-7 | D | ausente 25/25 na s42; presente **e verdadeiro** no smoke |
| A26 | 🆕 `campanha_id` + schema v2 (B-03) | (2) B-03 | D | ausente/v1 25/25; `t11-smoke-195f64e`/v2 no smoke |
| A27 | 🆕 `patches: NENHUM` agora **MEDIDO** | (1) | **D** (sai do T) | `git status` do PlatEMO: **12 sujos, 0 em NSGA-III/UniformPoint/NDSort/CD/OperatorGA** |
| A28 | 🆕 Mating pool uniformemente aleatório | (1) | **F** | `TournamentSelection.m:26-29` com `cons≡0` ⇒ `randi` puro (NSGA-III stock) |
| A29 | 🆕 Instrumentação T11 **não perturba a busca** | (1) | **D** | **sha256 da ① e da ② IDÊNTICOS** s42 × smoke |

### 2.2 Blocos narrativos

---

**A1 — Orçamento FE = 31D−1 com hard-stop exato.**
*(a) Canônico:* o NSGA-III termina por `maxFE` do `Problem`; não tem orçamento próprio. *(b) Espec:* `maxFE = 31D−1` (§5.1) com hard-stop no wrapper de FE (D21/D61) — o `obj.FE` nativo do PlatEMO **não** governa o término. *(c) Observado:* `man.maxfe == man.fe_final == len(①) == 31D−1` em **25/25**, com `fe_index ≡ arange(n)` denso 0-based em **25/25** (`t11_b5_mecanismo.py`, colunas `A1_maxfe_ok`/`A1_feindex_denso`). Valores: 61 · 216 · 309 · 371 · 619 · 681 · 929. O guard `hard_stop` dispara em `fe == maxfe` em **25/25** — estrutural, não excepcional. No smoke (DTLZ2, D=12): idem, `hard_stop` em `fe=371`. *(d) Mecanismo:* orçamento e (população × gerações) são amarrados; `20D mod n_off ≠ 0` nas 25 células ⇒ o hard-stop sempre corta um lote pela metade (o resto `maxfe − fe_última` é `≤ n_off` em 25/25). *(e)* **(2) D21/D61 · D.**

---

**A2 — DoE `11D−1` bit-a-bit, e agora também no smoke.**
*(a) Canônico:* inicialização aleatória interna. *(b) Espec:* DoE compartilhado (§5.2/D63) lido de `data/doe/{prob}/doe_{prob}_42.parquet`, nunca regenerado — é o que torna a régua uma régua. *(c) Observado:* comparei o bloco `fase=='init'` da ① contra o artefato nas 25 células **e** na do smoke: **`max|ΔX| = 0,0` em 26/26**, com a **ordem** preservada (o join posicional é legítimo). `doe_hash` do sidecar ≡ manifesto em 26/26 (DTLZ2 `e9e359a6…`). Contagens exatas: `init == 11D−1` e `opt == 20D` em 26/26 (Σ = 3.836 + 7.020 = 10.856). *(d) Mecanismo:* `run_piso` pré-avalia o artefato pelo `bud` na ordem do arquivo (`experiment.m:2419-2423`) e o `assert bud.fe == n_init` trava qualquer desvio. *(e)* **(2) D63/D88 · D.**

---

**A3 — `N = 20` cravado, e ainda provisório.**
*(a) Canônico:* Deb & Jain usam N = |lattice| (91, 210…) com dezenas de milhares de FE. *(b) Espec:* protocolo Knowles/ParEGO — sob orçamento minúsculo o piso se calibra **reduzindo a população**; N=20 cravado em 2026-07-18 com justificativa de 4 pontos. *(c) Observado:* `N_nominal=20` em 25/25 manifestos + 25/25 headers (`N_origem` com o texto da decisão) + 25/25 footers; idem no smoke. *(d)* Config-echo puro. *(e)* **(2) §3.2/D65/DI-39 · DD.**
⚠ **A pendência de pré-registro NÃO foi tocada pelo T11.** A DI-39 (2026-07-25) declarou o N=20 **provisório** e manteve o SUB-varN como **pré-requisito do M8**; `cards/INDEX.md:67` continua ⬜. Note a contradição documental viva: a DI-32/A2 (2026-07-23) diz "N=20 = DEFINITIVO; SUB-varN vira opcional do M11" e a DI-39, **posterior**, o reverte. Pela precedência cronológica do REGISTRO vale a DI-39 — **se a varredura eleger N≠20, estas 25 células são descartadas**. Item para a torre: o bundle e o REGISTRO precisam concordar antes do M8.

---

**A4 — `N efetivo = 15` em M=3, medido em 413 gerações.**
*(a) Canônico:* `NSGAIII.m:23` é literalmente `[Z,Problem.N] = UniformPoint(Problem.N,Problem.M)` — **reatribui N**. Comportamento stock, não patch. *(b) Espec:* §6.3 ⟦v5.2.1⟧ pré-registra a consequência. *(c) Observado:* `n_pop` do ⑥ e `groupby('geracao').size()` da ② concordam e são **constantes por célula**: 15 nas 6 células M=3, 20 nas 19 M=2, `nunique==1` em 25/25 (`A8_npop_eq_Nef` 25/25, `A8_grupos2_eq_Nef` 25/25). Consequência de orçamento medida: DTLZ2/3/4 **18 gerações** contra 13 do nsga2; DTLZ7 33 vs 23; MMF16_20 30 vs 21 — ~1,4× mais gerações com 25% menos população. *(d)* O lattice das-Dennis só existe em `C(H+M−1,M−1)`; em M=3 as opções são 6/10/15/21 e o PlatEMO arredonda para baixo. *(e)* **(2) DI-18/§6.3 · D. Confirmada exatamente como pré-registrada.**

---

**A5 — JOIA nº 1: identidade fechada do lattice.**
*(a) Canônico:* Deb & Jain §IV-A, lattice das-Dennis; PlatEMO faz `H1=1; while nchoosek(H1+M,M−1)<=N, H1=H1+1; end` + gerador combinatório + `W = max(W,1e-6)`. *(b) Espec:* nenhuma mudança — mas o run **loga a matriz inteira** no registro `decomposicao`, o que converte teto em prova. *(c) Observado:* traduzi literalmente o `UniformPoint(N,M,'NBI')` para Python (`t11_b5_mecanismo.py::uniformpoint_nbi`) e comparei **linha a linha na ordem gravada**: **`max|ΔW| = 0,0` em 25/25**. H₁=19 (M=2, componentes `k/19`) e H₁=4 (M=3, componentes `{1e-6; 0,25; 0,5; 0,75; 1}`). `N_lattice` logado ≡ `N_efetivo` ≡ `|pop|` em 25/25. **Novo nesta passada:** a matriz do smoke é **bit-idêntica** à da s42 (`max|ΔW| = 0,0` entre as duas). *(d)* O lattice é determinístico e independe de semente — ou bate exato, ou não é o NSGA-III. Bateu. *(e)* **(1) · D.**

---

**A6 — Vetores fixos: é o NSGA-III stock, não o A-NSGA-III.**
*(a) Canônico:* o NSGA-III original mantém `Z` fixo; a variante adaptativa (Jain & Deb, parte II) injeta vetores em fronts degenerados. Confundir os dois é o erro clássico. *(b) Espec:* `patches: NENHUM`. *(c) Observado:* exatamente **1** registro `decomposicao` por run em 25/25 + smoke; `N_lattice` invariante nas 413 gerações; nenhum evento de re-geração. Se houvesse adaptação, o piso M=3 (15 vetores para 15 indivíduos em DTLZ1/DTLZ3/DTLZ7) teria disparado injeção. **Fonte:** `NSGAIII.m:23` está **fora** do `while`, e o arquivo está limpo no `git status` (A27). *(d)* Prova negativa por instrumentação posicionada antes do `Solve`. *(e)* **(1) · D.**

---

**A7 — JOIA nº 2: a semeadura D88, recomputada do zero.**
*(a) Canônico:* nada — o NSGA-III não prescreve semeadura por DoE. *(b) Espec:* §3.2 + **D88** — os N melhores das `11D−1` por não-dominância, com desempate por **crowding distance** e, no empate final, por índice; racional = comparabilidade (se o piso partisse de outra amostra, a régua deixaria de medir só a seleção). *(c) Observado:* reimplementei NDSort (front-filling) + CrowdingDistance + desempate por índice e comparei o **conjunto de `solution_id` da geração 1 da ②**: **idêntico em 24/25**, incluindo os casos em que a frente-1 excede a população (DTLZ2 `n_frente1=40` > 15). Os `solution_id` da geração 1 caem todos em `[0, 11D−1)` em 25/25 — a população inicial é **estritamente** DoE. No smoke, o mesmo recomputo fecha (`A7_conjunto_igual=1`, `n_frentes` 6≡6, `n_frente1` 40≡40). *(d)* NDSort+CD são determinísticos e livres de semente; coincidir bit-a-bit em 24 problemas independentes prova que o critério implementado é o da D88. *(e)* **(2) D88 · D.**

> **DTLZ4 — a 25ª célula, re-medida.** O log diz `n_frentes=7, n_frente1=23`; meu recomputo sobre a ① diz **23 e 7** — *trocados*. Re-medi a causa: dos **393 valores objetivo do bloco init, 92 são exatamente 0,0 (23,4%)**, 16 são denormais (<1,18e-38), 72 estão abaixo de 1e-20 e o menor não-nulo é **1e-45**. Em double (o que o MATLAB ordenou) esses valores são positivos e distintos e servem de desempate fino ⇒ frente-1 grande; em float32 (o que a ① grava, D53) colapsam em 0,0 ⇒ a dominância vira comparação por f₀ e a cadeia de frentes explode. **Isto é exatamente a `regra 11` que o T11 acrescentou ao `CONTRATO_DE_DADOS.md` §10** ("dominância sobre ① ou ⑦ é LOSSY"). Classe **(2) com verificabilidade rebaixada a indireta nessa única célula** — mecanismo provado, não desvio.

---

**A8/A9 — População constante e a truncagem `2⌊N/2⌋`, agora verificadas NO FONTE.**
*(a) Canônico:* o pseudocódigo do NSGA-III gera N descendentes e a seleção ambiental devolve N. *(b) Espec:* operadores stock do Balde C. *(c) Observado:* `|pop|` constante ≡ `N_ef` em 413/413 gerações, gerações densas `1..n` sem buracos, 100% dos `solution_id` da ② válidos na ①. A **taxa de descendentes**, medida por `ΔFE + cache-hits do intervalo`, tem moda **14 em M=3 e 20 em M=2 — nunca 15** (25/25; os desvios ±1 que aparecem em 7 células são artefato de atribuição de um cache-hit exatamente na fronteira do intervalo e **cancelam na soma**, que fecha exata em A10). *(d) Mecanismo — agora lido no fonte, não inferido:* `OperatorGA.m:56-58` faz `Parent1 = Parent(1:floor(end/2),:)`, `Parent2 = Parent(floor(end/2)+1:floor(end/2)*2,:)`, `Offspring = zeros(2*size(Parent1,1),·)` — com 15 pais usa 7+7 e **descarta o 15º**. *(e)* **(1) — fidelidade ao código canônico · D+F.** Na F5 este item era medida + hipótese; agora é medida + fonte.

---

**A10 — JOIA nº 3: a aritmética entre camadas fecha exata.**
*(a) Canônico:* cada descendente consome 1 avaliação. *(b) Espec:* **D89** — duplicata bit-exata não gasta FE, gasta o slot; logo `descendentes = FE_infill + cache_hits_de_descendente`. *(c) Observado:* para cada célula, `off_full = (n_ger−1)·2⌊N/2⌋`, `fe_cons = fe(última) − init`, `dup = |cache_hit|` no intervalo `(init, fe_última]` — **`off_full − fe_cons == dup` fecha em 25/25**. Agregado: **7.028 = 6.849 + 179**; somando os 172 do lote truncado, **7.200 descendentes**. Smoke (DTLZ2): 238 = 230 + 8 ✔. *(d)* Três camadas escritas por caminhos independentes (⑥ por evento, ① por avaliação, ⑤ por contador) convergindo ao mesmo número em 25 problemas de D=2..30 só é possível se wrapper de FE, dedup e laço evolutivo estiverem os três corretos. *(e)* **(1) · D.**

---

**A11 — Dedup D57/D89: 2,55% medido contra 1,91% PREVISTO pelo fonte.** 🆕
*(a) Canônico:* nenhum MOEA stock deduplica. *(b) Espec:* D57 + **D89** (decisão do autor: "o catálogo ① torna re-consulta gratuita, como na prática real de otimização cara"); o bundle §3.2-5 pré-registra o efeito colateral (23% no MOEA/D com `T=2`). *(c) Observado:* 179 duplicatas de descendente em 7.028 = **2,55%** (mín. 1 em BBOB_F17/F49/MMF11_L/MMF4, máx. 17 em ZDT1, mediana 7). **O que é novo:** derivei a taxa *a priori* do fonte — o mating pool é `randi(N,2,N)` com aptidão toda-zero (⇒ pais uniformes **com reposição**, A28), o pareamento é posicional, pais idênticos fazem o SBX devolver os dois filhos ≡ pai, e o PM mantém o filho intacto com probabilidade `(1−1/D)^D`. Logo `E[dup] = 2⌊N/2⌋ · (1/N) · (1−1/D)^D`. **Previsto 1,91% × medido 2,55%**, com a ordenação M=3 (2,81% medido / 2,36% previsto) > M=2 (2,46% / 1,77%) **reproduzida**, e correlação por célula **r = 0,811** (`t11_b9_dedup_modelo.py`). *(d)* O excedente (2,55 − 1,91) é o segundo canal: filhos do SBX caindo sobre pontos já catalogados por clamp de bounds / convergência de canto. *(e)* **(2) D57/D89 · D+F.** A duplicata do `nsga3` deixa de ser "assinatura empírica" e passa a ser **quantidade prevista pelo operador stock** — e continua a 9× de distância dos 23% do MOEA/D, porque este não tem vizinhança `T=2` reciclando dois pais.

---

**A12 — Colisão float32 na ①, e a regra que o T11 escreveu.**
*(a)* n/a. *(b) Espec:* export float32 sem arredondamento (D53); dedup e orçamento em **double**. Armadilha pré-registrada em 2026-07-18. *(c) Observado:* varri as 10.856 linhas procurando X bit-idênticos com `solution_id` distintos: **4 ocorrências (0,037%)**, concentradas em DTLZ4 e em D=2; zero nas 21 células restantes; **zero no smoke**. Se fossem falhas de dedup teriam virado cache-hit e não consumido FE — consumiram, logo os doubles diferiam. *(d)* SBX/PM produzem doubles a ~1e-9 do pai; float32 tem ~7 dígitos. *(e)* **(2) · D.** 🆕 **O T11 generalizou este achado em doutrina:** `CONTRATO_DE_DADOS.md` §10 **regra 11** ("dominância sobre ① ou ⑦ é LOSSY; diferenças abaixo da resolução do float32 não são conclusivas; onde a distinção importa use `solution_id`"). É exatamente o que a F5 do `nsga3` mediu em A12 e no DTLZ4 — a regra nova **cobre** este config e o join do R4 fica protegido.

---

**A13 — O arranque: `N_ef + 1` cache-hits, em 25/25.**
*(a)* n/a. *(b) Espec:* o manifesto declara que os N pontos re-adicionados entram como cache-hit (0 FE). *(c) Observado:* em `fe == init` há **sempre `N_ef+1`** guards `cache_hit` (16 em M=3, 21 em M=2) mas apenas `N_ef` `solution_id` **distintos** — 1 hit excedente sistemático (a repetição de um sid já presente). 25/25 + smoke (16 hits, 15 sids). *(d)* Assinatura do arranque do wrapper: o probe do construtor (`Initialization(1)`) pega `Xsel(1,:)`, já em cache. *(e)* **(2) D57 · D.** **Armadilha:** tratar os 495 hits de semeadura como duplicatas do algoritmo superestima a taxa em **3,8×** (675 vs 179).

---

**A14 — Não existe geração fantasma.**
*(c) Observado:* o evento `nsga3_gen` é emitido **no início** da geração (`fe` da geração 1 é exatamente `init` em 25/25), logo a geração truncada pelo hard-stop **já teve snapshot**: `n_geracoes(⑤) == |eventos| == grupos(②) == linhas(④)` em **25/25** + smoke. *(e)* **(1) · D.** **Armadilha positiva:** o off-by-one do c217 **não** se aplica aqui.

---

**A15 — Operadores do Balde C: de declarativo a verificado no fonte.**
*(a) Canônico:* Deb & Jain usam SBX `η_c=30, p_c=1` e PM `η_m=20, p_m=1/D`. *(b) Espec:* **Balde C** — `SBX proC=1 dis_c=20 + PM proM=1 dis_m=20`; o desvio de η_c (20 vs 30) é **deliberado e transversal**: isolar o ganho do surrogate exige operadores idênticos aos dos SA-MOEA, não idênticos ao paper do piso. *(c) Observado:* a string é idêntica em 25/25 headers e em `params.operadores` de 26/26 manifestos. **Novo:** `OperatorGA.m:48` traz `[proC,disC,proM,disM] = deal(1,20,1,20)` como default e o arquivo está **limpo** no `git status` (A27); `GAreal` faz `Site = rand(2N,D) < proM/D`, i.e. `proM=1` ⇒ taxa por variável **1/D**, exatamente a prescrição do paper. *(d)* O eco do log agora tem um lastro de fonte. *(e)* **(2) Balde C · D+F** (era DD na F5 — **upgrade de verificabilidade**).

---

**A16 — A seleção por nicho: o teto que continua teto (mas com o código provado).**
*(a) Canônico:* §IV-C–E — normalização por pontos extremos + ASF, associação por distância perpendicular ao vetor mais próximo, e **niche-preserving** (escolher da última frente o indivíduo do nicho menos povoado). É o que distingue NSGA-III de NSGA-II. *(b) Espec:* nada muda (stock). *(c) Observado:* a associação por indivíduo **não é exportada** (a ② só tem `solution_id`) ⇒ **T**. A assinatura indireta: rank médio de `spacing` entre os 4 pisos = **nsga3 2,40 · smsemoa 2,12 · nsga2 2,20 · moead 3,28**, mas o corte por M é decisivo — **1,67/4 em M=3** contra 2,63 em M=2. E `|F1| == |pop|` (regime em que só o nicho decide) ocorre em **77,2% das gerações M=3** contra **19,5% em M=2** (re-medido: `g7_sentinela.csv`). *(d)* Em M=2 o crowding do NSGA-II já é quase ótimo; em M=3, com 15 nichos para 15 indivíduos, o nicho é o único critério ativo — e é lá que o `nsga3` lidera em uniformidade. *(e)* **T (observabilidade) · I.** ⚠ **Refino desta passada:** o *código* deixou de ser dúvida — `EnvironmentalSelection.m:38-53` (Extreme+Hyperplane+normalização), `:55-63` (associação e `rho`), `:63-83` (niche-preserving) estão presentes e o arquivo é **byte-idêntico ao upstream** `b686ca2` (A27). O teto é sobre *o que os nossos runs exportam*, não sobre *que código rodou*.

---

**A17 — Normalização interna e `Zmin` acumulado.**
*(a)/(b)* `EnvironmentalSelection.m:32` faz `PopObj = [PopObj1;PopObj2] − Zmin`, com `Zmin` acumulado ao longo do run (`NSGAIII.m:25,31`). *(c)* Nada disso é exportado — o run loga o `ideal` da **população corrente**. *(e)* **T · NV+F.** Registrado para eventual re-run instrumentado; não afeta nenhum outro aspecto — e é a chave de leitura de A18.

---

**A18 — Ideal/nadir: 12 não-monotonias em 898, e por que 10 delas são ruído de underflow.** ⚠ *auto-errata contra a F5*
*(a)/(b)* Instrumentação nossa (`piso_instrument.m:54-68`): cada evento carrega `f_best`, `ideal`, `nadir_pop`, `nadir_front1`. *(c) Observado:* `ideal ≡ f_best` bit-a-bit em **25/25** (são o mesmo vetor emitido sob dois nomes, por decisão de contrato). Sobre a monotonia, **corrijo o número da F5**: contando *toda* piora estrita, são **12 em 898 transições-objetivo (1,34%)**, não 2. Mas a distribuição é decisiva: **só 2 excedem 1e-6** (DTLZ1 g7→g8 obj 2: 0,0 → 0,0400; DTLZ2 g2→g3 obj 0: 3,01e-4 → 1,31e-3) e as **10 restantes estão em 1e-17 ou abaixo** (7 delas em DTLZ4, com deltas de até 6,5e-194). `nadir ≥ ideal` em 100%. O smoke reproduz exatamente as 3 de DTLZ2 (`ideal_nao_monotonias.csv`). *(d)* O `ideal` logado é o mínimo da **população corrente**; a seleção do NSGA-III é *niche-preserving*, não *extreme-preserving-por-objetivo* — ela pode descartar o detentor do mínimo de um objetivo se o nicho estiver superpovoado. O `Zmin` **interno** (A17) é monotônico por construção e é outra grandeza; ler a instrumentação como se fosse o `Zmin` produz falso-alarme. As 10 micro-pioras são o mesmo underflow/denormal do DTLZ4 batendo na leitura float32. *(e)* **(1) · D.** A F5 reportou "2/898" porque aplicou implicitamente um piso de magnitude; **o número honesto é 12/898, dos quais 2 são materiais** — a conclusão não muda, a precisão sim.

---

**A19 — Ausência total de surrogate, agora provada em SEIS camadas.**
*(b) Espec:* "Mesmos hooks/export (tabela ③ vazia; série §17.6 vazia)" (§3.2); o arquivo ③ existe vazio por completude (DI-13.7). *(c) Observado, 25/25 + smoke:* (i) ③ com **0 linhas** (schema completo presente); (ii) `fit_series == []`; (iii) `sonda = {status:"nao_se_aplica", motivo:"piso ONLINE = MOEA puro…", n_blocos:0, n_linhas:0}`; (iv) `header.surrogate = false` e `header.piso = true`; (v) `timing.tempo_fit_surrogate_s = tempo_busca_s = tempo_pred_sonda_s = null`; (vi) 🆕 **`sigma_dict` declarado** (A25). Consequência de contrato: `integridade_f52a.csv` traz 25 linhas `VAZIO` (por desenho) e `sonda_f52e.csv` tem **0 linhas nsga3** — ambos corretos. **U3, U4, U5, U6, U8, U11 e U12 são N/A por desenho**, com regra citada; a **regra 12 do CONTRATO é vacuamente satisfeita** (não há `sonda` nem `sonda_estratificada` a separar). *(e)* **(2) §3.2/DI-13.7 · D.**

---

**A20 — Timing: o ④ é o filme do laço, e fecha com o ⑥.**
*(c) Observado:* ④ com `n_geracoes` linhas em 25/25 (413), `tempo_fit_s`/`tempo_busca_s`/`tempo_pred_sonda_s` **NaN em 413/413** (U7 é vacuamente satisfeita, então a substituo por duas mais fortes): **(i)** `④.tempo_geracao_s ≡ ⑥.nsga3_gen.tempo_geracao_s` com **`max|Δ| = 1,3e-8`** nas 25 células (7,3e-9 no smoke); **(ii)** `Σ④ ≤ timing.tempo_total_s` em 25/25. Agregados: total 123,7 s, Σ④ = **20,97 s (17,0%)**, `tempo_aval_real` = 6,62 s (5,4%) — os 83% restantes são arranque do MATLAB + I/O. *(d)* O piso é tão barato que o custo fixo do processo domina — o que valida quantitativamente o "custo trivial (não treina GP)" do bundle. *(e)* **(2) §17.6/DI-13.10 · D.** 🆕 Nota T11 (I-3): `tempo_aval_real_s` é **não-nulo já na s42** do `nsga3` (0,112 s em DTLZ2) e continua não-nulo no smoke (0,0335 s) — este config nunca esteve na lacuna.

---

**A21/A22 — U9 e contrato: o config mais limpo do lote, com 3 buracos que o T11 fechou.**
*(c) Observado:* `man.cache_hits == |guards cache_hit|` célula a célula em 25/25, total **675 ≡ 675**; `|hard_stop| == 1` com `fe == maxfe` em 25/25; os únicos dois nomes de guard são `cache_hit` e `hard_stop` (`fallback_ativado=false`, `n_retries=0` em 25/25). `contrato_f52b.csv` tem **0 linhas nsga3**. O ⑤ tem `params` com **12 chaves** em 26/26; footer é **1 registro** (não 2) e o término vive em **`footer.termino='normal'`** — `motivo_parada` **não existe** (usar `status` sozinho é o bug B1). 🆕 **O que a T11 mudou:** aferi eu mesmo o `quinto_obrigatorio` do `contrato_61.json` (`params, sigma_dict, timing, doe_hash, campanha_id, repo_hash`): a s42 entrega **3/6** (falta `sigma_dict`, falta `campanha_id`, `repo_hash` vazio) e o smoke entrega **6/6**. Rodei os gates de proveniência sobre o smoke: `G-2 OK · G-3 OK · G-4 6/6 camadas · G-7 ⑥ 3/3 campos · ⑤ 6/6 chaves · B-15 OK` (G-1 n/a, sem linhas marcadas na ③). *(e)* **(1) · D.**

---

**A23 — 🆕 O elo código→log: o teto que o T11 derrubou (quase todo).**
*(a)/(b)* D80 exige que o run diga qual código o produziu. *(c) Observado:* na s42, `repo_hash = ""` em **25/25** — a F5 registrou isto como **T**. No smoke, `repo_hash = 195f64ed0a69dc3f6c64c66912076e243be90c49`. **Verifiquei que é real:** `git cat-file -t` devolve `commit`, e o commit é `[T11-B3/T5] relatório de conformidade dos 24 configs…` de **30/07 18:00 −0300**, enquanto o smoke gravou `created_at = 2026-07-30T21:45:23Z` = **18:45 −0300** — o carimbo aponta o HEAD vigente 45 min antes do run, sem staleness (havia commits às 20:02 e 20:12 locais, **posteriores** ao run). Implementação: `src/manifest.py:64-84` (`git rev-parse HEAD`) e `src/experiment.m:3080` no lado MATLAB. *(d)* A ausência anterior era transversal (666/666 células da rodada-42). *(e)* **(2) T11/I-09 · D.**
⚠ **Resíduo medido, e é o mesmo do repo inteiro:** `repo_hash_corrente()` é `git rev-parse HEAD` **sem detecção de árvore suja** — não há `--dirty`, `git status --porcelain` nem content-hash do repo-mãe no ⑤. Um HEAD limpo com working tree modificado produz o mesmo carimbo. Para o `nsga3` isso é **compensado** por A27 (o lacre de conteúdo do PlatEMO), mas o buraco existe para o código do harness.

---

**A24 — 🆕 A fórmula de gerações: o T11 corrigiu o número e errou o rótulo. E eu re-meço as duas versões.**
*(a)/(b)* A F5 apontou que a string `geracoes_derivadas = "20D ÷ N_efetivo"` do manifesto estava errada e **recomendou corrigi-la antes do M8** — foi o único item que o relatório mandou à torre. *(c) O que o T11 fez:* reescreveu a string (`src/experiment.m:2516-2527`), citando "I-13/A24 corrigido contra o dado em 2026-07-30", e a ERRATA 5 do handoff afirma: *"`⌈…⌉` acerta 0/112; a string antiga acerta 2/112; `floor(…)` 103/112 ⇒ **`n_geracoes` é EMERGENTE, não fechada**"*. **Re-medi, como o handoff manda** (`t11_b1/b2/b3`):

| candidata | `n_dup` usado | acerta (nsga3, 25) | acerta (4 pisos, 100) |
|---|---|---|---|
| string antiga `20D ÷ N_ef` | — | **0/25** | — |
| `⌈(20D + n_dup)/2⌊N_ef/2⌋⌉` (A24 da F5) | **duplicatas de DESCENDENTE** | **25/25** | 72/100 |
| `⌊(20D + n_dup)/2⌊N_ef/2⌋⌋` (T11) | **`cache_hits` TOTAL do ⑤** | **25/25** | 93/100 |
| **`⌊(20D + dup_desc)/n_off⌋ + 1`, `n_off` = 2⌊N_ef/2⌋ (GA pareado) ou `N_ef` (MOEA/D)** | duplicatas de descendente | **25/25** | **100/100** |

**Conclusões medidas.** (i) A errata 5 está **certa sobre a string que testou e errada sobre a conclusão**: ela substituiu na minha fórmula um `n_dup` diferente do que eu havia definido — o `cache_hits` do manifesto **inclui as `N_ef+1` do bloco de semeadura** (A13), que não são descendentes. Com o `n_dup` certo, o teto acerta 25/25. (ii) A afirmação **"`n_geracoes` é EMERGENTE, não fechada" é REFUTADA**: a forma fechada `⌊(20D + dup_desc)/n_off⌋ + 1` acerta **100/100 células dos 4 pisos**, incluindo as 9 que a fórmula do T11 erra (1 no nsga2 e 6 no moead — este último porque o MOEA/D gera **1 prole por subproblema (N_ef)** e não pares, o que o `2⌊N_ef/2⌋` da string não captura). O `+1` é a geração que o snapshot-no-início (A14) sempre registra antes do hard-stop. (iii) **Para o `nsga3` a string nova é numericamente exata (25/25)** e o conselho final dela — *"o valor REAL de cada run está em `n_geracoes`; não derive, LEIA"* — é seguro. *(e)* **(2) — refinamento documental · D.** **Ação para a torre:** trocar "EMERGENTE, não fechada" por a forma fechada acima (ou apagar a meta-alegação); é a única frase do manifesto do `nsga3` que a dissertação lerá e que está errada.

---

**A25 — 🆕 `sigma_dict` DECLARADO: a correção G-7/T11-P0, e ela NÃO é o padrão do c217.**
*(a)/(b)* A DEF-C4 chama o `sigma_dict` de "leitura OBRIGATÓRIA antes de usar a ③" e o CONTRATO §5 o lista como obrigatório; omiti-lo deixava **112 células de piso** (28 × 4) sem a chave, e quem itera as chaves do §5 não distingue "não se aplica" de "esqueceram" (`contrato_61.json:pendencias_medidas.quinto.sigma_dict`). *(c) Observado:* ausente em **25/25** manifestos da s42; presente no smoke com `{status:"nao_se_aplica", motivo:"piso ONLINE = MOEA puro: a ③ existe (contrato de camadas) mas nasce VAZIA — não há modelo cujas colunas descrever", terceira:"0 linhas por desenho"}` (`experiment.m:2507-2511`). *(d) A pergunta que o mandato manda fazer — "campo presente, dado sentinela?":* **não.** Testei a declaração contra o dado: a ③ do smoke tem de fato **0 linhas**, `fit_series` é `[]`, os 3 campos de timing de surrogate são `null`. A declaração é **verdadeira e checável**, ao contrário do `pmid_ids = [-1,-1,-1,-1,-1]` do c217 (campo presente, dado inexistente). É o mesmo idioma do `tempo_fit_s = NULL` da DI-13.2 e do bloco `sonda` do próprio piso: **declarar a não-aplicabilidade é informação; omitir é silêncio.** *(e)* **(2) G-7 · D.**
⚠ **Resíduo:** não achei **nenhum teste** que exija o `sigma_dict` do piso **ONLINE** (`grep -rn "nao_se_aplica" tests/*.py` não retorna nada; `tests/test_piso_off.py:112` cobre o piso **OFFLINE**, outro config). A correção está guardada só pelo gate G-7 (`contrato_61.json` + `gates_proveniencia.py:426`) e pela evidência do smoke — e o G-7 depende do artefato, que é editável. Nota menor, não defeito.

---

**A26 — 🆕 `campanha_id` + schema v2.**
*(b)* B-03 — o carimbo distingue célula da campanha de célula de smoke/pré-retrofit; `is_run_done` exige `campanha_id` (`src/manifest.py:249-250`), e sem ele as stale de semente 0 eram absorvidas como prontas. *(c) Observado:* ausente e `schema_version=1` em 25/25 na s42; `campanha_id = "t11-smoke-195f64e"` e `schema_version=2` no smoke (`experiment.m:3067-3068`). *(d)* Consequência direta e **desejada** para este config: as 25 células da s42 são v1 ⇒ **não contam como prontas** na campanha M8 e serão re-rodadas — o que já aconteceria de todo modo pela DI-39 e custa segundos (0,034 h-core). *(e)* **(2) B-03 · D.**
⚠ **Risco operacional medido (é o D-G do handoff):** sem a env `UA_DD_SAEA_CAMPANHA_ID`, o default é `{commit12}_{data UTC}` — que **muda à meia-noite UTC** (`manifest.py:110`). Os 4 pisos rodam em segundos e em lote; um lote atravessando a virada de dia recebe **dois `campanha_id` diferentes** e o `is_run_done` cruzado entre máquinas quebra. Para o `nsga3` o dano é desprezível (re-roda em segundos), mas a env precisa ser exportada nas 4 máquinas.

---

**A27 — 🆕 `patches: NENHUM` deixou de ser declaração e virou MEDIDA.** 🎯 *(o item que mais mudou desde a F5)*
*(a)/(b)* O piso inteiro repousa sobre uma única afirmação: *"este é o NSGA-III do PlatEMO 4.15 sem modificação"* (`algo_version` + `params.patches`). Na F5 isso era **T** (A23): não havia hash de repositório nem `anchors.json` (não há patch a ancorar). *(c) Observado, em três medidas independentes:*
1. **O `preflight` passou a conferir o PlatEMO.** `scripts/preflight.py:112-121` traz o conserto de 2026-07-30 e o comentário é explícito: *o PlatEMO **faltava no `dir_map`**, então o `continue` o pulava e ele **nunca era conferido**; pior, ele tem `.git` próprio e o pin é por commit, mas ninguém commita no repo aninhado — os 12 arquivos patchados vivem como working-tree changes, então o pin por commit atesta a BASE e nunca o ESTADO*. Rodei o preflight (modo leitura): **`PlatEMO git HEAD b686ca20cd89 (pin OK)` + `content-hash fb9ed1d399d4 LACRE OK`**.
2. **O `git status` do repo vendorizado nomeia exatamente quem está sujo:** 12 arquivos modificados — `CSEA/*` (b4), `EDN-ARMOEA/*` (e7), `K-RVEA/*` (b3), `PC-SAEA/*` (c217), `ParEGO/{EvolALG,ParEGO}.m` (b1) — e **mais nada** (os 2 `??` são `.DS_Store`, excluídos do hash por `tree_sha256`, `preflight.py:34`).
3. **Os arquivos do `nsga3` estão limpos:** `NSGA-III/{NSGAIII.m, EnvironmentalSelection.m}` e os utilitários `UniformPoint.m`, `NDSort.m`, `CrowdingDistance.m`, `OperatorGA.m` retornam **vazio** no `git status --porcelain` ⇒ são **byte-idênticos ao commit `b686ca2` do upstream BIMK/PlatEMO**.
*(d)* Como o repo aninhado tem `.git` próprio e o HEAD bate com o pin, "arquivo limpo" ≡ "arquivo igual ao upstream". Nenhuma das **23 âncoras** do `anchors.json` toca arquivo do NSGA-III. *(e)* **(1) · D — sai do balde T.** É a diferença mais concreta entre esta análise e a F5: a alegação central do piso agora tem prova.

---

**A28 — 🆕 O mating pool é uniformemente aleatório (e isso é o NSGA-III stock).**
*(a) Canônico:* Deb & Jain descartam o operador de comparação por crowding do NSGA-II e usam **seleção aleatória de pais** — não há medida escalar de aptidão a torneiar. *(b) Espec:* nada muda. *(c) Observado no fonte:* `NSGAIII.m:29` chama `TournamentSelection(2, Problem.N, sum(max(0,Population.cons),2))`; nos 25 problemas (todos box-constrained, sem restrições) `cons ≡ 0`, então em `TournamentSelection.m:24-29` o `rank` é constante, `min` devolve o **primeiro** dos K=2 candidatos, e `index = Parents(1,:)` com `Parents = randi(N,2,N)` ⇒ **amostragem uniforme com reposição**. *(d)* É esta propriedade que fecha o modelo quantitativo de duplicatas de A11 (`P(par idêntico) = 1/N`), e é ela que explica por que o `nsga3` fica **longe** dos 23% do MOEA/D: sem vizinhança `T=2`, os pais varrem a população inteira. *(e)* **(1) · F** — verificabilidade **de fonte**; os pais não são exportados, então no dado é NV. Consistente com o teto A16.

---

**A29 — 🆕 A instrumentação T11 não perturbou a busca: prova BIT-A-BIT, sem par G-6.**
*(a)/(b)* A campanha T11 alega instrumentação read-only e prova não-perturbação em **19/19** configs pelo par `g6_com`×`g6_sem`. **O `nsga3` não está nesses pares** (é ⚪ "sem sonda", `T11-RODADA-FINAL.md:231`), de modo que, para este config, a premissa "a busca da s42 é a mesma que o código de hoje faria" seria **extrapolação**. *(c) Observado:* o smoke T11 rodou **exatamente a mesma célula** `main/nsga3/DTLZ2/42`, com o mesmo DoE e a mesma semente, em 30/07 — 4 dias depois da s42 (26/07 10:39Z) e **depois** de todas as mudanças de código. Comparei:
- **①**: mesmas 371 linhas, mesmas 21 colunas, `max|ΔX| = 0,0`, `max|Δf| = 0,0`, **sha256 do conteúdo IDÊNTICO** (`fee35e9fa2d8d206…`);
- **②**: 270 linhas, **sha256 IDÊNTICO**;
- **⑥**: mesmo inventário de registros (1 header, 1 `decomposicao`, 1 `seeding`, 18 `nsga3_gen`, 25 guards, 1 footer) e **campos idênticos em todos os 6 tipos** (nenhum campo novo, nenhum perdido); header difere **só no `ts`**; footer idêntico em todos os 11 campos exceto `ts`; lattice `max|ΔW| = 0,0`;
- **④** difere (wall-clock, como deve).
*(d)* As três mudanças do T11 neste config (`sigma_dict`, `campanha_id`+schema, string `geracoes_derivadas`) vivem **todas** no `build_manifest`/`man.params`, executados **depois** do `algo.Solve` (`experiment.m:2447 → 2490-2537`); o `rng(semente,'twister')` e o laço evolutivo não foram tocados. *(e)* **(1) · D.** **Para este config a premissa do exercício não é mais extrapolação: é medida.**

---

## 3. % por classe

**Denominador = total − T = 29 − 2 = 27.** (T listado à parte, com razão.)

| classe | n | % (sobre **27**) | itens |
|---|---|---|---|
| **(1) conforme o método canônico** | **12** | **44,4%** | A5 · A6 · A8 · A9 · A10 · A14 · A18 · A21 · A22 · **A27** · **A28** · **A29** |
| **(2) desvio sancionado** | **15** | **55,6%** | A1 (D21/D61) · A2 (D63/D88) · A3 (§3.2/D65/DI-39) · A4 (DI-18/§6.3) · A7 (D88) · A11 (D57/D89) · A12 (armadilha + regra 11) · A13 (D57) · A15 (Balde C) · A19 (§3.2/DI-13.7) · A20 (§17.6/DI-13.10) · **A23 (T11/I-09)** · A24 (doc) · **A25 (G-7)** · **A26 (B-03)** |
| **(3) inexplicado 🎯** | **0** | **0,0%** | — |
| **T (fora do denominador)** | 2 | — | **A16** associação a nicho por indivíduo (não exportada; código provado limpo) · **A17** normalização/`Zmin` interno (exige instrumentar `EnvironmentalSelection.m`) |

Comparação com a F5: **24 → 29 aspectos**; T **3 → 2** (A23 saiu do teto por A27+A23); (1) 9 → 12; (2) 12 → 15; (3) **0 → 0**. Todos os 15 itens de classe (2) têm decisão citada **nominalmente**.

---

## 4. 🆕 AS CORREÇÕES DA T11 — o que tocou o `nsga3`, item a item

O `nsga3` é um piso: **nenhuma** das melhorias de instrumentação de modelo o toca (`REGRA_DO_ROTULO`, `pmid_ids`/`ref_ids`, `y_treino_dist`, `sonda_estratificada`, `p_wrong_stats` — todas exigem surrogate; a ③ tem 0 linhas). O que sobrou foram **3 correções de ⑤ + 1 de documentação + 1 de gate**, todas verificadas:

| # | correção | implementada? | **funciona de fato?** | evidência | o que ainda falta |
|---|---|---|---|---|---|
| 1 | **`sigma_dict` declarado** (G-7/T11-P0) | ✅ `experiment.m:2507-2511` | ✅ **sim, e não é sentinela**: a declaração `nao_se_aplica` é *verdadeira* — ③ com 0 linhas, `fit_series=[]`, 3 timings NULL, tudo medido no mesmo manifesto | **MEDIDA** (smoke): ausente em 25/25 na s42, presente no smoke | nenhum **teste** cobre o piso ONLINE (só o OFFLINE, `test_piso_off.py:112`); guardado apenas pelo G-7 |
| 2 | **`repo_hash`** (I-09) | ✅ `manifest.py:64-84` + `experiment.m:3080` | ✅ **sim**: `195f64ed…` é commit **real** (`git cat-file -t` = commit), de 30/07 18:00 −0300, e o run é 18:45 −0300 ⇒ sem staleness | **MEDIDA** (smoke) + **LIDA** (git) | **sem detecção de árvore suja** — é `rev-parse HEAD` puro; um working tree modificado dá o mesmo carimbo |
| 3 | **`campanha_id` + schema v2** (B-03) | ✅ `experiment.m:3067-3068` | ✅ **sim**: `t11-smoke-195f64e`, v2; e o efeito colateral é o desejado (as 25 células v1 da s42 **não** contam como prontas — `manifest.py:249-250`) | **MEDIDA** (smoke) | **D-G**: a env `UA_DD_SAEA_CAMPANHA_ID` precisa ser exportada nas 4 máquinas; o default vira a data **UTC** e muda na virada do dia |
| 4 | **string `geracoes_derivadas`** (I-13/A24 — *a recomendação do meu próprio relatório F5*) | ✅ `experiment.m:2516-2527` | ⚠ **parcialmente**: a fórmula nova acerta **25/25** no `nsga3` (a antiga acertava 0/25) — mas a meta-alegação *"`n_geracoes` é EMERGENTE, não fechada"* é **falsa**: a forma fechada `⌊(20D+dup_desc)/n_off⌋+1` acerta **100/100** nos 4 pisos | **MEDIDA** (`t11_b1/b2/b3_*.py`, 25 e 100 células) | trocar a frase "EMERGENTE, não fechada" pela forma fechada, ou removê-la |
| 5 | **`preflight` passou a conferir o PlatEMO** | ✅ `preflight.py:112-121` (conserto de 30/07) | ✅ **sim, e é a correção mais valiosa para este config**: antes, o `dir_map` não tinha `PlatEMO` e ele **nunca era aferido**; agora `content-hash fb9ed1d399d4 LACRE OK` | **MEDIDA** (rodei o preflight, modo leitura) + `git status` do repo aninhado | o lacre é da árvore INTEIRA (inclui os 12 patchados de outros configs); a isolação do NSGA-III vem do `git status`, não do hash |
| 6 | `tempo_aval_real_s` não-nulo (I-3) | — | ✅ este config **nunca** esteve na lacuna: 0,112 s na s42, 0,0335 s no smoke | MEDIDA | — |
| 7 | `NO_RETRY` (I-4, `experiments.py:84-88`) | ✅ | ⚪ **inerte aqui**: os 3 padrões determinísticos são de b1/c154/c262; `n_retries=0` e `fallback_ativado=false` em 25/25 | MEDIDA + LIDA | — |
| 8 | **regra 11 do CONTRATO §10** (dominância sobre ① é LOSSY) | ✅ doc | ✅ **cobre exatamente** o que a F5 mediu neste config (A12: 4 colisões; DTLZ4: 23,4% de zeros exatos) | MEDIDA | — |

**Caça ao padrão do c217 ("campo presente, dado sentinela"): NEGATIVA.** Varri os candidatos naturais do `nsga3` (`t11_b7_g7_sentinela.py`): `n_front1` presente em **413/413** gerações, **0 NaN, 0 zeros**, faixa 2..20, valores distintos por célula (o `try/catch` do `piso_instrument.m:44-51` **nunca** caiu no ramo NaN); `nadir_front1` com M componentes em **413/413** (nenhum vazio); `f_best` com M componentes em 413/413, nenhum todo-zero; `tempo_geracao_s` nunca NaN nem 0. O único campo declarativo do config (`sigma_dict`) tem a sua declaração **confirmada pelo dado** da mesma célula. **Nada do padrão c217 neste config.**

---

## 5. Comparação canônica — **N/A** (controle sem artigo) → **o papel de régua**

| critério | evidência (25 problemas, `main`, semente 42; insumos F5.2 pré-computados) | veredito |
|---|---|---|
| **Não trivial** | SA-MOEA batem o `nsga3` em **182/305 comparações = 59,7%**; mas em DTLZ1 **nenhum dos 13 SA o bate** e em WFG4/WFG2/WFG1 só 2 | ✅ |
| **Atingível** | rank geral médio **9,52 de 17**; nunca 1º nem último no grid (faixa 2–14) | ✅ |
| **Custo trivial** | Σ = **123,7 s = 0,0344 h-core**; os 4 pisos = **0,1426 h-core** contra **257,0 h-core** dos 13 SA em `main` = **0,056%** | ✅ |
| **Coerente entre pisos** | rank médio IGD+: **nsga2 1,80 · nsga3 2,24 · smsemoa 2,28 · moead 3,68**; `nsga3` é o melhor piso em **6/25** e **o pior em 0/25** | ✅ |
| **Confirma o prior do bundle** | §3.2-5 previu "o MOEA/D fica o pior dos 4 pisos" — **`nsga3` bate `moead` em 24/25** e o `moead` tem o pior rank | ✅ prior confirmado |
| **Assinatura do próprio mecanismo** | spacing: rank **1,67/4 em M=3** contra 2,63 em M=2 — o nicho aparece exatamente onde deveria | ✅ |
| **Casamento com o e7 (EA-Indicador)** | **e7 melhor que `nsga3` em 13/25 (52%)** — moeda ao ar | ⚠ ver abaixo |

**A leitura de controle que importa para a D97.** Sob `31D−1`, o surrogate do e7 compra **13 vitórias em 25** contra o seu próprio piso casado — indistinguível de zero ganho. Isso não é veredito sobre o e7 (a análise dele é dele); é a **prova de que a régua faz o trabalho que a §3.2 lhe atribuiu**: dar atribuição limpa do ganho ao surrogate, inclusive quando o ganho é nulo.

**Nota metrológica (O-18).** As 25 células rodaram **100% na `vm3`** (`tempo_f52d.csv`). Toda comparação contra configs de outras máquinas está sujeita ao piso de ruído (HV ≤1,55%; **IGD+ até 58,98%**) — não trato razões dentro de ~1,6× como diferença. As conclusões acima (moead pior em 24/25; e7 ~50%; `nsga3` nunca o pior piso) são robustas a esse piso, e **as comparações entre os 4 pisos são imunes** (mesma máquina).

**Nota de comparabilidade interna (DI-18).** A banda dos pisos em M=3 **não** é a população constante: `nsga3`/`moead` correm com N=15 e 14–15 descendentes/geração; `nsga2`/`smsemoa` com 20. Recomendo que a banda min–máx usada pelos BO-especiais (D25/DEF-A13) leve essa nota ao M8/M9.

---

## 6. Saúde (s42 = corpus principal)

**Trajetórias (20 checkpoints × 25 células, `f5/trajetorias/`).** IGD+ monotônico não-crescente em **475/475 transições — 0 violações**. Ganho `IGD+(0)/IGD+(final)`: mediana **4,83×**, máximo **99,0×** (BBOB_F17), mínimo **1,34×** (ZDT6, o pior problema do config). `|ND|` final: 5 a 228, mediana 19.

**Dinâmica interna (413 gerações).** `|F1| == |pop|` em **77,2% das gerações M=3** contra **19,5% em M=2** — em M=3 o piso converge para o regime em que só o nicho decide. Ponto ideal quase-monotônico (2 pioras materiais em 898 transições; 10 adicionais ≤1e-17 — A18).

**Duplicatas.** 179 em 7.028 descendentes (**2,55%**), previstas em 1,91% pelo modelo do operador stock (A11), mediana 7/célula, máximo 17 (ZDT1). Muito abaixo dos 23% pré-registrados para o MOEA/D com `T=2`.

**Integridade e contrato.** `integridade_f52a.csv`: 25 linhas, todas `VAZIO` (③ com 0 linhas, por desenho) — **zero corrupção**. `contrato_f52b.csv`: **0 linhas nsga3** (padrão-ouro do lote). `tempo_f52d.csv`: 25/25 com wall, roster homogêneo.

**Sonda.** **N/A por desenho** — não há régua Sobol nem bloco estratificado; a **regra 12 do CONTRATO é vacuamente satisfeita**. A análise de saúde do config é a dinâmica de gerações + as trajetórias, e o endpoint é a ① do regime online (não há ⑦; o config é online).

---

## 7. SCORE e VEREDITO

### **SCORE: 10/10 — ACEITAR** · **VEREDITO: MANTEVE** (com fortalecimento medido da evidência)

**Por que MANTEVE, e não MELHOROU ou PIOROU — a causa nomeada.** O score não podia subir (já era o teto) e não havia por que descer. A razão substantiva é **A29: o mecanismo não mudou, e isso está provado bit-a-bit** — a ① e a ② do smoke pós-T11 têm o **mesmo sha256** das da s42 na mesma célula. Não é "a campanha alega que a instrumentação é read-only"; é a mesma busca, o mesmo lattice, a mesma semeadura, a mesma aritmética. As três correções do T11 vivem todas depois do `Solve`.

**O que MELHOROU, e é medida, não impressão:**
1. **Um teto caiu (A27).** `patches: NENHUM` era declaração na F5 (T, `repo_hash=""`); hoje é medida tripla — o `preflight` **passou a conferir o PlatEMO** (antes o pulava), o lacre de conteúdo bate, e o `git status` do repo vendorizado mostra **12 arquivos sujos, nenhum deles do NSGA-III / UniformPoint / NDSort / CrowdingDistance / OperatorGA**. A alegação central do piso deixou de repousar em `algo_version`.
2. **Dois aspectos subiram de verificabilidade (A9, A15):** a truncagem `2⌊N/2⌋` e os defaults `deal(1,20,1,20)` saíram de "medido + hipótese"/"config-echo" para **verificados no fonte**.
3. **Três buracos de contrato do ⑤ fecharam** (A23/A25/A26): a s42 entrega 3/6 do `quinto_obrigatorio`; o código de hoje entrega 6/6, e os gates de proveniência dão `G-7 ⑤ 6/6` sobre o smoke.
4. **Um aspecto novo com poder explicativo (A11+A28):** a taxa de duplicata deixou de ser assinatura empírica e virou **quantidade prevista a priori** pelo operador (1,91% previsto × 2,55% medido, r=0,81, ordenação M=3 > M=2 reproduzida).

**O que PIOROU — nada de mecanismo; um item documental novo:** a string `geracoes_derivadas`, que a F5 mandou corrigir, foi corrigida no **número** (0/25 → 25/25) mas ganhou uma **meta-alegação falsa** ("`n_geracoes` é EMERGENTE, não fechada"), que refuto com **100/100** nos 4 pisos. É classe (2) documental, zero impacto no dado, e o conselho operacional da própria string ("não derive, LEIA") é seguro.

**Auto-errata contra o meu relatório F5 (a honestidade obriga):** a F5 reportou "2 não-monotonias do `ideal` em 898"; o número completo é **12 em 898 (1,34%)**, dos quais 10 estão em ≤1e-17 (7 no DTLZ4, região denormal). A conclusão de A18 não muda; a precisão sim.

**Nada a enviar à F5.4.** Zero aspectos classe (3) em 29 aspectos × 25 células + 1 smoke. A única pendência viva continua sendo de **pré-registro, não de fidelidade**: o **SUB-varN (DI-39)** — inalterado pelo T11 (`cards/INDEX.md:67` ⬜), com a contradição DI-32/A2 × DI-39 a resolver antes do M8.

---

## 8. Aspectos classe (3) 🎯

**Nenhum.** A verificação adversarial não recebe itens do `nsga3`.

*Confirmação OPCIONAL (mecanismo já provado por dado):* a semeadura do **DTLZ4** só é reconstruível em double — re-medi 92/393 objetivos exatamente 0,0 (23,4%), menor não-nulo 1e-45, e o recomputo devolve `n_frentes/n_frente1` **trocados** em relação ao log. É a `regra 11` do CONTRATO em ação. Se a torre quiser fechar a zero, basta um re-run instrumentado de 1 célula gravando os `solution_id` selecionados no registro `seeding` (~5 s).

---

## 9. Teto T + armadilhas + o que este corpus NÃO permite verificar

**T (2 itens, exigem re-run instrumentado):**
1. **Associação a nicho / distância perpendicular / seleção da última frente (A16)** — não exportada por indivíduo. Evidência indireta favorável (spacing rank 1,67/4 em M=3; `|F1|=|pop|` em 77,2% das gerações M=3). ⚠ O *código* já não é dúvida: `EnvironmentalSelection.m:38-83` está byte-idêntico ao upstream.
2. **Normalização por ASF / hiperplano de interceptos / `Zmin` acumulado (A17)** — não exportados; o `ideal` logado é o da população corrente, grandeza diferente (é o que gera o falso-alarme de A18).

**Resíduos declarados (não são T, são caveats):** `repo_hash` é HEAD-only, sem detecção de árvore suja · o `campanha_id` default vira a data UTC e muda na virada do dia (D-G) · a correção do `sigma_dict` do piso ONLINE não tem teste.

**O que este corpus NÃO permite verificar:**
- **Nada sobre modelo/surrogate** — o config não tem nenhum. U3, U4, U5, U6, U8, U11, U12 são N/A com regra citada; a régua Sobol e o bloco estratificado (regra 12) não existem aqui.
- **A parte comportamental do nicho** (T1/T2) — exigiria instrumentar `EnvironmentalSelection.m`, o que violaria o "piso = stock".
- **Comportamento em escala de campanha** — 1 semente; a variância entre as 30 sementes do M8/M9 é outro regime.
- **Se `N=20` é o N certo** — é decisão de pré-registro (SUB-varN), não de fidelidade.
- **As correções T11 em produção** — o smoke é 1 célula em tempdir; nenhuma célula da s42 tem `campanha_id`/`repo_hash`/`sigma_dict`.

**Armadilhas confirmadas na escala (25/25 salvo indicação):**
1. **`N` do manifesto é ambíguo por desenho** — `N_nominal=20` sempre, `N_efetivo=15` em M=3. Usar o nominal reprova as 6 células M=3 (DI-18).
2. **Descendentes por geração são `2⌊N/2⌋`, não `N`** — 14 em M=3. Qualquer aritmética com N falha em 6/25.
3. **O bloco de arranque tem `N_ef+1` cache-hits** (16 ou 21) com `N_ef` sids distintos. Tratar os 495 hits de semeadura como duplicatas do algoritmo superestima a taxa em **3,8×** (675 vs 179). **🆕 É exatamente o erro que gerou a ERRATA 5** — substituir `cache_hits` do ⑤ no lugar de "duplicatas de descendente" numa fórmula que pedia a segunda.
4. **O `fe` do evento `nsga3_gen` é o do INÍCIO da geração** (`gen 1` tem `fe == 11D−1`). Filtrar cache-hits por `fe > init` sem o teto `fe ≤ fe(última)` quebra a aritmética em DTLZ1.
5. **NÃO há geração fantasma** — aplicar o off-by-one do c217 reprova 25/25 falsamente.
6. **`hard_stop` é estrutural** (25/25, sempre em `fe==maxfe`), não anomalia.
7. **Término é `footer.termino`** (`'normal'`); **não existe `motivo_parada`** e o footer é **1 registro**, não 2 (bug B1).
8. **Dedup e joins do R4 sempre por `solution_id`** (regra 1 + regra 11 do CONTRATO §10) — 4 colisões float32 em 10.856 linhas.
9. **DTLZ4 não é re-verificável a partir da ①** onde há underflow (23,4% de zeros exatos no bloco init).
10. **🆕 Não derive `n_geracoes` da string do manifesto sem definir `n_dup`.** A forma fechada correta é `⌊(20D + duplicatas de DESCENDENTE)/n_off⌋ + 1`, com `n_off = 2⌊N_ef/2⌋` (nsga2/nsga3/smsemoa) ou `N_ef` (moead) — **100/100 nos 4 pisos**. A string do manifesto acerta 25/25 no `nsga3` mas erra o rótulo ("emergente") e falha em 7/100 nos outros pisos.
11. **③ vazia, `sigma_dict` "nao_se_aplica", sonda "nao_se_aplica" e 3 timings NULL não são perda de dado** — são a assinatura, em seis camadas independentes, de que o piso não tem surrogate.
12. **🆕 `sigma_dict` presente ≠ surrogate presente** neste config: a partir do T11 o piso **declara** o dicionário como não-aplicável. Quem usar "tem `sigma_dict`?" como discriminante de surrogate passa a errar nos 4 pisos.

---

### Nota lateral para a torre (fora do escopo do config, mas medida)

O `T11-RODADA-FINAL.md` §15.2 afirma: *"Os 11 smokes PYTHON **não estão preservados** — rodaram em tempdirs removidos"*. **Falso:** `/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/` existe, com **17 MB** e células de `c122`, `c149`, `c154`, `c262`, `e81` (main), `b5r`, `c311`, `moead_media` (off), `sobol_batch` (batch) e `treed_media` (sweep-big-mvns). Os analistas dos configs Python **têm** corpus de smoke — a §15.2 os está mandando embora de mãos vazias. Seria a **errata 17**.

---

*Insumos pré-computados usados SEM recomputo: `f5/metricas_finais_f52c.csv` · `f5/trajetorias/main_nsga3_*_42.json` (25) · `f5/contrato_f52b.csv` (0 linhas nsga3) · `f5/integridade_f52a.csv` (25 `VAZIO`) · `f5/tempo_f52d.csv` (`vm3` 25/25) · `f5/sonda_f52e.csv` (0 linhas, correto por desenho). Gates F5.1 citados, não re-verificados.*

*Scripts e evidências desta bateria (único local de escrita autorizado) em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga3/`:*
`t11_b1_formula.py` (errata 5 nas 25 células) · `t11_b2_formula_4pisos.py` (nas 100) · `t11_b3_formula_fechada.py` (**a forma fechada 100/100**) · `t11_b4_smoke_vs_s42.py` (**diff smoke×s42 + bit-identidade**) · `t11_b5_mecanismo.py` (re-medição dos 24 aspectos da F5 em 25 células + smoke) · `t11_b6_ideal.py` (as 12 não-monotonias com magnitude) · `t11_b7_g7_sentinela.py` (**G-7 + caça à sentinela**) · `t11_b8_regua.py` (papel de régua) · `t11_b9_dedup_modelo.py` (**modelo do operador × medida**).
*CSVs:* `ASPECTOS_nsga3_t11.csv` (os 29) · `mecanismo_t11.csv` · `formula_ngeracoes.csv` · `formula_4pisos.csv` · `formula_fechada_4pisos.csv` · `g7_sentinela.csv` · `ideal_nao_monotonias.csv` · `dedup_modelo.csv` · `regua_t11.csv` · `smoke_vs_s42.txt`.
*Fontes de código lidas (read-only):* `src/experiment.m:2329-2554` (`run_piso`), `:3054-3097` (`build_manifest`) · `src/piso_instrument.m` · `src/manifest.py:39-115` · `scripts/preflight.py:100-180` · `algorithms/_PlatEMO/PlatEMO/Algorithms/Multi-objective optimization/NSGA-III/{NSGAIII.m, EnvironmentalSelection.m}` · `.../Utility functions/{OperatorGA.m, TournamentSelection.m}` · `claude_code_context/artifacts/{contrato_61.json, repos.lock}`.