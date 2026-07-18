# R2-00-harness — REPASSE À INSTÂNCIA QUE GEROU AS INSTRUÇÕES

> Relatório de execução completo do cartão **R2-00-harness** (infra transversal
> BoTorch, contrato N.1/§22.3), escrito para a instância que emitiu o prompt
> desta sessão entender **exatamente o que foi feito, como, e com quais
> resultados**. Companheiro dos dois handoffs já no repo:
> `handoff/R2-00-harness.md` (conciso, para a próxima sessão) e
> `handoff/R2-00-harness_RELATORIO-EXECUCAO.md` (narrativa de execução).
>
> **Data:** 2026-07-17 · **Máquina:** Mac (macOS 12.5.1, arm64) · **env-main**
> (`.../mestrado_experimentos_dissertacao/bin/python`) · **Veredito: VERDE ✅**
> (gate objetivo de encanamento; SEM algoritmo, SEM fidelidade — D97).
>
> ⚠ **NADA foi commitado nem staged** (instrução explícita do autor: outra
> instância — o cartão R1-c238/MATLAB — trabalha na MESMA árvore agora; o autor
> avisará o momento do commit). O HEAD do branch avançou durante a sessão por
> commits da outra faixa (c238); nenhum arquivo meu entrou neles.

---

## 0. O QUE O CARTÃO PEDIA vs O QUE FOI ENTREGUE (mapa 1-para-1)

O prompt definia o teste de aceitação: `accept.py R2-00-harness --alg stubpy`
exit 0 (MMF1+ZDT1) + smoke GCS byte-idêntico + regressão Python verde. Tudo
entregue. Mapa item-a-item do contrato N.1/§22.3/L.18:

| Exigência do prompt/contrato | Onde foi implementada | Estado |
|---|---|---|
| BoTorch OFICIAL 0.18.1; fork `Unknown` PROIBIDO (N.2.3); versão+hash no manifesto | `botorch_harness.env_info()` (guarda + sha256 do RECORD) | ✅ |
| `torch.set_num_threads(1)` + float64 + CPU (N.1.1/D79) | `pin_runtime()` + env vars no topo do módulo | ✅ |
| Salvar/restaurar RNG global em volta de `pymoo.minimize` (N.1.3) | `preserve_global_rng()` / `guarded_pymoo_minimize()` | ✅ |
| Adapter normalize/unnormalize [0,1]↔nativo + `−f` + Standardize de Y (§5.5) | `BoTorchProblemAdapter` (usa `botorch.utils.transforms`) | ✅ |
| `torch.manual_seed(h(run,it))` ANTES de modelo+acqf (L.10) | `torch_seed_for()`, chamado no topo da iteração | ✅ |
| Snapshot por iteração de BO (§17.3/§17.6) | `SnapshotBuffer` (②③+timing/iteração) | ✅ |
| Versão do scipy no manifesto (L.18) | `env_info()['scipy']` → manifesto | ✅ |
| Sementes internas via `SeedSequence` (D62/D91, seeds.json) | `iteration_seed()` (fórmula do artefato, trunc 32b) | ✅ |
| Higiene torch: no_grad + del/gc por iteração (D86/N.1.5) | `iteration_cleanup()` + `no_grad` na predição | ✅ |
| DoE carregado do artefato, NUNCA regenerado (D63/D87/D88) | `load_doe()` (hash=sidecar; ausente/corrompido ⇒ pára) | ✅ |
| Orçamento pelo FEBudget: cache-hit=0 FE (D89), BudgetExhausted (D61) | adapter amarra toda avaliação ao `FEBudget` (reuso F0-03) | ✅ |
| Export 4 camadas via `export.py` (§17.2, reuso, não duplicar) | `write_run_outputs()` | ✅ |
| Dual-write local+bucket construído aqui, reusado pela R3 (§17.7) | `dual_write_run()` (usa `gcs.mirror_run`, reuso F0-03) | ✅ |
| Wiring `ALGORITHM_DISPATCH`/`run()` sem tocar `experiments.py` | `experiment._DISPATCH_LOADERS` (lazy) + corpo de `run()` | ✅ |
| Branch R2-00 ADITIVO no `accept.py`, D97 intacto | `check_r2_00` + `_r2_00_gcs_smoke` + branch em `main()` | ✅ |
| STUB `stubpy` ponta-a-ponta (NUNCA `stub` = R1-00) | `run_stubpy()` | ✅ |
| Smoke GCS real COM LIMPEZA (o deferido do F0-03) | `_r2_00_gcs_smoke` (flag `--gcs-smoke`) | ✅ |

