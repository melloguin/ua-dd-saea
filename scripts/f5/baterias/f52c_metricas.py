#!/usr/bin/env python3
# f52c_metricas.py — F5.2c: métricas OFICIAIS (src/metrics.py, NUNCA reimplementar)
# nas 664 células aprovadas: finais (IGD+ primária, HV, IGD, GD, spacing, n_nd) +
# trajetória de 20 checkpoints. Gate D92 ANTES de qualquer conta.
# Saídas: f5/metricas_finais_f52c.csv + f5/trajetorias/{run_id}.json
import csv, os, sys, json
from concurrent.futures import ProcessPoolExecutor

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
CENSO = os.path.expanduser('~/censo_bucket_42.csv')
sys.path.insert(0, REPO)
os.chdir(REPO)

from src import metrics  # noqa: E402

# ── GATE D92 ────────────────────────────────────────────────────────────────
v = metrics.hv_smoke_bbob_f1()
assert abs(v - 1.04333) < 5e-6, 'GATE D92 FALHOU: %r' % v
print('gate D92 OK: %.5f' % v, flush=True)

REPROVADAS = {('sweep-big-mvns', 'c311', 'MMF16_20'),   # F5.1: B1 mascarado
              ('main', 'b1', 'WFG1')}                    # F5.2a: ⑥ contaminado
cells = [(r['exp'], r['alg'], r['problema'])
         for r in csv.DictReader(open(CENSO, encoding='utf-8'))
         if r['estado'] == 'OK' and (r['exp'], r['alg'], r['problema']) not in REPROVADAS]
print('células:', len(cells), flush=True)

TRAJ_DIR = os.path.join(REPO, 'f5', 'trajetorias')
os.makedirs(TRAJ_DIR, exist_ok=True)

def uma(args):
    exp, alg, prob = args
    try:
        m = metrics.metrics_from_real(exp, alg, prob, 42, with_trajectory=True,
                                      n_checkpoints=20)
        rid = '%s_%s_%s_42' % (exp, alg, prob)
        with open(os.path.join(TRAJ_DIR, rid + '.json'), 'w') as fh:
            json.dump(m['trajectory'], fh)
        f = m['final']
        return [exp, alg, prob, f['igd_plus'], f['hv'], f['igd'], f['gd'],
                f['spacing'], f['n_nd'], '']
    except Exception as e:  # noqa: BLE001
        return [exp, alg, prob, '', '', '', '', '', '', '%s: %s' % (type(e).__name__, str(e)[:150])]

if __name__ == '__main__':
    res = []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for i, r in enumerate(ex.map(uma, cells, chunksize=8)):
            res.append(r)
            if (i + 1) % 100 == 0:
                print('%d/%d' % (i + 1, len(cells)), flush=True)
    res.sort(key=lambda r: (r[0], r[1], r[2]))
    with open(os.path.join(REPO, 'f5', 'metricas_finais_f52c.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['exp', 'alg', 'problema', 'igd_plus', 'hv', 'igd', 'gd',
                    'spacing', 'n_nd', 'erro'])
        w.writerows(res)
    erros = [r for r in res if r[9]]
    print(json.dumps({'ok': len(res) - len(erros), 'erros': len(erros)}))
    for r in erros[:20]:
        print('ERRO:', r[0], r[1], r[2], '|', r[9])
