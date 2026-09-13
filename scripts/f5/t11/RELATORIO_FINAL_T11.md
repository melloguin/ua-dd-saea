# RELATÓRIO FINAL — validação de fidelidade da campanha T11

**Torre central de validação de fidelidade · 2026-07-31**
**Escopo:** 24 configs · corpus de mecanismo = rodada-42 (666 células oficiais) · corpus de
instrumentação = `evidencia_T11/` (27 células: 11 smokes Python, 15 MATLAB, 9 pares g6, 1 teto)
**Doutrina:** D97 — a torre ANALISA e RECOMENDA; **o veredito é do autor.**

> **Como este documento foi produzido.** 24 agentes independentes (1 por config, ~5,8 M tokens),
> depois 11 agentes de consolidação que **tentaram refutar** os 24 vereditos e varreram as
> transversais, depois 12 agentes sobre os smokes Python. Tudo re-medido: nenhum número deste
> relatório foi copiado do handoff da T11 nem aceito de agente irmão sem conferência.

---

## 1. Veredito recomendado

**ACEITAR os 24 configs.** Nenhum config tem bug de mecanismo. A T11 **não tocou uma linha de
algoritmo** — e isso não é alegação da campanha, é medida: em **9/9 pares `g6_com`×`g6_sem`** a
camada ① sai com **sha256 idêntico**, e em 5 configs a célula da s42 reproduz **bit-a-bit** sob o
código de hoje. A rodada-42 continua sendo evidência válida do mecanismo em 23 dos 24 configs.

**Mas o saldo é menor do que os 24 relatórios sugerem, e a razão é estrutural.** A campanha
melhorou o que o pipeline **decide** e piorou o que ele **declara**: nasceu uma família inteira de
defeitos com a mesma forma — *um campo é criado para fechar uma lacuna que a auditoria nomeou,
entra verde, e o que ele carrega é sentinela*.

---

## 2. 🚨 O achado metodológico mais importante: a régua estava trincada

Antes de comparar T11 com F5 eu fui conferir a base — e ela não é única.

- `f5/scores_f53.csv` guarda os scores da **F5.3** (análise por config). É **pré-adversarial**.
- A **F5.4** rodou depois. Das 14 sentenças, várias movem score. **O CSV nunca foi atualizado** —
  a própria sentença `moead_media-C9b.md:76` escreve *"`scores_f53.csv` a atualizar"*.
- O `RELATORIO_FINAL_F5.md:129` tem uma matriz **D1** com os valores revistos — **mas ela não é
  nota homologada**: é a recomendação da torre dentro de uma decisão **aberta** de três opções,
  listada entre as 16 que bloqueiam o disparo. E a §1 do mesmo relatório continua publicando a
  matriz-mestra com os valores **pré**-adversariais.

**Consequência.** Comparar a T11 contra o CSV **credita a ela 5 achados que a F5.4 já havia
resolvido sem uma linha de código** (`b4-A12`, `c154-J27`, `moead-M16`, `moead_media-C9b`,
`e103-A25` — ganhos de contraditório, não de refinamento). Comparar contra a D1 embute como fato
4 movimentos que a evidência primária não consuma: `b4` e `c149` são *"recomendo / merece
revisão"* (PROPOSTO), `b5r` é *"sobe para 10 **apenas se** o autor aceitar"* e devolve uma faixa
9,5–10 (CONDICIONAL), e `e103` **sequer enuncia número novo** — o 9,8 é aritmética da torre.

**Base honesta = a híbrida:** adotar o valor pós-adversarial **só nos 3 movimentos APLICADOS na
própria sentença** (`c154` 9,0 · `moead` 10,0 · `moead_media` 9,5) e exibir os 4
PROPOSTOS/CONDICIONAIS como par *"CSV → pendente-D1"* até o autor decidir.

| base usada | média F5 | média T11 | Δ | melhorou / manteve / piorou |
|---|:--:|:--:|:--:|:--:|
| CSV pré-adversarial (otimista) | 9,325 | 9,483 | **+0,158** | 12 / 11 / 1 |
| **híbrida (recomendada)** | **9,408** | **9,483** | **+0,075** | **10 / 11 / 3** |
| D1 integral (pessimista) | 9,492 | 9,483 | −0,008 | 7 / 12 / 5 |

