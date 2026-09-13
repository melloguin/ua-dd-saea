# DI09-retrofit-R1 — RELATÓRIO DE EXECUÇÃO

> **Para:** a instância-torre que emitiu o cartão `DI09-retrofit-R1`.
> **Sessão:** 2026-07-19, stack MATLAB, committer único.
> **Cartão:** instrumentação de assertividade dos surrogates (DI-09 sonda canônica + DI-10
> enriquecimento do `.jsonl`, SPEC v5.2.1) nos 9 configs SA-MATLAB + o pacote leve dos 4 pisos.

---

## 0. RESPOSTA DIRETA: a etapa NÃO está 100% pronta

**Estado: infra transversal COMPLETA e verificada · 2 de 9 configs entregues (c217, c141) · 7 configs
+ o pacote dos pisos NÃO iniciados.**

O que está pronto está **validado com código executado**, não por inspeção: 24 runs reais de MATLAB,
gate de não-perturbação bit-a-bit em 18 runs, `accept.py` exit 0 em 6/6, 194 testes Python OK,
preflight OK. Os números estão no §3.

**Faltam:** b1, b4, e7, b3, e103, e74, c238 (7 configs) + o pacote leve dos 4 pisos.
A **receita está mecânica e provada** em dois configs de naturezas diferentes (um classificador
par-a-par e um regressor interpolante), o que é o principal ativo desta sessão — ver §7.

⚠ **A regressão de encerramento do cartão NÃO foi feita integralmente**: o cartão pede
"F0×4 + 13 configs × MMF1 + preflight + suíte" **ao final dos 9**. Rodei a parte que já faz sentido
agora (13 configs × MMF1 + preflight + suíte — §3.4), mas os F0×4 e a re-validação final ficam para
o encerramento real.

---

## 1. Processo executado, etapa a etapa

### Etapa 0 — Contexto (PASSO 0 do cartão)
Li na ordem exigida: `CONTRATO_DE_DADOS.md` **inteiro** · SPEC §17.2.2 + §S.7.1 + §17.6 (por grep) ·
`REGISTRO_DECISOES_IMPLEMENTACAO.md` (DI-09/DI-10 + o invariante de não-perturbação) ·
`claude_code_context/CLAUDE.md` + `HANDOFF_MESTRE.md` §10/§11. Não li bundles de algoritmo inteiros
nem os handoffs de c262/c154, conforme instruído.

**Gate de ambiente (D81), conferido ANTES de qualquer código:**
`matlab -batch "pe=pyenv; py.numpy.array([1,2,3]).sum()"` → **pyenv 3.11 → `~/ponte_teste/bin/python`,
soma = 6 ✓**, MATLAB **25.1.0.2973910 (R2025a) Update 1**. `PY` → Python 3.11.9, pyarrow 25.0.0 ✓.

### Etapa 1 — Recon (11 agentes, read-only)
Fan-out de 11 agentes sobre os 9 configs + a infra do writer, ~1,2 M tokens, 325 chamadas de
ferramenta, tudo ancorado em `file:line`. Produziu, por config: onde o modelo é treinado, a API exata
de predição em lote, o ponto de inserção da sonda, se o preditor consome RNG, o que é "geração" ali,
cada campo DI-10 com sua variável, e os riscos de perturbação.

**Achados estruturais do recon que moldaram o desenho:**
- `write_surrogate` aplicava **um `regime` escalar ao arquivo inteiro** — impossível misturar
  busca+sonda na mesma ③ sem tornar `regime` por linha.
- `man.timing` **nascia zerado** e só o e103 o preenchia (`experiment.m:1841` era a única atribuição
  no repo inteiro) — confirma a auditoria da torre ("ZERADO em 10/12").
- `write_timing` lia `geracao`/`n_acumulado`/`tempo_fit_s` **sem guarda** — qualquer linha de timing
  nova derrubaria o export no fim do run.
- `RunBuffer.mkSurrogateRow` usa `inputParser` com `KeepUnmatched=false` ⇒ passar campo novo **erra
  em runtime**.
- O lado **Python já estava retrofitado** (`export.py` com `fe_treino_max`, `regime` por linha,
  `timing_schema` com 7 campos) — o gap era só do MATLAB.

