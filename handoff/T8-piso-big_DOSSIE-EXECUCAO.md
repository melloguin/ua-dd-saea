# T8 — piso-big (`treed_media`, alg_id=23) · DOSSIÊ DE EXECUÇÃO

> Relatório detalhado, processo-a-processo, do que a sessão T8 executou, COMO, e
> quais resultados atingiu. Destinado ao **Claude torre central** (que gerou as
> instruções) + ao autor. **Ao final há a seção "DEFINIÇÕES EM ABERTO" — torre: você
> DEVE levantar esses itens com o autor para decidirmos.**

---

## 0. Sumário executivo
`treed_media` é a **ablação do c311 no tier big (50k)** — "o c311 sem os GPs": mesma
árvore/vendor/RVEA-final, mas surrogate = **árvore pura** (`build_surrogates` direto, sem
`addGPs`), predição pela MÉDIA, **σ NULL em toda a ③** (DI-16.1). Entregue: `src/treed_media.py`
+ `tests/test_treed_media.py` + dispatch descomentado + 2 one-liners de fiação de gate
(autorizados pelo autor). **Status: os 4 gates VERDES; 5/5 problemas smoke-verdes; 2 commits
`[T8-piso-big]` (sem push).** Decisões em aberto: 2 reais (política ⑦-no-teto; baseline de
não-perturbação) + 3 confirmações/cosméticas — ver §8.

---

## 1. Objetivo & escopo
- **Cartão:** escrever o runner do `treed_media` (o piso-big do sweep), o teste, descomentar
  1 linha do dispatch. Fundamentos: B15.4 / DI-16.5[P5] / D38 / DI-35.2 / REGISTRO A23.
- **Faixa DISJUNTA da T9** (que edita c262/c154/test_batch_q10). Regras de coexistência git
  honradas: `git diff --cached` vazio antes de cada `add`; nenhum `push`; nenhum `add -A`.
- **Arquivos que a sessão criou/editou** (e SÓ estes): `src/treed_media.py` (novo),
  `tests/test_treed_media.py` (novo), `src/experiment.py` (1 linha — dispatch),
  `scripts/auditar.py` + `experiments.py` (1 linha cada — fiação de gate, AUTORIZADA),
  os 4 handoffs, e os artefatos de smoke em `data/experiments/sweep-big-*/treed_media/**`
  (gitignored).

---

## 2. Método — como cheguei ao design

### 2.1 Fase de entendimento (antes de escrever 1 linha)
1. **Orientação** (grep/ls): localizei o dispatch-stub (`experiment.py:170`), os 2 moldes
   (`c311_tgprmo.py` = o fluxo; `piso_offline.py`/`moead_media` = o precedente média/no-σ),
   os handoffs T7/piso, o REGISTRO.
2. **Workflow paralelo de 5 leitores** (mapeamento dos contratos) — 5 agentes read-only
   mapeando em paralelo: (a) o contrato de dados / schema das 7 camadas + semântica σ/geracao/
   sonda/nd_pos_real; (b) as decisões do REGISTRO (DI-16.1/16.5/16.17/28/35.2/35.5, D38,
   B15.4, D79, D81); (c) o grid sweep-big + `naming.dataset_variant` + o fio T7; (d) os gates
   (auditar/final_eval/portão/preflight) + wiring de env; (e) o molde de teste. Retornaram um
   mapa preciso (assinaturas, colunas, comandos exatos).
3. **Leitura pessoal dos 2 moldes** (código que eu ADAPTO linha-a-linha): `c311_tgprmo.py`
   inteiro + `piso_offline.py` inteiro + os trechos relevantes de `standalone_harness.py`
   (assinaturas dos ~15 helpers).
4. **Verificação da mecânica do vendor** (o que decidiu 3 pontos de projeto):
   - `BaseEA.iterate()` chama SÓ `_next_gen` (nunca `_refresh_population`) ⇒ no RVEA final o
     `_current_gen_count` anda **1..1000** limpo (contador simples, fase única).
   - `treeGP.fit` treina SÓ a árvore; `error_leaves` fica `None`; `treeGP.predict` (stock)
     devolve `(μ_árvore, None)` quando não há GP.
   - `Problem.evaluate(use_surrogate=True)` faz `uncertainity[:,c] = results.uncertainity`
     (Problem.py:853) ⇒ **risco com σ=None**. Decisão: usar o `_patched_predict` do c311
     (μ BYTE-idêntico ao stock; sem GP ⇒ σ TODO NaN, nunca None) por robustez.
   - Datasets big (50k) + sonda existem para os 5 problemas × s42.

