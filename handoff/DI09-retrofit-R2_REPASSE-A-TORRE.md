# DI09-retrofit-R2 — REPASSE À TORRE

> **Para:** a instância que emitiu as instruções do cartão.
> **De:** a sessão executora (faixa Python R2), 2026-07-19.
> **O que é:** o relato completo do processo — o que foi feito, em que ordem,
> que código rodou, que resultado deu, o que foi encontrado no caminho, e
> **o que exige decisão do autor**.
>
> 🔴 **AÇÃO REQUERIDA DA TORRE:** a §8 lista **13 definições em aberto**, sendo
> **3 bloqueadores** e **4 decisões de contrato de dados** que eu tomei para não
> travar o cartão e que precisam de ratificação. A torre deve **levantá-las com
> o autor**. Nenhuma é decisão de fidelidade (D97).
>
> ⚡ **A mais urgente é a §8.1/B-0:** a sessão retrofit-MATLAB implementou a
> sonda com uma **cadência diferente** da minha. Quanto mais runs forem gravados
> antes de padronizar, maior o retrabalho.

---

## 1. Resposta direta: a etapa está pronta?

**SIM — obrigatório E opcional, tudo executado e validado.** O run opcional
`c262/DTLZ2` terminou depois da primeira versão deste relatório e também passou
no gate (§7). Não há nada pendente de execução.

| | |
|---|---|
| Escopo obrigatório | ✅ completo, gates verdes |
| `c262/DTLZ2` (o cartão marcou **OPCIONAL**) | ✅ **concluído — gate VERDE** (ver §7) |
| Escopo explicitamente proibido pelo cartão | não tocado (§9) |

O único run que o cartão proibiu re-executar (`c154/DTLZ2`, 14h37) recebeu
backfill da ④, como determinado.

## 2. O código que rodei e o resultado — evidência, não memória

Tudo abaixo foi re-executado no fechamento, com `PY` = env-main
(`/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`),
botorch 0.18.1 OFICIAL.

### 2.1 🔴 O gate central — NÃO-PERTURBAÇÃO

```bash
$PY -c "from src import experiment; experiment.run('c262','MMF1',0, exp='main')"
$PY -c "from src import experiment; experiment.run('c154','MMF1',0, exp='main')"
# depois: sha256 da ① re-executada vs a de data/experiments/_baseline_pre_retrofit/
```
```
c262/MMF1   baseline=61L /c37afd6d4f551d66      pos-retrofit=61L /c37afd6d4f551d66      -> VERDE
c154/MMF1   baseline=61L /95be196c1855bd70      pos-retrofit=61L /95be196c1855bd70      -> VERDE
c262/DTLZ2  baseline=371L/e43c52033eff0b9d29a2  pos-retrofit=371L/e43c52033eff0b9d29a2  -> VERDE
```
O DTLZ2 (D=12, M=3, **241 iterações, 122 blocos de sonda**) é a prova mais forte
das três: 6× mais iterações que o MMF1 e um espaço muito maior.
**A ① é bit-idêntica com a sonda ativa.** É a prova objetiva que o invariante
DI-09 exige.

### 2.2 Suíte de testes

```bash
$PY -m unittest discover -s tests
# Ran 122 tests in 2.474s / OK (skipped=1)
```
122 testes (eram 92 antes do cartão; **+30 novos**, em `tests/test_di09_r2.py`).
O 1 skip é o teste que exige stack ausente em interpretador base — comportamento
projetado, igual aos demais testes da R2.

### 2.3 Gates `accept.py` e preflight

```
R2-c262/MMF1     VERDE      F0-01-harness   VERDE
R2-c262/DTLZ2    VERDE      F0-02-doe       VERDE
R2-c154/MMF1     VERDE      F0-03-export    VERDE
R2-c154/DTLZ2    VERDE      F0-04-metrica   VERDE (FECHA a Fase 0)
                            R2-00-harness   VERDE
                            preflight       pré-voo OK ✓ (1 deferimento intencional)
```
Cada gate R2 afere: 4 saídas + jsonl presentes · FE = 31D−1 exato (61 e 371) ·
CP-init do DoE bit-a-bit.

**Gates R1 NÃO rodados** — a faixa MATLAB está ativa (instrução do cartão).

### 2.4 Auditoria pyarrow dos artefatos

