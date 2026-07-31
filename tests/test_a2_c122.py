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

    def test_emit_sonda_block_LEVA_o_meta_ao_evento(self):
        # [T12.7] Era `assertIn("meta", signature(...))`: provava que o
        # parâmetro EXISTE, não que ele chega ao ⑥. Um `meta` aceito e
        # descartado passaria verde — e o bloco sairia com o rótulo velho.
        import numpy as np

        from src.standalone_harness import emit_sonda_block

        class _Buf:
            def __init__(self):
                self.rows = []

            def add_surrogate(self, row):
                self.rows.append(row)

        class _Log:
            def __init__(self):
                self.eventos = []

            def event(self, kind, **campos):
                self.eventos.append((kind, campos))

        buf, log = _Buf(), _Log()
        X = np.array([[0.1, 0.2], [0.3, 0.4]])
        sonda = {"X": X, "x_hash": "abc", "f_hash": "def"}
        emit_sonda_block(
            buf, log, geracao=2, fe=9, sonda=sonda,
            predict=lambda Z: (np.zeros(Z.shape[0]), np.ones(Z.shape[0])),
            fe_treino_max=8, pred_tipo="score",
            meta={"n_ref": 21, "n_ref_nominal": 11, "ref_ids": [1, 2, 3]})
        kind, campos = log.eventos[0]
        self.assertEqual(kind, "sonda")
        self.assertEqual(campos["n_ref"], 21)
        self.assertEqual(campos["n_ref_nominal"], 11)
        self.assertEqual(campos["ref_ids"], [1, 2, 3])
        # e o `meta` NÃO contamina a ③ (ele é do ⑥, por contrato)
        self.assertNotIn("n_ref", buf.rows[0])

    def test_TODAS_as_emissoes_do_c122_levam_meta(self):
        # 3 sítios: a sonda da cadência, a sonda FINAL (que a §3.1 torna
        # obrigatória) e o bloco ESTRATIFICADO do A11. Se um só ficasse de fora,
        # aquele bloco sairia com o rótulo velho (`n_ref` nominal) e a análise
        # não saberia contra o que ele mediu.
        with open(C.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count("meta=_meta_referencia(pop, bud, MU)"), 3)

