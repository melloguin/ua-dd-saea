#!/usr/bin/env python
"""F5.3b · treed_media — BATERIA 05: reconciliação da LINHA DO TEMPO do ⑥ contra o ④/⑤.
Prova por relógio da RECEITA do T8: dataset → _build_surrogates → SONDA (1 bloco) →
RVEA final 1000 ger → ⑦. Se a sonda fosse emitida DEPOIS da busca (ou entre gerações),
os intervalos não fechariam.
Saída: tm_timeline.csv
"""
import glob, json, os
import datetime as dt
import pandas as pd

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/treed_media"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/treed_media"


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


linhas = []
for d in sorted(glob.glob(os.path.join(RAIZ, "swap_big-*"))):
    label = os.path.basename(d)
    stem = [b for b in glob.glob(os.path.join(d, "42", "*.manifest.json")) if "__final" not in b][0]
    stem = stem[: -len(".manifest.json")]
    mf = json.load(open(stem + ".manifest.json"))
    recs = [json.loads(l) for l in open(stem + ".jsonl") if l.strip()]
    h = [r for r in recs if r["rec"] == "header"][0]
    s = [r for r in recs if r["rec"] == "sonda"][0]
    fs = [r for r in recs if r["rec"] == "footer"]
    t = mf["timing"]
    dt_hs = (ts(s["ts"]) - ts(h["ts"])).total_seconds()
    r = dict(label=label,
             dt_header_sonda_s=round(dt_hs, 4),
             fit_mais_sonda_s=round(t["tempo_fit_surrogate_s"] + t["tempo_pred_sonda_s"], 4),
             resid_fase1_s=round(dt_hs - t["tempo_fit_surrogate_s"] - t["tempo_pred_sonda_s"], 4),
             tempo_busca_s=t["tempo_busca_s"], tempo_total_s=t["tempo_total_s"])
    if fs:
        dt_sf = (ts(fs[0]["ts"]) - ts(s["ts"])).total_seconds()
        r["dt_sonda_footer_s"] = round(dt_sf, 4)
        r["resid_fase2_s"] = round(dt_sf - t["tempo_busca_s"], 4)
        r["dt_header_footer_s"] = round((ts(fs[0]["ts"]) - ts(h["ts"])).total_seconds(), 4)
        r["resid_total_s"] = round(r["dt_header_footer_s"] - t["tempo_total_s"], 4)
        r["sonda_antes_da_busca"] = bool(dt_sf > 0.5 * t["tempo_busca_s"])
    else:
        r["dt_sonda_footer_s"] = None; r["resid_fase2_s"] = None
        r["dt_header_footer_s"] = None; r["resid_total_s"] = None
        r["sonda_antes_da_busca"] = None
    r["ordem_eventos"] = ">".join(x["rec"] for x in recs)
    linhas.append(r)

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(OUT, "tm_timeline.csv"), index=False)
print(df.to_string())
