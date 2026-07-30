# -*- coding: utf-8 -*-
"""Testes dos gates de proveniência e dos 3 artefatos normativos — G6 [T11].

O portão da rodada-42 gateava CONTEÚDO e não olhava DE ONDE O DADO VEIO: 34 das
666 células com assinatura anômala (5,1%) e 1 quimera (`batch/c149/q10_ZDT4`).
Aqui cada gate tem controle POSITIVO e NEGATIVO, e os 3 artefatos novos
(`motivos_parada.json`, `mapa_termino.json`, `gabarito_camadas.json`) são cobrados
contra o CÓDIGO — a lição do 'cache_cap' × 'cache_hit_travado' (DI-41.2) é que
literal duplicado sempre diverge.

Tudo em tempdir (B-13/G-8).
"""
import json
import os
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)
sys.path.insert(0, os.path.join(_RAIZ, "scripts"))

from src import naming                                    # noqa: E402
import gates_proveniencia as G                             # noqa: E402

try:
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq
    _TEM_ARROW = True
except ImportError:                                        # pragma: no cover
    _TEM_ARROW = False

ARTEFATOS = os.path.join(_RAIZ, "claude_code_context", "artifacts")


class TestMotivosParada(unittest.TestCase):
    """B-06: a classificação vem de UM artefato, e ele cobre o que o código emite."""

    def test_classifica_as_3_classes(self):
        self.assertEqual(G.classifica_motivo("teto_wall"), "sancionado")
        self.assertEqual(G.classifica_motivo("cache_hit_travado"), "sancionado")
        self.assertEqual(G.classifica_motivo("orcamento"), "normal")
        self.assertEqual(G.classifica_motivo(None), "normal")
        self.assertEqual(G.classifica_motivo("gpy_bfgs_linalg"), "falha")
        self.assertEqual(G.classifica_motivo("erro_LinAlgError"), "falha")

    def test_cache_cap_nao_e_sancionado(self):
        # o literal ERRADO da DI-38a (corrigido na DI-41.2): 'cache_cap' é NOME
        # DE PARÂMETRO no header, nunca um motivo_parada. Se ele voltar a
        # aparecer como sancionado, todo aborto por cache travado vira ⚪ falso.
        self.assertEqual(G.classifica_motivo("cache_cap"), "desconhecido")
        self.assertFalse(G.motivo_e_sancionado("cache_cap"))

    def test_todo_motivo_do_codigo_esta_classificado(self):
        """O teste de aceitação do B-06: grep dos literais em `src/*.py` × o
        artefato ⇒ conjunto de NÃO-CLASSIFICADOS vazio."""
        import re
        lit = set()
        pad = re.compile(r'motivo_parada\s*(?:=|:)\s*[\'"]([a-z_0-9]+)[\'"]'
                         r'|motivo_parada\s*=\s*"[a-z_]+",\s*"([a-z_0-9]+)"'
                         r'|motivo\s*=\s*[\'"]([a-z_0-9]+)[\'"]')
        for nome in sorted(os.listdir(os.path.join(_RAIZ, "src"))):
            if not nome.endswith(".py"):
                continue
            with open(os.path.join(_RAIZ, "src", nome), encoding="utf-8") as fh:
                for m in pad.finditer(fh.read()):
                    lit.update(x for x in m.groups() if x)
        # `failed`/`ok` são STATUS, não motivo (aparecem no mesmo unpacking)
        lit -= {"failed", "ok", "retried_ok"}
        nao_classificados = sorted(m for m in lit
                                   if G.classifica_motivo(m) == "desconhecido")
        self.assertEqual(nao_classificados, [],
                         f"motivos emitidos pelo código e AUSENTES do artefato: "
                         f"{nao_classificados}")

    def test_os_3_consumidores_leem_o_artefato(self):
        # B-06: o literal não pode voltar a viver em 3 arquivos
        for rel in ("scripts/portao.py", "scripts/accept.py", "scripts/censo42.py"):
            with self.subTest(arquivo=rel):
                with open(os.path.join(_RAIZ, rel), encoding="utf-8") as fh:
                    src = fh.read()
                self.assertIn("gates_proveniencia", src)
                self.assertNotIn('("teto_wall", "cache_hit_travado")', src)
                self.assertNotIn('{"teto_wall", "cache_hit_travado"}', src)


