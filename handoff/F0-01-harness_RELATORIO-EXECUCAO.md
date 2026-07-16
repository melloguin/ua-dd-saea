# RELATÓRIO DE EXECUÇÃO — Sessão 2 · Cartão F0-01-harness (Fase 0, 1/4)

> **Para quem é este documento.** É a narrativa COMPLETA de como a sessão do implementador
> executou o cartão **F0-01-harness** — passo a passo, com o raciocínio, os achados, as decisões
> e os resultados verificados. Destinado à instância que gerou as instruções (a **torre de
> controle**, dona do `ORQUESTRACAO_MESTRE.md`) entender exatamente o que foi feito, como, e o
> que mudou. O handoff conciso é `handoff/F0-01-harness.md`; **este é o detalhado** (mesmo par
> handoff+RELATORIO da Sessão 1 de pré-voo).
>
> **Data:** 2026-07-15 · **Branch:** `experiment/definitive_algorythms` · **Interpretador:** `python3` (3.12.1 base).
> **Veredito:** **VERDE** — `python3 scripts/accept.py F0-01-harness` sai **0**; toda a aceitação do F0-01 passou; sem regressão no pré-voo.

---

## 0. Sumário executivo (TL;DR)

O cartão era **pura infraestrutura** (sem algoritmo, sem julgamento de fidelidade — D97): montar o
andaime comum da Fase 0 sobre o qual R1/R2/R3 vão plugar. Entreguei:

- **4 módulos novos stdlib** (`src/naming.py`, `src/atomic_io.py`, `src/manifest.py`, `src/audit_log.py`);
- **reescrita** do adapter (`src/experiment.py`) e do despachante (`experiments.py`), removendo a POC descomissionada e os imports mortos;
- **3 esqueletos MATLAB** (`experiments.m`, `src/experiment.m`, `src/hook_output.m`) — corpo real na R1;
- **enriquecimento do `scripts/accept.py`** com uma checagem de andaime real (sem tocar D97);
- **17 unittests** + `handoff/F0-01-harness.md` + `cards/INDEX.md`→✅.

**7 commits** `[F0-01-harness]`. **Nenhum código de algoritmo tocado.** **Nenhuma dependência instalada**
(descobri que o andaime não precisa — ver §3). **Nenhum pára-e-loga** foi necessário (não houve
ambiguidade/conflito de fontes que exigisse parar — D81).

---

## 1. Contexto e escopo recebido

- **Papel:** implementador do pipeline experimental do mestrado (`ua-dd-saea`), 1 sessão = 1 cartão.
- **Cartão:** F0-01-harness — o 1º dos 4 da Fase 0. Escopo textual do prompt: *"limpar imports mortos;
  os despachantes (§16.5); a esteira idempotente (resume + escrita atômica); o manifesto e o logger de
  auditoria (§17.5)."*
- **Explicitamente FORA:** DoE (F0-02), export/FE/gcs (F0-03), métrica (F0-04).
- **Regras firmes herdadas:** precedência D83 (Anexo S > §22 > D > corpo > …); pára-e-loga D81
  (ambiguidade ⇒ parar e perguntar, nunca escolher sozinho); D97 (fidelidade = análise manual do autor,
  o harness só instrumenta + gate objetivo); commits pequenos `[F0-01-harness]`.
- **Gate objetivo:** `python3 scripts/accept.py F0-01-harness` sai 0 + o que `00_fundacao/04` define p/ o F0-01.

---

## 2. PASSO 0 — Leitura de contexto (o que li, na ordem mandada, e o que extraí)

Li **somente** o conjunto autorizado (não abri a SPEC inteira nem bundles de outras rodadas):

