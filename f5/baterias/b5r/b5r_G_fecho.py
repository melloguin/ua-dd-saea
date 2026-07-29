#!/usr/bin/env python
"""F5.3b · b5r — BATERIA G: fechamento (agregados do corpus, ⑦ pelo criterio DO
GATE, footers, overshoot x prole, e o volume auditado)."""
import json
import os
import re
import sys
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0, REPO)
os.chdir(REPO)
RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5r"
OUT = os.path.join(REPO, "f5/baterias/b5r")
SEED = 42
ISX = lambda t: bool(re.fullmatch(r"x\d+", t))
ISF = lambda t: bool(re.fullmatch(r"f\d+", t))
from src import problems as PBL  # noqa: E402
from src import experiment as EXP  # noqa: E402


def main():
    rows = []
    for lab in sorted(os.listdir(RES)):
        d = os.path.join(RES, lab, str(SEED))
        if not os.path.isdir(d):
            continue
        stem = [x for x in os.listdir(d) if x.endswith(".manifest.json")
                and not x.endswith("__final.manifest.json")][0][: -len(".manifest.json")]
        prob = lab.split("_", 2)[-1] if lab.startswith("swap_") else lab
        man = json.load(open(os.path.join(d, stem + ".manifest.json")))
        L = [json.loads(x) for x in open(os.path.join(d, stem + ".jsonl"))]
        rec = pd.Series([x.get("rec") for x in L]).value_counts().to_dict()
        d7 = pd.read_parquet(os.path.join(d, stem + "__final.parquet"))
        X7 = d7[[c for c in d7.columns if ISX(c)]].values.astype(np.float32)
        F7 = d7[[c for c in d7.columns if ISF(c)]].values.astype(np.float64)
        Fchk = np.asarray(PBL.evaluate_problem(EXP._instantiate_problem(prob),
                                               X7.astype(np.float64)), dtype=np.float64)
        gate_ok = bool(np.allclose(Fchk, F7, rtol=1e-5, atol=1e-6))
        d3 = pd.read_parquet(os.path.join(d, stem + "__surrogate.parquet"))
        b3 = d3[d3.regime == "offline"]
        fm7 = json.load(open(os.path.join(d, stem + "__final.manifest.json")))
        rows.append(dict(
            label=lab, problema=prob,
            n_header=rec.get("header", 0), n_sonda=rec.get("sonda", 0),
            n_decision=rec.get("decision", 0), n_footer=rec.get("footer", 0),
            n_guard=rec.get("guard", 0), n_jsonl=len(L),
            gate7_allclose=gate_ok,
            dmax_abs=float(np.max(np.abs(Fchk - F7))),
            n3_busca=len(b3), n3_sonda=int((d3.regime == "sonda").sum()),
            n_ger_arquivadas=int(b3["geracao"].max()),
            n_ger_reais=int(b3["geracao"].max()) - 1,
            n7=len(d7), final_man=json.dumps(sorted(fm7.keys()))[:120],
            upload=man.get("upload_status"),
            motivo=man.get("motivo_parada"), status=man["status"]))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "b5r_G_fecho.csv"), index=False)
    print("celulas:", len(df))
    print("gate ⑦ allclose(rtol=1e-5,atol=1e-6):", int(df.gate7_allclose.sum()), "/", len(df),
          "| desvio abs max global: %.3e" % df.dmax_abs.max())
    print("footers:", df.n_footer.value_counts().to_dict(),
          "| headers:", df.n_header.unique().tolist(),
          "| sonda ev:", df.n_sonda.unique().tolist(),
          "| guards:", df.n_guard.unique().tolist())
    print("TOTAIS: decisoes=%d | ③busca=%d | ③sonda=%d | ⑦=%d | ger.arquivadas=%d | ger.reais=%d | jsonl=%d"
          % (df.n_decision.sum(), df.n3_busca.sum(), df.n3_sonda.sum(), df.n7.sum(),
             df.n_ger_arquivadas.sum(), df.n_ger_reais.sum(), df.n_jsonl.sum()))
    print("status:", df.status.unique().tolist(), "| motivo:", df.motivo.unique().tolist(),
          "| upload:", df.upload.unique().tolist())
    print(df[["label", "n_ger_arquivadas", "n_ger_reais", "n3_busca", "n7",
              "gate7_allclose", "dmax_abs"]].to_string(index=False))


if __name__ == "__main__":
    main()
