# -*- coding: utf-8 -*-
"""Testes do runner c311 TGPR-MO (OFFLINE, treed-GP/GPy).

TRÊS camadas, por dependência de ambiente:
  * `Test*` sem marcador — puros, rodam em QUALQUER env (a suíte env-main os pega).
  * `@skipUnless(VENDOR_OK)` — precisam do vendor c311 (GPy 1.9.9 + sklearn 1.1.2 +
    numpy 1.20.2) ⇒ SÓ no `env_c311`. Em env-main o import do GPy 1.9.9 falha e a
    classe é PULADA (o mesmo padrão do test_e81/test_c149: 7 skips na suíte env-main).
  * `@skipUnless(VENDOR_OK and SLOW)` — runs completos (constrói+otimiza); atrás de
    `C311_SLOW=1` para não pesar a suíte. Rodados no fechamento (env_c311).

Como rodar os pesados:
    C311_SLOW=1 MPLBACKEND=Agg <env_c311>/bin/python -m unittest tests.test_c311
"""
from __future__ import annotations

import os
import tempfile
import unittest

import numpy as np

from src import c311_tgprmo as C
from src import naming
from src import standalone_harness as H

SLOW = os.environ.get("C311_SLOW") == "1"


def _vendor_ok() -> bool:
    # Sonda LEVE e SEM efeito colateral (não mexe em sys.path/sys.modules): só o
    # env_c311 tem GPy 1.9.9 (env-main tem numpy 2.x, incompatível). Assim a suíte
    # env-main NUNCA dispara `_import_vendor` (que insere o overlay do vendor).
    try:
        import GPy  # noqa: F401
        return True
    except Exception:
        return False


VENDOR_OK = _vendor_ok()


def _trained_model(D: int = 2, n: int = 60, seed: int = 0, n_addgps: int = 3):
    """Constrói UMA `treeGP` (1 objetivo) treinada com alguns GPs — para os ganchos.

    Devolve `(model, X, F)`. Com `min_samples_leaf=10D` e `n` pequeno a árvore tem
    poucas folhas; após alguns `addGPs` há folhas COM GP e folhas SÓ-árvore ⇒ o mix
    exato que os testes de σ (real × NaN) exigem.
    """
    DataProblem, treeGP, RVEA, Base, CI = C._import_vendor()
    rng = np.random.default_rng(seed)
    X = rng.random((n, D))
    F = rng.random((n, 1))
    prob = C._build_surrogates(DataProblem, treeGP, X, F, np.zeros(D), np.ones(D))
    model = prob.objectives[0]._model
    for _ in range(n_addgps):
        model.addGPs(rng.random((30, D)))
    return model, X, F


def _link_artefatos(td: str) -> None:
    """Linka datasets/sonda do repo para um data_root temporário (offline não usa doe)."""
    for sub in ("datasets", "sonda"):
        os.symlink(os.path.join(H.ROOT, "data", sub), os.path.join(td, sub))


# ═══════════════════════════════════════════════════════════════════════════
#  Puros — rodam em env-main
# ═══════════════════════════════════════════════════════════════════════════

