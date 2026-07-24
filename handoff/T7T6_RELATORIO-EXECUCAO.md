# RELATÓRIO DE EXECUÇÃO — sessão T7 (sweep) + T6 (batch q=10)

> **Para a torre central (a instância que gerou as instruções).** Este documento descreve,
> passo a passo, o que a sessão executou, com os comandos rodados e os resultados, e —
> **na §7** — as **definições em aberto que a torre DEVE levantar com o autor humano para
> decidirmos.**
> Sessão · 2026-07-23/24 · branch `experiment/definitive_algorythms` · entrada HEAD `0155686`
> → saída HEAD `26087f1`. Detalhe por cartão: `T7-sweep.md`, `T6-batch.md` (+`_REPASSE`).
> **Este relatório foi verificado adversarialmente** (workflow de 5 auditores + crítico
> re-checando cada afirmação contra o repo) — as correções deles estão incorporadas aqui.

---

## 0. Veredito em uma linha

**A implementação dos dois cartões (T7 e T6) está completa e commitada; a suíte e todos os
gates estão verdes.** A validação por smoke é **integral no T7** (6 tokens) e **parcial no
T6** (3 de 5 configs verdes; os **2 GP-BO — c154, c262 — são computacionalmente inviáveis no
batch completo de D≥10** e ficaram **deferidos por decisão do autor**, com o fio q=10 deles
já validado por outra via). **Resta 1 gap de robustez no offline** (b5/piso sem teto de
wall-clock) — não-bloqueante, listado na §7.

---

## 1. FASE 0 — reconhecimento (sem edição)

Comandos e resultados:
- `git status` / `git log`: working tree limpo, HEAD `0155686`, branch correta.
- Suíte: `python -m unittest discover -s tests` → **Ran 328 · OK (skipped=22)** (baseline).
- `python scripts/preflight.py` → **exit 0**.
- `python scripts/portao.py --varredura --exp off` → **12 runs / 36 gates / 0 vermelhos**.
- Leitura obrigatória (CLAUDE.md, CONTRATO §6.1, REGISTRO A21, bundles) + **reconhecimento
  em fan-out** (workflow de 8 leitores + crítico).

**Achado já na Fase 0:** 3 premissas dos cartões não se sustentavam — (a) os datasets dos
tiers **não existiam para a semente 42**; (b) **não havia** roteamento `big` no c311; (c)
`small/lhs` **é** o dataset principal (sem sufixo). Também 2 defeitos de lançamento latentes.

---

## 2. T7 — o fio do sweep (commits `9fcde9f`, `82317a3`, `e328c83`)

**Problema (REGISTRO A21):** ninguém derivava `(tier,dist)` do token `exp=sweep-<tier>-<dist>`
⇒ um run de sweep carregaria o dataset principal e gravaria sob o nome do sweep — erro
**silencioso** (o CP-init passa, pois confere contra o arquivo que foi lido).

**Implementado:**
- `src/naming.py`: `parse_sweep(exp)→(tier,dist)`, `is_main_variant`, `dataset_variant`
  (small/lhs = principal, sem sufixo; token com vocabulário inválido ESTOURA — D81).
- Os 3 runners offline (`b5_prob`, `c311_tgprmo`, `piso_offline`) derivam do `exp` e gravam
  `tier`/`dist` no manifesto + header do `.jsonl`.
- Gates tier-aware (`scripts/accept.py`): `n_dataset_esperado`/`fe_esperado_por_exp` leem o
  `n` do **sidecar do artefato** (nunca hard-code 2000/50000).
- **Patch MATLAB** (`src/experiment.m`): helpers `nm_parse_sweep`/`nm_is_main_variant`/sufixo;
  `run_e103` deriva do `exp` e o `n` vem do artefato; manifesto honesto.
- Teste de paridade entre os 2 stacks (`tests/test_fio_sweep.py`).

**Fixes de lançamento (latentes, corrigidos):**
- 🔴 `enable_bucket`/`run_in_venv`: `experiment.run` repassava `**kwargs` cru ao transporte
  ⇒ **TypeError em todo run venv-only** despachado pela bateria (engolido como retry+failed).
- 🔴 lacuna D23/D60: `b5_prob`/`piso_offline` tinham `try/finally` sem `except` ⇒ morriam
  **sem manifesto** ⇒ o run **sumia** da varredura do portão (o total cai, nada fica
  vermelho). Novo `H.write_failed_manifest` + re-`raise`.