class TestMapaTermino(unittest.TestCase):
    """I-08: o mapa de término é artefato, e cobre os 24 configs."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ARTEFATOS, "mapa_termino.json"), encoding="utf-8") as fh:
            cls.mapa = json.load(fh)

    def test_cobre_os_24_configs_da_matrix(self):
        import csv
        with open(os.path.join(ARTEFATOS, "runs_matrix.csv"), encoding="utf-8") as fh:
            algs = {r["alg"] for r in csv.DictReader(fh)}
        self.assertEqual(algs - set(self.mapa["configs"]), set())

    def test_as_3_familias_de_rito_estao_declaradas(self):
        fams = {c["familia"] for c in self.mapa["configs"].values()}
        self.assertEqual(fams, {"matlab", "standalone", "botorch"})

    def test_matlab_espera_1_footer_e_python_1_ou_2(self):
        for alg in ("b1", "b3", "e103"):
            self.assertEqual(self.mapa["configs"][alg]["n_footers_esperado"], [1])
        for alg in ("c122", "c311", "c262"):
            self.assertEqual(self.mapa["configs"][alg]["n_footers_esperado"], [1, 2])

    def test_o_campo_de_termino_e_heterogeneo_por_desenho(self):
        # a prova de que o CONTRATO §6 promete um mapa único que não existe
        campos = {c["campo_termino"] for c in self.mapa["configs"].values()}
        self.assertEqual(campos, {"termino", "motivo_parada", "motivo",
                                  "hard_stopped", None})

    def test_treed_media_declarado_sem_evento_de_geracao(self):
        # achado da medição: é o único config sem `<alg>_gen`/`decision` no ⑥
        self.assertIsNone(self.mapa["configs"]["treed_media"]["evento_geracao"])


class TestGabaritoCamadas(unittest.TestCase):
    """G-4: gabarito NORMATIVO — o modal era cego a '0/45 células têm ⑦'."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ARTEFATOS, "gabarito_camadas.json"),
                  encoding="utf-8") as fh:
            cls.gab = json.load(fh)

    def test_a_lista_offline_e_a_do_codigo(self):
        from src.manifest import OFFLINE_ALGS
        self.assertEqual(set(self.gab["configs_offline"]), set(OFFLINE_ALGS))

    def test_so_o_offline_exige_a_setima(self):
        for alg, ent in self.gab["configs"].items():
            with self.subTest(alg=alg):
                self.assertEqual("final" in ent["obrigatorias"],
                                 alg in self.gab["configs_offline"])

    def test_gate_acusa_setima_ausente_mesmo_com_0_de_45(self):
        # É O PONTO DO G-4: com o gabarito MODAL, se NENHUMA célula tem a ⑦, a
        # ausência é invisível — foi assim que 44 dos 49 vermelhos da F5.1 (e103
        # sem ⑦) atravessaram o censo.
        with tempfile.TemporaryDirectory() as dr:
            args = ("off", "e103", "ZDT1", 0)
            for ly in naming.LAYERS:
                p = naming.layer_path(*args, ly, data_root=dr)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "w").close()
            open(naming.jsonl_path(*args, data_root=dr), "w").close()
            open(naming.manifest_path(*args, data_root=dr), "w").close()
            ok, det = G.gate_gabarito_camadas(*args, data_root=dr)
            self.assertFalse(ok)
            self.assertIn("final", det)
            # e com a ⑦ presente fica verde (controle negativo)
            open(naming.layer_path(*args, "final", data_root=dr), "w").close()
            ok2, _ = G.gate_gabarito_camadas(*args, data_root=dr)
            self.assertTrue(ok2)

    def test_online_nao_e_cobrado_pela_setima(self):
        with tempfile.TemporaryDirectory() as dr:
            args = ("main", "b1", "ZDT1", 0)
            for ly in naming.LAYERS:
                p = naming.layer_path(*args, ly, data_root=dr)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "w").close()
            open(naming.jsonl_path(*args, data_root=dr), "w").close()
            open(naming.manifest_path(*args, data_root=dr), "w").close()
            self.assertTrue(G.gate_gabarito_camadas(*args, data_root=dr)[0])


