"""[R3-c149] Testes do runner LBN-MOBO (`src/c149_lbnmobo.py`).

Cobrem: identidade (alg_id/dispatch/env/offset D22), fidelidade da
reconstrução (arquitetura + nº de params âncora da SPEC, ativações da RAIZ,
σ² populacional ddof=0, fix `[:, :M]`, determinismo do treino com a ordem de
RNG do stock), a regra D96 (normalização observada, ref ×1,1, desempate σ²,
fallback com RNG do harness), a des-padronização da sonda, e o invariante
cache-hit×treino (D89/DI-21). As 2 provas CARAS (determinismo bit-a-bit e
não-perturbação da sonda §3.1) ficam atrás de `C149_SLOW=1` — molde c122.
"""

from __future__ import annotations

import os
import unittest

import numpy as np

from src import c149_lbnmobo as C
from src import standalone_harness as H
from src.budget import FEBudget

SLOW = os.environ.get("C149_SLOW") == "1"


class TestIdentidade(unittest.TestCase):

    def test_alg_id_bate_com_o_artefato(self):
        import json
        with open(os.path.join(H.ROOT, "claude_code_context", "artifacts",
                               "seeds.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["alg_id"]["c149"], C.ALG_ID)

    def test_dispatch_registrado(self):
        from src import experiment
        self.assertIn("c149", experiment._DISPATCH_LOADERS)
        self.assertEqual(experiment._DISPATCH_LOADERS["c149"],
                         ("src.c149_lbnmobo", "run_c149", "standalone"))

    def test_c149_NAO_e_venv_only_e_env_main(self):
        self.assertNotIn("c149", H.VENV_ONLY_ALGS)
        self.assertEqual(H.load_env_table()["alg_to_env"]["c149"]["env"],
                         "env_main")

    def test_offset_D22_na_base(self):
        """c149 ∈ SEED_OFFSET_ALGS: base = 1000·s — DENTRO do SeedSequence."""
        self.assertIn("c149", H.SEED_OFFSET_ALGS)
        self.assertEqual(H.seed_base("c149", 7), 7000)
        self.assertEqual(H.seed_base("c149", 0), 0)

    def test_seed_por_rede_e_stock_na_semente_0(self):
        """A metade HARD-CODED do D22: `1000·s + net_n + 1`; em s=0 é o
        `manual_seed(net_n+1)` LITERAL do stock (Forward_BNN.py:57)."""
        base = H.seed_base("c149", 0)
        self.assertEqual([base + n + 1 for n in range(3)], [1, 2, 3])
        base7 = H.seed_base("c149", 7)
        self.assertEqual(base7 + 0 + 1, 7001)


class TestReconstrucao(unittest.TestCase):
    """Fidelidade das peças reconstruídas vs o repo oficial."""

    def test_arquitetura_e_n_params_ancora(self):
        """Âncora da SPEC (§22.4): 13.452 params em D=30/M=2."""
        import torch
        antes = torch.get_default_dtype()
        with C._c149_runtime():
            from layer_config_forward import MultiLayerPerceptron_forward
            self.assertEqual(torch.get_default_dtype(), torch.float32,
                             "o contexto não impôs o float32 do stock")
            m = MultiLayerPerceptron_forward(30, C.HIDDEN, 2, 0)
            n = sum(p.numel() for p in m.parameters() if p.requires_grad)
        self.assertEqual(n, 13452)
        self.assertEqual(torch.get_default_dtype(), antes,
                         "o contexto não restaurou o dtype ANTERIOR")

    def test_ativacoes_da_raiz(self):
        """Convenção da RAIZ (net_n 0..9): tanh, ReLU, CELU, LeakyReLU, ELU,
        Hardswish, tanh, ReLU, CELU, LeakyReLU (SPEC v2.2)."""
        import torch
        import torch.nn as nn
        with C._c149_runtime():
            from layer_config_forward import activation_function_list as A
        esperado = [torch.tanh, nn.ReLU, nn.CELU, nn.LeakyReLU, nn.ELU,
                    nn.Hardswish, torch.tanh, nn.ReLU, nn.CELU, nn.LeakyReLU]
        for i, exp in enumerate(esperado):
            if exp is torch.tanh:
                self.assertIs(A[i], torch.tanh, f"net_n={i}")
            else:
                self.assertIsInstance(A[i], exp, f"net_n={i}")

    @staticmethod
    def _stub_models(torch, vals):
        """K modelos constantes: forward(x) -> (n, M) com a linha `vals[k]`."""
        class _Const(torch.nn.Module):
            def __init__(self, v):
                super().__init__()
                self.v = torch.tensor(v).float()

            def forward(self, x):
                return self.v.expand(x.shape[0], -1)
        return [_Const(v) for v in vals]

    def test_acq_fix_M_e_sigma2_populacional(self):
        """O F da aquisição tem 2M colunas ([:, :M] — 🔴 ARTIGO) e a σ² é a
        variância POPULACIONAL ddof=0 entre as K=10 saídas (stock :40-43)."""
        import torch
        with C._c149_runtime():
            rng = np.random.default_rng(0)
            for M in (2, 3):
                vals = rng.normal(size=(C.K_ENSEMBLE, M))
                models = self._stub_models(torch, vals)
                prob = C._make_acq_problem(models, D=4, M=M, torch=torch)
                self.assertEqual(prob.n_obj, 2 * M)
                X = rng.random((5, 4))
                F = prob.evaluate(X)
                self.assertEqual(F.shape, (5, 2 * M))
                mu_esp = vals.mean(axis=0)
                var_esp = vals.var(axis=0, ddof=0)     # POPULACIONAL
                np.testing.assert_allclose(F[0, :M], mu_esp, rtol=1e-5)
                np.testing.assert_allclose(-F[0, M:], var_esp, rtol=1e-4,
                                           atol=1e-7)

    def test_bnn_treino_deterministico_e_diverso(self):
        """Mesmo (net_n, dados, seed) ⇒ pesos bit-a-bit; net_n diferente ⇒
        rede diferente (ativação da raiz + seed distintos)."""
        import torch
        rng = np.random.default_rng(42)
        X01 = rng.random((12, 2))
        Yz = rng.normal(size=(12, 2))
        with C._c149_runtime():
            from layer_config_forward import MultiLayerPerceptron_forward
            outs = []
            for _ in range(2):
                m, vmse, n_tr, n_val = C._bnn_diverse_func(
                    0, X01, Yz, 2, 2, seed=1, torch=torch,
                    MLP=MultiLayerPerceptron_forward)
                outs.append({k: v.clone() for k, v in m.state_dict().items()})
            for k in outs[0]:
                self.assertTrue(torch.equal(outs[0][k], outs[1][k]),
                                f"treino não-determinístico em {k}")
            self.assertEqual((n_tr, n_val), (10, 2))   # split 90/10 de 12
            m2, *_ = C._bnn_diverse_func(
                1, X01, Yz, 2, 2, seed=2, torch=torch,
                MLP=MultiLayerPerceptron_forward)
            algum_diferente = any(
                not torch.equal(outs[0][k], v)
                for k, v in m2.state_dict().items())
            self.assertTrue(algum_diferente, "net_n=1 idêntica à net_n=0")


class TestHviGreedyD96(unittest.TestCase):
    """A regra FECHADA do D96 — normalização observada, ref ×1,1, desempate."""

    def setUp(self):
        # arquivo observado 2D: 3 pontos, front = {(0,10), (5,5), (10,0)}
        self.F_arc = np.array([[0., 10.], [5., 5.], [10., 0.]])
        self.rng = np.random.default_rng(123)

    def test_candidato_dominante_vence(self):
        mu = np.array([[4., 4.],      # domina (5,5) — HVI > 0
                       [6., 6.]])     # dominado — HVI = 0
        s2 = np.zeros((2, 2))
        sel = C._hvi_greedy_d96(self.F_arc, mu, s2, self.rng)
        self.assertEqual(sel["idx"], 0)
        self.assertEqual(sel["caminho"], "hvi")
        self.assertGreater(sel["hvi"], 0)
        self.assertEqual(sel["n_hvi_pos"], 1)

    def test_normalizacao_e_do_arquivo_observado(self):
        """Escala 1000× num objetivo NÃO domina a escolha (o ponto do D96):
        candidatos que normalizam para pontos ESPELHADOS ((0.3,0.45) ×
        (0.45,0.3)) têm HVI idêntico, apesar da escala 1000× do obj₀."""
        F_arc = self.F_arc * np.array([1000., 1.])   # obj0 ∈ [0,10⁴], obj1 ∈ [0,10]
        mu = np.array([[3000., 4.5],                 # → (0.30, 0.45)
                       [4500., 3.0]])                # → (0.45, 0.30)
        s2 = np.zeros((2, 2))
        sel = C._hvi_greedy_d96(F_arc, mu, s2, self.rng)
        h = sorted(sel["hvi_top5"][:2])
        self.assertGreater(h[0], 0)
        self.assertAlmostEqual(h[0], h[1], places=9,
                               msg="a normalização observada não simetrizou")

    def test_fora_do_ref_contribui_zero(self):
        mu = np.array([[100., 100.]])               # >> nadir×1,1
        s2 = np.zeros((1, 2))
        sel = C._hvi_greedy_d96(self.F_arc, mu, s2, self.rng)
        self.assertEqual(sel["hvi"], 0.0)

    def test_desempate_maior_sigma2(self):
        mu = np.array([[6., 6.], [7., 7.]])          # ambos dominados: HVI=0
        s2 = np.array([[.1, .1], [.5, .5]])
        sel = C._hvi_greedy_d96(self.F_arc, mu, s2, self.rng)
        self.assertEqual(sel["idx"], 1)
        self.assertEqual(sel["caminho"], "desempate_sigma")

    def test_fallback_aleatorio_deterministico_pelo_rng(self):
        mu = np.array([[6., 6.], [7., 7.], [8., 8.]])
        s2 = np.zeros((3, 2))
        picks = {C._hvi_greedy_d96(self.F_arc, mu, s2,
                                   np.random.Generator(np.random.PCG64(k)))
                 ["idx"] for k in range(20)}
        self.assertGreater(len(picks), 1, "o fallback não é aleatório")
        a = C._hvi_greedy_d96(self.F_arc, mu, s2,
                              np.random.Generator(np.random.PCG64(5)))
        b = C._hvi_greedy_d96(self.F_arc, mu, s2,
                              np.random.Generator(np.random.PCG64(5)))
        self.assertEqual(a["idx"], b["idx"])
        self.assertEqual(a["caminho"], "fallback_aleatorio")

    def test_sigma2_negativa_clampada_no_desempate(self):
        mu = np.array([[6., 6.], [7., 7.]])
        s2 = np.array([[-1e-6, -1e-6], [0., 0.]])    # float32 residual
        sel = C._hvi_greedy_d96(self.F_arc, mu, s2, self.rng)
        # clamp ⇒ agregadas 0 e 0 ⇒ empate total ⇒ fallback (nunca a −1e-6
        # "vencer" por ser menos negativa não se aplica: ambas viram 0)
        self.assertEqual(sel["caminho"], "fallback_aleatorio")


class TestOracleESonda(unittest.TestCase):

    def _oracle(self):
        return C._Oracle("MMF1", FEBudget(D=2))

    def test_desnormalizacao_mmf1(self):
        """MMF1: xl=[1,−1], xu=[3,1] — o adapter cria a desnormalização que o
        repo NÃO tem (L.14)."""
        o = self._oracle()
        np.testing.assert_allclose(o.to_native([0., 0.]), [1., -1.])
        np.testing.assert_allclose(o.to_native([1., 1.]), [3., 1.])
        np.testing.assert_allclose(o.to01(o.to_native([.25, .75])),
                                   [.25, .75], atol=1e-15)

    def test_sonda_despadroniza_mu_e_sigma(self):
        """μ_nat = μ_z·std+mean; σ_nat = sqrt(max(σ²_z,0))·std (A-02: σ,
        nunca σ²)."""
        import torch
        with C._c149_runtime():
            vals = np.array([[1., -1.]] * 5 + [[3., 1.]] * 5)  # μ_z=(2,0)
            models = TestReconstrucao._stub_models(torch, vals)
            estado = {"models": models,
                      "z_mean": np.array([10., 20.]),
                      "z_std": np.array([2., 4.])}
            predict = C._sonda_predict(estado, self._oracle(), torch)
            mu, sig = predict(np.array([[1.5, 0.0], [2.0, 0.5]]))
        # μ_z = (2, 0); σ²_z populacional = (1, 1) ⇒ σ_z = 1
        np.testing.assert_allclose(mu, [[14., 20.]] * 2, rtol=1e-5)
        np.testing.assert_allclose(sig, [[2., 4.]] * 2, rtol=1e-4)

    def test_oracle_delega_ao_budget(self):
        """O adapter NÃO conta FE (D89): quem conta é o FEBudget."""
        o = self._oracle()
        f1 = o.eval_native(np.array([1.5, 0.0]))
        f2 = o.eval_native(np.array([1.5, 0.0]))    # cache-hit
        np.testing.assert_array_equal(f1, f2)
        self.assertEqual(o._bud.fe, 1)
        self.assertEqual(o._bud.cache_hits, 1)
        self.assertEqual(len(o._bud.records), 1,
                         "o treino cresceria num cache-hit (hazard c122 §5.3)")


@unittest.skipUnless(SLOW, "run completo — exporte C149_SLOW=1")
class TestRunsCompletos(unittest.TestCase):
    """As duas provas CARAS exigidas pelo contrato (§3.1 e L.14)."""

    def test_determinismo_bit_a_bit(self):
        import tempfile

        import pyarrow.parquet as pq

        from src import naming
        fs = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                C.run_c149("main", "c149", "MMF1", 0, data_root=td)
                fs.append(pq.read_table(naming.layer_path(
                    "main", "c149", "MMF1", 0, "real",
                    data_root=td)).to_pydict())
        self.assertEqual(fs[0], fs[1], "dois runs da MESMA semente divergiram")

    def test_sonda_NAO_perturba_a_busca(self):
        """🔴 Invariante de não-perturbação (§3.1): ① com sonda == ① sem."""
        import tempfile

        import pyarrow.parquet as pq

        from src import naming
        out = []
        for k in (H.SONDA_K, 10 ** 9):     # k gigante ⇒ só a 1ª e a última
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                orig, H.SONDA_K = H.SONDA_K, k
                try:
                    C.run_c149("main", "c149", "MMF1", 0, data_root=td)
                finally:
                    H.SONDA_K = orig
                out.append(pq.read_table(naming.layer_path(
                    "main", "c149", "MMF1", 0, "real",
                    data_root=td)).to_pydict())
        self.assertEqual(out[0], out[1],
                         "a sonda MOVEU a busca — o `preserve_all_rng` falhou")


def _link_artefatos(td: str) -> None:
    """Linka doe/sonda do repo para um data_root temporário (molde c122)."""
    for sub in ("doe", "sonda"):
        os.symlink(os.path.join(H.ROOT, "data", sub), os.path.join(td, sub))


if __name__ == "__main__":                            # pragma: no cover
    unittest.main()
