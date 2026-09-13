## SÍNTESE COM 30 SEMENTES — evidência, não veredito (D97)

### 0 · O que foi efetivamente medido

Recalculei **do zero** a camada de métrica sobre o canônico, com `src/metrics.py` (D69/D70/D92), sem tocar em `experiments.py`/`experiment.run` (verifiquei por AST que `src/experiment.py` só tem docstring + 9 constantes + 4 funções no topo — import sem efeito colateral; ainda assim os ref-sets foram cacheados em disco e o harvest não importa nada do despachante).

- **Gate D92 reproduzido**: `hv_smoke_bbob_f1()` = **1,0433** (âncora oficial). Métrica validada antes de qualquer número.
- **15.129 células do censo lidas** → **15.033 com ① legível**, **2.129 com ⑦**. As 96 sem ① são todas `fail` (95) + 1 célula `batch` do e81.
- **Fecha a ressalva O-21 sobre as ⚪**: as **501/501 células ⚪ têm ① legível**, inclusive **as 300 do c154** (`fe_final` mediano 296 = **46% do orçamento 31D−1**; c122 91%, c262 89%, c149 91%). A presença que estava por conferir está conferida.
- **Cross-check contra o número já aceito na F5** (`f5/metricas_finais_f52c.csv`, semente 42): 505 linhas casadas, **360 (71,3%) idênticas a <1e-9** — meu encanamento é o mesmo. As 145 divergentes **não são erro meu**: em **132 delas o próprio `n_nd` da ① mudou**, i.e. o dado embaixo mudou (ver escalação nº 7).

---

### 1 · Contraste surrogate × piso — **de 17,7% para ~75–80% de comparações conclusivas**

Unidade de aleatorização = **semente**. Teste = **Wilcoxon signed-rank pareado por semente** + **Holm** sobre toda a família de comparações + **rope 0,05** (D48/D70) + **bayesiano de sinais-postos** (Benavoli 2014). Endpoint IGD+ (D70). Só comparações com ≥20 pares.

| comparador do "piso" | N | SA vence na mediana | **conclusivas (Holm)** | pró-SA / pró-piso |
|---|---:|---:|---:|---:|
| **C** — mín. dos 4 pisos **por semente** (= o análogo exato do n=1) | 294 | 41,5% | **234/294 = 79,6%** | 91 / 143 |
| **A** — melhor piso pela mediana das 30 | 294 | 46,9% | **221/294 = 75,2%** | 101 / 120 |
| **B** — nsga2 pré-fixado | 294 | 53,1% | **204/294 = 69,4%** | 117 / 87 |

**Resposta direta:** com n=1 eram **54/305 (17,7%)**. Com n=30 são **221–234 de 294 (75–80%)** — um fator **4,3×**. Estável sob a política de inclusão das ⚪ (P2 = ok+teto dá 240–253/317 = 75,7–79,8%).

**O piso de ruído mudou de natureza.** O O-18 (58,98%, entre máquinas) era o floor errado. Medido agora, **entre sementes**, em 394 pares (alg×problema, n≥20): IQR/mediana **22,9%**, amplitude(máx−mín)/mediana **78,8%**, CV **19,6%** — e **67,3% dos pares têm amplitude entre sementes MAIOR que o piso O-18 inteiro**. A variância da semente domina a variância da máquina. Aplicado à moda antiga, o O-18 sobre as medianas das 30 deixaria só 36,1% "conclusivas" — é ele que estava sufocando o estudo, não os dados.

**Por família** (comparador A; `n=1` entre parênteses):

| família | vence na mediana | conclusivas |
|---|---:|---:|
| BBOB | 64,8% (66%) | **74,7%** (28%) |
| ZDT | 69,4% (62%) | **73,5%** (42%) |
| MMF | 56,9% (62%) | **47,1%** (**0%**) |
| DTLZ | 27,1% (34%) | **81,4%** (14%) |
| WFG | 20,0% (26%) | **85,0%** (**2%**) |

