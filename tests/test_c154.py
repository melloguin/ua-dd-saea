"""Testes do R2-c154 (runner JES sobre o harness R2-00).

Cobrem o ENCANAMENTO leve (D97 — nada de fidelidade): identidade com o
seeds.json (D91 — alg_id 10 + catálogo de usos 0 / 1..S / S+1..2S), a receita
L.11 por introspecção (modelo SEM train_Yvar = ruído INFERIDO, kernel Matérn
5/2 ARD gamma, Standardize; S=P=10; "LB"; 5D/1000D), a escada de fallback do
RuntimeError (obrigatória — D75/L.11), a política DEF-L2 replicada e a linha
do dispatch. O run ponta-a-ponta é provado pelo gate `accept.py R2-c154` +
pilotos (mais caros).

Como em `test_botorch_harness.py`: pulam limpo sem torch/botorch (python3
base) — a suíte inteira continua verde em qualquer interpretador.
"""

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    import numpy as np
    import torch  # noqa: F401
    import botorch  # noqa: F401
    HAS_STACK = True
except Exception:  # noqa: BLE001 — python3 base: pula tudo
    HAS_STACK = False

pytestmark_reason = "stack R2 (torch/botorch) ausente neste interpretador"


@unittest.skipUnless(HAS_STACK, pytestmark_reason)
class TestC154Identidade(unittest.TestCase):
    """alg_id/uso_id do c154 = artifacts/seeds.json (D91) — anti-descompasso."""

    def test_alg_id_e_catalogo_de_usos_batem_com_seeds_json(self):
        from src import c154_jes as c
        sp = os.path.join(ROOT, "claude_code_context", "artifacts",
                          "seeds.json")
        with open(sp, encoding="utf-8") as fh:
            sj = json.load(fh)
        self.assertEqual(c.C154_ALG_ID, sj["alg_id"]["c154"])
        usos = sj["uso_id_catalogo"]["c154"]
        self.assertIn("manual_seed", usos[str(c.USO_MANUAL_SEED)])
        # catálogo: "1..S" = hs do caminho; "S+1..2S" = hs' do NSGA-II (b).
        self.assertIn("1..S", usos)
        self.assertIn("S+1..2S", usos)
        S = c.NUM_PARETO_SAMPLES
        self.assertEqual(c.uso_path(1), 1)
        self.assertEqual(c.uso_path(S), S)
        self.assertEqual(c.uso_nsgaii(1), S + 1)
        self.assertEqual(c.uso_nsgaii(S), 2 * S)
        for fn in (c.uso_path, c.uso_nsgaii):
            with self.assertRaises(ValueError):
                fn(0)
            with self.assertRaises(ValueError):
                fn(S + 1)

    def test_seeds_rederivadas_independentes(self):
        # anti-tautologia: fórmula D62/D91 re-materializada direto do numpy.
        from src import c154_jes as c
        from src.botorch_harness import iteration_seed
        for it in (1, 7):
            for uso in (0, c.uso_path(1), c.uso_path(10),
                        c.uso_nsgaii(1), c.uso_nsgaii(10)):
                want = int(np.random.SeedSequence(
                    (0, c.C154_ALG_ID, it, uso))
                    .generate_state(1, dtype=np.uint64)[0]) & 0xFFFFFFFF
                got = iteration_seed(0, c.C154_ALG_ID, it, uso, bits32=True)
                self.assertEqual(got, want)


