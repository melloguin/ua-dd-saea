

==========================================================================================
### CONFIG: b1

## 7. SCORE, recomendação e VEREDITO

### **SCORE: 9,6/10 · ACEITAR + caveat**  ·  **VEREDITO: MELHOROU (9,4 → 9,6)**

**As quatro causas, nomeadas:**

1. **INSTRUMENTAÇÃO NOVA fechou um teto — a causa principal.** O par `g6_com`/`g6_sem` não existia na F5; agora existe e eu o medi: **① bit-idêntica, ③-online bit-idêntica, 54 eventos do ⑥ idênticos em 16 campos**, com a sonda comprovadamente ligada de um lado. O **U5** era um dos 3 itens do teto e um dos "o que impede o 10" da F5. Está fechado, com evidência de classe `direta`.
2. **MAIS EVIDÊNCIA — a WFG1 voltou.** 23 → **24 células**; +443 iterações, +681 linhas de ①, +205.350 de ②, +854.888 de ③, +223 blocos de sonda. E não voltou de graça: **todas as identidades fecham nos 374 eventos sobreviventes**, o ledger fecha exato, a cadência fecha exata, e ela reproduz a assinatura do finalProbe numa 6ª célula. Além disso **eu preenchi a métrica que faltava** (IGD+ 0,5189), que era o único buraco do b1 na matriz de 15 algoritmos × WFG1.
3. **CORREÇÃO REAL, verificada — e ela é do meu config.** O `jsonl_open` em append (T11-G1) ataca nominalmente a família `main/b1/WFG1`. Verifiquei nos dois escritores (`experiment.m:3347`, `audit_log.py:130`) e no gêmeo em tempdir: **`a+a` perde 0 de 10.000 em 2/2; `w+w` perde exatamente 5.000**. O modo de perda que destruiu 15,6% do filme da WFG1 está eliminado.
4. **MÉTODO — o torneio K.3 saiu da sombra.** Era T ("invisível nos dados") e vira **(2) com efeito quantificado**: ativo em 91,5% das iterações, `P(pai=DoE)` mediana **0,9912**, peso **3,78%** dos 73,47 M candidatos, com a derivação exata (o vetor de aptidão está **ordenado** pós-cap ⇒ o torneio degenera em `min(U1,U2)` ⇒ seleção por **idade**, não por aptidão). E isso **REFUTA uma recomendação minha da F5**: eu havia nomeado o t


==========================================================================================
### CONFIG: b3

## 7. Score, recomendação e **VEREDITO**

### **SCORE: 9,8/10 · ACEITAR** · **VEREDITO: MELHOROU** (F5 9,6 → T11 9,8)

**A causa nomeada é EVIDÊNCIA NOVA, não mecanismo novo — e não é "amostra diferente":** o corpus da s42 é o mesmo, e **todas as 27 checagens verificáveis da F5 reproduziram com o mesmo número na re-medição** (1.443 ciclos, 7.215 seleções, 3.776.308 linhas, joia 7.215/7.215 a 5,92e-8, critério a 4,31e-16, ΔWAPE +4,40%, 18/25 vs pisos, rank 6,36, 9.220,2 s em vm3). O que subiu o score foram três coisas medidas nesta rodada:

1. **Dois T fechados com dado (4 → 2).** O **U5** (não-perturbação da sonda) deixou de ser "exige run pareado" e virou prova: ①②③-online bit-idênticas e **Δapd_sel = 0** nos 8 ciclos do par g6. O **B13** (ramo (a) do `UpdataArchive`) deixou de ser "sem rastro, alcance 4/25" e virou **discriminação célula a célula**: impossível em 21/25 por aritmética, **rodou** em MMF1/MMF4/MMF11_L, **não rodou** em DTLZ1, com robustez testada a 10⁵× o ruído do float32.
2. **A decisão em aberto da T11 sobre o b3 (D-D) ficou respondida sem tocar em código.** O handoff diz que "medir isso exigiria 2 linhas read-only"; a reconstrução determinística de `UniformPoint`+`NoActive`+`V=V0·faixa` mostrou que o dado já bastava para o ciclo 1, e o Monte Carlo dá a exposição dos demais (63%/97%/92%/0%). E ficou provado que o defeito é **index-safe por construção** (`size(Via,1) ≤ |Total|`) — não derruba run, não muda |A1|, não aparece em `nzero`.
3. **A instrumentação nova foi auditada e passou** — `adapt_delta_V` não é sentinela e bate um recomputo independente a 6,3e-6; e a reprodutibilidade cross-máquina do b3 é **exata ao float32 em todo o run**.

**O que impede o 10** (e é o mesmo de antes, menos dois itens): (i) **θ nunca é logado** (F6) — bounds, θ0 e a tr


==========================================================================================
### CONFIG: b4

## 7. Score, recomendação e VEREDITO

### **SCORE: 9,5 / 10 — ACEITAR** (caveat de LEITURA, não de aceitação)

### **VEREDITO: MELHOROU — de 9,0 para 9,5.** Causa, nomeada e decomposta:

1. **CORREÇÃO REAL (o fator dominante): o único item (3) do config caiu, e caiu com a ação certa.** A F5 classificou a semântica de `p0`/`p1` como (3) 🎯; a F5.4 refutou; a T11 implementou exatamente a ação doc que a verificação adversarial recomendou (glosa no `sigma_dict`, `src/experiment.m`), **e eu confirmei os dois lados de forma independente** — pelo fonte (`CSEA.m:77-79`) e pelo dado (6.268/6.268 na predição de NaN). O config passa a **(3) = 0,0%**. Isso, sozinho, é o degrau 9→9,5 da régua ("9 = com (3) menores já investigados e provados benignos" → agora sem nenhum).
2. **EVIDÊNCIA NOVA, não amostra nova: um teto T virou (1).** A não-perturbação da sonda era o teto T⑧ da F5 ("exige código/re-run"). Agora está **medida**, em 3 pares independentes, com a ① bit-idêntica e `Δp0 = 0,0` no par com/sem. Nenhum outro aspecto mudou de classe por mais dados.
3. **NÃO é "amostra diferente".** O mecanismo é literalmente o mesmo: provei que a célula do smoke reproduz a da s42 **bit a bit**. Todas as identidades centrais re-mediram idênticas (gate 6.268/6.268 · partição 6.268/6.268 · rótulo 3.589/3.589 · `rr`/`tr` 6.268/6.268 · L>0,9 1.811/1.811). **O mecanismo não mudou — e essa é a razão pela qual o salto é de meio ponto e não maior.**
4. **INSTRUMENTAÇÃO NOVA validada, com uma ressalva.** `ref_ids` real (0 sentinelas — o contraste exato com o `pmid_ids = [-1×5]` do c217), `REGRA_DO_ROTULO` fiel ao `GetOutput.m`, bloco estratificado funcional e recomposta a métrica que ele deixa NaN por desenho.

