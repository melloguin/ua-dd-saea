# F5.5 — ADENDO: a régua por família e a ablação do tier big

## A. A régua por FAMÍLIA de problema (a variável que explica melhor que D)

| família | problemas | D (faixa) | SA batem o melhor piso | % | conclusivas |
|---|---:|---|---|---:|---:|
| BBOB | 7 | 10–10 | 59/90 | **66%** | 25 |
| ZDT | 4 | 10–30 | 30/48 | **62%** | 20 |
| MMF | 4 | 2–20 | 31/50 | **62%** | 0 |
| DTLZ | 5 | 7–22 | 20/59 | **34%** | 8 |
| WFG | 5 | 22–22 | 15/58 | **26%** | 1 |

**Leitura**: a fração de SA-MOEAs que batem o melhor piso varia mais por FAMÍLIA que por dimensão. A afirmação "a vantagem do surrogate cresce com D" (construída na R1 sobre 3 problemas: MMF1 D=2, DTLZ2 D=12, ZDT1 D=30) NÃO se sustenta no grid completo de 25 problemas — o que separa é a natureza do problema (multimodalidade/deceptividade × suavidade), não o número de variáveis. Base: 1 semente — descritivo, não teste (M13).


## B. Ablação do tier BIG pela camada ⑦ — `c311` × `treed_media`

> `treed_media` = "o c311 SEM os GPs locais" (T8/DI-35.2): árvore pura + RVEA sobre a média das folhas. A pergunta: **quanto os GPs locais acrescentam em N=50.000?** Endpoint = ⑦ (ND final avaliado na função real).

| dist | problema | IGD+⑦ c311 | fantasia c311 | IGD+⑦ treed | fantasia treed | GPs ajudam? |
|---|---|---:|---:|---:|---:|---|
| lhs | DTLZ2 | 0.02547 | 0.962 | 0.1354 | 0.581 | ✔ sim |
| lhs | MMF16_20 | 0.02512 | 0.952 | 0.03923 | 0.752 | ✔ sim |
| lhs | WFG9 | 0.2324 | 0.980 | 0.3409 | 0.348 | ✔ sim |
| lhs | ZDT1 | 0.2174 | 0.560 | 2.353 | 0.220 | ✔ sim |
| lhs | ZDT4 | 67.39 | 0.080 | 62.25 | 0.194 | ✘ não |
| mvns | DTLZ2 | 0.03015 | 0.905 | 0.3842 | 0.363 | ✔ sim |
| mvns | MMF16_20 | — | — | 0.0515 | 0.676 | — (célula excluída) |
| mvns | WFG9 | 0.3884 | 0.020 | 0.2915 | 0.234 | ✘ não |
| mvns | ZDT1 | 0.0445 | 0.653 | 1.931 | 0.208 | ✔ sim |
| mvns | ZDT4 | 75.42 | 0.140 | 107.5 | 0.216 | ✔ sim |

**Placar**: os GPs locais melhoraram o endpoint em **7** células big e pioraram em **2** (de 9 comparáveis). Custo: o c311-big roda ~100× mais caro que o treed_media (6-14 s/célula) — o insumo de custo×benefício da ablação.

