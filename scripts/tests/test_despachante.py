# -*- coding: utf-8 -*-
"""Testes do despachante honesto — G2: B-02 · B-16 · I-10 · revogação DI-40.

A "camada de lançamento" (o fio despachante→runner) é o ponto cego clássico
deste repo: 5 bugs históricos nasceram nela (roster fantasma, kwargs não
repassados, `q` que não chegava, projetor não-batch-aware, status rebaixado).
Todo teste daqui roda em **tempdir** (B-13/G-8) e prova o FIO, não a intenção.

* **B-02** — `AuditLogger.for_run` era a 1ª linha de `_run_one`, antes de
  qualquer decisão: 22 células "pulou"/semente ⇒ ~660 células/campanha com o ⑥
  poluído por um par header+footer vazio, e a regra O-22 dando ~270 falsos
  alarmes de "morte de máquina".
* **B-16** — retry 3× de falha DETERMINÍSTICA: ~430 h-core em 30 sementes
  contra ~145 h-core com a lista (economia ~285 h-core).
* **I-10** — os 5 manifestos abortados de `batch/c262` gravaram `q=1` com
  `header.params.q=10` no ⑥ (150 células com o `q` errado no ⑤).
* **DI-40 revogada (DI-43/44)** — rodam TODAS as 695 células, INCLUSIVE as 5
  de `batch/c154`: nenhum filtro de dispatch pode excluí-las.
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

import experiments                                   # noqa: E402
from src import naming                               # noqa: E402


def _impressao(path):
    """(existe, tamanho, mtime_ns, sha256) — a assinatura que o B-02 preserva."""
    if not os.path.exists(path):
        return (False, None, None, None)
    st = os.stat(path)
    with open(path, "rb") as fh:
        return (True, st.st_size, st.st_mtime_ns, hashlib.sha256(fh.read()).hexdigest())


def _le_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


class TestNoOpNaoTocaOSexto(unittest.TestCase):
    """B-02: o caminho de skip não abre — nem cria — o ⑥ da célula."""

    ARGS = ("batch", "e81", "ZDT4", 42)

    def test_celula_pronta_nao_cria_o_sexto(self):
        with tempfile.TemporaryDirectory() as dr:
            jp = naming.jsonl_path(*self.ARGS, data_root=dr)
            with mock.patch.object(experiments, "is_run_done", return_value=True), \
                 mock.patch.object(experiments, "_adapter") as ad:
                st = experiments._run_one(*self.ARGS, dr)
            self.assertEqual(st, "skipped")
            self.assertFalse(os.path.exists(jp), "o no-op criou o ⑥")
            ad.run.assert_not_called()

    def test_celula_pronta_nao_altera_o_sexto_existente(self):
        with tempfile.TemporaryDirectory() as dr:
            jp = naming.jsonl_path(*self.ARGS, data_root=dr)
            os.makedirs(os.path.dirname(jp), exist_ok=True)
            with open(jp, "w", encoding="utf-8") as fh:
                fh.write('{"ts":"2026-07-24T09:21:00Z","rec":"header","D":30}\n')
                fh.write('{"ts":"2026-07-24T12:00:00Z","rec":"footer",'
                         '"status":"ok","fe_final":2109}\n')
            antes = _impressao(jp)
            with mock.patch.object(experiments, "is_run_done", return_value=True):
                st = experiments._run_one(*self.ARGS, dr)
            self.assertEqual(st, "skipped")
            self.assertEqual(_impressao(jp), antes)   # tamanho + mtime + sha256

    def test_controle_negativo_celula_nao_pronta_escreve_o_sexto(self):
        # sem o controle, o teste acima passaria mesmo com o ⑥ nunca sendo aberto
        with tempfile.TemporaryDirectory() as dr:
            jp = naming.jsonl_path(*self.ARGS, data_root=dr)
            with mock.patch.object(experiments, "is_run_done", return_value=False), \
                 mock.patch.object(experiments, "_adapter"):
                st = experiments._run_one(*self.ARGS, dr)
            self.assertEqual(st, "ok")
            self.assertEqual([r["rec"] for r in _le_jsonl(jp)], ["header", "footer"])

    def test_stage_grid_nao_paga_is_run_done_duas_vezes(self):
        # a esteira já filtrou: repetir a consulta custa uma LISTAGEM DE BUCKET
        # por célula nos 5 bucket-only (D58).
        with tempfile.TemporaryDirectory() as dr:
            with mock.patch.object(experiments, "is_run_done",
                                   return_value=False) as done, \
                 mock.patch.object(experiments, "_run_one",
                                   return_value="ok") as um:
                experiments._stage_grid([("e81", "ZDT4", 42)], "batch", dr,
                                        n_jobs=1, force=False, modo_rapido=False,
                                        sb=experiments.Scoreboard())
            self.assertEqual(done.call_count, 1)
            self.assertIs(um.call_args[1]["checar_pronto"], False)


class TestNoRetryDeterminista(unittest.TestCase):
    """B-16: exceção da lista ⇒ 0 retries; transitória ⇒ as 3 tentativas."""

    #: as 3 falhas determinísticas MEDIDAS na rodada-42, com a mensagem real
    CASOS = (
        # main/b1/DTLZ4 — falhou idêntico em vm3 Linux/Intel e Mac arm64
        ("least squares problem is underdetermined",
         ValueError("least squares problem is underdetermined")),
        # main/c154/{ZDT6 it 62, BBOB_F55 it 55}
        ("random_search_optimizer falhou nas 3 tentativas",
         RuntimeError("rota (a): random_search_optimizer falhou nas 3 "
                      "tentativas da escada p/ a amostra 2")),
        # main/c262/WFG1 — it 41, n_train=281 (fe 281/681)
        ("ModelFittingError: All attempts to fit",
         RuntimeError("ModelFittingError: All attempts to fit the model "
                      "have failed")),
    )

    def _roda(self, exc, dr, alg="c154", problema="ZDT6"):
        with mock.patch.object(experiments, "_adapter") as ad, \
             mock.patch.object(experiments, "RETRY_BACKOFF_S", 0):
            ad.run.side_effect = exc
            st = experiments._run_one("main", alg, problema, 42, dr,
                                      checar_pronto=False)
        return st, ad.run.call_count

    def test_falha_determinista_nao_retria(self):
        for padrao, exc in self.CASOS:
            with self.subTest(padrao=padrao), tempfile.TemporaryDirectory() as dr:
                st, n = self._roda(exc, dr)
                self.assertEqual(st, "failed")
                self.assertEqual(n, 1, f"{padrao}: {n} tentativas (esperado 1)")
                recs = _le_jsonl(naming.jsonl_path("main", "c154", "ZDT6", 42,
                                                   data_root=dr))
                guardas = [r for r in recs
                           if r.get("name") == "determinista_nao_retriavel"]
                self.assertEqual(len(guardas), 1)
                self.assertEqual(guardas[0]["padrao"], padrao)
                self.assertEqual([r["rec"] for r in recs if r["rec"] == "retry"], [])
                with open(naming.manifest_path("main", "c154", "ZDT6", 42,
                                              data_root=dr), encoding="utf-8") as fh:
                    man = json.load(fh)
                self.assertEqual(man["n_retries"], 0)
                self.assertEqual(man["status"], "failed")

    def test_falha_transitoria_ainda_retria_3x(self):
        # licença MATLAB contendida / I/O / OOM momentâneo: é PARA isto que o
        # retry existe (DI-06 item 1) — a lista não pode capturá-los.
        with tempfile.TemporaryDirectory() as dr:
            st, n = self._roda(OSError("Resource temporarily unavailable"), dr)
            self.assertEqual(st, "failed")
            self.assertEqual(n, experiments.RETRY_ATTEMPTS)
            recs = _le_jsonl(naming.jsonl_path("main", "c154", "ZDT6", 42,
                                               data_root=dr))
            self.assertEqual(len([r for r in recs if r["rec"] == "retry"]),
                             experiments.RETRY_ATTEMPTS - 1)

    def test_erro_de_preparacao_segue_nao_retriavel(self):
        # regressão do comportamento antigo (M7): artefato ausente não é
        # transitório — DoE/dataset/sonda faltando corta na hora.
        with tempfile.TemporaryDirectory() as dr:
            st, n = self._roda(FileNotFoundError("data/doe/ZDT6/doe_ZDT6_42.npy"), dr)
            self.assertEqual((st, n), ("failed", 1))

    def test_a_lista_e_a_do_plano(self):
        self.assertEqual(experiments.NO_RETRY_SUBSTRINGS,
                         tuple(p for p, _ in self.CASOS))


class TestManifestoDoAbortoCarregaACelula(unittest.TestCase):
    """I-10: o ⑤ do aborto grava a CÉLULA do grid (q, tier, dist, regime)."""

    def _aborta(self, exp, alg, problema, dr):
        with mock.patch.object(experiments, "_adapter") as ad, \
             mock.patch.object(experiments, "RETRY_BACKOFF_S", 0):
            ad.run.side_effect = RuntimeError("ModelFittingError: All attempts to fit")
            experiments._run_one(exp, alg, problema, 42, dr, checar_pronto=False)
        with open(naming.manifest_path(exp, alg, problema, 42, data_root=dr),
                  encoding="utf-8") as fh:
            return json.load(fh)

    def test_aborto_no_batch_grava_q_10(self):
        with tempfile.TemporaryDirectory() as dr:
            man = self._aborta("batch", "c262", "ZDT4", dr)
            self.assertEqual(man["q"], 10)          # era 1 nos 5 de batch/c262
            self.assertEqual(man["status"], "failed")

    def test_aborto_no_main_segue_q_1(self):
        with tempfile.TemporaryDirectory() as dr:
            self.assertEqual(self._aborta("main", "c262", "ZDT4", dr)["q"], 1)

    def test_aborto_no_sweep_grava_tier_e_dist(self):
        with tempfile.TemporaryDirectory() as dr:
            man = self._aborta("sweep-medium-mvns", "c311", "WFG9", dr)
            self.assertEqual((man["tier"], man["dist"]), ("medium", "mvns"))
            self.assertEqual(man["regime"], "offline")

    def test_aborto_online_declara_regime_online(self):
        with tempfile.TemporaryDirectory() as dr:
            self.assertEqual(self._aborta("main", "c149", "ZDT4", dr)["regime"],
                             "online")


class TestRevogacaoDI40(unittest.TestCase):
    """DI-43/44: roster 100% — `batch/c154` volta e nada no dispatch o exclui."""

    def test_c154_no_batch_e_despachado(self):
        with tempfile.TemporaryDirectory() as dr:
            with mock.patch.object(experiments, "_run_one",
                                   return_value="ok") as um:
                experiments.main(["--exp", "batch", "--algorithms", "c154",
                                  "--problems", "ZDT4", "--seeds", "42",
                                  "--data-root", dr, "--no-consolidate"])
            self.assertEqual(um.call_count, 1)
            self.assertEqual(um.call_args[0][:4], ("batch", "c154", "ZDT4", 42))

    def test_c154_esta_no_roster_do_batch_da_matrix(self):
        import csv
        p = os.path.join(_RAIZ, "claude_code_context", "artifacts",
                         "runs_matrix.csv")
        with open(p, encoding="utf-8") as fh:
            linhas = [r for r in csv.DictReader(fh)
                      if r["exp"] == "batch" and r["alg"] == "c154"]
        self.assertEqual(len(linhas), 150)          # 5 problemas × 30 sementes
        self.assertEqual({r["q"] for r in linhas}, {"10"})


if __name__ == "__main__":
    unittest.main()
