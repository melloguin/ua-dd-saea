# REPASSE À TORRE CENTRAL — campanhas T12 e T13 (2026-07-31)

**De:** sessão de implementação (cartão `handoff/T12-CARTAO.md` + os blocos B e C que o autor
encomendou depois) · **Para:** torre central
**Registro:** `REGISTRO_DECISOES_IMPLEMENTACAO.md` **PARTE A41** (T12) e **PARTE A42** (T13)
**Duração:** 15:20 → 19:45 (**4h25**) · **11 commits** · **suíte 627 → 688, 0 falhas**

> Este documento é **auto-suficiente**. Quem o ler tem o mesmo contexto de quem executou. Ele
> supersede o `handoff/T12-FINAL.md` (que cobre só o T12) — aquele continua válido, este é maior.

---

## §0 · COMO LER

| você tem | leia |
|---|---|
| **3 min** | §1 (as 3 respostas ao autor) + §12 (definições em aberto) |
| **15 min** | + §2 (tabela suprema) + §4 (os achados) |
| **completo** | tudo — §5 a §11 são o detalhe por item, os erros e as lições |

---

## §1 · AS TRÊS RESPOSTAS QUE O AUTOR PEDIU

### (1) Está 100% pronta a etapa? Rodou código? Qual e qual foi o resultado?

**Está pronta, sim — com uma exceção declarada e uma lista de 9 itens que nunca estiveram no
escopo.** O que foi encomendado (T12 completo + blocos B e C) está implementado, testado e
commitado. A exceção é o **B3**, que eu **recomendei não fazer** e não fiz (§7.3). Os 9 itens são
bloqueadores do `bloqueios.json` que o cartão T12 não incluiu (§12.1).

**Sim, rodei código — e o critério desta campanha foi justamente esse: nada foi aceito por
leitura.** Segue o inventário exato do que rodou e o que deu.

**Suíte de testes** — `<PY> -m unittest discover -s tests`, o interpretador por caminho completo:

| momento | resultado |
|---|---|
| baseline (antes de tocar em nada) | **Ran 627 · OK (skipped=30)** |
| após T12 completo | **Ran 671 · OK (skipped=31)** |
| após T13-B e T13-C | **Ran 688 · OK (skipped=31)** |
| revalidação após a queda de internet | **Ran 688 · OK (skipped=31)** |

**+61 testes novos**, todos com controle negativo embutido.

**Controles negativos — cada fix rodado contra o fonte PRÉ-fix, e a reprovação registrada:**

| item | o que o teste disse contra o código de ontem |
|---|---|
| T12.1 `pmid_ids` | `AssertionError: [-1, -1, -1, -1] != [2, 6, 10, 14]` |
| T12.2 `flag_vetores` | 2 falhas + 2 erros (`unexpectedly None`) |
| T12.3 `y_treino_dist` | `KeyError: 'classe_melhor'` em 3 testes + 1 falha |
| T12.4 finalProbe | `AssertionError: 3 not found in [1, 2]` (4 falhas + 2 erros) |
| T12.6 pin scipy | 1 falha + 1 erro (`não é EXATO`) |
| T12.8 BL-04/BL-15 | 5 falhas + 1 erro |
| T13-B4 pin numpy | `KeyError: 'numpy'` + `'numpy>=2,<3'` não é exato |
| T13-B1 piso | **0/381** linhas com o campo (contra 381/381 depois) |

**Runs REAIS de célula (11 execuções, todas em tempdir — nada escreveu em `data/experiments`):**

| célula | custo | o que provou |
|---|---|---|
| `main/c217/MMF1/42` (MATLAB) ×2 | 19 s cada | `pmid_ids` **426/426 com id ≥ 0** (era 426/426 = −1); `y_treino_dist` 42/42 com `n=|TrainIn|≠|Input|`; `params` com as 3 chaves corrigidas |
| `off/b5m/DTLZ2/42` | 2.808 s | flag **381/381 não-nula** (era 0/1.144); célula SADIA (Σ 7.769 substituições) |
| `off/b5m/DTLZ3/42` | 2.736 s | **105/105 vetores colapsados em 381/381 gerações**, `P_wrong ≡ 0`, 0 substituições |
| `off/b5m/DTLZ1/42` | 2.704 s | **o ONSET**: g1–11 sadias com 1.042–1.093 subs/ger.; **g12** 105/105 colapsados e 0 subs |
| `off/moead_media/DTLZ1/42` | 46 s | piso colapsa **14 de 105**, onset g12 |
| `off/moead_media/DTLZ3/42` | 53 s | piso colapsa **1 de 105**, onset g2 |
| `off/moead_media/DTLZ1/42` (pré-fix) | 46 s | controle negativo: **0/381** com o campo |
| `main/c122/MMF1/42` | 52 s | **11.000/11.000** linhas com `pred_score` (era `mu_0` com `pred_score` NULL) |
| `main/c154` + `main/c262` MMF1/42 ×3 | ~40 s | **bit-identidade ①②③** pré×pós, com controle de que ④ varia entre 2 runs do MESMO código |
| `main/c217/MMF1/42` (host) | 19 s | ⑤ MATLAB com `host`/`plataforma` |

