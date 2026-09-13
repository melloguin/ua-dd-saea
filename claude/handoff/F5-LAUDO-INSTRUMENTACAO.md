# LAUDO DA INSTRUMENTAÇÃO — o que falta para a análise ser completa

> **De:** torre de validação de fidelidade (F5) · **Para:** torre central de implementação
> **Data:** 2026-07-29 · **Base:** as 666 células da rodada-42, medidas — não estimadas.
> **Origem:** perguntas do autor sobre retry, sonda, suficiência dos logs e medição de tempo.
> **Escopo:** este documento NÃO repete o `f5/PLANO_RODADA_PERFEITA.md` (que trata de
> proveniência, append cego e gates). Aqui é só **instrumentação para ANÁLISE** — o que
> falta para responder cientificamente "o surrogate é bom?" e "quanto custa cada parte?".
>
> **Veredito geral: 8,5/10.** Para regressores e para provar mecanismo, a instrumentação
> está completa e foi o que sustentou os 24 relatórios de fidelidade. **A lacuna real está
> nos classificadores**, e ela é **irrecuperável a posteriori** — se não entrar antes do
> disparo das 30 sementes, a análise comparativa de classificadores não existe.

---

## 0. Sumário das 8 recomendações, por prioridade

| # | item | onde | custo | se não fizer |
|---|---|---|---|---|
| **I-1** 🔴 | Logar a **identidade** da referência do classificador (`pmid_ids`, `ref_ids`) | `c217`, `c122` | ~2 linhas cada | **A qualidade do classificador vira não-mensurável em 2 dos 4 configs** — irrecuperável |
| **I-2** 🔴 | Declarar no `sigma_dict` a **REGRA do rótulo verdadeiro** | `b4`, `c217`, `c122`, `e74` | ~0 (string) | A acurácia publicada varia de 0,35 a 0,995 conforme a regra escolhida pelo leitor |
| **I-3** 🟠 | Cronômetro no portão de avaliação Python + permitir NULL | `src/budget.py:222`, `src/export.py:559` | ~1 h | "não medi" e "custou zero" ficam indistinguíveis (5 células hoje; qualquer runner novo amanhã) |
| **I-4** 🟠 | Lista `NO_RETRY` de exceções determinísticas | `experiments.py:111-178` | ~40 min | ~285 h-core queimados em 30 sementes retentando falhas determinísticas |
| **I-5** 🟠 | `y_treino_dist` — prevalência das classes no treino | `b4`, `c217`, `c122`, `e74` | ~1 linha | Não dá para separar "classificador ruim" de "problema desbalanceado" |
| **I-6** 🟡 | Sonda estratificada ou maior para classificadores | `scripts/gen_sonda.py` + loaders | médio | ~8 positivos por bloco ⇒ precision/recall instáveis |
| **I-7** 🟡 | `tempo_geracao_s` no e103; `tempo_fit_s` no sobol_batch | `e103`, `sobol_batch` | ~2 linhas | 2 configs fora da comparação de custo por fase |
| **I-8** 🟡 | `n_front1`/`f_best` no `sobol_batch` (mínimo comum DI-10) | `src/sobol_batch.py:159` | ~1 linha | O único config sem o mínimo comum; recuperável pós-hoc |

---

## 1. RETRY — o mecanismo está bem implementado; falta a lista de não-retriáveis

### O que existe (e está correto)
`experiments.py:72-178`: `RETRY_ATTEMPTS = 3` com **backoff exponencial**
(`RETRY_BACKOFF_S · 2^i` = 0s → 5s → 20s); classe **não-retriável** já implementada para
erros de PREPARAÇÃO (`FileNotFoundError`, `KeyError` → `guard('nao_retriavel')`);
`NotImplementedError` corta; `WallClockAbort` marcado como não-retriável
(`guard('teto_wall_nao_retriavel')`); cada tentativa emite evento `retry` no ⑥ e alimenta
`n_retries` no ⑤. O desenho responde exatamente ao que motiva retry: falha **transitória**
(licença MATLAB contendida, I/O, OOM momentâneo, rede no upload).

