# SUPER HANDOFF — o resultado do smoke-gate da ZONA MORTA (DDMOP7)

> **De:** torre de controle · 2026-08-15
> **Para:** o agente de validação de fidelidade (o mesmo que produziu o
> `T15-LAUDO-FIDELIDADE-PROBLEMAS-REAIS.md` e diagnosticou o colapso do front)
> **Assunto:** você definiu o gate — *"1 config surrogate × 1 semente × τ=0,5, e
> medir se o ND vindo da busca sai de 0/340. Se sair, a solução está validada;
> se não sair, o problema é mais fundo que a codificação"*. O autor mandou rodar
> **20 células em paralelo** em vez de uma. Elas rodaram. Este documento traz o
> resultado inteiro, incluindo **uma ressalva que só apareceu na segunda
> medição** e que eu considero a informação mais importante daqui.
> **O que eu quero de você:** contestar o que está abaixo e responder às cinco
> perguntas do §6. Não preciso de concordância — preciso de refutação honesta.

---

## 1 · O QUE FOI RODADO (e o que não rodou)

**Bateria:** 20 células, DDMOP7, semente 0, τ=0,5, teto de 2 h, 10 por VM
(vm1 = us-east1-b, vm5 = us-east4-a), código no commit `3240f4b`.

| estado | n | quais |
|---|---|---|
| completas 526/526 | 11 | nsga2, nsga3, moead, smsemoa, b3, e7, c238 (vm1) · c217, c141, e74, e81 (vm5) |
| teto de 2 h, curva parcial | 4 | c149 (339 FE), c154 (208), c262 (398), c122 (425) |
| em voo ao fechar o laudo | 1 | b1 |
| **não rodaram** | 4 | e103, b5r, b5m, moead_media (offline) — **dataset da semente 0 ausente na vm5**: o Processo A distribuiu s0–s14 para a vm1 e s15–s28/42 para a vm5. Erro meu de despacho, não do código. A rota offline já fora validada em 14/08 (b5r/DDMOP7 com ⑦ de Engine real e portão 0-vermelhos), então o gate não depende dela — mas **a foto offline sob zona morta ainda não existe**. |

**Onde estão os dados** (para você re-medir): `~/ua-dd-saea/data/experiments/main/<alg>/exp_main_<alg>_DDMOP7_0*` nas duas VMs — camadas ①③④⑥ + `.jsonl` + manifesto. Os três scripts que produziram as tabelas abaixo estão em `~/analisa_gate.py`, `~/perfil_propostas.py` e `~/nd_distintos.py` nas duas VMs (código no scratchpad da sessão).

---

## 2 · O CRITÉRIO QUE VOCÊ DEFINIU: **CUMPRIDO**

Medição sobre a camada ①. **Nota metodológica importante:** a ① grava o x
**PROPOSTO** (decisão D102.17 — o efetivo é reconstrutível pela transformação
determinística). Logo, contar zeros na ① **não** mede a codificação; quem mede
é o `f₁`, que vem do oráculo e portanto enxerga o x **efetivo**.

| config | f₁<1 na busca | ND vindo da busca | melhor f₂ | (antes, sua medição: 0/340 · ND 0) |
|---|---|---|---|---|
| b3 | 340/340 | 195 | 0,140580 | |
| c262 | 212/212 | 202 | 0,144928 | teto |
| c217 | 333/340 | 172 | 0,140580 | |
| c141 | 322/340 | 79 | **0,130435** ← melhor global | |
| e74 | 214/340 | 82 | 0,144928 | |
| c122 | 238/239 | 34 | 0,159420 | teto |
| c154 | 22/22 | 7 | 0,144928 | teto |
| e7 | 331/340 | 6 | 0,143478 | |
| c238 | 183/340 | 2 | 0,144928 | |
| e81 | 303/340 | 2 | 0,150725 | |
| **c149** | **1/153** | **0** | 0,159420 (= o do DoE) | teto — ver §3 |
| nsga2 / nsga3 / moead / smsemoa (pisos) | 339–340/340 | 225 / 212 / 10 / 257 | 0,137681 / 0,137681 / 0,147826 / 0,140580 | |

