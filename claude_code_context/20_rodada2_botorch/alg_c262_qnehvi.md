# c262 qNEHVI (BoTorch 0.18.1)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Específicas:** Matérn 5/2 ARD (🔵 ARTIGO, D30); `train_Yvar=1e-6` (B8.6a); refit from scratch/iteração (D44); ref da AQUISIÇÃO = nadir×1,1 (interno — a MÉTRICA usa o ref normalizado D69); **bucket-only (D54)**.

---

- [ ] **c262 qNEHVI** *(I.10, L.10)* — receita L.10 na íntegra: `SingleTaskGP` por objetivo com **`train_Yvar=1e-6`** (B8.6a) + **`covar_module=get_matern_kernel_with_gamma_prior(d)`** (🔵 ARTIGO — Matérn 5/2) + `Standardize`; `qLogNEHVI(sampler=SobolQMCNormalSampler(128, seed=h1), prune_baseline=True, alpha=0.0, cache_pending=True, max_iep=0, incremental_nehvi=True, cache_root=None, tau_relu=1e-6, tau_max=1e-3, fat=True)`; `optimize_acqf(num_restarts=10, raw_samples=512, sequential=(q>1), options={seed:h2, maxiter:2000, init_batch_limit:32})`. **Refit from scratch por iteração** (D44); ref da aquisição = nadir×1.1 — **fonte do (ideal, nadir) = tabela S.5 CONGELADA** (`metrics.reference_bounds`), em **escala BRUTA** (Anexo J: c262 = escala bruta), fixo por problema; é **informação de ORÁCULO** (espelha a Tab. 2 do paper, que fixa o ref de um pool noiseless por problema) → **declarar como vantagem informacional (D73)** e registrar no Anexo J. Contraste deliberado com o c149 (**D96**: nadir OBSERVADO por iteração). Logado no header do `.jsonl` e no manifesto (`acqf_ref_f`) ⟦v5.2.1⟧; μ/σ dos candidatos via `posterior` (Standardize des-transforma). Retry do optimize_acqf desloca o RNG — **registrar**.

---

