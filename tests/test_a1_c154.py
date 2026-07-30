# -*- coding: utf-8 -*-
"""[T11-A1] c154 — `params` no ⑤ (I-07) · ordem da ③ dos BoTorch (I-12) · `executable`.

* **I-07** — o CONTRATO §5 lista `params` (a config EFETIVA) como obrigatória, e o
  stack BoTorch a gravava SÓ no header do ⑥: medido na s42, **13 células de c154 +
  24 de c262 sem a chave no ⑤** (com o roster completo, 750+750 = 1.500 violando o
  §5). Quem lê a tabela de execuções não tem por que abrir um ⑥ de 40 MB para
  saber com que `num_restarts` o run correu.
* **I-12** — a ③-online dos BoTorch vem na ordem dos restarts **com o vencedor
  removido e re-anexado no fim**. Casar por índice ingênuo conclui *"mismatch em
  89% das iterações"* — e a conclusão é do LEITOR, não do dado (J27 REFUTADO).
  MEDIDO nos parquets da s42: **1.200 blocos de c154+c262, vencedor na ÚLTIMA
  linha em 1.200 (100%)**.
* **`env.executable`** — achado do gate G-3 na célula nova: o
  `standalone_harness.env_info` gravava o intérprete e o do BoTorch não, então o
  gate de proveniência não tinha como afirmar que a célula correu no venv do
  roster (`envs.json:venvs_aceitos`).
"""
import os
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)
sys.path.insert(0, os.path.join(_RAIZ, "scripts"))

try:
    from src.botorch_harness import env_info, restart_de_linha
    _TEM_TORCH = True
except Exception:                                   # noqa: BLE001 — venv sem torch
    _TEM_TORCH = False


@unittest.skipUnless(_TEM_TORCH, "stack BoTorch ausente")
class TestOrdemDaTerceiraI12(unittest.TestCase):
    """I-12: `restart_de_linha` é a forma EXECUTÁVEL da regra de leitura."""

    def test_vencedor_e_sempre_a_ultima_linha(self):
        for R in (2, 5, 10, 40):
            for best in range(R):
                with self.subTest(R=R, best=best):
                    self.assertEqual(restart_de_linha(R, best)[-1], best)

    def test_e_uma_permutacao_dos_restarts(self):
        # nenhuma linha inventa nem perde restart
        for R in (2, 5, 10):
            for best in range(R):
                self.assertEqual(sorted(restart_de_linha(R, best)), list(range(R)))

    def test_a_regra_literal_do_plano(self):
        # linha j → restart j (j<best) | j+1 (j≥best); linha R−1 → best
        R, best = 10, 3
        m = restart_de_linha(R, best)
        for j in range(R - 1):
            self.assertEqual(m[j], j if j < best else j + 1)
        self.assertEqual(m[R - 1], best)

    def test_best_igual_ao_ultimo_e_identidade(self):
        self.assertEqual(restart_de_linha(5, 4), [0, 1, 2, 3, 4])

    def test_best_fora_do_intervalo_estoura(self):
        with self.assertRaises(ValueError):
            restart_de_linha(5, 5)
        with self.assertRaises(ValueError):
            restart_de_linha(5, -1)

    def test_vazio_e_vazio(self):
        self.assertEqual(restart_de_linha(0, 0), [])

    def test_a_regra_esta_no_sigma_dict_dos_DOIS_gemeos(self):
        # DEF-C4: o `sigma_dict` é "LEITURA OBRIGATÓRIA antes de usar a ③" — a
        # regra tem de viajar COM o dado, não só no CONTRATO.
        from src.c154_jes import _sigma_dict as sd154
        from src.c262_qnehvi import _sigma_dict as sd262
        for nome, sd in (("c154", sd154()), ("c262", sd262())):
            with self.subTest(config=nome):
                self.assertIn("ordem_terceira_online", sd)
                txt = sd["ordem_terceira_online"]
                self.assertIn("restart_de_linha", txt)
                self.assertIn("NAO vale para q>1", txt)

    def test_a_regra_esta_no_CONTRATO(self):
        with open(os.path.join(_RAIZ, "CONTRATO_DE_DADOS.md"),
                  encoding="utf-8") as fh:
            doc = fh.read()
        self.assertIn("ORDEM DAS LINHAS da ③-online dos BoTorch", doc)
        self.assertIn("restart_de_linha", doc)


@unittest.skipUnless(_TEM_TORCH, "stack BoTorch ausente")
class TestParamsNoQuintoI07(unittest.TestCase):

    def test_o_harness_grava_params_quando_recebe(self):
        import inspect

        from src.botorch_harness import write_run_outputs
        self.assertIn("params", inspect.signature(write_run_outputs).parameters)

    def test_c154_passa_a_config_efetiva(self):
        from src import c154_jes
        with open(c154_jes.__file__, encoding="utf-8") as fh:
            src = fh.read()
        # a MESMA fonte no header do ⑥ e no ⑤ (duplicar literal é como o `q` do
        # batch divergiu: ⑤ dizia 1, header dizia 10 — I-10)
        self.assertEqual(src.count("params=_params_efetivos("), 2)

    def test_os_params_do_c154_tem_o_que_o_relatorio_pede(self):
        from src.c154_jes import _params_efetivos
        p = _params_efetivos(q=1, num_restarts=10, raw_samples=2000)
        for k in ("S", "P", "estimation_type", "rs_ladder", "num_restarts",
                  "raw_samples", "q", "refit", "kernel", "acqf"):
            self.assertIn(k, p)
        self.assertEqual(p["q"], 1)
        self.assertEqual(p["num_restarts"], 10)


@unittest.skipUnless(_TEM_TORCH, "stack BoTorch ausente")
class TestExecutableNoQuinto(unittest.TestCase):

    def test_env_info_declara_o_interprete(self):
        e = env_info()
        self.assertEqual(e["executable"], sys.executable)

    def test_o_venv_declarado_esta_no_roster_do_c154(self):
        # é o que o gate G-3 afere: célula no venv ERRADO é o desastre silencioso
        # do N.1.2 (o `sys.modules` entrega o `desdeo_*` do outro config)
        import gates_proveniencia as G
        venv = G.venv_de(env_info()["executable"])
        self.assertIn(venv, G._venvs_por_alg()["c154"])

    def test_os_dois_harnesses_declaram_o_mesmo_campo(self):
        from src.standalone_harness import env_info as env_standalone
        self.assertIn("executable", env_standalone())
        self.assertIn("executable", env_info())


if __name__ == "__main__":
    unittest.main()
