# -*- coding: utf-8 -*-
"""[DI-35.2/T8] treed_media — o PISO-BIG do sweep (treed-GP-MÉDIA, env_c311).

**O que é (B15.4 / DI-16.5[P5] / D38 / DI-35.2):** a ABLAÇÃO CIRÚRGICA do c311
no tier `big` (50k). É "o c311 SEM os GPs": mesmo vendor, mesma árvore, mesmo
motor RVEA-final, mudando SÓ que o surrogate é a ÁRVORE PURA — `build_surrogates`
direto, SEM a construção iterativa `addGPs` (a folha-de-maior-impureza NUNCA ganha
um GP). A predição é a MÉDIA da árvore; sem GP local não há variância ⇒ σ NULL em
TODA a ③ (o precedente moead_media/DI-16.1 — "o b5 sem σ" — aqui "o c311 sem GPs").
O contraste sonda `c311` × `treed_media` isola o VALOR de σ: MESMA ESPECIFICAÇÃO
de árvore, treino INDEPENDENTE por config (DI-28), diferindo SÓ em o GP entrar
(c311) ou não (treed_media).

═══════════════════════════════════════════════════════════════════════════
POR QUE UM MÓDULO PRÓPRIO (e não o "ramo big" do c311)
═══════════════════════════════════════════════════════════════════════════
A torre RATIFICOU (DI-35.2, contra a leitura antiga do T7): rotear `tier=='big'`
para dentro do c311 transformaria o ÚNICO config do tier big na sua própria
ablação. O c311-big RODA a construção iterativa (âncoras SPEC :1904/:1520 —
"2500 iterações máx"); o treed_media é o PISO ao lado dele. Por isso o laço de
construção do c311 fica INTOCADO e o piso-big vive AQUI (`c311_tgprmo._build_surrogates`
docstring, "abertas à torre"). Ambos rodam no `env_c311` porque a `treeGP` mora no
vendor do c311; NUNCA co-importar com b5 (N.1.2/D79).

═══════════════════════════════════════════════════════════════════════════
O FLUXO (o c311 SEM a construção e SEM σ)
═══════════════════════════════════════════════════════════════════════════
OFFLINE puro (o dataset É o orçamento, D90): carrega `ds_{prob}_{sem}_big_{dist}.parquet`
(CP-init x_hash E f_hash) → `_build_surrogates` (a função do c311, IMPORTADA — fonte
única; treina 1 `treeGP` por objetivo, SÓ a árvore) → SONDA (1 bloco de 20.000, μ da
árvore, σ NULL, geracao=NULL) → RVEA final `10 × 100 = 1000` gerações sobre a árvore
FIXA (selection_type="mean", os defaults do RVEA — como a fase FINAL do c311) → ⑦ do
ND real pós-hoc (fora do orçamento, DI-08). Qualquer FE REAL na busca é
`OfflineBudgetViolation` (pára-e-loga D81).

O contador `geracao` é SIMPLES 1..1000: há UMA fase (não há a construção do c311, logo
não há o offset C311-11/DI-16.19). O RVEA final NUNCA chama `_refresh_population`
(`iterate()` só chama `_next_gen`), então enganchamos SÓ o `_next_gen`.

═══════════════════════════════════════════════════════════════════════════
CONTRATOS QUE ESTE RUNNER HONRA (e onde)
═══════════════════════════════════════════════════════════════════════════
- **σ NULL POR CONSTRUÇÃO** (DI-16.1): sem GPs, `error_leaves` fica None ⇒ o
  `_predict_batch` do c311 devolve σ TODO-NaN; a ③ grava `sigma=None` (busca E sonda).
  A seleção é por `mean` (`APD_Select` lê SÓ `pop.fitness`), então σ nunca move a busca.
- **② VAZIA por construção** (DI-16.17): a população do RVEA são candidatos gerados
  (LHS+SBX/PM) sobre o surrogate, nunca membros do dataset ⇒ `real_solution_id=NULL`;
  `buf.pop_rows` vazio.
- **1 bloco de sonda** (modelo ÚNICO, sem retreino — a diferença vs os 2 blocos do
  c311/DI-16.12): geracao=NULL (carimbada pós-hoc; `emit_sonda_block` força int),
  `predict_batch` vetoriza a predição por folha, custo FE=ZERO, sob `preserve_all_rng`.
- **④ = 1 LINHA** (treino único; molde piso/moead_media): sem a série multi-linha do
  c311 (não há retreino addGPs — este É o eixo de escalabilidade que a ablação remove).
  `tempo_geracao_s` EXCLUI a sonda (DI-13.10).
- **⑦ RECONSTITUÍVEL da ③**: nasce da última geração RVEA-final; TODOS os finais
  avaliados 1× na verdade; ND filtrado DEPOIS da real (DI-13.9/B7.5); `nd_pos_real`
  calculado pelo `write_final` sobre a vista float32 (não passar — DI-27/A15).
- **TETO UNIVERSAL** (DI-35.5, 43200s nos definitivos): rito do piso/b5 — ao estourar
  no RVEA final, aborto LIMPO (status=failed, motivo=teto_wall), curva parcial
  preservada; a ⑦ sai da última pop RVEA (válida — o teto só ocorre na fase final).
- **VENV-only / não-co-importar** (D79/N.1.2): env_c311; vendor do c311 root-first
  (`_import_vendor` importado). uso_id=_default/0 (mesmo s p/ numpy e random).

⚠ **Fidelidade NÃO é julgada aqui (D97)** — o runner instrumenta e aplica o gate;
o julgamento é manual, do autor. Ambiguidade ⇒ pára-e-pergunta (D81).
"""
from __future__ import annotations