**A leitura correta:** a T11 entregou um ganho **real, pequeno e concentrado**. Não foi o salto
que os relatórios individuais descrevem — parte do que eles chamaram de melhora já tinha sido
paga pela F5.4.

---

## 3. A TABELA COMPARATIVA

Base híbrida. ⚠ marca os 4 configs cuja posição depende da decisão D1 do autor.

| config | F5 | T11 | Δ | veredito | causa dominante (verificada) |
|---|:--:|:--:|:--:|---|---|
| **b3** | 9,6 | **9,8** | +0,2 | 🔼 MELHOROU | 2 tetos T fechados com dado (U5 · ramo `UpdataArchive` discriminado célula a célula) |
| **c262** | 9,5 | **9,7** | +0,2 | 🔼 MELHOROU | `acqf_hp` 10 campos + `params` no ⑤ byte a byte; I-12 virou contrato legível |
| **e81** | 9,5 | **9,7** | +0,2 | 🔼 MELHOROU | B28 fechado nas 2 barreiras; par pré×pós bit-idêntico em ①②③ |
| **b1** | 9,4 | **9,6** | +0,2 | 🔼 MELHOROU | par G-6 fecha U5; WFG1 volta ao denominador (+443 iterações) |
| **e74** | 9,0 | **9,5** | +0,5 | 🔼 MELHOROU | **DI-45: argmax 12,23% → 86,89%** (recomputado do zero nos 2 corpora) |
| **sobol_batch** | 9,0 | **9,5** | +0,5 | 🔼 MELHOROU | 3 classe-(3) fechados; bit-identidade ①②④ pré×pós em 5/5, outra máquina |
| **b5m** | 8,0 | **8,5** | +0,5 | 🔼 MELHOROU | `p_wrong_stats` 800/801 reconciliado; A8 provada elo a elo em bancada |
| **b4** ⚠ | 9,0→9,5? | 9,5 | +0,5 / 0 | 🔼/⏸ | único (3) caiu; `ref_ids` real. **A F5.4 já havia refutado o A12** → dupla contagem |
| **c149** ⚠ | 9,0→9,5? | 9,5 | +0,5 / 0 | 🔼/⏸ | trava de colisão de blob; A22 99,7%→100%. **Mesma dupla contagem** |
| **e103** ⚠ | 9,3→9,8? | 9,5 | +0,2 / **−0,3** | 🔼/🔽 | ⑦ regerada 45/45. **Se a D1 valer, o veredito INVERTE para PIOROU** |
| **c154** | 8,5→**9,0** | 9,0 | **0** | ⏸ MANTEVE | J27 já refutado pela F5.4; o rito de teto é ganho real mas não move a nota |
| e7 · nsga2 · nsga3 · smsemoa | 10 | 10 | 0 | ⏸ MANTEVE | teto da régua; evidência estritamente maior (tetos T caem, mecanismo idêntico) |
| c122 | 9,5 | 9,5 | 0 | ⏸ MANTEVE | +`ref_ids` real e AUC medível · −defeito novo de contrato na ③ |
| c141 | 9,5 | 9,5 | 0 | ⏸ MANTEVE | nenhum arquivo do config tocado pela T11; U11 sai do teto |
| c238 | 9,5 | 9,5 | 0 | ⏸ MANTEVE | +T1 sai do teto (27 campos do ⑥ com Δ=0,0) · −kriging degenera em 3/25 |
| c311 | 9,5 | 9,5 | 0 | ⏸ MANTEVE | +2 tetos caem (fórmula do early-stop 94,9%; determinismo bit-a-bit) |
| treed_media | 9,5 | 9,5 | 0 | ⏸ MANTEVE† | +A18 determinística · −**2 classe-(3) nascidos na T11** |
| **b5r** ⚠ | 9,0→9,5? | 9,0 | 0 / **−0,5** | ⏸/🔽 | +4 itens fechados · −2 (3) novos (`flag_vetores_degenerados` sentinela) |
| **moead_media** | 9,0→**9,5** | 9,3 | **−0,2** | 🔽 **PIOROU** | `tempo_aval_real_s` mede ingestão no offline, 22,2× fora de escala |
| **moead** | 9,0→**10,0** | 9,0 | **−1,0** | 🔽 **PIOROU** | F5.4 refutou M16 e levou a 10; a T11 trouxe 2 (3) novos e devolveu o ponto |
| **c217** | 9,5 | **9,0** | **−0,5** | 🔽 **PIOROU** | **3 classe-(3), todos da instrumentação que a própria T11 escreveu** |