| # | Arquivo | O que retirei que MUDOU a implementação |
|---|---|---|
| 1 | `HANDOFF_MESTRE.md` | Mapa geral; §10 (pré-voo feito), §11 (armadilhas de cartões futuros). A2, os 3 estágios, o export de 3 camadas. |
| 2 | `handoff/00-preflight.md` | Continuidade: pré-voo verde/idempotente; interpretador é `python3`; próximo = F0-01. |
| 3 | `claude_code_context/CLAUDE.md` | Regra de ouro (ler só o necessário), precedência D83, protocolo D81, DoD §22.6. |
| 4 | `cards/INDEX.md` (linha F0-01) | Tarefa exata do cartão + que F0-02/03/04 são os outros 3 (fronteira de escopo). |
| 5 | `00_fundacao/01` (regras globais) | §5.4/D89 (cache-hit=0 FE, wrapper é a fonte do orçamento), D55/D57/D58/D62, tabela D53–D100. |
| 6 | `00_fundacao/02` (arquitetura) | A2, §16.5 (despachantes+adapters), receita N.4 do MATLAB, S.6 (envs, brotli). |
| 7 | `00_fundacao/03` (export) | §17.1–17.7: 3 camadas + manifesto + `.jsonl` §17.5 + topologia §17.7 (local+bucket). |
| 8 | `00_fundacao/04` (plano/gates) | **A fonte da aceitação:** §22.0/22.1/22.6 + **cartão S.4-F0** (o delta exato) + S.8. |
| 9 | `00_fundacao/05` (problemas) | Os 25 problemas (MMF16_L3 removido → catálogo de 25); tabela S.5. |

**Achados-chave da leitura que definiram o desenho:**
- **A POC foi descomissionada (§16.5):** os 7 runners reimplementados + `NoisyProblem`/Kriging + toggle de
  ruído **não entram** — `experiment.py` deve ser **reescrito para chamar as mains oficiais**.
- **Cartão S.4-F0 dá o delta linha-a-linha** (imports mortos em `experiment.py:36-42`, `_invoke_runner`,
  `_apply_algorithm_overrides`, `ALGORITHM_DISPATCH` vazio; naming novo com token `{exp}`; manifesto+logger).
- **§17.7/D55:** o token `{exp}` no caminho evita a colisão principal×sub-estudos → a nomenclatura é central.
- **D58:** "run pronto = escrita atômica + fragmento de manifesto + skip" → a esteira idempotente.
- **D97:** o `accept.py` só verifica encanamento objetivo; nunca julga fidelidade.

---

## 3. Descoberta do estado REAL do código e do ambiente (o achado mais importante)

Antes de escrever, inspecionei os arquivos que o cartão modifica e o ambiente. Dois fatos mudaram a rota:

### 3.1 O `import src.experiment` estava QUEBRADO
`src/experiment.py` importava 7 runners POC (`src.nsgaII_runner`, `src.k_rvea_runner`, …) que **não existem
mais** no `src/`, e `sklearn` (também ausente). Confirmei: `python3 -c "import src.experiment"` →
`ModuleNotFoundError`. Ou seja, o repo não importava o próprio harness. A reescrita do adapter resolveu isso.

### 3.2 O env-main COMPLETO não está provisionado neste Mac (achado operacional)
Investiguei os interpretadores (é operacional, não spec — por isso não parei):

| Interpretador | Tem | NÃO tem |
|---|---|---|
| `python3` base (3.12.1) | numpy, pandas, pyarrow | joblib, tqdm, sklearn, **pymoo** |
| `~/ponte_teste` (venv 3.11.9, o da ponte MATLAB) | numpy 2.4.6, scipy 1.17.1, **pymoo 0.6.2** | pandas, pyarrow, joblib, tqdm, sklearn |
| pyenv 3.11.9 / 3.10.14 / 3.8.19 | — | stack científico (base pura) |

**Conclusão e decisão de projeto:** em vez de parar para instalar (env/pin é decisão do autor — D80/§8)
ou de bloquear o cartão, **desenhei o andaime para ser leve**: os 4 módulos de infra são **stdlib puro**, o
adapter faz **import lazy** de `src.problems` (que puxa pymoo), e o despachante faz **import lazy** de
joblib/pandas/tqdm. Resultado: **toda a aceitação do F0-01 roda no `python3` base**, sem env-main. As libs
pesadas só são exigidas quando há execução real de algoritmo/export — ou seja, a partir do **F0-02/F0-03**,
que aí sim precisam de pandas+pyarrow+pymoo no mesmo interpretador (ver §9, heads-up).

*(Por que isso é correto e não um atalho: o harness scaffold É naturalmente leve; carregar pesos só sob
demanda é boa prática e mantém a promessa "o interpretador é `python3`". A parede de env cai no cartão que
de fato gera parquet/DoE.)*

---

