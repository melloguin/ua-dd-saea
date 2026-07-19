"""Testes do cartão DI09-retrofit-R2 — a instrumentação DI-09/DI-10/DI-11.3 nos
2 runners BoTorch (c262 qNEHVI, c154 JES) + o lado Python do writer.

Cobrem o ENCANAMENTO (D97 — nada de fidelidade):

- **③/④ ADITIVAS**: `fe_treino_max`, `regime` por linha, `tempo_pred_sonda_s`/
  `tempo_geracao_s` — e a garantia de que um ④ gravado ANTES do retrofit segue
  legível (o compromisso explícito do cartão).
- **SONDA §17.2.2**: hash-check do artefato (a disciplina D63/D87 — o runner
  CARREGA, nunca gera), cadência k=2 e a 🔴 guarda de RNG (não-perturbação).
- **DI-10**: mínimo comum do `<alg>_gen` e o `sigma_dict` dos 2 configs — em
  particular a decisão da torre sobre o `n_baseline` N/A no JES (DI-11 item 2).
- **DI-11.3**: o teto de tempo DECORRIDO independente da projeção pós-10-iters
  (a lacuna D-8 herdada do c262) — provado sem run real, como o adendo pede.
- **backfill da ④** a partir do `.jsonl`, incluindo a guarda anti-reescrita.

Como nos demais testes da R2: pulam limpo sem torch/botorch (a suíte segue
verde em qualquer interpretador); os que só precisam de pyarrow/numpy rodam
sempre.
"""

import json
import os
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    import numpy as np
    import pyarrow  # noqa: F401
    HAS_ARROW = True
except Exception:  # noqa: BLE001
    HAS_ARROW = False

try:
    import torch  # noqa: F401
    import botorch  # noqa: F401
    HAS_STACK = True
except Exception:  # noqa: BLE001
    HAS_STACK = False

SEM_ARROW = "pyarrow/numpy ausente neste interpretador"
SEM_STACK = "stack R2 (torch/botorch) ausente neste interpretador"


# ═══════════════════════════════════════════════════════════════════════════
#  ③ e ④ — as colunas ADITIVAS da v5.2.1
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(HAS_ARROW, SEM_ARROW)
class TestColunasAditivas(unittest.TestCase):

    def test_schema_ganhou_as_3_colunas_todas_nullable(self):
        from src import export
        s = export.surrogate_schema(3, 2)
        self.assertIn("fe_treino_max", s.names)
        self.assertTrue(s.field("fe_treino_max").nullable)
        t = export.timing_schema()
        for c in ("tempo_pred_sonda_s", "tempo_geracao_s"):
            self.assertIn(c, t.names)
            self.assertTrue(t.field(c).nullable)

    def test_regime_por_linha_sobrepoe_o_default_do_writer(self):
        # é o mecanismo que deixa busca e sonda na MESMA ③ (§17.2.2).
        import pyarrow.parquet as pq
        from src import export
        rows = [
            export.surrogate_row(1, [0.1, 0.2], mu=[1.0, 2.0]),            # ⇒ default
            export.surrogate_row(1, [0.3, 0.4], mu=[3.0, 4.0], regime="sonda"),
        ]
        with tempfile.TemporaryDirectory() as d:
            p = export.write_surrogate("main", "c262", "MMF1", 0, rows,
                                       D=2, M=2, regime="online", data_root=d)
            got = pq.read_table(p).column("regime").to_pylist()
        self.assertEqual(got, ["online", "sonda"])

    def test_fe_treino_max_grava_e_aceita_ausencia(self):
        import pyarrow.parquet as pq
        from src import export
        rows = [export.surrogate_row(1, [0.1], mu=[1.0], fe_treino_max=41),
                export.surrogate_row(1, [0.2], mu=[2.0])]
        with tempfile.TemporaryDirectory() as d:
            p = export.write_surrogate("main", "c262", "MMF1", 0, rows,
                                       D=1, M=1, data_root=d)
            self.assertEqual(
                pq.read_table(p).column("fe_treino_max").to_pylist(), [41, None])

    def test_timing_aceita_linhas_SEM_as_colunas_novas(self):
        # compat.: um instrumentador que ainda não as produz segue válido.
        import pyarrow.parquet as pq
        from src import export
        with tempfile.TemporaryDirectory() as d:
            p = export.write_timing(
                "main", "b3", "MMF1", 0,
                [{"geracao": 1, "n_acumulado": 10, "tempo_fit_s": 0.5}],
                data_root=d)
            t = pq.read_table(p)
        self.assertEqual(t.column("tempo_pred_sonda_s").null_count, 1)
        self.assertEqual(t.column("tempo_geracao_s").null_count, 1)

    def test_timing_PRE_retrofit_continua_legivel(self):
        """O compromisso do cartão: runs antigos não quebram. Escreve um ④ com
        o schema ANTIGO (5 colunas) e confirma que a leitura segue funcionando —
        as colunas novas simplesmente não existem no arquivo."""
        import pyarrow as pa
        import pyarrow.parquet as pq
        antigo = pa.schema([
            pa.field("run_id", pa.string(), nullable=False),
            pa.field("geracao", pa.int32(), nullable=False),
            pa.field("n_acumulado", pa.int32(), nullable=False),
            pa.field("tempo_fit_s", pa.float32(), nullable=False),
            pa.field("tempo_busca_s", pa.float32(), nullable=True),
        ])
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "velho__timing.parquet")
            pq.write_table(pa.table(
                {"run_id": ["r"], "geracao": [1], "n_acumulado": [10],
                 "tempo_fit_s": [0.5], "tempo_busca_s": [None]}).cast(antigo), p)
            t = pq.read_table(p)
        self.assertEqual(t.num_rows, 1)
        self.assertNotIn("tempo_geracao_s", t.schema.names)   # ausente, não erro
        self.assertEqual(float(t.column("tempo_fit_s")[0].as_py()), 0.5)


