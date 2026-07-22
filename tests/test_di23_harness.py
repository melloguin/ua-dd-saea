# -*- coding: utf-8 -*-
"""[DI-23, torre 2026-07-22] Testes das correções pós-validação do R3-c149.

- **§3.3** `write_run_outputs(status=, motivo_parada=)`: o carimbo deixou de
  ser `'ok'` hard-coded — um aborto por teto/cache-cap grava manifesto HONESTO
  (a exposição que o c122 herdava; o c149 contornava reescrevendo).
- **§3.4** `emit_sonda_block(c3=...)`: as colunas DEF-C3 entram pelo helper —
  configs futuros com espaço transformado não precisam do carimbo pós-hoc.
"""
from __future__ import annotations

import json
import os
import tempfile
import types
import unittest

import numpy as np

from src import naming
from src.budget import RealEval
from src.standalone_harness import SnapshotBuffer, emit_sonda_block, write_run_outputs


def _bud_fake(D=2, M=2, n=3):
    """FEBudget mínimo p/ o plumbing do write_run_outputs (sem rodar nada)."""
    rng = np.random.RandomState(0)
    recs = [RealEval(solution_id=i, x=rng.rand(D), f=rng.rand(M),
                     fe_index=i, fase="init") for i in range(n)]
    X0 = np.vstack([r.x for r in recs])
    return types.SimpleNamespace(records=recs, maxfe=n, fe=n, cache_hits=0,
                                 init_X=lambda: X0)


def _fechar(root, *, status="ok", motivo=None):
    from src import doe as _doe
    bud = _bud_fake()
    buf = SnapshotBuffer()
    buf.add_pop(1, [r.solution_id for r in bud.records])
    buf.add_timing(1, 3, tempo_fit_s=0.1, tempo_busca_s=0.2,
                   tempo_pred_sonda_s=0.0, tempo_geracao_s=0.3)
    kw = {} if motivo is None else {"motivo_parada": motivo}
    return write_run_outputs(
        "main", "stubdi23", "MMF1", 0, bud, buf, D=2, M=2,
        cp_hashes={"doe_hash": _doe.decoded_hash(bud.init_X())},
        env={}, pinning={}, n_geracoes=1, algo_version="t",
        timing_totais={"tempo_total_s": 1.0, "tempo_fit_surrogate_s": 0.1,
                       "tempo_busca_s": 0.2, "tempo_aval_real_s": 0.1},
        sigma_dict={"nota": "teste"}, regime="online",
        status=status, data_root=root, **kw)


class TestStatusNoManifesto(unittest.TestCase):
    def test_default_segue_ok(self):
        with tempfile.TemporaryDirectory() as root:
            _fechar(root)
            man = json.load(open(naming.manifest_path("main", "stubdi23",
                                                      "MMF1", 0, root)))
            self.assertEqual(man["status"], "ok")
            self.assertNotIn("motivo_parada", man)

    def test_aborto_grava_failed_e_motivo(self):
        with tempfile.TemporaryDirectory() as root:
            _fechar(root, status="failed", motivo="teto_wall")
            man = json.load(open(naming.manifest_path("main", "stubdi23",
                                                      "MMF1", 0, root)))
            self.assertEqual(man["status"], "failed")
            self.assertEqual(man["motivo_parada"], "teto_wall")
            # e o resume NUNCA lê este run como pronto:
            from src.manifest import is_run_done
            self.assertFalse(is_run_done("main", "stubdi23", "MMF1", 0, root))

    def test_c122_passa_status_real(self):
        """O call-site do c122 agora repassa status/motivo (cumpre o docstring)."""
        src = open("src/c122_thetadeadp.py", encoding="utf-8").read()
        self.assertIn("status=status, motivo_parada=motivo_parada", src)


class TestC3NoEmitSonda(unittest.TestCase):
    def test_c3_entra_nas_linhas_do_bloco(self):
        buf = SnapshotBuffer()
        log = types.SimpleNamespace(event=lambda *a, **k: None)
        X = np.random.RandomState(1).rand(5, 2)
        sonda = {"X": X, "x_hash": "h1", "f_hash": "h2"}
        emit_sonda_block(
            buf, log, geracao=1, fe=10, sonda=sonda,
            predict=lambda Xc: (np.zeros((len(Xc), 2)),
                                np.ones((len(Xc), 2))),
            fe_treino_max=9, modelo_flag="GP-teste",
            # transf_params = DICT (string = duplo-encode; agora falha-alto, DI-24)
            c3={"espaco_modelo": "cru", "transf_tipo": "zscore",
                "transf_params": {"mu": [0, 0]}})
        self.assertEqual(len(buf.surr_rows), 5)
        for r in buf.surr_rows:
            self.assertEqual(r["espaco_modelo"], "cru")
            self.assertEqual(r["transf_tipo"], "zscore")

    def test_sem_c3_segue_como_antes(self):
        buf = SnapshotBuffer()
        log = types.SimpleNamespace(event=lambda *a, **k: None)
        X = np.random.RandomState(1).rand(4, 2)
        emit_sonda_block(
            buf, log, geracao=1, fe=10, sonda={"X": X, "x_hash": "h1", "f_hash": "h2"},
            predict=lambda Xc: (np.zeros((len(Xc), 2)), None),
            fe_treino_max=9)
        self.assertEqual(len(buf.surr_rows), 4)
        self.assertIsNone(buf.surr_rows[0].get("espaco_modelo"))


if __name__ == "__main__":
    unittest.main()


class TestGuardaTransfParamsString(unittest.TestCase):
    """[DI-24] transf_params STRING falha-ALTO (duplo-encode silencioso morto)."""

    def test_string_levanta(self):
        from src import export
        with self.assertRaises(ValueError):
            export.surrogate_row(1, np.zeros(2), regime="online",
                                 transf_params='{"mu": [0, 0]}')

    def test_dict_segue_ok(self):
        from src import export
        r = export.surrogate_row(1, np.zeros(2), regime="online",
                                 transf_params={"mu": [0, 0]})
        self.assertEqual(json.loads(r["transf_params"]), {"mu": [0, 0]})
