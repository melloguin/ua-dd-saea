# R1-c141 — RELATÓRIO DE EXECUÇÃO (narrativa completa p/ a torre de controle)

> **Propósito.** Este documento descreve, passo a passo, TUDO o que a sessão de
> implementação do cartão **R1-c141** executou: a verificação de ambiente, a leitura de
> contexto (na ordem prescrita), o reconhecimento do código, as decisões de implementação
> (cada uma amarrada à decisão vinculante que a cobre), os patches, e — o mais importante
> para o veto do autor — **cada trecho de código rodado e o resultado exato obtido**.
> Companheiro do handoff conciso `handoff/R1-c141.md`.
>
> **Data:** 2026-07-16 · **Máquina:** Mac (macOS 12.5.1, arm64) · **Veredito final: VERDE ✅**
> (gate objetivo de encanamento em MMF1 e ZDT1; fidelidade = validação MANUAL do autor, D97).

---

## 0. TL;DR (resposta à pergunta "está 100% pronta?")

- **Sim, para 100% do escopo que o cartão atribui ao implementador**, e **validado
  rodando código** (3 runs MATLAB completos + 10 gates Python + 3 auditorias de dados),
  não por inspeção. O gate objetivo exigido — `accept.py R1-c141 --alg c141 --problema
  {MMF1,ZDT1} --semente 0` → **exit 0** — passou nos dois problemas, e o DTLZ2 (pedido
  para a fidelidade) também fechou verde.
- **A única parte NÃO concluída é, por desenho, do AUTOR (D97):** o aval de fidelidade
  manual, a posteriori, lendo os `.jsonl` (cascata/níveis) e a camada ①. O cartão diz
  explicitamente que eu não julgo fidelidade — instrumentei e entreguei os números-guia
  (§9). O gate por cartão do HANDOFF_MESTRE §8 é "(A) accept.py verde **+ (B) aval de
  fidelidade manual do autor**": o (A) está fechado; o (B) está pendente e é seu.
- **Zero regressão:** F0-01/02/03/04, R1-00 (stub) e R1-c217 (MMF1+ZDT1) re-rodados →
  todos exit 0; `preflight.py` exit 0 (âncora do c141 = APLICADO).
- **Achado estrutural da sessão:** o padrão do caso-modelo c217 **generalizou sem UMA
  linha de mudança na infra transversal** (FEBudget/RunBuffer/hook_output/write_*/
  despachante intocados; `c217_batch_eval` reusado como está) — o custo do fan-out é o
  previsto: copiar `run_c217`, aplicar os patches do `alg_*.md`, escrever o instrument.
- **Honestidade sobre limites do que foi exercitado** (detalhe em §11): 2 guardas novas
  (batch-vazio, +eps do SDE) ficaram ARMADAS mas não dispararam nos 3 runs (nenhum batch
  veio vazio; nenhum min-max degenerou); o sync D89 foi no-op observado (zero duplicata
  de infill nestes runs) mas é load-bearing por desenho (provado no c217/ZDT1); só a
  semente 0 e 3 problemas rodaram (o escopo do cartão; a bateria é M8).

---

## 1. VERIFICAÇÃO DE AMBIENTE (bloqueante — feita ANTES de tudo, D81)

