# -*- coding: utf-8 -*-
"""[T15.7b/D102.9 — "Processo B"] A ⑦ pós-hoc do DDMOP7 offline.

Decisão da torre: para problemas cuja avaliação real exige processo EXTERNO
(`PROBLEMAS_FINAL_POS_HOC` — DDMOP7), os runners offline NÃO avaliam a ⑦
inline: declaram no ⑤ (`params.nd_final`, a gramática do e103) e a ⑦ é
gravada pós-hoc por `scripts/final_eval.py` (ramo DDMOP7: motor da ponte +
guard de 600) — o MESMO mecanismo retroativo do e103, MESMO contrato DI-08,
MESMO veredito dos gates (⑦ ausente = vermelho até o final_eval rodar).

Camadas de prova:
  (a) constante canônica + fiação nos 3 runners offline guardados (estrutural
      — b5/piso_offline/treed_media são venv-only, não importáveis aqui) com
      o CONTROLE de que o caminho inline continua vivo p/ os demais problemas;
  (b) `final_eval` ramo DDMOP7 com motor DETERMINÍSTICO (fake da Engine) ⇒
      ⑦ gravada no contrato, sidecar com a certidão do avaliador, `--check`
      verde, idempotência, e os guards (600; matlab.engine ausente ⇒ erro
      ACIONÁVEL);
  (c) gates: o run offline DDMOP7 SEM ⑦ leva do `auditar` EXATAMENTE o achado
      que o e103 leva hoje ("⑦ __final AUSENTE"), e o achado some depois do
      final_eval — nenhum estado novo foi inventado.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np                                        # noqa: E402

from src import export, naming                            # noqa: E402
from src.experiment import (FINAL_POS_HOC_INFO,           # noqa: E402
                            PROBLEMAS_FINAL_POS_HOC,
                            SONDA_AUSENTE_INFO)

EXP, ALG, SEM = "off", "b5m", 0
D, M = 17, 2

try:
    import matlab.engine                                  # noqa: F401
    _HAVE_ENGINE = True
except Exception:                                         # noqa: BLE001
    _HAVE_ENGINE = False


def _final_eval():
    spec = importlib.util.spec_from_file_location(
        "_final_eval_t157b", os.path.join(ROOT, "scripts", "final_eval.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class _MotorFake:
    """Fake DETERMINÍSTICO da Engine (função pura de X) — o `--check`
    re-avalia e TEM de reproduzir; o `_MotorMock` da ponte é estocástico de
    propósito e reprovaria a própria ⑦. `encerra` rastreado (D86)."""

    def __init__(self):
        self.encerrado = False

    def avalia(self, X):
        X = np.atleast_2d(np.asarray(X, dtype=np.float64))
        f1 = (X != 0.0).sum(axis=1) / 17.0
        f2 = 0.5 + 0.1 * np.tanh(X.sum(axis=1))
        return np.column_stack([f1, f2])

    def encerra(self):
        self.encerrado = True


class TestConstanteCanonica(unittest.TestCase):
    def test_ddmop7_esta_no_conjunto_imutavel(self):
        self.assertIsInstance(PROBLEMAS_FINAL_POS_HOC, frozenset)
        self.assertIn("DDMOP7", PROBLEMAS_FINAL_POS_HOC)

    def test_canonicos_ficam_fora(self):
        # ⑦ inline continua o caminho dos demais — o opt-out não vaza.
        for prob in ("MMF1", "ZDT1", "DTLZ2", "WFG9", "BBOB_F1", "RE21",
                     "ESTOQUE40"):
            self.assertNotIn(prob, PROBLEMAS_FINAL_POS_HOC)

    def test_declaracao_cita_decisao_mecanismo_e_precedente(self):
        for trecho in ("D102.9", "Processo B", "final_eval.py", "e103",
                       "DI-08"):
            self.assertIn(trecho, FINAL_POS_HOC_INFO)


class TestFiacaoRunnersOffline(unittest.TestCase):
    """(a) estrutural: b5/piso_offline/treed_media são venv-only (py3.7/3.8,
    desdeo vendorizado) — não importam neste env; a fiação é conferida no
    fonte, com o CONTROLE de que o caminho inline segue vivo."""

    GUARDADOS = ("b5_prob.py", "piso_offline.py", "treed_media.py")

    def _src(self, nome):
        with open(os.path.join(ROOT, "src", nome), encoding="utf-8") as fh:
            return fh.read()

    def test_guarda_antes_do_write_final(self):
        for nome in self.GUARDADOS:
            with self.subTest(arquivo=nome):
                src = self._src(nome)
                self.assertIn("PROBLEMAS_FINAL_POS_HOC", src)
                # a decisão vem ANTES da escrita inline da ⑦
                self.assertLess(src.index("PROBLEMAS_FINAL_POS_HOC"),
                                src.index("H.write_final("))
                # CONTROLE: o caminho inline (os 27 demais) segue vivo
                self.assertIn("H.write_final(", src)
                # a declaração canônica (⑤ params.nd_final) está fiada
                self.assertIn("FINAL_POS_HOC_INFO", src)
                self.assertIn("nd_final", src)

    def test_e103_ja_declarava_a_mesma_gramatica(self):
        # o precedente: o run_e103 declara `nd_final` no params do ⑤ — é a
        # gramática que os runners Python agora copiam (não um dialeto novo).
        with open(os.path.join(ROOT, "src", "experiment.m"),
                  encoding="utf-8") as fh:
            self.assertIn("'nd_final'", fh.read())


def _monta_terceira(td, n_ger=2, n_por_ger=8, seed=7):
    """③ offline sintética MÍNIMA p/ o final_eval/auditar (busca, sem sonda)."""
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(1, n_ger + 1):
        for _ in range(n_por_ger):
            rows.append(export.surrogate_row(
                g, rng.uniform(-1, 1, D), regime="offline",
                real_solution_id=None, mu=[0.5] * M, sigma=[0.1] * M,
                pred_tipo="valor", modelo_flag="TESTE", espaco_modelo="cru",
                fe_treino_max=525))
    export.write_surrogate(EXP, ALG, "DDMOP7", SEM, rows, D=D, M=M,
                           regime="offline", data_root=td)
    return n_por_ger


class TestFinalEvalRamoDDMOP7(unittest.TestCase):
    """(b) o ramo pós-hoc grava a ⑦ no contrato DI-08 e o --check aprova."""

    def _roda(self, td, fe_mod, motor):
        with mock.patch.object(fe_mod, "_motor_pos_hoc", lambda: motor):
            return fe_mod.final_eval_run(EXP, ALG, "DDMOP7", SEM,
                                         data_root=td)

    def test_grava_no_contrato_e_check_aprova(self):
        fe_mod = _final_eval()
        with tempfile.TemporaryDirectory() as td:
            n = _monta_terceira(td)
            motor = _MotorFake()
            r = self._roda(td, fe_mod, motor)
            self.assertEqual(r["status"], "ok")
            self.assertEqual(r["n_final"], n)          # a ÚLTIMA geração
            self.assertTrue(motor.encerrado)           # D86 — sempre
            # certidão do avaliador (a ⑦ NÃO veio do problems.py)
            side = r["sidecar"]
            self.assertIn("DDMOP7.p", side["avaliador"])
            self.assertIn("D102.9", side["avaliador"])
            self.assertTrue(side["origem_precisao"])
            self.assertTrue(side["fora_do_orcamento"])
            # o --check re-avalia pelo MESMO caminho e aprova
            with mock.patch.object(fe_mod, "_motor_pos_hoc",
                                   lambda: _MotorFake()):
                ok, msg = fe_mod.check_final(EXP, ALG, "DDMOP7", SEM,
                                             data_root=td)
            self.assertTrue(ok, msg)
            # idempotência: 2a chamada NÃO reavalia (nem abre motor)
            r2 = fe_mod.final_eval_run(EXP, ALG, "DDMOP7", SEM, data_root=td)
            self.assertEqual(r2["status"], "skip")

    def test_controle_negativo_f_adulterado_reprova(self):
        import pyarrow.parquet as pq
        from src import standalone_harness as sh
        fe_mod = _final_eval()
        with tempfile.TemporaryDirectory() as td:
            _monta_terceira(td)
            self._roda(td, fe_mod, _MotorFake())
            p = naming.final_path(EXP, ALG, "DDMOP7", SEM, data_root=td)
            tbl = pq.read_table(p)
            f0 = tbl.column("f0").combine_chunks().to_numpy(
                zero_copy_only=False).astype(np.float32).copy()
            f0[0] += 0.25                       # 1 f adulterado
            cols = {c: tbl.column(c) for c in tbl.column_names}
            import pyarrow as pa
            cols["f0"] = pa.array(f0, type=pa.float32())
            pq.write_table(pa.table(cols).cast(sh.final_schema(D, M)), p)
            with mock.patch.object(fe_mod, "_motor_pos_hoc",
                                   lambda: _MotorFake()):
                ok, msg = fe_mod.check_final(EXP, ALG, "DDMOP7", SEM,
                                             data_root=td)
            self.assertFalse(ok)
            self.assertIn("INCONSISTENTE", msg)

    def test_guard_600_dispara_antes_do_motor(self):
        fe_mod = _final_eval()
        with self.assertRaisesRegex(RuntimeError, "D88.5"):
            # 601 > teto ⇒ erro ANTES de abrir Engine (nenhum monkeypatch)
            fe_mod.evaluate_final("DDMOP7", np.zeros((601, 17)))

    @unittest.skipIf(_HAVE_ENGINE, "matlab.engine presente — o erro acionável "
                     "só existe onde ele falta")
    def test_sem_engine_falha_acionavel(self):
        fe_mod = _final_eval()
        with self.assertRaisesRegex(RuntimeError, "matlab.engine"):
            fe_mod.evaluate_final("DDMOP7", np.zeros((3, 17)))

    def test_problema_normal_nao_passa_pelo_ramo(self):
        # CONTROLE: MMF1 segue no problems.py canônico (nenhum motor).
        fe_mod = _final_eval()
        chamado = {"n": 0}

        def _boom():
            chamado["n"] += 1
            raise AssertionError("motor pós-hoc chamado p/ problema normal")

        with mock.patch.object(fe_mod, "_motor_pos_hoc", _boom):
            F = fe_mod.evaluate_final("MMF1", np.array([[2.0, 0.0]]))
        self.assertEqual(chamado["n"], 0)
        self.assertEqual(F.shape, (1, 2))


class TestVereditoDosGates(unittest.TestCase):
    """(c) DDMOP7 offline cai no MESMO veredito do e103 — nenhum estado novo."""

    def _monta_celula(self, td):
        """Célula b5m/DDMOP7/off MÍNIMA e verde-exceto-⑦ p/ o auditar."""
        # dataset da célula (mock em tempdir — dá os hashes do CP-init)
        spec = importlib.util.spec_from_file_location(
            "gen_ds_t157b",
            os.path.join(ROOT, "scripts", "gen_dataset_ddmop7.py"))
        g = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(g)
        blocos = g._carrega_csv(g.CSV_DEFAULT)
        ds = g.gen_one(0, blocos[0], csv_sha=g._sha256_file(g.CSV_DEFAULT),
                       data_root=td, engine="mock")
        _monta_terceira(td)
        export.write_timing(EXP, ALG, "DDMOP7", SEM,
                            [{"geracao": 1, "n_acumulado": 526,
                              "tempo_fit_s": 0.1, "tempo_busca_s": 0.1,
                              "tempo_pred_sonda_s": 0.0,
                              "tempo_geracao_s": 0.2}], data_root=td)
        man = {"fe_final": 526, "timing": {"tempo_total_s": 1.0},
               "sigma_dict": {"modelo": "TESTE"},
               "sonda": dict(SONDA_AUSENTE_INFO),
               "params": {"nd_final": FINAL_POS_HOC_INFO},
               "cp_init_offline": {"x_hash": ds["x_hash"],
                                   "f_hash": ds["f_hash"]}}
        mp = naming.manifest_path(EXP, ALG, "DDMOP7", SEM, data_root=td)
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        with open(mp, "w", encoding="utf-8") as fh:
            json.dump(man, fh)

    def test_auditar_mesmo_achado_do_e103_e_some_pos_final_eval(self):
        import scripts.auditar as A
        fe_mod = _final_eval()
        with tempfile.TemporaryDirectory() as td:
            self._monta_celula(td)
            achados = A.audita(ALG, "DDMOP7", SEM, EXP, data_root=td)
            # o ÚNICO achado é a ⑦ pendente — o MESMO texto que o e103 leva
            # (ramo `alg in OFFLINE` do auditar, sem estado novo).
            self.assertEqual(len(achados), 1, achados)
            self.assertIn("⑦ __final AUSENTE", achados[0])
            # pós-hoc roda ⇒ o achado some (célula VERDE)
            with mock.patch.object(fe_mod, "_motor_pos_hoc",
                                   lambda: _MotorFake()):
                r = fe_mod.final_eval_run(EXP, ALG, "DDMOP7", SEM,
                                          data_root=td)
            self.assertEqual(r["status"], "ok")
            self.assertEqual(A.audita(ALG, "DDMOP7", SEM, EXP,
                                      data_root=td), [])

    def test_check_final_ausente_mesmo_veredito_para_b5m_e_e103(self):
        fe_mod = _final_eval()
        with tempfile.TemporaryDirectory() as td:
            ok1, m1 = fe_mod.check_final(EXP, "b5m", "DDMOP7", SEM,
                                         data_root=td)
            ok2, m2 = fe_mod.check_final(EXP, "e103", "DDMOP7", SEM,
                                         data_root=td)
            self.assertFalse(ok1)
            self.assertFalse(ok2)
            self.assertIn("camada ⑦ ausente", m1)
            self.assertIn("camada ⑦ ausente", m2)


if __name__ == "__main__":
    unittest.main()