### O que os dados mostram (666 células)
```
n_retries nos 666 manifestos : {0: 666}
eventos no corpus inteiro    : retry = 2 · guard:hard_error = 2
```
**O mecanismo praticamente não foi exercitado** — e não por ausência de falhas (houve 29),
mas porque **as falhas foram DETERMINÍSTICAS**, e aí o retry só queima tempo.

### A lacuna — 🔴 I-4
Não existe lista de exceções que **não devem** ser retentadas por serem determinísticas.
Evidência de determinismo, medida:

| célula | erro | prova de determinismo |
|---|---|---|
| `main/b1/DTLZ4` | `least squares problem is underdetermined` | falhou **idêntico em 2 arquiteturas** (vm3 Linux/Intel e Mac arm64) |
| `main/c154/ZDT6` | `random_search_optimizer falhou nas 3 tentativas da escada` (it 62) | a própria escada já esgotou 3 relaxações internas |
| `main/c154/BBOB_F55` | idem (it 55) | idem |
| `main/c262/WFG1` | `ModelFittingError: All attempts to fit the model have failed` | o BoTorch já esgotou as tentativas internas |

Nos 4 casos o despachante ainda repetiu 3×. Em 30 sementes isso é **~430 h-core** contra
~145 h-core com a lista — **economia de ~285 h-core**.

**Correção:** lista `NO_RETRY` de motivos/exceções consultada ANTES do backoff, com os 3
padrões acima. Teste: exceção da lista ⇒ 0 retries; exceção transitória ⇒ 3.

---

## 2. A SONDA — completa para regressores, **incompleta para classificadores**

### 2.1 Regressores: nada a fazer ✅

A régua funciona como projetada — os MESMOS 2.000 pontos Sobol previstos por todos os
modelos, custo 0 FE, join posicional com o gabarito. Medido nas 461 células regressoras
(44.928 medições, `f5/sonda_f52e.csv`), com des-transformação pelo `transf_params`:

| config | WAPE 1º→último bloco | correlação | cobertura ±1,96σ | leitura |
|---|---|---|---|---|
| `c262` (GP exato) | 0,0162 → **0,0135** | 0,995 → 0,997 | **0,990 → 0,996** | calibração de livro-texto, 321 blocos |
| `e7` (MC-dropout) | 0,178 → **0,203** | 0,947 → 0,926 | 0,887 → 0,877 | **piora** = esquecimento do `SelectTrainData` (fiel); σ otimista (família) |

Figuras: `f5/figuras/surrogate_regressor_{c262_ZDT1,e7_DTLZ2}.png`.
**Conclusão:** para regressores, os dados permitem WAPE, correlação, calibração, curva de
aprendizado e comparação entre algoritmos — tudo na mesma régua. **Nada falta.**

### 2.2 Classificadores: a lacuna crítica 🔴 I-1

Um classificador não prevê um valor — ele classifica **contra uma referência**. Para medir
AUC/acurácia é preciso reconstruir o **rótulo verdadeiro** dos 2.000 pontos da sonda, e
para isso é preciso saber **quais pontos** formavam a referência naquela geração.

**Varredura das 100 células dos 4 configs classificadores:**

| config | o que o ⑥ loga | identidade da referência? | AUC/acurácia calculáveis? |
|---|---|:---:|:---:|
| `b4` (CSEA, FNN) | `ref_ids = [556, 598, 623, 624, 633, 653]` + `n_refs=6` | ✅ **25/25 células** | ✅ **sim** |
| `c217` (PC-SAEA, PNN) | apenas `n_Pmid = 13` (o TAMANHO) | ❌ **0/25** | ❌ **não** |
| `c122` (θ-DEA-DP, 2×FNN) | apenas `n_ref = 11` (o TAMANHO) | ❌ **0/25** | ❌ **não** |
| `e74` (CLMEA, PNN) | nem tamanho nem identidade | ❌ **0/25** | ❌ **não** |

