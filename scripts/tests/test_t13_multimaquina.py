# -*- coding: utf-8 -*-
"""[T13/C] A campanha em 9 máquinas — o que precisava mudar para caber.

Por que este arquivo existe
---------------------------
A alocação da campanha passa a ser **por SEMENTE**: cada máquina roda TODOS os
pares em algumas sementes, para que a máquina varie DENTRO de cada config ao
longo das 30 repetições e o efeito vire ruído entre repetições — que a mediana
das 30 dilui. (Média/mediana dilui efeito **aleatório**; a regra antiga O-16
— *"um config, uma máquina"* — mantinha a máquina CONSTANTE nas 30 sementes de
um config, e nesse regime nenhuma média dilui coisa alguma.)

Isso quebrou três pressupostos que estavam embutidos no código porque, até aqui,
**os venvs próprios só existiam no Mac**:

* **C1** — `interpreter_for_alg` resolvia o interpretador por caminho ABSOLUTO
  de macOS (`/Users/gmello/...`). Em VM Linux ele não existe e o `run_in_venv`
  pára-e-loga. Passa a resolver por CANDIDATOS, pelo NOME do venv — a mesma
  identidade que o gate G-3 já usa (*"o mesmo venv vive em `/Users/...` no Mac e
  em `/home/jupyter/...` na VM"*).
* **C2** — a MÁQUINA não viajava com o dado. O ⑤ trazia versões de biblioteca e
  pinos de thread, e a única atribuição de máquina era a coluna `maquina_dona`
  do censo, **derivada do roster planejado** — que rotula errado toda célula
  recuperada noutra máquina (aconteceu na s42, na queda da vm3). Sem `host` no
  ⑤ não há como DEMONSTRAR que a diluição aconteceu.
* **C3** — o censo tinha lista FECHADA de 4 máquinas e `sys.exit` em host
  desconhecido.
"""
import json
import os
import re
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

CENSO = os.path.join(RAIZ, "scripts", "censo42.py")
EXPERIMENT_M = os.path.join(RAIZ, "src", "experiment.m")

#: Os 5 venvs que cada máquina precisa ter para rodar o roster COMPLETO.
VENVS = ("env_main", "env_b5", "env_c311", "env_e81_qpots")


def _tem_harness():
    try:
        from src import standalone_harness  # noqa: F401
        return True
    except Exception:                        # noqa: BLE001
        return False


@unittest.skipUnless(_tem_harness(), "harness standalone ausente")
class TestResolucaoDeVenvPorMaquina(unittest.TestCase):
    """[C1] O interpretador tem de ser achável numa máquina que não é o Mac."""

    def _envs_falso(self, prefixo_declarado):
        """Tabela `envs.json` mínima, com o caminho DECLARADO onde eu quiser."""
        return {
            "alg_to_env": {"b5m": {"env": "env_b5"}},
            "environments": {
                "env_b5": {"mac_interpreter":
                           os.path.join(prefixo_declarado, "env_b5",
                                        "bin", "python")}},
        }

    def test_o_caminho_DECLARADO_ganha_quando_existe(self):
        """No Mac nada muda — é a garantia de não-regressão do C1."""
        from src import standalone_harness as H
        with tempfile.TemporaryDirectory() as td:
            alvo = os.path.join(td, "env_b5", "bin")
            os.makedirs(alvo)
            open(os.path.join(alvo, "python"), "w").close()
            env_id, interp = H.interpreter_for_alg(
                "b5m", envs=self._envs_falso(td))
            self.assertEqual(env_id, "env_b5")
            self.assertEqual(interp, os.path.join(alvo, "python"))

    def test_cai_no_PREFIXO_da_maquina_quando_o_declarado_nao_existe(self):
        """O caso da VM: o caminho de macOS não existe lá.

        Antes do C1 isto devolvia o caminho inexistente e o `run_in_venv`
        derrubava o run com `FileNotFoundError` — em TODOS os configs de venv
        próprio, em TODAS as máquinas que não fossem o Mac.
        """
        from src import standalone_harness as H
        with tempfile.TemporaryDirectory() as td:
            alvo = os.path.join(td, "env_b5", "bin")
            os.makedirs(alvo)
            open(os.path.join(alvo, "python"), "w").close()
            antes = os.environ.get("UA_DD_SAEA_VENVS")
            os.environ["UA_DD_SAEA_VENVS"] = td
            try:
                _, interp = H.interpreter_for_alg(
                    "b5m", envs=self._envs_falso("/nao/existe/em/lugar/nenhum"))
            finally:
                if antes is None:
                    os.environ.pop("UA_DD_SAEA_VENVS", None)
                else:
                    os.environ["UA_DD_SAEA_VENVS"] = antes
            self.assertEqual(interp, os.path.join(alvo, "python"),
                             "não caiu no venv da máquina — os configs de venv "
                             "próprio continuam sendo Mac-only")

    def test_CONTROLE_sem_nenhum_candidato_devolve_o_declarado(self):
        """Falhar tem de ser ACIONÁVEL: quem dá a mensagem é o `run_in_venv`.

        Se esta função inventasse um caminho plausível, o operador receberia
        "arquivo não encontrado" num caminho que ele nunca declarou. Usa um NOME
        de venv que não existe sob prefixo nenhum — com um nome real
        (`env_b5`) o fallback acharia o venv da máquina, e acharia certo.
        """
        from src import standalone_harness as H
        declarado = "/nao/existe/env_fantasma/bin/python"
        envs = {"alg_to_env": {"b5m": {"env": "env_fantasma"}},
                "environments": {"env_fantasma":
                                 {"mac_interpreter": declarado}}}
        _, interp = H.interpreter_for_alg("b5m", envs=envs)
        self.assertEqual(interp, declarado)