| c262 | Biblioteca | Compartilhado (c262,c154) | BoTorch OFICIAL 0.18.1 | código oficial (N.2/DEF-L2) | Backend (versão oficial, não o fork _BoTorch — reprodutível entre VMs) |
| c262 | Aquisição | Específico | qLogNEHVI | código oficial / paper | qNEHVI na formulação log (estabilidade numérica do gradiente da HV esperada) |
| c262 | Amostras MC | Específico | 128 (qMC, sampler c/ seed) | paper ✓ | Estima a HV esperada; seed explícito → estimativa reprodutível |
| c262 | prune_baseline | Específico | True | paper ✓ | Remove baselines dominados do NEHVI (reduz custo) |
| c262 | cache_root | Específico | True | código oficial | Cacheia a raiz de Cholesky entre avaliações da aquisição |
| c262 | tau_max / eta | Específico | 1e-3 / 1e-3 | código oficial | Temperaturas do soft-max da partição de HV / do soft-indicator (menor → mais fiel) |
| c262 | fat | Específico | True | código oficial | Aproximação fat-tailed → gradiente não nulo longe da fronteira |
| c262 | alpha | Específico | 0 (M≤4) | código oficial | 0 = partição **exata** da região dominada (viável p/ M≤4) |
| c262 | Estratégia q>1 | Específico | Sequential greedy | paper ✓ | Monta o lote ponto a ponto (condiciona nos anteriores) |
| c262 | num_restarts / raw_samples | Específico | 10 / 512 | código oficial | Reinícios do L-BFGS-B e amostras da heurística de init da aquisição |
| c262 | Transform de saída | Específico | Standardize(Y) | código oficial | Padroniza Y (estabiliza a estimação de hiperparâmetros) |
| c262 | Kernel | Compartilhado (c262,e81) | Matérn 5/2 ARD | D30 (ARTIGO) | Substitui o RBF ARD default; 5/2 (suavidade finita) + ARD (escala/eixo) — kernel é o coração da incerteza |
| c262 | Ruído (train_Yvar) | Específico | 1e-6 (noiseless) | D40 | Fixa variância de observação ~0 (benchmark determinístico). Efeito: qNEHVI opera como qEHVI |
| c262 | Refit do GP | Específico | do zero a cada iteração (MAP) | D44 | Re-estima hiperparâmetros por MAP a cada iteração (sem warm-start) |
| c262 | Init (DoE) | Global-override | 11D−1 LHS (≠ 2(d+1) Sobol) | protocolo uniforme (Anexo J) | Sobrescreve o Sobol 2(d+1) do paper |
| c262 | Ref-point | Específico | nadir − 0,1·(ideal−nadir) | paper | Recuado 10% além do nadir → recompensa cobertura das bordas |
| c262 | Sinal / domínio | Compartilhado (BO) | Maximização (−f), [0,1]^D | §5.5 | Adapter devolve −f e trabalha no cubo unitário |
> **Notas.** D40: com train_Yvar≈1e−6 a maquinaria "noisy" fica dormente → opera como qEHVI (achado justo). D44: refit do zero (re-MAP) por iteração (custo desprezível no n pequeno). Kernel default do código é RBF ARD; forçamos Matérn 5/2 ARD (D30).
| c262 qNEHVI | ⟦v2.7 — corrigido, supera "pin na tag": o clone `_BoTorch` é um **FORK** (`__version__=="Unknown"`) ⟦v5.2.1 — CORRIGIDO, achado S.3#9 verificado por byte-identidade: o `csrc/logei_fused.cpp` **TAMBÉM ESTÁ no wheel OFICIAL do PyPI** — a premissa "ausente do PyPI" era falsa. A política vigente (DI-05) é **desligar o kernel fusionado explicitamente** em todo runner BoTorch (DEF-L2 ⇒ caminho Python puro, determinístico Mac×Linux); o motivo de usar o oficial passa a ser a rastreabilidade do pin, não a ausência do kernel⟧ → **usar o BoTorch OFICIAL 0.18.1** (kernel Python puro, determinístico entre VMs; N.2/DEF-L2); o fork fica só como referência⟧ **qLogNEHVI**: MC=128 qMC (⟦v2.2⟧ default MOO=128, single-obj=512; sampler nasce no `__init__` via `_set_cell_bounds` — passar explícito com seed); `prune_baseline=True`; ⟦v2.2⟧ `cache_root=None→True` (resolvido p/ SingleTaskGP+Standardize), **`tau_max=1e-3`** (≠ global 1e-2), `fat=True`, `eta=1e-3`, alpha=0 exato (M≤4); sequential greedy p/ q>1; restarts/raw 10/512; ⟦v2.2⟧ **Standardize(Y) já é DEFAULT** do SingleTaskGP; kernel default = RBF ARD **sem ScaleKernel** (priors dim-scaled LogNormal) → **forçar Matérn 5/2 ARD** (2 rotas: Gamma-legada fiel ao paper vs dim-scaled); noiseless: `train_Yvar=full_like(Y,1e-6)` é o caminho oficial (Standardize divide por std²) | MC=128 ✓ paper; pruning ✓; sequential greedy ✓; Matérn 5/2 ARD = paper; restarts/raw n.r.; **DEF-B8.6 [FECHADA — D40, rota (a): `train_Yvar=1e-6`, ≡ protocolo do paper; NEHVI→EHVI, posterior colapsa nos observados]** ⟦rota (b) REJEITADA: inferir (default: prior LogNormal(−4,1), piso 1e-4)⟧; ref do paper: nadir−0,1·(ideal−nadir); init 2(d+1) Sobol; noiseless sancionado (H.7); ⟦v2.2⟧ **kernel C++ fusionado** (`csrc/logei_fused.cpp`): warm-up ~7 s/máquina, `-march=native`, ativo em CPU+fat+q≤32, sem flag pública (OFF = `_load_attempted=True`) [PP L]; M=3: partição em **loop CPU por amostra MC** = custo dominante |

---

### I.10 · c262 qNEHVI (BoTorch 0.18.1)
**Fluxo real:** SingleTaskGP por objetivo (forçar Matérn 5/2 ARD) + qLogNEHVI (CBD: partição não-dominada cacheada 1×/iteração; MC 128 qMC; prune_baseline) + optimize_acqf multi-start L-BFGS-B → 1 FE (q=1) ou lote greedy sequencial (batch). **Integração:** adapter BoTorch padrão (§5.5); refit from scratch por iteração (B8.3 ►); ref da aquisição nadir×1.1. **σ exportável:** posterior por objetivo nos candidatos dos restarts + escolhido. **Ruído (DEF-B8.6): FECHADA em D40** — rota (a) `train_Yvar=1e-6` (≡ paper); NEHVI→EHVI (maquinaria *noisy* dormente = achado justo, §16). **Efeito colateral ratificado (DI-04/A4):** o piso 1e-6 do gpytorch sob `Standardize` emite ~2 `NumericalWarning`/iteração — filtrados do stderr e CONTADOS/registrados no `.jsonl`. Noiseless sancionado pelo paper (H.7).

---

### L.10 · c262 qNEHVI — receita por iteração: `torch.manual_seed(h(run,it))` ANTES de construir modelo+acqf (ancora fit-retries/prune/sampler/scramble); modelos SingleTaskGP por objetivo com `train_Yvar=1e-6` (se B8.6(a)) + `covar_module=get_matern_kernel_with_gamma_prior(d)` (rota fiel ao paper) + Standardize; `qLogNEHVI(..., sampler=SobolQMCNormalSampler(128, seed=h1), prune_baseline=True, alpha=0.0, cache_pending=True, max_iep=0, incremental_nehvi=True, cache_root=None, tau_relu=1e-6, tau_max=1e-3, fat=True)`; `optimize_acqf(..., num_restarts=10, raw_samples=512, sequential=(q>1), options={"seed":h2,"maxiter":2000,"init_batch_limit":32})`; μ/σ dos candidatos via `model.posterior(cand)` (escala original — Standardize des-transforma). Determinismo: threads=1, float64, versão scipy registrada (fast-path batched L-BFGS-B em [1.13,1.19)), política do kernel fusionado (DEF-L2), retry do optimize_acqf desloca o RNG (registrado). **RNG:** tudo no torch global + 2 seeds explícitos; scipy determinístico; numpy fora do caminho. **FE:** init injetado + q/iteração — exato.

