# RELATÓRIO DE FIDELIDADE T11 — `smsemoa` · SMS-EMOA (piso online, sem surrogate) · validação da rodada T11

**Analista de fidelidade smsemoa · 2026-07-31 · protocolo v1.1 (Etapa 7, formato RICO) · READ-ONLY · corpus do MECANISMO = `resultados_experimentos/smsemoa/{25 problemas}/42/` (25 células, 376 gerações, 10.856 linhas da ①, 7.520 linhas da ②, 351 transições, 545 guards) · corpus da INSTRUMENTAÇÃO NOVA = `evidencia_T11/smoke_matlab/.../main/smsemoa/DTLZ2/42` (1 célula) · config SEM artigo (Entrega 2 = N/A) · comparação contra `f5/relatorios_config/smsemoa.md` (F5, score 10)**

> **Todos os números abaixo foram RE-MEDIDOS nesta sessão.** Nenhum foi copiado da F5 nem do handoff T11. Onde a re-medição confirma a F5, digo "reproduz"; onde diverge, digo o quanto.

---

## 1. Ficha do mecanismo (condensada)

**SMS-EMOA puro** (Emmerich/Beume/Naujoks 2005 — a referência que o próprio `SMSEMOA.m:6-9` cita), built-in do **PlatEMO 4.15**, **zero patches**. EA **steady-state (μ+1)**: `SMSEMOA.m:26-31` roda `while NotTerminated; for i = 1:Problem.N; Offspring = OperatorGAhalf(Problem, Population(randperm(end,2))); [Population,FrontNo] = Reduce([Population,Offspring],FrontNo); end; end` — a "geração" logada = N substituições unitárias; cada passo gera **1 filho de 2 pais sorteados uniformemente**, funde N+1 e descarta **1**: o de **menor contribuição de hipervolume (S-metric)** na pior frente (`Reduce.m:13-33`). É o **espelho mecânico do c262/qNEHVI** (D25/§3.2): mesma seleção por HV, um com GP, outro sem.

Instanciação nossa, com as divergências sancionadas NOMEADAS: `maxFE = 31D−1` com hard-stop exato **D21/D61** · **N = 20 CRAVADO** (§3.2/D65, protocolo Knowles/ParEGO) e **`N_efetivo ≡ N_nominal = 20` mesmo em M=3** (§6.3 — SMS-EMOA não usa lattice; NSGA-III/MOEA/D caem a 15) · população inicial **semeada do DoE compartilhado 11D−1** pelos melhores N por **NDSort + CrowdingDistance + índice (D88/D63)** · operadores **Balde C** (`OperatorGA` stock: SBX proC=1/dis_c=20 + PM proM=1/dis_m=20) · export **float32 (D53)** · dedup **D57/D89** (duplicata não gasta FE, gasta o slot) · **sem surrogate**: ③ vazia (DI-13.7), `fit_series` vazio, `sonda.status='nao_se_aplica'`. Evento de geração no ⑥ = `smsemoa_gen`; campo de término = **`footer.termino`** (`motivo_parada` ausente do ⑤ em 25/25) — agora normativo em `artifacts/mapa_termino.json`.

