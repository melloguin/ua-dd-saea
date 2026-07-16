# PROGRESSO — log vivo da implementação + mapa dos arquivos

> Este é o **registro vivo** do que já foi feito, com resultados, e o **mapa de para que serve cada arquivo** do repo.
> Estado-fonte da orquestração: `ORQUESTRACAO_MESTRE.md` (status board). Plano geral: `PLANO_IMPLEMENTACAO.md` (15 milestones).
> Atualizado: 2026-07-15.

---

## Parte 1 — Para que serve cada tanto de arquivo (o mapa)

O repo tem 4 "camadas" de arquivos, cada uma com um papel distinto. Entender isso evita confusão:

### 🟦 Camada 1 — A metodologia (a "constituição": O QUÊ e POR QUÊ)
- **`claude_code_context/SPEC_experimentos_v5.2.md`** — a **fonte única da verdade**. Descreve, de forma agnóstica de máquina, TODO o experimento: os 25 problemas, os 16 algoritmos, o protocolo (orçamento, DoE, sementes, export), as 100 decisões (D1–D100). É consultada por trecho, nunca lida inteira.
- **`claude_code_context/{00_fundacao..50_analise_R4}/`** — a **SPEC fatorada em bundles**. `gen_bundles.py` recorta a SPEC em pedaços cirúrgicos, um por fase/algoritmo, para cada sessão ler só o que precisa. São GERADOS — nunca editados à mão.
- **`claude_code_context/REGISTRO_DECISOES_pingpong_v5.md`** — o "porquê" rico das decisões (histórico de raciocínio).
- **`claude_code_context/gen_bundles.py`** — o gerador dos bundles a partir da SPEC.

### 🟩 Camada 2 — Os dados que o agente consome (machine-readable: os NÚMEROS)
`claude_code_context/artifacts/`:
- **`runs_matrix.csv`** — o grid completo: quais corridas existem (alg × problema × semente).
- **`envs.json`** — o mapa alg→ambiente + os pins de cada venv + o bloco `provisioning` (venvs, requirements, viabilidade Mac/VM).
- **`seeds.json`** — as sementes: alg_id→int, catálogo de usos, e o bloco `shared_init_artifacts` (fórmulas de DoE/dataset).
- **`params.json`** — parâmetros por config.
- **`anchors.json`** — as "coordenadas de GPS" dos patches de fidelidade (arquivo:linha exatos).
- **`decisions.json`** — índice das decisões D53–D100.
- **`characteristics.csv`** — a matriz problema×característica (para a análise; será re-derivada pelo autor, D98).
- **`repos.lock`** — o pin por content-hash de cada repo de algoritmo.

### 🟨 Camada 3 — A orquestração (COMO tocamos o trabalho)
- **`cards/INDEX.md`** — os 25 cartões-sessão (1 sessão = 1 cartão), com dependências e status.
- **`cards/_TEMPLATE.md`** — o molde de cartão.
- **`scripts/preflight.py`** — o pré-voo (valida âncoras + content-hashes antes de começar).
- **`scripts/accept.py`** — o gate objetivo por cartão (só encanamento; nunca fidelidade — D97).
- **`handoff/{CARTAO}.md`** + `handoff/{CARTAO}_RELATORIO-EXECUCAO.md` — o que cada sessão fez (continuidade + narrativa).
- **`HANDOFF_MESTRE.md`** — a orientação geral para uma instância nova (mapa + estado + armadilhas).
- **`ORQUESTRACAO_MESTRE.md`** — o **control tower** (status board, matriz de ambientes, armadilhas, mapa de bundles). É por onde a torre de controle guia.
- **`PLANO_IMPLEMENTACAO.md`** — o plano em 15 milestones (versão didática).
- **`PROGRESSO.md`** — este arquivo (log vivo + mapa).
- **`START_HERE.md`** — arranque curto.
- **`requirements/`** — 1 `requirements.txt` por ambiente virtual + `env_matlab.md` + `README.md` (mapa venv↔alg). Ver §Ambientes.