### Etapa 2 — PASSO 1: plano + pára-e-pergunta (D81)
Apresentei o plano (≤20 linhas) e **parei** para levar ao autor as ambiguidades que o
CONTRATO+SPEC não resolviam. **Cinco decisões cravadas** → registradas como **DI-12.1 a DI-12.5** em
`REGISTRO_DECISOES_IMPLEMENTACAO.md` (PARTE A2). Resumo em `handoff/DI09-retrofit-R1.md` §1.

### Etapa 3 — Infra transversal (commit `cc3eee1`)
`load_sonda` (+ CP do `x_hash` no arranque) · `SondaState` (novo) · `regime` por linha +
`fe_treino_max` na ③ · `tempo_pred_sonda_s` + `tempo_geracao_s` na ④ + `field_or` em tudo ·
`fill_manifest_timing` (bloco `timing` obrigatório + `fit_series` + `man.sonda`) · cronômetro
`tempo_aval_real_s` no `FEBudget`.

**Autoteste:** estendi o config `stub` (o autoteste do harness) para exercitar o caminho inteiro sem
algoritmo real — inclusive **prova de RNG** (estado *e* sequência de sorteios) e os dois casos do
`finalProbe`. Assim uma regressão da infra aparece no `stub`, não no primeiro config real.

### Etapa 4 — c217 (commit `845743a`) e c141 (commit `ff38f2b`)
Receita: `<alg>_sonda.m` novo + 1 linha no arquivo stock (pós-fit, pré-decisão, **pré-`Evaluation`**)
+ 4 pontos no `run_<alg>` + campos DI-10 no instrument. Detalhe por config em
`handoff/DI09-retrofit-R1.md` §7.

### Etapa 5 — Correções descobertas durante a execução
- **Performance (durante o c217/DTLZ2):** o `inputParser` custava **148 µs/linha** ⇒ ~87 s/run só no
  c217/ZDT1. Adicionei `RunBuffer.mkSurrogateRows` (lote) com **equivalência campo-a-campo provada**.
- **`DTLZ2_d15` abortou o run:** não tem artefato de sonda. Investiguei: é problema **só de piloto**,
  fora do grid. `load_sonda` passou a tolerar, gravando `man.sonda.status='artefato_ausente'`.
- **`n_acumulado` do c217 media o ARQUIVO, não o TREINO** — corrigido (⚠ pendente de ratificação, §5).

### Etapa 6 — Alinhamento cross-stack (commits `47daa76`, `a5f6eab`)
A sessão retrofit-R2 escalou (commit `652e24d`) duas divergências entre stacks. Ambas fechadas:
- **`tempo_geracao_s`**: o meu **incluía** a sonda; o Python desconta. Corrigi para descontar.
- **Cadência**: MATLAB `1,3,5,…` × Python `1,2,4,6,…`. O autor decidiu **alinhar o MATLAB ao Python**
  (DI-12.5). Re-rodei e re-validei os 2 configs.

### Etapa 7 — Documentação
`handoff/DI09-retrofit-R1.md` (estado + receita + provas) · **DI-12** no registro canônico de
decisões · agenda de pendências ampliada com os **doc-syncs da torre** (itens 5–8).

---

## 2. Código executado — inventário completo

| # | Comando | Resultado |
|---|---|---|
| 1 | `matlab -batch "pyenv; py.numpy.array([1,2,3]).sum()"` | pyenv 3.11 → `ponte_teste`; **soma = 6**; R2025a Update 1 ✓ |
| 2 | `PY -c "import pyarrow,numpy"` | py 3.11.9, pyarrow 25.0.0 ✓ |
| 3 | `experiment('stub','MMF1',0,...)` (autoteste da infra) | ✓ — ver §3.1 |
| 4 | `bench_row.m` (custo do `mkSurrogateRow`) | **148,1 µs/linha** → 87 s/run no c217/ZDT1 |
| 5 | `bench_rows.m` (equivalência + custo do lote) | **0 divergências** em 2000 linhas × 15 campos; **3,8 µs/linha (38×)** |
| 6 | `experiment('c217',...)` × MMF1/DTLZ2/DTLZ2_d15/ZDT1 | 4 runs ok |
| 7 | `experiment('c141',...)` × MMF1/DTLZ2/ZDT1 | 3 runs ok |
| 8 | **Regressão:** `experiment(<alg>,'MMF1',0)` × b1, b3, b4, e7, c238, e74, e103, moead, nsga2, nsga3, smsemoa | **11 runs ok** |
| 9 | `naoperturbacao.py` (① bit-a-bit vs `_baseline_pre_retrofit`) | **18 runs: IDÊNTICA em todos** |
| 10 | `auditar.py` (DI-09/DI-10 completo) | **6 runs: TUDO VERDE** |
| 11 | `scripts/accept.py R1-<alg> …` | **exit 0 em 6/6** |
| 12 | `PY -m unittest discover -s tests -q` | **194 testes OK** (1 skip) |
| 13 | `PY scripts/preflight.py` | **pré-voo OK ✓** (1 deferimento intencional conhecido) |

