# DI09-retrofit-R1 — instrumentação de assertividade dos surrogates (SPEC v5.2.1)

> **Cartão:** retrofit DI-09 (sonda canônica) + DI-10 (enriquecimento do `.jsonl`) nos 9 configs
> SA-MATLAB + o pacote leve dos 4 pisos. Instrumentação **read-only**; o gate central é provar que
> **nada da busca mudou**.
> **Estado:** infra transversal **COMPLETA e verificada** · **2 de 9 configs** entregues (c217, c141).
> **Ambiente (D81, conferido ANTES):** MATLAB R2025a Update 1 · ponte `pyenv` → `~/ponte_teste/bin/python`,
> `py.numpy.array([1,2,3]).sum()` = **6** ✓ · venv `mestrado_experimentos_dissertacao` py3.11.9, pyarrow 25.0.0.

---

## 1. Decisões do autor cravadas nesta sessão (2026-07-19)

Quatro ambiguidades reais foram levadas ao autor (protocolo D81) e decididas:

| # | Questão | Decisão |
|---|---|---|
| **1** | Acrescentar um valor de retorno a função stock, para expor número que ela **já** calculou, conta como "patch invasivo" (§6.1)? | **Liberar b3 (`apd_sel`) e e103 (`margem_3sigma`); barrar e7 (`loss_treino`)** — este último fica dentro do laço de treino de 8e4 iterações do run mais caro da R1. `loss_treino` → registrar como INACESSÍVEL no handoff do e7. |
| **2** | Como garantir a sonda na **última** geração, se o orçamento estoura no meio do ciclo e a exceção salta para fora do laço? | **Carrier handle + bloco pós-`Solve`.** Implementado no `SondaState` (`arm`/`finalProbe`). |
| **3** | e74: qual das **três** RBFs é a cabeça-valor, e os blocos PNN/RBF levam o mesmo `geracao`? | **Medir as três** (boot, s2/`Hv_Select`, s3/`Local_infill`), discriminadas por `modelo_flag`. |
| **4** | Instrumentar `FEBudget.evaluate` para preencher `tempo_aval_real_s`? | **Sim.** Cronômetro acumulador no portão único das avaliações reais. |

### Resoluções que tomei com o contrato na mão (vetáveis)

- **`fe_treino_max` = máximo sobre o conjunto de TREINO real**, literal do §17.2 ("no TREINO do modelo").
  Em b4/c217/b1, que subamostram, o valor **não é monotônico** — e é essa a semântica que o filtro
  in-sample × out-of-sample da R4 (§9) precisa. Preenchido **também nas linhas de busca**, não só na sonda.
- **e103** carimba a sonda e a derivação de `n_geracoes` **filtra `regime=='sonda'`**, preservando o
  manifesto idêntico à baseline. *(a executar no cartão do e103)*
- **Sem bloco extra para os fits de bootstrap** (e7 `:47`, e74 `:60`): a cadência do §3.1 é por geração.
- **`accept.py` é `.py`** — checagem de sonda no gate fica como **repasse à torre/R3-00** (§6 abaixo).

---

## 2. Infra transversal (commit `cc3eee1`) — COMPLETA

| Onde | O quê |
|---|---|
| `src/experiment.m::load_sonda` | Carrega `data/sonda/sonda_{p}.parquet` + sidecar e **confere o `x_hash`** (sha256 float64 row-major) no arranque, abortando em divergência — disciplina D63/D87. Nenhum algoritmo gera pontos. + `nm_sonda_path`/`nm_sonda_manifest_path`. |
| `src/SondaState.m` **(novo)** | O motor da sonda. Ver §3. |
| `src/experiment.m::write_surrogate` | `regime` **por linha** (o argumento vira default — espelha `export.py:328`) + coluna **`fe_treino_max`**, com o branch int32/double-NaN do `real_solution_id`. |
| `src/experiment.m::write_timing` | **`tempo_pred_sonda_s`** + **`tempo_geracao_s`**; toda leitura de trow por `field_or` (o acesso direto derrubava o export com qualquer linha nova); `n_acumulado` cai para double+NaN em linha sem retreino, em vez de `int32(NaN)=0`, que se leria como "treinou com 0 pontos". |
| `src/experiment.m::fill_manifest_timing` **(novo)** | Preenche o bloco `timing` **obrigatório** (§17.6 — nascia zerado; só o e103 o preenchia) + `fit_series` + bloco `man.sonda`. |
| `src/FEBudget.m` | Cronômetro acumulador `tempo_aval_real_s` em volta do `evalFcn` — só avaliação inédita; cache-hit (D89) não avalia e não entra. |
| `src/RunBuffer.m` | Parâmetros `regime`/`fe_treino_max`; defaults dos campos novos de timing; **`mkSurrogateRows`** (lote) — ver §5. |

