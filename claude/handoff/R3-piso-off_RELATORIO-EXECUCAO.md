# R3-piso-off — RELATÓRIO DE EXECUÇÃO (o COMO: comandos + números)

Sessão 2026-07-23. Runner `src/piso_offline.py`. Todos os comandos rodados a
partir da raiz do repo. Envs:

```
ENV_B5=/Users/gmello/Documents/python_venvs/env_b5/bin/python                          # py3.7 x86_64 (Rosetta)
ENV_MAIN=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python  # py3.11.9
```

Pilotos SEQUENCIAIS, 1 core (D79); env de thread pinada antes de numpy:
`export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`.

---

## 1. FASE 0 — gate de ambiente (provas)

**1.1 env_b5 RODA desdeo mode-12** (prova nova; o R3-00 só exercitou import+sonda):
```
MPLBACKEND=Agg PYTHONHASHSEED=0 $ENV_B5 <scratchpad>/proof_env_b5.py
→ OK env_b5 RODA desdeo mode-12:
  MOEA_D de: desdeo_emo.EAs.ProbMOEAD
  sklearn 0.21.3 | pandas 1.3.5 | pyarrow 12.0.1 | numpy 1.21.6
  sonda MMF1 offline: S=20000 D=2 M=2
  ⑦-proof: F.shape=(8, 2) nd=2
  OFFLINE_CONFIGS: ('e103','b5r','b5m','c311','moead_media')
```
A prova confere: root-first (desdeo_problem/emo sob o vendor), `MOEA_D._next_gen`
arquiva ind/obj/unc, `MOEA_D.__init__` usa `MOEAD_select`, gancho pyDOE presente.

**1.2 preflight** (env_main): `pré-voo OK ✓` — **exit 0**. `b5-mode72-kde` /
`b5-mode7-archive` = APLICADO; sem placeholders.

**1.3 datasets/sonda** (D=M=n via `load_offline_budget` no env_b5, SEM o shim do b5):
```
MMF1   D=2  M=2 n=61   maxfe=61   x_hash=a3c765a13833
DTLZ2  D=12 M=3 n=371  maxfe=371  x_hash=0da07c151b6b
ZDT1   D=30 M=2 n=929  maxfe=929  x_hash=7aa32875a6da
```
⇒ `doe.py` é pyarrow-12-safe (DI-26) — o `_patch_doe_pyarrow_compat` do b5 NÃO é
necessário; foi OMITIDO do runner.

**1.4 suíte env-main baseline:** `$ENV_MAIN -m unittest discover -s tests`
→ `Ran 309 tests in 16.403s` · `OK (skipped=17)` · **exit 0**.

**1.5 identidade:** `seeds.json` alg_id `moead_media` = **21**; `alg_to_env.moead_media
= env_b5`; `experiment.py:163` (dispatch) COMENTADO; `OFFLINE_ALGS`/`OFFLINE_CONFIGS`/
`auditar.OFFLINE`/`final_eval.permitidos` já contêm `moead_media`.

---

## 2. Pilotos (invocação DIRETA no env_b5)

```
MPLBACKEND=Agg PYTHONHASHSEED=0 $ENV_B5 -c \
  "from src import piso_offline as P; print(P.run_piso_offline('off','moead_media','<P>',0))"
```

| config | resultado | wall |
|---|---|---|
| MMF1  | `fe_final=61  maxfe=61  n_dataset=61  cp_init_ok=True  n_geracoes=801  n_final=50  n_nd_pos_real=8  mode=12`  | 36.6 s |
| DTLZ2 | `fe_final=371 maxfe=371 n_dataset=371 cp_init_ok=True n_geracoes=381 n_final=105 n_nd_pos_real=53 mode=12` | 46.2 s |
| ZDT1  | `fe_final=929 maxfe=929 n_dataset=929 cp_init_ok=True n_geracoes=801 n_final=50  n_nd_pos_real=29 mode=12` | 112.4 s |

Saídas em `data/experiments/off/moead_media/exp_off_moead_media_<P>_0.*` (8
arquivos por run: `__real/__pop/__surrogate/__timing/__final.parquet` +
`.manifest.json` + `.jsonl` + `__final.manifest.json`). **Cross-check b5m:**
`n_ger`/`n_final` idênticos (MMF1 801/50, DTLZ2 381/105, ZDT1 801/50) ⇒ N herdado
= lattice do b5m (DI-16.4).

