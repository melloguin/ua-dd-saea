"""Testes do cartão F0-04-metrica: esqueleto da camada de métrica pós-hoc
(`src.metrics`) — normalização D69, IGD/IGD+/HV/GD/spacing, reference set,
leitura da camada ①, trajetória e a **âncora do smoke D92 (HV(BBOB_F1)=1,0433)**.

- `src.metrics` requer numpy + pymoo (env-main) → PULADO sem pymoo.
- os testes de leitura da ① requerem pyarrow (`src.export`) → PULADOS sem ele.
Não testa fidelidade (D97): mede, não decide.
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    import numpy as np
    import pymoo  # noqa: F401
    from src import metrics
    _HAVE_METRICS = True
except Exception:  # noqa: BLE001
    _HAVE_METRICS = False

try:
    import numpy as np  # noqa: F811
    import pyarrow  # noqa: F401
    from src import budget, export, problems as _P, experiment
    _HAVE_STACK = True
except Exception:  # noqa: BLE001
    _HAVE_STACK = False


@unittest.skipUnless(_HAVE_METRICS, "sem numpy/pymoo (env-main)")
class TestBoundsNormalize(unittest.TestCase):

    def test_table_covers_28_problems(self):
        # 28 chaves (25 sintéticos + 3 reais, D101), todas com régua concreta
        # — a do DDMOP7 é a FASE 1 (REAL-2.15/opção A) e carrega o SELO.
        from src import experiment as _E
        self.assertEqual(len(metrics.F_MIN_MAX), 28)
        self.assertEqual(set(metrics.F_MIN_MAX), set(_E.ALL_PROBLEMS))
        self.assertTrue(all(v is not None for v in metrics.F_MIN_MAX.values()))

    def test_regua_fase1_ddmop7_ideal_e_infimo_teorico(self):
        # [REAL-2.15 ERRATA 2, autor 2026-08-15] O `ideal` deixou de ser a
        # ESTIMATIVA sobre os 62 pontos do probe (`[4/17 ; 202/690]`, opção A)
        # e passou a ser o ÍNFIMO TEÓRICO `[0 ; 0]`. Motivo medido: a
        # estimativa furou em 3.203 de 7.156 pontos dos smokes pós-zona-morta,
        # e o furo tocava a BUSCA (c122 normaliza o PBI por ela;
        # c262 deriva daqui o ref-point da aquisição), não só a análise.
        # O nadir segue como a ERRATA 1 (468/690; o 0,44493 dos docs era
        # errado). A fase 2 pooled continua obrigatória (selo abaixo).
        ideal, nadir = metrics.reference_bounds("DDMOP7")
        self.assertTrue(np.allclose(ideal, [0.0, 0.0]))
        self.assertTrue(np.allclose(nadir, [1.0, 468 / 690]))

    def test_infimo_ddmop7_nao_pode_ser_furado(self):
        # A propriedade que motivou a errata 2, como TESTE e não como comentário:
        # os objetivos do DDMOP7 são contagens normalizadas (f1 = k/17, k ≥ 0;
        # f2 = n/690, n ≥ 0), logo NENHUM ponto legítimo fica abaixo de [0;0].
        # Varre toda a grade de valores possíveis (18 × 691 = 12.438 pares).
        k = np.arange(0, 18) / 17.0
        n = np.arange(0, 691) / 690.0
        F = np.stack(np.meshgrid(k, n, indexing="ij"), -1).reshape(-1, 2)
        metrics.checa_regua(F, "DDMOP7")            # não pode levantar
        ideal, nadir = metrics.reference_bounds("DDMOP7")
        Z = (F - ideal) / (nadir - ideal)
        self.assertTrue((Z[:, 0] >= 0).all() and (Z[:, 1] >= 0).all())

    def test_checa_regua_reprova_dado_melhor_que_o_ideal(self):
        # [T15.13] CONTROLE NEGATIVO do guard: um gate que nunca reprova é
        # decorativo (T11 §4.1). Um ponto melhor que o ideal tem de PARAR.
        ideal, _ = metrics.reference_bounds("ZDT1")
        metrics.checa_regua(np.atleast_2d(ideal), "ZDT1")        # no ideal: passa
        with self.assertRaises(RuntimeError):
            metrics.checa_regua(np.atleast_2d(ideal - 1.0), "ZDT1")

    def test_selo_de_substituicao_obrigatoria_vivo(self):
        # [D102.3/TD-13] o selo NÃO sai antes da fase 2 — tripwire de auditoria.
        self.assertIn("DDMOP7", metrics.REGUAS_PROVISORIAS)

    def test_regua_none_para_e_loga(self):
        # o mecanismo do selo-null continua vivo p/ problemas futuros: régua
        # None ⇒ erro DESENHADO, nunca número inventado.
        metrics.F_MIN_MAX["_TESTE_SELO"] = None
        try:
            with self.assertRaises(RuntimeError):
                metrics.reference_bounds("_TESTE_SELO")
        finally:
            del metrics.F_MIN_MAX["_TESTE_SELO"]

    def test_sem_front_d72_barreira(self):
        # [TD-08] true_front_raw barra ANTES de instanciar (21,76 dias-core).
        with self.assertRaises(NotImplementedError):
            metrics.true_front_raw("DDMOP7", 10)

    def test_reference_bounds_known(self):
        ideal, nadir = metrics.reference_bounds("BBOB_F1")
        self.assertTrue(np.allclose(ideal, [0.0, 0.0]))
        self.assertTrue(np.allclose(nadir, [82.042, 82.042]))

    def test_reference_bounds_unknown_raises(self):
        with self.assertRaises(KeyError):
            metrics.reference_bounds("NAO_EXISTE")

    def test_normalize_maps_ideal_to_0_nadir_to_1(self):
        ideal, nadir = np.array([1.0, -2.0]), np.array([3.0, 2.0])
        F = np.array([[1.0, -2.0], [3.0, 2.0], [2.0, 0.0]])
        Fn = metrics.normalize(F, ideal, nadir)
        self.assertTrue(np.allclose(Fn[0], [0.0, 0.0]))
        self.assertTrue(np.allclose(Fn[1], [1.0, 1.0]))
        self.assertTrue(np.allclose(Fn[2], [0.5, 0.5]))

    def test_normalize_range_floor_no_div0(self):
        # nadir == ideal ⇒ range 0 → guarda 1e-12, sem inf/nan.
        Fn = metrics.normalize([[5.0, 5.0]], [5.0, 5.0], [5.0, 5.0])
        self.assertTrue(np.all(np.isfinite(Fn)))


@unittest.skipUnless(_HAVE_METRICS, "sem numpy/pymoo (env-main)")
class TestSmokeAnchor(unittest.TestCase):

    def test_hv_smoke_bbob_f1_is_1_0433(self):
        """A âncora oficial da métrica (D92): HV(BBOB_F1, ref=1,1/coord)=1,0433."""
        hv = metrics.hv_smoke_bbob_f1()
        self.assertAlmostEqual(hv, 1.0433, delta=5e-4)

    def test_hv_front_sanity_is_0_8333(self):
        """Sanity do FRONT (ref no nadir 1,0) — NÃO é o gate (D92)."""
        hv = metrics.hv_front_sanity_bbob_f1()
        self.assertAlmostEqual(hv, 0.8333, delta=5e-4)


@unittest.skipUnless(_HAVE_METRICS, "sem numpy/pymoo (env-main)")
class TestMetricsCore(unittest.TestCase):

    def setUp(self):
        self.Rraw = metrics.true_front_raw("BBOB_F1", 2000)
        ideal, nadir = metrics.reference_bounds("BBOB_F1")
        self.Rn = metrics.normalize(self.Rraw, ideal, nadir)

    def test_front_vs_itself_is_zero(self):
        self.assertAlmostEqual(metrics.igd(self.Rn, self.Rn), 0.0, places=9)
        self.assertAlmostEqual(metrics.igd_plus(self.Rn, self.Rn), 0.0, places=9)
        self.assertAlmostEqual(metrics.gd(self.Rn, self.Rn), 0.0, places=9)

    def test_hv_of_front_matches_anchor(self):
        self.assertAlmostEqual(
            metrics.hv(self.Rn, metrics.HV_REF_COORD), 1.0433, delta=1e-3)

    def test_hv_empty_is_zero(self):
        self.assertEqual(metrics.hv(np.empty((0, 2)), 1.1), 0.0)

    def test_igd_empty_is_nan(self):
        self.assertTrue(np.isnan(metrics.igd(np.empty((0, 2)), self.Rn)))

    def test_spacing_uniform_small_irregular_positive(self):
        sp_unif = metrics.spacing(self.Rn)                 # front analítico ⇒ ~0
        sp_irr = metrics.spacing(
            np.array([[0.0, 1.0], [0.02, 0.9], [0.05, 0.6],
                      [0.5, 0.5], [0.55, 0.1]]))
        self.assertLess(sp_unif, 1e-6)
        self.assertGreater(sp_irr, 0.0)

    def test_spacing_degenerate(self):
        self.assertEqual(metrics.spacing(np.array([[0.1, 0.2]])), 0.0)

    def test_igd_plus_le_igd(self):
        # IGD+ ≤ IGD (a distância modificada nunca é maior) num conjunto pior.
        A = self.Rn[::7] + 0.05
        self.assertLessEqual(metrics.igd_plus(A, self.Rn),
                             metrics.igd(A, self.Rn) + 1e-12)


@unittest.skipUnless(_HAVE_METRICS, "sem numpy/pymoo (env-main)")
class TestReferenceSet(unittest.TestCase):

    def test_size_and_normalized(self):
        R = metrics.reference_set("MMF1", size=1000)
        self.assertLessEqual(R.shape[0], 1000)
        self.assertGreater(R.shape[0], 0)
        self.assertEqual(R.shape[1], 2)
        # normalizado: os valores caem em torno de [0,1] (com folga).
        self.assertTrue(np.all(R >= -0.2) and np.all(R <= 1.5))


@unittest.skipUnless(_HAVE_STACK and _HAVE_METRICS, "sem numpy/pyarrow/pymoo")
class TestReadRealAndTrajectory(unittest.TestCase):

    def _stub_real(self, dr, problema="MMF1"):
        prob = experiment._instantiate_problem(problema)
        Xf, Ff = prob.true_pareto_front(n=20)
        rng = np.random.default_rng(0)
        Xd = prob.xl + rng.random((10, prob.n_var)) * (prob.xu - prob.xl)
        Fd = _P.evaluate_problem(prob, Xd)
        X = np.vstack([Xd, Xf]); F = np.vstack([Fd, Ff])
        recs = [budget.RealEval(solution_id=i, x=X[i], f=F[i], fe_index=i,
                                fase=("init" if i < Xd.shape[0] else "opt"))
                for i in range(X.shape[0])]
        export.write_real("main", "stub", problema, 0, recs, data_root=dr)
        return "main", "stub", problema, 0

    def test_load_real_shape(self):
        with tempfile.TemporaryDirectory() as dr:
            exp, alg, prob, sem = self._stub_real(dr)
            real = metrics.load_real(exp, alg, prob, sem, data_root=dr)
            self.assertEqual(real["M"], 2)
            self.assertEqual(real["F"].shape[1], 2)
            self.assertEqual(real["F"].shape[0], real["fe_index"].shape[0])

    def test_metrics_from_real_full(self):
        with tempfile.TemporaryDirectory() as dr:
            exp, alg, prob, sem = self._stub_real(dr)
            res = metrics.metrics_from_real(exp, alg, prob, sem, data_root=dr,
                                            n_checkpoints=5)
            for k in ("igd", "igd_plus", "hv", "gd", "spacing", "n_nd"):
                self.assertIn(k, res["final"])
            self.assertTrue(np.isfinite(res["final"]["igd_plus"]))
            self.assertGreaterEqual(len(res["trajectory"]), 2)

    def test_trajectory_converges(self):
        # dominados primeiro, front depois ⇒ IGD+ cai e HV sobe ao longo dos FEs.
        with tempfile.TemporaryDirectory() as dr:
            exp, alg, prob, sem = self._stub_real(dr)
            real = metrics.load_real(exp, alg, prob, sem, data_root=dr)
            traj = metrics.trajectory(real["F"], real["fe_index"], prob,
                                      n_checkpoints=5)
            self.assertGreaterEqual(traj[0]["igd_plus"], traj[-1]["igd_plus"])
            self.assertLessEqual(traj[0]["hv"], traj[-1]["hv"])


if __name__ == "__main__":
    unittest.main()
