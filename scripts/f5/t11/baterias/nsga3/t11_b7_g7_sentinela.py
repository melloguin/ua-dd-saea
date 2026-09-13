"""T11/nsga3 — bateria 7: o G-7 (contrato_61.json) aferido POR MIM, e a CACA A SENTINELA.
Padrao c217: 'campo presente, dado sentinela'. Aqui os candidatos sao:
  n_front1 (NaN se o NDSort do piso_instrument cair no catch) · nadir_front1 (vazio) ·
  f_best/ideal (vazios) · sigma_dict declarativo · repo_hash/campanha_id.
READ-ONLY. Saida: g7_sentinela.csv
"""
import json, os, glob
import numpy as np
import pandas as pd

S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3"
SMK = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/nsga3"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga3"
DI10 = ["f_best", "n_front1"]
QUINTO = ["params", "sigma_dict", "timing", "doe_hash", "campanha_id", "repo_hash"]


def check(d, prob, rot):
    base = glob.glob(os.path.join(d, "*.manifest.json"))[0][:-len(".manifest.json")]
    man = json.load(open(base + ".manifest.json"))
    recs = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    gens = [r for r in recs if r.get("rec") == "nsga3_gen"]
    M = [r for r in recs if r.get("rec") == "header"][0]["M"]
    o = dict(fonte=rot, prob=prob, n_gen=len(gens))
    for c in DI10:
        o["di10_" + c + "_presente"] = sum(1 for g in gens if c in g)
    # SENTINELAS
    o["n_front1_nan"] = sum(1 for g in gens if g.get("n_front1") is None or
                            (isinstance(g["n_front1"], float) and np.isnan(g["n_front1"])))
    o["n_front1_zero"] = sum(1 for g in gens if g.get("n_front1") == 0)
    v = [g["n_front1"] for g in gens if isinstance(g.get("n_front1"), (int, float))
         and not (isinstance(g["n_front1"], float) and np.isnan(g["n_front1"]))]
    o["n_front1_min"] = min(v) if v else None
    o["n_front1_max"] = max(v) if v else None
    o["n_front1_unicos"] = len(set(v))
    o["nadir_f1_vazio"] = sum(1 for g in gens if not g.get("nadir_front1"))
    o["nadir_f1_len_ok"] = sum(1 for g in gens
                               if isinstance(g.get("nadir_front1"), list) and len(g["nadir_front1"]) == M)
    o["fbest_len_ok"] = sum(1 for g in gens
                            if isinstance(g.get("f_best"), list) and len(g["f_best"]) == M)
    o["fbest_todos_zero"] = sum(1 for g in gens
                                if isinstance(g.get("f_best"), list) and
                                all(x == 0 for x in g["f_best"]))
    o["tger_nan"] = sum(1 for g in gens if g.get("tempo_geracao_s") is None or
                        (isinstance(g["tempo_geracao_s"], float) and np.isnan(g["tempo_geracao_s"])))
    o["tger_zero"] = sum(1 for g in gens if g.get("tempo_geracao_s") == 0)
    # QUINTO
    for c in QUINTO:
        val = man.get(c, "<AUSENTE>")
        o["q_" + c] = ("<AUSENTE>" if val == "<AUSENTE>"
                       else ("<VAZIO>" if val in ("", {}, [], None) else "PRESENTE"))
    o["repo_hash_val"] = man.get("repo_hash", "")
    o["campanha_val"] = man.get("campanha_id", "<AUSENTE>")
    # a fracao de geracoes com pop inteiramente nao-dominada
    npop = [g["n_pop"] for g in gens]
    o["frac_F1_eq_pop"] = float(np.mean([a == b for a, b in zip(v, npop)])) if v else None
    return o


rows = [check(os.path.join(S42, p, "42"), p, "s42")
        for p in sorted(os.listdir(S42)) if os.path.isdir(os.path.join(S42, p, "42"))]
rows.append(check(SMK, "DTLZ2", "smokeT11"))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "g7_sentinela.csv"), index=False)
s = df[df.fonte == "s42"]
print("=== s42: 25 celulas, %d geracoes ===" % s.n_gen.sum())
print("  di10 f_best presente : %d/%d geracoes" % (s.di10_f_best_presente.sum(), s.n_gen.sum()))
print("  di10 n_front1 present: %d/%d geracoes" % (s.di10_n_front1_presente.sum(), s.n_gen.sum()))
print("  SENTINELA n_front1 NaN : %d · ==0 : %d" % (s.n_front1_nan.sum(), s.n_front1_zero.sum()))
print("  n_front1 faixa: %d..%d · valores distintos por celula: %s"
      % (s.n_front1_min.min(), s.n_front1_max.max(), sorted(set(s.n_front1_unicos))))
print("  nadir_front1 vazio: %d · com M componentes: %d" % (s.nadir_f1_vazio.sum(), s.nadir_f1_len_ok.sum()))
print("  f_best com M componentes: %d · todos-zero: %d" % (s.fbest_len_ok.sum(), s.fbest_todos_zero.sum()))
print("  tempo_geracao_s NaN: %d · ==0: %d" % (s.tger_nan.sum(), s.tger_zero.sum()))
print("  QUINTO obrigatorio (25 celulas):")
for c in QUINTO:
    print("    %-14s %s" % (c, dict(s["q_" + c].value_counts())))
print()
print("=== smoke T11 ===")
k = df[df.fonte == "smokeT11"].iloc[0]
print("  n_gen=%d · f_best=%d · n_front1=%d · NaN=%d · faixa %s..%s"
      % (k.n_gen, k.di10_f_best_presente, k.di10_n_front1_presente, k.n_front1_nan,
         k.n_front1_min, k.n_front1_max))
print("  QUINTO: %s" % {c: k["q_" + c] for c in QUINTO})
print("  repo_hash=%s campanha=%s" % (k.repo_hash_val, k.campanha_val))
print()
print("  |F1|==|pop| por celula (s42): M=3 %.1f%% · M=2 %.1f%%"
      % (100 * s[s.prob.isin(['DTLZ1', 'DTLZ2', 'DTLZ3', 'DTLZ4', 'DTLZ7', 'MMF16_20'])].frac_F1_eq_pop.mean(),
         100 * s[~s.prob.isin(['DTLZ1', 'DTLZ2', 'DTLZ3', 'DTLZ4', 'DTLZ7', 'MMF16_20'])].frac_F1_eq_pop.mean()))
