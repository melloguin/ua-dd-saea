# Fundação 2/5 — Arquitetura A2, harness, ambientes, paralelismo e infra

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

## 2. Arquitetura — [DECIDIDO: A2, objetivo Python única]

### 2.1 O problema
Duas "cozinhas" executam os algoritmos: **PlatEMO** (MATLAB) e **Python** (BoTorch / repos). Os 25 problemas estão implementados **em Python** (classes pymoo). Risco central: se um algoritmo MATLAB resolver um "DTLZ2 do MATLAB" e um algoritmo Python resolver um "DTLZ2 do Python", e não forem *idênticos* (mesma fórmula, limites, dimensão), a comparação quebra — dois corredores em pistas diferentes.

### 2.2 A decisão (A2)
Existe **uma única implementação de cada problema**: as 26 classes Python. **Nenhum algoritmo usa problema nativo do MATLAB.**
- Algoritmos **Python** (BoTorch/repos) leem as classes Python **diretamente**.
- Algoritmos **MATLAB** (PlatEMO) avaliam via **ponte MATLAB→Python**: o PlatEMO roda o loop e, a cada avaliação real, chama a objetivo Python e recebe `f(x)`. Mecanismo: **`UserProblem` do PlatEMO com um `objFcn`** — uma casca MATLAB que repassa `x` para `py.problems.evaluate_problem(...)` e devolve o vetor de objetivos. O PlatEMO **não traduz nem importa** o código Python; há um processo Python vivo ao lado, e o MATLAB é um cliente que pergunta `f(x)`.
- **Todas as métricas** são calculadas **a posteriori, em Python**, sobre os arquivos de saída, usando os fronts verdadeiros das classes. Nenhuma métrica interna de framework é usada como resultado.

### 2.3 Por que A2 (e não A1 "problemas nativos validados" nem híbrido)
Foram consideradas três vias: **A1** (usar problemas nativos do PlatEMO e validá-los ponto a ponto contra o Python, portando os que faltam), **A2** (objetivo Python única via ponte) e **híbrido**. Escolheu-se **A2** porque:
- **Conformidade por construção:** não existem "dois DTLZ2 para reconciliar"; a padronização é propriedade estrutural do desenho, não uma promessa a validar. Elimina a categoria inteira de risco "e se a implementação nativa divergir num detalhe?".
- **Resolve o BBOB:** os 7 problemas BBOB são uma construção *bbob-biobj custom* com front verdadeiro **empírico** (NSGA-II acumulado, cacheado) e **não existem no PlatEMO** (que só tem BBOB single-objective). Sob A1, o BBOB exigiria reimplementar toda a maquinaria COCO em MATLAB — laborioso e sujeito a divergência silenciosa. Sob A2, o BBOB nunca sai do Python.
- **Auditabilidade (defesa):** à pergunta "como você garante que dois algoritmos foram testados no mesmo problema?", a resposta é uma frase — "há uma única implementação de cada problema; todos a chamam" — em vez de "reimplementei e validei, confie".

### 2.4 O preço aceito (documentar)
- **Perda de redundância de verificação:** somem a métrica interna do PlatEMO e a "validação cruzada entre ambientes" (rodar o mesmo algoritmo nos dois stacks e ver as métricas baterem) — porque não há mais duas fontes de objetivo para reconciliar. Não é perda de qualidade do resultado, é perda de uma segunda opinião "de brinde".
- **Complexidade de paralelismo (§19):** cada worker do PlatEMO precisa de um processo Python vivo para a ponte. É o custo real de engenharia do A2 (não o overhead por chamada, que é irrelevante no regime caro de ~centenas de FEs).

*(Histórico do raciocínio desta decisão — a analogia da "receita/cozinha", os achados de código que a viabilizaram (`UserProblem`/`objFcn`) e a discussão da validação cruzada que "fica moot" — no Anexo G.1.)*

---
---

