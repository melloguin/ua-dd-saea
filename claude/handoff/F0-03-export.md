# handoff/F0-03-export.md — Fase 0, cartão 3/4 (wrapper de FE + export das 3 camadas + ponte GCS)

**Data:** 2026-07-16 · **Env:** env-main (`.../mestrado_experimentos_dissertacao/bin/python`;
numpy 2.4.6 · pandas 2.3.3 · pyarrow 25.0.0 · pymoo 0.6.2 ✓)
**Gate:** `PY scripts/accept.py F0-03-export` → **VERDE, exit 0** ✅
**Escopo:** PURA INFRAESTRUTURA — o encanamento de orçamento + escrita que **todas as
Rodadas** vão consumir; **SEM algoritmo, SEM métrica, SEM fidelidade** (D97). O único
gate é o de **encanamento objetivo** (D81/D97).

## Resultado (tudo verde)
- `PY scripts/accept.py F0-03-export` → **exit 0**. Prova com um **algoritmo-STUB**
  (sem algoritmo real) ponta a ponta, num tempdir, os 8 checks:
  1. **FE final = 31D−1 EXATO** (avaliações reais DISTINTAS — D89). Provado em
     **D=2 (MMF1, FE=61)**, **D=10 (BBOB_F1, FE=309)** e **D=30 (ZDT1, FE=929)**.
  2. **cache-hit = 0 FE** (re-avaliar X do DoE não move o saldo — D89) **+ hard-stop
     exato** (a X inédita seguinte levanta `BudgetExhausted` — D21/D61).
  3. **4 saídas** presentes (§17.7) — 3 parquets + `__timing` + `.jsonl`.
  4. **schema §17.2 EXATO** (①②③+timing, nomes+tipos+nulabilidade), ③ unificada C1
     (regressor μ/σ **E** classificador classe/score) + **float32 sem arredondar (D53)**.
  5. **escrita atômica** (0 `.tmp` residual — D58) **+ run pronto ⇒ skip** idempotente.
  6. **`gcs.py`: bucket-only correto (D58)** + **caminho LOCAL sem rede** (no Mac não
     chama GCS — a lib `google-cloud-storage` está ausente, import lazy confirmado).
  7. **CP-init por-run** (fecha o corte do F0-02): `manifest['doe_hash']` (hash da
     init X **float64** do run) = sidecar do DoE (D87/D88).
  8. regressão F0-02: DoE bit-a-bit (`check_doe_hash`).
- **44 testes** (`PY -m unittest discover -s tests -t .`) → **OK** (17 F0-01 + 10 F0-02
  + 17 novos F0-03). No `python3` base (sem pyarrow) os de export/doe **pulam**; os de
  `gcs`/`budget` que só precisam de stdlib/numpy seguem rodando.
- **Regressões:** `accept.py F0-01` exit 0, `accept.py F0-02` exit 0, `preflight.py` exit 0.
- **5 casos-limite adversariais do wrapper de FE** (à mão) — todos fiéis a D89:
  `-0.0 ≠ +0.0` (bit-a-bit distinto), NaN-idêntico = cache-hit, entrada 2D/não-contígua
  **colide** com a 1D equivalente, falha de hard-stop **não polui** o catálogo ①,
  `int x == float x`.

## Arquivos

**Novos:**
- `src/budget.py` — **o wrapper de FE, fonte ÚNICA do orçamento (D89/D57/D21).**
  `FEBudget.evaluate(x, true_f)`: chave = **X NATIVO bit-a-bit**
  (`np.ascontiguousarray(x,'<f8').tobytes()`); **cache-hit = 0 FE + loga evento (D89)**;
  `solution_id` = dedup-por-X inteiro 0-based (D57); **hard-stop EXATO**: a `31D`-ésima
  X inédita levanta `BudgetExhausted` (D21/D61), sem poluir ①. Acumula o **catálogo ①
  em float64** (`RealEval`) e expõe `init_X()` (as 11D−1 primeiras, fase `init`) —
  fonte do `doe_hash` do CP-init. `fase` = `init` se `fe_index < 11D−1` senão `opt`.
