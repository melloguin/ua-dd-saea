# R2-c154 — RELATÓRIO DE EXECUÇÃO (narrativa completa p/ a torre de controle)

> **Propósito.** Descreve, passo a passo, TUDO o que a sessão do cartão
> **R2-c154** executou: verificação de ambiente, leitura de contexto, a
> resolução da B9.5, implementação, os pilotos e — o mais importante para o
> veto do autor — **cada comando rodado e o resultado exato**. Companheiro do
> handoff conciso `handoff/R2-c154.md`.
>
> **Data:** 2026-07-18/19 · **Máquina:** Mac (macOS 12.5.1, arm64), env-main
> por caminho completo · **Veredito final: VERDE ✅** (gate objetivo em
> MMF1 e DTLZ2; ZDT1 sob o teto de 8h do piloto — §6; SEM julgamento de
> fidelidade — D97, validação em LOTE do autor).
>
> ⚠ **Sessão em PARALELISMO DE FAIXAS** com a e103/MATLAB na mesma árvore.
> Faixa tocada: `src/c154_jes.py` (novo) · `src/experiment.py` (1 linha) ·
> `tests/test_c154.py` (novo) · `handoff/R2-c154*.md`. **Zero** `.m`,
> `algorithms/**`, `botorch_harness.py`, `accept.py`, artefatos, cards.
> ⛔ **NADA COMMITADO** — instrução explícita do autor para esta janela; o
> trabalho está no working tree aguardando aprovação (§10).

---

## 0. TL;DR

- **Gate `accept.py R2-c154` exit 0** (semente 0): **MMF1 FE=61** · **DTLZ2
  FE=371** — ambos com DoE bit-a-bit (CP-init) e 4 saídas válidas. **ZDT1
  abortou LIMPO** na it 10 pelo teto de 8h (projeção: 97h/semente) — previsto
  pelo cartão, que condicionava o gate do ZDT1 a ele caber no teto (§6).
- **A B9.5 foi RESOLVIDA no piloto, como a D75 manda** — e **não exigiu
  martelo do autor** (é item [IMPL] declarado; §3). Rota (a)
  `random_search` confirmada para produção; rota (b) paper-faithful medida:
  **×17,7 no wall em D=2** (96s → 1.703s), inviável na bateria.
- **1 achado 🔴 que teria derrubado o cartão:** o estimador LB do JES devolve
  **NaN** em bolsões raros e matava o run no `torch.multinomial` da seleção
  de ICs (DTLZ2, it 11, determinístico). **NaN-guard instalado e logando**
  (§17.5): 24 disparos reais no DTLZ2 completo. Detalhe em §5.
- **A curva §17.6:** fit ≈ **n^1,87** (DTLZ2, 0,98s→8,01s em n 131→371) —
  mas no c154 o fit é **coadjuvante**: a **BUSCA é 98,3% do wall**.
- **O JES confirma o rótulo de CURINGA DE CUSTO:** DTLZ2 em **14h37 contra
  2h31 do c262 no mesmo problema/semente — ×5,8**. O dimensionamento da R2
  deve ser feito pelo c154, não pelo c262.
- **Regressão intacta:** R2-00 (stubpy) + R2-c262 + F0-01..04 + preflight
  exit 0; suíte **91 OK (1 skip)** = 82 pré-existentes + 9 novos.
- **Zero mudança no harness R2-00** (cobriu tudo, como no c262).

---

## 1. AMBIENTE (gate bloqueante — antes de tudo)

```
PY -c "import botorch, torch, gpytorch; print(...)"
→ botorch 0.18.1 · torch 2.11.0 · gpytorch 1.15.2                (exit 0)
git log --oneline -8 | grep R2-c262
→ 8d91202 [R2-c262] relatório: +§9 definições em aberto…         (MOLDE ✓)
→ 417f9cf [R2-c262] handoff + relatório de execução…
```
`env_info()` do harness re-verifica a guarda N.2.3 em RUNTIME (fork ⇒
RuntimeError) a cada run. Nenhum `pip install` (D80). ✅

