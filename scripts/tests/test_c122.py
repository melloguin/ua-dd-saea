"""[R3-c122] Testes do θ-DEA-DP — contrato, fidelidade do FORK e determinismo.

**Escopo (D97):** nada aqui julga FIDELIDADE do algoritmo — isso é validação
MANUAL do autor, em lote. O que se prova aqui é (a) que o nosso FORK
instrumentado decide EXATAMENTE o que o código stock decidiria, (b) que os
patches obrigatórios estão de pé, e (c) o contrato de dados v5.2.1.

Os testes CAROS (runs completos: determinismo bit-a-bit e não-perturbação da
sonda) ficam atrás de `C122_SLOW=1` para não pesar na suíte — foram executados
no fechamento do cartão e o resultado está em `handoff/R3-c122.md`.
"""

from __future__ import annotations

import os
import unittest

import numpy as np

from src import c122_thetadeadp as C
from src import metrics as _metrics

SLOW = os.environ.get("C122_SLOW") == "1"


class TestFLimits(unittest.TestCase):
    """DEF-B11.1 — os `f_min`/`f_max` FIXOS pela assinatura."""

    def test_margem_de_10_pct_sobre_o_nadir(self):
        ideal, nadir = _metrics.reference_bounds("MMF1")
        f_min, f_max = C.f_limits("MMF1")
        np.testing.assert_allclose(f_min, ideal)
        np.testing.assert_allclose(f_max, nadir + 0.1 * (nadir - ideal))

    def test_todos_os_25_problemas_tem_par(self):
        for p in _metrics.F_MIN_MAX:
            f_min, f_max = C.f_limits(p)
            self.assertEqual(f_min.shape, f_max.shape, p)
            self.assertTrue(np.all(f_max > f_min), f"{p}: range não-positivo")

    def test_escala_extrema_do_BBOB_F17_sobrevive(self):
        """O f₁ do BBOB F17 vive em 10⁷ — é a prova viva do porquê da B11.1."""
        _, f_max = C.f_limits("BBOB_F17")
        self.assertGreater(f_max[0], 1e7)

    def test_a_assinatura_do_core_JA_aceita_f_min_f_max(self):
        """O patch é de CHAMADA, não de core: `scalar_dom_ea_dp` já os aceita.

        Se um upgrade do repo removesse esses parâmetros, o patch obrigatório
        DEF-B11.1 viraria silenciosamente um no-op — este teste falha antes.
        """
        import inspect
        with C._c122_runtime():
            from evolution.algorithms import scalar_dom_ea_dp
            par = inspect.signature(scalar_dom_ea_dp).parameters
        self.assertIn("f_min", par)
        self.assertIn("f_max", par)

    def test_o_default_do_core_e_a_IDENTIDADE_o_bug_que_o_patch_corrige(self):
        """Sem o patch, `init_obj_limits` devolve 0/1 e a normalização some."""
        with C._c122_runtime():
            from evolution.utils import init_obj_limits
            self.assertEqual(init_obj_limits(None, None), (0, 1))


class TestBypassEStub(unittest.TestCase):
    """Bypass do factory (S.8) + stub do visualizer."""

    def test_o_factory_NUNCA_e_importado(self):
        """`pymop`/`optproblems`/`autograd` não existem no env-main (S.8)."""
        import sys
        with C._c122_runtime():
            import evolution.selection            # noqa: F401
            import learning.prediction            # noqa: F401
        for proibido in ("pymop", "optproblems", "autograd", "problems.factory"):
            self.assertNotIn(proibido, sys.modules,
                             f"{proibido} carregado — bypass falhou")

    def test_visualizer_e_stubado(self):
        with C._c122_runtime():
            from evolution import selection
            self.assertIs(selection.visualize_preselection, C._no_op_visualizer)

    def test_dtype_float32_e_restaurado_na_saida(self):
        """O float32 é FORÇADO pelo código do repo — mas não pode VAZAR."""
        import torch
        antes = torch.get_default_dtype()
        with C._c122_runtime():
            self.assertEqual(torch.get_default_dtype(), torch.float32)
        self.assertEqual(torch.get_default_dtype(), antes)


class TestCreatorPerRun(unittest.TestCase):
    """O `creator` do DEAP é estado GLOBAL — tem de nascer novo a cada run."""

    def test_M_diferente_nao_vaza_entre_runs(self):
        from deap import creator
        C._fresh_creator(2)
        self.assertEqual(creator.FitnessMin.weights, (-1.0, -1.0))
        C._fresh_creator(3)
        self.assertEqual(creator.FitnessMin.weights, (-1.0, -1.0, -1.0),
                         "o FitnessMin do run anterior vazou — o M errado "
                         "passaria SEM ERRO")


