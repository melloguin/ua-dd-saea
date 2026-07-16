# handoff/R1-00-harness.md — Rodada 1, cartão 00 (infra TRANSVERSAL MATLAB/PlatEMO)

**Data:** 2026-07-16 · **Env:** MATLAB **R2025a Update 1** (Mac arm64) + a PONTE Python
embutida (`pyenv` InProcess → `/Users/gmello/ponte_teste/bin/python`; numpy 2.4.6 ·
**pymoo 0.6.2** ✓ · pyarrow 25.0.0). Verificação Python independente no **env-main**
(`.../mestrado_experimentos_dissertacao/bin/python`).
**Gate:** `accept_r1_00` (MATLAB) **7/7 VERDE** em 4 problemas + `accept.py R1-00-harness`
(leitor Python independente) **VERDE, exit 0**. ✅
**Escopo:** PURA INFRAESTRUTURA TRANSVERSAL (contrato N.0). **SEM algoritmo** dos 16
(o c217 é o próximo cartão), **SEM julgamento de fidelidade** (D97). Prova por **run-STUB**
(avaliador trivial pela ponte) — espelho MATLAB do `_f0_03_stub_run` do Python.

## Ambiente (verificado ANTES de tudo — D80/D81)
`pyenv` InProcess aponta `ponte_teste/bin/python`; a ponte importa `numpy`
(`sum([1,2,3])→6`), `pymoo==0.6.2`, `pyarrow==25.0.0`, e avalia `src/problems.py`
(`evaluate_problem`) ponta a ponta. **Nada instalado** (pins são decisão do autor).
⚠ **Armadilha MATLAB↔ponte:** o MATLAB NÃO acessa atributos dunder por ponto
(`py.pymoo.__version__` e `._instantiate_problem` quebram — id não pode começar por `_`):
usar `py.importlib.metadata.version(...)` para versões e `py.getattr(mod,'_nome')` para
privados. (Um parse-error de `.m` também disparou um segfault do `ddux LicenseLogger` no
caminho de saída — benigno, não sistêmico: batch trivial sai limpo, exit 0.)

## Resultado (tudo verde)
- **`accept_r1_00` (MATLAB) 7/7** em **MMF1**(D2,M2,FE61), **DTLZ2**(D12,**M3**,FE371),
  **ZDT1**(D30,FE929) e **BBOB_F1**(D10,FE309 — nome reconciliado): STUB→`ok`; **FE final =
  31D−1 EXATO** (linhas da ①); **cache-hit = 0 FE + hard-stop exato**; **4 saídas**; **schema
  §17.2** (nomes+tipos das 4 camadas); **CP-init** (hash float64 = sidecar **E** ①(float32) =
  `single(DoE)` bit-a-bit).
- **`accept.py R1-00-harness --alg stub …` (Python env-main, leitor independente)** VERDE nos
  4: 4 saídas, FE=31D−1 (leitura pyarrow), **DoE CP-init hash = sidecar**.
- **CP-init cross-language fechado:** `manifest['doe_hash']` (init X **float64** capturada pelo
  wrapper no MATLAB) **==** `doe_{prob}_{sem}.manifest.json::doe_hash` (Python) — MATCH.
- **Despachante:** roster vazio (andaime), serial `ok`, **skip idempotente** (2ª execução →
  `skipped`, gate §22.6 kill+resume), **`parfor` 2 células** (produção, ponte por worker) → `ok=2`.
- **③ surrogate C1/C3:** `mu_0..mu_{M-1}`/`sigma_*` por objetivo (M=3 ok); NULLs corretos
  (numérico ausente `single(NaN)`→NULL; string ausente `<missing>`→NULL, como o `None` do Python);
  mono-output b1 (`mu_0` preenchido, `mu_1..` NULL); linha classificador (`pred_classe`/score).
- **.jsonl (§17.5):** header + decisions + **guards `cache_hit`/`hard_stop` (eventos D89)** +
  timing + footer (`status ok`, `fe_final`, `cp_init:true`).
- **Regressão:** `accept.py` F0-01/F0-02/F0-03/F0-04 e `preflight.py` seguem **exit 0** (zero
  Python tocado). `.gitignore` ignora `data/experiments/` → outputs do STUB não versionam.

