# -*- coding: utf-8 -*-
"""[T12/BL-08] O pin do PAR `numpy`+`scipy` — declarado, instalado e MEDIDO no lote.

Por que este arquivo existe
---------------------------
O `sobol_batch` é o piso "ao acaso" da campanha, e o lote dele é uma sequência
de Sobol com randomização de **Owen** vinda do `scipy.stats.qmc`
(`src/sobol_batch.py:72-73`). A bit-identidade desse lote está provada
cross-OS/cross-arquitetura — mas **só sob `numpy 2.4.6` + `scipy 1.17.1` nos
dois lados**; a estabilidade cross-VERSÃO nunca foi provada e segue no teto T.
Com a intenção solta (`scipy` sem `==`), o `pip` de cada máquina resolve o que
quiser, e o piso de 3 máquinas deixa de ser comparável consigo mesmo. É
literalmente a lição do `torch` (DI-34/Q4): *"a intenção solta deixou o pip da
VM resolver 2.13.0"*.

Um pin só existe se três coisas coincidirem, e é isso que se afere aqui:
**o que os artefatos declaram**, **o que está instalado** e **o que o lote
produz**. Declarar sem medir foi exatamente o modo de falha da campanha T11.
"""
import hashlib
import json
import os
import re
import sys
import unittest

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

ENVS = os.path.join(RAIZ, "claude_code_context", "artifacts", "envs.json")
LOCK = os.path.join(RAIZ, "claude_code_context", "artifacts", "repos.lock")
REQ = os.path.join(RAIZ, "requirements", "env_main.txt")

#: sha256 dos bytes `<f8` row-major do lote, medido em 2026-07-31 sob
#: scipy 1.17.1 + numpy 2.4.6 (macOS arm64). Se o scramble de Owen mudar de
#: versão, ESTES números mudam — é o gate que o pin existe para armar.
LOTES = {
    (2, 10, 12345):
        "bc1b4d5ea0d4cf11b54c895d76859b50e210cc6d08573565468a2f27487a4be1",
    (10, 10, 999):
        "a7372bd33041e344d96625e32547b31babc72c04d095e347431a785915d3ef52",
    (30, 10, 7):
        "774da0112fbc23b50ad6b9f66d8eaadb002b447160aa24202309583eb8965f83",
}


#: O PAR que a bit-identidade de Owen exige. Pinar um só protege metade.
PACOTES = ("numpy", "scipy")


def _pin_do_lock(pkg):
    with open(LOCK, encoding="utf-8") as fh:
        return json.load(fh)["repos"][pkg]["version"]


def _pin_da_envs(pkg):
    with open(ENVS, encoding="utf-8") as fh:
        envs = json.load(fh)
    pins = envs["environments"]["env_main"]["key_pins"]
    achados = [p for p in pins if p.startswith(pkg)]
    if len(achados) != 1:
        raise AssertionError("esperava 1 pin de %s em key_pins, achei %r"
                             % (pkg, achados))
    m = re.match(r"%s==([0-9][^\s⟦]*)" % pkg, achados[0])
    if not m:
        raise AssertionError(
            "o pin do %s na envs.json não é EXATO (`%s==X.Y.Z`): %r"
            % (pkg, pkg, achados[0]))
    return m.group(1)


def _pin_do_requirements(pkg):
    with open(REQ, encoding="utf-8") as fh:
        for linha in fh:
            m = re.match(r"\s*%s==([0-9][^\s#]*)" % pkg, linha)
            if m:
                return m.group(1)
    raise AssertionError(
        "requirements/env_main.txt não pina %s com `==`" % pkg)


class TestPinDoScipy(unittest.TestCase):

    def test_os_tres_artefatos_declaram_a_MESMA_versao(self):
        """Um pin em 2 dos 3 lugares é pior que nenhum: dá falsa segurança."""
        for pkg in PACOTES:
            with self.subTest(pacote=pkg):
                declarados = {_pin_da_envs(pkg), _pin_do_lock(pkg),
                              _pin_do_requirements(pkg)}
                self.assertEqual(
                    len(declarados), 1,
                    "envs.json, repos.lock e requirements/env_main.txt "
                    "discordam sobre a versão do %s: %r" % (pkg, declarados))

    def test_o_PAR_numpy_scipy_bate_com_o_INSTALADO(self):
        """O que roda tem de ser o que se declara — em CADA máquina.

        Este é o teste que muda de resposta nas VMs: se o `pip` de lá resolver
        outra versão, ele fica vermelho ANTES do disparo, não depois. E afere o
        **par**, porque a bit-identidade de Owen exige os dois lados: com o
        numpy solto, o pin do scipy protegia metade.
        """
        import numpy
        import scipy
        instalado = {"numpy": numpy.__version__, "scipy": scipy.__version__}
        for pkg in PACOTES:
            with self.subTest(pacote=pkg):
                self.assertEqual(
                    instalado[pkg], _pin_do_lock(pkg),
                    "o %s instalado (%s) não é o pinado (%s) — o lote de Owen "
                    "do sobol_batch deixa de ser comparável entre máquinas"
                    % (pkg, instalado[pkg], _pin_do_lock(pkg)))

    def test_o_lote_de_Owen_reproduz_byte_a_byte(self):
        """O que o pin PROTEGE, medido — não a existência da linha no artefato.

        `_sobol_batch01` é o caminho real do piso. Se o scramble de Owen mudar
        de versão para versão, o hash muda e o gate acusa.
        """
        from src.sobol_batch import _sobol_batch01
        for (D, q, seed), esperado in LOTES.items():
            with self.subTest(D=D, q=q, seed=seed):
                X = _sobol_batch01(D, q, seed)
                self.assertEqual(X.shape, (q, D))
                obtido = hashlib.sha256(
                    np.ascontiguousarray(X, dtype="<f8").tobytes()).hexdigest()
                self.assertEqual(
                    obtido, esperado,
                    "o lote Sobol/Owen mudou (D=%d q=%d seed=%d) — scipy %s. "
                    "O piso do batch deixou de reproduzir a rodada anterior."
                    % (D, q, seed, __import__("scipy").__version__))

    def test_o_lote_e_deterministico_na_semente(self):
        """Controle: mesma semente ⇒ mesmos bytes; semente vizinha ⇒ outros.

        Sem a segunda metade, o teste acima passaria até se `_sobol_batch01`
        ignorasse a semente e devolvesse sempre a mesma matriz.
        """
        from src.sobol_batch import _sobol_batch01
        a = _sobol_batch01(10, 10, 999)
        self.assertTrue(np.array_equal(a, _sobol_batch01(10, 10, 999)))
        self.assertFalse(np.array_equal(a, _sobol_batch01(10, 10, 1000)),
                         "a semente não muda o lote — o Sobol do piso não "
                         "estaria semeado por iteração (D62/D91)")


if __name__ == "__main__":
    unittest.main()
