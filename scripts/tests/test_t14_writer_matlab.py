# -*- coding: utf-8 -*-
"""T14.10 / B3 — a exceção do writer ⑥ do MATLAB, FECHADA com tripwire.

**O que o B3 é.** O splice (entrelaçamento parcial de linha) do ⑥ do MATLAB está
CONFIRMADO e MEDIDO no T12 (`tests/test_t12_jsonl_matlab.py`): 4 escritores
concorrentes × 300 linhas de 6,4 KB dão **`fprintf` = 30 linhas partidas ·
`fwrite` = 26 · `java.io.FileOutputStream` (append) = 0**. O fix existe, está
medido e é 1 função.

**Por que ele NÃO foi aplicado — a exceção que este arquivo fecha.** O splice
exige **≥2 escritores no MESMO ⑥**, e o ⑥ do MATLAB tem escritor ÚNICO. Não é
promessa: é consequência mecânica de o `experiments.py` derivar o
`KNOWN_ALGORITHMS` dos loaders reais e RECUSAR na CLI qualquer config MATLAB.
Trocar o writer nos 19 sítios de 13 configs na véspera da tag custa mais do que
o risco que remove — é a recomendação do T12 §7.3, e é a que está adotada aqui.

**O que muda com este arquivo:** a exceção deixa de ser uma afirmação em prosa e
vira uma TRIPWIRE. Se algum dia o roster Python passar a despachar um config
MATLAB — o único caminho pelo qual um 2º escritor apareceria —, estes testes
ficam vermelhos e o B3 volta à mesa ANTES de a campanha gravar ⑥ spliced.

⚠ **Para o autor.** A decisão de aplicar ou não o writer Java segue sendo sua
(repasse §12.6, nunca respondida). O que está fechado aqui é a exceção COM a
guarda; o caminho pronto está em `test_t12_jsonl_matlab.py`.

Os 3 cenários que reabrem o item — e cada um tem seu teste abaixo:
  1. um config MATLAB entrar no dispatch Python;
  2. o `jsonl_open` deixar de abrir em append (`'a'`);
  3. dois processos escreverem a MESMA célula (fora do escopo mecânico daqui —
     é disciplina de operação; o `lote3s.sh` particiona por semente).
"""
from __future__ import annotations

import os
import re
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

#: Os 13 configs do stack MATLAB (`runs_matrix.csv`, coluna `stack`).
MATLAB_ALGS = frozenset({
    "b1", "b3", "b4", "c141", "c217", "c238", "e103", "e7", "e74",
    "moead", "nsga2", "nsga3", "smsemoa"})


def _experiment_m() -> str:
    with open(os.path.join(_RAIZ, "src", "experiment.m"),
              encoding="utf-8", errors="replace") as fh:
        return fh.read()


class TestRosterEhARaizDaExcecao(unittest.TestCase):
    """Cenário 1: o ⑥ do MATLAB só pode ter escritor único se o Python nunca
    despachar um config MATLAB."""

    def test_o_roster_python_e_DERIVADO_dos_loaders(self):
        # se virasse lista literal, alguém poderia acrescentar um MATLAB à mão
        import experiments
        from src import experiment as _adapter
        self.assertEqual(
            set(experiments.KNOWN_ALGORITHMS),
            {a for a in _adapter._DISPATCH_LOADERS if not a.startswith("stub")})

    def test_NENHUM_config_MATLAB_esta_no_dispatch_python(self):
        import experiments
        intruso = MATLAB_ALGS & set(experiments.KNOWN_ALGORITHMS)
        self.assertEqual(
            intruso, set(),
            "config MATLAB no dispatch Python ⇒ 2 escritores no MESMO ⑥ "
            "viram possíveis e a exceção do B3 CAIU: reabra o item "
            "(o writer Java está medido em test_t12_jsonl_matlab.py).")

    def test_a_CLI_RECUSA_um_config_MATLAB(self):
        # comportamento, não texto: o gate tem de disparar de fato
        import experiments
        for alg in sorted(MATLAB_ALGS)[:3]:
            with self.subTest(alg=alg):
                with self.assertRaises(SystemExit) as ctx:
                    experiments.main(["--algorithms", alg, "--problems", "MMF1",
                                      "--seeds", "0"])
                self.assertIn("fora do stack Python", str(ctx.exception))

    def test_o_grid_concorda_com_a_particao_de_stack(self):
        import csv
        p = os.path.join(_RAIZ, "claude_code_context", "artifacts",
                         "runs_matrix.csv")
        if not os.path.exists(p):
            self.skipTest("runs_matrix.csv ausente")
        with open(p, encoding="utf-8") as fh:
            por = {}
            for r in csv.DictReader(fh):
                por.setdefault(r["stack"], set()).add(r["alg"])
        self.assertEqual(por.get("matlab"), set(MATLAB_ALGS))
        self.assertEqual(por.get("python", set()) & MATLAB_ALGS, set())


