"""[T6-batch] `sobol_batch` — o PISO do sub-estudo batch (D66/DI-33).

O piso do batch q=10: a cada iteração propõe um lote de `q` pontos por **Sobol
SCRAMBLED (Owen)** e os avalia na função REAL — **sem surrogate, sem aquisição**.
Isola a pergunta central do sub-estudo: *"o surrogate + a aquisição compram algo
sobre lotear ao acaso?"* (batch_largebatch.md V-B.2).

**É um PISO ONLINE** (avaliação real via `FEBudget`), não offline:
  - DoE init = 11D−1 do artefato (D63/D87/D88 — **PAREADO com o principal**,
    NUNCA regenerado), fase `init`;
  - K=200 iterações de lote (`maxfe_por_exp('batch', D, q)` = 11D−1 + 200·q),
    cada uma = um lote Sobol de `q` pontos avaliados no real, fase `opt`;
  - **SEM modelo** ⇒ **③ VAZIA** e **SEM sonda** (CONTRATO §6.1 linha "pisos":
    o piso online não tem surrogate nem régua). ④ com `tempo_fit_s=NULL`
    (não há fit). ①②④⑤⑥ completos; ⑦ é só dos OFFLINE (não se aplica).

**Determinismo (D62/D91).** O Sobol de cada iteração é semeado por
`iteration_seed(seed_base(alg, semente), 22, iter, 0)` — `alg_id=22` já
provisionado no `seeds.json` (DI-33). Cada iteração tem seu Sobol independente e
reprodutível; 2 runs ⇒ ① bit-a-bit.

**Fidelidade = validação MANUAL do autor (D97).** Este módulo só instrumenta.
"""
from __future__ import annotations

# ⚠ ORDEM: o `standalone_harness` pina as env vars de thread (D79/N.1.1) no
# TOPO, ANTES de qualquer `import numpy`.
from src import standalone_harness as H
from src.checkpoint import Checkpointer as _Checkpointer   # [DI-43]

import time

import numpy as np

from src import export as _export
from src import naming
from src.budget import BudgetExhausted, FEBudget, maxfe_por_exp

#: alg_id canônico — `artifacts/seeds.json:alg_id` (DI-33; há teste-guarda).
ALG_ID = 22
#: uso_id do Sobol da iteração (0 = o único RNG do piso).
USO_SOBOL = 0
#: q do experimento principal (o piso só existe no batch; o grid usa q=10).
Q_PRINCIPAL = 1
ALGO_VERSION = "sobol_batch-1.0"


def _oracle(problema: str):
    """Avaliador de 1 ponto na função REAL (float64), p/ o `FEBudget`."""
    from src import problems as _problems
    prob = H._instantiate(problema)

    def true_f(x: np.ndarray) -> np.ndarray:
        F = _problems.evaluate_problem(
            prob, np.asarray(x, dtype=np.float64).reshape(1, -1))
        return np.asarray(F, dtype=np.float64).reshape(-1)

    return prob, true_f


def _sobol_batch01(D: int, q: int, seed: int) -> np.ndarray:
    """Um lote de `q` pontos Sobol SCRAMBLED (Owen) em [0,1]^D, semeado.

    `scramble=True` = randomização de Owen (o "scrambled/Owen" do contrato).
    A semente vem de `iteration_seed` ⇒ cada iteração tem seu Sobol próprio e
    reprodutível. `random_base2` daria potências de 2 (a propriedade de
    balanceamento do Sobol); com q=10 não-potência usamos `random(q)` — o lote
    do sub-estudo é q FIXO (D36), a propriedade de balanceamento não é exigida
    pelo contrato (o piso é a ablação "ao acaso").
    """
    import warnings
    from scipy.stats import qmc
    sob = qmc.Sobol(d=int(D), scramble=True, seed=int(seed))
    with warnings.catch_warnings():
        # q=10 não é potência de 2 ⇒ o scipy avisa que a propriedade de
        # balanceamento se perde. É ESPERADO e documentado (o lote do
        # sub-estudo é q fixo, D36); silenciado p/ não poluir o log do piso.
        warnings.filterwarnings("ignore", message=".*balance properties.*")
        return np.asarray(sob.random(int(q)), dtype=np.float64)


