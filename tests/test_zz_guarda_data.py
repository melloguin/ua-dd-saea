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
        """CONTROLE: sem isto, um bug na fotografia deixaria a guarda cega.

        ⚠ [conserto 2026-07-30] Este controle plantava o arquivo em
        `data/experiments` DE PRODUÇÃO. Ele só não disparava a própria guarda
        porque a impressão era cega à RAIZ — criar e apagar um arquivo lá muda o
        mtime do diretório-raiz, e o `os.walk` estatava apenas os filhos. Ao
        fechar aquele ponto cego, o controle passou a acusar a si mesmo. Agora
        ele mede a SENSIBILIDADE da função num tempdir: é a mesma propriedade
        (a impressão reage a um arquivo novo) sem tocar em produção.
        """
        import os
        import tempfile
        with tempfile.TemporaryDirectory(prefix="g8_controle_") as base:
            os.makedirs(os.path.join(base, "main", "zz"))
            antes = impressao_data_experiments(base)
            with tempfile.NamedTemporaryFile(dir=base, suffix=".violacao"):
                durante = impressao_data_experiments(base)
            depois = impressao_data_experiments(base)
            self.assertNotEqual(antes, durante, "a guarda não viu o arquivo novo")
            self.assertEqual(antes[0], depois[0])   # e o rastro foi desfeito

    def test_a_impressao_reage_a_mudanca_SO_NA_RAIZ(self):
        """O ponto cego exato que existia até 2026-07-30.

        Uma subpasta que nasce e morre não muda NENHUM filho — muda o mtime do
        diretório-raiz. Se a impressão não estatar a raiz, essa escrita passa
        invisível, e foi assim que `test_drivers_b12` escreveu em produção a
        cada execução da suíte sem a guarda acusar.
        """
        import os
        import tempfile
        with tempfile.TemporaryDirectory(prefix="g8_raiz_") as base:
            os.makedirs(os.path.join(base, "main"))
            antes = impressao_data_experiments(base)
            alvo = os.path.join(base, "_efemera")
            os.makedirs(alvo)
            os.rmdir(alvo)
            depois = impressao_data_experiments(base)
            self.assertEqual(antes[0], depois[0], "a contagem não deveria mudar")
            self.assertNotEqual(
                antes[1], depois[1],
                "a impressão NÃO reagiu a uma subpasta que nasceu e morreu — "
                "a raiz voltou a ficar fora da fotografia e a guarda está cega")


if __name__ == "__main__":
    unittest.main()
