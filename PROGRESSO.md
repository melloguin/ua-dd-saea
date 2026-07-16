# PROGRESSO — registro-mestre completo da implementação

> **Para quem é este documento.** É o **registro vivo e completo** de tudo que foi feito no pipeline
> experimental do mestrado, consolidando o trabalho de TODAS as instâncias de Claude Code (a
> torre-de-controle + as sessões de implementação). Uma instância **sem nenhum contexto** deve
> conseguir ler isto e incorporar todo o conhecimento do estado atual: o que foi feito, como, os
> desafios, as soluções, as mudanças de rota, e todas as validações rodadas.
> **Fonte da verdade técnica:** `claude_code_context/SPEC_experimentos_v5.2.md`. **Control tower
> operacional:** `ORQUESTRACAO_MESTRE.md`. **Plano:** `PLANO_IMPLEMENTACAO.md` (15 milestones).
> Última atualização: **2026-07-16** (R1-00 fechado; R1-c217 rodando).

---

## 1. O projeto (o quê e por quê)

- **Autor:** Guilherme de Mello Nunes · PPGCC/UFMG · orientadora Gisele · defesa ~set/2026.
- **A dissertação:** survey sistemático + **análise experimental** de **16 algoritmos SA-MOEA** que usam
  explicitamente a **incerteza do surrogate** na otimização (SA-MOO-UU). O algoritmo próprio do autor
  (UA-SA-NSGA-II) é trabalho futuro — NÃO entra nos experimentos.
- **Este repo (`ua-dd-saea`)** é o **pipeline experimental**: roda os 16 algoritmos (de suas
  implementações OFICIAIS em `algorithms/`, sem reimplementar) sobre **25 problemas × 30 sementes**.
- **Bateria principal = 16.500 runs** (12.750 online + 3.750 offline).
- **Grid completo (`runs_matrix.csv`):** 19.950 runs (principal + sub-estudos).

### O desenho experimental (o essencial)
- **Arquitetura A2:** fonte ÚNICA de cada problema em `src/problems.py` (25 classes pymoo); cada
  algoritmo roda da sua implementação; os algoritmos MATLAB avaliam os problemas Python via **ponte
  `pyenv` InProcess**.
- **Protocolo:** `maxFE = 31D−1` (DoE inicial `11D−1` LHS + 20D infills), **hard-stop exato**. 30
  sementes {0–28, 42}. DoE/dataset novos por semente, **compartilhados por (problema, semente)** — todos
  os 21 configs partem dos MESMOS pontos iniciais (invariante D88 = comparação justa).
- **Export de 3 camadas** (Parquet): ① avaliações reais · ② população/geração · ③ surrogate (μ/σ por
  candidato×geração, salvar-tudo) + camada de timing + log `.jsonl` de auditoria. Float32 sem
  arredondamento (D53). Volume estimado ~0,5–0,9 TB (5 volumosos = bucket-only).
- **Métrica pós-hoc** (Python): IGD, **IGD+ (endpoint primário, D70)**, HV, GD, spacing + trajetória.
  Ref do HV = 1,1 por coordenada no espaço normalizado (D69).
- **As 100 decisões (D1–D100)** vivem no Anexo D da SPEC; as 14 do ping-pong pós-auditoria (D87–D100)
  são o coração da v5.2. Índice em `artifacts/decisions.json`.

---

## 2. O modelo de trabalho (como tocamos isto)

- **Torre de controle (uma instância persistente):** mantém a visão holística, monta os prompts de cada
  cartão, salva o contexto no repo, VERIFICA o trabalho de cada sessão (rodando código + lendo), e
  guia o processo. (É "eu" neste documento.)
- **Sessões de implementação (instâncias novas, 1 por cartão):** cada uma lê só o bundle do seu cartão,
  implementa, fecha o gate objetivo, escreve `handoff/{CARTAO}.md` + `handoff/{CARTAO}_RELATORIO-EXECUCAO.md`.
- **Regras firmes (do autor):** **1 sessão = 1 cartão** · **fidelidade = validação MANUAL do autor, a
  posteriori (D97)** (o agente só instrumenta + aplica o gate de encanamento; NUNCA julga/auto-conserta
  fidelidade) · ambiguidade/conflito ⇒ **pára-e-loga (D81)** · pins/ambiente = decisão do autor (D80) ·
  **nunca `git push`** (commits locais).
