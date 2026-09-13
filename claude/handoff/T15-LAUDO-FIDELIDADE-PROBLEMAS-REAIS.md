# LAUDO DE FIDELIDADE — os 3 problemas de dados reais (T15)

**De:** torre de validação de fidelidade · **Para:** torre central de implementação
**Data:** 2026-08-14 · **Doutrina:** D97 — analiso e recomendo; **o veredito é do autor**
**Corpus:** 13 células-smoke em `data/_quarentena_smokes/` + o pacote de fusão do Agente 8
**Método:** 11 agentes independentes + medição direta minha. Nada aceito do handoff sem re-medir.

> **O autor já cravou a decisão do §3 deste laudo.** A torre executa o §4.

---

## 1. Veredito recomendado, em uma tela

| problema | score | veredito | classe (3) | bloqueia o disparo? |
|---|:--:|---|:--:|---|
| **RE21** (D=4) | **9,4** | ACEITAR | 3, todos documentais | não |
| **ESTOQUE40** (D=40) | **9,2** | ACEITAR | 1, de régua (afeta a R4, não a execução) | não |
| **DDMOP7** (D=17) | **8,0** | ACEITAR a formulação, **com 2 bloqueadores** | 7 | **SIM — dois** |
| **pisos** (nsga2 · moead_media) | **7,0** | APROVAR os 3 online · **SEGURAR o offline** | 2 | **SIM — um** |
| caveats + bateria universal | 49/52 = **94,2%** | 3 caveats do handoff precisam de correção | 11 | não |

**A formulação dos três problemas está certa.** O que trava o disparo são **três bloqueadores**:
o **colapso do front do DDMOP7 sob busca contínua** (§2), a **⑦ estruturalmente impossível** (§5),
e o **piso offline congelado no ESTOQUE40** (§6.3).

---

## 2. 🔴 O PROBLEMA CENTRAL — o DDMOP7 não mede otimização multiobjetivo

### 2.1 A mecânica

`f₁ = k/17`, onde **k é o número de pesos NÃO-ZERO da rede depois do treino interno** do `.p`.
O corte é **zero exato — não existe ε** (medido no probe v6: `x = 1e-4·(1,…,1)` já dá f₁ = 1,0).
Otimizador contínuo nunca propõe zero exato ⇒ fica preso em f₁ = 1,0.

Vocês **sabiam disto** e mitigaram: **D102.1** (DoE = os 30 sorteios oficiais do `init`) e
**D102.9** (dataset offline = 3 sorteios concatenados). O motivo está escrito no B-6: *"LHS em
[−1,1]¹⁷ nunca produz zero exato ⇒ f1 ≡ 1, o ND final teria 1 ponto, e o HV não existiria"*.

### 2.2 A mitigação funcionou — e não sobrevive à busca

**Medi na camada ①, separando por fase:**

| célula | fase | pontos c/ zero exato | f₁ < 1 | ND do DoE | ND da busca |
|---|---|---|---|---|---|
| **c149** (surrogate) | init 186 | 186 (100%) | 87 (46,8%) | **3** | — |
| | **opt 340** | **0 (0,0%)** | **0 (0,0%)** | | **0** |
| **nsga2** (piso GA) | init 186 | 186 (100%) | 87 (46,8%) | 1 | — |
| | **opt 340** | **340 (100%)** | **320 (94,1%)** | | **14** |
| **b5r** (offline) | dataset 526 | 526 (100%) | 245 (46,6%) | 9 | — |

O DoE tem a esparsidade que os autores programaram — **100% dos pontos** com ao menos um zero
exato. Mas o SBX/PM do GA **herda e preserva** os zeros (94% dos filhos continuam esparsos, e 14
dos 15 pontos do front vêm da busca), enquanto a **aquisição contínua destrói todos** — 0 de 340.

### 2.3 As três consequências, cada uma medida

**(a) Os 13 configs online compartilham o mesmo DoE.** Confirmei: `max|ΔX| = 0.000e+00` exato
entre `c149` e `nsga2`. Se a busca surrogate não contribui, **os 13 terminam com o mesmo front —
o do DoE — e o mesmo HV.** A comparação entre eles não tem sinal nenhum.

