#!/usr/bin/env python
"""F5.3b · b5r — BATERIA F: a POPULACAO INICIAL (query-joia do B18.9/DI-28.3).

Descoberta estrutural (lida do vendorizado + confirmada pela contabilidade do FE):
`Population.__init__` chama `add(individuals)` ANTES do laco => a chave "1" do
archive e a POPULACAO INICIAL LHS (pre-selecao), e as chaves 2..n sao os
sobreviventes. Logo a ③ na geracao 1 E o desenho LHS que substituiu o dataset
como pop inicial (divergencia B18.9 do Alg. 1 L2 do paper).

F1  estratificacao de Latin hypercube: em CADA dimensao, os n pontos caem um por
    estrato de largura 1/n (permutacao exata de {0..n-1}) — assinatura do
    `pyDOE.lhs(n, samples=n)` com criterion=None
F2  a pop inicial NAO e o dataset (intersecao vazia) e respeita os bounds
F3  |pop inicial| == numero de vetores de referencia (50 M=2 / 105 M=3)

Saida: b5r_F_lhs.csv
"""
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

from src import standalone_harness as H  # noqa: E402


def main():
    rows = []
    for lab in sorted(os.listdir(RES)):
        d = os.path.join(RES, lab, str(SEED))
        if not os.path.isdir(d):
            continue
        stem = [x for x in os.listdir(d) if x.endswith(".manifest.json")
                and not x.endswith("__final.manifest.json")][0][: -len(".manifest.json")]
        prob = lab.split("_", 2)[-1] if lab.startswith("swap_") else lab
        d3 = pd.read_parquet(os.path.join(d, stem + "__surrogate.parquet"))
        b3 = d3[d3.regime == "offline"]
        xc = [x for x in b3.columns if ISX(x)]
        M = len([x for x in d3.columns if re.fullmatch(r"mu_\d+", x)])
        g1 = b3[b3["geracao"] == 1]
        X = g1[xc].values.astype(np.float64)
        n, D = X.shape
        xl, xu = H._bounds(prob)
        U = (X - xl) / (xu - xl)
        # estratificacao LHS: floor(u*n) deve ser permutacao de 0..n-1 por dimensao
        S = np.floor(np.clip(U, 0, 1 - 1e-15) * n).astype(int)
        perfeitas = sum(1 for j in range(D)
                        if np.array_equal(np.sort(S[:, j]), np.arange(n)))
        # colisoes por dimensao (quantos estratos repetidos)
        colis = [n - len(np.unique(S[:, j])) for j in range(D)]
        d1 = pd.read_parquet(os.path.join(d, stem + "__real.parquet"))
        X1 = d1[[c for c in d1.columns if ISX(c)]].values.astype(np.float32)
        inter = len(set(map(bytes, np.ascontiguousarray(X1))) &
                    set(map(bytes, np.ascontiguousarray(X.astype(np.float32)))))
        rows.append(dict(label=lab, problema=prob, M=M, D=D, n_pop1=n,
                         NRV=(50 if M == 2 else 105),
                         pop1_eq_NRV=bool(n == (50 if M == 2 else 105)),
                         dims_lhs_perfeitas=perfeitas, dims=D,
                         share_lhs=perfeitas / D, colisoes_max=int(max(colis)),
                         colisoes_tot=int(sum(colis)),
                         dentro_bounds=bool((U >= -1e-12).all() and (U <= 1 + 1e-12).all()),
                         u_min=float(U.min()), u_max=float(U.max()),
                         inter_dataset=inter))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "b5r_F_lhs.csv"), index=False)
    print(df.to_string(index=False))
    print()
    print("celulas com 100%% das dimensoes LHS-perfeitas: %d/%d" %
          ((df.share_lhs == 1).sum(), len(df)))
    print("dimensoes LHS-perfeitas: %d/%d (%.4f%%)" %
          (df.dims_lhs_perfeitas.sum(), df.dims.sum(),
           100 * df.dims_lhs_perfeitas.sum() / df.dims.sum()))
    print("intersecao pop-inicial x dataset:", int(df.inter_dataset.sum()))
    print("pop1 == NRV:", int(df.pop1_eq_NRV.sum()), "/", len(df))


if __name__ == "__main__":
    main()
