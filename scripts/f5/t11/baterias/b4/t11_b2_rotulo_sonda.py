"""T11/b4 — bateria 2: aplica a REGRA_DO_ROTULO declarada no sigma_dict e mede
AUC / acuracia / precision / recall / F1 REAIS, SEPARADAMENTE na regua Sobol
(regime='sonda') e no bloco estratificado (regime='sonda_estratificada').
Regra 12 do CONTRATO: os dois NUNCA entram na mesma analise.
READ-ONLY. Corpus: smoke T11 (main/b4/MMF1) — a unica celula com o bloco novo.
"""
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

SM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4'
ART = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4'


def mmf1(X):
    x1, x2 = X[:, 0].astype(float), X[:, 1].astype(float)
    f1 = np.abs(x1 - 2.0)
    f2 = 1.0 - np.sqrt(f1) + 2.0 * (x2 - np.sin(6.0 * np.pi * np.abs(x1 - 2.0) + np.pi)) ** 2
    return np.column_stack([f1, f2])


def auc_mw(y, s):
    """AUC por Mann-Whitney com correcao de empates."""
    y = np.asarray(y).astype(int); s = np.asarray(s, dtype=float)
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = pd.Series(s).rank().values
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)


def metrics(y, pred, score):
    y = np.asarray(y).astype(int); pred = np.asarray(pred).astype(int)
    tp = int(((y == 1) & (pred == 1)).sum()); fp = int(((y == 0) & (pred == 1)).sum())
    fn = int(((y == 1) & (pred == 0)).sum()); tn = int(((y == 0) & (pred == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else np.nan
    rec = tp / (tp + fn) if tp + fn else np.nan
    f1 = 2 * prec * rec / (prec + rec) if (prec and rec and not np.isnan(prec) and not np.isnan(rec) and prec + rec > 0) else np.nan
    return dict(n=len(y), prevalencia=y.mean(), acuracia=(tp + tn) / len(y),
                precision=prec, recall=rec, f1=f1, auc=auc_mw(y, score),
                tp=tp, fp=fp, fn=fn, tn=tn, taxa_pred_bom=pred.mean())


# ── gabaritos ────────────────────────────────────────────────────────────────
art = pq.read_table(ART).to_pandas()
Xa = art[['x0', 'x1']].values[:2000]
Fa = art[['f0', 'f1']].values[:2000]
chk = np.abs(mmf1(Xa) - Fa).max()
print(f'[check] |mmf1(X_artefato) - f_artefato|_max = {chk:.3e}  (implementacao conferida)')

real = pq.read_table(f'{SM}/exp_main_b4_MMF1_42__real.parquet').to_pandas()
Fsid = real.set_index('solution_id')[['f0', 'f1']].astype(float)

sur = pq.read_table(f'{SM}/exp_main_b4_MMF1_42__surrogate.parquet').to_pandas()
recs = [json.loads(l) for l in open(f'{SM}/exp_main_b4_MMF1_42.jsonl')]
gens = {r['geracao']: r for r in recs if r.get('rec') == 'b4_gen'}


def rotulo(F, R, tol=0.0):
    """GetOutput.m:18 — Output = AND_j ( OR_k  f_k <= R_jk ).
    tol>0 relaxa (limite HI); tol<0 aperta (limite LO)."""
    out = np.ones(len(F), dtype=bool)
    for j in range(R.shape[0]):
        out &= (F <= R[j] + tol * (np.abs(R[j]) + 1.0)).any(axis=1)
    return out


rows = []
for regime in ['sonda', 'sonda_estratificada']:
    blk = sur[sur.regime == regime]
    for g, sub in blk.groupby('geracao'):
        gi = gens.get(int(g))
        if gi is None:
            rows.append(dict(regime=regime, geracao=int(g), n=len(sub), sem_gen=True)); continue
        rid = [int(v) for v in gi['ref_ids']]
        R = Fsid.loc[rid].values
        if regime == 'sonda':
            F = Fa[:len(sub)]
            Xb = sub[['x0', 'x1']].values
            djoin = np.abs(Xb.astype(np.float32) - Xa[:len(sub)].astype(np.float32)).max()
        else:
            Xb = sub[['x0', 'x1']].values.astype(float)
            F = mmf1(Xb)
            djoin = np.nan
        y = rotulo(F, R)
        y_hi = rotulo(F, R, tol=+1e-6)
        y_lo = rotulo(F, R, tol=-1e-6)
        pred = (sub['pred_classe'].values == 'bom').astype(int)
        L = sub['pred_confianca'].values.astype(float)
        m = metrics(y, pred, L)
        m.update(regime=regime, geracao=int(g), n_refs=len(rid),
                 ambiguos_f32=int((y_hi != y_lo).sum()), max_dX_join=djoin,
                 L_mediano=float(np.median(L)), rr_gen=gi['rr'],
                 prev_treino=gi['y_treino_dist']['prevalencia_classe_1'],
                 ramo=gi['ramo'], n_arquivo=gi['n_treino'])
        rows.append(m)

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/t11_b4_sonda_rotulo.csv', index=False)

pd.set_option('display.width', 250, 'display.max_columns', 40)
for regime in ['sonda', 'sonda_estratificada']:
    d = df[df.regime == regime]
    print(f'\n=== {regime.upper()} — {len(d)} blocos, {int(d.n.sum())} linhas ===')
    print(f'  prevalencia (rotulo DI-18/GetOutput): media {d.prevalencia.mean():.4f} · '
          f'mediana {d.prevalencia.median():.4f} · min {d.prevalencia.min():.4f} · max {d.prevalencia.max():.4f}')
    print(f'  prevalencia POOLED = {(d.tp + d.fn).sum() / d.n.sum():.4f}')
    print(f'  AUC       : media {d.auc.mean():.4f} · mediana {d.auc.median():.4f} · '
          f'min {d.auc.min():.4f} · max {d.auc.max():.4f} · >0,5 em {(d.auc > .5).sum()}/{d.auc.notna().sum()}')
    print(f'  acuracia  : media {d.acuracia.mean():.4f} · mediana {d.acuracia.median():.4f}')
    print(f'  precision : media {d.precision.mean():.4f} (blocos com TP+FP>0: {d.precision.notna().sum()})')
    print(f'  recall    : media {d.recall.mean():.4f}')
    print(f'  F1        : media {d.f1.mean():.4f}')
    print(f'  taxa pred="bom": media {d.taxa_pred_bom.mean():.4f} · L mediano {d.L_mediano.median():.4f}')
    print(f'  ambiguos float32 (banda 1e-6): {int(d.ambiguos_f32.sum())} de {int(d.n.sum())} linhas')
    tot = dict(tp=int(d.tp.sum()), fp=int(d.fp.sum()), fn=int(d.fn.sum()), tn=int(d.tn.sum()))
    P = tot['tp'] / max(tot['tp'] + tot['fp'], 1); Rc = tot['tp'] / max(tot['tp'] + tot['fn'], 1)
    print(f'  POOLED tp={tot["tp"]} fp={tot["fp"]} fn={tot["fn"]} tn={tot["tn"]} | '
          f'acc={(tot["tp"]+tot["tn"])/d.n.sum():.4f} prec={P:.4f} rec={Rc:.4f} '
          f'F1={0 if P+Rc==0 else 2*P*Rc/(P+Rc):.4f}')
    if regime == 'sonda':
        print(f'  join posicional: max|dX| float32 = {d.max_dX_join.max():.1e} em {len(d)} blocos')
    # tendencia
    d2 = d.sort_values('geracao')
    q = len(d2) // 4
    if q:
        print(f'  tendencia AUC: 1o quartil {d2.auc.head(q).mean():.4f} -> ultimo {d2.auc.tail(q).mean():.4f}')
        print(f'  tendencia prevalencia: {d2.prevalencia.head(q).mean():.4f} -> {d2.prevalencia.tail(q).mean():.4f}')

print('\n=== comparacao dos dois blocos (regra 12: SEPARADOS, nunca somados) ===')
a = df[df.regime == 'sonda']; b = df[df.regime == 'sonda_estratificada']
com = sorted(set(a.geracao) & set(b.geracao))
print(f'  geracoes com AMBOS os blocos: {len(com)}')
cmp = pd.DataFrame({'g': com,
                    'prev_regua': [a[a.geracao == g].prevalencia.iloc[0] for g in com],
                    'prev_estrat': [b[b.geracao == g].prevalencia.iloc[0] for g in com],
                    'auc_regua': [a[a.geracao == g].auc.iloc[0] for g in com],
                    'auc_estrat': [b[b.geracao == g].auc.iloc[0] for g in com]})
cmp.to_csv(f'{OUT}/t11_b4_cmp_blocos.csv', index=False)
print(cmp.to_string(index=False))
print(f'\n  razao prevalencia estrat/regua (mediana) = '
      f'{(cmp.prev_estrat / cmp.prev_regua.replace(0, np.nan)).median():.3f}')
