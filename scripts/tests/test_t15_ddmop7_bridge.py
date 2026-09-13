# -*- coding: utf-8 -*-
"""[T15.7 §1/§5] A ponte do DDMOP7 na rota R2 — bind/avalia/encerra + D89.

O que se prova AQUI (mock da Engine — a ponte tem engine='mock'):
  * a casca `problems.DDMOP7` liga com contabilidade EXTERNA por default e,
    nesse caminho, a ponte NÃO conta FE, NÃO deduplica e NÃO grava catálogo —
    o FEBudget do harness é o ÚNICO contador (D89), com o gêmeo de VALOR
    (cache-hit no budget ⇒ o motor nem é tocado);
  * controle: contabilidade='propria' (standalone/smoke) PRESERVA o arnês
    histórico completo (fe, dedup, hard-stop exato em 526);
  * o DoE oficial: artefato parquet ≡ CSV congelado bit-a-bit; fallback CSV
    com AVISO; sidecar divergente ⇒ RuntimeError (D63 não relaxa no fallback);
  * resolução da pasta do .p (explícita > UA_DD_SAEA_DDMOP_DIR > default);
  * bind nos adapters dos runners (gêmeos standalone/botorch) + encerra
    idempotente; sem bind ⇒ RuntimeError pára-e-loga (D81).

O que NÃO se prova aqui: a Engine REAL (skip declarado sem matlab.engine —
validada pela torre no smoke C3; a âncora de VALOR do .p vive no teste MATLAB
`test_t15_ddmop7_matlab.py`).
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
import warnings
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np                                        # noqa: E402

from src import ddmop7_bridge as B                        # noqa: E402
from src import problems as P                             # noqa: E402
from src.budget import FEBudget                           # noqa: E402

DATA = os.path.join(ROOT, "data")

try:
    import matlab.engine                                  # noqa: F401
    _HAVE_ENGINE = True
except Exception:                                         # noqa: BLE001
    _HAVE_ENGINE = False


def _ponte_mock():
    """Substituto de `_importa_ponte_ddmop7` que crava engine='mock' — para
    exercitar o caminho bind/avalia/encerra dos ADAPTERS sem MATLAB."""
    class _MockPonte(B.DDMOP7Matlab):
        def __init__(self, semente, **kw):
            kw.setdefault("engine", "mock")
            super().__init__(semente, **kw)
    return _MockPonte


class TestResolveProblemsDir(unittest.TestCase):
    def test_explicito_vence(self):
        with mock.patch.dict(os.environ, {"UA_DD_SAEA_DDMOP_DIR": "/env/x"}):
            self.assertEqual(B.resolve_problems_dir("/exp/y"), "/exp/y")

    def test_env_vence_default(self):
        with mock.patch.dict(os.environ, {"UA_DD_SAEA_DDMOP_DIR": "/env/x"}):
            self.assertEqual(B.resolve_problems_dir(None), "/env/x")

    def test_default_e_home(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("UA_DD_SAEA_DDMOP_DIR", None)
            d = B.resolve_problems_dir(None)
        self.assertEqual(
            d, os.path.expanduser(os.path.join(
                "~", "DDMOP", "DDMOP_Exp", "Problems")))


class TestDoEOficial(unittest.TestCase):
    """D63: artefato parquet ≡ CSV congelado; fallback com aviso E com hash."""

    def test_artefato_e_csv_bit_a_bit(self):
        X_art = B.carrega_doe_oficial(0, data_root=DATA)
        X_csv = B.carrega_doe(0, B.CSV_DOE_CONGELADO)
        self.assertEqual(X_art.shape, (186, 17))
        self.assertTrue(np.array_equal(X_art, X_csv))
        # zeros NEGATIVOS preservados nas DUAS rotas (D63 — bit patterns)
        neg = np.signbit(X_art) & (X_art == 0.0)
        self.assertGreater(int(neg.sum()), 0)
        self.assertTrue(np.array_equal(np.signbit(X_art), np.signbit(X_csv)))

    def test_fallback_csv_avisa_e_devolve_o_mesmo(self):
        with tempfile.TemporaryDirectory() as td:      # sem artefato parquet
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                X = B.carrega_doe_oficial(0, data_root=td)
            self.assertTrue(any("FALLBACK" in str(x.message) for x in w),
                            [str(x.message) for x in w])
        self.assertTrue(np.array_equal(
            X, B.carrega_doe_oficial(0, data_root=DATA)))

    def test_fallback_confere_sidecar_quando_ha(self):
        # controle NEGATIVO: sidecar presente com hash adulterado ⇒ mesmo na
        # rota CSV o D63 detecta (o fallback não relaxa a disciplina).
        import json
        with tempfile.TemporaryDirectory() as td:
            d = os.path.join(td, "doe", "DDMOP7")
            os.makedirs(d)
            with open(os.path.join(d, "doe_DDMOP7_0.manifest.json"), "w",
                      encoding="utf-8") as fh:
                json.dump({"doe_hash": "deadbeef"}, fh)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with self.assertRaisesRegex(RuntimeError, "DIVERGEM"):
                    B.carrega_doe_oficial(0, data_root=td)

    def test_nem_artefato_nem_csv(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                B.carrega_doe_oficial(0, data_root=td,
                                      csv_path=os.path.join(td, "nao_ha.csv"))


class TestContabilidadeExterna(unittest.TestCase):
    """§1.3/D89: na R2 a ponte é avaliador CRU sob o FEBudget do harness."""

    def _casca_mock(self, semente=0, **kw):
        p = P.DDMOP7()
        return p.bind(semente, engine="mock", data_root=DATA, **kw)

    def test_casca_liga_externa_por_default(self):
        p = self._casca_mock()
        self.assertEqual(p._ponte.contabilidade, "externa")
        p.encerra()

    def test_override_propria_disponivel(self):
        p = self._casca_mock(contabilidade="propria")
        self.assertEqual(p._ponte.contabilidade, "propria")
        p.encerra()

    def test_contabilidade_desconhecida_e_erro(self):
        with self.assertRaises(ValueError):
            B.DDMOP7Matlab(semente=0, engine="mock", contabilidade="dupla")

    def test_avaliador_cru_nao_conta_nem_cataloga(self):
        p = self._casca_mock()
        X = np.linspace(-0.9, 0.9, 3 * 17).reshape(3, 17)
        F = P.evaluate_problem(p, X)
        self.assertEqual(F.shape, (3, 2))
        self.assertTrue(np.all(np.isfinite(F)))
        # ASSERÇÃO DE VALOR do D89: fe/catálogo da ponte ZERADOS de propósito;
        # só o contador do teto do .p (que NÃO é contabilidade) avança.
        self.assertEqual(p._ponte.fe, 0)
        self.assertEqual(len(p._ponte.cat), 0)
        self.assertEqual(p._ponte.n_cache_hits, 0)
        self.assertEqual(p._ponte.chamadas_p, 3)
        p.encerra()

    def test_febudget_e_o_unico_contador(self):
        p = self._casca_mock()
        bud = FEBudget(D=17)

        def true_f(x):
            return P.evaluate_problem(
                p, np.asarray(x, dtype=np.float64).reshape(1, -1)).reshape(-1)

        x = np.linspace(-0.5, 0.5, 17)
        f1 = bud.evaluate(x, true_f)
        self.assertEqual(bud.fe, 1)
        self.assertEqual(p._ponte.chamadas_p, 1)
        # cache-hit: o BUDGET devolve a memória e o MOTOR nem é tocado —
        # gêmeo de valor da unicidade do contador (se a ponte deduplicasse em
        # paralelo, chamadas_p avançaria OU o F divergiria).
        f2 = bud.evaluate(x, true_f)
        self.assertEqual(bud.fe, 1)
        self.assertEqual(bud.cache_hits, 1)
        self.assertEqual(p._ponte.chamadas_p, 1)
        self.assertTrue(np.array_equal(np.asarray(f1), np.asarray(f2)))
        self.assertEqual(p._ponte.fe, 0)
        p.encerra()

    def test_guard_600_vale_tambem_no_modo_externa(self):
        # D88.5 não é contabilidade — o teto do .p protege o PROCESSO.
        p = self._casca_mock()
        p._ponte.chamadas_p = 599
        with self.assertRaisesRegex(RuntimeError, "D88.5"):
            P.evaluate_problem(p, np.zeros((2, 17)))
        p.encerra()

    def test_nao_finito_para_e_loga(self):
        p = self._casca_mock()
        with mock.patch.object(p._ponte.motor, "avalia",
                               return_value=np.full((1, 2), np.nan)):
            with self.assertRaisesRegex(RuntimeError, "nao-finito"):
                P.evaluate_problem(p, np.zeros((1, 17)))
        p.encerra()

    def test_forma_errada_para_e_loga(self):
        p = self._casca_mock()
        with mock.patch.object(p._ponte.motor, "avalia",
                               return_value=np.zeros((1, 3))):
            with self.assertRaises(RuntimeError):
                P.evaluate_problem(p, np.zeros((1, 17)))
        p.encerra()

    def test_manifesto_declara_contabilidade(self):
        p = self._casca_mock()
        m = p.manifesto()
        self.assertEqual(m["contabilidade"], "externa")
        self.assertIn("AVISO_CONTABILIDADE", m)
        self.assertEqual(m["engine"], "mock")
        self.assertIn("AVISO", m)               # mock NUNCA passa por real
        p.encerra()

    def test_encerra_idempotente(self):
        p = self._casca_mock()
        p.encerra()
        p.encerra()                             # 2a chamada = no-op seguro


class TestContabilidadePropriaPreservada(unittest.TestCase):
    """Controle do controle: o modo standalone/smoke segue o arnês histórico."""

    def test_arnes_completo_ate_o_hard_stop(self):
        p = B.DDMOP7Matlab(semente=0, engine="mock",
                           contabilidade="propria", data_root=DATA)
        out = {}
        p._evaluate(p.doe, out)
        self.assertEqual(p.fe, 186)
        self.assertEqual(len(p.cat), 186)
        # cache-hit próprio (D57.5)
        p._evaluate(p.doe[:5], out)
        self.assertEqual(p.fe, 186)
        self.assertEqual(p.n_cache_hits, 5)
        # infills até o hard-stop exato (D21/D61)
        rng = np.random.default_rng(0)
        with self.assertRaises(B.BudgetExhausted):
            while True:
                p._evaluate(rng.uniform(-1, 1, size=(37, 17)), out)
        self.assertEqual(p.fe, 526)
        self.assertEqual(len(p.cat), 526)
        self.assertEqual(p.chamadas_p, 526)     # < 600: cabe no processo
        c1 = p.camada1()
        self.assertEqual(c1["x"].dtype, np.float32)
        self.assertEqual(c1["x"].shape, (526, 17))
        p.encerra()


class TestBindNosAdapters(unittest.TestCase):
    """§1.2: quem conhece a semente liga; sem bind ⇒ RuntimeError (D81)."""

    def test_problema_ligado_standalone(self):
        from src import standalone_harness as H
        with mock.patch.object(P, "_importa_ponte_ddmop7", _ponte_mock):
            prob = H.problema_ligado("DDMOP7", 5)
            self.assertTrue(prob.ligado)
            self.assertEqual(prob.semente, 5)
            self.assertEqual(prob._ponte.contabilidade, "externa")
            H.encerra_problema(prob)

    def test_sem_semente_fica_desligado_e_para_e_loga(self):
        from src import standalone_harness as H
        prob = H.problema_ligado("DDMOP7", None)
        self.assertFalse(prob.ligado)
        with self.assertRaisesRegex(RuntimeError, "D81"):
            P.evaluate_problem(prob, np.zeros((1, 17)))

    def test_no_op_para_os_27(self):
        from src import standalone_harness as H
        prob = H.problema_ligado("MMF1", 3)
        self.assertEqual(prob.n_var, 2)
        H.encerra_problema(prob)                # no-op sem `encerra`
        H.encerra_problema(None)                # no-op com None

    def test_gemeo_botorch_concorda(self):
        from src import botorch_harness as BH
        from src import standalone_harness as H
        with mock.patch.object(P, "_importa_ponte_ddmop7", _ponte_mock):
            pa = BH.problema_ligado("DDMOP7", 7)
            pb = H.problema_ligado("DDMOP7", 7)
            try:
                self.assertTrue(pa.ligado and pb.ligado)
                self.assertEqual(pa.semente, pb.semente)
                self.assertEqual(pa._ponte.contabilidade,
                                 pb._ponte.contabilidade)
            finally:
                BH.encerra_problema(pa)
                H.encerra_problema(pb)

    def test_adapter_botorch_liga_e_o_budget_conta(self):
        from src import botorch_harness as BH
        from src import budget as _budget
        with mock.patch.object(P, "_importa_ponte_ddmop7", _ponte_mock):
            bud = _budget.FEBudget(D=17)
            ad = BH.BoTorchProblemAdapter("DDMOP7", bud, semente=4)
            try:
                self.assertTrue(ad.problem.ligado)
                self.assertEqual(ad.D, 17)
                self.assertEqual(ad.M, 2)
                f = ad.evaluate_native(np.zeros(17))
                self.assertEqual(np.asarray(f).shape, (2,))
                self.assertEqual(bud.fe, 1)
                self.assertEqual(ad.problem._ponte.fe, 0)      # D89
            finally:
                BH.encerra_problema(ad.problem)

    def test_adapters_dos_runners_r3_ligam(self):
        # a fiação REAL: _Adapter (c122) e _Oracle (c149/e81) com semente.
        from src.budget import FEBudget as FB
        from src.c122_thetadeadp import _Adapter
        from src.c149_lbnmobo import _Oracle as O149
        from src.e81_qpots import _Oracle as O81
        with mock.patch.object(P, "_importa_ponte_ddmop7", _ponte_mock):
            for cls in (_Adapter, O149, O81):
                with self.subTest(cls=cls.__qualname__):
                    a = cls("DDMOP7", FB(D=17), semente=2)
                    self.assertTrue(a._p.ligado)
                    from src import standalone_harness as H
                    H.encerra_problema(a._p)


@unittest.skipUnless(_HAVE_ENGINE, "matlab.engine ausente neste interpretador "
                     "— o caminho da Engine REAL é validado no smoke C3 da "
                     "torre (e foi provado 1x nesta sessão via o venv "
                     "env_matlab_engine: âncoras [4/17, 307/690] batidas)")
class TestEngineReal(unittest.TestCase):        # pragma: no cover
    def test_bind_avalia_encerra(self):
        p = P.DDMOP7().bind(0, data_root=DATA)
        try:
            xA = np.zeros((1, 17))
            xA[0, 2], xA[0, 6] = 0.5, -0.2
            F = P.evaluate_problem(p, xA)
            self.assertLessEqual(abs(F[0, 0] - 4 / 17), 1e-12)
            self.assertLessEqual(abs(F[0, 1] - 307 / 690), 1e-12)
        finally:
            p.encerra()


if __name__ == "__main__":
    unittest.main()
