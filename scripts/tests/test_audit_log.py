"""Testes do ⑥ blindado — B-01 (anti-append) + B-11 (escrita atômica de linha).

Os dois defeitos que este arquivo trava foram MEDIDOS na rodada-42:

* **B-01** — `AuditLogger` abria em `"a"` sem guarda: `batch/e81/q10_ZDT4`
  acumulou **94 pares header/footer espúrios** (747→767 linhas), todos com
  `D`/`maxfe`/`params`/`sigma_dict` NULL, e 34 das 666 células ficaram com a
  auditoria de término indecidível (~1.020 em 30 sementes).
* **B-11** — escrita com deslocamento próprio (o `open(path,"w")` do rito
  `append=False`) e buffer de usuário: `main/b1/WFG1` fechou com **49 de 931
  linhas spliced** e **zero footer** — o "filme" do mecanismo, produto principal
  da Classe A, inutilizável. Cada malformada é um `b1_gen`/`sonda` com um `guard`
  de ts POSTERIOR sobrescrito no meio ⇒ dois deslocamentos de escrita sobre o
  mesmo ⑥ (não é linha grande partida: o `header` de lá tem 512 B).

Suíte stdlib pura: `python -m unittest discover -s tests -t .`.
**Tudo em tempdir** — nenhum teste desta suíte toca `data/` (B-13/G-8).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)

from src import naming                              # noqa: E402
from src.audit_log import (                         # noqa: E402
    LIMITE_ATOMICO_B, AuditLogger, RunJaFechado, footer_fechado)


def _linhas(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


class TestAntiAppendB01(unittest.TestCase):
    """B-01: reabrir em append um run já FECHADO levanta."""

    def _fecha_run(self, dr, *, fe_final=464):
        with AuditLogger.for_run("main", "c217", "DTLZ2", 0,
                                 data_root=dr, append=False) as log:
            log.header(D=15, M=3, maxfe=464, doe_hash="deadbeef")
            log.footer(status="ok", fe_final=fe_final, n_geracoes=37)
        return naming.jsonl_path("main", "c217", "DTLZ2", 0, data_root=dr)

    def test_reabrir_run_fechado_levanta(self):
        with tempfile.TemporaryDirectory() as dr:
            jp = self._fecha_run(dr)
            antes = (os.path.getsize(jp), os.path.getmtime(jp))
            with self.assertRaises(RunJaFechado):
                AuditLogger.for_run("main", "c217", "DTLZ2", 0, data_root=dr)
            # a guarda não pode NEM criar nem tocar o arquivo (o defeito era
            # justamente acrescentar 2 linhas por invocação no-op)
            self.assertEqual((os.path.getsize(jp), os.path.getmtime(jp)), antes)

    def test_reexecucao_legitima_trunca_e_reassume(self):
        with tempfile.TemporaryDirectory() as dr:
            jp = self._fecha_run(dr)
            with AuditLogger.for_run("main", "c217", "DTLZ2", 0,
                                     data_root=dr, append=False) as log:
                log.header(D=15, M=3, maxfe=464, doe_hash="deadbeef")
                log.footer(status="ok", fe_final=464, n_geracoes=37)
            self.assertEqual([r["rec"] for r in _linhas(jp)],
                             ["header", "footer"])       # 1 par, não 2

    def test_run_em_andamento_aceita_append(self):
        # o fio real: o despachante abre e escreve o header; o runner/harness
        # ainda não fechou nada — append TEM de continuar valendo.
        with tempfile.TemporaryDirectory() as dr:
            with AuditLogger.for_run("main", "c217", "DTLZ2", 0,
                                     data_root=dr, append=False) as log:
                log.header(D=15, M=3, maxfe=464)
            with AuditLogger.for_run("main", "c217", "DTLZ2", 0,
                                     data_root=dr) as log:
                log.footer(status="failed", n_retries=0)
            jp = naming.jsonl_path("main", "c217", "DTLZ2", 0, data_root=dr)
            self.assertEqual([r["rec"] for r in _linhas(jp)],
                             ["header", "footer"])

    def test_footer_do_despachante_nao_bloqueia(self):
        # o footer do despachante NÃO carrega `fe_final` (quem contabiliza o
        # orçamento é o runner): ele não pode fechar o ⑥ para o retry/mescla.
        with tempfile.TemporaryDirectory() as dr:
            with AuditLogger.for_run("main", "c217", "DTLZ2", 0,
                                     data_root=dr, append=False) as log:
                log.footer(status="failed", n_retries=2, tempo_total_s=1.5)
            with AuditLogger.for_run("main", "c217", "DTLZ2", 0,
                                     data_root=dr) as log:
                log.event("ok_pode_acrescentar")

    def test_fe_final_null_dos_pares_espurios_nao_bloqueia(self):
        # a assinatura exata dos 94 pares espúrios (fe_final NULL) — bloquear
        # por eles impediria a própria re-execução da célula poluída.
        with tempfile.TemporaryDirectory() as dr:
            self._fecha_run(dr, fe_final=None)
            with AuditLogger.for_run("main", "c217", "DTLZ2", 0,
                                     data_root=dr) as log:
                log.event("ok_pode_acrescentar")

    def test_guarda_atravessa_linha_malformada(self):
        # ⑥ com splice/cauda de crash ANTES do footer de fechamento: a guarda
        # tem de continuar decidindo (leitura tolerante, §17.5).
        with tempfile.TemporaryDirectory() as dr:
            jp = self._fecha_run(dr)
            with open(jp, encoding="utf-8") as fh:
                bom = fh.read()
            with open(jp, "w", encoding="utf-8") as fh:
                fh.write('{"ts":"2026-07-27T00:27:12Z","rec":"guar\n')
                fh.write(bom)
            with self.assertRaises(RunJaFechado):
                AuditLogger.for_run("main", "c217", "DTLZ2", 0, data_root=dr)

    def test_footer_fechado_devolve_o_footer(self):
        # o helper é também o fallback-footer do O-21/E-04 (o stack MATLAB
        # certifica a própria falha no footer do ⑥, não no ⑤).
        with tempfile.TemporaryDirectory() as dr:
            jp = self._fecha_run(dr)
            rec = footer_fechado(jp)
            self.assertEqual(rec["status"], "ok")
            self.assertEqual(rec["fe_final"], 464)
            self.assertIsNone(footer_fechado(os.path.join(dr, "nao_existe.jsonl")))


class TestEscritaAtomicaB11(unittest.TestCase):
    """B-11: 1 linha = 1 `os.write` sob O_APPEND; > PIPE_BUF sob `flock`."""

    def test_linha_maior_que_o_limite_sai_inteira(self):
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "grande.jsonl")
            gordo = {"chave_%d" % i: "x" * 64 for i in range(400)}   # ~30 KB
            with AuditLogger(p, append=False) as log:
                log.header(sigma_dict=gordo)
                log.footer(status="ok", fe_final=1)
            recs = _linhas(p)
            self.assertEqual(len(recs), 2)
            self.assertGreater(len(json.dumps(recs[0])), LIMITE_ATOMICO_B)
            self.assertEqual(recs[0]["sigma_dict"], gordo)

    def test_sem_buffer_a_linha_e_visivel_na_hora(self):
        # o ⑥ é stream de auditoria: um SIGKILL não pode engolir linhas já
        # emitidas (é o que o kill-test do G5 vai exigir).
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "vivo.jsonl")
            log = AuditLogger(p, append=False)
            try:
                log.decision(caminho="estado_1", motivo="smoke")
                self.assertEqual(len(_linhas(p)), 1)
            finally:
                log.close()

    def test_8_escritores_concorrentes_todas_as_linhas_parseaveis(self):
        """O teste de aceitação do B-11: 8 processos × 10.000 linhas ⇒ 80.000
        linhas, todas parseáveis, nenhuma spliced."""
        n_proc, n_linhas = 8, 10_000
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "concorrente.jsonl")
            drv = os.path.join(dr, "escritor.py")
            with open(drv, "w", encoding="utf-8") as fh:
                fh.write(_ESCRITOR)
            procs = [subprocess.Popen(
                [sys.executable, drv, _RAIZ, p, str(tag), str(n_linhas)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for tag in range(n_proc)]
            for pr in procs:
                _, err = pr.communicate(timeout=600)
                self.assertEqual(pr.returncode, 0, err.decode()[-2000:])

            por_escritor, mal = {}, []
            with open(p, encoding="utf-8") as fh:
                for i, linha in enumerate(fh):
                    try:
                        rec = json.loads(linha)
                    except ValueError:
                        mal.append((i, linha[:120]))
                        continue
                    por_escritor.setdefault(rec["escritor"], set()).add(rec["i"])
                    # payload íntegro: o splice cortava a linha no meio do JSON
                    self.assertEqual(len(rec["pad"]), rec["n_pad"])
            self.assertEqual(mal, [], f"{len(mal)} linhas spliced")
            self.assertEqual(sorted(por_escritor), list(range(n_proc)))
            for tag, vistos in por_escritor.items():
                self.assertEqual(len(vistos), n_linhas,
                                 f"escritor {tag}: {len(vistos)} de {n_linhas}")

    def test_dono_do_arquivo_nao_atropela_os_outros_escritores(self):
        """O controle que DISCRIMINA o B-11.

        O rito `append=False` (o dono da célula: runner/harness) abria em `"w"`,
        cujo handle escreve no PRÓPRIO deslocamento — a descarga do buffer dele
        passa por cima do que outro escritor já pôs no fim do arquivo. Medido
        neste MESMO cenário com a semântica antiga (dono `"w"` + 2 filhos `"a"`,
        3×5.000 linhas): os filhos perdem **2.903 de 10.000 linhas** e sai **1
        linha malformada** — a família do `main/b1/WFG1` (49 de 931 spliced, 0
        footer) e do `moead_media/swap_small-lhs_ZDT1` (2 escritores, retrocesso
        de 134,3 s). Dois escritores `"w"` (dois processos da mesma célula, a
        janela O-19) perdiam metade: 5.000 de 10.000. Com O_APPEND em toda
        abertura o truncamento acontece 1× no open e nada posterior se perde.
        """
        n_filho, n_linhas = 2, 5_000
        with tempfile.TemporaryDirectory() as dr:
            p = os.path.join(dr, "dono_e_convidados.jsonl")
            drv = os.path.join(dr, "escritor.py")
            with open(drv, "w", encoding="utf-8") as fh:
                fh.write(_ESCRITOR)
            dono = AuditLogger(p, append=False)      # trunca ANTES de qualquer filho
            try:
                procs = [subprocess.Popen(
                    [sys.executable, drv, _RAIZ, p, str(tag), str(n_linhas)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    for tag in range(1, n_filho + 1)]
                for i in range(n_linhas):            # o dono escreve CONCORRENTE
                    dono.event("linha", escritor=0, i=i, n_pad=32, pad="z" * 32)
                for pr in procs:
                    _, err = pr.communicate(timeout=600)
                    self.assertEqual(pr.returncode, 0, err.decode()[-2000:])
            finally:
                dono.close()

            por_escritor = {}
            with open(p, encoding="utf-8") as fh:
                for linha in fh:
                    rec = json.loads(linha)          # nenhuma linha malformada
                    por_escritor.setdefault(rec["escritor"], set()).add(rec["i"])
            self.assertEqual(sorted(por_escritor), list(range(n_filho + 1)))
            for tag, vistos in por_escritor.items():
                self.assertEqual(len(vistos), n_linhas,
                                 f"escritor {tag}: {len(vistos)} de {n_linhas}")


class TestWriterMATLABDoSexto(unittest.TestCase):
    """[B-11] O ⑥ tem DOIS writers e o outro é o MATLAB.

    `src/experiment.m:jsonl_open` abria em `'w'` — deslocamento próprio, a
    semântica que perde linha (§ do teste acima). Não há como exercitá-lo aqui
    (o engine MATLAB não importa no venv da suíte), então o que se cobra é a
    PARIDADE do fonte, no molde de `tests/test_fio_sweep.py`.
    """

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(_RAIZ, "src", "experiment.m"),
                  encoding="utf-8", errors="replace") as fh:
            fonte = fh.read()
        i = fonte.index("function fid = jsonl_open(path)")
        cls.corpo = fonte[i:fonte.index("\nfunction ", i + 1)]

    def test_jsonl_open_trunca_uma_vez_e_devolve_handle_em_append(self):
        c = self.corpo
        for lit in ("fopen(path, 'w')", "fclose(fid)", "fopen(path, 'a')"):
            self.assertIn(lit, c, f"{lit} ausente de jsonl_open")
        # a ordem é o contrato: trunca (o dono assume o ⑥) → fecha → append
        self.assertLess(c.index("fopen(path, 'w')"), c.index("fclose(fid)"))
        self.assertLess(c.index("fclose(fid)"), c.index("fopen(path, 'a')"))
        # e o handle DEVOLVIDO é o de append, não o de truncamento
        self.assertGreater(c.rindex("fopen(path, 'a')"),
                           c.rindex("fopen(path, 'w')"))

    def test_o_sexto_nao_tem_outro_fopen_no_stack_matlab(self):
        # ERRATA ao PLANO F5/B-11 ("src/b1_instrument.m: 2 handles no mesmo
        # arquivo"): não há 2º handle — só `experiment.m` abre arquivo no stack
        # MATLAB, 1 fid por run. Se um 2º aparecer, o B-11 volta pela outra porta.
        alheios = []
        for nome in sorted(os.listdir(os.path.join(_RAIZ, "src"))):
            if not nome.endswith(".m") or nome == "experiment.m":
                continue
            with open(os.path.join(_RAIZ, "src", nome),
                      encoding="utf-8", errors="replace") as fh:
                if "fopen(" in fh.read():
                    alheios.append(nome)
        self.assertEqual(alheios, [])


#: Escritor do teste de concorrência: 1 em cada 10 linhas passa de
#: `LIMITE_ATOMICO_B` (é a faixa do header/sigma_dict, onde o splice de
#: `main/b1/WFG1` aconteceu) — o resto fica na faixa atômica por O_APPEND.
_ESCRITOR = '''\
import sys
sys.path.insert(0, sys.argv[1])
from src.audit_log import AuditLogger, LIMITE_ATOMICO_B

path, tag, n = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
log = AuditLogger(path, append=True)
try:
    for i in range(n):
        n_pad = (LIMITE_ATOMICO_B * 4) if i % 10 == 0 else 32
        log.event("linha", escritor=tag, i=i, n_pad=n_pad, pad="z" * n_pad)
finally:
    log.close()
'''


if __name__ == "__main__":
    unittest.main()
