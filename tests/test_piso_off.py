# -*- coding: utf-8 -*-
"""Testes do runner piso-off `moead_media` (MOEA/D-média, DESDEO mode 12, OFFLINE).

TRÊS camadas, por dependência de ambiente (mesmo padrão do test_c311):
  * `TestPuros` — SEM vendor; rodam em QUALQUER env (a suíte env-main os pega).
  * `@skipUnless(VENDOR_OK)` — precisam do vendor desdeo (py3.7 + sklearn 0.21.3)
    ⇒ SÓ no `env_b5`. Em env-main (py3.11) / env_c311 (py3.8) a classe é PULADA —
    o overlay root-first do vendor NUNCA é inserido pela suíte env-main.
  * `@skipUnless(VENDOR_OK and SLOW)` — runs completos (treina+otimiza 40k); atrás
    de `PISO_SLOW=1` para não pesar a suíte. Rodados no fechamento (env_b5).

Como rodar os pesados:
    PISO_SLOW=1 MPLBACKEND=Agg PYTHONHASHSEED=0 <env_b5>/bin/python -m unittest tests.test_piso_off
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

import numpy as np

from src import naming
from src import piso_offline as P
from src import standalone_harness as H

SLOW = os.environ.get("PISO_SLOW") == "1"


def _vendor_ok() -> bool:
    # Probe LEVE e SEM efeito colateral (não toca sys.path/sys.modules do vendor):
    # o piso roda SÓ no env_b5 (py3.7 + sklearn 0.21.3). Em env-main (py3.11) e
    # env_c311 (py3.8) a classe pesada é PULADA — assim a suíte env-main NUNCA
    # dispara `_import_vendored` (que insere o overlay root-first do desdeo).
    if sys.version_info[:2] != (3, 7):
        return False
    try:
        import sklearn
        return sklearn.__version__.startswith("0.21")
    except Exception:
        return False


VENDOR_OK = _vendor_ok()


def _link_artefatos(td: str) -> None:
    """Linka datasets/sonda do repo para um data_root temporário (offline não usa doe)."""
    for sub in ("datasets", "sonda"):
        os.symlink(os.path.join(H.ROOT, "data", sub), os.path.join(td, sub))


def _base(td: str, prob: str, sem: int = 0) -> str:
    return os.path.join(td, "experiments", "off", "moead_media",
                        "exp_" + naming.run_id("off", "moead_media", prob, sem))


def _iguais(tbl_a, tbl_b) -> bool:
    """Igualdade NaN-aware (a ③ do piso tem σ = NULL/NaN em TODAS as linhas). Um
    `==` reprovaria NaN==NaN espúrio; `pandas.DataFrame.equals` trata NaN
    co-localizado como igual — a semântica correta de 'bit-a-bit' com NaN."""
    return tbl_a.to_pandas().equals(tbl_b.to_pandas())


# ═══════════════════════════════════════════════════════════════════════════
#  Puros — rodam em env-main (sem vendor)
# ═══════════════════════════════════════════════════════════════════════════

class TestPuros(unittest.TestCase):

    def test_identidade(self):
        self.assertEqual(P._ALG, "moead_media")
        self.assertEqual(P._MODE, 12)                     # Gen-MOEA/D (PBI)
        self.assertEqual(P._FE_TOTAL, 40000)              # rampa θ divide por ele
        self.assertIn("moead_media", P.ALGO_VERSION)
        self.assertTrue(os.path.isdir(P._VENDOR))

    def test_alg_id_bate_com_seeds_json(self):
        """alg_id = 21 (anti-descompasso D91) — a fonte é o seeds.json."""
        _p = os.path.join(H.ROOT, "claude_code_context", "artifacts", "seeds.json")
        with open(_p, encoding="utf-8") as _fh:
            sj = json.load(_fh)
        # o mapa alg_id pode estar em chave 'alg_id' ou no topo — busca robusta
        alg_id_map = sj.get("alg_id") or sj
        found = None
        for k, v in (alg_id_map.items() if isinstance(alg_id_map, dict) else []):
            if k == "moead_media" and isinstance(v, int):
                found = v
        if found is None:  # aninhado sob outra chave — varre 1 nível
            for v in (sj.values() if isinstance(sj, dict) else []):
                if isinstance(v, dict) and isinstance(v.get("moead_media"), int):
                    found = v["moead_media"]
                    break
        self.assertEqual(found, P._ALG_ID)
        self.assertEqual(P._ALG_ID, 21)

    def test_dispatch_rejeita_alg_errado(self):
        with self.assertRaises(ValueError):
            P.run_piso_offline("off", "b5m", "MMF1", 0)

    def test_registros_offline(self):
        """moead_media é config OFFLINE (COM surrogate), NÃO piso-online."""
        self.assertIn("moead_media", H.OFFLINE_CONFIGS)
        from src import manifest
        self.assertIn("moead_media", manifest.OFFLINE_ALGS)
        import scripts.auditar as A
        self.assertIn("moead_media", A.OFFLINE)
        self.assertNotIn("moead_media", A.PISOS_ONLINE)

    def test_sigma_dict_declara_sigma_NULL_e_ablacao(self):
        sd = P._sigma_dict(61)
        # σ NULL é a decisão-âncora (DI-16.1)
        self.assertIn("NULL", sd["sigma_*"])
        self.assertIn("DI-16.1", sd["sigma_*"])
        # o motor é o mode 12 (MOEAD_select), a ablação do b5m
        self.assertIn("MOEAD_select", sd["motor"])
        self.assertIn("12", sd["motor"])
        # N = lattice do b5m (DI-16.4), não 100
        self.assertIn("50", sd["N_lattice"])
        self.assertIn("105", sd["N_lattice"])
        self.assertIn("DI-16.4", sd["N_lattice"])
        # redação ratificada DI-28: 'ESPECIFICACAO' + 'INDEPENDENTE', nunca 'identico'
        self.assertIn("INDEPENDENTE", sd["modelo"])
        self.assertNotIn("identico ao b5", sd["modelo"].lower())
        # fe_treino_max = n-1
        self.assertIn("60", sd["fe_treino_max"])

    def test_null_sonda_geracao_carimba_so_o_bloco(self):
        buf = H.SnapshotBuffer()
        buf.add_surrogate({"regime": "offline", "geracao": 3})   # busca — intocada
        S = 5
        for _ in range(S):
            buf.add_surrogate({"regime": "sonda", "geracao": 1})
        P._null_sonda_geracao(buf, S)
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
            P._null_sonda_geracao(buf, 2)     # pega 1 linha de busca no bloco


# ═══════════════════════════════════════════════════════════════════════════
#  Ganchos — precisam do vendor (env_b5)
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(VENDOR_OK, "vendor desdeo indisponível (rode no env_b5)")
class TestGanchos(unittest.TestCase):

    def test_import_vendored_e_o_MOEA_D_do_mode12(self):
        DataProblem, SurrogateKriging, MOEA_D = P._import_vendored()
        import inspect
        # o MODE 12 é o MOEA_D de ProbMOEAD.py (PBI + MOEAD_select), NÃO o de MOEAD.py
        self.assertEqual(MOEA_D.__module__, "desdeo_emo.EAs.ProbMOEAD")
        self.assertIn("MOEAD_select", inspect.getsource(MOEA_D.__init__))
        src_ng = inspect.getsource(MOEA_D._next_gen)
        self.assertIn("individuals_archive", src_ng)   # arquiva por geração (③ nativa)
        self.assertIn("objectives_archive", src_ng)
        self.assertIn("uncertainty_archive", src_ng)   # existe, mas o piso NÃO a reporta

    def test_root_first_e_pydoe_patch(self):
        P._import_vendored()
        import desdeo_problem
        self.assertTrue(os.path.abspath(desdeo_problem.__file__)
                        .startswith(os.path.abspath(P._VENDOR)))
        from desdeo_emo.population import CreateIndividuals as CI
        self.assertTrue(getattr(CI, "_piso_lhs_patched", False))   # fix determinismo


# ═══════════════════════════════════════════════════════════════════════════
#  Runs completos — env_b5 + PISO_SLOW=1
# ═══════════════════════════════════════════════════════════════════════════

@unittest.skipUnless(VENDOR_OK and SLOW, "run completo — PISO_SLOW=1 no env_b5")
class TestRunCompleto(unittest.TestCase):

    def _run(self, td, prob="MMF1", **kw):
        return P.run_piso_offline("off", "moead_media", prob, 0,
                                  data_root=td, **kw)

    def test_sete_camadas_e_invariantes(self):
        import pyarrow.parquet as pq
        import pyarrow.compute as pc
        with tempfile.TemporaryDirectory() as td:
            _link_artefatos(td)
            res = self._run(td)
            self.assertEqual(res["n_final"] > 0, True)
            self.assertTrue(res["cp_init_ok"])
            self.assertEqual(res["mode"], 12)
            base = _base(td, "MMF1")
            for suf in ("__real", "__pop", "__surrogate", "__timing", "__final"):
                self.assertTrue(os.path.exists(base + suf + ".parquet"), suf)
            self.assertTrue(os.path.exists(base + ".manifest.json"))
            self.assertTrue(os.path.exists(base + ".jsonl"))

            t = pq.read_table(base + "__surrogate.parquet")
            sig_cols = [c for c in t.schema.names if c.startswith("sigma_")]
            mu_cols = [c for c in t.schema.names if c.startswith("mu_")]
            sonda = t.filter(pc.equal(t.column("regime"), "sonda"))
            busca = t.filter(pc.equal(t.column("regime"), "offline"))

            # SONDA: 1 bloco de 20.000, geracao TODA nula (DI-13.5)
            self.assertEqual(sonda.num_rows, 20000)
            self.assertEqual(sonda.column("geracao").null_count, sonda.num_rows)
            self.assertEqual(set(sonda.column("modelo_flag").to_pylist()),
                             {P._MODELO_FLAG})
            # σ NULL em TODA a ③ (busca E sonda) — DI-16.1 ('b5 sem σ')
            for c in sig_cols:
                self.assertEqual(sonda.column(c).null_count, sonda.num_rows, c)
                self.assertEqual(busca.column(c).null_count, busca.num_rows, c)
            # μ preenchido em ambos
            for c in mu_cols:
                self.assertEqual(sonda.column(c).null_count, 0, c)
                self.assertEqual(busca.column(c).null_count, 0, c)
            # BUSCA: geracao 1..n_geracoes; espaco cru; real_solution_id NULL (② vazia)
            bg = np.array(busca.column("geracao").to_pylist())
            self.assertEqual(int(bg.min()), 1)
            self.assertEqual(int(bg.max()), res["n_geracoes"])
            self.assertEqual(set(busca.column("espaco_modelo").to_pylist()), {"cru"})
            self.assertEqual(busca.column("real_solution_id").null_count,
                             busca.num_rows)

            # ④ = 1 LINHA com tempo_fit_s REAL (DI-16.1: o piso offline TREINA)
            t4 = pq.read_table(base + "__timing.parquet")
            self.assertEqual(t4.num_rows, 1)
            self.assertTrue(all(v is not None
                                for v in t4.column("tempo_fit_s").to_pylist()))

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
                base = _base(td, "MMF1")
                finais.append(pq.read_table(base + "__final.parquet"))
                t = pq.read_table(base + "__surrogate.parquet")
                buscas.append(t.filter(pc.equal(t.column("regime"), "offline")))
        self.assertTrue(_iguais(finais[0], finais[1]), "⑦ divergiu")
        self.assertTrue(_iguais(buscas[0], buscas[1]), "③-busca divergiu")

    def test_sonda_NAO_perturba_a_busca(self):
        """🔴 §3.1: ⑦ e ③-busca IDÊNTICAS com a sonda ligada ou não."""
        import pyarrow.parquet as pq
        import pyarrow.compute as pc
        finais, buscas = [], []
        for on in (True, False):
            with tempfile.TemporaryDirectory() as td:
                _link_artefatos(td)
                self._run(td, sonda_on=on)
                base = _base(td, "MMF1")
                finais.append(pq.read_table(base + "__final.parquet"))
                t = pq.read_table(base + "__surrogate.parquet")
                buscas.append(t.filter(pc.equal(t.column("regime"), "offline")))
        self.assertTrue(_iguais(finais[0], finais[1]),
                        "a sonda MOVEU a ⑦ (preserve_all_rng falhou)")
        self.assertTrue(_iguais(buscas[0], buscas[1]),
                        "a sonda MOVEU a ③-busca")


if __name__ == "__main__":                                    # pragma: no cover
    unittest.main()
