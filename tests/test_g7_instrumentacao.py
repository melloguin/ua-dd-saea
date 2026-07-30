# -*- coding: utf-8 -*-
"""[G7] Cronômetro no portão de avaliação (I-02) + `repo_hash` no ⑤ (I-09).

* **I-02** — `tempo_aval_real_s = 0.0` era lido como "avaliar foi instantâneo"
  quando o significado real era "não medi". Causa em 3 camadas, nesta ordem:
  `src/budget.py` — o portão ÚNICO de avaliação do Python — **sem cronômetro** (a
  DI-12.4 instrumentou só o `src/FEBudget.m` do MATLAB) → `src/export.py`
  (`round(float(...))` tornava o NULL INEXPRIMÍVEL) → `src/sobol_batch.py`
  (passava `0.0` literal). Medido: **5/5** células do sobol_batch com zero EXATO
  contra **0 zeros em 416** células online alheias; o valor verdadeiro é
  **4,110 s-VM nas 5 = 20,6% do wall** (57,15% no WFG9). E o buraco reaparecia em
  qualquer runner Python novo, porque o helper não PERMITIA dizer "não medi".
* **I-09** — `repo_hash` vazio em **666/666** células: quebra o elo D80
  run↔código em ~10.350 células/campanha e rebaixa todo o aspecto declarativo
  (pins, patches, âncoras), que é o que sustenta os itens do teto T.
"""
import json
import os
import sys
import tempfile
import time
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

from src import export, manifest, naming            # noqa: E402
from src.budget import FEBudget                     # noqa: E402

try:
    import numpy as np
    _TEM_NUMPY = True
except ImportError:                                 # pragma: no cover
    _TEM_NUMPY = False


@unittest.skipUnless(_TEM_NUMPY, "numpy ausente")
class TestCronometroDoPortao(unittest.TestCase):
    """I-02: a medida nasce no ponto por onde TODA avaliação real passa."""

    def test_sem_avaliacao_o_tempo_e_NULL_nao_zero(self):
        # é a distinção que o item existe para criar: "não medi" ≠ "custou zero"
        self.assertIsNone(FEBudget(D=2, maxfe=5).tempo_aval_real_s)

    def test_mede_o_tempo_dentro_de_true_f(self):
        bud = FEBudget(D=2, maxfe=5)

        def lenta(x):
            time.sleep(0.02)
            return np.array([1.0, 2.0])

        bud.evaluate(np.array([0.1, 0.2]), lenta)
        self.assertGreaterEqual(bud.tempo_aval_real_s, 0.02)
        self.assertLess(bud.tempo_aval_real_s, 2.0)

    def test_acumula_por_avaliacao(self):
        bud = FEBudget(D=2, maxfe=5)
        for i in range(3):
            bud.evaluate(np.array([0.1 * (i + 1), 0.2]),
                         lambda x: (time.sleep(0.01), np.array([1.0, 2.0]))[1])
        self.assertGreaterEqual(bud.tempo_aval_real_s, 0.03)

    def test_cache_hit_nao_entra_na_conta(self):
        # cache-hit = 0 FE (D89) e nenhuma chamada a `true_f`: contar tempo ali
        # inflaria o custo de avaliação com trabalho que não aconteceu.
        bud = FEBudget(D=2, maxfe=5)
        x = np.array([0.3, 0.4])
        bud.evaluate(x, lambda v: np.array([1.0, 2.0]))
        t1 = bud.tempo_aval_real_s
        for _ in range(5):
            bud.evaluate(x, lambda v: (time.sleep(0.05), np.array([1.0, 2.0]))[1])
        self.assertEqual(bud.cache_hits, 5)
        self.assertEqual(bud.tempo_aval_real_s, t1)

    def test_hard_stop_nao_cronometra(self):
        bud = FEBudget(D=2, maxfe=1)
        bud.evaluate(np.array([0.1, 0.2]), lambda v: np.array([1.0, 2.0]))
        t1 = bud.tempo_aval_real_s
        from src.budget import BudgetExhausted
        with self.assertRaises(BudgetExhausted):
            bud.evaluate(np.array([0.9, 0.9]), lambda v: np.array([1.0, 2.0]))
        self.assertEqual(bud.tempo_aval_real_s, t1)


