# BATERIA DE CONTRATO E SAÚDE — 15.128 células (medido em streaming, read-only)

**Nada foi executado do repo. Nenhum `experiments.py`/`experiment.run`/`experiments.m` foi invocado.** Tudo por leitura direta de disco (footers Parquet + streaming de JSONL) com o interpretador indicado. Artefatos da varredura em `/private/tmp/claude-501/-Users-gmello/33c29160-6eb6-4277-a041-db4855486063/scratchpad/` (`inventario.csv`, `merged.csv`, `l6_scan.csv`, `l6_footers.csv`, `foot_merged.csv`, `l5_scan.csv`, `col_stats.parquet`, `l1_scan.csv`, `celulas_mistas.csv`).

---

## 0. CORREÇÃO DE DENOMINADOR (antes de tudo)

O denominador correto do acervo canônico é **15.128**, não 15.129.

| | valor |
|---|---|
| células no `resultados_experimentos/` (dir alg/prob/seed) | **15.128** |
| linhas do `censo_completo_22.csv` | 15.129 |
| chaves (alg,prob,seed) em comum | 15.128 (conjuntos **idênticos**) |
| linha excedente | `e81 · batch · ZDT4 · 42` — **duplicata de chave** com a linha `e81·main·ZDT4·42` |

A célula `exp_batch_e81_ZDT4_42` existe **só no espelho** `~/mestrado_coleta_m8/matlab-vm3/experiments/batch/e81/` e é um **stub de 4 linhas** de 2026-07-29: `tempo_total_s=0.0003`, `fe_final=null`, `maxfe=null`, `regime=null`, `campanha_id` ausente, **zero camadas de dado**. Não é célula — é um despacho no-op de piloto. O `censo_completo_22.csv` a conta como célula `batch` com `camadas=⑥`, o que infla `batch` para 4. **Batch real = 3** (`sobol_batch·MMF16_20·{0,1,2}`).
Fora isso, o censo e eu **batemos em 15.128/15.128** em `estado` (ok 14.418 · teto 501 · fail 209) e em `sem_manifest` (80/80).

---

## 1. CONTRATO DAS 7 CAMADAS POR REGIME

Contrato lido em `CONTRATO_DE_DADOS.md` §0/§7 + D54 + T15.

| camada | main (12.321) | off (2.805) | batch (3) | total 15.128 |
|---|---|---|---|---|
| ① `__real` | 12.233 (99,29%) | 2.798 (99,75%) | 3 | 15.033 (99,37%) |
| ② `__pop` | 12.233 | 2.798 | 3 | 15.033 (99,37%) |
| ③ `__surrogate` | 8.917 (72,37%) | 2.798 | 3 | 11.718 (77,46%) |
| ④ `__timing` | 12.233 | 2.798 | 3 | 15.033 (99,37%) |
| ⑤ `.manifest.json` | 12.248 (99,41%) | 2.798 | 3 | 15.048 (99,47%) |
| ⑥ `.jsonl` | **12.321 (100%)** | **2.805 (100%)** | **3 (100%)** | **15.128 (100%)** |
| ⑦ `__final` | 0 (n/a) | 2.129 (75,90%) | 0 (n/a) | 2.129 |

Decomposição integral das ausências (fecha sem resto):

| ausência | n | classe |
|---|---|---|
| ①②④ ausentes | 95 | **(2) sancionado** — 100% `fail` (runner morreu antes do write) |
| ⑤ ausente | 80 | **(2) sancionado** — 100% `fail`; distribuição **b1 32 · c238 31 · b4 7 · b5m 7 · b3 1 · c154 1 · e74 1**. ⚠ O enunciado O-21 diz "73 do b1": **medido 80 no total, dos quais 32 são b1**. Registrado como divergência de contabilidade (D81). |
| ③ ausente c/ ① ausente | 95 | **(2)** mesmo evento acima |
| ③ ausente c/ ① presente | 3.315 | **(2) sancionado D54** — 100% em `{c122,c149,c154,c262,e81}` (bucket-only). **Zero** casos fora dos 5. |
| ③ presente nos bucket-only | 174 | c122 31 · c154 70 · c262 40 · e81 17 · c149 16 — cópia local sobrevivente; **59 delas vieram de VM diferente das demais camadas** (§7) |
| ⑦ ausente no off | 676 | b5m 7 (`fail`) + **e103 669 (`ok`)** — ver §1.1 |
| ⑦ presente | 2.129 | b5r 725 · moead_media 725 · b5m 679 — **+2.129 sidecars `__final.manifest.json`** (camada extra não listada no contrato §0) |

