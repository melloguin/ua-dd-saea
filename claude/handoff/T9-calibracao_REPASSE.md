# T9-calibracao — REPASSE À TORRE: os NÚMEROS que o autor ratifica

> Complemento de `handoff/T9-calibracao.md` (detalhe técnico completo lá).
> Cartão T9 / DI-35.1: calibrar POR MEDIÇÃO o custo batch (q=10) de c262 e c154
> p/ ~10 h/run. **A TABELA abaixo é o entregável central — o autor ratifica os
> NÚMEROS.** Nada aqui foi decidido sozinho: são medições + recomendação.

---

## D-0 · 🔑 A TABELA (knob → t/iter → projeção) — o entregável

Tudo em ZDT4/42 (D=10, M=2), q=10, **medido LIMPO** (1 core, serial, sem contenção,
tempdir). Projeção das 200 iterações (n=109…2099).

### c262 (qNEHVI)
| config | restarts/raw/MC | t_busca @n=109 | @n≈499 | **projeção 200 it** |
|---|---|---|---|---|
| **CHEIO (paper) ⟵ mantido** | 10 / 512 / 128 | ~5 s | ~19 s | **~2,2 h** (1,9–2,7 h) |
| MC=64 | 10 / 512 / 64 | ~4 s | ~20 s | ~2,1 h |
| MC=32 | 10 / 512 / 32 | ~4 s | ~13 s | ~1,5 h |
| MC=16 | 10 / 512 / 16 | ~4 s | ~17 s | ~1,7 h |

→ **c262: SEM redução.** ~2,2 h cheio << 10 h alvo << 12 h teto. `MC_SAMPLES` é
um DUD (não muda o custo). O "~56 h" do T6 era contenção/OOM, não a receita.

### c154 (JES) — 🔴 ~10 h COMPLETO é INVIÁVEL; o teto TRUNCA
Projeção pela **PRÓPRIA curva medida** (200 it, n→2099) + **FLOOR** sem extrapolação
(iters medidas + o resto ao ÚLTIMO t_busca — crescimento ZERO, um piso):

| config (D=10) | restarts/raw | t_busca 109→último | **FLOOR** | proj. linear |
|---|---|---|---|---|
| CHEIO (paper) | 50 / 10000 | 1051 s (só it 1) | ≫ | centenas de h |
| 2D/50D | 20 / 500 | 150→867 s | 47 h | ~255 h |
| **1D/50D ⟵ shipado** | **10 / 500** | **101→567 s** | **30 h** | ~147 h |
| 1D/25D | 10 / 250 | 81→295 s | 16 h | ~62 h |

→ **TODO FLOOR > o teto de 12 h** ⇒ NENHUM knob defensável de restarts/raw fecha as
200 iters do c154 batch em ~10 h (aquisição JES-LB ~n^1,6, sem prune de baseline).
Shipado **`1D/50D`** (`NUM_RESTARTS_PER_D_BATCH=1`, `RAW_SAMPLES_PER_D_BATCH=50`
= 10/500 ≈ default BoTorch 10/512): a MAIOR redução defensável — o teto de 12 h
(DI-35.5) **trunca** o run (parcial, ~iter 50–80). **A estratégia é decisão do autor
(D-1).** ⚠ Correção honesta: meu 1º "~10–14 h" usava o *método da razão* sobre uma
âncora-cheia NÃO medida — errado; a revisão adversária pegou. A projeção correta é
a integração da própria curva (acima).

---

## D-1 · Decisões que precisam do autor (D97/D81 — NÃO decidi sozinho)

1. **c262 = receita CHEIA (sem knob).** Medido ~2,2 h << 10 h ⇒ dispensa redução
   (reduzir só baixaria qualidade). Ratifica?
