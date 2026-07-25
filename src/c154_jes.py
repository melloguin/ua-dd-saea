"""Runner do c154 — JES (Joint Entropy Search, BoTorch OFICIAL 0.18.1) sobre o
harness R2-00, no MOLDE do c262 (R2-c262).

Cartão R2-c154 (receita L.11; §22.3/N.1; I.11/E.1; a DEF-B9.5 está FECHADA
pela D75 — §6.4 é a DONA da receita). O algoritmo é o
qLowerBoundMultiObjectiveJointEntropySearch("LB") do BoTorch 0.18.1; NADA é
reimplementado: modelo, caminhos (Matheron/decoupled), otimizadores dos
caminhos, aquisição e otimização são as classes/helpers oficiais. Este módulo
só INTEGRA (adapter §5.5 + FEBudget + export §17) e INSTRUMENTA (jsonl
§17.5/S.7 + ③ com μ/σ do posterior + curva §17.6). **SEM julgamento de
fidelidade (D97)** — a validação é MANUAL do autor, a posteriori, em lote.

Receita por iteração (L.11 — a fonte; parâmetros também em params.json):
  - `torch.manual_seed(h0)` ANTES de modelo+acqf (uso_id 0 do seeds.json);
    usos 1..S = hs por amostra do caminho (MatheronPathModel); usos S+1..2S =
    hs' do NSGA-II (rota b) — fórmula D62/D91, trunc 32 bits, logadas.
  - Modelo COMO NO L.10 mas com **ruído INFERIDO** (B9.x — NÃO fixar
    `train_Yvar`): `SingleTaskGP` por objetivo com a likelihood DEFAULT do
    0.18.1 (prior LogNormal, piso 1e-4 — declarada no header do jsonl) +
    `covar_module=get_matern_kernel_with_gamma_prior(D)` (Matérn 5/2 ARD,
    rota Gamma 🔵 D30, como no c262) + `Standardize(m=1)` → `ModelListGP`;
    **refit from scratch por iteração (D44)** via `fit_gpytorch_mll`.
  - Pipeline pré-aquisição (B9.5/D75):
    * rota (a) PRODUÇÃO: S chamadas de `sample_optimal_points(num_samples=1,
      num_points=P, optimizer=random_search_optimizer,
      optimizer_kwargs={pop_size:1024, max_tries:10})`, cada uma sob
      `torch.manual_seed(hs)` — o 0.18.1 NÃO expõe seed no path (a nota
      "MatheronPathModel(seed=)" do bundle está desatualizada vs a lib
      instalada); o path E o Sobol do random_search consomem o RNG GLOBAL do
      torch (verificado nesta sessão), logo o hs por amostra do catálogo D91
      materializa-se por `manual_seed` antes de cada chamada.
      **Fallback OBRIGATÓRIO do `RuntimeError`** (random_search achou <P
      pontos ND): escada DETERMINÍSTICA (1024,10)→(2048,20)→(4096,40), sem
      re-seed (o stream segue), cada degrau logado como evento; esgotada a
      escada ⇒ RuntimeError pára-e-loga (D81). [Escada = definição do
      executor — item [IMPL] da B9.5; sinalizada p/ ratificação da torre.]
    * rota (b) PILOTO (checagem de fidelidade da D75, 1–2 problemas):
      `get_matheron_path_model` → `MultiOutputPosteriorMean` →
      `optimize_with_nsgaii(q=P, population_size=100, max_gen=500, seed=hs')`
      sob `preserve_global_rng` (N.1.3) com os 3 RNGs semeados
      (pymoo+np+random — L.11); guarda shape≠P (o helper pode devolver a
      população cheia com aviso). A truncagem HV-greedy é a INTERNA do helper
      oficial. Rodada nesta sessão com o token de namespace `c154b`
      (alg_id/sementes = 10, idênticos — comparação pareada), NUNCA na
      bateria.
  - `compute_sample_box_decomposition(pf)` (ref interno −1e10 do helper — o
    JES NÃO usa ref-point externo; difere do c262) →
    `qLowerBoundMultiObjectiveJointEntropySearch(model, ps, pf, hcb,
    estimation_type="LB")` — o __init__ já condiciona o modelo COM o ruído da
    likelihood (não há knob noiseless no MO); hazard do logdet inicial sem
    jitter mitigado por q=1 (card).
  - `optimize_acqf(q=1, num_restarts=5·D, raw_samples=1000·D — valores do
    PAPER, options={init_batch_limit — guarda de RAM NOSSA (D86), declarada},
    return_best_only=False)` → os 5D candidatos dos restarts (③, política
    BoTorch §17.4) + escolhido = argmax. Sem seed explícito no optimize_acqf:
    o catálogo D91 do c154 não define esse uso — a geração de ICs consome o
    RNG global (determinística, ancorada nos manual_seed).
  - **NaN-guard (§17.5 — guarda que loga quando dispara):** o estimador LB
    devolve não-finito em bolsões raros (~1/10⁴; covariância moment-matched
    não-PSD → logdet NaN mesmo com o jitter oficial — visto no DTLZ2 it 11,
    onde derrubava o `torch.multinomial` da seleção Boltzmann de ICs).
    Remédio: (i) os ICs são gerados pelo `gen_batch_initial_conditions`
    OFICIAL com a acqf embrulhada em `_NaNGuardedAcqfICs` (não-finito →
    pior-finito−1 SÓ na pontuação dos raw samples; guard `nan_guard_ics`);
    (ii) o escolhido é o argmax NAN-MASKED dos restarts (guard
    `nan_guard_argmax`; todos não-finitos ⇒ pára-e-loga D81). A acqf crua
    segue intocada na otimização L-BFGS e nos valores exportados.

③: μ/σ do `model.posterior` (modelo PRINCIPAL) nos candidatos dos restarts,
sob `no_grad` (D86); μ exportado = −mean (o sinal nunca vaza — §5.5); o
escolhido aponta `real_solution_id` pós-FE. ②: membership do train set.
§17.6: `add_timing(it, n_acumulado=bud.fe ANTES do infill, t_fit)` logo após
o fit — o t_fit é SÓ o fit_gpytorch_mll (mesma semântica do c262 → curvas
comparáveis); o estágio JES (paths+acqf) é BUSCA e vai desdobrado no jsonl
(`t_paths_s`/`t_busca_s` por iteração) e no manifesto.

jsonl S.7 (c154): rota (a-default/b-paper) B9.5; S fronts amostrados (shapes
+ valores em f, 6 casas); RuntimeError capturado (eventos da escada); valor
da acqf (escolhido + restarts); restarts 5D/1000D; h0/hs/hs' efetivos.

Política do kernel fusionado (DEF-L2/S.3#9): REPLICADA do c262 — OFF
explícito via `c262_qnehvi.disable_fused_kernel()` (a chamada de 1 linha que
o handoff R2-c262 manda). O JES não passa pelo logei, mas a política vale
p/ o processo (determinismo Mac×Linux) e fica registrada em jsonl+manifesto.

Guardas: hard-stop D21/D61 (`BudgetExhausted` = fim NATURAL); stall de
cache-hit D89/D60-b (teto 100); projeção de wall-clock (`max_wall_s` — teto
de 8h do ZDT1 no piloto; reuso do projetor do c262): estouro projetado aborta
LIMPO com a curva §17.6 parcial no jsonl — a decisão de completar é da
torre/autor (M7).

Módulo PESADO (torch/botorch) — importado LAZY pelo `_DISPATCH_LOADERS`.
"""