**O que dá para medir hoje, por config:**
- `b4` ✅ — AUC real. Medido em ZDT1: **0,906 → 0,819** (mediana 0,716) em 280 blocos.
  O classificador **discrimina**.
- `c217` ❌ — só a distribuição do score ternário {−1, 0, +1} e o `pred_confianca`
  (= Error1, constante por bloco por desenho). Medido: score = 0 em **20,7%** dos pontos
  (mediana) — o surrogate inativo sob δ=0,8, que é o caveat já aceito. Mas *"o modelo
  classifica bem?"* **não tem resposta**.
- `c122` ❌ — o `e(z)` é relativo à população selecionada; sem os ids dela, idem.
- `e74` ❌ — idem, sem nem o tamanho.

**Correção (I-1):** logar a identidade no evento de geração —
`pmid_ids` no c217 (≤13 int32/geração), `ref_ids` no c122 (11-15 ids), `ref_ids` no e74.
**Custo: ~2 linhas por config.** O `b4` já faz — é só replicar o padrão dele.

**⚠ Por que é urgente:** essa informação **não é reconstituível a posteriori**. Rodar 30
sementes sem ela significa 19.980 células em que a qualidade do classificador é
não-mensurável — e classificadores são 4 dos 24 configs do estudo.

### 2.3 A regra do rótulo não está cravada em lugar nenhum 🔴 I-2

Mesmo no `b4`, onde os ids ESTÃO logados, testei as 3 definições plausíveis de rótulo
verdadeiro sobre as mesmas 280 gerações:

| regra do rótulo | prevalência real | acurácia | AUC |
|---|---:|---:|---:|
| não é pior que TODAS as 6 refs (a leitura da DI-18) | 65,5% | **0,350** | 0,716 |
| domina ao menos 1 ref | 0,00% | **0,999** | 0,917 |
| não é dominado por nenhuma ref | 0,40% | **0,995** | 0,713 |

**A escolha da regra move a acurácia de 0,35 para 0,995.** O AUC é robusto (~0,72), mas
"acurácia do classificador" **não é um número reprodutível** enquanto a regra não estiver
escrita. O `sigma_dict` descreve o que a COLUNA contém, não **contra o que** o modelo
classificou.

**Correção (I-2):** uma string no `sigma_dict` de cada classificador, com a regra exata e
a referência do paper. **Custo: zero de dados.**

**Nota de método para a torre:** eu mesmo tropecei aqui. No primeiro cálculo construí o
score do AUC como `±pred_confianca` e obtive 0,28 — quase reportei uma falha inexistente.
A verificação da orientação do campo (`max ruim = 0,4999` / `min bom = 0,5000` ⇒
`pred_confianca` É P(bom), corte em 0,5) mostrou que o erro era meu. **Isso é sintoma do
mesmo problema**: campo sem semântica declarada gera erro de leitura até em quem conhece o
projeto. A declaração no `sigma_dict` resolve os dois.

### 2.4 Tamanho e composição da amostra 🟡 I-5, I-6

Hoje: **2.000 pontos Sobol** (online, a cada 2 gerações) e 20.000 (offline, 1×).
*(O autor mencionou 3.000 — o valor implementado é 2.000; DI-09/DI-13.5.)*

Para regressores, 2.000 é suficiente e a evidência confirma. Para **classificadores** há um
problema de **desbalanceamento**: pontos Sobol aleatórios quase nunca são "bons" —
prevalência medida de **0,4%** ⇒ ~8 positivos por bloco de 2.000. Com 8 positivos,
precision/recall/F1 têm variância enorme; só o AUC é estável.

**Correções:**
- **I-5 (barato, ~1 linha):** logar `y_treino_dist` — a contagem de bons/ruins no conjunto
  de treino daquela geração. Sem isso não dá para separar *"o classificador é ruim"* de
  *"o problema está desbalanceado"*.
