# c141 MMRAEA (autor, MATLAB — porte 3 linhas)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Decisões específicas:** D76 registra **L4**: `+eps` no SDE (NaN) é 🟠 obrigatório. Renames defensivos opcionais (colisões same-folder se auto-resolvem — S.8).

---

- [ ] **c141 MMRAEA** *(I.7, L.7, N.2.6)* — porte 3 linhas (MMRAEA.m:21/:50 → `Problem.Evaluation`; EAOptimization.m:33 → `OperatorGA(Problem,·)`). ✔ procedência verificada na v4.2: o init é **STOCK** (byte-igual ao idioma K-RVEA oficial — S.2#18). **Guard batch-vazio** antes da :50 [IMPL]; `N=min(100, 11D−1)` (DEF-A5 — crash pool<N em **D≤4** ⟦v5.2.1 — corrigido: a faixa D≤9 divergia da linha de fidelidade e da tabela⟧); **guard NaN do SDE → `+eps` logado** (DEF-L4). σ = **U de ranks** (D45). Instrumentação: Fit1/2/3 (InfillStrategy:11–17), ranks/Q/U (:28–35), nível de saída, subpops pós-ES_PDR + **telemetria de quantos ciclos ativam o ramo (Q,U)**. FE: init :21 + batch variável 0..2N (:50) → hard-stop. **Zero toolbox; o único MATLAB parfor-limpo** (N.2.6).

---

| c141 | N por subpopulação | Específico | min(100, 11D−1) | D20 (anti-crash; paper 50/subpop) | Tamanho de cada subpop; teto 100 + piso 11D−1 evitam N>amostras (crash D≤4) |
| c141 | Nº de subpopulações | Específico | 2 (ES_PDR = NSGA-II) | código oficial; paper ✓ | Duas subpops evoluídas por NSGA-II; base da cascata de infill |
| c141 | Ensemble RBF | Específico | 3× multiquadrático, c=1, poly=0 | código oficial; paper ✓ (MQ σ=1) | 3 surrogates MQ; o desvio entre os 3 vira uma das incertezas (D45) |
| c141 | Scaling de X no RBF | Específico | nenhum | CÓDIGO herdado do paper (D30) ✓ | Não normaliza as variáveis antes do RBF |
| c141 | Solve do RBF | Específico | mldivide denso, sem regularização | código oficial | Resolve pesos por mldivide denso (risco de mau condicionamento, mantido) |
| c141 | Operadores GA | Específico | SBX proC=1,0/disC=20; PM proM=1/d | código oficial (Balde B); paper ✓ | Reprodução nas subpops NSGA-II |
| c141 | CSO r1, r2 | Específico | escalares | código oficial | Coeficientes do Competitive Swarm Optimizer como escalar (1 valor/par) |
| c141 | Batch de infill | Específico | variável (pode ser 0) | código oficial; paper ✓ | Emerge da cascata de 3 níveis; pode ser 0 num ciclo (iteração 0-FE) |
| c141 | dsmerge (ds) | Específico | 1e-14 | código oficial | Distância de dedup; pontos a <1e-14 são fundidos |
| c141 | σ exportado | Específico | 2 colunas (D45) | D45 | Exporta AS DUAS incertezas: nativa (ranks/SDE) + desvio entre os 3 RBFs (comparável ao ensemble do c149) |
> **Notas.** FEmax nativo do paper=11d+119 NÃO adotado (usamos maxFE=31D−1). Cascata de infill (3 níveis) gera o batch variável. Kernel/scaling/solve = CÓDIGO herdado do paper (MQ σ=1, sem scaling, mldivide sem reg.) — fiéis. D45: as duas incertezas em colunas separadas.
| c141 MMRAEA | 3 RBFs multiquadráticas (⟦v2.2⟧ **B12.7 fechada no código**: `rbf_build(S,Y)` com defaults idênticos ×3 — MQ c=1, poly=0; NENHUM scaling de X; solve por `mldivide` denso SEM regularização); ⟦v2.2⟧ cascata de infill **sem u=5 em lugar nenhum** (gatilhos = "resta >1 candidato"); nível 1 mistura POP predita + ARQUIVO verdadeiro; nível 2 = ND de [−Fit1, Fit2, −Fit3] (max SDE-calc, min FN-pred, max SDE-pred); nível 3 = front ND de (Q,U) — **minimiza U** — ∪ argmax U; **batch VARIÁVEL, pode ser 0** (iteração 0-FE); CSO com r1,r2 ESCALARES por par; ES_PDR = seleção NSGA-II literal nas DUAS subpops (SDE só no torneio do CSO); subpops sequenciais sem migração; ⟦v2.2⟧ **B12.6 fechada: `Problem.N` é POR subpopulação** (pool de infill = 2N) — fidelidade ao paper = N=50; ⟦v2.2⟧ **crash real é D≤4 com N=100** (ES_PDR.m:20; pool ger.1 = NI+2·⌊NI/2⌋) — fix N=min(100,11D−1) segue válido (conservador) ou fix mínimo `Rank(1:min(end,·))`; dedup `unique` por decisão REORDENA o arquivo (lex) a cada ciclo; dsmerge ds=1e-14 (quase-duplicatas passam → warning de mal condicionamento) | Batch variável ✓ paper (FATO); kernel MQ σ=1 ✓; sem scaling ✓ (herdado do paper); U de ranks ✓; SBX 20/1.0 + PM 1/d ✓ (GA); FEmax do paper = 11d+119; ⟦v2.2⟧ hazard novo: SDE via min-max → **NaN se fmax=fmin** em algum objetivo do subconjunto (propaga ao NDSort do nível 2) [PP L]; srgtsRBF* = código morto |

---

### I.7 · c141 MMRAEA (autor, MATLAB API 3.x → porte 4.15)
**Fluxo real:** 3 RBFs multiquadráticas (σ=1, sem scaling) sobre alvos distintos — objetivos (ARBFs), SDE-fitness (FitRBF), front number (FNRBF) → bi-pop wmax=20: P1 CSO (fitness=SDE predito) explora, P2 GA (SBX/PM, seleção ambiental NSGA-II sobre ARBFs) explota → triagem: 1º front ND real∪pop (predito); se >u=5, 1º front de **[−Fit1, Fit2, −Fit3]** ⟦v5.2.1 — corrigido: os sinais divergiam da regra canônica ⟦v2.2⟧ da linha de fidelidade (max Fit1, min Fit2, max Fit3)⟧; ⟦v5.2.1 — o gatilho **u=5 foi REVOGADO pela v2.2** (a cascata de infill não o usa em lugar nenhum); o texto abaixo descreve a leitura antiga⟧ se >5, **frente ND de (Q,U) ∪ argmax U = batch variável** (Q=Σranks, U=discordância de ranks Eq. 8). **Integração:** porte 3 linhas; N=min(100,11D−1) (crash pool<N em D≤9 — DEF-A5); injeção do DoE **D63/classe D94** em `MMRAEA.m:24` — `A2 = Problem.Evaluation(Problem.data.X0)` substitui UniformPoint-Latin + re-escala + `SOLUTION(dec)` **DE UMA VEZ** (`handoff/R1-c141.md` §2) ⟦v5.2.1⟧. **σ exportável:** U de ranks nativa (requer ranks sobre a pop completa — extensão leve) vs desvio bruto entre modos (escalas incomensuráveis) — DEF-B12.4. **Checks novos:** N subpop×Ptot (B12.6); kernels por modo (B12.7). Em D baixo/M=2, o ramo (Q,U) raramente ativa (|front|≤5) → logar telemetria de quantos ciclos usam U.

---

### L.7 · c141 MMRAEA — porte 3 linhas confirmado (MMRAEA.m:21/:50 SOLUTION→Problem.Evaluation; EAOptimization.m:33 OperatorGA(Problem,·)). ⟦v5.2.1 · RESOLVIDO⟧ o mtime divergente do init (`MMRAEA.m:19–21`, 2024-04 ≠ 2022-01 dos demais) foi investigado: o init é **STOCK**, byte-igual ao idioma K-RVEA oficial (S.2#18) — nenhuma edição de terceiros. Guard batch-vazio antes da :50 [IMPL] (`Problem.Evaluation([])`). Fix alternativo do crash: `Rank(1:min(end,N−sum(Next)))` em ES_PDR.m:20. Instrumentação: Fit1/2/3 (InfillStrategy:11–17), ranks/Q/U (:28–35), nível de saída (:9/:24/:41/:44), subpops pós-ES_PDR (EAOptimization:26–28/:42–43). **RNG:** LHS; por ciclo: 20×[randperm + 2 rand escalares/par + PM 2 rand] (CSO) + 20×OperatorGA; ZERO RNG em infill/RBF/dsmerge/ES_PDR. **FE:** MMRAEA.m:21 (init) e :50 (batch variável 0..2N; overshoot ≤|PopNew|−1). Dependências: NENHUMA toolbox (rbftlbx e dsmerge inclusos; srgtsRBF* morto).

---

### M.13 · c141 MMRAEA
- **Por que 3 alvos (não 3 kernels):** sem σ analítico (RBF escolhida porque Kriging é O(n³)), os 3 modos "cooperate to estimate quality AND uncertainty": ARBFs=objetivos; **FitRBF prevê o escalar SDE porque o CSO precisa de fitness escalar** para decidir vencedor/perdedor; FNRBF=front-number. A **incerteza = discordância de ranks** entre os 3 modos (proxy barato de erro epistêmico sem GP); uso bivalente: preferir baixa incerteza (confiabilidade) E forçar o ponto de máxima incerteza (exploração em alta-dim).
- **Ablação do bi-pop:** MMRAEA-CSO sozinho SUPERA o completo em DTLZ1/DTLZ3 (multimodais — exploração do CSO), mas o completo vence no geral → "validates that the bi-population strategy is effective" (CSO explora, GA exploita). Honestidade: inadequado para many-objective; RBF impreciso em WFG (perde para os classificadores do MCEA/D).

---

**Âncora de fidelidade (Anexo J):**

| c141 MMRAEA | DTLZ1–7, ZDT1–4/6, WFG1–9 × d∈{20,40,60,100} | 11d−1 LHS | 11d+119 | 20 | IGD (10k ref); Wilcoxon+Friedman 0.05 | DTLZ2 M=3 d=20: 1,2010e-1; ZDT1 d=20: 3,3486e-2; admite fraqueza em WFG (MCEA/D vence 18/6/12) |
