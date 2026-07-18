# R2-00-harness — RELATÓRIO DE EXECUÇÃO (narrativa completa p/ a torre de controle)

> **Propósito.** Descreve, passo a passo, TUDO o que a sessão do cartão
> **R2-00-harness** executou: verificação de ambiente, leitura de contexto, decisões
> de projeto, implementação e — o mais importante para o veto do autor — **cada
> comando rodado e o resultado exato obtido**. Companheiro do handoff conciso
> `handoff/R2-00-harness.md`.
>
> **Data:** 2026-07-17 · **Máquina:** Mac (macOS 12.5.1, arm64) — decisão do autor:
> tudo no Mac até o M7; VM só M8+ · **Veredito final: VERDE ✅** (gate objetivo de
> encanamento; SEM algoritmo, SEM fidelidade — D97).
>
> ⚠ **Sessão em PARALELISMO DE FAIXAS** com o R1-c238 (MATLAB) na mesma árvore de
> trabalho. **NADA foi commitado nem staged por esta sessão** (instrução do autor:
> a torre coordena o momento do commit). O working tree contém as duas faixas.

---

## 0. TL;DR (resposta à pergunta "está 100% pronta?")

- **Sim, para o escopo do cartão R2-00** (infra TRANSVERSAL BoTorch + gate objetivo
  de encanamento + smoke GCS real), **validado rodando código**, não por inspeção:
  gate `accept.py R2-00-harness` **exit 0 em MMF1 (D=2) e ZDT1 (D=30)**, com 15
  checks cada; **smoke GCS REAL verde com limpeza comprovada (0 blobs residuais)**;
  regressão Python completa verde (F0-01..04, preflight, 75 testes unittest).
- **Ressalvas de escopo (por desenho, não lacunas):**
  1. **Nenhum algoritmo roda no R2-00** — c262/c154 são os próximos cartões. A prova
     é o run-STUB `stubpy` (proposta de infill por sorteio torch semeado), espelho
     Python do STUB MATLAB do R1-00.
  2. **Bucket-only pleno** (poda da ③ dos 5 volumosos) só se exercita na bateria
     M8/VM — aqui o dual-write foi provado com o stubpy (que não é bucket-only) e a
     poda existe no código reusado (`gcs.mirror_run`, F0-03).
  3. **1 pendência de integração PRÉ-EXISTENTE documentada** (fora da minha faixa):
     o `_run_one` do `experiments.py` sobrescreve o manifesto do runner (§7 abaixo).
- **Zero regressão** · **zero item fora da faixa staged** · 1 conserto documentado
  de teste F0-03 (bug latente exposto pelo env R2 que este cartão exige).

---

## 1. VERIFICAÇÃO DE AMBIENTE (gate bloqueante D80/D81 — ANTES de tudo)

**Comando 1** — imports + versões no env-main:
```
PY -c "import numpy,pandas,pyarrow,pymoo,botorch,gpytorch,torch,deap; \
       from google.cloud import storage; print(...)"
→ botorch 0.18.1 · torch 2.11.0 · pymoo 0.6.2 · gpytorch 1.15.2      (exit 0)
```
- **botorch.__version__ == "0.18.1"** → é o OFICIAL (o fork do device reporta
  `"Unknown"` — N.2.3). **pymoo 0.6.2** ✓. Nada instalado (D80/D81).

**Comando 2** — GCS via ADC do Mac:
```
PY -c "from google.cloud import storage; print(storage.Client().bucket('mestrado_experiments').exists())"
→ True                                                                (exit 0)
```
**→ Ambiente VERDE. Prosseguir autorizado.** Nota: o `git status` inicial mostrava a
faixa do c238 em andamento (`algorithms/c238_EIM/*.m`, `src/experiment.m`,
`anchors.json`) — arquivos jamais tocados por esta sessão. O c238 mexe em
`src/experiment.m`; minha faixa é `src/experiment.py` — **sem colisão**.

