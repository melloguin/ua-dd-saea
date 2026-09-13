# T6-batch — REPASSE À TORRE: decisões que precisam do autor

> Complemento de `handoff/T6-batch.md` (detalhe técnico completo lá).
> Commits: `4d89702` · `c5eeb0a` · `29d2dca` · `aa584c4` · `2fa542f` · `ff9111b` · `dd5d229`.
> **Nada aqui foi decidido por mim** — são achados de custo/fidelidade (D81/D97/A3) que
> a torre precisa levar ao autor.

---

## D-0 · 🔴🔑 OS DOIS GP-BO (c154 E c262) são INVIÁVEIS no batch de D≥10 — mesma causa

**O achado central do T6**, medido ao vivo nos dois: **o greedy q=10 da AQUISIÇÃO** é o
gargalo (não o fit do GP), e ele **cresce com n** → o batch completo (2000 infills, n até
2109) é computacionalmente inviável em D≥10 para ambos os GP-BO.

| config | mecanismo do custo | wall medido | projeção total |
|---|---|---|---|
| **c154 (JES)** | greedy q=10 × `optimize_acqf(50 restarts, 10000 raw)` × LB-JES | **~30 min/iter** | **~100 h** (morto na it 6) |
| **c262 (qNEHVI)** | greedy q=10 × qLogNEHVI (prune_baseline+MC crescem com n) | 4,5→13 s/iter (it 1→10) | **~56 h** (projetor abortou na it 10) |

No c262 o `t_fit` é **~0,2 s** (plano) — o custo é 100% a aquisição (`t_busca` 4,5→13 s em
10 iterações, crescendo com o baseline). No c154 idem (`t_paths_s`~1-2s; `t_busca_s`~1800s).
**A raiz comum: o lote q=10 multiplica a aquisição por 10× e a aquisição escala com n.**

**Isto valida o fix `dd5d229`** (teto_s→max_wall_s): o c262 abortou LIMPO pelo projetor
(manifesto `failed`/`teto_wall`, curva parcial) ao projetar 56h > o teto de 8h. Sem o fix,
rodaria sem teto (como o c154 rodou 3h antes de ser morto à mão).

**Estado dos 5 smokes do batch (ZDT4/42, q=10):** sobol_batch ✅ · e81 ✅ · c149 ✅ (os 3
baratos, verdes) · **c154 e c262 = deferidos (inviáveis no batch cheio — decisão de custo
do autor).** O fio q=10 dos dois está validado por outra via (regressão q=1 BIT-IDÊNTICA +
~10 iterações corretas cada — ①②③④ certos, FE avançando).

**A decisão (a mesma para os dois, agora):** como viabilizar os GP-BO no batch da rodada de
fidelidade? Ver D-1 abaixo (era c154-específico; **vale para c262 também**).

---

## D-1 · 🔴🔑 Como reduzir o custo da aquisição batch dos GP-BO (c154 + c262)?

**O achado (medido ao vivo, não estimado).** O smoke `batch/c154/ZDT4/42` custou
**~30 min POR ITERAÇÃO** → **~100 horas** para as 200 iterações (fez 6 em 3h07 antes de ser
encerrado por decisão do autor). O jsonl (streamado por iteração) isola a causa:

- `t_paths_s` (amostragem de Pareto do JES, rota 'a') = **~1-2 s** — barato, a escada de
  fallback NÃO disparou.
- `t_busca_s` (a aquisição greedy q=10) = **~1350-2040 s/iteração** — **99% do custo**.

**Causa:** o greedy q=10 faz **10 `optimize_acqf` sequenciais**, cada um com
`num_restarts=5D=50` e `raw_samples=1000D=10000` (§L.11, "valores do PAPER", que escalam
com D), e cada avaliação do lower-bound do JES é cara. Em D=10 × q=10 isso explode. **Não é
bug** (o run q=10 é correto — produziu ①②③④ certos nas 6 iterações) nem o GP (n≈170). É a
**receita da aquisição** aplicada ao regime batch.

**Generaliza:** todos os problemas do batch exceto MMF1 têm D≥10 (ZDT4=10, DTLZ2=12,
WFG9=22, ZDT1=30) ⇒ o c154 batch é inviável em **todo o roster** na receita cheia. (E o
próprio c154 principal já é reconhecidamente caríssimo — a SPEC estima c154/ZDT1 em
~121 dias-core; o batch multiplica por ~10.)

**Decisão do autor já tomada (2026-07-24):** *"a redução do custo da aquisição do c154 vai
DIRETO no teste de fidelidade real, não no smoke; para o smoke, pode só matar."* Feito: o
c154 foi encerrado, o fio q=10 fica validado por outra via (regressão q=1 bit-idêntica +
6 iterações corretas), e o smoke completo do c154 fica **deferido**.

