# R3-piso-off — Piso OFFLINE MOEA/D-média (`moead_media`, DESDEO mode 12), OFFLINE

> **Cartão único** desta sessão (1 sessão = 1 cartão): cobre SÓ o `moead_media`
> (mode 12 = Gen-MOEA/D PBI). Nenhum outro algoritmo tocado. Data: 2026-07-23.
> Runner: `src/piso_offline.py`. Env: `env_b5`. **FASE A** (só arquivos meus) — a
> Fase B (wiring em `experiment.py`) aguarda comando do autor.

## 0. Veredito
`src/piso_offline.py::run_piso_offline` implementa o piso offline `moead_media` no
regime OFFLINE, sobre o `standalone_harness` (molde DIRETO = `src/b5_prob.py`, o
cartão irmão). **Todos os gates da Fase A VERDES** (§6). A fidelidade é validação
MANUAL do autor a posteriori (D97) — não entra aqui.

O piso é, por desenho (D77/DEF-E3), **a ablação cirúrgica do b5**: MESMO motor
(MOEA/D do DESDEO), MESMO surrogate (SurrogateKriging), MESMO orçamento (40k
aval-surrogate); muda **só a seleção** — mode 12 usa `MOEAD_select` (decomposição
PBI, só a média), o b5m (mode 72) usa `ProbMOEAD_select` (comparação MC
probabilística). É **"o b5 sem σ"**.

## 1. Fase 0 — gate de ambiente (D80/D81 — provas, zero instalação)
- `envs.json`: `alg_to_env.moead_media = env_b5` ✅ (o MESMO venv do b5, pronto).
- **env_b5 RODA o desdeo mode-12** ✅ (prova nova desta sessão): `MOEA_D` de
  `desdeo_emo.EAs.ProbMOEAD` (root-first), `SurrogateKriging`, `DataProblem`,
  sonda offline S=20000, filtro ND (pymoo 0.6.1.2 + shim `typing.Literal`),
  `OFFLINE_CONFIGS ∋ moead_media`. sklearn 0.21.3 · pandas 1.3.5 · pyarrow 12.0.1.
- Artefatos: `data/datasets/{MMF1,DTLZ2,ZDT1}/ds_*_0.parquet` (61/371/929 = 31D−1)
  + `data/sonda/*.parquet`. Vendored `algorithms/b5_Prob-RVEA/desdeo_*`.
- **Suíte env-main: 309 OK (skipped=17)** + **preflight exit 0** (baseline, antes
  de começar). Âncoras `b5-mode72-kde` / `b5-mode7-archive` = APLICADO (INERTES
  p/ o mode 12 — §5).
- Sementes: `seeds.json` **alg_id `moead_media` = 21** (READ-ONLY); `seed_base` sem
  offset D22 ⇒ base = semente. Derivadas dos helpers D62/D91.

## 2. Decisões cravadas / herdadas (o autor delegou; ver REPASSE p/ ratificações)
1. **σ NULL na ③ (busca E sonda)** — DI-16.1 (`sigma_* NULL`) + CONTRATO §3.2
   (`mu_* preenchido; sigma_* NULL`). O piso reporta SÓ μ. A linha OUTPUTS do
   cartão dizia "σ = desvio do GPR" (resíduo copiado do sigma_dict do b5) —
   sobreposta por DI-16.1. **CONFIRMADO PELA TORRE (2026-07-23): contradição do
   prompt resolvida por PRECEDÊNCIA — definitivo, sem re-trabalho.**
2. **Mode 12 = `MOEA_D` de `desdeo_emo.EAs.ProbMOEAD`** (PBI + `MOEAD_select`,
   arquiva ind/obj/unc por geração). ⚠ há um SEGUNDO `MOEA_D` em
   `desdeo_emo/EAs/MOEAD.py:22` (default TCH, `_next_gen` NÃO arquiva) — a
   armadilha; `Main_Execute.py:21/115` confirma a de ProbMOEAD.
3. **N = o lattice do b5m** (DI-16.4): 50 vetores em M=2 / 105 em M=3 — HERDADO
   sem override (`lattice_resolution=None`), IDÊNTICO ao b5m. NÃO 100.
4. **Semeadura pela convenção D62/seeds.json** com o `alg_id` (canônica,
   anti-descompasso; mesma escolha ratificada no b5).
5. **Sonda geracao=NULL** carimbada pós-hoc no buffer (DI-13.5; precedente
   `b5._null_sonda_geracao` / `c149._stamp_c3_sonda`).
6. **④ = 1 linha, `tempo_fit_s` REAL** (DI-16.1: o piso offline TREINA um GP).
7. **Shim pyarrow do b5 OMITIDO** — `doe.py` já é pyarrow-12-safe (DI-26); provado
   ao vivo (`load_offline_budget` roda limpo no env_b5).