- **Gate por cartão:** `accept.py {CARTAO}` verde (encanamento objetivo: FE=31D−1, 4 saídas, CP-init,
  guardas) **+** aval de fidelidade manual do autor no piloto.
- **Ordem (D84):** Fase 0 → R1 (MATLAB, Mac) ∥ R2 (BoTorch, VM) → R3 (standalone, VM) → sub-estudos → R4.

---

## 3. A jornada completa, cartão por cartão (o que foi feito, desafios, soluções, validações)

### 🟩 M0 — Preparação & pré-voo — ✅ COMPLETO

**Preparação (antes desta conversa):** auditoria multi-agente da SPEC v5.1 (28 auditores, 85 achados
confirmados) → 15 decisões em ping-pong com o autor → **SPEC v5.2** (D87–D100 tecidas) → correções
mecânicas ("Higiene v5.2") → higiene de repo (e103 vendorizado como arquivos planos; `claude_code_context/`
instalado; scaffolding cards/scripts/handoff) → **setup de infra executado pelo autor** (Mac + VM Vertex
+ bucket). Detalhe em `HANDOFF_MESTRE.md`.

**Nesta conversa, a torre entregou primeiro:** `HANDOFF_MESTRE.md` (orientação completa p/ instância
nova), `START_HERE.md`, `PLANO_IMPLEMENTACAO.md` (15 milestones, didático) e `ORQUESTRACAO_MESTRE.md`
(o control tower técnico: status board, matriz de ambientes, mapa de bundles, armadilhas).

**Sessão 1 — Pré-voo (resolver as 9 pendências de âncora):**
- *O quê:* resolveu as 9 pendências que o `preflight.py` achou (âncoras de patch com caminho
  incompleto/`expect_before` divergente/placeholders).
- *Como/desafios:* Família A (3 paths com `...`) → resolvidos. Família B: b1/b4 tinham a linha alinhada
  por colunas (whitespace) → trocou por token exato robusto; **e81 na verdade estava CERTA** — o
  "DIVERGE" era colisão de basename `acquisition.py` (uma no `_BoTorch`, outra no `e81_qPOTS`) → a
  sessão consertou o **matcher do preflight** (resolução por sufixo de caminho), NÃO a âncora (mexer na
  âncora corromperia o patch real). Família C: `<SHA>` vestigial + e103 faltando no `dir_map`.
- *Validação da torre (ADVERSARIAL):* rodei um workflow de **5 verificadores** (gate-integrity,
  anchor-uniqueness b1/b4, e81-intact, familyA+e103, global). **Todos CONFIRMED.** O ponto sensível
  (a sessão editou o próprio `preflight.py`, o gate) foi provado: **o portão foi REFINADO, não
  enfraquecido** — injetei um `<PIN>` falso numa cópia → ainda dá exit 1. Registrei 2 armadilhas p/ o
  futuro no HANDOFF §11 (b1 patch escopado ao arquivo; âncoras precisam de prefixo de diretório).

### ✅ M1 — Fase 0 (a bancada) — COMPLETA (4/4 cartões, 2026-07-16)

**F0-01-harness** — o andaime comum (Mac, python3 base).
- *O quê:* limpou imports mortos + a POC descomissionada; reescreveu o despachante (`experiments.py`) e o
  adapter A2 (`src/experiment.py`, `ALGORITHM_DISPATCH` vazio); 4 módulos stdlib novos — `src/naming.py`
  (fonte única de caminhos §17.7/D55), `src/atomic_io.py` (escrita atômica D58), `src/manifest.py`
  (fragmento por run + `is_run_done` resume + Scoreboard), `src/audit_log.py` (`.jsonl` §17.5);
  esqueletos MATLAB (`experiments.m`/`src/experiment.m`/`src/hook_output.m` — corpo real deixado p/ R1);
  enriqueceu `accept.py` (check de andaime); `tests/` (17 unittests).
