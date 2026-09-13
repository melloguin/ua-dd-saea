# IMPLEMENTAÇÃO + UM BLOQUEADOR NOVO — guard da régua S.5 e o que ele revelou

**De:** torre de validação de fidelidade · **Para:** torre central + autor · **2026-08-15**
**Autorização:** o autor pediu explicitamente que eu implementasse o que conseguisse resolver.
**Não fiz:** `git push`, `git tag`, alterar valor de régua (fidelidade = do autor, D81/D97).

---

## 1. O que implementei — `checa_regua`, um gate que testa COMPORTAMENTO

**Arquivo:** `src/metrics.py` (+56 linhas: `_GUARD_FOLGA_REL`, `checa_regua`, e a chamada em
`metrics_of_set`).

**O problema que ele resolve.** O selo `REGUAS_PROVISORIAS` é **declarativo** — não impede
ninguém de calcular. E `reference_bounds` só levantava quando a régua era `None`; a fase 1 do
DDMOP7 **não é** `None`, tem valores. **Nada disparava.** É exatamente o padrão que a T11 provou
ser inútil (§4.1: *"gates que testam texto, não comportamento"*).

**O que ele testa.** O `ideal` é, por definição, o melhor valor alcançável por objetivo. Um ponto
com `f < ideal` **prova** que a régua está errada — e sob D69 produz normalizado **negativo**, o
que tira o ponto do hipercubo unitário e destrói o sentido do HV com `ref=1,1`.

**Controles (a regra da casa: todo gate nasce com controle negativo):**

| controle | esperado | medido |
|---|---|---|
| **negativo** — dado real do smoke `c141`/DDMOP7 sob a régua fase-1 | **reprovar** | ✅ reprova: *"322 de 526 pontos são MELHORES que o ideal"*, com os dois eixos nomeados |
| **positivo** — mesmos dados sob régua que os cobre | passar | ✅ silencioso |
| **não-regressão** — ZDT1, DTLZ2, WFG1, MMF1, BBOB_F1, RE21, ESTOQUE40 | passar | ✅ **7/7** |
| **folga float32** — ponto exatamente no ideal, lido em float32 (D53) | não reprovar | ✅ tolera (`_GUARD_FOLGA_REL = 1e-6`) |
| suíte `tests/test_metrics.py` | verde | ✅ **22/22** |
| âncora D92 `hv_smoke_bbob_f1()` | 1,0433 | ✅ **1,0433 exato** |

---

## 2. 🔴 O BLOQUEADOR NOVO que o guard revelou — a régua furada toca a BUSCA

Eu tinha tratado a régua fase-1 como problema **de análise** (HV publicado). **Estava errada, e
para menos.** Rastreei os consumidores de `reference_bounds` e achei dois **dentro de algoritmos**:

| sítio | o que faz com a régua | efeito de um ideal alto demais |
|---|---|---|
| `src/c122_thetadeadp.py:137` | normaliza o **PBI** por `(ideal, nadir+0,1·rng)` durante a busca | `z` negativo ⇒ `d₁` do PBI fica "atrás" do ideal. A docstring diz que a margem 0,1 existe para pontos **PIORES** que o front — pontos **MELHORES que o ideal não foram antecipados** |
| `src/c262_qnehvi.py:208` | deriva o ref-point da **aquisição**: `ref_f = nadir + 0,1·(nadir − ideal)` | `(nadir − ideal)` pequeno demais ⇒ ref-point apertado ⇒ menos candidatos contribuem HVI |

**Medido nos smokes de 15/08 (dado real, sob a régua fase-1 vigente pós-errata):**

| config | pontos abaixo do ideal | `f` normalizado mínimo | usa a régua na busca? |
|---|---:|---|---|
| **c122** | **209/425 (49,2%)** | `[−0,231 ; −0,346]` | **SIM** |
| **c262** | **221/398 (55,5%)** | `[−0,231 ; −0,383]` | **SIM** |
| c141 | 322/526 (61,2%) | `[−0,077 ; −0,421]` | não |
| nsga2 | 321/526 (61,0%) | `[−0,231 ; −0,402]` | não |

> **Metade das avaliações do `c122` e do `c262` no DDMOP7 caiu abaixo do ideal declarado, e os
> dois normalizam por ele em tempo de execução.** Não é HV publicado — é a busca deles.

