# -*- coding: utf-8 -*-
"""T14.5 / BL-12 — a calibragem do `REGRA_DO_ROTULO` do b4, RE-MEDIDA.

**O defeito.** Os 3 números publicados dentro do `sigma_dict` do b4 —
*"prevalência real medida 65,5%, acurácia 0,350, AUC 0,716"* — não reproduzem
em corpus nenhum. Nenhuma das 5 leituras candidatas testadas na F5.4 os produz,
e o par `0,40% / 0,995`, atribuído ali a uma leitura "errada", é o par que a
regra 12 do CONTRATO atribui ao **c122**. A REGRA em si está certa (confere com
`GetOutput.m:16-19`); os parênteses é que vieram de outro lugar.

**O que este teste faz de diferente de um `assertIn` de texto.** Ele RE-MEDE os
números a partir das baterias da F5 e exige que o texto os reproduza — a
armadilha doc×código mecanizada. Se alguém reescrever a string com um número
"de memória", o teste cai.

Medido aqui (régua Sobol do smoke, MMF1, 24 blocos × 2.000 = 48.000 linhas):

| leitura | prevalência | acurácia | AUC (média dos blocos) |
|---|---|---|---|
| **DI-18 / GetOutput** (a do algoritmo) | 28,43% | 0,5743 | **0,5075** |
| "não dominado por nenhuma ref" | 28,43% | 0,5743 | 0,5075 ← **idêntica** |
| "domina ≥1 ref" (Alg. 4 do paper) | 9,85% | 0,6312 | 0,5193 |

⚠ **Errata do próprio cartão T14:** ele manda gravar `AUC 0,5065`. A medição dá
**0,5075** — e é o valor que o `b4.md` publica na sua §6.3, na regra de leitura
12 e no controle cruzado régua-do-smoke × célula-MMF1-da-s42. O `0,5065` aparece
uma única vez, na tabela do §E1 do mesmo relatório.

⚠ Consequência da 2ª linha da tabela: a frase antiga *"elas medem outra coisa e
inflam o número"* é FALSA para 19/25 células do b4 (as M=2), onde as duas
leituras são numericamente idênticas. Isso também foi corrigido.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import shutil
import statistics as st
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

EXPERIMENT_M = os.path.join(_RAIZ, "src", "experiment.m")
BATERIA = os.path.join(_RAIZ, "f5", "t11", "baterias", "b4")

def _matlab_bin():
    """O binário do MATLAB, ou None (a máquina do autor tem R2025a — D80)."""
    cand = os.environ.get("UA_DD_SAEA_MATLAB")
    if cand and os.path.exists(cand):
        return cand
    cand = "/Applications/MATLAB_R2025a.app/bin/matlab"
    if os.path.exists(cand):
        return cand
    return shutil.which("matlab")


#: Os números que estavam publicados e não reproduzem em corpus nenhum.
STALE = ("65,5%", "acuracia 0,350", "AUC 0,716", "0,00%", "0,999", "0,40%",
         "0,995")


def _bloco_b4() -> str:
    """O `REGRA_DO_ROTULO` do b4 (o do c217 é outro — a busca é ancorada)."""
    with open(EXPERIMENT_M, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index("o b4 (CSEA) classifica um candidato")
    return src[i:src.index("'cobertura_3'", i)]


class TestCalibragemDoRotuloB4(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bloco = _bloco_b4()

    # ── o que SAIU ──────────────────────────────────────────────────────────
    def test_os_numeros_que_nao_reproduzem_sairam(self):
        for n in STALE:
            with self.subTest(numero=n):
                self.assertNotIn(n, self.bloco,
                                 "número de calibração stale ainda publicado")

    def test_a_afirmacao_falsa_sobre_a_leitura_alternativa_saiu(self):
        self.assertNotIn("elas medem outra coisa e inflam o numero", self.bloco)

    # ── o que ENTROU ────────────────────────────────────────────────────────
    def test_a_REGRA_continua_intacta(self):
        # o que estava errado eram os parênteses, não a regra: ela confere com
        # `GetOutput.m:16-19` e NÃO se mexe (a F5.4 provou 3.589/3.589 exato).
        self.assertIn("nao e pior que TODAS as 6 referencias", self.bloco)
        self.assertIn("GetOutput.m:16-19", self.bloco)

    def test_todo_numero_vem_com_o_corpus_nomeado(self):
        for marca in ("regua Sobol do SMOKE", "MMF1", "48.000 linhas",
                      "s42 INTEIRA", "3.166 blocos"):
            with self.subTest(marca=marca):
                self.assertIn(marca, self.bloco)

    def test_a_definicao_de_cada_agregado_esta_escrita(self):
        # o pecado original era publicar número sem dizer o que ele agrega:
        # "AUC" sozinho é ambíguo (média dos blocos × pooled) — e é essa
        # ambiguidade que produziu 0,5065 num lugar e 0,5075 em três outros.
        self.assertIn("POOLED", self.bloco)
        self.assertIn("media dos AUC", self.bloco)

    def test_declara_que_em_M2_as_duas_leituras_COINCIDEM(self):
        self.assertIn("NUMERICAMENTE IDENTICA", self.bloco)
        self.assertIn("19/25", self.bloco)

    # ── asserção de VALOR: o texto reproduz a MEDIÇÃO ────────────────────────
    def _leituras_medidas(self) -> dict:
        p = os.path.join(BATERIA, "b4_t11_leituras_sobol.csv")
        if not os.path.exists(p):
            self.skipTest("baterias da F5 ausentes nesta máquina "
                          "(f5/t11 não é rastreado pelo git)")
        por = defaultdict(list)
        with open(p, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                por[r["leitura"]].append(r)
        out = {}
        for k, v in por.items():
            aucs = [float(x["auc"]) for x in v if x["auc"] not in ("", "nan")]
            out[k] = {
                "prev": st.mean(float(x["prev"]) for x in v),
                "acc": st.mean(float(x["acc"]) for x in v),
                "auc": st.mean(aucs) if aucs else None,
                "n_blocos": len(v),
            }
        return out

    def test_os_numeros_do_texto_SAO_os_medidos(self):
        m = self._leituras_medidas()
        di18 = next(v for k, v in m.items() if k.startswith("A_DI18"))
        self.assertEqual(di18["n_blocos"], 24)
        for valor, texto in ((di18["prev"] * 100, "28,43%"),
                             (di18["acc"], "0,5743"),
                             (di18["auc"], "0,5075")):
            with self.subTest(esperado=texto):
                fmt = ("%.2f%%" % valor if texto.endswith("%")
                       else "%.4f" % valor).replace(".", ",")
                self.assertEqual(fmt, texto, "a medição mudou de valor")
                self.assertIn(texto, self.bloco, "o texto não publica o medido")

    def test_a_leitura_do_PAPER_tambem_e_o_valor_medido(self):
        m = self._leituras_medidas()
        b = next(v for k, v in m.items() if k.startswith("B_domina"))
        self.assertEqual("%.2f%%" % (b["prev"] * 100), "9.85%")
        self.assertEqual("%.4f" % b["acc"], "0.6312")
        self.assertIn("9,85%", self.bloco)
        self.assertIn("0,6312", self.bloco)

    def test_a_COINCIDENCIA_em_M2_e_medida_e_nao_afirmada(self):
        # a base da correção da frase: A e C dão o MESMO número na régua
        m = self._leituras_medidas()
        a = next(v for k, v in m.items() if k.startswith("A_DI18"))
        c = next(v for k, v in m.items() if k.startswith("C_nao-dominado pelas"))
        for campo in ("prev", "acc", "auc"):
            with self.subTest(campo=campo):
                self.assertAlmostEqual(a[campo], c[campo], places=9)

    def test_CONTROLE_o_65_5_por_cento_nao_sai_de_leitura_NENHUMA(self):
        """Sem isto, "os números são stale" seria alegação, não medida."""
        m = self._leituras_medidas()
        prevs = sorted(round(v["prev"] * 100, 2) for v in m.values())
        self.assertTrue(all(abs(p - 65.5) > 5.0 for p in prevs),
                        "alguma leitura reproduz 65,5%%: %r" % (prevs,))
        self.assertGreaterEqual(len(m), 5, "corpus de leituras raso demais")


@unittest.skipUnless(_matlab_bin(), "MATLAB ausente nesta máquina")
class TestOSigmaDictChegaAoQuintoDeVerdade(unittest.TestCase):
    """Célula b4 REAL: a string tem de ATRAVESSAR o writer, não só existir.

    `checkcode` não pega erro de concatenação de `string`×`char` em MATLAB — só
    o run pega. Célula: `main/b4/MMF4/42`, a mais barata do config (50,8 s na
    `f5/tempo_f52d.csv`; ~46 s medidos aqui), em tempdir.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="t14_b4_")
        dr = os.path.join(cls.tmp, "data")
        os.makedirs(dr)
        for sub in ("doe", "sonda"):     # artefatos de ENTRADA (D63) — por link
            os.symlink(os.path.join(_RAIZ, "data", sub), os.path.join(dr, sub))
        with open(os.path.join(cls.tmp, "drv_t14_b4.m"), "w",
                  encoding="utf-8") as fh:
            fh.write("function drv_t14_b4(raiz, dr)\n"
                     "  addpath(genpath(fullfile(raiz,'src')));\n"
                     "  cd(raiz);\n"
                     "  experiment('b4', 'MMF4', 42, 'main', dr);\n"
                     "end\n")
        cls.proc = subprocess.run(
            [_matlab_bin(), "-sd", cls.tmp, "-batch",
             "drv_t14_b4('%s','%s')" % (_RAIZ, dr)],
            capture_output=True, text=True, timeout=1800)
        cls.man = None
        alvo = glob.glob(os.path.join(dr, "experiments", "main", "b4",
                                      "*.manifest.json"))
        if alvo:
            with open(alvo[0], encoding="utf-8") as fh:
                cls.man = json.load(fh)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_a_celula_rodou(self):
        self.assertIsNotNone(
            self.man, "b4/MMF4 não produziu manifesto.\nSTDOUT:\n%s\nSTDERR:\n%s"
                      % (self.proc.stdout[-2000:], self.proc.stderr[-2000:]))

    def test_a_regra_gravada_no_quinto_e_a_do_fonte(self):
        gravada = self.man["sigma_dict"]["REGRA_DO_ROTULO"]
        # a string do fonte é uma concatenação com `+ ...`: o que se compara é
        # o CONTEÚDO que sobreviveu ao writer, número a número.
        for n in ("28,43%", "0,5743", "0,5075", "8,32%", "0,9035", "0,6646",
                  "9,85%", "0,6312"):
            with self.subTest(numero=n):
                self.assertIn(n, gravada)
        for n in STALE:
            with self.subTest(stale=n):
                self.assertNotIn(n, gravada)

    def test_o_run_fechou_ok(self):
        self.assertIn(self.man["status"], ("ok", "retried_ok"))
        self.assertEqual(self.man["fe_final"], self.man["maxfe"])


