# c154 JES (BoTorch 0.18.1)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**D75 (a receita, §6.4 é a DONA):** produção = **`random_search_optimizer`**; `nsgaii(pop=100,gen=500)` SÓ no piloto (1–2 problemas, mede o gap); pop-250 MORTA. Fallback do `RuntimeError` obrigatório. Ruído INFERIDO (não fixar `train_Yvar`). **Bucket-only (D54).**

---

- [ ] **c154 JES** *(I.11, L.11)* — modelo como o c262 **mas ruído INFERIDO** (não fixar `train_Yvar` — B9.x). **Pipeline pré-aquisição = DEF-B9.5, decidir no PILOTO desta rodada:** rota (a) default `sample_optimal_points(..., random_search_optimizer, pop_size=1024, max_tries=10)` com try/except do `RuntimeError` × rota (b) **paper-faithful** `MatheronPathModel → optimize_with_nsgaii(pop=100, gen=500) → truncagem HV-greedy` (► paper-faithful se trivial). `qLowerBoundMultiObjectiveJointEntropySearch(..., estimation_type="LB")`; `optimize_acqf` com **5D restarts / pool 1000D** (paper). Guards: shape≠P do NSGA-II; logdet inicial sem jitter (q=1 mitiga). Semear **os 3 RNGs** do caminho NSGA-II (pymoo + np + random). Logar os S fronts amostrados. Âncora (ordem, ZDT2 q=1): JES-LB < MES-LB < TSEMO < NEHVI < Sobol.

---

| c154 | Biblioteca | Compartilhado (c262,c154) | BoTorch 0.18.1 | código oficial | Backend (mesmo stack de c262) |
| c154 | Aquisição | Específico | qLowerBoundMultiObjectiveJointEntropySearch | código oficial | JES-MO: reduz a entropia conjunta do Pareto set/front; escolhe x que mais informa |
| c154 | estimation_type | Específico | "LB" (lower bound) | paper ✓ (recomendação) | Estimador do ganho de informação por limite inferior (estável e barato) |
| c154 | S / p (amostras de Pareto sets / pontos) | Específico | 10 / 10 | paper | Média sobre 10 amostras do ótimo, 10 pontos por set |
| c154 | RFF num_features | Específico | 1024 (par) | código oficial | Random Fourier Features dos decoupled paths (aproximação fiel do GP) |
| c154 | Amostragem de paths | Específico | MatheronPathModel(seed=) | código oficial | Amostras de função via Matheron; base p/ pareto_sets/fronts e box decomposition |
| c154 | Ruído do modelo | Específico | condicionado COM ruído da likelihood | código oficial | JES-MO não expõe knob noiseless (difere de c262/e81) |
| c154 | LB jitter | Específico | 1e-6 (no logdet) | código oficial | Evita logdet de matriz mal-condicionada |
| c154 | Otimizador de aquisição | Específico | optimize_with_nsgaii embutido (pop 250, HV-greedy) | código oficial | Otimiza a aquisição via NSGA-II interno + truncagem HV-greedy (cobre quase todo o protocolo do paper) |
| c154 | Init (DoE) | Global-override | 11D−1 LHS (≠ 2(D+1)) | protocolo uniforme (Anexo J) | Sobrescreve o 2(D+1) do paper |
| c154 | Sinal / domínio | Compartilhado (BO) | Maximização, [0,1]^D | §5.5 | BoTorch maximiza; cubo unitário |
> **Notas (otimizador interno do JES — D75; §6.4 é a DONA da receita).** **Principal = `random_search_optimizer`** (default de produção, barato); **checagem de fidelidade = `optimize_with_nsgaii(pop=100, gen=500)`** rodada só no **piloto**, em 1–2 problemas, para medir o gap (a)vs(b). **A variante `pop=250` foi REMOVIDA (D75)** — encerra a DEF-B9.5 (única receita dos 16 sem fechamento). Pipeline do paper = RFF L=500 + NSGA-II + HV-greedy (divergência menor RFF 1024 vs 500 anotada). GHV por região = opcional (D52). JES-MO não expõe knob noiseless (condiciona com ruído da likelihood).
| c154 JES | BoTorch 0.18.1 `qLowerBoundMultiObjectiveJointEntropySearch`; estimation_type="LB"; S=10/p=10 (⟦v2.2⟧ **sem defaults no código** — `sample_optimal_points` exige os valores; 10/10 vem do paper); ⟦v2.2⟧ pipeline de caminhos = **Matheron/decoupled paths** (prior RFF num_features=1024 default, precisa ser PAR; a docstring "RFF" está desatualizada — não é RFF puro); `MatheronPathModel(seed=)` é o único seed explícito; ⟦v2.2⟧ construção prévia obrigatória: pareto_sets (S×P×d), pareto_fronts (S×P×M), `compute_sample_box_decomposition` (S×2×J×M; DominatedPartitioning em loop por amostra; ref interno −1e10); o `__init__` já **condiciona o modelo COM ruído da likelihood** (sem knob noiseless no MO); LB: jitter fixo 1e-6 no logdet M×M; entropia inicial SEM jitter (hazard: q=1 mitiga) | "LB" ✓ (recomendação do paper); ⚠ pipeline do paper = RFF L=500 + NSGA-II (100 pop/500 ger/10 off) + truncagem HV-greedy [DEF-B9.5]; ⟦v2.2⟧ **`optimize_with_nsgaii` embutido no BoTorch** (pop default 250, HV-greedy interno na truncagem, **sem knob n_offsprings**; completa com dominados via np.random.choice; pode retornar shape≠P) — cobre quase todo o protocolo do paper; `random_search_optimizer` (Sobol 1024, max_tries 10) trunca por **slice**, não HV-greedy; acqf do paper: 5D restarts/pool 1000·D; ruído inferido mesmo a 0% ✓; q>1: aviso é só docstring |

