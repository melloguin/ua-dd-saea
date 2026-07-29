# F5.5 — Comparativos transversais (semente 42)

> Métrica primária IGD+ (D70). Piso de ruído entre máquinas: HV ≤1,55%, IGD+ até 58,98% (O-18) — diferenças abaixo disso NÃO são conclusivas. Base = 1 semente: tudo aqui é DESCRITIVO, não teste estatístico (isso é M13).

## 1. A RÉGUA — SA-MOEAs vs pisos, por dimensão

| problema | D | melhor piso | IGD+ | melhor SA | IGD+ | SA>piso | conclusivas |
|---|---:|---|---:|---|---:|---:|---:|
| MMF1 | 2 | nsga3 | 0.05701 | e81 | 0.03686 | 9/13 | 0 |
| MMF11_L | 2 | nsga3 | 0.02316 | c238 | 0.01196 | 6/13 | 0 |
| MMF4 | 2 | nsga3 | 0.03771 | c262 | 0.02102 | 10/13 | 0 |
| DTLZ1 | 7 | nsga2 | 45.35 | c122 | 54.67 | 0/13 | 0 |
| BBOB_F1 | 10 | nsga2 | 0.136 | c262 | 0.001456 | 10/13 | 8 |
| BBOB_F17 | 10 | nsga2 | 0.02061 | b4 | 0.01692 | 3/13 | 0 |
| BBOB_F22 | 10 | smsemoa | 0.1591 | c141 | 0.03433 | 7/13 | 4 |
| BBOB_F37 | 10 | smsemoa | 0.2539 | c141 | 0.1024 | 10/13 | 1 |
| BBOB_F49 | 10 | nsga2 | 0.2071 | c141 | 0.08085 | 8/13 | 1 |
| BBOB_F5 | 10 | smsemoa | 0.1193 | c262 | 0.004828 | 10/13 | 6 |
| BBOB_F55 | 10 | nsga2 | 0.6061 | c141 | 0.01312 | 11/12 | 5 |
| ZDT4 | 10 | nsga2 | 43.9 | c262 | 5.928 | 4/13 | 1 |
| ZDT6 | 10 | nsga2 | 6.446 | c262 | 0.002445 | 11/12 | 8 |
| DTLZ2 | 12 | smsemoa | 0.1701 | c262 | 0.03066 | 7/12 | 2 |
| DTLZ3 | 12 | smsemoa | 129.8 | c122 | 187.6 | 0/12 | 0 |
| DTLZ4 | 12 | nsga3 | 0.2824 | c122 | 0.1165 | 4/11 | 0 |
| MMF16_20 | 20 | smsemoa | 0.03162 | c238 | 0.01891 | 6/11 | 0 |
| DTLZ7 | 22 | nsga3 | 1.125 | c141 | 0.0349 | 9/11 | 6 |
| WFG1 | 22 | smsemoa | 0.4954 | b4 | 0.4904 | 1/10 | 0 |
| WFG2 | 22 | nsga2 | 0.1228 | c262 | 0.05653 | 2/12 | 0 |
| WFG4 | 22 | smsemoa | 0.04442 | b4 | 0.06511 | 0/12 | 0 |
| WFG5 | 22 | nsga2 | 0.09308 | c238 | 0.03016 | 8/12 | 1 |
| WFG9 | 22 | nsga3 | 0.09553 | c141 | 0.07508 | 4/12 | 0 |
| ZDT1 | 30 | nsga2 | 0.4441 | c262 | 0.0007028 | 9/12 | 7 |
| ZDT3 | 30 | nsga2 | 0.3443 | b1 | 0.01269 | 6/11 | 4 |

**Agregado por dimensão** (a tese: a vantagem do surrogate cresce com D):

| D | células SA que batem o melhor piso | % |
|---:|---|---:|
| 2 | 25/39 | 64% |
| 7 | 0/13 | 0% |
| 10 | 74/115 | 64% |
| 12 | 11/35 | 31% |
| 20 | 6/11 | 55% |
| 22 | 24/69 | 35% |
| 30 | 15/23 | 65% |

## 2. Ranking global no `main` (rank médio de IGD+ nos 25 problemas)

| # | config | tipo | rank médio | melhor | pior | n |
|---:|---|---|---:|---:|---:|---:|
| 1 | c262 | SA | 3.71 | 1 | 11 | 21 |
| 2 | c122 | SA | 4.72 | 1 | 14 | 25 |
| 3 | c141 | SA | 4.84 | 1 | 14 | 25 |
| 4 | e74 | SA | 6.08 | 2 | 13 | 25 |
| 5 | b3 | SA | 6.36 | 2 | 16 | 25 |
| 6 | c238 | SA | 6.88 | 1 | 16 | 25 |
| 7 | b1 | SA | 7.65 | 1 | 16 | 23 |
| 8 | c154 | SA | 8.91 | 5 | 16 | 11 |
| 9 | nsga2 | piso | 8.92 | 1 | 14 | 25 |
| 10 | smsemoa | piso | 9.08 | 1 | 16 | 25 |
| 11 | e7 | SA | 9.16 | 2 | 15 | 25 |
| 12 | nsga3 | piso | 9.52 | 2 | 14 | 25 |
| 13 | b4 | SA | 9.84 | 1 | 15 | 25 |
| 14 | c217 | SA | 10.44 | 3 | 16 | 25 |
| 15 | e81 | SA | 12.00 | 1 | 17 | 25 |
| 16 | moead | piso | 13.44 | 3 | 16 | 25 |
| 17 | c149 | SA | 14.32 | 8 | 17 | 25 |

