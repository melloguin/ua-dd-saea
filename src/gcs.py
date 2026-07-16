"""Ponte para o bucket GCS — dual-write local+bucket (§17.7 / D58).

Topologia de persistência (§17.7): os runs **Python** (VMs Vertex AI) gravam cada
artefato em DOIS destinos — **local** (fonte-de-verdade da esteira idempotente) e
**bucket** `gs://mestrado_experiments`; os runs **MATLAB** (Mac) gravam **só
local**. Este módulo é o lado-bucket.

⚠ **Import LAZY do `google-cloud-storage` (como o F0-01 fez com deps pesadas).**
O `google-cloud-storage` **não** está no env-main do Mac (é do stack de VM). Por
isso o `import` da lib acontece **dentro de cada função** que fala com a rede —
`import src.gcs` roda em QUALQUER interpretador. No Mac testa-se o **caminho
LOCAL** (as funções puras `is_bucket_only`/`plan_targets`/`blob_*`, que não
tocam a rede); o dual-write real é exercido na VM.

**Bucket-only para os 5 volumosos (D58/§17.4/§17.7):** `c154, c122, e81, c149,
c262` — a camada ③ (surrogate) deles é ENORME (~0,5–0,9 TB no total do estudo);
o disco da VM não a segura junto do resto, então a ③ **só vai ao bucket** (o
resume desses lista o bucket). As demais camadas (①②/timing/jsonl/manifesto) e os
demais algoritmos fazem **dual-write** (local + bucket).

Identificadores (HANDOFF §7.6):
- bucket  = `mestrado_experiments` (Standard, US multi-região; versionamento ON)
- projeto = `skilled-text-480300-d9`
Nas VMs a SA já traz ADC (sem chave em arquivo).
"""

from __future__ import annotations

import os

from src import naming

#: Identificadores canônicos (HANDOFF §7.6 / §17.7).
BUCKET = "mestrado_experiments"
PROJECT = "skilled-text-480300-d9"

#: Os 5 volumosos cuja camada ③ é **bucket-only** (D58/§17.4). A lista é
#: EXATA (CLAUDE.md §5): c154, c122, e81, c149, c262.
BUCKET_ONLY_ALGS: frozenset[str] = frozenset({"c154", "c122", "e81", "c149", "c262"})

#: Só a camada surrogate (③) é volumosa o bastante p/ ser bucket-only; as demais
#: camadas dos 5 algs seguem dual-write (o resume ainda acha ①②/timing local).
BUCKET_ONLY_LAYERS: frozenset[str] = frozenset({"surrogate"})


def is_bucket_only(alg: str, layer: str = "surrogate") -> bool:
    """A camada `layer` do algoritmo `alg` é bucket-only (D58)? PURA (sem rede)."""
    return alg in BUCKET_ONLY_ALGS and layer in BUCKET_ONLY_LAYERS


# ── Plano de destinos (PURO — sem rede; é o que o Mac exercita) ──────────────

def plan_targets(exp: str, alg: str, problema: str, semente, *,
                 enable_bucket: bool = True,
                 data_root: str = naming.DEFAULT_DATA_ROOT) -> dict:
    """Decide, por artefato do run, ONDE ele mora — SEM tocar a rede.

    Retorna `{artefato: {"local": path|None, "blob": blob_path|None,
    "bucket_only": bool}}` para as 4 camadas + jsonl + manifesto.

    - `enable_bucket=False` (Mac/MATLAB, ou env sem gcs): tudo local, `blob=None`
      → o run não fala com a rede (o caminho que o Mac testa).
    - `enable_bucket=True` (VM Python): dual-write; a ③ dos 5 volumosos é
      **bucket-only** (`local=None` na consolidação, mas escrita local-primeiro
      acontece e é podada após upload — ver `mirror_run`).
    """
    arts: dict[str, dict] = {}
    for layer in naming.LAYERS:
        local = naming.layer_path(exp, alg, problema, semente, layer, data_root)
        fname = naming.layer_filename(exp, alg, problema, semente, layer)
        bonly = enable_bucket and is_bucket_only(alg, layer)
        arts[layer] = {
            "local": local,
            "blob": (naming.blob_path(exp, alg, fname) if enable_bucket else None),
            "bucket_only": bonly,
        }
    # jsonl + manifesto: sempre dual-write (nunca bucket-only) — trilha leve.
    for kind, fn, pathfn in (
        ("jsonl", naming.jsonl_filename, naming.jsonl_path),
        ("manifest", naming.manifest_filename, naming.manifest_path),
    ):
        arts[kind] = {
            "local": pathfn(exp, alg, problema, semente, data_root),
            "blob": (naming.blob_path(exp, alg,
                                      fn(exp, alg, problema, semente))
                     if enable_bucket else None),
            "bucket_only": False,
        }
    return arts


