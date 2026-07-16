# RELATÓRIO DE EXECUÇÃO — cartão F0-03-export

> Narrativa completa da sessão (para a torre de controle / a instância que emitiu as
> instruções). Descreve **cada etapa executada, na ordem, e o resultado concreto de
> cada uma** — para auditar exatamente o que foi feito, como, e o que foi atingido.
> **Data:** 2026-07-16 · **Branch:** `experiment/definitive_algorythms` · **Env:** env-main.

---

## 0. Sumário executivo (TL;DR)

- **Objetivo do cartão:** o 3º dos 4 da Fase 0 — **infraestrutura pura** (SEM algoritmo,
  SEM métrica, SEM fidelidade): o **wrapper de FE** (orçamento), os **escritores das 3
  camadas de export + timing**, e a **ponte GCS** (dual-write). D97: só encanamento.
- **Entregue:** `src/budget.py`, `src/export.py`, `src/gcs.py` (novos), `scripts/accept.py`
  (branch F0-03), `tests/test_export_budget.py` (novo), `cards/INDEX.md` (✅), 2 handoffs.
- **Gate:** `PY scripts/accept.py F0-03-export` → **exit 0 (VERDE)**, 8/8 checks, provado
  em **D=2 (FE=61), D=10 (FE=309), D=30 (FE=929)**.
- **Testes:** **44/44 OK** (17 F0-01 + 10 F0-02 + 17 novos) sob env-main.
- **Regressões:** F0-01, F0-02, preflight → todos exit 0. Base `python3` runnability preservada.
- **Commits:** 6, prefixo `[F0-03-export]`, taxonomia dos cartões F0-01/F0-02. Working tree limpo.
- **Concorrência:** uma 2ª instância rodou em paralelo (higiene F0-02 + reconciliação BBOB);
  **validado: zero interferência, conjuntos de arquivos disjuntos**, meu gate verde sob o novo HEAD.

---

## 1. Contexto e escopo (o que o cartão pediu)

O prompt fixou 4 entregáveis, todos **encanamento** (D97 — nenhum julgamento de fidelidade):
1. **Wrapper de FE:** fonte ÚNICA do orçamento nos 2 stacks; conta avaliações reais
   **DISTINTAS por X nativo bit-a-bit**; **cache-hit = 0 FE (D89)**; `solution_id` =
   dedup-por-X (D57); **hard-stop EXATO em 31D−1** (`BudgetExhausted`, D21/D61). O DoE é
   CARREGADO do artefato do F0-02 (D63), nunca regenerado.
2. **3 camadas de export (§17.2):** ① avaliações reais (dedup por X) · ② população/geração ·
   ③ surrogate (μ/σ por candidato×geração, salvar TUDO D54) + tabela de timing (§17.6).
   Parquet **float32 SEM arredondamento (D53)**; escrita **ATÔMICA** (D58); run pronto = skip.
3. **`src/gcs.py`:** dual-write GCS com **import LAZY**; bucket-only = c154,c122,e81,c149,c262
   (D58); no Mac o caminho é local (não chama GCS).
4. **`scripts/accept.py`:** transformar os stubs de export em checagens REAIS — sem tocar D97.

Restrições fortes do prompt: rodar **só** sob env-main por caminho completo; **NÃO instalar
nada** (D80/D81 — pins são decisão do autor); **NÃO** importar `google-cloud-storage`
(lazy); **PARE-e-logue** em ambiguidade (D81); usar os tokens de problema **do código/DoE**.

---

## 2. Etapa 1 — Gate de ambiente (antes de tudo)

Executei, por caminho completo do interpretador env-main:
```
PY -c "import numpy,pandas,pyarrow,pymoo; print(...)"
→ ok 2.4.6 (numpy) · 2.3.3 (pandas) · 25.0.0 (pyarrow) · 0.6.2 (pymoo)
```
**Resultado:** env-main saudável. Prossegui (se falhasse, PARARIA e avisaria — D81).

---