† o verificador não refuta nenhuma medição do `treed_media` — refuta a **nota**: o relatório
declara ele mesmo "0 → 2 aspectos classe (3), ambos nascidos na T11" e mantém 9,5.

### 3.1 A verificação adversarial derrubou 8 dos 24 vereditos

E o modo de falha é **um só: dupla contagem**. Sete dos oito agentes partiram da base
pré-adversarial e somaram de novo, como mérito da T11, o crédito que a F5.4 já havia dado.

| config | alegou | corrigido | por quê |
|---|---|---|---|
| b4 | MELHOROU | **MANTEVE** | o degrau 9,0→9,5 tem a mesma causa que a F5.4 já consumou |
| c149 | MELHOROU | **MANTEVE** | idem — parte de "Prior F5: 9,0" que a D1 já corrigira |
| c154 | MELHOROU | **MANTEVE** | as correções são reais e confirmadas, mas o crédito já fora pago |
| e103 | MELHOROU | **PIOROU** | inverte: 9,5 − 9,8 = −0,3 |
| moead | MANTEVE | **PIOROU** | usou 9,0 *sabendo* que M16 aplicara 10,0 — cita a subida no próprio texto |
| moead_media | MANTEVE | **PIOROU** | usou a base certa (9,5) e rotulou −0,2 como "manteve" |
| b5r | MANTEVE | **PIOROU** | nunca declara a base; "manteve" só fecha contra 9,0 |
| treed_media | MANTEVE | MANTEVE | nota contestada, não o veredito |

---

## 4. O que a T11 QUEBROU — a assinatura da campanha

**14 regressões**, todas verificadas por medição minha. Elas têm a mesma forma, e o arquétipo é o
c217: *o campo entrou verde e veio vazio; a lacuna continua aberta e agora está camuflada.*

| tipo | config(s) | o que medi |
|---|---|---|
| **campo sentinela** | c217 | `pmid_ids`: **426/426 = −1**, ids distintos = `[-1]`. Criado exatamente para fechar a lacuna que eu nomeei na F5 |
| **campo sentinela** | b5r · b5m | `flag_vetores_degenerados`: presente em **1.144/1.144**, não-nulo em **0/1.144** (b5r) e 801/801 (b5m) — ramo morto, lê o atributo no objeto errado |
| **declaração falsa** | c217 | `y_treino_dist` conta alvo ternário `{−1,0,+1}` sobre vetor que só tem `{1,2}`: `(0,0,n)` em **42/42** |
| **declaração falsa** | c217 | `params.operadores` declara Balde C 20/20 onde a SPEC §567 escreve *"não se aplica"* e o código roda `{1,15,1,5}` — **converteu desvio sancionado em falsa conformidade com o paper** |
| **semântica trocada** | os 5 offline Python | `tempo_aval_real_s` passou a medir **ingestão do dataset**, contra a docstring que justifica o campo. Na s42 era 0,0 exato em **200/200** manifestos |
| **semântica trocada** | c122 | sonda estratificada grava `e(z)` em `mu_0` e max-softmax em `sigma_0`, `pred_score` NULL — **10.500/10.500 linhas** contra o próprio `sigma_dict` |
| **semântica trocada** | treed_media + todo runner com DI-43 | I/O do checkpoint atômico cronometrado **dentro** de `tempo_busca_s`: 3,27 s → 6,97 s (**2,13×**) na mesma célula |
| **declaração falsa** | moead · nsga2/3 · smsemoa | `geracoes_derivadas`: trocou fórmula errada por redação honesta **com mecanismo falso** para M=3 |
| **declaração falsa** | sobol_batch | `params.nota_potencia_de_2` fala de `q=10` num run com `q=1` |
| **lacuna do rito** | c154 · c262 | sob `teto_wall` o finalProbe não roda: última geração sem bloco de sonda (76 blocos, último em g=150 de 151) |

### 4.1 A regressão de segunda ordem — por que tudo isto passou

**O gate é decorativo: testa TEXTO, não COMPORTAMENTO.** É o modo dominante e explica sozinho por
que estes defeitos sobreviveram a uma campanha inteira com 6 portões verdes:

