"""Métricas de qualidade das frentes para os notebooks de análise (src_nb) — 03/10/2026.

Movido de `src/metrics.py` e enxugado: fica só o que `1. fitness_landscape.ipynb` e `2. analises_dissertacao.ipynb`
usam. Tudo é medido no espaço de objetivos NORMALIZADO pela régua S.5 (`F_MIN_MAX`: ideal e nadir CRUS do front
verdadeiro, fixos por problema — D69), com ref-point do HV = 1,1 em cada coordenada (D69/D92).

As três métricas oficiais do cap. 5 (decisão do autor, 03/10/2026):
- **HV** (`hv`, puro) e **HV normalizado** = hv / `hv_frente` (em [0, 1]; 1 = a frente de referência inteira);
- **IGD+** (`igd_plus`, primária — D70), média do d⁺ sobre a frente de referência Z;
- **CPF_K20** (`cpf`), cobertura da frente de Tian et al. (2019) com cota VPF/max(20, N) e deduplicação dos z*.

A frente de referência Z é UNIFORME ao longo da frente verdadeira (`reference_set_uniform`: 2 objetivos por comprimento
de arco, 3 por ponto mais distante; frentes empíricas como estão). `reference_set` (subamostra por f₀, a regra antiga)
permanece porque o notebook 1 a usa na exportação das frentes. `*_passos` devolvem a memória de cálculo de cada métrica
e `memoria_compacta`/`reconstruir_memoria` gravam e reconstroem essa memória por experimento.

Requer numpy + pymoo; `src.problems`/`src.experiment` são importados preguiçosamente para instanciar os problemas.
"""

from __future__ import annotations

import numpy as np

# ── Constantes de decisão (§12/D69/D70/D92/S.5) ─────────────────────────────

#: Ref-point do HV: 1,1 em CADA coordenada no espaço normalizado (D69/D92).
HV_REF_COORD = 1.1

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
    # foi COMPUTADA e a régua RATIFICADA pelo autor em 2026-08-22 (ver
    # REGUAS_PROVISORIAS abaixo — o DDMOP7 saiu do selo). O guard executável
    # `checa_regua` (T15.13) faz o cálculo FALHAR se esta régua for furada —
    # verificado: 0 furos em 302.643 pontos do corpus final.
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
    # [REAL-2.15 RATIFICADA · autor 2026-08-22] O DDMOP7 SAIU deste selo. A fase 2
    # pooled (D102.3) foi COMPUTADA na validação final sobre 568 células válidas
    # (293.944 pontos de ①): z* = [1/17 ; 84/690] · znad da nuvem = [1 ; 593/690]
    # · front pooled de 6 pontos, 100% vindos da busca. Decisão do autor: MANTER
    # ideal = [0;0] (dedutivo — e foi a régua EM EXECUÇÃO no c122/c262, que a
    # consomem durante a busca; trocar dessincronizaria busca e análise) e
    # MANTER nadir = 468/690 (nunca excedido por ND válido; máx n=383). O z*
    # pooled NÃO é adotado (uma estimativa voltaria a poder ser furada); o nadir
    # do front pooled NÃO é adotado (cliparia ND válidos). Sensibilidade medida:
    # Spearman(ranking fase-1 × pooled) = 0,9993 — a escolha não move ranking.
    # Os valores pooled ficam DECLARADOS no texto (f5/final/reais/DDMOP7.json).
    # 17 células s0 rodadas pré-errata (commit 3240f4b) sancionadas como classe
    # (2): os configs delas não usam a régua na busca; a métrica é pós-hoc.
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


def igd_plus(approx_norm, ref_norm) -> float:
    """IGD+ — Pareto-compliant; **endpoint PRIMÁRIO do estudo (D70)**."""
    _, IGDPlus, _, _ = _pymoo_indicators()
    A = np.atleast_2d(np.asarray(approx_norm, dtype=np.float64))
    if A.shape[0] == 0:
        return float("nan")
    return float(IGDPlus(np.asarray(ref_norm, dtype=np.float64))(A))


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