## 3. Etapa 2 — Leitura de contexto (PASSO 0, na ordem mandada)

Li **somente** o prescrito (regra de ouro do contexto):
- `HANDOFF_MESTRE.md` (§10 estado, §11 armadilhas) + `handoff/F0-02-doe.md` — o que a
  sessão anterior deixou (o `doe.py`, `seeds.json`, os helpers F0-01, e **o CONTRATO para
  quem carrega**, inclusive o **corte do CP-init** deixado para o F0-03).
- `claude_code_context/CLAUDE.md` (precedência D83, pára-e-loga D81, invariantes §5).
- A linha **F0-03-export** em `cards/INDEX.md`.
- Os 2 arquivos-chave de `00_fundacao/`: **`03_contrato_export.md`** (§17 completo — o
  coração do cartão: 3 camadas, schema §17.2, C1/C3, timing §17.6, persistência §17.7) e
  **`04_plano_F0_piloto_gates.md`** (§22.0/22.1 Fase 0, §22.6 gates, **cartão S.4 com o
  teste de aceitação F0**).
- Os arquivos-fonte a **reusar**: `naming.py`, `atomic_io.py`, `manifest.py`,
  `audit_log.py` (F0-01), `doe.py` (F0-02), `experiment.py`, `accept.py`.

**Fatos-chave extraídos** (que guiaram o design):
- `solution_id`/`geracao`/ids devem ser **inteiros** no Parquet (§17.4 — comprimem quase a
  nada); o `R-001` do §17.2 é ilustração de mock.
- A ③ é **UMA tabela** (D35) com colunas opcionais (DEF-C1): regressor μ/σ, classificador
  classe/score, híbrido os dois; + C3 (`espaco_modelo/transf_tipo/transf_params`).
- **b1 (ParEGO) é mono-output** (§17.2/D47): preenche `mu_0`, deixa `mu_1..` NULL.
- O CP-init compara **hash do ARRAY decodificado** (não nomes de coluna); o `doe_hash` do
  run vem da **init X float64**, não do Parquet float32.
- **Sonda:** MMF1 → D=2, M=2 (n_init=21, maxfe=61) — escolhido como problema pequeno do
  STUB; pyarrow 25 suporta **zstd** (confirmado por escrita de teste).

---

## 4. Etapa 3 — Plano (PASSO 1) + decisão fixada

Apresentei plano ≤15 linhas (5 arquivos + teste de aceitação exato) e **segui direto**
(o cartão manda não esperar OK; exceção só p/ ambiguidade). **Decisão que FIXEI** (documentada
para veto, no padrão do F0-02):
- **Colunas do export em 0-based** (`x0..x{D-1}, f0..f{M-1}, mu_0.., sigma_0..`). O §17.2
  escreve `x_1..x_D` como **notação matemática**; o F0-02 já materializou o DoE/dataset em
  0-based e o MATLAB os lê assim → mesma convenção p/ o join ①↔DoE ser trivial. O CP-init
  compara hash do array (não nomes) ⇒ **indiferente ao gate**. Centralizei em 4 funções
  (`export.x_cols/f_cols/mu_cols/sigma_cols`) — trocar p/ 1-based = 1 edição.
- **Não** classifiquei isto como ambiguidade bloqueante (D81): é encanamento, a SPEC dá
  leitura defensável, e o F0-02 abriu o precedente ("fixo e ofereço veto barato").

---

## 5. Etapa 4 — Implementação (PASSO 2), arquivo por arquivo