### 2.2 Decisões de projeto (com a razão)
| decisão | razão |
|---|---|
| Importar `_import_vendor`/`_build_surrogates`/`_predict_batch`/`_patched_predict`/`_lhs_determinismo`/`_silencio`/`_threads_pinned`/`_max_busca_geracao` de `src.c311_tgprmo` | fonte única (DI-35.2 "IMPORTE-A de lá"); vendor c311 INTOCADO |
| Árvore-só: `_build_surrogates` direto, SEM `addGPs`, SEM o laço de construção | B15.4/DI-35.2 — é a ablação; o mecanismo treed-GP É o c311 |
| `_patched_predict` no RVEA (não o stock) | robustez: garante σ=NaN (nunca None) no evaluate; μ idêntico |
| σ NULL em toda a ③ (recorder e sonda passam `sigma=None`) | DI-16.1 ("o c311 sem GPs"); seleção "mean" não usa σ |
| 1 bloco de sonda (não 2) | modelo ÚNICO (sem retreino build/final) — o cartão crava 1 |
| ④ = 1 linha | treino único (molde piso); a ablação remove o eixo de escalabilidade addGPs |
| ⑦ mesmo no teto (rito piso) | DI-35.5; no treed_media o teto só cai na FINAL (pop válida) — ⚠ ver §8.1 |
| contador geracao 1..1000 | fase única (sem o offset C311-11 do c311) |
| hooks mínimos: só `_next_gen` + `lhs` (sem `_refresh`, sem `predict_batch` no treeGP) | o RVEA final não chama `_refresh`; a sonda chama `_predict_batch` direto |
| uso_id=_default/0 | seeds.json:157 — mesmo `s` p/ numpy e random |

---

## 3. Implementação
- **`src/treed_media.py`** — `run_treed_media(exp, alg, problema, semente, *, data_root,
  enable_bucket=False, teto_s=None, q=1, emitir_sonda=True)`. Espelha `run_c311`/`run_piso_offline`.
  Blocos: `_Recorder` (σ=None, contador simples), `_hooks` (predict→_patched_predict, lhs,
  _next_gen→capture), `_sonda_predict_media` (μ, None), `_null_sonda_geracao`, `_sigma_dict`.
- **`tests/test_treed_media.py`** — 3 camadas: `TestPuros` (sem vendor: identidade, alg_id=23,
  sigma_dict, recorder, null_sonda), `TestGanchos` (@skipUnless GPy: build_surrogates sem GP,
  predict_batch σ-NaN, sonda predict None), `TestRunCompleto` (@skipUnless GPy+TREED_SLOW:
  7 camadas, determinismo, não-perturbação).
- **`src/experiment.py`** — dispatch `'treed_media': ('src.treed_media','run_treed_media','standalone')`
  DESCOMENTADO.
- **`scripts/auditar.py:43`** + **`experiments.py:57`** — `treed_media` nos sets `OFFLINE`/`_OFFLINE`
  (fiação de gate — ver §5).

---

## 4. Validação — log de execução, comando → resultado

### 4.1 Testes unitários
| suíte | env | resultado |
|---|---|---|
| `unittest tests.test_treed_media` | env-main (py3.11) | **8 ok / 7 skip** (vendor+SLOW) — prova importável/env-main-safe |
| `unittest tests.test_treed_media` | env_c311 (py3.8, GPy) | **12 ok / 3 skip** (SLOW) — ganchos do vendor OK |
| `unittest discover -s tests` (SUÍTE COMPLETA) | env-main | **Ran 384 tests · OK (skipped=30)** — antes E depois do descomento (sem regressão) |

