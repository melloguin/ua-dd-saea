"""Testes do LACRE das árvores vendorizadas (repos.lock / D80).

Por que este arquivo existe
---------------------------
Em 2026-07-30 o patch vendorizado `b5-pwrong-stats` foi reescrito e commitado
SEM re-lacrar o `repos.lock`. O `preflight.py` não acusou nada: no modo leitura
ele RECALCULAVA o content-hash da árvore e imprimia o valor recalculado — que,
por construção, sempre bate com o disco. O "lacre" não lacrava nada.

Um lacre serve para uma coisa só: detectar que a árvore vendorizada mudou sem
autorização. Se o gate não COMPARA disco × lacrado, ele é decorativo — e uma
cirurgia vendorizada não-registrada entra na campanha em silêncio, que é
exatamente o cenário que o D80 existe para impedir.

Os dois testes abaixo cobrem as duas metades da propriedade:
  1. `tree_sha256` é SENSÍVEL — um único byte em qualquer arquivo da árvore
     muda o hash (senão o lacre não detecta nada mesmo comparando);
  2. o `preflight.py` COMPARA e reporta pendência — com CONTROLE MEDIDO: a
     mesma checagem rodada contra a versão ANTIGA do preflight (tirada do git)
     tem de REPROVAR. Sem o controle, o teste poderia estar passando por
     acidente.
"""
import ast
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFLIGHT = os.path.join(RAIZ, "scripts", "preflight.py")


def _carrega_preflight():
    import importlib.util as iu
    spec = iu.spec_from_file_location("_pf_lacre", PREFLIGHT)
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _compara_e_reporta(fonte):
    """O bloco do content-hash compara o hash guardado e vira PENDÊNCIA?

    Checagem por AST, não por grep: procura, DENTRO da função que monta a
    seção 1, uma comparação que envolva `sha256_tree` e um `problems.append`
    no mesmo `if/else` — é isso que transforma "imprimi o hash" em "acusei a
    divergência".
    """
    arvore = ast.parse(fonte)
    for no in ast.walk(arvore):
        if not isinstance(no, ast.If):
            continue
        trecho = ast.dump(no)
        if "sha256_tree" not in trecho:
            continue
        # tem de existir uma comparação (== ou !=) e um problems.append no ramo
        tem_comparacao = any(isinstance(c, ast.Compare) for c in ast.walk(no))
        tem_pendencia = any(
            isinstance(c, ast.Call)
            and isinstance(c.func, ast.Attribute)
            and c.func.attr == "append"
            and isinstance(c.func.value, ast.Name)
            and c.func.value.id == "problems"
            for c in ast.walk(no)
        )
        if tem_comparacao and tem_pendencia:
            return True
    return False


class TestLacreSensivel(unittest.TestCase):
    def test_um_byte_muda_o_hash_da_arvore(self):
        pf = _carrega_preflight()
        with tempfile.TemporaryDirectory() as d:
            sub = os.path.join(d, "pacote")
            os.makedirs(sub)
            alvo = os.path.join(sub, "modulo.py")
            with open(alvo, "w", encoding="utf-8") as fh:
                fh.write("x = 1\n")
            with open(os.path.join(sub, "outro.m"), "w", encoding="utf-8") as fh:
                fh.write("y = 2;\n")
            antes = pf.tree_sha256(d)
            # um byte, no meio de uma árvore com 2 arquivos
            with open(alvo, "w", encoding="utf-8") as fh:
                fh.write("x = 2\n")
            depois = pf.tree_sha256(d)
        self.assertNotEqual(
            antes, depois,
            "tree_sha256 não reagiu a uma mudança de 1 byte — o lacre seria cego",
        )

    def test_hash_estavel_entre_chamadas(self):
        """Sem estabilidade o gate viraria falso-positivo crônico e seria desligado."""
        pf = _carrega_preflight()
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.py"), "w", encoding="utf-8") as fh:
                fh.write("a = 1\n")
            self.assertEqual(pf.tree_sha256(d), pf.tree_sha256(d))


class TestPreflightComparaOLacre(unittest.TestCase):
    def test_preflight_atual_compara_e_acusa(self):
        with open(PREFLIGHT, encoding="utf-8") as fh:
            fonte = fh.read()
        self.assertTrue(
            _compara_e_reporta(fonte),
            "preflight.py voltou a apenas RECALCULAR o content-hash sem comparar "
            "com o valor lacrado no repos.lock — o lacre voltou a ser decorativo",
        )

    def test_controle_a_versao_antiga_REPROVA(self):
        """CONTROLE MEDIDO: sem ele, o teste acima poderia passar por acidente.

        A versão do preflight anterior a este conserto (o commit que introduziu
        a comparação) tem de ser REPROVADA pela mesma checagem. Se ela passar,
        a checagem não discrimina nada e o teste de cima não vale.
        """
        antiga = subprocess.run(
            ["git", "-C", RAIZ, "show", "819cf45:scripts/preflight.py"],
            capture_output=True, text=True,
        )
        if antiga.returncode != 0:
            self.skipTest("commit de referência 819cf45 indisponível neste clone")
        self.assertFalse(
            _compara_e_reporta(antiga.stdout),
            "o CONTROLE passou: a checagem não discrimina a versão sem comparação, "
            "logo o teste positivo não prova nada",
        )


if __name__ == "__main__":
    unittest.main()
