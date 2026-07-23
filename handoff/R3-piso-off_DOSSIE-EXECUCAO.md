# DOSSIÊ DE EXECUÇÃO — R3-piso-off (`moead_media`, MOEA/D-média, DESDEO mode 12)

> **Auto-contido.** Cobre Fase 0 → A → B do cartão do piso offline, cada comando
> rodado e seu resultado, a resolução do σ-NULL, os achados da revisão adversarial,
> e TODA definição em aberto para o autor. Sessão 2026-07-23. Runner:
> `src/piso_offline.py`. Env de execução: `env_b5`. Molde direto: `src/b5_prob.py`.

---

## 0. Veredito

**CARTÃO FECHADO.** O piso offline `moead_media` (mode 12 = Gen-MOEA/D PBI) está
implementado, wired e validado ponta-a-ponta. É, por desenho (D77/DEF-E3), **a
ablação cirúrgica do b5**: MESMO motor (MOEA/D do DESDEO), MESMA especificação de
surrogate (SurrogateKriging), MESMO orçamento (40k aval-surrogate) — muda **só a
seleção** (mode 12 = `MOEAD_select` PBI, só a média; b5m = `ProbMOEAD_select`
probabilístico). É "o b5 sem σ".

Todos os gates objetivos VERDES (Fase A + Fase B). Fidelidade = validação MANUAL do
autor a posteriori (D97) — fora do escopo do encanamento.

**Com este cartão, os 21/21 configs do estudo estão implementados.**

Interpretadores:
- `env_b5 = /Users/gmello/Documents/python_venvs/env_b5/bin/python` (py3.7 x86_64/Rosetta)
- `env_main = /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python` (py3.11.9)

---

## 1. FASE 0 — gate de ambiente (provas, ZERO instalação — D80/D81)

| Prova | Comando (resumo) | Resultado |
|---|---|---|
| envs.json mapping | `alg_to_env.moead_media` | `{stack: python, env: env_b5}` ✓ |
| **env_b5 RODA desdeo mode-12** | proof script no env_b5 | `MOEA_D` de `desdeo_emo.EAs.ProbMOEAD`, root-first, `SurrogateKriging`, sonda MMF1 S=20000, filtro ND pymoo — ✓ |
| datasets | `data/datasets/{MMF1,DTLZ2,ZDT1}/ds_*_0.parquet` | presentes (61/371/929 = 31D−1) ✓ |
| sonda | `data/sonda/sonda_{P}.parquet` | presentes ✓ |
| `load_offline_budget` no env_b5 SEM shim | direto | MMF1 D2/M2/n61 · DTLZ2 D12/M3/n371 · ZDT1 D30/M2/n929 ✓ ⇒ `doe.py` já é pyarrow-12-safe (DI-26); shim do b5 OMITIDO |
| suíte env-main baseline | `unittest discover -s tests` | **Ran 309 · OK (skipped=17)** · exit 0 |
| preflight | `scripts/preflight.py` | `pré-voo OK ✓` · exit 0; âncoras b5-* APLICADO |
| alg_id (D62/D91) | `seeds.json` | `moead_media = 21`; `seed_base` sem offset D22 ⇒ base=semente |

Prova-chave nova: o R3-00 só exercitara import+sonda; esta sessão provou que o
env_b5 **executa** o evolver/DataProblem/dataset-read de fato.

---

## 2. FASE A — o runner `src/piso_offline.py`

### 2.1 Delta líquido vs o molde b5m (`b5_prob.py`)
1. importa `MOEA_D` de `desdeo_emo.EAs.ProbMOEAD` (mode 12) — **não** `ProbMOEAD`
   (mode 72), **nem** o `MOEA_D` de `desdeo_emo/EAs/MOEAD.py:22` (default TCH,
   `_next_gen` NÃO arquiva — a armadilha; `Main_Execute.py:21/115` confirma a de
   ProbMOEAD, PBI, que usa `MOEAD_select` e arquiva ind/obj/unc por geração);
2. `_ALG_ID=21`, `_MODE=12`, `_MODELO_FLAG="moead_media/MOEAD-PBI+GPR-media"`;
3. `_predict` devolve `(mu, None)` — σ NULL (DI-16.1);
4. linhas de busca da ③ com `sigma=None`;
5. `_sigma_dict` reescrito p/ o piso;
6. **zero** mudança de construtor / `population_size` / patch vendorizado novo.

