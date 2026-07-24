# T8 — piso-big do sweep (`treed_media`, alg_id=23) · O CARTÃO

**1 sessão = 1 cartão.** Este cobre SÓ o runner `src/treed_media.py` (+ seu teste +
o descomento de 1 linha do dispatch). Faixa DISJUNTA da T9 (c262/c154/test_batch_q10).

## O que é (B15.4 / DI-16.5[P5] / D38 / DI-35.2 / REGISTRO A23)
`treed_media` é a **ABLAÇÃO CIRÚRGICA do c311 no tier `big` (50k)** — "o c311 SEM os
GPs". Mesmo vendor (`algorithms/c311_TGPR-MO`, INTOCADO), mesma árvore de regressão,
mesmo motor RVEA-final, mudando SÓ que o surrogate é a **árvore pura**: `build_surrogates`
DIRETO (treina 1 `treeGP` por objetivo, SÓ a árvore) — SEM a construção iterativa
`addGPs` (a folha-de-maior-impureza NUNCA ganha um GP local). Predição = MÉDIA da
árvore; sem GP não há variância ⇒ **σ NULL em TODA a ③** (o precedente moead_media /
DI-16.1 — "o b5 sem σ" — aqui "o c311 sem GPs"). Roda no `env_c311` porque a `treeGP`
mora no vendor do c311; NUNCA co-importar com b5 (N.1.2/D79).

**Por que módulo próprio e não o "ramo big" do c311** (DI-35.2, contra a leitura antiga
do T7): rotear `tier=='big'` para dentro do c311 transformaria o ÚNICO config do tier big
na sua própria ablação. O c311-big RODA a construção iterativa (âncoras SPEC :1904/:1520).
O piso-big vive AQUI, ao lado do c311. O laço do c311 fica INTOCADO.

## O fluxo (o c311 SEM a construção e SEM σ)
`ds_{prob}_{sem}_big_{dist}.parquet` (① = dataset, orçamento ESGOTADO, CP x_hash E f_hash)
→ `_build_surrogates` (IMPORTADA de `src.c311_tgprmo`, fonte única) → **SONDA** (1 bloco
de 20.000, μ da árvore, σ NULL, geracao=NULL) → **RVEA final** `10 × 100 = 1000` gerações
sobre a árvore FIXA (`selection_type="mean"`, os defaults do RVEA — a fase FINAL do c311
à risca) → **⑦** do ND real pós-hoc (fora do orçamento, DI-08). Qualquer FE REAL na busca
⇒ `OfflineBudgetViolation` (pára-e-loga D81).

Contador `geracao` **SIMPLES 1..1000** (fase única: sem o offset C311-11/DI-16.19 do c311;
o RVEA final nunca chama `_refresh_population`, então enganchamos SÓ o `_next_gen`).

## Contratos honrados (e onde)
| contrato | decisão | onde |
|---|---|---|
| σ NULL POR CONSTRUÇÃO | DI-16.1 | `_Recorder` (sigma=None) + `_sonda_predict_media` (→None) |
| ② VAZIA | DI-16.17 | `real_solution_id=None`; `buf.pop_rows` vazio |
| 1 bloco de sonda | modelo único (vs 2 do c311/DI-16.12) | `emit_sonda_block` + `_null_sonda_geracao` |
| ④ = 1 LINHA | treino único (molde piso) | `add_timing(geracao=1)` + `update_timing(1,…)` |
| ⑦ reconstituível da ③ | DI-13.9/B7.5; `nd_pos_real` calc. pelo write_final (DI-27/A15) | `write_final(...)` sem `nd_pos_real=` |
| teto UNIVERSAL | DI-35.5 (43200s); rito do piso/b5 | check inline no laço RVEA → status=failed, curva parcial |
| uso_id=_default/0 | seeds.json:157 | `iteration_seed(base,23,0,0)` p/ np.random E random |
| vendor intocado / venv-only | D79/N.1.2 | `_import_vendor` importado; NUNCA b5 |
| redação sigma_dict | DI-28 ("mesma ESPECIFICAÇÃO, treino INDEPENDENTE") | `_sigma_dict()` |

**Fonte única:** `_import_vendor`, `_build_surrogates`, `_predict_batch`,
`_patched_predict`, `_lhs_determinismo`, `_silencio`, `_threads_pinned`,
`_max_busca_geracao`, `VENDOR_ROOT` — todos IMPORTADOS de `src.c311_tgprmo`.

## O grid (runs_matrix.csv — já regenerado pela torre)
300 linhas `treed_media`: 5 problemas `{ZDT4, ZDT1, DTLZ2, WFG9, MMF16_20}` × 30 sementes
`{0..28, 42}` × 2 dists `{lhs, mvns}`. Tudo `tier=big`, `env=env_c311`, `q=1`, `regime=offline`.

## Fechamento
- `src/treed_media.py` (novo) · `tests/test_treed_media.py` (novo) · 1 linha descomentada
  em `src/experiment.py` (dispatch `treed_media`).
- Gates: ver `T8-piso-big_RELATORIO.md` — **os 4 VERDES** (o portão inclusive, após 2
  one-liners de fiação de gate autorizados pelo autor: `auditar.OFFLINE` + `experiments._OFFLINE`).
  Definições em aberto p/ a torre (cosmética + confirmação ⑦-no-teto): ver `T8-piso-big_REPASSE.md`.