---

### I.11 · c154 JES (BoTorch 0.18.1)
**Fluxo real:** GPs por objetivo → amostrar S=10 conjuntos (X*,Y*) da posterior (caminhos RFF; otimização dos caminhos = pipeline nosso, B9.5) → qLowerBoundMultiObjectiveJointEntropySearch("LB") condiciona nos pares amostrados e mede o ganho de informação conjunto → optimize_acqf → 1 FE. **Integração:** E.1; não fixar σ²=0 (jitter); num_restarts=5D/raw=1000D (valores do paper). **σ exportável:** posterior; logar também os S fronts amostrados. **Nuances do paper:** JES ≥ β·PES+(1−β)·MES (Prop. 1); invariância a reparametrizações monótonas (Prop. 3 — argumento anti-viés-de-escala do HV); forte out-of-sample / mais fraco in-sample → registrar o protocolo de recomendação (nosso IGD/HV é sobre pontos amostrados — o paper usa recomendação out-of-sample; assimetria documentada §20).

---

### L.11 · c154 JES — receita por iteração: modelo como no L.10 (ruído INFERIDO — não fixar train_Yvar; B9.x) → (a) default: `sample_optimal_points(model, bounds, num_samples=10, num_points=10, optimizer=random_search_optimizer, maximize=True, optimizer_kwargs={pop_size:1024, max_tries:10})` com try/except do RuntimeError; ou (b) paper-faithful: por amostra s, `MatheronPathModel(model, seed=hs)` → `MultiOutputPosteriorMean` → `optimize_with_nsgaii(..., q=10, population_size=100, max_gen=500, seed=hs')` (truncagem HV-greedy interna; SEM knob n_offsprings=10 — relaxar ou loop pymoo próprio) → `compute_sample_box_decomposition(pf)` → `qLowerBoundMultiObjectiveJointEntropySearch(model, ps, pf, hcb, estimation_type="LB")` (condiciona no __init__, COM ruído) → optimize_acqf (5D restarts / pool 1000D). Shapes: ps (S,P,d) em X original; pf/hcb na escala ORIGINAL de Y. **RNG:** pesos do prior/Gamma/ε do update/Sobol do random_search = torch global; NSGA-II: pymoo seed + np.random.choice + random.choice (semear os 3). **Hazards:** logdet inicial sem jitter (q=1 mitiga); NSGA-II pode retornar shape≠P (guard). **FE:** init + 1/iteração — exato.

---

