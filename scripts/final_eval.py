#!/usr/bin/env python3
"""Avaliador PÓS-HOC do ND final do regime OFFLINE — a camada ⑦ (DI-08).

O QUE RESOLVE. O §11/B7.5 manda avaliar o conjunto não-dominado FINAL dos
algoritmos offline **uma vez** na função verdadeira — "a única chamada real do
offline" — e computar as métricas sobre ele. Mas o desenho do regime fixa
① = o DATASET (31D−1 linhas EXATAS, que o gate exige): as ~N avaliações finais
não têm casa lá. A DI-08 decidiu a camada própria `__final.parquet`, avaliada
pós-hoc em Python canônico (`src/problems.py`), **uniforme para os 5 configs
offline** — o que tira a ponte MATLAB da equação: o e103 (MATLAB) e o
b5r/b5m/c311/piso-off (Python) passam pelo MESMO avaliador, então a comparação
cross-stack do §9 vale por construção.

COMO FUNCIONA. Lê a ③ `__surrogate.parquet` do run, pega a ÚLTIMA geração
(descartando as linhas de sonda, que não são candidatos da busca), avalia
aqueles decs 1× em `problems.py` em float64 e grava a ⑦. A avaliação é
**FORA do orçamento**: nenhum `FEBudget` é instanciado, a ① não é tocada e o
`fe_final` do manifesto não muda (a exceção contábil documentada do §11).

Convenção B7.5 — **avaliar TODOS os finais e filtrar pós-real**: guardamos as N
linhas (D54, salvar tudo) e marcamos `nd_pos_real` depois de conhecer o f
verdadeiro. Filtrar a não-dominância ANTES seria filtrar pela fantasia do
modelo, e é justamente o "erro de fantasia" que esta camada existe para medir.

DETERMINÍSTICO e IDEMPOTENTE: as funções dos problemas são analíticas e puras,
não há RNG em lugar nenhum deste caminho; rodar duas vezes produz o mesmo
parquet. Por padrão um `__final` já existente é PRESERVADO (`--force` reescreve).

USO
    PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
    $PY scripts/final_eval.py --exp off --alg b5r --problema MMF1 --semente 0
    $PY scripts/final_eval.py --exp main --alg e103 --problema MMF1 --semente 0
    $PY scripts/final_eval.py --alg e103 --all-seeds          # lote
    $PY scripts/final_eval.py ... --check                     # só verifica

⚠ CAVEAT DE PRECISÃO (definição em aberto — ver handoff §Definições): os decs
lidos da ③ estão em **float32** (D53 vale para todas as camadas). A avaliação
pós-hoc é, portanto, sobre o dec float32-truncado, não sobre o float64 que o
algoritmo tinha em mãos. Para os cartões R3 (Python) isso é evitável — o
harness pode chamar `standalone_harness.write_final(...)` no fim do run com os
decs float64 em memória. Para o e103 (MATLAB, já executado) a ③ é a única
fonte. MEDIDO no STUB (não estimado): desvio relativo em `f` de até **9,7e-6**
(MMF1) e 6,0e-8 (ZDT1), com **0 inversões** do filtro `nd_pos_real` em ambos.
Fica REGISTRADO no sidecar de cada ⑦ (`origem_precisao`) para a auditoria.

INVARIANTE ⑦×③ (aprendido na prova deste cartão, e agora conferido pelo
`--check`): **o ND final tem de estar NA ③**. Um runner que escreva a ⑦ a
partir de pontos que a ③ não registrou — o caso clássico é usar a PROLE da
última geração em vez da população gravada — produz uma camada que ninguém
consegue reconstituir nem auditar, e para o e103 (cuja ③ é a única fonte) o
retroativo simplesmente avaliaria outro conjunto. O erro é silencioso: as duas
camadas ficam bem-formadas e o run passa em todo o resto.

[T15.7b/D102.9 — "Processo B"] RAMO DDMOP7. Para problemas em
`experiment.PROBLEMAS_FINAL_POS_HOC` (avaliação real exige processo EXTERNO —
o DDMOP7.p via MATLAB Engine), os runners offline NÃO avaliam a ⑦ inline: eles
a DECLARAM no ⑤ (`params.nd_final`) e ESTE script a grava pós-hoc — o MESMO
mecanismo retroativo do e103, mesma fonte (③, última geração), MESMO contrato
DI-08. A única diferença é o avaliador: em vez de `problems.py`, o motor da
ponte (`src/ddmop7_bridge._MotorMatlab`, fatiamento ≤64) sob o guard de 600
chamadas/processo (D88.5). Contabilidade NÃO se aplica (a ⑦ é MEDIÇÃO
pós-hoc, fora do orçamento — nenhum FEBudget, nenhuma dedup). A máquina
precisa de matlab.engine (ex.: o venv `env_matlab_engine`, ou uma VM
provisionada) — sem ele o script FALHA com mensagem acionável. O `--check`
re-avalia pelo MESMO caminho (custa |⑦|×~6 s por célula numa máquina com
Engine). Os gates não mudam de veredito: ⑦ ausente segue vermelha até este
script rodar — exatamente o estado do e103 hoje.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from src import naming  # noqa: E402
from src import experiment as _exp  # noqa: E402
from src import problems as _problems  # noqa: E402
from src import standalone_harness as sh  # noqa: E402

#: Regimes da ③ que NÃO são candidatos da busca (§17.2.2). O bloco de sonda
#: são os 2000 pontos da régua fixa — nunca o front do algoritmo.
_NAO_BUSCA = frozenset({"sonda"})


def read_final_candidates(exp: str, alg: str, problema: str, semente, *,
                          data_root: str = naming.DEFAULT_DATA_ROOT) -> dict:
    """Extrai da ③ os decs da ÚLTIMA geração da BUSCA (o front no surrogate).

    Retorna `{X, geracao, linhas, solution_ids, D, M, n_total, n_sonda}` —
    `X` float64 (promovido do float32 gravado; ver o caveat no topo), `linhas`
    = a posição de cada candidato dentro do bloco daquela geração (o link
    posicional à ③), `solution_ids` = o `real_solution_id` quando o ponto era
    um membro do dataset (nulo na maioria).
    """
    import pyarrow.parquet as pq
    path = naming.layer_path(exp, alg, problema, semente, "surrogate",
                             data_root=data_root)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"camada ③ ausente p/ {alg}/{problema}/{semente}: {path}. O "
            f"`__final` é derivado dela — rode o algoritmo antes. "
            f"Pára-e-loga (D81).")
    tbl = pq.read_table(path)
    n_total = tbl.num_rows
    cols = set(tbl.column_names)
    D = sum(1 for c in cols if len(c) > 1 and c[0] == "x" and c[1:].isdigit())
    M = sum(1 for c in cols if c.startswith("mu_") and c[3:].isdigit())
    if not D:
        raise RuntimeError(f"③ de {alg}/{problema}/{semente} sem colunas x*.")

    regime = (np.asarray(tbl.column("regime").to_pylist(), dtype=object)
              if "regime" in cols else np.array(["online"] * n_total,
                                                dtype=object))
    # geracao=NULL nas linhas de sonda offline (DI-16.12) — sentinela -1 evita
    # o RuntimeWarning de cast NaN→int64; só ger[busca] é consumido adiante.
    ger = np.array([-1 if g is None else int(g)
                    for g in tbl.column("geracao").to_pylist()], dtype=np.int64)
    busca = np.array([r not in _NAO_BUSCA for r in regime], dtype=bool)
    n_sonda = int((~busca).sum())
    if not busca.any():
        raise RuntimeError(
            f"③ de {alg}/{problema}/{semente} só tem linhas de sonda — não há "
            f"front de busca para avaliar. Pára-e-loga (D81).")

    g_final = int(ger[busca].max())
    sel = busca & (ger == g_final)

    # [DI-41] Config MULTI-SURROGATE (e103/IBEA-MS): a ③ grava UMA LINHA POR
    # (membro × modelo) — 100 membros × {Kriging-DACE, RBFN} = 200 linhas. Sem
    # este filtro a ⑦ nascia com o DOBRO de linhas (cada ponto avaliado 2× na f
    # real), inflando `n_final` e ZERANDO o `spacing` (duplicatas têm distância
    # 0). Filtra por UM modelo (o 1º na ordem da ③) — NUNCA por X: membros
    # legitimamente coincidentes (população convergida) DEVEM ser preservados.
    # Config de modelo único (b5r/b5m/c311/moead_media/treed_media) é no-op.
    if "modelo_flag" in cols:
        flags = np.asarray(tbl.column("modelo_flag").to_pylist(), dtype=object)
        distintos = list(dict.fromkeys(flags[sel].tolist()))
        if len(distintos) > 1:
            sel = sel & (flags == distintos[0])

    idx = np.flatnonzero(sel)

    X = np.column_stack([
        np.asarray(tbl.column(f"x{j}"), dtype=np.float64)[idx]
        for j in range(D)])
    sids = (np.asarray(tbl.column("real_solution_id").to_pylist(), dtype=object)[idx]
            if "real_solution_id" in cols else np.array([None] * len(idx),
                                                        dtype=object))
    return {"X": X, "geracao": g_final,
            "linhas": np.arange(len(idx), dtype=np.int64),
            "solution_ids": list(sids), "D": D, "M": M,
            "n_total": n_total, "n_sonda": n_sonda}


def _motor_pos_hoc():
    """[T15.7b/D102.9] O motor do ramo pós-hoc do DDMOP7 — a MATLAB Engine da
    ponte oficial. Função-fábrica DE PROPÓSITO: os testes a substituem por um
    motor determinístico; produção SEMPRE abre a Engine real (não há knob de
    mock aqui — uma ⑦ de mentira seria silenciosa e fatal)."""
    _MSG_SEM_ENGINE = (
        "matlab.engine ausente neste interpretador — o ramo pós-hoc do "
        "DDMOP7 (D102.9/Processo B) avalia no DDMOP7.p via MATLAB Engine. "
        "Rode este script num interpretador com matlab.engine (ex.: "
        "/Users/gmello/Documents/python_venvs/env_matlab_engine/bin/python "
        "no Mac, ou o venv provisionado da VM) e com UA_DD_SAEA_DDMOP_DIR "
        "apontando para .../DDMOP_Exp/Problems. Pára-e-loga (D81).")
    try:
        import matlab.engine  # noqa: F401 — só detecção; o motor importa de novo
    except ImportError as exc:
        raise RuntimeError(_MSG_SEM_ENGINE) from exc
    from src import ddmop7_bridge as B
    try:
        return B._MotorMatlab(None)      # resolve por env → default (T15.7)
    except ImportError as exc:
        # [medido na suíte] o qpots (e81, tsemo_runner.py) registra um
        # matlab.engine FALSO cujo start_matlab levanta ImportError — a
        # detecção acima passa e o erro cru vazaria aqui. Mesmo veredito.
        raise RuntimeError(_MSG_SEM_ENGINE) from exc


def _avalia_pos_hoc(problema: str, X: np.ndarray) -> np.ndarray:
    """F real de um problema PROCESSO-EXTERNO (hoje: DDMOP7) — medição
    pós-hoc, FORA de qualquer contabilidade (não é busca: nenhum FEBudget,
    nenhuma dedup). Ficam os guards que não são contabilidade: teto de 600
    chamadas de 'value' por processo (D88.5) e forma/finito (D81). A ponte
    fatia em ≤64 pontos/chamada (watchdog D60a)."""
    from src import ddmop7_bridge as B
    if X.shape[0] > B.P_CODE_CAP:
        raise RuntimeError(
            f"⑦ com {X.shape[0]} pontos passaria o teto de {B.P_CODE_CAP} "
            f"chamadas do DDMOP7.p num processo (D88.5) — |ND| offline "
            f"esperado é ~10²; isto indica ③ corrompida. Pára-e-loga (D81).")
    motor = _motor_pos_hoc()
    try:
        F = np.atleast_2d(np.asarray(motor.avalia(X), dtype=np.float64))
    finally:
        motor.encerra()                              # D86 — inclusive em falha
    if F.shape != (X.shape[0], 2):
        raise RuntimeError(f"DDMOP7('value') devolveu {F.shape}, esperado "
                           f"({X.shape[0]}, 2) — pára-e-loga (D81).")
    if not np.all(np.isfinite(F)):
        raise RuntimeError("DDMOP7('value') devolveu não-finito — D81.")
    return F


def evaluate_final(problema: str, X: np.ndarray) -> np.ndarray:
    """Avalia `X` na função VERDADEIRA, em float64, FORA do orçamento.

    Ponto único do §11 ("a única chamada real do offline"). Usa o
    `problems.py` canônico — o mesmo módulo que gerou o `F` do dataset (D90) e
    o gabarito da sonda —, então o `f` desta camada é comparável com tudo o
    mais sem nenhuma conversão. Nenhum `FEBudget` é envolvido: por construção,
    é impossível esta chamada consumir orçamento.

    [T15.7b/D102.9] Problema em `PROBLEMAS_FINAL_POS_HOC` (DDMOP7): a MESMA
    porta, mas o `f` sai do `.p` oficial via `_avalia_pos_hoc` (Engine +
    guard 600). O check de bounds/clip continua o daqui — a casca desligada
    dá xl/xu de graça (sem Engine).
    """
    prob = _exp._instantiate_problem(problema)
    X = np.ascontiguousarray(X, dtype=np.float64)
    xl = np.asarray(prob.xl, dtype=np.float64)
    xu = np.asarray(prob.xu, dtype=np.float64)

    # A tolerância tem de acompanhar a PRECISÃO DE ARMAZENAMENTO, não ser uma
    # constante. Todo X que chega aqui passou por uma camada float32 (D53): a
    # ③ no caminho retroativo, a própria ⑦ no `check_final`. Perto de 1.0 o
    # quantum do float32 é ~1,2e-7 — 100× MAIOR que um 1e-9 fixo. E clipar no
    # bound é comportamento rotineiro de MOEA (o próprio `run_stubr3` faz).
    # Medido: com 1e-9, MMF11_L (xl=0.1, xu=1.1 — o único dos 25 canônicos com
    # bounds não representáveis em float32) reprovava a própria ⑦ em 8 de 29
    # sementes. `tol` abaixo é ~8 ULPs float32 da escala do bound.
    escala = np.maximum(np.abs(xl), np.abs(xu)).astype(np.float32)
    tol = np.maximum(1e-9, 8.0 * np.spacing(escala).astype(np.float64))
    fora = (X < xl - tol).any(axis=1) | (X > xu + tol).any(axis=1)
    if fora.any():
        pior = float(np.max(np.maximum(xl - X, X - xu)))
        raise RuntimeError(
            f"{problema}: {int(fora.sum())} dec(s) do ND final FORA dos "
            f"bounds nativos (excesso máx {pior:.3g} > tol {float(tol.max()):.3g})"
            f" — o algoritmo devolveu solução inválida (ou a ③ está "
            f"corrompida). Pára-e-loga (D81).")
    # Violações DENTRO da tolerância são ruído de armazenamento, não do
    # algoritmo: clipamos para que o problema não receba um X fora do domínio.
    X = np.clip(X, xl, xu)
    if problema in _exp.PROBLEMAS_FINAL_POS_HOC:     # [T15.7b/D102.9]
        return _avalia_pos_hoc(problema, X)
    return np.ascontiguousarray(
        _problems.evaluate_problem(prob, X), dtype=np.float64)


def final_eval_run(exp: str, alg: str, problema: str, semente, *,
                   data_root: str = naming.DEFAULT_DATA_ROOT,
                   force: bool = False) -> dict:
    """Avalia e grava a ⑦ de UM run offline. Idempotente (ver `force`)."""
    out_path = naming.final_path(exp, alg, problema, semente,
                                 data_root=data_root)
    if os.path.exists(out_path) and not force:
        return {"status": "skip", "path": out_path,
                "motivo": "__final já existe (use --force para reescrever)"}

    cand = read_final_candidates(exp, alg, problema, semente,
                                 data_root=data_root)
    F = evaluate_final(problema, cand["X"])
    # [T15.7b] Certidão HONESTA do avaliador: no ramo pós-hoc o f NÃO vem do
    # problems.py — o sidecar tem de dizer (auditoria da procedência).
    pos_hoc = problema in _exp.PROBLEMAS_FINAL_POS_HOC
    avaliador = ("DDMOP7.p oficial via src/ddmop7_bridge (MATLAB Engine) — "
                 "⑦ POS-HOC, D102.9/Processo B" if pos_hoc else None)
    # `nd_pos_real` fica a cargo do `write_final`, que o computa sobre a vista
    # float32 PERSISTIDA — a mesma que o `--check` relê. Computá-lo aqui, no
    # float64 cru, criava a assimetria que reprovava uma ⑦ correta.
    path = sh.write_final(
        exp, alg, problema, semente, cand["X"], F,
        origem_solution_id=cand["solution_ids"],
        origem_geracao=[cand["geracao"]] * F.shape[0],
        origem_linha=cand["linhas"],
        origem_precisao="float32 (decs lidos da ③ — ver caveat do módulo)",
        avaliador=avaliador,
        data_root=data_root)
    with open(_sidecar_path(out_path), encoding="utf-8") as fh:
        side = json.load(fh)
    return {"status": "ok", "path": path, "sidecar": side,
            "n_final": int(F.shape[0]), "n_nd": int(side["n_nd_pos_real"]),
            "geracao": int(cand["geracao"]), "n_sonda_ignorada": cand["n_sonda"]}


def _sidecar_path(final_parquet_path: str) -> str:
    return final_parquet_path[:-len(".parquet")] + ".manifest.json"


def check_final(exp: str, alg: str, problema: str, semente, *,
                data_root: str = naming.DEFAULT_DATA_ROOT) -> tuple:
    """Verifica presença + CONSISTÊNCIA da ⑦ (o check do gate offline, DI-08).

    Consistência = re-avaliar os `x` gravados na ⑦ e exigir que o `f` gravado
    seja reproduzido (dentro da tolerância do float32 em que ele foi gravado).
    É a prova de que o `f` da camada é mesmo o f VERDADEIRO daquele `x`, e não
    um resíduo do surrogate — exatamente o que a DI-08 quer garantir.
    """
    import pyarrow.parquet as pq
    p = naming.final_path(exp, alg, problema, semente, data_root=data_root)
    if not os.path.exists(p):
        return False, f"camada ⑦ ausente: {p}"
    tbl = pq.read_table(p)
    cn = set(tbl.column_names)
    D = sum(1 for c in cn if len(c) > 1 and c[0] == "x" and c[1:].isdigit())
    M = sum(1 for c in cn if len(c) > 1 and c[0] == "f" and c[1:].isdigit())
    if not (D and M):
        return False, f"⑦ sem colunas x*/f* (obtido {sorted(cn)})"
    if tbl.num_rows == 0:
        return False, "⑦ vazia (o ND final tem de ter ao menos 1 ponto — §11)"
    exp_sch = sh.final_schema(D, M)
    got = pq.read_schema(p).remove_metadata()
    if not got.equals(exp_sch, check_metadata=False):
        return False, (f"schema da ⑦ diverge do DI-08 (esperado "
                       f"{exp_sch.names}, obtido {got.names})")
    X = np.column_stack([np.asarray(tbl.column(f"x{j}"), dtype=np.float64)
                         for j in range(D)])
    F = np.column_stack([np.asarray(tbl.column(f"f{j}"), dtype=np.float64)
                         for j in range(M)])
    try:
        F_re = evaluate_final(problema, X).astype(np.float32).astype(np.float64)
    except RuntimeError as exc:
        # [T15.10 · achado nº 15 da revisão / B-07] NÃO CONSEGUIR MEDIR não é
        # REPROVAR: sem matlab.engine/.p nesta máquina, a ⑦ do DDMOP7 é
        # NÃO-AFERÍVEL aqui (⛔), nunca vermelho — pintar incapacidade de
        # medição como reprovação de dado mascara vermelhos verdadeiros.
        if "matlab.engine" in str(exc) or "DDMOP7.p" in str(exc):
            return None, (f"⑦: NÃO-AFERÍVEL nesta máquina — {exc}")
        return False, f"⑦: não foi possível reavaliar o X gravado ({exc})"
    except Exception as exc:  # noqa: BLE001
        # Um check TEM de devolver veredito, nunca estourar: `check_r3_00` não
        # protege a chamada, e um traceback aqui abortava o gate ANTES dos
        # checks de manifesto/pinning/subprocess (eles nunca rodavam).
        return False, f"⑦: não foi possível reavaliar o X gravado ({exc})"
    # [B-14/G-5] `rtol=1e-4`, não 1e-5. A tolerância antiga não modelava a
    # AMPLIFICAÇÃO do float32 (D53) pelo número de condição do problema e deu
    # 4 FALSOS-VERMELHOS medidos na s42, com desvio RELATIVO 1,5e-5–7,3e-5:
    # `off/c311/DTLZ3` 7,3e-5 (abs 6,10e-4; cond ~10³ por `g` com 100·Σcos(20πx)) ·
    # `off/c311/DTLZ4` 4,9e-5 (α=100 ⇒ x^100) · `sweep-big-mvns/c311/WFG9` 1,9e-5 ·
    # `sweep-medium-mvns/b5m/WFG9` 1,5e-5. Mecanismo provado: ULP-float32
    # (~6e-8 rel em x) × nº de condição — recomputar com e sem clip nos bounds dá
    # o MESMO desvio. Em 30 sementes seriam ~120 falsos-vermelhos, e cada triagem
    # manual é uma chance de mascarar um vermelho VERDADEIRO. O controle negativo
    # continua reprovando: a ⑦ de 200 linhas de `swap_medium-lhs/e103/ZDT4`.
    # Reporta-se o desvio RELATIVO (o absoluto sozinho não diz nada de escala).
    if not np.allclose(F, F_re, rtol=1e-4, atol=1e-6, equal_nan=True):
        pior = float(np.nanmax(np.abs(F - F_re)))
        den = np.maximum(np.abs(F_re), 1e-30)
        pior_rel = float(np.nanmax(np.abs(F - F_re) / den))
        return False, (f"⑦ INCONSISTENTE: o f gravado não reproduz "
                       f"problems.py (desvio relativo máx {pior_rel:.3g}; "
                       f"absoluto {pior:.3g})")
    nd = np.asarray(tbl.column("nd_pos_real").to_pylist(), dtype=bool)
    nd_re = np.zeros(len(nd), dtype=bool)
    nd_re[list(int(i) for i in _problems._nds_filter(F))] = True
    if not np.array_equal(nd, nd_re):
        return False, (f"⑦: nd_pos_real diverge do filtro recomputado "
                       f"({int(nd.sum())} vs {int(nd_re.sum())})")

    # ── INVARIANTE ⑦×③: o ND final tem de estar NA ③ ────────────────────
    # Sem isto, a ⑦ pode ser escrita a partir de pontos que a ③ nunca
    # registrou (ex.: a PROLE da última geração, em vez da população que foi
    # gravada). O erro é silencioso e fatal: para o e103 — já executado em
    # MATLAB — a ③ é a ÚNICA fonte, então uma ⑦ irreconstituível não é
    # auditável nem reproduzível. A comparação é em float32 porque é nessa
    # precisão que a ③ guarda o X (D53).
    try:
        cand = read_final_candidates(exp, alg, problema, semente,
                                     data_root=data_root)
    except Exception as exc:  # noqa: BLE001
        return False, f"⑦: não foi possível reler a ③ p/ conferir ({exc})"
    # A conferência é POR `origem_linha` — o link que a própria ⑦ declara —, e
    # não por igualdade posicional da tabela inteira. A invariante que o
    # contrato exige é "cada ponto da ⑦ ESTÁ na ③", não "a ⑦ é a ③ na mesma
    # ordem e cardinalidade": um config que devolva só o subconjunto ND, ou em
    # outra ordem, é legítimo e não pode levar vermelho. O bug-alvo (a PROLE da
    # última geração, cujos X não aparecem em lugar nenhum da ③) continua morto.
    ref = cand["X"].astype(np.float32).astype(np.float64)
    linhas = np.asarray(tbl.column("origem_linha").to_pylist(), dtype=np.int64)
    gers = np.asarray(tbl.column("origem_geracao").to_pylist(), dtype=np.int64)
    if (linhas < 0).any() or (linhas >= ref.shape[0]).any():
        return False, (f"⑦ IRRECONSTITUÍVEL: `origem_linha` fora do intervalo "
                       f"[0,{ref.shape[0]}) da geração {cand['geracao']} da ③ "
                       f"— a ⑦ aponta para linhas que não existem. D81.")
    fora_ger = gers != int(cand["geracao"])
    if fora_ger.any():
        return False, (f"⑦ IRRECONSTITUÍVEL: {int(fora_ger.sum())} linha(s) "
                       f"com `origem_geracao` != {cand['geracao']} (a última "
                       f"geração da busca na ③). D81.")
    if not np.array_equal(X, ref[linhas]):
        pior = float(np.abs(X - ref[linhas]).max())
        return False, (f"⑦ IRRECONSTITUÍVEL: o X da ⑦ não bate com a linha "
                       f"que ela mesma aponta na ③ (maior desvio {pior:.3g}) "
                       f"— a ⑦ veio de pontos que a ③ não registrou. D81.")

    # A certidão (`origem_precisao`) é obrigatória: sem ela a auditoria não
    # sabe se os decs vieram em float64 (nativo) ou float32 (retroativo).
    spath = _sidecar_path(p)
    if not os.path.exists(spath):
        return False, f"⑦ sem sidecar de procedência: {os.path.basename(spath)}"
    with open(spath, encoding="utf-8") as fh:
        side = json.load(fh)
    if not side.get("origem_precisao"):
        return False, "⑦: sidecar sem `origem_precisao` (procedência dos decs)"

    return True, (f"⑦ presente e consistente ({tbl.num_rows} finais, "
                  f"{int(nd.sum())} ND pós-real, f reproduz problems.py, "
                  f"X reconstituível da ③ ger {cand['geracao']} via "
                  f"origem_linha; procedência: {side['origem_precisao']})")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Avaliador pós-hoc do ND final offline (DI-08 / camada ⑦)")
    ap.add_argument("--exp", default="off")
    ap.add_argument("--alg", required=True)
    ap.add_argument("--problema", required=True)
    ap.add_argument("--semente", default="0")
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--force", action="store_true",
                    help="reescreve um __final já existente")
    ap.add_argument("--check", action="store_true",
                    help="só verifica presença+consistência (não escreve)")
    ap.add_argument("--all-seeds", action="store_true",
                    help="itera as 30 sementes {0..28, 42}")
    a = ap.parse_args()

    dr = a.data_root or os.path.join(ROOT, "data")
    # Guarda de escopo: a ⑦ só existe no regime offline (DI-08). O STUB do
    # R3-00 entra por ser justamente a prova de encanamento desta camada.
    permitidos = sh.OFFLINE_CONFIGS + (sh.STUB_ALG,)
    if a.alg not in permitidos:
        print(f"  [FAIL] {a.alg!r} não é config OFFLINE. A camada ⑦ existe só "
              f"nos 5 do regime offline: {list(sh.OFFLINE_CONFIGS)} (DI-08).")
        return 2

    sementes = (list(range(29)) + [42]) if a.all_seeds else [int(a.semente)]
    falhou = False
    inconclusivo = False
    for s in sementes:
        try:
            if a.check:
                ok, msg = check_final(a.exp, a.alg, a.problema, s, data_root=dr)
                # [T15.10/B-07] ok=None = NÃO-AFERÍVEL nesta máquina (sem
                # Engine/.p) — exit 2, nunca vermelho (DI-41 aceita exit 2).
                if ok is None:
                    mark = "N/AF"
                    inconclusivo = True
                else:
                    mark = "OK  " if ok else "FAIL"
                    falhou = falhou or not ok
            else:
                r = final_eval_run(a.exp, a.alg, a.problema, s, data_root=dr,
                                   force=a.force)
                ok = r["status"] in ("ok", "skip")
                mark = "OK  " if r["status"] == "ok" else "SKIP"
                msg = (r.get("motivo") or
                       f"{r['n_final']} finais avaliados (ger {r['geracao']}), "
                       f"{r['n_nd']} ND pós-real → {os.path.basename(r['path'])}")
        except Exception as exc:  # noqa: BLE001 — pára-e-loga com diagnóstico
            mark, msg, falhou = "FAIL", f"{type(exc).__name__}: {exc}", True
        print(f"  [{mark}] {a.alg}/{a.problema}/{s}: {msg}")
    if falhou:
        print("\n  >>> VERMELHO — pára-e-loga (D81)")
        return 1
    if inconclusivo:
        print("\n  >>> NÃO-AFERÍVEL nesta máquina (B-07) — rode onde houver "
              "matlab.engine + DDMOP7.p")
        return 2
    print("\n  >>> VERDE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
