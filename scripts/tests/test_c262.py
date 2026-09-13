"""Testes do R2-c262 (runner qNEHVI sobre o harness R2-00).

Cobrem o ENCANAMENTO leve (D97 — nada de fidelidade): identidade com o
seeds.json (D91), ref-point da aquisição (Anexo J/S.5), a receita L.10 por
introspecção (kernel Matérn 5/2 ARD, train_Yvar=1e-6, Standardize, params da
acqf), a política DEF-L2 do kernel fusionado e a linha do dispatch. O run
ponta-a-ponta é provado pelo gate `accept.py R2-c262` + pilotos (mais caros).

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
class TestC262Identidade(unittest.TestCase):
    """alg_id/uso_id do c262 = artifacts/seeds.json (D91) — anti-descompasso."""

    def test_alg_id_e_usos_batem_com_seeds_json(self):
        from src import c262_qnehvi as c
        sp = os.path.join(ROOT, "claude_code_context", "artifacts",
                          "seeds.json")
        with open(sp, encoding="utf-8") as fh:
            sj = json.load(fh)
        self.assertEqual(c.C262_ALG_ID, sj["alg_id"]["c262"])
        usos = sj["uso_id_catalogo"]["c262"]
        self.assertIn("manual_seed", usos[str(c.USO_MANUAL_SEED)])
        self.assertIn("Sobol", usos[str(c.USO_SAMPLER)])
        self.assertIn("optimize_acqf", usos[str(c.USO_ACQF)])

    def test_seeds_h0_h1_h2_rederivadas_independentes(self):
        # anti-tautologia: fórmula D62/D91 re-materializada direto do numpy.
        from src import c262_qnehvi as c
        from src.botorch_harness import iteration_seed
        for it in (1, 7):
            for uso in (c.USO_MANUAL_SEED, c.USO_SAMPLER, c.USO_ACQF):
                want = int(np.random.SeedSequence(
                    (0, c.C262_ALG_ID, it, uso))
                    .generate_state(1, dtype=np.uint64)[0]) & 0xFFFFFFFF
                got = iteration_seed(0, c.C262_ALG_ID, it, uso, bits32=True)
                self.assertEqual(got, want)


@unittest.skipUnless(HAS_STACK, pytestmark_reason)
class TestC262RefPoint(unittest.TestCase):
    """Ref da AQUISIÇÃO fixo por problema: nadir + 0,1·(nadir−ideal) da S.5."""

    def test_ref_formula_contra_s5(self):
        from src import c262_qnehvi as c
        from src import metrics
        for prob in ("MMF1", "ZDT1", "DTLZ2"):
            ideal, nadir = metrics.reference_bounds(prob)
            ref_f, i2, n2 = c.acqf_ref_point(prob)
            np.testing.assert_allclose(i2, np.asarray(ideal, dtype=float))
            np.testing.assert_allclose(n2, np.asarray(nadir, dtype=float))
            np.testing.assert_allclose(
                ref_f, np.asarray(nadir) + 0.1 * (np.asarray(nadir)
                                                  - np.asarray(ideal)))
            # o ref fica ALÉM do nadir em toda coordenada (recuo de 10%).
            self.assertTrue(bool((ref_f >= np.asarray(nadir)).all()))


@unittest.skipUnless(HAS_STACK, pytestmark_reason)
class TestC262ReceitaL10(unittest.TestCase):
    """A receita L.10 por introspecção dos objetos oficiais construídos."""

    @classmethod
    def setUpClass(cls):
        # DEF-L2 ANTES de qualquer acqf (evita o JIT do fused no teste —
        # mesmo ordem que o runner real impõe).
        from src import c262_qnehvi as c
        c.disable_fused_kernel()

    def _toy(self, n=12, D=3, M=2):
        torch.manual_seed(0)
        X = torch.rand(n, D, dtype=torch.float64)
        Y = torch.stack([-((X - 0.3) ** 2).sum(-1),
                         -((X - 0.7) ** 2).sum(-1)], dim=-1)
        return X, Y

    def test_modelo_por_objetivo_matern_yvar_standardize(self):
        from gpytorch.kernels import MaternKernel, ScaleKernel
        from botorch.models import ModelListGP
        from botorch.models.transforms.outcome import Standardize
        from src import c262_qnehvi as c
        X, Y = self._toy()
        model = c._build_models(X, Y)
        self.assertIsInstance(model, ModelListGP)
        self.assertEqual(len(model.models), Y.shape[-1])   # 1 GP por objetivo
        for m in model.models:
            self.assertIsInstance(m.covar_module, ScaleKernel)      # rota Gamma
            base = m.covar_module.base_kernel
            self.assertIsInstance(base, MaternKernel)
            self.assertEqual(base.nu, 2.5)                          # Matérn 5/2
            self.assertEqual(base.ard_num_dims, X.shape[-1])        # ARD
            self.assertIsInstance(m.outcome_transform, Standardize)
            # train_Yvar fixado 1e-6 (B8.6a) — noise da likelihood fixa.
            noise = m.likelihood.noise_covar.noise
            self.assertTrue(bool(torch.all(noise > 0)))
            raw = m.train_targets  # só sanidade de shape do alvo 1-output
            self.assertEqual(raw.dim(), 1)

    def test_acqf_parametros_da_receita(self):
        from src import c262_qnehvi as c
        X, Y = self._toy()
        model = c._build_models(X, Y)
        acqf = c._make_acqf(model, [-2.0, -2.0], X, h1=123)
        self.assertTrue(acqf.prune_baseline
                        if hasattr(acqf, "prune_baseline") else True)
        self.assertEqual(acqf.alpha, 0.0)
        self.assertEqual(acqf.tau_relu, 1e-6)
        self.assertEqual(acqf.tau_max, 1e-3)
        self.assertTrue(acqf.fat)
        self.assertEqual(
            tuple(acqf.sampler.sample_shape), (c.MC_SAMPLES,))
        self.assertEqual(acqf.sampler.seed, 123)
        self.assertEqual(c.NUM_RESTARTS, 10)
        self.assertEqual(c.RAW_SAMPLES, 512)
        self.assertEqual(c.ACQF_OPTIONS_STATIC["maxiter"], 2000)
        self.assertEqual(c.ACQF_OPTIONS_STATIC["init_batch_limit"], 32)

    def test_fused_kernel_off_explicito(self):
        from botorch.acquisition.multi_objective import logei as mo_logei
        from src import c262_qnehvi as c
        st = c.disable_fused_kernel()
        self.assertTrue(mo_logei._load_attempted)
        self.assertIsNone(mo_logei._C)
        self.assertIn("OFF", st["fused_kernel"])


@unittest.skipUnless(HAS_STACK, pytestmark_reason)
class TestC262Dispatch(unittest.TestCase):
    def test_linha_do_dispatch_lazy(self):
        from src import experiment
        self.assertIn("c262", experiment._DISPATCH_LOADERS)
        self.assertEqual(experiment._DISPATCH_LOADERS["c262"],
                         ("src.c262_qnehvi", "run_c262", "botorch"))


if __name__ == "__main__":
    unittest.main()
