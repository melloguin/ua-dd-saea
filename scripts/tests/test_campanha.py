# -*- coding: utf-8 -*-
"""Testes da identidade de campanha — G3: B-03 · OP-6 · fallback-footer (O-21/E-04).

* **B-03** — `is_run_done` não tinha noção de CAMPANHA: as células stale de
  semente **0** (b1 DTLZ2/ZDT1, c238 ZDT1, c262 ZDT1, c154 DTLZ2, todas
  pré-retrofit) eram absorvidas como prontas — e a semente 0 é uma das 30.
  Medido na rodada-42: 22 células "pulou" únicas nos `done.txt`, 9 delas ZDT4.
  Sem o carimbo, ~660 células/campanha entram como pré-campanha.
* **OP-6** — `--force` re-rodava POR CIMA: camadas de uma execução + ⑤ de outra
  é a mecânica exata da quimera `batch/c149/q10_ZDT4`.
* **O-21/E-04** — o stack MATLAB certifica a própria falha no FOOTER do ⑥
  (`main/b1/DTLZ4`: `least squares problem is underdetermined` só existe lá);
  quem olha só o ⑤ declara SEM-MANIFESTO e perde o diagnóstico.

Stdlib puro, tudo em tempdir (B-13/G-8).
"""
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

import experiments                                   # noqa: E402
from src import manifest, naming                     # noqa: E402

ARGS = ("main", "c262", "ZDT1", 0)


def _mini_celula(dr, *, args=ARGS, campanha_id=None, status="ok", com_final=False):
    """Manifesto + as camadas (arquivos vazios: o teste não afere footer)."""
    for ly in naming.LAYERS + ((naming.FINAL_LAYER,) if com_final else ()):
        p = naming.layer_path(*args, ly, data_root=dr)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").close()
    man = manifest.new_manifest(*args, status=status, maxfe=929, fe_final=929,
                                campanha_id=campanha_id, data_root=dr)
    manifest.write_manifest(man, dr)
    return man


def _pronto(dr, **kw):
    return manifest.is_run_done(*ARGS, dr, check_footers=False, **kw)


