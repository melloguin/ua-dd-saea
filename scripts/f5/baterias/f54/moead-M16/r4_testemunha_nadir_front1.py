#!/usr/bin/env python
"""
F5.4 / moead-M16 — TESTEMUNHA INDEPENDENTE: o campo `nadir_front1` do ⑥.

`piso_instrument.m:46` grava  nadir_front1 = max(PopObj(fno==1,:),[],1)  em
FLOAT64 — i.e. o max componentwise da frente-1 QUE O MATLAB VIU. Ele identifica,
individuo a individuo, o conjunto que o NDSort usou, sem depender de nenhuma
hipotese minha.

Controle POSITIVO: nas 439 geracoes que batem, float32(nadir_front1_log) tem de
ser identico ao max da MINHA frente-1 (o instrumento e valido).
Teste: nas 30 que divergem, ele aponta o individuo que a ① float32 perdeu.

Tambem mede, para cada geracao divergente, a FOLGA RELATIVA na coordenada que
DECIDE a dominancia (a que empata) — que e o numero que o analista deveria ter
olhado; o `min_rel_gap` dele mede outra coisa.
"""
import json, os
import numpy as np
import pandas as pd

RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/moead-M16"


def nd_possivel(F):
    n = len(F); keep = np.ones(n, bool)
    for j in range(n):
        m = np.all(F <= F[j], axis=1) & np.any(F < F[j], axis=1); m[j] = False
        if m.any(): keep[j] = False
    return keep


def nd_certo(F):
    n = len(F); keep = np.ones(n, bool)
    for j in range(n):
        m = np.all(F < F[j], axis=1); m[j] = False
        if m.any(): keep[j] = False
    return keep


rows, ctrl_ok, ctrl_n = [], 0, 0
for prob in sorted(os.listdir(RES)):
    d = os.path.join(RES, prob, "42"); base = f"exp_main_moead_{prob}_42"
    pop = pd.read_parquet(os.path.join(d, base + "__pop.parquet"))
    real = pd.read_parquet(os.path.join(d, base + "__real.parquet"))
    fc = sorted([c for c in real.columns if c.startswith("f") and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    Fmap = {int(s): real.loc[i, fc].to_numpy(np.float64)
            for i, s in zip(real.index, real["solution_id"].to_numpy())}
    recs = [json.loads(l) for l in open(os.path.join(d, base + ".jsonl"))]
    for r in [x for x in recs if x.get("rec") == "moead_gen"]:
        g = r["geracao"]
        sids = pop.loc[pop["geracao"] == g, "solution_id"].to_numpy()
        F = np.vstack([Fmap[int(s)] for s in sids])
        keep = nd_possivel(F); certo = nd_certo(F)
        lo, hi, log = int(keep.sum()), int(certo.sum()), int(r["n_front1"])
        nf1_log32 = np.asarray(r["nadir_front1"], np.float64).astype(np.float32).astype(np.float64)
        nf1_meu = F[keep].max(0)
        bate_nadir = bool(np.array_equal(nf1_log32, nf1_meu))
        ctrl_n += 1; ctrl_ok += int(bate_nadir and lo == log)
        if lo == log:
            continue
        # quem sao os individuos "tie-dependentes": dominados em f32, mas cuja
        # dominancia depende de um EMPATE EXATO de coordenada
        extras = []
        for j in np.where(~keep)[0]:
            if certo[j]:                      # nao ha dominador estrito em todas
                doms = np.where(np.all(F <= F[j], 1) & np.any(F < F[j], 1))[0]
                doms = [i for i in doms if i != j]
                for i in doms:
                    tied = np.where(F[i] == F[j])[0]
                    if len(tied):
                        extras.append((int(sids[j]), int(sids[i]), tied.tolist()))
                        break
        # o nadir_front1 do log aponta um individuo fora da MINHA frente-1?
        aponta = []
        for k in np.where(~keep)[0]:
            if np.any(F[k] > nf1_meu) and np.all(F[k] <= nf1_log32):
                aponta.append(int(sids[k]))
        # colisao de LINHA inteira (o caso delta<0)
        grp = {}
        for i, s in enumerate(sids):
            grp.setdefault(tuple(F[i].tolist()), set()).add(int(s))
        colis = [sorted(v) for v in grp.values() if len(v) > 1]
        rows.append(dict(problema=prob, ger=g, log=log, f32=lo, certo=hi,
                         delta=log - lo, bracket=(lo <= log <= hi),
                         nadir_f1_bate_f32=bate_nadir,
                         nadir_aponta_sids=aponta,
                         tie_dependentes=[e[0] for e in extras],
                         dominador_e_coord=[(e[1], e[2]) for e in extras],
                         colisao_linha_f32=colis))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "r4_testemunha.csv"), index=False)
pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 60)
print(f"CONTROLE POSITIVO: nas geracoes em que log==recomputo f32, "
      f"float32(nadir_front1_log) == max(minha frente-1) em {ctrl_ok}/{469 - len(df)}")
print()
print(df[["problema", "ger", "log", "f32", "certo", "delta", "bracket",
          "nadir_f1_bate_f32", "nadir_aponta_sids", "tie_dependentes",
          "colisao_linha_f32"]].to_string(index=False))