*(Os validadores `naoperturbacao.py` e `auditar.py` foram escritos no scratchpad da sessão e **não
versionados** — são ferramenta de verificação, não entregável. O conteúdo das checagens está no §3.3;
recriá-los é trivial e o §7 recomenda promovê-los ao `accept.py`, que é território `.py`.)*

---

## 3. Resultados das validações

### 3.1 Autoteste da infra (`stub`/MMF1)
```
sonda_x_hash_ok = 1        rng_intacto = 1            final_foi_noop = 1
sonda_n_blocos  = 3        rng_mesma_sequencia = 1    final_disparou = 1
sonda_n_linhas  = 6000     sonda_n_falhas = 0         tempo_aval_real_s = 0.0129
```
`rng_intacto` compara o **estado** do RNG antes/depois; `rng_mesma_sequencia` compara o **sorteio
seguinte** contra um run sem sonda nenhuma — é a prova que interessa (estado igual mas sequência
diferente passaria despercebido no primeiro teste).

### 3.2 🔴 GATE CENTRAL — não-perturbação (① bit-a-bit vs baseline pré-retrofit)

**Os 2 configs retrofitados:**

| config/problema | resultado |
|---|---|
| c217/MMF1 | **IDÊNTICA** — 61 linhas × 10 colunas |
| c217/DTLZ2 | **IDÊNTICA** — 371 × 21 |
| c217/DTLZ2_d15 | **IDÊNTICA** — 464 × 24 |
| c217/ZDT1 | **IDÊNTICA** — 929 × 38 |
| c141/MMF1 | **IDÊNTICA** — 61 × 10 |
| c141/DTLZ2 | **IDÊNTICA** — 371 × 21 |
| c141/ZDT1 | **IDÊNTICA** — 929 × 38 |

**Os 11 configs NÃO retrofitados** (regressão da infra compartilhada — `FEBudget.m`, `RunBuffer.m`,
`write_surrogate`, `write_timing` são usados por todos):

`b1` · `b3` · `b4` · `e7` · `c238` · `e74` · `e103` · `moead` · `nsga2` · `nsga3` · `smsemoa`
→ **IDÊNTICA em MMF1 nos 11** (61 × 10 cada).

> Esta regressão é o que prova que instrumentar o `FEBudget` (DI-12.4) e mexer nos writers **não
> tocou a busca de nenhum config**, inclusive os que ainda nem foram retrofitados.

### 3.3 Auditoria DI-09/DI-10 (6 runs, todos TUDO VERDE)
O que cada auditoria confere: coluna `fe_treino_max` e `regime` na ③ · linhas de sonda = **S × nº de
disparos exatas** · blocos **contíguos** de 2000 · **ordem do artefato preservada** em cada bloco
(join por posição) · `real_solution_id` NULL em toda linha de sonda · `fe_treino_max` preenchido
(sonda **e** busca) e ≤ `fe_final` · as 4 colunas da ④ presentes e preenchidas · `timing` do
manifesto com os 4 campos ≠ 0 · `fit_series` não vazia · `man.sonda.n_blocos` == blocos na ③ ·
`man.sonda.x_hash` == sidecar do artefato · eventos `sonda` no jsonl == nº de blocos · mínimo comum
DI-10 presente no `<alg>_gen`.

**Blocos de sonda medidos** (após o alinhamento de cadência):

