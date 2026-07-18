"""Runner do c262 — qNEHVI (BoTorch OFICIAL 0.18.1) sobre o harness R2-00.

Cartão R2-c262 (receita L.10 na íntegra; §22.3/N.1; I.10). O algoritmo é o
qLogNEHVI do BoTorch 0.18.1 ("qNEHVI" = qLogNEHVI na formulação log — E.2);
NADA é reimplementado: modelo, aquisição e otimização são as classes oficiais.
Este módulo só INTEGRA (adapter §5.5 + FEBudget + export §17) e INSTRUMENTA
(jsonl §17.5/S.7 + ③ com μ/σ do posterior + curva §17.6). **SEM julgamento de
fidelidade (D97)** — a validação é MANUAL do autor, a posteriori, em lote.

Receita por iteração (L.10 — a fonte; parâmetros também em params.json):
  - `torch.manual_seed(h(run,it))` ANTES de construir modelo+acqf (uso_id 0);
    h1 = seed do SobolQMCNormalSampler (uso_id 1); h2 = seed do optimize_acqf
    (uso_id 2) — fórmula D62/D91 do seeds.json, truncada a 32 bits.
  - Modelo: `SingleTaskGP` POR OBJETIVO com `train_Yvar=1e-6` (B8.6a, noiseless
    — opera como qEHVI, achado justo D40) + `covar_module =
    get_matern_kernel_with_gamma_prior(d)` (🔵 ARTIGO/D30 — Matérn 5/2 ARD,
    rota Gamma-legada fiel ao paper) + `Standardize` (m=1 por objetivo);
    `ModelListGP`. **Refit from scratch por iteração** (D44 — re-MAP via
    `fit_gpytorch_mll`, sem warm-start).
  - Aquisição: `qLogNEHVI(sampler=SobolQMCNormalSampler(128, seed=h1),
    prune_baseline=True, alpha=0.0, cache_pending=True, max_iep=0,
    incremental_nehvi=True, cache_root=None, tau_relu=1e-6, tau_max=1e-3,
    fat=True, eta=1e-3)`; X_baseline = todo o ① em [0,1]^D.
  - `optimize_acqf(q=1, num_restarts=10, raw_samples=512,
    sequential=(q>1)=False, options={seed:h2, maxiter:2000,
    init_batch_limit:32}, return_best_only=False)` → os 10 candidatos dos
    restarts (③) + escolhido = argmax da acqf.

Ref-point da AQUISIÇÃO (interno — a MÉTRICA usa o ref normalizado D69): FIXO
POR PROBLEMA, como no paper (Anexo J: `r = nadir − 0,1·(ideal−nadir)`, fixo,
Tab. 2 — ≡ `nadir + 0,1·(nadir−ideal)`, o "nadir×1,1" shorthand da SPEC/D69),
sobre o (ideal, nadir) CONGELADO da tabela S.5 (`src.metrics`), em escala
BRUTA (Anexo J: c262 = escala bruta) e negado p/ o espaço de maximização.

Política do kernel fusionado (DEF-L2/S.3#9): o 0.18.1 OFICIAL do PyPI TAMBÉM
embarca `csrc/logei_fused.cpp` (verificado byte-a-byte contra o wheel do PyPI
— a premissa "ausente do oficial" do S.3#9 está desatualizada; registrado no
handoff). O JIT usa `-march=native` (falha no clang/arm64 → fallback
silencioso; compilaria no Linux → numérica assimétrica Mac×Linux). Remédio da
DEF-L2 aplicado: **OFF EXPLÍCITO** (`_load_attempted=True`, `_C=None`) →
caminho Python puro determinístico nos 2 SOs; logado no jsonl e no manifesto.

③ (§17.3/§17.4 — política BoTorch): os candidatos avaliados nos RESTARTS por
iteração, com μ/σ do `model.posterior` sob `no_grad` (D86). O Standardize
des-transforma; o posterior vive em −f (maximização) e o μ é exportado como
`−mean` — **o sinal invertido nunca vaza para o export** (§5.5). O escolhido
aponta `real_solution_id` quando o FE foi de fato consumido.

②: membership do conjunto de treino (o arquivo real que o modelo VIU) por
iteração. §17.6: `add_timing(it, n_acumulado=bud.fe ANTES do infill, t_fit)`
IMEDIATAMENTE após o fit — a curva O(n³) (o dado-alvo do piloto) retém
inclusive o fit final da iteração interrompida pelo hard-stop (D61).

Guardas: hard-stop D21/D61 = fim NATURAL do laço (`BudgetExhausted`); stall de
cache-hit (D89: duplicata desperdiça o SLOT) com teto D60-b de 100 iterações
consecutivas sem FE ⇒ RuntimeError (pára-e-loga); projeção de wall-clock
(`max_wall_s`, p/ o teto de 8h do ZDT1 no piloto): fit ~ c·n³ ajustado nas
últimas iterações ⇒ estouro projetado aborta LIMPO (o jsonl retém a curva
§17.6 parcial) — a decisão de completar é da torre/autor (M7).

Módulo PESADO (torch/botorch) — importado LAZY pelo `_DISPATCH_LOADERS`.
"""

