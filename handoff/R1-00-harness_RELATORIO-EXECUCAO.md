# R1-00-harness — RELATÓRIO DE EXECUÇÃO (narrativa completa p/ a torre de controle)

> **Propósito.** Este documento descreve, passo a passo, TUDO o que a sessão de
> implementação do cartão **R1-00-harness** executou: a verificação de ambiente, a
> leitura de contexto, as decisões de projeto, a implementação, e — o mais importante
> para o veto do autor — **cada trecho de código rodado e o resultado exato obtido**.
> Companheiro do handoff conciso `handoff/R1-00-harness.md`.
>
> **Data:** 2026-07-16 · **Máquina:** Mac (macOS 12.5.1, arm64) · **Veredito final: VERDE ✅**
> (gate objetivo de encanamento; SEM algoritmo, SEM fidelidade — D97).

---

## 0. TL;DR (resposta à pergunta "está 100% pronta?")

- **Sim, para o escopo do cartão R1-00** (infra TRANSVERSAL MATLAB + gate objetivo de
  encanamento), **validado rodando código** (MATLAB R2025a + Python env-main), não por
  inspeção. **13 execuções de código, todas verdes.**
- **Ressalvas de escopo (por desenho, não lacunas do R1-00):**
  1. **Nenhum dos 16 algoritmos roda em R1-00** — o c217 é o próximo cartão. A prova é
     um **run-STUB** (avaliador trivial pela ponte), espelho MATLAB do `_f0_03_stub_run`
     do Python. O caminho `Algorithm.Solve`/`UserProblem` real está **escrito** (corpo do
     `hook_output`) mas só executa pela 1ª vez no c217 (HANDOFF §8: c217 = ponta-a-ponta).
  2. **2 decisões deferidas ao c217** (documentadas): `evalFcn` de **lote** com hard-stop
     no meio (D61) e `real_solution_id` **nullable** na ③ (MATLAB não expressa int32-NULL).
- **Zero regressão** (F0-01..04 + preflight verdes); **git limpo** (6 arquivos meus;
  outputs do STUB são gitignored).

---

## 1. VERIFICAÇÃO DE AMBIENTE (o gate bloqueante D80/D81 — feito ANTES de tudo)

O prompt exige: parar e avisar se a ponte MATLAB↔Python não importar numpy/pymoo/pyarrow,
ou se pymoo≠0.6.2. Executei essa checagem primeiro.

### 1.1 Localização
- Repo: `~/Documents/python_repos/mestrado/ua-dd-saea`.
- MATLAB: `/Applications/MATLAB_R2025a.app` (não no PATH; binário em `bin/matlab`).
- Ponte (venv que o `pyenv` do MATLAB usa): `~/ponte_teste` (Python 3.11.9) — inspeção do
  `site-packages`: numpy 2.4.6, pyarrow 25.0.0, **pymoo 0.6.2** ✓.

