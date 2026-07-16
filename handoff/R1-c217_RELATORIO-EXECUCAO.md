# R1-c217 — RELATÓRIO DE EXECUÇÃO (narrativa completa da sessão)

> **Propósito.** Este documento descreve **o processo INTEIRO** de execução do cartão R1-c217,
> passo a passo, com cada decisão, cada código rodado e cada resultado — para a torre de controle
> (a instância que gerou as instruções) entender exatamente o que foi feito, como, e o que se atingiu.
> O `handoff/R1-c217.md` é o repasse TÉCNICO enxuto (patches, contrato herdado); **este é o relatório
> de PROCESSO**. Data: 2026-07-16. Branch: `experiment/definitive_algorythms`. Modelo: Opus 4.8.

---

## 0. Veredito em uma linha

**Gate objetivo VERDE e VALIDADO por execução real** (`accept.py R1-c217 --alg c217 --problema
{MMF1,ZDT1} --semente 0` → exit 0). O caso-modelo prova o pipeline MATLAB ponta-a-ponta. **A
validação de fidelidade é do autor (D97) e permanece pendente — por design, não por incompletude.**
Um bug real (D89) foi encontrado PELA validação (ZDT1) e corrigido.

---

## 1. PASSO 0 — Contexto lido (na ordem exigida, e só isto)

Li, nesta ordem: `HANDOFF_MESTRE.md` (§10/§11) · `handoff/R1-00-harness.md` (a infra herdada) ·
`claude_code_context/CLAUDE.md` · `cards/INDEX.md` (linha R1-c217) ·
`10_rodada1_matlab/00_contrato_rodada1.md` (N.0) · `10_rodada1_matlab/alg_c217_pcsaea.md` (as
especificidades — inteiro) · `00_fundacao/01_regras_globais.md` (D53–D100 completo) ·
`00_fundacao/03_contrato_export.md` (§17).

Depois, o **código real** que precisava para os patches por arquivo:linha: os fontes c217
(`PCSAEA.m`, `SurrogateAssistedSelectionPC.m`, `DataProcess.m`, `CalFitnessPC.m`, `RBFNNPC.m`,
`EnvironmentalSelection.m`, `ESCalFitness.m`), a infra R1-00 (`FEBudget.m`, `RunBuffer.m`,
`hook_output.m`, `experiment.m`, `experiments.m`), o gate (`scripts/accept.py`), as classes base
PlatEMO (`ALGORITHM.m`, `UserProblem.m`, `PROBLEM.m`, `SOLUTION.m`), o `anchors.json` (c217) e o
`preflight.py`. **NÃO li** os `alg_*.md` de outros algoritmos (cada patch pertence a UM).

## 2. Verificação de ambiente (ANTES de tudo — D80/D81)

Rodei `check_bridge.m` no MATLAB R2025a (batch). Resultado:
- `pyenv.Executable = /Users/gmello/ponte_teste/bin/python`, `Status=NotLoaded` (normal — carrega no 1º uso).
- `double(py.numpy.array([1,2,3]).sum()) = 6` ✅
- Versões (via `py.importlib.metadata.version`, evitando a armadilha do dot-dunder): **numpy 2.4.6,
  pymoo 0.6.2, pyarrow 25.0.0** — batem com o R1-00. **Ambiente OK → segui.**

## 3. PASSO 1 — Plano (apresentado em ≤15 linhas antes de codar)

Apresentei os patches por arquivo:linha, o teste de aceitação e como resolveria as 2 decisões
deferidas. Segui direto (o card autoriza), sem esperar OK. **Não houve ambiguidade que disparasse
D81 no início** — as decisões deferidas eram para eu RESOLVER (não perguntar).

## 4. PASSO 2 — Implementação (o que fiz, por quê, e o design)

