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

from tests import TIMEOUT_MATLAB   # [M8] teto unico — nunca literal

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
    mp = strrep(jp, '.jsonl', '.manifest.json');
    if ~isfile(jp), continue; end
    reg = struct();
    linhas = splitlines(string(fileread(jp)));
    for k = 1:numel(linhas)
      if strlength(linhas(k)) > 0 && contains(linhas(k), '"rec":"seeding"')
        r = jsondecode(linhas(k));
        reg.n_frente1 = r.n_frente1;
        reg.N_nominal = r.N_nominal;
        reg.frente1_excede_pop = r.frente1_excede_pop;
        break
      end
    end
    if isfile(mp)                       % [T14.6] os params do ⑤ (BL-13)
      man = jsondecode(fileread(mp));
      reg.N_efetivo   = man.params.N_efetivo;
      reg.n_geracoes  = man.n_geracoes;
      reg.cache_hits  = man.cache_hits;
      reg.maxfe       = man.maxfe;
      reg.operadores  = man.params.operadores;
      reg.ger_deriv   = man.params.geracoes_derivadas;
    end
    out.(sprintf('%s__%s', a, p)) = reg;
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

#: [M8 · 2026-08-01] GUARDA DE PORTABILIDADE — o corpus da s42 NÃO viaja.
#:
#: `data/experiments/` é **gitignored** (`.gitignore:6`): o corpus da rodada-42
#: mora no BUCKET e, localmente, só no Mac do autor. Numa VM recém-clonada ele
#: não existe — medido em 2026-08-01: Mac ~666 células, vm10 6, vm2 5, vm1 **0**.
#:
#: Sem esta guarda, um teste que AFIRMA sobre o corpus reprova a máquina por um
#: motivo que não é a máquina — e foi o que aconteceu: as 4 VMs "reprovaram" o
#: portão de aceitação do M8 medindo dados que nunca estiveram lá. É a MESMA
#: disciplina do `skipUnless(MATLAB, ...)` deste arquivo: onde o insumo não
#: está, PULA-SE; não se inventa vermelho.
_N_CORPUS_PISOS = sum(
    len(glob.glob(os.path.join(_RAIZ, "data", "experiments", "main", _a, "*.jsonl")))
    for _a in ("nsga2", "nsga3", "moead", "smsemoa"))
#: 112 no Mac (4 pisos × 28 células); 0–6 nas VMs. O limiar separa os dois mundos
#: sem depender do número exato, que pode crescer.
_TEM_CORPUS = _N_CORPUS_PISOS >= 100
_SEM_CORPUS = ("corpus da s42 ausente/parcial nesta máquina (%d células de piso; "
               "`data/experiments/` é gitignored e o corpus mora no bucket)"
               % _N_CORPUS_PISOS)


@unittest.skipUnless(_TEM_CORPUS, _SEM_CORPUS)
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
@unittest.skipUnless(_TEM_CORPUS, _SEM_CORPUS)   # o A/B é CONTRA o corpus da s42
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
            capture_output=True, text=True, timeout=TIMEOUT_MATLAB)
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


# ═══════════════════════════════════════════════════════════════════════════
#  T14.6 / BL-13 — `geracoes_derivadas` RAMIFICADA por família de operador
# ═══════════════════════════════════════════════════════════════════════════
#
# A string única declarava o mecanismo do NSGA-II para os 4 pisos. Mas
# `MOEAD.m:45` e `SMSEMOA.m:29` chamam **`OperatorGAhalf`** (1 prole por
# subproblema ⇒ `N_efetivo` por geração) e `NSGAII.m:27`/`NSGAIII.m:29` chamam
# **`OperatorGA`** (prole em PARES ⇒ `2*floor(N_ef/2)`). Os dois denominadores
# só DIVERGEM com `N_efetivo` ÍMPAR — as células M=3 do lattice (N_ef=15) —, e é
# exatamente ali que o moead errava.
#
# ⚠ O bloqueador BL-13 prescreve `floor((20D+clones)/N_ef) + 1` para o moead.
# MEDIDO: o `+1` acerta **0/28**; sem ele, **28/28**. A prescrição está errada e
# foi corrigida pelo dado (o teste abaixo tranca isso).

PAR = ("nsga2", "nsga3")          # OperatorGA      → prole em pares
HALF = ("moead", "smsemoa")       # OperatorGAhalf  → 1 prole por subproblema


