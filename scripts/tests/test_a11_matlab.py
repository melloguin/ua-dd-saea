"""[A11] O gêmeo MATLAB da sonda ESTRATIFICADA — o que dá para provar sem MATLAB.

Contexto
--------
A11 pede o bloco estratificado nos 4 classificadores. O lado Python (c122) já
está feito e provado por par de runs (G-6). O lado MATLAB (b4, c217, e74) não
pode ser executado nesta sessão — o engine MATLAB não importa neste venv —, e a
prova de não-perturbação dele é do autor.

O que AINDA assim é verificável aqui, e é o que este arquivo cobre:

1. **A aritmética do derivador de semente.** O primeiro `sementeBlocoEstrat` que
   escrevi era um FNV-1a de 64 bits em `uint64`. Em MATLAB a aritmética inteira
   **satura** em vez de dar wrap-around (ao contrário de C/numpy): o acumulador
   cravava em `intmax('uint64')` e TODA geração recebia a MESMA semente — o
   bloco estratificado sairia idêntico em todos os ciclos. O mixer vigente é o
   Lehmer/MINSTD, escolhido porque o produto máximo `(2^31-2)·16807 ≈ 3,6e13`
   fica **abaixo de 2^53** e portanto cada passo é EXATO em double. Isso é uma
   propriedade aritmética — testável aqui, sem MATLAB.

2. **A fiação nos 3 classificadores.** Que cada um chame `probeEstratificada`
   logo após a régua e sob `snd.due(g)`.

3. **A separação régua × bloco.** Que o método estratificado não escreva nos
   contadores da régua Sobol (`n_blocos`/`n_linhas`/`gens_sondadas`) e que o
   evento do ⑥ tenha `rec` próprio. Se ele reusasse `rec='sonda'`, todo
   consumidor que conta blocos da régua passaria a contar em dobro nos 4
   classificadores e em nenhum outro config.

Cada teste positivo vem com CONTROLE: a versão anterior dos mesmos arquivos
(tirada do git) tem de REPROVAR. Sem isso um teste estrutural não prova nada.
"""
import os
import re
import subprocess
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONDA = os.path.join(RAIZ, "src", "SondaState.m")
CLASSIFICADORES = ("b4_sonda.m", "c217_sonda.m", "e74_sonda.m")

M_MINSTD = 2147483647
A_MINSTD = 16807


def _semente_bloco(alg, g, uso=91):
    """Réplica em Python de `SondaState.sementeBlocoEstrat` (MINSTD)."""
    s = 1
    for v in [ord(c) for c in alg] + [g, uso]:
        s = ((s + v) % M_MINSTD * A_MINSTD) % M_MINSTD
    return s or 1


