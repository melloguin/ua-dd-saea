"""Unit-test da nomenclatura §17.7/D55 (3 camadas + jsonl + manifesto + blob).

Roda em stdlib puro: `python3 -m unittest discover -s tests` (ou direto).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import naming


class TestNaming(unittest.TestCase):

    def test_run_id_e_base(self):
        self.assertEqual(naming.run_id("main", "c217", "DTLZ2", 0),
                         "main_c217_DTLZ2_0")
        self.assertEqual(naming.base("main", "c217", "DTLZ2", 0),
                         "exp_main_c217_DTLZ2_0")

    def test_tres_camadas(self):
        b = "exp_main_c217_DTLZ2_0"
        self.assertEqual(naming.LAYERS, ("real", "pop", "surrogate", "timing"))
        self.assertEqual(
            naming.layer_filenames("main", "c217", "DTLZ2", 0),
            [f"{b}__real.parquet", f"{b}__pop.parquet",
             f"{b}__surrogate.parquet", f"{b}__timing.parquet"])

    def test_jsonl_e_manifesto(self):
        b = "exp_main_c217_DTLZ2_0"
        self.assertEqual(naming.jsonl_filename("main", "c217", "DTLZ2", 0),
                         f"{b}.jsonl")
        self.assertEqual(naming.manifest_filename("main", "c217", "DTLZ2", 0),
                         f"{b}.manifest.json")

    def test_quatro_saidas(self):
        # As "4 saídas" verificáveis = 3 tabelas + timing + jsonl (§22.6).
        outs = naming.output_filenames("main", "c217", "DTLZ2", 0)
        self.assertEqual(len(outs), 5)
        self.assertTrue(outs[-1].endswith(".jsonl"))

    def test_caminhos_locais(self):
        rd = naming.run_dir("main", "c217", data_root="data")
        self.assertEqual(rd, os.path.join("data", "experiments", "main", "c217"))
        lp = naming.layer_path("main", "c217", "DTLZ2", 0, "surrogate", data_root="data")
        self.assertEqual(lp, os.path.join(rd, "exp_main_c217_DTLZ2_0__surrogate.parquet"))

    def test_token_exp(self):
        # O token {exp} separa principal × sub-estudos (D55).
        self.assertTrue(naming.is_valid_exp("main"))
        self.assertTrue(naming.is_valid_exp("off"))
        self.assertTrue(naming.is_valid_exp("batch"))
        self.assertEqual(naming.sweep_exp("small", "LHS"), "sweep-small-LHS")
        self.assertTrue(naming.is_valid_exp("sweep-small-LHS"))
        self.assertFalse(naming.is_valid_exp("bogus"))
        # off e sweep do MESMO (alg,prob,sem) NÃO colidem:
        self.assertNotEqual(naming.base("off", "b5r", "ZDT1", 0),
                            naming.base("sweep-small-LHS", "b5r", "ZDT1", 0))

    def test_blob_gcs(self):
        self.assertEqual(naming.blob_prefix("main", "c262"),
                         "experiments/main/c262")
        fn = naming.layer_filename("main", "c262", "MMF1", 0, "real")
        self.assertEqual(naming.blob_path("main", "c262", fn),
                         f"experiments/main/c262/{fn}")

    def test_camada_invalida_estoura(self):
        with self.assertRaises(ValueError):
            naming.layer_filename("main", "c217", "DTLZ2", 0, "bogus")
        with self.assertRaises(ValueError):
            naming.run_id("expX", "c217", "DTLZ2", 0)


if __name__ == "__main__":
    unittest.main()