**O que a torre precisa decidir com o autor (para a rodada de fidelidade real):**
1. **Reduzir a aquisição SÓ no `exp=batch`** (knob batch-aware, não hard-code):
   - **c154 (JES):** `num_restarts`/`raw_samples` de 5D/1000D → sugestão **2D/50D**
     (~50× mais barato/`optimize_acqf` ⇒ da ordem de ~2 h/run). Fica perto dos defaults
     do BoTorch (10/512) — defensável.
   - **c262 (qNEHVI):** hoje `NUM_RESTARTS=10`/`RAW_SAMPLES=512` FIXOS (não escalam com D),
     então o alvo é diferente: o custo vem do **qLogNEHVI × q=10 com baseline crescente**.
     Opções: `prune_baseline` mais agressivo, `MC_SAMPLES` menor (128→32) no batch, ou um
     teto de baseline. **Precisa de análise do autor** — não há um knob óbvio como no c154.
   - **É mudança de receita (D97): o autor ratifica os valores nos DOIS casos.**
2. **OU** aceitar os GP-BO batch como "inviáveis-medidos/documentados" e **tirá-los do
   roster do batch** (o sub-estudo compara o LOTE; com e81/c149/sobol_batch + o piso, a
   pergunta "surrogate+aquisição compram algo sobre lotear?" ainda tem resposta — perde-se
   só a âncora GP-BO clássica).
3. **OU** rodar os GP-BO batch só num problema barato (MMF1, D=2 — se a parede densidade não
   matar) + teto agressivo (dado parcial).

O fio de `teto_s` já chega aos dois (fix `dd5d229`), então qualquer teto do M8 é honrado —
o c262 já demonstrou o aborto-por-projeção limpo. A implementação da redução do c154 é
~10 linhas batch-aware; a do c262 pede análise antes. **NÃO as fiz — decisão de fidelidade.**

---

## D-2 · 🔴 Perfil de MEMÓRIA do batch — provisionamento M8 é limitado pela RAM, não pelos cores

Rodando os 4 online em paralelo (1 core cada) numa máquina de **16 GB**, o **c262 foi MORTO
por pressão de memória (OOM/SIGKILL)**. Picos medidos: **c154 ~3 GB · c262 ~2-3 GB** (o GP
guarda o `X_baseline` de ~2000 pontos + a amostragem MC sobre os restarts); e81 ~1,1 GB;
c149 ~0,4 GB. **Recomendação:** no M8, o paralelismo por máquina é **~1 run de c262/c154 do
batch por 4 GB de RAM**, não 1 por core. Numa VM de 16 GB, no máximo **2-3 configs GP-BO
batch em paralelo**. Insumo direto da **A3** (provisionamento). NÃO é vazamento de código.

---

## D-3 · Achados de custo (walls medidos) — insumo da A3/A5

| config | wall do batch (ZDT4/42, q=10) | por iteração |
|---|---|---|
| sobol_batch | 2,4 s | trivial (piso, sem modelo) |
| e81 | ~35 min | ~10 s |
| c149 | ~116 min | ~35 s |
| c262 | em curso (~10-13 s/iter no início; cresce com n) | — |
| **c154** | **~100 h projetado (INVIÁVEL)** | **~30 min** |

---

## D-4 · ℹ️ Correções de LANÇAMENTO/instrumentação feitas nesta sessão (não pedem decisão)

1. **🔴 e81 rodava no stack ERRADO** — `VENV_ONLY_ALGS` era literal e esquecia o e81
   (env próprio `env_e81_qpots`, botorch **0.16.1** vs 0.18.1 do env_main). Agora derivado
   de `envs.json` (drift-proof). (`4d89702`)
2. **`teto_s` não chegava ao c262/c154** (usavam `max_wall_s`; o despachante passa
   `teto_s`) ⇒ rodavam SEM teto. Unificado (`dd5d229`).
3. **e81 fallback qmaximin não gravava a ③** dos pontos completados (28 gerações com <q
   escolhidos no 1º smoke) — o FE estava certo, a ③ incompleta. Corrigido (`2fa542f`).
4. **Gate do c149 hard-coded em q=1** — reprovava um run de batch correto (2000
   escolhidos). Batch-aware (`ff9111b`).

Todos os 4 online mantêm a **prova de regressão q=1 BIT-IDÊNTICA** (o principal intocado).

---

## D-5 · Pendências para a torre (não são decisão, são execução da torre)
1. **Regenerar `runs_matrix.csv`** se o batch trocar MMF1→MMF16_20 (território da torre).
2. O `q` no dict de RETORNO do c149 sai `None` (cosmético — o manifesto grava q=10 certo;
   só o valor de retorno em memória não inclui a chave). Corrigir num toque futuro do c149.

---

## Resumo para o autor (a decisão central)
**c154 batch custa ~100 h na receita cheia (medido). Como reduzir a aquisição JES para a
rodada de fidelidade?** (a) reduzir num_restarts/raw_samples batch-only [sugestão 2D/50D],
(b) tirar c154 do roster do batch, ou (c) rodar parcial com teto. Os outros 4 configs do
batch (sobol_batch/e81/c149 verdes; c262 em curso) estão OK.