def _fonte(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return fh.read()


def _so_codigo(fonte):
    """Remove comentários MATLAB, respeitando aspas simples.

    Necessário porque os arquivos DOCUMENTAM armadilhas citando o nome delas
    (ex.: a nota que manda NÃO usar `Problem.CalObj`). Um teste que casasse a
    string crua reprovaria justamente o arquivo que avisa sobre o perigo.
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
        saida.append("".join(buf))
    return "\n".join(saida)


#: Commit ANTERIOR à fiação do A11 (`9a53a51`). Fixo de propósito: a 1ª versão
#: usava `HEAD~1`, que SE MOVE — dois commits depois o "controle" já continha a
#: fiação e passava, dando falso-verde ao teste positivo. Um controle ancorado
#: em referência móvel não é controle.
BASE_ANTES_DO_A11 = "9a53a51~1"


def _do_git(rel):
    r = subprocess.run(["git", "-C", RAIZ, "show", BASE_ANTES_DO_A11 + ":" + rel],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def _tem_fiacao(fonte):
    """O arquivo chama `probeEstratificada` sob `snd.due(g)`, após a régua?"""
    if "probeEstratificada" not in fonte:
        return False
    if not re.search(r"snd\.due\(g\)", fonte):
        return False
    # a régua tem de vir ANTES do bloco (mesmo modelo, mesma geração)
    return fonte.index("snd.probe(") < fonte.index("probeEstratificada")


class TestMixerDeSemente(unittest.TestCase):
    def test_produto_cabe_em_double_sem_perda(self):
        """A razão de ser do MINSTD aqui: exatidão garantida em float64."""
        maior = (M_MINSTD - 1) * A_MINSTD
        self.assertLess(maior, 2 ** 53,
                        "o produto do mixer estoura a mantissa do double — "
                        "os passos deixariam de ser exatos em MATLAB")
        # e de fato exato: comparar float x inteiro em todo o domínio de borda
        for s in (0, 1, 2, M_MINSTD - 2, M_MINSTD - 1):
            self.assertEqual(float(s * A_MINSTD), s * A_MINSTD)

    def test_deterministico_e_sem_colisao(self):
        pares = {(a, g): _semente_bloco(a, g)
                 for a in ("b4", "c217", "e74", "c122")
                 for g in range(1, 401)}
        self.assertEqual(len(set(pares.values())), len(pares),
                         "sementes colidem entre (alg, geração)")
        for (a, g), s in list(pares.items())[:50]:
            self.assertEqual(s, _semente_bloco(a, g), "mixer não é determinístico")

    def test_semente_varia_com_a_geracao(self):
        """O teste que a versão FNV-saturada REPROVARIA."""
        ss = [_semente_bloco("b4", g) for g in range(1, 9)]
        self.assertEqual(len(set(ss)), 8,
                         "a semente não varia com a geração — o bloco sairia "
                         "idêntico em todos os ciclos")

    def test_controle_o_fnv_saturado_REPROVA(self):
        """CONTROLE MEDIDO: reproduz a saturação de inteiro do MATLAB."""
        sat = 2 ** 64 - 1

        def fnv_saturando(alg, g, uso=91):
            h, pr = 14695981039346656037, 1099511628211
            for v in [ord(c) for c in alg] + [g, uso]:
                h ^= v
                h = min(h * pr, sat)          # MATLAB satura; C/numpy dá wrap
            return h % 2 ** 32

        ss = [fnv_saturando("b4", g) for g in range(1, 9)]
        self.assertEqual(len(set(ss)), 1,
                         "o controle não reproduziu a saturação — então o teste "
                         "positivo acima não discrimina nada")

    def test_uso_id_bate_com_o_lado_python(self):
        from src import standalone_harness as H
        fonte = _fonte(SONDA)
        for nome, valor in (("USO_ESTRAT", H.SONDA_ESTRAT_USO),
                            ("N_ESTRAT", H.SONDA_ESTRAT_N)):
            m = re.search(nome + r"\s*\([^)]*\)\s*double\s*=\s*([0-9.]+)", fonte)
            self.assertIsNotNone(m, "constante %s sumiu da SondaState" % nome)
            self.assertEqual(float(m.group(1)), float(valor),
                             "%s divergiu do lado Python" % nome)
        m = re.search(r"SIGMA_REL_ESTRAT\s*\([^)]*\)\s*double\s*=\s*([0-9.]+)", fonte)
        self.assertEqual(float(m.group(1)), float(H.SONDA_ESTRAT_SIGMA_REL))


class TestFiacaoNosClassificadores(unittest.TestCase):
    def test_os_tres_chamam_o_bloco(self):
        for nome in CLASSIFICADORES:
            with self.subTest(arquivo=nome):
                self.assertTrue(
                    _tem_fiacao(_fonte(os.path.join(RAIZ, "src", nome))),
                    "%s não chama probeEstratificada sob snd.due(g) depois da "
                    "régua" % nome)

    def test_controle_a_versao_anterior_REPROVA(self):
        vistos = 0
        for nome in CLASSIFICADORES:
            antiga = _do_git("src/" + nome)
            if antiga is None:
                continue
            vistos += 1
            self.assertFalse(_tem_fiacao(antiga),
                             "%s: o CONTROLE passou — a checagem não "
                             "discrimina" % nome)
        if not vistos:
            self.skipTest("%s indisponível neste clone" % BASE_ANTES_DO_A11)

    def test_nao_usa_CalObj(self):
        """`UserProblem` é construído com `evalFcn` e SEM `objFcn` — o CalObj cai
        no stub da PROBLEM base e devolveria ZEROS, dando prevalência 1,0 falsa
        e silenciosa em todo bloco."""
        for nome in CLASSIFICADORES:
            with self.subTest(arquivo=nome):
                codigo = _so_codigo(_fonte(os.path.join(RAIZ, "src", nome)))
                self.assertNotIn("CalObj", codigo,
                                 "%s CHAMA CalObj (não só cita em comentário) — "
                                 "devolveria zeros e prevalência 1,0" % nome)


class TestSeparacaoDaRegua(unittest.TestCase):
    def _corpo_estratificado(self):
        f = _fonte(SONDA)
        ini = f.index("function probeEstratificada")
        fim = f.index("function blk = manifestBlockEstrat")
        return f[ini:fim]

    def test_nao_escreve_nos_contadores_da_regua(self):
        corpo = self._corpo_estratificado()
        for campo in ("obj.n_blocos ", "obj.n_linhas ", "obj.gens_sondadas",
                      "obj.tempo_pendente "):
            self.assertNotIn(campo + "=", corpo,
                             "o bloco estratificado escreve em '%s', que é o "
                             "certificado da régua Sobol" % campo.strip())

    def test_carimba_o_regime_proprio(self):
        self.assertIn('rows{i}.regime = "sonda_estratificada"',
                      self._corpo_estratificado())

    def test_evento_tem_rec_proprio(self):
        f = _fonte(SONDA)
        self.assertIn('\'rec\', "sonda_estratificada"', f,
                      "o evento do ⑥ precisa de `rec` próprio; reusar 'sonda' "
                      "faria censo/gates contarem blocos em dobro")

    def test_manifesto_declara_nao_comparavel(self):
        f = _fonte(SONDA)
        self.assertIn("comparavel_entre_configs", f)
        self.assertRegex(f, r"comparavel_entre_configs',\s*false")


if __name__ == "__main__":
    unittest.main()
