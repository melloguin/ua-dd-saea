# handoff/R2-00-harness.md — Rodada 2, cartão 00 (infra TRANSVERSAL BoTorch)

**Data:** 2026-07-17 · **Env:** env-main NO MAC (decisão do autor: implementação/
pilotos no Mac; a VM só no M8) — `.../mestrado_experimentos_dissertacao/bin/python`;
**botorch 0.18.1 OFICIAL** (N.2.3 ✓, não é o fork `Unknown`) · torch 2.11.0 ·
gpytorch 1.15.2 · pymoo 0.6.2 · scipy 1.17.1 · numpy 2.4.6 · pyarrow 25.0.0 ·
google-cloud-storage presente (ADC do Mac → bucket OK).
**Gate:** `PY scripts/accept.py R2-00-harness --alg stubpy --problema {MMF1,ZDT1}
--semente 0` → **VERDE, exit 0 nos 2** (15/15 checks) + **SMOKE GCS REAL verde**
(`--gcs-smoke`: 6 blobs byte-idênticos · sync re-subiu 1 · 6 deletados, 0 resíduo). ✅
**Escopo:** PURA INFRAESTRUTURA TRANSVERSAL (contrato N.1/§22.3). **SEM algoritmo**
(c262/c154 são os próximos cartões), **SEM fidelidade** (D97). Prova por run-STUB
**`stubpy`** (espelho Python do STUB MATLAB do R1-00 — token distinto de propósito:
`data/experiments/main/stub/` é do R1-00 e não foi tocado).

## Paralelismo (faixas)
Sessão executada em PARALELO com o R1-c238 (MATLAB) na MESMA árvore. Toquei SÓ a
minha faixa: `src/botorch_harness.py` + `src/experiment.py` + `scripts/accept.py`
(branch aditivo) + `tests/test_botorch_harness.py` + este handoff — mais **1
exceção documentada** (abaixo). Zero `.m`, zero `algorithms/**`, zero artefatos
compartilhados; `cards/INDEX.md` **NÃO marcado** (a torre marca no merge).

## Resultado (tudo verde)
- **Gate R2-00 (15 checks × 2 problemas):** botorch==0.18.1 oficial · wiring
  `experiment.run`→dispatch lazy · **FE = 31D−1 EXATO** (MMF1 D2: 61; ZDT1 D30:
  929) · **cache-hit = 0 FE ×3** (U repetida, X nativa, pós-esgotamento — D89) ·
  **hard-stop natural** no laço (D61) · 4 saídas · **schema §17.2 EXATO** (①②③+
  timing; float32 D53; zstd) · atômico + skip (D58) · **CP-init**
  (manifest.doe_hash = sidecar — D87/D88) · **pinning D79/N.1.1** (threads=1,
  float64, CPU, env=1) · **RNG-guard N.1.3** (provado contra `pymoo.minimize`
  REAL) · **sementes L.10/D62/D91** determinísticas (trunc 32b) · **adapter §5.5**
  (−f + Standardize + [0,1]↔nativo) · jsonl §17.5.1 · manifesto com env
  N.2.3/L.18 + fit_series §17.6 · plano bucket dual-write.
- **SMOKE GCS REAL (o deferido do F0-03 — fechado):** `gcs.mirror_run` subiu as 4
  camadas + jsonl + manifesto ao bucket real; **byte-identidade sha256 blob×local
  nos 6**; `sync_pending` re-subiu 1 blob derrubado; **DELETE de todos os blobs de
  teste** (verificado: 0 resíduo em `experiments/main/stubpy/`). Nota: o bucket tem
  versionamento ON → os deletes viram non-current (somem pela lifecycle pendente —
  HANDOFF §7.5; custo desprezível).
- **Regressão Python:** accept F0-01/F0-02/F0-03/F0-04 **exit 0** · `preflight.py`
  **exit 0** · unittest **75 OK (1 skip legítimo)** · 13 testes novos do harness.
- **Auditoria pyarrow das saídas do stubpy** (`data/experiments/main/stubpy/`,
  gitignored): schemas §17.2 exatos, codec ZSTD, ① com `init=11D−1`/`opt=20D`
  cravados e `solution_id` único, ③ com C1 (μ **e** classe) e `real_solution_id`
  nullable, timing com 20D eventos.
