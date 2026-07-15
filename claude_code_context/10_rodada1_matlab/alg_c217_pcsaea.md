# c217 PC-SAEA (PlatEMO 4.15) — caso-modelo da auditoria

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Decisões específicas:** Patch = **2 guardas** (D17); N=50; **referência de fidelidade (validação MANUAL do autor — D97): IGD≈6,9212e-2, faixa-guia ±3σ=±2,335e-2** (não é limiar automático; o antigo ±1σ reprovaria 1/3 das corretas); log `.txt` por geração (§17.2.1).

---

- [ ] **c217 PC-SAEA** *(I.5, L.5, N.3)* — **o caso-modelo da auditoria.** Patch da correção = **2 guardas** (`SAS:21` → `error1>delta`; `SAS:39` → `error2>delta`; corpos intactos — D17); **regime-NaN → aleatório** (L6); **N=50** + init→11D−1 + **fix `min(Problem.N,length(Arc))`** (PCS:55); **clip do lote ao saldo** antes de PCS:53 [IMPL]; corte pós-hoc `Arc(1:31D−1)` exato (append-only). NaN novo em `CalFitnessPC.m:17` (objetivo constante); D≡0.5 nasce em :54. **Log de estados por geração** (p+/p−/δ/contradições/estado/motivo/lote — §17.2.1). **Referência da prova dupla (validação MANUAL do autor — D97): DTLZ2 m=3 d=15 → IGD ≈ 6,9212e-2, faixa-guia ±3σ = ±2,335e-2** (o `7,78e-3` é **1σ** do paper; ±3σ por D81, pois ±1σ numa única semente reprovaria ~1/3 das implementações CORRETAS; *não é limiar automático*) (Anexo J). D=2: Error ∈ {0, 0.5, 1} (granularidade intrínseca — registrar).

---