# ── CPF_K20 — cobertura da frente a resolução fixa (Tian et al., 2019; porte do CPF.m do PlatEMO) ──
#  Variante declarada (decisão do autor, 03/10/2026): cota por solução VPF/max(K, N), com K = 20 e N = nº de
#  pontos únicos de S levados à frente. Até 20 soluções cada uma representa no máximo 1/20 da frente (um conjunto
#  só cobre a frente inteira com ao menos 20 soluções bem distribuídas); acima de 20 a cota volta a ser VPF/N — a
#  CPF publicada —, o que limita a métrica a [0, 1] por construção. K=None → CPF publicada (cota VPF/N) sempre.
#  Diversidade PURA (ignora convergência), maior é melhor. Entradas JÁ normalizadas (D69).

#: Resolução mínima da CPF_K20 — a população dos pisos (uma solução representa no máximo 1/K da frente).
CPF_K = 20


def _cpf_map(x, PF):
    """`map()` do CPF.m: projeta pontos da variedade (M−1)-d da frente no hipercubo unitário (M−1)-d.
    Em M = 2 reduz-se a y = (f₁ − f₂ + 1)/2 — a posição ao longo da reta f₁ + f₂ = 1."""
    x = np.array(x, float); PF = np.array(PF, float); N, M = x.shape
    x = x - ((x.sum(1) - 1) / M)[:, None]; PF = PF - ((PF.sum(1) - 1) / M)[:, None]   # desliza na diagonal até Σf = 1
    x = x - PF.min(0); x = x / x.sum(1)[:, None]; x = np.maximum(1e-6, x)
    y = np.zeros((N, M - 1))
    for i in range(N):                                   # índices 1-based do MATLAB emulados
        c = np.ones(M + 1); k = int(np.nonzero(x[i] != 0)[0][0]) + 1
        for j in range(k + 1, M + 1):
            lo, hi = M - j + 2, M - k
            temp = x[i, j - 1] / x[i, k - 1] * (np.prod(c[lo:hi + 1]) if lo <= hi else 1.0)
            c[M - j + 1] = 1.0 / (temp + 1.0)
        y[i] = c[1:M]
    return y ** np.arange(M - 1, 0, -1)[None, :]


def _cpf_coverage_detalhada(P, maxv) -> dict:
    """`Coverage()` do CPF.m, devolvendo a memória de cálculo: para cada ponto da régua, o lado `L` do
    hipercubo (distância de Chebyshev ao vizinho mais próximo, limitada à cota `maxv^(1/(M−1))`), os cantos
    `lower`/`upper` (hipercubo centrado no ponto, recortado em [0, 1]) e o volume `vol`; `V` é a soma."""
    P = np.array(P, float); N, M = P.shape; L = np.zeros(N)
    for i in range(N):
        P1 = P.copy(); P1[i] = np.inf
        L[i] = np.max(np.abs(P1 - P[i]), axis=1).min()   # N = 1 → inf → vira a cota
    cota = float(maxv) ** (1.0 / M) if np.isfinite(maxv) else np.inf
    L = np.minimum(L, cota)
    Lower = np.maximum(0, P - (L / 2)[:, None]); Upper = np.minimum(1, P + (L / 2)[:, None])
    vol = np.prod(Upper - Lower, axis=1)
    return {"P": P, "L": L, "cota_lado": cota, "lower": Lower, "upper": Upper, "vol": vol, "V": float(vol.sum())}


def _cpf_scale(ref_norm):
    """Passo 1 da CPF: mínimo e range de Z, coordenada a coordenada (guarda `range ≥ 1e-12`)."""
    Z = np.atleast_2d(np.asarray(ref_norm, dtype=np.float64))
    fmin = Z.min(0)
    return fmin, np.maximum(Z.max(0) - fmin, _RANGE_FLOOR)


def cpf_vpf(ref_norm) -> float:
    """VPF: cobertura da própria frente de referência Z na régua, SEM cota (lado = distância ao vizinho) —
    denominador da CPF. O(|Z|²): calcular UMA vez por problema e cachear.

    [03/10] Z é DEDUPLICADA antes (`np.unique`): um ponto repetido em Z tem distância zero ao vizinho,
    segmento nulo, e deflaciona o VPF (medido: MMF4 com a Z da classe caía de 0,69 para 0,09)."""
    return cpf_vpf_detalhado(ref_norm)["V"]


