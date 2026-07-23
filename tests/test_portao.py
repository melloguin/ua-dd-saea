# -*- coding: utf-8 -*-
"""test_portao — [DI-32/T1] o driver de portão cobre TODOS os configs do grid."""
import csv
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)

import portao  # noqa: E402
from src.manifest import OFFLINE_ALGS  # noqa: E402


class TestCoberturaDoPortao(unittest.TestCase):
    def _algs_do_grid(self):
        p = os.path.join(ROOT, "claude_code_context", "artifacts",
                         "runs_matrix.csv")
        with open(p, encoding="utf-8") as fh:
            return {r["alg"] for r in csv.DictReader(fh)}

    def test_todo_config_do_grid_tem_cartao(self):
        faltam = self._algs_do_grid() - set(portao.CARTAO_POR_ALG) - {"sobol_batch"}
        self.assertFalse(faltam, f"configs do grid SEM cartão no portão: {faltam} "
                                 "(sobol_batch é a exceção conhecida — M10/T6)")

    def test_offline_vem_da_fonte_unica(self):
        # o portão importa OFFLINE_ALGS do manifest (não duplica o conjunto)
        self.assertEqual(portao.OFFLINE_ALGS, OFFLINE_ALGS)
        for alg in ("e103", "b5r", "b5m", "c311", "moead_media"):
            self.assertIn(alg, portao.OFFLINE_ALGS)

    def test_cartoes_r3_dedicados(self):
        for alg, card in (("c311", "R3-c311"), ("moead_media", "R3-piso-off"),
                          ("b5r", "R3-b5"), ("b5m", "R3-b5"),
                          ("c122", "R3-c122"), ("c149", "R3-c149"),
                          ("e81", "R3-e81")):
            self.assertEqual(portao.CARTAO_POR_ALG[alg], card)


if __name__ == "__main__":
    unittest.main()
