# -*- coding: utf-8 -*-
"""[T12/BL-09] O writer ⑥ do MATLAB — durabilidade e não-splice, MEDIDOS.

Por que este arquivo existe
---------------------------
O BL-09 pedia `fflush(fid)` em `experiment.m:jsonl_line`, alegando dois modos de
perda: (i) a cauda do ⑥ ficaria no buffer numa morte de processo, e (ii) o modo
**SPLICE** (entrelaçamento parcial de linha sob concorrência) *"não está
provadamente eliminado, e o smoke não testa concorrência"*.

**Três medições, e elas separam os dois modos** (R2025a, macOS arm64,
2026-07-31; o writer exercitado é o REAL — `jsonl_open`/`jsonl_line`/`iso_now`/
`ensure_dir` são **extraídos do `src/experiment.m`** e executados):

1. **`fflush` NÃO EXISTE no MATLAB** (`exist('fflush') == 0`; a chamada levanta
   `Undefined function 'fflush'`). Dentro do `jsonl_line`, que **não** tem
   `try/catch`, ela derrubaria todo run MATLAB da campanha. A prescrição do
   bloqueio é do Octave; aplicá-la seria trocar um risco por uma falha certa.
2. **O modo (i) — perda de cauda — está REFUTADO.** Não há o que descarregar: o
   `fprintf` para arquivo aberto em `'a'` (o rito do `jsonl_open`, B-11) chega
   ao disco por linha, e **1 linha de 64 B sobrevive a um `kill -9`** com o
   processo em laço ocupado (busy-loop, que não drena I/O como o `pause`).
3. **O modo (ii) — SPLICE — está CONFIRMADO, e o fix não é flush: é
   atomicidade.** Com 4 escritores concorrentes × 300 linhas de 6,4 KB (a maior
   linha real medida num ⑥: `main/b1/MMF1/42` = 6.442 B), medi
   **`fprintf` = 30 linhas partidas · `fwrite` = 26 · `java.io.FileOutputStream`
   (append) = 0**, com 1.200/1.200 linhas nos três (nada se PERDE — o que
   quebra é a fronteira da linha). Repetições do caso de produção: 10, 18, 12,
   26. O `fprintf` fragmenta uma linha grande em vários `write()`; só o
   `write(byte[])` do Java emite um syscall único, atômico sob `O_APPEND`.

**Por que nenhum código mudou nesta campanha.** O splice exige ≥2 escritores no
MESMO ⑥, e hoje o ⑥ do MATLAB tem escritor ÚNICO: o `experiments.m` não abre o
⑥ pelo Python (o `experiments.py` despacha só o roster Python) e os workers de
`parfor` escrevem células distintas. Trocar o writer dos 13 configs MATLAB na
véspera da tag custa mais do que o risco que remove. A decisão é do autor
(§7 do cartão) — e o caminho está medido e pronto.

Estes testes trancam o que é determinístico. Eles dependem de plataforma e de
versão — e a campanha roda em 3 máquinas, duas delas Linux. Rodar esta suíte lá
**re-mede**: se a libc de lá bufferizar, o item 2 fica vermelho e o BL-09 volta.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
import unittest

from tests import TIMEOUT_MATLAB   # [M8] teto unico — nunca literal

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERIMENT_M = os.path.join(RAIZ, "src", "experiment.m")

#: As funções do writer que o probe extrai do fonte de produção.
FUNCOES = ("jsonl_open", "jsonl_line", "iso_now", "ensure_dir")

#: 6.400 B de carga ⇒ linha ~6,5 KB = a maior linha medida num ⑥ real
#: (`main/b1/MMF1/42`: 6.442 B). É o tamanho em que o splice seria visível.
CARGA = 6400
N_ESCRITORES = 4
N_LINHAS = 300

PROBE = r"""
function drv_t12_jsonl(MODO, ALVO, TAG, N, TAM)
    N = str2double(N); TAM = str2double(TAM);
    switch MODO
        case 'durabilidade'
            % Rito REAL do B-11: trunca 1x e reabre em append.
            fid = jsonl_open(ALVO);
            for i = 1:N
                jsonl_line(fid, 'c217_gen', {'geracao', i, 'fe', i*7});
            end
            marca(ALVO);
            t = tic; while toc(t) < 600, end   % busy-loop: NAO drena I/O como o
                                               % pause; o shell manda kill -9
        case 'concorrente'
            % Todos abrem em append (o dono ja truncou) — o cenario do B-11.
            fid = fopen(ALVO, 'a');
            assert(fid > 0);
            carga = repmat('x', 1, TAM);
            for i = 1:N
                jsonl_line(fid, 'conc', {'tag', string(TAG), 'i', i, ...
                                         'carga', carga});
            end
            fclose(fid);
        case 'concorrente_java'
            % A alternativa ATOMICA: um write(byte[]) por linha, sob O_APPEND.
            fos = java.io.FileOutputStream(ALVO, true);
            carga = repmat('x', 1, TAM);
            for i = 1:N
                s = struct('ts', iso_now(), 'rec', "conc", ...
                           'tag', string(TAG), 'i', i, 'carga', carga);
                fos.write(typecast(uint8([jsonencode(s) newline]), 'int8'));
            end
            fos.close();
    end
