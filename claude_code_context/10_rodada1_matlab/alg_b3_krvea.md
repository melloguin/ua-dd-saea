# b3 K-RVEA (PlatEMO 4.15)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Decisões específicas:** Guard do crash latente (`UpdataArchive:61`) + **DoE livre de duplicatas** (1º fit sem dedup).

---

- [ ] **b3 K-RVEA** *(I.2, L.2, N.3)* — patch DoE (`KRVEA.m:33`); **DoE livre de duplicatas** (1º fit sem dedup); **crash latente** `UpdataArchive.m:61` (não filtra zeros de `Next` — [IMPL] guard); overshoot nativo ≤+4 (:80) → o hard-stop corta exato. σ por objetivo `sqrt(max(MSE_j,0))`. Instrumentação: |A1|, u efetivo, NumV1/NumV2/Flag/ramo (KrigingSelect:15/:42/:50) + `index` (:64, patch 1 linha). kmeans/pdist2 (Statistics).

---

| b3 | N (vetores de referência) | Compartilhado (b1,b3,e7) | 100 (M=2 → 100; M=3 → 91) | D20 (default; paper não prescreve N p/ M=2) | Tamanho da pop / nº de vetores; também escala δ (=0,05·N_vetores) |
| b3 | wmax | Compartilhado (b3,e7) | 20 | código oficial + paper ✓ | Nº de gerações do RVEA sobre o surrogate entre atualizações do modelo (comprimento do ciclo) |
| b3 | u (infills-alvo) | Específico | 5, com min{u,\|Vaᵃ\|} | paper ✓ + código | Nº de soluções por ciclo p/ avaliação real via k-means (u clusters); clusters vazios descartados → u efetivo ≤ 5 |
| b3 | δ (limiar do switch) | Específico | 0,05·N_vetores (M=2→5; M=3→4,55) | código oficial | Flag=NumV2−NumV1 ≤ δ → seleção por APD (arquivo real × pop predita); Flag>δ → por incerteza (M=3: sse Flag≥5) |
| b3 | Métrica de incerteza | Específico | variância média (MSE), SEM √ | código oficial | Ranqueia candidatos pela média das variâncias preditivas; escolhe os de maior incerteza |
| b3 | Modelo DACE | Compartilhado (b1,b3) | regpoly1 + corrgauss | código oficial; corrgauss ✓; D30 | Kriging DACE (tendência 1ª ordem + kernel gaussiano), 1 por objetivo |
| b3 | θ0 (init) + warm-θ | Específico | 5 (warm-θ entre ciclos) | código oficial; D30 | Ponto inicial da MLE; ciclos seguintes reusam θ (mais barato) |
| b3 | Bounds de θ | Específico | [1e-5, 100] | código oficial | Caixa de busca da MLE por θ |
| b3 | θ_APD do infill | Específico | (21/20)^α | código oficial | Fator de penalização angular (APD); cresce como 1,05^α, balanceando convergência×diversidade no ciclo |
> **Notas.** Paper corrobora wmax=20, u=5 com min{u,\|Vaᵃ\|}, corrgauss; N p/ M=2 não é prescrito → 100 (D20). u é efetivamente variável (clusters vazios). Incerteza como variância média sem raiz é do código. regpoly1/warm-θ ficam no código (D30). Balde C: b3 (EA) usa SBX 1/20 + PM 1/D/20. *(wmax=20 coincide com e7 por serem defaults independentes, não acoplamento.)*
| b3 K-RVEA | `wmax`=20; u=5 alvo (clusters vazios descartados → u efetivo variável); δ=0.05·N_vetores; ⟦v2.2⟧ N=100 → 100 vetores (M=2) / **91** (M=3 → δ=4,55; Flag inteiro ⇒ incerteza sse Flag≥5); switch: **Flag=NumV2−NumV1 (com sinal) ≤ δ → APD** (arquivo real × pop predita); critério de incerteza = média das **variâncias** (MSE), sem sqrt; DACE ⟦v2.2⟧ **regpoly1**+corrgauss, θ0=5, [1e-5,100], **warm-θ** entre ciclos; θ_APD do infill = (21/20)^α | wmax=20 ✓, u=5 c/ min{u,\|Vaᵃ\|} ✓; corrgauss ✓; ⟦v2.2⟧ **B3.5 fechada**: A1 = `unique` por decisão (reordena lex!) c/ teto NI e **mu fixo** (A1 encolhe p/ NI−5+u se u<5); ramo (a) tem **bug de índice** vetores→soluções (alcançável só D≤9); ramo (b) ≈ Alg. 4 do paper; ⚠ **sem "1º update sempre APD" no código**; pop interna reinicia do arquivo a cada ciclo; **N p/ M=2 não é prescrito no paper** |

