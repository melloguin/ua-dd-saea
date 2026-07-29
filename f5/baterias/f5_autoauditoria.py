#!/usr/bin/env python3
# f5_autoauditoria.py — verificacao final do estado da F5: os artefatos existem, os
# numeros batem entre si, e nada ficou pendente. Roda tudo do zero, sem confiar em
# memoria. READ-ONLY (so le).
import csv, json, os, subprocess, sys, glob, collections

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
os.chdir(REPO)
OK, FAIL = [], []


def chk(nome, cond, detalhe=''):
    (OK if cond else FAIL).append('%-58s %s' % (nome, detalhe))


# ── 1. artefatos obrigatorios existem ───────────────────────────────────────
OBRIG = ['f5/RELATORIO_F5.md', 'f5/RELATORIO_FINAL_F5.md', 'f5/PLANO_RODADA_PERFEITA.md',
         'f5/INVENTARIO_ARTEFATOS_F5.md', 'f5/PROTOCOLO_ANALISE_FIDELIDADE.md',
         'f5/scores_f53.csv', 'f5/gates_f51.csv', 'f5/integridade_f52a.csv',
         'f5/contrato_f52b.csv', 'f5/metricas_finais_f52c.csv', 'f5/sonda_f52e.csv',
         'f5/tempo_f52d.csv', 'f5/transversais_f55.md',
         'f5/transversais_f55_sec4_corrigida.md', 'DOSSIE_FIDELIDADE_R1.md']
for p in OBRIG:
    chk('existe: ' + p, os.path.exists(p), '%d B' % (os.path.getsize(p) if os.path.exists(p) else 0))

# ── 2. contagens ────────────────────────────────────────────────────────────
n_rel = len(glob.glob('f5/relatorios_config/*.md'))
chk('24 relatorios por config', n_rel == 24, '%d' % n_rel)
n_adv = len(glob.glob('f5/adversarial/*.md'))
chk('14 vereditos adversariais', n_adv == 14, '%d' % n_adv)
n_traj = len(glob.glob('f5/trajetorias/*.json'))
chk('664 trajetorias', n_traj == 664, '%d' % n_traj)
n_cel = len(glob.glob(RES + '/*/*/42'))
chk('666 celulas organizadas', n_cel == 666, '%d' % n_cel)

# ── 3. coerencia dos numeros ────────────────────────────────────────────────
gates = list(csv.DictReader(open('f5/gates_f51.csv')))
verm = [g for g in gates if g['exit'] != '0']
chk('gates: 666 linhas', len(gates) == 666, '%d' % len(gates))
chk('gates: 5 vermelhos (4 tolerancia + 1 B1)', len(verm) == 5,
    '%d: %s' % (len(verm), ', '.join('%s/%s' % (v['alg'], v['problema']) for v in verm)))

met = list(csv.DictReader(open('f5/metricas_finais_f52c.csv')))
chk('metricas: 664 celulas, 0 erro', len(met) == 664 and not any(m['erro'] for m in met),
    '%d linhas, %d erros' % (len(met), sum(1 for m in met if m['erro'])))

sc = list(csv.DictReader(open('f5/scores_f53.csv')))
media = sum(float(s['score']) for s in sc) / len(sc)
chk('scores: 24 configs', len(sc) == 24, 'media %.2f' % media)
chk('scores: todos ACEITAR', all('aceitar' in s['recomendacao'].lower() for s in sc),
    'min=%s' % min(float(s['score']) for s in sc))

sonda = sum(1 for _ in open('f5/sonda_f52e.csv')) - 1
chk('sonda: 44.928 medicoes', sonda == 44928, '%d' % sonda)

# ── 4. gate D92 da metrica (re-executado agora) ─────────────────────────────
sys.path.insert(0, REPO)
try:
    from src.metrics import hv_smoke_bbob_f1
    v = hv_smoke_bbob_f1()
    chk('gate D92 hv_smoke_bbob_f1 == 1,04333', abs(v - 1.04333) < 5e-6, '%.6f' % v)
except Exception as e:
    chk('gate D92', False, str(e)[:60])

# ── 5. correcoes aplicadas seguem aplicadas ─────────────────────────────────
import pyarrow.parquet as pq
p7 = RES + '/e103/swap_medium-lhs_ZDT4/42/exp_sweep-medium-lhs_e103_ZDT4_42__final.parquet'
n7 = pq.read_table(p7).num_rows if os.path.exists(p7) else -1
chk('correcao: 7 do e103/ZDT4 com 100 linhas (era 200)', n7 == 100, '%d' % n7)

j = 'data/experiments/batch/e81/exp_batch_e81_ZDT4_42.jsonl'
nf = sum(1 for l in open(j) if '"footer"' in l)
modo = oct(os.stat(j).st_mode)[-3:]
chk('correcao: jsonl do e81/ZDT4 restaurado (95 footers) e congelado', nf == 95 and modo == '444',
    '%d footers, modo %s' % (nf, modo))

# 666 jsonl locais vs bucket
import hashlib
def h(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()
STAG = RES + '/_old/_bucket_raw/experiments'
dif = []
for p in glob.glob('data/experiments/*/*/*_42.jsonl'):
    s = os.path.join(STAG, os.path.relpath(p, 'data/experiments'))
    if os.path.exists(s) and h(p) != h(s):
        dif.append(os.path.relpath(p, 'data/experiments'))
chk('jsonl locais identicos ao bucket (exceto 2 versoes do Mac)', len(dif) <= 2,
    '%d divergentes: %s' % (len(dif), ', '.join(d.split('/')[-1] for d in dif)))

# ── 6. git limpo e commits ──────────────────────────────────────────────────
st = subprocess.run(['git', 'status', '--porcelain', 'f5/', 'DOSSIE_FIDELIDADE_R1.md'],
                    capture_output=True, text=True).stdout.strip()
chk('git: f5/ e dossie commitados', st == '', st[:60] or 'limpo')
n_commits = subprocess.run(['bash', '-c', "git log --oneline | grep -cE '\\[F5'"],
                           capture_output=True, text=True).stdout.strip()
chk('git: commits [F5*]', int(n_commits) >= 19, n_commits)

# ── 7. exclusoes coerentes entre os documentos ──────────────────────────────
rel = open('f5/RELATORIO_FINAL_F5.md', encoding='utf-8').read()
for cel in ['sweep-big-mvns/c311/MMF16_20', 'main/b1/WFG1', 'batch/c149/ZDT4']:
    chk('exclusao citada no relatorio final: ' + cel,
        cel in rel or cel.replace('/', '/') in rel, '')

print('=' * 78)
print(' AUTOAUDITORIA F5 — %d OK / %d FALHAS' % (len(OK), len(FAIL)))
print('=' * 78)
for l in OK:
    print('  ok   ' + l)
for l in FAIL:
    print('  FAIL ' + l)
sys.exit(1 if FAIL else 0)
