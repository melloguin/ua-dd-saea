# DI09-retrofit-R2 — RELATÓRIO DE EXECUÇÃO

> Números medidos nesta sessão. Ambiente `env-main`, botorch 0.18.1 OFICIAL,
> Mac (arm64), 1 core pinado (D79). **Nada aqui é julgamento de fidelidade
> (D97)** — só encanamento objetivo e evidência do gate.

---

## 1. Gates

```
🔴 NAO-PERTURBACAO (① bit-a-bit vs data/experiments/_baseline_pre_retrofit/)
   c262/MMF1 : 61L  sha=c37afd6d4f551d66     == idem   VERDE ✓
   c154/MMF1 : 61L  sha=95be196c1855bd70     == idem   VERDE ✓
   c262/DTLZ2: 371L sha=e43c52033eff0b9d29a2 == idem   VERDE ✓  (opcional; D=12,M=3,241 iters)

accept.py    R2-c262/MMF1 · R2-c262/DTLZ2 · R2-c154/MMF1 · R2-c154/DTLZ2   VERDE ×4
             (4 saídas + jsonl · FE=31D−1 exato · CP-init DoE bit-a-bit)
             F0-01 · F0-02 · F0-03 · F0-04 · R2-00-harness · preflight        VERDE ×6
suíte        122 testes (30 novos em tests/test_di09_r2.py)                   VERDE
```
Gates R1 **não** rodados — faixa MATLAB ativa (instrução do cartão).

## 2. Auditoria pyarrow — c262/MMF1 e c154/MMF1

Idênticos nos dois configs (MMF1: D=2, M=2, 41 iterações):

| Item | Medido | Esperado |
|---|---|---|
| ③ total | 44.410 linhas | — |
| ③ busca | 410 | 41 iters × 10 restarts |
| ③ sonda | 44.000 | 22 × 2000 |
| blocos de sonda | 22, gerações `{1, 2, 4, …, 40, 41}` | 1ª + k=2 + última ✓ |
| linhas por bloco | todas exatamente 2000 | 2000 ✓ |
| ordem do artefato | bit-exata vs `sonda_MMF1.parquet` | join por posição ✓ |
| `fe_treino_max` | 0 NULL em 44.410 | toda linha ✓ |
| `real_solution_id` na sonda | 44.000/44.000 NULL | ✓ |
| ④ | 41 linhas, **0 NULL** em busca/sonda/geração | ✓ |
| ⑤ `timing` | 4 chaves + `tempo_pred_sonda_s` | obrigatório ✓ |
| ⑤ `sigma_dict` | 10 chaves | DEF-C4 ✓ |
| ⑥ eventos `sonda` | 22 | 1 por bloco ✓ |
| ⑥ mínimo comum DI-10 | completo | ✓ |

Específicos do jsonl (1ª decisão): c262 `n_baseline=7` (pós-prune, contra
`n_train=21` — a poda é real e visível), `mll_final=−0,8214`,
`|acqf_todos_restarts|=10`. c154 `n_train=21` (o campo que substitui o
`n_baseline` N/A — DI-11), `mll_final=−0,6794`, `|acqf_todos_restarts|=10`
(=5·D).

## 3. Custo da instrumentação (MMF1, 41 iterações, 22 blocos = 44.000 predições)

| | c262 | c154 |
|---|---|---|
| `tempo_total_s` | 34,73 s | 95,76 s |
| `tempo_busca_s` | 28,09 s (80,9%) | 84,71 s (88,5%) |
| `tempo_fit_surrogate_s` | 2,86 s | 7,41 s |
| **`tempo_pred_sonda_s`** | **1,16 s (3,3%)** | **1,43 s (1,5%)** |
| ③ em disco | 15 KB → **1,4 MB** | 16 KB → 1,4 MB |

**Leitura para o dimensionamento do M7:** a sonda custa **1,5–3,3% do wall** e
o custo é praticamente idêntico nos 2 configs — é função do modelo (GP sobre
2000 pontos), não do algoritmo. Como a busca domina (81–89%), a sonda **não
muda a ordem de grandeza de nenhum run**. O que ela move é **volume em disco**:
a ③ cresce ~90× no MMF1. Confirma a aritmética dos ~260 GB extras que o autor
já cravou na DI-09 — não é surpresa, mas agora é medido.

## 4. c154/DTLZ2 — backfill da ④ (sem re-rodar as 14h37)

```
241 linhas · tempo_busca_s: 0 NULL (240 EXATAS + 1 DERIVADA)
241/241 conferidas contra a ④ do disco antes de qualquer escrita
```

**Validação cruzada independente** (dois caminhos que não se conversam):

| Grandeza | ④ backfillada | Manifesto (registrado no run) | Δ |
|---|---|---|---|
| Σ `tempo_busca_s` | 51.674,4 s | 51.674,4185 s | ~0,02 s |
| Σ `tempo_geracao_s` | 52.596,1 s | `tempo_total_s` = 52.596,3 s | 0,2 s |

