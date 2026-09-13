"""B28 pos-T11: o discriminador `footer_fechado` (B-01) sobre o ⑥ contaminado real."""
import sys, json, collections
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src.audit_log import footer_fechado
P="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81/q10_ZDT4/42/exp_batch_e81_ZDT4_42.jsonl"
objs=[json.loads(l) for l in open(P)]
ft=[o for o in objs if o.get("rec")=="footer"]
com=[f for f in ft if f.get("fe_final") is not None]
sem=[f for f in ft if f.get("fe_final") is None]
print("footers totais: %d | com fe_final: %d | sem fe_final (espurios): %d" % (len(ft),len(com),len(sem)))
print("\nfooter LEGITIMO (o unico com fe_final):"); print(" ", json.dumps(com[0]))
print("\n2 footers ESPURIOS (amostra):")
for f in sem[:2]: print(" ", json.dumps(f))
r=footer_fechado(P)
print("\n>>> footer_fechado(⑥ contaminado) devolve:")
print("   ", json.dumps(r))
print("   ACERTA o footer do runner?", r==com[0])
print("\n--- o que o consumidor INGENUO leria (footers[-1]) ---")
print("   ", json.dumps(ft[-1]))
hs=[o for o in objs if o.get("rec")=="header"]
leg=[h for h in hs if h.get("D") is not None]; esp=[h for h in hs if h.get("D") is None]
print("\nheaders: %d | com D/maxfe/params (legitimo): %d | com tudo NULL (espurios): %d" % (len(hs),len(leg),len(esp)))
print("ts do header legitimo :", leg[0]["ts"])
print("ts do 1o espurio      :", esp[0]["ts"])
print("ts do ultimo espurio  :", esp[-1]["ts"])
print("soma tempo_total_s dos footers espurios: %.4f s" % sum(f.get("tempo_total_s") or 0 for f in sem))
c=collections.Counter(o.get("rec") for o in objs)
print("\ninventario do ⑥:", dict(c), "| linhas:", len(objs))
print("linhas LIMPAS esperadas (1 hdr + 1 ftr + eventos):", len(objs)-2*len(esp))