---

## 3. Gates da FASE A

### 3.1 GATE 1 — `auditar.py` (env_main) ×3
```
$ENV_MAIN scripts/auditar.py moead_media <P> 0 --exp off --regime offline
→ AUDITORIA moead_media/MMF1/0:  VERDE   (exit 0)
→ AUDITORIA moead_media/DTLZ2/0: VERDE   (exit 0)
→ AUDITORIA moead_media/ZDT1/0:  VERDE   (exit 0)
```
(sem `--piso`: `moead_media ∉ PISOS_ONLINE` ⇒ auditado como config offline COM
surrogate — exige bloco de sonda 20000, geracao NULL, sigma_dict, ⑦.)

### 3.2 GATE 2 — `final_eval.py --check` (env_main) ×3
```
$ENV_MAIN scripts/final_eval.py --exp off --alg moead_media --problema <P> --semente 0 --check
→ MMF1:  [OK] 50 finais, 8 ND pós-real, f reproduz problems.py, X reconstituível da ③ ger 801  · VERDE
→ DTLZ2: [OK] 105 finais, 53 ND pós-real, ...,                  X reconstituível da ③ ger 381  · VERDE
→ ZDT1:  [OK] 50 finais, 29 ND pós-real, ...,                   X reconstituível da ③ ger 801  · VERDE
```
> `final_eval` roda no **env_main** (py3.11 tem `typing.Literal` nativo; no env_b5
> cru o script — que não aplica o shim do runner — falha no import do pymoo). O
> `f` de `problems.py` é analítico e determinístico ⇒ reproduz o `f` gravado pela
> ⑦ (escrita no env_b5) na tolerância do float32. (Mesmo caminho do b5.)

### 3.3 GATES 3+4+5 — suíte `test_piso_off` no env_b5 (`PISO_SLOW=1`)
```
PISO_SLOW=1 MPLBACKEND=Agg PYTHONHASHSEED=0 $ENV_B5 -m unittest tests.test_piso_off -v
→ Ran 12 tests in 171.161s · OK   (0 skips — todos rodam no env_b5)
```
- `test_determinismo_bit_a_bit` (gate 3): 2 runs MMF1 mesma semente ⇒ ⑦ E ③-busca
  idênticas (`pandas.equals`, NaN-aware).
- `test_sonda_NAO_perturba_a_busca` (gate 4): sonda ON vs OFF ⇒ ⑦ E ③-busca idênticas.
- `test_sete_camadas_e_invariantes`: 7 camadas; sonda=20000 geracao NULL; **σ NULL
  em TODA a ③** (busca e sonda); μ preenchido; busca geracao 1..n_ger, cru,
  real_solution_id NULL; ④=1 linha com `tempo_fit_s` REAL; manifesto com sigma_dict.
- `TestGanchos`: `MOEA_D` de `ProbMOEAD` (MOEAD_select + arquiva); root-first; fix pyDOE.
- `TestPuros` (7): identidade, alg_id=21 vs seeds.json, dispatch-guard, registros
  offline, sigma_dict (σ NULL/DI-16.1, motor MOEAD_select, N 50/105/DI-16.4),
  `_null_sonda_geracao`.

### 3.4 GATE 6 — módulo isolado na suíte env-main
```
$ENV_MAIN -m unittest tests.test_piso_off -v → Ran 12 tests · OK (skipped=5)
```
(7 puros rodam; 2 ganchos + 3 slow SKIPPED limpos — `VENDOR_OK=False` em py3.11.)

### 3.5 Cortesia — suíte env-main COMPLETA com o módulo presente (Fase B é a vinculante)
```
$ENV_MAIN -m unittest discover -s tests → Ran 321 tests · OK (skipped=22) · exit 0
```
Baseline 309/17 → 321/22 = +12 coletados (7 puros rodam, 5 pulam). Sem regressão,
sem falha na faixa da sessão c311 concorrente.

---

