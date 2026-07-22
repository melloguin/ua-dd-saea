# R3-e81 — REPASSE À TORRE · DOSSIÊ COMPLETO DA SESSÃO

> **Para quem lê:** a torre central (a instância que montou o cartão). Este
> documento é **autossuficiente**: o veredito, cada comando executado com o seu
> resultado literal, o processo etapa a etapa, os achados, a auditoria dos
> dados, o custo medido — e, na **§8, as DEFINIÇÕES EM ABERTO que a torre DEVE
> levantar com o autor**. Companheiros: `handoff/R3-e81.md` (o *o quê* —
> mapa técnico) e `R3-e81_RELATORIO-EXECUCAO.md` (o *como* — a narrativa).

**Data:** 2026-07-22 · **Cartão:** R3-e81 (qPOTS sobre BoTorch 0.16.1), ONLINE,
`env_e81_qpots` no Mac (DI-14/RI-08) · **Commits:** 3 × `[R3-e81]` no branch
`experiment/definitive_algorythms` (`5bde3db`, `681b0eb`, `7751f5d`).

---

## 0. Resposta direta às três perguntas

**(1) O escopo executável do cartão está 100% pronto?** **Sim.** Todos os
gates que o cartão define estão VERDES e foram **re-executados ao vivo no
fechamento** (§1). O que resta é, por desenho, de **outras mãos**: o
julgamento de fidelidade do autor (D97), a marcação do `cards/INDEX.md`
(torre) e as decisões da §8.

**(2) Rodei código para validar?** Sim — tudo abaixo é execução real, nada é
estimativa. Os comandos e resultados literais estão na §1.

**(3) Há definições em aberto?** **Sim — 10, e duas delas são materiais.**
Estão na §8. As duas que mais importam: **(a)** o kernel que escolhi para a
D30 é a única decisão desta sessão que toca fidelidade e precisa de
ratificação; **(b)** a granularidade da ③-busca do e81, seguindo a mesma regra
do c149, captura **1%–24%** da população da aquisição, contra **100%** no
c149 — a regra é a mesma, o efeito é 100× diferente.

---

## 1. O que foi RODADO para provar (re-executado ao vivo em 2026-07-22 19:10:43)

### 1.1 Os 3 runs-piloto

| # | Comando | Resultado |
|---|---|---|
| 1 | `run_e81('main','e81','MMF1',0)` | `fe_final=61` (**=31·2−1 EXATO**), 40 ger, `status=ok`, `motivo_parada='orcamento'`, wall **10,9 s** |
| 2 | `run_e81('main','e81','DTLZ2',0)` | `fe_final=371` (=31·12−1), 240 ger, `status=ok`, wall **549,0 s** |
| 3 | `run_e81('main','e81','ZDT1',0, teto_s=8*3600)` | `fe_final=929` (=31·30−1), 600 ger, `status=ok`, **`motivo_parada='orcamento'` — o teto de 8 h NÃO disparou**, wall **7.167,7 s = 1,99 h** |

Os três rodaram **em sequência, com a máquina livre** — os walls são limpos
(lição do repasse c122 §6, que alertava para medições sob disputa).

### 1.2 Os gates (saída literal)

```
### 1. accept.py R3-e81 (gate do cartao, 18 checks) ###
  MMF1  -> exit 0 | 18 OK, 0 FAIL
  DTLZ2 -> exit 0 | 18 OK, 0 FAIL
  ZDT1  -> exit 0 | 18 OK, 0 FAIL

### 2. auditar.py (validador permanente da torre) ###
  exit 0 | AUDITORIA e81/MMF1/0: VERDE
  exit 0 | AUDITORIA e81/DTLZ2/0: VERDE
  exit 0 | AUDITORIA e81/ZDT1/0: VERDE

### 3. naoperturbacao.py (gate 1 permanente) ###
  exit 0 | NÃO-PERTURBAÇÃO: 0 verdes · 1 sem baseline · 0 falhas → VERDE

### 4. suite completa + preflight ###
  Ran 293 tests in 16.960s
  OK (skipped=7)
  preflight -> exit 0

### 5. testes do e81 no env PROPRIO (inclui as 2 provas caras) ###
  Ran 21 tests in 39.688s
  OK
```