## 3. O runner — `src/piso_offline.py`
Molde offline (`b5_prob.py`) com o motor como CAIXA-PRETA. **Delta líquido vs o
b5m:** (a) importa `MOEA_D` (não `ProbMOEAD`); (b) `_ALG_ID=21`, `_MODE=12`; (c)
`_predict` devolve `(mu, None)` (σ NULL); (d) linhas de busca com `sigma=None`;
(e) `_sigma_dict` reescrito; (f) strings `modelo_flag`/`ALGO_VERSION`. **Zero**
mudança de construtor, **zero** patch vendorizado novo, **zero** `population_size`.

Fluxo:
1. Shim `typing.Literal`; `import standalone_harness as H` (pina threads D79) ANTES de numpy.
2. Seeds D62/D91: `base=seed_base(alg,s)` (=s); `random`/`np.random.seed` via
   `iteration_seed(base, 21, 0, uso)`.
3. `_import_vendored()`: stub pygmo → root vendorizado A FRENTE do sys.path →
   `DataProblem, SurrogateKriging, MOEA_D` (confere root-first) + fix pyDOE.
4. `load_offline_budget` (① = dataset, orçamento esgotado) + `load_sonda(offline)`.
5. `DataProblem(1-based, bounds REAIS via H._bounds)` → `problem.train(SurrogateKriging)`
   (kernel/alpha/n_restarts fixos; treino ÚNICO) → `buf.add_timing` (④ 1 linha).
6. `_predict(X)=problem.evaluate(X,use_surrogate=True)→(.objectives μ, None)` (σ NULL).
7. `emit_sonda_block` (1 bloco, S=20000, μ/σ=NULL) FORA do laço → geracao=NULL pós-hoc.
8. `MOEA_D(problem, use_surrogates=True, n_gen_per_iter=10, total_function_evaluations=40000)`
   → `with offline_guard: while continue_evolution(): iterate()`.
9. Replay dos arquivos por geração (`individuals/objectives_archive`) → ③ busca
   (`regime='offline'`, μ, **σ=None**, cru, real_solution_id=NULL) + ⑥ (DI-10 por gen).
10. ⑦ __final: `problems.evaluate_problem` (1× na verdade, fora do orçamento) + ND
    filtrado DEPOIS → `write_final` **SEM `nd_pos_real`** (ele calcula na vista
    float32). pop_final = última geração gravada na ③ (reconstituível — DI-16.16).
11. `write_run_outputs(status=ok, motivo_parada=orcamento, q=1, sigma_dict, regime=offline)`.

## 4. Outputs (nasce retrofitado — iguais ao b5, com σ NULL)
① dataset (CP x_hash+f_hash) · ② vazia (DI-16.17, real_solution_id=NULL) · ③ busca
por geração + SONDA offline (1 bloco 20000, geracao=NULL, ordem do artefato,
fe_treino_max, σ NULL) · ④ 1 linha (fit real) · ⑤ manifesto (sigma_dict completo)
· ⑥ jsonl DI-10 (exceções offline) · ⑦ __final (write_final SEM nd_pos_real).

## 5. Patches vendorizados — INERTES para o mode 12 (confirmado)
- `b5-mode72-kde` (`ProbMOEAD_select.py`): o mode 12 usa `MOEAD_select` (arquivo
  distinto) — não entra no caminho.
- `b5-mode7-archive` (`BaseEA._next_gen`): o `MOEA_D._next_gen` (ProbMOEAD.py:134-176)
  SOBRESCREVE `BaseDecompositionEA._next_gen` sem `super()` — não executa.
- A ⑦ nasce reconstituível da ③ **NATIVAMENTE** (o próprio `MOEA_D._next_gen`
  arquiva pós-replace por geração) — sem necessidade do patch-archive do b5r.
- **Nenhum arquivo vendorizado editado.** Único gancho runtime = o fix pyDOE do b5
  (injeção do RandomState global no `lhs`), aplicado por monkey-patch local.

## 6. Gates de aceite da FASE A (re-executados AO VIVO — ver RELATORIO)
Todos os runs OFFLINE, semente 0, `PYTHONHASHSEED=0` + threads pinadas, FE_final = 31D−1.

| config | D | M | FE | n_ger | n_final | n_nd_pos_real | auditar | final_eval |
|---|---|---|---|---|---|---|---|---|
| MMF1  | 2  | 2 | 61  | 801 | 50  | 8  | 🟢 | 🟢 |
| DTLZ2 | 12 | 3 | 371 | 381 | 105 | 53 | 🟢 | 🟢 |
| ZDT1  | 30 | 2 | 929 | 801 | 50  | 29 | 🟢 | 🟢 |