**Fora de escopo por desenho (confirmado):** nenhum algoritmo (c262/c154), nenhum
julgamento de fidelidade (D97), nenhuma métrica. A bateria bucket-only plena e o
pinning por subprocess (D79) são da bateria M8/VM — aqui provados no caminho
Mac/local + 1 smoke real.

---

## 1. VERIFICAÇÃO DE AMBIENTE (gate bloqueante D80/D81 — ANTES de qualquer código)

Rodado primeiro, como o prompt exige (PARE se falhar):
```
PY -c "import numpy,pandas,pyarrow,pymoo,botorch,gpytorch,torch,deap; from google.cloud import storage; print(...)"
→ botorch 0.18.1 · torch 2.11.0 · pymoo 0.6.2 · gpytorch 1.15.2 · scipy 1.17.1   (exit 0)
PY -c "...bucket('mestrado_experiments').exists()"  → True                        (exit 0)
```
- `botorch.__version__ == "0.18.1"` = OFICIAL (o fork do device reporta
  `"Unknown"` — N.2.3). pymoo 0.6.2 ✓. **Nada instalado** (pins = decisão do
  autor, D80/D81). Ambiente VERDE → prosseguir autorizado.

## 2. LEITURA DE CONTEXTO (Passo 0 do prompt, na ordem, e só ela)

`HANDOFF_MESTRE.md` (§10/§11) · `handoff/F0-03-export.md` (o contrato de REUSO de
budget/export/gcs + o smoke GCS que o F0-03 DEFERIU a este cartão) ·
`handoff/R1-00-harness.md` (o espelho MATLAB) · `claude_code_context/CLAUDE.md` ·
a linha R2-00 do `cards/INDEX.md` (só leitura) · **`20_rodada2_botorch/
00_contrato_rodada2.md` INTEIRO** (N.1/§22.3/L.18) · `00_fundacao/
01_regras_globais.md` (incl. Anexo D §D.3 D53–D100) · `00_fundacao/
03_contrato_export.md` (§17). Consultas dirigidas: `artifacts/seeds.json` (fórmula
D91 + catálogo `uso_id` c262/c154 + a nota "truncar p/ 32 bits onde a API exigir");
assinaturas de `src/doe.py`, `src/problems.py`, `src/budget.py`, `src/export.py`,
`src/gcs.py`, `src/manifest.py`, `src/audit_log.py`, `src/naming.py`,
`src/experiment.py`, `experiments.py`, `scripts/accept.py`; `.gitignore`.

## 3. DECISÕES DE PROJETO (as 5 do Passo 1, com o porquê)

1. **Despacho LAZY em `src/experiment.py`.** O check de andaime do F0-01 exige
   `ALGORITHM_DISPATCH` **vazio no import** (e o módulo tem de importar no
   `python3` base, sem torch). Registrei um mapa de strings
   `_DISPATCH_LOADERS = {'stubpy': ('src.botorch_harness','run_stubpy','botorch')}`
   e um `_resolve_dispatch()` que importa/cacheia na 1ª chamada de `run()`.
   Resultado: F0-01 verde por processo, `import src.experiment` leve, `experiments.py`
   **INTOCADO** (ele já chamava `_adapter.run`), c262/c154 = 1 linha nova.
2. **Pinning D79 em duas camadas, declarado.** Env vars
   (`OMP/OPENBLAS/MKL/NUMEXPR=1`) no TOPO de `botorch_harness.py` antes do
   `import torch`; `pin_runtime()` aplica threads=1/float64/CPU e devolve o estado,
   que vai ao manifesto. O pinning AUTORITATIVO da bateria continua o subprocess
   do D79 (M8) — documentado no docstring, não mascarado.