---

### M.7 · c262 qNEHVI
- **Racional profundo (unificação ruído↔paralelismo):** o paper argumenta que **gerar q candidatos em paralelo É uma encarnação de EHVI com incerteza na fronteira** — mesmo SEM ruído: no greedy sequencial, os x_1..x_{i−1} já escolhidos ainda não foram avaliados → seus f são incertos → a PF que x_i deve melhorar é incerta. **Batch e ruído são o MESMO mecanismo.** É o *porquê conceitual* de a maquinaria "noisy"/CBD não ser desperdiçada em batch noiseless (a DEF-B8.6 tratava só do "colapsa em EHVI"; aqui está a razão mais funda) — fundamenta a inclusão do qNEHVI no nosso setting e no sub-estudo batch.
- **Diagnóstico "otimizar ruído"/clumping:** EHVI usa a PF observada (ruidosa), é enganado por pontos que *parecem* Pareto-ótimos e agrupa a fronteira; o paper contraria o consenso da simulação ("melhor ignorar ruído") mostrando que tratá-lo ajuda.
- **Garantia (App F, informa o batch):** cadeia submodular (qEHVI submodular p/ PF fixa → PF estocástica sob ruído → esperança de submodular estocástica é submodular) → **regret do greedy ≤ (1/e)α***: o greedy captura ≥63% do ótimo do lote sem resolver o problema qd-dimensional conjunto. Caveat honesto: submodularidade exige X finito, estendida ao contínuo por analogia. Justifica usar `sequential=True` para o batch (DEF-B8.4) com garantia.

---

### E.2 — qNEHVI (c262) e ambiente BoTorch moderno [ENRIQUECIDO v2.1]
Sem bloqueios (viab. 10). Adapter padrão BoTorch (§5.5). `q=1` no principal; `q` do sub-estudo no batch (sequential greedy — protocolo do paper, com base samples redesenhados por candidato).
- **qLogNEHVI** = variante numérica atual; registrar na dissertação: "qNEHVI" = qLogNEHVI 0.18.1 (fidelidade de mecanismo, não bit-a-bit — a aquisição do paper usa [·]⁺ hard; maximizadores ~equivalentes).
- **Config fiel ao paper:** MC=128 qMC (= default) explícito; `prune_baseline=True` (o paper usa pruning — fn. 4/G.2); **kernel Matérn 5/2 ARD FORÇADO** (o default moderno do SingleTaskGP mudou para RBF — sem forçar, desviamos do paper silenciosamente); `Standardize(Y)` (paper silente — registrar como escolha nossa); `num_restarts`/`raw_samples` não estão no paper → fixar 10/512 (tutorial) e registrar fonte.
- **Ruído (DEF-B8.6) — ⟦FECHADA: D40, rota (a)⟧:** o paper FIXA a variância de ruído no valor verdadeiro; no nosso noiseless adotamos **(a) `train_Yvar=1e-6`** (≡ protocolo do paper; NEHVI→EHVI, posterior colapsa nos observados). ⟦Rota (b) — inferir (default; mantém σ>0 nos observados e o mecanismo "noisy" ativo) — **REJEITADA**; a maquinaria noisy fica dormente e isso é um achado justo a reportar (§16).⟧ **Não é mais ping-pong.**
- Ref point da AQUISIÇÃO: nadir×1.1 por problema (**interno da aquisição**; a MÉTRICA da análise usa o ref **normalizado** — D69/§12); heurística do paper (nadir−0,1·(ideal−nadir)) registrada no Anexo J para o check de reprodução. **Fonte do par (ideal, nadir): tabela S.5 CONGELADA** (`metrics.reference_bounds`), escala BRUTA, fixa por problema — algebricamente `nadir+0,1·(nadir−ideal)` ≡ a heurística do paper. É **informação de ORÁCULO** ⇒ **vantagem informacional declarada (D73)**, em contraste deliberado com o nadir OBSERVADO do c149 (D96) ⟦v5.2.1⟧.

---

**Âncora de fidelidade (Anexo J):**

| c262 qNEHVI | BraninCurrin(d2), DTLZ2(d6), ZDT1(d4), VehicleSafety(d5,M3), CarSideImpact(d7,M4), ABR, AutoML + **noiseless H.7** | 2(d+1) Sobol | ~200–224 FEs (400 em H.6/H.8) | 100 | log-HV-difference (média±2SEM); SEM testes | q∈{1,8,16,32}; ruído principal 1–10%; wall GPU q=1: 6,15s (BC) / 20,81s (VS); q=32: 177,6/546,8s |
