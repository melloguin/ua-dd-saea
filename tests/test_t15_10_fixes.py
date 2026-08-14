"""Testes dos fixes de COMPORTAMENTO do T15.10 (revisão adversarial 2026-08-14).

Cobrem os 3 achados de runtime cuja regressão seria silenciosa em campanha:

  * nº 7  — `manifest.is_run_done`: célula offline de problema PÓS-HOC
            (D102.9) com o ⑤ declarando `params.nd_final` está PRONTA sem a
            ⑦; sem a declaração, a exigência da ⑦ segue de pé (achado A3 da
            DI-20 continua fechado para todo o resto).
  * nº 11 — `ddmop7_bridge._MotorMatlab.encerra`: Engine marcada TRAVADA
            (pós-BridgeTimeout) NÃO recebe o eval síncrono de higiene (ele
            penduraria o worker para sempre); o quit continua acontecendo.
  * nº 15 — `final_eval.check_final`: máquina sem matlab.engine/.p devolve
            `(None, "NÃO-AFERÍVEL…")` — INCONCLUSIVO (B-07), nunca vermelho —
            e o `portao._sub` mapeia exit 2 para `None` (DI-41).

Tudo em tempdir; nenhum teste toca `data/` nem depende de MATLAB.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import numpy as np  # noqa: F401
    import pyarrow  # noqa: F401
    _HAS_STACK = True
except ImportError:
    _HAS_STACK = False

_SKIP = "numpy/pyarrow ausentes neste interpretador — rode no env-main"
_CAMP = "T15_TESTE_LOCAL"


def _load_final_eval():
    """`scripts/` não é pacote — mesmo recurso do test_r3_final_eval."""
    p = os.path.join(ROOT, "scripts", "final_eval.py")
    spec = importlib.util.spec_from_file_location("_final_eval_t1510", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- achado nº 7

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestIsRunDonePosHoc(unittest.TestCase):
    """A exceção declarada do pós-hoc — e SÓ ela — dispensa a ⑦."""

    def _monta_run(self, dr, alg, problema, *, declara_pos_hoc, com_final):
        """⑤ + camadas ①–④ sintéticos mínimos; a ⑦ é opcional."""
        from src import naming
        man = {"status": "ok", "campanha_id": _CAMP,
               "fe_final": 600, "maxfe": 600, "params": {}}
        if declara_pos_hoc:
            from src.experiment import FINAL_POS_HOC_INFO
            # se a constante virar falsy um dia, a exceção morre em silêncio
            # e TODA célula offline DDMOP7 volta a re-executar a cada resume.
            self.assertTrue(FINAL_POS_HOC_INFO)
            man["params"]["nd_final"] = FINAL_POS_HOC_INFO
        mp = naming.manifest_path("off", alg, problema, 0, dr)
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        with open(mp, "w", encoding="utf-8") as fh:
            json.dump(man, fh)
        for ly in naming.LAYERS:
            p = naming.layer_path("off", alg, problema, 0, ly, dr)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").close()
        if com_final:
            p = naming.layer_path("off", alg, problema, 0,
                                  naming.FINAL_LAYER, dr)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").close()

    def _done(self, dr, alg, problema):
        from src.manifest import is_run_done
        return is_run_done("off", alg, problema, 0, dr,
                           check_footers=False, campanha_id=_CAMP)

    def test_pos_hoc_declarado_dispensa_a_setima(self):
        with tempfile.TemporaryDirectory() as dr:
            self._monta_run(dr, "b5r", "DDMOP7",
                            declara_pos_hoc=True, com_final=False)
            self.assertTrue(self._done(dr, "b5r", "DDMOP7"))

    def test_sem_declaracao_a_setima_segue_exigida(self):
        """Achado A3 (DI-20) intacto: offline sem ⑦ E sem declaração ⇒ re-roda."""
        with tempfile.TemporaryDirectory() as dr:
            self._monta_run(dr, "b5r", "DDMOP7",
                            declara_pos_hoc=False, com_final=False)
            self.assertFalse(self._done(dr, "b5r", "DDMOP7"))

    def test_com_a_setima_presente_pronto_como_sempre(self):
        with tempfile.TemporaryDirectory() as dr:
            self._monta_run(dr, "b5r", "DDMOP7",
                            declara_pos_hoc=False, com_final=True)
            self.assertTrue(self._done(dr, "b5r", "DDMOP7"))

    def test_declaracao_em_problema_nao_pos_hoc_nao_dispensa(self):
        """A exceção é POR PROBLEMA (PROBLEMAS_FINAL_POS_HOC), não pela mera
        presença do campo — um ⑤ adulterado de ZDT1 não compra dispensa."""
        with tempfile.TemporaryDirectory() as dr:
            self._monta_run(dr, "b5r", "ZDT1",
                            declara_pos_hoc=True, com_final=False)
            self.assertFalse(self._done(dr, "b5r", "ZDT1"))

    def test_online_nunca_exigiu_a_setima(self):
        with tempfile.TemporaryDirectory() as dr:
            self._monta_run(dr, "nsga2", "DDMOP7",
                            declara_pos_hoc=False, com_final=False)
            self.assertTrue(self._done(dr, "nsga2", "DDMOP7"))


# --------------------------------------------------------------- achado nº 11

class _EngGravadora:
    """Fake do matlab.engine: grava o que foi chamado, nunca trava."""

    def __init__(self):
        self.evals: list = []
        self.quit_chamado = False

    def eval(self, *a, **k):
        self.evals.append(a)

    def quit(self):
        self.quit_chamado = True


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestEncerraTravada(unittest.TestCase):
    """Engine TRAVADA ⇒ encerra() pula o eval de higiene e vai direto ao quit."""

    def _motor(self):
        from src.ddmop7_bridge import _MotorMatlab
        m = object.__new__(_MotorMatlab)          # sem __init__: sem MATLAB
        m.eng = _EngGravadora()
        return m

    def test_travada_pula_o_eval_de_higiene(self):
        m = self._motor()
        eng = m.eng
        m._travada = True                          # o que o BridgeTimeout seta
        m.encerra()
        self.assertEqual(eng.evals, [],
                         "eval síncrono numa Engine travada = worker pendurado "
                         "para sempre (achado nº 11)")
        self.assertTrue(eng.quit_chamado)
        self.assertIsNone(m.eng)

    def test_sadia_mantem_a_higiene_d86(self):
        m = self._motor()
        eng = m.eng
        m.encerra()                                # sem _travada
        self.assertEqual(len(eng.evals), 1, "a higiene D86 sumiu do caminho são")
        self.assertIn("clear DDMOP7", eng.evals[0][0])
        self.assertTrue(eng.quit_chamado)


# ------------------------------------------------- O-18 · watchdog da partida

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestBootComPrazo(unittest.TestCase):
    """`_boot_com_prazo`: o antídoto do handshake pendurado (MEDIDO 14/08:
    37 min de `start_matlab` sem retorno, MATLAB ocioso, zero exceção)."""

    def test_estouro_vira_bridge_timeout(self):
        import time as _t
        from src.ddmop7_bridge import BridgeTimeout, _boot_com_prazo
        with self.assertRaises(BridgeTimeout) as cm:
            _boot_com_prazo(lambda: _t.sleep(30), 0.2, "boot de teste")
        self.assertIn("O-18", str(cm.exception))

    def test_valor_atravessa(self):
        from src.ddmop7_bridge import _boot_com_prazo
        self.assertEqual(_boot_com_prazo(lambda: 42, 5.0, "x"), 42)

    def test_excecao_do_boot_atravessa(self):
        from src.ddmop7_bridge import _boot_com_prazo

        def _explode():
            raise FileNotFoundError("DDMOP7.p sumiu")
        with self.assertRaises(FileNotFoundError):
            _boot_com_prazo(_explode, 5.0, "x")


# --------------------------------------------------------------- achado nº 15

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestCheckFinalNaoAferivel(unittest.TestCase):
    """Sem Engine na máquina: ⑦ do DDMOP7 é NÃO-AFERÍVEL (None), não vermelha."""

    def _monta_setima(self, dr):
        from src import standalone_harness as sh
        rng = np.random.default_rng(7)
        X = rng.uniform(-1.0, 1.0, size=(3, 17))
        F = np.column_stack([np.array([4, 5, 6]) / 17.0,
                             np.array([310, 305, 300]) / 690.0])
        sh.write_final("off", "b5r", "DDMOP7", 0, X, F,
                       origem_geracao=[1, 1, 1], origem_linha=[0, 1, 2],
                       data_root=dr)

    def test_sem_engine_vira_none_nunca_vermelho(self):
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            self._monta_setima(dr)

            def _sem_engine(problema, X):
                raise RuntimeError(
                    "matlab.engine indisponível nesta máquina (instale a "
                    "partir da árvore do MATLAB — ver locks)")
            fe.evaluate_final = _sem_engine
            ok, msg = fe.check_final("off", "b5r", "DDMOP7", 0, data_root=dr)
            self.assertIsNone(ok, msg)
            self.assertIn("NÃO-AFERÍVEL", msg)

    def test_runtime_error_generico_segue_vermelho(self):
        """Só a INCAPACIDADE de medir vira ⛔ — falha real de reavaliação
        continua reprovando (senão todo estouro viraria 'inconclusivo')."""
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            self._monta_setima(dr)

            def _falha_real(problema, X):
                raise RuntimeError("colapso numérico qualquer")
            fe.evaluate_final = _falha_real
            ok, msg = fe.check_final("off", "b5r", "DDMOP7", 0, data_root=dr)
            self.assertIs(ok, False, msg)


# ------------------------------------------------------- exit 2 = None (DI-41)

class TestPortaoExitDois(unittest.TestCase):
    """`portao._sub`: 0→verde, 2→None (INCONCLUSIVO), resto→vermelho."""

    @classmethod
    def setUpClass(cls):
        sp = os.path.join(ROOT, "scripts")
        if sp not in sys.path:
            sys.path.insert(0, sp)
        import portao
        cls.portao = portao

    def test_mapa_de_exit_codes(self):
        for codigo, esperado in ((0, True), (2, None), (1, False), (3, False)):
            verde, _ = self.portao._sub(
                ["-c", f"import sys; sys.exit({codigo})"])
            self.assertIs(verde, esperado,
                          f"exit {codigo} devia mapear para {esperado}")


if __name__ == "__main__":
    unittest.main()