@unittest.skipUnless(HAS_ARROW, SEM_ARROW)
class TestManifestTimingBlock(unittest.TestCase):

    def test_as_4_chaves_obrigatorias_mais_extras(self):
        from src import export
        b = export.manifest_timing_block(
            tempo_total_s=1.23456789, tempo_fit_surrogate_s=0.5,
            tempo_busca_s=0.7, tempo_aval_real_s=0.01,
            tempo_pred_sonda_s=0.2, tempo_paths_s=0.3)
        for k in ("tempo_total_s", "tempo_fit_surrogate_s",
                  "tempo_busca_s", "tempo_aval_real_s"):
            self.assertIn(k, b)
        self.assertEqual(b["tempo_total_s"], 1.2346)          # 4 casas
        self.assertEqual(b["tempo_pred_sonda_s"], 0.2)
        self.assertEqual(b["tempo_paths_s"], 0.3)             # extra do c154

    def test_sonda_omitida_quando_o_config_nao_tem(self):
        from src import export                                # os 4 pisos (R1)
        b = export.manifest_timing_block(
            tempo_total_s=1.0, tempo_fit_surrogate_s=0.0,
            tempo_busca_s=1.0, tempo_aval_real_s=0.0)
        self.assertNotIn("tempo_pred_sonda_s", b)


