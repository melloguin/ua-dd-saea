# T6-batch — o sub-estudo batch q=10 (D66/D42)

> Sessão de implementação · 2026-07-23/24 · branch `experiment/definitive_algorythms`
> Commits: `4d89702` (orçamento + fix e81/env) · `c5eeb0a` (teto_s + c262) ·
> `29d2dca` (c154/c149/e81) · `aa584c4` (sobol_batch + gates)
> Baseline de entrada: T7 fechado, suíte 348 OK.

## 1. Contrato (o que o cartão pedia)

q=10 · `maxFE_batch = 11D−1 + K·q` com **K=200** (2.000 infills) · DoE **PAREADO**
com o principal (o MESMO artefato 11D−1 — nunca gerado) · roster
**c149/c262/e81/c154 + sobol_batch** · 5 problemas {MMF1, ZDT1, ZDT4, DTLZ2, WFG9} ·
cada algoritmo no modo de lote **NATIVO** (sem fallback livre) · `exp='batch'` (D55).

## 2. O que foi implementado

### 2.1 Orçamento por exp (`src/budget.py`) — a fundação
`maxfe_por_exp(exp, D, q)`: `batch` ⇒ `11D−1 + 200·q`; `main` ⇒ `31D−1` **inalterado**
(o q é ignorado fora do batch); `off`/`sweep-*` ⇒ **levantam** (no offline o orçamento
É o dataset, D90 — devolver uma fórmula ali seria o bug silencioso que o T7 fechou).
`K_BATCH=200` é constante nomeada, não literal solto.

### 2.2 O fio do q nos 4 online — e o conflito de API que ele revelou

**c262 (qNEHVI) e c154 (JES): `_lote_greedy_sequencial`.** O contrato do batch (D66)
manda `sequential=True`; o contrato da ③ (§17.4 + DI-10 `acqf_todos_restarts`) exige
`return_best_only=False`. **O BoTorch PROÍBE a combinação**
(`NotImplementedError: return_best_only=False only supported for joint optimization`).
Saída sem perder nenhum dos dois: o modo sequencial do BoTorch
(`_optimize_acqf_sequential_q`) é **literalmente `q` chamadas com q=1 + `set_X_pending`
dos já escolhidos** — transcrevi esse laço, trocando só `return_best_only` (que **não
altera a seleção**, o `argmax` devolve o mesmo ponto; só expõe o que o stock descarta —
critério DI-12.1/DI-21). No c154 há um 2º motivo: `batch_initial_conditions` também é
incompatível com sequencial, e a transcrição re-gera os ICs por passo (correto).
**Verificado:** o `forward` do qLB-JES é decorado com `@concatenate_pending_points` no
0.18.1 ⇒ `X_pending` É usado (entropia conjunta) ⇒ o greedy É o lote nativo do JES.
Caveat B9.4 anotado (q=10 extrapola o máx do paper q=8; LB não-monotônico).

**c149 (LBN-MOBO): `_hvi_greedy_lote_d42`.** D42: HVI-greedy sequencial, 10 um a um por
ganho de HV, sem reposição. A cada passo o front de referência do HV é o ND observado
**AUMENTADO pelos μ preditos dos já-escolhidos** deste lote (infills pendentes — só o μ
existe). Normalização FIXA na iteração (card). ⚠ **DECISÃO DE EXECUÇÃO (autor ratificou
2026-07-24; D97 revê a fidelidade):** a D42 não fixa com que valor o já-escolhido entra
no passo seguinte; μ predito é a única leitura coerente (= a escolha do qEHVI).

