#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[T14.11] Gera o mapa semente→máquina BALANCEADO POR CUSTO da campanha M8/M9.

**O problema.** A O-16 ("um config, uma máquina") foi APOSENTADA para o resultado
(T13/D1): a máquina constante nas 30 sementes de um config vira offset
SISTEMÁTICO, e média dilui ruído aleatório, não viés. A alocação passa a ser
**por semente** — cada máquina roda todos os pares de ALGUMAS sementes. Falta o
mapa: quais sementes em qual máquina, sem que a máquina mais carregada estique o
wall da campanha.

**A estrutura do problema (e por que ela é simples).** O grid é SIMÉTRICO em
semente: as mesmas 695 células valem para as 30 sementes. Logo o custo de uma
semente é o MESMO para qualquer semente, e balancear é distribuir CONTAGENS —
não escolher quais sementes. O que não é trivial é a partição por
ELEGIBILIDADE: nem toda máquina roda tudo.

**Grupos de execução.** Em vez de dois mapas fixos ("MATLAB" e "Python"), os
pares são agrupados por CONJUNTO DE MÁQUINAS ELEGÍVEIS — derivado de
`envs.json:alg_to_env` × os `envs` declarados de cada máquina. Numa frota
homogênea isso colapsa EXATAMENTE nos dois mapas do cartão (MATLAB nas 7 com
licença, Python nas 9); se o autor declarar que uma VM não tem `env_b5`, um
terceiro grupo aparece sozinho — a restrição de env vira consequência, não
remendo.

**Custo.** `f5/tempo_f52d.csv` (wall MEDIDO da s42) por célula. As 30 células
sem medida (19 c154 · 9 c262 · 1 b1 · 1 c311) são IMPUTADAS pela mediana do
próprio alg — e a imputação vai declarada no artefato, célula a célula: elas são
justamente as mais caras do estudo, e descartá-las subestimaria o Python.

**Objetivo.** minimizar `max_i (carga_i / jobs_i)` — o wall da máquina mais
carregada. `jobs` é a capacidade (runs simultâneos; 1 run = 1 core, D79).

Uso:
    python3 scripts/mapa_sementes.py            # gera o artefato
    python3 scripts/mapa_sementes.py --check    # só confere o que está no disco
    python3 scripts/mapa_sementes.py --frota f.json
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ART = os.path.join(ROOT, "claude_code_context", "artifacts")
GRID = os.path.join(ART, "runs_matrix.csv")
ENVS = os.path.join(ART, "envs.json")
FROTA = os.path.join(ART, "frota.json")
TEMPO = os.path.join(ROOT, "f5", "tempo_f52d.csv")
SAIDA = os.path.join(ART, "mapa_sementes.json")