**14 de 15 configs online passaram.** O critério binário que você fixou está
cumprido: a busca voltou a contribuir para o front.

---

## 3 · O c149 É RESULTADO, NÃO FALHA — e está medido

Verifiquei primeiro a hipótese de defeito: **a fronteira DoE/busca está correta
nele** — a primeira decisão de busca acontece em `fe=187`, idêntico ao c154, que
passou. Não é o caso de "os 186 primeiros da busca foram tratados como DoE".

O que explica é o **perfil das propostas** (fração das coordenadas que caem na
zona morta, por ponto proposto):

| config | coords com \|x\|<τ | nnz médio efetivo | leitura |
|---|---|---|---|
| **c149** | **1,2 %** | **16,8 de 17** | propõe nos extremos da caixa — rede quase cheia |
| c238 | 51,8 % | 8,2 | |
| e7 | 66,0 % | 5,8 | |
| moead | 84,5 % | 2,6 | |
| b3 / c154 | 89,3 / 89,6 % | 1,8 | |
| nsga3 / smsemoa / nsga2 | 91,0 / 92,1 / 92,2 % | 1,5 / 1,3 / 1,3 | |

A codificação é idêntica para todos; **a aquisição de cada um decide se a usa**.
A do c149 (deep ensemble + desempate por σ) empurra para as bordas de
`[−1,1]¹⁷`, onde a incerteza do ensemble é máxima — e borda não é esparsidade.
**Interpretação da torre** (não é fato medido, é leitura): isso é precisamente o
tipo de comportamento que o problema deveria discriminar, e antes da codificação
era invisível — todos pareciam iguais.

---

## 4 · 🔴 A RESSALVA QUE SÓ APARECEU NA SEGUNDA MEDIÇÃO — leia antes de opinar

Ao ver `|ND| = 257` no smsemoa, desconfiei: `f₁ = k/17` tem no máximo 18 valores
possíveis, então um front com 257 pontos **distintos** é impossível. Medi os
valores **distintos** no espaço de objetivos:

| config | \|ND\| bruto | ND com valores **DISTINTOS** | distintos vindos da busca | faixa de k no front |
|---|---|---|---|---|
| c122 | 35 | **6** | 5 | 1..10 |
| c141 | 79 | **4** | 4 | 3..17 |
| nsga2 / nsga3 | 225 / 212 | **4 / 4** | 4 / 4 | 1..5 |
| c149 | 3 | 3 | **0** | 5..10 |
| e7 / moead / smsemoa / c217 / e81 | 6 / 10 / 257 / 172 / 3 | **3** cada | 3 / 3 / 3 / 3 / 2 | 1..4 (e81: 5..9) |
| b3 / c238 / c262 | 195 / 2 / 202 | **2 / 2 / 2** | 2 / 2 / 2 | 1..4 |
| c154 / e74 | 7 / 82 | **1 / 1** | 1 / 1 | 3..3 |

**O `|ND|` bruto é quase todo empate.** O front efetivo de cada célula tem
**1 a 6 pontos distintos** — mediana 3. Isso não é defeito da zona morta: é a
quantização do problema (18 degraus possíveis, e o front real do próprio
conjunto de dados oficial tem 9 pontos, como você mediu). Mas tem consequência
direta para a análise do capítulo 5:

- o **HV do DDMOP7 medirá essencialmente o melhor compromisso alcançado**
  (o par $(k_{\min}, f_2)$ da ponta), não a qualidade da distribuição do front;
- a **faixa de discriminação existe mas é estreita**: melhor f₂ vai de 0,1304
  (c141) a 0,1594 (c149, que é o valor do DoE) — cerca de 18 % de amplitude
  relativa; o k mínimo alcançado vai de 1 a 5;
- **a comparação deixou de ser degenerada** (antes: os 13 online produziriam o
  mesmo front, do DoE compartilhado, com HV idêntico), **mas continua de baixa
  resolução** por natureza do problema.

Em uma frase: **a zona morta consertou a degenerescência, não a quantização** —
e a quantização é o problema, não nós.

---

## 5 · O QUE EU **NÃO** CONSEGUI PROVAR (limites honestos deste smoke)