**Materialização no repositório `ua-dd-saea` (§harness).** A decisão A2 se concretiza no código assim: os **25 problemas** vivem em `src/problems.py` (as classes pymoo — a *única* implementação de cada um), e os **16 algoritmos** ficam nos seus **repositórios oficiais** dentro de `algorithms/` (PlatEMO em `_PlatEMO/`, BoTorch em `_BoTorch/`, os standalone cada um na sua pasta). Um despachante por stack — `experiments.py` (Python) e `experiments.m` (MATLAB) — recebe `{algoritmo, problema, semente}` e roda o experimento chamando a *main oficial* do algoritmo via os adapters `src/experiment.py`/`src/experiment.m`, que **injetam** o problema de `problems.py`. Assim a 'conformidade por construção' da A2 é literal: existe **uma** fórmula de cada problema e todo algoritmo a consome pela mesma porta. Arquitetura completa na seção do harness.

# PARTE II — O QUE RODA

---

## §16.5 · Arquitetura do harness de execução — repositório `ua-dd-saea` [NOVO — reflete o código]

Esta seção é o **mapa de execução** que o implementador (Claude Code) consome primeiro: como um único despachante recebe `{algoritmo, problema, semente}` e roda o experimento chamando a **implementação oficial** de cada algoritmo, em paralelo, gravando o contrato de export (§17). Consolida o que estava espalhado em §5.5 (adapter de bounds/sinal), §18–§19 (ambientes e paralelismo), §21 (multi-VM) e Anexo N (contrato de integração por repo).

### Layout do repositório

Todo o experimento vive no repo **`ua-dd-saea`**. **Princípio central: cada um dos 16 algoritmos permanece no seu repositório oficial**, dentro de `algorithms/`; nós **não reimplementamos** nenhum — apenas adaptamos a *main* de cada um para ser chamável pelo despachante (fidelidade, §20; Anexo N).

```
ua-dd-saea/
├── experiments.py        # despachante PYTHON (raiz): joblib paralelo sobre (alg, problema, seed)
├── experiments.m         # despachante MATLAB (raiz): parfor sobre (alg, problema, seed)
├── src/
│   ├── problems.py       # os 25 problemas (classes pymoo, cada uma com true_pareto_front)
│   ├── experiment.py     # adapter Python: chama a main de qualquer repo .py em algorithms/
│   ├── experiment.m      # adapter MATLAB: chama a main de qualquer algoritmo em algorithms/_PlatEMO (e standalone)
│   └── processing.py     # utilidades de export/consolidação (contrato §17)
├── algorithms/           # os 16 repositórios OFICIAIS (fonte executável — fidelidade)
│   ├── _PlatEMO/         # framework PlatEMO 4.15 → b1, b3, b4, c217, e7 + pisos (NSGA-II/III, MOEA/D, SMS-EMOA)
│   ├── _BoTorch/         # BoTorch oficial 0.18.1 → c262 (qNEHVI), c154 (JES)
│   ├── b5_Prob-RVEA/     # standalone (DESDEO)          ├── c238_EIM/       # standalone (MATLAB)
│   ├── c122_θ-DEA-DP/    # standalone (torch)           ├── c311_TGPR-MO/   # standalone (DESDEO, py3.8)
│   ├── c141_MMRAEA/      # PlatEMO-packaged (API 3.x)   ├── e74_CLMEA/      # PlatEMO-packaged
│   ├── c149_LBN-MOBO/    # standalone (reconstruir loop de BO — N.3)
│   ├── e103_IBEA-MS/     # standalone AUTOR (offline; API própria `IBEAMS(Global)` — NÃO é built-in do PlatEMO; worker dedicado N.3) ⚠ adicionar (S.1)
│   └── e81_qPOTS/        # standalone (env BoTorch 0.16.1 próprio)
└── data/                 # saídas: data/experiments/{exp}/{alg}/exp_{exp}_{alg}_{prob}_{seed}__*.parquet (§17.7/D55 — com o token {exp}; Python espelha no bucket mestrado_experiments) + cache BBOB (data/bbob_pf_cache/) + DoE/datasets (data/doe/, data/datasets/ — D87/D90)
```

> **Descomissionado.** O repo continha uma POC com 7 algoritmos **reimplementados em Python** (`src/*_runner.py`: NSGA2_surrogate, DR-NSGA-II, Prob-MOEA/D, K-RVEA, ParEGO, KTA2, K-RVEA-OPT) e o algoritmo próprio do autor (UA-DD-SAEA). **Nada disso entra no experimento** — o único código executado é o dos **16 repos oficiais em `algorithms/`**. O `experiment.py` é reaproveitado apenas no que faz sentido (o padrão de despacho, o logging por geração, a re-avaliação limpa da fitness), reescrito para chamar as mains oficiais.