# ═══════════════════════════════════════════════════════════════════════════
#  T14.9 / BL-19 — a convenção p0/p1 do b4 sai do run e entra no CONTRATO/SPEC
# ═══════════════════════════════════════════════════════════════════════════
#
# `p0`/`p1` NÃO são "probabilidade da classe 0/1": são MAE por classe no
# conjunto de teste, com os nomes NATIVOS do PlatEMO. A glosa existia só dentro
# do `sigma_dict` de cada run — e quem lê o CONTRATO/SPEC sem abrir um ⑤ troca
# os dois. A F5.4 mediu o custo da troca: a contagem de acertos do log cai de
# **6.268 para 1.252**.
#
# Fonte única, conferida linha a linha (`CSEA.m:77-79`):
#     IndexGood = TestOut==1;
#     p0 = MAE sobre  IndexGood   ⇒ classe RÓTULO 1 (categoria II)
#     p1 = MAE sobre ~IndexGood   ⇒ classe RÓTULO 0 (categoria I)

CSEA_M = os.path.join(
    _RAIZ, "algorithms", "_PlatEMO", "PlatEMO", "Algorithms",
    "Multi-objective optimization", "CSEA", "CSEA.m")
SPEC = os.path.join(_RAIZ, "claude_code_context", "SPEC_experimentos_v5.2.md")
CONTRATO = os.path.join(_RAIZ, "CONTRATO_DE_DADOS.md")
BUNDLE_B4 = os.path.join(_RAIZ, "claude_code_context", "10_rodada1_matlab",
                         "alg_b4_csea.md")