### 5.1 `src/budget.py` (NOVO) — wrapper de FE
- `BudgetExhausted(Exception)` — o hard-stop; espelho MATLAB = `MException('PlatEMO:Termination')`.
- `RealEval` (dataclass) — uma linha do catálogo ①; `x`/`f` em **float64** (valor exato).
- `FEBudget`:
  - **Chave de identidade** `_key(x)` = `np.ascontiguousarray(np.asarray(x,'<f8').reshape(-1)).tobytes()`
    → **bit-a-bit no X nativo** (D89). Normaliza dtype/shape (2D, não-contígua, int) para a
    MESMA chave que a 1D contígua equivalente.
  - `evaluate(x, true_f)`: se a chave já existe → **cache-hit: 0 FE**, loga evento `cache_hit`
    (D89), devolve o `f` memorizado (livre mesmo após esgotar). Se inédita → **hard-stop
    EXATO** (`if fe >= maxfe: raise BudgetExhausted` ANTES de consumir), senão avalia,
    `fe += 1`, cria `RealEval` com `solution_id = fe_index` e `fase`.
  - `fase`: `init` se `fe_index < 11D−1` (o DoE), senão `opt` (infill).
  - `init_X()` → as 11D−1 primeiras X (float64) → fonte do `doe_hash` do CP-init.
  - `maxfe = 31D−1` default; `remaining/exhausted/cache_hits/records` expostos.

### 5.2 `src/export.py` (NOVO) — as 4 camadas
- **Schemas autoritativos** (pyarrow), parametrizados em (D,M): `real_schema`, `pop_schema`,
  `surrogate_schema`, `timing_schema`. Tipos: ids `int32`, numéricos `float32`, strings.
  Obrigatórias não-nulas; opcionais da ③ (μ/σ, pred_*, C3) nuláveis.
- **Escritor físico** `_write_table`: `atomic_path` (D58) + `compression="zstd"` (D53).
- `_f32` = `ascontiguousarray(dtype=float32)` — cast IEEE, **NÃO** arredondamento decimal
  (D53: o `round(x,3)` foi morto — colapsava σ 10⁻⁴–10⁻⁶ e colidia o dedup).
- `write_real(records)` (do `bud.records`), `write_pop(pop_rows)` (membership
  `(geracao, solution_id)` — sem x/f, D31), `write_surrogate(rows, D, M, regime)`,
  `write_timing(timing_rows)`.
- `surrogate_row(...)` — monta linha com defaults NULL; **suporta μ/σ mais curtos que M**
  (caso mono-output do b1: mu_0 preenchido, mu_1.. NULL). `transf_params` → JSON string.
- `run_done` = re-export de `manifest.is_run_done` (skip D58).

### 5.3 `src/gcs.py` (NOVO) — dual-write lazy
- `import src.gcs` roda em QUALQUER interpretador: o `from google.cloud import storage`
  está **DENTRO** de `_client()` (LAZY); `_client` levanta **`RuntimeError` claro** se a
  lib faltar (nunca ImportError cru, nunca instala — D80/D81).
- `BUCKET_ONLY_ALGS = {c154,c122,e81,c149,c262}`; `BUCKET_ONLY_LAYERS = {surrogate}` →
  só a ③ dos 5 é bucket-only (D58); demais camadas/algs = dual-write.
- `plan_targets(exp,alg,prob,sem, enable_bucket, data_root)` — **PURO, sem rede**:
  `enable_bucket=False` = caminho local do Mac (todos os blobs None); `=True` = dual-write
  (blobs c/ prefixo `experiments/{exp}/{alg}/`, ③ do alg volumoso marcada bucket_only).
- `upload / blob_exists / mirror_run / sync_pending` — lazy (VM). `mirror_run` sobe local→
  bucket e **poda a ③ local só dos bucket-only, DEPOIS do upload** (nunca perde dado).
- `smoke_blob_path()` = `experiments/_smoke/...` (o smoke real roda na VM).

### 5.4 `scripts/accept.py` (MODIFICADO)
- `check_outputs/check_fe/check_doe_hash` ganharam parâmetro **`data_root`** (default =
  `data/` do repo — R1/R2/R3 seguem iguais; o F0-03 injeta um tempdir).