---

## 2. CONTEXTO LIDO (na ordem e SOMENTE o prescrito)

1. `HANDOFF_MESTRE.md` (§10/§11) · **`handoff/R2-c262.md`** (o MOLDE) ·
   `handoff/R2-00-harness.md` (o harness herdado).
2. `claude_code_context/CLAUDE.md` INTEIRO.
3. A linha **R2-c154** de `cards/INDEX.md` (leitura apenas — não marquei).
4. `20_rodada2_botorch/00_contrato_rodada2.md` (N.1) e
   **`alg_c154_jes.md` INTEIRO**.
5. `00_fundacao/01_regras_globais.md` + `03_contrato_export.md` (§17).
6. **`src/c262_qnehvi.py` INTEIRO** (o molde de código) + as APIs do harness
   que o runner consome.
7. Greps pontuais na SPEC: `B9.5` (7 ocorrências — §6.4, D75, S.3, L.11,
   E.1, I.11, §22.6) para confirmar o estado da definição.

**NÃO li** nenhum `alg_*.md` de outro algoritmo (nem o `c262_qnehvi.md` — o
molde é o handoff + o código, como instruído).

---

## 3. A B9.5 — POR QUE NÃO HOUVE PÁRA-E-PERGUNTA

O prompt da sessão dizia: *"a decisão B9.5 que o bundle manda resolver NO
PILOTO — se a B9.5 exigir decisão MINHA, pára-e-pergunta ANTES de rodar o
caro"*. Verifiquei a cadeia de precedência (D83: Anexo S > §22 > Anexo D >
corpo) e a B9.5 **já está fechada**:

- **D75 (Anexo D, vinculante):** *"JES/c154: §6.4 é a DONA; `random_search`
  principal + `nsgaii(100,500)` como checagem de fidelidade; pop-250 morta
  **(fecha a DEF-B9.5)**"*.
- **§6.4 (a dona da receita):** *"**Principal = `random_search_optimizer`**
  (default de produção, barato); **checagem de fidelidade =
  `optimize_with_nsgaii(pop=100, gen=500)`** rodada só no **piloto**, em 1–2
  problemas, para medir o gap (a)vs(b)"*.
- **§O5 (estado das definições):** *"O que resta são itens **[IMPL]/piloto**
  (guards de NaN, **pipeline do JES B9.5**, hazards L4/L5/L8) que o executor
  resolve na implementação/piloto de timing — **não exigem martelo do
  autor**"*.

**Portanto:** a tarefa delegada não era *escolher* a rota (a D75 já escolheu)
— era **implementar as duas e MEDIR o gap**, que é o que fiz. O resultado
está em §5.3 e **confirma a D75 como escrita**. *(Se o piloto tivesse
mostrado o inverso — rota (b) barata —, aí sim eu teria parado e perguntado,
porque contradiria a premissa de custo da decisão.)*

**As DEFINIÇÕES genuinamente novas** que surgiram na implementação (escada de
fallback, likelihood default, NaN-guard, `init_batch_limit`) estão listadas
em §9 para ratificação — nenhuma delas bloqueava o cartão, e todas são
encanamento, não mecanismo.

---

## 4. IMPLEMENTAÇÃO

**`src/c154_jes.py` (novo, ~560 linhas com docstrings).** Molde do
`run_c262`: mesma espinha (pin → env → DEF-L2 → load_doe → laço BO →
`BudgetExhausted` → `write_run_outputs`), com as especificidades do JES.