| config | MMF1 | DTLZ2 | ZDT1 |
|---|---|---|---|
| c217 | 21 × 2000 | 117 × 2000 | **296 × 2000 = 592 000 linhas** |
| c141 | 6 × 2000 | 33 × 2000 | 78 × 2000 |

### 3.4 Regressão de encerramento (parcial)
`preflight.py` → **pré-voo OK ✓** (exit 0; o único deferimento é o pin conhecido do `desdeo-emo`).
Suíte Python → **194 testes OK** (1 skip). *(Nenhum `.py` foi tocado por mim; o crescimento
122 → 174 → 194 vem da sessão R3-00, que está com arquivos não commitados na árvore.)*
13 configs × MMF1 → **13/13 ok** (os 11 acima + c217 + c141).
**Falta:** F0×4 e a re-validação final — pertencem ao encerramento dos 9.

### 3.5 Custo (insumo para o dimensionamento M7)
Wall dos runs retrofitados, **já com a sonda**: c217/MMF1 12,3 s · c217/DTLZ2 40,3 s ·
c217/ZDT1 107,7 s · c141/MMF1 4,6 s · c141/DTLZ2 25,2 s · c141/ZDT1 171,1 s.
O c217/ZDT1 gera **592 mil linhas de ③ de sonda num único run** — número real, útil para
a checagem de disco que a DI-09 mandou fazer no piloto M7.

---

## 4. O que foi entregue

**Commits** (todos com o ritual anti-mistura: `add` explícito → `git diff --cached --name-only` →
commit, num comando; nunca `git add -A`):

| commit | conteúdo |
|---|---|
| `cc3eee1` | infra: `load_sonda` + `SondaState` + colunas novas ③/④ + timing do manifesto |
| `845743a` | c217: sonda PNN-par + DI-10 + construtor de linhas em lote |
| `ff38f2b` | c141: sonda RBF-MQ3 (μ sem σ) + DI-10 da cascata |
| `c91587b` | handoff |
| `47daa76` | B-0b: `tempo_geracao_s` desconta a sonda (alinha ao Python) |
| `a5f6eab` | cadência alinhada: `g = 1,2,4,6,…` |
| `5147fb6` | **DI-12** no registro de decisões + agenda de doc-syncs |

**Arquivos novos:** `src/SondaState.m` · `src/c217_sonda.m` · `src/c141_sonda.m` ·
`handoff/DI09-retrofit-R1.md` · este relatório.
**Modificados:** `src/experiment.m` · `src/RunBuffer.m` · `src/FEBudget.m` ·
`src/c217_instrument.m` · `src/c141_instrument.m` · `PCSAEA.m` (1 linha de sonda + 3 de timing) ·
`MMRAEA.m` (idem) · `REGISTRO_DECISOES_IMPLEMENTACAO.md`.

**Faixa respeitada:** nenhum `.py` tocado · `scripts/gen_sonda.py` e `data/sonda/**` só lidos ·
`data/experiments/_baseline_pre_retrofit/**` intocado · SPEC/bundles/CONTRATO/INDEX intocados.

---

## 5. 🔴 DEFINIÇÕES EM ABERTO — a torre deve levantá-las com o autor

> Estas **não** são resolvíveis com o CONTRATO+SPEC na mão. As de **A** bloqueiam configs específicos
> e devem ser decididas **antes** de retomar aquele config; as de **B** são ratificações de escolhas
> que já tomei e estão valendo em código.

### A. Bloqueantes (definição a CRIAR — o texto normativo não a contém)

**A-1 · e103: qual é o escalar `margem_3sigma`?** *(bloqueia o e103)*
O §6.1 pede *"o valor que decide o KFlag"*, mas o mecanismo é **booleano com relaxação**:
`sum(site,3) >= M-1` sobre pares i≠j (`JudgeModel.m:38`, eps=1e-5). **Não existe UM valor.**
Proposta do recon (precisa de ratificação — é definição **criada**, não lida): para cada par, o
(M−1)-ésimo maior de `(I − MSEI)` entre os M objetivos; `margem_3sigma = min` sobre os pares
(vale `margem>0 ⟺ KFlag==1`). *Alternativas razoáveis existem — daí ser decisão do autor.*