### 4.1 Patches de fidelidade (2 guardas ANCORADAS — D17)
`anchors.json` registra SÓ estas 2 (o resto é [IMPL] meu). `expect_before` batia com o código:
- `SurrogateAssistedSelectionPC.m:21` `if error1 < 1-delta` → **`if error1 > delta`**
- `SurrogateAssistedSelectionPC.m:39` `elseif error2 < 1-delta` → **`elseif error2 > delta`**
Corpos dos ramos intactos. O ramo `else` (`:57`, aleatório) passa a cobrir contradições **E** o
regime-NaN (`NaN>δ`=false em ambas → aleatório, L6).

### 4.2 Integração [IMPL] em `PCSAEA.m`
- **Injeção do DoE (:26-31):** troquei o LHS nativo por `PopDec = Problem.data.X0; Population =
  Problem.Evaluation(PopDec)`. X0 é NATIVO (do artefato) → passa direto, **sem re-escala** (a
  dupla-escala D94 não ocorre). `Problem.N=50` governa população/lote.
- **Timing (:43):** `tic/toc` em volta de `net.train` (§17.6).
- **Fix `min(Problem.N,length(Arc))` (:57):** o stock usava `Problem.N=50`; em D≤4 o `|Arc|<50` faz
  `Rank(1:50)` estourar em `EnvironmentalSelection`. Confirmado lendo `EnvironmentalSelection.m`.
- **Instrumentação (:59):** chamada `c217_instrument(...)` — ③ score + §17.2.1 + timing.

### 4.3 Infra nova
- **`case 'c217' → run_c217` em `src/experiment.m`** (reusa TODA a infra R1-00: ponte, `load_doe`,
  `FEBudget`, `write_real/pop/surrogate/timing`, manifesto, CP-init, jsonl, atômico). Locais novos:
  `c217_batch_eval` (embrulho de lote D61) e `ensure_platemo_c217` (addpath rede).
- **`src/c217_instrument.m` (novo):** ponto único da instrumentação c217, alinhado à geração do hook
  via `buf.gen`.

### 4.4 O DESIGN que fecha a receita N.0 (o pattern-setter — todo PlatEMO herda)
Três problemas técnicos que precisei resolver e que valem para o fan-out inteiro:

1. **O probe do construtor.** `UserProblem(...)` chama `Initialization(1)` no construtor → avaliaria
   1 ponto e, se apontasse para `bud`, POLUIRIA a ① (ponto extra). **Solução:** criar `bud` ANTES do
   Problem + `initFcn = @(N,~)X0(1:N,:)` → o probe avalia **DoE[0]** (não aleatório), que o lote-init
   reencontra como **cache-hit** (0 FE) → `obj.FE==bud.fe`, ① com exatamente 31D−1 linhas, sem poluir.
   (Verifiquei lendo `UserProblem.m`: `data` é slot livre; `initFcn` existe; `Str2Fcn` passa struct/
   handle sem alterar; `once=true` chama `evalFcn(X,data)`.)
2. **Injeção via `Problem.data`.** Empacotei `struct(X0, buf, bud, log, …)` em `'data'` — a PCSAEA
   lê `Problem.data.X0` (injeção) e a instrumentação lê `Problem.data.buf/bud/log`. `data` é
   `SetAccess=protected` mas GET público.
2b. **`rng(semente,'twister')` DEPOIS do Problem, ANTES do Solve (D59).** O probe determinístico não
   consome RNG, então a semente fica limpa.
3. **O hard-stop exato (o item 5 abaixo virou o achado principal).**

## 5. ⚠ O ACHADO PRINCIPAL — a validação pegou um bug (D89)

**Sintoma:** na 1ª rodada, MMF1 (FE=61) e DTLZ2 (FE=371) fecharam exatos, mas **ZDT1 fechou
FE=926 ≠ 929** → `accept.py ZDT1` **VERMELHO**. ZDT1 tinha `cache_hits=4`.