- **Números do STUB:** MMF1 → FE 61, 40 iters, ~2,1 s · ZDT1 → FE 929, 600 iters,
  ~28 s (o custo é do stub com `gc.collect()`/iter + sonda pymoo, não do harness).
- **Revisão adversarial (4 lentes + adjudicação):** contrato N.1 = 10/10 ✓ ·
  faixa/aditividade = limpo · 8 endurecimentos aplicados no gate/smoke/testes
  (limpeza do smoke derivada do PLANO + verificada pós-delete; sementes
  re-derivadas independentes no gate; jsonl blindado + ≥3 guards cache_hit
  cruzados com o manifesto; D/M anti-circular; labels honestos) · 1 fix no stub
  (`n_acumulado` da §17.6 capturado ANTES do infill: 1º=11D−1, último=31D−2 ✓) ·
  2 majors de INTEGRAÇÃO pré-existentes → Pendências 1–2. Tudo re-validado após.

## Arquivos
**Novos:**
- **`src/botorch_harness.py`** — a infra transversal R2 (o que c262/c154 HERDAM):
  - **Pinning D79/N.1.1:** env `OMP/OPENBLAS/MKL/NUMEXPR=1` setados NO TOPO do
    módulo (antes do `import torch`) + `pin_runtime()` (threads=1, float64
    default, `DEVICE=cpu`) — chame no INÍCIO de todo run. *Honestidade:* o pinning
    autoritativo da bateria é o subprocess do D79 (despachante, M8); em-processo o
    módulo pina o que é runtime e REGISTRA o estado no manifesto.
  - **`env_info()`** — guarda N.2.3 (`__version__=="Unknown"` ⇒ RuntimeError) +
    versões p/ o manifesto (botorch + **sha256 do RECORD instalado**, scipy L.18).
  - **`load_doe()`** — CARREGA o artefato (D63/D87), hash do array decodificado =
    sidecar; ausente ⇒ FileNotFoundError; divergente ⇒ RuntimeError (pára-e-loga).
  - **`BoTorchProblemAdapter`** — §5.5: `normalize/unnormalize` DO botorch com
    `bounds_native` (2×D f64); `evaluate_unit_max(U)` → **−f** (o sinal vive SÓ no
    motor; ① e métrica ficam no f de minimização); `make_standardize()`;
    avaliação DIRETA de `problems.py` (mesmo processo, sem ponte) SEMPRE via
    `FEBudget` (D89 vale p/ U repetida: des-normalização determinística ⇒ mesmo X
    nativo bit-a-bit ⇒ cache-hit). Acumula `tempo_aval_real_s`.
  - **`iteration_seed()`/`torch_seed_for()`** — a materialização EXATA do
    `seeds.json` (D91): `SeedSequence((base, alg_id, iteracao, uso_id))`, uint64,
    **truncada a 32 bits p/ `torch.manual_seed`/pymoo** (como o artefato manda).
    L.10 = `torch_seed_for(...)` ANTES de construir modelo+acqf (uso_id 0 do
    catálogo c262). Sementes efetivas logadas no `.jsonl`.
  - **`preserve_global_rng()` / `guarded_pymoo_minimize()`** — N.1.3 (salva/
    restaura `np.random`+`random`; use o embrulho p/ TODO pymoo interno).
  - **`iteration_cleanup()`** — gancho D86/N.1.5: o chamador `del`eta os tensores
    da iteração e chama o gancho (`gc.collect()` + `empty_cache` se GPU);
    predição SEMPRE sob `torch.no_grad()`.
  - **`SnapshotBuffer`** — ②(membership)+③(`export.surrogate_row`)+timing POR
    ITERAÇÃO DE BO (§17.3/§17.6); `fit_series` p/ o manifesto.
  - **`write_run_outputs()`** — fecha o run: 4 camadas via `src.export` (REUSO,
    nada duplicado), **CP-init AFIRMADO** (hash(init_X f64) ≠ sidecar ⇒
    RuntimeError), manifesto com doe_hash/env/pinning/fit_series/cache_hits.
  - **`dual_write_run()`** — §17.7 (reusado pela R3): `gcs.mirror_run` (poda ③
    dos bucket-only — D58) + `upload_status` no manifesto regravado e re-subido.
    No Mac/pilotos `enable_bucket=False` (default) = local puro; bucket-only
    plena é da bateria M8.
  - **`run_stubpy()`** — o STUB (assinatura padrão dos runners R2:
    `runner(exp, alg, problema, semente, **kwargs)`).
