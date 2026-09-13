#!/usr/bin/env python3
# f52b_contrato.py — F5.2b: varredura de CONTRATO das 664 células aprovadas contra
# o CONTRATO_DE_DADOS (schema por camada + contagens esperadas por regime/tier) +
# o mapa "análise da dissertação → dado presente" (§9 do CONTRATO).
# Saídas: f5/contrato_f52b.csv (só desvios) + resumo no stdout.
import csv, os, sys, json, collections
import numpy as np
from concurrent.futures import ProcessPoolExecutor

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
CENSO = os.path.expanduser('~/censo_bucket_42.csv')
sys.path.insert(0, REPO)
os.chdir(REPO)
import pyarrow.parquet as pq  # noqa: E402

REPROVADAS = {('sweep-big-mvns', 'c311', 'MMF16_20'), ('main', 'b1', 'WFG1')}
PISOS_ONLINE = {'nsga2', 'nsga3', 'moead', 'smsemoa'}
SEM_SONDA = PISOS_ONLINE | {'sobol_batch'}
OFFLINE_FAM = {'e103', 'b5r', 'b5m', 'c311', 'moead_media', 'treed_media'}
POP2_VAZIA_OK = {'b5r', 'b5m', 'c311', 'moead_media', 'treed_media'}
DIMS = {}
for r in csv.DictReader(open(os.path.join(REPO, 'claude_code_context', 'artifacts',
                                          'characteristics.csv'), encoding='utf-8')):
    DIMS[r['problema']] = int(r['D'])

COLS_1 = {'algoritmo', 'problema', 'semente', 'solution_id', 'fe_index', 'fase'}
COLS_3 = {'regime', 'geracao', 'real_solution_id', 'pred_tipo', 'pred_classe',
          'pred_score', 'pred_confianca', 'modelo_flag', 'espaco_modelo',
          'transf_tipo', 'transf_params', 'fe_treino_max'}
COLS_4 = {'run_id', 'geracao', 'n_acumulado', 'tempo_fit_s', 'tempo_busca_s',
          'tempo_pred_sonda_s', 'tempo_geracao_s'}
MAN_KEYS = {'run_id', 'status', 'fe_final', 'maxfe', 'params', 'timing'}

def esperado_n1(exp, alg, D):
    if exp == 'batch':
        return 11 * D - 1 + 2000
    if exp.startswith('sweep-'):
        tier = exp.split('-')[1]
        return {'small': 31 * D - 1, 'medium': 2000, 'big': 50000}[tier]
    return 31 * D - 1