**Bancadas MATLAB medidas** (R2025a local): `exist('fflush') = 0`; 1 linha de 64 B sobrevive a
`kill -9`; splice com 4 escritores × 300 linhas de 6,4 KB = `fprintf` **30 partidas**, `fwrite`
**26**, Java append **0**; 5 repetições com bytes SEMPRE 7.765.968 e newlines SEMPRE 1.200.

**Gates da casa:** 6/6 portões de proveniência **verdes** no ⑤ com as chaves novas
(`G-1 3x1`, `G-2 sexto`, `G-3 proveniência`, `G-4 camadas`, `G-7 contrato61`, `B-15 O-22`).
`scripts/staleness.py` → **STALE: 0**. Driver: `LOTE_MAQ=vm7 LOTE_SEEDS="0 1" LOTE_PARES=todos`
derivou as **695 células** numa máquina desconhecida.

### (2) O relatório detalhado

É este documento inteiro. A tabela suprema está no **§2**; o detalhe por item no **§5**; os erros
no **§9**; as lições no **§10**; o estado das validações no **§11**.

### (3) Existem definições em aberto?

**Sim — 8.** Estão no **§12**, com o que cada uma custa e a minha recomendação. As mais urgentes:
os **9 bloqueadores nunca tratados** (§12.1), o **provisionamento dos venvs nas 8 máquinas novas**
(§12.2) e o **mapa semente→máquina** (§12.3).

---

## §2 · A TABELA SUPREMA

Todos os itens das três frentes, na ordem em que foram executados.

| # | item | o que era | status | prova (medida) | commit |
|---|---|---|---|---|---|
| 0 | Bootstrap | cartão, regras, baseline, descoberta do MATLAB local | ✅ | suíte 627 OK | — |
| 1 | **T12.1 · BL-01** | `pmid_ids` = −1 em 426/426 (Pmid tem D+1 colunas) | ✅ | **426/426 com id ≥ 0** (min 0, máx 59) | `f524bc4` |
| 2 | **T12.2 · BL-02** | flag não-nula em 0/1.144 (lia o `problem`, não o evolver) | ✅ | **381/381 não-nula** | `2a28e02` |
| 3 | **T12.3 · BL-05** | `y_treino_dist` = (0,0,n) em 42/42 | ✅ | 42/42 com `n=|TrainIn| ≠ |Input|` | `79c9282` |
| 4 | **T12.4 · BL-06** | sob teto, a última iteração ficava sem bloco de sonda | ✅ | bloco na iteração truncada; ①②③ bit-idênticas | `c9969a0` |
| 5 | **T12.5 · BL-09** | pedia `fflush` — que não existe no MATLAB | ⚠ medido, **não aplicado** | perda REFUTADA; splice CONFIRMADO | `a4e6ef8` |
| 6 | **T12.6 · BL-08** | `scipy` sem pin | ✅ | pin × 3 artefatos + sha256 do lote de Owen | `219bcba` |
| 7 | **T12.7 · BL-16** | gates aferiam texto do fonte | ✅ **achou o BL-03** | **11.000/11.000** com `pred_score` | `8acff69` |
| 8 | **T12.8** | varredura de VALOR dos campos T11 | ✅ **achou BL-04 e BL-15** | ⑤ do c217 com 3 chaves corrigidas | `d17644a` |
| 9 | **T12.D2 · BL-10** | contradição N=20 (DI-32/A2 × DI-39) | ✅ decidido | 3 textos varridos + PARTE A41 | `a81608d` |
| 10 | T12.F | handoff do T12 | ✅ | — | `d7ef653` |
| 11 | **T12.D1 · BL-07** | piso de ruído entre máquinas | ✅ **decidido pelo autor** | diluição por semente (§4.4) | `e3368af` |
| 12 | **T13-B4** | `numpy` solto — metade do par do BL-08 | ✅ | pin × 3 + controle negativo | `f36593e` |
| 13 | **T13-B1** | campo nunca escrito no `moead_media` | ✅ | piso colapsa **parcialmente** (14/105) | `f36593e` |
| 14 | **T13-B2** | flag constante nas 381 gerações | ✅ | **onset na geração 12** medido | `f36593e` |
| 15 | **T13-B3** | writer ⑥ do MATLAB não-atômico | ⛔ **não feito (recomendação minha)** | risco condicional, §7.3 | — |
| 16 | **T13-C1** | venv resolvido por caminho de macOS | ✅ | fallback testado; 0 regressão no Mac | `e3368af` |
| 17 | **T13-C2** | máquina não viajava com o dado | ✅ | ⑤ Python **e** MATLAB; 6/6 portões | `e3368af` |
| 18 | **T13-C3** | censo abortava em host novo | ✅ | sem `sys.exit` | `e3368af` |
| 19 | **T13-C4** | roster por config; O-16 no driver | ✅ | `vm7` derivou 695 células | `e3368af` |
| 20 | **T13-C5** | lista fechada de 4 máquinas no relatório | ✅ | deriva do disco | `e3368af` |
| 21 | **T13-C6** | — | ✅ | 13 testes de multimáquina | `e3368af` |
| 22 | **A1/A3** | REGISTRO A42 + este repasse | ✅ | — | (este commit) |

