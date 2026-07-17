# b4 CSEA (PlatEMO 4.15)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Decisões específicas:** `ExecutionEnvironment='cpu'` obrigatório (N.2.4); N=50 do paper; export semântico (schema C1); stall 0-FE → guarda (c) do D60.

---

- [ ] **b4 CSEA** *(I.3, L.3, N.2.4)* — patches: init `CSEA.m:29`→11D−1; **`ExecutionEnvironment='cpu'`** (:47 — 'auto' disputa GPU e quebra reprodutibilidade); DoE (:30–31); **N=50 do paper** via `Problem.N` (B4.2); **treino no arquivo inteiro** (🔵 ARTIGO, B4.6/D30); treinador SGD-família fica (CÓDIGO). Registrar o z-score da `featureInputLayer` (:36). Guards: `randperm` pode exceder linhas se D>|Pop|+6 (SAS.m:30); stall 0-FE do regime R2 (monitorar via outputFcn); NaN em p0/p1 cai no else (ok). Export: L∈(0,1) dos selecionados + (p1,p2,rr,tr)/geração (C1). FE ∈ [maxFE, maxFE+11] → hard-stop. DLT + Statistics.

---

| b4 | N (Problem.N) | Global-override | 50 | D20 (override ao default-100; paper — load-bearing) | N limita o cap de treino e o nº de gerações sob orçamento → segue o paper (50) |
| b4 | K (refs) | Específico | 6 | paper ✓ + código | Nº de soluções de referência; rótulo 1 ⟺ candidato não é estritamente pior que TODAS as K=6 refs |
| b4 | gmax (gerações internas) | Específico | 3000 (lotes de 12) | código oficial | Máx. de gerações do otimizador guiado pelo classificador; candidatos em lotes de 12 |
| b4 | DoE inicial | Global-override | 11D−1 (cap min(·,109) removido) | fidelidade (ARTIGO/global) | Patch remove o cap 109; p/ D≥10 (11D−1>109) o cap reduziria o DoE — restaura 11D−1 |
| b4 | Conjunto de treino | Específico | arquivo INTEIRO | D30 (ARTIGO) | Corrige o cap nativo (=Problem.N); o classificador treina em todos os pontos → fronteira melhor (capar handicaparia) |
| b4 | Rede (arquitetura) | Específico | H=2D, 1 oculta; zscore+BatchNorm+ReLU+sigmoide+MSE | código oficial | Rede rasa; saída sigmoide dá pseudo-prob. L∈[0,1]; treino por regressão MSE |
| b4 | Treino da rede | Específico | adam lr=1e-3, 100 épocas, batch 32, sem early-stop, rede NOVA/Glorot por geração | código oficial (divergência em bloco vs paper, mantida) | Pesos reinicializados a cada geração → rede do zero sempre (paper: LM, T=500) |
| b4 | tr (razão de seleção) | Específico | 0,5·min{rr, 1−rr} | código oficial | Limiar adaptativo derivado de rr (proporção de positivos); ajusta a fração aceita/ciclo |
| b4 | Gate de seleção | Específico | 4 ramos, 0,4 hardcoded; L>0,9 avalia / L<0,1 descarta | código oficial | A classe decide *quem gasta um FE real*: L>0,9 → avaliação real, L<0,1 → descarte |
| b4 | div (diversidade) | Específico | ceil(√k)=3 | código oficial | 3 subgrupos p/ diversificar a escolha dos infills entre aprovados |
> **Notas.** D20: N=50 é o único override load-bearing (em CSEA N limita treino e gerações). D30: treino no ARQUIVO INTEIRO (ARTIGO — capar handicaparia o classificador); patch do init min(11D−1,109)→11D−1. Divergência em bloco mantida no CÓDIGO: paper treina com Levenberg-Marquardt/T=500; o código usa adam + rede nova por geração. Balde C SUBSTITUI os operadores nativos {ηc=15, ηm=5} do CSEA por SBX 1/20 + PM 1/D/20.
| b4 CSEA | K=6; gmax=3000 (⟦v2.2⟧ conta só os lotes INTERNOS de 12 → i termina em 3000 exato; overshoot é de FE: lote final ≤12 sem truncagem → FE ≤ maxFE+11); init `min(11D−1,109)` → **patch p/ 11D−1 (fiel ao paper)**; cap treino = `Problem.N`; ⟦v2.2⟧ rede: **H=2D**, 1 oculta, zscore+**BatchNorm+ReLU**+sigmoide+regressionLayer (**MSE**), **adam** lr=1e-3, 100 épocas, batch 32, sem early-stop, **rede NOVA por geração** (Glorot); **tr=0.5·min{rr,1−rr}** (CSEA.m:61); operadores internos **{1,15,1,5}** (ηc=15, ηm=5) *[descrição do código SHIPPED; na EXECUÇÃO o Balde C os SUBSTITUI por {1,20,1,20} — §6.4 nota D20/D30; ratificado pelo autor no R1-b4]*; gate de 4 ramos com **0.4 hardcoded**; p0/p1 = **MAE contínuos** por classe; rótulo 1 ⟺ não-estritamente-pior que TODAS as refs; div=ceil(√k)=3; 1ª ref = min d2-PBI à diagonal | K=6 ✓; ⚠ **N do paper = 50**; ⚠ paper treina no arquivo INTEIRO [DEF-B4.6]; ⚠ treinador do paper = LM/T=500/Δw<0,001/sigmoide dupla/U[0,1]/warm-start — **o código substitui tudo** (adam/rede nova — divergência em bloco, registrada); L>0.9/L<0.1 ✓; **Q=∅ é design** ✓ [B4.4]; ⟦v2.2⟧ M=2: W₂=(−1, 1,22e−16) — quase-degenerada (grade radial ~1-D quantizada), com risco raro de crash no RadarGrid |

