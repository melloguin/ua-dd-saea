# -*- coding: utf-8 -*-
"""Testes do espelho resiliente — G4: B-09 (espelho no aborto) · B-10 (identidade).

* **B-09** — `mirror_run` só rodava DENTRO de `write_run_outputs`, isto é, no fim
  de run bem-sucedido: as **~870 células não-OK** de 30 sementes (29/semente)
  tinham a evidência órfã no disco de uma VM efêmera e ela morria com a VM. O
  footer `failed`+`erro` do ⑥ é o ÚNICO lugar onde o stack MATLAB certifica a
  própria falha (O-21) — perde-se o diagnóstico inteiro.
* **B-10** — `gcs.py:155` fazia `os.remove(local)` da ③ (a ÚNICA cópia local dos
  5 bucket-only) sem identidade de execução no blob. É a mecânica exata da
  quimera `batch/c149/q10_ZDT4`: ①②④⑤⑥ do run da v6 (26/07) com a ③ do run do
  Mac (24/07), md5 `1269b87f7612`, cruzamento ③×① fechando **0/2.000**. Com a ③
  local podada, a quimera ficou IRRECUPERÁVEL.

Sem rede: um cliente GCS **falso** implementa o contrato que usamos
(`bucket().blob().upload_from_filename(..., if_generation_match=)`, `.reload()`,
`.md5_hash`) e o 412 do GCS. Tudo em tempdir (B-13/G-8).
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

import experiments                                   # noqa: E402
from src import gcs, manifest, naming                 # noqa: E402


class _Precondicao412(Exception):
    """O que o `google-cloud-storage` levanta quando o `if_generation_match`
    falha (`google.api_core.exceptions.PreconditionFailed`, code 412)."""
    code = 412


class _BlobFalso:
    def __init__(self, bucket, nome):
        self.bucket, self.nome = bucket, nome
        self.md5_hash = None

    def upload_from_filename(self, local, **kw):
        igm = kw.get('if_generation_match')
        if igm == 0 and self.nome in self.bucket.objetos:
            raise _Precondicao412(f'412 já existe: {self.nome}')
        # `corromper` simula o upload que chega DIFERENTE do local (rede/disco)
        self.bucket.objetos[self.nome] = ('md5-corrompido-no-transporte'
                                          if self.bucket.corromper
                                          else gcs.md5_b64(local))
        self.bucket.uploads.append(self.nome)

    def exists(self):
        return self.nome in self.bucket.objetos

    def reload(self):
        self.md5_hash = self.bucket.objetos.get(self.nome)


class _BucketFalso:
    def __init__(self, objetos=None, corromper=False):
        self.objetos = dict(objetos or {})
        self.uploads = []
        self.corromper = corromper

    def blob(self, nome):
        return _BlobFalso(self, nome)


class _ClienteFalso:
    def __init__(self, objetos=None, corromper=False):
        self._b = _BucketFalso(objetos, corromper)

    def bucket(self, nome):
        return self._b


ARGS = ("main", "c149", "ZDT4", 42)


def _celula_local(dr, *, args=ARGS, conteudo=b"parquet-falso"):
    """As 4 camadas + ⑥ + ⑤ em disco (é o que o `mirror_run` espelha)."""
    for ly in naming.LAYERS:
        p = naming.layer_path(*args, ly, data_root=dr)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(conteudo + ly.encode())
    with open(naming.jsonl_path(*args, data_root=dr), "w", encoding="utf-8") as fh:
        fh.write('{"rec":"footer","status":"failed","fe_final":2109,'
                 '"erro":"least squares problem is underdetermined"}\n')
    manifest.write_manifest(
        manifest.new_manifest(*args, status="failed", data_root=dr), dr)


class TestIdentidadeDeExecucao(unittest.TestCase):
    """B-10: criar-ou-recusar, e a ③ local só é podada com upload CONFIRMADO."""

    def test_blob_de_outro_host_nao_e_sobrescrito(self):
        with tempfile.TemporaryDirectory() as dr:
            _celula_local(dr)
            # o objeto da ③ JÁ está no bucket (o run do Mac, na quimera)
            blob3 = naming.blob_path("main", "c149", naming.layer_filename(
                *ARGS, "surrogate"))
            cli = _ClienteFalso({blob3: "md5-do-run-do-Mac"})
            st = gcs.mirror_run(*ARGS, data_root=dr, client=cli)
            self.assertEqual(st["surrogate"], "colidiu_412")
            # e o essencial: a ÚNICA cópia local da ③ continua no disco
            self.assertTrue(os.path.exists(
                naming.layer_path(*ARGS, "surrogate", data_root=dr)))
            self.assertEqual(cli._b.objetos[blob3], "md5-do-run-do-Mac")

    def test_run_dono_sobe_e_poda_a_terceira(self):
        with tempfile.TemporaryDirectory() as dr:
            _celula_local(dr)
            cli = _ClienteFalso()
            st = gcs.mirror_run(*ARGS, data_root=dr, client=cli)
            self.assertEqual(st["surrogate"], "uploaded_bucket_only")
            self.assertFalse(os.path.exists(
                naming.layer_path(*ARGS, "surrogate", data_root=dr)))
            # as demais camadas são dual-write: sobem e FICAM
            for ly in ("real", "pop", "timing"):
                self.assertEqual(st[ly], "uploaded")
                self.assertTrue(os.path.exists(
                    naming.layer_path(*ARGS, ly, data_root=dr)))

    def test_sobrescrever_true_e_a_re_execucao_legitima(self):
        with tempfile.TemporaryDirectory() as dr:
            _celula_local(dr)
            blob3 = naming.blob_path("main", "c149", naming.layer_filename(
                *ARGS, "surrogate"))
            cli = _ClienteFalso({blob3: "md5-antigo"})
            st = gcs.mirror_run(*ARGS, data_root=dr, client=cli,
                                sobrescrever=True)
            self.assertEqual(st["surrogate"], "uploaded_bucket_only")
            self.assertNotEqual(cli._b.objetos[blob3], "md5-antigo")

    def test_md5_divergente_nao_poda(self):
        # "upload confirmado" tem de significar confirmado: se o blob volta com
        # md5 diferente, a cópia local é a única boa e NÃO pode ser apagada.
        with tempfile.TemporaryDirectory() as dr:
            _celula_local(dr)
            cli = _ClienteFalso(corromper=True)
            local3 = naming.layer_path(*ARGS, "surrogate", data_root=dr)
            with self.assertRaises(RuntimeError):
                gcs.mirror_run(*ARGS, data_root=dr, client=cli)
            self.assertTrue(os.path.exists(local3))

    def test_upload_verificado_compara_o_md5(self):
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "a.parquet")
            with open(p, "wb") as fh:
                fh.write(b"conteudo")
            cli = _ClienteFalso()
            out = gcs.upload(p, "experiments/x/a.parquet", client=cli,
                             verificar=True)
            self.assertEqual(out["status"], "uploaded_verificado")
            self.assertEqual(out["md5_local"], out["md5_blob"])
            self.assertEqual(out["md5_local"], gcs.md5_b64(p))

    def test_412_vira_colisao_de_blob(self):
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "a.parquet")
            with open(p, "wb") as fh:
                fh.write(b"x")
            cli = _ClienteFalso({"experiments/x/a.parquet": "md5-alheio"})
            with self.assertRaises(gcs.ColisaoDeBlob):
                gcs.upload(p, "experiments/x/a.parquet", client=cli,
                           if_generation_match=0)

    def test_412_e_reconhecido_pelas_3_formas(self):
        class _PorCode(Exception):
            code = 412

        class PreconditionFailed(Exception):
            pass

        class _PorMessage(Exception):
            message = "412 Precondition Failed"

        for e in (_PorCode(), PreconditionFailed(), _PorMessage()):
            self.assertTrue(gcs._e_412(e), type(e).__name__)
        self.assertFalse(gcs._e_412(OSError("disco cheio")))


class TestEspelhoNoAborto(unittest.TestCase):
    """B-09: a trilha leve (⑥+⑤) do run não-OK sobe."""

    def test_mirror_evidencia_sobe_so_jsonl_e_manifesto(self):
        with tempfile.TemporaryDirectory() as dr:
            _celula_local(dr)
            cli = _ClienteFalso()
            out = gcs.mirror_evidencia(*ARGS, data_root=dr, client=cli)
            self.assertEqual(out, {"jsonl": "uploaded", "manifest": "uploaded"})
            subidos = " ".join(cli._b.uploads)
            self.assertIn(".jsonl", subidos)
            self.assertIn(".manifest.json", subidos)
            self.assertNotIn("__surrogate", subidos)   # camada pesada NÃO
            self.assertNotIn("__real", subidos)

    def test_mirror_evidencia_nunca_levanta(self):
        # a blindagem DI-42.3: o run já morreu; um erro de upload aqui não pode
        # virar uma segunda causa de morte (foi assim que 7/58 runs do c311
        # morreram na rodada-42, truncando o ⑥ DEPOIS do manifesto 'ok').
        with tempfile.TemporaryDirectory() as dr:
            _celula_local(dr)
            cli = mock.Mock()
            cli.bucket.side_effect = RuntimeError("google-cloud-storage ausente")
            out = gcs.mirror_evidencia(*ARGS, data_root=dr, client=cli)
            self.assertIn("erro", out)

    def test_ausente_e_declarado_nao_inventado(self):
        with tempfile.TemporaryDirectory() as dr:
            out = gcs.mirror_evidencia(*ARGS, data_root=dr, client=_ClienteFalso())
            self.assertEqual(out, {"jsonl": "absent", "manifest": "absent"})

    def test_despachante_espelha_a_evidencia_do_run_falho(self):
        with tempfile.TemporaryDirectory() as dr:
            chamadas = []

            def _falso_mirror(exp, alg, problema, semente, **kw):
                chamadas.append((exp, alg, problema, semente))
                return {"jsonl": "uploaded", "manifest": "uploaded"}

            with mock.patch.object(experiments, "_adapter") as ad, \
                 mock.patch.object(experiments, "RETRY_BACKOFF_S", 0), \
                 mock.patch.object(gcs, "mirror_evidencia", _falso_mirror):
                ad.run.side_effect = RuntimeError(
                    "ModelFittingError: All attempts to fit")
                st = experiments._run_one(*ARGS, dr, checar_pronto=False,
                                          enable_bucket=True)
            self.assertEqual(st, "failed")
            self.assertEqual(chamadas, [ARGS])
            with open(naming.manifest_path(*ARGS, data_root=dr),
                      encoding="utf-8") as fh:
                man = json.load(fh)
            self.assertEqual(man["upload_status"]["evidencia_jsonl"], "uploaded")

    def test_despachante_nao_espelha_run_ok(self):
        # no caminho de sucesso o harness já espelhou TUDO via mirror_run —
        # repetir aqui seria upload duplicado de artefato pesado.
        with tempfile.TemporaryDirectory() as dr:
            with mock.patch.object(experiments, "_adapter"), \
                 mock.patch.object(gcs, "mirror_evidencia") as ev:
                st = experiments._run_one(*ARGS, dr, checar_pronto=False,
                                          enable_bucket=True)
            self.assertEqual(st, "ok")
            ev.assert_not_called()

    def test_write_failed_manifest_espelha_quando_bucket_ligado(self):
        from src import standalone_harness as H
        with tempfile.TemporaryDirectory() as dr:
            with mock.patch.object(gcs, "mirror_evidencia",
                                   return_value={"jsonl": "uploaded",
                                                 "manifest": "uploaded"}) as ev:
                p = H.write_failed_manifest(
                    *ARGS, motivo="erro_LinAlgError", regime="offline",
                    maxfe=929, fe_final=300, enable_bucket=True, data_root=dr)
            ev.assert_called_once()
            with open(p, encoding="utf-8") as fh:
                man = json.load(fh)
            self.assertEqual(man["status"], "failed")
            self.assertEqual(man["motivo_parada"], "erro_LinAlgError")
            self.assertEqual(man["upload_status"]["jsonl"], "uploaded")

    def test_write_failed_manifest_sem_bucket_nao_fala_com_a_rede(self):
        from src import standalone_harness as H
        with tempfile.TemporaryDirectory() as dr:
            with mock.patch.object(gcs, "mirror_evidencia") as ev:
                H.write_failed_manifest(*ARGS, motivo="erro_X", regime="offline",
                                        data_root=dr)
            ev.assert_not_called()

    def test_os_4_runners_standalone_repassam_enable_bucket(self):
        # fio despachante→runner→harness: esquecer 1 sítio = evidência perdida
        # justamente na célula que falhou (a família dos 5 bugs de lançamento).
        import re
        for nome in ("b5_prob", "piso_offline", "sobol_batch", "treed_media"):
            with self.subTest(runner=nome):
                with open(os.path.join(_RAIZ, "src", f"{nome}.py"),
                          encoding="utf-8") as fh:
                    src = fh.read()
                bloco = src[src.index("H.write_failed_manifest("):]
                bloco = bloco[:bloco.index(")\n")]
                self.assertIn("enable_bucket=enable_bucket", bloco)


if __name__ == "__main__":
    unittest.main()
