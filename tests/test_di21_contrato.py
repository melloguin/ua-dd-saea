# -*- coding: utf-8 -*-
"""[DI-21, torre 2026-07-22] Testes do lote de decisões ratificadas pelo autor.

Cobrem as mudanças de contrato/infra aplicadas após o fechamento do retrofit
DI-09 (MATLAB 11/11 + BoTorch) — cada teste cita a decisão que trava:

- **D-01** `n_acumulado` NULLABLE na ④ (pisos não treinam — irmã da DI-13.2).
- **D-02** `normalize_schema`/`concat_normalized`: a consolidação cross-stack
  (MATLAB grava double+NaN e large_string; Python grava int32-null e string).
- **D-03** `is_run_done` bucket-aware FALHA FECHADO sem a lib/rede.
- **D-07** aborto por teto ⇒ manifesto `failed` + `WallClockAbort` não-retriável.
- **D-12** os 5 offline exigem a ⑦ `__final` no `is_run_done`;
  `plan_targets(optional_layers=...)` planeja a ⑦ na rota única.
- **D-15** o próprio arquivo: a varredura de schema dos parquets REAIS do repo
  (o teste que teria pego o `n_acumulado` dos pisos e o `espaco_modelo`
  "nativo" antes de qualquer auditoria).
"""
from __future__ import annotations

import glob
import json
import os
import tempfile
import unittest

import numpy as np

from src import export, manifest, naming


def _pa():
    import pyarrow as pa
    return pa


class TestD01NAcumuladoNullable(unittest.TestCase):
    def test_schema_nullable(self):
        f = export.timing_schema().field("n_acumulado")
        self.assertTrue(f.nullable, "D-01: n_acumulado deve ser NULLABLE")

    def test_write_timing_aceita_none(self):
        with tempfile.TemporaryDirectory() as root:
            p = export.write_timing(
                "main", "nsga2", "MMF1", 0,
                [{"geracao": 1, "n_acumulado": None, "tempo_fit_s": None,
                  "tempo_busca_s": None, "tempo_pred_sonda_s": None,
                  "tempo_geracao_s": 0.1}],
                data_root=root)
            import pyarrow.parquet as pq
            t = pq.read_table(p)
            self.assertIsNone(t.column("n_acumulado").to_pylist()[0])

    def test_piso_real_casta_ao_schema(self):
        """O caso que estourava: a ④ do piso (n_acumulado NULL) sob o schema."""
        import pyarrow.parquet as pq
        p = "data/experiments/main/nsga2/exp_main_nsga2_MMF1_0__timing.parquet"
        if not os.path.exists(p):
            self.skipTest("run do piso ausente")
        t = pq.read_table(p)
        norm = export.normalize_schema(t)
        norm.cast(export.timing_schema())          # não pode levantar


class TestD02NormalizeConcat(unittest.TestCase):
    def test_double_nan_vira_int32_null(self):
        pa = _pa()
        t = pa.table({"geracao": pa.array([1.0, float("nan"), 3.0],
                                          type=pa.float64())})
        out = export.normalize_schema(t)
        self.assertEqual(out.schema.field("geracao").type, pa.int32())
        self.assertEqual(out.column("geracao").to_pylist(), [1, None, 3])

    def test_large_string_vira_string(self):
        pa = _pa()
        t = pa.table({"fase": pa.array(["init", "infill"],
                                       type=pa.large_string())})
        out = export.normalize_schema(t)
        self.assertEqual(out.schema.field("fase").type, pa.string())

    def test_concat_matlab_x_python_na_pratica(self):
        """A operação REAL da consolidação R4: ④ MATLAB (piso, colunas velhas
        possíveis) + ④ Python — antes desta função, ArrowInvalid."""
        import pyarrow.parquet as pq
        a = "data/experiments/main/nsga2/exp_main_nsga2_MMF1_0__timing.parquet"
        b = "data/experiments/main/c262/exp_main_c262_MMF1_0__timing.parquet"
        if not (os.path.exists(a) and os.path.exists(b)):
            self.skipTest("runs de referência ausentes")
        out = export.concat_normalized([pq.read_table(a), pq.read_table(b)])
        self.assertEqual(out.num_rows,
                         pq.read_table(a).num_rows + pq.read_table(b).num_rows)

    def test_concat_surrogate_cross_stack(self):
        import pyarrow.parquet as pq
        a = "data/experiments/main/b1/exp_main_b1_MMF1_0__surrogate.parquet"
        b = "data/experiments/main/c262/exp_main_c262_MMF1_0__surrogate.parquet"
        if not (os.path.exists(a) and os.path.exists(b)):
            self.skipTest("runs de referência ausentes")
        ta, tb = pq.read_table(a), pq.read_table(b)
        out = export.concat_normalized([ta, tb])
        self.assertEqual(out.num_rows, ta.num_rows + tb.num_rows)
        # a coluna crítica do e103: geracao aceita NULL dos dois lados
        self.assertTrue(out.schema.field("geracao").nullable)


