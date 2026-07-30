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
        # [T6-batch] sobol_batch DEIXOU de ser exceção — agora tem cartão.
        faltam = self._algs_do_grid() - set(portao.CARTAO_POR_ALG)
        self.assertFalse(faltam, f"configs do grid SEM cartão no portão: {faltam}")

    def test_sobol_batch_tem_cartao_do_batch(self):
        self.assertEqual(portao.CARTAO_POR_ALG["sobol_batch"], "T6-sobol_batch")

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


class TestAbortoSancionadoDI38(unittest.TestCase):
    """[DI-38a] teto_wall/cache_hit_travado = estado ESPERADO, não vermelho.

    ⟦ATUALIZADO no T11-G5/G6 — DI-43/44⟧ Quando este teste nasceu, o aborto por
    teto NÃO gravava camada nenhuma (anti-órfão DI-21), então a célula sancionada
    não tinha o que gatear e o portão devolvia UMA linha. Com o
    truncamento-com-dado a célula PASSA A TER camadas parciais — e dado sem
    proveniência é exatamente o que a campanha T11 existe para matar. Contrato
    novo: o sancionado dispensa os gates de CONTEÚDO (accept/auditar/final_eval)
    e continua passando pelos de PROVENIÊNCIA (G-1..G-4 + B-15)."""

    def _run_fake(self, tmp, motivo="teto_wall", status="failed"):
        import json
        from src import naming
        exp, alg, prob, sem = "batch", "c154", "DTLZ2", 42
        mp = naming.manifest_path(exp, alg, prob, sem, data_root=tmp)
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        with open(mp, "w", encoding="utf-8") as fh:
            json.dump({"exp": exp, "alg": alg, "problema": prob,
                       "semente": sem, "status": status, "q": 10,
                       "motivo_parada": motivo, "fe_final": 240,
                       "maxfe": 2131}, fh)
        return exp, alg, prob, sem

    def test_portao_reporta_sancionado_sem_gatear(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            exp, alg, prob, sem = self._run_fake(tmp)
            res = portao.gates_de_um_run(exp, alg, prob, sem, data_root=tmp)
            nome, ok, det = res[0]
            self.assertEqual(nome, "aborto-sancionado")
            self.assertTrue(ok)
            self.assertIn("teto_wall", det)
            # os gates de CONTEÚDO ficam de fora; os de PROVENIÊNCIA, não
            nomes = [n for n, _, _ in res]
            self.assertNotIn("auditar", nomes)
            self.assertFalse([n for n in nomes if n.startswith("accept[")])
            self.assertIn("G-1 3x1", nomes)
            self.assertIn("G-2 sexto", nomes)

    def test_portao_failed_nao_sancionado_gateia_normal(self):
        # um failed comum (crash) NÃO ganha o carve-out — os gates rodam e acusam
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            exp, alg, prob, sem = self._run_fake(tmp, motivo="excecao")
            res = portao.gates_de_um_run(exp, alg, prob, sem, data_root=tmp)
            self.assertNotEqual(res[0][0], "aborto-sancionado")

    def test_check_fe_skipa_sancionado_sem_camada_1(self):
        # check_fe: SKIP (None) ANTES do check de camada ① — a ① ausente no
        # rito BoTorch é por desenho, não falha.
        import importlib.util as u
        import tempfile
        spec = u.spec_from_file_location(
            "accept_mod", os.path.join(ROOT, "scripts", "accept.py"))
        acc = u.module_from_spec(spec)
        spec.loader.exec_module(acc)
        with tempfile.TemporaryDirectory() as tmp:
            exp, alg, prob, sem = self._run_fake(tmp)
            ok, msg = acc.check_fe(exp, alg, prob, sem, 12, data_root=tmp)
            self.assertIsNone(ok, msg)
            self.assertIn("sancionado", msg)


if __name__ == "__main__":
    unittest.main()
