#!/usr/bin/env python
"""
F5.4 / moead-M16 — o teste que decide: BRACKET de float32 (D53).

Fato de aritmetica: o arredondamento f64->f32 (round-to-nearest) e MONOTONO
NAO-DECRESCENTE. Logo, para dois individuos i,j e um objetivo m:
    F32[i,m] <  F32[j,m]   =>  F64[i,m] < F64[j,m]      (ORDEM CERTA)
    F32[i,m] == F32[j,m]   =>  a ordem em F64 e DESCONHECIDA (<, = ou >)

Definicoes derivadas (sobre a ①, que e float32 por D53):
  * i domina j COM CERTEZA   <=>  F32[i,m] <  F32[j,m] para TODO m
        (entao i domina j em F64, seja qual for o valor exato)
  * i domina j POSSIVELMENTE <=>  F32[i,m] <= F32[j,m] p/ todo m e < em algum
        (= a dominancia padrao em float32)

Portanto o |frente-1| VERDADEIRO (float64, o que o MATLAB computou com NDSort
sobre pop.objs em double) esta OBRIGATORIAMENTE no intervalo
        [ n_f32 , n_certo ]
onde n_f32  = ND padrao sobre a ① float32 (o recomputo do analista)
      n_certo = ND usando so a dominancia CERTA (limite superior).

TESTE: se `n_front1` do log cai dentro de [n_f32, n_certo] em 469/469 geracoes,
entao NENHUMA divergencia exige mecanismo desconhecido — todas sao consequencia
aritmetica da D53 (① gravada em float32) e da instrumentacao do ⑥ (NDSort sobre
float64). Achado M16 = FALSO-POSITIVO.

Controle: aplicar o mesmo teste aos outros 3 pisos (nsga2/nsga3/smsemoa), que
usam o MESMO piso_instrument.m / o MESMO writer.
"""
import json, os, sys
import numpy as np
import pandas as pd

RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/moead-M16"


def nd_possivel(F):
    """ND padrao (dominancia <= em todos, < em algum) -> limite INFERIOR."""
    n = len(F)
    keep = np.ones(n, bool)
    for j in range(n):
        le = np.all(F <= F[j], axis=1)
        lt = np.any(F < F[j], axis=1)
        m = le & lt
        m[j] = False
        if m.any():
            keep[j] = False
    return keep


def nd_certo(F):
    """ND com dominancia CERTA (< em TODOS os objetivos) -> limite SUPERIOR."""
    n = len(F)
    keep = np.ones(n, bool)
    for j in range(n):
        m = np.all(F < F[j], axis=1)
        m[j] = False
        if m.any():
            keep[j] = False
    return keep


def analisa(alg, rec_name):
    raiz = os.path.join(RES, alg)
    linhas = []
    for prob in sorted(os.listdir(raiz)):
        d = os.path.join(raiz, prob, "42")
        base = f"exp_main_{alg}_{prob}_42"
        if not os.path.exists(os.path.join(d, base + "__pop.parquet")):
            continue
        pop = pd.read_parquet(os.path.join(d, base + "__pop.parquet"))
        real = pd.read_parquet(os.path.join(d, base + "__real.parquet"))
        fc = sorted([c for c in real.columns if c.startswith("f") and c[1:].isdigit()],
                    key=lambda c: int(c[1:]))
        Fmap = {int(s): real.loc[i, fc].to_numpy(np.float64)
                for i, s in zip(real.index, real["solution_id"].to_numpy())}
        recs = [json.loads(l) for l in open(os.path.join(d, base + ".jsonl"))]
        for r in recs:
            if r.get("rec") != rec_name:
                continue
            g = r["geracao"]
            sids = pop.loc[pop["geracao"] == g, "solution_id"].to_numpy()
            if len(sids) == 0:
                continue
            F = np.vstack([Fmap[int(s)] for s in sids])
            lo = int(nd_possivel(F).sum())
            hi = int(nd_certo(F).sum())
            log = int(r["n_front1"])
            # quantos pares (i,j) i!=j com algum objetivo EXATAMENTE igual em f32
            # e sids diferentes (a fonte do empate)
            n_emp = 0
            for a in range(len(F)):
                for b in range(a + 1, len(F)):
                    if sids[a] != sids[b] and np.any(F[a] == F[b]):
                        n_emp += 1
            linhas.append(dict(alg=alg, problema=prob, M=len(fc), ger=g,
                               n_pop=len(sids), log=log, lo=lo, hi=hi,
                               dentro=(lo <= log <= hi), delta=log - lo,
                               largura=hi - lo, pares_empate_f32=n_emp))
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    todos = []
    for alg, rec in [("moead", "moead_gen"), ("nsga2", "nsga2_gen"),
                     ("nsga3", "nsga3_gen"), ("smsemoa", "smsemoa_gen")]:
        try:
            df = analisa(alg, rec)
        except Exception as e:
            print(f"!! {alg}: {e}")
            continue
        todos.append(df)
        n = len(df)
        div = df[df.delta != 0]
        fora = df[~df.dentro]
        print(f"\n### {alg}: {n} geracoes | divergem do recomputo f32: {len(div)} "
              f"({100*len(div)/max(n,1):.1f}%) | FORA do bracket f32: {len(fora)}")
        if len(div):
            print(div[["problema", "M", "ger", "log", "lo", "hi", "dentro",
                       "pares_empate_f32"]].to_string(index=False))
        if len(fora):
            print("  >>> FORA DO BRACKET:")
            print(fora.to_string(index=False))
    T = pd.concat(todos, ignore_index=True)
    T.to_csv(os.path.join(OUT, "r2_bracket.csv"), index=False)
    print("\n=== GLOBAL 4 pisos:", len(T), "geracoes;",
          int((T.delta != 0).sum()), "divergencias;",
          int((~T.dentro).sum()), "fora do bracket float32")