**Código rodado (execução #1):**
```
/Applications/MATLAB_R2025a.app/bin/matlab -batch "pe = pyenv; disp(pe.Version);
disp(pe.Executable); disp(pe.ExecutionMode); s = double(py.numpy.array([1,2,3]).sum());
fprintf('numpy_sum=%g\n', s);"
```
**Resultado:** `3.11` · `/Users/gmello/ponte_teste/bin/python` · `InProcess` ·
`numpy_sum=6`. ✅ Exatamente o exigido pelo prompt (MATLAB R2025a + ponte embutida). A
armadilha conhecida (dot-access a dunder/privado quebra) foi respeitada reusando o
`bridge_ctx` do R1-00 (`py.getattr`/`importlib`), sem nenhum acesso novo por ponto.

## 2. LEITURA DE CONTEXTO (na ordem prescrita pelo prompt — e SÓ ela)

Li, nesta ordem: `HANDOFF_MESTRE.md` (§10/§11) → `handoff/R1-c217.md` (o template) →
`handoff/R1-00-harness.md` (a infra herdada) → `claude_code_context/CLAUDE.md` inteiro →
linha R1-c141 do `cards/INDEX.md` → `10_rodada1_matlab/00_contrato_rodada1.md` (N.0) →
**`alg_c141_mmraea.md` inteiro** → `00_fundacao/01_regras_globais.md` e
`03_contrato_export.md` (§17). **Não li o `alg_*.md` de nenhum outro algoritmo.**
Consultas pontuais à SPEC (permitidas): grep de **D45** (a semântica exata do σ exportado
— linha 1560 + racional v3.0.29 na linha ~2459) e de **DEF-B12.4**; nada mais da SPEC.

## 3. RECONHECIMENTO DO CÓDIGO (o que verifiquei ANTES de codar)

1. **Fontes do c141** (`algorithms/c141_MMRAEA/extracted/MMRAEA/`): li TODOS —
   `MMRAEA.m`, `EAOptimization.m`, `InfillStrategy.m`, `calFitness.m`, `ES_PDR.m`,
   `CSO.m`, `UpdataArchive.m`, `dsmerge.m`, `rbf/rbftlbx/{rbf_build,rbf_predict}.m`.
   Confirmei os 3 pontos do porte (MMRAEA.m:21/:50 `SOLUTION(dec)`; EAOptimization.m:33
   `OperatorGA(dec)` 1-arg), o LHS nativo a substituir (:19-21), o SDE min-max sem guard
   (calFitness.m:6), o crash DEF-A5 (ES_PDR.m:20 indexa `Rank(1:N-sum(Next))` — estoura
   se pool < N), e o kernel MQ c=1/poly=0/mldivide sem regularização (fatos herdados,
   NÃO tocar — bundle).
2. **Infra herdada**: li `src/experiment.m` (o `run_c217` inteiro + export/naming/ponte),
   `src/c217_instrument.m`, `src/FEBudget.m`, `src/RunBuffer.m`, `src/hook_output.m`, o
   `PCSAEA.m` patchado (o padrão em produção), `experiments.m` (despachante — o roster
   default JÁ inclui 'c141') e `scripts/accept.py` (o caminho genérico `--alg` serve o
   R1-c141 sem mudança).
3. **Colisões de path** (hazard classe-e103): grep na árvore PlatEMO 4.15 →
   `UpdataArchive.m` (K-RVEA), `CSO.m` (single-obj), `CalFitness.m` (IBEA e outros),
   `dsmerge.m` (AB-SAEA), `rbf_build/rbf_predict.m` (SAMSO, SACC-EAM-II) colidem com a
   pasta do c141. **Veredito: todas same-folder nos DOIS lados** (cada cópia é chamada
   de dentro da própria pasta) → auto-resolvem (regra S.8; "renames defensivos
   opcionais" do bundle dispensados). Risco residual: o `c141_instrument` vive em `src/`
   (sem same-folder) → resolvido com asserts de precedência de path (§4.6).
4. **Contratos 4.15 verificados no código real**: `UserProblem.m` (probe do construtor =
   `Initialization(1)` via `initFcn`; `Evaluation` com `once=true` passa o LOTE ao
   `evalFcn`; lote VAZIO quebraria o `CallFcn`/`SOLUTION` → confirma o guard [IMPL]) e
   `OperatorGA.m` (matriz entra → matriz sai SEM avaliar; defaults `{1,20,1,20}` = SBX
   proC=1/disC=20 + PM proM=1 → 1/d por variável = exatamente o Balde B do c141).
5. **Preflight**: `expect_before` começando com `<` = descrição (não valida conteúdo) —
   por isso a âncora do c141 podia ser resolvida para literais reais sem quebrar nada.
6. **Artefatos**: DoE de MMF1/ZDT1/DTLZ2 semente 0 presentes em `data/doe/` (30 sementes
   materializadas desde F0-02) — nada a gerar.

## 4. DECISÕES DE IMPLEMENTAÇÃO (cada uma com a decisão vinculante que a cobre)

1. **Injeção do DoE substitui o PAR gera+re-escala** (MMRAEA.m:19-21 → 1 linha): o LHS
   nativo gera em [0,1] e re-escala na :21 — mesma classe de hazard da **D94** (injetar
   só no RHS re-escalaria de novo, distorcendo WFG/BBOB). X0 nativo entra direto na
   `Evaluation`. Cobre também a 1ª linha do porte (SOLUTION→Evaluation).
2. **N = min(100, 11D−1) via `'N'` do UserProblem** (DEF-A5/B12.6): o `Problem.N` do
   c141 é POR SUBPOPULAÇÃO (pool de infill = 2N); nenhuma linha do algoritmo precisa
   mudar. O crash real (D≤9, pool ger.1 ≈ 2(11D−1) < 100) fica coberto — e o MMF1 (D=2,
   N=21) é a PROVA VIVA: com N=100 stock, o ES_PDR estouraria na 1ª geração.
3. **Guard batch-vazio [IMPL]** antes da Evaluation do infill (mandado pelo bundle):
   `if ~isempty(PopNew)`; batch 0 = iteração 0-FE FIEL ao paper (ciclo segue, RNG
   avança, watchdog D60-b é a rede) + evento logado.
4. **Sync D89 herdado do c217** (`Problem.FE = Problem.data.bud.fe` pós-infill):
   obrigatório porque o c141 PODE propor duplicatas (membros do arquivo sobrevivem nas
   subpops e chegam ao infill — `UpdataArchive` até deduplica por `unique` rows). O
   handoff do c217 declara o sync obrigatório p/ todo PlatEMO; fiado igual.
5. **Guard +eps do SDE (D76/L4) em `calFitness.m` — CONDICIONAL**: o alg bundle manda
   "+eps logado"; implementei `den(den==0)=eps` (só o caso degenerado muda; o caso
   normal fica **BIT-IDÊNTICO ao stock** — estritamente melhor p/ fidelidade que somar
   eps incondicional) + 2º output flag p/ log por sítio. **Local**: a âncora
   `c141-sde-eps-L4` apontava `InfillStrategy.m` com placeholders (`line: null`,
   `<SDE sem guard>`), mas o SDE VIVE em `calFitness.m:6` (chamado de MMRAEA:44 — treino
   do Fmodel — e de InfillStrategy:22 — Fit1 do subconjunto, o sítio do hazard [PP L]).
   Patchear a função cobre os 2 sítios com 1 guard. **Corrigi o path/literais no
   `anchors.json`** — mesmo gesto da Sessão 1 (pré-voo, Família A: "achar o arquivo real
   e corrigir o path"); não é escolha de fidelidade, é fato de onde o código mora.
   *Não considerei isso ambiguidade D81 (o guard em si é mandado; só o endereço da
   âncora estava impreciso) — registrado aqui para o seu veto.*
6. **③ = o pool 2N pós-ES_PDR por ciclo** (DEF-C2: "a população SELECIONADA por geração,
   não todo rascunho interno" — as wmax=20 iterações internas são rascunho). σ conforme
   **D45 literal** ("exportar AS DUAS, em colunas separadas; extensão leve p/ a
   população completa"): `sigma_0` = U de ranks |Q1−Q2|+|Q1−Q3|+|Q2−Q3| recomputada
   sobre o pool inteiro (mesmas convenções de ordenação de InfillStrategy:25-35);
   `sigma_1` = std bruto de [Fit1,Fit2,Fit3] por candidato (proxy ensemble ~c149;
   escalas incomensuráveis — aceito pela D45, documentado no `sigma_dict` do manifesto,
   DEF-C4). `real_solution_id` nullable → 1º uso real do fallback `double+NaN` do R1-00.
7. **Instrumentação sem tocar decisão nem RNG (D97)**: `InfillStrategy` ganhou um 2º
   output `info` e `EAOptimization` um 3º (`nsub`) — só capturam o que JÁ é computado
   (verifiquei linha a linha: zero mudança de fluxo); o `c141_instrument` usa apenas
   calFitness/rbf_predict/sort/NDSort (todos determinísticos — **zero consumo de RNG**,
   crítico p/ não perturbar a reprodutibilidade da busca).
8. **Reuso do `c217_batch_eval`** (D61): o handoff do c217 o declara genérico; reusei
   como está (sem renomear — menor diff; nota p/ um rename futuro se incomodar).
9. **`ensure_paths_c141`**: addpath do PlatEMO (se faltar) + da pasta do autor
   (prepend), com asserts de que `rbf_predict`/`calFitness` resolvem p/ a cópia do c141
   (protege as chamadas via path do instrument em qualquer ordem de addpath do worker).

## 5. PATCHES APLICADOS (arquivo:linha, pós-edição)

| Arquivo | Linha(s) | O quê | Decisão |
|---|---|---|---|
| `MMRAEA.m` | :24 | init = `Problem.Evaluation(Problem.data.X0)` (substitui UniformPoint+re-escala+SOLUTION) | D63/D87/D88, classe D94, porte L.7 |
| `MMRAEA.m` | :32/:47/:51 | `tic`/captura flag L4 do treino do Fmodel/`toc` | §17.6, D76 |
| `MMRAEA.m` | :59-63 | guard batch-vazio + `New = Problem.Evaluation(PopNew)` | [IMPL] bundle, porte L.7 |
| `MMRAEA.m` | :69 | `Problem.FE = Problem.data.bud.fe` | D89 (herdado c217) |
| `MMRAEA.m` | :73-77 | chamada `c141_instrument(...)` | D97 (pós-decisão) |
| `EAOptimization.m` | :39 | `OperatorGA(Problem,PopDec2)` | porte L.7; Balde B ✓ |
| `EAOptimization.m` | :55 | `nsub = [\|sub1\|,\|sub2\|]` (3º output) | instrumentação S.7 |
| `calFitness.m` | :8-14 | guard `den(den==0)=eps` + flag (2º output) | D76/L4 |
| `InfillStrategy.m` | (função) | 2º output `info` (nível/Fit/Q/U/flags) — decisões idênticas | instrumentação S.7 |
| `src/experiment.m` | :43, :377-503, :506-530 | `case 'c141'`, `run_c141`, `ensure_paths_c141` | receita N.0/c217 §4 |
| `src/c141_instrument.m` | (novo) | ③ D45 + `.jsonl c141_gen` + timing §17.6 | D45/DEF-C2/S.7 |
| `anchors.json` | c141-sde-eps-L4 | path `InfillStrategy.m`→`calFitness.m:6` + literais reais | D80; precedente Sessão 1 |
| `repos.lock` | c141_mmraea | content-hash re-pinado pós-patch (`5475…8bb8c0`) | D80 (`--write`) |

**O que NÃO foi tocado:** FEBudget.m, RunBuffer.m, hook_output.m, write_*/naming/
manifesto, experiments.m, accept.py, qualquer arquivo Python de `src/`, qualquer outro
algoritmo. `ES_PDR.m`, `CSO.m`, `UpdataArchive.m`, `dsmerge.m`, `rbf_*` = 100% stock.

## 6. EXECUÇÕES DE CÓDIGO E RESULTADOS EXATOS (a prova, em ordem)

| # | Comando | Resultado exato |
|---|---|---|
| 1 | MATLAB `pyenv` + `py.numpy...sum()` | 3.11 · ponte_teste · InProcess · **6** ✅ |
| 2 | `python3 scripts/preflight.py` (pós-edição da âncora) | **pré-voo OK ✓** · `c141-sde-eps-L4 APLICADO calFitness.m` · c217-guards APLICADO · resto STOCK |
| 3 | `python3 scripts/preflight.py --write` | repos.lock: c141_mmraea `sha256_tree=5475…8bb8c0` persistido |
| 4 | MATLAB `experiment('c141','MMF1',0,'main','data')` | **STATUS=ok** · FE **61/61** · cp_ok **1** · n_ger 11 · cache_hits 1 · hash run == sidecar (`89b8ce4e…`) |
| 5 | `accept.py R1-c141 --alg c141 --problema MMF1 --semente 0` (env-main) | 3×[OK] (4 saídas · FE=61, D=2 derivado da ① · DoE bit-a-bit) → **VERDE, exit 0** |
| 6 | MATLAB batch: `experiment('c141','DTLZ2',0,…)` + `experiment('c141','ZDT1',0,…)` | DTLZ2 **ok FE=371/371 cp=1** nger=65 hits=1 · ZDT1 **ok FE=929/929 cp=1** nger=154 hits=1 |
| 7 | `accept.py R1-c141 … ZDT1` e `… DTLZ2` | **VERDE, exit 0** nos dois |
| 8 | Regressão: `accept.py` F0-01/F0-02/F0-03/F0-04 | **4× exit 0** |
| 9 | Regressão: `accept.py R1-00-harness --alg stub --problema MMF1` | **exit 0** |
| 10 | Regressão: `accept.py R1-c217 --alg c217 --problema {MMF1,ZDT1}` | **2× exit 0** |
| 11 | Auditoria pyarrow/json do MMF1 (③②/timing/jsonl) | ver §7 |
| 12 | Auditoria do DTLZ2 (③ M=3, manifesto, IGD_raw) | ver §7/§9 |
| 13 | Auditoria consolidada 3 problemas + IGD ZDT1 | ver §7/§9 |

Wall-clock dos runs (semente 0): MMF1 ~10 s · DTLZ2 ~45 s · ZDT1 ~4 min — dado p/ o
piloto de timing (§22.5).

## 7. AUDITORIA DAS SAÍDAS (o que verifiquei DENTRO dos arquivos gerados)

Com o leitor Python independente (env-main, pyarrow) — execuções #11-13:

- **③ surrogate**: MMF1 **420 linhas** (42/ciclo = pool 2N=2×21, ×10 ciclos) · DTLZ2
  **12.800** · ZDT1 **30.600**. Schema §17.2 com as colunas na ordem canônica;
  `pred_tipo='valor'`, `modelo_flag='RBF-MQ3'`; `mu_*` 100% preenchido; **`sigma_2`
  100% NULL no DTLZ2 (M=3)** — confirma o D45 "2 colunas"; `real_solution_id` =
  double+NaN nullable (MMF1: 37/420 presentes = membros do arquivo no pool) — o
  fallback do R1-00 funcionando como projetado.
- **② pop**: MMF1 113 linhas / 11 gerações (a 11ª = a chamada final do NotTerminated,
  sem ③ — mesmo comportamento do c217); membership = A2 (ND-front) por ciclo.
- **timing §17.6**: 1 retreino/ciclo; `n_acumulado` cresce 21→52 (MMF1) e até 926
  (ZDT1, `tempo_fit_s`=0,482 s no último fit) — a curva O(n³) do mldivide capturada.
- **`.jsonl`**: header (com `N_subpop`, `wmax`, `sigma_dict`) + 1 linha `c141_gen` por
  ciclo (nivel, motivo, ramo_QU, n_front1/2, lote, n_pool, n_sub1/2, resumos fit1/2/3
  e Q/U, U_pool_max, fe, |arquivo|, tempo_fit_s) + guards + footer (status ok, fe_final,
  cp_init true). Guards observados: `cache_hit`×1 (o probe absorvido — receita N.0)
  em TODOS; `hard_stop`×1 em MMF1 e DTLZ2 (o throw do wrapper NO MEIO do lote — D61
  exercitado); ZDT1 SEM hard_stop (o último batch fechou o orçamento exatamente e o
  NotTerminated parou pelo FE sincronizado) → **os DOIS caminhos de término foram
  exercitados** entre os 3 runs.
- **Batch variável**: lotes 2-6 (MMF1), 2-8 (DTLZ2), 2-9 (ZDT1); nenhum lote 0
  observado (guard armado).
- **①**: contagem = 31D−1 exata verificada pelo accept (com D derivado das colunas da
  própria ①, não do `--dim`) nos 3 problemas.

## 8. GATE OBJETIVO — VEREDITO

**(A) accept.py R1-c141 → exit 0 em MMF1 e ZDT1 (o que o cartão exige) + DTLZ2.**
FE=31D−1 exato · 4 saídas válidas · CP-init (hash do artefato = sidecar ✓ pelo accept;
hash da init-X do run = sidecar ✓ pelo cp_ok=1 in-run) · `.jsonl` presente e conforme
§17.5/S.7. **(B) fidelidade = pendente, do autor (D97).** Zero regressão (7 gates
anteriores re-rodados verdes) e preflight exit 0.

## 9. NÚMEROS DE FIDELIDADE (GUIA p/ o SEU julgamento — D97; eu NÃO julguei)

| Problema | FE | IGD_raw (meu cálculo, fora do metrics.py) | \|ND\| | âncora J do paper |
|---|---|---|---|---|
| ZDT1 (d=30) | 929 | **1,7354e-2** (front analítico f2=1−√f1, 10k pts) | 43 | 3,3486e-2 @ **d=20**, 11d+119=339 FE |
| DTLZ2 (d=12, M=3) | 371 | **6,7651e-2** (das-dennis H=99 → esfera, 5050 pts) | 179 | 1,2010e-1 @ **d=20**, 339 FE |
| MMF1 (d=2) | 61 | — (multimodal decisório: IGDX é pós-hoc, D99) | — | — |

**Caveats e achados para a sua leitura:**
1. Orçamento e d divergem do paper (31D−1 nos d canônicos vs 11d+119 @ d=20) — IGDs
   melhores que a âncora são esperados (mais FEs); a comparação justa é do MECANISMO.
   Se quiser a réplica d=20, é 1 entrada em `FIDELITY_PROBLEMS` (padrão DTLZ2_d15 do
   c217); não fiz porque o cartão não pede.
2. **Ramo (Q,U) ativou em 100% dos ciclos nos 3 problemas** (10/10, 64/64, 153/153).
   O I.7 esperava ativação RARA em D baixo/M=2, mas essa expectativa era da leitura
   pré-v2.2 (gatilho "u=5"); com o gatilho REAL do código (">1 candidato", fechado na
   v2.2), o front de [−Fit1,Fit2,−Fit3] (3 ordenações quase-independentes) raramente
   colapsa a 1 ponto. Mecanismo = código oficial; o `.jsonl` tem nivel/motivo por ciclo.
3. **Warning esperado em runtime** (visto no ZDT1): `rbf_build:145` mldivide
   quase-singular, RCOND≈1e-16 — é o comportamento herdado documentado no bundle
   ("mldivide denso sem regularização" + "dsmerge ds=1e-14 deixa quase-duplicatas
   passarem → warning de mau condicionamento"). NÃO é falha; NÃO corrigi (fidelidade).
4. Guardas `batch_vazio` e `sde_eps`: armadas, logam quando dispararem; nenhum disparo
   nestes 3 runs.

## 10. ARTEFATOS, COMMITS E ESTADO DO REPO

- **Commits `[R1-c141]`** (branch `experiment/definitive_algorythms`):
  `6d63f6f` porte 3 linhas + injeção DoE + guard batch-vazio + sync D89 ·
  `a230857` guard L4 + captura da cascata + anchors.json/repos.lock ·
  `2031052` adapter `run_c141` + `c141_instrument` ·
  `271d08f` handoff + `cards/INDEX.md` R1-c141 → ✅. Nenhum blob (outputs gitignored).
- **Outputs** (regeneráveis): `data/experiments/main/c141/exp_main_c141_{MMF1,ZDT1,DTLZ2}_0__{real,pop,surrogate,timing}.parquet` + `.jsonl` + `.manifest.json`.
- Working tree limpo exceto `data/doe/DTLZ2_d15/` (untracked, herdado da sessão c217 —
  não é meu; não toquei).

## 11. HONESTIDADE — o que NÃO foi exercitado / pendências

1. **Fidelidade (B do gate)** = sua, pendente (D97). Os dados p/ julgar estão nos
   `.jsonl` + ① dos 3 runs.
2. **Guardas não disparadas em runtime**: `batch_vazio` e `sde_eps` foram revisadas por
   leitura (lógica de 2-3 linhas) mas nenhum run as acionou. Se quiser prova de disparo,
   um teste sintético (forçar PopObj com objetivo constante em `calFitness`) é trivial —
   não fiz para não inventar teste fora do cartão.
3. **Sync D89 = no-op nos runs observados** (cache_hits=1 = só o probe; o c141 não
   propôs duplicata bit-a-bit nestes 3 runs — CSO/SBX em real raramente repetem bits).
   O sync está fiado e é load-bearing por desenho (o c217/ZDT1 provou o cenário com 4
   duplicatas); sem ele, a 1ª duplicata da bateria reprovaria o gate.
4. **Só semente 0, 3 problemas** — o escopo do cartão. A bateria (25×30) é M8; o
   despachante já tem c141 no roster e o skip idempotente cobre resume.
5. **Caminho `experiments.m`/parfor não re-exercitado para o c141** — os runs foram por
   chamada direta `experiment('c141',…)` (a MESMA função que o `run_cell` do despachante
   invoca; o caminho parfor foi provado no R1-00/c217). Risco residual baixo; o 1º
   `experiments(…,'parallel',true)` da bateria confirma.
6. **Tipo do `real_solution_id` na ③ do c141 = double+NaN** (nullable) — difere do c217
   (int32 all-present, por construção dele). É o fallback projetado no R1-00; a
   consolidação (estágio 3) re-casta p/ int32 nullable. Na prática o tipo não varia
   entre runs do c141 (o pool 2N sempre contém candidato não-avaliado).
7. **Âncora re-endereçada** (InfillStrategy→calFitness, §4.5) — meu único juízo de
   implementação não-mecânico; documentado com racional e precedente p/ seu veto.
8. **Próximos fan-outs**: b1/b3/b4/e7 são cópias diretas do padrão (b1/e7 com o patch
   D94 próprio; b4 com cap-109/cpu — âncoras prontas); c238 exige o embrulho classdef
   N.5 (único não-cópia); e74/e103 NÃO seguem N.0 (worker dedicado, árvore própria).