**A família separa — e agora é teste, não descrição.** Friedman com **config como bloco** (12 configs SA) e família como tratamento: **χ²=31,53, p=2,4e-06**. Ranks: ZDT 1,33 · BBOB 2,50 · MMF 2,58 · WFG 4,17 · DTLZ 4,42. Post-hoc Wilcoxon+Holm: **8 dos 10 pares separam**; os que **não** separam são **BBOB~MMF** e **DTLZ~WFG** ⇒ as 5 famílias colapsam em **3 blocos: {ZDT} ≫ {BBOB, MMF} ≫ {WFG, DTLZ}**. O efeito é enorme em ZDT (log₂ razão até −5,43 no c262 = 43× melhor) e a taxa de vitória do n=1 escondia isso porque é adimensional.

**"A vantagem cresce com D" — continua não sustentada, agora com teste.** Spearman de log₂(IGD+_SA / IGD+_piso) vs D, **por config**: ρ mediano **+0,006**; Wilcoxon dos 13 ρ contra 0: **p=0,787**; 7/13 ρ positivos. Só o e81 é individualmente significativo (ρ=+0,49, p=0,012, **sem** correção). Por D (comparador C): 2→46,2% · 7→0% · 10→59,0% · 12→20,0% · 20→50,0% · 22→23,9% · 30→69,6% — não-monotônico. **Dentro de DTLZ** (o único onde D varia com família fixa em 3 níveis) o sinal é o **contrário**: ρ=−0,507, p=4,2e-05 (o SA melhora com D). O confundimento D×família da D50 é **total** no set atual: D=7 é só DTLZ1, D=20 é só MMF16_20, D=30 é só ZDT1/ZDT3.

---

### 2 · Ranking dos 22 configs — **estável às sementes, instável ao conjunto de problemas**

**Não existe bloco completo 17×25.** Nenhum problema tem os 17 configs do `main` com ≥20 sementes fora de 8; nenhum config tem os 25 problemas fora de 11. O "quadro global de Friedman, vista única com os 25 problemas, **blocos completos**" do §15.1 **não é executável** no corpus atual (escalação nº 6). Rodei três recortes.

**Bloco A — 11 configs × 25 problemas (completo).** Friedman χ²=84,63, **p=6,2e-14**. CD Nemenyi(0,05)=3,020.

```
c141 2,92 · b3 3,96 · e74 4,44 · smsemoa 4,80 · nsga2 5,52 · nsga3 6,16
· e7 6,20 · b4 7,16 · c217 7,28 · e81 8,08 · moead 9,48
```

**Incerteza, decomposta (bootstrap B=2000, mesma reamostra aplicada a todos — o DoE é compartilhado):**

| fonte | largura mediana do IC95 do rank médio | nº mediano de posições plausíveis (p≥5%) |
|---|---:|---:|
| **sementes** | **0,60** | **2** (mín 1, máx 2) |
| **problemas** | **2,04** | 4 (mín 2, máx 6) |
| ambas | 2,12 | 4 |

**O conjunto de problemas contribui 3,4× mais incerteza que as sementes.** Com 30 sementes a posição de cada config é praticamente determinada (probabilidade da posição modal 0,52–1,00; c141 fica em 1º em 100% das reamostras, e81 em 10º em 100%, moead em 11º em 100%). Mas o Nemenyi sobre 25 problemas só separa **17 dos 55 pares** — 38 permanecem indistinguíveis, inclusive `c141~smsemoa` e `nsga2~e81`. **Mais sementes não compram poder no quadro agregado; mais problemas comprariam.** (Se a unidade for (problema,semente) em log-razão, 52/55 pares "separam" — mas isso é pseudo-replicação entre problemas; ver escalação nº 5.)

