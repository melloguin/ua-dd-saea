"""Camada de métrica pós-hoc (§12–§13 · D69/D70/D92) — ESQUELETO (casca).

Lê a camada ① (avaliações reais do export §17.2), NORMALIZA os objetivos por
`(ideal, nadir)` do front verdadeiro (D69 / tabela S.5) e calcula:

    IGD · **IGD+ (endpoint PRIMÁRIO — D70)** · HV · GD · spacing

sobre o conjunto não-dominado, mais a **trajetória** dessas métricas ao longo
das avaliações reais (§13, só faz sentido no online). Módulo único, agnóstico a
stack, que roda DEPOIS da bateria (pós-hoc).

**Convenções fixadas (§12.2):**
- Métricas sobre objetivos NORMALIZADOS `f′ = (f − ideal)/(nadir − ideal)`
  (D69). `ideal = f_min`, `nadir = f_max` (o nadir CRU do front — tabela S.5,
  **sem** a margem de 10%). A margem entra pelo ref-point, não na normalização.
- Ref-point do HV = **1,1 em cada coordenada** do espaço normalizado (D69/D92) —
  equivale a `nadir + 0,1·(nadir − ideal)` no espaço cru (Ishibuchi 2018).
- Reference set do IGD/IGD+/GD amostrado do `true_pareto_front` (`|R|≈5000`,
  §12.2). Para os **BBOB** o front é EMPÍRICO (cache `data/bbob_pf_cache/`,
  §12.1) → IGD é relativo (apoiar a leitura no HV; nuance registrada no R4).

**⚠ ESQUELETO (cartão F0-04).** Aqui vivem as funções-núcleo + a **âncora do
smoke** (`hv_smoke_bbob_f1()` = **1,0433** — D92) que FECHA a Fase 0. A ANÁLISE
COMPLETA — agregação das 30 sementes (mediana+IQR, §13), os 4 testes
estatísticos (§14), a análise por característica (§15), IGDX/attainment/GHV, o
re-espaçamento fino do reference set (arc-length 2-obj / Das-Dennis 3-obj) — é da
camada de análise, **refinada/implementada pelo AUTOR no R4 (D100)**.

Não julga fidelidade (D97): mede, não decide. Requer numpy + pymoo (env-main); o
leitor da ① usa pyarrow. `import src.metrics` sozinho só exige numpy (pymoo/
pyarrow são LAZY, como em `src/export.py`).
"""

from __future__ import annotations

import numpy as np

from src import naming

# ── Constantes de decisão (§12/D69/D70/D92/S.5) ─────────────────────────────

#: Endpoint primário do estudo (D70) — as demais são secundárias/apoio.
PRIMARY_METRIC = "igd_plus"

#: Ref-point do HV: 1,1 em CADA coordenada no espaço normalizado (D69/D92).
HV_REF_COORD = 1.1

#: HV analítico de aceitação do smoke — BBOB F1, front `f2′=(1−√f1′)²`, ref 1,1
#: por coordenada: 1,21 − ∫₀¹(1−√x)²dx = 1,21 − 1/6 = 1,0433… (D92).
HV_SMOKE_BBOB_F1 = 1.0433

#: HV do MESMO front com ref no nadir (1,0): 1 − 1/6 = 0,8333… — SANITY do FRONT
#: (valida a geometria do front analítico), **NÃO** a métrica oficial (D92/§12.2).
HV_SANITY_BBOB_F1 = 0.8333

#: Tamanho-alvo do reference set do IGD/IGD+/GD (§12.2; M ≤ 3).
REF_SET_SIZE = 5000

#: Guarda numérica do denominador da normalização (range ≥ 1e-12 — S.5).
_RANGE_FLOOR = 1e-12


