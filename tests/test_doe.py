"""Testes do gerador de inicialização (cartão F0-02-doe): DoE-maximin (D87),
dataset offline (D90), seeds.json (D91) e o hash do array decodificado.

Requerem numpy+pyarrow+pymoo (env-main). No `python3` base (sem essas libs) os
testes são PULADOS — o `discover` do F0-01 continua verde. Sob o interpretador
env-main (PY), rodam de fato.
"""
import hashlib
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import numpy as np  # noqa: F401
    import pyarrow  # noqa: F401
    import pymoo  # noqa: F401
    from src import doe, naming
    from src import problems as P
    _HAVE_STACK = True
except Exception:  # noqa: BLE001
    _HAVE_STACK = False


@unittest.skipUnless(_HAVE_STACK, "requer numpy+pyarrow+pymoo (env-main)")
class TestDoE(unittest.TestCase):

    def test_reproducible_same_hash(self):
        # A âncora exata do F0: 2 chamadas = mesmo hash do array decodificado.
        for prob, sem in (("MMF1", 0), ("DTLZ2", 7), ("ZDT4", 42)):
            h1 = doe.decoded_hash(doe.generate_doe(prob, sem)[0])
            h2 = doe.decoded_hash(doe.generate_doe(prob, sem)[0])
            self.assertEqual(h1, h2, f"{prob}/{sem} não reprodutível")

    def test_bounds_size_and_maxfe(self):
        for prob in ("MMF1", "ZDT4", "WFG9"):
            X, meta = doe.generate_doe(prob, 0)
            p = doe._instantiate_problem(prob)
            D = p.n_var
            self.assertEqual(X.shape, (11 * D - 1, D))
            self.assertEqual(meta["maxfe"], 31 * D - 1)
            xl, xu = np.asarray(p.xl), np.asarray(p.xu)
            self.assertTrue((X >= xl - 1e-12).all() and (X <= xu + 1e-12).all())

    def test_distinct_seed_and_problem(self):
        h00 = doe.decoded_hash(doe.generate_doe("MMF1", 0)[0])
        h01 = doe.decoded_hash(doe.generate_doe("MMF1", 1)[0])
        h10 = doe.decoded_hash(doe.generate_doe("MMF4", 0)[0])
        self.assertNotEqual(h00, h01)
        self.assertNotEqual(h00, h10)

    def test_decoded_hash_matches_spec_formula(self):
        X, _ = doe.generate_doe("MMF1", 0)
        want = hashlib.sha256(
            np.ascontiguousarray(X, dtype="<f8").tobytes()).hexdigest()
        self.assertEqual(doe.decoded_hash(X), want)

    def test_roundtrip_and_idempotent(self):
        with tempfile.TemporaryDirectory() as dr:
            r = doe.ensure_doe("MMF1", 0, data_root=dr)
            self.assertFalse(r["skipped"])
            # relê o parquet e re-hasheia — bit-a-bit igual ao sidecar
            back = doe._read_matrix_parquet(r["path"], r["columns"])
            self.assertEqual(doe.decoded_hash(back), r["doe_hash"])
            again = doe.ensure_doe("MMF1", 0, data_root=dr)
            self.assertTrue(again["skipped"])
            self.assertEqual(again["doe_hash"], r["doe_hash"])

    def test_dataset_F_reproduces_and_size(self):
        X, F, meta = doe.generate_dataset("MMF1", 0)
        D = doe._instantiate_problem("MMF1").n_var
        self.assertEqual(X.shape[0], 31 * D - 1)
        F_re = P.evaluate_problem(doe._instantiate_problem("MMF1"), X)
        self.assertEqual(doe.decoded_hash(F), doe.decoded_hash(F_re))
        self.assertEqual(meta["sampler"], "lhs-maximin")

    def test_dataset_naming_main_vs_sweep(self):
        with tempfile.TemporaryDirectory() as dr:
            main = doe.ensure_dataset("MMF1", 0, data_root=dr)  # small/lhs
            self.assertTrue(main["path"].endswith("ds_MMF1_0.parquet"))
            med = doe.ensure_dataset("MMF1", 0, tier="medium", dist="lhs",
                                     data_root=dr)
            self.assertTrue(med["path"].endswith("ds_MMF1_0_medium_lhs.parquet"))

    def test_sampler_paths(self):
        _, _, mm = doe.generate_dataset("MMF1", 0, tier="medium", dist="lhs")
        self.assertEqual((mm["sampler"], mm["n"]), ("lhs-maximin", 2000))
        _, _, mv = doe.generate_dataset("MMF1", 0, tier="small", dist="mvns")
        self.assertEqual(mv["sampler"], "mvns")
        _, _, mb = doe.generate_dataset("MMF1", 0, tier="big", dist="lhs")
        self.assertEqual((mb["sampler"], mb["n"]), ("lhs-simple", 50000))

    def test_seed_tuple_no_alg_id(self):
        # DoE = (semente, problema_id); dataset = (+tier_id, dist_id). Sem alg_id.
        _, dm = doe.generate_doe("ZDT1", 3)
        self.assertEqual(dm["seed_tuple"], [3, doe.PROBLEMA_ID["ZDT1"]])
        _, _, sm = doe.generate_dataset("ZDT1", 3, tier="small", dist="lhs")
        self.assertEqual(sm["seed_tuple"],
                         [3, doe.PROBLEMA_ID["ZDT1"], 0, 0])

    def test_seeds_json_publishes_maps(self):
        sp = os.path.join(ROOT, "claude_code_context", "artifacts", "seeds.json")
        sj = json.load(open(sp, encoding="utf-8"))
        shared = sj["shared_init_artifacts"]
        self.assertEqual(shared["problema_id"], doe.PROBLEMA_ID)
        self.assertEqual(shared["tier_id"], doe.TIER_ID)
        self.assertEqual(shared["dist_id"], doe.DIST_ID)
        self.assertEqual(len(sj["alg_id"]), 22)


if __name__ == "__main__":
    unittest.main()
