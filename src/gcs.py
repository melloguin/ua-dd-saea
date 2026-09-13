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
                 optional_layers: tuple = (),
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
    # [D-12/DI-21] `optional_layers` entra na MESMA rota das obrigatórias — a ⑦
    # `__final` dos 5 offline subia por um bloco paralelo improvisado no
    # standalone (achado A9 da auditoria DI-20); agora o chamador passa
    # `optional_layers=(naming.FINAL_LAYER,)` e a ⑦ é planejada como as demais.
    arts: dict[str, dict] = {}
    for layer in naming.LAYERS + tuple(optional_layers):
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


class ColisaoDeBlob(RuntimeError):
    """[B-10] O objeto JÁ existe e este run não é o dono dele.

    A quimera `batch/c149/q10_ZDT4` foi feita disto: ①②④⑤⑥ do run da v6 (26/07
    14:52→19:05) com a ③ **bit-idêntica** (md5 `1269b87f7612`) ao run do Mac de
    24/07 — dois runs da mesma célula em hosts distintos, um sobrescrevendo o
    objeto do outro. Teste cruzado: ③(bucket)×①(bucket) fechou **0/2.000**.
    """


def _e_412(e: Exception) -> bool:
    """A exceção é o 412 do `if_generation_match`? (sem importar a lib — o
    módulo tem de ser importável no Mac, onde `google-cloud-storage` não existe)"""
    return (getattr(e, 'code', None) == 412
            or type(e).__name__ == 'PreconditionFailed'
            or '412' in str(getattr(e, 'message', '')))


def md5_b64(path: str) -> str:
    """MD5 do arquivo local no MESMO formato que o GCS devolve em `blob.md5_hash`
    (base64 do digest bruto) — é o que permite CONFIRMAR o upload antes de podar."""
    import base64
    import hashlib
    h = hashlib.md5()                     # noqa: S324 — checksum do GCS, não cripto
    with open(path, 'rb') as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b''):
            h.update(bloco)
    return base64.b64encode(h.digest()).decode()


