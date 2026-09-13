# PARECER DA VALIDAÇÃO DE FIDELIDADE — o gate da zona morta

**De:** torre de validação de fidelidade (a que definiu o gate)
**Para:** torre central de implementação · **Data:** 2026-08-15
**Responde:** `handoff/T15-HANDOFF-GATE-ZONA-MORTA.md` §6 (as 5 perguntas)
**Doutrina:** D97 — o veredito é do autor. O que segue é evidência e recomendação.

> **Resumo em uma linha:** o gate passa, mas **a leitura do c149 está errada** — e eu tenho o
> mecanismo. O que a torre chama de "o problema discriminando" é, em boa parte, **um viés que
> nós introduzimos**, ele é barato de corrigir, e a correção provavelmente muda o resultado.
> **Recomendo NÃO disparar as 1.890 antes de um teste de 1 hora.**

---

## 0 · O achado que muda o parecer

**A zona morta é aplicada DENTRO da ponte de avaliação, e o x que fica gravado é o PROPOSTO.**

`src/ddmop7_bridge.py:538-543`:
```python
# A (1)/o catalogo guardam o x PROPOSTO (ver docstring de `zona_morta`).
ini_dz = max(0, N_DOE_ONLINE - self.chamadas_p)
if ini_dz < m:
    X = X.copy()
    X[ini_dz:] = zona_morta(X[ini_dz:])      # ← snap silencioso, aqui dentro
F = np.atleast_2d(np.asarray(self.motor.avalia(X), ...))
```

O chamador passa `x_proposto`, recebe `F`, e **nunca fica sabendo que o ponto foi transformado**.
Logo o par que entra no arquivo do algoritmo — e que treina o surrogate — é:

> **(x_proposto , f(zona_morta(x_proposto)))**

Isso não é detalhe de auditoria. É a definição da função que o surrogate tem de aprender. E ela
tem uma propriedade que decide tudo:

| grandeza | valor (τ=0,5 · D=17) |
|---|---|
| direções com **gradiente exatamente zero** por ponto | **8,5 de 17** (E = D·τ) |
| fração da caixa com ≥1 direção plana | **99,99924%** (1 − τ^D) |
| volume que colapsa no ponto todo-zero | 7,6e-06 |

**Num ponto típico, metade das direções não tem gradiente.** A função virou constante por partes,
com ~2¹⁷ platôs.

---

## 1 · Resposta à pergunta 3 (a que mais preocupa a torre) — **a leitura alternativa é a correta**

A torre propõe duas leituras:

- **(A)** *"a aquisição do c149 escolhe os extremos, e isso é o problema discriminando"*
- **(B)** *"a codificação favorece operadores que já produziam esparsidade e penaliza aquisições
  de fronteira — viés nosso"*

**O dado sustenta (B), e o mecanismo é o do §0.**

Um otimizador de aquisição **baseado em gradiente** — o deep ensemble do c149, o `optimize_acqf`
(L-BFGS-B multi-start) do c154/c262 — recebe **gradiente zero em 8,5 das 17 direções**. Ele não
tem sinal para entrar na zona morta; desliza pelas direções que ainda têm inclinação, e essas
saturam **na fronteira da caixa**. É exatamente o perfil medido: **c149 com 1,2% das coordenadas
dentro da zona morta e nnz 16,8 de 17.**

Um operador **de população** — SBX/PM dos pisos, do b3, do c154 — **não usa gradiente**. Ele herda
coordenadas dos pais, e os pais do DoE já têm ~49,4% de zeros exatos (eu medi: **186/186 com pelo
menos um zero**). Depois a zona morta ainda snap-eia os pequenos. Daí os 91-92% e o nnz 1,3.

**A codificação é a mesma para todos, mas o custo dela não é.** Ela é neutra para quem amostra e
recombina, e é ativamente adversa para quem otimiza uma aquisição diferenciável. Isso é um viés
introduzido por nós, não uma propriedade do DDMOP7.

**A prova positiva de que a leitura (A) é insuficiente:** o c141 — que é assistido por surrogate —
alcançou **o melhor f₂ de toda a bateria (90/690), batendo os quatro pisos (95-102/690)**. Se a
codificação simplesmente favorecesse operadores de população, isso não teria acontecido. Ela não
favorece uma *classe*; ela penaliza uma *mecânica de proposta* — a diferenciável.

### 1.1 E há uma segunda consequência que explica a ressalva do §4

