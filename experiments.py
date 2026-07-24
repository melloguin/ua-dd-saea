"""Despachante PYTHON do harness (raiz) — arquitetura A2 (§16.5 / §19).

Recebe `{algoritmos} × {problemas} × {sementes}` e roda uma task por
`(algoritmo, problema, semente)` chamando a *main oficial* via o adapter
`src/experiment.py` (nada é reimplementado — §2/§20). Paraleliza com
`joblib.Parallel` (backend `loky`), 1 processo por núcleo; a esteira é
**idempotente e resumível** (manifesto `run_id → status`, D58/§19): células
prontas são puladas — com ~16 mil runs, quebras são certas e nunca se re-roda
uma célula concluída.

    python3 experiments.py --exp main --algorithms c262 c154 \
                           --problems MMF1 ZDT1 --seeds 0 1 42 --n-jobs 10
    python3 experiments.py --algorithms none --problems MMF1 --seeds 0   # só monta o grid

**Fase 0 (F0-01-harness):** o despacho por algoritmo ainda **não existe**
(`src.experiment.run` levanta `NotImplementedError` — corpo real em R1/R2/R3).
Este arquivo entrega o **andaime**: grid, esteira idempotente, manifesto por
run (§17.2), logger `.jsonl` (§17.5) e placar de console (D23). Uma task
executada agora fecha como `failed` (adapter não ligado) — honesto e nunca
silencioso; use `--algorithms none` para exercitar só o encanamento.

Imports pesados (`joblib`, `pandas`, `tqdm`) são **lazy** — o andaime roda em
qualquer interpretador; só a execução paralela real (n-jobs>1) e a
consolidação (F0-03) puxam essas libs.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# src/ importável a partir da raiz do repo
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import naming
from src import experiment as _adapter
from src.manifest import (Scoreboard, new_manifest, write_manifest, read_manifest,
                          is_run_done)
from src.audit_log import AuditLogger

# ── Roster canônico do stack PYTHON (§21.2 / S.4-F0#2) ─────────────────────
# Os algoritmos MATLAB (b1,b3,b4,e7,c217,c141,e74,c238,e103,pisos) rodam pelo
# despachante `experiments.m`. Aqui, só o lado Python (BoTorch + standalone).
#
# [DI-31] KNOWN_ALGORITHMS é DERIVADO dos loaders reais (`_DISPATCH_LOADERS`) —
# a lista literal antiga (`…,'b5','c311'`) era um bug de bateria: 'b5' NÃO existe
# no dispatch (as chaves são 'b5r'/'b5m') e 'moead_media' faltava ⇒ a validação
# do CLI (bad_alg abaixo) REJEITAVA os 3 configs offline b5r/b5m/moead_media e a
# bateria M9 era irrodável. Derivar do dispatch torna o allowlist IMPOSSÍVEL de
# driftar (o teste `test_roster_cobre_loaders` trava a regressão).
KNOWN_ALGORITHMS: frozenset = frozenset(
    a for a in _adapter._DISPATCH_LOADERS if not a.startswith('stub'))
#: Default do no-arg (coerente com DEFAULT_EXP='main'): só os ONLINE. Os OFFLINE
#: (b5r/b5m/c311/moead_media) rodam com `--exp off --algorithms …` explícito.
_OFFLINE = frozenset({'b5r', 'b5m', 'c311', 'moead_media', 'e103'})
DEFAULT_ALGORITHMS: list[str] = sorted(KNOWN_ALGORITHMS - _OFFLINE)

# ── Problemas: os 25 canônicos (A2/§4; MMF16_L3 removido) ──────────────────
DEFAULT_PROBLEMS: list[str] = list(_adapter.ALL_PROBLEMS)

# ── Sementes: {0..28} ∪ {42} = 30 (§5.3/D85) ───────────────────────────────
DEFAULT_SEEDS: list[int] = list(range(29)) + [42]

DEFAULT_EXP = 'main'
DEFAULT_DATA_ROOT = 'data'

# ── Política de retry da bateria [M7/DI-06 item 1] ──────────────────────────
#: Tentativas por run (1 + N−1 retries). D23 pedia 1 retry; a bateria pede mais.
RETRY_ATTEMPTS = 3
#: Base do backoff exponencial em segundos (0s → 5s → 20s nas 3 tentativas).
RETRY_BACKOFF_S = 5
GCS_BUCKET = 'mestrado_experiments'   # espelho Python (§17.7); MATLAB = só local
#: [D-16/DI-21] Configs BoTorch — o despachante desliga o kernel fusionado
#: (DEF-L2/DI-05) antes de despachá-los; estado POR PROCESSO.
BOTORCH_ALGS = frozenset({'c262', 'c154', 'e81'})


# ═══════════════════════════════════════════════════════════════════════════
#  Uma task = um run (adapter + manifesto + log de auditoria)
# ═══════════════════════════════════════════════════════════════════════════

def _run_one(exp: str, alg: str, problema: str, semente: int,
             data_root: str, *, modo_rapido: bool = False,
             enable_bucket: bool = False,
             teto_s: float | None = None) -> str:
    """Executa (ou tenta) um run e materializa manifesto + `.jsonl`.

    Retorna o `status` ∈ {ok, retried_ok, failed}. A política de erro-duro
    (D23) dá **1 retry** em falha genérica; um `NotImplementedError` (adapter
    ausente na Fase 0) NÃO é retriável — fecha `failed` na hora, com a razão
    registrada. Toda parada é logada (nunca silenciosa — D23/D60).
    """
    status, n_retries, stack_trace = 'failed', 0, None
    t0 = time.time()
    log = AuditLogger.for_run(exp, alg, problema, semente, data_root)
    try:
        log.header(run_id=naming.run_id(exp, alg, problema, semente),
                   alg=alg, problema=problema, semente=semente, exp=exp,
                   modo_rapido=modo_rapido)
        # ── Retry com BACKOFF [M7/DI-06 item 1 — o incremento 1 do autor] ────
        # A bateria são 16.500 runs em máquina compartilhada: falhas transitórias
        # (licença MATLAB contendida, I/O, OOM momentâneo, rede no upload) são
        # CERTAS. O D23 já previa 1 retry; aqui ele vira `RETRY_ATTEMPTS`
        # tentativas com espera crescente `RETRY_BACKOFF_S · 2^i` (0s → 5s → 20s),
        # que é o que separa "falha transitória" de "falha real". Erros
        # NÃO-RETRIÁVEIS (adapter ausente, arquivo de contexto faltando) cortam na
        # hora — retriar não conserta e só queima tempo.
        attempts = RETRY_ATTEMPTS
        # [D-16/DI-21 — a letra da DI-05] DEF-L2 é estado POR PROCESSO: o
        # despachante também desliga o kernel fusionado antes de despachar um
        # runner BoTorch, sem depender da ordem de importação do runner. Import
        # LAZY e tolerante: no Mac/MATLAB o stack torch pode nem existir.
        if alg in BOTORCH_ALGS:
            try:
                from src.c262_qnehvi import disable_fused_kernel
                disable_fused_kernel()
            except Exception as e:  # noqa: BLE001 — melhor rodar que abortar
                log.event('fused_kernel_disable_indisponivel', err=repr(e))
        for i in range(attempts):
            try:
                # [D-06/DI-21] repassa `data_root` (a mescla DI-13.1 procurava o
                # manifesto no root ERRADO sob --data-root customizado e regravava
                # o toco com 3 timings None — o defeito voltava por outra porta).
                # [DI-32/T2] `enable_bucket` agora é FIO DE PONTA A PONTA: o CLI
                # `--enable-bucket` liga o dual-write §17.7 (a VM efêmera do M8
                # gravaria SÓ local sem isto — perda total no descarte). Default
                # False = Mac/pilotos local puro (RI-08/DI-16.8), como sempre.
                # [DI-34] `q` FIADO AO RUNNER: exp=batch ⇒ q=Q_BATCH (D66; fonte
                # única em budget.py). Sem este fio a bateria batch rodava em
                # q=1 SILENCIOSO (achado crítico da validação final da torre).
                # [T6-batch] `teto_s` FIADO ATE O RUNNER. Os runners que o
                # aceitam (c311, e81) tratam o estouro como DADO — aborto limpo
                # com manifesto `failed`/`teto_wall` (D61/§22.5), nao excecao.
                # Antes o parametro existia mas o despachante NUNCA o passava:
                # o `_TetoWall` era inalcancavel na bateria. Os runners que nao
                # o conhecem simplesmente ignoram (cai no **_kwargs deles).
                _kw = {} if teto_s is None else {'teto_s': float(teto_s)}
                if exp == 'batch':
                    from src.budget import Q_BATCH
                    _kw['q'] = Q_BATCH
                _adapter.run(alg, problema, semente, exp=exp,
                             data_root=data_root, enable_bucket=enable_bucket,
                             **_kw)
                status = 'ok' if i == 0 else 'retried_ok'
                n_retries = i          # nº de re-tentativas até o sucesso
                break
            except NotImplementedError as e:
                # Andaime da Fase 0: adapter não ligado — NÃO retriar.
                status, stack_trace, n_retries = 'failed', repr(e), i
                log.event('not_implemented', msg=str(e))
                break
            except (FileNotFoundError, KeyError) as e:
                # [M7] artefato/config ausente (DoE, dataset, sonda, chave de env):
                # é ERRO DE PREPARAÇÃO, não transitório — retriar não conserta.
                status, stack_trace, n_retries = 'failed', repr(e), i
                log.guard('nao_retriavel', err=f'{type(e).__name__}: {e}')
                break
            except Exception as e:  # noqa: BLE001 — D23: capturar tudo, logar, seguir
                # [D-07/DI-21] Aborto por TETO de wall-clock (`WallClockAbort`
                # dos runners BoTorch) NÃO é retriável: cada retry estouraria o
                # MESMO teto e um teto de 8h viraria 24h. Checagem pelo NOME da
                # classe para não importar torch no despachante.
                if type(e).__name__ == 'WallClockAbort':
                    status, stack_trace, n_retries = 'failed', repr(e), i
                    log.guard('teto_wall_nao_retriavel', err=str(e)[:200])
                    break
                import traceback
                stack_trace = traceback.format_exc()
                n_retries = i          # i re-tentativas já gastas
                log.guard('hard_error', attempt=i, err=f'{type(e).__name__}: {e}')
                if i + 1 >= attempts:
                    status = 'failed'  # esgotou as tentativas
                else:
                    espera = RETRY_BACKOFF_S * (2 ** i)
                    log.event('retry', tentativa=i + 1, de=attempts,
                              espera_s=espera, motivo=f'{type(e).__name__}')
                    time.sleep(espera)
    finally:
        log.footer(status=status, n_retries=n_retries,
                   tempo_total_s=round(time.time() - t0, 4),
                   stack_trace=stack_trace)
        log.close()

    # ── Manifesto: MESCLAR, nunca reconstruir [DI-13.1, autor 2026-07-19] ──────
    # O RUNNER já gravou o manifesto RICO (doe_hash, fe_final, n_geracoes, timing
    # medido, fit_series, sigma_dict, bloco sonda). O despachante sabe outras 3
    # coisas — status/n_retries/stack_trace — e o wall-clock de fora. Reconstruir
    # aqui (o comportamento anterior) SOBRESCREVIA a certidão do runner e a bateria
    # M8 perderia TODO o payload DI-09/DI-10 da camada ⑤, sem sintoma visível.
    # Regra: se o runner gravou → mescla só os campos do despachante; se não gravou
    # (run morreu antes) → cria do zero, como antes.
    bucket = GCS_BUCKET  # Python espelha no bucket (§17.7); o upload é F0-03
    wall = round(time.time() - t0, 4)
    mpath = naming.manifest_path(exp, alg, problema, semente, data_root=data_root)
    man = read_manifest(mpath)
    if man is None:                       # o runner não chegou a gravar
        # [D-06/DI-21] `bucket=None`: se o runner morreu antes de gravar, nada
        # subiu — o carimbo de espelho só entra quando o upload CONFIRMA.
        man = new_manifest(exp, alg, problema, semente, status=status,
                           n_retries=n_retries, stack_trace=stack_trace,
                           timing={'tempo_total_s': wall,
                                   'tempo_fit_surrogate_s': None,
                                   'tempo_busca_s': None, 'tempo_aval_real_s': None},
                           data_root=data_root, bucket=None)
    else:                                 # MESCLA (preserva tudo que o runner pôs)
        man['status'] = status
        man['n_retries'] = n_retries
        if stack_trace:
            man['stack_trace'] = stack_trace
        man.setdefault('timing', {})
        # o wall do despachante inclui overhead de orquestração; só preenche se o
        # runner não mediu (nunca sobrescreve medida por estimativa).
        if not man['timing'].get('tempo_total_s'):
            man['timing']['tempo_total_s'] = wall
        man['timing']['tempo_total_despachante_s'] = wall
        # [D-06/DI-21] O carimbo `paths.bucket` é CONDICIONAL: só afirma o
        # espelho quando o upload de fato aconteceu — `upload_status` é o mapa
        # por artefato que `dual_write_run` grava ({art: "uploaded"|...}); no
        # Mac ele é None e o carimbo NÃO acontece. Um manifesto que MENTE sobre
        # persistência é pior que um que se cala: a VM é efêmera e a ③ dos 5
        # volumosos é o dado insubstituível.
        us = man.get('upload_status')
        subiu = isinstance(us, dict) and any(
            str(v).startswith('uploaded') for v in us.values())
        if bucket and subiu:
            man.setdefault('paths', {})['bucket'] = man.get('paths', {}).get('bucket') or bucket
    write_manifest(man, data_root)
    return status


# ═══════════════════════════════════════════════════════════════════════════
#  Estágios (§16.5): (1) pré-cache compartilhável · (2) grid · (3) consolidação
# ═══════════════════════════════════════════════════════════════════════════

def _stage_precache(problems, seeds, data_root):
    """Estágio 1 — pré-cache do compartilhável por (problema, semente).

    Na arquitetura final, gera/garante o DoE `11D−1` e o dataset offline
    (artefatos parquet — D87/D90). **Fase 0:** stub — o gerador é o cartão
    **F0-02-doe**. Aqui só anuncia.
    """
    print(f'[1/3] Pré-cache compartilhável (DoE/dataset) → cartão F0-02 '
          f'(stub; {len(problems)}×{len(seeds)} pares).')


def sweep_tmp_orfaos(data_root: str = DEFAULT_DATA_ROOT, *, idade_min_s: float = 3600,
                     dry_run: bool = False) -> list[str]:
    """Remove `.tmp` ÓRFÃOS de escritas atômicas interrompidas [M7/DI-06 item 1].

    A escrita atômica (D58) grava em `<arquivo>.tmp` e faz `replace` no fim — um
    crash DURO (kill -9, spot-VM revogada, OOM) entre os dois deixa o `.tmp` para
    trás. Eles não corrompem nada (o resume ignora), mas em 16.500 runs viram
    dezenas de GB de lixo silencioso no disco e no bucket.

    Só apaga o que tem **mais de `idade_min_s`** (default 1h): um `.tmp` recente
    pode ser de um run VIVO neste instante — apagá-lo mataria a escrita em curso.
    Devolve a lista de caminhos (removidos, ou que seriam removidos em `dry_run`).
    """
    from pathlib import Path
    agora, alvos = time.time(), []
    raiz = Path(data_root)
    if not raiz.exists():
        return alvos
    for p in raiz.rglob('*.tmp'):
        try:
            if agora - p.stat().st_mtime < idade_min_s:
                continue           # jovem demais: pode ser um run VIVO
            alvos.append(str(p))
            if not dry_run:
                p.unlink()
        except OSError:
            continue               # sumiu no caminho / sem permissão: ignora
    return alvos


def _stage_grid(tasks, exp, data_root, *, n_jobs, force, modo_rapido, sb,
                enable_bucket=False, teto_s=None):
    """Estágio 2 — executa o grid (idempotente/resumível)."""
    pending = []
    for alg, prob, seed in tasks:
        if not force and is_run_done(exp, alg, prob, seed, data_root):
            sb.record_skip()
        else:
            pending.append((alg, prob, seed))

    print(f'[2/3] Grid: {len(tasks)} células — {sb.skipped} prontas (skip), '
          f'{len(pending)} a rodar em {n_jobs} worker(s).')
    if not pending:
        return

    if n_jobs == 1:
        # Serial — sem joblib (mantém o andaime rodável no python3 base).
        for alg, prob, seed in pending:
            sb.record(_run_one(exp, alg, prob, seed, data_root,
                               modo_rapido=modo_rapido,
                               enable_bucket=enable_bucket, teto_s=teto_s))
            sb.print()
    else:
        from joblib import Parallel, delayed  # lazy (execução paralela real)
        results = Parallel(n_jobs=n_jobs, backend='loky', verbose=0)(
            delayed(_run_one)(exp, alg, prob, seed, data_root,
                              modo_rapido=modo_rapido,
                              enable_bucket=enable_bucket, teto_s=teto_s)
            for alg, prob, seed in pending)
        for st in results:
            sb.record(st)
        sb.print()


def _stage_consolidate(exp, data_root, *, enabled):
    """Estágio 3 — consolida os Parquet por task no export final (§17.4).

    Lê Mac-local + bucket, re-encoda brotli→zstd. **Fase 0:** stub — a
    consolidação real é o cartão de export/consolidação (F0-03/D82). Puxa
    `pandas`/`pyarrow` de forma lazy quando ligada.
    """
    if not enabled:
        print('[3/3] Consolidação desligada (--no-consolidate) — '
              'implementação em F0-03.')
        return
    print('[3/3] Consolidação → cartão F0-03/consolidação (stub).')


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def _parse_algorithms(values) -> list[str]:
    """Resolve o roster. Sentinela `none` (ou vazio) = roster vazio — permite
    montar o grid/manifesto sem executar nada (andaime da Fase 0)."""
    if values is None:
        return list(DEFAULT_ALGORITHMS)
    vals = [v for v in values]
    if len(vals) == 1 and vals[0].lower() == 'none':
        return []
    return vals


def main(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('--exp', default=DEFAULT_EXP,
                   help="Token de experimento (main|off|batch|sweep-<tier>-<dist>).")
    p.add_argument('--algorithms', nargs='+', default=None,
                   help="Roster (subset do stack Python). 'none' = só monta o grid.")
    p.add_argument('--problems', nargs='+', default=DEFAULT_PROBLEMS,
                   help='Problemas (short names; 25 canônicos).')
    p.add_argument('--seeds', nargs='+', type=int, default=DEFAULT_SEEDS,
                   help='Sementes (default: 30 = {0..28} ∪ {42}).')
    p.add_argument('--n-jobs', type=int, default=1,
                   help='Workers joblib (default 1 = serial, sem joblib).')
    p.add_argument('--data-root', default=DEFAULT_DATA_ROOT,
                   help='Raiz das saídas (default: data).')
    p.add_argument('--force', action='store_true',
                   help='Re-roda mesmo células já prontas (ignora a esteira).')
    p.add_argument('--teto-s', type=float, default=None,
                   help='[T6] Teto de wall-clock POR RUN, em segundos. O runner '
                        'que o aceita (c311, e81) aborta LIMPO ao estourar — '
                        'manifesto failed/teto_wall (aborto por teto = DADO, '
                        'D61/§22.5). Default None = sem teto.')
    p.add_argument('--no-consolidate', action='store_true',
                   help='Pula o estágio 3 de consolidação (§17.4/F0-03).')
    p.add_argument('--modo-rapido', action='store_true',
                   help='(passthrough) marca budget reduzido p/ smoke — F0-03.')
    p.add_argument('--enable-bucket', action='store_true',
                   help='[DI-32/T2] liga o dual-write local+bucket (§17.7) — '
                        'OBRIGATÓRIO na VM efêmera do M8; default = só local.')
    args = p.parse_args(argv)

    # Validação de entradas
    if not naming.is_valid_exp(args.exp):
        raise SystemExit(f"exp inválido: {args.exp!r} "
                         f"(main|off|batch|sweep-<tier>-<dist>).")
    algorithms = _parse_algorithms(args.algorithms)
    bad_alg = [a for a in algorithms if a not in KNOWN_ALGORITHMS]
    if bad_alg:
        raise SystemExit(
            f"Algoritmos fora do stack Python: {bad_alg}. "
            f"Conhecidos aqui: {sorted(KNOWN_ALGORITHMS)} "
            f"(os MATLAB rodam via experiments.m).")
    bad_prob = [q for q in args.problems if not _adapter.is_known_problem(q)]
    if bad_prob:
        raise SystemExit(f"Problemas desconhecidos: {bad_prob}. "
                         f"Conhecidos: {_adapter.ALL_PROBLEMS}")

    tasks = [(a, q, s) for a in algorithms for q in args.problems for s in args.seeds]
    print(f"\n[grid] exp={args.exp} | algs={len(algorithms)} × "
          f"problemas={len(args.problems)} × sementes={len(args.seeds)} "
          f"= {len(tasks)} células")
    if not algorithms:
        print("[grid] roster vazio (--algorithms none) — só andaime; "
              "nenhum run executado.")

    sb = Scoreboard()
    t0 = time.time()
    _stage_precache(args.problems, args.seeds, args.data_root)
    _stage_grid(tasks, args.exp, args.data_root,
                n_jobs=args.n_jobs, force=args.force,
                modo_rapido=args.modo_rapido, sb=sb,
                enable_bucket=args.enable_bucket, teto_s=args.teto_s)
    _stage_consolidate(args.exp, args.data_root, enabled=not args.no_consolidate)

    print(f"\n{'=' * 66}")
    print(f"Concluído em {time.time() - t0:.1f}s.  {sb.render()}")
    print('=' * 66)
    # A esteira nunca falha o processo por um run `failed` (D23: segue o grid);
    # o placar/manifesto carregam o status. Saída != 0 só em erro de invocação.
    return 0


if __name__ == '__main__':
    sys.exit(main())