class TestConfMaxSemDiagonal(unittest.TestCase):
    """`conf[i,i]` é lixo (nunca escrito) — incluí-lo constantifica a coluna."""

    def test_diagonal_ignorada_na_matriz_intra(self):
        m = np.array([[1.0, 0.3], [0.4, 1.0]])       # diagonal = np.ones default
        np.testing.assert_allclose(C._conf_max_sem_diagonal(m), [0.3, 0.4])

    def test_duas_redes_tomam_o_maximo(self):
        a = np.array([[1.0, 0.2], [0.9, 1.0]])
        b = np.array([[1.0, 0.7], [0.1, 1.0]])
        np.testing.assert_allclose(C._conf_max_sem_diagonal(a, b), [0.7, 0.9])


class TestFidelidadeDoFork(unittest.TestCase):
    """🔴 O teste que importa: o FORK decide o MESMO que o código stock.

    Todo o resto da instrumentação é inócuo se a ESCOLHA divergir — seria uma
    mudança silenciosa de algoritmo. Montamos um estado real (init de MMF1 +
    as 2 redes treinadas) e comparamos `_filtro_instrumentado` com o
    `pareto_scalar_nn_filter` STOCK, com contadores em estado idêntico.
    """

    @classmethod
    def setUpClass(cls):
        cls.ctx = C._c122_runtime()
        cls.ctx.__enter__()
        import random

        import torch
        from evolution.counter import PerCounter
        from evolution.dom import pareto_dominance, scalar_dominance
        from evolution.norm import var_normalization
        from evolution.utils import (full_evaluate, get_non_dominated_scalar_rep,
                                     init_dom_rel_map, init_scalar_rep)
        from evolution.variation import random_genetic_variation
        from learning.model_init import init_dom_nn_classifier
        from problems.rp import get_reference_points
        from src.budget import FEBudget

        random.seed(7)
        np.random.seed(7)
        torch.manual_seed(7)

        from src import standalone_harness as H
        doe = H.load_doe("MMF1", 0)
        D = doe["X"].shape[1]
        bud = FEBudget(D=D)
        cls.ad = C._Adapter("MMF1", bud)
        creator = C._fresh_creator(cls.ad.n_obj)
        cls.rp = get_reference_points(cls.ad.n_obj)
        cls.MU = len(cls.rp)
        tb = C._ToolboxShim(cls.ad, cls.rp)

        pop = [creator.Individual(list(x)) for x in doe["X"]]
        var_normalization(pop, low=cls.ad.xl, up=cls.ad.xu)
        f_min, f_max = C.f_limits("MMF1")
        full_evaluate(pop, tb, f_min, f_max)
        p_map, s_map = init_dom_rel_map(bud.maxfe)
        dev = torch.device("cpu")
        cls.p_net = init_dom_nn_classifier(pop, p_map, pareto_dominance, dev,
                                           2 * D, C.HIDDEN, C.N_HIDDEN, C.E_INIT)
        cls.s_net = init_dom_nn_classifier(pop, s_map, scalar_dominance, dev,
                                           2 * D, C.HIDDEN, C.N_HIDDEN, C.E_INIT)
        cls.reps = init_scalar_rep(pop)
        cls.nd = get_non_dominated_scalar_rep(cls.reps)
        cls.dev = dev
        # um pool menor que 7000: o teste mede EQUIVALÊNCIA, não custo
        cls.offs = random_genetic_variation(pop, 400, tb, cxpb=1.0, mutpb=1.0)
        var_normalization(cls.offs, low=cls.ad.xl, up=cls.ad.xu)
        cls.PerCounter = PerCounter

    @classmethod
    def tearDownClass(cls):
        cls.ctx.__exit__(None, None, None)

    def test_fork_escolhe_o_MESMO_individuo_que_o_stock(self):
        """Percorre TODOS os clusters e compara escolha a escolha.

        Um cluster só não basta: no MMF1 as 3 categorias saem vazias com
        frequência (é o *spin* — `algorithms.py:44-45` re-sampla), e nesse caso
        AMBOS devolvem `None`. O teste tem de cobrir os dois desfechos —
        concordar no `None` também é concordar —, senão ele ou é vacuamente
        verde ou falha por um estado que é o comportamento CORRETO.
        """
        from evolution.selection import pareto_scalar_nn_filter
        c_stock, c_meu = self.PerCounter(self.MU), self.PerCounter(self.MU)
        n_achou = n_none = 0
        for _ in range(self.MU):                    # um ciclo completo de cids
            stock = pareto_scalar_nn_filter(
                self.offs, self.reps, self.nd, self.p_net, self.s_net,
                C.CATEGORY_SIZE, self.dev, self.rp, c_stock,
                toolbox=None, visualization=False)
            meu, tel = C._filtro_instrumentado(
                self.offs, self.reps, self.nd, self.p_net, self.s_net,
                C.CATEGORY_SIZE, self.dev, self.rp, c_meu)
            self.assertEqual(
                None if stock is None else list(stock),
                None if meu is None else list(meu),
                f"o FORK divergiu do stock no cid={tel['cid']} — isso é uma "
                f"MUDANÇA DE ALGORITMO, não instrumentação. Pára-e-loga (D81).")
            self.assertEqual(tel["n_pool"], len(self.offs))
            n_achou += meu is not None
            n_none += meu is None
        self.assertGreater(n_achou, 0, "nenhum cluster produziu candidato — o "
                                       "teste ficaria vacuamente verde")
        # (n_none > 0 é esperado no MMF1, mas não é exigido: depende da amostra)

    def test_e_of_z_reproduz_o_argmax_do_select_best_individual(self):
        from evolution.selection import select_best_individual
        cands = self.offs[:40]
        stock = select_best_individual(cands, self.p_net, self.s_net, self.dev)
        e_z, conf = C._e_of_z(cands, self.p_net, self.s_net, self.dev)
        self.assertEqual(list(cands[int(np.argmax(e_z))]), list(stock))
        self.assertEqual(e_z.shape, (len(cands),))
        self.assertTrue(np.all(e_z >= 0), "e(z) é soma de confianças mascaradas")
        self.assertTrue(np.all((conf > 0) & (conf <= 1)), "max-softmax ∈ (0,1]")

    def test_telemetria_do_pool_e_coerente(self):
        _, tel = C._filtro_instrumentado(
            self.offs, self.reps, self.nd, self.p_net, self.s_net,
            C.CATEGORY_SIZE, self.dev, self.rp, self.PerCounter(self.MU))
        if tel["ramo"] != "categorias":
            self.skipTest("cluster sem representante nesta amostra")
        self.assertEqual(tel["n_acordo"] + tel["n_desacordo"], tel["n_pool"],
                         "acordo+desacordo tem de fechar o pool INTEIRO")
        self.assertLessEqual(tel["n_q1"] + tel["n_q2"] + tel["n_q3"],
                             tel["n_pool"])
        self.assertLessEqual(tel["scf_min"], tel["scf_med"])
        self.assertLessEqual(tel["scf_med"], tel["scf_max"])

    def test_ez_rows_respeita_o_TOP_e_so_o_escolhido_tem_sid(self):
        """[P3/DI-16.3 A+] o TOP-100 por e(z), ordenado, 1 único `sid`."""
        cands = self.offs[:250]
        e_z, conf = C._e_of_z(cands, self.p_net, self.s_net, self.dev)
        escolhido = cands[int(np.argmax(e_z))]
        tel = {"cands": cands, "e_z": e_z, "conf": conf}
        rows = C._ez_rows(tel, geracao=3, escolhido=escolhido, sid=42,
                          modelo_flag="EDN-par(2xFNN)")
        self.assertEqual(len(rows), C.TOP_BUSCA)
        scores = [r["pred_score"] for r in rows]
        self.assertEqual(scores, sorted(scores, reverse=True), "não ordenado")
        com_sid = [r for r in rows if r["real_solution_id"] == 42]
        self.assertEqual(len(com_sid), 1, "só o escolhido vira FE")
        self.assertIs(rows[0]["real_solution_id"], 42,
                      "o escolhido é o argmax ⇒ tem de ser o topo")
        for r in rows:
            self.assertEqual(r["pred_tipo"], "score")
            self.assertIsNone(r["mu"], "μ não se aplica ao c122 (par-a-par)")
            self.assertIsNone(r["sigma"])
            self.assertEqual(r["regime"], "online")

    def test_sonda_predict_devolve_e_z_e_confianca_por_ponto(self):
        """[P2/DI-16.2] referência = a população selecionada, n_ref FIXO."""
        pop_ref = self.offs[:self.MU]
        estado = {"pop": pop_ref, "p_net": self.p_net, "s_net": self.s_net,
                  "device": self.dev}
        predict = C._sonda_predict(estado, self.ad.xl, self.ad.xu)
        X = np.random.default_rng(0).uniform(self.ad.xl, self.ad.xu, size=(37, 2))
        score, conf = predict(X)
        self.assertEqual(score.shape, (37,))
        self.assertEqual(conf.shape, (37,))
        self.assertTrue(np.all(score >= 0))
        self.assertTrue(np.all(score <= 2 * len(pop_ref)),
                        "e(z) ≤ 2 redes × n_ref (confiança ≤ 1 por par)")
        self.assertTrue(np.all((conf > 0) & (conf <= 1)))

    def test_sonda_sem_modelo_devolve_NaN_e_nao_inventa_numero(self):
        estado = {"pop": [], "p_net": None, "s_net": None, "device": self.dev}
        score, conf = C._sonda_predict(estado, self.ad.xl, self.ad.xu)(
            np.zeros((5, 2)))
        self.assertTrue(np.all(np.isnan(score)))
        self.assertTrue(np.all(np.isnan(conf)))

    def test_predicao_NAO_consome_RNG(self):
        """A premissa que torna o fork seguro: prever não move a trajetória.

        É por isso que podemos recalcular a triagem para telemetria sem alterar
        a busca (`prediction.py:76-78` — `eval()` + `no_grad()`).
        """
        import random

        import torch
        est = (random.getstate(), np.random.get_state(),
               torch.random.get_rng_state())
        C._e_of_z(self.offs[:30], self.p_net, self.s_net, self.dev)
        self.assertEqual(random.getstate(), est[0])
        self.assertEqual(np.random.get_state()[1].tolist(),
                         est[1][1].tolist())
        self.assertTrue(torch.equal(torch.random.get_rng_state(), est[2]))


