"""F5.4 · sobol_batch-S23 · R1 — censo INDEPENDENTE dos campos do evento de geracao.

Nao reusa nada da bateria do analista. Varre o .jsonl de TODOS os configs online
da s42 (main + batch + off) e monta o censo de chaves do evento de geracao,
separando: (a) o minimo comum DI-10 LITERAL (CONTRATO §6, 7 campos), (b) os
extras da linha "pisos (5)" (§6.1: ideal/nadir), (c) o que o helper canonico
`standalone_harness.minimo_comum_di10` PRODUZ de fato.
"""
import json, os, sys, collections
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S23"

DI10_LITERAL = ["fe", "f_best", "n_front1", "modelo_hp", "tempo_fit_s",
                "tempo_busca_s", "dist_min_arquivo"]
PISOS_EXTRA = ["ideal", "nadir_pop", "nadir_front1"]

rows = []
chaves_por_alg = {}
for alg in sorted(os.listdir(ROOT)):
    d0 = os.path.join(ROOT, alg)
    if not os.path.isdir(d0):
        continue
    for prob in sorted(os.listdir(d0)):
        d1 = os.path.join(d0, prob)
        if not os.path.isdir(d1):
            continue
        for sem in sorted(os.listdir(d1)):
            d2 = os.path.join(d1, sem)
            if not os.path.isdir(d2) or sem != "42":
                continue
            for fn in sorted(os.listdir(d2)):
                if not fn.endswith(".jsonl"):
                    continue
                exp = fn.split("_")[1]
                cnt = collections.Counter()
                keys = collections.Counter()
                n_gen = 0
                caminhos = collections.Counter()
                with open(os.path.join(d2, fn)) as fh:
                    for ln in fh:
                        ln = ln.strip()
                        if not ln:
                            continue
                        try:
                            e = json.loads(ln)
                        except Exception:
                            continue
                        r = e.get("rec", "")
                        cnt[r] += 1
                        # evento de geracao: <alg>_gen OU decision com caminho *_gen
                        is_gen = r.endswith("_gen") or (
                            r == "decision" and str(e.get("caminho", "")).endswith("_gen"))
                        if is_gen:
                            n_gen += 1
                            caminhos[str(e.get("caminho", r))] += 1
                            for k, v in e.items():
                                if v is not None:
                                    keys[k] += 1
                if n_gen == 0:
                    continue
                pres = {k: (keys[k] == n_gen) for k in DI10_LITERAL + PISOS_EXTRA}
                rows.append(dict(alg=alg, exp=exp, problema=prob, n_gen=n_gen,
                                 caminho=";".join(sorted(caminhos)),
                                 **{("has_" + k): pres[k] for k in pres},
                                 n_di10_literal=sum(pres[k] for k in DI10_LITERAL),
                                 n_pisos_extra=sum(pres[k] for k in PISOS_EXTRA),
                                 chaves=";".join(sorted(keys))))
                chaves_por_alg.setdefault(alg, set()).update(keys)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "r1_censo_campos_celula.csv"), index=False)

# agregado por alg (coerencia interna: todas as celulas do alg tem as mesmas chaves?)
g = (df.groupby(["alg", "exp"])
       .agg(n_celulas=("problema", "count"),
            n_gen_total=("n_gen", "sum"),
            caminhos=("caminho", lambda s: ";".join(sorted(set(s)))),
            **{c: (c, "all") for c in df.columns if c.startswith("has_")},
            n_di10_literal=("n_di10_literal", "min"),
            n_pisos_extra=("n_pisos_extra", "min"),
            variacao_chaves=("chaves", lambda s: len(set(s))))
       .reset_index())
g.to_csv(os.path.join(OUT, "r1_censo_campos_alg.csv"), index=False)
pd.set_option("display.width", 250, "display.max_columns", 60)
print(g.to_string(index=False))