### O despachante — dois pontos de entrada, um contrato

Há **dois despachantes na raiz**, um por stack, com a **mesma assinatura lógica** `run(algoritmo, problema_id, semente)`:

- **`experiments.py` (Python)** — os algoritmos Python/BoTorch (c262, c154, e81, c122, c149, b5, c311). Paraleliza com **`joblib.Parallel`** (backend `loky`), **uma task por `(algoritmo, problema, semente)`**, um processo por núcleo. É o padrão que a POC já validava (barra de progresso `tqdm`, `--modo-rapido` a 10% do orçamento para *smoke test*).
- **`experiments.m` (MATLAB)** — o stack MATLAB completo: **built-ins do PlatEMO** (b1, b3, b4, c217, e7), **PlatEMO-packaged do autor** (c141 porte 3.x→4.15, e74), **standalone embrulhado** (c238 → classdef N.5) e **standalone do autor** (e103 — API própria, wrapper L.15, worker dedicado) + os pisos. Paraleliza com **`parfor`** sobre o mesmo grid (uma VM grande × vCPUs — §21).

Cada despachante recebe subconjuntos de `{algoritmos} × {problemas} × {sementes}` por linha de comando (ex.: `python experiments.py --algorithms c262 c154 --problems MMF1 ZDT1 --seeds 0 1 42 --n-jobs 10`), de modo que **qualquer fatia do grid** pode ser rodada em qualquer máquina.

### O adapter — chamar a main oficial de cada repo

`src/experiment.py` (Python) e `src/experiment.m` (MATLAB) são os **adapters** que traduzem `run(alg, problema_id, semente)` numa chamada à *main* oficial do repo correspondente em `algorithms/`. Por algoritmo, o adapter:

1. **Instancia o problema** de `src/problems.py` pelo `problema_id` (a fonte única — nenhum algoritmo usa o problema do seu próprio repo; A2/§2).
2. **Aplica o contrato de adapter (§5.5):** apresenta o problema na parametrização que o repo oficial espera — **des-normaliza `[0,1]↔nativo`** para os BoTorch, mantém bounds nativos para PlatEMO/EA, e devolve `−f` aos motores que maximizam (BoTorch, e81); a **métrica sai sempre do `f` verdadeiro de minimização** (Checks B/C).
3. **Semeia** conforme o stack: no Python, `np.random.Generator` próprio para o DoE + salvar/restaurar o RNG global em volta de `pymoo.minimize`; no MATLAB, `rng(seed,'twister')` **depois** de construir o `Problem` e antes de `Algorithm.Solve` (Anexo N.4). As sementes internas hard-coded do **e81/c149** recebem o **offset `+1000·semente`** (D22, §5.3).
4. **Injeta o orçamento** `maxFE = 31D−1` e o DoE `11D−1` LHS compartilhado (§5), com **hard-stop exato** no teto (D21).
5. **Chama a main oficial** adaptada (ponte PlatEMO via `Algorithm.Solve` bypassando `platemo()`; API BoTorch; módulo standalone) e **coleta a trajetória** (população real por geração + a camada surrogate μ/σ), gravando o **export §17** nos destinos da **§17.7** (Python: local + bucket GCS; MATLAB: só local).
6. **Envolve tudo em `try/except`** com 1 retry (D23) → `status ∈ {ok, retried_ok, failed}` no manifesto; um soluço numérico nunca derruba o grid.

Os **detalhes de integração por repositório** (o que quebra sob paralelismo, o embrulho exato de cada main, os 3 isolamentos duros — e103 em worker MATLAB dedicado, b5/c311 em processos separados, e81 em env próprio) estão no **Anexo N** (o contrato que o implementador segue algoritmo a algoritmo).

### Esteira, idempotência e execução multi-máquina

