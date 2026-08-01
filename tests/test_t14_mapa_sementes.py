# -*- coding: utf-8 -*-
"""T14.11 — o mapa semente→máquina balanceado por custo.

**Por que ele existe.** A O-16 ("um config, uma máquina") foi APOSENTADA para o
RESULTADO (T13/D1): com a máquina constante nas 30 sementes de um config, a
divergência cross-máquina vira offset SISTEMÁTICO, e média dilui ruído
aleatório, não viés. A alocação passa a ser POR SEMENTE — e faltava o mapa.

**A estrutura.** O grid é SIMÉTRICO em semente (as mesmas 695 células nas 30),
então o custo de uma semente não depende de QUAL semente: balancear é repartir
CONTAGENS. O que não é trivial é a ELEGIBILIDADE — por isso os pares são
agrupados por CONJUNTO DE MÁQUINAS QUE OS RODAM (stack MATLAB ×
`envs.json:alg_to_env` × os `envs` de cada máquina). Na frota default isso dá 3
grupos, que são os "dois mapas" do cartão com o `env_main` separado dos venvs
próprios — a restrição de env vira consequência, não remendo.

**O que estes testes cobram** (o critério do cartão, ao pé da letra):
soma das células dos mapas = grid completo · interseção vazia · desbalanceamento
máximo ≤10%. Mais: que o `lote3s.sh` de fato CONSOME o artefato (comportamento,
não texto) e que a máquina Python-only nunca recebe par MATLAB.

⚠ **⟦M8, 2026-08-01⟧ A FROTA DEIXOU DE SER PLACEHOLDER.** O autor fechou a frota
real em `artifacts/frota.json`: **4 máquinas** (vm1, vm2, vm10, vm3), todas com
MATLAB e os 4 venvs; v5/v6 saíram e o Mac ficou fora do grid. Três premissas
destes testes morreram com isso e foram atualizadas — cada uma preservando a
proteção que dava:

1. o `_pendente_autor` era cobrado como VISÍVEL (para ninguém disparar 14 mil
   h-core contra máquina fictícia); agora se cobra o inverso — **nenhum
   placeholder** pode sobreviver até o disparo;
2. a existência de máquina **Python-only** (v5/v6) era premissa de um teste;
   virou `skipTest` quando não há nenhuma, e o invariante segue valendo se houver;
3. um grupo com alg MATLAB tinha de ser **puramente** MATLAB. Isso valia com
   frota heterogênea (as Python-only faziam o conjunto de elegíveis do Python
   diferir do de MATLAB, separando os grupos). Com as 4 máquinas rodando tudo,
   os conjuntos coincidem e o gerador colapsa num **grupo só** — que é o
   comportamento CORRETO e desejado: é o que faz uma máquina rodar TODOS os
   pares das suas sementes. O invariante que fica é o que importa: par MATLAB
   nunca cai em máquina sem licença.
"""
from __future__ import annotations

import collections
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)
sys.path.insert(0, os.path.join(_RAIZ, "scripts"))

MAPA = os.path.join(_RAIZ, "claude_code_context", "artifacts",
                    "mapa_sementes.json")
GRID = os.path.join(_RAIZ, "claude_code_context", "artifacts",
                    "runs_matrix.csv")
TEMPO = os.path.join(_RAIZ, "f5", "tempo_f52d.csv")
LOTE = os.path.join(_RAIZ, "scripts", "lote3s.sh")

MATLAB_ALGS = frozenset({
    "b1", "b3", "b4", "c141", "c217", "c238", "e103", "e7", "e74",
    "moead", "nsga2", "nsga3", "smsemoa"})


def _mapa() -> dict:
    with open(MAPA, encoding="utf-8") as fh:
        return json.load(fh)


