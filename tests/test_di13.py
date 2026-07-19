# -*- coding: utf-8 -*-
"""Regressões da DI-13 (decisões do autor, 2026-07-19).

DI-13.1 · o despachante MESCLA o manifesto do runner (nunca reconstrói).
DI-13.2 · `tempo_fit_s` aceita NULL (pisos não treinam) e o writer não estoura.
DI-13.5 · a sonda: artefato de 20.000 ANINHADO — as 2.000 primeiras são as do online.
"""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDI13_1_MesclaManifesto(unittest.TestCase):
    def test_mescla_preserva_payload_do_runner(self):
        import experiments
        from src import naming
        from src.manifest import new_manifest, write_manifest
        d = tempfile.mkdtemp()
        rich = new_manifest('main', 'fake', 'MMF1', 0, status='ok', data_root=d)
        rich.update({'doe_hash': 'ABC', 'fe_final': 61, 'n_geracoes': 40,
                     'sigma_dict': {'mu_j': 'x'}, 'sonda': {'blocos': 21},
                     'timing': {'tempo_total_s': 12.5, 'tempo_fit_surrogate_s': 3.0,
                                'tempo_busca_s': 9.0, 'tempo_aval_real_s': 0.5}})
        write_manifest(rich, d)
        experiments._run_one('main', 'fake', 'MMF1', 0, d)   # adapter inexistente ⇒ failed
        m = json.load(open(naming.manifest_path('main', 'fake', 'MMF1', 0, data_root=d)))
        self.assertEqual(m['doe_hash'], 'ABC')               # ← o bug: sumia
        self.assertEqual(m['fe_final'], 61)
        self.assertTrue(m['sigma_dict'] and m['sonda'])
        self.assertEqual(m['timing']['tempo_fit_surrogate_s'], 3.0)  # medida ≠ stub None
        self.assertEqual(m['status'], 'failed')              # o campo do despachante entra
        self.assertIn('tempo_total_despachante_s', m['timing'])

    def test_cria_do_zero_se_runner_nao_gravou(self):
        import experiments
        from src import naming
        d = tempfile.mkdtemp()
        experiments._run_one('main', 'fake', 'MMF1', 0, d)
        m = json.load(open(naming.manifest_path('main', 'fake', 'MMF1', 0, data_root=d)))
        self.assertEqual(m['status'], 'failed')


class TestDI13_2_PisoTimingNull(unittest.TestCase):
    def test_schema_aceita_null_e_writer_grava(self):
        import pyarrow.parquet as pq
        import src.export as E
        f = [x for x in E.timing_schema() if x.name == 'tempo_fit_s'][0]
        self.assertTrue(f.nullable, "pisos precisam de NULL (≠ 0.0) em tempo_fit_s")
        d = tempfile.mkdtemp()
        E.write_timing('main', 'nsga2', 'MMF1', 0, [
            {'geracao': 1, 'n_acumulado': 0, 'tempo_fit_s': None,
             'tempo_busca_s': 0.5, 'tempo_pred_sonda_s': None, 'tempo_geracao_s': 0.7}],
            data_root=d)
        p = [os.path.join(r, fn) for r, _, fs in os.walk(d)
             for fn in fs if fn.endswith('__timing.parquet')][0]
        t = pq.read_table(p)
        self.assertIsNone(t['tempo_fit_s'].to_pylist()[0])   # NULL = não se aplica
        self.assertAlmostEqual(t['tempo_geracao_s'].to_pylist()[0], 0.7, places=5)


class TestDI13_5_SondaAninhada(unittest.TestCase):
    def test_artefato_20k_e_fatia_online_2k(self):
        import glob
        mans = glob.glob('data/sonda/*.manifest.json')
        self.assertEqual(len(mans), 25)
        for f in mans:
            m = json.load(open(f))
            self.assertEqual(m['S'], 20000)
            self.assertEqual(m['S_online'], 2000)
            self.assertIn('x_hash_online', m)

    def test_sobol_e_aninhado(self):
        """A propriedade que sustenta o desenho: 2.000 ⊂ 20.000, bit-a-bit."""
        import numpy as np
        from scipy.stats import qmc
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            a = qmc.Sobol(d=6, scramble=True, seed=12345).random(2000)
            b = qmc.Sobol(d=6, scramble=True, seed=12345).random(20000)[:2000]
        self.assertEqual(np.abs(a - b).max(), 0.0)


if __name__ == '__main__':
    unittest.main()