class TestA6SobolBatchENsga3(unittest.TestCase):
    """[T11-A6] I-03 (`n_front1` no sobol_batch) + I-13 (`geracoes_derivadas`).

    * **I-03** — o sobol_batch montava o evento à mão em vez de chamar
      `H.minimo_comum_di10`: era o ÚNICO dos 47 pares (alg,exp) do estudo sem
      `n_front1` (presente em 46/47), e o campo faltava também no header, nos 2
      footers e nas 31 chaves do ⑤. Custo de gravá-lo: 0,020–0,052 s = 0,3–1,6%
      do wall.
    * **I-13** — a string `geracoes_derivadas` dos 4 pisos. MEDIDO nas 112
      células de piso da s42: a string antiga (`20D ÷ N_efetivo`) acerta
      **2/112**; a fórmula do plano F5 (com `ceil`) acerta **0/112**; a melhor
      aproximação (`floor((20D+n_dup)/(2⌊N_ef/2⌋))`) acerta **103/112**. Logo:
      `n_geracoes` é EMERGENTE, e o metadado passa a dizer isso em vez de
      prometer uma fórmula fechada que não existe.
    """

    def test_sobol_batch_usa_o_minimo_comum(self):
        with open(os.path.join(_RAIZ, "src", "sobol_batch.py"),
                  encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("**H.minimo_comum_di10(", src)
        # o `f_best` montado à mão saiu (o helper o entrega junto de n_front1)
        self.assertNotIn('f_best=[float(v) for v in', src)

    def test_a_string_do_piso_nao_promete_formula_fechada(self):
        with open(os.path.join(_RAIZ, "src", "experiment.m"),
                  encoding="utf-8", errors="replace") as fh:
            m = fh.read()
        i = m.index("'geracoes_derivadas'")
        bloco = m[i:i + 1200]
        self.assertIn("EMERGENTE", bloco)
        self.assertIn("103/112", bloco)          # a acurácia MEDIDA da aproximação
        self.assertNotIn('"20D ÷ N_efetivo', bloco)
        self.assertIn("nao derive, LEIA", bloco)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(_TEM, "stack do c122 ausente")
class TestA11SondaEstratificada(unittest.TestCase):
    """[T11-A11/I-6/D11] O bloco que destrava precision/recall dos classificadores.

    Pontos Sobol quase nunca são "bons": prevalência medida **0,4%** ⇒ ~8
    positivos por bloco de 2.000, e com 8 positivos precision/recall/F1 têm
    variância enorme (só o AUC é estável). Subir para 3.000 Sobol NÃO resolve —
    a prevalência não muda, só o n. **A estratificação é o que resolve.**

    Medido no smoke (c122/MMF1/s0): prevalência de ND no bloco estratificado =
    **7,4%** contra 0,4% da régua — 18× mais positivos. E os regimes ficam
    SEPARADOS na ③: 44.000 `sonda` · 10.500 `sonda_estratificada` · 3.632 busca.
    """

    def test_amostra_fica_dentro_dos_bounds(self):
        from src.standalone_harness import amostra_estratificada
        A = np.array([[0.02, 0.98], [0.99, 0.01]])     # arquivo NAS BORDAS
        X = amostra_estratificada(A, [0, 0], [1, 1], n=400, semente_bloco=7)
        self.assertEqual(X.shape, (400, 2))
        self.assertTrue((X >= 0).all() and (X <= 1).all())

    def test_e_deterministica_por_semente(self):
        from src.standalone_harness import amostra_estratificada
        A = np.array([[0.5, 0.5]])
        a = amostra_estratificada(A, [0, 0], [1, 1], n=50, semente_bloco=3)
        b = amostra_estratificada(A, [0, 0], [1, 1], n=50, semente_bloco=3)
        c = amostra_estratificada(A, [0, 0], [1, 1], n=50, semente_bloco=4)
        self.assertTrue(np.array_equal(a, b))
        self.assertFalse(np.array_equal(a, c))

    def test_fica_PERTO_do_arquivo(self):
        # é o ponto do item: a amostra tem de cair na vizinhança do arquivo,
        # senão é uma régua Sobol com outro nome
        from src.standalone_harness import amostra_estratificada
        A = np.array([[0.5, 0.5]])
        X = amostra_estratificada(A, [0, 0], [1, 1], n=2000, semente_bloco=1)
        d = np.linalg.norm(X - A[0], axis=1)
        self.assertLess(float(np.median(d)), 0.12)     # σ_rel=0,05 por dimensão

    def test_arquivo_vazio_devolve_bloco_vazio(self):
        from src.standalone_harness import amostra_estratificada
        X = amostra_estratificada(np.empty((0, 2)), [0, 0], [1, 1], n=10)
        self.assertEqual(X.shape[0], 0)

    # ── [T12.7] Os 5 gates abaixo eram `inspect.getsource` + `assertIn` ──────
    # Eles aferiam o TEXTO da função e passaram VERDES sobre o BL-03 (10.500 de
    # 10.500 linhas com o score par-a-par gravado em `mu_0` e `pred_score`
    # NULL). Agora cada um EXECUTA `emit_sonda_estratificada` e afere a LINHA
    # emitida — é a diferença entre "a função menciona X" e "a ③ contém X".

    @staticmethod
    def _emite(pred_tipo="score", n=8, true_f=None):
        """Roda o emissor de verdade e devolve `(linhas da ③, evento do ⑥)`."""
        from src import standalone_harness as H

        class _Buf:
            def __init__(self):
                self.rows = []

            def add_surrogate(self, row):
                self.rows.append(row)

        class _Log:
            def __init__(self):
                self.eventos = []

            def event(self, kind, **campos):
                self.eventos.append((kind, campos))

        buf, log = _Buf(), _Log()
        A = np.array([[0.5, 0.5], [0.2, 0.8]])
        # `predict` do CLASSIFICADOR par-a-par: (valor, confiança) 1-D — a
        # mesma forma que o `emit_sonda_block` documenta para score/classe.
        def predict(X):
            return (np.linspace(-1.0, 1.0, X.shape[0]),
                    np.full(X.shape[0], 0.25))

        H.emit_sonda_estratificada(
            buf, log, geracao=3, fe=17, arquivo_X=A, xl=[0, 0], xu=[1, 1],
            predict=predict, true_f=true_f, fe_treino_max=16,
            pred_tipo=pred_tipo, n=n, semente_bloco=5)
        return buf.rows, log.eventos[0]

    def test_o_regime_e_SEPARADO_da_regua(self):
        # NUNCA misturar: cada algoritmo tem um arquivo diferente, então o bloco
        # não é comparável ENTRE configs (a ressalva da opção (b) do laudo §6).
        rows, (kind, _) = self._emite()
        self.assertEqual(kind, "sonda_estratificada")
        self.assertTrue(rows)
        self.assertEqual({r["regime"] for r in rows}, {"sonda_estratificada"},
                         "alguma linha entrou na régua Sobol")

    def test_o_score_vai_para_pred_score_e_NAO_para_mu(self):
        """[BL-03] O defeito que os 5 gates de texto deixaram passar.

        `mu_j` significa "média do posterior de um regressor". Gravar ali o
        score par-a-par do c122 (que é um CLASSIFICADOR) envenena a leitura da
        ③ pela R4 — e deixa `pred_score` NULL, que é onde a análise procura.
        A função irmã (`emit_sonda_block`) já ramifica por `pred_tipo`; esta
        não ramificava, e o guard do writer não pega porque `len(mu)=1 < M=2`
        é o caso legítimo do b1 mono-output.
        """
        rows, _ = self._emite(pred_tipo="score")
        for r in rows:
            self.assertIsNone(r["mu"], "o score foi para `mu` — BL-03")
            self.assertIsNone(r["sigma"], "a confiança foi para `sigma` — BL-03")
            self.assertIsNotNone(r["pred_score"], "`pred_score` saiu NULL")
            self.assertIsNotNone(r["pred_confianca"])
        self.assertEqual([float(r["pred_score"]) for r in rows],
                         list(np.linspace(-1.0, 1.0, len(rows))),
                         "o score emitido não é o que o `predict` devolveu")

    def test_o_regressor_continua_indo_para_mu_e_sigma(self):
        """O controle do teste acima: ramificar não pode quebrar o `valor`."""
        rows, _ = self._emite(pred_tipo="valor")
        for r in rows:
            self.assertIsNotNone(r["mu"])
            self.assertIsNone(r["pred_score"])

    def test_o_f_verdadeiro_NAO_vai_para_a_terceira(self):
        # o schema da ③ é contrato (§3): mudá-lo custaria re-run de tudo por
        # ZERO informação nova — os problemas são analíticos e o f é
        # recomputável do X gravado (mesma doutrina do I-12). O que vai ao ⑥ é
        # o AGREGADO: a prevalência da classe positiva no bloco.
        rows, (_, campos) = self._emite(
            true_f=lambda X: np.column_stack([X[:, 0], 1.0 - X[:, 0]]))
        self.assertNotIn("f_verdadeiro", rows[0])
        self.assertIn("prevalencia_nd_no_bloco", campos)
        prev = campos["prevalencia_nd_no_bloco"]
        self.assertIsNotNone(prev, "a prevalência saiu NULL com `true_f` dado")
        self.assertGreater(prev, 0.0)
        self.assertLessEqual(prev, 1.0)

    def test_roda_sob_preserve_all_rng(self):
        # a amostragem E a predição consomem RNG; sem a guarda, MEDIR MOVERIA A
        # BUSCA e o run inteiro seria inválido (invariante §3.1). Aferido no
        # ESTADO do RNG global, não no texto do `with`.
        import random
        np.random.seed(4242)
        random.seed(4242)
        antes_np = np.random.get_state()
        antes_py = random.getstate()
        self._emite(n=200)
        depois_np = np.random.get_state()
        self.assertEqual(antes_np[0], depois_np[0])
        self.assertTrue(np.array_equal(antes_np[1], depois_np[1]),
                        "o bloco estratificado MOVEU o RNG do numpy — a busca "
                        "sai diferente com e sem instrumento (§3.1)")
        self.assertEqual(antes_np[2:], depois_np[2:])
        self.assertEqual(antes_py, random.getstate(),
                         "o bloco estratificado MOVEU o RNG do `random`")

    def test_o_c122_usa_uso_id_proprio_no_RNG(self):
        # a semente do bloco sai do catálogo D62/D91 com `uso_id` dedicado —
        # reusar o uso_id da busca acoplaria instrumento e algoritmo
        from src.standalone_harness import SONDA_ESTRAT_USO
        self.assertEqual(SONDA_ESTRAT_USO, 91)
        with open(C.__file__, encoding="utf-8") as fh:
            self.assertIn("H.SONDA_ESTRAT_USO", fh.read())
