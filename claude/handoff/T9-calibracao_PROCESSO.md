# T9-calibracao — RELATÓRIO DETALHADO DO PROCESSO (para a torre/autor)

> Narrativa completa e auto-contida da execução do cartão T9, para a instância que
> gerou as instruções entender EXATAMENTE o que foi feito, como, e com quais números.
> Companheiro dos 3 handoffs: `T9-calibracao.md` (técnico), `_RELATORIO.md` (execução
> enxuta), `_REPASSE.md` (a tabela + as decisões do autor). Este arquivo é o
> "diário de bordo" completo. Commit: `b8a9f90` [T9-calibracao].

---

## 0. O cartão e o que ele pedia

**T9 (DI-35.1):** calibrar POR MEDIÇÃO o custo da aquisição batch (q=10) de **c262**
(qNEHVI) e **c154** (JES) para **~10 h/run** ("o ponto ótimo do tradeoff tempo×qualidade"
do autor; aceitar 8–12 h). Método pedido: probes curtos → projeção com o crescimento
do custo em n → valores que projetem ~10 h → ratificação com números. Batch-only (o
principal q=1 fica intocado, com prova de regressão bit-a-bit). Entregável central: a
TABELA knob→t/iter→projeção. Caveat obrigatório para o D97: o confounder q=1 × q=10.

**Arquivos que eu podia tocar (os ÚNICOS):** `src/c262_qnehvi.py`, `src/c154_jes.py`,
`tests/test_batch_q10.py`, `handoff/T9-calibracao*`. Coexistência com a sessão T8
(faixas disjuntas). **Respeitado:** só esses arquivos mudaram (git confirma).

---

## 1. Infraestrutura de medição (como eu medi — reprodutível)

Todos os probes: **ZDT4/42** (D=10, M=2 — a célula do smoke T6), **q=10**, no
`env_main` (`.../mestrado_experimentos_dissertacao`, py3.11.9, **botorch 0.18.1**),
**1 core** (`OMP/MKL/OPENBLAS/NUMEXPR=1` + `torch.set_num_threads(1)` do `pin_runtime`),
e **SEMPRE serial** — 2 probes ao mesmo tempo falseiam o t/iter, que É o entregável.

Ferramentas que escrevi (em scratchpad, **NÃO** tocam `src/`):
- `probe.py` — patcha `budget.K_BATCH` (cap de iterações: `maxfe = 11D−1 + K·q`) e as
  constantes de módulo do runner (monkeypatch em memória), roda o runner **REAL** num
  **TEMPDIR** (`doe`/`sonda` symlink p/ `data/`, saídas fora de `data/`), e extrai a
  curva por iteração do `.jsonl` (`tempo_busca_s`, `tempo_fit_s`, `t_paths_s`, ts).
- `sweep.sh` — fila serial hardened (captura stderr, sem `set -e`, loga RAM, faz
  rescue de `.jsonl` parcial em caso de OOM).
- `analyze.py` — projeção das 200 iterações (n=109…2099) integrando a própria curva
  medida (busca power/linear + fit + overhead) e um FLOOR sem extrapolação.
- `regression.py` — a prova ①②③④ q=1 bit-a-bit contra o disco.

**Por que TEMPDIR + 1 core:** o cartão exige "probes SEMPRE em tempdir (nunca data/)"
e "1 core/probe (D79)". A régua do timing só vale sem contenção.

---

## 2. Achado que reenquadrou o cartão: os números do T6 eram CONTENÇÃO

O repasse T6 dizia c262 ~56 h e c154 ~100 h. Achei os artefatos do smoke T6 em
`/private/tmp/...`: o "56 h" veio do **projetor embutido** rodando **os 4 configs em
paralelo + swap** (o c262 do T6 foi OOM-killed em fe=209). **Medido LIMPO e serial, o
custo real é muito diferente** — daí a necessidade de re-medir do zero.

---

## 3. Execução, etapa por etapa (ordem cronológica + resultados)

### 3.1 Reconhecimento
Li os 2 runners inteiros, `experiment.py`/`budget.py`/`botorch_harness` (load_doe/
load_sonda/pin_runtime), `envs.json`, os handoffs T6, o REGISTRO A23/DI-35.1. Confirmei
os alvos da regressão no disco (`data/experiments/main/c{262,154}/…MMF1_0.*`, semente 0).

