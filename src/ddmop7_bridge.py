#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ddmop7_bridge.py  --  D88.5/D102.5: o DDMOP7 e avaliado em MATLAB (caixa-preta)

[T15.7] Transplantado de `mestrado2/_real_experiments/ddmop7_bridge.py` (a
versao com os DOIS fixes MEDIDOS de 2026-08-13: init no setup do motor, B-26;
fatiamento <=64 pontos/chamada, B-27), com tres adaptacoes declaradas:
  (a) o DoE vem do ARTEFATO parquet via o load_doe oficial (D63 — o MESMO
      arquivo das outras rotas); a rota por CSV congelado vira FALLBACK com
      aviso (util no venv da Engine, que nao tem pyarrow);
  (b) `problems_dir` resolve por `UA_DD_SAEA_DDMOP_DIR` (env) -> default
      `~/DDMOP/DDMOP_Exp/Problems`;
  (c) o import de matlab.engine permanece TARDIO (dentro do motor).

POR QUE ESTE ARQUIVO EXISTE (D88.5). O `DDMOP7.p` e P-code ofuscado. O paper
fixa f1 ("the ratio of nonzero weights"), f2 ("the classification error rate")
e a arquitetura (14 x 1 x 1), mas NAO da o limiar eps de "peso nulo", nem a
ativacao, nem a normalizacao das features. Portar exigiria ESCOLHER tres
definicoes ausentes -- exatamente o que o D81 proibe ("definicao ausente =>
pare e pergunte; nao improvise"). A saida fiel e nao portar: chama-se o .p.

Este e o UNICO problema do grid que quebra a arquitetura A2 (problems.py como
fonte unica em Python). RE21 e ESTOQUE40 seguem em A2. O desvio esta declarado
no D102.5 e nao se estende a mais nada.

DUAS ROTAS DE AVALIACAO (so a primeira precisa deste arquivo):
  * Algoritmos PYTHON (R2/R3)  : Python -> MATLAB Engine -> DDMOP7('value',X)
                                 <- e esta classe, via a casca problems.DDMOP7.
  * Algoritmos MATLAB (R1)     : o harness chama DDMOP7('value',X) DIRETO, no
                                 mesmo processo -- ver `src/ddmop7_value_local.m`.
                                 A ponte Python nao entra; nao ha ida-e-volta.

CONTABILIDADE — UM CONTADOR SO (D89, cartao T15.7 §1.3). Dois modos:
  * `contabilidade='externa'` (o modo dos HARNESSES R2/R3 — default da casca
    `problems.DDMOP7.bind`): esta classe e um AVALIADOR CRU. `_evaluate`/
    `avalia` NAO contam FE, NAO deduplicam, NAO gravam catalogo e NUNCA
    levantam BudgetExhausted — o FEBudget do harness e a UNICA autoridade de
    orcamento/dedup/camada ①. Ficam SO os guards que nao sao contabilidade:
    forma/finito (D81) e o teto de 600 chamadas do proprio .p (D88.5).
  * `contabilidade='propria'` (default DESTA classe — modo standalone/smoke):
    o comportamento historico completo (contador de FE, hard-stop exato em
    526, dedup D57, catalogo ①, watchdogs D60) — para exercitar o arnes fora
    dos harnesses. NUNCA usar sob um FEBudget: seriam dois contadores.

INVARIANTES HONRADOS (nenhum e negociado aqui):
  D63  DoE carregado bit-a-bit do artefato congelado (186 = 11D-1)
  D21/D61  (modo 'propria') hard-stop EXATO em 31D-1 = 526
  D57  (modo 'propria') solution_id = identidade da SOLUCAO; cache-hit = 0 FE
  D53  export float32 SEM arredondamento
  D79  1 run = 1 core -> maxNumCompThreads(1) do lado MATLAB
  D60  (modo 'propria') watchdogs; na R2 os guards do harness governam
  D86  higiene: encerra() fecha a Engine, sem estado retido
  D88.5  UM processo MATLAB por run (o .p aborta acima de 600 chamadas de
         'value'; o guard `chamadas_p` PARA antes, em qualquer modo)

MODO MOCK. Sem `matlab.engine` instalado, a classe roda com `engine="mock"`:
um avaliador em Python que NAO e fiel ao .p e existe apenas para exercitar o
arnes. Ele NUNCA deve ser usado para produzir numero de tese -- todo artefato
gravado em modo mock leva `engine="mock"` no manifesto.
"""
from __future__ import annotations

import gc
import json
import os
import threading
import time
import warnings
from dataclasses import dataclass, field

import numpy as np

try:                                             # pymoo e opcional para o mock
    from pymoo.core.problem import Problem as _PymooProblem
except Exception:                                # pragma: no cover
    _PymooProblem = object

D = 17
DOE_N = 11 * D - 1                               # 186
MAX_FE = 31 * D - 1                              # 526  (D21, hard-stop exato)
P_CODE_CAP = 600                                 # teto interno do DDMOP7.p

#: Raiz do repo (este arquivo vive em src/).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: CSV congelado dos 30 sorteios (D88.1) — a rota FALLBACK do DoE (aviso).
CSV_DOE_CONGELADO = os.path.join(
    _ROOT, "data", "real_sources", "ddmop7",
    "doe_ddmop7_online_30sementes.csv")


class BudgetExhausted(Exception):
    """D61: excecao canonica do hard-stop no lado Python (modo 'propria')."""


class BridgeTimeout(Exception):
    """D60(a): a chamada da ponte pendurou (IPC/sidecar)."""


class RunTimeout(Exception):
    """D60(b): o run estourou o wall-clock."""


class StalledRun(Exception):
    """D60(c): N iteracoes consecutivas sem consumir FE."""


#: [T15.12 · REAL-2.17/D102.17 — ZONA MORTA na codificacao, 2026-08-15]
#: O front do DDMOP7 exige pesos EXATAMENTE zero (6-13 dos 17), e aquisicao
#: continua nunca produz zero exato — MEDIDO no laudo de fidelidade: 0/340
#: propostas da busca do c149 com algum zero (f1=1.0 em todas) vs 320/340 do
#: GA (que herda zeros do DoE por crossover). A busca surrogate contribuia
#: ZERO pontos ao front. Solucao do autor (15/08): codificacao declarada
#: genotipo->fenotipo, |x_i| < TAU => 0, aplicada IDENTICAMENTE aos 21
#: configs, SOMENTE aos pontos propostos pela busca (pos-DoE): aplicar ao DoE
#: congelado zeraria 50,1% das coordenadas nao-zero e mudaria 99,2% dos
#: pontos (MEDIDO 15/08 nos 30 blocos) — o DoE ja e esparso por construcao
#: do init. TAU=0,5: nnz ~ Binomial(17; 0,5), 83,5% das propostas na faixa
#: do front (nnz 2-10, com Delta=k-nnz=+1/+2 medido nessa regiao). A (1)
#: grava o x PROPOSTO; o efetivo e reconstrutivel deterministicamente por
#: esta funcao + o tau declarado no (5) (params.zona_morta). O PAR desta
#: constante vive em src/ddmop7_value_local.m (rota R1) — teste de paridade
#: em tests/test_t15_zona_morta.py. Gate de validacao: smoke c149 s0 na vm1
#: (ND da busca deve sair de 0/340) ANTES do disparo das 1.890.
TAU_ZONA_MORTA = 0.5
N_DOE_ONLINE = 11 * D - 1                        # 186 (o DoE fica CRU)


def zona_morta(X: np.ndarray, tau: float = TAU_ZONA_MORTA) -> np.ndarray:
    """A codificacao D102.17: coordenada com |x| < tau vira EXATAMENTE 0."""
    X = np.asarray(X, dtype=np.float64)
    return np.where(np.abs(X) < tau, 0.0, X)


#: [T15.10 · O-18 MEDIDO 2026-08-14] `start_matlab` NAO tem prazo interno: o
#: Processo A ficou 37 min com o MATLAB de pe e OCIOSO (run loop vazio) e o
#: Python dormindo no poll do handshake — slot morto para sempre, sem
#: excecao, sem manifesto. A partida sadia na MESMA maquina, minutos depois,
#: levou 10,6 s (probe) — jitter transitorio, nao defeito. 300 s = ~28x a
#: partida medida; estourou ⇒ BridgeTimeout, run failed, processo novo
#: (a Engine orfa e coberta pelo parar_tudo/pkill do plano3s).
TIMEOUT_PARTIDA = 300.0


def _boot_com_prazo(fn, prazo: float, rotulo: str):
    """Roda `fn()` numa thread-daemon com prazo; estourou ⇒ BridgeTimeout.

    E o watchdog da PARTIDA (O-18): as chamadas de avaliacao ja tem o d60a
    (`background=True` + poll), mas o boot (`start_matlab` + cd + init) e
    sincrono e sem prazo na API da MathWorks. A thread abandonada e daemon —
    nao segura o exit do processo; um MATLAB orfao pode sobrar (aceito,
    ver TIMEOUT_PARTIDA)."""
    caixa: dict = {}

    def _alvo():
        try:
            caixa["ok"] = fn()
        except BaseException as exc:  # noqa: BLE001 — atravessa a thread
            caixa["exc"] = exc

    th = threading.Thread(target=_alvo, daemon=True, name="ddmop7-boot")
    th.start()
    th.join(prazo)
    if th.is_alive():
        raise BridgeTimeout(
            f"{rotulo} nao completou em {prazo:.0f}s (O-18/T15.10) — "
            f"handshake da Engine pendurado; processo deve morrer e "
            f"tentar de novo em processo novo (D88.5)")
    if "exc" in caixa:
        raise caixa["exc"]
    return caixa["ok"]


# ═══════════════════════════════════════════════════════════════════════════
#  Pasta do .p (adaptacao (b) do T15.7)
# ═══════════════════════════════════════════════════════════════════════════

def resolve_problems_dir(problems_dir: str | None = None) -> str:
    """Resolve a pasta do `DDMOP7.p`: argumento explicito ->
    `UA_DD_SAEA_DDMOP_DIR` (env) -> default `~/DDMOP/DDMOP_Exp/Problems`.
    So resolve o CAMINHO — a validacao (DDMOP_Plat, presenca do .p) e do
    motor, que e quem abre a Engine."""
    if problems_dir:
        return os.path.expanduser(problems_dir)
    env = os.environ.get("UA_DD_SAEA_DDMOP_DIR", "").strip()
    if env:
        return os.path.expanduser(env)
    return os.path.expanduser(os.path.join("~", "DDMOP", "DDMOP_Exp",
                                           "Problems"))


# ═══════════════════════════════════════════════════════════════════════════
#  DoE congelado (D88.1 + D63) — artefato parquet PRIMEIRO, CSV como fallback
# ═══════════════════════════════════════════════════════════════════════════

def carrega_doe(semente: int, csv_path: str) -> np.ndarray:
    """
    Rota FALLBACK: le o DoE oficial do DDMOP7 do CSV congelado -- os 30
    sorteios de DDMOP7('init') gravados com %.17g (D88.1).

    Formato long: semente, ponto, x1..x17.  Retorna (186, 17) float64.
    A leitura e bit-a-bit: %.17g e o round-trip exato de um double IEEE-754,
    entao o que sai daqui e o mesmo bit que o MATLAB sorteou (D63).
    """
    M = np.loadtxt(csv_path, delimiter=",", skiprows=1)
    sel = M[M[:, 0] == semente]
    if len(sel) == 0:
        raise FileNotFoundError(
            f"semente {semente} ausente em {csv_path} (D88.1)")
    X = sel[np.argsort(sel[:, 1], kind="stable"), 2:]
    _valida_doe(X, semente)
    return np.ascontiguousarray(X, dtype=np.float64)


def _valida_doe(X: np.ndarray, semente: int) -> None:
    if X.shape != (DOE_N, D):
        raise ValueError(f"DoE da semente {semente} tem {X.shape}, "
                         f"esperado ({DOE_N}, {D}) = 11D-1 (D88.1)")
    if not np.all((X >= -1.0) & (X <= 1.0)):
        raise ValueError("DoE fora dos bounds [-1,1]^17 confirmados pelo oraculo")


def carrega_doe_oficial(semente: int, *, data_root: str | None = None,
                        csv_path: str | None = None) -> np.ndarray:
    """[T15.7 §1.1(a)] O DoE pela via OFICIAL: o artefato parquet de
    `data/doe/DDMOP7/` via `standalone_harness.load_doe` (D63 — o MESMO
    arquivo e o MESMO leitor das outras rotas, hash conferido no sidecar).

    FALLBACK (com aviso): se o artefato nao puder ser lido — tipicamente o
    venv da MATLAB Engine, que nao tem pyarrow — cai no CSV congelado
    (bit-identico por construcao, provado em tests/test_t15_doe_ddmop7). Se o
    sidecar do artefato estiver legivel, o hash do X decodificado do CSV e
    conferido contra ele MESMO no fallback (a disciplina D63 nao relaxa).
    """
    err_artefato: Exception | None = None
    try:
        from src.standalone_harness import load_doe as _load_doe
        kw = {} if data_root is None else {"data_root": data_root}
        X = _load_doe("DDMOP7", int(semente), **kw)["X"]
        _valida_doe(X, semente)
        return X
    except Exception as e:                                    # noqa: BLE001
        err_artefato = e

    csv_path = csv_path or CSV_DOE_CONGELADO
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"DoE do DDMOP7 (semente {semente}): nem o artefato parquet "
            f"({type(err_artefato).__name__}: {err_artefato}) nem o CSV "
            f"congelado ({csv_path}) — pára-e-loga (D81/D63).")
    warnings.warn(
        f"DoE do DDMOP7 (semente {semente}) carregado pela rota FALLBACK "
        f"(CSV congelado {os.path.basename(csv_path)}): o artefato parquet "
        f"nao pode ser lido ({type(err_artefato).__name__}: {err_artefato}). "
        f"As duas rotas sao bit-identicas por construcao (D63/D88.1).",
        RuntimeWarning, stacklevel=2)
    X = carrega_doe(int(semente), csv_path)
    _confere_hash_sidecar(X, semente, data_root)
    return X


def _confere_hash_sidecar(X: np.ndarray, semente: int,
                          data_root: str | None) -> None:
    """Mesmo no fallback CSV, se o SIDECAR do artefato estiver legivel (json
    puro — nao precisa de pyarrow), confere o sha256 do array decodificado
    contra o `doe_hash` dele. Sidecar ausente => segue (o aviso ja saiu)."""
    import hashlib
    try:
        from src import naming
        root = data_root if data_root is not None else naming.DEFAULT_DATA_ROOT
        mpath = naming.doe_manifest_path("DDMOP7", int(semente), root)
        with open(mpath, encoding="utf-8") as fh:
            side = json.load(fh)
    except Exception:                                         # noqa: BLE001
        return
    h = hashlib.sha256(
        np.ascontiguousarray(X, dtype="<f8").tobytes()).hexdigest()
    if h != side.get("doe_hash"):
        raise RuntimeError(
            f"DoE do DDMOP7 (semente {semente}): o CSV congelado decodifica "
            f"para hash {h[:16]}… mas o sidecar do artefato diz "
            f"{str(side.get('doe_hash'))[:16]}… — as duas rotas DIVERGEM. "
            f"Pára-e-loga (D81/D63).")


# ═══════════════════════════════════════════════════════════════════════════
#  Motores de avaliacao
# ═══════════════════════════════════════════════════════════════════════════

class _MotorMatlab:
    """
    UM engine MATLAB por run (D88.5). Faz o guard de pasta, pina 1 thread
    (D79) e expoe `avalia(X) -> (N,2)`.
    """

    def __init__(self, problems_dir: str | None, timeout_chamada: float = 900.0):
        import matlab.engine                                     # noqa: F401
        self._matlab = __import__("matlab")
        self.timeout_chamada = float(timeout_chamada)

        problems_dir = resolve_problems_dir(problems_dir)
        if "DDMOP_Plat" in os.path.normpath(problems_dir):
            raise RuntimeError(
                "recusando DDMOP_Plat: essa copia exige o objeto GLOBAL do "
                "PlatEMO. Use a interface standalone DDMOP_Exp/Problems (D88.5)")
        if not os.path.exists(os.path.join(problems_dir, "DDMOP7.p")):
            raise FileNotFoundError(f"DDMOP7.p nao encontrado em {problems_dir}")

        def _boot():
            eng = matlab.engine.start_matlab(
                "-nodisplay -nosplash -nodesktop")
            eng.cd(problems_dir, nargout=0)
            eng.maxNumCompThreads(1, nargout=0)                   # D79
            eng.eval("clear DDMOP7", nargout=0)
            # [MEDIDO, B-26 2026-08-13] O .p EXIGE um DDMOP7('init') por
            # processo ANTES de 'value' (estado persistente; 'value' a frio
            # morre num assert interno "condition ... scalar logical"). O
            # sorteio devolvido e DESCARTADO: amostragem gratis (nao-FE,
            # nao-dado; nao toca o contador de 600 — medido: 4 inits = 744
            # draw-points + value OK). O DoE do run vem BIT-A-BIT do artefato
            # congelado, jamais deste init. Mesmo fix do ddmop7_value_local.m
            # (rota R1) — as duas rotas pareadas.
            eng.eval("descarte_init = DDMOP7('init');", nargout=0)
            return eng

        # [T15.10 · O-18] boot INTEIRO sob prazo — ver TIMEOUT_PARTIDA.
        self.eng = _boot_com_prazo(_boot, TIMEOUT_PARTIDA,
                                   "boot da Engine (start+init)")
        self.problems_dir = problems_dir

    #: [MEDIDO, B-27 2026-08-13] ~6 s/avaliacao TAMBEM no Mac arm64 — um lote
    #: de 186 pontos numa chamada so (~1.116 s) estoura o watchdog de 900 s.
    #: Fatiar preserva o PROPOSITO do watchdog (pegar travamento, nao lote
    #: legitimo): o .p e funcao pura ponto-a-ponto (D102.11), entao fatiar e
    #: valor-identico. 64 pontos ~ 400 s por chamada, folga de 2x.
    MAX_PONTOS_POR_CHAMADA = 64

    def avalia(self, X: np.ndarray) -> np.ndarray:
        """
        Chama DDMOP7('value', X) com watchdog na CHAMADA (D60a), fatiando
        lotes maiores que MAX_PONTOS_POR_CHAMADA (valor-identico; ver acima).
        """
        X = np.atleast_2d(X)
        if X.shape[0] > self.MAX_PONTOS_POR_CHAMADA:
            partes = [self._avalia_bloco(b) for b in
                      np.array_split(X, int(np.ceil(
                          X.shape[0] / self.MAX_PONTOS_POR_CHAMADA)))]
            return np.vstack(partes)
        return self._avalia_bloco(X)

    def _avalia_bloco(self, X: np.ndarray) -> np.ndarray:
        """
        Um bloco <= MAX_PONTOS_POR_CHAMADA. `background=True` devolve um
        future; se nao completar no prazo, cancela-se e o run vira `failed`
        no manifesto -- o worker nao fica pendurado para sempre.
        """
        Xm = self._matlab.double([[float(v) for v in linha] for linha in X])
        fut = self.eng.DDMOP7("value", Xm, nargout=1, background=True)
        t0 = time.time()
        while not fut.done():
            if time.time() - t0 > self.timeout_chamada:
                try:
                    fut.cancel()
                except Exception:
                    pass
                try:
                    fut.cancel()
                finally:
                    # [T15.10 · achado nº 11 da revisão] a Engine acabou de
                    # provar que está TRAVADA — qualquer chamada síncrona a
                    # ela (o eval de higiene do encerra) penduraria o worker
                    # PARA SEMPRE (slot morto, sem manifesto, teto inócuo).
                    self._travada = True
                raise BridgeTimeout(
                    f"DDMOP7('value', {X.shape[0]}x{X.shape[1]}) nao retornou "
                    f"em {self.timeout_chamada:.0f}s (D60a)")
            time.sleep(0.05)
        F = np.asarray(fut.result(), dtype=np.float64)
        return np.atleast_2d(F)

    def encerra(self):
        """D86: nada de estado retido entre runs; o processo inteiro morre.

        [T15.10] Engine marcada TRAVADA (pós-BridgeTimeout) ⇒ PULA o eval
        síncrono de higiene (penduraria para sempre) e vai direto ao quit —
        o processo morre inteiro de qualquer forma (D88.5)."""
        if not getattr(self, "_travada", False):
            try:
                self.eng.eval("clear DDMOP7; clear functions", nargout=0)
            except Exception:
                pass
        try:
            self.eng.quit()
        except Exception:
            pass
        self.eng = None
        gc.collect()


class _MotorMock:
    """
    NAO E FIEL AO .p. Existe so para exercitar o arnes sem MATLAB. Reproduz as
    duas propriedades ESTRUTURAIS medidas no oraculo -- e nada mais:
      * f1 = k/17 com k inteiro (escada), e o treino nunca poda (k >= nz(x));
      * f2 in [0,1], decrescente com k na media (o trade-off do front de 4 pts).
    Qualquer artefato gerado com este motor carrega engine="mock".
    """

    def __init__(self, semente: int = 0):
        self.rng = np.random.default_rng(20260730 + int(semente))

    def avalia(self, X: np.ndarray) -> np.ndarray:
        X = np.atleast_2d(X)
        nz = (X != 0.0).sum(axis=1)
        # o treino interno so ACRESCENTA pesos (delta >= 0, medido no oraculo)
        k = np.minimum(D, nz + self.rng.integers(0, 3, size=len(X)))
        f1 = k / D
        f2 = 0.68 - 0.35 * f1 + 0.02 * self.rng.standard_normal(len(X))
        return np.column_stack([f1, np.clip(f2, 0.0, 1.0)])

    def encerra(self):
        gc.collect()


# ═══════════════════════════════════════════════════════════════════════════
#  O problema
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class _Catalogo:
    """Camada (1) do export: 1 linha por SOLUCAO unica (D57)."""
    x: list = field(default_factory=list)
    f: list = field(default_factory=list)
    first_fe_index: list = field(default_factory=list)

    def __len__(self):
        return len(self.x)


class DDMOP7Matlab(_PymooProblem):
    """
    O DDMOP7 como problema pymoo, avaliado no MATLAB oficial.

    Uso R2/R3 (via a casca `problems.DDMOP7`, que faz bind com
    contabilidade='externa' — um objeto por run, D88.5):
        prob = problems.DDMOP7().bind(semente)   # abre a Engine AQUI
        ...  # o FEBudget do harness chama evaluate_problem(prob, x)
        prob.encerra()                           # D86 — SEMPRE, em finally

    Uso standalone/smoke (contabilidade='propria'):
        prob = DDMOP7Matlab(semente=0, engine=...)
        X0   = prob.doe                      # 186 x 17, bit-a-bit do artefato
        ...  # o algoritmo consome X0 e propoe infills ate BudgetExhausted
        prob.encerra()                       # D86

    Em AMBOS os modos toda chamada ao .p passa por `avalia` -- o ponto unico
    dos guards de forma/finito (D81) e do teto de 600 (D88.5).
    """

    def __init__(self, semente: int, problems_dir: str | None = None,
                 doe_csv: str | None = None, engine: str = "matlab",
                 timeout_chamada: float = 900.0,
                 timeout_run: float = float("inf"),
                 max_iters_sem_fe: int = 50,
                 contabilidade: str = "propria",
                 data_root: str | None = None):
        super().__init__(n_var=D, n_obj=2,
                         xl=np.full(D, -1.0), xu=np.full(D, 1.0))
        if contabilidade not in ("propria", "externa"):
            raise ValueError(
                f"contabilidade desconhecida: {contabilidade!r} "
                f"(esperado 'propria' | 'externa' — cartao T15.7 §1.3/D89)")
        self.semente = int(semente)
        self.engine_kind = engine
        self.contabilidade = contabilidade
        self.fe = 0
        self.max_fe = MAX_FE
        self.chamadas_p = 0                       # pontos enviados ao .p (600)
        self._ids: dict[bytes, int] = {}          # bytes float64 de x -> id
        self.cat = _Catalogo()
        self.t0 = time.time()
        self.timeout_run = float(timeout_run)
        self.max_iters_sem_fe = int(max_iters_sem_fe)
        self._iters_sem_fe = 0
        self.n_cache_hits = 0
        self.n_pontos_zona_morta = 0              # [T15.12] p/ footer/laudo

        # [T15.7 §1.1(a)] DoE LAZY: carregado do ARTEFATO oficial no 1o acesso
        # (fallback CSV com aviso). No modo 'externa' o DoE do run e injetado
        # pelo HARNESS (load_doe + FEBudget) — a ponte nem o toca.
        self._doe: np.ndarray | None = None
        self._doe_csv = doe_csv
        self._data_root = data_root

        if engine == "matlab":
            self.motor = _MotorMatlab(problems_dir, timeout_chamada)
        elif engine == "mock":
            self.motor = _MotorMock(self.semente)
        else:
            raise ValueError(f"engine desconhecido: {engine!r}")

    # ------------------------------------------------------------------- DoE
    @property
    def doe(self) -> np.ndarray:
        """O DoE congelado da semente (186 x 17, bit-a-bit do artefato)."""
        if self._doe is None:
            if self._doe_csv is not None:
                self._doe = carrega_doe(self.semente, self._doe_csv)
            else:
                self._doe = carrega_doe_oficial(self.semente,
                                                data_root=self._data_root)
        return self._doe

    # ---------------------------------------------------------------- guardas
    def _checa_watchdogs(self):
        if time.time() - self.t0 > self.timeout_run:                    # D60b
            raise RunTimeout(f"run excedeu {self.timeout_run:.0f}s (D60b)")
        if self._iters_sem_fe > self.max_iters_sem_fe:                  # D60c
            raise StalledRun(
                f"{self._iters_sem_fe} chamadas consecutivas sem consumir FE "
                f"(saldo congelado, D60c)")

    # -------------------------------------------------------- avaliador CRU
    def avalia(self, X: np.ndarray) -> np.ndarray:
        """Ponto UNICO de contato com o motor (as duas contabilidades passam
        por aqui). Guards que NAO sao contabilidade: teto de 600 do .p
        (D88.5 — nao se confia na disciplina, checa-se) e forma/finito (D81).
        NAO conta FE, NAO deduplica, NAO grava catalogo."""
        X = np.atleast_2d(np.ascontiguousarray(np.asarray(X, dtype=np.float64)))
        m = X.shape[0]
        # [T15.12/D102.17] ZONA MORTA pos-DoE: os primeiros N_DOE_ONLINE
        # pontos enviados ao .p sao o DoE congelado (ficam CRUS — 50,1% das
        # coordenadas nao-zero dele tem |x|<tau e seriam corrompidas); todo
        # ponto alem e proposta da BUSCA => codificacao aplicada. O contador
        # `chamadas_p` e a fronteira (cache-hits nao chegam aqui, entao ele
        # conta exatamente os pontos REAIS ja enviados). A (1)/o catalogo
        # guardam o x PROPOSTO (ver docstring de `zona_morta`).
        ini_dz = max(0, N_DOE_ONLINE - self.chamadas_p)
        if ini_dz < m:
            X = X.copy()
            X[ini_dz:] = zona_morta(X[ini_dz:])
            self.n_pontos_zona_morta += int(m - ini_dz)
        if self.chamadas_p + m > P_CODE_CAP:
            raise RuntimeError(
                f"{self.chamadas_p + m} chamadas ao DDMOP7.p neste processo "
                f"passariam o teto de {P_CODE_CAP} -- UM processo MATLAB por "
                f"run (D88.5)")
        F = np.atleast_2d(np.asarray(self.motor.avalia(X), dtype=np.float64))
        self.chamadas_p += m
        if F.shape != (m, 2):
            raise RuntimeError(f"DDMOP7('value') devolveu {F.shape}, "
                               f"esperado ({m}, 2)")
        if not np.all(np.isfinite(F)):
            raise RuntimeError("DDMOP7('value') devolveu nao-finito "
                               "-- pára-e-loga (D81)")
        return F

    # ------------------------------------------------------------- avaliacao
    def _evaluate(self, X, out, *args, **kwargs):
        X = np.atleast_2d(np.ascontiguousarray(np.asarray(X, dtype=np.float64)))

        # ── [T15.7 §1.3] modo 'externa': avaliador CRU sob o FEBudget do
        # harness — UM contador so (D89). Nada de fe/dedup/catalogo/hard-stop
        # aqui: o harness ja dedupou (cache-hit nem chega) e ja conta.
        if self.contabilidade == "externa":
            out["F"] = self.avalia(X)
            return

        # ── modo 'propria' (standalone/smoke): o arnes completo ─────────────
        self._checa_watchdogs()

        # --- D57: quem ja tem id nao consome FE (cache-hit = 0 FE) -----------
        # A dedup e feita em DOIS niveis: contra o catalogo (lotes anteriores do
        # mesmo run) E dentro do proprio lote. Sem o segundo nivel, um algoritmo
        # que propoe o mesmo ponto duas vezes no mesmo lote gastaria 2 FE por
        # 1 solucao e criaria 2 solution_id para o mesmo x -- violando o D57.
        novos_idx, chaves, vistos_no_lote = [], [], set()
        for i, linha in enumerate(X):
            ch = linha.tobytes()                  # igualdade BIT-A-BIT (D57.3)
            chaves.append(ch)
            if ch not in self._ids and ch not in vistos_no_lote:
                vistos_no_lote.add(ch)
                novos_idx.append(i)
        self.n_cache_hits += len(X) - len(novos_idx)

        # --- D61: hard-stop no MEIO do lote ---------------------------------
        # avalia os primeiros `saldo` pontos NOVOS, grava, e SO ENTAO lanca.
        saldo = self.max_fe - self.fe
        estourou = len(novos_idx) > saldo
        a_avaliar = novos_idx[:saldo] if estourou else novos_idx

        if a_avaliar:
            self._iters_sem_fe = 0
            Xn = X[a_avaliar]
            Fn = self.avalia(Xn)          # guards + teto de 600 no ponto unico
            for j, i in enumerate(a_avaliar):
                self._ids[chaves[i]] = len(self.cat)
                self.cat.x.append(X[i].copy())
                self.cat.f.append(Fn[j].copy())
                self.cat.first_fe_index.append(self.fe + j)
            self.fe += len(Xn)
        else:
            self._iters_sem_fe += 1

        # --- monta a saida (cache-hits e recem-avaliados) --------------------
        F = np.full((len(X), 2), np.nan)
        for i, ch in enumerate(chaves):
            sid = self._ids.get(ch)
            if sid is not None:
                F[i] = self.cat.f[sid]
        out["F"] = F

        if estourou:
            raise BudgetExhausted(
                f"orcamento esgotado: FE = {self.fe} = 31D-1 (D21/D61). "
                f"{len(novos_idx) - len(a_avaliar)} ponto(s) do lote nao "
                "avaliado(s); os avaliados ja estao gravados no catalogo.")

    # --------------------------------------------------------------- export
    def camada1(self):
        """
        Camada (1) pronta para o Parquet: float32 SEM arredondamento (D53),
        uma linha por solucao unica, `solution_id` sequencial pela ordem da
        1a avaliacao real (D57.2). So faz sentido no modo 'propria' — na R2 a
        ① e do FEBudget/write_real do harness (D89).
        """
        return {
            "solution_id": np.arange(len(self.cat), dtype=np.int32),
            "first_fe_index": np.asarray(self.cat.first_fe_index, dtype=np.int32),
            "x": np.asarray(self.cat.x, dtype=np.float32),
            "f": np.asarray(self.cat.f, dtype=np.float32),
        }

    def manifesto(self, status: str = "ok", extra: dict | None = None) -> dict:
        m = {
            "problema": "DDMOP7", "semente": self.semente,
            "status": status,
            "engine": self.engine_kind,
            "contabilidade": self.contabilidade,          # [T15.7 §1.3/D89]
            "fe_final": self.fe, "fe_esperado": self.max_fe,
            "hard_stop_exato": self.fe == self.max_fe,
            "n_solucoes_unicas": len(self.cat),
            "n_cache_hits": self.n_cache_hits,
            "chamadas_p_code": self.chamadas_p, "teto_p_code": P_CODE_CAP,
            "doe_n": DOE_N, "doe_sha256_semente": _sha_doe(self.doe),
            "wall_clock_s": round(time.time() - self.t0, 3),
            "decisoes": ["D88.1", "D88.2", "D88.3", "D88.5", "D63", "D61",
                         "D57", "D53", "D79", "D60", "D86", "D102.5"],
        }
        if self.engine_kind == "mock":
            m["AVISO"] = ("motor MOCK -- nao e o DDMOP7.p; numeros NAO servem "
                          "para a tese, so para testar o arnes")
        if self.contabilidade == "externa":
            m["AVISO_CONTABILIDADE"] = (
                "contabilidade EXTERNA (R2): fe/catalogo desta ponte ficam "
                "zerados DE PROPOSITO — a autoridade e o FEBudget do harness "
                "(D89); use o manifesto do run, nao este")
        if extra:
            m.update(extra)
        return m

    def encerra(self):
        """D86: fecha o engine e solta o estado. Um processo por run.
        Idempotente (2a chamada e no-op)."""
        if getattr(self, "motor", None) is None:
            return
        try:
            self.motor.encerra()
        finally:
            self.motor = None
            gc.collect()


def _sha_doe(X: np.ndarray) -> str:
    import hashlib
    return hashlib.sha256(np.ascontiguousarray(X, np.float64).tobytes()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
#  Smoke test do arnes (roda sem MATLAB: --mock)
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    eng = "mock" if "--mock" in sys.argv else "matlab"
    doe_csv = None
    for a in sys.argv[1:]:
        if a.startswith("--doe="):
            doe_csv = a.split("=", 1)[1]

    p = DDMOP7Matlab(semente=0, engine=eng, doe_csv=doe_csv)
    print(f"DoE carregado: {p.doe.shape}  sha256={_sha_doe(p.doe)[:16]}")

    out = {}
    p._evaluate(p.doe, out)
    print(f"apos o DoE: FE = {p.fe} (esperado {DOE_N})")

    # cache-hit: re-submeter o DoE nao pode consumir FE (D57.5)
    p._evaluate(p.doe[:10], out)
    assert p.fe == DOE_N, "cache-hit consumiu FE!"
    print(f"cache-hit ok: FE segue {p.fe}, hits = {p.n_cache_hits}")

    # duplicata DENTRO do lote: 3 copias de 1 ponto novo = 1 FE, 1 solucao
    fe_antes, n_antes = p.fe, len(p.cat)
    novo = np.full((3, D), 0.123456789)
    p._evaluate(novo, out)
    assert p.fe - fe_antes == 1, f"duplicata no lote consumiu {p.fe-fe_antes} FE"
    assert len(p.cat) - n_antes == 1, "duplicata no lote criou >1 solution_id"
    assert np.allclose(out["F"][0], out["F"][1]) and np.allclose(out["F"][1], out["F"][2])
    print(f"dedup no lote ok: 3 copias -> 1 FE, 1 solucao (FE = {p.fe})")

    # infills ate o hard-stop, com um lote que ESTOURA o saldo de proposito
    rng = np.random.default_rng(0)
    n_lotes = 0
    try:
        while True:
            X = rng.uniform(-1, 1, size=(37, D))
            p._evaluate(X, out)
            n_lotes += 1
    except BudgetExhausted as e:
        print(f"\nBudgetExhausted apos {n_lotes} lotes cheios: {e}")

    print(f"FE final = {p.fe}  (31D-1 = {MAX_FE})  exato = {p.fe == MAX_FE}")
    c1 = p.camada1()
    print(f"camada 1: {len(c1['solution_id'])} solucoes, "
          f"x {c1['x'].dtype} {c1['x'].shape}, f {c1['f'].dtype} {c1['f'].shape}")
    print(json.dumps(p.manifesto(), indent=2, ensure_ascii=False))
    p.encerra()