---

### I.3 · b4 CSEA (PlatEMO 4.15)
**Fluxo real:** K=6 soluções de referência por seleção radial → rotula o arquivo (cat. II = domina ≥1 referência) → treina FNN (trainNetwork) → mede (p1,p2) por classe no teste 25% → regime R1/R2/R3 decide COMO usar as predições (gate L>0.9/L<0.1; R2 → lote vazio, geração sem FE real — comportamento de projeto) → avalia os aprovados. **Integração:** patch init (CSEA.m:29 — p/ 11D−1, fiel ao paper); **forçar `ExecutionEnvironment='cpu'`** (código = `'auto'` em CSEA.m:47 — N.2; 'auto' disputaria GPU entre workers e quebraria a reprodutibilidade por semente); patch LHS (CSEA.m:30). **Export:** classificador — logar L∈(0,1) dos selecionados + (p1,p2,rr,tr) por geração (DEF-C1). **Divergências:** treinador SGD-família × Levenberg–Marquardt do paper; cap de treino Problem.N × arquivo inteiro; N=100 × 50; H/tr: conflitos internos do paper (código arbitra); M=2 degenera a projeção radial (flag de análise §15.1).

---

### L.3 · b4 CSEA — patches: init (CSEA.m:29→11D−1), CPU (:47), DoE (:30–31; initFcn NÃO alcança o CSEA). N=50 do paper via `Problem.N` explícito [decisão B4.2]. Bug latente: `randperm(length(Next))` no ramo (b) pode exceder linhas se D>|Pop|+6 (SAS.m:30); stall 0-FE sem limite (monitorar via outputFcn); NaN em p0/p1 (classe ausente no teste) → cai no else (1 aleatório) — sem crash. RefSelect pula a normalização INTEIRA se algum objetivo tiver range≤1e-6 (vetorial). **RNG/geração:** 2 randperm (partição) + trainNetwork (Glorot + shuffle por época — maior consumidor) + OperatorGA inicial + 250×OperatorGA(12) nos ramos a/c + randperm/randi (b/d). **FE:** init + 0–12/geração (ramos); FE final ∈ [maxFE, maxFE+11]. Toolboxes: DLT (7 funções) + Statistics (pdist2, tabulate).

---

### M.3 · b4 CSEA
- **Racional das escolhas:** classificar candidato-vs-referências usa **1 único surrogate independente de M** (vs M Krigings) e a relação candidato-vs-referência é "mais previsível"; pop=50 minúscula para caber mais gerações sob 300 FEs; tr distante de 0,5 (=0,5·min{rr,1−rr}) com rescaling para **decisão confiável sob desbalanceamento de classe**.
- **Ablação/sensibilidade (importante — contraintuitivo):** no estudo de H, **H=2d vence em M=3 e M=5** (mais capacidade); 0,5d só vence em M=10 e é o default **conservador anti-overfitting** dado o treino 11d−1 — mas a comparação principal do paper usa H=10(=d). Nosso código usa **H=2D** (Anexo L.3) → *estamos na configuração que o próprio estudo de ablação aponta como a melhor para M=3* — registrar como escolha fundamentada, não acidente. K: DTLZ5 prefere 4, DTLZ7 prefere 8, DTLZ2 é U-shaped com fundo em 6 → K=6 é compromisso robusto. A FNN fica **mais acurada com M crescente** (encaixe favorável a many-objective).
- **Modo de falha:** DTLZ7 (front descontínuo) — CSEA perde (classificação+projeção radial sofre com diversidade em fronts descontínuos); forte em multimodais DTLZ1/3 e degenerada DTLZ5.

---

**Âncora de fidelidade (Anexo J):**

| b4 CSEA | DTLZ1–7 × M∈{3,4,6,8,10} (d=10); ZDT1 d=10/20/30 | 11d−1 LHS | 300 (ZDT1: 300/600/900) | 30 (§IV) vs 20 (Tab. III) — inconsistência | IGD (~5000 ref); Wilcoxon 0.05 | DTLZ2 M=3: 1,89e-1 (1,13e-2); DTLZ5 M=10: 1,00e-2; MOEA/D-EGO vence DTLZ7 M=3 (2,30e-1 × 1,39e0) |