@unittest.skipUnless(HAS_STACK, pytestmark_reason)
class TestC154Receita(unittest.TestCase):
    """A receita L.11 por introspecção (encanamento, não fidelidade)."""

    def test_constantes_da_receita(self):
        from src import c154_jes as c
        self.assertEqual(c.NUM_PARETO_SAMPLES, 10)      # S (paper)
        self.assertEqual(c.NUM_PARETO_POINTS, 10)       # P (paper)
        self.assertEqual(c.ESTIMATION_TYPE, "LB")
        self.assertEqual(c.NUM_RESTARTS_PER_D, 5)       # 5D (paper)
        self.assertEqual(c.RAW_SAMPLES_PER_D, 1000)     # 1000D (paper)
        self.assertEqual(c.RS_FALLBACK_LADDER[0], (1024, 10))  # card/L.11
        self.assertEqual(c.NSGAII_POP, 100)             # D75 (pop-250 morta)
        self.assertEqual(c.NSGAII_GEN, 500)

    def test_modelo_ruido_inferido_kernel_matern_standardize(self):
        # "modelo como o c262 MAS ruído INFERIDO" (L.11/B9.x): sem
        # train_Yvar ⇒ likelihood com noise APRENDÍVEL (não fixado).
        from botorch.models import ModelListGP
        from botorch.models.transforms.outcome import Standardize
        from gpytorch.kernels import MaternKernel, ScaleKernel
        from gpytorch.likelihoods import GaussianLikelihood
        from src.c154_jes import _build_models
        torch.manual_seed(0)
        X = torch.rand(8, 3, dtype=torch.float64)
        Y = torch.rand(8, 2, dtype=torch.float64)
        model = _build_models(X, Y)
        self.assertIsInstance(model, ModelListGP)
        self.assertEqual(len(model.models), 2)
        for m in model.models:
            # ruído INFERIDO: GaussianLikelihood com raw_noise treinável
            # (um FixedNoiseGaussianLikelihood não teria raw_noise assim).
            self.assertIsInstance(m.likelihood, GaussianLikelihood)
            self.assertTrue(m.likelihood.noise_covar.raw_noise.requires_grad)
            k = m.covar_module
            self.assertIsInstance(k, ScaleKernel)
            self.assertIsInstance(k.base_kernel, MaternKernel)
            self.assertEqual(k.base_kernel.nu, 2.5)
            self.assertEqual(k.base_kernel.ard_num_dims, 3)
            self.assertIsInstance(m.outcome_transform, Standardize)

    def test_fallback_ladder_do_runtimeerror(self):
        # a escada (obrigatória — L.11) captura o RuntimeError do
        # random_search e escala; esgotada, propaga (pára-e-loga D81).
        from unittest import mock
        from src import c154_jes as c

        class _Log:
            def __init__(self):
                self.events, self.guards = [], []

            def event(self, kind, **kw):
                self.events.append((kind, kw))

            def guard(self, name, **kw):
                self.guards.append((name, kw))

        calls = []

        def fake_sop(model, bounds, num_samples, num_points, optimizer,
                     maximize, optimizer_kwargs):
            calls.append(dict(optimizer_kwargs))
            if optimizer_kwargs["pop_size"] < 4096:
                raise RuntimeError("Only found 3 optimal points instead of 10.")
            D = bounds.shape[-1]
            return (torch.zeros(1, num_points, D, dtype=torch.float64),
                    torch.zeros(1, num_points, 2, dtype=torch.float64))

        log = _Log()
        with mock.patch(
                "botorch.acquisition.multi_objective.utils."
                "sample_optimal_points", side_effect=fake_sop):
            ps, pf, hs, n_fb = c._sample_pareto_points_rs(
                model=None, D=2, semente=0, it=1, log=log)
        S = c.NUM_PARETO_SAMPLES
        self.assertEqual(tuple(ps.shape), (S, c.NUM_PARETO_POINTS, 2))
        self.assertEqual(len(hs), S)
        # por amostra: degraus (1024,10) e (2048,20) falham → 2 eventos.
        self.assertEqual(n_fb, 2 * S)
        self.assertEqual(len(log.events), 2 * S)
        self.assertEqual(calls[0]["pop_size"], 1024)
        self.assertEqual(calls[1]["pop_size"], 2048)
        self.assertEqual(calls[2]["pop_size"], 4096)

        def always_fail(*a, **kw):
            raise RuntimeError("Only found 1 optimal points instead of 10.")

        log2 = _Log()
        with mock.patch(
                "botorch.acquisition.multi_objective.utils."
                "sample_optimal_points", side_effect=always_fail):
            with self.assertRaises(RuntimeError):
                c._sample_pareto_points_rs(
                    model=None, D=2, semente=0, it=1, log=log2)
        self.assertEqual(len(log2.guards), 1)  # rs_fallback_esgotado

    def test_def_l2_replicada_do_c262(self):
        # a política OFF é a MESMA função do c262 (a chamada de 1 linha que
        # o handoff R2-c262 manda replicar no c154).
        from src import c154_jes, c262_qnehvi
        self.assertIs(c154_jes.disable_fused_kernel,
                      c262_qnehvi.disable_fused_kernel)
        estado = c154_jes.disable_fused_kernel()
        self.assertTrue(estado["_load_attempted"])
        self.assertTrue(estado["_C_is_none"])

    def test_rota_invalida_rejeitada(self):
        from src.c154_jes import run_c154
        with self.assertRaises(ValueError):
            run_c154("main", "c154", "MMF1", 0, rota="z")

    def test_nan_guard_ics(self):
        # o guard troca não-finito pelo pior-finito−1 (só na pontuação de
        # ICs) e conta os fires; tudo-não-finito → piso −1e10 (o fallback
        # aleatório oficial assume via Ystd==0).
        from src.c154_jes import _NaNGuardedAcqfICs

        class _FakeAcqf:
            def __init__(self, out):
                self.out = out

            def __call__(self, X):
                return self.out

        vals = torch.tensor([1.0, float("nan"), 3.0, float("-inf"), 2.0],
                            dtype=torch.float64)
        g = _NaNGuardedAcqfICs(_FakeAcqf(vals))
        out = g(torch.zeros(5, 1, 2, dtype=torch.float64))
        self.assertTrue(bool(torch.isfinite(out).all()))
        self.assertEqual(g.n_nonfinite, 2)
        self.assertEqual(float(out[1]), 0.0)     # pior finito (1.0) − 1
        self.assertEqual(float(out[3]), 0.0)
        np.testing.assert_allclose(out[[0, 2, 4]].numpy(), [1.0, 3.0, 2.0])

        g2 = _NaNGuardedAcqfICs(_FakeAcqf(
            torch.full((4,), float("nan"), dtype=torch.float64)))
        out2 = g2(torch.zeros(4, 1, 2, dtype=torch.float64))
        self.assertTrue(bool((out2 == -1e10).all()))
        self.assertEqual(g2.n_nonfinite, 4)


class TestC154Dispatch(unittest.TestCase):
    """A linha do c154 no _DISPATCH_LOADERS (leve — sem importar torch)."""

    def test_linha_do_dispatch(self):
        from src import experiment
        self.assertIn("c154", experiment._DISPATCH_LOADERS)
        mod, fn, stack = experiment._DISPATCH_LOADERS["c154"]
        self.assertEqual((mod, fn, stack),
                         ("src.c154_jes", "run_c154", "botorch"))
        # o registro segue LAZY: importar experiment não puxa o runner.
        self.assertNotIn("c154", experiment.ALGORITHM_DISPATCH)


if __name__ == "__main__":
    unittest.main()
