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
from src.checkpoint import Checkpointer as _Checkpointer   # [DI-43]
from src import botorch_harness as _H
from src.botorch_harness import (
    BoTorchProblemAdapter,
    SnapshotBuffer,
    di10_minimo_comum,
    emit_sonda_block,
    env_info,
    iteration_cleanup,
    iteration_seed,
    load_doe,
    load_sonda,
    pin_runtime,
    sonda_due,
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

#: [T11-A4 / T1 do relatório de fidelidade] Os 8 hiperparâmetros do qLogNEHVI
#: que a receita L.10 crava e que NÃO estavam declarados em lugar nenhum —
#: só no corpo do `_make_acqf`. Sem eles no header/⑤, quem audita a aquisição
#: tem de LER O CÓDIGO da versão que rodou (e o `repo_hash` estava vazio: I-09).
#: São a FONTE ÚNICA — `_make_acqf` os consome daqui.
ACQF_HP = {
    "prune_baseline": True,     # poda o X_baseline dominado (o n_baseline do ⑥)
    "alpha": 0.0,               # 0 = HV exato (sem aproximação por caixas)
    "cache_pending": True,
    "max_iep": 0,               # nenhum ponto pendente incremental
    "incremental_nehvi": True,
    "cache_root": None,         # DEF-L2/L.10: sem cache de raiz de Cholesky
    "tau_relu": 1e-6,           # suavização do ReLU (fat=True)
    "tau_max": 1e-3,            # suavização do max
    "fat": True,                # cauda "gorda" do log (a formulação Log)
    "eta": 1e-3,
}
# [T9/DI-35.1] CALIBRAÇÃO BATCH — DECISÃO MEDIDA: **o c262 NÃO recebe knob de
# redução**. Medido POR ITERAÇÃO (ZDT4/42, q=10, 1 core, serial, cartão T9): a
# receita CHEIA projeta **~2,2 h** o run batch completo (200 iters; busca ~1,6 h
# sub-linear p≈0,54 + fit ~0,6 h + overhead) — MUITO abaixo do alvo ~10 h e do
# teto 12 h. Os "~56 h" do repasse T6 eram CONTENÇÃO (4 configs em paralelo +
# swap/OOM), não a receita. Além disso `MC_SAMPLES` é um DUD aqui: 16/32/64/128
# dão o MESMO t_busca (o custo é o particionamento do baseline, não a amostragem
# MC) — reduzi-lo não baixaria o custo, só a qualidade. O único gargalo real do
# c262 batch é RAM (o baseline cresce com n — D-2): provisionamento, não receita.
# Se um dia se quiser margem, o lever seria NUM_RESTARTS/RAW_SAMPLES (não MC).
# Autor ratifica manter a receita cheia (D97). O caminho q=1 já é intocado.

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


def _sonda_header(sonda_art: dict) -> dict:
    """O bloco `sonda` do header do jsonl — a certidão de QUAL régua foi usada
    (o hash é o CP da sonda; §17.2.2)."""
    return {"S": sonda_art["S"], "k": _H.SONDA_K,
            "cadencia": "1ª iteração, a cada k=2, e SEMPRE a última",
            "x_hash": sonda_art["x_hash"], "f_hash": sonda_art["f_hash"],
            "path": sonda_art["path"], "custo_fe": 0}


def _sigma_dict() -> dict:
    """`sigma_dict` (DEF-C4) — o dicionário semântico da ③ do c262, LEITURA
    OBRIGATÓRIA antes de usar a tabela (CONTRATO §3/R4 regra 3)."""
    return {
        "ordem_terceira_online": "[I-12] as R linhas de uma iteracao vem na ordem dos restarts com o VENCEDOR removido e re-anexado NO FIM: linha j -> restart j (j<best) | j+1 (j>=best); linha R-1 -> best, com best=argmax isfinite(acqf_todos_restarts). Casar por indice ingenuo da 89% de falso-mismatch (J27 REFUTADO). Utilitario: botorch_harness.restart_de_linha(R, best). NAO vale para q>1",
        "pred_tipo": "valor (regressor probabilístico)",
        "modelo_flag": "GP = SingleTaskGP por objetivo (ModelListGP)",
        "mu_j": "média do posterior do GP do objetivo j, em f de MINIMIZAÇÃO "
                "(o motor opera em −f; o export inverte — §5.5)",
        "sigma_j": "desvio-padrão do posterior (VAR-GP, não erro empírico); "
                   "inclui o train_Yvar=1e-6 fixo (B8.6a — noiseless)",
        "espaco_modelo": "cru (o GP treina em [0,1]^D; a ③ grava x NATIVO)",
        "regime": "'sonda' = os 2000 pontos fixos do artefato §17.2.2, na "
                  "ORDEM do artefato (join com o gabarito POR POSIÇÃO); "
                  "'online' = os candidatos dos restarts do optimize_acqf",
        "fe_treino_max": "maior fe_index no treino do GP no fit desta predição "
                         "(DI-09/A1 — filtro in-sample × out-of-sample)",
        "real_solution_id": "preenchido só na linha do candidato ESCOLHIDO que "
                            "de fato consumiu FE; NULL nos demais restarts e "
                            "em toda a sonda",
        "jsonl_n_baseline": "|X_baseline| PÓS-PRUNE do qLogNEHVI "
                            "(prune_baseline=True)",
        "jsonl_acqf_todos_restarts": "os NUM_RESTARTS valores da acqf, um por "
                                     "restart (a paisagem da aquisição — DI-10)"
                                     ". ⚠ Runs PRÉ-retrofit gravaram a mesma "
                                     "grandeza sob o nome `acqf_restarts`.",
    }


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


def _fit_models(model) -> tuple[int, dict]:
    """Refit from scratch por iteração (D44) via `fit_gpytorch_mll` oficial
    (max_attempts default; retries amostram dos priors → RNG torch, ancorado
    no manual_seed da iteração — L.10).

    Retorna `(fit_retries, modelo_hp)`: o nº de warnings de retry/otimização
    capturados (fit-retries do jsonl S.7) e o bloco **`modelo_hp` do DI-10/B1**
    — `mll_final` (o valor final da log-verossimilhança marginal, o "quão bem o
    modelo ajustou" da S.7.1) + θ/lengthscales (min/med/max), outputscale e
    ruído por objetivo. Tudo LEITURA de parâmetros já ajustados.

    ⚠ Não-perturbação: o forward do MLL roda sob `no_grad` + `preserve_torch_rng`
    e o modo de treino do módulo é restaurado ao que estava. Verificado por
    probe direto: os candidatos E os valores da acqf do `optimize_acqf` seguinte
    saem BIT-A-BIT idênticos com e sem a extração."""
    from botorch.fit import fit_gpytorch_mll
    from gpytorch.mlls import SumMarginalLogLikelihood
    mll = SumMarginalLogLikelihood(model.likelihood, model)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fit_gpytorch_mll(mll)
    n_retries = sum(1 for w in caught
                    if "attempt" in str(w.message).lower()
                    or "retry" in str(w.message).lower()
                    or "optimization" in str(w.message).lower())
    return n_retries, _modelo_hp(model, mll)


def _modelo_hp(model, mll) -> dict:
    """O bloco `modelo_hp` do DI-10/B1 (read-only sobre o modelo ajustado)."""
    from src.botorch_harness import preserve_torch_rng
    modo = mll.training
    try:
        with preserve_torch_rng(), torch.no_grad():
            mll.train()
            mll_final = float(mll(model(*model.train_inputs),
                                  model.train_targets))
    except Exception as err:            # noqa: BLE001 — B1 é instrumentação:
        mll_final = None                # nunca derruba o run (D97/patch-mínimo)
        _hp_warn(err)
    finally:
        mll.train(modo)

    por_obj = []
    with torch.no_grad():
        for m in model.models:
            ls = m.covar_module.base_kernel.lengthscale.detach().reshape(-1)
            por_obj.append({
                "lengthscale_min": float(ls.min()),
                "lengthscale_med": float(ls.median()),
                "lengthscale_max": float(ls.max()),
                "outputscale": float(m.covar_module.outputscale.detach()),
                "noise": float(m.likelihood.noise.detach().reshape(-1)[0]),
            })
    return {"mll_final": mll_final, "por_objetivo": por_obj}


def _hp_warn(err: Exception) -> None:
    """Aviso único e barulhento se o `mll_final` (B1) ficar indisponível."""
    warnings.warn(f"modelo_hp: mll_final indisponível ({type(err).__name__}: "
                  f"{err}) — instrumentação DI-10/B1 degradada, run segue.",
                  RuntimeWarning, stacklevel=3)


def _n_baseline(acqf) -> int | None:
    """`n_baseline` do DI-10 (c262): o tamanho do X_baseline **PÓS-PRUNE** —
    o qLogNEHVI foi construído com `prune_baseline=True`, então o buffer
    `X_baseline` guarda o conjunto já podado (é ele que o custo da aquisição
    enxerga). Read-only; ausente numa versão futura ⇒ None, sem derrubar."""
    xb = getattr(acqf, "X_baseline", None)
    return None if xb is None else int(xb.shape[0])


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
        **ACQF_HP,          # [A4] os 8 hp declarados (fonte única do header/⑤)
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


def _lote_greedy_sequencial(acqf, D: int, h2: int, q: int):
    """[T6-batch] O lote NATIVO do qLogNEHVI (D66) — greedy sequencial em q.

    **Por que reimplementar em vez de `optimize_acqf(q=10, sequential=True)`.**
    O BoTorch PROÍBE a combinação que o nosso contrato exige:
    `sequential=True` + `return_best_only=False` ⇒
    `NotImplementedError: return_best_only=False only supported for joint
    optimization`. Mas a ③ do c262 é definida (§17.4) sobre **TODOS os
    candidatos dos restarts**, e a DI-10 exige `acqf_todos_restarts` ("a
    paisagem da aquisição = COMO o BO escolheu"). Escolher um dos dois
    contratos seria perder fidelidade (lote não-nativo) ou perder a
    instrumentação central do config.

    Não há terceiro caminho na API — mas há na implementação: o modo sequencial
    do BoTorch (`botorch.optim.optimize._optimize_acqf_sequential_q`) é
    literalmente *"for each of q times, generate a single candidate greedily,
    then add it to the list of pending points"*, isto é, **q chamadas com q=1**
    e `set_X_pending` acumulando os já escolhidos. Esta função é a transcrição
    fiel desse laço, trocando apenas `return_best_only` — que **não altera a
    seleção** (o `argmax` devolve o mesmo ponto que o `return_best_only=True`
    devolveria), só expõe o que o stock descarta. Mesmo critério DI-12.1/DI-21
    ("adição read-only que só EXPÕE valor já computado é permitida") e mesmo
    precedente do `_build_surrogates` do c311.

    ⚠ **q=1 tem saída ANTECIPADA**: nem toca em `X_pending`, para o caminho do
    experimento principal sair BIT-INTOCADO (é o que a prova de regressão do
    T6 afere contra os runs já validados).

    Devolve `[(cands, acq_vals, n_warn, idx_best), ...]` — um passo por infill.
    """
    if int(q) == 1:                       # ← caminho do principal, intocado
        cands, acq_vals, n_warn = _optimize_acqf_restarts(acqf, D, h2)
        return [(cands, acq_vals, n_warn, int(torch.argmax(acq_vals)))]

    base_pending = acqf.X_pending
    passos, escolhidos = [], []
    try:
        for _ in range(int(q)):
            if escolhidos:
                novos = torch.cat(escolhidos, dim=-2)
                acqf.set_X_pending(
                    novos if base_pending is None
                    else torch.cat([base_pending, novos], dim=-2))
            cands, acq_vals, n_warn = _optimize_acqf_restarts(acqf, D, h2)
            b = int(torch.argmax(acq_vals))
            escolhidos.append(cands[b].detach().reshape(1, -1))
            passos.append((cands, acq_vals, n_warn, b))
    finally:
        acqf.set_X_pending(base_pending)   # o stock também restaura ao fim
    return passos


class WallClockAbort(RuntimeError):
    """[D-07/DI-21] Aborto por teto de wall-clock — classe DISTINTA para o
    despachante reconhecer (pelo NOME, sem importar torch) que retriar não
    conserta: cada retry estouraria o MESMO teto (8h virariam 24h).

    ⟦DI-43/44⟧ **O rito do teto não a levanta mais** (o run trunca e fecha
    `failed`/`teto_wall` COM as camadas). Ela fica: (i) o despachante mantém o
    ramo não-retriável por NOME, que é barato e defende qualquer runner futuro;
    (ii) o `teto_s` de um runner standalone pode continuar usando-a."""


def _manifesto_failed_teto(exp, alg, problema, semente, data_root, *,
                           criterio, elapsed_s, fe, maxfe):
    """[D-07/DI-21 — o padrão do c122 replicado] Grava um manifesto `failed`
    NO PONTO do aborto por teto. Sem ele, artefatos de uma execução ANTERIOR
    do mesmo run_id sobreviviam ao lado de um jsonl novo dizendo failed, e o
    `is_run_done` (D58) lia o run truncado como PRONTO — o cenário B-2 da
    auditoria. O manifesto é NOVO (não mescla): misturar campos ricos da
    execução antiga com o aborto novo confundiria duas execuções.

    ⟦DI-43/44⟧ Fora do rito do teto (que agora fecha pelo `write_run_outputs`
    com as camadas parciais); segue disponível para aborto SEM dado."""
    from src import manifest as _manifest
    man = _manifest.new_manifest(
        exp, alg, problema, semente, status="failed",
        stack_trace=(f"WallClockAbort[{criterio}]: {elapsed_s:.0f}s "
                     f"(fe={fe}/{maxfe})"),
        maxfe=maxfe, fe_final=fe, data_root=data_root)
    man["motivo_parada"] = "teto_wall"
    _manifest.write_manifest(man, data_root)


class _WallClockProjector:
    """Teto de wall-clock (DI-44: **12 h**) — hoje com UM critério de aborto.

    (1) **Projeção**: ajusta `t_fit ≈ c·n³` nas últimas iterações e projeta o
        restante do run (fits em n crescente + busca/aval ~constantes); só arma
        depois de 10 amostras. ⟦**DI-43/44: NÃO ABORTA MAIS** — virou AVISO.⟧
    (2) **Teto de tempo DECORRIDO** (DI-11.3, adendo B): `elapsed > max_wall_s`
        aborta na hora. **É o único critério de aborto** (DI-43).

    **Por que (1) deixou de abortar [DI-43, emendada pela DI-44].** O aborto por
    projeção matava o run ANTES de qualquer parquet existir: medido na s42, as
    células do `main/c154` D≥12 queimaram 0,87–2,99 h cada (média 1,47 h — o
    "~6,3 h" da DI-40 era ~4× superestimado, ERRATA da PARTE A32) para entregar
    **zero dado**. Com o roster 100% e o teto de 12 h, a doutrina passa a ser
    *truncamento-com-dado*: o run vai até o RELÓGIO e fecha
    `failed`/`teto_wall` GRAVANDO as camadas parciais — "curva parcial é o
    dado" (DI-37.1). A projeção continua sendo CALCULADA e LOGADA
    (`wall_projection_warning`): ela é a estimativa que explica por que a célula
    não vai fechar, e apagá-la perderia o diagnóstico.

    NUNCA reduz orçamento e nada aqui toca a busca ou a numérica."""

    def __init__(self, max_wall_s: float | None, t0: float, maxfe: int):
        self.max_wall_s = max_wall_s
        self.t0 = t0
        self.maxfe = maxfe
        self.samples: list[tuple[int, float, float]] = []  # (n, t_fit, t_iter)
        #: já avisamos que a projeção estourou? (1 linha por run, não 1 por it)
        self.avisou_projecao = False

    def add(self, n: int, t_fit: float, t_iter: float) -> None:
        self.samples.append((int(n), float(t_fit), float(t_iter)))

    def projection_s(self, n_now: int) -> float | None:
        """Segundos projetados p/ TERMINAR o run a partir de `n_now` FEs.

        [DI-36] O passo de FE POR ITERAÇÃO é inferido dos próprios samples
        (mediana dos deltas de n): em q=1 dá 1 — projeção BIT-IGUAL à
        original; em lote (q=10) cada iteração futura avança ~q FEs — somar
        termo-a-termo em passo 1 superestimava ~q× nos DOIS termos, e o
        projetor abortaria espuriamente o batch do c262 (~2,2h reais
        projetados acima do teto). Era também a origem do "~56h" do T6
        (artefato do projetor, não contenção/swap — causa-raiz corrigida
        pela auditoria da torre sobre a evidência do T9).
        """
        if len(self.samples) < 10:
            return None
        recent = self.samples[-5:]
        c = float(np.mean([tf / max(n, 1) ** 3 for n, tf, _ in recent]))
        other = float(np.mean([ti - tf for n, tf, ti in recent]))
        difs = np.diff([n for n, _, _ in self.samples])
        avanca = difs[difs > 0]
        passo = int(np.median(avanca)) if avanca.size else 1
        ns = np.arange(n_now, self.maxfe + 1, max(1, passo), dtype=np.float64)
        return float(c * np.sum(ns ** 3) + max(other, 0.0) * len(ns))

    def exceeded(self, n_now: int) -> tuple[bool, float | None, float, str | None]:
        """`(estourou, proj_restante_s|None, elapsed_s, criterio|None)`.

        ⟦DI-43/44⟧ `estourou` é **True SÓ por `elapsed`**. Quando a projeção
        indica que o run não fecharia no teto, devolve
        `criterio='projecao_warning'` com `estourou=False`: o chamador LOGA e
        segue rodando até o relógio, para entregar curva parcial em parquet.
        """
        elapsed = time.time() - self.t0
        if self.max_wall_s is None:
            return False, None, elapsed, None
        if elapsed > self.max_wall_s:            # (2) DI-11.3 — o ÚNICO aborto
            return True, None, elapsed, "elapsed"
        proj = self.projection_s(n_now)          # (1) projeção pós-10-amostras
        if proj is None:
            return False, None, elapsed, None
        if (elapsed + proj) > self.max_wall_s:
            return False, proj, elapsed, "projecao_warning"
        return False, proj, elapsed, None


def _params_efetivos(q) -> dict:
    """[I-07/A4] A config EFETIVA — fonte ÚNICA do `params` do header do ⑥ E do
    ⑤ (o CONTRATO §5 o exige e 24 células de c262 na s42 não o tinham no ⑤).
    Inclui os 8 hp da acqf (T1): sem eles, auditar a aquisição exige ler o
    código da versão que rodou."""
    return {"mc_samples": MC_SAMPLES, "num_restarts": NUM_RESTARTS,
            "raw_samples": RAW_SAMPLES, "train_Yvar": TRAIN_YVAR,
            "q": int(q), "refit": "from-scratch/iter (D44)",
            "kernel": "Matern-5/2-ARD gamma-prior (D30)",
            "acqf": "qLogNEHVI L.10",
            "acqf_hp": dict(ACQF_HP),          # [A4] os 8 do T1
            **ACQF_OPTIONS_STATIC}


def run_c262(exp: str, alg: str, problema: str, semente, *,
             sonda_on: bool = True,
             data_root: str = naming.DEFAULT_DATA_ROOT,
             enable_bucket: bool = False,
             max_wall_s: float | None = None,
             teto_s: float | None = None,
             q: int = 1, **_kwargs) -> dict:
    """Um run c262 — assinatura padrão dos runners R2 (`experiment.run`
    repassa os kwargs). `max_wall_s` liga a projeção de teto do piloto (8h no
    ZDT1); estouro projetado ⇒ aborto limpo + RuntimeError (pára-e-loga D81).
    Retorna o dict de evidências (FE, iters, timing, curva §17.6)."""
    # [T6-batch] `teto_s` do despachante → `max_wall_s` (o mesmo teto de wall);
    # NO-OP quando teto_s=None (o principal q=1). Ver a nota em run_c154.
    if max_wall_s is None and teto_s is not None:
        max_wall_s = float(teto_s)
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
    # SONDA DI-09/§17.2.2: CARREGADA 1× (hash conferido) antes de abrir o log —
    # artefato ausente/corrompido pára o run ANTES de gastar FE (como o DoE).
    sonda_art = load_sonda(problema, data_root=data_root)
    ref_f, ideal_s5, nadir_s5 = acqf_ref_point(problema)

    log = AuditLogger.for_run(exp, alg, problema, semente,
                              data_root=data_root, append=False)
    try:
        return _run_c262_body(exp, alg, problema, semente, t0, pinning, env,
                              fused_policy, doe_art, sonda_art, ref_f,
                              ideal_s5, nadir_s5,
                              log, data_root, enable_bucket, max_wall_s,
                              int(q),
                              sonda_on=sonda_on)
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
                   doe_art, sonda_art, ref_f, ideal_s5, nadir_s5, log,
                   data_root, enable_bucket, max_wall_s, q=1, sonda_on=True) -> dict:
    # [T6-batch] o orçamento é POR EXP (D66): main = 31D−1; batch = 11D−1+200q.
    _D0 = doe_art["X"].shape[1]
    bud = _budget.FEBudget(
        D=_D0, maxfe=_budget.maxfe_por_exp(exp, _D0, q), logger=log)
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
               sonda=_sonda_header(sonda_art),
               sigma_dict=_sigma_dict(),
               params=_params_efetivos(q))

    # (1) init: os 11D−1 pontos do DoE, NATIVOS, pelo wrapper (fase init).
    X0 = doe_art["X"]
    for i in range(X0.shape[0]):
        adapter.evaluate_native(X0[i])
    buf.add_pop(0, [r.solution_id for r in bud.records])

    # (2) laço de BO até o hard-stop NATURAL (D61). 1 infill real/iteração.
    proj = _WallClockProjector(max_wall_s, t0, bud.maxfe)
    # [DI-43] checkpoint atômico periódico — 25 iterações OU 30 min.
    ckpt = _Checkpointer(exp, alg, problema, semente, D=adapter.D, M=adapter.M,
                         regime="online", q=int(q), data_root=data_root, log=log)
    tempo_fit_total = 0.0
    tempo_busca_total = 0.0
    tempo_sonda_total = 0.0                    # DI-09 (agregado do manifesto)
    n_blocos_sonda = 0                         # blocos de 2000 linhas emitidos
    hard_stopped = False
    truncou_por_teto = False                   # [DI-43] teto por RELÓGIO
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
            fit_retries, modelo_hp = _fit_models(model)   # +modelo_hp (DI-10/B1)
            if fit_retries:
                # [A4] AVISO AMARELO: o fit do GP precisou de tentativa extra.
                # Antes o número só viajava dentro do evento de geração, onde
                # ninguém filtra por ele; como `guard` ele entra na varredura de
                # guardas do portão e na triagem do dossiê. É o sintoma precoce
                # do MESMO gargalo que matou `main/c262/WFG1` com
                # `ModelFittingError: All attempts to fit` na it 41 (n_train=281,
                # 41,3% do orçamento) — a região quase-plana do WFG1 degenera a
                # matriz de covariância, e o retry conta essa história ANTES do
                # erro duro.
                log.guard("fit_retries", it=it, n_retries=int(fit_retries),
                          n_train=int(n_train),
                          motivo="fit_gpytorch_mll precisou de tentativa extra "
                                 "(condicionamento do GP) — precursor do "
                                 "ModelFittingError")
            tempo_fit = time.time() - t_fit0
            tempo_fit_total += tempo_fit
            n_iters_fit = it
            # DI-09/A1: o modelo desta iteração viu os fe_index 0..n_train−1 —
            # toda linha ③ emitida daqui em diante herda o marcador.
            buf.set_fe_treino_max(n_train - 1)
            # timing ANTES do infill: a curva O(n³) retém o fit final mesmo
            # quando o hard-stop corta a iteração (D61). Busca/sonda/geração
            # entram por `update_timing` no fim da iteração.
            buf.add_timing(it, n_acumulado=n_train, tempo_fit_s=tempo_fit)
            log.timing(n_acumulado=n_train, tempo_fit_s=tempo_fit, it=it)
            # ②: o arquivo real que o modelo VIU nesta iteração.
            buf.add_pop(it, range(n_train))

            t_busca0 = time.time()
            acqf = _make_acqf(model, ref_max, train_X, h1)
            n_baseline = _n_baseline(acqf)               # pós-prune (DI-10)
            # [T6-batch] LOTE NATIVO: q passos gulosos sequenciais (D66/D42).
            # q=1 ⇒ 1 passo, sem tocar em X_pending = o principal INTOCADO.
            passos = _lote_greedy_sequencial(acqf, D, h2, q)
            tempo_busca = time.time() - t_busca0
            tempo_busca_total += tempo_busca
            acqf_warns = sum(p[2] for p in passos)
            if acqf_warns:
                log.event("optimize_acqf_warning",
                          it=it, n=acqf_warns,
                          nota="retry/warning desloca o RNG (L.10 — registrado)")

            # ③: μ/σ do posterior nos candidatos dos restarts (D86: no_grad).
            # Com q>1 há uma PAISAGEM POR PASSO guloso (o X_pending muda a
            # aquisição a cada escolha) — a ③ registra todas, que é a leitura
            # forte do §17.4/DI-10 ("como o BO escolheu"), agora por infill.
            cands, acq_vals, _nw0, best = passos[0]
            U_cand = cands.squeeze(1)                       # (restarts, D)
            with torch.no_grad():
                post = model.posterior(U_cand)
                mu_max = post.mean.cpu().numpy()            # −f (maximização)
                sigma = np.sqrt(post.variance.cpu().numpy())
            mu_f = -mu_max                       # export SEMPRE em f (§5.5)
            acqf_best = float(acq_vals[best])
            X_cand_nat = adapter.to_native(U_cand)

            # Os passos 2..q (só existem no batch): ③ dos NÃO-escolhidos agora;
            # os escolhidos entram depois do FE, junto com o do passo 1.
            extras = []                    # [(X_nat, mu, sigma, idx_best), ...]
            for cands_i, acqv_i, _nwi, best_i in passos[1:]:
                U_i = cands_i.squeeze(1)
                with torch.no_grad():
                    post_i = model.posterior(U_i)
                    mu_i = -post_i.mean.cpu().numpy()
                    sig_i = np.sqrt(post_i.variance.cpu().numpy())
                X_i = adapter.to_native(U_i)
                for k in range(U_i.shape[0]):
                    if k == best_i:
                        continue
                    buf.add_surrogate(_export.surrogate_row(
                        it, X_i[k], mu=mu_i[k], sigma=sig_i[k],
                        pred_tipo="valor", modelo_flag="GP"))
                extras.append((X_i, mu_i, sig_i, best_i,
                               float(acqv_i[best_i]), U_i))
                del post_i

            for k in range(U_cand.shape[0]):
                if k == best:
                    continue                     # o escolhido entra após o FE
                buf.add_surrogate(_export.surrogate_row(
                    it, X_cand_nat[k],
                    mu=mu_f[k], sigma=sigma[k],
                    pred_tipo="valor", modelo_flag="GP"))

            def di10():
                """Os campos DI-10 do `<alg>_gen` TIRADOS NO MOMENTO DO LOG —
                `fe`/`f_best`/`n_front1` refletem o arquivo depois (ou não) do
                infill, conforme o ramo que chamar."""
                return dict(
                    fe=bud.fe, modelo_hp=modelo_hp, n_baseline=n_baseline,
                    acqf_todos_restarts=[float(v) for v in acq_vals],
                    tempo_fit_s=round(tempo_fit, 4),
                    tempo_busca_s=round(tempo_busca, 4),
                    **di10_minimo_comum(bud, u_infill=U_cand[best],
                                        train_U=train_X))

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
                             n_restarts=NUM_RESTARTS, **di10())
                # §17.2.2: esta É a última iteração — a sonda é OBRIGATÓRIA
                # nela. O bloco desta iteração ainda não saiu (o ponto de
                # emissão é a jusante do infill, que acabou de levantar), e o
                # modelo desta iteração continua vivo aqui.
                t_snd = 0.0 if not sonda_on else emit_sonda_block(   # [G-6]
                    buf, log, it=it, fe=bud.fe, sonda=sonda_art,
                    adapter=adapter, model=model,
                    fe_treino_max=n_train - 1,
                    motivo="ultima iteracao (hard-stop D61)")
                tempo_sonda_total += t_snd
                n_blocos_sonda += 1
                buf.update_timing(it, tempo_busca_s=tempo_busca,
                                  tempo_pred_sonda_s=t_snd,
                                  # [BL-11] 0.0 aqui: o checkpoint desta iteração
                                  # nunca chegou a rodar (o hard-stop corta antes).
                                  tempo_checkpoint_s=ckpt.consumir_tempo_s(),
                                  tempo_geracao_s=(time.time() - t_it0) - t_snd)
                raise
            sid = bud.solution_id_of(X_cand_nat[best])
            buf.add_surrogate(_export.surrogate_row(
                it, X_cand_nat[best], real_solution_id=sid,
                mu=mu_f[best], sigma=sigma[best],
                pred_tipo="valor", modelo_flag="GP"))

            # [T6-batch] os FE dos passos 2..q do lote (vazio quando q=1).
            # O orçamento governa (D61): se estourar NO MEIO do lote, a linha ③
            # do escolhido sai sem `real_solution_id` e o hard-stop segue o
            # MESMO rito do passo 1 (sonda obrigatória na última iteração).
            sids_lote = [sid]
            for X_i, mu_i, sig_i, best_i, acqv_i, U_i in extras:
                try:
                    adapter.evaluate_unit_max(U_i[best_i])
                except _budget.BudgetExhausted:
                    buf.add_surrogate(_export.surrogate_row(
                        it, X_i[best_i], mu=mu_i[best_i], sigma=sig_i[best_i],
                        pred_tipo="valor", modelo_flag="GP"))
                    log.decision(caminho="hard_stop", it=it,
                                 motivo="orçamento esgotado no meio do lote "
                                        "(D21/D61)",
                                 torch_seed=h0, h1=h1, h2=h2,
                                 acqf_escolhido=acqv_i, q=q,
                                 n_no_lote=len(sids_lote),
                                 n_restarts=NUM_RESTARTS, **di10())
                    t_snd = 0.0 if not sonda_on else emit_sonda_block(  # [G-6]
                        buf, log, it=it, fe=bud.fe, sonda=sonda_art,
                        adapter=adapter, model=model,
                        fe_treino_max=n_train - 1,
                        motivo="ultima iteracao (hard-stop D61, lote parcial)")
                    tempo_sonda_total += t_snd
                    n_blocos_sonda += 1
                    buf.update_timing(
                        it, tempo_busca_s=tempo_busca,
                        tempo_pred_sonda_s=t_snd,
                        tempo_checkpoint_s=ckpt.consumir_tempo_s(),   # [BL-11]
                        tempo_geracao_s=(time.time() - t_it0) - t_snd)
                    raise
                sid_i = bud.solution_id_of(X_i[best_i])
                sids_lote.append(sid_i)
                buf.add_surrogate(_export.surrogate_row(
                    it, X_i[best_i], real_solution_id=sid_i,
                    mu=mu_i[best_i], sigma=sig_i[best_i],
                    pred_tipo="valor", modelo_flag="GP"))

            cache_hit_iter = (bud.fe == fe_antes)
            stall_streak = stall_streak + 1 if cache_hit_iter else 0
            log.decision(caminho="infill",
                         motivo="argmax do qLogNEHVI nos restarts (L.10)",
                         it=it, torch_seed=h0, h1=h1, h2=h2,
                         acqf_escolhido=acqf_best,
                         n_restarts=NUM_RESTARTS, fit_retries=fit_retries,
                         acqf_warnings=acqf_warns,
                         solution_id=sid, cache_hit=cache_hit_iter,
                         q=q, lote_solution_ids=sids_lote,
                         n_train=n_train, **di10())

            # SONDA §17.2.2 — DEPOIS da busca da iteração (isolamento máximo) e
            # ANTES do `del model`. Cadência k=2 + 1ª; a última é coberta no
            # ramo do hard-stop acima OU no do teto (BL-06), conforme o motivo
            # de parada. ZERO FE, RNG preservado.
            t_snd = 0.0
            emitiu_sonda = False
            if sonda_on and sonda_due(it):                  # [G-6]
                t_snd = emit_sonda_block(
                    buf, log, it=it, fe=bud.fe, sonda=sonda_art,
                    adapter=adapter, model=model, fe_treino_max=n_train - 1)
                tempo_sonda_total += t_snd
                n_blocos_sonda += 1
                emitiu_sonda = True
            # ④ (§17.6 expandida): o wall da GERAÇÃO exclui a sonda — ela é
            # instrumentação DESTE estudo, não custo do algoritmo, e vai
            # medida à parte em `tempo_pred_sonda_s`. (O projetor de teto,
            # abaixo, vê o wall CHEIO: lá a pergunta é o relógio de parede.)
            buf.update_timing(it, tempo_busca_s=tempo_busca,
                              tempo_pred_sonda_s=t_snd,
                              tempo_geracao_s=(time.time() - t_it0) - t_snd)

            if stall_streak >= MAX_STALL_ITERS:      # D60-b (guarda de stall)
                log.guard("stall_logico", it=it, streak=stall_streak,
                          fe=bud.fe)
                raise RuntimeError(
                    f"c262 estagnado: {stall_streak} iterações consecutivas "
                    f"sem consumir FE (só duplicatas D89) — D60-b. "
                    f"Pára-e-loga (D81).")

            # [DI-43] checkpoint atômico periódico (25 its OU 30 min): as
            # camadas parciais existem ANTES do fim, então uma morte matada
            # (spot revogada, OOM, SIGKILL) não zera o run.
            ckpt.talvez_gravar(bud, buf, iteracao=it)
            # [BL-11] o I/O do checkpoint é publicado à parte — e roda DEPOIS do
            # `tempo_geracao_s` fechar, de propósito: o instrumento não entra na
            # conta do algoritmo (mesma doutrina da sonda, DI-13.10).
            buf.update_timing(it, tempo_checkpoint_s=ckpt.consumir_tempo_s())

            # [BL-06] O `del model` (D86) desceu para DEPOIS do teto: sob
            # truncamento esta É a última iteração, e o §17.2.2 promete bloco
            # de sonda na última — mas predizer exige o modelo VIVO. Nada mais
            # muda de ordem: `proj.exceeded` aborta só por `elapsed` desde a
            # DI-43, então o instante do teto não se move.
            # teto de wall-clock (DI-44: 12 h) — elapsed-only desde a DI-43.
            proj.add(n_train, tempo_fit, time.time() - t_it0)
            over, proj_s, elapsed, criterio = proj.exceeded(bud.fe)
            if criterio == "projecao_warning" and not proj.avisou_projecao:
                # [DI-43] a projeção não aborta mais: ela AVISA (1 linha por
                # run). O run segue até o relógio para entregar curva parcial.
                proj.avisou_projecao = True
                log.event("wall_projection_warning", it=it, fe=bud.fe,
                          elapsed_s=round(elapsed, 1),
                          proj_restante_s=round(proj_s, 1),
                          max_wall_s=max_wall_s,
                          nota="projecao indica que o run nao fecha no teto; "
                               "seguindo ate o relogio (truncamento-com-dado, "
                               "DI-43/44)")
            if over:
                # [DI-43] TRUNCAMENTO-COM-DADO: sai do laço e fecha pelo rito
                # normal com status='failed'/motivo='teto_wall' — as camadas
                # parciais são GRAVADAS (era `raise WallClockAbort` e zero
                # parquet: ~1,47 h/célula queimada por nada na s42).
                truncou_por_teto = True
                # [BL-06] O bloco FINAL da sonda, ANTES de fechar as camadas
                # parciais. `sonda.cadencia` declara no ⑤ "1ª, a cada k=2 e
                # SEMPRE a última"; sob teto a última é ESTA, e o ramo do
                # hard-stop (o único que cobria a promessa) nunca é alcançado.
                # Custo medido: ~0,08 s — e é a foto mais informativa de uma
                # célula truncada, a única em que o modelo viu todos os dados.
                if sonda_on and not emitiu_sonda:
                    t_snd = emit_sonda_block(
                        buf, log, it=it, fe=bud.fe, sonda=sonda_art,
                        adapter=adapter, model=model,
                        fe_treino_max=n_train - 1,
                        motivo="ultima iteracao (teto_wall DI-43/44)")
                    tempo_sonda_total += t_snd
                    n_blocos_sonda += 1
                    buf.update_timing(it, tempo_pred_sonda_s=t_snd)
                log.event("teto_wall_truncamento", it=it, fe=bud.fe,
                          criterio=criterio, elapsed_s=round(elapsed, 1),
                          max_wall_s=max_wall_s,
                          proj_restante_s=(None if proj_s is None
                                           else round(proj_s, 1)),
                          n_blocos_sonda=n_blocos_sonda,
                          acao="fecha failed/teto_wall GRAVANDO as camadas "
                               "parciais (DI-43/44 — curva parcial e o dado)")

            # D86: fim da iteração — solta tensores e coleta.
            del model, acqf, cands, acq_vals, post, train_X, train_Y, U_cand
            del passos, extras
            iteration_cleanup()
            if truncou_por_teto:
                break
    except _budget.BudgetExhausted:
        hard_stopped = True                       # D21/D61: fim limpo do laço
        iteration_cleanup()

    timing_totais = _export.manifest_timing_block(
        tempo_total_s=time.time() - t0,
        tempo_fit_surrogate_s=tempo_fit_total,
        tempo_busca_s=tempo_busca_total,
        tempo_aval_real_s=adapter.tempo_aval_real_s,
        tempo_pred_sonda_s=tempo_sonda_total,
        tempo_checkpoint_s=ckpt.tempo_total_s)          # [BL-11]
    out = write_run_outputs(
        exp, alg, problema, semente, bud, buf, adapter=adapter,
        doe_hash_sidecar=doe_art["doe_hash"], env=env, pinning=pinning,
        n_geracoes=n_iters_fit, algo_version=ALGO_VERSION,
        timing_totais=timing_totais, regime="online", q=int(q),
        # [DI-43] truncamento-com-dado: o teto fecha o run como `failed` MAS
        # com as camadas escritas — é o rito, não uma exceção ao rito.
        status=("failed" if truncou_por_teto else "ok"),
        motivo_parada=("teto_wall" if truncou_por_teto else None),
        params=_params_efetivos(q),            # [I-07/A4] a config no ⑤
        data_root=data_root, enable_bucket=enable_bucket)
    out["manifest"]["checkpoint"] = ckpt.resumo()
    out["manifest"]["acqf_ref_f"] = ref_f.tolist()
    out["manifest"]["fused_kernel"] = fused_policy["fused_kernel"]
    out["manifest"]["sigma_dict"] = _sigma_dict()       # DEF-C4 (obrigatório)
    out["manifest"]["sonda"] = {**_sonda_header(sonda_art),
                                "n_blocos": n_blocos_sonda,
                                "n_linhas": n_blocos_sonda * sonda_art["S"]}
    from src import manifest as _manifest
    _manifest.write_manifest(out["manifest"], data_root)

    # [DI-43] o footer não pode dizer 'ok' num run truncado: `status` mente e
    # `motivo_parada` não — a triagem tem de casar os dois (história do B1).
    log.footer(status=("failed" if truncou_por_teto else "ok"),
               motivo=("teto_wall" if truncou_por_teto else None),
               fe_final=bud.fe, n_geracoes=n_iters_fit,
               cache_hits=bud.cache_hits, cp_init=out["cp_init_ok"],
               n_blocos_sonda=n_blocos_sonda,
               n_checkpoints=ckpt.n_checkpoints,
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