**Bloco B — 17 configs × 8 problemas (completo, mas o subconjunto é enviesado: sem WFG, sem ZDT1/3/6, 1 DTLZ):** Friedman χ²=48,00, p=4,8e-05; CD=8,731 sobre um spread de 12,9 ⇒ praticamente nada separa; até **7 posições plausíveis** por config.

**Ranking descritivo (17 configs, rank entre os presentes — o formato do n=1):**
```
c262 3,65 · c141 4,36 · c122 4,71 · b3 5,92 · e74 6,64 · b1 7,46 · smsemoa 7,48
· c238 7,52 · c154 7,62 · nsga2 8,36 · nsga3 8,96 · e7 9,36 · b4 10,16
· c217 10,32 · e81 11,56 · moead 12,60 · c149 14,70
```
**Concordância com o ranking da semente 42: Spearman ρ = 0,973 (p=5,8e-11).** O ranking do n=1 já estava certo; as 30 sementes trocaram apenas pares vizinhos (c141↔c122, b3↔e74, smsemoa↔c238, e7↔nsga3). ⚠ c154 aparece em 9º sobre **8 problemas** e 40,5% de células ok — não é comparável às outras linhas.

---

### 3 · Ablação offline — **⚠ o par do enunciado não é a ablação (D81)**

**Conflito com a fonte, registrado e não resolvido por mim.** O enunciado diz que b5m×b5r "difere só na seleção probabilística". `src/b5_prob.py:1` e `src/piso_offline.py:1-14` dizem outra coisa: **b5r = Prob-RVEA (mode 7)**, **b5m = Prob-MOEA/D (mode 72)** — diferem no **motor** (RVEA × MOEA/D), **ambos com seleção probabilística**. Quem difere **só** na seleção é **b5m (ProbMOEAD_select) × moead_media (MOEAD_select, mode 12)** — literalmente "a ABLAÇÃO CIRÚRGICA do b5… mudando SÓ a seleção… o b5 sem σ" (D77/DEF-E3). **Corroboração estrutural medida:** b5m e moead_media entregam ND de tamanho **idêntico em 25/25 problemas**; b5r entrega menor (44 vs 50) em 25/25 (p=1,2e-05). Medi os três pares.

**A ① empata por desenho — agora provado, não afirmado.** Nas **623 células (problema,semente)** com os 4 offline presentes: **1 único valor distinto de IGD+① por célula em 623/623 (100%)**, diferença relativa máx−mín = **0,000e+00** na mediana **e no p99**. O endpoint é a ⑦, sem discussão.

**Na ⑦ (IGD+, pareado por semente, Holm; unidade global = problema, n=25):**

| par | melhor na mediana | conclusivos | global (n=25) | bayesiano (rope ±5%) |
|---|---:|---:|---:|---|
| **b5m × b5r** (o do enunciado) | 12/25 p/ b5m | 6/25 (5 / 1) | **p=0,958** | P(b5m)=0,523 · P(rope)=0,012 · P(b5r)=0,465 |
| **b5m × moead_media** (σ real) | 15/25 p/ b5m | 10/25 (4 / 6) | **p=0,182** | P(b5m)=**0,867** · P(rope)=0,000 · P(piso)=0,133 |
| b5r × moead_media | 12/25 p/ b5r | 14/25 (8 / 6) | p=0,458 | P(b5r)=0,834 · P(rope)=0,000 · P(piso)=0,166 |

**Friedman dos 3 na ⑦: χ²=0,32, p=0,852** (ranks 1,92 / 2,00 / 2,08) — **indistinguíveis em agregado com n=30**. O valor de σ é **direcionalmente favorável e não conclusivo**: 0,87 de probabilidade bayesiana, longe de qualquer limiar decisório, e o efeito é fortemente **problema-dependente** (b5m ganha muito em WFG2/WFG4 — log₂r −1,21/−1,68 — e perde muito em ZDT1/ZDT3 — +2,24/+0,66).

