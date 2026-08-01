# -*- coding: utf-8 -*-
"""T14.7 / BL-18 e T14.8 / BL-20 — os dois literais que descreviam outro run.

**T14.7 · `espaco_modelo` NULL nas linhas de BUSCA da ③.** A DEF-C3 (CONTRATO §3)
manda declarar o espaço em que o modelo opera. O critério que transforma isso em
DEFEITO — e não em escolha — é a **assimetria INTRA-run**: o mesmo ⑤, com o
MESMO modelo sobre o MESMO X nativo, declarando `"cru"` nas linhas de sonda e
NULL nas de busca.

Medido no corpus da s42 (o bloqueador nomeia 3 configs; só **2** têm a
assimetria):

| config | sonda | busca | veredito |
|---|---|---|---|
| **e103** | `"cru"` 40.000 | **NULL** 19.800 | assimétrico ⇒ defeito |
| **c217** | `"cru"` 198.000 | **NULL** 201 | assimétrico ⇒ defeito |
| c262 | NULL 204.000 | NULL 2.010 | uniforme ⇒ **escolha, não defeito** |
| b4 (controle) | `"cru"` 202.000 | `"cru"` 200 | já correto |

O c262 fica FORA de propósito: pelo próprio critério do BL-18 ("é a assimetria
INTRA-run que faz disto defeito") ele não tem o defeito, e preencher o campo
lá seria decidir semântica de config — item novo, do autor (D81).

**T14.8 · `nota_potencia_de_2` do sobol_batch.** Era literal fixa afirmando
`q=10` enquanto o `params.q` do MESMO manifesto dizia 1 (o smoke da campanha).
Virou f-string do `q` real — e a nota agora acompanha o comportamento do scipy,
que só avisa quando `q` NÃO é potência de 2 (verificado empiricamente aqui).
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

try:
    import pyarrow.parquet as pq
    _TEM_ARROW = True
except ImportError:                                  # pragma: no cover
    _TEM_ARROW = False


def _matlab_bin():
    cand = os.environ.get("UA_DD_SAEA_MATLAB")
    if cand and os.path.exists(cand):
        return cand
    cand = "/Applications/MATLAB_R2025a.app/bin/matlab"
    if os.path.exists(cand):
        return cand
    return shutil.which("matlab")


MATLAB = _matlab_bin()


# ═══════════════════════════════════════════════════════════════════════════
#  T14.7 — a fiação nos dois instrumentadores
# ═══════════════════════════════════════════════════════════════════════════

class TestFiacaoEspacoModelo(unittest.TestCase):

    ALVOS = {"e103_instrument.m": 2, "c217_instrument.m": 1}

    def _src(self, nome):
        with open(os.path.join(_RAIZ, "src", nome), encoding="utf-8") as fh:
            return fh.read()

    def test_as_linhas_de_busca_declaram_o_espaco(self):
        for nome, n in self.ALVOS.items():
            with self.subTest(arquivo=nome):
                self.assertEqual(self._src(nome).count("'espaco_modelo', \"cru\""),
                                 n, "número de sítios de busca não bate")

    def test_a_sonda_do_MESMO_config_ja_dizia_cru(self):
        # a simetria é o argumento inteiro do item: se a sonda não dissesse
        # "cru", preencher a busca seria escolher semântica (D81), não corrigir.
        for nome in ("e103_sonda.m", "c217_sonda.m"):
            with self.subTest(arquivo=nome):
                self.assertIn("'espaco_modelo', \"cru\"", self._src(nome))

    def test_o_c262_NAO_foi_tocado_e_por_um_motivo(self):
        # Uniforme-NULL não é assimetria: pelo critério do próprio BL-18 não é
        # defeito. E o c262 declara a semântica onde o leitor a procura — no
        # `sigma_dict` do ⑤ (DEF-C4) —, então a coluna vazia não esconde nada.
        # Preencher a COLUNA lá seria decidir semântica de config (D81).
        with open(os.path.join(_RAIZ, "src", "c262_qnehvi.py"),
                  encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("espaco_modelo=", src, "a coluna passou a ser gravada")
        self.assertIn('"espaco_modelo": "cru', src,
                      "o sigma_dict deixou de declarar o espaço")


@unittest.skipUnless(_TEM_ARROW, "pyarrow ausente")
class TestAssimetriaNoCorpusS42(unittest.TestCase):
    """O corpus é o registro do defeito — gravado pelo código ANTIGO."""

    def _por_regime(self, alg):
        ps = sorted(glob.glob(os.path.join(
            _RAIZ, "data", "experiments", "main", alg, "*__surrogate.parquet")))
        if not ps:
            self.skipTest("célula local de %s ausente" % alg)
        t = pq.read_table(ps[0])
        if "espaco_modelo" not in t.column_names:
            self.skipTest("③ sem a coluna espaco_modelo")
        out = {}
        reg = t.column("regime").to_pylist()
        esp = t.column("espaco_modelo").to_pylist()
        for r, e in zip(reg, esp):
            out.setdefault(r, set()).add(e)
        return out

    def test_e103_e_c217_eram_assimetricos(self):
        for alg in ("e103", "c217"):
            with self.subTest(alg=alg):
                por = self._por_regime(alg)
                sonda = [v for k, v in por.items() if str(k).startswith("sonda")]
                busca = [v for k, v in por.items()
                         if not str(k).startswith("sonda")]
                self.assertTrue(sonda and busca, "célula sem os dois regimes")
                self.assertEqual(set().union(*sonda), {"cru"})
                self.assertEqual(set().union(*busca), {None},
                                 "o corpus já não registra o defeito — re-meça")

    def test_c262_era_UNIFORME_e_por_isso_ficou_de_fora(self):
        por = self._por_regime("c262")
        self.assertEqual(set().union(*por.values()), {None},
                         "o c262 tem assimetria: reabra o item com o autor")


@unittest.skipUnless(MATLAB and _TEM_ARROW, "MATLAB/pyarrow ausentes")
class TestCelulasReaisEspacoModelo(unittest.TestCase):
    """Células REAIS: a ③ inteira passa a declarar o espaço.

    `main/c217/MMF1/42` (13,3 s na F5.2d) e `main/e103/ZDT4/42` (23,8 s) — as
    mais baratas de cada config. O e103 é OFFLINE: precisa de `datasets` no
    dataRoot (armadilha O-01), além de `doe`/`sonda`.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="t14_espaco_")
        dr = os.path.join(cls.tmp, "data")
        os.makedirs(dr)
        for sub in ("doe", "sonda", "datasets"):     # entrada (D63) — por link
            os.symlink(os.path.join(_RAIZ, "data", sub), os.path.join(dr, sub))
        with open(os.path.join(cls.tmp, "drv_t14_espaco.m"), "w",
                  encoding="utf-8") as fh:
            fh.write("function drv_t14_espaco(raiz, dr)\n"
                     "  addpath(genpath(fullfile(raiz,'src')));\n"
                     "  cd(raiz);\n"
                     "  experiment('c217', 'MMF1', 42, 'main', dr);\n"
                     "  experiment('e103', 'ZDT4', 42, 'main', dr);\n"
                     "end\n")
        cls.proc = subprocess.run(
            [MATLAB, "-sd", cls.tmp, "-batch",
             "drv_t14_espaco('%s','%s')" % (_RAIZ, dr)],
            capture_output=True, text=True, timeout=1800)
        cls.dr = dr

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _tabela(self, alg):
        ps = glob.glob(os.path.join(self.dr, "experiments", "main", alg,
                                    "*__surrogate.parquet"))
        self.assertTrue(ps, "%s não produziu ③.\nSTDERR:\n%s"
                        % (alg, self.proc.stderr[-2000:]))
        return pq.read_table(ps[0])

    def test_nenhuma_linha_da_terceira_sai_com_espaco_NULL(self):
        for alg in ("c217", "e103"):
            with self.subTest(alg=alg):
                t = self._tabela(alg)
                esp = t.column("espaco_modelo").to_pylist()
                self.assertGreater(len(esp), 0)
                self.assertEqual(set(esp), {"cru"},
                                 "ainda há linha sem `espaco_modelo`")

    def test_a_assimetria_entre_busca_e_sonda_ACABOU(self):
        for alg in ("c217", "e103"):
            with self.subTest(alg=alg):
                t = self._tabela(alg)
                por = {}
                for r, e in zip(t.column("regime").to_pylist(),
                                t.column("espaco_modelo").to_pylist()):
                    por.setdefault(r, set()).add(e)
                self.assertGreaterEqual(len(por), 2,
                                        "a célula tem só um regime — sem prova")
                for regime, vals in por.items():
                    with self.subTest(regime=regime):
                        self.assertEqual(vals, {"cru"})


