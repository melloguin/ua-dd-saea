# R3-c149 — REPASSE À TORRE (o dossiê completo da sessão, para a instância que gerou o cartão)

> **Para quem lê:** a torre central. Autossuficiente: contexto, cada validação
> RE-EXECUTADA AO VIVO no fechamento, os achados, e — na §6 — as DEFINIÇÕES
> EM ABERTO que a torre DEVE levantar com o autor, incluindo a recomendação
> fundamentada sobre a **DEF-N4** (§7). Companheiros: `handoff/R3-c149.md`
> (o *o quê*) e `R3-c149_RELATORIO-EXECUCAO.md` (o *como*).

**Data da sessão:** 2026-07-22 · **Cartão:** R3-c149 (LBN-MOBO), ONLINE,
`env_main` no Mac (DI-14/RI-08), timebox D-20 de 10 h.
**Veredito: CARTÃO FECHADO — accept exit 0 (13/13) nos 3 problemas, auditar
VERDE ×3, provas caras verdes, regressão completa verde, commits [R3-c149].
O teto de 8 h do ZDT1 NÃO disparou (3,37 h). Recomendação DEF-N4: FICA (§7).**
**Fidelidade NÃO julgada** (D97 — validação manual do autor; números-guia no
handoff).

---

## 1. Resposta direta: o que foi RODADO para provar?

| # | Comando | Resultado |
|---|---|---|
| 1 | `run_c149('main','c149','MMF1',0)` | `fe_final=61` (=31·2−1 EXATO), 40 ger, `status=ok`, wall 240,3 s |
| 2 | `run_c149('main','c149','DTLZ2',0)` | `fe_final=371` (=31·12−1), 240 ger, `status=ok`, wall 2.636,4 s |
| 3 | `run_c149('main','c149','ZDT1',0, teto_s=8*3600)` | `fe_final=929` (=31·30−1), 600 ger, `status=ok`, **`motivo_parada='orcamento'`** (o teto de 8 h NÃO disparou), wall **12.118,5 s = 3,37 h** |
| 4 | `accept.py R3-c149 --alg c149 --problema {MMF1,DTLZ2,ZDT1} --semente 0` | **exit 0 nos 3, 13/13 checks cada** |
| 5 | `auditar.py c149 {MMF1,DTLZ2,ZDT1} 0` | **VERDE ×3** (exit 0) |
| 6 | `C149_SLOW=1 unittest tests.test_c149.TestRunsCompletos` | **2 OK em 936,1 s** — determinismo bit-a-bit (2 runs MMF1 ⇒ ① idêntica) **e** invariante §3.1 (① com sonda k=2 ≡ ① com k=10⁹) |
| 7 | `unittest discover` + `preflight.py` + accept {F0×4, R3-00×2, R3-c122} | **267 OK (5 skip)** — era 247, +20 do c149 · preflight exit 0 · TODOS os gates exit 0 (re-executados no fechamento, 2026-07-22 ~13:50) |

## 2. O timebox D-20 (a razão de ser do cartão)