---

## §3 · A DOUTRINA — e por que ela pagou

O cartão T12 impôs duas regras, e elas são a razão de o resultado ser maior que o escopo:

1. **Todo fix exige controle negativo** — um teste que REPROVA no código de ontem e PASSA depois.
2. **Todo campo de instrumentação exige asserção sobre o VALOR medido em run real** — nunca sobre
   a existência da chave.

**O que isso rendeu:** dos 8 itens do cartão, **3 defeitos que ninguém tinha listado** apareceram
sozinhos, porque os gates passaram a medir valor em vez de texto (§4.1). E **1 bloqueador da lista
foi refutado** pela medição, evitando uma mudança que teria derrubado a campanha (§4.3).

**A assinatura de defeito que a campanha T11 deixou** — e que este cartão existia para matar — era
*"campo verde, dado sentinela"*: o campo nasce para fechar uma lacuna nomeada, entra verde, e vem
vazio. A lacuna passa de **aberta-e-visível** para **aberta-e-camuflada**, que é pior.

---

## §4 · OS ACHADOS

### §4.1 · Os 3 defeitos que a doutrina achou sozinha

**BL-03 · c122 — o score do classificador ia para a coluna do regressor.**
`emit_sonda_estratificada` não ramificava por `pred_tipo`, ao contrário da função irmã
(`emit_sonda_block`), cuja própria docstring exige: score/classe vão para `pred_score`, *"NUNCA
para mu_*/sigma_*, que significam outra coisa e envenenariam a leitura da ③ pela R4"*. Com o
default do emissor sendo `'score'` (o c122 é classificador par-a-par), o `e(z)` ia para `mu_0` e a
confiança para `sigma_0`, com `pred_score` NULL em **10.500/10.500** linhas. O guard do writer não
pegava porque `len(mu)=1 < M=2` é o caso legítimo do b1 mono-output.
**Achado no 1º disparo do gate convertido. Depois do fix: 11.000/11.000 corretas.**

**BL-04 · os 5 offline — o ⑤ publicava o tempo de INGESTÃO como custo de avaliar.**
A carga do dataset empurra as n linhas do artefato pelo portão de avaliação (para atribuir
`solution_id` — D57 — e esgotar o orçamento — D90), e o cronômetro do I-02 contava aquilo:
**0,0003 s** medido no b5m/DTLZ2. Na s42 era `0.0` exato — o I-02 trocou um número errado por
outro. O fix zera relógio **e contador**: zerar só o relógio devolveria `0.0`, que é a afirmação
*"avaliar custou zero"* — o sentinela que o I-02 nasceu para matar. Offline agora publica **NULL**.

**BL-15 · o `params` do ⑤ do c217 — 3 afirmações falsas.** Não era sentinela: era erro declarado,
que é pior. O §15.7 manda o validador cruzar o `params` com o paper, e para o c217 isso devolvia
*"confere, 20/20"* — falso **nas duas direções** (o stock roda `{1,15,1,5}` e a SPEC §567 diz que
Balde C não se aplica). Também `treino` dizia "do arquivo" (vem da POPULAÇÃO) e `surrogate` dizia
alvo ternário (é BINÁRIO `{1,2}`).

### §4.2 · A cadeia A8, medida em célula real pela primeira vez

O `flag_vetores_degenerados` era o campo que a F5 pediu para fechar o laço do congelamento do b5m
e que a T11 entregou morto (`None` em 1.144/1.144, `AttributeError` engolido pelo `except`). Com o
fix — os vetores vivem no **evolver** (`BaseEA.py:182`), e o `desdeo_problem` vendorizado tem
**zero** ocorrências do atributo — a cadeia inteira virou leitura direta do ⑥:

| célula | `n_norma_zero` | normas | `n_substituicoes` | onset |
|---|---|---|---|---|
| `b5m/DTLZ2` (SADIA) | 0 em 381/381 | ≈ 1,0 | 3–12/ger. (**Σ 7.769**) | — |
| `b5m/DTLZ3` (CONGELADA TOTAL) | **105 de 105** em 381/381 | 0,0 | **0** | g1 |
| `b5m/DTLZ1` (ONSET) | 0 → **105 de 105** | 1,0 → 0,0 | **10.479 antes, 0 depois** | **g12** |
| `moead_media/DTLZ1` (PISO) | 0 → **14 de 105** | amplitude 1,0 | — | **g12** |
| `moead_media/DTLZ3` (PISO) | 0 → **1 de 105** | amplitude 1,0 | — | **g2** |

