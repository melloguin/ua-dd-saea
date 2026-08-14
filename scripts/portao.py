#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""portao.py — o DRIVER DE PORTÃO das baterias [DI-32 · T1+T3].

O `experiments.py`/`experiments.m` RODAM os runs mas não GATEIAM nenhum; este
script fecha a lacuna: roteia, POR RUN, o conjunto de gates aplicável ao config —

  1. `accept.py <cartão>`         — branch DEDICADO p/ os R3 (c122/c149/e81/b5/
                                    c311/piso-off); os R1/R2 caem no catch-all
                                    F0-01 (gate genérico por run: FE=31D−1 exato,
                                    4 camadas, CP-init) — que é o desenho.
  2. `auditar.py`                 — o validador de conteúdo (sonda/blocos/schema;
                                    regime auto-detectado).
  3. `final_eval.py --check`      — SÓ offline: a ⑦ __final é o endpoint OFICIAL
                                    do regime (reconstituível da ③, f real).

Uso:
  python3 scripts/portao.py --exp off --alg moead_media --problema MMF1 --semente 0
  python3 scripts/portao.py --varredura                      # TODO run em data/
  python3 scripts/portao.py --varredura --exp off            # só o offline
  python3 scripts/portao.py --varredura --alg c311           # só um config

O modo `--varredura` é TAMBÉM o driver de LOTE da ⑦ offline (T3): varre os
manifestos e roda o `--check` de cada run offline. Exit 0 ⟺ TUDO verde.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
PY = sys.executable

from src.manifest import OFFLINE_ALGS  # noqa: E402 — fonte única (DI-16.8)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from gates_proveniencia import (           # noqa: E402 — [T11-G6] G-1..G-4 + B-15
    gates_de_proveniencia, motivo_e_sancionado, especie_do_none,
    MARCA_NAO_AFERIVEL)

#: alg → cartão do accept. R3 = branches dedicados; R1/R2 = rótulo informativo
#: (o catch-all F0-01 roteia pelo `--alg`, não pelo nome do cartão).
CARTAO_POR_ALG = {
    "c122": "R3-c122", "c149": "R3-c149", "e81": "R3-e81",
    "b5r": "R3-b5", "b5m": "R3-b5",
    "c311": "R3-c311", "moead_media": "R3-piso-off",
    "treed_media": "T8-piso-big",   # [DI-35.2] catch-all tier-aware até o T8 fechar
    "c262": "R2-c262", "c154": "R2-c154",
    # [T6-batch] o piso do batch — gate genérico por-run (4 saídas + FE=11D−1+
    # 200q + CP-init do DoE online); sem branch dedicado (③ vazia, sem sonda).
    "sobol_batch": "T6-sobol_batch",
    **{a: f"R1-{a}" for a in ("c217", "c141", "b1", "b3", "b4", "e7", "c238",
                              "e74", "e103", "nsga2", "nsga3", "moead",
                              "smsemoa")},
}


def _sub(args: list[str]) -> tuple[bool, str]:
    """Roda um gate em subprocesso; devolve (verde?, última linha útil)."""
    r = subprocess.run([PY] + args, cwd=ROOT, capture_output=True, text=True)
    linhas = [ln for ln in (r.stdout + r.stderr).strip().splitlines() if ln.strip()]
    # [T15.10/B-07/DI-41] exit 2 = INCONCLUSIVO/NÃO-AFERÍVEL (None), não
    # vermelho — a distinção que impede incapacidade-de-medir virar reprovação.
    verde = True if r.returncode == 0 else (None if r.returncode == 2 else False)
    return verde, (linhas[-1][:110] if linhas else "")


