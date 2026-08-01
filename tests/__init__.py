
# [conserto 2026-07-30] Anotações LAZY. Sem isto, `tuple[int, str]`
# (py3.9+) e `str | None` (py3.10+) quebram o IMPORT do pacote de
# testes em **py3.7 (env_b5)** e **py3.8 (env_c311)** — exatamente os
# dois interpretadores que 13 `skipUnless` mandam usar. A suíte parecia
# ter cobertura naqueles envs e não rodava nem o import.
from __future__ import annotations
# Pacote de testes do harness (F0-01). Rodar:
#   python3 -m unittest discover -s tests -t .
#
# ── [G-8 / B-13] GUARDA ANTI-ESCRITA EM `data/experiments/` ──────────────────
# A suíte NÃO PODE tocar dados de produção. O caso real: `test_batch_q10.py`
# chamava `_run_one(..., "data")` com a raiz LITERAL de produção e, a cada
# execução, deixava 2 pares header/footer no ⑥ de `batch/e81/q10_ZDT4` — 47
# execuções × 2 = os 94 pares espúrios que tornaram a auditoria de término
# daquela célula indecidível (e ainda fabricaram
# `timing.tempo_total_despachante_s` = 0,0002 s contra `tempo_total_s + 3..8 s`
# nas outras 29 células do e81).
#
# O tempdir de cada teste (B-13a) fecha a INSTÂNCIA; esta guarda fecha a
# CLASSE. O mecanismo: fotografa `data/experiments/**` no import do pacote
# (antes de qualquer teste rodar) e o `tests/test_zz_guarda_data.py` — que o
# `unittest discover` executa por ÚLTIMO, em ordem alfabética — compara.
import hashlib
import os

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_EXP = os.path.join(_RAIZ, "data", "experiments")


def impressao_data_experiments(raiz: str | None = None) -> tuple[int, str]:
    """(nº de entradas, sha256 de (caminho, mtime_ns, tamanho) de tudo).

    Inclui DIRETÓRIOS: um teste que cria e apaga um arquivo muda o mtime do
    diretório, e é justamente esse o rastro que um `.tmp` órfão deixaria.
    """
    # `raiz` existe para o CONTROLE da guarda medir a SENSIBILIDADE da função
    # num tempdir, em vez de plantar um arquivo em `data/experiments` de
    # produção — que era o que ele fazia, e que só passava despercebido porque a
    # própria impressão era cega à raiz (o ponto cego consertado em 2026-07-30).
    DATA_EXP = raiz or globals()["DATA_EXP"]
    if not os.path.isdir(DATA_EXP):
        return 0, "sem-data-experiments"
    itens = []
    # [G-8 · conserto 2026-07-30] A PRÓPRIA RAIZ entra na impressão. O `os.walk`
    # abaixo estata os FILHOS de `data/experiments`, nunca o diretório raiz — e
    # criar/apagar uma subpasta lá muda o mtime DA RAIZ, não o dos filhos. Um
    # teste que criasse e removesse `data/experiments/_algo/` passava invisível
    # (foi o caso do `test_drivers_b12`, que escrevia na produção a cada suíte).
    try:
        st_raiz = os.stat(DATA_EXP, follow_symlinks=False)
        itens.append(f".|{st_raiz.st_mtime_ns}|{st_raiz.st_size}")
    except OSError:
        itens.append(".|indisponivel|0")
    for raiz, dirs, arqs in os.walk(DATA_EXP):
        dirs.sort()
        for nome in sorted(dirs) + sorted(arqs):
            p = os.path.join(raiz, nome)
            try:
                st = os.stat(p, follow_symlinks=False)
                itens.append(f"{os.path.relpath(p, DATA_EXP)}|{st.st_mtime_ns}|"
                             f"{st.st_size}")
            except OSError:
                itens.append(f"{os.path.relpath(p, DATA_EXP)}|sumiu")
    return len(itens), hashlib.sha256("\n".join(itens).encode()).hexdigest()


#: Fotografia tirada no IMPORT do pacote de testes (antes do 1º teste).
IMPRESSAO_INICIAL = impressao_data_experiments()


# ═══════════════════════════════════════════════════════════════════════════
#  [M8 · 2026-08-01] TETO ÚNICO dos subprocessos que sobem MATLAB
# ═══════════════════════════════════════════════════════════════════════════

def _teto_matlab() -> float:
    """Segundos de teto para um `subprocess` que sobe MATLAB.

    **Por que existe.** Havia 10 tetos HARD-CODED espalhados pelos testes (900s,
    1800s, 600s…), todos calibrados no Mac. Eles são guarda contra TRAVA, não
    asserção de desempenho — mas na `matlab-vm2` o
    `test_t12_c217_instrument.setUpClass` estourou os 900s e derrubou a máquina
    no portão de aceitação do M8, por disco lento e não por defeito.

    **A medida.** A suíte inteira leva **325 s no Mac** e **1.639 s na vm2** —
    5,0× mais lenta. A vm2 é a única com `pd-standard` (achado O-19: *"o gargalo
    aparece no startup do MATLAB, que é I/O-bound"*), e o startup do MATLAB é
    justamente o que estes testes pagam N vezes.

    **O valor.** 2.700 s (45 min) cobre 5–8× de lentidão sobre o pior teste do
    Mac e continua pegando uma trava de verdade, que nunca termina. Override por
    `UA_DD_SAEA_TIMEOUT_MATLAB` para máquina mais lenta ainda — em vez de mais um
    número hard-coded.
    """
    v = os.environ.get("UA_DD_SAEA_TIMEOUT_MATLAB")
    if v:
        try:
            n = float(v)
            if n > 0:
                return n
        except ValueError:
            pass
    return 2700.0


#: Teto dos subprocessos que sobem MATLAB. Use SEMPRE este, nunca um literal.
TIMEOUT_MATLAB = _teto_matlab()