class TestPuros(unittest.TestCase):

    def test_identidade(self):
        self.assertEqual(C.ALG_ID, 19)                    # seeds.json:alg_id.c311
        self.assertIn("TGPR-MO", C.ALGO_VERSION)
        self.assertTrue(os.path.isdir(C.VENDOR_ROOT))

    def test_max_busca_geracao_ignora_sonda(self):
        buf = H.SnapshotBuffer()
        # 3 linhas de busca (geracao 5, 12, 12) + 1 de sonda (geracao NULL)
        buf.add_surrogate({"regime": "offline", "geracao": 5})
        buf.add_surrogate({"regime": "offline", "geracao": 12})
        buf.add_surrogate({"regime": "sonda", "geracao": None})
        self.assertEqual(C._max_busca_geracao(buf), 12)
        self.assertEqual(C._max_busca_geracao(H.SnapshotBuffer()), 0)

    def test_emit_sonda_offline_grava_geracao_NULL(self):
        """A sonda offline NÃO passa por emit_sonda_block (que força int(geracao));
        as S linhas nascem com geracao=None (DI-16.12) e regime='sonda'."""
        with tempfile.TemporaryDirectory() as td:
            buf = H.SnapshotBuffer()
            log = H.AuditLogger.for_run("off", "c311", "MMF1", 0,
                                        data_root=td, append=False)
            S, M = 7, 2
            X = np.random.RandomState(0).rand(S, 3)
            sonda = {"X": X, "x_hash": "xh", "f_hash": "fh", "S": S}

            def predict(Xin):
                n = Xin.shape[0]
                return np.zeros((n, M)), np.full((n, M), 0.5)

            dt = C._emit_sonda_offline(buf, log, sonda, modelo_flag="treedGP_build",
                                       predict=predict, fe_treino_max=60, fe=61)
            log.close()
        self.assertEqual(len(buf.surr_rows), S)
        self.assertTrue(all(r["geracao"] is None for r in buf.surr_rows))
        self.assertTrue(all(r["regime"] == "sonda" for r in buf.surr_rows))
        self.assertTrue(all(r["modelo_flag"] == "treedGP_build" for r in buf.surr_rows))
        self.assertTrue(all(r["fe_treino_max"] == 60 for r in buf.surr_rows))
        self.assertGreaterEqual(dt, 0.0)

    def test_emit_sonda_offline_pune_ordem_quebrada(self):
        """predict que devolve cardinalidade errada ⇒ pára-e-loga (join posicional R4.5)."""
        with tempfile.TemporaryDirectory() as td:
            buf = H.SnapshotBuffer()
            log = H.AuditLogger.for_run("off", "c311", "MMF1", 0,
                                        data_root=td, append=False)
            sonda = {"X": np.zeros((5, 2)), "x_hash": "x", "f_hash": "f", "S": 5}
            with self.assertRaises(RuntimeError):
                C._emit_sonda_offline(buf, log, sonda, modelo_flag="treedGP_final",
                                      predict=lambda X: (np.zeros((3, 2)),
                                                         np.zeros((3, 2))),
                                      fe_treino_max=1, fe=1)
            log.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Ganchos — precisam do vendor (env_c311)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(VENDOR_OK, "vendor c311 indisponível (rode no env_c311)")