- **293 testes** — eram **272** antes da sessão; **+21** são do e81.
- `naoperturbacao.py` diz "sem baseline" porque o e81 é config **NOVO** (não há
  baseline pré-retrofit congelado) — é o resultado esperado, e o gate o trata
  como verde.

### 1.3 As duas provas caras (`E81_SLOW=1`)

| prova | o que assere | resultado |
|---|---|---|
| `test_determinismo_bit_a_bit` | 2 runs da MESMA semente em `data_root` distintos ⇒ ① idêntica em `to_pydict()` | **OK** |
| `test_sonda_NAO_perturba_a_busca` | ① com `sonda_k=2` ≡ ① com `sonda_k=10⁹` (só 1ª+última) | **OK** |

A 2ª é o invariante 🔴 §3.1: se o `preserve_all_rng()` em volta do `predict`
falhasse, o Thompson da iteração seguinte mudaria e a ① divergiria.

### 1.4 Não-regressão dos cartões anteriores

Como acrescentei um branch ao `accept.py`, re-rodei **todos** os gates
existentes:

```
  accept F0-01-harness   -> exit 0      accept R3-c122/MMF1  -> exit 0
  accept F0-02-doe       -> exit 0      accept R3-c122/DTLZ2 -> exit 0
  accept F0-03-export    -> exit 0      accept R3-c122/ZDT1  -> exit 0
  accept F0-04-metrica   -> exit 0      accept R3-c149/MMF1  -> exit 0
  accept R3-00-harness/MMF1  -> exit 0  accept R3-c149/DTLZ2 -> exit 0
  accept R3-00-harness/DTLZ2 -> exit 0  accept R3-c149/ZDT1  -> exit 0
```

**12/12 exit 0.** O diff do `accept.py` é **279 inserções / 0 remoções** —
puramente aditivo, nenhum branch existente tocado.

---

## 2. FASE 0 — o gate de ambiente e a TAREFA 0 (D80/D81)

O cartão exigia um gate real, não uma inspeção de `pip list`:

| # | Verificação | Resultado |
|---|---|---|
| 1 | `envs.json:alg_to_env.e81` | `env_e81_qpots` ✓ |
| 2 | Import de cada pin, no env | py **3.11.9 arm64** · torch **2.11.0** · botorch **0.16.1** · gpytorch **1.14.2** · numpy **2.2.6** · pymoo **0.6.1.6** · scipy 1.17.1 · pyarrow 25.0.0 ✓ |
| 3 | Fit BoTorch mínimo | `SingleTaskGP` + `fit_gpytorch_mll` + `posterior()` OK em float64 |
| 4 | **TAREFA 0 — CP-init** | `problems.py` avalia no env e o hash do `init_X()` do `FEBudget` **bate o sidecar do DoE nos 3 problemas** — **3/3 ✅** |
| 5 | Artefatos | DoE + sonda presentes; sonda online = 2000×D ✓ |
| 6 | Suíte no env-main + preflight | **272 OK (5 skip)** · preflight **exit 0** |

Hashes CP-init conferidos: MMF1 `89b8ce4e…` · DTLZ2 `71d3398a…` · ZDT1
`ed4a004a…` — **o pymoo 0.6.1.6 avaliando os problemas é bit-idêntico ao
artefato**, que era exatamente a rede que o cartão pedia (S.6).

**Nota de ambiente:** o `env_e81_qpots` **não tem pandas**. Irrelevante para o
runner (o harness usa pyarrow puro), mas **quebra o `scripts/auditar.py`** se
rodado nesse interpretador (ele chama `.to_pandas()`). Rodei no env-main.
→ §8, item 8.

