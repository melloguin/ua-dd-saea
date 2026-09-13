# R3-e81 — RELATÓRIO DE EXECUÇÃO (o *como*: a narrativa, com o que deu errado)

> Companheiros: `R3-e81.md` (o *o quê* — o mapa técnico) e
> `R3-e81_REPASSE-A-TORRE.md` (validação ao vivo + definições em aberto).
> Este documento existe para a próxima sessão **não repetir os meus erros**.

**Data:** 2026-07-22 · **Cartão:** R3-e81 (qPOTS), ONLINE, `env_e81_qpots` no Mac.

---

## 1. FASE 0 — o gate de ambiente (D80/D81)

Correu sem susto, e vale registrar o que foi conferido, porque o cartão exigia
um gate real e não uma inspeção de `pip list`:

| # | Verificação | Resultado |
|---|---|---|
| 1 | `envs.json:alg_to_env.e81` | `env_e81_qpots` ✓ |
| 2 | Import de cada pin no env | py3.11.9 **arm64** · torch 2.11.0 · botorch 0.16.1 · gpytorch 1.14.2 · numpy 2.2.6 · **pymoo 0.6.1.6** · scipy 1.17.1 · pyarrow 25.0.0 ✓ |
| 3 | Fit BoTorch mínimo | `SingleTaskGP` + `fit_gpytorch_mll` + `posterior()` OK em float64 |
| 4 | **TAREFA 0 — CP-init** | `problems.py` avalia no env e o hash do `init_X` do `FEBudget` bate o sidecar do DoE **nos 3 problemas** (MMF1 `89b8ce4e…`, DTLZ2 `71d3398a…`, ZDT1 `ed4a004a…`) — **3/3 ✅** |
| 5 | Artefatos | `data/doe/{MMF1,DTLZ2,ZDT1}/doe_*_0.parquet` + `data/sonda/sonda_*.parquet` presentes; sonda online = 2000×D ✓ |
| 6 | Suíte no env-main + preflight | **272 OK (5 skip)** · preflight **exit 0** |

**Uma diferença do env que merece registro:** o `env_e81_qpots` **não tem
pandas**. Isso é irrelevante para o runner (o harness usa `pyarrow` puro), mas
**quebra o `scripts/auditar.py` se rodado nesse interpretador** — ele chama
`.to_pandas()`. O `auditar.py` deve ser rodado no **env-main** (foi o que fiz).

---

## 2. O que deu errado — e é a parte útil deste documento

### 2.1 🔴 O erro que quase virou um pára-e-loga desnecessário: o kernel sem prior

**O que aconteceu.** Implementei o patch Matérn da D30 do jeito literal que o
cartão descreve — *"Matérn = 1 linha `covar_module=`"* — como
`ScaleKernel(MaternKernel(nu=2.5, ard_num_dims=D))`. MMF1 e DTLZ2 rodaram; o
**ZDT1 explodiu no primeiro fit**:

```
botorch.exceptions.errors.ModelFittingError: All attempts to fit the model have failed.
```

**A investigação (o que eu media a cada passo).** Isolei em 4 eixos:

| eixo testado | resultado |
|---|---|
| nugget `1e-12` vs `1e-6` | **as duas falham** ⇒ não é o valor do nugget |
| kernel RBF stock (sem patch) | **OK nos 2 objetivos** ⇒ é o patch |
| Matérn **sem** `train_Yvar` (ruído inferido) | **OK** ⇒ é a interação Matérn × ruído FIXO |
| n-scan do objetivo 1 (`n`=50…329) | 50 OK, 100 OK, **150 FALHA**, 200 OK, 250 OK, 300 OK, **329 FALHA** ⇒ **intermitente, não-monotônico em n** |

A causa-raiz **não era numérica no sentido de PSD/Cholesky** — o warning
subjacente era:

```
OptimizationWarning: `scipy_minimize` terminated with status
OptimizationStatus.FAILURE ... "ABNORMAL"
```

isto é, **o L-BFGS-B do `fit_gpytorch_mll` não convergia**, e o BoTorch
esgotava as tentativas.

