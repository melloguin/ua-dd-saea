# -*- coding: utf-8 -*-
"""[T12/BL-01] `pmid_ids` do c217 — teste de VALOR, com controle negativo.

Por que este arquivo existe
---------------------------
O campo `pmid_ids` nasceu na campanha T11 (item I-1) para dar a IDENTIDADE da
referência do gate par-a-par do c217 — sem ela o rótulo verdadeiro dos pontos da
sonda é irreconstituível e a acurácia do classificador vira não-mensurável na
dissertação inteira. Ele atravessou **6 portões verdes** gravando **−1 em
426/426 valores**: os gates da época aferiam o TEXTO do fonte
(`inspect.getsource` + `assertIn`), nunca a linha emitida.

A causa (A40-1): `CalFitnessPC.m:67-68` monta `Input = [PopDec, Fitness]` e
`:73` recorta o `Pmid` dele — **D+1 colunas**. `FEBudget.solutionIdOf` casa o X
nativo **bit-a-bit** em `8*D` bytes (D89/D57), então uma chave de `8*(D+1)`
bytes nunca existe no catálogo e o `catch` da instrumentação silencia a pista.

Por isso este teste **executa o `c217_instrument.m` de verdade** (MATLAB real,
`FEBudget` real, `RunBuffer` real, `Pmid` com a largura que o stock produz) e
afere o **valor** da chave `pmid_ids` na linha do ⑥ — e o controle negativo
roda uma cópia do MESMO fonte com a fatia revertida para `Pmid(i, :)`, provando
que o teste discrimina (a versão de ontem REPROVA aqui).
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "src", "c217_instrument.m")

#: A fatia correta (hoje) e a fatia de ontem — o par que define o controle.
FATIA_HOJE = "bud.solutionIdOf(Pmid(i, 1:D))"
FATIA_ONTEM = "bud.solutionIdOf(Pmid(i, :))"

#: `Pmid` sintético: as linhas 3, 7, 11 e 15 do catálogo (solution_id 0-based
#: 2, 6, 10, 14), com a coluna de Fitness colada à direita — a forma exata do
#: `Input` do stock.
LINHAS_PMID = [3, 7, 11, 15]
IDS_ESPERADOS = [i - 1 for i in LINHAS_PMID]

DRIVER = r"""
function drv_t12_c217(REPO, OUT, MUT)
    addpath(fullfile(REPO, 'src'));
    addpath(MUT);
    r = struct();
    r.oficial = uma_rodada(@c217_instrument,     OUT, 'oficial');
    r.mutante = uma_rodada(@c217_instrument_MUT, OUT, 'mutante');
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

    % O que o stock entrega: Input = [PopDec, Fitness] (D+1 colunas);
    % Pmid e um recorte de LINHAS de Input -> tambem D+1 colunas.
    sel     = [3 7 11 15];
    Pmid    = [X(sel,:), (1:numel(sel)).'/10];
    TrainIn = [X([1 2 4 5 6],:), zeros(5,1)];
    Output  = [2;2;1;1;1];
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
                 'fe_treino_max', rec.fe_treino_max);
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
class TestPmidIdsC217(unittest.TestCase):
    """Roda o `c217_instrument` de verdade e afere o VALOR de `pmid_ids`."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="t12_c217_")
        mut = os.path.join(cls.tmp, "mutante")
        os.makedirs(mut)

        with open(FONTE, encoding="utf-8") as fh:
            fonte = fh.read()
        cls.n_fatia_hoje = fonte.count(FATIA_HOJE)
        # O mutante é o MESMO fonte com a fatia de ontem — nada mais muda.
        alvo = fonte.replace("function c217_instrument(",
                             "function c217_instrument_MUT(")
        alvo = alvo.replace(FATIA_HOJE, FATIA_ONTEM)
        with open(os.path.join(mut, "c217_instrument_MUT.m"), "w",
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

    def test_pmid_ids_carrega_os_solution_id_reais(self):
        """A prova de VALOR: os ids do Pmid são os do catálogo, não sentinelas."""
        ids = [int(v) for v in self.res["oficial"]["pmid_ids"]]
        self.assertEqual(
            ids, IDS_ESPERADOS,
            "pmid_ids não recuperou a identidade das linhas do Pmid")
        self.assertTrue(all(v >= 0 for v in ids),
                        "há sentinela −1 em pmid_ids: %r" % (ids,))
        self.assertEqual(int(self.res["oficial"]["n_Pmid"]), len(ids),
                         "n_Pmid e |pmid_ids| discordam — o campo não descreve "
                         "o mesmo objeto")

    def test_CONTROLE_NEGATIVO_a_fatia_de_ontem_devolve_menos_um(self):
        """Sem este controle o teste acima não provaria nada.

        A versão anterior passava `Pmid(i, :)` — D+1 colunas — para o
        `solutionIdOf`. Se ela também passasse no teste de valor, o teste de
        valor não estaria medindo a fatia.
        """
        self.assertEqual(
            self.n_fatia_hoje, 1,
            "a fatia `%s` não está mais no fonte (1 ocorrência esperada) — o "
            "controle negativo perdeu o alvo" % FATIA_HOJE)
        ids = [int(v) for v in self.res["mutante"]["pmid_ids"]]
        self.assertEqual(
            ids, [-1] * len(IDS_ESPERADOS),
            "o mutante NÃO reproduziu o defeito A40-1 — então o teste de valor "
            "não discrimina a fatia")

    def test_fe_treino_max_tambem_carrega_valor(self):
        """O `TrainIn` sai do MESMO `Input` D+1 — a fatia dele (:32) já era certa."""
        self.assertGreaterEqual(int(self.res["oficial"]["fe_treino_max"]), 0)


if __name__ == "__main__":
    unittest.main()
