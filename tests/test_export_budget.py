"""Testes do cartão F0-03-export: wrapper de FE (`src.budget`), export das 3
camadas + timing (`src.export`) e a ponte GCS (`src.gcs`).

- `src.gcs` é **stdlib puro** (só nomes/plano; import LAZY do google-cloud) →
  a classe de GCS roda em QUALQUER interpretador, inclusive o `python3` base.
- `src.budget` requer numpy; `src.export` requer numpy+pyarrow → PULADOS sem
  o env-main (como o `test_doe.py`).
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    import numpy as np  # noqa: F401
    from src import budget
    _HAVE_NP = True
except Exception:  # noqa: BLE001
    _HAVE_NP = False

try:
    import numpy as np  # noqa: F811
    import pyarrow  # noqa: F401
    import pyarrow.parquet as pq
    from src import export, naming
    _HAVE_STACK = True
except Exception:  # noqa: BLE001
    _HAVE_STACK = False


# ── src.gcs (stdlib puro — sempre roda) ─────────────────────────────────────

class TestGCS(unittest.TestCase):

    def setUp(self):
        from src import gcs
        self.gcs = gcs

    def test_bucket_only_lista_exata(self):
        # A lista EXATA da D58 (CLAUDE.md §5): c154,c122,e81,c149,c262.
        self.assertEqual(self.gcs.BUCKET_ONLY_ALGS,
                         frozenset({"c154", "c122", "e81", "c149", "c262"}))
        for a in ("c154", "c122", "e81", "c149", "c262"):
            self.assertTrue(self.gcs.is_bucket_only(a))          # ③ é bucket-only
            self.assertFalse(self.gcs.is_bucket_only(a, "real"))  # ①② não
        for a in ("c217", "b1", "e103", "b5"):
            self.assertFalse(self.gcs.is_bucket_only(a))

    def test_plan_local_only_sem_rede(self):
        # Mac/MATLAB: enable_bucket=False → tudo local, blob=None (não fala rede).
        plan = self.gcs.plan_targets("main", "stub", "MMF1", 0,
                                     enable_bucket=False, data_root="/tmp/x")
        self.assertEqual(set(plan),
                         set(naming.LAYERS) | {"jsonl", "manifest"}
                         if _HAVE_STACK else
                         {"real", "pop", "surrogate", "timing", "jsonl", "manifest"})
        for tgt in plan.values():
            self.assertIsNone(tgt["blob"])
            self.assertFalse(tgt["bucket_only"])
            self.assertTrue(tgt["local"].startswith("/tmp/x"))

    def test_plan_bucket_marca_surrogate_bucket_only(self):
        # VM: enable_bucket=True, alg bucket-only → só a ③ é bucket_only; blobs c/
        # o prefixo experiments/{exp}/{alg}/ (§17.7).
        plan = self.gcs.plan_targets("main", "c149", "ZDT1", 0,
                                     enable_bucket=True, data_root="data")
        self.assertTrue(plan["surrogate"]["bucket_only"])
        self.assertFalse(plan["real"]["bucket_only"])
        self.assertTrue(plan["surrogate"]["blob"].startswith(
            "experiments/main/c149/"))
        # alg NÃO bucket-only: nenhuma camada é bucket_only, mas há blob (dual).
        plan2 = self.gcs.plan_targets("main", "c217", "ZDT1", 0,
                                      enable_bucket=True, data_root="data")
        self.assertFalse(plan2["surrogate"]["bucket_only"])
        self.assertIsNotNone(plan2["surrogate"]["blob"])

    def test_import_lazy_client_falha_clara_sem_lib(self):
        # Sem a lib de gcs no env → _client levanta RuntimeError claro (nunca
        # um ImportError cru). Se a lib existir (env R2+/VM — o stack do R2-00
        # a inclui no env-main), pulamos: nada a afirmar.
        # [R2-00-harness] o skipTest ficava DENTRO do try e o `except Exception`
        # engolia o SkipTest (que herda de Exception) → falha espúria assim que
        # a lib foi instalada; o intent (skip com lib presente) é o mesmo.
        try:
            import google.cloud.storage  # noqa: F401
            have_lib = True
        except ImportError:
            have_lib = False
        if have_lib:
            self.skipTest("google-cloud-storage presente (env R2/VM) — "
                          "nada a afirmar")
        with self.assertRaises(RuntimeError):
            self.gcs._client()


# ── src.budget (numpy) ──────────────────────────────────────────────────────

@unittest.skipUnless(_HAVE_NP, "requer numpy (env-main)")
class TestBudget(unittest.TestCase):

    @staticmethod
    def _f(x):
        return np.array([float(np.sum(x)), float(np.sum(x ** 2))])

    def test_hard_stop_exato(self):
        D = 2
        bud = budget.FEBudget(D=D)
        self.assertEqual(bud.maxfe, 61)          # 31·2−1
        for i in range(61):
            bud.evaluate(np.array([i * 1.0, i * 2.0]), self._f)
        self.assertEqual(bud.fe, 61)
        with self.assertRaises(budget.BudgetExhausted):
            bud.evaluate(np.array([999.0, 998.0]), self._f)  # X inédita, saldo 0
        self.assertEqual(bud.fe, 61)             # a falha não moveu o saldo

    def test_cache_hit_zero_fe_e_mesmo_id(self):
        bud = budget.FEBudget(D=3)
        x = np.array([0.1, 0.2, 0.3])
        f1 = bud.evaluate(x, self._f)
        self.assertEqual(bud.fe, 1)
        f2 = bud.evaluate(x.copy(), self._f)     # bit-idêntico → cache-hit
        self.assertEqual(bud.fe, 1)              # 0 FE (D89)
        self.assertEqual(bud.cache_hits, 1)
        np.testing.assert_array_equal(f1, f2)
        self.assertEqual(bud.solution_id_of(x), 0)

    def test_near_duplicata_paga_1_fe(self):
        # D89: identidade é X NATIVO bit-a-bit; 1 ULP de diferença = OUTRA solução.
        bud = budget.FEBudget(D=1)
        x = np.array([0.3])
        bud.evaluate(x, self._f)
        x2 = np.array([np.nextafter(0.3, 1.0)])  # +1 ULP
        bud.evaluate(x2, self._f)
        self.assertEqual(bud.fe, 2)              # near-dup pagou 1 FE
        self.assertEqual(bud.cache_hits, 0)

    def test_solution_id_incremental_e_dedup(self):
        bud = budget.FEBudget(D=2)
        ids = [bud.evaluate(np.array([i * 1.0, 0.0]), self._f) is not None
               for i in range(5)]
        self.assertTrue(all(ids))
        self.assertEqual([r.solution_id for r in bud.records], [0, 1, 2, 3, 4])

    def test_fase_init_opt(self):
        D = 2
        bud = budget.FEBudget(D=D)               # n_init = 21
        for i in range(30):
            bud.evaluate(np.array([i * 1.0, i * 3.0]), self._f)
        fases = [r.fase for r in bud.records]
        self.assertEqual(fases[:21], ["init"] * 21)
        self.assertEqual(fases[21:], ["opt"] * 9)

    def test_init_X_float64_e_hash_estavel(self):
        bud = budget.FEBudget(D=2)               # n_init = 21
        for i in range(25):
            bud.evaluate(np.array([i * 0.5, i * 0.25]), self._f)
        X0 = bud.init_X()
        self.assertEqual(X0.shape, (21, 2))
        self.assertEqual(X0.dtype, np.dtype("float64"))
        # o hash é o do array float64 (o que o CP-init compara).
        import hashlib
        h = hashlib.sha256(np.ascontiguousarray(X0, "<f8").tobytes()).hexdigest()
        self.assertEqual(len(h), 64)

    def test_cache_hit_livre_apos_esgotar(self):
        bud = budget.FEBudget(D=1)               # maxfe = 30
        for i in range(30):
            bud.evaluate(np.array([i * 1.0]), self._f)
        self.assertTrue(bud.exhausted)
        # re-consultar um X já avaliado é livre mesmo com o saldo zerado (D89).
        f = bud.evaluate(np.array([0.0]), self._f)
        self.assertIsNotNone(f)
        self.assertEqual(bud.fe, 30)
        self.assertEqual(bud.cache_hits, 1)


# ── src.export (numpy + pyarrow) ────────────────────────────────────────────

@unittest.skipUnless(_HAVE_STACK, "requer numpy+pyarrow (env-main)")
class TestExport(unittest.TestCase):

    def _records(self, D=2, M=2, n=61):
        recs = []
        for i in range(n):
            x = np.array([i * 0.123456789 + 0.000001 * j for j in range(D)],
                         dtype=np.float64)
            f = np.array([float(i + j) for j in range(M)], dtype=np.float64)
            fase = "init" if i < 11 * D - 1 else "opt"
            recs.append(budget.RealEval(i, x, f, i, fase))
        return recs

    def test_schemas_nomes_e_tipos(self):
        import pyarrow as pa
        rs = export.real_schema(2, 3)
        self.assertEqual(rs.names,
                         ["algoritmo", "problema", "semente", "solution_id",
                          "x0", "x1", "f0", "f1", "f2", "fe_index", "fase"])
        self.assertEqual(rs.field("x0").type, pa.float32())
        self.assertEqual(rs.field("solution_id").type, pa.int32())
        ss = export.surrogate_schema(2, 2)
        for c in ("mu_0", "mu_1", "sigma_0", "sigma_1", "real_solution_id",
                  "pred_tipo", "pred_classe", "pred_score", "pred_confianca",
                  "modelo_flag", "espaco_modelo", "transf_tipo", "transf_params",
                  "regime"):
            self.assertIn(c, ss.names)
        self.assertTrue(ss.field("mu_0").nullable)         # opcional (DEF-C1)
        self.assertFalse(ss.field("x0").nullable)          # x sempre presente

    def test_real_roundtrip_e_float32(self):
        with tempfile.TemporaryDirectory() as dr:
            recs = self._records(D=2, M=2, n=61)
            p = export.write_real("main", "stub", "MMF1", 0, recs, data_root=dr)
            t = pq.read_table(p)
            self.assertEqual(t.num_rows, 61)
            # float32 SEM arredondamento decimal (D53): o valor lido == cast f32
            # do float64 original (NÃO um round(x,3)).
            got = t.column("x0")[1].as_py()
            want = float(np.float32(recs[1].x[0]))
            self.assertEqual(got, want)
            self.assertNotEqual(round(recs[1].x[0], 3), want)   # não é round3

    def test_surrogate_opcionais_e_mono_output_b1(self):
        with tempfile.TemporaryDirectory() as dr:
            rows = [
                export.surrogate_row(1, [0.1, 0.2], real_solution_id=3,
                                     mu=[0.4, 0.7], sigma=[0.08, 0.05],
                                     pred_tipo="valor", modelo_flag="GP"),
                export.surrogate_row(1, [0.3, 0.4], pred_tipo="classe",
                                     pred_classe="bom", pred_confianca=0.83,
                                     modelo_flag="FNN"),
                # b1 mono-output: mu_0 preenchido, mu_1 NULL (§17.2/D47).
                export.surrogate_row(2, [0.5, 0.6], mu=[1.05], pred_tipo="valor",
                                     modelo_flag="GP",
                                     espaco_modelo="transformado",
                                     transf_tipo="escalar-tcheby",
                                     transf_params={"lambda": [0.5, 0.5]}),
            ]
            p = export.write_surrogate("main", "stub", "MMF1", 0, rows,
                                       D=2, M=2, data_root=dr)
            t = pq.read_table(p).to_pydict()
            # regressor preenche μ, classificador não:
            self.assertAlmostEqual(t["mu_0"][0], 0.4, places=5)
            self.assertIsNone(t["mu_0"][1])
            self.assertEqual(t["pred_classe"][1], "bom")
            self.assertIsNone(t["pred_classe"][0])
            # b1 mono-output: mu_0 preenchido, mu_1 NULL:
            self.assertAlmostEqual(t["mu_0"][2], 1.05, places=5)
            self.assertIsNone(t["mu_1"][2])
            self.assertIn("lambda", t["transf_params"][2])      # C3 (JSON)

    def test_escrita_atomica_sem_tmp(self):
        with tempfile.TemporaryDirectory() as dr:
            export.write_real("main", "stub", "MMF1", 0, self._records(), data_root=dr)
            rundir = naming.run_dir("main", "stub", data_root=dr)
            self.assertFalse([f for f in os.listdir(rundir) if f.endswith(".tmp")])

    def test_codec_zstd(self):
        with tempfile.TemporaryDirectory() as dr:
            p = export.write_real("main", "stub", "MMF1", 0, self._records(),
                                  data_root=dr)
            md = pq.ParquetFile(p).metadata
            codec = md.row_group(0).column(0).compression
            self.assertEqual(codec.lower(), "zstd")

    def test_pop_e_timing(self):
        with tempfile.TemporaryDirectory() as dr:
            pp = export.write_pop("main", "stub", "MMF1", 0,
                                  [(1, 0), (1, 1), (2, 0)], data_root=dr)
            self.assertEqual(pq.read_table(pp).num_rows, 3)
            tp = export.write_timing(
                "main", "stub", "MMF1", 0,
                [{"geracao": 1, "n_acumulado": 21, "tempo_fit_s": 0.01}],
                data_root=dr)
            tt = pq.read_table(tp)
            self.assertEqual(tt.num_rows, 1)
            self.assertEqual(tt.column("run_id")[0].as_py(), "main_stub_MMF1_0")


if __name__ == "__main__":
    unittest.main()