**O resultado científico:** o piso **também** colapsa — mas só **parcialmente** (14/105 e 1/105),
contra o colapso **TOTAL** do b5m (105/105). **O achado do b5m sobrevive ao contraste da ablação**:
o congelamento total é específico da maquinaria probabilística, não comum aos dois. Isso só é
afirmável porque o B1 escreveu o campo no piso — antes, a pergunta era **inrespondível**, e a
resposta não era recuperável a posteriori (os vetores são estado interno do evolver).

**Fecha também o BL-22** (o smoke da célula congelada do b5m, que nunca existira).

### §4.3 · O bloqueio que NÃO sobreviveu à medição (BL-09)

O engine MATLAB estava disponível, então os dois modos de perda foram medidos:

1. **`fflush` NÃO EXISTE no MATLAB** (`exist('fflush') = 0`). O `jsonl_line` **não tem
   `try/catch`** — a "1 linha" prescrita **derrubaria todo run MATLAB da campanha**. É do Octave.
2. **Perda de cauda: REFUTADA.** Uma linha de 64 B sobrevive a `kill -9`.
3. **SPLICE: CONFIRMADO, e o fix é ATOMICIDADE, não flush.** `fprintf` 30 partidas · `fwrite` 26 ·
   `java.io.FileOutputStream` **0**. Bytes e newlines SEMPRE exatos — **nada se perde**; o que
   quebra é a fronteira da linha.

**Se eu tivesse aplicado o que o bloqueio pedia, a campanha inteira do stack MATLAB teria morrido
no primeiro run.**

### §4.4 · O piso de ruído (BL-07) — resolvido por desenho

Medição nos 15 pares Mac×vm3: **7 bit-idênticos** (Δ = 0,0 — os 4 pisos puros + b4 + c217 + e103,
isto é, exatamente os configs que **não** ajustam surrogate por otimização numérica) e **8
divergentes**, **6 acima do piso O-18 (HV ≤1,55%)**. Em **IGD+ — o endpoint PRIMÁRIO (D70) — o
piso declarado nem existe**, e é lá que está o pior número: `c238/MMF1` **80,03%**.

**A decisão do autor:** cada máquina roda TODOS os experimentos em algumas sementes; a mediana das
30 dilui. **Isso resolve, e resolve por inversão de regime:** sob a O-16 a máquina era CONSTANTE
nas 30 sementes de um config — um offset sistemático que nenhuma média dilui. Alocando por
semente, a máquina varia DENTRO do config entre repetições, vira ruído aleatório, e a mediana faz
o trabalho. **Média dilui ruído aleatório, não viés** — e a decisão troca um pelo outro.

---

## §5 · DETALHE POR ITEM

### T12.1 · `pmid_ids` (BL-01)
`CalFitnessPC.m:67-68` monta `Input = [PopDec, Fitness]` e `:73` recorta o `Pmid` dele — **D+1
colunas**. `FEBudget.solutionIdOf` casa o X nativo bit-a-bit em `8*D` bytes (D89/D57), então a
chave de `8*(D+1)` bytes nunca existia no keymap. **Fix:** `Pmid(i, 1:D)` — a mesma fatia que o
`fe_treino_max` já aplicava ao `TrainIn` (:32), 169 linhas acima, no mesmo arquivo.
**Teste:** `tests/test_t12_c217_instrument.py` executa o `c217_instrument.m` em **MATLAB real**
(`FEBudget`/`RunBuffer` reais, `Pmid` com a largura do stock) + **mutante** que é o mesmo fonte
com a expressão de ontem.

### T12.2 · `flag_vetores_degenerados` (BL-02)
Lia `evolver.population.problem.reference_vectors` — o `problem` do DESDEO **nunca teve** o
atributo (0 ocorrências no vendorizado). **Fix:** `evolver.reference_vectors`.
**Teste:** roda a cadeia A8 sobre a classe `ReferenceVectors` **VENDORIZADA de verdade** —
`adapt` com fitness constante → norma 0 em 15/15; com UM objetivo constante → colapso **PARCIAL**
1/15, o único cenário com amplitude > 0.

### T12.3 · `y_treino_dist` (BL-05)
Dois defeitos: (i) contava `y<0`/`y==0`/`y>0` supondo alvo ternário, mas o `Output` é **binário
{1,2}** (`CalFitnessPC.m:69-71`) ⇒ `(0,0,n)` invariante; (ii) media o `Input` inteiro, não o
`TrainIn` que o nome promete. **Fix:** derivação do `TrainOut` (descartado em `PCSAEA.m:41`, mas
determinístico — `DataProcess.m:14-21` mantém ceil(3/4) de cada estrato) + o campo
`confere_com_TrainIn`, que publica o próprio controle.

