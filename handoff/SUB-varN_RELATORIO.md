# SUB-varN — RELATÓRIO DA VARREDURA (D65) · 2026-08-01

> **Veredito: `N = 20` CONFIRMADO nas três faixas de `D`.** A varredura
> pré-registrada rodou, não substituiu o valor cravado, e produziu **três
> achados** que não estavam em lugar nenhum. Os runs do `R1-pisos` já feitos
> seguem definitivos — nada a re-rodar.

- **Cartão:** `handoff/SUB-varN.md` · **Decisão:** D65 (pré-registro) + DI-39
  (promoveu a pré-requisito do M8)
- **Execução:** 440 células · 4 pisos × `N∈{10,20,30,50}` × 6 problemas × 5 sementes
- **dataRoot:** `mestrado/varredura_subvarn/N{10,20,30,50}` — **fora do repo**, o
  corpus do M8 não foi tocado
- **Métrica:** IGD+ (D70, primária), sobre objetivos normalizados pela S.5 (D69),
  via `src/metrics.py` — o caminho oficial, não um cálculo próprio

---

## §1 · A DECISÃO

**`N = 20` para as faixas baixa (`D≤5`), média e alta (`D≥20`).**

O valor cravado pelo autor em 2026-07-18 se confirma. As quatro justificativas
originais (precedente Knowles/ParEGO · único ponto comum entre `~20–25` do §3.2 e
`{10,20,30,50}` da D65 · viável em todo o grid · densidade de gerações) sobrevivem
intactas, e a varredura acrescenta uma quinta, que só o dado podia dar:
**`N=20` é o único valor factível nas três faixas ao mesmo tempo.**

### Por que não `N=10`, que ganha em quase toda linha

Ele **quebra o MOEA/D**. Não degrada: quebra, com erro duro, em 30 de 30 células.
Causa provada no fonte (`MOEAD.m`):

```
:26   T = ceil(Problem.N/10)            → N=10 dá T=1
:31   B = B(:,1:T)                      → a vizinhança fica com 1 coluna
:42   P = B(i,randperm(size(B,2)))      → P tem 1 elemento; o P(2) a jusante estoura
```

`Index exceeds the number of array elements. Index must not exceed 1.`

E o MOEA/D não é um piso substituível: os 4 são **casados por princípio de
seleção** ao set de algoritmos (NSGA-II→dominância · **MOEA/D→decomposição** ·
NSGA-III→referência · SMS-EMOA→hipervolume). Sem ele, `b3`, `c122` e `b1` ficam
sem régua casada, e a atribuição limpa do ganho ao surrogate se perde.

⇒ **`N ≥ 11` é restrição estrutural**, não preferência.

### Por que não `N=30`, que vence as medianas agregadas

Na faixa **média**, o "ganho" do `N=30` é **artefato de agregação**. A mediana
agregada de 13,15 **é literalmente o número do `moead`** — e olhando piso a piso,
o `N=30` é **pior** que o `N=20` em dois dos três que rodaram todos os valores:

| piso | N=20 | N=30 | |
|---|---|---|---|
| nsga2 | 16,23 | **21,96** | pior |
| smsemoa | 14,75 | **17,81** | pior |
| nsga3 | 18,06 | 14,14 | melhor |
| moead | 21,11 | 13,15 | melhor |

Na faixa **alta**, o `N=30` ganha em 3 de 4 pisos, mas a margem agregada é de
**3%** (0,1104 × 0,1139). Com 5 sementes e mediana, 3% não é mandato para mover
um default pré-registrado — e inventar um teste estatístico agora, **depois** de
ver o dado, seria trocar o critério para caber no resultado. O critério
pré-registrado da D65 é a mediana, e ela não separa.

### Custo de trocar, que também pesou