---

### I.2 · b3 K-RVEA (PlatEMO 4.15)
**Fluxo real:** ciclo = wmax=20 gerações no surrogate (RVEA com vetores adaptativos) → seleção de ≤5 infills por clustering dos vetores ativos: critério APD (convergência) se ΔVf≤δ, senão máx **MSE̅** (média das VARIÂNCIAS preditivas, **sem raiz** — código oficial, `KrigingSelect.m:61`) ⟦v5.2.1 — corrigido: dizia 'máx σ̄'⟧; clusters vazios são descartados (u efetivo < 5). Retreina 1 DACE/objetivo. **Integração:** patch de DoE **classe D94** (`KRVEA.m:33` — o par gera+re-escala substituído JUNTO pela injeção do X0 nativo) ⟦v5.2.1 — a D94 não estava citada⟧; N→nº de vetores + δ=0.05N. **σ exportável:** por objetivo `sqrt(max(MSE_j,0))` (B3.2 ► — a raiz é unidade de **EXPORT apenas**; o critério interno **NÃO** usa raiz: média das VARIÂNCIAS ⟦v5.2.1 — corrigido⟧). **Divergências/checks:** gestão do arquivo de treino vs Alg. 4 do paper (B3.5); falha dura do dacefit (sites duplicados/"Bad parameter region" — DEF-A8); overshoot até +4 FEs (DEF-A2).

---

### L.2 · b3 K-RVEA — logar |A1| por ciclo (encolhe p/ NI−5+u quando u<5) + u efetivo + NumV1/NumV2/Flag/ramo (KrigingSelect:15/:42/:50) + exportar `index` (:64, patch 1 linha). Pop interna reinicia do arquivo (KRVEA.m:53); ordem lex do `unique` define o pareamento do OperatorGA (posicional). **DoE injetado DEVE ser livre de duplicatas** (1º fit sem dedup). Predictor: MSE por ponto só em chamada 1-a-1 (como o KRVEA faz). **RNG:** LHS (some c/ patch); OperatorGA; kmeans (k-means++) em KrigingSelect:19 e UpdataArchive:37/:50; randi por cluster (UpdataArchive:41/:54). **FE:** KRVEA.m:34 (init) e :80 (≤5/ciclo; overshoot ≤+4 na :80). D=2: 21 pontos × 100 vetores — pressão fraca no início (comportamento, não bug).

---

### M.2 · b3 K-RVEA
- **Racional das escolhas:** wmax fixo é **simplificação deliberada** — "a rigorous guideline for adapting the frequency still lacks; for simplicity we adopt a prefixed frequency" (§III-B); os vetores **fixos Vf são termômetro de diversidade justamente porque os adaptativos Va se redistribuem** e escondem a perda de cobertura — contar Vf inativos entre updates é o único diagnóstico estável (é o coração do switch APD×incerteza); δ escala com N para acompanhar a granularidade dos vetores.
- **Ablação/sensibilidade (informa manter-default vs variar):** δ↑ → menos uso de incerteza → diversidade e HV pioram; **K-RVEA é relativamente INSENSÍVEL a wmax** (§V) — a cadência não é crítica aqui (ao contrário de δ); **u=5 é problema-específico** (depende de multimodalidade), sem valor universal. Payoff empírico do arquivo fixo |A1|=NI: **tempo de treino CONSTANTE** ao longo do run (Fig. 9) — enquanto SMS-EGO/MOEA-D-EGO crescem — o que sustenta a viabilidade de rodá-lo em orçamento apertado.
- **Garantia/pressuposto + modos de falha:** "**there is no solid theory for guiding when to update the surrogates**" — cadência puramente empírica. DTLZ1/3 (multimodais) convergem devagar (vetores forçam diversidade sobre convergência); DTLZ5/6 (front degenerado) deixam ~70% dos vetores vazios → lentidão. **Contraste natural para a §15**: onde K-RVEA é fraco (multimodal/degenerado), CSEA é forte — EA+GP vs classificação.

---

**Âncora de fidelidade (Anexo J):**

| b3 K-RVEA | DTLZ1–7 (n=10; M=3,4,6,8,10) | 109 (11n−1) | 300 FEs | 10 (§IV-A) vs 25 (§IV-B) — inconsistência do paper | IGD; Wilcoxon 0.05 | DTLZ2 M=3: 0,155 (RVEA 0,288; ParEGO 0,191); DTLZ7 M=3: 0,111; PERDE DTLZ5 M=3 p/ MOEA/D-EGO (0,046) |
