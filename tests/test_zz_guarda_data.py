# -*- coding: utf-8 -*-
"""[G-8] A guarda que fecha a CLASSE do defeito B-13 — roda por ÚLTIMO.

`unittest discover` executa os módulos em ordem alfabética, e é por isso que
este arquivo se chama `test_zz_*`: quando ele roda, todos os outros já rodaram.
A fotografia de `data/experiments/**` foi tirada no import de `tests/__init__.py`
— antes do primeiro teste — e aqui se cobra que NADA mudou.

Por que a classe importa mais que a instância: o B-13 foi corrigido com um
tempdir em `test_batch_q10.py`, mas nada impedia o próximo teste de escrever em
`data/` outra vez. Este guarda transforma "disciplina" em "propriedade do
código" — o mesmo argumento do B-02 (o F5 §7.3 escreveu: *"agente de análise não
invoca experiments.py, nem para no-op — e, com o B-02 aplicado, isso deixa de ser
regra de disciplina e passa a ser propriedade do código"*).
"""
import unittest

from tests import DATA_EXP, IMPRESSAO_INICIAL, impressao_data_experiments


class TestGuardaAntiEscritaEmProducao(unittest.TestCase):

    def test_a_suite_nao_tocou_data_experiments(self):
        n_antes, h_antes = IMPRESSAO_INICIAL
        n_depois, h_depois = impressao_data_experiments()
        self.assertEqual(
            (n_antes, h_antes), (n_depois, h_depois),
            "🔴 [G-8/B-13] A SUÍTE ESCREVEU EM DADOS DE PRODUÇÃO.\n"
            f"    {DATA_EXP}\n"
            f"    entradas: {n_antes} → {n_depois}\n"
            "    Todo teste que roda um runner/despachante TEM de passar um "
            "`data_root` em `tempfile.TemporaryDirectory()`. Foi assim que 47 "
            "execuções da suíte deixaram 94 pares header/footer espúrios no ⑥ "
            "de `batch/e81/q10_ZDT4` (B-13). Ache o teste pela lista de "
            "arquivos com mtime novo sob `data/experiments/`.")

    def test_a_propria_guarda_pega_uma_violacao(self):
        # controle: sem isto, um bug na fotografia deixaria a guarda cega.
        import os
        import tempfile
        if not os.path.isdir(DATA_EXP):
            self.skipTest("sem data/experiments neste checkout")
        antes = impressao_data_experiments()
        with tempfile.NamedTemporaryFile(dir=DATA_EXP, suffix=".violacao"):
            durante = impressao_data_experiments()
        depois = impressao_data_experiments()
        self.assertNotEqual(antes, durante, "a guarda não viu o arquivo novo")
        self.assertEqual(antes[0], depois[0])   # e o rastro foi desfeito


if __name__ == "__main__":
    unittest.main()
