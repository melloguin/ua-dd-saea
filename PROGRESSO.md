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
- **Grid completo (`runs_matrix.csv`):** 20.850 runs (principal + sub-estudos; DI-35).

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
- **FIDELIDADE = ✅ ACEITA PELO AUTOR, 9/10 (D97, 2026-07-16):** o autor validou o mecanismo (a gestão de confiabilidade do PC-SAEA, Seção 3.3 do paper) operando certo — o estado sai de 3 só quando a validação cruza δ=0.8 (ZDT1 uso-direto 3×/p⁺=0.833; DTLZ2 uso-reverso 2×/p⁻=1.0), o lote vira 6 ("at most six", Alg.5), scores ±1/0, params idênticos ao paper (N=50/δ=0.8/Gmax=3000/σ=0.2). **Insight da dissertação:** sob 31D−1 (~4× menos que o paper) o surrogate fica majoritariamente inativo em δ=0.8 — NÃO é falha, é o mecanismo acertando (surrogate ruim → ignorá-lo é fiel; caveat documentado). O 9 (não 10): a leitura foi comportamental (logs×paper), não auditoria linha-a-linha do código patchado; 1 semente × 4 problemas; + 2 pontas soltas de log **c217-only** (`n_contradicoes==n_empates` = bug de cópia em `c217_instrument.m:71`; `pred_confianca=Error1` = semântica) que NÃO propagam ao fan-out.
- **→ M2 COMPLETO. O caso-modelo provou o pipeline; os outros 8 MATLAB (M3) são multiplicação e herdam o fix D89.**