2. **🔑 c154 — a ESTRATÉGIA (nenhum knob defensável fecha ~10 h; ver D-0):**
   (a) **aceitar o batch TRUNCADO pelo teto de 12 h** (parcial ~iter 50–80; alinhado
       com o T6 já ter DEFERIDO o smoke do c154) — o `1D/50D` shipado já maximiza o
       alcance; nada mais a fazer.
   (b) **limitar o nº de infills** (K_BATCH<200 só p/ o c154, p/ COMPLETAR sob 12 h) —
       muda o contrato de FE do batch (11D−1+200q); território da torre.
   (c) **redução mais agressiva** (< 1D/25D, ou menos amostras de Pareto S) — re-medir
       até fechar; custo de fidelidade (abaixo do default da lib).
   (d) **tirar o c154 do roster do batch** (T6 D-1b) — o sub-estudo do LOTE mantém
       resposta com c149/e81/sobol_batch + c262.
   Recomendação da torre: **(a) ou (d)**. `1D/50D` shipado é a melhor redução defensável
   sob qualquer escolha; trocar valor/estratégia = 1 constante + 1 assert.
3. **c262 sem hook de dial.** Não adicionei knob ao c262 (medido dispensa). Lever de
   margem, se um dia: NUM_RESTARTS/RAW_SAMPLES (não MC) — ~5 linhas.

---

## D-2 · 🔴 Confounder q=1 × q=10 (para o D97)

O caminho **q=1 (principal) fica INTOCADO** — prova de regressão ①②③④ BIT-A-BIT
(c262 e c154, main/MMF1/s0). Mas o batch do c154 passa a rodar `1D/50D` em vez de
`5D/1000D` do paper: **é mudança de receita da AQUISIÇÃO**, só no batch. O D97 avalia
o batch pelo que ele é — um sub-estudo do LOTE com aquisição reduzida (defensável,
≈ default da lib) — e o principal pela receita cheia. **São fidelidades distintas;
o autor ratifica a do batch.** (O c262 batch mantém a receita cheia → sem confounder.)

## D-3 · ⚠ D-dependência do knob c154 (calibrado em D=10)

O knob é PER_D; calibrado em ZDT4/D=10. Nos problemas de D alto (MMF16_20 D=20,
WFG9 D=22, ZDT1 D=30) o mesmo `1D/50D` custa MAIS (×D restarts/raw + avaliação mais
cara) ⇒ pode passar de 10 h e **bater no teto de 12 h** (failed/teto_wall honesto,
aborto=dado — DI-35.5). A calibração garante ~10 h SÓ em ZDT4; o **teto governa** os
demais. Aceitável? (é o mesmo espírito da DI-35.5.)

## D-4 · Método da projeção (e a correção honesta)

O c154 cresce ~n^1,6 (posterior do GP por avaliação, SEM prune de baseline). Projetei
cada config **pela integração da SUA PRÓPRIA curva medida** + um **FLOOR** sem
extrapolação (o resto das iters ao último t_busca medido). O FLOOR é o argumento à
prova de bala: mesmo com crescimento ZERO, 1D/50D = 30 h e 1D/25D = 16 h, ambos > o
teto de 12 h. ⚠ Meu 1º repasse dizia "~10–14 h" via **método da razão** (razão ×
custo-cheio) — mas a âncora-cheia (~80–140 h) NUNCA foi medida (o probe cheio fez só
1 iteração). A revisão adversária (5 agentes) pegou o erro; refiz por integração
direta. **Lição registrada: a razão só vale se a curva-cheia for medida — não era.**

## D-5 · 🔴 RAM (reforça D-2 do T6) — insumo M8/A3

Um ÚNICO probe c262 cheio foi **OOM-killed em n=669** (16 GB, ~0,3 GB livres). O batch
GP-BO é RAM-bound: **provisionar por RAM, não por core** (~1 run c262/c154 por 4 GB).
Não é bug — é dimensionamento (M8).

## D-6 · Execução da torre (pós-ratificação)
- Doc-sync: `params.json`/§L.11 do c154 (batch-aware 1D/50D). Território da torre.
- (Se trocar p/ 1D/25D) editar 2 constantes + 1 assert.

---

**T9 FECHADO — c262 medido ~2,2 h (receita cheia, SEM knob, gargalo é RAM); c154 NÃO
fecha ~10 h com knob defensável (FLOOR ≥ 30 h em `1D/50D` > teto 12 h ⇒ run parcial/
truncado); shipei `1D/50D` (maior redução defensável, ≈ default BoTorch) e ESCALO a
estratégia (truncar / limitar-infills / agressivo / drop) ao autor (D97/D81). Aguardo
ratificação dos NÚMEROS e a validação da torre.**
