# c238 EIM (autor, MATLAB standalone → embrulho ALGORITHM)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Decisões específicas:** Embrulho `classdef EIM < ALGORITHM` (N.5, abaixo). Hard-stop usa o MESMO `PlatEMO:Termination` (D61).

---

- [ ] **c238 EIM** *(I.9, L.9, N.5, N.3)* — **conversão obrigatória p/ `classdef EIM < ALGORITHM`** (o script roda `clearvars/close all`): seguir o **contrato exato N.5** (8 pontos). **Remover as 2 linhas `Hypervolume`** (:40,:64 — mex Windows-only, crash em Linux); `criterion` vira variável (literal hardcoded; var morta :51); `rng(seed)` no topo. Guards [IMPL]: `EIM(isnan(EIM))=0`; `max(range,eps)` no re-scaling; **chol desprotegido** (GP_Train.m:22) → dedup do dataset. GA interno fica (🟠 CÓDIGO, D30); anti-clustering ausente → CÓDIGO + guard. Logar min/max do y-scaling/iteração (C3) + `[y,u,s]` do Infill_EIM + pop final do GA. FE exato (overshoot zero). Optimization (fmincon sqp) + Statistics.

---

| c238 | Critério de aquisição | Específico | EIM-Euclidean (EIMe), hardcoded | paper (variante EIMe ✓) | Expected Improvement Matrix euclidiano; 1 candidato/iter que maximiza a melhoria esperada conjunta |
| c238 | Tipo de kriging | Específico | Ordinary kriging (μ constante), estilo Forrester | código oficial | Surrogate gaussiano próprio (não DACE); μ/σ ao EIM (1 GP/objetivo) |
| c238 | Kernel | Específico | Gaussiano (squared-exponential) | código oficial | Correlação do kriging; assume resposta suave |
| c238 | Estimação de θ | Específico | MLE concentrada, fmincon SQP em log10(θ), single-start, MaxFunEvals=20D | código oficial | Ajusta θ por 1 arranque (rápido; sujeito a ótimo local) |
| c238 | θ0 / bounds de θ | Específico | 1 / [1e-3, 1e3] | paper ✓ | Ponto de partida e faixa dos comprimentos de correlação |
| c238 | Normalização de X | Específico | [0,1] por eixo | código oficial | θ comparável entre eixos, condicionamento estável |
| c238 | Nugget | Específico | (10+n)·eps | código oficial | Jitter na diagonal (cresce com n); regulariza |
| c238 | Re-scaling de y | Específico | min-max por iteração | paper ✓ | Reescala cada objetivo a [0,1] antes do EIM (equaliza escalas) |
| c238 | GA de aquisição | Específico | pop=10D, 200 ger, torneio k=2, SBX dis_c=10/0,5, PM dis_m=20/pm=1/D, (μ+λ) elitista | código oficial | Maximiza o EIM → 2000·D avaliações de aquisição/iter. **Diverge do paper (DE)** |
| c238 | Init (DoE) / maxFE | Global-override | 11D−1 LHS / 31D−1 | protocolo uniforme (Anexo J) | Sobrescreve o init=100 e maxFE=200 fixos do repo |
| c238 | Guard anti-crash Cholesky | Específico | ativo (objetivo constante → trata NaN) | fidelidade (CÓDIGO / IMPL) | Impede quebra do fit quando um objetivo é constante |
> **Notas.** Otimizador de aquisição diverge do paper (DE 50×50 F=0,8 CR=0,8 ×4); adotamos o **GA nativo** do repo (CÓDIGO). **Anti-clustering ausente** no repo (o remédio do paper dist<1e-8→argmax σ teria de ser adicionado — hazard, não decisão nossa). init/maxFE fixos do repo sobrescritos pelo global.
| c238 EIM | driver default EIM-**Euclidean** (⟦v2.2⟧ definido por **literal hardcoded** na chamada; a variável `criterion` é código morto — refactor deve passá-la); ⟦v2.2⟧ **kriging PRÓPRIO estilo Forrester** (não DACE): ordinary kriging (μ constante), kernel gaussiano, MLE concentrada via **fmincon sqp em log10(θ), single-start, MaxFunEvals=20D**, θ0=1, bounds [1e-3,1e3], X normalizado p/ [0,1] pelos bounds; nugget (10+n)·eps; **chol final DESPROTEGIDO** (duplicata exata → erro fatal); re-scaling min-max de y por iteração; ⟦v2.2⟧ GA interno: **pop=10D, 200 gerações**, torneio k=2, SBX **dis_c=10** por-variável (prob 0.5), PM dis_m=20 pm=1/D, seleção (μ+λ) elitista → 2000·D avaliações de aquisição/iteração; ⟦v2.2⟧ defaults do repo: init=100/maxFE=200 FIXOS (nosso 11D−1/31D−1 é injeção); overshoot **zero** (término exato) | ⚠ otimizador do paper = DE 50×50 F=0.8 CR=0.8 ×4 [DEF-B10.2]; re-scaling ✓ paper; θ₀=1/[1e-3,1e3] ✓; variante: paper não elege (EIMe mais consistente) ✓; ⟦v2.2⟧ **B10.7 FECHADA: anti-clustering NÃO EXISTE no repo** — o remédio do paper (dist<1e-8 → argmax σ) teria de ser adicionado por nós [PP L]; hazards: s=0/NaN sobrevive por sort; **objetivo constante → 0/0 → NaN → chol quebra** (guarda `max(range,eps)` [IMPL]); ⟦v5.2.1⟧ **CRASH LATENTE STOCK: front ND de 1 ponto → `min(reshape(...))'` (`Infill_EIM.m:25`) colapsa a ESCALAR → `Optimizer_GA.m:17` estoura ('Index exceeds…') — byte-idêntico ao repo oficial, deliberadamente NÃO consertado (falha HONESTA de código stock, não bug da integração; conserto = decisão de fidelidade do autor, D81); análogo ao crash latente do b3 (`UpdataArchive:61`)**; lhsdesign maximin its=1000 no DoE do driver |

