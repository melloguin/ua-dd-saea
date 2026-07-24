# -*- coding: utf-8 -*-
"""test_fio_sweep — [T7-sweep] trava o FIO do sweep de ponta a ponta.

Dois defeitos distintos, o mesmo fio:

1. 🔴 **Transporte quebrado (bug de LANÇAMENTO).** `experiment.run` repassava
   `**kwargs` cru a `run_in_venv`, cuja assinatura é de TRANSPORTE (só conhece
   exp/data_root/envs/interpreter/timeout/extra_kwargs/capture_output). Como
   `experiments.py` SEMPRE passa `enable_bucket`, todo run dos 4 configs
   venv-only (b5r/b5m/moead_media/c311) despachado pela bateria estourava
   `TypeError` — engolido pelo `except Exception` do despachante como 3 retries
   + `status='failed'`. Latente porque os cartões R3 chamaram os runners direto.

2. **O elo do sweep.** Ninguém derivava `(tier, dist)` do token
   `exp='sweep-<tier>-<dist>'`, então um run de sweep carregaria o dataset
   PRINCIPAL (small/lhs) e gravaria sob o nome do sweep — erro SILENCIOSO, que
   é a pior espécie: o CP-init passa (confere contra o arquivo que foi lido).

Estes testes não executam algoritmo: exercitam o ROTEAMENTO (que é onde os dois
bugs viviam) com um duplo de `run_in_venv`.
"""
import unittest
from unittest import mock

from src import experiment, naming


class TestTransporteVenvOnly(unittest.TestCase):
    """O que é transporte fica em run_in_venv; o resto desce por extra_kwargs."""

    def _captura(self, **kwargs):
        """Roda o roteamento com um duplo e devolve a chamada a run_in_venv."""
        falso = mock.Mock(return_value={"ok": True, "result": {"status": "ok"}})
        with mock.patch("src.standalone_harness.run_in_venv", falso):
            experiment.run("b5r", "MMF1", 0, **kwargs)
        self.assertEqual(falso.call_count, 1)
        return falso.call_args

    def test_enable_bucket_nao_estoura_e_desce_ao_runner(self):
        # A regressão exata do 🔴: isto levantava TypeError.
        args, kw = self._captura(exp="off", data_root="data",
                                 enable_bucket=False)
        self.assertEqual(args, ("b5r", "MMF1", 0))
        self.assertEqual(kw["exp"], "off")
        self.assertEqual(kw["data_root"], "data")
        # enable_bucket é do RUNNER, não do transporte:
        self.assertEqual(kw["extra_kwargs"], {"enable_bucket": False})
        self.assertNotIn("enable_bucket", kw)

    def test_kwargs_de_runner_novos_descem_sozinhos(self):
        # Drift-proof: um kwarg de runner que não existe hoje tem de atravessar
        # sem ninguém editar o transporte (a lição da DI-31).
        _, kw = self._captura(exp="sweep-medium-mvns", data_root="data",
                              enable_bucket=True, tier="medium", dist="mvns",
                              teto_s=60.0, q=1)
        self.assertEqual(kw["extra_kwargs"],
                         {"enable_bucket": True, "tier": "medium",
                          "dist": "mvns", "teto_s": 60.0, "q": 1})

    def test_kwargs_de_transporte_ficam_no_transporte(self):
        _, kw = self._captura(exp="off", data_root="data", timeout=90.0,
                              capture_output=False, enable_bucket=False)
        self.assertEqual(kw["timeout"], 90.0)
        self.assertIs(kw["capture_output"], False)
        self.assertEqual(kw["extra_kwargs"], {"enable_bucket": False})

    def test_sem_kwargs_de_runner_extra_kwargs_e_none(self):
        _, kw = self._captura(exp="off", data_root="data")
        self.assertIsNone(kw["extra_kwargs"])

    def test_online_nao_passa_por_run_in_venv(self):
        # c262 não é venv-only: o roteamento não pode desviar (e portanto o
        # caminho q=1 do principal segue intocado — prova de não-regressão).
        falso = mock.Mock()
        with mock.patch("src.standalone_harness.run_in_venv", falso), \
                mock.patch.dict(experiment.ALGORITHM_DISPATCH, {}, clear=True):
            with mock.patch.object(experiment, "_resolve_dispatch",
                                   return_value={"main": mock.Mock(
                                       return_value={"status": "ok"})}) as res:
                experiment.run("c262", "MMF1", 0, exp="main",
                               data_root="data", enable_bucket=False)
                # o runner recebeu os kwargs DIRETO, sem passar por extra_kwargs
                runner = res.return_value["main"]
                self.assertEqual(runner.call_args[0],
                                 ("main", "c262", "MMF1", 0))
                self.assertEqual(runner.call_args[1],
                                 {"data_root": "data", "enable_bucket": False})
        falso.assert_not_called()


class TestElooDoSweepChegaAoDataset(unittest.TestCase):
    """O `exp` do sweep vira (tier, dist) e escolhe o ARQUIVO certo."""

    def test_os_6_tokens_do_grid_resolvem_arquivo_distinto(self):
        # runs_matrix tem 6 tokens de sweep; small-lhs reusa o principal, os
        # outros 5 têm arquivo próprio. Se dois tokens colidissem no mesmo
        # arquivo, metade do sweep rodaria sobre os dados errados.
        vistos = {}
        for tier in naming.SWEEP_TIERS:
            for dist in naming.SWEEP_DISTS:
                exp = naming.sweep_exp(tier, dist)
                t, d = naming.dataset_variant(exp)
                vistos[exp] = naming.dataset_filename("MMF1", 42, t, d)
        self.assertEqual(vistos["sweep-small-lhs"], "ds_MMF1_42.parquet")
        self.assertEqual(len(set(vistos.values())), 6,
                         f"tokens colidindo no mesmo dataset: {vistos}")

    def test_off_e_sweep_small_lhs_leem_o_MESMO_arquivo(self):
        # D90/seeds.json: small/lhs É o offline principal. Não pode procurar
        # sufixo (o arquivo não existe em disco) — 150 runs quebrariam.
        self.assertEqual(naming.dataset_variant("off"),
                         naming.dataset_variant("sweep-small-lhs"))