**Onde eu quase errei.** Cheguei a montar a pergunta de pára-e-loga (D81) para
o autor, com 4 remédios candidatos (subir `max_attempts`, re-semear e re-tentar,
cair para `fit_gpytorch_mll_torch`, ou simplesmente abortar). **Estava
perguntando a coisa errada** — porque o problema não era do algoritmo, era da
*minha* materialização da D30.

**A resposta estava no próprio repo.** A D30 é marcada
**"Compartilhado (c262, e81)"** no bundle do e81, e os **dois runners BoTorch
já aceitos** implementam essa mesma decisão com uma chamada só:

```
src/c262_qnehvi.py:195   covar_module=get_matern_kernel_with_gamma_prior(D)
src/c154_jes.py:247      covar_module=get_matern_kernel_with_gamma_prior(D)
```

que é `ScaleKernel(MaternKernel(nu=2.5, ARD, lengthscale_prior=Gamma(3,6)),
outputscale_prior=Gamma(2,0.15))`. Trocado o kernel pelo helper:

| problema | Matérn SEM prior | `get_matern_kernel_with_gamma_prior` |
|---|---|---|
| MMF1 (n=21) | OK, OK | OK, OK |
| DTLZ2 (n=131) | OK, OK, OK | OK, OK, OK |
| **ZDT1 (n=329)** | OK, **ModelFittingError** | **OK, OK** |

E o **n-scan de robustez ao longo de TODA a trajetória do ZDT1**
(`n` = 329→929, os 2 objetivos): **28/28 fits OK, zero falhas**.

**A lição, que vale para os cartões seguintes.** Quando a SPEC marca uma
decisão como **"Compartilhado"** entre configs, ela não está descrevendo só o
*nome* do kernel — está exigindo a **mesma construção**, priors inclusive. Um
Matérn sem prior e um Matérn com `GammaPrior` são surrogates diferentes; se
dois configs os usassem sob o rótulo de uma decisão só, a comparação entre eles
mediria a diferença de priors, não a diferença de algoritmo. **Antes de
materializar uma decisão marcada "Compartilhado", vá ler como o irmão já
aceito a materializou** — o repo é a fonte, não a prosa do cartão.

