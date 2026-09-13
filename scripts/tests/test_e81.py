"""Testes do cartão **R3-e81** (qPOTS) — `src/e81_qpots.py`.

Cobrem, nesta ordem: (1) identidade/artefatos, (2) os TRÊS ganchos sobre o
repo vendorizado (Matérn, offsets D22/A6, instrumentação read-only), (3) o
adapter e a des-padronização μ/σ, (4) as colunas DEF-C3, (5) o contrato do
`select_candidates` (assert |lote|==q, front 1-D).

As **provas caras** (runs completos: determinismo bit-a-bit + não-perturbação
da sonda §3.1) ficam atrás de `E81_SLOW=1` — molde c122/c149.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src import e81_qpots as E                                      # noqa: E402

SLOW = os.environ.get("E81_SLOW") == "1"

try:
    import torch                                                    # noqa: F401
    TEM_TORCH = True
except ImportError:                                                 # pragma: no cover
    TEM_TORCH = False

try:
    sys.path.insert(0, E._repo_root())
    import qpots                                                    # noqa: F401
    TEM_QPOTS = True
except ImportError:                                                 # pragma: no cover
    TEM_QPOTS = False
finally:
    if E._repo_root() in sys.path:
        sys.path.remove(E._repo_root())


def _art(nome):
    with open(os.path.join(ROOT, "claude_code_context", "artifacts", nome),
              encoding="utf-8") as fh:
        return json.load(fh)


class TestIdentidade(unittest.TestCase):
    """O que o runner afirma sobre si tem de bater com os artefatos."""

    def test_alg_id_bate_com_o_artefato(self):
        self.assertEqual(
            E.ALG_ID, _art("seeds.json")["shared_init_artifacts"].get("alg_id",
                        _art("seeds.json").get("alg_id", {})).get("e81",
                        _art("seeds.json").get("alg_id", {}).get("e81")))

    def test_dispatch_registrado(self):
        from src import experiment as exp
        self.assertIn("e81", exp._DISPATCH_LOADERS)
        mod, fn, stack = exp._DISPATCH_LOADERS["e81"]
        self.assertEqual((mod, fn, stack),
                         ("src.e81_qpots", "run_e81", "standalone"))

    def test_env_proprio_no_envs_json(self):
        """e81 roda em env PRÓPRIO (isolamento duro) — nunca no env-main."""
        envs = _art("envs.json")
        self.assertEqual(envs["alg_to_env"]["e81"]["env"], "env_e81_qpots")

    def test_offset_D22_na_base(self):
        """`seed_base('e81', s) == 1000·s` (D22 — e81 e c149 só)."""
        from src import standalone_harness as H
        for s in (0, 1, 7, 28, 42):
            self.assertEqual(H.seed_base("e81", s), 1000 * s)

    def test_os_dois_sitios_de_seed_do_artefato(self):
        """`seeds.json` lista EXATAMENTE os 2 sítios que o runner offseta."""
        off = _art("seeds.json")["offset_D22_hardcoded"]["e81"]
        self.assertEqual(len(off), 2)
        self.assertTrue(any("acquisition.py:219" in s and "1024" in s
                            for s in off))
        self.assertTrue(any("acquisition.py:366" in s and "2430" in s
                            for s in off))
        self.assertEqual(E.SEED_GP_POSTERIOR, 1024)
        self.assertEqual(E.SEED_NSGA2, 2430)

    def test_seed_select_candidates_NAO_e_offsetado(self):
        """O 2043 do `select_candidates` não consta no artefato ⇒ intocado."""
        off = _art("seeds.json")["offset_D22_hardcoded"]["e81"]
        self.assertFalse(any("2043" in s for s in off))
        self.assertEqual(E.SEED_SELECT, 2043)

    def test_config_do_balde(self):
        """ngen=10 (D46), Nyström OFF, q=1 no principal."""
        self.assertEqual(E.NGEN, 10)
        self.assertEqual(E.NYSTROM, 0)
        self.assertEqual(E.Q_PRINCIPAL, 1)
        self.assertEqual(E.MATERN_NU, 2.5)


class TestAncorasDoVendor(unittest.TestCase):
    """As âncoras de patch do `anchors.json` têm de bater com o vendor REAL.

    É o mesmo contrato do patcher (que ABORTA em divergência): se o repo
    vendorizado mudar debaixo do runner, estes testes denunciam antes de
    qualquer run.
    """

    def _linha(self, arquivo, n):
        with open(os.path.join(E._repo_root(), arquivo), encoding="utf-8") as fh:
            return fh.read().splitlines()[n - 1]

    def test_ancoras_e81_conferem(self):
        pats = {p["id"]: p for p in _art("anchors.json")["patches"]
                if p.get("repo") == "e81_qpots"}
        self.assertEqual(set(pats), {"e81-matern", "e81-offset1",
                                     "e81-offset2"})
        for pid, p in pats.items():
            with self.subTest(patch=pid):
                self.assertIn(p["expect_before"],
                              self._linha(p["file"], p["line"]))

    def test_o_stock_NAO_passa_covar_module(self):
        """A razão de existir do patch Matérn: o fit stock cai no RBF default."""
        with open(os.path.join(E._repo_root(), "qpots/model_object.py"),
                  encoding="utf-8") as fh:
            corpo = fh.read()
        inicio = corpo.index("def fit_gp(")
        fim = corpo.index("def fit_multitask_gp(")
        self.assertNotIn("covar_module", corpo[inicio:fim])


@unittest.skipUnless(TEM_TORCH and TEM_QPOTS,
                     "exige o env_e81_qpots (torch + qpots vendorizado)")
class TestGanchos(unittest.TestCase):
    """Os 3 ganchos: aplicam o que prometem E restauram o vendor na saída."""

    def setUp(self):
        self.ctx = E._e81_runtime()
        self.ctx.__enter__()
        import torch
        self.torch = torch

    def tearDown(self):
        self.ctx.__exit__(None, None, None)

    def test_matern_patch_troca_o_kernel_e_restaura(self):
        from gpytorch.kernels import MaternKernel, ScaleKernel
        from gpytorch.priors import GammaPrior
        from qpots import model_object as MO
        from qpots.model_object import ModelObject

        original = MO.SingleTaskGP
        X = self.torch.rand(12, 3, dtype=self.torch.float64)
        Y = self.torch.rand(12, 2, dtype=self.torch.float64)
        B01 = self.torch.stack([self.torch.zeros(3, dtype=self.torch.float64),
                                self.torch.ones(3, dtype=self.torch.float64)])
        with E._silencio(), E._matern_patch(3, self.torch):
            mo = ModelObject(train_x=X, train_y=Y, bounds=B01, nobj=2, ncons=0,
                             device="cpu", dtype=self.torch.float64)
            mo.fit_gp()
        for m in mo.models:
            self.assertIsInstance(m.covar_module, ScaleKernel)
            k = m.covar_module.base_kernel
            self.assertIsInstance(k, MaternKernel)
            self.assertEqual(float(k.nu), 2.5)
            self.assertEqual(int(k.ard_num_dims), 3)     # ARD, não isotrópico
            # os priors fazem parte da decisão (é o que torna a D30 de fato
            # COMPARTILHADA com c262/c154 — não só o `nu`)
            self.assertIsInstance(k.lengthscale_prior, GammaPrior)
            self.assertIsInstance(m.covar_module.outputscale_prior, GammaPrior)
        self.assertIs(MO.SingleTaskGP, original)         # vendor restaurado

    def test_e_o_MESMO_kernel_de_c262_c154(self):
        """A D30 é 'Compartilhado (c262, e81)' ⇒ a construção tem de ser UMA."""
        from botorch.models.utils.gpytorch_modules import (
            get_matern_kernel_with_gamma_prior)
        from qpots import model_object as MO
        from qpots.model_object import ModelObject

        ref = get_matern_kernel_with_gamma_prior(3)
        capt = {}
        original = MO.SingleTaskGP

        def espia(*a, **kw):
            capt["covar"] = kw.get("covar_module")
            return original(*a, **kw)

        MO.SingleTaskGP = espia
        try:
            X = self.torch.rand(12, 3, dtype=self.torch.float64)
            Y = self.torch.rand(12, 2, dtype=self.torch.float64)
            B01 = self.torch.stack([
                self.torch.zeros(3, dtype=self.torch.float64),
                self.torch.ones(3, dtype=self.torch.float64)])
            with E._silencio(), E._matern_patch(3, self.torch):
                ModelObject(train_x=X, train_y=Y, bounds=B01, nobj=2, ncons=0,
                            device="cpu", dtype=self.torch.float64).fit_gp()
        finally:
            MO.SingleTaskGP = original
        got = capt["covar"]
        self.assertEqual(type(got), type(ref))
        self.assertEqual(type(got.base_kernel), type(ref.base_kernel))
        self.assertEqual(float(got.base_kernel.nu), float(ref.base_kernel.nu))
        for attr in ("concentration", "rate"):
            self.assertAlmostEqual(
                float(getattr(got.base_kernel.lengthscale_prior, attr)),
                float(getattr(ref.base_kernel.lengthscale_prior, attr)))
            self.assertAlmostEqual(
                float(getattr(got.outputscale_prior, attr)),
                float(getattr(ref.outputscale_prior, attr)))

    def test_sem_o_patch_o_stock_da_RBF_PURO(self):
        """Prova que é o patch — e não o BoTorch — que traz o Matérn.

        O default do `SingleTaskGP` no BoTorch 0.16.1 é um `RBFKernel` **puro**
        (sem `ScaleKernel`, logo sem outputscale) — é exatamente isso que a
        D30 corrige.
        """
        from gpytorch.kernels import RBFKernel, ScaleKernel
        from qpots.model_object import ModelObject

        X = self.torch.rand(12, 3, dtype=self.torch.float64)
        Y = self.torch.rand(12, 2, dtype=self.torch.float64)
        B01 = self.torch.stack([self.torch.zeros(3, dtype=self.torch.float64),
                                self.torch.ones(3, dtype=self.torch.float64)])
        with E._silencio():
            mo = ModelObject(train_x=X, train_y=Y, bounds=B01, nobj=2, ncons=0,
                             device="cpu", dtype=self.torch.float64)
            mo.fit_gp()
        k = mo.models[0].covar_module
        self.assertIsInstance(k, RBFKernel)
        self.assertNotIsInstance(k, ScaleKernel)

    def test_instrumentacao_offseta_os_2_seeds_e_restaura(self):
        from qpots import acquisition as ACQ
        from qpots.acquisition import Acquisition

        o_post, o_nsga2, o_sel = (Acquisition._gp_posterior, ACQ.nsga2,
                                  ACQ.select_candidates)
        espia = E._Espia()
        vistos = {}

        def fake_nsga2(problem, ngen=100, pop_size=100, seed=2436,
                       callback=None):
            vistos["seed"] = seed
            class _R:                                    # noqa: D401
                X = np.zeros((3, 2))
            return _R()

        ACQ.nsga2 = fake_nsga2
        try:
            with E._instrumentacao(espia, offset=7000, torch=self.torch):
                ACQ.nsga2(None, seed=E.SEED_NSGA2)
        finally:
            ACQ.nsga2 = o_nsga2
        # 2430 + 1000·7 (D22/A6)
        self.assertEqual(vistos["seed"], E.SEED_NSGA2 + 7000)
        self.assertEqual(espia.seed_nsga2, E.SEED_NSGA2 + 7000)
        # vendor restaurado nos TRÊS pontos
        self.assertIs(Acquisition._gp_posterior, o_post)
        self.assertIs(ACQ.select_candidates, o_sel)

    def test_gp_posterior_desloca_o_seed_iter(self):
        """O offset entra deslocando `seed_iter` — o corpo stock fica intacto."""
        from qpots.acquisition import Acquisition

        espia = E._Espia()
        capt = {}
        orig = Acquisition._gp_posterior

        def falso(self, x, gps, seed_iter=1):
            capt["seed_iter"] = seed_iter
            return self_torch_zeros()

        def self_torch_zeros():
            import torch as _t
            return _t.zeros((2, 2), dtype=_t.float64)

        Acquisition._gp_posterior = falso
        try:
            with E._instrumentacao(espia, offset=5000, torch=self.torch):
                Acquisition._gp_posterior(None, None, None, seed_iter=3)
        finally:
            Acquisition._gp_posterior = orig
        self.assertEqual(capt["seed_iter"], 3 + 5000)
        # a semente EFETIVA registrada é a do `manual_seed(1024+seed_iter)`
        self.assertEqual(espia.seed_gp, E.SEED_GP_POSTERIOR + 3 + 5000)

    def test_select_candidates_trata_front_1d(self):
        """|ND|==1 ⇒ pymoo devolve `res.X` 1-D; sem o reshape o cdist quebra."""
        from qpots import acquisition as ACQ

        espia = E._Espia()
        orig = ACQ.select_candidates
        capt = {}

        def falso(gps, pareto_set, device, q=1, seed=None):
            capt["ndim"] = np.asarray(pareto_set).ndim
            import torch as _t
            return _t.as_tensor(np.asarray(pareto_set)[:q],
                                dtype=_t.float64)

        ACQ.select_candidates = falso
        try:
            with E._instrumentacao(espia, offset=0, torch=self.torch):
                ACQ.select_candidates(None, np.array([0.3, 0.7]), "cpu", q=1)
        finally:
            ACQ.select_candidates = orig
        self.assertEqual(capt["ndim"], 2)                # 2-D no stock
        self.assertEqual(espia.n_front_1d, 1)            # e o guard contou


@unittest.skipUnless(TEM_TORCH and TEM_QPOTS, "exige o env_e81_qpots")
class TestAdapterEDesPadronizacao(unittest.TestCase):

    def test_oracle_delega_ao_budget_e_desnormaliza(self):
        """O adapter faz SÓ `xl + X01·(xu−xl)` e delega o FE (D89)."""
        from src.budget import FEBudget
        bud = FEBudget(D=2)
        orc = E._Oracle("MMF1", bud)
        np.testing.assert_allclose(orc.xl, [1.0, -1.0])
        np.testing.assert_allclose(orc.xu, [3.0, 1.0])
        np.testing.assert_allclose(orc.to_native([0.0, 0.0]), [1.0, -1.0])
        np.testing.assert_allclose(orc.to_native([1.0, 1.0]), [3.0, 1.0])
        np.testing.assert_allclose(orc.to01(orc.to_native([0.25, 0.75])),
                                   [0.25, 0.75], atol=1e-12)
        self.assertEqual(bud.fe, 0)
        orc.eval_native(orc.to_native([0.5, 0.5]))
        self.assertEqual(bud.fe, 1)                      # 1 FE, contado no bud
        orc.eval_native(orc.to_native([0.5, 0.5]))
        self.assertEqual(bud.fe, 1)                      # cache-hit = 0 FE
        self.assertEqual(bud.cache_hits, 1)

    def test_mu_sigma_desfaz_AS_DUAS_padronizacoes_e_o_sinal(self):
        """`_mu_sigma` tem de coincidir com a inversa que o STOCK usa.

        O stock faz `unstandardize(Ys, gps.train_y)` e devolve `−Ys`; se a
        nossa rota divergisse, a ③ deixaria de ser reconstituível.
        """
        import torch
        from qpots.model_object import ModelObject
        from qpots.utils.utils import unstandardize

        rng = np.random.default_rng(0)
        X01 = rng.random((15, 2))
        f = np.column_stack([X01[:, 0] * 3.0 + 1.0, X01[:, 1] * 7.0 - 2.0])
        B01 = torch.stack([torch.zeros(2, dtype=torch.float64),
                           torch.ones(2, dtype=torch.float64)])
        with E._silencio(), E._matern_patch(2, torch):
            mo = ModelObject(train_x=torch.as_tensor(X01, dtype=torch.float64),
                             train_y=torch.as_tensor(-f, dtype=torch.float64),
                             bounds=B01, nobj=2, ncons=0, device="cpu",
                             dtype=torch.float64)
            mo.fit_gp()
        Xq = X01[:5]
        mu, sig = E._mu_sigma(mo, Xq, torch)

        # rota do STOCK: posterior.mean → unstandardize(train_y) → negar
        with torch.no_grad():
            z = torch.cat([m.posterior(torch.as_tensor(
                Xq, dtype=torch.float64)).mean.reshape(-1, 1)
                for m in mo.models], dim=-1)
            mu_stock = -unstandardize(z, mo.train_y).cpu().numpy()
        np.testing.assert_allclose(mu, mu_stock, rtol=1e-10, atol=1e-10)

        # σ é escala (a negação não a afeta) e é estritamente positivo
        self.assertTrue(np.all(sig >= 0))
        self.assertGreater(float(sig.max()), 0.0)
        # e o GP quase-interpolante (nugget 1e-12) acerta o treino
        mu_tr, _ = E._mu_sigma(mo, X01, torch)
        self.assertLess(float(np.abs(mu_tr - f).max()), 0.5)


class TestC3(unittest.TestCase):
    """DEF-C3: `transf_params` vai como **dict** — string = duplo-encode."""

    def test_c3_e_dict_e_reconstitui_o_z(self):
        f = np.array([[1.0, 10.0], [3.0, 20.0], [5.0, 30.0]])
        c3 = E._c3(f)
        self.assertEqual(c3["espaco_modelo"], "cru")
        self.assertEqual(c3["transf_tipo"], "zscore")
        self.assertIsInstance(c3["transf_params"], dict)   # NÃO string
        p = c3["transf_params"]
        self.assertEqual(p["sinal"], -1)
        self.assertEqual(p["ddof"], 1)
        # z = (−f − mean)/std reconstitui o espaço do modelo
        mean, std = np.array(p["mean"]), np.array(p["std"])
        np.testing.assert_allclose(mean, (-f).mean(axis=0))
        np.testing.assert_allclose(std, (-f).std(axis=0, ddof=1))

    def test_c3_no_surrogate_row_NAO_duplo_encoda(self):
        """O caminho REAL: `**c3` → `surrogate_row` → `json.dumps` uma vez."""
        from src import export as _export
        row = _export.surrogate_row(1, np.array([0.5, 0.5]), regime="online",
                                    real_solution_id=None,
                                    mu=np.array([1.0, 2.0]),
                                    sigma=np.array([0.1, 0.2]),
                                    pred_tipo="valor", modelo_flag="GP",
                                    **E._c3(np.array([[1.0, 2.0],
                                                      [3.0, 4.0]])))
        decodificado = json.loads(row["transf_params"])
        self.assertIsInstance(decodificado, dict)          # 1 nível, não 2
        self.assertIn("mean", decodificado)


def _link_artefatos(td: str) -> None:
    """Espelha os artefatos de entrada (DoE + sonda) num `data_root` temporário.

    O `exp` é validado contra `('main','off','batch')` + `sweep-*` (D55), então
    dois runs isolados NÃO podem ser separados por um token de `exp` inventado
    — a separação é por `data_root` (molde c149).
    """
    os.makedirs(td, exist_ok=True)
    for sub in ("doe", "sonda"):
        os.symlink(os.path.join(ROOT, "data", sub), os.path.join(td, sub))


@unittest.skipUnless(SLOW, "runs completos — exporte E81_SLOW=1")
class TestRunsCompletos(unittest.TestCase):
    """As duas provas caras do cartão (molde c122/c149), em `data_root` temp."""

    def _um_real(self, td):
        import pyarrow.parquet as pq
        from src import naming
        return pq.read_table(naming.layer_path(
            "main", "e81", "MMF1", 0, "real", data_root=td)).to_pydict()

    def test_determinismo_bit_a_bit(self):
        """2 runs da mesma semente ⇒ ① IDÊNTICA (torch CPU + threads=1)."""
        from src.e81_qpots import run_e81
        saidas = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                run_e81("main", "e81", "MMF1", 0, data_root=td)
                saidas.append(self._um_real(td))
        self.assertEqual(saidas[0], saidas[1],
                         "dois runs da MESMA semente divergiram")

    def test_sonda_NAO_perturba_a_busca(self):
        """🔴 §3.1: ① com sonda k=2 ≡ ① com a sonda praticamente desligada.

        `sonda_k=10**9` deixa só a 1ª (g==1) e a última (finalProbe) — o
        mínimo que a fórmula normativa admite. Se o `preserve_all_rng` em
        volta do `predict` falhasse, o Thompson da iteração seguinte mudaria
        e a ① divergiria.
        """
        from src import standalone_harness as H
        from src.e81_qpots import run_e81
        saidas = []
        for k in (H.SONDA_K, 10 ** 9):
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                run_e81("main", "e81", "MMF1", 0, data_root=td, sonda_k=k)
                saidas.append(self._um_real(td))
        self.assertEqual(saidas[0], saidas[1],
                         "a sonda MOVEU a busca — o `preserve_all_rng` falhou")


if __name__ == "__main__":                                # pragma: no cover
    unittest.main()