```
── c262/MMF1 e c154/MMF1 (idênticos nos dois) ──
③ 44.410 linhas | busca 410 · sonda 44.000
③ blocos: 22, gerações {1,2,4,…,40,41} — confere com 1ª + k=2 + última
   todas com exatamente 2000 linhas: True
   ordem do artefato bit-exata (vs sonda_MMF1.parquet): True
   fe_treino_max: 0 NULL em 44.410 · real_solution_id na sonda: 44.000/44.000 NULL
④ 41 linhas | NULLs: busca=0 sonda=0 geracao=0
⑤ timing 4 chaves + tempo_pred_sonda_s · sigma_dict 10 chaves · sonda 22×2000
⑥ header 1 · timing 41 · decision 41 · sonda 22 · footer 1
⑥ DI-10 mínimo comum completo · c262 n_baseline=7 (pós-prune, vs n_train=21)
   c154 n_train=21 · mll_final −0,8214 / −0,6794 · |acqf_todos_restarts|=10
```

### 2.5 Probe de risco isolado (antes de gastar o gate caro)

O `mll_final` era o único ponto com risco real de perturbar a numérica (exige um
forward do MLL sobre o modelo ajustado). Rodei um probe dedicado comparando o
`optimize_acqf` seguinte com e sem a extração:
```
candidatos bit-a-bit identicos: True
acqf vals bit-a-bit identicos : True
max |delta cands|: 0.0   max |delta acqf|: 0.0
```
Virou teste unitário (`test_extrair_o_mll_nao_desloca_o_rng_nem_o_modo_do_modulo`).

### 2.6 Backfill da ④ do c154/DTLZ2

```
241 linhas · tempo_busca_s: 0 NULL (240 EXATAS + 1 DERIVADA) · 0 anômalas
241/241 conferidas contra a ④ do disco antes de escrever
```
**Duas validações cruzadas independentes** (caminhos que não se conversam):
Σ`tempo_busca_s` = **51.674,4 s** vs manifesto **51.674,4185 s**;
Σ`tempo_geracao_s` ≈ `tempo_total_s` a menos do setup/teardown fora do laço.
**Calibração do estimador derivado:** nas 240 iterações de valor conhecido,
`ts(decision) − ts(timing)` errou **+8 ms em ~450 s** (2×10⁻⁵ relativo).

## 3. O processo, etapa por etapa

**PASSO 0 — contexto.** Li `CONTRATO_DE_DADOS.md` inteiro; extraí verbatim
SPEC §17.2.2 / §S.7.1 / §17.6 / §17.4; REGISTRO DI-09/DI-10/DI-11 + DEFS-c154
§D-4; os 2 handoffs R2; CLAUDE.md. Li os 4 fontes da faixa por completo.

**Três achados do PASSO 0 mudaram o desenho** (não estavam nas instruções):
1. `buf.add_timing(...)` é chamado **logo após o fit**, antes da busca — as
   colunas novas exigiram um `update_timing` (patch da linha da geração),
   inclusive no ramo `BudgetExhausted`.
2. `write_surrogate` aplicava **um `regime` para o arquivo inteiro** — a sonda
   exigiu `regime` **por linha**.
3. c154/DTLZ2: o jsonl tem `t_busca_s` em **240** decisões, não 241 — a última é
   o `hard_stop`, que fecha antes de o wall da busca ser logado. O cartão
   esperava 241 não-NULL, então calibrei um estimador para essa 1 linha.

**PASSO 1 — plano** (≤15 linhas, entregue antes de codar).

**PASSO 2 — implementação**, 11 commits com o ritual anti-mistura (`add`
explícito + staged-check + commit num comando; nunca `git add -A`):

| commit | conteúdo |
|---|---|
| `b087b6a` | export: colunas aditivas + `manifest_timing_block` + backfill |
| `234c6b6` | harness: helper da sonda + guarda de RNG + buffer |
| `acbf720` | harness: mínimo comum DI-10 (**+ correção do bug `n_front1`**) |
| `e81b76e` | c262: sonda + DI-10 + sigma_dict + DI-11.3 |
| `055a893` | c154: idem, com as especificidades do JES |
| `8ed4555` | testes do cartão (26 casos) |
| `05ccc97` | handoff + relatório + definições em aberto |
| `bb17129` | **fix** do backfill (revisão adversarial) |
| `72d67fc` | +4 testes de regressão |
| `3aa0d25` | docs da revisão + escalação dos 2 achados fora da faixa |
| `4a2c9d2` | sincronização de números no handoff |