# ── ORDEM (D79/N.1.1): o `standalone_harness` (e o `c311_tgprmo`) pinam as env
#    vars de thread ANTES de numpy, no import. Importá-los primeiro é o cinto. ──
from src import standalone_harness as H
from src.checkpoint import Checkpointer as _Checkpointer   # [DI-43]

import contextlib
import random
import time

import numpy as np

from src import export as _export
from src import naming

# ── FONTE ÚNICA: toda a maquinaria do treed-GP vem do c311 (vendor INTOCADO;
#    `_build_surrogates`/`_predict_batch`/`_patched_predict`/`_lhs_determinismo`
#    reusados à risca — DI-35.2 "IMPORTE-A de lá"). Importar o módulo é seguro
#    fora do env_c311: ele NÃO importa o vendor no load (só dentro de
#    `_import_vendor`), então este arquivo é importável no env-main (a suíte). ──
from src.c311_tgprmo import (
    _import_vendor,
    _build_surrogates,
    _predict_batch,
    _patched_predict,
    _lhs_determinismo,
    _silencio,
    _threads_pinned,
    _max_busca_geracao,
    VENDOR_ROOT,
)

# ── Identidade do config (Balde de parâmetros do cartão T8) ──────────────────

#: `artifacts/seeds.json:alg_id.treed_media` (D62/D91) — anti-descompasso.
ALG_ID = 23

#: uso_id=_default/0 (seeds.json:157): mesmo `s` p/ numpy e random (molde c311).
USO_ID = 0

ALGO_VERSION = ("treed-media-c311-ablacao-r3 (build_surrogates direto, SEM addGPs; "
                "RVEA final 10x100; sigma NULL DI-16.1; vendor c311 intocado)")

_ALG = "treed_media"

#: modelo_flag ÚNICO (fase única): identifica o config na ③/sonda/manifesto.
_MODELO_FLAG = "treed_media/RVEA-arvore-media"

#: §22.4·3.3 / §11 — a FASE FINAL do c311 à risca: RVEA n_iterations=10 ×
#: n_gen_per_iter default 100 = 1000 gerações. min_samples_leaf=10D / max_depth=100
#: vivem no `treeGP.fit`; α=2 e selection_type="mean" são os DEFAULTS do RVEA.
N_ITER_FINAL = 10


# ═══════════════════════════════════════════════════════════════════════════
#  Recorder — ③ por geração (σ NULL), contador SIMPLES 1..1000 (fase única)
# ═══════════════════════════════════════════════════════════════════════════