#: Frota DEFAULT — 9 máquinas, 2 delas Python-only (repasse T13 §12.3).
#: ⚠ PENDENTE DO AUTOR: os nomes/`jobs`/`envs` das 5 máquinas NOVAS não existem
#: em lugar nenhum do repo (é o item §12.2, "quem provisiona?"). As 4 conhecidas
#: vêm dos perfis REAIS do `lote3s.sh` (jobs) e do que o repo declara sobre elas.
#: Editar `artifacts/frota.json` e re-rodar este script refaz o mapa inteiro.
FROTA_DEFAULT = {
    "_pendente_autor": (
        "Os nomes, o `jobs` e os `envs` das 5 máquinas NOVAS são PLACEHOLDER — "
        "o repo só conhece mac/v5/v6/vm3 (perfis do lote3s.sh). Corrija aqui e "
        "rode `python3 scripts/mapa_sementes.py` para refazer o mapa."),
    "maquinas": [
        # as 4 que o repo conhece (jobs = perfil real do lote3s.sh)
        {"nome": "mac", "jobs": 4, "matlab": True,
         "envs": ["env_main", "env_b5", "env_c311", "env_e81_qpots"],
         "fonte": "lote3s.sh perfil `mac` + envs.json (único host com os 4 venvs)"},
        {"nome": "vm3", "jobs": 6, "matlab": True, "envs": ["env_main"],
         "fonte": "lote3s.sh perfil `vm3` — 'única máquina com licença' na s42"},
        {"nome": "v5", "jobs": 12, "matlab": False, "envs": ["env_main"],
         "fonte": "lote3s.sh perfil `v5` · PYTHON-ONLY (repasse §12.3)"},
        {"nome": "v6", "jobs": 6, "matlab": False, "envs": ["env_main"],
         "fonte": "lote3s.sh perfil `v6` · PYTHON-ONLY (repasse §12.3)"},
        # as 5 NOVAS — placeholder
        {"nome": "vm1", "jobs": 6, "matlab": True,
         "envs": ["env_main", "env_b5", "env_c311", "env_e81_qpots"],
         "fonte": "PLACEHOLDER (§12.2 — provisionamento do autor)"},
        {"nome": "vm2", "jobs": 6, "matlab": True,
         "envs": ["env_main", "env_b5", "env_c311", "env_e81_qpots"],
         "fonte": "PLACEHOLDER (§12.2)"},
        {"nome": "vm4", "jobs": 6, "matlab": True,
         "envs": ["env_main", "env_b5", "env_c311", "env_e81_qpots"],
         "fonte": "PLACEHOLDER (§12.2)"},
        {"nome": "vm7", "jobs": 6, "matlab": True,
         "envs": ["env_main", "env_b5", "env_c311", "env_e81_qpots"],
         "fonte": "PLACEHOLDER (§12.2)"},
        {"nome": "vm8", "jobs": 6, "matlab": True,
         "envs": ["env_main", "env_b5", "env_c311", "env_e81_qpots"],
         "fonte": "PLACEHOLDER (§12.2)"},
    ],
}


# ── entradas ────────────────────────────────────────────────────────────────

