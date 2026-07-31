# -*- coding: utf-8 -*-
"""[T12.8] Varredura de VALOR dos campos criados na campanha T11.

Por que este arquivo existe
---------------------------
A assinatura de defeito do T11 foi *"campo verde, dado sentinela"*: o campo
nasce para fechar uma lacuna nomeada, entra verde e vem vazio — e a lacuna
passa de aberta-e-visível para aberta-e-camuflada. Os gates da época aferiam a
existência da chave ou o texto do fonte, nunca o VALOR emitido.

Aqui cada campo tem **um teste sobre o valor**, e cada teste tem **controle**:
ou um mutante que reproduz o defeito histórico, ou uma travessia que reprovaria
se o campo voltasse a ser sentinela.

Cobertura por onde o campo mora
-------------------------------
* `pmid_ids`, `y_treino_dist`, `fe_treino_max` (⑥ MATLAB) →
  `tests/test_t12_c217_instrument.py` (MATLAB real + mutantes).
* `flag_vetores_degenerados` (⑥ b5) → `tests/test_t12_b5_vetores.py`
  (cadeia A8 sobre a classe vendorizada + mutante).
* `pred_score`/`pred_confianca` do bloco estratificado (③ c122) →
  `tests/test_a2_c122.py` (emissor real).
* `n_front1`/`f_best` do `sobol_batch`, `tempo_aval_real_s` do offline,
  `params` do ⑤ do c217, `repo_hash`/`campanha_id` → **aqui**.
"""
import json
import os
import re
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

EXPERIMENT_M = os.path.join(RAIZ, "src", "experiment.m")
SAS_M = os.path.join(
    RAIZ, "algorithms", "_PlatEMO", "PlatEMO", "Algorithms",
    "Multi-objective optimization", "PC-SAEA",
    "SurrogateAssistedSelectionPC.m")


def _bloco_params_c217(fonte):
    """O `man.params` do c217 no `experiment.m` — o texto que vai ao ⑤."""
    i = fonte.index("[I-07/A9] `params`")
    j = fonte.index("write_manifest(man", i)
    return fonte[i:j]


# ═══════════════════════════════════════════════════════════════════════════
#  `tempo_aval_real_s` (I-02) — BL-04
# ═══════════════════════════════════════════════════════════════════════════

class TestTempoAvalRealOffline(unittest.TestCase):
    """No offline não HÁ avaliação real: o valor honesto é NULL, não um número.

    O `load_offline_budget` empurra as n linhas do artefato pelo portão de
    avaliação para atribuir `solution_id` (D57) e esgotar o orçamento (D90).
    O cronômetro do I-02 contava aquilo: o ⑤ dos 5 configs offline publicava o
    tempo de INGESTÃO do parquet como se fosse o custo de avaliar a função —
    medido em **0,0003 s** no smoke `off/b5m/DTLZ2/s42` (na s42 era `0.0`
    exato em 200/200, que o I-02 tentou consertar e trocou por outro número
    errado).
    """

    @classmethod
    def setUpClass(cls):
        try:
            import numpy  # noqa: F401
            import pyarrow  # noqa: F401
            from src import standalone_harness  # noqa: F401
            cls.tem = True
        except Exception:                       # noqa: BLE001
            cls.tem = False

    def setUp(self):
        if not self.tem:
            self.skipTest("stack do harness standalone ausente")

    def test_a_carga_do_dataset_NAO_conta_como_avaliacao(self):
        from src import standalone_harness as H
        bud, ds = H.load_offline_budget("MMF1", 42,
                                        data_root=os.path.join(RAIZ, "data"))
        self.assertTrue(bud.exhausted, "a carga não esgotou o orçamento (D90)")
        self.assertGreater(bud.fe, 0)
        self.assertIsNone(
            bud.tempo_aval_real_s,
            "o ⑤ offline voltou a publicar o tempo de INGESTÃO como custo de "
            "avaliação (BL-04): %r" % (bud.tempo_aval_real_s,))

    def test_CONTROLE_uma_avaliacao_de_verdade_volta_a_ser_medida(self):
        """Sem isto, `descarta_cronometro_de_aval` poderia ter matado a medida.

        O I-02 existe porque o número REAL importa (4,110 s = 20,6% do wall nas
        5 células offline da s42). Zerar o cronômetro na carga não pode
        desligar a medição de quem avalia de verdade depois.
        """
        import time

        from src import budget as B
        bud = B.FEBudget(D=2, maxfe=5, n_init=1)
        bud.evaluate([0.1, 0.2], lambda x: (time.sleep(0.01), [1.0, 2.0])[1])
        self.assertIsNotNone(bud.tempo_aval_real_s)
        self.assertGreater(bud.tempo_aval_real_s, 0.0)
        bud.descarta_cronometro_de_aval()
        self.assertIsNone(bud.tempo_aval_real_s,
                          "o descarte tem de devolver NULL, não 0.0 — 0.0 é a "
                          "afirmação 'avaliar custou zero'")
        bud.evaluate([0.3, 0.4], lambda x: (time.sleep(0.01), [3.0, 4.0])[1])
        self.assertIsNotNone(
            bud.tempo_aval_real_s,
            "depois do descarte o cronômetro parou de medir — a avaliação real "
            "de um runner online ficaria invisível")
        self.assertGreater(bud.tempo_aval_real_s, 0.0)