**③ presente porém com 0 linhas:** moead/nsga2/nsga3/smsemoa (3.000) + sobol_batch (3) = **3.003 células**. O ⑤ desses declara `sonda.status="nao_se_aplica"` — **(1) conforme** ao T15 ("as TRÊS ausências de sonda são inconfundíveis"). Nenhuma célula tem sonda onde não devia: das 11.715 ③ com linhas, **11.715 têm bloco de sonda** (`regime` alcança `sonda`/`sonda_estratificada`).

### 1.1 e103 sem ⑦ — INVESTIGADO E ESCALADO

**Medido:** 0/669 (0,00%). Não é perda de arquivo — **a ⑦ do e103 nunca existiu em lugar nenhum**: `_FONTES.csv` tem `camada=final` só para b5m (1.358) / b5r (1.450) / moead_media (1.450) = 4.258 = 2×2.129 (parquet+sidecar); **zero** para e103. Busca em `~/mestrado_coleta_m8/**/e103/*__final*` = vazia.

**Causa medida:** o e103 é o único offline do stack **MATLAB**, e o seu ⑤ **declara** a ausência, em `params.nd_final`:

> `"AVALIACAO REAL DO ND FINAL (§11/B7.5) NAO acontece neste run (a ① = SO o dataset; gate 31D-1): 'avaliado 1x FORA' — os decs finais estao na ③ (ultima geracao) e em FinalDec; DEFINICAO EM ABERTO p/ a torre: onde persiste (recomendacao: pos-hoc Python canonico, uniforme p/ todo o offline, antes do R3)"`

Corroboração no ⑥: o rodapé do runner do e103 traz `n_final=100` (constante nas 669) mas **não traz `n_nd_pos_real`** — enquanto b5m/b5r/moead_media trazem os dois. O `paths.local` do ⑤ do e103 **não tem entrada `final`**.

**Classe: (2) desvio SANCIONADO com ressalva 🔴.** O T15 §7 nomeia explicitamente "o MESMO trilho retroativo do e103", ou seja o autor já sabe que a ⑦ do e103 sai pós-hoc. **Mas** a forma exigida pelo T15 **não** está aplicada: o T15 manda `params.nd_final = FINAL_POS_HOC_INFO`, `footer` com `final_pos_hoc`, e `n_nd_pos_real` **NULL-declarado**. O que existe é a redação **antiga em prosa livre** ("DEFINIÇÃO EM ABERTO"), sem `final_pos_hoc` no rodapé e sem `n_nd_pos_real` nenhum.

**ESCALAÇÃO (D81):** (a) as métricas oficiais do regime offline (§11) **não podem incluir o e103** enquanto `scripts/final_eval.py` não rodar — 669 células, 23,85% do regime off; (b) decidir se o `params.nd_final` em prosa satisfaz a cláusula "`is_run_done` considera o run offline PRONTO sem a ⑦ **somente** com a declaração no ⑤" ou se as 669 devem ser retro-declaradas no formato T15. **Não escolhi.**

---

## 2. ⑥ ÍNTEGRO — header + footer + linhas malformadas

Denominador: **15.128 ⑥ · 6.795.313 linhas** lidas e parseadas uma a uma.