**A assinatura do paper do b5 NÃO se reproduz.** "Fantasia" (`nd_pos_real/n_final`, maior = modelo menos iludido): **b5m 0,300 · b5r 0,283 · moead_media 0,305**. Nenhum par difere com o problema como unidade (p=0,52 / 0,80 / 0,62). O piso **sem σ** é o **menos** iludido pela mediana. HV⑦ idem, sem diferença (p=0,18–0,60).

**e103 sem a ⑦ — pergunta aberta RESPONDIDA (medido).**
- ⑦ ausente em **669/669** células do canônico **e em 0 arquivos dos 6 espelhos de VM** (`~/mestrado_coleta_m8/matlab-vm{1,2,3,4,5,10}`).
- **Causa mecânica**: a ⑦ **não é escrita pelo run** — é escrita pelo passo **pós-hoc `scripts/final_eval.py`** (docstring: lê a ③, pega a última geração, avalia 1× em `problems.py`, grava a ⑦; "determinístico e idempotente"). `src/e103_instrument.m` **não contém a string "final"**. O lote de `final_eval` cobriu b5m/b5r/moead_media e **não** cobriu o e103. *Não medido: por que o lote não o cobriu.*
- **Regressão**: a s42 do e103 **tinha** a ⑦ (F5 mediu 45/45, `f5/transversal_offline_camada7.csv` traz IGD+⑦=0,2251 e o e103 **liderava** os 5 offline). Hoje `e103/*/42/` tem 6 arquivos, mtime **07/08/2026**, **sem** `__final.parquet`. Foi re-aterrado sem a camada.
- **Custo de recuperação: zero re-run** — `$PY scripts/final_eval.py --alg e103 --all-seeds`. **Não executei (READ-ONLY: escreve no repo).** Enquanto não rodar, **o e103 não pode entrar no ranking offline**, e o quadro offline acima está sem o config que liderava no n=1.

---

### 4 · O que MUDA em relação ao n=1

**Passa de inconclusivo a CONCLUSIVO (o ganho principal das 30 sementes):**
1. **A régua inteira.** 17,7% → **75–80%** de comparações acima do piso inferencial. As duas famílias-âncora que tinham **0/50 (MMF)** e **1/58 (WFG)** conclusivas agora têm **24/51** e **51/60**.
2. **"A família separa"** deixa de ser descrição e vira teste: Friedman p=2,4e-06, 8/10 pares pós-hoc significativos, **3 blocos** ({ZDT} ≫ {BBOB,MMF} ≫ {WFG,DTLZ}) — e BBOB~MMF e DTLZ~WFG **não** separam, o que a leitura por percentual do n=1 não podia saber.
3. **O empate da ① no offline** vira fato medido (623/623, spread 0,000e+00), não inferência de desenho.
4. **A estabilidade do ranking** vira medida: IC95 do rank médio ±0,3 e ≤2 posições plausíveis por config.

**CONFIRMA-SE (mesmo sinal, agora com n):**
5. **"A vantagem do surrogate cresce com D" segue sem sustentação** — ρ mediano +0,006, p=0,787. E o único recorte com D variando dentro de família aponta para o **contrário** (DTLZ: ρ=−0,507, p=4,2e-05).
6. **A ordem por família** se mantém no topo e no fundo: BBOB/ZDT altos, DTLZ/WFG baixos.
7. **O ranking global** se mantém quase intacto: **Spearman ρ=0,973** com a s42.
8. **O endpoint do offline é a ⑦**, não a ①.

