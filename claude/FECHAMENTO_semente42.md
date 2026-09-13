# FECHAMENTO DA SEMENTE 42 — `ua-dd-saea`

**Data:** 2026-07-28 · **Fonte autoritativa:** censo do bucket `gs://mestrado_experiments`, lido na v5 e arquivado em `_censo/censo_bucket_42_FINAL.csv`
**Supersede:** §10.4 e §10.5 do `HANDOFF_operacao_multimaquina.md` (que traziam projeção; aqui é medição)

---

## 1. O número

**666 de 695 células OK — 95,8%.** Descontando as 5 retiradas por desenho (DI-40): **666/690 = 96,5%**.

| família | total | OK | não-OK |
|---|---:|---:|---:|
| main online | 425 | **406** | 19 |
| main offline (`off`) | 125 | **125** | **0** |
| swap offline (`sweep-*`) | 120 | **120** | **0** |
| q10 (`batch`) | 25 | **15** | 10 |
| **TOTAL** | **695** | **666** | **29** |

O `off` e o `sweep` fecharam **100%**. Todo o déficit está em `main` e `batch`, e concentrado em **dois algoritmos**: `c154` e `c262`.

Duas categorias do censo anterior foram a zero: `S/BUCKET` (25 → 0) e `OK-INCOMPLETO` (1 → 0). Não há mais nenhum resultado preso em disco de máquina — o bucket é o inventário completo.

---

## 2. As 29 células que não fecharam

### A · Retiradas por desenho — 5 células ⚪

**`batch/c154`** em DTLZ2, MMF16_20, WFG9, ZDT1, ZDT4.

Retiradas do roster **antes de rodar**, pela DI-40: aborto certo, zero parquet produzido. Não são perda, são decisão de desenho.

> Nota para o REGISTRO: a justificativa original da DI-40 citava "~6,3 h por célula". Isso foi **falsificado** por medição na v5 — o real ficou entre 0,87 e 2,99 h, média 1,47 h. A decisão continua válida (aborto certo), mas o número precisa ser corrigido.

### B · Aborto por projeção de custo — 20 células ⚪

Aborto **sancionado** pela DI-38(a): `motivo_parada = teto_wall`, disparado pelo `_WallClockProjector`.

**`main/c154` — 12 células**, exatamente as de D≥12:

| D | maxFE | problemas |
|---|---|---|
| 12 | 371 | DTLZ2, DTLZ3, DTLZ4 |
| 20 | 619 | MMF16_20 |
| 22 | 681 | DTLZ7, WFG1, WFG2, WFG4, WFG5, WFG9 |
| 30 | 929 | ZDT1, ZDT3 |

**`main/c262` — 3 células:** DTLZ7, MMF16_20, ZDT3.

**`batch/c262` — 5 células:** DTLZ2, MMF16_20, WFG9, ZDT1, ZDT4 — ou seja, **o experimento q10 do c262 inteiro**, 5/5, quatro delas abaixo de 30% de progresso.

*(A identidade nominal das 12 do `c154` e das 3 do `main/c262` é derivada do corte por dimensão e dos processos que estavam em voo na v5/v6; a coluna `problema` do CSV do censo confirma célula a célula.)*

### C · Falha algorítmica real — 3 células 🔴

| célula | máquina | erro |
|---|---|---|
| `main/c262` / **WFG1** | v6 | `botorch.exceptions.errors.ModelFittingError: All attempts to fit the model have failed.` |
| `main/c154` / **ZDT6** | v5 | `RuntimeError: c154 rota (a): random_search_optimizer falhou nas 3 tentativas da escada p/ a amostra 2 (it 62)` |
| `main/c154` / **BBOB_F55** | v5 | idem, `it 55` |

As duas do `c154` são o **mesmo modo de falha**: o amostrador JES não converge na escada de tentativas. As duas ocorrem em D=10. A do `c262` é ajuste do GP no BoTorch. **Todas do lado numérico do BoTorch; nenhuma ambiental.**

### D · Sem manifesto — 1 célula 🔴

**`main/b1` / DTLZ4** — `least squares problem is underdetermined`, certificado no *footer* do `.jsonl` com `status=failed`.

**Determinística e reproduzida em duas arquiteturas** (Linux/Intel na vm3 e macOS/arm64 no Mac). Não é flake, não é infraestrutura: é um defeito do `b1` naquele problema. Aparece como `SEM-MANIFESTO` porque o stack MATLAB certifica no `.jsonl`, não no `.manifest.json` — lacuna de instrumentação registrada como O-21.

---

## 3. Por algoritmo — quem fechou e quem não

**Fecharam 100% (21 dos 24 configs):** b3, b4, c122, c141, c149, c217, c238, e7, e74, e81, moead, nsga2, nsga3, smsemoa, b5m, b5r, c311, e103, moead_media, treed_media, sobol_batch.

**Não fecharam (3 configs):**

| config | OK | não-OK | natureza |
|---|---:|---:|---|
| `main/c154` | 11/25 | 14 | 12 abortos por projeção (D≥12) + 2 falhas do amostrador JES |
| `main/c262` | 21/25 | 4 | 3 abortos por projeção + 1 `ModelFittingError` |
| `batch/c262` | 0/5 | 5 | aborto por projeção, 5/5 |
| `main/b1` | 24/25 | 1 | falha determinística em DTLZ4 |

O `c154` completou exatamente os problemas com **D≤10**, menos os dois onde o amostrador falhou: MMF1, MMF4, MMF11_L, DTLZ1, ZDT4, BBOB_F1, F5, F17, F22, F37, F49.

---

## 4. O que isso significa — e por que 24 das 29 não são "pendência"