class TestGanchos(unittest.TestCase):

    def test_import_root_first_sem_pygmo(self):
        DataProblem, treeGP, RVEA, Base, CI = C._import_vendor()
        import desdeo_problem
        self.assertTrue(os.path.abspath(desdeo_problem.__file__)
                        .startswith(os.path.abspath(C.VENDOR_ROOT)))
        import sys
        self.assertNotIn("pygmo", sys.modules)            # DI-16.14

    def test_stock_predict_descarta_sigma(self):
        """O `treeGP.predict` do autor devolve σ=None (o que o nosso patch corrige)."""
        model, X, _ = _trained_model()
        mu, sg = model.predict(X)                          # STOCK (não-patcheado)
        self.assertIsNone(sg)

    def test_patched_predict_mu_identico_ao_stock(self):
        """μ do patch = μ do stock, BYTE a byte (só σ é adicionado)."""
        model, X, _ = _trained_model()
        mu_stock, _ = model.predict(X)
        mu_patch, sg = C._patched_predict(model, X)
        np.testing.assert_array_equal(np.asarray(mu_stock, float).reshape(-1),
                                      np.asarray(mu_patch, float).reshape(-1))
        self.assertEqual(np.asarray(sg).shape[0], X.shape[0])

    def test_predict_batch_mu_igual_ao_patched(self):
        """predict_batch (vetorizado, p/ a sonda) e predict (1-por-linha, p/ a busca)
        dão o MESMO μ e σ NA PRECISÃO GRAVADA (float32).

        `GP.predict(X_leaf)` em lote e `GP.predict(x_i)` ponto-a-ponto diferem por ~1e-15
        (não-associatividade do BLAS) — ABAIXO da resolução do float32 que a ③ persiste.
        Ou seja: idênticos como GRAVADOS. Isso NÃO afeta fidelidade nem não-perturbação —
        a BUSCA usa só o `_patched_predict` (byte-idêntico ao stock); o batch só a sonda."""
        model, X, _ = _trained_model()
        mu_b, sg_b = C._predict_batch(model, X)
        mu_p, sg_p = C._patched_predict(model, X)
        np.testing.assert_array_equal(mu_b.astype(np.float32),
                                      np.asarray(mu_p, float).reshape(-1).astype(np.float32))
        self.assertTrue(np.array_equal(sg_b.astype(np.float32),
                                       np.asarray(sg_p, float).reshape(-1).astype(np.float32),
                                       equal_nan=True))
        # e a diferença float64 é, de fato, ruído de arredondamento (< 1e-12):
        np.testing.assert_allclose(mu_b, np.asarray(mu_p, float).reshape(-1),
                                   atol=1e-12, rtol=0)

    def test_sigma_e_sqrt_da_variancia_nunca_a_variancia(self):
        """DI-16.9: sigma_* carrega σ = sqrt(var_GPy), NUNCA σ²."""
        model, X, _ = _trained_model()
        leaves = model.regr.apply(X)
        gp_leaves = np.intersect1d(leaves, np.atleast_1d(np.asarray(model.error_leaves)))
        self.assertTrue(gp_leaves.size > 0, "precisa de ao menos 1 folha com GP")
        lf = gp_leaves[0]
        loc = np.where(leaves == lf)[0][:1]
        _, var = model.dict_gps[str(lf)].predict(X[loc])
        _, sg = C._predict_batch(model, X)
        got = float(sg[loc[0]])
        self.assertAlmostEqual(got, float(np.sqrt(max(float(var[0][0]), 0.0))), places=10)
        self.assertNotAlmostEqual(got, float(var[0][0]), places=6)   # não é a variância

    def test_sigma_NaN_em_folha_sem_GP(self):
        """Ponto numa folha SÓ-árvore (sem GP) ⇒ σ = NaN (semântica por-região)."""
        model, X, _ = _trained_model()
        leaves = model.regr.apply(X)
        gp = np.atleast_1d(np.asarray(model.error_leaves))
        tree_only = np.setdiff1d(np.unique(leaves), gp)
        if tree_only.size == 0:
            self.skipTest("todas as folhas viradas GP nesta amostra")
        loc = np.where(leaves == tree_only[0])[0][0]
        _, sg = C._predict_batch(model, X)
        self.assertTrue(np.isnan(sg[loc]))

    def test_hooks_restauram_o_vendor(self):
        """O contextmanager de ganchos DESMONTA tudo — o vendor volta bit-a-bit."""
        DataProblem, treeGP, RVEA, Base, CI = C._import_vendor()
        orig_predict = treeGP.predict
        orig_ng = Base._next_gen
        orig_rp = RVEA._refresh_population
        orig_lhs = CI.lhs
        rec = C._Recorder(H.SnapshotBuffer(), D=2, M=1, fe_treino_max=1)
        with C._hooks(treeGP, RVEA, Base, CI, rec):
            self.assertIsNot(treeGP.predict, orig_predict)
            self.assertTrue(hasattr(treeGP, "predict_batch"))
            self.assertIsNot(CI.lhs, orig_lhs)
        self.assertIs(treeGP.predict, orig_predict)
        self.assertIs(Base._next_gen, orig_ng)
        self.assertIs(RVEA._refresh_population, orig_rp)
        self.assertIs(CI.lhs, orig_lhs)
        self.assertFalse(hasattr(treeGP, "predict_batch"))