@unittest.skipUnless(_TEM_ARROW, "pyarrow/numpy ausentes")
class TestGate3x1(unittest.TestCase):
    """G-1: o gate que pega a quimera."""

    def _par(self, dr, *, coerente=True, D=2):
        X = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]], dtype=np.float32)
        p1 = os.path.join(dr, "um__real.parquet")
        p3 = os.path.join(dr, "tres__surrogate.parquet")
        pq.write_table(pa.table({"solution_id": pa.array([0, 1, 2], pa.int32()),
                                 "x0": X[:, 0], "x1": X[:, 1]}), p1)
        X3 = X.copy()
        if not coerente:
            X3[1, 0] = np.float32(0.9999)      # a assinatura da quimera
        pq.write_table(pa.table({"real_solution_id": pa.array([0, 1, None], pa.int32()),
                                 "x0": X3[:, 0], "x1": X3[:, 1]}), p3)
        return p3, p1

    def test_celula_coerente_passa(self):
        with tempfile.TemporaryDirectory() as dr:
            ok, det = G.gate_3x1(*self._par(dr, coerente=True))
            self.assertTrue(ok, det)
            self.assertIn("2/2", det)

    def test_quimera_reprova(self):
        with tempfile.TemporaryDirectory() as dr:
            ok, det = G.gate_3x1(*self._par(dr, coerente=False))
            self.assertFalse(ok)
            self.assertIn("1/2", det)

    def test_sem_real_solution_id_e_NAO_APLICAVEL(self):
        # não-aplicável NUNCA é verde nem vermelho (a lição do falso-VERDE B-07)
        with tempfile.TemporaryDirectory() as dr:
            p3 = os.path.join(dr, "t__surrogate.parquet")
            p1 = os.path.join(dr, "r__real.parquet")
            pq.write_table(pa.table({"x0": [0.1]}), p3)
            pq.write_table(pa.table({"solution_id": [0], "x0": [0.1]}), p1)
            ok, det = G.gate_3x1(p3, p1)
            self.assertIsNone(ok)
            self.assertIn("não-aplicável", det)

    def test_id_que_nao_existe_na_primeira_reprova(self):
        with tempfile.TemporaryDirectory() as dr:
            p3 = os.path.join(dr, "t__surrogate.parquet")
            p1 = os.path.join(dr, "r__real.parquet")
            pq.write_table(pa.table({"real_solution_id": pa.array([77], pa.int32()),
                                     "x0": [0.1]}), p3)
            pq.write_table(pa.table({"solution_id": pa.array([0], pa.int32()),
                                     "x0": [0.1]}), p1)
            ok, det = G.gate_3x1(p3, p1)
            self.assertFalse(ok)
            self.assertIn("IDS_AUSENTES", det)


