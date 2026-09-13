"""T11 · sobol_batch · BATERIA 2 — as CORRECOES da campanha, medidas.

Fonte: /Users/gmello/.../evidencia_T11/smoke_python/experiments/batch/sobol_batch
(o smoke POS-T11 que o LEIA-ME e o handoff §15.2 dizem NAO existir — existe).
Cruza com a s42 (PRE-T11) da mesma celula (ZDT4, semente 42).
"""
import json, os, sys, warnings
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
SMK = ("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/"
       "smoke_python/experiments/batch/sobol_batch/exp_batch_sobol_batch_ZDT4_42")
S42 = ("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/"
       "sobol_batch/q10_ZDT4/42/exp_batch_sobol_batch_ZDT4_42")
OUT = os.path.join(REPO, "f5/t11/baterias/sobol_batch")
sys.path.insert(0, REPO)
os.chdir(REPO)
from src import standalone_harness as H          # noqa: E402
from src import problems as _problems            # noqa: E402
from scipy.stats import qmc                      # noqa: E402

man = json.load(open(SMK + ".manifest.json"))
L = [json.loads(l) for l in open(SMK + ".jsonl")]
real = pd.read_parquet(SMK + "__real.parquet")
tim = pd.read_parquet(SMK + "__timing.parquet")
dec = [x for x in L if x.get("rec") == "decision"]
xc = [c for c in real.columns if c.startswith("x") and c[1:].isdigit()]
fc = [c for c in real.columns if c.startswith("f") and c[1:].isdigit()]
D = len(xc); n_init = 11 * D - 1
res = {}

print("=" * 78)
print("I-03 · n_front1 pelo minimo_comum_di10 — PRESENTE **E CORRETO**?")
print("=" * 78)
res["n_eventos"] = len(dec)
res["n_front1_presente"] = sum(1 for e in dec if "n_front1" in e)
F = real[fc].values.astype(np.float64)
ok_nf = ok_fb = 0; dmax_fb = 0.0
lin = []
for e in dec:
    fe = int(e["fe"])
    Fa = F[:fe]
    idx = _problems._nds_filter(Fa)
    nf_exp = int(len(idx))
    ok_nf += int(int(e["n_front1"]) == nf_exp)
    fb_exp = Fa.min(axis=0)
    d = float(np.abs(np.asarray(e["f_best"], dtype=np.float64) - fb_exp).max())
    dmax_fb = max(dmax_fb, d); ok_fb += int(d <= 1e-5)
    lin.append({"geracao": e["geracao"], "fe": fe, "n_front1_log": e["n_front1"],
                "n_front1_recomp": nf_exp, "dmax_f_best": d,
                "seed_sobol": e["seed_sobol"],
                "tempo_busca_s": e.get("tempo_busca_s")})
res["n_front1_correto"] = ok_nf
res["f_best_correto_1e5"] = ok_fb
res["f_best_dmax"] = dmax_fb
nfs = [int(e["n_front1"]) for e in dec]
res["n_front1_min"] = min(nfs); res["n_front1_max"] = max(nfs)
res["n_front1_distintos"] = len(set(nfs))
res["n_front1_sentinela(-1/0)"] = sum(1 for v in nfs if v in (-1, 0))
res["n_front1_constante"] = len(set(nfs)) == 1
print({k: res[k] for k in list(res)})
pd.DataFrame(lin).to_csv(f"{OUT}/b2_smoke_eventos.csv", index=False)

print()
print("=" * 78)
print("I-02 · tempo_aval_real_s — nao-nulo? cobre o DoE?")
print("=" * 78)
t = man["timing"]
res["timing"] = t
proxy = float((tim["tempo_geracao_s"] - tim["tempo_busca_s"]).sum())
res["proxy_aval_4(sem DoE)"] = proxy
res["tempo_aval_real_s"] = t["tempo_aval_real_s"]
res["razao_aval/proxy"] = t["tempo_aval_real_s"] / proxy if proxy else None
res["n_avals"] = len(real)
res["frac_wall"] = t["tempo_aval_real_s"] / t["tempo_total_s"]
print({k: res[k] for k in ["timing", "proxy_aval_4(sem DoE)",
                           "tempo_aval_real_s", "razao_aval/proxy",
                           "n_avals", "frac_wall"]})

