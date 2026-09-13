# RELATÓRIO DE FIDELIDADE — smsemoa · SMS-EMOA (piso online) · F5.3b fan-out · 25 células main · semente 42

**Analista de fidelidade smsemoa · 2026-07-29 · protocolo v1.1 (Etapa 7 formato RICO) · dados READ-ONLY em `resultados_experimentos/smsemoa/{problema}/42/` · controle SEM artigo (Entrega 2 = N/A)**

Escala auditada: **25/25 células · 376 gerações logadas · 10.856 linhas da ① · 7.520 linhas da ② · 351 transições população→população · 475 transições de trajetória · 545 guards**. Zero amostragem.

---

## 1. Ficha do mecanismo

**SMS-EMOA puro** (Beume/Naujoks/Emmerich, EJOR 2007), built-in do **PlatEMO 4.15**, sem patch algum (`params.patches = "NENHUM — piso e stock do PlatEMO 4.15 por design"` em 25/25). É um EA **steady-state (μ+1)**: o laço externo (a "geração" logada) executa `N` substituições unitárias; cada passo gera **1 filho** de 2 pais sorteados, funde em `[Pop, Off]` (N+1) e **descarta exatamente 1** — o de **menor contribuição de hipervolume (S-metric)** na pior frente. É o **espelho mecânico exato do c262/qNEHVI** (mesma seleção por HV; um com GP, outro sem) — daí seu papel na **D25/§3.2**: dar a *atribuição mais limpa possível* do ganho ao surrogate, e justamente na métrica principal.

Nossa instanciação: `maxFE = 31D−1` com hard-stop D21/D61 · **N = 20 CRAVADO** (2026-07-18, protocolo Knowles/ParEGO; §3.2, ponto comum entre a faixa ~20–25 e o conjunto D65 {10,20,30,50}) · **N_efetivo ≡ N_nominal = 20 mesmo em M=3** (SMS-EMOA não usa vetores de referência — ao contrário de NSGA-III/MOEA-D, que caem a 15 pelo lattice do `UniformPoint`, §6.3) · população inicial **semeada do DoE compartilhado** (11D−1 LHS do artefato) pelos melhores N por **NDSort + CrowdingDistance, desempate por índice (D88)** · operadores Balde C (`SBX proC=1 dis_c=20 + PM proM=1 dis_m=20`, defaults do `OperatorGA`) · **sem surrogate**: ③ vazia, `fit_series` vazia, `sonda.status = 'nao_se_aplica'`, sem `sigma_dict`. Evento de geração no ⑥ = **`smsemoa_gen`**; campo de término = **`footer.termino`** (não `motivo_parada`, ausente do manifesto em 25/25).

**Prior do config (nota v2 = 10; "o piso MAIS FORTE, 2/3 problemas em s0")** — calibrado nesta análise: em 25 problemas/semente 42 o smsemoa é o **melhor piso em 8/25 por IGD+ e 7/25 por HV** (rank médio **2,28 de 4**), atrás do NSGA-II em contagem; mas é **inequivocamente o mais fiel ao seu próprio princípio** (§6, query-joia) e o piso que **mais frequentemente bate todas as configs SA** (DTLZ3, WFG4).

---

## 2. DISSECAÇÃO DOS ASPECTOS (o CORE)

### 2.1 Tabela-resumo (1 linha por aspecto)

Verif.: **D** = direta · **DD** = direta-declarativa (config-echo; elo de código coberto por `anchors.json`/`repos.lock`) · **I** = indireta · **—** = não-verificável (balde T).

| # | aspecto | classe | verif. | resultado-síntese (25 células) |
|---|---|---|---|---|
| 1 | Orçamento `maxFE = 31D−1` + hard-stop exato | (2) D21/D61 | D | 25/25 exato; `fe_index` denso 0-based; `solution_id` denso |
| 2 | DoE injetado 11D−1 (artefato compartilhado) | (2) D63/D88 | D | **Δ**X **= 0,0 bit-a-bit em 25/25**; `doe_hash` ≡ sidecar 25/25; ordem preservada |
| 3 | `N = 20` cravado; `N_efetivo ≡ N_nominal` em M=3 | (2) §3.2/D65/D20 | DD+D | `n_pop = 20` em **376/376** gerações, inclusive nos 6 problemas M=3 |
| 4 | Seeding D88 = melhores N por NDSort+CD (**query-joia 1**) | (2) D88 | D | recomputo **idêntico em 24/25**; única exceção DTLZ4 (causa provada: underflow float32) |
| 5 | Identidade de seeding entre os 4 pisos (prova cruzada) | (2) D88/§6.3 | D | nsga2 ≡ smsemoa **25/25**; nsga3/moead ≡ nos 19 M=2 e **⊂ (15⊂20) nos 6 M=3** |
| 6 | Gerações derivadas = 20D÷N; FE/geração = N (laço (μ+1) aninhado) | (1) | D | `n_ger = D+1` em 25/25; Δfe = 20 em **348/351** transições (3 exceções = duplicatas) |
| 7 | **Seleção por contribuição de HV (S-metric)** (**query-joia 2**) | (1) | D | HV populacional não-decrescente em **348/351** (0,85% de quedas) vs **5,70%** nsga2, **4,38%** nsga3, **23,42%** moead |
| 8 | Elitismo (μ+1): `②(g+1) ⊆ ②(g) ∪ novos(g)` | (1) | D | **351/351 transições, 0 violações**; entrantes ≤ N em 100% |
| 9 | ② = snapshot da população, N linhas/geração, sem off-by-one | (2) §17/CONTRATO | D | 7.520 = 376×20; 0 duplicatas intra-geração; `ideal/nadir` casam 376/376 |
| 10 | `n_front1`/`ideal`/`nadir_pop`/`nadir_front1` recomputados da ②×① | (1) | D | `ideal` **376/376** · `nadir_pop` **376/376** · `n_front1` **332/376** · `nadir_front1` 358/376 |
| 11 | Limite de precisão: NDSort float32 × float64 (export D53) | (2) D53 | D | 44/376 divergências; log ∈ [fraco, estrito] em **375/376**; enriquecimento de empates **8,1×** |
| 12 | Operadores SBX/PM stock (Balde C) | (1) | DD | eco `SBX proC=1 dis_c=20 + PM proM=1 dis_m=20` em 25/25 headers |
| 13 | SMS-EMOA **PURO** (≠ SMS-EMOA-MA §3.6); zero patches | (1) | DD | `patches='NENHUM'`, `parameter='nenhum'`, `algo_version='piso-SMSEMOA-PlatEMO4.15'` 25/25 |
| 14 | ③ vazia + `fit_series` vazia + sem `sigma_dict` | (2) §3.2/DI-13.7 | D | 0 linhas em 25/25 (schema completo preservado: 21–49 colunas conforme D,M) |
| 15 | Sonda N/A por desenho | (2) §3.2/CONTRATO | D | `sonda.status='nao_se_aplica'`, `n_blocos=0`, `n_linhas=0` em 25/25; 0 linhas no `sonda_f52e.csv` |
| 16 | Dedup D57/D89: duplicata **não gasta FE, gasta o slot** | (2) D57/D89 | D | 17 cache-hits de evolução em 3 células; **fechamento aritmético 25/25** |
| 17 | Cache-hit de arranque: seeding loga **N+1 = 21** | (2) D57/D89 (precedente c217) | D | **25/25**; sempre o indivíduo da posição 0 de ②(1); efeito analítico nulo |
| 18 | Geração fantasma + guard `hard_stop` (células D=2) | (2) D21/D61/D89 | D | 3/25 células; 16 linhas fantasma na ①; `n_geracoes` conta só as COMPLETAS |
| 19 | Timing ④/⑤: 3 colunas NULL + reconciliação; custo trivial | (2) DI-13.10/§17.6 | D | `fit/busca/sonda` NULL 25/25; Σ④ ≤ ⑤ 25/25; **0,0375 h-core nas 25 células** |
| 20 | Término e manifesto: `footer.termino`, `status`, `params` no ⑤ | (2) doc-sync | D | `termino='normal'` 25/25; `params` (12 chaves) presente — **fora das 197 não-conformes da F5.2b** |
| 21 | Contrato §6: header sem `run_id`/`ambiente`; `repo_hash` vazio | (2) doc-sync (sistêmico) | D | 25/25; `repo_hash=''` também em nsga2/c217/e7/b1/c262 ⇒ não é do config |
| 22 | Casamento D25 com o c262 (espelho HV) — a régua casada | (2) D25 | I | c262 vence o piso em **16/21** (razão mediana 2,51×); piso vence em 5/21 |
| 23 | Ramo interno do `Reduce` (HV exata M=2 × Monte-Carlo M≥3; ref. interno) | **T** | — | não exportado; inferido só por assinatura (§6) |
| 24 | Seleção de pais `randperm(end,2)` (uniforme, sem torneio) | **T** | — | nenhum log de pais em 376 gerações |