## 2. LEITURA DE CONTEXTO (Passo 0, na ordem prescrita, e somente ela)

HANDOFF_MESTRE (§10/§11) · handoff/F0-03-export.md (contrato de reuso
budget/export/gcs + o smoke GCS deferido) · handoff/R1-00-harness.md (o espelho
MATLAB) · claude_code_context/CLAUDE.md · linha R2-00 do cards/INDEX.md (só
leitura) · **20_rodada2_botorch/00_contrato_rodada2.md INTEIRO** (N.1/§22.3/L.18) ·
00_fundacao/01_regras_globais.md · 00_fundacao/03_contrato_export.md (§17).
Consultas dirigidas: `artifacts/seeds.json` (fórmula D91 + catálogo uso_id c262/
c154 + **"truncar p/ 32 bits onde a API exigir (torch.manual_seed, pymoo seed)"**),
assinaturas de `src/doe.py`/`src/problems.py`, `.gitignore` (data/experiments/ ✓).

## 3. DECISÕES DE PROJETO (as 5 que moldaram a implementação)

1. **Despacho LAZY em `src/experiment.py`.** O check do F0-01 exige
   `ALGORITHM_DISPATCH` **vazio no import**; registrar o stubpy no módulo o
   quebraria. Solução: `_DISPATCH_LOADERS` (strings `alg → (módulo, fn, stack)`,
   sem import pesado) + `_resolve_dispatch()` que importa/cacheia na 1ª chamada de
   `run()`. Ganhos: F0-01 segue verde por processo; `import src.experiment`
   continua leve (python3 base); c262/c154 = 1 linha. `experiments.py` INTOCADO
   (ele já chama `_adapter.run`).
2. **Pinning D79 em duas camadas, com honestidade.** As env vars
   (`OMP/OPENBLAS/MKL/NUMEXPR=1`) são setadas NO TOPO de `botorch_harness.py`,
   antes do `import torch`; `pin_runtime()` aplica o que é runtime
   (`torch.set_num_threads(1)`, float64 default, CPU) e devolve o estado, que vai
   ao manifesto. O pinning AUTORITATIVO da bateria continua sendo o subprocess do
   D79 (despachante/M8) — documentado, não mascarado.
3. **Cache-hit D89 pelo caminho unit-cube.** `normalize→unnormalize` NÃO é
   bit-exato em geral; o que a D89 garante é que a des-normalização é
   determinística ⇒ a MESMA `u` produz o MESMO X nativo. O stub prova o cache-hit
   dos DOIS jeitos: U repetida (o caminho BoTorch real) e X nativa re-avaliada
   (o caminho do DoE) — e ainda o hit pós-esgotamento (livre, D89).
4. **Hard-stop NATURAL no laço.** O stub não conta 20D e para: ele itera até o
   `BudgetExhausted` subir do ponto único de avaliação (D61) — exatamente o fluxo
   de controle que c262/c154 herdarão (`except BudgetExhausted` = fim limpo).
5. **Smoke GCS opt-in (`--gcs-smoke`).** O gate padrão é offline-determinístico
   (CI/bateria); o smoke real (rede) é flag explícita, com **limpeza em `finally`**
   (deleta os blobs de teste mesmo em falha).

## 4. IMPLEMENTAÇÃO (o que cada arquivo ganhou)

- **`src/botorch_harness.py` (novo, ~550 linhas):** `pin_runtime` · `env_info`
  (guarda N.2.3 + sha256 do RECORD do botorch + scipy L.18) · `iteration_seed`/
  `torch_seed_for` (fórmula EXATA do seeds.json; trunc 32b; L.10) ·
  `preserve_global_rng`/`guarded_pymoo_minimize` (N.1.3) · `iteration_cleanup`
  (D86) · `load_doe` (D63: carrega, confere hash, NUNCA regenera) ·
  `BoTorchProblemAdapter` (§5.5: normalize/unnormalize do botorch, −f,
  Standardize, avaliação direta problems.py→FEBudget) · `SnapshotBuffer` (②③/
  timing por iteração de BO — §17.3/§17.6) · `write_run_outputs` (4 camadas via
  export.py; **CP-init afirmado**: hash≠sidecar ⇒ RuntimeError; manifesto com
  doe_hash/env/pinning/fit_series) · `dual_write_run` (mirror_run + upload_status
  re-subido) · `run_stubpy` (o STUB ponta-a-ponta).