# ── Tabela S.5 — `f_min/f_max` CRUS por problema (ideal, nadir do front) ─────
#  Computados dos fronts verdadeiros de `problems.py` (BBOB do cache i1). O
#  `f_max` aqui é o **nadir CRU** (a margem de 10% NÃO está embutida — ela entra
#  via ref=1,1). Chaves = short names de `experiment.PROBLEM_CLASSES`.
#  Fonte congelada: 00_fundacao/05_problemas.md · S.5.
F_MIN_MAX: dict[str, tuple[tuple[float, ...], tuple[float, ...]] | None] = {
    "MMF1":     ((0.0005, 0.0),          (1.0, 0.9776)),
    "MMF4":     ((0.001, 0.0),           (1.0, 1.0)),
    "MMF11_L":  ((0.1, 0.9523),          (1.1, 10.4757)),
    "MMF16_20": ((0.0, 0.0, 0.0),        (2.0, 2.0, 2.0)),
    "ZDT1":     ((0.0, 0.0),             (1.0, 1.0)),
    "ZDT3":     ((0.0, -0.7734),         (0.8519, 1.0)),
    "ZDT4":     ((0.0, 0.0),             (1.0, 1.0)),
    "ZDT6":     ((0.2809, 0.0),          (1.0, 0.9211)),
    "DTLZ1":    ((0.0, 0.0, 0.0),        (0.5, 0.5, 0.5)),
    "DTLZ2":    ((0.0, 0.0, 0.0),        (1.0, 1.0, 1.0)),
    "DTLZ3":    ((0.0, 0.0, 0.0),        (1.0, 1.0, 1.0)),
    "DTLZ4":    ((0.0, 0.0, 0.0),        (1.0, 1.0, 1.0)),
    "DTLZ7":    ((0.0, 0.0, 2.614),      (0.8599, 0.8599, 6.0)),
    "WFG1":     ((0.0, 0.0),             (2.0, 4.0)),
    "WFG2":     ((0.0, 0.0),             (2.0, 4.0)),
    "WFG4":     ((0.0014, 0.0),          (2.0, 4.0)),
    "WFG5":     ((0.1569, 0.0032),       (2.0, 3.9877)),
    "WFG9":     ((0.0, 0.0),             (2.0, 4.0)),
    "BBOB_F1":  ((0.0, 0.0),             (82.042, 82.042)),
    "BBOB_F5":  ((0.0156, 33.9822),      (87.3013, 1495.7185)),
    "BBOB_F17": ((0.7912, 0.3073),       (5.6972e07, 107.9268)),
    "BBOB_F22": ((2.5729, 22.0423),      (92863.619, 1215.6824)),
    "BBOB_F37": ((17.8485, 23.3374),     (1724.6925, 390.3391)),
    "BBOB_F49": ((25.3176, 0.0123),      (1243.2907, 84.7479)),
    "BBOB_F55": ((0.0002, 0.1473),       (75.1174, 63.0222)),
    # [D101] Problemas de DADOS REAIS — réguas MEDIDAS dos fronts D72
    # (fonte congelada: S5_ideal_nadir.json do pacote de fusão do Agente 8).
    "RE21":      ((1237.8414665029802, 0.002761428901174483),
                  (2886.3687781863305, 0.03999999758374547)),
    # [REAL-2.15 ERRATA 2 · autor 2026-08-15] DDMOP7: o `ideal` da fase 1 passa
    # a ser o ÍNFIMO TEÓRICO `[0/17 ; 0/690]`, não mais a estimativa sobre os
    # 62 pontos do probe v6 (`[4/17 ; 202/690]`, opção A de 2026-08-13).
    #
    # POR QUÊ (laudo de fidelidade 15/08, com a zona morta D102.17 no ar): a
    # estimativa FUROU. Medido nos 15 smokes (7.156 pontos): **3.203 pontos
    # (44,8%) melhores que o ideal estimado**, chegando a `z = [−0,231;
    # −0,421]`. E o furo NÃO era só de análise: `c122_thetadeadp.py:137`
    # normaliza o PBI por esta régua DURANTE a busca (209/425 = 49,2% dos
    # pontos dele abaixo do ideal) e `c262_qnehvi.py:208` deriva daqui o
    # ref-point da aquisição (221/398 = 55,5%). A fase 2 (pós-hoc) não podia
    # corrigir isso — os dois precisam de régua EM TEMPO DE EXECUÇÃO.
    #
    # POR QUE O ÍNFIMO TEÓRICO: os objetivos do DDMOP7 são contagens
    # normalizadas — `f1 = k/17` com k ≥ 0 (pesos não-nulos) e `f2 = n/690`
    # com n ≥ 0 (erros de classificação), medido em 15/15 células a 100%.
    # Logo `[0;0]` é o ínfimo POR CONSTRUÇÃO, não por medição: nenhuma semente
    # futura pode furá-lo. Verificado: **0 furos em 7.156 pontos**. É a única
    # escolha que não introduz parâmetro arbitrário (D81 — não inventar valor)
    # e não repete o modo de falha da estimativa. Precedente próximo: a
    # D102.20 estendeu a régua do ESTOQUE40 pelos CANTOS da caixa (objetos
    # determinísticos); aqui não há canto conhecido, então sobe-se ao ínfimo.
    # Custo: HV menor em valor absoluto, IGUALMENTE comparável entre configs.
    #
    # O `nadir` fica como estava (468/690 — errata 1, de 2026-08-13). A FASE 2
    # segue OBRIGATÓRIA (REGUAS_PROVISORIAS abaixo): z*/z_nad pooled sobre as
    # runs reais substituem isto e a §12 re-roda (D102.3). O guard executável
    # `checa_regua` (T15.13) faz o cálculo FALHAR se esta régua for furada.
    "DDMOP7":    ((0.0, 0.0),
                  (1.0, 0.678260869565217)),
    # [T15.12 · C3-01 do laudo de fidelidade 15/08] Régua ESTENDIDA pelos DOIS
    # CANTOS da caixa, que sao membros EXTREMOS do front verdadeiro e furavam
    # a regua anterior nos 3 objetivos (f1 por 424,515 = 2,37%; f2 por
    # 183,961; f3 por 2,171e-04): x=xl=0 ("nao compra nada") da f=[0,0,0] e
    # x=xu da o melhor f1 alcancavel. MEDIDO em 15/08 via problems.py:
    # f(xl)=[-0,0,0] · f(xu)=[-17909.135471698115, 7492.938905660378,
    # 3.199116]. Sem isto, com 30 sementes x 21 configs, um reparo-aos-bounds
    # tocaria um canto e o HV normalizado passaria de 1.
    "ESTOQUE40": ((-17909.135471698115, 0.0, 0.0),
                  (0.0, 7492.938905660378,
                   4.2561157380901555)),
}

