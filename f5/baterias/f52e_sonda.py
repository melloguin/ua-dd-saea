#!/usr/bin/env python3
# f52e_sonda.py — F5.2c(2): curvas da SONDA por célula — WAPE/corr/cobertura por
# bloco × objetivo, na régua comum (join POR POSIÇÃO com data/sonda). Definições
# congeladas no protocolo §5: por objetivo, espaço CRU (des-transformado via
# transf_params quando espaco_modelo=='transformado'), cobertura = |mu-f|<=1.96σ.
# Escopo: configs regressores (pred_tipo='valor'). b1 = à parte (escalar D47);
# classificadores (c217, b4, c122) e sobol/pisos-online = sem sonda ou fora.
import csv, os, sys, json
import numpy as np
from concurrent.futures import ProcessPoolExecutor

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
CENSO = os.path.expanduser('~/censo_bucket_42.csv')
sys.path.insert(0, REPO)
os.chdir(REPO)
import pyarrow.parquet as pq  # noqa: E402

REGRESSORES = {'b3', 'e7', 'c141', 'c238', 'c262', 'c154', 'e81', 'c149',
               'c311', 'e103', 'b5r', 'b5m', 'moead_media', 'treed_media', 'e74'}
REPROVADAS = {('sweep-big-mvns', 'c311', 'MMF16_20'), ('main', 'b1', 'WFG1')}
OFFLINE = {'off'} | {e for e in ['sweep-small-lhs','sweep-small-mvns','sweep-medium-lhs',
                                 'sweep-medium-mvns','sweep-big-lhs','sweep-big-mvns']}

def destransforma(mu, sg, tipo, params, espaco):
    if espaco != 'transformado' or tipo in (None, '', 'cru'):
        return mu, sg
    p = json.loads(params) if isinstance(params, str) else (params or {})
    if tipo == 'translacao':
        ymin = np.asarray(p.get('ymin'), float)
        return mu + ymin, sg
    if tipo in ('zscore', 'z'):
        mean = np.asarray(p.get('mean'), float); std = np.asarray(p.get('std'), float)
        return mu * std + mean, (sg * std if sg is not None else None)
    if tipo == 'minmax':
        mn = np.asarray(p.get('min'), float)
        rg = np.asarray(p.get('range', p.get('max')), float)
        return mu * rg + mn, (sg * rg if sg is not None else None)
    raise ValueError('transf_tipo nao suportado: %r' % tipo)

def uma(args):
    exp, alg, prob = args
    rid = '%s_%s_%s_42' % (exp, alg, prob)
    path = 'data/experiments/%s/%s/exp_%s__surrogate.parquet' % (exp, alg, rid)
    out, err = [], ''
    try:
        t = pq.read_table(path, filters=[('regime', '=', 'sonda')])
        if t.num_rows == 0:
            return [], '%s: 0 linhas de sonda' % rid
        gab = pq.read_table('data/sonda/sonda_%s.parquet' % prob)
        fcols = sorted(c for c in gab.column_names if c[0] == 'f' and c[1:].isdigit())
        Fg = np.column_stack([np.asarray(gab.column(c), float) for c in fcols])
        M = len(fcols)
        df = t.to_pandas()
        # blocos: online -> por geracao; offline -> chunks POSICIONAIS de 20000
        # (b5/moead_media 1 bloco; c311/treed 2 [build,final]; e103 2 [Krig,RBFN])
        blocos = []
        if exp in OFFLINE and df['geracao'].isna().all():
            S = 20000
            for i in range(0, len(df), S):
                blocos.append(('blk%d' % (i // S), df.iloc[i:i + S]))
        else:
            for g, sub in df.groupby(df['geracao'].astype(float)):
                blocos.append((int(g), sub.sort_index()))
        for bid, sub in blocos:
            n = len(sub)
            if n not in (2000, 20000):
                err += ' bloco %s com %d linhas;' % (bid, n)
                continue
            mu = np.column_stack([sub['mu_%d' % j].to_numpy(float) for j in range(M)])
            sg_cols = ['sigma_%d' % j for j in range(M) if 'sigma_%d' % j in sub.columns]
            sg = (np.column_stack([sub[c].to_numpy(float) for c in sg_cols])
                  if len(sg_cols) == M else None)
            tipo = sub['transf_tipo'].dropna().iloc[0] if sub['transf_tipo'].notna().any() else None
            esp = sub['espaco_modelo'].dropna().iloc[0] if sub['espaco_modelo'].notna().any() else 'cru'
            par = sub['transf_params'].dropna().iloc[0] if sub['transf_params'].notna().any() else None
            try:
                mu, sg = destransforma(mu, sg, tipo, par, esp)
            except Exception as e:  # noqa: BLE001
                err += ' destransf %s: %s;' % (bid, e)
                continue
            F = Fg[:n]
            flag = str(sub['modelo_flag'].iloc[0]) if 'modelo_flag' in sub else ''
            for j in range(M):
                m_j, f_j = mu[:, j], F[:, j]
                ok = np.isfinite(m_j)
                if ok.sum() < 10:
                    continue
                wape = float(np.abs(m_j[ok] - f_j[ok]).sum() / max(np.abs(f_j[ok]).sum(), 1e-12))
                corr = float(np.corrcoef(m_j[ok], f_j[ok])[0, 1]) if np.std(m_j[ok]) > 0 else float('nan')
                cob = ''
                if sg is not None:
                    s_j = sg[:, j]
                    ok2 = ok & np.isfinite(s_j)
                    if ok2.sum() >= 10:
                        cob = float((np.abs(m_j[ok2] - f_j[ok2]) <= 1.96 * s_j[ok2]).mean())
                fe = int(sub['fe_treino_max'].dropna().iloc[0]) if sub['fe_treino_max'].notna().any() else ''
                out.append([exp, alg, prob, bid, flag, fe, j, round(wape, 6),
                            round(corr, 6) if corr == corr else '',
                            round(cob, 4) if cob != '' else '',
                            int(ok.sum()), int(n - ok.sum())])
    except Exception as e:  # noqa: BLE001
        err = '%s: %s: %s' % (rid, type(e).__name__, str(e)[:150])
    return out, err

if __name__ == '__main__':
    cells = [(r['exp'], r['alg'], r['problema'])
             for r in csv.DictReader(open(CENSO, encoding='utf-8'))
             if r['estado'] == 'OK' and r['alg'] in REGRESSORES
             and (r['exp'], r['alg'], r['problema']) not in REPROVADAS]
    print('células regressoras:', len(cells), flush=True)
    rows, errs = [], []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for i, (o, e) in enumerate(ex.map(uma, cells, chunksize=4)):
            rows.extend(o)
            if e:
                errs.append(e)
            if (i + 1) % 50 == 0:
                print('%d/%d' % (i + 1, len(cells)), flush=True)
    with open(os.path.join(REPO, 'f5', 'sonda_f52e.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['exp', 'alg', 'problema', 'bloco', 'modelo_flag', 'fe_treino_max',
                    'obj', 'wape', 'corr', 'cobertura95', 'n_validas', 'n_nan'])
        w.writerows(rows)
    print(json.dumps({'linhas': len(rows), 'células_com_aviso': len(errs)}))
    for e in errs[:25]:
        print('AVISO:', e)
