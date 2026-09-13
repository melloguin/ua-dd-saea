# -*- coding: utf-8 -*-
"""[T15.7 §3] Processo A — o dataset offline do DDMOP7 honra o contrato D90.

Controles (tempdir SEMPRE; motor mock — o F REAL é das VMs Linux, D102.14):
  * geração em tempdir a partir do CSV congelado real (sha conferido);
  * o artefato é consumido pelo `load_dataset` OFICIAL sem NENHUM caso
    especial — a prova de que os runners offline (b5m b5r moead_media e103)
    ficam com ZERO mudança;
  * round-trip bit-a-bit; zeros NEGATIVOS preservados; idempotência;
  * controle negativo de adulteração (1 célula trocada ⇒ o CP-init offline
    DETECTA); bloco de forma errada ⇒ pára-e-loga;
  * `--limite` exige data-root explícito e carimba PARCIAL_LIMITE (artefato
    parcial jamais silencioso); motor mock carimba engine='mock' + AVISO.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np                                        # noqa: E402

CSV = os.path.join(ROOT, "data", "real_sources", "ddmop7",
                   "dataset_ddmop7_offline_30sementes.csv")


def _mod():
    spec = importlib.util.spec_from_file_location(
        "gen_dataset_ddmop7",
        os.path.join(ROOT, "scripts", "gen_dataset_ddmop7.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@unittest.skipUnless(os.path.exists(CSV), "CSV congelado ausente")
class TestProcessoA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = _mod()
        cls.sha = cls.g._sha256_file(CSV)
        cls.blocos = cls.g._carrega_csv(CSV)

    def test_csv_congelado_confere(self):
        # âncora do cartão §3.2: sha 03056b6e… e 30 blocos de 526×17
        self.assertEqual(self.sha, self.g.CSV_SHA256_ESPERADO)
        self.assertEqual(sorted(self.blocos), sorted(self.g.SEEDS))
        self.assertEqual(self.blocos[0].shape, (526, 17))
        neg = np.signbit(self.blocos[0]) & (self.blocos[0] == 0.0)
        self.assertGreater(int(neg.sum()), 0,
                           "o CSV congelado TEM -0; a carga deve preservar")

    def test_geracao_mock_e_consumo_pelo_load_dataset_oficial(self):
        g = self.g
        with tempfile.TemporaryDirectory() as td:
            r = g.gen_one(0, self.blocos[0], csv_sha=self.sha, data_root=td,
                          engine="mock")
            self.assertFalse(r["skipped"])
            self.assertEqual((r["n_rows"], r["n_cols"]), (526, 19))
            self.assertEqual(r["problema_id"], 26)
            # slot de CONTRATO + proveniência REAL, lado a lado
            self.assertEqual((r["tier"], r["dist"]), ("small", "lhs"))
            self.assertEqual(r["sampler"], "frozen-ddmop7-init-offline")
            self.assertEqual(r["engine"], "mock")
            self.assertIn("AVISO", r)               # mock NUNCA vira tese
            # consumo pelo load_dataset OFICIAL (o contrato de verdade —
            # runners offline com ZERO mudança):
            from src.standalone_harness import load_dataset
            ds = load_dataset("DDMOP7", 0, data_root=td)
            self.assertEqual(ds["X"].shape, (526, 17))
            self.assertEqual(ds["F"].shape, (526, 2))
            self.assertEqual(ds["n"], 526)
            self.assertTrue(np.array_equal(ds["X"], self.blocos[0]))
            neg = np.signbit(ds["X"]) & (ds["X"] == 0.0)
            self.assertGreater(int(neg.sum()), 0)   # -0 sobreviveu ao parquet
            # o orçamento offline monta em cima (o molde do e103):
            from src.standalone_harness import load_offline_budget
            bud, ds2 = load_offline_budget("DDMOP7", 0, data_root=td)
            self.assertEqual(bud.maxfe, 526)
            self.assertEqual(bud.fe, 526)           # nasce ESGOTADO (D90)
            # idempotência: 2a chamada pula com integridade
            r2 = g.gen_one(0, self.blocos[0], csv_sha=self.sha, data_root=td,
                           engine="mock")
            self.assertTrue(r2["skipped"])
            # --check aprova
            self.assertTrue(g.check_one(0, self.blocos[0], csv_sha=self.sha,
                                        data_root=td))

    def test_limite_gera_parcial_carimbado(self):
        g = self.g
        with tempfile.TemporaryDirectory() as td:
            r = g.gen_one(0, self.blocos[0], csv_sha=self.sha, data_root=td,
                          engine="mock", limite=4)
            self.assertEqual(r["n"], 4)
            self.assertEqual(r["PARCIAL_LIMITE"], 4)
            self.assertIn("AVISO_PARCIAL", r)
            from src.standalone_harness import load_dataset
            ds = load_dataset("DDMOP7", 0, data_root=td)
            self.assertEqual(ds["n"], 4)            # espelho fiel do sidecar

    def test_controle_negativo_adulteracao(self):
        g = self.g
        with tempfile.TemporaryDirectory() as td:
            g.gen_one(0, self.blocos[0], csv_sha=self.sha, data_root=td,
                      engine="mock")
            from src import doe as _doe
            from src import naming
            cols = [f"x{i}" for i in range(17)] + ["f0", "f1"]
            path = naming.dataset_path("DDMOP7", 0, None, None, td)
            XF = _doe._read_matrix_parquet(path, cols)
            XF[0, 0] = 0.5                          # 1 célula adulterada
            _doe._write_matrix_parquet(path, XF, cols)
            from src.standalone_harness import load_dataset
            with self.assertRaises(RuntimeError):
                load_dataset("DDMOP7", 0, data_root=td)
            self.assertFalse(g.check_one(0, self.blocos[0], csv_sha=self.sha,
                                         data_root=td))

    def test_bloco_errado_para_e_loga(self):
        g = self.g
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(RuntimeError):
                g.gen_one(0, self.blocos[0][:100], csv_sha="x", data_root=td,
                          engine="mock")

    def test_limite_sem_data_root_e_recusado(self):
        g = self.g
        with mock.patch.object(sys, "argv",
                               ["gen_dataset_ddmop7.py", "--limite", "4",
                                "--engine", "mock", "--sementes", "0"]):
            self.assertEqual(g.main(), 1)

    def test_semente_fora_do_estudo_e_recusada(self):
        g = self.g
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(sys, "argv",
                                   ["gen_dataset_ddmop7.py", "--engine",
                                    "mock", "--sementes", "31",
                                    "--data-root", td]):
                self.assertEqual(g.main(), 1)

    def test_engine_matlab_sem_engine_e_skip_declarado(self):
        try:
            import matlab.engine                    # noqa: F401
        except Exception:
            g = self.g
            with tempfile.TemporaryDirectory() as td:
                with self.assertRaises(ImportError):
                    g.gen_one(0, self.blocos[0], csv_sha=self.sha,
                              data_root=td, engine="matlab", limite=1)
            self.skipTest("matlab.engine ausente — o F REAL é gerado nas "
                          "VMs Linux (D102.14) pelo provisionamento")


if __name__ == "__main__":
    unittest.main()
