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
        # [DI-35.3] MMF1 -> MMF16_20 (paredes de D=2; padronizacao total do autor)
        self.assertEqual({r["problema"] for r in self.linhas},
                         {"MMF16_20", "ZDT1", "ZDT4", "DTLZ2", "WFG9"})

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


class TestTetoFiadoPeloDespachante(unittest.TestCase):
    """[T6-batch] `teto_s` do CLI ate o runner (autorizacao do autor, 2026-07-24).

    Os runners c311/e81 ja aceitavam `teto_s` e tratam o estouro como DADO
    (manifesto `failed`/`teto_wall` — D61/§22.5), mas `experiments.py` NUNCA o
    passava: o `_TetoWall` era codigo morto na bateria. Sem isto nao ha como
    dimensionar o batch (cujos smokes podem custar ordens de grandeza mais que
    o principal) nem aplicar o teto de 4 h decidido pelo autor.
    """

    def _adapter_kwargs(self, **kw):
        from unittest import mock
        import experiments
        falso = mock.Mock()
        with mock.patch.object(experiments, "_adapter") as ad:
            ad.run = falso
            experiments._run_one("batch", "e81", "ZDT4", 42, "data", **kw)
        return falso.call_args[1]

    def test_teto_s_chega_ao_runner(self):
        kw = self._adapter_kwargs(teto_s=14400.0)      # as 4 h do autor
        self.assertEqual(kw["teto_s"], 14400.0)

    def test_sem_teto_a_chave_NAO_e_passada(self):
        # Não pode injetar `teto_s=None` — runners que não conhecem a chave a
        # engoliriam no **_kwargs, mas os que a conhecem passariam a receber
        # um None explícito onde antes recebiam o default. Menos ruído: omitir.
        kw = self._adapter_kwargs()
        self.assertNotIn("teto_s", kw)

    def test_cli_expoe_teto_s(self):
        import experiments
        args = experiments._parse_args(["--exp", "batch", "--teto-s", "14400"]) \
            if hasattr(experiments, "_parse_args") else None
        if args is None:
            self.skipTest("parser não exposto isoladamente")
        self.assertEqual(args.teto_s, 14400.0)


class TestCalibracaoBatchT9(unittest.TestCase):
    """[T9/DI-35.1] Calibração POR MEDIÇÃO do custo da aquisição batch (q=10) p/
    ~10 h/run (o ponto ótimo do tradeoff tempo×qualidade do autor).

    Regra de ouro (a mesma da prova de regressão ①②③④): o knob age **SÓ** no
    batch (q>1). O caminho q=1 (experimento principal) mantém a receita CHEIA do
    paper — byte-idêntico ao pré-T9. Estes guardas travam os VALORES calibrados
    e a intocabilidade do q=1 na fonte única (`_restarts_raw_for_q`).
    """

    def test_c154_constantes_batch_calibradas(self):
        # 1D/50D = 10 restarts / 500 raw em D=10 (≈ o default do BoTorch 10/512).
        from src import c154_jes as m
        self.assertEqual(m.NUM_RESTARTS_PER_D_BATCH, 1)
        self.assertEqual(m.RAW_SAMPLES_PER_D_BATCH, 50)
        # a receita do PAPER fica intocada (q=1 a usa).
        self.assertEqual(m.NUM_RESTARTS_PER_D, 5)
        self.assertEqual(m.RAW_SAMPLES_PER_D, 1000)

    def test_c154_q1_receita_cheia_do_paper_intocada(self):
        # o principal (q=1) tem de sair 5D/1000D em QUALQUER D — a base da prova
        # de regressão bit-a-bit.
        from src import c154_jes as m
        for D in (2, 10, 12, 22, 30):
            self.assertEqual(m._restarts_raw_for_q(1, D), (5 * D, 1000 * D))

    def test_c154_batch_usa_receita_reduzida(self):
        from src import c154_jes as m
        for D in (2, 10, 12, 22, 30):
            self.assertEqual(m._restarts_raw_for_q(10, D), (1 * D, 50 * D))
        # ZDT4 (D=10) — a célula de calibração: 10 restarts / 500 raw.
        self.assertEqual(m._restarts_raw_for_q(10, 10), (10, 500))
        # q>1 é sempre reduzido; q=1 nunca (fronteira exata do knob).
        self.assertNotEqual(m._restarts_raw_for_q(2, 10),
                            m._restarts_raw_for_q(1, 10))

    def test_c154_call_site_usa_o_helper_nao_hardcode(self):
        # [T9 review] WIRING: o call site REAL (`_optimize_acqf_restarts`) tem de
        # PASSAR os valores do helper ao gen_batch_ic + optimize_acqf. Um hardcode
        # que ignorasse o helper (rodando o batch com a receita cheia) passaria os
        # outros testes (que só checam a aritmética do helper) mas falha AQUI —
        # este teste cruza o call site de fato.
        from unittest import mock
        from src import c154_jes as m
        cap = {}

        def fake_gen_ic(*a, **k):
            cap["gen"] = (k.get("num_restarts"), k.get("raw_samples"))
            return mock.MagicMock()

        def fake_opt(*a, **k):
            cap["opt"] = (k.get("num_restarts"), k.get("raw_samples"))
            return mock.MagicMock(), mock.MagicMock()

        with mock.patch("botorch.optim.initializers.gen_batch_initial_conditions",
                        fake_gen_ic), \
             mock.patch("botorch.optim.optimize_acqf", fake_opt):
            # q=1 (principal) ⇒ 5D/1000D em D=10 (byte-idêntico ao pré-T9)
            m._optimize_acqf_restarts(mock.MagicMock(), 10, mock.MagicMock(), 1,
                                      q=1)
            self.assertEqual(cap["gen"], (50, 10000))
            self.assertEqual(cap["opt"], (50, 10000))
            # q=10 (batch) ⇒ 1D/50D reduzido = 10/500 em D=10
            m._optimize_acqf_restarts(mock.MagicMock(), 10, mock.MagicMock(), 1,
                                      q=10)
            self.assertEqual(cap["gen"], (10, 500))
            self.assertEqual(cap["opt"], (10, 500))

    def test_c262_sem_reducao_batch_decisao_medida(self):
        # [T9] c262 medido ~2,2 h no batch cheio (<< 10 h) ⇒ NENHUM knob. Os
        # parâmetros da receita L.10 são os mesmos em q=1 e q>1 (MC é um dud; o
        # gargalo é RAM, não CPU). A AUSÊNCIA de constante batch é intencional.
        from src import c262_qnehvi as m
        self.assertEqual(m.MC_SAMPLES, 128)
        self.assertEqual(m.NUM_RESTARTS, 10)
        self.assertEqual(m.RAW_SAMPLES, 512)
        self.assertFalse(hasattr(m, "MC_SAMPLES_BATCH"),
                         "c262 não deve ganhar knob batch (decisão medida T9)")
        self.assertFalse(hasattr(m, "NUM_RESTARTS_BATCH"))


