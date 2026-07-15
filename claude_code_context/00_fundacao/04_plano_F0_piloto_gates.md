# Fundação 4/5 — Plano de implementação: molde, Fase 0, piloto (gate) e gates de saída

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

## 22. Plano de implementação — a reta final (3 rodadas com Claude Code) [NOVO — v4.1]

**O que é.** A ordem de ataque da implementação, acordada com o autor (v4.1): **Fase 0** (andaime comum) → **Rodada 1** (todos os PlatEMO/MATLAB) → **Rodada 2** (todos os BoTorch) → **Rodada 3** (uma sub-rodada por standalone). **Implementação SEQUENCIAL com o Claude Code** (uma rodada por vez, cada uma numa sessão dedicada consumindo esta seção + os anexos apontados); **execução em PARALELO assim que cada lado fica pronto** — ao fechar a Rodada 1, o **Mac já começa a bateria MATLAB** enquanto o Claude Code implementa as Rodadas 2–3; a **VM Vertex AI** entra com a bateria Python quando o lado Python fechar (§17.7). *Este plano é um checklist vivo — o piloto pode reordenar itens dentro de uma rodada; o que não muda são os gates de saída (§22.6).*

> **⚠ [v4.2] Antes de executar qualquer cartão:** a leitura profunda do repo real (2026-07-14) está no **Anexo S** — estado do repositório (S.1, com os pré-requisitos do usuário: baixar o e103 e restaurar o PlatEMO completo), correções de âncora (S.2), hazards novos (S.3), cartões com testes de aceitação (S.4), tabela `f_min/f_max` (S.5), ambientes (S.6) e DEF-C5 (S.7). Em conflito entre um checklist abaixo e o Anexo S, **vale o Anexo S** (é o estado-real verificado).

**Como ler os checklists.** Cada algoritmo tem um bloco com: **patches de fidelidade** (a fonte decidida no Anexo K.3/D30 — 🔴🔵🟠🟣🟢), **guardas/hazards [IMPL]** (Anexos L/N), **instrumentação** (export ③ §17.2 + log §17.5 + tempo §17.6), **contrato de RNG/semente** e **contrato de FE**. Os itens têm `arquivo:linha` quando mapeados. A referência completa de cada item está no anexo apontado — o bloco aqui é a **lista de trabalho**; o anexo é o **recibo**.

### 22.0 O molde de rodada (os 5 passos, iguais nas três)

1. **Adapter do stack** — a ponte que traduz `run(alg, problema_id, semente)` na chamada à *main* oficial (§16.5.3), com bounds/sinal (§5.5), semeadura (§5.3) e orçamento/hard-stop (D21).
2. **Wrapper por algoritmo** — ligar cada um + aplicar os **patches de fidelidade** (K.3) e as **guardas** (L/N) do seu bloco abaixo.
3. **As 4 saídas** — export 3-tabelas (§17.1–17.2), log de auditoria `.jsonl` (§17.5), camada de tempo (§17.6), persistência local(/bucket) (§17.7).
4. **Piloto da rodada** — cada algoritmo em 1–2 `(problema, semente)` com verbosidade máxima; **a auditoria de fidelidade é do AUTOR (manual, a posteriori do piloto; o Claude é assistente de leitura — D97/§20)**: percorrer o checklist §17.5.1 no `.jsonl` e conferir o **número-âncora** (Anexo J) quando o setup do paper for reproduzível (±3σ como **faixa-guia**, não limiar automático); medir **timing** (§17.6) — este sim, gate automático bloqueante (D84).
5. **Gate de saída** — os 7 critérios da §22.6. Só então a rodada está "pronta" e sua bateria pode começar.

### 22.1 Fase 0 — andaime comum (uma vez, antes da Rodada 1)