@unittest.skipUnless(_tem_harness(), "harness standalone ausente")
class TestMaquinaViajaComODado(unittest.TestCase):
    """[C2] `host`/`plataforma` no ⑤ — nos DOIS stacks Python e no MATLAB."""

    def test_o_env_do_harness_standalone_traz_host_e_plataforma(self):
        from src.standalone_harness import env_info
        info = env_info()
        self.assertTrue(info.get("host"), "⑤ sem `host`")
        self.assertRegex(info.get("plataforma") or "", r"^[A-Za-z]+/\S+$")

    def test_o_operador_pode_ROTULAR_a_maquina(self):
        """`UA_DD_SAEA_HOST` = o nome do roster, não o hostname do provedor."""
        from src.standalone_harness import _host_info
        antes = os.environ.get("UA_DD_SAEA_HOST")
        os.environ["UA_DD_SAEA_HOST"] = "vm7"
        try:
            self.assertEqual(_host_info()["host"], "vm7")
        finally:
            if antes is None:
                os.environ.pop("UA_DD_SAEA_HOST", None)
            else:
                os.environ["UA_DD_SAEA_HOST"] = antes

    def test_os_dois_stacks_Python_declaram_o_MESMO_par_de_campos(self):
        """Um ⑤ com host e outro sem tornaria a coluna inútil na R4."""
        from src.standalone_harness import env_info as e_standalone
        try:
            from src.botorch_harness import env_info as e_botorch
        except Exception:                    # noqa: BLE001
            self.skipTest("stack R2 (torch/botorch) ausente")
        a, b = e_standalone(), e_botorch()
        for campo in ("host", "plataforma"):
            with self.subTest(campo=campo):
                self.assertEqual(a[campo], b[campo])

    def test_o_MATLAB_normaliza_a_arquitetura_para_o_vocabulario_do_Python(self):
        """`computer('arch')` fala 'maca64'/'glnxa64'; o Python fala arm64/x86_64.

        Duas grafias para a MESMA máquina obrigariam a R4 a conhecer dois
        vocabulários só porque a célula mudou de stack.
        """
        with open(EXPERIMENT_M, encoding="utf-8", errors="replace") as fh:
            fonte = fh.read()
        i = fonte.index("function p = plataforma_curta()")
        bloco = fonte[i:i + 1200]
        for arch, esperado in (("maca64", "arm64"), ("maci64", "x86_64"),
                               ("glnxa64", "x86_64")):
            with self.subTest(arch=arch):
                m = re.search(r'case "%s",\s*arq = "([^"]+)"' % arch, bloco)
                self.assertIsNotNone(m, "o MATLAB não mapeia %r" % arch)
                self.assertEqual(m.group(1), esperado)


class TestCensoAceitaMaquinaNova(unittest.TestCase):
    """[C3] O censo não pode morrer por não reconhecer o host."""

    def test_o_censo_NAO_aborta_em_host_desconhecido(self):
        with open(CENSO, encoding="utf-8") as fh:
            fonte = fh.read()
        self.assertNotIn('sys.exit("FATAL: nao reconheci o host', fonte,
                         "host desconhecido volta a derrubar o censo — 5 das 9 "
                         "máquinas cairiam aí")

    def test_o_rotulo_cai_no_PROPRIO_host(self):
        """Rótulo DERIVADO, não planejado: é a correção de fundo do C3."""
        with open(CENSO, encoding="utf-8") as fh:
            fonte = fh.read()
        i = fonte.index("MAQ = os.environ.get(\"MAQ\", \"\")")
        bloco = fonte[i:i + 1400]
        self.assertIn("MAQ = H or", bloco,
                      "o fallback para o próprio host sumiu")