def _prev(alg: str, D: int, n_dup: int, n_ef: int) -> int:
    """A fórmula RAMIFICADA — a que este item passa a publicar no ⑤."""
    den = 2 * (n_ef // 2) if alg in PAR else n_ef
    return (20 * D + n_dup) // den


def _corpus_geracoes() -> list[dict]:
    linhas = []
    for alg in PISOS:
        for mp in sorted(glob.glob(os.path.join(
                _RAIZ, "data", "experiments", "main", alg, "*.manifest.json"))):
            with open(mp, encoding="utf-8") as fh:
                m = json.load(fh)
            pr = m.get("params") or {}
            if None in (pr.get("N_efetivo"), m.get("n_geracoes"),
                        m.get("cache_hits"), m.get("maxfe")):
                continue
            linhas.append({
                "alg": alg, "celula": os.path.basename(mp),
                "D": (int(m["maxfe"]) + 1) // 31,
                "N_efetivo": int(pr["N_efetivo"]),
                "n_dup": int(m["cache_hits"]),
                "n_geracoes": int(m["n_geracoes"]),
            })
    return linhas


class TestGeracoesDerivadasCorpus(unittest.TestCase):
    """A fórmula é aferida contra o `n_geracoes` REAL das 112 células."""

    @classmethod
    def setUpClass(cls):
        cls.linhas = _corpus_geracoes()

    def setUp(self):
        if len(self.linhas) < 100:
            self.skipTest("corpus de pisos ausente/raso no disco local")

    def test_a_ramificada_acerta_mais_que_a_formula_unica(self):
        ram = sum(_prev(x["alg"], x["D"], x["n_dup"], x["N_efetivo"])
                  == x["n_geracoes"] for x in self.linhas)
        # a fórmula ÚNICA de antes: denominador em pares para TODOS
        uni = sum(((20 * x["D"] + x["n_dup"]) // (2 * (x["N_efetivo"] // 2)))
                  == x["n_geracoes"] for x in self.linhas)
        self.assertEqual((uni, ram), (103, 110),
                         "os acertos mudaram — re-meça antes de mexer no texto")

    def test_o_moead_fecha_28_de_28_com_o_denominador_certo(self):
        for alg, esperado in (("moead", 28), ("smsemoa", 28),
                              ("nsga2", 27), ("nsga3", 27)):
            with self.subTest(alg=alg):
                sub = [x for x in self.linhas if x["alg"] == alg]
                ok = sum(_prev(alg, x["D"], x["n_dup"], x["N_efetivo"])
                         == x["n_geracoes"] for x in sub)
                self.assertEqual((len(sub), ok), (28, esperado))

    def test_CONTROLE_o_mais_um_do_bloqueador_acerta_ZERO(self):
        """O BL-13 prescreve `floor(.../N_ef)+1` para o moead. Medido: 0/28."""
        sub = [x for x in self.linhas if x["alg"] == "moead"]
        com_mais_um = sum(((20 * x["D"] + x["n_dup"]) // x["N_efetivo"]) + 1
                          == x["n_geracoes"] for x in sub)
        self.assertEqual(com_mais_um, 0,
                         "o `+1` do bloqueador acertou algo — re-avalie")

    def test_os_denominadores_so_divergem_com_N_efetivo_IMPAR(self):
        # é a explicação de por que o defeito só aparecia no moead: em N_ef=20
        # `2*floor(N/2) == N`, então as duas famílias dão o MESMO número.
        for x in self.linhas:
            par = 2 * (x["N_efetivo"] // 2)
            with self.subTest(alg=x["alg"], celula=x["celula"]):
                self.assertEqual(par == x["N_efetivo"], x["N_efetivo"] % 2 == 0)

    def test_o_smsemoa_nao_muda_de_numero_apesar_de_mudar_de_familia(self):
        # honestidade: no smsemoa o N_ef é sempre 20 (não decompõe) ⇒ a troca de
        # denominador é semanticamente certa e numericamente NEUTRA.
        for x in [y for y in self.linhas if y["alg"] == "smsemoa"]:
            with self.subTest(celula=x["celula"]):
                self.assertEqual(x["N_efetivo"] % 2, 0)
                self.assertEqual(_prev("smsemoa", x["D"], x["n_dup"], x["N_efetivo"]),
                                 (20 * x["D"] + x["n_dup"]) // (2 * (x["N_efetivo"] // 2)))


class TestGeracoesDerivadasFonte(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(_RAIZ, "src", "experiment.m"), encoding="utf-8") as fh:
            cls.src = fh.read()

    def test_a_string_ramifica_pelas_DUAS_familias(self):
        self.assertIn('if any(strcmp(char(alg), {\'moead\',\'smsemoa\'}))', self.src)
        self.assertIn('familia_op  = "OperatorGAhalf";', self.src)
        self.assertIn('familia_op  = "OperatorGA";', self.src)

    def test_a_string_unica_para_os_4_pisos_saiu(self):
        self.assertNotIn(
            'gerando prole em PARES — 2*floor(N_efetivo/2) por " + ...', self.src)

    def test_os_sitios_do_vendor_estao_citados(self):
        for sitio in ("MOEAD.m:45", "SMSEMOA.m:29", "NSGAII.m:27", "NSGAIII.m:29"):
            with self.subTest(sitio=sitio):
                self.assertIn(sitio, self.src)

    def test_os_sitios_citados_EXISTEM_no_vendor(self):
        """Doc×código: a linha citada tem de chamar o operador que a string diz."""
        base = os.path.join(_RAIZ, "algorithms", "_PlatEMO", "PlatEMO",
                            "Algorithms", "Multi-objective optimization")
        alvos = {
            os.path.join(base, "MOEA-D", "MOEAD.m"): (45, "OperatorGAhalf"),
            os.path.join(base, "SMS-EMOA", "SMSEMOA.m"): (29, "OperatorGAhalf"),
            os.path.join(base, "NSGA-II", "NSGAII.m"): (27, "OperatorGA("),
            os.path.join(base, "NSGA-III", "NSGAIII.m"): (29, "OperatorGA("),
        }
        for p, (linha, token) in alvos.items():
            with self.subTest(arquivo=os.path.basename(p)):
                if not os.path.exists(p):
                    self.skipTest("árvore vendorizada ausente")
                with open(p, encoding="utf-8", errors="replace") as fh:
                    linhas = fh.read().splitlines()
                self.assertIn(token, linhas[linha - 1],
                              "a citação da string aponta para a linha errada")


@unittest.skipUnless(MATLAB, "MATLAB ausente nesta máquina")
class TestGeracoesDerivadasNoQuintoReal(unittest.TestCase):
    """As 8 células reais do A/B também carregam o ⑤ ramificado."""

    @classmethod
    def setUpClass(cls):
        cls.res = TestCelulasReaisMatlab.res

    def test_cada_piso_declara_a_sua_familia(self):
        for alg in PISOS:
            esperado = "OperatorGAhalf" if alg in HALF else "OperatorGA"
            for prob in ("DTLZ1", "DTLZ3"):
                chave = "%s__%s" % (alg, prob)
                if chave not in self.res:
                    continue
                with self.subTest(alg=alg, problema=prob):
                    ops = self.res[chave]["operadores"]
                    self.assertIn(esperado, ops)
                    if esperado == "OperatorGA":       # não pode casar o irmão
                        self.assertNotIn("OperatorGAhalf", ops)

    def test_a_formula_do_texto_bate_com_o_n_geracoes_do_MESMO_run(self):
        """Dado FRESCO, não a s42: o ⑤ tem de ser autoconsistente."""
        for alg in PISOS:
            for prob in ("DTLZ1", "DTLZ3"):
                chave = "%s__%s" % (alg, prob)
                if chave not in self.res or "n_geracoes" not in self.res[chave]:
                    continue
                r = self.res[chave]
                D = (int(r["maxfe"]) + 1) // 31
                with self.subTest(alg=alg, problema=prob):
                    self.assertEqual(
                        _prev(alg, D, int(r["cache_hits"]), int(r["N_efetivo"])),
                        int(r["n_geracoes"]),
                        "a fórmula publicada no ⑤ não reproduz o `n_geracoes` "
                        "do próprio run")

    def test_o_manda_LER_continua_na_string(self):
        # a string prescreve "não derive, LEIA" — é a regra que sobrevive a
        # qualquer fórmula aproximada, e não pode sumir na reescrita.
        r = self.res["moead__DTLZ1"]
        self.assertIn("nao derive, LEIA", r["ger_deriv"])
        self.assertIn("110/112", r["ger_deriv"])


if __name__ == "__main__":
    unittest.main()