---

## 3. O processo, etapa a etapa

1. **Gate de ambiente + TAREFA 0** (§2) — 3/3 CP-init verdes.
2. **Leitura obrigatória** na ordem exata do cartão: `claude_code_context/CLAUDE.md`
   → `CONTRATO_DE_DADOS.md` (inteiro) → `00_fundacao/03_contrato_export.md` (§17
   completo) → `30_rodada3_standalone/00_contrato_rodada3.md` → o cartão
   `alg_e81_qpots.md` + o checklist §22.4·3.5 → os repasses c149 e c122 →
   `REGISTRO_DECISOES_IMPLEMENTACAO.md` PARTES A10–A12 (DI-21/22/23).
3. **Recon multi-agente com verificação cética** — 6 leitores paralelos (repo
   vendorizado, molde c149, API do harness, gates, SPEC/artefatos, runners R2)
   + **3 refutadores adversariais** por lente (assinaturas / arquivo:linha /
   contrato). Os refutadores acharam **1 erro acionável e perigoso** e **2
   defeitos de contrato que eu teria herdado do molde**:
   - `transf_params` dentro de `c3=` tem de ser **dict**, não string (§4.2);
   - o `break` do cache-cap do c149 deixa a ④ com NULL (§4.3);
   - `write_run_outputs` não repassa `q` (§4.4).
4. **Verificação bit-a-bit das 3 âncoras** do `anchors.json` contra o vendor:

   | âncora | arquivo:linha | conteúdo REAL | veredito |
   |---|---|---|---|
   | `e81-matern` | `qpots/model_object.py:120` | `model = SingleTaskGP(` | ✓ |
   | `e81-offset1` | `qpots/acquisition.py:219` | `torch.manual_seed(1024 + seed_iter)` | ✓ |
   | `e81-offset2` | `qpots/acquisition.py:366` | `seed=2430,` | ✓ |

   **3/3 conferem**, e viraram teste permanente (`test_ancoras_e81_conferem`).
5. **Smoke do mecanismo ANTES de escrever o runner**: 3 iterações do loop
   canônico, provando que os ganchos capturam draws/front/índice, que o Matérn
   é aplicado, e que `newx ∈ [0,1]^D` com `|lote| == q`.
6. **Implementação** de `src/e81_qpots.py`.
7. **O ZDT1 quebrou** → diagnóstico em 4 eixos → correção do kernel (§4.1).
8. **Gate `check_r3_e81`** (18 checks, ADITIVO antes do catch-all F0-01),
   `tests/test_e81.py` (21 testes), linha do dispatch em `experiment.py`.
9. **Pilotos** MMF1 → DTLZ2 → ZDT1 (teto 8 h), sequenciais.
10. **Validação, auditoria pyarrow, documentação e 3 commits.**

---

## 4. Os achados estruturais

### 4.1 🔴 A D30 "Compartilhado" não é só o *nome* do kernel — e eu quase perguntei a coisa errada

**O que aconteceu.** Implementei o patch Matérn como o cartão escreve
literalmente (*"**Matérn = 1 linha** `covar_module=` (model_object.py:120–124)"*):
`ScaleKernel(MaternKernel(nu=2.5, ard_num_dims=D))`. MMF1 e DTLZ2 rodaram; o
**ZDT1 morreu no primeiro fit**:

```
botorch.exceptions.errors.ModelFittingError: All attempts to fit the model have failed.
```

**O que medi, antes de escalar** (para não perguntar a coisa errada):

| eixo isolado | resultado |
|---|---|
| nugget `1e-12` vs `1e-6` | as **duas** falham ⇒ **não é o nugget** |
| kernel RBF stock (sem patch) | **OK** nos 2 objetivos ⇒ **é o patch** |
| Matérn **sem** `train_Yvar` (ruído inferido) | **OK** ⇒ é Matérn × ruído **FIXO** |
| n-scan do obj 1 (n = 50…329) | 50 ✓, 100 ✓, **150 ✗**, 200 ✓, 250 ✓, 300 ✓, **329 ✗** ⇒ **intermitente, não-monotônico** |
| causa subjacente | `OptimizationWarning: scipy_minimize ... "ABNORMAL"` ⇒ **o L-BFGS-B não converge**; **NÃO** é PSD/Cholesky |

