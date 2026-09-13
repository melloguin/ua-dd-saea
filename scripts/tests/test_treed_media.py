# -*- coding: utf-8 -*-
"""Testes do runner `treed_media` — o PISO-BIG do sweep (treed-GP-MÉDIA, OFFLINE).

`treed_media` é a ABLAÇÃO do c311 no tier big: a MESMA árvore/vendor/RVEA-final,
SEM os GPs (sem `addGPs`, sem a construção iterativa) ⇒ σ NULL em TODA a ③
(DI-16.1). Espelha o `test_piso_off` (o irmão média/no-σ), com o probe de vendor
do `test_c311` (env_c311 = GPy).

TRÊS camadas, por dependência de ambiente (mesmo padrão do test_c311/test_piso_off):
  * `TestPuros` — SEM vendor; rodam em QUALQUER env (a suíte env-main os pega).
  * `@skipUnless(VENDOR_OK)` — precisam do vendor c311 (GPy) ⇒ SÓ no `env_c311`.
    Em env-main (py3.11, sem GPy) a classe é PULADA — a suíte env-main NUNCA
    dispara `_import_vendor` (que insere o overlay root-first do desdeo).
  * `@skipUnless(VENDOR_OK and SLOW)` — runs completos (treina 50k + RVEA 1000 ger);
    atrás de `TREED_SLOW=1` para não pesar a suíte. Rodados no fechamento (env_c311).

Como rodar os pesados (célula REAL do grid — big/50k):
    TREED_SLOW=1 MPLBACKEND=Agg PYTHONHASHSEED=0 <env_c311>/bin/python -m unittest tests.test_treed_media
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest

import numpy as np

from src import naming
from src import standalone_harness as H
from src import treed_media as T

SLOW = os.environ.get("TREED_SLOW") == "1"

#: célula REAL usada nos runs completos (o treed_media roda SÓ em big/50k).
_PROB = "ZDT4"
_SEM = 42


def _vendor_ok() -> bool:
    # Probe LEVE e SEM efeito colateral (não toca sys.path/sys.modules do vendor):
    # o treed_media roda no env_c311 (py3.8 + GPy 1.9.9), o MESMO do c311. Em
    # env-main (py3.11, sem GPy) a classe pesada é PULADA — assim a suíte env-main
    # NUNCA dispara `_import_vendor` (que insere o overlay root-first do desdeo).
    try:
        import GPy  # noqa: F401
        return True
    except Exception:
        return False


VENDOR_OK = _vendor_ok()


def _link_artefatos(td: str) -> None:
    """Linka datasets/sonda do repo p/ um data_root temporário (offline não usa doe)."""
    for sub in ("datasets", "sonda"):
        os.symlink(os.path.join(H.ROOT, "data", sub), os.path.join(td, sub))


def _base(td: str, dist: str = "lhs", prob: str = _PROB, sem: int = _SEM) -> str:
    exp = "sweep-big-" + dist
    return os.path.join(td, "experiments", exp, "treed_media",
                        "exp_" + naming.run_id(exp, "treed_media", prob, sem))


def _iguais(tbl_a, tbl_b) -> bool:
    """Igualdade NaN-aware (a ③ do treed_media tem σ = NULL em TODAS as linhas). Um
    `==` reprovaria NaN==NaN espúrio; `pandas.DataFrame.equals` trata NaN
    co-localizado como igual — a semântica correta de 'bit-a-bit' com NaN."""
    return tbl_a.to_pandas().equals(tbl_b.to_pandas())


# ═══════════════════════════════════════════════════════════════════════════
#  Puros — rodam em env-main (sem vendor)
# ═══════════════════════════════════════════════════════════════════════════

class TestPuros(unittest.TestCase):

    def test_identidade(self):
        self.assertEqual(T._ALG, "treed_media")
        self.assertEqual(T.ALG_ID, 23)                    # seeds.json (D91)
        self.assertEqual(T.USO_ID, 0)                     # uso_id=_default/0
        self.assertEqual(T.N_ITER_FINAL, 10)              # 10x100 = 1000 ger
        self.assertIn("treed", T.ALGO_VERSION.lower())
        self.assertTrue(os.path.isdir(T.VENDOR_ROOT))     # o vendor do c311

    def test_alg_id_bate_com_seeds_json(self):
        """alg_id = 23 (anti-descompasso D91) — a fonte é o seeds.json."""
        _p = os.path.join(H.ROOT, "claude_code_context", "artifacts", "seeds.json")
        with open(_p, encoding="utf-8") as _fh:
            sj = json.load(_fh)
        alg_id_map = sj.get("alg_id") or sj
        found = None
        for k, v in (alg_id_map.items() if isinstance(alg_id_map, dict) else []):
            if k == "treed_media" and isinstance(v, int):
                found = v
        if found is None:  # aninhado sob outra chave — varre 1 nível
            for v in (sj.values() if isinstance(sj, dict) else []):
                if isinstance(v, dict) and isinstance(v.get("treed_media"), int):
                    found = v["treed_media"]
                    break
        self.assertEqual(found, T.ALG_ID)
        self.assertEqual(T.ALG_ID, 23)

    def test_dispatch_rejeita_alg_errado(self):
        with self.assertRaises(ValueError):
            T.run_treed_media("sweep-big-lhs", "c311", _PROB, _SEM)

    def test_registros_offline(self):
        """treed_media é config OFFLINE (COM surrogate), NÃO piso-online — nos 3
        registries paralelos (OFFLINE_CONFIGS, manifest.OFFLINE_ALGS, auditar.OFFLINE)."""
        self.assertIn("treed_media", H.OFFLINE_CONFIGS)
        from src import manifest
        self.assertIn("treed_media", manifest.OFFLINE_ALGS)
        import scripts.auditar as A
        self.assertIn("treed_media", A.OFFLINE)           # DI-34 binding por hash
        self.assertNotIn("treed_media", A.PISOS_ONLINE)   # não é piso-online

    def test_sigma_dict_declara_sigma_NULL_e_ablacao(self):
        sd = T._sigma_dict(50000)
        # σ NULL é a decisão-âncora (DI-16.1)
        self.assertIn("NULL", sd["sigma_*"])
        self.assertIn("DI-16.1", sd["sigma_*"])
        # o motor é o RVEA final, seleção pela média, SEM addGPs (a ablação B15.4)
        self.assertIn("RVEA", sd["motor"])
        self.assertIn("mean", sd["motor"])
        self.assertIn("addGPs", sd["motor"])
        # redação ratificada DI-28: 'ESPECIFICAÇÃO' + 'INDEPENDENTE', nunca 'idêntico'
        self.assertIn("INDEPENDENTE", sd["modelo"])
        self.assertNotIn("idêntico ao c311", sd["modelo"].lower())
        # sigma_* NÃO pode reafirmar o over-claim "mesma árvore byte-a-byte":
        self.assertIn("INDEPENDENTE", sd["sigma_*"])
        # fe_treino_max = n-1 (n=50000 ⇒ 49999)
        self.assertIn("49999", sd["fe_treino_max"])
        # o teto é honrado (DI-35.5)
        self.assertIn("teto", sd)
        self.assertIn("DI-35.5", sd["teto"])

    def test_recorder_escreve_sigma_NULL_e_contador_simples(self):
        """O _Recorder grava σ=None e geracao = _current_gen_count (fase única)."""
        class _StubPop:
            individuals = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float64)
            objectives = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)

        class _StubEvolver:
            _current_gen_count = 7
            population = _StubPop()

        buf = H.SnapshotBuffer()
        buf.set_fe_treino_max(49999)
        rec = T._Recorder(buf, fe_treino_max=49999, modelo_flag=T._MODELO_FLAG)
        rec.capture(_StubEvolver())
        self.assertEqual(len(buf.surr_rows), 2)
        for row in buf.surr_rows:
            self.assertEqual(row["geracao"], 7)              # contador simples
            self.assertEqual(row["regime"], "offline")
            self.assertIsNone(row["sigma"])                  # σ NULL (DI-16.1)
            self.assertIsNone(row["real_solution_id"])       # ② vazia (DI-16.17)
            self.assertEqual(row["modelo_flag"], T._MODELO_FLAG)
            self.assertEqual(row["espaco_modelo"], "cru")
        self.assertEqual(rec.max_geracao, 7)

    def test_null_sonda_geracao_carimba_so_o_bloco(self):
        buf = H.SnapshotBuffer()
        buf.add_surrogate({"regime": "offline", "geracao": 3})   # busca — intocada
        S = 5
        for _ in range(S):
            buf.add_surrogate({"regime": "sonda", "geracao": 1})
        T._null_sonda_geracao(buf, S)
        self.assertEqual(buf.surr_rows[0]["geracao"], 3)          # busca preservada
        self.assertTrue(all(r["geracao"] is None
                            for r in buf.surr_rows[-S:]))          # sonda → NULL
        self.assertTrue(all(r["regime"] == "sonda"
                            for r in buf.surr_rows[-S:]))

    def test_null_sonda_geracao_pune_bloco_nao_sonda(self):
        buf = H.SnapshotBuffer()
        buf.add_surrogate({"regime": "offline", "geracao": 3})
        buf.add_surrogate({"regime": "sonda", "geracao": 1})
        with self.assertRaises(AssertionError):
            T._null_sonda_geracao(buf, 2)     # pega 1 linha de busca no bloco


# ═══════════════════════════════════════════════════════════════════════════
#  Ganchos — precisam do vendor (env_c311 / GPy)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(VENDOR_OK, "vendor c311 indisponível (rode no env_c311)")
class TestGanchos(unittest.TestCase):

    def _trained_trees(self, D=2, n=60, seed=0):
        """Treina SÓ as árvores (sem addGPs) — o surrogate do treed_media."""
        DataProblem, treeGP, RVEA, BaseDecompositionEA, CI = T._import_vendor()
        rng = np.random.RandomState(seed)
        X = rng.random((n, D))
        F = rng.random((n, 2))
        x_low = np.zeros(D)
        x_high = np.ones(D)
        problem = T._build_surrogates(DataProblem, treeGP, X, F, x_low, x_high)
        models = [problem.objectives[i]._model for i in range(2)]
        return X, models

    def test_import_vendor_root_first(self):
        DataProblem, treeGP, RVEA, BaseDecompositionEA, CI = T._import_vendor()
        import desdeo_problem, desdeo_emo
        for mod in (desdeo_problem, desdeo_emo):
            self.assertTrue(os.path.abspath(mod.__file__)
                            .startswith(os.path.abspath(T.VENDOR_ROOT)))

    def test_build_surrogates_sem_GP(self):
        """A ablação: `_build_surrogates` treina SÓ a árvore ⇒ error_leaves None."""
        _X, models = self._trained_trees()
        for m in models:
            self.assertIsNone(m.error_leaves)         # NENHUM GP (a ablação)
            self.assertEqual(len(m.dict_gps), 0)

    def test_predict_batch_sigma_toda_NaN_sem_GP(self):
        """Sem GP, `_predict_batch` devolve σ TODO NaN (μ = predição da árvore)."""
        X, models = self._trained_trees()
        for m in models:
            mu, sg = T._predict_batch(m, X)
            self.assertEqual(mu.shape[0], X.shape[0])
            self.assertTrue(np.all(np.isnan(sg)))     # σ = NaN (descartado → NULL)
            # μ = predição da árvore pura (mesma regr.predict)
            self.assertTrue(np.allclose(mu, np.asarray(m.regr.predict(X)).reshape(-1)))

    def test_sonda_predict_media_devolve_sigma_None(self):
        """O predict da sonda descarta σ (DI-16.1): devolve (μ (S,M), None)."""
        X, models = self._trained_trees()
        mu, sg = T._sonda_predict_media(models)(X)
        self.assertEqual(mu.shape, (X.shape[0], 2))
        self.assertIsNone(sg)                          # σ NULL


# ═══════════════════════════════════════════════════════════════════════════
#  Runs completos — env_c311 + TREED_SLOW=1 (célula REAL big/50k)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(VENDOR_OK and SLOW, "run completo — TREED_SLOW=1 no env_c311")
class TestRunCompleto(unittest.TestCase):

    def _run(self, td, dist="lhs", **kw):
        return T.run_treed_media("sweep-big-" + dist, "treed_media", _PROB, _SEM,
                                 data_root=td, **kw)

    def test_sete_camadas_e_invariantes(self):
        import pyarrow.parquet as pq
        import pyarrow.compute as pc
        with tempfile.TemporaryDirectory() as td:
            _link_artefatos(td)
            res = self._run(td)
            self.assertEqual(res["status"], "ok")
            self.assertTrue(res["cp_init_ok"])
            self.assertEqual(res["n_sonda_blocos"], 1)     # 1 bloco (modelo único)
            self.assertEqual(res["n_pop_rows"], 0)         # ② vazia
            self.assertEqual(res["n_geracoes"], 1000)      # 10x100
            self.assertGreater(res["n_final"], 0)
            base = _base(td, "lhs")
            for suf in ("__real", "__pop", "__surrogate", "__timing", "__final"):
                self.assertTrue(os.path.exists(base + suf + ".parquet"), suf)
            self.assertTrue(os.path.exists(base + ".manifest.json"))
            self.assertTrue(os.path.exists(base + ".jsonl"))

            t = pq.read_table(base + "__surrogate.parquet")
            sig_cols = [c for c in t.schema.names if c.startswith("sigma_")]
            mu_cols = [c for c in t.schema.names if c.startswith("mu_")]
            sonda = t.filter(pc.equal(t.column("regime"), "sonda"))
            busca = t.filter(pc.equal(t.column("regime"), "offline"))

            # SONDA: 1 bloco de 20.000, geracao TODA nula (DI-13.5), 1 modelo_flag
            self.assertEqual(sonda.num_rows, 20000)
            self.assertEqual(sonda.column("geracao").null_count, sonda.num_rows)
            self.assertEqual(set(sonda.column("modelo_flag").to_pylist()),
                             {T._MODELO_FLAG})
            # σ NULL em TODA a ③ (busca E sonda) — DI-16.1 ('c311 sem GPs')
            for c in sig_cols:
                self.assertEqual(sonda.column(c).null_count, sonda.num_rows, c)
                self.assertEqual(busca.column(c).null_count, busca.num_rows, c)
            # μ preenchido em ambos
            for c in mu_cols:
                self.assertEqual(sonda.column(c).null_count, 0, c)
                self.assertEqual(busca.column(c).null_count, 0, c)
            # BUSCA: geracao 1..1000; espaco cru; real_solution_id NULL (② vazia)
            bg = np.array(busca.column("geracao").to_pylist())
            self.assertEqual(int(bg.min()), 1)
            self.assertEqual(int(bg.max()), 1000)
            self.assertEqual(set(busca.column("espaco_modelo").to_pylist()), {"cru"})
            self.assertEqual(busca.column("real_solution_id").null_count,
                             busca.num_rows)

            # ④ = 1 LINHA com tempo_fit_s REAL (o treed_media TREINA a árvore)
            t4 = pq.read_table(base + "__timing.parquet")
            self.assertEqual(t4.num_rows, 1)
            self.assertTrue(all(v is not None
                                for v in t4.column("tempo_fit_s").to_pylist()))
            self.assertEqual(t4.column("n_acumulado")[0].as_py(), res["n_dataset"])
            # DI-13.10: tempo_geracao_s EXCLUI a sonda (geracao == fit+busca)
            t_ger = t4.column("tempo_geracao_s")[0].as_py()
            t_fitbusca = (t4.column("tempo_fit_s")[0].as_py()
                          + t4.column("tempo_busca_s")[0].as_py())
            self.assertAlmostEqual(t_ger, t_fitbusca, places=6)
            self.assertGreater(t4.column("tempo_pred_sonda_s")[0].as_py(), 0.0)

            # ⑤ manifesto: sigma_dict + timing.tempo_total_s
            man = json.load(open(base + ".manifest.json"))
            self.assertTrue(man.get("sigma_dict"))
            self.assertTrue((man.get("timing") or {}).get("tempo_total_s"))

    def test_determinismo_bit_a_bit(self):
        """2 runs da MESMA semente ⇒ ⑦ E ③-busca idênticas (NaN-aware)."""
        import pyarrow.parquet as pq
        import pyarrow.compute as pc
        finais, buscas = [], []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                self._run(td)
                base = _base(td, "lhs")
                finais.append(pq.read_table(base + "__final.parquet"))
                t = pq.read_table(base + "__surrogate.parquet")
                buscas.append(t.filter(pc.equal(t.column("regime"), "offline")))
        self.assertTrue(_iguais(finais[0], finais[1]), "⑦ divergiu")
        self.assertTrue(_iguais(buscas[0], buscas[1]), "③-busca divergiu")

    def test_sonda_NAO_perturba_a_busca(self):
        """§3.1: ⑦ e ③-busca IDÊNTICAS com a sonda ligada ou não."""
        import pyarrow.parquet as pq
        import pyarrow.compute as pc
        finais, buscas = [], []
        for on in (True, False):
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                self._run(td, emitir_sonda=on)
                base = _base(td, "lhs")
                finais.append(pq.read_table(base + "__final.parquet"))
                t = pq.read_table(base + "__surrogate.parquet")
                buscas.append(t.filter(pc.equal(t.column("regime"), "offline")))
        self.assertTrue(_iguais(finais[0], finais[1]),
                        "a sonda MOVEU a ⑦ (preserve_all_rng falhou)")
        self.assertTrue(_iguais(buscas[0], buscas[1]),
                        "a sonda MOVEU a ③-busca")


if __name__ == "__main__":                                    # pragma: no cover
    unittest.main()
