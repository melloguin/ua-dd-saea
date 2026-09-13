# -*- coding: utf-8 -*-
"""[T12/BL-02] `flag_vetores_degenerados` da família b5 — VALOR + controle negativo.

Por que este arquivo existe
---------------------------
O campo nasceu no T11 (I-05 item 3) para tornar MEDIDA a causa a montante da
cadeia **A8** (o congelamento do b5m): `ReferenceVectors.adapt` multiplica os
vetores por `max(fitness) − min(fitness)` **por objetivo**
(`ReferenceVectors.py:256-261`); com o surrogate devolvendo objetivo constante o
fator vira 0, os vetores colapsam, o PBI dá NaN, `P_wrong ≡ 0` e nenhuma
substituição acontece. O campo entrou verde e veio **não-nulo em 0/1.144**.

A causa (A40-2): ele lia `evolver.population.problem.reference_vectors` — mas os
vetores vivem no **evolver** (`BaseEA.py:182`), e o `desdeo_problem` vendorizado
tem **zero** ocorrências de `reference_vectors`. O `except Exception: return
None` engolia o `AttributeError`.

O que este teste faz
--------------------
Usa a classe **`ReferenceVectors` VENDORIZADA de verdade** (carregada do
`algorithms/b5_Prob-RVEA/`) e roda a cadeia A8 sobre ela — colapso total,
colapso PARCIAL e vetores sadios — aferindo os **valores** que
`_vetores_degenerados` emite. O controle negativo executa o **mesmo fonte** da
função com o leitor de ontem e prova que ele devolve `None`.

> ⚠ `inspect.getsource` aparece aqui para **construir o mutante que é
> EXECUTADO** — não para afirmar nada sobre texto. É o oposto do antipadrão que
> este cartão extingue (BL-16).
"""
import importlib.util as _iu
import inspect
import os
import sys
import textwrap
import unittest

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from src import b5_prob  # noqa: E402

#: O par que define o controle: o leitor de hoje × o de ontem.
LEITOR_HOJE = "V = evolver.reference_vectors.values"
LEITOR_ONTEM = "V = evolver.population.problem.reference_vectors.values"

_RV_PATH = os.path.join(RAIZ, "algorithms", "b5_Prob-RVEA", "desdeo_emo",
                        "othertools", "ReferenceVectors.py")


def _reference_vectors_vendorizado():
    """A classe REAL do vendorizado, carregada por caminho.

    Import direto (`from desdeo_emo.othertools import ...`) puxaria o
    `plotlyanimate` do `__init__`, que exige `plotly` (ausente no env-main). O
    carregamento por caminho pega a classe sem o pacote — e é a MESMA classe que
    o `BaseEA` instancia no run.
    """
    spec = _iu.spec_from_file_location("_t12_rv", _RV_PATH)
    mod = _iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ReferenceVectors


RV = _reference_vectors_vendorizado()


class _ProblemDoDesdeo:
    """O `problem` do DESDEO (um `DataProblem`).

    Medido no vendorizado: **0 ocorrências** de `reference_vectors` em
    `algorithms/b5_Prob-RVEA/desdeo_problem/`. É por isso que o leitor de ontem
    levantava `AttributeError` — e não porque o objeto estivesse vazio.
    """

    def __init__(self, n_obj):
        self.n_of_objectives = n_obj


class _PopulationDoDesdeo:
    def __init__(self, problem):
        self.problem = problem


class _EvolverDoDesdeo:
    """A forma do `BaseEA`: `self.reference_vectors` no EVOLVER (:182) e
    `self.population = Population(problem, ...)` ao lado."""

    def __init__(self, rv, problem):
        self.reference_vectors = rv
        self.population = _PopulationDoDesdeo(problem)


def _evolver(n_obj=3, lattice=4, fitness=None):
    rv = RV(lattice_resolution=lattice, number_of_objectives=n_obj)
    if fitness is not None:
        rv.adapt(np.asarray(fitness, dtype=float))   # a cadeia A8, literal
    return _EvolverDoDesdeo(rv, _ProblemDoDesdeo(n_obj))