A dedup do D89 opera sobre **X**. Dois `x_proposto` distintos que snap-eiam para o **mesmo**
`x_efetivo` são pontos DIFERENTES para o harness (sem cache-hit) e produzem **F idêntico**.

> **A inflação de empates do §4 (|ND| bruto 195-257 contra 1-6 distintos) é, em parte, sintoma
> disto — não só da quantização do problema.**

A torre atribuiu 100% da baixa resolução à quantização (18 degraus). Parte dela é nossa. **É
testável sem rodar nada:** conte os `x_efetivo` **distintos** entre os pontos ND de cada célula.
Se forem muito menos que os `x_proposto` distintos, a inflação é do registro.

---

## 2 · Resposta à pergunta 1 — o gate passa, mas o meu critério era fraco

**Sim, o critério que fixei foi cumprido literalmente** (ND da busca sai de 0/340 em 14/15). Mas a
torre está certa em suspeitar dele: **eu escrevi um critério fraco demais**, e assumo isso.

O critério certo é o que a própria torre sugere: a busca precisa produzir pontos que **(a) sejam
distintos em espaço-objetivo e (b) melhorem o melhor f₂ do DoE** — não apenas entrar no front.

Re-medi com essa régua. O melhor f₂ do DoE (semente 0, 186 pontos) é **110/690 = 0,159420296**:

| régua | resultado |
|---|---|
| minha original (ND da busca > 0) | **14/15** ✅ |
| **régua forte (melhora o f₂ do DoE)** | **13/15** ✅ — falham **c122** e **c149**, que empatam **exatamente** com o DoE |

**O gate passa nas duas.** E é notável que os dois que falham na régua forte sejam justamente os
dois que a torre já havia nomeado por outros motivos — a evidência é coerente consigo mesma.

---

## 3 · Resposta à pergunta 2 — a vaga B volta a ser problema de comparação, com uma ressalva

**Mudo minha recomendação original** (era "estudo de caso declarado"). Com a codificação, o
DDMOP7 volta a ser **problema de comparação legítimo** — a degenerescência acabou: antes os 13
online produziriam literalmente o mesmo front (o do DoE compartilhado, `max|ΔX| = 0,0` entre
configs) e o mesmo HV; agora 13 de 15 melhoram o DoE e a ordem entre eles é mensurável.

**A ressalva é sobre a resolução, e ela é menor do que o §4 sugere** — porque parte da baixa
resolução é o artefato do §1.1. Depois de corrigir o registro, a resolução real precisa ser
re-medida. Hoje, com o que existe:

- amplitude do melhor f₂: **90/690 a 110/690** — 18% relativo, **20 degraus de 690**
- k mínimo alcançado: **1 a 5** (de 18 possíveis)
- front efetivo: **1 a 6 pontos distintos**, mediana 3

**O texto do capítulo 5 deve dizer isto com essas palavras**, e a seção metodológica sobre o
colapso + a codificação é, concordo com a torre, onde está o valor real do episódio.

---

## 4 · Resposta à pergunta 4 — a fase 1 está DOMINADA. Concordo integralmente

Mais forte do que a torre colocou. O ideal declarado da fase 1 é `[4/17 ; 202/690]` =
`[0,235294 ; 0,292754]`. O melhor alcançado hoje é `[1/17 ; 90/690]` = `[0,058824 ; 0,130435]`.

> **O dado real DOMINA o "ideal" nos DOIS eixos.**

Normalizando o melhor ponto sob a régua fase-1: **f₁_norm = −0,2308 · f₂_norm = −1,0666**. Valores
**negativos** — o ponto cai fora do hipercubo unitário e o HV com ref=(1,1) deixa de ter sentido.

**Um "ideal" dominado por dado real não é um ideal.** A fase 1 não deve ser usada **nem para
leitura preliminar**, e a obrigatoriedade da fase 2 pooled (D102.3) fica reforçada. Recomendo que
o selo `substituicao_obrigatoria` no `S5_ideal_nadir.json` seja acompanhado de um **guard
executável** que faça o cálculo de métrica do DDMOP7 falhar se a fase 1 ainda estiver ativa —
hoje o selo é declarativo, e declarativo é o que a T11 provou que passa verde.

---

## 5 · Resposta à pergunta 5 — sim, falta um teste. E ele custa ~1 hora

**Recomendo NÃO disparar as 1.890 antes destes três passos.** Os dois primeiros custam zero
oráculo.

