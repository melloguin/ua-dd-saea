# Piso offline — MOEA/D-média (DESDEO mode 12, GP-média) [D77]

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**D77 (a casa canônica):** roda no **MESMO motor do b5** — `MOEA_D` (mode 12) do repo DESDEO — sobre **GP-média** (SurrogateKriging só-μ, sem σ) = **a ablação exata do b5** (DEF-E3: o contraste piso-vs-b5 mede exatamente o valor de usar σ). A antiga listagem 'built-in PlatEMO / Rodada 1' está MORTA. Python, Rodada 3, cartão R3 próprio. N interno = 100 (D65 não se aplica: sem pressão de orçamento). ND final sem cap (D68).

---

### 3.4 Offline — 1 piso [DECIDIDO: MOEA/D sobre surrogate-média]

No offline, MOEA puro é **impossível** (não há função real para avaliar durante a busca). O piso offline é, portanto, **um MOEA/D otimizando sobre um surrogate treinado uma vez no dataset, usando só a média (ignorando a incerteza)**.
- **Por que MOEA/D:** é a **ablação exata do b5** — Prob-MOEA/D menos a seleção probabilística → mesmo motor, mesmo surrogate, muda **só** o uso de σ. É a atribuição mais cirúrgica possível ("usar σ vs só a média"). Também casa com a decomposição de 2/3 dos offline viáveis.
- **Assimetria de regime (por que não é MOEA puro):** no online, "não fazer a coisa inteligente" = "não ter surrogate"; no offline, o surrogate é obrigatório (única fonte de informação), então "não fazer a coisa inteligente" = "ter surrogate, mas usar só a média".

---

## 10. Surrogate do piso offline — [DECIDIDO: GP-média]
O piso treina um **GP (Kriging)** no dataset e otimiza sobre a **média** — **mesma família dos 3 viáveis** (todos GP). Isola *uma* variável (usar σ vs só a média); RBF/NN introduziria uma segunda diferença (família do modelo) e poluiria o isolamento.
- **Ajuste no tier big-data (~50k):** o GP padrão não treina (parede O(n³)); **só nesse tier** o piso usa **treed-GP-média**, mantendo o conceito "GP-média" e a presença do piso em todos os tiers.

---

## 11. Orçamento interno do MOEA + avaliação final — [DECIDIDO]

**Orçamento interno** (MOEA rodando sobre o surrogate — avaliações no modelo, de graça): **default do autor** para cada algoritmo, em suas próprias unidades (não equiparado — cada um converge no seu ritmo):

| Algoritmo | Motor interno | Orçamento interno (default do código, corroborado no paper — [CORRIGIDO v2.1]) |
|---|---|---|
| e103 (IBEA-MS) | IBEA | **10.000 avaliações-surrogate** = 100 gerações nominais × pop 100 (paper §IV-4; o código executa 99 — off-by-one documentado) |
| b5 (Prob-MOEA/D & Prob-RVEA) | RVEA / MOEA/D | **40.000 avaliações-surrogate** (paper FE_max ✓) + S=1000 amostras MC/indivíduo |
| c311 (TGPR-MO) | RVEA | **Construção** (= treino do surrogate, parte do método): `Imax = N/(10D)` iterações (float → executa ⌈Imax⌉) × 50 gerações, com early-stop **[re-lido v2.2]**: para quando o nº de soluções em folhas SEM GP não cresce por 2 iterações (mínimo de 6 iterações) — **implementa ≈ o critério do paper** ("todas em folhas com GPR") com persistência; B15.8 rebaixada a nuance + **otimização final**: 10 iterações × 100 ger = 1.000 gerações (vetores adaptados no início de cada iteração). ⚠ O "1.500 ger (50×30)" das versões anteriores estava **errado** — sem base no paper nem no código |
| **Piso** (MOEA/D-média) | MOEA/D | **40.000 avaliações-surrogate** (ancorado no b5) |

**Piso ancorado no b5 (40k):** porque piso-MOEA/D vs Prob-MOEA/D com o **mesmo orçamento interno** é a ablação cirúrgica (única diferença = seleção probabilística).

**Avaliação final [DECIDIDO]:** o algoritmo termina com uma frente aproximada *no surrogate*; **[DI-13.9]** **TODOS os finais** são avaliados na **função verdadeira uma única vez** (`src/problems.py`, pós-hoc, fora do orçamento) e o **não-dominado é filtrado DEPOIS** da avaliação real — filtrar pelo ND-segundo-o-modelo ANTES seria filtrar a realidade pela FANTASIA do modelo, destruindo o que a camada mede (custo extra nulo: funções analíticas). Camada **⑦ `__final.parquet`** (colunas `x*|f*|origem_solution_id|origem_geracao|origem_linha|nd_pos_real` — DI-13.8), escrita/checada por `scripts/final_eval.py`. **Invariante: a ⑦ tem de ser RECONSTITUÍVEL da ③** (gravar a partir da população que a ③ REGISTROU, não da seguinte). O conjunto não-dominado final era avaliado (a única chamada real no offline), e as métricas são computadas sobre ele. Revela o "erro de fantasia" do surrogate (soluções ótimas no modelo, ruins na verdade). Padrão do offline data-driven.

---

| Piso offline (MOEA/D-média) | Motor / orçamento | Específico | MOEA/D sobre GP-média; 40.000 aval-surrogate | Ablação cirúrgica do b5 (mesmo motor/orçamento; única diferença = seleção probabilística) | Treina GP-média no dataset e otimiza sobre a média (treed-GP-média no tier big) |