- **I-6 (médio):** sonda **estratificada** para classificadores — manter os 2.000 Sobol
  (que garantem a régua comum) e acrescentar um bloco menor amostrado perto do arquivo
  corrente, onde a classe positiva é frequente. Alternativa mais simples: subir para 3.000
  pontos, o que ajuda pouco no desbalanceamento (a prevalência não muda) — **a
  estratificação é o que resolve, não o tamanho**.

---

## 3. OS LOGS BASTAM PARA ATESTAR VALIDADE CIENTÍFICA?

### Sim, para o mecanismo — e a prova é forte

O teste decisivo é: *o log permite REFAZER a decisão do algoritmo e conferir?* Nos 24
configs, sim. Exemplos medidos, em escala:

| config | identidade recomputada dos dados | resultado |
|---|---|---|
| `b1` | EI fechado: `(gbest−μ)Φ(z) + σφ(z) ≡ −ei_best` | **7.073/7.073** (13 caudas com \|Δ\|<1e-18) |
| `e81` | maximin em [0,1]^D recomputado | **8.020/8.020**, \|Δ\| máx 8,1e-8 |
| `c262` | escolhido == argmax de `acqf_todos_restarts` | **5.201/5.201** |
| `e7` | ramo ⇔ desigualdade `RatioOld−Ratio` vs δ | **2.328/2.328** |
| `c217` | estado ⇔ regra tripla p⁺/p⁻ vs δ | **6.762/6.762** |
| `b3` | critério = média das VARIÂNCIAS sem raiz | **7.215/7.215**, erro rel. 4,24e-16 |

Isso é o que dá validade científica: as conclusões dos 24 relatórios não dependem de
acreditar no log — dependem de recomputar a decisão e ela fechar.

### Não, para a análise de qualidade dos classificadores

É a lacuna do §2. Especificamente, **não são respondíveis hoje** com `c217`/`c122`/`e74`:
acurácia, precision, recall, F1, AUC, matriz de confusão, curva de aprendizado do
classificador, e a comparação classificador × regressor na mesma régua.

### O que eu adicionaria além dos itens acima (ordem de valor/custo)

| adicionar | por quê | custo |
|---|---|---|
| **`pmid_ids`/`ref_ids`** (I-1) | destrava toda a análise de classificador | ~2 linhas/config |
| **Regra do rótulo no `sigma_dict`** (I-2) | torna a métrica reprodutível | ~0 |
| **`y_treino_dist`** (I-5) | separa modelo ruim de problema desbalanceado | ~1 linha |
| **`n_front1`/`f_best` no sobol_batch** (I-8) | fecha o único config sem o mínimo comum DI-10 | ~1 linha |
| Sonda estratificada (I-6) | positivos suficientes para precision/recall | médio |
| `repo_hash` preenchido | está **vazio em 666/666 células** — o elo run↔código não se auto-certifica | ~1 linha |

**O que eu NÃO recomendo adicionar** (custo > benefício, e já rejeitado pelo DI-10 como
patch invasivo): genealogia de pais por indivíduo · predições intermediárias do EA interno
(o b1 faz ~10.000 avaliações de EI por iteração — gravá-las seria TB) · serialização do
modelo por geração.

---

## 4. TEMPO — mede as duas coisas, com um buraco

### O que existe e funciona

**Camada ④, por geração/retreino:** `tempo_fit_s` (treino do surrogate), `tempo_busca_s`
(aquisição/otimização interna), `tempo_pred_sonda_s` (custo do instrumento) e
`tempo_geracao_s` (wall da geração **excluindo** a sonda — DI-13.10, para o instrumento não
contaminar a curva de custo).
**Manifesto ⑤, agregados:** `tempo_total_s`, `tempo_fit_surrogate_s`, `tempo_busca_s`,
`tempo_aval_real_s`, e `tempo_total_despachante_s` onde aplicável.