**PASSO 3 — validação**: §2 deste documento.

**PASSO 4 (não pedido, feito por conta do risco)** — revisão adversarial do
diff: 5 lentes independentes → verificação cética de cada achado (viés default
REFUTAR). **35 levantados, 12 confirmados.** Ver §5.

## 4. O que passou a ser gravado (o contrato, na prática)

**③ `__surrogate`** — `fe_treino_max` (int32 nullable, DI-09/A1), cravado no
buffer após o fit e **herdado por toda linha**; `regime` **por linha**; e a
sonda: 2000 linhas/bloco, `regime='sonda'`, `real_solution_id=NULL`, **na ordem
do artefato** (o join com o gabarito é por posição — R4 regra 5).

**④ `__timing`** — `tempo_pred_sonda_s` e `tempo_geracao_s`; `tempo_busca_s`,
que era NULL em 100% das linhas nos 2 configs, passa a ser sempre preenchido.

**⑤ manifesto** — `timing` completo pelo helper único + bloco `sonda`
(S/k/hashes/nº de blocos) + **`sigma_dict`** (DEF-C4).

**⑥ jsonl** — mínimo comum DI-10 (`fe`, `f_best[]`, `n_front1`,
`dist_min_arquivo`, `tempo_fit_s`, `tempo_busca_s`, `modelo_hp` com θ min/med/max
+ outputscale + ruído + `mll_final`); `acqf_todos_restarts`; `n_baseline` (c262,
pós-prune) / `n_train` (c154, DI-11); evento `sonda` por bloco.

**Como a não-perturbação foi garantida:** `preserve_torch_rng`/`preserve_all_rng`
(torch+numpy+random) em volta de **toda** predição de sonda, do `modelo_hp` e do
mínimo comum DI-10; sonda emitida **depois** da busca e **antes** do `del model`;
`no_grad`, lotes de 512, sem tocar o `FEBudget` (ZERO FE).

**DI-11.3** (adendo B / lacuna D-8): `_WallClockProjector.exceeded()` ganhou um
teto de **tempo decorrido independente** da projeção pós-10-amostras, e passou a
devolver o **critério** (`'elapsed'`|`'projecao'`) que vai ao jsonl. Aborto segue
limpo. Validado em teste unitário, sem run real.

## 5. Dois bugs encontrados no caminho (transparência)

**(a) `n_front1` estava errado — pego pelo próprio teste que escrevi.**
`src/problems._nds_filter` devolve **ÍNDICES**, não máscara booleana; eu usei
`np.count_nonzero(...)`, que descarta silenciosamente o índice 0. O número
estaria errado por −1 na maioria das iterações e **nada acusaria até a análise
R4**. Corrigido (`len(...)`) e os 2 runs de gate re-executados.

**(b) O backfill trocava medida por derivação — achado pela revisão
adversarial, reproduzido empiricamente.** Rodar o backfill sobre um run
**pós-retrofit** inflava `tempo_geracao_s` em **+10,66%** e trocava
`tempo_pred_sonda_s` de `0.0` para NULL em 19/41 linhas — sem erro, e com o
relatório dizendo "41 linhas conferidas vs disco". Raiz: `write_timing`
reescreve o arquivo INTEIRO, mas a guarda só conferia
`geracao`/`n_acumulado`/`tempo_fit_s` — que **batem por construção** (vêm do
mesmo `add_timing`). Somaram-se duas causas: a definição do backfill **incluía**
a sonda (o escritor vivo desconta) e a última geração ia até o `footer`, que os
runners só emitem **depois** de `write_run_outputs` (4 parquets + manifesto +
upload). Corrigido em `bb17129` com 4 mudanças + 4 testes de regressão; o
c154/DTLZ2 foi **re-backfillado** com a semântica correta.

## 6. Custo medido da instrumentação (insumo para o M7)

MMF1, 41 iterações, 22 blocos = 44.000 predições de sonda:

| | c262 | c154 |
|---|---|---|
| `tempo_total_s` | 34,73 s | 95,76 s |
| `tempo_busca_s` | 28,09 s (80,9%) | 84,71 s (88,5%) |
| **`tempo_pred_sonda_s`** | **1,16 s (3,3%)** | **1,43 s (1,5%)** |
| ③ em disco | 15 KB → **1,4 MB** | 16 KB → 1,4 MB |

