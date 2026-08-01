# -*- coding: utf-8 -*-
"""progress.py — o PAINEL da execução (M7, incremento 3/4 do autor).

READ-ONLY. Lê os `.jsonl` (streaming, §17.5) e os manifestos (§17.2) e mostra:

  (a) **runs ATIVOS** — barra tipo tqdm por run em andamento (FE consumido / maxFE,
      geração corrente, wall decorrido, ETA linear, e o último evento do algoritmo);
  (b) **a TABELA DE EXECUÇÕES** — o grid × o que já rodou (o "registro de execuções"
      que o autor pediu): status, wall, nº de retries, por (exp, alg, problema, semente);
  (c) o **placar** (ok / retried_ok / failed / pendente) contra o `runs_matrix.csv`.

Um run é "ativo" quando o `.jsonl` tem header mas ainda não tem footer FECHADO (o
footer com `fe_final` é o sinal canônico de término — lição das sessões MATLAB: NÃO
monitorar pelo processo, que sobrevive ao fim do run por causa dos MathWorksServiceHost).
⚠ [BL-21] "footer fechado" é `src.audit_log.footer_fechado`, não "o último footer":
o append cego (B-01) empilha pares header/footer VAZIOS, e ler o último faz o painel
mentir sobre o estado da célula DURANTE a campanha — que é justamente quando alguém
está olhando para ele.

Uso:
    python3 scripts/progress.py                 # snapshot
    python3 scripts/progress.py --watch         # atualiza a cada 5s
    python3 scripts/progress.py --tabela        # só a tabela de execuções
    python3 scripts/progress.py --exp main --alg c262
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.audit_log import footer_fechado          # noqa: E402  [BL-21]

DATA = os.path.join(ROOT, "data", "experiments")
GRID = os.path.join(ROOT, "claude_code_context", "artifacts", "runs_matrix.csv")


# ── leitura barata (nunca carrega o jsonl inteiro) ───────────────────────────

def _tail_json(path: str, n: int = 400) -> list[dict]:
    """Últimas `n` linhas parseáveis do jsonl (lê só o fim do arquivo)."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            fh.seek(max(0, size - 256 * 1024))          # 256 KB de cauda bastam
            blob = fh.read().decode("utf-8", "ignore")
        out = []
        for ln in blob.splitlines()[-n:]:
            ln = ln.strip()
            if ln.startswith("{"):
                try:
                    out.append(json.loads(ln))
                except Exception:                        # noqa: BLE001
                    pass
        return out
    except OSError:
        return []


def _head_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln.startswith("{"):
                    return json.loads(ln)
    except Exception:                                    # noqa: BLE001
        return None
    return None


def _scan(exp_f=None, alg_f=None) -> list[dict]:
    """Varre `data/experiments/**` e resume cada run pelo jsonl + manifesto."""
    runs = []
    if not os.path.isdir(DATA):
        return runs
    for exp in sorted(os.listdir(DATA)):
        if exp.startswith("_") or (exp_f and exp != exp_f):
            continue
        d_exp = os.path.join(DATA, exp)
        if not os.path.isdir(d_exp):
            continue
        for alg in sorted(os.listdir(d_exp)):
            if alg_f and alg != alg_f:
                continue
            d_alg = os.path.join(d_exp, alg)
            if not os.path.isdir(d_alg):
                continue
            for fn in sorted(os.listdir(d_alg)):
                if not fn.endswith(".jsonl"):
                    continue
                p = os.path.join(d_alg, fn)
                head = _head_json(p) or {}
                tail = _tail_json(p)
                # [BL-21] a primitiva, NÃO o último footer da cauda: numa célula
                # com pares espúrios (append cego, B-01) o último footer é um dos
                # vazios e o painel MENTE o run inteiro. Medido em
                # `batch/e81/ZDT4_42`: 95 footers, 1 só com `fe_final` — o último
                # dá `fe_final=None`, a primitiva dá 2109/200 gerações.
                foot = footer_fechado(p)
                gens = [r for r in tail if str(r.get("rec", "")).endswith("_gen")
                        or str(r.get("rec", "")) in ("c262_iter", "c154_iter")]
                last = gens[-1] if gens else None
                base = fn[:-6]
                man_p = os.path.join(d_alg, base + ".manifest.json")
                man = {}
                if os.path.exists(man_p):
                    try:
                        man = json.load(open(man_p, encoding="utf-8"))
                    except Exception:                    # noqa: BLE001
                        man = {}
                runs.append({
                    "exp": exp, "alg": alg, "arquivo": base,
                    "problema": head.get("problema") or man.get("problema"),
                    "semente": head.get("semente", man.get("semente")),
                    "maxfe": head.get("maxfe") or man.get("maxfe"),
                    "fe": (foot or {}).get("fe_final") or (last or {}).get("fe"),
                    "geracao": (last or {}).get("geracao") or (last or {}).get("iter"),
                    "status": (foot or {}).get("status") or man.get("status"),
                    "ativo": (head and not foot),
                    "mtime": os.path.getmtime(p),
                    "wall": (man.get("timing") or {}).get("tempo_total_s"),
                    "retries": man.get("n_retries"),
                })
    return runs