**Aborto por projeção não é limitação de infraestrutura. É propriedade do algoritmo.**

O `_WallClockProjector` (`src/c262_qnehvi.py`) ajusta `t_fit ≈ c·n³` e compara `decorrido + projetado` contra o teto, armando na 11ª iteração. `c154` e `c262` (BoTorch/qNEHVI) com D≥12 têm custo de refit de GP que cresce com `n³`, e o orçamento `maxFE = 31D−1` põe o run exatamente na região onde o refit domina o custo total.

Isso foi **testado**, não suposto. Numa janela exploratória o teto foi ampliado de 12 h para 48 h (rompendo a DI-35.5, com autorização do autor). Resultado sobre as 14 células que fecharam nessa janela: **`ok=0`** — reabortaram, e reabortaram *cedo*, em poucas horas, porque o critério dominante é a projeção e não o relógio.

A leitura correta não é "o teto não importa" — o teto **é** um limiar sobre `decorrido + projetado`, e ampliá-lo resgataria qualquer célula cuja projeção caísse na faixa nova. A leitura correta é mais forte: **a razão projeção/orçamento é bimodal.** Ou a célula fecha com folga, ou estoura por ordem de grandeza — as projeções observadas foram de 41 a 190 h contra um teto de 12 h. Não existe faixa marginal a resgatar em escala.

**Consequência para a dissertação:** as 20 células abortadas são um **resultado sobre o limite de escalabilidade do BoTorch/qNEHVI em D≥12 sob orçamento `31D−1`**, com evidência empírica de irrecuperabilidade — não um buraco no experimento. Vale reportar como tal.

**Consequência para o desenho:** o padrão da DI-40 deveria ser estendido, agora com base empírica em vez de projeção. Candidatos: **`batch/c262`** (5/5 abortadas) e **`main/c154` com D≥12**.

---

## 5. Ressalva de atribuição de máquina — para a tabela de tempo do M7

A vm3 não conseguiu completar parte do stack MATLAB (O-19: disco `pd-standard` estrangulando I/O, UUID duplicado no clone de boot, capacidade zonal `n2` esgotada). Essas células foram recuperadas **no Mac**, em macOS/arm64, enquanto as irmãs rodaram em Linux/Intel:

- **`main/e7` — as 25 células rodaram no Mac.** O config inteiro está numa máquina só, então a O-16 ("um config, uma máquina") está **preservada** — só que a máquina é outra. Para comparação de wall entre algoritmos, precisa de nota.
- **`main/c238` — dividido.** A maioria na vm3, um punhado (DTLZ7, MMF16_20, WFG1, WFG2, WFG4, WFG5, WFG9) no Mac. **Aqui a O-16 está rompida** e o `wall_s` do config mistura duas microarquiteturas.
- **`main/b1` — ZDT1, ZDT3 e DTLZ4 passaram pelo Mac.**

⚠ **A coluna `maquina_dona` do `censo_bucket.py` é derivada do ROSTER, não medida** — ela vai rotular essas células como `vm3`. A atribuição real precisa vir do manifesto (campo de host, se registrado) ou dos `done.txt` dos lotes, arquivados em `gs://mestrado_experiments/_logs_lotes/mac/`.

Isso **não afeta os indicadores** (IGD+, HV, spacing são determinísticos dado o resultado), só o endpoint de tempo.

---

## 6. Estado dos artefatos

| onde | o quê |
|---|---|
| `gs://mestrado_experiments/experiments/` | as 695 células, ~4.954 objetos |
| `_censo/censo_bucket_42_FINAL.csv` | inventário autoritativo, uma linha por célula |
| `_snapshot_pre_teto48h/{main/c154, main/c262, batch/c262}` | 269 objetos — reversão dos lotes de 48 h |
| `_logs_teto48h/{v5,v6}/` | logs e `andamento.txt` dos lotes de teto ampliado |
| `_logs_lotes/mac/` | `done.txt` e `grid.txt` de todos os lotes do Mac — o rastro de atribuição de máquina |

`final_eval.py` fechou **`>>> VERDE`** com 105 finais avaliados.

---

## 7. O que fica aberto

1. **Entrada no REGISTRO sobre o rompimento da DI-35.5** — o teto de 48 h, com o resultado (`ok=0` entre as que fecharam) e o achado da §4 como justificativa retrospectiva.
2. **O-20, O-21, O-22** a redigir: o teto não é a variável que decide (§4); o MATLAB certifica no footer do `.jsonl` e não no manifesto; o footer discrimina falha algorítmica de morte de máquina.
3. **Nota operacional:** as últimas 8 células (3 de `main/c154` em DTLZ2/3/4 e 5 de `c262`) estavam **vivas** e foram encerradas por decisão do operador em 28/07, para liberar as VMs. O `.jsonl` delas fica truncado sem footer — que é a assinatura de "morte de máquina" da O-22. **Sem esta nota, uma auditoria futura lerá as 8 como incidente de infraestrutura.**
4. **Extensão da DI-40** para `batch/c262` e `main/c154` D≥12 — decisão do autor.
5. **O que fazer com as 3 falhas reais** e com `main/b1/DTLZ4`.
6. **Correção do número da DI-40** ("~6,3 h/célula" → 0,87–2,99 h, média 1,47 h).
7. **O censo depende da v5** (usa o SDK `google.cloud.storage`). Quando as VMs forem deletadas, o inventário não poderá mais ser regenerado. Trocar a listagem para `gcloud storage ls --recursive` + `gcloud storage cat` deixa o censo rodando do Mac para sempre — vale fazer antes da defesa.
8. **`main/c238` com atribuição de máquina mista** (§5) — resolver antes de montar a tabela de tempo do M7.