| aspecto | resultado | classe |
|---|---|---|
| linhas malformadas (JSON inválido / não-objeto) | **0 / 6.795.313 (0,000%)** | (1) conforme |
| linhas em branco | **0** | (1) |
| `rec=="header"` na 1ª linha | **15.128 / 15.128 (100%)** | (1) |
| exatamente 1 header por arquivo | **15.128 / 15.128 (100%)** — nenhum arquivo com 2 headers ⇒ **nenhum re-run apensado** | (1) |
| última linha é `footer` | **15.073 / 15.128 (99,64%)** | — |
| **⑥ SEM footer nenhum** | **55 (0,36%)** | ver abaixo |
| **⑥ com DOIS footers** | **5.599 (37,01%)** | **(3) armadilha de leitura — ver 2.1** |

### 2.1 DOIS rodapés no ⑥, com `status` CONFLITANTE — achado principal

O padrão mapeia **exatamente o stack Python** (b5m, b5r, c122, c149, c154, c262, e81, moead_media, sobol_batch: 5.599 dos 5.654 arquivos desses configs; os 55 restantes são os truncados). O stack MATLAB tem sempre 1 rodapé. Os dois rodapés são:

1. **rodapé do RUNNER** (rico: `fe_final`, `n_geracoes`, `cache_hits`, `cp_init`, `motivo`)
2. **rodapé do DESPACHANTE** (`status`, `n_retries`, `tempo_total_s`, `stack_trace`) — o append cego do AuditLogger.

Exemplo real (`c154/DTLZ2/0`): runner `{"status":"failed","motivo":"teto_wall","fe_final":284}` · despachante `{"status":"ok","n_retries":0}`.

| cruzamento (só as 5.599 com 2 rodapés) | despachante=ok | despachante=failed |
|---|---|---|
| runner=ok | 5.006 | 0 |
| runner=failed | **501** | 92 |

**As 501 divergências são exatamente as 501 ⚪.** Ou seja: **`status` do ⑥ das ⚪ depende de qual rodapé você lê.** A regra O-21 ("`manifest:failed` + `rodapé:ok` = ⚪") só fecha se "rodapé" significar o **último** (o do despachante). Mas a mesma regra diz que "o rodapé do .jsonl é a AUTORIDADE sobre o que o **algoritmo** fez" — e quem descreve o algoritmo é o **primeiro** rodapé, que diz `failed` + `teto_wall`.

**ESCALAÇÃO (D81):** fixar por escrito, na O-21, **qual dos dois rodapés é a autoridade**. Qualquer script que faça `tail -1` do ⑥ hoje lê a visão do despachante e classifica as 501 ⚪ como `ok` sem ressalva. Medição de apoio: `motivo` do rodapé do runner = `teto_wall` em 390 e `motivo_parada="teto_wall"` em 111 → **501/501 ⚪ com truncamento por parede declarado no rodapé do runner**; `motivo_parada="checkpoint_em_andamento"` **não aparece em nenhuma célula** (a sentinela ambígua da O-21 não ocorre neste acervo).

### 2.2 As 55 sem rodapé + as 5 células com ⑥ órfão — nomeadas

55 sem rodapé: `c154 15 · c122 13 · b5m 7 · c262 7 · c149 3 · b4 2 · c238 2 · b1 2 · b3 1 · c141 1 · c217 1 · nsga3 1`. Dessas, **51 são `fail`** (esperado) e **4 são `ok`**. Somando 1 caso de rodapé desalinhado, há **5 células em que o ⑥ NÃO descreve o run que gerou ①/⑤**:

| célula | ⑥ | ① | ⑤ | fontes (`_FONTES.csv`) |
|---|---|---|---|---|
| `b1·BBOB_F17·8` | 337 linhas, header 09/08 18:38, morre em `b1_gen`, sem footer | 309 (=31D−1) | ok, `fe_final=309`, `n_ger=201`, criado **14/08 11:25** vm5 | todas vm5 |
| `c141·ZDT4·9` | **1 linha (só o header)**, 08/08 | 309 | ok, `n_ger=58`, criado 14/08 11:04 vm5 | todas vm5 |
| `c217·WFG4·12` | 884 linhas, morre em `c217_gen`, sem footer | 681 | ok, `n_ger=441`, criado 14/08 11:19 | **⑥①②③④ = vm1 · ⑤ = vm5** |
| `nsga3·MMF1·14` | 34 linhas, morre em `guard` | 61 | ok, `n_ger=3`, criado 14/08 10:34 | **⑥①②③④ = vm4 · ⑤ = vm5** |
| `nsga3·DTLZ3·17` | 21 linhas, **footer `status=failed`, `fe_final=145`** | **371** | ok, `fe_final=371`, `n_ger=18` | **⑥ = vm10 · ⑤①②③④ = vm1** |