class _Recorder:
    """Captura a população selecionada por geração para a ③, com σ NULL (DI-16.1).

    Fase ÚNICA ⇒ `geracao = evolver._current_gen_count` (sem o offset das 2 fases
    do c311). Chamado pelo hook de `_next_gen` a cada geração do RVEA final; o
    RVEA final NUNCA chama `_refresh_population`, então o contador anda 1..1000.
    """

    def __init__(self, buf, *, fe_treino_max, modelo_flag):
        self.buf = buf
        self.fe_treino_max = int(fe_treino_max)
        self.modelo_flag = modelo_flag
        self.max_geracao = 0

    def capture(self, evolver):
        g = int(evolver._current_gen_count)
        self.max_geracao = max(self.max_geracao, g)
        pop = evolver.population
        Xg = np.asarray(pop.individuals, dtype=np.float64)
        MU = np.asarray(pop.objectives, dtype=np.float64)
        for i in range(Xg.shape[0]):
            # ② VAZIA por construção (DI-16.17): candidatos gerados ≠ dataset ⇒
            # real_solution_id=NULL. σ NULL (DI-16.1): árvore pura não tem σ.
            self.buf.add_surrogate(_export.surrogate_row(
                g, Xg[i], regime="offline", real_solution_id=None,
                mu=MU[i], sigma=None, pred_tipo="valor",
                modelo_flag=self.modelo_flag, espaco_modelo="cru",
                fe_treino_max=self.fe_treino_max))


@contextlib.contextmanager
def _hooks(treeGP, RVEA, BaseDecompositionEA, CreateIndividuals, recorder):
    """Instala SÓ o necessário à ablação treed-média e DESMONTA (vendor bit-a-bit).

    (1) `predict` → `_patched_predict` do c311 — μ é BYTE-idêntico ao stock (mesma
        `regr.predict`, mesmo laço); como NÃO há GPs (`error_leaves` é None), a
        rama-GP nunca roda e σ sai TODO NaN. Usado por ROBUSTEZ: garante
        `uncertainity=NaN` (nunca None) no `evaluate` do vendor (Problem.py:853
        faz `uncertainity[:,c] = results.uncertainity`). A incerteza NÃO é
        "exposta" — não existe; a ③ grava σ=NULL de qualquer forma.
    (2) `lhs` → gancho `_lhs_determinismo` do c311 (DEFINITIVO, DI-28.3): a pop
        inicial LHS do RVEA fica reprodutível da semente (o pyDOE do env_c311, sem
        pin, ignoraria `np.random.seed`).
    (3) `_next_gen` → `recorder.capture`: a ③-busca por geração. NÃO enganchamos
        `_refresh_population` (o RVEA final não o chama — fase única, contador simples).

    SEM `predict_batch` no `treeGP` (a sonda chama `_predict_batch(m, X)` direto).
    """
    orig_predict = treeGP.predict
    orig_next_gen = BaseDecompositionEA._next_gen
    orig_lhs, hooked_lhs = _lhs_determinismo(CreateIndividuals)

    def _hooked_next_gen(self, *a, **k):
        r = orig_next_gen(self, *a, **k)
        recorder.capture(self)
        return r

    treeGP.predict = _patched_predict
    BaseDecompositionEA._next_gen = _hooked_next_gen
    CreateIndividuals.lhs = hooked_lhs
    try:
        yield
    finally:
        treeGP.predict = orig_predict
        BaseDecompositionEA._next_gen = orig_next_gen
        CreateIndividuals.lhs = orig_lhs


# ═══════════════════════════════════════════════════════════════════════════
#  Sonda OFFLINE — 1 bloco (modelo único), μ da árvore, σ NULL (DI-16.1)
# ═══════════════════════════════════════════════════════════════════════════

def _sonda_predict_media(models):
    """`predict(X) -> (μ, None)` do treed-média inteiro (empilha os M objetivos).

    Vetoriza a predição por FOLHA (`_predict_batch` do c311 — molde DI-16.13). Como
    não há GPs, o σ que o `_predict_batch` devolve é TODO NaN e é DESCARTADO: o piso
    reporta SÓ a média (DI-16.1) ⇒ devolve σ=None ⇒ `emit_sonda_block` grava σ NULL.
    """
    def f(X):
        mus = []
        for m in models:
            mu, _sg = _predict_batch(m, X)     # σ = all-NaN (sem GP) — descartado
            mus.append(mu)
        return np.column_stack(mus), None      # σ NULL (DI-16.1)
    return f