def _mutante_leitor_de_ontem():
    """O MESMO fonte de `_vetores_degenerados`, com o leitor de ontem."""
    src = textwrap.dedent(inspect.getsource(b5_prob._vetores_degenerados))
    if src.count(LEITOR_HOJE) != 1:
        raise AssertionError(
            "o leitor `%s` não está mais no fonte (1 ocorrência esperada) — o "
            "controle negativo perdeu o alvo" % LEITOR_HOJE)
    ns = {}
    exec(compile(src.replace(LEITOR_HOJE, LEITOR_ONTEM),  # noqa: S102
                 "<b5_prob:mutante_A40-2>", "exec"), ns)
    return ns["_vetores_degenerados"]


class TestVetoresDegenerados(unittest.TestCase):

    def test_vetores_sadios_dao_valores_medidos(self):
        """O caso de controle: nada colapsou, e o campo diz isso com números."""
        d = b5_prob._vetores_degenerados(_evolver())
        self.assertIsNotNone(d, "campo nulo com evolver válido — o leitor "
                                "voltou a apontar para o objeto errado")
        self.assertEqual(d["n_vetores"], 15)
        self.assertEqual(d["n_norma_zero"], 0)
        self.assertAlmostEqual(d["norma_min"], 1.0)
        self.assertAlmostEqual(d["norma_max"], 1.0)

    def test_colapso_A8_total_aparece_em_n_norma_zero(self):
        """O achado D9-4/A8, finalmente instrumentado.

        `adapt` com fitness CONSTANTE em todos os objetivos (o que o surrogate
        congelado devolve) zera `max−min` e leva TODOS os vetores a norma 0.
        """
        d = b5_prob._vetores_degenerados(_evolver(fitness=np.zeros((5, 3))))
        self.assertEqual(d["n_norma_zero"], d["n_vetores"],
                         "o colapso total do A8 não apareceu no campo")
        self.assertEqual(d["norma_max"], 0.0)

    def test_congelamento_PARCIAL_e_visivel(self):
        """O caso que só a medida contínua discrimina (I-05 item 4).

        Com UM objetivo constante, `adapt` zera só aquela coluna: colapsam os
        vetores que viviam apenas nela — 1 dos 15 no lattice 4×3, a face
        prevista. `n_norma_zero` sozinho não distinguiria "colapso parcial" de
        "colapso total"; a AMPLITUDE sim — e é o único dos três cenários em que
        ela é > 0 (sadio e colapso total dão amplitude 0 nos dois).
        """
        fit = np.array([[0., 5., 1.], [2., 5., 3.]])   # objetivo 2 constante
        d = b5_prob._vetores_degenerados(_evolver(fitness=fit))
        self.assertGreater(d["n_norma_zero"], 0)
        self.assertLess(d["n_norma_zero"], d["n_vetores"])
        self.assertGreater(d["amplitude"], 0.0)

    def test_CONTROLE_NEGATIVO_o_leitor_de_ontem_devolve_None(self):
        """Sem este controle os testes acima não provariam nada.

        O leitor de ontem tem de devolver `None` nos MESMOS objetos — é o
        0/1.144 da campanha T11 reproduzido em banco.
        """
        ontem = _mutante_leitor_de_ontem()
        for cenario, ev in (("sadio", _evolver()),
                            ("colapso A8", _evolver(fitness=np.zeros((5, 3))))):
            with self.subTest(cenario=cenario):
                self.assertIsNone(
                    ontem(ev),
                    "o leitor de ontem NÃO reproduziu o defeito A40-2 — então "
                    "o teste de valor não discrimina o objeto lido")

    def test_o_problem_do_desdeo_nao_tem_os_vetores(self):
        """A causa-raiz, aferida no objeto e não no grep."""
        ev = _evolver()
        self.assertFalse(hasattr(ev.population.problem, "reference_vectors"))
        self.assertTrue(hasattr(ev, "reference_vectors"))


if __name__ == "__main__":
    unittest.main()
