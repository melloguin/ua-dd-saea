"""[G-6] O gêmeo MATLAB do `sonda_on` — cobertura e caminhos de desarme.

O gate G-6 prova o invariante 🔴 do CONTRATO §3.1: *a sonda não pode alterar a
busca* — a ① tem de sair BIT-IDÊNTICA com e sem sonda. Nos runners Python a
sonda se desliga por kwarg. No stack MATLAB não havia como desligá-la, então os
13 configs MATLAB ficavam na promessa: o gate simplesmente não rodava neles.

O gêmeo é uma variável de ambiente (`UA_DD_SAEA_SONDA_OFF`) lida no construtor
do `SondaState`, que se DESARMA. Duas escolhas de projeto que estes testes
travam:

* **Desarmar, não sumir.** A alternativa óbvia seria `load_sonda` devolver `[]`
  — os 14 sítios de construção já fazem `if ~isempty(sd)`. Mas `build_manifest`
  lê `snd.n_blocos`/`n_linhas`/`n_falhas` direto, e `[].n_blocos` é erro. Com o
  objeto vivo e desarmado o manifesto continua legível E declara
  `desligada=true` — a sonda nunca some em silêncio.
* **Todos os caminhos até `fire`, não só a cadência.** `due()` cobre o `probe`,
  mas `probeOffline` e `finalProbe` chamam `fire` DIRETO, e o
  `probeEstratificada` tem caminho próprio. Um desarme que só olhasse a cadência
  deixaria o bloco final e o offline dispararem — e o par G-6 reprovaria por um
  motivo que não é perturbação de verdade.
"""
import json
import os
import re
import subprocess
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONDA_M = os.path.join(RAIZ, "src", "SondaState.m")
CONTRATO = os.path.join(RAIZ, "claude_code_context", "artifacts",
                        "contrato_61.json")

#: Os 5 configs SEM surrogate ⇒ sem régua §17.2.2 ⇒ o gate não se aplica.
SEM_SONDA = {"moead", "nsga2", "nsga3", "smsemoa", "sobol_batch"}


def _modulo():
    import importlib.util as iu
    spec = iu.spec_from_file_location(
        "_np_g6", os.path.join(RAIZ, "scripts", "naoperturbacao.py"))
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fonte_m(texto=None):
    if texto is not None:
        return texto
    with open(SONDA_M, encoding="utf-8") as fh:
        return fh.read()


def _so_codigo(fonte):
    """Remove comentários MATLAB, respeitando aspas simples.

    Sem isto a checagem abaixo mede o tamanho do COMENTÁRIO, não a posição do
    guard: o `probeEstratificada` tem ~50 linhas de cabeçalho explicando por que
    o bloco existe, e o guard cairia fora de qualquer janela razoável.
    """
    saida = []
    for linha in fonte.splitlines():
        buf, aspas = [], False
        for i, c in enumerate(linha):
            if c == "'" and not (i and linha[i - 1] == "'"):
                aspas = not aspas
            if c == "%" and not aspas:
                break
            buf.append(c)
        if "".join(buf).strip():
            saida.append("".join(buf))
    return "\n".join(saida)


def _caminhos_desarmados(fonte):
    """Os 4 caminhos até `fire` respeitam `desligada`?

    Devolve o conjunto dos que estão cobertos, para o teste dizer QUAL falta em
    vez de só "falhou".
    """
    codigo = _so_codigo(fonte)
    ok = set()
    if re.search(r"tf\s*=\s*~obj\.desligada\s*&&", codigo):
        ok.add("due")                       # cobre o `probe` (cadência)
    for nome in ("probeOffline", "finalProbe", "probeEstratificada"):
        i = codigo.find("function " + nome)
        if i < 0:
            continue
        # as 3 PRIMEIRAS linhas de código do corpo — o guard tem de vir antes de
        # qualquer trabalho, senão já houve efeito colateral quando ele barra.
        corpo = codigo[i:].splitlines()[1:4]
        if any("if obj.desligada, return; end" in l for l in corpo):
            ok.add(nome)
    return ok


