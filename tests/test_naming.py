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

    def test_parse_sweep_tokens_validos(self):
        # [T7-sweep] O elo que faltava: derivar (tier, dist) do token exp.
        # As 6 combinações do grid (runs_matrix: 18 exp|alg = 90 células/semente).
        for tier in ("small", "medium", "big"):
            for dist in ("lhs", "mvns"):
                exp = naming.sweep_exp(tier, dist)
                self.assertEqual(naming.parse_sweep(exp), (tier, dist),
                                 f"round-trip sweep_exp/parse_sweep falhou p/ {exp}")

    def test_parse_sweep_nao_sweep_devolve_none(self):
        # main/off/batch NÃO são sweep ⇒ (None, None) = "o dataset principal",
        # que é exatamente o que load_dataset já entende (sufixo omitido).
        for exp in ("main", "off", "batch"):
            self.assertEqual(naming.parse_sweep(exp), (None, None))
        # Tokens sem forma de sweep também caem no principal, sem estourar.
        for exp in ("bogus", "sweep", "sweep-small", "", "sweepsmalllhs"):
            self.assertEqual(naming.parse_sweep(exp), (None, None))

    def test_parse_sweep_vocabulario_invalido_estoura(self):
        # A armadilha que o T7 fecha: um token COM forma de sweep mas com
        # tier/dist fora do vocabulário canônico NÃO pode devolver (None, None)
        # — isso recriaria o bug silencioso (rodar sobre o dataset small e
        # gravar sob o nome do sweep). Tem de PARAR (D81).
        for exp in ("sweep-foo-bar", "sweep-small-sobol", "sweep-huge-lhs",
                    "sweep-SMALL-lhs", "sweep-small-LHS"):
            with self.assertRaises(ValueError, msg=f"{exp} deveria estourar"):
                naming.parse_sweep(exp)

    def test_is_main_variant_e_dataset_variant(self):
        # small/lhs É o offline principal (nome SEM sufixo — D90/seeds.json):
        # não existe ds_{p}_{s}_small_lhs.parquet em disco.
        self.assertTrue(naming.is_main_variant("small", "lhs"))
        self.assertTrue(naming.is_main_variant(None, None))
        self.assertFalse(naming.is_main_variant("medium", "lhs"))
        self.assertFalse(naming.is_main_variant("small", "mvns"))
        self.assertFalse(naming.is_main_variant("big", "lhs"))
        # dataset_variant = o que os runners passam a load_offline_budget.
        self.assertEqual(naming.dataset_variant("sweep-small-lhs"), (None, None))
        self.assertEqual(naming.dataset_variant("off"), (None, None))
        self.assertEqual(naming.dataset_variant("sweep-medium-mvns"),
                         ("medium", "mvns"))
        self.assertEqual(naming.dataset_variant("sweep-big-lhs"), ("big", "lhs"))

    def test_dataset_variant_casa_com_o_arquivo_em_disco(self):
        # O par devolvido tem de reconstruir o MESMO nome que doe.ensure_dataset
        # escreve (regra is_main lá; is_main_variant aqui) — se estes dois
        # divergirem, o runner lê um arquivo que ninguém gerou.
        t, d = naming.dataset_variant("sweep-small-lhs")
        self.assertEqual(naming.dataset_filename("MMF1", 42, t, d),
                         "ds_MMF1_42.parquet")
        t, d = naming.dataset_variant("sweep-medium-mvns")
        self.assertEqual(naming.dataset_filename("MMF1", 42, t, d),
                         "ds_MMF1_42_medium_mvns.parquet")

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