## 4. Timings (para a curva de custo — §17.6; wall env_b5, 1 core)
| config | n_dataset | wall_run | nota |
|---|---|---|---|
| MMF1  | 61  | 36.6 s  | GP pequeno (2 obj) |
| DTLZ2 | 371 | 46.2 s  | 3 GPs (M=3) |
| ZDT1  | 929 | 112.4 s | fit domina (GP O(n³), 929 pts) |

`tempo_fit_s` REAL gravado na ④ (1 linha/run) — o piso offline TREINA (DI-16.1);
contrasta com os 4 pisos ONLINE (`tempo_fit_s`=NULL, sem modelo). ZDT1: fit=49.7 s
(GP em 929 pts domina) vs busca=55.2 s; MMF1 fit=0.13 s.

---

## 5. FASE B — WIRING (2026-07-23, mesma sessão; torre liberou)

**5.1 dispatch** — `src/experiment.py:163` descomentado:
`'moead_media': ('src.piso_offline','run_piso_offline','standalone')`. Já estavam
prontos: `VENV_ONLY_ALGS ∋ moead_media` (standalone_harness:87) e
`alg_to_env.moead_media = env_b5` (envs.json:266). Nada em `requirements/**`.

**5.2 accept** — `scripts/accept.py::check_r3_piso_off` (molde `check_r3_b5`) + bloco
CLI `R3-piso-off` antes do catch-all F0-01. Deltas do piso conferidos: σ_* NULL em
TODA a ③, μ_* preenchido, N=lattice b5m (50/105), ④=1 linha tempo_fit_s real.
```
$ENV_MAIN scripts/accept.py R3-piso-off --alg moead_media --problema <P> --semente 0 --exp off
→ MMF1 VERDE · DTLZ2 VERDE · ZDT1 VERDE   (11 checks OK cada; exit 0)
```
Exemplo (MMF1): "③ piso 'b5 sem σ': μ_*=2 (sem nulo) · σ_*=2 (todos NULL)" · "N(pop
última ger 801)=50 esperado=50 (M=2)" · "④ 1 linha tempo_fit_s=[0.127]".

**5.3 e2e do dispatch** (precedente c311-B):
```
$ENV_MAIN -c "from src import experiment; experiment.run('moead_media','MMF1',0,exp='off')"
→ DISPATCH_RESULT: {... n_final:50, mode:12, executavel_filho:.../env_b5/bin/python,
   pin_filho:OMP/OPENBLAS/MKL/NUMEXPR=1}   (status ok)
→ ⑦ sha256 ANTES(direto)==DEPOIS(dispatch) = 1131114f… → BIT-IDÊNTICA ✓
→ ③ sha256 idêntica ✓
```

**5.4 teste compartilhado atualizado** — `tests/test_r3_harness.py::
test_experiment_run_roteia_venv_only_para_subprocesso`: a cobaia `moead_media`
("venv-only não-registrado") esgotou com o dispatch ligado; reescrito p/ forçar
interpretador inexistente (prova o roteamento via `FileNotFoundError` no spawn, sem
rodar o piso). Ver REPASSE §B7.

**5.5 revisão adversarial (workflow próprio) — 2 achados MINOR corrigidos:**
- F1: `sigma_dict['sigma_*']` reafirmava "mesmo GP, mesmo μ" (contradizia `modelo`,
  DI-28). Reescrito → "MESMA ESPECIFICAÇÃO, treino independente".
- F2: teste da ④ não guardava DI-13.10. Asserções adicionadas.
- Pilotos ×3 RE-RODADOS (manifesto c/ sigma_dict corrigido): resultados IDÊNTICOS
  (fe/n_ger/n_final/n_nd) · ⑦ byte-inalterada.

**5.6 fechamento:**
```
$ENV_B5  PISO_SLOW=1 -m unittest tests.test_piso_off      → Ran 12 · OK (gates 3/4/5)
$ENV_MAIN -m unittest discover -s tests                   → Ran 321 · OK (skipped=22)
$ENV_MAIN scripts/preflight.py                            → exit 0
```

**Matriz final (Fase B):**
| config | accept | e2e dispatch | ⑦ bit-idêntica |
|---|---|---|---|
| MMF1  | 🟢 | 🟢 (env_b5 subprocess) | 🟢 `1131114f…` |
| DTLZ2 | 🟢 | — | — |
| ZDT1  | 🟢 | — | — |