# ── Cliente e primitivas de rede (LAZY — só na VM) ──────────────────────────

def _client(project: str = PROJECT):
    """Cria o `storage.Client`. Import LAZY: falha clara se a lib não existe
    (é o caso do Mac — onde estas funções NÃO devem ser chamadas)."""
    try:
        from google.cloud import storage  # noqa: WPS433 (import local proposital)
    except ImportError as e:  # pragma: no cover — exercido só na VM
        raise RuntimeError(
            "google-cloud-storage ausente — o dual-write GCS roda na VM Vertex "
            "(no Mac o caminho é local; não chame gcs.upload/sync aqui). Pins são "
            "decisão do autor (D80): NÃO instalar aqui.") from e
    return storage.Client(project=project)


def blob_exists(blob_path: str, *, bucket: str = BUCKET,
                project: str = PROJECT, client=None) -> bool:
    """Existe o objeto `blob_path` no bucket? (LAZY — rede.)"""
    client = client or _client(project)
    return client.bucket(bucket).blob(blob_path).exists()


def upload(local_path: str, blob_path: str, *, bucket: str = BUCKET,
           project: str = PROJECT, client=None) -> dict:
    """Sobe `local_path` → `gs://{bucket}/{blob_path}` (LAZY — rede).

    Local-primeiro + upload → local e blob ficam byte-idênticos (§17.7). Upload é
    idempotente (sobrescreve). Retorna `{status, blob, gs_uri}`."""
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"nada a subir: {local_path!r} não existe")
    client = client or _client(project)
    client.bucket(bucket).blob(blob_path).upload_from_filename(local_path)
    return {"status": "uploaded", "blob": blob_path,
            "gs_uri": f"gs://{bucket}/{blob_path}"}


def mirror_run(exp: str, alg: str, problema: str, semente, *,
               bucket: str = BUCKET, project: str = PROJECT,
               prune_bucket_only: bool = True,
               data_root: str = naming.DEFAULT_DATA_ROOT,
               client=None) -> dict:
    """Espelha os artefatos LOCAIS de um run no bucket (LAZY — rede; VM only).

    Sobe cada artefato existente localmente; para a ③ bucket-only dos 5 volumosos
    (D58), após o upload **poda** a cópia local (`prune_bucket_only`) p/ liberar
    disco. Retorna o mapa de `upload_status` por artefato (pra ir ao manifesto,
    §17.7). NÃO é chamado no Mac (sem gcs)."""
    client = client or _client(project)
    plan = plan_targets(exp, alg, problema, semente,
                        enable_bucket=True, data_root=data_root)
    status: dict[str, str] = {}
    for art, tgt in plan.items():
        local, blob = tgt["local"], tgt["blob"]
        if blob is None or not os.path.exists(local):
            status[art] = "absent"
            continue
        upload(local, blob, bucket=bucket, project=project, client=client)
        if tgt["bucket_only"] and prune_bucket_only:
            os.remove(local)                       # ③ volumosa só no bucket (D58)
            status[art] = "uploaded_bucket_only"
        else:
            status[art] = "uploaded"
    return status


def sync_pending(runs: list[tuple], *, bucket: str = BUCKET,
                 project: str = PROJECT,
                 data_root: str = naming.DEFAULT_DATA_ROOT,
                 client=None) -> dict:
    """Re-sobe locais cujo blob falte (§17.7 — passo de sync da esteira). `runs`
    = lista de `(exp, alg, problema, semente)`. Idempotente (upload sobrescreve;
    checa `blob_exists` antes). LAZY — rede; VM only."""
    client = client or _client(project)
    resent = 0
    checked = 0
    for exp, alg, problema, semente in runs:
        plan = plan_targets(exp, alg, problema, semente,
                            enable_bucket=True, data_root=data_root)
        for tgt in plan.values():
            local, blob = tgt["local"], tgt["blob"]
            if blob is None or not os.path.exists(local):
                continue
            checked += 1
            if not blob_exists(blob, bucket=bucket, project=project, client=client):
                upload(local, blob, bucket=bucket, project=project, client=client)
                resent += 1
    return {"checked": checked, "resent": resent}


def smoke_blob_path() -> str:
    """Objeto de smoke do gate F0 (`experiments/_smoke/...` — §22.6/S.4). O upload
    real roda na VM; no Mac só computamos o nome (sem rede)."""
    return "experiments/_smoke/f0_smoke.parquet"


__all__ = [
    "BUCKET", "PROJECT", "BUCKET_ONLY_ALGS", "BUCKET_ONLY_LAYERS",
    "is_bucket_only", "plan_targets", "blob_exists", "upload",
    "mirror_run", "sync_pending", "smoke_blob_path",
]
