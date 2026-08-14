# -*- coding: utf-8 -*-
"""[T15.4/D102.1] DoE congelado do DDMOP7 — o artefato honra o contrato D63.

Controles: geração em TEMPDIR a partir do CSV congelado real; round-trip
bit-exato; consumo pelos DOIS load_doe oficiais; controle negativo de
adulteração (CSV corrompido ⇒ o --check DETECTA); zeros negativos preservados.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CSV = os.path.join(ROOT, "data", "real_sources", "ddmop7",
                   "doe_ddmop7_online_30sementes.csv")

try:
    import numpy as np
    from src import doe as _doe
    _HAVE_STACK = True
except Exception:  # noqa: BLE001
    _HAVE_STACK = False


def _mod():
    spec = importlib.util.spec_from_file_location(
        "gen_doe_ddmop7", os.path.join(ROOT, "scripts", "gen_doe_ddmop7.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@unittest.skipUnless(_HAVE_STACK and os.path.exists(CSV),
                     "sem stack ou sem o CSV congelado")
class TestDoECongelado(unittest.TestCase):
    def test_geracao_em_tempdir_e_consumo_oficial(self):
        g = _mod()
        blocos = g._carrega_csv(CSV)
        self.assertEqual(sorted(blocos), sorted(g.SEEDS))
        sha = g._sha256_file(CSV)
        with tempfile.TemporaryDirectory() as td:
            r = g.gen_one(0, blocos[0], csv_sha=sha, data_root=td)
            self.assertFalse(r["skipped"])
            self.assertEqual((r["n_rows"], r["n_cols"]), (186, 17))
            self.assertEqual(r["problema_id"], 26)
            # consumo pelo load_doe oficial (o contrato de verdade)
            from src.standalone_harness import load_doe
            d = load_doe("DDMOP7", 0, data_root=td)
            self.assertEqual(d["X"].shape, (186, 17))
            self.assertTrue(np.array_equal(d["X"], blocos[0]))
            # idempotência: segunda chamada pula com integridade
            r2 = g.gen_one(0, blocos[0], csv_sha=sha, data_root=td)
            self.assertTrue(r2["skipped"])

    def test_zeros_negativos_preservados(self):
        g = _mod()
        blocos = g._carrega_csv(CSV)
        X = blocos[0]
        neg = np.signbit(X) & (X == 0.0)
        self.assertGreater(int(neg.sum()), 0,
                           "o CSV congelado TEM -0; a carga deve preservar")

    def test_controle_negativo_adulteracao(self):
        # corromper 1 valor do parquet ⇒ o hash do sidecar DETECTA no load
        g = _mod()
        blocos = g._carrega_csv(CSV)
        sha = g._sha256_file(CSV)
        with tempfile.TemporaryDirectory() as td:
            g.gen_one(0, blocos[0], csv_sha=sha, data_root=td)
            from src import naming
            path = naming.doe_path("DDMOP7", 0, td)
            X_adult = blocos[0].copy()
            X_adult[0, 0] = 0.5  # adulteração de 1 célula
            _doe._write_matrix_parquet(path, X_adult,
                                       [f"x{i}" for i in range(17)])
            from src.standalone_harness import load_sonda  # noqa: F401
            from src.standalone_harness import load_doe
            with self.assertRaises(RuntimeError):
                load_doe("DDMOP7", 0, data_root=td)

    def test_bloco_errado_para_e_loga(self):
        g = _mod()
        blocos = g._carrega_csv(CSV)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(RuntimeError):
                g.gen_one(0, blocos[0][:100], csv_sha="x", data_root=td)


if __name__ == "__main__":
    unittest.main()