Reuso deliberado do molde (import direto de `src.c262_qnehvi`), **não cópia**:
- `disable_fused_kernel()` — a chamada de 1 linha que o handoff R2-c262
  mandou replicar (DEF-L2/S.3#9). O teste garante que é a MESMA função.
- `_fit_models()` — a receita de fit é idêntica (D44, `fit_gpytorch_mll` com
  contagem de retries).
- `_WallClockProjector` — o projetor de teto do piloto.

O que é PRÓPRIO do c154:
- `_build_models` — **sem `train_Yvar`** (ruído INFERIDO, B9.x) — a única
  diferença de modelo vs o c262; kernel e Standardize idênticos.
- `_sample_pareto_points_rs` (rota a) / `_sample_pareto_points_nsgaii`
  (rota b) — o pipeline B9.5, com a escada de fallback e a guarda shape≠P.
- `_make_acqf` — box decomposition + `qLBMOJES("LB")` (sem ref externo).
- `_optimize_acqf_restarts` — 5D/1000D do paper + **NaN-guard** (§5).
- `_NaNGuardedAcqfICs` — o embrulho da guarda (§5).
- `uso_path(s)` / `uso_nsgaii(s)` — a materialização do catálogo D91 do c154
  (0 · 1..S · S+1..2S), com validação de faixa.

**`src/experiment.py`** — exatamente **1 linha** (+1 de comentário) em
`_DISPATCH_LOADERS`: `'c154': ('src.c154_jes', 'run_c154', 'botorch')`.
Nada mais foi tocado no arquivo (a faixa mandava só isso).

**`tests/test_c154.py` (novo, 9 testes)** — encanamento leve, pulam limpo sem
o stack R2: identidade com o `seeds.json` (alg_id 10 + catálogo de usos +
sementes re-derivadas direto do numpy, anti-tautologia); constantes da
receita (S=P=10, "LB", 5D/1000D, escada, pop/gen da rota b); modelo por
introspecção (**ruído inferido = `raw_noise.requires_grad`**, Matérn 5/2 ARD,
Standardize); **escada de fallback com mock** (2 degraus falham → 3º passa;
escada esgotada → RuntimeError + guard); DEF-L2 é a mesma função do c262;
rota inválida rejeitada; **NaN-guard** (troca por pior-finito−1, conta fires,
tudo-NaN → piso); linha do dispatch (sem importar torch).

---

## 5. OS PILOTOS (semente 0, LOCAL — nada ao bucket)

### 5.1 Cronologia honesta (incluindo o que deu errado)

| # | Run | Desfecho |
|---|---|---|
| 1 | MMF1 (a) | ❌ `RuntimeError: Can't call numpy() on Tensor that requires grad` — o `random_search_optimizer` avalia o posterior SEM `no_grad`, então `pf` volta com grafo. **Fix:** `.detach()` em ps/pf (1 linha; D86 — solta o grafo). |
| 2 | MMF1 (a) | ✅ FE 61, 129s (com `init_batch_limit=32` herdado do molde). |
| 3 | DTLZ2 (a) | ⏹ interrompido POR MIM na it 5, ao medir 135–155s/iteração: fui investigar se o `init_batch_limit=32` do molde era o gargalo (benchmark em §5.4). |
| 4 | MMF1 (a) | ✅ FE 61, 94s com `init_batch_limit=256`. |
| 5 | MMF1 (b) | ✅ FE 61, 1.287s — o gap da D75. |
| 6 | DTLZ2 (a) | ❌ **it 11: `RuntimeError: probability tensor contains inf, nan or element < 0`** — o achado 🔴 (§5.2). Footer `failed` gravado (D23/D60 funcionando). |
| 7 | diagnóstico | Reprodução determinística do NaN + dissecção (§5.2). |
| 8 | MMF1 (a) e (b) | ✅ re-rodados COM o NaN-guard (96s / 1.703s) — as saídas finais. |
| 9 | DTLZ2 (a) | ✅ **FE 371, 14h37**, 24 disparos do NaN-guard. |
| 10 | ZDT1 (a) | §6 (o teste do teto de 8h). |

*Os runs 2/4/5 foram sobrescritos pelos 8/9 — o que está no disco é o
conjunto final coerente (mesmo código, mesmas guardas).*

### 5.2 🔴 O achado que teria derrubado o cartão

**Sintoma:** DTLZ2, iteração 11, determinístico (reproduzido 2×):
```
File ".../botorch/optim/initializers.py", line 1018, in initialize_q_batch
    idcs = boltzmann_sample(...)
File ".../botorch/utils/sampling.py", line 351, in batched_multinomial
    flat_samples = torch.multinomial(...)
RuntimeError: probability tensor contains either `inf`, `nan` or element < 0
```

**Causa (leitura do fonte oficial + diagnóstico):** o `optimize_acqf` pontua
`raw_samples=1000·D` pontos e escolhe os ICs por **seleção Boltzmann**. O
`boltzmann_sample` tem tratamento para `+inf` (baixa o η num laço) mas
**nenhum para NaN/−inf** — que passam pelo `standardize`, viram peso inválido
e explodem no `torch.multinomial`. A fonte do NaN é a rota **LB** do
estimador: a covariância M×M da distribuição truncada vem de
**moment-matching** (`mom2 − mom1·mom1ᵀ`) e **não é garantidamente PSD**, de
modo que o `torch.logdet` produz NaN mesmo com o jitter fixo de 1e-6 que o
BoTorch adiciona — cujo próprio comentário no fonte diz *"o jitter
provavelmente nem é necessário aqui"*. **É raro:** ~1 ponto em 10⁴; 4.096
Sobol frescos na mesma iteração deram 0 não-finitos.

⚠ O hazard que o card ANTECIPAVA era outro: *"logdet inicial sem jitter
(q=1 mitiga)"* — o termo INICIAL. O que mordeu foi o termo **condicional**.

**Remédio (dentro da minha faixa; NÃO toca a numérica do algoritmo):**
1. Os ICs passam a ser gerados pelo `gen_batch_initial_conditions`
   **OFICIAL** (mesma função que o `optimize_acqf` chamaria), mas com a acqf
   embrulhada em `_NaNGuardedAcqfICs`: valor não-finito → **pior-finito−1**,
   **só na PONTUAÇÃO** dos raw samples. O ponto nunca é escolhido como IC; se
   TUDO for não-finito, o `Ystd==0` do código oficial cai sozinho no fallback
   aleatório. Guard `nan_guard_ics` logado com a contagem.
2. O escolhido é o **argmax NAN-MASKED** dos restarts (guard
   `nan_guard_argmax`); se TODOS os restarts forem não-finitos ⇒ RuntimeError
   pára-e-loga (D81).
3. **A acqf CRUA segue intocada** na otimização L-BFGS e em todos os valores
   exportados/logados — a guarda é de SELEÇÃO, não de numérica.

**Disparos reais no DTLZ2 completo:** 23× `nan_guard_ics` + 1×
`nan_guard_argmax`, em 240 iterações — todos no `.jsonl`, como a §17.5 manda
("cada guarda que definimos loga quando dispara").

### 5.3 O gap (a)×(b) da B9.5 — o dado que a D75 pediu

MMF1, semente 0, mesmo DoE, mesmas sementes D91:

| | rota (a) produção | rota (b) paper-faithful | razão |
|---|---|---|---|
| wall total | **96,4 s** | **1.703,3 s** | **×17,7** |
| estágio de caminhos (S=10) | 21,7 s | 1.633,7 s | **×75** |
| % do wall em caminhos | 26% | **99%** | — |
| fit do GP | 6,8 s | 7,1 s | ×1,0 |
| FE / iters / CP-init | 61 / 41 / ✓ | 61 / 41 / ✓ | = |
| acqf (1ª → última) | 1,541 → 1,053 | 1,295 → **0,079** | — |

**Leitura (medição, não juízo):** a rota (b) resolve os Pareto samples muito
melhor — o ganho de informação **cai uma ordem de grandeza** ao longo do run,
como o paper prevê, contra a queda modesta da rota (a). O preço é ×17,7 **em
D=2**, o caso mais barato do grid. Para 25 problemas × 30 sementes com D até
30, é inviável — exatamente o motivo pelo qual a D75 a reservou à checagem.
**O piloto confirma a D75.**

### 5.4 Benchmark do `init_batch_limit` (por que 256 e não 32)

Config sintética DTLZ2-like (n=131, D=12, M=3), mesma acqf, mesma seed:

| `init_batch_limit` | tempo do `optimize_acqf` | melhor valor da acqf |
|---|---|---|
| 32 (herdado do molde c262) | 125,3 s | 2,4854 |
| 256 | **108,0 s** | **2,4854** |
| 1024 | 107,8 s | 2,4854 |

É chunking de AVALIAÇÃO — **numericamente neutro** (valor idêntico nos 3) —,
então 32→256 poupa ~14% da busca sem alterar nada. Como a busca é 98% do
custo do c154, o ganho é material. RAM folgada. Declarado no jsonl/manifesto.

### 5.5 Comandos e resultados exatos (runs finais)

```
PY -c "…experiment.run('c154','MMF1',0, exp='main')"
→ fe_final 61 · n_iters 41 · cache_hits 0 · cp_init_ok True
  · rs_fallbacks 0 · wall 96,4s (fit 6,8 / busca 85,9 / paths 21,7)
PY scripts/accept.py R2-c154 --alg c154 --problema MMF1 --semente 0
→ [OK] 4 saídas · [OK] FE=61 (esperado 61, D=2) · [OK] DoE bit-a-bit
  >>> VERDE                                                     (exit 0)

PY -c "…run_c154('main','c154b','MMF1',0, rota='b', max_wall_s=14400)"
→ fe_final 61 · n_iters 41 · cp_init_ok True · wall 1.703,3s

PY -c "…experiment.run('c154','DTLZ2',0, exp='main')"
→ fe_final 371 · n_iters 241 · cache_hits 0 · cp_init_ok True
  · rs_fallbacks 0 · wall 52.596s (fit 903 / busca 51.674 / paths 215)
PY scripts/accept.py R2-c154 --alg c154 --problema DTLZ2 --semente 0
→ [OK] 4 saídas · [OK] FE=371 (esperado 371, D=12) · [OK] DoE bit-a-bit
  >>> VERDE                                                     (exit 0)
```

---

## 6. ZDT1 — o teste do teto de 8h

Rodado por ÚLTIMO com `max_wall_s=28800`, como o cartão manda. **O teto
disparou e o run abortou LIMPO na iteração 10** — comportamento projetado,
não falha:

```
PY -c "…experiment.run('c154','ZDT1',0, exp='main', max_wall_s=28800)"
→ ABORTO-LIMPO: projeção de wall-clock estourou o teto do piloto:
  5.514s decorridos + 345.554s projetados > 28.800s (fe=339/929).
  Aborto LIMPO — curva §17.6 parcial no jsonl. A decisão de completar é da
  torre/autor (M7). Pára-e-loga (D81).
→ wall=5.514,8s (1h32)
```

**Como o teto se comporta (para a torre entender o mecanismo):** o projetor
(herdado do molde c262) só projeta depois de **10 amostras** de iteração —
antes disso não aborta. Medi a cadência do ZDT1 antes de deixá-lo correr
(8,2 min na it 2; 9,3 min na it 3) justamente para confirmar que a iteração
11 chegaria **muito** antes das 8h (chegou: 1h32). Se a cadência fosse
~45 min/iteração, o run furaria o teto sem o projetor disparar — **é uma
lacuna real do projetor herdado**, que não morde aqui, mas que a torre pode
querer fechar antes da M8 (bastaria um teste de `elapsed` independente da
projeção). Não mexi: o projetor é código do c262, fora da minha faixa.

**Custo medido (10 iterações, n 329→338):**

| | valor | % do wall |
|---|---|---|
| busca (avaliação da aquisição) | 5.488 s (549 s/iter) | **99,5%** |
| fit do GP | 23,7 s (2,4 s/iter) | 0,4% |
| estágio de caminhos (S=10) | 0,7 s | 0,1% |

⚠ **O expoente do fit NÃO é estimável** com esses 10 pontos: n variou só de
329 a 338 (2,7%), então a regressão log-log devolve ruído (deu −0,32).
Reportar isso como "curva §17.6 do ZDT1" seria desonesto — o que o run mede
é o **custo por iteração em D=30**, não o escalonamento.

**Projeção:** ~97h (4 dias) por semente ⇒ **≈121 dias·core para as 30
sementes só no ZDT1**. Os demais problemas D=22–30 ficam na mesma ordem.

**⚠ O NaN-guard foi muito mais exercitado aqui:** **8 disparos de
`nan_guard_argmax` em 10 iterações** (contra 1 em 240 no DTLZ2) e **zero** de
`nan_guard_ics`. Leitura: em D=30 a pontuação dos raw samples vai bem, mas o
**L-BFGS empurra os restarts para dentro da região degenerada** do estimador
LB — em 8 de 10 iterações pelo menos um dos 150 restarts voltou não-finito.
**Sem a guarda, o ZDT1 do c154 seria praticamente irrodável.** Isso eleva a
prioridade do item 1 das DEFINIÇÕES EM ABERTO (§9).

**Saídas no disco:** SÓ o `.jsonl` (41 recs: header + 10 timing + 10 decision
+ 10 acqf-warnings + 8 guards + o evento de aborto + footer `failed`). O
`write_run_outputs` nunca roda no aborto ⇒ **não há parquets órfãos nem
manifesto `ok` mentiroso** — exatamente o que o cartão pediu ("preserve a
curva parcial e pára-e-loga").

**A decisão de completar é da torre/autor no M7** (D81 — eu não decido
orçamento). Opções: (a) rodar sem teto na VM (~4 dias·core, paralelo por
semente); (b) aceitar o corte e documentar; (c) reduzir `raw_samples` (desvio
do paper, mediria-se o gap).

---

## 7. AUDITORIA pyarrow

| | ① real | ② pop | ③ surrogate | timing | jsonl |
|---|---|---|---|---|---|
| MMF1 (a) | 61 (21+40) | 1.702 / 42 ger | 410 = 41×10 | 41 pts | 86 recs |
| MMF1 (b) | 61 (21+40) | 1.702 / 42 ger | 410 = 41×10 | 41 pts | 85 recs |
| DTLZ2 (a) | 371 (131+240) | 60.622 / 242 ger | 14.460 = 241×60 | 241 pts | 750 recs |

Em todos: `solution_id` único ✓ · x/f **float32** ✓ · codec **ZSTD** ✓ ·
③ com μ/σ **finitos e σ>0** ✓ · `pred_tipo='valor'`, `modelo_flag='GP'` ✓ ·
`real_solution_id` preenchido em N−1 linhas (o candidato da iteração cortada
pelo hard-stop fica NULL — correto) · manifesto `status=ok`, FE exato,
`doe_hash` = sidecar, bloco `jes` + `fused_kernel` presentes.

**Sanidade de encanamento** (não é juízo de fidelidade — D97): |μ−f| mediana
nos escolhidos = 0,078 (MMF1-a) · 0,035 (MMF1-b) · 0,031 (DTLZ2).

---

## 8. REGRESSÃO FINAL

```
PY scripts/accept.py F0-01 / F0-02 / F0-03 / F0-04       → exit 0 (4×)
PY scripts/preflight.py                                  → exit 0
PY scripts/accept.py R2-00-harness --alg stubpy …MMF1    → exit 0
PY scripts/accept.py R2-c262 --alg c262 …MMF1            → exit 0
PY -m unittest discover -s tests -t .   → 91 OK (skipped=1)
```
(82 antes desta sessão → 91 com os 9 novos.) **Gates MATLAB NÃO rodados** —
faixa da sessão e103, como instruído.

---

## 9. ⚠ DEFINIÇÕES EM ABERTO — a TORRE deve levantar com o AUTOR

Nenhuma bloqueou o cartão; todas são encanamento (D97 intacto).

1. **NaN-guard do estimador LB (§5.2)** — ratificar. É defensivo e logado,
   mas é código NOSSO no caminho de seleção de ICs de um algoritmo oficial.
   Alternativas se o autor preferir: (i) trocar `estimation_type` para
   `"LB2"` (diagonal, sem `logdet` M×M — mas foge da recomendação do paper);
   (ii) aumentar o jitter (mexe na numérica — eu não faria sem ordem).
2. **Escada de fallback do `RuntimeError`** `(1024,10)→(2048,20)→(4096,40)`
   — definição minha; a L.11 só exige "try/except obrigatório". Zero
   disparos nos 3 runs. Ratificar ou substituir.
3. **Likelihood do ruído inferido** — usei o **default do 0.18.1** (prior
   LogNormal, piso 1e-4). Assimetria deliberada a registrar: o **kernel** usa
   a rota Gamma-legada (herdada do c262/D30) e a **likelihood** o default
   moderno. Ratificar ou uniformizar.
4. **`init_batch_limit=256`** (c154) vs **32** (c262) — divergência
   consciente com benchmark (§5.4). Ratificar; se a torre quiser uniformizar,
   o custo é ~14% da busca do c154.
5. **Token `c154b`** para a rota (b) do piloto — não é config do estudo, não
   entra no grid. Confirmar que a torre não o quer no `runs_matrix`.
6. **Sem seed explícito no `optimize_acqf`** — o catálogo D91 do c154 (0 ·
   1..S · S+1..2S) **não prevê** um uso para isso (o do c262 previa, uso 2).
   Mantive o catálogo à risca: os ICs saem do RNG global, determinístico e
   ancorado nos `manual_seed`. Se a torre quiser paridade com o c262, é uma
   linha no `seeds.json` — mas isso ALTERA o artefato (fora da minha faixa).
7. **Doc-sync da S.3/L.11:** `MatheronPathModel(seed=)` não existe no
   0.18.1 (Achado 2 do handoff).
8. **Custo do c154 na bateria (p/ o M7):** DTLZ2 ≈ 18,3 dias·core/problema
   (30 sementes). O dimensionamento de VM da R2 deve ser feito pelo c154.
   *Alavancas se a torre precisar cortar, em ordem de menor dano:*
   (a) `raw_samples` 1000·D → 500·D (desvio do paper, mediria-se o gap);
   (b) paralelizar por semente (embaraçoso, sem mudar nada);
   (c) reduzir S=10 (mexe no mecanismo — eu NÃO recomendo).

---

## 10. ⛔ PEDIDO DE COMMIT (nada foi commitado — aguarda aprovação do autor)

`git status` ao fim da sessão (working tree sobre o commit-base `14b362c`,
branch `experiment/definitive_algorythms`):
```
 M src/experiment.py          (+2 linhas — SÓ a linha do c154 no dispatch)
?? src/c154_jes.py            ?? tests/test_c154.py
?? handoff/R2-c154.md         ?? handoff/R2-c154_RELATORIO-EXECUCAO.md
```
**A lista exata + as 2 mensagens de commit propostas estão na seção
"PEDIDO DE COMMIT" do handoff `R2-c154.md`.** Confirmei com `git diff` que a
única mudança em `src/experiment.py` são as 2 linhas do dispatch — nada mais
do arquivo foi tocado.