- **`src/experiment.py`:** cabeçalho + bloco de despacho substituídos pelo
  registro lazy; `run()` ganhou corpo real (resolve → chama
  `runner(exp, alg, problema, semente, **kwargs)`).
- **`scripts/accept.py` (ADITIVO):** `check_r2_00` (15 checks), `_r2_00_gcs_smoke`,
  branch `R2-00` no `main()`, flag `--gcs-smoke`, guarda anti-`--alg stub`
  (protege os artefatos MATLAB do R1-00). Reusa `check_fe`/`check_outputs`/
  `_check_export_schema`. **Nenhum branch existente alterado; D97 intacto.**
- **`tests/test_botorch_harness.py` (novo):** 13 testes de unidade (pulam sem
  torch/botorch).
- **`tests/test_export_budget.py` (⚠ exceção de faixa, 1 bloco):** o
  `test_import_lazy_client_falha_clara_sem_lib` do F0-03 engolia o `SkipTest` num
  `except Exception` ⇒ falha espúria assim que o `google-cloud-storage` entrou no
  env-main (exigência DESTE cartão). Conserto preserva o intent escrito do teste
  ("lib presente ⇒ skip"). Sem ele, a regressão "unittest verde" era impossível.

## 5. EXECUÇÕES E RESULTADOS EXATOS (todas verdes)

1. `PY -m unittest tests.test_botorch_harness -v` → **13/13 OK** (0,9 s).
2. `PY scripts/accept.py R2-00-harness --alg stubpy --problema MMF1 --semente 0`
   → **VERDE, exit 0** — FE=61 (D=2), hits=3 (unit/nativa/pós ✓), hard_stop ✓,
   schema §17.2 ✓, CP-init `89b8ce4e…`=sidecar ✓, pinning `{threads:1, float64,
   cpu, env=1}` ✓, rng_guard ✓, seeds `[2353700321, 2139298428, 103646281]` ✓,
   sign/standardize ✓, jsonl 86 recs (guards cache_hit+hard_stop) ✓, env
   botorch=0.18.1/scipy=1.17.1 + fit_series 40 pts ✓, plano bucket 6 artefatos ✓.
3. Idem **ZDT1** → **VERDE, exit 0** — FE=929 (D=30), fit_series 600 pts, jsonl
   1206 recs; 32 s total.
4. **SMOKE GCS REAL** (`--gcs-smoke`, MMF1): **VERDE** — “6 blobs byte-idênticos
   (sha256) · sync_pending re-subiu 1 · 6 blobs de teste deletados”.
5. Verificação independente de resíduo:
   `list_blobs(prefix='experiments/main/stubpy/')` → **0 blobs**.
6. Regressão: `accept.py F0-01|F0-02|F0-03|F0-04` → **exit 0 (4×)** ·
   `preflight.py` → **exit 0**.
7. `PY -m unittest discover -s tests -t .` → 1 falha **pré-existente** (o teste
   F0-03 do §4) → conserto → **75 OK (1 skip legítimo)**.
8. Runs stubpy em `data/` (gitignored, p/ inspeção do autor):
   **MMF1 → FE 61/61, 40 iters, 2,1 s · ZDT1 → FE 929/929, 600 iters, 28,4 s.**
9. **Auditoria pyarrow** das saídas: schemas §17.2 EXATOS nas 4 camadas, codec
   ZSTD, ① com init=11D−1 e opt=20D cravados e `solution_id` único, ③ com C1
   (μ=81/1201 linhas, classe=1) e `real_solution_id` nullable (NULL=42/602).
