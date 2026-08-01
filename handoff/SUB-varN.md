# Cartão SUB-varN — varredura pré-registrada do `N` dos pisos online (D65)

- **Fase / rodada:** SUB
- **Depende de:** `R1-pisos` ✅
- **Bundle a ler:** `claude_code_context/40_subestudos/varredura_N_pisos.md` (INTEIRO — são 53 linhas e as três armadilhas deste cartão saem dele)
- **Artefatos a consultar:** `artifacts/runs_matrix.csv` · `characteristics.csv` · `seeds.json`
- **Escrito por:** sessão de provisionamento do M8, 2026-08-01

---

## §0 · Por que este cartão é PRÉ-REQUISITO e não sub-estudo opcional

O `N=20` dos 4 pisos online está **CRAVADO mas PROVISÓRIO**. A história:

- A **D65** delegou o valor a esta varredura pré-registrada.
- Mas a varredura depende do `R1-pisos` (o piso precisa existir para ser varrido),
  então havia circularidade. O autor cortou o nó cravando **N=20** em 2026-07-18,
  com 4 justificativas defensáveis em banca (precedente Knowles/ParEGO; único valor
  na interseção das fontes vivas; viável em todo o grid; densidade de gerações).
- A **DI-32/A2** chamou isso de definitivo; a **DI-39 (2026-07-25) RETIFICOU**:
  é provisório, e a varredura é **pré-requisito do M8**, não sub-estudo do M11.
  A torre ratificou a DI-39 por ser posterior e do autor.

**O que está em jogo:** se a varredura eleger um `N` diferente de 20 para alguma
faixa de `D`, os 4 pisos × 25 problemas × 30 sementes daquela faixa teriam de ser
re-rodados. Rodar isto **antes** do disparo custa minutos; rodar depois custa
células da campanha.

Se ela reconfirmar 20, os runs do `R1-pisos` já são os definitivos — e o
pré-registro fica honrado, que é o ponto metodológico.

---

## §1 · 🔴 As três coisas que a D65 NÃO resolve (leia antes de codar)

Estas não são detalhes de implementação: são buracos na receita. Cada uma tem
minha leitura e o que a sessão deve MEDIR em vez de assumir.

### 1.1 · A faixa de `D` baixa não tem problema para decidir

A D65 manda **"escolher 1 `N` por faixa de `D` (baixa ≤5 / média / alta ≥20)"** e
prescreve o conjunto **"5 problemas do sweep + 2 reps alta-D"**. Mas os 5 do sweep
são `ZDT4` (D=10) · `DTLZ2` (D=12) · `MMF16_20` (D=20) · `WFG9` (D=22) ·
`ZDT1` (D=30). **Nenhum tem D≤5.** A faixa baixa fica indecidível com o conjunto
prescrito, e os 3 únicos candidatos do grid inteiro são `MMF1`, `MMF4` e
`MMF11_L`, todos D=2.

**Leitura recomendada:** acrescentar **`MMF1` (D=2)** ao conjunto. Razões: é a
"calibração unitária do niching" da suíte MMF (Anexo P.2), é o problema mais
barato do grid, e D=2 é exatamente onde o `N` mais morde — a população chega perto
do tamanho do DoE inteiro.

E os "2 reps alta-D" da D65 **já estão dentro do conjunto do sweep**
(`MMF16_20` 20, `WFG9` 22, `ZDT1` 30 — três, não dois). Somar mais dois seria
redundância sem cobertura nova.

⚠ Isto é interpretação de um pré-registro. Se o autor discordar, o conjunto muda
antes de rodar — **nunca depois de ver os resultados**, que é o que um
pré-registro existe para impedir.

### 1.2 · `N=30` e `N=50` são INFACTÍVEIS em D=2

Os pisos são **semeados do DoE compartilhado** (§3.2 do bundle). Em D=2 o DoE tem
`11D−1 = 21` pontos e o orçamento é `31D−1 = 61`. Uma população de 30 ou 50 **não
cabe no DoE que a semeia**, e mesmo ignorando isso `N=30` renderia
`(61−21)/30 = 1` geração — degenerado.