---

### I.9 · c238 EIM (autor, MATLAB standalone)
**Fluxo real:** ⟦corrigido v2.7⟧ **kriging PRÓPRIO estilo Forrester (NÃO DACE; MLE via fmincon sqp single-start, §6.5)** por objetivo sobre y re-escalado min-max por iteração → matriz EIM (EI elemento a elemento vs cada ponto do front) agregada por min sobre o front (Euclidean no driver) → otimizador interno maximiza (GA no código; DE no paper) → 1 FE. **Integração:** refactor script→função; embrulhar como ALGORITHM PlatEMO (► B10.5); rng inexistente → injetar; substituir L28–29 pelo DoE. **σ exportável:** kriging próprio em espaço y-escalado → logar min/max por iteração (C3); s=0 nos amostrados → filtrar NaN. **Divergências:** GA×DE (B10.2 — a única material); re-scaling é do paper ✓; anti-clustering a verificar (B10.7).

---

### L.9 · c238 EIM — refactor: assinatura `EIM_core(fobj,M,D,lb,ub,DoE_x,DoE_y,maxFE,criterion,seed)`; passar `criterion` como VARIÁVEL (hoje literal hardcoded; var morta na :51); remover clearvars/fprintf/Hypervolume-mex; rng(seed) no topo. Wrapper PlatEMO-ALGORITHM: DoE via Problem.Evaluation; loop NotTerminated. Sanitizações [IMPL]: `EIM(isnan(EIM))=0` (s=0 & f=u), `max(range,eps)` no re-scaling, dedup/anti-clustering se aprovado (DEF de fidelidade). Instrumentação: saídas extras `[y,u,s]` do Infill_EIM (μ/σ já computados em :7–11) + pop final do GA; mínimo viável = 1 chamada extra pós-GA (0 FE). **RNG:** lhsdesign (DoE, maximin its=1000) + lhsdesign (init GA) + randi (torneio, sinal SBX) + rand (SBX μ, máscara, mutação); fmincon determinístico. **FE:** init 1 lote + 1/iteração; término EXATO (`while evaluation<maxFE` c/ +1) — overshoot zero. Aquisição: 2000·D avaliações/iteração (200 lotes × 10D).