def cpf_vpf_detalhado(ref_norm) -> dict:
    """Os cubos da própria Z na régua (sem cota): a decomposição que define a PEGADA da frente — `V` é o VPF.
    Passe este dicionário como `VPF` a `cpf_passos`/`cpf` para também obter `cpf_dentro` (ver lá)."""
    Z = np.unique(np.atleast_2d(np.asarray(ref_norm, dtype=np.float64)), axis=0)
    fmin, rng = _cpf_scale(Z)
    Z = (Z - fmin) / rng
    return _cpf_coverage_detalhada(_cpf_map(Z, Z), np.inf)


def cpf(approx_norm, ref_norm, K: int | None = CPF_K, VPF=None) -> float:
    """CPF_K20 do conjunto-aproximação (normalizado) contra a frente de referência Z (normalizada).

    (1) reescala S e Z pelo min/max de Z; (2) leva cada s ao ponto mais próximo de Z (z*) e DEDUPLICA
    (dois s no mesmo z* contam uma vez); (3) projeta z* e Z na régua pelo `map`; (4) cada ponto ganha um
    hipercubo de lado min(dist. ao vizinho, (VPF/max(K, N))^(1/(M−1))) recortado em [0,1], N = nº de z* únicos; (5) CPF = Σ volumes / VPF ∈ [0, 1].
    `S` vazio → NaN. `VPF` (de `cpf_vpf`) é cacheado por problema pelo chamador."""
    return cpf_passos(approx_norm, ref_norm, K=K, VPF=VPF)["cpf"]


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


# ── Memória de cálculo (passo a passo) das três métricas oficiais ───────────
#  [03/10/2026] Cada função abaixo devolve o MESMO número da função oficial (hv / igd_plus / cpf) e, junto,
#  todos os intermediários necessários para ilustrar o cálculo (fichas "HV, IGD e IGD+ na prática").
#  São as únicas implementações dos passos: `cpf` é um atalho para `cpf_passos(...)["cpf"]`.

def hv_frente(ref_norm, ref_coord: float = HV_REF_COORD) -> float:
    """HV da própria frente de referência Z (normalizada; não dominada; sem duplicatas) com r = ref_coord — o
    máximo atingível no problema e o denominador do `hv_norm`. Calcular UMA vez por problema e cachear."""
    Z = np.unique(np.atleast_2d(np.asarray(ref_norm, dtype=np.float64)), axis=0)
    if Z.size == 0:
        return float("nan")
    return hv(nondominated_front(Z), ref_coord)


def hv_passos(approx_norm, ref_coord: float = HV_REF_COORD, *, contribuicoes: bool = True,
              hv_ref: float | None = None) -> dict:
    """HV no espaço normalizado com r = ref_coord por coordenada, com a memória de cálculo.

    Devolve: `A` (como veio), `dentro` (quem domina r — só esses contribuem), `A_dentro`, `r`, `hv` (pymoo — o HV
    PURO), e, se `hv_ref` (= `hv_frente(Z)`) for dado, `hv_frente` e `hv_norm` = hv / hv_frente — o HV NORMALIZADO
    pelo da frente (decisão 03/10: fica em [0, 1], 1 = a frente inteira; pode passar de 1 só onde a frente de
    referência é empírica e o conjunto a domina em parte). Em 2 objetivos, a varredura exata: `A_ord` (por f₁
    crescente), `largura` (f₁ do próximo − f₁ do ponto, com r₁ no último), `altura` (r₂ − f₂), `area` por retângulo
    e `hv_varredura` (= Σ área, confere o pymoo). `contrib` = contribuição exclusiva de cada ponto,
    hv(A) − hv(A sem o ponto) (qualquer M; |A| ≤ 400)."""
    A = np.atleast_2d(np.asarray(approx_norm, dtype=np.float64))
    M = A.shape[1]
    dentro = (A < ref_coord).all(axis=1) if A.size else np.zeros(0, bool)
    Ad = A[dentro]
    valor = float("nan") if A.size == 0 else hv(Ad, ref_coord)
    out = {"M": M, "r": np.full(M, float(ref_coord)), "A": A, "dentro": dentro, "A_dentro": Ad, "hv": valor,
           "hv_frente": float("nan") if hv_ref is None else float(hv_ref),
           "hv_norm": float("nan") if (hv_ref is None or not np.isfinite(hv_ref) or hv_ref <= 0) else valor / float(hv_ref)}
    if M == 2 and Ad.shape[0]:
        P = Ad[np.argsort(Ad[:, 0], kind="stable")]
        f1_prox = np.r_[P[1:, 0], ref_coord]
        larg, alt = f1_prox - P[:, 0], ref_coord - P[:, 1]
        out.update(A_ord=P, largura=larg, altura=alt, area=larg * alt, hv_varredura=float((larg * alt).sum()))
    if contribuicoes and 0 < Ad.shape[0] <= 400:
        out["contrib"] = np.array([out["hv"] - hv(np.delete(Ad, i, axis=0), ref_coord) for i in range(Ad.shape[0])])
    return out