O próprio bundle já diz a metade disso (§3.2, ponto 3: *"`20 ≤ 11D−1` para todo
`D≥2`"*), sem tirar a conclusão sobre 30 e 50.

**Consequência:** a faixa baixa se decide entre **`N ∈ {10, 20}`** apenas. A
sessão deve **declarar isso no relatório**, não deixar as células de N=30/50 em
D=2 falharem e virarem ruído.

### 1.3 · A tabela de `N` efetivo em M=3 tem um número que não fecha

O bundle (§6.3) afirma que em M=3 os nominais `{10,20,30,50}` viram efetivos
`{6,15,28,45}`, porque o `UniformPoint(N,3)` do PlatEMO arredonda para baixo até
o maior `H` com `C(H+2,2) ≤ N`.

Recalculando: `N=20 → H=4 → 15` ✓ · `N=30 → H=6 → 28` ✓ · `N=50 → H=8 → 45` ✓.
Mas **`N=10 → H=3 → C(5,2) = 10`**, não 6. O 6 corresponde a `H=2`.

Pode ser que o `UniformPoint` use desigualdade estrita, ou outra convenção. **Não
assuma nenhuma das duas.** Primeira tarefa da sessão, custa segundos:

```matlab
for N = [10 20 30 50]; V = UniformPoint(N,3); fprintf('N=%2d -> %d vetores\n', N, size(V,1)); end
```

O que sair daí é o que vale, e a divergência (qualquer que seja o lado) entra
como errata no bundle/SPEC. É a lição do T14: **número de relatório é hipótese até
ser re-medido** — quatro dos itens daquele cartão caíram assim.

⚠ Vale só para `nsga3` e `moead` (usam vetores de referência). `nsga2` e `smsemoa`
mantêm o `N` nominal. Ou seja: **o `N` não é uniforme entre os 4 pisos em M=3**, e
metade do grid é M=3. Já é assim hoje com N=20 (efetivo 15) e está aceito.

---

## §2 · Tarefa

### 2.1 · O grid

`4 pisos × 4 valores de N × 6 problemas × 5 sementes`, menos as células infactíveis
do §1.2:

| eixo | valores |
|---|---|
| pisos | `nsga2` · `nsga3` · `moead` · `smsemoa` (os 4 ONLINE; o offline `moead_media` **NÃO entra** — mantém o lattice do b5m, DI-16.4) |
| `N` | `10` · `20` · `30` · `50` |
| problemas | `MMF1` (D=2) · `ZDT4` (10) · `DTLZ2` (12) · `MMF16_20` (20) · `WFG9` (22) · `ZDT1` (30) |
| sementes | as 5 primeiras da lista canônica: `0,1,2,3,4` |

`4 × 4 × 6 × 5 = 480` células, menos `4 pisos × 2 N × 1 problema × 5 sementes = 40`
infactíveis (N=30/50 em MMF1) ⇒ **440 células**. Custo: segundos cada (os pisos não
treinam surrogate) — a varredura inteira é da ordem de dezenas de minutos no Mac.

### 2.2 · Onde escrever — e por que não em `data/`

Estas células **não estão no `runs_matrix.csv`** e **não são resultado da
campanha**. Escrevê-las em `data/experiments/` contaminaria o corpus do M8 com
células de `N` não-canônico, e o censo/`is_run_done` passaria a vê-las.

**Use um `--data-root` separado** (ex.: `data_varn/`). Duas consequências que já
custaram tempo neste projeto:

- ⚠ **A armadilha O-01:** um `dataRoot` novo **não tem `doe/`** e a célula morre com
  *"DoE ausente"*. O T14 caiu nisso, e a torre também. Faça o link/cópia dos
  pré-requisitos ANTES do primeiro run.
- ⚠ **`accept.py` e `auditar.py` ignoram `--data-root` POR DESENHO**
  (`portao.py:94`). Isto **não é problema aqui**: o SUB-varN não passa pelos
  portões da campanha — o critério dele é o IGD+ mediano, computado da camada ①
  com `src/metrics.py`. Só não tente rodar `portao.py` sobre estas células.

### 2.3 · A via de injeção — ✅ IMPLEMENTADA (2026-08-01)

O `N` era um literal (`N_nominal = 20;`) num **ponto único** de
`src/experiment.m`. Agora sai de `piso_n_nominal()`, que lê a env
**`UA_DD_SAEA_PISO_N`** e cai em `20` quando ela está ausente.

| requisito | como ficou |
|---|---|
| `N` nominal **e** efetivo no manifesto | já existiam (`N_nominal`/`N_efetivo`); o que faltava era a **procedência**, agora em `piso_n_origem()` |
| default intocado | `tests/test_subvarn_piso_n.py` roda a função de produção sob MATLAB e exige `20` sem a env |
| `algorithms/` intocado | a mudança é só em `src/experiment.m` |

**O que a implementação acrescentou além do pedido — e por quê.** Um valor
inválido **pára** (`ua_dd_saea:pisoNInvalido`) em vez de cair no default. O modo
de falha que isso fecha é o pior possível para uma varredura: um typo
(`UA_DD_SAEA_PISO_N=3O`, com letra O) viraria `20` em silêncio e produziria uma
célula **rotulada N=30 que rodou em N=20** — contaminando exatamente a
comparação que a varredura existe para fazer. É a mesma classe do `LOTE_ORDEM`
fora do vocabulário que virava `hibrida` sem avisar.

E o manifesto passa a declarar **qual dos dois caminhos** produziu a célula: sem
isso, uma célula da varredura e uma da campanha ficam indistinguíveis no corpus
depois de gravadas — e a varredura escreve células com `N` que a campanha nunca
usaria.

⚠ A env tem de estar **AUSENTE** na campanha M8. O portão é o próprio manifesto:
toda célula de piso do corpus oficial tem de trazer `N_origem` com `CRAVADO`.

---

## §3 · Teste de aceitação (o que torna o cartão VERDE)

**Automático (bloqueia):**
- [ ] `UniformPoint(N,3)` medido para os 4 valores de `N`, e a tabela do §6.3 do
      bundle **confirmada ou corrigida por errata** (§1.3)
- [ ] as 440 células com as 4 saídas válidas + manifesto
- [ ] `N` **nominal e efetivo** no manifesto de cada run
- [ ] FE final exato = `31D−1` em toda célula concluída
- [ ] controle negativo: célula default (N=20) **bit-idêntica** à de antes da
      mudança (`sha256` da ①)
- [ ] as 40 células infactíveis (N=30/50 em D=2) **declaradas e excluídas**, não
      falhando em silêncio
- [ ] `data/experiments/` **intocado** — `git status` e contagem antes/depois

**Decisão (é do AUTOR, D97/D81):**
- [ ] mediana do IGD+ final (D70, sobre objetivos normalizados da S.5) por
      `(N, faixa de D)`, com as 5 sementes
- [ ] **1 `N` eleito por faixa** — baixa (≤5) · média · alta (≥20)
- [ ] se eleger `N=20` numa faixa ⇒ os runs do `R1-pisos` daquela faixa já são
      definitivos, nada a re-rodar
- [ ] se eleger outro ⇒ **PARE** e escale: as células de piso daquela faixa
      precisam ser re-planejadas ANTES do disparo do M8

---

## §4 · Ao fechar

- Verde ⇒ `handoff/SUB-varN_RELATORIO.md` com a tabela de medianas, o `N` eleito
  por faixa, a errata do §1.3 e as decisões do §1.1/§1.2 registradas. Atualizar
  `cards/INDEX.md` (linha 67, `⬜` → `✅`) e o `REGISTRO_DECISOES_IMPLEMENTACAO.md`.
- Vermelho ⇒ **pára-e-loga** (D81): grave o diagnóstico e devolva ao autor.
  **Nunca** escolha o `N` sozinho — é decisão científica, e é pré-registrada.

⚠ **A ordem importa:** o resultado desta varredura pode mudar o que a campanha
roda. Ela vem **antes** do disparo do M8, não em paralelo com ele.