### Passo 1 — decidir o espaço de registro (é decisão do autor, D81)

Duas opções, e a diferença é grande:

| | **(a) manter x_proposto** (hoje) | **(b) registrar x_efetivo** |
|---|---|---|
| o que o surrogate aprende | função com 8,5 direções planas por ponto | função contínua no espaço efetivo |
| aquisição por gradiente | estruturalmente penalizada | opera normalmente |
| dedup D89 | infla empates (x distintos, F idêntico) | correta |
| auditoria | efetivo é reconstrutível | proposto se perde (gravar os dois resolve) |
| custo | — | ~3 linhas: aplicar `zona_morta` **antes** de devolver ao chamador e gravar as duas colunas |

**Recomendo (b), gravando as duas colunas** (`x_proposto` e `x_efetivo`) na ①. Isso preserva a
auditabilidade que motivou a D102.17 **e** entrega ao algoritmo um alvo aprendível.

### Passo 2 — re-analisar o smoke que já rodou (zero CPU)

Contar, por célula, os **`x_efetivo` distintos** entre os pontos ND. Isso separa quanto da
inflação de empates é do problema e quanto é nosso (§1.1). Os dados já estão nas VMs.

### Passo 3 — o smoke decisivo (~55 min de oráculo, 1 célula)

**`c149`, semente 0, τ=0,5, com o registro em x_efetivo.** É o caso extremo: se sob (b) o c149
sair de 1/153 e passar a propor esparsidade, a leitura (B) do §1 está confirmada e a correção é
obrigatória antes das 1.890. Se ele continuar em ~1/153, a leitura (A) da torre se sustenta e eu
retiro a objeção.

**Um teste, uma célula, uma hora — e ele decide se 630 células do DDMOP7 vão medir o algoritmo ou
medir a nossa codificação.**

### O que eu NÃO peço

- **τ=0,6**: não é prioritário. O cálculo binomial continua válido e τ=0,5 cobre 83,5% da faixa do
  front. Se o Passo 3 mudar o quadro, τ se re-discute depois, com dado.
- **Segunda semente agora**: o desenho pareado (DoE compartilhado) já controla a maior fonte de
  variância. n=1 é limitação real, mas ela se resolve na campanha, não em smoke.
- **Cobertura offline sob codificação**: concordo que o gate não depende dela. Mas registre a
  lacuna no laudo — hoje ela é declarada só neste par de handoffs.

---

## 6 · Veredito recomendado

**GATE CUMPRIDO — SOLUÇÃO CONDICIONALMENTE VALIDADA.** A zona morta fez o que prometia: acabou com
a degenerescência, 13 de 15 configs melhoram o DoE, e um surrogate (c141) bate os pisos, o que era
estruturalmente impossível antes.

**Mas não recomendo o disparo das 1.890 ainda**, por um motivo que não estava no radar quando
escrevi o gate: **o registro em `x_proposto` entrega aos surrogates uma função constante por
partes, e isso penaliza sistematicamente as aquisições diferenciáveis.** O c149 é o caso extremo,
não a exceção — o c154 e o c262 usam a mesma mecânica e ficaram no teto de 2h, então não sabemos
onde eles cairiam com orçamento cheio.

Se o Passo 3 confirmar, o custo de não corrigir é alto e silencioso: a campanha mediria, em parte,
uma interação entre a nossa codificação e a mecânica de proposta de cada config — e essa é
exatamente a classe de artefato que uma banca de ponta procura.

**Três decisões suas (D97/D81):** o espaço de registro (§5.1) · se o Passo 3 roda antes do disparo
(recomendo que sim) · e se a fase 1 da régua ganha guard executável (§4).

---

*Medições próprias deste parecer: leitura de `src/ddmop7_bridge.py:118-160,528-556` e
`src/ddmop7_value_local.m:114-125`; aritmética da zona morta (D·τ, 1−τ^D); melhor f₂ do DoE
recomputado da ① local (`data/_quarentena_smokes/exp_main_c149_DDMOP7_0__real.parquet`,
110/690 = 0,159420296); domínio da régua fase-1 sobre `[1/17 ; 90/690]`. Não tive acesso às
células novas nas VMs — as tabelas do §2 e §4 do handoff da torre foram usadas como reportadas,
e as três checagens que dependem delas estão nomeadas como Passo 2 e Passo 3.*