## 3. OFFLINE — o endpoint é a ⑦, não a ①

> As métricas da ① EMPATAM por desenho entre os 5 offline (a ① É o mesmo dataset compartilhado; D69 lê a ①). O discriminante é a camada ⑦: o ND final avaliado 1× na função REAL. `fantasia` = fração do "front" do modelo que sobrevive à realidade (`nd_pos_real`/n_final) — quanto MAIOR, menos o modelo se iludiu.

| config | células | fantasia mediana | IGD+⑦ mediano | vitórias IGD+⑦ (vs os outros offline) |
|---|---:|---:|---:|---:|
| e103 | 25 | 0.260 | 0.2251 | 17 |
| b5r | 25 | 0.333 | 0.3814 | 2 |
| b5m | 25 | 0.300 | 0.4868 | 2 |
| c311 | 25 | 0.340 | 0.7211 | 3 |
| moead_media | 25 | 0.340 | 0.5959 | 1 |

## 4. SWEEP — "mais dado → melhor?" (tier) e LHS × MVNS (distribuição)

| config | dist | problema | small | medium | big | melhora small→maior |
|---|---|---|---:|---:|---:|---|
| b5m | lhs | DTLZ2 | 0.4382 | 0.3063 | — | ✔ |
| b5m | lhs | MMF16_20 | 0.05278 | 0.02797 | — | ✔ |
| b5m | lhs | WFG9 | 0.2333 | 0.1844 | — | ✔ |
| b5m | lhs | ZDT1 | 1.984 | 1.739 | — | ✔ |
| b5m | lhs | ZDT4 | 76.27 | 36.38 | — | ✔ |
| b5m | mvns | DTLZ2 | 0.3485 | 0.3503 | — | ✘ |
| b5m | mvns | MMF16_20 | 0.05557 | 0.02895 | — | ✔ |
| b5m | mvns | WFG9 | 0.2109 | 0.1773 | — | ✔ |
| b5m | mvns | ZDT1 | 1.056 | 0.802 | — | ✔ |
| b5m | mvns | ZDT4 | 85.73 | 55.05 | — | ✔ |
| b5r | lhs | DTLZ2 | 0.4382 | 0.3063 | — | ✔ |
| b5r | lhs | MMF16_20 | 0.05278 | 0.02797 | — | ✔ |
| b5r | lhs | WFG9 | 0.2333 | 0.1844 | — | ✔ |
| b5r | lhs | ZDT1 | 1.984 | 1.739 | — | ✔ |
| b5r | lhs | ZDT4 | 76.27 | 36.38 | — | ✔ |
| b5r | mvns | DTLZ2 | 0.3485 | 0.3503 | — | ✘ |
| b5r | mvns | MMF16_20 | 0.05557 | 0.02895 | — | ✔ |
| b5r | mvns | WFG9 | 0.2109 | 0.1773 | — | ✔ |
| b5r | mvns | ZDT1 | 1.056 | 0.802 | — | ✔ |
| b5r | mvns | ZDT4 | 85.73 | 55.05 | — | ✔ |
| c311 | lhs | DTLZ2 | 0.4382 | 0.3063 | 0.1739 | ✔ |
| c311 | lhs | MMF16_20 | 0.05278 | 0.02797 | 0.007557 | ✔ |
| c311 | lhs | WFG9 | 0.2333 | 0.1844 | 0.1253 | ✔ |
| c311 | lhs | ZDT1 | 1.984 | 1.739 | 1.637 | ✔ |
| c311 | lhs | ZDT4 | 76.27 | 36.38 | 44.3 | ✔ |
| c311 | mvns | DTLZ2 | 0.3485 | 0.3503 | 0.1919 | ✔ |
| c311 | mvns | MMF16_20 | 0.05557 | 0.02895 | — | ✔ |
| c311 | mvns | WFG9 | 0.2109 | 0.1773 | 0.1434 | ✔ |
| c311 | mvns | ZDT1 | 1.056 | 0.802 | 0.8512 | ✔ |
| c311 | mvns | ZDT4 | 85.73 | 55.05 | 45.51 | ✔ |
| e103 | lhs | DTLZ2 | 0.4382 | 0.3063 | — | ✔ |
| e103 | lhs | MMF16_20 | 0.05278 | 0.02797 | — | ✔ |
| e103 | lhs | WFG9 | 0.2333 | 0.1844 | — | ✔ |
| e103 | lhs | ZDT1 | 1.984 | 1.739 | — | ✔ |
| e103 | lhs | ZDT4 | 76.27 | 36.38 | — | ✔ |
| e103 | mvns | DTLZ2 | 0.3485 | 0.3503 | — | ✘ |
| e103 | mvns | MMF16_20 | 0.05557 | 0.02895 | — | ✔ |
| e103 | mvns | WFG9 | 0.2109 | 0.1773 | — | ✔ |
| e103 | mvns | ZDT1 | 1.056 | 0.802 | — | ✔ |
| e103 | mvns | ZDT4 | 85.73 | 55.05 | — | ✔ |
| moead_media | lhs | DTLZ2 | 0.4382 | 0.3063 | — | ✔ |
| moead_media | lhs | MMF16_20 | 0.05278 | 0.02797 | — | ✔ |
| moead_media | lhs | WFG9 | 0.2333 | 0.1844 | — | ✔ |
| moead_media | lhs | ZDT1 | 1.984 | 1.739 | — | ✔ |
| moead_media | lhs | ZDT4 | 76.27 | 36.38 | — | ✔ |
| moead_media | mvns | DTLZ2 | 0.3485 | 0.3503 | — | ✘ |
| moead_media | mvns | MMF16_20 | 0.05557 | 0.02895 | — | ✔ |
| moead_media | mvns | WFG9 | 0.2109 | 0.1773 | — | ✔ |
| moead_media | mvns | ZDT1 | 1.056 | 0.802 | — | ✔ |
| moead_media | mvns | ZDT4 | 85.73 | 55.05 | — | ✔ |