def upload(local_path: str, blob_path: str, *, bucket: str = BUCKET,
           project: str = PROJECT, client=None,
           if_generation_match: int | None = None,
           verificar: bool = False) -> dict:
    """Sobe `local_path` → `gs://{bucket}/{blob_path}` (LAZY — rede).

    Local-primeiro + upload → local e blob ficam byte-idênticos (§17.7).

    **[B-10]** `if_generation_match=0` = "só se o objeto NÃO existir": o GCS
    responde **412** e o upload falha em vez de passar por cima do objeto de
    outra execução — a proteção estrutural contra a quimera. Aqui isso vira
    `ColisaoDeBlob`. `verificar=True` compara o `md5_hash` do blob com o md5
    local: é o que autoriza PODAR a cópia local (D58) — "upload confirmado"
    tem de significar confirmado.
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"nada a subir: {local_path!r} não existe")
    client = client or _client(project)
    blob = client.bucket(bucket).blob(blob_path)
    kw = {} if if_generation_match is None else {
        'if_generation_match': if_generation_match}
    try:
        blob.upload_from_filename(local_path, **kw)
    except Exception as e:  # noqa: BLE001 — só o 412 tem tratamento próprio
        if if_generation_match is not None and _e_412(e):
            raise ColisaoDeBlob(
                f"gs://{bucket}/{blob_path} já existe (generation≠"
                f"{if_generation_match}) — outro run/host é o dono; "
                f"upload recusado para não repetir a quimera do c149.") from e
        raise
    out = {"status": "uploaded", "blob": blob_path,
           "gs_uri": f"gs://{bucket}/{blob_path}"}
    if verificar:
        local_md5 = md5_b64(local_path)
        blob.reload()
        out["md5_local"], out["md5_blob"] = local_md5, blob.md5_hash
        if blob.md5_hash != local_md5:
            raise RuntimeError(
                f"upload NÃO confirmado (md5 divergente) em "
                f"gs://{bucket}/{blob_path}: local={local_md5} "
                f"blob={blob.md5_hash} — a cópia local NÃO será podada.")
        out["status"] = "uploaded_verificado"
    return out


def mirror_run(exp: str, alg: str, problema: str, semente, *,
               bucket: str = BUCKET, project: str = PROJECT,
               prune_bucket_only: bool = True,
               sobrescrever: bool = False,
               data_root: str = naming.DEFAULT_DATA_ROOT,
               client=None) -> dict:
    """Espelha os artefatos LOCAIS de um run no bucket (LAZY — rede; VM only).

    Sobe cada artefato existente localmente; para a ③ bucket-only dos 5 volumosos
    (D58), após o upload **CONFIRMADO por md5** poda a cópia local
    (`prune_bucket_only`) p/ liberar disco. Retorna o mapa de `upload_status` por
    artefato (pra ir ao manifesto, §17.7). NÃO é chamado no Mac (sem gcs).

    **[B-10] `sobrescrever=False` (default) = criar-ou-recusar.** Cada upload vai
    com `if_generation_match=0`: se o objeto já existe, o dono é outro run/host e
    o artefato fica com status `colidiu_412` — **e a cópia local NÃO é podada**.
    Era a poda cega (`os.remove` em `gcs.py:155`) que tornava a quimera do c149
    IRRECUPERÁVEL: a única ③ local havia sido apagada. Re-execução legítima
    (`--force`, re-run de célula `failed`) passa `sobrescrever=True`.
    """
    client = client or _client(project)
    plan = plan_targets(exp, alg, problema, semente,
                        enable_bucket=True, data_root=data_root)
    status: dict[str, str] = {}
    igm = None if sobrescrever else 0
    for art, tgt in plan.items():
        local, blob = tgt["local"], tgt["blob"]
        if blob is None or not os.path.exists(local):
            status[art] = "absent"
            continue
        podar = bool(tgt["bucket_only"] and prune_bucket_only)
        try:
            upload(local, blob, bucket=bucket, project=project, client=client,
                   if_generation_match=igm, verificar=podar)
        except ColisaoDeBlob:
            # o objeto é de outra execução: não sobrescreve, não poda, não mente.
            status[art] = "colidiu_412"
            continue
        if podar:
            os.remove(local)                   # ③ volumosa só no bucket (D58)
            status[art] = "uploaded_bucket_only"
        else:
            status[art] = "uploaded"
    return status


def mirror_evidencia(exp: str, alg: str, problema: str, semente, *,
                     bucket: str = BUCKET, project: str = PROJECT,
                     sobrescrever: bool = True,
                     data_root: str = naming.DEFAULT_DATA_ROOT,
                     client=None) -> dict:
    """[B-09] Espelha a TRILHA LEVE (⑥ + ⑤) de um run que ABORTOU ou FALHOU.

    `mirror_run` só rodava no fim de run bem-sucedido (dentro de
    `write_run_outputs`), então a evidência das ~870 células não-OK de 30
    sementes (29/semente) ficava órfã no disco de uma VM efêmera e morria com
    ela — e o footer `failed`+`erro` do ⑥ é o ÚNICO lugar onde o stack MATLAB
    certifica a própria falha (O-21). Foi por isso que o `rsync` manual das 4
    máquinas teve de acontecer ANTES do desligamento.

    Sobe SÓ ⑥ e ⑤ (nunca bucket-only, nunca poda: as camadas podem estar
    parciais/inconsistentes e o dado local é a fonte-de-verdade da esteira).
    `sobrescrever=True` por default: a evidência do MEU aborto é mais recente
    que o que estiver lá para esta célula, e um 412 aqui perderia o diagnóstico
    — que é justamente o que este espelho existe para salvar.
    **NUNCA levanta**: devolve `{'erro': ...}` (blindagem DI-42.3 — upload
    acessório não mata run, e aqui o run já morreu).
    """
    out: dict[str, str] = {}
    try:
        client = client or _client(project)
        alvos = (('jsonl', naming.jsonl_path(exp, alg, problema, semente, data_root),
                  naming.jsonl_filename(exp, alg, problema, semente)),
                 ('manifest', naming.manifest_path(exp, alg, problema, semente,
                                                   data_root),
                  naming.manifest_filename(exp, alg, problema, semente)))
        for art, local, fname in alvos:
            if not os.path.exists(local):
                out[art] = 'absent'
                continue
            try:
                upload(local, naming.blob_path(exp, alg, fname), bucket=bucket,
                       project=project, client=client,
                       if_generation_match=(None if sobrescrever else 0))
                out[art] = 'uploaded'
            except ColisaoDeBlob:
                out[art] = 'colidiu_412'
    except Exception as e:  # noqa: BLE001 — o run já falhou; isto é resgate
        out['erro'] = f'mirror_evidencia_failed: {e!r}'
    return out


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
    "ColisaoDeBlob", "is_bucket_only", "plan_targets", "blob_exists", "upload",
    "md5_b64", "mirror_run", "mirror_evidencia", "sync_pending",
    "smoke_blob_path",
]
