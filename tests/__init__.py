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


def impressao_data_experiments() -> tuple[int, str]:
    """(nº de entradas, sha256 de (caminho, mtime_ns, tamanho) de tudo).

    Inclui DIRETÓRIOS: um teste que cria e apaga um arquivo muda o mtime do
    diretório, e é justamente esse o rastro que um `.tmp` órfão deixaria.
    """
    if not os.path.isdir(DATA_EXP):
        return 0, "sem-data-experiments"
    itens = []
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
