# -*- coding: utf-8 -*-
"""[T12/BL-01+BL-05] O `c217_instrument.m` — testes de VALOR com controle negativo.

Por que este arquivo existe
---------------------------
Dois campos nascidos na campanha T11 atravessaram **6 portões verdes** com dado
sentinela, porque os gates da época aferiam o TEXTO do fonte
(`inspect.getsource` + `assertIn`) e nunca a linha emitida:

* **`pmid_ids` (I-1 / BL-01)** — **−1 em 426/426**. `CalFitnessPC.m:67-68` monta
  `Input = [PopDec, Fitness]` e `:73` recorta o `Pmid` dele (**D+1 colunas**);
  `FEBudget.solutionIdOf` casa o X nativo **bit-a-bit** em `8*D` bytes
  (D89/D57), então a chave de `8*(D+1)` bytes nunca existe no catálogo e o
  `catch` da instrumentação silencia a pista.
* **`y_treino_dist` (I-5 / BL-05)** — **`(0,0,n)` em 42/42**. O rótulo do
  PC-SAEA é **binário `{1,2}`** (`CalFitnessPC.m:69-71`), não ternário
  `{-1,0,+1}`; e o conjunto medido era o `Input` inteiro, não o `TrainIn` que o
  nome do campo promete.

Este arquivo **executa o `c217_instrument.m` de verdade** (MATLAB real,
`FEBudget`/`RunBuffer` reais, `Pmid`/`Output` com a forma que o stock produz) e
afere o **valor** emitido na linha do ⑥. Cada campo tem um **mutante**: o MESMO
fonte com a expressão de ontem, que TEM de reproduzir o defeito histórico —
senão o teste de valor não estaria medindo aquela expressão.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "src", "c217_instrument.m")

#: Cada mutante = {expressão de hoje: expressão de ontem}. Toda substituição
#: tem de casar EXATAMENTE 1 vez, senão o controle perdeu o alvo e o teste
#: reprova dizendo isso.
MUTANTES = {
    # BL-01: a fatia que não existia — `Pmid` tem D+1 colunas.
    "MUTPMID": {
        "bud.solutionIdOf(Pmid(i, 1:D))": "bud.solutionIdOf(Pmid(i, :))",
    },
    # BL-05: a leitura ternária sobre um rótulo binário, sobre o Input inteiro.
    "MUTYDIST": {
        "n_melhor = ceil(3/4 * sum(y >  1));": "n_melhor = sum(y > 0);",
        "n_pior   = ceil(3/4 * sum(y <= 1));": "n_pior   = sum(y < 0);",
        "n = n_melhor + n_pior;": "n = numel(y);",
    },
}

#: `Pmid` sintético: as linhas 3, 7, 11 e 15 do catálogo (solution_id 0-based
#: 2, 6, 10, 14), com a coluna de Fitness colada à direita — a forma do `Input`.
IDS_PMID_ESPERADOS = [2, 6, 10, 14]

#: `Output` com 12 linhas (6 "melhor" = 2, 6 "pior" = 1) ⇒ o treino guarda
#: ceil(3/4·6) = 5 de cada estrato ⇒ n = 10 ≠ n_input = 12. A desigualdade é o
#: que discrimina "mediu o TrainIn" de "mediu o Input".
N_INPUT = 12
N_TREINO = 10
CLASSE_MELHOR = 5
CLASSE_PIOR = 5

DRIVER = r"""
function drv_t12_c217(REPO, OUT, MUT)
    addpath(fullfile(REPO, 'src'));
    addpath(MUT);
    r = struct();
    r.oficial  = uma_rodada(@c217_instrument,          OUT, 'oficial');
    r.mutpmid  = uma_rodada(@c217_instrument_MUTPMID,  OUT, 'mutpmid');
    r.mutydist = uma_rodada(@c217_instrument_MUTYDIST, OUT, 'mutydist');
    fid = fopen(fullfile(OUT, 'resultado.json'), 'w');
    fprintf(fid, '%s', jsonencode(r));
    fclose(fid);
end