### 2.2 Fluxo (idêntico ao b5, regime offline)
shim `typing.Literal` → `import standalone_harness` (pina threads D79 antes de numpy)
→ seeds D62 (`iteration_seed(base, 21, 0, uso)`, random e numpy, bits32) →
`_import_vendored` (stub pygmo, root-first, fix pyDOE `lhs`←RandomState global) →
`load_offline_budget` (① = dataset) + `load_sonda(offline)` → `DataProblem` (1-based,
bounds reais) → `train(SurrogateKriging)` (1 GPR/obj, n_restarts=9, treino ÚNICO;
cronometrado → ④ 1 linha) → `_predict` (μ; σ=None) → `emit_sonda_block` (1 bloco
S=20000, geracao=NULL pós-hoc) → `MOEA_D(use_surrogates=True, n_gen_per_iter=10,
total_function_evaluations=40000)` sob `offline_guard` → replay dos arquivos por
geração (③ busca, σ=None) + ⑥ DI-10 → ⑦ `write_final` (avalia 1× na verdade, ND
pós-real, SEM `nd_pos_real`) → `write_run_outputs`.

### 2.3 Outputs ①..⑦
① dataset (CP x_hash+f_hash) · ② vazia (DI-16.17) · ③ busca+SONDA (σ NULL, geracao
NULL na sonda, ordem do artefato) · ④ 1 linha (tempo_fit_s REAL) · ⑤ manifesto
(sigma_dict completo) · ⑥ jsonl DI-10 · ⑦ __final (reconstituível da ③, DI-16.16).

### 2.4 Patches vendorizados — INERTES para o mode 12 (confirmado ao vivo)
`b5-mode72-kde` (ProbMOEAD_select.py — o mode 12 usa `MOEAD_select`, outro arquivo) e
`b5-mode7-archive` (BaseEA._next_gen — o `MOEA_D._next_gen` sobrescreve sem `super()`)
não entram no caminho. A ⑦ nasce reconstituível da ③ NATIVAMENTE. Nenhum vendored
editado; único gancho runtime = o fix pyDOE do b5 (RATIFICADO DI-28.3).

### 2.5 Gates da Fase A (todos VERDES)
```
$ENV_B5 -c "run_piso_offline('off','moead_media','<P>',0)"    # pilotos diretos
$ENV_MAIN scripts/auditar.py moead_media <P> 0 --exp off --regime offline
$ENV_MAIN scripts/final_eval.py --exp off --alg moead_media --problema <P> --semente 0 --check
PISO_SLOW=1 $ENV_B5 -m unittest tests.test_piso_off            # gates 3/4/5
$ENV_MAIN -m unittest tests.test_piso_off                      # gate 6 (isolado)
```

| config | D | M | FE | n_ger | n_final | n_nd_pos_real | auditar | final_eval | wall |
|---|---|---|---|---|---|---|---|---|---|
| MMF1  | 2  | 2 | 61  | 801 | 50  | 8  | 🟢 | 🟢 | 36.6 s |
| DTLZ2 | 12 | 3 | 371 | 381 | 105 | 53 | 🟢 | 🟢 | 46.2 s |
| ZDT1  | 30 | 2 | 929 | 801 | 50  | 29 | 🟢 | 🟢 | 112.4 s |

- **`n_ger`/`n_final` == b5m em 3/3** (50/105/50) — a geometria é IDÊNTICA; só a
  seleção difere (⇒ `n_nd_pos_real` diverge). Prova viva da DI-16.4 (N = lattice b5m).
- Determinismo (gate 3): 2 runs mesma semente ⇒ ⑦ + ③-busca bit-a-bit ✓.
- Não-perturbação (gate 4): sonda ON/OFF ⇒ ⑦ + ③-busca bit-a-bit (NaN-aware, σ=NULL) ✓.
- `test_piso_off`: 12/12 no env_b5 (PISO_SLOW) · env-main-safe (skips limpos) · isolado
  no env-main `Ran 12 · OK (skipped=5)`.

---

## 3. FASE B — wiring (mesma sessão; torre liberou após validar o parcial)

### 3.1 dispatch
`src/experiment.py:163` descomentado:
`'moead_media': ('src.piso_offline','run_piso_offline','standalone')`. Já prontos:
`VENV_ONLY_ALGS ∋ moead_media` e `alg_to_env.moead_media=env_b5`. `requirements/**`
intocado.

