# -*- coding: utf-8 -*-
"""T14.3 / BL-14 — `frente1_excede_pop` contra o N EFETIVO, não o nominal.

**O defeito.** A D88 nomeia a cláusula *"quando a frente-1 do DoE excede A
POPULAÇÃO"*. A população do `moead`/`nsga3` em M=3 é **15** (o `UniformPoint`
reajusta o lattice: 20 → 15), e é por ela que o `initFcn` corta — mas
`src/experiment.m` comparava com `N_nominal = 20`. `nsga2`/`smsemoa` não
decompõem, então neles `N_efetivo == N_nominal` e a flag sempre esteve certa.

**O controle negativo é o próprio corpus da rodada-42** — 112 células de piso
gravadas pelo código ANTIGO. Re-medido aqui (não copiado do relatório):

| alg | problema | \\|F1\\| | N_nom | N_ef | flag gravada | verdade |
|---|---|---|---|---|---|---|
| moead | DTLZ1 | 17 | 20 | 15 | **False** | True |
| moead | DTLZ3 | 19 | 20 | 15 | **False** | True |
| nsga3 | DTLZ1 | 17 | 20 | 15 | **False** | True |
| nsga3 | DTLZ3 | 19 | 20 | 15 | **False** | True |

4/112 — exatamente a faixa 16–20, que só existe quando o lattice reduz N.
`nsga2`/`smsemoa`: 0/56. E o A/B é limpo: rodando as MESMAS 4 células com o
código novo, `n_frente1` sai **idêntico** (17/19) e só a flag vira `true` — o
que muda é o metadado, não a busca.

O campo é descritivo (nenhum passo do MOEA/D o lê) e a seleção REAL está
correta — o dano é de leitura: quem usa a flag para achar "aqui o crowding
decidiu na frente 1" perde DTLZ1 e DTLZ3 em dois configs.
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

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

PISOS = ("moead", "nsga3", "nsga2", "smsemoa")
COM_LATTICE = ("moead", "nsga3")

#: As 4 células que o código antigo errou (re-medidas no corpus, não copiadas).
ERRADAS_ESPERADAS = {("moead", "DTLZ1"), ("moead", "DTLZ3"),
                     ("nsga3", "DTLZ1"), ("nsga3", "DTLZ3")}


def _matlab_bin():
    """O binário do MATLAB, ou None (a máquina do autor tem R2025a — D80)."""
    cand = os.environ.get("UA_DD_SAEA_MATLAB")
    if cand and os.path.exists(cand):
        return cand
    cand = "/Applications/MATLAB_R2025a.app/bin/matlab"
    if os.path.exists(cand):
        return cand
    return shutil.which("matlab")


MATLAB = _matlab_bin()

#: Driver: roda as células REAIS em tempdir e devolve o `rec:'seeding'` de cada.
#: `parallel` nunca entra aqui (O-09) — `experiment` é chamado célula a célula.
DRIVER = r"""
function drv_t14_pisos(raiz, dr, especifico)
  addpath(genpath(fullfile(raiz, 'src')));
  cd(raiz);
  pares = jsondecode(especifico);
  out = struct();
  for i = 1:numel(pares)
    a = pares(i).alg; p = pares(i).problema;
    try
      experiment(a, p, 42, 'main', dr);
    catch e
      fprintf(2, 'FALHOU %s/%s: %s\n', a, p, e.message);
    end
    jp = fullfile(dr, 'experiments', 'main', a, ...
                  sprintf('exp_main_%s_%s_42.jsonl', a, p));
    if ~isfile(jp), continue; end
    linhas = splitlines(string(fileread(jp)));
    for k = 1:numel(linhas)
      if strlength(linhas(k)) > 0 && contains(linhas(k), '"rec":"seeding"')
        r = jsondecode(linhas(k));
        out.(sprintf('%s__%s', a, p)) = struct( ...
          'n_frente1', r.n_frente1, 'N_nominal', r.N_nominal, ...
          'frente1_excede_pop', r.frente1_excede_pop);
        break
      end
    end
  end
  % o N EFETIVO vem do lattice — deterministico, sem run nenhum
  out.uniformpoint_M3 = numel(UniformPoint(20, 3)) / 3;
  out.uniformpoint_M2 = numel(UniformPoint(20, 2)) / 2;
  fid = fopen(fullfile(dr, 'resultado.json'), 'w');
  fprintf(fid, '%s', jsonencode(out)); fclose(fid);
