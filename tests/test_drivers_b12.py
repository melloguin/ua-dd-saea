# -*- coding: utf-8 -*-
"""[B-12] Os 9 drivers de operação estão VERSIONADOS + preflight anti-forasteiro.

O disparo das 30 sementes seria feito por drivers FORA do controle de versão:
`git status --porcelain scripts/` acusava `lote42.sh`, `lote3s.sh`,
`preflight42.sh`, `censo_bucket.py`, `coletar42.sh`, `estado42.sh`, `tabela42.py`,
`tempo42.sh` e `plano3s.sh` como UNTRACKED. O `repo_hash` do manifesto (D80) não
cobre o que não está no repo: a campanha inteira seria orquestrada por código sem
proveniência, e um driver editado no meio do caminho não deixaria rastro.
"""
import os
import subprocess
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

#: Os 9 drivers que orquestram o disparo/censo por máquina.
DRIVERS = ("lote42.sh", "lote3s.sh", "plano3s.sh", "preflight42.sh",
           "coletar42.sh", "estado42.sh", "tempo42.sh",
           "censo_bucket.py", "tabela42.py")


class TestDriversVersionados(unittest.TestCase):

    def test_os_9_drivers_existem(self):
        for d in DRIVERS:
            with self.subTest(driver=d):
                self.assertTrue(os.path.exists(os.path.join(_RAIZ, "scripts", d)))

    def test_nenhum_driver_esta_untracked(self):
        r = subprocess.run(["git", "status", "--porcelain", "--", "scripts/"],
                           cwd=_RAIZ, capture_output=True, text=True)
        if r.returncode != 0:
            self.skipTest("git indisponível neste checkout")
        untracked = {ln[3:].strip() for ln in r.stdout.splitlines()
                     if ln.startswith("??")}
        fora = sorted(f"scripts/{d}" for d in DRIVERS
                      if f"scripts/{d}" in untracked)
        self.assertEqual(fora, [], f"drivers de disparo FORA do git: {fora}")


class TestPreflightAntiForasteiro(unittest.TestCase):
    """B-12(a): o preflight aborta se houver dado de OUTRA máquina em data/."""

    def _preflight(self):
        import importlib.util as u
        spec = u.spec_from_file_location(
            "preflight_mod", os.path.join(_RAIZ, "scripts", "preflight.py"))
        mod = u.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_o_discriminador_e_o_HOST_nao_o_venv(self):
        # a mesma máquina roda 4 venvs por desenho (D79/N.1.2): env_b5,
        # env_c311 e env_e81_qpots são venvs LEGÍTIMOS do Mac. O critério
        # literal do B-12 ("venv != o da máquina") daria 304 falsos-positivos
        # neste checkout; o que denuncia dado que VIAJOU é o caminho do
        # intérprete não existir aqui.
        mod = self._preflight()
        fora = mod._manifestos_forasteiros()
        for rel, venv in fora:
            with self.subTest(manifesto=rel):
                self.assertNotIn(venv, ("env_b5", "env_c311", "env_e81_qpots",
                                        "mestrado_experimentos_dissertacao"))

    def test_manifesto_forasteiro_plantado_e_acusado(self):
        import json
        import tempfile
        mod = self._preflight()
        alvo = os.path.join(_RAIZ, "data", "experiments", "_teste_b12")
        os.makedirs(alvo, exist_ok=True)
        p = os.path.join(alvo, "exp_main_zz_MMF1_0.manifest.json")
        try:
            with open(p, "w", encoding="utf-8") as fh:
                json.dump({"exp": "main", "alg": "zz", "problema": "MMF1",
                           "semente": 0, "status": "ok",
                           "env": {"executable": "/nao/existe/env_fantasma/bin/python"}},
                          fh)
            achados = dict(mod._manifestos_forasteiros())
            rel = os.path.relpath(p, _RAIZ)
            self.assertIn(rel, achados)
            self.assertEqual(achados[rel], "env_fantasma")
        finally:
            os.remove(p)
            os.rmdir(alvo)

    def test_o_baseline_pre_retrofit_nunca_e_varrido(self):
        # proibição absoluta da casa: nem para LER em varredura de escrita
        mod = self._preflight()
        for rel, _ in mod._manifestos_forasteiros():
            self.assertNotIn("_baseline_pre_retrofit", rel)


if __name__ == "__main__":
    unittest.main()