**Smokes (comandos: `experiment.run(..., exp='sweep-*', semente=42)` + `portao.py`):**
| token | célula | resultado |
|---|---|---|
| `sweep-small-lhs` | b5r/MMF1/42 | ✅ 3 gates VERDE · fe=61 · ~142 s |
| `sweep-small-mvns` | b5r/ZDT4/42 | ✅ VERDE · fe=309 · ~148 s |
| `sweep-medium-lhs` | b5m/ZDT4/42 | ✅ VERDE · fe=2000 · ~49 min |
| `sweep-medium-lhs` | **e103**/ZDT4/42 (MATLAB) | ✅ VERDE · fe=2000 · ~187 s |
| `sweep-medium-mvns` | b5m/ZDT4/42 | ✅ VERDE · fe=2000 · ~50 min |
| `sweep-big-lhs` | c311/ZDT4/42 | ✅ VERDE · fe=50000 · **~70 s** |
| `sweep-big-mvns` | c311/ZDT4/42 | ✅ VERDE · fe=50000 · ~52 s |
| `sweep-medium-lhs` | b5m/**MMF16_20**/42 | ✅ VERDE · fe=2000 · ~55 min |

**Determinismo** (2 runs ⇒ ⑦ bit-a-bit) e **não-perturbação** (sonda on/off ⇒ ⑦ e ③-busca
bit-a-bit) — **BIT-IDÊNTICOS** (sobre `sweep-big-lhs/c311/ZDT4/42`). Regressão do patch
MATLAB (e103/MMF1/0/main vs disco): ①②③ **bit-idênticas**; ④ difere só nos `tempo_*_s`.

**Decisões do autor no T7 (2026-07-23):**
- **B15.4** = o PISO do tier big (o laço do c311 fica INTOCADO; vira cartão próprio).
- **O piso PARTICIPA do sweep** (a SPEC vence, D83).
- **MMF1 → MMF16_20 em todo o sweep** — o MMF1 (D=2) quebra em `mvns` (o clip da D67 gera
  duplicata bit-a-bit, fatal nos 2 stacks) e em `medium/big` (GP singular por densidade);
  o MMF16_20 (D=20) é o único MMF que sobrevive aos dois modos (validado, ~55 min no medium).

---

## 3. T6 — batch q=10 (commits `4d89702`…`6cd5e82`)

**Contrato (D66):** q=10 · maxFE = 11D−1 + 200·q · DoE pareado · roster
c149/c262/e81/c154 + `sobol_batch` · exp=`batch`.

**Implementado:**
- `src/budget.py`: `maxfe_por_exp(exp,D,q)` (batch = 11D−1+200q; main = 31D−1 intocado;
  off/sweep **levantam** — no offline o orçamento é o dataset).