**Cobertura medida (uma célula por config, 20 configs):** `tempo_fit_s`, `tempo_busca_s`,
`tempo_pred_sonda_s` e `tempo_geracao_s` presentes em **todos** os configs com surrogate.
Exemplo real (`c262/ZDT1`): Σfit = 3.330,7 s · Σbusca = 28.391,2 s · total = 31.899,5 s —
**a busca domina (89%), e isso é mensurável célula a célula.** Nos 4 pisos online,
`tempo_fit_s = NULL` (correto — não treinam) com `tempo_geracao_s` preenchido.

**Resposta direta à pergunta:** sim, os logs medem **tanto o tempo de treino do surrogate
por retreino** quanto **o tempo total do algoritmo** — e ainda o breakdown fit × busca ×
sonda × geração. Foi com isso que a projeção de 30 sementes (~10.173 h-core) foi feita.

### Os 3 buracos 🟠 I-3, I-7

1. **`tempo_aval_real_s` não é medido no lado Python.** Varredura das 421 células online:
   **5/5 células do `sobol_batch` têm `0.0` exato**; os outros 17 configs têm valor
   não-nulo mas irrisório (~0,05 s em runs de horas). Causa em 3 camadas:
   `src/budget.py:222` (`f = np.asarray(true_f(x), ...)` — o portão único de avaliação
   **sem cronômetro**; a DI-12.4 instrumentou só o `FEBudget.m` do MATLAB) →
   `src/export.py:559-564` (`round(float(...))` torna **NULL inexprimível**) →
   `src/sobol_batch.py:186` (passa `0.0` literal). **Consequência:** "não medi" e "custou
   zero" são indistinguíveis, e o buraco reaparece em qualquer runner Python novo.
   **Correção:** cronômetro acumulador em `budget.py` + aceitar `None` em `export.py`.
2. **`e103` não grava `tempo_geracao_s`** (é o único; ④ com 1 linha por desenho, D-09/T-8).
3. **`sobol_batch` não grava `tempo_fit_s`** — correto no espírito (não treina modelo), mas
   deveria ser **NULL** como os pisos, não ausente.

---

## 5. O QUE JÁ ESTÁ NO OUTRO DOCUMENTO (não repetir esforço)

Os defeitos de **proveniência e escrita** — append cego do `AuditLogger`, no-op que abre o
⑥, `campanha_id` no `is_run_done`, gates de proveniência, `mirror_run` no aborto, escrita
não-atômica, `params` ausente no ⑤ de 7 configs — estão no
**`f5/PLANO_RODADA_PERFEITA.md`** (17 bloqueadores, ~19 h). Este laudo é complementar: lá
é *"o dado é confiável?"*, aqui é *"o dado permite a análise?"*.

**Custo somado deste laudo: ~2 h de código** (I-1, I-2, I-4, I-5, I-7, I-8) + o item médio
da sonda estratificada (I-6), que é o único que merece discussão de escopo com o autor.

---

## 6. DECISÃO QUE A TORRE CENTRAL DEVE LEVANTAR COM O AUTOR

**A sonda dos classificadores deve ser estratificada?** (item I-6)
- **(a) Manter 2.000 Sobol puros** — a régua fica perfeitamente comparável entre todos os
  algoritmos, mas precision/recall dos classificadores continuam instáveis (~8 positivos
  por bloco).
- **(b) Acrescentar um bloco estratificado** (ex.: 500 pontos perto do arquivo corrente) —
  destrava precision/recall/F1 estáveis, mas o bloco novo **não é comparável entre
  algoritmos** (cada um tem um arquivo diferente) e aumenta o volume.
- **(c) Subir para 3.000 Sobol** — quase não ajuda: a prevalência não muda, só o n.
- **Recomendação da torre: (b)**, mantendo os 2.000 Sobol como régua comum e marcando o
  bloco estratificado com `regime='sonda_estratificada'` para nunca ser misturado com a
  régua. É a única opção que responde "o classificador é bom?" sem quebrar a comparação.