### T12.4 · finalProbe sob teto (BL-06)
**Não era 1 linha.** No ponto do `break` o modelo já morrera no `del` da higiene de memória (D86).
O `del`/`iteration_cleanup` desceram para DEPOIS do teto — e nada mais mudou de ordem, porque
`_WallClockProjector.exceeded` aborta **só por `elapsed`** desde a DI-43, então o instante do
truncamento não se move. **Bit-identidade:** ①②③ byte-idênticas pré×pós nos 2 configs; a ④ difere
— e o **controle** mostra que ela difere também entre 2 execuções do MESMO código (são wall-times).

### T12.5 · BL-09 → §4.3.

### T12.6 / T13-B4 · o par `numpy`+`scipy` (BL-08)
O lote do `sobol_batch` é Sobol com randomização de **Owen** do `scipy.stats.qmc`
(`src/sobol_batch.py:72-73`). A bit-identidade vale **só sob `numpy 2.4.6` E `scipy 1.17.1` nos
dois lados**. Pinados nos **3** artefatos (`envs.json`, `repos.lock`, `requirements/env_main.txt`)
— um pin em 2 de 3 dá falsa segurança. **O gate não afere a linha no artefato**: casa os 3 entre
si, casa com o **instalado** (muda de resposta em cada máquina) e trava o **sha256 do lote**.

### T12.7 · gates texto→comportamento (BL-16) → §4.1 (BL-03).
Também convertidos: o `meta` do `emit_sonda_block` é aferido no EVENTO (não na assinatura); a
não-perturbação de RNG é aferida no **ESTADO** do numpy/random (não no texto do `with`); o gancho
do mode 12 casa o **objeto** (`mod.MOEAD_select is MOEAD_select`, e **não** o probabilístico) e
constrói uma `Population` vendorizada real.

### T12.8 · varredura de VALOR → §4.1 (BL-04, BL-15).

### T12.D2 · N=20 (BL-10)
A **DI-39** (2026-07-25, posterior) prevalece sobre a **DI-32/A2**: N=20 é **provisório** e o
**SUB-varN é pré-requisito do M8**. 3 textos varridos — e a epígrafe do bundle foi corrigida
**no `gen_bundles.py` que a gera**, porque o bundle é GERADO e corrigir só o `.md` seria desfeito.

### T13-B1/B2 → §4.2. · T13-C1..C6 → §6.

---

## §6 · O QUE MUDOU PARA AS 9 MÁQUINAS (T13-C)

| item | o que estava embutido | o que mudou |
|---|---|---|
| **C1** | `interpreter_for_alg` resolvia por caminho ABSOLUTO de macOS. Os 6 configs de venv próprio **nunca rodaram fora do Mac** — o driver dizia isso: *"mac: TODO o venv-próprio — únicos venvs do projeto"* | resolve por CANDIDATOS pelo **NOME** do venv (a identidade que o gate G-3 já usa). Override `UA_DD_SAEA_VENVS`. Sem candidato, devolve o DECLARADO para a mensagem ser acionável |
| **C2** | **zero** ocorrências de `gethostname`/`uname` em `src/`; a única atribuição era `maquina_dona`, DERIVADA do roster | `host` + `plataforma` nos 3 writers de ⑤; arquitetura normalizada no MATLAB (`maca64`→`arm64`); `UA_DD_SAEA_HOST` rotula com o nome do roster |
| **C3** | lista fechada de 4 + `sys.exit` em host novo | o próprio host vira o rótulo (derivado, não planejado) |
| **C4** | roster por config; a O-16 escrita como "Regra de ouro" no driver | `LOTE_PARES=todos` deriva do ARTEFATO; **O-16 aposentada no texto** |
| **C5** | `MAQS = ["mac","v5","v6","vm3"]` | deriva do disco, com fallback e `MAQS=` no ambiente |

**Detalhe prático que a torre precisa levar ao autor:** **VM5 e VM6 são Python-only**, então
*"cada máquina roda TODOS os experimentos"* tem exceção — os 13 configs MATLAB não rodam lá. Na
prática o mapa semente→máquina são **dois** mapas (MATLAB em 7 máquinas, Python em 9). Não
compromete a diluição; muda o planejamento.

---

## §7 · O QUE **NÃO** FOI FEITO, E POR QUÊ

### §7.1 · Fora do cartão (D81) — 9 bloqueadores
Ver **§12.1**. Não os fiz porque o protocolo manda parar no limite do cartão.