- `src/export.py` — **os escritores das 4 camadas (§17.2/§17.3/§17.6).** Schemas
  autoritativos (`real_schema/pop_schema/surrogate_schema/timing_schema`) parametrizados
  em (D,M); ③ é a base ÚNICA C1 (μ/σ opcionais + `pred_classe/score/confianca/modelo`
  + C3 `espaco_modelo/transf_tipo/transf_params`), com `real_solution_id` ligando ao ①.
  **float32 sem arredondar (D53)**, codec **zstd**, **escrita atômica** (reuse
  `atomic_io.atomic_path`), **salvar TUDO sem teto (D54)**. `run_done` = `manifest.is_run_done`
  (skip D58). `surrogate_row(...)` monta linhas com defaults NULL; suporta **μ/σ mais
  curtos que M** (caso mono-output do b1/ParEGO — mu_0 preenchido, mu_1.. NULL, §17.2/D47).
- `src/gcs.py` — **dual-write local+bucket com import LAZY (§17.7/D58).** `import src.gcs`
  roda em QUALQUER interpretador (o `from google.cloud import storage` está DENTRO das
  funções de rede). `BUCKET_ONLY_ALGS = {c154,c122,e81,c149,c262}` (só a camada
  **surrogate** é bucket-only; ①②/timing/jsonl/manifesto = dual-write). `plan_targets(...)`
  é PURO (sem rede) — `enable_bucket=False` = caminho local do Mac; `mirror_run/upload/
  sync_pending/blob_exists` são lazy (VM). `_client()` levanta `RuntimeError` claro se a
  lib faltar (nunca ImportError cru). Bucket `mestrado_experiments`, projeto
  `skilled-text-480300-d9`.
- `tests/test_export_budget.py` — 17 testes (hard-stop exato, cache-hit=0/mesmo-id,
  near-dup paga 1 FE, dedup incremental, fase init/opt, init_X float64; schemas/tipos,
  round-trip real, **float32 ≠ round3**, opcionais C1 + mono-output b1, atômico, zstd,
  pop/timing; bucket-only lista exata, plan local-only sem rede, plan bucket, lazy import).

**Modificados:**
- `scripts/accept.py` — branch real do cartão **`F0-03-export`** (`check_f0_03` roda o
  STUB `_f0_03_stub_run` num tempdir e afere os 8 pontos + `_check_export_schema`).
  Os 3 checks por-run (`check_outputs/check_fe/check_doe_hash`) ganharam **`data_root`**
  (default = `data/` do repo — R1/R2/R3 seguem iguais; o F0-03 injeta o tempdir).
  **NÃO tocou a política D97** (só encanamento; nunca fidelidade).
- `cards/INDEX.md` — F0-03-export → ✅.

## Contrato para quem CONSOME (F0-04 e Rodadas — leia isto)
- **Orçamento:** instancie **UM** `budget.FEBudget(D=prob.n_var, logger=audit_log)` por run.
  TODA avaliação da função verdadeira passa por `bud.evaluate(x_nativo, true_f)`. O
  hard-stop é `except budget.BudgetExhausted` no ponto único de avaliação → o run
  termina com **FE = 31D−1 cravado**. **NÃO** use o `obj.FE` nativo do PlatEMO (D89).
- **CP-init por-run:** ao fechar o run, grave `manifest['doe_hash'] =
  doe.decoded_hash(bud.init_X())` — bate com o sidecar do DoE (o `accept.py --alg`
  compara via `check_doe_hash`). A init X vem em **float64** (a ① no parquet é float32,
  mas o hash é do float64 — não confunda).
- **Export:** `export.write_real(records)` (do `bud.records`), `write_pop(pop_rows)`
  (membership `(geracao, solution_id)`), `write_surrogate(rows, D=, M=, regime=)`
  (monte com `export.surrogate_row(...)`), `write_timing(timing_rows)`. Depois:
  `manifest.new_manifest(status='ok', ...)` + `manifest.write_manifest(...)`. O
  despachante pula o run pronto via `export.run_done(...)` (= `is_run_done`, D58).
- **Colunas (0-based):** o export usa `x0..x{D-1} / f0..f{M-1} / mu_0.. / sigma_0..`
  (ver DECISÃO FIXADA abaixo). Consuma sempre `src.naming` p/ caminhos; **nunca**
  reconstrua strings.
- **Bucket (só VM Python):** após gravar local, `gcs.mirror_run(exp,alg,prob,sem)` sobe
  tudo e **poda a ③ local dos 5 volumosos** (bucket-only, D58). No **Mac/MATLAB** não
  chame gcs — `plan_targets(enable_bucket=False)` = local puro.

