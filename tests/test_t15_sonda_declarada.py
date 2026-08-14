# -*- coding: utf-8 -*-
"""[T15.3/D102.10] Runners e gates toleram sonda ausente POR PROBLEMA.

Doutrina do CONTROLE NEGATIVO (T12): cada aceite tem o seu gêmeo que REPROVA —
o `auditar` que aceita o ③ sem sonda de um problema declarado tem de REPROVAR
o MESMO ③ com linhas de sonda (sonda onde não devia é tão grave quanto falta
onde devia), e tem de continuar reprovando um problema COM sonda sem linhas
(o opt-out não pode virar silenciador geral).

ASSERÇÃO DE VALOR: o bloco ⑤ declarado é conferido campo a campo (status
inconfundível com 'nao_se_aplica' e 'artefato_ausente' — as duas espécies de
None já catalogadas), nunca só truthiness.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import export, naming                            # noqa: E402
from src.experiment import (PROBLEMAS_SEM_SONDA,          # noqa: E402
                            SONDA_AUSENTE_INFO)

EXP, ALG, SEM = "main", "c149", 0
D, M = 3, 2


class TestFormaCanonica(unittest.TestCase):
    """(a) A forma canônica de SONDA_AUSENTE_INFO — campo a campo."""

    def test_chaves_exatas(self):
        self.assertEqual(set(SONDA_AUSENTE_INFO),
                         {"status", "motivo", "n_blocos", "n_linhas", "S"})

    def test_status_unico_e_inconfundivel(self):
        # As TRÊS ausências têm de ser inconfundíveis (duas espécies de None).
        self.assertEqual(SONDA_AUSENTE_INFO["status"], "sem_sonda_por_problema")
        self.assertNotEqual(SONDA_AUSENTE_INFO["status"], "nao_se_aplica")
        self.assertNotEqual(SONDA_AUSENTE_INFO["status"], "artefato_ausente")

    def test_contadores_zerados(self):
        self.assertEqual(SONDA_AUSENTE_INFO["n_blocos"], 0)
        self.assertEqual(SONDA_AUSENTE_INFO["n_linhas"], 0)
        self.assertEqual(SONDA_AUSENTE_INFO["S"], 0)

    def test_motivo_cita_a_decisao(self):
        self.assertIn("D102.10", SONDA_AUSENTE_INFO["motivo"])

    def test_ddmop7_esta_declarado(self):
        # O caso concreto do cartão: DDMOP7 (id 26) é o problema sem régua.
        self.assertIn("DDMOP7", PROBLEMAS_SEM_SONDA)


def _linha_busca(g):
    return export.surrogate_row(
        g, [0.1 * g] * D, regime="online", real_solution_id=None,
        mu=[1.0] * M, sigma=[0.1] * M, pred_tipo="valor",
        modelo_flag="TESTE", espaco_modelo="cru", transf_tipo="zscore",
        transf_params={"m": [0.0] * M}, fe_treino_max=10)


def _linha_sonda(i):
    return export.surrogate_row(
        2, [0.01 * i] * D, regime="sonda", real_solution_id=None,
        mu=[1.0] * M, sigma=[0.1] * M, pred_tipo="valor",
        modelo_flag="TESTE", espaco_modelo="cru", fe_treino_max=10)


def _monta_run(td, prob, *, com_sonda, sonda_5):
    """Run online sintético MÍNIMO para o `audita` (③ + ④ + ⑤); tempdir SEMPRE."""
    rows = [_linha_busca(g) for g in range(1, 5)]
    if com_sonda:
        rows += [_linha_sonda(i) for i in range(5)]
    export.write_surrogate(EXP, ALG, prob, SEM, rows, D=D, M=M,
                           regime="online", data_root=td)
    export.write_timing(EXP, ALG, prob, SEM,
                        [{"geracao": 1, "n_acumulado": 10, "tempo_fit_s": 0.1,
                          "tempo_busca_s": 0.1, "tempo_pred_sonda_s": 0.0,
                          "tempo_geracao_s": 0.2}], data_root=td)
    man = {"fe_final": 92, "timing": {"tempo_total_s": 1.0},
           "sigma_dict": {"modelo": "TESTE"}}
    if sonda_5 is not None:
        man["sonda"] = sonda_5
    mp = naming.manifest_path(EXP, ALG, prob, SEM, data_root=td)
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(man, fh)


class TestAuditarSemSonda(unittest.TestCase):
    """(b) O ramo novo do `auditar` — aceite + os dois controles negativos."""

    def _audita(self, td, prob):
        import scripts.auditar as A
        return A.audita(ALG, prob, SEM, EXP, data_root=td)

    def test_aceita_ausencia_declarada(self):
        with tempfile.TemporaryDirectory() as td:
            _monta_run(td, "DDMOP7", com_sonda=False,
                       sonda_5=dict(SONDA_AUSENTE_INFO))
            self.assertEqual(self._audita(td, "DDMOP7"), [])

    def test_reprova_sonda_onde_nao_devia(self):
        # O MESMO ③, agora COM linhas de sonda ⇒ VERMELHO (controle do controle).
        with tempfile.TemporaryDirectory() as td:
            _monta_run(td, "DDMOP7", com_sonda=True,
                       sonda_5=dict(SONDA_AUSENTE_INFO))
            achados = self._audita(td, "DDMOP7")
            self.assertTrue(achados)
            self.assertTrue(any("D102.10" in a for a in achados), achados)

    def test_reprova_5_sem_declaracao(self):
        # ③ correto mas ⑤ mudo (bloco de hash comum) ⇒ a ausência NÃO declarada
        # reprova — truthiness não basta (asserção de valor).
        with tempfile.TemporaryDirectory() as td:
            _monta_run(td, "DDMOP7", com_sonda=False,
                       sonda_5={"S": 2000, "x_hash": "deadbeef"})
            achados = self._audita(td, "DDMOP7")
            self.assertTrue(any("sem_sonda_por_problema" in a
                                for a in achados), achados)

    def test_reprova_status_de_outra_especie(self):
        # 'artefato_ausente' (acidente) NÃO vale como declaração D102.10.
        with tempfile.TemporaryDirectory() as td:
            _monta_run(td, "DDMOP7", com_sonda=False,
                       sonda_5={"status": "artefato_ausente", "motivo": "x"})
            achados = self._audita(td, "DDMOP7")
            self.assertTrue(any("sem_sonda_por_problema" in a
                                for a in achados), achados)

    def test_nao_superbloqueia_problema_com_sonda(self):
        # MMF1 (fora do opt-out) sem NENHUMA linha de sonda ⇒ continua VERMELHO.
        with tempfile.TemporaryDirectory() as td:
            _monta_run(td, "MMF1", com_sonda=False, sonda_5={"S": 2000})
            achados = self._audita(td, "MMF1")
            self.assertTrue(any("SEM nenhuma linha de sonda" in a
                                for a in achados), achados)


class TestRunnerStandaloneSondaInfo(unittest.TestCase):
    """(c) standalone: o trecho do c149 que monta o `sonda_info` com sonda=None."""

    def test_none_vira_bloco_declarado(self):
        from src import c149_lbnmobo as C
        from src import standalone_harness as H
        buf = H.SnapshotBuffer()
        info = C._sonda_info(None, buf)
        self.assertEqual(info, SONDA_AUSENTE_INFO)
        # cópia fresca — mutar o retorno não pode corromper a constante.
        info["n_blocos"] = 99
        self.assertEqual(SONDA_AUSENTE_INFO["n_blocos"], 0)

    def test_com_sonda_mantem_a_forma_antiga(self):
        from src import c149_lbnmobo as C
        from src import standalone_harness as H
        buf = H.SnapshotBuffer()
        for _ in range(4):
            buf.add_surrogate({"regime": "sonda"})
        info = C._sonda_info({"S": 2, "x_hash": "a", "f_hash": "b"}, buf)
        self.assertEqual(info["S"], 2)
        self.assertEqual(info["n_blocos"], 2)
        self.assertEqual(info["x_hash"], "a")
        self.assertNotIn("status", info)      # run COM sonda não declara ausência

    def test_stub_harness_decl(self):
        from src import standalone_harness as H
        self.assertEqual(H._sonda_decl(), SONDA_AUSENTE_INFO)


class TestRunnerBotorchSondaInfo(unittest.TestCase):
    """(c) botorch: o `_sonda_header` do c262 (header ⑥ E bloco ⑤) com None."""

    def test_none_vira_bloco_declarado(self):
        from src.c262_qnehvi import _sonda_header
        hdr = _sonda_header(None)
        self.assertEqual(hdr, SONDA_AUSENTE_INFO)
        hdr["S"] = 99                          # cópia fresca
        self.assertEqual(SONDA_AUSENTE_INFO["S"], 0)

    def test_com_sonda_mantem_a_forma_antiga(self):
        from src.c262_qnehvi import _sonda_header
        art = {"S": 2000, "x_hash": "a", "f_hash": "b", "path": "p"}
        hdr = _sonda_header(art)
        self.assertEqual(hdr["S"], 2000)
        self.assertEqual(hdr["x_hash"], "a")
        self.assertNotIn("status", hdr)

    def test_gemeo_c154_concorda(self):
        # Os 2 runners BoTorch declaram o MESMO bloco (nenhum dialeto próprio).
        from src.c154_jes import _sonda_header as h154
        from src.c262_qnehvi import _sonda_header as h262
        self.assertEqual(h262(None), h154(None))


if __name__ == "__main__":
    unittest.main()