1. **n = 1 semente.** Tudo acima é a semente 0. Não sei se a ordenação entre
   configs se mantém em 30 sementes — e o desenho pareado (DoE compartilhado)
   ajuda, mas não substitui repetição.
2. **4 células no teto de 2 h** (c149, c154, c262, c122) — curvas parciais. O
   c149, em especial, viu apenas 153 propostas; não posso afirmar que ele
   *nunca* proporia esparsidade com o orçamento completo, apenas que em 153
   propostas não propôs (1/153).
3. **Zero cobertura offline sob zona morta** (§1) — a ⑦ pós-hoc com codificação
   foi validada por teste unitário e pela rota do 14/08, não por célula real
   nova.
4. **Nada aqui é fidelidade.** Continua valendo o que este handoff sempre disse:
   os portões que rodei são mecânicos. Se a codificação é ou não uma
   intervenção legítima sobre um benchmark canônico é julgamento do autor,
   informado por você.
5. **τ = 0,5 não foi comparado empiricamente com τ = 0,6.** A escolha segue o
   cálculo binomial do seu laudo. Um smoke com τ=0,6 custaria ~1 h e diria se a
   faixa de k útil melhora.

---

## 6 · AS CINCO PERGUNTAS QUE EU QUERO QUE VOCÊ RESPONDA

1. **O gate está cumprido na sua régua?** Você fixou "ND da busca sai de 0/340".
   Saiu em 14/15. Isso valida a solução no seu critério — ou o critério deveria
   ser mais exigente à luz do §4 (ex.: exigir que os pontos da busca sejam
   distintos e melhorem o melhor f₂ do DoE, e não apenas entrem no front)?
2. **O §4 muda o veredito sobre a vaga B?** Com front efetivo de 1–6 pontos
   distintos e HV dominado pela ponta, o DDMOP7 volta a ser *problema de
   comparação pleno*, ou a sua recomendação original (estudo de caso declarado)
   continua de pé — agora com a codificação como parte da história?
3. **A leitura do c149 é defensável?** Eu afirmo "a aquisição escolhe os
   extremos, e isso é o problema discriminando". A leitura alternativa é
   "a codificação favorece operadores que já produziam esparsidade (crossover) e
   penaliza aquisições de fronteira" — o que seria um viés introduzido por nós.
   **Qual das duas o dado sustenta?** Esta é a pergunta que mais me preocupa.
4. **A régua fase-2 muda?** Os valores agora alcançados (k mínimo 1, f₂ até
   0,1304) são melhores que o `ideal` da régua provisória fase-1
   (`[4/17, 202/690]` = `[0,2353, 0,2928]`) em f₁ e piores em f₂. Isso reforça
   a obrigatoriedade da fase 2 pooled (D102.3) — concorda que a fase 1 não deve
   ser usada nem para leitura preliminar?
5. **Falta algum teste antes das 1.890 células?** Custo: cada célula DDMOP7
   online = ~55 min de oráculo; a onda inteira do DDMOP7 são ~630 células
   (21 configs × 30 sementes). Se você recomendar um teste adicional (τ=0,6, uma
   segunda semente, o offline sob codificação), ele cabe ANTES do disparo.

---

## 7 · O VEREDITO DA TORRE (para você contestar)

**Aprovo o resultado do gate, com a ressalva do §4 explícita.** O que a
codificação prometia entregar, entregou: a busca voltou a contribuir, a
comparação deixou de ser degenerada, e o comportamento que separa os configs é
mensurável e explicável. O que ela não prometia — e não entregou — é resolução:
o DDMOP7 continua sendo um problema de front curto, e qualquer análise do
capítulo 5 sobre ele deve dizer isso com essas palavras. **Recomendo o disparo
das 1.890 células**, com o DDMOP7 entrando como problema de comparação **de
resolução declaradamente baixa** — e com a seção da dissertação sobre o colapso
e a codificação escrita como contribuição metodológica, que é onde o valor real
deste episódio está.

*Evidência bruta, scripts e caminhos: §1. Registro da decisão: `REGISTRO_DECISOES_IMPLEMENTACAO.md` PARTES A51 (implementação) e A52 (este gate). Código: commit `3240f4b`.*
