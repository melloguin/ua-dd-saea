# T7 + T6 — DOSSIÊ DE EXECUÇÃO (a sessão em série estrita)

> Sessão de implementação · 2026-07-23/24 · branch `experiment/definitive_algorythms`
> Escopo: T7 (fio do sweep) → T6 (batch q=10), em série estrita.
> Entrada: HEAD `0155686` · suíte 328 OK · saída: HEAD `6cd5e82` · suíte **368 OK**.
> Detalhe por cartão: `T7-sweep.md` (+`_REPASSE-A-TORRE`) e `T6-batch.md` (+`_REPASSE-A-TORRE`).

---

## FASE 0 — reconhecimento
Baseline confirmado: git limpo em `0155686`; suíte **328 OK (skipped=22)**; `preflight.py`
exit 0; `portao --varredura --exp off` **12 runs/36 gates VERDE**. Leitura obrigatória +
reconhecimento em fan-out (workflow de 8 leitores + crítico). Achado decisivo já na Fase 0:
**3 premissas dos cartões não se sustentavam** (datasets dos tiers não existiam p/ seed 42;
sem roteamento big no c311; small/lhs = principal sem sufixo) + **defeitos de lançamento**.

## T7 — o fio do sweep (commits `9fcde9f`, `82317a3`, `e328c83`)

**Implementado:** `naming.parse_sweep`/`is_main_variant`/`dataset_variant`; os 3 runners
offline (b5/c311/piso) derivam (tier,dist) do `exp` e gravam no manifesto; gates tier-aware
(`n_dataset_esperado` lê o n do sidecar); **patch MATLAB do e103** (espelho, validado ao
vivo com regressão ①②③ bit-idêntica); teste de paridade entre os 2 stacks.

**Fixes de lançamento (latentes):** 🔴 `enable_bucket`/`run_in_venv` (tornava a bateria
offline irrodável — TypeError engolido como retry) · 🔴 lacuna D23/D60 (b5/piso morriam sem
manifesto ⇒ sumiam da varredura do portão).