# ═══════════════════════════════════════════════════════════════════════════
#  Runs completos — env_c311 + C311_SLOW=1
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(VENDOR_OK and SLOW, "run completo — C311_SLOW=1 no env_c311")
class TestRunCompleto(unittest.TestCase):

    def _run(self, td, **kw):
        return C.run_c311("off", "c311", "MMF1", 0, data_root=td, teto_s=900, **kw)

    @staticmethod
    def _iguais(tbl_a, tbl_b) -> bool:
        """Igualdade NaN-aware (a ③ tem σ=NaN nas folhas só-árvore). Um `==` de dict
        REPROVA NaN==NaN espúrio; `pandas.DataFrame.equals` trata NaN co-localizado
        como igual — a semântica correta de 'bit-a-bit' para colunas com NaN."""
        return tbl_a.to_pandas().equals(tbl_b.to_pandas())

    def test_sete_camadas_e_invariantes(self):
        import pyarrow.parquet as pq
        import pyarrow.compute as pc
        with tempfile.TemporaryDirectory() as td:
            _link_artefatos(td)
            res = self._run(td)
            self.assertEqual(res["status"], "ok")
            self.assertTrue(res["cp_init_ok"])
            self.assertEqual(res["n_pop_rows"], 0)                 # ② vazia (DI-16.17)
            self.assertEqual(res["n_sonda_blocos"], 2)            # DI-16.12
            base = os.path.join(td, "experiments", "off", "c311",
                                "exp_" + naming.run_id("off", "c311", "MMF1", 0))
            for suf in ("__real", "__pop", "__surrogate", "__timing", "__final"):
                self.assertTrue(os.path.exists(base + suf + ".parquet"), suf)
            self.assertTrue(os.path.exists(base + ".manifest.json"))
            self.assertTrue(os.path.exists(base + ".jsonl"))
            t = pq.read_table(base + "__surrogate.parquet")
            sonda = t.filter(pc.equal(t.column("regime"), "sonda"))
            busca = t.filter(pc.equal(t.column("regime"), "offline"))
            # sonda: geracao TODA nula; 2×20000; 2 modelo_flags
            self.assertEqual(sonda.column("geracao").null_count, sonda.num_rows)
            self.assertEqual(sonda.num_rows, 40000)
            flags = set(sonda.column("modelo_flag").to_pylist())
            self.assertEqual(flags, {"treedGP_build", "treedGP_final"})
            # busca: contador 1..n_geracoes, monotônico atravessando as 2 fases
            bg = np.array(busca.column("geracao").to_pylist())
            self.assertEqual(int(bg.min()), 1)
            self.assertEqual(int(bg.max()), res["n_geracoes"])
            self.assertEqual(set(busca.column("espaco_modelo").to_pylist()), {"cru"})

    def test_determinismo_bit_a_bit(self):
        import pyarrow.parquet as pq
        outs = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                self._run(td)
                base = os.path.join(td, "experiments", "off", "c311",
                                    "exp_" + naming.run_id("off", "c311", "MMF1", 0))
                outs.append(pq.read_table(base + "__final.parquet"))
        self.assertTrue(self._iguais(outs[0], outs[1]),
                        "2 runs da MESMA semente divergiram (⑦)")

    def test_sonda_NAO_perturba_a_busca(self):
        """🔴 §3.1 (molde c122): ⑦ e ③-busca IDÊNTICAS com a sonda ligada ou não."""
        import pyarrow.parquet as pq
        import pyarrow.compute as pc
        finais, buscas = [], []
        for on in (True, False):
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                self._run(td, emitir_sonda=on)
                base = os.path.join(td, "experiments", "off", "c311",
                                    "exp_" + naming.run_id("off", "c311", "MMF1", 0))
                finais.append(pq.read_table(base + "__final.parquet"))
                t = pq.read_table(base + "__surrogate.parquet")
                buscas.append(t.filter(pc.equal(t.column("regime"), "offline")))
        self.assertTrue(self._iguais(finais[0], finais[1]),
                        "a sonda MOVEU a ⑦ (preserve_all_rng falhou)")
        self.assertTrue(self._iguais(buscas[0], buscas[1]),
                        "a sonda MOVEU a ③-busca")


if __name__ == "__main__":                                    # pragma: no cover
    unittest.main()