- *Desafio/solução:* descobriu que **`import src.experiment` estava QUEBRADO** (importava 7 runners POC
  inexistentes + sklearn) → a reescrita resolveu. Descobriu também que o **env-main não estava
  provisionado** (o python3 base tinha numpy/pandas/pyarrow mas não pymoo/joblib) → desenhou o andaime
  leve (stdlib + import lazy) p/ rodar no base, e sinalizou o env-main como bloqueio p/ F0-02+.
- *Validação da torre:* rodei `accept.py F0-01-harness` (exit 0), 17 unittests OK, confirmei 0 arquivos
  de algoritmo tocados, `import src.experiment` OK. Verifiquei a realidade do ambiente (base sem pymoo).

**Provisionamento do env-main (ação do autor, guiada pela torre):**
- Criou o venv `env-main` = `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao`
  sobre pyenv 3.11.9, com o núcleo do harness.
- **Mudança de rota:** o pip resolveu **pandas 3.0.3** (major novíssimo). A torre RECOMENDOU fixar em
  `<3` (reprodutibilidade); o autor aceitou → **pandas 2.3.3**. Verifiquei o round-trip de parquet
  (float64 exato) e o pymoo (avalia DTLZ2). Versões finais: numpy 2.4.6, pandas 2.3.3, pyarrow 25.0.0,
  scipy 1.17.1, pymoo 0.6.2, sklearn 1.9.0. Lock em `<venv>/requirements.lock`.

**A arquitetura de ambientes virtuais (`requirements/`, criada pela torre):**
- **Pergunta do autor: quantos venvs? como no MATLAB?** Resposta consolidada em `requirements/README.md`:
  **4 venvs Python** que rodam algoritmos (`env_main`→c262/c154/c122/c149 · `env_e81_qpots`→e81 ·
  `env_b5`→b5r/b5m/moead_media · `env_c311`→c311) + **`env_bridge`** (ponte MATLAB, não roda algoritmo)
  + **`env_c149_fallback`** (condicional). **MATLAB = 0 venv** (1 instalação R2025a; isolamento por
  árvore PlatEMO + ponte).
- Criei `requirements/` com 1 `.txt` por ambiente + `env_matlab.md` + o `README.md` (mapa venv↔alg dos
  21 configs + estratégia).
- **Descoberta honesta / mudança de rota:** `env_b5` (sklearn 0.21.3, x86/2019) e `env_c311` (numpy
  1.20.2) **são INVIÁVEIS no Mac arm64** (sem wheel) — são **VM-Linux por design**. Então NÃO se cria
  tudo no Mac: só o env_main (viável+necessário já); os demais têm o `.txt` pronto e nascem
  *just-in-time* no ambiente certo. Registrado em `envs.json.provisioning`.

**F0-02-doe** — o gerador dos pontos iniciais (env-main).
- *O quê:* `src/doe.py` (LHS-maximin PRÓPRIO D87: K=100 candidatos sobre `Generator(PCG64(SeedSequence))`,
  seleção via `pdist(sqeuclidean)` BLAS-free/determinística; **hash SHA256 do array DECODIFICADO**
  row-major; parquet float64) + gerador do **dataset offline** (D90, X+F) + `seeds.json` (bloco
  `shared_init_artifacts`, D91). **Materializou 750 DoE + 755 datasets.**
- *Validação (da sessão):* a bit-identidade **Python↔MATLAB FECHADA em-sessão** (`check_doe_matlab.m` no
  R2025a → **PASS=1505, FAIL=0**) + um **oráculo independente** (reimplementado do zero) reproduz os
  hashes exatos → spec auto-suficiente.
- *Validação da torre:* `accept.py F0-02-doe` exit 0, 27 testes OK, 750+755 artefatos, `seeds.json`
  válido (bloco antigo intacto + novo).
- *3 decisões p/ o autor:* (1) **seed do DoE = `SeedSequence((semente, problema_id))`** (o `problema_id`
  é o ÍNDICE 0-based em `ALL_PROBLEMS`), sem alg_id → **ratificado** (consistente com D88). (2) a desync
  BBOB (abaixo). (3) o blob de 97 MB → **persistir no repo** (decisão do autor: sem bucket).