- **Idempotente e resumível:** manifesto `run_id → status`; cada task grava seu próprio Parquet e o despachante **pula células já concluídas** (a POC já fazia isso via cache por task + `skip_existing`). Com ~16 mil runs, quebras são certas — nunca se re-roda célula pronta.
- **Três estágios** (do `experiments.py`): (1) pré-cache do que é compartilhável por `(problema, semente)`; (2) execução paralela do grid; (3) consolidação dos Parquet por task no export final (§17).
- **Multi-fonte (§21) e persistência (§17.7):** o grid é embaraçosamente paralelo → espalha-se sem coordenação. **Plano atual:** os experimentos **Python** rodam em **VMs GCP Vertex AI** (`experiments.py`) e gravam em **dois destinos — local + bucket GCS `mestrado_experiments`**; os experimentos **MATLAB** rodam no **Mac M1 Pro** (`experiments.m`) e gravam **só local**. Cada nó pega uma fatia do grid; ao fim, os outputs (do bucket e do Mac) convergem num só lugar antes da métrica. Escalar o MATLAB para nuvem (Azure/AWS) fica como **scale-out opcional** se o Mac não bastar (§21) — aí o teto real pode ser o **nº de ativações da licença** (§21.3).

---

## 18. Ambiente de execução — [ATUALIZADO v2.1]
- **MATLAB:** licença acadêmica completa, válida até 31/Jan/2027 (cobre o cronograma).
- **Parallel Computing Toolbox ✓** — habilita `parfor` (base do paralelismo, §19).
- **Deep Learning Toolbox ✓** — requisito de **b4** (trainNetwork), **c217** (newpnn/ind2vec/vec2ind), **e74** (newrbe/newpnn/sim) e **e7** (assert `nnet` + mapminmax). Confirmado → todos destravados.
- **Statistics and Machine Learning Toolbox ✓ [censo v2.1 — FATO D2]** — requisito de **b1** (normcdf/normpdf), **e7** (kmeans/pdist2 — **dependência NÃO declarada no repo**), **e103** (kmeans/pdist), **EIM** (lhsdesign/normcdf). c141 não usa toolbox nenhuma (base pura).
- **Optimization Toolbox — necessário para o c238** (fmincon no `GP_Train` do repo do autor; confirmado na análise de código).
- **PlatEMO por linha de comando**, nunca GUI. ⚠ **[v2.1] Bypass do `platemo()` é OBRIGATÓRIO:** `platemo.m:79` executa `rng('shuffle')` e destruiria as sementes → o harness chama `rng(seed,'twister')` e depois `Algorithm.Solve(Problem)` **diretamente**. Uma (alg, prob, semente) por processo (DEF-A12). ✔ **e7** [corrigido v2.7 — N.2]: a cópia no device é o **built-in PlatEMO 4.15 (API moderna)**, integração idêntica a c217 — **o antigo dilema "portar 3.x vs env isolado" está resolvido** (só valeria para o repo GitHub `xw00616`, ausente aqui); checar fidelidade vs o paper. **c141** é pasta de algoritmo em API 3.x → porte de 3 linhas (§3.5). **e103** é standalone (wrapper próprio, E.9). **c238** standalone (E.5).
- **[v2.2] Mecânica de integração do PlatEMO 4.15 (2ª passada — detalhes no Anexo L.0):** (i) construtores aceitam SÓ `{'parameter','save','run','metName','outputFcn'}`; `parameter` é **cell POSICIONAL** casando com o ParameterSet do algoritmo (`[]` mantém default); (ii) **hook `outputFcn(Algorithm,Problem)` é chamado a CADA geração** (inclusive a final) — instrumentação por geração sem editar algoritmos; seu runtime não conta no metric.runtime; (iii) **fixar `'save'` e `'outputFcn'` SEMPRE**: o default `save=−10` roda `clc` por geração e **abre FIGURA no fim** (mata headless); `Algorithm.result` = snapshots {FE, Population} equiespaçados em FE (num=\|save\|, com sobrescrita por slot); (iv) `UserProblem` aceita `{N, M, D, maxFE, maxRuntime, encoding, lower, upper, initFcn, evalFcn, decFcn, objFcn, conFcn, data, once}`; **`'once',true` = 1 chamada de ponte por LOTE** (false = por indivíduo — decidir e fixar); o dec RETORNADO pelo evalFcn é o que vai ao SOLUTION (o clamp do wrapper é autoritativo); (v) o **probe do construtor é INEVITÁVEL** (passar M não evita; 1 avaliação real fora do orçamento + 1 consumo de RNG `unifrnd` ANTES do run → **semear antes de construir o Problem**, convenção única); `optimum` fica lixo p/ UserProblem → métricas SEMPRE externas; (vi) término normal = `MException('PlatEMO:Termination')` lançada pelo próprio NotTerminated e engolida por Solve — o hard-stop do wrapper usa o mesmo identificador (validado); erro real da ponte é RETHROWN → try/catch em volta de `Algorithm.Solve` no runner; (vii) `SOLUTION.add` é um campo público por indivíduo utilizável p/ anexar μ/σ; (viii) `maxRuntime=inf` sempre (senão reescala maxFE); (ix) nuance Balde C: o SBX do PlatEMO randomiza o SINAL de β (≠ SBX canônico/pymoo) — registrar ao comparar operadores entre stacks.
- **Python — ambientes isolados (v3.0.1: ~6 + ponte):**
  1. **BoTorch 0.18.1 moderno** (Python ≥3.11, torch ≥2.4) — **c262 qNEHVI + c154 JES** (fonte atualizada — E.1) + piso Sobol-batch + (b1-qParEGO se aprovado). Nota: kernel C++ JIT do 0.18 → pré-aquecer no piloto (B8.5).
  2. **e81 qPOTS** — **env BoTorch 0.16.1 PRÓPRIO por padrão** [alinhado v3.0.1 ao N.4: o pin `botorch==0.16.1` + o isolamento do grid tornam o env dedicado a rota segura; a alternativa "testar sobre o env (1)" fica só como experimento opcional de piloto]; py3.10/3.11; forçar float64 no adapter (N.2).
  3. **c122 θ-DEA-DP** — torch 2.x CPU + DEAP 1.4 + numpy; ⟦v2.7 — corrigido (N.2): `pymop`/`optproblems`/`autograd` são imports DUROS⟧ (`problems/factory.py`, `problems/wfg.py`) → satisfazer os imports **ou** cortar `problems/wfg.py` do caminho (nossos problemas entram pelo adapter, mas o import precisa resolver); CPU-only + `use_deterministic_algorithms(True)`; ⚠ rodar com `cwd=examples/` E `PYTHONPATH=raiz` (senão ModuleNotFound/FileNotFound — N.2).
  4. **c149 LBN-MOBO** — torch + pymoo 0.6.x (notebook → script; E.3).
  6. **DESDEO-b5** (py3.8/3.9) — sklearn 0.23.2/numpy 1.20 do lock (GPR alpha=0 diverge em versões novas); sementes: `np.random.seed` + `random.seed` (o SBX usa o stdlib `random`!).
  7. **DESDEO-c311** (⟦corrigido v2.7⟧ **py3.8 efetivo** — o lock não traz pygmo cp39) — GPy 1.9.9 + numpy 1.20 + sklearn 1.1.2 + pymoo 0.4.2.2 (**nunca importado**); ⚠ **pygmo NÃO está no caminho `framework/`** (N.3) → o swap por NDS-pymoo é **desnecessário** no caminho canônico que usamos (só seria p/ drivers de análise SS).
  - **Ponte/harness:** env com **pymoo moderno + problems.py** (o `pyenv` do MATLAB aponta para ele, `ExecutionMode='InProcess'`, 1×/processo — DEF-D3). ⚠ **Os envs DESDEO usam pymoo antigo → o dataset offline é gerado FORA deles** (o harness gera X,F com o env da ponte e injeta arrays; o offline nunca reavalia — DEF-D1).

