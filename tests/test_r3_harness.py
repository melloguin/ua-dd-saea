"""Testes do cartão R3-00-harness — infra transversal standalone + camada ⑦.

Estilo herdado do R2-00: `unittest` puro, imports LOCAIS aos métodos (para o
skip funcionar no `python3` base) e `tempfile.TemporaryDirectory()` sempre que
tocar disco — nunca o `data/` real.

Disciplina anti-tautologia (precedente R2-00/c262): onde o teste confere uma
FÓRMULA, ele a re-materializa direto do numpy em vez de chamar o helper testado.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import numpy as np  # noqa: F401
    import pyarrow  # noqa: F401
    _HAS_STACK = True
except ImportError:
    _HAS_STACK = False

_SKIP = "numpy/pyarrow ausentes neste interpretador — rode no env-main"


# ══════════════════════════════════════════════════════════════════════════
#  naming — a camada ⑦ é ADITIVA (o risco: cobrar `final` de run online)
# ══════════════════════════════════════════════════════════════════════════

class TestNamingCamadaFinal(unittest.TestCase):
    """`FINAL_LAYER` fora de `LAYERS` — e é ESSE o ponto."""

    def test_LAYERS_segue_com_as_4_obrigatorias(self):
        from src import naming
        self.assertEqual(naming.LAYERS, ("real", "pop", "surrogate", "timing"))

    def test_ALL_LAYERS_inclui_final_e_LAYERS_nao(self):
        from src import naming
        self.assertNotIn("final", naming.LAYERS)
        self.assertIn("final", naming.ALL_LAYERS)
        self.assertEqual(naming.ALL_LAYERS, naming.LAYERS + ("final",))

    def test_check_layer_aceita_final_e_rejeita_invento(self):
        from src import naming
        self.assertEqual(naming.check_layer("final"), "final")
        self.assertEqual(naming.check_layer("real"), "real")
        with self.assertRaises(ValueError):
            naming.check_layer("surrogate_sonda")

    def test_layer_path_final_e_o_atalho_final_path_coincidem(self):
        from src import naming
        a = naming.layer_path("off", "b5r", "MMF1", 0, "final", "data")
        b = naming.final_path("off", "b5r", "MMF1", 0, "data")
        self.assertEqual(a, b)
        self.assertTrue(a.endswith("exp_off_b5r_MMF1_0__final.parquet"))

    def test_listas_de_saida_NAO_passam_a_cobrar_a_camada_final(self):
        """A regressão que a aditividade existe para impedir: se `final`
        entrasse em `LAYERS`, todo run ONLINE viraria 'incompleto' para
        sempre e a esteira idempotente o re-executaria em loop."""
        from src import naming
        fns = naming.layer_filenames("main", "c262", "MMF1", 0)
        outs = naming.output_filenames("main", "c262", "MMF1", 0)
        self.assertEqual(len(fns), 4)
        self.assertFalse(any("__final" in f for f in fns))
        self.assertFalse(any("__final" in f for f in outs))

    @unittest.skipUnless(_HAS_STACK, _SKIP)
    def test_is_run_done_ignora_a_camada_final(self):
        """Um run ONLINE com as 4 camadas continua 'pronto' (D58)."""
        from src import manifest, naming
        with tempfile.TemporaryDirectory() as dr:
            d = naming.run_dir("main", "algx", data_root=dr)
            os.makedirs(d, exist_ok=True)
            for fn in naming.output_filenames("main", "algx", "MMF1", 0):
                with open(os.path.join(d, fn), "wb") as fh:
                    fh.write(b"x")
            man = manifest.new_manifest("main", "algx", "MMF1", 0,
                                        status="ok", data_root=dr)
            manifest.write_manifest(man, dr)
            self.assertTrue(manifest.is_run_done("main", "algx", "MMF1", 0,
                                                 data_root=dr,
                                                 check_footers=False))
            # e a ⑦ ausente NÃO o torna "não pronto" (o ponto do teste)
            self.assertFalse(os.path.exists(
                naming.final_path("main", "algx", "MMF1", 0, dr)))

    def test_gcs_plan_targets_nao_planeja_a_camada_final(self):
        from src import gcs
        alvos = gcs.plan_targets("off", "b5r", "MMF1", 0, enable_bucket=True)
        self.assertNotIn("final", alvos)


# ══════════════════════════════════════════════════════════════════════════
#  Sementes (D62/D91/D22) e guardas de RNG (N.2.3)
# ══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestSeedsERng(unittest.TestCase):

    def test_iteration_seed_bit_a_bit_vs_SeedSequence(self):
        """Anti-tautologia: re-materializa a fórmula do D91 direto do numpy."""
        import numpy as np
        from src import standalone_harness as sh
        for base, alg_id, it, uso in ((0, 5, 1, 0), (42, 12, 7, 2),
                                      (28000, 3, 99, 1)):
            ss = np.random.SeedSequence((base, alg_id, it, uso))
            esperado = int(ss.generate_state(1, dtype=np.uint64)[0])
            self.assertEqual(sh.iteration_seed(base, alg_id, it, uso),
                             esperado)
            self.assertEqual(sh.iteration_seed(base, alg_id, it, uso,
                                               bits32=True),
                             esperado & 0xFFFFFFFF)

    def test_seed_base_aplica_o_offset_D22_so_em_e81_e_c149(self):
        from src import standalone_harness as sh
        self.assertEqual(sh.seed_base("e81", 7), 7000)
        self.assertEqual(sh.seed_base("c149", 7), 7000)
        for alg in ("c122", "b5r", "b5m", "c311", "moead_media"):
            self.assertEqual(sh.seed_base(alg, 7), 7)

    def test_preserve_global_rng_restaura_numpy_e_random(self):
        import random
        import numpy as np
        from src import standalone_harness as sh
        np_b, py_b = np.random.get_state(), random.getstate()
        with sh.preserve_global_rng():
            np.random.seed(1234)
            random.seed(1234)
            np.random.random(10)
        np_a, py_a = np.random.get_state(), random.getstate()
        self.assertEqual(np_b[0], np_a[0])
        self.assertTrue(np.array_equal(np_b[1], np_a[1]))
        self.assertEqual(py_b, py_a)

    def test_preserve_all_rng_restaura_tambem_o_torch(self):
        from src import standalone_harness as sh
        try:
            import torch
        except ImportError:
            self.skipTest("torch ausente (envelope b5/c311) — guarda degrada")
        antes = torch.get_rng_state().clone()
        with sh.preserve_all_rng():
            torch.manual_seed(999)
            torch.randn(5)
        self.assertTrue(torch.equal(antes, torch.get_rng_state()))

    def test_guarded_pymoo_minimize_contra_o_culpado_REAL(self):
        """N.2.3: `pymoo.minimize` re-semeia os RNGs GLOBAIS. A prova é contra
        um NSGA-II de verdade, não contra um mock."""
        import random
        import numpy as np
        from src import experiment, standalone_harness as sh
        try:
            from pymoo.algorithms.moo.nsga2 import NSGA2
        except ImportError:
            self.skipTest("pymoo ausente")
        prob = experiment._instantiate_problem("MMF1")
        np_b, py_b = np.random.get_state(), random.getstate()
        sh.guarded_pymoo_minimize(prob, NSGA2(pop_size=8), ("n_gen", 2),
                                  seed=1, verbose=False)
        np_a, py_a = np.random.get_state(), random.getstate()
        self.assertTrue(np.array_equal(np_b[1], np_a[1]))
        self.assertEqual(py_b, py_a)

    def test_a_guarda_restaura_MESMO_com_perturbacao_maxima(self):
        """Prova MECÂNICA da guarda — e ela é necessária porque a prova
        "contra o pymoo real" é VACUAMENTE verde no env-main:

        MEDIDO nesta sessão: `pymoo 0.6.2` **não desloca** `np.random` nem
        `random` — nem com `seed=`, nem sem. A premissa do contrato R3 item 3
        ("`pymoo.minimize(seed=·)` re-semeia os GLOBAIS") vale para o **pymoo
        ANTIGO** dos venvs `env_b5`/`env_c311`, que é justamente onde b5/c311
        rodam e onde a guarda é indispensável. Rodar a prova só contra o pymoo
        moderno passaria mesmo que `preserve_global_rng` fosse um `pass`.

        Então provamos o MECANISMO: perturbamos de propósito lá dentro e
        exigimos a restauração bit-a-bit.
        """
        import random
        import numpy as np
        from src import standalone_harness as sh
        np.random.seed(7)
        random.seed(7)
        np_b, py_b = np.random.get_state(), random.getstate()
        with sh.preserve_global_rng():
            np.random.seed(999999)      # o que o pymoo antigo faz
            random.seed(999999)
            np.random.random(50)
            random.random()
        np_a, py_a = np.random.get_state(), random.getstate()
        self.assertTrue(np.array_equal(np_b[1], np_a[1]))
        self.assertEqual(np_b[2:], np_a[2:])
        self.assertEqual(py_b, py_a)

    def test_registro_do_comportamento_do_pymoo_desta_versao(self):
        """Sentinela de versão: se um upgrade de pymoo voltar a mexer nos
        globais, este teste falha e o `handoff` volta a valer literalmente."""
        import random
        import numpy as np
        from src import experiment
        try:
            import pymoo
            from pymoo.algorithms.moo.nsga2 import NSGA2
            from pymoo.optimize import minimize
        except ImportError:
            self.skipTest("pymoo ausente")
        if pymoo.__version__ != "0.6.2":
            self.skipTest(f"sentinela escrita p/ pymoo 0.6.2 "
                          f"(instalado: {pymoo.__version__})")
        prob = experiment._instantiate_problem("MMF1")
        np_b, py_b = np.random.get_state()[1].copy(), random.getstate()
        minimize(prob, NSGA2(pop_size=8), ("n_gen", 2), seed=1, verbose=False)
        self.assertTrue(np.array_equal(np_b, np.random.get_state()[1]),
                        "pymoo 0.6.2 passou a deslocar np.random — reavaliar "
                        "o N.2.3 e o gate R3-00")
        self.assertEqual(py_b, random.getstate())


# ══════════════════════════════════════════════════════════════════════════
#  Artefatos: dataset offline (D90) e sonda (§17.2.2)
# ══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestArtefatos(unittest.TestCase):

    def _repo_data(self):
        return os.path.join(ROOT, "data")

    def test_load_dataset_ausente_levanta_FileNotFound(self):
        from src import standalone_harness as sh
        with tempfile.TemporaryDirectory() as dr:
            with self.assertRaises(FileNotFoundError):
                sh.load_dataset("MMF1", 0, data_root=dr)

    def test_load_dataset_com_hash_corrompido_para_e_loga(self):
        """CP-init OFFLINE: corrompe o `f_hash` do sidecar e exige o D81. É o
        `f_hash` de propósito — é ele que o CP online NÃO cobre."""
        import json
        import shutil
        from src import naming, standalone_harness as sh
        with tempfile.TemporaryDirectory() as dr:
            shutil.copytree(os.path.join(self._repo_data(), "datasets"),
                            os.path.join(dr, "datasets"))
            mp = naming.dataset_manifest_path("MMF1", 0, data_root=dr)
            side = json.load(open(mp, encoding="utf-8"))
            side["f_hash"] = "0" * 64
            json.dump(side, open(mp, "w", encoding="utf-8"))
            with self.assertRaises(RuntimeError):
                sh.load_dataset("MMF1", 0, data_root=dr)

    def test_load_sonda_equivale_ao_gemeo_do_botorch_harness(self):
        """Os dois loaders existem porque a R3 roda em venvs SEM torch. Este
        teste é o que impede que divirjam silenciosamente."""
        import numpy as np
        from src import standalone_harness as sh
        try:
            from src import botorch_harness as bh
        except ImportError:
            self.skipTest("stack R2 (torch) ausente")
        a = sh.load_sonda("MMF1", data_root=self._repo_data())
        b = bh.load_sonda("MMF1", data_root=self._repo_data())
        self.assertTrue(np.array_equal(a["X"], b["X"]))
        self.assertTrue(np.array_equal(a["F"], b["F"]))
        self.assertEqual((a["x_hash"], a["f_hash"]), (b["x_hash"], b["f_hash"]))
        self.assertEqual(a["S"], 2000)

    def test_sonda_due_cadencia_online_k2(self):
        from src import standalone_harness as sh
        self.assertEqual([sh.sonda_due(i) for i in range(1, 8)],
                         [True, True, False, True, False, True, False])


# ══════════════════════════════════════════════════════════════════════════
#  Regime OFFLINE — o orçamento É o dataset
# ══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestRegimeOffline(unittest.TestCase):

    def test_orcamento_nasce_esgotado_e_a_1_e_o_dataset(self):
        import numpy as np
        from src import standalone_harness as sh
        bud, ds = sh.load_offline_budget("MMF1", 0,
                                         data_root=os.path.join(ROOT, "data"))
        self.assertEqual(bud.fe, bud.maxfe)
        self.assertEqual(bud.fe, 31 * ds["D"] - 1)
        self.assertTrue(bud.exhausted)
        X = np.vstack([r.x for r in bud.records])
        F = np.vstack([r.f for r in bud.records])
        self.assertTrue(np.array_equal(X, ds["X"]))
        self.assertTrue(np.array_equal(F, ds["F"]))
        self.assertEqual({r.fase for r in bud.records}, {"init"})

    def test_FE_na_busca_vira_OfflineBudgetViolation_e_nao_termino(self):
        """A distinção que importa: no ONLINE `BudgetExhausted` é o fim NORMAL
        (D61); no OFFLINE é prova de que o desenho está errado."""
        import numpy as np
        from src import budget, standalone_harness as sh
        bud, ds = sh.load_offline_budget("MMF1", 0,
                                         data_root=os.path.join(ROOT, "data"))
        with self.assertRaises(sh.OfflineBudgetViolation):
            with sh.offline_guard(alg="b5r", problema="MMF1"):
                bud.evaluate(np.full(ds["D"], 0.123456789),
                             lambda x: np.zeros(ds["M"]))
        self.assertTrue(issubclass(sh.OfflineBudgetViolation, RuntimeError))
        self.assertFalse(issubclass(sh.OfflineBudgetViolation,
                                    budget.BudgetExhausted))

    def test_cache_hit_do_dataset_custa_0_FE_mesmo_esgotado(self):
        from src import standalone_harness as sh
        bud, ds = sh.load_offline_budget("MMF1", 0,
                                         data_root=os.path.join(ROOT, "data"))
        fe0, hits0 = bud.fe, bud.cache_hits
        bud.evaluate(ds["X"][5], lambda x: None)
        self.assertEqual(bud.fe, fe0)
        self.assertEqual(bud.cache_hits, hits0 + 1)


# ══════════════════════════════════════════════════════════════════════════
#  Instrumentação: DI-10 e o buffer das camadas
# ══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestInstrumentacao(unittest.TestCase):

    def test_n_front1_usa_len_e_nao_count_nonzero(self):
        """Regressão da armadilha A-8 herdada do retrofit R2: `_nds_filter`
        devolve ÍNDICES. Aqui o índice 0 ESTÁ no front — `count_nonzero` o
        descartaria e devolveria 2 em vez de 3, silenciosamente."""
        import numpy as np
        from src import problems, standalone_harness as sh
        F = np.array([[0.0, 3.0], [1.0, 1.0], [3.0, 0.0], [5.0, 5.0]])
        idx = problems._nds_filter(F)
        self.assertIn(0, list(map(int, idx)))          # o índice 0 é ND
        self.assertEqual(int(np.count_nonzero(idx)), 2)   # a armadilha
        self.assertEqual(sh.minimo_comum_di10(F, fe=10)["n_front1"], 3)

    def test_minimo_comum_traz_os_campos_do_contrato(self):
        import numpy as np
        from src import standalone_harness as sh
        d = sh.minimo_comum_di10(np.array([[1.0, 2.0], [0.5, 3.0]]), fe=61,
                                 modelo_hp={"theta": 1.0}, tempo_fit_s=0.5,
                                 tempo_busca_s=0.25, dist_min_arquivo=0.01)
        for k in ("fe", "f_best", "n_front1", "modelo_hp", "tempo_fit_s",
                  "tempo_busca_s", "dist_min_arquivo"):
            self.assertIn(k, d)
        self.assertEqual(d["f_best"], [0.5, 2.0])

    def test_minimo_comum_nao_desloca_o_rng(self):
        import numpy as np
        from src import standalone_harness as sh
        antes = np.random.get_state()[1].copy()
        sh.minimo_comum_di10(np.random.default_rng(0).random((20, 2)), fe=1)
        self.assertTrue(np.array_equal(antes, np.random.get_state()[1]))

    def test_buffer_aceita_tempo_fit_None_para_os_pisos(self):
        """CONTRATO §4: 'Pisos: ④ por geração com tempo_geracao_s (fit=NULL)'."""
        from src import standalone_harness as sh
        buf = sh.SnapshotBuffer()
        buf.add_timing(geracao=1, n_acumulado=20, tempo_fit_s=None,
                       tempo_busca_s=0.5, tempo_geracao_s=0.7)
        self.assertIsNone(buf.timing_rows[0]["tempo_fit_s"])

    def test_update_timing_em_geracao_inexistente_falha_barulhento(self):
        from src import standalone_harness as sh
        buf = sh.SnapshotBuffer()
        buf.add_timing(geracao=1, n_acumulado=1, tempo_fit_s=0.1)
        with self.assertRaises(KeyError):
            buf.update_timing(9, tempo_busca_s=0.2)

    def test_linha_da_3_herda_o_fe_treino_max_corrente(self):
        from src import export, standalone_harness as sh
        buf = sh.SnapshotBuffer()
        buf.set_fe_treino_max(60)
        buf.add_surrogate(export.surrogate_row(1, [0.1, 0.2], mu=[1.0, 2.0]))
        self.assertEqual(buf.surr_rows[0]["fe_treino_max"], 60)
        # a linha que traz o SEU valor não é sobrescrita
        buf.add_surrogate(export.surrogate_row(1, [0.3, 0.4], mu=[1.0, 2.0],
                                               fe_treino_max=7))
        self.assertEqual(buf.surr_rows[1]["fe_treino_max"], 7)


# ══════════════════════════════════════════════════════════════════════════
#  Camada ⑦ (DI-08)
# ══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestCamadaFinal(unittest.TestCase):

    def test_write_final_schema_e_nd_pos_real_calculado(self):
        import numpy as np
        import pyarrow.parquet as pq
        from src import naming, standalone_harness as sh
        X = np.array([[0.1, 0.2], [0.3, 0.4], [0.9, 0.9]])
        F = np.array([[0.0, 3.0], [1.0, 1.0], [5.0, 5.0]])
        with tempfile.TemporaryDirectory() as dr:
            os.makedirs(naming.run_dir("off", "b5r", data_root=dr))
            p = sh.write_final("off", "b5r", "MMF1", 0, X, F, data_root=dr)
            t = pq.read_table(p)
            self.assertTrue(pq.read_schema(p).remove_metadata().equals(
                sh.final_schema(2, 2), check_metadata=False))
            self.assertEqual(t.column("nd_pos_real").to_pylist(),
                             [True, True, False])
            self.assertEqual(t.num_rows, 3)

    def test_write_final_vazio_para_e_loga(self):
        import numpy as np
        from src import naming, standalone_harness as sh
        with tempfile.TemporaryDirectory() as dr:
            os.makedirs(naming.run_dir("off", "b5r", data_root=dr))
            with self.assertRaises(ValueError):
                sh.write_final("off", "b5r", "MMF1", 0,
                               np.zeros((0, 2)), np.zeros((0, 2)),
                               data_root=dr)


# ══════════════════════════════════════════════════════════════════════════
#  Subprocess-por-venv (D79 / N.2) — o mecanismo que separa b5 × c311
# ══════════════════════════════════════════════════════════════════════════

class TestSubprocessPorVenv(unittest.TestCase):

    def test_b5_e_c311_resolvem_para_ENVS_DISTINTOS(self):
        """O achado nº 1 do contrato R3: os dois vendorizam `desdeo_*` com o
        mesmo nome e código diferente. Mesmo env ⇒ o `sys.modules` entrega o
        pacote errado SEM ERRO."""
        from src import standalone_harness as sh
        envs = {a: sh.interpreter_for_alg(a)[0]
                for a in ("b5r", "b5m", "c311", "moead_media")}
        self.assertNotEqual(envs["b5r"], envs["c311"])
        self.assertNotEqual(envs["b5m"], envs["c311"])
        self.assertEqual(envs["b5r"], envs["b5m"])

    def test_os_6_configs_R3_tem_env_declarado(self):
        from src import standalone_harness as sh
        for alg in ("c122", "c149", "e81", "b5r", "b5m", "c311",
                    "moead_media"):
            env_id, interp = sh.interpreter_for_alg(alg)
            self.assertTrue(env_id and interp, alg)

    def test_alg_desconhecido_levanta_KeyError(self):
        from src import standalone_harness as sh
        with self.assertRaises(KeyError):
            sh.interpreter_for_alg("nao_existe")

    def test_child_env_pina_as_4_vars_D79_e_aplica_env_flags(self):
        from src import standalone_harness as sh
        e = sh.child_env(env_id="env_c311", base={"PATH": "/usr/bin"})
        for v in sh.D79_THREAD_VARS:
            self.assertEqual(e[v], "1")
        self.assertEqual(e.get("MPLBACKEND"), "Agg")   # env_flags do c311

    def test_interpretador_inexistente_e_erro_de_CONFIGURACAO(self):
        from src import standalone_harness as sh
        with self.assertRaises(FileNotFoundError):
            sh.run_in_venv("c122", "MMF1", 0,
                           interpreter="/nao/existe/python")

    def test_protocolo_de_resultado_sobrevive_ao_ruido_do_stdout(self):
        """Os drivers de b5/c311 imprimem à vontade; o resultado viaja entre
        sentinelas para não se confundir com esse ruído."""
        from src import standalone_harness as sh
        ruido = ("Training GPR...\nWARNING: bla\n"
                 f"{sh._RESULT_BEGIN}\n" '{"ok": true, "result": {"fe": 61}}'
                 f"\n{sh._RESULT_END}\n" "done.\n")
        self.assertEqual(sh._parse_child_result(ruido),
                         {"ok": True, "result": {"fe": 61}})
        self.assertIsNone(sh._parse_child_result("sem sentinela nenhuma"))


# ══════════════════════════════════════════════════════════════════════════
#  Wiring do despacho
# ══════════════════════════════════════════════════════════════════════════

class TestWiring(unittest.TestCase):

    def test_stubr3_registrado_com_stack_standalone(self):
        from src import experiment
        self.assertEqual(experiment._DISPATCH_LOADERS["stubr3"],
                         ("src.standalone_harness", "run_stubr3",
                          "standalone"))

    def test_dispatch_continua_VAZIO_no_import(self):
        """O check do F0-01 ('dispatch vazio') tem de seguir verde: o registro
        é LAZY, senão o módulo deixa de importar no `python3` base."""
        import subprocess
        out = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, %r);"
             "from src import experiment;"
             "print(len(experiment.ALGORITHM_DISPATCH))" % ROOT],
            capture_output=True, text=True, cwd=ROOT, check=True)
        self.assertEqual(out.stdout.strip(), "0")


if __name__ == "__main__":
    unittest.main()


# ══════════════════════════════════════════════════════════════════════════
#  REGRESSÕES da revisão adversarial (7 achados confirmados)
# ══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestRegressoesRevisao(unittest.TestCase):

    def test_VENV_ONLY_cobre_os_4_configs_de_overlay(self):
        """N.1.2 deixou de ser convenção em comentário e virou mecanismo:
        `experiment.run` ROTEIA estes algs para o subprocesso."""
        from src import standalone_harness as sh
        self.assertEqual(set(sh.VENV_ONLY_ALGS),
                         {"b5r", "b5m", "moead_media", "c311"})

    def test_sentinela_de_overlay_ABORTA_em_raizes_distintas(self):
        """O 'pior achado' do contrato R3: dois `desdeo_emo` homônimos no mesmo
        processo. Sem a sentinela, o 2º run recebe as classes do 1º em
        silêncio; com ela, o run MORRE."""
        import types
        from src import standalone_harness as sh
        sh._OVERLAY_SEEN.clear()
        try:
            m1 = types.ModuleType("desdeo_emo")
            m1.__file__ = "/raiz/b5/desdeo_emo/__init__.py"
            sys.modules["desdeo_emo"] = m1
            sh.assert_overlay_coerente()               # 1ª vez: registra
            sh.assert_overlay_coerente()               # idem raiz: ok
            m2 = types.ModuleType("desdeo_emo")
            m2.__file__ = "/raiz/c311/desdeo_emo/__init__.py"
            sys.modules["desdeo_emo"] = m2
            with self.assertRaises(RuntimeError):
                sh.assert_overlay_coerente()
        finally:
            sys.modules.pop("desdeo_emo", None)
            sh._OVERLAY_SEEN.clear()

    def test_experiment_run_roteia_venv_only_para_subprocesso(self):
        """Prova do ROTEAMENTO sem provisionar env_b5: o roteamento tem de
        acontecer ANTES do despacho in-process — aqui ele falha por
        interpretador ausente, e é justamente isso que mostra que passou pelo
        caminho do venv em vez de importar b5 neste processo."""
        from src import experiment, standalone_harness as sh
        experiment._DISPATCH_LOADERS["b5r"] = (
            "src.standalone_harness", "run_stubr3", "standalone")
        try:
            with self.assertRaises((FileNotFoundError, RuntimeError)) as cm:
                experiment.run("b5r", "MMF1", 0, exp="off")
            self.assertNotIsInstance(cm.exception, NotImplementedError)
        finally:
            experiment._DISPATCH_LOADERS.pop("b5r", None)
            experiment.ALGORITHM_DISPATCH.pop("b5r", None)
        self.assertIn("b5r", sh.VENV_ONLY_ALGS)

    def test_in_child_corta_a_recursao_do_roteamento(self):
        """O bootstrap do filho reentra em `experiment.run`; sem `_in_child` o
        filho re-despacharia para outro filho, para sempre."""
        from src import standalone_harness as sh
        self.assertIn("_in_child=True", sh._CHILD_BOOTSTRAP)
        self.assertIn("pin_filho", sh._CHILD_BOOTSTRAP)

    def test_run_in_venv_com_interpreter_preserva_env_id_e_flags(self):
        """`interpreter=` sobrescreve o BINÁRIO, nunca a identidade do env —
        senão os `env_flags` (MPLBACKEND=Agg do c311) sumiam."""
        from src import standalone_harness as sh
        with self.assertRaises(FileNotFoundError) as cm:
            sh.run_in_venv("c311", "MMF1", 0, interpreter="/nao/existe/python")
        self.assertIn("env_c311", str(cm.exception))

    def test_sonda_de_SCORE_vai_para_pred_score_e_nao_para_mu(self):
        """Regressão do achado: o caminho escalar estourava no `vstack` e,
        contornado, gravava o score em `mu_0` — envenenando a ③."""
        import numpy as np
        from src import standalone_harness as sh

        class _Log:
            def event(self, *a, **k):
                pass

        sonda = {"X": np.linspace(0, 1, 1200).reshape(600, 2),
                 "x_hash": "a", "f_hash": "b"}
        buf = sh.SnapshotBuffer()
        # devolve 1-D (o formato do contrato) e força >1 chunk (600 > 512)
        def predict(Xq):
            n = Xq.shape[0]
            return np.full(n, 0.75), np.full(n, 0.9)
        sh.emit_sonda_block(buf, _Log(), geracao=3, fe=10, sonda=sonda,
                            predict=predict, fe_treino_max=5,
                            pred_tipo="score", modelo_flag="EDN")
        self.assertEqual(len(buf.surr_rows), 600)
        r = buf.surr_rows[0]
        self.assertEqual(r["pred_score"], 0.75)
        self.assertEqual(r["pred_confianca"], 0.9)
        self.assertIsNone(r["mu"])          # NUNCA em mu_*
        self.assertIsNone(r["sigma"])
        self.assertEqual(r["regime"], "sonda")

    def test_sonda_de_CLASSE_vai_para_pred_classe(self):
        import numpy as np
        from src import standalone_harness as sh

        class _Log:
            def event(self, *a, **k):
                pass

        sonda = {"X": np.zeros((4, 2)), "x_hash": "a", "f_hash": "b"}
        buf = sh.SnapshotBuffer()
        sh.emit_sonda_block(
            buf, _Log(), geracao=1, fe=0, sonda=sonda,
            predict=lambda Xq: (np.array(["bom"] * Xq.shape[0]),
                                np.full(Xq.shape[0], 0.83)),
            fe_treino_max=1, pred_tipo="classe", modelo_flag="FNN")
        self.assertEqual(buf.surr_rows[0]["pred_classe"], "bom")
        self.assertEqual(buf.surr_rows[0]["pred_confianca"], 0.83)
        self.assertIsNone(buf.surr_rows[0]["mu"])

    def test_sonda_recusa_pred_tipo_invalido(self):
        import numpy as np
        from src import standalone_harness as sh
        with self.assertRaises(ValueError):
            sh.emit_sonda_block(sh.SnapshotBuffer(), None, geracao=1, fe=0,
                                sonda={"X": np.zeros((2, 2)), "x_hash": "",
                                       "f_hash": ""},
                                predict=lambda X: (X, None), fe_treino_max=1,
                                pred_tipo="inventado")

    def test_sonda_recusa_predict_com_cardinalidade_errada(self):
        """A ordem/cardinalidade do artefato é o join posicional da R4."""
        import numpy as np
        from src import standalone_harness as sh

        class _Log:
            def event(self, *a, **k):
                pass
        with self.assertRaises(RuntimeError):
            sh.emit_sonda_block(sh.SnapshotBuffer(), _Log(), geracao=1, fe=0,
                                sonda={"X": np.zeros((4, 2)), "x_hash": "",
                                       "f_hash": ""},
                                predict=lambda X: (np.zeros(2), None),
                                fe_treino_max=1, pred_tipo="score")

    def test_nd_pos_real_e_reproduzivel_a_partir_do_ARQUIVO(self):
        """A coluna é computada sobre a vista float32 PERSISTIDA — quem reler a
        ⑦ recomputa exatamente o mesmo front."""
        import numpy as np
        import pyarrow.parquet as pq
        from src import naming, problems, standalone_harness as sh
        rng = np.random.default_rng(3)
        X = rng.random((40, 2))
        # F com empates a ~1e-9: é onde float64 × float32 divergiriam
        F = np.round(rng.random((40, 2)), 6)
        F[5] = F[4] + 1e-9
        with tempfile.TemporaryDirectory() as dr:
            os.makedirs(naming.run_dir("off", "b5r", data_root=dr))
            p = sh.write_final("off", "b5r", "MMF1", 0, X, F, data_root=dr)
            t = pq.read_table(p)
            nd = np.asarray(t.column("nd_pos_real").to_pylist(), dtype=bool)
            F_relido = np.column_stack(
                [np.asarray(t.column(f"f{j}"), dtype=np.float64)
                 for j in range(2)])
            nd_re = np.zeros(len(nd), dtype=bool)
            nd_re[list(map(int, problems._nds_filter(F_relido)))] = True
            self.assertTrue(np.array_equal(nd, nd_re))

    def test_write_final_grava_o_sidecar_de_procedencia(self):
        import json
        import numpy as np
        from src import naming, standalone_harness as sh
        with tempfile.TemporaryDirectory() as dr:
            os.makedirs(naming.run_dir("off", "b5r", data_root=dr))
            p = sh.write_final("off", "b5r", "MMF1", 0,
                               np.zeros((2, 2)), np.ones((2, 2)),
                               data_root=dr)
            with open(p[:-len(".parquet")] + ".manifest.json",
                      encoding="utf-8") as fh:
                side = json.load(fh)
            self.assertIn("float64", side["origem_precisao"])
            self.assertEqual(side["decisao"], "DI-08")

    def test_dual_write_sobe_a_camada_7_e_o_sidecar(self):
        """`gcs.plan_targets` itera `LAYERS` (sem a ⑦) — sem este trecho a
        camada sumiria com uma VM Vertex AI destruída."""
        import numpy as np
        from src import gcs, naming, standalone_harness as sh
        subidos = []
        with tempfile.TemporaryDirectory() as dr:
            os.makedirs(naming.run_dir("off", "b5r", data_root=dr))
            sh.write_final("off", "b5r", "MMF1", 0, np.zeros((2, 2)),
                           np.ones((2, 2)), data_root=dr)
            orig_mirror, orig_upload = gcs.mirror_run, gcs.upload
            orig_wm = sh._manifest.write_manifest
            gcs.mirror_run = lambda *a, **k: {}
            gcs.upload = lambda p, b, **k: subidos.append(os.path.basename(p))
            sh._manifest.write_manifest = lambda m, d: "/tmp/x.manifest.json"
            try:
                st = sh.dual_write_run("off", "b5r", "MMF1", 0,
                                       manifest_dict={}, data_root=dr)
            finally:
                gcs.mirror_run, gcs.upload = orig_mirror, orig_upload
                sh._manifest.write_manifest = orig_wm
        self.assertIn("exp_off_b5r_MMF1_0__final.parquet", subidos)
        self.assertIn("exp_off_b5r_MMF1_0__final.manifest.json", subidos)
        self.assertEqual(st["exp_off_b5r_MMF1_0__final.parquet"], "uploaded")

    def test_LACUNA_CONHECIDA_piso_com_fit_NULL_nao_e_gravavel(self):
        """SENTINELA de uma lacuna do CONTRATO §4, fora da minha faixa.

        O §4 manda: *"Pisos: ④ por geração com `tempo_geracao_s` (fit=NULL)"*.
        O `SnapshotBuffer` aceita `tempo_fit_s=None` (fiel ao contrato), mas o
        **escritor não consegue gravar**: `export.timing_schema()` declara
        `tempo_fit_s` com `nullable=False` e `export.write_timing` faz
        `float(r["tempo_fit_s"])` sem guarda. Conserto = 2 linhas em
        `src/export.py` — **faixa do retrofit-BoTorch**, por isso não o fiz.

        Atinge o cartão **piso-off** (`moead_media`) da R3 e os 4 pisos online.

        Este teste PINA a lacuna: quando `export.py` for corrigido, ele falha e
        avisa quem for atualizar o handoff/§4. Não é um teste de comportamento
        desejado — é um marcador de dívida com dono.
        """
        import tempfile as _tf
        from src import export, naming, standalone_harness as sh
        buf = sh.SnapshotBuffer()
        buf.add_timing(geracao=1, n_acumulado=20, tempo_fit_s=None,
                       tempo_busca_s=0.5, tempo_geracao_s=0.7)
        self.assertIsNone(buf.timing_rows[0]["tempo_fit_s"])
        self.assertFalse(export.timing_schema().field("tempo_fit_s").nullable)
        with _tf.TemporaryDirectory() as dr:
            os.makedirs(naming.run_dir("off", "moead_media", data_root=dr))
            with self.assertRaises(TypeError, msg=(
                    "export.write_timing passou a aceitar tempo_fit_s=None — "
                    "a lacuna do §4 (piso com fit=NULL) foi CORRIGIDA. "
                    "Remova esta sentinela e a pendência do handoff R3-00.")):
                export.write_timing("off", "moead_media", "MMF1", 0,
                                    buf.timing_rows, data_root=dr)