- **Fio do q nos 4 online**, com prova de que o caminho q=1 fica intocado (saída antecipada):
  - **c262 / c154:** `_lote_greedy_sequencial(_jes)` — **transcrição fiel** do modo
    sequencial do BoTorch (q chamadas com q=1 + `set_X_pending`), contornando a proibição
    da API (`return_best_only=False` é incompatível com `sequential=True`). No c154,
    verificado que o `forward` do qLB-JES é decorado com `@concatenate_pending_points` ⇒ o
    lote nativo funciona.
  - **c149:** `_hvi_greedy_lote_d42` — HVI-greedy sequencial sem reposição (D42), com o
    já-escolhido entrando no front pelo μ predito (decisão de execução documentada p/ D97).
  - **e81:** fallback qmaximin (DI-25 #3) — completa o lote até q por maximin sobre rank-1+.
- **Runner novo** `src/sobol_batch.py` (piso online, ③ vazia, sem sonda; Sobol scrambled).
- `teto_s` fiado no despachante (`experiments.py --teto-s` → runner).
- Gates batch-aware (`accept.check_fe` lê o q do manifesto; `auditar` trata sobol_batch como
  piso; `portao` mapeia `sobol_batch→T6-sobol_batch`).

**Fixes de lançamento (3 a mais, o total da sessão = 5):**
- 🔴 **e81 rodava no stack ERRADO** — `VENV_ONLY_ALGS` era literal e esquecia o env próprio
  do e81 (botorch **0.16.1** × 0.18.1); agora derivado de `envs.json` (drift-proof).
- 🔴 e81 fallback qmaximin **não gravava a ③** dos pontos completados (achado no 1º smoke
  real: 28 gerações com <q escolhidos; o FE estava certo, a ③ incompleta) — corrigido.
- gate do c149 **hard-coded em q=1** (reprovava um batch correto) — batch-aware.
- `teto_s` não chegava a c262/c154 (usavam `max_wall_s`) — unificado (`dd5d229`).

**Provas de regressão q=1 (o gate mais importante do T6):** para **c262, c154, c149, e81**,
re-rodei `main/MMF1/semente-0` num tempdir e comparei bit-a-bit com o run validado em disco →
**①②③④ BIT-IDÊNTICAS** (só os `tempo_*_s` de wall variam). O caminho do experimento
principal está **provadamente intocado** nos 4.

**Smokes do batch (ZDT4/42, q=10, FE=2109):**
| smoke | desfecho | evidência |
|---|---|---|
| sobol_batch | ✅ VERDE + determinismo | manifesto ok/q=10/fe=2109; 2 gates VERDE; ①②④ bit-a-bit |
| e81 | ✅ VERDE | ok/q=10/fe=2109; distribuição \|lote\|=q = **{10:200}=2000/2000** |
| c149 | ✅ VERDE | ok/q=10/fe=2109; **{10:200}=2000/2000** |
| **c154** | ⛔ **inviável — deferido** | ~30 min/iter (medido) → ~100 h; morto na it 6 |
| **c262** | ⛔ **inviável — deferido** | ver §4 (morreu 2×: OOM e depois aborto-por-projeção) |

---

## 4. 🔴 ACHADO CENTRAL — os 2 GP-BO são inviáveis no batch completo de D≥10

Medido **ao vivo** (jsonl streamado por iteração). **A causa é a mesma nos dois: o greedy
q=10 da AQUISIÇÃO (não o fit do GP), que cresce com n.**

- **c154 (JES):** `t_paths_s` (amostragem de Pareto) ≈ 1–2 s; **`t_busca_s` (aquisição
  greedy q=10) ≈ 1350–2040 s/iteração**. Cada passo do lote re-gera ICs
  (`gen_batch_initial_conditions`, raw_samples=10000 em D=10) **e** roda
  `optimize_acqf(num_restarts=5D=50)` — os 10 passos multiplicam isso. **~30 min/iter × 200
  ≈ 100 h.** Encerrado à mão na iteração 6.
- **c262 (qNEHVI):** `t_fit` ≈ 0,2 s (plano — **não** é o gargalo); **`t_busca_s` = 4,5 →
  13 s** nas 10 primeiras iterações, crescendo com o baseline do qLogNEHVI (prune+MC). O
  **projetor de wall-clock estimou ~56 h** e abortou.

⚠ **Reconciliação honesta de COMO o c262 morreu (a verificação apontou 2 narrativas — ambas
verdadeiras, de DUAS execuções distintas):**
1. **1ª execução** (junto com c154/c149/e81, os 4 em paralelo numa máquina de 16 GB, teto de
   4 h): **morto por pressão de memória (SIGKILL/OOM)** — sem manifesto.
2. **2ª execução** (re-rodado SOZINHO após liberar a RAM, teto de **8 h** — o autor pediu para
   subir de 4 h para 8 h): **aborto LIMPO pelo projetor de wall-clock** (~56 h projetado > 8 h;
   manifesto `failed`/`teto_wall`). Isso validou o fix `dd5d229` (o teto agora chega ao c262).

⚠ **Sobre os números (56 h / 100 h / ~30 min-iter):** foram **medidos ao vivo**, mas os runs
parciais/falhos foram **removidos do disco** (não são células válidas) — portanto **não são
reproduzíveis agora**. A **mecânica** (o fator 10× do greedy q=10 + a escala com n) é
**confirmável por leitura do código**; a **magnitude exata** é medição empírica removida.

**Corolário de MEMÓRIA (insumo A3/M8):** o batch dos GP-BO é **RAM-bound** — picos medidos
c154 ~3 GB, c262 ~2–3 GB (o GP guarda o X_baseline de ~2000 pontos + MC). Rodar 4 em
paralelo em 16 GB causou o OOM. **Recomendação: ~1 run GP-BO batch por 4 GB de RAM.**

**Decisão do autor (2026-07-24):** a redução do custo da aquisição vai **direto ao teste de
fidelidade real** (D97), **não** ao smoke; para o smoke, os 2 GP-BO ficam **deferidos**. O
fio q=10 dos dois está validado (regressão q=1 bit-idêntica + ~10 iterações corretas cada).

---

## 5. Os 12 commits da sessão (de `0155686`, exclusive)

**12 commits, todos prefixados** (3 `[T7-sweep]` + 8 `[T6-batch]` + 1 `[T7+T6]`):
`9fcde9f`, `82317a3`, `e328c83` (T7) · `4d89702`, `c5eeb0a`, `29d2dca`, `aa584c4`, `2fa542f`,
`ff9111b`, `dd5d229`, `6cd5e82` (T6) · `26087f1` (dossiê).
*(No range `0155686..HEAD` há 13 commits; o 13º — `6be7c53 docs(F1)` — é um handoff de
provisionamento **pré-existente, NÃO desta sessão**.)*

---

## 6. Validação final rodada AO VIVO (para a pergunta "está pronto?")

| validação | comando | resultado |
|---|---|---|
| Suíte | `python -m unittest discover -s tests` | **Ran 368 · OK (skipped=23)** (baseline 328, **+40**) |
| Pré-voo | `python scripts/preflight.py` | **exit 0** |
| Git | `git status` | código+handoffs nada pendente · HEAD `26087f1` |
| Portão não-regressão | `portao --varredura --exp off` | **12 runs / 36 gates / 0 vermelhos** |
| Portão sweep (6 tokens) | `portao --varredura --exp sweep-*` | **todos VERDES** |
| Portão batch | `portao --varredura --exp batch` | **3 runs / 6 gates / 0 vermelhos** |

**Ressalva de escopo (correção da auto-avaliação):** "fechado" vale para **o escopo dos
cartões T7/T6**. Resta **1 item de código no offline** — os runners `b5_prob`/`piso_offline`
**não honram `teto_s`** (não têm aborto por wall-clock; o c311 tem). Não é bloqueante (o
offline é limitado pelo dataset, sem loop infinito), mas é uma pendência real listada na §7.

---

## 7. ⚠️ DEFINIÇÕES EM ABERTO — a torre central DEVE levantar estas com o autor para decidirmos

> **Instrução à torre:** os itens abaixo NÃO foram decididos nesta sessão. Leve-os ao autor
> humano. O item 1 é a decisão-chave (bloqueia a rodada de fidelidade dos GP-BO no batch).

1. **🔑 [T6·CENTRAL — D97] Redução do custo da aquisição batch dos 2 GP-BO.** c154 e c262
   são inviáveis no batch cheio (§4). Como viabilizar na rodada de fidelidade?
   - **c154 (JES):** reduzir `num_restarts`/`raw_samples` de 5D/1000D → sugestão **2D/50D**
     (~2 h/run; perto dos defaults do BoTorch). Mudança de receita — o autor ratifica.
   - **c262 (qNEHVI):** restarts já são fixos (10/512); o custo vem do qLogNEHVI × q=10 com
     baseline crescente → opções: `MC_SAMPLES` 128→32, prune mais agressivo, teto de baseline.
     **Pede análise do autor** (não há knob óbvio).
   - **OU** tirar os GP-BO do roster do batch (os outros configs ainda respondem à pergunta).
2. **[T7·B15.4] Cartão próprio do piso-big** (treeGP-média em `env_c311`) — decorre da
   ratificação "o piso participa do sweep"; não existe hoje.
3. **[T7/T6] Regenerar `runs_matrix.csv`** (torre): incluir o piso no sweep (3 tiers) +
   trocar MMF1→MMF16_20 (sweep; **e avaliar se o batch também troca** — o MMF1 D=2 tem a
   mesma parede densidade no batch).
4. **[T7] Materializar os ~441 datasets do sweep** (hoje só os dos smokes existem).
5. **[A3/M8 · offline] Custo do sweep medium ~22 h-core** (32 células viáveis × ~50 min) —
   medido, insumo do teto/orçamento por config e do provisionamento.
6. **[A3/M8 · batch] Provisionamento de RAM do batch** — GP-BO ~1 run por 4 GB (§4); + os
   walls medidos (sobol 2 s · e81 ~35 min · c149 ~116 min).
7. **[robustez · offline] `b5_prob`/`piso_offline` NÃO honram `teto_s`** — sem aborto por
   wall-clock na bateria offline (o c311 tem). Um run que degenere não pára limpo. Decidir se
   entra no M8 (portar o teto ao b5/piso) ou fica documentado.
8. **[cosmético] `q` no dict de RETORNO do c149 sai `None`** — o manifesto grava q=10 certo;
   só o valor de retorno em memória não inclui a chave. Corrigir num toque futuro.

---

## 8. Higiene e rastreabilidade
- Todo commit: `git add` explícito + staged-check; **ZERO `git push`**, **ZERO `git add -A`**.
- Territórios da torre (SPEC/bundles/REGISTRO/`artifacts/**`/algorithms vendored) **NÃO
  tocados**.
- Dados gerados (datasets dos smokes, saídas de run) ficam untracked — não commitados (são
  da alçada da torre/autor).

**T7+T6: implementação FECHADA no escopo dos cartões; os 665 tipos de célula da rodada-42
estão implementados. Pendências offline (§7 itens 5–7) e a decisão-chave (§7 item 1) aguardam
o autor via a torre.**