3. **Cache-hit D89 pelo caminho unit-cube.** `normalize/unnormalize` não é
   bit-exato em geral, mas a des-normalização é DETERMINÍSTICA ⇒ a mesma `u` dá o
   mesmo X nativo bit-a-bit ⇒ cache-hit. O stub prova os DOIS caminhos (U repetida
   = o real do BoTorch; X nativa do DoE re-avaliada) + o hit pós-esgotamento.
4. **Hard-stop NATURAL.** O stub itera até o `BudgetExhausted` subir do ponto
   único de avaliação (D61) — exatamente o `except BudgetExhausted` que c262/c154
   herdam como fim limpo de laço.
5. **Smoke GCS opt-in (`--gcs-smoke`), com limpeza verificada.** O gate padrão é
   offline-determinístico; o smoke real (rede) é flag explícita, com limpeza
   derivada do PLANO de blobs e VERIFICADA pós-delete.

## 4. ARQUIVOS (o que cada um ganhou)

**Novos (minha faixa):**
- `src/botorch_harness.py` (691 linhas) — o harness transversal N.1. Peças:
  `pin_runtime` · `env_info` (guarda N.2.3 + sha256 do RECORD + scipy L.18) ·
  `iteration_seed`/`torch_seed_for` (fórmula EXATA do seeds.json; trunc 32b; L.10) ·
  `preserve_global_rng`/`guarded_pymoo_minimize` (N.1.3) · `iteration_cleanup` (D86) ·
  `load_doe` (D63/D87/D88) · `BoTorchProblemAdapter` (§5.5) · `SnapshotBuffer`
  (§17.3/§17.6) · `write_run_outputs` (4 camadas + CP-init afirmado + manifesto) ·
  `dual_write_run` (§17.7, reuso R3) · `run_stubpy` (o STUB ponta-a-ponta).
- `tests/test_botorch_harness.py` (213 linhas) — 13 testes de unidade (pinning;
  guarda N.2.3 + pin `==0.18.1`; fórmula D91 bit-a-bit; determinismo L.10; N.1.3;
  load_doe ausente/corrompido; bijeção+sinal+hard-stop+Standardize média0/desvio1;
  buffer; wiring lazy). Pulam sem torch/botorch (python3 base).
- `handoff/R2-00-harness.md`, `handoff/R2-00-harness_RELATORIO-EXECUCAO.md`, e este.

**Modificados (minha faixa):**
- `src/experiment.py` — registro lazy + corpo real de `run()`
  (`runner(exp, alg, problema, semente, **kwargs)`). `ALGORITHM_DISPATCH` vazio no
  import.
- `scripts/accept.py` — branch ADITIVO `R2-00` (`check_r2_00` 15 checks +
  `_r2_00_gcs_smoke` + flag `--gcs-smoke` + guarda anti-`--alg stub`). Zero branch
  existente alterado; D97 intacto. Reusa `check_fe`/`check_outputs`/
  `_check_export_schema`.