10. **Revisão adversarial multi-agente** (4 lentes: correção, contrato,
    faixa/paralelismo, qualidade do gate → verificação adversarial por achado) —
    resultado na seção 8.

## 6. SEMENTES — nota de auditoria (não é bug)

As sementes por iteração são IDÊNTICAS entre problemas (MMF1 e ZDT1 mostram o
mesmo `seeds[:3]`): a fórmula vinculante D62/D91 é
`SeedSequence((base, alg_id, iteracao, uso_id))` — **sem `problema` na entropia**.
A diferenciação entre problemas vem do DoE/dados. Conferido bit-a-bit contra o
`seeds.json` (teste `test_iteration_seed_matches_seeds_json_formula`).

## 7. PENDÊNCIA DE INTEGRAÇÃO PRÉ-EXISTENTE (decisão p/ o autor antes do M8/c262)

O `_run_one` do `experiments.py` (F0-01) grava um manifesto PRÓPRIO **depois** do
`run()` do adapter — sobrescrevendo o manifesto rico do runner (perde `doe_hash`,
`fe_final`, `env`); e o logger do runner (`append=False`) trunca o header que o
despachante escreveu no mesmo `.jsonl`. O gate não passa por esse caminho (o
`accept.py` chama `experiment.run` direto), mas a bateria via `experiments.py`
sim. **Sugestão (1 mudança pequena em `experiments.py`, FORA da minha faixa — não
fiz):** o `_run_one` ler o manifesto que o runner gravou e completar
status/n_retries/timing em vez de recriar do zero. Registrado também no handoff.

## 8. REVISÃO ADVERSARIAL (multi-agente) — resultado

4 revisores independentes (lentes: correção do harness · conformidade N.1 ·
faixa/aditividade · qualidade do gate), cada um com acesso ao repo e aos
contratos; achados adjudicados por mim contra o código. *(1ª tentativa via
workflow morreu silenciosamente — relançada como 4 agentes diretos.)*

**Lente contrato N.1 — NENHUM ACHADO.** Os 10 itens (N.1.1, N.1.3, N.2.3, L.10,
L.18, §5.5, §17.3, §17.7, fórmula seeds.json, D86) verificados item a item com
evidência arquivo:linha dos dois lados.

**Lente faixa/aditividade — LIMPO.** Zero diff nos módulos F0/arquivos proibidos;
`accept.py` provadamente aditivo puro (zero linhas removidas); dispatch vazio no
import (empírico); `stub/` do R1-00 intocado (mtimes). 3 notas operacionais:
conserto do teste F0-03 pede sign-off do autor (§4); commit por caminho explícito
(o plano); resíduo `data/experiments/main/stubpy/` intencional e gitignored.

**Lente correção — 2 majors de INTEGRAÇÃO (fora da faixa, viram §7/§10) + 2
pontos no código da faixa:**
- *(major, pré-existente)* o clobber do manifesto/jsonl pelo `_run_one` (§7) —
  agravado pelo fato de `_run_one` não repassar `data_root`/`enable_bucket`.
- *(major, pré-existente)* **resume × bucket-only quebrado**: `is_run_done` exige
  as 4 camadas LOCAIS; a poda da ③ pós-upload (D58) torna um run COMPLETO de
  c262/c154 "não pronto" → a esteira o re-executaria eternamente. O "resume
  lista o bucket" (D58) ainda NÃO existe em código. Decisão do autor antes do
  M8 (§10).
- *(minor, CORRIGIDO)* `n_acumulado` da série §17.6 deslocado de +1 (lia o FE
  DEPOIS do infill) — corrigido: captura ANTES; auditoria pós-fix confirma
  1º=11D−1 e último=31D−2 nos 2 problemas.
