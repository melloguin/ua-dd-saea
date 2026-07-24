# -*- coding: utf-8 -*-
"""test_roster_bateria — [DI-31] trava a regressão do bug de roster da bateria.

O `experiments.py` (despachante Python das baterias M8/M9) validava o `--algorithms`
contra um `KNOWN_ALGORITHMS` LITERAL que continha o token-fantasma 'b5' (as chaves
reais são 'b5r'/'b5m') e OMITIA 'moead_media' — a bateria offline M9 era irrodável
(os 3 configs eram rejeitados no parse). Agora o allowlist é DERIVADO dos loaders
reais; estes testes garantem que ele cobre TODOS os configs Python despacháveis e
que o token errado nunca volta.
"""
import unittest

import experiments
from src import experiment


class TestRosterCobreLoaders(unittest.TestCase):
    def test_known_algorithms_e_o_conjunto_dos_loaders_nao_stub(self):
        esperado = {a for a in experiment._DISPATCH_LOADERS
                    if not a.startswith("stub")}
        self.assertEqual(set(experiments.KNOWN_ALGORITHMS), esperado)

    def test_os_4_configs_offline_estao_no_allowlist(self):
        for alg in ("b5r", "b5m", "c311", "moead_media"):
            self.assertIn(alg, experiments.KNOWN_ALGORITHMS,
                          f"{alg} FORA do allowlist ⇒ bateria o rejeitaria")

    def test_token_fantasma_b5_nunca_volta(self):
        self.assertNotIn("b5", experiments.KNOWN_ALGORITHMS)
        self.assertNotIn("b5", experiments.DEFAULT_ALGORITHMS)

    def test_fio_do_q_batch(self):
        """[DI-34] o despachante FIA q=Q_BATCH ao runner em exp=batch — sem
        este fio a bateria batch rodava em q=1 SILENCIOSO (FE=11D−1+200, gates
        passando porque liam o q do próprio manifesto). 3º bug da família da
        camada de lançamento (roster DI-31, transporte E1/T7)."""
        import tempfile
        from unittest import mock
        from src.budget import Q_BATCH
        capturado = {}

        def _fake_run(alg, problema, semente, **kw):
            capturado.update(kw)
            return {"status": "ok"}

        with tempfile.TemporaryDirectory() as td, \
                mock.patch.object(experiments._adapter, "run", _fake_run):
            experiments._run_one("batch", "sobol_batch", "ZDT4", 42, td)
            self.assertEqual(capturado.get("q"), Q_BATCH)
            capturado.clear()
            experiments._run_one("main", "c122", "MMF1", 0, td)
            self.assertNotIn("q", capturado,
                             "exp=main NÃO deve fiar q (q=1 é o default)")

    def test_default_e_coerente_com_exp_main(self):
        # o default do no-arg roda sob DEFAULT_EXP='main' ⇒ só ONLINE
        for off in ("b5r", "b5m", "c311", "moead_media", "e103"):
            self.assertNotIn(off, experiments.DEFAULT_ALGORITHMS)
        self.assertTrue(set(experiments.DEFAULT_ALGORITHMS)
                        <= set(experiments.KNOWN_ALGORITHMS))


if __name__ == "__main__":
    unittest.main()