---

## 19. Paralelismo e engenharia — [DECIDIDO abordagem; números v2.0]
- **Grid embaraçosamente paralelo.** Dimensões: **principal online [v3.0.8/D25]** = **17 configs** (13 SA-MOEA + **4 pisos**: NSGA-II, NSGA-III, MOEA/D, SMS-EMOA) × 25 problemas × 30 sementes = **12.750 runs**; **offline** = 4 configs × 25 × 30 = **3.000 runs**; **sub-estudo batch** = 5–6 configs × 5 problemas × 30 sementes = **750–900 runs** (caros por run); **sweep offline** = medium: 4 × 5 × 30 = 600; big: 2 × 5 × 30 = 300 (small reaproveita o principal offline).
- **MATLAB (PlatEMO):** `parfor` sobre o grid. **Ponto de atenção real (A2):** cada worker precisa de um processo Python vivo para a ponte. Estratégias: (a) cada worker sobe seu próprio interpretador Python isolado (simples, mais memória) — **começar por (a)**; (b) pool de serviços Python (mais eficiente, mais complexo).
- **Python:** multiprocessing/joblib sobre o grid, nos ambientes isolados (§18).
- **Esteira idempotente e resumível:** manifesto `run_id → status`; pula células concluídas; checkpoint. Com dezenas de milhares de runs, quebras são certas — **nunca re-rodar célula pronta**.
- **[D23] Política de erro-duro + contabilidade (DEF-A8):** cada run em try/catch; **1 retry** (perturbação/re-jitter/re-seed local); se falhar de novo → `status=failed` no manifesto/Parquet + stack trace, e **segue** (um soluço numérico não derruba a configuração). **Nunca silencioso.** Status (`ok`/`retried_ok`/`failed`) registrado em 3 lugares — manifesto/Parquet (§17.2), logs `.jsonl` (§17.5) e **placar de console corrido** (contagem acumulada de sucessos × falhas). A **taxa de falha por (algoritmo, característica de problema) é dado reportável de robustez** na dissertação. Hazards já mapeados por algoritmo nos Anexos L/N (Cholesky desprotegido do c238/e81, NaN por objetivo constante, dacefit com sites duplicados, etc.) — cada guarda aciona um evento no log.
- **Piloto de timing ANTES da bateria completa:** medir runtime por (alg, prob) para dimensionar a cauda cara e orçar compute. **Serve só para timing/validação, nunca para selecionar algoritmo** (seleção é analítica). Também calibra a população dos pisos (§3.2) e o intervalo de snapshot (§17.4). Casos de pior-caso a medir: GP no ZDT1 D=30 (929 pts), c149 (retreino BNN), c122 (pares por retreino em D=30).
- **Custo cúbico do GP (nota):** treino do GP/Kriging é ~O(n³). Os runs de **alto D** (ZDT1/3, WFG, DTLZ7 → GP chega a ~600–930 pontos) e os tiers grandes são os mais lentos. **Se algum estourar o tempo, a mitigação é teto no nº de pontos de treino do GP** (janela dos mais recentes/informativos acima de ~500) — **não reduzir o orçamento**; vários algoritmos já fazem isso internamente.
- **Runtime entre stacks:** confundido por linguagem (MATLAB vs Python) → comparar runtime **dentro** de cada stack, ou reportar com a ressalva. Nunca "X é mais rápido que Y" cruzando stacks.