**Leitura:** a sonda custa **1,5–3,3% do wall** e o custo é praticamente igual
nos 2 configs — é função do modelo (GP sobre 2000 pontos), não do algoritmo.
Como a busca domina (81–89%), **a sonda não muda a ordem de grandeza de nenhum
run**. O que ela move é **volume em disco**: a ③ cresce ~90× no MMF1. Confirma
por medição a aritmética dos ~260 GB que o autor já cravou na DI-09.

## 7. O run opcional (`c262/DTLZ2`) — CONCLUÍDO, VERDE

Rodado em escala real (D=12, M=3, 241 iterações; wall **8.972 s = 2h29**, contra
~2h31 do baseline pré-retrofit — ou seja, **a sonda não é distinguível do ruído
no wall total**).

```
🔴 NAO-PERTURBACAO: ① 371 linhas, sha e43c52033eff0b9d29a2 == baseline  -> VERDE
③ 246.410 linhas | busca 2.410 · sonda 244.000
   blocos: 122 (esperado 122) · gerações {1,2,4,…,240,241} conferem: True
   todas com 2000 linhas: True · ordem do artefato bit-exata: True
   fe_treino_max: 0 NULL
④ 241 linhas | NULLs: busca=0 sonda=0 geracao=0
⑤ sonda 122×2000 = 244.000 · sigma_dict 10 chaves · timing 5 chaves
⑥ header 1 · timing 241 · decision 241 · sonda 122 · footer 1
```

**Custo medido em escala (corrige a projeção da §6):**

| | medido |
|---|---|
| `tempo_pred_sonda_s` | **16,29 s de 8.972 s = 0,18 %** |
| `tempo_busca_s` | 8.838 s (98,5 %) |
| ③ em disco | 0,22 MB → **9,1 MB (41×)** |

> ⚠ Correção honesta: eu havia projetado ~7 s (0,08 %) para a sonda aqui; o
> medido foi **16,3 s (0,18 %)** — a projeção linear a partir do MMF1 subestimou
> por ~2×, porque o custo do posterior cresce com `n_train` (que vai a 371 no
> DTLZ2 contra 61 no MMF1). **A conclusão não muda:** a sonda continua sendo
> ruído no wall (a busca é 98,5 %) e o que ela move é disco.

**Extrapolação de volume para a M8:** 9,1 MB/run neste porte. A bateria tem
16.500 runs, com D variando até 30 (ZDT1) — o que sustenta, por medição, a ordem
de grandeza dos **~260 GB extras** que o autor já cravou na DI-09.

---

# 8. 🔴 DEFINIÇÕES EM ABERTO — A TORRE DEVE LEVANTAR COM O AUTOR

*(Documento completo: `handoff/DI09-retrofit-R2_DEFINICOES-EM-ABERTO.md`.
Abaixo o resumo executivo, por prioridade.)*

## 8.1 BLOQUEADORES (não são decisão minha; precisam de cartão)

### ⚡🔴 B-0 · CADÊNCIA DA SONDA DIVERGE entre Python e MATLAB — decidir JÁ
Achado no fechamento, ao conferir faixa. A sessão **retrofit-MATLAB** commitou
em paralelo (`cc3eee1`) e implementou a mesma sonda com outra cadência:

| | fórmula | gerações com bloco |
|---|---|---|
| **MATLAB** (`SondaState.due`) | `g==1 \|\| mod(g-1,k)==0` | **1, 3, 5, 7, …** |
| **Python** (`sonda_due`) | `it==1 or it%k==0` | **1, 2, 4, 6, …** |

Ambas são leituras defensáveis de *"a cada k=2 + SEMPRE a 1ª e a última"*.
**Argumento textual a favor da Python:** sob a fórmula MATLAB a cláusula
"+ SEMPRE a 1ª" fica **vazia** (1 já está em 1,3,5,…); a SPEC tê-la escrito
sugere que a cadência não inclui a 1ª naturalmente. Não é conclusivo, e **não é
decisão minha**.

**Impacto, sem alarmismo:** *não* quebra o contrato de análise (o eixo de
comparação é o **FE**, não a geração — CONTRATO §3.1 / R4 regra 6). **Mas** a
sonda é vendida como *"a régua ÚNICA, idêntica para todos"*, e uma diferença
arbitrária **por stack** contradiz isso; muda a contagem de blocos (logo, o
volume) e desalinha leituras indexadas por geração.
**Custo de padronizar: 1 linha de cada lado — e cai a cada run gravado.**