**Smokes: os 6 tokens provados** (7 células, 3 gates cada, VERDES) — small-lhs/b5r,
small-mvns/b5r/ZDT4, medium-lhs/b5m/ZDT4, medium-lhs/**e103**/ZDT4 (MATLAB),
medium-mvns/b5m/ZDT4, big-lhs/c311/ZDT4, big-mvns/c311/ZDT4, + medium-lhs/b5m/**MMF16_20**.
Determinismo + não-perturbação **BIT-IDÊNTICOS**. Walls: small ~145 s · medium ~50 min ·
**big ~1 min** (o tier big é BARATO — a âncora do paper estava certa; o caro é o
`SurrogateKriging` O(n³) do b5 no medium).

**Decisões do autor (2026-07-23):** B15.4 = o PISO do tier big (laço do c311 INTOCADO, vira
cartão próprio) · piso PARTICIPA do sweep (SPEC vence, D83) · **MMF1 → MMF16_20** em todo o
sweep (o MMF1 D=2 quebra em mvns [clip→duplicata] e em medium/big [GP singular]; MMF16_20
é o único MMF que sobrevive aos dois modos — validado, 55 min no medium).

## T6 — batch q=10 (commits `4d89702`…`6cd5e82`)

**Implementado:** `budget.maxfe_por_exp` (batch = 11D−1+200q); fio do q nos 4 online
(c262/c154 = greedy sequencial transcrito, contornando a proibição BoTorch
`return_best_only=False`+`sequential`; c149 = HVI-greedy sequencial D42; e81 = fallback
qmaximin DI-25 #3); runner novo **`sobol_batch`** (piso online, ③ vazia); `teto_s` fiado
ponta-a-ponta; gates batch-aware.

**Fixes de lançamento (3º, 4º, 5º da sessão):** 🔴 e81 rodava no stack ERRADO
(`VENV_ONLY_ALGS` esquecia o env próprio — botorch 0.16.1×0.18.1; agora derivado de
`envs.json`) · e81 fallback não gravava a ③ dos completados (achado no 1º smoke real) ·
gate do c149 hard-coded em q=1 · `teto_s` não chegava a c262/c154 (usavam `max_wall_s`).

**Provas de regressão q=1 (o gate mais importante):** c262, c154, c149, e81 —
**①②③④ BIT-IDÊNTICAS** ao run validado em disco (só os `tempo_*_s` de wall variam). O
caminho do experimento principal está provadamente intocado nos 4.

**Smokes do batch (ZDT4/42, q=10):**

| smoke | desfecho | wall/iter |
|---|---|---|
| sobol_batch | ✅ VERDE + determinismo | 2,4 s total |
| e81 | ✅ VERDE (2000/2000 escolhidos) | ~35 min |
| c149 | ✅ VERDE | ~116 min |
| c154 | ⛔ inviável (~30 min/iter → ~100 h) — morto | — |
| c262 | ⛔ inviável (~56 h projetado) — abortado LIMPO pelo projetor | — |

**🔴 Achado central do T6:** os DOIS GP-BO (c154/JES, c262/qNEHVI) são computacionalmente
inviáveis no batch cheio de D≥10 — **mesma causa: o greedy q=10 da AQUISIÇÃO (não o fit) que
cresce com n.** O fio q=10 dos dois está validado (regressão q=1 + ~10 iterações corretas
cada); o smoke completo é DEFERIDO. **Decisão do autor (2026-07-24):** a redução do custo da
aquisição vai à rodada de fidelidade real (D97), não ao smoke — levada à torre no REPASSE
(D-0/D-1). Corolário medido: o batch dos GP-BO é **RAM-bound** (~1 run por 4 GB; o c262 foi
OOM-killed rodando 4 em paralelo em 16 GB) — insumo A3 para o provisionamento M8.

## Estado final
- **Código:** commitado em **12 commits** desta sessão (`0155686`→`26087f1`, todos
  prefixados [T7-sweep]/[T6-batch]/[T7+T6]; o 13º no range, `6be7c53 docs(F1)`, é
  pré-existente/não-desta-sessão). **Nada de código/handoff pendente.**
- **Suíte 368 OK** (baseline 328, **+40**) · preflight 0 · `portao --varredura` VERDE em
  `off` (12/36) e `batch` (3 verdes/6 gates); sweep 6 tokens verdes.
- **Escopo do "fechado":** vale para os CARTÕES T7/T6. Resta **1 gap de robustez offline**
  (b5/piso sem `teto_s` — item 7 abaixo), não-bloqueante.
- **Higiene:** add explícito, staged-check em todo commit, ZERO `git push`, ZERO `git add -A`.
- **⚠ O relatório completo e VERIFICADO está em `T7T6_RELATORIO-EXECUCAO.md`** (este dossiê
  é o resumo; o relatório traz cada comando/resultado + as reconciliações da verificação
  adversarial).

## Definições em aberto para a torre levantar com o autor
*(lista consolidada — a versão detalhada, com instrução explícita à torre, está na §7 do
`T7T6_RELATORIO-EXECUCAO.md`)*
1. **🔑 [T6·central·D97] Redução do custo da aquisição batch dos GP-BO** (c154: restarts/
   raw_samples 2D/50D; c262: MC_SAMPLES/prune_baseline — pede análise). **A decisão-chave.**
2. **[T7·B15.4]** cartão próprio do piso-big (treeGP-média em env_c311).
3. **[T7/T6] Regenerar `runs_matrix.csv`** (torre): piso no sweep + MMF1→MMF16_20 (sweep, e
   avaliar no batch).
4. **[T7]** materializar os ~441 datasets do sweep.
5. **[A3/M8·offline] Custo do sweep medium ~22 h-core** (32 células × ~50 min) — insumo do
   teto/orçamento por config. *(estava só no corpo do T7; subido à lista.)*
6. **[A3/M8·batch]** provisionamento RAM do batch (GP-BO ~1 run/4 GB) + walls medidos.
7. **[robustez·offline] b5/piso NÃO honram `teto_s`** — sem aborto por wall-clock na bateria
   offline (o c311 tem). *(pendência de código; estava fora da lista — subida agora.)*
8. **[cosmético]** `q` no dict de retorno do c149 sai None (manifesto correto).

---
**T7+T6 FECHADOS (no escopo dos cartões) — os 665 tipos de célula da rodada-42 estão
implementados; resta o gap offline b5/piso-teto_s (§7, não-bloqueante) e as decisões do autor
(§1 é a chave). Aguardo a validação final da torre.**