---

## 21. Infraestrutura de execução — [DECIDIDO: multi-fonte]

> **[v4.0.3] Plano atual de execução:** **Python** nas **VMs GCP Vertex AI** (grava local + bucket GCS `mestrado_experiments`, §17.7); **MATLAB** no **Mac M1 Pro** (grava só local). O conteúdo abaixo (MATLAB em nuvem Azure/AWS) é o **caminho de scale-out** caso o Mac não dê conta do lado MATLAB — permanece válido como referência.

O grid é **embaraçosamente paralelo** e a esteira é **resumível** (manifesto `run_id → status`, §19). Isso habilita uma estratégia **multi-fonte**: espalhar os runs por **quantas VMs quanto possível, em várias contas/provedores** (Azure + AWS + as VMs Python já existentes), sem coordenação especial — cada VM pega um subconjunto do grid, e o manifesto evita retrabalho/duplicação.

### 21.1 MATLAB em nuvem (via Reference Architecture)
- **Como:** MathWorks Reference Architectures (AWS via CloudFormation; Azure via ARM template) sobem uma VM com MATLAB + toolboxes prontos (inclui Deep Learning Toolbox, requisito de e7/b4/c217/e74). Alternativas mais simples: Azure/AWS Marketplace (quase 1-clique) ou Cloud Center.
- **Licença:** a licença **Individual acadêmica** já vem "configured for cloud use" (Individual e Campus-Wide são elegíveis) — confirmar o flag na conta MathWorks. **Não** é necessário MATLAB Parallel Server (isso é para *cluster de várias VMs*); o objetivo é **uma VM grande + `parfor`** sobre seus vCPUs.
- **Máquina:** **compute-optimized**, muitos vCPUs, RAM generosa (~32–64 vCPU, 128–256 GB), **sem GPU** (os algoritmos MATLAB não usam GPU). **Spot/interruptível** corta custo (os experimentos toleram interrupção pela esteira resumível).