**e81 (qPOTS): só o fallback qmaximin (DI-25 #3).** O resto já estava fiado. Quando
`|ND| < q`, o stock `argsort()[-q:]` devolve um lote menor **em silêncio**; agora completa
até q por **MAXIMIN sobre os rank-1+** (`res.pop.get("rank")>=1`) via o `qmaximin`
**vendorizado** (farthest-point fiel), maximizando a distância mínima aos já-selecionados;
**falha-alto** se nem assim fechar; evento ⑥ `lote_completado_por=qmaximin`. Removido o
remendo de 2 escritas do manifesto (o q vai direto ao `write_run_outputs`).

Nos 4: q=1 tem **saída antecipada** (o principal fica bit-intocado), orçamento por exp,
q no manifesto e no `.jsonl`, hard-stop no meio do lote com o mesmo rito do passo 1.

### 2.3 Runner novo `src/sobol_batch.py` — o piso do batch
Piso **ONLINE** (avaliação real de lotes Sobol SCRAMBLED/Owen, **sem surrogate**): DoE
init 11D−1 pareado + 200 iterações de lote q. **③ VAZIA, SEM sonda** (CONTRATO §6.1 linha
"pisos"); ④ com `tempo_fit_s=NULL`. Sobol semeado por `iteration_seed(base, 22, iter, 0)`
(`alg_id=22` do `seeds.json`, DI-33). Dispatch em `experiment.py` (o roster auto-deriva —
DI-31); roda no `env_main`.

### 2.4 `teto_s` fiado de ponta a ponta (autorização do autor)
`experiments.py --teto-s` → `_stage_grid` → `_run_one` → `adapter.run` → runner. Antes o
parâmetro existia em c311/e81 mas o despachante **nunca o passava** — o `_TetoWall` era
código morto na bateria. **Teto do batch: 4 h/run inicialmente (autor 2026-07-24), depois
elevado a 8 h/run** para os 2 GP-BO restantes (o c262 re-rodado sozinho usou `teto_s=28800`).

### 2.5 🔴 FIX de lançamento — o e81 rodaria no stack errado
`VENV_ONLY_ALGS` era literal e **esquecia o e81**, que tem env próprio (`env_e81_qpots`,
botorch **0.16.1** contra **0.18.1** do env_main). Os runs validados do e81 registram
0.16.1 — a bateria o rodaria com stack diferente, sem erro. Agora **derivado de
`envs.json`** pelo critério real ("env do alg ≠ env do despachante") — drift-proof.
Terceiro defeito de lançamento da sessão (após `enable_bucket` e a lacuna D23/D60 do T7).

### 2.6 Gates batch-aware
`accept.fe_esperado_por_exp(exp,…,q)`: batch ⇒ `11D−1+200q` (o **q vem do manifesto**, via
`budget.maxfe_por_exp` — a mesma fonte do runner). `check_fe` lê o q e usa isto.
`auditar`: `sobol_batch` entra em `PISOS_ONLINE` (não se exige sonda). `portao`:
`sobol_batch → T6-sobol_batch` (gate genérico; online ⇒ sem `final_eval`).

## 3. Validação

| item | resultado |
|---|---|
| Suíte | **368 OK** (baseline 328, +40) |
| preflight | exit **0** |
| **Provas de regressão q=1** (main/MMF1/s0 vs disco) | **c262, c154, c149, e81 — ①②③④ BIT-IDÊNTICAS** (só os `tempo_*_s` de wall variam). O caminho do principal está intocado nos 4. |
| Smoke `sobol_batch/ZDT4/42` q=10 | ✅ fe=**2109** exato · 2 gates VERDES · determinismo (2 runs) ①②④ bit-idênticas |

Testes novos: `tests/test_batch_q10.py` (orçamento, roster do `runs_matrix`, q=10, 5
problemas, alg_id 22, roteamento de env, teto_s) + guardas em `test_r3_harness`,
`test_portao`, `test_fio_sweep`.

## 4. Smokes do batch (q=10, ZDT4/42, teto do autor)

| célula | status | fe | wall | gates |
|---|---|---|---|---|
| `batch/sobol_batch/ZDT4/42` | ✅ **ok** | 2109 | 2,4 s | accept+auditar VERDES · determinismo OK |
| `batch/e81/ZDT4/42` | ✅ **ok** (pós-fix) | 2109 | ~35 min | accept+auditar VERDES · 2000/2000 escolhidos |
| `batch/c149/ZDT4/42` | ✅ **ok** (gate corrigido) | 2109 | ~116 min | accept+auditar VERDES · 2000/2000 |
| `batch/c154/ZDT4/42` | ⛔ **MORTO — inviável** (ver §4c) | — | ~30 min/iter | fio validado por outra via; smoke deferido |
| `batch/c262/ZDT4/42` | ⏳ **rodando** (rápido: ~10-13 s/iter no início) | — | — | — |

Nota `sobol_batch`/`e81`/`c149`: os 3 fecharam com FE=2109 exato e determinismo/gates
verdes. O `c262` está em execução (perfil de custo bom); o `c154` foi encerrado.

**Decisão do autor sobre o problema dos smokes (2026-07-24):** MMF1 → MMF16_20 em todo o
sweep (ver T7); no batch usei **ZDT4** (o mais barato do roster: D=10, M=2 ⇒ maxFE=2109).
O MMF1 no batch levaria o GP a n=2109 em D=2 (a mesma parede densidade do sweep-medium) —
sinalizado para a torre avaliar se o batch também troca MMF1→MMF16_20.

## 4c. 🔴 c154/JES batch é COMPUTACIONALMENTE INVIÁVEL na receita cheia (decisão do autor)

**Medido ao vivo** (`batch/c154/ZDT4/42`, jsonl streamado por iteração):

| iteração | wall | `t_paths_s` (JES paths) | `t_busca_s` (aquisição q=10) |
|---|---|---|---|
| it=1 | 22,6 min | 2,2 s | **1358 s** |
| it=2 | 26,9 min | 1,4 s | **1614 s** |
| it=3 | 29,2 min | 2,1 s | **1755 s** |
| it=4 | 33,9 min | 1,7 s | **2037 s** |
| it=5 | 32,0 min | 1,0 s | **1919 s** |
| it=6 | 33,4 min | — | **2001 s** |

**~30 min/iteração × 200 iterações ≈ 100 HORAS.** Fez 6 de 200 em 3h07 antes de ser
encerrado. **A causa não é o GP** (n≈170) **nem um bug** (a escada de fallback NÃO
disparou — `t_paths_s` ≈ 1-2 s): é o **greedy q=10 da aquisição JES** — 10 `optimize_acqf`
sequenciais, cada um com `num_restarts=5D=50` e `raw_samples=1000D=10000` (que escalam com
D), e cada avaliação do lower-bound do JES é cara. É **inerente à receita** (D=10 × q=10).

**Decisão do autor (2026-07-24):** o fio do c154 é validado por outra via (regressão q=1
bit-idêntica + 6 iterações corretas observadas); o **smoke completo do c154 fica DEFERIDO**
e a **redução do custo da aquisição JES é uma decisão da torre/autor para o teste de
fidelidade real** (D97) — ver o `T6-batch_REPASSE-A-TORRE.md`, item central.

## 4b. 🔴 Achado de MEMÓRIA — crítico para o M8 e a decisão A3

Medido ao vivo rodando os 4 online em paralelo (1 core cada) numa máquina de **16 GB**:
o **RSS cresce com n** (o GP guarda o `X_baseline` de todos os ~2.000 pontos + a
amostragem MC sobre os restarts + o greedy q=10). Picos observados:

| config | RSS no fim (n≈2109) |
|---|---|
| **c154 (JES)** | **~3,0 GB** |
| c262 (qNEHVI) | ~2–3 GB (estimado; morreu antes de medir o pico) |
| e81 (qPOTS) | ~1,1 GB (estável — overhead do torch) |
| c149 (BNN) | ~0,4 GB (MLPs pequenas) |

**Consequência medida:** com os 4 juntos + swap, o pico passou da RAM física e o
**c262 foi MORTO por pressão de memória (SIGKILL — sem traceback, sem manifesto)**. Ou
seja: **os configs GP-BO do batch são memory-bound, não só CPU-bound** — ao contrário do
principal q=1 (onde n≤929 e o RSS fica em centenas de MB).

**Recomendações à torre (pré-M8):**
1. **Paralelismo por máquina limitado pela RAM, não pelos cores:** ~1 run de c154/c262 do
   batch por **4 GB** de RAM (com folga p/ swap). Numa VM de 16 GB, no máximo **2–3
   configs GP-BO batch em paralelo**, não os 4+ que os 8 cores permitiriam.
2. É insumo direto da **A3** (teto/orçamento por config): o batch de c154/c262 precisa de
   provisionamento de RAM explícito no M8, não só de cores.
3. NÃO é vazamento do código (a `del`+`gc` por iteração recicla; o crescimento é o
   `X_baseline`/MC inerente do qNEHVI/JES em n grande). Sem correção de código a fazer —
   é dimensionamento de infra.

## 5. Pendências para a torre
1. **Regenerar `runs_matrix.csv`** se o batch também trocar MMF1→MMF16_20 (território
   da torre; o grid do batch hoje lista MMF1).
2. Os walls medidos (§4) + o perfil de RAM (§4b) alimentam a decisão A3 do autor
   (teto/orçamento por config no M7) e o provisionamento da VM (M8).