**⚠ Reconciliação BBOB (mudança de rota importante):**
- *Descoberta:* o `runs_matrix.csv` usava `BBOB_F1…` mas o CÓDIGO/DoE usavam o token curto `BBOB1…`.
- *Erro da torre + correção:* eu PRIMEIRO recomendei canônico = `BBOB1` (editar só o runs_matrix). **Ao
  LER as fontes**, descobri que estava errado: a **SPEC §4, o `characteristics.csv` e o `runs_matrix`
  JÁ usavam `BBOB_F1`** (o canônico) — o anômalo era o token curto no `experiment.py` (7 chaves de
  dispatch) + os folders do DoE. Corrigi a direção: **canônico = `BBOB_F*`**.
- *Como reconciliei (a torre fez):* renomeei as 7 chaves em `experiment.py` + `seeds.json`, e regenerei
  os 7 BBOB. **Prova-chave:** como o seed usa o ÍNDICE `problema_id` (não a string), os valores do DoE
  ficaram **byte-idênticos ao baseline** (capturei os hashes ANTES: BBOB1 s0 = `1a5143cc…`; DEPOIS:
  BBOB_F1 s0 = `1a5143cc…` idêntico). Reconciliação = só nome; a prova MATLAB PASS=1505 vale por
  identidade de conteúdo. Gate F0-02 segue verde.

**Incidente de concorrência (validação pedida pelo autor):**
- O autor rodou o F0-03 EM PARALELO com o trabalho da torre (BBOB + commits). Avaliei: os dois tocaram
  **conjuntos de arquivos DISJUNTOS** (torre = `experiment.py`/`seeds.json`/docs/data; F0-03 =
  `budget.py`/`export.py`/`gcs.py`/`accept.py`/`tests`). **Zero sobreposição de escrita.** Committei
  cirurgicamente só o meu + F0-02 (4 commits, `git add` explícito por arquivo, nunca `-A`), preservando
  o F0-03 intacto. O F0-03 tinha visto meu rename e "estranhado" o BBOB — expliquei que a preocupação
  dele era stale (movi o DoE junto → consistente; código dele é agnóstico a BBOB).
- Persisti o blob no repo (`git add data/doe data/datasets` = 3010 arquivos = 750 DoE + 750 manifests +
  755 datasets + 755 manifests, ~97 MB).

**F0-03-export** — o contador de orçamento + o exportador (env-main).
- *O quê:* `src/budget.py` (`FEBudget`: fonte única do orçamento; **cache-hit = 0 FE** por X NATIVO
  bit-a-bit — chave `ascontiguousarray('<f8').tobytes()`; `solution_id` dedup-por-X D57; **hard-stop
  EXATO em 31D−1** D21); `src/export.py` (as 4 camadas §17.2; float32 SEM round D53; escrita atômica
  D58; salvar-tudo D54; zstd); `src/gcs.py` (dual-write com import LAZY; bucket-only c154/c122/e81/c149/
  c262 D58); branch F0-03 no `accept.py` (checagens reais); `tests/test_export_budget.py` (17).
- *Desafio/solução (da sessão):* achou um bug real durante a execução — `IndexError` no `write_surrogate`
  com `mu` mono-output (caso b1/ParEGO: μ₁ preenchido, μ₂ NULL). Corrigiu para tratar μ/σ mais curtos
  que M como NULL.
- *Validação da torre (deterministic + ADVERSARIAL):* `accept.py F0-03-export` exit 0, 44 testes,
  regressões F0-01/02 verdes, escopo limpo. Rodei um workflow de **6 lentes** (cada uma escreveu um
  probe e tentou refutar): **5 CONFIRMED** (hard-stop exato — para em 92 p/ D=3, a X que dispara não
  polui o catálogo; cache-hit=0 com bordas -0.0/+0.0/NaN/2D/dtype corretas, 18/18; solution_id dedup;
  float32 IEEE sem round; schema §17.2 + mono-output). **1 PARTIAL:** a escrita é atômica (arquivo final
  NUNCA corrompe, mesmo sob SIGKILL), MAS num **kill duro** sobra um **`.tmp` órfão** (o `finally` não
  roda sob SIGKILL). Não é corrupção. **2 itens de hardening p/ o M8** (registrados): (1) varredura de
  `.tmp` órfãos no arranque (CRÍTICO p/ spot-VMs, que dão SIGKILL); (2) guarda p/ `mu` mais LONGO que M
  (hoje trunca em silêncio). Nota de design (não-bug, D89): -0.0/+0.0 e NaN de payloads distintos contam
  como soluções distintas (2 FE) — ciente na validação de fidelidade.