**A-2 · e103: com que `geracao` carimbar os 2 blocos offline da sonda?** *(bloqueia o e103)*
O e103 é offline: a sonda roda **1× por modelo** (Kriging e RBFN), fora do laço de gerações.
`experiment.m` deriva `n_geracoes` de `unique(geracao)` sobre a ③ — carimbar com `g=0` faria
`n_geracoes` virar 100 em vez de 99, **mudando a certidão do run sem nada ter mudado na busca**.
Resolvi filtrar `regime=='sonda'` da derivação (preserva o manifesto), **mas o valor a carimbar
segue indefinido**: `0`? `99` (a última)? `1`?

**A-3 · e74: a RBF `s3` é treinada POR PONTO — quantos blocos por ciclo?** *(bloqueia o e74)*
A DI-12.3 decidiu "medir as três RBFs", mas a s3 (`Local_infill.m:31`) é re-treinada **para cada
ponto** do ciclo. "Medir a s3" pode significar 1 bloco/ciclo (qual instância? a primeira? a última?)
ou N blocos/ciclo (inviável em volume). **Precisa de regra explícita.**

**A-4 · Pisos: o invariante `piso_com_surrogate` conflita com o cartão.** *(bloqueia os pisos)*
`experiment.m:2091-2095` asserta que os pisos têm `buf.srows` **e** `buf.trows` **vazios**. Mas o
cartão exige para os pisos "④/manifesto timing" — ou seja, `trows` **não vazio**. O assert precisa
ser relaxado para "sem `srows`" (sem sonda/modelo, correto) mantendo `trows`. Confirmar que é isso
que se quer, já que mexe num invariante existente.

### B. Ratificações (já estão valendo em código; vetáveis)

**B-1 · 🔴 `n_acumulado` do c217 — corrigi uma divergência de spec.**
O §17.6 define *"nº de pontos reais no **treino** naquele retreino"*; o código gravava `numel(Arc)`
(o **arquivo**). Corrigi para `size(TrainIn,1)` (o c217 treina numa subamostra 3/4 estratificada).
**Não toca a busca nem a ①** (gate verde), mas **muda a ④ do c217 vs a baseline**.
*Se o autor preferir preservar a continuidade histórica da ④, reverto e documento a divergência.*

**B-2 · `fe_treino_max` = máximo sobre o TREINO real (não sobre o arquivo).**
Literal do §17.2 (*"no TREINO do modelo"*). Consequência que merece ciência explícita: em
**b4, c217 e b1** o treino é subamostrado/capeado ⇒ o valor **não é monotônico** entre gerações e
**não coincide** com `bud.fe-1`. Isso é o que o filtro in-sample × out-of-sample da R4 (§9) precisa,
mas muda como a R4 deve ler a coluna nesses 3 configs.

**B-3 · `real_solution_id` da ③ cai para `double+NaN` quando há sonda.**
O MATLAB não expressa `int32`-NULL, e a sonda tem `real_solution_id=NULL` por contrato ⇒ a coluna
inteira degrada de dtype. A consolidação Python re-casta, então é inócuo — **mas quebra a nota
"c217 → int32 SEMPRE" do `handoff/R1-c217.md:82-85`**, que precisa de doc-sync.

**B-4 · Contiguidade do bloco de sonda.** Implementei sempre contíguo (1 disparo = 2000 linhas
seguidas). O §3.1 garante o join por posição *dentro* do bloco, mas não diz se o bloco pode ser
partido. Cravar como invariante (e assertar no accept) ou deixar o consumidor filtrar por `regime`?

**B-5 · `accept.py` não tem NENHUMA checagem de sonda** — nem a invariante de ordem que o §3.1
promete estar *"documentada no accept"*. Faixa `.py` ⇒ repasse à torre/R3-00. Sugestão de escopo:
contagem `S × blocos`, contiguidade, ordem vs artefato, `fe_treino_max ≤ fe`, presença de
`man.sonda`, `n_blocos` == eventos `sonda` do jsonl.