### ⚠ B-0b · `tempo_geracao_s`: o MATLAB desconta a sonda?
Ligada a B-0 e à minha decisão **D-1**. Implementei descontando. No MATLAB,
`c217_instrument.m` grava `tempo_geracao_s` e `tempo_pred_sonda_s` lado a lado e
**não vi a subtração** — mas a sessão seguia ATIVA e o código em fluxo, então
**não afirmo que esteja errado**; registro para a torre conferir. Se um lado
descontar e o outro não, a mesma coluna significa duas coisas entre stacks.

### 🔴🔴 B-1 · `experiments.py` APAGA o manifesto do retrofit — bloqueador da M8
`experiments.py::_run_one` chama `new_manifest`+`write_manifest`
**incondicionalmente depois do runner**, com um `timing` stub
(3 das 4 chaves em `None`). Isso **sobrescreve** o manifesto que o runner
gravou: somem **`sigma_dict`** (leitura OBRIGATÓRIA antes de usar a ③), o bloco
**`sonda`**, `doe_hash` (CP-init D87/D88), `fe_final`, `maxfe`, `n_geracoes`,
`algo_version`, `env`, `fit_series`, `acqf_ref_f`, `fused_kernel`.

Pendência já conhecida (DI-06), **mas o retrofit multiplicou a consequência**:
se a bateria M8 for despachada por ali, os 16.500 runs perdem todo o payload
DI-09/DI-10 da camada ⑤ — e o `timing` obrigatório volta a nascer zerado,
desfazendo o retrofit **sem sintoma visível**.
*Os runs desta sessão estão íntegros* (despachei por `src.experiment.run`
direto; verificado). **Fora da minha faixa** (dispatcher = R3-00).
**Recomendação:** o dispatcher deve **mesclar** (ler o manifesto do disco e só
atualizar `status`/`n_retries`/`stack_trace`), nunca reconstruir do zero.

### 🔴 B-2 · Aborto por teto × artefatos de execução anterior
No aborto por teto o `write_run_outputs` não roda (por desenho) e **nenhum
manifesto `failed` é gravado**. Se houver artefatos de uma execução ANTERIOR do
mesmo `run_id`, sobrevivem: manifesto `status:"ok"` + 4 parquets antigos ao lado
de um jsonl novo dizendo `failed` — e o `is_run_done` (D58) leria o run como
pronto. Pré-existente. **Não mexi** porque gravar um manifesto `failed` no
caminho de aborto muda a semântica de resume/`run_done` — decisão de infra
(DI-06/M7), não deste cartão.

## 8.2 DECISÕES DE CONTRATO QUE EU TOMEI — PRECISAM DE RATIFICAÇÃO

### D-1 · `tempo_geracao_s` **EXCLUI** o custo da sonda
Implementado: o wall da geração na ④ desconta a sonda; o custo dela vai à parte.
**O projetor de teto, ao contrário, vê o wall CHEIO.**
**Por quê:** são duas perguntas diferentes. A ④ alimenta a curva de
escalabilidade e a comparação de custo entre famílias (§17.6) — incluir a
instrumentação deste estudo contaminaria a medida do *mecanismo*, e **de forma
desigual**, porque a sonda só roda a cada 2 iterações. Já o teto é o relógio de
parede do operador, que paga a sonda também.
**Se ratificada:** o CONTRATO §4 merece uma frase explícita (hoje diz só
"fit+busca+aval+overhead", que não resolve o caso). **Custo de mudar:** 1 linha
por runner.

### D-2 · `acqf_restarts` → **`acqf_todos_restarts`** (renomeado)
Adotei o nome NORMATIVO da SPEC §S.7.1. Runs pré-retrofit (c154/DTLZ2,
c262/ZDT1, c154/ZDT1) têm a mesma grandeza sob o nome antigo; a divergência está
no `sigma_dict`. O repasse do c154 (§7) pediu explicitamente que a torre
confirmasse este rename. Emitir os dois nomes duplicaria ~340 KB no jsonl do
DTLZ2. **Opções:** (a) ratificar [implementado]; (b) reverter; (c) emitir os dois
numa janela de transição. **A análise R4 vai ter de tolerar os 2 nomes de
qualquer forma**, porque os runs pré-retrofit não serão re-executados.