Um `N` por faixa exigiria re-rodar os pisos de duas faixas, um protocolo mais
difícil de descrever ("por que 30 aqui e 20 ali?" → "porque a mediana deu 3% de
diferença"), e **lattices diferentes por faixa** em M=3. Contra um ganho que o
próprio dado não sustenta.

---

## §2 · OS TRÊS ACHADOS

### 2.1 · 🔴 MOEA/D exige `N ≥ 11` — e isso não estava em lugar nenhum

O bundle §3.2 já registrava o vizinho disto (*"com `N=20` a vizinhança do MOEA/D
é `T = ceil(N/10) = 2`, mínima"*) sem notar que **`N=10` leva `T=1` e o algoritmo
não roda**. Se o `N` tivesse sido eleito no papel, seriam 30 células mortas
descobertas no meio do M8.

### 2.2 · 🔴 `N=30` e `N=50` são infactíveis em `D=2`

Os pisos são semeados do DoE compartilhado, que em `D=2` tem `11D−1 = 21` pontos.
Uma população de 30 ou 50 não cabe no DoE que a semeia. A guarda anti-crash
(`piso_init`) trunca e loga — ou seja, a célula **rodaria**, mas com `N` efetivo
de 21, produzindo um ponto rotulado `N=30` que rodou em 21. Por isso essas 40
células foram **excluídas por desenho**, não deixadas falhar.

### 2.3 · 🔴 ERRATA na tabela de `N` efetivo em M=3

O bundle `40_subestudos/varredura_N_pisos.md` §6.3 afirma que os nominais
`{10,20,30,50}` viram efetivos **`{6,15,28,45}`**. Medido no `UniformPoint` real
do PlatEMO:

| nominal | bundle diz | **medido** |
|---|---|---|
| 10 | 6 | **10** |
| 20 | 15 | 15 ✓ |
| 30 | 28 | 28 ✓ |
| 50 | 45 | 45 ✓ |

O `10` está certo por construção: `C(H+2,2) ≤ N` com `H=3` dá `C(5,2) = 10 ≤ 10`.
O `6` corresponde a `H=2`. **Três dos quatro conferem; o primeiro não.** A errata
vale para o bundle e para a SPEC §6.3.

---

## §3 · OS NÚMEROS

Mediana do IGD+ final (menor é melhor). `—` = célula infactível, excluída.

| faixa | piso | N=10 | N=20 | N=30 | N=50 |
|---|---|---|---|---|---|
| **baixa** (MMF1, D=2) | nsga2 | 0,0526 | 0,0541 | — | — |
| | nsga3 | 0,0586 | 0,0532 | — | — |
| | moead | ✗ quebra | 0,0557 | — | — |
| | smsemoa | 0,0552 | 0,0486 | — | — |
| | **TODOS** | 0,0566 | **0,0536** | — | — |
| **média** (ZDT4 D=10, DTLZ2 D=12) | nsga2 | 9,31 | 16,23 | 21,96 | 18,26 |
| | nsga3 | 13,64 | 18,06 | 14,14 | 26,28 |
| | moead | ✗ quebra | 21,11 | 13,15 | 13,79 |
| | smsemoa | 10,04 | 14,75 | 17,81 | 25,19 |
| | **TODOS** | 9,31 | 14,82 | **13,15** | 13,82 |
| **alta** (MMF16_20 D=20, WFG9 D=22, ZDT1 D=30) | nsga2 | 0,0901 | 0,1131 | 0,0971 | 0,1150 |
| | nsga3 | 0,1103 | 0,1146 | 0,1114 | 0,1484 |
| | moead | ✗ quebra | 0,1990 | 0,1838 | 0,1894 |
| | smsemoa | 0,0896 | 0,0857 | 0,0885 | 0,1170 |
| | **TODOS** | **0,0901** | 0,1139 | 0,1104 | 0,1248 |

⚠ **As colunas `N=10` não são comparáveis às demais**: elas agregam 3 pisos, as
outras agregam 4. É por isso que a leitura correta é piso a piso, e é por isso
que o "melhor N" do agregado engana.

**Nota sobre a escala da faixa média:** IGD+ de 9–26 em objetivos *normalizados*
não é erro. O `ZDT4` tem `g = 1 + 10(n−1) + Σ(x²−10cos(4πx))`, que sob orçamento
mínimo fica longe do front; normalizado pelo nadir de 1,0, o `f2′` passa fácil de
20. É o problema de multimodalidade extrema fazendo o que dele se espera com um
MOEA puro em 309 avaliações.

---

## §4 · O QUE ISTO LIBERA

- ✅ O `N=20` do `R1-pisos` **já rodado é definitivo** — zero re-execução.
- ✅ O pré-registro da D65 está **cumprido**: a varredura rodou e está reportada,
  com os números à vista, antes da bateria.
- ✅ A `UA_DD_SAEA_PISO_N` deve ficar **AUSENTE** na campanha M8. O portão é o
  próprio manifesto: toda célula de piso do corpus oficial traz `N_origem` com
  `CRAVADO`; célula da varredura traz `INJETADO`.
- ➡️ **Destrava a tag `m8-freeze`**, que estava segurada esperando esta decisão.

## §5 · REPRODUZIR

Dado bruto em `mestrado/varredura_subvarn/` (440 células, 4 dataRoots) + os logs
`varn_N{10,20,30,50}.log`. A análise recomputa do zero:

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea
# para cada célula: load_real(①) -> metrics_of_set -> igd_plus; mediana por (faixa, N)
```

O `reference_set` de 5.000 pontos tem de ser **cacheado por problema** — sem isso
a análise reconstrói o front de referência 440 vezes e não termina.