**Diagnóstico (li `ALGORITHM.m` + `UserProblem.m`):** o `UserProblem.Evaluation` faz
`obj.FE = obj.FE + length(Population)` — conta TODAS as linhas do lote, **incluindo cache-hits**
(duplicatas de infill; o c217 não deduplica — DEF-B5.6). Já `bud.fe` conta só X **distintas**. À 1ª
duplicata, `obj.FE` avança à frente de `bud.fe`. Com `Problem.maxFE=31D−1`, o `NotTerminated` lança
`PlatEMO:Termination` quando `obj.FE=929` mas `bud.fe=926` → a ① fica com 926 linhas → gate reprova.
**É EXATAMENTE o que a D89 proíbe** ("o `obj.FE` não governa; o hard-stop é do wrapper").

**Meu 1º design (errado):** deixei o `obj.FE` (via `maxFE`) poder preemptar o `bud`.

**Fix (PCSAEA.m:56):** `Problem.FE = Problem.data.bud.fe;` após cada infill — re-sincroniza o contador
nativo com o **saldo DISTINTO** do wrapper. Assim: (a) `NotTerminated` para em `bud.fe=31D−1`; (b) o
`rate = Problem.FE/maxFE` (que a `CalFitnessPC` lê) fica fiel; (c) o hard-stop real segue sendo o
throw do `bud` no meio do lote. Deixei a linha do `rate` STOCK e o `maxFE=31D−1` intactos.
**Considerei a alternativa** `maxFE=inf` + patch do `rate` para `bud.fe/bud.maxfe`; escolhi o sync
por ser mais LOCAL e não mexer na expressão do rate.

Também **endureci `run_c217`**: se `FE≠31D−1` ou CP-init falhar → manifesto `status=failed` (falha
honesta, D23/D81; o despachante não pula um run inválido).

**Prova do fix:** re-rodei os 3 → **MMF1 61/61, ZDT1 929/929 (cache_hits=4, agora ABSORVIDOS),
DTLZ2 371/371** — todos EXATOS, `accept.py` VERDE nos 3. **Este fix é obrigatório para todo PlatEMO
do fan-out que possa propor duplicatas.**

## 6. As 2 decisões deferidas pelo R1-00 — como resolvi

- **(D61) evalFcn de LOTE com hard-stop no meio.** `c217_batch_eval(X, bud, evalFcnPerX)` itera as
  linhas por `bud.evaluate` (cache-hit=0 FE, D89). Quando o saldo zera, o `bud` lança
  `MException('PlatEMO:Termination')` no meio do lote (D61) → propaga por `CallFcn` (o `addCause`
  **preserva o identifier** — verifiquei o doc) → `Solve` engole → **FE=31D−1 exato**. `dec=X`
  (clamp autoritativo), `con=zeros`.
- **(③ `real_solution_id` nullable).** O c217 grava ③ **só dos candidatos SELECIONADOS** (o lote de
  infill), que são avaliados no ciclo → têm `solution_id` → `real_solution_id` **SEMPRE presente →
  int32** (evita tipo variável entre runs). O fallback `double+NaN` do `write_surrogate` (R1-00)
  fica para algoritmos que gravem candidatos NÃO-avaliados (NULL); o c217 não precisa dele.

## 7. Coisas que fiz ALÉM do plano de ≤15 linhas (a torre deve revisar)

Estas NÃO estavam no plano inicial; surgiram na execução e são as que merecem sua revisão:

1. **O sync D89 `Problem.FE = bud.fe` (§5).** Necessário para o gate; é o único ponto em que o
   algoritmo escreve o contador da plataforma. **É fiel** (aplica a D89: o wrapper é a fonte do
   orçamento). Vale a pena confirmar que você concorda com esta leitura.
2. **`preflight.py` patch-aware.** Ao aplicar as 2 guardas, o `expect_before` some → o pré-voo
   reportaria "expect_before ausente" e sairia 1. Como c217 é o 1º algoritmo a aplicar patches
   in-place, tornei a checagem de âncoras: `expect_before`=STOCK · `expect_after`=**APLICADO** (OK) ·
   nenhum=DIVERGE. Verifiquei verde (guardas c217=APLICADO, resto STOCK, exit 0). **Isto é o padrão
   para todo patch de fidelidade do fan-out.**