- [ ] **Despachantes + esteira idempotente** (§16.5/§19): `experiments.py`/`experiments.m` na raiz; manifesto `run_id → status` + `skip_existing`; política de erro-duro (try/catch + 1 retry → `failed`, D23); placar de console corrido; no manifesto, os **dois caminhos** e o status de upload (§17.7).
- [ ] **`src/problems.py` validado**: 25 classes; **cache BBOB gerado 1×, versionado por hash, distribuído** (`instance=1`, layout `<raiz-pai>/data/` — D24/A9); *smoke-test* da métrica com o F1 analítico (**v5.2 — D92: HV oficial com ref = 1,1 por coordenada → 1,0433**; o 0,8333 = sanity do front com ref no nadir (1,0), rotulado — L.19).
- [ ] **Gerador de DoE e datasets (v5.2 — D87/D88/D90/D91)**: `11D−1` por **LHS-maximin PRÓPRIO** (K candidatos sobre `Generator(PCG64)` — D87) por `(problema, semente)`, **compartilhado e pareado**; artefato **parquet** (pyarrow escreve; MATLAB lê com `parquetread`); X canônico em bounds nativos + **hash SHA256 do ARRAY DECODIFICADO no manifesto**; injeção nos algoritmos por **patch local** (A1 — os SAEAs não usam `Problem.Initialization`); **+ dataset offline `31D−1` (X,F) pela mesma convenção** (`data/datasets/…` — D90); **+ `artifacts/seeds.json`** (D91); a aceitação da fase inclui o **CP-init** (§5.5/D88).
- [ ] **Sementes**: `{0…28} ∪ {42}`; **offset `+1000·semente`** para os RNGs internos de e81/c149 (D22); receita por stack (§5.3, N.0.2, N.1.3).
- [ ] **Hard-stop**: exceção no ponto único de avaliação quando o saldo zera (`MException('PlatEMO:Termination')` no MATLAB; wrapper de FE no Python) → toda execução termina em **exatamente `31D−1`** (D21). **[v5.2 — D89] O saldo é o do WRAPPER (única fonte nos 2 stacks; o `obj.FE` nativo do PlatEMO não governa o término) e conta avaliações reais DISTINTAS — cache-hit bit-a-bit = 0 FE, logado como evento.**
- [ ] **Schemas**: as 3 tabelas + colunas opcionais (C1/C3), a série de tempo (§17.6), o formato mínimo do `.jsonl` (§17.5) e o **dicionário de colunas C4** (esqueleto, preenchido por algoritmo nas rodadas).
- [ ] **Esqueleto da camada de métrica** (§12, pós-hoc — casca apenas; roda depois da bateria).

---

### 22.5 O que o piloto mede (consolidado — alimenta §17.6, §21.3 e o dimensionamento)

1. **Fidelidade (a dupla prova) — análise MANUAL do autor (D97), não gate automático:** checklist §17.5.1 linha a linha no `.jsonl` + número-âncora do Anexo J onde o setup é reproduzível (formal: c217/DTLZ2 IGD≈6,92e-2, faixa-guia ±3σ). Sem σ publicado ou âncora reproduzível → validação **qualitativa** (mecanismo conforme + patamar sensato), registrada como tal.
2. **Protocolo:** FE final = `31D−1` exato em todos; hash do DoE pareado; sementes/offsets corretos.
3. **Timing/dimensionamento:** piores-casos por stack — GP\@ZDT1-D30 (929 pts: b3, c262, e81), c149 (retreino BNN 60 ép/iter), c122 (pares em D=30), c217 (pares), e7 (1,7M SGD) → extrapolar pelo mix e **dimensionar VM Vertex/dias de Mac** (§21.3). A série `(n_acumulado, tempo_fit_s)` já sai aqui.
4. **Robustez:** taxa de disparo de cada guarda por (algoritmo, problema) — guarda disparando sempre = erro de implementação.
5. **Persistência (§17.7):** local+bucket byte-idênticos (Python); sync de pendentes; `skip_existing` pulando célula pronta.
6. **Smoke-test de integração por stack:** `--modo-rapido` (10% do orçamento) numa fatia 2 algs × 2 problemas × 2 sementes, ponta a ponta (dispatch → adapter → export → consolidação → métrica no F1 analítico).
7. **[D86/v5.1] Pico de memória (RAM) por config-curinga:** medir o pico por run nos curingas (c149 em D=30 = caso-teste canônico do retreino-por-FE; ponte MATLAB↔pymoo por worker) com a higiene do D86 ativa; **teto configurável dispara alarme → entra no gate bloqueante (D84)**. Transforma "esperamos que caiba" em "medimos que cabe".

---

### 22.6 Gates de saída (a definição de "pronto" — por rodada e global)