from __future__ import annotations

import time
import warnings

import numpy as np
import torch

from src import budget as _budget
from src import export as _export
from src import naming
from src.audit_log import AuditLogger
from src.botorch_harness import (
    BoTorchProblemAdapter,
    SnapshotBuffer,
    env_info,
    iteration_cleanup,
    iteration_seed,
    load_doe,
    pin_runtime,
    torch_seed_for,
    write_run_outputs,
)

#: alg_id canônico do c262 no `artifacts/seeds.json` (D91).
C262_ALG_ID = 9

#: catálogo uso_id do c262 (seeds.json/D91): 0 = torch.manual_seed da iteração
#: (modelo+acqf, L.10); 1 = SobolQMCNormalSampler; 2 = seed do optimize_acqf.
USO_MANUAL_SEED, USO_SAMPLER, USO_ACQF = 0, 1, 2

#: parâmetros da receita L.10 (espelho do params.json — Balde B congelado).
MC_SAMPLES = 128
NUM_RESTARTS = 10
RAW_SAMPLES = 512
TRAIN_YVAR = 1e-6
ACQF_OPTIONS_STATIC = {"maxiter": 2000, "init_batch_limit": 32}

#: D60-b (guarda de stall): teto de iterações CONSECUTIVAS sem consumir FE
#: (só duplicatas bit-a-bit — cache-hit D89). O watchdog pleno é do despachante.
MAX_STALL_ITERS = 100

ALGO_VERSION = "c262-qNEHVI/qLogNEHVI-botorch-0.18.1"


def disable_fused_kernel() -> dict:
    """DEF-L2/S.3#9: desliga EXPLICITAMENTE o kernel C++ fusionado do logei
    (`_load_attempted=True` com `_C=None` ⇒ o caminho fica Python puro,
    determinístico entre Mac (arm64, onde o JIT `-march=native` falharia com
    fallback silencioso) e Linux (onde compilaria → numérica assimétrica).
    Idempotente; retorna o estado p/ o manifesto/jsonl."""
    from botorch.acquisition.multi_objective import logei as _mo_logei
    _mo_logei._load_attempted = True
    _mo_logei._C = None
    return {"fused_kernel": "OFF-explicito (python puro; DEF-L2/S.3#9)",
            "_load_attempted": True, "_C_is_none": _mo_logei._C is None}


