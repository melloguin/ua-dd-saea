# -*- coding: utf-8 -*-
"""test_batch_q10 — [T6-batch] o contrato do sub-estudo batch q=10 (D66/D42).

Contrato (bundle `40_subestudos/batch_largebatch.md` + SPEC:831):
q=10 · `maxFE_batch = 11D−1 + K·q` com K=200 (2.000 infills) · DoE **pareado**
com o principal (o MESMO artefato 11D−1 — nunca gerado) · roster
c149/c262/e81/c154 + `sobol_batch` · 5 problemas · cada algoritmo usa o modo de
lote **NATIVO**, sem fallback livre.

A regra de ouro destes testes: **nada muda fora de `exp=batch`**. O caminho q=1
do experimento principal tem de sair bit-intocado (a prova bit-a-bit contra os
runs já validados está no handoff T6-batch).
"""
import unittest

from src import budget, naming


class TestOrcamentoPorExp(unittest.TestCase):

    def test_batch_e_11D_menos_1_mais_200q(self):
        # MMF1 (D=2): 11·2−1 + 200·10 = 21 + 2000 = 2021 — a célula dos smokes.
        self.assertEqual(budget.maxfe_por_exp("batch", 2, 10), 2021)
        # ZDT1 (D=30): 329 + 2000 = 2329
        self.assertEqual(budget.maxfe_por_exp("batch", 30, 10), 2329)
        # a parcela do DoE é EXATAMENTE o n_init do principal (DoE pareado)
        for D in (2, 10, 12, 22, 30):
            self.assertEqual(budget.maxfe_por_exp("batch", D, 10),
                             budget.n_init_for(D) + 2000)

    def test_K_e_200_e_nao_um_literal_solto(self):
        self.assertEqual(budget.K_BATCH, 200)
        self.assertEqual(budget.maxfe_por_exp("batch", 2, 1),
                         budget.n_init_for(2) + 200)

    def test_main_continua_31D_menos_1(self):
        # NENHUMA mudança fora do batch — o q é ignorado no principal.
        for D in (2, 10, 12, 22, 30):
            self.assertEqual(budget.maxfe_por_exp("main", D), budget.maxfe_for(D))
            self.assertEqual(budget.maxfe_por_exp("main", D, 10),
                             31 * D - 1)

    def test_offline_recusa_em_vez_de_devolver_numero_errado(self):
        # No offline o orçamento É o dataset (D90). Devolver 31D−1 aqui seria
        # exatamente o bug silencioso que o T7 fechou — então levanta.
        for exp in ("off", "sweep-medium-lhs", "sweep-big-mvns"):
            with self.assertRaises(ValueError, msg=f"{exp} deveria recusar"):
                budget.maxfe_por_exp(exp, 2, 1)

    def test_febudget_aceita_o_maxfe_do_batch(self):
        # O FEBudget continua parametrizável — quem manda é o runner.
        bud = budget.FEBudget(D=2, maxfe=budget.maxfe_por_exp("batch", 2, 10),
                              n_init=budget.n_init_for(2))
        self.assertEqual(bud.maxfe, 2021)
        self.assertEqual(bud.n_init, 21)
        self.assertEqual(bud.fe, 0)


class TestContratoDoGrid(unittest.TestCase):
    """O que o artefato do grid diz — a fonte da verdade do roster."""

    @classmethod
    def setUpClass(cls):
        import csv
        import os
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        p = os.path.join(raiz, "claude_code_context", "artifacts",
                         "runs_matrix.csv")
        with open(p, encoding="utf-8") as fh:
            cls.linhas = [r for r in csv.DictReader(fh) if r["exp"] == "batch"]

    def test_roster_do_batch_sao_os_5_configs(self):
        self.assertEqual({r["alg"] for r in self.linhas},
                         {"c149", "c154", "c262", "e81", "sobol_batch"})

    def test_todo_run_de_batch_tem_q_igual_10(self):
        self.assertEqual({r["q"] for r in self.linhas}, {"10"})

    def test_os_5_problemas_do_sub_estudo(self):
        self.assertEqual({r["problema"] for r in self.linhas},
                         {"MMF1", "ZDT1", "ZDT4", "DTLZ2", "WFG9"})

    def test_batch_nao_tem_tier_nem_dist(self):
        # batch é ONLINE — tier/dist são do sweep offline.
        for r in self.linhas:
            self.assertIn(r["tier"], ("", None))
            self.assertIn(r["dist"], ("", None))

    def test_exp_batch_e_token_estatico_valido(self):
        self.assertIn("batch", naming.STATIC_EXPS)
        self.assertTrue(naming.is_valid_exp("batch"))
        self.assertEqual(naming.parse_sweep("batch"), (None, None))


class TestAlgIdDoSobolBatch(unittest.TestCase):
    """O piso do batch precisa de alg_id próprio (DI-33 pré-provisionou o 22)."""

    @classmethod
    def setUpClass(cls):
        import json
        import os
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(raiz, "claude_code_context", "artifacts",
                               "seeds.json"), encoding="utf-8") as fh:
            cls.seeds = json.load(fh)

    def test_sobol_batch_tem_alg_id_22(self):
        self.assertEqual(self.seeds["alg_id"]["sobol_batch"], 22)

    def test_alg_id_do_sobol_batch_nao_colide(self):
        ids = self.seeds["alg_id"]
        self.assertEqual(len(set(ids.values())), len(ids),
                         "alg_id duplicado no seeds.json")


class TestRoteamentoDeEnvDoBatch(unittest.TestCase):
    """[T6-batch] 🔴 O e81 tem de rodar no env QUE VALIDOU o config.

    `VENV_ONLY_ALGS` era literal e cobria só os 4 configs do overlay `desdeo_*`;
    o `e81` ficava de fora **apesar de ter env próprio**. Efeito: a bateria
    despachada por `experiments.py` rodaria o e81 in-process no `env_main`
    (botorch **0.18.1**) enquanto os runs validados em
    `data/experiments/main/e81/` registram botorch **0.16.1** — stack diferente,
    sem erro e sem warning. Agora o conjunto é DERIVADO de `envs.json`.
    """

    def test_todo_alg_com_env_proprio_e_roteado(self):
        from src import standalone_harness as sh
        tabela = sh.load_env_table()["alg_to_env"]
        for alg, spec in tabela.items():
            if spec.get("stack") != "python":
                continue
            if spec.get("env") != "env_main":
                self.assertIn(alg, sh.VENV_ONLY_ALGS,
                              f"{alg} roda em {spec.get('env')} mas NÃO é "
                              f"roteado ⇒ rodaria com o stack errado")
            else:
                self.assertNotIn(alg, sh.VENV_ONLY_ALGS)

    def test_os_3_configs_batch_do_env_main_nao_pagam_subprocesso(self):
        from src import standalone_harness as sh
        for alg in ("c149", "c154", "c262"):
            self.assertNotIn(alg, sh.VENV_ONLY_ALGS)

    def test_e81_do_batch_resolve_para_o_env_pinado(self):
        from src import standalone_harness as sh
        env_id, _ = sh.interpreter_for_alg("e81")
        self.assertEqual(env_id, "env_e81_qpots")


if __name__ == "__main__":
    unittest.main()