**Classe: (3) INEXPLICADO.** Todas as 5 são contadas `ok` pelo censo, com ① completo e `fe==maxfe`. Para D97 (a fidelidade sai do ⑥) **estas 5 são NÃO-AUDITÁVEIS**, e uma delas (`nsga3·DTLZ3·17`) tem ⑥ que **contradiz** o ①. Fração: 5/14.418 ok = **0,035%**. Todas com `⑤.created_at` em **14/08 10:34–11:25** — janela de re-execução. **Escalado.**

---

## 3. ⑤ COM `params` / `sigma_dict` / `campanha_id` / `repo_hash` — a T11 em escala

Denominador correto: **14.919** = ok(14.418) + teto(501) com ⑤ presente. (Os 129 ⑤ de `fail` restantes são criados do zero pelo despachante — DI-13.1 — e por construção não têm esses blocos: `c154 79 · c262 33 · c122 13 · c149 3 · sobol_batch 1`.)

| campo | chave presente | **valor não-nulo** | classe |
|---|---|---|---|
| `sigma_dict` | 14.919 (100,000%) | **14.919 (100,000%)** | (1) conforme |
| `repo_hash` | 14.919 (100,000%) | **14.917 (99,987%)** | (1) — os 2 nulos são `sobol_batch` ok, `schema_version=1` |
| `params` | 14.917 (99,987%) | 14.917 (99,987%) | (1) |
| `campanha_id` | 14.917 (99,987%) | 14.917 (99,987%) | (1) |
| `doe_hash`, `timing`, `fit_series`, `cache_hits`, `q`, `tier`, `dist`, `paths`, `env`, `algo_version`, `fallback_ativado`, `n_retries`, `status`, `maxfe`, `fe_final`, `n_geracoes`, `schema_version` | 100,000% | — | (1) |

`sigma_dict` é dict em 100% (2 a 21 chaves; constante por config). `params` idem (4 a 19 chaves). **T11 fecha.**

**Achado 🎯 dentro do que fechou — `campanha_id` com DOIS valores:**

| valor | n | % |
|---|---|---|
| `7f4f0e429a46_M8` (o cravado na env, modo normativo B-03) | 14.644 | 98,16% |
| **`63db46b10063_2026-08-14`** (o default derivado da DATA) | **273** | **1,83%** |

As 273 são todas do stack MATLAB e todas `ok`: `smsemoa 41 · nsga3 38 · moead 35 · nsga2 30 · b4 24 · e74 24 · c141 23 · b1 22 · c238 12 · b3 11 · c217 10 · e7 3`; concentradas nas sementes 12 (108), 13 (61), 26 (47), 17 (22). O prefixo `63db46b10063` é o `repo_hash` truncado, e o sufixo é a data — exatamente o modo que o B-03 mandou evitar ("a campanha leva ~21 dias e o default derivado da data mudaria de valor no meio"). **Consequência operacional:** `is_run_done` com filtro de campanha trata essas 273 como stale e **força re-run**. **Classe (3) INEXPLICADO. Escalado (D81).**

---

## 4. LEDGER DE FE

Denominador: **14.416** células `ok` (14.418 menos as 2 `sobol_batch`, cujo regime `batch` tem orçamento próprio `maxfe=2219`, medido, ≠ 31D−1=619 — **(2) sancionado por desenho do regime**).