def acqf_ref_point(problema: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Ref-point da AQUISIÇÃO, fixo por problema (paper/Anexo J):
    `ref_f = nadir + 0,1·(nadir − ideal)` sobre o (ideal, nadir) congelado da
    tabela S.5 (`src.metrics.reference_bounds`), em escala BRUTA de
    minimização. Retorna `(ref_f, ideal, nadir)`; o motor (maximização) usa
    `−ref_f`. NÃO confundir com o ref normalizado da métrica (D69)."""
    from src import metrics as _metrics  # lazy — módulo F0-04 (leitura apenas)
    ideal, nadir = _metrics.reference_bounds(problema)
    ideal = np.asarray(ideal, dtype=np.float64)
    nadir = np.asarray(nadir, dtype=np.float64)
    ref_f = nadir + 0.1 * (nadir - ideal)
    return ref_f, ideal, nadir


def _build_models(train_X: torch.Tensor, train_Y_max: torch.Tensor):
    """Os modelos da receita L.10: `SingleTaskGP` POR OBJETIVO com
    `train_Yvar=1e-6` (B8.6a) + Matérn 5/2 ARD com prior Gamma (🔵 D30, rota
    fiel ao paper) + `Standardize(m=1)`, agregados num `ModelListGP`.
    `train_Y_max` já está em −f (maximização — §5.5)."""
    from botorch.models import ModelListGP, SingleTaskGP
    from botorch.models.transforms.outcome import Standardize
    from botorch.models.utils.gpytorch_modules import (
        get_matern_kernel_with_gamma_prior,
    )
    D = train_X.shape[-1]
    models = []
    for j in range(train_Y_max.shape[-1]):
        Yj = train_Y_max[:, j:j + 1]
        models.append(SingleTaskGP(
            train_X, Yj,
            train_Yvar=torch.full_like(Yj, TRAIN_YVAR),
            covar_module=get_matern_kernel_with_gamma_prior(D),
            outcome_transform=Standardize(m=1)))
    return ModelListGP(*models)


def _fit_models(model) -> int:
    """Refit from scratch por iteração (D44) via `fit_gpytorch_mll` oficial
    (max_attempts default; retries amostram dos priors → RNG torch, ancorado
    no manual_seed da iteração — L.10). Retorna o nº de warnings de retry/
    otimização capturados (fit-retries do jsonl S.7)."""
    from botorch.fit import fit_gpytorch_mll
    from gpytorch.mlls import SumMarginalLogLikelihood
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fit_gpytorch_mll(mll)
    return sum(1 for w in caught
               if "attempt" in str(w.message).lower()
               or "retry" in str(w.message).lower()
               or "optimization" in str(w.message).lower())


def _make_acqf(model, ref_max, X_baseline: torch.Tensor, h1: int):
    """A aquisição da receita L.10 NA ÍNTEGRA (§22.3 — parâmetros vinculantes;
    `cache_root=None` conforme o checklist/L.10)."""
    from botorch.acquisition.multi_objective.logei import (
        qLogNoisyExpectedHypervolumeImprovement,
    )
    from botorch.sampling.normal import SobolQMCNormalSampler
    return qLogNoisyExpectedHypervolumeImprovement(
        model=model,
        ref_point=list(ref_max),
        X_baseline=X_baseline,
        sampler=SobolQMCNormalSampler(
            sample_shape=torch.Size([MC_SAMPLES]), seed=h1),
        prune_baseline=True,
        alpha=0.0,
        cache_pending=True,
        max_iep=0,
        incremental_nehvi=True,
        cache_root=None,
        tau_relu=1e-6,
        tau_max=1e-3,
        fat=True,
        eta=1e-3,
    )


def _optimize_acqf_restarts(acqf, D: int, h2: int):
    """`optimize_acqf` da receita (q=1 ⇒ sequential=False) com
    `return_best_only=False` → TODOS os candidatos dos restarts (a ③ da
    política BoTorch §17.4) + os valores da acqf. Warnings de otimização
    contados (retry desloca o RNG — registrar, L.10/S.7)."""
    from botorch.optim import optimize_acqf
    bounds = torch.stack([torch.zeros(D, dtype=torch.float64),
                          torch.ones(D, dtype=torch.float64)])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cands, acq_vals = optimize_acqf(
            acqf, bounds=bounds, q=1,
            num_restarts=NUM_RESTARTS, raw_samples=RAW_SAMPLES,
            options={"seed": h2, **ACQF_OPTIONS_STATIC},
            sequential=False,          # sequential=(q>1); principal é q=1
            return_best_only=False)
    n_warn = sum(1 for w in caught
                 if "optimization" in str(w.message).lower()
                 or "trying again" in str(w.message).lower())
    return cands.detach(), acq_vals.detach(), n_warn


class _WallClockProjector:
    """Projeção do teto de wall-clock do piloto (ZDT1 ≤ ~8h): ajusta
    `t_fit ≈ c·n³` nas últimas iterações e projeta o restante do run
    (fits em n crescente + busca/aval ~constantes). NUNCA reduz orçamento —
    só decide abortar LIMPO quando a projeção estoura o teto."""

    def __init__(self, max_wall_s: float | None, t0: float, maxfe: int):
        self.max_wall_s = max_wall_s
        self.t0 = t0
        self.maxfe = maxfe
        self.samples: list[tuple[int, float, float]] = []  # (n, t_fit, t_iter)

    def add(self, n: int, t_fit: float, t_iter: float) -> None:
        self.samples.append((int(n), float(t_fit), float(t_iter)))

    def projection_s(self, n_now: int) -> float | None:
        """Segundos projetados p/ TERMINAR o run a partir de `n_now` FEs."""
        if len(self.samples) < 10:
            return None
        recent = self.samples[-5:]
        c = float(np.mean([tf / max(n, 1) ** 3 for n, tf, _ in recent]))
        other = float(np.mean([ti - tf for n, tf, ti in recent]))
        ns = np.arange(n_now, self.maxfe + 1, dtype=np.float64)
        return float(c * np.sum(ns ** 3) + max(other, 0.0) * len(ns))

    def exceeded(self, n_now: int) -> tuple[bool, float | None, float]:
        elapsed = time.time() - self.t0
        if self.max_wall_s is None:
            return False, None, elapsed
        proj = self.projection_s(n_now)
        if proj is None:
            return False, None, elapsed
        return (elapsed + proj) > self.max_wall_s, proj, elapsed


def run_c262(exp: str, alg: str, problema: str, semente, *,
             data_root: str = naming.DEFAULT_DATA_ROOT,
             enable_bucket: bool = False,
             max_wall_s: float | None = None, **_kwargs) -> dict:
    """Um run c262 (q=1) — assinatura padrão dos runners R2 (`experiment.run`
    repassa os kwargs). `max_wall_s` liga a projeção de teto do piloto (8h no
    ZDT1); estouro projetado ⇒ aborto limpo + RuntimeError (pára-e-loga D81).
    Retorna o dict de evidências (FE, iters, timing, curva §17.6)."""
    t0 = time.time()
    pinning = pin_runtime()
    env = env_info()                          # guarda N.2.3 (fork ⇒ RuntimeError)
    fused_policy = disable_fused_kernel()     # DEF-L2: OFF explícito
    # Artefato CONHECIDO do train_Yvar=1e-6 (B8.6a): o Standardize divide o
    # Yvar por std² e o gpytorch aplica o piso 1e-6 com um NumericalWarning
    # por modelo (~2/iteração — só ruído de stderr; a numérica é a documentada
    # do stack oficial). Filtrado aqui e REGISTRADO no header do jsonl.
    warnings.filterwarnings(
        "ignore", message="Very small noise values detected")
    semente = int(semente)

    doe_art = load_doe(problema, semente, data_root=data_root)
    ref_f, ideal_s5, nadir_s5 = acqf_ref_point(problema)

    log = AuditLogger.for_run(exp, alg, problema, semente,
                              data_root=data_root, append=False)
    try:
        return _run_c262_body(exp, alg, problema, semente, t0, pinning, env,
                              fused_policy, doe_art, ref_f, ideal_s5, nadir_s5,
                              log, data_root, enable_bucket, max_wall_s)
    except Exception:
        # D23/D60: parada anômala NUNCA silenciosa — footer failed no jsonl
        # (o despachante decide retry; o BudgetExhausted não chega aqui — é
        # capturado como fim NATURAL dentro do corpo, D61).
        import traceback
        log.footer(status="failed", stack=traceback.format_exc()[-2000:])
        raise
    finally:
        log.close()


def _run_c262_body(exp, alg, problema, semente, t0, pinning, env, fused_policy,
                   doe_art, ref_f, ideal_s5, nadir_s5, log, data_root,
                   enable_bucket, max_wall_s) -> dict:
    bud = _budget.FEBudget(D=doe_art["X"].shape[1], logger=log)
    adapter = BoTorchProblemAdapter(problema, bud)
    D, M = adapter.D, adapter.M
    buf = SnapshotBuffer()
    ref_max = (-ref_f).tolist()               # aquisição maximiza −f (§5.5)

    log.header(run_id=naming.run_id(exp, alg, problema, semente),
               alg=alg, alg_id=C262_ALG_ID, problema=problema, D=D, M=M,
               semente=semente, regime="online", maxfe=bud.maxfe,
               doe_hash=doe_art["doe_hash"], env=env, pinning=pinning,
               algo_version=ALGO_VERSION,
               acqf_ref_f=ref_f.tolist(), acqf_ref_max=ref_max,
               ref_fonte="S.5 fixo por problema (Anexo J: nadir+0,1·(nadir−ideal))",
               ideal_s5=ideal_s5.tolist(), nadir_s5=nadir_s5.tolist(),
               fused_kernel=fused_policy["fused_kernel"],
               warning_filter=("gpytorch 'Very small noise values' suprimido: "
                               "artefato esperado do train_Yvar=1e-6 (B8.6a) "
                               "sob Standardize (piso 1e-6 do gpytorch)"),
               params={"mc_samples": MC_SAMPLES, "num_restarts": NUM_RESTARTS,
                       "raw_samples": RAW_SAMPLES, "train_Yvar": TRAIN_YVAR,
                       "q": 1, "refit": "from-scratch/iter (D44)",
                       "kernel": "Matern-5/2-ARD gamma-prior (D30)",
                       "acqf": "qLogNEHVI L.10", "cache_root": None,
                       **ACQF_OPTIONS_STATIC})

    # (1) init: os 11D−1 pontos do DoE, NATIVOS, pelo wrapper (fase init).
    X0 = doe_art["X"]
    for i in range(X0.shape[0]):
        adapter.evaluate_native(X0[i])
    buf.add_pop(0, [r.solution_id for r in bud.records])

    # (2) laço de BO até o hard-stop NATURAL (D61). 1 infill real/iteração.
    proj = _WallClockProjector(max_wall_s, t0, bud.maxfe)
    tempo_fit_total = 0.0
    tempo_busca_total = 0.0
    hard_stopped = False
    stall_streak = 0
    it = 0
    n_iters_fit = 0                            # iterações com modelo ajustado
    try:
        while True:
            it += 1
            t_it0 = time.time()
            # L.10: manual_seed ANTES de construir modelo+acqf (uso_id 0);
            # h1/h2 = sampler/acqf (usos 1/2), trunc 32b (D91).
            h0 = torch_seed_for(semente, C262_ALG_ID, it, USO_MANUAL_SEED)
            h1 = iteration_seed(semente, C262_ALG_ID, it, USO_SAMPLER,
                                bits32=True)
            h2 = iteration_seed(semente, C262_ALG_ID, it, USO_ACQF,
                                bits32=True)

            # §17.6: o fit desta iteração treina com os pontos JÁ avaliados.
            n_train = bud.fe
            X_nat = np.vstack([r.x for r in bud.records])
            F_min = np.vstack([r.f for r in bud.records])
            train_X = adapter.to_unit(X_nat)
            train_Y = torch.as_tensor(-F_min, dtype=torch.float64)

            t_fit0 = time.time()
            model = _build_models(train_X, train_Y)
            fit_retries = _fit_models(model)
            tempo_fit = time.time() - t_fit0
            tempo_fit_total += tempo_fit
            n_iters_fit = it
            # timing ANTES do infill: a curva O(n³) retém o fit final mesmo
            # quando o hard-stop corta a iteração (D61).
            buf.add_timing(it, n_acumulado=n_train, tempo_fit_s=tempo_fit)
            log.timing(n_acumulado=n_train, tempo_fit_s=tempo_fit, it=it)
            # ②: o arquivo real que o modelo VIU nesta iteração.
            buf.add_pop(it, range(n_train))

            t_busca0 = time.time()
            acqf = _make_acqf(model, ref_max, train_X, h1)
            cands, acq_vals, acqf_warns = _optimize_acqf_restarts(acqf, D, h2)
            tempo_busca = time.time() - t_busca0
            tempo_busca_total += tempo_busca
            if acqf_warns:
                log.event("optimize_acqf_warning",
                          it=it, n=acqf_warns,
                          nota="retry/warning desloca o RNG (L.10 — registrado)")

            # ③: μ/σ do posterior nos candidatos dos restarts (D86: no_grad).
            U_cand = cands.squeeze(1)                       # (restarts, D)
            with torch.no_grad():
                post = model.posterior(U_cand)
                mu_max = post.mean.cpu().numpy()            # −f (maximização)
                sigma = np.sqrt(post.variance.cpu().numpy())
            mu_f = -mu_max                       # export SEMPRE em f (§5.5)
            best = int(torch.argmax(acq_vals))
            acqf_best = float(acq_vals[best])
            X_cand_nat = adapter.to_native(U_cand)

            for k in range(U_cand.shape[0]):
                if k == best:
                    continue                     # o escolhido entra após o FE
                buf.add_surrogate(_export.surrogate_row(
                    it, X_cand_nat[k],
                    mu=mu_f[k], sigma=sigma[k],
                    pred_tipo="valor", modelo_flag="GP"))

            # o infill: consome 1 FE (ou cache-hit=0 FE; ou BudgetExhausted).
            fe_antes = bud.fe
            try:
                adapter.evaluate_unit_max(U_cand[best])
            except _budget.BudgetExhausted:
                # linha ③ do escolhido nunca-avaliado (real_solution_id NULL)
                buf.add_surrogate(_export.surrogate_row(
                    it, X_cand_nat[best],
                    mu=mu_f[best], sigma=sigma[best],
                    pred_tipo="valor", modelo_flag="GP"))
                log.decision(caminho="hard_stop", it=it,
                             motivo="infill inédito com saldo zerado (D21/D61)",
                             torch_seed=h0, h1=h1, h2=h2,
                             acqf_escolhido=acqf_best,
                             n_restarts=NUM_RESTARTS)
                raise
            sid = bud.solution_id_of(X_cand_nat[best])
            buf.add_surrogate(_export.surrogate_row(
                it, X_cand_nat[best], real_solution_id=sid,
                mu=mu_f[best], sigma=sigma[best],
                pred_tipo="valor", modelo_flag="GP"))

            cache_hit_iter = (bud.fe == fe_antes)
            stall_streak = stall_streak + 1 if cache_hit_iter else 0
            log.decision(caminho="infill",
                         motivo="argmax do qLogNEHVI nos restarts (L.10)",
                         it=it, torch_seed=h0, h1=h1, h2=h2,
                         acqf_escolhido=acqf_best,
                         acqf_restarts=[float(v) for v in acq_vals],
                         n_restarts=NUM_RESTARTS, fit_retries=fit_retries,
                         acqf_warnings=acqf_warns, fe=bud.fe,
                         solution_id=sid, cache_hit=cache_hit_iter,
                         n_train=n_train)
            if stall_streak >= MAX_STALL_ITERS:      # D60-b (guarda de stall)
                log.guard("stall_logico", it=it, streak=stall_streak,
                          fe=bud.fe)
                raise RuntimeError(
                    f"c262 estagnado: {stall_streak} iterações consecutivas "
                    f"sem consumir FE (só duplicatas D89) — D60-b. "
                    f"Pára-e-loga (D81).")

            # D86: fim da iteração — solta tensores e coleta.
            del model, acqf, cands, acq_vals, post, train_X, train_Y, U_cand
            iteration_cleanup()

            # projeção do teto de wall-clock do piloto (ZDT1 ≤ 8h).
            proj.add(n_train, tempo_fit, time.time() - t_it0)
            over, proj_s, elapsed = proj.exceeded(bud.fe)
            if over:
                log.event("wall_projection_abort", it=it, fe=bud.fe,
                          elapsed_s=round(elapsed, 1),
                          proj_restante_s=round(proj_s, 1),
                          max_wall_s=max_wall_s)
                raise RuntimeError(
                    f"projeção de wall-clock estourou o teto do piloto: "
                    f"{elapsed:.0f}s decorridos + {proj_s:.0f}s projetados > "
                    f"{max_wall_s:.0f}s (fe={bud.fe}/{bud.maxfe}). Aborto "
                    f"LIMPO — curva §17.6 parcial no jsonl. A decisão de "
                    f"completar é da torre/autor (M7). Pára-e-loga (D81).")
    except _budget.BudgetExhausted:
        hard_stopped = True                       # D21/D61: fim limpo do laço
        iteration_cleanup()

    timing_totais = {
        "tempo_total_s": round(time.time() - t0, 4),
        "tempo_fit_surrogate_s": round(tempo_fit_total, 4),
        "tempo_busca_s": round(tempo_busca_total, 4),
        "tempo_aval_real_s": round(adapter.tempo_aval_real_s, 4),
    }
    out = write_run_outputs(
        exp, alg, problema, semente, bud, buf, adapter=adapter,
        doe_hash_sidecar=doe_art["doe_hash"], env=env, pinning=pinning,
        n_geracoes=n_iters_fit, algo_version=ALGO_VERSION,
        timing_totais=timing_totais, regime="online",
        data_root=data_root, enable_bucket=enable_bucket)
    out["manifest"]["acqf_ref_f"] = ref_f.tolist()
    out["manifest"]["fused_kernel"] = fused_policy["fused_kernel"]
    from src import manifest as _manifest
    _manifest.write_manifest(out["manifest"], data_root)

    log.footer(status="ok", fe_final=bud.fe, n_geracoes=n_iters_fit,
               cache_hits=bud.cache_hits, cp_init=out["cp_init_ok"],
               hard_stopped=hard_stopped)

    return {
        "D": D, "M": M, "maxfe": bud.maxfe, "fe_final": bud.fe,
        "n_init": bud.n_init, "n_iters": n_iters_fit,
        "cache_hits": bud.cache_hits, "hard_stopped": hard_stopped,
        "cp_init_ok": out["cp_init_ok"],
        "doe_hash_run": out["doe_hash_run"],
        "acqf_ref_f": ref_f.tolist(),
        "fused_kernel": fused_policy["fused_kernel"],
        "timing_totais": timing_totais,
        "fit_series": buf.fit_series,
        "upload_status": out["upload_status"],
    }


__all__ = [
    "C262_ALG_ID", "USO_MANUAL_SEED", "USO_SAMPLER", "USO_ACQF",
    "MC_SAMPLES", "NUM_RESTARTS", "RAW_SAMPLES", "TRAIN_YVAR",
    "disable_fused_kernel", "acqf_ref_point", "run_c262",
]