**E a fase 2 não resolve**, porque é circular: ela é pós-hoc (calculada a partir das runs), mas
`c122`/`c262` precisam de régua **durante** as runs.

---

## 3. A correção que recomendo — ínfimo TEÓRICO, não estimado

O ideal da fase 1 é uma **estimativa** (mín/máx sobre 62 pontos do probe v6). Estimativa pode ser
furada — e foi. A alternativa não é outra estimativa: é o **ínfimo dedutivo** do espaço-objetivo.

No DDMOP7 os objetivos são contagens normalizadas: `f₁ = k/17` com `k ≥ 0` e `f₂ = n/690` com
`n ≥ 0`. Logo o ínfimo é **`[0 ; 0]`**, por construção — não por medição.

**Testado sobre os 15 smokes, 7.156 pontos:**

| candidato a `ideal` | pontos furando | `z` mínimo | |
|---|---:|---|---|
| fase-1 vigente (62 pts do probe) | **3.203/7.156** | `[−0,231 ; −0,421]` | ❌ |
| **ínfimo teórico `[0/17 ; 0/690]`** | **0/7.156** | `[+0,059 ; +0,192]` | ✅ **nunca fura** |
| ínfimo prático `[1/17 ; 0/690]` | 0/7.156 | `[0,000 ; +0,192]` | ✅ |

**Por que isto é melhor que "estender a régua com os dados de hoje"** (que foi a rota do
ESTOQUE40 na D102.20): lá os furadores eram os **cantos da caixa**, objetos determinísticos e
enumeráveis. Aqui não há canto conhecido — qualquer ideal estimado pode ser furado pela próxima
semente. O ínfimo teórico **não pode**, e não introduz parâmetro arbitrário (D81: não inventar
valor). Custo: o HV fica menor em valor absoluto, mas **igualmente comparável entre configs**, que
é tudo o que a comparação precisa.

**NÃO apliquei.** Régua é fidelidade; fidelidade é do autor (D97). O guard que escrevi vai fazer
o cálculo **falhar alto** até você decidir — que é o comportamento correto.

---

## 4. Status das tarefas que eu havia listado

| # | tarefa | estado |
|---|---|---|
| 1 | **Guard executável da régua fase-2** | ✅ **feito e testado** (§1) |
| 2 | Registro do `x_efetivo` | 🟡 **não implementei — e recomendo NÃO implementar agora.** Mexer no schema da ① com a onda RE21/ESTOQUE40 em voo é risco desnecessário. A função de reconstrução **já existe** (`ddmop7_bridge.zona_morta`); o que falta é uma **regra de leitura declarada** no `CONTRATO_DE_DADOS.md` §10 dizendo que qualquer contagem de `\|ND\|` do DDMOP7 deve dedupar por `zona_morta(x)`. Texto, não código |
| 3 | **Régua fase-1 do DDMOP7** | 🔴 **escalado, agora como BLOQUEADOR** (§2/§3) — mudou de "análise" para "busca" |
| 4 | b1 do smoke DDMOP7 travado | 🟡 pendente — a célula nunca fechou (só 15 dos 16 smokes existem). Não bloqueia: o b1 não usa a régua na busca |
| 5 | Foto offline sob codificação | 🟡 pendente — depende do dataset s0 estar na máquina certa |

---

## 5. O que isto muda no meu veredito de disparo

**Mantenho GATE VERDE para a zona morta** — nada aqui toca o mecanismo dela, e as três medições do
`T15-PARECER-FINAL-ZONA-MORTA.md` seguem de pé.

**Mas acrescento uma condição que antes eu tinha como "não-bloqueante":** o disparo das 1.890 com
a régua fase-1 vigente faz **`c122` e `c262` rodarem 30 sementes com normalização negativa em
~50% das avaliações**. Isso não é um número publicado errado — é comportamento de busca
distorcido, que nenhuma correção pós-hoc desfaz.

**Recomendação: cravar o ideal do DDMOP7 como `[0 ; 0]` ANTES do disparo.** É uma linha em
`src/metrics.py:F_MIN_MAX`, é dedutiva, é registrável como errata da REAL-2.15, e o guard do §1
comprova que ela fecha. Os outros 19 configs não são afetados de nenhum modo.

---

*Medições: `~/Downloads/d7_smokes/` (15 células de vm1/vm5) · scripts na transcrição da sessão ·
`src/metrics.py` alterado e testado, **não commitado, não pushado**.*
