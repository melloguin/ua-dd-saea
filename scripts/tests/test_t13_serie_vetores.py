# -*- coding: utf-8 -*-
"""[T13/BL-02b] A série do `flag_vetores_degenerados` — por GERAÇÃO, com onset.

Por que este arquivo existe
---------------------------
O T12 consertou *de onde* o campo é lido (os vetores vivem no evolver, não no
`problem`). Ficou de fora *quando* ele é lido: a coleta acontecia **uma vez**,
no replay pós-busca, sobre o estado **final** — e o mesmo valor ia carimbado nas
381 gerações. O comentário do próprio campo promete o oposto (*"mostra os
vetores encolhendo ANTES de zerar, que é onde a cadeia A8 começa"*), e sem a
série não se separa congelamento **TOTAL** de **PARCIAL**: 649 das 2.237
transições congeladas da s42 são intermitentes, e o que as distingue é o
**onset**.

A correção amostra o estado na cadência do `iterate()` — que é a cadência real
do `adapt` (`BaseEA.py:244`, chamado por `manage_preferences` no topo de cada
`iterate`) — e carimba cada geração com o estado que a governou.

Este teste tranca a **aritmética do carimbo** nos dois módulos gêmeos
(`b5_prob` e `piso_offline`), com um evolver duplo cujos vetores colapsam num
`iterate` conhecido. O controle negativo reproduz a coleta-única de ontem e
prova que ela **não** enxerga o onset.
"""
import os
import sys
import unittest

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

#: `n_gen_per_iter` do desdeo nos dois configs (Main_Execute.py:34).
GEN_POR_ITER = 10


class _RefVecs:
    def __init__(self, values):
        self.values = values


class _Pop:
    def __init__(self):
        self.individuals_archive = {"1": None}

    def avanca(self, n=GEN_POR_ITER):
        """Simula o que o `iterate()` faz ao archive: n chaves novas."""
        prox = max(int(k) for k in self.individuals_archive) + 1
        for g in range(prox, prox + n):
            self.individuals_archive[str(g)] = None


class _EvolverDuplo:
    """A forma do `BaseDecompositionEA`: vetores no evolver, archive na pop."""

    def __init__(self, n=105):
        self.reference_vectors = _RefVecs(np.ones((n, 3)) / np.sqrt(3))
        self.population = _Pop()

    def colapsa(self, quantos):
        """O que o `adapt` faz com fitness constante: zera linhas inteiras."""
        v = np.array(self.reference_vectors.values, dtype=float)
        v[:quantos] = 0.0
        self.reference_vectors.values = v


def _modulos():
    """Os dois gêmeos. `piso_offline` roda em env_b5, mas IMPORTA em qualquer um."""
    mods = []
    for nome in ("b5_prob", "piso_offline"):
        try:
            mods.append((nome, __import__("src." + nome, fromlist=[nome])))
        except Exception:                    # noqa: BLE001
            pass
    return mods


MODULOS = _modulos()


@unittest.skipUnless(MODULOS, "nenhum dos módulos b5/piso importa neste venv")
class TestSerieDosVetores(unittest.TestCase):

    def _roda(self, mod, colapso_no_iterate, n_iters=3):
        """Snapshot inicial + `n_iters` blocos; colapsa no bloco indicado.

        Devolve `(serie, geracao_do_colapso)` — a 1ª geração produzida pelo
        `iterate` em que os vetores já estavam colapsados.
        """
        ev = _EvolverDuplo()
        serie, ultima = {}, 0
        ultima = mod._registra_vetores(ev, serie, ultima)   # estado inicial
        colapsou_em = None
        for k in range(1, n_iters + 1):
            if k == colapso_no_iterate:
                ev.colapsa(14)                # o `adapt` roda no TOPO do iterate
                colapsou_em = ultima + 1
            ev.population.avanca()
            ultima = mod._registra_vetores(ev, serie, ultima)
        return serie, colapsou_em

    def test_toda_geracao_recebe_carimbo(self):
        """Buraco na série é pior que série constante: some sem avisar."""
        for nome, mod in MODULOS:
            with self.subTest(modulo=nome):
                serie, _ = self._roda(mod, colapso_no_iterate=2)
                self.assertEqual(sorted(serie), list(range(1, 1 + 1 + 3 * GEN_POR_ITER)),
                                 "a série não cobre todas as gerações")
                self.assertTrue(all(v is not None for v in serie.values()))

    def test_o_ONSET_do_colapso_aparece_na_geracao_certa(self):
        """O que a coleta-única não conseguia mostrar: QUANDO começou."""
        for nome, mod in MODULOS:
            with self.subTest(modulo=nome):
                serie, g_colapso = self._roda(mod, colapso_no_iterate=2)
                antes = [g for g in serie if g < g_colapso]
                depois = [g for g in serie if g >= g_colapso]
                self.assertTrue(antes and depois, "cenário degenerado")
                self.assertTrue(
                    all(serie[g]["n_norma_zero"] == 0 for g in antes),
                    "gerações ANTERIORES ao colapso já saem colapsadas — o "
                    "carimbo está usando o estado final")
                self.assertTrue(
                    all(serie[g]["n_norma_zero"] == 14 for g in depois),
                    "gerações POSTERIORES ao colapso não registram o colapso")

    def test_a_serie_NAO_e_constante_quando_o_estado_muda(self):
        """A asserção que o campo de ontem reprovaria em qualquer cenário."""
        for nome, mod in MODULOS:
            with self.subTest(modulo=nome):
                serie, _ = self._roda(mod, colapso_no_iterate=2)
                distintos = {v["n_norma_zero"] for v in serie.values()}
                self.assertEqual(distintos, {0, 14},
                                 "a série tem um valor só — voltou a ser o "
                                 "estado final carimbado em tudo")

    def test_CONTROLE_NEGATIVO_a_coleta_unica_nao_ve_o_onset(self):
        """Sem este controle os testes acima não provariam nada.

        Reproduz o comportamento de ontem: uma leitura só, no fim, aplicada a
        todas as gerações. Tem de perder o onset — se não perdesse, a série não
        estaria acrescentando informação nenhuma.
        """
        for nome, mod in MODULOS:
            with self.subTest(modulo=nome):
                ev = _EvolverDuplo()
                for k in range(1, 4):
                    if k == 2:
                        ev.colapsa(14)
                    ev.population.avanca()
                # a coleta de ontem: `_vetores_degenerados(evolver)` no replay
                final = mod._vetores_degenerados(ev)
                gers = [int(k) for k in ev.population.individuals_archive]
                serie_ontem = {g: final for g in gers}
                self.assertEqual(
                    {v["n_norma_zero"] for v in serie_ontem.values()}, {14},
                    "a coleta-única deixou de ser constante — o controle "
                    "perdeu o alvo")
                self.assertEqual(
                    serie_ontem[1]["n_norma_zero"], 14,
                    "a geração 1 (com vetores SADIOS) não saiu marcada como "
                    "colapsada — o defeito histórico não foi reproduzido")


if __name__ == "__main__":
    unittest.main()