if __name__ == "__main__":
    unittest.main()


class TestProjetorBatchAware(unittest.TestCase):
    """[DI-36] O projetor de wall-clock tem de ser batch-aware: com q=10 as
    iterações futuras avançam ~q FEs — somar em passo 1 superestimava ~q× e
    abortaria espuriamente o batch do c262 (~2,2h reais > teto). Em q=1 a
    projeção fica BIT-IGUAL à fórmula original."""

    def _proj(self, passo, n0=100, k=12, t_fit=2.0, t_iter=5.0, maxfe=400):
        from src.c262_qnehvi import _WallClockProjector
        p = _WallClockProjector(3600.0, 0.0, maxfe)
        for i in range(k):
            p.add(n0 + i * passo, t_fit, t_iter)
        return p, n0 + (k - 1) * passo

    def test_q1_bit_igual_a_formula_original(self):
        import numpy as np
        p, n_now = self._proj(passo=1)
        recent = p.samples[-5:]
        c = float(np.mean([tf / max(n, 1) ** 3 for n, tf, _ in recent]))
        other = float(np.mean([ti - tf for n, tf, ti in recent]))
        ns = np.arange(n_now, p.maxfe + 1, dtype=np.float64)
        legado = float(c * np.sum(ns ** 3) + max(other, 0.0) * len(ns))
        self.assertEqual(p.projection_s(n_now), legado)

    def test_q10_projeta_por_iteracao_nao_por_fe(self):
        import numpy as np
        p10, n10 = self._proj(passo=10, n0=100, maxfe=400 + 9 * 11)
        proj_novo = p10.projection_s(n10)
        # a fórmula ANTIGA (passo 1 = 1 termo por FE — o bug): ~10× maior
        recent = p10.samples[-5:]
        c = float(np.mean([tf / max(n, 1) ** 3 for n, tf, _ in recent]))
        other = float(np.mean([ti - tf for n, tf, ti in recent]))
        ns1 = np.arange(n10, p10.maxfe + 1, dtype=np.float64)
        proj_bug = float(c * np.sum(ns1 ** 3) + max(other, 0.0) * len(ns1))
        self.assertLess(proj_novo, proj_bug / 5,
                        "o passo não foi inferido — projeção q=10 continua "
                        "somando 1 termo por FE (o bug do aborto espúrio)")