**Estado pós-T11 do config:** a s42 é **PRÉ-T11**, mas para o `smsemoa` a validade do corpus não depende do argumento geral 19/19 — ela foi **medida diretamente** (aspecto #25): o smoke T11 (`main/smsemoa/DTLZ2/42`, commit `195f64e`) reproduz a célula homônima da s42 **bit-a-bit em 5 das 6 camadas**; a única diferença em todo o dado é a coluna `tempo_geracao_s` do ④ (wall-clock).

---

## 2. DISSECAÇÃO DOS ASPECTOS (o CORE)

### 2.1 Tabela-resumo

Verif.: **D** = direta · **DD** = direta-declarativa · **C** = direta no **código lacrado** (`repos.lock/PlatEMO sha256_tree=fb9ed1d399d4`, LACRE OK conferido hoje) · **I** = indireta · **—** = balde T.
🆕 = aspecto novo ou reclassificado nesta rodada.

| # | aspecto | classe | verif. | resultado-síntese (25 células / 376 gerações) |
|---|---|---|---|---|
| 1 | Orçamento `31D−1` + hard-stop exato | (2) D21/D61 | D | 25/25 exatos; `fe_index` e `solution_id` densos 25/25; `init=11D−1` e `opt=20D` 25/25 |
| 2 | DoE 11D−1 bit-a-bit + `doe_hash` | (2) D63/D88 | D | **max\|ΔX\| = 0,0 em float32, 25/25**; `doe_hash` ⑤ ≡ sidecar **25/25** |
| 3 | `N=20`; `N_efetivo ≡ N_nominal` em M=3 | (2) §3.2/D65/D20 | DD+D | `n_pop=20` em **376/376**; ② com 20 linhas/geração em 25/25; 0 duplicatas intra-geração |
| 4 | Seeding D88 (NDSort+CD+índice) | (2) D88 | D | recomputo idêntico **24/25** (exceção DTLZ4, causa provada em #13) |
| 5 | Identidade de seeding entre os 4 pisos | (2) D88/§6.3 | D | ②(1) do smsemoa ≡ nsga2 25/25; nsga3/moead ⊂ (15⊂20) nos 6 M=3 |
| 6 | Laço (μ+1): N passos, 1 filho/passo | (1) | D+C | `n_ger = D+1` **25/25**; Δfe=20 em **345/351**; as 6 exceções = duplicatas, à unidade |
| 7 | **Seleção por contribuição de HV** (query-joia) | (1) | D | HV populacional não-decrescente em **348/351 (99,15%)** vs 94,30% nsga2 · 95,62% nsga3 · 76,58% moead |
| 8 | 🆕 **Ramo interno do `Reduce`** (M=2 exato/extremos protegidos × M≥3 Monte-Carlo) | (1) *[era **T** na F5]* | C+D | assinatura medida: `ideal` **nunca piora em M=2 (0/266)** e piora **10/85 (11,8%) em M=3** |
| 9 | Elitismo (μ+1) | (1) | D | **0 violações em 351 transições**; entrantes ≤ N em 100%, média 8,83/geração |
| 10 | 🆕 **Pais `randperm(end,2)`** (uniforme, sem torneio) | (1) *[era **T** na F5]* | C | `SMSEMOA.m:29` na árvore lacrada; log de pais é **exclusão sancionada** (CONTRATO §6.1, "Rejeitados no DI-10") |
| 11 | ② = snapshot da população, sem off-by-one | (2) §17 | D | 7.520 = 376×20; `ideal`/`nadir_pop` do ⑥(g) casam com ②(g) em 376/376 |
| 12 | Recomputo `ideal`/`nadir_pop`/`n_front1`/`nadir_f1` | (1) | D | ideal **376/376** · nadir_pop **376/376** (desvio rel. máx 5,9e-08 = ULP float32) · n_front1 332/376 · nadir_f1 358/376 |
| 13 | Teto de precisão float32 (D53) → **regra 11 do CONTRATO** | (2) D53 + T11/A37.2 | D | 44/376 divergentes; log ∈ [fraco,estrito] em **375/376**; empates **12,75 × 1,57 = 8,1×** |
| 14 | 🆕 **PlatEMO STOCK: operadores Balde C + zero patches — agora LACRADO** | (1) *[era **DD** na F5]* | **C** | `git status` do PlatEMO: 12 arquivos modificados, **0 em `SMS-EMOA/`**; `anchors.json`: 23 patches, **0 tocam SMSEMOA/Reduce/CalHV/OperatorGA** |
| 15 | ③ vazia + sonda N/A + `sigma_dict` explícito | (2) §3.2/DI-13.7 | D | 0 linhas em 25/25 (21→49 colunas conforme D,M); `sonda.status='nao_se_aplica'` 25/25; `sonda_f52e.csv` 0 linhas |
| 16 | Dedup D57/D89 (duplicata não gasta FE) | (2) D57/D89 | D | **17 cache-hits de evolução** em 3 células D=2; **fechamento aritmético 25/25** |
| 17 | Cache-hit de arranque **N+1 = 21** — 🆕 causa PROVADA no código | (2) D57/D89 | D+C | 21 guards em 25/25, sempre a posição 0 de ②(1); causa: `experiment.m:2424-2426` + `piso_init:2599` |
| 18 | Geração fantasma + guard `hard_stop` | (2) D21/D61/D89 | D | 3/25 células (D=2); 3 guards `hard_stop`; `n_geracoes` conta só as COMPLETAS |
| 19 | Timing ④/⑤: 3 NULL + reconciliação + custo trivial | (2) DI-13.10/§17.6 | D | fit/busca/pred_sonda **100% NaN** 25/25; Σ④ ≤ ⑤ 25/25; **0,0375 h-core** |
| 20 | Término: `footer.termino` + 🆕 `mapa_termino.json` (I-08) | (2) doc-sync ✅ | D | 1 footer 25/25; `termino='normal'` 25/25; artefato confere **25/25** |
| 21 | 🆕🎯 `params.geracoes_derivadas` — a ERRATA 5 deixou **off-by-one** | (2) doc-sync **com resíduo** | D | fórmula T11 acerta **0/28** contra `n_geracoes`; **28/28** contra `n_geracoes−1`. O texto diz "103/112" |
| 22 | 🆕 ⑤ `quinto_obrigatorio`: `campanha_id`/`repo_hash`/`sigma_dict` (I-09/B-03) | (2) doc-sync ✅ | D | s42: faltam os 3 em **25/25**. Smoke T11: **6/6 presentes** |
| 23 | CONTRATO §6: header do ⑥ sem `run_id`/`ambiente`/`params` | (2) doc-sync ❌ **não corrigido** | D | header 19 chaves em 25/25 **e no smoke** — diff de chaves s42×T11 = **∅** |
| 24 | Casamento D25 com o c262 (espelho HV) | (2) D25 | I | c262 vence **16/21**, razão mediana **2,51×** |
| 25 | 🆕 **Não-perturbação da instrumentação T11** | (2) verificação | D | ①②③⑥ **bit-idênticas** s42×smoke; única diferença em 6 camadas: `tempo_geracao_s` |
| 26 | `FrontNo` incremental do `UpdateFront` (o que o algoritmo DECIDE) | **T** | — | `Reduce.m:14,32` mantém FrontNo incrementalmente; o log grava um NDSort FRESCO (`piso_instrument.m:43`) |

---

### 2.2 Blocos narrativos

---

**#1 — Orçamento `maxFE = 31D−1` com hard-stop exato.**
*(a)* O SMS-EMOA canônico não prescreve orçamento; `Algorithm.NotTerminated` (`SMSEMOA.m:26`) avalia terminação **entre** gerações — o laço interno de N passos corre até o fim mesmo estourando. *(b)* D21/D61 impõem hard-stop **exato** por exceção dentro do wrapper de FE, para que os 21 configs partilhem o denominador. *(c)* Re-medido: `len(①) == 31D−1` e `fe_final == maxfe` em **25/25**; `fe_index` e `solution_id` estritamente `arange(31D−1)` em **25/25**; `fase` fecha `init = 11D−1` e `opt = 20D` **exatos em 25/25**, inclusive nas 3 células que sofreram hard-stop no meio de geração (MMF1/MMF11_L/MMF4: init=21, opt=40). *(d)* O wrapper conta FE reais; duplicatas bit-exatas não incrementam (D89), o laço prossegue e a exceção corta no FE exato. *(e)* **(2) D21/D61 · direta.**

---

**#2 — DoE 11D−1, bit-a-bit contra o artefato.**
*(a)* PlatEMO inicializaria com `Problem.Initialization(N)` interno. *(b)* D63 substitui por carga do artefato LHS-maximin (`SeedSequence((semente, problema_id))`) e D88 define como ele vira população — o objetivo é o pareamento exato entre os 21 configs. *(c)* Confrontei a matriz X do artefato contra `fase=='init'` da ①: **`max|ΔX| = 0,0` em float32 nas 25 células**, ordem preservada, resíduo em float64 ≤ **1,907e-06** (o arredondamento do export D53). O `doe_hash` do ⑤ ≡ `doe_hash` do sidecar em **25/25** *(a F5 reportava esta checagem; a minha primeira passada dela deu 0/25 por eu ler a chave errada do sidecar — corrigido e re-medido: 25/25)*. *(e)* **(2) D63/D88 · direta.**

---

**#3 — `N = 20` e `N_efetivo ≡ N_nominal` mesmo em M=3.**
*(a)* Default PlatEMO N=100. *(b)* §3.2 crava 20 (Knowles/ParEGO: sob orçamento mínimo o piso calibra-se REDUZINDO a população; N=100 é infactível em D=2, onde a pop superaria o DoE de 21). §6.3 registra a consequência: `UniformPoint(20,3)` → H=4 → **15 vetores**, logo NSGA-III/MOEA-D rodam com 15 e NSGA-II/SMS-EMOA mantêm 20. *(c)* `n_pop == 20` em **376/376** gerações; ② com **exatamente 20 linhas por geração em 25/25** e **zero duplicatas intra-geração**; `N_nominal = N_efetivo = 20` no ⑤, header e footer das 25, inclusive nos 6 problemas M=3. *(d)* O SMS-EMOA não constrói lattice — o `Reduce` opera sobre a população crua, e o arredondamento do `UniformPoint` não o toca. *(e)* **(2) §3.2/D65/D20 · declarativa + direta.**

---

**#4 — Seeding D88: os melhores N do DoE por NDSort + CrowdingDistance.**
*(a)* Não existe no stock — é acoplamento nosso, e o código dele está em `experiment.m:2409-2420` (`sortrows([FrontNo, -CrowdDis, índice],[1 2 3])`). *(b)* D88: "melhores por não-dominância; desempate por crowding distance, determinístico" — reprodutibilidade sem sorteio. *(c)* Reimplementei NDSort + crowding (∞ nos extremos, desempate final por índice crescente) sobre os `11D−1` primeiros pontos da ① e comparei ao conjunto `②(g=1)`: **idêntico em 24/25**; `n_frentes`/`n_frente1` do evento `seeding` reproduzidos em **24/25**. A flag `frente1_excede_pop=true` aparece em **6/25** — nesses, o desempate por CD é o único critério. A única exceção é DTLZ4 (#13). *(e)* **(2) D88 · direta.**

---

**#5 — Identidade de seeding entre os 4 pisos (a prova cruzada).**
*(b)* §3.2: os 4 pisos partem do MESMO DoE pela MESMA regra — é o que torna a comparação entre pisos uma comparação de *seleção*. *(c)* `②(primeira geração)` de smsemoa ≡ nsga2 em **25/25** (mesmos 20 `solution_id`); nsga3/moead ≡ nas 19 células M=2 e, nas 6 M=3, os seus **15 são subconjunto estrito dos 20**. *(d)* A ordem total (frente, CD, índice) é aninhada em N: os melhores 15 estão contidos nos melhores 20. Prova que (i) a D88 é compartilhada, (ii) o corte 20→15 é do lattice e não de outra regra, (iii) qualquer diferença de desempenho entre os 4 pisos é atribuível **só** ao princípio de seleção. *(e)* **(2) D88/§6.3 · direta.**

---

**#6 — O laço (μ+1) aninhado: N passos, 1 filho por passo.**
*(a)* `SMSEMOA.m:26-31` — a geração externa consome **exatamente N avaliações** (`OperatorGAhalf` devolve metade da prole usual = 1 filho de 2 pais). Isto agora é lido **na árvore lacrada**, não inferido. *(b)* §3.2: "gerações são derivadas = K ÷ população", K = 20D. Nada mudou no laço. *(c)* `n_geracoes = D + 1` em **25/25** (a geração 1 é o snapshot da população semeada, `fe = 11D−1`, **zero FE gasto**); Δfe entre gerações consecutivas é **exatamente 20 em 345 das 351 transições**; as 6 exceções vivem nas 3 células D=2 (MMF1 {16,18}, MMF11_L {15,19}, MMF4 {17,19}) e são explicadas **à unidade** pelas duplicatas (#16). *(e)* **(1) conforme o método canônico · direta + código.**

---

**#7 — Seleção por contribuição de hipervolume (S-metric): a query-joia.**
*(a)* `Reduce.m:13-33`: identifica a **pior frente**, calcula `deltaS` de cada solução dela e remove `min(deltaS)`. A consequência mecânica é uma quase-garantia de **monotonicidade do HV populacional** — propriedade que nenhum dos outros 3 pisos tem (crowding, nicho de referência, PBI). *(b)* D25/§3.2 escolhe o SMS-EMOA *por causa* disso. Nada foi alterado. *(c)* Re-medi a série de HV da população geração a geração, camada ②×①, com **ponto de referência FIXO por problema, comum aos 4 pisos** (máximo da união das quatro ① + 1%), usando **HV EXATO** — fórmula 2D para M=2 e **fatiamento exato** para M=3 (a F5 usara estimador; troquei justamente para não confundir ruído com mecanismo):

| piso | transições | quedas | % | quedas > 1% | pior queda relativa |
|---|---:|---:|---:|---:|---:|
| **smsemoa** | 351 | **3** | **0,85%** | **0** | **−0,092%** |
| nsga3 | 388 | 17 | 4,38% | 0 | −0,83% |
| nsga2 | 351 | 20 | 5,70% | 6 | −4,62% |
| moead | 444 | 104 | 23,42% | 45 | −20,99% |

Zero quedas em **24 das 25 células**; as 3 estão todas em **MMF16_20** (transições 11→12, 12→13, 19→20: **−0,0909%, −0,0250%, −0,0916%**). Ganho de HV do início ao fim positivo em **25/25** (mediana **+36,4%**, máximo WFG1 **+324,1%**, mínimo BBOB_F17 **+1,6%**). *(d)* A monotonicidade **discrimina 6,7× contra o NSGA-II e 27× contra o MOEA/D no mesmo dado, com o mesmo DoE, o mesmo N e os mesmos operadores** (o #5 garante que só a seleção difere). O resíduo de MMF16_20 é dissecado no #8 — e, com HV exato, **não é ruído do meu estimador**: é o ramo Monte-Carlo do algoritmo. *(e)* **(1) · direta** — *o uso do hipervolume como critério de seleção está PROVADO pelos dados.*

---

**#8 🆕 — O ramo interno do `Reduce`: de teto T a aspecto MEDIDO.**
*(a) O que o método faz.* `Reduce.m:20-28`, agora legível na árvore **lacrada**:
```
deltaS = inf(1,N);
if M == 2
    [~,rank] = sortrows(PopObj);
    for i = 2 : N-1     % <- os DOIS extremos ficam com deltaS = inf
        deltaS(rank(i)) = (PopObj(rank(i+1),1)-PopObj(rank(i),1)).*(PopObj(rank(i-1),2)-PopObj(rank(i),2));
elseif N > 1
    deltaS = CalHV(PopObj, max(PopObj,[],1)*1.1, 1, 10000);   % Monte-Carlo, 10.000 amostras, ref MÓVEL
```
Duas propriedades caem daí: **em M=2 a contribuição é EXATA e os extremos lexicográficos da pior frente são intocáveis** (`deltaS = inf` ⇒ nunca são o `min`); **em M≥3 é uma ESTIMATIVA Monte-Carlo com 10.000 amostras e referência móvel `1,1 × max` do último front** (`CalHV.m:17-36`), que dá valor **finito a todos** — nenhum extremo protegido.
*(b) Nossa SPEC.* Não toca no ramo (piso stock). A F5 classificou este item **T** ("não exportado; inferido só por assinatura").
*(c) Observado — o teste discriminativo que a propriedade prediz.* Se os extremos são intocáveis em M=2, o vetor `ideal` da população **nunca pode piorar**; em M≥3, pode. Medi `ideal` componente a componente nas 376 gerações, nos 4 pisos:

| piso | M=2: transições / pioras do `ideal` | M=3: transições / pioras |
|---|---|---|
| **smsemoa** | 266 / **0 (0,00%)** | 85 / **10 (11,76%)** |
| nsga2 | 266 / 0 | 85 / 0 |
| nsga3 | 266 / 0 | 122 / 12 (9,84%) |
| moead | 324 / 79 (24,38%) | 120 / 46 (38,33%) |

O **smsemoa é o único piso cujo padrão de proteção dos extremos MUDA com M — e muda exatamente onde `Reduce.m:21` troca de ramo.** As pioras em M=3 concentram-se em **MMF16_20 (6 de 20 transições)**, que é também a única célula com queda de HV — e é uma das duas células M=3 com `frac_front1 = 1,000` (o ramo de HV roda sobre a população inteira em **21/21** gerações).
*(d) Mecanismo.* Com 10.000 amostras e referência local móvel, o `min(deltaS)` pode cair sobre um indivíduo cuja contribuição verdadeira (sob referência global fixa) não é a menor — o descarte é **ótimo sob a referência do algoritmo** e ligeiramente subótimo sob a minha. Magnitude ≤ 0,092% ⇒ é a resolução do estimador do PlatEMO, não mudança de princípio. *(e)* **(1) conforme o método canônico · direta no código lacrado + assinatura medida no dado.** *(Resíduo T: os `deltaS` por indivíduo continuam não exportados — ver #26.)*

---

**#9 — Elitismo (μ+1): nada entra que não tenha acabado de ser avaliado.**
*(a)* Cada passo funde N+1 e remove 1 ⇒ `②(g+1) ⊆ ②(g) ∪ filhos(g)`, sem re-inserção de descartados. *(c)* Testei em cada uma das **351 transições** a inclusão contra `②(g) ∪ {solution_id ∈ [fe(g), fe(g+1))}`: **0 violações em 351**. Entrantes por geração entre 0 e 14, nunca > N: média **8,83** (44,2% de N=20). *(d)* Prova conjunta de que (i) a ② reflete a população e não um arquivo, (ii) os `solution_id` são atribuídos na ordem de avaliação e a janela corresponde aos filhos daquela geração, (iii) não há contaminação por arquivo externo. *(e)* **(1) · direta.**

---

**#10 🆕 — Seleção de pais `randperm(end,2)`: de teto T a verificado.**
*(a)* `SMSEMOA.m:29`: `OperatorGAhalf(Problem, Population(randperm(end,2)))` — **sorteio uniforme de 2 índices distintos sobre a população inteira, sem torneio**. *(b)* A F5 classificou **T** porque nenhuma das 6 camadas registra os pais de um filho. A leitura correta é outra: o CONTRATO §6.1 lista explicitamente **"genealogia de operadores/pais por indivíduo"** entre os *"Rejeitados no DI-10 (inacessíveis sem patch invasivo no miolo stock — viola patch-mínimo/D30)"* — a ausência é **sancionada e declarada**, não uma lacuna. *(c)* Com a árvore agora **lacrada por content-hash** (`fb9ed1d399d4`, LACRE OK) e `git status` mostrando **zero modificações em `SMS-EMOA/`**, o operador de acasalamento é verificável no código com a mesma força de um pin. Corroboração indireta no dado: 17 duplicatas bit-exatas em 25 células, contra 182 numa única célula do MOEA/D com vizinhança T=2 — exatamente a razão esperada entre sorteio uniforme sobre 20 e sorteio dentro de 2. *(e)* **(1) · direta no código lacrado + exclusão sancionada do log.**

---

**#11 — ② = snapshot da população, sem off-by-one.**
*(b)* CONTRATO §17 define a ② como a composição da população por geração; vale o alerta do c217, onde a ② era o `Arc` com snapshot no INÍCIO da geração. *(c)* `len(②) = 20 × n_geracoes` em **25/25** (7.520 linhas), todos os grupos com exatamente 20, **zero duplicatas intra-geração**. O decisivo: `ideal`, `nadir_pop` e `nadir_front1` logados no ⑥ da geração g são reproduzidos da `②(g)` (#12) — houvesse deslocamento, casariam com g−1. *(d)* ② e evento `smsemoa_gen` são escritos no mesmo instante (fim do laço externo, `piso_instrument.m:3` "DEPOIS do hook_output que já fez o bumpGen"), o que elimina o off-by-one do c217. *(e)* **(2) instrumentação §17 · direta.**

---

**#12 — Recomputo `ideal` / `nadir_pop` / `n_front1` / `nadir_front1` da ②×①.**
*(b)* DI-10/S.7.1 enriqueceram o ⑥ com esses campos exatamente para a verificação a posteriori sem re-run. *(c)* Nas 376 gerações, com a **tolerância correta para a dicotomia ①=float32 × log=float64** (a F5 não a explicitou; com `atol=1e-12` o teste reprova quase tudo por artefato de precisão): `ideal` casa **376/376** com desvio relativo máximo **5,71e-08**; `nadir_pop` **376/376**, máximo **5,89e-08** — ambos ≈ 1 ULP de float32, isto é, igualdade exata no espaço em que o dado vive. `nadir_front1` **358/376** e `n_front1` **332/376 (88,3%)**; as 44 divergências são inteiramente absorvidas pelo #13. `f_best ≡ ideal` em **376/376** — e agora sabe-se por quê: `piso_instrument.m:38,57-58` emite o **mesmo vetor** sob os dois nomes, com o comentário explicando que o contrato pede "ideal/nadir" e o mínimo comum pede "f_best[]". *(e)* **(1) · direta.**

---

**#13 — O teto de precisão float32 (D53) — e a regra 11 do CONTRATO que nasceu dele.**
*(a)* O PlatEMO ordena em float64 (`NDSort.m` → `ENS_SS`, que faz `unique(PopObj,'rows')` e trata vetores idênticos como **mutuamente não-dominados**, mesma semântica do meu recomputo). *(b)* D53 manda exportar float32 sem arredondamento. *(c)* 44 das 376 gerações (11,7%) têm `n_front1` recomputado ≠ logado. Envelope: **o valor logado cai em [fraco, estrito] em 375/376**. O discriminante é o número de coordenadas objetivas repetidas na população: **12,75 em média nas gerações divergentes contra 1,57 nas concordantes — enriquecimento de 8,1×** (reproduz a F5 ao centésimo). O caso extremo é **DTLZ4**, onde `x^100` com α=100 underflowa para 0,0 exato no cast float32 e a estrutura de frentes fica **irreconstruível da ①** — a única célula em que o seeding recomputado (#4) não fecha. *(d) O que a T11 fez com isso.* Meu item (11) da F5 virou **`CONTRATO_DE_DADOS.md` §10 regra 11** ("[T11/A37.2] DOMINÂNCIA sobre ① ou ⑦ é LOSSY"), com a medição do schema por `read_schema` registrada em `REGISTRO PARTE A37.2`. E a decisão explícita foi **NÃO mexer no D53** (`PLANO_RODADA_PERFEITA:88`: "Mexer no D53 (export float32) — caro e de raio largo"). Ou seja: o achado foi aceito como **teto declarado**, não como defeito — a resposta certa. *(e)* **(2) D53 + T11/A37.2 · direta.**

---

**#14 🆕 — PlatEMO STOCK: operadores Balde C + zero patches — e o lacre que faltava.**
*(a)* `OperatorGAhalf` usa SBX (`proC=1`, `dis_c=20`) + PM (`proM=1` ⇒ 1/D por variável, `dis_m=20`). A §3.2 é explícita: "SMS-EMOA **puro**, não o SMS-EMOA-MA (§3.6)". *(b)* O bundle fixa os mesmos operadores dos EAs para isolar o ganho do surrogate; D25 acrescenta o 4º piso como *stock*, custo-zero. *(c) O que a F5 podia dizer, e o que se pode dizer hoje.* A F5 classificou #12/#13 como **`direta-declarativa`**, com a justificativa "o elo código↔log é coberto por `anchors.json`/`repos.lock`". **Essa justificativa era falsa à época** — e quem provou foi a própria T11: o commit `53c129a` documenta que *"o `dir_map` do preflight tinha 9 entradas e o `repos.lock` tem 11: `PlatEMO` e `botorch` caíam no `continue` e **nunca eram checados**"*, e que os 12 arquivos patchados viviam como working-tree changes num repo aninhado invisível dos dois lados. **O pin do PlatEMO era decorativo.** Hoje: `preflight.py` (rodado read-only, `repos.lock` conferido intacto depois) devolve `PlatEMO git HEAD b686ca20cd89 (pin OK)` **e** `content-hash fb9ed1d399d4 LACRE OK`; `git status --porcelain` dentro da árvore lista **12 arquivos modificados — CSEA, EDN-ARMOEA, K-RVEA, PC-SAEA, ParEGO — e nenhum em `SMS-EMOA/`**; `anchors.json` tem **23 patches** e **zero** tocam `SMSEMOA.m`, `Reduce.m`, `CalHV.m`, `UpdateFront.m` ou `OperatorGA`. Nos dados, a prova negativa continua dura: ③ com **0 linhas em 25/25**, `fit_series` vazio, `params.patches = "NENHUM — piso e stock do PlatEMO 4.15 por design"`, `parameter='nenhum'`, `surrogate=false` no header — 25/25. *(d)* O aspecto **sobe de `direta-declarativa` para `direta no código lacrado`**: a pureza do piso deixou de depender de um eco de log e passou a depender de um sha256 de árvore conferido. *(e)* **(1) · direta (código lacrado).**

---

**#15 — Ausência de surrogate DECLARADA: ③ vazia, sonda N/A, `sigma_dict` explícito.**
*(b)* §3.2 ("tabela ③ vazia; série §17.6 vazia") + DI-13.7 (o arquivo **existe** vazio por completude de camadas). *(c)* 0 linhas em 25/25, schema íntegro e dimensionalmente correto (**21, 28, 29, 33, 41, 43 e 49 colunas** conforme D e M — o par 41↔43 nas duas células D=22 é exatamente `mu_2`+`sigma_2` do 3º objetivo). `sonda.status='nao_se_aplica'` com motivo explícito em 25/25, `n_blocos=0`; o `sonda_f52e.csv` (44.928 medições) tem **0 linhas smsemoa** — correto. Em consequência **U3, U4, U5, U6, U8, U11 e U12 são N/A por desenho**, e a **regra 12 do CONTRATO é vacuosa aqui** (não há bloco `sonda` nem `sonda_estratificada`; a régua Sobol não se aplica a um config sem μ). *(d) 🆕 O que a T11 acrescentou.* No smoke, o ⑤ passou a trazer também **`sigma_dict = {status:'nao_se_aplica', motivo:'piso ONLINE = MOEA puro: a ③ existe (contrato de camadas) mas nasce VAZIA — nao ha modelo cujas colunas descrever', terceira:'0 linhas por desenho'}`** — na s42 a chave era **ausente em 25/25**. É a lição §4.2.2 da campanha ("INCONCLUSIVO tem duas espécies") aplicada: "não se aplica por desenho" deixou de ser indistinguível de "faltou". *(e)* **(2) §3.2/DI-13.7 · direta.**

---

**#16 — Dedup D57/D89: a duplicata não gasta FE, gasta o slot.**
*(b)* D57 define `solution_id` por dedup-por-X bit-a-bit; D89 estabelece que a duplicata não consome FE mas consome o slot do infill. *(c)* **17 cache-hits de evolução em toda a bateria**, concentrados nas 3 células D=2 (MMF1 6, MMF11_L 6, MMF4 5) e **ZERO nas outras 22**. O fechamento `N·(n_ger−1) = Σ Δfe + cache-hits da evolução` vale **25/25** — mas **só** atribuindo os guards por **ORDEM no fluxo do ⑥**; pela fronteira de `fe` o MMF4 quebra (armadilha ⑤ da F5, reconfirmada: há 1 cache-hit `fe=57` logado **depois** do evento da geração 3). *(d)* D=2 com caixa unitária e N=20 torna alta a chance de recriar um X bit-idêntico; em D≥7 é praticamente nula. O contraste com o MOEA/D (182 numa célula, vizinhança T=2) é a mesma D89 produzindo efeitos opostos por causa do operador de acasalamento — hoje ancorado no `randperm(end,2)` do #10. *(e)* **(2) D57/D89 · direta.**

---

**#17 — O cache-hit de arranque N+1 = 21: a causa, enfim, provada.**
*(a/b)* `params.seeding` promete "os N entram como cache-hit (0 FE)" — o esperado seria 20. *(c)* Medi **21 guards `cache_hit` com `fe == 11D−1` em 25/25**, com **20 `solution_id` distintos** e **sempre um repetido**: o indivíduo da **posição 0 de ②(1)**, em **25/25**. O total de `cache_hits` do ⑤ (`21 + evolução`) reconcilia com a contagem de guards do ⑥ em **25/25** (Σ = 542 cache-hits + 3 hard_stop = **545 guards**). *(d) 🆕 A causa.* A F5 classificou por precedente (c217) e deixou uma "confirmação OPCIONAL sugerida à F5.4". **Fecho-a agora por leitura de código**, que a T11 tornou legítima ao lacrar a árvore: `src/experiment.m:2424-2426` documenta em comentário — *"O probe do construtor (`Initialization(1)`) pega `Xsel(1,:)`, que já está no cache => 0 FE"* — e `piso_init` (`experiment.m:2599-2611`) devolve `Xsel(1:min(N,n_init),:)`. Logo: **1 probe do construtor do `UserProblem` + 20 do `Problem.Initialization()` de `SMSEMOA.m:22` = 21 guards, e o repetido é necessariamente `Xsel(1,:)` = a posição 0 da população.** O efeito permanece estritamente contábil: a ① não ganha linha, a ② tem 20 ids únicos, `opt = 20D` fecha exato. *(e)* **(2) D57/D89 · direta + código — item da F5 ENCERRADO.**

---

**#18 — Geração fantasma e o guard `hard_stop` (as 3 células D=2).**
*(c)* Em **22/25** o último evento de geração tem `fe == maxfe`. Nas 3 células D=2, as duplicatas deixaram FE sobrando (MMF1/MMF11_L terminam a geração 3 em fe=55, MMF4 em fe=57, contra maxfe=61): o run reentra numa 4ª geração abortada no meio — **3 guards `hard_stop`** (os únicos guards não-`cache_hit` das 25 células, medidos) e **16 linhas fantasma na ①**. Crucialmente, `n_geracoes = 3` no ⑤, no footer, no ⑥, na ② **e no ④** — as quatro camadas concordam em 25/25 (`n_ger manifesto == jsonl == pop == timing` em **25/25**), ao contrário do c217. `footer.termino` continua `'normal'` — o hard-stop D21 **é** o término previsto. *(d)* Interação D89 × D21, visível só onde a taxa de duplicata é alta. *(e)* **(2) D21/D61/D89 · direta.**

---

**#19 — Timing: o ④ degenerado, a reconciliação e o custo trivial.**
*(b)* §17.6/DI-13.10 obrigam `timing.tempo_total_s` no ⑤ e a série por geração no ④; para um piso sem modelo `fit`/`busca`/`pred_sonda` **devem** ser NULL — U7 é degenerada por desenho. O `piso_instrument.m:20-24` documenta o porquê de NULL e não 0 ("gravar 0 diria que a busca custou zero"). *(c)* ④ com `n_geracoes` linhas em **25/25**, `tempo_fit_s`/`tempo_busca_s`/`tempo_pred_sonda_s` **100% NaN** em 25/25; série do ④ bit-idêntica à do ⑥ (`allclose` rtol 1e-5) em **25/25**; `Σ④ ≤ ⑤` em **25/25** (Σ 26,77 s de geração dentro de 134,94 s de wall). `tempo_aval_real_s` **não-nulo em 25/25**, Σ 7,37 s. **Custo total das 25 células: 134,94 s = 0,0375 h-core**, mediana 5,25 s, máximo 10,57 s (WFG5); projeção 30 sementes ≈ **1,12 h-core**. *(d) 🆕* A T11 tornou isto **auditável por gate**: `contrato_61.json.configs.smsemoa.nao_se_aplica = {tempo_fit_s, tempo_busca_s}` — os NULLs deixaram de depender de o auditor conhecer a DI-13.2. *(e)* **(2) DI-13.10/§17.6 · direta.**

---

**#20 — Término: `footer.termino` e o `mapa_termino.json` (I-08).**
*(b)* O protocolo adverte que o campo de término varia por config e que ler `status` sozinho é o bug B1. *(c)* Re-medido: `manifest.status='ok'`, `n_retries=0`, `fallback_ativado=false` em 25/25; **1 footer em 25/25** (não 2), `footer.termino='normal'` em **25/25**, e **`motivo_parada` AUSENTE do ⑤ em 25/25**. O ⑤ **tem** `params` com 12 chaves — o smsemoa está fora das 197 células não-conformes da F5.2b (`contrato_f52b.csv`: **0 linhas smsemoa**, re-conferido). *(d) 🆕 A correção.* O que na F5 era a **armadilha ⑧** (prosa num relatório) virou artefato normativo: `artifacts/mapa_termino.json` declara `smsemoa: {familia:'matlab', evento_geracao:{rec:'smsemoa_gen'}, campo_termino:'termino', n_footers_esperado:[1]}` e é consumido por `gates_proveniencia.py (G-2)`, `portao.py` e `censo42.py`. Conferi o artefato contra o corpus: **25/25 células batem** com o que ele declara. *(e)* **(2) doc-sync · direta — CORRIGIDO.**

---

**#21 🆕🎯 — `params.geracoes_derivadas`: a ERRATA 5 corrigiu a fórmula e deixou um off-by-one.**
*(a/b)* A string antiga do ⑤ dizia `"20D ÷ N_efetivo (o DoE 11D-1 e gasto ANTES do Solve)"`. A ERRATA 5 do handoff (`I-13/A24`) reporta que essa forma "acerta 0/112" e a substituiu, em `src/experiment.m:2516-2527`, por um texto longo e honesto: *"EMERGENTE, nao fechada … Melhor aproximacao MEDIDA: `floor((20D + n_dup) / (2*floor(N_efetivo/2)))`, que **acerta 103/112 celulas da s42**; as 9 restantes erram por 1-2 … A string antiga acerta 2/112 e a formula com ceil do plano F5 acerta 0/112. **O valor REAL de cada run esta em `n_geracoes`, neste mesmo manifesto — nao derive, LEIA.**"*
*(c) Re-medido.* Apliquei a fórmula, com `n_dup` = cache-hits de evolução (`fe > 11D−1`), a **todas** as células de piso:

| convenção | smsemoa (28 células `main`) | 4 pisos (112 células `main`) |
|---|---|---|
| fórmula == `n_geracoes` | **0 / 28** | **2 / 112** |
| fórmula == `n_geracoes − 1` | **28 / 28** | **106 / 112** |

O erro é **exatamente +1 em 117 das 124 células de piso** do universo (`n_ger − fórmula = +1`). Nas 25 células oficiais da s42 do smsemoa: **`ger_T11_mais1` = 25/25**. *(d) Por quê.* A fórmula conta as gerações de **EVOLUÇÃO**; `n_geracoes` conta também a **geração 1**, que é o snapshot da população semeada (`fe = 11D−1`, **0 FE gastos**, aspecto #6). Para nsga2 e smsemoa — os dois pisos cujo `n_ger = D+1` em 25/25 — o desvio é um **+1 determinístico**. O número "103/112" só é verdadeiro sob a convenção `n_geracoes − 1`, que o texto não enuncia e cuja frase final (*"o valor real está em `n_geracoes`"*) ativamente contradiz. **Este é o análogo local do padrão do c217** que a torre mandou procurar: *o campo está lá, é mais rico que antes, cita uma medição — e o número que ele afirma não sobrevive à re-medição.* A diferença benigna em relação ao c217 é que aqui **nenhuma análise quebra**: a própria string manda LER `n_geracoes`, que está presente e concorda em 4 camadas (25/25). *(e)* **(2) doc-sync com resíduo NOMEADO · direta — item para a torre (§8).** Conserto: uma linha — `1 + floor((20D + n_dup)/(2*floor(N_efetivo/2)))`, ou dizer "gerações de EVOLUÇÃO" em vez de "geracoes_derivadas".

---

**#22 🆕 — O `quinto_obrigatorio` do ⑤: `campanha_id`, `repo_hash`, `sigma_dict` (I-09/B-03).**
*(a/b)* D80 amarra o código por `repos.lock`/`anchors.json`, com o `repo_hash` do ⑤ como elo verificável; B-03 acrescentou o `campanha_id`. *(c) O antes.* Na s42 o `repo_hash` está **vazio em 25/25**, `campanha_id` e `sigma_dict` **ausentes em 25/25**; contra `contrato_61.json.quinto_obrigatorio` (`params, sigma_dict, timing, doe_hash, campanha_id, repo_hash`), faltam **3 de 6 em 25/25**. *(d) O depois.* No smoke T11: `schema_version 1→2`, `campanha_id='t11-smoke-195f64e'`, `repo_hash='195f64ed0a69dc3f6c64c66912076e243be90c49'`, `sigma_dict` presente — **6/6, faltando zero**. Verifiquei três coisas que o campo sozinho não prova: (i) `195f64e` **é um commit real** (`git cat-file -t` → commit; *"[T11-B3/T5] relatório de conformidade dos 24 configs"*); (ii) o `campanha_id` **deriva** do `repo_hash` (sufixo ≡ 7 primeiros dígitos); (iii) **a cadeia fecha**: `repo_hash → repos.lock@195f64e`, que já continha `PlatEMO.sha256_tree = fb9ed1d399d4…` — o mesmo valor que o `preflight` confirma no disco hoje. É por isso que o I-09 do `PLANO_RODADA_PERFEITA:72` cita literalmente *"(item 9 do smsemoa)"*: o achado saiu deste relatório e voltou fechado. **Resíduo honesto:** o ⑤ carrega o hash do **repo-adaptador**, não o da árvore PlatEMO — a ligação até o algoritmo passa por dois saltos (⑤ → `repos.lock` versionado → `sha256_tree`). Ambos verificáveis, mas são dois. *(e)* **(2) doc-sync · direta — CORRIGIDO.**

---

**#23 — CONTRATO §6: o header do ⑥ continua sem `run_id`, `ambiente`, `params`, `sigma_dict`.**
*(a/b)* O `CONTRATO_DE_DADOS.md` §6 promete, no `header`, *"run_id, alg+versão, problema, D, M, semente, regime, maxFE, doe_hash, **ambiente, params, sigma_dict**, ts"*. *(c)* Medido: o header do smsemoa tem **19 chaves** e **não tem** `run_id`, `ambiente`, `params` nem `sigma_dict`, em **25/25 da s42** — e o **diff de chaves header s42 × smoke T11 é ∅**: nada foi acrescentado. O mesmo vale para o footer (chaves idênticas, valores idênticos). *(d)* Não é defeito de mecanismo: o `run_id` e o `env` vivem no ⑤ (que agora está completo, #22), e o header **achata o essencial** (`N_nominal`, `N_origem`, `seeding`, `operadores`, `principio`, `casamento`, `piso`, `surrogate`) — redundância que é bônus. Mas a **promessa do CONTRATO §6 continua não cumprida e não retificada**: o gate G-7 (`contrato_61.json`) confere o **evento de geração** e o **⑤**, nunca o header, então a lacuna é estruturalmente invisível ao portão. *(e)* **(2) doc-sync sistêmico · direta — NÃO corrigido; item para a torre.**

---

**#24 — O casamento D25 com o c262: a régua faz o trabalho para o qual foi criada.**
*(b)* D25/§3.2: SMS-EMOA ↔ c262 (qNEHVI) é o espelho mecânico exato; os BO-especiais são lidos contra a **BANDA min–máx dos 4 pisos** (DEF-A13). *(c)* Re-medido do `metricas_finais_f52c.csv` (insumo pré-computado, não recomputado): head-to-head IGD+ nas 21 células em que ambos existem — **c262 vence o piso em 16/21, razão mediana `sms/c262` = 2,51×**; o piso vence em 5. Contra a banda dos 4 pisos: **c149 fica ACIMA do envelope (pior que TODOS) em 19/25**; e81 dentro em 12/25 e abaixo em 6; c154 abaixo em 6/11; c262 abaixo em 16/21. *(d)* O par HV-com-GP × HV-sem-GP isola o surrogate: em 16/21 células o GP compra ~2,5× de IGD+; nas 5 restantes — multimodais severos, α=100, WFG4 — não compra nada. É o achado que só um controle casado produz, e a banda faz o serviço previsto (expõe o c149). *(e)* **(2) D25 · indireta.**

---

**#25 🆕 — A não-perturbação da instrumentação T11, medida diretamente neste config.**
*(a/b)* A campanha T11 afirma ter acrescentado apenas instrumentação READ-ONLY, provada em 19/19 configs pelos pares `g6_com`/`g6_sem`. **O smsemoa não está nesses pares** (confirmado: `find g6_com g6_sem -path "*smsemoa*"` = vazio) — e corretamente, porque não tem sonda a desligar. Sem essa prova, o corpus s42 do config dependeria de um argumento por analogia. *(c)* Substituí o argumento por medição. A célula do smoke (`main/smsemoa/DTLZ2/42`) é **a mesma célula** que existe na s42. Comparei as 6 camadas:

| camada | s42 | smoke T11 | veredito |
|---|---|---|---|
| ① `__real` | (371, 21) | (371, 21) | `DataFrame.equals` **True** · hash `aaabd64581b0ebc5` **idêntico** · max\|ΔX\|=0,0 · max\|Δf\|=0,0 |
| ② `__pop` | (260, 5) | (260, 5) | **True**, hash `0bd3d2019b00abc6` idêntico |
| ③ `__surrogate` | (0, 33) | (0, 33) | **True** |
| ④ `__timing` | (13, 7) | (13, 7) | única coluna diferente: **`tempo_geracao_s`** (wall) |
| ⑥ `.jsonl` | 37 linhas | 37 linhas | 13 eventos de geração com **0 campos divergentes**; **21 guards idênticos** em (name, solution_id, x_key, fe); header e footer com **diff de chaves ∅ e diff de valores ∅** (exceto `ts`) |
| ⑤ `manifest` | — | — | acréscimos: `campanha_id`, `sigma_dict`, `schema_version 1→2`, `repo_hash ''→195f64ed…`, `params.geracoes_derivadas` (texto) |

*(d)* **A busca da rodada-42 é, bit a bit, a busca que o código de hoje faz.** O corpus de 25 células é válido para fidelidade de mecanismo sem ressalva, e nenhum dos acréscimos da T11 tocou o algoritmo. *(e)* **(2) verificação da campanha · direta.**

---

**#26 — [T] O `FrontNo` incremental do `UpdateFront` — o teto que resta.**
`Reduce.m:14` e `:32` **não recomputam** a estrutura de frentes: mantêm-na incrementalmente via `UpdateFront` (115 linhas de bookkeeping, com dois ramos — inserção e remoção). É esse `FrontNo` incremental que define `LastFront` e, portanto, **quem é candidato ao descarte**. O que o ⑥ grava (`piso_instrument.m:40-47`) é um **`NDSort(PopObj,1)` FRESCO**, calculado à parte para o log. Se o bookkeeping incremental divergisse do NDSort fresco — em qualquer geração, por qualquer razão — **nenhuma das 6 camadas registraria a diferença**: o log continuaria a mostrar a frente "certa" enquanto o algoritmo decidiria sobre a "sua". Também continuam não exportados os `deltaS` por indivíduo e o número de amostras efetivo do `CalHV`. Verificar exige instrumentar `Reduce` (patch invasivo em hot-loop ⇒ barrado pelo critério DI-12.1) ou re-run com dump. **Classe T** — mas um T *muito* mais estreito que o da F5 (que englobava o ramo inteiro, hoje resolvido em #8).

---

## 3. % por classe

**Total de aspectos = 26. T listado à parte = 1 (#26). DENOMINADOR = 26 − 1 = 25.**

| classe | n | % (sobre 25) | itens |
|---|---:|---:|---|
| **(1)** conforme o método canônico | **7** | **28,0%** | #6 laço (μ+1) · #7 seleção por HV · **#8 ramo do `Reduce`** 🆕 · #9 elitismo · **#10 pais `randperm`** 🆕 · #12 recomputo ideal/nadir/frentes · **#14 PlatEMO stock lacrado** 🆕 |
| **(2)** desvio sancionado | **18** | **72,0%** | #1 D21/D61 · #2 D63/D88 · #3 §3.2/D65/D20 · #4 D88 · #5 D88/§6.3 · #11 §17 · #13 D53+A37.2 · #15 §3.2/DI-13.7 · #16 D57/D89 · #17 D57/D89 · #18 D21/D61/D89 · #19 DI-13.10/§17.6 · #20 I-08 · **#21 ERRATA 5 (com resíduo)** · #22 I-09/B-03 · #23 CONTRATO §6 · #24 D25 · **#25 não-perturbação** |
| **(3)** inexplicado 🎯 | **0** | **0,0%** | — |
| **T** (fora do denominador) | 1 | — | #26 `FrontNo` incremental do `UpdateFront` + `deltaS` por indivíduo |

**Comparação com a F5:** F5 = 24 aspectos, denominador 22, **(1) 6 / (2) 16 / T 2**. Hoje = 26 aspectos, denominador 25, **(1) 7 / (2) 18 / T 1**. Os dois T da F5 (#23 ramo do `Reduce`, #24 sorteio de pais) **saíram do balde** — um por medição no dado (#8), outro por leitura de fonte lacrada (#10) — e entrou um T novo, mais estreito (#26). Dois aspectos deixaram de ser `direta-declarativa` e passaram a `direta` (#14). A marca declarativa visível (Botão 3) hoje se aplica **só ao #3** (`N=20` é declarado E medido em 376/376).

---

## 4. 🆕 AS CORREÇÕES DA T11 — implementada? funciona de fato? o que falta?

| # | correção | toca o smsemoa? | implementada? | **funciona de fato?** (evidência MEDIDA/LIDA) | o que ainda falta |
|---|---|---|---|---|---|
| C1 | **I-09 · `repo_hash` no ⑤** — *o item nasceu deste relatório* (`PLANO_RODADA_PERFEITA:72`: "item 9 do smsemoa") | **sim, diretamente** | ✅ | **MEDIDO.** s42: `repo_hash=''` em **25/25**. Smoke: `195f64ed0a69…`, que **é um commit real** (`git cat-file -t` → commit) e cujo `repos.lock` já continha o lacre do PlatEMO. Cadeia D80 fecha | o ⑤ não carrega o `sha256_tree` da árvore PlatEMO — o elo até o **algoritmo** passa por 2 saltos |
| C2 | **B-03 · `campanha_id` no ⑤** + `schema_version` 2 | sim | ✅ | **MEDIDO.** ausente em 25/25 na s42; `t11-smoke-195f64e` no smoke, derivado do `repo_hash` | — |
| C3 | **`sigma_dict` explícito `'nao_se_aplica'`** (lição "INCONCLUSIVO tem duas espécies") | sim | ✅ | **MEDIDO.** ausente em 25/25 na s42; no smoke vem com `status`+`motivo`+`terceira`. **Não é sentinela**: tem campo `status` semântico, mesma disciplina do bloco `sonda` | — |
| C4 | **I-08 · `mapa_termino.json`** (armadilha ⑧ da F5 vira artefato) | sim | ✅ | **MEDIDO.** o artefato declara `{familia:matlab, evento:smsemoa_gen, campo_termino:termino, n_footers:[1]}` e **bate em 25/25 células da s42 e no smoke**. Consumido por 3 scripts | o artefato registra `n_footers_observado {"1": 28}` — medido sobre as 28 células de `data/experiments`, não sobre as 25 oficiais. Consistente, mas os denominadores diferem |
| C5 | **G-7 · `contrato_61.json`** (DI-10 por config + `nao_se_aplica` declarado) | sim | ✅ | **MEDIDO.** `smsemoa.di10=['f_best','n_front1']`, `nao_se_aplica={tempo_fit_s, tempo_busca_s}`. Campos exigidos presentes em **376/376 eventos da s42** e **13/13 do smoke**. Gate `G-7 contrato61 OK · ⑥ 3/3 campos · ⑤ 6/6 chaves` | o gate **não confere o header do ⑥** — a lacuna do CONTRATO §6 (#23) é invisível a ele |
| C6 | **G-4 · `gabarito_camadas.json`** | sim | ✅ | **MEDIDO.** `smsemoa: 6 camadas obrigatórias (nota "piso ONLINE")`; 6/6 presentes no smoke; gate `G-4 camadas OK 6/6` | — |
| C7 | **T11-C0 · o LACRE do PlatEMO** (`53c129a`) | **sim — a mais importante para este config** | ✅ | **MEDIDO + LIDO.** Antes, o `dir_map` do `preflight` tinha 9 entradas e o `repos.lock` 11: PlatEMO caía no `continue` e **nunca era conferido** (`preflight.py:112-121`). Hoje: `PlatEMO git HEAD b686ca20cd89 (pin OK)` + `content-hash fb9ed1d399d4 **LACRE OK**`, e `git status` da árvore mostra 12 arquivos modificados, **0 em `SMS-EMOA/`** | — (mas ver §7: isto **retifica** a justificativa que a minha F5 dera para classificar #12/#13 como declarativos) |
| C8 | **A37.2 · regra 11 do CONTRATO** (dominância é LOSSY) — *nasceu do item (11) deste relatório* | sim | ✅ (como DOC) | **LIDO.** `CONTRATO §10.11` + `REGISTRO A37.2` com o schema medido por `read_schema`. A decisão de **não** mexer no D53 está registrada em `PLANO:88` | a regra descreve o efeito, mas **não nomeia o caso extremo**: em DTLZ4 a estrutura de frentes é literalmente irreconstruível da ① (13/13 gerações divergentes) — vale citar o exemplo na regra |
| C9 | **ERRATA 5 / I-13 · `params.geracoes_derivadas`** | sim | ⚠️ **implementada com resíduo** | **RE-MEDIDO — e é o achado desta rodada.** A fórmula nova acerta **0/28** células smsemoa e **2/112** células de piso contra `n_geracoes`; acerta **28/28** e **106/112** contra `n_geracoes − 1`. O erro é **+1 determinístico em 117/124** células. O texto do ⑤ afirma "acerta **103/112**" | **1 linha**: `1 + floor((20D+n_dup)/(2*floor(N_ef/2)))`, ou dizer "gerações de EVOLUÇÃO". `src/experiment.m:2516-2527` |
| C10 | **item (10) da F5** · o cache-hit de arranque N+1 | sim | ❌ **não entrou no plano** | — mas **eu fechei a causa por leitura de código**: `experiment.m:2424-2426` (o probe `Initialization(1)` do construtor pega `Xsel(1,:)`, já em cache) + `piso_init:2599`. O invariante já estava provado por dado (25/25); faltava a causa, e ela está comentada na fonte | nada a corrigir — é comportamento correto. Basta **documentar** que `cache_hits` do seeding é **N+1** (um teste `cache_hits == N` reprova 25/25 falsamente) |
| C11 | **item da F5** · CONTRATO §6 header sem `run_id`/`ambiente`/`params`/`sigma_dict` | sim | ❌ **não corrigido** | **MEDIDO.** diff de chaves do header s42 × smoke = **∅**. Nem o código nem o texto do CONTRATO §6 mudaram | doc-sync: ou o writer passa a emitir, ou o §6 passa a descrever o que existe |
| C12 | **I-02 · cronômetro `tempo_aval_real_s`** | marginalmente | n/a | **MEDIDO.** já não-nulo em **25/25 da s42** (Σ 7,37 s). O I-02 era do stack Python; o MATLAB já tinha | — |
| C13 | **A11 · sonda estratificada** e **regra 12** | **não** | n/a | vacuoso: o smsemoa não tem sonda (0 linhas no `sonda_f52e.csv`, `status='nao_se_aplica'` 25/25). Nenhuma análise deste config mistura regimes | — |

**Procura pelo padrão do c217 (campo presente, dado sentinela): ENCONTRADO UM — o C9.** Não é sentinela numérica, é **afirmação de medição que não sobrevive à re-medição**. Gravidade baixa (nenhuma análise deriva o número: a própria string manda ler `n_geracoes`, que está presente e concorda em 4 camadas em 25/25), mas é exatamente a espécie de item que a §15.7 do handoff pediu para caçar, e a taxa de erro declarada da campanha (16 erratas) previa.

---

## 5. Comparação canônica (Entrega 2) — **N/A por desenho** · o papel de RÉGUA no lugar dela

Não há paper de referência: o gabarito é a especificação canônica do método no bundle + as decisões do REGISTRO, usados aspecto a aspecto na §2. O que se pode reportar é o papel para o qual o config existe (§3.2: *"o surrogate compra alguma coisa, afinal?"*) — tudo re-medido de `metricas_finais_f52c.csv`:

| evidência | número (re-medido) | leitura |
|---|---|---|
| Células SA (main) piores que o piso smsemoa, IGD+ | **135 de 305 (44,3%)** | quase metade das células SA não bate um MOEA puro de N=20 sob 31D−1 |
| Problemas em que o piso bate **TODAS** as SA | **2/25** — DTLZ3, WFG4 | alerta de atribuição: ali o surrogate é passivo puro |
| Rank global do smsemoa entre as 17 configs do main | **9,08 / 17** | um piso mediano é um bom piso |
| Espelho casado c262 × smsemoa (D25) | **c262 vence 16/21 · razão mediana 2,51×** | o ganho do GP sob o MESMO princípio de seleção, quantificado |
| Banda dos 4 pisos vs BO-especiais (DEF-A13) | **c149 acima da banda em 19/25**; e81 dentro em 12/25 e abaixo em 6; c154 abaixo em 6/11; c262 abaixo em 16/21 | a banda discrimina |
| Posição entre os 4 pisos | IGD+: nsga2 11 · **smsemoa 8** · nsga3 6 · moead 0 · rank médio **2,28/4**; HV: nsga2 7 · **smsemoa 7** · nsga3 6 · moead 5 | melhor onde a frente premia distribuição por HV (DTLZ2, DTLZ3, MMF16_20, WFG1, WFG4, BBOB_F5/F22/F37) |
| Fidelidade ao próprio princípio | **0,85% de quedas de HV** vs 5,70% / 4,38% / 23,42% | a régua mede HV *porque é HV* |
| Custo | **0,0375 h-core / 25 células** (≈1,12 h-core em 30 sementes) | a régua é gratuita — cabe em M8/M9 sem negociação |

---

## 6. Saúde (s42 = corpus principal)

**(i) O coração — a seleção por HV é real, e agora o RAMO também.** 348/351 transições com HV populacional não-decrescente (**99,15%**) contra 94,30% / 95,62% / 76,58% dos outros três pisos, sobre o mesmo DoE, mesmo N, mesmos operadores e mesmo ponto de referência (HV **exato** em M=2 e M=3). E o teste novo do #8: `ideal` **nunca piora em M=2 (0/266)** e piora **10/85 em M=3** — o padrão troca exatamente onde `Reduce.m:21` troca de ramo, e nenhum dos outros 3 pisos exibe essa troca.

**(ii) Dinâmica populacional.** Entrantes: média **8,83/geração** (44,2% de N=20), máximo 14, **nunca > N** em 351 transições. Fração média da população na frente-1 = **0,743** (média ponderada por geração), com três regimes: **saturado** (DTLZ2, MMF16_20, WFG4 = 1,000 em todas as gerações — o `Reduce` opera sempre no ramo de HV), **misto** (WFG5 0,993, WFG1 0,965, ZDT3 0,810, DTLZ3 0,781) e **estratificado** (ZDT4 0,250, ZDT6 0,286, BBOB_F37 0,314 — domina o descarte na pior frente, não o de HV).

**(iii) Sonda.** **N/A por desenho** — 0 linhas no `sonda_f52e.csv`, `sonda.status='nao_se_aplica'` em 25/25. Não há régua Sobol nem bloco estratificado; a **regra 12 é vacuosa** aqui. A "curva de aprendizado" deste config é, por construção, a curva de HV populacional de (i).

**(iv) Contrato.** `contrato_f52b.csv`: **0 linhas smsemoa** (o ⑤ tem `params` com 12 chaves em 25/25). `integridade_f52a.csv`: **25 linhas, todas `VAZIO/__surrogate.parquet`** — por desenho (§3.2 + DI-13.7), schema íntegro e dimensionalmente correto. Gates de proveniência sobre o smoke: **G-2 OK · G-3 OK · G-4 OK · G-7 OK · B-15 OK · G-1 n/a por desenho** (③ sem linha marcada).

**(v) Máquina e tempo.** 25/25 em `vm3` (roster homogêneo). O piso de ruído entre máquinas (HV ≤1,55%; IGD+ ≤58,98%, O-18) é **irrelevante** para toda a análise intra-pisos (mesma máquina) e foi respeitado na leitura contra as configs SA da §5.

**Caveat de saúde (não de fidelidade):** em MMF1/MMF4/MMF11_L o piso roda **apenas 2 gerações completas** de evolução (D=2 ⇒ 40 FE de infill / N=20) e o resultado é essencialmente a qualidade do DoE. É a consequência aritmética prevista pela §3.2 — mas **essas 3 células têm poder discriminativo quase nulo como régua** e devem ser lidas com a ressalva.

---

## 7. SCORE, recomendação e VEREDITO

# SCORE: 10 / 10 — ACEITAR
# VEREDITO: **MANTEVE** (10 → 10), com **evidência estritamente maior**

**Por que MANTEVE e não MELHOROU no número — a causa nomeada.** O mecanismo **não mudou**, e isto não é suposição: está medido no aspecto #25 — o código de hoje reproduz a célula da s42 **bit-a-bit em 5 das 6 camadas**, com a única diferença em todo o dado sendo o wall-clock do ④. Um score que já estava no teto da régua ("tudo (1)/(2), cada (2) ancorada em decisão documentada; contrato perfeito; saúde limpa") não tem para onde subir quando o objeto avaliado é idêntico. O que mudou foi a **confiança**, e ela mudou em quatro frentes mensuráveis:

1. **O balde T encolheu de 2 aspectos para 1**, e por dois caminhos diferentes: o ramo interno do `Reduce` virou **assinatura medida no dado** (`ideal` 0/266 em M=2 × 10/85 em M=3, precisamente onde `Reduce.m:21` troca de ramo), e o sorteio de pais virou **leitura de fonte lacrada** (`SMSEMOA.m:29`) com a ausência de log reconhecida como **exclusão sancionada** do CONTRATO §6.1. O T que resta (#26, o `FrontNo` incremental) é muito mais estreito e muito mais preciso.
2. **Dois aspectos deixaram de ser declarativos.** A T11 lacrou o PlatEMO por content-hash (`fb9ed1d399d4`, `LACRE OK` conferido hoje), e `git status` da árvore mostra **12 arquivos modificados, zero em `SMS-EMOA/`**. A pureza do piso deixou de ser um eco de header.
3. **Duas lacunas de contrato que EU escalei foram fechadas no código** (`repo_hash` — o `PLANO:72` cita "item 9 do smsemoa") ou **no documento normativo** (`regra 11 do CONTRATO`, do meu item 11), e o `mapa_termino.json` transformou a minha armadilha ⑧ num artefato que 3 scripts consomem.
4. **A confirmação opcional que eu deixara em aberto foi encerrada** — a causa do cache-hit N+1 está comentada em `experiment.m:2424-2426`.

**Uma retificação contra a minha própria F5, que a honestidade exige.** A F5 classificou os aspectos de operadores e de "SMS-EMOA puro" como `direta-declarativa` justificando que *"o elo código↔log é coberto por `anchors.json`/`repos.lock`"*. **Essa justificativa era falsa à época** — o commit `53c129a` provou que o PlatEMO nunca era conferido pelo `preflight` e que o pin por commit atestava a base e não o estado, com 12 arquivos patchados vivendo como working-tree changes num repo aninhado invisível. A conclusão da F5 (o piso é stock) estava certa; o **fundamento** que ela invocou não existia. Hoje existe.

**O que impediria o 10, e por que não impede.** O único achado novo desta rodada é o **C9/#21** — a fórmula de `geracoes_derivadas` errando por +1 determinístico em 28/28 células deste config. Não é (3): a causa é conhecida e mecanicamente trivial (a geração 1 é o snapshot da semeadura, 0 FE), o campo é prosa e não schema, o config está fora das não-conformidades do `contrato_f52b`, e a própria string instrui a **ler `n_geracoes`** — que está presente e concorda entre ⑤, ⑥, ② e ④ em 25/25. Nenhuma análise da dissertação deriva esse número. Se o autor preferir penalizar afirmação-medida-que-não-se-sustenta no ⑤, o score cai para **9**; a minha leitura é que a régua pune **desvio de mecanismo**, e não há nenhum.

**Recomendação: ACEITAR** — sem caveat de fidelidade; com **1 doc-fix de uma linha** (`src/experiment.m:2516-2527`) antes do disparo das 30 sementes, **1 caveat de saúde** (as 3 células D=2 não discriminam) e **2 itens de doc-sync** para a torre (§8).

---

## 8. Aspectos classe (3) 🎯 e itens para a torre

**Classe (3): NENHUM.** A verificação adversarial não recebe itens obrigatórios do smsemoa. Os três itens abaixo são **doc-sync**, com evidência completa:

**🎯 T-1 · `params.geracoes_derivadas` erra por +1 determinístico (o análogo local do padrão do c217).**
*Onde:* `src/experiment.m:2516-2527`, gravado no ⑤ de 100% dos manifestos dos 4 pisos.
*O que a string afirma:* `floor((20D + n_dup)/(2*floor(N_efetivo/2)))` "acerta **103/112** células da s42"; "a string antiga acerta 2/112 e a fórmula com ceil do plano F5 acerta 0/112".
*O que eu medi:* contra `n_geracoes` (o campo que a própria string manda ler), a fórmula acerta **0/28** no smsemoa e **2/112** nos 4 pisos; contra `n_geracoes − 1`, acerta **28/28** e **106/112**. O erro é `n_ger − fórmula = +1` em **117 de 124** células de piso do universo (`errata5_universo_pisos.csv`).
*Causa:* a fórmula conta gerações de **evolução**; `n_geracoes` inclui a geração 1, que é o snapshot da população semeada (`fe = 11D−1`, 0 FE). Para nsga2 e smsemoa, `n_ger = D+1` em 25/25 ⇒ +1 determinístico.
*Impacto:* **nulo nas análises** (ninguém deriva; o valor real está em `n_geracoes`, concordante em 4 camadas em 25/25). *Conserto:* 1 linha.

**T-2 · CONTRATO §6 promete `run_id`/`ambiente`/`params`/`sigma_dict` no header do ⑥; o smsemoa não os tem — e nada mudou na T11.**
Header com 19 chaves em 25/25 da s42 **e no smoke**; diff de chaves s42×T11 = ∅. O gate G-7 confere o evento de geração e o ⑤, nunca o header ⇒ a divergência é estruturalmente invisível ao portão. Ou o writer emite, ou o §6 descreve o que existe.

**T-3 · `cache_hits` do seeding é N+1 = 21 — documentar antes que vire gate.**
25/25, sempre o indivíduo da posição 0 de ②(1), efeito analítico nulo. **Causa encerrada** (`experiment.m:2424-2426` + `piso_init:2599`). Qualquer gate futuro que teste `cache_hits == N` reprova os 4 pisos falsamente em 100% das células.

---

## 9. Teto de verificabilidade (T) + armadilhas + o que este corpus NÃO permite verificar

**T — exige patch invasivo ou re-run** (o balde encolheu de 6 itens da F5 para 3):
· o **`FrontNo` incremental** do `UpdateFront` que o algoritmo de fato usa para escolher `LastFront` (o log grava um NDSort **fresco e independente**, `piso_instrument.m:43`) — uma deriva entre os dois seria invisível nas 6 camadas · os **`deltaS` por indivíduo** e o número de amostras efetivo do `CalHV` (o ramo e a referência móvel já não são T — `Reduce.m:20-28`, árvore lacrada) · a **ordem interna dos N passos steady-state** dentro de uma geração (② e ⑥ só expõem o estado no fim do laço externo).
*Saíram do balde nesta rodada:* ramo do `Reduce` (#8) · sorteio de pais (#10) · elo run↔código (`repo_hash` preenchido + PlatEMO lacrado, #14/#22) · quais variáveis o SBX/PM cruzou (continua não exportado, mas a rejeição é **sancionada** pelo CONTRATO §6.1 e o operador é verificável na fonte lacrada).

**Armadilhas confirmadas na escala** (25/25 salvo indicação):
① **`cache_hits` do seeding é N+1 = 21, não N=20** — o probe do construtor do `UserProblem` pega `Xsel(1,:)` duas vezes; testar `cache_hits == N` reprova 25/25 falsamente.
② **`n_geracoes` conta só as gerações COMPLETAS** — ⑤, ⑥, ②, ④ dizem todos o mesmo número (25/25); as 16 linhas fantasma da ① (3 células D=2) **não têm geração associada em nenhuma camada**.
③ **`f_best` ≡ `ideal`** em 376/376 — é o vetor de mínimos componente a componente, emitido sob os dois nomes por construção (`piso_instrument.m:57-58`); usá-lo como "a melhor solução" é erro de leitura.
④ **Δfe entre gerações NÃO é sempre N** — é N menos as duplicatas daquela geração; testar `Δfe == 20` reprova 3/25 células falsamente.
⑤ **Guards de cache-hit devem ser atribuídos à geração por ORDEM no fluxo do ⑥, não por fronteira de `fe`** — pela ordem o fechamento é 25/25; pelo `fe`, o MMF4 quebra.
⑥ **A frente-1 recomputada da ① diverge do log em 11,7% das gerações** — e em DTLZ4 em 13/13. Causa: underflow subnormal float32 (D53), hoje **regra 11 do CONTRATO**. **O log é a fonte, não o recomputo.**
⑦ **`ideal`/`nadir_pop` recomputados exigem tolerância de float32** (desvio relativo máximo medido 5,9e-08 ≈ 1 ULP); com `atol=1e-12` o teste reprova 332/376 por artefato de precisão, não por infidelidade.
⑧ **`N_efetivo = 20` no smsemoa mesmo em M=3** — comparar populações com nsga3/moead nas 6 células M=3 (que rodam com 15) sem normalizar é comparar coisas diferentes.
⑨ **`motivo_parada` NÃO existe no ⑤** — o campo é `footer.termino` (`'normal'` em 25/25, inclusive nas 3 que sofreram hard-stop D21 no meio de uma geração). Hoje normativo em `mapa_termino.json`.
⑩ **③ vazia + `sonda='nao_se_aplica'` ⇒ U3, U4, U5, U6, U8, U11 e U12 são N/A por desenho** — `sonda_f52e.csv` e `contrato_f52b.csv` com 0 linhas smsemoa estão **corretos**; ausência de linha não é ausência de verificação.
⑪ 🆕 **`params.geracoes_derivadas` erra por +1** — ver T-1. Não derive: **leia `n_geracoes`**.

**O que este corpus NÃO permite verificar:**
· nada sobre **fidelidade de MODELO** — o config não tem surrogate; não há μ, σ, WAPE, cobertura, calibração nem régua Sobol a medir (é o piso, e essa ausência **é** o mecanismo);
· a **contribuição de HV de cada indivíduo** e o `FrontNo` que o algoritmo de fato usou (T, §9);
· **estabilidade em múltiplas sementes** — 1 semente por célula; nota baixa de comportamento numa semente ≠ infidelidade (caveat 8 do F5). Os 3 problemas D=2 são, além disso, quase cegos como régua;
· o comportamento em **regime de campanha** (695 células × 30 sementes: concorrência, disco, memória, teto) — o smoke valida 1 célula, e o handoff §8.4 declara isso;
· a **instrumentação NOVA da T11 em escala** — para o smsemoa ela é inteiramente metadado do ⑤ (`campanha_id`/`repo_hash`/`sigma_dict`), medida em **1 célula**; as outras 24 células que ela produzirá ainda não existem.

---

*Insumos pré-computados usados sem recomputo (protocolo): `f5/metricas_finais_f52c.csv` (25 linhas smsemoa) · `f5/contrato_f52b.csv` (0 linhas) · `f5/integridade_f52a.csv` (25 linhas, ③ vazia por desenho) · `f5/tempo_f52d.csv` (25 linhas, vm3) · `f5/sonda_f52e.csv` (0 linhas). Tudo o mais foi RE-MEDIDO. Artefatos normativos lidos: `claude_code_context/artifacts/{contrato_61,mapa_termino,gabarito_camadas,motivos_parada,anchors,repos.lock}.json`. Fontes lidas (árvore lacrada `fb9ed1d399d4`, `LACRE OK`): `algorithms/_PlatEMO/PlatEMO/Algorithms/Multi-objective optimization/SMS-EMOA/{SMSEMOA,Reduce,CalHV,UpdateFront}.m` e `Utility functions/NDSort.m`; `src/piso_instrument.m`; `src/experiment.m:2329-2611`; `scripts/preflight.py:100-175`.*

***Evidência produzida (diretiva de preservação) — toda em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/smsemoa/`:***
`t11_01_smoke_vs_s42.py` (não-perturbação bit-a-bit smoke×s42, 6 camadas) · `t11_02_bateria_s42.py` → **`aspectos_t11_smsemoa.csv`** (86 colunas × 25 células: U1/U2, N, Δfe, guards, fechamento, ③, ⑤, término, DI-10, timing, elitismo, recomputo, float32, seeding, declarativos) · `t11_03_correcoes.py` → **`errata5_geracoes_4pisos.csv`**, **`hv_monotonicidade_4pisos.csv`** · `t11_04_hv_exato_e_errata5.py` → **`hv_exato_4pisos.csv`** (HV EXATO, fatiamento em M=3), **`errata5_universo_pisos.csv`** (124 células de piso) · `t11_05_fechamento.py` (quedas exatas de MMF16_20, insumos F5, papel de régua, smoke × artefatos normativos) · `t11_06_ramo_reduce.py` → **`ramo_reduce_ideal.csv`** (a assinatura M=2 × M≥3 do `Reduce`, nos 4 pisos).
Interpretador: `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`. **Nenhuma célula foi rodada; `data/experiments` não foi tocada; `experiments.py` não foi invocado; `repos.lock` conferido intacto após o `preflight` read-only.**
*(Nota: a pasta continha, antes desta sessão, `t11_smsemoa_b{1,2,3}_*.py|csv` de 11:36–11:40, que não são meus — não os cito como evidência; a leitura que fiz deles não conflita com nada acima.)*