## 4. PASSO 1 — Plano apresentado (antes de qualquer código)

Apresentei ao autor um plano em ≤15 linhas: reescrever `src/experiment.py` (adapter A2, catálogo 25,
dispatch vazio, POC removida); criar 4 módulos stdlib (naming/atomic_io/manifest/audit_log); reescrever
`experiments.py` (imports lazy, sentinela `none`, esteira idempotente, 3 estágios); esqueletos MATLAB;
enriquecer `accept.py` + `tests/`. Declarei as 2 decisões de engenharia (sentinela `none`; fronteira da
escrita atômica F0-01×F0-03) e o heads-up de ambiente, e afirmei **não haver ambiguidade bloqueante** →
segui direto para a execução (autorizado pelo prompt).

---

## 5. PASSO 2 — Execução, etapa por etapa (com resultados verificados)

### 5.1 `src/naming.py` — fonte ÚNICA da nomenclatura (§17.7/D55)
Convenção canônica num só lugar: `run_id={exp}_{alg}_{problema}_{semente}`, base `exp_{run_id}`, as 4 camadas
(`__real/__pop/__surrogate/__timing.parquet`), `.jsonl`, `.manifest.json`, prefixo do blob GCS, validação do
token `{exp}` (`main|off|batch|sweep-<tier>-<dist>`) e das camadas. **Motivo de ser fonte única:** quem
**escreve** (despachante) e quem **verifica** (`accept.py`) importam o MESMO módulo → impossível divergirem
no nome do arquivo.

### 5.2 `src/atomic_io.py` — escrita atômica (D58)
`atomic_write_bytes/text` + context manager `atomic_path` (grava em `*.tmp` no MESMO diretório → `os.replace`
atômico; limpa o `.tmp` se o bloco estourar). É a primitiva da esteira; **F0-03 reusa** para as 3 tabelas.

### 5.3 `src/manifest.py` — fragmento de manifesto + esteira + placar (D58/§17.2/§17.6)
`new_manifest(...)` monta o dicionário do run (status/n_retries/stack_trace, timing+desdobramento §17.6,
`fit_series`, `paths.local`+`paths.bucket`, `upload_status`, `doe_hash`/`repo_hash`/`env` prontos p/ as
rodadas); `write_manifest` grava atômico; `is_run_done` = **resume D58** (manifesto ok **E** camadas presentes
**E** footers válidos); `Scoreboard` = placar corrido (ok/retried_ok/failed/skipped).

### 5.4 `src/audit_log.py` — logger `.jsonl` (§17.5)
`AuditLogger` com `header/decision/partial/guard/timing/footer` — uma decisão por linha, timestamp em cada.
**D97 respeitado por construção:** só instrumenta; não julga fidelidade, não é gate.

**➤ Verificação (5.1–5.4):** rodei um smoke que exercita naming + atomic (sem `.tmp` residual; falha no meio
não cria alvo) + manifesto (round-trip, `is_run_done`) + placar + logger (6 registros na ordem certa). **Tudo
verde no `python3` base.** Descobri de passagem que o `pyarrow` ESTÁ no base → a validação de footer do
`is_run_done` é real (rejeita parquet corrompido — provado). **Commit `85fb331`.**

### 5.5 `src/experiment.py` — reescrita para esqueleto de adapter A2
De POC para o **contrato de adapter** (§16.5.3): catálogo `PROBLEM_CLASSES` de **25** (removi `MMF16_L3`),
`_instantiate_problem` com **import lazy** de `src.problems`, `ALGORITHM_DISPATCH={}`, `run()` que levanta
`NotImplementedError` (despacho é R1/R2/R3), e os **6 passos do contrato documentados** (bounds/sinal §5.5,
sementes §5.3+offset D22, maxFE+DoE+hard-stop, ponte, export, retry D23). **Removidos:** 7 imports mortos,
`_invoke_runner`, `_apply_algorithm_overrides`, kriging/noisy/`experiment_sa_moea`.