- `tests/test_botorch_harness.py` — 13 testes (pinning; guarda N.2.3; fórmula
  D91 bit-a-bit vs `SeedSequence`; determinismo L.10; N.1.3; load_doe
  ausente/corrompido; bijeção+sinal+hard-stop+Standardize do adapter; buffer;
  wiring lazy). Pulam sem torch/botorch (python3 base).

**Modificados:**
- `src/experiment.py` — **despacho LAZY**: `_DISPATCH_LOADERS` (`alg → (módulo,
  fn, stack)`; strings, sem import pesado) + `_resolve_dispatch` + corpo real de
  `run()` (resolve, cacheia em `ALGORITHM_DISPATCH`, repassa `**kwargs` —
  `data_root`/`enable_bucket`). **`ALGORITHM_DISPATCH` continua VAZIO no import**
  → o módulo segue leve (python3 base) e o check do F0-01 (`dispatch vazio`)
  segue verde por processo. **c262/c154: adicionar 1 linha no
  `_DISPATCH_LOADERS`** e pronto.
- `scripts/accept.py` — branch **ADITIVO** `R2-00-harness` (`check_r2_00` + smoke
  `_r2_00_gcs_smoke` + flag `--gcs-smoke` + guarda anti-`--alg stub`). Zero
  branch existente tocado; **D97 intacto** (só encanamento objetivo). Reusa
  `check_fe`/`check_outputs`/`_check_export_schema`.
- `tests/test_export_budget.py` — ⚠ **exceção de faixa, documentada:** o teste
  `test_import_lazy_client_falha_clara_sem_lib` (F0-03) tinha o `skipTest` DENTRO
  de um `try` cujo `except Exception` engolia o `SkipTest` ⇒ falha espúria assim
  que o stack R2 (que ESTE cartão exige) entrou no env-main. Conserto de 1 bloco
  preservando o intent escrito ("lib presente ⇒ skip"); sem ele a regressão
  "unittest verde" do cartão era impossível. Commit separado.

## O que c262/c154 HERDAM — leia isto
1. **Esqueleto do runner** (copie do `run_stubpy`): `pin_runtime()` → `env_info()`
   → `load_doe()` → `FEBudget(D, logger)` + `BoTorchProblemAdapter` → laço de BO
   com `torch_seed_for(semente, ALG_ID, it)` ANTES de modelo+acqf (L.10; ALG_ID
   do `seeds.json`: c262=9, c154=10; usos: c262 0=manual_seed/1=sampler/2=acqf) →
   `except BudgetExhausted` como fim NATURAL do laço (D61) → `write_run_outputs`.
2. **Modelo/aquisição:** train_X = `adapter.to_unit(X_nativo)`; train_Y =
   `adapter.evaluate_unit_max(...)` (JÁ em −f/maximização); outcome transform =
   `adapter.make_standardize()`. Candidatos do `optimize_acqf` → snapshot ③ da
   iteração (`buf.add_surrogate`, μ/σ do posterior sob `no_grad` — D86) →
   `adapter.evaluate_unit_max(cand)` gasta o FE.
3. **pymoo interno** (checagem b do c154): SEMPRE `guarded_pymoo_minimize` (N.1.3).
4. **Fim de iteração:** `del` modelo/acqf/posteriors + `iteration_cleanup()` (D86).
   **Timing §17.6:** capture `n_train = bud.fe` ANTES do infill da iteração e use
   esse valor no `add_timing` — a curva `(n_acumulado, tempo_fit_s)` pareia o fit
   com os pontos que o modelo VIU (1º=11D−1; o stub é o exemplo).