def _manifesto_do_run(exp, alg, problema, semente, data_root) -> dict:
    """Lê o manifesto do run (dict vazio se ausente/ilegível)."""
    from src import naming
    root = data_root if os.path.isabs(data_root) else os.path.join(ROOT, data_root)
    try:
        with open(naming.manifest_path(exp, alg, problema, semente,
                                       data_root=root), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001 — sem manifesto ⇒ os gates dirão o resto
        return {}


def gates_de_um_run(exp: str, alg: str, problema: str, semente,
                    data_root: str = "data", *,
                    modo: str = "campanha") -> list[tuple[str, bool, str]]:
    """O conjunto de gates aplicável a UM run, na ordem canônica.

    `modo='historico'` audita a **rodada-42**, cujos ⑤ nasceram no schema v1 e
    por isso não têm `campanha_id` nem `repo_hash` (o B-03 é desta campanha).
    Sem esta opção o portão pintava de VERMELHO as 666 células da s42 por um
    campo que elas não podiam ter — e o gate do §1 do RUNBOOK, que manda gatear
    o corpus histórico, ficava inutilizável. O `gates_proveniencia` já tinha os
    dois modos; o portão é que não os expunha.
    """
    if alg not in CARTAO_POR_ALG:
        return [("cartao", False, f"config desconhecido do portão: {alg!r}")]
    # [DI-38a] Aborto SANCIONADO (teto de wall / cache-cap): estado ESPERADO da
    # célula, não falha do pipeline. Sob o rito BoTorch não há camadas a gatear
    # (a curva parcial vive no jsonl §17.6) — sem este guard a varredura F4
    # reprovaria por desenho exatamente as células que a DI-37.1/DI-38 sancionam.
    man = _manifesto_do_run(exp, alg, problema, semente, data_root)
    # [B-06] a classificação do motivo vem do ARTEFATO
    # `artifacts/motivos_parada.json` — nunca de literais aqui (a divergência
    # 'cache_cap' × 'cache_hit_travado' custou a DI-41.2).
    if man.get("status") == "failed" and motivo_e_sancionado(man.get("motivo_parada")):
        # ⚠ [DI-43/T11-G5] O carve-out "sem gates" era do tempo em que o teto
        # abortava SEM camadas. Agora o truncamento-com-dado GRAVA as parciais,
        # então a célula sancionada AINDA passa pelos gates de proveniência —
        # ela tem dado, e dado sem proveniência é o que a T11 existe para matar.
        prov = gates_de_proveniencia(exp, alg, problema, semente, data_root,
                                     modo=modo)
        return [("aborto-sancionado", True,
                 f"{man.get('motivo_parada')} — gates de conteúdo dispensados "
                 f"(DI-38a); fe_final={man.get('fe_final')}")] + prov
    out = list(gates_de_proveniencia(exp, alg, problema, semente, data_root,
                                     modo=modo))
    card = CARTAO_POR_ALG[alg]
    # ⚠ [conserto 2026-07-30 · achado #42] O `accept.py` NÃO expõe `--data-root`:
    # ele opera sempre sobre `data/`. Até agora o portão o chamava assim mesmo e
    # publicava o veredito como se fosse da célula pedida — PROVADO: gatear uma
    # célula INEXISTENTE num sandbox devolvia `accept=VERDE`, porque ele foi
    # olhar a célula de mesmo nome em produção.
    # Isso importa no gate **F4 do RUNBOOK**, que roda o portão sobre o corpus
    # CONSOLIDADO: 2 dos 8 gates estariam avaliando outro corpus.
    # Expor `--data-root` no accept exigiria fiar o parâmetro por dezenas de
    # `check_*` num arquivo de 2.500 linhas — refatoração às cegas num gate.
    # A escolha aqui é ADMITIR QUE NÃO SABE: fora de `data/`, o accept vira
    # NÃO-AFERÍVEL (⛔, exit 2) em vez de mentir verde.
    _fora_de_producao = os.path.abspath(
        data_root if os.path.isabs(data_root) else os.path.join(ROOT, data_root)
    ) != os.path.abspath(os.path.join(ROOT, "data"))
    if _fora_de_producao:
        out.append((f"accept[{card}]", None,
                    f"{MARCA_NAO_AFERIVEL}: accept.py não aceita --data-root e "
                    f"leria data/ em vez de {data_root!r} (achado #42)"))
    else:
        ok, det = _sub(["scripts/accept.py", card, "--alg", alg,
                        "--problema", problema, "--semente", str(semente),
                        "--exp", exp])
        out.append((f"accept[{card}]", ok, det))
    # o `auditar` ganhou `--data-root` no mesmo conserto — este já é confiável
    ok, det = _sub(["scripts/auditar.py", alg, problema, str(semente),
                    "--exp", exp, "--data-root", data_root])
    out.append(("auditar", ok, det))
    if alg in OFFLINE_ALGS:
        ok, det = _sub(["scripts/final_eval.py", "--exp", exp, "--alg", alg,
                        "--problema", problema, "--semente", str(semente),
                        "--check", "--data-root", data_root])
        out.append(("final_eval --check", ok, det))
    return out


def _runs_em_disco(data_root: str, exp_f: str | None, alg_f: str | None):
    """Enumera (exp, alg, problema, semente) dos manifestos em data/."""
    for man in sorted(glob.glob(os.path.join(
            ROOT, data_root, "experiments", "*", "*", "*.manifest.json"))):
        if "__final" in os.path.basename(man) or "_baseline_pre_retrofit" in man:
            continue
        try:
            m = json.load(open(man, encoding="utf-8"))
        except Exception:  # noqa: BLE001 — manifesto ilegível ≠ parar a varredura
            continue
        exp = m.get("exp") or os.path.basename(os.path.dirname(os.path.dirname(man)))
        alg = m.get("alg") or os.path.basename(os.path.dirname(man))
        prob, sem = m.get("problema"), m.get("semente")
        if prob is None or sem is None:
            continue
        if exp_f and exp != exp_f:
            continue
        if alg_f and alg != alg_f:
            continue
        if alg.startswith("stub") or alg not in CARTAO_POR_ALG:
            continue  # stubs/sondagens não são células do grid
        yield exp, alg, prob, sem


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exp", default=None)
    ap.add_argument("--alg", default=None)
    ap.add_argument("--problema", default=None)
    ap.add_argument("--semente", type=int, default=None)
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--varredura", action="store_true",
                    help="varre TODOS os runs em data/ (filtros --exp/--alg)")
    ap.add_argument("--historico", action="store_true",
                    help="audita a rodada-42 (⑤ v1, sem campanha_id/repo_hash) "
                         "— sem isto o portão reprova as 666 células por um "
                         "campo que elas não podiam ter")
    a = ap.parse_args(argv)

    if a.varredura:
        runs = list(_runs_em_disco(a.data_root, a.exp, a.alg))
    else:
        if not all([a.exp, a.alg, a.problema, a.semente is not None]):
            ap.error("modo 1-run exige --exp --alg --problema --semente "
                     "(ou use --varredura)")
        runs = [(a.exp, a.alg, a.problema, a.semente)]

    total_gates, vermelhos, inconclusivos, nao_afericos = 0, [], [], []
    for exp, alg, prob, sem in runs:
        res = gates_de_um_run(exp, alg, prob, sem, a.data_root,
                              modo=("historico" if a.historico else "campanha"))
        total_gates += len(res)
        if res and res[0][0] == "aborto-sancionado":
            marca = "⚪"                       # [DI-38a] sancionado ≠ verde ≠ falha
        elif any(ok is False for _, ok, _ in res):
            marca = "🔴"
        elif any(ok is None and especie_do_none(d) == "nao_aferivel"
                 for _, ok, d in res):
            marca = "⛔"                        # o gate NÃO CONSEGUIU medir
        elif any(ok is None for _, ok, _ in res):
            marca = "⚪"                        # não-aplicável POR DESENHO
        else:
            marca = "✅"
        print(f"{marca} {exp}/{alg}/{prob}/s{sem}: " + " · ".join(
            f"{nome}={'VERDE' if ok else ('INCONCL' if ok is None else 'FALHOU')}"
            for nome, ok, _ in res))
        for nome, ok, det in res:
            if ok is False:
                vermelhos.append((exp, alg, prob, sem, nome, det))
            elif ok is None and especie_do_none(det) == "nao_aferivel":
                # NÃO-AFERÍVEL: o gate DEVERIA medir e não conseguiu (parquet
                # ilegível, dependência ausente, ⑥ inexistente). Some no meio
                # dos não-aplicáveis se os dois usam a mesma marca — e é o único
                # dos dois que pede investigação.
                nao_afericos.append((exp, alg, prob, sem, nome, det))
            elif ok is None:
                # [B-07] INCONCLUSIVO **NUNCA** conta como verde. Até 2026-07-30
                # esta doutrina valia só para o emoji: `vermelhos` só recebia
                # `ok is False`, então uma célula cujo ÚNICO não-verde fosse
                # INCONCLUSIVO imprimia "VERDE" e saía 0 — e este é o portão que
                # AUTORIZA O DISPARO. Um gate que não sabe medir não atesta nada.
                inconclusivos.append((exp, alg, prob, sem, nome, det))

    if vermelhos:
        veredito = "REPROVADO"
    elif nao_afericos:
        veredito = "NÃO-AFERÍVEL (gate não conseguiu medir — investigar)"
    elif inconclusivos:
        veredito = "INCONCLUSIVO (não é verde — B-07)"
    else:
        veredito = "VERDE"
    print(f"\nPORTÃO: {len(runs)} runs · {total_gates} gates · "
          f"{len(vermelhos)} vermelho(s) · {len(nao_afericos)} não-aferível(is) · "
          f"{len(inconclusivos)} não-aplicável(is) → {veredito}")
    for exp, alg, prob, sem, nome, det in vermelhos:
        print(f"  🔴 {exp}/{alg}/{prob}/s{sem} [{nome}]: {det}")
    for exp, alg, prob, sem, nome, det in nao_afericos:
        print(f"  ⛔ {exp}/{alg}/{prob}/s{sem} [{nome}]: {det}")
    for exp, alg, prob, sem, nome, det in inconclusivos:
        print(f"  ⚪ {exp}/{alg}/{prob}/s{sem} [{nome}]: {det}")
    # 0 = verde · 1 = vermelho · 2 = inconclusivo (distintos DE PROPOSITO: quem
    # chama precisa poder tratar "reprovou" e "nao consegui medir" de formas
    # diferentes — colapsar os dois foi o que criou o falso-verde).
    # 0 = verde · 1 = vermelho · 2 = NÃO-AFERÍVEL (o gate não mediu — investigar).
    # NÃO-APLICÁVEL por desenho NÃO bloqueia: um piso sem surrogate nunca terá ③
    # para o G-1 conferir, e tratar isso como pendência tornaria o portão
    # permanentemente amarelo — o caminho conhecido para um gate ser ignorado.
    if vermelhos:
        return 1
    return 2 if nao_afericos else 0


if __name__ == "__main__":
    raise SystemExit(main())
