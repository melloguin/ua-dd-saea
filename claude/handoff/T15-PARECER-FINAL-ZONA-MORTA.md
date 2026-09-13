# PARECER FINAL — gate da zona morta, agora com os dados medidos

**De:** torre de validação de fidelidade · **Para:** torre central · **Data:** 2026-08-15
**Substitui:** `T15-PARECER-FIDELIDADE-ZONA-MORTA.md` (escrito **sem** acesso aos artefatos)
**Corpus:** 15 células, 42 MB, puxadas das vm1/vm5 e re-medidas por mim aqui

> **APROVO O GATE, SEM RESSALVA DE MECANISMO. Recomendo o disparo das 1.890.**
> **As duas objeções do meu parecer anterior estão REFUTADAS pelo dado** — a primeira
> integralmente, a segunda no que importava. Registro os dois erros abaixo.

---

## 1 · Erro nº 1, meu — o `c149` já morava na borda

Eu afirmei que a zona morta **empurrava** as aquisições diferenciáveis para a fronteira da
caixa, e que o `c149` era o caso extremo desse viés. Construí o argumento lendo o código
(`ddmop7_bridge.py:538`) e a aritmética dos platôs (8,5 direções planas de 17), sem tocar em dado.

**O teste que decide** eu não tinha feito: comparar o perfil de propostas do `c149` **antes** e
**depois** da zona morta. Tenho os dois corpora — o smoke pré-codificação de 14/08 e o de agora:

| config | corpus | n busca | \|x\|<0,5 | **\|x\|>0,9** | mediana \|x\| | nnz efetivo |
|---|---|---:|---:|---:|---:|---:|
| **c149** | **ANTES** (sem zona morta) | 340 | 2,8% | **83,3%** | **0,979** | 16,5 |
| **c149** | **DEPOIS** (τ=0,5) | 153 | 1,2% | **90,3%** | **0,990** | 16,8 |
| nsga2 | ANTES | 340 | 89,4% | 4,4% | 0,000 | 1,8 |
| nsga2 | DEPOIS | 340 | 92,2% | 1,8% | 0,011 | 1,3 |

**O perfil é o mesmo nos dois lados.** O `c149` propunha 83,3% das coordenadas na borda **antes de
a codificação existir**. A zona morta não o levou para lá — é a aquisição dele (deep ensemble com
desempate por σ, que maximiza incerteza, e incerteza é máxima na extrapolação) que mora lá.

> **A leitura (A) da torre está correta: é o problema discriminando, não viés nosso.**
> A codificação é neutra em relação a *onde* cada algoritmo propõe; ela só muda o que acontece
> com os valores pequenos que ele já propunha. Quem nunca propõe pequeno nunca a usa.

Meu argumento dos platôs era sobre uma função que o surrogate **de fato** tem de aprender, mas eu
saltei um passo: o surrogate não conhece a zona morta, ele ajusta um modelo suave a amostras. Se
as amostras quase nunca caem na região colapsada — e no `c149` caem em 1,2% —, o modelo nunca
enxerga o platô. **A premissa era correta e a conclusão não seguia dela.**

## 2 · Erro nº 2, meu — a inflação de empates é em parte nossa, mas isso não muda nada

Eu disse que a baixa resolução do §4 era, em parte, artefato do registro em `x_proposto`. Medi:

| config | \|ND\| bruto | `x_proposto` distintos | `x_efetivo` distintos | **F distintos** |
|---|---:|---:|---:|---:|
| smsemoa | 257 | 257 | 99 (**61% colapsa**) | **3** |
| nsga2 | 225 | 223 | 86 (61%) | **4** |
| nsga3 | 212 | 209 | 64 (69%) | **4** |
| c217 | 172 | 172 | 69 (60%) | **3** |
| e74 | 82 | 82 | 27 (67%) | **1** |
| **b3** | 195 | 195 | **180 (só 8%)** | **2** |
| **c141** | 79 | 79 | **72 (só 9%)** | **4** |
| **c262** | 202 | 202 | **180 (11%)** | **2** |

**O colapso existe e chega a 70% nos operadores de população.** Mas olhe a última coluna: o `b3`
tem **180 pontos efetivos distintos** e ainda assim **só 2 valores objetivo distintos**. O `c262`,
180 efetivos e 2 valores. **A baixa resolução não vem do nosso registro — vem da quantização do
problema**, exatamente como a torre atribuiu.

Minha ressalva estava tecnicamente certa e **praticamente irrelevante**: corrigir o registro
deixaria o `|ND|` honesto (deixaria de contar 257 quando são 99 pontos reais), mas **não
aumentaria a resolução em uma única unidade**. O §4 da torre está certo no que decide.

