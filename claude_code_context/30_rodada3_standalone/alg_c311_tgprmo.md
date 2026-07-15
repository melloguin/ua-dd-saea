# c311 TGPR-MO (autor, Python/DESDEO/GPy — OFFLINE)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Específicas:** σ nas folhas = extensão nossa ('author-modified', D73b); **fallback D78** (treed/sparse-GP substituto se o venv py3.9+GPy não fechar); tier big=50k c311-only; vetorizar predict se o piloto mandar (D84); conferir `*_archive` do Population (fix: copiar do b5 — mesmo fork).

---

- [ ] **3.3 · c311 TGPR-MO** *(I.17, L.17, N.3 — offline)* — **venv py3.8 PRÓPRIO** (mesma regra de não-co-importar). ⚠ **NÃO importar `evaluate_population`** (dispara `matlab.engine.start_matlab()` no import — não usamos); usar **só `framework/`** (as estratégias de `Main_Execute_SS` estão quebradas e não entram); a `DataProblem` viva é a de `desdeo_problem/Problem.py:913`. Receita: `run_treed_GP(X, F, x_low, x_high)` → `RVEA(use_surrogates=True, n_iterations=10)` → ND final. **Piso big = `build_surrogates` direto** (treeGP sem addGPs — B15.4). **σ = extensão NOSSA** (🟢 B15.5 — patch exportar; o código descarta). Guards: `GPy optimize('bfgs')` **sem try** → try + dedup do dataset (LinAlgError mata a run); `graphviz` import duro; predict 1-ponto-por-linha = custo real do building (mitigação opcional: vetorizar à la `predict_new`). Logar `len(dict_gps)`, `total_points_per_model_sequence`, iterações efetivas; instrumentar os archives do building (descartados no caminho 2-fases). Âncoras de escalabilidade: build @50k treed **31,6 s** × sparse **21.600 s**; edge 61 pts/D=2 → 4 iterações, early-stop inativo.

---