**Cheguei a montar a pergunta de pára-e-loga (D81)** com 4 remédios candidatos
(subir `max_attempts`; re-semear e re-tentar; cair para
`fit_gpytorch_mll_torch`; ou simplesmente abortar). **Era a pergunta errada** —
o problema não era do algoritmo, era da *minha* materialização da D30.

**A resposta estava no próprio repo:**

> A **D30 é marcada "Compartilhado (c262, e81)"** no bundle do e81 — e os DOIS
> runners BoTorch **já aceitos** materializam essa mesma decisão com uma chamada
> só: `covar_module=get_matern_kernel_with_gamma_prior(D)`
> (**`src/c262_qnehvi.py:195`** e **`src/c154_jes.py:247`**), que é
> `ScaleKernel(MaternKernel(nu=2.5, ARD, lengthscale_prior=Gamma(3,6)),
> outputscale_prior=Gamma(2,0.15))`.

Trocado pelo helper, medido:

| problema | Matérn SEM prior | `get_matern_kernel_with_gamma_prior` |
|---|---|---|
| MMF1 (n=21) | OK, OK | OK, OK |
| DTLZ2 (n=131) | OK, OK, OK | OK, OK, OK |
| **ZDT1 (n=329)** | OK, **ModelFittingError** | **OK, OK** |

E o **n-scan de robustez ao longo de TODA a trajetória do ZDT1** (n = 329→929,
os 2 objetivos): **28/28 fits OK, zero falhas**.

**Por que isto é normativo, não estético.** Um Matérn sem prior e um Matérn com
`GammaPrior` são **surrogates diferentes**. Se c262/c154 usam um e o e81 usa
outro sob o rótulo de *uma* decisão, a comparação entre esses configs mede a
diferença de priors, não a diferença de algoritmo — e "Compartilhado" vira
falso no dado.

**Achado de fidelidade colateral, travado por teste:** o default do
`SingleTaskGP` no **BoTorch 0.16.1** é um **`RBFKernel` PURO** — sem
`ScaleKernel`, logo **sem outputscale**. A prosa da SPEC ("RBF ARD default")
está certa quanto ao RBF, mas a ausência do `ScaleKernel` é o detalhe que muda
o que a D30 de fato acrescenta.

→ **§8, item 1 (a única decisão desta sessão que toca fidelidade).**

### 4.2 O kwarg `c3=` do DI-23 exige **dict** — e o próprio teste do DI-23 passa string

As duas rotas de C3 têm formatos **opostos**:
- `_stamp_c3_sonda` (c149) **muta a row já construída** ⇒ **string**;
- `c3=` repassa `**c3` ao `surrogate_row`, que faz o `json.dumps` ⇒ **dict**.

Medido:

```
c3 com DICT   -> {"mu": [0, 0]}          json.loads -> dict
c3 com STRING -> "{\"mu\": [0, 0]}"      json.loads -> str    (precisa de 2 loads)
```

⚠ **`tests/test_di23_harness.py:90-91` passa `json.dumps({...})` dentro de
`c3=`** — e o teste **passa**, porque as asserções (`:94-96`) só olham
`espaco_modelo` e `transf_tipo`, **nunca** `transf_params`. Qualquer config
futuro (b5 / c311 / piso-off) que copie esse teste como exemplo de uso grava a
③ **duplo-encodada em silêncio**. → §8, item 4.

### 4.3 O `break` do cache-cap do c149 deixa a ④ com NULL — e reprovaria o próprio gate

