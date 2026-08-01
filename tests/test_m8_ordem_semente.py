# -*- coding: utf-8 -*-
"""[M8] `LOTE_ORDEM=semente` — a fila entra SEMENTE-major, do barato ao caro.

**O problema.** O modelo de execução do M8 (autor, 2026-08-01) é: cada máquina
roda TODAS as células de uma semente antes de passar à seguinte, e DENTRO da
semente do mais barato ao mais caro (as que batem no teto de 12 h ficam por
último). Os três modos que o `lote3s.sh` tinha — `hibrida`, `barata`, `cara` —
ordenam por CUSTO primeiro; a semente é só desempate. O `hibrida`, que é o
DEFAULT, faz literalmente o oposto do pedido, e está escrito no cabeçalho do
próprio driver (item 1): *"a ordem híbrida passa a valer ENTRE sementes: tudo
que é barato (nas 3 sementes) roda antes de qualquer coisa cara"*.

**Como o teste funciona.** A ordenação vive dentro de um heredoc Python
(`PYEOF`) no meio de um script bash de 560 linhas. Em vez de copiar a lógica —
o que faria o teste passar mesmo se o driver regredisse — ele EXTRAI o bloco do
arquivo real e o executa com `argv` controlado. O `data_root` apontado é um
caminho que NÃO existe, então `estado()` devolve `ausente` para toda célula
(nenhuma é pré-filtrada) e nada é escrito em `data/`. Sem bash, sem MATLAB,
sem venv.

**Controle negativo** (doutrina T12/T14 — todo fix com um teste que reprova no
código velho): o MESMO bloco, com `ordem=hibrida`, tem de REPROVAR a asserção
de semente-major. Sem esse par, se algum dia `semente` virasse alias de
`hibrida` o teste continuaria verde por vacuidade.
"""
import os
import subprocess
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

_DRIVER = os.path.join(_RAIZ, "scripts", "lote3s.sh")

#: Pares que cobrem a faixa de custo: `nsga2` é o piso (âncora 1 s), `c238` é um
#: dos caros (14.100 s em FE=929), `e103` é offline barato. É essa mistura que
#: torna a asserção "barato antes de caro DENTRO da semente" não-trivial.
_PARES = "main/nsga2 main/c238 off/e103"
_SEEDS = "0 1 2"


def _bloco_pyeof() -> str:
    """O bloco Python REAL do driver, entre `<<'PYEOF'` e a linha `PYEOF`."""
    with open(_DRIVER, encoding="utf-8") as fh:
        linhas = fh.read().splitlines()
    try:
        ini = next(i for i, l in enumerate(linhas) if l.rstrip().endswith("<<'PYEOF'"))
        fim = next(i for i, l in enumerate(linhas) if i > ini and l.strip() == "PYEOF")
    except StopIteration:                                    # pragma: no cover
        raise AssertionError(
            "não achei o heredoc PYEOF em scripts/lote3s.sh — o driver foi "
            "reestruturado e ESTE teste precisa ser revisto junto (não o "
            "desative: ele é o que prova a ordem da campanha).")
    return "\n".join(linhas[ini + 1:fim]) + "\n"


def _roda(ordem: str, seeds: str = _SEEDS, pares: str = _PARES):
    """Executa o bloco e devolve `(rc, linhas_da_grade, stderr)`.

    `data_root` é um caminho INEXISTENTE de propósito: `estado()` devolve
    `ausente` para tudo, nenhuma célula é pré-filtrada, e o teste não pode
    tocar em `data/` nem por acidente.
    """
    with tempfile.TemporaryDirectory() as tmp:
        bloco = os.path.join(tmp, "bloco.py")
        with open(bloco, "w", encoding="utf-8") as fh:
            fh.write(_bloco_pyeof())
        censo = os.path.join(tmp, "censo.txt")
        r = subprocess.run(
            [sys.executable, bloco, _RAIZ, seeds, pares, ordem,
             "_data_root_inexistente_do_teste", "0", "nao", censo, "0"],
            capture_output=True, text=True)
    grade = []
    for ln in r.stdout.splitlines():
        t = ln.split()
        if len(t) == 6:
            grade.append({"exp": t[0], "alg": t[1], "problema": t[2],
                          "semente": t[3], "stack": t[4], "custo": float(t[5])})
    return r.returncode, grade, r.stderr


def _ranks(grade, seeds=_SEEDS):
    """A sequência de ranks de semente, na ordem em que as células entram."""
    srank = {s: i for i, s in enumerate(seeds.split())}
    return [srank[c["semente"]] for c in grade]


def _e_semente_major(grade, seeds=_SEEDS) -> bool:
    """A sequência de ranks é não-decrescente?  ⇔ a fila é semente-major."""
    r = _ranks(grade, seeds)
    return all(a <= b for a, b in zip(r, r[1:]))