**F0-04-metrica** — o esqueleto da métrica (env-main). ÚLTIMO da Fase 0.
- *O quê:* `src/metrics.py` (esqueleto pós-hoc: IGD, **IGD+ primária D70**, HV, GD, spacing +
  trajetória; **normaliza por (ideal, nadir) da S.5** — a margem de 10% entra pelo ref=1,1, não na
  normalização; **delega IGD+/HV/GD ao pymoo pinado**, escolha certa; spacing de Schott L1 próprio; a
  tabela `F_MIN_MAX` = cópia congelada da S.5). É o ESQUELETO — a análise completa (agregação das 30
  sementes, testes estatísticos, IGDX, re-espaçamento fino do ref set) é do R4 (D100).
- *Validação da torre (leitura + probe independente):* li o `metrics.py` inteiro (bem-feito). Rodei um
  probe: **âncora D92 batida — HV(BBOB_F1, ref=1,1, normalizado) = 1,04333** (|Δ|=2,7e-5; a derivação
  analítica é `1,21 − 1/6 = 1,0433`); sanity do front (ref=1,0) = 0,83333; normalize(½·nadir) = [0.5,0.5]
  exato; IGD+ ref-vs-ref = 0.0 exato; monotonicidade HV (0.1,0.1)=1.0 > (0.9,0.9)=0.04; HV=0 (não-NaN)
  fora do box; front verdadeiro ZDT1 → IGD+~4.5e-4, HV=0.876. **Tudo correto, 0 correções.**
- *Nits não-bug:* docstring diz "short names" mas as chaves já são `BBOB_F1`; `F_MIN_MAX` é cópia da S.5
  (caveat de DRY se a S.5 mudar).
- **→ Fase 0 COMPLETA:** os 4 gates verdes, 62 testes, módulos `src/` coerentes, sem conflito entre
  sessões nem com a reconciliação BBOB.

### 🟡 M2 — Caso-modelo c217 (2 cartões): R1-00 ✅ · R1-c217 (rodando)

**Provisionamento da ponte `env_bridge` (autor, guiado pela torre):**
- A torre INSPECIONOU o Mac (read-only): a ponte é `~/ponte_teste` (venv sobre pyenv 3.11.9
  `--enable-shared`), que tinha numpy+pymoo 0.6.2 mas **faltava pyarrow**. Ensinei o passo a passo:
  no MATLAB `pyenv` (Executable = `/Users/gmello/ponte_teste/bin/python`, Status NotLoaded — bônus: sem
  restart), e no Terminal `<esse python> -m pip install pyarrow`.
- *Desafio:* os erros "Invalid text character" no MATLAB do autor eram só os **comentários** colados (o
  chat introduz caractere invisível) — não do ambiente. Solução: colar os comandos SEM os comentários.
- *Validação da torre:* confirmei `~/ponte_teste` = numpy 2.4.6 + pymoo 0.6.2 + **pyarrow 25.0.0**, e que
  a ponte **lê um DoE parquet** (`doe_BBOB_F1_0.parquet`, 109×10). Registrei em `envs.json`/`requirements`.

**R1-00-harness** — a infra transversal MATLAB (contrato N.0). Mac.
- *O quê:* o corpo REAL de `experiments.m` (despachante: grid, addpath PlatEMO/worker, skip idempotente,
  parfor), `src/experiment.m` (adapter: ponte→`problems.py`, **DoE carregado** do artefato D63,
  **budget pelo `FEBudget`** com hard-stop 31D−1 — NUNCA o `obj.FE` do PlatEMO D89, export das 4 camadas
  §17.2 `parquetwrite` brotli+single SEM round D53 atômico D58, `.jsonl`, manifesto, **CP-init**),
  `src/hook_output.m` (o outputFcn real), `src/FEBudget.m` + `src/RunBuffer.m` (wrapper de FE + coletor
  ②③/timing, `mkSurrogateRow` espelha o `export.surrogate_row` do Python). Prova por **run-STUB**
  (avaliador trivial pela ponte — SEM algoritmo, que é o c217).
