# b1 ParEGO (PlatEMO 4.15)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Decisões específicas:** D76 registra **L8**: guard `sqrt(max(mse,0))` (mse<0 do dacefit) é 🟠 obrigatório.

---

- [ ] **b1 ParEGO** *(I.1, L.1, N.3)* — patches: **P1 DoE = substituir `ParEGO.m:29–:30` JUNTAS** (v5.2 — D94: injeção do X nativo direto na `Problem.Evaluation`; a re-escala interna da :30 nunca roda — injetar só na :29 causa dupla-escala silenciosa em WFG/BBOB); P2 guard `sqrt(max(mse,0))` (`EvolALG.m:25`, DEF-L8, logado); P4 NaN-guard (`ParEGO.m:39`). O bug do torneio (EvolALG:16) **fica** (🟠 CÓDIGO — periférico, K.3); λ=100 vetores fica (CÓDIGO, D30). θ-bounds [1e-5,**20**]. Hazards: mutação-only copia o pai (~37% → mse≈0); near-duplicata <1e-6 → "Bad parameter region"; all-NaN na 1ª geração → `Best` indefinido. Instrumentação: λ (:36), θ/dmodel (:58–59), pop do GA interno (`Off`, EvolALG:16/:34), μ/σ (:23–27); **export lossy do escalar + λ + min/max + Gbest/iter** (D47/C3). FE: init :30, +1/iter :61 — exato. Statistics Toolbox.

---

| b1 | N (escalarizações / vetores λ) | Compartilhado (b1,b3,e7) | 100 (M=2 → 100 λ; M=3 → NBI 91) | D20 (default PlatEMO; paper não prescreve N load-bearing p/ b1) | Nº de vetores de peso λ por iteração p/ a escalarização; sorteia-se 1 λ/iteração p/ construir o alvo PCheby |
| b1 | GA interno de aquisição (IFEs) | Específico | 10.000 aval. do modelo/iteração | código oficial + paper ✓ | Orçamento do GA que maximiza a aquisição (EI) sobre o GP escalar; gasta 10k avaliações baratas do surrogate antes de propor 1 ponto real |
| b1 | ρ (Tchebycheff aumentada / PCheby) | Específico | 0,05 | paper ✓ + código | Coeficiente do termo aumentado Σ\|f_i\|; ρ=0,05 evita soluções fracamente dominadas — valor canônico ParEGO |
| b1 | Modelo DACE (regressão+correlação) | Compartilhado (b1,b3) | regpoly1 + corrgauss | código oficial (default); corrgauss ✓ | Kriging com tendência polinomial de 1ª ordem e kernel gaussiano; superfície de resposta do escalar PCheby |
| b1 | θ0 (init) + warm-θ | Específico | 10 (só na 1ª iteração; warm-start depois) | código oficial | Ponto inicial da MLE por θ na 1ª iteração; depois reusa o θ anterior (mais barato) |
| b1 | Bounds de θ | Específico | [1e-5, 20] | código oficial | Caixa de busca da MLE por θ (comprimentos de escala do kernel) |
| b1 | Otimizador da MLE | Específico | boxmin, SEM restarts | código oficial (mantido; periférico) | 1 corrida de boxmin de θ0 (paper: Nelder-Mead 20 restarts) |
| b1 | Subset de treino | Específico | top-(11D−1+25) por PCheby (determinístico) | código oficial (segue CÓDIGO) | Treina o GP nos melhores (11D−1+25) pontos pela escalarização corrente; sem componente aleatório |
| b1 | Normalização | Específico | min/max do arquivo, por iteração | código oficial | Reescala objetivos por min/max do arquivo antes de escalarizar (escala dinâmica) |
| b1 | Saída/incerteza σ | Específico | mono-output (escalar PCheby); σ = desvio do escalar | D47 | Um único GP modela o escalar de Tchebycheff (não M GPs); μ/σ são escalares — a essência do ParEGO; exporta μ/σ + loga λ, min/max, Gbest |
> **Notas.** b1 é BO-decomposição: usa GA interno na aquisição, **não** herda o Balde C (só b3/b4/e7). Divergências paper×código mantidas no **CÓDIGO** (periféricas, D30/D47): λ=100/91 vs 11/15; subset top-determinístico vs ½ melhores+½ aleatórias; GA geracional c/ truncamento elitista vs steady-state pop 20; MLE boxmin sem restarts vs Nelder-Mead 20 restarts; torneio bugado. D47: rejeitado treinar M GPs (mudaria o algoritmo — mono-output é ParEGO).
| b1 ParEGO | `Problem.N`=100 escalarizações (M=2); ⟦v2.2⟧ **M=3 → NBI devolve 91** (N reescrito em ParEGO.m:27); GA interno IFEs=10.000 (decremento PÓS-geração; lote ≈2·\|arquivo\|, crescente); DACE mono-output do PCheby (ρ=0.05): ⟦v2.2⟧ **regpoly1**+corrgauss, θ0=10 só na 1ª iteração (**warm-start de θ** depois), bounds [1e-5,20], MLE boxmin **sem restarts**; subset de treino = **top-(11D−1+25) por PCheby** (determinístico); normalização min/max do arquivo por iteração (ParEGO.m:39) | ρ=0.05 ✓, 10k evals do GA ✓ (Tab. V diz 200k — inconsistência do paper); ⚠ paper usa **11/15 vetores λ** [DEF-B1.1]; ⚠ subset do paper = ½ melhores + ½ aleatórias; ⚠ GA do paper = steady-state pop 20 (código: geracional c/ truncamento elitista); ⚠ MLE do paper = Nelder-Mead 20 restarts; B1.6 fechada: o código normaliza pelo ARQUIVO (não por limites conhecidos); ⟦D47⟧ **σ = escalar de Tchebycheff (mono-output) → export do escalar μ/σ + λ/min-max/Gbest (C3); reais por-objetivo via join ao ①** |