**(b) A busca surrogate não melhorou nada, em nenhum eixo.** O melhor f₂ do `c149` (0,159420) é
**exatamente** o melhor f₂ do DoE. Dentro da fatia f₁=1 ela melhora +29,47% (0,275362 → 0,194203)
— mas essa fatia inteira é **dominada** por um ponto do DoE. Testei mover o ref-point para
1,1×znad: **não recupera nada** (ponto dominado não contribui HV sob régua nenhuma).

**(c) O colapso atinge os DOIS regimes, não só o online.** A ⑦ do `b5r` offline — o *endpoint
oficial* do regime — tem **47 finais com f₁ = 1,0 exato em 47/47**. Isso **refuta** a leitura do
`T15-HANDOFF-FIDELIDADE-SMOKES.md` §1 linha 8 (*"2 ND pós-real, coerente com o front de ~4 pontos
esperado pela quantização"*): os 2 ND não estão espalhados pela escada, estão os dois no canto
degenerado, diferindo só em f₂.

**Custo do que não mede nada:** 340 FE × 6,267 s = **35,5 min por run**; nos 13 online × 30
sementes = **231 h-core ≈ 9,6 core-dias**.

### 2.4 Isto NÃO é infidelidade

O problema replica o binário oficial corretamente — provei: `f₁ = k/17` e `f₂ = n/690` fecham com
erro **0,0 EXATO em float64** nos 526 pontos do dataset e 3e-16 nos 62 do probe. É uma
**característica estrutural do benchmark**, corretamente prevista pelo Agente 8 (`B-16c`:
*"o HV do DDMOP7 separa por CLASSE DE OPERADOR, não por qualidade de busca"*, elevando a D102.8 de
risco a **expectativa estrutural quase-certa**). O que este laudo acrescenta é a **confirmação
empírica em dado real**, com o número: **0/340 vs 320/340**.

---

## 3. As soluções discutidas, e a que ficou

O autor decidiu **manter o DDMOP7 com o avaliador oficial** (a rede neural, o `.p`). Isso descarta
de saída as opções que trocam o avaliador. As cinco alternativas avaliadas, com número:

| # | opção | veredito | por quê |
|---|---|---|---|
| 1 | **Trocar o avaliador** (Opção 1 do `ddmop7_VEREDICTO.md` §9: f₁ = média dos quadrados dos pesos, f₂ = erro da rede como dada) | ❌ **descartada pelo autor** | Funciona — implementei e testei: f₁ com **526/526 valores distintos**, \|ND\|=9 com os 9 vindos da busca, **17,4 µs/aval** (360.000× mais rápido, campanha em 6 s). Mas **perde o selo canônico** da vaga B |
| 2 | **Mover o ref-point** (1,1×znad) | ❌ **refutada por medição** | A busca continua somando `0.000000`. Ponto **dominado** não contribui HV sob régua nenhuma. Hipótese minha, derrubada pelo próprio teste |
| 3 | **Fixar as variáveis que "têm que ser zero"** e otimizar só o resto | ❌ **impossível como formulado** | Medi nos 9 pontos do front: **nenhuma** coordenada é zero em todos, **nenhuma** é não-zero em todos. O suporte **muda ao longo do front** — *quais* zerar **é** a decisão de f₁. Fixar um suporte = escolher um ponto do front antes de otimizar |
| 4 | **Codificação por portão** (17 pesos + 17 gates) | ❌ **cara demais** | D vai 17→34 ⇒ maxFE 526→**1.053**, custo **dobra** (25,2 → 50,4 core-dias), e a escada 4→17→40 vira 4→34→40 (o degrau do meio some) |
| 5 | **✅ ZONA MORTA na codificação** | ✅ **ADOTADA** | Ver §4 |

### 3.1 Por que a ideia (3) não fecha — a medição

Os 9 pontos do front do dataset oficial:

| k = f₁·17 | f₂ | nnz(x) | **Δ = k − nnz** | zeros em x |
|---|---|---|---|---|
| 4/17 | 0,4449 | 3 | **+1** | 14 coordenadas |
| 5/17 | 0,3971 | 3 | **+2** | 14 |
| 6/17 | 0,3377 | 4 | **+2** | 13 |
| 8/17 | 0,2841 | 6 | **+2** | 11 |
| 9/17 | 0,2464 | 7 | **+2** | 10 |
| 10/17 | 0,1971 | 9 | **+1** | 8 |
| 11/17 | 0,1928 | 10 | **+1** | 7 |

**O front vive entre k=4 e k=11** — ou seja, **6 a 13 dos 17 pesos precisam terminar zero**, e
`nnz(x)` na entrada vai de **2 a 10**.

E aqui está o fato que **habilita a solução**: no geral o `Δ = k − nnz(x)` é caótico (1 a 14,
mediana 5, sempre ≥ 0 — o treino nunca poda, só acrescenta), **mas na região do front ele é +1 ou
+2, sempre**. Ou seja: **controlando `nnz(x)` você controla o f₁ exatamente onde importa.** A cota
inferior `nnz(x)/17` é frouxa no geral e **apertada no front**.

---

## 4. ✅ A SOLUÇÃO DEFINIDA — zona morta na codificação

### 4.1 O quê

Antes de chamar o `.p`, aplicar coordenada a coordenada:

```
x_efetivo[i] = 0        se |x_proposto[i]| < τ
x_efetivo[i] = x_proposto[i]   caso contrário
```

**Não é reparo escondido — é uma codificação declarada**, aplicada **identicamente aos 21
configs** (surrogates, pisos, online e offline), de modo que a comparação segue justa.

### 4.2 Por que funciona, e o τ

Com `x ~ U[−1,1]¹⁷`, `P(|x_i| < τ) = τ`, logo `nnz ~ Binomial(17, 1−τ)`. Medi:

| τ | E[nnz] | faixa 5–95% | % dentro de [2,10] (a faixa do front) |
|---|---|---|---|
| 0,1 | 15,3 | [13, 17] | 0,1% |
| 0,3 | 11,9 | [9, 15] | 22,6% |
| **0,5** | **8,5** | **[5, 12]** | **83,5%** |
| **0,6** | **6,8** | **[4, 10]** | **96,4%** |
| 0,7 | 5,1 | [2, 8] | 97,8% |

**Recomendo τ ∈ [0,5 ; 0,6].** Nenhuma região fica proibida: `nnz = 0` e `nnz = 17` continuam
alcançáveis dentro da caixa. E como `Δ = +1/+2` no front, `nnz(x)` nessa faixa produz `k` na faixa
do front.

### 4.3 O que NÃO muda

**D continua 17** · **maxFE continua 526 = 31D−1** · **o grid não muda** · **a escada 4→17→40 fica
intacta** · **o oráculo oficial continua sendo o oráculo** · **o selo canônico da vaga B é
preservado** · **os 30 sorteios congelados continuam válidos** (já têm zeros exatos; a zona morta
é idempotente sobre eles se τ não zerar coordenadas legítimas — **verificar**, ver §4.5).

O que muda é uma coisa só: **a aquisição contínua passa a conseguir propor esparsidade**.

### 4.4 O que a torre precisa implementar

| # | item | onde | custo |
|---|---|---|---|
| 1 | A transformação de zona morta, no ponto único de entrada do avaliador — as **3 rotas** (R1 nativa, R2 ponte, replay offline pós-hoc) | `src/ddmop7_bridge.py` (R2 + motor), `src/ddmop7_value_local.m` (R1), `scripts/final_eval.py` (⑦) | ~10 linhas × 3 sítios |
| 2 | **Gravar os DOIS x na camada ①** — `x_proposto` e `x_efetivo` | schema da ① | quebra a **D89** (identidade do ponto = X bit-a-bit) se só um for gravado — ver §4.5 |
| 3 | Registrar `tau_zona_morta` no `sigma_dict` do ⑤ e no `params` | `_sigma_dict()` dos runners do DDMOP7 | 1 linha |
| 4 | Registrar a decisão como **REAL-2.15 / D102.15** | `docs/DECISOES_REAL_D101_D102.md` + `gen_artifacts_delta_D87_D88.py` | texto |

### 4.5 🔴 As três coisas que precisam ser resolvidas ANTES de comprometer as 30 sementes

**(i) A quebra da D89.** Hoje a identidade do ponto é X bit-a-bit. Com zona morta, `x_proposto ≠
x_efetivo`. A dedup e o cache-hit passam a operar sobre qual? **Recomendo: dedup sobre
`x_efetivo`** (é o que o oráculo vê, e é o que a D89 quer proteger), **gravando os dois**. Sem
isso, a auditoria futura vê incoerência entre o que o algoritmo escolheu e o que foi avaliado.

**(ii) A idempotência sobre o DoE congelado.** Os 30 sorteios oficiais já têm ~49,4% de zeros
exatos, mas as coordenadas **não-zero** deles podem ter |x| < τ e seriam zeradas pela transformação
— o que **mudaria o DoE**. Medir antes: quantas coordenadas não-zero do DoE congelado têm |x| < τ?
Se for significativo, a zona morta deve ser aplicada **só aos pontos propostos pela busca**, não ao
DoE (que já é esparso por construção). **Recomendo essa segunda leitura**, e ela precisa estar no
texto da D102.15.

**(iii) O smoke de validação — e este é o gate.** Eu **não posso provar** aqui que a zona morta
funciona no oráculo real: provei que ela produz `nnz` na faixa certa e que `Δ = +1/+2` nessa
região, mas o `.p` treina por dentro e só ele diz o `k` final.

> **O teste honesto: 1 config surrogate × 1 semente × τ=0,5, e medir se o ND vindo da busca sai de
> 0/340.** Custo: ~55 min de MATLAB. **Se sair, a solução está validada; se não sair, o problema é
> mais fundo do que a codificação e voltamos à mesa.** Não disparar as 1.890 células antes disso.

---

## 5. 🔴 O SEGUNDO BLOQUEADOR DO DDMOP7 — a ⑦ é estruturalmente impossível

**Achado independente, confirmado por mim no código e no dado.**

`scripts/final_eval.py:196-199` levanta `RuntimeError` quando a ⑦ teria mais de 600 pontos
(`P_CODE_CAP`, teto de chamadas do `.p` por processo, D88.5). A mensagem diz *"|ND| offline
esperado é ~10²; isto indica ③ corrompida. Pára-e-loga (D81)"*.

**Medido:**

| célula | última geração da ③ | linhas nela | resultado |
|---|---|---|---|
| `c149` | 340 | **1.000** | **RECUSA — RuntimeError** |
| `b5r` | 928 | 47 | passa |

A ③ **não está corrompida** — o `c149` tem população 1.000 por desenho. **O `b5r` só passou por
acidente**, porque a ③ dele terminou com 47 linhas. Qualquer config de população grande vai
estourar na campanha, e **nenhuma decisão D101/D102 cobre o caso**.

**Opções para o autor:** (a) filtrar a última geração por não-dominância antes de avaliar (o mais
natural — a ⑦ quer o front, não a população); (b) fatiar em múltiplos processos; (c) truncar por
um critério declarado. **Recomendo (a)**, que é o que a mensagem de erro já pressupõe ao dizer
"|ND| esperado ~10²".

---

## 6. Os outros dois problemas

### 6.1 RE21 — score 9,4 · ACEITAR

**A query-joia fecha no nível mais forte que existe.** O agente reimplementou o four-bar truss do
zero, a partir do artigo, sem olhar `src/problems.py` nem `reproblem_official.py`, e o F produzido
é **idêntico bit-a-bit ao gravado em 20.825 pontos float64** (20.000 da sonda + 123 do dataset
offline + 702 do front D72), com **erro absoluto máximo 0,0 EXATO — zero ULP**. O sha256 dos bytes
float64 reproduz o `f_hash` congelado no manifesto.

21 aspectos: **17 classe (1) · 2 classe (2) · 1 classe (3) · 1 T**. Constantes (F=10, σ=10,
E=2,0e5, L=200) idênticas token a token; limites `x1,x4 ∈ [1,3]` e `x2,x3 ∈ [√2,3]` bit-idênticos
a `np.sqrt(2.0)`.

**O que impede o 10 — e é um item que a banca checa:**

> 🎯 **T01 — o artigo designado NÃO define o problema.** Nas 21 páginas do PDF de Tanabe &
> Ishibuchi, o RE2-4-1 só aparece na Tabela 2 (p.7) com `M=2, D=4, Continuous, Convex`. A §2.2
> (p.6) diz literalmente que **só o RE2-3-2 é detalhado no corpo**, e manda os outros 15 para a
> **Seção S.1.1 do arquivo SUPLEMENTAR — que não está no acervo**. A fonte primária [24] Cheng &
> Li (1999) também não está.

Isso **não afeta a fidelidade** (a implementação está provada contra o código oficial da suíte),
mas **afeta a cadeia de citação da dissertação**. Recomendo baixar o suplementar e/ou o Cheng & Li
e citar a fonte que de fato contém a formulação.

Os 2 classe-(3) restantes são menores: um número de cross-check IGD⁺ na docstring
(`src/problems.py:1420`) que aponta para um front que o repo não entrega, e um X órfão na ⑦ do
`e103` (rastreabilidade de proveniência, com o próprio sidecar já admitindo perda float32).

### 6.2 ESTOQUE40 — score 9,2 · ACEITAR

**A cadeia inteira reproduz.** O agente re-derivou o `estoque_problem.npz` a partir do XLSX cru
(sha `bcbe73b3…`) e o arquivo saiu **bit-a-bit idêntico** ao congelado (sha `660b5896…`
reproduzido), num pandas/numpy diferente do que o gerou.

**A query-joia fecha no nível mais forte possível:** na rota online, a `①.F` é *literalmente*
`float32(f(DoE_float64))`, com `np.array_equal = True` nas 3 células main; na rota offline, o erro
relativo máximo sobre 37.170 pontos float64 é **1,02e-15** em f₁.

31 aspectos: **23 classe (1) · 4 classe (2) · 1 classe (3) · 3 T**.

**A regra da categoria — o pior erro do Agente 8 — está certa no dado.** Confirmei eu mesma:
ordem-lexicográfica mod 8 acerta **40/40**; "dígitos mod 8" acerta **5/40**, exatamente como o
documento declara. O exemplo bate ao dígito: `84077` → família `840` → rank 18 → categoria 2.
Também confirmados: `f₁ < 0` em 5.720/5.720 (receita negada), janela de 106 semanas sem grau de
liberdade, chaves do `.npz`.

**O único classe (3) — e ele afeta a R4, não o disparo:**

> 🎯 **C3-01 — a régua D69 é mais curta que o front verdadeiro nos três objetivos**: f₁ por
> 424,515 (2,37%), f₂ por 183,961 e f₃ por 2,171e-04. Os pontos que a furam são os **dois cantos
> da caixa** (`x=0` e `x=xu`), que qualquer operador de reparo aos bounds alcança de graça. Nos 5
> smokes nenhum ponto fica abaixo do ideal, então o efeito é **benigno hoje** — mas com 30
> sementes e 21 configs a chance de alguém tocar um canto é alta, e aí o HV normalizado passa de 1.

**Três itens que o agente escala a você** (nenhum bloqueia o disparo): o rótulo `concave_front=1`
no `characteristics.csv` (a medição no front D72 dá curvatura **mista**: 47,0% côncavo / 53,0%
convexo); a dimensionalidade efetiva em D=40; e a redação da procedência — o artigo `real3` tem
**zero ocorrências** de "optimization/objective/constraint/bound", o que confirma que a formulação
é 100% nossa e precisa ser escrita assim, sem sugerir que o problema veio do artigo.

### 6.3 🔴 TERCEIRO BLOQUEADOR — o piso OFFLINE está congelado no ESTOQUE40

**Achado do agente dos pisos, confirmado por mim na camada ③.** O `moead_media/ESTOQUE40` — que
é a **régua do regime offline** — **não otimizou absolutamente nada**:

| célula | gerações | pop | transições COM mudança | ger₁ == ger_N? |
|---|---|---|---|---|
| **`moead_media/ESTOQUE40`** | 381 | 105 | **0 / 380 (0,0%)** | **sim — idêntica** |
| `b5r/ESTOQUE40` (mesmo problema, mesmo regime) | 6.284 | 105 | 6.272 / 6.283 (99,8%) | não |
| `b5r/RE21` | 19.810 | 50 | 15.702 / 19.809 (79,3%) | não |

**A população da geração 1 é idêntica à da geração 381**, nas 380 transições, com 39.900
tentativas de substituição rejeitadas.

**Causa diagnosticada pelo agente:** o `SurrogateKriging` do DESDEO — que a **DI-28 obriga a
manter com "a MESMA ESPECIFICAÇÃO do b5"** — usa kernel `C(1,(1e-3,1e3))*RBF(10,(1e-2,1e2))` com
`normalize_y=False`. A `length_scale` máxima admissível (**100**) é **uma a duas ordens de
grandeza menor** que a distância típica entre pontos do dataset do ESTOQUE40 (mediana **3.577**,
caixa não-normalizada com amplitude média de 1.213 por dimensão). Resultado: o kernel fora da
diagonal faz **underflow para ≤ 1,3e-70** e o GP **reverte ao prior** (μ=0), então toda proposta
empata e nada substitui.

**Por que isso é bloqueante:** o piso é a régua. Qualquer diferença medida entre `b5r` e o piso no
ESTOQUE40 será **artefato de desempate**, não medida do valor do σ. Em 30 sementes são **30
células de piso offline mortas** + as do b5 no mesmo problema. E note que **o `b5r` no mesmo
problema anda** (99,8%) — então não é o problema que é degenerado, é a configuração do surrogate
do piso nessa escala.

**Escalo pela bússola D29 (não escolho — D81):** é 🔴 *bug nosso* (a especificação do kernel não
serve para D=40 não-normalizado), 🟠 *detalhe de implementação* (fica como está, e a DI-28 manda),
ou 🟢 *extensão declarada* (normalizar a caixa do ESTOQUE40 antes do GP, para os dois lados)?
**Recomendo tratar como 🔴** — um piso que não se move não é piso.

**Achado menor do mesmo agente (classe 3, MEDIA):** `params.geracoes_derivadas` **erra 3/3** nos
pisos — mesma família de defeito que encontrei na T11. O dado está certo; o **texto** que o
descreve está errado, e ele vai para 1.890 manifestos. Forma correta, verificada 3/3:
`G = floor((20D + n_dup_prole) / (2·floor(N_ef/2))) + 1`, com `n_dup_prole` definido como
*cache-hits com fe > 11D−1*.

**O que passou, e passou bem:** os **3 pisos ONLINE** são a peça mais bem verificada da auditoria.
O agente reproduziu, só com ① e ②, a **semeadura D88 completa (conjunto E ordem) em 3/3** e a
**seleção ambiental do NSGA-II em 60 das 61 transições** (a única falha explicada por empate exato
criado pela persistência float32). Ledger fecha na unha nos 3, CP-init reproduzido por sha256
independente em 3/3, e a **rota R1 do DDMOP7 concorda com a R2 com |Δf| = 0,0 EXATO** nas 186 X
compartilhadas.

### 6.4 A verificação dos caveats — 49/52, e três correções ao handoff da torre

A bateria universal passa em **49 de 52 checks (94,2%)**; as 3 falhas estão **todas na c122** e são
consequência do kill. As **52 contagens da tabela §2 do handoff batem 52/52** — a torre não errou
uma contagem. Mas três dos seis caveats precisam de correção:

| caveat | veredito | medição |
|---|---|---|
| 1 — *"tudo é Mac arm64/Accelerate"* | ❌ **falso em 5 de 13** | Mac: 13/13 ✅. **arm64: só 8/13** — as 4 células `b5r` + a `moead_media` rodam **Darwin/x86_64 sob Rosetta**, python 3.7.12, numpy 1.21.6, sklearn 0.21.3 |
| 1 — *"Accelerate"* | ❌ **refutado** | é **OpenBLAS** nos dois venvs (`libopenblas.0.dylib` no `env_b5`, `libscipy_openblas64_` no arm64) |
| 3 — *"dividiu CPU ~1h42"* | ⚠ **58min39s** | e o efeito é menor: **+19%** na mediana de `tempo_geracao_s` |
| **4 — *"b5r em dose dupla = prova de determinismo"*** | ❌ **refutado** | **①, ③ e ⑦ são byte-idênticas** (mesmo sha256 do arquivo inteiro); só ⑥ e ⑤ diferem, e apenas no `run_id`. **Os dois manifestos declaram `regime=offline`** — não são duas execuções, é **a mesma gravação persistida sob dois nomes**. Uma cópia não prova determinismo |
| 2 — gêmeo do e81 | ✅ confirmado e quantificado | **297 de 2.062 registros (14,4%)** são do processo morto |
| 5 — `wall_clock_s: 0.0` | ✅ existe | mas o sidecar **não declara o fatiamento** — `grep 'fatia'` dá zero. Lido de fora, parece bug |
| 6 — c122 incompleta | ⚠ confirmada, **não declarada** | `motivo_parada='checkpoint_em_andamento'` (assinatura de kill), sem footer, ⑤ amputado. **Nada no artefato distingue "decisão" de "morreu"** |

**A consequência séria é o X2.** Se as VMs Linux rodarem o `b5r` com o stack novo, a comparação
Mac-x86_64 × VM-Linux **não é "micro-diferença de BLAS"** — são stacks numéricos diferentes por
uma geração inteira. Isso muda a expectativa de deriva de todo o balde b5/moead_media.

**Mais 4 escalações do agente:** qual venv é o canônico do balde b5r (X2/X3); o `ds_DDMOP7_0` foi
montado em **Darwin-arm64** mas o próprio manifesto cita a D102.14 (*"os F válidos são os das VMs
Linux"*) — é smoke a substituir ou foi promovido? (X7); o sidecar tem `dist='lhs'` contra a D102.1
(X6); e 11 avaliações reais do `c122` existem no ⑥ mas não na ① — num kill, **o ⑥ (append cego)
fica à frente dos parquets (flush por checkpoint)**, não o contrário (X8).

### 6.5 Os algoritmos sobre os problemas reais

| config | score | o problema real quebra alguma premissa do artigo? |
|---|:--:|---|
| **e81** (qPOTS) | 9,3 | **não** — as 3 candidatas testadas com número |
| **c154** (JES) | 9,2 | **não** — o RE21 exercita *menos* ramos que os sintéticos |
| **c122** | 8,6 | **não** — 3 regimes levados a extremos, nenhum ramo novo |
| **e103** (TSEMO) | 8,6 | **não** — mas exercita um regime que os sintéticos nunca produziram |
| **c149** (LBN-MOBO) | 8,0 | **sim — e a quebra NÃO é do c149 contra o artigo**; é do PROBLEMA contra a premissa de continuidade que o artigo (e todo SAEA contínuo) assume |
| **b5r** | 7,5 | **sim — quebra em 2 dos 3 problemas**, e não na parte do artigo esperada; o motor segue fiel (hiperparâmetros batem exatamente) |

---

## 7. O que falta para fechar 100%

| # | item | estado | quem |
|---|---|---|---|
| 1 | Bateria de 11 agentes | ✅ **11/11, 0 erros** | torre de fidelidade |
| 2 | Este laudo consolidado | ✅ **fechado** | torre de fidelidade |
| 2b | **Piso offline congelado no ESTOQUE40** (§6.3) — leitura pela bússola D29 | 🔴 **BLOQUEANTE** | autor |
| 2c | Corrigir os caveats 1, 3 e 4 do handoff da torre (§6.4) | 🟡 texto | torre central |
| 2d | Definir o venv canônico do balde b5r/moead_media (X2/X3) | 🟡 antes do disparo | autor |
| 3 | **Smoke de validação da zona morta** (§4.5-iii) | 🔴 **GATE** — 1 config × 1 semente × τ=0,5, ~55 min | torre central |
| 4 | **Medir a idempotência da zona morta sobre o DoE congelado** (§4.5-ii) | 🔴 antes do item 3 | torre central |
| 5 | **Decidir o contrato da ⑦ do DDMOP7** (§5) | 🔴 **BLOQUEANTE** | autor |
| 6 | **Cravar τ** e registrar REAL-2.15/D102.15 | 🔴 depende do item 3 | autor + torre |
| 7 | Régua S.5 fase 1 do DDMOP7 (a decisão A/B/C que já estava aberta) | 🔴 aberta desde 04/08 | autor |
| 8 | Régua D69 do ESTOQUE40 (C3-01) | 🟡 antes da **R4**, não do disparo | autor |
| 9 | Cadeia de citação do RE21 (T01) — baixar o suplementar / Cheng & Li | 🟡 antes da escrita | autor |
| 10 | Rótulo `concave_front` do ESTOQUE40 | 🟡 antes da R4 | autor |
| 11 | Teste de determinismo do `.p` (~10 FE, 63 s) — o artigo diz *"noisy during the training"*, a D89 assume pureza | 🟡 recomendado antes do disparo | torre central |

**Resumo:** os itens **3, 4, 5 e 6** travam o disparo das 1.890 células e são todos do DDMOP7.
Os itens 8-10 são de escrita e da R4. Os itens 1-2 são meus e fecham hoje.

---

## 8. Onde está a evidência

| artefato | endereço |
|---|---|
| Este laudo | `handoff/T15-LAUDO-FIDELIDADE-PROBLEMAS-REAIS.md` |
| Relatórios por problema e por config | `f5/t15/` *(a gerar no item 2)* |
| Células auditadas | `data/_quarentena_smokes/` (13 células, 7 camadas cada) |
| Pacote de fusão do Agente 8 | `/Users/gmello/Downloads/_fusao_extraido/fusao_torre_agente8/real_experiments/` ⚠ **mais novo que a cópia local em `mestrado/real_experiments`** |
| O documento que previu tudo isto | `.../real_experiments/ddmop7_VEREDICTO.md` §5 e §9 · `LEDGER…` B-6, B-7, B-16c |