from __future__ import annotations

import random
import time
import warnings

import numpy as np
import torch

from src import budget as _budget
from src import export as _export
from src import naming
from src.audit_log import AuditLogger
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
    preserve_global_rng,
    sonda_due,
    torch_seed_for,
    write_run_outputs,
)
# Reuso deliberado do MOLDE (R2-c262): a política DEF-L2 (chamada blessada
# pelo handoff R2-c262), o fit L.10 (D44 — receita idêntica) e o projetor de
# wall-clock do piloto. Nada é duplicado; o c262 é código congelado da rodada.
from src.c262_qnehvi import (
    WallClockAbort,
    _WallClockProjector,
    _fit_models,
    _manifesto_failed_teto,
    disable_fused_kernel,
)

#: alg_id canônico do c154 no `artifacts/seeds.json` (D91).
C154_ALG_ID = 10

#: catálogo uso_id do c154 (seeds.json/D91): 0 = torch.manual_seed da
#: iteração; 1..S = hs por amostra do caminho; S+1..2S = hs' do NSGA-II (b).
USO_MANUAL_SEED = 0

#: parâmetros da receita L.11 (paper/§6.4 — Balde B congelado).
NUM_PARETO_SAMPLES = 10          # S (paper)
NUM_PARETO_POINTS = 10           # P (paper)
ESTIMATION_TYPE = "LB"           # recomendação explícita do paper
#: rota (a): random_search_optimizer (D75 — produção). Escada de fallback do
#: RuntimeError (obrigatório — L.11): degrau 1 = os valores do card.
RS_FALLBACK_LADDER = ((1024, 10), (2048, 20), (4096, 40))
#: rota (b): checagem de fidelidade do piloto (D75; pop-250 morta).
NSGAII_POP = 100
NSGAII_GEN = 500
#: optimize_acqf — fórmulas do PAPER (por dimensão D).
NUM_RESTARTS_PER_D = 5
RAW_SAMPLES_PER_D = 1000
#: [T9/DI-35.1] Aquisição batch-aware — SÓ no `exp=batch` (q>1). Calibrado POR
#: MEDIÇÃO (cartão T9; ZDT4/42, 1 core, serial; projeção pela PRÓPRIA curva medida
#: integrada nas 200 iterações — n→2099).
#: 🔴 ACHADO MEDIDO: ~10 h COMPLETO é INVIÁVEL no c154 batch com knob defensável.
#: O custo da aquisição JES-LB cresce ~n^1,5-1,7 (o posterior do GP por avaliação,
#: SEM prune de baseline — ≠ c262) e domina no n alto. Projeções diretas (ZDT4/D=10),
#: e o FLOOR sem extrapolação (t_busca das iters medidas + o resto ao ÚLTIMO valor
#: medido, i.e. crescimento ZERO — um piso, pois o custo AINDA acelerava):
#:   2D/50D (20/500)  → ~255 h  (floor 47 h)
#:   1D/50D (10/500)  → ~147 h  (FLOOR 30 h)   ⟵ ESTE (≈ default BoTorch 10/512)
#:   1D/25D (10/250)  → ~62 h   (floor 16 h)
#: TODO config mede FLOOR > o teto de 12 h ⇒ NENHUM knob defensável fecha 200 iters
#: em ~10 h. `1D/50D` é a MAIOR redução DEFENSÁVEL (≈ default da lib, ~10× mais
#: barato/optimize_acqf que o cheio): sob o teto de 12 h (DI-35.5) ele avança o
#: MÁXIMO no run antes de truncar (failed/teto_wall = dado). A escolha de estratégia
#: — {aceitar truncado · limitar nº de infills K_BATCH · redução mais agressiva ·
#: tirar o c154 do roster (T6 D-1b)} — é do AUTOR (D97/D81); ver
#: handoff/T9-calibracao_REPASSE.md. q=1 (principal) INTOCADO (regressão ①②③④
#: bit-a-bit). Knob é PER_D: em D alto custa ainda mais. NÃO altera paths (S=10).
NUM_RESTARTS_PER_D_BATCH = 1
RAW_SAMPLES_PER_D_BATCH = 50
#: guarda de RAM NOSSA (D86) — não vem do paper. 256 (≠32 do molde c262):
#: chunking de AVALIAÇÃO dos ICs, numericamente neutro (benchmark do piloto
#: em DTLZ2-like n=131/D=12/M=3: best idêntico 32×256×1024; 32→256 poupa
#: ~14% da busca; RAM folgada — os tensores do forward JES são pequenos).
ACQF_OPTIONS_STATIC = {"init_batch_limit": 256}

#: D60-b (guarda de stall): teto de iterações CONSECUTIVAS sem consumir FE.
MAX_STALL_ITERS = 100

ALGO_VERSION = "c154-JES/qLBMOJES-LB-botorch-0.18.1"


def _restarts_raw_for_q(q, D: int) -> tuple[int, int]:
    """[T9/DI-35.1] `(num_restarts, raw_samples)` EFETIVOS por `q`.

    - `q > 1` (batch): receita calibrada REDUZIDA (`*_PER_D_BATCH`) — ~10 h/run.
    - `q == 1` (principal): receita CHEIA do paper (5D/1000D) — **byte-idêntica**
      ao pré-T9 (a prova de regressão ①②③④ afere isto).

    Fonte ÚNICA: o runner (`_optimize_acqf_restarts`), o header/params e o
    teste-guarda leem daqui — nunca podem divergir do que roda de fato."""
    per_r = NUM_RESTARTS_PER_D_BATCH if int(q) > 1 else NUM_RESTARTS_PER_D
    per_s = RAW_SAMPLES_PER_D_BATCH if int(q) > 1 else RAW_SAMPLES_PER_D
    return per_r * int(D), per_s * int(D)