### 4.2 GATE 1 — smokes (células REAIS s42, wall medido), TODOS os 5 problemas
| problema (D,M) | dist | wall | status | n_ger | n_final | ② | ④ | sonda |
|---|---|---|---|---|---|---|---|---|
| ZDT4 (10,2) | lhs | 7,37 s | ok | 1000 | 36 | 0 | 1 | 1×20000 |
| ZDT4 (10,2) | mvns | 6,48 s | ok | 1000 | 37 | 0 | 1 | 1×20000 |
| DTLZ2 (12,3) | lhs | 12,10 s | ok | 1000 | 105 | 0 | 1 | 1×20000 |
| ZDT1 (30,2) | lhs | 14,40 s | ok | 1000 | 50 | 0 | 1 | 1×20000 |
| WFG9 (22,2)* | lhs | 8,12 s | ok | 1000 | 46 | 0 | 1 | 1×20000 |
| MMF16_20 (20,3) | lhs | 12,91 s | ok | 1000 | 105 | 0 | 1 | 1×20000 |

Todas: `fe_final == maxfe == 50000`, `cp_init_ok=True`. *WFG9 tem bounds ≠ [0,1] (xu=(2,4)) —
o LHS/RVEA/árvore honram os bounds reais (via `H._bounds`). Muito abaixo do ~1min do c311-big
(a ablação pula o laço `addGPs`, o gargalo O(n³) do GPy).

### 4.3 GATE 2 — auditar + final_eval --check + portão
| comando | ANTES do fix | DEPOIS do fix |
|---|---|---|
| `auditar treed_media ZDT4 42 --exp sweep-big-lhs --regime offline` | VERDE | VERDE |
| `auditar treed_media ZDT4 42 --exp sweep-big-lhs` (sem --regime) | 🔴 2 achados | **VERDE** |
| `final_eval --exp sweep-big-lhs --alg treed_media --problema ZDT4 --semente 42 --check` | VERDE | VERDE |
| `portao --exp sweep-big-lhs --alg treed_media --problema ZDT4 --semente 42` | 🔴 REPROVADO | **✅ VERDE** |

Portão re-rodado em **4 células** pós-fix, todas ✅ VERDE: ZDT4/lhs, ZDT4/mvns, MMF16_20/lhs
(M=3), WFG9/lhs. (accept[T8-piso-big] + auditar + final_eval, 0 vermelhos.)

### 4.4 GATE 3 — determinismo + não-perturbação (`TestRunCompleto`, env_c311, TREED_SLOW=1)
| teste | resultado |
|---|---|
| `test_determinismo_bit_a_bit` | **OK** — 2 runs mesma semente ⇒ ⑦ E ③-busca idênticas (NaN-aware) |
| `test_sonda_NAO_perturba_a_busca` | **OK** — ⑦ e ③-busca idênticas com sonda on/off (`preserve_all_rng`) |
| `test_sete_camadas_e_invariantes` | **OK** — σ NULL busca+sonda; μ preenchido; sonda 20000/geracao NULL; busca 1..1000; ④ `geracao=fit+busca` (DI-13.10) |
| (5 runs de 50k) | 27,6 s |

### 4.5 GATE 4 — suíte + preflight
- Suíte completa: **384 OK / 30 skip** (§4.1). `preflight.py` → **pré-voo OK ✓** (exit 0).
- `_resolve_dispatch('treed_media')` → `run_treed_media`/standalone; ∈ `KNOWN_ALGORITHMS`,
  `VENV_ONLY_ALGS` (roteado p/ `run_in_venv`/env_c311).

---

## 5. A fiação de gate (2 one-liners) — AUTORIZADA pelo autor
O cartão dizia "a torre já fiou … portão/guards". **Na prática, faltavam 2 registros:**
1. `scripts/auditar.py:43` `OFFLINE` NÃO tinha `treed_media` — e `portao.py:78` chama auditar
   SEM `--regime`. Como `offline = (regime=="offline") or alg in OFFLINE`, o run offline era
   auto-classificado como ONLINE ⇒ sonda conferida contra S=2000 e geracao-NULL vira achado ⇒
   portão VERMELHO. **Prova:** com `--regime offline` era VERDE; sem, 2 achados.
2. `experiments.py:57` `_OFFLINE` NÃO tinha `treed_media` ⇒ caía em `DEFAULT_ALGORITHMS` ⇒
   um `experiments.py` sem `--algorithms` tentaria rodá-lo no exp `main` (sem dataset).

