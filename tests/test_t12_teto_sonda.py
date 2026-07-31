# -*- coding: utf-8 -*-
"""[T12/BL-06] O bloco FINAL da sonda sob `teto_wall` (c154 e c262).

Por que este arquivo existe
---------------------------
O ⑤ de c154/c262 declara `sonda.cadencia = "1ª iteração, a cada k=2, e SEMPRE a
última"`. A promessa só era cumprida quando o laço morria por **hard-stop**
(`BudgetExhausted`): o ramo do **teto** (`motivo_parada='teto_wall'`, DI-43/44)
saía do laço sem passar por nenhum ponto de emissão — e sob truncamento a
última iteração é justamente a mais informativa (é a única em que o modelo viu
todos os dados que a célula chegou a coletar).

Havia um obstáculo real, e é o que este teste tranca: o `del model` da higiene
de memória (D86) rodava **antes** da checagem de teto, então no ponto do `break`
não existia mais modelo para predizer. O fix desce o `del` para depois do teto —
e `_WallClockProjector.exceeded` aborta **só por `elapsed`** desde a DI-43,
então o instante do truncamento não se move.

Como o teste força o caso
-------------------------
Roda uma célula REAL (`main/<alg>/MMF1/42`, D=2) em tempdir e substitui
`exceeded` por um contador determinístico que dispara na **iteração 3** — ímpar,
onde `sonda_due` é `False`. Se o bloco final aparecer, ele só pode ter vindo do
ramo do teto. É o "kill-por-teto artificial" do cartão, sem depender de relógio.

⚠ **Em PROCESSO PRÓPRIO, e isto não é zelo.** Rodar a célula dentro do
interpretador da suíte a faz morrer com `ValueError: torch.cat(): expected a
non-empty list of Tensors` dentro do `optimize_acqf` — **e o defeito é
pré-existente a este cartão** (reproduz com o fix do BL-06 desfeito). O gatilho
medido é `tests/test_batch_q10.py::TestCalibracaoBatchT9::
test_c154_call_site_usa_o_helper_nao_hardcode`, que faz `mock.patch` em
`botorch.optim.optimize_acqf` e em `gen_batch_initial_conditions`: o estado
global que ele deixa no BoTorch atravessa o processo e derruba um run REAL
posterior. É a mesma lição que produziu os smokes do T11 ("1 por vez, em
processo próprio — `torch.set_default_dtype` é global"). Subprocesso também é
como a campanha roda de fato (1 célula = 1 processo), então este teste passa a
medir o que vai ao ar.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

try:
    import torch  # noqa: F401
    import botorch  # noqa: F401
    HAS_STACK = True
except Exception:  # noqa: BLE001 — python3 base: pula tudo
    HAS_STACK = False

#: A iteração em que o teto dispara. ÍMPAR e > 1 ⇒ `sonda_due` é False lá
#: (cadência = 1ª ou múltiplos de k=2), então um bloco nessa iteração só pode
#: ter saído do ramo do teto. Trocar por um valor par desarma o teste.
IT_TETO = 3

#: Os artefatos de entrada são só leitura — o run escreve exclusivamente no
#: tempdir (`data_root`), nunca em `data/experiments` (proibição da casa).
ENTRADAS = ("doe", "datasets", "sonda", "bbob_pf_cache", "models")


def _data_root(tmp):
    """tempdir com as entradas do repo ligadas por symlink (leitura)."""
    for nome in ENTRADAS:
        origem = os.path.join(RAIZ, "data", nome)
        if os.path.isdir(origem):
            os.symlink(origem, os.path.join(tmp, nome))
    return tmp


#: O driver que roda DENTRO do subprocesso: substitui `exceeded` por um
#: contador determinístico (estoura na n-ésima chamada = n-ésima iteração) e
#: roda a célula. Nada mais é tocado — o resto do runner é o de produção.
DRIVER = r'''
import os, sys, time
RAIZ, ALVO, ALG, DR = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
sys.path.insert(0, RAIZ)
from src import c262_qnehvi as C262

estado = {"n": 0}
def exceeded(self, n_now):
    estado["n"] += 1
    elapsed = time.time() - self.t0
    if estado["n"] == ALVO:
        return True, None, elapsed, "elapsed"
    return False, None, elapsed, None
C262._WallClockProjector.exceeded = exceeded

if ALG == "c154":
    from src.c154_jes import run_c154 as runner
else:
    from src.c262_qnehvi import run_c262 as runner
runner("main", ALG, "MMF1", 42, data_root=DR, teto_s=1e9)
'''


def _roda_truncado(alg):
    """Roda a célula EM PROCESSO PRÓPRIO e devolve `(⑤, eventos do ⑥, ③)`."""
    import pyarrow.parquet as pq
    from src import naming

    with tempfile.TemporaryDirectory(prefix="t12_teto_") as tmp:
        dr = _data_root(tmp)
        drv = os.path.join(tmp, "drv_teto.py")
        with open(drv, "w", encoding="utf-8") as fh:
            fh.write(DRIVER)
        proc = subprocess.run(
            [sys.executable, drv, RAIZ, str(IT_TETO), alg, dr],
            capture_output=True, text=True, timeout=1800)
        base = os.path.join(naming.run_dir("main", alg, data_root=dr),
                            "exp_main_%s_MMF1_42" % alg)
        if not os.path.exists(base + ".manifest.json"):
            raise RuntimeError(
                "o run de %s não produziu ⑤ (rc=%d)\nSTDOUT:\n%s\nSTDERR:\n%s"
                % (alg, proc.returncode, proc.stdout[-2000:],
                   proc.stderr[-4000:]))
        with open(base + ".manifest.json", encoding="utf-8") as fh:
            man = json.load(fh)
        eventos = []
        with open(base + ".jsonl", encoding="utf-8") as fh:
            for linha in fh:
                eventos.append(json.loads(linha))
        t3 = pq.read_table(base + "__surrogate.parquet").to_pydict()
        return man, eventos, t3


@unittest.skipUnless(HAS_STACK, "stack R2 (torch/botorch) ausente")
class TestBlocoFinalSobTeto(unittest.TestCase):
    """Um run REAL truncado por teto tem de trazer o bloco final da sonda."""

    ALG = "c154"

    @classmethod
    def setUpClass(cls):
        cls.man, cls.eventos, cls.t3 = _roda_truncado(cls.ALG)

    def _sondas(self):
        return [e for e in self.eventos if e.get("rec") == "sonda"]

    def test_a_celula_fechou_truncada_por_teto(self):
        """O pressuposto do teste: sem truncamento nada aqui prova nada."""
        self.assertEqual(self.man["status"], "failed")
        self.assertEqual(self.man["motivo_parada"], "teto_wall")
        trunc = [e for e in self.eventos
                 if e.get("rec") == "teto_wall_truncamento"]
        self.assertEqual(len(trunc), 1)
        self.assertEqual(int(trunc[0]["it"]), IT_TETO,
                         "o teto não caiu na iteração planejada — o teste "
                         "deixou de exercitar a iteração sem cadência")

    def test_a_iteracao_do_teto_NAO_e_de_cadencia(self):
        """Se `sonda_due(IT_TETO)` fosse True, o bloco viria da cadência."""
        from src.botorch_harness import sonda_due
        self.assertFalse(sonda_due(IT_TETO),
                         "IT_TETO caiu na cadência — o controle está cego")

    def test_a_ultima_iteracao_tem_bloco_de_sonda(self):
        """A promessa do ⑤: `SEMPRE a última`. É o que o BL-06 quebrava."""
        its = [int(e["it"]) for e in self._sondas()]
        self.assertIn(IT_TETO, its,
                      "a iteração truncada ficou SEM bloco de sonda — o ⑤ "
                      "promete 'SEMPRE a última' e o ⑥ desmente: %r" % (its,))

    def test_o_bloco_final_declara_o_motivo_teto(self):
        """Quem ler a ③ tem de saber por que aquele bloco existe."""
        final = [e for e in self._sondas() if int(e["it"]) == IT_TETO]
        self.assertEqual(len(final), 1)
        self.assertIn("teto_wall", final[0]["motivo"])

    def test_o_bloco_final_chegou_a_camada_3_com_valores(self):
        """Bloco no ⑥ e nada na ③ seria o mesmo defeito com outra roupa."""
        n_pontos = int([e for e in self._sondas()
                        if int(e["it"]) == IT_TETO][0]["n_pontos"])
        self.assertGreater(n_pontos, 0)
        col = self.t3
        linhas = [i for i, (g, r) in enumerate(zip(col["geracao"],
                                                   col["regime"]))
                  if g == IT_TETO and r == "sonda"]
        self.assertEqual(len(linhas), n_pontos,
                         "a ③ não recebeu as linhas do bloco final")
        mus = [col["mu_0"][i] for i in linhas]
        self.assertTrue(any(m is not None for m in mus),
                        "o bloco final chegou à ③ sem predição — sentinela")

    def test_o_tempo_da_sonda_final_entrou_na_contabilidade(self):
        """④/⑤: o custo do bloco final não pode sumir do `tempo_pred_sonda_s`."""
        self.assertEqual(int(self.man["sonda"]["n_blocos"]), len(self._sondas()))
        self.assertGreater(float(self.man["timing"]["tempo_pred_sonda_s"]), 0.0)


@unittest.skipUnless(HAS_STACK, "stack R2 (torch/botorch) ausente")
class TestBlocoFinalSobTetoC262(TestBlocoFinalSobTeto):
    """O mesmo rito no c262 — o molde é compartilhado, o defeito era também."""

    ALG = "c262"


if __name__ == "__main__":
    unittest.main()