**[v5.2 — D97] Os 7 critérios têm DUAS naturezas distintas — (A) checagens objetivas AUTOMÁTICAS do harness, e (B) o aval de fidelidade, que é ANÁLISE MANUAL DO AUTOR (a posteriori do piloto; o harness não a executa nem a julga).** Uma rodada só fecha quando, para CADA algoritmo dela: **(B — autor)** (1) mecanismo fiel confirmado **pelo autor** (dupla prova §17.5.1 + Anexo J — juízo manual, ±3σ como faixa-guia); **(A — automáticas)** (2) FE exato `31D−1` (avaliações reais distintas — D89); (3) DoE/semente pareados por hash (CP-init); (4) guardas instaladas e logando; (5) as 4 saídas válidas (3 tabelas §17.2 + `.jsonl` §17.5 + timing §17.6 + manifesto); (6) persistência conforme §17.7 (dois destinos no Python; local no MATLAB); (7) timing do pior-caso registrado. **Global (antes da bateria completa):** o smoke-test multi-máquina passa (Mac local + VM→bucket + consolidação lendo os dois) e o placar/manifesto resistem a um kill+resume (esteira idempotente comprovada, §19).

> **Registro.** Plano acordado com o autor (v4.1): c238 na Rodada 1 (embrulho PlatEMO, N.5); implementação sequencial com Claude Code + execução paralela por stack assim que cada gate fecha; ordem da Rodada 3 = c122 → b5 → c311 → c149 → e81. Decisão em Anexo D/REF-5.

---
---

---

### S.4 — Cartões de execução (work orders com testes de aceitação)

**CARTÃO F0 — Fase 0 (o delta exato do harness; Python no env principal):**
1. `src/experiment.py:36-42` — **remover os 7 imports mortos** (+ `_invoke_runner` :237-271, `_apply_algorithm_overrides` :102-131 e o caminho noisy morto :420-426/:516-521; `ALGORITHM_DISPATCH` :91-99 será substituído na R2/R3 — pode ficar vazio com `raise NotImplementedError` por enquanto).
2. `experiments.py:78-86` — `DEFAULT_ALGORITHMS` → lista oficial por stack (Python: c262, c154, e81, c122, c149, b5, c311); `:95-101` — **remover `MMF16_L3`** (25 problemas); `:104` — `DEFAULT_SEEDS` → `list(range(29))+[42]` (30, §5.3).
3. **Naming novo do export** (§17.7/D55 — **com o token `{exp}`**, Higiene v5.2): `data/experiments/{exp}/{alg}/exp_{exp}_{alg}_{problema}_{semente}__{camada}.parquet` (`exp∈{main,off,batch,sweep-{tier}-{dist}}` — evita a colisão main×sub-estudos) — refatorar `experiment_cache_path` (`experiment.py:330-343`) e a consolidação (`experiments.py:311`); o skip idempotente (`load_memory`, :393-403) passa a checar a base nova.
4. **Dual-write GCS**: novo módulo `src/gcs.py` — `upload(local_path, blob_path)` com `google-cloud-storage`, bucket **`mestrado_experiments`**, projeto `skilled-text-480300-d9`, prefixo `experiments/{alg}/...` idêntico ao local; + `sync_pending()` (re-sobe locais sem blob); manifesto grava os DOIS caminhos + status.
5. **DoE compartilhado + datasets (A1/A7 · v5.2 — D87/D88/D90/D91)**: novo `src/doe.py` — **LHS-maximin PRÓPRIO** (K candidatos sobre `np.random.Generator(PCG64(SeedSequence))`, argmax da distância mínima — D87) por `(problema, semente)`; artefato **parquet** (`data/doe/{problema}/doe_{problema}_{semente}.parquet`, colunas `x0…x{D−1}`; escritor único pyarrow; MATLAB lê com `parquetread`); X canônico em bounds nativos + **hash SHA256 do ARRAY DECODIFICADO** no manifesto; **+ gerador do dataset offline** (`data/datasets/…` — X,F, mesma convenção, derivação SEM alg_id — D90); **+ `artifacts/seeds.json`** (alg_id→int, catálogo uso_id, materialização — D91).
6. **Manifesto + logger §17.5** (`src/manifest.py`, `src/audit_log.py`): run_id, status {ok/retried_ok/failed}+n_retries, wall-clock+desdobramento §17.6, série `(n_acumulado, tempo_fit_s)`, campos S.7; placar de console.
7. Esqueleto `experiments.m` + `src/experiment.m` (receita N.4; corpo real na R1).
**Aceitação F0:** `python -c "import src.experiment"` OK; `python experiments.py --algorithms none --problems MMF1 --seeds 0` monta grid/manifesto sem erro; `src/doe.py` gera DoE com hash estável (2 chamadas = mesmo hash) **e o MATLAB lê o mesmo array via `parquetread` (hash do array decodificado idêntico — D87); amostra do CP-init (§5.5/D88) passa**; upload de um arquivo-teste aparece em `gs://mestrado_experiments/experiments/_smoke/`; unit-test do naming (3 camadas + jsonl + manifesto).

