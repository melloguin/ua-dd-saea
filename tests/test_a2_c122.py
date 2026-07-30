# -*- coding: utf-8 -*-
"""[T11-A2] c122 — I-01 `n_ref` real · I-1 `ref_ids` · I-2 regra do rótulo · I-5 `y_treino_dist`.

* **I-01** — o `n_ref` era o literal `MU` em 7 sítios, mas o bloco de sonda g=1 é
  emitido ANTES da truncagem: naquele instante a população ainda é a
  NÃO-truncada. Medido na s42: o bloco-1 excede o teto H0(=2N) em **22/25**
  problemas e H1(=2·(11D−1)) em **0/25**; no ZDT4 o `max e(z)` = **108,944778** =
  99,949% de 109 = 11D−1, contra **11,000000 EXATO** no g≥2 (0/202.000
  violações); ρ(custo, (11D−1)/N) = **0,9990**. Com o rótulo errado, a queda
  bloco-1→bloco-2 (mediana **16,5×**) seria lida como "o surrogate degradou" em
  750 blocos. ⚠ NÃO se muda QUANDO a sonda dispara — só o metadado.
* **I-1** — sem os IDS da referência a qualidade do classificador é
  NÃO-MENSURÁVEL a posteriori (0/25 células tinham). O b4 já loga `ref_ids`.
* **I-2** — a regra do rótulo verdadeiro: no b4, as 3 definições plausíveis dão
  acurácia **0,350 / 0,999 / 0,995** sobre as MESMAS 280 gerações. "Acurácia do
  classificador" não é um número enquanto a regra não estiver escrita.
* **I-5** — `y_treino_dist` separa "classificador ruim" de "problema
  desbalanceado".

O smoke REAL (c122/MMF1/s0) mediu: **n_ref=21 (=11D−1) no g=1 · n_ref=11 (=MU) no
g≥2** — o teste de aceitação do I-01, com D=2.
"""
import json
import os
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

try:
    import numpy as np
    from src import c122_thetadeadp as C
    _TEM = True
except Exception:                                   # noqa: BLE001
    _TEM = False


@unittest.skipUnless(_TEM, "stack do c122 ausente")
class TestNRefRealI01(unittest.TestCase):

    class _BudFalso:
        def solution_id_of(self, x):
            return int(round(float(np.asarray(x).ravel()[0]) * 10))

    def test_meta_declara_o_tamanho_REAL_e_o_nominal(self):
        pop = [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6)]
        m = C._meta_referencia(pop, self._BudFalso(), mu_nominal=11)
        self.assertEqual(m["n_ref"], 3)          # o REAL
        self.assertEqual(m["n_ref_nominal"], 11)  # o que o algoritmo pede
        self.assertFalse(m["n_ref_truncada"])     # 3 != 11 ⇒ ainda não truncou

    def test_truncada_quando_o_real_bate_o_nominal(self):
        pop = [(0.1, 0.2)] * 11
        m = C._meta_referencia(pop, self._BudFalso(), mu_nominal=11)
        self.assertTrue(m["n_ref_truncada"])

    def test_ref_ids_traz_a_identidade(self):
        pop = [(0.1, 0.0), (0.2, 0.0), (0.3, 0.0)]
        m = C._meta_referencia(pop, self._BudFalso(), mu_nominal=11)
        self.assertEqual(m["ref_ids"], [1, 2, 3])

    def test_o_literal_MU_saiu_do_evento_de_geracao(self):
        with open(C.__file__, encoding="utf-8") as fh:
            src = fh.read()
        # o `n_ref=MU` do `log.decision` era o rótulo errado em 750 blocos
        self.assertNotIn("cid=tel.get(\"cid\"), n_ref=MU", src)
        self.assertIn("n_ref=len(pop), n_ref_nominal=MU", src)


@unittest.skipUnless(_TEM, "stack do c122 ausente")
class TestYTreinoDistI5(unittest.TestCase):
    """I-5: as 3 classes do par-a-par, contadas SÓ nos pares já computados."""

    def test_conta_as_3_classes_e_os_nao_computados(self):
        m = np.array([[0, 1, -1],
                      [2, 0, 1],
                      [-1, 2, 0]], dtype=np.int8)
        d = C._y_treino_dist([0, 1, 2], m)
        self.assertEqual(d["n_pares_possiveis"], 9)
        self.assertEqual(d["n_pares_computados"], 7)     # 2 são −1
        self.assertEqual(d["classe_0_empate"], 3)
        self.assertEqual(d["classe_1_i_domina"], 2)
        self.assertEqual(d["classe_2_j_domina"], 2)

    def test_recorta_o_bloco_do_arquivo_corrente(self):
        # o rel_map nasce (maxfe × maxfe): contar a matriz inteira mediria
        # pares que não existem
        m = np.full((10, 10), -1, dtype=np.int8)
        m[:3, :3] = 0
        d = C._y_treino_dist([0, 1, 2], m)
        self.assertEqual(d["n_pares_possiveis"], 9)
        self.assertEqual(d["n_arquivo"], 3)

    def test_arquivo_vazio_devolve_none(self):
        self.assertIsNone(C._y_treino_dist([], np.zeros((3, 3), dtype=np.int8)))

    def test_nunca_derruba_o_run(self):
        # instrumentação com formato inesperado devolve None, não estoura (D97)
        self.assertIsNone(C._y_treino_dist([1, 2], None))


@unittest.skipUnless(_TEM, "stack do c122 ausente")
class TestRegraDoRotuloI2(unittest.TestCase):

    def test_o_sigma_dict_declara_CONTRA_O_QUE_o_modelo_classifica(self):
        # o `sigma_dict` descrevia o que a COLUNA contém, nunca contra o quê —
        # e a escolha da regra move a acurácia de 0,35 para 0,995 (medido no b4)
        import inspect
        src = inspect.getsource(C)
        i = src.index('"REGRA_DO_ROTULO"')
        bloco = src[i:i + 1400]
        for pista in ("ref_ids", "pareto_dominance", "scalar_dominance",
                      "y_treino_dist", "§17.2.2"):
            with self.subTest(pista=pista):
                self.assertIn(pista, bloco)


@unittest.skipUnless(_TEM, "stack do c122 ausente")
class TestSondaLevaOsMetadados(unittest.TestCase):

    def test_emit_sonda_block_aceita_meta(self):
        import inspect

        from src.standalone_harness import emit_sonda_block
        self.assertIn("meta", inspect.signature(emit_sonda_block).parameters)

    def test_as_DUAS_emissoes_do_c122_levam_meta(self):
        # a da cadência E a final: se só uma levasse, o bloco da última geração
        # (que a §3.1 torna obrigatório) sairia com o rótulo velho
        with open(C.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count("meta=_meta_referencia(pop, bud, MU)"), 2)


if __name__ == "__main__":
    unittest.main()