- **`_f0_03_stub_run(...)`** — o **algoritmo-STUB** (sem algoritmo real): carrega o DoE do
  F0-02, avalia os 11D−1 pontos (init) + 20D infills distintos (opt) = 31D−1; força um
  **cache-hit** (re-avalia o DoE[0]) e o **hard-stop** (X inédita → BudgetExhausted); gera
  ② pop, ③ surrogate (regressor + classificador + linha C3 mono-output), timing; grava
  as 4 camadas + `.jsonl` + manifesto (`doe_hash` = hash da init X). Local puro (sem GCS).
- **`_check_export_schema(...)`** — compara o schema lido de cada parquet com
  `export.*_schema` (nomes+tipos+nulabilidade EXATOS) + confirma que a ③ tem linhas de μ
  E de classe + float32.
- **`check_f0_03()`** — orquestra os 8 checks num tempdir e devolve a lista.
- Branch `F0-03-export` no `main()` (imprime, sai 0/1). **Preservei a política D97** (o
  lembrete "fidelidade = manual do autor" continua).

### 5.5 `tests/test_export_budget.py` (NOVO) — 17 testes
- **GCS (stdlib, sempre roda):** lista bucket-only exata, plan local-only sem rede, plan
  bucket, import lazy (RuntimeError sem a lib).
- **Budget (numpy):** hard-stop exato, cache-hit=0/mesmo-id, near-dup paga 1 FE, dedup
  incremental, fase init/opt, init_X float64, cache-hit livre após esgotar.
- **Export (numpy+pyarrow):** schemas/tipos, round-trip real, **float32 ≠ round3**,
  opcionais C1 + mono-output b1, escrita atômica, codec zstd, pop/timing.

---

## 6. Etapa 5 — Bug encontrado e corrigido DURANTE a execução

Na 1ª rodada do gate, o STUB estourou:
```
IndexError: index 1 is out of bounds for axis 0 with size 1
  em export.write_surrogate (float(r["mu"][j]) com mu de len 1 e M=2)
```
**Diagnóstico:** era um **bug real do writer**, não só do STUB — um `mu` mono-output (o
**caso b1/ParEGO**, §17.2: `mu_0` preenchido, `mu_1..` NULL) fazia o writer indexar fora.
**Correção:** `write_surrogate` agora trata `mu`/`sigma` **mais curtos que M** como NULL nos
índices faltantes (`opt_obj`). Isto é exatamente o comportamento que a SPEC exige para o b1.
O STUB passou a exercitar legitimamente esse caminho. **Lição para as Rodadas:** o schema ③
acomoda regressor multi-output, mono-output (b1), RBF-puro (σ NULL) e classificador — testado.

---

## 7. Etapa 6 — Aceitação e verificação (PASSO 3)

### 7.1 Gate objetivo do cartão
`PY scripts/accept.py F0-03-export` → **VERDE, exit 0**. Os 8 checks:
| # | Check | Resultado |
|---|---|---|
| 1 | FE final = 31D−1 exato (D89) | OK — D=2 FE=61 · D=10 FE=309 · D=30 FE=929 |
| 2 | cache-hit = 0 FE + hard-stop exato (D89/D21) | OK — cache_hits=1 (0-FE), hard_stop=True, fe_final==maxfe |
| 3 | 4 saídas presentes (§17.7) | OK — 3 parquets + timing + jsonl |
| 4 | schema §17.2 (①②③+timing) + float32 (D53) | OK — schemas exatos, ③ com μ E classe |
| 5 | escrita atômica (0 .tmp) + skip idempotente (D58) | OK — tmp=[], run_done pre=False post=True |
| 6 | gcs.py bucket-only + caminho local sem rede | OK — lista exata, local_only, gcs ausente no Mac |
| 7 | CP-init por-run: manifest doe_hash = sidecar (D87/D88) | OK — hash bate |
| 8 | regressão F0-02: DoE bit-a-bit | OK |

### 7.2 Suite de testes
`PY -m unittest discover -s tests -t .` → **Ran 44, OK**. No `python3` base (sem pyarrow)
os de export/doe **pulam** corretamente (runnability F0-01 preservada; verificado).