---

### M.16 · c238 EIM
- **Por que a MATRIZ EIM e não o EI multiobjetivo verdadeiro:** o EI verdadeiro integra a região não-dominada em ~(k+1)^m células → maldição da dimensionalidade; racional de custo concreto: 6-obj, 200 iterações × GA(100×100) = 2×10⁶ avaliações do critério × 1 s ≈ **23 dias**, podendo exceder a própria simulação cara. A EIM troca por k×m integrações 1-D em forma fechada (linear em m). Escolhe manter a família EI para **herdar as propriedades teóricas do EI single-objetivo** e reaproveitar as extensões (restrições/ruído) — critérios lineares baratos anteriores foram rejeitados por "carecerem de propriedades teóricas".
- **Monotonicidade N1/N2 como qualidade:** N1 (ŷ¹ domina ⇒ EI maior) e N2 (mais σ ⇒ EI maior) são "fundamentalmente importantes"; **o EIe original as VIOLA** (a distância Euclidiana toma valor absoluto por eixo e ignora a direção) — por isso é o pior em todos os ZDT; matriciar restaura N1/N2. Racional que sustenta EIMe como default do driver.
- **Garantia noise-free:** em ponto amostrado s=0 → EIM=0 → o próximo é "qualquer um menos os já amostrados" → amostragem densa → convergência garantida ([45]); **vale SÓ sem ruído** (com ruído a incerteza é não-nula em todo ponto, quebra a densidade). Alinha com o nosso escopo noiseless (§16) — é um caso em que a ausência de ruído é *pressuposto de garantia*, não só simplificação.

---

### E.5 — EIM (c238) · autor/MATLAB standalone (fora do PlatEMO) [ENRIQUECIDO v2.1]
Não usa a API do PlatEMO → **wrapper próprio** OU embrulhar como `ALGORITHM` do PlatEMO (► embrulhar: uniformiza FE/export/DoE com o cluster MATLAB — DEF-B10.5); refactor script→função (remover `clearvars`; receber problem/seed/DoE/bounds/maxFE); remover `Hypervolume.mexw64` (Windows-only, só log); **injetar `rng(seed)`** (não existe nenhum no repo) + DoE compartilhado.
Sequencial q=1 nativo (argmax do EIM por iteração). **Variante: EIM-Euclidean** (default do driver; o paper NÃO elege default — EIMe é a mais consistente e recomendada c/ EIMm para fronts desconexos, §VI-D; registrar como escolha).
**⚠ Otimizador interno (DEF-B10.2):** o código usa **GA (SBX+PM)**; o paper especifica **DE/rand/1/bin, pop 50, 50 iterações, F=0.8, CR=0.8, ×4 restarts** (10.000 avaliações da aquisição/infill). Fidelidade-ao-código vs fidelidade-ao-paper — ping-pong (guarda-chuva K.3).
**Kriging (paper §V-B):** DACE regpoly0 + corrgauss, θ₀=1, bounds [1e-3, 1e3]; **re-scaling min-max de y por iteração É do paper** (§V-B(5)a) → logar min/max por iteração (DEF-C3); MLE do paper = boxmin do DACE (o fmincon do GP_Train do repo é reimplementação — Optimization Toolbox, §18). Anti-clustering do paper (dist<1e-8 → substitui por argmax σ) — verificar presença no código (B10.7). Minimiza; bounds nativos.

---

**Âncora de fidelidade (Anexo J):**

| c238 EIM | ZDT1–3 (m=2), DTLZ2/5/7 (m=3,4,6) — todos n=6 | 65 (11n−1) | 100 (m=2)/200 | 10 | HV (refs Tab. I) + IGD (grades); t pareado + signed-rank 0.05 | ZDT1 IGD médio EIMe=0,0178; ZDT3 IGD mediano 0,0380 (EIMh 0,0564); DTLZ2 m=3 HV mediano EIMh=15,031 |
