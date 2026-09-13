"""[G-1] O CONTROLE-POSITIVO do gate 3×1 — sintético, porque o real sumiu.

Por que este arquivo existe
---------------------------
O critério de aceitação da campanha diz: *"re-gate das 666 células ⇒ exatamente
1 quimera (c149/q10_ZDT4)"*. A quimera é o **controle-positivo** do G-1: a única
célula do corpus que o gate DEVE reprovar, e é ela que prova que o gate
discrimina.

Medição de 2026-07-30: a varredura devolve **0 quimeras**, e o gate roda a
`batch/c149/ZDT4/s42` — o arquivo existe, 17 MB — devolvendo
`G-1 3x1 = ✅ 2000/2000 bit-idênticos`. Ou seja: **o controle-positivo não está
mais no corpus que gateamos**, e sem ele não existe nenhuma evidência de que o
G-1 consiga reprovar uma quimera. Um gate sem controle-positivo é uma promessa.

O que este arquivo faz
----------------------
Constrói uma quimera **sintética** — um par ①/③ em que a ③ diz ter copiado o X
de um `solution_id` da ①, mas o X **não bate** — e exige que o G-1 REPROVE.
Mais o controle simétrico: o par coerente tem de passar. Sem os dois lados, o
teste não discrimina.

Isto NÃO substitui achar a quimera real (é item do autor, V2/T11-D2). O que ele
garante é que, quando ela aparecer, o gate saberá reconhecê-la.
"""
import os
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _gates():
    if os.path.join(_RAIZ, "scripts") not in sys.path:
        sys.path.insert(0, os.path.join(_RAIZ, "scripts"))
    if _RAIZ not in sys.path:
        sys.path.insert(0, _RAIZ)
    import gates_proveniencia
    return gates_proveniencia


def _escreve_par(dirpath, *, coerente: bool, n=64, d=3):
    """Escreve ① e ③ num tempdir. `coerente=False` ⇒ quimera sintética."""
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq

    rng = np.random.default_rng(7)
    X1 = rng.random((n, d))
    cols_x = [f"x{i}" for i in range(d)]

    primeira = {"solution_id": list(range(n))}
    for i, c in enumerate(cols_x):
        primeira[c] = X1[:, i].tolist()
    p1 = os.path.join(dirpath, "um.parquet")
    pq.write_table(pa.table(primeira), p1)

    # a ③: metade das linhas aponta um solution_id real
    marcadas = list(range(0, n, 2))
    X3 = X1[marcadas].copy()
    if not coerente:
        # a QUIMERA: o X gravado não é o X do solution_id declarado. Uma única
        # linha basta — é exatamente o defeito que o G-1 existe para pegar.
        X3[0, 0] += 0.5
    terceira = {"real_solution_id": list(marcadas)}
    for i, c in enumerate(cols_x):
        terceira[c] = X3[:, i].tolist()
    p3 = os.path.join(dirpath, "tres.parquet")
    pq.write_table(pa.table(terceira), p3)
    return p3, p1


class TestG1ControlePositivo(unittest.TestCase):

    def setUp(self):
        try:
            import numpy  # noqa: F401
            import pyarrow  # noqa: F401
        except ImportError:
            self.skipTest("numpy/pyarrow ausentes")

    def test_quimera_sintetica_e_REPROVADA(self):
        """O lado que faltava: prova que o G-1 sabe dizer NÃO."""
        G = _gates()
        with tempfile.TemporaryDirectory(prefix="g1_quimera_") as d:
            p3, p1 = _escreve_par(d, coerente=False)
            ok, det = G.gate_3x1(p3, p1)
        self.assertIs(ok, False,
                      "o G-1 NÃO reprovou uma quimera sintética — o gate não "
                      "discrimina, e o critério de aceitação '1 quimera' não "
                      "significa nada. Detalhe: %s" % det)

    def test_par_coerente_e_APROVADO(self):
        """Controle simétrico: sem ele, um gate que reprova TUDO passaria acima."""
        G = _gates()
        with tempfile.TemporaryDirectory(prefix="g1_coerente_") as d:
            p3, p1 = _escreve_par(d, coerente=True)
            ok, det = G.gate_3x1(p3, p1)
        self.assertIs(ok, True,
                      "o G-1 reprovou um par COERENTE — falso-positivo. "
                      "Detalhe: %s" % det)

    def test_parquet_ilegivel_e_INCONCLUSIVO_e_nao_derruba(self):
        """Um ③ de 0 byte derrubava a VARREDURA inteira com traceback.

        Gate que explode é pior que gate vermelho: o vermelho você vê, a
        explosão leva junto todas as células que ainda não foram gateadas.
        """
        G = _gates()
        with tempfile.TemporaryDirectory(prefix="g1_ilegivel_") as d:
            _p3, p1 = _escreve_par(d, coerente=True)
            ruim = os.path.join(d, "vazio.parquet")
            open(ruim, "wb").close()            # 0 byte
            ok, det = G.gate_3x1(ruim, p1)      # não pode levantar
        self.assertIsNone(ok, "③ ilegível tem de ser INCONCLUSIVO, não verde "
                              "nem vermelho — recebi %r (%s)" % (ok, det))
        self.assertIn("ileg", det.lower())


if __name__ == "__main__":
    unittest.main()