### 7.3 Verificação adversarial de casos-limite (à mão)
Testei 5 arestas do wrapper de FE que os testes automatizados não cobrem — **todas fiéis a D89:**
- `-0.0 ≠ +0.0` → distintos (bit-a-bit; é a semântica literal do D89).
- NaN com bits idênticos → cache-hit (0 FE).
- Entrada **2D / não-contígua** → **colide** com a 1D equivalente (dedup correto).
- Falha de hard-stop → **não polui** o catálogo ① (30 records, 30 fe).
- `int x == float x` → mesma chave (normalização p/ float64).

### 7.4 Workflow de verificação adversarial (transparência)
Disparei um **workflow de 6 lentes adversariais** (D89, D53/D54, schema §17.2, D58, gcs-lazy,
escopo-D97) em background. Os 6 agentes chegaram a **investigar** (Read/Bash sobre o código),
mas o workflow foi **interrompido quando você me pausou** e **não emitiu as saídas
estruturadas finais** (a task saiu do registry). **Compensei com a verificação manual focada
da §7.3** — mais dirigida que as lentes genéricas. Registro isto por honestidade: o workflow
não produziu veredito formal; a confiança vem dos 44 testes + gate em 3 dimensões + 5 arestas.

### 7.5 Regressões
`accept.py F0-01` exit 0 · `accept.py F0-02` exit 0 · `preflight.py` exit 0 · base `python3`
`accept.py F0-01` VERDE (import não puxa numpy — o andaime segue leve).

---

## 8. Etapa 7 — Incidente de concorrência (validação pedida pelo autor)

Você me informou (a meio da tarefa) que uma **2ª instância de Claude Code** rodou em paralelo
e já fechou. Validei (read-only) **antes de commitar**:
- **HEAD moveu:** 4 commits novos da outra instância — `e8adacc` (reconcilia **BBOB1→BBOB_F***,
  o canônico da SPEC §4/characteristics/runs_matrix), `cf4a4cc` (persiste `data/doe`+`data/datasets`
  agora sob `BBOB_F*`), `d1edcf2` (requirements + pin pandas<3), `bb72de0` (docs da torre).
- **`git status` mostrou EXATAMENTE meus 5 arquivos** não-commitados — nada mais. **Conjuntos
  disjuntos, zero sobreposição de escrita.** A outra instância commitou só o dela.
- **Meu gate reverde sob o novo HEAD:** F0-03 VERDE, F0-01/F0-02 exit 0, 44 testes OK.
  Rodei `--problema BBOB_F1` (D=10 → **FE=309 exato**) provando que **meu código é agnóstico
  ao token** (usa `naming` + `experiment.ALL_PROBLEMS`, nunca hardcode de BBOB).
- **Correção de rumo importante:** minha "preocupação" inicial (o rename `BBOB1→BBOB_F1` parecia
  contradizer o DoE) **caiu** — a outra instância moveu o DoE junto (regenerou sob `BBOB_F*`,
  valores idênticos por hash) e esclareceu que **`BBOB_F*` é o canônico** (o token curto `BBOB1`
  era o anômalo). A **NOTA DE NOMES do meu prompt ficou stale**; meu handoff já reflete o correto.

**Veredito:** sem interferência; meu progresso intocado; nada meu havia sido commitado até eu commitar.

---

## 9. Decisões fixadas nesta sessão (para veto do autor — trocar é barato)

1. **Colunas do export 0-based** (`x0../f0../mu_0..`) — harmoniza com o DoE/dataset do F0-02;
   CP-init é indiferente (compara hash do array). Trocar = 1 edição (4 funções centralizadas).
2. **`solution_id`/`geracao`/ids = `int32`** no Parquet (§17.4 — comprimem quase a nada); o
   `R-001` do §17.2 é só ilustração de mock. Semântica = dedup-por-X (D57), preservada.
3. **STUB vive em `scripts/accept.py`** (não em módulo de produção) — é harness de aceitação,
   como o `check_f0_02` do F0-02. Nenhum código de STUB entra em `src/`.