Em `src/c149_lbnmobo.py`: `buf.add_timing(...)` abre a linha da ④ na **:665**,
o `break` do cache-cap está na **:738**, e o `buf.update_timing(...)` só vem na
**:760-762**. Num aborto, a geração fica com `tempo_busca_s` /
`tempo_pred_sonda_s` / `tempo_geracao_s` = **NULL** — o que **reprova o check
`④ timing v5.2.1 completa`** do `accept.py:928-933`. Pior: se a sonda de
cadência rodou nessa geração, o bloco final não roda (guardado por
`ultima_sonda_g != g`) e o `t_snd` medido se perde.

**No e81 a ④ é fechada em `finally`**, então o aborto por teto — que o cartão
trata como **DADO** — produz uma ④ **válida**. → §8, item 5.

### 4.4 `write_run_outputs` não repassa `q` — os runs de `exp=batch` mentiriam

`new_manifest` fixa `q=1` (`manifest.py:45`) e o `write_run_outputs` não o
repassa (`standalone_harness.py:1044-1053`). O `runs_matrix.csv` tem **900
linhas de e81: 750 em `main` (q=1) e 150 em `batch` (q=10)**. O runner carimba
`man["q"]` quando diverge, mas a lacuna é de infra. → §8, item 6.

---

## 5. Auditoria consolidada dos dados (pyarrow, os 3 runs)

| Verificação | MMF1 | DTLZ2 | ZDT1 |
|---|---|---|---|
| ① linhas (=31D−1) | 61 | 371 | 929 |
| ① fases init/opt | 21/40 ✓ | 131/240 ✓ | 329/600 ✓ |
| ② membership (linhas) | 1.660 | 60.360 | 377.700 |
| ③ blocos de sonda (×2000) | 21 | 121 | 301 |
| ③ sonda na ORDEM do artefato (join posicional, R4 regra 5) | ✓ | ✓ | ✓ |
| ③ linhas de busca (front rank-0) | 697 | 68.187 | 18.821 |
| ③ `mu_*` / `sigma_*` nulos | 0 / 0 | 0 / 0 | 0 / 0 |
| ③ `fe_treino_max` nulos | 0 | 0 | 0 |
| ③ sonda com `real_solution_id` NULL | ✓ | ✓ | ✓ |
| ③ C3 `espaco_modelo` em TODAS as linhas | `{cru}` | `{cru}` | `{cru}` |
| ③ `transf_params` decodifica para **dict** (sem duplo-encode) | ✓ | ✓ | ✓ |
| ③ q=1: EXATAMENTE 1 escolhido/geração | 40/40 | 240/240 | 600/600 |
| ④ nulos nas 5 colunas | 0 | 0 | 0 |
| ④ `n_acumulado` = TREINO (monotônico) | 21→60 | 131→370 | 329→928 |
| ⑤ status · motivo_parada | ok · orcamento | ok · orcamento | ok · orcamento |
| ⑤ cache_hits · lotes menores que q · guards `front_1d` | 0 · 0 · 0 | 0 · 0 · 0 | 0 · 0 · 0 |
| ⑤ `sigma_dict` (chaves) · `sonda.regime` | 11 · online | 11 · online | 11 · online |
| ⑥ eventos de decisão · campos DI-10+S.7 ausentes | 40 · nenhum | 240 · nenhum | 600 · nenhum |

⑦ `__final.parquet` **não se aplica** (é só offline — DI-08). Correto.

---

## 6. Custo medido — e a parede está onde não se esperava

| Run | wall | fit% | busca% | sonda% | s/geração |
|---|---|---|---|---|---|
| MMF1 (D=2) | 10,9 s | 22,6 | 37,4 | 11,1 | 0,17 |
| DTLZ2 (D=12) | 549,0 s | 12,0 | **82,2** | 2,3 | 2,18 |
| ZDT1 (D=30) | **7.167,7 s = 1,99 h** | 15,5 | **83,0** | 0,6 | 11,7 |

**A curva de escalabilidade da ④, por regressão log-log:**