@unittest.skipUnless(_tem_harness(), "harness standalone ausente")
class TestAlocacaoPorSemente(unittest.TestCase):
    """[C4/C6] Duas máquinas rodando sementes DISJUNTAS do mesmo par.

    É o invariante que torna a alocação por semente segura: a semente entra na
    IDENTIDADE da célula (`run_id = {exp}_{alg}_{problema}_{semente}` — D55) e,
    portanto, no caminho de todas as camadas. Duas máquinas escrevendo o mesmo
    par em sementes diferentes não podem colidir, e o "já rodou?" tem de ser
    respondido POR SEMENTE — senão uma máquina pularia o trabalho da outra.
    """

    def test_sementes_diferentes_do_mesmo_par_nao_colidem_em_caminho(self):
        from src import naming
        caminhos = set()
        for semente in (0, 1, 42):
            for camada in ("real", "pop", "surrogate", "timing"):
                caminhos.add(naming.layer_path("off", "b5m", "DTLZ1", semente,
                                               camada, "data"))
            caminhos.add(naming.manifest_path("off", "b5m", "DTLZ1", semente,
                                              "data"))
            caminhos.add(naming.jsonl_path("off", "b5m", "DTLZ1", semente,
                                           "data"))
        self.assertEqual(len(caminhos), 3 * 6,
                         "duas sementes do MESMO par compartilham arquivo — a "
                         "alocação por semente sobrescreveria dado entre "
                         "máquinas")

    def test_a_esteira_procura_o_manifesto_POR_SEMENTE(self):
        """Se a busca ignorasse a semente, cada máquina pularia a outra.

        Afere a CHAVE de busca (que é onde o risco mora), não o veredito
        completo do `is_run_done` — este exige campanha, `fe_final == maxfe`,
        as camadas parquet e os footers, e reproduzi-los aqui mediria o
        contrato do manifesto, não a alocação por semente.
        """
        from src import manifest, naming
        with tempfile.TemporaryDirectory() as dr:
            os.makedirs(naming.run_dir("off", "b5m", data_root=dr),
                        exist_ok=True)
            alvo = naming.manifest_path("off", "b5m", "DTLZ1", 0, dr)
            with open(alvo, "w", encoding="utf-8") as fh:
                json.dump({"run_id": "off_b5m_DTLZ1_0", "status": "ok"}, fh)
            self.assertIsNotNone(
                manifest.read_manifest(
                    naming.manifest_path("off", "b5m", "DTLZ1", 0, dr)))
            self.assertIsNone(
                manifest.read_manifest(
                    naming.manifest_path("off", "b5m", "DTLZ1", 1, dr)),
                "a semente 1 enxergou o manifesto da 0 — uma máquina pularia "
                "o trabalho da outra")
            self.assertFalse(
                manifest.is_run_done("off", "b5m", "DTLZ1", 1, data_root=dr),
                "célula sem manifesto foi dada como pronta")

    def test_o_driver_deriva_o_roster_COMPLETO_do_artefato(self):
        """`LOTE_PARES=todos` não pode ser uma lista digitada que envelhece."""
        import csv
        with open(os.path.join(RAIZ, "scripts", "lote3s.sh"),
                  encoding="utf-8") as fh:
            drv = fh.read()
        self.assertIn('if [ "$PARES" = "todos" ]', drv,
                      "o modo `LOTE_PARES=todos` sumiu do driver")
        self.assertIn("runs_matrix.csv", drv,
                      "o roster completo deixou de sair do ARTEFATO")
        with open(os.path.join(RAIZ, "claude_code_context", "artifacts",
                               "runs_matrix.csv"), encoding="utf-8") as fh:
            pares = {(r["exp"], r["alg"]) for r in csv.DictReader(fh)}
        self.assertGreater(len(pares), 40,
                           "o grid encolheu — confira o artefato")

    def test_a_regra_O16_esta_APOSENTADA_no_driver(self):
        """Doc×código: o driver não pode documentar o oposto do desenho."""
        with open(os.path.join(RAIZ, "scripts", "lote3s.sh"),
                  encoding="utf-8") as fh:
            drv = fh.read()
        self.assertIn("O-16", drv)
        self.assertIn("APOSENTADA", drv,
                      "a regra 'um config, uma máquina' voltou a valer no "
                      "texto do driver, contra a alocação por semente")


if __name__ == "__main__":
    unittest.main()