#: [D102.4/TD-08] Problemas SEM front de referência D72 — o consumidor de
#: `true_pareto_front`/`true_front_raw` DEVE pular estes (só HV; sem IGD+/GD).
#: No DDMOP7 a classe levanta NotImplementedError por para-raios (uma chamada
#: distraída custaria 21,76 dias-core no `.p`); este conjunto é o mecanismo de
#: skip para quem itera problemas. Precedente de métrica por subconjunto: o
#: IGDX pós-hoc dos 4 MMF (D99) — "as 2 vias" (decisão do autor, M1b).
PROBLEMAS_SEM_FRONT_D72: frozenset = frozenset({"DDMOP7"})

#: [D102.3/TD-13] SELO de régua PROVISÓRIA — substituição OBRIGATÓRIA na fase
#: 2 (pós-hoc, pooled sobre as runs reais; re-roda a §12). Qualquer análise
#: que leia F_MIN_MAX de um problema listado aqui está usando número
#: PROVISÓRIO e deve declará-lo. O selo só sai quando a fase 2 gravar os
#: definitivos — auditoria que veja esta constante não-vazia sabe que há
#: pendência. Espelho do `provisorio: true` do S5_ideal_nadir.json.
REGUAS_PROVISORIAS: dict[str, str] = {
    "DDMOP7": "fase 1 = 62 pontos do probe v6 (REAL-2.15, opção A); "
              "fase 2 pós-hoc obrigatória (D102.3)",
}


# ── Bounds + normalização (D69/S.5) ─────────────────────────────────────────