**Autoteste:** o config `stub` exercita o caminho inteiro (artefato → CP do hash → SondaState → ③
`regime='sonda'` → ④ → `man.sonda`) **sem algoritmo real**, para que uma regressão da infra apareça
ali e não no primeiro config. Inclui prova de RNG (estado **e** sequência de sorteios) e os dois
casos do `finalProbe` (no-op na geração já sondada; disparo na inédita).

---

## 3. `SondaState` — os invariantes garantidos pela CLASSE

Os invariantes não dependem da disciplina de cada config; são estruturais:

- **I1 — RNG intocado.** `rng()` salvo e restaurado por `onCleanup` em torno de **toda** predição
  (o MC-dropout do e7 consome ~1,4e7 draws por bloco).
- **I2 — zero FE.** **A classe não recebe o `FEBudget`** — não tem como gastar orçamento.
- **I3 — ordem do artefato.** 1 disparo = exatamente **S=2000** linhas contíguas, na ordem do parquet
  (o join com o gabarito é **por posição**). Sem sort/unique/clamp.
- **I4 — `regime='sonda'` + `real_solution_id=NULL` + `fe_treino_max`** carimbados pela classe.
- **I5 — nunca derruba a busca.** `try/catch` com evento de guarda, **re-lançando `PlatEMO:Termination`**.
- **I6 — cronômetro próprio**, fora dos `tic/toc` de fit e de busca.

**Cadência:** `probe(g, fn, ftm, ...)` **arma sempre** e dispara em `g = 1, 3, 5, …` (k=2, a 1ª incluída).
A **última** vem do `finalProbe(buf.gen)` chamado pelo `run_*` **depois** do `Algorithm.Solve`.

---

## 4. A receita por config (mecânica — usar nos 7 restantes)

1. **`src/<alg>_sonda.m`** (novo): recebe o modelo treinado + o que a semântica do §3.2 exige;
   monta o `predict_fn` e chama `snd.probe(g, fn, ftm, 'modelo', "<flag>")`.
2. **1 linha no arquivo stock**, logo após o fit e **antes da 1ª decisão / do 1º consumo de RNG** —
   e crucialmente **antes da `Evaluation`**, onde o hard-stop aborta o corpo do ciclo.
   Mais: `tic` no topo do corpo (tempo_geracao_s), `tic/toc` em volta da busca (tempo_busca_s),
   snapshot do arquivo **pré-infill** (dist_min_arquivo).
3. **`run_<alg>` em `experiment.m`**: `t0_run = tic` · `load_sonda` + `SondaState` dentro do `data`
   (⚠ `UserProblem.data` é `SetAccess=protected` — **não há como injetar depois**) ·
   `snd.finalProbe(buf.gen)` antes do export · `fill_manifest_timing(...)` antes do `write_manifest`.
4. **`<alg>_instrument.m`**: `fe_treino_max` nas linhas de busca · campos DI-10 do §S.7.1 ·
   `tempo_busca_s`/`tempo_geracao_s`/`tempo_pred_sonda_s` (via `snd.takePendingTime()`).
5. **Validar** (ferramentas no scratchpad da sessão, não versionadas):
   `naoperturbacao.py <alg> <prob> 0` (bit-a-bit vs `_baseline_pre_retrofit`) ·
   `auditar.py <alg> <prob> 0` (contagens/ordem/colunas/manifesto/jsonl) ·
   `scripts/accept.py R1-<alg> --alg <alg> --problema <prob> --semente 0` → exit 0.

**⚠ Serialidade:** não rodar MATLAB enquanto se edita `experiment.m` (RI-07 — arquivo compartilhado).

---

## 5. Achados desta sessão

### 5.1 `mkSurrogateRow` custava 148 µs/linha (corrigido)
O `inputParser` sozinho custava **~87 s por run** no c217/ZDT1 (295 blocos × 2000). Mesmo precedente
do **DI-02** (o writer O(n²) que inviabilizava a bateria): o custo por linha decide se a M8 é viável.
Adicionado `RunBuffer.mkSurrogateRows` (lote, sem inputParser): **148 → 3,8 µs/linha (38×)**, com
**equivalência campo-a-campo provada** (0 divergências em 2000 linhas × 15 campos).
Wall c217/ZDT1: **188 → 105 s**.