| | `tempo_fit_s` | `tempo_busca_s` |
|---|---|---|
| DTLZ2 (n 131→370) | 0,118 → 0,462 s (×3,9) — **n^1,81** | 1,81 → 1,96 s (×1,1) — **n^0,10** |
| ZDT1 (n 329→928) | 0,521 → 3,409 s (×6,5) — **n^2,53** | 9,41 → 10,22 s (×1,1) — **n^0,10** |

**A leitura (um resultado do §17.6).** O `tempo_fit_s` **exibe a parede
O(n³)** — o expoente sobe de n^1,81 (D=12) para **n^2,53** (D=30), convergindo
para o cúbico à medida que n cresce. Mas o fit é só **~15% do wall**. Os **83%**
estão na **busca**, que é **essencialmente PLANA em n (n^0,10)** e explode com
**D**: 1,8 s (D=12, pop=1.200) → 9,4 s (D=30, pop=3.000).

Ou seja: **no qPOTS o gargalo não é o treino, é a aquisição.** O Thompson
sampling exige uma amostra da posterior sobre `pop = 100·D` pontos, a cada uma
das `ngen=10` gerações do NSGA-II, por objetivo; o custo é dominado pela
decomposição da covariância **do lado do TESTE** (3.000×3.000 no ZDT1, exata
porque importar BoTorch eleva `max_cholesky_size` a 4096 — N.2), que **não
depende de n**. Contraste direto e limpo com c238/c262 (parede no treino) e com
c122/c149 (que escapam da parede por construção).

**Dimensionamento M8 (30 sementes):** ZDT1 domina — **~60 h·core por
problema-D30**; paraleliza por semente. O e81 **não** é o curinga imprevisível
que o cartão temia: virou um custo MEDIDO, com folga de **75%** sobre o teto.

---

## 7. O que foi entregue

| Artefato | O quê |
|---|---|
| `src/e81_qpots.py` (novo) | O runner: driver instrumentado sobre o vendor, com o `standalone_harness` fazendo toda a infra |
| `src/experiment.py` | SÓ a linha do `e81` em `_DISPATCH_LOADERS` (5 ins / 1 del) |
| `tests/test_e81.py` (novo, 21 testes) | Identidade/artefatos · as 3 âncoras contra o vendor real · os 3 ganchos (aplicam **e restauram**) · adapter e des-padronização μ/σ (comparada numericamente com a inversa do stock, `rtol=1e-10`) · DEF-C3 sem duplo-encode · 2 provas caras atrás de `E81_SLOW=1` |
| `scripts/accept.py` | Branch **ADITIVO** `R3-e81` + `check_r3_e81` (18 checks) — **279 ins / 0 del** |
| `handoff/R3-e81.md` · `_RELATORIO-EXECUCAO.md` · este repasse | Documentação |
| Dados | `data/experiments/main/e81/exp_main_e81_{MMF1,DTLZ2,ZDT1}_0.*` |

**O repo vendorizado `algorithms/e81_qPOTS/` NÃO foi tocado** — `git status`
sobre `algorithms/` devolve **0 arquivos modificados**; o `repos.lock`
(`sha256_tree d2fa63a4…`) continua válido. SPEC, bundles, `CONTRATO_DE_DADOS`,
`REGISTRO` e `artifacts/` **também intocados** (território da torre).

---

## 8. 🔴 DEFINIÇÕES EM ABERTO — a torre DEVE levantar estas com o autor

> Os itens **1 e 2** são materiais (tocam fidelidade e o dado da tese). Os
> **4, 5, 6** bloqueiam ou arriscam **cartões seguintes**. Nenhum bloqueia o
> e81, que está fechado e verde.

### 1. 🔴 RATIFICAR o kernel `get_matern_kernel_with_gamma_prior(D)`