3. **`FIDELITY_PROBLEMS` + `_instantiate_problem` em `src/experiment.py`** (para o DTLZ2 d=15, §8).
   Registro SEPARADO, não-canônico; **NÃO toca `ALL_PROBLEMS` nem `PROBLEMA_ID`** → os gates F0
   (que exigem `==25` e `seeds.json==doe.PROBLEMA_ID`) ficam intactos (confirmei rodando F0-01..04).
4. **`scripts/gen_fidelity_doe.py` (novo).** Gera o DoE das instâncias de fidelidade reusando as
   primitivas do `src.doe` (LHS-maximin D87, round-trip bit-a-bit), fora do gate `PROBLEMA_ID`, com
   `problema_id` de fidelidade ≥1000. Idempotente. Torna o DTLZ2_d15 reprodutível de código committed.

## 8. A pergunta que fiz a você (D81 — conflito de fontes) e o "Ambos"

O card pediu fidelidade em **DTLZ2 (m=3, d=15)**, mas a fonte canônica A2 (`problems.py`) é
**DTLZ2 d=12/m=3** (`DTLZ2(k=10)`). Isto é um conflito de fontes genuíno. Como o gate objetivo
(MMF1+ZDT1) já estava VERDE, **perguntei** (não bloqueei o principal). Você respondeu **"Ambos"**.
Então:
- **DTLZ2 d=12 canônico** (a bateria usa): rodado, gate VERDE, FE=371.
- **DTLZ2_d15 d=15** (`DTLZ2(k=13)`, não-canônico via `FIDELITY_PROBLEMS`, exp=`main`): gerei o DoE
  d=15 (via `gen_fidelity_doe.py`, hash `15a686cc…`), rodei, gate VERDE, FE=464, cp_ok=1.

*(Nota de processo: a 1ª tentativa do d=15 usei `exp='fidelity'`, que o `naming.py` REJEITA
(D55 só aceita main/off/batch/sweep-*). Não inventei categoria (D81) → refiz sob `exp='main'` e
limpei. Também alinhei o `problema_id` de fidelidade ao gerador committed (1000) e re-rodei, para o
①/CP-init casarem com o DoE reprodutível.)*

## 9. Instrumentação de fidelidade produzida (para o SEU julgamento — D97)

Por run: **① real** (31D−1 linhas) · **② pop** (membership, todas as gerações) · **③ surrogate**
(`pred_tipo=score`, `pred_score`∈{−1,0,+1}=ação da regra corrigida, `pred_confianca=Error1`,
`modelo=PNN-par`, `real_solution_id` int32) · **timing §17.6** · **`.jsonl` §17.2.1** (header +
`c217_gen` por geração com `p_mais`/`p_menos`/`n_contradicoes`/`n_empates`/`estado`/`motivo`/`lote`/
`score` + footer).

**Números (GUIA, não gate — eu NÃO julguei):**

| Problema | FE | IGD_raw (ref esfera unit. 5050 pts) | Observação |
|---|---|---|---|
| MMF1 (d=2) | 61 | — | **todos estado 3 (aleatório)**: D=2 → `Error∈{0,0.5,1}` (granularidade grosseira, L.5) |
| DTLZ2 (d=12) | 371 | ≈**2,63e-1** | — |
| DTLZ2_d15 (d=15) | 464 | ≈**3,08e-1** | — |

**⚠ 4 CAVEATS que descobri (críticos para a sua leitura — D97):**
1. **Orçamento (o maior):** a guia do paper (IGD≈6,9212e-2 ± 3σ 2,335e-2) é a **2000 FEs**; nosso
   protocolo roda **31D−1** (=371 p/ d=12, **464 p/ d=15**) — **~4× menos** (§5.1/D21, decisão sua).
   IGD raw acima da guia é **ESPERADO** sob orçamento apertado. A comparação justa é do **MECANISMO**
   (os estados 1/2/3 no `.jsonl`), não do IGD cru.