# ═══════════════════════════════════════════════════════════════════════════
#  Backfill da ④ a partir do `.jsonl` (gap D-4 do c154)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(HAS_ARROW, SEM_ARROW)
class TestBackfillTiming(unittest.TestCase):

    def _run_sintetico(self, d, *, com_timing=True):
        """3 iterações: as 2 primeiras com `t_busca_s` logado; a 3ª é o
        `hard_stop` (sem a grandeza) — o retrato exato do c154/DTLZ2."""
        from src import export, naming
        jp = naming.jsonl_path("main", "c154", "MMF1", 0, d)
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        t0 = 1_000_000.0
        linhas, rows = [], []

        def ts(x):
            from datetime import datetime, timezone
            return datetime.fromtimestamp(x, timezone.utc).isoformat(
                timespec="milliseconds")

        for it in (1, 2, 3):
            ini = t0 + (it - 1) * 100.0
            fit = 2.0
            linhas.append({"ts": ts(ini + fit), "rec": "timing", "it": it,
                           "n_acumulado": 10 + it, "tempo_fit_s": fit})
            dec = {"ts": ts(ini + fit + 90.0), "rec": "decision", "it": it,
                   "caminho": "infill" if it < 3 else "hard_stop"}
            if it < 3:
                dec["t_busca_s"] = 90.0
            linhas.append(dec)
            rows.append({"geracao": it, "n_acumulado": 10 + it,
                         "tempo_fit_s": fit})
        linhas.append({"ts": ts(t0 + 295.0), "rec": "footer", "status": "ok"})
        with open(jp, "w", encoding="utf-8") as fh:
            for r in linhas:
                fh.write(json.dumps(r) + "\n")
        if com_timing:
            export.write_timing("main", "c154", "MMF1", 0, rows, data_root=d)
        return d

    def test_exatos_derivados_e_zero_nulos(self):
        import pyarrow.parquet as pq
        from src import export
        with tempfile.TemporaryDirectory() as d:
            self._run_sintetico(d)
            rel = export.backfill_timing_from_jsonl(
                "main", "c154", "MMF1", 0, data_root=d)
            self.assertEqual(rel["n_linhas"], 3)
            self.assertEqual(rel["busca_exatas"], 2)     # as 2 com t_busca_s
            self.assertEqual(rel["busca_derivadas"], 1)  # o hard_stop
            self.assertEqual(rel["busca_nulas"], 0)
            self.assertEqual(rel["linhas_conferidas_vs_disco"], 3)
            t = pq.read_table(rel["path"])
            self.assertEqual(t.column("tempo_busca_s").null_count, 0)
            # o derivado reconstrói o valor real (ts(decision)−ts(timing)).
            self.assertAlmostEqual(
                float(t.column("tempo_busca_s")[2].as_py()), 90.0, places=2)
            # tempo_geracao_s: âncoras = ts(timing)−tempo_fit_s ⇒ 100s de passo.
            self.assertAlmostEqual(
                float(t.column("tempo_geracao_s")[0].as_py()), 100.0, places=2)
            # run PRÉ-sonda: a coluna fica NULL (não havia grandeza a medir).
            self.assertEqual(t.column("tempo_pred_sonda_s").null_count, 3)

    def test_guarda_anti_reescrita_as_cegas(self):
        """④ do disco divergindo do jsonl ⇒ RuntimeError e NADA sobrescrito."""
        import pyarrow.parquet as pq
        from src import export
        with tempfile.TemporaryDirectory() as d:
            self._run_sintetico(d)
            export.write_timing("main", "c154", "MMF1", 0,
                                [{"geracao": 1, "n_acumulado": 999,
                                  "tempo_fit_s": 0.5}], data_root=d)
            antes = pq.read_table(
                os.path.join(d, "experiments", "main", "c154",
                             "exp_main_c154_MMF1_0__timing.parquet")).num_rows
            with self.assertRaises(RuntimeError):
                export.backfill_timing_from_jsonl(
                    "main", "c154", "MMF1", 0, data_root=d)
            depois = pq.read_table(
                os.path.join(d, "experiments", "main", "c154",
                             "exp_main_c154_MMF1_0__timing.parquet")).num_rows
        self.assertEqual(antes, depois)              # intacto

    def test_dry_run_nao_escreve(self):
        from src import export
        with tempfile.TemporaryDirectory() as d:
            self._run_sintetico(d, com_timing=False)
            rel = export.backfill_timing_from_jsonl(
                "main", "c154", "MMF1", 0, data_root=d, dry_run=True)
            self.assertTrue(rel["dry_run"])
            self.assertFalse(os.path.exists(rel["path"]))

    def test_jsonl_ausente_para_e_loga(self):
        from src import export
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                export.backfill_timing_from_jsonl(
                    "main", "c154", "MMF1", 0, data_root=d)

    # ── regressões da revisão adversarial ────────────────────────────────
    # Os 4 casos abaixo nasceram de defeitos CONFIRMADOS numa revisão do diff.
    # Cada um corrompia dados de forma silenciosa e plausível.

    def test_run_POS_retrofit_e_recusado(self):
        """🔴 O defeito mais grave achado na revisão: rodar o backfill sobre um
        run PÓS-retrofit substituía as colunas MEDIDAS por derivadas — inflando
        `tempo_geracao_s` (a definição do backfill incluía a sonda e o gc) e
        trocando `tempo_pred_sonda_s`=0.0 por NULL. `write_timing` reescreve o
        arquivo inteiro, então a troca era invisível."""
        from src import export
        with tempfile.TemporaryDirectory() as d:
            self._run_sintetico(d, com_timing=False)
            export.write_timing("main", "c154", "MMF1", 0, [
                {"geracao": it, "n_acumulado": 10 + it, "tempo_fit_s": 2.0,
                 "tempo_busca_s": 90.0, "tempo_pred_sonda_s": 0.0,
                 "tempo_geracao_s": 92.0} for it in (1, 2, 3)], data_root=d)
            with self.assertRaises(RuntimeError) as ctx:
                export.backfill_timing_from_jsonl(
                    "main", "c154", "MMF1", 0, data_root=d)
            self.assertIn("PÓS-retrofit", str(ctx.exception))

    def test_ultima_geracao_nao_absorve_a_cauda_de_escrita(self):
        """O `footer` do jsonl é emitido DEPOIS de `write_run_outputs` (4
        parquets + manifesto + upload). Estender a última geração até ele
        inflava justamente a linha de maior `n` — a que mais pesa no ajuste da
        curva de custo. A última passa a valer fit+busca (cota inferior)."""
        import pyarrow.parquet as pq
        from src import export
        with tempfile.TemporaryDirectory() as d:
            self._run_sintetico(d, com_timing=False)   # footer a t0+295
            rel = export.backfill_timing_from_jsonl(
                "main", "c154", "MMF1", 0, data_root=d)
            t = pq.read_table(rel["path"])
            ultima = float(t.column("tempo_geracao_s")[2].as_py())
        self.assertAlmostEqual(ultima, 2.0 + 90.0, places=2)   # fit + busca
        self.assertLess(ultima, 95.0)                          # não vai ao footer

    def test_tempo_pred_sonda_s_zero_vs_null(self):
        """NULL só quando o run é PRÉ-sonda (nenhum evento no jsonl inteiro).
        Num run COM sonda, iteração sem bloco vale 0.0 — a convenção do
        escritor vivo. Misturar as duas faz a coluna significar duas coisas."""
        import pyarrow.parquet as pq
        from src import export, naming
        with tempfile.TemporaryDirectory() as d:
            self._run_sintetico(d, com_timing=False)
            jp = naming.jsonl_path("main", "c154", "MMF1", 0, d)
            with open(jp, "a", encoding="utf-8") as fh:        # sonda só na it 2
                fh.write(json.dumps({"ts": "2001-09-09T01:48:10.000+00:00",
                                     "rec": "sonda", "it": 2,
                                     "tempo_pred_sonda_s": 1.5}) + "\n")
            rel = export.backfill_timing_from_jsonl(
                "main", "c154", "MMF1", 0, data_root=d)
            self.assertFalse(rel["pre_sonda"])
            col = pq.read_table(rel["path"]).column("tempo_pred_sonda_s")
        self.assertEqual(col.null_count, 0)                    # nenhum NULL
        self.assertEqual([v.as_py() for v in col], [0.0, 1.5, 0.0])

    def test_tempo_busca_derivado_negativo_nao_e_gravado(self):
        """`ts(decision) < ts(timing)` viola a premissa de ordem do estimador.
        Gravar o negativo (ou clampá-lo a 0) produziria um número plausível e
        falso; a linha fica NULL e a anomalia é CONTADA no relatório."""
        import pyarrow.parquet as pq
        from src import export, naming
        with tempfile.TemporaryDirectory() as d:
            self._run_sintetico(d, com_timing=False)
            jp = naming.jsonl_path("main", "c154", "MMF1", 0, d)
            from datetime import datetime, timezone
            # a it 3 começa em t0+200 e loga o `timing` em t0+202 (ver
            # _run_sintetico); pôr a `decision` em t0+150 inverte a ordem.
            antes_do_timing = datetime.fromtimestamp(
                1_000_150.0, timezone.utc).isoformat(timespec="milliseconds")
            linhas = [json.loads(x) for x in open(jp, encoding="utf-8")]
            for r in linhas:                       # a it 3 (hard_stop, derivada)
                if r["rec"] == "decision" and r["it"] == 3:
                    r["ts"] = antes_do_timing
            with open(jp, "w", encoding="utf-8") as fh:
                for r in linhas:
                    fh.write(json.dumps(r) + "\n")
            rel = export.backfill_timing_from_jsonl(
                "main", "c154", "MMF1", 0, data_root=d)
            col = pq.read_table(rel["path"]).column("tempo_busca_s")
        self.assertEqual(rel["busca_anomalas"], 1)
        self.assertEqual(rel["busca_derivadas"], 0)
        self.assertIsNone(col[2].as_py())          # NULL, não 0.0 nem negativo
        self.assertTrue(all(v.as_py() >= 0 for v in col[:2]))


