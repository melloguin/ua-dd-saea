"""Testes da CODIFICAÇÃO zona-morta do DDMOP7 (T15.12 / REAL-2.15/D102.15).

Cobrem o contrato inteiro da codificação:
  * a função canônica (`zona_morta`): semântica, zeros EXATOS, idempotência;
  * a isenção do DoE na rota R2 (`DDMOP7Matlab.avalia`): os primeiros 186
    pontos passam CRUS, do 187º em diante a codificação aplica — inclusive
    num lote que ATRAVESSA a fronteira;
  * a paridade R1↔R2: as constantes do `.m` são extraídas por parsing e
    comparadas às do python (o par não pode divergir em silêncio);
  * a ⑦ (`final_eval`): candidatos pós-hoc são TODOS codificados, e o
    filtro ND-da-predição (bloqueador 2) reduz população grande antes do
    teto de 600.

Tudo em tempdir/mock — nenhum MATLAB, nenhuma escrita em data/.
"""

from __future__ import annotations

import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import numpy as np
    import pyarrow  # noqa: F401
    _HAS_STACK = True
except ImportError:
    _HAS_STACK = False

_SKIP = "numpy/pyarrow ausentes neste interpretador — rode no env-main"


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestFuncaoCanonica(unittest.TestCase):

    def test_semantica_e_zero_exato(self):
        from src.ddmop7_bridge import TAU_ZONA_MORTA, zona_morta
        x = np.array([[0.49999, -0.49999, 0.5, -0.5, 0.51, -1.0, 0.0]])
        y = zona_morta(x)
        # |x| < tau vira zero EXATO (bit); |x| >= tau fica intocado
        self.assertEqual(y[0, 0], 0.0)
        self.assertEqual(y[0, 1], 0.0)
        self.assertEqual(y[0, 2], 0.5)      # fronteira: >= tau NAO zera
        self.assertEqual(y[0, 3], -0.5)
        self.assertEqual(y[0, 4], 0.51)
        self.assertEqual(y[0, 5], -1.0)
        self.assertEqual(y[0, 6], 0.0)
        self.assertEqual(TAU_ZONA_MORTA, 0.5)

    def test_idempotente_e_nao_muta_entrada(self):
        from src.ddmop7_bridge import zona_morta
        rng = np.random.default_rng(3)
        X = rng.uniform(-1, 1, (50, 17))
        X0 = X.copy()
        Y = zona_morta(X)
        self.assertTrue(np.array_equal(X, X0), "zona_morta mutou a entrada")
        self.assertTrue(np.array_equal(zona_morta(Y), Y), "não idempotente")


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestIsencaoDoDoeR2(unittest.TestCase):
    """A fronteira DoE/busca na rota R2, via motor mock (sem MATLAB)."""

    def _prob(self):
        from src.ddmop7_bridge import DDMOP7Matlab
        return DDMOP7Matlab(semente=0, engine="mock")

    def test_doe_cru_busca_codificada_e_lote_na_fronteira(self):
        from src.ddmop7_bridge import N_DOE_ONLINE
        prob = self._prob()
        capturados = []
        avalia_motor = prob.motor.avalia

        def espiao(X):
            capturados.append(np.array(X, copy=True))
            return avalia_motor(X)
        prob.motor.avalia = espiao

        rng = np.random.default_rng(1)
        doe = rng.uniform(-1, 1, (N_DOE_ONLINE, 17))     # tudo |x|<1, sem 0
        # lote 1: 100 pontos do DoE — CRUS
        prob.avalia(doe[:100])
        self.assertTrue(np.array_equal(capturados[-1], doe[:100]),
                        "DoE foi codificado — corromperia o congelado")
        # lote 2: ATRAVESSA a fronteira (86 do DoE + 14 da busca)
        lote = np.vstack([doe[100:], rng.uniform(-1, 1, (14, 17))])
        prob.avalia(lote)
        visto = capturados[-1]
        self.assertTrue(np.array_equal(visto[:86], lote[:86]),
                        "parte-DoE do lote fronteiriço foi codificada")
        from src.ddmop7_bridge import zona_morta
        self.assertTrue(np.array_equal(visto[86:], zona_morta(lote[86:])),
                        "parte-busca do lote fronteiriço passou crua")
        # lote 3: pós-DoE puro — TODO codificado (e com zeros exatos)
        prop = rng.uniform(-0.49, 0.49, (5, 17))          # tudo dentro do tau
        prob.avalia(prop)
        self.assertTrue(np.all(capturados[-1] == 0.0),
                        "propostas 100%-na-zona-morta deviam virar zero")
        self.assertEqual(prob.n_pontos_zona_morta, 14 + 5)


