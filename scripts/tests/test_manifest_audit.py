"""Unit-test do manifesto (D58/§17.2), da esteira idempotente e do logger §17.5.

Stdlib puro: `python3 -m unittest discover -s tests`.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import naming, atomic_io, manifest, audit_log


class TestAtomicIO(unittest.TestCase):

    def test_grava_atomico_sem_tmp_residual(self):
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "sub", "a.txt")
            atomic_io.atomic_write_text(p, "olá")
            with open(p, encoding="utf-8") as f:
                self.assertEqual(f.read(), "olá")
            self.assertFalse([f for f in os.listdir(os.path.dirname(p))
                              if f.endswith(".tmp")])

    def test_falha_no_meio_nao_cria_alvo(self):
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "x.txt")
            with self.assertRaises(ValueError):
                with atomic_io.atomic_path(p) as tmp:
                    with open(tmp, "w") as f:
                        f.write("parcial")
                    raise ValueError("boom")
            self.assertFalse(os.path.exists(p))
            self.assertFalse([f for f in os.listdir(dr) if f.endswith(".tmp")])


class TestManifest(unittest.TestCase):

    def test_round_trip_e_paths(self):
        with tempfile.TemporaryDirectory() as dr:
            man = manifest.new_manifest("main", "c217", "DTLZ2", 0, status="ok",
                                        maxfe=464, fe_final=464,
                                        bucket="mestrado_experiments", data_root=dr)
            mp = manifest.write_manifest(man, data_root=dr)
            back = manifest.read_manifest(mp)
            self.assertEqual(back["run_id"], "main_c217_DTLZ2_0")
            self.assertEqual(back["status"], "ok")
            self.assertEqual(set(back["paths"]["local"]),
                             set(naming.LAYERS) | {"jsonl", "manifest"})
            self.assertTrue(back["paths"]["bucket"]["real"].startswith(
                "gs://mestrado_experiments/experiments/main/c217/"))
            self.assertEqual(back["upload_status"]["surrogate"], "pending")

    def test_matlab_sem_bucket(self):
        with tempfile.TemporaryDirectory() as dr:
            man = manifest.new_manifest("main", "e103", "ZDT1", 0, status="ok",
                                        bucket=None, data_root=dr)
            self.assertIsNone(man["paths"]["bucket"])
            self.assertIsNone(man["upload_status"])

    def test_status_invalido_estoura(self):
        with self.assertRaises(ValueError):
            manifest.new_manifest("main", "c217", "DTLZ2", 0, status="bogus")

    def test_is_run_done_exige_manifesto_e_camadas(self):
        with tempfile.TemporaryDirectory() as dr:
            args = ("main", "c217", "DTLZ2", 0)
            self.assertFalse(manifest.is_run_done(*args, data_root=dr))   # nada
            manifest.write_manifest(
                manifest.new_manifest(*args, status="ok", data_root=dr), data_root=dr)
            # manifesto ok mas camadas ausentes → NÃO pronto
            self.assertFalse(manifest.is_run_done(*args, data_root=dr))
            for ly in naming.LAYERS:
                p = naming.layer_path(*args, ly, data_root=dr)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "w").close()
            # sem footers válidos (arquivos vazios), a checagem profunda reprova
            # se pyarrow existir; com check_footers=False é aceito.
            self.assertTrue(manifest.is_run_done(*args, data_root=dr, check_footers=False))

    def test_failed_nao_e_pronto(self):
        with tempfile.TemporaryDirectory() as dr:
            args = ("main", "c217", "DTLZ2", 0)
            manifest.write_manifest(
                manifest.new_manifest(*args, status="failed", data_root=dr), data_root=dr)
            for ly in naming.LAYERS:
                open(naming.layer_path(*args, ly, data_root=dr), "w").close()
            self.assertFalse(manifest.is_run_done(*args, data_root=dr, check_footers=False))


class TestScoreboard(unittest.TestCase):

    def test_conta_e_placar(self):
        sb = manifest.Scoreboard()
        for s in ("ok", "ok", "retried_ok", "failed"):
            sb.record(s)
        sb.record_skip()
        self.assertEqual(sb.ok, 3)
        self.assertEqual(sb.failed, 1)
        self.assertEqual(sb.skipped, 1)
        self.assertIn("failed=1", sb.render())


class TestAuditLog(unittest.TestCase):

    def test_uma_decisao_por_linha(self):
        with tempfile.TemporaryDirectory() as dr:
            with audit_log.AuditLogger.for_run("main", "c217", "DTLZ2", 0,
                                               data_root=dr) as log:
                log.header(D=15, M=3, maxfe=464, doe_hash="deadbeef")
                log.decision(caminho="estado_1", motivo="p_mais=0.86 > delta=0.80")
                log.partial(fe_index=120, nd_size=14)
                log.guard("cache_hit", x_hash="abc")       # D89
                log.timing(n_acumulado=109, tempo_fit_s=0.4)
                log.footer(status="ok", fe_final=464, n_geracoes=37)
            jp = naming.jsonl_path("main", "c217", "DTLZ2", 0, data_root=dr)
            with open(jp, encoding="utf-8") as f:
                lines = [json.loads(l) for l in f]
            self.assertEqual([l["rec"] for l in lines],
                             ["header", "decision", "partial", "guard",
                              "timing", "footer"])
            for l in lines:               # toda linha carrega timestamp
                self.assertIn("ts", l)


if __name__ == "__main__":
    unittest.main()