class TestGate2Sexto(unittest.TestCase):
    """G-2: 1 header, footers esperados POR CONFIG, 0 malformada."""

    def _jsonl(self, dr, linhas):
        p = os.path.join(dr, "x.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("".join(linhas))
        return p

    HEADER = '{"ts":"t","rec":"header","D":30}\n'
    FOOT_RUNNER = '{"ts":"t","rec":"footer","status":"ok","fe_final":929}\n'
    FOOT_DESP = '{"ts":"t","rec":"footer","status":"ok","n_retries":0}\n'

    def test_matlab_com_1_footer_passa(self):
        with tempfile.TemporaryDirectory() as dr:
            p = self._jsonl(dr, [self.HEADER, self.FOOT_RUNNER])
            self.assertTrue(G.gate_unicidade_sexto(p, "b1")[0])

    def test_matlab_com_2_footers_reprova(self):
        # o nº esperado vem do ARTEFATO, não de 'MATLAB=1/Python=2' hard-coded
        with tempfile.TemporaryDirectory() as dr:
            p = self._jsonl(dr, [self.HEADER, self.FOOT_RUNNER, self.FOOT_DESP])
            ok, det = G.gate_unicidade_sexto(p, "b1")
            self.assertFalse(ok)
            self.assertIn("esperado [1]", det)

    def test_python_aceita_1_ou_2(self):
        with tempfile.TemporaryDirectory() as dr:
            for linhas in ([self.HEADER, self.FOOT_RUNNER],
                           [self.HEADER, self.FOOT_RUNNER, self.FOOT_DESP]):
                self.assertTrue(G.gate_unicidade_sexto(
                    self._jsonl(dr, linhas), "c122")[0])

    def test_append_cego_reprova(self):
        # a assinatura de `batch/e81/q10_ZDT4`: 95 pares header/footer
        with tempfile.TemporaryDirectory() as dr:
            p = self._jsonl(dr, [self.HEADER, self.FOOT_RUNNER] * 95)
            ok, det = G.gate_unicidade_sexto(p, "e81")
            self.assertFalse(ok)
            self.assertIn("95 headers", det)

    def test_linha_spliced_reprova(self):
        # a assinatura de `main/b1/WFG1`: 49 de 931 linhas cortadas no meio
        with tempfile.TemporaryDirectory() as dr:
            p = self._jsonl(dr, [self.HEADER,
                                 '{"ts":"t","rec":"b1_gen","tempo_fit_s":4{"ts":"20\n',
                                 self.FOOT_RUNNER])
            ok, det = G.gate_unicidade_sexto(p, "b1")
            self.assertFalse(ok)
            self.assertIn("malformadas", det)

    def test_so_o_footer_do_despachante_reprova(self):
        # footer sem `fe_final` = ninguém contabilizou o orçamento
        with tempfile.TemporaryDirectory() as dr:
            p = self._jsonl(dr, [self.HEADER, self.FOOT_DESP])
            ok, det = G.gate_unicidade_sexto(p, "c122")
            self.assertFalse(ok)
            self.assertIn("fe_final", det)


class TestGate3Proveniencia(unittest.TestCase):
    """G-3: venv no roster + campanha + repo_hash — e os 2 modos."""

    def _man(self, **kw):
        base = {"env": {"executable": "/home/jupyter/python_venvs/env_main/bin/python"},
                "campanha_id": "abc123456789_2026-08-01", "repo_hash": "deadbeef"}
        base.update(kw)
        return base

    def test_venv_do_roster_passa(self):
        self.assertTrue(G.gate_proveniencia(self._man(), "c149")[0])

    def test_venv_fora_do_roster_reprova(self):
        # o desastre silencioso do N.1.2: b5 rodando no env_main faz o
        # `sys.modules` entregar o `desdeo_*` errado SEM ERRO
        man = self._man(env={"executable": "/x/python_venvs/env_main/bin/python"})
        ok, det = G.gate_proveniencia(man, "b5m")
        self.assertFalse(ok)
        self.assertIn("fora do roster", det)

    def test_mac_e_vm_sao_o_MESMO_venv(self):
        for caminho in ("/home/jupyter/python_venvs/env_b5/bin/python",
                        "/Users/gmello/Documents/python_venvs/env_b5/bin/python"):
            self.assertEqual(G.venv_de(caminho), "env_b5")
            self.assertTrue(G.gate_proveniencia(
                self._man(env={"executable": caminho}), "b5m")[0])

    def test_modo_campanha_cobra_campanha_id_e_repo_hash(self):
        ok, det = G.gate_proveniencia(self._man(campanha_id=None), "c149")
        self.assertFalse(ok)
        self.assertIn("campanha_id", det)
        ok, det = G.gate_proveniencia(self._man(repo_hash=""), "c149")
        self.assertFalse(ok)
        self.assertIn("repo_hash", det)

    def test_modo_historico_nao_cobra_o_que_nao_existia(self):
        # o re-gate das 666 lê ⑤ v1: `repo_hash` está vazio em 666/666 por
        # construção. No modo estrito o grid inteiro ficaria vermelho e o placar
        # de aceitação viraria ruído.
        man = self._man(campanha_id=None, repo_hash="")
        self.assertTrue(G.gate_proveniencia(man, "c149", modo="historico")[0])

    def test_campanha_diferente_da_corrente_reprova(self):
        ok, det = G.gate_proveniencia(self._man(), "c149",
                                      campanha_id="outra_2026-09-01")
        self.assertFalse(ok)
        self.assertIn("≠ corrente", det)

    def test_matlab_sem_executable_nao_reprova_por_isso(self):
        man = {"env": {"matlab": "24.2"}, "campanha_id": "x_1", "repo_hash": "h"}
        ok, det = G.gate_proveniencia(man, "b1")
        self.assertTrue(ok)
        self.assertIn("sem env.executable", det)


class TestGate7Contrato61(unittest.TestCase):
    """G-7: as chaves que o CONTRATO §6.1 promete estão no ⑥ e no ⑤?

    Nenhum gate conferia campo DI-10 de config algum — `auditar.py` não inspeciona
    o ⑥ e o `accept.py:check_r3_b5` tem 8 itens, todos estruturais. Foi por essa
    porta que I-05, I-07 e I-03 atravessaram CINCO gates verdes.
    """

    MIN = ("fe", "f_best", "n_front1", "tempo_fit_s", "tempo_busca_s")

    def _celula(self, dr, *, campos_extra=(), man=None, rec="decision"):
        p = os.path.join(dr, "x.jsonl")
        ev = {"ts": "t", "rec": rec, "caminho": "c122_gen:x"}
        ev.update({c: 1 for c in self.MIN})
        ev.update({c: 1 for c in campos_extra})
        with open(p, "w", encoding="utf-8") as fh:
            fh.write('{"ts":"t","rec":"header","D":30}\n')
            fh.write(json.dumps(ev) + "\n")
            fh.write('{"ts":"t","rec":"footer","status":"ok","fe_final":9}\n')
        return p, (man if man is not None else
                   {"params": {"N": 11}, "sigma_dict": {"modelo": "x"},
                    "timing": {"tempo_total_s": 1.0}, "doe_hash": "h",
                    "campanha_id": "c_1", "repo_hash": "r"})

    def test_celula_completa_passa(self):
        with tempfile.TemporaryDirectory() as dr:
            jp, man = self._celula(dr, campos_extra=("n_acordo", "n_desacordo"))
            ok, det = G.gate_contrato_61("c122", jp, man)
            self.assertTrue(ok, det)

    def test_campo_di10_ausente_reprova(self):
        # a assinatura do I-05: `p_wrong_stats` 0/N em 30.165 eventos do b5
        with tempfile.TemporaryDirectory() as dr:
            jp, man = self._celula(dr)
            ok, det = G.gate_contrato_61("b5m", jp, man)
            self.assertFalse(ok)
            self.assertIn("p_wrong_stats", det)

    def test_params_ausente_no_quinto_reprova(self):
        # a assinatura do I-07: 197 células (~32% do grid) sem `params` no ⑤
        with tempfile.TemporaryDirectory() as dr:
            jp, man = self._celula(dr, campos_extra=("n_acordo", "n_desacordo"))
            man.pop("params")
            ok, det = G.gate_contrato_61("c122", jp, man)
            self.assertFalse(ok)
            self.assertIn("params", det)

    def test_n_front1_ausente_reprova_o_sobol_batch(self):
        # a assinatura do I-03: o único config sem o mínimo comum DI-10
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "x.jsonl")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write('{"ts":"t","rec":"header"}\n')
                fh.write('{"ts":"t","rec":"decision","caminho":"sobol_batch_gen",'
                         '"fe":9,"f_best":[1,2]}\n')
            ok, det = G.gate_contrato_61("sobol_batch", p, {"params": {}})
            self.assertFalse(ok)
            self.assertIn("n_front1", det)

    def test_o_que_NAO_SE_APLICA_nao_vira_falso_vermelho(self):
        # `tempo_fit_s` nos 4 pisos online é NULL por contrato (DI-13.2: não
        # treinam) e `n_baseline` no e81 é conceito do qLogNEHVI (P6/DI-16.6).
        sexto_piso, _, nsa_piso = G.campos_contratados("nsga2")
        self.assertNotIn("tempo_fit_s", sexto_piso)
        self.assertIn("tempo_fit_s", nsa_piso)
        sexto_e81, _, nsa_e81 = G.campos_contratados("e81")
        self.assertNotIn("n_baseline", sexto_e81)
        self.assertIn("n_baseline", nsa_e81)

    def test_treed_media_sem_evento_e_NAO_APLICAVEL(self):
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "x.jsonl")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write('{"ts":"t","rec":"header"}\n')
                fh.write('{"ts":"t","rec":"footer","fe_final":9}\n')
            ok, det = G.gate_contrato_61("treed_media", p, {})
            self.assertIsNone(ok)
            self.assertIn("não-aplicável", det)

    def test_o_artefato_cobre_os_24_configs(self):
        import csv
        art = G._artefato("contrato_61.json")
        with open(os.path.join(ARTEFATOS, "runs_matrix.csv"), encoding="utf-8") as fh:
            algs = {r["alg"] for r in csv.DictReader(fh)}
        self.assertEqual(algs - set(art["configs"]), set())

    def test_as_pendencias_medidas_estao_declaradas(self):
        # o gate FICA vermelho nestas até a FASE A fechar — e é para isso que
        # ele existe. O artefato tem de dizer QUAL item resolve cada uma.
        art = G._artefato("contrato_61.json")["pendencias_medidas"]
        self.assertIn("p_wrong_stats", art["sexto"]["b5r/b5m/moead_media"]["ausente"])
        self.assertIn("sobol_batch", art["quinto"]["params"]["configs"])
        for fam in art["sexto"].values():
            self.assertTrue(fam.get("item"))
            self.assertTrue(fam.get("medido"))