function out = uma_rodada(fn, OUT, tag)
    D = 4; M = 2; N = 16;
    % Catalogo DETERMINISTICO (sem rng): X(i,j) = (i-1)/N + (j-1)/100.
    X = (0:N-1).'/N + (0:D-1)/100;
    bud = FEBudget(D);
    F = zeros(N, M);
    for i = 1:N
        F(i,:) = bud.evaluate(X(i,:), @(z) [sum(z), sum((z-0.5).^2)]);
    end

    % O que o stock entrega: Input = [PopDec, Fitness] (D+1 colunas); `Pmid` e
    % `TrainIn` sao recortes de LINHAS de Input -> tambem D+1 colunas.
    sel     = [3 7 11 15];
    Pmid    = [X(sel,:), (1:numel(sel)).'/10];
    Output  = [2;2;2;2;2;2;1;1;1;1;1;1];        % 12 linhas: 6 "melhor", 6 "pior"
    TrainIn = [X(1:10,:), zeros(10,1)];         % ceil(3/4*6)*2 = 10 linhas
    Next    = X([9 10],:);
    ArcDecPre = X(1:8,:);
    TestPre = [1.5; 1.0; 2.0; 1.5];
    Arc = struct('objs', F, 'decs', X);

    jsonl = fullfile(OUT, ['c217_' tag '.jsonl']);
    fid = fopen(jsonl, 'w');
    Problem = struct('D', D, 'data', ...
        struct('buf', RunBuffer(), 'bud', bud, 'log', fid));
    fn(Problem, Arc, Next, 0.5, 0.9, 0.1, TestPre, ...
       0.01, 0.02, 0.03, TrainIn, Output, Pmid, ArcDecPre);
    fclose(fid);

    rec = jsondecode(strtrim(fileread(jsonl)));
    out = struct('pmid_ids', rec.pmid_ids(:).', 'n_Pmid', rec.n_Pmid, ...
                 'fe_treino_max', rec.fe_treino_max, ...
                 'n_best', rec.n_best, 'n_worst', rec.n_worst, ...
                 'n_treino', rec.n_treino, ...
                 'y_treino_dist', rec.y_treino_dist);
end
"""


def _matlab_bin():
    """O binário do MATLAB, ou None (a máquina do autor tem R2025a — D80)."""
    cand = os.environ.get("UA_DD_SAEA_MATLAB")
    if cand and os.path.exists(cand):
        return cand
    cand = "/Applications/MATLAB_R2025a.app/bin/matlab"
    if os.path.exists(cand):
        return cand
    return shutil.which("matlab")


MATLAB = _matlab_bin()


@unittest.skipUnless(MATLAB, "MATLAB ausente nesta máquina")
class TestC217Instrument(unittest.TestCase):
    """Roda o `c217_instrument` de verdade e afere os VALORES do ⑥."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="t12_c217_")
        mut = os.path.join(cls.tmp, "mutantes")
        os.makedirs(mut)

        with open(FONTE, encoding="utf-8") as fh:
            fonte = fh.read()
        cls.alvos_perdidos = []
        for sufixo, subs in MUTANTES.items():
            alvo = fonte.replace("function c217_instrument(",
                                 "function c217_instrument_%s(" % sufixo)
            for hoje, ontem in subs.items():
                if fonte.count(hoje) != 1:
                    cls.alvos_perdidos.append((sufixo, hoje, fonte.count(hoje)))
                alvo = alvo.replace(hoje, ontem)
            with open(os.path.join(mut, "c217_instrument_%s.m" % sufixo), "w",
                      encoding="utf-8") as fh:
                fh.write(alvo)
        with open(os.path.join(cls.tmp, "drv_t12_c217.m"), "w",
                  encoding="utf-8") as fh:
            fh.write(DRIVER)

        cls.proc = subprocess.run(
            [MATLAB, "-sd", cls.tmp, "-batch",
             "drv_t12_c217('%s','%s','%s')" % (RAIZ, cls.tmp, mut)],
            capture_output=True, text=True, timeout=900)
        alvo_json = os.path.join(cls.tmp, "resultado.json")
        cls.res = None
        if os.path.exists(alvo_json):
            with open(alvo_json, encoding="utf-8") as fh:
                cls.res = json.load(fh)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_o_driver_matlab_rodou(self):
        self.assertIsNotNone(
            self.res, "MATLAB não produziu resultado.json.\nSTDOUT:\n%s\n"
                      "STDERR:\n%s" % (self.proc.stdout, self.proc.stderr))

    def test_os_mutantes_ainda_tem_alvo(self):
        """Um mutante que não mutou nada torna todo controle negativo teatro."""
        self.assertEqual(
            self.alvos_perdidos, [],
            "expressões de controle ausentes do fonte (esperado 1 ocorrência "
            "de cada): %r" % (self.alvos_perdidos,))

    # ── BL-01 · pmid_ids ────────────────────────────────────────────────────
    def test_pmid_ids_carrega_os_solution_id_reais(self):
        ids = [int(v) for v in self.res["oficial"]["pmid_ids"]]
        self.assertEqual(ids, IDS_PMID_ESPERADOS,
                         "pmid_ids não recuperou a identidade das linhas do Pmid")
        self.assertTrue(all(v >= 0 for v in ids),
                        "há sentinela −1 em pmid_ids: %r" % (ids,))
        self.assertEqual(int(self.res["oficial"]["n_Pmid"]), len(ids),
                         "n_Pmid e |pmid_ids| discordam — o campo não descreve "
                         "o mesmo objeto")

    def test_CONTROLE_NEGATIVO_pmid_sem_a_fatia_devolve_menos_um(self):
        """A versão de ontem passava `Pmid(i, :)` — D+1 colunas."""
        ids = [int(v) for v in self.res["mutpmid"]["pmid_ids"]]
        self.assertEqual(
            ids, [-1] * len(IDS_PMID_ESPERADOS),
            "o mutante NÃO reproduziu o defeito A40-1 — então o teste de valor "
            "não discrimina a fatia")

    def test_fe_treino_max_tambem_carrega_valor(self):
        """O `TrainIn` sai do MESMO `Input` D+1 — a fatia dele (:32) já era certa."""
        self.assertGreaterEqual(int(self.res["oficial"]["fe_treino_max"]), 0)

    # ── BL-05 · y_treino_dist ───────────────────────────────────────────────
    def test_y_treino_dist_mede_o_treino_e_o_rotulo_binario(self):
        d = self.res["oficial"]["y_treino_dist"]
        self.assertEqual(int(d["classe_melhor"]), CLASSE_MELHOR)
        self.assertEqual(int(d["classe_pior"]), CLASSE_PIOR)
        self.assertEqual(int(d["n"]), N_TREINO)
        self.assertEqual(int(d["n_input"]), N_INPUT)
        self.assertNotEqual(int(d["n"]), int(d["n_input"]),
                            "n == n_input: o campo voltou a medir o Input")
        self.assertAlmostEqual(float(d["prevalencia_classe_melhor"]), 0.5)

    def test_y_treino_dist_fecha_a_identidade_do_split(self):
        """O controle: a derivação TEM de reproduzir |TrainIn| e o n_best/n_worst."""
        d = self.res["oficial"]["y_treino_dist"]
        o = self.res["oficial"]
        self.assertEqual(int(d["classe_melhor"]) + int(d["classe_pior"]),
                         int(d["n"]))
        self.assertEqual(int(d["n"]), int(o["n_treino"]))
        self.assertTrue(d["confere_com_TrainIn"],
                        "a derivação do TrainOut não reproduziu |TrainIn|")
        self.assertEqual(int(d["classe_melhor"]), int(o["n_best"]))
        self.assertEqual(int(d["classe_pior"]), int(o["n_worst"]))

    def test_CONTROLE_NEGATIVO_a_leitura_ternaria_degenera_em_0_0_n(self):
        """A assinatura histórica: uma classe leva tudo, e `n` é o do Input."""
        d = self.res["mutydist"]["y_treino_dist"]
        self.assertEqual(int(d["classe_pior"]), 0,
                         "o mutante NÃO reproduziu o (0,0,n) do BL-05")
        self.assertEqual(int(d["classe_melhor"]), N_INPUT)
        self.assertEqual(int(d["n"]), N_INPUT)
        self.assertFalse(d["confere_com_TrainIn"],
                         "o controle interno não pegou a degeneração — ele é "
                         "a rede que sobra se um dia a fórmula mudar")


if __name__ == "__main__":
    unittest.main()