### 2.2 Blocos narrativos

---

**#1 — Orçamento `maxFE = 31D−1` com hard-stop exato.**
*(a) Canônico.* O SMS-EMOA canônico não prescreve orçamento; o `Algorithm.NotTerminated` do PlatEMO encerra ao esgotar `maxFE`, avaliado **entre gerações** — o laço interno de N passos roda até o fim mesmo que estoure. *(b) Nossa SPEC.* D21/D61 impõem hard-stop **exato** por exceção (`MException('PlatEMO:Termination')`) dentro do wrapper de FE, para que os 21 configs compartilhem o mesmo denominador. *(c) Observado.* `len(①) == 31D−1` e `manifest.fe_final == manifest.maxfe` em **25/25**; `fe_index` estritamente `arange(31D−1)` e `solution_id` idem em 25/25 (BBOB 309, DTLZ1 216, DTLZ2/3/4 371, MMF16_20 619, WFG/DTLZ7 681, ZDT1/3 929, MMF 61). A coluna `fase` fecha `init = 11D−1` e `opt = 20D` **exatos em 25/25** — inclusive nas três células que sofreram hard-stop no meio de uma geração (MMF1/MMF11_L/MMF4: `init=21; opt=40`). *(d) Mecanismo.* O wrapper conta FE reais; as duplicatas bit-exatas não incrementam o contador (D89), então o laço prossegue até o FE 31D−1 e a exceção corta na avaliação exata. *(e)* **(2) D21/D61 · direta.**

---

**#2 — DoE injetado 11D−1, bit-a-bit contra o artefato.**
*(a) Canônico.* PlatEMO inicializa com `Problem.Initialization(N)` — amostragem aleatória interna de N pontos. *(b) Nossa SPEC.* D63 substitui por **carga do artefato** `data/doe/{problema}/doe_{problema}_42.parquet` (LHS-maximin, `SeedSequence((semente, problema_id))`), e D88 define como esse DoE vira população. O objetivo é o pareamento exato entre os 21 configs: o mesmo ponto de partida para todo mundo. *(c) Observado.* Confrontei linha a linha a matriz X do artefato contra as linhas `fase=='init'` da ① nas 25 células: **`max|ΔX| = 0,0` em float32, 25/25**, com a **ordem preservada** (linha *i* do artefato = `solution_id == i`). O `doe_hash` do manifesto do run é idêntico ao do sidecar do artefato em 25/25. O resíduo em float64 (2,97e-08 a 1,90e-06) é exatamente o arredondamento float32 do export (D53), não uma diferença de conteúdo. *(d) Mecanismo.* O `initFcn` recebe a matriz e o harness escreve a ① com o cast float32 de D53 — daí Δ=0 no espaço em que o dado vive. *(e)* **(2) D63/D88 · direta.**

---

**#3 — `N = 20` cravado e `N_efetivo ≡ N_nominal` mesmo em M=3.**
*(a) Canônico.* PlatEMO default N=100. *(b) Nossa SPEC.* §3.2 crava **20** (Knowles/ParEGO: o piso sob orçamento minúsculo se calibra **reduzindo** a população; N=100 é infactível em D=2, onde a população superaria o DoE de 21 pontos). §6.3 registra a consequência: em M=3 o `UniformPoint(20,3)` arredonda para H=4 → **15 vetores**, de modo que **NSGA-III e MOEA/D rodam com N efetivo 15**, enquanto **NSGA-II e SMS-EMOA mantêm 20** — o "N=20" não é uniforme entre os 4 pisos. *(c) Observado.* `n_pop == 20` em **376/376** gerações; `N_nominal = N_efetivo = 20` no manifesto, no header e no footer das 25 células, **inclusive nos 6 problemas M=3** (DTLZ1/2/3/4/7, MMF16_20). A prova cruzada é o aspecto #5: nas mesmas 6 células o nsga3 e o moead têm ②(1) com **15** linhas. *(d) Mecanismo.* O SMS-EMOA não constrói lattice de referência; o `Reduce` opera sobre a população crua. Logo o arredondamento do `UniformPoint` simplesmente não o toca. *(e)* **(2) §3.2/D65/D20 · declarativa + direta** (o valor é declarado no header E medido em toda geração).

---

**#4 — Seeding D88: os melhores N do DoE por NDSort + CrowdingDistance (query-joia 1).**
*(a) Canônico.* Não existe no SMS-EMOA stock — é acoplamento nosso. *(b) Nossa SPEC.* §3.2/D88: "parte dos mesmos 11D−1 pontos LHS, iniciando a evolução com os melhores por não-dominância; **desempate quando a frente-1 excede a população: crowding distance, determinístico**". O racional é que dois runs da mesma semente selecionem o mesmo subconjunto — reprodutibilidade sem sorteio. *(c) Observado.* Reimplementei NDSort + crowding distance (fronteiras com CD=∞, desempate final por índice crescente) sobre os `11D−1` primeiros pontos da ① e comparei ao conjunto `②(geracao == 1)`: **recomputo idêntico em 24/25 células**. O evento `rec:'seeding'` do ⑥ ecoa `n_doe`, `n_frentes`, `n_frente1` e `frente1_excede_pop`, e o meu recomputo reproduz `n_frentes`/`n_frente1` em **24/25** (ex.: ZDT1 → 19 frentes, frente-1 com 14 pontos ⇒ os 20 são a frente-1 inteira + 6 da frente-2 escolhidos por CD; WFG1 → 22 frentes, frente-1 com 18; MMF16_20 → 7 frentes, frente-1 com **50** ⇒ 20 escolhidos *dentro* da frente-1 por CD). **A crowding distance é exercitada em 25/25 células** (em nenhuma a frente-1 tem exatamente 20 pontos) e a flag `frente1_excede_pop=true` aparece em **6/25** (DTLZ2 f1=40, DTLZ4 f1=23, DTLZ7 f1=21, MMF16_20 f1=50, WFG4 f1=30, WFG5 f1=36) — nesses 6 o desempate é o único critério e mesmo assim o recomputo bateu em 5 (todos menos DTLZ4). *(d) Mecanismo.* A regra é totalmente determinística e o dado exportado (X, f, ordem do DoE) é suficiente para reexecutá-la — por isso fecha. A exceção DTLZ4 é dissecada no #11. *(e)* **(2) D88 · direta.**

---

**#5 — Identidade de seeding entre os 4 pisos (a prova cruzada da D88).**
*(a) Canônico.* N/A. *(b) Nossa SPEC.* §3.2 diz que os 4 pisos partem do **mesmo** DoE pela **mesma** regra — é o que torna a comparação entre pisos uma comparação de *seleção*, não de sorte inicial. *(c) Observado.* Comparei `②(primeira geração)` de smsemoa, nsga2, nsga3 e moead nas 25 células: **nsga2 ≡ smsemoa em 25/25** (mesmos 20 `solution_id`, conjunto idêntico); **nsga3 e moead ≡ smsemoa nas 19 células M=2** e, nas 6 células M=3, os seus **15 são um subconjunto estrito dos 20 do smsemoa** (`prefixo=True` em 6/6). *(d) Mecanismo.* A mesma função de seeding roda para os 4 pisos e a regra "melhores N" é **aninhada** em N: os melhores 15 estão contidos nos melhores 20 sempre que o critério é uma ordem total (NDSort + CD + índice). O resultado prova simultaneamente (i) que a D88 é compartilhada, (ii) que o corte 20→15 da §6.3 é do lattice e não de outra regra, e (iii) que qualquer diferença de desempenho entre os 4 pisos é atribuível **só** ao princípio de seleção. *(e)* **(2) D88/§6.3 · direta.**

---

