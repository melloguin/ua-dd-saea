# T9-calibracao — calibração POR MEDIÇÃO do custo da aquisição batch (q=10)

> Sessão de implementação · 2026-07-24/25 · branch `experiment/definitive_algorythms`
> Cartão ÚNICO T9 (DI-35.1): calibrar POR MEDIÇÃO o custo da aquisição batch (q=10)
> de **c262** e **c154** para ~10 h/run ("o ponto ótimo do tradeoff tempo×qualidade"
> do autor). Coexistência com T8 (faixas disjuntas) respeitada.
> Arquivos tocados (os ÚNICOS): `src/c154_jes.py` · `src/c262_qnehvi.py` (só comentário) ·
> `tests/test_batch_q10.py` · `handoff/T9-calibracao{,_RELATORIO,_REPASSE}.md`.

## 1. O achado que reenquadra tudo: os "~56 h/~100 h" do T6 eram CONTENÇÃO

O repasse T6 (D-0/D-1) reportou c262 ~56 h e c154 ~100 h como custo do batch cheio.
**Medido agora LIMPO (1 core, serial, sem contenção, em TEMPDIR), os dois são MUITO
mais baratos** — o T6 mediu os 4 online **em paralelo numa máquina de 16 GB, com
swap/OOM** (o próprio c262 do T6 foi morto por memória). O projetor embutido, sob esse
regime, projetou 202 336 s (~56 h) em fe=209 — puro artefato de contenção.

**Método desta calibração (o que o cartão pediu — medir, não chutar):**
- Probes em TEMPDIR (`doe`/`sonda` symlink p/ `data/`, saídas fora de `data/`), no
  `env_main` (botorch 0.18.1), **1 core** (`OMP/MKL/OPENBLAS/NUMEXPR=1` + `pin_runtime`),
  **SEMPRE serial** (2 probes juntos falseiam o t/iter — o entregável).
- ZDT4/42 (D=10, M=2), q=10 — a mesma célula do smoke T6. Cap de iterações por
  `budget.K_BATCH`; knobs por monkeypatch das constantes de módulo (NÃO tocam `src/`).
- Curva por iteração do jsonl (`tempo_busca_s`, `tempo_fit_s`, `t_paths_s`, ts).
  Projeção das 200 iterações (n=109…2099) pela **integração da PRÓPRIA curva medida**
  (busca power/linear + fit + overhead), + um **FLOOR sem extrapolação** (o resto das
  iters ao último t_busca medido) como piso robusto. ⚠ Um 1º repasse usou "método da
  razão" (razão × custo-cheio) p/ o c154 e ERROU (âncora-cheia não medida): a revisão
  adversária pegou; a projeção correta e mais conservadora é a integração direta (§3).

## 2. c262 (qNEHVI) — NÃO precisa de knob (medido ~2,2 h)

**MC_SAMPLES é um DUD.** Sweep MC ∈ {16,32,64,128} (40 iters cada, n→499):
o `t_busca` fica ~13–23 s em n≈499 em TODOS — reduzir MC **não muda o custo**
(o gargalo é o particionamento do baseline, não a amostragem MC). Reduzi-lo só
baixaria a qualidade da aquisição.

**Receita CHEIA (10 restarts / 512 raw / MC 128), medida limpa até n=669 (57 iters,
o probe deep foi OOM-killed em n=669 — ver §5):**

| componente | projeção 200 it | expoente |
|---|---|---|
| busca (aquisição greedy q=10) | ~1,6 h | p≈0,54 (sub-linear) |
| fit (GP O(n³), pequeno) | ~0,6 h | p≈2,17 |
| overhead (sonda/export/eval) | ~0,0 h | — |
| **TOTAL** | **~2,2 h** | faixa 1,9–2,7 h |

**~2,2 h << 10 h alvo << 12 h teto ⇒ o c262 fica com a receita cheia (paper), SEM
redução.** É a leitura fiel (mantém a receita do artigo) e a mais barata em tempo.
O único gargalo real do c262 batch é **RAM** (o baseline cresce com n — D-2 do T6),
reproduzido aqui como OOM ao vivo: é **provisionamento**, não receita.

## 3. c154 (JES) — 🔴 ~10 h COMPLETO é INVIÁVEL (medido); o teto trunca

Diferente do c262: o c154 é **genuinamente caro**. Anchor limpo medido: **receita
cheia (5D/1000D), t_busca@n=109 = 1051 s** (~17,5 min só a it 1). E o custo **cresce
~n^1,5-1,7** (o posterior do GP por avaliação da aquisição JES-LB, **SEM prune de
baseline** — ≠ c262, que satura). Projetei cada config **pela SUA PRÓPRIA curva
medida** integrada nas 200 iterações (n→2099), e um **FLOOR sem extrapolação**
(iters medidas + o resto ao ÚLTIMO t_busca medido = crescimento ZERO — piso, pois
o custo AINDA acelerava na última iteração):

| config (D=10) | restarts/raw | t_busca@109→último | **FLOOR** | projeção (linear) |
|---|---|---|---|---|
| cheio (paper) | 50 / 10000 | 1051 s | ≫ | centenas de h |
| 2D/50D | 20 / 500 | 150→867 s | **47 h** | ~255 h |
| **1D/50D ⟵ shipado** | **10 / 500** | **101→567 s** | **30 h** | ~147 h |
| 1D/25D | 10 / 250 | 81→295 s | **16 h** | ~62 h |