def igd_plus_passos(approx_norm, ref_norm, *, bloco: int = 2000) -> dict:
    """IGD+ (e o IGD comum, para contraste) com a memória de cálculo, por ponto de referência z.

    Para cada z ∈ Z: `j` = índice do ponto de A mais próximo em d⁺, `dplus` = min_a d⁺(z, a) com
    d⁺(z, a) = √Σ max(aᵢ − zᵢ, 0)², `p` = projeção de a sobre o quadrante dominado por z (o canto
    max(a, z); p = z quando a domina z e d⁺ = 0), `d_euclid` = min_a ‖z − a‖ (o IGD comum).
    `cobertura_por_a` = quantos z cada ponto de A serve. `igd_plus` = média de `dplus` (= pymoo IGDPlus)."""
    A = np.atleast_2d(np.asarray(approx_norm, dtype=np.float64))
    Z = np.atleast_2d(np.asarray(ref_norm, dtype=np.float64))
    if A.shape[0] == 0 or Z.shape[0] == 0:
        return {"A": A, "Z": Z, "igd_plus": float("nan"), "igd": float("nan")}
    j = np.empty(Z.shape[0], int); dplus = np.empty(Z.shape[0]); deuc = np.empty(Z.shape[0])
    for i0 in range(0, Z.shape[0], bloco):                     # em blocos: |Z|×|A|×M nunca inteira na memória
        Zb = Z[i0:i0 + bloco]
        diff = A[None, :, :] - Zb[:, None, :]
        Dp = np.sqrt((np.maximum(diff, 0.0) ** 2).sum(-1))
        De = np.sqrt((diff ** 2).sum(-1))
        jb = Dp.argmin(1)
        j[i0:i0 + bloco] = jb
        dplus[i0:i0 + bloco] = Dp[np.arange(len(jb)), jb]
        deuc[i0:i0 + bloco] = De.min(1)
    p = np.maximum(A[j], Z)
    return {"A": A, "Z": Z, "j": j, "dplus": dplus, "p": p, "d_euclid": deuc,
            "cobertura_por_a": np.bincount(j, minlength=A.shape[0]),
            "igd_plus": float(dplus.mean()), "igd": float(deuc.mean())}


def _volume_intersecao_cubos(loA, upA, loB, upB, bloco: int = 2000) -> np.ndarray:
    """Matriz |A|×|B| do volume de interseção entre os hipercubos [loA, upA] e [loB, upB] (em blocos de B)."""
    out = np.empty((loA.shape[0], loB.shape[0]))
    for i0 in range(0, loB.shape[0], bloco):
        lo = np.maximum(loA[:, None, :], loB[None, i0:i0 + bloco, :])
        up = np.minimum(upA[:, None, :], upB[None, i0:i0 + bloco, :])
        out[:, i0:i0 + bloco] = np.prod(np.maximum(up - lo, 0.0), axis=-1)
    return out


