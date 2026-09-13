# Fundação 5/5 — Os 25 problemas, f_min/f_max e notas do problems.py

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

## 4. Os problemas — 25 [DECIDIDO — MMF16_L3 d=3 removido; ver Anexo P e Anexo D/REF-1]

Extraídos de `problems.py` (classes pymoo, cada uma com `true_pareto_front`). **n_var (D) e n_obj são os defaults programados — são os valores oficiais e devem ser respeitados em TODAS as análises** (D é fator de dificuldade e de escalabilidade). O `n_init = 11D−1` aparece porque é o DoE inicial (§5.2).

| # | Problema | Suíte | n_obj | D | n_init (11D−1) | Característica estressada (motivo da escolha) |
|---|---|---|---|---|---|---|
| 1 | MMF1 | MMF | 2 | 2 | 21 | multimodalidade / niching (calibração) |
| 2 | MMF4 | MMF | 2 | 2 | 21 | front côncavo + multimodalidade |
| 3 | MMF11_L | MMF | 2 | 2 | 21 | ótimos locais vs globais próximos |
| 4 | MMF16_20 | MMF | 3 | 20 | 219 | multimodalidade em alta dimensão |
| 5 | ZDT1 | ZDT | 2 | 30 | 329 | front convexo, alta dimensão (estresse dimensional deliberado) |
| 6 | ZDT3 | ZDT | 2 | 30 | 329 | front descontínuo/fragmentado |
| 7 | ZDT4 | ZDT | 2 | 10 | 109 | multimodalidade extrema |
| 8 | ZDT6 | ZDT | 2 | 10 | 109 | densidade não-uniforme / heterocedasticidade |
| 9 | DTLZ1 | DTLZ | 3 | 7 | 76 | front linear + multimodalidade |
| 10 | DTLZ2 | DTLZ | 3 | 12 | 131 | front côncavo (baseline suave) |
| 11 | DTLZ3 | DTLZ | 3 | 12 | 131 | côncavo + multimodalidade severa |
| 12 | DTLZ4 | DTLZ | 3 | 12 | 131 | densidade enviesada (α=100) |
| 13 | DTLZ7 | DTLZ | 3 | 22 | 241 | front desconexo (4 regiões) |
| 14 | WFG1 | WFG | 2 | 22 | 241 | não-separabilidade + bias |
| 15 | WFG2 | WFG | 2 | 22 | 241 | front desconexo + não-separável |
| 16 | WFG4 | WFG | 2 | 22 | 241 | multimodalidade (estresse surrogate) |
| 17 | WFG5 | WFG | 2 | 22 | 241 | enganosidade (deceptive) |
| 18 | WFG9 | WFG | 2 | 22 | 241 | não-separável + enganoso + dependência |
| 19 | BBOB_F1 Sphere/Sphere | BBOB | 2 | 10 | 109 | baseline unimodal (front analítico) |
| 20 | BBOB_F5 Sphere/SharpRidge | BBOB | 2 | 10 | 109 | crista aguda / condicionamento |
| 21 | BBOB_F17 Ellipsoid/SchafferF7 | BBOB | 2 | 10 | 109 | separável × multimodal |
| 22 | BBOB_F22 AttractiveSector/SharpRidge | BBOB | 2 | 10 | 109 | assimetria + crista |
| 23 | BBOB_F37 SharpRidge/Rastrigin | BBOB | 2 | 10 | 109 | crista × multimodal regular |
| 24 | BBOB_F49 Rastrigin/Gallagher101 | BBOB | 2 | 10 | 109 | multimodal regular × irregular |
| 25 | BBOB_F55 Gallagher101/Gallagher101 | BBOB | 2 | 10 | 109 | multimodal irregular (Gaussian peaks) |

