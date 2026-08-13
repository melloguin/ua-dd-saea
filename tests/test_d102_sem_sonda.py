# -*- coding: utf-8 -*-
"""[D102.10/REAL-2.10] O opt-out da sonda POR PROBLEMA — controles de comportamento.

Doutrina do controle negativo (T12): cada teste aqui REPROVA no código anterior
ao opt-out — `load_sonda('DDMOP7')` levantava FileNotFoundError em vez de
devolver None, e `gen_sonda` não tinha conceito de problema-sem-sonda.

O conjunto também carrega o controle de NÃO-superbloqueio: um problema fora de
`PROBLEMAS_SEM_SONDA` com artefato ausente continua parando-e-logando (D81) —
o opt-out não pode virar um silenciador geral de sonda ausente.
"""
import importlib.util
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.experiment import PROBLEMAS_SEM_SONDA  # noqa: E402


def _carrega_gen_sonda():
    """Importa scripts/gen_sonda.py por caminho (o diretório não é pacote)."""
    spec = importlib.util.spec_from_file_location(
        "gen_sonda", os.path.join(ROOT, "scripts", "gen_sonda.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestConstanteCanonica(unittest.TestCase):
    def test_ddmop7_esta_no_conjunto(self):
        self.assertIn("DDMOP7", PROBLEMAS_SEM_SONDA)

    def test_conjunto_e_imutavel(self):
        self.assertIsInstance(PROBLEMAS_SEM_SONDA, frozenset)

    def test_canonicos_atuais_ficam_fora(self):
        # Nenhum dos problemas COM sonda materializada pode cair no opt-out —
        # isso desligaria a régua viva de um problema que a tem.
        for prob in ("MMF1", "ZDT1", "DTLZ2", "WFG9", "BBOB_F1"):
            self.assertNotIn(prob, PROBLEMAS_SEM_SONDA)


class TestLoadSondaGemeos(unittest.TestCase):
    """Os dois gêmeos devolvem None para problema sem sonda — e SÓ para eles."""

    def test_botorch_devolve_none(self):
        from src.botorch_harness import load_sonda
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(load_sonda("DDMOP7", data_root=td))

    def test_standalone_devolve_none(self):
        from src.standalone_harness import load_sonda
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(load_sonda("DDMOP7", data_root=td))

    def test_gemeos_concordam(self):
        from src.botorch_harness import load_sonda as ls_bt
        from src.standalone_harness import load_sonda as ls_sa
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(ls_bt("DDMOP7", data_root=td),
                             ls_sa("DDMOP7", data_root=td))

    def test_nao_superbloqueia_botorch(self):
        # Problema FORA do conjunto + artefato ausente ⇒ continua D81.
        from src.botorch_harness import load_sonda
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                load_sonda("MMF1", data_root=td)

    def test_nao_superbloqueia_standalone(self):
        from src.standalone_harness import load_sonda
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                load_sonda("MMF1", data_root=td)


class TestGenSondaPula(unittest.TestCase):
    def test_predicado_de_pulo(self):
        gs = _carrega_gen_sonda()
        self.assertTrue(gs._sem_sonda("DDMOP7"))
        self.assertFalse(gs._sem_sonda("MMF1"))

    def test_predicado_le_a_fonte_unica(self):
        # O predicado não pode ter lista própria: tem de espelhar a constante
        # canônica (fonte única, doutrina B-06).
        gs = _carrega_gen_sonda()
        for prob in PROBLEMAS_SEM_SONDA:
            self.assertTrue(gs._sem_sonda(prob))


if __name__ == "__main__":
    unittest.main()