def _grid() -> list[dict]:
    with open(GRID, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _custo_por_celula() -> tuple[dict, dict]:
    """(custo_s por (exp,alg,problema), imputadas). Mediana dos walls medidos."""
    medidos = collections.defaultdict(list)
    with open(TEMPO, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            medidos[(r["exp"], r["alg"], r["problema"])].append(float(r["wall_s"]))
    custo = {k: statistics.median(v) for k, v in medidos.items()}
    por_alg = collections.defaultdict(list)
    for (_, alg, _), v in custo.items():
        por_alg[alg].append(v)
    imputadas = {}
    for r in _grid():
        k = (r["exp"], r["alg"], r["problema"])
        if k in custo:
            continue
        if not por_alg.get(r["alg"]):
            raise SystemExit(f"sem base para imputar {k} — pára-e-loga (D81).")
        custo[k] = statistics.median(por_alg[r["alg"]])
        imputadas["/".join(k)] = round(custo[k], 3)
    return custo, imputadas


def _frota(path: str | None) -> dict:
    alvo = path or (FROTA if os.path.exists(FROTA) else None)
    if alvo is None:
        return FROTA_DEFAULT
    with open(alvo, encoding="utf-8") as fh:
        return json.load(fh)


def _alg_to_env() -> dict:
    """alg → nome do env. O `alg_to_env` do artefato traz `{stack, env}`."""
    with open(ENVS, encoding="utf-8") as fh:
        d = json.load(fh)
    mapa = {}
    for alg, v in (d.get("alg_to_env") or {}).items():
        mapa[alg] = v["env"] if isinstance(v, dict) else v
    if not mapa:                              # deriva de `environments.algs`
        for env, v in d["environments"].items():
            for a in (v.get("algs") or ()):
                mapa[a.split("(")[0]] = env
    return mapa


# ── o balanceamento ─────────────────────────────────────────────────────────

def _elegiveis(alg: str, env: str, stack: str, maquinas: list[dict]) -> tuple:
    if stack == "matlab":
        return tuple(m["nome"] for m in maquinas if m.get("matlab"))
    return tuple(m["nome"] for m in maquinas
                 if env in (m.get("envs") or ()) and not _so_matlab(m))


def _so_matlab(m: dict) -> bool:
    return not (m.get("envs") or ())


def _distribui(n_sementes: int, custo_semente: float, elegiveis: list[str],
               jobs: dict, carga: dict) -> dict:
    """Guloso LPT: a cada semente, quem ficaria com o MENOR wall leva."""
    fora = {m: 0 for m in elegiveis}
    for _ in range(n_sementes):
        alvo = min(elegiveis,
                   key=lambda m: ((carga[m] + custo_semente) / jobs[m], m))
        fora[alvo] += 1
        carga[alvo] += custo_semente
    return fora


def _refina(alloc: dict, grupos: dict, jobs: dict, carga: dict,
            max_passos: int = 20_000) -> int:
    """Busca local GLOBAL: move 1 semente por vez para baixar o wall MÁXIMO.

    O guloso trata um grupo por vez e não pode desfazer o que fez; o gargalo
    real nasce da INTERAÇÃO (a máquina lenta que já levou uma semente cara do
    grupo grande). Aqui todos os grupos são movidos juntos, e só se aceita o
    movimento que reduz o wall máximo — critério do cartão ("minimizar o wall
    da máquina mais carregada"). Determinístico: empates caem no nome.
    """
    def wall(m):
        return carga[m] / jobs[m]

    passos = 0
    while passos < max_passos:
        pior = max(carga, key=lambda m: (wall(m), m))
        melhor_ganho, melhor_mov = 0.0, None
        for eleg, g in grupos.items():
            if pior not in eleg or alloc[eleg][pior] <= 0:
                continue
            c = g["custo_semente_s"]
            for destino in eleg:
                if destino == pior:
                    continue
                novo_pior = (carga[pior] - c) / jobs[pior]
                novo_dest = (carga[destino] + c) / jobs[destino]
                # o max LOCAL do par tem de cair — e sem estourar o máximo global
                antes = max(wall(pior), wall(destino))
                depois = max(novo_pior, novo_dest)
                ganho = antes - depois
                if ganho > melhor_ganho + 1e-9:
                    melhor_ganho, melhor_mov = ganho, (eleg, pior, destino, c)
        if melhor_mov is None:
            break
        eleg, origem, destino, c = melhor_mov
        alloc[eleg][origem] -= 1
        alloc[eleg][destino] += 1
        carga[origem] -= c
        carga[destino] += c
        passos += 1
    return passos


def construir(frota: dict) -> dict:
    maquinas = frota["maquinas"]
    nomes = [m["nome"] for m in maquinas]
    if len(set(nomes)) != len(nomes):
        raise SystemExit("frota com nome de máquina repetido — D81.")
    jobs = {m["nome"]: int(m.get("jobs", 1)) for m in maquinas}
    custo, imputadas = _custo_por_celula()
    a2e = _alg_to_env()
    grid = _grid()
    sementes = sorted({int(r["semente"]) for r in grid})

    # 1) pares (exp,alg) → grupo de elegibilidade + custo por semente
    pares = {}
    for r in grid:
        par = (r["exp"], r["alg"])
        if par not in pares:
            env = a2e.get(r["alg"], "env_main")
            pares[par] = {"stack": r["stack"], "env": env,
                          "eleg": _elegiveis(r["alg"], env, r["stack"], maquinas),
                          "custo_semente_s": 0.0, "n_celulas": 0}
        if int(r["semente"]) == sementes[0]:       # 1 semente = o padrão do grid
            pares[par]["custo_semente_s"] += custo[(r["exp"], r["alg"],
                                                    r["problema"])]
            pares[par]["n_celulas"] += 1

    # 2) grupos = pares com o MESMO conjunto de máquinas elegíveis
    grupos = collections.defaultdict(
        lambda: {"pares": [], "custo_semente_s": 0.0, "n_celulas": 0})
    for par, d in sorted(pares.items()):
        g = grupos[d["eleg"]]
        g["pares"].append("%s/%s" % par)
        g["custo_semente_s"] += d["custo_semente_s"]
        g["n_celulas"] += d["n_celulas"]
    for eleg, g in grupos.items():
        if not eleg:
            raise SystemExit(
                f"grupo SEM máquina elegível: {g['pares'][:3]}… — a frota não "
                f"cobre o grid. Pára-e-loga (D81).")

    # 3) guloso LPT (grupo mais caro primeiro) + busca local GLOBAL
    carga = {m: 0.0 for m in nomes}
    alloc = {}
    for eleg, g in sorted(grupos.items(),
                          key=lambda kv: -kv[1]["custo_semente_s"]):
        alloc[eleg] = _distribui(len(sementes), g["custo_semente_s"],
                                 list(eleg), jobs, carga)
    n_passos = _refina(alloc, grupos, jobs, carga)

    saida = {}
    for eleg, g in sorted(grupos.items(),
                          key=lambda kv: -kv[1]["custo_semente_s"]):
        # as sementes CONCRETAS: fatia contígua da lista canônica, determinística
        it, por_maq = iter(sementes), {}
        for m in eleg:
            por_maq[m] = [next(it) for _ in range(alloc[eleg][m])]
        saida[",".join(eleg)] = {
            "pares": g["pares"], "n_celulas_por_semente": g["n_celulas"],
            "custo_semente_h": round(g["custo_semente_s"] / 3600, 4),
            "elegiveis": list(eleg),
            "sementes_por_maquina": {m: v for m, v in por_maq.items() if v},
        }

    wall = {m: carga[m] / jobs[m] / 3600 for m in nomes}
    media = sum(wall.values()) / len(wall)
    desbal = max(abs(v - media) for v in wall.values()) / media if media else 0.0
    return {
        "_meta": {
            "artefato": "mapa_sementes.json",
            "gerado_por": "scripts/mapa_sementes.py (T14.11 / cartão §4)",
            "decisao": ("T13/D1 — a O-16 foi aposentada PARA O RESULTADO: a "
                        "alocação é POR SEMENTE, para a máquina virar ruído "
                        "aleatório entre repetições em vez de offset "
                        "sistemático (média dilui ruído, não viés)."),
            "custo": ("wall MEDIDO da s42 (`f5/tempo_f52d.csv`, mediana por "
                      "célula) × 30 sementes. O grid é SIMÉTRICO em semente, "
                      "então o custo de uma semente independe de QUAL semente — "
                      "balancear é repartir contagens."),
            "objetivo": ("minimizar max_i(carga_i / jobs_i) = o wall da "
                         "máquina mais carregada. Guloso LPT (grupo mais caro "
                         "primeiro) + busca local GLOBAL de 1 semente: %d "
                         "movimentos aceitos." % n_passos),
            "imputacao": ("%d células sem wall medido na s42 receberam a MEDIANA "
                          "DO PRÓPRIO ALG (são as mais caras do estudo — "
                          "descartá-las subestimaria o Python)." % len(imputadas)),
            "celulas_imputadas_h": {k: round(v / 3600, 4)
                                    for k, v in sorted(imputadas.items())},
            "grupos": ("os pares são agrupados por CONJUNTO DE MÁQUINAS "
                       "ELEGÍVEIS (stack MATLAB × `envs.json:alg_to_env` × os "
                       "`envs` de cada máquina). Numa frota homogênea isso dá "
                       "exatamente os DOIS mapas do cartão."),
            "consumidor": "scripts/lote3s.sh (LOTE_SEEDS derivado de LOTE_MAQ)",
            "frota": frota,
        },
        "sementes": sementes,
        "mapas": saida,
        "resumo": {
            "n_maquinas": len(nomes),
            "n_celulas_por_semente": sum(g["n_celulas"] for g in grupos.values()),
            "n_celulas_total": sum(g["n_celulas"] for g in grupos.values())
                               * len(sementes),
            "custo_total_h_core": round(sum(carga.values()) / 3600, 2),
            "wall_por_maquina_h": {m: round(wall[m], 2) for m in nomes},
            "wall_medio_h": round(media, 2),
            "wall_max_h": round(max(wall.values()), 2),
            "desbalanceamento_max": round(desbal, 6),
            "criterio": "desbalanceamento_max <= 0.10 (cartão T14.11)",
        },
    }


# ── conferência (o mesmo que o teste cobra) ─────────────────────────────────

def conferir(mapa: dict) -> list[str]:
    """Cobertura total, interseção vazia e desbalanceamento ≤10%."""
    erros = []
    grid = _grid()
    esperado = collections.Counter(
        (r["exp"], r["alg"], int(r["semente"])) for r in grid)
    visto = collections.Counter()
    n_cel = {}
    for r in grid:
        n_cel[(r["exp"], r["alg"])] = n_cel.get((r["exp"], r["alg"]), 0)
    for g in mapa["mapas"].values():
        for maq, seeds in g["sementes_por_maquina"].items():
            for par in g["pares"]:
                exp, alg = par.split("/", 1)
                for s in seeds:
                    visto[(exp, alg, s)] += 1
    faltando = sorted(set(esperado) - set(visto))
    if faltando:
        erros.append("%d (exp,alg,semente) sem máquina: %r…"
                     % (len(faltando), faltando[:3]))
    duplas = sorted(k for k, v in visto.items() if v > 1)
    if duplas:
        erros.append("%d (exp,alg,semente) em MAIS de uma máquina: %r…"
                     % (len(duplas), duplas[:3]))
    sobra = sorted(set(visto) - set(esperado))
    if sobra:
        erros.append("%d atribuições fora do grid: %r…" % (len(sobra), sobra[:3]))
    d = mapa["resumo"]["desbalanceamento_max"]
    if d > 0.10:
        erros.append("desbalanceamento %.1f%% > 10%%" % (100 * d))
    return erros


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frota", default=None)
    ap.add_argument("--check", action="store_true",
                    help="confere o artefato JÁ no disco (não regrava)")
    ap.add_argument("--saida", default=SAIDA)
    a = ap.parse_args(argv)

    if a.check:
        with open(a.saida, encoding="utf-8") as fh:
            mapa = json.load(fh)
    else:
        mapa = construir(_frota(a.frota))
    erros = conferir(mapa)
    r = mapa["resumo"]
    print("máquinas .............. %d" % r["n_maquinas"])
    print("células/semente ....... %d   (× %d sementes = %d)"
          % (r["n_celulas_por_semente"], len(mapa["sementes"]),
             r["n_celulas_total"]))
    print("custo total ........... %.1f h-core" % r["custo_total_h_core"])
    print("wall máx / médio ...... %.1f h / %.1f h" % (r["wall_max_h"],
                                                       r["wall_medio_h"]))
    print("desbalanceamento ...... %.2f%%  (critério ≤10%%)"
          % (100 * r["desbalanceamento_max"]))
    print("grupos ................ %d" % len(mapa["mapas"]))
    for chave, g in mapa["mapas"].items():
        print("  [%s] %d pares · %d células/semente · %.1f h/semente"
              % (chave, len(g["pares"]), g["n_celulas_por_semente"],
                 g["custo_semente_h"]))
        for m, s in g["sementes_por_maquina"].items():
            print("      %-6s %2d sementes  %s" % (m, len(s), s))
    if erros:
        print("\nREPROVADO:")
        for e in erros:
            print("  ✗", e)
        return 1
    print("\nOK — cobertura total, interseção vazia, desbalanceamento no critério.")
    if not a.check:
        with open(a.saida, "w", encoding="utf-8") as fh:
            json.dump(mapa, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("gravado: %s" % os.path.relpath(a.saida, ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
