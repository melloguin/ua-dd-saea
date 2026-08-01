# -*- coding: utf-8 -*-
"""T14.4 / BL-17 — o G-7 passa a vigiar a linha dos PISOS do CONTRATO §6.1.

**O defeito.** O `contrato_61.json` declara, no próprio `_meta`, que foi
construído por *"extração automática dos identificadores em crase"* da tabela
§6.1. Na linha dos pisos só `n_front1` e `f_best[]` estavam em crase — `ideal`,
`nadir_pop` e `nadir_front1` aparecem em PROSA. Resultado: os 3 campos que o
§6.1 exige "por geração" ficaram FORA da vigilância nos 4 pisos online.

**A prova por mutante** (relatada na F5 e reproduzida aqui): removendo os 3 de
um ⑥ de smoke, o G-7 seguia VERDE relatando *"⑥ 3/3 campos"*. Hoje ele REPROVA.

**Por que agora e não depois do disparo.** Os campos EXISTEM: medido em
2026-08-01 sobre as 112 células de piso da s42, **1.840/1.840 eventos `_gen`**
com os 3 preenchidos, ZERO ausências ⇒ ligar a vigilância não produz
falso-vermelho. O que ela impede é a perda SILENCIOSA em 30 sementes, que
apagaria as bases de §P5 (787 medições) e §P6 (376) sem acender gate nenhum —
e aí seria irrecuperável.

**A raiz também foi fechada** (lição "corrigir o gerador, não o gerado"): os 3
nomes entraram em crase no §6.1, então a próxima extração automática os pega.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)
sys.path.insert(0, os.path.join(_RAIZ, "scripts"))

import gates_proveniencia as G                        # noqa: E402

PISOS = ("nsga2", "nsga3", "moead", "smsemoa")
NOVOS = ("ideal", "nadir_pop", "nadir_front1")
ARTEFATO = os.path.join(_RAIZ, "claude_code_context", "artifacts",
                        "contrato_61.json")


def _evento(geracao: int, *, sem: tuple = ()) -> dict:
    """Um `nsga2_gen` REAL da s42 (main/nsga2/DTLZ2/0, g=1), campo a campo."""
    ev = {
        "ts": "2026-07-20T02:08:43Z", "rec": "nsga2_gen",
        "geracao": geracao, "fe": 131, "n_pop": 20, "n_front1": 20,
        "f_best": [0.00086301889, 0.00040080724, 0.00228721917],
        "ideal": [0.00086301889, 0.00040080724, 0.00228721917],
        "nadir_pop": [2.24096291, 1.97056267, 1.93421829],
        "nadir_front1": [2.24096291, 1.97056267, 1.93421829],
        "tempo_geracao_s": 0.111501625,
    }
    for k in sem:
        ev.pop(k, None)
    return ev


def _quinto() -> dict:
    """⑤ COMPLETO — o gate afere ⑥ e ⑤ juntos; aqui o alvo é o ⑥."""
    art = G._artefato("contrato_61.json")
    man = {k: f"<{k}>" for k in art["quinto_obrigatorio"]["campos"]}
    man.update({"params": {"N_efetivo": 20}, "sigma_dict": {"modelo": "piso"},
                "timing": {"tempo_total_s": 1.0}, "fe_final": 619,
                "n_geracoes": 13, "maxfe": 619})
    return man


def _sexto(dr: str, eventos: list[dict]) -> str:
    p = os.path.join(dr, "x.jsonl")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"rec": "header", "alg": "nsga2"}) + "\n")
        for ev in eventos:
            fh.write(json.dumps(ev) + "\n")
        fh.write(json.dumps({"rec": "footer", "status": "ok",
                             "fe_final": 619}) + "\n")
    return p


# ═══════════════════════════════════════════════════════════════════════════
#  O artefato — a linha dos pisos entrou na vigilância
# ═══════════════════════════════════════════════════════════════════════════

class TestArtefato(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(ARTEFATO, encoding="utf-8") as fh:
            cls.art = json.load(fh)

    def test_os_4_pisos_contratam_ideal_e_os_dois_nadir(self):
        for alg in PISOS:
            with self.subTest(alg=alg):
                di10 = self.art["configs"][alg]["di10"]
                for c in NOVOS:
                    self.assertIn(c, di10)
                # o que já havia continua lá — a linha foi ESTENDIDA, não trocada
                self.assertIn("f_best", di10)
                self.assertIn("n_front1", di10)

    def test_so_os_pisos_ONLINE_mudaram(self):
        # moead_media é "piso" na taxonomia mas segue a linha do b5 (DI-30.B3):
        # ⑥ estruturalmente idêntico ao b5m, SEM ideal/nadir por geração.
        for alg, ent in self.art["configs"].items():
            if alg in PISOS:
                continue
            with self.subTest(alg=alg):
                self.assertEqual([c for c in NOVOS if c in (ent.get("di10") or ())],
                                 [], "campo de piso vazou para outro config")

    def test_a_errata_declara_a_causa_raiz(self):
        metas = " ".join(str(v) for v in self.art["_meta"].values())
        self.assertIn("BL-17", metas)
        self.assertIn("crase", metas)

    def test_a_RAIZ_foi_fechada_no_contrato(self):
        # o artefato é GERADO por extração dos identificadores em crase: se os 3
        # nomes seguirem em prosa, a próxima regeneração desfaz este item.
        with open(os.path.join(_RAIZ, "CONTRATO_DE_DADOS.md"), encoding="utf-8") as fh:
            linha = [l for l in fh if "**pisos (5)**" in l]
        self.assertEqual(len(linha), 1)
        for c in NOVOS:
            with self.subTest(campo=c):
                self.assertIn("`%s`" % c, linha[0])


# ═══════════════════════════════════════════════════════════════════════════
#  O MUTANTE — o controle negativo que o cartão pede
# ═══════════════════════════════════════════════════════════════════════════

class TestMutanteDoSexto(unittest.TestCase):
    """Remover os 3 campos de um ⑥ de smoke: o G-7 tem de REPROVAR agora."""

    def _roda(self, sem: tuple):
        with tempfile.TemporaryDirectory() as dr:
            jp = _sexto(dr, [_evento(g, sem=sem) for g in (1, 2, 3)])
            return G.gate_contrato_61("nsga2", jp, _quinto(), modo="campanha")

    def test_o_sexto_COMPLETO_passa(self):
        ok, det = self._roda(())
        self.assertTrue(ok, det)

    def test_o_mutante_sem_ideal_REPROVA(self):
        ok, det = self._roda(("ideal",))
        self.assertFalse(ok, "o gate seguiu verde sem `ideal`: %s" % det)
        self.assertIn("ideal", det)

    def test_o_mutante_sem_os_TRES_reprova_e_nomeia_os_tres(self):
        ok, det = self._roda(NOVOS)
        self.assertFalse(ok, det)
        for c in NOVOS:
            with self.subTest(campo=c):
                self.assertIn(c, det)

    def test_cada_campo_novo_sozinho_ja_derruba_o_gate(self):
        # granularidade: nenhum dos 3 está coberto "de carona" por outro
        for c in NOVOS:
            with self.subTest(campo=c):
                ok, det = self._roda((c,))
                self.assertFalse(ok, det)

    def test_CONTROLE_o_artefato_ANTIGO_deixava_passar(self):
        """Sem esta asserção o teste acima não prova que o item mudou nada.

        Reconstrói a entrada do artefato como ela era (`["f_best","n_front1"]`)
        e alimenta o MESMO mutante: o gate tem de sair VERDE, relatando
        literalmente `⑥ 3/3 campos` — a frase que a F5 mediu.
        """
        real = G._artefato("contrato_61.json")
        antigo = json.loads(json.dumps(real))
        antigo["configs"]["nsga2"]["di10"] = ["f_best", "n_front1"]
        with mock.patch.object(
                G, "_artefato",
                side_effect=lambda n: antigo if n == "contrato_61.json"
                else real):
            with tempfile.TemporaryDirectory() as dr:
                jp = _sexto(dr, [_evento(g, sem=NOVOS) for g in (1, 2, 3)])
                ok, det = G.gate_contrato_61("nsga2", jp, _quinto(),
                                             modo="campanha")
        self.assertTrue(ok, "o mutante não reproduziu o buraco do BL-17: %s" % det)
        self.assertIn("⑥ 3/3 campos", det,
                      "o relato antigo era exatamente '⑥ 3/3 campos'")


# ═══════════════════════════════════════════════════════════════════════════
#  O corpus REAL — ligar a vigilância não acende falso-vermelho
# ═══════════════════════════════════════════════════════════════════════════

class TestCorpusRealNaoFicaVermelho(unittest.TestCase):

    def test_os_3_campos_estao_em_TODOS_os_eventos_dos_4_pisos(self):
        total = faltas = 0
        celulas = 0
        for alg in PISOS:
            for p in sorted(glob.glob(os.path.join(
                    _RAIZ, "data", "experiments", "main", alg, "*.jsonl"))):
                celulas += 1
                with open(p, "rb") as fh:
                    for raw in fh:
                        if b'_gen"' not in raw:
                            continue
                        try:
                            r = json.loads(raw.decode("utf-8", "replace"))
                        except ValueError:
                            continue
                        if not str(r.get("rec", "")).endswith("_gen"):
                            continue
                        total += 1
                        faltas += sum(1 for c in NOVOS if G._vazio(r.get(c)))
        if not celulas:
            self.skipTest("corpus de pisos ausente no disco local")
        self.assertGreater(total, 1000, "corpus raso demais p/ a asserção")
        self.assertEqual(faltas, 0,
                         "ligar a vigilância acenderia falso-vermelho no corpus")


if __name__ == "__main__":
    unittest.main()