| invariante | resultado | classe |
|---|---|---|
| `⑤.maxfe == 31D−1` | **15.030 / 15.033 (99,98%)** — as 3 exceções são as 3 `sobol_batch` | (1) |
| `n(①) == 31D−1` nas ok | **14.416 / 14.416 (100,000%)** | (1) |
| `⑤.fe_final == ⑤.maxfe` nas ok | **14.416 / 14.416 (100,000%)** | (1) |
| `⑥.fe_final == ⑤.fe_final == n(①)` (ok+teto) | **14.914 / 14.919 (99,966%)** — as 5 exceções são exatamente as 5 células de ⑥ órfão (§2.2) | (1)/(3) |
| `⑥.n_geracoes == ⑤.n_geracoes` | 14.914 / 14.919 | (1) |
| `⑥.cache_hits == ⑤.cache_hits` | 14.914 / 14.919 | (1) |
| `⑥.cp_init == true` | **14.914 / 14.914 (100%)** — zero `false` | (1) |
| **composição `init = 11D−1`** | **11.618 / 11.618 online (100,000%)** | (1) |
| idem, offline | 2.798 células com `n_init = 31D−1` (a ① inteira é `fase=init`) | **(2) sancionado D90** (§1: "a ① = o DATASET completo") |
| `n_init + n_opt == n` | 14.416 / 14.416 | (1) |
| `fase` ∈ {init;opt} online / {init} offline | 11.618 / 2.798 — nenhum outro valor | (1) |
| **`init` é prefixo contíguo de `fe_index`** | **14.416 / 14.416 (100%)** | (1) |
| NaN / Inf em `f`; NaN em `x` | **0 / 0 / 0** | (1) |

**As 501 ⚪ (teto) — e a ressalva do c154 que faltava conferir:**

| | medido |
|---|---|
| ①②④⑤⑥ presentes | **501 / 501 (100%)** — inclusive as **300 do c154** ✔ *(a ressalva O-21 "presença dos parquets das ⚪ do c154 não conferida" está agora **conferida: presentes e íntegros**)* |
| ③ presente | 2 / 501 (só c262) — **(2) sancionado D54**, bucket-only |
| `n(①) == ⑤.fe_final` | **501 / 501** |
| `fe_index` denso, `init == 11D−1`, X duplicado = 0 | 501 / 501 |
| ponto de truncamento (`fe_final / 31D−1`) | mediana **0,774** · mín **0,374** · máx 1,000 |

Orçamento comum por config (para a regra "comparar em FE COMUM"):

| config | ⚪ | `fe_final` mín | mediana | máx | `31D−1` mediano |
|---|---|---|---|---|---|
| c154 | 300 | 236 | 297 | 367 | 681 |
| c262 | 90 | 501 | 599,5 | 929 | 681 |
| c122 | 85 | 537 | 646 | 929 | 681 |
| c149 | 26 | 795 | 849 | 927 | 929 |

---

## 5. A ARMADILHA DA T11 — campos presentes com dado sentinela

Varredura por estatísticas de rodapé Parquet (min/max/null_count) de **58.946 arquivos** (①②③④⑦) + varredura de valores dos 15.048 ⑤. Listo **só** o que é constante/nulo em ~100% do denominador.

### 5.1 INEXPLICADOS — (3) 🎯