**🔴 TODO config mede FLOOR > o teto de 12 h.** Ou seja: **NENHUM knob de
restarts/raw defensável fecha as 200 iterações do c154 batch em ~10 h** — a
aquisição n²-dominada no n alto (n até 2099) inviabiliza o alvo. (O erro do meu
1º repasse — "~10–14 h" via *método da razão* — vinha de dividir por uma âncora-
cheia NÃO medida; corrigido: a projeção correta é a integração da própria curva.)

**O que fica shipado: `1D/50D`** (`NUM_RESTARTS_PER_D_BATCH=1`,
`RAW_SAMPLES_PER_D_BATCH=50` = 10/500 em D=10 ≈ **default BoTorch 10/512**). É a
**MAIOR redução DEFENSÁVEL** (o default da própria lib, ~10× mais barato/optimize_acqf
que o cheio): sob o teto de 12 h (DI-35.5) ele **avança o MÁXIMO no run antes de
truncar** (failed/teto_wall = dado — melhor que o cheio, que trunca ainda mais cedo).
**A ESTRATÉGIA é decisão do AUTOR (D97/D81)** — ver `T9-calibracao_REPASSE.md` D-1:
{aceitar truncado · limitar nº de infills (K_BATCH<200) · redução mais agressiva
(custo de fidelidade) · tirar c154 do roster (T6 D-1b)}.

## 4. Implementação (batch-only, q=1 intocado)

- **`src/c154_jes.py`:** constantes `NUM_RESTARTS_PER_D_BATCH=1`,
  `RAW_SAMPLES_PER_D_BATCH=50` + helper puro `_restarts_raw_for_q(q, D)` (fonte
  ÚNICA: runner + header + teste). Threaded em `_optimize_acqf_restarts(…, q=1)`
  (gen_batch_ic + optimize_acqf), no passo greedy (`q=q`) e no header/params do body.
  **q=1 ⇒ 5D/1000D do paper, byte-idêntico.**
- **`src/c262_qnehvi.py`:** só um **comentário** documentando a decisão medida
  (sem redução; ~2,2 h; MC é dud; RAM é o gargalo). ZERO mudança de comportamento.
- **`tests/test_batch_q10.py`:** classe `TestCalibracaoBatchT9` — trava os valores
  calibrados (c154 1D/50D), a intocabilidade do q=1 (`_restarts_raw_for_q(1,D)==(5D,1000D)`
  em D∈{2,10,12,22,30}), o reduzido em q>1, e a **ausência intencional** de knob no c262.

**PROVA DE REGRESSÃO ①②③④ (o gate central):** re-rodei `main/MMF1/s0` (q=1) em
tempdir p/ os DOIS e comparei contra `data/experiments/main/*`:

| | ① real | ② pop | ③ surrogate | ④ timing (estrut.) |
|---|---|---|---|---|
| c262/MMF1/s0 q=1 | BIT-IDÊNTICO | BIT-IDÊNTICO | BIT-IDÊNTICO (44 410 linhas) | idêntico (só tempo_* wall variam) |
| c154/MMF1/s0 q=1 | BIT-IDÊNTICO | BIT-IDÊNTICO | BIT-IDÊNTICO | idêntico |

⇒ **o caminho do principal está intocado nos dois.**

## 5. Caveats (para o D97 e a torre)

1. **🔴 Confounder q=1×q=10 (D97).** A calibração é do batch (q=10); o principal é
   q=1, INTOCADO. Mas a mudança do c154 batch (1D/50D vs 5D/1000D) é **mudança de
   receita da aquisição** — a fidelidade do batch é diferente do principal. O D97
   avalia o batch como o que é: um sub-estudo do LOTE com aquisição reduzida
   (defensável ≈ default BoTorch) **e provavelmente TRUNCADO pelo teto** (§3).
2. **⚠ D-dependência (knob PER_D).** Calibrado em ZDT4/D=10 (o mais barato). Como o
   knob é PER_D, nos problemas de D alto (MMF16_20 D=20, WFG9 D=22, ZDT1 D=30) o
   mesmo `1D/50D` dá mais restarts/raw (×D) E cada avaliação é mais cara ⇒ **ainda
   mais caro** que os 30–147 h do D=10. O teto de 12 h trunca todos.
3. **🔴 c154 não fecha ~10 h por knob — o teto TRUNCA (não é "estimativa com banda").**
   A projeção pela própria curva medida dá FLOOR ≥ 30 h (1D/50D) / 16 h (1D/25D),
   ambos > o teto de 12 h. Não é incerteza de projeção: é o piso MEDIDO. O run do
   c154 batch será PARCIAL (failed/teto_wall, ~iter 50–80 de 200). Decisão de
   estratégia = autor (D-1 do REPASSE). (Corrige o "~10–14 h" do 1º repasse, que
   usava o método da razão sobre uma âncora-cheia não medida.)
4. **🔴 RAM (reforça D-2).** Um ÚNICO probe c262 cheio foi OOM-killed em n=669 numa
   máquina de 16 GB com ~0,3 GB livres (2 sessões + browser). O batch GP-BO é
   RAM-bound: provisionar por RAM, não por core (M8/A3).

## 6. Definições em aberto (para a torre/autor)
- **Ratificar os NÚMEROS** (§2, §3) e a receita: c262 cheio (sem knob); c154 1D/50D
  (ou 1D/25D). 1 palavra troca a constante.
- **c262 sem hook:** decidi NÃO adicionar knob ao c262 (medido dispensa). Se o autor
  quiser um dial de margem, o lever é NUM_RESTARTS/RAW_SAMPLES (não MC) — ~5 linhas.
- **Doc-sync SPEC/params.json:** o `params.json` do c154 (e §L.11) hoje lista 5D/1000D;
  o batch usa 1D/50D — anotar a receita batch-aware (território da torre).