class TestConvencaoP0P1(unittest.TestCase):

    def _texto(self, p):
        if not os.path.exists(p):
            self.skipTest("%s ausente" % os.path.basename(p))
        with open(p, encoding="utf-8", errors="replace") as fh:
            return fh.read()

    # ── a FONTE (o que a doc tem de descrever) ──────────────────────────────
    def test_a_FONTE_diz_o_que_a_doc_afirma(self):
        """Doc×código: se o vendor mudar, a afirmação cai aqui, não no leitor."""
        src = self._texto(CSEA_M).splitlines()
        self.assertIn("IndexGood = TestOut==1;", src[76],
                      "CSEA.m:77 não é mais a definição de IndexGood")
        # :78 mede sobre IndexGood (rótulo 1) e :79 sobre o complemento
        self.assertTrue(src[77].strip().startswith("p0 ="), src[77])
        self.assertIn("TestOut(IndexGood)", src[77])
        self.assertNotIn("~IndexGood", src[77])
        self.assertTrue(src[78].strip().startswith("p1 ="), src[78])
        self.assertIn("TestOut(~IndexGood)", src[78])

    # ── os 3 sítios de doc ──────────────────────────────────────────────────
    def test_o_CONTRATO_publica_a_convencao(self):
        t = self._texto(CONTRATO)
        self.assertIn("BL-19", t)
        self.assertIn("`p0` = MAE da categoria II (rótulo 1", t)
        self.assertIn("`p1` = MAE da categoria I (rótulo 0)", t)
        self.assertIn("CSEA.m:77-79", t)

    def test_a_SPEC_publica_a_convencao_nos_TRES_sitios(self):
        # ⚠ o cartão nomeia :803 e :1875; a varredura deste teste achou um
        # TERCEIRO — o cartão S.4 do b4 (:1486), que também trazia `(p1,p2)`.
        t = self._texto(SPEC)
        self.assertEqual(t.count("BL-19"), 3, "a SPEC tem 3 sítios do p0/p1")
        self.assertIn("`p0` = MAE do rótulo 1 (categoria II)", t)
        self.assertIn("`p1` = MAE do rótulo 0", t)

    def test_o_par_INEXISTENTE_p1_p2_saiu_da_SPEC(self):
        # `(p1,p2)` não existe no código: era o resíduo que a F5.4 apontou
        self.assertNotIn("(p1,p2,rr,tr)", self._texto(SPEC))

    def test_o_bundle_do_b4_foi_REGENERADO(self):
        # "corrigir o gerador, não o gerado": o bundle sai da SPEC por
        # `gen_bundles.py`; se ele não for regenerado, o leitor do bundle
        # continua sem a glosa.
        t = self._texto(BUNDLE_B4)
        self.assertIn("BL-19", t)
        self.assertIn("`p0` = MAE do rótulo 1 (categoria II)", t)
        self.assertNotIn("(p1,p2,rr,tr)", t)

    # ── o alarme contra a inversão ──────────────────────────────────────────
    def test_os_TRES_sitios_avisam_que_a_ORDEM_NAO_se_inverte(self):
        for nome, p in (("CONTRATO", CONTRATO), ("SPEC", SPEC),
                        ("bundle", BUNDLE_B4)):
            with self.subTest(sitio=nome):
                t = self._texto(p).lower()
                self.assertTrue(
                    "não se inverte" in t or "nunca invertíveis" in t
                    or "não-corrigir" in t,
                    "o sítio não alerta contra a inversão")

    def test_o_custo_MEDIDO_da_inversao_esta_publicado(self):
        # número em doc vem com a medida: 6.268 → 1.252 (F5.4)
        for nome, p in (("CONTRATO", CONTRATO), ("SPEC", SPEC)):
            with self.subTest(sitio=nome):
                t = self._texto(p)
                self.assertIn("6.268", t)
                self.assertIn("1.252", t)

    def test_o_sigma_dict_do_run_continua_dizendo_o_MESMO(self):
        # a glosa nova não pode divergir da que já viaja dentro de cada ⑤
        with open(EXPERIMENT_M, encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("'p0_p1'")
        # a string do ⑤ é concatenada com `+ ...`: normaliza antes de comparar
        bloco = " ".join(src[i:i + 400].split())
        self.assertIn('p0 = MAE da categoria II (rotulo 1, CSEA.m:78)', bloco)
        self.assertIn('categoria I (rotulo 0, CSEA.m:79)', bloco)
        self.assertIn("NAO devem ser trocados", bloco)


if __name__ == "__main__":
    unittest.main()