---

## 3 · O que eu medi, e confirma a torre em cada linha

Re-medi as 15 células com código meu, sem usar as tabelas do handoff:

| checagem | resultado | a torre reportou |
|---|---|---|
| `f₁ = k/17` e `f₂ = n/690` | **15/15 células, 100% dos pontos** (tolerância float32) | — |
| **o gate que eu fixei** (ND da busca > 0) | **14/15** | 14/15 ✅ |
| **régua forte** (melhora o melhor f₂ do DoE = 110/690) | **13/15** — falham `c122` e `c149`, que empatam *exatamente* com o DoE | (não medida) |
| `\|ND\|` **distinto** | min 1 · **mediana 3** · max 6 | 1–6, mediana 3 ✅ |
| melhor f₂ global | **`c141` = 90/690 = 0,130435** — bate os 4 pisos (95–102/690) | 0,130435 ✅ |
| `c149` | ND da busca **0**, melhor f₂ = **110/690 = o do DoE** | 0 e 0,159420 ✅ |
| ⑥ íntegro | 15/15 com rodapé; estados `ok` (10), `teto_wall` (4), `orçamento` (1) | ✅ |

**Não achei uma divergência.** As tabelas do handoff da torre reproduzem número por número.

---

## 4 · Resposta final às 5 perguntas

1. **O gate está cumprido?** **Sim** — no critério que fixei (14/15) e no critério mais forte que
   a torre sugeriu e eu adotei (13/15). Os 2 que não passam na régua forte são exatamente os 2 que
   a torre já havia nomeado. A evidência é internamente coerente.
2. **O §4 muda o veredito da vaga B?** **Muda o meu anterior**, para melhor: o DDMOP7 volta a ser
   **problema de comparação legítimo** — a degenerescência acabou (antes os 13 online terminavam
   com o mesmo front do DoE compartilhado). Fica de pé a ressalva de **resolução baixa**, e ela é
   do problema: front efetivo de 1–6 pontos, amplitude do melhor f₂ de 20 degraus em 690.
3. **A leitura do `c149` é defensável?** **Sim, e a minha era a errada** — §1.
4. **A régua fase-1 muda?** **Sim, e é o único item onde eu insisto.** O ideal declarado
   `[4/17 ; 202/690]` é **dominado nos dois eixos** pelo alcançado `[1/17 ; 90/690]`; normalizado,
   o melhor ponto dá `f₁_norm = −0,23` e `f₂_norm = −1,07`. Um ideal dominado por dado real não é
   ideal. **Fase 2 pooled é obrigatória, e recomendo trocar o selo declarativo por guard
   executável** (a T11 provou que selo declarativo passa verde).
5. **Falta teste antes das 1.890?** **Não, nenhum bloqueante.** Retiro o Passo 3 que eu havia
   pedido — o teste before/after do §1 já respondeu o que ele responderia, a custo zero.
   Ficam **duas recomendações não-bloqueantes**: (i) gravar `x_efetivo` ao lado do `x_proposto` na
   ①, para que o `|ND|` publicado seja honesto (~3 linhas, não muda comportamento, e evita que um
   revisor encontre 257 pontos onde há 99); (ii) rodar a foto offline sob codificação quando o
   dataset s0 estiver na máquina certa — hoje essa lacuna só existe declarada em handoff.

---

## 5 · Veredito

**GATE VERDE. Aprovo. Recomendo o disparo das 1.890 células.**

O DDMOP7 entra como **problema de comparação de resolução declaradamente baixa** — e a seção
metodológica sobre o colapso, o diagnóstico e a codificação é, concordo com a torre, onde está o
valor real deste episódio. Sugiro que o texto registre as três medições que sustentam a história:
o colapso original (0/340 do `c149` pré-codificação), a recuperação (13/15 melhoram o DoE) e o
limite honesto (front efetivo de 1–6 pontos, que é do benchmark).

**Registro de método, para mim:** errei duas vezes neste episódio, e as duas por analisar o código
e a aritmética em vez do dado. É exatamente o padrão que o Agente 8 descreveu no §9 dele —
*"analisei a lembrança em vez da fonte"* — e que eu cobrei da campanha T11. O corretivo foi ter
acesso aos artefatos: 42 MB e três medições resolveram o que dois documentos de argumentação não
resolveram.

---

*Medições: `~/Downloads/d7_smokes/` (15 células puxadas de vm1/vm5 em 15/08). Comparativo
antes/depois usa `ua-dd-saea/data/_quarentena_smokes/` como corpus pré-codificação. Scripts na
transcrição da sessão. Nenhum arquivo do repo ou das VMs foi alterado.*
