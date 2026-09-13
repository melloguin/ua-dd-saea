# F5.5 §4 — CORRIGIDA: o sweep medido pela camada 7

> **Por que esta correcao existe.** A versao anterior desta secao usou o IGD+ da
> camada 1. Nos configs OFFLINE a camada 1 E o dataset compartilhado, entao a metrica
> EMPATA por desenho entre todos os algoritmos do mesmo (tier, dist, problema) —
> provado: 119 linhas colapsam em **30 valores distintos**, e **30/30 grupos tem valor
> unico entre todos os algs**. Aquele placar media o DATASET, nao o algoritmo.
> O discriminante correto e a camada 7 (ND final avaliado na funcao REAL), como a
> secao 3 ja fazia para o `off`. Achado do consolidador F5.6, confirmado e corrigido.

## A. "Mais dado -> melhor?" — pela camada 7

| config | dist | problema | small | medium | big | melhora? |
|---|---|---|---:|---:|---:|---|
| b5m | lhs | DTLZ2 | 0.05689 | 0.06522 | — | NAO |
| b5m | lhs | MMF16_20 | 0.07016 | 0.9554 | — | NAO |
| b5m | lhs | WFG9 | 0.3232 | 0.2173 | — | sim |
| b5m | lhs | ZDT1 | 1.136 | 1.275 | — | NAO |
| b5m | lhs | ZDT4 | 46.73 | 194.1 | — | NAO |
| b5m | mvns | DTLZ2 | 0.2567 | 0.3007 | — | NAO |
| b5m | mvns | MMF16_20 | 0.1381 | 0.3597 | — | NAO |
| b5m | mvns | WFG9 | 0.2159 | 0.147 | — | sim |
| b5m | mvns | ZDT1 | 1.572 | 1.039 | — | sim |
| b5m | mvns | ZDT4 | 230.3 | 210.3 | — | sim |
| b5r | lhs | DTLZ2 | 0.04753 | 0.03412 | — | sim |
| b5r | lhs | MMF16_20 | 0.1144 | 0.06631 | — | sim |
| b5r | lhs | WFG9 | 0.3814 | 0.2641 | — | sim |
| b5r | lhs | ZDT1 | 0.3149 | 0.3294 | — | NAO |
| b5r | lhs | ZDT4 | 127.3 | 148 | — | NAO |
| b5r | mvns | DTLZ2 | 0.1841 | 0.1424 | — | sim |
| b5r | mvns | MMF16_20 | 0.2299 | 0.1752 | — | sim |
| b5r | mvns | WFG9 | 0.3317 | 0.2625 | — | sim |
| b5r | mvns | ZDT1 | 0.2867 | 0.218 | — | sim |
| b5r | mvns | ZDT4 | 149.8 | 55.58 | — | sim |
| c311 | lhs | DTLZ2 | 0.04081 | 0.02549 | 0.02547 | sim |
| c311 | lhs | MMF16_20 | 0.02645 | 0.05824 | 0.02512 | sim |
| c311 | lhs | WFG9 | 0.497 | 0.4622 | 0.2324 | sim |
| c311 | lhs | ZDT1 | 0.03335 | 0.1382 | 0.2174 | NAO |
| c311 | lhs | ZDT4 | 184.7 | 170.6 | 67.39 | sim |
| c311 | mvns | DTLZ2 | 0.04884 | 0.03402 | 0.03015 | sim |
| c311 | mvns | MMF16_20 | 0.04716 | 0.02603 | — | sim |
| c311 | mvns | WFG9 | 0.3881 | 0.388 | 0.3884 | NAO |
| c311 | mvns | ZDT1 | 0.006216 | 0.009432 | 0.04451 | NAO |
| c311 | mvns | ZDT4 | 201.3 | 138.4 | 75.42 | sim |
| e103 | lhs | DTLZ2 | 0.07575 | 0.07025 | — | sim |
| e103 | lhs | MMF16_20 | 0.506 | 0.5072 | — | NAO |
| e103 | lhs | WFG9 | 0.2843 | 0.2099 | — | sim |
| e103 | lhs | ZDT1 | 0.005206 | 0.007176 | — | NAO |
| e103 | lhs | ZDT4 | 71.04 | 53.95 | — | sim |
| e103 | mvns | DTLZ2 | 0.4651 | 0.4788 | — | NAO |
| e103 | mvns | MMF16_20 | 0.2298 | 0.5018 | — | NAO |
| e103 | mvns | WFG9 | 0.1875 | 0.1466 | — | sim |
| e103 | mvns | ZDT1 | 0.003236 | 0.003079 | — | sim |
| e103 | mvns | ZDT4 | 133.7 | 118.5 | — | sim |
| moead_media | lhs | DTLZ2 | 0.8904 | 2.686 | — | NAO |
| moead_media | lhs | MMF16_20 | 0.3008 | 0.1083 | — | sim |
| moead_media | lhs | WFG9 | 0.5271 | 0.4715 | — | sim |
| moead_media | lhs | ZDT1 | 0.1978 | 0.2363 | — | NAO |
| moead_media | lhs | ZDT4 | 210.6 | 144.5 | — | sim |
| moead_media | mvns | DTLZ2 | 0.6856 | 2.427 | — | NAO |
| moead_media | mvns | MMF16_20 | 0.08182 | 0.4275 | — | NAO |
| moead_media | mvns | WFG9 | 0.3237 | 0.388 | — | NAO |
| moead_media | mvns | ZDT1 | 0.1958 | 0.4151 | — | NAO |
| moead_media | mvns | ZDT4 | 204.2 | 144.5 | — | sim |

**Placar (camada 7)**: mais dado melhorou o endpoint em **29** series; piorou em **21**.

**LHS x MVNS (camada 7, mesma celula)**: LHS melhor em **27**, MVNS em **32**.

## B. Ranking dos configs no sweep (camada 7) — agora DISCRIMINA

| config | rank medio | celulas | fantasia mediana | vitorias |
|---|---:|---:|---:|---:|
| treed_media | 1.70 | 10 | 0.291 | 3 |
| c311 | 2.03 | 29 | 0.905 | 15 |
| e103 | 2.40 | 20 | 0.515 | 10 |
| b5r | 2.85 | 20 | 0.376 | 1 |
| b5m | 3.45 | 20 | 0.391 | 1 |
| moead_media | 3.90 | 20 | 0.381 | 0 |

**Guarda de front degenerado**: celulas cuja camada 7 tem 1 unico X distinto (o "front" e uma duplicata): moead_media=3, b5m=1, c311=1 — reportadas, nao usadas como evidencia de qualidade.

