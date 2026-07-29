# -*- coding: utf-8 -*-
"""Testes do G5 — o coração da DI-43: checkpoint atômico + truncamento-com-dado.

**O problema.** As 4 camadas só nasciam no `write_run_outputs`, no FIM do run.
Um run de 8 h interrompido (spot revogada, OOM, SIGKILL, teto do orquestrador)
deixava **zero parquet** — e, com o teto de 12 h da DI-44, a doutrina passou a
ser *"curva parcial é o dado"* (DI-37.1). Sem checkpoint, a doutrina não se
sustenta: o dado não existiria no momento da morte.

**Os 3 testes que importam** (os 3 do PLANO §G5):
1. `test_checkpoint_nao_muda_o_resultado` — run completo COM e SEM checkpoint ⇒
   as 4 camadas **byte-idênticas** (o checkpoint não pode tocar a numérica).
2. `test_kill_test_*` — SIGKILL no meio ⇒ camadas parciais LEGÍVEIS + ⑤ coerente
   + `is_run_done` False; e a retomada NÃO duplica linha.
3. `test_teto_*` — o rito do teto: aborto SÓ por relógio, projeção virou aviso.

Tudo em tempdir (B-13/G-8).
"""
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

from src import checkpoint as C                    # noqa: E402
from src import manifest, naming                   # noqa: E402

try:
    import numpy as np
    import pyarrow.parquet as pq
    _TEM_ARROW = True
except ImportError:                                # pragma: no cover
    _TEM_ARROW = False

ARGS = ("main", "c262", "ZDT1", 0)


def _sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class _RegistroFalso:
    """O mínimo que `export.write_real` consome de um record do FEBudget."""

    def __init__(self, i, D=2, M=2):
        self.solution_id = i
        self.x = np.full(D, 0.1 * (i + 1), dtype=np.float64)
        self.f = np.full(M, 0.2 * (i + 1), dtype=np.float64)
        self.fe_index = i
        self.fase = "init" if i < 3 else "opt"


class _BudFalso:
    def __init__(self, n=6, maxfe=10, D=2, M=2):
        self.records = [_RegistroFalso(i, D, M) for i in range(n)]
        self.fe = n
        self.maxfe = maxfe
        self.cache_hits = 0