### M.8 · c154 JES
- **Por que a incerteza CONJUNTA (Prop. 1, com intuição):** condicionar em mais variáveis nunca aumenta a entropia → JES (condiciona em X* E Y*) tem entropia condicional ≤ a de PES (só X*) e a de MES (só Y*) → **αJES ≥ max(αPES, αMES) por construção**, não por heurística. Intuição: PES capta a correlação-de-input com x*, MES a probabilidade de superar y*; JES capta os dois canais. É o racional de por que escolhemos o JES como representante O2 (cobre o information-gain de forma dominante).
- **Invariância a reparametrizações = argumento anti-viés-de-escala do HV (Prop. 3):** o HV é Pareto-compliant mas trata objetivos **assumindo implicitamente que 1 unidade de um objetivo = 1 unidade de outro** (hipótese arbitrária) e enfatiza os extremos do front; uma transformação monótona por objetivo muda qual conjunto o HV prefere sem mudar o Pareto set. PES/MES/JES são AGNÓSTICOS à parametrização ("tratam todo ponto do front como igualmente desejável a priori"). Este é um argumento forte para a dissertação sobre **por que métricas info-teóricas complementam as de HV**.
- **Exploração/explotação dentro do funcional:** αJES-0 decompõe em explotação (−E[log p(y⪯Y*)]) + exploração (diferença de log-variâncias) — um único critério, sem κ de balanço. **Assimetria out-of-sample vs in-sample:** a recomendação default do paper é out-of-sample (NSGA-II sobre a média posterior); se a decisão final for restrita aos pontos amostrados, o JES é penalizado por escolher pontos *informativos*, não os melhores → **fundamenta a ressalva da §20** (nosso IGD/HV in-sample penaliza o JES; considerar ε-greedy ou reportar a assimetria).

---

### E.1 — JES (c154) · BoTorch 0.18.1 [FONTE ATUALIZADA v2.1] · O2/entropy-search
**Fonte:** `qLowerBoundMultiObjectiveJointEntropySearch` do **BoTorch 0.18.1** — implementação da formulação Lower-Bound do próprio paper (Tu et al. 2022). **Supera o plano do env pinado benmltu/JES** (que morre em BoTorch 0.5.1/pymoo 0.5.0): um único env moderno serve c262+c154. O repo benmltu vira referência de conferência de parâmetros.
**Parametrização (§5.5):** convenção BoTorch — [0,1]^D + `standardize` + **maximiza** → reusa o wrapper do qNEHVI.
**Pipeline pré-aquisição (é NOSSO — decisão B9.5):** amostrar S=10 fronts de Pareto da posterior e p=10 pontos/front (defaults = paper). O paper otimiza os caminhos amostrados com **RFF L=500 + NSGA-II (pymoo: pop 100, 500 ger, 10 offspring) + truncagem HV-greedy (ref = nadir observado − 0.1·|nadir|)**; o helper default do BoTorch usa `random_search_optimizer` (Sobol 1024, max_tries 10, pode lançar RuntimeError). ► Fidelidade ao paper = caminho NSGA-II-pymoo; decidir com teste no piloto.
**Estimation type:** `"LB"` (recomendação explícita do paper: a estimativa mais barata; "LB2" é fallback diagonal; evitar "0").
**Otimização da aquisição (valores do paper):** multi-start L-BFGS-B, **num_restarts=5·D**, pool inicial **1000·D** pontos.
**⚠ Ruído no noiseless:** o paper infere σ² do GP mesmo a 0% de ruído (prior Gamma) e trata os Pareto samples como pseudo-observações — **não fixar σ²=0**; manter inferência + jitter para estabilidade do Cholesky.
**DoE/orçamento/FE:** DoE compartilhado como `train_X`; 1 FE/iteração; `11D−1` + `20D` ⇒ `31D−1` (init do paper era 2(D+1) — desvio declarado).
**Camada surrogate:** por iteração, candidatos avaliados na otimização da aquisição + μ/σ do posterior; logar também os fronts amostrados (S×p) se barato.
**Sub-estudo batch:** ~~verificar repo~~ **FECHADO** — qLB-JES batch é suportado no BoTorch (greedy sequencial; o paper prova submodularidade e garante regret e⁻¹), com caveat documentado de não-monotonicidade (B9.4).

---

**Âncora de fidelidade (Anexo J):**

| c154 JES | ZDT2(d6), SnAr(d4), Penicillin(d7,M3), Marine(d6,M4) — com ruído 0,5–10%; L.4 inclui 0% | 2(D+1) | 100 iterações | 100 | mean log-HV-discrepancy ±2SE; GHV; SEM testes | ZDT2 q=1 (run p20): JES-LB 1,14 < MES-LB 1,63 < TSEMO 1,91 < NEHVI 2,38 < Sobol 3,14 |