### 21.2 Partição do trabalho (evita transferir dados pesados entre nuvens) — [ATUALIZADO v2.0]
- **VMs MATLAB** (Azure e/ou AWS): **9 configs MATLAB** — b1, b3, b4, e7, c217 (PlatEMO), c141, e74 (PlatEMO-packaged), c238 (standalone) + e103 (offline) — **+ 4 pisos online (NSGA-II, NSGA-III, MOEA/D, SMS-EMOA) + piso offline** (PlatEMO/próprio).
- **VMs Python [v3.0.1]:** **7 configs Python** — c262, c154 (BoTorch oficial), e81 (env 0.16.1 próprio), c122, c149 (standalone), b5, c311 (DESDEO, processos isolados) — **+ sub-estudo batch** (c149, c262, e81, c154, piso Sobol, opcional qParEGO). Escalam à vontade (sem trava de licença).
- **Consolidação no fim:** cada VM grava seus próprios Parquet localmente; ao término, baixar os outputs de todas para um único lugar antes de rodar a camada de métrica (§12). **Não** mover dados entre nuvens durante a execução — cada VM trabalha isolada; só o resultado final se junta.

### 21.3 Ressalvas da estratégia multi-VM [ATENÇÃO]
1. **Quota de vCPU da AWS (removível):** VMs grandes não saírem "de fábrica" numa conta nova costuma ser **limite de quota**, não indisponibilidade — pedir aumento no *Service Quotas* (às vezes aprovado em horas) antes de assumir que a AWS não serve para máquinas parrudas.
2. **Teto de ativações da licença MATLAB [risco real do paralelismo MATLAB]:** a licença **Individual** permite um número **limitado de ativações simultâneas** (tipicamente poucas máquinas por usuário, não N VMs em nuvem ao mesmo tempo). Subir muitas VMs MATLAB pode bater nesse teto e as excedentes não licenciam. **Confirmar com o admin do campus / MathWorks quantas ativações simultâneas a licença permite** — esse, e não o nº de VMs alugáveis, pode ser o **teto real** do paralelismo MATLAB. (O lado Python não tem essa trava.)
3. **Estimativa de tempo é ordem de grandeza** (o custo O(n³) do GP é o curinga): no Mac (M1 Pro, 8 CPU, 16 GB), ordem de **5–10 dias** contínuos, com 16 GB apertando nos GP de alta dimensão; numa VM de 32–64 vCPU (128–256 GB), ordem de **~1 dia**. **O piloto de timing (Anexo B) pina o número real** e dimensiona a(s) VM(s): medir 2 casos no Mac (barato = piso no MMF1; pior caso = GP no ZDT1 D=30), cronometrar, extrapolar pelo mix de problemas.

### 21.4 Citação canônica de nuvem
Referências: MathWorks Reference Architectures (github.com/mathworks-ref-arch/matlab-on-aws e /matlab-on-azure); "License Requirements for MATLAB on Cloud Platforms" (mathworks.com/help/cloudcenter).

---
---

---