**INVERTE-SE ou se corrige:**
9. **A taxa de vitória do surrogate era otimista.** Com o comparador análogo (envelope por semente): **50,8% (n=1) → 41,5% (n=30)**. E o erro é **assimétrico**: no subconjunto onde o dado da s42 **não** mudou, a semente 42 dava 13 falsos "SA vence" contra 4 falsos "SA perde". **Taxa de inversão de sinal de uma semente qualquer: 11,4% mediana (mín 8,5%, máx 16,9%)** sobre as 30 — quantificação direta do custo de n=1.
10. **A ordem interna das famílias muda quando se olha tamanho de efeito e não taxa de vitória:** ZDT sai de "empatado com MMF" (62% vs 62%) para **isoladamente o primeiro** (rank 1,33 vs 2,58, p=0,0068 após Holm). MMF cai de 62%→57% e WFG de 26%→20%.
11. **A ablação offline INVERTE de "o piso perde" para "indistinguível":** no n=1 o quadro da ⑦ dava e103 17 vitórias / b5r 2 / b5m 2 / c311 3 / moead_media 1. Com 30 sementes, **Friedman p=0,852** entre b5m/b5r/moead_media, e o **σ do b5 não é conclusivo** (P=0,867) — e a "fantasia" do b5, que é a assinatura do paper, **não difere do piso sem σ**.
12. **O piso de ruído O-18 (58,98%, entre máquinas) fica obsoleto como critério** — a dispersão **entre sementes** o excede em 67,3% dos pares alg×problema. Manter o O-18 como filtro descartaria 64% de comparações que o teste pareado declara conclusivas.

**Fica PIOR do que se sabia:**
13. Das 234 comparações conclusivas (comparador C), **143 são a favor do piso** e 91 a favor do SA. O que as 30 sementes tornaram conclusivo foi, em maioria, a **derrota** do surrogate — sobretudo em WFG (44 pró-piso) e DTLZ (40 pró-piso). Com n=1 isso era invisível.

---

### 5 · ESCALAÇÕES (D81) — decisões metodológicas que **não** tomei

1. **🔴 b5m×b5r não é a ablação de σ.** Fonte contra enunciado (`src/b5_prob.py:1`, `src/piso_offline.py:1-14`), com corroboração no dado (|ND| idêntico b5m≡moead_media em 25/25). Entreguei os dois pares. **O autor decide qual vai ao capítulo.**
2. **Qual é "o piso".** A escolha do comparador move a taxa de vitória em **12 pontos** (41,5% C → 46,9% A → 53,1% B) e a contagem de conclusivas em 10 pontos. O comparador A (melhor piso escolhido pela mediana dos mesmos dados) é **selecionado no próprio desfecho** → otimista. O C é o análogo exato do n=1. O B é o único não-enviesado. **Não escolhi.**
3. **Política de inclusão das ⚪.** P1 (só ok) favorece os 4 configs truncados; P2 (ok+teto) os penaliza por orçamento desigual (c154 a 46% do 31D−1). Os headlines são estáveis entre as duas, mas o ranking de c154/c122/c262 não é. **Não escolhi** — reportei as duas.
4. **O rope 0,05 ABSOLUTO da D70/D48 é incomensurável entre problemas.** IGD+ vai de 7,3e-04 (c262×ZDT1) a 600 (offline×DTLZ3). Um rope fixo de 0,05 é trivialmente excedido nos DTLZ1/DTLZ3 e nunca alcançado nos ZDT1/BBOB_F1. Sugestão a decidir: **rope relativo** (usei ±5% em razão nos testes bayesianos globais). Com o rope absoluto, 61,9% ficam "fora"; com ±5% em razão, só 8,5% são empate prático.
5. **Unidade do quadro agregado.** Problema (Friedman/Nemenyi, N=25 → 17/55 pares separam) × (problema,semente) pooled (N≈700 → 52/55 separam). O segundo é mais poderoso e **pseudo-replica entre problemas**. A D70 implica o primeiro. **Consequência que precisa ir ao texto: as 30 sementes não aumentam o poder do ranking agregado.**
6. **O §15.1 ("Friedman, 25 problemas, blocos completos") não é executável** no corpus atual — não existe bloco 17×25. Alternativas: bloco A (11×25, perde os 6 configs mais interessantes) ou bloco B (17×8, subconjunto enviesado) ou imputação. **Não escolhi.**
7. **A base de comparação n=1 está superseded.** 145 das 405 células `main` da semente 42 mudaram de valor desde a F5, **132 delas com `n_nd` diferente** (o dado mudou, não a métrica), concentradas em e74/c122/e81/c262/e7/c149/c154/c238 — os configs de stack Python/BoTorch. O corpus atual é **internamente homogêneo** (`repo_hash = 63db46b1…` único em todos os 22 configs e nas 30 sementes), então a análise acima é sólida; mas **não dá para separar "efeito de n" de "efeito de re-execução"** nesses 8 configs. Isolei o efeito puro de n nos 150 pares cujo dado da s42 não mudou (inversão 11,3%, consistente com os 11,4% globais).
8. **`gabarito_camadas.json` se contradiz sobre a ⑦ do e103**: `_meta.medido_na_rodada_42` diz "final (⑦) em 100% das células … e103(49)"; `_meta.por_que` diz "44 dos 49 vermelhos eram e103 sem a ⑦". Mesmo arquivo, mesma rodada.
9. **|R| dos BBOB é pequeno.** Os ref-sets empíricos saíram com **233–523 pontos** (F37 233, F17 264, F49 309, F55 460, F22 474, F5 523), não os ~5.000 do §12.2 — só o F1 (analítico) tem 5.000. A própria SPEC cita o alerta do K-RVEA de que "IGD é muito sensível ao tamanho do reference set". Os 7 BBOB são 91 das 310 comparações. Já é sabido que o IGD deles é relativo (§12.1), mas a **resolução** é outra coisa e não está declarada.
10. **c154 não é comparável às demais linhas**: 40,5% ok, ⑦ irrelevante, 8 problemas no ranking, ⚪ a 46% do orçamento.

