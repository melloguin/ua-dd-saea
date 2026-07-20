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
# despachante `experiments.m`. Aqui, só o lado Python (BoTorch + standalone):
DEFAULT_ALGORITHMS: list[str] = ['c262', 'c154', 'e81', 'c122', 'c149', 'b5', 'c311']
KNOWN_ALGORITHMS: set[str] = set(DEFAULT_ALGORITHMS)

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


# ═══════════════════════════════════════════════════════════════════════════
#  Uma task = um run (adapter + manifesto + log de auditoria)
# ═══════════════════════════════════════════════════════════════════════════

def _run_one(exp: str, alg: str, problema: str, semente: int,
             data_root: str, *, modo_rapido: bool = False) -> str:
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
        for i in range(attempts):
            try:
                _adapter.run(alg, problema, semente, exp=exp)
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
        man = new_manifest(exp, alg, problema, semente, status=status,
                           n_retries=n_retries, stack_trace=stack_trace,
                           timing={'tempo_total_s': wall,
                                   'tempo_fit_surrogate_s': None,
                                   'tempo_busca_s': None, 'tempo_aval_real_s': None},
                           data_root=data_root, bucket=bucket)
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
        if bucket:
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


def _stage_grid(tasks, exp, data_root, *, n_jobs, force, modo_rapido, sb):
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
                               modo_rapido=modo_rapido))
            sb.print()
    else:
        from joblib import Parallel, delayed  # lazy (execução paralela real)
        results = Parallel(n_jobs=n_jobs, backend='loky', verbose=0)(
            delayed(_run_one)(exp, alg, prob, seed, data_root,
                              modo_rapido=modo_rapido)
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
    p.add_argument('--no-consolidate', action='store_true',
                   help='Pula o estágio 3 de consolidação (§17.4/F0-03).')
    p.add_argument('--modo-rapido', action='store_true',
                   help='(passthrough) marca budget reduzido p/ smoke — F0-03.')
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
                modo_rapido=args.modo_rapido, sb=sb)
    _stage_consolidate(args.exp, args.data_root, enabled=not args.no_consolidate)

    print(f"\n{'=' * 66}")
    print(f"Concluído em {time.time() - t0:.1f}s.  {sb.render()}")
    print('=' * 66)
    # A esteira nunca falha o processo por um run `failed` (D23: segue o grid);
    # o placar/manifesto carregam o status. Saída != 0 só em erro de invocação.
    return 0


if __name__ == '__main__':
    sys.exit(main())