def uma(args):
    exp, alg, prob = args
    D = DIMS[prob]
    base = 'data/experiments/%s/%s/exp_%s_%s_%s_42' % (exp, alg, exp, alg, prob)
    achados = []
    def A(camada, tipo, det):
        achados.append([exp, alg, prob, camada, tipo, det])
    try:
        # ① — contagem exata + colunas + fase
        t1 = pq.read_table(base + '__real.parquet')
        n_esp = esperado_n1(exp, alg, D)
        if t1.num_rows != n_esp:
            A('1', 'CONTAGEM', 'linhas=%d esperado=%d' % (t1.num_rows, n_esp))
        falta = COLS_1 - set(t1.column_names)
        if falta:
            A('1', 'SCHEMA', 'faltam %s' % sorted(falta))
        fase = collections.Counter(str(x) for x in t1.column('fase').to_pylist())
        if exp == 'main' or exp == 'batch':
            if fase.get('init', 0) != 11 * D - 1:
                A('1', 'FASE', 'init=%d esperado=%d' % (fase.get('init', 0), 11 * D - 1))
        else:
            if fase.get('init', 0) != t1.num_rows:
                A('1', 'FASE', 'offline com fase!=init: %s' % dict(fase))
        # ② — presença/vazio conforme família
        t2 = pq.read_table(base + '__pop.parquet')
        if t2.num_rows == 0 and alg not in POP2_VAZIA_OK and alg != 'sobol_batch':
            A('2', 'VAZIA', '0 linhas fora da família offline-vazia')
        # ③ — schema + sonda conforme família
        t3m = pq.read_table(base + '__surrogate.parquet')
        if alg in SEM_SONDA:
            if t3m.num_rows != 0:
                A('3', 'INESPERADA', 'piso com ③ não-vazia: %d' % t3m.num_rows)
        else:
            falta = COLS_3 - set(t3m.column_names)
            if falta:
                A('3', 'SCHEMA', 'faltam %s' % sorted(falta))
            reg = collections.Counter(str(x) for x in t3m.column('regime').to_pylist())
            n_sonda = reg.get('sonda', 0)
            if alg in OFFLINE_FAM and exp != 'main':
                esp = {'e103': 40000, 'c311': 40000, 'treed_media': 20000,
                       'b5r': 20000, 'b5m': 20000, 'moead_media': 20000}[alg]
                if n_sonda != esp:
                    A('3', 'SONDA', 'linhas sonda=%d esperado=%d' % (n_sonda, esp))
            else:
                if n_sonda == 0 or n_sonda % 2000 != 0:
                    A('3', 'SONDA', 'linhas sonda=%d (esperado múltiplo de 2000, >0)' % n_sonda)
        # ④
        t4 = pq.read_table(base + '__timing.parquet')
        if t4.num_rows == 0:
            A('4', 'VAZIA', '0 linhas')
        falta = COLS_4 - set(t4.column_names)
        if falta:
            A('4', 'SCHEMA', 'faltam %s' % sorted(falta))
        # ⑤
        m = json.load(open(base + '.manifest.json', encoding='utf-8'))
        falta = MAN_KEYS - set(m)
        if falta:
            A('5', 'CHAVES', 'faltam %s' % sorted(falta))
        if m.get('fe_final') != m.get('maxfe'):
            A('5', 'FE', 'fe_final=%s maxfe=%s' % (m.get('fe_final'), m.get('maxfe')))
        if alg not in SEM_SONDA and not m.get('sigma_dict'):
            A('5', 'SIGMA_DICT', 'ausente/vazio (DEF-C4)')
        if exp == 'batch' and int(m.get('q') or 0) != 10:
            A('5', 'Q', 'q=%s esperado 10' % m.get('q'))
        # ⑦ offline
        if alg in OFFLINE_FAM and exp != 'main':
            t7 = pq.read_table(base + '__final.parquet')
            if t7.num_rows == 0:
                A('7', 'VAZIA', '0 linhas')
            if 'nd_pos_real' not in t7.column_names:
                A('7', 'SCHEMA', 'sem nd_pos_real')
    except Exception as e:  # noqa: BLE001
        A('?', 'ERRO', '%s: %s' % (type(e).__name__, str(e)[:140]))
    return achados

if __name__ == '__main__':
    cells = [(r['exp'], r['alg'], r['problema'])
             for r in csv.DictReader(open(CENSO, encoding='utf-8'))
             if r['estado'] == 'OK' and (r['exp'], r['alg'], r['problema']) not in REPROVADAS]
    todos = []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for i, a in enumerate(ex.map(uma, cells, chunksize=8)):
            todos.extend(a)
            if (i + 1) % 150 == 0:
                print('%d/%d' % (i + 1, len(cells)), flush=True)
    with open(os.path.join(REPO, 'f5', 'contrato_f52b.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['exp', 'alg', 'problema', 'camada', 'tipo', 'detalhe'])
        w.writerows(todos)
    por = collections.Counter((a[3], a[4]) for a in todos)
    print(json.dumps({'celulas': len(cells), 'desvios': len(todos),
                      'por_tipo': {'%s/%s' % k: v for k, v in sorted(por.items())}},
                     indent=1))
    for a in todos[:30]:
        print('DESVIO:', a)