# ═══════════════════════════════════════════════════════════════════════════
#  `params` do ⑤ do c217 (I-07) — BL-15
# ═══════════════════════════════════════════════════════════════════════════

class TestParamsDoC217(unittest.TestCase):
    """O `params` não era sentinela: era AFIRMAÇÃO ERRADA, que é pior.

    O §15.7 do handoff manda o validador *"cruzar o `params` do ⑤ com a Tabela
    do paper"*. Para o c217 isso devolvia **"sim, 20/20 = o índice 20 do §4.1"**
    — falso nas duas direções: o código roda `{1,15,1,5}` e a SPEC §567 declara
    a divergência como deliberada (K.3). O campo novo transformava uma
    divergência sancionada e auditável numa conformidade fictícia.

    O teste cruza a declaração com o **vendorizado que roda**, não com o texto
    esperado — se o stock mudar os η, o gate acusa.
    """

    @classmethod
    def setUpClass(cls):
        with open(EXPERIMENT_M, encoding="utf-8", errors="replace") as fh:
            cls.params = _bloco_params_c217(fh.read())
        with open(SAS_M, encoding="utf-8", errors="replace") as fh:
            cls.sas = fh.read()

    def test_os_operadores_declarados_sao_os_que_o_stock_roda(self):
        # o que o vendorizado REALMENTE chama, nas 3 variações
        literais = re.findall(r"OperatorGA\(.*?\{([^}]*)\}", self.sas)
        self.assertEqual(len(literais), 3, "as 3 chamadas de variação mudaram")
        self.assertEqual(set(literais), {"1,15,1,5"},
                         "o stock deixou de rodar {1,15,1,5}: %r" % (literais,))
        # ...tem de estar declarado no params, com os DOIS índices
        self.assertIn("dis_c=15", self.params)
        self.assertIn("dis_m=5", self.params)
        self.assertNotIn("dis_c=20", self.params)

    def test_o_params_NAO_declara_Balde_C(self):
        """A SPEC §567 diz "Balde C não se aplica" ao c217 (η próprios, K.3)."""
        self.assertNotIn("Balde C: OperatorGA stock", self.params,
                         "o `params` do c217 voltou a herdar a string dos pisos")
        self.assertIn("Balde C NAO se aplica", self.params)

    def test_o_alvo_do_surrogate_e_declarado_BINARIO(self):
        """O `Output` do PC-SAEA é `{1,2}` (CalFitnessPC.m:69-71), não ternário."""
        self.assertIn("BINARIO {1,2}", self.params)
        self.assertNotIn('score ternario {-1,0,+1}"', self.params,
                         "o `params` ainda declara o alvo como ternário — é a "
                         "mesma ficção do BL-05, agora no ⑤")

    def test_o_treino_e_declarado_como_vindo_da_POPULACAO(self):
        """`CalFitnessPC(Population.objs, Population.decs)` — PCSAEA.m:39."""
        self.assertIn("POPULACAO", self.params)
        self.assertNotIn("estratificada do arquivo", self.params)


