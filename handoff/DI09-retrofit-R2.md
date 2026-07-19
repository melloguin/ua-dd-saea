# DI09-retrofit-R2 — handoff

> **Cartão:** a instrumentação DI-09/DI-10 (SPEC v5.2.1) nos 2 runners BoTorch
> (c262 qNEHVI, c154 JES) + o lado Python do writer, mais o adendo DI-11.3
> (projetor de wall-clock). READ-ONLY na busca; o gate central é a
> **NÃO-PERTURBAÇÃO**. Ambiente: `env-main`, botorch **0.18.1 OFICIAL**.
> Sessão em paralelismo triplo (retrofit-MATLAB + R3-00) — faixa respeitada.

---

## 1. Veredito

| Gate | Resultado |
|---|---|
| 🔴 **NÃO-PERTURBAÇÃO c262/MMF1** (① vs `_baseline_pre_retrofit/`) | **VERDE — bit-idêntica** |
| 🔴 **NÃO-PERTURBAÇÃO c154/MMF1** (① vs `_baseline_pre_retrofit/`) | **VERDE — bit-idêntica** |
| Suíte de testes (122 casos, +30 novos) | **VERDE** |
| F0-01 / F0-02 / F0-03 / F0-04 | **VERDE** ×4 |
| R2-00-harness · preflight | **VERDE** |
| `accept.py` R2-c262 / R2-c154 (MMF1 e DTLZ2) | **VERDE** |
| Revisão adversarial do diff (5 lentes, 35→12 confirmados) | 4 corrigidos · 2 escalados (fora da faixa) |

Gates R1 **não** rodados (faixa MATLAB ativa — instrução do cartão).

## 2. O que passou a ser gravado

### ③ `__surrogate` — a sonda entra na tabela
- **`fe_treino_max`** (int32, nullable — DI-09/A1): maior `fe_index` no treino do
  modelo no fit daquela predição. Cravado no `SnapshotBuffer` logo após o fit
  (`set_fe_treino_max(n_train−1)`) e **herdado por toda linha** — nenhuma
  predição sai sem o marcador in-sample × out-of-sample.
- **`regime` por linha**: era um valor único para o arquivo inteiro; agora a
  linha manda sobre o default do writer. É o que permite `'sonda'` e a busca
  conviverem na MESMA ③, como a §17.2.2 exige.
- **A sonda**: 2000 linhas por bloco, `regime='sonda'`, `real_solution_id=NULL`,
  **na ORDEM do artefato** (o join com o gabarito é POR POSIÇÃO — R4 regra 5).

### ④ `__timing` — `tempo_pred_sonda_s` e `tempo_geracao_s`
Ambas nullable. `tempo_busca_s`, que era NULL em 100% das linhas nos 2 configs,
passa a ser **preenchido sempre**.

> ⚠ **Decisão de semântica que a torre deve conhecer:** `tempo_geracao_s`
> **EXCLUI** a sonda. Ela é instrumentação DESTE estudo, não custo do algoritmo;
> incluí-la contaminaria a análise de custo/escalabilidade (§17.6) e a
> comparação entre famílias. O custo da sonda vai medido à parte, na coluna
> própria. **O projetor de teto, ao contrário, vê o wall CHEIO** — lá a
> pergunta é o relógio de parede do operador, não o custo do mecanismo.

### ⑤ manifesto
`timing` completo pelo helper único (`export.manifest_timing_block`, agora com
`tempo_pred_sonda_s`) + bloco **`sonda`** (S, k, hashes, nº de blocos/linhas) +
**`sigma_dict`** (DEF-C4) nos dois configs.

### ⑥ jsonl — DI-10
Mínimo comum novo em todo `<alg>_gen`: `fe`, `f_best[]`, `n_front1`,
`dist_min_arquivo` (B3, espaço de decisão normalizado), `tempo_fit_s`,
`tempo_busca_s`, `modelo_hp` (θ min/med/max + outputscale + ruído + `mll_final`).
Específicos: **`acqf_todos_restarts`**, **`n_baseline`** (c262) / **`n_train`**
(c154), **`mll_final`**. Evento **`sonda`** por bloco (geração, fe, n_pontos,
tempo, hash-check).

Os campos são tirados **no momento do log**, para que `fe`/`f_best`/`n_front1`
reflitam o ramo que chamou (com ou sem o infill consumido).

## 3. Como a NÃO-PERTURBAÇÃO foi garantida (e provada)

O laço dos 2 runners depende do **RNG global do torch** (`manual_seed` por
iteração, e no c154 também por amostra de caminho). Qualquer consumo de RNG pela
instrumentação deslocaria a trajetória.

1. `preserve_torch_rng()` / `preserve_all_rng()` (torch + numpy + `random`)
   envolvem **toda** predição de sonda, o cálculo do `modelo_hp` e o mínimo
   comum DI-10.
2. A sonda é emitida **depois** da busca da iteração (isolamento máximo) e
   **antes** do `del model`.
3. Predição sob `no_grad`, em lotes de 512 (os 2000 pontos são independentes ⇒
   numericamente neutro), sem tocar o `FEBudget` (ZERO FE).
4. **Prova objetiva**: a ① dos runs re-executados é **bit-idêntica** à baseline.