class TestCoberturaDoGate(unittest.TestCase):
    def test_os_24_configs_estao_classificados(self):
        with open(CONTRATO, encoding="utf-8") as fh:
            todos = set(json.load(fh)["configs"].keys())
        mod = _modulo()
        cobertos = set(mod.FLAG_SONDA)
        faltando = todos - cobertos - SEM_SONDA
        self.assertFalse(
            faltando,
            "configs com surrogate fora do gate G-6: %s" % sorted(faltando))
        intrusos = cobertos & SEM_SONDA
        self.assertFalse(
            intrusos,
            "configs SEM surrogate no gate (não têm régua): %s" % sorted(intrusos))
        self.assertEqual(len(cobertos) + len(SEM_SONDA), len(todos))

    def test_os_matlab_usam_a_sentinela_de_ambiente(self):
        mod = _modulo()
        matlab = {k for k, v in mod.FLAG_SONDA.items() if v is mod.MATLAB_ENV}
        self.assertGreaterEqual(len(matlab), 9,
                                "os configs MATLAB sumiram do gate")
        for alg in ("b1", "b3", "b4", "e7", "c141", "c217", "c238", "e74", "e103"):
            self.assertIn(alg, matlab, "%s não está no gate G-6" % alg)

    def test_config_sem_sonda_devolve_nao_aplicavel(self):
        mod = _modulo()
        ok, msg = mod.par_de_runs("sobol_batch", "ZDT1", 0)
        self.assertIsNone(ok)
        self.assertIn("não-aplicável", msg)

    def test_nome_da_variavel_bate_nos_dois_stacks(self):
        mod = _modulo()
        self.assertIn(mod.ENV_SONDA_OFF, _fonte_m(),
                      "o nome da variável divergiu entre o Python e o "
                      "SondaState.m — o desarme silenciosamente não aconteceria")


class TestDesarmeNoSondaState(unittest.TestCase):
    def test_todos_os_caminhos_ate_o_fire(self):
        ok = _caminhos_desarmados(_fonte_m())
        esperado = {"due", "probeOffline", "finalProbe", "probeEstratificada"}
        self.assertEqual(ok, esperado,
                         "caminhos até `fire` SEM guard de desligada: %s"
                         % sorted(esperado - ok))

    def test_o_objeto_continua_existindo(self):
        """`build_manifest` lê snd.n_blocos direto — o objeto não pode sumir."""
        fonte = _fonte_m()
        self.assertIn("desligada (1,1) logical = false", fonte)
        self.assertNotIn("sd = [];  % sonda desligada", fonte)

    def test_o_manifesto_declara(self):
        fonte = _fonte_m()
        self.assertEqual(fonte.count("'desligada',"), 2,
                         "os DOIS manifestos (régua e estratificado) têm de "
                         "declarar `desligada` — senão um run sem sonda passa "
                         "por um run com sonda vazia")

    def test_controle_a_versao_anterior_REPROVA(self):
        """CONTROLE MEDIDO: sem ele a checagem estrutural não prova nada."""
        # Commit ANTERIOR ao desarme (`4126b78`). FIXO de propósito — e é a
        # SEGUNDA vez nesta campanha que eu erro isto: a 1ª versão apontava para
        # `HEAD`, que virou o próprio commit do desarme, então o "controle"
        # continha os guards e passava. Referência móvel não é controle.
        r = subprocess.run(
            ["git", "-C", RAIZ, "show", "4126b78~1:src/SondaState.m"],
            capture_output=True, text=True)
        if r.returncode != 0:
            self.skipTest("4126b78~1 indisponível neste clone")
        self.assertEqual(
            _caminhos_desarmados(r.stdout), set(),
            "o CONTROLE passou: a versão anterior (sem desarme) foi aceita, "
            "logo a checagem não discrimina")


class TestRestauracaoDoAmbiente(unittest.TestCase):
    def test_o_finally_restaura(self):
        """Um env vazado deixaria a PRÓXIMA célula sem sonda em silêncio — o
        oposto exato do que este gate existe para impedir."""
        with open(os.path.join(RAIZ, "scripts", "naoperturbacao.py"),
                  encoding="utf-8") as fh:
            fonte = fh.read()
        i = fonte.index("def par_de_runs")
        corpo = fonte[i:fonte.index("\ndef ", i + 10)]
        self.assertIn("env_antes = os.environ.get(ENV_SONDA_OFF)", corpo)
        self.assertIn("finally:", corpo)
        pos_finally = corpo[corpo.index("finally:"):]
        self.assertIn("env_antes", pos_finally,
                      "a restauração do env não está no finally")

    def test_nao_vaza_de_verdade(self):
        """Execução real: o env volta ao estado anterior mesmo com o run falhando."""
        mod = _modulo()
        antes = os.environ.get(mod.ENV_SONDA_OFF)
        try:
            # alg inexistente => o _adapter.run levanta; o finally tem de rodar
            with self.assertRaises(Exception):
                mod.par_de_runs("b1", "__PROBLEMA_INEXISTENTE__", 0)
        except AssertionError:
            pass                      # se não levantou, o teste do env ainda vale
        depois = os.environ.get(mod.ENV_SONDA_OFF)
        self.assertEqual(antes, depois,
                         "UA_DD_SAEA_SONDA_OFF vazou para o ambiente")


if __name__ == "__main__":
    unittest.main()