class TestDispatch(unittest.TestCase):
    def test_c122_registrado_no_dispatch(self):
        from src import experiment
        self.assertIn("c122", experiment._DISPATCH_LOADERS)
        mod, fn, stack = experiment._DISPATCH_LOADERS["c122"]
        self.assertEqual((mod, fn, stack),
                         ("src.c122_thetadeadp", "run_c122", "standalone"))

    def test_c122_NAO_e_venv_only(self):
        """c122 → `env_main` (DI-14): roda in-process, sem subprocess."""
        from src import standalone_harness as H
        self.assertNotIn("c122", H.VENV_ONLY_ALGS)
        self.assertEqual(H.load_env_table()["alg_to_env"]["c122"]["env"],
                         "env_main")

    def test_alg_id_bate_com_o_artefato(self):
        import json
        from src import standalone_harness as H
        with open(os.path.join(H.ROOT, "claude_code_context", "artifacts",
                               "seeds.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["alg_id"]["c122"], C.ALG_ID)


@unittest.skipUnless(SLOW, "run completo — exporte C122_SLOW=1")
class TestRunsCompletos(unittest.TestCase):
    """As duas provas CARAS exigidas pelo contrato (§3.1 e L.6)."""

    def test_determinismo_bit_a_bit(self):
        import tempfile

        import pyarrow.parquet as pq

        from src import naming
        fs = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                C.run_c122("main", "c122", "MMF1", 0, data_root=td)
                fs.append(pq.read_table(naming.layer_path(
                    "main", "c122", "MMF1", 0, "real", data_root=td)).to_pydict())
        self.assertEqual(fs[0], fs[1], "dois runs da MESMA semente divergiram")

    def test_sonda_NAO_perturba_a_busca(self):
        """🔴 Invariante de não-perturbação (§3.1): ① com sonda == ① sem."""
        import tempfile

        import pyarrow.parquet as pq

        from src import naming, standalone_harness as H
        out = []
        for k in (H.SONDA_K, 10 ** 9):     # k gigante ⇒ só a 1ª e a última
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                orig, H.SONDA_K = H.SONDA_K, k
                try:
                    C.run_c122("main", "c122", "MMF1", 0, data_root=td)
                finally:
                    H.SONDA_K = orig
                out.append(pq.read_table(naming.layer_path(
                    "main", "c122", "MMF1", 0, "real", data_root=td)).to_pydict())
        self.assertEqual(out[0], out[1],
                         "a sonda MOVEU a busca — o `preserve_all_rng` falhou")


def _link_artefatos(td: str) -> None:
    """Linka doe/sonda do repo para um data_root temporário."""
    from src import standalone_harness as H
    for sub in ("doe", "sonda"):
        os.symlink(os.path.join(H.ROOT, "data", sub), os.path.join(td, sub))


if __name__ == "__main__":                                # pragma: no cover
    unittest.main()
