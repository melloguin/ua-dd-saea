# -*- coding: utf-8 -*-
"""[SUB-varN/D65] O `N` dos pisos online passa a ser INJETÁVEL — sem mover o default.

**Por que existe.** O `N=20` dos 4 pisos online está CRAVADO (autor, 2026-07-18)
mas a própria SPEC o declara **provisório**: a D65 pré-registrou uma varredura
`N ∈ {10,20,30,50}` que elege 1 `N` por faixa de `D`, e a DI-39 a promoveu de
sub-estudo opcional do M11 a **pré-requisito do M8**. Para varrer é preciso
poder injetar o valor — e o valor vivia como literal em `src/experiment.m`.

**As duas coisas que estes testes travam**, e o porquê de cada uma:

1. **O default não se move.** A campanha M8 roda com `UA_DD_SAEA_PISO_N`
   ausente e tem de ver exatamente `20`. Se a injeção deslocasse o default,
   as 3.000 células de piso da campanha (4 pisos × 25 problemas × 30 sementes)
   rodariam com um `N` que ninguém decidiu.

2. **Valor inválido PÁRA, não cai no default.** É o modo de falha mais caro que
   uma varredura pode ter: um typo (`3O` com letra O) viraria `20` em silêncio e
   produziria uma célula **rotulada N=30 que rodou em N=20** — contaminando
   exatamente a comparação que a varredura existe para fazer. É a mesma classe
   do `LOTE_ORDEM` fora do vocabulário que virava `hibrida` sem avisar, fechada
   no mesmo dia.

**Como testam.** Extraem a `function` do fonte de PRODUÇÃO (`src/experiment.m`)
e a executam isolada no MATLAB — o mesmo padrão de `test_t12_jsonl_matlab.py`.
Não é cópia da lógica: é a função real, e se ela mudar de forma o `_extrai`
falha alto em vez de testar um fantasma.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERIMENT_M = os.path.join(RAIZ, "src", "experiment.m")

#: O conjunto pré-registrado da D65.
D65_N = (10, 20, 30, 50)


def _matlab_bin():
    cand = os.environ.get("UA_DD_SAEA_MATLAB")
    if cand and os.path.exists(cand):
        return cand
    cand = "/Applications/MATLAB_R2025a.app/bin/matlab"
    if os.path.exists(cand):
        return cand
    return shutil.which("matlab")


MATLAB = _matlab_bin()


def _fonte():
    with open(EXPERIMENT_M, encoding="utf-8") as fh:
        return fh.read()


def _extrai(fonte, nome):
    """O bloco `function ... <nome>(...) ... end` do fonte de produção."""
    m = re.search(r"^function\s+[^\n]*\b%s\b\s*\(.*?^end\s*$" % re.escape(nome),
                  fonte, re.MULTILINE | re.DOTALL)
    if not m:
        raise AssertionError(
            "não achei `function %s` em src/experiment.m — a função mudou de "
            "forma e este teste perdeu o alvo" % nome)
    return m.group(0)


class TestOSitioDeChamada(unittest.TestCase):
    """Sem MATLAB: o ponto único de definição do `N` chama a função."""

    @classmethod
    def setUpClass(cls):
        cls.src = _fonte()

    def test_o_literal_20_saiu_do_sitio_de_chamada(self):
        # o `N_nominal = 20;` literal não pode voltar: seria um segundo lugar
        # onde o N se decide, e a varredura passaria a mentir.
        self.assertNotIn("N_nominal = 20;", self.src)
        self.assertIn("N_nominal = piso_n_nominal();", self.src)

    def test_a_procedencia_vai_ao_jsonl_E_ao_manifesto(self):
        # os DOIS sítios (header ⑥ e params ⑤) têm de derivar da mesma função,
        # senão um deles continua afirmando "CRAVADO" numa célula injetada.
        self.assertIn("'N_origem', piso_n_origem(N_nominal)", self.src)
        self.assertIn("'N_decisao', piso_n_origem(N_nominal)", self.src)

    def test_o_N_lattice_continua_derivando_do_nominal(self):
        # invariante do T14.3 (BL-14): a flag `frente1_excede_pop` compara com o
        # N EFETIVO, e o efetivo nasce do nominal. Não pode ter se soltado.
        self.assertIn("N_lattice = N_nominal;", self.src)


@unittest.skipUnless(MATLAB, "MATLAB ausente nesta máquina")
class TestPisoNNominal(unittest.TestCase):
    """Comportamento REAL da função de produção, sob MATLAB."""

    @classmethod
    def setUpClass(cls):
        src = _fonte()
        cls.tmp = tempfile.mkdtemp(prefix="subvarn_")
        for nome in ("piso_n_nominal", "piso_n_origem"):
            with open(os.path.join(cls.tmp, nome + ".m"), "w",
                      encoding="utf-8") as fh:
                fh.write(_extrai(src, nome) + "\n")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _roda(self, valor=None):
        """Devolve `{'n': int|None, 'erro': str, 'origem': str}`."""
        script = (
            "try, n = piso_n_nominal(); "
            "o = piso_n_origem(n); "
            "r = struct('n', n, 'erro', \"\", 'origem', o); "
            "catch ME, "
            "r = struct('n', -1, 'erro', string(ME.identifier), 'origem', \"\"); "
            "end, "
            # ⚠ aspas DUPLAS: em MATLAB '<<<' é char array e `+` sobre char
            # array é SOMA NUMÉRICA (erro de tamanhos incompatíveis). Só o
            # tipo `string` concatena com `+`.
            "disp(\"<<<\" + string(jsonencode(r)) + \">>>\");")
        env = dict(os.environ)
        env.pop("UA_DD_SAEA_PISO_N", None)
        if valor is not None:
            env["UA_DD_SAEA_PISO_N"] = valor
        p = subprocess.run(
            [MATLAB, "-batch", "cd('%s'); %s" % (self.tmp, script)],
            capture_output=True, text=True, timeout=600, env=env)
        m = re.search(r"<<<(.*?)>>>", p.stdout, re.DOTALL)
        self.assertTrue(m, "MATLAB não devolveu o JSON:\n%s\n%s"
                            % (p.stdout[-1500:], p.stderr[-800:]))
        return json.loads(m.group(1))

    def test_SEM_a_env_o_default_e_exatamente_20(self):
        """A campanha M8 roda assim. Se este número mudar, 3.000 células mudam."""
        r = self._roda(None)
        self.assertEqual(r["erro"], "")
        self.assertEqual(r["n"], 20)

    def test_SEM_a_env_a_procedencia_diz_CRAVADO(self):
        r = self._roda(None)
        self.assertIn("CRAVADO", r["origem"])
        self.assertNotIn("INJETADO", r["origem"])

    def test_a_env_injeta_os_4_valores_da_D65(self):
        for n in D65_N:
            with self.subTest(N=n):
                r = self._roda(str(n))
                self.assertEqual(r["erro"], "")
                self.assertEqual(r["n"], n)

    def test_a_celula_injetada_e_DISTINGUIVEL_no_corpus(self):
        """Sem isto, uma célula da varredura some dentro do corpus da campanha."""
        r = self._roda("30")
        self.assertIn("INJETADO", r["origem"])
        self.assertIn("SUB-varN", r["origem"])
        self.assertIn("NAO e celula da campanha", r["origem"])

    def test_valor_INVALIDO_para_em_vez_de_cair_no_default(self):
        """O controle negativo do cartão: o typo não pode virar 20 em silêncio.

        `3O` (letra O) é o typo realista — e é exatamente o que produziria uma
        célula rotulada N=30 que rodou em N=20.
        """
        for ruim in ("3O", "abc", " ", "0", "1", "-5", "20.5"):
            with self.subTest(valor=repr(ruim)):
                r = self._roda(ruim)
                self.assertEqual(r["erro"], "ua_dd_saea:pisoNInvalido",
                                 "aceitou %r em vez de parar" % ruim)

    def test_env_VAZIA_e_o_mesmo_que_env_ausente(self):
        """`""` cai no default; `" "` (espaço) NÃO — e a distinção é deliberada.

        O `getenv` do MATLAB devolve `''` tanto para variável ausente quanto
        para variável definida como vazia, e o `isempty` não distingue as duas.
        Já um espaço é conteúdo: a variável FOI setada, com lixo — e aí parar é
        a resposta certa, senão um `UA_DD_SAEA_PISO_N=" 30"` mal colado rodaria
        em 20 achando que rodou em 30.
        """
        r = self._roda("")
        self.assertEqual(r["n"], 20)
        self.assertIn("CRAVADO", r["origem"])


if __name__ == "__main__":
    unittest.main()
