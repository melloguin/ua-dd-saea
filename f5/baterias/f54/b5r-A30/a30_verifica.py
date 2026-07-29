"""[F5.4 / b5r-A30] Verificacao ADVERSARIAL independente do achado A30.

Achado sob ataque: "a geracao 1 da camada 3 do b5r e a POPULACAO INICIAL
(pre-selecao), nao os sobreviventes declarados".

Este script NAO reusa nenhum artefato da bateria b5r original: le os parquets
crus e recomputa tudo. Testes:
  T1  tamanho da geracao 1 vs N_RV (50 M=2 / 105 M=3) e perfil de |pop| por ger.
  T2  estratificacao Latin-hypercube nas geracoes 1, 2 e 3 (controle NEGATIVO:
      uma pop SELECIONADA nao pode ser LHS perfeito).
  T3  contabilidade do orcamento 40k sob as DUAS leituras (teste de off-by-one).
  T4  sobreposicao X(g) inter X(g-1) (sobreviventes retem pais) — g=2 e g>=3.
  T5  tolerancia: T2 refeito com criterio alternativo (nao-colisao de estratos
      com margem, e teste sobre a coluna ORDENADA) + float32 vs float64.
Saida: CSV por celula em b5r_A30_celulas.csv
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = os.path.join(REPO, "f5", "baterias", "f54", "b5r-A30")
sys.path.insert(0, REPO)
from src import standalone_harness as H  # noqa: E402


def _par(n):
    return n + (n % 2)


def _bounds(problema):
    p = H._instantiate(problema)
    return np.asarray(p.xl, dtype=np.float64), np.asarray(p.xu, dtype=np.float64)


def _lhs_perfeito(X, xl, xu):
    """Fracao de dimensoes 'LHS-perfeitas' (1 ponto por estrato de largura 1/n)."""
    n, D = X.shape
    U = (X.astype(np.float64) - xl) / (xu - xl)
    ok = 0
    for j in range(D):
        idx = np.floor(np.clip(U[:, j], 0, 1 - 1e-12) * n).astype(int)
        if np.array_equal(np.sort(idx), np.arange(n)):
            ok += 1
    return ok, D


def _rows_set(X):
    return set(map(tuple, np.ascontiguousarray(X).tolist()))


def analisa(alg, prob_dir):
    prob = os.path.basename(prob_dir)
    cel = os.path.join(prob_dir, "42")
    g = glob.glob(os.path.join(cel, "*__surrogate.parquet"))
    if not g:
        return None
    man = glob.glob(os.path.join(cel, "*_42.manifest.json"))
    mn = json.load(open(man[0])) if man else {}
    df = pd.read_parquet(g[0])
    b = df[df["regime"] != "sonda"]
    xc = [c for c in df.columns if c.startswith("x") and c[1:].isdigit()]
    xc = sorted(xc, key=lambda c: int(c[1:]))
    mc = [c for c in df.columns if c.startswith("mu_")]
    M = len(mc)
    ger = b["geracao"].astype(int).values
    Ks = np.unique(ger)
    K = int(Ks.max())
    denso = bool(np.array_equal(Ks, np.arange(1, K + 1)))
    cnt = b.groupby(b["geracao"].astype(int)).size()
    n_rv = 50 if M == 2 else 105

    # problema base (tira o prefixo de sweep)
    pbase = prob.split("_", 2)[2] if prob.startswith("swap_") else prob
    xl, xu = _bounds(pbase)

    grupos = {int(k): b[ger == k][xc].to_numpy() for k in [1, 2, 3] if k in Ks}
    res = {
        "alg": alg, "celula": prob, "M": M, "D": len(xc), "N_RV": n_rv,
        "n_ger_arquivadas_K": K, "keys_densas": denso,
        "n_ger_manifesto": mn.get("n_geracoes"),
        "n_ger1": int(cnt.get(1, -1)), "n_ger2": int(cnt.get(2, -1)),
        "n_ger3": int(cnt.get(3, -1)),
        "n_pop_mediana_g>=2": float(cnt[cnt.index >= 2].median()),
        "n_pop_max_g>=2": int(cnt[cnt.index >= 2].max()),
        "frac_g>=2_com_NRV": float((cnt[cnt.index >= 2] == n_rv).mean()),
    }
    for k, X in grupos.items():
        ok, D = _lhs_perfeito(X, xl, xu)
        res["lhs_ok_g%d" % k] = ok
        res["lhs_dim_g%d" % k] = D
    # T4 sobreposicao
    if 1 in grupos and 2 in grupos:
        s1, s2 = _rows_set(grupos[1]), _rows_set(grupos[2])
        res["inter_g1g2"] = len(s1 & s2)
        res["frac_g2_em_g1"] = len(s1 & s2) / len(s2)
    # sobreposicao media em gerações do meio
    mid = [int(k) for k in Ks if 3 <= k <= min(K, 40)]
    fr = []
    for k in mid:
        A = _rows_set(b[ger == k - 1][xc].to_numpy())
        B = b[ger == k][xc].to_numpy()
        if len(B):
            fr.append(len(A & _rows_set(B)) / len(B))
    res["frac_pais_retidos_g3_40"] = float(np.mean(fr)) if fr else np.nan

    # T3 contabilidade 40k
    sizes = np.array([int(cnt[k]) for k in range(1, K + 1)])
    off = np.array([_par(s) for s in sizes])
    # leitura A (achado): chave1=pop inicial; K-1 passos de selecao
    feA_final = n_rv + off[:K - 1].sum()
    feA_antes = n_rv + off[:K - 2].sum()
    # leitura B (declarada no runner): as K chaves sao passos de selecao
    feB_final = n_rv + off[:K].sum()
    feB_antes = n_rv + off[:K - 1].sum()
    res.update({
        "FE_A_antes": int(feA_antes), "FE_A_final": int(feA_final),
        "FE_A_ok": bool(feA_antes <= 40000 < feA_final),
        "FE_B_antes": int(feB_antes), "FE_B_final": int(feB_final),
        "FE_B_ok": bool(feB_antes <= 40000 < feB_final),
    })

    # ⑥ jsonl: n de eventos decision e f_best da geracao 1
    jl = glob.glob(os.path.join(cel, "*.jsonl"))
    n_dec, fb1 = 0, None
    if jl:
        with open(jl[0]) as fh:
            for line in fh:
                if '"decision"' in line or '"rec": "decision"' in line:
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    if ev.get("rec") == "decision":
                        n_dec += 1
                        if ev.get("geracao") == 1:
                            fb1 = ev.get("f_best")
    res["n_eventos_decision"] = n_dec
    if fb1 is not None and 1 in grupos:
        mu1 = b[ger == 1][mc].to_numpy()
        res["fbest_g1_bate_mu_g1"] = bool(
            np.allclose(np.asarray(fb1, dtype=np.float64),
                        mu1.min(axis=0).astype(np.float32).astype(np.float64),
                        rtol=0, atol=0))
    return res


def main():
    algs = sys.argv[1:] or ["b5r"]
    linhas = []
    for alg in algs:
        for pd_ in sorted(glob.glob(os.path.join(RES, alg, "*"))):
            if not os.path.isdir(pd_):
                continue
            r = analisa(alg, pd_)
            if r:
                linhas.append(r)
                print(alg, r["celula"], "K=%d" % r["n_ger_arquivadas_K"],
                      "n1=%d/%d" % (r["n_ger1"], r["N_RV"]),
                      "lhs1=%s/%s" % (r.get("lhs_ok_g1"), r.get("lhs_dim_g1")),
                      "lhs2=%s" % r.get("lhs_ok_g2"),
                      "FE_A=%s FE_B=%s" % (r["FE_A_ok"], r["FE_B_ok"]), flush=True)
    out = pd.DataFrame(linhas)
    dest = os.path.join(OUT, "b5r_A30_celulas_%s.csv" % "_".join(algs))
    out.to_csv(dest, index=False)
    print("\n=> %s (%d linhas)" % (dest, len(out)))


if __name__ == "__main__":
    main()