### 5.6 `experiments.py` — despachante Python
`DEFAULT_ALGORITHMS=[c262,c154,e81,c122,c149,b5,c311]` (stack Python; os MATLAB vão no `experiments.m`),
25 problemas, **30 sementes `range(29)+[42]`**, token `--exp`, esteira idempotente por manifesto, 3 estágios
(pré-cache stub→F0-02 · grid · consolidação stub→F0-03), placar, política **D23 (1 retry)**. **Imports pesados
lazy** (joblib só se `n_jobs>1`; pandas só na consolidação). **Sentinela `--algorithms none`** = roster vazio.

**➤ Verificação (5.5–5.6):**
- `import src.experiment` → **OK** (25 problemas, dispatch vazio).
- `experiments.py --algorithms none --problems MMF1 --seeds 0` → **monta grid/manifesto, exit 0**.
- **Demonstração ponta-a-ponta do encanamento:** rodei `--algorithms c262 --problems MMF1 --seeds 0` (data-root
  em scratch): gravou o **manifesto** (paths local+bucket corretos, `upload_status=pending`) e o **`.jsonl`**
  (header/not_implemented/footer), placar `failed=1`, exit 0. Ou seja: com o dispatch vazio, um run fecha
  **`failed` honesto** (adapter não ligado) — nunca silencioso (D23). **Commit `e1868f1`.**

### 5.7 Esqueletos MATLAB (`experiments.m`, `src/experiment.m`, `src/hook_output.m`)
Esqueletos da **receita N.4**, com o corpo real explicitamente deixado para **R1-00-harness**. Já carregam,
em destaque, as **armadilhas críticas** para a R1 não violar: bypass do `platemo()`; `rng(seed,'twister')`
**depois** de construir o Problem (D59); `'save',-K` + `'outputFcn'` sempre; `maxRuntime=inf`; **hard-stop pelo
contador do WRAPPER de FE, não `obj.FE`** (D89); `parquetwrite` brotli+single **sem `round`** (S.6); e103/e74 em
worker dedicado (D95); assert das toolboxes (S.6). **Não executei MATLAB** (não há nesta CLI) — são esqueletos
validados por leitura, a serem ligados/validados na R1. **Commit `cd38020`.**

### 5.8 `scripts/accept.py` — checagem de andaime F0-01 (sem tocar D97)
Adicionei `check_scaffold()`: verifica que os módulos de infra importam, que o catálogo é 25 (MMF16_L3
removido), que o dispatch está vazio na Fase 0, que o naming §17.7 bate, e que manifesto+`.jsonl` fazem
round-trip num tempdir. Passei o `accept.py` a **importar `src.naming`** (mesma fonte do escritor). Mantive os
checks de run (4 saídas/FE/DoE) para os cartões futuros. **A política D97 ficou intacta** — só encanamento
objetivo, com o lembrete impresso.

### 5.9 `tests/` — unittests
`test_naming.py` (3 camadas + jsonl + manifesto + blob + token) e `test_manifest_audit.py` (atomic, manifesto
round-trip, `is_run_done`, placar, logger). **17 testes, stdlib.** **Commit `17ac02f`.**

### 5.10 Demonstração da esteira idempotente (resume/force)
Simulei um run **concluído** (manifesto `ok` + 4 parquets válidos) e rodei o despachante apontado para lá:
- resume → **PULOU** (`skipped=1`, 0 a rodar);
- `--force` → **re-rodou** (e falhou, dispatch vazio).
Prova do gate global §22.6 (kill+resume/esteira idempotente).

### 5.11 Correção de bug latente na contagem de retry (D23)
Numa releitura, achei que `_run_one` não contava `n_retries` corretamente num **retry bem-sucedido** (ficaria 0
em vez de 1). O F0-01 não exercita esse caminho (dispatch sempre `NotImplementedError`), mas **R1/R2/R3
dependem** dessa lógica. Corrigi e provei com 3 casos (sucesso→`ok`/n=0; falha-depois-sucesso→`retried_ok`/n=1;
falha-sempre→`failed`/n=1 + stack_trace). **Commit `bf2edff`.**

---

## 6. PASSO 3 — Aceitação (resultados consolidados)

Aceitação do F0-01 (recorte "harness" do cartão S.4-F0 + §22.1/§22.6), **toda verde**:

| Critério de aceitação | Como verifiquei | Resultado |
|---|---|---|
| **Gate objetivo** `python3 scripts/accept.py F0-01-harness` | execução direta | **exit 0** (andaime OK) |
| `python3 -c "import src.experiment"` OK | execução direta | **OK** — 25 problemas, dispatch vazio |
| `experiments.py --algorithms none --problems MMF1 --seeds 0` monta grid/manifesto | execução direta | **exit 0** |
| unit-test do naming (3 camadas + jsonl + manifesto) | `python3 -m unittest discover -s tests` | **17/17 OK** |
| esteira idempotente (resume/skip) — gate global §22.6 | demo run `ok` simulado + `--force` | **pula / re-roda** conforme esperado |
| política D23 (1 retry, status ok/retried_ok/failed) | teste com runner mockado | **correto** (n_retries certo) |
| `accept.py` REPROVA regressão (não é verde vazio) | injetei dispatch sujo | **FAIL/VERMELHO** como esperado |
| `py_compile` de todos os módulos Python | execução direta | **compilam** |
| **Não-regressão:** pré-voo da Sessão 1 | `python3 scripts/preflight.py` | **exit 0, "pré-voo OK ✓"** |

**Mapeamento aos 7 critérios §22.6 (para o F0-01, que não roda algoritmo):** os critérios "de run" (FE exato,
DoE pareado, 4 parquets, timing) pertencem a F0-02/F0-03; o F0-01 entrega os **mecanismos** que os tornam
verificáveis (naming, manifesto com os 2 caminhos+upload_status §17.7, guarda-logging via `audit_log.guard`,
`is_run_done` p/ o global "kill+resume"). Fidelidade (critério B) = manual do autor (D97), fora daqui.

---

## 7. Decisões de engenharia tomadas (com justificativa; nenhuma é fidelidade)

1. **`--algorithms none` = roster vazio.** A aceitação usa esse comando literal; monta grid/manifesto sem
   executar. Interpretação óbvia, não é definição da SPEC.
2. **Fronteira "escrita atômica" F0-01×F0-03.** O prompt lista "escrita atômica" no F0-01 e o cartão F0-03
   também. Resolvi: **F0-01 entrega a primitiva** (`atomic_io`) **+ o fragmento de manifesto** (D58, o
   mecanismo da esteira); **F0-03 a aplica** às 3 tabelas parquet + wrapper de FE. D58 é o mecanismo; F0-03 é o uso.
3. **Nome do manifesto.** D58 diz `{run_id}.manifest.json`; realizei como `exp_{run_id}.manifest.json` para
   TODOS os artefatos do run compartilharem a base `exp_{run_id}` do §17.7. Harmonização D58×§17.7, não conflito.
4. **Imports lazy** (problems no adapter; joblib/pandas/tqdm no despachante). Mantêm o andaime rodando no
   `python3` base e evitam puxar peso que o `none`-path não usa. (Ver §3.)

**Por que NÃO houve pára-e-loga (D81):** nenhuma dessas é uma definição ausente ou um conflito entre fontes —
são escolhas de engenharia dentro do que a SPEC deixa livre, registradas para o autor conferir. O único ponto
sensível (ambiente) é operacional (provisionamento), não spec; resolvi por design sem instalar nada.

---

## 8. Fronteiras de escopo — o que NÃO foi feito (por design) e os ganchos deixados prontos

| Fora de escopo | Cartão dono | Gancho já deixado no F0-01 |
|---|---|---|
| `src/doe.py` (LHS-maximin D87), dataset offline (D90), `seeds.json` (D91), CP-init | **F0-02-doe** | estágio 1 do despachante é stub que anuncia; `doe_hash` já existe no manifesto; `accept.check_doe_hash` pronto |
| Wrapper de FE (cache-hit=0 D89) + hard-stop; schemas 3 tabelas (C1/C3/C4); `src/gcs.py` (dual-write+sync); consolidação brotli→zstd | **F0-03-export** | `atomic_io` pronto p/ os parquets; `paths.bucket`+`upload_status` no manifesto; estágio 3 stub |
| Esqueleto da métrica + smoke HV(F1)=1,0433 (D92) | **F0-04-metrica** | — |
| Corpo real dos `.m` (ponte pyenv, UserProblem, export, manifesto MATLAB) | **R1-00-harness** | esqueletos com a receita N.4 + armadilhas destacadas |

---

## 9. Achados e heads-ups (o que o autor / próximas sessões precisam saber)