| c217 | N (pop / lote de infill) | Global-override | 50 | D20/D17 (paper) | Governa o lote de infill; dele derivam split (13/12), Pmid (13) e o batch (=6) das gerações ≥2 |
| c217 | δ (pré-seleção) | Específico | 0,8 | código oficial; paper ✓ | Controla a fração de candidatos aceitos como promissores pelo classificador |
| c217 | Gmax (gerações internas) | Específico | 3000 | código oficial | Teto de gerações; deriva wmax=⌊3000/lnum⌋ |
| c217 | Spread da PNN (newpnn) | Específico | 0,1925 | CÓDIGO documentado (K.3; paper 0,2) | Largura das gaussianas radiais da PNN (determinístico); 0,1925 estreita levemente vs 0,2 |
| c217 | DoE inicial | Global-override | max(11D−1, N) | código oficial (override do DoE) | Garante ≥50 amostras iniciais quando N>11D−1 (D≤4) |
| c217 | Gate de confiança | Específico | ±0,95 | código oficial; paper ✓ | Janela ±0,95 sobre a saída do classificador que decide quem vai à avaliação real |
| c217 | Split assimétrico | Específico | best=⌈N/4⌉ / worst=⌈N/2⌉−⌈N/4⌉ (13/12) | código oficial | Particiona o treino em melhores/piores p/ formar pares rotulados |
| c217 | Pmid (refs na fronteira) | Específico | 13 | código oficial | Pontos de referência na fronteira do corte p/ balancear a seleção |
| c217 | Operadores GA (SBX/PM) | Específico | η_c=15 / η_m=5 | CÓDIGO documentado (K.3; ≠ Balde C 20/20) | Índices próprios do código; η menores → filhos/mutações mais dispersos |
| c217 | Regra tripla (estados 1/2/3) | Específico | fiação CORRIGIDA ao paper | fidelidade → ARTIGO (D17) | Liga condição↔ação dos 3 regimes de uso da incerteza; patch de 2 guardas desfaz o comportamento anti-greedy do código; regime-NaN → ramo aleatório |
> **Notas.** D17 é central: o código religa ação↔condição ao contrário (anti-greedy nos regimes confiáveis); como a tese é sobre USO da incerteza, corrigimos a fiação ao paper (ARTIGO) com 2 guardas. `min(N,length(Arc))` evita crash D≤4 (guarda). Fidelidade K.3 mantida no CÓDIGO: spread 0,1925, pares todos×todos, operadores η 15/5. Balde C não se aplica (usa η próprios).
| c217 PC-SAEA | δ=0.8; Gmax=3000 (→ wmax=floor(3000/lnum) internas); PNN `newpnn` spread=0.1925 (⟦v2.2⟧ **determinístico** — sem RNG); init `max(11D−1, N)`; batch = ⟦v2.2⟧ **contagem do gate quando 0<c≤floor(lnum/2)**, senão fallback floor(lnum/2) (ger.1 ≈1,375D; ger.≥2 = 6 se N=50), estado 3 → 1; gate ±0.95; ⟦v2.2⟧ split assimétrico best=⌈N/4⌉/worst=⌈N/2⌉−⌈N/4⌉ (13/12 p/ N=50); Pmid = 13 refs na FRONTEIRA do corte; rótulos dos pares pela coluna Fitness contínua; \|TestOut\|=6 (N=50) → granularidade 1/6 | δ=0.8 ✓, gate ✓; ✔ **DECIDIDO v3.0.2 (D17): CORRIGIR a fiação** [DEF-B5.1] — patch de 2 guardas religando condição→ação ao paper (correção fiel em I.5); **N=50** [DEF-B5.2] + patch init→11D−1; **regime-NaN → ramo aleatório** (estado 3, DEF-L6 resolvida); fix obrigatório `min(N,length(Arc))` em PCSAEA:55 (crash em D≤4); **log `.txt` de auditoria da regra tripla por geração** (§17.2). ⚠ **AINDA ABERTO [DEF-B5.6]** (guarda-chuva de fidelidade, K.3): spread PNN 0.1925×0.2, pares todos×todos × N/4-best×N/4-worst, operadores η 15/5 × 20/20, diversidade degenerada D≡0.5, SDE inerte, sem dedup de infill |

---

### I.5 · c217 PC-SAEA (PlatEMO 4.15) — ⚠ o caso crítico [DEF-B5.1/B5.2 DECIDIDAS na D17/v3.0.2: corrigir a fiação + N=50]
**Fluxo real (como shipped):** PNN par-a-par (`newpnn`, entrada [x;y] concatenada, spread 0.1925) treinado a cada geração com pares todos×todos do conjunto best/worst (SDE-fitness) → validação vs referências Pmid → Error1 (taxa de ACERTO, apesar do nome) e Error2 (taxa de inversão) → **ramos: `Error1<1−δ` → maximiza Label; `Error2<1−δ` → minimiza; else aleatório** → gate ±0.95 → batch floor(lnum/2). **O veredito (leitura verbatim paper Alg. 4–6 + código master):** paper manda *acurado→maximizar score, invertido→minimizar*; o código, nos dois regimes confiáveis, seleciona os preditos-PIORES (anti-greedy sistemático). Correção fiel mínima [ADOTADA — D17/v3.0.2]: `if Error1>δ → maximiza; elseif Error2>δ → minimiza; else aleatório` (trocar só os corpos max↔min não reproduz o paper quando há contradições — elas + o **regime-NaN** devem cair no ramo aleatório). **Instrumentação exigida (D17):** cada avaliação da regra grava no log `.txt` (§17.2) p+/p−/δ/nº-contradições/estado-escolhido/motivo/lote — auditar que a fiação corrigida dispara os estados como o paper prevê; **prova** = check de reprodução DTLZ2 m=3 d=15 (IGD≈6,92e-2, §20). **Integração:** N=50 (paper) [DEF-B5.2] + patch init→11D−1 reproduz init E batch≤6 p/ D≥5 + fix `min(N,length(Arc))` (PCSAEA:55); patch LHS (PCSAEA.m:28). **Export:** score ternário {−1,0,+1} + Error1/Error2 por geração (C1). **Demais divergências:** §6.5 (σ, pares, operadores, diversidade degenerada D≡0.5).

