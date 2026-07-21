# R3-c122 — RELATÓRIO DE EXECUÇÃO (a narrativa do processo)

> Companheiro do `handoff/R3-c122.md` (que é o *o quê*). Este é o *como* — o que
> aconteceu na sessão, na ordem em que aconteceu, incluindo o que deu errado.
> Escrito para a torre entender as decisões sem ter que reconstruí-las.

## 1. O recon primeiro, o código depois (e valeu a pena)

O cartão descreve o c122 como "driver próprio, bypassa o factory, cap anti-spin,
stub do visualizer, f_min/f_max pela assinatura" — cinco patches. Antes de
escrever uma linha, mapeei o repo oficial com 4 leitores em paralelo (driver ·
learning/evolution · SPEC/S.5 · APIs do harness), **cada um seguido de um
verificador cético** que reabriu os arquivos e conferiu âncora por âncora.

Isso mudou o desenho inteiro. Os verificadores acharam 5 âncoras erradas e 8
omissões materiais nos relatórios brutos — entre elas duas que teriam custado
caro:

- **existem DOIS `emit_sonda_block`** (`standalone_harness.py:738` com
  `geracao=`/`predict=`, e `botorch_harness.py:421` com `it=`/`adapter=`/
  `model=`). O relatório bruto apontava o c262 como "análogo da R2" — copiar
  aquela forma de chamada num cartão R3 é `TypeError` imediato;
- **`write_run_outputs` tem `regime="offline"` por default** enquanto
  `export.write_surrogate` tem `"online"`. Um cartão online que omitisse
  `regime=` carimbaria **toda** a ③ como `offline` *e* ganharia um
  `cp_init_offline` no manifesto — sem erro nenhum.

**Resultado do recon: quatro dos cinco "patches" não eram patches.** O repo
oficial ficou **bit-a-bit intocado** (detalhe por arquivo:linha no handoff §ZERO
PATCHES). O caso mais bonito é o DEF-B11.1: `scalar_dom_ea_dp` **já declara**
`f_min=None, f_max=None` (`evolution/algorithms.py:7-8`) — o bug é que
`tdeadp_main.py:135` simplesmente não os passa, e aí `init_obj_limits` cai para
`0/1` e a normalização vira a identidade. "Entregar pela assinatura sem tocar o
core" era literalmente passar dois argumentos.

E o bypass do factory dispensou cortar `problems/wfg.py`: **`evolution/` e
`learning/` não importam `problems/`** — os imports duros de
`pymop`/`optproblems`/`autograd` vivem só naquele pacote, que nunca tocamos.
Há sentinela no teste que falha se algum deles aparecer em `sys.modules`.

## 2. 🔴 O bloqueio real: a P3/DI-16.3 não era implementável

Este foi o achado da sessão, e o único que exigiu parar.

A DI-16.3 manda gravar *"o TOP-100 do pool N\*=7000 por `e(z)` + os agregados
(min/mediana/máx de `e(z)`) do pool INTEIRO"*. Ao ler o `select_best_individual`
percebi que **`e(z)` não existe para o pool**. Antes de escalar, submeti a
afirmação a **4 lentes adversariais independentes** — leitura de código,
definicional (será que `e(z)` pode ser lido como o score inter?), custo, e
referência-alternativa — cada uma instruída a REFUTAR.

**4/4 confirmaram, 0 refutaram.** O que ficou provado:

| | `e(z)` (o que a DI-16.3 pede) | o que existe para os 7.000 |
|---|---|---|
| onde | `selection.py:158-168`, `nn_predict_dom_intra` | `selection.py:86-87,108`, `nn_predict_dom_inter` |
| forma | Σ_j I(z ≻ j)·p̂(z,j), 2 redes | `scf = p_cfs[i] + s_cfs[i]` |
| conjunto | **intra**, a categoria vencedora, ≤ `Q_max=300` | vs **1** representante de cluster |
| soma em *j*? | sim | **não** (o rep é um só) |
| indicador de dominância? | sim | **não** — soma a confiança do *argmax*, seja qual for; no ramo Q2 soma confiança de **NÃO**-dominância com sinal positivo |

E o custo fecha o caso: um `e(z)` real sobre 7.000 é C(7000,2)×2 redes =
**49 milhões de pares por iteração**, e o `nn_predict_dom_intra` materializa uma
**lista Python** antes do `torch.tensor` (`prediction.py:17-24`) — **~8–10 GB por
rede por iteração**, ~185 iterações. Não é lento: é impossível.