## Arquivos
**Novos:**
- `src/FEBudget.m` — **o wrapper de FE, a ÚNICA fonte do orçamento (D89/D57/D21).** Classe
  `handle`. Dedup por **X NATIVO bit-a-bit** (`typecast(double(x),'uint8')` = `<f8` LE row-major,
  idêntico a `np.ascontiguousarray(x,'<f8').tobytes()`; chave hex numa `containers.Map`).
  **Cache-hit = 0 FE + log**; `solution_id` = dedup 0-based (D57); **hard-stop EXATO**: a 31D-ésima
  X inédita levanta `MException('PlatEMO:Termination')` (D21/D61). Catálogo ① em **float64**;
  `init_X()` (as 11D−1 primeiras, fase `init`) = fonte do `doe_hash` do CP-init.
- `src/RunBuffer.m` — coletor de ②(membership)+③(surrogate C1/C3)+timing(§17.6) por geração
  (`addGeneration(view)`), alimentado pelo `hook_output` (c217) e pelo STUB (R1-00). Static
  `mkSurrogateRow(...)` = espelho de `export.surrogate_row` (defaults ausentes → NULL).
- `scripts/accept_r1_00.m` — **aceitação MATLAB do cartão** (roda o STUB + afere FE/cache/
  hard-stop/4-saídas/schema §17.2/CP-init). `nfail = accept_r1_00(problema, semente, dataRoot)`.

**Modificados (corpo real, eram esqueletos do F0-01):**
- `src/experiment.m` — **o adapter transversal**. ⚠ **A função primária agora é `experiment(...)`**
  (o esqueleto declarava `experiment_run`, que NÃO casava com o nome do arquivo `experiment.m` →
  não era chamável; corrigido). Corpo: setup da PONTE (repo-root no `sys.path`), instancia o
  problema Python (D/M/bounds), **carrega o DoE do artefato via `parquetread` (D63/D87 — NUNCA
  regenera)**, monta o `evalFcn` (a ponte), roda o STUB (init=DoE → opt=20D infills distintos →
  31D−1; cache-hit; hard-stop), grava as **4 camadas §17.2** (`parquetwrite` **brotli**+`single`+
  `int32`, SEM round — D53; escrita **atômica** `*.tmp→movefile` — D58), o `.jsonl` (§17.5) e o
  **manifesto** (§17.7), e **fecha o CP-init** (`sha256_rowmajor_f64(init_X)`=sidecar, ecoado em
  `manifest.doe_hash`). Espelha o naming de `src/naming.py`.
- `src/hook_output.m` — **corpo real do `outputFcn(Algorithm,Problem,buf,bud,timing)`** (extrai a
  geração → `buf.addGeneration`), guardado, **pronto para c217** (1ª execução sob um `Solve` real
  é no c217 — HANDOFF §8). No STUB a coleta ②③/timing usa o MESMO `RunBuffer.addGeneration`.
- `experiments.m` — despachante: grid, `addpath(genpath(PlatEMO))` **uma vez por worker** (N.0.1,
  só p/ algoritmos reais), **skip idempotente** (`is_run_done_m`: manifesto `ok` + 4 camadas),
  `parfor`/serial (`'parallel'`), placar. `default_problems()` → 25 canônicos (**BBOB_F1..F55**).
- `cards/INDEX.md` — R1-00-harness → ✅.

## O que o c217 (e os outros MATLAB) HERDAM — leia isto
- **Orçamento:** `bud = FEBudget(D)`; TODA avaliação real passa por `bud.evaluate(x_nativo, evalFcn)`.
  O hard-stop é `catch e; if strcmp(e.identifier,'PlatEMO:Termination')` no runner → FE final =
  31D−1 cravado. **NUNCA** usar `obj.FE` do PlatEMO para governar o término (D89).
- **evalFcn da ponte:** `@(x) double(prm.evaluate_problem(pp.obj, py.numpy.array(x)))` (bounds
  NATIVOS, §5.5 — CP-bounds já conferido contra o sidecar do DoE). Reusar `bridge_ctx`/`py_problem`.
- **DoE (D63/D87):** `load_doe(prob,sem,D,dataRoot)` devolve `X0` (float64) + hash + bounds; injetar
  `X0` como fase `init` (patch local A1 — os SAEAs NÃO usam `Problem.Initialization`). NUNCA regenerar.
- **CP-init por-run:** grave `manifest.doe_hash = sha256_rowmajor_f64(bud.init_X())` — bate com o
  sidecar (o `accept.py --alg`/`accept_r1_00` comparam). A init X é **float64** (a ① no parquet é
  float32, mas o hash é do float64 — não confunda).
- **Export:** `write_real/write_pop/write_surrogate/write_timing` (locais em `experiment.m`) já
  produzem o schema §17.2 idêntico ao `src/export.py` (verificado por pyarrow) — **brotli** (a
  consolidação Python re-encoda p/ zstd — S.6/D53). `RunBuffer.mkSurrogateRow` monta as linhas ③.