class TestParidadeR1R2(unittest.TestCase):
    """As constantes do `.m` (rota R1) extraídas por parsing ≡ python."""

    def test_constantes_espelhadas(self):
        m = open(os.path.join(ROOT, "src", "ddmop7_value_local.m"),
                 encoding="utf-8").read()
        tau = re.search(r"TAU_ZONA_MORTA\s*=\s*([0-9.]+)\s*;", m)
        ndoe = re.search(r"N_DOE_ONLINE\s*=\s*11\s*\*\s*D\s*-\s*1\s*;", m)
        self.assertIsNotNone(tau, "TAU_ZONA_MORTA sumiu do .m")
        self.assertIsNotNone(ndoe, "N_DOE_ONLINE sumiu do .m (11*D-1)")
        if _HAS_STACK:
            from src.ddmop7_bridge import TAU_ZONA_MORTA
            self.assertEqual(float(tau.group(1)), TAU_ZONA_MORTA,
                             "tau divergiu entre R1 (.m) e R2 (python)")
        # o corte pos-DoE existe no .m (ini_dz) e cobre lote fronteirico
        self.assertIn("ini_dz", m)
        self.assertIn("abs(Xdz) < TAU_ZONA_MORTA", m)


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestSetimaNDFiltrada(unittest.TestCase):
    """Bloqueador 2: candidatos da ⑦ pós-hoc = ND da predição da ③."""

    def _monta_terceira(self, dr, n_pop, problema="DDMOP7"):
        import importlib.util
        import tempfile  # noqa: F401
        from src import export, naming
        rng = np.random.default_rng(5)
        os.makedirs(naming.run_dir("off", "b5r", data_root=dr), exist_ok=True)
        rows = []
        X = rng.uniform(-1, 1, (n_pop, 17))
        mu = np.column_stack([np.linspace(0, 1, n_pop),
                              np.linspace(1, 0, n_pop)])   # front perfeito...
        mu[n_pop // 2:, 1] = 2.0                            # ...metade dominada
        for i in range(n_pop):
            rows.append(export.surrogate_row(
                7, X[i], regime="offline", mu=mu[i], sigma=None,
                pred_tipo="valor", modelo_flag="fake", fe_treino_max=10))
        export.write_surrogate("off", "b5r", problema, 0, rows, D=17, M=2,
                               regime="offline", data_root=dr)
        p = os.path.join(ROOT, "scripts", "final_eval.py")
        spec = importlib.util.spec_from_file_location("_fe_zm", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, X

    def test_populacao_grande_reduz_para_nd_da_predicao(self):
        import tempfile
        with tempfile.TemporaryDirectory() as dr:
            mod, X = self._monta_terceira(dr, n_pop=800)
            cand = mod.read_final_candidates("off", "b5r", "DDMOP7", 0,
                                             data_root=dr)
            # metade dominada cai fora; só o front-na-predição fica
            self.assertLessEqual(cand["X"].shape[0], 400)
            self.assertGreater(cand["X"].shape[0], 0)
            # o join posicional sobrevive: linhas apontam o bloco original
            self.assertTrue(np.array_equal(
                cand["X"],
                X.astype(np.float32).astype(np.float64)[cand["linhas"]]))

    def test_problema_nao_pos_hoc_fica_intacto(self):
        import tempfile
        with tempfile.TemporaryDirectory() as dr:
            mod, X = self._monta_terceira(dr, n_pop=60, problema="MMF1")
            cand = mod.read_final_candidates("off", "b5r", "MMF1", 0,
                                             data_root=dr)
            self.assertEqual(cand["X"].shape[0], 60,
                             "config fora do rol pós-hoc foi ND-filtrado — "
                             "mudaria a semântica do corpus coletado")


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestEspacoEntradaGpPiso(unittest.TestCase):
    """Bloqueador 3: o critério mecânico do espaço de entrada do GP do piso."""

    def test_caixa_grande_normaliza_e_roundtrip_exato(self):
        from src.piso_offline import _espaco_entrada_gp
        rng = np.random.default_rng(9)
        xl, xu = np.zeros(40), np.full(40, 3000.0)     # caixa estilo ESTOQUE40
        X = xl + rng.random((300, 40)) * (xu - xl)
        n2g, g2n, X_gp, xl_gp, xu_gp, info = _espaco_entrada_gp(X, xl, xu)
        self.assertEqual(info["modo"], "minmax_caixa")
        self.assertTrue(np.all(X_gp >= 0) and np.all(X_gp <= 1))
        self.assertTrue(np.allclose(g2n(n2g(X)), X, rtol=0, atol=1e-9),
                        "roundtrip nat→gp→nat perdeu precisão")

    def test_caixa_pequena_fica_crua_retro_consistente(self):
        from src.piso_offline import _espaco_entrada_gp
        rng = np.random.default_rng(9)
        xl, xu = np.zeros(10), np.ones(10)              # caixa ZDT
        X = rng.random((300, 10))
        n2g, g2n, X_gp, xl_gp, xu_gp, info = _espaco_entrada_gp(X, xl, xu)
        self.assertEqual(info["modo"], "cru")
        self.assertTrue(np.array_equal(X_gp, X),
                        "caixa pequena mudou — quebraria a retro-consistência "
                        "com o corpus sintético coletado")

    def test_deterministico_e_nao_consome_rng(self):
        from src.piso_offline import _espaco_entrada_gp
        rng = np.random.default_rng(2)
        X = rng.random((500, 5)) * 4000
        xl, xu = np.zeros(5), np.full(5, 4000.0)
        np.random.seed(123)
        antes = np.random.get_state()[1][:3].copy()
        r1 = _espaco_entrada_gp(X, xl, xu)[5]
        depois = np.random.get_state()[1][:3]
        self.assertTrue(np.array_equal(antes, depois),
                        "o critério consumiu o RNG global — quebra D62")
        r2 = _espaco_entrada_gp(X, xl, xu)[5]
        self.assertEqual(r1, r2)


if __name__ == "__main__":
    unittest.main()