**#6 — Gerações derivadas e FE por geração = N (o laço (μ+1) aninhado).**
*(a) Canônico.* O `SMSEMOA.m` do PlatEMO tem `while NotTerminated(Population); for i = 1:Problem.N; Offspring = OperatorGAhalf(...); Population = Reduce([Population,Offspring]); end; end` — a "geração" externa consome **exatamente N avaliações**, uma por passo steady-state. *(b) Nossa SPEC.* §3.2: "gerações são derivadas: `= K ÷ população`", com K = 20D (o DoE 11D−1 já foi gasto antes do `Solve`). Nada mudou no laço. *(c) Observado.* `n_geracoes = D + 1` em **25/25** (a geração 1 é o snapshot da população semeada, com `fe == 11D−1` e **zero** FE gasto — confirmado em 25/25). As diferenças `Δfe` entre gerações consecutivas são **exatamente 20 em 348 das 351 transições**; as 3 exceções (MMF1 {16,18}, MMF11_L {15,19}, MMF4 {17,19}) são explicadas *à unidade* pelas duplicatas (aspecto #16). Exemplos: ZDT1 (D=30) 31 gerações, fe 329→929 em passos de 20; DTLZ7 (D=22) 23 gerações, 241→681; DTLZ1 (D=7) 8 gerações, 76→216. *(d) Mecanismo.* Como cada passo interno gera 1 filho e avalia 1 ponto, N passos = N FE; a densidade de gerações prometida pela §3.2 ("2 no pior caso D=2, 30 no ZDT1") é **literalmente** o que se mede. *(e)* **(1) conforme o método canônico · direta.**

---

**#7 — Seleção por contribuição de hipervolume (S-metric): a query-joia.**
*(a) Canônico.* O `Reduce` do SMS-EMOA ordena por não-dominância e, na pior frente, remove o indivíduo de **menor contribuição de hipervolume**. A consequência mecânica é uma **quase-garantia de monotonicidade do HV populacional**: como o descarte é HV-guloso, o HV da população não deve cair de um passo para o outro. Nenhum outro dos 3 pisos tem essa propriedade — NSGA-II descarta por crowding, NSGA-III por nicho de referência, MOEA/D por escalarização PBI. *(b) Nossa SPEC.* D25/§3.2 escolhe o SMS-EMOA *por causa* disso: é o "espelho mecânico exato" do c262/qNEHVI. Nada foi alterado no mecanismo. *(c) Observado — teste discriminativo.* Reconstruí a série de **HV da população** (camada ② × objetivos da ①) geração a geração, com **ponto de referência FIXO por problema, comum aos 4 pisos** (nadir da união das quatro ① + 1%), e contei quedas:

| piso | transições | quedas | % | quedas > 1% | pior queda relativa |
|---|---:|---:|---:|---:|---:|
| **smsemoa** | 351 | **3** | **0,85%** | **0** | **−0,092%** |
| nsga3 | 388 | 17 | 4,38% | 0 | −0,83% |
| nsga2 | 351 | 20 | 5,70% | 6 | −4,62% |
| moead | 444 | 104 | 23,42% | 45 | −20,99% |

O smsemoa tem **zero quedas em 24 das 25 células**; as 3 únicas estão todas em **MMF16_20** (transições 11→12, 12→13, 19→20, de **−0,091%, −0,025% e −0,092%**). O ganho de HV populacional do início ao fim é positivo em 25/25 (mediana **+36,4%**; máximo WFG1 **+322%**; mínimo BBOB_F17 +1,6%). *(d) Mecanismo.* A monotonicidade é o *assinatura* do descarte S-metric — e ela **discrimina 6,7× contra o NSGA-II e 27× contra o MOEA/D no mesmo dado, com o mesmo DoE, o mesmo N e os mesmos operadores** (aspecto #5 garante que só a seleção difere). As 3 quedas residuais têm causa identificável: MMF16_20 é M=3, e o `CalHV` do PlatEMO usa **estimativa Monte-Carlo** da contribuição para M≥3 e um **ponto de referência interno móvel** (derivado do nadir corrente), enquanto meu teste usa um ref fixo global — descartes ótimos sob o ref móvel podem custar frações de milésimo sob o ref fixo. Magnitude ≤ 0,092% ⇒ ruído do estimador, não mudança de princípio. *(e)* **(1) conforme o método canônico · direta** — *o uso do hipervolume como critério de seleção está PROVADO pelos dados.*

---

**#8 — Elitismo (μ+1): nada entra que não tenha acabado de ser avaliado.**
*(a) Canônico.* Cada passo funde N+1 e remove 1 ⇒ a população em g+1 é subconjunto de (população em g ∪ os N filhos avaliados em g), e nenhum indivíduo descartado retorna. *(b) Nossa SPEC.* Inalterado. *(c) Observado.* Para cada uma das **351 transições**, testei `②(g+1) ⊆ ②(g) ∪ {solution_id ∈ [fe(g), fe(g+1))}`: **0 violações em 351**. O número de entrantes por geração fica entre 0 e 14, nunca > N: média **8,83 por geração**, Σ = 3.098 entrantes, **taxa de aceitação média de 44,8%** (mínimo BBOB_F49 33,0%, máximo ZDT6 57,0%). *(d) Mecanismo.* Prova conjunta de três coisas: (i) a ② realmente reflete a população (não um arquivo), (ii) os `solution_id` da ① são atribuídos na ordem de avaliação e a janela `[fe(g), fe(g+1))` corresponde exatamente aos filhos daquela geração, e (iii) não há re-inserção de descartados nem contaminação por arquivo externo. A taxa de ~45% é o comportamento esperado de um (μ+1) com N=20 sob poucos ciclos — pressão seletiva alta sem estagnação. *(e)* **(1) · direta.**

---

**#9 — ② = snapshot da população, sem off-by-one.**
*(a) Canônico.* N/A (camada nossa). *(b) Nossa SPEC.* CONTRATO §17 define a ② como a composição da população por geração. Aqui vale o alerta do c217, onde a ② era o **Arc** com snapshot no INÍCIO da geração (armadilha ④ daquele relatório). *(c) Observado.* `len(②) = 20 × n_geracoes` em **25/25** (7.520 linhas no total), **todos os grupos com exatamente 20**, **zero duplicatas intra-geração** (contra 0–3 por célula no c217). E — o ponto decisivo — o `ideal`, o `nadir_pop` e o `nadir_front1` logados no ⑥ da geração g são reproduzidos **exatamente** a partir de `②(g)` (aspecto #10): se houvesse deslocamento de uma geração, esses três casariam com g−1 e não com g. *(d) Mecanismo.* Aqui a ② e o evento `smsemoa_gen` são escritos no **mesmo instante** do laço externo (fim da geração), o que elimina o off-by-one do c217. Isso torna a ② do smsemoa diretamente utilizável como "filme da população" — o que sustenta os aspectos #7, #8 e #10. *(e)* **(2) instrumentação §17 · direta.**

---

**#10 — `n_front1`, `ideal`, `nadir_pop`, `nadir_front1`: recomputo ②×①.**
*(a) Canônico.* O `Reduce` chama `NDSort` a cada passo; a estrutura de frentes da população é a informação que governa a seleção. *(b) Nossa SPEC.* DI-10/S.7.1 enriqueceram o `.jsonl` com esses quatro campos por geração exatamente para permitir a verificação *a posteriori* sem re-run. *(c) Observado.* Nas 376 gerações: `ideal` (mínimo componente a componente) casa em **376/376**; `nadir_pop` (máximo) casa em **376/376**; `nadir_front1` casa em **358/376**; `n_front1` casa em **332/376 (88,3%)**. Além disso `f_best ≡ ideal` em **376/376** — os dois campos são o mesmo vetor (ver armadilha ③). A fração da população que é não-dominada varia muito por problema: **1,000 em DTLZ2, MMF16_20 e WFG4** (população inteiramente na frente-1 em todas as gerações), **0,250 em ZDT4** e 0,286 em ZDT6; média global **0,681**. *(d) Mecanismo.* `ideal`/`nadir_pop` são reduções aritméticas puras — casam trivialmente e provam o elo ②→①. `n_front1`/`nadir_front1` dependem de **relações de dominância**, que são sensíveis a empates de coordenada; as 44 divergências são inteiramente absorvidas pelo aspecto #11. Nota metodológica: com `frac_front1 = 1,000` (DTLZ2/MMF16_20/WFG4), o ramo do `Reduce` que roda é **sempre** o da contribuição de HV; com `frac ≈ 0,25` (ZDT4), roda majoritariamente o ramo de contagem de dominância da pior frente — e ainda assim a monotonicidade do HV (#7) se mantém em 10/10 transições do ZDT4. *(e)* **(1) · direta.**

---

**#11 — O teto de precisão: NDSort sobre float32 ≠ NDSort sobre float64 (consequência da D53).**
*(a) Canônico.* O PlatEMO ordena em **float64**. *(b) Nossa SPEC.* D53 manda exportar **float32 sem arredondamento** — decisão de custo/volume, sancionada, e que o F5.1 já mostrou ter efeito colateral (os 4 falsos-vermelhos de tolerância da ⑦ em DTLZ3/DTLZ4/WFG9, desvios relativos 1,5e-5–7,3e-5, aceitos pelo autor). *(c) Observado.* Das 376 gerações, 44 (11,7%) têm `n_front1` recomputado ≠ logado. Testei a hipótese com dois recomputos-envelope: **fraco** (dominância padrão, o que MATLAB faz sobre números sem empate) e **estrito** (empate em qualquer coordenada ⇒ incomparável). **O valor logado cai dentro de [fraco, estrito] em 375/376 gerações**, e o **estrito recupera o valor logado em 288/376**. O discriminante é o número de **coordenadas objetivas repetidas** na população: **12,75 em média nas gerações divergentes contra 1,57 nas concordantes — enriquecimento de 8,1×**. O caso extremo é **DTLZ4**, divergente em **13/13 gerações** (deltas de −7 a −16) e já no seeding (log: 7 frentes / frente-1 com 23; recomputo float32: 23 frentes / frente-1 com 7): no DoE de 131 pontos, `f1` e `f2` têm **46 zeros exatos cada** e mínimo positivo de **1,401e-45 e 7,006e-45** — precisamente o piso **subnormal do float32 (2⁻¹⁴⁹)**. Contra-prova: no DoE do ZDT1 há **0** coordenadas repetidas, e o ZDT1 diverge em só 11/31 gerações, com deltas de −1 a −4. Na direção oposta há exatamente **1 caso** (MMF11_L geração 3, log 18 < fraco 19): ali dois pontos têm **vetores de objetivo idênticos em float32** (19 vetores únicos em 20), ou seja uma dominância verdadeira em float64 foi *apagada* pelo arredondamento. *(d) Mecanismo.* DTLZ4 com α=100 gera `x^100`; para `x ≲ 0,35` o valor **underflowa para 0,0 exato** no cast float32. Empate em uma coordenada torna um par que era mutuamente não-dominado em float64 **comparável** em float32 ⇒ a frente-1 **encolhe** (direção dominante, 43/44 casos). No caso inverso, o arredondamento colapsa dois pontos em vetores idênticos ⇒ a dominância some e a frente-1 **cresce** (1/44). Consequência prática: **em DTLZ4 a estrutura de frentes não é reconstruível a partir da ①** — o log é a fonte fiel, o recomputo não. Isto **não** contamina as métricas oficiais (IGD+/HV lêem a mesma ① float32 para *todos* os 21 configs, D69 — a comparação segue justa), mas contamina qualquer recomputo de dominância pós-hoc naquele problema. *(e)* **(2) D53 · direta** — e **item novo para a torre central** (§5).

---

**#12 — Operadores SBX/PM stock (Balde C).**
*(a) Canônico.* O `OperatorGAhalf` do PlatEMO usa SBX (`proC=1`, `dis_c=20`) + mutação polinomial (`proM=1` ⇒ prob. por variável `1/D`, `dis_m=20`). *(b) Nossa SPEC.* O bundle fixa "SBX 1/20 + PM 1/D/20 — **mesmos operadores dos EAs** → a única diferença piso×SA-MOEA é o surrogate", isolando o ganho do surrogate. *(c) Observado.* O header do ⑥ ecoa a string exata `"Balde C: SBX proC=1 dis_c=20 + PM proM=1 dis_m=20 (defaults OperatorGA do PlatEMO)"` em **25/25 células**, e o manifesto repete em `params.operadores`. Evidência indireta corroborante: com `proC=1` metade das variáveis de cada filho é herdada intacta, o que se manifesta nos empates de coordenada objetiva medidos no #11 nos problemas separáveis. *(d) Mecanismo.* O piso não tem `parameter` (o manifesto declara `parameter='nenhum'`), logo o PlatEMO usa os defaults do `OperatorGA` — que são exatamente os declarados. *(e)* **(1) · direta-declarativa** (o elo código↔log é coberto por `anchors.json`/`repos.lock`; a grandeza numérica não é exportada por linha).

---

**#13 — SMS-EMOA PURO, zero patches.**
*(a) Canônico.* A §3.2 é explícita: "SMS-EMOA **puro**, não o SMS-EMOA-MA" — a variante surrogate (mtm5) é só reserva (§3.6). *(b) Nossa SPEC.* D25 acrescenta o 4º piso justamente como *stock*, custo-zero de integração. *(c) Observado.* Em 25/25: `params.patches = "NENHUM — piso e stock do PlatEMO 4.15 por design"`; `params.parameter = "nenhum (SMS-EMOA PURO stock — nao e o SMS-EMOA-MA surrogate do §3.6)"`; `params.surrogate = "NENHUM (piso = MOEA puro)"`; `algo_version = "piso-SMSEMOA-PlatEMO4.15"`; header com `piso:true` e `surrogate:false`. E a prova negativa é dura: ③ com **0 linhas em 25/25**, `fit_series` vazio, `tempo_fit_surrogate_s = null`, `sonda.status='nao_se_aplica'` — não há **nenhum** traço de modelo em lugar nenhum das 6 camadas. *(d) Mecanismo.* Sendo stock, não há divergência D29 a arbitrar: o único vetor de infidelidade possível seria um patch, e os quatro campos declarativos + a ausência total de sinal de surrogate fecham essa porta. *(e)* **(1) · direta-declarativa + direta** (a ausência é medida, não só declarada).

---

**#14 — ③ vazia com schema completo.**
*(a) Canônico.* N/A. *(b) Nossa SPEC.* §3.2 ("tabela ③ vazia; série §17.6 vazia — sem surrogate") + DI-13.7 (o arquivo **existe** vazio por completude de camadas). *(c) Observado.* 0 linhas em 25/25, com o schema **íntegro e dimensionalmente correto**: 21 colunas em D=2/M=2, 28 em D=7/M=3, 29 em D=10/M=2, 33 em D=12/M=3, 41 em D=20/M=3 e D=22/M=2, **43 em DTLZ7 (D=22/M=3)** e 49 em D=30/M=2 — a diferença 41↔43 nas duas células D=22 é exatamente `mu_2` + `sigma_2` do terceiro objetivo. O `integridade_f52a.csv` traz **25 linhas smsemoa, todas `VAZIO / __surrogate.parquet`** — o veredito "por desenho" já registrado na F5.2a (105 ③ vazias = 4 pisos × 25 + sobol_batch × 5). *(d) Mecanismo.* O writer instancia o schema a partir de (D, M) e nunca recebe linha — a completude de camadas é preservada sem inventar dado. *(e)* **(2) §3.2/DI-13.7 · direta.**

---

**#15 — Sonda N/A por desenho (a régua comum não se aplica).**
*(a) Canônico.* N/A. *(b) Nossa SPEC.* A sonda (§17.2.2) mede `μ×verdade` num gabarito fixo; sem surrogate não há `μ`. *(c) Observado.* Em 25/25 o bloco `sonda` do manifesto traz `status='nao_se_aplica'`, `motivo="piso ONLINE = MOEA puro, sem surrogate a sondar (CONTRATO §3.2)"`, `n_blocos=0`, `n_linhas=0`; o `sonda_f52e.csv` (44.928 medições da F5.2e) tem **0 linhas smsemoa** — correto. Em consequência, **U4 (cadência), U5 (join posicional), U6 (WAPE/cobertura), U8 (`fe_treino_max`) e U11 (erro de fantasia) são N/A por desenho**, e U12 (⑦/`nd_pos_real`) é N/A por regime (online). *(d) Mecanismo.* O harness escreve o motivo explícito em vez de omitir o bloco — é a diferença entre "não se aplica" e "faltou", e é o que permite ao gate distinguir os dois. *(e)* **(2) §3.2/CONTRATO · direta.**

---

**#16 — Dedup D57/D89: a duplicata não gasta FE, gasta o slot (e o fechamento aritmético).**
*(a) Canônico.* O PlatEMO reavalia duplicatas sem cerimônia. *(b) Nossa SPEC.* D57 define `solution_id` por dedup-por-X bit-a-bit; D89 estabelece que a duplicata **não consome FE, mas consome o slot do infill**. A §3.2/v5.2.1 registra o efeito colateral **conhecido e aceito** no MOEA/D (T=`ceil(N/10)`=2 ⇒ 182 cache-hits ≈ 23% dos offspring em ZDT1/semente 0) e adverte explicitamente para que a dupla prova de sanidade **não leia isso como defeito**. *(c) Observado.* No smsemoa: **17 cache-hits de evolução em toda a bateria**, concentrados nas **3 células D=2** (MMF1 6, MMF11_L 6, MMF4 5) e **ZERO nas outras 22**. O fechamento aritmético `N·(n_ger−1) = Σ Δfe + cache_hits_da_evolução` vale **25/25** (atribuindo os guards por **ordem no fluxo do ⑥**, não por fronteira de `fe` — ver armadilha ⑤). Por geração, exato: MMF1 g2 `20 − (37−21) = 4` ≡ 4 guards; g3 `20 − (55−37) = 2` ≡ 2 guards. MMF11_L g2 `20−15=5` ≡ 5; g3 `20−19=1` ≡ 1. MMF4 g2 `20−17=3` ≡ 3; g3 `20−19=1` ≡ 1. *(d) Mecanismo.* MMF1/MMF4/MMF11_L têm **D=2** e caixa unitária: com N=20 e SBX/PM, a chance de recriar um X bit-idêntico é alta, ao passo que em D≥7 é praticamente nula. E — este é o contraste que interessa à D97 — o SMS-EMOA sorteia os pais com `randperm(end,2)` sobre a **população inteira**, enquanto o MOEA/D sorteia dentro de uma vizinhança de **2**; por isso o smsemoa tem 17 duplicatas em 25 células e o MOEA/D tem 182 numa só. É a mesma D89 produzindo efeitos opostos por causa do operador de acasalamento. *(e)* **(2) D57/D89 · direta.**

---

**#17 — O cache-hit de arranque: o seeding loga N+1 = 21.**
*(a) Canônico.* N/A. *(b) Nossa SPEC.* `params.seeding`: "os N entram como **cache-hit (0 FE)**" — os 20 semeados já estão na ①, então passam pelo wrapper de dedup e disparam o guard. O esperado é, portanto, exatamente **20**. *(c) Observado.* São **21 guards `cache_hit` com `fe == 11D−1` em 25/25 células**, com **20 `solution_id` distintos** e **sempre um repetido**: o indivíduo que ocupa a **posição 0 de ②(1)**, em 25/25 (ex.: ZDT1 sid 261 logado 2×, DTLZ7 sid 96, WFG1 sid 169, BBOB_F17 sid 4). O total de `cache_hits` do manifesto e do footer é `21 + evolução` e reconcilia com a contagem de guards do ⑥ em **25/25** (Σ = 542 cache-hits + 3 `hard_stop` = 545 guards). *(d) Mecanismo.* O efeito é **estritamente contábil**: a ① não ganha linha, a ② tem 20 ids únicos, o FE não se move (o `fe` do guard é o do fim do init), e o `opt = 20D` fecha exato. A causa exata (o primeiro indivíduo atravessa o wrapper duas vezes na montagem da população) não é provável só pelo dado. Classifico por **precedente**: o c217 registrou o fenômeno gêmeo ("cache-hit de arranque `fe=1/sid=0` em 25/25 — infla `cache_hits` em +1 sistemático") sob (2) D57/D89, e aqui a assinatura é ainda mais regular (sempre a posição 0, sempre `fe==init`, sempre exatamente +1). *(e)* **(2) D57/D89, por precedente c217 · direta** — com **confirmação OPCIONAL sugerida à F5.4** (§8) e item de contagem para a torre (§5).

---

**#18 — Geração fantasma e o guard `hard_stop` (as 3 células D=2).**
*(a) Canônico.* O PlatEMO checa terminação **entre** gerações. *(b) Nossa SPEC.* D21/D61 cortam **dentro** do laço, na avaliação exata de `maxFE`. *(c) Observado.* Em **22/25 células** o último evento de geração tem `fe == maxfe` e não há fantasma. Nas **3 células D=2**, porém, as duplicatas (#16) deixaram FE sobrando: MMF1 e MMF11_L terminam a geração 3 em `fe=55` e MMF4 em `fe=57`, contra `maxfe=61`. O run então **entra numa 4ª geração que é abortada no meio**: um guard **`hard_stop` com `fe=61, maxfe=61`** (o único guard não-`cache_hit` de toda a bateria, 3 ocorrências) e **16 linhas fantasma na ①** (6 + 6 + 4). Em MMF4 a geração fantasma inclui ainda 1 cache-hit (logado *depois* do evento da geração 3), totalizando 5 slots gastos antes do corte. Crucialmente: **`n_geracoes = 3` no manifesto, no footer, no ⑥, na ② e no ④** — ou seja, **o smsemoa conta apenas as gerações COMPLETAS**, ao contrário do c217 (onde `n_geracoes` incluía a abortada e as camadas tinham n−1). O `footer.termino` permanece `'normal'` nas 3, o que é correto: o hard-stop D21 **é** o término previsto. *(d) Mecanismo.* Duplicata não gasta FE ⇒ o orçamento sobrevive à geração ⇒ o laço externo reentra ⇒ a exceção do wrapper corta no FE 61. É a interação D89 × D21, e ela só aparece onde a taxa de duplicata é alta (D=2). *(e)* **(2) D21/D61/D89 · direta.**

---

**#19 — Timing: o ④ degenerado, a reconciliação com o ⑤ e o custo trivial.**
*(a) Canônico.* N/A. *(b) Nossa SPEC.* §17.6/v5.2.1 obriga `timing.tempo_total_s` no ⑤ e a série por geração no ④; DI-13.10 define as invariantes `fit + busca ≤ tempo_geracao`. Para um piso sem modelo, `fit`, `busca` e `pred_sonda` **devem** ser NULL — a invariante U7 é degenerada por desenho. *(c) Observado.* O ④ tem `n_geracoes` linhas em 25/25 (`T_rows_ok` 25/25) com `tempo_fit_s`, `tempo_busca_s`, `tempo_pred_sonda_s` e `n_acumulado` **100% NaN**, e o manifesto espelha `tempo_fit_surrogate_s = tempo_busca_s = tempo_pred_sonda_s = null` em 25/25. `tempo_geracao_s > 0` em **376/376** e a série do ④ é **bit-idêntica** à do ⑥ (`allclose` rtol 1e-5 em 25/25). `Σ ④ tempo_geracao ≤ ⑤ tempo_total` em 25/25 (Σ global 26,77 s de geração dentro de 134,94 s de wall — 19,8%; o restante é abertura/DoE/escrita/fechamento). `tempo_aval_real_s` soma 7,37 s = 27,5% do tempo de geração — coerente com um MOEA puro cujo custo é dominado pela avaliação real e pelo `CalHV`. **Custo total das 25 células: 134,94 s = 0,0375 h-core**, mediana 5,25 s, máximo 10,57 s (WFG5); em linha com os outros 3 pisos (moead 126,19 s · nsga2 128,65 s · nsga3 123,67 s). Projeção 30 sementes ≈ **1,12 h-core** — irrelevante diante das 10.173 h-core da campanha. *(d) Mecanismo.* A §3.2 promete "custo trivial (não treina GP)" e o dado confirma em 3 ordens de grandeza contra os dominantes (main/c149 2.131 h-core). É o que torna o piso uma régua **viável** em 30 sementes sem negociação de orçamento. *(e)* **(2) instrumentação DI-13.10/§17.6 · direta.**

---

**#20 — Término, status e `params` no ⑤.**
*(a) Canônico.* N/A. *(b) Nossa SPEC.* CONTRATO §5 exige `params` no ⑤; o mapa de término da Etapa 1 do protocolo adverte que o campo varia por config (`motivo_parada` no ⑤ | `footer.termino` | `footer.motivo`) — nunca ler `status` sozinho (bug B1). *(c) Observado.* `manifest.status='ok'`, `n_retries=0` e `fallback_ativado=false` em 25/25; `footer.status='ok'` e **`footer.termino='normal'` em 25/25**; **`motivo_parada` AUSENTE do manifesto em 25/25** ⇒ para o smsemoa **o campo de término é `footer.termino`** (mesma família dos MATLAB b1/e7). O ⑤ **TEM** a chave `params` com **12 chaves** (`N_nominal`, `N_efetivo`, `N_decisao`, `N_efetivo_nota`, `seeding`, `geracoes_derivadas`, `operadores`, `parameter`, `surrogate`, `patches`, `principio`, `casamento`) — o smsemoa está **fora** das 197 células/7 configs não-conformes da F5.2b, e o `contrato_f52b.csv` traz **0 linhas smsemoa**, confirmando. O `footer` é **1 registro** (não 2 como nos configs com despachante+runner separados). *(d) Mecanismo.* O writer do piso escreve `params` completo e ainda achata o essencial no header do ⑥ — redundância que salvou o c217 e que aqui é bônus. *(e)* **(2) doc-sync · direta.**

---

**#21 — CONTRATO §6: header sem `run_id`/`ambiente`, `repo_hash` vazio.**
*(a) Canônico.* N/A. *(b) Nossa SPEC.* CONTRATO §6 lista `run_id`, `ambiente` e `sigma_dict` no header do ⑥; D80 amarra o código por `repos.lock`/`anchors.json`, com o `repo_hash` do manifesto como o elo verificável. *(c) Observado.* O header do ⑥ tem 19 chaves (`alg, problema, semente, D, M, regime, maxfe, doe_hash, algo, piso, surrogate, principio, casamento, N_nominal, N_origem, seeding, operadores` + `ts/rec`) e **não tem `run_id`, `ambiente` nem `sigma_dict`** — a ausência do `sigma_dict` é **correta** (sem surrogate); as outras duas caem no item 5 do §0 do RELATORIO_F5 (doc-sync já escalado). O `manifest.repo_hash` está **vazio em 25/25** — e amostrei nsga2, c217, e7, b1 e c262: **vazio em todos** ⇒ é **sistêmico**, não do config. O `env` é idêntico nas 25 (`MATLAB 25.1.0.2973910 (R2025a) Update 1`, `stack=matlab-platemo`, `pymoo 0.6.2`) — consistente com o pin R2025a. *(d) Mecanismo.* O `repo_hash` vazio é o que rebaixa aspectos como #12/#13 de "direta" para "direta-declarativa": o log declara o parâmetro, mas o elo até o código-fonte exato depende do `anchors.json` fora do run. Não invalida nada nesta rodada (o piso é stock e as âncoras existem), mas **deve ser preenchido antes de M8/M9**. *(e)* **(2) doc-sync sistêmico · direta** — **item novo para a torre (§5)**.

---

**#22 — O casamento D25 com o c262: a régua faz o trabalho para o qual foi criada.**
*(a) Canônico.* N/A — é decisão de interpretação. *(b) Nossa SPEC.* D25/§3.2: SMS-EMOA ↔ c262 (qNEHVI) é o "espelho mecânico exato" — mesma seleção por HV, um com GP outro sem — e os **BO-especiais (c154, e81, c149) são lidos contra a BANDA min–máx dos 4 pisos**, não contra um piso único (DEF-A13). *(c) Observado.* Head-to-head IGD+ nas 21 células em que ambos existem: **o c262 vence o piso em 16/21, com razão mediana `sms/c262` = 2,51×** e casos de 2 a 3 ordens de grandeza (ZDT6 2.701×, ZDT1 997×, BBOB_F1 102×). **O piso vence em 5/21**: DTLZ4 (0,56×), DTLZ3 (0,58×), WFG4 (0,61×), DTLZ1 (0,82×) e BBOB_F17 (0,98×). Sobre a banda: **c149 fica ACIMA do envelope dos 4 pisos (pior que TODOS) em 19/25 problemas**; e81 fica dentro da banda em 12/25 e abaixo (melhor) em 6/25; c154 abaixo em 6/11. *(d) Mecanismo.* Este é o resultado que dá sentido ao config. O par HV-com-GP × HV-sem-GP isola o surrogate: em 16/21 células **o GP compra ~2,5× de IGD+**; nas 5 restantes — multimodais severos (DTLZ1/DTLZ3), α=100 (DTLZ4) e WFG4 — **o GP não compra nada e o piso puro é melhor**, o que é exatamente o tipo de achado que só um controle casado consegue produzir. E a banda faz o serviço previsto na DEF-A13: expõe o c149 como sistematicamente abaixo do envelope. *(e)* **(2) D25 · indireta** (a comparação é de resultado, não de mecanismo).

---

**#23 — Ramo interno do `Reduce` (HV exata para M=2 × Monte-Carlo para M≥3; ponto de referência interno). [T]**
O `.jsonl` registra o *efeito* da seleção (a população resultante), nunca o cálculo: não há `deltaS` por indivíduo, nem o ponto de referência usado, nem o número de amostras do estimador, nem qual dos dois ramos (contribuição de HV quando a pior frente é a frente-1 × contagem de dominância quando há mais de uma frente) foi acionado em cada passo. A assinatura de §7 (0,85% de quedas contra 5,70%/23,42% dos concorrentes) **prova o princípio**, e as 3 quedas de MMF16_20 (M=3, ≤0,092%) são **compatíveis** com estimador amostral + ref móvel, mas isso é inferência, não medição. Verificar exige código/re-run. **Classe T.**

---

**#24 — Seleção de pais `randperm(end,2)` (uniforme sobre a população, sem torneio). [T]**
Nenhuma das 6 camadas registra os pais de um filho. A única evidência é circunstancial e negativa: a taxa de duplicata bit-exata do smsemoa (17 em 25 células) é ~duas ordens de grandeza menor que a do MOEA/D com vizinhança T=2 (182 numa célula), o que é o que se espera de sorteio uniforme sobre 20 indivíduos contra sorteio dentro de 2. Sustenta a hipótese, não a prova. **Classe T.**

---

## 3. % por classe

**Denominador = total − T = 24 − 2 = 22.**

| classe | n | % (sobre 22) | itens |
|---|---:|---:|---|
| **(1)** conforme o método canônico | **7** | **31,8%** | #6, #7, #8, #10, #12 (DD), #13 (DD+D), #22… *não* — ver nota |
| **(2)** desvio sancionado | **15** | **68,2%** | #1, #2, #3, #4, #5, #9, #11, #14, #15, #16, #17, #18, #19, #20, #21, #22 |
| **(3)** inexplicado 🎯 | **0** | **0,0%** | — |
| **T** (fora do denominador) | 2 | — | #23 ramo interno do `Reduce`; #24 seleção de pais |

*Nota de leitura da linha (1)* — os 7 itens da classe (1) são **#6, #7, #8, #10, #12, #13** e, por completude do somatório, nenhum outro: são **6** itens em (1) e **16** em (2). Corrigindo a aritmética para não deixar ambiguidade ao D97:

| classe | n | % (sobre 22) | itens |
|---|---:|---:|---|
| **(1)** conforme o método canônico | **6** | **27,3%** | #6 (gerações/FE por geração) · #7 (seleção por HV) · #8 (elitismo μ+1) · #10 (frentes/ideal/nadir) · #12 (operadores, DD) · #13 (SMS-EMOA puro, DD+D) |
| **(2)** desvio sancionado | **16** | **72,7%** | #1 D21/D61 · #2 D63/D88 · #3 §3.2/D65/D20 · #4 D88 · #5 D88/§6.3 · #9 §17 · #11 D53 · #14 §3.2/DI-13.7 · #15 §3.2 · #16 D57/D89 · #17 D57/D89 · #18 D21/D61/D89 · #19 DI-13.10/§17.6 · #20 doc-sync · #21 doc-sync · #22 D25 |
| **(3)** inexplicado 🎯 | **0** | **0,0%** | — |
| **T** | 2 | — | #23, #24 |

Marca declarativa visível (Botão 3): **#12 e #13** contam como (1) na modalidade `direta-declarativa`; **#3** conta como (2) `declarativa + direta` (o valor N=20 é declarado E medido em 376/376 gerações).

---

## 4. PAPEL DE CONTROLE (substitui a comparação canônica — config sem artigo)

**A pergunta que o piso existe para responder (§3.2): "o surrogate compra alguma coisa, afinal?"** — e a resposta, com evidência, é **sim, em 55,7% das células, e a régua diz exatamente onde não compra**.

| evidência | número | leitura |
|---|---|---|
| Configs SA piores que o piso smsemoa (IGD+, main) | **135 de 305 (44,3%)** | quase metade das células SA não bate um MOEA puro de N=20 sob 31D−1 |
| Problemas em que o piso bate **TODAS** as SA | **2/25** — DTLZ3, WFG4 | alerta de atribuição: ali o surrogate é passivo puro |
| Rank global do smsemoa entre as 17 configs do main (IGD+) | **9,08 / 17** | um piso mediano é um bom piso: não é chão-de-fábrica nem competidor |
| Espelho casado c262 × smsemoa (D25) | **c262 vence 16/21, razão mediana 2,51×** | o ganho do GP sob o MESMO princípio de seleção, quantificado |
| Envelope dos 4 pisos vs BO-especiais (DEF-A13) | **c149 acima da banda em 19/25**; e81 dentro em 12/25, abaixo em 6; c154 abaixo em 6/11 | a banda discrimina — não é uma régua frouxa |
| Fidelidade do piso ao seu próprio princípio | **0,85% de quedas de HV vs 5,70% / 4,38% / 23,42%** | a régua mede HV *porque é HV*, não por acidente |
| Custo | **0,0375 h-core / 25 células** (≈1,12 h-core em 30 sementes) | a régua é gratuita — cabe em M8/M9 sem negociação |

**Posição entre os 4 pisos (IGD+, semente 42, 25 problemas):** melhor em **8/25** (BBOB_F5/F22/F37, DTLZ2, DTLZ3, MMF16_20, WFG1, WFG4), 2º em 6, 3º em 7, 4º em 4 (DTLZ1, DTLZ7, MMF1, MMF4) — **rank médio 2,28/4**; por HV, melhor em 7/25; por **HV da população final** (a métrica nativa do mecanismo, mesmo ref por problema), vitórias empatadas: nsga2 9 · **smsemoa 8** · nsga3 8 · **moead 0**. **Calibração do prior:** a nota v2 = 10 e o rótulo "piso mais forte (2/3 problemas em s0)" vinham de um piloto de 3 problemas na semente 0; em 25 problemas o smsemoa **não é o piso dominante em contagem de IGD+** (o NSGA-II vence 11/25), mas é (i) o melhor onde a frente premia distribuição por hipervolume — DTLZ2/DTLZ3/WFG4/MMF16_20, todos com frente-1 ocupando ~100% da população — e (ii) o pior em D=2 (MMF1/MMF4: só 2 gerações de evolução, o resultado é essencialmente o DoE) e em DTLZ7 (frente desconexa, onde a contribuição de HV privilegia extremos). **Nenhum desses fatos é infidelidade** — é o comportamento do S-metric selection, e a régua está informando corretamente.

*(Entrega 2 — comparação numérica com artigo: **N/A por desenho**. Não há paper de referência; o gabarito é a especificação canônica do bundle + as decisões do REGISTRO, usados aspecto a aspecto na §2.)*

---

## 5. Veredito de contrato (Entrega 3)

| fonte | achado F5.2 sobre o smsemoa | interpretação |
|---|---|---|
| `integridade_f52a.csv` | **25 linhas**, todas `__surrogate.parquet / VAZIO / linhas=0` | **por desenho, não defeito** — §3.2 ("tabela ③ vazia") + DI-13.7 (arquivo existe vazio por completude). Verifiquei que o schema está íntegro e dimensionalmente correto (21→49 colunas conforme D e M, incl. o par `mu_2/sigma_2` só em DTLZ7) |
| `contrato_f52b.csv` | **0 linhas** | ⑤ **tem** `params` (12 chaves) em 25/25 — o smsemoa está **fora** das 197 células/7 configs da não-conformidade da F5.2b |
| Gates F5.1 | dentro dos "13 configs MATLAB + os pisos: **zero vermelhos**" | cito, não re-verifico |
| F5.2c métricas | 25/25 células com IGD+/HV/IGD/GD/spacing/|ND| e trajetória | sem erro |
| F5.2d tempo | 25/25 com `timing.tempo_total_s`; **máquina vm3 em 25/25** (roster homogêneo) | o piso de ruído entre máquinas **não entra** nas comparações intra-piso (todos os 4 pisos + smsemoa na mesma vm3); entra apenas na leitura contra configs de outras máquinas, e foi aplicado |
| **Achados por-desenho** confirmados por mim | ⑥ com **1 footer** (não 2) · campo de término = `footer.termino` (`motivo_parada` ausente em 25/25) · header sem `run_id`/`ambiente` · `sigma_dict` ausente (correto) | os três primeiros são **doc-sync**, já escalado (item 5 do §0 do RELATORIO_F5); o quarto é conformidade |
| **Itens NOVOS para a torre central** | **(9)** `repo_hash` **vazio no manifesto** — sistêmico (smsemoa, nsga2, c217, e7, b1, c262 amostrados): quebra o elo D80 run↔código e rebaixa todo aspecto declarativo · **(10)** contagem `cache_hits` do seeding = **N+1** (o indivíduo da posição 0 é logado 2×), em 25/25, sem efeito analítico · **(11)** **export float32 (D53) impede reconstruir a estrutura de frentes em DTLZ4** (underflow: 46/131 zeros exatos em f1 e f2, mínimo positivo 1,401e-45 = subnormal float32) — mesma família dos falsos-vermelhos de tolerância da F5.1 | **nenhum é defeito de mecanismo**; (9) e (10) são de contrato/contagem; (11) é limite de verificabilidade a documentar (ou float64 seletivo para problemas mal-condicionados) |

**Veredito: nenhum defeito de mecanismo. Três itens por-desenho com regra citada, três itens de contrato/instrumentação escalados.**

---

## 6. SAÚDE em escala

**(i) O coração do config — a seleção por hipervolume é real.** Já detalhado em #7: **348/351 transições com HV populacional não-decrescente (99,15%)**, contra 94,30% (nsga2), 95,62% (nsga3) e 76,58% (moead) sobre o **mesmo DoE, o mesmo N, os mesmos operadores e o mesmo ponto de referência**. Nenhuma queda acima de 1% (nsga2 tem 6, moead 45). É a prova por dado de que o mecanismo entregue é S-metric selection e não um NSGA-II disfarçado — o requisito da D25 para que o casamento com o c262 signifique alguma coisa.

**(ii) Dinâmica populacional.** Taxa média de aceitação de filhos **44,8%** (33,0% em BBOB_F49 → 57,0% em ZDT6); 3.098 entrantes em 351 gerações (média 8,83/geração, máximo 14, nunca > N=20). Fração média da população na frente-1 = **0,681**, com três regimes distintos: **saturado** (DTLZ2, MMF16_20, WFG4 = 1,000 em todas as gerações — o `Reduce` opera sempre no ramo de HV), **misto** (ZDT1 0,748, DTLZ3 0,781, WFG2 0,746) e **estratificado** (ZDT4 0,250, ZDT6 0,286, BBOB_F37 0,314 — o ramo de contagem de dominância domina). Ganho de HV populacional do início ao fim positivo em **25/25**, mediana **+36,4%**, máximo WFG1 **+322%**, mínimo BBOB_F17 +1,6%.

**(iii) Trajetórias (20 checkpoints × 25 células = 475 transições).** **IGD+ monotônico não-crescente em 475/475 — 0 violações**; HV monotônico não-decrescente em **475/475 — 0 violações**. Redução de IGD+ do 1º ao último checkpoint entre **+26,2%** (ZDT6, o mais duro) e **+99,1%** (BBOB_F17); mediana ≈ 85%. As 104 quedas de `|ND|` **não são violação**: o conjunto não-dominado de um arquivo crescente encolhe quando um ponto novo domina vários antigos — comportamento esperado, e as células de maior queda (DTLZ3 10, DTLZ7 8, WFG2 8) são exatamente as de maior progresso relativo.

**(iv) Endpoint correto.** O smsemoa é **online**: o endpoint é a ① avaliada (D69), e a trajetória/métrica oficial é legítima — **não se aplica** o caveat da família offline (métricas que empatam por desenho e exigem a ⑦/`nd_pos_real`). Também **não se aplica** a análise de sonda/WAPE (0 linhas no `sonda_f52e.csv`, por desenho). A "curva de aprendizado" deste config é, por construção, a curva de HV populacional da §(i)/#7 — foi essa que usei.

**(v) Máquina e tempo.** 25/25 em **vm3** (roster homogêneo, sem correção O-19 aplicável); Σ 134,94 s (mediana 5,25 s/célula, máximo 10,57 s em WFG5). O piso de ruído entre máquinas (HV ≤1,55%; IGD+ ≤58,98%, O-18) é **irrelevante** para toda a análise intra-pisos desta seção (mesma máquina) e foi respeitado na leitura contra as configs SA da §4.

**Caveat de saúde (não de fidelidade):** em MMF1/MMF4/MMF11_L o piso roda **apenas 2 gerações completas** de evolução (D=2 ⇒ 40 FE de infill / N=20) e termina 4º entre os pisos; o resultado é essencialmente a qualidade do DoE. Não é defeito — é a consequência aritmética prevista pela §3.2 ("rende 2 gerações no pior caso D=2"). Para D97: **as 3 células D=2 têm poder discriminativo quase nulo como régua**, e devem ser lidas com essa ressalva.

---

## 7. SCORE e recomendação

# SCORE: 10 / 10 — ACEITAR

1. **Zero aspectos classe (3)** em 24 aspectos × 25 células. Todas as 16 divergências contra o método stock têm decisão citada (D21/D61, D63/D88, D20/D65/§3.2, D53, D57/D89, D25, DI-13.7/13.10, §17), e as 6 propriedades canônicas do SMS-EMOA que *podiam* ter sido quebradas — orçamento por geração, elitismo (μ+1), seleção por HV, estrutura de frentes, operadores stock, ausência de patch — foram **medidas e confirmadas**, não presumidas.
2. **A query-joia fecha e discrimina**: o hipervolume populacional é não-decrescente em 348/351 transições contra 94,3%/95,6%/76,6% dos outros três pisos no mesmo DoE, mesmo N e mesmos operadores — o princípio de seleção declarado pela D25 está **provado pelos dados**, que é o padrão máximo do protocolo (Etapa 3).
3. **As duas identidades estruturais fecham exatas**: seeding D88 recomputado do zero (NDSort+CrowdingDistance+índice) idêntico em 24/25 e **idêntico ao dos outros 3 pisos em 25/25** (com o subconjunto 15⊂20 nos 6 M=3, confirmando a §6.3 por dado); e o fechamento aritmético FE↔slots↔cache-hits↔geração-fantasma em 25/25.
4. **A única divergência não-trivial (44/376 frentes) é um teto de precisão, não de mecanismo**: causa provada até o bit (underflow subnormal float32 da D53 em DTLZ4; enriquecimento de empates 8,1× nas gerações divergentes; log dentro do envelope [fraco, estrito] em 375/376) — e a fonte fiel (o ⑥) permanece íntegra.
5. **O contrato está limpo** (fora das 197 não-conformidades da F5.2b, 0 linhas no `contrato_f52b.csv`, 25 linhas de integridade todas "③ vazia por desenho") **e o piso cumpre seu papel de régua com evidência quantificada** (44,3% das células SA abaixo dele; c262 comprando 2,51× mediano sob o mesmo princípio; banda D25 discriminando o c149 em 19/25). O que separaria de 10 seria um desvio, e não há: o T declarado (ramo interno do `Reduce`, sorteio de pais) é teto de instrumentação, contabilizado à parte conforme o Botão 2.

**Recomendação: ACEITAR** (sem caveat de fidelidade; com 1 caveat de saúde — poder discriminativo nulo das 3 células D=2 — e 3 itens de contrato/instrumentação para a F5.7). **Nada a enviar à F5.4** além da confirmação opcional abaixo.

---

## 8. Aspectos classe (3) 🎯

**Nenhum.** A verificação adversarial F5.4 **não recebe itens obrigatórios** do smsemoa.

**Confirmação OPCIONAL sugerida (não é classe (3)):** o **+1 sistemático do cache-hit de arranque** (#17) — 21 guards para 20 semeados, sempre o indivíduo da posição 0 de ②(1), em 25/25 células, com efeito analítico **nulo** (FE, ①, ② e o fechamento `opt = 20D` todos intactos). O *invariante* está provado por dado; o que não está é a *causa de código* (dupla passagem pelo wrapper de dedup na montagem da população). Classificado (2) pelo precedente idêntico do c217 (armadilha ⑤ daquele relatório). Uma leitura de 3 linhas do adapter do piso resolve — mesmo padrão da confirmação opcional do c311 aceita pelo autor.

---

## 9. Teto de verificabilidade (T) + armadilhas confirmadas na escala

**T — exige código ou re-run:**
`deltaS` por indivíduo e o ramo escolhido do `Reduce` (contribuição exata de HV para M=2 × estimativa Monte-Carlo para M≥3; nº de amostras; ponto de referência interno — apenas *inferido* pelas 3 quedas ≤0,092% de MMF16_20) · seleção de pais `randperm(end,2)` (nenhum log de pais em 376 gerações; sustentada só pelo contraste de duplicatas contra o MOEA/D-T=2) · quais variáveis o SBX/PM efetivamente cruzou/mutou por filho (η=20/20 e proC/proM são **eco de header**, não grandeza por linha) · a ordem interna dos N passos steady-state dentro de uma geração (a ② e o ⑥ só expõem o estado no fim do laço externo) · **estrutura de frentes de DTLZ4** (irreconstruível da ① por underflow float32 — o log é a única fonte fiel) · elo run↔código (`repo_hash` vazio ⇒ depende de `anchors.json`/`repos.lock` externos).

**Armadilhas confirmadas na escala** (25/25 salvo indicação):
① **`cache_hits` do seeding é N+1 = 21, não N=20** — o indivíduo da posição 0 de ②(1) é logado duas vezes; testar `cache_hits == N` reprova 25/25 falsamente.
② **`n_geracoes` conta só as gerações COMPLETAS** — ao contrário do c217, onde a fantasma entrava na contagem; aqui ⑥, ②, ④ e manifesto dizem todos o mesmo número, e as 16 linhas fantasma da ① (3 células D=2) **não têm geração associada em nenhuma camada**.
③ **`f_best` ≡ `ideal`** em 376/376 — é o vetor de mínimos componente a componente, **não** os objetivos de uma solução; usá-lo como "a melhor solução" é erro de leitura.
④ **Δfe entre gerações NÃO é sempre N** — é N menos as duplicatas daquela geração (D89); testar `Δfe == 20` reprova 3/25 células falsamente (MMF1 {16,18}, MMF11_L {15,19}, MMF4 {17,19}).
⑤ **Guards de cache-hit devem ser atribuídos à geração por ORDEM no fluxo do ⑥, não por fronteira de `fe`** — em MMF4 há um `cache_hit` com `fe=57` **depois** do evento da geração 3 (`fe=57`): pelo `fe` ele cai na geração 3 e quebra a aritmética; pela ordem cai na fantasma e o fechamento é exato em 25/25.
⑥ **A frente-1 recomputada da ① diverge do log em 11,7% das gerações** — e em **DTLZ4 em 13/13**, com a estrutura de frentes literalmente invertida no seeding (log 7 frentes/f1=23 × recomputo 23 frentes/f1=7). Causa: underflow subnormal float32 (D53). Reprovar o run por isso é falso-alarme; **o log é a fonte, não o recomputo**.
⑦ **`N_efetivo = 20` no smsemoa mesmo em M=3** — comparar populações com nsga3/moead nas 6 células M=3 (que rodam com 15) sem normalizar é comparar coisas diferentes; a interseção correta é `pop(nsga3) ⊂ pop(smsemoa)` na geração 1.
⑧ **`motivo_parada` NÃO existe no manifesto** — o campo de término é `footer.termino` (`'normal'` em 25/25, **inclusive nas 3 células que sofreram hard-stop D21 no meio de uma geração** — hard-stop *é* o término normal).
⑨ **③ vazia + `sonda='nao_se_aplica'` + `sigma_dict` ausente ⇒ U3, U4, U5, U6, U8, U11 e U12 são N/A por desenho** — o `sonda_f52e.csv` e o `contrato_f52b.csv` com 0 linhas smsemoa estão **corretos**; a ausência de linha não é ausência de verificação.

---

*Insumos pré-computados usados sem recomputo: `f5/metricas_finais_f52c.csv` · `f5/trajetorias/main_smsemoa_*_42.json` (25) · `f5/contrato_f52b.csv` (0 linhas smsemoa) · `f5/integridade_f52a.csv` (25 linhas, ③ vazia por desenho) · `f5/tempo_f52d.csv` (coluna `maquina` corrigida) · `f5/sonda_f52e.csv` (0 linhas smsemoa, correto). Achados F5.1/F5.2 citados e não re-verificados: gates "pisos = zero vermelhos", falsos-vermelhos de tolerância da ⑦, não-conformidade de `params` no ⑤ (197 células — smsemoa fora), doc-sync do CONTRATO §6.*

***Artefatos de evidência (diretiva de preservação do autor) — todos em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/smsemoa/`:*** `bateria_smsemoa.py` (bateria principal U1–U12 + módulo de família, 127 colunas × 25 células) → `aspectos_smsemoa.csv`, `evidencia_smsemoa.pkl` · `diag_doe_e_frentes.py` (DoE bit-a-bit, frentes, hard-stop, seeding entre pisos) → `diag_doe.csv`, `diag_frentes.csv`, `diag_hardstop.csv`, `diag_pisos_seeding.csv` · `diag_front1_precisao.py` (envelope fraco/estrito da dominância float32) → `diag_front1_precisao.csv` · `diag_hv_selecao.py` (**query-joia**: monotonicidade do HV populacional nos 4 pisos) → `diag_hv_selecao.csv`, `serie_hv_pop.json` · `diag_aritmetica.py` (fechamento U10) → `diag_aritmetica.csv` · `diag_papel_controle.py` (papel de régua, trajetórias, tempo) → `diag_papel_controle.csv`, `diag_pisos_igd.csv`, `diag_trajetorias.csv`. Interpretador: `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`.