- Checkpoint das 5 h: **loop MMF1 ponta-a-ponta VERDE em ~2 h de sessão** —
  a premissa de risco ("reconstruir o loop é o maior risco de fidelidade do
  R3") se materializou BEM MENOR que o previsto, porque (i) o notebook do
  loop EXISTE no repo (como o D78 já suspeitava: "mais fácil que a SPEC
  dizia") e (ii) o harness R3-00 + o molde c122 removeram toda a
  infraestrutura da equação.
- Total da sessão: ~6 h de trabalho (das quais ~4 h de pilotos rodando
  dedicados) — DENTRO do timebox de 10 h, sem sacrifício de fidelidade.

## 3. Achados estruturais da sessão (decisões que a torre precisa conhecer)

### 3.1 Semente do NSGA-II da aquisição: artefato × SPEC em conflito — resolvido por autoconsistência
`seeds.json:offset_D22_hardcoded.c149` manda `+1000·s` sobre os "seeds
internos do NSGA-II" — o seed stock é o ÍNDICE DE RUN (`NSGA2_seed ∈
range(Batch/1000)`), que no q=1 é ≡0 ⇒ seed CONSTANTE por iteração. A SPEC
§22.4·3.4 manda `seed=h(s,iter,run)` (por iteração, via helper). **Provado na
sessão: a leitura por-iteração é a única em que o dedup D89 converge** — com
seed constante, um cache-hit repõe exatamente o mesmo estado (treino não
cresce + mesmo init per-net + mesma aquisição) ⇒ o MESMO candidato para
sempre ⇒ livelock até o cap. Implementado por-iteração (precedência D83:
SPEC > artifacts). **Ação da torre: sincronizar o `offset_D22_hardcoded` do
seeds.json** (e o rótulo STALE "Generator(PCG64) do DoE" do uso 2 — o DoE
não se gera desde D87).

### 3.2 PM `prob_var`: a nota SPEC:722 é factualmente incorreta — autor já decidiu
Medido no env_main: pymoo 0.6.2 usa `min(0.5, 1/n_var)`; não há "1/30"
literal no repo (que chama `NSGA2(pop_size=1000)` sem operadores). **O autor
cravou nesta sessão (2026-07-22): default do pymoo (1/D)** — 0,5/D=2,
1/12/D=12, 1/30/D=30. Registrado em `params.nsga2_acq.pm` dos manifestos.
**Ação da torre: reescrever a nota da SPEC:714/722** (o "1/30 hard-coded
(não 1/D): hazard se D≠30" descreve o default avaliado em D=30 como se fosse
literal de código).

### 3.3 `write_run_outputs` carimba `status='ok'` hard-coded — o c122 herda o bug; o c149 o contorna
O runner do c149 REESCREVE o manifesto com `failed`+`motivo_parada` no aborto
(teto/cache-cap) e acrescenta `motivo_parada='orcamento'` no fim natural. O
**c122 tem a contradição viva**: o docstring do `run_c122` promete manifesto
`failed`+`motivo_parada='teto_wall'`, mas o código não reescreve — um aborto
por teto do c122 sairia com manifesto `ok` (a rede que segura é o
`fe_final != maxfe` do `is_run_done`). **Ação sugerida: ou um kwarg
`status=` no `write_run_outputs` (1 linha, M7), ou replicar o contorno do
c149 no c122.**

### 3.4 `emit_sonda_block` não aceita as colunas C3 — carimbo no runner
Os μ/σ da sonda do c149 são DES-padronizados (cru) e os params do z-score
pertencem a toda linha (DEF-C3); o helper não tem como declará-los ⇒
`_stamp_c3_sonda` completa as linhas do buffer após cada bloco. Pego pelo
gate novo (o `check_r3_c149` cobre TODAS as colunas C1/C3 — o do c122 só
olhava `mu_0`, cobertura ilusória descoberta na recon adversarial). **Ação
sugerida (M7): kwargs C3 opcionais no `emit_sonda_block`.**

### 3.5 Desempate do HVI-greedy: σ² agregada EM Z (escolha declarada desta sessão)
O D96 fixa "maior σ² agregada" sem fixar o espaço. Somar σ² NATIVA deixaria
o objetivo de maior escala dominar o desempate — exatamente a degenerescência
que o D96 mata na normalização do HVI. Implementado EM Z (escala-neutra),
declarado no `sigma_dict`. **A torre deve ratificar (ou vetar) com o autor.**

## 4. Validação consolidada (auditoria pyarrow dos 3 runs)

| Verificação | MMF1 | DTLZ2 | ZDT1 |
|---|---|---|---|
| ① linhas (=31D−1) | 61 | 371 | 929 |
| ① fases init/opt | 21/40 ✓ | 131/240 ✓ | 329/600 ✓ |
| ③ blocos sonda (×2000, ordem do artefato — accept check 6) | 21 ✓ | 121 ✓ | 301 ✓ |
| ③ linhas de busca (pop final da aquisição, DEF-C2) | 40.000 | 240.000 | 600.000 |
| ③ `mu_{M−1}` preenchido na sonda (fix `[:, :M]` NO DADO) | ✓ | ✓ (M=3!) | ✓ |
| ③ `fe_treino_max` nulos · `real_solution_id` NULL na sonda | 0 · ✓ | 0 · ✓ | 0 · ✓ |
| ③ q=1: EXATAMENTE 1 escolhido/geração | ✓ 40/40 | ✓ 240/240 | ✓ 600/600 |
| ③ C3 (espaco='cru' + zscore + params) em TODAS as linhas | ✓ | ✓ | ✓ |
| ④ nulos nas 4 colunas de tempo | 0 | 0 | 0 |
| ⑤ timing (5 chaves) + sigma_dict (10) + bloco sonda c/ regime | ✓ | ✓ | ✓ |
| cache-hits · clamps σ²<0 | 0 · 0 | 0 · 0 | 0 · 0 |

Provas caras (`C149_SLOW=1`, molde c122 — 4 runs MMF1 em data_root
temporário): **determinismo bit-a-bit** (2 runs da mesma semente ⇒ ①
idêntica em `to_pydict()`) e **não-perturbação §3.1** (① com k=2 ≡ ① com
k=10⁹) — **2 OK em 936,1 s** (§1 linha 6). Nota: durante estas provas os
pilotos já estavam FECHADOS — nenhum wall oficial foi medido sob disputa.

## 5. Custo medido (o insumo do M7/M8)

| Run | wall | s/ger | fit% | busca% | sonda |
|---|---|---|---|---|---|
| MMF1 | 240 s | 6,0 | 18 | 80 | 0,5 s |
| DTLZ2 | 2.636 s | 11,0 | 52 | 47 | 2,5 s |
| ZDT1 | 12.119 s | 20,2 | 70 | 30 | 6,0 s |

- **A estrutura de custo é a narrativa M.11 em dados:** a busca (NSGA-II
  pop 1000×100 ger sobre o ensemble) é ~constante/geração (~5–6 s); o fit
  cresce ~LINEAR em n (60 ép × n/10 batches × K=10) — sem parede O(n³).
  A curva `(n_acumulado, tempo_fit_s)` está na ④ dos 3 runs.
- **ZDT1 = 3,37 h < 8 h**: o "curinga de custo do M7" coube com 58% de
  folga, medido com máquina DEDICADA (lição c122 §6 aplicada).
- Dimensionamento M8 (30 sementes): ZDT1 domina — ~101 h·core por
  problema-D30; paraleliza por semente (decisão do M7).

## 6. 🔴 DEFINIÇÕES EM ABERTO — a torre DEVE levantar com o autor

1. **Ratificar o desempate σ²-em-z do HVI-greedy** (§3.5) — 1 frase no D96.
2. **Doc-sync da nota PM prob_var** (§3.2) — SPEC:714/722; a decisão do
   autor já existe, falta o texto normativo.
3. **Sincronizar seeds.json** (§3.1): `offset_D22_hardcoded.c149` (a metade
   NSGA-II) + rótulo do uso 2. Sem isso, o próximo leitor reencontra o
   conflito.
4. **`write_run_outputs(status=)`** (§3.3) — decisão de infra (M7); o c122
   está exposto.
5. **C3 no `emit_sonda_block`** (§3.4) — infra (M7); qualquer futuro config
   com espaço transformado + sonda re-herda a lacuna.
6. **Fila de outras mãos:** julgamento de fidelidade D97 (autor, em lote —
   números-guia no handoff); `cards/INDEX.md` (torre).

## 7. Recomendação fundamentada sobre a DEF-N4 (o c149 fica ou sai?)

**RECOMENDAÇÃO: FICA.** Os argumentos, na ordem do que a sessão PROVOU:

1. **O risco que motivava o drop morreu.** A D-20 timeboxou o cartão porque
   "reconstruir o loop" era o maior risco de fidelidade do R3. A
   reconstrução fechou EM SESSÃO, com gate verde, mapeamento peça-a-peça
   auditável (handoff §reconstrução) e âncora de arquitetura (13.452 params)
   coberta por teste. O custo já foi pago.
2. **O c149 é o ÚNICO representante online da família BNN/ensemble** — sem
   ele, a narrativa V-B.3 (a parede O(n³) do GP × o retreino ~linear do
   BNN) perde o espelho online e "repousa no c311" (treed-GP, offline) —
   exatamente o fallback D78 que a SPEC queria evitar.
3. **Custo viável no Mac:** MMF1 4 min · DTLZ2 44 min · ZDT1 3,37 h (42% do
   teto de 8 h, que NÃO disparou) ⇒ as 30 sementes do M8 são dimensionáveis
   por paralelismo de sementes — o c149 deixou de ser o curinga imprevisível
   e virou um custo MEDIDO.
4. **Fidelidade instrumentada:** μ/σ nativos por candidato, val-MSE por
   rede, HVI da escolha, sonda comparável — o c149 entrega exatamente o
   dado de que a tese precisa para o eixo "incerteza epistêmica de ensemble".

Condição honesta: se o julgamento D97 do autor reprovar a reconstrução (é a
ÚNICA peça do R3 sem código-de-referência linha-a-linha executável), o
fallback pré-registrado continua sendo o env_c149_fallback (D78) — não o
drop.

## 8. Onde está cada coisa

- Mapeamento peça-a-peça + decisões de materialização: `handoff/R3-c149.md`
- Narrativa (o que deu errado): `handoff/R3-c149_RELATORIO-EXECUCAO.md`
- Dados: `data/experiments/main/c149/exp_main_c149_{MMF1,DTLZ2,ZDT1}_0.*`
- Reprodução: handoff §como-reproduzir (comandos literais).