def cpf_passos(approx_norm, ref_norm, K: int | None = CPF_K, VPF=None) -> dict:
    """CPF_K20 com a memória de cálculo dos cinco passos (porte do CPF.m; cota VPF/max(K, N); K=None → CPF publicada).

    (1) `fmin`/`rng` de Z e os conjuntos reescalados `S1`, `Z1`; (2) `j_star` = ponto de Z mais próximo de
    cada s (euclidiana) e `idx_unicos` (duplicatas em z* contam uma vez) → `S_star`; (3) `yZ`, `yS` =
    posições na régua [0,1]^(M−1) pelo `map`; (4) `cob_Z` (os cubos da própria Z, sem cota — a pegada da
    frente; V = VPF) e `cob_S` (os cubos de S* com a cota VPF/max(K, N), N = |S*|): lado `L`, `cota_lado`, cantos e `vol`;
    (5) `cpf` = V / VPF, em [0, 1] (≤ N/K quando N ≤ K; ≤ 1 sempre, porque cada cubo vale no máximo a cota).

    `VPF` pode ser o número (só `cpf`) ou o dicionário de `cpf_vpf_detalhado` (cacheado por problema): com
    ele sai também `V_dentro` e `cpf_dentro` = a parte dos cubos de S* que cai DENTRO da pegada da frente
    (interseção com os cubos de Z) ÷ VPF — diagnóstico apenas (subestima em 3 objetivos; não é a métrica)."""
    S = np.atleast_2d(np.asarray(approx_norm, dtype=np.float64))
    Z = np.unique(np.atleast_2d(np.asarray(ref_norm, dtype=np.float64)), axis=0)
    if S.shape[0] == 0 or S.shape[1] != Z.shape[1]:
        return {"S": S, "Z": Z, "cpf": float("nan"), "cpf_dentro": float("nan")}
    fmin, rng = _cpf_scale(Z)
    S1 = (S - fmin) / rng; Z1 = (Z - fmin) / rng                                   # passo 1
    j_star = np.linalg.norm(S1[:, None, :] - Z1[None, :, :], axis=-1).argmin(1)   # passo 2
    idx_unicos = np.unique(j_star)
    S_star = Z1[idx_unicos]
    cob_Z = VPF if isinstance(VPF, dict) else None
    yZ = cob_Z["P"] if cob_Z is not None else _cpf_map(Z1, Z1)                     # passo 3 (yZ vem do cache por problema)
    yS = _cpf_map(S_star, Z1)
    if cob_Z is None and VPF is None:
        cob_Z = _cpf_coverage_detalhada(yZ, np.inf)
    vpf = float(cob_Z["V"]) if cob_Z is not None else float(VPF)
    K_ef = max(K, S_star.shape[0]) if K else S_star.shape[0]                       # cota VPF/max(K, N) — decisão 03/10
    cob_S = _cpf_coverage_detalhada(yS, vpf / K_ef)                                # passo 4
    V_dentro = cpf_dentro = float("nan")
    if cob_Z is not None:
        V_dentro = float(_volume_intersecao_cubos(cob_S["lower"], cob_S["upper"], cob_Z["lower"], cob_Z["upper"]).sum())
        cpf_dentro = V_dentro / vpf
    return {"S": S, "Z": Z, "fmin": fmin, "rng": rng, "S1": S1, "Z1": Z1, "j_star": j_star,
            "idx_unicos": idx_unicos, "S_star": S_star, "n_duplicados": int(S.shape[0] - idx_unicos.size),
            "yZ": yZ, "yS": yS, "cob_Z": cob_Z, "cob_S": cob_S, "K": K_ef, "VPF": vpf,
            "cota_vol": float(vpf / K_ef), "V": cob_S["V"], "cpf": float(cob_S["V"] / vpf),     # passo 5
            "V_dentro": V_dentro, "cpf_dentro": cpf_dentro}


# ── Memória de cálculo GRAVÁVEL por experimento, e a sua reconstrução ───────
#  [03/10/2026] O que se grava por célula (`memoria_compacta`) é o mínimo que reconstrói as três figuras passo a
#  passo sem recomputar nada caro: o conjunto não dominado A (normalizado), a contribuição exclusiva de cada ponto
#  no HV (as recomputações do pymoo), o z* de cada s (CPF) e, por ponto de referência z, o vizinho em A e o d⁺
#  (IGD+). `reconstruir_memoria` deriva o resto com numpy a partir de A, da Z do problema e dos cubos de Z.