1. **⚠ Ambiente — blocker latente para F0-02/F0-03 (não bloqueou o F0-01):** o **env-main completo não está
   provisionado** neste Mac (detalhe na tabela §3.2). F0-02/03 precisam de **pandas+pyarrow+pymoo num mesmo
   interpretador** (pandas/pyarrow p/ os parquets; pymoo p/ instanciar problemas e gerar o F do dataset offline).
   **Recomendação:** provisionar o env-main (S.6: numpy/pandas/pyarrow/joblib/tqdm/scipy/pymoo==0.6.2 …) sobre
   **pyenv 3.11.9** e **registrar as versões no manifesto**. A **decisão de env/pin é do autor** (D80/§8) — por
   isso **não instalei nada**.
2. **`import src.experiment` estava quebrado antes desta sessão** (runners POC inexistentes + sklearn ausente).
   Agora importa limpo em qualquer interpretador.
3. **`ORQUESTRACAO_MESTRE.md` e `PLANO_IMPLEMENTACAO.md`** apareceram no working tree como **untracked, não
   criados por esta sessão** (são os docs da torre de controle). **Deixei-os intactos** (fora do escopo do
   cartão). O **Status board do `ORQUESTRACAO_MESTRE.md` ainda precisa marcar F0-01 ✅** — isso é papel da
   torre de controle, não deste implementador.
4. **MATLAB não foi executado** (não há MATLAB nesta CLI) — os `.m` são esqueletos, validados de fato na R1.
5. **`accept.py` para F0-01 valida o andaime** (sem `--alg`); a partir de R1, passar `--alg`/`--dim` exercita
   os checks de run (4 saídas/FE/DoE), que F0-02/03 tornam verdes.

---

## 10. Commits desta sessão (branch `experiment/definitive_algorythms`)

```
99f7b1f  [F0-01-harness] handoff da sessão + marca F0-01 ✅ no INDEX
bf2edff  [F0-01-harness] corrige contagem de n_retries no _run_one (D23)
17ac02f  [F0-01-harness] accept.py: checagem de andaime F0-01 + unittests (17 testes)
cd38020  [F0-01-harness] esqueletos MATLAB (receita N.4, armadilhas D59/D89/S.6; corpo real R1)
e1868f1  [F0-01-harness] despachante Python + adapter A2 (POC removida, dispatch vazio, esteira idempotente)
85fb331  [F0-01-harness] infra stdlib: naming + atomic_io + manifest + audit_log
```
*(+ este relatório.)* Working tree limpo exceto os 2 untracked da torre de controle (§9.3), intocados.

**Arquivos por operação:**
- **Novos:** `src/naming.py`, `src/atomic_io.py`, `src/manifest.py`, `src/audit_log.py`, `experiments.m`,
  `src/experiment.m`, `src/hook_output.m`, `tests/__init__.py`, `tests/test_naming.py`,
  `tests/test_manifest_audit.py`, `handoff/F0-01-harness.md`, este relatório.
- **Reescritos:** `src/experiment.py`, `experiments.py`.
- **Editados:** `scripts/accept.py`, `cards/INDEX.md`.
- **Removido (conteúdo):** a POC de `src/experiment.py`/`experiments.py` (runners, kriging, noisy). Não toquei
  `src/processing.py` (mantém a capacidade de ruído documentada+desligada, Anexo Q — só deixei de importá-la).

---

## 11. Como reproduzir a aceitação (comandos exatos, tudo no `python3` base)

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea
python3 scripts/accept.py F0-01-harness            # → exit 0 (VERDE)
python3 -c "import src.experiment"                 # → OK
python3 experiments.py --algorithms none --problems MMF1 --seeds 0   # → monta grid, exit 0
python3 -m unittest discover -s tests -t .         # → 17 testes OK
python3 scripts/preflight.py                        # → não-regressão: "pré-voo OK ✓", exit 0
```

---

## 12. Estado do cartão

**F0-01-harness = ✅ FECHADO (VERDE).** Base pronta para os 3 cartões seguintes da Fase 0 (F0-02-doe,
F0-03-export, F0-04-metrica) e, depois, R1-00-harness. Próxima sessão deve começar lendo
`handoff/F0-01-harness.md` (conciso) — este relatório é o detalhe de execução.