- **Contagem:** **25 classes concretas.** Da família MMF16 mantém-se **só a variante d=20 (`MMF16_20`)**; a variante d=3 (`MMF16_L3`) foi **removida** (decisão registrada no Anexo D e no MAPA) — o `MMF16_20` já cobre a multimodalidade 3-obj com o agravante da alta dimensão.
- **Distribuição de objetivos [corrigido v2.7]:** **19 problemas de 2-obj + 6 de 3-obj = 25** (2-obj = MMF1/4/11_L + ZDT1/3/4/6 + WFG1/2/4/5/9 + 7 BBOB = 19; 3-obj = MMF16_20 + DTLZ1/2/3/4/7 = 6). **Todos os algoritmos do set rodam nos 25 problemas — a matriz experimental é densa, sem buracos.** A restrição de escalabilidade dos métodos BO-HV só morderia acima de ~4–5 obj, fora do escopo.
- **Nuance do BBOB:** o front verdadeiro do BBOB é **empírico** (NSGA-II acumulado, cache em `data/bbob_pf_cache/`), exceto F1 (analítico). Consequência métrica em §12.1.
- **[v2.2] Achados da releitura integral do `problems.py` (arquivo idêntico ao da 1ª passada; detalhes no Anexo L.19):**
  - **MMF16_20 tem 17 variáveis INERTES**: g depende só de x20 (código: `xn = X[:,-1]`); x3..x19 não afetam F em nada. A característica real do problema é *"dimensões irrelevantes + multimodalidade em 1 variável de distância"* — um teste de parcimônia do surrogate (ARD deveria matar 17 lengthscales) → registrar na coluna de característica e usar na análise por característica (§15).
  - **BBOB**: cada objetivo usa uma INSTÂNCIA diferente (Kα=2K+1, Kβ=2K+2; default instance=1 → (3,4)) — Pareto set não-degenerado por construção; o RNG das instâncias é próprio (SeedSequence[fid, inst, n_var]) e **NÃO é bit-idêntico ao COCO** (nota de honestidade para a dissertação — o header do arquivo já a declara); F1 tem HV normalizado analítico = 0,8333 (sanity check citável); f_pen (F17/F49/F55) é inativo dentro de [−5,5] (nosso clamp garante).
  - **Cache do BBOB**: o caminho é `<pai-do-diretório-do-problems.py>/data/bbob_pf_cache/` (relativo à LOCALIZAÇÃO do arquivo) → a distribuição às VMs (DEF-A9) deve preservar o layout `<raiz>/problems.py` + `<raiz-pai>/data/` ou padronizar a raiz; parâmetros do cache: pop 200 × 300 ger × 5 sementes (seed 0), subsample uniforme por f1.
  - **Semântica dos `true_pareto_front(n)`**: os 3-obj retornam grades n² parametrizadas (meshgrid) — densidade NÃO-uniforme na esfera (polos densos); MMF1/MMF4 retornam 2n pontos; ZDT3 usa n=5000+NDS; DTLZ7 200²+NDS → **a camada de métrica (§12) NUNCA usa o retorno cru como reference set** — re-amostra Das-Dennis/Riesz (3-obj) e re-espeça (2-obj), como já decidido.
  - **`MMF16_20` usa g = 2 − sin²(…)** (código e docstring consistentes); é extensão própria do autor (report §1.3), não a MMF16 2-obj de Liang et al. *(A antiga DEF-A10/D19, que corrigia a docstring do `MMF16_L3` d=3, ficou obsoleta com a remoção desse problema — ver Anexo D.)*
  - `evaluate_problem` chama `problem._evaluate` DIRETO (bypassa `Problem.do` do pymoo: sem repair, sem contagem, sem validação de bounds — confirma DEF-A4/A11); `_nds_filter` usa ENS do **pymoo moderno** (confirma que o env da ponte precisa de pymoo 0.6.x — DEF-D1).

---
---

# PARTE III — PROTOCOLO COMPARTILHADO (online + offline)

---

### S.5 — Dados prontos: `f_min/f_max` por problema (B11.1 — computados dos fronts verdadeiros de `problems.py`, BBOB do cache `i1`)

