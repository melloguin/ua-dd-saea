# handoff/F0-01-harness.md — Fase 0, cartão 1/4 (andaime comum do harness)

**Data:** 2026-07-15 · **Gate:** `python3 scripts/accept.py F0-01-harness` → **VERDE, exit 0** ✅
**Escopo:** PURA INFRAESTRUTURA — despachantes (§16.5), esteira idempotente (resume + escrita
atômica, D58), manifesto + logger `.jsonl` (§17.5), limpeza dos imports mortos. **Sem algoritmo**
(sem julgamento de fidelidade — D97). **Ambiente:** o interpretador é `python3` (Python 3.12.1 base).

## Resultado (aceitação F0-01, tudo verde)
- `python3 scripts/accept.py F0-01-harness` → **exit 0** (andaime: infra importa · naming §17.7 · manifesto+jsonl round-trip).
- `python3 -c "import src.experiment"` → **OK** (25 problemas canônicos, `MMF16_L3` removido, `ALGORITHM_DISPATCH={}`).
- `python3 experiments.py --algorithms none --problems MMF1 --seeds 0` → **monta grid/manifesto, exit 0**.
- **17 unittests** (`python3 -m unittest discover -s tests -t .`) → **OK** (naming 3 camadas+jsonl+manifesto; manifesto/esteira; logger; escrita atômica).
- **Esteira idempotente comprovada:** run `ok` simulado → **pulado** no resume (`skipped=1`); `--force` → re-roda. (Prova do gate global §22.6 "kill+resume".)
- **D23 (retry) comprovado:** ok / retried_ok / failed com `n_retries` corretos.
- **Regressão:** `scripts/preflight.py` da sessão anterior **continua verde (exit 0)**.

## Arquivos

**Novos (stdlib puro — rodam em qualquer interpretador):**
- `src/naming.py` — **fonte única** da nomenclatura §17.7/D55: `run_id = {exp}_{alg}_{problema}_{semente}`,
  base `exp_{run_id}`, 4 camadas (`__real/__pop/__surrogate/__timing.parquet`), `.jsonl`,
  `.manifest.json`, prefixo do blob GCS. Token `{exp}∈{main,off,batch,sweep-<tier>-<dist>}`. **accept.py
  e o despachante importam este módulo** → escritor e verificador não podem divergir no nome.
- `src/atomic_io.py` — escrita atômica `*.tmp→os.replace` (D58; `.tmp` no MESMO dir → rename atômico).
  Primitiva da esteira; **F0-03 reusa** para as 3 tabelas parquet.
- `src/manifest.py` — fragmento `{base}.manifest.json` por run (D58): status {ok/retried_ok/failed},
  n_retries, stack_trace, timing/desdobramento §17.6, `fit_series`, `paths.local`+`paths.bucket`,
  `upload_status`, doe_hash/repo_hash/env (campos prontos, preenchidos nas rodadas). `is_run_done`
  (resume: manifesto ok **E** camadas presentes **E** footers válidos) + `Scoreboard` (placar).
- `src/audit_log.py` — `AuditLogger` do `.jsonl` §17.5: `header/decision/partial/guard/timing/footer`,
  uma decisão por linha. **D97 respeitado:** só instrumenta; não julga fidelidade.
- `experiments.m`, `src/experiment.m`, `src/hook_output.m` — **esqueletos MATLAB** (receita N.4); corpo
  real na **R1-00-harness**. Já carregam as armadilhas críticas: bypass do `platemo()`, `rng(seed)` DEPOIS
  do Problem (D59), `save=-K`/`outputFcn` sempre, `maxRuntime=inf`, hard-stop pelo contador do WRAPPER
  (não `obj.FE` — D89), `parquetwrite` brotli+single sem `round` (S.6), e103/e74 worker dedicado (D95).
- `tests/` — `test_naming.py`, `test_manifest_audit.py`, `__init__.py` (17 testes, stdlib).

**Reescritos:**
- `src/experiment.py` — de POC para **esqueleto de adapter A2** (§16.5.3): catálogo de 25 problemas
  (import de `src.problems` **lazy** → o módulo importa sem pymoo), `ALGORITHM_DISPATCH={}`,
  `run()` levanta `NotImplementedError` (despacho é R1/R2/R3), contrato dos 6 passos documentado.
  **Removidos:** os 7 imports de runners mortos, `_invoke_runner`, `_apply_algorithm_overrides`,
  kriging/noisy/`experiment_sa_moea` (POC descomissionada — §16.5).
- `experiments.py` — despachante Python (§16.5/§19): `DEFAULT_ALGORITHMS`=[c262,c154,e81,c122,c149,b5,c311]
  (stack Python), 25 problemas, 30 sementes `range(29)+[42]`, token `--exp`, esteira idempotente por
  manifesto, placar, política D23 (1 retry). Imports pesados (**joblib/pandas/tqdm lazy**) → o andaime
  roda no `python3` base. Sentinela `--algorithms none` = roster vazio (monta só o grid).