# ═══════════════════════════════════════════════════════════════════════════
#  SONDA canônica §17.2.2 + a 🔴 guarda de não-perturbação
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(HAS_STACK, SEM_STACK)
class TestSonda(unittest.TestCase):

    def test_carrega_o_artefato_real_e_confere_o_hash(self):
        from src.botorch_harness import load_sonda
        a = load_sonda("MMF1")
        self.assertEqual(a["S"], 2000)
        self.assertEqual(a["X"].shape, (2000, a["D"]))
        self.assertEqual(a["F"].shape, (2000, a["M"]))
        self.assertEqual(a["x_hash"], a["sidecar"]["x_hash"])
        self.assertEqual(a["f_hash"], a["sidecar"]["f_hash"])
        self.assertIs(load_sonda("MMF1"), a)          # cache por processo

    def test_artefato_ausente_para_e_loga(self):
        from src.botorch_harness import load_sonda
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                load_sonda("MMF1", data_root=d)

    def test_hash_divergente_para_e_loga(self):
        """A disciplina D63/D87: artefato adulterado NÃO passa."""
        import shutil
        from src import botorch_harness as H
        with tempfile.TemporaryDirectory() as d:
            sd = os.path.join(d, "sonda")
            os.makedirs(sd)
            for ext in (".parquet", ".manifest.json"):
                shutil.copy(os.path.join("data", "sonda", "sonda_MMF1" + ext),
                            os.path.join(sd, "sonda_MMF1" + ext))
            mp = os.path.join(sd, "sonda_MMF1.manifest.json")
            side = json.load(open(mp))
            side["x_hash"] = "0" * 64
            json.dump(side, open(mp, "w"))
            H._SONDA_CACHE.pop("MMF1", None)
            try:
                with self.assertRaises(RuntimeError):
                    H.load_sonda("MMF1", data_root=d)
            finally:
                H._SONDA_CACHE.pop("MMF1", None)

    def test_cadencia_k2_com_a_primeira(self):
        from src.botorch_harness import sonda_due
        devidas = [i for i in range(1, 13) if sonda_due(i)]
        self.assertEqual(devidas, [1, 2, 4, 6, 8, 10, 12])
        self.assertTrue(sonda_due(1))                 # SEMPRE a 1ª
        self.assertFalse(sonda_due(3))
        # (a ÚLTIMA é responsabilidade do runner, no ramo do hard-stop.)

    def test_guarda_de_rng_torch_restaura_o_stream(self):
        """🔴 O invariante de NÃO-PERTURBAÇÃO: consumir RNG dentro da guarda
        não desloca o stream que a busca vai usar em seguida."""
        from src.botorch_harness import preserve_all_rng, preserve_torch_rng
        torch.manual_seed(7)
        esperado = torch.rand(4)                       # o que a busca veria
        torch.manual_seed(7)
        with preserve_torch_rng():
            torch.rand(1000)                           # a instrumentação
        self.assertTrue(torch.equal(esperado, torch.rand(4)))
        torch.manual_seed(7)
        with preserve_all_rng():
            torch.rand(1000)
            np.random.rand(1000)
        self.assertTrue(torch.equal(esperado, torch.rand(4)))


