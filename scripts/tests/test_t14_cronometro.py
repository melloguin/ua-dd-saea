# -*- coding: utf-8 -*-
"""T14.1 / BL-11 — o cronômetro: o I/O do checkpoint sai do tempo de busca.

**O defeito.** `tempo_busca_s`/`tempo_geracao_s` medem o ALGORITMO. O checkpoint
atômico (DI-43) é instrumentação DESTA campanha — a mesma natureza da sonda, que
a DI-13.10 já manda excluir. Enquanto o custo dele ficava dentro do relógio da
busca (ou, pior, em lugar NENHUM), a curva de escalabilidade e o ranking de custo
entre configs viajavam contaminados por 30 sementes. Timing é resultado de 1ª
classe (§17.6/D50).

**O que a auditoria dos 8 runners com checkpoint achou** (não é o que o cartão
supunha — "o padrão é o mesmo nos 8"):

* **7 runners** (c262, c154, c122, c149, e81, c311, sobol_batch) já chamavam
  `talvez_gravar` DEPOIS de a ④ da geração fechar ⇒ o I/O caía no vão ENTRE
  gerações: fora de `tempo_geracao_s`, mas **sem nome** — o buraco entre
  Σ`tempo_geracao_s` e `tempo_total_s` não era atribuível. Medido em célula real
  (`batch/sobol_batch/MMF1`, cadência 1): **4,15 s de checkpoint num run de
  5,72 s = 72,6% do wall**, contra Σ`tempo_geracao_s` = 0,109 s.
* **1 runner — `treed_media`** — contaminava de fato: a ④ dele é 1 linha só e
  fecha DEPOIS do laço inteiro, então `t_busca_total` engolia todos os
  checkpoints.

**Os controles negativos** (célula REAL, os dois):
1. `TestCelulaRealSobolBatch` — env-main. Mesma célula com checkpoint FORÇADO
   (cadência 1) × DESLIGADO.
2. `TestCelulaRealTreedMedia` — env_c311 (precisa de GPy). O controle que o
   cartão pede ao pé da letra, no runner que de fato inflava.

Tudo em tempdir (B-13/G-8).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

from src import checkpoint as C                      # noqa: E402
from src import export as _export                    # noqa: E402
from src import naming                               # noqa: E402

try:
    import numpy as np
    import pyarrow.parquet as pq
    _TEM_ARROW = True
except ImportError:                                  # pragma: no cover
    _TEM_ARROW = False


def _vendor_c311_ok() -> bool:
    """Probe LEVE do vendor do c311/treed_media (GPy) — só existe no env_c311."""
    try:
        import GPy                                   # noqa: F401
        return True
    except Exception:
        return False


#: Fração da contaminação REMOVIDA que a diferença residual entre os dois runs
#: ainda pode ocupar. Não é tolerância de igualdade numérica (dois runs de
#: wall-clock nunca são iguais): é a pergunta certa — "o que sobrou de diferença
#: é uma fração pequena do que o instrumento custou?". Medido: 2,2% no
#: treed_media, ordens de grandeza abaixo no sobol_batch.
TOL_FRACAO_DO_CKPT = 0.25


# ═══════════════════════════════════════════════════════════════════════════
#  A primitiva — src/checkpoint.py
# ═══════════════════════════════════════════════════════════════════════════

class TestPrimitivaConsumirTempo(unittest.TestCase):
    """`consumir_tempo_s()` é a fonte comum do fix (os 8 runners a usam)."""

    def _ck(self, **kw):
        return C.Checkpointer("main", "c262", "ZDT1", 0, D=2, M=2,
                              data_root="/tmp/nao-usado", **kw)

    def test_zero_quando_nada_foi_gravado(self):
        # 0.0 = "faz checkpoint e não gravou" — DIFERENTE de NULL ("não faz").
        ck = self._ck()
        self.assertEqual(ck.consumir_tempo_s(), 0.0)

    def test_devolve_o_incremento_e_zera_o_ponteiro(self):
        ck = self._ck()
        ck.tempo_total_s = 1.5                      # simula 1 gravação
        self.assertAlmostEqual(ck.consumir_tempo_s(), 1.5)
        self.assertEqual(ck.consumir_tempo_s(), 0.0, "não zerou o ponteiro")
        ck.tempo_total_s += 0.25                    # simula outra
        self.assertAlmostEqual(ck.consumir_tempo_s(), 0.25)

    def test_o_acumulador_do_run_NUNCA_e_zerado(self):
        # o ⑤ publica o AGREGADO do run: consumir por geração não pode gastá-lo
        ck = self._ck()
        ck.tempo_total_s = 2.0
        ck.consumir_tempo_s()
        self.assertEqual(ck.tempo_total_s, 2.0)

    def test_a_soma_dos_pedacos_e_o_agregado(self):
        # o invariante que a R4 usa: Σ④ tempo_checkpoint_s == ⑤ tempo_checkpoint_s
        ck, pedacos = self._ck(), []
        for dt in (0.1, 0.0, 0.4, 0.25):
            ck.tempo_total_s += dt
            pedacos.append(ck.consumir_tempo_s())
        self.assertAlmostEqual(sum(pedacos), ck.tempo_total_s)


# ═══════════════════════════════════════════════════════════════════════════
#  O campo — ④ (parquet) e ⑤ (manifesto)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_TEM_ARROW, "pyarrow/numpy ausentes")
class TestCampoNaQuartaCamada(unittest.TestCase):

    def test_schema_tem_a_coluna_nullable_float32(self):
        campo = _export.timing_schema().field("tempo_checkpoint_s")
        self.assertEqual(str(campo.type), "float")
        # NULLABLE por contrato cross-stack: o writer MATLAB (13 configs) não
        # tem checkpoint e não escreve a coluna — NULL é "não se aplica".
        self.assertTrue(campo.nullable)

    def test_ausente_vira_NULL_e_presente_vira_VALOR(self):
        with tempfile.TemporaryDirectory() as dr:
            args = ("main", "nsga2", "ZDT1", 0)
            _export.write_timing(*args, [
                {"geracao": 1, "n_acumulado": 10, "tempo_fit_s": None},
                {"geracao": 2, "n_acumulado": 20, "tempo_fit_s": None,
                 "tempo_checkpoint_s": 0.0},
                {"geracao": 3, "n_acumulado": 30, "tempo_fit_s": None,
                 "tempo_checkpoint_s": 1.25},
            ], data_root=dr)
            col = pq.read_table(
                naming.layer_path(*args, "timing", data_root=dr)
            ).column("tempo_checkpoint_s").to_pylist()
        self.assertIsNone(col[0], "config sem checkpoint tem de sair NULL")
        self.assertEqual(col[1], 0.0, "0.0 ≠ NULL: 'não gravou nesta geração'")
        self.assertAlmostEqual(col[2], 1.25, places=5)

    def test_a_quarta_antiga_sem_a_coluna_ainda_casa_no_cast(self):
        # regra da casa: coluna nova é NULLABLE, então um run PRÉ-T14 continua
        # legível pelo cast canônico da R4 (mesmo precedente do tempo_geracao_s)
        pa = _export._pa()
        antiga = pa.table({
            "run_id": pa.array(["x"], type=pa.string()),
            "geracao": pa.array([1], type=pa.int32()),
            "n_acumulado": pa.array([10], type=pa.int32()),
            "tempo_fit_s": pa.array([0.5], type=pa.float32()),
            "tempo_busca_s": pa.array([0.2], type=pa.float32()),
            "tempo_pred_sonda_s": pa.array([0.0], type=pa.float32()),
            "tempo_geracao_s": pa.array([0.7], type=pa.float32()),
        })
        t = _export.cast_completo(antiga, _export.timing_schema())
        self.assertIsNone(t.column("tempo_checkpoint_s").to_pylist()[0])


class TestCampoNoManifesto(unittest.TestCase):

    def _blk(self, **kw):
        return _export.manifest_timing_block(
            tempo_total_s=10.0, tempo_fit_surrogate_s=1.0,
            tempo_busca_s=2.0, tempo_aval_real_s=0.5, **kw)

    def test_omitido_quando_o_config_nao_faz_checkpoint(self):
        # ausência da chave = "não se aplica"; 0.0 significaria "faz e nunca gravou"
        self.assertNotIn("tempo_checkpoint_s", self._blk())

    def test_publicado_com_VALOR_quando_ha_checkpoint(self):
        self.assertEqual(
            self._blk(tempo_checkpoint_s=3.75419)["tempo_checkpoint_s"], 3.7542)

    def test_zero_explicito_e_publicado(self):
        # cadência que nunca venceu ⇒ 0.0 é MEDIDA, não ausência
        self.assertEqual(self._blk(tempo_checkpoint_s=0.0)["tempo_checkpoint_s"],
                         0.0)


# ═══════════════════════════════════════════════════════════════════════════
#  Controle negativo #1 — célula REAL em env-main (sobol_batch)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_TEM_ARROW, "pyarrow/numpy ausentes")
class TestCelulaRealSobolBatch(unittest.TestCase):
    """A MESMA célula com checkpoint FORÇADO × DESLIGADO.

    A célula é a mais barata que entrega a prova (~6 s) e é a que a bit-
    identidade do G5 já usa. Com cadência 1 o instrumento custa ~72% do wall:
    se ele vazasse para o relógio do algoritmo, vazaria de forma GRITANTE.
    """

    ALVO = ("batch", "sobol_batch", "MMF1", 0)

    def _roda(self, dr, *, com_checkpoint):
        # o DoE é artefato de ENTRADA e nunca se regenera (D63): tempdir o vê
        # por link, e o run escreve só em `<dr>/experiments/`.
        os.symlink(os.path.join(_RAIZ, "data", "doe"), os.path.join(dr, "doe"))
        from src.sobol_batch import run_sobol_batch
        if com_checkpoint:
            with mock.patch.object(C, "K_ITER_DEFAULT", 1):
                run_sobol_batch(*self.ALVO, data_root=dr, q=10)
        else:
            with mock.patch.object(C.Checkpointer, "talvez_gravar",
                                   lambda self, *a, **k: False):
                run_sobol_batch(*self.ALVO, data_root=dr, q=10)
        t = pq.read_table(naming.layer_path(*self.ALVO, "timing", data_root=dr))
        with open(naming.manifest_path(*self.ALVO, data_root=dr),
                  encoding="utf-8") as fh:
            man = json.load(fh)
        return t.to_pydict(), man["timing"]

    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            cls.sem_q, cls.sem_m = cls._roda(cls, a, com_checkpoint=False)
            cls.com_q, cls.com_m = cls._roda(cls, b, com_checkpoint=True)

    def test_o_checkpoint_realmente_rodou_no_run_com(self):
        # sem esta asserção o controle seria vazio (o instrumento podia não ter
        # rodado, e aí "tempo igual" não prova nada)
        self.assertGreater(self.com_m["tempo_checkpoint_s"], 0.0)
        self.assertEqual(self.sem_m["tempo_checkpoint_s"], 0.0)

    def test_toda_linha_da_quarta_tem_VALOR(self):
        # asserção de VALOR: config COM checkpoint não pode ter NULL na coluna
        for rot, q in (("com", self.com_q), ("sem", self.sem_q)):
            with self.subTest(run=rot):
                col = q["tempo_checkpoint_s"]
                self.assertGreater(len(col), 0)
                self.assertEqual([i for i, v in enumerate(col) if v is None], [],
                                 "linha da ④ com tempo_checkpoint_s NULL")

    def test_a_soma_da_quarta_bate_com_o_agregado_do_quinto(self):
        soma = sum(self.com_q["tempo_checkpoint_s"])
        self.assertAlmostEqual(soma, self.com_m["tempo_checkpoint_s"], places=2)

    def test_o_tempo_do_ALGORITMO_nao_mudou(self):
        # o coração do BL-11: o instrumento custou ~72% do wall e o relógio do
        # algoritmo NÃO o viu.
        ckpt = self.com_m["tempo_checkpoint_s"]
        for campo, com, sem in (
                ("tempo_busca_s", self.com_m["tempo_busca_s"],
                 self.sem_m["tempo_busca_s"]),
                ("Σ tempo_geracao_s",
                 sum(v for v in self.com_q["tempo_geracao_s"] if v is not None),
                 sum(v for v in self.sem_q["tempo_geracao_s"] if v is not None))):
            with self.subTest(campo=campo):
                self.assertLess(
                    abs(com - sem), TOL_FRACAO_DO_CKPT * ckpt,
                    f"{campo} absorveu o I/O do checkpoint: com={com:.4f} "
                    f"sem={sem:.4f} (checkpoint={ckpt:.4f})")

    def test_o_defeito_ERA_visivel_neste_arranjo(self):
        # controle do controle: reconstrói o que o código PRÉ-BL-11 teria
        # gravado (busca + I/O do checkpoint na mesma conta) e exige que ele
        # REPROVASSE a asserção acima — senão o teste passaria por vacuidade.
        ckpt = self.com_m["tempo_checkpoint_s"]
        antigo = self.com_m["tempo_busca_s"] + ckpt
        self.assertGreater(abs(antigo - self.sem_m["tempo_busca_s"]),
                           TOL_FRACAO_DO_CKPT * ckpt,
                           "o arranjo não distingue contaminado de limpo")


# ═══════════════════════════════════════════════════════════════════════════
#  Controle negativo #2 — o runner que de fato inflava (env_c311)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_TEM_ARROW and _vendor_c311_ok(),
                     "vendor c311/GPy ausente — rode no env_c311")
class TestCelulaRealTreedMedia(unittest.TestCase):
    """O controle do cartão, ao pé da letra, no `treed_media`.

    Célula: a MAIS BARATA do config (`sweep-big-mvns/ZDT4`, 5,86 s medidos na
    F5.2d) — a régua da casa é "a mais barata que entregue o mesmo poder de
    prova". `emitir_sonda=False` porque a sonda é ortogonal ao item e roda FORA
    do laço (o que se mede aqui é o laço).

    Medido nesta implementação (Mac, 2026-07-31):

    | | checkpoint OFF | cadência 1 |
    |---|---|---|
    | `tempo_busca_s` | 3,2089 | 3,2798 (+2,2%) |
    | `tempo_checkpoint_s` | 0,0 | **2,6632** |

    Pré-BL-11 o segundo teria gravado 3,2798+2,6632 = **5,943 s = +85,2%**.
    """

    EXP, ALG, PROB, SEM = "sweep-big-mvns", "treed_media", "ZDT4", 42

    def _roda(self, dr, *, com_checkpoint):
        for sub in ("datasets", "sonda"):            # offline não usa DoE
            os.symlink(os.path.join(_RAIZ, "data", sub), os.path.join(dr, sub))
        from src.treed_media import run_treed_media
        alvo = (self.EXP, self.ALG, self.PROB, self.SEM)
        if com_checkpoint:
            with mock.patch.object(C, "K_ITER_DEFAULT", 1):
                run_treed_media(*alvo, data_root=dr, emitir_sonda=False)
        else:
            with mock.patch.object(C.Checkpointer, "talvez_gravar",
                                   lambda self, *a, **k: False):
                run_treed_media(*alvo, data_root=dr, emitir_sonda=False)
        t = pq.read_table(naming.layer_path(*alvo, "timing", data_root=dr))
        with open(naming.manifest_path(*alvo, data_root=dr),
                  encoding="utf-8") as fh:
            man = json.load(fh)
        return t.to_pydict(), man["timing"]

    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            cls.sem_q, cls.sem_m = cls._roda(cls, a, com_checkpoint=False)
            cls.com_q, cls.com_m = cls._roda(cls, b, com_checkpoint=True)

    def test_o_instrumento_rodou_e_esta_declarado(self):
        self.assertGreater(self.com_m["tempo_checkpoint_s"], 0.0)
        self.assertEqual(self.sem_m["tempo_checkpoint_s"], 0.0)
        # a ④ do treed_media é 1 linha só — e ela tem de carregar o valor
        self.assertEqual(len(self.com_q["tempo_checkpoint_s"]), 1)
        self.assertAlmostEqual(self.com_q["tempo_checkpoint_s"][0],
                               self.com_m["tempo_checkpoint_s"], places=2)

    def test_tempo_busca_s_estatisticamente_igual_nos_dois(self):
        ckpt = self.com_m["tempo_checkpoint_s"]
        com, sem = self.com_m["tempo_busca_s"], self.sem_m["tempo_busca_s"]
        self.assertLess(abs(com - sem), TOL_FRACAO_DO_CKPT * ckpt,
                        f"tempo_busca_s ainda paga o checkpoint: com={com:.4f} "
                        f"sem={sem:.4f} (checkpoint={ckpt:.4f})")

    def test_tempo_geracao_s_tambem_saiu_limpo(self):
        ckpt = self.com_m["tempo_checkpoint_s"]
        com = self.com_q["tempo_geracao_s"][0]
        sem = self.sem_q["tempo_geracao_s"][0]
        self.assertLess(abs(com - sem), TOL_FRACAO_DO_CKPT * ckpt)

    def test_o_defeito_ERA_visivel_nesta_celula(self):
        # o mutante: `tempo_busca_s` como o código PRÉ-BL-11 o gravava.
        ckpt = self.com_m["tempo_checkpoint_s"]
        antigo = self.com_m["tempo_busca_s"] + ckpt
        self.assertGreater(abs(antigo - self.sem_m["tempo_busca_s"]),
                           TOL_FRACAO_DO_CKPT * ckpt,
                           "a célula não distingue contaminado de limpo — "
                           "escolha outra ou aumente a cadência")

    def test_o_wall_do_run_CONTINUA_pagando_o_checkpoint(self):
        # o instrumento sai do relógio do ALGORITMO, não do relógio de PAREDE:
        # o teto (DI-43/44) e o custo da campanha veem o wall cheio.
        self.assertGreater(self.com_m["tempo_total_s"],
                           self.sem_m["tempo_total_s"])


# ═══════════════════════════════════════════════════════════════════════════
#  A fiação nos 8 — quem publica e quem NÃO publica
# ═══════════════════════════════════════════════════════════════════════════

class TestFiacaoDosOitoRunners(unittest.TestCase):
    """Os 8 com checkpoint publicam `tempo_checkpoint_s` na ④ E no ⑤.

    Varredura ESTRUTURAL — o comportamento está provado nas células reais das
    duas classes acima (sobol_batch em env-main, treed_media em env_c311);
    rodar as 8 células custaria horas de BoTorch para provar 1 linha por runner.
    """

    COM_CHECKPOINT = ("c262_qnehvi", "c154_jes", "c122_thetadeadp",
                      "c149_lbnmobo", "e81_qpots", "c311_tgprmo",
                      "treed_media", "sobol_batch")
    SEM_CHECKPOINT = ("b5_prob", "piso_offline")

    def _src(self, nome):
        with open(os.path.join(_RAIZ, "src", f"{nome}.py"), encoding="utf-8") as fh:
            return fh.read()

    def test_os_8_publicam_na_quarta_e_no_quinto(self):
        for nome in self.COM_CHECKPOINT:
            with self.subTest(runner=nome):
                src = self._src(nome)
                self.assertIn("tempo_checkpoint_s=", src,
                              "não publica o campo na ④/⑤")
                self.assertIn("tempo_checkpoint_s=ckpt.tempo_total_s", src,
                              "o ⑤ não recebe o AGREGADO do run")

    def test_o_desconto_por_geracao_usa_a_primitiva_comum(self):
        # o fix mora na FONTE (checkpoint.consumir_tempo_s), não copiado 8×
        for nome in self.COM_CHECKPOINT:
            with self.subTest(runner=nome):
                self.assertIn("ckpt.consumir_tempo_s()", self._src(nome))

    def test_quem_nao_faz_checkpoint_nao_finge_que_faz(self):
        for nome in self.SEM_CHECKPOINT:
            with self.subTest(runner=nome):
                self.assertNotIn("tempo_checkpoint_s", self._src(nome))

    def test_treed_media_DESCONTA_e_os_outros_nao_precisam(self):
        # o treed_media é o único cuja ④ fecha DEPOIS do laço: lá o desconto é
        # explícito. Nos outros 7 o `talvez_gravar` vem DEPOIS da ④ da geração —
        # é essa ordem que os mantém limpos, e ela é o que se tranca aqui.
        self.assertIn("t_busca_total = (time.time() - t_f0) - t_ckpt",
                      self._src("treed_media"))
        for nome in ("c122_thetadeadp", "c149_lbnmobo", "sobol_batch",
                     "c311_tgprmo", "c262_qnehvi", "c154_jes"):
            with self.subTest(runner=nome):
                src = self._src(nome)
                i_timing = src.rindex("tempo_geracao_s=")
                i_ckpt = src.index("ckpt.talvez_gravar(")
                self.assertLess(
                    i_timing, i_ckpt,
                    "o `talvez_gravar` subiu para DENTRO do tempo_geracao_s — "
                    "é exatamente o defeito BL-11 voltando")


if __name__ == "__main__":
    unittest.main()
