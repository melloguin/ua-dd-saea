"""O SMOKE T11 do b5m (off/MMF1/s0) — a instrumentacao NOVA funciona de fato?
Reconcilia `n_substituicoes` (⑥) contra as substituicoes reconstruidas da ③.
"""
import json, numpy as np, pandas as pd, pyarrow.parquet as pq
B = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/off/b5m/exp_off_b5m_MMF1_0"
recs = [json.loads(l) for l in open(B + ".jsonl")]
dec = {r["geracao"]: r for r in recs if r["rec"] == "decision"}
sg = pq.read_table(B + "__surrogate.parquet").to_pandas()
print("③ regimes:", sg.regime.value_counts().to_dict())
busca = sg[sg.regime == "offline"]
xs = [c for c in sg.columns if c.startswith("x")]
mus = [c for c in sg.columns if c.startswith("mu_")]
G = {int(k): np.ascontiguousarray(v[xs].values) for k, v in busca.groupby("geracao")}
ks = sorted(G); pop = G[ks[0]].shape[0]
print("pop=%d  n_ger=%d  linhas busca=%d" % (pop, len(ks), len(busca)))

rows = []
for a, b in zip(ks, ks[1:]):
    A, Bm = G[a], G[b]
    mudou = int(sum(1 for i in range(pop) if bytes(A[i]) != bytes(Bm[i])))   # por POSICAO
    sa = set(map(bytes, A))
    novos = int(sum(1 for r in Bm if bytes(r) not in sa))                     # por CONJUNTO
    d = dec[b]; pw = d["p_wrong_stats"] or {}
    rows.append(dict(ger=b, n_sub=d["n_substituicoes"], slots_mudou=mudou, novos=novos,
                     p_min=pw.get("min"), p_med=pw.get("med"), p_max=pw.get("max"),
                     n_chamadas=pw.get("n_chamadas"), n_nan=pw.get("n_nan"),
                     flag=d["flag_vetores_degenerados"]))
df = pd.DataFrame(rows)
df.to_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b5m/t11_b5m_smoke.csv", index=False)

print("\n--- RECONCILIACAO ⑥ n_substituicoes  x  ③ ---")
print("n_chamadas == pop em            :", int((df.n_chamadas == pop).sum()), "/", len(df))
print("n_sub >= slots_mudou em         :", int((df.n_sub >= df.slots_mudou).sum()), "/", len(df))
print("n_sub == 0  <=>  slots_mudou==0 :",
      int(((df.n_sub == 0) == (df.slots_mudou == 0)).sum()), "/", len(df),
      " (zeros: n_sub=%d, slots=%d)" % (int((df.n_sub == 0).sum()), int((df.slots_mudou == 0).sum())))
print("corr(n_sub, slots_mudou) Pearson:", round(float(df.n_sub.corr(df.slots_mudou)), 6),
      " Spearman:", round(float(df.n_sub.corr(df.slots_mudou, method="spearman")), 6))
print("razao n_sub/slots_mudou mediana :", round(float((df.n_sub / df.slots_mudou.replace(0, np.nan)).median()), 4))
print("soma n_sub=%d  soma slots_mudou=%d  soma novos=%d" %
      (df.n_sub.sum(), df.slots_mudou.sum(), df.novos.sum()))
print("\n--- TESTE FALSIFICAVEL: max(P_wrong) <= 0,5  =>  n_sub == 0 ---")
sub = df[df.p_max <= 0.5]
print("gerações com p_max<=0,5:", len(sub), " dessas com n_sub==0:", int((sub.n_sub == 0).sum()))
sub2 = df[df.p_max > 0.5]
print("gerações com p_max> 0,5:", len(sub2), " dessas com n_sub>=1:", int((sub2.n_sub >= 1).sum()))
print("\n--- RAMPA θ: P_wrong cai com a geracao (A15 agora DIRETA) ---")
print("spearman(p_med, ger) =", round(float(df.p_med.corr(df.ger, method="spearman")), 4))
print("spearman(n_sub, ger) =", round(float(df.n_sub.corr(df.ger, method="spearman")), 4))
q = df.groupby(pd.qcut(df.ger, 4, labels=["Q1", "Q2", "Q3", "Q4"]), observed=True)[
    ["p_min", "p_med", "p_max", "n_sub", "slots_mudou"]].median()
print(q.to_string())
print("\n--- flag_vetores_degenerados ---")
print("nao-nulo em:", int(df.flag.notna().sum()), "/", len(df))
print("\n--- p_wrong_stats: dominio ---")
print("min global=%.6g  max global=%.6g  n_nan total=%d" % (df.p_min.min(), df.p_max.max(), df.n_nan.sum()))
print("gerações com p_max == 1,0 exato :", int((df.p_max == 1.0).sum()))
print("gerações com p_min == 0,0 exato :", int((df.p_min == 0.0).sum()))