| c311 | Critério da árvore | Específico | MSE | código oficial | Split por redução de MSE; particiona o espaço em folhas |
| c311 | min_samples_leaf | Específico | 10D | paper ✓ (Nmin=10D) | Mínimo de pontos por folha (dados suficientes p/ o GP local) |
| c311 | max_depth | Específico | 100 | código oficial | Profundidade máxima (teto folgado) |
| c311 | Construção (RVEA) | Específico | Imax=ceil(N/(10D)) × Gmax=50 | paper ✓ | Orçamento do RVEA na construção da árvore |
| c311 | Early-stop | Específico | 2 iters sem crescer (mín. 6) | código oficial | Para quando o nº de soluções em folhas sem GP não cresce por 2 iters |
| c311 | Otimização final (RVEA) | Específico | 10 iter × 100 ger = 1000 ger | paper ✓ | Busca final sobre a árvore treinada |
| c311 | Kernel GP local | Específico | GPy Matern52 ARD; sem White/normalizer/priors; bfgs único | código oficial | GP por folha; 1 otimização BFGS sem restarts |
| c311 | Seleção / escopo do GP | Específico | argmax impurity de treino; só pontos da folha | código oficial | Próxima folha = maior impureza; cada GP só com os pontos da folha (modelos locais) |
| c311 | RVEA selection_type | Específico | "mean" | código oficial | Seleção pela média prevista (o paper nunca consome σ) |
| c311 | α (APD) | Compartilhado (b5,c311) | 2 | paper ✓ | Expoente de penalização angular |
| c311 | Pop (lattice) | Compartilhado (b5,c311) | 50 (M=2) / 105 (M=3) | paper ✓ | Tamanho da pop = nº de vetores de referência |
| c311 | σ das folhas | Específico | sqrt(var_GPy) | EXTENSÃO nossa (D30) | Desvio do GP local exposto (o paper anuncia σ e nunca consome) |
| c311 | Tier do dataset | Global-override | big=50k (c311-only); small=31D−1, medium=2000 | D38 (big 50k ✓ paper) | Tamanho do dataset offline por tier; big=50k só p/ c311 (GP cheio dá OOM nos demais) |
> **Notas.** σ das folhas (sqrt(var_GPy)) é extensão nossa (D30). Tier big=50k é override exclusivo (D38; os demais dão OOM). D51: eixo LHS×MVNS no sweep. Kernel local sem restarts → hazard de ótimo local. α=2 e lattice 50/105 compartilhados com b5.
| c311 TGPR-MO | árvore MSE, `min_samples_leaf`=10D, ⟦v2.2⟧ **max_depth=100** (não "livre"); construção RVEA Imax=N/(10D) (float → ceil) × Gmax=50; ⟦v2.2⟧ **early-stop re-lido**: `delta = total_points − sequence[counter−3]` com `counter>5` — janela de 2 iterações sobre o nº de soluções em folhas SEM GP ⇒ **implementa ≈ o critério do paper com persistência de 2 iterações e mínimo de 6** (B15.8 rebaixada de divergência a nuance); final RVEA 10×100 ✓; ⟦v2.2⟧ kernel confirmado: **GPy Matern52 ARD**, sem White/normalizer/priors, `optimize('bfgs')` ÚNICO (sem restarts); folha nova = argmax da **impurity de treino** entre folhas visitadas sem GP; GP local usa SÓ os pontos da folha; `_refresh_population` re-avalia tudo (+1 ger/iteração); ⟦v2.2⟧ **σ vira NaN** (não None) no pipeline — nosso patch encaixa sem plumbing; **duas implementações no repo**: `treeGP` (framework/, SEM GPs iniciais — a canônica) × `HybridTreeGP_v2` (SS, GPs iniciais c/ MSE>1) — usar a 1ª; ⟦v2.2⟧ **pygmo NÃO está no caminho framework/** (zero imports — o swap p/ pymoo só seria p/ drivers de análise); RVEA `selection_type="mean"`, α=2, adapt no INÍCIO de cada iterate; pop lattice 50 (M=2)/105 (M=3), **pode encolher** | Nmin=10D ✓ paper; Imax/Gmax ✓; final 1000 ger ✓; σ nunca consumido no paper ✓ (patch = extensão nossa); tier big 50k ✓; ⟦v2.2⟧ hazards novos: `m.optimize` SEM try (LinAlgError derruba a run — jitchol do GPy tenta ~5 jitters antes); **predict em loop Python 1-ponto-por-linha** (50k/D=2 sem early-stop ≈ 39M chamadas GPy — inviável; early-stop corta; mitigação opcional: vetorização à la `predict_new`); `graphviz` é import hard; env efetivo **py3.8** (lock: numpy 1.20.2, sklearn 1.1.2, GPy 1.9.9, pymoo 0.4.2.2 NUNCA importado); piso big = `build_surrogates` direto (sem flag; predict puro-árvore vetorizado) |

---

### I.17 · c311 TGPR-MO (autor, Python/DESDEO/GPy — offline)
**Fluxo real:** árvore de regressão (MSE, min_samples_leaf=10D, **max_depth=100** — ⟦corrigido v2.7; não 'livre'⟧) por objetivo sobre o dataset → construção iterativa: RVEA roda 50 ger sobre o modelo híbrido; a cada iteração, a folha visitada de pior MSE ganha um GP local (Matérn 5/2 ARD, ≤2Nmin−1 pontos); para por Imax=N/(10D) ou early-stop → otimização final RVEA 10×100 → ND final. Predição: μ do GP na folha (ou média da folha se sem GP); **σ descartado pelo código e nunca usado no paper** → patch = extensão nossa (B15.5). **Integração:** E.9; NDS do pymoo no lugar do pygmo; logar Imax efetivo/nº de GPs; early-stop código≠paper (B15.8). **Piso big:** treeGP sem addGPs (B15.4). **Âncoras de escalabilidade (paper):** full GP OOM ≥10k (2 GiB cap; 56 GiB projetados @50k); build mediano @50k: treed 31,6 s × sparse 21.600 s (~683×) — o espelho offline do achado V-B.3.

---

---

### L.17 · c311 TGPR-MO — receita: `sys.path.insert(1, REPO_ROOT)`; `np.random.seed(s); random.seed(s)`; `prob, tppm, seq = run_treed_GP(X, F, x_low, x_high)` (constrói DataProblem+treeGP internamente; Imax=N/(10D), G=50, early-stop interno) → `evolver = RVEA(prob, use_surrogates=True, n_iterations=10)` → loop → `evolver.population` (+archives por geração). **Piso big = `build_surrogates(...)` direto** (pula o while; predict puro-árvore vetorizado — rápido mesmo em 50k). Building archives são descartados no caminho 2-fases → instrumentar o loop p/ a camada surrogate do building. Logar: `len(model.dict_gps)` (nº de GPs/objetivo), `total_points_per_model_sequence`, iterações efetivas. **Hazards:** GPy `optimize('bfgs')` sem try (LinAlgError mata a run — jitchol tenta ~5 jitters; dedup do dataset ajuda); predict 1-ponto-por-linha (loop Python) — custo real do building em datasets grandes (50k/D=2 sem early-stop seria ~39M chamadas; early-stop corta; mitigação opcional: vetorização à la `predict_new`); `graphviz` import hard. **RNG:** numpy global (pyDOE lhs, SBX, PM, sklearn-tree random_state=None) + stdlib random (shuffle SBX); GPy determinístico neste caminho. **Contagem:** interna ao DESDEO (surrogate-only); FE real = dataset (injetado) + ND final 1× (externo). Edge: 61 pts/D=2 → ≤3 folhas, ⌈3,05⌉=4 iterações de building, early-stop inativo (exige >5).

---

### M.17 · c311 TGPR-MO (números de escalabilidade — achado-alvo offline)
- **Por que treed-GP:** GP cheio é O(N³) tempo / O(N²) memória (O(KN²) p/ K objetivos); sparse-GP corta custo mas degrada acurácia *perto da PF*. Insight central: **no offline só importa acurácia na região de trade-off** — daí árvore barata para localizá-la + GPRs locais só nas folhas dela. **Por que árvore e não K-means:** a árvore particiona o espaço de decisão minimizando a perda nos valores OBJETIVO (agrupa objetivo-semelhante e ainda prediz), enquanto K-means/mean-shift usam perda no espaço de decisão; a folha de MAIOR perda entre as tocadas pela MOEA é simultaneamente região-Pareto E onde a árvore é pior.
- **Variância anunciada mas NÃO consumida:** o GPR fornece a variância (motivo de escolher GPR), mas a otimização usa só a média; o autor DECLARA que consumir a variância fica como trabalho futuro — **portanto o nosso patch de σ (Anexo L.17) vai ALÉM do paper**, e o "único treed-GP" nem usa o σ que motiva sua inclusão no nosso eixo de incerteza (ponto honesto e interessante para a dissertação).
- **Números (citáveis):** GP cheio K=3 = 2,3 GiB@10k → **56 GiB@50k** → OOM consistente com teto de 2 GiB/run (só rodou a N=2000); TGPR-MO pior caso O(KN(2Nmin−1)²) ≈ **linear em N**; construção medida ~13–28 s vs 86–9370 s (sparse) vs 136–616 s (full, só N=2000); melhor em tempo em ~46–48/48 instâncias; testado até N=50.000. **Nuance de qualidade:** em N=2000 o full-GP vence (HV e RMSE) → o TGPR-MO só se justifica quando N é grande o bastante para o full-GP ficar inviável — exatamente o nosso tier big (30–50k). Fundamenta a §11.5.

---

---

**Âncora de fidelidade (Anexo J):**

| c311 TGPR-MO | DBMOPP P1–P4 (n∈{2,5,7,10}; K∈{3,5,7}); DTLZ supl. | datasets 2k/10k/50k (LHS+MVNS) | construção N/(10D)×50 + 1000 ger | 31 | HV (ref 2√K), RMSE, build-time; Wilcoxon+Bonferroni | full GP OOM ≥10k (cap 2 GiB); build @50k: treed 3,16e1 s × sparse 2,16e4 s; @2k full GP vence em RMSE (4,18e-2 × 2,67e-1) |