---

### L.5 · c217 PC-SAEA — **patch da correção = 2 GUARDAS** (SAS:21 `error1<1−delta`→`error1>delta`; SAS:39 idem c/ error2; corpos intactos; nada mais consome Error1/2). **Fix acoplado obrigatório** (com init 11D−1): PCS:55 → `EnvironmentalSelection(Arc,min(Problem.N,length(Arc)))`. Clip do lote ao saldo antes de PCS:53 [IMPL]. Arc é append-only cronológico → corte pós-hoc `Arc(1:31D−1)` exato. Regime-NaN: logar `sum(TestPre==1.5)`, Error1/2 e estado por geração (instrumentação PCS:48–51 + retorno extra do SAS). **RNG:** LHS 1×; DP: 2×randperm (ÚNICA estocasticidade do pipeline de modelo — newpnn/sim/ind2vec determinísticos); SAS: OperatorGA (1+wmax vezes) + randperm/iteração interna + randi no estado 3. **FE:** PCS:29 (init) e :53 (lote); sem cap nativo. D=30/N=50: ger.1 batch 41, depois 6 (~95 gerações); D=2 patch+fix: teste=1+1 → Error∈{0, 0.5, 1} (granularidade intrínseca — registrar).

---

### M.4 · c217 PC-SAEA
- **Racional dos 3 estados (o mais importante — reenquadra a DEF-B5.1):** o pareamento par-a-par embute um **teste de consistência** — o modelo deveria rotular ⟨x,y⟩ e ⟨y,x⟩ de forma OPOSTA. p⁺ = consistente-e-certo; **p⁻ = consistente-e-invertido = erro SISTEMÁTICO, recuperável invertendo o uso do modelo**; rótulos iguais = contradição = erro ALEATÓRIO, perdido → ignorar. A distinção inverter-vs-ignorar é exatamente "erro sistemático (recuperável) vs aleatório (inútil)" — é isto que justifica 3 estados e não 2, e o piso δ>0,5 vem do acaso do binário (interpretabilidade que um regressor não teria). **A inversão em state 2 é FEATURE deliberada** (Alg. 5 explícito; precedente creditado ao CSEA [30]) e a Tabela 8 valida o switch dinâmico. ⚠ Isso convive com o achado de código (v2.1/v2.2): os RAMOS do PlatEMO estão anexados às CONDIÇÕES trocadas — o *mecanismo* é do paper, mas a *ligação condição→ação* no 4.15 inverte. A decisão de fidelidade (rodar as-shipped vs corrigir a ligação) permanece; o racional agora está documentado.
- **Ablação:** parear N/4×N/4 vence N/2 e N/3 **apesar de menos amostras** (fronteira mais nítida; acc 0,604 vs 0,585 vs 0,571) — sustenta o split do código. **Lacuna honesta:** o paper NÃO reporta a frequência com que os states 2/3 disparam num run — não sabemos, a priori, quão frequente é o ramo invertido (relevante para dimensionar o impacto da troca).

---

**Âncora de fidelidade (Anexo J):**

| c217 PC-SAEA | DTLZ1–7, WFG1–9, MaF1–5 (d=15–21; m=2,3) + CSI/WRM/GAA | 11d−1 LHS | 2000 FEs | 30 | IGD (10k ref) / HV reais; Wilcoxon 0.05 | **Piloto do veredito B5.1: DTLZ2 m=3 d=15 IGD=6,9212e-2 (7,78e-3)**; DTLZ1 m=2: 2,9490e1; acurácia média PNN 0,604 |