2. **d:** a bateria usa o canônico d=12; o d=15 é o `DTLZ2_d15` NÃO-canônico (filtre-o da análise da bateria).
3. **IGD:** calculei o **raw** (ref = das-dennis projetado à esfera unitária); o `metrics.py`
   normaliza (D69) e não conhece `DTLZ2_d15`. Compute o IGD do SEU jeito a partir da ① crua.
4. **Guardas de fidelidade ABERTAS (K.3/DEF-B5.6, INTOCADAS — não são bug):** spread PNN 0,1925,
   pares todos×todos, operadores η 15/5, diversidade degenerada D≡0.5, SDE inerte, sem dedup de infill.

## 10. Regressões confirmadas (nada quebrou)

| Suite | Comando | Resultado |
|---|---|---|
| Fase 0 | `accept.py F0-0{1,2,3,4}-*` | exit **0** nos 4 |
| Pré-voo | `preflight.py` | exit **0** (guardas c217=APLICADO) |
| Infra R1-00 | `accept.py R1-00-harness --alg stub --problema MMF1 --semente 0 --dim 2` | **VERDE** |

Ou seja: as mudanças no `experiment.py` (FIDELITY_PROBLEMS) NÃO poluíram os 25 canônicos; a infra
herdada continua íntegra.

## 11. Arquivos tocados + commits

**Repo raiz (branch `experiment/definitive_algorythms`):**
- `src/experiment.m` (+167: `case 'c217'`, `run_c217`, `c217_batch_eval`, `ensure_platemo_c217`)
- `src/experiment.py` (+27: `FIDELITY_PROBLEMS`, `_instantiate_problem` estendido)
- `src/c217_instrument.m` (novo, 86)
- `scripts/gen_fidelity_doe.py` (novo, 103)
- `scripts/preflight.py` (+15: patch-aware)
- `handoff/R1-c217.md` (novo) · `cards/INDEX.md` (R1-c217 → ✅) · este relatório

**Árvore `_PlatEMO` (rastreada pela raiz):**
- `…/PC-SAEA/PCSAEA.m` (init/min/sync/instrument) · `…/PC-SAEA/SurrogateAssistedSelectionPC.m` (2 guardas)

**Commits `[R1-c217]`:** `bd009ea` (código) · `650f4f7` (INDEX ✅). Working tree limpa (só `data/`
gitignored resta). Nenhum blob binário versionado (parquets/jsonl/DoE são gitignored, regeneráveis).

## 12. O que o fan-out herda (b1,b3,b4,e7,c141,c238,pisos)

1. **O padrão `run_c217`** (copiar e ajustar os patches do `alg_*.md` de cada um).
2. **O sync D89 `Problem.FE = bud.fe`** — OBRIGATÓRIO em qualquer PlatEMO que possa propor duplicatas.
3. **O embrulho de lote `c217_batch_eval`** (D61) — genérico, reusável.
4. **A absorção do probe** (`bud` antes do Problem + `initFcn=DoE[0]`).
5. **`c217_instrument.m`** como template da camada ③/§17.5 por algoritmo.
6. **`preflight.py` patch-aware** e **`FIDELITY_PROBLEMS`/`gen_fidelity_doe.py`** (config-de-paper de cada um).
7. ⚠ **e103/e74 NÃO seguem N.0** (worker dedicado, árvore própria — N.3/N.0-4.1); herdam export/CP-init, não o Solve do 4.15.

## 13. Status honesto para a torre

- ✅ **Gate objetivo (o que era meu): 100% pronto e validado por execução real.** MMF1 e ZDT1
  `accept.py` exit 0.
- ⏳ **Fidelidade: pendente — é do autor (D97).** Instrumentação entregue; o veredito (mecanismo
  fiel? faixa ±3σ ajustada ao orçamento?) é seu, a posteriori, lendo os `.jsonl` (estados) + a ①.
- 🔎 **Para a torre revisar** (o que decidi além do plano): o sync D89, o `preflight` patch-aware, o
  registro `FIDELITY_PROBLEMS` + gerador de DoE de fidelidade. Todos documentados aqui e no código.
