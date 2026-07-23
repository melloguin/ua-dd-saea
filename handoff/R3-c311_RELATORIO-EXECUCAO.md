# R3-c311 — RELATÓRIO DE EXECUÇÃO (o COMO)

> Sessão de implementação do cartão **R3-c311 · TGPR-MO** (treed-GP/GPy, OFFLINE, no Mac).
> Faixa em 2 fases (coexistência com a sessão R3-b5 ATIVA). **Esta é a FASE A** — código
> próprio + pilotos + provas, SEM tocar a faixa do b5/torre. O wiring (dispatch/accept/locks)
> é a FASE B, sob gatilho do autor após o commit do b5.

## 0. Estado da faixa no arranque (coexistência)
`git status --porcelain` no início mostrou APENAS a faixa do b5 (esperado, A.7):
`algorithms/b5_Prob-RVEA/**` (BaseEA.py, ProbMOEAD_select.py), `anchors.json`, `envs.json`,
`requirements/{PROVISIONAMENTO.md,env_b5.txt,locks/env_b5.lock.txt}`, `?? src/b5_prob.py`.
**Nenhum arquivo meu tocado por terceiros.** `scripts/preflight.py` = **VERDE** (exit 0),
com os lacres do b5 já APLICADOS e o meu vendored `c311_tgprmo` intacto
(content-hash `e3b3f802dad9`) — confirmando A.7 e a razão dos ganchos por monkeypatch.
Durante toda a sessão os 3 pilotos do b5 (`b5m` MMF1/DTLZ2/ZDT1) rodaram em paralelo;
meus runs (1 core cada, sequenciais) coexistiram sem conflito (D79).

## 1. FASE 0 — gate de ambiente (env_c311 + artefatos)
- **env_c311 validado:** py3.8.20 x86_64/Rosetta · GPy 1.9.9 · numpy 1.20.2 · sklearn 1.1.2 ·
  scipy 1.10.1 · Pillow 9.5.0 (<10) · pyarrow 17.0.0 · graphviz 0.20.3 (import hard satisfeito) ·
  matplotlib 3.7.5 (sempre `MPLBACKEND=Agg`).
- **pymoo AUSENTE ⇒ instalado `pymoo==0.6.1.2`** (pré-autorizado, Fase 0 item 2) COM constraints
  do freeze do env (o núcleo validado NÃO se moveu: numpy/scipy/sklearn/GPy/pyarrow intactos —
  conferido). Build **puro-python** (`py3-none-any.whl`, sem Cython). py3.8 tem `typing.Literal`
  nativo ⇒ o shim do b5 NÃO foi necessário.