### D-3 · `tempo_pred_sonda_s` = **NULL** (não 0) em run pré-sonda
O CONTRATO §4 diz "0 quando não roda", mas isso descreve uma iteração de um run
**com** sonda. Num run pré-retrofit não havia grandeza a medir — gravar 0
afirmaria "a sonda rodou e custou zero", que é falso. Implementei: NULL só
quando o jsonl inteiro não tem evento `sonda`; num run com sonda, iteração sem
bloco vale 0.0.

### D-4 · Dado **derivado-e-rotulado** na ④ do backfill
A ④ do c154/DTLZ2 tem 1 linha de `tempo_busca_s` e 241 de `tempo_geracao_s`
derivadas, com a procedência gravada no manifesto (`timing_backfill`).
A alternativa era NULL, e o cartão pede as 241 preenchidas.
**Decisão:** aceitar derivado-e-rotulado, ou exigir NULL onde não houve medição
direta? **Se a torre preferir NULL**, é re-executável em segundos.

## 8.3 ITENS MENORES / DE ESCOPO

- **M-1 · c262/ZDT1 e c154/ZDT1 seguem sem as colunas novas** (o cartão disse
  "ZDT1: nenhum"). Nota: o jsonl do c262 **nunca logou a busca por iteração**, então
  ali o backfill só recuperaria por derivação de `ts` (diferente do c154, que tem
  valor exato). **Recomendo rodar o backfill derivado no c262/ZDT1** se o custo
  do ZDT1 entrar na análise R4 — é 1 comando, tudo rotulado. c154/ZDT1 abortou
  pelo teto e só tem jsonl (por desenho).
- **M-2 · Risco de leitura `n_baseline` × `n_train`** (a decisão em si já é da
  DI-11). **Não são a mesma grandeza:** medido, `n_baseline`=7 contra
  `n_train`=21 na 1ª iteração do MMF1 — a poda corta ~2/3. Uma análise que ponha
  as duas colunas lado a lado como "tamanho do baseline" concluirá que o JES tem
  3× mais dados. O `sigma_dict` avisa; um teste trava o aviso contra refactor.
- **M-3 · `sigma_dict` nos outros 19 configs.** Implementei nos 2 da minha
  faixa. O repasse do c154 nota que vale para os 21 — é retrofit-R1 / R3.
- **M-4 · Sonda/`fe_treino_max`/DI-10 nos 9 configs MATLAB e nos do R3.** Fora
  da faixa por construção (paralelismo triplo).
- **M-5 · Re-executar um backfill exige restaurar a ④ antes** (custo deliberado
  da guarda de escopo criada em `bb17129`). Procedimento documentado.
  **Alternativa que NÃO cravei sozinho:** marcar a procedência dentro da ④ (uma
  coluna `origem` ∈ {medido, backfill}) em vez de inferi-la pela presença de
  `tempo_geracao_s` — mais explícito, mas é +1 coluna no contrato.
- **M-6 · Armadilha de manutenção:** `_nds_filter` devolve ÍNDICES, não máscara.
  Quem instrumentar `n_front1` nos demais configs: use `len(...)`. Já custou um
  bug nesta sessão.

## 9. Faixa e higiene (prestação de contas)

**Tocados:** `src/export.py`, `src/botorch_harness.py`, `src/c262_qnehvi.py`,
`src/c154_jes.py`, `tests/test_di09_r2.py`, `handoff/DI09-retrofit-R2*.md`.

**NÃO tocados** (proibidos pelo cartão): qualquer `*.m` · `algorithms/**` ·
`experiment.py` · `accept.py` · `naming.py` · standalone · `gen_sonda.py` ·
`data/sonda/**` (só CARREGADO, com hash conferido) ·
`data/experiments/_baseline_pre_retrofit/**` · INDEX/SPEC/docs-torre.
`manifest.py`/`budget.py`/`audit_log.py`/`gcs.py` **não** foram editados — o
`sigma_dict` e os blocos novos entram pelo runner, no mesmo padrão que o c262 já
usava para `acqf_ref_f`/`fused_kernel` (nenhum gancho novo ⇒ nenhum D81).

**Commits:** 11, todos com o ritual anti-mistura. Árvore limpa (0 arquivos
não-commitados). Branch `experiment/definitive_algorythms`.