- `scripts/accept.py` — **checagem de andaime F0-01 real** (`check_scaffold`: infra importa + naming §17.7
  + manifesto/jsonl round-trip) sem tocar a política D97 (só encanamento objetivo). Passou a importar
  `src.naming` (mesma fonte do escritor). Checks de run (4 saídas/FE/DoE) mantidos p/ cartões futuros.
- `cards/INDEX.md` — F0-01-harness → ✅.

## Decisões de engenharia (não conflitam com a SPEC — registradas aqui, não são fidelidade)
1. **`--algorithms none` = roster vazio** (a aceitação usa esse comando literal): monta grid/manifesto
   sem executar nada. Interpretação óbvia; não é definição da SPEC.
2. **Fronteira "escrita atômica" F0-01×F0-03:** F0-01 entrega a *primitiva* (`atomic_io`) + o fragmento
   de manifesto (D58); **F0-03** a usa para gravar as 3 tabelas parquet + o wrapper de FE/hard-stop.
   (D58 é o mecanismo; F0-03 aplica.)
3. **Nome do manifesto:** D58 diz `{run_id}.manifest.json`; realizei como `exp_{run_id}.manifest.json`
   (base `exp_{run_id}` do §17.7) p/ TODOS os artefatos do run compartilharem o prefixo. Harmonização
   D58×§17.7, não conflito.
4. **Imports lazy** (problems em `experiment.py`; joblib/pandas/tqdm em `experiments.py`): o andaime é
   leve por design → roda no `python3` base sem env-main; as libs pesadas carregam só na execução real.

## Fora de escopo (próximos cartões — NÃO implementados aqui, por design)
- **F0-02-doe:** `src/doe.py` (LHS-maximin próprio D87 + parquet + hash do array decodificado), dataset
  offline (D90), `artifacts/seeds.json` (D91), CP-init. *(o estágio 1 do despachante é um stub que anuncia isto.)*
- **F0-03-export:** wrapper de FE (cache-hit=0 D89) + hard-stop, schemas das 3 tabelas (C1/C3/C4),
  `src/gcs.py` (dual-write + `sync_pending`), consolidação brotli→zstd. *(paths de bucket + `upload_status`
  já estão no manifesto, prontos p/ o upload.)*
- **F0-04-metrica:** esqueleto da métrica + smoke HV(F1)=**1,0433** (D92).
- **R1-00-harness:** corpo real dos esqueletos `.m` (ponte pyenv, UserProblem, export, manifesto MATLAB).

## ⚠ O que a próxima sessão (F0-02-doe) precisa saber
- **Ambiente (importante):** o **env-main COMPLETO não está provisionado** neste Mac. Estado real:
  - `python3` base (3.12.1): tem **numpy, pandas, pyarrow**; **NÃO** tem joblib/tqdm/sklearn/pymoo.
  - `~/ponte_teste` (venv py3.11.9, o da ponte MATLAB): numpy 2.4.6 / scipy 1.17.1 / **pymoo 0.6.2**;
    **NÃO** tem pandas/pyarrow/joblib/tqdm/sklearn.
  - pyenv tem 3.11.9/3.10.14/3.8.19 **sem** o stack científico instalado.
  - **F0-02/F0-03 vão precisar de pandas+pyarrow (+ pymoo p/ instanciar problemas e gerar F do dataset)
    num MESMO interpretador.** Sugestão: provisionar env-main (S.6: numpy/pandas/pyarrow/joblib/tqdm/
    scipy/pymoo==0.6.2 …) sobre pyenv 3.11.9 — **decisão de env/pin é do autor (D80/§8)**; registrar as
    versões no manifesto. (F0-01 não precisou disso — andaime é stdlib+lazy.)
- **Consuma o naming pelo módulo:** `from src import naming` (nunca reconstrua strings de caminho à mão).
- **DoE:** artefato `data/doe/{problema}/doe_{problema}_{semente}.parquet` (colunas `x0…x{D−1}`, escritor
  único pyarrow; MATLAB lê com `parquetread`); **hash SHA256 do ARRAY DECODIFICADO** no manifesto
  (campo `doe_hash` já existe em `new_manifest`). O despachante MATLAB injeta via `initFcn` (A1).
- **accept.py** já tem `check_doe_hash` e `check_fe`; F0-02 os torna verdes com o artefato real + CP-init.
- **Sem tocar D97:** o accept.py só verifica encanamento objetivo; fidelidade é manual do autor.

## Pendências abertas / notas
- Nada commitado além dos arquivos deste cartão. Apareceram no working tree **sem serem meus**:
  `ORQUESTRACAO_MESTRE.md` e `PLANO_IMPLEMENTACAO.md` (untracked) — **deixei intactos** (não são do F0-01).
- Commits desta sessão (prefixo `[F0-01-harness]`): infra stdlib → despachante+adapter → esqueletos MATLAB
  → accept+tests → fix n_retries. Branch: `experiment/definitive_algorythms` (não commitado nada fora dos meus arquivos + `cards/INDEX.md`).
- MATLAB **não foi executado** (não há MATLAB neste passo/CLI) — os `.m` são esqueletos verificados por
  leitura, validados de fato na R1.