def _sonda_header(sonda_art: dict) -> dict:
    """O bloco `sonda` do header do jsonl — a certidão da régua usada (§17.2.2)."""
    return {"S": sonda_art["S"], "k": _H.SONDA_K,
            "cadencia": "1ª iteração, a cada k=2, e SEMPRE a última",
            "x_hash": sonda_art["x_hash"], "f_hash": sonda_art["f_hash"],
            "path": sonda_art["path"], "custo_fe": 0}


def _sigma_dict() -> dict:
    """`sigma_dict` (DEF-C4) — o dicionário semântico da ③ do c154, LEITURA
    OBRIGATÓRIA antes de usar a tabela (CONTRATO §3/R4 regra 3)."""
    return {
        "pred_tipo": "valor (regressor probabilístico)",
        "modelo_flag": "GP = SingleTaskGP por objetivo (ModelListGP), o modelo "
                       "PRINCIPAL — não os caminhos de Matheron do JES",
        "mu_j": "média do posterior do GP do objetivo j, em f de MINIMIZAÇÃO "
                "(o motor opera em −f; o export inverte — §5.5)",
        "sigma_j": "desvio-padrão do posterior (VAR-GP). ⚠ Difere do c262: o "
                   "ruído aqui é INFERIDO (B9.x — likelihood default do "
                   "0.18.1, prior LogNormal, piso 1e-4), não fixado em 1e-6",
        "espaco_modelo": "cru (o GP treina em [0,1]^D; a ③ grava x NATIVO)",
        "regime": "'sonda' = os 2000 pontos fixos do artefato §17.2.2, na "
                  "ORDEM do artefato (join com o gabarito POR POSIÇÃO); "
                  "'online' = os 5D candidatos dos restarts do optimize_acqf",
        "fe_treino_max": "maior fe_index no treino do GP no fit desta predição "
                         "(DI-09/A1 — filtro in-sample × out-of-sample)",
        "real_solution_id": "preenchido só na linha do candidato ESCOLHIDO que "
                            "de fato consumiu FE; NULL nos demais restarts e "
                            "em toda a sonda",
        # 🔴 A decisão da torre (DI-11 item 2 / DEFS-c154 §D-4) documentada
        # exatamente onde o CONTRATO §3 manda que a análise vá procurar.
        "jsonl_n_baseline": "AUSENTE POR DESENHO no c154. `n_baseline` é "
                            "conceito do qNEHVI (o X_baseline podado do "
                            "prune_baseline); o JES não tem X_baseline. Por "
                            "decisão da torre (DI-11), o c154 loga `n_train` — "
                            "o tamanho do conjunto de treino do GP na iteração "
                            "— e é ESSE o campo a usar na comparação com o "
                            "c262. NÃO são a mesma grandeza: n_train é o "
                            "arquivo inteiro, n_baseline é o subconjunto podado",
        "jsonl_acqf_todos_restarts": "os 5·D valores da acqf, um por restart (a "
                                     "paisagem da aquisição — DI-10). ⚠ Runs "
                                     "PRÉ-retrofit gravaram a mesma grandeza "
                                     "sob o nome `acqf_restarts`. Valores "
                                     "não-finitos são possíveis (NaN-guard do "
                                     "estimador LB) e ficam COMO ESTÃO aqui — "
                                     "a guarda age só na seleção",
    }


def uso_path(s: int) -> int:
    """uso_id do hs da amostra `s` (1-based) do caminho — catálogo D91: 1..S."""
    if not 1 <= s <= NUM_PARETO_SAMPLES:
        raise ValueError(f"amostra fora de 1..S: {s}")
    return s


def uso_nsgaii(s: int) -> int:
    """uso_id do hs' do NSGA-II da amostra `s` (rota b) — catálogo: S+1..2S."""
    if not 1 <= s <= NUM_PARETO_SAMPLES:
        raise ValueError(f"amostra fora de 1..S: {s}")
    return NUM_PARETO_SAMPLES + s