### N.4 — Implicações para o grid (atualiza §19/§21.2)
- **Partição por isolamento, não só por licença:** além do split MATLAB×Python, o grid agora exige **3 isolamentos duros**: (i) **e103 em worker MATLAB dedicado** (polui path global — N.3); (ii) **b5 e c311 em processos/venvs separados** (colisão `desdeo_*` — N.1.2); (iii) **e81 em env BoTorch 0.16.1 próprio** (≠ clone c262/c154; e o clone c262 é fork — usar oficial). Confirma e endurece a matriz de ambientes (§18).
- **Receita `parfor` MATLAB (por worker):** `addpath(genpath(PLATEMO))` → construir `UserProblem` → `rng(seed,'twister')` → construir `Algorithm('save',-K,'outputFcn',@(~,~)[])` → `try Algorithm.Solve(Problem); catch e; log; end` → ler `Algorithm.result`. Nunca `save>0`; nunca `maxRuntime<inf`; e103 fora do pool comum.
- **Receita fan-out Python (por processo):** `torch.set_num_threads(1)`; float64; `np.random.Generator` próprio p/ DoE; salvar/restaurar RNG global em volta de `pymoo.minimize`; diretórios de export por `(alg,problema,semente)` (namespacing — os repos dos autores não fazem); c149/c311-SS: usar só os módulos de modelo/aquisição, não os drivers de cluster.
- **Determinismo cross-VM:** preferir kernels Python puros/CPU determinísticos (BoTorch oficial, sem `-march=native`); registrar no manifesto a versão exata de cada lib e o hash do repo (o fork c262 e o `__version__=="Unknown"` tornam isto obrigatório).

---

### S.6 — Ambientes machine-readable (a matriz §18, verificada nos arquivos dos repos)

**env-main** (Vertex + Mac; py 3.11) — harness + c262 + c154 + c122 + c149*:
`numpy>=2,<3 · pandas · pyarrow (zstd) · joblib · tqdm · scipy(versão REGISTRADA no manifesto — fast-path L-BFGS-B) · pymoo==0.6.2(harness) · botorch==0.18.1 · gpytorch(compatível) · torch(estável mais recente) · google-cloud-storage · scikit-learn(harness) · deap (c122)` — **[v4.3/S.8#2]** com o driver próprio do c122 (bypass do `problems/factory`), `pymop`/`optproblems`/`autograd`/`matplotlib` **saem do env** — *c149: tentar no env-main (pins do Colab: pymoo 0.6.0.1/numpy 1.22.4/py3.10 conflitam com numpy 2.x); se o piloto divergir do esperado, criar `env-c149` com os pins do Colab e registrar.*
**env-e81** (isolamento duro; py 3.10/3.11) — pins **verificados** em `e81_qPOTS/requirements.txt`: `botorch==0.16.1 · torch==2.12.0 (existe) · gpytorch==1.14.2 · numpy==2.2.6 · pymoo==0.6.1.6`.
**env-b5** (venv próprio; py conforme wheels) — `scikit-learn==0.21.3 (S.2#12 — se sem wheel p/ o py escolhido, usar a mais próxima COM validação de equivalência do GPR no piloto, registrada) · desdeo-problem==0.14.0 · desdeo-tools==0.2.6 · desdeo-emo==<PIN A CRAVAR NO GATE R3.2> · statsmodels · matplotlib · pyDOE · pandas · numpy(compatível com sklearn antigo)` — overlay root-first no sys.path.
**env-c311** (venv próprio; **py>=3.8,<3.10**) — `GPy~=1.9.9 · graphviz · scikit-learn(tree) · desdeo overlay root-first · pandas · numpy` — **sem** matlab.engine (não importar `evaluate_population`).
**MATLAB (Mac) — VERIFICADO em 2026-07-14: R2025a Update 1 (25.1.0).** `parquetwrite` do R2025a aceita `{snappy, gzip, brotli, uncompressed}` — **SEM zstd** → **decisão registrada: MATLAB grava `'brotli'`**; a consolidação Python (§17.4) re-encoda o export final para zstd (o codec por-nó é livre — §17.7). Toolboxes — **TODAS ✓ (re-verificado 2026-07-14 após instalação)**: **Deep Learning ✓** (b4 trainNetwork; c217/e74 newpnn/newrbe/sim/ind2vec/vec2ind) · **Statistics & ML ✓** · **Optimization ✓** (fmincon — c238) · **Parallel Computing ✓**. Check gravado em `data/matlab_check.txt`. Assert no arranque do harness: `assert(~isempty(ver('nnet')) && ~isempty(ver('stats')) && ~isempty(ver('optim')) && ~isempty(ver('parallel')))`.