*(Registrado também que os priors NÃO são cosmética: são o que faz o MLL
convergir em D=30. O achado de fidelidade — "o default do `SingleTaskGP` no
BoTorch 0.16.1 é `RBFKernel` PURO, sem `ScaleKernel`" — está travado por teste.)*

### 2.2 O erro de leitura da API: `transf_params` no kwarg `c3=`

O `c149` precisava carimbar as colunas C3 da sonda **pós-hoc**
(`_stamp_c3_sonda`), porque o `emit_sonda_block` não as aceitava. O DI-23 fechou
essa lacuna com o kwarg `c3=`. Só que as duas rotas têm **formatos opostos**:

- `_stamp_c3_sonda` **muta a row já construída** ⇒ `transf_params` tem de ser
  **string** (o `json.dumps` já aconteceu);
- `c3=` repassa `**c3` ao `surrogate_row`, que faz o `json.dumps` ⇒ tem de ser
  **dict**.

Passar string no `c3=` produz **duplo-encode silencioso**. Medido:

```
c3 com DICT   -> {"mu": [0, 0]}           json.loads -> dict
c3 com STRING -> "{\"mu\": [0, 0]}"       json.loads -> str   (precisa de 2 loads)
```

O runner usa **dict**, e o gate `check_r3_e81` **decodifica uma amostra e
reprova se não for `dict`** — o hazard não volta em silêncio.

⚠ **O próprio teste do DI-23 usa a forma errada** — ver o repasse §definições.

### 2.3 O defeito herdado que eu NÃO copiei: a ④ com NULL no aborto

No molde `c149`, o `break` do cache-cap (`c149_lbnmobo.py:738`) acontece
**antes** do `buf.update_timing(...)` (`:760`). Num aborto, a última geração
fica com `tempo_busca_s`/`tempo_pred_sonda_s`/`tempo_geracao_s` = **NULL** —
o que **reprova o próprio check** `④ timing v5.2.1 completa` do `accept.py`.

No e81 a linha da ④ é fechada em **`finally`**, então o aborto (teto ou
cache-cap) preserva uma ④ VÁLIDA — que é justamente o entregável que o cartão
pede quando o ZDT1 estoura o teto ("manifesto failed + curva parcial").

### 2.4 O `q` que o manifesto mentiria

`write_run_outputs` não repassa `q` ao `new_manifest`, que fixa `q=1`. O grid
tem **150 runs de e81 em `exp=batch` com q=10**. O runner carimba `man["q"]`
quando diverge. Lacuna de infra — sinalizada à torre.

### 2.5 Detalhes menores que custaram tempo

- **`ModelObject.models` é append-only.** Chamar `fit_gp()` duas vezes no mesmo
  objeto deixa `len(models) == 2·M` sem erro nenhum. A receita canônica já
  manda recriar por iteração; agora há uma segunda razão documentada.
- **`res.X` do pymoo vem 1-D quando |ND|==1**, e o `cdist` do
  `select_candidates` exige 2-D — quebraria no meio do run. Guarda `front_1d`
  com `reshape(1,-1)` + log.
- **O stock imprime muito** (`Fitting GPs`, `Fit: i`, `Sample Pareto Set…`) —
  ~3 linhas × 600 iterações no ZDT1. Engolido por `_silencio()` (só `stdout`;
  warnings, `stderr` e exceções passam).
- **`gpytorch` arredonda o nugget**: `train_Yvar=1e-12` dispara
  `NumericalWarning: Rounding small noise values up to 1e-06`. É comportamento
  do stock, registrado nos `params` do manifesto — não uma alteração nossa.

---

## 3. O processo, etapa a etapa

1. **Gate de ambiente + TAREFA 0** (§1) — 3/3 CP-init verdes.
2. **Leitura obrigatória** na ordem do cartão (CLAUDE.md, CONTRATO_DE_DADOS,
   contrato de export §17, contrato R3, o cartão `alg_e81_qpots.md` + o
   checklist §22.4·3.5, os 2 repasses c122/c149, REGISTRO A10–A12).
3. **Recon multi-agente com verificação cética** (6 leitores + 3 refutadores
   adversariais): repo vendorizado, molde c149, API do harness, gates,
   SPEC/artefatos, runners R2. Os refutadores acharam **um erro acionável e
   perigoso** — a orientação de passar `transf_params` já serializado no `c3=`
   (§2.2) — e dois defeitos de contrato que eu herdaria (§2.3, §2.4).
4. **Verificação bit-a-bit das 3 âncoras** do `anchors.json` contra o vendor
   (`model_object.py:120` = `model = SingleTaskGP(`; `acquisition.py:219` =
   `torch.manual_seed(1024 + seed_iter)`; `acquisition.py:366` = `seed=2430,`)
   — **3/3 conferem**, e viraram teste permanente.
5. **Smoke do mecanismo** antes de escrever o runner: 3 iterações do loop
   canônico com o patch e a instrumentação, provando que os ganchos capturam
   draws/front/índice e que `newx ∈ [0,1]^D`.
6. **Implementação** (`src/e81_qpots.py`).
7. **Diagnóstico da falha do ZDT1** (§2.1) → correção do kernel.
8. **Gate `check_r3_e81`** (18 checks, ADITIVO antes do catch-all F0-01) +
   `tests/test_e81.py` (21 testes) + linha do dispatch.
9. **Pilotos** MMF1 → DTLZ2 → ZDT1 (teto 8 h), **sequenciais** para os walls
   saírem sem disputa de máquina (lição c122 §6).
10. **Validação, documentação e commits** — ver o repasse.

---

## 4. Aviso de método para a próxima sessão

Os walls dos pilotos foram medidos com os 3 runs **em sequência** e sem
workflow de agentes rodando junto. As medições intermediárias que fiz **durante**
a recon multi-agente saíram 2–4× pessimistas (a mesma armadilha que o repasse
do c122 §6 já registrava). **Dimensione o M8 pelos walls do repasse, não por
medições feitas com a máquina disputada.**