**A única decisão desta sessão que toca fidelidade.** O cartão diz apenas
*"Matérn = 1 linha `covar_module=`"*; eu implementei a **mesma chamada de
c262:195 e c154:247**, ancorado no rótulo **"Compartilhado (c262, e81)"** da
D30 (§4.1). A evidência é forte (a alternativa sem prior torna o **ZDT1
irrodável**; com o helper, 28/28 fits OK), mas **a escolha é minha e precisa
do autor**.

**Se o autor VETAR**, o cartão precisa de uma decisão sobre o fit que falha —
os 4 remédios que eu tinha levantado: subir `max_attempts`; capturar
`ModelFittingError` e re-tentar com outra seed; cair para
`fit_gpytorch_mll_torch` (Adam); ou aceitar `pára-e-loga` (e o ZDT1 do e81
não roda).

### 2. 🔴 A granularidade da ③-busca: a mesma regra do c149, efeito 100× diferente

A DEF-C2 diz *"a **população final** do otimizador de aquisição"* para "BO com
EA interno (… e81 qPOTS/NSGA-II, c149/NSGA-II)". A S.7 do e81 diz *"front +
índice do `select_candidates`"*. Segui o precedente c149 (rank-0 da população
final) — que é também exatamente o conjunto `res.X` que o `select_candidates`
ranqueia, i.e. o universo da decisão. **Mas o efeito medido é radicalmente
diferente:**

| config | pop do NSGA-II | linhas ③-busca / geração | **% da população** |
|---|---|---|---|
| e81 / MMF1 | 200 | 17,4 | **8,7 %** |
| e81 / DTLZ2 | 1.200 | 284,1 | **23,7 %** |
| e81 / ZDT1 | 3.000 | 31,4 | **1,0 %** |
| **c149** / MMF1·DTLZ2·ZDT1 | 1.000 | 1.000,0 | **100 %** |

O c149 captura 100% porque a aquisição dele é **2M** (μ e −σ²), onde quase tudo
é não-dominado; o e81 otimiza os **M objetivos verdadeiros**, e o rank-0 é uma
fatia fina. **A regra é a mesma; o dado que sobra não é.**

**A pergunta ao autor:** a ③-busca do e81 deve continuar sendo o **front**
(barata, é o universo da decisão, e é o que a S.7 do e81 pede nominalmente), ou
a **população final completa** (fiel à letra da DEF-C2, mas ~1,8 M linhas só no
ZDT1 e uma avaliação de posterior sobre 3.000 pontos por iteração)? Isto afeta
diretamente as análises "contrafactual greedy-μ" e "Kendall-τ do ranking" do
`CONTRATO_DE_DADOS.md` §9.

### 3. 🟠 `|ND| < q` no sub-estudo batch (D66, q=10) — risco quantificado, na borda

O `select_candidates` faz `argsort()[-q:]`: se o front tiver menos de `q`
pontos, o lote sai **menor, em silêncio** (o cartão já avisava). O runner conta,
loga `guard('lote_menor_que_q')` e grava `assert_lote_eq_q` no jsonl; o gate
**reprova** se não for `q` em toda geração. Nos pilotos (q=1) **nunca disparou**.
Medido para o batch:

| run | `|ND|` mín | p05 | mediana | máx | gerações com `|ND|<10` |
|---|---|---|---|---|---|
| MMF1 | **10** | 11 | 17 | 29 | 0 / 40 |
| DTLZ2 | 171 | 209 | 286 | 375 | 0 / 240 |
| ZDT1 | 14 | 23 | 31 | 49 | 0 / 600 |

**O MMF1 tem mínimo EXATAMENTE 10** — ou seja, o `exp=batch` com q=10 roda **na
borda**, e outra semente pode cair abaixo. **A pergunta:** quando isso
acontecer, o run deve **abortar** (`failed`), **aceitar o lote menor** (e então
o gate precisa relaxar), ou usar o **"fallback qmaximin"** que o cartão cita —
que eu **documentei mas não implementei**, por não haver definição do que ele é?