### §7.2 · `moead_media` no T12 — virou T13-B1
No T12 eu **parei e perguntei**, porque acrescentar chave ao ⑥ de um config com contrato fechado é
item novo, não conserto. O autor autorizou depois, e foi feito — e rendeu o contraste do §4.2.

### §7.3 · B3 · o writer ⑥ do MATLAB atômico — **recomendação de NÃO fazer**
O splice é real (§4.3), mas exige ≥2 escritores no mesmo ⑥, e **hoje o ⑥ do MATLAB tem escritor
único**: o `experiments.py` despacha só o roster Python e os workers de `parfor` escrevem células
distintas. **A alocação por semente não aumenta esse risco** — cada semente é um arquivo distinto.
Trocar o writer dos 13 configs MATLAB (o `jsonl_line` + 18 `fprintf(fid,…)` diretos nos
`*_instrument.m`) na véspera da tag custa mais do que o risco que remove.
**Caminho pronto se o autor quiser:** `jsonl_write(fid, linha)` com
`java.io.FileOutputStream(fopen(fid), true)` — o `fid` continua sendo a identidade que os 19
sítios já passam, e todos os guards `fid > 2` seguem valendo.
⚠ O comentário do `jsonl_open` (B-11) descreve um co-escritor Python *"durante a chamada MATLAB"*
que **não existe na arquitetura de hoje** — vale corrigir junto (armadilha doc×código).

---

## §8 · UM DEFEITO PRÉ-EXISTENTE QUE FICOU VISÍVEL

Um run REAL de c262 no MESMO processo em que já rodou
`tests/test_batch_q10.py::TestCalibracaoBatchT9::test_c154_call_site_usa_o_helper_nao_hardcode`
morre com `ValueError: torch.cat(): expected a non-empty list of Tensors` dentro do
`optimize_acqf`. Aquele teste faz `mock.patch` em `botorch.optim.optimize_acqf` e em
`gen_batch_initial_conditions`.