- `n_ger`/`n_final` **IDÊNTICOS ao b5m** (50/105/50) — a ablação é cirúrgica (mesma
  geometria; só a seleção difere ⇒ `n_nd_pos_real` difere). Prova viva da DI-16.4.
- **Determinismo (gate 3):** 🟢 — 2 runs MMF1 mesma semente ⇒ ⑦ + ③-busca bit-a-bit.
- **Não-perturbação (gate 4):** 🟢 — MMF1 sonda-ON vs OFF ⇒ ⑦ + ③-busca bit-a-bit
  (NaN-aware, pois σ = NULL/NaN em toda a ③).
- **`tests/test_piso_off.py` (gate 5):** 🟢 no env_b5 (`PISO_SLOW=1`, 12/12 OK) E
  env-main-safe (skips limpos sem vendor).
- **Módulo isolado na suíte env-main (gate 6):** 🟢 (`Ran 12, OK skipped=5`).
- Cortesia (a suíte COMPLETA é da Fase B): env-main **321 OK (skipped=22)** com o
  módulo presente — sem regressão.

## 7. Rituais / coexistência (sessão R3-c311 concorrente na Fase B dela)
NUNCA `git push` · NUNCA `git add -A` · não toquei em `experiment.py`, `accept.py`,
`requirements/**`, `claude_code_context/**`, `algorithms/**` (vendored),
`src/*` compartilhado, REGISTRO/SPEC/PROGRESSO, nem testes alheios. `data/experiments/`
é gitignored ⇒ os outputs dos pilotos ficam LOCAIS (não commitados). Commits
`[R3-piso-off]` só da Fase A: `src/piso_offline.py`, `tests/test_piso_off.py`,
`handoff/R3-piso-off*.md`.

## 8. Fase B — WIRING (COMPLETA · 2026-07-23, mesma sessão, torre liberou)
- **`experiment.py:163`** — dispatch `moead_media → run_piso_offline` DESCOMENTADO
  (`_DISPATCH_LOADERS`). `VENV_ONLY_ALGS`/`alg_to_env` já continham moead_media.
- **`scripts/accept.py`** — `check_r3_piso_off` ADITIVO (molde `check_r3_b5`, com
  os deltas do piso: σ_* NULL em TODA a ③ · ④ 1 linha tempo_fit_s real · N =
  lattice b5m 50/105) + bloco de dispatch do cartão `R3-piso-off` antes do
  catch-all F0-01. **accept R3-piso-off ×3 (MMF1/DTLZ2/ZDT1) = VERDE.**
- **`requirements/**`** — NADA mudado (não instalei nada; env_b5 intocado).
- **e2e do dispatch:** `experiment.run('moead_media','MMF1',0,exp='off')` → subprocesso
  `env_b5` (executavel_filho confirmado, threads pinadas) → status ok · **⑦ BYTE-
  IDÊNTICA** ao piloto direto (sha256 `1131114f…`).
- **`tests/test_r3_harness.py`** — 1 teste ATUALIZADO (necessário): o
  `test_experiment_run_roteia_venv_only_para_subprocesso` usava `moead_media` como
  cobaia "venv-only não-registrado"; com o dispatch ligado essa cobaia se esgota
  (os 4 venv-only estão TODOS registrados). Reescrito para forçar um INTERPRETADOR
  inexistente ⇒ prova o roteamento (FileNotFoundError no spawn, nunca
  NotImplementedError) SEM rodar o piso. Ver REPASSE §B7.
- **Fechamento:** suíte COMPLETA env-main **Ran 321 · OK (skipped=22)** · preflight
  **exit 0** · accept ×3 VERDE.

## 9. Revisão adversarial (workflow próprio) — 2 achados MINOR corrigidos
- **F1 (piso_offline.py sigma_dict):** o campo `sigma_*` reafirmava "mesmo GP, mesmo
  μ" — contradição com o campo `modelo` (DI-28: treino INDEPENDENTE, nunca idêntico;
  alg_id 21≠18 semeia RNGs distintos ⇒ μ não byte-igual). Reescrito p/ "MESMA
  ESPECIFICAÇÃO, treino independente; μ da mesma especificação, não presumido-igual".
- **F2 (test_piso_off ④):** o teste não guardava a DI-13.10 (`tempo_geracao_s` EXCLUI
  a sonda) nem `n_acumulado=n_ds`. Adicionadas as asserções (geracao == fit+busca;
  sonda separada > 0; n_acumulado == n_dataset). Pilotos re-rodados; tudo VERDE.

**CARTÃO FECHADO — com este cartão, os 21/21 configs do estudo estão implementados.**