## ⚠ DECISÃO QUE FIXEI (para seu veto — trocar = 1 edição)
- **Nomes de coluna do export em 0-based** (`x0..x{D-1}, f0..f{M-1}, mu_0.., sigma_0..`).
  O §17.2 escreve `x_1..x_D`/`f_1..f_M` como **notação matemática**; o F0-02 já
  materializou o DoE/dataset compartilhados em **0-based** e o MATLAB os lê assim → usei
  a MESMA convenção p/ o join ①↔DoE ser trivial. **O CP-init compara HASH DO ARRAY (não
  nomes) → indiferente ao gate.** Centralizei em 4 funções (`export.x_cols/f_cols/mu_cols/
  sigma_cols`) — se você quiser 1-based, é 1 edição. `solution_id`/`geracao`/ids são
  **inteiros (int32)** no parquet (§17.4 — comprimem quase a nada); o `R-001` do §17.2 é
  só ilustração do mock.

## CP-init — o que FECHOU agora (fecha o corte do F0-02)
O F0-02 deixou **1 corte**: "o CP-init COMPLETO exige o X inicial capturado na CAMADA ①
de um run REAL". **A metade Python fechou agora**: o STUB captura a init X pelo wrapper,
grava `manifest['doe_hash']` e o `accept.py` confirma que bate com o sidecar (D87/D88).
**Falta ainda** (herda p/ **R1-00**): o mesmo gancho num run com **adapter real nos 2
stacks** (o `doe_hash` lido da ① que o adapter injeta) — aí o CP-init está 100%
cross-linguagem. O gancho objetivo já está pronto (`accept.py --alg` → `check_doe_hash`).

## Estado do dual-write GCS (herda p/ R2-00 e as Rodadas Python)
- **Encanamento pronto e testado no caminho LOCAL** (Mac): `plan_targets` puro, bucket-only
  correto, import lazy. **NÃO exercitado contra o bucket real** — `google-cloud-storage`
  não está no env-main do Mac (D80/D81: **não instalei** pins; é decisão do autor). O
  **smoke real** (`gs://mestrado_experiments/experiments/_smoke/...` do gate F0/S.4) e o
  `mirror_run/sync_pending` rodam **na VM Vertex** (ADC da SA já provisionado — HANDOFF §7).
  `gcs.smoke_blob_path()` já dá o nome do objeto de smoke.

## Pendências abertas / decisões do autor
1. **Commit dos meus arquivos:** feito nesta sessão com prefixo **`[F0-03-export]`**
   (taxonomia dos cartões F0-01/F0-02). **Só meus 5 arquivos** — não toquei nada de
   terceiros.
2. **⚠ Concorrência — outra instância rodou em paralelo (SEM interferência).** Enquanto
   eu fazia o F0-03, uma 2ª sessão fechou trabalho de F0-02/higiene e **commitou 4 commits
   `chore/docs`** (movendo o HEAD): `e8adacc` reconcilia **BBOB1→BBOB_F*** (o canônico da
   SPEC §4/characteristics/runs_matrix — **o token curto `BBOB1` é que era o anômalo**;
   a NOTA DE NOMES do meu prompt ficou stale), `cf4a4cc` persiste `data/doe`+`data/datasets`
   (agora sob `BBOB_F*`), `d1edcf2` requirements/pandas<3, `bb72de0` docs da torre. **Zero
   sobreposição de arquivos** com o F0-03; meu gate segue verde sob o novo HEAD (inclusive
   `--problema BBOB_F1` → FE=309). **Meu código é agnóstico ao token** (usa `naming` +
   `experiment.ALL_PROBLEMS`) → nada a reconciliar do meu lado.
3. **Camada de auditoria fina (S.7/DEF-C5) e o dicionário C4** ficam para as Rodadas — o
   F0-03 entrega o **mínimo comum** (`audit_log` do F0-01) + o schema ③ que já acomoda
   os campos por algoritmo. Não é do F0-03.
4. **`_stage_precache` do despachante** (`experiments.py`) — **NÃO toquei** (é do F0-01;
   e o import pesado regrediria o `python3` base). As Rodadas ligam `doe.ensure_doe`/
   `ensure_dataset` no adapter (import lazy), como o F0-02 já orientou.

## Commits desta sessão (branch `experiment/definitive_algorythms`)
Prefixo `[F0-03-export]`, cada um citando a decisão. Só meus arquivos.