def memoria_compacta(algoritmo: str, problema: str, seed, m: dict, mem: dict) -> dict:
    """Uma linha gravável (listas) do `df_memoria_calculo` a partir da saída de `metricas(..., memoria=True)`."""
    h = mem.get("hv", {}); g = mem.get("igd_plus"); c = mem.get("cpf")
    return {"algoritmo": algoritmo, "problema": problema, "seed": seed, "M": int(h.get("M", 0)),
            "A": h["A"].astype(np.float32).ravel().tolist() if "A" in h else None,
            "contrib": h["contrib"].astype(np.float32).tolist() if h.get("contrib") is not None else None,
            "j_star": c["j_star"].astype(np.int32).tolist() if c else None,
            "j": g["j"].astype(np.int32).tolist() if g else None,
            "dplus": g["dplus"].astype(np.float32).tolist() if g else None}


def reconstruir_memoria(reg, m: dict, Z=None, cob_Z: dict | None = None) -> dict:
    """Reconstrói o dicionário `mem` das figuras (chaves `hv`, `igd_plus`, `cpf`) a partir de uma linha de
    `df_memoria_calculo` (`reg`, com A/contrib/j_star/j/dplus), da linha de métricas (`m`: hv, hv_frente, hv_norm,
    igd), da frente de referência `Z` do problema e dos cubos de Z (`cob_Z` = `cpf_vpf_detalhado(Z)`).
    Sem `Z` (DDMOP7) devolve só a parte do HV."""
    M = int(reg["M"]); A = np.asarray(reg["A"], dtype=np.float64).reshape(-1, M)
    r = HV_REF_COORD; dentro = (A < r).all(axis=1); Ad = A[dentro]
    h = {"M": M, "r": np.full(M, r), "A": A, "dentro": dentro, "A_dentro": Ad, "hv": float(m["hv"]),
         "hv_frente": float(m.get("hv_frente", np.nan)), "hv_norm": float(m.get("hv_norm", np.nan)),
         "contrib": np.asarray(reg["contrib"], dtype=np.float64) if reg["contrib"] is not None else None}
    if M == 2 and Ad.shape[0]:
        P = Ad[np.argsort(Ad[:, 0], kind="stable")]; larg = np.r_[P[1:, 0], r] - P[:, 0]; alt = r - P[:, 1]
        h.update(A_ord=P, largura=larg, altura=alt, area=larg * alt, hv_varredura=float((larg * alt).sum()))
    mem = {"hv": h}
    if Z is None or reg["j"] is None:
        return mem
    Z = np.atleast_2d(np.asarray(Z, dtype=np.float64))
    j = np.asarray(reg["j"], dtype=int); dplus = np.asarray(reg["dplus"], dtype=np.float64)
    mem["igd_plus"] = {"A": A, "Z": Z, "j": j, "dplus": dplus, "p": np.maximum(A[j], Z),
                       "cobertura_por_a": np.bincount(j, minlength=A.shape[0]), "igd_plus": float(dplus.mean()),
                       "igd": float(m["igd"]) if "igd" in m and np.isfinite(m["igd"]) else float("nan")}
    if cob_Z is None:
        cob_Z = cpf_vpf_detalhado(Z)
    Zu = np.unique(Z, axis=0); fmin, rng = _cpf_scale(Zu); S1 = (A - fmin) / rng; Z1 = (Zu - fmin) / rng
    j_star = np.asarray(reg["j_star"], dtype=int); idx = np.unique(j_star); S_star = Z1[idx]
    vpf = float(cob_Z["V"]); K_ef = max(CPF_K, idx.size)
    yS = _cpf_map(S_star, Z1); cob_S = _cpf_coverage_detalhada(yS, vpf / K_ef)
    mem["cpf"] = {"S": A, "Z": Zu, "fmin": fmin, "rng": rng, "S1": S1, "Z1": Z1, "j_star": j_star, "idx_unicos": idx,
                  "S_star": S_star, "n_duplicados": int(A.shape[0] - idx.size), "yZ": cob_Z["P"], "yS": yS,
                  "cob_Z": cob_Z, "cob_S": cob_S, "K": K_ef, "VPF": vpf, "cota_vol": vpf / K_ef,
                  "V": cob_S["V"], "cpf": float(cob_S["V"] / vpf)}
    return mem