def reference_bounds(problema: str) -> tuple[np.ndarray, np.ndarray]:
    """`(ideal, nadir)` do front verdadeiro (tabela S.5 congelada) — D69.

    Base de normalização FIXA por problema, idêntica para todos os algoritmos
    (§12) e para todas as VMs. `nadir` é o nadir CRU (a margem de 10% do HV mora
    no ref=1,1, não aqui)."""
    if problema not in F_MIN_MAX:
        raise KeyError(f"problema sem f_min/f_max na S.5: {problema!r} "
                       f"(conhecidos: {sorted(F_MIN_MAX)})")
    if F_MIN_MAX[problema] is None:
        # [D102.3/TD-13] selo provisório: régua ainda não cravada — erro
        # DESENHADO no lugar do KeyError tardio. NUNCA preencha com um número
        # improvisado: régua é fidelidade (D81).
        raise RuntimeError(
            f"régua S.5 de {problema!r} está PROVISÓRIA (selo D102.3): a "
            f"fase 1 aguarda a decisão REAL-2.15 do autor e a fase 2 é "
            f"pós-hoc sobre as runs. Pára-e-loga (D81) — não invente valor.")
    ideal, nadir = F_MIN_MAX[problema]
    return np.asarray(ideal, dtype=np.float64), np.asarray(nadir, dtype=np.float64)


def normalize(F, ideal, nadir) -> np.ndarray:
    """`f′ = (f − ideal)/(nadir − ideal)` (D69), com guarda `range ≥ 1e-12` (S.5).

    Aplica-se IGUAL ao conjunto-aproximação e ao reference set (é o que torna as
    células comparáveis dentro do problema)."""
    F = np.atleast_2d(np.asarray(F, dtype=np.float64))
    ideal = np.asarray(ideal, dtype=np.float64)
    nadir = np.asarray(nadir, dtype=np.float64)
    rng = np.maximum(nadir - ideal, _RANGE_FLOOR)
    return (F - ideal) / rng


def nondominated_front(F) -> np.ndarray:
    """Sub-conjunto não-dominado de `F` (minimização) — ENS do pymoo moderno,
    o MESMO usado em `problems.py` (consistência A2)."""
    F = np.atleast_2d(np.asarray(F, dtype=np.float64))
    if F.shape[0] == 0:
        return F
    from src.problems import _nds_filter  # lazy (pymoo)
    return F[_nds_filter(F)]


# ── Métricas (todas sobre objetivos JÁ NORMALIZADOS) ────────────────────────
#  IGD/IGD+/GD via pymoo (lib pinada — D80); spacing próprio (numpy).

def _pymoo_indicators():
    from pymoo.indicators.igd import IGD
    from pymoo.indicators.igd_plus import IGDPlus
    from pymoo.indicators.gd import GD
    from pymoo.indicators.hv import HV
    return IGD, IGDPlus, GD, HV


def igd(approx_norm, ref_norm) -> float:
    """IGD (Inverted Generational Distance) do conjunto-aproximação ao ref set."""
    IGD, _, _, _ = _pymoo_indicators()
    A = np.atleast_2d(np.asarray(approx_norm, dtype=np.float64))
    if A.shape[0] == 0:
        return float("nan")
    return float(IGD(np.asarray(ref_norm, dtype=np.float64))(A))


def igd_plus(approx_norm, ref_norm) -> float:
    """IGD+ — Pareto-compliant; **endpoint PRIMÁRIO do estudo (D70)**."""
    _, IGDPlus, _, _ = _pymoo_indicators()
    A = np.atleast_2d(np.asarray(approx_norm, dtype=np.float64))
    if A.shape[0] == 0:
        return float("nan")
    return float(IGDPlus(np.asarray(ref_norm, dtype=np.float64))(A))


def gd(approx_norm, ref_norm) -> float:
    """GD (Generational Distance) do conjunto-aproximação ao ref set."""
    _, _, GD, _ = _pymoo_indicators()
    A = np.atleast_2d(np.asarray(approx_norm, dtype=np.float64))
    if A.shape[0] == 0:
        return float("nan")
    return float(GD(np.asarray(ref_norm, dtype=np.float64))(A))