A lente de custo trouxe o número que faltava para a decisão: um `e(z)` de
*instrumento* sobre os 7.000 **contra a população** (a referência da P2) custaria
só 154k (M=2) / 210k (M=3) pares — 318× menos —, e a forma de chamada
`7000 × ~11` **já existe no código oficial** (`find_distinct_individuals`,
`selection.py:178`). Ou seja: a opção B era viável, só cara e com referência
inventada.

Escalei por **D81** com 3 opções e uma recomendação (A+). O autor cravou **A+**:
③ = TOP-100 por `e(z)` entre os que **têm** `e(z)`; agregados do pool inteiro no
jsonl restritos ao que o algoritmo **de fato computa** (contagens Q1/Q2/Q3,
`n_acordo`/`n_desacordo`, min/med/máx do score inter). Custo extra zero,
perturbação zero, e nenhum número fabricado.

*Nota para a torre:* o cartão dizia "P3 JÁ CRAVADA — não re-perguntar". Não
re-perguntei a decisão; reportei que a **premissa** dela era falsa. É a distinção
que o D81 existe para preservar.

## 3. O achado de brinde: a perna (ii) da P2/DI-16.2 é factualmente errada

A lente "referência-alternativa" foi instruída a avaliar se `pop` era uma escolha
faithful — e devolveu mais do que pedi. A DI-16.2 justifica a sonda-vs-população
por duas pernas: **(i)** tamanho fixo ⇒ comparabilidade, e **(ii)** *"é o contexto
REAL em que o modelo decide na busca"*.

A **(i)** é sólida e sozinha suficiente. A **(ii)** não se sustenta: o contexto
real de decisão tem dois estágios — um representante de cluster
(`selection.py:86-87`) e depois o intra entre ≤300 co-candidatos
(`selection.py:158-168`). A população selecionada **nunca** aparece do lado
direito de uma consulta de dominância; ela é pool de pais e alvo da survival
selection, só isso.

**Não muda nada na implementação** (a decisão (a) continua correta pela perna i),
mas muda como o dado deve ser LIDO: a sonda do c122 é um **instrumento de medida
com referência própria**, não uma reconstrução do score interno. Registrei isso
no `sigma_dict` do manifesto — que é justamente o campo que a R4 declara "leitura
obrigatória antes de usar a ③".

## 4. O bug que só o run real encontrou: cache-hit × o arquivo

MMF1 rodou até a ÚLTIMA geração e morreu com
`IndexError: index 61 is out of bounds for axis 1 with size 61`, dentro do
`access_dom_rel` (`evolution/dom.py:57`).

Causa: o laço stock (`algorithms.py:48-50`) faz `evaluations += 1` e
`archive.append(individual)` **incondicionalmente** — o repo não tem dedup. O
nosso contrato tem (**D89**: X bit-a-bit idêntico = mesma solução, 0 FE). Eu
dirigi o laço por `bud.fe` (correto — é o que garante FE = 31D−1 exato mesmo com
cache-hits), mas continuei anexando ao arquivo. Num cache-hit o `bud.fe` não
anda e o arquivo anda: `len(archive)` ultrapassa `maxfe`, e o `rel_map` —
dimensionado exatamente em `maxfe` (`algorithms.py:27`) — estoura.

Conserto: **no cache-hit o arquivo não cresce.** A ③ continua sendo gravada (a
predição foi decisão-relevante — o modelo escolheu aquele ponto), com
`real_solution_id` apontando a solução **preexistente**, que é o join correto. E
pus um cap de segurança: `SPIN_MAX` cache-hits consecutivos ⇒ pára-e-loga, senão
um modelo teimoso travaria o orçamento para sempre.

Ocorreu **1×** em MMF1 e 0× em DTLZ2 — raro, mas fatal quando ocorre, e **atinge
c149 e e81 pelo mesmo mecanismo**. Está nas definições em aberto do handoff.

## 5. O dtype: medi antes de decidir