O autor AUTORIZOU (resposta em sessão) o T8 a aplicar os 2 one-liners (paralelos aos outros 5
offline configs). Aplicados; portão VERDE. **Ambos os arquivos NÃO são da faixa T9 — sem
colisão.** ⚠ Torre: ciência de que esses 2 registros ficaram fora da fiação original.

---

## 6. Git
- **2 commits `[T8-piso-big]`** (na branch `experiment/definitive_algorythms`):
  - `bfe68a2` — runner + testes + dispatch + fiação de gate (código/testes).
  - `9957ccf` — handoffs.
- **SEM push. SEM `add -A`.** `git diff --cached --name-only` conferido vazio antes de cada
  `add`; apenas os arquivos da faixa T8 foram staged. Artefatos de smoke em `data/experiments`
  são gitignored (não commitados — são reproduzíveis).

---

## 7. O que NÃO está coberto (fronteira do escopo T8)
- A **RODADA-42 das 300 células** (5 problemas × 30 sementes × 2 dists) é da TORRE — o T8
  entrega o CONFIG VALIDADO (runner + gates), não roda a bateria. Smokes cobriram 5/5 problemas
  em s42 (+ mvns no ZDT4) — o mecanismo está validado em todas as dimensões (D∈{10,12,20,22,30},
  M∈{2,3}, bounds unitários e não-unitários, ambas as dists).
- Fidelidade (D97) NÃO é julgada aqui — é manual do autor, a posteriori.

---

## 8. ⭐ DEFINIÇÕES EM ABERTO — TORRE: LEVANTAR COM O AUTOR
> **Instrução ao Claude torre central:** os itens 8.1 e 8.2 são DECISÕES reais do autor;
> 8.3/8.4 são confirmações; 8.5 é cosmético. **Levante 8.1 e 8.2 com o autor antes de fechar
> a validação da torre.**

### 8.1 ⭐ Política da ⑦ no `teto_wall` (DECISÃO)
Segui o **rito do piso/b5** (DI-35.5): ao estourar o teto no RVEA final → `status=failed`,
`motivo=teto_wall`, curva parcial preservada, e a **⑦ SAI da última população RVEA** (válida,
pois no treed_media o teto só pode cair na fase FINAL). **O c311 DIFERE:** OMITE a ⑦ no teto
(usa `_TetoWall`, porque no c311 o teto pode cair na CONSTRUÇÃO, sem pop final válida).
**Decisão do autor:** confirmar o rito-piso (⑦ parcial) OU adotar o rito-c311 (⑦ omitida no
teto)? Não exercitado pelos gates (teto=43200s ≫ ~10s de wall). Declarado em `_sigma_dict["teto"]`.

### 8.2 Baseline de não-perturbação para `treed_media` (DECISÃO / protocolo de congelamento)
O gate permanente `scripts/naoperturbacao.py` compara contra um baseline congelado em
`data/experiments/_baseline_pre_retrofit/`, que NÃO existe para `treed_media` (config novo,
pós-congelamento) — retorna `[--] sem baseline` (RUNBOOK §6-bis: N/A). Provei a não-perturbação
por teste unitário (sonda on/off ⇒ idêntico). **Decisão do autor:** criar um baseline congelado
para `treed_media` (como os outros configs têm) para o gate permanente cobri-lo, ou manter
só-teste (N/A no gate)?

### 8.3 RVEA-final = espelho EXATO do c311-final (CONFIRMAR)
Usei os defaults do RVEA idênticos à fase final do c311 (`n_iterations=10` × `n_gen_per_iter=100`
= 1000 ger; lattice/α/selection default). Assim a ablação isola **só σ** (mesma busca, só sem
GP). Creio ser o contraste pretendido. **Confirmar** (baixo risco).

### 8.4 String do `modelo_flag` (CONFIRMAR — menor)
Escolhi `"treed_media/RVEA-arvore-media"` (não especificado em lugar nenhum; formato paralelo
ao piso `<alg>/<motor>+<surrogate>`). O auditor não confere o valor. **Confirmar ou fixar
convenção.**

### 8.5 Cosmético — `artifacts/envs.json:165-167` `env_c311.algs` ainda é `["c311"]`
Não lista `treed_media` (roteamento é autoritativo via `alg_to_env`, que já diz `env_c311`).
Anexar por consistência (opcional). Arquivo da torre.