@unittest.skipUnless(_TEM_ARROW, "pyarrow/numpy ausentes")
class TestCheckpointGrava(unittest.TestCase):

    def _buf(self):
        from src import export as _export
        from src.standalone_harness import SnapshotBuffer
        buf = SnapshotBuffer()
        buf.add_pop(1, [0, 1, 2])
        buf.add_surrogate(_export.surrogate_row(
            1, np.array([0.1, 0.2]), regime="online", real_solution_id=None,
            mu=[0.3, 0.4], sigma=[0.01, 0.02], pred_tipo="valor",
            modelo_flag="GP", fe_treino_max=5))
        buf.add_timing(geracao=1, n_acumulado=5, tempo_fit_s=0.5)
        return buf

    def test_grava_as_4_camadas_e_um_manifesto_coerente(self):
        with tempfile.TemporaryDirectory() as dr:
            ck = C.Checkpointer(*ARGS, D=2, M=2, data_root=dr)
            self.assertTrue(ck.gravar(_BudFalso(), self._buf(), iteracao=7))
            for ly in naming.LAYERS:
                p = naming.layer_path(*ARGS, ly, data_root=dr)
                self.assertTrue(os.path.exists(p), ly)
                pq.ParquetFile(p).metadata          # footer legível
            with open(naming.manifest_path(*ARGS, data_root=dr),
                      encoding="utf-8") as fh:
                man = json.load(fh)
            # o ⑤ tem de ser HONESTO: camadas sem ⑤ são invisíveis ao censo
            # (buraco do O-21), e um ⑤ 'ok' aqui seria mentira.
            self.assertEqual(man["status"], "failed")
            self.assertEqual(man["motivo_parada"], "checkpoint_em_andamento")
            self.assertEqual(man["checkpoint"]["iteracao"], 7)
            self.assertEqual(man["fe_final"], 6)
            self.assertFalse(manifest.is_run_done(*ARGS, dr))

    def test_sem_tmp_residual(self):
        # escrita atômica (D58): tmp+rename, nunca um .tmp sobrando
        with tempfile.TemporaryDirectory() as dr:
            ck = C.Checkpointer(*ARGS, D=2, M=2, data_root=dr)
            ck.gravar(_BudFalso(), self._buf(), iteracao=1)
            d = naming.run_dir(*ARGS[:2], data_root=dr)
            self.assertEqual([f for f in os.listdir(d) if f.endswith(".tmp")], [])

    def test_o_checkpoint_seguinte_sobrescreve_o_anterior(self):
        with tempfile.TemporaryDirectory() as dr:
            ck = C.Checkpointer(*ARGS, D=2, M=2, data_root=dr)
            buf = self._buf()
            ck.gravar(_BudFalso(n=4), buf, iteracao=1)
            p1 = naming.layer_path(*ARGS, "real", data_root=dr)
            n1 = pq.ParquetFile(p1).metadata.num_rows
            ck.gravar(_BudFalso(n=6), buf, iteracao=2)
            self.assertEqual(pq.ParquetFile(p1).metadata.num_rows, 6)
            self.assertGreater(6, n1)
            # 1 arquivo por camada, sempre — nada de `.ckpt` forasteiro
            d = naming.run_dir(*ARGS[:2], data_root=dr)
            self.assertEqual(len([f for f in os.listdir(d)
                                  if f.endswith("__real.parquet")]), 1)

    def test_nunca_mata_o_run(self):
        # a rede de segurança não pode ser causa de morte (doutrina DI-42.3)
        with tempfile.TemporaryDirectory() as dr:
            from src import export as _export
            log = mock.Mock()
            ck = C.Checkpointer(*ARGS, D=2, M=2, data_root=dr, log=log)
            with mock.patch.object(_export, "write_real",
                                   side_effect=OSError("disco cheio")):
                self.assertFalse(ck.gravar(_BudFalso(), self._buf(), iteracao=1))
            self.assertEqual(log.guard.call_args[0][0], "checkpoint_falhou")
            self.assertEqual(ck.n_checkpoints, 0)

    def test_o_custo_do_instrumento_vai_para_o_sexto(self):
        with tempfile.TemporaryDirectory() as dr:
            log = mock.Mock()
            ck = C.Checkpointer(*ARGS, D=2, M=2, data_root=dr, log=log)
            ck.gravar(_BudFalso(), self._buf(), iteracao=3)
            nome, campos = log.event.call_args[0][0], log.event.call_args[1]
            self.assertEqual(nome, "checkpoint")
            self.assertIn("tempo_checkpoint_s", campos)
            self.assertEqual(campos["iteracao"], 3)
            self.assertEqual(ck.resumo()["n_checkpoints"], 1)


class TestCadencia(unittest.TestCase):
    """DI-43: 25 iterações OU 30 min — o que vier primeiro."""

    def _ck(self, **kw):
        return C.Checkpointer(*ARGS, D=2, M=2, data_root="/tmp/nao-usado", **kw)

    def test_por_iteracoes(self):
        ck = self._ck()
        self.assertEqual(ck.k_iter, 25)
        self.assertFalse(ck.devido(24))
        self.assertTrue(ck.devido(25))

    def test_por_tempo_mesmo_sem_iteracoes(self):
        # o caso do c154/c262: iteração de ~45 min. Esperar 25 delas seria
        # esperar 18 h — o critério de TEMPO é o que salva esses runs.
        ck = self._ck()
        self.assertEqual(ck.intervalo_s, 1800.0)
        self.assertFalse(ck.devido(1))
        self.assertTrue(ck.devido(1, agora=time.time() + 1801))

    def test_desligado_nunca_e_devido(self):
        self.assertFalse(self._ck(ativo=False).devido(10_000))

    def test_defaults_lidos_em_runtime(self):
        with mock.patch.object(C, "K_ITER_DEFAULT", 1):
            self.assertEqual(self._ck().k_iter, 1)