@unittest.skipUnless(HAS_STACK, SEM_STACK)
class TestSnapshotBufferRetrofit(unittest.TestCase):

    def test_fe_treino_max_e_herdado_por_toda_linha(self):
        from src import export
        from src.botorch_harness import SnapshotBuffer
        buf = SnapshotBuffer()
        buf.set_fe_treino_max(41)
        buf.add_surrogate(export.surrogate_row(1, [0.1], mu=[1.0]))
        buf.add_surrogate(export.surrogate_row(1, [0.2], mu=[2.0],
                                               fe_treino_max=7))
        self.assertEqual([r["fe_treino_max"] for r in buf.surr_rows], [41, 7])

    def test_update_timing_completa_a_linha_da_geracao(self):
        from src.botorch_harness import SnapshotBuffer
        buf = SnapshotBuffer()
        buf.add_timing(1, n_acumulado=10, tempo_fit_s=0.5)
        buf.add_timing(2, n_acumulado=11, tempo_fit_s=0.6)
        buf.update_timing(1, tempo_busca_s=2.0, tempo_pred_sonda_s=0.3,
                          tempo_geracao_s=2.9)
        self.assertEqual(buf.timing_rows[0]["tempo_busca_s"], 2.0)
        self.assertIsNone(buf.timing_rows[1]["tempo_busca_s"])

    def test_update_timing_de_geracao_inexistente_falha_barulhento(self):
        from src.botorch_harness import SnapshotBuffer
        buf = SnapshotBuffer()
        buf.add_timing(1, n_acumulado=10, tempo_fit_s=0.5)
        with self.assertRaises(KeyError):
            buf.update_timing(99, tempo_busca_s=1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  DI-10 — mínimo comum do `<alg>_gen` e os `sigma_dict`
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(HAS_STACK, SEM_STACK)
class TestDI10(unittest.TestCase):

    def test_minimo_comum(self):
        from src.botorch_harness import di10_minimo_comum

        class _R:
            def __init__(self, f):
                self.f = np.asarray(f, dtype=np.float64)

        class _Bud:
            records = [_R([1.0, 5.0]), _R([2.0, 2.0]), _R([9.0, 9.0])]

        out = di10_minimo_comum(_Bud(), u_infill=[0.5, 0.5],
                                train_U=[[0.0, 0.0], [0.5, 0.6]])
        self.assertEqual(out["f_best"], [1.0, 2.0])   # melhor POR objetivo
        self.assertEqual(out["n_front1"], 2)          # o (9,9) é dominado
        self.assertAlmostEqual(out["dist_min_arquivo"], 0.1, places=9)

    def test_sigma_dict_dos_2_configs_documenta_a_decisao_do_n_baseline(self):
        """DI-11 item 2 / DEFS-c154 §D-4: `n_baseline` é N/A no JES — a torre
        decidiu logar `n_train` e DOCUMENTAR no `sigma_dict`. Este teste é o
        que impede a decisão de se perder num refactor."""
        from src.c154_jes import _sigma_dict as sd154
        from src.c262_qnehvi import _sigma_dict as sd262
        for sd in (sd154(), sd262()):
            for k in ("regime", "fe_treino_max", "mu_j", "sigma_j"):
                self.assertIn(k, sd)
        self.assertIn("PÓS-PRUNE", sd262()["jsonl_n_baseline"])
        alvo = sd154()["jsonl_n_baseline"]
        self.assertIn("AUSENTE POR DESENHO", alvo)
        self.assertIn("n_train", alvo)


# ═══════════════════════════════════════════════════════════════════════════
#  DI-11.3 — o teto de tempo DECORRIDO independente (lacuna D-8 do projetor)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(HAS_STACK, SEM_STACK)
class TestTetoWallClockDI113(unittest.TestCase):

    def test_elapsed_dispara_SEM_nenhuma_amostra_de_projecao(self):
        """O cerne do adendo: o projetor herdado só armava depois de 10
        amostras, então um problema de ~45 min/iteração furava um teto de 8h
        sem NUNCA projetar. O teste de `elapsed` fecha essa janela."""
        from src.c262_qnehvi import _WallClockProjector
        p = _WallClockProjector(max_wall_s=10.0, t0=time.time() - 100.0,
                                maxfe=100)
        self.assertEqual(len(p.samples), 0)           # projeção NÃO armada
        self.assertIsNone(p.projection_s(50))
        over, proj, elapsed, criterio = p.exceeded(50)
        self.assertTrue(over)
        self.assertEqual(criterio, "elapsed")
        self.assertIsNone(proj)                       # não houve projeção
        self.assertGreater(elapsed, 99.0)

    def test_nao_dispara_dentro_do_teto(self):
        from src.c262_qnehvi import _WallClockProjector
        p = _WallClockProjector(max_wall_s=10_000.0, t0=time.time() - 1.0,
                                maxfe=100)
        for n in range(10):
            p.add(n + 1, 1e-9, 1e-9)                  # fits desprezíveis
        over, _, _, criterio = p.exceeded(50)
        self.assertFalse(over)
        self.assertIsNone(criterio)

    def test_a_projecao_original_segue_funcionando(self):
        # regressão: o critério (1) não foi trocado pelo (2).
        from src.c262_qnehvi import _WallClockProjector
        p = _WallClockProjector(max_wall_s=100.0, t0=time.time(), maxfe=500)
        for n in range(10, 20):
            p.add(n, 1.0, 1.0)                        # c·n³ ⇒ projeção enorme
        over, proj, _, criterio = p.exceeded(20)
        self.assertTrue(over)
        self.assertEqual(criterio, "projecao")
        self.assertIsNotNone(proj)

    def test_sem_teto_nunca_dispara(self):
        from src.c262_qnehvi import _WallClockProjector
        p = _WallClockProjector(max_wall_s=None, t0=time.time() - 1e6,
                                maxfe=100)
        over, proj, _, criterio = p.exceeded(50)
        self.assertFalse(over)
        self.assertIsNone(criterio)


@unittest.skipUnless(HAS_STACK, SEM_STACK)
class TestModeloHP(unittest.TestCase):
    """`modelo_hp`/`mll_final` (DI-10/B1) — e a prova de que extraí-los NÃO
    perturba a busca (o gate central do retrofit)."""

    def _modelo(self):
        from src.c262_qnehvi import _build_models
        torch.manual_seed(0)
        return _build_models(torch.rand(12, 3, dtype=torch.float64),
                             torch.rand(12, 2, dtype=torch.float64))

    def test_fit_devolve_retries_e_modelo_hp(self):
        from src.c262_qnehvi import _fit_models
        n_retries, hp = _fit_models(self._modelo())
        self.assertIsInstance(n_retries, int)
        self.assertIn("mll_final", hp)
        self.assertIsInstance(hp["mll_final"], float)
        self.assertEqual(len(hp["por_objetivo"]), 2)
        for o in hp["por_objetivo"]:
            for k in ("lengthscale_min", "lengthscale_med", "lengthscale_max",
                      "outputscale", "noise"):
                self.assertIn(k, o)
            self.assertLessEqual(o["lengthscale_min"], o["lengthscale_max"])

    def test_extrair_o_mll_nao_desloca_o_rng_nem_o_modo_do_modulo(self):
        from src.c262_qnehvi import _modelo_hp
        from gpytorch.mlls import SumMarginalLogLikelihood
        from botorch.fit import fit_gpytorch_mll
        model = self._modelo()
        mll = SumMarginalLogLikelihood(model.likelihood, model)
        fit_gpytorch_mll(mll)
        modo, estado = mll.training, torch.get_rng_state().clone()
        _modelo_hp(model, mll)
        self.assertEqual(mll.training, modo)                    # modo restaurado
        self.assertTrue(torch.equal(estado, torch.get_rng_state()))  # RNG intacto


if __name__ == "__main__":
    unittest.main()