print()
print("=" * 78)
print("I-07 · params no ⑤ + campanha_id/repo_hash/schema v2")
print("=" * 78)
p = man["params"]
res["params_chaves"] = sorted(p)
res["params_q"] = p["q"]; res["manifest_q"] = man["q"]
res["params_maxfe"] = p["maxfe"]; res["manifest_maxfe"] = man["maxfe"]
res["params_D"] = p["D"]; res["params_M"] = p["M"]
res["params_nota_potencia"] = p["nota_potencia_de_2"][:70]
res["campanha_id"] = man.get("campanha_id")
res["repo_hash"] = man.get("repo_hash")
res["schema_version"] = man.get("schema_version")
res["ckpt_recs"] = sum(1 for x in L if x.get("rec") == "checkpoint")
res["sigma_dict_chaves"] = sorted(man["sigma_dict"])
res["sonda_bloco"] = man["sonda"]
print({k: res[k] for k in ["params_chaves", "params_q", "manifest_q",
                           "params_maxfe", "manifest_maxfe",
                           "params_nota_potencia", "campanha_id", "repo_hash",
                           "schema_version", "ckpt_recs"]})

print()
print("=" * 78)
print("PONTE PRE×POS-T11 — o OPERADOR mudou? (seeds e pontos)")
print("=" * 78)
man42 = json.load(open(S42 + ".manifest.json"))
L42 = [json.loads(l) for l in open(S42 + ".jsonl")]
d42 = [x for x in L42 if x.get("rec") == "decision"]
r42 = pd.read_parquet(S42 + "__real.parquet")
X42 = r42[xc].values[n_init:].astype(np.float64)      # 2000 pontos (q=10)
Xsm = real[xc].values[n_init:].astype(np.float64)     # 200 pontos (q=1)
s42_seeds = [int(e["seed_sobol"]) for e in d42]
smk_seeds = [int(e["seed_sobol"]) for e in dec]
res["seeds_iguais_200"] = int(sum(int(a == b) for a, b in
                                  zip(s42_seeds, smk_seeds)))
# q=1 tira o 1o ponto do MESMO motor que q=10 tira 10 ⇒ deve ser bit-igual
prim42 = X42[::10]
res["pontos_bit_iguais_f32"] = int((prim42.astype(np.float32) ==
                                    Xsm.astype(np.float32)).all(axis=1).sum())
res["pontos_dmax_f64"] = float(np.abs(prim42 - Xsm).max())
res["doe_hash_igual"] = man["doe_hash"] == man42["doe_hash"]
res["doe_bit_igual"] = bool(np.array_equal(
    r42[xc].values[:n_init].astype(np.float32),
    real[xc].values[:n_init].astype(np.float32)))
res["algo_version_42"] = man42["algo_version"]
res["algo_version_smk"] = man["algo_version"]
print({k: res[k] for k in ["seeds_iguais_200", "pontos_bit_iguais_f32",
                           "pontos_dmax_f64", "doe_hash_igual",
                           "doe_bit_igual", "algo_version_42",
                           "algo_version_smk"]})

print()
print("=" * 78)
print("O QUE AINDA NAO ESTA LA (campos do §6.1 linha 'pisos')")
print("=" * 78)
ev = dec[0]
for campo in ["ideal", "nadir_pop", "nadir_front1", "dist_min_arquivo",
              "modelo_hp", "tempo_fit_s", "n_front1", "f_best",
              "tempo_busca_s"]:
    res[f"campo_{campo}"] = campo in ev
    print(f"  {campo:20s} {'PRESENTE' if campo in ev else 'ausente'}")
res["chaves_evento"] = sorted(ev)
res["params_geracoes_derivadas"] = "geracoes_derivadas" in p

json.dump(res, open(f"{OUT}/b2_resumo.json", "w"), ensure_ascii=False,
          indent=1, default=str)
print("\nOK →", f"{OUT}/b2_resumo.json")
