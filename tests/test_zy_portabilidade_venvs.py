# -*- coding: utf-8 -*-
"""A suíte IMPORTA nos venvs alternativos? (py3.7 env_b5 · py3.8 env_c311)

Por que este arquivo existe
---------------------------
13 testes usam `skipUnless` apontando para `env_b5` (py3.7) e `env_c311`
(py3.8) — os venvs de b5r/b5m/moead_media e c311/treed_media. A varredura de
2026-07-30 mediu que o pacote `tests` **não importava** em nenhum dos dois:
`tuple[int, str]` é py3.9+ e `str | None` é py3.10+. Ou seja, os 13 skips
sugeriam cobertura condicional que **nem chegaria ao import**.

Pior: o segundo defeito (`str | None`) fui EU que introduzi hoje, ao
parametrizar a impressão da guarda G-8 — e a suíte no venv principal continuava
verde, porque py3.11 aceita as duas formas. Um teste que só roda no intérprete
mais novo não vê regressão de portabilidade.

Roda por ÚLTIMO (`test_zy_*`, logo antes do `test_zz` da guarda) e é SKIP quando
os venvs não existem — num checkout novo eles não estão provisionados, e isso é
ausência de ambiente, não falha.
"""
import os
import subprocess
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VENVS = {
    "env_b5": "/Users/gmello/Documents/python_venvs/env_b5/bin/python",
    "env_c311": "/Users/gmello/Documents/python_venvs/env_c311/bin/python",
}


class TestPacoteDeTestesImportaNosVenvs(unittest.TestCase):

    def _roda(self, py, codigo):
        return subprocess.run([py, "-c", codigo], cwd=_RAIZ,
                              capture_output=True, text=True, timeout=120)

    def test_o_pacote_tests_importa(self):
        for nome, py in _VENVS.items():
            with self.subTest(venv=nome):
                if not os.path.exists(py):
                    self.skipTest(f"{nome} não provisionado neste host")
                r = self._roda(py, "import sys; sys.path.insert(0,'.'); import tests")
                self.assertEqual(
                    r.returncode, 0,
                    f"o pacote `tests` NÃO importa em {nome} — os skipUnless que "
                    f"apontam para este venv prometem cobertura que não existe.\n"
                    f"{r.stderr[-400:]}")

    def test_a_guarda_G8_funciona_nos_venvs(self):
        """Não basta importar: a função que a guarda usa tem de rodar."""
        for nome, py in _VENVS.items():
            with self.subTest(venv=nome):
                if not os.path.exists(py):
                    self.skipTest(f"{nome} não provisionado neste host")
                r = self._roda(py, "import sys; sys.path.insert(0,'.')\n"
                                   "import tests\n"
                                   "n,h = tests.impressao_data_experiments()\n"
                                   "assert isinstance(n,int) and isinstance(h,str)\n"
                                   "print('ok',n)")
                self.assertEqual(r.returncode, 0,
                                 f"a impressão da guarda G-8 falhou em {nome}\n"
                                 f"{r.stderr[-400:]}")

    def test_os_modulos_dos_runners_daqueles_venvs_importam(self):
        """`src.b5_prob` em py3.7 e `src.c311_tgprmo`/`treed_media` em py3.8.

        É o mesmo teste que já existia em outro arquivo para os 8 módulos do
        G-6, mas ancorado aqui no que o venv DAQUELE config precisa: se estes
        quebrarem, o disparo quebra, não a suíte.
        """
        alvos = {"env_b5": "src.b5_prob", "env_c311": "src.treed_media"}
        for nome, mod in alvos.items():
            with self.subTest(venv=nome, modulo=mod):
                py = _VENVS[nome]
                if not os.path.exists(py):
                    self.skipTest(f"{nome} não provisionado neste host")
                r = self._roda(py, f"import sys; sys.path.insert(0,'.')\n"
                                   f"import importlib; importlib.import_module('{mod}')")
                self.assertEqual(r.returncode, 0,
                                 f"{mod} não importa em {nome}\n{r.stderr[-400:]}")


if __name__ == "__main__":
    unittest.main()