### 3.2 Harness + smoke de pipeline
`SMOKE_c262` (3 iters): validou tudo — `maxfe=139 = 11·10−1 + 3·10` (o cap K_BATCH
funciona), o knob aparece no header, a curva bate com o perfil cheio. ✅ **0,6 min.**

### 3.3 c262 — sweep de MC_SAMPLES (Fase A)
MC ∈ {128, 64, 32, 16}, 40 iters cada. **RESULTADO: `MC_SAMPLES` é um DUD.** `t_busca`
em n≈499 fica ~13–23 s em TODOS — reduzir MC **não muda o custo** (o gargalo é o
particionamento do baseline, não a amostragem MC). Contraria a hipótese D-1 ("MC 128→32").
Tempos: 10,8 / 10,4 / 9,6 / 9,6 min. ✅

### 3.4 c262 — deep da receita cheia (Fase B)
Receita cheia (10/512/128), 100 iters pedidas. Rodou LIMPO de n=109 a **n=669 (57
iters)** e foi **OOM-killed** (16 GB, ~0,3 GB livres). **É a prova viva do D-2** (batch
GP-BO é RAM-bound). Os 57 iters limpos bastaram. **Projeção componente-a-componente:**
busca ~1,6 h (p≈0,54, sub-linear) + fit ~0,6 h (p≈2,17) + overhead ~0 = **~2,2 h**
(faixa 1,9–2,7 h). 🔴 **~17 min até o OOM.**
> **DECISÃO MEDIDA:** ~2,2 h << 10 h alvo << 12 h teto ⇒ **c262 fica com a receita
> CHEIA, SEM knob.** Reduzir só baixaria qualidade. O gargalo é RAM (provisionamento).

### 3.5 c262 — confirmação (runner REAL)
Runner real, empty knob, q=10, 15 iters. Header = 128/10/512 (cheio, como esperado —
c262 sem knob); `t_busca` 5,2→17,3 s (n=109→249) bate com a Fase A. **Wiring OK.** ✅ 3,6 min.

### 3.6 c154 — anchor da receita cheia
Receita cheia (5D/1000D). **it 1 limpa = `t_busca@n=109 = 1051 s`** (~17,5 min só a
primeira iteração). Matei após 1 iter (o caro não se repete — instrução do card). **c154
é genuinamente caro** (não é contenção). Custo cresce ~n^1,6 (aquisição JES-LB, SEM
prune de baseline). 🟡 ~19 min (1 iter).

### 3.7 c154 — bracket (2D/50D · 1D/50D · 1D/25D)
Sweep serial, 14/14/12 iters (n→239). Dados **limpos** (`ts_delta ≈ t_busca` — sem
contenção). Tempos: **131,2 / 74,2 / 47,9 min** (o c154 é caro por iteração — ~4,2 h
só aqui). Curvas: cada config CRESCE dentro do run (ex.: 1D/50D vai de 101 s na it 1 a
567 s na it 14).

### 3.8 🔴 O ERRO e a CORREÇÃO (a parte mais importante deste relatório)
**Meu 1º cálculo projetou 1D/50D em "~10–14 h" pelo *método da razão*** (razão
reduzido/cheio × custo-cheio ~80–140 h). **Estava ERRADO:** a âncora-cheia (~80–140 h)
NUNCA foi medida (o probe cheio fez só 1 iteração). Uma **revisão adversária (workflow
de 5 agentes)** que rodei sobre o meu próprio diff pegou o erro. **Verifiquei
independentemente** integrando a PRÓPRIA curva medida de cada config:

| config (D=10) | FLOOR (sem extrapolação) | projeção linear |
|---|---|---|
| 2D/50D | 47 h | ~255 h |
| **1D/50D** (shipado) | **30 h** | ~147 h |
| 1D/25D | 16 h | ~62 h |

O **FLOOR** é à prova de bala: soma dos t_busca medidos + o resto das 200 iters ao
ÚLTIMO valor medido (crescimento ZERO — um piso, pois o custo AINDA acelerava).
**TODO config mede FLOOR > o teto de 12 h.** ⇒ **~10 h COMPLETO é INVIÁVEL** para o
c154 batch com knob defensável de restarts/raw. Corrigi comentário, handoffs e o método
(integração direta, não razão).
> **Lição registrada:** o método da razão só vale se a curva-cheia for medida; não era.