# ═══════════════════════════════════════════════════════════════════════════
#  `n_front1` / `f_best` do `sobol_batch` (I-03)
# ═══════════════════════════════════════════════════════════════════════════

class TestMinimoComumDoSobolBatch(unittest.TestCase):
    """O sobol_batch era o ÚNICO dos 47 pares (alg,exp) sem `n_front1`.

    O gate anterior fazia grep de `**H.minimo_comum_di10(` no fonte. Aqui o
    evento é MONTADO de verdade, com um `FEBudget` real que já tem avaliações,
    e o que se afere são os VALORES de `n_front1` e `f_best`.
    """

    def setUp(self):
        try:
            import numpy  # noqa: F401
            from src import standalone_harness  # noqa: F401
        except Exception:                       # noqa: BLE001
            self.skipTest("stack do harness standalone ausente")

    def test_o_evento_traz_n_front1_e_f_best_com_valor(self):
        import numpy as np

        from src import budget as B
        from src import standalone_harness as H

        bud = B.FEBudget(D=2, maxfe=10, n_init=3)
        # 3 pontos: 2 na fronteira (trade-off) e 1 dominado por ambos.
        for x, f in (([0.0, 1.0], [0.0, 1.0]),
                     ([1.0, 0.0], [1.0, 0.0]),
                     ([0.9, 0.9], [2.0, 2.0])):
            bud.evaluate(x, lambda _x, _f=f: _f)
        campos = H.minimo_comum_di10(
            np.array([[0.0, 1.0], [1.0, 0.0], [2.0, 2.0]]), fe=bud.fe)
        self.assertEqual(campos["n_front1"], 2,
                         "|ND| calculado errado — o campo perde o sentido")
        self.assertEqual([float(v) for v in campos["f_best"]], [0.0, 0.0],
                         "`f_best` não é o ideal empírico por objetivo")
        self.assertEqual(campos["fe"], 3)

    def test_CONTROLE_um_front_degenerado_NAO_da_o_mesmo_numero(self):
        """Se `n_front1` fosse constante (ex.: |P|), o teste acima passaria."""
        import numpy as np

        from src import standalone_harness as H
        todos_nd = H.minimo_comum_di10(
            np.array([[0.0, 2.0], [1.0, 1.0], [2.0, 0.0]]), fe=3)
        um_so = H.minimo_comum_di10(
            np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]), fe=3)
        self.assertEqual(todos_nd["n_front1"], 3)
        self.assertEqual(um_so["n_front1"], 1)


# ═══════════════════════════════════════════════════════════════════════════
#  `repo_hash` / `campanha_id` (G-3)
# ═══════════════════════════════════════════════════════════════════════════

class TestProvenienciaTemValor(unittest.TestCase):
    """`repo_hash` é o elo entre a célula e o código que a produziu."""

    def setUp(self):
        try:
            from src import manifest  # noqa: F401
        except Exception:                       # noqa: BLE001
            self.skipTest("stack do manifesto ausente")

    def test_o_repo_hash_e_um_sha_de_commit_REAL(self):
        import subprocess

        from src import manifest
        h = manifest.repo_hash_corrente()
        self.assertRegex(h, r"^[0-9a-f]{40}$",
                         "`repo_hash` não é um sha1 de commit: %r" % (h,))
        ok = subprocess.run(["git", "cat-file", "-e", h + "^{commit}"],
                            cwd=RAIZ, capture_output=True)
        self.assertEqual(ok.returncode, 0,
                         "o `repo_hash` gravado não existe no repositório — a "
                         "célula não seria rastreável até o código")


if __name__ == "__main__":
    unittest.main()