- **hook:** fiar com `algo = <ALGO>('save',-K,'outputFcn',@(A,P) hook_output(A,P,buf,bud,timing))`.

## Pontos de ATENÇÃO para o c217 (o corpo PlatEMO/Solve NÃO existe ainda — é do c217)
1. **`evalFcn` de LOTE (D61):** o `FEBudget.evaluate` é a primitiva **por-x**. O `UserProblem` do
   PlatEMO 4.15 chama o `evalFcn` com um **lote** (N×D) esperando `[dec,obj,con]`. O c217 escreve o
   embrulho de lote: iterar as linhas por `bud.evaluate`, avaliar os primeiros `saldo` do lote e
   **lançar `PlatEMO:Termination` no MEIO do lote** quando zera (D61), devolvendo `[dec,obj,con]`
   (`con=zeros`; `dec` = o X armazenado → clamp autoritativo). **Não construído/testado aqui** de
   propósito (depende do Solve real — é o ponta-a-ponta do c217, HANDOFF §8).
2. **`real_solution_id` (③) nullable:** no STUB toda linha ③ liga a um `solution_id` real →
   coluna **int32** (casa com §17.2). Candidatos NÃO avaliados (o caso comum do c217) precisam de
   **NULL**, que o MATLAB **não expressa em int32**. O `write_surrogate` já cai p/ `double`+`NaN`
   (→NULL) quando há ausentes (a consolidação re-casta p/ int32 nullable) — **decisão a confirmar
   no c217** (int32 all-present vs double+NaN por-run; evitar tipo variável entre runs de um mesmo alg).
3. **Receita N.0 no `Solve` real:** bypass do `platemo()`, `rng(seed,'twister')` **depois** do
   `Problem` e **antes** do `Solve`, `save=-K`+`outputFcn` fixos, `maxRuntime=inf`, `Problem`/
   `Algorithm` novos por task, `try/catch` em volta do `Solve` (o `PlatEMO:Termination` é engolido).
   e103/e74 em **worker dedicado** (N.3/N.0-4.1).
4. **`string`→`large_string`:** o `parquetwrite` do MATLAB grava strings como `large_string`
   (o Python usa `string`); os **nomes e os tipos numéricos/int batem**; diferença benigna (a
   consolidação re-encoda). `single`-NaN→NULL e `<missing>`→NULL confirmados.

## Estado do CP-init (fecha o corte herdado de F0-02/F0-03)
O F0-02 deixou o corte "X inicial na CAMADA ① de um run REAL, nos 2 stacks"; o F0-03 fechou a
**metade Python** (STUB). **A metade MATLAB fecha AGORA:** o run-STUB lê o DoE por `parquetread`,
injeta-o como fase `init` pelo wrapper, e (a) `init_X()` (float64) tem hash = sidecar; (b) a ①
(float32) = `single(DoE)` bit-a-bit; (c) o `manifest.doe_hash` do MATLAB = o sidecar do Python
(cross-language MATCH). O CP-init cross-linguagem está **100%** para o caminho STUB; o c217 apenas
repete o gancho com o `initFcn` do algoritmo real (o `accept.py --alg`/`accept_r1_00` já comparam).

## Como reproduzir
```
# MATLAB (na raiz do repo):
addpath('src'); addpath('scripts');
nfail = accept_r1_00('MMF1', 0, 'data')      % 7/7 VERDE (idem DTLZ2/ZDT1/BBOB_F1)
experiments('algorithms',{'stub'},'problems',{'MMF1'},'seeds',0,'parallel',false)

# Python (env-main), leitor independente:
python scripts/accept.py R1-00-harness --alg stub --problema MMF1 --semente 0 --dim 2
```
Outputs do STUB em `data/experiments/main/stub/` (gitignored — regeneráveis; deletáveis).

## Pendências / decisões
1. **Commit:** meus 6 arquivos com prefixo `[R1-00-harness]` (taxonomia F0-*). Nada de terceiros
   tocado; nenhum blob binário (os parquets do STUB são gitignored).
2. **Renome `experiment_run`→`experiment`** (necessidade do MATLAB: função primária == nome do
   arquivo). Se preferir o arquivo `experiment_run.m`, é 1 renome + 2 call-sites — me avise.
3. **Batch evalFcn + real_solution_id nullable** (itens 1–2 acima): **decisões do c217**, não do R1-00.