class TestExportAceitaNull(unittest.TestCase):
    """I-02: `round(float(...))` tornava o NULL inexprimível."""

    def _blk(self, aval):
        return export.manifest_timing_block(
            tempo_total_s=10.0, tempo_fit_surrogate_s=1.0,
            tempo_busca_s=2.0, tempo_aval_real_s=aval)

    def test_none_atravessa_como_none(self):
        self.assertIsNone(self._blk(None)["tempo_aval_real_s"])

    def test_zero_continua_expressavel(self):
        # 0.0 tem de continuar POSSÍVEL — só deixa de ser o único jeito de dizer
        # "não sei"
        self.assertEqual(self._blk(0.0)["tempo_aval_real_s"], 0.0)

    def test_valor_medido_e_arredondado_como_os_outros(self):
        self.assertEqual(self._blk(4.1101234)["tempo_aval_real_s"], 4.1101)

    def test_os_outros_3_seguem_obrigatorios(self):
        # o bloco `timing` nasceu ZERADO em 10/12 configs (auditoria da torre):
        # só o `tempo_aval_real_s` ganhou o direito ao NULL.
        blk = self._blk(None)
        for k in ("tempo_total_s", "tempo_fit_surrogate_s", "tempo_busca_s"):
            self.assertIsInstance(blk[k], float)

    def test_o_sobol_batch_nao_passa_mais_zero_literal(self):
        with open(os.path.join(_RAIZ, "src", "sobol_batch.py"),
                  encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("tempo_aval_real_s=bud.tempo_aval_real_s", src)
        self.assertNotIn("tempo_aval_real_s=0.0", src)

    def test_os_offline_declaram_NULL_em_vez_de_zero(self):
        # no offline o orçamento nasce esgotado (a ① é o dataset, D90): nenhuma
        # avaliação real acontece DENTRO do run.
        for nome in ("c311_tgprmo", "b5_prob", "piso_offline", "treed_media",
                     "standalone_harness"):
            with self.subTest(runner=nome):
                with open(os.path.join(_RAIZ, "src", f"{nome}.py"),
                          encoding="utf-8") as fh:
                    src = fh.read()
                self.assertNotIn("tempo_aval_real_s=0.0", src)


class TestRepoHashNoManifesto(unittest.TestCase):
    """I-09: o elo D80 run↔código nos DOIS stacks."""

    def test_manifesto_novo_carrega_o_commit(self):
        man = manifest.new_manifest("main", "c149", "ZDT4", 42)
        self.assertTrue(man["repo_hash"])
        self.assertEqual(man["repo_hash"], manifest.repo_hash_corrente())

    def test_o_commit_e_o_HEAD_do_repo(self):
        import subprocess
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_RAIZ,
                           capture_output=True, text=True)
        if r.returncode != 0:
            self.skipTest("git indisponível")
        self.assertEqual(manifest.repo_hash_corrente(), r.stdout.strip())

    def test_quem_passa_explicito_manda(self):
        man = manifest.new_manifest("main", "c149", "ZDT4", 42,
                                    repo_hash="cafebabe")
        self.assertEqual(man["repo_hash"], "cafebabe")

    def test_writer_matlab_tambem_preenche(self):
        with open(os.path.join(_RAIZ, "src", "experiment.m"),
                  encoding="utf-8", errors="replace") as fh:
            m = fh.read()
        self.assertIn("man.repo_hash = string(repo_hash_corrente());", m)
        self.assertNotIn('man.repo_hash = "";', m)
        self.assertIn("rev-parse HEAD", m)

    def test_o_gate_G3_passa_com_o_manifesto_novo(self):
        # o fechamento do fio: G-3 (modo campanha) exigia campanha_id E
        # repo_hash, e o ⑤ novo nasce com os dois.
        sys.path.insert(0, os.path.join(_RAIZ, "scripts"))
        import gates_proveniencia as G
        with tempfile.TemporaryDirectory() as dr:
            man = manifest.new_manifest(
                "main", "c149", "ZDT4", 42, data_root=dr,
                env={"executable": "/home/jupyter/python_venvs/env_main/bin/python"})
            manifest.write_manifest(man, dr)
            with open(naming.manifest_path("main", "c149", "ZDT4", 42,
                                          data_root=dr), encoding="utf-8") as fh:
                lido = json.load(fh)
            ok, det = G.gate_proveniencia(lido, "c149",
                                          campanha_id=manifest.campanha_id_corrente())
            self.assertTrue(ok, det)


if __name__ == "__main__":
    unittest.main()