**O que impede 10** (e é tudo instrumentação, nada de mecanismo): (i) **⚠E1** — os 3 números de


==========================================================================================
### CONFIG: b5m

## 7. SCORE e VEREDITO

### **SCORE: 8,5/10** (F5: 8,0) · **RECOMENDAÇÃO: ACEITAR + CAVEAT** · **VEREDITO: MELHOROU**

**A causa nomeada do movimento, item a item — e o que NÃO o causou:**

| fator | move o score? | por quê |
|---|---|---|
| **CORREÇÃO REAL, verificada em dado** | **+** | o único (3) da F5 (A25/DI-10) foi implementado e **funciona**: `p_wrong_stats` 800/801 e `n_substituicoes` 800/801, reconciliados contra a ③ em 800/800 gerações. Era literalmente "o item que segura o score abaixo de 8,5" (F5 §7.3). A **quantidade central do artigo deixou de ser inauditável ex-post** |
| **A8 CONFIRMADA em bancada** | **+** | a cadeia que a F5 inferiu e mandou à F5.4 está provada elo a elo (`adapt`→norma 0 em 50/50 → PBI NaN 1000/1000 → `P_wrong = 0.0` exato → 0 substituições), com contrafactual (vetor sadio, mesmo μ/σ → **0,4995**). O caveat científico central do config passou de suspeita a fato |
| **verificabilidade elevada** | **+** | A15 (rampa θ) migrou de **indireta → direta** (Spearman −0,8688 sobre o próprio P_wrong); A19 (40.000 FE) ganhou **contagem exata** (Σ n_chamadas = 40.000); o balde T caiu de 4 para 3 |
| **achado de contrato da F5 fechado** | **+** | `params` no ⑤ (era 0/45) + `campanha_id`/`repo_hash`/schema v2 + `granularidade_③` no `sigma_dict` (fecha a armadilha nº 1 da F5) |
| **3 novos (3) — todos de instrumentação** | **−** | `flag_vetores_degenerados` morto (**e é justamente o que fecharia o laço da A8**), pesos no header ausentes + requisito retirado do contrato executável sem errata, e o I-02 quebrando a semântica offline de `tempo_aval_real_s` |
| **MECANISMO** | **0** | **não mudou nada, e é isso que se esperava.** As 45 células da s42 seguem válidas: re-medi 20 invariantes estruturais e **todos reproduzem exatamente** os números da F5 (n


==========================================================================================
### CONFIG: b5r

## 7. SCORE, recomendação e VEREDITO vs F5

### **SCORE: 9,0/10** · **RECOMENDAÇÃO: ACEITAR + CAVEAT** (caveats **científicos**, não de fidelidade) · **VEREDITO: MANTEVE**

**Por que MANTEVE, com a causa nomeada — e por que isso é o resultado certo.**

1. **O mecanismo não mudou — e isso não é inferência, é bit-identidade.** ①, ③ (59.436 linhas × 29 colunas) e ⑦ da célula `BBOB_F22/42` são idênticas entre a s42 (pré-T11) e o smoke T11. A campanha acrescentou **só instrumentação read-only** no b5r. Toda a fidelidade de mecanismo é a mesma, re-medida com os mesmos números: 63,56% de rejeição-por-σ em 56.081 transições (z≈64), 727/727 dimensões LHS, 45/45 no invariante de 40k, ⑦≡③ bit-a-bit 45/45, ND recomputado 45/45.
2. **O que PUXOU PARA CIMA (+):** o único (3) da F5 (**A30**) foi **corrigido exatamente como recomendei** e a correção **funciona** — `granularidade_③` no `sigma_dict`, texto correto, controle negativo declarado; ganhei ainda uma **prova executável** que a F5 não tinha. O contrato fechou (**A27**, `params`). **A31 saiu do teto T** (determinismo agora é dado). Proveniência ficou auditável dentro do manifesto (**A34**). Sozinhos, esses quatro itens justificariam **9,5**.
3. **O que PUXOU PARA BAIXO (−):** dois (3) NOVOS, ambos achados por medição e ambos do tipo que o prompt mandou caçar. **A32** é o padrão do c217 na forma pura — `flag_vetores_degenerados` presente em 1144/1144 eventos e **sentinela em 1144/1144**, por caminho de atributo errado, com o `except Exception` mudo; e a ERRATA 13 "consertou" a `amplitude` **dentro do ramo morto**. **A33** é uma regressão semântica silenciosa: `tempo_aval_real_s` deixou de ser 0/None no offline e passou a medir a ingestão do dataset, contradizendo a docstring que justifica o próprio campo — e custando uma das cinc


==========================================================================================
### CONFIG: c122

## 7. SCORE e VEREDITO

### **SCORE: 9,5 / 10 — ACEITAR + CAVEAT** · **VEREDITO: MANTEVE**

**A causa nomeada do "manteve" é uma soma de duas parcelas que se cancelam:**

- **+ (correção REAL, não cosmética):** o **único (3) da F5** — a referência do bloco-1 contradizendo o `n_ref` declarado em 3.537/3.537 recs — está **fechado no nível do rec** (N1), com `ref_ids` de **dado real** (o teste que o c217 reprovou), e a instrumentação nova **habilita uma medição que a F5 não podia fazer**: eu executei a `REGRA_DO_ROTULO` e produzi AUC/ρ do classificador contra a verdade, bloco a bloco. Isso vale, sozinho, +0,3.
- **− (defeito NOVO de contrato):** o **N3** tira do c122 exatamente o pilar que sustentava a nota alta na F5 — "contrato 100% conforme, zero defeitos". A ③ de hoje grava, num regime inteiro, `e(z)` em `mu_0` e `pred_score` NULL, contra o `sigma_dict` do próprio run e contra o CONTRATO §3. Vale −0,3.
- **= mecanismo INALTERADO e re-medido em escala maior que a F5:** 8 aspectos **(1)** incluindo a query-joia; identidades fechando **7.022/7.022** (TOP-100, Q_max), **6.440/6.440** (argmax), **5.047/5.047** (prioridade), **13.843/13.843** (gate), **8.538/8.538** (E_upd), **668/668** (rodadas). **Nada no laço de busca mudou entre a F5 e hoje** — e nada nas correções da T11 podia mudar (são read-only, sob `preserve_all_rng`, com a não-perturbação registrada em 19/19 configs).

**A recomendação vem com uma condição barata e com prazo:** *aplicar, ANTES do disparo do M8, a ramificação de 4 linhas em `emit_sonda_estratificada` (`standalone_harness.py:950`) que já existe na função irmã*. Sem ela, a campanha grava ~**53 M linhas em 30 sementes** na coluna errada — recuperáveis por regra de leitura, mas por que pagar isso quando o conserto é gratuito hoje? **Com esse conserto +


==========================================================================================
### CONFIG: c141

## 7. SCORE, recomendação e VEREDITO vs F5

## **SCORE: 9,5/10 · ACEITAR** · **VEREDITO: MANTEVE**

**Por que MANTEVE, com a causa nomeada.** O mecanismo **não mudou** — e isso é medido, não suposto: os arquivos do c141 (`c141_instrument.m`, `c141_sonda.m`, `algorithms/c141_MMRAEA`) não têm commit desde **2026-07-19**, sete dias antes da célula da s42, e nenhum dos arquivos compartilhados alterados pela T11 toca um caminho que o c141 execute. Nenhuma das 16 erratas da T11, nenhum dos 4 CRÍTICOS, nenhum dos 18 ALTOS e nenhum dos 11 itens da FASE A endereça este config. **"Manteve" é o veredito esperado e é o correto.**

O que **melhorou de fato**, e é pouco mas é real:
1. **U11 saiu do balde T.** O par G-6 (`d7f20cd0c4648c3f`, medido por mim nas duas pastas) provou por DADO o invariante 🔴 do CONTRATO §3.1 que a F5 só podia declarar por CÓDIGO. **A verificabilidade do config foi de 24/26 (92,3%) para 24/25 (96,0%)**, e o T restante é o único inalcançável por artefato.
2. **A cascata foi re-provada no código de HOJE.** No smoke pós-T11 reconstruí do zero: kernel MQ c=1/poly=0/sem-scaling (erro rel. mediano 5,9e-05), nível 1 em **10/10**, Fit1/SDE em **10/10** a rel<1e-5, teto de σ_0 = 82 EXATO com `U_pool_max`≡max(σ_0) em **10/10**, ledger 21+37−1+4=61, finalProbe exercitado numa geração ímpar. **A fidelidade não é uma afirmação sobre um dado velho — ela vale para o binário que vai rodar a campanha.**
3. **O elo D80 finalmente existe** (`repo_hash` de `''` em 25/25 para um SHA-1 real), o que dá base ao aspecto declarativo do C5 sem tirá-lo do balde T.

O que **piorou / o que eu corrijo**:
4. **Apareceu um (3) que a F5 não tinha** — mas ele é **transversal do harness, não do c141**, e seu impacto sobre a fidelidade do c141 é **medido como nulo** (a cascata reconstrói igual


==========================================================================================
### CONFIG: c149

## 7. SCORE, recomendação e VEREDITO

# SCORE: 9,5 / 10 — recomendação: **ACEITAR + CAVEAT** (caveat reduzido)

### VEREDITO: **MELHOROU** (9,0 → 9,5)

**A causa, nomeada — e é CORREÇÃO REAL, não amostra nova:**

1. **O único aspecto classe (3) da F5 deixou de existir (−1,0 → 0 de desconto por (3)).** A verificação adversarial provou a causa-raiz byte-a-byte (colisão de blob, `md5 1269b87f…` idêntico ao gêmeo do Mac de 2026-07-24), **refutou** as minhas H2 e H3, e estabeleceu que **D29 não dispara**: o defeito não toca o artigo, nem o código do autor, nem o surrogate. É persistência, não fidelidade.
2. **A minha recomendação da F5 §8 virou código, com controle positivo E negativo, e eu a re-executei**: `gate_3x1` em `scripts/gates_proveniencia.py:89` reproduz **29 OK / 1 RUIM** com `max|ΔX| = 9,99983` ao dígito.
3. **A causa-raiz recebeu trava estrutural mais forte que a recomendada**: `if_generation_match=0` → `ColisaoDeBlob` → sem sobrescrita e **sem poda da cópia local**, + md5 como pré-condição da poda, + `campanha_id` obrigatório no `is_run_done`. Os 3 sítios isolados pelo adversarial estão cobertos.
4. **Um número do mecanismo MELHOROU**: A22 sobe de **622/624 (99,7%) para 424/424 (100,0%)** — as 2 únicas falhas eram da célula contaminada. A reconstrução da regra D42 é perfeita no dado limpo.
5. **Um teto foi descarregado**: T2 (não-perturbação da sonda) virou o aspecto A29, com a flag `sonda_on` gateando **os dois** sítios de emissão e 2 testes de plumbing (AST + wrapper→inner) que **executei e passam**.
6. **Instrumentação nova, medida e barata**: checkpoint DI-43 disparou no smoke (0,069% do wall) e projeta 0,109% na escala real — relevante porque o c149 é o config mais caro (2.811 h-core em 30 sementes).
7. **A premissa do corpus foi PROVADA, não assumida**: 


==========================================================================================
### CONFIG: c154

## 7. Score, recomendação e VEREDITO

### **SCORE: 9,0/10** (F5: 8,5) · **Recomendação: ACEITAR + CAVEAT** · **VEREDITO: MELHOROU**

**A causa, nomeada.** A melhora **não vem de mais evidência nem de amostra diferente** — o corpus de mecanismo é o mesmo (11 células, 1.673 decisões) e **todos** os números centrais da F5 reproduziram (query-joia `acqf_escolhido == max` dos finitos em **1.824/1.824**; identidade do ponto com **max\|ΔX\| = 0,0** em 1.813 links; escada 1.364/19/0; platô 503/1.673; `hs_paths` 18.240 distintos; cadeia do ruído 11/11 no `outputscale`). Vem de **três correções reais, verificadas**:

1. **A única classe (3) da F5 foi REFUTADA — e por dado, não por decreto.** A T11 não "declarou" o J27 resolvido: publicou uma regra executável (`restart_de_linha`), e eu a testei contra o dado com um discriminador independente (α é determinística em x ⇒ X idêntico ⟹ α idêntica). Nos 170 pares discriminantes, a regra dá \|Δα\|/α ≤ **1,74e-09** e o índice ingênuo dá mediana **0,132** — **sete ordens de grandeza**, com o controle de 111 pares fixando o piso do ruído float32 em 1,46e-10. O que era "teto da auditabilidade da família GP-BO" virou **regra de leitura provada**. Isto sozinho move o score pela régua (de "(3) periférico não provado" para "(3) menores investigados e provados benignos").
2. **A não-conformidade de contrato fechou.** As 11 linhas de `contrato_f52b.csv` (`camada 5 · faltam ['params']`) e a armadilha nº 1 do meu relatório (`motivo_parada` ausente) foram ambas corrigidas, com dado **não-sentinela** — verifiquei a coerência cruzada de `params` (5D/1000D com D=12) contra o bloco `jes` e contra as 60 linhas/geração da ③.
3. **O rito de teto converte perda total em dado utilizável.** As 12 células D≥12 do `main/c154` entregavam **zero parquet**; a célu


==========================================================================================
### CONFIG: c217

## 7. SCORE, recomendação e VEREDITO

### **SCORE: 9,0 / 10 — ACEITAR + CAVEAT**
### **VEREDITO: PIOROU 0,5 vs a F5 (9,5 → 9,0). O MECANISMO MANTEVE‑SE INTEGRALMENTE; a queda é inteiramente da camada de instrumentação declarativa introduzida pela própria T11.**

**A causa, nomeada.** Não é amostra diferente (re‑medi as MESMAS 25 células e as MESMAS 6.762 gerações, e **todos** os números da F5 reproduziram ao dígito: 6.762/6.762 nas cinco identidades fechadas, 87,7% no contrafactual D17, 179,9× na assinatura de tempo, 1.076 quedas de `fe_treino_max`, 3.410/3.410 blocos bit‑a‑bit, 0,5485 de acurácia, 475/475 monotônicas, 7/25 vs pisos, 0,5473 h‑core). Não é correção real revertida. **É a entrada de três aspectos classe (3), onde a F5 tinha zero:**

1. **`pmid_ids` = −1 em 426/426.** A T11 foi criada, entre outras coisas, para fechar exatamente a lacuna que a F5 nomeou — *"a AUC é impossível, só há `n_Pmid`"*. O campo entrou, o comentário do commit descreve a aposta com precisão, e **o dado não veio**, por uma fatia `1:D` esquecida (`c217_instrument.m:201` × `CalFitnessPC.m:67‑68,73` × `FEBudget.m:171`). O comentário que acompanha o campo oferece uma explicação **falsa** do sentinela. **A lacuna da F5 continua aberta e agora está camuflada por um campo verde.**
2. **`y_treino_dist` degenerado em 42/42**, por uma codificação `{−1,0,+1}` que o `Output` nunca teve — contradita 106 linhas acima no mesmo arquivo.
3. **`params.operadores` factualmente falso**, declarando o Balde C 20/20 num config em que a SPEC §567 escreve, com todas as letras, *"Balde C não se aplica"*, e em que o código roda `{1,15,1,5}` em três chamadas. **É a única regressão de auditabilidade da T11 neste config:** transformou uma divergência sancionada e explícita (T1) numa falsa conformidade com o paper.


==========================================================================================
### CONFIG: c238

## 7. Score, recomendação e VEREDITO

### **SCORE: 9,5/10 · ACEITAR** (mesma nota, com 3 caveats de LEITURA nomeados)

### **VEREDITO: MANTEVE**

**A causa, nomeada:** **o mecanismo não mudou, e isso é PROVADO por duas vias independentes.** (i) **Git**: `src/c238_instrument.m`, `src/c238_sonda.m` e `algorithms/c238_EIM/` estão congelados em `941901f` (21/07) e `b3675ef` (24/07) — anteriores à s42 e à T11; os únicos `.m` compartilhados tocados na campanha são cabeçalho do ⑤, um acessor read-only de 20 linhas para uma sonda que o c238 não tem, e um kill-switch de sonda desligado por padrão. (ii) **Dado**: a re-medição integral das 25 células com scripts escritos hoje do zero reproduz **todos** os números da F5 — 7.020/7.020 na identidade EIMe com mediana 2,17e-09, 4.783/7.020 no argmax, 5.316/7.020 no contrafactual, 6.557/7.020 na frente exata, 189 saturações todas em BBOB_F1, 259.880.000 avaliações da aquisição, c0=1, 6.995/6.995 no ledger, ΣFE=10.856.

**O que puxou para cima:** **T1 saiu do balde T** — a invariante 🔴 do CONTRATO §3.1 deixou de ser não-verificável e passou a estar provada com uma força maior do que o handoff reivindica: não só ① e ② com sha256 idêntico, mas **os 27 campos do evento de geração do ⑥ com Δ = 0,0 exato** — θ, lnL, `eim_best`, `u_best`, `s_best`, `norm_min/max`, `n_front` — isto é, **a trajetória interna inteira**, não apenas o resultado. Some-se a proveniência de campanha (N2) e 6/6 gates verdes.

**O que puxou para baixo:** **N1** — a degeneração numérica do kriging em 3 de 25 células (12% do corpus, **incluindo MMF11_L, que é um dos 3 primeiros lugares absolutos do config**), com cota rigorosa σ̂² ≥ 1 em 118/15.740 componentes-geração e até ≥ 9,0e+04. **Não é infidelidade** (cada elo é código do próprio autor do paper, citado por arquivo


==========================================================================================
### CONFIG: c262

## 7. SCORE e VEREDITO

## **SCORE: 9,7 / 10** — recomendação: **ACEITAR** · **VEREDITO: MELHOROU** (9,5 → 9,7)

### A causa NOMEADA da melhora

**Não é mais evidência de mecanismo, não é amostra diferente, não é sorte de semente.** O mecanismo é **exatamente o mesmo** — provei-o re-executando as quatro query-joias sobre as mesmas 21 células e obtendo **os mesmos números até o último dígito** (argmax 5.201/5.201 Δ=0,0 · elo ③→① 5.180/5.180 Δ=0,0 · ruído 11.220/11.220 err 1,429e-7 · I-12 277/7.111 = 3,90%), e reproduzindo-as **também no artefato do HEAD** (41/41, 40/41 + G-1 40/40, 80/80). A melhora é de **duas correções reais** e de **verificabilidade**:

1. **Fechou 2 dos 3 itens que compunham o desconto de 0,5 da F5.** A F5 disse, literalmente, que o desconto era "exclusivamente de verificabilidade e contrato: (i) T2 batch; (ii) T1 — 8 hiperparâmetros internos não estão no `params`; (iii) a não-conformidade de contrato do ⑤". **(ii) e (iii) estão fechados e medidos em artefato**, não prometidos: `acqf_hp` com 10 campos de fonte única (7/10 confirmados contra o objeto BoTorch + controle negativo) e `params` no ⑤ com `header == manifest` byte a byte.
2. **A armadilha nº 1 do config virou regra de dado.** O `ordem_terceira_online` (I-12) + `restart_de_linha` transformam o achado mais frágil da F5 — que vivia só no meu relatório e que faria um agente fresco reprovar um run perfeito — em contrato machine-readable, e eu **verifiquei** que a regra declarada é a mesma que provei de forma independente.
3. **Verificabilidade que eu mesmo levantei nesta rodada**: S1 sai de direta-declarativa para **direta** (kernel `MaternKernel nu=2.5`, `ard_num_dims=D`, `GammaPrior(3,6)/(2,0.15)` lidos do objeto instanciado); `Standardize` sai de indireta para direta; o risco do DEF-L2 deixou


==========================================================================================
### CONFIG: c311

## 7. SCORE, RECOMENDAÇÃO E VEREDITO

### **SCORE: 9,5/10 · RECOMENDAÇÃO: ACEITAR** (caveats **científicos**, não de fidelidade)
### **VEREDITO: MANTEVE vs a F5 — mas com a composição TROCADA**

*Prior F5.3a-v1.1: 9,5 · piloto v1.0: 8,5 · prior v2: 7,5.*

**A causa, nomeada, é dupla e ela se cancela:**

**(+0,5) EVIDÊNCIA NOVA, não mecanismo novo — dois itens do teto T caíram, e eram exatamente os que a F5 §7.5 nomeou como o que impedia o 10.**
1. **A fórmula do early-stop.** A F5 escreveu, textualmente, *"o que NÃO ficou provado: a fórmula interna de `delta`… a melhor taxa de acerto foi 20 de 369 = 5,4%… ela vai para o teto T"*, e sugeriu à F5.4 a leitura de "uma linha de código". A leitura foi feita: `total_point_gps` conta **FOLHAS**, não pontos (`surrogate_treedGP.py:49`) — a razão pela qual as 9 famílias falharam. Com a grandeza certa, `delta(k) = c(k)+c(k−1)` reconstrói **338/369 iterações elegíveis (91,6%)**, 235/235 sentinelas, **573/604 = 94,9%**, **52/54 células a 100%**, com os 31 desencontros concentrados nas mesmas 2 células de sempre e pela mesma causa declarada. E a divergência 🟠 B15.8 fica **inteiramente caracterizada**: é o critério do paper com persistência de 2 e piso de 6, custa **3.162 de 30.804 gerações (10,3%)**, e a janela de 2 **guarda contra uma não-monotonicidade real** (5/54 células em que `c(k)` volta a >0 após zerar).
2. **O determinismo bit-a-bit.** A F5 escreveu *"só re-execução bit-idêntica de ① e ③ prova"*. O smoke T11 preservado É essa re-execução: **①②③⑦ byte-idênticas** (sha256) entre 26/07 e 31/07, tempdir diferente, HEAD com 3 alterações no runner. A disciplina D62/DI-28.3 está provada, e de quebra a não-perturbação da T11 está provada **para este config, na ③ inteira**, não só na ①.
3. Somam-se, sem mover o score sozinhas: a ânco


==========================================================================================
### CONFIG: e103

## 7. SCORE, RECOMENDAÇÃO e VEREDITO

**SCORE: 9,5/10** (F5: 9,3) · **RECOMENDAÇÃO: ACEITAR + CAVEAT** (o caveat é 1 arquivo de metadado e 1 coluna cosmética — nenhum toca o mecanismo).

**VEREDITO: MELHOROU** (9,3 → 9,5). Causas **nomeadas**, em ordem de peso:

1. **CORREÇÃO REAL** — o único item (3) da F5 (A25) foi (i) **refutado** pela F5.4 (a DI‑41 já existia e o meu cálculo de impacto estava aritmeticamente errado) e (ii) **corrigido no dado**: a ⑦ da `swap_medium-lhs_ZDT4` foi regerada (mtime 29/07 13:29:14) e hoje **45/45 células têm 100 linhas com link posicional bit‑a‑bit** — era 44/45. O `spacing` dessa célula deixou de ser 0,0 e vale 1,9583742395.
2. **INSTRUMENTAÇÃO NOVA QUE FUNCIONA** — `tempo_geracao_s` (I‑7/A5) **medido igual a fit+busca ao float**, com a sonda fora; e as erratas 7 e 14 fecharam a divergência artefato×runner (e103 saiu de 🔴 para ✅ 6/6 no G‑7, re‑executado por mim).
3. **MAIS EVIDÊNCIA sobre o MESMO mecanismo** — três provas que a F5 não tinha: (a) a não‑perturbação da sonda **sobre a busca** (19 800 linhas bit‑idênticas), mais forte que a que a campanha declarou; (b) o **determinismo bit‑a‑bit** entre execuções independentes (5/5 pares, 4 camadas cada), que **derruba o teto T1**; (c) a **estabilidade cross‑arquitetura do endpoint** (ΔIGD+ 0,12 %) apesar de a busca divergir a partir da geração 37.
4. **NÃO foi amostra diferente** — o corpus é o mesmo, e nesta rodada eu **descobri que ele é menor do que eu disse**: 45 células = **40 execuções distintas**.
5. **Contrapeso** — 2 itens (3) novos, ambos plumbing, ambos com fix de minutos; e **3 erratas contra a minha própria F5** (`origem_solution_id`, o decay 17/6→22/23, o expoente O(N³)).

O que sustenta o 9,5 e não mais: **duas identidades FECHADAS sem exceção** (o gate 3σ em 4 455/4 455 ge


==========================================================================================
### CONFIG: e7

## 7. SCORE, recomendação e VEREDITO

# SCORE: 10 / 10 — recomendação: **ACEITAR**
# VEREDITO vs F5: **MANTEVE (10/10 = teto da régua) — com dois ganhos materiais que o score, já saturado, não consegue expressar**

**Por que o score não mudou:** a régua do FRAMEWORK-v2 §F5.3b dá 10 quando *"tudo (1)/(2), cada (2) ancorado em decisão documentada; contrato perfeito; saúde limpa"*. A F5 já estava lá, e nada nesta volta produziu um aspecto (3), um 🔴 novo ou uma anomalia de saúde. **"Manteve" é o veredito correto e esperado: o mecanismo não mudou — o e7 não recebeu uma única linha de correção de algoritmo na T11.** Re-executei as invariantes centrais e **todas reproduzem número por número**: joia 1.684/1.684 e 644/644, refutadores 695 e 1.215, gatilho 2.328/2.328, quantização 7,105e-15, `ymin` com erro 0,0 em 2.303, 6.837.200 linhas com σ>0, U7 com 0 violações e o espelho 1.187 = 1.207−20, 0 X fora do box em 81.988.800.

**As duas melhoras, com a causa NOMEADA:**
1. **CORREÇÃO REAL DA CAMPANHA (verificabilidade)** — o **T1**, que a F5 declarou *"o teto MAIS crítico de toda a bateria"* para este config, saiu de **não-verificável** para **provado por medição direta**: o par `g6_com`×`g6_sem` dá ①/② com sha256 idêntico e a ③ online bit-idêntica **incluindo `mu_*`/`sigma_*`** em 24.700 linhas. Para um config cujo σ é estocástico, essa é a prova mais forte possível de que a sonda não toca o RNG. T cai de 6 para 5, e o que saiu era o único item T ancorado num invariante 🔴 do CONTRATO.
2. **ERRO MEU, CORRIGIDO (fidelidade medida)** — **A11 migra de (2) para (1)**. A normalização `[−1,1]` do paper existe no código (`mapminmax` em X e Y, `EDNARMOEA.m:38-39,121-123`; `Estimate.m:13,18`), com duas assinaturas independentes nos dados (invariância de escala em 3,62e7× de amplitude, Spea


==========================================================================================
### CONFIG: e74

## 7. SCORE, recomendação e **VEREDITO vs F5**

# **SCORE: 9,5 / 10** · **Recomendação: ACEITAR (mecanismo) + CAVEAT DE CORPUS**

# 🔼 **VEREDITO: MELHOROU** (9,0 → 9,5)

**Causa NOMEADA: correção REAL, medida — não amostra, não instrumentação nova.** O único ponto que tirava 1,0 da nota da F5 era, textualmente, *"a eq. 7-8 — Contribuição 1 declarada do paper — não se realiza (argmax em 12,24%)"*. O fix DI-45 foi aplicado no código (verificado linha a linha contra o upstream **e** pelo content-hash lacrado) e **funciona nos dados**: argmax global 12,24% → **86,89%**, argmax restrito ao nível-1 → **95,88%**, razão de incerteza capturada 0,669 → **1,000**, rank mediano 43 → **1**, e as **duas** metades da Contribuição 1 passam a operar (pré-triagem 100%). **A11 migrou de classe (2) para classe (1)** — é a única mudança de classificação, e é a que move o score. Não dou 10 por três razões medidas, não por desconfiança: (i) só **3 dos 25 problemas** têm corpus pós-fix; (ii) o **2º desalinhamento permanece** e custa **4,12%** dos infills de s1; (iii) **duas dívidas de documentação** (anchors.json com instrução errada; 2º sítio mal localizado) que fariam a próxima auditoria errar.

**⚠ CAVEAT DURO DE CORPUS (novo, e é operacional):** as **25 células da s42 do e74 descrevem um algoritmo diferente do que rodará no M8**. Elas continuam válidas como evidência de fidelidade da s2/s3 e de todo o protocolo, mas **não podem ser agregadas** com runs pós-fix, nem servir de baseline de qualidade do e74 na R4/F5.5. Este é o único config em que isso vale.

---

## 8. Aspectos classe (3) 🎯 — para a F5.4

**Nenhum.** Zero aspectos vão à verificação adversarial. Registro os **três falsos-alarmes resolvidos dentro desta análise** (para que ninguém os levante de novo):

1. **"A s3 caiu para 32,


==========================================================================================
### CONFIG: e81

## 7. SCORE, RECOMENDAÇÃO E VEREDITO

# SCORE: 9,7/10  ·  VEREDITO: **MELHOROU** (F5: 9,5)

**Recomendação: ACEITAR.** 1 item ao D97 (A20, a ambiguidade B17.5 quantificada) · 1 item pequeno à torre central (o resíduo de A24) · 2 erratas de documento a corrigir.

**A causa NOMEADA do movimento — são três, e nenhuma é "amostra diferente":**

1. **Correção real.** O único aspecto classe (3) da F5 (B28) teve a **causa confirmada** e a **escrita corrigida** por duas barreiras independentes (`experiments.py:116‑124` B‑02 e `audit_log.py:53‑64` B‑01), e a primitiva de leitura nova **acerta o meu arquivo contaminado real** (1 footer legítimo entre 95). O que sobra é estritamente menor: 1 consumidor de exposição real (`progress.py:95`) não migrado, sobre um corpus congelado.
2. **Evidência nova que nenhuma amostra maior daria.** O par **pré×pós‑T11 da mesma célula** provou que a campanha inteira não moveu **nada** do e81: ①②③ bit‑idênticas e ④ diferindo **só** nas 4 colunas de wall‑clock. Isso valida retroativamente o uso da s42 como corpus de mecanismo *e* garante que o código de hoje reproduz aquela busca — algo que a F5 não podia afirmar.
3. **Um teto derrubado.** A fórmula de semeadura A6/D22 (`1024+iter+1000·s`, `2430+1000·s`) era **indeterminável com uma única semente**; o smoke em s=0 a determinou. O aspecto A15 sai de `direta-declarativa` para **direta**.

**O que NÃO mudou, e por isso o score não vai a 10.** O mecanismo é o mesmo — e essa é a conclusão certa, não uma limitação: a query‑joia fecha em **7.988/7.988** gerações com \|Δ\| máx **8,087e‑08** em valor, conjunto, ordem e marcação, com **16.700/16.700** links X bit‑idênticos, **e fecha 40/40 no código pós‑T11**. Os 15 desvios do paper seguem todos com decisão sancionada citada. Permanecem: o resíduo de leitura d


==========================================================================================
### CONFIG: moead

## 7. SCORE, recomendação e VEREDITO

### **SCORE: 9,0/10 — ACEITAR** (2 itens classe (3), ambos da camada DECLARATIVA, ambos investigados e provados benignos)

### **VEREDITO vs F5: MANTEVE** — mesma nota, composição diferente. As causas, nomeadas:

**O que EMPURROU PARA CIMA (3 causas, todas medidas):**
1. **CORREÇÃO REAL** — a T11 fechou as 3 lacunas do ⑤ que a s42 tinha (`campanha_id`, `repo_hash`, `sigma_dict`): a s42 reprova G-3 e G-7 em **25/25**, o smoke passa **5/5 + 1 n/a**. O `repo_hash` era **escalação explícita da minha F5 §5**.
2. **O MEU CLASSE (3) CAIU** — M16 (`n_front1` ±1 em 16/469) foi refutado pela verificação adversarial e eu **reproduzi a refutação com código próprio**: bracket fecha **469/469, 0 inexplicadas**. Pelo raciocínio da própria F5 isso valia +1,0 na nota.
3. **INSTRUMENTAÇÃO/EVIDÊNCIA NOVA** — a não-perturbação, que para o moead **não tinha prova** (sem par G-6), passou a ter a prova mais forte do lote: **bit-identidade das 4 camadas + do ⑥** entre o código pré-T11 e o pós-T11, na mesma célula. Isso valida retroativamente o uso da s42 como corpus de mecanismo **por medida**, não por argumento.

**O que EMPURROU PARA BAIXO (2 causas, ambas classe (3)):**
4. **AMOSTRA/QUERY NOVA** — **M10b**: a flag `frente1_excede_pop` compara com `N_nominal` em vez de `N_efetivo` (`src/experiment.m:2419`), errando em **2/25** células (DTLZ1, DTLZ3) e em 4/100 nos 4 pisos. Defeito pré-existente que a minha F5 **não mediu** (eu li a flag como se fosse contra N_ef e escrevi um intervalo errado no §M10). A T11 não o tocou.
5. **REGRESSÃO INTRODUZIDA PELA T11** — **X3**: a string `geracoes_derivadas` trocou uma fórmula errada por uma redação honesta **com um mecanismo falso para este config**, e a falha é sistemática exatamente nas 6 células M=3.

**Por que


==========================================================================================
### CONFIG: moead_media

## 7. SCORE, RECOMENDAÇÃO e VEREDITO

### **SCORE: 9,3/10 · RECOMENDAÇÃO: ACEITAR + CAVEAT**
### **VEREDITO: MANTEVE**

**A régua da comparação.** O `scores_f53.csv` registra **9,0**; o veredito adversarial `moead_media-C9b.md` §Impacto item 3 determinou a subida para **9,5** ao derrubar o único (3) da F5. A base honesta de comparação é, portanto, **9,5**, e não 9,0.

**Por que MANTEVE — a causa nomeada, item a item:**

1. **O mecanismo não mudou, e isso está MEDIDO, não presumido.** O `sigma_dict` do smoke pós-T11 é **idêntico** ao da s42 nas 20 chaves de mecanismo (única diferença: a chave nova `granularidade_③`, que é *declaração*, não comportamento). O smoke reproduz a assinatura inteira: `n_geracoes=801`, `fe_final=61`, 40.050 linhas de busca, 20.000 de sonda, N=50, σ NaN 100%, ⑥ com o mesmo conjunto de chaves. A campanha T11 foi, para este config, **read-only sobre o comportamento** — e a s42 continua sendo evidência válida da busca que o código de hoje faria.
2. **O que subiu (+):** a não-conformidade de contrato da F5 (⑤ sem `params`) **fechou** e eu a verifiquei no dado; a causa do único defeito de integridade da F5 (o resíduo de dois escritores) **fechou em código** (`O_TRUNC`); a identidade de campanha (`campanha_id`/`repo_hash`/schema v2) entrou; a `granularidade_③` **converteu um teto de leitura em fato provado** (LHS 1,0000 em 45/45; 40.000 exatos de seleção); e a ERRATA 12 **blindou a ablação** ao declarar `p_wrong_stats` inaplicável com o argumento certo.
3. **O que desceu (−):** nasceu **um (3) novo** (A25, `tempo_aval_real_s` medindo uma `lambda` de ingestão no offline, 22,2× fora da escala dos online, contra a docstring do próprio código); e a correção que a F5.4 pediu **por nome para `src/piso_offline.py`** — o wrapper do `adapt` — **não foi entregu


==========================================================================================
### CONFIG: nsga2

## 7. SCORE e VEREDITO

### **SCORE: 10/10 — ACEITAR** · **VEREDITO: MANTEVE**

**Por que MANTEVE, com a causa nomeada.** O score não muda porque **o mecanismo não mudou — e desta vez isso é medido, não inferido**: o smoke T11 e a célula da s42 de `main/nsga2/DTLZ2` são **bit-idênticos** na ①, na ② e, campo a campo, no ⑥ (0 de 42 registros divergentes fora de `ts`/wall). As quatro correções da T11 que tocam o config são **todas de instrumentação do ⑤**, e a inspeção dos três commits que alteram `src/experiment.m` na região do piso confirma que nenhum toca uma linha de algoritmo; `src/piso_instrument.m` não foi tocado pela campanha. **Não havia correção de mecanismo a validar porque a F5 não achou defeito de mecanismo** (0 classe (3) em 25 aspectos).

O que a T11 **melhorou** de fato, medido: **3 das 4 lacunas declarativas que a F5 apontou fecharam** — `repo_hash` (I-09), `sigma_dict` (G-7) e a string errada de `geracoes_derivadas` (I-13) — e a **armadilha nº5 da F5** (recomputar dominância na ① é recomputá-la em float32) virou a **regra normativa 11 do CONTRATO**. O que **não fechou**: o header do ⑥ (`run_id`/`ambiente`/`params`/`sigma_dict`, CONTRATO §6 l.296) segue vazio na s42 **e no smoke**; e o gate novo G-7 cobre 2 dos 4 campos da linha "pisos".

**Por que segue 10 e não 9.** A base do 10 é o mecanismo, e ele está intacto e mais provado que antes: **zero aspectos (3)**; a query-joia D88 fecha 25/25 (24 diretas + DTLZ4 restaurado em float64, fórmula validada 393/393); o ledger da D89 fecha 25/25 **por dois métodos independentes**; `n_geracoes = D+1` deixou de ser regularidade observada e passou a ter **mecanismo provado** (`Σ(20−Δfe_g) ≡ resto`, 25/25); 1.613 transições sem uma violação. A lacuna do G-7 é de **cobertura de gate**, não de dado nem de algoritmo — e 


==========================================================================================
### CONFIG: nsga3

## 7. SCORE e VEREDITO

### **SCORE: 10/10 — ACEITAR** · **VEREDITO: MANTEVE** (com fortalecimento medido da evidência)

**Por que MANTEVE, e não MELHOROU ou PIOROU — a causa nomeada.** O score não podia subir (já era o teto) e não havia por que descer. A razão substantiva é **A29: o mecanismo não mudou, e isso está provado bit-a-bit** — a ① e a ② do smoke pós-T11 têm o **mesmo sha256** das da s42 na mesma célula. Não é "a campanha alega que a instrumentação é read-only"; é a mesma busca, o mesmo lattice, a mesma semeadura, a mesma aritmética. As três correções do T11 vivem todas depois do `Solve`.

**O que MELHOROU, e é medida, não impressão:**
1. **Um teto caiu (A27).** `patches: NENHUM` era declaração na F5 (T, `repo_hash=""`); hoje é medida tripla — o `preflight` **passou a conferir o PlatEMO** (antes o pulava), o lacre de conteúdo bate, e o `git status` do repo vendorizado mostra **12 arquivos sujos, nenhum deles do NSGA-III / UniformPoint / NDSort / CrowdingDistance / OperatorGA**. A alegação central do piso deixou de repousar em `algo_version`.
2. **Dois aspectos subiram de verificabilidade (A9, A15):** a truncagem `2⌊N/2⌋` e os defaults `deal(1,20,1,20)` saíram de "medido + hipótese"/"config-echo" para **verificados no fonte**.
3. **Três buracos de contrato do ⑤ fecharam** (A23/A25/A26): a s42 entrega 3/6 do `quinto_obrigatorio`; o código de hoje entrega 6/6, e os gates de proveniência dão `G-7 ⑤ 6/6` sobre o smoke.
4. **Um aspecto novo com poder explicativo (A11+A28):** a taxa de duplicata deixou de ser assinatura empírica e virou **quantidade prevista a priori** pelo operador (1,91% previsto × 2,55% medido, r=0,81, ordenação M=3 > M=2 reproduzida).

**O que PIOROU — nada de mecanismo; um item documental novo:** a string `geracoes_derivadas`, que a F5 mandou c


==========================================================================================
### CONFIG: smsemoa

## 7. SCORE, recomendação e VEREDITO

# SCORE: 10 / 10 — ACEITAR
# VEREDITO: **MANTEVE** (10 → 10), com **evidência estritamente maior**

**Por que MANTEVE e não MELHOROU no número — a causa nomeada.** O mecanismo **não mudou**, e isto não é suposição: está medido no aspecto #25 — o código de hoje reproduz a célula da s42 **bit-a-bit em 5 das 6 camadas**, com a única diferença em todo o dado sendo o wall-clock do ④. Um score que já estava no teto da régua ("tudo (1)/(2), cada (2) ancorada em decisão documentada; contrato perfeito; saúde limpa") não tem para onde subir quando o objeto avaliado é idêntico. O que mudou foi a **confiança**, e ela mudou em quatro frentes mensuráveis:

1. **O balde T encolheu de 2 aspectos para 1**, e por dois caminhos diferentes: o ramo interno do `Reduce` virou **assinatura medida no dado** (`ideal` 0/266 em M=2 × 10/85 em M=3, precisamente onde `Reduce.m:21` troca de ramo), e o sorteio de pais virou **leitura de fonte lacrada** (`SMSEMOA.m:29`) com a ausência de log reconhecida como **exclusão sancionada** do CONTRATO §6.1. O T que resta (#26, o `FrontNo` incremental) é muito mais estreito e muito mais preciso.
2. **Dois aspectos deixaram de ser declarativos.** A T11 lacrou o PlatEMO por content-hash (`fb9ed1d399d4`, `LACRE OK` conferido hoje), e `git status` da árvore mostra **12 arquivos modificados, zero em `SMS-EMOA/`**. A pureza do piso deixou de ser um eco de header.
3. **Duas lacunas de contrato que EU escalei foram fechadas no código** (`repo_hash` — o `PLANO:72` cita "item 9 do smsemoa") ou **no documento normativo** (`regra 11 do CONTRATO`, do meu item 11), e o `mapa_termino.json` transformou a minha armadilha ⑧ num artefato que 3 scripts consomem.
4. **A confirmação opcional que eu deixara em aberto foi encerrada** — a causa do


==========================================================================================
### CONFIG: sobol_batch

## 7. SCORE e VEREDITO

### **SCORE: 9,5 / 10 — recomendação: ACEITAR** (caveats de leitura, nenhum de mecanismo)
### **VEREDITO: MELHOROU** (9,0 → 9,5)

**A causa, nomeada — são três, em ordem de peso:**

1. **CORREÇÃO REAL, verificada em comportamento (não em presença de campo).** Os **três** achados classe (3) da F5 foram fechados e eu os verifiquei um a um contra o padrão do c217 (campo presente / dado sentinela): `n_front1` está presente **e correto em 1.000/1.000** eventos q=10 com NDS recomputado (faixa 5–221, até 121 valores distintos por célula, zero sentinelas); `tempo_aval_real_s` saiu de **0,0 exato em 5/5** para 0,0176–1,5387 s **e passou a cobrir o custo do DoE inicial que a F5 declarara irrecuperável** (razão acumulador/proxy = 1,085 no WFG9); `params` está no ⑤ em 5/5 com os valores derivados das mesmas fontes da busca. Classe (3) caiu de **12,0% (3/25) para 3,7% (1/27)**.
2. **EVIDÊNCIA NOVA que não existia na F5.** O corpus POS-T11 deste config existe (errata 17) e, sobretudo, o re-run q=10 provou **bit-identidade ①②④ pré×pós-T11 em 5/5 células** (dX=dF=0,0 sobre 11.029 linhas de ① e 1.211.829 de ②), em outra máquina e outro SO. Nenhum outro config do estudo tem prova de não-perturbação tão forte — e ela é o que autoriza formalmente usar a s42 como corpus de mecanismo depois da T11. Some-se o **controle-positivo do G-7** (RUIM na s42 × OK no pós), que torna a correção auditável por terceiro sem me refazer.
3. **A amostra não mudou** — as mesmas 5 células, os mesmos indicadores, o mesmo papel de régua. O mecanismo **não mudou**: era fiel e continua fiel. O que subiu foi a **auditabilidade**, e é exatamente por isso que o salto é de meio ponto, não de dois: a régua da F5 dá 10 a "tudo (1)/(2), cada (2) ancorado, contrato perfeito, saúde limpa" e 9 a "id


==========================================================================================
### CONFIG: treed_media

## 7. SCORE, recomendação e VEREDITO vs a F5

### SCORE: **9,5/10** · RECOMENDAÇÃO: **ACEITAR o mecanismo + CORRIGIR 2 itens de instrumentação ANTES do disparo** (ambos ≤2 linhas, ambos transversais aos 5 offline Python)

### VEREDITO: **MANTEVE** — com o mecanismo mais VERIFICÁVEL e duas regressões de instrumentação nomeadas

**A causa do "manteve", nomeada:** **o mecanismo não mudou, e desta vez isso não é inferência — é medida.** As camadas ①③⑦② da célula `sweep-big-mvns/ZDT4/42` saem **bit-idênticas** antes e depois da T11 (107.318 linhas; a ③ com os mesmos 1.472.124 bytes). Não há "amostra diferente", não há deriva numérica, não há re-classificação de aspecto por mais evidência: o algoritmo de hoje é literalmente o algoritmo de 24/07. Por isso a nota de FIDELIDADE fica onde estava.

**O que MELHOROU (e é substantivo):**
1. **A18 saiu do balde estatístico.** A decomposição 10×100 do RVEA — o único aspecto do mecanismo central que a F5 só sustentava com um teste de permutação (p≤0,053 em 10/10) — agora é **observação determinística**: 10 eventos `checkpoint` em `iteracao`=100,200,…,1000, um por `iterate()`, com `n_linhas_terceira` casando com a ③ em 10/10.
2. **A premissa desta campanha inteira ficou provada para este config.** "A busca da s42 é a que o código de hoje faria" era, no briefing, uma extrapolação de 19 pares MATLAB. Aqui está medida, bit-a-bit.
3. **Um buraco real de silêncio foi fechado e eu o executei** (N2): o guard de tier barra 5/5 despachos errados, e o dano que ele evita é um dataset **162× menor** gravado sob o nome desta célula com o manifesto internamente coerente.
4. **A proveniência chegou ao ⑤** (`campanha_id`/`repo_hash`/schema v2), medida.

**O que PIOROU (0 → 2 aspectos classe (3)):** ambos nasceram na T11, ambos vivem na camada de TEMPO