# ── render ──────────────────────────────────────────────────────────────────

def _barra(frac: float, largura: int = 28) -> str:
    frac = 0.0 if frac is None else max(0.0, min(1.0, frac))
    cheio = int(round(frac * largura))
    return "█" * cheio + "░" * (largura - cheio)


def _hms(s) -> str:
    if s is None:
        return "—"
    s = int(s)
    return f"{s//3600}h{(s%3600)//60:02d}m" if s >= 3600 else f"{s//60}m{s%60:02d}s"


def painel(runs: list[dict]) -> None:
    ativos = [r for r in runs if r["ativo"]]
    print(f"\n\033[1m▶ RUNS ATIVOS ({len(ativos)})\033[0m"
          f"   ·   {time.strftime('%H:%M:%S')}")
    if not ativos:
        print("  (nenhum run em andamento — nenhum .jsonl com header e sem footer)")
    for r in sorted(ativos, key=lambda x: -x["mtime"]):
        fe, mx = r["fe"], r["maxfe"]
        frac = (fe / mx) if (fe and mx) else None
        idade = time.time() - r["mtime"]
        eta = ""
        if frac and 0 < frac < 1:
            # ETA linear a partir do 1º evento do jsonl (aproximação honesta)
            eta = f" · ETA ~{_hms((idade / frac) - idade)}" if idade > 0 else ""
        vivo = "🟢" if idade < 120 else "🟡" if idade < 900 else "🔴"
        pct = f"{100*frac:5.1f}%" if frac is not None else "  ?  "
        print(f"  {vivo} {r['alg']:9} {str(r['problema']):9} s{r['semente']!s:<3} "
              f"[{_barra(frac)}] {pct}  FE {fe or '?'}/{mx or '?'}"
              f"  ger {r['geracao'] or '?'}{eta}"
              f"  · últ. evento há {_hms(idade)}")


def tabela(runs: list[dict], limite: int = 30) -> None:
    print(f"\n\033[1m▶ TABELA DE EXECUÇÕES\033[0m (concluídos, mais recentes primeiro)")
    print(f"  {'exp':5} {'alg':9} {'problema':9} {'sem':>4} {'status':11} "
          f"{'wall':>8} {'retries':>7}  FE")
    fin = [r for r in runs if not r["ativo"]]
    for r in sorted(fin, key=lambda x: -x["mtime"])[:limite]:
        st = r["status"] or "?"
        cor = "\033[32m" if st in ("ok", "retried_ok") else "\033[31m" if st == "failed" else ""
        print(f"  {r['exp']:5} {r['alg']:9} {str(r['problema']):9} {r['semente']!s:>4} "
              f"{cor}{st:11}\033[0m {_hms(r['wall']):>8} {str(r['retries'] or 0):>7}"
              f"  {r['fe'] or '?'}/{r['maxfe'] or '?'}")
    if len(fin) > limite:
        print(f"  … +{len(fin)-limite} runs (use --tabela para a lista inteira)")


def placar(runs: list[dict]) -> None:
    c = Counter((r["status"] or "sem-status") for r in runs if not r["ativo"])
    total_grid = None
    if os.path.exists(GRID):
        try:
            import csv
            total_grid = sum(1 for _ in csv.DictReader(open(GRID, encoding="utf-8")))
        except Exception:                                # noqa: BLE001
            pass
    linha = " · ".join(f"{k}={v}" for k, v in sorted(c.items()))
    print(f"\n\033[1m▶ PLACAR\033[0m  {linha or '(vazio)'}"
          + (f"   ·   grid completo = {total_grid} runs" if total_grid else ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true", help="atualiza a cada 5s")
    ap.add_argument("--tabela", action="store_true", help="só a tabela (lista inteira)")
    ap.add_argument("--exp"), ap.add_argument("--alg")
    a = ap.parse_args()
    while True:
        runs = _scan(a.exp, a.alg)
        if a.watch:
            os.system("clear" if os.name != "nt" else "cls")
        if a.tabela:
            tabela(runs, limite=10**6)
        else:
            painel(runs)
            tabela(runs)
        placar(runs)
        if not a.watch:
            return
        time.sleep(5)


if __name__ == "__main__":
    main()