class TestOrdemSemente(unittest.TestCase):
    """A ordem que o M8 vai usar."""

    @classmethod
    def setUpClass(cls):
        cls.rc, cls.grade, cls.err = _roda("semente")

    def test_a_grade_foi_montada(self):
        self.assertEqual(self.rc, 0, f"bloco falhou (rc={self.rc}): {self.err}")
        # 3 sementes × (25 nsga2 + 25 c238 + 25 e103) = 225 células.
        self.assertEqual(len(self.grade), 225,
                         f"grade com {len(self.grade)} células, esperado 225")

    def test_a_fila_e_semente_major(self):
        """TODA a semente 0 entra antes de QUALQUER célula da semente 1."""
        self.assertTrue(
            _e_semente_major(self.grade),
            "a fila NÃO é semente-major; primeiras 12 sementes na fila: "
            f"{[c['semente'] for c in self.grade[:12]]}")

    def test_dentro_da_semente_vai_do_barato_ao_caro(self):
        por_semente = {}
        for c in self.grade:
            por_semente.setdefault(c["semente"], []).append(c["custo"])
        self.assertEqual(sorted(por_semente), ["0", "1", "2"])
        for s, custos in por_semente.items():
            with self.subTest(semente=s):
                self.assertEqual(
                    custos, sorted(custos),
                    f"semente {s}: custo não-monotônico na fila (a célula de "
                    f"teto de 12 h tem de ser a ÚLTIMA da semente)")

    def test_a_ultima_celula_de_cada_semente_e_a_mais_cara(self):
        """O corolário operacional: o teto de 12 h fecha a semente, não a abre."""
        por_semente = {}
        for c in self.grade:
            por_semente.setdefault(c["semente"], []).append(c)
        for s, cels in por_semente.items():
            with self.subTest(semente=s):
                self.assertEqual(cels[-1]["custo"], max(c["custo"] for c in cels))

    def test_a_fila_e_deterministica(self):
        """Duas montagens seguidas dão a MESMA fila (desempate por exp/alg/prob).

        Sem o desempate, os 25 `nsga2` (todos com custo modelado 1 s) sairiam na
        ordem de leitura do CSV — estável na prática, mas não garantida.
        """
        _, g2, _ = _roda("semente")
        chave = lambda g: [(c["exp"], c["alg"], c["problema"], c["semente"])
                           for c in g]
        self.assertEqual(chave(self.grade), chave(g2))

    def test_cobertura_identica_a_da_hibrida(self):
        """Mudar a ORDEM não pode mudar QUAIS células rodam."""
        _, g_hib, _ = _roda("hibrida")
        conj = lambda g: sorted((c["exp"], c["alg"], c["problema"], c["semente"])
                                for c in g)
        self.assertEqual(conj(self.grade), conj(g_hib))


class TestControleNegativo(unittest.TestCase):
    """O par que impede o teste acima de passar por vacuidade."""

    def test_hibrida_NAO_e_semente_major(self):
        """O default de hoje reprova a asserção — é por isso que o modo novo existe.

        Se este teste começar a FALHAR, `hibrida` virou semente-major: ou alguém
        trocou o default (mudança de comportamento da campanha inteira, D81) ou
        o modo novo virou alias do antigo. Nos dois casos, PARE.
        """
        rc, grade, err = _roda("hibrida")
        self.assertEqual(rc, 0, f"bloco falhou (rc={rc}): {err}")
        self.assertFalse(
            _e_semente_major(grade),
            "`hibrida` saiu semente-major — o controle negativo perdeu o "
            "sentido e o teste de cima passou por vacuidade.")

    def test_barata_NAO_e_semente_major(self):
        rc, grade, _ = _roda("barata")
        self.assertEqual(rc, 0)
        self.assertFalse(_e_semente_major(grade))


class TestOrdemInvalidaParaELoga(unittest.TestCase):
    """D81: valor fora do vocabulário não pode virar `hibrida` em silêncio."""

    def test_ordem_desconhecida_sai_com_erro(self):
        rc, grade, err = _roda("sementes")          # plural — o typo provável
        self.assertEqual(rc, 4, "ordem inválida devia sair 4, saiu %d" % rc)
        self.assertIn("ORDEM_INVALIDA", err)
        self.assertEqual(grade, [], "nada pode ser emitido com ordem inválida")

    def test_os_quatro_modos_do_cabecalho_sao_aceitos(self):
        """O vocabulário documentado e o implementado não podem divergir."""
        with open(_DRIVER, encoding="utf-8") as fh:
            doc = fh.read()
        self.assertIn("LOTE_ORDEM=hibrida|barata|cara|semente", doc)
        for modo in ("hibrida", "barata", "cara", "semente"):
            with self.subTest(modo=modo):
                rc, grade, err = _roda(modo)
                self.assertEqual(rc, 0, f"modo {modo} falhou: {err}")
                self.assertEqual(len(grade), 225)


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