---

### I.1 · b1 ParEGO (PlatEMO 4.15)
**Fluxo real:** a cada iteração sorteia λ do conjunto de `Problem.N` vetores uniformes → re-escalariza TODO o arquivo pelo PCheby (Tchebycheff aumentada ρ=0.05) → treina 1 DACE mono-output no escalarizado (subset top do arquivo) → GA interno (EvolALG, ~10k avaliações) maximiza o EI do escalarizado → 1 FE real. **Integração:** ⟦v5.2.1 — CORRIGIDO pela D94⟧ o patch de DoE substitui o **par `ParEGO.m:29–:30` JUNTO** (injeção do X0 NATIVO do artefato direto na `Problem.Evaluation`; a re-escala da :30 NUNCA roda — patchar só a :29 causaria **dupla-escala silenciosa** em WFG/BBOB). N controla o nº de escalarizações. **σ exportável:** do escalarizado (mono-output) — logar λ, min/max da normalização e Gbest por iteração p/ reconstrução (DEF-C3); granularidade: ⟦v5.2.1 — corrigido, o implementado é OUTRO⟧ a ③ grava a **POPULAÇÃO FINAL do GA interno por iteração de BO** (a política 'BO com EA interno' da DEF-C2), não o best/geração — é o que dá o pool de candidatos com μ/σ que a análise precisa. **Divergências:** bug de índices no torneio (EvolALG.m:16, após iter≥26 — sem contraparte no paper, que usa outro GA); nº de vetores, subset de treino e GA divergem do paper (§6.5); NaN se objetivo constante (ParEGO.m:39 — DEF-A8).

---

### L.1 · b1 ParEGO — patch points: P1 DoE = **substituir ParEGO.m:29–:30 JUNTAS** (v5.2 — D94: injetar só no RHS da :29 causa dupla-escala — a :30 re-escala p/ bounds nativos); P2 guard mse (EvolALG.m:25); P3 fix opcional do torneio (passar PDec alinhado em ParEGO.m:60); P4 NaN-guard (ParEGO.m:39). Precisões: o bug do torneio, com o cap ativo (a partir do 27º treino), favorece sistematicamente os pontos mais ANTIGOS (LHS inicial) — pior que "desalinhamento"; predictor 1-ponto computa gradiente inútil (custo); hazards reais: mutação-only copia o pai com prob. ~37% → mse≈0; near-duplicatas <1e-6 → "Bad parameter region" (crash em convergência); todos-NaN na 1ª geração → `Best` indefinido. **RNG/iteração:** 1 randi (λ) + por geração interna: 2×randi(torneio) + GAreal (4 rand + 1 randi) + PM (2 rand) ×2 chamadas. **FE:** ParEGO.m:30 (init) e :61 (+1/iter) — total exato 31D−1, sem overshoot. Instrumentação: λ (:36), θ/dmodel (:58–59), pop do GA = `Off` local (EvolALG:16/:34), μ/σ no loop :23–27.

---

### M.1 · b1 ParEGO
- **Racional das escolhas:** o GA interno que maximiza o EI substitui o branch-and-bound do EGO **por facilidade de implementação e mira futura em restrições** (§III-A) — o autor declara o maximizador de aquisição *intercambiável*; isso legitima que a nossa fidelidade seja ao mecanismo (Kriging do escalarizado + EI), não ao GA específico. O nº de vetores de escalarização foi dimensionado para permitir **"várias passadas" sobre cada vetor** dentro do orçamento (§VII-B) — racional direto da DEF-B1.1 (por que poucos vetores no paper; nosso N=100 os multiplica e quebra esse racional — anotar).
- **Ablação/sensibilidade:** o paper **não abla os próprios knobs** (ρ, s, cap) — só compara com NSGA-II/random. Única sensibilidade real: em d=8 a 100 FEs o LHS 11d−1 consome 87% do orçamento e a fase inicial degrada ("chosen only 13 of 100") → em D alto o DoE domina (relevante para os nossos ZDT/WFG/DTLZ7 de D=22–30).
- **Garantia/pressuposto (honestidade):** §III **renuncia a garantia teórica** — o DACE "cannot be recommended on any theoretical basis" (no-free-lunch); só se justifica sob suavidade local + ruído baixo + dim. moderada. **O cap=80 e o subset ½-melhores/½-aleatório são concessão aos 21 runs, não o método**: "on a very expensive cost function, all solutions should be used to update the DACE model, at every iteration" — se algum dia questionarmos o cap de treino, o próprio autor está do nosso lado.

---

### E.10 — b1 ParEGO dual (registro)
No **principal**, b1 = **ParEGO do PlatEMO** (MATLAB, q=1, canônico). No **sub-estudo batch** (se aprovado na definição), a variante batch é o **qParEGO do BoTorch** — implementação diferente do mesmo princípio → **rotular como qParEGO** nos resultados batch, nunca somar/misturar com o ParEGO do principal. Propósito: dar ao batch um representante de decomposição barato; é opcional (V-B.2).

---

**Âncora de fidelidade (Anexo J):**

| b1 ParEGO | KNO1, OKA1/2, VLMOP2/3, DTLZ1a/2a/4a/7a (d=2–8; M=2–3; DTLZ *modificados*) | 11d−1 LHS | 100 e 250 FEs | 21 | HV (anti-ideal+0.01·range), ε-binário; Mann-Whitney 99% | DTLZ2a S=4,46196 (SD 0,0277) vs NSGA-II 4,07554; OKA2 24,0278 vs 19,1279; a 100 FEs NSGA-II vence DTLZ7a (12,99×16,90) |