- *Desafios/soluções (da sessão):* (a) a função primária de `src/experiment.m` teve que ser renomeada
  `experiment_run`→`experiment` (o MATLAB exige nome-função = nome-arquivo; o esqueleto do F0-01 não era
  chamável). (b) 2 armadilhas MATLAB↔ponte: acesso a dunder/privado por ponto QUEBRA
  (`py.pymoo.__version__`, `._x`) → usar `py.importlib.metadata.version`/`py.getattr`; o `parquetwrite`
  grava string como `large_string` (Python usa `string`; benigno). (c) 2 decisões DEFERIDAS ao c217:
  evalFcn de LOTE com hard-stop no meio (D61); `real_solution_id` nullable na ③ (o MATLAB não expressa
  int32-NULL).
- *Validação da torre (não rodo MATLAB, mas o resto sim):* escopo **MATLAB-only** (0 `.py`/algoritmo/meus
  docs — o rename foi no `.m`, confirmei via `git diff -- src/*.py` vazio). A saída do STUB **persistiu**
  em `data/experiments/main/stub/` → rodei o **leitor Python independente** (`accept.py R1-00-harness
  --alg stub`) VERDE nos 4 problemas; **li os parquets MATLAB com pyarrow** e confirmei o **schema §17.2
  IDÊNTICO** ao Python (real/pop/surrogate/timing, x/f em float32); **CP-init cross-language MATCH**
  (`manifest.doe_hash` MATLAB = sidecar Python `89b8ce4e…`). Regressões F0-01..04 + 62 testes verdes.
- *Problema pego + FIX da torre (commit `9b454f8`):* ao validar, descobri que o `check_fe` do `accept.py`
  confiava no `--dim` (default 30). Se você passa o D errado, o gate dá **veredito falso** — perigoso p/
  a bateria automática do M8. **Corrigi:** o gate agora deriva o D das colunas `x0..x{D-1}` da própria
  camada ① (correto por construção; `--dim` vira fallback). Provado robusto (`--dim 99` errado agora é
  ignorado, MMF1 segue VERDE) e sem regressão.
- *Ponto p/ veto:* `src/experiment.py` (Python) e `src/experiment.m` (MATLAB) coexistem — nomes iguais,
  runtimes diferentes (benigno, mas confuso).

**R1-c217 — o CASO-MODELO 🔑 — ✅ PROVADO (2026-07-16). O PIPELINE INTEIRO FUNCIONA COM UM ALGORITMO REAL.**
- **Achado principal (herdado por TODO o fan-out MATLAB):** a sessão pegou + corrigiu um **BUG D89** — o `obj.FE` do PlatEMO contava cache-hits (duplicatas de infill) e o `NotTerminated` parava o run CEDO (ZDT1 fechou 926≠929). Fix: `obj.FE = bud.fe` (FEBudget = fonte única, D89) + Termination no MEIO do lote (D61). MMF1/DTLZ2 (sem duplicatas) mascaravam o bug; só o D=30 (ZDT1) o expôs.
- **Verificado pela torre (independente, rodando código):** `accept.py R1-c217` na saída REAL → **VERDE nos 4** (MMF1=61 · **ZDT1=929 apesar de 4 cache-hits** · DTLZ2=371 · DTLZ2_d15=464, todos **31D−1 EXATO**); parquets com schema §17.2 (x/f float32); CP-init OK; li o mecanismo do fix no `experiment.m`. **Escopo limpo:** só o alg c217 + infra compartilhada (`experiment.m` fix D89, `experiment.py` +FIDELITY_PROBLEMS aditivo, `preflight.py` patch-aware) — **0 DoE congelado tocado, 0 conflito BBOB**; regressões F0-01..04+R1-00 verdes.
- **Mudanças "além do plano" (revisadas, sãs):** `FIDELITY_PROBLEMS` (DTLZ2_d15 = config d=15 do paper, SEPARADA dos 25 da bateria); `preflight` patch-aware (aceita STOCK ou APLICADO — não enfraqueceu); `data/doe/DTLZ2_d15/` untracked (DoE de fidelidade; autor decide commitar).
- **FIDELIDADE = pendente, é do AUTOR (D97):** o IGD está longe da guia do paper (≈6,9212e-2) porque **nosso orçamento é ~4× menor** (o paper roda ~2000 FE; nós 31D−1). O autor julga lendo os estados nos `.jsonl` + o IGD na ① crua, com o caveat do orçamento. A torre NÃO julga fidelidade.
- **→ M2 COMPLETO. O caso-modelo provou o pipeline; os outros 8 MATLAB (M3) são multiplicação e herdam o fix D89.**