- *(conforme a SPEC, sem mudança)* falha de rede após manifesto `ok` deixa o
  espelho incompleto porém detectável (`upload_status=pending`) e recuperável
  por `sync_pending` — é a letra do §17.7 ("local-first; sync posterior completa").

**Lente qualidade do gate — 11 achados; 8 CORRIGIDOS, 3 decisões documentadas:**
- ✔ *(major)* limpeza do smoke agora deriva do PLANO (não do progresso do loop) —
  falha no MEIO do `mirror_run` não vaza mais blob; backstop no `finally`.
- ✔ *(major)* a mensagem de sucesso só afirma o que foi VERIFICADO pós-delete
  (`blob_exists` após a deleção; resíduo ⇒ FAIL).
- ✔ *(major)* check de sementes des-tautologizado: o gate re-deriva a fórmula do
  seeds.json DIRETO do numpy e compara com as sementes usadas.
- ✔ *(minor)* jsonl blindado (malformado ⇒ FAIL, não crash) + exige ≥3 guards
  `cache_hit` + cruza `cache_hits` jsonl×manifesto-em-disco×runner.
- ✔ *(minor)* schema §17.2 validado com D/M re-derivados do problema canônico
  (anti-circular) + check de que o adapter reporta os mesmos.
- ✔ *(minor)* rótulo honesto: "run pronto p/ o skip do despachante" (o skip em si
  é do despachante — F0-01).
- ✔ *(minor)* exceção no smoke (auth/rede) vira FAIL com o relatório dos 15
  checks preservado.
- ✔ *(minor ×2, testes)* `test_standardize` agora afere desvio 1;
  `test_env_info` pina `== 0.18.1` (N.2.3/D80).
- ✖ *(documentado, sem mudança)* o smoke usa o namespace real
  `experiments/main/stubpy/` de propósito: é o que exercita `mirror_run`/
  `sync_pending` DE VERDADE; `stubpy` nunca colide com config do estudo, e a
  limpeza é verificada. Dois smokes SIMULTÂNEOS colidiriam entre si — não rodar
  `--gcs-smoke` em 2 máquinas ao mesmo tempo (nota no handoff).
- ✖ *(documentado)* a evidência de cache-hit segue majoritariamente do runner
  (agora cruzada com jsonl+manifesto); a distinção fina dos 3 cenários só existe
  no runner — aceito (o unittest cobre a primitiva no FEBudget).
- ✖ *(já coberto)* o pin `==0.18.1` do gate + teste; ver acima.

**Pós-correções, TUDO re-rodado:** 13 testes do harness OK · gate MMF1 e ZDT1
exit 0 · smoke GCS verde com "deletado (verificado pós-delete)" e 0 resíduo ·
F0-01..04 + preflight exit 0 · suíte completa 75 OK (1 skip) · python3 base leve.

## 9. DECISÕES DO AUTOR ANTES DO M8 (levantadas pela revisão; fora da faixa R2-00)

1. **`experiments.py::_run_one` × runner** (§7): clobber de manifesto/jsonl +
   não-repasse de `data_root`/`enable_bucket`. Sugestão: `_run_one` ler/completar
   o manifesto do runner; repassar kwargs.
2. **Resume bucket-aware (D58):** `is_run_done` exige camadas locais; a poda da
   ③ dos 5 volumosos quebra o resume na VM. Sugestão: `is_run_done` (ou um
   irmão bucket-aware no despachante) aceitar `blob_exists` p/ camadas
   bucket-only — o "resume lista o bucket" prometido pela D58.

## 10. O QUE NÃO FOI FEITO (e por quê)

- `cards/INDEX.md` **não tocado** (a torre marca no merge — instrução da sessão).
- Nenhum commit/stage (instrução do autor: outra instância ativa no repo; a torre
  coordena o momento).
- Nenhum pin instalado, nenhuma definição inventada, nenhum julgamento de
  fidelidade (D80/D81/D97).
- Os gates R1-* não foram rodados (faixa do c238 ativa; a torre roda no merge).