Ponto de risco isolado antes do gate caro: a extração do `mll_final` exige um
forward do MLL sobre o modelo ajustado. Um probe direto confirmou que os
candidatos **e** os valores da acqf do `optimize_acqf` seguinte saem
**bit-a-bit idênticos** com e sem a extração (modo do módulo e RNG restaurados).
Há teste unitário para isso.

## 4. A última iteração da sonda

`sonda_due(it)` cobre a 1ª e a cadência k=2. A **última** iteração só se conhece
quando o hard-stop chega — então o bloco é emitido no ramo `BudgetExhausted`,
onde o modelo daquela iteração ainda está vivo. Verificado no c262/MMF1:
blocos nas gerações `{1, 2, 4, …, 40, 41}` — 22 blocos, 44.000 linhas, todos com
exatamente 2000 linhas, ordem do artefato bit-exata.

## 5. c154/DTLZ2 — o backfill (sem re-rodar as 14h37)

`export.backfill_timing_from_jsonl()` reconstrói a ④ a partir do `.jsonl`.
Resultado: **241 linhas, `tempo_busca_s` 0 NULL** (240 exatas + 1 derivada), as
241 conferidas contra a ④ do disco antes de qualquer escrita.

**A distinção exato × derivado está no manifesto** (`timing_backfill`) — dado de
tese não se maquia:

| Coluna | Procedência |
|---|---|
| `geracao`, `n_acumulado`, `tempo_fit_s` | EXATO (evento `timing`) |
| `tempo_busca_s` (240/241) | EXATO (`t_busca_s` da `decision`) |
| `tempo_busca_s` (it 241) | DERIVADO — a `decision` da última é o `hard_stop`, que fecha antes de o wall da busca ser logado |
| `tempo_geracao_s` (240/241) | DERIVADO — âncoras `ts(timing) − tempo_fit_s`, **descontada a sonda** (a definição do escritor vivo) |
| `tempo_geracao_s` (it 241) | DERIVADO — `fit + busca`, cota INFERIOR: o `footer` do jsonl vem **depois** da escrita das 4 camadas e do upload, que não são custo da geração |
| `tempo_pred_sonda_s` | NULL — run PRÉ-sonda (o jsonl inteiro não tem evento `sonda`), não havia grandeza a medir |

**Calibração do estimador derivado:** contra as 240 iterações de valor
conhecido, `ts(decision) − ts(timing)` errou **+8 ms em ~450 s** (2×10⁻⁵
relativo).

**Validação cruzada independente:** o ④ backfillado soma `tempo_busca_s` =
**51 674,4 s** contra os **51 674,4185 s** que o manifesto já registrava por
outro caminho.

> ⚠ A semântica de `tempo_geracao_s` deste backfill foi **corrigida após a
> revisão adversarial** (commit `bb17129`); a ④ foi restaurada ao estado
> pré-backfill e reconstruída. Ver §4.1 do RELATÓRIO.

## 6. DI-11.3 — o teto de wall-clock (adendo B / lacuna D-8)

O projetor herdado só armava **depois de 10 amostras** e nunca testava `elapsed`
isoladamente: um problema de ~45 min/iteração furaria um teto de 8h **sem nunca
projetar**. `_WallClockProjector.exceeded()` ganhou um **teto de tempo DECORRIDO
independente**, avaliado antes da projeção, e passou a devolver também o
**critério** (`'elapsed'` | `'projecao'`), que vai ao jsonl — a leitura de um
aborto muda conforme o motivo. O comportamento do aborto é o mesmo de antes
(limpo, curva parcial, sem parquets órfãos). Não muda busca nem numérica;
validado em teste unitário, sem run real, como o adendo pede.

## 6.1 ⚠ Bloqueador escalado (fora da faixa) — leia antes da M8

A revisão adversarial confirmou que **`experiments.py::_run_one` sobrescreve o
manifesto que o runner grava**, com um `timing` stub — apagando `sigma_dict`,
bloco `sonda`, `doe_hash`, `fe_final`, `fit_series`. É pendência conhecida
(DI-06) mas o retrofit multiplicou a consequência: **a bateria M8 despachada por
ali perderia todo o payload DI-09/DI-10 da camada ⑤, sem sintoma visível.**
Detalhes e recomendação em §A-9 das DEFINIÇÕES EM ABERTO. Os runs desta sessão
estão íntegros (despacho por `src.experiment.run` direto, verificado).

## 7. Faixa e higiene

Tocados: `src/export.py`, `src/botorch_harness.py`, `src/c262_qnehvi.py`,
`src/c154_jes.py`, `tests/test_di09_r2.py`, `handoff/DI09-retrofit-R2*.md`.
**Nenhum** `*.m`, `algorithms/**`, `experiment.py`, `accept.py`, `naming.py`,
`gen_sonda.py`, `data/sonda/**`, `_baseline_pre_retrofit/**`, INDEX/SPEC/docs.
`manifest.py`/`budget.py`/`audit_log.py`/`gcs.py` **não** foram editados — o
`sigma_dict` e os blocos novos entram pelo runner, no padrão que o c262 já usava
para `acqf_ref_f`/`fused_kernel`. Commits com o ritual anti-mistura (`add`
explícito + staged-check + commit num comando); nunca `git add -A`.
