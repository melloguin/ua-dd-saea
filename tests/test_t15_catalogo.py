# -*- coding: utf-8 -*-
"""[T15.2/D101] Os 3 problemas de dados reais no catálogo — posições, cascas e âncoras.

Controles:
  * POSIÇÕES 25/26/27 são IRREVERSÍVEIS (Q1): o id posicional alimenta a
    SeedSequence (D62) — estes asserts são o tripwire contra reordenação.
  * Âncoras de VALOR (não de existência — doutrina T12): pontos com f
    verificado pelos portões do gerador de exemplos do pacote de fusão
    (`docs/exemplos/gerar_exemplos.py`, escrita diferida provada).
  * A casca do DDMOP7 nunca devolve número sem estar ligada (D81) e o
    para-raios do front D72 (D102.4) levanta SEMPRE.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    import numpy as np
    from src import problems as P
    _HAVE_STACK = True
except Exception:  # noqa: BLE001
    _HAVE_STACK = False


class TestPosicoesIrreversiveis(unittest.TestCase):
    def test_ids_posicionais(self):
        from src.doe import PROBLEMA_ID
        self.assertEqual(PROBLEMA_ID["RE21"], 25)
        self.assertEqual(PROBLEMA_ID["DDMOP7"], 26)
        self.assertEqual(PROBLEMA_ID["ESTOQUE40"], 27)

    def test_28_problemas_e_os_25_intactos(self):
        from src.experiment import ALL_PROBLEMS
        from src.doe import PROBLEMA_ID
        self.assertEqual(len(ALL_PROBLEMS), 28)
        # os ids 0-24 são IMUTÁVEIS (âncoras dos hashes de DoE/sonda da s42)
        self.assertEqual(PROBLEMA_ID["MMF1"], 0)
        self.assertEqual(PROBLEMA_ID["BBOB_F55"], 24)

    def test_seeds_json_espelha(self):
        import json
        with open(os.path.join(ROOT, "claude_code_context", "artifacts",
                               "seeds.json"), encoding="utf-8") as fh:
            pub = json.load(fh)
        from src.doe import PROBLEMA_ID
        self.assertEqual(pub["shared_init_artifacts"]["problema_id"],
                         PROBLEMA_ID)

    def test_espelho_matlab_tem_os_3(self):
        # experiments.m::default_problems é lista HARDCODED (espelho sem fonte
        # derivável) — tripwire de drift entre os catálogos.
        txt = open(os.path.join(ROOT, "experiments.m"), encoding="utf-8").read()
        for nome in ("'RE21'", "'DDMOP7'", "'ESTOQUE40'"):
            self.assertIn(nome, txt)


@unittest.skipUnless(_HAVE_STACK, "sem numpy/pymoo (env-main)")
class TestRE21(unittest.TestCase):
    def test_forma(self):
        p = P.RE21()
        self.assertEqual((p.n_var, p.n_obj), (4, 2))
        s2 = np.sqrt(2.0)
        self.assertTrue(np.allclose(p.xl, [1.0, s2, s2, 1.0]))
        self.assertTrue(np.allclose(p.xu, [3.0, 3.0, 3.0, 3.0]))

    def test_ancora_de_valor_canto_ideal_f1(self):
        # canto (1, √2, √2, 1): f1 = 200·(2+2+2^0.25+1); f2 = 0.01·(2+2−2+2)
        p = P.RE21()
        s2 = np.sqrt(2.0)
        F = P.evaluate_problem(p, np.array([[1.0, s2, s2, 1.0]]))
        self.assertAlmostEqual(F[0, 0], 1237.8414230005442, places=9)
        self.assertAlmostEqual(F[0, 1], 0.04, places=12)

    def test_front_d72_em_cache(self):
        cache = os.path.join(ROOT, "data", "real_pf_cache", "RE21_d4.npz")
        self.assertTrue(os.path.exists(cache),
                        "cache D72 do RE21 ausente — NUNCA recompute em laço")
        X, F = P.RE21().true_pareto_front(n=100)
        self.assertEqual(X.shape[1], 4)
        self.assertEqual(F.shape[1], 2)

    def test_front_oficial_crosscheck_presente(self):
        F = P.RE21.front_oficial_suite_RE()
        self.assertIsNotNone(F)
        self.assertEqual(F.shape, (1000, 2))


@unittest.skipUnless(_HAVE_STACK, "sem numpy/pymoo (env-main)")
class TestDDMOP7Casca(unittest.TestCase):
    def setUp(self):
        os.environ.pop("DDMOP7_SEMENTE", None)

    def test_instancia_barato_e_desligado(self):
        p = P.DDMOP7()
        self.assertEqual((p.n_var, p.n_obj), (17, 2))
        self.assertTrue(np.allclose(p.xl, -1.0) and np.allclose(p.xu, 1.0))
        self.assertFalse(p.ligado)

    def test_avaliar_sem_ligar_para_e_loga(self):
        p = P.DDMOP7()
        with self.assertRaises(RuntimeError):
            P.evaluate_problem(p, np.zeros((1, 17)))

    def test_para_raios_do_front(self):
        with self.assertRaises(NotImplementedError):
            P.DDMOP7().true_pareto_front()

    def test_sem_sonda_e_sem_front_nas_fontes_unicas(self):
        from src.experiment import PROBLEMAS_SEM_SONDA
        from src.metrics import PROBLEMAS_SEM_FRONT_D72
        self.assertIn("DDMOP7", PROBLEMAS_SEM_SONDA)
        self.assertIn("DDMOP7", PROBLEMAS_SEM_FRONT_D72)


@unittest.skipUnless(_HAVE_STACK, "sem numpy/pymoo (env-main)")
class TestESTOQUE40(unittest.TestCase):
    def test_forma_e_dado_congelado(self):
        p = P.ESTOQUE40()
        self.assertEqual((p.n_var, p.n_obj), (40, 3))
        self.assertTrue(np.all(p.xl == 0.0))
        self.assertEqual(p._D.shape, (40, 106))   # 40 produtos × 106 semanas

    def test_ancora_x_zero(self):
        p = P.ESTOQUE40()
        F = P.evaluate_problem(p, np.zeros((1, 40)))
        self.assertAlmostEqual(F[0, 0], 0.0, places=12)   # não vende nada
        self.assertAlmostEqual(F[0, 1], 0.0, places=12)   # não sobra nada
        self.assertAlmostEqual(F[0, 2], 0.0, places=12)   # cobertura = estoque

    def test_ancora_x_igual_xu(self):
        # linha 2 do CSV de exemplos VERIFICADO por portões (gerar_exemplos.py)
        p = P.ESTOQUE40()
        F = P.evaluate_problem(p, p.xu.reshape(1, -1))
        self.assertAlmostEqual(F[0, 0], -17909.135472, delta=1e-4)
        self.assertAlmostEqual(F[0, 1], 7492.938906, delta=1e-4)
        self.assertAlmostEqual(F[0, 2], 3.19911603, delta=1e-6)

    def test_front_d72_em_cache(self):
        cache = os.path.join(ROOT, "data", "real_pf_cache", "ESTOQUE40_d40.npz")
        self.assertTrue(os.path.exists(cache),
                        "cache D72 do ESTOQUE40 ausente — recompute = 164 s")
        X, F = P.ESTOQUE40().true_pareto_front(n=100)
        self.assertEqual(X.shape[1], 40)
        self.assertEqual(F.shape[1], 3)


if __name__ == "__main__":
    unittest.main()