def hv(approx_norm, ref_coord: float = HV_REF_COORD) -> float:
    """Hypervolume com ref = `ref_coord` em CADA coordenada (D69: 1,1).

    HV exato (box-decomposition do pymoo). Sob orçamento apertado o HV pode
    ZERAR (front mal-convergido) — isso é **dado**, não NaN (§12.2); retorna 0,0
    e a leitura apoia-se no IGD+."""
    _, _, _, HV = _pymoo_indicators()
    A = np.atleast_2d(np.asarray(approx_norm, dtype=np.float64))
    if A.shape[0] == 0:
        return 0.0
    M = A.shape[1]
    return float(HV(ref_point=np.full(M, float(ref_coord)))(A))


def spacing(approx_norm) -> float:
    """Spacing de Schott (1995) sobre objetivos normalizados, distância **L1**:

        d_i = min_{j≠i} ‖f_i − f_j‖₁ ,  SP = √( Σ(d̄ − d_i)² / (N−1) ).

    Mede a uniformidade da distribuição do conjunto-aproximação (menor = mais
    uniforme). `N<2 → 0`."""
    A = np.atleast_2d(np.asarray(approx_norm, dtype=np.float64))
    n = A.shape[0]
    if n < 2:
        return 0.0
    dmin = np.empty(n)
    for i in range(n):                       # N ≤ 31D−1 (≤929) → barato e sem NxN
        di = np.abs(A - A[i]).sum(axis=1)
        di[i] = np.inf
        dmin[i] = di.min()
    dbar = dmin.mean()
    return float(np.sqrt(np.sum((dbar - dmin) ** 2) / (n - 1)))


# ── Reference set (§12.2) ───────────────────────────────────────────────────

def true_front_raw(problema: str, n: int = REF_SET_SIZE) -> np.ndarray:
    """Front verdadeiro CRU (objetivos) de `true_pareto_front` (§4/L.19).

    Analítico para a maioria; EMPÍRICO (cache NSGA-II) para os BBOB≠F1 (§12.1).
    Retorna só `F` (o `X` do front não é usado nas métricas em objetivos)."""
    if problema in PROBLEMAS_SEM_FRONT_D72:
        # [D102.4/TD-08] barreira ANTES de instanciar: no DDMOP7 o caminho
        # empírico custaria 21,76 dias-core no `.p`. Só HV para estes.
        raise NotImplementedError(
            f"{problema} não tem front D72 (D102.4) — reporte só HV; o "
            f"consumidor deve pular PROBLEMAS_SEM_FRONT_D72.")
    from src import experiment            # lazy (puxa problems/pymoo)
    prob = experiment._instantiate_problem(problema)
    _, F = prob.true_pareto_front(n)
    return np.atleast_2d(np.asarray(F, dtype=np.float64))


def reference_set(problema: str, size: int = REF_SET_SIZE) -> np.ndarray:
    """Reference set NORMALIZADO p/ IGD/IGD+/GD (§12.2).

    Front verdadeiro → normalizado (mesma base do conjunto-aproximação) → filtro
    não-dominado → subamostra uniforme (por f₀) se maior que `size`.

    ⚠ ESQUELETO: o re-espaçamento FINO — arc-length nos 2-obj, Das-Dennis/Riesz
    s-energy nos 3-obj (§12.2) — é refinamento do R4 (D100). Aqui a subamostra
    uniforme entrega um ref set válido e reprodutível para o encanamento."""
    ideal, nadir = reference_bounds(problema)
    R = normalize(true_front_raw(problema, max(size, REF_SET_SIZE)), ideal, nadir)
    R = nondominated_front(R)
    if R.shape[0] > size:
        order = np.argsort(R[:, 0])
        pick = np.unique(np.linspace(0, R.shape[0] - 1, size).round().astype(int))
        R = R[order[pick]]
    return R


# ── Leitura da camada ① (reusa `naming`/`export`) ───────────────────────────