### C. Doc-syncs na SPEC/CONTRATO (torre — RI-12)
Já registrados na *Agenda de execução pendente* do registro (item 5). **Três dos quatro existem
porque o texto normativo admitia duas leituras — foi exatamente isso que produziu a divergência de
cadência entre os stacks.** Cravar a redação é o que impede a reincidência no R3 e na M8:
1. **§17.2.2 + CONTRATO §3.1** — cravar a **fórmula** `g = 1,2,4,6,…` (não só a prosa).
2. **§17.6 + CONTRATO §4** — `tempo_geracao_s` **DESCONTA a sonda**.
3. **CONTRATO §6.1** — o critério de "patch invasivo" da DI-12.1.
4. **CONTRATO §3.2** — e74 mede as **três** RBFs.

---

## 6. Notas de fidelidade (para o julgamento manual do autor, D97)

- **Nenhuma decisão de busca foi alterada em nenhum config.** Os patches nos arquivos stock são:
  1 linha de chamada da sonda + `tic`/`toc` + 1 snapshot de variável já existente. Provado pelo gate
  bit-a-bit em 18 runs.
- **c141 — o pareamento `(RModel{j}, mS)` foi REPLICADO, não "corrigido".** `mS` é reatribuído no
  laço `MMRAEA.m:40` e só o do `i=M` sobrevive; o código oficial usa esse único `mS` como Xtr de
  **todos** os `RModel{j}`. Sondar com outro pareamento mediria um modelo que o algoritmo não usa.
- **c217 — `n_best`/`n_worst` saem de `Output`, não de `TrainOut`.** O `TrainOut` é descartado em
  `PCSAEA.m:40`; a contagem é determinística a partir de `Output` ⇒ substituto **exato** sem tocar
  no miolo stock.
- **c141 — `dist_min_arquivo` sem `pdist2`**: o config é zero-toolbox confirmado; usar Statistics
  Toolbox criaria uma dependência que ele não tem.
- **e7 — `loss_treino` fica NULL por decisão do autor** (DI-12.1): está no laço de 8e4 iterações do
  run mais caro da R1.

---

## 7. Como continuar (7 configs + pisos)

Receita mecânica, provada em dois configs de naturezas opostas — em
`handoff/DI09-retrofit-R1.md` §4. Resumo:
1. `src/<alg>_sonda.m` novo (monta o `predict_fn`, chama `snd.probe`).
2. **1 linha** no arquivo stock, **pós-fit, pré-decisão, pré-`Evaluation`** (essa ordem é o que
   garante que o hard-stop não engula o bloco) + `tic`/`toc` de geração e busca + snapshot do
   arquivo pré-infill.
3. 4 pontos no `run_<alg>`: `t0_run` · `load_sonda`+`SondaState` no `data` (⚠ `UserProblem.data` é
   `SetAccess=protected` — **não há como injetar depois**) · `finalProbe` antes do export ·
   `fill_manifest_timing` antes do `write_manifest`.
4. Campos DI-10 no `<alg>_instrument.m` + `fe_treino_max` nas linhas de busca.
5. Validar: não-perturbação → auditoria → `accept.py`.

**Ordem restante:** b1 → b4 → e7 → b3 → e103 → e74 → c238 → pisos.
**Definições a resolver antes:** e103 (A-1, A-2) · e74 (A-3) · pisos (A-4).

**Atenção por config:**
- **e7** — único preditor de fato **estocástico** (MC-dropout, ~1,4e7 draws/bloco). É onde o
  invariante de RNG deixa de ser cinto-e-suspensórios. Wall base já é o maior da R1 (321 s em MMF1).
- **e74** — até 4 blocos/ciclo (PNN + 3 RBFs). **Medir volume antes do ZDT1.**
- **b3** — `apd_sel` liberado (DI-12.1): +1 output em `KrigingSelect.m` (já patchado pela L.2).
- **e103** — `margem_3sigma` liberado, mas **invalida o `repos.lock`** ⇒ re-lacre por
  `preflight.py --write` + reverificação das 3 âncoras.
- **b1** — único que **não precisa tocar o miolo stock**: o probe cabe no próprio `b1_instrument`.

⚠ **Serialidade:** não rodar MATLAB enquanto se edita `experiment.m` (RI-07 — arquivo compartilhado).
⚠ **Coexistência:** durante esta sessão a árvore recebeu commits `[DI09-R2]` e ficou com arquivos
`.py` não commitados da sessão R3-00. O ritual anti-mistura isolou minha faixa em todos os 7 commits.