<!-- (descrição original da tarefa, mantida) -->
**R1-c217 — patches e infra:**
- O 1º algoritmo REAL (PC-SAEA) ponta-a-ponta na infra do R1-00 + a **1ª validação de fidelidade do
  autor** (compara com o artigo). Patches do `alg_c217_pcsaea.md`: as 2 guardas (SAS:21/:39, D17), N=50,
  fix PCS:55, clip do lote ao saldo, DoE injetado (D63), rng após Problem (D59), export/timing pela infra.
  Gate objetivo (FE exato + 4 camadas + jsonl §17.5.1 + CP-init) em MMF1/ZDT1; DTLZ2 p/ a fidelidade.
  **Quando fechar, a torre verifica o encanamento a fundo (1º run real de verdade) e ajuda o autor na
  validação de fidelidade.**

---

## 4. Ambientes (estado real)
- **Mac** (arm64, macOS 12.5.1): MATLAB R2025a (R1 + Fase 0 + pilotos) + os venvs Python. Grava local.
- **VM Vertex** `v5-mestrado` (Debian 12, us-central1-a, micromamba+pyenv): R2/R3 + análise. Grava local
  + bucket `gs://mestrado_experiments` (STANDARD, US multi-região).
- **env-main** ✅ = `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao` (3.11.9;
  numpy 2.4.6/pandas 2.3.3/pyarrow 25/pymoo 0.6.2/scipy 1.17.1/sklearn 1.9). Falta o stack de R2
  (botorch 0.18.1/torch/gpytorch/gcs/deap) NO MESMO venv antes do M4.
- **env_bridge** ✅ = `~/ponte_teste` (3.11.9 --enable-shared; numpy+pymoo 0.6.2+pyarrow 25); MATLAB
  `pyenv` aponta pra ele.
- **env_b5 / env_c311** = INVIÁVEIS no Mac arm64 → provisionar na **VM Linux** (M5) via `requirements/`.
- Detalhe: `requirements/README.md` + `envs.json.provisioning`.

## 5. Todas as validações que a torre rodou (resumo)
- **Pré-voo:** workflow adversarial 5 lentes (todas CONFIRMED; provei que o gate não foi enfraquecido).
- **F0-01:** accept + 17 tests + escopo + realidade do ambiente.
- **F0-02:** accept + 27 tests + 750/755 artefatos + grep BBOB + seeds.json.
- **Reconcile BBOB:** baseline de hashes → rename → regenera → **prova de identidade de hash** → accept.
- **F0-03:** deterministic (accept, 44 tests, regressões) + workflow adversarial 6 lentes (5 CONFIRMED,
  1 PARTIAL não-corrupção).
- **F0-04:** deterministic (4 gates, 62 tests, imports) + leitura do metrics.py + probe independente
  (âncora 1.04333, normalização, IGD+, HV).
- **R1-00:** deterministic (escopo MATLAB-only, regressões, 62 tests) + leitura dos `.m` + cross-language
  (leitor Python sobre a saída MATLAB, schema §17.2 lido, **CP-init hash MATCH**) + **fix do check_fe**.
- Padrão: eu rodo o gate + os testes + leio o código; para infra crítica (pré-voo/F0-03) faço workflow
  adversarial (agentes escrevem probes e tentam REFUTAR).

## 6. Armadilhas / hardening pendentes (reter)
1. **Órfão `.tmp` em kill duro (F0-03)** → varredura no arranque da esteira. CRÍTICO p/ spot-VMs no M8.
2. **`mu`/`sigma` mais LONGO que M truncado em silêncio (F0-03)** → assert/warning defensivo.
3. **b1 (cartão futuro):** o patch `sqrt(mse)` DEVE ser escopado ao `EvolALG.m` do ParEGO (o token
   também existe em `EGO/EvolEI.m`).