def _grid() -> list[dict]:
    with open(GRID, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _atribuicoes(mapa: dict) -> collections.Counter:
    """(exp, alg, semente) → quantas máquinas o receberam."""
    c = collections.Counter()
    for g in mapa["mapas"].values():
        for _maq, seeds in g["sementes_por_maquina"].items():
            for par in g["pares"]:
                exp, alg = par.split("/", 1)
                for s in seeds:
                    c[(exp, alg, int(s))] += 1
    return c


class TestCoberturaEExclusividade(unittest.TestCase):
    """O critério do cartão: soma = grid completo, interseção vazia."""

    @classmethod
    def setUpClass(cls):
        cls.mapa = _mapa()
        cls.esperado = {(r["exp"], r["alg"], int(r["semente"])) for r in _grid()}
        cls.visto = _atribuicoes(cls.mapa)

    def test_o_grid_INTEIRO_tem_maquina(self):
        faltando = sorted(self.esperado - set(self.visto))
        self.assertEqual(faltando, [], "%d (exp,alg,semente) órfãos"
                                       % len(faltando))

    def test_NENHUMA_atribuicao_em_duas_maquinas(self):
        duplas = sorted(k for k, v in self.visto.items() if v > 1)
        self.assertEqual(duplas, [], "%d em mais de uma máquina" % len(duplas))

    def test_nada_FORA_do_grid_foi_atribuido(self):
        sobra = sorted(set(self.visto) - self.esperado)
        self.assertEqual(sobra, [])

    def test_a_conta_de_celulas_fecha_com_o_artefato(self):
        # a soma declarada no `resumo` tem de ser a do grid, não um número solto.
        # nº de PROBLEMAS por (exp,alg) — contado numa semente só, senão a
        # multiplicação por 30 entra duas vezes.
        s0 = str(self.mapa["sementes"][0])
        n_prob = collections.Counter((r["exp"], r["alg"]) for r in _grid()
                                     if r["semente"] == s0)
        total = sum(n_prob[(e, a)] for (e, a, _s) in self.visto)
        self.assertEqual(total, len(_grid()))
        self.assertEqual(self.mapa["resumo"]["n_celulas_total"], len(_grid()))
        self.assertEqual(self.mapa["resumo"]["n_celulas_por_semente"],
                         sum(n_prob.values()))

    def test_as_30_sementes_sancionadas(self):
        self.assertEqual(self.mapa["sementes"], list(range(29)) + [42])


class TestBalanceamento(unittest.TestCase):

    def setUp(self):
        self.r = _mapa()["resumo"]

    def test_desbalanceamento_dentro_do_criterio(self):
        self.assertLessEqual(
            self.r["desbalanceamento_max"], 0.10,
            "wall máx %.1f h × médio %.1f h" % (self.r["wall_max_h"],
                                                self.r["wall_medio_h"]))

    def test_toda_maquina_recebe_trabalho(self):
        # uma máquina ociosa não é "balanceada": é frota desperdiçada
        for m, w in self.r["wall_por_maquina_h"].items():
            with self.subTest(maquina=m):
                self.assertGreater(w, 0.0)

    def test_o_wall_maximo_e_MENOR_que_a_soma_ingenua(self):
        # controle: se o mapa não distribuísse nada, o max seria o total
        self.assertLess(self.r["wall_max_h"], self.r["custo_total_h_core"] / 4)


class TestRestricoesDeEnvEStack(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mapa = _mapa()
        cls.frota = {m["nome"]: m
                     for m in cls.mapa["_meta"]["frota"]["maquinas"]}

    def test_par_MATLAB_so_cai_em_maquina_com_matlab(self):
        """⟦M8⟧ A pureza do GRUPO caiu; o invariante da LICENÇA continua.

        Ver §3 do docstring do módulo: com a frota homogênea o gerador colapsa
        num grupo só, que MISTURA MATLAB e Python de propósito. O que não pode
        acontecer nunca é o que este teste guarda: um par MATLAB numa máquina
        sem licença.
        """
        for g in self.mapa["mapas"].values():
            algs = {p.split("/", 1)[1] for p in g["pares"]}
            if not (algs & MATLAB_ALGS):
                continue
            for maq in g["sementes_por_maquina"]:
                with self.subTest(maquina=maq):
                    self.assertTrue(self.frota[maq].get("matlab"),
                                    "config MATLAB numa máquina sem licença")

    def test_as_PYTHON_ONLY_nunca_recebem_MATLAB(self):
        py_only = [n for n, m in self.frota.items() if not m.get("matlab")]
        if not py_only:
            self.skipTest("⟦M8⟧ a frota é 100% MATLAB (v5/v6 saíram) — o "
                          "invariante não tem alvo, mas segue codificado para "
                          "quando uma máquina Python-only voltar à frota")
        for g in self.mapa["mapas"].values():
            algs = {p.split("/", 1)[1] for p in g["pares"]}
            if not (algs & MATLAB_ALGS):
                continue
            for m in py_only:
                with self.subTest(maquina=m):
                    self.assertNotIn(m, g["sementes_por_maquina"])

    def test_cada_grupo_so_vai_para_quem_TEM_o_env(self):
        import mapa_sementes as M
        a2e = M._alg_to_env()
        for g in self.mapa["mapas"].values():
            envs = {a2e.get(p.split("/", 1)[1], "env_main") for p in g["pares"]}
            if envs == {"env_matlab"}:
                continue
            for maq in g["sementes_por_maquina"]:
                with self.subTest(maquina=maq, envs=sorted(envs)):
                    self.assertTrue(
                        envs <= set(self.frota[maq].get("envs") or ()),
                        "máquina sem o venv do grupo (envs.json venvs_aceitos)")


class TestProcedenciaDoCusto(unittest.TestCase):

    def setUp(self):
        self.meta = _mapa()["_meta"]

    def test_a_imputacao_esta_DECLARADA_celula_a_celula(self):
        imp = self.meta["celulas_imputadas_h"]
        self.assertEqual(len(imp), 30, "mudou o nº de células sem wall medido")
        # são as mais CARAS do estudo: descartá-las subestimaria o Python
        self.assertTrue(any(k.startswith("main/c154/") for k in imp))
        self.assertTrue(all(v > 0 for v in imp.values()))

    def test_a_fonte_do_custo_e_o_wall_MEDIDO(self):
        self.assertIn("tempo_f52d.csv", self.meta["custo"])
        self.assertTrue(os.path.exists(TEMPO))

    def test_a_frota_e_REAL__nenhum_placeholder_sobrevive_ao_disparo(self):
        """⟦M8, 2026-08-01⟧ INVERTIDO — e agora é uma trava mais forte.

        Enquanto a frota era placeholder, este teste cobrava que o
        `_pendente_autor` estivesse VISÍVEL no artefato: quem fosse consumir o
        mapa tinha de topar com o aviso antes de disparar 14 mil h-core contra
        5 máquinas que não existiam. O autor fechou a frota real, então a
        cobrança se inverte: o que não pode existir agora é placeholder.
        """
        frota = self.meta["frota"]
        placeholders = [m["nome"] for m in frota["maquinas"]
                        if "PLACEHOLDER" in (m.get("fonte") or "")]
        self.assertEqual(placeholders, [],
                         "máquina PLACEHOLDER na frota do disparo: %r"
                         % placeholders)
        self.assertNotIn("_pendente_autor", frota,
                         "a frota ainda se declara pendente do autor")
        for m in frota["maquinas"]:
            with self.subTest(maquina=m["nome"]):
                self.assertTrue((m.get("fonte") or "").strip(),
                                "máquina sem procedência declarada")
                self.assertGreater(int(m.get("jobs", 0)), 0)


class TestGeradorDeterministico(unittest.TestCase):

    def test_regerar_da_o_MESMO_mapa(self):
        # se o gerador não for determinístico, o artefato no git vira ruído
        if not os.path.exists(TEMPO):
            self.skipTest("f5/tempo_f52d.csv ausente")
        import mapa_sementes as M
        a = M.construir(M.FROTA_DEFAULT)
        b = M.construir(M.FROTA_DEFAULT)
        self.assertEqual(json.dumps(a["mapas"], sort_keys=True),
                         json.dumps(b["mapas"], sort_keys=True))

    def test_o_artefato_no_disco_e_o_que_o_gerador_produz(self):
        """Anti-stale: o mapa commitado tem de ser o que o gerador produz HOJE.

        ⟦M8⟧ A frota de referência passa a ser `M._frota(None)` — que resolve
        `artifacts/frota.json` quando ele existe e só cai no `FROTA_DEFAULT`
        se não existir. Comparar contra o `FROTA_DEFAULT` fixo passou a ser
        errado no instante em que a frota real foi escrita: o teste acusaria
        stale num artefato correto.
        """
        if not os.path.exists(TEMPO):
            self.skipTest("f5/tempo_f52d.csv ausente")
        import mapa_sementes as M
        novo = M.construir(M._frota(None))
        self.assertEqual(json.dumps(novo["mapas"], sort_keys=True),
                         json.dumps(_mapa()["mapas"], sort_keys=True),
                         "o artefato está stale — rode scripts/mapa_sementes.py")

    def test_o_conferidor_do_gerador_aprova_o_artefato(self):
        import mapa_sementes as M
        self.assertEqual(M.conferir(_mapa()), [])

    def test_uma_frota_MENOR_ainda_cobre_o_grid(self):
        # robustez: o mapa não pode depender de a frota ter 9 máquinas
        if not os.path.exists(TEMPO):
            self.skipTest("f5/tempo_f52d.csv ausente")
        import mapa_sementes as M
        frota = {"maquinas": [
            {"nome": "a", "jobs": 6, "matlab": True,
             "envs": ["env_main", "env_b5", "env_c311", "env_e81_qpots"]},
            {"nome": "b", "jobs": 6, "matlab": False,
             "envs": ["env_main", "env_b5", "env_c311", "env_e81_qpots"]},
        ]}
        m = M.construir(frota)
        self.assertEqual([e for e in M.conferir(m)
                          if not e.startswith("desbalanceamento")], [])


@unittest.skipUnless(os.path.exists(LOTE), "lote3s.sh ausente")
class TestOLote3sCONSOMEOMapa(unittest.TestCase):
    """Comportamento: o driver tem de derivar SEMENTES e PARES do artefato."""

    def _censo(self, maq: str):
        env = dict(os.environ, CENSO="1", LOTE_MAQ=maq)
        env.pop("LOTE_SEEDS", None)
        return subprocess.run(["bash", LOTE], cwd=_RAIZ, env=env,
                              capture_output=True, text=True, timeout=900)

    def test_uma_maquina_QUE_SO_EXISTE_NO_MAPA_roda(self):
        # vm1 não tem perfil no `case` do driver: se ele não lesse o artefato,
        # abortaria com "defina LOTE_MAQ".
        mapa = _mapa()
        alvo = next(m for m in mapa["resumo"]["wall_por_maquina_h"]
                    if m not in ("mac", "vm3", "v5", "v6"))
        p = self._censo(alvo)
        self.assertIn("MAPA T14.11", p.stdout, p.stdout[-1500:] + p.stderr[-800:])
        esperadas = sorted({s for g in mapa["mapas"].values()
                            for s in (g["sementes_por_maquina"].get(alvo) or [])})
        linha = [l for l in p.stdout.splitlines() if "sementes=" in l]
        self.assertTrue(linha, p.stdout[-1500:])
        vistas = sorted(int(x) for x in
                        linha[0].split("sementes=")[1].split("·")[0].strip().split(","))
        self.assertEqual(vistas, esperadas)

    def test_LOTE_SEEDS_explicito_TEM_PRIORIDADE_sobre_o_mapa(self):
        # o modo manual continua existindo (reprodução da s42, diagnóstico)
        env = dict(os.environ, CENSO="1", LOTE_MAQ="vm3", LOTE_SEEDS="42")
        p = subprocess.run(["bash", LOTE], cwd=_RAIZ, env=env,
                           capture_output=True, text=True, timeout=900)
        self.assertNotIn("MAPA T14.11", p.stdout)
        self.assertIn("sementes=42", p.stdout)

    def test_LOTE_MAPA_0_desliga(self):
        env = dict(os.environ, CENSO="1", LOTE_MAQ="vm3", LOTE_MAPA="0")
        env.pop("LOTE_SEEDS", None)
        p = subprocess.run(["bash", LOTE], cwd=_RAIZ, env=env,
                           capture_output=True, text=True, timeout=900)
        self.assertNotIn("MAPA T14.11", p.stdout)

    def test_maquina_FORA_do_mapa_falha_com_mensagem_acionavel(self):
        p = self._censo("maquina-que-nao-existe")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("nao aparece em", p.stdout)
        self.assertIn("LOTE_MAPA=0", p.stdout)


if __name__ == "__main__":
    unittest.main()
