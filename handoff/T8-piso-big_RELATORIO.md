# T8 — piso-big (`treed_media`) · RELATÓRIO DE EXECUÇÃO

## Arquivos (a faixa T8, e SÓ ela)
- **NOVO** `src/treed_media.py` — o runner `run_treed_media(exp, alg, problema, semente,
  *, data_root, enable_bucket=False, teto_s=None, q=1, emitir_sonda=True)`.
- **NOVO** `tests/test_treed_media.py` — 3 camadas (TestPuros / TestGanchos[GPy] /
  TestRunCompleto[TREED_SLOW]).
- **EDIT (1 linha)** `src/experiment.py` — dispatch `treed_media` DESCOMENTADO.
- **EDIT (1 linha, AUTORIZADO pelo autor)** `scripts/auditar.py:43` — `treed_media` no set OFFLINE.
- **EDIT (1 linha, AUTORIZADO pelo autor)** `experiments.py:57` — `treed_media` em `_OFFLINE`.
- **DADOS** `data/experiments/sweep-big-{lhs,mvns}/treed_media/**` — os smokes (células reais).
- Nada mais tocado (accept/portao/artefatos/vendored/SPEC/REGISTRO INTOCADOS — faixa da
  torre/T9; auditar.py/experiments.py NÃO são da faixa T9, sem colisão).

## Decisão de projeto validada em runtime
O vendor `Problem.evaluate(use_surrogate=True)` faz `uncertainity[:,c] = results.uncertainity`
(Problem.py:853). Para blindar contra σ=None, o runner usa o `_patched_predict` do c311 no
RVEA: μ é BYTE-idêntico ao stock e, como NÃO há GPs (`error_leaves is None`), σ sai TODO
NaN (nunca None) — a ③ grava σ=NULL de qualquer forma (DI-16.1). Verificado no teste
`test_predict_batch_sigma_toda_NaN_sem_GP` e `test_build_surrogates_sem_GP`.

## GATES

### GATE 1 — Smokes (células REAIS s42), wall medido (50k é terreno novo)
Cobri os **5/5 problemas** do grid (o cartão pedia ZDT4×2 + 1; estendi para robustez):
| célula (D,M) | dist | wall | status | n_ger | n_final | n_ND | ② | sonda |
|---|---|---|---|---|---|---|---|---|
| ZDT4 (10,2) | lhs | **7,37 s** | ok | 1000 | 36 | 7 | vazia | 1×20000 |
| ZDT4 (10,2) | mvns | **6,48 s** | ok | 1000 | 37 | 8 | vazia | 1×20000 |
| DTLZ2 (12,3) | lhs | **12,10 s** | ok | 1000 | 105 | 61 | vazia | 1×20000 |
| ZDT1 (30,2) | lhs | **14,40 s** | ok | 1000 | 50 | 11 | vazia | 1×20000 |
| WFG9 (22,2)* | lhs | **8,12 s** | ok | 1000 | 46 | 16 | vazia | 1×20000 |
| MMF16_20 (20,3) | lhs | **12,91 s** | ok | 1000 | 105 | 79 | vazia | 1×20000 |

*WFG9 tem bounds ≠ [0,1] — honrados via `H._bounds`. Muito abaixo do ~1min do c311-big: a
ablação PULA o laço `addGPs` (o gargalo O(n³) do GPy). `fe_final == maxfe == 50000`,
`cp_init_ok=True` em todas. Portão re-rodado pós-fix em 4 células (ZDT4 lhs/mvns, MMF16_20,
WFG9) — todas VERDE.

### GATE 2 — auditar + final_eval --check + portão → **VERDE**
| gate | sweep-big-lhs/ZDT4/42 | sweep-big-mvns/ZDT4/42 |
|---|---|---|
| `auditar` (offline por classificação) | **VERDE** (DI-34 binding por hash do tier + ⑦ + sonda offline) | — |
| `final_eval … --check` | **VERDE** (⑦ consistente; X reconstituível da ③ ger 1000; 36/37 finais) | — |
| `portao …` (accept+auditar+final_eval) | **✅ VERDE** (0 vermelhos) | **✅ VERDE** (0 vermelhos) |

**Nota:** o portão estava vermelho porque `scripts/auditar.py:43` `OFFLINE` NÃO listava
`treed_media` (e `portao.py` chama auditar SEM `--regime` ⇒ misclassificava o run offline
como online). O AUTOR AUTORIZOU (resposta em sessão) o T8 a aplicar os 2 one-liners de
fiação de gate — `scripts/auditar.py:43` (+`"treed_media"` no set OFFLINE) e
`experiments.py:57` (`_OFFLINE` += `treed_media`) — ambos ALHEIOS à faixa T9. Aplicados;
portão agora VERDE. (Ver REPASSE #1/#2 — RESOLVIDOS.)

### GATE 3 — Determinismo + Não-perturbação (via TestRunCompleto, env_c311, TREED_SLOW=1)
- `test_determinismo_bit_a_bit` — **OK**: 2 runs da mesma semente ⇒ ⑦ E ③-busca IDÊNTICAS
  (NaN-aware `pandas.equals`).
- `test_sonda_NAO_perturba_a_busca` — **OK**: ⑦ e ③-busca IDÊNTICAS com sonda on/off
  (a sonda roda sob `preserve_all_rng`). σ é todo NULL ⇒ comparação NaN-safe trivial.
- `test_sete_camadas_e_invariantes` — **OK**: 7 camadas; σ NULL em busca E sonda; μ
  preenchido; sonda 20000/1-flag/geracao NULL; busca geracao 1..1000; ④ 1 linha com
  `tempo_geracao_s == fit+busca` (DI-13.10, exclui sonda); ⑤ sigma_dict presente.
- (5 runs de 50k em 27,6 s.)

### GATE 4 — Testes + suíte + preflight
- `tests/test_treed_media.py`: **env_c311** (py3.8) → 12 ok / 3 skip(SLOW); **env-main**
  (py3.11) → 8 ok / 7 skip(vendor+SLOW). Importável e env-main-safe (imports do vendor
  diferidos p/ `_import_vendor`).
- **Suíte completa (env-main discover):** `Ran 384 tests … OK (skipped=30)` — ANTES e DEPOIS
  de descomentar o dispatch (sem regressão). Nenhum módulo da faixa T9 falhou na janela.
- `scripts/preflight.py`: **pré-voo OK ✓** (exit 0).
- Dispatch: `_resolve_dispatch('treed_media')` → `run_treed_media`/standalone; em
  `KNOWN_ALGORITHMS` e `VENV_ONLY_ALGS` (roteado p/ `run_in_venv`/env_c311).

## Coexistência T9
`git diff --cached --name-only` VAZIO conferido antes de cada passo; nenhum push; nenhum
`add -A`. A suíte completa passou sem tocar arquivos da T9.

## Invocação (reprodução)
```
TREED_SLOW=1 MPLBACKEND=Agg PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  /Users/gmello/Documents/python_venvs/env_c311/bin/python -m unittest tests.test_treed_media
```
Smoke direto: `run_treed_media("sweep-big-lhs","treed_media","ZDT4",42, data_root="data")`.