| camada | campo | fração | leitura |
|---|---|---|---|
| **⑦** | **`origem_solution_id`** | **100% NULO em 2.129/2.129 células** (b5m 679, b5r 725, moead_media 725) | O §7 define esse campo como o link da ⑦ para a ①. **Nunca foi preenchido.** O `origem_linha`+`origem_geracao` (o link posicional DI-31/T4) estão preenchidos, então há caminho alternativo — mas o campo do contrato está morto. **Mesma assinatura do `pmid_ids` do c217.** |
| **②** | **arquivo com 0 LINHAS** | **2.129/2.129 células** de b5m+b5r+moead_media (100% do offline-Python) | ② vazia em 100%. O e103 (offline-MATLAB) tem ② com 42–9.900 linhas. §2 admite "só os membros do DATASET na pop selecionada", mas **zero em 100% das 2.129** contra **não-zero em 100% das 669 do e103** é assimetria de stack, não amostragem. Qualquer análise ①+② (sobrevivência/descarte) é **vazia** para 3 dos 4 offline. |
| **④** | **`tempo_busca_s` 100% NULO** | **3.000 células** (moead, nsga2, nsga3, smsemoa — 100% dos 4 pisos online) | §4 grava em negrito que `tempo_busca_s` é **OBRIGATÓRIO** ("era opcional/NaN"). O DI-13.2 sanciona NULL **só para `tempo_fit_s`**. O `sobol_batch` (também piso) **grava** `tempo_busca_s`. |
| **④** | `tempo_pred_sonda_s` 100% NULO | 3.000 (mesmos 4 pisos) | §4 define `0` = "não roda", não NULL. |
| **④** | `n_acumulado` 100% NULO | 3.000 (mesmos 4 pisos) | eixo-x da escalabilidade morto nos pisos |
| **⑤** | bloco `timing` **sem** `tempo_fit_surrogate_s` **e sem** `tempo_busca_s` | 3.000/14.919 (20,11%) — mesmos 4 pisos | §4: "o bloco `timing` do MANIFESTO vira **OBRIGATÓRIO nos 21**" com os 4 agregados nomeados. Falta 2 dos 4 em 20% do acervo. Idem `fit_series = []` nas mesmas 3.000. |
| **②** | **`geracao` 0-BASED** | **1.313/12.904 (10,18%)**: c154 624 · c262 686 · sobol_batch 3 | R4 #8: "gerações são **1-based**". Nas mesmas células a ③ e a ④ são 1-based (verificado em **110/110** células de c154/c262 que têm ② e ③): **off-by-one entre ② e ③/④ dentro do mesmo config.** Trava qualquer join ②↔③ por geração nesses dois. |
| **④** | `geracao` 0-based | 669/669 (e103) | 1 linha por célula (offline) |
| **③** | `transf_tipo`/`transf_params` **100% NULOS** | **669/669 (e103)** | DEF-C3 nomeia o e103 **explicitamente** entre os que operam em espaço transformado ("e103/c149 z/…"). Preenchidos em b1, c149, c238, e7, e81; nulos no e103. |
| **③** | `espaco_modelo` **CONSTANTE** (1 valor só) | b1 `transformado` (701) · c149 `cru` (16) · e81 `cru` (17) | DEF-C3: "gravam-se os **DOIS** espaços". Só **c238 e e7** gravam `cru`→`transformado`. c149/e81 declaram `transf_tipo="zscore"` **e** marcam `espaco_modelo="cru"` em 100% das linhas — contraditório. |
| **③** | `espaco_modelo` **100% NULO** | c122 31 · c154 70 · c262 40 (100% das ③ locais desses) | campo do contrato ausente de ponta a ponta |

### 5.2 SANCIONADOS / explicáveis — (2), listados para o autor bater o olho

| campo | fração | por quê |
|---|---|---|
| ⑤ `fallback_ativado = False` | **14.919/14.919 (100,000%)** | nunca disparou. Não é possível distinguir "não disparou" de "não instrumentado" — vale registrar. |
| ⑤ `n_retries = 0` | **14.919/14.919 (100,000%)** no denominador ok+teto | mecanismo **existe e disparou**: 3 células `fail` têm `n_retries=2`. Sentinela aparente, não real. |
| ⑤ `repo_hash` = 1 valor único (`63db46b1006…`) | 14.917/14.917 | consistente com o `m8-freeze`; mas por ser constante **não detecta** troca de código. |
| ④ `tempo_checkpoint_s` **100% NULO** | 2.129 (b5m, b5r, moead_media) | BL-11: NULL = "config sem checkpoint" — **é a semântica documentada** |
| ⑤ `timing` sem `tempo_aval_real_s` | 2.129 (b5m,b5r,moead_media) | offline não avalia real na busca (D90) |
| ③ `mu_*` 100% nulo | b4, c122, c217 (classificador/score) | DEF-C1 |
| ③ `mu_*`/`sigma_*` nulos em 54,7% | b1 | D47 mono-output (mu_0 preenchido, mu_1.. NULL) |
| ③ `real_solution_id` 100% NULO | b5m, b5r, moead_media (2.129) | offline não avalia candidatos; **mas o e103 preenche (0% nulo)** — assimetria de stack que quebra join uniforme no offline |
| ③ `sigma_*` nulo em 55,4% (e74) / 10,7% (c141) | híbrido RBF sem σ | DEF-C1 |
| ③ `fe_treino_max` constante | b5m, b5r, moead_media, e103 (100%) | treino único (offline) |
| ⑥ `n_final = 100` constante | 669/669 e103 | = N do IBEA, não contagem de ND |
| ③ `geracao` como `double` | e103 | R4 #2 (dicotomia cross-stack int-NULL × double+NaN) |