### 3.9 Implementação (batch-only)
- **`src/c154_jes.py`:** `NUM_RESTARTS_PER_D_BATCH=1`, `RAW_SAMPLES_PER_D_BATCH=50`
  (1D/50D = 10/500 em D=10 ≈ **default do BoTorch, 10/512**) + helper puro
  `_restarts_raw_for_q(q, D)` (fonte ÚNICA: runner + header + teste). Threaded em
  `_optimize_acqf_restarts(…, q=1)` (gen_batch_ic + optimize_acqf), no passo greedy
  (`q=q`) e no header/params. **q=1 ⇒ 5D/1000D do paper, BYTE-IDÊNTICO.**
- **`src/c262_qnehvi.py`:** só **comentário** (decisão medida: sem knob).
- **`tests/test_batch_q10.py`:** classe `TestCalibracaoBatchT9` (5 testes) — valores
  calibrados, q=1 intocado em D∈{2,10,12,22,30}, q>1 reduzido, **WIRING do call site**
  (mock em `optimize_acqf`/`gen_batch_ic` — pega hardcode que ignore o helper), c262 sem knob.

### 3.10 c154 — confirmação (runner REAL)
Runner real, empty knob, q=10. Header = **num_restarts=10 / raw_samples=500** (o batch
1D/50D ATIVO — wiring provado); `t_busca` 100→265 s (n=109→179) bate com o probe. Matei
após 8 iters (o header já provava o wiring; liberei CPU). 🟡 ~27 min.

### 3.11 Gates e commit
Prova de regressão, suíte, preflight, revisão adversária (§4). Commit `b8a9f90`
[T9-calibracao] — só os 6 arquivos meus, **NÃO fiz push** (regra de coexistência).

---

## 4. Está 100% pronto? Que código rodei e qual o resultado?

**A ENGENHARIA está 100% pronta, validada e commitada. O que falta são DECISÕES do
autor — 1 estrutural + ratificações (§5):** a decisão estrutural é a **estratégia do
c154 (DEF-1)**; as ratificações são **DEF-2** (c262 sem knob), **DEF-3** (o valor
`1D/50D`), **DEF-4 — o caveat OBRIGATÓRIO do D97** (confounder q=1×q=10, receita batch
reduzida/truncada) e **DEF-5** (D-dependência). Nenhuma é pendência técnica: são
escolhas de fidelidade que, por D81, eu NÃO tomo sozinho. O código roda, é reversível
e está commitado.

**Código que rodei para validar (re-executado fresco agora):**

| validação | comando | resultado |
|---|---|---|
| **Regressão q=1 ①②③④** | `regression.py` (re-roda main/MMF1/s0 q=1 em tempdir e compara bit-a-bit com `data/experiments/main/*`) | **BIT-IDÊNTICO** nos 2 (c262 + c154): ①real, ②pop, ③surrogate (44 410 linhas) idênticos; ④timing estrutural idêntico (só `tempo_*_s` de wall variam). ✅ |
| **Testes-guarda T9** | `unittest tests.test_batch_q10.TestCalibracaoBatchT9` | **5 OK** (inclui o teste de WIRING do call site). ✅ |
| **Suíte completa** | `unittest discover -s tests` | **389 OK** (30 skip, gated por venv/MATLAB), exit 0. ✅ |
| **Preflight** | `scripts/preflight.py` | **exit 0.** ✅ |
| **Confirmação de wiring** | runner REAL (empty knob, q=10) p/ os 2 | c262 header=128/10/512 (cheio); c154 header=10/500 (batch ativo). ✅ |
| **Revisão adversária** | workflow de 5 agentes sobre o diff | pegou o erro do "~10–14 h" → corrigido por integração direta. ✅ |

**Conclusão:** implementação **completa, testada, bit-a-bit segura no principal, e
commitada**. Os itens abertos são **decisões/ratificações do autor** (§5, DEF-1…DEF-5)
— a estrutural é a estratégia do c154; **inclui a disclosure OBRIGATÓRIA do D97 (DEF-4)**.

---

## 5. 🔑 DEFINIÇÕES EM ABERTO — a torre PRECISA levar ao autor

> **Torre: estas decisões NÃO foram tomadas por mim (D97/D81). Você precisa levantá-las
> com o autor para decidirmos.** A troca de qualquer valor = 1 constante + 1 assert.