def _mini_run(root, alg, *, com_final=False, status="ok"):
    """Materializa um run mínimo válido (4 camadas parquet + manifesto)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    exp, prob, sem = "main", "MMF1", 0
    for ly in naming.LAYERS + ((naming.FINAL_LAYER,) if com_final else ()):
        p = naming.layer_path(exp, alg, prob, sem, ly, root)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        pq.write_table(pa.table({"x": pa.array([1])}), p)
    man = manifest.new_manifest(exp, alg, prob, sem, status=status,
                                maxfe=61, fe_final=61, data_root=root)
    manifest.write_manifest(man, root)
    return exp, prob, sem


class TestD12FinalNoResume(unittest.TestCase):
    def test_offline_sem_final_nao_esta_pronto(self):
        with tempfile.TemporaryDirectory() as root:
            exp, prob, sem = _mini_run(root, "e103", com_final=False)
            self.assertFalse(manifest.is_run_done(exp, "e103", prob, sem, root))

    def test_offline_com_final_esta_pronto(self):
        with tempfile.TemporaryDirectory() as root:
            exp, prob, sem = _mini_run(root, "e103", com_final=True)
            self.assertTrue(manifest.is_run_done(exp, "e103", prob, sem, root))

    def test_online_nao_exige_final(self):
        with tempfile.TemporaryDirectory() as root:
            exp, prob, sem = _mini_run(root, "b1", com_final=False)
            self.assertTrue(manifest.is_run_done(exp, "b1", prob, sem, root))

    def test_lista_offline_canonica(self):
        # [DI-35.2/T8] +treed_media (o piso-big do sweep)
        self.assertEqual(manifest.OFFLINE_ALGS,
                         frozenset({"e103", "b5r", "b5m", "c311",
                                    "moead_media", "treed_media"}))

    def test_plan_targets_inclui_final(self):
        from src import gcs
        arts = gcs.plan_targets("off", "b5r", "MMF1", 0, enable_bucket=False,
                                optional_layers=(naming.FINAL_LAYER,))
        self.assertIn("final", arts)
        arts_sem = gcs.plan_targets("off", "b5r", "MMF1", 0,
                                    enable_bucket=False)
        self.assertNotIn("final", arts_sem)


class TestD03BucketFallbackFalhaFechado(unittest.TestCase):
    def test_camada_ausente_sem_gcs_e_nao_pronto(self):
        """c154 (bucket-only na ③) com a ③ removida: no Mac (sem lib/rede) o
        fallback tem de FALHAR FECHADO — False, nunca um falso 'pronto'."""
        with tempfile.TemporaryDirectory() as root:
            exp, prob, sem = _mini_run(root, "c154", com_final=False)
            os.remove(naming.layer_path(exp, "c154", prob, sem, "surrogate",
                                        root))
            self.assertFalse(
                manifest.is_run_done(exp, "c154", prob, sem, root))

    def test_camada_nao_bucket_only_nunca_consulta_rede(self):
        """b1 (não bucket-only): camada ausente ⇒ False direto (o fallback nem
        se aplica — _bucket_has responde False antes de tocar a rede)."""
        self.assertFalse(manifest._bucket_has("main", "b1", "MMF1", 0,
                                              "surrogate"))


class TestD07TetoWall(unittest.TestCase):
    def test_manifesto_failed_no_aborto(self):
        from src.c262_qnehvi import _manifesto_failed_teto
        with tempfile.TemporaryDirectory() as root:
            _manifesto_failed_teto("main", "c262", "ZDT1", 0, root,
                                   criterio="elapsed", elapsed_s=28800.0,
                                   fe=500, maxfe=929)
            man = manifest.read_manifest(
                naming.manifest_path("main", "c262", "ZDT1", 0, root))
            self.assertEqual(man["status"], "failed")
            self.assertEqual(man["motivo_parada"], "teto_wall")
            self.assertEqual(int(man["fe_final"]), 500)
            # e o is_run_done NUNCA lê este run como pronto:
            self.assertFalse(manifest.is_run_done("main", "c262", "ZDT1", 0,
                                                  root))

    def test_despachante_nao_retria_wallclockabort(self):
        """O retry de um teto de 8h viraria 24h — WallClockAbort corta na 1ª."""
        import experiments as exps
        chamadas = {"n": 0}

        class WallClockAbort(RuntimeError):
            pass

        def fake_run(alg, problema, semente, **kw):
            chamadas["n"] += 1
            raise WallClockAbort("teto estourado (teste)")

        orig = exps._adapter.run
        exps._adapter.run = fake_run
        try:
            with tempfile.TemporaryDirectory() as root:
                st = exps._run_one("main", "b1", "MMF1", 0, root)
        finally:
            exps._adapter.run = orig
        self.assertEqual(st, "failed")
        self.assertEqual(chamadas["n"], 1,
                         "aborto por teto NÃO pode ser retriado")


class TestD15VarreduraDeSchema(unittest.TestCase):
    """A rede permanente: todo parquet REAL do repo tem de normalizar ao
    canônico sem erro, e o vocabulário das colunas-enum tem de estar dentro
    do contrato. Teria pego o 'nativo' (1.050.000 linhas) e o n_acumulado dos
    pisos ANTES de qualquer workflow de auditoria."""

    def test_todos_os_parquets_normalizam(self):
        import pyarrow.parquet as pq
        files = glob.glob("data/experiments/main/*/*__*.parquet")
        if not files:
            self.skipTest("sem dados no repo")
        erros = []
        for f in files:
            try:
                export.normalize_schema(pq.read_table(f))
            except Exception as e:            # noqa: BLE001 — coleta p/ laudo
                erros.append(f"{f}: {type(e).__name__}: {e}")
        self.assertEqual(erros, [])

    def test_espaco_modelo_dentro_do_enum(self):
        import pyarrow.parquet as pq
        ruins = []
        for f in glob.glob("data/experiments/main/*/*__surrogate.parquet"):
            if "_stub" in f:      # stubs de infra: auto-teste, fora do contrato
                continue
            t = pq.read_table(f, columns=["espaco_modelo"])
            vals = {v for v in t.column("espaco_modelo").to_pylist()
                    if v is not None and v != ""}
            fora = vals - set(export.ESPACOS)
            if fora:
                ruins.append(f"{os.path.basename(f)}: {sorted(fora)}")
        self.assertEqual(ruins, [], "valores fora do enum DI-19.8")

    def test_timing_real_casta_ao_canonico(self):
        """Toda ④ do repo, normalizada, casta ao timing_schema()."""
        import pyarrow.parquet as pq
        erros = []
        for f in glob.glob("data/experiments/main/*/*__timing.parquet"):
            if "_stub" in f:
                continue
            try:
                # `cast_completo` = a leitura canônica do R4: completa as
                # colunas nullable dos runs PRÉ-retrofit (c238/e7 ZDT1, fora
                # do cartão por custo) e casta ao schema.
                export.cast_completo(pq.read_table(f), export.timing_schema())
            except Exception as e:            # noqa: BLE001
                erros.append(f"{os.path.basename(f)}: {e}")
        self.assertEqual(erros, [])


if __name__ == "__main__":
    unittest.main()