**CARTÃO R1 — PlatEMO/MATLAB (pré-requisito: S.1 itens 1-2 resolvidos pelo usuário):**
Aplicar §22.2 com as correções S.2 (#1-6, #16-19) e S.3 (#1, #4-6). Arquivos NOVOS: `experiments.m` (parfor sobre células; addpath genpath(PLATEMO) por worker; 1 processo por run — A12), `src/experiment.m` (constrói UserProblem com DoE injetado via `initFcn`, `rng(seed)` pós-Problem, `'save',0,'outputFcn',@hook`, hard-stop no evalFcn quando saldo zera, try/catch A8, **`parquetwrite` com `'VariableCompression','brotli'` + `single`, SEM `round` — Higiene v5.2: `zstd` inexiste no R2025a (S.6) e `round3` foi morto pela D53; a consolidação Python reencoda p/ zstd**), `src/hook_output.m` (emite ②③+timing por geração). Patches por algoritmo = §22.2 + S.2 (b4: remover cap 109 e forçar 'cpu'; c217: 2 guardas + N=50 + fix :55 + clip :53; e74: NDSort→objetivos, fix Local_infill:47, **rodar na própria árvore 4.1 (erratum S.8 — SelectTrainData existe)**, Nw=min(100,|Arc|); c141: porte 3 linhas + guard batch-vazio + N=min(100,11D−1); c238: classdef N.5 + remover as 2 linhas Hypervolume; e103: patches (a)-(d) com linhas exatas em **S.2-e103** + fix pm (`IBEAMS.m:43` → proM=1) + fix JudgeModel (diagonal, `:32-34`) + worker dedicado — **centros do RBFN = `⌈√(n_dataset)⌉` com o n injetado (v5.2 — D93; o "NO-OP" está superseded)**; e74: **opção A decidida (D95) — worker dedicado + contrato N.0-4.1**; pisos: fixar MOEAD type=1 explícito).
**Aceitação R1 [v5.2 — D97: duas naturezas]. (A — automática, harness):** cada algoritmo roda MMF1+ZDT1 seed 0 ponta-a-ponta com FE final = 31D−1 exato (avaliações distintas — D89); parquets nas 3 camadas + timing legíveis pelo consolidador; **(B — validação MANUAL do autor, a posteriori, fora da aceitação automática):** c217/DTLZ2 m=3 d=15 → IGD ≈ 6,92e-2 (faixa-guia ±3σ) e leitura do `.jsonl` pelo checklist §17.5.1 nos 7 itens; `parquetwrite` com **brotli** no Mac (fato R2025a — S.6; consolidação re-encoda zstd).

**CARTÃO R2 — BoTorch (VM Vertex; env-main S.6):**
§22.3 + S.2 (#9-11) + S.3 (#9). BoTorch **oficial 0.18.1 do PyPI** (nunca o clone); receitas L.10/L.11 verbatim; decidir B9.5 no piloto; **registrar caminho fused/fallback no manifesto**; persistência local+bucket `mestrado_experiments` + sync.
**Aceitação R2:** c262 e c154 em MMF1+ZDT1 seed 0; FE exato; μ/σ des-padronizados na tabela ③; série `(n_acumulado, tempo_fit_s)` crescendo super-linear no GP (sanity); local+blob byte-idênticos; kill+resume não re-roda célula pronta.

**CARTÃO R3 — standalone (ordem c122 → b5 → c311 → c149 → e81):**
§22.4 + S.2 (#12-15) + S.3 (#2-3, #7-8, #10-12). c122: stub visualizer + `visualization=False` + IGD bypass + **passar `(f_min, f_max)` da S.5 pela assinatura** + cap anti-spin + CPU forçado. b5: venv S.6 + pin desdeo-emo no gate + patch :65-75 (inclui a :75 viva). c311: venv py3.8 + NUNCA importar `evaluate_population` + `run_treed_GP` com assinatura real (S.2#15) + try no `optimize('bfgs')` + σ exportado (extensão B15.5). c149: reconstruir o loop (convenção da RAIZ — S.3#12) + fix `[:, :M]` (linha 46) + z-score + Oracle_eval com desnormalização + seeds/offset + **regra HVI-greedy fechada (v5.2 — D96: normalização pelo arquivo observado; ref = nadir-obs×1,1; desempate σ²; fallback aleatório-do-front)**. e81: env próprio (pins S.6, hoje satisfazíveis) + receita canônica (noise_ablation, NUNCA unconstrained_branin — bug stale confirmado) + Matérn 1-linha em `model_object.py:120-124` + bounds=[0,1] + float64 + assert nystrom==0 + assert |lote|==q + dedup.
**Aceitação R3 (por sub-rodada):** algoritmo roda MMF1+ZDT1 seed 0; FE exato; `.jsonl` §17.5.1; para c122, as predições normalizadas usam a S.5 (log mostra f_min/f_max carregados); para b5/c311, os venvs isolados não co-importam (`python -c "import desdeo_emo; print(desdeo_emo.__file__)"` aponta o overlay certo em cada venv); para e81, o run inteiro em float64 (assert dtype no log).

---

### S.8 — Diagnóstico independente de viabilidade (passe cego v4.3) + estimativas de tempo de execução

**Metodologia (a pedido do autor: 100% código, zero herança da `mapa_literatura_v7`).** Quatro avaliadores **cegos** re-leram o código em 2026-07-14 com uma rubrica fixa ancorada só no contrato de integração (§16.5/§22), proibidos de consultar qualquer score anterior. Como os avaliadores leram a **cópia stageada (parcial)**, cada penalidade por "arquivo faltante" foi **cross-checada contra as listagens completas do repositório real no Mac** — penalidades cuja causa era artefato de staging foram levantadas; os achados de conteúdo (bugs, colisões, guards) foram mantidos. Rubrica: **A = prontidão** (10 = roda como está; 6–7 = wrapper/conversão com caminho claro; 4–5 = reconstrução parcial; ≤3 = quase-inviável, território c168) · **B = custo de adaptação** (0 = config; 2–3 = patches+instrumentação; 4–5 = wrapper/conversão+env próprio; 6–7 = reimplementar componente; ≥8 = reescrever subsistemas).

**⚠ ERRATUM (corrige o S.3#1): `SelectTrainData.m` do e74 EXISTE** — `CLMEA_Code/.../CLMEA/SelectTrainData.m`, confirmado na listagem completa (595 entradas) do repo real; os dois passes anteriores o marcaram ausente por artefato de staging. **Não há helper a reimplementar no e74.** Bônus do mesmo cross-check: a árvore `CLMEA_Code` é um PlatEMO 4.1 **completo** (com `Utility functions/`, `SOLUTION.m`, `PROBLEM.m` e **`UserProblem.m`**) → o e74 pode rodar **dentro da própria árvore 4.1** (opção A, zero colisão) ou fundido no 4.15 (opção B). Idem para outros "ausentes" que eram artefato: os helpers do e103 (DACE/, RBFN/, PopOperate/, TournamentSelection — todos presentes), o `tsemo_runner.py`/`tc_utils.py` do e81, o `MOEAD_select.py` e a árvore quase-completa do desdeo_emo do b5 (recombination/, ReferenceVectors, SelectionBase, CreateIndividuals presentes), o `pf/` do c122 (existe com 4 fronts; o bypass do IGD interno segue valendo por projeto), o `dacefit/predictor` do K-RVEA, o `RadarGrid.m` do CSEA e o mex do c238. **Continuam genuinamente ausentes:** `evolution/visualizer.py` do c122 (stub de 3 linhas) e o notebook do loop do c149 (README aponta p/ Colab → confirma a reconstrução do loop).

**Achados NOVOS do passe cego (entram nos cartões R1/R3):**
1. **Colisões de nome na fusão com o PlatEMO 4.15** — c141: `UpdataArchive.m` (2 args) × `K-RVEA/UpdataArchive.m` (5 args) e `CSO.m` (função) × classdef `CSO` single-objective; e74 (se opção B): `DE.m` × classdef `DE`, `CalHV.m` × `HypE/CalHV.m`, `SelectTrainData.m` (2 args) × `EDN-ARMOEA/SelectTrainData.m` (3 args). **Nuance que desarma o risco:** o MATLAB resolve funções chamadas de arquivos **na MESMA pasta** com precedência máxima (acima do path) — e todos esses call-sites são same-folder → em 1-processo-por-run + `Solve` re-addpath, as colisões se auto-resolvem. **Cartão: renames defensivos opcionais** (`MMRAEA_UpdataArchive` etc.) + smoke-test de resolução (`which -all` no arranque, logado).
2. **c122 fica MAIS barato que o avaliado antes:** com driver próprio injetando o problema via `toolbox.register("evaluate", ...)`, o `problems/factory.py` **nem é importado** → `pymop`, `optproblems`, `autograd` e `matplotlib` **saem do env** (S.6 ajustada). Permanecem: stub do visualizer, `visualization=False`, cap anti-spin, f_min/f_max da S.5, CPU forçado.
3. **b4/c217 sem μ/σ nativo** (classificadores) — já coberto pelo schema C1 (colunas opcionais), mas o passe reforça: o export deles é *semântico* (Label/score + taxas), não numérico de GP — conferir o dicionário C4 no gate.
4. **c149:** o avaliador cego deu A=3 apontando que "a política de seleção sob orçamento não existe no código" — correto sobre o código, mas **a política já está DECIDIDA na SPEC** (D41: q=1 = HVI-greedy(μ); extensão nossa documentada) → não é lacuna de decisão, é implementação prevista. Com isso e os blocos-núcleo reaproveitáveis (~250 linhas: MLP parametrizado, ensemble μ/σ², NSGA-II pymoo), o consolidado fica A=5.
5. **b5:** único ponto duro que sobra é a *arqueologia de ambiente* (pins 2020, overlay sobre desdeo-emo pip 1.1.3 — release máxima do PyPI) + efeitos de import (`usetex`, `filterwarnings` global, `OMP_NUM_THREADS=1` — mitigar com `MPLBACKEND=Agg` e wrapper). **c311:** conferir no gate R3.3 se o `Population` da árvore tem os `*_archive` (fix documentado: copiar o `Population.py` do b5 — mesmo fork; `Problem.py` é byte-idêntico entre os dois, verificado).

**Scores consolidados (cegos + correção de artefato; independentes da mapa v7):**

| id | Algoritmo | A (prontidão) | B (custo) | Fato dominante (do código lido hoje) |
|---|---|---|---|---|
| — | 4 pisos + MOEA/D-média | **10** | **1** | Built-ins do 4.15 completo; DoE via `initFcn`; hard-stop D21 cobre o overshoot |
| b1 | ParEGO | **9** | **2** | Pasta completa (DACE incluso); FE +1/iter exato (zero overshoot); patches P1–P4 pontuais |
| c262 | qNEHVI | **9** | **2.5** | Lib oficial estável; ~150–250 linhas NOSSAS (loop/adapter/export), reaproveitáveis p/ c154 |
| b3 | K-RVEA | **8.5** | **3** | Pasta completa; guard do crash latente (`UpdataArchive:61`/índices de Via) + dedup DoE |
| b4 | CSEA | **8** | **3.5** | Cap 109 + `'cpu'` + guards (randperm/lote-vazio/NaN p0-p1); export semântico (C1) |
| e7 | EDN-ARMOEA | **8** | **3.5** | `genpath` p/ `Dropout/`; guard sqrt-complexo; μ em espaço transladado (log C3); custo alto é de RUN |
| c217 | PC-SAEA | **8** | **4** | 2 guardas da fiação + N=50 + fix `:55` + clip + guard NaN (`CalFitnessPC:17` e R-norm) + log de estados |
| e103 | IBEA-MS | **8** | **4** | Autocontido (artefatos corrigidos); wrapper (a)–(d) + 2 fixes de 1 linha (pm; diagonal do JudgeModel) |
| c141 | MMRAEA | **8** | **3** | Porte de 3 linhas; guard batch-vazio + `N=min(100,11D−1)`; renames defensivos (same-folder resolve) |
| c154 | JES | **8** | **4** | Loop do c262 + estágio JES (~50 linhas) + fallback obrigatório do `RuntimeError` (rota B9.5 no piloto) |
| e74 | CLMEA | **7.5** | **3.5** | **Erratum: SelectTrainData EXISTE**; rodar na própria árvore 4.1 (opção A) ou fundir c/ renames (B); 2 fixes 🔴 + Nw/k_local |
| e81 | qPOTS | **7.5** | **4** | Pacote instalável (pins satisfazíveis); ~6 sítios de seed a offsetar; kernel 1 linha; bounds=[0,1]; env próprio |
| c122 | θ-DEA-DP | **7** | **4** | Stub visualizer (3 linhas) + driver próprio (bypassa factory → env encolhe); cap anti-spin; f_min/f_max prontos (S.5) |
| b5 | Prob-RVEA/MOEA-D | **7** | **4.5** | Árvore quase-completa (MOEAD_select ✓); custo = env arqueológico + patches 65-75/bounds + efeitos de import |
| c311 | TGPR-MO | **6.5** | **5** | Caminho `framework/` limpo; venv py3.9+GPy frágil; archives do Population a conferir; predict por-ponto lento; σ = +15 linhas |
| c149 | LBN-MOBO | **5** | **7** | Loop TEM de ser reconstruído (notebook ausente; driver é pipeline de cluster com TypeErrors); núcleo ~250 linhas reaproveitável; D41 já define a seleção |

**Leitura:** nenhum caso c168 (todos A≥5 — o c168 estava em A≈2–3). A mediana do set é A=8/B=3.5–4: majoritariamente *patches pontuais + instrumentação*. Os 3 mais caros (c149, c311, b5) são exatamente os que os cartões R3 mais detalham. *(Divergências vs o passe cego cru: quase todas por artefato de staging; as duas materiais — e74 ↑ pelo erratum, c149 A 3→5 pela D41 — estão justificadas acima.)*

**Estimativas de tempo de execução (750 runs = 25 problemas × 30 sementes por config).** Estimativas de engenharia por estrutura de código + âncoras dos papers (qNEHVI 6–20 s/iter GPU; c149 167 s treino/iter; c311 build 31,6 s @50k); **o piloto de timing (§22.5) substitui estas estimativas pelos números medidos — é gate, não formalidade.** Premissas: Mac M1 Pro ~8 workers; VM 32 vCPU, 1 run/core, threads=1.

| Stack | Configs | Estimativa (produção contínua) |
|---|---|---|
| Mac/MATLAB | pisos (4) + e103 + c141 | ~1,5–3 dias somados |
| Mac/MATLAB | b1 · b4 · c238 | ~1–2,5 dias cada |
| Mac/MATLAB | e7 · c217 · e74 · b3 | ~1,5–4 dias cada (tail: dacefit/PNN/newrbe em n→929) |
| **Mac total** | 10 configs MATLAB | **~10–22 dias corridos** |
| VM/Python | b5 · c311 | <1 dia cada |
| VM/Python | c122 | ~1–2 dias |
| VM/Python | c262 | ~1,5–3 dias |
| VM/Python | e81 · c154 | ~2–4 dias cada (JES paper-faithful pode ×3–10 → B9.5) |
| VM/Python | **c149** | **~5–8 dias** (retreino do zero por FE — D43: aceitar, medir) |
| **VM total** | 7 configs Python | **~12–22 dias @32 vCPU · ~6–11 @64 vCPU (ou 2 VMs)** |

**Wall-clock do experimento principal** (Mac ∥ VM): **~2–3 semanas** (caminho crítico = MATLAB no Mac ou c149 na VM); com scale-out (VM 64 vCPU/2ª VM + MATLAB em nuvem §21 opcional): **~1–1,5 semana**. **Sub-estudos:** large-batch V-B ≈ **1–2 semanas @32 vCPU** (~4–8 dias @64) — dominado pela parede O(n³) dos GP-BO em n→2500 + retreino do c149 (a lentidão É o dado, §17.6); sweep offline ≈ **3–6 dias** (small/medium rápidos; big c311-only mitigável vetorizando o predict). **Curingas que o piloto pina:** c149, rota do JES (B9.5) e o tail O(n³) do GP em n≈929/2500.