### DEF-1 (🔴 a principal) — ESTRATÉGIA do c154 batch
**Medido: NENHUM knob defensável de restarts/raw fecha as 200 iterações do c154 batch
em ~10 h** (FLOOR ≥ 30 h em 1D/50D, ≥ 16 h em 1D/25D — ambos > o teto de 12 h; a
aquisição JES-LB cresce ~n^1,6 sem prune de baseline e domina no n alto). O que fazer?
- **(a) Aceitar o batch TRUNCADO pelo teto de 12 h** (run parcial, ~iter 50–80 de 200;
  `failed/teto_wall` = dado honesto, DI-35.5). Alinhado ao T6 já ter DEFERIDO o c154
  batch. O `1D/50D` shipado já MAXIMIZA o alcance antes de truncar. **Nada mais a fazer.**
- **(b) Limitar o nº de infills** (K_BATCH<200 só p/ o c154, p/ COMPLETAR sob 12 h).
  Muda o contrato de FE do batch (11D−1+200q) — território da torre.
- **(c) Redução mais agressiva** (< 1D/25D, ou menos amostras de Pareto S). Re-medir até
  fechar; custo de fidelidade (abaixo do default da lib).
- **(d) Tirar o c154 do roster do batch** (T6 D-1b). O sub-estudo do LOTE mantém resposta
  com c149/e81/sobol_batch + c262.
- **Recomendação da torre:** (a) ou (d).

### DEF-2 — Ratificar o c262 SEM knob
Medido ~2,2 h (limpo) << 10 h. Recomendo **manter a receita cheia** (reduzir só baixaria
qualidade; MC é dud; o gargalo é RAM). O autor ratifica? (Não adicionei hook de dial ao
c262; se quiser margem futura, o lever é NUM_RESTARTS/RAW_SAMPLES — não MC — ~5 linhas.)

### DEF-3 — Ratificar o valor shipado do c154 (`1D/50D`) OU trocar
Shipei `1D/50D` (≈ default BoTorch) como a MAIOR redução defensável. Se o autor escolher
(c) acima, o valor muda. Ratifica `1D/50D` ou pede outro?

### DEF-4 — Confounder q=1 × q=10 para o D97
O principal q=1 fica INTOCADO (prova bit-a-bit). Mas o c154 batch passa a rodar `1D/50D`
em vez de `5D/1000D` do paper: **é mudança de receita da AQUISIÇÃO, só no batch, e
provavelmente com run TRUNCADO**. O D97 avalia o batch pelo que ele é (sub-estudo do
LOTE, aquisição reduzida ≈ default da lib, possivelmente parcial). O autor ratifica
essa fidelidade do batch como distinta da do principal?

### DEF-5 — D-dependência do knob (calibrado em D=10)
O knob é PER_D; calibrado em ZDT4/D=10 (o mais barato). Nos problemas de D alto
(MMF16_20 D=20, WFG9 D=22, ZDT1 D=30) o `1D/50D` custa AINDA MAIS ⇒ truncam mais cedo
no teto. Aceitável (é o espírito da DI-35.5)?

### DEF-6 — Doc-sync (execução da torre, pós-ratificação)
`params.json` e a §L.11 da SPEC listam o c154 como 5D/1000D sem nota de batch. Anotar a
receita batch-aware (território da torre).

---

## 6. Perfil de RAM (insumo direto do M8/A3)
Um ÚNICO probe c262 CHEIO foi OOM-killed em n=669 (16 GB, ~0,3 GB livres). O batch GP-BO
é **RAM-bound**: provisionar por RAM (~1 run c262/c154 por ~4 GB), não por core. Reforça
o D-2 do T6. Não é bug — é dimensionamento.

---

## 7. Frase de fechamento
**T9 FECHADO — c262 medido ~2,2 h (receita cheia, SEM knob; gargalo é RAM); c154 NÃO
fecha ~10 h com knob defensável (FLOOR ≥ 30 h em `1D/50D` > teto 12 h ⇒ run parcial/
truncado); shipei `1D/50D` (maior redução defensável, ≈ default BoTorch) e ESCALO a
estratégia (truncar / limitar-infills / agressivo / drop) ao autor (D97/D81). Aguardo
ratificação dos NÚMEROS e a validação da torre.**