def run_sobol_batch(exp: str, alg: str, problema: str, semente, *,
                    data_root: str = naming.DEFAULT_DATA_ROOT,
                    enable_bucket: bool = False,
                    teto_s: float | None = None,
                    q: int = Q_PRINCIPAL, **_kwargs) -> dict:
    """Roda o piso Sobol-batch sob o contrato v5.2.1. Assinatura padrão.

    `teto_s` (opcional): teto de wall-clock — aborto LIMPO (manifesto
    `failed`/`teto_wall`, D61/§22.5). `q` = tamanho do lote (10 no grid batch).
    """
    t_run = time.time()
    pinning = H.pin_runtime()
    env = H.env_info()
    semente = int(semente)
    q = int(q)

    log = H.AuditLogger.for_run(exp, alg, problema, semente,
                                data_root=data_root, append=False)
    doe = H.load_doe(problema, semente, data_root=data_root)
    D = int(doe["X"].shape[1])
    bud = FEBudget(D=D, maxfe=maxfe_por_exp(exp, D, q), logger=log)
    prob, true_f = _oracle(problema)
    M = int(prob.n_obj)
    if doe["X"].shape[0] != bud.n_init:
        raise RuntimeError(
            f"DoE com {doe['X'].shape[0]} pontos != 11D−1 = {bud.n_init} "
            f"— pára-e-loga (D81).")
    xl, xu = H._bounds(problema)

    buf = H.SnapshotBuffer()
    # [DI-43] checkpoint atômico periódico — 25 gerações OU 30 min.
    ckpt = _Checkpointer(exp, alg, problema, semente, D=D, M=M,
                         regime="online", q=int(q), data_root=data_root, log=log)
    base = H.seed_base(alg, semente)
    status, motivo_parada = "ok", "orcamento"
    n_geracoes = 0

    #: CONTRATO §6.1 (linha "pisos"): SEM surrogate ⇒ ③ VAZIA, SEM sonda.
    sigma_dict = {
        "modelo": "PISO Sobol-batch — SEM surrogate (a ablação 'ao acaso'; "
                  "batch_largebatch.md V-B.2). A ③ SAI VAZIA por construção.",
        "regime": "online = avaliação real de lotes Sobol; NÃO há regime sonda "
                  "(piso online não tem régua §17.2.2).",
        "mu_*": "N/A (sem modelo).", "sigma_*": "N/A (sem modelo).",
        "sonda": "AUSENTE (piso online — CONTRATO §6.1).",
        "modelo_hp": "NULL (não há modelo a ajustar; ④ com tempo_fit_s=NULL).",
        "lote": f"q={q} pontos Sobol SCRAMBLED/Owen por iteração, semeados por "
                f"iteration_seed(base, {ALG_ID}, iter, {USO_SOBOL}).",
    }

    try:
        log.header(alg=alg, versao=ALGO_VERSION, problema=problema, D=D, M=M,
                   semente=semente, regime="online", maxfe=bud.maxfe,
                   doe_hash=doe["doe_hash"], ambiente=env, pinning=pinning,
                   sigma_dict=sigma_dict, q=q)

        # ── DoE init (fase 'init'): 11D−1 do artefato, PAREADO (D88) ─────────
        for x in doe["X"]:
            bud.evaluate(np.asarray(x, dtype=np.float64), true_f)
        buf.add_pop(0, [r.solution_id for r in bud.records])

        # ── K=200 iterações de LOTE Sobol (fase 'opt') ──────────────────────
        g = 0
        try:
            while bud.fe < bud.maxfe:
                g += 1
                t_g0 = time.time()
                seed_it = H.iteration_seed(base, ALG_ID, g, USO_SOBOL,
                                           bits32=True)
                lote01 = _sobol_batch01(D, q, seed_it)
                lote_nat = xl + lote01 * (xu - xl)     # [0,1]^D → nativo
                t_busca = time.time() - t_g0
                for x in lote_nat:
                    bud.evaluate(np.asarray(x, dtype=np.float64), true_f)
                # ② membership: o arquivo REAL corrente (todo o histórico)
                buf.add_pop(g, [r.solution_id for r in bud.records])
                # ④: SEM fit (tempo_fit_s=NULL — piso sem modelo)
                buf.add_timing(geracao=g, n_acumulado=bud.fe, tempo_fit_s=None)
                buf.update_timing(g, tempo_busca_s=t_busca,
                                  tempo_pred_sonda_s=0.0,
                                  tempo_geracao_s=(time.time() - t_g0))
                ckpt.talvez_gravar(bud, buf, iteracao=g)   # [DI-43]
                # [BL-11] I/O do checkpoint à parte — roda DEPOIS de a ④ da
                # geração fechar, logo fica FORA do `tempo_geracao_s` (DI-13.10).
                buf.update_timing(g,
                                  tempo_checkpoint_s=ckpt.consumir_tempo_s())
                # [I-03] o MÍNIMO COMUM DI-10 pelo helper, não à mão. Este era
                # o ÚNICO dos 47 pares (alg,exp) do estudo sem `n_front1` — o
                # evento era montado aqui em vez de chamar
                # `H.minimo_comum_di10`, e o campo faltou também no header, nos
                # 2 footers e nas 31 chaves do ⑤. Custo medido de gravá-lo:
                # `problems._nds_filter` × 200 gerações = 0,020–0,052 s =
                # 0,3–1,6% do wall. `tempo_fit_s=None` (piso sem modelo, DI-13.2)
                # e `tempo_busca_s` sobe ao ⑥ de brinde.
                log.decision(caminho="sobol_batch_gen",
                             motivo=f"lote Sobol scrambled q={q} (piso — sem "
                                    f"surrogate)",
                             geracao=g, q=q, seed_sobol=int(seed_it),
                             **H.minimo_comum_di10(
                                 np.vstack([r.f for r in bud.records]),
                                 fe=bud.fe, tempo_fit_s=None,
                                 tempo_busca_s=t_busca))
                n_geracoes = g
                if teto_s is not None and (time.time() - t_run) > teto_s:
                    status, motivo_parada = "failed", "teto_wall"
                    log.guard("teto_wall", geracao=g, fe=bud.fe,
                              decorrido_s=round(time.time() - t_run, 1),
                              teto_s=teto_s,
                              acao="ABORTO LIMPO — curva parcial; manifesto "
                                   "failed (D-07); completar é do M7 (D81)")
                    break
        except BudgetExhausted:
            log.guard("hard_stop_capturado", fe=bud.fe, maxfe=bud.maxfe,
                      motivo="fim natural do orcamento (D61)")

        # ③ VAZIA (piso) — mas a camada TEM de existir (LAYERS). buf.surr_rows
        # segue vazio ⇒ write_surrogate grava um parquet de 0 linhas.
        timing_totais = _export.manifest_timing_block(
            tempo_total_s=time.time() - t_run, tempo_fit_surrogate_s=0.0,
            tempo_busca_s=sum(buf.timing_rows and
                              [r.get("tempo_busca_s", 0.0) or 0.0
                               for r in buf.timing_rows] or [0.0]),
            # [I-02] o valor MEDIDO pelo portão único (`budget.py`), não o
            # `0.0` literal: as 5 células deste config na s42 são as únicas do
            # estudo com `tempo_aval_real_s` = zero EXATO (0 zeros em 416
            # células alheias), e o valor real medido é 4,110 s-VM nas 5 —
            # 20,6% do wall, 57,15% no WFG9.
            tempo_aval_real_s=bud.tempo_aval_real_s, tempo_pred_sonda_s=0.0,
            tempo_checkpoint_s=ckpt.tempo_total_s)      # [BL-11]
        # [I-07/C2] `params` — a config EFETIVA no ⑤. O CONTRATO §5 lista
        # `params` entre as chaves obrigatórias do manifesto, e o sobol_batch era
        # o ÚNICO config Python que ainda não o gravava (medido nos smokes de
        # 2026-07-30: 9 de 10 gravam). O I-07 do plano nomeia só 5 configs, então
        # esta lacuna não tinha item — foi achado do smoke e reportado ao autor
        # antes de virar código (D81).
        # Os valores NÃO são literais soltos: saem das MESMAS fontes que a busca
        # usou (`q`, `D`, `maxfe` do budget), para que quem lê a tabela de
        # execuções não precise abrir o ⑥ para saber com que lote o run correu.
        params = {
            "alg": "sobol_batch",
            "motor": ("piso do BATCH — a cada iteração propõe q pontos por "
                      "sequência de Sobol SCRAMBLED (randomização de Owen), "
                      "SEM surrogate e SEM aquisição"),
            "q": int(q),
            "scramble": True,
            "scramble_tipo": "Owen (scipy.stats.qmc.Sobol scramble=True)",
            "gerador": "scipy.stats.qmc.Sobol",
            "semeadura": ("um `seed` por iteração, derivado da semente do run — "
                          "o lote i não repete o lote i-1"),
            "nota_potencia_de_2": ("q=10 não é potência de 2: usamos `random(q)`, "
                                   "e o scipy avisa que a propriedade de "
                                   "balanceamento do Sobol não vale para o lote"),
            "surrogate": "NENHUM (é o piso — a comparação existe para isolar o efeito do modelo)",
            "sigma": "NULL por construção (sem modelo, não há incerteza a reportar)",
            "D": int(D), "M": int(M), "maxfe": int(bud.maxfe),
            "regime": "online",
        }
        res = H.write_run_outputs(
            exp, alg, problema, semente, bud, buf, D=D, M=M, params=params,
            cp_hashes={"doe_hash": doe["doe_hash"]},
            env=env, pinning=pinning, n_geracoes=n_geracoes,
            algo_version=ALGO_VERSION, timing_totais=timing_totais,
            sigma_dict=sigma_dict, regime="online",
            status=status, motivo_parada=motivo_parada, q=q,
            # CONTRATO §6.1: piso online ⇒ bloco sonda `nao_se_aplica` (o auditar
            # exige esta marca explícita — a MESMA dos pisos MATLAB).
            sonda_info={"status": "nao_se_aplica", "S": 0, "n_blocos": 0,
                        "motivo": "piso online sem surrogate (sem régua §17.2.2)"},
            data_root=data_root, enable_bucket=enable_bucket)
        log.footer(status=status, fe_final=bud.fe, cp_init=True,
                   cache_hits=bud.cache_hits, n_geracoes=n_geracoes,
                   motivo_parada=motivo_parada, q=q)
    except Exception as exc:                          # noqa: BLE001 — D23/D60
        log.guard("erro_inesperado", detalhe=repr(exc))
        log.footer(status="failed", motivo=f"erro_{type(exc).__name__}",
                   fe_final=bud.fe, cp_init=None, cache_hits=bud.cache_hits)
        H.write_failed_manifest(
            exp, alg, problema, semente,
            motivo=f"erro_{type(exc).__name__}", regime="online",
            maxfe=bud.maxfe, fe_final=bud.fe, q=q,
            env=env, pinning=pinning, algo_version=ALGO_VERSION,
            detalhe=repr(exc), data_root=data_root,
            enable_bucket=enable_bucket)  # [B-09] evidência do aborto sobe
        raise
    finally:
        log.close()

    return {
        "fe_final": bud.fe, "maxfe": bud.maxfe, "n_geracoes": n_geracoes,
        "cp_init_ok": bool(res["cp_init_ok"]), "q": q,
        "cache_hits": bud.cache_hits, "status": status, "alg": alg,
        "n_surrogate_rows": len(buf.surr_rows),
    }