def _build_models(train_X: torch.Tensor, train_Y_max: torch.Tensor):
    """O modelo da receita: COMO NO c262/L.10 mas com ruído INFERIDO (B9.x —
    sem `train_Yvar`; likelihood default do 0.18.1). Matérn 5/2 ARD com prior
    Gamma (🔵 D30) + `Standardize(m=1)`, agregados num `ModelListGP`.
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
            covar_module=get_matern_kernel_with_gamma_prior(D),
            outcome_transform=Standardize(m=1)))
    return ModelListGP(*models)


def _sample_pareto_points_rs(model, D: int, semente: int, it: int, log):
    """Rota (a) — produção (D75): S amostras de (X*,Y*) via o helper OFICIAL
    `sample_optimal_points` + `random_search_optimizer`, 1 chamada POR amostra
    sob `torch.manual_seed(hs)` (usos 1..S — D91). Fallback do RuntimeError =
    escada determinística `RS_FALLBACK_LADDER` (sem re-seed; o stream segue),
    cada degrau logado; esgotada ⇒ propaga (pára-e-loga D81).
    Retorna (ps (S,P,D), pf (S,P,M), hs_list, n_fallbacks)."""
    from botorch.acquisition.multi_objective.utils import (
        random_search_optimizer,
        sample_optimal_points,
    )
    bounds = torch.stack([torch.zeros(D, dtype=torch.float64),
                          torch.ones(D, dtype=torch.float64)])
    ps_list, pf_list, hs_list = [], [], []
    n_fallbacks = 0
    for s in range(1, NUM_PARETO_SAMPLES + 1):
        hs = torch_seed_for(semente, C154_ALG_ID, it, uso_path(s))
        hs_list.append(hs)
        last_err = None
        for degrau, (pop_size, max_tries) in enumerate(RS_FALLBACK_LADDER):
            try:
                ps_s, pf_s = sample_optimal_points(
                    model=model, bounds=bounds,
                    num_samples=1, num_points=NUM_PARETO_POINTS,
                    optimizer=random_search_optimizer, maximize=True,
                    optimizer_kwargs={"pop_size": pop_size,
                                      "max_tries": max_tries})
                break
            except RuntimeError as err:            # <P pontos ND achados
                last_err = err
                n_fallbacks += 1
                log.event("rs_runtimeerror_fallback", it=it, amostra=s,
                          degrau_falho=degrau,
                          pop_size=pop_size, max_tries=max_tries,
                          erro=str(err)[:200])
        else:
            log.guard("rs_fallback_esgotado", it=it, amostra=s,
                      escada=list(RS_FALLBACK_LADDER))
            raise RuntimeError(
                f"c154 rota (a): random_search_optimizer falhou nas "
                f"{len(RS_FALLBACK_LADDER)} tentativas da escada p/ a amostra "
                f"{s} (it {it}) — {last_err}. Pára-e-loga (D81).")
        ps_list.append(ps_s)
        pf_list.append(pf_s)
    return torch.cat(ps_list), torch.cat(pf_list), hs_list, n_fallbacks


def _sample_pareto_points_nsgaii(model, D: int, M: int, semente: int, it: int,
                                 log):
    """Rota (b) — paper-faithful, SÓ piloto (checagem de fidelidade D75):
    por amostra s, `torch.manual_seed(hs)` (uso s) → caminho
    `get_matheron_path_model` → `MultiOutputPosteriorMean` →
    `optimize_with_nsgaii(q=P, pop=100, gen=500, seed=hs')` (uso S+s) com os
    3 RNGs semeados (pymoo+np+random — L.11) sob `preserve_global_rng`
    (N.1.3; o helper chama o pymoo.minimize por dentro). Truncagem HV-greedy
    = a interna do helper OFICIAL. Guarda shape≠P: >P ⇒ corte [:P] logado;
    <P ⇒ RuntimeError (pára-e-loga). Retorna (ps, pf, hs_list, hs2_list)."""
    from botorch.acquisition.multioutput_acquisition import (
        MultiOutputPosteriorMean,
    )
    from botorch.sampling.pathwise import get_matheron_path_model
    from botorch.utils.multi_objective.optimize import optimize_with_nsgaii
    bounds = torch.stack([torch.zeros(D, dtype=torch.float64),
                          torch.ones(D, dtype=torch.float64)])
    ps_list, pf_list, hs_list, hs2_list = [], [], [], []
    for s in range(1, NUM_PARETO_SAMPLES + 1):
        hs = torch_seed_for(semente, C154_ALG_ID, it, uso_path(s))
        hs_list.append(hs)
        path_model = get_matheron_path_model(model=model)
        pm_acqf = MultiOutputPosteriorMean(model=path_model)
        hs2 = iteration_seed(semente, C154_ALG_ID, it, uso_nsgaii(s),
                             bits32=True)
        hs2_list.append(hs2)
        with preserve_global_rng():                # N.1.3
            np.random.seed(hs2)                    # np.random.choice do helper
            random.seed(hs2)                       # L.11: semear os 3
            X_p, Y_p = optimize_with_nsgaii(
                acq_function=pm_acqf, bounds=bounds, num_objectives=M,
                q=NUM_PARETO_POINTS, population_size=NSGAII_POP,
                max_gen=NSGAII_GEN, seed=hs2)
        if X_p.shape[0] != NUM_PARETO_POINTS:      # guarda shape≠P (card)
            log.guard("nsgaii_shape_neq_P", it=it, amostra=s,
                      shape=list(X_p.shape), P=NUM_PARETO_POINTS)
            if X_p.shape[0] > NUM_PARETO_POINTS:
                X_p = X_p[:NUM_PARETO_POINTS]
                Y_p = Y_p[:NUM_PARETO_POINTS]
            else:
                raise RuntimeError(
                    f"c154 rota (b): optimize_with_nsgaii devolveu "
                    f"{X_p.shape[0]} < P={NUM_PARETO_POINTS} pontos "
                    f"(it {it}, amostra {s}). Pára-e-loga (D81).")
        ps_list.append(X_p.unsqueeze(0))
        pf_list.append(Y_p.unsqueeze(0))
        del path_model, pm_acqf
    return torch.cat(ps_list), torch.cat(pf_list), hs_list, hs2_list


def _make_acqf(model, ps: torch.Tensor, pf: torch.Tensor):
    """A aquisição da receita L.11: box decomposition OFICIAL (ref interno
    −1e10 do helper; o JES não usa ref-point externo) + qLBMOJES("LB"). O
    __init__ condiciona o modelo nos (X*,Y*) COM o ruído da likelihood."""
    from botorch.acquisition.multi_objective.joint_entropy_search import (
        qLowerBoundMultiObjectiveJointEntropySearch,
    )
    from botorch.acquisition.multi_objective.utils import (
        compute_sample_box_decomposition,
    )
    hcb = compute_sample_box_decomposition(pf)
    acqf = qLowerBoundMultiObjectiveJointEntropySearch(
        model=model, pareto_sets=ps, pareto_fronts=pf,
        hypercell_bounds=hcb, estimation_type=ESTIMATION_TYPE)
    return acqf, hcb


class _NaNGuardedAcqfICs(torch.nn.Module):
    """NaN-guard da SELEÇÃO DE ICs (§17.5 — guarda que LOGA quando dispara).

    O estimador LB do JES pode devolver não-finito em bolsões raros do espaço
    (a covariância M×M *moment-matched* da truncagem não é garantidamente PSD
    → `logdet` NaN mesmo com o jitter 1e-6 do código oficial — visto ao vivo
    no DTLZ2 it 11, ~1 ponto em 10⁴). O `initialize_q_batch` oficial trata
    +inf (baixa o η) mas NaN/−inf envenenam o `standardize`+`multinomial` e
    DERRUBAM o run. Este embrulho é usado SÓ para PONTUAR os raw samples na
    geração de ICs: troca valor não-finito pelo pior-finito−1 (⇒ o ponto
    nunca é escolhido como IC; se TUDO for não-finito, o Ystd==0 cai no
    fallback aleatório OFICIAL). A acqf crua segue intocada na otimização e
    no argmax. Fires contados p/ o jsonl."""

    def __init__(self, acqf):
        super().__init__()
        self.acqf = acqf
        self.n_nonfinite = 0

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        vals = self.acqf(X)
        bad = ~torch.isfinite(vals)
        if bad.any():
            self.n_nonfinite += int(bad.sum())
            finite = vals[~bad]
            floor = (float(finite.min()) - 1.0) if finite.numel() else -1e10
            vals = torch.where(bad, torch.full_like(vals, floor), vals)
        return vals


def _optimize_acqf_restarts(acqf, D: int, log, it: int, *, q: int = 1):
    """`optimize_acqf` da receita (q=1 por passo greedy) com `return_best_only=
    False` → TODOS os candidatos dos restarts (③ §17.4). Sem seed explícito
    (catálogo D91 do c154 não define esse uso; ICs saem do RNG global, ancorado
    nos manual_seed). Os ICs são gerados pelo gerador OFICIAL
    (`gen_batch_initial_conditions`) com o NaN-guard `_NaNGuardedAcqfICs` na
    pontuação (guarda logada); a otimização L-BFGS e os valores finais usam a
    acqf CRUA. Warnings contados (deslocam RNG).

    [T9/DI-35.1] `num_restarts`/`raw_samples` são batch-aware via
    `_restarts_raw_for_q(q, D)`: q=1 (principal) = 5D/1000D do PAPER, byte-
    idêntico; q>1 (batch) = a receita calibrada reduzida (~10 h/run)."""
    from botorch.optim import optimize_acqf
    from botorch.optim.initializers import gen_batch_initial_conditions
    num_restarts, raw_samples = _restarts_raw_for_q(q, D)
    bounds = torch.stack([torch.zeros(D, dtype=torch.float64),
                          torch.ones(D, dtype=torch.float64)])
    guarded = _NaNGuardedAcqfICs(acqf)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ics = gen_batch_initial_conditions(
            acq_function=guarded, bounds=bounds, q=1,
            num_restarts=num_restarts,
            raw_samples=raw_samples,
            options=dict(ACQF_OPTIONS_STATIC))
        cands, acq_vals = optimize_acqf(
            acqf, bounds=bounds, q=1,
            num_restarts=num_restarts,
            raw_samples=raw_samples,
            options=dict(ACQF_OPTIONS_STATIC),
            batch_initial_conditions=ics,
            sequential=False,          # sequential=(q>1); principal é q=1
            return_best_only=False)
    if guarded.n_nonfinite:
        log.guard("nan_guard_ics", it=it, n_nonfinite=guarded.n_nonfinite,
                  nota="acqf não-finita em raw samples — pontos rebaixados "
                       "ao pior-finito na seleção de ICs (LB/logdet não-PSD)")
    n_warn = sum(1 for w in caught
                 if "optimization" in str(w.message).lower()
                 or "trying again" in str(w.message).lower())
    return cands.detach(), acq_vals.detach(), n_warn


def _lote_greedy_sequencial_jes(acqf, D: int, log, it: int, q: int):
    """[T6-batch] O lote NATIVO do qLB-JES (D66) — greedy sequencial em q.

    Mesmo raciocínio do c262 (ver `_lote_greedy_sequencial` lá), com DOIS
    motivos a mais para transcrever o laço em vez de `optimize_acqf(q, seq)`:

    1. `return_best_only=False` (a ③ exige TODOS os restarts) é incompatível com
       `sequential=True` na API — idêntico ao c262.
    2. o c154 passa `batch_initial_conditions=ics` explícito, e o BoTorch
       PROÍBE isso sob sequencial (`UnsupportedError: batch_initial_conditions
       is not supported for sequential optimization`). O laço manual re-gera os
       ICs a cada passo (o correto: a acqf muda quando `X_pending` cresce).

    O JES condiciona no lote via `@concatenate_pending_points` no seu `forward`
    (verificado no 0.18.1): a entropia é conjunta sobre `[X, X_pending]`, então
    `set_X_pending` dos já escolhidos É o mecanismo de lote nativo (o bundle
    batch_largebatch.md: "qLB-JES batch … greedy sequencial; submodular").

    q=1 ⇒ 1 passo, sem tocar em `X_pending` = o principal INTOCADO.
    Devolve `[(cands, acq_vals, n_warn, idx_best), ...]`.

    ⚠ CAVEAT (B9.4, anotar no dado): q=10 extrapola o máx do paper (q=8) e o
    lower bound do JES NÃO é monotônico — o ganho por passo pode não decrescer.
    É esperado; não é bug. O `motivo` do log registra o passo.
    """
    def _argmax_finito(acq_vals):
        m = torch.isfinite(acq_vals)
        if not bool(m.any()):
            raise RuntimeError(
                f"c154: TODOS os restarts com acqf não-finita no lote (it {it}). "
                f"Pára-e-loga (D81).")
        masked = torch.where(m, acq_vals,
                             torch.full_like(acq_vals, float("-inf")))
        return int(torch.argmax(masked))

    if int(q) == 1:                       # ← caminho do principal, intocado
        cands, acq_vals, n_warn = _optimize_acqf_restarts(acqf, D, log, it)
        return [(cands, acq_vals, n_warn, _argmax_finito(acq_vals))]

    base_pending = acqf.X_pending
    passos, escolhidos = [], []
    try:
        for _p in range(int(q)):
            if escolhidos:
                novos = torch.cat(escolhidos, dim=-2)
                acqf.set_X_pending(
                    novos if base_pending is None
                    else torch.cat([base_pending, novos], dim=-2))
            # [T9] q>1 aqui (o ramo q==1 saiu antes) ⇒ receita batch reduzida.
            cands, acq_vals, n_warn = _optimize_acqf_restarts(
                acqf, D, log, it, q=q)
            b = _argmax_finito(acq_vals)
            escolhidos.append(cands[b].detach().reshape(1, -1))
            passos.append((cands, acq_vals, n_warn, b))
    finally:
        acqf.set_X_pending(base_pending)
    return passos


def run_c154(exp: str, alg: str, problema: str, semente, *,
             data_root: str = naming.DEFAULT_DATA_ROOT,
             enable_bucket: bool = False,
             max_wall_s: float | None = None,
             teto_s: float | None = None,
             rota: str = "a", q: int = 1, **_kwargs) -> dict:
    """Um run c154 (q=1) — assinatura padrão dos runners R2. `rota` ∈ {'a'
    (produção, D75), 'b' (paper-faithful; SÓ piloto — chamar com o token de
    namespace `alg='c154b'` p/ não colidir com o run de produção)}.
    `max_wall_s` liga a projeção de teto do piloto (8h no ZDT1); estouro
    projetado ⇒ aborto limpo + RuntimeError (pára-e-loga D81)."""
    if rota not in ("a", "b"):
        raise ValueError(f"rota B9.5 inválida: {rota!r} (esperado 'a'|'b')")
    # [T6-batch] o despachante da bateria passa `teto_s` (fio unificado); o c154
    # implementa o teto via `max_wall_s` (o projetor). São o MESMO conceito —
    # mapeia p/ que o cap de 4h do batch chegue de fato aqui (senão `teto_s`
    # cairia em `**_kwargs` e o run correria sem teto). NO-OP quando teto_s=None
    # (o principal q=1 — a prova de regressão fica intocada).
    if max_wall_s is None and teto_s is not None:
        max_wall_s = float(teto_s)
    t0 = time.time()
    pinning = pin_runtime()
    env = env_info()                          # guarda N.2.3 (fork ⇒ RuntimeError)
    fused_policy = disable_fused_kernel()     # DEF-L2 replicada do c262
    semente = int(semente)

    doe_art = load_doe(problema, semente, data_root=data_root)
    # SONDA DI-09/§17.2.2: CARREGADA 1× (hash conferido) antes de abrir o log —
    # artefato ausente/corrompido pára o run ANTES de gastar FE (como o DoE).
    sonda_art = load_sonda(problema, data_root=data_root)

    log = AuditLogger.for_run(exp, alg, problema, semente,
                              data_root=data_root, append=False)
    try:
        return _run_c154_body(exp, alg, problema, semente, t0, pinning, env,
                              fused_policy, doe_art, sonda_art, rota, log,
                              data_root, enable_bucket, max_wall_s, int(q))
    except Exception:
        # D23/D60: parada anômala NUNCA silenciosa — footer failed no jsonl.
        import traceback
        log.footer(status="failed", stack=traceback.format_exc()[-2000:])
        raise
    finally:
        log.close()


def _run_c154_body(exp, alg, problema, semente, t0, pinning, env, fused_policy,
                   doe_art, sonda_art, rota, log, data_root, enable_bucket,
                   max_wall_s, q=1) -> dict:
    # [T6-batch] orcamento POR EXP (D66): main = 31D-1; batch = 11D-1+200q.
    _D0 = doe_art["X"].shape[1]
    bud = _budget.FEBudget(
        D=_D0, maxfe=_budget.maxfe_por_exp(exp, _D0, q), logger=log)
    adapter = BoTorchProblemAdapter(problema, bud)
    D, M = adapter.D, adapter.M
    buf = SnapshotBuffer()
    # [T9/DI-35.1] EFETIVOS por exp: q=1 = 5D/1000D (paper, header idêntico ao
    # pré-T9); batch (q>1) = a receita calibrada reduzida. Mesma fonte do runner.
    num_restarts, raw_samples = _restarts_raw_for_q(q, D)

    log.header(run_id=naming.run_id(exp, alg, problema, semente),
               alg=alg, alg_id=C154_ALG_ID, problema=problema, D=D, M=M,
               semente=semente, regime="online", maxfe=bud.maxfe,
               doe_hash=doe_art["doe_hash"], env=env, pinning=pinning,
               algo_version=ALGO_VERSION,
               rota_b95=rota,
               fused_kernel=fused_policy["fused_kernel"],
               ruido=("INFERIDO (B9.x — sem train_Yvar; likelihood default "
                      "0.18.1: prior LogNormal, piso 1e-4)"),
               acqf_ref=("JES não usa ref-point externo; box decomposition "
                         "com ref interno -1e10 do helper oficial"),
               sonda=_sonda_header(sonda_art),
               sigma_dict=_sigma_dict(),
               params={"S": NUM_PARETO_SAMPLES, "P": NUM_PARETO_POINTS,
                       "estimation_type": ESTIMATION_TYPE,
                       "rs_ladder": list(RS_FALLBACK_LADDER),
                       "nsgaii_pop": NSGAII_POP, "nsgaii_gen": NSGAII_GEN,
                       "num_restarts": num_restarts,        # 5D/1000D no q=1;
                       "raw_samples": raw_samples,          # reduzido no batch (T9)
                       "q": int(q), "refit": "from-scratch/iter (D44)",
                       "kernel": "Matern-5/2-ARD gamma-prior (D30)",
                       "acqf": "qLBMOJES-LB L.11",
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
    tempo_paths_total = 0.0
    tempo_sonda_total = 0.0                    # DI-09 (agregado do manifesto)
    n_blocos_sonda = 0                         # blocos de 2000 linhas emitidos
    rs_fallbacks_total = 0
    hard_stopped = False
    stall_streak = 0
    it = 0
    n_iters_fit = 0
    try:
        while True:
            it += 1
            t_it0 = time.time()
            # L.11: manual_seed ANTES de modelo+acqf (uso 0 — D91).
            h0 = torch_seed_for(semente, C154_ALG_ID, it, USO_MANUAL_SEED)

            # §17.6: o fit desta iteração treina com os pontos JÁ avaliados.
            n_train = bud.fe
            X_nat = np.vstack([r.x for r in bud.records])
            F_min = np.vstack([r.f for r in bud.records])
            train_X = adapter.to_unit(X_nat)
            train_Y = torch.as_tensor(-F_min, dtype=torch.float64)

            t_fit0 = time.time()
            model = _build_models(train_X, train_Y)
            fit_retries, modelo_hp = _fit_models(model)  # +modelo_hp (DI-10/B1)
            tempo_fit = time.time() - t_fit0
            tempo_fit_total += tempo_fit
            n_iters_fit = it
            # DI-09/A1: o modelo desta iteração viu os fe_index 0..n_train−1 —
            # toda linha ③ emitida daqui em diante herda o marcador.
            buf.set_fe_treino_max(n_train - 1)
            # timing ANTES do infill: a curva §17.6 retém o fit final mesmo
            # quando o hard-stop corta a iteração (D61). Busca/sonda/geração
            # entram por `update_timing` no fim da iteração.
            buf.add_timing(it, n_acumulado=n_train, tempo_fit_s=tempo_fit)
            log.timing(n_acumulado=n_train, tempo_fit_s=tempo_fit, it=it)
            # ②: o arquivo real que o modelo VIU nesta iteração.
            buf.add_pop(it, range(n_train))

            # o estágio JES (paths + acqf + otimização) é BUSCA (§17.6).
            t_busca0 = time.time()
            hs2_list = None
            if rota == "a":
                ps, pf, hs_list, n_fb = _sample_pareto_points_rs(
                    model, D, semente, it, log)
                rs_fallbacks_total += n_fb
            else:
                ps, pf, hs_list, hs2_list = _sample_pareto_points_nsgaii(
                    model, D, M, semente, it, log)
            # o random_search_optimizer avalia o posterior SEM no_grad → os
            # tensores voltam com grad; solta o grafo (D86; e o export/log
            # não diferencia nada).
            ps, pf = ps.detach(), pf.detach()
            t_paths = time.time() - t_busca0
            tempo_paths_total += t_paths

            acqf, hcb = _make_acqf(model, ps, pf)
            # [T6-batch] LOTE NATIVO: q passos gulosos sequenciais (D66).
            # q=1 ⇒ 1 passo sem X_pending = o principal INTOCADO.
            passos = _lote_greedy_sequencial_jes(acqf, D, log, it, q)
            cands, acq_vals, acqf_warns, _best0 = passos[0]
            tempo_busca = time.time() - t_busca0
            tempo_busca_total += tempo_busca
            if acqf_warns:
                log.event("optimize_acqf_warning", it=it, n=acqf_warns,
                          nota="retry/warning desloca o RNG (registrado)")

            # ③: μ/σ do posterior do modelo PRINCIPAL nos restarts (D86).
            U_cand = cands.squeeze(1)             # (num_restarts, D); 5D no q=1
            with torch.no_grad():
                post = model.posterior(U_cand)
                mu_max = post.mean.cpu().numpy()            # −f (maximização)
                sigma = np.sqrt(post.variance.cpu().numpy())
            mu_f = -mu_max                       # export SEMPRE em f (§5.5)
            # argmax nan-masked (mesmo NaN-guard §17.5: restart não-finito
            # nunca é o escolhido; TODOS não-finitos ⇒ pára-e-loga D81).
            finite_mask = torch.isfinite(acq_vals)
            if not bool(finite_mask.all()):
                log.guard("nan_guard_argmax", it=it,
                          n_nonfinite=int((~finite_mask).sum()))
                if not bool(finite_mask.any()):
                    raise RuntimeError(
                        f"c154: TODOS os {int(acq_vals.numel())} restarts "
                        f"devolveram acqf não-finita (it {it}). "
                        f"Pára-e-loga (D81).")
            masked = torch.where(finite_mask, acq_vals,
                                 torch.full_like(acq_vals, float("-inf")))
            best = int(torch.argmax(masked))
            acqf_best = float(acq_vals[best])
            X_cand_nat = adapter.to_native(U_cand)

            # [T6-batch] ③ dos passos 2..q do lote (vazio quando q=1): a ③ de
            # cada passo guloso — o NÃO-escolhido agora, o escolhido após o FE.
            extras = []           # [(X_nat, mu, sigma, idx_best, acqf_best), ...]
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
                extras.append((X_i, mu_i, sig_i, best_i, float(acqv_i[best_i]),
                               U_i))
                del post_i

            for k in range(U_cand.shape[0]):
                if k == best:
                    continue                     # o escolhido entra após o FE
                buf.add_surrogate(_export.surrogate_row(
                    it, X_cand_nat[k],
                    mu=mu_f[k], sigma=sigma[k],
                    pred_tipo="valor", modelo_flag="GP"))

            # S.7: os S fronts amostrados — shapes + valores em f (−pf).
            pf_f = (-pf).cpu().numpy()
            decision_extra = dict(
                rota=rota, torch_seed=h0, hs_paths=hs_list,
                pf_shape=list(pf.shape), ps_shape=list(ps.shape),
                pf_amostrados_f=np.round(pf_f, 6).tolist(),
                n_restarts=num_restarts, raw_samples=raw_samples,
                t_paths_s=round(t_paths, 4))
            if hs2_list is not None:
                decision_extra["hs_nsgaii"] = hs2_list

            def di10():
                """Os campos DI-10 do `<alg>_gen` TIRADOS NO MOMENTO DO LOG —
                `fe`/`f_best`/`n_front1` refletem o arquivo depois (ou não) do
                infill, conforme o ramo que chamar. `n_baseline` NÃO existe no
                JES (DI-11): o campo comparável é `n_train`, documentado no
                `sigma_dict`."""
                return dict(
                    fe=bud.fe, modelo_hp=modelo_hp, n_train=n_train,
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
                             acqf_escolhido=acqf_best,
                             **decision_extra, **di10())
                # §17.2.2: esta É a última iteração — a sonda é OBRIGATÓRIA
                # nela. O bloco desta iteração ainda não saiu (o ponto de
                # emissão é a jusante do infill, que acabou de levantar), e o
                # modelo desta iteração continua vivo aqui.
                t_snd = emit_sonda_block(
                    buf, log, it=it, fe=bud.fe, sonda=sonda_art,
                    adapter=adapter, model=model,
                    fe_treino_max=n_train - 1,
                    motivo="ultima iteracao (hard-stop D61)")
                tempo_sonda_total += t_snd
                n_blocos_sonda += 1
                buf.update_timing(it, tempo_busca_s=tempo_busca,
                                  tempo_pred_sonda_s=t_snd,
                                  tempo_geracao_s=(time.time() - t_it0) - t_snd)
                raise
            sid = bud.solution_id_of(X_cand_nat[best])
            buf.add_surrogate(_export.surrogate_row(
                it, X_cand_nat[best], real_solution_id=sid,
                mu=mu_f[best], sigma=sigma[best],
                pred_tipo="valor", modelo_flag="GP"))

            # [T6-batch] os FE dos passos 2..q do lote (vazio quando q=1).
            # Orçamento governa (D61): estouro NO MEIO do lote segue o MESMO
            # rito do passo 1 (③ sem real_solution_id + sonda obrigatória).
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
                                 acqf_escolhido=acqv_i, q=q,
                                 n_no_lote=len(sids_lote),
                                 **decision_extra, **di10())
                    t_snd = emit_sonda_block(
                        buf, log, it=it, fe=bud.fe, sonda=sonda_art,
                        adapter=adapter, model=model,
                        fe_treino_max=n_train - 1,
                        motivo="ultima iteracao (hard-stop D61, lote parcial)")
                    tempo_sonda_total += t_snd
                    n_blocos_sonda += 1
                    buf.update_timing(
                        it, tempo_busca_s=tempo_busca,
                        tempo_pred_sonda_s=t_snd,
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
                         motivo="argmax do qLBMOJES-LB nos restarts (L.11)",
                         it=it, acqf_escolhido=acqf_best,
                         fit_retries=fit_retries, acqf_warnings=acqf_warns,
                         solution_id=sid, cache_hit=cache_hit_iter,
                         q=q, lote_solution_ids=sids_lote,
                         t_busca_s=round(tempo_busca, 4),   # legado (compat.)
                         **decision_extra, **di10())

            # SONDA §17.2.2 — DEPOIS da busca da iteração (isolamento máximo) e
            # ANTES do `del model`. Cadência k=2 + 1ª; a última é coberta no
            # ramo do hard-stop acima. ZERO FE, RNG preservado.
            t_snd = 0.0
            if sonda_due(it):
                t_snd = emit_sonda_block(
                    buf, log, it=it, fe=bud.fe, sonda=sonda_art,
                    adapter=adapter, model=model, fe_treino_max=n_train - 1)
                tempo_sonda_total += t_snd
                n_blocos_sonda += 1
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
                    f"c154 estagnado: {stall_streak} iterações consecutivas "
                    f"sem consumir FE (só duplicatas D89) — D60-b. "
                    f"Pára-e-loga (D81).")

            # D86: fim da iteração — solta tensores e coleta.
            del (model, acqf, hcb, ps, pf, cands, acq_vals, post, train_X,
                 train_Y, U_cand)
            iteration_cleanup()

            # projeção do teto de wall-clock do piloto (ZDT1 ≤ 8h).
            proj.add(n_train, tempo_fit, time.time() - t_it0)
            over, proj_s, elapsed, criterio = proj.exceeded(bud.fe)
            if over:
                log.event("wall_projection_abort", it=it, fe=bud.fe,
                          criterio=criterio,          # 'elapsed' | 'projecao'
                          elapsed_s=round(elapsed, 1),
                          proj_restante_s=(None if proj_s is None
                                           else round(proj_s, 1)),
                          max_wall_s=max_wall_s)
                # [D-07/DI-21] mesmo padrão do c262/c122: failed no disco
                # ANTES do raise (cenário B-2 da auditoria).
                _manifesto_failed_teto(exp, alg, problema, semente, data_root,
                                       criterio=criterio, elapsed_s=elapsed,
                                       fe=bud.fe, maxfe=bud.maxfe)
                raise WallClockAbort(
                    f"teto de wall-clock do piloto estourado por "
                    f"'{criterio}': {elapsed:.0f}s decorridos"
                    + ("" if proj_s is None
                       else f" + {proj_s:.0f}s projetados")
                    + f" > {max_wall_s:.0f}s (fe={bud.fe}/{bud.maxfe}). Aborto "
                      f"LIMPO — curva §17.6 parcial no jsonl + manifesto "
                      f"failed. A decisão de completar é da torre/autor (M7). "
                      f"Pára-e-loga (D81).")
    except _budget.BudgetExhausted:
        hard_stopped = True                       # D21/D61: fim limpo do laço
        iteration_cleanup()

    timing_totais = _export.manifest_timing_block(
        tempo_total_s=time.time() - t0,
        tempo_fit_surrogate_s=tempo_fit_total,
        tempo_busca_s=tempo_busca_total,
        tempo_aval_real_s=adapter.tempo_aval_real_s,
        tempo_pred_sonda_s=tempo_sonda_total,
        tempo_paths_s=round(tempo_paths_total, 4))   # desdobramento do JES
    out = write_run_outputs(
        exp, alg, problema, semente, bud, buf, adapter=adapter,
        doe_hash_sidecar=doe_art["doe_hash"], env=env, pinning=pinning,
        n_geracoes=n_iters_fit, algo_version=ALGO_VERSION,
        timing_totais=timing_totais, regime="online", q=int(q),
        data_root=data_root, enable_bucket=enable_bucket)
    out["manifest"]["fused_kernel"] = fused_policy["fused_kernel"]
    out["manifest"]["sigma_dict"] = _sigma_dict()       # DEF-C4 (obrigatório)
    out["manifest"]["sonda"] = {**_sonda_header(sonda_art),
                                "n_blocos": n_blocos_sonda,
                                "n_linhas": n_blocos_sonda * sonda_art["S"]}
    out["manifest"]["jes"] = {
        "rota_b95": rota, "S": NUM_PARETO_SAMPLES, "P": NUM_PARETO_POINTS,
        "estimation_type": ESTIMATION_TYPE,
        "num_restarts": num_restarts, "raw_samples": raw_samples,
        "rs_fallbacks_total": rs_fallbacks_total,
        "tempo_paths_s": round(tempo_paths_total, 4),
    }
    from src import manifest as _manifest
    _manifest.write_manifest(out["manifest"], data_root)

    log.footer(status="ok", fe_final=bud.fe, n_geracoes=n_iters_fit,
               cache_hits=bud.cache_hits, cp_init=out["cp_init_ok"],
               rs_fallbacks_total=rs_fallbacks_total,
               n_blocos_sonda=n_blocos_sonda,
               hard_stopped=hard_stopped)

    return {
        "D": D, "M": M, "maxfe": bud.maxfe, "fe_final": bud.fe,
        "n_init": bud.n_init, "n_iters": n_iters_fit,
        "cache_hits": bud.cache_hits, "hard_stopped": hard_stopped,
        "cp_init_ok": out["cp_init_ok"],
        "doe_hash_run": out["doe_hash_run"],
        "rota_b95": rota,
        "rs_fallbacks_total": rs_fallbacks_total,
        "fused_kernel": fused_policy["fused_kernel"],
        "timing_totais": timing_totais,
        "tempo_paths_s": round(tempo_paths_total, 4),
        "fit_series": buf.fit_series,
        "upload_status": out["upload_status"],
    }


__all__ = [
    "C154_ALG_ID", "USO_MANUAL_SEED", "uso_path", "uso_nsgaii",
    "NUM_PARETO_SAMPLES", "NUM_PARETO_POINTS", "ESTIMATION_TYPE",
    "RS_FALLBACK_LADDER", "NSGAII_POP", "NSGAII_GEN",
    "NUM_RESTARTS_PER_D", "RAW_SAMPLES_PER_D",
    "NUM_RESTARTS_PER_D_BATCH", "RAW_SAMPLES_PER_D_BATCH",
    "_restarts_raw_for_q", "run_c154",
]