### 🟥 Camada 4 — O código e os dados que a bancada produz (o que RODA)
- **`src/`** — o harness: `problems.py` (os 25 problemas, fonte única), `experiment.py` (adapter A2 + registro de algoritmos), `doe.py` (gerador do DoE/dataset), `naming.py`/`atomic_io.py`/`manifest.py`/`audit_log.py` (infra de export), `experiment.m`/`hook_output.m` (lado MATLAB).
- **`experiments.py`** / `experiments.m` — os despachantes (rodam as baterias).
- **`algorithms/`** — os repos oficiais dos 16 algoritmos + PlatEMO (código de terceiros, vendorizado; NÃO se toca sem patch de fidelidade).
- **`data/doe/`** + **`data/datasets/`** — os pontos iniciais (DoE) e datasets offline, gerados pelo `doe.py`. Persistidos no repo (decisão do autor: sem bucket).

---

## Parte 2 — Log de progresso (o que foi feito, com resultados)

### ✅ M0 — Preparação & pré-voo (concluído)
- SPEC auditada (multi-agente, 85 achados) → 14 decisões (D87–D100) → SPEC v5.2.
- Infra montada (Mac MATLAB + VM Vertex + bucket) e validada pelo autor.
- **Sessão pré-voo:** resolvidas as 9 pendências de âncora; `preflight.py` verde. Verificado por 5 verificadores adversariais (o portão foi refinado, não enfraquecido; injeção de `<PIN>` falso → exit 1).

### ✅ M1 — Fase 0 (a bancada): 4 de 4 cartões — **COMPLETA (2026-07-16)**
- **✅ F0-01-harness** — despachantes + esteira idempotente + manifesto/logger (§17.5). Gate verde; 17 unittests; 0 código de algoritmo tocado. Descoberta: o **env-main** não estava provisionado (levou à criação do venv + `requirements/`).
- **✅ F0-02-doe** — `src/doe.py` (LHS-maximin próprio D87, hash do array decodificado), dataset offline (D90), `seeds.json` (D91). **Materializou 750 DoE + 755 datasets.** Bit-identidade Python↔MATLAB **fechada em-sessão** (`check_doe_matlab.m` → PASS=1505, FAIL=0) + oráculo independente reproduz os hashes. Gate verde, 27 testes.
  - **Reconciliação BBOB (2026-07-15):** o token curto `BBOB1…` (anômalo) foi renomeado para **`BBOB_F1…`** (o canônico da SPEC §4 / characteristics / runs_matrix). Os 7 BBOB foram regenerados; **valores idênticos ao baseline** (o seed usa o índice `problema_id`, não a string) → a prova MATLAB continua válida por identidade de conteúdo. Gate segue verde.
- **✅ F0-03-export** — `src/budget.py` (wrapper de FE: cache-hit=0 D89, hard-stop 31D−1 exato, solution_id dedup D57), `src/export.py` (4 camadas §17.2, float32 sem round D53, escrita atômica D58), `src/gcs.py` (dual-write lazy). Gate verde, 44 testes. **Verificado adversarialmente pela torre (6 lentes): 5 CONFIRMED + 1 PARTIAL não-corrupção** (órfão `.tmp` em kill duro — hardening p/ M8; mu>M sem guarda). Corrigiu o bug mono-output do b1.
- **✅ F0-04-metrica** — `src/metrics.py` (esqueleto pós-hoc: IGD, **IGD+ primária D70**, HV, GD, spacing + trajetória; normaliza por (ideal,nadir) da S.5, delega ao pymoo pinado). Gate verde: **âncora D92 batida — HV(BBOB_F1)=1,04333** (|Δ|=2,7e-5). 62 testes. **Verificado pela torre por leitura + probe independente** (âncora, normalização exata, IGD+ ref-vs-ref=0, monotonicidade HV, HV=0 não-NaN) — tudo correto, 0 correções.