class TestGateTierAware(unittest.TestCase):
    """O gate afere contra o |dataset| DA CÉLULA, não contra 31D−1 fixo."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        import os
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = importlib.util.spec_from_file_location(
            "_accept_t7", os.path.join(raiz, "scripts", "accept.py"))
        cls.accept = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.accept)
        cls.raiz = raiz

    def test_nao_sweep_continua_31D_menos_1(self):
        # Nenhuma mudança de comportamento fora do sweep (a suíte prova).
        for exp in ("main", "off", "batch"):
            n, origem = self.accept.n_dataset_esperado(exp, "MMF1", 42, 2)
            self.assertEqual(n, 61, f"{exp} deveria seguir 31D−1")
            self.assertIn("31D", origem)

    def test_sweep_small_lhs_reusa_o_principal(self):
        n, _ = self.accept.n_dataset_esperado("sweep-small-lhs", "MMF1", 42, 2)
        self.assertEqual(n, 61)

    def test_sweep_medium_le_o_n_do_SIDECAR_nao_hardcode(self):
        # O 2000 NÃO pode estar no gate: ele vem do sidecar do artefato.
        # (o dataset ds_MMF1_42_medium_lhs foi materializado no T7)
        import os
        from src import naming
        side = naming.dataset_manifest_path(
            "MMF1", 42, "medium", "lhs",
            data_root=os.path.join(self.raiz, "data"))
        if not os.path.exists(side):
            self.skipTest("dataset medium/lhs de MMF1/42 não materializado")
        n, origem = self.accept.n_dataset_esperado("sweep-medium-lhs", "MMF1",
                                                   42, 2)
        self.assertEqual(n, 2000)
        self.assertIn("sidecar", origem)
        # e é DIFERENTE do 31D−1 que o gate antigo exigiria — o bug que o T7 fecha
        self.assertNotEqual(n, self.accept.maxfe(2))

    def test_sidecar_ausente_reprova_com_motivo_honesto(self):
        # Nunca comparar contra um número inventado: sem sidecar, reprova.
        n, origem = self.accept.n_dataset_esperado(
            "sweep-big-mvns", "PROBLEMA_INEXISTENTE", 999, 2)
        self.assertIsNone(n)
        self.assertIn("sidecar", origem)


class TestParidadeMatlabPython(unittest.TestCase):
    """[T7-sweep] O fio do sweep existe em DOIS stacks — eles não podem derivar.

    `src/experiment.m` reimplementa `parse_sweep`/`is_main_variant`/o sufixo do
    dataset porque o MATLAB não importa `naming.py`. Duas implementações da mesma
    convenção é dívida: se alguém acrescentar um tier em `naming.py` e esquecer o
    `.m`, os 600 runs de e103 do sweep leem o arquivo errado EM SILÊNCIO. Estes
    testes leem o fonte `.m` e cobram a paridade do vocabulário e da regra
    `is_main`. (O comportamento em si é aferido pela regressão ao vivo do e103 —
    ①②③ bit-idênticas — registrada no handoff T7-sweep §4.5.)
    """

    @classmethod
    def setUpClass(cls):
        import os
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(raiz, "src", "experiment.m"),
                  encoding="utf-8") as fh:
            cls.m = fh.read()

    def test_o_m_tem_os_3_helpers_do_fio(self):
        for fn in ("nm_parse_sweep", "nm_is_main_variant", "nm_dataset_sufixo"):
            self.assertIn(f"function", self.m)
            self.assertIn(fn, self.m, f"{fn} ausente de src/experiment.m")

    def test_vocabulario_do_m_bate_com_o_do_naming(self):
        from src import naming
        # o .m declara o vocabulário em literais de cell array
        for t in naming.SWEEP_TIERS:
            self.assertIn(f"'{t}'", self.m,
                          f"tier {t!r} de naming.SWEEP_TIERS ausente do .m")
        for d in naming.SWEEP_DISTS:
            self.assertIn(f"'{d}'", self.m,
                          f"dist {d!r} de naming.SWEEP_DISTS ausente do .m")
        # e a lista literal tem de ter EXATAMENTE o mesmo conteúdo
        self.assertIn("{'small','medium','big'}", self.m)
        self.assertIn("{'lhs','mvns'}", self.m)
        self.assertEqual(naming.SWEEP_TIERS, ("small", "medium", "big"))
        self.assertEqual(naming.SWEEP_DISTS, ("lhs", "mvns"))

    def test_o_m_nao_crava_mais_31D_menos_1_no_e103(self):
        # run_e103 cravava `n_ds = 31*D - 1` ANTES de ler o artefato, o que
        # estourava o assert em medium/big. Agora o n vem de ds.n.
        self.assertIn("n_ds  = ds.n", self.m)
        self.assertNotIn("n_ds  = 31*D - 1", self.m)

    def test_o_m_nao_crava_mais_tier_small_no_manifesto(self):
        # `'tier', "small", 'dist', "lhs"` constante fazia o manifesto de um run
        # de sweep MENTIR — pior que falhar.
        self.assertNotIn("'tier', \"small\", 'dist', \"lhs\"", self.m)


if __name__ == "__main__":
    unittest.main()