class TestDiscriminadorO22(unittest.TestCase):
    """B-15: footer ausente ≠ morte de máquina (eram ~270 falsos alarmes)."""

    def _jsonl(self, dr, com_footer):
        p = os.path.join(dr, "x.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write('{"rec":"header"}\n')
            if com_footer:
                fh.write('{"rec":"footer","status":"ok","fe_final":929}\n')
        return p

    def test_smoke_completo_sem_footer_NAO_e_morte(self):
        # medido: 21 células com footer faltante, 9 com ZERO footer, todas com
        # fe_final==maxfe 666/666 e doe_hash igual aos irmãos de tier
        with tempfile.TemporaryDirectory() as dr:
            man = {"status": "ok", "fe_final": 929, "maxfe": 929}
            v, det = G.discriminador_o22(man, self._jsonl(dr, False))
            self.assertEqual(v, "smoke_fora_do_despachante")
            self.assertIn("NÃO é morte", det)

    def test_sem_footer_e_manifesto_incompleto_E_morte(self):
        with tempfile.TemporaryDirectory() as dr:
            man = {"status": "failed", "fe_final": 300, "maxfe": 929}
            self.assertEqual(G.discriminador_o22(man, self._jsonl(dr, False))[0],
                             "morte")

    def test_sem_manifesto_nenhum_E_morte(self):
        with tempfile.TemporaryDirectory() as dr:
            self.assertEqual(G.discriminador_o22({}, self._jsonl(dr, False))[0],
                             "morte")

    def test_com_footer_e_ok(self):
        with tempfile.TemporaryDirectory() as dr:
            self.assertEqual(G.discriminador_o22({}, self._jsonl(dr, True))[0], "ok")


if __name__ == "__main__":
    unittest.main()