### 4. 🟠 `c3=` exige dict, e o teste do DI-23 usa string — **bloqueia b5 / c311 / piso-off**

§4.2. Ações sugeridas: corrigir `tests/test_di23_harness.py:90-91` e, de
preferência, fazer `surrogate_row` **recusar** uma string em `transf_params`
(falha aberta em vez de duplo-encode silencioso).

### 5. 🟠 `update_timing` antes de qualquer `break` no c149

§4.3. Um aborto por teto/cache-cap do c149 grava uma ④ que o **próprio gate
reprova**. Decisão de infra (M7); o padrão correto está no e81 (`finally`).

### 6. 🟠 `q` no `write_run_outputs`

§4.4. Kwarg no harness — senão **todo o sub-estudo batch (D66)** grava `q=1`
mentido no manifesto, que é a fonte da tabela de execuções.

### 7. 🟡 `load_sonda` recalcula `f_hash_online` e nunca o compara ao sidecar

`standalone_harness.py:701-707` confere `x_hash_online` mas **não**
`f_hash_online`, embora o campo exista nos 3 sidecars que conferi. O `f_hash`
que vai ao `sonda_info` do manifesto é, portanto, **não auditado**.

### 8. 🟡 `auditar.py` usa `.to_pandas()` e o `env_e81_qpots` não tem pandas

O validador permanente **só roda no env-main**. Funciona (foi como rodei), mas
convém registrar no cartão, ou trocar por pyarrow puro — os envs próprios de
b5/c311 podem ter a mesma restrição.

### 9. 🟡 Doc-sync do checklist §22.4·3.5

Consequência do item 1: cravar a chamada exata do kernel, para o próximo leitor
não repetir o meu caminho. Vale registrar também que o default do BoTorch 0.16.1
é `RBFKernel` **puro** (sem `ScaleKernel`).

### 10. Fila de outras mãos (não são definições)

- **Julgamento de fidelidade D97** (autor, em lote) — números-guia na §5/§6 e
  no `handoff/R3-e81.md`.
- **`cards/INDEX.md`** (torre) — não marquei.

---

## 9. Ressalvas honestas (o que NÃO foi provado)

1. **O caminho de ABORTO não foi exercitado ao vivo.** O ZDT1 fechou em 1,99 h,
   então nem `teto_wall` nem `cache_hit_travado` dispararam. A ④ em `finally`
   garante a camada válida **por construção**, e o plumbing do
   `write_run_outputs(status=, motivo_parada=)` tem teste (DI-23.2/3.3) — mas o
   end-to-end fica pendente. É **a mesma lacuna que a DI-23.4 registrou para o
   c149**.
2. **`|ND| < q` nunca disparou** (q=1 nos pilotos). O código está lá e coberto
   por gate, mas não exercitado — ver §8 item 3.
3. **Fidelidade não foi julgada** (D97). O runner instrumenta e aplica o gate
   objetivo; o julgamento é manual, do autor.
4. **Os walls são de UMA semente (0) em UMA máquina** (M1 Pro, 1 core, threads
   pinados). Servem para dimensionar o M8, com a ressalva de stack do §19.

---

## 10. Onde está cada coisa

- **Mapa técnico** (os 3 ganchos, a semântica exata do σ, as 9 decisões de
  sessão com respaldo): `handoff/R3-e81.md`
- **Narrativa do processo** (o que deu errado e como foi pego):
  `handoff/R3-e81_RELATORIO-EXECUCAO.md`
- **Dados:** `data/experiments/main/e81/exp_main_e81_{MMF1,DTLZ2,ZDT1}_0.*`
  (4 camadas + `.jsonl` + manifesto cada)
- **Reprodução:** `handoff/R3-e81.md` §6 (comandos literais)
- **Commits:** `5bde3db` (código+gate+testes) → `681b0eb` (handoff+relatório)
  → `7751f5d` (este repasse). Branch `experiment/definitive_algorythms`,
  **sem push**.