`pin_runtime()` deixa o default do torch em **float64** (N.1.1: "fixar CPU +
threads=1 + float64"). O c122 é float32-nativo — `prediction.py:24` faz
`torch.tensor(data).float()` explícito. Em vez de supor, rodei o experimento
mínimo: `NeuralNet` sob float64 + entrada `.float()` →
`RuntimeError: mat1 and mat2 must have the same dtype, but got Float and Double`.

É **forçado pelo código**, não uma escolha de fidelidade (D29 🟠 impl→código).
Uso float32 só dentro de `_c122_runtime()`, restauro na saída (há teste de
vazamento) e registro em `params.torch_default_dtype`. Sinalizei à torre que o
N.1.1 enuncia "float64" como se fosse universal, quando é uma regra escrita
pensando nos configs de GP.

## 6. O teste que quase mentiu

O teste mais importante da sessão é o que prova que o **fork instrumentado decide
o mesmo que o código stock** — porque toda a telemetria é inócua se a ESCOLHA
divergir; aí não é instrumentação, é outro algoritmo.

A primeira versão falhou com `AssertionError: unexpectedly None`. Fui depurar
esperando um bug meu — e o stock devolvia `None` **também**. Os dois
concordavam: era o caso de *spin* (as 3 categorias saem vazias e o laço
re-sampla), que no MMF1 é comum (5 disparos no run completo). Meu
`assertIsNotNone` é que estava errado.

Corrigi para percorrer **um ciclo completo de cluster ids**, comparando escolha a
escolha e aceitando `None == None` como concordância — com um
`assertGreater(n_achou, 0)` no fim para o teste não poder ficar **vacuamente
verde** se nenhum cluster produzisse candidato. Sem essa última linha eu teria
trocado um teste falso-vermelho por um falso-verde.

*(A premissa que torna o fork seguro tem teste próprio:
`test_predicao_NAO_consome_RNG` — predição roda sob `eval()`+`no_grad()`
(`prediction.py:76-78`), então recomputar a triagem para telemetria não move a
trajetória. É isso que me deixa calcular os agregados do pool sem pagar 2× os
forwards nem perturbar a busca.)*

## 7. Épocas: medidas, não recomputadas

O `update_dom_nn_classifier` só **imprime** as accs e não devolve nada. A
tentação é recomputar a Eq. 5 (`E_upd = ceil(20·(γ−min_acc)/γ)`) a partir das
accs capturadas. **Não serve:** a fórmula confunde três caminhos distintos de
"zero época" —

1. gate `min_acc >= γ` passou (`model_update.py:22`) — o modelo está bom;
2. `compute_class_weight` devolveu `None`, classe ausente (`:28-29`) — o modelo
   **não pôde** treinar;
3. treinou de verdade.

O caso 2 apareceria no dossiê como se tivesse treinado. Então sombreio
`mu.train_nn` e capturo o `epochs` **realmente passado** — adição read-only que
só expõe valor já computado (o critério da DI-12.1), com o treino 100% do código
do autor.

Aproveitei para registrar uma armadilha de leitura: `get_accuracy` devolve o
sentinela **`1`** para classe AUSENTE (`learning/utils.py:144-145`). Logo
`acc == 1,0` pode significar "sem amostra dessa classe", **não** "perfeito" — e
como o gate é `min(acc) >= 0,9`, uma classe ausente **empurra para o skip**.
Quem ler o dossiê precisa saber disso para não interpretar `skip_treino` como
"modelo já bom".

## 8. A segunda questão de faixa: o gate não existia

No PASSO 3 descobri que o critério de aceitação do cartão
(`scripts/accept.py R3-c122 … exit 0`) referencia um branch **inexistente**, e
`accept.py` não estava na minha faixa. Parei e perguntei (D81), com `git status`
mostrando o arquivo limpo (a sessão paralela estava em `*.m`, SPEC e
`scripts/progress.py`).

Autorizado, escrevi o branch **ADITIVO**, inserido **antes** do catch-all
`if a.cartao.startswith("F0-01") or not a.alg:` — a armadilha que o R3-00 já
tinha documentado: sem isso o cartão é engolido e devolve o VERDE do andaime
F0-01, um falso verde perfeito.

Uma diferença de desenho vale registro: o `check_r3_00` **roda** o stub (segundos);
o `check_r3_c122` **afere um run já gravado**. Um run real do c122 vai de 49 s
(MMF1) a horas (ZDT1) — re-rodar dentro do gate o tornaria inutilizável na
bateria.

## 9. A auditoria que acusou o próprio auditor

Na auditoria pyarrow dois itens saíram vermelhos: `e(z)` "fora de ordem" no
DTLZ2 e `tempo_aval_real_s = 0.0`. Os dois eram **defeitos do meu script de
auditoria**, não dos dados:

- a ordenação: eu fatiava as 100 primeiras linhas de busca, mas em DTLZ2 a
  maioria das gerações tem **menos** de 100 candidatos (o `Q_max=300` raramente
  vincula), então o fatiamento atravessava a fronteira de geração. Conferindo
  **por geração**: 0/41 e 0/240 fora de ordem;
- o tempo: valores reais 0,002 s e 0,0143 s — meu `print` arredondava para 1
  casa.

Registro porque a lição é geral: **um vermelho de auditoria merece a mesma
desconfiança que um verde.** Se eu tivesse "consertado" o writer para satisfazer
o meu próprio script, teria introduzido um bug para corrigir um erro de
formatação.

## 10. Sequência executada

| # | Ação | Resultado |
|---|---|---|
| 1 | PASSO 0 — contrato de dados, handoff R3-00, contrato R3, cartão, registro A3/A4/A5 | — |
| 2 | Recon 4×2 agentes (leitor + verificador cético) | 5 âncoras erradas, 8 omissões materiais |
| 3 | Verificação adversarial da P3 (4 lentes) | **4/4 confirmaram** — premissa falsa |
| 4 | **D81 #1 → autor: opção A+** | ③-busca definida |
| 5 | `src/c122_thetadeadp.py` + correções de assinatura | — |
| 6 | Smoke MMF1 | `IndexError` do cache-hit → §4 |
| 7 | MMF1 · DTLZ2 | FE **61** e **371** exatos |
| 8 | **D81 #2 → autor: estender faixa** | branch aditivo em `accept.py` |
| 9 | Gate R3-c122 | **exit 0** nos 2 |
| 10 | `tests/test_c122.py` | 1 falha → era o teste (§6) → **23 OK** |
| 11 | Provas caras | determinismo bit-a-bit ✅ · ① com sonda ≡ ① sem ✅ |
| 12 | Regressão | **228 OK** · F0-01..04 · R3-00 ×2 · preflight — todos exit 0 |
| 13 | Auditoria pyarrow | §9 |
| 14 | Commits `[R3-c122]` (ritual, staged conferido) | `dc40174`, `e921b3d` |
| 15 | ZDT1 (teto 8 h) | ver §11 |

## 11. ZDT1 — a projeção, o teto, e por que a projeção errou para MAIS

**Fechou limpo: FE=929 exato, 600 gerações, `status='ok'`,
`motivo_parada='orcamento'`, wall 5.060,1 s = 1,41 h.** O teto de 8 h **não foi
exercitado** — o cartão antecipava que seria.

O histórico das projeções vale registro, porque a lição não é "acertei":

| momento | ritmo medido | projeção de wall total |
|---|---|---|
| geração 31 | — | ~5,5 h |
| geração 51 | 17,5 s/ger (médio) · 18,3 (recente) | ~3,0 h |
| geração 65 | 15,9 s/ger (médio) · **13,3 (recente)** | ~2,3 h |
| **final** | **8,4 s/ger** (600 ger / 5.060 s) | **1,41 h** |

Duas causas, e só uma eu tinha previsto:

1. **O platô do fit (previsto).** A janela `T_max = 11D+24 = 354` capeia o
   pareamento: a partir de ~25 gerações (arquivo > 354) o custo por geração para
   de crescer. É por isso que a extrapolação linear é legítima aqui e **não
   seria** num algoritmo com parede O(n³) — o contraste com c238/c262 é
   exatamente esse, e é material para o §17.6.
2. **Contenção de CPU minha (não previsto).** As primeiras ~65 gerações rodaram
   **enquanto** eu executava a suíte de regressão, os gates e as duas provas
   caras (que são elas mesmas 2 runs completos de MMF1). Todo processo está
   pinado em 1 thread (D79), mas são processos concorrentes disputando o mesmo
   Mac. O ritmo "recente" que eu media estava contaminado pela minha própria
   carga.

**Lição para o dimensionamento do M8:** minhas projeções de custo feitas *durante*
a sessão são **pessimistas por construção** — media com a máquina ocupada por
mim. O número honesto para o M7 é o **wall final de um run sozinho**, e é esse
que está na tabela do handoff. Quem for extrapolar a bateria a partir dos meus
números intermediários vai superdimensionar.

*(Nota adicional: `n_spin_total=21` em 600 gerações — o cap de 10 nunca foi
atingido, e os spins não custam FE, só wall. `cache_hits=0` no ZDT1, contra 1 em
MMF1: em D=30 a chance de o SBX/PM reproduzir um X bit-a-bit idêntico é
desprezível — o cache-hit é um fenômeno de D baixo.)*

## 12. O que eu NÃO fiz (de propósito)

- **Não julguei fidelidade** (D97) — nem uma vez. O cap anti-spin e o float32
  são desvios **declarados e logados**, não consertos.
- **Não toquei** SPEC, bundles, `CONTRATO_DE_DADOS.md`, registros, `cards/INDEX.md`,
  `data/{doe,datasets,sonda}`, `src/standalone_harness.py`, `src/export.py`,
  nenhum `.m`, nenhum `algorithms/**`.
- **Não instalei nada** (D80) — conferi `torch`/`deap`/`matplotlib` antes de começar.
- **Não rodei os gates R1** (faixa MATLAB ativa) nem os R2-c\* (desnecessário).
- **Não configurei GCS** — `enable_bucket=False` (DI-16.8/RI-08: o `bucket-only`
  vale do M8 em diante; até o M7 as camadas locais ficam completas, sem podar a ③).