**Não medido (e por quê):** ⑦ do e103 (ausente; reconstruir exige rodar `final_eval.py`, que escreve no repo — vetado) · sub-estudo **sweep 29×21** (o token `sweep` não está no censo de 22 configs) · spot-check cross-máquina pelas duplicatas dos `reorg_conflitos.log` · IGDX dos 4 MMF (D99) · attainment worst-case (D52) · trajetórias §13 · regime `batch` (4 células, n insuficiente) · c238 **não foi tocado** (investigação da torre pendente) · nenhuma VM foi desligada, nada foi deletado, nenhuma célula disparada.

---

### 6 · Arquivos (⚠ scratchpad da sessão — copiar antes de fechar)

`/private/tmp/claude-501/-Users-gmello/33c29160-6eb6-4277-a041-db4855486063/scratchpad/f30_analise/`

- **`metricas_30seeds.csv`** (2,3 MB) — a base: 15.129 células × {igd_plus, hv, igd, gd, spacing, n_nd, n_rows, fe_final} da ① **e** da ⑦, com `estado` do censo. É o insumo de qualquer re-análise.
- `t1_regua_P1_ok.csv` / `t1_regua_P2_ok_teto.csv` — 930/972 comparações (3 comparadores × config × problema) com mediana, razão, fração de sementes vencidas, p de Wilcoxon, p de Holm, rope, O-18 e as 3 probabilidades bayesianas.
- `t1_por_problema.csv` · `t2_blocoA.csv` · `t2_blocoB.csv` · `t3_igdplus7_por_problema.csv`
- Scripts reprodutíveis: `build_refsets.py` · `harvest.py` · `lib30.py` · `t1_regua.py` · `t2_ranking.py` · `t2b_incerteza.py` · `t3_offline.py` (todos com o interpretador `mestrado_experimentos_dissertacao`, sementes de bootstrap fixadas em 20260815).
- `../refsets/*.npy` — os 25 reference sets normalizados (cache; DTLZ7 leva 6,5 min para reconstruir).