# ── Frente de referência UNIFORME (a Z única do IGD+ e da CPF_K20) ──────────
#  [03/10/2026] Os amostradores de `true_pareto_front` são uniformes na VARIÁVEL (x₁, t, grade u×v), não ao
#  longo da frente — e repetem pontos (MMF1/MMF4: duas ramificações do PS com o mesmo f). Aqui a frente vira
#  uma amostra UNIFORME no espaço normalizado: em 2 objetivos, reamostragem por comprimento de arco sobre
#  um candidato denso (trecho a trecho, sem atravessar vãos — ZDT3, WFG1, WFG2); em 3, amostragem de
#  ponto mais distante (maximin) sobre o candidato denso — sem interpolar. As frentes EMPÍRICAS (D72) são
#  usadas como estão (todos os pontos únicos e não dominados): não se inventa ponto de frente empírica.

#: Tamanho da frente de referência uniforme por número de objetivos (ver `reference_set_uniform`).
N_REF_UNIFORME: dict[int, int] = {2: 2000, 3: 10000}

#: Tamanho do candidato denso de onde a frente uniforme é amostrada (3 objetivos: grade 400×400).
N_CANDIDATOS = 160_000

#: Tolerância da deduplicação do candidato (casas decimais no espaço normalizado): os amostradores com duas
#: ramificações do PS (MMF1, MMF4) e os de forma multimodal (WFG4/WFG5) repetem o mesmo f com erro de 1e-12.
_DEDUP_DECIMAIS = 10

#: Problemas cuja frente de referência é EMPÍRICA (cache NSGA-II, D72): usados como estão.
PROBLEMAS_FRENTE_EMPIRICA: frozenset = frozenset({
    "BBOB_F5", "BBOB_F17", "BBOB_F22", "BBOB_F37", "BBOB_F49", "BBOB_F55", "RE21", "ESTOQUE40"})


def frente_candidata(problema: str, n_cand: int = N_CANDIDATOS) -> np.ndarray:
    """Candidato denso da frente verdadeira, NORMALIZADO (S.5), não dominado e sem duplicatas.
    Em 3 objetivos os amostadores usam grade n×n: pede-se n = ⌈√n_cand⌉."""
    ideal, nadir = reference_bounds(problema)
    M = ideal.size
    if problema in PROBLEMAS_FRENTE_EMPIRICA:
        n_param = 10 ** 9                       # o cache inteiro (true_pareto_front subamostra se len(F) > n)
    else:
        n_param = n_cand if M == 2 else int(np.ceil(np.sqrt(n_cand)))
    R = normalize(true_front_raw(problema, n_param), ideal, nadir)
    R = np.unique(np.round(nondominated_front(R), _DEDUP_DECIMAIS), axis=0)
    return R


def _reamostra_arco_2d(R, n: int, fator_vao: float = 10.0) -> np.ndarray:
    """n pontos igualmente espaçados em COMPRIMENTO DE ARCO sobre a poligonal de R (2 objetivos, ordenada
    por f₁). Um salto entre vizinhos maior que `fator_vao` × o espaçamento-alvo (comprimento total / n) é
    um VÃO: a frente é reamostrada trecho a trecho (pontos por trecho ∝ comprimento), e nenhum ponto é
    interpolado no vão. (A referência é o alvo, não a mediana dos saltos: candidatos uniformes na variável
    ficam esparsos nos trechos íngremes — ZDT1 perto de f₁ = 0, ZDT6 — e a mediana acusaria vãos falsos.)"""
    P = R[np.argsort(R[:, 0], kind="stable")]
    if P.shape[0] <= 2:
        return P
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    cortes = np.flatnonzero(seg > fator_vao * seg.sum() / n) + 1
    trechos = np.split(np.arange(P.shape[0]), cortes)
    comp = np.array([seg[t[0]:t[-1]].sum() if len(t) > 1 else 0.0 for t in trechos])
    total = comp.sum()
    saida = []
    for t, c in zip(trechos, comp):
        Q = P[t]
        if len(t) == 1 or c == 0.0:
            saida.append(Q[:1]); continue
        k = max(2, int(round(n * c / total)))
        s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
        alvo = np.linspace(0.0, s[-1], k)
        saida.append(np.column_stack([np.interp(alvo, s, Q[:, m]) for m in range(Q.shape[1])]))
    Z = np.vstack(saida)
    return Z[np.argsort(Z[:, 0], kind="stable")]