### 3.2 accept
`scripts/accept.py::check_r3_piso_off` (molde `check_r3_b5`) + bloco CLI do cartão
`R3-piso-off` antes do catch-all F0-01. Deltas do piso: **σ_* NULL em TODA a ③** (μ_*
preenchido), **④ = 1 linha** com tempo_fit_s real, **N = lattice b5m** (pop da última
geração 50/105). ⑦ reconstituível delegada ao `final_eval.check_final`.
```
$ENV_MAIN scripts/accept.py R3-piso-off --alg moead_media --problema <P> --semente 0 --exp off
→ MMF1 / DTLZ2 / ZDT1 = VERDE (11 checks OK cada; exit 0)
```

### 3.3 e2e do dispatch (precedente c311-B)
```
$ENV_MAIN -c "experiment.run('moead_media','MMF1',0,exp='off')"
→ status ok · executavel_filho=.../env_b5/bin/python · pin_filho=OMP/OPENBLAS/MKL/NUMEXPR=1
→ ⑦ sha256 ANTES(direto)==DEPOIS(dispatch)=1131114f… → BIT-IDÊNTICA ✓ · ③ idêntica ✓
```
Prova que o roteamento por venv (D79/N.1.2) produz saída byte-idêntica ao piloto
direto — PYTHONHASHSEED=0 (DI-27) + threads pinadas no filho.

### 3.4 teste compartilhado atualizado (necessário)
`tests/test_r3_harness.py::test_experiment_run_roteia_venv_only_para_subprocesso`
usava `moead_media` como cobaia "venv-only não-registrado". Com os 4 venv-only agora
TODOS registrados, reescrevi a prova p/ forçar interpretador inexistente ⇒ roteamento
provado via `FileNotFoundError` no spawn (nunca `NotImplementedError`), sem rodar o
piso. Único teste compartilhado tocado.

### 3.5 fechamento
```
PISO_SLOW=1 $ENV_B5 -m unittest tests.test_piso_off  → Ran 12 · OK
$ENV_MAIN -m unittest discover -s tests              → Ran 321 · OK (skipped=22)
$ENV_MAIN scripts/preflight.py                       → exit 0
```

---

## 4. σ-NULL — a resolução (registro definitivo)

O prompt do cartão trazia, na epígrafe (i) e na linha OUTPUTS, "③ … σ = desvio do
GPR — NUNCA variância". Essa frase é **cópia literal** do `sigma_dict` do molde b5
(`b5_prob.py:189`) e **contradiz** a decisão que o próprio cartão cita:
- **DI-16.1** (REGISTRO:637): *"`sigma_*` **NULL**"*;
- **CONTRATO §3.2** (linhas 191/645): piso offline = *"mu_* preenchido; **sigma_*
  NULL**"*;
- o **gate 4 do próprio cartão**: *"NaN-aware **se houver σ=NaN**"* — antecipa σ=NaN
  na ③-busca.

**Aplicada a precedência (SPEC/DI > frase-resíduo do prompt): σ = NULL** em TODA a ③
(busca E sonda). O `problem.evaluate` ainda CALCULA `.uncertainity` (o motor a
arquiva), mas o runner a DESCARTA — o piso reporta SÓ μ.

**Confirmação da torre (2026-07-23):** *"sua resolução está CORRETA e é DEFINITIVA …
NÃO é decisão em aberto; registre como 'contradição do prompt resolvida por
precedência, confirmada pela torre'. Nenhum re-trabalho."* → **REGISTRADO.**

---

## 5. Revisão adversarial (workflow próprio de 3 lentes + verificação) — 2 MINOR

- **F1 — `piso_offline.py` `sigma_dict['sigma_*']`:** reafirmava "mesmo GP, mesmo μ",
  contradizendo o campo `modelo` (DI-28: treino INDEPENDENTE por config, nunca
  idêntico — `moead_media` alg_id 21 ≠ b5m 18 semeia RNGs distintos; os 9 restarts do
  GPR podem convergir a μ não byte-igual). Um leitor R4 poderia presumir μ-delta=0.
  **Corrigido:** reescrito p/ "MESMA ESPECIFICAÇÃO de GP, treino independente; μ da
  mesma especificação, não presumido-igual".
- **F2 — `test_piso_off.py` ④:** não guardava a DI-13.10 (`tempo_geracao_s` EXCLUI a
  sonda) nem `n_acumulado=n_ds` — uma regressão que dobrasse a sonda no
  `tempo_geracao_s` passaria silenciosa (contaminando a curva de escalabilidade).
  **Corrigido:** asserções `tempo_geracao_s == fit+busca`, `tempo_pred_sonda_s > 0`,
  `n_acumulado == n_dataset`.
