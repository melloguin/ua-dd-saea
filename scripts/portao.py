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

#: alg → cartão do accept. R3 = branches dedicados; R1/R2 = rótulo informativo
#: (o catch-all F0-01 roteia pelo `--alg`, não pelo nome do cartão).
CARTAO_POR_ALG = {
    "c122": "R3-c122", "c149": "R3-c149", "e81": "R3-e81",
    "b5r": "R3-b5", "b5m": "R3-b5",
    "c311": "R3-c311", "moead_media": "R3-piso-off",
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
    return r.returncode == 0, (linhas[-1][:110] if linhas else "")


def gates_de_um_run(exp: str, alg: str, problema: str, semente,
                    data_root: str = "data") -> list[tuple[str, bool, str]]:
    """O conjunto de gates aplicável a UM run, na ordem canônica."""
    if alg not in CARTAO_POR_ALG:
        return [("cartao", False, f"config desconhecido do portão: {alg!r}")]
    out = []
    card = CARTAO_POR_ALG[alg]
    # (accept.py não expõe --data-root: opera sempre sobre data/ — o
    #  passthrough de data_root do portão vale p/ o final_eval)
    ok, det = _sub(["scripts/accept.py", card, "--alg", alg,
                    "--problema", problema, "--semente", str(semente),
                    "--exp", exp])
    out.append((f"accept[{card}]", ok, det))
    ok, det = _sub(["scripts/auditar.py", alg, problema, str(semente),
                    "--exp", exp])
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
    a = ap.parse_args(argv)

    if a.varredura:
        runs = list(_runs_em_disco(a.data_root, a.exp, a.alg))
    else:
        if not all([a.exp, a.alg, a.problema, a.semente is not None]):
            ap.error("modo 1-run exige --exp --alg --problema --semente "
                     "(ou use --varredura)")
        runs = [(a.exp, a.alg, a.problema, a.semente)]

    total_gates, vermelhos = 0, []
    for exp, alg, prob, sem in runs:
        res = gates_de_um_run(exp, alg, prob, sem, a.data_root)
        total_gates += len(res)
        marca = "✅" if all(ok for _, ok, _ in res) else "🔴"
        print(f"{marca} {exp}/{alg}/{prob}/s{sem}: " + " · ".join(
            f"{nome}={'VERDE' if ok else 'FALHOU'}" for nome, ok, _ in res))
        for nome, ok, det in res:
            if not ok:
                vermelhos.append((exp, alg, prob, sem, nome, det))

    print(f"\nPORTÃO: {len(runs)} runs · {total_gates} gates · "
          f"{len(vermelhos)} vermelho(s) → "
          f"{'VERDE' if not vermelhos else 'REPROVADO'}")
    for exp, alg, prob, sem, nome, det in vermelhos:
        print(f"  🔴 {exp}/{alg}/{prob}/s{sem} [{nome}]: {det}")
    return 0 if not vermelhos else 1


if __name__ == "__main__":
    raise SystemExit(main())