**Reproduzido com o fix do BL-06 desfeito ⇒ NÃO é desta campanha.** Ficou visível porque este é o
primeiro cartão a rodar célula real dentro da suíte. **Risco para a campanha: nenhum** (1 célula =
1 processo). **Mitigação adotada:** todo teste que roda célula real vai em **subprocesso** — é a
regra que produziu os smokes do T11 (*"1 por vez, em processo próprio — `torch.set_default_dtype`
é global"*) e é como a campanha roda.

---

## §9 · O QUE FIZEMOS ERRADO (e custou tempo)

Registro honesto, porque a próxima sessão herda estes erros se eu não os escrever.

1. **Caí numa armadilha do catálogo da própria casa.** O `T11-PROMPT-SESSAO.md §4` avisa:
   *"zsh não faz word-splitting de `$var` sem aspas"*. Usei `$H1` sem array num bisect e o zsh
   passou a lista inteira como **um** argumento — 3 rodadas de bisect com resultado sem sentido
   (`Ran 13 tests`) antes de eu perceber. **Custo: ~15 min.** Lição: em zsh, sempre array.
2. **Tirei conclusão de um resultado negativo numa corrida, sem repetir.** A primeira medição de
   splice no scratchpad deu **0 partidas** e eu escrevi *"o BL-09 não se sustenta"*. Era sorte: o
   mesmo cenário com o writer de produção dá 10/18/12/26/30. **Custo: quase entrou um veredito
   errado no cartão.** Lição: resultado negativo em teste de corrida **exige repetição**.
3. **Escolhi a célula de smoke antes de ler o relatório do config.** Rodei `b5m/DTLZ2` (47 min)
   esperando o congelamento A8 — o DTLZ2 é célula **sadia**; as congeladas são DTLZ3 e DTLZ1, e o
   `f5/t11/relatorios_config/b5m.md` já dizia isso. **Custo: ~47 min.** Lição: o relatório do
   config escolhe a célula, não a intuição. (O autor reforçou depois: **sempre a mais barata que
   entregue o mesmo poder de prova** — aplicado no B1, onde `moead_media` a 46 s substituiu o que
   eu ia rodar em 45 min.)
4. **Entreguei um teste instável.** O de perda de linha exigia 4 MATLABs simultâneos e, sob a carga
   da suíte cheia, media o **arranque do engine**, não o writer — a suíte ficou vermelha uma vez.
   Removi e substituí pela medição estável. Lição: teste que sobe processo externo pesado tem de
   **pular** em falha de ambiente, não reprovar.
5. **Escrevi um teste no nível errado.** Afirmei `is_run_done` sobre um manifesto sintético fino;
   ele exige campanha, `fe_final == maxfe`, camadas e footers. Corrigi para aferir a **chave de
   busca**, que é onde o risco mora.
6. **Dois erros pequenos de mecânica:** regex `OperatorGA\([^)]*\{` quebrou por `)` aninhado; o
   bloco `LOTE_PARES=todos` ficou antes do `cd "$REPO"`. Ambos pegos no primeiro teste.

---

## §10 · O QUE APRENDEMOS (reutilizável)

1. **Converter um gate de texto para comportamento acha defeito no primeiro disparo.** Aconteceu
   literalmente: o BL-03 caiu no primeiro `unittest` depois da conversão.
2. **Medir antes de prescrever.** O BL-09 pedia uma função que não existe; aplicá-la teria matado a
   campanha. Um bloqueador é uma hipótese até ser medido.
3. **O dado ganha do cartão.** O cartão dizia que o congelamento estava no DTLZ2; estava no
   DTLZ3/DTLZ1. Seguir o cartão contra o dado teria produzido um "controle positivo" vazio.
4. **Corrigir o gerador, não o gerado.** A epígrafe do bundle vive no `gen_bundles.py`; corrigir só
   o `.md` seria desfeito na próxima regeneração.
5. **Bit-identidade precisa de controle.** A ④ diferia pré×pós e parecia regressão — só o controle
   (2 execuções do MESMO código) mostrou que ela **sempre** difere: carrega wall-times.
6. **Zerar um relógio não é o mesmo que declarar "não medi".** No BL-04, zerar só o relógio
   devolveria `0.0` = *"avaliar custou zero"*, que é o sentinela original com outra roupa. Era
   preciso zerar o **contador** para a property voltar a NULL.
7. **Média dilui ruído aleatório, não viés.** É o eixo de toda a decisão do piso: a mesma
   estatística salva ou não salva conforme a máquina seja constante ou variável dentro do config.
8. **Run real vai em subprocesso.** Estado global de torch/BoTorch atravessa testes.

---

## §11 · ESTADO ATUAL DAS VALIDAÇÕES

| validação | comando | resultado |
|---|---|---|
| Suíte | `<PY> -m unittest discover -s tests` | **Ran 688 · OK (skipped=31)** |
| Staleness | `<PY> scripts/staleness.py` | **STALE: 0** |
| Portões de proveniência | `gates_proveniencia` sobre smoke real | **6/6 OK** |
| Bit-identidade ①②③ | pré×pós em c154 e c262 | **idênticas** (com controle na ④) |
| Driver multimáquina | `LOTE_MAQ=vm7 … LOTE_PARES=todos` | **695 células derivadas** |
| Escrita em `data/experiments` | — | **nenhuma** (tudo em tempdir) |
| `git push` | — | **nenhum** (proibição da casa) |

**Testes novos (61), todos com controle negativo:**

| arquivo | tranca |
|---|---|
| `tests/test_t12_c217_instrument.py` | `c217_instrument.m` em MATLAB real + 2 mutantes |
| `tests/test_t12_b5_vetores.py` | cadeia A8 na classe `ReferenceVectors` vendorizada |
| `tests/test_t12_teto_sonda.py` | célula c154/c262 real truncada (subprocesso) |
| `tests/test_t12_jsonl_matlab.py` | writer ⑥ real: `fflush` ausente, durabilidade, atomicidade |
| `tests/test_t12_pin_scipy.py` | o PAR numpy+scipy × 3 artefatos + sha256 do lote de Owen |
| `tests/test_t12_valores_t11.py` | `tempo_aval_real_s`, `params` do c217, `n_front1`, `repo_hash` |
| `tests/test_t13_serie_vetores.py` | a série por geração nos 2 módulos gêmeos |
| `tests/test_t13_multimaquina.py` | venv por máquina, host no ⑤, censo, alocação por semente |
| (convertidos) `test_a2_c122.py`, `test_piso_off.py` | de texto para comportamento |

⚠ Testes MATLAB **pulam limpo** onde não há engine; os de célula real rodam em **subprocesso**.
**Rodar a suíte nas VMs Linux RE-MEDE** as propriedades dependentes de plataforma (§4.3): se a
libc de lá bufferizar, o BL-09 volta — agora com o fix certo já identificado.

---

## §12 · AS DEFINIÇÕES EM ABERTO — a torre precisa levantar estas com o autor

### §12.1 · 🔴 NOVE bloqueadores do `bloqueios.json` nunca tratados
O cartão T12 cobriu 13 dos 22. Ficaram **fora do cartão e sem tratamento** — e são todos baratos:

| id | o quê | custo |
|---|---|---|
| **BL-11** | `treed_media`: I/O do checkpoint dentro de `tempo_busca_s`/`tempo_geracao_s` | 1–2 linhas |
| **BL-12** | b4: os 3 números de calibração da `REGRA_DO_ROTULO` não reproduzem em corpus nenhum | ~20 min |
| **BL-13** | `geracoes_derivadas` declara o operador do NSGA-II para os 4 pisos (moead/smsemoa usam `OperatorGAhalf`) | 1 edição |
| **BL-14** | `frente1_excede_pop` compara com `N_nominal` em vez de `N_efetivo` (difere em M=3) | 1 token |
| **BL-17** | `contrato_61.json` não cobre a linha "pisos" do CONTRATO §6.1 | 1 linha × 4 |
| **BL-18** | e103: `espaco_modelo` NULL na busca e `'cru'` na sonda, na MESMA ③ | 1 literal |
| **BL-19** | b4: 2 das 3 edições de doc que a F5.4 pediu (convenção `p0`/`p1`) | ~20 min |
| **BL-20** | `sobol_batch`: `params.nota_potencia_de_2` é literal fixa afirmando `q=10` com `q=1` | 1 linha |
| **BL-21** | e81: `scripts/progress.py:95` lê `footers[-1]` em vez de `footer_fechado()` | 1 linha |

**Pergunta ao autor:** faço um cartão T14 com os 9 (estimo ~2 h com testes) antes da tag, ou eles
vão para depois do disparo? **Minha recomendação: fazer antes** — são todos de instrumentação/doc,
somam ~2 h, e o BL-14 e o BL-18 afetam o que a R4 consegue ler.

### §12.2 · 🔴 Provisionamento dos venvs nas 8 máquinas novas
O C1 tornou a **resolução** portável, mas os venvs precisam **existir**. Cada máquina precisa de
`env_main`, `env_b5`, `env_c311`, `env_e81_qpots` (+ `env_bridge` nas de MATLAB).
**O item de risco é o `env_b5`: py3.7.12 x86_64** — no Mac ele só existe via **Rosetta**, e a
`nota_mac_vm_DI11` já previa duas rotas: (a) pins vizinhos com validação de equivalência do GPR ou
(b) exceção documentada. **Não consigo validar isto daqui.** **Pergunta:** qual rota nas imagens
Linux, e quem provisiona?

### §12.3 · 🟠 O mapa semente→máquina
30 sementes, 9 máquinas — mas **VM5 e VM6 são Python-only**, então são **dois** mapas (MATLAB em 7,
Python em 9). **Pergunta:** o autor define a atribuição, ou quer que eu gere um mapa balanceado por
custo (usando os walls medidos da s42) e o publique como artefato?

### §12.4 · 🟠 A tabela de tempo do M7 sob alocação por semente
A O-16 foi aposentada **para resultado**, mas ela existia para a **tabela de TEMPO** — comparar
wall entre algoritmos exige a mesma máquina. Com alocação por semente, o wall de um config passa a
misturar 9 máquinas de 8 a 32 cores. **Pergunta:** como reportar custo computacional na
dissertação? (Opções: normalizar por máquina usando as células-calibradoras; reportar por máquina;
ou rodar a tabela de tempo num subconjunto controlado.)

### §12.5 · 🟡 O `piso_ruido.json` ainda vale?
O autor decidiu assumir o problema via diluição e disse *"não mude nada em relação a isso"* — não
fiz. Mas o piso continua útil como **régua de leitura** para os casos que furarem o desenho
(re-runs, recuperação de célula noutra máquina). E **7 dos 15 pares têm piso = 0**, o que é
informação acionável. **Pergunta:** publicar como artefato, ou deixar fora?

### §12.6 · 🟡 B3 — writer ⑥ do MATLAB atômico
Ver §7.3. **Minha recomendação: não fazer antes da tag.** **Pergunta:** o autor concorda, ou
prevê algum dos 3 cenários que o tornariam necessário?

### §12.7 · 🟡 SUB-varN antes do M8
Ratificado no T12.D2 (a DI-39 prevalece): é **pré-requisito do M8**, custo ~3,3 h-core.
**Pergunta:** quando roda?

### §12.8 · 🟡 O comentário do `jsonl_open` (B-11) descreve arquitetura que não existe
Ele fala de um co-escritor Python *"durante a chamada MATLAB"*; o `experiments.py` despacha só o
roster Python. **Pergunta:** corrijo junto do B3, ou já?

---

## §13 · COMO REPRODUZIR

```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY -m unittest discover -s tests     # esperado: Ran 688 · OK (skipped=31)
$PY scripts/staleness.py              # esperado: STALE: 0
```

Modo da campanha por semente, numa máquina qualquer:
```bash
CENSO=1 LOTE_MAQ=<nome> LOTE_SEEDS="0 1 2" LOTE_PARES=todos bash scripts/lote3s.sh
```

Os 11 commits: `f524bc4` `2a28e02` `79c9282` `c9969a0` `a4e6ef8` `219bcba` `8acff69` `d17644a`
`a81608d` `d7ef653` `f36593e` `e3368af`.

---

## §14 · PRÓXIMO PASSO

**Nada bloqueia a tag** exceto as decisões do §12. Caminho crítico até o disparo:
**§12.1 (T14, ~2 h) → §12.2 (provisionamento, infra do autor) → §12.3 (mapa) → SUB-varN → disparo.**

**Nada foi pushado.**
