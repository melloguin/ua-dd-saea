"""Testes do harness transversal R2 (`src/botorch_harness.py` — R2-00-harness).

Unidade dos helpers do contrato N.1 (§22.3): pinning D79, guarda N.2.3, DoE
D63 (carrega/nunca regenera), adapter §5.5 ([0,1]↔nativo, −f, Standardize),
sementes D62/D91/L.10, RNG-guard N.1.3, SnapshotBuffer §17.3 e o wiring lazy
do `experiment.run`. O ponta-a-ponta completo é o gate
`scripts/accept.py R2-00-harness` — aqui são as peças.

No interpretador sem torch/botorch (python3 base) os testes PULAM (o env-main
do Mac os roda — HANDOFF §7.1).
"""

from __future__ import annotations

import os
import random
import tempfile
import unittest

try:
    import numpy as np
    import torch  # noqa: F401
    import botorch  # noqa: F401
    _HAS_STACK = True
except ImportError:
    _HAS_STACK = False

_SKIP = "stack R2 (torch/botorch) ausente neste interpretador — rode no env-main"


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestPinningEnv(unittest.TestCase):
    def test_pin_runtime_d79(self):
        from src import botorch_harness as bh
        pin = bh.pin_runtime()
        self.assertEqual(pin["torch_num_threads"], 1)
        self.assertEqual(pin["default_dtype"], "torch.float64")
        self.assertEqual(pin["device"], "cpu")
        for v in bh.D79_THREAD_VARS:
            self.assertEqual(os.environ.get(v), "1")
        # idempotente
        self.assertEqual(bh.pin_runtime(), pin)

    def test_env_info_official_botorch(self):
        from src import botorch_harness as bh
        env = bh.env_info()                    # não levanta (0.18.1 oficial)
        self.assertNotEqual(env["botorch"], "Unknown")     # N.2.3 (fork)
        # pin do contrato N.1 (= requirements/env_main.txt); se o autor
        # re-pinar o botorch um dia, esta linha acompanha a decisão (D80).
        self.assertEqual(env["botorch"], "0.18.1")
        for k in ("scipy", "torch", "gpytorch", "pymoo", "numpy"):
            self.assertTrue(env[k])                        # L.18 etc.
        self.assertTrue(env["botorch_record_sha256"])


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestSeeds(unittest.TestCase):
    def test_iteration_seed_matches_seeds_json_formula(self):
        from src import botorch_harness as bh
        want = int(np.random.SeedSequence((0, 9, 3, 1))
                   .generate_state(1, dtype=np.uint64)[0])
        self.assertEqual(bh.iteration_seed(0, 9, 3, 1), want)      # D91
        self.assertEqual(bh.iteration_seed(0, 9, 3, 1, bits32=True),
                         want & 0xFFFFFFFF)                        # trunc 32b

    def test_torch_seed_for_is_deterministic(self):
        from src import botorch_harness as bh
        s1 = bh.torch_seed_for(42, bh.STUBPY_ALG_ID, 7)
        d1 = torch.rand(3).tolist()
        s2 = bh.torch_seed_for(42, bh.STUBPY_ALG_ID, 7)
        d2 = torch.rand(3).tolist()
        self.assertEqual(s1, s2)
        self.assertEqual(d1, d2)               # L.10: mesmo stream por (run,it)
        self.assertLess(s1, 2**32)
        # iterações/usos distintos → sementes distintas
        self.assertNotEqual(s1, bh.torch_seed_for(42, bh.STUBPY_ALG_ID, 8))
        self.assertNotEqual(
            bh.iteration_seed(42, bh.STUBPY_ALG_ID, 7, 0),
            bh.iteration_seed(42, bh.STUBPY_ALG_ID, 7, 1))


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestRngGuard(unittest.TestCase):
    def test_preserve_global_rng_restores(self):
        from src import botorch_harness as bh
        np.random.seed(777)
        random.seed(777)
        np_before = np.random.get_state()
        py_before = random.getstate()
        with bh.preserve_global_rng():
            np.random.seed(0)                  # simula o pymoo re-semeando
            random.seed(0)
            np.random.random(10)
            random.random()
        self.assertTrue(np.array_equal(np_before[1],
                                       np.random.get_state()[1]))  # N.1.3
        self.assertEqual(py_before, random.getstate())


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestDoeLoad(unittest.TestCase):
    def test_load_doe_missing_raises(self):
        from src import botorch_harness as bh
        with tempfile.TemporaryDirectory() as dr:
            with self.assertRaises(FileNotFoundError):     # D63: nunca regenera
                bh.load_doe("MMF1", 0, data_root=dr)

    def test_load_doe_hash_checked(self):
        import json
        from src import botorch_harness as bh
        from src import doe as _doe, naming
        with tempfile.TemporaryDirectory() as dr:
            _doe.ensure_doe("MMF1", 0, data_root=dr)
            art = bh.load_doe("MMF1", 0, data_root=dr)
            self.assertEqual(art["X"].dtype, np.float64)
            self.assertEqual(art["X"].shape[0], 11 * 2 - 1)        # 11D−1, D=2
            # corrompe o sidecar → pára-e-loga (D81)
            mp = naming.doe_manifest_path("MMF1", 0, data_root=dr)
            with open(mp, encoding="utf-8") as fh:
                side = json.load(fh)
            side["doe_hash"] = "0" * 64
            with open(mp, "w", encoding="utf-8") as fh:
                json.dump(side, fh)
            with self.assertRaises(RuntimeError):
                bh.load_doe("MMF1", 0, data_root=dr)


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestAdapter(unittest.TestCase):
    def _mk(self):
        from src import botorch_harness as bh
        from src import budget
        bud = budget.FEBudget(D=2)
        ad = bh.BoTorchProblemAdapter("MMF1", bud)         # bounds ≠ [0,1]
        return bh, bud, ad

    def test_unit_native_bijection(self):
        _, _, ad = self._mk()
        U = np.array([[0.0, 0.0], [1.0, 1.0], [0.25, 0.75]])
        Xn = ad.to_native(U)
        self.assertTrue(np.allclose(Xn[0], ad.xl))
        self.assertTrue(np.allclose(Xn[1], ad.xu))
        self.assertTrue(np.allclose(ad.to_unit(Xn).numpy(), U))    # §5.5

    def test_sign_and_budget(self):
        from src import budget
        _, bud, ad = self._mk()
        u = np.array([0.3, 0.6])
        y = ad.evaluate_unit_max(u)                        # −f, 1 FE
        self.assertEqual(bud.fe, 1)
        x = ad.to_native(u)
        f = ad.evaluate_native(x)                          # cache-hit (mesmo X)
        self.assertEqual(bud.fe, 1)                        # D89: 0 FE
        self.assertTrue(np.allclose(y.numpy().reshape(-1), -f))    # −f (§5.5)
        # hard-stop: esgota e confere BudgetExhausted na inédita
        n = 0
        try:
            while True:
                ad.evaluate_native(ad.xl + (n + 1) * 1e-3 * (ad.xu - ad.xl))
                n += 1
        except budget.BudgetExhausted:
            pass
        self.assertEqual(bud.fe, bud.maxfe)                # D21/D61 exato

    def test_standardize(self):
        _, _, ad = self._mk()
        stdz = ad.make_standardize()
        Y = torch.tensor([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]],
                         dtype=torch.float64)
        Ys, _ = stdz(Y)
        self.assertLess(float(Ys.mean().abs()), 1e-9)      # §5.5: média 0
        self.assertTrue(torch.allclose(                    # §5.5: desvio 1
            Ys.std(dim=0), torch.ones(2, dtype=torch.float64), atol=1e-9))


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestSnapshotBuffer(unittest.TestCase):
    def test_buffer_and_fit_series(self):
        from src import botorch_harness as bh
        from src import export
        buf = bh.SnapshotBuffer()
        buf.add_pop(0, [0, 1, 2])
        buf.add_pop(1, [3])
        buf.add_surrogate(export.surrogate_row(
            1, [0.1, 0.2], mu=[1.0, 2.0], sigma=[0.1, 0.2],
            pred_tipo="valor", modelo_flag="GP-stub"))
        buf.add_timing(1, n_acumulado=22, tempo_fit_s=0.01,
                       tempo_busca_s=0.02)
        self.assertEqual(buf.pop_rows, [(0, 0), (0, 1), (0, 2), (1, 3)])
        self.assertEqual(len(buf.surr_rows), 1)
        self.assertEqual(buf.fit_series,
                         [{"iter": 1, "n_acumulado": 22, "tempo_fit_s": 0.01}])


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestDispatchWiring(unittest.TestCase):
    def test_lazy_dispatch_resolves_stubpy(self):
        from src import experiment as _exp
        entry = _exp._resolve_dispatch("stubpy")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["stack"], "botorch")
        self.assertTrue(callable(entry["main"]))
        self.assertIn("stubpy", _exp.ALGORITHM_DISPATCH)   # cacheado
        self.assertIsNone(_exp._resolve_dispatch("nao-existe"))

    def test_unknown_algorithm_raises(self):
        from src import experiment as _exp
        with self.assertRaises(NotImplementedError):
            _exp.run("nao-existe", "MMF1", 0)


if __name__ == "__main__":
    unittest.main()