def _fps(R, n: int, inicio: int | None = None) -> np.ndarray:
    """Amostragem de ponto mais distante (maximin, determinística): começa no ponto de menor f₁ e, a cada
    passo, acrescenta o candidato mais longe do conjunto já escolhido. Cobertura quase uniforme de qualquer
    variedade (contínua ou em pedaços) sem interpolar; devolve R inteiro se |R| ≤ n."""
    R = np.asarray(R, dtype=np.float64)
    if R.shape[0] <= n:
        return R
    i = int(np.argmin(R[:, 0])) if inicio is None else int(inicio)
    sel = [i]
    dmin = np.linalg.norm(R - R[i], axis=1)
    for _ in range(n - 1):
        i = int(np.argmax(dmin)); sel.append(i)
        dmin = np.minimum(dmin, np.linalg.norm(R - R[i], axis=1))
    return R[np.array(sel)]


def reference_set_uniform(problema: str, n: int | None = None, *, n_cand: int = N_CANDIDATOS) -> np.ndarray:
    """A frente de referência Z OFICIAL (03/10/2026) do IGD+ e da CPF_K20: normalizada (S.5), não dominada,
    sem duplicatas e UNIFORMEMENTE espaçada ao longo da frente verdadeira — `n` pontos (padrão
    `N_REF_UNIFORME[M]`). Frentes empíricas (D72) voltam como estão (subamostradas por maximin se > n).
    DDMOP7 não tem frente (D102.4) → NotImplementedError, como `true_front_raw`."""
    ideal, _ = reference_bounds(problema)
    M = ideal.size
    n = N_REF_UNIFORME[M] if n is None else int(n)
    R = frente_candidata(problema, n_cand)
    if problema in PROBLEMAS_FRENTE_EMPIRICA:
        Z = R if R.shape[0] <= n else _fps(R, n)
    elif M == 2:
        Z = _reamostra_arco_2d(R, n)
    else:
        Z = _fps(R, n)
    Z = np.unique(Z, axis=0)
    return Z[np.lexsort(Z[:, ::-1].T)]


def uniformidade(Z) -> dict:
    """Diagnóstico de uniformidade de uma amostra Z da frente: distância ao vizinho mais próximo (dnn) —
    média, desvio, CV (desvio/média: 0 = perfeitamente uniforme), mínimo, máximo e razão máx/mín — e, em
    2 objetivos, os saltos consecutivos por f₁ (contando os VÃOS > 20× a mediana, que são geometria da frente,
    não irregularidade da amostra)."""
    from scipy.spatial import cKDTree
    Z = np.atleast_2d(np.asarray(Z, dtype=np.float64))
    n, M = Z.shape
    out = {"n": int(n), "M": int(M)}
    if n < 2:
        return out
    d, _ = cKDTree(Z).query(Z, k=2)
    dnn = d[:, 1]
    out.update(dnn_media=float(dnn.mean()), dnn_desvio=float(dnn.std()), dnn_cv=float(dnn.std() / dnn.mean()),
               dnn_min=float(dnn.min()), dnn_max=float(dnn.max()), dnn_razao=float(dnn.max() / max(dnn.min(), 1e-300)))
    if M == 2:
        P = Z[np.argsort(Z[:, 0], kind="stable")]
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        vao = seg > 20.0 * np.median(seg)
        s = seg[~vao]
        out.update(n_vaos=int(vao.sum()), seg_media=float(s.mean()), seg_cv=float(s.std() / s.mean()),
                   seg_min=float(s.min()), seg_max=float(s.max()))
    return out

# ── Guard executável da régua S.5 (`checa_regua`) ─────────────────────────

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