end
"""


def _seeding_do_corpus(alg: str, path: str) -> dict | None:
    with open(path, "rb") as fh:
        for raw in fh:
            if b'"rec":"seeding"' not in raw:
                continue
            try:
                return json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                return None
    return None


def _corpus_pisos() -> list[dict]:
    """As células de piso da s42 no disco local, com ⑥ + `params.N_efetivo`."""
    linhas = []
    for alg in PISOS:
        for p in sorted(glob.glob(os.path.join(
                _RAIZ, "data", "experiments", "main", alg, "*.jsonl"))):
            mp = p[:-len(".jsonl")] + ".manifest.json"
            if not os.path.exists(mp):
                continue
            seed = _seeding_do_corpus(alg, p)
            if seed is None:
                continue
            with open(mp, encoding="utf-8") as fh:
                man = json.load(fh)
            n_ef = (man.get("params") or {}).get("N_efetivo")
            if n_ef is None:
                continue
            nome = os.path.basename(p)[len("exp_main_%s_" % alg):-len("_42.jsonl")]
            linhas.append({
                "alg": alg, "problema": nome, "n_frente1": int(seed["n_frente1"]),
                "N_nominal": int(seed["N_nominal"]), "N_efetivo": int(n_ef),
                "flag_gravada": bool(seed["frente1_excede_pop"]),
            })
    return linhas


# ═══════════════════════════════════════════════════════════════════════════
#  O controle negativo: o corpus da rodada-42, gravado pelo código ANTIGO
# ═══════════════════════════════════════════════════════════════════════════

class TestCorpusS42(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.linhas = _corpus_pisos()

    def setUp(self):
        if not self.linhas:
            self.skipTest("corpus de pisos ausente no disco local "
                          "(a cópia OFICIAL é a do BUCKET)")

    def test_o_corpus_cobre_os_4_pisos(self):
        por_alg = {a: sum(1 for x in self.linhas if x["alg"] == a) for a in PISOS}
        self.assertEqual(set(por_alg), set(PISOS))
        for alg, n in por_alg.items():
            with self.subTest(alg=alg):
                self.assertGreaterEqual(n, 25, "corpus raso demais p/ o controle")

    def test_o_lattice_REDUZ_a_populacao_so_em_moead_e_nsga3(self):
        # a premissa do item: se N_ef == N_nominal em toda parte, não há defeito
        reduzidos = {(x["alg"], x["problema"]) for x in self.linhas
                     if x["N_efetivo"] < x["N_nominal"]}
        self.assertTrue(reduzidos, "nenhuma célula com lattice reduzido")
        self.assertEqual({a for a, _ in reduzidos}, set(COM_LATTICE))

    def test_a_flag_ANTIGA_erra_exatamente_as_4_celulas_conhecidas(self):
        erradas = {(x["alg"], x["problema"]) for x in self.linhas
                   if x["flag_gravada"] != (x["n_frente1"] > x["N_efetivo"])}
        self.assertEqual(erradas, ERRADAS_ESPERADAS)

    def test_a_flag_antiga_e_exatamente_a_comparacao_com_o_NOMINAL(self):
        # prova de que o defeito é ESTE e não outro: a flag gravada reproduz
        # `|F1| > N_nominal` em 112/112, inclusive nas 4 que ela erra.
        divergem = [(x["alg"], x["problema"]) for x in self.linhas
                    if x["flag_gravada"] != (x["n_frente1"] > x["N_nominal"])]
        self.assertEqual(divergem, [])

    def test_nsga2_e_smsemoa_nunca_foram_afetados(self):
        for x in self.linhas:
            if x["alg"] in ("nsga2", "smsemoa"):
                with self.subTest(alg=x["alg"], problema=x["problema"]):
                    self.assertEqual(x["N_efetivo"], x["N_nominal"])


# ═══════════════════════════════════════════════════════════════════════════
#  A fiação em src/experiment.m
# ═══════════════════════════════════════════════════════════════════════════

class TestFiacaoNoExperimentM(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(_RAIZ, "src", "experiment.m"), encoding="utf-8") as fh:
            cls.src = fh.read()

    def test_a_flag_compara_com_o_lattice(self):
        self.assertIn("'frente1_excede_pop', sum(FrontNo == 1) > N_lattice",
                      self.src)
        self.assertNotIn("'frente1_excede_pop', sum(FrontNo == 1) > N_nominal",
                         self.src)

    def test_o_lattice_nasce_no_nominal_e_e_reescrito_pelo_UniformPoint(self):
        # nsga2/smsemoa não decompõem: sem o default a variável nem existiria
        self.assertIn("N_lattice = N_nominal;", self.src)
        self.assertIn("N_lattice = Nlat;", self.src)

    def test_o_lattice_e_definido_ANTES_da_linha_de_seeding(self):
        i_def = self.src.index("N_lattice = N_nominal;")
        i_uso = self.src.index("'frente1_excede_pop'")
        self.assertLess(i_def, i_uso,
                        "a flag usaria uma variável ainda inexistente")


# ═══════════════════════════════════════════════════════════════════════════
#  A célula REAL em MATLAB — o A/B contra o corpus
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(MATLAB, "MATLAB ausente nesta máquina")
class TestCelulasReaisMatlab(unittest.TestCase):
    """Roda as 4 células erradas + 4 de controle e compara com a s42.

    Célula: DTLZ1/DTLZ3 nos 4 pisos, semente 42 — as MESMAS do corpus, ~4,4 s
    cada (`f5/tempo_f52d.csv`). O A/B é limpo porque `n_frente1` tem de sair
    IDÊNTICO ao gravado na s42: se ele mudasse, a busca teria mudado, e aí a
    comparação da flag não provaria nada.
    """

    ALVOS = [{"alg": a, "problema": p}
             for a in PISOS for p in ("DTLZ1", "DTLZ3")]

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="t14_pisos_")
        dr = os.path.join(cls.tmp, "data")
        os.makedirs(dr)
        # o DoE é artefato de ENTRADA e nunca se regenera (D63): link, não cópia.
        os.symlink(os.path.join(_RAIZ, "data", "doe"), os.path.join(dr, "doe"))
        with open(os.path.join(cls.tmp, "drv_t14_pisos.m"), "w",
                  encoding="utf-8") as fh:
            fh.write(DRIVER)
        cls.proc = subprocess.run(
            [MATLAB, "-sd", cls.tmp, "-batch",
             "drv_t14_pisos('%s','%s','%s')"
             % (_RAIZ, dr, json.dumps(cls.ALVOS).replace("'", "''"))],
            capture_output=True, text=True, timeout=1800)
        alvo = os.path.join(dr, "resultado.json")
        cls.res = None
        if os.path.exists(alvo):
            with open(alvo, encoding="utf-8") as fh:
                cls.res = json.load(fh)
        cls.corpus = {(x["alg"], x["problema"]): x for x in _corpus_pisos()}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_o_driver_matlab_rodou(self):
        self.assertIsNotNone(
            self.res, "MATLAB não produziu resultado.json.\nSTDOUT:\n%s\n"
                      "STDERR:\n%s" % (self.proc.stdout[-2000:],
                                       self.proc.stderr[-2000:]))

    def test_o_lattice_do_UniformPoint_e_o_que_o_item_afirma(self):
        # a premissa medida NO MATLAB: M=3 reduz 20→15; M=2 mantém 20.
        self.assertEqual(int(self.res["uniformpoint_M3"]), 15)
        self.assertEqual(int(self.res["uniformpoint_M2"]), 20)

    def test_as_4_celulas_erradas_agora_dizem_a_VERDADE(self):
        for alg, prob in sorted(ERRADAS_ESPERADAS):
            with self.subTest(alg=alg, problema=prob):
                r = self.res["%s__%s" % (alg, prob)]
                self.assertTrue(
                    r["frente1_excede_pop"],
                    "|F1|=%s > N_ef=15 e a flag continua falsa"
                    % (r["n_frente1"],))
                # o corpus (código ANTIGO) dizia False na MESMA célula
                self.assertFalse(self.corpus[(alg, prob)]["flag_gravada"])

    def test_a_BUSCA_nao_mudou_e_por_isso_o_A_B_vale(self):
        for alvo in self.ALVOS:
            chave = (alvo["alg"], alvo["problema"])
            if chave not in self.corpus:
                continue
            with self.subTest(alg=chave[0], problema=chave[1]):
                r = self.res["%s__%s" % chave]
                self.assertEqual(int(r["n_frente1"]),
                                 self.corpus[chave]["n_frente1"],
                                 "n_frente1 mudou — o fix tocou a busca")
                self.assertEqual(int(r["N_nominal"]),
                                 self.corpus[chave]["N_nominal"])

    def test_nsga2_e_smsemoa_saem_BIT_IDENTICOS_ao_corpus(self):
        # controle do outro lado: nos 2 pisos sem lattice nada pode ter mudado
        for alg in ("nsga2", "smsemoa"):
            for prob in ("DTLZ1", "DTLZ3"):
                chave = (alg, prob)
                if chave not in self.corpus:
                    continue
                with self.subTest(alg=alg, problema=prob):
                    r = self.res["%s__%s" % chave]
                    self.assertEqual(bool(r["frente1_excede_pop"]),
                                     self.corpus[chave]["flag_gravada"],
                                     "o fix mexeu num piso que não tem lattice")


if __name__ == "__main__":
    unittest.main()