- `tests/test_export_budget.py` — ⚠ **exceção de faixa, 1 bloco, justificada:** o
  teste `test_import_lazy_client_falha_clara_sem_lib` (do F0-03) tinha o `skipTest`
  DENTRO de um `try` cujo `except Exception` engolia o `SkipTest` (que herda de
  Exception) ⇒ falha espúria assim que o `google-cloud-storage` entrou no env-main
  (dependência que ESTE cartão exige). Conserto preserva o intent escrito ("lib
  presente ⇒ skip"). Sem ele, a regressão "unittest verde" era impossível. **Pede
  sign-off do autor** — commit separado no plano.

## 5. RESULTADOS DE EXECUÇÃO (todos re-rodados ao vivo no fechamento)

1. **Ambiente:** botorch 0.18.1 oficial, GCS `exists()==True`.
2. **`unittest tests.test_botorch_harness`** → **13/13 OK**.
3. **Gate MMF1 (D=2)** → **exit 0, 15/15 checks**: FE=61 · cache-hit×3 (unit/nativa/
   pós) · hard-stop · schema §17.2 (D/M re-derivados do problema canônico) · CP-init
   `89b8ce4e…`=sidecar · pinning `{threads:1,float64,cpu,env=1}` · rng_guard · sementes
   `[2353700321,2139298428,103646281]` == re-derivadas direto do numpy · sinal+standardize ·
   jsonl 86 recs (3 guards cache_hit, cache_hits jsonl/manifesto/runner = 3/3/3) ·
   env botorch=0.18.1/scipy=1.17.1 + fit_series 40 pts · plano bucket 6 artefatos.
4. **Gate ZDT1 (D=30)** → **exit 0, 15/15 checks**: FE=929, fit_series 600 pts.
5. **Smoke GCS real** (`--gcs-smoke`) → **exit 0**: 6 blobs byte-idênticos (sha256),
   sync_pending re-subiu 1, 6 deletados **verificado pós-delete**;
   `list_blobs(prefix='experiments/main/stubpy/')` → **0 resíduos**.
6. **Regressão:** F0-01/02/03/04 → exit 0 (4×); preflight → exit 0.
7. **Suíte completa:** `unittest discover` → **75 OK (1 skip legítimo)**.
8. **python3 base:** `import src.experiment` leve, 25 problemas, dispatch vazio ✓.
9. **Auditoria pyarrow** (runs em `data/experiments/main/stubpy/`, gitignored):
   MMF1 → ①61/②61/③82/timing40; ZDT1 → ①929/②929/③1202/timing600; schemas §17.2
   exatos, ZSTD, ① init=11D−1/opt=20D cravados, `solution_id` único, ③ com C1 (μ E
   classe) e `real_solution_id` nullable; §17.6 `n_acumulado` 1º=11D−1, último=31D−2.

## 6. REVISÃO ADVERSARIAL (4 lentes independentes + adjudicação)

Após a implementação, 4 revisores independentes (correção do harness ·
conformidade N.1 · faixa/aditividade · qualidade do gate), com acesso ao repo e
aos contratos; cada achado adjudicado por mim contra o código.

- **Contrato N.1 — 10/10 ✓** (evidência arquivo:linha dos dois lados).
- **Faixa/aditividade — LIMPO** (zero diff em módulos F0/proibidos; `accept.py`
  aditivo puro; dispatch vazio empírico; `stub/` do R1-00 intocado por mtime).
- **8 endurecimentos APLICADOS** (gate/smoke/testes) + **1 fix no harness** — todos
  re-validados:
  1. Limpeza do smoke derivada do PLANO (não do progresso do loop) + backstop no
     `finally` → falha no MEIO do `mirror_run` não vaza mais blob.
  2. Mensagem de sucesso do smoke só afirma o que foi VERIFICADO pós-delete
     (`blob_exists` após deleção; resíduo ⇒ FAIL).
  3. Check de sementes des-tautologizado: o gate re-deriva a fórmula do seeds.json
     DIRETO do numpy e compara com as sementes que o runner usou.
  4. jsonl blindado (malformado ⇒ FAIL, não crash) + exige ≥3 guards `cache_hit`
     cruzados com `cache_hits` do manifesto-em-disco e do runner.
  5. Schema §17.2 validado com D/M re-derivados do problema canônico (anti-circular).
  6. Rótulo honesto: "run pronto p/ o skip do despachante" (o skip é do despachante).
  7. Exceção no smoke (auth/rede) vira FAIL com o relatório dos 15 checks preservado.
  8. Testes: `test_standardize` afere desvio 1; `test_env_info` pina `== 0.18.1`.
  9. **[fix harness]** `n_acumulado` da série §17.6 estava +1 (lia o FE DEPOIS do
     infill) → capturo ANTES; auditoria confirma 1º=11D−1, último=31D−2.
- **3 pontos DOCUMENTADOS sem mudança** (decisão consciente): o smoke usa o
  namespace real `experiments/main/stubpy/` de propósito (é o que exercita
  `mirror_run`/`sync_pending` de verdade; não colide com config do estudo; limpeza
  verificada) — não rodar `--gcs-smoke` em 2 máquinas simultâneas; a evidência dos
  3 cenários de cache-hit continua majoritariamente do runner (agora cruzada com
  jsonl+manifesto); o pin `==0.18.1` cobre a versão.

## 7. DOIS MAJORS DE INTEGRAÇÃO PRÉ-EXISTENTES (fora da minha faixa — decisão do autor antes do M8)

A revisão de correção apontou **2 problemas no despachante `experiments.py`
(código do F0-01, NÃO da minha faixa)** que não aparecem no gate (o `accept.py`
chama `experiment.run` direto), mas mordem a bateria real. NÃO os consertei —
estão fora da faixa; registro para decisão:

1. **`_run_one` clobbera o manifesto/jsonl do runner.** Depois do `run()`, o
   `_run_one` grava um `new_manifest(status='ok', ...)` **sem** `doe_hash`/
   `fe_final`/`env`/`fit_series` por cima do manifesto rico que o `write_run_outputs`
   acabou de escrever; e o logger do runner (`append=False`) trunca o header que o
   despachante já abriu no mesmo `.jsonl` (sobra um 2º footer). Além disso, `_run_one`
   **não repassa `data_root`/`enable_bucket`** ao adapter. **Efeito:** com a bateria
   despachada por `experiments.py`, o manifesto persistido perde a evidência do
   CP-init (D88) e do orçamento (D21), e o dual-write nunca liga. **Sugestão:**
   `_run_one` LER o manifesto do runner e completar status/timing (não recriar) +
   repassar kwargs.
2. **Resume × bucket-only quebrado.** `manifest.is_run_done` exige as 4 camadas
   LOCAIS presentes; mas a poda da ③ pós-upload (D58, `gcs.mirror_run`) remove a
   local dos 5 volumosos (c154/c122/e81/c149/c262). **Efeito:** um run COMPLETO de
   c262/c154 na VM fica "não pronto" para sempre → a esteira o re-executa
   eternamente. O "resume dos bucket-only LISTA O BUCKET" prometido pela D58 ainda
   não existe em código. **Sugestão:** `is_run_done` bucket-aware (aceitar
   `blob_exists` p/ camadas bucket-only). Não morde os pilotos no Mac
   (`enable_bucket=False`).

## 8. FAIXA / PARALELISMO (coexistência com o c238)

- Toquei SÓ minha faixa + 1 exceção documentada (o teste F0-03). Zero `.m`, zero
  `algorithms/**`, zero módulos F0 editados, `cards/INDEX.md` NÃO marcado (a torre
  marca no merge).
- `git diff` dos módulos F0 e arquivos proibidos = **vazio** (confirmado pela lente
  de faixa). O diff do `anchors.json` que aparece no working tree é 100% da faixa
  c238 (âncora do EIM) — não toquei.
- Token do STUB = **`stubpy`** em todo lugar; os artefatos MATLAB do R1-00 em
  `data/experiments/main/stub/` (mtime 16/jul) estão intocados.
- **NADA staged, NADA commitado.** HEAD avançou por commits da faixa c238 durante a
  sessão; nenhum arquivo meu neles.

## 9. PLANO DE COMMIT (quando o autor autorizar — `git add` explícito, NUNCA -A)

1. `[R2-00-harness]` → `src/botorch_harness.py`, `src/experiment.py`,
   `scripts/accept.py`, `tests/test_botorch_harness.py`, `handoff/R2-00-harness.md`,
   `handoff/R2-00-harness_RELATORIO-EXECUCAO.md`, este arquivo.
2. `[R2-00-harness]` (separado, justificado) → `tests/test_export_budget.py`
   (conserto do `SkipTest` engolido no teste F0-03 — pede sign-off).

## 10. O QUE A PRÓXIMA SESSÃO (c262) HERDA

Esqueleto do runner = copiar `run_stubpy`: `pin_runtime` → `env_info` →
`load_doe` → `FEBudget(D,logger)` + `BoTorchProblemAdapter` → laço com
`torch_seed_for(semente, ALG_ID, it)` ANTES de modelo+acqf (ALG_ID do seeds.json:
c262=9, c154=10) → `except BudgetExhausted` = fim → `write_run_outputs`. train_X =
`adapter.to_unit(X)`; train_Y = `evaluate_unit_max(...)` (já −f); outcome =
`adapter.make_standardize()`. pymoo interno = `guarded_pymoo_minimize`. Fim de
iteração = `del` + `iteration_cleanup()`. Timing §17.6: `n_train = bud.fe` ANTES do
infill. Registrar 1 linha em `_DISPATCH_LOADERS`. c262/c154 SÃO bucket-only —
`enable_bucket=True` na VM/M8 (o `dual_write_run` já poda a ③). Antes do M8, os 2
majors da §7 precisam de decisão.
