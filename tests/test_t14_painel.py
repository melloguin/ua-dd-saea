# -*- coding: utf-8 -*-
"""T14.2 / BL-21 — o painel não pode mentir: `footer_fechado()` × `footers[-1]`.

**O defeito.** O append cego (B-01) empilha pares header/footer ESPÚRIOS sobre a
certidão de um run já encerrado — todos com `fe_final`/`D`/`maxfe`/`params` NULL.
Quem lê "o último footer" lê um deles. Medido no corpus REAL da rodada-42:

    data/experiments/batch/e81/exp_batch_e81_ZDT4_42.jsonl
    → 95 headers, 95 footers, 747 linhas, **1 só** footer com `fe_final`
    → último footer:  status='ok', fe_final=None,  n_geracoes=None
    → footer_fechado: status='ok', fe_final=2109,  n_geracoes=200

O `progress.py` é o painel que o autor olha DURANTE a campanha de 30 sementes —
é o pior momento possível para um relatório mentir sobre o estado de uma célula.

**A varredura do padrão** (o cartão manda varrer, não só consertar a linha 95):

| sítio | era | virou |
|---|---|---|
| `scripts/progress.py` | último footer da cauda | `footer_fechado(p)` |
| `scripts/accept.py` (R2-00) | `recs[-1]` | `footer_fechado(jp)` |
| `src/export.py` (backfill ④) | ts do ÚLTIMO footer | ts do footer FECHADO |
| `scripts/gates_proveniencia.py` | — | já CONTA footers com `fe_final` (correto) |
| `src/manifest.py:305` | — | já usava a primitiva |

Controle negativo: ⑥ sintético com footer espúrio DEPOIS do real ⇒ a leitura
antiga devolve o errado, a nova devolve o certo — nos três sítios convertidos.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)
sys.path.insert(0, os.path.join(_RAIZ, "scripts"))

from src import naming                              # noqa: E402
from src.audit_log import footer_fechado            # noqa: E402


def _escreve_jsonl(path: str, recs: list[dict]) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


#: O ⑥ do controle: 1 run REAL fechado + 2 pares espúrios do append cego.
def _recs_envenenado() -> list[dict]:
    real = [
        {"rec": "header", "ts": "2026-07-31T10:00:00.000+00:00",
         "problema": "ZDT4", "semente": 42, "maxfe": 2109, "D": 10},
        {"rec": "c149_gen", "ts": "2026-07-31T10:00:01.000+00:00",
         "geracao": 200, "fe": 2109},
        {"rec": "footer", "ts": "2026-07-31T10:00:02.000+00:00",
         "status": "ok", "fe_final": 2109, "n_geracoes": 200,
         "motivo_parada": "orcamento", "cp_init": True, "cache_hits": 3},
    ]
    espurio = [
        {"rec": "header", "ts": "2026-07-31T11:00:00.000+00:00",
         "problema": "ZDT4", "semente": 42, "maxfe": None, "D": None},
        {"rec": "footer", "ts": "2026-07-31T11:00:00.500+00:00",
         "status": "ok", "fe_final": None, "n_geracoes": None},
    ]
    return real + espurio * 2


# ═══════════════════════════════════════════════════════════════════════════
#  A primitiva × a leitura ingênua (o controle negativo, isolado)
# ═══════════════════════════════════════════════════════════════════════════

class TestControleNegativoDaPrimitiva(unittest.TestCase):

    def test_a_leitura_ANTIGA_le_o_footer_errado(self):
        # sem esta asserção o teste da nova leitura seria vazio: é ela que prova
        # que o ⑥ do controle de fato ENGANA quem lê o último footer.
        with tempfile.TemporaryDirectory() as dr:
            p = _escreve_jsonl(os.path.join(dr, "x.jsonl"), _recs_envenenado())
            with open(p, encoding="utf-8") as fh:
                recs = [json.loads(ln) for ln in fh]
            antigo = next(r for r in reversed(recs) if r.get("rec") == "footer")
            self.assertIsNone(antigo.get("fe_final"))
            self.assertIsNone(antigo.get("n_geracoes"))

    def test_a_primitiva_le_o_footer_CERTO(self):
        with tempfile.TemporaryDirectory() as dr:
            p = _escreve_jsonl(os.path.join(dr, "x.jsonl"), _recs_envenenado())
            novo = footer_fechado(p)
            self.assertEqual(novo["fe_final"], 2109)
            self.assertEqual(novo["n_geracoes"], 200)
            self.assertEqual(novo["motivo_parada"], "orcamento")


# ═══════════════════════════════════════════════════════════════════════════
#  O painel — scripts/progress.py
# ═══════════════════════════════════════════════════════════════════════════

class TestPainelNaoMente(unittest.TestCase):

    def _scan(self, dr):
        import progress
        alvo, orig = os.path.join(dr, "experiments"), progress.DATA
        try:
            progress.DATA = alvo
            return progress._scan()
        finally:
            progress.DATA = orig

    def _monta(self, dr):
        p = naming.jsonl_path("batch", "e81", "ZDT4", 42, data_root=dr)
        _escreve_jsonl(p, _recs_envenenado())
        return p

    def test_o_painel_reporta_o_fe_e_o_status_do_run_REAL(self):
        with tempfile.TemporaryDirectory() as dr:
            self._monta(dr)
            runs = self._scan(dr)
        self.assertEqual(len(runs), 1)
        r = runs[0]
        # ANTES: fe caía para o `fe` do último evento de geração e o footer
        # espúrio dava status/None — o painel descrevia outra célula.
        self.assertEqual(r["fe"], 2109)
        self.assertEqual(r["status"], "ok")

    def test_celula_com_footer_espurio_NAO_aparece_como_ativa(self):
        # "ativo = tem header e não tem footer": com pares espúrios o header
        # também se multiplica, então a definição tem de casar com o FECHADO.
        with tempfile.TemporaryDirectory() as dr:
            self._monta(dr)
            runs = self._scan(dr)
        self.assertFalse(runs[0]["ativo"],
                         "run encerrado apareceu como EM ANDAMENTO no painel")

    def test_run_de_verdade_em_andamento_continua_ativo(self):
        # controle do outro lado: sem footer nenhum, o painel tem de dizer ATIVO
        with tempfile.TemporaryDirectory() as dr:
            p = naming.jsonl_path("batch", "e81", "ZDT4", 42, data_root=dr)
            _escreve_jsonl(p, _recs_envenenado()[:2])       # header + 1 geração
            runs = self._scan(dr)
        self.assertTrue(runs[0]["ativo"])
        self.assertEqual(runs[0]["fe"], 2109)              # do evento de geração

    def test_footer_ABERTO_nao_conta_como_termino(self):
        # o footer do DESPACHANTE não porta `fe_final` (audit_log:71): sozinho,
        # ele não pode declarar a célula terminada.
        with tempfile.TemporaryDirectory() as dr:
            p = naming.jsonl_path("batch", "e81", "ZDT4", 42, data_root=dr)
            _escreve_jsonl(p, _recs_envenenado()[:2] + [
                {"rec": "footer", "ts": "2026-07-31T10:00:02.000+00:00",
                 "status": "ok", "fe_final": None}])
            runs = self._scan(dr)
        self.assertTrue(runs[0]["ativo"])


# ═══════════════════════════════════════════════════════════════════════════
#  O backfill da ④ — src/export.py (o sítio que era CÓDIGO MORTO)
# ═══════════════════════════════════════════════════════════════════════════

class TestBackfillSemAncoraNoFooter(unittest.TestCase):
    """O 3º achado da varredura: `footer_ts` era atribuído e NUNCA lido.

    Não foi "corrigido" — foi REMOVIDO. O footer não é âncora de tempo de
    geração nenhuma (vem depois da escrita das camadas e do upload, que não são
    custo da geração), e uma variável morta com a semântica errada é um convite
    a fiar o defeito de volta. O que se tranca aqui é a AUSÊNCIA.
    """

    def _jsonl(self, dr, com_espurio: bool):
        recs = [
            {"rec": "header", "ts": "2026-07-31T10:00:00.000+00:00"},
            {"rec": "timing", "it": 1, "n_acumulado": 10, "tempo_fit_s": 0.5,
             "ts": "2026-07-31T10:00:01.000+00:00"},
            {"rec": "decision", "it": 1, "tempo_busca_s": 0.25,
             "ts": "2026-07-31T10:00:02.000+00:00"},
            {"rec": "footer", "ts": "2026-07-31T10:00:03.000+00:00",
             "status": "ok", "fe_final": 61},
        ]
        if com_espurio:                       # +1 h de pares espúrios DEPOIS
            recs += [{"rec": "header", "ts": "2026-07-31T11:00:00.000+00:00"},
                     {"rec": "footer", "ts": "2026-07-31T11:00:00.500+00:00",
                      "status": "ok", "fe_final": None}]
        p = naming.jsonl_path("main", "c154", "DTLZ2", 0, data_root=dr)
        return _escreve_jsonl(p, recs)

    def _backfill(self, dr):
        from src import export
        return export.backfill_timing_from_jsonl(
            "main", "c154", "DTLZ2", 0, data_root=dr, dry_run=True)

    def test_o_footer_espurio_NAO_muda_a_quarta_reconstruida(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            self._jsonl(a, com_espurio=False)
            self._jsonl(b, com_espurio=True)
            limpo, sujo = self._backfill(a), self._backfill(b)
        for chave in ("n_linhas", "busca_exatas", "busca_derivadas",
                      "busca_nulas", "busca_anomalas"):
            with self.subTest(chave=chave):
                self.assertEqual(limpo[chave], sujo[chave])

    def test_a_variavel_morta_saiu(self):
        with open(os.path.join(_RAIZ, "src", "export.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("footer_ts = _jsonl_ts(r)", src)
        self.assertIn("procedencia", src)     # a regra viva ficou


# ═══════════════════════════════════════════════════════════════════════════
#  A varredura — nenhum consumidor do ⑥ voltou a ler "o último footer"
# ═══════════════════════════════════════════════════════════════════════════

class TestVarreduraDoPadrao(unittest.TestCase):

    #: sítios que LEEM o ⑥ do corpus (o smoke que o próprio accept escreve em
    #: tempdir tem 3 linhas e footer único — não é consumidor de corpus).
    ARQUIVOS = ("scripts/progress.py", "scripts/accept.py", "src/export.py",
                "src/manifest.py", "scripts/gates_proveniencia.py")

    def test_ninguem_le_o_ultimo_footer(self):
        for rel in self.ARQUIVOS:
            with self.subTest(arquivo=rel):
                with open(os.path.join(_RAIZ, rel), encoding="utf-8") as fh:
                    src = fh.read()
                for padrao in ('for r in reversed(tail) if r.get("rec") == "footer"',
                               'recs[-1]', 'footers[-1]'):
                    self.assertNotIn(padrao, src,
                                     f"{rel}: voltou a ler o ÚLTIMO footer")

    def test_os_consumidores_usam_a_primitiva(self):
        for rel in ("scripts/progress.py", "scripts/accept.py", "src/manifest.py"):
            with self.subTest(arquivo=rel):
                with open(os.path.join(_RAIZ, rel), encoding="utf-8") as fh:
                    self.assertIn("footer_fechado(", fh.read())


# ═══════════════════════════════════════════════════════════════════════════
#  O corpus REAL — o número do docstring é MEDIDO, não copiado
# ═══════════════════════════════════════════════════════════════════════════

#: [M8 · 2026-08-01] GUARDA DE PORTABILIDADE — ver `test_t14_pisos.py`.
#: `data/experiments/` é gitignored; o corpus da s42 mora no BUCKET e localmente
#: só no Mac. Esta classe afirma sobre UMA célula concreta da s42.
#:
#: ⚠ [conserto no mesmo dia] "o arquivo existe" NÃO basta como guarda: vm2/vm3/
#: vm10 têm exatamente esta célula como HERANÇA do provisionamento de julho
#: (handoff vm10 §12 — "manifesto de batch/e81/ZDT4 rastreado até a cópia de
#: data/"), com conteúdo DIFERENTE do canônico — a guarda passava e o conteúdo
#: falhava (`footer_fechado` → None). O sinal robusto é o TAMANHO do corpus:
#: só o Mac tem ~1.000 manifests; as VMs têm 0–6, herdados.
_CELULA_ALVO = os.path.join(_RAIZ, "data", "experiments", "batch", "e81",
                            "exp_batch_e81_ZDT4_42.jsonl")
_N_CORPUS = len(glob.glob(os.path.join(
    _RAIZ, "data", "experiments", "*", "*", "*.manifest.json")))
_TEM_CORPUS = os.path.exists(_CELULA_ALVO) and _N_CORPUS >= 300
_SEM_CORPUS = ("corpus da s42 ausente/parcial nesta máquina (%d manifests; a "
               "célula-alvo %s pode existir como HERANÇA de provisionamento, "
               "com conteúdo != canônico) — o corpus mora no bucket"
               % (_N_CORPUS, os.path.basename(_CELULA_ALVO)))


@unittest.skipUnless(_TEM_CORPUS, _SEM_CORPUS)
class TestCorpusReal(unittest.TestCase):
    """A errata do docstring do `RunJaFechado` (747→767 ⇒ 559→747).

    Regra da casa (armadilha doc×código): número em doc se MEDE antes de gravar.
    """

    ALVO = "data/experiments/batch/e81/exp_batch_e81_ZDT4_42.jsonl"

    def setUp(self):
        self.p = os.path.join(_RAIZ, self.ALVO)
        if not os.path.exists(self.p):
            self.skipTest("célula do controle ausente no disco local "
                          "(a cópia OFICIAL é a do BUCKET)")

    def test_a_celula_tem_94_pares_espurios_e_559_linhas_de_run(self):
        n = nh = nf = nffe = 0
        with open(self.p, "rb") as fh:
            for raw in fh:
                if raw.strip():
                    n += 1
                if b'"header"' not in raw and b'"footer"' not in raw:
                    continue
                try:
                    r = json.loads(raw.decode("utf-8", "replace"))
                except ValueError:
                    continue
                if r.get("rec") == "header":
                    nh += 1
                elif r.get("rec") == "footer":
                    nf += 1
                    nffe += r.get("fe_final") is not None
        self.assertEqual((nh, nf, nffe, n), (95, 95, 1, 747))
        self.assertEqual(n - 2 * (nh - 1), 559, "o run original tinha 559 linhas")

    def test_o_docstring_publica_o_numero_MEDIDO(self):
        with open(os.path.join(_RAIZ, "src", "audit_log.py"), encoding="utf-8") as fh:
            doc = fh.read()
        self.assertIn("559→747", doc)
        self.assertNotIn("(747→767 linhas", doc)

    def test_a_primitiva_recupera_o_termino_que_o_ultimo_footer_perde(self):
        recs = []
        with open(self.p, "rb") as fh:
            for raw in fh:
                if b'"footer"' not in raw:
                    continue
                try:
                    r = json.loads(raw.decode("utf-8", "replace"))
                except ValueError:
                    continue
                if r.get("rec") == "footer":
                    recs.append(r)
        self.assertIsNone(recs[-1].get("fe_final"), "o controle perdeu a graça")
        self.assertEqual(footer_fechado(self.p)["fe_final"], 2109)

    def test_o_corpus_LOCAL_inteiro_e_lido_sem_perda(self):
        # varredura: em toda célula com footer fechado a primitiva devolve algo
        # — e a leitura ingênua perde pelo menos uma (senão não haveria item).
        perdidas = []
        for p in glob.glob(os.path.join(_RAIZ, "data", "experiments",
                                        "**", "*.jsonl"), recursive=True):
            foots = []
            with open(p, "rb") as fh:
                for raw in fh:
                    if b'"footer"' not in raw:
                        continue
                    try:
                        r = json.loads(raw.decode("utf-8", "replace"))
                    except ValueError:
                        continue
                    if r.get("rec") == "footer":
                        foots.append(r)
            if not foots:
                continue
            fechado = footer_fechado(p)
            if fechado is not None and foots[-1].get("fe_final") is None:
                perdidas.append(os.path.relpath(p, _RAIZ))
        self.assertGreater(len(perdidas), 0,
                           "nenhuma célula do corpus distingue as duas leituras "
                           "— o controle ficou vazio")


if __name__ == "__main__":
    unittest.main()