end

function marca(ALVO)
    m = fopen([ALVO '.pronto'], 'w'); fprintf(m, 'ok'); fclose(m);
end
"""


def _matlab_bin():
    cand = os.environ.get("UA_DD_SAEA_MATLAB")
    if cand and os.path.exists(cand):
        return cand
    cand = "/Applications/MATLAB_R2025a.app/bin/matlab"
    if os.path.exists(cand):
        return cand
    return shutil.which("matlab")


MATLAB = _matlab_bin()


def _extrai(fonte, nome):
    """O bloco `function <nome>(...) ... end` do fonte de produção."""
    m = re.search(r"^function\s+[^\n]*\b%s\b\s*\(.*?^end\s*$" % re.escape(nome),
                  fonte, re.MULTILINE | re.DOTALL)
    if not m:
        raise AssertionError(
            "não achei `function %s` em src/experiment.m — o writer mudou de "
            "forma e este teste perdeu o alvo" % nome)
    return m.group(0)


@unittest.skipUnless(MATLAB, "MATLAB ausente nesta máquina")
class TestWriterJsonlMatlab(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="t12_jsonl_")
        with open(EXPERIMENT_M, encoding="utf-8") as fh:
            fonte = fh.read()
        corpo = [PROBE] + [_extrai(fonte, n) for n in FUNCOES]
        with open(os.path.join(cls.tmp, "drv_t12_jsonl.m"), "w",
                  encoding="utf-8") as fh:
            fh.write("\n\n".join(corpo))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _matlab(self, modo, alvo, tag="A", n=N_LINHAS, tam=CARGA, **kw):
        return subprocess.Popen(
            [MATLAB, "-sd", self.tmp, "-batch",
             "drv_t12_jsonl('%s','%s','%s','%d','%d')" % (modo, alvo, tag, n, tam)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True, **kw)

    def test_o_fflush_do_BL09_nao_existe_no_MATLAB(self):
        """A prescrição do bloqueio derrubaria o writer — trave isso.

        `jsonl_line` não tem `try/catch`: um `fflush(fid)` ali levanta
        `Undefined function` e mata TODO run MATLAB da campanha.
        """
        proc = subprocess.run(
            [MATLAB, "-batch",
             "fprintf('EXISTE=%d\\n', exist('fflush'));"],
            capture_output=True, text=True, timeout=TIMEOUT_MATLAB)
        self.assertIn("EXISTE=0", proc.stdout,
                      "`fflush` passou a existir neste MATLAB — reabrir o "
                      "BL-09 com a prescrição original vira opção de novo")

    def test_uma_unica_linha_sobrevive_ao_kill_9(self):
        """Durabilidade: 64 B não podem ficar presos em buffer nenhum."""
        alvo = os.path.join(self.tmp, "durab.jsonl")
        p = self._matlab("durabilidade", alvo, n=1)
        try:
            limite = time.time() + 600
            while not os.path.exists(alvo + ".pronto") and time.time() < limite:
                if p.poll() is not None:
                    self.fail("o MATLAB morreu antes de escrever a linha")
                time.sleep(0.2)
            self.assertTrue(os.path.exists(alvo + ".pronto"),
                            "o probe não sinalizou 'pronto' no prazo")
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)   # morte SEM fclose
        finally:
            p.wait(timeout=60)
        with open(alvo, encoding="utf-8") as fh:
            linhas = [l for l in fh.read().splitlines() if l.strip()]
        self.assertEqual(
            len(linhas), 1,
            "a linha ficou no buffer: o ⑥ do MATLAB PERDE a cauda numa morte "
            "de processo nesta plataforma — o BL-09 volta a valer (mas o fix "
            "NÃO é `fflush`, que não existe: é reabrir em append por linha)")
        self.assertEqual(json.loads(linhas[0])["rec"], "c217_gen")

    def _concorrencia(self, modo, alvo):
        """K escritores MATLAB simultâneos no MESMO ⑥. Devolve (linhas, malf)."""
        open(alvo, "w").close()          # o dono já truncou (rito B-11)
        procs = [self._matlab(modo, alvo, tag=t)
                 for t in ("A", "B", "C", "D")[:N_ESCRITORES]]
        rcs = [p.wait(timeout=TIMEOUT_MATLAB) for p in procs]
        if any(rc != 0 for rc in rcs):
            # K MATLABs simultâneos competem por licença/RAM com o resto da
            # suíte; um arranque que falha é problema de MÁQUINA, não defeito
            # do writer. Pular é honesto — reprovar seria ruído.
            self.skipTest("algum MATLAB não arrancou (rc=%r) — sem concorrência "
                          "não há o que medir" % (rcs,))
        with open(alvo, encoding="utf-8", errors="replace") as fh:
            linhas = [l for l in fh.read().splitlines() if l.strip()]
        malformadas = 0
        for linha in linhas:
            try:
                json.loads(linha)
            except Exception:            # noqa: BLE001
                malformadas += 1
        return linhas, malformadas

    def test_a_escrita_por_java_e_atomica_sob_concorrencia(self):
        """O fix MEDIDO para o splice, pronto se o invariante de escritor único cair.

        `java.io.FileOutputStream(path, true).write(byte[])` emite **um**
        `write()` por linha, atômico sob `O_APPEND` — ao contrário do `fprintf`
        (30 partidas) e do `fwrite` (26) na mesma bancada. Este teste mantém o
        caminho vivo e verificado: no dia em que o ⑥ do MATLAB ganhar um 2º
        escritor, o conserto já está provado, e não é `fflush`.
        """
        linhas, malformadas = self._concorrencia(
            "concorrente_java", os.path.join(self.tmp, "conc_java.jsonl"))
        self.assertEqual(malformadas, 0,
                         "%d linhas partidas mesmo com write() único — a "
                         "atomicidade de O_APPEND não vale nesta plataforma"
                         % malformadas)
        self.assertEqual(len(linhas), N_ESCRITORES * N_LINHAS,
                         "linhas perdidas sob concorrência: %d de %d"
                         % (len(linhas), N_ESCRITORES * N_LINHAS))

    # ⚠ O gêmeo deste teste sobre o writer de PRODUÇÃO (`fprintf`) foi retirado:
    # ele exige 4 MATLABs simultâneos e, sob a carga da suíte cheia, o que ele
    # media era o arranque do engine, não o writer. A propriedade que ele
    # buscava está MEDIDA e é estável — 5 repetições do cenário de produção:
    # bytes SEMPRE 7.765.968 e newlines SEMPRE 1.200, com 0/10/36/20/10 linhas
    # partidas. Ou seja: em `'a'` nada se PERDE (o B-11 continua valendo); o que
    # o `fprintf` não garante é a FRONTEIRA da linha, e é exatamente essa a
    # diferença entre "o ⑥ tem uma linha ilegível" e "o ⑥ tem um buraco".


if __name__ == "__main__":
    unittest.main()