**Placar tier**: mais dado melhorou o IGD+ em **46** séries; piorou em **4**.

**Placar distribuição** (mesma célula, LHS × MVNS): LHS melhor em **32**, MVNS melhor em **27**.


## 5. BATCH q=10 × main q=1 (⚠ orçamentos DIFERENTES: batch = 11D−1+2000)

> Caveat DI-37.4: o contraste limpo é c262/e81 (o c154 saiu do roster por DI-40 e carrega 2 confounders). `sobol_batch` é o CONTROLE — todo SA-batch deve batê-lo.

| problema | D | c149 | e81 | sobol_batch | q=1 (melhor SA main) |
|---|---:|---:|---:|---:|---:|
| ZDT4 | 10 | 91.92 | 40.87 | 68.13 | 5.928 |
| DTLZ2 | 12 | 0.4484 | 0.2249 | 0.2994 | 0.03066 |
| MMF16_20 | 20 | 0.04437 | 0.01169 | 0.02834 | 0.01891 |
| WFG9 | 22 | 0.142 | 0.1789 | 0.2039 | 0.07508 |
| ZDT1 | 30 | 0.07368 | 0.7498 | 1.809 | 0.0007028 |

**Vs o controle Sobol**:
- `c149`: bate o Sobol em **2/5** problemas
- `e81`: bate o Sobol em **5/5** problemas

## 6. Ablações declaradas (D77 e big)

> **D77**: `moead_media` = "o b5 sem σ" — mesmo motor, mesmo surrogate, mesmo lattice; muda SÓ a seleção. **Big**: `treed_media` = "o c311 sem os GPs locais".

| problema | b5m (σ) | moead_media (μ) | quem espalha mais | c311 | treed_media |
|---|---:|---:|---|---:|---:|
| MMF1 | 0.380 | 0.020 | b5m | 0.180 | — |
| MMF11_L | 0.640 | 0.360 | b5m | 0.980 | — |
| MMF4 | 0.640 | 0.260 | b5m | 0.500 | — |
| DTLZ1 | 0.038 | 0.895 | piso | 0.202 | — |
| BBOB_F1 | 0.540 | 0.580 | piso | 0.340 | — |
| BBOB_F17 | 0.140 | 1.000 | piso | 0.500 | — |
| BBOB_F22 | 0.440 | 0.340 | b5m | 0.143 | — |
| BBOB_F37 | 0.180 | 0.060 | b5m | 0.100 | — |
| BBOB_F49 | 0.300 | 0.080 | b5m | 0.156 | — |
| BBOB_F5 | 0.420 | 0.560 | piso | 0.040 | — |
| BBOB_F55 | 0.180 | 0.080 | b5m | 0.140 | — |
| ZDT4 | 0.260 | 0.340 | piso | 0.980 | — |
| ZDT6 | 0.240 | 0.360 | piso | 0.040 | — |
| DTLZ2 | 0.790 | 0.943 | piso | 0.989 | — |
| DTLZ3 | 0.248 | 0.991 | piso | 0.379 | — |
| DTLZ4 | 0.114 | 0.029 | b5m | 0.798 | — |
| MMF16_20 | 0.429 | 0.619 | piso | 0.989 | — |
| DTLZ7 | 0.267 | 0.314 | piso | 0.797 | — |
| WFG1 | 0.480 | 0.360 | b5m | 0.440 | — |
| WFG2 | 0.280 | 0.040 | b5m | 0.059 | — |
| WFG4 | 0.420 | 0.300 | b5m | 0.100 | — |
| WFG5 | 0.420 | 0.300 | b5m | 0.020 | — |
| WFG9 | 0.380 | 0.020 | b5m | 0.040 | — |
| ZDT1 | 0.260 | 0.460 | piso | 1.000 | — |
| ZDT3 | 0.240 | 0.300 | piso | 0.800 | — |