# ═══════════════════════════════════════════════════════════════════════════
#  T14.8 — a f-string do sobol_batch
# ═══════════════════════════════════════════════════════════════════════════

class TestNotaPotenciaDeDois(unittest.TestCase):

    def _params(self, q: int) -> dict:
        """Roda a célula mais barata do piso com o `q` pedido, em tempdir."""
        from src import naming
        with tempfile.TemporaryDirectory() as dr:
            os.symlink(os.path.join(_RAIZ, "data", "doe"),
                       os.path.join(dr, "doe"))
            from src.sobol_batch import run_sobol_batch
            alvo = ("batch", "sobol_batch", "MMF1", 0)
            run_sobol_batch(*alvo, data_root=dr, q=q)
            with open(naming.manifest_path(*alvo, data_root=dr),
                      encoding="utf-8") as fh:
                return json.load(fh)["params"]

    def test_a_nota_segue_o_q_REAL_do_run(self):
        pr = self._params(1)
        self.assertEqual(pr["q"], 1)
        self.assertIn("q=1", pr["nota_potencia_de_2"])
        self.assertNotIn("q=10", pr["nota_potencia_de_2"],
                         "a nota descreve OUTRO run — é o defeito BL-20")

    def test_no_q_do_grid_a_nota_continua_correta(self):
        # o grid inteiro é q=10 (150/150 linhas do runs_matrix): a correção não
        # pode ter mudado o que a campanha de fato publica.
        pr = self._params(10)
        self.assertEqual(pr["q"], 10)
        self.assertIn("q=10 não é potência de 2", pr["nota_potencia_de_2"])
        self.assertIn("random(10)", pr["nota_potencia_de_2"])

    def test_a_nota_bate_com_o_COMPORTAMENTO_REAL_do_scipy(self):
        """Doc×código: a nota afirma que o scipy avisa — então ele tem de avisar."""
        from scipy.stats import qmc
        for q in (1, 2, 3, 10, 16):
            with self.subTest(q=q):
                s = qmc.Sobol(d=2, scramble=True, seed=7)
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    s.random(q)
                    avisou = any("balance properties" in str(x.message) for x in w)
                self.assertEqual(avisou, bool(q & (q - 1)),
                                 "o scipy não se comporta como a nota afirma")

    def test_o_sigma_dict_e_a_nota_concordam_sobre_o_q(self):
        # o sigma_dict do MESMO manifesto sempre derivou do `q` real — era essa
        # discordância interna que provava a omissão local.
        with tempfile.TemporaryDirectory() as dr:
            from src import naming
            os.symlink(os.path.join(_RAIZ, "data", "doe"),
                       os.path.join(dr, "doe"))
            from src.sobol_batch import run_sobol_batch
            alvo = ("batch", "sobol_batch", "MMF1", 0)
            run_sobol_batch(*alvo, data_root=dr, q=1)
            with open(naming.manifest_path(*alvo, data_root=dr),
                      encoding="utf-8") as fh:
                man = json.load(fh)
        self.assertIn("q=1", man["sigma_dict"]["lote"])
        self.assertIn("q=1", man["params"]["nota_potencia_de_2"])


if __name__ == "__main__":
    unittest.main()
