"""Testes do avaliador pós-hoc da camada ⑦ — `scripts/final_eval.py` (DI-08).

Tudo roda sobre um run OFFLINE **sintético** montado à mão num tempdir (③ + ⑦
mínimas), sem depender de nenhum algoritmo — é a prova de que o avaliador e o
seu check funcionam para os 5 configs offline, inclusive o e103 (MATLAB, cuja
③ é a ÚNICA fonte).
"""

from __future__ import annotations

import importlib.util
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


def _load_final_eval():
    """`scripts/` não é pacote — carrega o módulo pelo caminho (mesmo recurso
    que o `accept.py` usa para não reimplementar a regra do DI-08)."""
    p = os.path.join(ROOT, "scripts", "final_eval.py")
    spec = importlib.util.spec_from_file_location("_final_eval_test", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_sintetico(dr, problema="MMF1", exp="off", alg="b5r", semente=0, *,
                   n_ger=3, n_pop=6, com_sonda=True):
    """Monta uma ③ sintética: `n_ger` gerações de busca + (opcional) um bloco
    de sonda. Devolve `(X_ultima_geracao, D, M)`.

    Os decs são reprodutíveis e dentro dos bounds nativos do problema.
    """
    import numpy as np
    from src import experiment, export, naming
    prob = experiment._instantiate_problem(problema)
    D, M = int(prob.n_var), int(prob.n_obj)
    xl = np.asarray(prob.xl, dtype=np.float64)
    xu = np.asarray(prob.xu, dtype=np.float64)
    rng = np.random.default_rng(0)
    os.makedirs(naming.run_dir(exp, alg, data_root=dr), exist_ok=True)

    rows, ultima = [], None
    for g in range(1, n_ger + 1):
        X = xl + rng.random((n_pop, D)) * (xu - xl)
        for i in range(n_pop):
            rows.append(export.surrogate_row(
                g, X[i], regime="offline", mu=np.zeros(M),
                sigma=np.ones(M), pred_tipo="valor", modelo_flag="fake",
                fe_treino_max=10))
        ultima = X
    if com_sonda:
        # a sonda entra na MESMA tabela, com `regime` por linha, e NÃO pode
        # ser confundida com o front final (é o ponto do filtro do avaliador).
        Xs = xl + rng.random((25, D)) * (xu - xl)
        for i in range(25):
            rows.append(export.surrogate_row(
                n_ger, Xs[i], regime="sonda", mu=np.zeros(M),
                pred_tipo="valor", modelo_flag="fake", fe_treino_max=10))
    export.write_surrogate(exp, alg, problema, semente, rows, D=D, M=M,
                           regime="offline", data_root=dr)
    return ultima, D, M


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestLeituraDaTerceira(unittest.TestCase):

    def test_ignora_as_linhas_de_SONDA_ao_achar_o_front_final(self):
        """A sonda partilha a tabela e a MESMA geração — confundi-la com o
        front final contaminaria a ⑦ com 2000 pontos de régua."""
        import numpy as np
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr, n_ger=3, n_pop=6, com_sonda=True)
            cand = fe.read_final_candidates("off", "b5r", "MMF1", 0,
                                            data_root=dr)
            self.assertEqual(cand["geracao"], 3)
            self.assertEqual(cand["X"].shape, (6, D))
            self.assertEqual(cand["n_sonda"], 25)
            self.assertTrue(np.allclose(
                cand["X"], X.astype(np.float32).astype(np.float64)))

    def test_3_so_com_sonda_para_e_loga(self):
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            _run_sintetico(dr, n_ger=0, n_pop=0, com_sonda=True)
            with self.assertRaises(RuntimeError):
                fe.read_final_candidates("off", "b5r", "MMF1", 0,
                                         data_root=dr)

    def test_3_ausente_para_e_loga(self):
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            with self.assertRaises(FileNotFoundError):
                fe.read_final_candidates("off", "b5r", "MMF1", 0,
                                         data_root=dr)


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestAvaliacaoEEscrita(unittest.TestCase):

    def test_avalia_fora_do_orcamento_e_com_o_problems_canonico(self):
        """O `f` da ⑦ é o do `problems.py` — o MESMO módulo que gerou o F do
        dataset (D90) e o gabarito da sonda. Nenhum FEBudget é envolvido."""
        import numpy as np
        from src import experiment, problems
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr)
            r = fe.final_eval_run("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertEqual(r["status"], "ok")
            import pyarrow.parquet as pq
            from src import naming
            t = pq.read_table(naming.final_path("off", "b5r", "MMF1", 0, dr))
            Xf = np.column_stack([np.asarray(t.column(f"x{j}"),
                                             dtype=np.float64)
                                  for j in range(D)])
            Ff = np.column_stack([np.asarray(t.column(f"f{j}"),
                                             dtype=np.float64)
                                  for j in range(M)])
            esperado = problems.evaluate_problem(
                experiment._instantiate_problem("MMF1"), Xf)
            self.assertTrue(np.allclose(Ff, esperado, rtol=1e-5, atol=1e-6))

    def test_e_determinístico_e_idempotente(self):
        """Duas execuções ⇒ bytes idênticos; sem `--force` a 2ª pula."""
        fe = _load_final_eval()
        from src import naming
        with tempfile.TemporaryDirectory() as dr:
            _run_sintetico(dr)
            fe.final_eval_run("off", "b5r", "MMF1", 0, data_root=dr)
            p = naming.final_path("off", "b5r", "MMF1", 0, dr)
            with open(p, "rb") as fh:
                b1 = fh.read()
            r2 = fe.final_eval_run("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertEqual(r2["status"], "skip")
            r3 = fe.final_eval_run("off", "b5r", "MMF1", 0, data_root=dr,
                                   force=True)
            self.assertEqual(r3["status"], "ok")
            with open(p, "rb") as fh:
                self.assertEqual(b1, fh.read())

    def test_grava_o_sidecar_com_a_procedencia(self):
        import json
        fe = _load_final_eval()
        from src import naming
        with tempfile.TemporaryDirectory() as dr:
            _run_sintetico(dr)
            fe.final_eval_run("off", "b5r", "MMF1", 0, data_root=dr)
            p = naming.final_path("off", "b5r", "MMF1", 0, dr)
            with open(p[:-len(".parquet")] + ".manifest.json",
                      encoding="utf-8") as fh:
                side = json.load(fh)
            self.assertEqual(side["decisao"], "DI-08")
            self.assertTrue(side["fora_do_orcamento"])
            self.assertIn("float32", side["origem_precisao"])

    def test_dec_fora_dos_bounds_para_e_loga(self):
        import numpy as np
        fe = _load_final_eval()
        with self.assertRaises(RuntimeError):
            fe.evaluate_final("MMF1", np.array([[99.0, 99.0]]))


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestCheckDaCamadaFinal(unittest.TestCase):

    def test_check_verde_no_caminho_feliz(self):
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            _run_sintetico(dr)
            fe.final_eval_run("off", "b5r", "MMF1", 0, data_root=dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertTrue(ok, msg)

    def test_check_pega_a_7_AUSENTE(self):
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            _run_sintetico(dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertFalse(ok)
            self.assertIn("ausente", msg)

    def test_check_pega_f_que_NAO_e_o_verdadeiro(self):
        """O defeito que a ⑦ existe para impedir: gravar como `f` o valor do
        SURROGATE em vez do valor real."""
        import numpy as np
        fe = _load_final_eval()
        from src import standalone_harness as sh
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr)
            sh.write_final("off", "b5r", "MMF1", 0, X,
                           np.zeros((X.shape[0], M)),   # "predição" fajuta
                           data_root=dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertFalse(ok)
            self.assertIn("INCONSISTENTE", msg)

    def test_check_pega_a_7_IRRECONSTITUIVEL_da_3(self):
        """REGRESSÃO do defeito encontrado na prova deste cartão: a ⑦ escrita
        a partir da PROLE da última geração — pontos que a ③ nunca registrou.

        As duas camadas ficam bem-formadas, o `f` É o verdadeiro daqueles `x`,
        e mesmo assim o run está errado: ninguém consegue reconstituir a ⑦, e
        para o e103 (cuja ③ é a única fonte) o retroativo avaliaria OUTRO
        conjunto. Sem este check o erro é silencioso.
        """
        import numpy as np
        fe = _load_final_eval()
        from src import experiment, problems, standalone_harness as sh
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr)
            prole = np.clip(X + 0.05, 0.0, 1.0)          # NUNCA foi para a ③
            F = problems.evaluate_problem(
                experiment._instantiate_problem("MMF1"), prole)
            sh.write_final("off", "b5r", "MMF1", 0, prole, F, data_root=dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertFalse(ok)
            self.assertIn("IRRECONSTITUÍVEL", msg)

    def test_check_pega_tamanho_divergente_entre_7_e_3(self):
        import numpy as np
        fe = _load_final_eval()
        from src import experiment, problems, standalone_harness as sh
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr, n_pop=6)
            sub = X[:3]
            F = problems.evaluate_problem(
                experiment._instantiate_problem("MMF1"), sub)
            sh.write_final("off", "b5r", "MMF1", 0, sub, F, data_root=dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertFalse(ok)
            self.assertIn("IRRECONSTITUÍVEL", msg)

    def test_check_pega_nd_pos_real_adulterado(self):
        import numpy as np
        fe = _load_final_eval()
        from src import experiment, problems, standalone_harness as sh
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr)
            F = problems.evaluate_problem(
                experiment._instantiate_problem("MMF1"), X)
            sh.write_final("off", "b5r", "MMF1", 0, X, F,
                           nd_pos_real=[True] * X.shape[0],   # todos ND: falso
                           data_root=dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertFalse(ok)
            self.assertIn("nd_pos_real", msg)


@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestGuardaDeEscopo(unittest.TestCase):

    def test_os_5_configs_offline_sao_os_do_contrato(self):
        from src import standalone_harness as sh
        self.assertEqual(set(sh.OFFLINE_CONFIGS),
                         {"e103", "b5r", "b5m", "c311", "moead_media"})

    def test_cli_recusa_config_online(self):
        import subprocess
        out = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "final_eval.py"),
             "--alg", "c262", "--problema", "MMF1"],
            capture_output=True, text=True, cwd=ROOT, check=False)
        self.assertEqual(out.returncode, 2)
        self.assertIn("não é config OFFLINE", out.stdout)


if __name__ == "__main__":
    unittest.main()


# ══════════════════════════════════════════════════════════════════════════
#  REGRESSÕES da revisão adversarial
# ══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(_HAS_STACK, _SKIP)
class TestRegressoesRevisao(unittest.TestCase):

    def test_tolerancia_de_bounds_acompanha_o_float32_MMF11_L(self):
        """🔴 O achado CRÍTICO. `MMF11_L` (xl=0.1, xu=1.1) é o único dos 25
        canônicos com bounds não representáveis em float32: `float32(1.1)` =
        1.100000023841858, que excede `xu` em 2,4e-8 — ~24× a tolerância fixa
        de 1e-9 que havia antes. Como clipar no bound é rotina de MOEA e TODO
        X que chega aqui passou por uma camada float32 (D53), a ⑦ de MMF11_L
        era rejeitada pelo próprio `--check` em ~28% das sementes."""
        import numpy as np
        from src import experiment
        fe = _load_final_eval()
        prob = experiment._instantiate_problem("MMF11_L")
        xu = np.asarray(prob.xu, dtype=np.float64)
        X = np.tile(xu, (3, 1)).astype(np.float32).astype(np.float64)
        self.assertTrue((X > xu).any(), "o caso-âncora exige X > xu")
        F = fe.evaluate_final("MMF11_L", X)      # não pode levantar
        self.assertEqual(F.shape[0], 3)

    def test_violacao_MATERIAL_de_bounds_ainda_para_e_loga(self):
        """A tolerância afrouxou para o ruído de armazenamento — não para
        solução inválida de verdade."""
        import numpy as np
        fe = _load_final_eval()
        with self.assertRaises(RuntimeError):
            fe.evaluate_final("MMF11_L", np.array([[5.0, 5.0]]))

    def test_check_final_DEVOLVE_veredito_e_nao_estoura(self):
        """Um check que levanta aborta o gate ANTES dos checks seguintes
        (manifesto, pinning, subprocesso nunca rodavam)."""
        import numpy as np
        from src import naming, standalone_harness as sh
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr)
            # ⑦ com X fora dos bounds ⇒ a reavaliação estoura lá dentro
            sh.write_final("off", "b5r", "MMF1", 0,
                           np.full((X.shape[0], D), 42.0),
                           np.zeros((X.shape[0], M)), data_root=dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertFalse(ok)
            self.assertIsInstance(msg, str)

    def test_7_pode_ser_SUBCONJUNTO_da_3_desde_que_aponte_origem_linha(self):
        """A invariante declarada é 'cada ponto da ⑦ ESTÁ na ③' — não
        'a ⑦ é a ③ inteira, na mesma ordem'. Um config que devolva só o
        subconjunto ND é legítimo e não pode levar vermelho."""
        import numpy as np
        from src import experiment, problems, standalone_harness as sh
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr, n_pop=6)
            X32 = X.astype(np.float32).astype(np.float64)
            sel = [4, 1, 0]                       # subconjunto E reordenado
            sub = X32[sel]
            F = problems.evaluate_problem(
                experiment._instantiate_problem("MMF1"), sub)
            sh.write_final("off", "b5r", "MMF1", 0, sub, F,
                           origem_geracao=[3] * len(sel), origem_linha=sel,
                           data_root=dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertTrue(ok, msg)

    def test_origem_linha_fora_do_intervalo_e_vermelho(self):
        import numpy as np
        from src import experiment, problems, standalone_harness as sh
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr, n_pop=6)
            X32 = X.astype(np.float32).astype(np.float64)
            F = problems.evaluate_problem(
                experiment._instantiate_problem("MMF1"), X32)
            sh.write_final("off", "b5r", "MMF1", 0, X32, F,
                           origem_geracao=[3] * 6,
                           origem_linha=[0, 1, 2, 3, 4, 99],   # 99 não existe
                           data_root=dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertFalse(ok)
            self.assertIn("origem_linha", msg)

    def test_a_PROLE_da_ultima_geracao_segue_sendo_vermelho(self):
        """O bug-alvo original continua morto depois do afrouxamento."""
        import numpy as np
        from src import experiment, problems, standalone_harness as sh
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr)
            prole = np.clip(X + 0.05, 0.0, 1.0)
            F = problems.evaluate_problem(
                experiment._instantiate_problem("MMF1"), prole)
            sh.write_final("off", "b5r", "MMF1", 0, prole, F, data_root=dr)
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertFalse(ok)
            self.assertIn("IRRECONSTITUÍVEL", msg)

    def test_check_exige_o_sidecar_de_procedencia(self):
        import os as _os
        import numpy as np
        from src import experiment, naming, problems, standalone_harness as sh
        fe = _load_final_eval()
        with tempfile.TemporaryDirectory() as dr:
            X, D, M = _run_sintetico(dr)
            X32 = X.astype(np.float32).astype(np.float64)
            F = problems.evaluate_problem(
                experiment._instantiate_problem("MMF1"), X32)
            p = sh.write_final("off", "b5r", "MMF1", 0, X32, F,
                               origem_geracao=[3] * X.shape[0],
                               origem_linha=list(range(X.shape[0])),
                               data_root=dr)
            _os.remove(p[:-len(".parquet")] + ".manifest.json")
            ok, msg = fe.check_final("off", "b5r", "MMF1", 0, data_root=dr)
            self.assertFalse(ok)
            self.assertIn("sidecar", msg)