class TestRitoDoAppendNoWriterMatlab(unittest.TestCase):
    """Cenário 2: o `jsonl_open` abre em append — o `'w'` é que perde linha."""

    def test_trunca_uma_vez_e_reabre_em_APPEND(self):
        bloco = _experiment_m()
        i = bloco.index("function fid = jsonl_open(path)")
        bloco = bloco[i:i + 1800]
        self.assertIn("fopen(path, 'w')", bloco, "o dono não trunca")
        self.assertIn("fopen(path, 'a')", bloco, "não reabriu em append (B-11)")
        self.assertLess(bloco.index("fopen(path, 'w')"),
                        bloco.index("fopen(path, 'a')"),
                        "a ordem trunca→append inverteu")

    def test_o_writer_NAO_ganhou_fflush(self):
        # `fflush` não existe no MATLAB e `jsonl_line` não tem try/catch:
        # a prescrição do BL-09 derrubaria TODO run MATLAB da campanha.
        i = _experiment_m().index("function jsonl_line(fid, rec, kv)")
        self.assertNotIn("fflush", _experiment_m()[i:i + 400])


class TestComentarioDoJsonlOpen(unittest.TestCase):
    """O item 8 do repasse: o comentário descrevia arquitetura inexistente."""

    def setUp(self):
        # o comentário é o cabeçalho da FUNÇÃO: vem DEPOIS da assinatura
        src = _experiment_m()
        i = src.index("function fid = jsonl_open(path)")
        self.bloco = src[i:src.index("ensure_dir(path);", i)]
        # o comentário quebra em linhas prefixadas por `%`: normaliza antes de
        # afirmar sobre FRASES (senão o teste vira refém da quebra de linha).
        self.plano = " ".join(
            l.lstrip("% ").strip() for l in self.bloco.splitlines())

    def test_a_arquitetura_inexistente_saiu(self):
        # a frase original, normalizada — se voltar, o teste cai
        self.assertNotIn(
            "arquivo (o footer do despachante Python, que mantem o ⑥ aberto",
            self.plano,
            "o comentário ainda descreve um co-escritor Python que não existe")

    def test_o_comentario_DIZ_por_que_a_arquitetura_nao_existe(self):
        # corrigir sem explicar deixaria a próxima sessão re-inventar a hipótese
        self.assertIn("NAO EXISTE", self.plano)
        self.assertIn("KNOWN_ALGORITHMS", self.plano)

    def test_o_motivo_MEDIDO_do_append_sobreviveu_a_correcao(self):
        # o rito do 'a' continua certo pelo 2º processo da mesma célula — e o
        # número medido é o que sustenta a regra, não a hipótese removida.
        self.assertIn("5.000 de 10.000", self.plano)
        self.assertIn("2.903 de 10.000", self.plano)
        self.assertIn("2o processo da MESMA celula", self.plano)


class TestOCaminhoDoB3ContinuaPronto(unittest.TestCase):
    """A exceção só é aceitável enquanto o fix seguir medido e à mão."""

    def test_a_medicao_do_splice_continua_na_suite(self):
        p = os.path.join(_RAIZ, "tests", "test_t12_jsonl_matlab.py")
        self.assertTrue(os.path.exists(p),
                        "a prova do B3 sumiu — a exceção perde a base")
        with open(p, encoding="utf-8") as fh:
            t = fh.read()
        self.assertIn("java.io.FileOutputStream", t)
        self.assertIn("test_a_escrita_por_java_e_atomica_sob_concorrencia", t)

    def test_os_19_sitios_de_escrita_seguem_passando_pelo_fid(self):
        # o caminho pronto (`jsonl_write(fid, linha)`) depende de o `fid`
        # continuar sendo a identidade que todo sítio passa: se alguém trocar
        # por caminho de arquivo, o fix de 1 função deixa de ser de 1 função.
        # Os sítios vivem nos `*_instrument.m` + o `jsonl_line` do experiment.m.
        import glob
        n, arquivos = 0, []
        for p in sorted(glob.glob(os.path.join(_RAIZ, "src", "*.m"))):
            with open(p, encoding="utf-8", errors="replace") as fh:
                k = len(re.findall(r"fprintf\(fid,", fh.read()))
            if k:
                n += k
                arquivos.append(os.path.basename(p))
        self.assertEqual(n, 19,
                         "os sítios de escrita do ⑥ mudaram de contagem "
                         "(%d em %r) — re-dimensione o custo do B3" % (n, arquivos))
        self.assertIn("function jsonl_line(fid, rec, kv)", _experiment_m())


if __name__ == "__main__":
    unittest.main()