**Uso (c122 e qualquer normalização por-problema):** `f_min` = ideal do front verdadeiro; `f_max_uso = nadir_front + 0,1·(nadir_front − f_min)` (margem de 10% do range, 🟢 escolha nossa — consistente com o ref-point do HV no espaço normalizado (D69) — para acomodar pontos piores que o front no início da busca; guarda `range ≥ 1e-12`). Valores CRUS abaixo (4 casas; a margem aplica-se no harness):

| Problema | M | f_min (ideal) | f_max (nadir do front) |
|---|---|---|---|
| MMF1 | 2 | [0.0005, 0.0] | [1.0, 0.9776] |
| MMF4 | 2 | [0.001, 0.0] | [1.0, 1.0] |
| MMF11_L | 2 | [0.1, 0.9523] | [1.1, 10.4757] |
| MMF16_20 | 3 | [0.0, 0.0, 0.0] | [2.0, 2.0, 2.0] |
| ZDT1 | 2 | [0.0, 0.0] | [1.0, 1.0] |
| ZDT3 | 2 | [0.0, −0.7734] | [0.8519, 1.0] |
| ZDT4 | 2 | [0.0, 0.0] | [1.0, 1.0] |
| ZDT6 | 2 | [0.2809, 0.0] | [1.0, 0.9211] |
| DTLZ1 | 3 | [0, 0, 0] | [0.5, 0.5, 0.5] |
| DTLZ2 | 3 | [0, 0, 0] | [1, 1, 1] |
| DTLZ3 | 3 | [0, 0, 0] | [1, 1, 1] |
| DTLZ4 | 3 | [0, 0, 0] | [1, 1, 1] |
| DTLZ7 | 3 | [0.0, 0.0, 2.614] | [0.8599, 0.8599, 6.0] |
| WFG1 | 2 | [0.0, 0.0] | [2.0, 4.0] |
| WFG2 | 2 | [0.0, 0.0] | [2.0, 4.0] |
| WFG4 | 2 | [0.0014, 0.0] | [2.0, 4.0] |
| WFG5 | 2 | [0.1569, 0.0032] | [2.0, 3.9877] |
| WFG9 | 2 | [0.0, 0.0] | [2.0, 4.0] |
| BBOB F1 | 2 | [0.0, 0.0] | [82.042, 82.042] |
| BBOB F5 | 2 | [0.0156, 33.9822] | [87.3013, 1495.7185] |
| BBOB F17 | 2 | [0.7912, 0.3073] | [**5.6972e+07**, 107.9268] |
| BBOB F22 | 2 | [2.5729, 22.0423] | [92863.619, 1215.6824] |
| BBOB F37 | 2 | [17.8485, 23.3374] | [1724.6925, 390.3391] |
| BBOB F49 | 2 | [25.3176, 0.0123] | [1243.2907, 84.7479] |
| BBOB F55 | 2 | [0.0002, 0.1473] | [75.1174, 63.0222] |

*(O f₁ do BBOB F17 em escala 10⁷ é a prova viva do porquê da B11.1: sem `f_min/f_max` por problema, o PBI/clustering do c122 colapsa nessas escalas. Os BBOB vêm do front EMPÍRICO do cache — regenerar a tabela se o cache for regenerado; script de geração: instanciar cada classe de `problems.py`, `true_pareto_front(1000)`, min/max por coluna.)*

---

### L.19 · problems.py — resumo dos achados na §4 [v2.2]. Adicional p/ o harness: `true_pareto_front` de MMF16_20 acha g_min numericamente em grade 10k (não exato em x=1/8 — erro ~1e-9, inócuo); `_s_linear` tem guard 1e-30; `_correct_to_01` clampa drift de float; BBOB `instance` é parâmetro do construtor (default 1) — **fixar instance=1 no manifesto** (mudar instance muda o problema); F1 analítico serve de teste de fumaça do pipeline de métricas (HV normalizado 0,8333).

---