- Pilotos ×3 RE-RODADOS (manifesto com sigma_dict corrigido); resultados IDÊNTICOS;
  ⑦ byte-inalterada.

---

## 6. DEFINIÇÕES EM ABERTO / CIÊNCIA PARA O AUTOR

> ### ⚠⚠ AÇÃO REQUERIDA DA TORRE CENTRAL ⚠⚠
> **Os itens B2 e B3 abaixo são DECISÕES DO AUTOR ainda em aberto.** Nenhum é falha
> de gate (o cartão fecha VERDE com os defaults que escolhi), mas ambos são escolhas
> semânticas/de contrato onde adotei o default consistente-com-b5 e o autor pode
> querer diferente. **A torre central DEVE levantar B2 e B3 com o autor para
> decisão** antes de considerar o cartão 100% ratificado. B7 pede CIÊNCIA (teste
> compartilhado alterado). B1/B8 já resolvidos; B4/B5/B6 são só informativos.

| # | Item | Status | Precisa do autor? |
|---|---|---|---|
| **B2** | `modelo_hp` = NULL offline (D-08 "HP fixos, treino único") **vs** "grava modelo_hp" (DI-16.1). Segui o molde b5 (NULL) p/ manter a ablação simétrica ao b5m; o VALOR é NULL por HP fixos. | 🟠 **ABERTO** | **SIM — ratificar** |
| **B3** | ⑥/HEADER: o `moead_media` é ao mesmo tempo "um piso" e "um config surrogate da família b5". A CONTRATO §6.1 tem uma linha "pisos" (pede ideal/nadir por geração + vetores de decomposição no HEADER) e uma linha "b5" (pede pesos no header + p_wrong). Segui a linha **"b5"** (⑥ = `minimo_comum_di10`); NÃO adicionei o enriquecimento "pisos". | 🟡 **ABERTO** | **SIM — decidir qual linha** |
| B1 | σ do piso = NULL | ✅ RESOLVIDO (torre, precedência) | não |
| B7 | `test_r3_harness.py` — 1 teste COMPARTILHADO atualizado (cobaia venv-only esgotou ao ligar o dispatch) | 🟡 ciência | ciência (opcional decidir se prefere outra abordagem) |
| B4 | shim pyarrow do b5 OMITIDO (doe.py já DI-26-safe) | 🟢 ciência | não |
| B5 | `final_eval` roda no env_main (py3.11 tem `typing.Literal`) | 🟢 ciência | não |
| B6 | seed pela convenção D62 (idêntico ao b5, já ratificado) | 🟢 ciência | não |
| B8 | 2 achados MINOR da revisão adversarial | ✅ corrigidos | não |

**Detalhe de B2 (para a decisão):** o GP (SurrogateKriging) OTIMIZA os HP do kernel
no fit único (n_restarts=9), então HP AJUSTADOS existem. O molde b5/D-08 grava
`modelo_hp=NULL` porque não há RE-treino/tuning por geração. Alternativa se o autor
quiser: logar os HP ajustados 1× no HEADER (read-only, não perturba) — mas isso
desviaria do b5m e criaria uma assimetria na ablação. **Recomendação:** manter NULL.

**Detalhe de B3 (para a decisão):** adicionar a linha "pisos" seria read-only e
não-perturbador (ideal/nadir = max/min por objetivo da pop arquivada por geração;
vetores = `evolver.reference_vectors` no header). **Recomendação:** como a análise do
piso é a do PAR de ablação (piso×b5m), a linha "b5" mantém o ⑥ estruturalmente
idêntico ao b5m — mas é decisão do autor porque a §6.1 lista o piso sob "pisos".

---

## 7. Rituais / higiene

Nenhum vendored (`algorithms/**`) editado; `requirements/**`, `repos.lock`,
`anchors.json`, `seeds.json`, SPEC/REGISTRO/bundles, `_baseline_pre_retrofit/**`
intocados. `git push` / `add -A` NÃO usados. `data/experiments/` é gitignored (os
outputs dos pilotos ficam LOCAIS). Commits `[R3-piso-off]`: código+testes num commit,
handoffs+dossiê noutro (add explícito). Reconhecidos os commits do c311 fechado
(`fb4fc30` wiring · `0a6fe8e` handoffs · `74281a0` dossiê) + as ratificações DI-27/28.
