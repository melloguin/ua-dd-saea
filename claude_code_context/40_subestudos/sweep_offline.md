# Sub-estudo SWEEP offline (tamanho × distribuição) — §11.5 [D38/D51/D67]

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**D67 (MVNS):** amostrar em **[0,1]^D**; **μ=0,3·𝟙 FIXO** (viés consistente; semente varia só as amostras); **Σ=diag(0,1)**; clip aos bounds; mapear a nativo. **Roster:** b5r+b5m+e103 (small/medium) e c311 (small/medium/big) — D56. `run_id`: `sweep-{tier}-{dist}` (D55).

---

## 11.5 — Sweep de tamanho de amostra (offline) — [DECIDIDO: sub-estudo focado]
Sub-estudo (não a bateria inteira) que **varia o tamanho do dataset** para mostrar como o desempenho muda com a quantidade de dados — e onde o **c311/treed-GP** justifica sua existência.

**[v5.2 — D90] Datasets do sweep = artefatos pela mesma convenção do §7:** o tier e a distribuição entram no nome e na derivação (`ds_{problema}_{semente}_{tier}_{dist}.parquet`); MVNS (D67) materializada igual; tier `big` usa LHS simples (D87).

**Tiers:**
- **Small = `31D−1`** (reaproveita os runs da comparação cross-regime; feasible para todos).
- **Medium ≈ 2000** (GP padrão ainda treina; acima de `31D−1` mesmo nos D altos).
- **Big ≈ 30000–50000** — **c311 + piso-treed-GP apenas**. O GP padrão bate na parede **O(n³)** (matriz 50k×50k inviável em memória/tempo) → e103/b5 **não rodam** nesse tier por impossibilidade computacional, não por qualidade. **Este é o achado de escalabilidade**, não um grid uniforme: *"quando os dados crescem, o GP padrão para de escalar; o treed-GP continua"*.

**~5 problemas do sweep [DECIDIDO]** (cobrindo D de 10 a 30 ⟦DI-35.3⟧ e landscapes fáceis→difíceis):

| Problema | D | Papel no sweep |
|---|---|---|
| MMF16_20 | 20 | ⟦DI-35.3⟧ substitui o MMF1 (o "controle D=2" era INEXECUTÁVEL: duplicata-clip no mvns e GP singular em medium/big — paredes numéricas de D=2, medidas no T7); mantém a família MMF (multimodal) no sweep |
| ZDT4 | 10 | Multimodalidade extrema → tamanho da amostra deve importar muito |
| DTLZ2 | 12 | Landscape suave/côncava → caso bem-comportado (3 obj) |
| WFG9 | 22 | Não-separável + enganoso → mais difícil de aproximar |
| ZDT1 | 30 | **Teto de dimensão** → onde o big-data e o treed-GP mostram vantagem |

**Custo controlado pelo nº de problemas (~5), não pelos tiers.** Offline é rápido no small/medium (surrogate treinado uma vez, sem retreino); lento só no big (treino único O(n³)).

**[✔ D51/v3.0.35 — DEF-O4] Eixo de DISTRIBUIÇÃO do dataset: LHS × MVNS (robustez a dado enviesado).** Além de variar o TAMANHO, o sweep varia a DISTRIBUIÇÃO da amostragem do dataset inicial: **LHS** (uniforme, o default do §9) **e MVNS** (normal multivariada enviesada, var=0,1) — replicando o desenho fatorial `tamanho × distribuição` dos nossos próprios **b5/c311**. **Só muda a amostragem** do dataset; o resto do pipeline é idêntico. **Motivo:** no offline real o dataset é fixo e frequentemente **enviesado** — o MVNS mede quão robusto cada método é a isso (achado citável do c311: sob MVNS o sparse-GP supera o treed-GP em RMSE). **Escopo contido:** só no sweep de ~5 problemas (a **campanha offline dos 26 permanece em LHS**) → o custo do sweep ~dobra, o que é modesto (o sweep já é o estudo enxuto). Registrar `dataset_dist ∈ {LHS, MVNS}` no manifesto de análise. *(Rejeitados: MVNS na campanha offline inteira — dobraria todo o offline por ganho marginal; e não-incluir — abriria mão de um eixo de robustez barato e central em b5/c311.)*

---
---

# PARTE V-B — SUB-ESTUDO LARGE-BATCH [NOVO v2.0 — ESCOPO DECIDIDO; parâmetros em definição]