def _f_columns(names) -> list[str]:
    """As colunas de objetivo `f0..f{M-1}` presentes, em ordem (0-based §17.2)."""
    fs, i = [], 0
    present = set(names)
    while f"f{i}" in present:
        fs.append(f"f{i}")
        i += 1
    if not fs:
        raise ValueError(f"camada ① sem colunas f0..: {list(names)}")
    return fs


def load_real(exp: str, alg: str, problema: str, semente, *,
              data_root: str = naming.DEFAULT_DATA_ROOT) -> dict:
    """Lê a camada ① (`__real.parquet`) → `{F, fe_index, fase, M}`.

    `F` em float64 (n, M) — as avaliações reais DISTINTAS, na ordem de avaliação
    (`fe_index`). Fonte única das métricas oficiais (§12)."""
    import pyarrow.parquet as pq          # lazy
    path = naming.layer_path(exp, alg, problema, semente, "real", data_root)
    tbl = pq.read_table(path)
    fcols = _f_columns(tbl.column_names)
    F = np.column_stack([np.asarray(tbl.column(c), dtype=np.float64) for c in fcols])
    fe = np.asarray(tbl.column("fe_index"), dtype=np.int64) \
        if "fe_index" in tbl.column_names else np.arange(F.shape[0])
    fase = (np.asarray(tbl.column("fase")) if "fase" in tbl.column_names
            else np.array(["opt"] * F.shape[0]))
    return {"F": F, "fe_index": fe, "fase": np.asarray(fase), "M": len(fcols)}


# ── Métricas de um conjunto + trajetória ────────────────────────────────────

#: [T15.13 · laudo de fidelidade 15/08] Folga numérica do guard de régua: o
#: export é float32 (D53), logo um ponto que ESTÁ no ideal pode ler ~1e-7
#: abaixo dele. Abaixo disso é ruído de persistência; acima é régua furada.
_GUARD_FOLGA_REL = 1e-6

#: [T15.13b · CALIBRAÇÃO MEDIDA da torre, 15/08 — ver `checa_regua`] Folga
#: proporcional ao RANGE da régua (nadir−ideal). A folga só-absoluta acima
#: (1e-6) reprovava 533 células JÁ COLETADAS da campanha M8 — ZDT6 411/603,
#: MMF4 87/623, MMF1 35/629 — cujos ideais foram declarados ARREDONDADOS
#: (0,2809 · 0,001 · 0,0005) e são furados pelo dado real por 1,1e-4 a 3,6e-4
#: em valor absoluto. Isso NÃO é ruído de float32 (1e-7): é imprecisão da
#: régua declarada, e é achado de FIDELIDADE escalado ao autor (D97) — a
#: torre não corrige régua. Mas também NÃO é o modo de falha que este guard
#: existe para pegar. A medição separa os dois casos por TRÊS ORDENS DE
#: GRANDEZA, em unidade de range: arredondamento 1,5e-4…3,6e-4 · régua
#: genuinamente errada (DDMOP7 fase-1) 0,231…0,421. O corte em 1e-3 do range
#: fica ~3x acima do pior arredondamento e ~230x abaixo do furo real.
#: Furos tolerados NÃO somem: viram aviso auditável (`avisos_regua`).
_GUARD_FOLGA_RANGE = 1e-3

#: [T15.13b] Registro dos furos TOLERADOS (abaixo do corte), para auditoria:
#: {problema: (n_pontos, pior_furo_relativo_ao_range)}. Não é log — é estado
#: consultável por quem publica número (a R4 deve reportá-lo junto do HV).
avisos_regua: dict[str, tuple[int, float]] = {}