class TestCarimboDeCampanha(unittest.TestCase):
    """B-03: o ⑤ nasce v2 e o resume exige a campanha CORRENTE."""

    def test_manifesto_novo_nasce_v2_com_carimbo(self):
        with tempfile.TemporaryDirectory() as dr:
            man = _mini_celula(dr)
            self.assertEqual(man["schema_version"], 2)
            self.assertEqual(man["campanha_id"], manifest.campanha_id_corrente())
            self.assertTrue(_pronto(dr))                      # controle positivo

    def test_manifesto_v1_sem_campo_nao_esta_pronto(self):
        # o comportamento DESEJADO: força o re-run das stale (as de semente 0)
        with tempfile.TemporaryDirectory() as dr:
            man = _mini_celula(dr)
            man.pop("campanha_id")
            man["schema_version"] = 1
            manifest.write_manifest(man, dr)
            self.assertFalse(_pronto(dr))

    def test_campanha_anterior_nao_esta_pronto(self):
        with tempfile.TemporaryDirectory() as dr:
            _mini_celula(dr, campanha_id="0bdd23512ab3_2026-07-24")
            self.assertFalse(_pronto(dr))

    def test_auditoria_do_passado_com_a_sentinela(self):
        # o re-gate das 666 lê manifestos v1: exigir a campanha corrente ali
        # pintaria o grid inteiro de "não-pronto".
        with tempfile.TemporaryDirectory() as dr:
            man = _mini_celula(dr)
            man.pop("campanha_id")
            manifest.write_manifest(man, dr)
            self.assertFalse(_pronto(dr))
            self.assertTrue(_pronto(dr, campanha_id=manifest.QUALQUER_CAMPANHA))

    def test_a_env_crava_a_identidade(self):
        with mock.patch.dict(os.environ,
                             {manifest.CAMPANHA_ENV: "  m8_2026-08-01  "}):
            self.assertEqual(manifest.campanha_id_corrente(), "m8_2026-08-01")

    def test_troca_de_campanha_invalida_o_pronto(self):
        with tempfile.TemporaryDirectory() as dr:
            with mock.patch.dict(os.environ, {manifest.CAMPANHA_ENV: "m8_2026-08-01"}):
                _mini_celula(dr)
                self.assertTrue(_pronto(dr))
            with mock.patch.dict(os.environ, {manifest.CAMPANHA_ENV: "m9_2026-09-01"}):
                self.assertFalse(_pronto(dr))

    def test_default_deriva_do_commit_e_da_data(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(manifest.CAMPANHA_ENV, None)
            cid = manifest.campanha_id_corrente()
        self.assertRegex(cid, r"^(?:[0-9a-f]{12}|sem-git)_\d{4}-\d{2}-\d{2}$")

    def test_writer_matlab_usa_a_mesma_fonte(self):
        # paridade de fonte: se um stack derivar o id de outro lugar, metade do
        # grid (345 células/semente) fica fora da campanha corrente.
        with open(os.path.join(_RAIZ, "src", "experiment.m"),
                  encoding="utf-8", errors="replace") as fh:
            m = fh.read()
        self.assertIn("man.schema_version = 2;", m)
        self.assertIn("man.campanha_id = string(campanha_id_corrente());", m)
        self.assertIn("getenv('UA_DD_SAEA_CAMPANHA_ID')", m)
        self.assertEqual(manifest.CAMPANHA_ENV, "UA_DD_SAEA_CAMPANHA_ID")
        # a MESMA fórmula do default (commit curto de 12 + data UTC)
        self.assertIn("rev-parse --short=12 HEAD", m)


class TestHigieneDoForce(unittest.TestCase):
    """OP-6: limpar os artefatos da célula ANTES de re-rodar."""

    def test_limpa_as_7_camadas_mais_jsonl_e_manifesto(self):
        with tempfile.TemporaryDirectory() as dr:
            _mini_celula(dr, com_final=True)
            jp = naming.jsonl_path(*ARGS, data_root=dr)
            open(jp, "w").close()
            removidos = manifest.limpar_celula(*ARGS, dr)
            self.assertEqual(len(removidos), 7)   # 4 camadas + ⑦ + ⑥ + ⑤
            for p in removidos:
                self.assertFalse(os.path.exists(p))
            self.assertFalse(_pronto(dr))

    def test_dry_run_nao_apaga(self):
        with tempfile.TemporaryDirectory() as dr:
            _mini_celula(dr)
            removidos = manifest.limpar_celula(*ARGS, dr, dry_run=True)
            self.assertTrue(all(os.path.exists(p) for p in removidos))

    def test_recusa_o_baseline_pre_retrofit(self):
        # proibição absoluta da casa: `data/experiments/_baseline_pre_retrofit/**`
        with tempfile.TemporaryDirectory() as dr:
            raiz = os.path.join(dr, "_baseline_pre_retrofit")
            with self.assertRaises(RuntimeError):
                manifest.limpar_celula(*ARGS, raiz)

    def test_force_limpa_antes_de_rodar(self):
        with tempfile.TemporaryDirectory() as dr:
            _mini_celula(dr)
            jp = naming.jsonl_path(*ARGS, data_root=dr)
            with open(jp, "w", encoding="utf-8") as fh:
                fh.write('{"rec":"header","LIXO":"da execução anterior"}\n')
            vistos = {}

            def _espia(exp, alg, prob, seed, root, **kw):
                vistos["jsonl_existe"] = os.path.exists(jp)
                vistos["manifesto_existe"] = os.path.exists(
                    naming.manifest_path(exp, alg, prob, seed, data_root=root))
                return "ok"

            with mock.patch.object(experiments, "_run_one", side_effect=_espia):
                experiments.main(["--exp", "main", "--algorithms", "c262",
                                  "--problems", "ZDT1", "--seeds", "0",
                                  "--data-root", dr, "--force", "--no-consolidate"])
            self.assertEqual(vistos, {"jsonl_existe": False,
                                      "manifesto_existe": False})

    def test_sem_force_a_celula_pronta_e_pulada_e_nada_e_apagado(self):
        with tempfile.TemporaryDirectory() as dr:
            _mini_celula(dr)
            mp = naming.manifest_path(*ARGS, data_root=dr)
            with mock.patch.object(experiments, "is_run_done", return_value=True), \
                 mock.patch.object(experiments, "_run_one") as um:
                experiments.main(["--exp", "main", "--algorithms", "c262",
                                  "--problems", "ZDT1", "--seeds", "0",
                                  "--data-root", dr, "--no-consolidate"])
            um.assert_not_called()
            self.assertTrue(os.path.exists(mp))


class TestFallbackFooter(unittest.TestCase):
    """O-21/E-04: sem ⑤, a certidão vem do footer do ⑥ — não de 'sem-manifesto'."""

    def _jsonl_com_footer(self, dr, **campos):
        jp = naming.jsonl_path(*ARGS, data_root=dr)
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        with open(jp, "w", encoding="utf-8") as fh:
            fh.write('{"ts":"2026-07-27T00:00:00Z","rec":"header","D":30}\n')
            fh.write(json.dumps({"ts": "2026-07-27T03:00:00Z", "rec": "footer",
                                 **campos}) + "\n")
        return jp

    def test_sem_nada_devolve_none(self):
        with tempfile.TemporaryDirectory() as dr:
            self.assertIsNone(manifest.certidao_do_run(*ARGS, dr))

    def test_cai_para_o_footer_do_jsonl(self):
        with tempfile.TemporaryDirectory() as dr:
            self._jsonl_com_footer(
                dr, status="failed", fe_final=929,
                erro="least squares problem is underdetermined")
            c = manifest.certidao_do_run(*ARGS, dr)
            self.assertEqual(c["fonte"], "footer_jsonl")
            self.assertEqual(c["status"], "failed")
            self.assertEqual(c["fe_final"], 929)
            self.assertEqual(c["motivo"],
                             "least squares problem is underdetermined")

    def test_o_manifesto_tem_precedencia(self):
        with tempfile.TemporaryDirectory() as dr:
            _mini_celula(dr)
            self._jsonl_com_footer(dr, status="failed", fe_final=929)
            c = manifest.certidao_do_run(*ARGS, dr)
            self.assertEqual(c["fonte"], "manifesto")
            self.assertEqual(c["status"], "ok")
            self.assertEqual(c["campanha_id"], manifest.campanha_id_corrente())

    def test_footer_sem_fe_final_nao_serve_de_certidao(self):
        # é o footer do DESPACHANTE (ou um par espúrio do append cego): não
        # certifica fim de run nenhum.
        with tempfile.TemporaryDirectory() as dr:
            self._jsonl_com_footer(dr, status="failed", n_retries=0)
            self.assertIsNone(manifest.certidao_do_run(*ARGS, dr))

    def test_termino_heterogeneo_por_config(self):
        # I-08: o campo de término muda por stack — `termino` (13 MATLAB),
        # `motivo` (c311), `erro`, `motivo_parada` (⑤ dos standalone).
        for campo in ("motivo_parada", "motivo", "erro", "termino"):
            with self.subTest(campo=campo), tempfile.TemporaryDirectory() as dr:
                self._jsonl_com_footer(dr, status="failed", fe_final=1,
                                       **{campo: "teto_wall"})
                self.assertEqual(manifest.certidao_do_run(*ARGS, dr)["motivo"],
                                 "teto_wall")


if __name__ == "__main__":
    unittest.main()