- **Provas de aceitação (ao vivo):** (1) GP treina+prediz; (2) ⑦/filtro-ND via
  `problems._nds_filter(evaluate_problem(...))` importa e roda (o warning "Compiled modules
  can not be used" é o pymoo puro-python — esperado, só velocidade); (3) `load_sonda('MMF1',
  regime='offline')` OK; (4) os 3 datasets `ds_{MMF1,DTLZ2,ZDT1}_0.parquet` carregam com
  x_hash **E** f_hash conferidos.
- **Datasets e sonda já existiam** (committados; D90 = carregar, nunca gerar) ⇒ nada regenerado.
- **Suíte env-main:** `Ran 295 tests · OK (skipped=7)` (exit 0). **preflight VERDE.**
- **Seeds:** `seeds.json:alg_id.c311 = 19`. O catálogo `uso_id_catalogo` NÃO lista o c311; o
  `_default` (uso_id=0) cobre "algoritmos sem RNG concorrente do harness" — que é o caso (a
  sonda é determinística, sob `preserve_all_rng`). Aplicada a receita L.17: `s = iteration_seed(
  seed_base('c311',semente), 19, 0, 0, bits32=True)` e `np.random.seed(s); random.seed(s)` (o
  MESMO s p/ os dois — literal da L.17). **Sinalizado à torre** (§ REPASSE).

## 2. Entendimento (workflow read-only, 8 leitores + síntese)
Antes de codar, um workflow multi-agente (read-only) digeriu, em paralelo: `standalone_harness`
(APIs a reusar) · `export`/`manifest`/`audit_log` (schemas) · `e81_qpots` (padrão dos ganchos) ·
`c122`+`naoperturbacao` (prova §3.1) · o vendored `c311_TGPR-MO/**` (fluxo + mecanismo) ·
`REGISTRO A10–A14` + REPASSEs (precedentes) · seeds/envs/gates. 7/8 leitores + síntese fecharam;
2 falharam no cap de output e foram cobertos por leitura direta minha (harness API + gates).
Verificações-chave feitas **na fonte** (não confiei só na síntese): DI-16.12 (2 blocos de sonda)
confirmado no REGISTRO linha 734-737; `_calculate_fitness` do `APD_Select_constraints` (a
seleção "mean" lê SÓ `pop.fitness`, nunca `uncertainity`) confirmado no vendored; contador
`_current_gen_count` inclui o +1 do `_refresh_population` (RVEA.py:191-205).

## 3. Implementação — `src/c311_tgprmo.py` (molde run_stubr3 · ganchos e81)
Fluxo OFFLINE 2-fases, VENDOR INTOCADO, tudo por monkeypatch em runtime:
- **Import root-first + shim:** `sys.path.insert(0, VENDOR_ROOT)` resolve `desdeo_*` para a cópia
  do c311; **shim `optproblems`** (o `desdeo_problem/__init__` o importa avidamente via
  `testproblems`, que o nosso caminho `DataProblem` nunca usa; o env não o tinha — evitou
  instalar pacote não-autorizado, respeitando D80). **pygmo AUSENTE** do caminho (DI-16.14,
  verificado em runtime). Prova root-first: `desdeo_problem.__file__` sob VENDOR_ROOT.
- **GANCHO 1 — σ (B15.5):** `_patched_predict` devolve `(μ, σ)` com μ BYTE-idêntico ao stock
  (mesma expressão `predict(...)[0][0]`) e σ = `sqrt(max(var,0))` (σ, NUNCA σ² — DI-16.9), NaN
  nas folhas só-árvore. Flui p/ `population.uncertainity`; a seleção "mean" a ignora ⇒
  não-perturbação por construção.
- **GANCHO 2 — predict_batch (DI-16.13):** `_predict_batch` vetoriza por FOLHA (μ+σ) p/ a sonda
  de 20.000 (o `predict` canônico é 1-ponto-por-linha). NÃO copia o `predict_new` (outra classe).
- **GANCHO 3 — snapshot/geracao (C311-11):** wrappers de `_next_gen`/`_refresh_population`
  capturam a pop selecionada por geração p/ a ③, com o contador ÚNICO e monotônico atravessando
  as 2 fases (build = `_current_gen_count`; final = `último_build + _current_gen_count`).
- **2 blocos de sonda (DI-16.12):** `treedGP_build` (fim da construção) e `treedGP_final` (fim
  do run), AMBOS `geracao=NULL`, construídos À MÃO via `surrogate_row(None,…)` — o
  `emit_sonda_block` força `int(geracao)` e o `auditar` reprova sonda offline com geração não-nula.
- **⑦:** todos os finais avaliados 1× na verdade; ND filtrado DEPOIS (DI-13.9); reconstituível
  da ③ (última geração `treedGP_final`, `origem_linha`).
- **teto_s** opcional (aborto limpo ⇒ `status='failed'`, `motivo_parada='teto_wall'`).
- **emitir_sonda** (kwarg) desliga os 2 blocos — só p/ a prova de não-perturbação.

## 4. 🔴 DOIS achados de DETERMINISMO (o debugging que valeu a sessão)
O smoke MMF1 fechou de 1ª (28s, 7 camadas, contador 1..1204, ② vazia, 2 sonda). Mas o gate de
**determinismo** (2 runs ⇒ ⑦ bit-a-bit) REPROVOU. Diagnóstico em camadas localizou DUAS causas —
NENHUMA no algoritmo, ambas de AMBIENTE, corrigidas por gancho/pin, VENDOR intocado:

1. **BLAS multi-thread (D79 não aplicado na invocação direta).** O `pin_runtime` do harness
   NÃO limita threads em env SEM torch (b5/c311) — só REGISTRA; o pin autoritativo é o
   `run_in_venv` (env limpo), que a invocação DIRETA (padrão dos pilotos) não usa. Sem
   `OMP/OPENBLAS/MKL=1`, o OpenBLAS rodou 8 threads ⇒ ruído de redução que 1000 gerações de RVEA
   amplificam. **Fix:** env-vars no topo do módulo (belt) + `threadpoolctl.threadpool_limits(1)`
   em runtime (suspenders, robusto à ordem de import — presente no env_c311). Verificado:
   openblas 8→1.

2. **DRIFT do pyDOE (a causa MAIOR).** O `env_c311` resolveu um pyDOE NOVO (o pip do
   PROVISIONAMENTO §3 instala `pyDOE` SEM pin). A pop inicial do RVEA usa o design `"LHSDesign"`
   (Population.py:116) ⇒ `lhs(n, samples)` SEM seed. No pyDOE novo, `lhs(seed=None)` usa um
   `RandomState` PRÓPRIO (entropia do SO), NÃO o `np.random` global. Prova (diag): o estado
   global fica IDÊNTICO após `RVEA.__init__`, mas a pop inicial VARIA ⇒ não-determinismo (diff
   de 0.28, estrutural). A receita L.17 assumia o pyDOE ANTIGO (lhs pelo global). **Fix — GANCHO
   4:** `_lhs_determinismo` injeta `seed=` derivado do `np.random` global (que o runner semeia
   por iteration_seed) ⇒ o lhs volta determinístico e atado à semente. **Sinalizado à torre**
   (pinar o pyDOE OU ratificar o gancho — fidelidade da init-pop é D97, do autor).

Um TERCEIRO "falso-positivo" no gate de **não-perturbação**: o `assertEqual(dict)` reprovava
`NaN==NaN` espúrio (a ③ tem σ=NaN nas folhas só-árvore). Era bug do TESTE, não do runner (o
diagnóstico coluna-a-coluna, NaN-aware, mostrou a ③-busca IDÊNTICA com/sem sonda). Corrigido p/
comparação `pandas.DataFrame.equals` (NaN co-localizado = igual).

## 5. tests/test_c311.py — 14 testes (env-main-safe)
- **Puros (4, env-main):** identidade (alg_id=19); `_max_busca_geracao`; sonda offline com
  `geracao=NULL`; punição de ordem quebrada (join posicional R4.5).
- **Ganchos (7, @skipUnless VENDOR_OK ⇒ env_c311):** root-first sem pygmo; stock descarta σ;
  μ do patch = stock byte-a-byte; predict_batch = patched (na precisão float32 gravada); σ =
  sqrt(var) NUNCA σ² (DI-16.9); σ=NaN em folha só-árvore; hooks restauram o vendor bit-a-bit.
- **Runs completos (3, @skipUnless VENDOR_OK+C311_SLOW ⇒ env_c311):** 7 camadas + invariantes
  (sonda geracao-NULL, 2×20000, ② vazia, contador 1..n); determinismo bit-a-bit; não-perturbação
  §3.1 (sonda off vs on ⇒ ⑦ e ③-busca idênticas — NaN-aware).
- **Sonda LEVE `_vendor_ok`:** `import GPy` (só o env_c311 o tem) — a suíte env-main NUNCA dispara
  o overlay do vendor. Confirmado: env-main `Ran 14 · OK (skipped=10)`; env_c311 `Ran 14 · OK
  (skipped=1)` (o skip é a folha-só-árvore no modelo minúsculo — coberta no run completo).

## 6. Pilotos oficiais (exp='off', semente 0) — DETERMINÍSTICOS
Re-rodados após os fixes (os 1os, pré-fix, eram realizações não-determinísticas):

| problema | status | n_geracoes | ③ linhas | ② | sonda | n_final | ND-real | wall |
|---|---|---|---|---|---|---|---|---|
| MMF1  | ok | 1204 | 90124  | 0 | 2 | 46 | 10 | 29 s |
| DTLZ2 | ok | 1204 | 131779 | 0 | 2 | 84 | 77 | 70 s |
| ZDT1  | ok | 1204 | 96467  | 0 | 2 | 50 | 50 | 49 s |

Todos: `cp_init_ok=true`, `fe_final=n_dataset` (o dataset É o orçamento), `n_geracoes=1204`
(build 4×51=204 + final 1000; Imax=N/(10D)→ceil=4 nos 3), ② vazia (DI-16.17), 2 blocos de sonda.

## 7. Gates (re-executados ao vivo — ver REPASSE p/ os comandos e saídas)
`auditar.py` VERDE ×3 · `final_eval.py --check` VERDE ×3 · determinismo ✅ · não-perturbação
✅ · suíte env_c311 (SLOW) ✅ · suíte env-main + preflight VERDES (Fase 0).

## 8. Fronteira da Fase A (o que NÃO fiz — é Fase B/torre)
Descomentar o dispatch (`experiment.py:156`), branch aditivo no `accept.py`, registrar o pymoo
no lock/PROVISIONAMENTO, materializar patch formal (se houver) + âncora + re-lacre, `accept.py
R3-c311 ×3`, suíte completa + preflight no fechamento. **Aguardando o commit do b5 e o comando
do autor.**