- `tests/test_g7_instrumentacao.py:118-127` faz `assertNotIn("tempo_aval_real_s=0.0", src)` sobre
  o **fonte** de 5 arquivos — e nunca roda um offline
- `tests/test_a2_c122.py:220-260` usa `inspect.getsource` + `assertIn`: afere o texto da função,
  nunca a linha emitida
- `tests/test_a9_regra_rotulo_c217.py` testa a aritmética do índice e a presença da string, nunca
  o **valor**

A ironia é estrutural: a própria T11 diagnosticou isto (*"um gate que nunca reprova é
decorativo"*) e depois validou as próprias correções com gates do mesmo tipo.

**Recomendação de método, e é a mais barata do relatório:** todo gate novo precisa de um
**controle negativo** — um teste que REPROVA na versão de hoje e passa depois do fix. O `c149` fez
isso certo (`gate_3x1` com 29 OK / 1 RUIM) e o `sobol_batch` também (G-7 RUIM na s42 × OK no pós).

---

## 5. O que a T11 ENTREGOU — ganhos reais, verificados em comportamento

| ganho | configs | medição minha |
|---|---|---|
| **DI-45** — fix do índice em `ClassifierSelect.m:56-58` | e74 | Contribuição 1 do paper sai de **12,23% → 86,89%** de realização (2.094 blocos PRÉ × 267 PÓS, recomputados do zero) |
| **Rito de teto DI-43/44** — projetor avisa em vez de abortar | c154 · c262 | 12 células que davam **zero parquet** agora dão **6 camadas** com curva utilizável: 282/371 FE, IGD+ 1,63→0,14 monotônica |
| **Não-perturbação da sonda** provada por dado | 9 configs MATLAB | ① com **sha256 idêntico em 9/9** pares `g6_com`×`g6_sem` — derruba um teto que era indecidível |
| **Proveniência no ⑤** (`campanha_id`, `repo_hash`, schema v2) | todos os 24 | s42: **0/666** manifestos com `campanha_id`. Corpus T11: **26/26** |
| **DI-41** — dedup da ⑦ | e103 | 45/45 células com exatamente 100 linhas (era 44/45) |
| **I-1 funcionando** onde funcionou | c122 · b4 | 703 ids reais, **zero negativos** — o contraste exato com o `pmid_ids` do c217 |
| **G1/B-11** — writer do ⑥ trunca 1× em `w` e reabre em `a` | b1 + todos MATLAB | o modo de perda que destruiu **15,6% do filme** da b1/WFG1 está eliminado (49 linhas malformadas → 0) |
| **I-3 no alvo nomeado** | sobol_batch | `tempo_aval_real_s` de **0,0 exato em 5/5** para 0,0176–1,5387 s, cobrindo o DoE inicial |

---

## 6. Placar do meu laudo de instrumentação (I-1 … I-8)

**1 FECHADO · 7 PARCIAIS · 0 intactos.**

| item | o que pedia | status | funciona em | falha em |
|---|---|:--:|---|---|
| I-1 | identidade da referência do classificador | 🟡 PARCIAL | b4, c122 | **c217 (sentinela)**, e74 (ausente) |
| I-2 | `REGRA_DO_ROTULO` no `sigma_dict` | 🟡 PARCIAL | b4, c217, c122 | e74 |
| I-3 | cronômetro no portão de avaliação Python | 🟡 PARCIAL | sobol_batch | **os 5 offline (semântica trocada)** |
| I-4 | `NO_RETRY` de exceções determinísticas | 🟡 PARCIAL | c154, c262 | b1, b3 |
| I-5 | `y_treino_dist` | 🟡 PARCIAL | b4, c122 | **c217 (degenerado)**, e74 |
| I-6 | sonda estratificada | 🟡 PARCIAL | funciona como instrumento em b4/c217/e74/c122 | **grava na coluna errada** |
| I-7 | `tempo_geracao_s` / `tempo_fit_s` | 🟡 PARCIAL | e103 | sobol_batch |
| I-8 | `n_front1` / `f_best` no `sobol_batch` | ✅ **FECHADO** | sobol_batch | — |

**Veredito da instrumentação: NÃO está pronta para as 30 sementes — mas falta pouco e é barato.**
A lacuna que o laudo chamou de irrecuperável (identidade da referência) fechou em **2 dos 4
classificadores**. Rodar hoje produziria ~10.000 células com **qualidade de classificador
não-mensurável** — metade do prejuízo que o laudo queria evitar, pelas **mesmas duas linhas**.

---

## 7. Bloqueadores antes do disparo (8 de 22)

Ordenados por impacto/custo. Todos com arquivo:linha verificado.

| id | o quê | configs | custo | se ignorado |
|---|---|---|---|---|
| **BL-01** | `pmid_ids` grava −1 em 100% — fatia `1:D` numa matriz de largura D+1 | c217 | **1 linha** + 1 controle negativo | ~625.000 gerações com o campo sentinela em 30 sementes |
| **BL-02** | `flag_vetores_degenerados` é código morto (`src/b5_prob.py:118` lê o objeto errado) | b5m, b5r, moead_media | **1 token** + ~3 linhas | ~8.000 células offline sem a causa a montante do PBI NaN |
| **BL-05** | `y_treino_dist` degenerado `(0,0,n)` | c217 | 1–3 linhas | ~625.000 gerações com a distribuição inauditável |
| **BL-06** | sob `teto_wall` o finalProbe não roda | c154, c262 | **1 linha** (~0,08 s) | última geração sem sonda, contra o próprio manifesto |
| **BL-07** | piso de ruído O-18 **desatualizado** × campanha em 3 máquinas | todas as 695×30 | 0 CPU (15 pares já existem) | c238/MMF1 ΔHV −9,69% = **6,3× o piso declarado** |
| **BL-08** | pinar `scipy` junto do `torch` na `envs.json` | sobol_batch | **1 linha** | a sequência Sobol scrambled muda entre máquinas e o piso batch deixa de ser régua |
| **BL-09** | `jsonl_line` grava sem `fflush` por linha | b1 + todos MATLAB | **1 linha** | este writer já destruiu 15,6% do filme de uma célula |
| **BL-10** | contradição documental viva sobre N=20 (DI-32/A2 × DI-39) | os 4 pisos | decisão + reconciliar | se o SUB-varN eleger N≠20 depois, **as 25 células de cada piso são descartadas** |

**Soma do trabalho de código: ~10 linhas.** O resto é decisão e texto.

---

## 8. As 18 decisões do autor (D97/D81)

A torre analisou e recomenda; o veredito é seu. As 5 mais consequentes:

1. **D1 — homologar qual matriz de score?** (a) o CSV como está · (b) a lista revista pós-F5.4
   · (c) reabrir config a config. **Recomendo (b)**, porque 4 das 5 revisões são refutações
   provadas — mas note que ela **inverte o veredito do e103** e muda b4/c149/b5r.
2. **DA-01 — piso de ruído O-18 × 3 máquinas.** O piso declarado (HV ≤1,55%) não cobre a
   divergência cross-máquina medida (c238/MMF1 ΔHV −9,69%). **Decidir ANTES do disparo.**
3. **DA-02 — N=20 é definitivo ou o SUB-varN é pré-requisito do M8?** Contradição documental viva.
   Recomendo (a) pela precedência cronológica da DI-39.
4. **DA-03 — `tempo_aval_real_s` no offline:** manter medindo ingestão (renomeando), voltar a
   NULL, ou separar em dois campos. Quatro relatórios escalam o mesmo item.
5. **DA-11 — as 25 células da s42 do e74 descrevem um algoritmo diferente do que rodará no M8.**
   Recomendo o caveat duro de corpus: não agregar com runs pós-fix. É o **único** config em que
   isso vale.

Mais: DA-04 (adotar a classe residual "(d) defeito de instrumentação"), DA-05 a DA-18 —
detalhadas em [`dados/bloqueios.json`](dados/bloqueios.json).

---

## 9. Validação do rito de teto (c154) — aprovada

Detalhe completo em [`VALIDACAO_TETO_c154.md`](VALIDACAO_TETO_c154.md). Resumo: na rodada-42 a
célula `main/c154/DTLZ2/s42` era categoria B (*"`teto_wall` por projeção"*) e produzia **zero
parquet**. Hoje entrega **6 camadas** e uma curva monotônica utilizável em 282/371 FE. O evento
`wall_projection_warning` em it=34 mostra exatamente a mudança: o aviso deixou de abortar.

**De brinde:** o gargalo é a **aquisição**, não o surrogate — `tempo_fit_surrogate_s` = 1,1% do
run, `tempo_busca_s` = 98,8%, com custo/geração quadruplicando (58,7 s → 238,8 s). Um teto de 6 h
**nunca** fecha esta célula: a projeção pede ~13,4 h.

---

## 10. Smokes Python — 11/11 auditados

Medição direta minha sobre `evidencia_T11/smoke_python/` (a bateria de 12 agentes foi
interrompida por tempo; estas 4 checagens cobrem o essencial e estão re-medidas).

**Inventário do §2 do handoff: 11/11 exato** — todas as contagens de ①②③④⑦⑥ batem. Os pares de
números idênticos entre configs diferentes (`c154`≡`c262`, `c149`≡`e81`, `b5m`≡`moead_media`)
**não são copy-paste**: as ① têm sha256 distintos. São runs genuínos com o mesmo scaffold.

| checagem | resultado |
|---|---|
| ⑤ contrato (`params`, `sigma_dict`, `campanha_id`, `repo_hash`, schema v2) | ✅ **11/11 OK** |
| ⑥ integridade (header, footer, linhas malformadas) | ✅ **11/11** — h1 f1, **0 malformadas** |
| CONTRATO regra 12 (estratificada nunca misturada com a régua Sobol) | ✅ regimes separados em todos |
| ③ nos pisos | ✅ 0 linhas em `sobol_batch` — por desenho, não é falha |

### Os 2 defeitos transversais do caminho Python — confirmados por mim

1. **`c122` · sonda estratificada grava na coluna errada.** `regime='sonda_estratificada'`:
   **10.500 linhas**, `mu_0` preenchido em 10.500, `sigma_0` em 10.500, **`pred_score` em 0**.
   O `sigma_dict` do próprio run declara outra coisa. É o único config Python com o bloco.
   *Fix: ramificação de 4 linhas em `emit_sonda_estratificada` que já existe na função irmã.*
2. **`tempo_aval_real_s` trocou de semântica nos 5 offline Python.** Medi nos dois corpora:

   | config | s42 | smoke T11 |
   |---|---|---|
   | b5r | **45/45 exatamente 0.0** | 0,0003 |
   | b5m | **45/45 exatamente 0.0** | 0,0001 |
   | moead_media | **45/45 exatamente 0.0** | 0,0001 |
   | c311 | **55/55 exatamente 0.0** | 0,0003 |
   | treed_media | **10/10 exatamente 0.0** | 0,0572 |

   **200/200 manifestos** da s42 tinham 0,0 — honestamente zero, porque no offline não há
   avaliação real. Agora o campo mede a **ingestão do dataset**, contradizendo a docstring que
   justifica sua existência. Vira a decisão do autor **DA-03**.

**Conclusão dos smokes:** o encanamento está bom em 11/11 — mas, como o §5 do próprio handoff
avisa, *"um algoritmo pode estar profundamente errado e passar nos 6 portões"*. Os smokes **não
movem nenhum score**: a fidelidade foi julgada sobre a rodada-42, que é o corpus certo.

---

## 11. Artefatos

| artefato | endereço | conteúdo |
|---|---|---|
| 24 relatórios de config | `f5/t11/relatorios_config/*.md` | 1,35 MB · 38–72 KB cada · 20–34 aspectos narrados |
| Seções de score verbatim | `f5/t11/_secoes_score.md` | 43 KB · a §7 de cada um dos 24 |
| Baseline resolvida | `f5/t11/dados/baseline.json` | 24 configs × (CSV, pós-adversarial, estado, citação) |
| Vereditos verificados | `f5/t11/dados/veredictos.json` | 24 × (alegado, corrigido, sustenta, evidência re-medida) |
| Classe (3) | `f5/t11/dados/classe3.json` | 21 achados, 9 transversais, dedupados |
| Instrumentação | `f5/t11/dados/instrumentacao.json` | placar I-1..I-8 |
| Bloqueadores + decisões | `f5/t11/dados/bloqueios.json` | 22 bloqueadores, 18 decisões do autor |
| Regressões e ganhos | `f5/t11/dados/regressoes.json` | 14 regressões, 8 ganhos, todos verificados |
| Validação do teto | `f5/t11/VALIDACAO_TETO_c154.md` | medição completa do rito DI-43/44 |