**Falsos positivos que investiguei e descartei:** `pred_confianca` identicamente 0 só em **3/750** células do c217 (não é sentinela sistêmica); `fe_treino_max` **nunca** negativo (0 células com −1) em 8.715 ③.

---

## 6. DUPLICATAS DE X (D89) E `fe_index` DENSO

| invariante | resultado | classe |
|---|---|---|
| **`fe_index` denso `0..n−1`** (0-based, R4 #8) | **14.416/14.416 ok (100,000%)** + **501/501 ⚪** + **114/114 fail com ①** = **15.033/15.033 (100,000%)** | (1) conforme |
| `fe_index` 1-based | 0 células | — |
| `solution_id` único e começando em 0 | **15.033/15.033 (100%)** | (1) |
| **X duplicado (float32) dentro da célula** | **1.802/14.416 ok (12,50%)** · **0/501 ⚪** | ver abaixo |

Distribuição das 1.802 (mediana e máximo de linhas duplicadas por célula):

| config | células c/ dup | mediana dup | máx dup |
|---|---|---|---|
| moead | 622 / 750 (82,9%) | 2 | 14 |
| b1 | 433 / 701 (61,8%) | 6 | **74** |
| smsemoa | 155 / 750 | 1 | 4 |
| nsga2 | 144 / 750 | 1 | 4 |
| nsga3 | 127 / 750 | 1 | 6 |
| c217 | 108 / 750 | 1 | 4 |
| b4 | 105 / 738 | 1 | 4 |
| c149 | 90 / 688 | **16** | 27 |
| c122 12 · c141 4 · b3 2 | — | 1 | 3 |

**Classe: T — teto de verificabilidade, não achado.** D57 manda dedup por **X float64 bit-a-bit em runtime**; o disco guarda **float32** (D53). A regra T11/A37.2 é explícita: float32 pode colidir pontos float64 distintos. **Portanto NÃO afirmo que há re-avaliação duplicada** — afirmo que **na resolução do dado persistido 12,50% das células ok têm ao menos 2 linhas de X indistinguíveis**, e que essa medida **não decide** entre (a) colisão de float32 e (b) violação de D89. Só o ⑥ (eventos `guard`/cache-hit) ou uma re-execução com X float64 decidiriam — e re-execução está vetada. Os 3 configs com concentração alta (moead 82,9%, b1 61,8%, c149 mediana 16) são os candidatos para o autor cravar manualmente se quiser fechar esse teto.

---

## 7. PROVENIÊNCIA — camadas de UMA célula vindas de VMs DIFERENTES

Não estava na lista, mas caiu no colo ao rastrear as 5 células de §2.2. Medido sobre as 91.257 linhas do `_FONTES.csv`:

| | n |
|---|---|
| células com **todas** as camadas da mesma VM | **15.067 (99,58%)** |
| células **MISTAS** (2 VMs) | **63 (0,42%)** |
| ↳ só a ③ de outra VM | 59 — `e81 17 · c122 18 · c149 13 · c262 7 · c154 4` (todos bucket-only: a ③ foi buscada onde sobreviveu). **(2) plausivelmente inócuo, não provado** |
| ↳ **⑤ de outra VM** | 3 — `c217·WFG4·12` (vm5 vs vm1) · `nsga3·MMF1·14` (vm5 vs vm4) · `e81·ZDT4·42` (vm3 vs vm5) |
| ↳ **⑥ de outra VM** | 2 — `nsga3·DTLZ3·17` (vm10 vs vm1) · `e81·ZDT4·42` (vm3 vs vm5) |

**As 4 células com ⑤ ou ⑥ de outra VM são 3 das 5 de §2.2** — ou seja, a consolidação montou células a partir de **execuções diferentes**. As outras 2 (`b1·BBOB_F17·8`, `c141·ZDT4·9`) vieram inteiras da vm5: lá o ⑥ velho ficou no disco e o re-run de 14/08 reescreveu ①③⑤ **sem** reescrever nem apensar ao ⑥ (o arquivo tem 1 header só). Lista completa em `celulas_mistas.csv`. **Classe (3). Escalado.** Isto é ortogonal à doutrina RUNBOOK §6.2 (fidelidade estatística, não bit-exata) — não é deriva de float, é **mistura de runs**.

---

## RESUMO DE VEREDITOS — evidência, não sentença (D97)

**(1) CONFORME, em escala:** ⑥ 100% presente, 0 malformadas em 6,79 M linhas, 1 header por arquivo, 0 re-runs apensados · `maxfe==31D−1` 99,98% · `fe_final==maxfe` 100,000% das ok · `init==11D−1` 100,000% das online · `fe_index` denso 100,000% · `solution_id` único 100% · `sigma_dict` 100,000% · `repo_hash` 99,987% · zero NaN/Inf · **501 ⚪ com ①②④⑤⑥ íntegros, inclusive as 300 do c154**.

**(3) INEXPLICADOS a escalar (D81) — 8, por ordem de peso:**
1. **Dois rodapés no ⑥ com `status` conflitante** em 5.599 células; nas 501 ⚪ o veredito inverte conforme o rodapé lido. A O-21 precisa dizer qual manda.
2. **5 células `ok` cujo ⑥ não descreve o run de ①/⑤** — não-auditáveis para D97; 1 delas (`nsga3·DTLZ3·17`) tem ⑥ contradizendo o ①.
3. **63 células montadas a partir de 2 VMs**, 4 delas no ⑤/⑥.
4. **⑦ `origem_solution_id` 100% NULO** em 2.129/2.129.
5. **② vazia (0 linhas) em 2.129/2.129** do offline-Python, contra 669/669 não-vazias do e103.
6. **`tempo_busca_s` (④ e ⑤) 100% NULO nos 4 pisos online** (3.000 células), contra o "OBRIGATÓRIO" do §4.
7. **② `geracao` 0-based em c154/c262/sobol_batch** (1.313 células) contra R4 #8, com ③/④ 1-based na mesma célula.
8. **`campanha_id` derivado da data em 273 células ok** — o modo que o B-03 proibiu.

**(2) SANCIONADOS, citados:** ③ ausente nos 5 bucket-only (D54) 3.315 · ①②④⑤ ausentes só em `fail` (95/80) · ① offline = dataset inteiro (D90) 2.798 · ③ vazia nos pisos sem surrogate (T15 `nao_se_aplica`) 3.003 · `tempo_fit_s` NULL nos pisos (DI-13.2) · `tempo_checkpoint_s` NULL = "sem checkpoint" (BL-11) · `mu/sigma` nulos por tipo de preditor (DEF-C1/D47).

**(T) TETOS:** duplicatas de X (float32 não decide, 12,50% das ok) · `fallback_ativado=False` e `repo_hash` constante em 100% (não distinguem "não ocorreu" de "não instrumentado") · a ③ dos 5 bucket-only mora no bucket e **não foi lida** (só 174 cópias locais).

**Duas correções de contabilidade para a torre:** o censo tem **15.128** células (a 15.129ª é um stub no-op de 4 linhas no espelho da vm3) e as células sem ⑤ são **80**, das quais **32** são b1 (a nota O-21 diz "73 do b1").