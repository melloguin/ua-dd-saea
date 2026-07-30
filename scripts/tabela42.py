#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tabela42.py — mescla, indexa e resume a rodada-42 já centralizada no Mac.

Lê  : resultados_experimentos/_maquinas/{mac,v5,v6,vm3}/experiments/**
Grava: resultados_experimentos/data/experiments/**   (layout NATIVO — serve de
                                                      --data-root p/ metrics.py,
                                                      progress.py, portao.py)
       resultados_experimentos/INDICE.csv            1 linha por célula
       resultados_experimentos/DUPLICADAS.csv        células em >1 máquina
       resultados_experimentos/TABELA_ALGORITMOS.csv
       resultados_experimentos/TABELA_ALGORITMOS.md
       resultados_experimentos/TABELA_ALGORITMOS.html

Idempotente: pode rodar quantas vezes quiser, inclusive com lote em voo.
Não escreve nada no repo e não apaga nada em _maquinas/.

    python3 tabela42.py                # usa os caminhos padrão
    python3 tabela42.py <resultados> <repo>
"""
from __future__ import annotations
import collections, csv, html, json, os, re, shutil, sys, time

HOME = os.path.expanduser("~")
BASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HOME, "Documents/python_repos/mestrado/resultados_experimentos")
REPO = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    HOME, "Documents/python_repos/mestrado/ua-dd-saea")
MAQS = ["mac", "v5", "v6", "vm3"]
SEMENTE = "42"

# ── 1. grade esperada ────────────────────────────────────────────────────────
art = os.path.join(REPO, "claude_code_context", "artifacts")
grade_todas = [r for r in csv.DictReader(open(os.path.join(art, "runs_matrix.csv"),
                                              encoding="utf-8"))
               if r["semente"] == SEMENTE]
# DI-40: c154 sai do roster do batch — 5 células não despachadas.
DI40 = [r for r in grade_todas if r["exp"] == "batch" and r["alg"] == "c154"]
grade = [r for r in grade_todas if r not in DI40]

def familia(exp):
    if exp == "main":  return "main"
    if exp == "off":   return "off"
    if exp == "batch": return "batch"
    return "sweep"

# ── 2. varre as cópias por máquina ───────────────────────────────────────────
CLASSES = [
    (r"motivo_parada.*teto_wall|WallClockAbort", "aborto por teto (projeção)"),
    (r"ModelFittingError",                       "erro numérico BoTorch (ajuste do modelo)"),
    (r"random_search_optimizer|optimal points",  "amostrador JES não convergiu"),
    (r"No module named 'google'|google-cloud-storage ausente",
                                                 "bucket indisponível no venv"),
    (r"MemoryError|Killed",                      "memória"),
    (r"FileNotFoundError",                       "artefato de entrada ausente"),
]
def classifica(m):
    st = m.get("status")
    if st in ("ok", "retried_ok"):
        return "ok", ""
    txt = "%s %s" % (m.get("motivo_parada") or "", (m.get("stack_trace") or ""))
    if str(m.get("motivo_parada") or "") == "teto_wall":
        return "abortou", "aborto por teto (projeção)"
    for pat, rot in CLASSES:
        if re.search(pat, txt):
            return ("abortou", rot) if "teto" in rot else ("FALHOU", rot)
    linhas = (m.get("stack_trace") or "").strip().splitlines()
    return "FALHOU", (linhas[-1][:90] if linhas else (st or "?"))

achados = collections.defaultdict(dict)   # (exp,alg,prob,sem) -> {maq: registro}
for maq in MAQS:
    raiz = os.path.join(BASE, "_maquinas", maq, "experiments")
    if not os.path.isdir(raiz):
        continue
    for exp in sorted(os.listdir(raiz)):
        if exp.startswith("_"):           # _baseline_pre_retrofit: nunca tocar
            continue
        dexp = os.path.join(raiz, exp)
        if not os.path.isdir(dexp): continue
        for alg in sorted(os.listdir(dexp)):
            dalg = os.path.join(dexp, alg)
            if not os.path.isdir(dalg): continue
            for fn in sorted(os.listdir(dalg)):
                if not fn.endswith(".manifest.json") or "__final" in fn:
                    continue
                base = fn[: -len(".manifest.json")]        # exp_{exp}_{alg}_{prob}_{sem}
                resto = base[len("exp_%s_%s_" % (exp, alg)):] if base.startswith(
                    "exp_%s_%s_" % (exp, alg)) else ""
                if "_" not in resto: continue
                prob, sem = resto.rsplit("_", 1)
                p = os.path.join(dalg, fn)
                try:
                    m = json.load(open(p, encoding="utf-8"))
                except Exception:
                    m = {"status": "ilegivel"}
                est, mot = classifica(m)
                achados[(exp, alg, prob, sem)][maq] = {
                    "estado": est, "motivo": mot,
                    "wall": (m.get("timing") or {}).get("tempo_total_s"),
                    "fe": m.get("fe_final"), "maxfe": m.get("maxfe"),
                    "mtime": os.path.getmtime(p), "base": base, "dir": dalg,
                }

# ── 3. mescla (precedência ok > abortou > FALHOU > mais recente) ─────────────
ORDEM = {"ok": 0, "abortou": 1, "FALHOU": 2, "ilegivel": 3}
os.makedirs(os.path.join(BASE, "data", "experiments"), exist_ok=True)
indice, duplicadas, copiados = [], [], 0
for (exp, alg, prob, sem), por_maq in sorted(achados.items()):
    esc = sorted(por_maq.items(),
                 key=lambda kv: (ORDEM.get(kv[1]["estado"], 9), -kv[1]["mtime"]))[0]
    maq, reg = esc
    if len(por_maq) > 1:
        duplicadas.append({
            "exp": exp, "alg": alg, "problema": prob, "semente": sem,
            "escolhida": maq,
            "todas": " | ".join("%s=%s" % (k, v["estado"]) for k, v in sorted(por_maq.items())),
        })
    destino = os.path.join(BASE, "data", "experiments", exp, alg)
    os.makedirs(destino, exist_ok=True)
    for fn in os.listdir(reg["dir"]):
        if not fn.startswith(reg["base"]):
            continue
        o, d = os.path.join(reg["dir"], fn), os.path.join(destino, fn)
        if os.path.exists(d):
            try:
                if os.stat(d).st_ino == os.stat(o).st_ino: continue     # já é o mesmo inode
            except OSError: pass
            if os.path.getsize(d) == os.path.getsize(o) \
               and abs(os.path.getmtime(d) - os.path.getmtime(o)) < 2:
                continue
            os.remove(d)
        try:                       # link duro: instantâneo e sem custo de disco
            os.link(o, d)
        except OSError:            # volumes diferentes → cópia
            shutil.copy2(o, d)
        copiados += 1
    camadas = sorted(f.split("__")[-1].split(".")[0]
                     for f in os.listdir(destino) if f.startswith(reg["base"] + "__"))
    indice.append({
        "algoritmo": alg, "experimento": exp, "problema": prob, "semente": sem,
        "maquina": maq, "estado": reg["estado"], "motivo": reg["motivo"],
        "wall_s": "" if reg["wall"] is None else round(float(reg["wall"])),
        "fe_final": reg["fe"], "maxfe": reg["maxfe"],
        "camadas": " ".join(camadas), "duplicada_em": len(por_maq),
    })

def grava_csv(nome, linhas, campos):
    with open(os.path.join(BASE, nome), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos); w.writeheader(); w.writerows(linhas)

grava_csv("INDICE.csv", sorted(indice, key=lambda r: (r["algoritmo"], r["experimento"],
                                                      r["problema"])),
          ["algoritmo", "experimento", "problema", "semente", "maquina", "estado",
           "motivo", "wall_s", "fe_final", "maxfe", "camadas", "duplicada_em"])
if duplicadas:
    grava_csv("DUPLICADAS.csv", duplicadas,
              ["exp", "alg", "problema", "semente", "escolhida", "todas"])

# ── 4. tabela por algoritmo × família ────────────────────────────────────────
prev = collections.defaultdict(collections.Counter)     # alg -> familia -> total
for r in grade:
    prev[r["alg"]][familia(r["exp"])] += 1
obt = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
mot = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for r in indice:
    if r["semente"] != SEMENTE: continue
    f = familia(r["experimento"])
    obt[r["algoritmo"]][f][r["estado"]] += 1
    if r["estado"] != "ok":
        mot[r["algoritmo"]][f][r["motivo"] or r["estado"]] += 1

FAMS = ["main", "off", "sweep", "batch"]
ROT = {"main": "main (25 problemas)", "off": "off (25)",
       "sweep": "sweep (6 tokens)", "batch": "batch q=10 (5)"}

def texto_motivo(alg, f, total, feitos):
    partes = ["%d %s" % (n, m) for m, n in mot[alg][f].most_common()]
    ausentes = total - sum(obt[alg][f].values())
    if ausentes > 0:
        partes.append("%d não rodou ainda" % ausentes)
    return " · ".join(partes)

linhas_tab = []
for alg in sorted(prev):
    linha = {"algoritmo": alg}
    for f in FAMS:
        total = prev[alg].get(f, 0)
        if not total:
            linha[f] = ""; linha["motivo_" + f] = ""; continue
        feitos = obt[alg][f]["ok"]
        linha[f] = "%d/%d" % (feitos, total)
        linha["motivo_" + f] = "" if feitos == total else texto_motivo(alg, f, total, feitos)
    linhas_tab.append(linha)

campos = ["algoritmo"] + sum([[f, "motivo_" + f] for f in FAMS], [])
grava_csv("TABELA_ALGORITMOS.csv", linhas_tab, campos)

# markdown
md = ["# Rodada-42 — situação por algoritmo",
      "",
      "Gerado em %s a partir de `resultados_experimentos/_maquinas/**`." %
      time.strftime("%Y-%m-%d %H:%M"),
      "Grade da semente 42: **%d células** (as %d de `c154`/`batch` estão fora pela DI-40)."
      % (len(grade), len(DI40)),
      "",
      "| algoritmo | " + " | ".join("%s | motivo" % ROT[f] for f in FAMS) + " |",
      "|---|" + "---|" * (2 * len(FAMS))]
for l in linhas_tab:
    md.append("| `%s` | " % l["algoritmo"] +
              " | ".join("%s | %s" % (l[f] or "—", l["motivo_" + f] or "") for f in FAMS) + " |")
tot_prev = len(grade)
tot_ok = sum(1 for r in indice if r["semente"] == SEMENTE and r["estado"] == "ok")
tot_ab = sum(1 for r in indice if r["semente"] == SEMENTE and r["estado"] == "abortou")
tot_fa = sum(1 for r in indice if r["semente"] == SEMENTE and r["estado"] == "FALHOU")
md += ["",
       "**Total:** %d/%d ok · %d abortos sancionados · %d falhas reais · %d ainda sem rodar."
       % (tot_ok, tot_prev, tot_ab, tot_fa, tot_prev - tot_ok - tot_ab - tot_fa)]
if duplicadas:
    md += ["", "**%d células existem em mais de uma máquina** — ver `DUPLICADAS.csv`."
           % len(duplicadas)]
open(os.path.join(BASE, "TABELA_ALGORITMOS.md"), "w", encoding="utf-8").write("\n".join(md))

# html
def esc(s): return html.escape(str(s or ""))
cel = []
for l in linhas_tab:
    tds = ["<td class=alg><code>%s</code></td>" % esc(l["algoritmo"])]
    for f in FAMS:
        v = l[f]
        cls = "vazio" if not v else ("cheio" if v.split("/")[0] == v.split("/")[1] else "parcial")
        tds.append("<td class='n %s'>%s</td>" % (cls, esc(v) or "—"))
        tds.append("<td class=mot>%s</td>" % esc(l["motivo_" + f]))
    cel.append("<tr>" + "".join(tds) + "</tr>")
HTML = """<!DOCTYPE html><html lang=pt-BR><head><meta charset=utf-8>
<title>Rodada-42 — situação por algoritmo</title><style>
:root{--s1:#fcfcfb;--s2:#f4f3f0;--ln:#e3e1dc;--tp:#0b0b0b;--ts:#52514e;--tm:#84837d;
      --ok:#0ca30c;--wr:#eda100;--bad:#d03b3b}
@media(prefers-color-scheme:dark){:root{--s1:#1a1a19;--s2:#232322;--ln:#3a3a37;
      --tp:#fff;--ts:#c3c2b7;--tm:#8f8e86}}
body{margin:0;background:var(--s1);color:var(--tp);padding:32px 26px 64px;
  font:14px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
h1{font-size:23px;font-weight:600;margin:0 0 6px}
p.sub{color:var(--ts);margin:0 0 18px;max-width:80ch}
.tiles{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 22px}
.tile{background:var(--s2);border:1px solid var(--ln);border-radius:10px;padding:12px 15px;min-width:150px}
.tile .l{color:var(--ts);font-size:12.5px}.tile .v{font-size:24px;font-weight:600;margin-top:2px;
  font-variant-numeric:tabular-nums}
table{border-collapse:collapse;width:100%;font-size:12.5px;font-variant-numeric:tabular-nums}
th{text-align:left;font-weight:600;color:var(--ts);padding:8px 9px;border-bottom:1px solid var(--ln);
  white-space:nowrap;font-size:12px}
td{padding:6px 9px;border-bottom:1px solid var(--ln);vertical-align:top}
td.alg{white-space:nowrap}td.n{text-align:right;white-space:nowrap;font-weight:600}
td.n.cheio{color:var(--ok)}td.n.parcial{color:var(--wr)}td.n.vazio{color:var(--tm);font-weight:400}
td.mot{color:var(--ts);max-width:30ch}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.nota{margin-top:26px;color:var(--ts);max-width:82ch;font-size:13px}
</style></head><body>
<h1>Rodada-42 — situação por algoritmo</h1>
<p class=sub>Uma linha por algoritmo, uma dupla de colunas por família de experimento:
quantas células fecharam <code>ok</code> sobre o total previsto no
<code>runs_matrix.csv</code> (semente 42), e o motivo de cada pendência.</p>
<div class=tiles>__TILES__</div>
<table><thead><tr><th>algoritmo</th>__CABEC__</tr></thead><tbody>__LINHAS__</tbody></table>
<div class=nota>__NOTA__</div></body></html>"""
tiles = "".join("<div class=tile><div class=l>%s</div><div class=v>%s</div></div>" % (l, v)
                for l, v in [("células previstas", tot_prev), ("ok", tot_ok),
                             ("abortos sancionados", tot_ab), ("falhas reais", tot_fa),
                             ("sem rodar", tot_prev - tot_ok - tot_ab - tot_fa)])
cabec = "".join("<th>%s</th><th>motivo</th>" % ROT[f] for f in FAMS)
nota = ("<p><b>Aborto sancionado</b> é <code>failed</code> com "
        "<code>motivo_parada=teto_wall</code>: o projetor de wall-clock cortou o run — "
        "resultado previsto pela DI-38(a)/DI-40, não defeito. <b>Falha real</b> é qualquer "
        "outro <code>failed</code>.</p>")
if duplicadas:
    nota += ("<p><b>%d células existem em mais de uma máquina</b> (configs partidos e "
             "manifestos herdados na cópia do <code>data/</code>). A escolhida segue a "
             "precedência ok &gt; aborto &gt; falha &gt; mais recente; todas as origens "
             "estão em <code>DUPLICADAS.csv</code>.</p>" % len(duplicadas))
open(os.path.join(BASE, "TABELA_ALGORITMOS.html"), "w", encoding="utf-8").write(
    HTML.replace("__TILES__", tiles).replace("__CABEC__", cabec)
        .replace("__LINHAS__", "".join(cel)).replace("__NOTA__", nota))

print("═══ MESCLA E TABELA · %s" % BASE)
print("    células indexadas: %d   ·   arquivos copiados agora: %d" % (len(indice), copiados))
print("    semente 42: %d/%d ok · %d abortos sancionados · %d falhas reais · %d sem rodar"
      % (tot_ok, tot_prev, tot_ab, tot_fa, tot_prev - tot_ok - tot_ab - tot_fa))
if duplicadas:
    print("    ⚠ %d células em >1 máquina → DUPLICADAS.csv" % len(duplicadas))
print()
print("    INDICE.csv · TABELA_ALGORITMOS.{csv,md,html}")
print("    árvore mesclada: %s/data  (use como --data-root)" % BASE)