5. **Registro no dispatch:** 1 linha em `experiment._DISPATCH_LOADERS`.
6. **Bucket:** c262/c154 SÃO bucket-only (③) — na VM/M8 rode com
   `enable_bucket=True` (o `dual_write_run` já poda a ③ local após upload). No
   Mac/piloto deixe o default local.

## Pendências / decisões p/ o autor (nenhuma bloqueia c262)
1. **⚠ Integração `experiments.py` × runner (pré-existente do F0-01, fora da
   minha faixa; CONFIRMADO como major pela revisão adversarial):** o `_run_one`
   do despachante escreve um manifesto PRÓPRIO depois do `run()` — sobrescreve o
   do runner e perde `doe_hash`/`fe_final`/`env` (e o jsonl do runner com
   `append=False` trunca o header do despachante; sobra um 2º footer). Agravante:
   `_run_one` **não repassa `data_root` nem `enable_bucket`** ao adapter. No gate
   isso não aparece (o accept chama `experiment.run` direto). **Decidir antes da
   bateria M8 / no c262:** o `_run_one` LER o manifesto do runner e completar
   status/timing em vez de recriar + repassar kwargs. (Mudança pequena em
   `experiments.py` — não fiz: fora da faixa.)
2. **⚠ Resume × bucket-only (pré-existente F0-01×F0-03; CONFIRMADO major):**
   `manifest.is_run_done` exige as 4 camadas LOCAIS, mas a poda da ③ pós-upload
   (D58, `gcs.mirror_run`) as remove p/ os 5 volumosos → um run COMPLETO de
   c262/c154 na VM ficaria "não pronto" e a esteira o re-executaria. O "resume
   dos bucket-only LISTA O BUCKET" (D58) ainda não existe em código. **Decidir
   antes do M8:** `is_run_done` bucket-aware no despachante (aceitar
   `blob_exists` p/ camadas bucket-only). Não morde os pilotos no Mac
   (`enable_bucket=False`).
3. **Sementes idênticas entre problemas (by design):** a fórmula D62/D91 não
   inclui `problema` ⇒ mesmo stream interno p/ (alg, semente, it) em todos os
   problemas; a diferenciação vem do DoE/dados. Conferido contra o `seeds.json` —
   é o especificado; registro para não parecer bug na auditoria do piloto.
4. **Smoke GCS usa o namespace real `experiments/main/stubpy/` de propósito**
   (é o que exercita `mirror_run`/`sync_pending` de verdade; limpeza VERIFICADA
   pós-delete). Não rodar `--gcs-smoke` em 2 máquinas SIMULTANEAMENTE (os blobs
   colidiriam entre si).
5. **`KNOWN_ALGORITHMS` do `experiments.py`** não tem `stubpy` (nem precisa — o
   gate não passa pelo CLI); quando c262 entrar, o roster já o contém.
6. **Lifecycle do bucket** segue pendente (HANDOFF §7.5) — os deletes do smoke
   viram versões non-current até lá.
7. **INDEX:** a linha R2-00-harness fica ⬜ até a torre marcar (paralelismo).

## Como reproduzir
```bash
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY scripts/accept.py R2-00-harness --alg stubpy --problema MMF1 --semente 0   # exit 0
$PY scripts/accept.py R2-00-harness --alg stubpy --problema ZDT1 --semente 0   # exit 0
$PY scripts/accept.py R2-00-harness --alg stubpy --problema MMF1 --semente 0 --gcs-smoke  # rede
$PY -m unittest discover -s tests -t .                                          # 75 OK
```
Saídas do stubpy em `data/experiments/main/stubpy/` (gitignored; regeneráveis).

## Commits desta sessão (branch `experiment/definitive_algorythms`)
⚠ **NADA commitado/staged ainda** (instrução do autor: outra instância ativa no
mesmo repo; a torre coordena o momento). Plano de commit, quando autorizado:
`git add` EXPLÍCITO só da minha faixa, prefixo `[R2-00-harness]` — (1) harness +
wiring + gate + testes novos; (2) commit separado e justificado p/ o conserto do
teste F0-03 (`tests/test_export_budget.py`). Nada do c238 tocado/staged.