A diferença de 0,2 s é o setup/teardown fora do laço — exatamente o resíduo
esperado. **Calibração do estimador derivado:** nas 240 iterações de valor
conhecido, `ts(decision) − ts(timing)` errou **+8 ms em ~450 s** (2×10⁻⁵).

A procedência exato × derivado está gravada no manifesto (`timing_backfill`).

## 4.1 Revisão adversarial do diff — 12 defeitos confirmados, 4 corrigidos

Rodei uma revisão multi-agente sobre o diff do cartão (5 lentes independentes →
verificação cética de cada achado, viés default REFUTAR). **35 levantados, 12
sobreviveram.** Consolidados, são 3 defeitos distintos:

**(a) 🔴 O backfill trocava medida por derivação — CORRIGIDO (`bb17129`).**
Sete dos doze achados apontavam a mesma raiz. `write_timing` reescreve o arquivo
INTEIRO, mas a guarda só conferia `geracao`/`n_acumulado`/`tempo_fit_s` — que
batem **por construção** (vêm do mesmo `add_timing`). As 3 colunas de tempo
passavam sem conferência. Um verificador **reproduziu empiricamente** o dano:
rodar o backfill sobre o run pós-retrofit `c262/MMF1` inflaria
`tempo_geracao_s` em **+10,66%** e trocaria `tempo_pred_sonda_s` de `0.0` para
NULL em **19/41** linhas — sem erro, e com o relatório ainda dizendo
"41 linhas conferidas vs disco". Duas causas somadas: a definição do backfill
**incluía** a sonda e o gc (o escritor vivo **desconta** a sonda), e a última
geração ia até o `footer`, que os 2 runners só emitem **depois** de
`write_run_outputs` (4 parquets + manifesto + upload) — inflando justamente a
linha de maior `n`, a que mais pesa no ajuste da curva de custo. Corrigido com
guarda de escopo, guarda estendida, definição alinhada, última geração =
`fit+busca`, e NULL-contado para `tempo_busca_s` derivado negativo. 4 testes de
regressão.

**(b) 🔴🔴 `experiments.py` apaga o manifesto do retrofit — NÃO corrigido
(fora da faixa).** É bloqueador para a M8; detalhado em §A-9 das DEFINIÇÕES EM
ABERTO. Os runs desta sessão estão íntegros (despachei por
`src.experiment.run` direto).

**(c) Aborto por teto × artefatos anteriores — NÃO corrigido (pré-existente,
DI-06).** §A-10 das definições.

O c154/DTLZ2 foi **re-backfillado** com a semântica corrigida (④ restaurada ao
estado pré-backfill antes): última geração 488,76 s → **488,54 s**. As somas
seguem batendo com o manifesto.

## 5. O achado do processo (vale registrar)

O teste `test_minimo_comum` reprovou na primeira execução e expôs um bug real:
`n_front1` usava `np.count_nonzero(_nds_filter(F))`, mas **`_nds_filter`
devolve ÍNDICES, não máscara booleana** — o índice 0 era silenciosamente
descartado sempre que o primeiro ponto fosse não-dominado. O número estava
errado por −1 na maioria das iterações e **nada teria acusado** até a análise
R4. Corrigido (`len(...)`) e os 2 runs de gate foram re-executados. É o
argumento a favor de instrumentar com teste, não com inspeção.

## 6. Run opcional `c262/DTLZ2` — CONCLUÍDO, VERDE (escala real)

D=12, M=3, 241 iterações. Wall **8.972 s = 2h29**, contra ~2h31 do baseline
pré-retrofit: **a sonda não é distinguível do ruído no wall total.**

```
🔴 NAO-PERTURBACAO: ① 371 linhas, sha e43c52033eff0b9d29a2 == baseline  VERDE ✓
③ 246.410 linhas | busca 2.410 · sonda 244.000
   122 blocos (esperado 122) · gerações {1,2,4,…,240,241} conferem
   todas com 2000 linhas · ordem do artefato bit-exata · fe_treino_max 0 NULL
④ 241 linhas, 0 NULL nas 3 colunas
⑤ sonda 122×2000 · sigma_dict 10 chaves   ⑥ sonda 122 eventos
```

| | medido |
|---|---|
| `tempo_pred_sonda_s` | **16,29 s de 8.972 s = 0,18 %** |
| `tempo_busca_s` | 8.838 s (**98,5 %**) |
| ③ em disco | 0,22 MB → **9,1 MB (41×)** |

> ⚠ **Correção honesta da minha projeção.** Eu havia projetado ~7 s (0,08 %) de
> sonda aqui, extrapolando linearmente do MMF1. O medido foi **16,3 s (0,18 %)**
> — subestimei por ~2×, porque o custo do posterior cresce com `n_train` (371 no
> DTLZ2 contra 61 no MMF1), não com o nº de blocos apenas. **A conclusão não
> muda:** a busca é 98,5 % do wall e o que a sonda move é disco.

**Extrapolação de volume para a M8:** 9,1 MB/run neste porte, 16.500 runs, com D
indo até 30 (ZDT1) — sustenta **por medição** a ordem de grandeza dos ~260 GB
extras que o autor já cravou na DI-09.