def checa_regua(F_raw, problema: str) -> None:
    """Guard EXECUTÁVEL da régua S.5 (D69): o dado não pode ser melhor que o ideal.

    O `ideal` é, por definição, o melhor valor alcançável por objetivo. Um ponto
    com `f < ideal` prova que a régua está errada — e, sob D69 (`f′ =
    (f−ideal)/(nadir−ideal)`), produz **normalizado negativo**, o que torna o HV
    com `ref=1,1` sem sentido (o ponto fica FORA do hipercubo).

    Por que isto existe (achado do laudo de fidelidade de 15/08): o selo
    `REGUAS_PROVISORIAS` é DECLARATIVO — ele não impede ninguém de calcular. E
    `reference_bounds` só levanta quando a régua é `None`; a fase 1 do DDMOP7
    NÃO é None, então nada disparava. Medido nos smokes de 15/08 com a zona
    morta: o melhor ponto alcançado é `[1/17 ; 90/690]` contra o ideal fase-1
    `[4/17 ; 202/690]` — **dominado nos DOIS eixos**, normalizado
    `[−0,231 ; −0,421]`. A errata do nadir (D102.3) não corrige isto: o furo é
    no ideal. A fase 2 pooled (D102.3) é a correção; este guard garante que
    ninguém publique um HV antes dela. Precedente da casa: gate que testa
    COMPORTAMENTO, não texto (T11 §4.1).

    Levanta `RuntimeError` (pára-e-loga D81). Não corrige nada sozinho —
    régua é fidelidade, e fidelidade é do autor (D97)."""
    F = np.atleast_2d(np.asarray(F_raw, dtype=np.float64))
    if F.size == 0:
        return
    ideal, nadir = reference_bounds(problema)
    # [T15.13b] folga = max(ruído de persistência, 1e-3 do range) — a
    # calibração medida que separa régua arredondada de régua errada.
    rng = np.abs(np.asarray(nadir, float) - np.asarray(ideal, float))
    folga = np.maximum(_GUARD_FOLGA_REL * np.maximum(1.0, np.abs(ideal)),
                       _GUARD_FOLGA_RANGE * np.maximum(rng, 1e-12))
    viol = F < (ideal - folga)
    if not viol.any():
        # [T15.13b] furo ABAIXO do corte não explode, mas fica AUDITÁVEL.
        leve = F < ideal
        if leve.any():
            pior = float(np.max((ideal - F)[leve] /
                                np.maximum(rng[np.where(leve)[1]], 1e-12)))
            n, p0 = avisos_regua.get(problema, (0, 0.0))
            avisos_regua[problema] = (n + int(leve.any(axis=1).sum()),
                                      max(p0, pior))
        return
    j = np.flatnonzero(viol.any(axis=0))
    pior = [(int(k), float(ideal[k]), float(F[:, k].min())) for k in j]
    prov = problema in REGUAS_PROVISORIAS
    raise RuntimeError(
        f"régua S.5 FURADA em {problema!r}: {int(viol.any(axis=1).sum())} de "
        f"{F.shape[0]} pontos são MELHORES que o ideal declarado. Por objetivo "
        f"(índice, ideal, melhor observado): {pior}. "
        + (f"A régua deste problema é PROVISÓRIA ({REGUAS_PROVISORIAS[problema]}) "
           f"— este é exatamente o caso que a fase 2 pós-hoc (D102.3) existe para "
           f"resolver. " if prov else
           f"A régua deste problema é DEFINITIVA — logo ou o ideal está errado, "
           f"ou o dado está. ")
        + "Sob D69 o normalizado fica NEGATIVO e o HV com ref=1,1 perde sentido. "
        "Pára-e-loga (D81): não invente valor, escale ao autor (D97).")


def metrics_of_set(F_raw, problema: str, *, ref_norm=None) -> dict:
    """As 5 métricas do conjunto-aproximação `F_raw` (objetivos CRUS) vs o front
    verdadeiro do `problema`. Normaliza (D69), filtra não-dominado, mede.

    [T15.13] Passa pelo `checa_regua` ANTES de normalizar — régua furada é
    pára-e-loga, não número silencioso."""
    ideal, nadir = reference_bounds(problema)
    checa_regua(F_raw, problema)
    nd = nondominated_front(np.atleast_2d(np.asarray(F_raw, dtype=np.float64)))
    A = normalize(nd, ideal, nadir)
    R = reference_set(problema) if ref_norm is None else np.asarray(ref_norm, float)
    return {
        "igd": igd(A, R),
        "igd_plus": igd_plus(A, R),     # PRIMÁRIA (D70)
        "hv": hv(A, HV_REF_COORD),
        "gd": gd(A, R),
        "spacing": spacing(A),
        "n_nd": int(nd.shape[0]),
    }