### 1.2 Diagnóstico da ponte (`bridge_check.m`)
**Comando:** `matlab -batch "bridge_check"`
**Descobertas (2 armadilhas MATLAB↔ponte, reter):**
- ⚠ **Dot-access a atributo dunder quebra o parser** (`py.pymoo.__version__` → "Invalid text
  character"): identificador MATLAB não pode começar por `_`. **Solução:** versões via
  `py.importlib.metadata.version(...)`; privados via `py.getattr(mod,'_nome')`.
- ⚠ Um parse-error de `.m` disparou um **segfault do `ddux LicenseLogger`** no caminho de
  SAÍDA do MATLAB. **Isolei:** um `matlab -batch "disp(1+1)"` trivial sai limpo (exit 0) → o
  segfault é só no caminho de erro, **não é sistêmico**.

**Resultado (após corrigir os dunders):**
```
PYENV.Executable = /Users/gmello/ponte_teste/bin/python   (ExecMode InProcess)
NUMPY sum([1,2,3]) = 6 ; NUMPY 2.4.6 ; PYMOO 0.6.2 ; PYARROW 25.0.0
=== BRIDGE CHECK: PASS ===          (exit 0)
```
**→ Ambiente VERDE. Prosseguir autorizado (D80/D81 satisfeitos). Nada instalado.**

### 1.3 Ponte de avaliação de ponta a ponta (de-risking antes de codar)
Testei o caminho real que o harness usa: instanciar um problema Python + ler D/M/bounds +
avaliar um ponto, tudo pela ponte:
```
inst = py.getattr(py.importlib.import_module('src.experiment'), '_instantiate_problem');
prob = inst('MMF1');                      % D=2, M=2, xl=[1 -1], xu=[3 1]
F = double(py.src.problems.evaluate_problem(prob, py.numpy.array([2.0 0.3])))  % = [0 1.18] ✓
```
**Resultado:** `BRIDGE_EVAL_OK` — a ponte instancia e avalia `problems.py` corretamente
(repo-root inserido no `sys.path` do Python embutido; `src` é namespace package).

---

## 2. LEITURA DE CONTEXTO (PASSO 0 — na ordem prescrita)

Li, nesta ordem: `HANDOFF_MESTRE.md` (§8 ordem/gates, §10/11 armadilhas); os dois
`CLAUDE.md`; os handoffs `F0-02-doe.md` e `F0-03-export.md`; o **contrato N.0**
(`10_rodada1_matlab/00_contrato_rodada1.md`); o **contrato de export §17** — que li
diretamente da FONTE autoritativa (`src/export.py`, `src/budget.py`, `src/naming.py`,
`src/manifest.py`, `src/atomic_io.py`, `src/audit_log.py`), pois o MATLAB precisa produzir
o **idêntico**; o `scripts/accept.py` (a esteira que devo satisfazer); `cards/INDEX.md`;
`00_fundacao/04_plano_F0_piloto_gates.md`; e os esqueletos F0-01 dos 3 arquivos-alvo.

**Fatos-chave extraídos (que guiaram o projeto):**
- **HANDOFF §8** designa **R1-c217 como o ponta-a-ponta**; R1-00 é a infra transversal
  (pattern-setter). → o STUB do R1-00 NÃO precisa de `Algorithm.Solve`.
- **`accept.py` (caminho genérico `--alg`)** = o gate do R1-00: `check_outputs` (4 saídas) +
  `check_fe` (linhas da ①) + `check_doe_hash` (DoE vs sidecar).
- **Schemas §17.2** (de `export.py`): ordem+nomes+tipos exatos das 4 camadas (mapeados linha
  a linha para replicar em MATLAB).
- **`budget.py`** (D89/D57/D21): dedup por X `<f8` bit-a-bit, cache-hit=0, hard-stop exato,
  `init_X()` (fonte do `doe_hash`).
- **F0-02/F0-03 deixaram o corte do CP-init** ("X inicial da CAMADA ① num run real") para
  **R1-00** — o que este cartão fecha.
- **Naming BBOB reconciliado para `BBOB_F*`** (canônico da SPEC; o token curto `BBOB1` era o
  anômalo) — o DoE em disco está sob `BBOB_F*` (confirmei: 25 pastas, sidecar de MMF1 lido).
- **`check_doe_matlab.m` (F0-02)** já provou (PASS=1505) que `parquetread`→SHA256 do array
  decodificado bate com o sidecar — **reusei o helper `sha256_rowmajor_f64`**.

---

## 3. DECISÕES DE PROJETO

### 3.1 STUB direto (NÃO via PlatEMO Solve)
**Decisão:** o run-STUB é um **avaliador trivial** que exercita a infra transversal
direto (ponte → FEBudget → DoE → export → manifesto → CP-init), sem `UserProblem`/`Solve`.
**Porquê:** (a) HANDOFF §8 designa o c217 como o ponta-a-ponta; (b) o gate do R1-00
(FE exato, 4 camadas, CP-init) é atingível dirigindo o FEBudget + export diretamente;
(c) o card diz "sem algoritmo (o c217 é o próximo cartão)"; (d) espelha exatamente o
`_f0_03_stub_run` do Python. **Não é ambiguidade que exigisse parar (D81)** — a evidência do
próprio contexto resolve a favor do STUB direto.

### 3.2 Persistência MATLAB via `parquetwrite` brotli (NÃO via a ponte pyarrow)
O contrato (S.6/D53/N.0) manda o lado MATLAB gravar com `parquetwrite(...,'brotli')` +
`single`, e a consolidação Python re-encoda p/ zstd. Sondei o mapeamento de tipos do
`parquetwrite` (ver §4.3) e confirmei que casa com o schema §17.2 (nomes/tipos), com
diferenças benignas documentadas (string→large_string; codec brotli≠zstd).

### 3.3 Arquivos
3 arquivos-alvo do card (corpo real) + 2 classes helper (`FEBudget`, `RunBuffer` — `classdef`
exige arquivo próprio) + 1 script de aceitação. Nenhum arquivo de terceiros tocado.

---

## 4. IMPLEMENTAÇÃO

### 4.1 Arquivos entregues
| Arquivo | Papel |
|---|---|
| `src/FEBudget.m` (novo) | Wrapper de FE = **fonte única do orçamento (D89)**. Dedup por X `<f8` bit-a-bit (`typecast(double(x),'uint8')`→hex numa `containers.Map`); cache-hit=0 FE + log; **hard-stop exato 31D−1** via `MException('PlatEMO:Termination')`; catálogo ① em **float64**; `init_X()` = fonte do `doe_hash` do CP-init. |
| `src/RunBuffer.m` (novo) | Coletor ②(membership)+③(surrogate C1/C3)+timing(§17.6) por geração (`addGeneration(view)`). `mkSurrogateRow` espelha `export.surrogate_row` (ausente → NULL). |
| `src/experiment.m` (corpo real) | Adapter transversal. **Função primária renomeada `experiment_run`→`experiment`** (o esqueleto F0-01 declarava `experiment_run`, que NÃO casava com o nome do arquivo → não era chamável em MATLAB). Ponte de avaliação, DoE via `parquetread` (D63/D87, nunca regenera), export das 4 camadas §17.2 (`parquetwrite` brotli+single+int32, SEM round D53, atômico `*.tmp→movefile` D58), `.jsonl` §17.5, manifesto §17.7, e **fechamento do CP-init**. Contém o run-STUB. |
| `src/hook_output.m` (corpo real) | `outputFcn(Algorithm,Problem,buf,bud,timing)` real (extrai a geração → `buf.addGeneration`), guardado, **pronto p/ o c217**. |
| `experiments.m` (corpo real) | Despachante: grid, `addpath(genpath(PlatEMO))`/worker (N.0.1), skip idempotente (`is_run_done_m`), parfor/serial, placar. `default_problems()` = 25 canônicos (BBOB_F*). |
| `scripts/accept_r1_00.m` (novo) | Aceitação MATLAB (roda o STUB + afere FE/cache/hard-stop/4-saídas/schema §17.2/CP-init). |

### 4.2 Como cada invariante-chave do card é cumprido
- **CP-init (metade MATLAB, bit-identidade da ①):** o STUB lê o DoE por `parquetread`
  (float64), injeta-o como fase `init` pelo FEBudget; `init_X()` (float64, mesma ordem) tem
  `sha256_rowmajor_f64 = sidecar.doe_hash`; e a ①(float32) = `single(DoE)` bit-a-bit. O hash
  ecoa em `manifest.doe_hash`.
- **Orçamento pelo wrapper, NÃO `obj.FE` (D89):** todo o saldo é do `FEBudget`; o hard-stop é
  `MException('PlatEMO:Termination')` capturado pelo runner; o `obj.FE` do PlatEMO nunca é
  consultado.

### 4.3 Sondagem do `parquetwrite` (para garantir schema §17.2 idêntico)
Escrevi uma tabela MATLAB e li o schema resultante com pyarrow:
```
MATLAB single   -> Arrow float32 ✓   (e single-NaN -> NULL Arrow ✓)
MATLAB int32    -> Arrow int32   ✓
MATLAB string   -> Arrow large_string  (Python usa string; benigno — consolidação re-encoda)
MATLAB missing  -> NULL ✓ ;  codec = BROTLI ✓
```
→ ajustei os defaults de string ausente de `""` para `<missing>` (NULL), casando com o `None`
do Python. (Numéricos ausentes já viram `single(NaN)`→NULL.)

---

## 5. VALIDAÇÃO — CADA CÓDIGO RODADO E O RESULTADO EXATO

> Esta é a seção que responde "que código rodou e qual foi o resultado". Todas as execuções
> abaixo foram rodadas de verdade nesta sessão (MATLAB R2025a + Python env-main).

### 5.1 Ambiente (§1) — `matlab -batch bridge_check`
`BRIDGE CHECK: PASS` — pyenv→`ponte_teste/bin/python`; numpy sum=6; pymoo 0.6.2; pyarrow 25.0.0.

### 5.2 Aceitação MATLAB do STUB — `accept_r1_00(problema, 0, 'data')`
| Problema | D | M | maxFE | Resultado | CP-init hash | ① init rows |
|---|---|---|---|---|---|---|
| MMF1 | 2 | 2 | 61 | **7/7 VERDE** | `89b8ce4ec510207f…` = sidecar | 21 = single(DoE) |
| DTLZ2 | 12 | **3** | 371 | **7/7 VERDE** | `71d3398a8fd224ef…` = sidecar | 131 = single(DoE) |
| ZDT1 | 30 | 2 | 929 | **7/7 VERDE** | `ed4a004aa0259182…` = sidecar | 329 = single(DoE) |
| BBOB_F1 | 10 | 2 | 309 | **7/7 VERDE** | `1a5143ccad7e9efe…` = sidecar | 109 = single(DoE) |

Os 7 checks por problema: (1) STUB→`ok`; (2) **FE final = 31D−1 EXATO** (linhas da ① ==
fe_final == maxfe); (3) **cache-hit=0 FE + hard-stop exato**; (4) 4 saídas presentes; (5)
**schema §17.2** (nomes+tipos das 4 camadas conferem); (6) **CP-init hash** init_X(float64) =
sidecar; (7) **CP-init camada ①** (float32) = single(DoE) bit-a-bit. **TOTAL FAIL = 0.**

### 5.3 Leitor Python INDEPENDENTE — `python scripts/accept.py R1-00-harness --alg stub …`
(env-main; um leitor que NÃO escreveu nada, só valida o que o MATLAB gravou.)
```
MMF1  (dim 2) : [OK] 4 saídas · [OK] FE=61  · [OK] DoE CP-init hash 89b8ce4… = sidecar → VERDE (exit 0)
DTLZ2 (dim 12): [OK] 4 saídas · [OK] FE=371 · [OK] DoE CP-init hash 71d3398… = sidecar → VERDE
ZDT1  (dim 30): [OK] 4 saídas · [OK] FE=929 · [OK] DoE CP-init hash ed4a004… = sidecar → VERDE
BBOB_F1(dim10): [OK] 4 saídas · [OK] FE=309 · [OK] DoE CP-init hash 1a5143c… = sidecar → VERDE
```

### 5.4 CP-init CROSS-LANGUAGE — cross-check em Python
```
manifest.doe_hash (MATLAB) : 89b8ce4ec510207f5199bc30…
DoE sidecar hash  (Python) : 89b8ce4ec510207f5199bc30…
CP-init cross-lang: MATCH ✓   |   status ok · fe_final 61 · maxfe 61 · ①rows(pyarrow)=61
```
→ a init X que o adapter MATLAB injetou (float64) hasheia idêntico ao DoE gerado em Python.

### 5.5 ③ surrogate (DTLZ2, M=3) — schema + semântica de NULL
```
cols = [algoritmo, problema, semente, regime, geracao, x0..x11, real_solution_id,
        mu_0, mu_1, mu_2, sigma_0..2, pred_tipo, pred_classe, pred_score, pred_confianca,
        modelo_flag, espaco_modelo, transf_tipo, transf_params]
names match Python export schema: True
NULLs corretos: pred_classe non-null=3/18 (só classifier) · espaco_modelo=3/18 (só C3) ·
                transf_tipo=3/18 · modelo_flag=18/18 · mu_0 non-null=15/18 · mu_1 NULLs=6
                (3 classifier + 3 mono-output b1 → mu_1.. NULL)
```

### 5.6 Despachante `experiments.m`
```
A) roster vazio            -> 0 células (andaime)
B) serial stub MMF1/0      -> [placar] ok=1
C) serial de novo          -> [placar] skipped=1   (idempotente — gate §22.6 kill+resume)
D) parfor 2 células {MMF1,ZDT3} -> [placar] ok=2   (produção; ponte por worker OK)
```

### 5.7 Teste ADVERSARIAL do FEBudget (espelha os 5 casos-limite do F0-03)
```
[OK] -0.0 ~= +0.0 (2 FE distintas)           [OK] hard-stop exato em 31D-1 (Termination)
[OK] NaN-idêntico = cache-hit (0 FE)          [OK] cache-hit pós-esgotamento = livre
[OK] near-dup (1 ULP) = distinta (1 FE)       [OK] int 1 == float 1.0 (cache-hit)
[adv_budget] PASS=6 FAIL=0
```
→ o `FEBudget` MATLAB casa byte-a-byte com o contrato do `budget.py` (a primitiva de
orçamento que os 10 configs MATLAB herdam).

### 5.8 `.jsonl` (§17.5) e manifesto — fidelidade de formato
```
.jsonl: 47 linhas = 1 header + 40 decision + 2 guard [cache_hit, hard_stop] + 3 timing + 1 footer
        footer: status ok · fe_final 61 · n_geracoes 3 · cache_hits 1 · cp_init True
manifest: run_id main_stub_MMF1_0 · status ok · maxfe 61 · fe_final 61 · n_geracoes 3 ·
          doe_hash(full) · cache_hits 1 · algo_version stub-R1-00 · paths.local {6 chaves}
```

### 5.9 Regressão (nada Python foi tocado, mas confirmei)
```
accept.py F0-01-harness : exit 0     accept.py F0-03-export : exit 0
accept.py F0-02-doe     : exit 0     accept.py F0-04-metrica: exit 0
scripts/preflight.py    : exit 0
.gitignore: data/experiments/ IGNORADO (outputs do STUB não versionam)
```

---

## 6. O QUE O c217 (E OS OUTROS MATLAB) HERDAM — e as 2 decisões deferidas

**Herda pronto e testado:** `FEBudget` (orçamento/dedup/hard-stop), `bridge_ctx`/`py_problem`
(ponte), `load_doe` (DoE do artefato), os 4 escritores §17.2, `RunBuffer`/`mkSurrogateRow`,
`hook_output`, o CP-init por-run, o despachante (skip/parfor/placar).

**Deferido ao c217 (NÃO é do R1-00):**
1. **`evalFcn` de LOTE (D61):** o `FEBudget.evaluate` é a primitiva **por-x**. O `UserProblem`
   4.15 chama o `evalFcn` com um **lote** (N×D) esperando `[dec,obj,con]`. O c217 escreve o
   embrulho: iterar as linhas por `bud.evaluate`, avaliar os primeiros `saldo` do lote e
   **lançar `PlatEMO:Termination` no MEIO do lote** quando zera. Não construído aqui de
   propósito (depende do `Solve` real — é o ponta-a-ponta do c217).
2. **`real_solution_id` (③) nullable:** no STUB toda linha ③ liga a um `solution_id` real →
   coluna int32 (casa com §17.2). Candidatos NÃO avaliados (o comum do c217) precisam de NULL,
   que o MATLAB não expressa em int32. O `write_surrogate` já cai p/ `double`+`NaN`→NULL quando
   há ausentes — **decisão a confirmar no c217** (evitar tipo variável entre runs de um mesmo alg).

**Receita N.0 para o `Solve` real (o c217 fia):** bypass do `platemo()`; `rng(seed,'twister')`
DEPOIS do `Problem` e ANTES do `Solve`; `save=-K`+`outputFcn` fixos; `maxRuntime=inf`;
`Problem`/`Algorithm` novos por task; `try/catch` em volta do `Solve`; e103/e74 em worker
dedicado (N.3/N.0-4.1).

---

## 7. ESTADO / HONESTIDADE / PONTOS PARA O VETO DO AUTOR

- **Gate objetivo do R1-00: 100% VERDE**, provado por 4 leitores independentes + 1 adversarial.
- **Limite honesto:** o R1-00 **não executa** o `Solve`/`UserProblem`/`outputFcn`-sob-Solve com
  algoritmo real — isso é o c217 (por desenho). O corpo do `hook_output` está escrito e guardado,
  mas roda pela 1ª vez no c217.
- **Ponto para veto #1:** o **renome `experiment_run`→`experiment`** (exigência do MATLAB:
  função primária == nome do arquivo `experiment.m`). Se preferir o arquivo `experiment_run.m`,
  é 1 renome + 2 call-sites.