**→ Com o F0-04, a Fase 0 (a bancada) está COMPLETA e verificada.** Todos os 4 gates verdes, 62 testes, módulos `src/` coerentes, sem conflito entre as sessões nem com a reconciliação BBOB. Abre o **M2 = c217** (o caso-modelo).

### 🟡 M2 — Caso-modelo c217 (2 cartões): R1-00 ✅ · R1-c217 (próximo)
- **✅ R1-00-harness (MATLAB, 2026-07-16)** — a infra transversal MATLAB (contrato N.0): `experiments.m` (despachante), `src/experiment.m` (adapter: ponte→`problems.py`, DoE carregado, budget, export, CP-init), `src/hook_output.m` (as 4 camadas §17.2), `src/FEBudget.m` + `src/RunBuffer.m` (wrapper de FE D89 + coletor ②③/timing). Prova por **run-STUB** (avaliador trivial pela ponte; o algoritmo real é o c217). **Verificado pela torre:** escopo **MATLAB-only** (0 `.py`/algoritmo/docs tocados — o renome `experiment_run→experiment` foi na função do `.m`, exigência do MATLAB); **CP-init cross-language MATCH** (o `doe_hash` do manifesto MATLAB = sidecar Python `89b8ce4e…`, confirmado por mim); **schema §17.2 IDÊNTICO entre stacks** (real/pop/surrogate/timing, x/f em float32); FE=31D−1 exato nos 4 problemas (MMF1/ZDT1/BBOB_F1/DTLZ2); regressões F0-01..04 verdes. **Fix da torre:** o `check_fe` do `accept.py` confiava no `--dim` (default 30 = footgun) → agora deriva o D das colunas `x0..x{D-1}` da própria camada ① (gate confiável p/ a bateria M8). 2 decisões deferidas ao c217 (evalFcn de lote com hard-stop no meio D61; `real_solution_id` nullable na ③). *(Ponto p/ veto: `experiment.py` e `experiment.m` coexistem — nomes iguais, runtimes diferentes.)*
- **⬜ R1-c217 (o CASO-MODELO 🔑, próximo)** — o 1º algoritmo REAL (PC-SAEA) rodando ponta-a-ponta na bancada + a **1ª validação de fidelidade do autor** (compara com o artigo). Prova o pipeline inteiro; depois dele, os outros algoritmos MATLAB são multiplicação.

### Decisões do autor consolidadas nesta fase
- Seed do DoE = `SeedSequence((semente, problema_id))`, sem alg_id (ratificado — consistente com D88).
- **pandas fixado em 2.x** (evitado o 3.0) no env-main.
- **DoE/datasets persistidos no repo** (sem bucket).
- **BBOB canônico = `BBOB_F*`** (reconciliado).

---

## Ambientes virtuais (resumo — detalhe em `requirements/README.md`)
- **4 venvs Python** que rodam algoritmos: `env_main` (c262/c154/c122/c149) · `env_e81_qpots` (e81) · `env_b5` (b5/moead_media) · `env_c311` (c311). **+ `env_bridge`** (ponte MATLAB) **+ `env_c149_fallback`** (condicional).
- **MATLAB = 0 venv** (1 instalação R2025a; isolamento por árvore PlatEMO + ponte).
- **Mac:** só `env_main` provisionado (é o viável+necessário já). `env_b5`/`env_c311` são **VM-Linux** (pins x86/antigos sem wheel arm64). Venvs em `/Users/gmello/Documents/python_venvs/`.

## Próximo passo
**R1-c217** — o caso-modelo (2º cartão do M2). O R1-00 (infra MATLAB) ✅ está pronto e verificado; agora o c217 pluga o 1º algoritmo REAL (PC-SAEA) e prova o pipeline de ponta a ponta, com a 1ª validação de fidelidade do autor. Em paralelo, **R2-00-harness** (BoTorch, VM) pode arrancar.