def trajectory(F_raw, fe_index, problema: str, *,
               n_checkpoints: int = 20, ref_norm=None) -> list[dict]:
    """Trajetória métrica × avaliações REAIS (§13, online): em cada checkpoint de
    FE, mede o conjunto não-dominado ACUMULADO até aquele FE.

    Retorna `[{fe, igd, igd_plus, hv, gd, spacing, n_nd}, …]`. `ref_norm` (o ref
    set normalizado) é calculado 1× e reusado — evita reconstruir o front por
    checkpoint. **Esqueleto:** a agregação das 30 sementes (mediana+IQR) é R4."""
    F = np.atleast_2d(np.asarray(F_raw, dtype=np.float64))
    fe = np.asarray(fe_index, dtype=np.int64)
    order = np.argsort(fe, kind="stable")
    F, fe = F[order], fe[order]
    n = F.shape[0]
    if n == 0:
        return []
    R = reference_set(problema) if ref_norm is None else np.asarray(ref_norm, float)
    cuts = np.unique(np.linspace(1, n, min(n_checkpoints, n)).round().astype(int))
    traj = []
    for k in cuts:
        m = metrics_of_set(F[:k], problema, ref_norm=R)
        m["fe"] = int(fe[k - 1])
        traj.append(m)
    return traj


def metrics_from_real(exp: str, alg: str, problema: str, semente, *,
                      data_root: str = naming.DEFAULT_DATA_ROOT,
                      with_trajectory: bool = True,
                      n_checkpoints: int = 20) -> dict:
    """Ponta-a-ponta do esqueleto: lê a ① do run, calcula as métricas FINAIS +
    (opcional) a trajetória. É o que o R4 chama por (alg, problema, semente)."""
    real = load_real(exp, alg, problema, semente, data_root=data_root)
    R = reference_set(problema)
    out = {"final": metrics_of_set(real["F"], problema, ref_norm=R)}
    if with_trajectory:
        out["trajectory"] = trajectory(real["F"], real["fe_index"], problema,
                                       n_checkpoints=n_checkpoints, ref_norm=R)
    return out


# ── Smoke da métrica (âncora D92 + sanity do front) ─────────────────────────

def hv_smoke_bbob_f1(n: int = 50000) -> float:
    """Âncora oficial de aceitação da métrica (D92): HV do front verdadeiro do
    **BBOB_F1**, normalizado por `(ideal, nadir)` da S.5, ref = 1,1 por
    coordenada → **1,0433**. `n` alto sub-amostra a densidade do front para o HV
    discreto convergir ao analítico (1,21 − 1/6)."""
    ideal, nadir = reference_bounds("BBOB_F1")
    F = true_front_raw("BBOB_F1", n)
    return hv(normalize(F, ideal, nadir), HV_REF_COORD)


def hv_front_sanity_bbob_f1(n: int = 50000) -> float:
    """SANITY do FRONT (rotulado — D92/§12.2), **NÃO** a métrica oficial: o mesmo
    front com ref no nadir `(1,0)` → **0,8333** (= 1 − 1/6). Valida a geometria
    do front analítico; um gate aqui reprovaria a métrica D69 correta."""
    ideal, nadir = reference_bounds("BBOB_F1")
    F = true_front_raw("BBOB_F1", n)
    return hv(normalize(F, ideal, nadir), 1.0)


__all__ = [
    "PRIMARY_METRIC", "HV_REF_COORD", "HV_SMOKE_BBOB_F1", "HV_SANITY_BBOB_F1",
    "REF_SET_SIZE", "F_MIN_MAX",
    "reference_bounds", "normalize", "nondominated_front",
    "igd", "igd_plus", "gd", "hv", "spacing",
    "true_front_raw", "reference_set", "load_real",
    "metrics_of_set", "trajectory", "metrics_from_real",
    "hv_smoke_bbob_f1", "hv_front_sanity_bbob_f1",
]