---

## 10. Estado final e commits

**Working tree limpo.** 6 commits, prefixo `[F0-03-export]` + trailer `Co-Authored-By`
(taxonomia idêntica a F0-01/F0-02):
```
1de4fd2  budget.py: wrapper de FE (cache-hit=0 D89 + hard-stop 31D-1 D21 + solution_id D57)
a8ae83a  export.py: 3 camadas + timing (§17.2; float32 sem round D53; salvar-tudo D54; zstd; atomico D58)
68ca8f3  gcs.py: dual-write local+bucket com import lazy; bucket-only c154/c122/e81/c149/c262 (D58/§17.7)
a66309f  accept: check_f0_03 (STUB ponta-a-ponta) + data_root nos checks por-run; nao toca D97
8b9b728  tests: unit de budget/export/gcs (cache-hit, hard-stop, float32≠round3, atomico, bucket-only, lazy)
7a04806  cards/handoff: F0-03 fechado (gate verde; FE/cache-hit/schemas §17.2/atomico/gcs-local/CP-init)
```
(+ este relatório, no commit de fecho.)

---

## 11. O que o F0-04 e as Rodadas HERDAM (contrato de consumo)

- **Orçamento:** UM `budget.FEBudget(D=prob.n_var, logger=audit_log)` por run; toda avaliação
  real via `bud.evaluate(x_nativo, true_f)`; hard-stop = `except BudgetExhausted`. NÃO usar
  o `obj.FE` do PlatEMO (D89).
- **CP-init por-run:** gravar `manifest['doe_hash'] = doe.decoded_hash(bud.init_X())` (init X
  em **float64**; a ① no parquet é float32, mas o hash é do float64). O `accept.py --alg`
  compara via `check_doe_hash`. **O corte do F0-02 (metade Python) FECHOU**; falta só o
  gancho num **run com adapter real nos 2 stacks** → herda p/ **R1-00** (aí o CP-init é 100%).
- **Export:** `write_real(bud.records)` · `write_pop(membership)` · `write_surrogate(rows, D, M,
  regime)` (montar com `export.surrogate_row`) · `write_timing(rows)` → depois
  `manifest.new_manifest(status='ok', ...)` + `write_manifest`. Skip via `export.run_done`.
- **Bucket (só VM Python):** `gcs.mirror_run(...)` após gravar local (poda a ③ local dos 5
  bucket-only). No **Mac/MATLAB**: `plan_targets(enable_bucket=False)` = local puro.
- **Estado do dual-write GCS:** encanamento pronto e testado **no caminho local**; **NÃO
  exercitado contra o bucket real** — `google-cloud-storage` não está no env-main do Mac
  (não instalei; D80/D81). O smoke real (`experiments/_smoke/...`) roda **na VM** (ADC da SA
  já provisionado — HANDOFF §7). Herda p/ **R2-00**.

---

## 12. Pendências / riscos abertos

1. **NOTA DE NOMES do meu prompt está stale:** ela dizia usar `BBOB1`; o repo agora usa
   `BBOB_F*` (canônico, já commitado pela outra instância). Meu código é agnóstico → sem ação
   do meu lado. Só registro para a torre não estranhar.
2. **Workflow adversarial não concluiu** (interrompido no pause) — a confiança vem dos 44
   testes + gate em D=2/10/30 + 5 arestas manuais, não de um veredito multi-agente formal.
   Se a torre quiser, dá para re-disparar o workflow numa sessão limpa.
3. **Camada de auditoria fina (S.7/DEF-C5) e dicionário C4** ficam para as Rodadas — o F0-03
   entrega o mínimo comum (`audit_log`) + o schema ③ que já acomoda os campos por algoritmo.
4. **Próximo cartão da Fase 0: F0-04-metrica** (esqueleto da métrica + smoke F1 = 1,0433, D92).

*Fim do relatório de execução do F0-03-export.*