### 5.2 A sonda cobre o grid, não os problemas de piloto
`DTLZ2_d15` (variante dimensional usada só em piloto) **não tem** artefato de sonda — e não pode ter
sem um artefato próprio, já que a sonda é Sobol com `d=D`. **Verificado: o grid oficial
(`runs_matrix.csv`) tem 25 problemas e todos os 25 têm sonda** — logo isto não afeta a bateria.
`load_sonda` passou a tolerar a ausência: o run segue **sem** sonda e o manifesto grava
`man.sonda.status='artefato_ausente'`, para que *"sem sonda"* nunca seja lido como *"sonda vazia"*.

### 5.3 🔴 `n_acumulado` do c217 estava errado — PENDENTE DE RATIFICAÇÃO
O §17.6 define `n_acumulado` = *"nº de pontos reais no **treino** naquele retreino"*. O
`c217_instrument` gravava `numel(Arc)` — o tamanho do **arquivo**, outra grandeza — o que achatava a
curva de escalabilidade do c217. Corrigido para `size(TrainIn,1)`; o tamanho do arquivo segue
auditável em `arc_size` na linha `c217_gen`.
**Não toca a busca nem a ①** (o gate passou), mas **muda a ④ do c217 vs a baseline** → o autor deve
ratificar.

---

## 6. Pendências e repasses

| Item | Para quem |
|---|---|
| **7 configs restantes**: b1, b4, e7, b3, e103, e74, c238 + o pacote leve dos 4 pisos | continuação deste cartão (receita no §4) |
| **`accept.py` não tem nenhuma checagem de sonda** (0 hits) — nem a invariante de ordem que o §3.1 promete estar "documentada no accept" | torre / R3-00 (faixa `.py`) |
| Ratificação do §5.3 (`n_acumulado` do c217) | autor |
| `loss_treino` do e7 = **INACESSÍVEL** por decisão do autor (§1, item 1) | registrar no cartão do e7 |
| Divergências colaterais esperadas e toleradas: `real_solution_id` da ③ cai para double+NaN quando há linhas de sonda (o MATLAB não expressa int32-NULL; a consolidação re-casta) — quebra a nota "c217 → int32 SEMPRE" do `handoff/R1-c217.md:82-85` | doc-sync |

---

## 7. Prova por config (o que foi verificado)

### c217 — PC-SAEA (commit `845743a`)
Sonda: score ternário vs `Pmid`, `pred_confianca=Error1`, `modelo_flag='PNN-par'`.
Ponto: `PCSAEA.m` entre `:50` e `:53`.
DI-10: `n_best`/`n_worst` (derivados de `Output` — o `TrainOut` é descartado em `:40`, mas a contagem
é determinística: **substituto exato sem tocar no miolo**), `|Pmid|`, `n_treino`, `n_pares_treino` +
mínimo comum completo.

| problema | ① não-perturbação | accept | blocos de sonda |
|---|---|---|---|
| MMF1 | **IDÊNTICA** 61×10 | exit 0 | 21 × 2000 |
| DTLZ2 | **IDÊNTICA** 371×21 | exit 0 | 116 × 2000 |
| DTLZ2_d15 | **IDÊNTICA** 464×24 | exit 0 | — (fora do grid, §5.2) |
| ZDT1 | **IDÊNTICA** 929×38 | exit 0 | 295 × 2000 |

### c141 — MMRAEA (commit `ff38f2b`)
Sonda: μ por objetivo, **σ NULL** (o RBF é interpolante — a distinção VAR-GP × ERR-EMP).
Ponto: `MMRAEA.m` após `:48`.
⚠ **Pareamento `(RModel{j}, mS)` replicado, não "corrigido"**: `mS` é reatribuído no laço `:40` e só o
do `i=M` sobrevive; o código oficial usa esse único `mS` como Xtr de **todos** os `RModel{j}`. Sondar
com outro pareamento mediria um modelo que o algoritmo não usa.
`dist_min_arquivo` **sem `pdist2`** — o c141 é zero-toolbox confirmado.
DI-10: `n_por_nivel` completo da cascata (o `idx_sel` já existia no struct `info`, só não era escrito)
+ hp do RBF + mínimo comum.

| problema | ① não-perturbação | accept | blocos de sonda |
|---|---|---|---|
| MMF1 | **IDÊNTICA** 61×10 | exit 0 | 6 × 2000 |
| DTLZ2 | **IDÊNTICA** 371×21 | exit 0 | 33 × 2000 |
| ZDT1 | **IDÊNTICA** 929×38 | exit 0 | 77 × 2000 |

**Suíte Python:** 122 testes OK (nenhum arquivo `.py` foi tocado).
