# -*- coding: utf-8 -*-
"""[T15.7 §2/§3b/§5] Rota R1 do DDMOP7 — avaliador local do .p + ⑤ declarado.

Três camadas de prova:
  1. ESTRUTURAL (sem MATLAB): o desvio "antes da ponte" está fiado nos 10
     sítios de evalFcn do experiment.m; o avaliador local NÃO tem contador de
     FE (o FEBudget é a autoridade, D89); o ⑤/load_sonda usam a fonte única.
  2. VALOR (MATLAB + corpus do .p): `ddmop7_value_local` bate as âncoras
     MEDIDAS f=[4/17, 307/690] (x=zeros com x(3)=0.5, x(7)=-0.2 — cartão §5,
     probe B-27) e f=[1/17, 307/690] (x=zeros — ddmop7_VEREDICTO.md §"zeros");
     pureza ponto-a-ponto; contador de chamadas; CONTROLE NEGATIVO do teto de
     600 (forçar >600 ⇒ DDMOP7:TetoPCode).
  3. FONTE ÚNICA (MATLAB): `sonda_bloco_declarado` devolve campo a campo o
     SONDA_AUSENTE_INFO do src/experiment.py (nenhum literal duplicado).

Guardas: MATLAB ausente ⇒ skip declarado; corpus do .p ausente ⇒ skip
declarado (aponte UA_DD_SAEA_DDMOP_DIR para DDMOP_Exp/Problems). Timeout
SEMPRE `tests.TIMEOUT_MATLAB` (M8), nunca literal.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

from tests import TIMEOUT_MATLAB                          # noqa: E402


def _matlab_bin():
    cand = os.environ.get("UA_DD_SAEA_MATLAB")
    if cand and os.path.exists(cand):
        return cand
    cand = "/Applications/MATLAB_R2025a.app/bin/matlab"
    if os.path.exists(cand):
        return cand
    return shutil.which("matlab")


def _corpus_dir():
    d = os.environ.get("UA_DD_SAEA_DDMOP_DIR", "").strip()
    if not d:
        d = os.path.expanduser(os.path.join("~", "DDMOP", "DDMOP_Exp",
                                            "Problems"))
    return d if os.path.exists(os.path.join(d, "DDMOP7.p")) else None


MATLAB = _matlab_bin()
CORPUS = _corpus_dir()


def _fonte(nome):
    with open(os.path.join(_RAIZ, "src", nome), encoding="utf-8") as fh:
        return fh.read()


def _so_codigo(fonte):
    """Remove comentários MATLAB (respeitando aspas simples) — padrão do
    test_a11_matlab: os arquivos DOCUMENTAM as armadilhas citando o nome
    delas, e um assertNotIn cru reprovaria justamente o aviso."""
    saida = []
    for linha in fonte.splitlines():
        buf, aspas = [], False
        for i, c in enumerate(linha):
            if c == "'" and not (i and linha[i - 1] == "'"):
                aspas = not aspas
            if c == "%" and not aspas:
                break
            buf.append(c)
        saida.append("".join(buf))
    return "\n".join(saida)


def _roda_matlab(script: str, extra_env: dict | None = None) -> dict:
    """Roda `script` num processo MATLAB (-batch) e devolve o JSON <<<...>>>."""
    tmp = tempfile.mkdtemp(prefix="t157_")
    try:
        with open(os.path.join(tmp, "runner_t157.m"), "w",
                  encoding="utf-8") as fh:
            fh.write(script)
        env = dict(os.environ)
        if extra_env:
            env.update(extra_env)
        p = subprocess.run(
            [MATLAB, "-batch", "cd('%s'); runner_t157" % tmp],
            capture_output=True, text=True, timeout=TIMEOUT_MATLAB, env=env)
        m = re.search(r"<<<(.*?)>>>", p.stdout, re.DOTALL)
        if not m:
            raise AssertionError("MATLAB não devolveu o JSON:\n%s\n%s"
                                 % (p.stdout[-2000:], p.stderr[-800:]))
        return json.loads(m.group(1))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════
#  1 · ESTRUTURAL — a fiação, sem MATLAB
# ═══════════════════════════════════════════════════════════════════════════

class TestFiacaoExperimentM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = _fonte("experiment.m")

    def test_os_10_sitios_de_evalFcn_usam_o_ponto_unico(self):
        # 9 run_* com evalFcnPerX + o run_stub com evalFcn = 10 SÍTIOS de
        # chamada (com `;`, o que exclui a linha da definição). Um sítio a
        # menos = um runner MATLAB avaliando DDMOP7 pela ponte py (§2.3).
        chamadas = self.src.count("eval_fcn_por_x(ctx, pp, problema);")
        self.assertEqual(chamadas, 10, "sítios de evalFcn fora do ponto único")
        self.assertEqual(self.src.count("function f = eval_fcn_por_x"), 1)

    def test_a_lambda_da_ponte_so_existe_dentro_do_helper(self):
        # controle: no código ANTERIOR havia 10 lambdas inline; agora a via
        # da ponte vive SÓ dentro de eval_fcn_por_x (1 ocorrência).
        self.assertEqual(
            self.src.count(
                "@(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)))"),
            1)

    def test_o_desvio_do_ddmop7_esta_no_helper(self):
        m = re.search(r"function f = eval_fcn_por_x.*?^end", self.src,
                      re.MULTILINE | re.DOTALL)
        self.assertTrue(m, "helper eval_fcn_por_x sumiu")
        corpo = m.group(0)
        self.assertIn("strcmp(char(problema), 'DDMOP7')", corpo)
        self.assertIn("@(x) ddmop7_value_local(x)", corpo)

    def test_load_sonda_declara_o_opt_out(self):
        m = re.search(r"function sd = load_sonda.*?^end", self.src,
                      re.MULTILINE | re.DOTALL)
        corpo = m.group(0)
        self.assertIn("sonda_bloco_declarado(problema)", corpo)
        # o opt-out vem ANTES do caminho do artefato (nunca toca o parquet)
        self.assertLess(corpo.index("sonda_bloco_declarado"),
                        corpo.index("nm_sonda_path"))

    def test_o_5_declarado_no_fill_manifest_timing(self):
        m = re.search(r"function man = fill_manifest_timing.*?^end", self.src,
                      re.MULTILINE | re.DOTALL)
        corpo = m.group(0)
        self.assertIn("sonda_bloco_declarado(char(man.problema))", corpo)
        # as outras DUAS espécies de ausência continuam existindo:
        self.assertIn("artefato_ausente", corpo)          # acidente/piloto
        self.assertIn('struct(\'status\', "nao_se_aplica"', self.src)  # pisos

    def test_e103_nao_avalia_pela_ponte(self):
        # §2.3: o offline MATLAB lê F do artefato; nenhum evalFcn de ponte.
        m = re.search(r"function \[status, info\] = run_e103.*?^end", self.src,
                      re.MULTILINE | re.DOTALL)
        self.assertNotIn("evaluate_problem", m.group(0))


class TestValueLocalSemContador(unittest.TestCase):
    """O avaliador local NÃO transplantou o contador do molde (D89)."""

    @classmethod
    def setUpClass(cls):
        cls.src = _fonte("ddmop7_value_local.m")

    def test_sem_hard_stop_proprio(self):
        # o molde DDMOP7_evalFcn.m levanta PlatEMO:Termination no hard-stop;
        # aqui NÃO pode existir NO CÓDIGO — o FEBudget do harness é a
        # autoridade (D89). (Os comentários citam a armadilha pelo nome, daí
        # o strip — o mesmo cuidado do test_a11_matlab.)
        codigo = _so_codigo(self.src)
        self.assertNotIn("PlatEMO:Termination", codigo)
        self.assertNotIn("MAX_FE", codigo)
        self.assertNotIn("BudgetExhausted", codigo)

    def test_guard_600_existe(self):
        self.assertIn("DDMOP7:TetoPCode", self.src)
        self.assertIn("P_CODE_CAP = 600", self.src)

    def test_init_descartado_por_processo(self):
        self.assertIn("DDMOP7('init')", self.src)
        self.assertIn("clear DDMOP7", self.src)

    def test_pasta_por_env_e_recusa_DDMOP_Plat(self):
        self.assertIn("UA_DD_SAEA_DDMOP_DIR", self.src)
        self.assertIn("DDMOP_Plat", self.src)

    def test_guards_de_forma_e_finito(self):
        self.assertIn("DDMOP7:FormaInesperada", self.src)
        self.assertIn("DDMOP7:NaoFinito", self.src)


# ═══════════════════════════════════════════════════════════════════════════
#  2 · VALOR — o .p de verdade (âncoras do probe da torre)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(MATLAB, "MATLAB ausente nesta máquina")
@unittest.skipUnless(CORPUS, "corpus do DDMOP7.p ausente — exporte "
                     "UA_DD_SAEA_DDMOP_DIR=<...>/DDMOP_Exp/Problems")
class TestValueLocalNoPCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = (
            "addpath('%s');\n"
            "r = struct();\n"
            "try\n"
            "    xA = zeros(1,17); xA(3) = 0.5; xA(7) = -0.2;\n"
            "    xB = zeros(1,17);\n"
            "    r.FA = ddmop7_value_local(xA);\n"
            "    r.FB = ddmop7_value_local([xB; xA]);\n"
            "    r.chamadas = ddmop7_value_local([], 'chamadas');\n"
            "    ddmop7_value_local(600, 'forca_contador');\n"
            "    try\n"
            "        ddmop7_value_local(xA);\n"
            "        r.guard_id = 'NAO_DISPAROU';\n"
            "    catch ME\n"
            "        r.guard_id = ME.identifier;\n"
            "    end\n"
            "    ddmop7_value_local([], 'reset');\n"
            "    r.chamadas_pos_reset = ddmop7_value_local([], 'chamadas');\n"
            "    r.FA2 = ddmop7_value_local(xA);\n"
            "    r.erro = \"\";\n"
            "catch ME\n"
            "    r.erro = string(ME.identifier) + \": \" + string(ME.message);\n"
            "end\n"
            "disp(\"<<<\" + string(jsonencode(r)) + \">>>\");\n"
            % os.path.join(_RAIZ, "src"))
        cls.r = _roda_matlab(script,
                             extra_env={"UA_DD_SAEA_DDMOP_DIR": CORPUS})

    def test_sem_erro(self):
        self.assertEqual(self.r["erro"], "", self.r)

    def test_ancora_A_do_cartao(self):
        # x=zeros com x(3)=0.5, x(7)=-0.2 ⇒ f=[4/17, 307/690] (cartão §5).
        FA = self.r["FA"]
        self.assertLessEqual(abs(FA[0] - 4 / 17), 1e-12, FA)
        self.assertLessEqual(abs(FA[1] - 307 / 690), 1e-12, FA)

    def test_ancora_B_zeros_do_veredicto(self):
        # zeros ⇒ [1/17, 307/690] (ddmop7_VEREDICTO.md, oráculo medido).
        FB = self.r["FB"][0]
        self.assertLessEqual(abs(FB[0] - 1 / 17), 1e-12, FB)
        self.assertLessEqual(abs(FB[1] - 307 / 690), 1e-12, FB)

    def test_pureza_ponto_a_ponto(self):
        # o MESMO x em chamadas distintas ⇒ o MESMO f (D102.11: 'value' pura).
        self.assertEqual(self.r["FA"], self.r["FB"][1])

    def test_quantizacao_dos_objetivos(self):
        # f1 = k/17 e f2 = err/690 com k/err INTEIROS — a estrutura MEDIDA.
        for f in [self.r["FA"]] + list(self.r["FB"]):
            self.assertLessEqual(abs(f[0] * 17 - round(f[0] * 17)), 1e-9, f)
            self.assertLessEqual(abs(f[1] * 690 - round(f[1] * 690)), 1e-9, f)

    def test_contador_de_chamadas(self):
        self.assertEqual(self.r["chamadas"], 3)            # 1 + lote de 2

    def test_controle_negativo_teto_600(self):
        self.assertEqual(self.r["guard_id"], "DDMOP7:TetoPCode")

    def test_reset_e_reinit(self):
        self.assertEqual(self.r["chamadas_pos_reset"], 0)
        # pós-reset o init re-arma e o valor é o MESMO (determinismo do .p,
        # medido também cruzando processos/sessões).
        FA, FA2 = self.r["FA"], self.r["FA2"]
        self.assertLessEqual(abs(FA[0] - FA2[0]), 1e-12)
        self.assertLessEqual(abs(FA[1] - FA2[1]), 1e-12)


# ═══════════════════════════════════════════════════════════════════════════
#  3 · FONTE ÚNICA — o ⑤ declarado vem do src/experiment.py
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(MATLAB, "MATLAB ausente nesta máquina")
class TestSondaBlocoDeclarado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = (
            "addpath('%s');\n"
            "r = struct();\n"
            "try\n"
            "    [b, ap] = sonda_bloco_declarado('DDMOP7');\n"
            "    r.aplica_ddmop7 = ap; r.bloco = b;\n"
            "    [~, ap2] = sonda_bloco_declarado('MMF1');\n"
            "    r.aplica_mmf1 = ap2;\n"
            "    r.erro = \"\";\n"
            "catch ME\n"
            "    r.erro = string(ME.identifier) + \": \" + string(ME.message);\n"
            "end\n"
            "disp(\"<<<\" + string(jsonencode(r)) + \">>>\");\n"
            % os.path.join(_RAIZ, "src"))
        cls.r = _roda_matlab(script)

    def test_sem_erro(self):
        self.assertEqual(self.r["erro"], "", self.r)

    def test_aplica_so_ao_problema_declarado(self):
        self.assertTrue(self.r["aplica_ddmop7"])
        self.assertFalse(self.r["aplica_mmf1"])

    def test_bloco_campo_a_campo_igual_a_fonte_unica(self):
        from src.experiment import SONDA_AUSENTE_INFO
        b = self.r["bloco"]
        self.assertEqual(set(b), set(SONDA_AUSENTE_INFO))
        for k, v in SONDA_AUSENTE_INFO.items():
            self.assertEqual(b[k], v, f"campo {k!r} divergiu da fonte única")


if __name__ == "__main__":
    unittest.main()
