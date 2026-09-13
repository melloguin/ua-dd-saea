# -*- coding: utf-8 -*-
"""[A9] A REGRA DO RÓTULO do c217 — a fórmula do emparelhamento, travada.

Por que este arquivo existe
---------------------------
O commit `52befff` tem "b4 e c217 (regra do rótulo…)" no título e o
`T11_STATUS` marcava **A9 como `[x]` DEFINITIVO** — mas só o b4 recebeu a regra.
Carimbo falso: o autor dispararia o c217 achando que a ③ dele era auditável.

E a regra do c217 não é a do b4. O b4 julga contra as K referências radiais
("não é pior que TODAS"). O c217 é par-a-par POSICIONAL E CÍCLICO —
`RBFNNPC.m:61` faz `Pref(i,:) = Preference(mod(i+numberP,numberP)+1, ...)`, ou
seja **cada ponto da sonda é julgado contra UMA referência específica,
determinada pela sua posição no bloco**. Quem agregar contra o conjunto Pmid
inteiro mede outra coisa.

Há um deslocamento de UM (o próprio stock comenta *"better than a random
reference point"*), e é exatamente onde eu errei ao escrever a regra na primeira
vez. Este teste trava a fórmula nas duas convenções e prova que a versão
off-by-one **não** reproduz o laço.
"""
import os
import re
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _pareamento_matlab(n, N):
    """O laço literal de RBFNNPC.m:61, i = 1..N (1-based)."""
    return [(i % n) + 1 for i in range(1, N + 1)]


def _pareamento_da_regra(n, N):
    """A regra como está escrita no sigma_dict: j 0-based → (j+1) mod n."""
    return [((j + 1) % n) + 1 for j in range(N)]


class TestFormulaDoPareamento(unittest.TestCase):

    def test_a_regra_reproduz_o_laco_do_stock(self):
        for n in (2, 3, 5, 7, 13):
            for N in (1, n, n + 1, 3 * n + 2):
                with self.subTest(n=n, N=N):
                    self.assertEqual(_pareamento_matlab(n, N),
                                     _pareamento_da_regra(n, N))

    def test_CONTROLE_a_versao_off_by_one_NAO_reproduz(self):
        """Sem este controle o teste acima não provaria nada.

        `pmid_ids[j mod n]` é o erro natural de quem converte 1-based para
        0-based sem notar o deslocamento — foi o que escrevi na 1ª versão.
        """
        errada = [(j % 5) + 1 for j in range(12)]
        self.assertNotEqual(_pareamento_matlab(5, 12), errada,
                            "a versão off-by-one reproduziu o laço — então o "
                            "teste positivo não discrimina")

    def test_o_stock_ainda_faz_o_pareamento_ciclico(self):
        """Se o vendorizado mudar, a regra documentada vira mentira."""
        alvo = None
        for raiz, _dirs, arqs in os.walk(os.path.join(_RAIZ, "algorithms")):
            if "RBFNNPC.m" in arqs:
                alvo = os.path.join(raiz, "RBFNNPC.m")
                break
        if not alvo:
            self.skipTest("RBFNNPC.m não encontrado neste checkout")
        with open(alvo, encoding="utf-8", errors="replace") as fh:
            fonte = fh.read()
        self.assertRegex(
            fonte, r"Preference\(mod\(i\s*\+\s*numberP\s*,\s*numberP\)\s*\+\s*1",
            "o emparelhamento cíclico sumiu do RBFNNPC — a REGRA_DO_ROTULO "
            "gravada no sigma_dict do c217 deixou de descrever o código")


class TestRegraGravadaNoManifesto(unittest.TestCase):

    def _experiment_m(self):
        with open(os.path.join(_RAIZ, "src", "experiment.m"),
                  encoding="utf-8") as fh:
            return fh.read()

    def test_o_c217_tem_REGRA_DO_ROTULO(self):
        fonte = self._experiment_m()
        i = fonte.index("man.sigma_dict = struct(")
        bloco = fonte[i:i + 4000]
        self.assertIn("pred_score", bloco)     # confirma que é o do c217
        self.assertIn("REGRA_DO_ROTULO", bloco,
                      "o sigma_dict do c217 voltou a não ter a regra do rótulo — "
                      "a ③ dele é 'leitura proibida' pela regra 3 do R4")

    def test_a_regra_avisa_do_deslocamento_e_da_ordem(self):
        """As duas armadilhas que a regra existe para impedir."""
        fonte = self._experiment_m()
        i = fonte.index("REGRA_DO_ROTULO")
        bloco = fonte[i:i + 3000]
        self.assertIn("(j+1) mod n", bloco, "falta a fórmula 0-based")
        self.assertIn("NAO e pmid_ids[j mod n]", bloco,
                      "falta o aviso do off-by-one")
        self.assertIn("REORDENAR", bloco,
                      "falta o aviso de que sort/unique na ③ corrompe o rótulo")


if __name__ == "__main__":
    unittest.main()