def _null_sonda_geracao(buf, S):
    """geracao=NULL nas S linhas de sonda RECÉM-emitidas (DI-13.5).

    O `emit_sonda_block` força `int(geracao)` e não aceita None; o runner completa
    as linhas do SEU buffer (precedente piso `_null_sonda_geracao` / c149
    `_stamp_c3_sonda` — mesma mutação de `buf.surr_rows[-S:]`). A ORDEM fica intacta.
    """
    for row in buf.surr_rows[-int(S):]:
        assert row.get("regime") == "sonda", "bloco de sonda esperado"
        row["geracao"] = None


# ═══════════════════════════════════════════════════════════════════════════
#  sigma_dict (DEF-C4) — o dicionário que torna a ③ auditável
# ═══════════════════════════════════════════════════════════════════════════

def _sigma_dict(n_ds):
    """Declara TODAS as exceções do offline (② vazia, σ NULL, ④ 1-linha, sonda,
    teto) + a diferença ÂNCORA vs o c311 (os GPs). Testável em unidade (molde piso)."""
    return {
        "modelo": ("treed-GP-MÉDIA = a ABLAÇÃO do c311 SEM os GPs: árvore de "
                   "regressão MSE (min_samples_leaf=10D, max_depth=100) por objetivo, "
                   "treino ÚNICO no dataset big (50k); predição = μ da árvore. SEM os "
                   "GPs locais do c311 (nenhum `addGPs`; `error_leaves` fica None). "
                   "MESMA ESPECIFICAÇÃO de árvore do c311, treino INDEPENDENTE por "
                   "config [DI-28: 'mesma ESPECIFICAÇÃO, treino INDEPENDENTE' — nunca "
                   "'idêntico'; alg_id 23 vs 19 semeia RNGs distintos]."),
        "motor": ("RVEA final 10x100 = 1000 gerações sobre o surrogate FIXO (árvore "
                  "pura), selection_type='mean' (α=2 — os DEFAULTS do RVEA, a fase "
                  "FINAL do c311 à risca). SEM a construção iterativa `addGPs` do c311 "
                  "(B15.4/DI-35.2: `build_surrogates` direto). Contador `geracao` "
                  "SIMPLES 1..1000 (fase única; o RVEA final não chama "
                  "`_refresh_population`)."),
        "mu_*": ("μ por objetivo = predição da árvore em f de MINIMIZAÇÃO, espaço "
                 "NATIVO (treed treina em Y cru — sem normalizer/z-score)."),
        "sigma_*": ("NULL POR CONSTRUÇÃO (DI-16.1): o treed-média é 'o c311 SEM os "
                    "GPs' — sem GP local não há variância; o motor seleciona SÓ pela "
                    "média, a incerteza NÃO é reportada (nem na busca nem na sonda). O "
                    "contraste sonda c311 × treed_media isola o VALOR de σ: MESMA "
                    "ESPECIFICAÇÃO de árvore e os MESMOS 20.000 pontos, diferindo SÓ em "
                    "o GP entrar (c311) ou não (treed_media). ⚠ NÃO é 'a mesma árvore "
                    "byte-a-byte': o treino é INDEPENDENTE por config (DI-28). Excluir σ "
                    "AQUI é o que torna o contraste atribuível só a σ."),
        "regime": ("offline = candidatos da busca RVEA sobre o surrogate; sonda = a "
                   "régua fixa §17.2.2."),
        "modelo_flag": ("valor ÚNICO '%s' (fase única: não há a distinção "
                        "build/final do c311)." % _MODELO_FLAG),
        "espaco_modelo": "cru (nativo); transf_tipo/params = NULL (sem transformação).",
        "fe_treino_max": ("constante %d (=n_dataset-1) em TODA linha (busca+sonda) — o "
                          "dataset É o orçamento (D90); o modelo vê as %d linhas 1×; "
                          "offline não retreina." % (n_ds - 1, n_ds)),
        "pop_inicial_②": ("VAZIA POR CONSTRUÇÃO (DI-16.17): a pop inicial do RVEA é LHS "
                          "novo (CreateIndividuals/LHSDesign) + SBX/PM contínuos ⇒ "
                          "nenhum indivíduo coincide com o dataset; real_solution_id=NULL "
                          "em TODA linha de busca; n_ds_membros=0. O gate NÃO exige ② "
                          "não-vazia."),
        "sonda_offline": ("1 bloco de 20.000 (§17.2.2), modelo ÚNICO (sem retreino — "
                          "por isso 1 bloco, não os 2 do c311/DI-16.12), geracao=NULL "
                          "(DI-13.5 — carimbada pós-hoc; `emit_sonda_block` faz "
                          "int(geracao)), μ da árvore preenchido / σ NULL. `predict_batch` "
                          "vetoriza a predição por folha. Custo FE=ZERO; RNG "
                          "salvo/restaurado (não-perturbação §3.1)."),
        "④_1_linha": ("④ = 1 LINHA (treino único; molde piso/moead_media): "
                      "n_acumulado=n_dataset, tempo_fit_s=wall do `build_surrogates` (a "
                      "árvore), tempo_busca_s=wall do RVEA final, tempo_geracao_s EXCLUI "
                      "a sonda (DI-13.10). SEM a série fit_series MULTI-linha do c311 — "
                      "a ablação REMOVE o eixo de escalabilidade (o retreino addGPs)."),
        "modelo_hp": ("NULL no offline — HP fixos (min_samples_leaf=10D, max_depth=100), "
                      "treino único [D-08]."),
        "teto": ("teto_s UNIVERSAL (DI-35.5, 43200s=12h nos definitivos) — rito do "
                 "piso/b5: ao estourar durante o RVEA final, ABORTO LIMPO (status=failed, "
                 "motivo=teto_wall), curva parcial preservada; a ⑦ sai da última pop RVEA "
                 "(válida — o teto só pode ocorrer na fase FINAL, onde a população é "
                 "sempre válida). [Aberto à torre: o c311 OMITE a ⑦ no teto durante a "
                 "construção; aqui não há construção. Ver handoff.]"),
        "vendor": ("vendor c311 INTOCADO (root-first, a MESMA cópia do c311: "
                   "DataProblem/treeGP/RVEA de algorithms/c311_TGPR-MO). "
                   "`_build_surrogates`/`_predict_batch`/`_patched_predict`/"
                   "`_lhs_determinismo` IMPORTADOS de src.c311_tgprmo (fonte única). "
                   "NUNCA co-importar com b5 (N.1.2/D79)."),
        "LHS_determinismo": ("o pyDOE do env_c311 (sem pin) mudou a API: lhs(...) SEM "
                             "seed usa RandomState próprio (ignora np.random.seed) ⇒ pop "
                             "inicial NÃO-reprodutível. O runner injeta seed derivado do "
                             "np.random global semeado (gancho `_lhs_determinismo` do "
                             "c311, DEFINITIVO DI-28.3) ⇒ LHS determinístico E fiado à "
                             "semente."),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Despacho (o `experiment.run` chama com `(exp, alg, problema, semente, **kw)`)
# ═══════════════════════════════════════════════════════════════════════════

def run_treed_media(exp: str, alg: str, problema: str, semente, *,
                    data_root: str = naming.DEFAULT_DATA_ROOT,
                    enable_bucket: bool = False,
                    teto_s: float | None = None,
                    q: int = 1,
                    emitir_sonda: bool = True,
                    **_kwargs) -> dict:
    """Roda o treed-média (piso-big) OFFLINE sob o contrato v5.2.1. O `alg` do
    despacho é sempre `treed_media`; 1 sessão = 1 cartão (guarda como o piso).

    `teto_s` = teto de wall-clock (rito do piso/b5, DI-35.5); None = sem teto.
    `emitir_sonda=False` DESLIGA o bloco de sonda — usado SÓ pela prova de
    não-perturbação (§3.1): a ⑦ e a ③-busca saem BIT-idênticas com a sonda
    ligada ou desligada (a sonda roda FORA da busca, sob `preserve_all_rng`).
    """
    if alg != _ALG:
        raise ValueError(
            "run_treed_media só cobre %r (recebeu %r) — 1 sessão = 1 cartão."
            % (_ALG, alg))

    t_run = time.time()
    pinning = H.pin_runtime()
    env = H.env_info()
    semente = int(semente)

    (DataProblem, treeGP, RVEA, BaseDecompositionEA,
     CreateIndividuals) = _import_vendor()

    # ── [T7-sweep] a CÉLULA do grid sai do token exp (`sweep-big-<dist>`) ────
    #    `tier/dist` = o par literal (manifesto/log); `t_ds/d_ds` = a VARIANTE de
    #    arquivo. O treed_media roda SÓ em `big` (D38/DI-16.5) — `dataset_variant`
    #    devolve ('big', dist) (o big nunca é o principal).
    tier, dist = naming.parse_sweep(exp)
    t_ds, d_ds = naming.dataset_variant(exp)

    # ── ① = o DATASET big 50k (D90): o orçamento nasce ESGOTADO; CP x_hash E f_hash
    bud, ds = H.load_offline_budget(problema, semente, tier=t_ds, dist=d_ds,
                                    data_root=data_root)
    D, M, n_ds = ds["D"], ds["M"], ds["n"]
    x_low, x_high = (np.asarray(b, dtype=np.float64) for b in H._bounds(problema))
    fe_treino_max = n_ds - 1                        # DI-09/A1: constante no offline

    sonda = H.load_sonda(problema, regime="offline", data_root=data_root)
    buf = H.SnapshotBuffer()
    buf.set_fe_treino_max(fe_treino_max)
    log = H.AuditLogger.for_run(exp, alg, problema, semente,
                                data_root=data_root, append=False)
    # [DI-43] checkpoint atômico periódico — 25 iterações OU 30 min. O hook
    # do `_next_gen` (linhas 174-183) alimenta o buffer a cada geração, então
    # aqui há dado parcial de verdade para gravar (ao contrário do b5/piso-off,
    # cujo ③ só nasce no replay pós-laço).
    ckpt = _Checkpointer(exp, _ALG, problema, semente, D=D, M=M,
                         regime="offline", tier=tier, dist=dist,
                         data_root=data_root, log=log)

    params = {
        "receita": ("build_surrogates(X,F,x_low,x_high) [SÓ árvore, sem addGPs] + "
                    "RVEA(n_iterations=10) final sobre a árvore pura"),
        "min_samples_leaf": 10 * D, "max_depth": 100,
        "n_iter_final": N_ITER_FINAL, "n_gen_final": 100, "n_gen_total_final": 1000,
        "selection_type": "mean", "alpha": 2,
        "surrogate": "treed-GP-média (árvore de regressão MSE, SEM GP local)",
        "sigma": "NULL por construção (sem GP ⇒ sem variância; DI-16.1)",
        "ablacao_de": "c311 (TGPR-MO) — remove a construção iterativa addGPs (B15.4)",
    }
    sigma_dict = _sigma_dict(n_ds)

    status, motivo_parada = "ok", "orcamento"       # [DI-35.5] teto pode mudar
    pop_final = None
    n_nd = 0
    final_gen_last = 0
    t_fit = t_busca_total = t_snd = 0.0

    try:
        log.header(alg=alg, versao=ALGO_VERSION, problema=problema, D=D, M=M,
                   semente=semente, regime="offline", maxfe=bud.maxfe,
                   n_dataset=n_ds, doe_hash=ds["x_hash"], f_hash=ds["f_hash"],
                   dataset_hash=ds.get("dataset_hash"),
                   ambiente=env, pinning=pinning, sigma_dict=sigma_dict,
                   sonda_x_hash=sonda["x_hash"], sonda_S=sonda["S"], params=params,
                   emitir_sonda=bool(emitir_sonda),
                   tier=tier, dist=dist,              # [T7] a célula do grid
                   dataset_path=ds.get("path"))       # o arquivo REALMENTE lido

        # ── RNG global (L.17): numpy (pyDOE/SBX/PM/sklearn-tree) + stdlib. uso_id=0
        #    (default seeds.json): mesmo `s` p/ np.random e random (molde c311). ──
        s = H.iteration_seed(H.seed_base(alg, semente), ALG_ID, 0, USO_ID,
                             bits32=True)
        np.random.seed(s)
        random.seed(s)

        recorder = _Recorder(buf, fe_treino_max=fe_treino_max,
                             modelo_flag=_MODELO_FLAG)

        with _threads_pinned(), \
                _hooks(treeGP, RVEA, BaseDecompositionEA, CreateIndividuals,
                       recorder), \
                H.offline_guard(log, alg=alg, problema=problema):
            # ══ TREINO ÚNICO — build_surrogates DIRETO (só a árvore, sem addGPs) ══
            t0 = time.time()
            with _silencio():
                problem = _build_surrogates(DataProblem, treeGP,
                                            ds["X"], ds["F"], x_low, x_high)
            t_fit = time.time() - t0
            models = [problem.objectives[i]._model for i in range(M)]
            # ④ = 1 linha (treino único); abre AGORA (retém o fit sob hard-stop, D61)
            buf.add_timing(geracao=1, n_acumulado=n_ds, tempo_fit_s=t_fit)

            # ── SONDA: 1 bloco (S=20.000), FORA do laço (tempo_geracao_s exclui a
            #    sonda). geracao=1 na emissão → NULL pós-hoc. σ NULL (DI-16.1). ──
            spred = _sonda_predict_media(models)
            if emitir_sonda:
                t_snd = H.emit_sonda_block(
                    buf, log, geracao=1, fe=bud.fe, sonda=sonda, predict=spred,
                    fe_treino_max=fe_treino_max, modelo_flag=_MODELO_FLAG,
                    pred_tipo="valor",
                    motivo="offline: 1 bloco (modelo unico, sem retreino)",
                    c3={"espaco_modelo": "cru"})
                _null_sonda_geracao(buf, sonda["S"])

            # ══ RVEA FINAL — 10x100=1000 gerações sobre a árvore FIXA ════════════
            with _silencio():
                evf = RVEA(problem, use_surrogates=True, n_iterations=N_ITER_FINAL)
            t_f0 = time.time()
            with _silencio():
                while evf.continue_evolution():
                    # [DI-35.5] TETO UNIVERSAL — mesmo rito do piso/b5.
                    if teto_s is not None and (time.time() - t_run) > teto_s:
                        status, motivo_parada = "failed", "teto_wall"
                        log.guard("teto_wall", fe=bud.fe,
                                  decorrido_s=round(time.time() - t_run, 1),
                                  teto_s=teto_s,
                                  acao=("ABORTO LIMPO — curva parcial preservada; "
                                        "manifesto failed (D-07). A ⑦ sai da última "
                                        "pop RVEA (fase final, pop válida)."))
                        break
                    evf.iterate()                   # 100 gerações (hook captura cada)
                    H.iteration_cleanup()
                    ckpt.talvez_gravar(bud, buf,
                                       iteracao=int(evf._current_gen_count))
            t_busca_total = time.time() - t_f0
            final_gen_last = int(evf._current_gen_count)
            pop_final = np.ascontiguousarray(
                evf.population.individuals, dtype=np.float64)

        # ── ⑦ __final: TODOS os finais avaliados 1× na verdade; ND filtrado DEPOIS.
        #    Emitida MESMO na parada por teto (rito do piso: curva parcial). ──────
        from src import problems as _problems
        F_final = np.ascontiguousarray(
            _problems.evaluate_problem(H._instantiate(problema), pop_final),
            dtype=np.float64)
        n_fin = int(pop_final.shape[0])
        # [DI-27/A15] `nd_pos_real`: NÃO passar — o `write_final` o calcula sobre a
        # vista FLOAT32 que a ⑦ PERSISTE (a mesma do `final_eval --check`). Molde
        # b5/c311: no float64 cru cria assimetria em empates de borda.
        H.write_final(
            exp, alg, problema, semente, pop_final, F_final,
            origem_solution_id=[None] * n_fin,       # ② vazia ⇒ sem vínculo c/ dataset
            origem_geracao=[final_gen_last] * n_fin,
            origem_linha=np.arange(n_fin),
            origem_camada="surrogate (③), ultima geracao treed_media (RVEA final)",
            data_root=data_root)
        nd_idx = set(int(i) for i in _problems._nds_filter(
            F_final.astype(np.float32).astype(np.float64)))
        n_nd = len(nd_idx)

        # ── ④ = 1 LINHA: completa fit + busca (EXCLUINDO a sonda, DI-13.10) ─────
        buf.update_timing(1, tempo_busca_s=t_busca_total,
                          tempo_pred_sonda_s=t_snd,
                          tempo_geracao_s=t_fit + t_busca_total)

    except H.OfflineBudgetViolation:
        # uma avaliação REAL na busca é desenho ERRADO (D81): o offline_guard já
        # gravou guard+footer(failed) e re-levantou. Não persistimos as camadas de
        # um run inválido — pára-e-loga HARD (molde c311).
        log.close()
        raise
    except Exception as exc:                          # noqa: BLE001 — D23/D60/D81
        # Qualquer outra falha: NUNCA silenciosa. Manifesto HONESTO (failed) +
        # re-levanta (molde piso/b5: `write_failed_manifest`).
        status, motivo_parada = "failed", f"erro_{type(exc).__name__}"
        log.guard("erro_inesperado", detalhe=repr(exc))
        log.footer(status="failed", motivo=motivo_parada, fe_final=bud.fe,
                   cp_init=None, cache_hits=bud.cache_hits)
        H.write_failed_manifest(
            exp, _ALG, problema, semente,
            motivo=motivo_parada, regime="offline",
            maxfe=bud.maxfe, fe_final=bud.fe, tier=tier, dist=dist,
            env=env, pinning=pinning, algo_version=ALGO_VERSION,
            detalhe=repr(exc), data_root=data_root,
            enable_bucket=enable_bucket)  # [B-09] evidência do aborto sobe
        log.close()
        raise

    # ── fechamento (sucesso OU parada por teto — o rito do piso escreve tudo) ───
    n_geracoes = _max_busca_geracao(buf)              # topo do contador (=1000 no ok)

    timing_totais = _export.manifest_timing_block(
        tempo_total_s=time.time() - t_run, tempo_fit_surrogate_s=t_fit,
        # [I-02] NULL, não 0.0: no OFFLINE o orçamento nasce ESGOTADO (a ①
        # é o dataset, D90) e nenhuma avaliação real acontece DENTRO do run —
        # gravar zero afirmaria "avaliar custou zero". `bud.tempo_aval_real_s`
        # devolve None quando nenhuma avaliação passou pelo portão.
        tempo_busca_s=t_busca_total,
        tempo_aval_real_s=bud.tempo_aval_real_s,
        tempo_pred_sonda_s=t_snd)

    res = H.write_run_outputs(
        exp, alg, problema, semente, bud, buf, D=D, M=M,
        cp_hashes={"x_hash": ds["x_hash"], "f_hash": ds["f_hash"]},
        env=env, pinning=pinning, n_geracoes=n_geracoes,
        algo_version=ALGO_VERSION, timing_totais=timing_totais,
        sigma_dict=sigma_dict, regime="offline", params=params,
        sonda_info=({"S": sonda["S"], "cadencia": "offline: 1 bloco (modelo unico)",
                     "n_blocos": (1 if emitir_sonda else 0),
                     "modelo_flags": [_MODELO_FLAG],
                     "x_hash": sonda["x_hash"], "f_hash": sonda["f_hash"]}
                    if emitir_sonda else
                    {"S": sonda["S"], "cadencia": "DESLIGADA (prova nao-perturbacao)",
                     "n_blocos": 0}),
        status=status, motivo_parada=motivo_parada, q=int(q),
        tier=tier, dist=dist,
        data_root=data_root, enable_bucket=enable_bucket)

    log.footer(status=status, motivo=motivo_parada, fe_final=bud.fe, cp_init=True,
               cache_hits=bud.cache_hits, n_geracoes=n_geracoes,
               n_final=(0 if pop_final is None else int(pop_final.shape[0])),
               n_nd_pos_real=n_nd)
    log.close()

    return {
        "status": status, "motivo_parada": motivo_parada,
        "fe_final": bud.fe, "maxfe": bud.maxfe, "n_dataset": n_ds,
        "cp_init_ok": bool(res["cp_init_ok"]), "n_geracoes": n_geracoes,
        "n_surrogate_rows": len(buf.surr_rows), "n_pop_rows": len(buf.pop_rows),
        "n_timing_rows": len(buf.timing_rows),
        "n_sonda_blocos": (1 if emitir_sonda else 0),
        "n_final": (0 if pop_final is None else int(pop_final.shape[0])),
        "n_nd_pos_real": n_nd, "regime": "offline", "cache_hits": bud.cache_hits,
        "tempo_pred_sonda_s": t_snd, "emitir_sonda": bool(emitir_sonda),
        "alg": _ALG,
    }