@unittest.skipUnless(_TEM_ARROW, "pyarrow/numpy ausentes")
class TestBitIdentidade(unittest.TestCase):
    """PROVA OBRIGATÓRIA: o checkpoint não muda o resultado final.

    Molde `scripts/regressao_q1.py`: ①②③④ byte-idênticas antes×depois. Aqui o
    "antes" é o run com o checkpoint DESLIGADO e o "depois" é com ele em cadência
    1 (grava a cada geração) — se o checkpoint tocasse o buffer, o orçamento ou o
    RNG, o hash mudaria.
    """

    ALVO = ("batch", "sobol_batch", "MMF1", 0)

    def _roda(self, dr, *, com_checkpoint):
        # o DoE é artefato de ENTRADA e nunca se regenera (D63): o tempdir o vê
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
        # ①②③ BIT-A-BIT; ④ ESTRUTURAL — a regra do molde
        # `scripts/regressao_q1.py:69` (as colunas `tempo_*` da ④ são wall-clock
        # MEDIDO e variam entre duas execuções por natureza, com ou sem
        # checkpoint; o que tem de casar são `geracao`/`n_acumulado`/`run_id`).
        out = {ly: _sha(naming.layer_path(*self.ALVO, ly, data_root=dr))
               for ly in ("real", "pop", "surrogate")}
        t = pq.read_table(naming.layer_path(*self.ALVO, "timing", data_root=dr))
        cols = [c for c in ("run_id", "geracao", "n_acumulado") if c in t.column_names]
        out["timing_estrutural"] = t.select(cols).to_pydict()
        out["timing_fit_nulo"] = t.column("tempo_fit_s").is_null().to_pylist() \
            if "tempo_fit_s" in t.column_names else None
        return out

    def test_checkpoint_nao_muda_o_resultado(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            sem = self._roda(a, com_checkpoint=False)
            com = self._roda(b, com_checkpoint=True)
        for chave in sem:
            with self.subTest(camada=chave):
                self.assertEqual(sem[chave], com[chave],
                                 f"o checkpoint mudou a camada {chave}")

    def test_o_checkpoint_realmente_rodou_no_run_com(self):
        # controle: sem esta asserção o teste acima passaria com o checkpoint
        # nunca sendo chamado.
        with tempfile.TemporaryDirectory() as dr:
            os.symlink(os.path.join(_RAIZ, "data", "doe"),
                       os.path.join(dr, "doe"))
            with mock.patch.object(C, "K_ITER_DEFAULT", 1), \
                 mock.patch.object(C.Checkpointer, "gravar",
                                   autospec=True, return_value=True) as gv:
                from src.sobol_batch import run_sobol_batch
                run_sobol_batch(*self.ALVO, data_root=dr, q=10)
            self.assertGreater(gv.call_count, 5)


@unittest.skipUnless(_TEM_ARROW, "pyarrow/numpy ausentes")
class TestKillTest(unittest.TestCase):
    """SIGKILL no meio ⇒ camadas parciais legíveis + ⑤ coerente + sem duplicata.

    O alvo é o MECANISMO (Checkpointer + FEBudget + SnapshotBuffer + os writers
    reais), não um algoritmo específico: um runner real do roster fecha em
    segundos e não daria janela para o SIGKILL — e o que o kill-test tem de
    provar é o rito de escrita, que é comum aos 7 runners com checkpoint.
    """

    FILHO = '''
import os, sys, time
sys.path.insert(0, %r)
import numpy as np
import src.checkpoint as C
C.K_ITER_DEFAULT = 1                       # checkpoint a cada iteração
from src import problems
from src import standalone_harness as H
from src.standalone_harness import SnapshotBuffer
from src.budget import FEBudget

dr = sys.argv[1]
prob = H._instantiate("MMF1")
D, M = int(prob.n_var), int(prob.n_obj)
def true_f(x):
    F = problems.evaluate_problem(prob, np.asarray(x, dtype=np.float64).reshape(1, -1))
    return np.asarray(F, dtype=np.float64).reshape(-1)
bud = FEBudget(D=D, maxfe=10_000)
buf = SnapshotBuffer()
ck = C.Checkpointer("main", "c262", "ZDT1", 0, D=D, M=M, data_root=dr)
rng = np.random.default_rng(7)
for it in range(1, 10_000):
    x = rng.random(D)
    bud.evaluate(x, true_f)
    buf.add_pop(it, [r.solution_id for r in bud.records])
    buf.add_timing(geracao=it, n_acumulado=bud.fe, tempo_fit_s=0.001)
    ck.talvez_gravar(bud, buf, iteracao=it)
    time.sleep(0.02)                       # janela para o SIGKILL
'''

    def test_kill_test_deixa_camadas_legiveis_e_manifesto_coerente(self):
        with tempfile.TemporaryDirectory() as dr:
            drv = os.path.join(dr, "filho.py")
            with open(drv, "w", encoding="utf-8") as fh:
                fh.write(self.FILHO % _RAIZ)
            pr = subprocess.Popen([sys.executable, drv, dr],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            mp = naming.manifest_path(*ARGS, data_root=dr)
            try:
                for _ in range(400):        # espera o 1º checkpoint (≤ 8 s)
                    if os.path.exists(mp):
                        break
                    time.sleep(0.02)
                time.sleep(0.3)             # deixa acumular algumas iterações
                self.assertTrue(os.path.exists(mp), "nenhum checkpoint saiu")
                os.kill(pr.pid, signal.SIGKILL)     # morte MATADA, sem finally
            finally:
                _, err = pr.communicate(timeout=30)
            self.assertEqual(pr.returncode, -signal.SIGKILL, err.decode()[-800:])

            # (1) camadas parciais LEGÍVEIS
            n_real = None
            for ly in naming.LAYERS:
                p = naming.layer_path(*ARGS, ly, data_root=dr)
                self.assertTrue(os.path.exists(p), ly)
                md = pq.ParquetFile(p).metadata
                if ly == "real":
                    n_real = md.num_rows
            self.assertGreater(n_real, 0)
            # (2) ⑤ COERENTE com as camadas — e a coerência é DIRECIONAL.
            # As 5 escritas do checkpoint são atômicas uma a uma, não como
            # grupo: o ⑤ é o ÚLTIMO, então um SIGKILL no meio deixa as camadas
            # ATÉ 1 checkpoint à frente dele (medido: ⑤ fe_final=11, ① 12
            # linhas). `fe_final` é PISO — o que NÃO pode acontecer é o ⑤
            # prometer dado que as camadas não têm.
            with open(mp, encoding="utf-8") as fh:
                man = json.load(fh)
            self.assertEqual(man["status"], "failed")
            self.assertEqual(man["motivo_parada"], "checkpoint_em_andamento")
            self.assertLessEqual(man["fe_final"], n_real,
                                 "o ⑤ prometeu mais dado do que a ① tem")
            self.assertEqual(man["checkpoint"]["fe"], man["fe_final"])
            self.assertGreater(man["fe_final"], 0)
            # (3) a esteira NÃO lê isso como pronto
            self.assertFalse(manifest.is_run_done(*ARGS, dr))
            # (4) nenhum .tmp órfão do rename atômico
            d = naming.run_dir(*ARGS[:2], data_root=dr)
            self.assertEqual([f for f in os.listdir(d) if f.endswith(".tmp")], [])

    def test_retomada_nao_duplica(self):
        # o checkpoint reescreve a camada INTEIRA a cada vez (não faz append),
        # então a re-execução da célula não pode herdar linha nenhuma.
        with tempfile.TemporaryDirectory() as dr:
            from src.standalone_harness import SnapshotBuffer
            ck = C.Checkpointer(*ARGS, D=2, M=2, data_root=dr)
            buf = SnapshotBuffer()
            buf.add_pop(1, [0, 1])
            ck.gravar(_BudFalso(n=6), buf, iteracao=1)
            p = naming.layer_path(*ARGS, "real", data_root=dr)
            self.assertEqual(pq.ParquetFile(p).metadata.num_rows, 6)
            # "re-execução": novo Checkpointer, mesmo run_id, orçamento do zero
            ck2 = C.Checkpointer(*ARGS, D=2, M=2, data_root=dr)
            ck2.gravar(_BudFalso(n=4), buf, iteracao=1)
            self.assertEqual(pq.ParquetFile(p).metadata.num_rows, 4)


class TestRitoDoTeto(unittest.TestCase):
    """DI-43/44: aborta SÓ por relógio; a projeção virou AVISO."""

    def _proj(self, max_wall_s, t0):
        from src.c262_qnehvi import _WallClockProjector
        return _WallClockProjector(max_wall_s, t0, maxfe=681)

    def test_elapsed_ainda_aborta(self):
        p = self._proj(10.0, time.time() - 11)
        over, _, elapsed, crit = p.exceeded(100)
        self.assertTrue(over)
        self.assertEqual(crit, "elapsed")
        self.assertGreater(elapsed, 10)

    def test_projecao_nao_aborta_mais_e_vira_aviso(self):
        # 12 amostras caras: a projeção estoura o teto com folga...
        p = self._proj(100.0, time.time() - 1)
        for n in range(1, 13):
            p.add(n * 10, 50.0, 60.0)
        over, proj_s, _, crit = p.exceeded(100)
        self.assertFalse(over, "a projeção NÃO pode mais abortar (DI-43)")
        self.assertEqual(crit, "projecao_warning")
        self.assertGreater(proj_s, 0)

    def test_sem_teto_nao_ha_criterio(self):
        over, proj_s, _, crit = self._proj(None, time.time()).exceeded(100)
        self.assertEqual((over, proj_s, crit), (False, None, None))

    def test_o_projetor_nao_foi_deletado(self):
        # o aviso É o dado (a estimativa que explica por que a célula não fecha)
        p = self._proj(1e9, time.time())
        for n in range(1, 13):
            p.add(n * 10, 1.0, 2.0)
        self.assertIsNotNone(p.projection_s(100))

    def test_os_dois_runners_botorch_truncam_com_dado(self):
        # paridade de rito: os 2 gêmeos BoTorch fecham pelo `write_run_outputs`
        # com status failed/teto_wall em vez de `raise WallClockAbort`.
        for nome in ("c262_qnehvi", "c154_jes"):
            with self.subTest(runner=nome):
                with open(os.path.join(_RAIZ, "src", f"{nome}.py"),
                          encoding="utf-8") as fh:
                    src = fh.read()
                self.assertIn("truncou_por_teto = True", src)
                self.assertIn('log.event("teto_wall_truncamento"', src)
                self.assertIn('motivo_parada=("teto_wall" if truncou_por_teto', src)
                self.assertIn('log.event("wall_projection_warning"', src)
                # o aborto seco por projeção não existe mais
                self.assertNotIn('log.event("wall_projection_abort"', src)

    def test_os_7_runners_com_hook_tem_checkpoint(self):
        # os 3 offline DESDEO (b5r/b5m/moead_media) ficam FORA por desenho: a ③
        # deles só nasce no replay dos archives PÓS-laço, então um checkpoint no
        # meio gravaria uma ③ vazia. Eles já truncam com dado por `teto_s`.
        com = ("c262_qnehvi", "c154_jes", "c122_thetadeadp", "c149_lbnmobo",
               "e81_qpots", "c311_tgprmo", "treed_media", "sobol_batch")
        sem = ("b5_prob", "piso_offline")
        for nome in com:
            with self.subTest(runner=nome):
                with open(os.path.join(_RAIZ, "src", f"{nome}.py"),
                          encoding="utf-8") as fh:
                    src = fh.read()
                self.assertIn("_Checkpointer(", src)
                self.assertIn("ckpt.talvez_gravar(", src)
        for nome in sem:
            with self.subTest(runner=nome, esperado="sem checkpoint"):
                with open(os.path.join(_RAIZ, "src", f"{nome}.py"),
                          encoding="utf-8") as fh:
                    src = fh.read()
                self.assertNotIn("_Checkpointer(", src)
                self.assertIn('motivo_parada = "failed", "teto_wall"', src)


if __name__ == "__main__":
    unittest.main()