- **Ponto para veto #2 e #3:** as 2 decisões deferidas (§6) — evalFcn de lote e int32-NULL.
- **Nada instalado** (pins são sua decisão, D80). **Nenhum arquivo de terceiros tocado.**

---

## 8. COMO REPRODUZIR (comandos exatos)

```matlab
% MATLAB, na raiz do repo:
addpath('src'); addpath('scripts');
nfail = accept_r1_00('MMF1', 0, 'data')     % 7/7 VERDE (idem DTLZ2/ZDT1/BBOB_F1)
experiments('algorithms',{'stub'},'problems',{'MMF1'},'seeds',0,'parallel',false)
```
```bash
# Python env-main, leitor independente:
ENVMAIN=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$ENVMAIN scripts/accept.py R1-00-harness --alg stub --problema MMF1 --semente 0 --dim 2
```
Outputs do STUB em `data/experiments/main/stub/` (gitignored — regeneráveis, deletáveis).

---

## 9. ARTEFATOS DE SAÍDA DESTA SESSÃO
- **Código:** `src/FEBudget.m`, `src/RunBuffer.m`, `src/experiment.m`, `src/hook_output.m`,
  `experiments.m`, `scripts/accept_r1_00.m`.
- **Commits** `[R1-00-harness]` (4, branch `experiment/definitive_algorythms`): `1e01304`
  (FEBudget+RunBuffer) · `06c0abe` (experiment.m+hook_output.m) · `5710655` (experiments.m) ·
  `dc1056f` (aceitação+handoff+INDEX).
- **Docs:** `handoff/R1-00-harness.md` (conciso) + este relatório · `cards/INDEX.md` → ✅.