### 🟡 M3 — Fan-out MATLAB (9 cartões): c141 ✅ · resto ⬜
- **✅ R1-c141 (MMRAEA) — o PRIMEIRO fan-out (2026-07-16). O padrão do c217 GENERALIZOU.** `case 'c141' → run_c141` em `experiment.m` (reusando o corpo do `run_c217`) + `src/c141_instrument.m` (③ σ D45 em 2 colunas) + o "porte 3 linhas" (MMRAEA.m:21/:50→`Problem.Evaluation`; EAOptimization.m:33→`OperatorGA`) + guardas (batch-vazio, `N=min(100,11D−1)` DEF-A5, guard NaN do SDE `+eps` D76/L4). **Herdou o fix D89** (o wrapper de eval compartilhado). **Verificado pela torre:** gate VERDE (MMF1=61/ZDT1=929/DTLZ2=371, FE exato, CP-init); **regressões incluindo o c217 verdes** (o `switch` compartilhado não quebrou); escopo limpo (só arquivos c141 + `experiment.m` + `anchors.json`/`repos.lock`); a ③ σ D45 (sigma_0/1 preenchidas, sigma_2 NULL em M=3) correta. **1 juízo não-mecânico (verifiquei, correto):** a âncora `c141-sde-eps-L4` foi re-endereçada de `InfillStrategy.m` → `calFitness.m` (onde o SDE de fato vive — confirmei). *(O `anchors.json` foi re-indentado inteiro pela sessão — cosmético, as 20 âncoras intactas.)* Fidelidade = aval do autor (D97), pendente. **Ordem do resto:** b3→b1→b4→e7→c238→pisos→e74→e103 (complexos por último).
- **✅ FUSÃO TRIPLA (2026-07-17): c217-fix ∥ (b3 → b4) — a 1ª execução PARALELA coordenada de sessões, e funcionou.**
  O autor rodou o c217-fix numa sessão e b3+b4 (em série) noutra, em paralelo, com o protocolo de coordenação da torre (o b3 codificou primeiro, esperou o `[c217-fix-log]` fechar via watcher, sincronizou, e só então rodou MATLAB + committou; `git add` explícito, nunca `-A`).
  - **✅ c217-fix:** a ponta (A) era de-duplicação real (`n_empates`≡`n_contradicoes` = 1 quantidade com 3 nomes na SPEC → 1 campo, `n_contradicoes`, escolha do autor). A ponta (B) **NÃO era bug** — a §17.2 define `pred_confianca=Error1` (3 citações); o implementador **parou-e-perguntou (D81)** em vez de mudar sozinho, e o autor decidiu manter. Diff mínimo (9+/2− em 1 arquivo). Runs do c217 regenerados, gate VERDE ×4.
  - **✅ R1-b3 (K-RVEA):** injeção DoE classe D94 (par gera+re-escala substituído JUNTO; X0 nativo — provado por probe nos bounds), `KrigingSelect.m` patch de 1 linha só na assinatura (APD byte-idêntico), guard `UpdataArchive:61` **bit-idêntico no caso são** (probe de 20k casos + exaustivo), sync D89 — **exercitado por duplicatas REAIS de infill** (MMF1 +1, ZDT1 +2; sem o sync, o run pararia curto como o ZDT1-926 do c217). Gate VERDE ×3 (61/929/371). ZDT1 ~26 min = pior-caso GP (⚠ ~13h/core p/ 30 sementes → o piloto M7 dimensiona).
  - **✅ R1-b4 (CSEA):** cap109→11D−1, DoE D94, auto→cpu, treino no ARQUIVO INTEIRO (🔵 ARTIGO B4.6/D30), **Balde C {1,15,1,5}→{1,20,1,20}** — o único patch que muda comportamento de busca, **verificado adversarialmente como SUPORTADO pela SPEC** (§6.2:445 lista o b4 nos EAs η=20/20; §6.4:811 nomeia como exceções só c122/c217 — o b4 não é), guard `randperm(size(Next,1))` bit-idêntico. Gate VERDE ×3. Stalls 0-FE são design (gate L>0.9), logados.
  - **Verificação da torre (a mais profunda até aqui):** disjunção provada POR COMMIT (`c217_instrument.m` só no fix; `experiment.m`/INDEX só em b3+b4) → **ZERO conflito entre as 3 sessões e zero com o histórico**; bateria completa de **19 gates** (F0-01..04, R1-00, c217×4, c141×3, b3×3, b4×3, preflight) todos exit 0 + suite unittest OK; **workflow adversarial de 5 lentes → 5/5 CONFIRMED** (patches b3 vs bundle; guard bit-idêntico; patches b4 vs bundle incl. o Balde C; c217-fix mínimo; auditoria parquet 72/72 checks nos 6 runs). Dados congelados (DoE/datasets/seeds) intactos. **0 correções necessárias.**
  - **Pendência de doc-sync registrada:** a SPEC ainda lista `n_empates` em 3 pontos (campo removido) — editar §17.2.1/S.7 + regen bundles numa pausa de docs. Zero consumidor de código afetado.
  - **Itens de veto do autor (avaliação da torre):** (1) âncora b3 concretizada = CORRETA (literais conferem); (2) carimbo `geracao=ciclo` na ③ do b3 = são (filme reconstruível via `pop_por_w` no jsonl); (3) Balde C do b4 = SUPORTADO pela SPEC (recomendo ratificar).
  - **As validações dos PRÓPRIOS implementadores (registro do processo — os relatórios completos estão em `handoff/*_RELATORIO-EXECUCAO.md`):**
    - *Sessão b3+b4:* verificou o ambiente ANTES (ponte→6); `checkcode` estático nos 9 arquivos `.m` (0 erros); **6 runs MATLAB completos** com timings medidos (b3: MMF1 13,6s · ZDT1 ~26min · DTLZ2 140s; b4: 33s · 12min · 175s); gate `accept.py` nos 6 + regressão total (incl. c217/c141 e, na fase b4, o próprio b3); auditoria pyarrow própria dos parquets. **Honestidade exemplar:** o script de auditoria dela acusou FAIL na 1ª passada — ela investigou ANTES de mexer e descobriu que era falso-positivo do próprio script (`large_string` do `parquetwrite` MATLAB vs `string` do Python — mesma coluna lógica, codificação diferente, padrão já aceito no c141); corrigiu o CRITÉRIO do script, não os dados. Cumpriu o protocolo de coordenação à risca: código do b3 escrito primeiro, watcher de 60s detectou o `[c217-fix-log]` fechar, sincronizou, confirmou disjunção, e só então rodou MATLAB + committou cirurgicamente (`git add` explícito).
    - *Sessão c217-fix:* leu as DEFINIÇÕES da SPEC antes de tocar código (§17.2 ×3 citações + M.4 + S.3#4); diagnosticou que (B) NÃO era bug e **parou-e-perguntou (D81)** em vez de "corrigir" — o autor decidiu (manter Error1; de-dup para `n_contradicoes`); re-rodou os 4 runs do c217 (FE exatos, instrumentação-only); provou os campos regenerados no caso ideal (DTLZ2 g214, estado-2: `pred_confianca`=Error1 mantido, p⁻ recuperável no jsonl); regressão incluindo o c141 (que tinha nascido entre as sessões).

### ✅ Faxina de pendências (autor, 2026-07-17) — TODAS as pendências dos 4 algoritmos implementados resolvidas
Varredura exaustiva da torre (handoffs + trackers + preflight + working tree) trouxe 8 itens; o autor decidiu todos:
**D1** âncora b3 concretizada → RATIFICADA · **D2** carimbo `geracao=ciclo` na ③ do b3 → RATIFICADO (schema §17.2 uniforme > coluna extra; filme interno reconstruível) · **D3** Balde C do b4 → **RATIFICADO** (o racional: isolar a variável surrogate — η=20/20 padronizado, exceções nomeadas só c122/c217, verificado adversarialmente na SPEC §6.2/§6.4) · **D4** âncora c141 (`calFitness.m`) → RATIFICADA · **D5** DoE de fidelidade `DTLZ2_d15` → COMMITADO (repo 100% reprodutível; ∉ grid, nunca na bateria) · **D6** doc-sync `n_empates` → AGENDADO p/ a torre na janela pós-Sessão-A · **A1** hardening (.tmp+mu>M) → mini-cartão junto do M7 · **A2** auditoria "9→10" do c217 → entra no dossiê de fidelidade em lote. **Estado: ZERO pendência de decisão nos 4 algoritmos implementados (c217, c141, b3, b4).**

### ✅ SESSÃO A (b1 ParEGO + e7 EDN-ARMOEA) — 2026-07-17, verificada pela torre
- **b1 (ParEGO):** P1 injeção DoE D94 (`ParEGO.m:29-30` JUNTAS), P2 guard `sqrt(max(mse,0))` **ESCOPADO** (a armadilha nº1 do projeto — EvolEI.m do EGO confirmado INTOCADO pela torre), P4 NaN-guard; torneio/λ=100/θ-bounds stock. ③ mono-output (mu_0; mu_1 NULL — o caso D47 que o F0-03 preparou). **Comportamento: excelente** — ZDT1 melhora 136,8× (IGD+ 3,2e-2, HV 0,82 = o melhor ZDT1 do set até aqui); hazard near-dup documentado operando (490 eventos logados, sem crash).
- **e7 (EDN-ARMOEA):** P1 injeção D94 (`EDNARMOEA.m:31-32` JUNTAS), dropout `[0.2,0.5]→[0.1,0.1]` (**mandato explícito do bundle/D30 "ARTIGO", verificado adversarialmente** — não foi decisão unilateral), guard `sqrt(max(var,0))` no Estimate. **Comportamento: fiel ao perfil** — converge devagar (esperado sob 31D−1), e o **gatilho dual está VIVO** (aritmética `RatioOld−Ratio ≷ δ=0.05` visível nos logs: 152 convergência / 48 incerteza no ZDT1). Novo pior-caso de custo: ZDT1 72 min + 3,25 GB RAM (dado p/ o M7).
- **3 incidentes da sessão (todos verificados pela torre):** (1) **fix infra `write_surrogate` O(n²)→O(n)** — a ③ do b1/ZDT1 (757k linhas) travava 3h30; o fix preserva schema/semântica EXATOS (análise linha-a-linha do diff + probe de schema old-vs-new writer: 20 colunas idênticas; sem ele a bateria M8 seria inviável); (2) **sombra de path DRLOS-EMCMO** — cópia idêntica do `Dropout/` vinha antes no genpath e anularia os patches SILENCIOSAMENTE (a regra same-folder não cobre subpastas!); fix `ensure_paths_e7` prepend+asserts; **virou lição obrigatória p/ todo cartão MATLAB** (checar `find` por basename dos patchados; risco máximo no e74); (3) CRLF (higiene, pego pela adversarial da própria sessão).
- **Verificação da torre:** 24 gates verdes (F0×4 + stub + c217×3 + c141×3 + b3×3 + b4×3 + b1×3 + e7×3 + preflight) + unittest OK + diagnóstico de comportamento (trajetórias IGD+ + eventos jsonl) + **workflow adversarial 4/4 CONFIRMED** (writer-fix equivalência; sombra real+neutralizada+varredura dos outros algs [c217/b1/b4 basenames únicos; b3 protegido por same-folder]; patches b1 conformes; patches e7+dropout com base no bundle). **0 correções necessárias.**
- **✅ D6 doc-sync EXECUTADO na janela (torre):** SPEC unificada p/ `n_contradicoes` (2 pontos) + carimbo Balde C no Anexo K do b4 + **bundles regenerados com diff auditado (SÓ os 3 esperados; 27 byte-idênticos)**. Bônus: consertado o bug do `gen_bundles.py` (criava pacote ANINHADO `claude_code_context/claude_code_context/` — regen in-place seguro agora, rmtree limitado às 6 pastas geradas).

### 🔬 Diagnóstico de comportamento b3/b4 (torre, 2026-07-17 — fechando assimetria de validação)
A pedido do autor ("vocês validaram O QUÊ em cada um?"), a torre detectou que b3/b4 não tinham recebido o diagnóstico de comportamento (trajetórias IGD+ + eventos de mecanismo) que b1/e7 e c217 receberam — e o executou: **os 6 runs de b3/b4 convergem MONOTONICAMENTE** (b3 ZDT1 melhora 248× — IGD+ 1,78e-2/HV 0,84, o melhor ZDT1 do set; b4 ramos 1/4 = 140/335 no ZDT1 com stalls 0-FE logados = design). Mecanismos vivos e coerentes com os relatos das sessões (b3 DTLZ2: incerteza 44/48 = aritmética v2.2 δ=4,55 confirmada independentemente). **Célula mais fraca do set: b3/DTLZ2 (HV 0,089, melhora 3,6×)** — perfil do K-RVEA sob 371 FE em M=3 (ramo incerteza dominante), monotônico e mecanicamente correto; marcado como ponto de atenção do dossiê de fidelidade (não é bug).

### ✅ R2-00-harness (infra BoTorch, NO MAC) — 2026-07-17, verificado pela torre (AINDA NÃO COMMITADO)
- **O quê:** a infra transversal da Rodada 2 (contrato N.1), rodando ∥ ao c238 com FAIXAS duras — `src/botorch_harness.py` (691 linhas: pin D79 torch-threads-1/float64/CPU, guarda anti-fork do BoTorch N.2.3, `iteration_seed` = fórmula EXATA do seeds.json D62 truncada a 32 bits, `preserve_global_rng` N.1.3, ganchos D86, `load_doe` com conferência de hash D63, adapter §5.5 normalize/−f/Standardize amarrado ao FEBudget, SnapshotBuffer §17.3/§17.6, export 4 camadas + CP-init com RuntimeError em mismatch, dual-write §17.7 reusável pela R3), dispatch LAZY em `src/experiment.py` (vazio no import — F0-01/base seguem verdes), branch aditivo R2-00 no accept.py (336+/0−), 13 testes novos. STUB `stubpy` (token distinto — NÃO clobberou o `stub` MATLAB do R1-00, verificado).
- **Auto-validação da sessão:** gate 15/15 em MMF1+ZDT1; smoke GCS REAL (ADC Mac): 6 blobs byte-idênticos sha256 + sync + delete verificado; adversarial própria de 4 lentes → 8 endurecimentos no gate/smoke + 1 fix real no harness (n_acumulado §17.6 estava +1 deslocado); suíte 75 OK.
- **Verificação da torre (por execução):** faixa LIMPA (F0 intocado por diff; accept aditivo puro; INDEX intocado); bateria completa verde INCLUINDO todos os gates R1 (nada quebrou); bucket com 0 blobs residuais (read-only); fórmula de seed conferida; fix do teste F0-03 adjudicado legítimo (SkipTest engolido por except Exception — sign-off recomendado).
- **2 MAJORS PRÉ-EXISTENTES confirmados pela torre (fora da faixa do R2-00; NÃO bloqueiam c262 no Mac; DECISÃO antes do M8):** (1) `experiments.py::_run_one` SOBRESCREVE o manifesto rico do runner (perde doe_hash/fe_final/env) e não repassa `data_root`/`enable_bucket` → na bateria, evidência de CP-init evaporaria e dual-write nunca ligaria; (2) **resume × bucket-only quebrado**: `is_run_done` exige as 4 camadas LOCAIS, mas a poda da ③ pós-upload (D58) as remove nos 5 volumosos → re-execução eterna na VM. O "resume lista o bucket" da D58 não existe em código. **→ Ambos entram no mini-cartão de hardening do M7** (junto com .tmp órfãos + guarda mu>M).
- **Estado git:** trabalho na árvore, NÃO commitado (decisão do autor — c238 ainda rodando). Plano: 2 commits explícitos quando o autor der o sinal.

### ✅ R1-c238 (EIM, embrulho classdef N.5) — 2026-07-17/18, verificado pela torre — NOTA DE COMPORTAMENTO: 9/10
- **O quê:** o ÚNICO não-cópia da R1 — o script standalone do EIM virou `EIM.m` (classdef N.5, ORQUESTRAÇÃO PURA: as decisões seguem nas funções STOCK; verificado adversarialmente linha-equivalente ao script). DoE injetado (D63), avaliação só pela ponte/FEBudget (D89), âncora `c238-hypervolume-rm` aplicada (mex Windows-only removido), critério EIMe (Euclidean) conforme bundle/params.json. **Padrão novo: sombra REVERSA** — `UniformPoint.m`/`DTLZ2.m` do repo c238 sombreariam os do PlatEMO (o Solve prependa e nunca remove) → fix `onCleanup(rmpath)` pós-run.
- **Verificação da torre:** bateria 28/28 verde (7 algs ×3 + F0 + stubs + preflight); **adversarial 3 lentes: 2 CONFIRMED + 1 PARTIAL** — o PARTIAL é INFORMATIVO: a auditoria provou que o perigo prático da sombra era MENOR que o estimado (o UniformPoint do c238 é byte-idêntico ao NBI do PlatEMO p/ chamadas 2-arg; classdef>function desde R2019b) — o fix é boa higiene, não conserto de corrupção; +1 janela teórica de vazamento se o assert falhar pós-addpath (edge case registrado). A **auditoria de parquets RECOMPUTOU DO ZERO** e bateu tudo: ② = Σ|pop| = 1.681/60.491/378.029 exatos; ③ = iters×10D = 800/28.800/180.000 com C3 {min,range} 0 linhas ruins; CP-init por sha256 independente; ① init bit-exato ao DoE.
- **Análise de COMPORTAMENTO (torre, parquets+logs → a nota 9/10):** trajetórias IGD+ **monotônicas nos 3** (MMF1 melhora 60×; ZDT1 111,7× → IGD+ 3,96e-2/HV 0,80; DTLZ2 7,9×). **Assinatura EGO de livro-texto:** n_treino +1/iter EXATO nos 3; eim_best DECAI em DTLZ2 (2,6e-1→7,4e-2) e ZDT1 (7,8e-1→~5e-5); a parede O(n³) MEDIDA (fit 3,5s→31s/iter no ZDT1). Ranking vs os 6 pares: DTLZ2 3º/7 · ZDT1 4º/7 · MMF1 6º/7 (pelotão apertado) — exatamente o perfil esperado de um EIM clássico. **Pontos p/ o dossiê:** eim_best ruidoso no MMF1 (40 iters, re-escala {min,range} muda por iter — explicável, confrontar com o paper) + salto tardio no ZDT1 (idem). Guards limpos (880 iters). **⚠ custo: ZDT1 3h55 = novo pior-caso R1 → ~118h/core p/ 30 sementes (dado do M7).**
- **Incidentes operacionais da sessão (lições):** cwd não-persistente; pipe-tail travado pelos MathWorksServiceHost (monitorar término pelo FOOTER do .jsonl, não pelo processo); coexistência limpa com o R2/c262 paralelo.

### ✅ Lote de decisões DI-01…DI-08 (autor, 2026-07-18) — pós-fechamento da onda MATLAB
O autor decidiu EM LOTE as 30+ pendências consolidadas pela torre (agrupadas em 8 decisões).
**Registro canônico e detalhado: `REGISTRO_DECISOES_IMPLEMENTACAO.md`** (raiz — o companheiro de
implementação do REGISTRO_DECISOES_pingpong_v5). Resumo: DI-01 âncoras em bloco ✓ · DI-02 fixes de
infra ✓ · DI-03 convenções de export ③/② ✓ · DI-04 leituras do c262 ✓ · DI-05 política fused-kernel
OFF + doc-syncs (agendado: janela documental) · DI-06 pacote hardening M7 (8 itens, escopo fechado) ·
DI-07 e74 (ndsort-obj FIEL-EQUIVALENTE ratificado; re-sim mantém telemetria com ATENÇÃO ~24,8%;
D74/edges ✓) · **DI-08 camada `__final.parquet` p/ o ND real offline (APROVADA — executar antes do R3)**.

### 📌 Decisão de estratégia (autor + torre, 2026-07-17) — o resto da onda MATLAB
1. **Fidelidade em LOTE no fim da onda** (não mais por-algoritmo): o padrão está provado (c217 9/10 + 3 fan-outs), os mecanismos são isolados por algoritmo, e a comparação lado-a-lado dos 8 é evidência MELHOR (anomalias saltam por contraste). A torre preparará um **dossiê consolidado de fidelidade** (curvas IGD+ × FE + resumo de mecanismo por `.jsonl` + números-guia com caveat de orçamento) para UMA sessão de julgamento profundo do autor. O gate objetivo (`accept.py`) segue por-algoritmo e automático; a verificação da torre segue por-sessão.
2. **Implementação em PARES/SOLOS, sessões novas** (padrão b3+b4 provado; nunca 6 numa sessão — contexto degradaria): **Sessão A: b1+e7** (gêmeos D94) → **B: c238+pisos** (classdef N.5 + os 4 triviais) → **C: e74 sozinho** (árvore 4.1 própria, N.0-4.1) → **D: e103 sozinho** (offline, D93). 4 sessões p/ 6 cartões.
3. **Sem Claudes paralelos no MATLAB** (todos editam o MESMO `experiment.m`/INDEX — merge no arquivo compartilhado = onde erro sutil nasce; não passa no critério "mesma qualidade"). **Paralelismo real e seguro: o R2 (BoTorch, VM)** — stack/máquina/arquivos diferentes; pode rodar em paralelo total com a onda MATLAB.

<!-- (descrição original da tarefa, mantida) -->
**R1-c217 — patches e infra:**
- O 1º algoritmo REAL (PC-SAEA) ponta-a-ponta na infra do R1-00 + a **1ª validação de fidelidade do
  autor** (compara com o artigo). Patches do `alg_c217_pcsaea.md`: as 2 guardas (SAS:21/:39, D17), N=50,
  fix PCS:55, clip do lote ao saldo, DoE injetado (D63), rng após Problem (D59), export/timing pela infra.
  Gate objetivo (FE exato + 4 camadas + jsonl §17.5.1 + CP-init) em MMF1/ZDT1; DTLZ2 p/ a fidelidade.
  **Quando fechar, a torre verifica o encanamento a fundo (1º run real de verdade) e ajuda o autor na
  validação de fidelidade.**

---

### 2026-07-23 — o dia do PARALELO: R3-b5 FECHADO ∥ R3-c311 Fase A (coreografia de 2 fases)
- **✅ R3-b5 (Prob-RVEA mode 7 = b5r · Prob-MOEA/D mode 72 = b5m, OFFLINE, env_b5/Rosetta).**
  `src/b5_prob.py` sobre o harness; 2 patches vendorizados ancorados (b5r re-archive DI-16.16;
  b5m KDE-morto); pin desdeo-emo CRAVADO = vendored (gate R3.2 fechado). 6/6 pilotos, gates 18/18,
  determinismo + não-perturbação bit-a-bit. A sessão descobriu e corrigiu: drift do pyDOE (LHS
  ignora o seed global — fix runner-local), pandas 0.25.3→1.3.5 (autor cravou; 0.25 quebra o
  DataProblem), bug de torre no doe.py/pyarrow-12 (escalou SEM tocar o arquivo compartilhado —
  fix central da torre `9e9ea9c`). Commits `e3ecab1`+`8847f0a`.
- **✅ R3-c311 Fase A (TGPR-MO, OFFLINE, env_c311).** `src/c311_tgprmo.py`: vendor INTACTO + 4
  ganchos runtime (σ B15.5 · predict_batch DI-16.13 · contador único C311-11 · lhs-determinismo);
  2 blocos de sonda 20k geracao=NULL (DI-16.12) bit-idênticos entre si; ② vazia (DI-16.17);
  3 pilotos verdes + determinismo + não-perturbação. Fase B (wiring: dispatch/accept/locks) aguarda
  comando. Commits `4d8a997`+`ba55f18`.
- **✅ Validação-torre do paralelo (DI-26/27, commits `9e9ea9c`+`b782167`):** interseção de arquivos
  entre as 2 sessões = ∅ (forense de git); gates ao vivo 309 OK/preflight 0/não-perturbação 53/
  auditar+final_eval 18/18; workflow 15 agentes (8 auditores + 7 verificação adversarial). 3 fixes
  de infra: `-s`+scrub (PYTHONHASHSEED=0 valia NADA sob `-I`), tree_sha256 sem `.pyc` (repos.lock
  re-lacrado — reprodutível em checkout limpo/VM), warning do final_eval. 1 latente ALTA achado no
  c311 (nd_pos_real float64 — fix cravado p/ a Fase B). Ver REGISTRO PARTE A15.

### 2026-07-23 (tarde) — 🏁 O MARCO: 21/21 CONFIGS IMPLEMENTADOS (fim da fase de implementação)
- **✅ R3-c311 Fase B** (`fb4fc30`/`0a6fe8e`/`74281a0`): fix nd_pos_real (float32, molde b5) +
  wiring (dispatch :162 · check_r3_c311 aditivo · pymoo/optproblems nos locks §3) + e2e do
  despachante (⑦ do subprocesso ≡ piloto direto). Auditoria dedicada da torre: 8,5/10.
- **✅ R3-piso-off** (`35ac50c`..`a92545f`): moead_media (MOEA/D-média, DESDEO mode 12) — a ablação
  "b5 sem σ" (DI-16.1: σ NULL em TODA a ③; N = lattice b5m 50/105 DI-16.4, provado empiricamente:
  gerações 801/381/801 ≡ b5m). A sessão resolveu a contradição σ do prompt POR PRECEDÊNCIA de
  documentos (protocolo D81 exemplar), pegou e corrigiu a regressão do teste de roteamento (B7) e
  2 achados da própria revisão adversarial. 3 pilotos + 6 gates Fase A + wiring Fase B VERDES.
- **✅ Validação-torre do marco (DI-29, `c740753`):** a maior varredura até aqui — suíte 321 ·
  accept 15/15 · auditar+final_eval 24/24 · não-perturbação 53/53 · workflow 8 agentes + auditor
  c311-B; ZERO achado média+ sobreviveu à refutação. **A ablação D77 FUNCIONA**: ZDT1 piso 0,179 vs
  b5m 1,52 (σ-machinery atrapalha 8,5×); DTLZ2 piso espalha (53/105) onde b5m colapsa (6/105);
  MMF1 inverte (rico). check_r3_c311 endurecido (contador contíguo + ambas as fases).
  Ver REGISTRO PARTE A17; decisões DI-30 (B2/B3/D97-b5m) na mesa do autor.

### 2026-07-23 (noite) — AUDITORIA EXAUSTIVA DE FECHAMENTO (DI-31): implementação 100% fechada
- **Workflow `fechamento-implementacao-21de21`**: 9 auditores Opus (todos os 22 configs + infra +
  gates + artefatos + prontidão M7/M8 + integridade de dados) + verificação adversarial (32/32
  procedem). Veredito: **a implementação dos ALGORITMOS está 100% fechada** — infra-core "sem bug
  latente"; runners impecáveis. O "aberto" NÃO é algoritmo: é lançamento/gate (torre corrigiu) +
  build de bateria M7/M8 + o D97 do autor.
- **Torre corrigiu (commit `c9c52f2`):** 🔴 bug de bateria M9 (`experiments.py` rejeitava
  b5r/b5m/moead_media — token-fantasma 'b5'; agora roster DERIVADO dos loaders, drift-proof +
  teste-guard); roster de `experiments.m` sem os 4 pisos online; endurecimento de gate portado da
  DI-29 aos gêmeos b5/piso (contiguidade 1..N + μ/σ em toda a busca) + guard `min([])` nos 3 checks
  online; órfão off/c122 removido. accept 12/12 · suíte **325 OK** · preflight 0.
- **Inventário definitivo no REGISTRO PARTE A19 (DI-31):** ~35 itens rastreados, maioria já fechada;
  o que resta são 6 cartões de build torre (portao.py, enable_bucket, driver ⑦ offline, doc-sync
  SPEC/bundles, hardening M7, sobol_batch/M10) + 7 decisões do autor (A1-A7, com A1=lote D97 a chave).

### 2026-07-23 (fechamento) — DI-32: A1-A7 ratificadas · T4 doc-sync · T1-T3/T5 construídos
- **T4 EXECUTADO** (`e18f968`): SPEC 21→22 configs · nota pyDOE/D62/PYTHONHASHSEED na L.17 ·
  epígrafes N-lattice/varN · CONTRATO §6.1+§7 · sigma_dicts ratificados · bundles regenerados
  (diff auditado: só os 8 esperados).
- **T1-T3/T5 CONSTRUÍDOS** (`1ec0624`): `scripts/portao.py` (driver de portão + lote ⑦-offline,
  com `--varredura`) · `--enable-bucket` ponta-a-ponta · `is_run_done_m` cobra a ⑦ do e103 ·
  probe mecânico de RNG no gate R2-00 (D-17). Suíte **328 OK**.
- **PROVA DE FOGO do portão — varredura TOTAL do data/: 66 runs · 147 gates · 61 verdes · 5
  vermelhos = EXATAMENTE as fatias stale pré-retrofit já conhecidas** (ZDT1 de c238/c262/e7 sem
  sonda + c154/DTLZ2 + c217/DTLZ2_d15) — a rede pegou o que devia; essas células re-rodam na
  varredura semente-42 com o código retrofitado. **A1/A4 (lote D97 + VM) = o plano de validação
  definitiva semente-42 acordado com o autor (3 máquinas, tudo × 25 problemas, seed 42).**

### 2026-07-24 — T7/T6 FECHADOS + F1 3/4 máquinas + VALIDAÇÃO FINAL da torre (DI-34)
- **T7 (fio do sweep) + T6 (batch q=10)** entregues pela sessão dupla (12 commits): exp=sweep
  fiado nos 2 stacks; orçamento D66; lote nativo nos 4 online; `sobol_batch`; 2 bugs de
  lançamento achados E corrigidos pela sessão (kwargs-transporte; e81 no stack errado);
  achado central de custo: **GP-BO inviáveis no batch cheio (c154 ~100h, c262 ~56h — decisão
  DI-35)**. Auto-auditoria adversarial da sessão corrigiu o próprio relatório.
- **F1**: Mac A, VM-1 e VM-2 100% (handoff v4; 2 D80 resolvidas por veredito; VM-2 de primeira).
- **Validação final da torre**: portão 78/180 (só os 5 stale) · spot b5r bit-idêntico ·
  workflow 10 agentes ⇒ **5 achados confirmados, TODOS corrigidos** (`c2a522d`): 🔴 fio do q
  (3º bug da camada de lançamento) + c149 lote + e81 straddle + e103 tier/dist + binding por
  hash no auditar. **Fila do congelamento executada** (`b3675ef`): datasets sweep-42,
  tree_sha256 sem lixo-de-SO (hashes Mac≡VM), torch pinado na intenção, receitas canônicas
  dos locks, RUNBOOK §6-bis. Ver REGISTRO A22; decisões DI-35 na mesa do autor.

### 2026-07-25 — DI-37 RATIFICADO · DOC-SYNC FINAL · REPO PRONTO PARA O PUSH+TAG 🔒→🚀
- **Autor ratificou os 7 itens DI-37 em bloco** (c154 batch termina no teto=DADO · c262 cheio
  2,2h · knob per-D 1D/50D · caveat D97 · ⑦-teto=rito-piso · não-perturbação teste-only ·
  confirmações T8). Nenhuma mudança de código — tudo já estava shipado. REGISTRO PARTE A25.
- **Doc-sync final executado:** SPEC ganhou o bloco do TETO UNIVERSAL 12h em §5.1 (gap real —
  nunca tinha sido anotado) + §V-B.4 custo medido do batch + §V-B.5 caveat + L.10/L.11;
  params.json +3 chaves (diff semântico auditado); bundles regen (4 arquivos esperados);
  RUNBOOK atualizado (3 máquinas/Mac B FORA, censo 695 células, comando batch, expectativa
  teto_wall das 5 c154-batch).
- **Auditoria de prontidão (13 agentes)**: 7 achados confirmados — 3 ALTA no próprio doc-sync da
  torre; corrigidos (SPEC §5.1 verdadeira: teto = Python-only, BoTorch aborta por PROJEÇÃO sem
  parquets; check_fe skip sancionado; heading V-B.5; e103-sweep no RUNBOOK; 19.950→20.850;
  headers q). REGISTRO A26. **Sobrou 1 decisão: 🔴 DI-38** (como materializar a curva parcial do
  c154 sob teto — rec.: cartão T10 rito-truncamento BoTorch ANTES do push).
- **Próximo ato: DI-38 (autor) → [T10 se (b)] → push + tag `rodada-42-freeze` (AUTOR) → F2 → disparo.**

### 2026-07-24 (noite) — T8+T9 FECHADOS · 23/23 configs · fix do projetor · PRONTO P/ CONGELAR
- **T8 treed_media** (piso-big, 6-14s/célula!) + **T9 calibração** (c262 batch = 2,2h CHEIO sem
  knob; c154 FLOOR ≥30h → decisão DI-37; knob per-D shipado; regressão q=1 bit-a-bit) — 4º
  paralelismo limpo (interseção vazia; one-liners autorizados).
- **Validação final da torre (DI-36):** 1 ALTA corrigida — projetor de wall-clock não-batch-aware
  (abortaria espuriamente o c262 batch; fix `acfac4b` com passo inferido, q=1 bit-igual) + a
  causa-raiz do "56h" do T6 corrigida (artefato do projetor) + regressao_q1.py preservado.
- **Estado: suíte 391 OK · portão 84/198 (só 5 stale) · 23/23 configs smoked · DI-37 na mesa →
  depois: push/tag do autor → desbloqueio das 3 máquinas → DISPARO da rodada-42 (~695 células).**

## 4. Ambientes (estado real)
- **Mac** (arm64, macOS 12.5.1): MATLAB R2025a (R1 + Fase 0 + pilotos) + os venvs Python. Grava local.
- **VM Vertex** `v5-mestrado` (Debian 12, us-central1-a, micromamba+pyenv): R2/R3 + análise. Grava local
  + bucket `gs://mestrado_experiments` (STANDARD, US multi-região).
- **env-main** ✅ = `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao` (3.11.9;
  numpy 2.4.6/pandas 2.3.3/pyarrow 25/pymoo 0.6.2/scipy 1.17.1/sklearn 1.9). Falta o stack de R2
  (botorch 0.18.1/torch/gpytorch/gcs/deap) NO MESMO venv antes do M4.
- **env_bridge** ✅ = `~/ponte_teste` (3.11.9 --enable-shared; numpy+pymoo 0.6.2+pyarrow 25); MATLAB
  `pyenv` aponta pra ele.
- **env_b5 / env_c311** = **PROVISIONADOS NO MAC (2026-07-22/23)** via micromamba x86_64/Rosetta
  (receitas EXECUTÁVEIS + locks em `requirements/PROVISIONAMENTO.md`); a VM Linux (M8) recria dos
  mesmos locks (manylinux cp37/cp38, sem Rosetta).
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

## 8. Estado atual + próximos passos *(atualizado 2026-07-23 — pós-paralelo b5∥c311-A)*
- **🏁 PLACAR: 21 de 21 CONFIGS IMPLEMENTADOS E VALIDADOS (2026-07-23).** A fase de implementação
  de algoritmos ACABOU — resta só o runner trivial `sobol_batch` + plumbing q=10 (pertencem ao M10).
  M5 e M6 COMPLETOS. O caminho agora: ratificações DI-30 → doc-sync SPEC/bundles (destravado:
  nenhuma sessão aberta) → lote D97 do autor → hardening pré-M7 → **M7 (PORTÃO de timing)** → VM/M8.
- **Feito:** M0 ✅ · M1 (Fase 0) ✅ · M2 ✅ · **M3 (fan-out MATLAB) ✅ 10/10** · **M4 (R2: R2-00 ✅ +
  c262 ✅ + c154 ✅)** · **M5.1/R3-c122 ✅** (3/3 gates, `29e8539`) · **M5.3/R3-e81 ✅** (qPOTS, 18/18 ×3, nota 9/10 — o anti-c149; validação DI-24) · **M5.2/R3-c149 ✅** (reconstrução em 6h/10h de timebox, 3/3 pilotos, DEF-N4: FICA; validação da torre = DI-23) · **RETROFIT DI-09 ✅ COMPLETO
  (MATLAB 11/11 + BoTorch)** — regressão total verde (14 runs ×MMF1 + F0×4 + 26 gates + suíte) ·
  **DI-21 ✅**: as 21 decisões da auditoria DI-20 RATIFICADAS pelo autor e APLICADAS (código+teste+
  doc; ver REGISTRO PARTE A10) — inclui a ⑦ do e103 GERADA, o backfill do c262/ZDT1, os validadores
  promovidos a `scripts/{naoperturbacao,auditar}.py`, e os bundles REGENERADOS pós-DI-18.
- **A ONDA DI-09 (instrumentação do surrogate) — o grande bloco desta semana:** o autor decidiu que
  TODO run persiste, além das 7 camadas, a **SONDA canônica** (2000 pontos Sobol fixos previstos por
  cada modelo a cada k=2 gerações — a régua ÚNICA que compara a assertividade de todos os 16
  algoritmos) + `fe_treino_max` (in/out-of-sample) + timing por geração + `sigma_dict` + o "mínimo
  comum DI-10" no jsonl. Isso exigiu **retrofitar os configs já implementados**, em duas frentes
  paralelas:
  - **Retrofit R1 (MATLAB): ✅ 11/11 COMPLETO (2026-07-21)** — decisões DI-19.x aplicadas
    (ver REGISTRO PARTE A8; pendências residuais R-1/D-11/T-8 no handoff DI09-retrofit-R1-cont).
  - **Retrofit R2 (BoTorch):** c262 e c154, com a sonda cobrindo **3 de 5 runs** (c262/ZDT1 ficou sem).
  - **Auditoria da torre (DI-20, workflow de 90 agentes):** invariante de não-perturbação **PROVADO**
    (53/53 ① bit-idênticas ao baseline); o GP **aprende e a sonda mede** (c262/DTLZ2 WAPE −41,5%,
    calibração 0,978; o achado-de-ouro c154/MMF1 it30-37: pior E mais confiante — só a sonda vê).
    **Notas de comportamento 0–10** (semente 0, ver REGISTRO A9): c262 9,5 · b1 8,5 · smsemoa 8,0 ·
    e74/nsga3/c154 7,5 · c238/nsga2 7,0 · b3/b4 6,5 · e7 6,0 · c217 4,5 · moead/c141/e103 4,0.
    **21 decisões em aberto** consolidadas em `handoff/DI20-AUDITORIA-RETROFIT_DECISOES.md`.
- **Antes disso, a auditoria de PROSA (DI-18):** 38 achados aplicados na SPEC. **Bundles já
  REGENERADOS (3× desde então, 44 arquivos)** — SPEC v5.2.1 e bundles em sincronia; próxima regen
  só quando NENHUMA sessão de implementação estiver aberta (regra RI-12).
- **Próximo (5 passos, 2026-07-23 pós-marco 21/21):** (1) **autor ratifica as DI-30** (B2 modelo_hp
  NULL · B3 linha ⑥ "b5" · D97-b5m/DTLZ2 aceitar+caveat — recomendações no REGISTRO A17);
  (2) torre executa o **doc-sync SPEC→bundles** (DESTRAVADO — nenhuma sessão aberta): header
  "N interno = 100" stale do cartão do piso, receita L.17/pyDOE, PYTHONHASHSEED, clarificação
  §6.1 pós-B3, regen + diff auditado; (3) **lote D97 do autor** (dossiê: 21 notas + flags
  b5m/DTLZ2 e c311 D1-D3); (4) hardening pré-M7 (D-17 RNG · abort e2e · dossiê itens 3/4/5 ·
  pisos no roster do experiments.m · enable_bucket); (5) **M7 (PORTÃO) pilotos de timing/memória**
  → dimensionamento VM/bucket → M8 (baterias).
- **Como uma instância nova assume:** leia este PROGRESSO + `CONTRATO_DE_DADOS.md` (obrigatório) +
  `REGISTRO_DECISOES_IMPLEMENTACAO.md` + `ORQUESTRACAO_MESTRE.md`. Regra de ouro: verifique cada sessão
  rodando código + lendo; nunca julgue fidelidade (D97); pára-e-pergunte em ambiguidade (D81).