4. **Âncoras novas** precisam carregar prefixo de diretório (senão a resolução por sufixo do preflight
   pega a cópia errada em colisões de basename).
5. **Nomes iguais** `experiment.py`/`experiment.m` (benigno).
6. **`F_MIN_MAX` do metrics.py** é cópia da S.5 (regenerar se a S.5 mudar).
7. **`--enable-shared` é Mac-only** (a ponte); MATLAB só no Mac.
8. **-0.0/+0.0 e NaN** contam como soluções distintas (D89 bit-a-bit) — ciente na fidelidade.

## 7. O mapa de arquivos (4 camadas)
- **🟦 Metodologia:** `claude_code_context/SPEC_experimentos_v5.2.md` (fonte da verdade) + os **bundles**
  `00_fundacao…50_analise_R4/` (a SPEC fatiada por `gen_bundles.py` — GERADOS, nunca editados à mão) +
  `REGISTRO_DECISOES`.
- **🟩 Artefatos machine-readable** (`artifacts/`): `runs_matrix.csv` (grid), `envs.json` (ambientes +
  provisioning), `seeds.json` (sementes + DoE), `params.json`, `anchors.json` (patches), `decisions.json`
  (D53–D100), `characteristics.csv` (análise, D98), `repos.lock`.
- **🟨 Orquestração:** `cards/INDEX.md` (25 cartões), `scripts/{preflight,accept}.py` + `accept_r1_00.m`,
  `handoff/*` (por sessão), `HANDOFF_MESTRE.md`, `ORQUESTRACAO_MESTRE.md`, `PLANO_IMPLEMENTACAO.md`,
  `PROGRESSO.md` (este), `requirements/`, `START_HERE.md`.
- **🟥 Código + dados:** `src/` (harness: `problems.py`, `experiment.py`/`.m`, `doe.py`, `budget.py`,
  `export.py`, `gcs.py`, `metrics.py`, `naming.py`, `atomic_io.py`, `manifest.py`, `audit_log.py`,
  `FEBudget.m`, `RunBuffer.m`, `hook_output.m`), `experiments.py`/`.m` (despachantes), `algorithms/`
  (16 repos oficiais + PlatEMO, vendorizados — só se toca com patch de fidelidade), `data/doe` +
  `data/datasets` (pontos iniciais, no repo) + `data/experiments/main/stub/` (saída do run-STUB do R1-00).

## 8. Estado atual + próximos passos
- **Feito:** M0 ✅ · M1 (Fase 0) ✅ · **M2 ✅ (R1-00 + R1-c217 PROVADOS — o pipeline funciona com um algoritmo real; falta só o julgamento de fidelidade do autor, D97)**.
- **Commits recentes (branch `experiment/definitive_algorythms`, nunca pushed):** `[F0-01..04]`, os 4
  `chore/docs` da torre (BBOB reconcile `e8adacc`, data `cf4a4cc`, envs `d1edcf2`, docs `bb72de0`),
  `[R1-00-harness]`, `9b454f8` (fix check_fe), `4b7c79e`/`6ab024d`/`b6cc0c9` (docs/env_bridge).
- **Próximo:** **M3** (fan-out MATLAB: b1,b3,b4,e7,c141,e74,c238,e103,pisos — **herdam o fix D89** e toda
  a infra do c217) ∥ **M4** (R2-00 → c262/c154 na VM). Em paralelo, o **autor faz a validação de fidelidade
  do c217** (D97, com o caveat do orçamento ~4× menor que o paper). Marco crítico seguinte: **M7** (piloto de tempo/memória, PORTÃO
  bloqueante) antes das baterias **M8/M9** ("tudo rodando"). Depois sub-estudos (M10/M11), consolidação
  (M12) e análise (M13/M14/M15).
- **Como uma instância nova assume:** leia este PROGRESSO + `ORQUESTRACAO_MESTRE.md` (status board +
  armadilhas + mapa de bundles) + `HANDOFF_MESTRE.md`. Monte o próximo prompt pelo padrão dos anteriores
  (ver os handoffs). Regra de ouro: verifique cada sessão rodando código + lendo; nunca julgue
  fidelidade (D97); pára-e-pergunte em ambiguidade (D81).
