"""Infra TRANSVERSAL da Rodada 3 — algoritmos standalone de repo próprio.

[R3-00-harness] O irmão torch-livre do `src/botorch_harness.py` (R2-00). Serve os
6 configs de implementação própria da R3 — **c122** (θ-DEA-DP), **b5r/b5m**
(Prob-RVEA / Prob-MOEA/D), **c311** (TGPR-MO), **c149** (LB-NMOBO), **e81**
(qPOTS) e o **piso offline** (MOEA/D-média, D77) — e a camada `__final` do
regime offline (DI-08, escrita por `scripts/final_eval.py`).

O QUE MUDA EM RELAÇÃO AO R2-00 (e por que este módulo existe):

1. **Sem torch no envelope de dependências.** `b5`/`c311`/`piso-off` rodam em
   venvs DESDEO com pymoo/sklearn antigos e **nenhum torch**; importar
   `botorch_harness` (que faz `import torch` no topo) quebraria o processo.
   Aqui todo stack pesado é import LAZY e OPCIONAL — o módulo importa no
   `python3` base do Mac.
2. **Subprocess-por-venv (D79 / contrato N.2).** O achado nº 1 do contrato R3:
   b5 e c311 vendorizam `desdeo_emo`/`desdeo_problem`/`desdeo_tools` com o
   MESMO NOME e código DIFERENTE. `sys.modules` cacheia o primeiro importado ⇒
   **co-importar b5 e c311 no mesmo processo usa DataProblem/RVEA ERRADOS, sem
   erro nenhum**. A separação não é higiene: é correção. `run_in_venv()` é o
   mecanismo — 1 run = 1 processo = 1 venv, com o pin D79 aplicado NO FILHO.
3. **Regime OFFLINE nativo.** O molde provado pelo e103 (R1): o orçamento **É**
   o dataset (D90), a ① é o dataset, o CP-init confere `x_hash` **E** `f_hash`,
   e qualquer FE na busca é **violação** (pára-e-loga), não término.
4. **Nasce em v5.2.1.** `fe_treino_max` na ③, `regime` por linha, ④ com
   `tempo_busca_s`/`tempo_pred_sonda_s`/`tempo_geracao_s` e o bloco `timing`
   do manifesto — tudo desde o primeiro run, sem retrofit posterior.

O QUE É REUSADO SEM DUPLICAÇÃO: `src.export` (as 4 camadas + o bloco timing),
`src.budget` (FEBudget/D89/D61), `src.doe` (hash do array decodificado),
`src.manifest`, `src.audit_log`, `src.gcs`, `src.naming`. Este módulo não
reimplementa nenhum writer.

Ver `handoff/R3-00-harness.md` para o que cada cartão R3 herda.
"""

from __future__ import annotations

import gc
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from contextlib import contextmanager

# ── Pin D79 / N.1.1 — ANTES de qualquer import numérico ─────────────────────
# O mesmo contrato do R2-00: as libs de BLAS leem estas variáveis no momento do
# `import`, não no momento da chamada. Setá-las depois é no-op silencioso.
#: As 4 variáveis de thread do D79 (o `maxNumCompThreads(1)` é o lado MATLAB).
D79_THREAD_VARS: tuple[str, ...] = (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
)
for _v in D79_THREAD_VARS:
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

from src import naming  # noqa: E402
from src import budget as _budget  # noqa: E402
from src import export as _export  # noqa: E402
from src import gcs as _gcs  # noqa: E402
from src import manifest as _manifest  # noqa: E402
from src.audit_log import AuditLogger  # noqa: E402

#: Raiz do repo (este arquivo mora em `src/`).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Tabela alg→env do D79 (artefato machine-readable — NUNCA parsear a SPEC).
ENVS_JSON = os.path.join(ROOT, "claude_code_context", "artifacts", "envs.json")

#: Os 5 configs do regime OFFLINE (§7/§9/D90 + D77). O e103 é MATLAB (R1); os
#: outros 4 são desta rodada. É esta lista que decide quem DEVE ter a camada ⑦.
OFFLINE_CONFIGS: tuple[str, ...] = ("e103", "b5r", "b5m", "c311", "moead_media",
                                    "treed_media")   # [DI-35.2/T8] piso-big

#: 🔴 Configs que **NUNCA** podem rodar no processo do despachante (N.1.2).
#: b5 e c311 vendorizam `desdeo_emo`/`desdeo_problem`/`desdeo_tools` com o MESMO
#: NOME e código DIFERENTE (21 arquivos .py homônimos e divergentes, incluindo
#: `EAs/RVEA.py` e `population/Population.py`); `sys.modules` cacheia o primeiro
#: importado, então o segundo run recebe as classes do primeiro **sem erro e sem
#: warning** — e sai numericamente errado com o manifesto dizendo `ok`.
#: `experiment.run` ROTEIA estes algs para `run_in_venv` (ver `_in_child`).
#:
#: [T6-batch] 🔴 **DERIVADO de `envs.json`, não mais literal.** O critério real é
#: *"o alg roda num env DIFERENTE do despachante"* — e o despachante roda em
#: `env_main` (`experiments.py`). A lista literal cobria só os 4 do overlay
#: `desdeo_*` e **esquecia o `e81`**, que tem env próprio (`env_e81_qpots`) com
#: pins materialmente distintos: **botorch 0.16.1 × 0.18.1** do env_main
#: (+ gpytorch 1.14.2×1.15.2, numpy 2.2.6×2.4.6, pymoo 0.6.1.6×0.6.2). Os runs
#: validados do e81 em `data/experiments/main/e81/` registram botorch **0.16.1**
#: no manifesto — ou seja, a bateria despachada por `experiments.py` rodaria o
#: e81 com um stack DIFERENTE do que validou o config, sem erro e sem warning.
#: Derivar do artefato torna isso drift-proof (a lição da DI-31): um config novo
#: com env próprio passa a ser roteado sozinho.
def _derivar_venv_only() -> frozenset[str]:
    """Algs cujo `alg_to_env` != o env do despachante (`env_main`) — D79."""
    try:
        tabela = load_env_table()["alg_to_env"]
    except Exception:                                      # noqa: BLE001
        raise RuntimeError(
            "envs.json:alg_to_env ilegível — não dá para decidir o roteamento "
            "por venv (D79). Pára-e-loga (D81): rodar com uma lista-fallback "
            "silenciosa é exatamente o bug que este derivador fecha.")
    return frozenset(
        alg for alg, spec in tabela.items()
        if spec.get("stack") == "python" and spec.get("env") != "env_main")


#: Materializado logo APÓS `load_env_table` (que este derivador consome) — ver
#: o fim da seção de ambientes. Declarado aqui só para o leitor do vocabulário.

#: Pacotes vendorizados homônimos que a sentinela vigia (N.1.2).
OVERLAY_PACKAGES: tuple[str, ...] = ("desdeo_emo", "desdeo_problem",
                                     "desdeo_tools")

#: Raiz do overlay já importado NESTE processo, por pacote — a sentinela.
_OVERLAY_SEEN: dict[str, str] = {}


def assert_overlay_coerente() -> dict:
    """Sentinela de processo contra a colisão de overlay (N.1.2) — BARULHENTA.

    Chame DEPOIS de importar o stack do algoritmo. Registra de qual árvore cada
    `desdeo_*` veio; se um segundo run no mesmo processo trouxer um overlay de
    raiz DIFERENTE, levanta `RuntimeError` (pára-e-loga D81) em vez de deixar o
    `sys.modules` entregar silenciosamente o pacote errado.

    É a rede de segurança do `run_in_venv`: se por algum caminho dois configs
    acabarem no mesmo processo, o run MORRE em vez de mentir.
    """
    visto = {}
    for pkg in OVERLAY_PACKAGES:
        mod = sys.modules.get(pkg)
        f = getattr(mod, "__file__", None) if mod is not None else None
        if not f:
            continue
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(f)))
        visto[pkg] = raiz
        anterior = _OVERLAY_SEEN.get(pkg)
        if anterior is not None and anterior != raiz:
            raise RuntimeError(
                f"COLISÃO DE OVERLAY (N.1.2): `{pkg}` já foi importado neste "
                f"processo de {anterior!r} e agora resolve para {raiz!r}. "
                f"b5 e c311 vendorizam `desdeo_*` homônimos com código "
                f"DIFERENTE — co-importá-los usa DataProblem/RVEA ERRADOS sem "
                f"erro. Use `run_in_venv` (1 processo por run). "
                f"Pára-e-loga (D81).")
        _OVERLAY_SEEN.setdefault(pkg, raiz)
    return visto

#: Cadência ONLINE da sonda (§17.2.2 / DI-09): 1ª iteração e depois a cada k=2.
SONDA_K = 2

#: Lote de predição da sonda — custo, nunca valor (os 2000 pontos são
#: independentes; nenhum modelo desta rodada acopla linhas na predição).
SONDA_CHUNK = 512

#: Cache por processo do artefato da sonda (imutável; o hash é conferido no 1º
#: carregamento — re-hashear 2000×D floats por bloco seria puro desperdício).
_SONDA_CACHE: dict[str, dict] = {}


# ═══════════════════════════════════════════════════════════════════════════
#  Pinning e ambiente (D79 / N.1.1 / N.2)
# ═══════════════════════════════════════════════════════════════════════════

def pin_runtime() -> dict:
    """Pina o runtime numérico do processo e DEVOLVE o estado (p/ o manifesto).

    Idempotente. O torch é OPCIONAL: quando presente (c122/c149/e81), aplica
    `set_num_threads(1)` + float64 default + CPU, conforme N.1.1 — "nenhum repo
    o faz, e vários abrem `device='cuda'` SEM índice". Quando ausente
    (b5/c311/piso-off), o dict registra `torch: None` e segue.

    ⚠ Honestidade (idem R2-00): o pinning AUTORITATIVO da bateria é o
    subprocess com env limpo (`run_in_venv`); em-processo pinamos o que é
    pinável e REGISTRAMOS o estado.
    """
    state: dict = {v: os.environ.get(v) for v in D79_THREAD_VARS}
    try:
        import torch
    except ImportError:
        state.update({"torch": None, "torch_num_threads": None,
                      "default_dtype": None, "device": None})
        return state
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64)
    state.update({
        "torch": torch.__version__,
        "torch_num_threads": torch.get_num_threads(),
        "default_dtype": str(torch.get_default_dtype()),
        "device": "cpu",
    })
    return state


def _host_info() -> dict:
    """[C2/BL-07] `(host, plataforma)` — a identidade da MÁQUINA no ⑤.

    `host` é o nome curto (sem domínio), a mesma convenção do
    `scripts/censo42.py`. `UA_DD_SAEA_HOST` sobrepõe, para o operador poder
    rotular a máquina com o nome do roster em vez do hostname do provedor.
    Nunca levanta: um ⑤ sem host é ruim, um run derrubado por causa dele é pior.
    """
    import platform
    import socket
    try:
        host = os.environ.get("UA_DD_SAEA_HOST") or \
            socket.gethostname().split(".")[0]
    except Exception:                        # noqa: BLE001
        host = None
    try:
        plataforma = "%s/%s" % (platform.system(), platform.machine())
    except Exception:                        # noqa: BLE001
        plataforma = None
    return {"host": host, "plataforma": plataforma}


def env_info(*, extra_mods: tuple[str, ...] = ()) -> dict:
    """Versões do stack CORRENTE para o manifesto (§17.7 / L.18).

    Diferente do `botorch_harness.env_info`, aqui nada é obrigatório: cada venv
    da R3 tem um envelope diferente (b5 = sklearn 0.21.3; c311 = GPy; e81/c149 =
    torch). Módulos ausentes entram como `None` em vez de estourar — o que
    importa é o REGISTRO fiel do que rodou. `extra_mods` deixa cada cartão
    anexar o seu (ex.: `("GPy", "desdeo_emo")`).
    """
    import platform
    info: dict = {"python": platform.python_version(),
                  "executable": sys.executable,
                  # [C2/BL-07] A MÁQUINA viaja com o dado. Até aqui ela não
                  # viajava: o ⑤ declarava versões de biblioteca e pinos de
                  # thread, e a única atribuição de máquina era a coluna
                  # `maquina_dona` do censo, DERIVADA DO ROSTER planejado — que
                  # rotula errado toda célula recuperada noutra máquina (foi o
                  # que aconteceu na s42 quando a vm3 caiu). Com a campanha
                  # alocada POR SEMENTE, as 30 repetições de um config passam a
                  # vir de máquinas diferentes de propósito: sem estes dois
                  # campos não há como DEMONSTRAR que a diluição aconteceu, nem
                  # responder "isto é o algoritmo ou a máquina?".
                  # `plataforma` importa tanto quanto o host: a divergência
                  # cross-máquina medida nasce no 1º fit do GP e é efeito de
                  # BLAS/libm — ou seja, de SO+arquitetura, não do nome do host.
                  **_host_info(),
                  "numpy": np.__version__}
    for mod in ("scipy", "pymoo", "sklearn", "torch", "gpytorch",
                "pandas", "pyarrow") + tuple(extra_mods):
        try:
            info[mod] = __import__(mod).__version__
        except Exception:  # noqa: BLE001 — ausência é informação, não erro
            info[mod] = None
    return info


def load_env_table(path: str = ENVS_JSON) -> dict:
    """Lê `claude_code_context/artifacts/envs.json` (o artefato do D79)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


#: [T6-batch] O roteamento por venv, DERIVADO do artefato (docstring completa em
#: `_derivar_venv_only`, acima). Materializado aqui porque consome
#: `load_env_table`.
VENV_ONLY_ALGS: frozenset[str] = _derivar_venv_only()


def interpreter_for_alg(alg: str, *, envs: dict | None = None) -> tuple[str, str]:
    """Resolve `(env_id, caminho_do_interpretador)` do algoritmo (D79).

    Fonte única: `envs.json` — `alg_to_env[alg].env` e depois, na ordem,
    `environments[env].mac_interpreter` ou `provisioning.envs[env].venv +
    /bin/python`. Algoritmo/env desconhecido ⇒ KeyError; interpretador
    inexistente NÃO é erro aqui (quem resolve é `run_in_venv`, que dá a
    mensagem acionável) — esta função é pura resolução de nome.
    """
    envs = envs or load_env_table()
    try:
        env_id = envs["alg_to_env"][alg]["env"]
    except KeyError as exc:
        raise KeyError(
            f"algoritmo {alg!r} não está em envs.json:alg_to_env "
            f"(D79). Conhecidos: {sorted(envs['alg_to_env'])}") from exc
    spec = envs.get("environments", {}).get(env_id, {})
    declarados = [spec.get("mac_interpreter")]
    venv = envs.get("provisioning", {}).get("envs", {}).get(
        env_id, {}).get("venv")
    if venv:
        declarados.append(os.path.join(venv, "bin", "python"))
    candidatos = [c for c in declarados if c]
    # [C1] O caminho declarado no artefato é ABSOLUTO e de macOS
    # (`/Users/gmello/...`): em qualquer VM Linux ele não existe, e o
    # `run_in_venv` pára-e-loga. Enquanto TODO config de venv próprio rodava só
    # no Mac isso nunca apareceu ("mac: TODO o venv-próprio — únicos venvs do
    # projeto", perfil do lote3s.sh). Com a campanha alocada POR SEMENTE, cada
    # máquina passa a rodar TODOS os pares, e o caminho fixo vira bloqueador.
    #
    # A resolução agora é por CANDIDATOS, na mesma doutrina que o driver já usa
    # para achar repo/python/MATLAB: (1) override explícito do operador,
    # (2) o que o artefato declara, (3) os prefixos conhecidos, pelo NOME do
    # venv — que é a identidade estável (o gate G-3 já compara pelo nome, não
    # pelo caminho: "o mesmo venv vive em /Users/... no Mac e em
    # /home/jupyter/... na VM"). O primeiro que EXISTIR ganha; se nenhum
    # existir, devolve o declarado para o `run_in_venv` dar a mensagem
    # acionável (esta função é resolução de nome, não validação).
    nome_venv = os.path.basename(os.path.dirname(os.path.dirname(candidatos[0]))) \
        if candidatos else None
    override = os.environ.get("UA_DD_SAEA_VENVS")
    prefixos = ([override] if override else []) + [
        os.path.expanduser("~/python_venvs"),
        os.path.expanduser("~/venvs"),
        os.path.expanduser("~/Documents/python_venvs"),
        "/home/jupyter/python_venvs",
    ]
    if nome_venv:
        candidatos += [os.path.join(p, nome_venv, "bin", "python")
                       for p in prefixos]
    if not candidatos:
        raise KeyError(
            f"env {env_id!r} (alg {alg!r}) não declara interpretador em "
            f"envs.json (nem `mac_interpreter` nem `provisioning.envs.venv`).")
    for c in candidatos:
        if os.path.exists(c):
            return env_id, c
    return env_id, candidatos[0]


def child_env(*, env_id: str | None = None,
              envs: dict | None = None,
              base: dict | None = None) -> dict:
    """Monta o `env` do processo FILHO: pin D79 + flags do ambiente (N.2).

    O pin vai no filho porque é lá que o `import numpy/torch` acontece — é o
    ponto em que as libs de BLAS leem as variáveis. Herdamos o env do pai
    (PATH/HOME são necessários) e sobrescrevemos o que é nosso; `env_flags` do
    `envs.json` (ex.: `MPLBACKEND=Agg` do c311, que sem isso tenta abrir uma
    janela num nó headless) entram aqui.
    """
    out = dict(base if base is not None else os.environ)
    # [DI-27] Scrub de TODO PYTHON* herdado: um PYTHONPATH do pai poderia
    # sombrear o overlay `desdeo_*` de outro venv (N.1.2). O scrub explícito
    # substitui o antigo `-I` do lançamento — com `-s` o filho volta a HONRAR
    # env vars, e o PYTHONHASHSEED=0 abaixo passa a valer de fato (com `-I`,
    # que implica `-E`, ele era ignorado silenciosamente).
    for k in [k for k in out if k.startswith("PYTHON")]:
        del out[k]
    for v in D79_THREAD_VARS:
        out[v] = "1"
    out["PYTHONHASHSEED"] = "0"          # reprodutibilidade de iteração de set
    if env_id:
        envs = envs or load_env_table()
        for flag in envs.get("environments", {}).get(
                env_id, {}).get("env_flags", []) or []:
            k, _, v = str(flag).partition("=")
            out[k] = v
    return out


#: Sentinelas do protocolo pai↔filho. O stdout do filho é território dos
#: drivers dos autores (b5/c311 imprimem à vontade) — o resultado viaja entre
#: marcas para não se confundir com esse ruído.
_RESULT_BEGIN = "@@R3_RESULT_BEGIN@@"
_RESULT_END = "@@R3_RESULT_END@@"

#: Bootstrap do filho. Roda ANTES de qualquer import pesado: entra no repo,
#: chama o despacho canônico e emite o resultado entre as sentinelas.
_CHILD_BOOTSTRAP = r"""
import json, os, sys, traceback
sys.path.insert(0, {root!r})
os.chdir({root!r})
payload = json.loads({payload!r})
try:
    from src import experiment
    res = experiment.run(payload["alg"], payload["problema"],
                         payload["semente"], exp=payload["exp"],
                         _in_child=True, **payload.get("kwargs", {{}}))
    if not isinstance(res, dict):
        res = {{"retorno": repr(res)}}
    out = {{"ok": True, "result": {{k: v for k, v in res.items()
                                   if isinstance(v, (str, int, float, bool,
                                                     type(None)))}}}}
    # ÂNCORA VINDA DE DENTRO DO FILHO. Sem isto o probe do gate seria
    # tautológico: ele afirmaria "pin D79 no FILHO" conferindo só que o
    # processo terminou. Lidas DEPOIS dos imports — é quando valem.
    out["result"]["pin_filho"] = ",".join(
        "%s=%s" % (v, os.environ.get(v)) for v in
        ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
         "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"))
    out["result"]["executavel_filho"] = sys.executable
    out["result"]["isolated_filho"] = bool(sys.flags.isolated)
except BaseException:
    out = {{"ok": False, "traceback": traceback.format_exc()}}
sys.stdout.write("\n{begin}\n" + json.dumps(out) + "\n{end}\n")
sys.stdout.flush()
sys.exit(0 if out["ok"] else 1)
"""


def run_in_venv(alg: str, problema: str, semente, *, exp: str = "off",
                data_root: str = naming.DEFAULT_DATA_ROOT,
                envs: dict | None = None,
                interpreter: str | None = None,
                timeout: float | None = None,
                extra_kwargs: dict | None = None,
                capture_output: bool = True) -> dict:
    """Executa UM run no venv PRÓPRIO do algoritmo, em subprocesso (D79 / N.2).

    **É o mecanismo que torna b5 × c311 seguros.** Os dois vendorizam
    `desdeo_*` com o mesmo nome e código diferente; num processo compartilhado
    o `sys.modules` entrega o pacote errado SEM ERRO. Um processo por run
    elimina a classe inteira de bug — e de quebra dá o pin D79 verdadeiro
    (env limpo no filho) e isola crashes dos drivers dos autores.

    O filho chama `src.experiment.run(...)` — o MESMO ponto de entrada do
    processo local, então não há um segundo caminho de código para auditar.

    Retorna `{ok, returncode, result|traceback, interpreter, env_id, cmd,
    stdout, stderr}`. **Não levanta** em run falho: quem decide é o chamador
    (o despachante aplica o retry D23). Levanta em erro de CONFIGURAÇÃO
    (interpretador ausente) — isso é pára-e-loga, não falha de run.
    """
    envs = envs or load_env_table()
    # O `env_id` é resolvido pelo ALG SEMPRE — `interpreter=` sobrescreve só o
    # caminho do binário, nunca a IDENTIDADE do ambiente. Sem isto, passar um
    # interpretador explícito descartava os `env_flags` do `envs.json` (ex.:
    # `MPLBACKEND=Agg` do c311, sem o qual ele tenta abrir janela em nó
    # headless) e gravava `env_id=None` no retorno/manifesto.
    try:
        env_id, interp_padrao = interpreter_for_alg(alg, envs=envs)
    except KeyError:
        env_id, interp_padrao = None, None   # tokens fora do grid (ex.: stub)
    interp = interpreter or interp_padrao
    if interp is None:
        raise KeyError(
            f"algoritmo {alg!r} não está em envs.json:alg_to_env e nenhum "
            f"`interpreter=` foi passado (D79).")
    if not os.path.exists(interp):
        raise FileNotFoundError(
            f"interpretador do env {env_id!r} (alg {alg!r}) não existe: "
            f"{interp}. Provisione o venv (requirements/) ou passe "
            f"`interpreter=` explicitamente. Pára-e-loga (D81).")

    payload = json.dumps({
        "alg": alg, "problema": problema, "semente": int(semente),
        "exp": exp,
        "kwargs": {"data_root": os.path.abspath(data_root),
                   **(extra_kwargs or {})},
    })
    code = _CHILD_BOOTSTRAP.format(root=ROOT, payload=payload,
                                   begin=_RESULT_BEGIN, end=_RESULT_END)
    # `-s` (sem user-site) + o scrub de PYTHON* no child_env cobrem o que o
    # antigo `-I` cobria (N.1.2: nada herdado sombreia o overlay `desdeo_*`),
    # MAS deixam o filho honrar o env controlado — em particular o
    # PYTHONHASHSEED=0, que o `-I` (⊃ `-E`) ignorava silenciosamente [DI-27].
    cmd = [interp, "-s", "-c", code]
    proc = subprocess.run(  # noqa: S603 — cmd é construído aqui, sem shell
        cmd, env=child_env(env_id=env_id, envs=envs), cwd=ROOT,
        capture_output=capture_output, text=True, timeout=timeout, check=False)

    out: dict = {"interpreter": interp, "env_id": env_id, "cmd": cmd,
                 "returncode": proc.returncode,
                 "stdout": proc.stdout, "stderr": proc.stderr}
    parsed = _parse_child_result(proc.stdout or "")
    if parsed is None:
        out.update({"ok": False, "traceback": (
            f"o filho não emitiu o bloco de resultado (returncode="
            f"{proc.returncode}). stderr:\n{(proc.stderr or '')[-4000:]}")})
        return out
    out.update(parsed)
    return out


def _parse_child_result(stdout: str) -> dict | None:
    """Extrai o JSON entre as sentinelas (o resto do stdout é ruído do autor)."""
    i = stdout.rfind(_RESULT_BEGIN)
    j = stdout.rfind(_RESULT_END)
    if i < 0 or j < 0 or j < i:
        return None
    try:
        return json.loads(stdout[i + len(_RESULT_BEGIN):j].strip())
    except json.JSONDecodeError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  Sementes (D62/D91) e guardas de RNG (N.2.3 / invariante de não-perturbação)
# ═══════════════════════════════════════════════════════════════════════════

def iteration_seed(base: int, alg_id: int, iteracao: int, uso_id: int,
                   *, bits32: bool = False) -> int:
    """`SeedSequence((base, alg_id, iteracao, uso_id))` — a fórmula do D62/D91.

    A MESMA materialização do R2-00 (há teste que a compara bit-a-bit com o
    `seeds.json`). `bits32=True` onde a API exige 32 bits — `pymoo.minimize`,
    `torch.manual_seed`, `random.seed`.

    ⚠ `base` já deve trazer o offset D22 (`1000·semente`) quando o algoritmo é
    e81 ou c149 — ver `seed_base`.
    """
    ss = np.random.SeedSequence(
        (int(base), int(alg_id), int(iteracao), int(uso_id)))
    s = int(ss.generate_state(1, dtype=np.uint64)[0])
    return s & 0xFFFFFFFF if bits32 else s


#: Configs com offset de semente `+1000·semente` (D22) — e81 e c149.
SEED_OFFSET_ALGS: frozenset[str] = frozenset({"e81", "c149"})


def seed_base(alg: str, semente: int) -> int:
    """Base de semente do algoritmo (D22): `1000·semente` p/ e81/c149, senão
    a própria semente. Centralizado para que nenhum cartão o esqueça."""
    s = int(semente)
    return 1000 * s if alg in SEED_OFFSET_ALGS else s


@contextmanager
def preserve_global_rng():
    """Salva/restaura `np.random` + `random` (N.2.3 / contrato R3 item 3).

    `pymoo.minimize(seed=·)` **re-semeia os RNGs GLOBAIS** — e81, c149 e o
    NSGA-II interno de vários passam por ele. Sem esta guarda, uma chamada
    interna desloca a trajetória de tudo o que vier depois.
    """
    np_state = np.random.get_state()
    py_state = random.getstate()
    try:
        yield
    finally:
        np.random.set_state(np_state)
        random.setstate(py_state)


@contextmanager
def preserve_all_rng():
    """`preserve_global_rng` + o RNG do torch quando ele existe.

    É a guarda do **INVARIANTE DE NÃO-PERTURBAÇÃO** (§3.1): a sonda e a
    instrumentação DI-10 não podem mover a busca. Preditores estocásticos
    (MC-dropout, Thompson) consomem RNG — sem isto, medir muda o medido.
    Prova objetiva por config: a ① do run com sonda é IDÊNTICA à do run sem.
    """
    with preserve_global_rng():
        try:
            import torch
        except ImportError:
            yield
            return
        t_state = torch.get_rng_state()
        try:
            yield
        finally:
            torch.set_rng_state(t_state)


def guarded_pymoo_minimize(*args, **kwargs):
    """`pymoo.optimize.minimize` sob `preserve_global_rng` (N.2.3).

    Use SEMPRE — nenhum cartão R3 deve chamar `minimize` cru.
    """
    from pymoo.optimize import minimize as _minimize
    with preserve_global_rng():
        return _minimize(*args, **kwargs)


def iteration_cleanup() -> None:
    """Higiene de memória por iteração (D86 / N.1.5).

    O chamador faz o `del` dos tensores/modelos da iteração e chama isto. Sem
    isso o retreino-por-FE do c149 (D43) acumula grafo ao longo de centenas de
    FEs e estoura no MEIO do run — dado perdido, e o D60 só mata o processo.
    """
    gc.collect()
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# ═══════════════════════════════════════════════════════════════════════════
#  Artefatos de entrada: DoE (online) e DATASET offline (D90)
# ═══════════════════════════════════════════════════════════════════════════

def _decoded_hash(arr: np.ndarray) -> str:
    """sha256 dos bytes float64 row-major — a convenção única do D87/D90."""
    return hashlib.sha256(
        np.ascontiguousarray(arr, dtype=np.float64).tobytes()).hexdigest()


def load_doe(problema: str, semente, *,
             data_root: str = naming.DEFAULT_DATA_ROOT) -> dict:
    """Carrega o DoE online 11D−1 do artefato (D63/D87/D88) e confere o hash.

    Para os 3 configs ONLINE da R3 (c122, c149, e81). O runner **nunca**
    regenera pontos. Ausente ⇒ FileNotFoundError; hash divergente ⇒
    RuntimeError (pára-e-loga D81).
    """
    from src import doe as _doe
    path = naming.doe_path(problema, semente, data_root=data_root)
    mpath = naming.doe_manifest_path(problema, semente, data_root=data_root)
    if not (os.path.exists(path) and os.path.exists(mpath)):
        raise FileNotFoundError(
            f"artefato do DoE ausente p/ ({problema}, {semente}): {path} "
            f"(+sidecar). O runner NUNCA regenera o DoE (D63). "
            f"Pára-e-loga (D81).")
    with open(mpath, encoding="utf-8") as fh:
        side = json.load(fh)
    X = _doe._read_matrix_parquet(path, side["columns"])
    h = _doe.decoded_hash(X)
    if h != side.get("doe_hash"):
        raise RuntimeError(
            f"DoE ({problema}, {semente}): hash do array decodificado "
            f"({h[:16]}…) diverge do sidecar ({str(side.get('doe_hash'))[:16]}…)"
            f" — artefato corrompido. Pára-e-loga (D81).")
    return {"X": X, "doe_hash": h, "sidecar": side, "path": path}


def load_dataset(problema: str, semente, *, tier: str | None = None,
                 dist: str | None = None,
                 data_root: str = naming.DEFAULT_DATA_ROOT) -> dict:
    """Carrega o DATASET OFFLINE (D90) e confere `x_hash` **E** `f_hash`.

    O análogo Python do `load_dataset` MATLAB do e103 — e o CP-init offline é
    **mais forte que o online**: o online só cobre X (o F é recalculado pelo
    run), enquanto no offline o F **vem do artefato** e é o insumo do modelo,
    então tem de ser conferido também.

    Tier `small`/`dist` `lhs` = o offline principal (§7/§9), nome SEM sufixo;
    as variantes do sweep (§11.5) trazem `_{tier}_{dist}`.

    Retorna `{X, F, n, D, M, x_hash, f_hash, dataset_hash, sidecar, path}`
    (X/F float64, na ORDEM do artefato — que a ① preserva).
    """
    from src import doe as _doe
    path = naming.dataset_path(problema, semente, tier, dist,
                               data_root=data_root)
    mpath = naming.dataset_manifest_path(problema, semente, tier, dist,
                                         data_root=data_root)
    if not (os.path.exists(path) and os.path.exists(mpath)):
        raise FileNotFoundError(
            f"dataset OFFLINE ausente p/ ({problema}, {semente}, "
            f"{tier or 'small'}/{dist or 'lhs'}): {path} (+sidecar). No regime "
            f"offline o dataset É o orçamento (D90) — nenhum config o gera. "
            f"Pára-e-loga (D81).")
    with open(mpath, encoding="utf-8") as fh:
        side = json.load(fh)
    D, M = int(side["D"]), int(side["M"])
    XF = _doe._read_matrix_parquet(path, side["columns"])
    X = np.ascontiguousarray(XF[:, :D], dtype=np.float64)
    F = np.ascontiguousarray(XF[:, D:D + M], dtype=np.float64)
    xh, fh_ = _decoded_hash(X), _decoded_hash(F)
    if xh != side.get("x_hash") or fh_ != side.get("f_hash"):
        raise RuntimeError(
            f"dataset ({problema}, {semente}): CP-init OFFLINE FALHOU — "
            f"x_hash {xh[:16]}… vs {str(side.get('x_hash'))[:16]}… ; "
            f"f_hash {fh_[:16]}… vs {str(side.get('f_hash'))[:16]}… . "
            f"Pára-e-loga (D81).")
    return {"X": X, "F": F, "n": int(X.shape[0]), "D": D, "M": M,
            "x_hash": xh, "f_hash": fh_,
            "dataset_hash": side.get("dataset_hash"),
            "sidecar": side, "path": path}


# ═══════════════════════════════════════════════════════════════════════════
#  Regime OFFLINE — "o orçamento É o dataset" (o molde provado pelo e103)
# ═══════════════════════════════════════════════════════════════════════════

class OfflineBudgetViolation(RuntimeError):
    """Uma avaliação REAL foi pedida durante a busca de um run OFFLINE.

    No offline **não existe** avaliação real durante a busca: o §11 dá UMA
    única chamada real, no ND final, pós-hoc e fora do orçamento (DI-08). Se o
    caminho do algoritmo pedir um FE com X inédita, o desenho está errado — e
    isso NÃO pode ser engolido como "orçamento esgotado" (que é o término
    NORMAL do online, D61). Daí uma exceção própria: o run pára e loga.
    """


def load_offline_budget(problema: str, semente, *,
                        tier: str | None = None, dist: str | None = None,
                        data_root: str = naming.DEFAULT_DATA_ROOT,
                        logger=None) -> tuple[_budget.FEBudget, dict]:
    """Monta o `FEBudget` do regime OFFLINE a partir do dataset (D90).

    O molde do e103, item por item:
      1. `FEBudget(D, maxfe=n, n_init=n)` com `n = len(dataset)` (= 31D−1 no
         principal) — o orçamento **é** o dataset;
      2. as `n` linhas entram uma a uma na carga, fase `init`, com o `F` VINDO
         DO ARTEFATO (a ponte nunca avalia — o F canônico do `problems.py` já
         está congelado no ds);
      3. após a carga o saldo está **ESGOTADO** — logo qualquer `evaluate` com
         X inédita na busca levanta `BudgetExhausted`, que o runner converte em
         `OfflineBudgetViolation`.

    Pré-checagens pára-e-loga (as do e103): `unique(X)` == n (duplicata quebra
    o ajuste de Kriging/GP) e shapes coerentes com o sidecar.

    Retorna `(bud, ds)`.
    """
    ds = load_dataset(problema, semente, tier=tier, dist=dist,
                      data_root=data_root)
    X, F, n = ds["X"], ds["F"], ds["n"]
    if np.unique(X, axis=0).shape[0] != n:
        raise RuntimeError(
            f"dataset ({problema}, {semente}): {n} linhas mas "
            f"{np.unique(X, axis=0).shape[0]} X únicas — duplicata no dataset "
            f"offline quebra o ajuste do surrogate (hazard L.15). "
            f"Pára-e-loga (D81).")
    bud = _budget.FEBudget(D=ds["D"], maxfe=n, n_init=n, logger=logger)
    for i in range(n):
        # `true_f` é um callable que devolve a linha do ARTEFATO — a ponte
        # nunca avalia nada (o F canônico do `problems.py` já está congelado
        # no ds, D90). O `_row` fecha sobre `i` por default-arg de propósito:
        # ligar a variável do laço tarde daria a ÚLTIMA linha a todas as FEs.
        bud.evaluate(X[i], lambda _x, _f=F[i]: _f)
    if not bud.exhausted:                       # `exhausted` é property (D61)
        raise RuntimeError(
            f"carga do dataset offline não esgotou o orçamento "
            f"(fe={bud.fe} de {bud.maxfe}) — o invariante 'o orçamento É o "
            f"dataset' (D90) foi violado. Pára-e-loga (D81).")
    # [BL-04] A CARGA não é avaliação. O laço acima passa pelo portão só para
    # atribuir `solution_id` (D57) e esgotar o orçamento (D90) — o `f` já está
    # congelado no parquet e o `true_f` apenas devolve a linha. Sem descartar o
    # cronômetro, o `tempo_aval_real_s` do ⑤ dos 5 offline publicaria o tempo de
    # INGESTÃO no lugar do custo de avaliar (medido: 0,0003 s no b5m/DTLZ2).
    # No regime offline a resposta honesta é NULL: não há avaliação real a medir.
    bud.descarta_cronometro_de_aval()
    return bud, ds


@contextmanager
def offline_guard(log=None, *, alg: str = "?", problema: str = "?"):
    """Converte um FE-na-busca em `OfflineBudgetViolation` **logado**.

    Embrulhe o laço de busca dos configs offline com isto. O `BudgetExhausted`
    que chega aqui não é término natural (o saldo já nasceu zerado): é a prova
    de que algo no caminho do algoritmo tentou avaliar de verdade.
    """
    try:
        yield
    except _budget.BudgetExhausted as exc:
        msg = (f"VIOLAÇÃO DE REGIME OFFLINE em {alg}/{problema}: o algoritmo "
               f"pediu uma avaliação REAL durante a busca. No offline o "
               f"orçamento É o dataset (D90) e a única chamada real é o ND "
               f"final, pós-hoc (§11/DI-08). Pára-e-loga (D81).")
        if log is not None:
            log.guard("violacao_regime_offline", detalhe=msg)
            log.footer(status="failed", motivo="violacao_regime_offline")
        raise OfflineBudgetViolation(msg) from exc


# ═══════════════════════════════════════════════════════════════════════════
#  SONDA canônica (§17.2.2 / DI-09) — a régua fixa de 2000 pontos
# ═══════════════════════════════════════════════════════════════════════════

def clear_sonda_cache() -> None:
    """Esvazia o cache de sonda por processo. [DI-13.5] A chave é
    `(problema, regime, data_root)` — o `data_root` FALTAVA (bug latente: um
    load de outra pasta devolvia o artefato cacheado, mascarando adulteração).
    Testes usam ESTA função em vez de mexer no dict interno."""
    _SONDA_CACHE.clear()


def load_sonda(problema: str, *,
               regime: str = 'online',
               data_root: str = naming.DEFAULT_DATA_ROOT) -> dict:
    """Carrega `data/sonda/sonda_{problema}.parquet` e confere os hashes.

    Gêmeo torch-livre de `botorch_harness.load_sonda` (a R3 roda em venvs sem
    torch, e aquele módulo faz `import torch` no topo). Mesma convenção, mesmos
    hashes, mesma ordem — há um teste de EQUIVALÊNCIA entre os dois em
    `tests/test_r3_harness.py` que falha se as implementações divergirem.

    A ORDEM DAS LINHAS é a ordem Sobol do artefato e é o que o writer da ③ tem
    de preservar: o gabarito (`F`) casa com o bloco POR POSIÇÃO (§3.1 / R4
    regra 5). Nenhum algoritmo GERA pontos de sonda — todos CARREGAM.

    [D102.10] `problema in experiment.PROBLEMAS_SEM_SONDA` ⇒ devolve **None**
    (ausência declarada e legítima POR PROBLEMA — o runner desarma a sonda e o
    ⑤ declara `sem_sonda_por_problema`; espelho do `sd=[]` do MATLAB).
    """
    from src.experiment import PROBLEMAS_SEM_SONDA  # leve/lazy (sem ciclo)
    if problema in PROBLEMAS_SEM_SONDA:
        return None
    _ck = (problema, regime, os.path.abspath(data_root))
    if _ck in _SONDA_CACHE:
        return _SONDA_CACHE[_ck]
    base = os.path.join(data_root, "sonda", f"sonda_{problema}")
    path, mpath = base + ".parquet", base + ".manifest.json"
    if not (os.path.exists(path) and os.path.exists(mpath)):
        raise FileNotFoundError(
            f"artefato da SONDA ausente p/ {problema}: {path} (+sidecar). O "
            f"runner NUNCA gera pontos de sonda (§17.2.2) — materialize antes "
            f"com scripts/gen_sonda.py. Pára-e-loga (D81).")
    with open(mpath, encoding="utf-8") as fh:
        side = json.load(fh)
    import pyarrow.parquet as pq
    tbl = pq.read_table(path)
    D, M, S = int(side["D"]), int(side["M"]), int(side["S"])
    X = np.column_stack([np.asarray(tbl.column(f"x{j}"), dtype=np.float64)
                         for j in range(D)])
    F = np.column_stack([np.asarray(tbl.column(f"f{j}"), dtype=np.float64)
                         for j in range(M)])
    if X.shape != (S, D) or F.shape != (S, M):
        raise RuntimeError(
            f"SONDA {problema}: shapes {X.shape}/{F.shape} != "
            f"({S},{D})/({S},{M}) do sidecar. Pára-e-loga (D81).")
    xh, fh_ = _decoded_hash(X), _decoded_hash(F)
    if xh != side.get("x_hash") or fh_ != side.get("f_hash"):
        raise RuntimeError(
            f"SONDA {problema}: hash do array decodificado diverge do sidecar "
            f"(x {xh[:16]}… vs {str(side.get('x_hash'))[:16]}…) — artefato "
            f"corrompido. Pára-e-loga (D81).")
    # ── [DI-13.5] fatia por REGIME (gêmeo do botorch_harness) ──────────────────
    # Artefato S=20.000: ONLINE lê as PRIMEIRAS S_online (2.000) a cada k=2
    # gerações; OFFLINE lê TODAS (modelo treina 1× ⇒ cabe mais ponto). Sobol é
    # ANINHADO ⇒ a fatia online é BIT-IDÊNTICA à sonda de 2.000 (test_di13).
    if regime == 'online':
        n_on = int(side.get('S_online', 2000))
        X, F = X[:n_on], F[:n_on]
        xh_on = _decoded_hash(X)
        if side.get('x_hash_online') and xh_on != side['x_hash_online']:
            raise RuntimeError(f'SONDA {problema}: fatia ONLINE diverge do sidecar (D81).')
        fh_on = _decoded_hash(F)
        # [DI-24/achado §8.7 do e81] o f_hash_online tambem se confere — antes
        # era recalculado e NUNCA comparado (ia nao-auditado ao manifesto).
        if side.get('f_hash_online') and fh_on != side['f_hash_online']:
            raise RuntimeError(f'SONDA {problema}: f da fatia ONLINE diverge do sidecar (D81).')
        xh, fh_, S = xh_on, fh_on, n_on

    art = {"X": X, "F": F, "S": S, "D": D, "M": M,
           "x_hash": xh, "f_hash": fh_, "path": path, "sidecar": side}
    _SONDA_CACHE[_ck] = art
    return art


def sonda_due(it: int, *, k: int = SONDA_K) -> bool:
    """Cadência ONLINE (§17.2.2): a 1ª iteração e depois a cada `k`.

    A ÚLTIMA também é obrigatória, mas só se sabe qual é quando o hard-stop
    chega — o runner cobre isso emitindo o bloco no ramo `BudgetExhausted` se a
    iteração corrente ainda não tiver emitido. **No OFFLINE não se usa esta
    função**: lá a cadência é `1× por modelo treinado` (o modelo não muda).

    ✅ **CANÔNICA — DI-12.5 (autor, 2026-07-19).** Houve divergência entre os
    stacks (MATLAB fazia `g==1 || mod(g-1,k)==0` → 1,3,5,7,…), escalada por D81
    em `652e24d`; o autor **cravou esta fórmula** (`1,2,4,6,…`) e o MATLAB foi
    alinhado a ela (`a5f6eab`). Razão decisiva registrada na decisão: a sonda é
    "a régua ÚNICA, idêntica para todos" — uma cadência que muda por STACK
    contradiz a própria definição.

    Alcance na R3: só os 3 configs ONLINE (c122, c149, e81) usam esta função.
    Os 4 offline (b5r/b5m/c311/piso-off) são IMUNES — lá a cadência é 1× por
    modelo treinado e não depende de `k`.
    """
    it = int(it)
    return it == 1 or it % int(k) == 0


def emit_sonda_block(buf: "SnapshotBuffer", log, *, geracao: int, fe: int,
                     sonda: dict, predict, fe_treino_max: int | None,
                     modelo_flag: str = "surrogate",
                     pred_tipo: str = "valor",
                     motivo: str = "cadencia k=2",
                     c3: dict | None = None,
                     meta: dict | None = None,
                     chunk: int = SONDA_CHUNK) -> float:
    """Emite UM bloco de sonda: S linhas na ③ com `regime='sonda'`, na ORDEM
    do artefato, + o evento `sonda` no `.jsonl`. Retorna `tempo_pred_sonda_s`.

    `predict(X) -> (mu, sigma)` é o gancho do cartão: recebe um lote (n, D) em
    espaço NATIVO e devolve μ **em f de minimização** (o sinal do motor nunca
    vaza para o export) e σ (ou `None` se o modelo não tem incerteza — RBF
    puro). É chamado sob `preserve_all_rng()`: a sonda **não pode** mover a
    busca (invariante de não-perturbação, §3.1).

    `meta` = metadados do CONFIG para o evento `sonda` (ex.: o `n_ref` REAL da
    referência do c122 — I-01). Vai só ao ⑥; não toca a ③ nem a predição.

    Custo de FE: **ZERO** — o `f` verdadeiro já está no artefato; a exceção
    contábil é documentada (precedente do `__final`, DI-08). Este bloco não
    toca o `FEBudget`.

    **Classificadores e scores** (o c122 da R3 é score par-a-par; b4/c217 no
    R1): passe `pred_tipo='classe'` ou `'score'`. Aí o `predict` devolve
    `(valor, confianca)` 1-D com S entradas — `valor` é a classe (string) ou o
    score (float) —, e as linhas vão para `pred_classe`/`pred_score` +
    `pred_confianca`, NUNCA para `mu_*`/`sigma_*` (que significam outra coisa
    e envenenariam a leitura da ③ pela R4).
    """
    if pred_tipo not in _export.PRED_TIPOS:
        raise ValueError(
            f"pred_tipo inválido p/ a sonda: {pred_tipo!r} "
            f"(esperado {_export.PRED_TIPOS}).")
    t0 = time.time()
    X = sonda["X"]
    escalar = pred_tipo in ("classe", "score")

    partes_a, partes_b = [], []
    with preserve_all_rng():
        for i in range(0, X.shape[0], int(chunk)):
            a_i, b_i = predict(X[i:i + int(chunk)])
            partes_a.append(np.asarray(a_i, dtype=object if pred_tipo ==
                                       "classe" else np.float64).reshape(-1)
                            if escalar
                            else np.asarray(a_i, dtype=np.float64))
            partes_b.append(
                None if b_i is None
                else (np.asarray(b_i, dtype=np.float64).reshape(-1) if escalar
                      else np.asarray(b_i, dtype=np.float64)))
    # `concatenate` no caminho escalar (1-D) e `vstack` no vetorial (n, M): o
    # `vstack` de chunks 1-D os empilharia como LINHAS e estouraria.
    junta = np.concatenate if escalar else np.vstack
    A = junta(partes_a)
    B = None if partes_b[0] is None else junta(partes_b)
    if A.shape[0] != X.shape[0]:
        raise RuntimeError(
            f"sonda: `predict` devolveu {A.shape[0]} valores p/ "
            f"{X.shape[0]} pontos — a ORDEM/cardinalidade do artefato tem de "
            f"ser preservada (join posicional, R4 regra 5). Pára-e-loga (D81).")

    for i in range(X.shape[0]):
        if pred_tipo == "classe":
            extra = {"pred_classe": (None if A[i] is None else str(A[i])),
                     "pred_confianca": (None if B is None else float(B[i]))}
        elif pred_tipo == "score":
            extra = {"pred_score": float(A[i]),
                     "pred_confianca": (None if B is None else float(B[i]))}
        else:                                     # 'valor' / 'híbrido'
            extra = {"mu": A[i], "sigma": (None if B is None else B[i])}
        # [DI-23/achado §3.4 do c149] `c3` = as colunas DEF-C3 (espaco_modelo/
        # transf_tipo/transf_params) pertencem a TODA linha quando o modelo
        # opera em espaço transformado — o c149 precisou de um carimbo pós-hoc
        # (_stamp_c3_sonda) porque este helper não as aceitava; agora aceita.
        buf.add_surrogate(_export.surrogate_row(
            int(geracao), X[i], regime="sonda", real_solution_id=None,
            pred_tipo=pred_tipo, modelo_flag=modelo_flag,
            fe_treino_max=fe_treino_max, **(c3 or {}), **extra))
    dt = time.time() - t0
    log.event("sonda", geracao=int(geracao), fe=int(fe),
              n_pontos=int(X.shape[0]), tempo_pred_sonda_s=round(dt, 4),
              fe_treino_max=(None if fe_treino_max is None
                             else int(fe_treino_max)),
              sonda_x_hash=sonda["x_hash"], sonda_f_hash=sonda["f_hash"],
              hash_check="ok (conferido no arranque — load_sonda)",
              modelo_flag=modelo_flag, motivo=motivo, **(meta or {}))
    return dt


# ═══════════════════════════════════════════════════════════════════════════
#  [A11/I-6/D11] SONDA ESTRATIFICADA — só para os 4 CLASSIFICADORES
# ═══════════════════════════════════════════════════════════════════════════

#: Nº de pontos do bloco estratificado (o plano pede "~500").
SONDA_ESTRAT_N = 500
#: Amplitude da perturbação, como fração do range de cada dimensão.
SONDA_ESTRAT_SIGMA_REL = 0.05
#: `uso_id` do RNG do bloco (catálogo D62/D91) — nunca colide com a busca.
SONDA_ESTRAT_USO = 91


def _problems_nds(F):
    """Índices do ND de F (import local: `problems` é pesado e só serve aqui)."""
    from src import problems as _p
    return _p._nds_filter(F)


def amostra_estratificada(arquivo_X, xl, xu, *, n=SONDA_ESTRAT_N,
                          sigma_rel=SONDA_ESTRAT_SIGMA_REL, semente_bloco=0):
    """`n` pontos amostrados PERTO do arquivo corrente, clipados aos bounds.

    **Por que existe [I-6/D11].** Pontos Sobol aleatórios quase nunca são "bons":
    a prevalência medida da classe positiva é **0,4%**, ou seja **~8 positivos por
    bloco de 2.000**. Com 8 positivos, precision/recall/F1 têm variância enorme e
    só o AUC é estável — a régua Sobol responde "o modelo é bom GLOBALMENTE?",
    não "ele acerta ONDE a decisão acontece?". Subir para 3.000 pontos NÃO
    resolve (a prevalência não muda, só o n): **a estratificação é o que resolve**.

    **O que NÃO se faz:** misturar com a régua. Os 2.000 Sobol continuam intactos
    e comparáveis entre TODOS os algoritmos; este bloco vai com
    `regime='sonda_estratificada'` e NUNCA entra na mesma análise — cada
    algoritmo tem um arquivo diferente, então o bloco não é comparável ENTRE
    configs (é a ressalva que o autor ratificou ao escolher a opção (b)).

    Determinismo: `numpy.random.default_rng(semente_bloco)` LOCAL — não toca o
    RNG global (o chamador ainda o envolve em `preserve_all_rng`, cinto e
    suspensório).
    """
    A = np.atleast_2d(np.asarray(arquivo_X, dtype=np.float64))
    xl = np.asarray(xl, dtype=np.float64).ravel()
    xu = np.asarray(xu, dtype=np.float64).ravel()
    if A.size == 0:
        return np.empty((0, xl.size), dtype=np.float64)
    rng = np.random.default_rng(int(semente_bloco))
    base = A[rng.integers(0, A.shape[0], size=int(n))]
    ruido = rng.normal(0.0, sigma_rel * (xu - xl), size=(int(n), xl.size))
    return np.clip(base + ruido, xl, xu)


def emit_sonda_estratificada(buf, log, *, geracao, fe, arquivo_X, xl, xu,
                             predict, true_f, fe_treino_max,
                             pred_tipo="score", modelo_flag="classificador",
                             n=SONDA_ESTRAT_N, semente_bloco=0,
                             meta=None) -> float:
    """Emite UM bloco `regime='sonda_estratificada'` na ③ + o evento no ⑥.

    O `f` VERDADEIRO destes pontos não está em artefato nenhum (eles dependem do
    arquivo corrente), então é avaliado AQUI, **fora do orçamento** — mesma
    exceção contábil da sonda Sobol (§17.2.2/DI-08): funções analíticas, custo de
    FE **ZERO**, e o `FEBudget` nem é tocado. É por isso que `true_f` entra por
    parâmetro em vez de sair do `bud`: quem chama declara que está fora do
    orçamento.

    Tudo sob `preserve_all_rng()` — a amostragem E a predição consomem RNG, e
    este bloco é INSTRUMENTO: mover a busca aqui invalidaria o run inteiro (o
    gate G-6 prova que não move).
    """
    t0 = time.time()
    with preserve_all_rng():
        X = amostra_estratificada(arquivo_X, xl, xu, n=n,
                                  semente_bloco=semente_bloco)
        if X.shape[0] == 0:
            return 0.0
        a, b = predict(X)
        for i in range(X.shape[0]):
            # [BL-03] RAMIFICA por `pred_tipo`, como a irmã `emit_sonda_block`
            # (:846-854) e como a docstring dela EXIGE: score/classe vão para
            # `pred_score`/`pred_classe` + `pred_confianca`, "NUNCA para
            # mu_*/sigma_*, que significam outra coisa e envenenariam a leitura
            # da ③ pela R4". Sem a ramificação, o `pred_tipo` default deste
            # emissor ('score' — o c122 é classificador par-a-par) gravava o
            # e(z) em `mu_0` e a confiança em `sigma_0`, com `pred_score` NULL:
            # 10.500/10.500 linhas. O guard do writer (export.py:468-478) não
            # pega, porque `len(mu)=1 < M=2` é o caso legítimo do b1
            # mono-output.
            if pred_tipo == "classe":
                extra = {"pred_classe": (None if a[i] is None else str(a[i])),
                         "pred_confianca": (None if b is None else float(b[i]))}
            elif pred_tipo == "score":
                extra = {"pred_score": float(a[i]),
                         "pred_confianca": (None if b is None else float(b[i]))}
            else:                                 # 'valor' / 'hibrido'
                extra = {"mu": (None if a is None else a[i]),
                         "sigma": (None if b is None else b[i])}
            buf.add_surrogate(_export.surrogate_row(
                (None if geracao is None else int(geracao)), X[i],
                regime="sonda_estratificada", real_solution_id=None,
                pred_tipo=pred_tipo, modelo_flag=modelo_flag,
                fe_treino_max=fe_treino_max, **extra))
        # ⚠ O `f` VERDADEIRO NÃO vai à ③: o schema dela é contrato (§3) e
        # mudá-lo custaria re-run de tudo por ZERO informação nova — os
        # problemas são ANALÍTICOS e determinísticos, então a análise recompõe
        # `problems.evaluate_problem(prob, X)` a partir do X gravado, EXATO. É a
        # mesma doutrina do I-12 (informação recuperável por regra de leitura) e
        # do que o plano recusa para o α do c154/c262.
        # O que vai ao ⑥ é o AGREGADO que justifica o bloco existir: a
        # prevalência da classe positiva. Na régua Sobol ela é 0,4% (~8
        # positivos em 2.000) e é por isso que precision/recall/F1 são instáveis.
        prevalencia = None
        if true_f is not None:
            try:
                F = np.atleast_2d(np.asarray(true_f(X), dtype=np.float64))
                idx = set(int(i) for i in _problems_nds(F))
                prevalencia = len(idx) / float(F.shape[0])
            except Exception:                # noqa: BLE001 — nunca derruba
                prevalencia = None
    dt = time.time() - t0
    log.event("sonda_estratificada", geracao=(None if geracao is None
                                              else int(geracao)),
              fe=int(fe), n_pontos=int(X.shape[0]),
              tempo_pred_s=round(dt, 4), fe_treino_max=fe_treino_max,
              sigma_rel=SONDA_ESTRAT_SIGMA_REL, semente_bloco=int(semente_bloco),
              n_arquivo=int(np.atleast_2d(arquivo_X).shape[0]),
              prevalencia_nd_no_bloco=prevalencia,
              modelo_flag=modelo_flag,
              nota=("bloco NAO-comparavel entre algoritmos (cada um tem um "
                    "arquivo diferente) — NUNCA misturar com regime='sonda'"),
              **(meta or {}))
    return dt


# ═══════════════════════════════════════════════════════════════════════════
#  Mínimo comum do `.jsonl` (DI-10) — o que TODO `<alg>_gen` carrega
# ═══════════════════════════════════════════════════════════════════════════

def minimo_comum_di10(F_pop, *, fe: int, modelo_hp=None,
                      tempo_fit_s: float | None = None,
                      tempo_busca_s: float | None = None,
                      dist_min_arquivo: float | None = None) -> dict:
    """Monta o **mínimo comum DI-10** de um evento `<alg>_gen` (CONTRATO §6).

    Campos: `fe`, `f_best[]` (melhor por objetivo), `n_front1` (tamanho do ND
    corrente), `modelo_hp`, `tempo_fit_s`/`tempo_busca_s`, `dist_min_arquivo`.

    ⚠ Armadilha herdada do retrofit R2 (definição M-6/A-8): `problems._nds_filter`
    devolve **ÍNDICES**, não máscara booleana — `count_nonzero` descartaria
    silenciosamente o índice 0. Aqui usamos `len(...)`, e há teste para isso.

    Roda sob `preserve_all_rng()` por segurança: nenhum cálculo aqui é
    estocástico hoje, mas o invariante de não-perturbação vale para TODA a
    instrumentação, e um `modelo_hp` que faça um forward não pode mover o RNG.
    """
    with preserve_all_rng():
        F = np.asarray(F_pop, dtype=np.float64)
        if F.ndim == 1:
            F = F.reshape(1, -1)
        from src import problems as _problems
        idx = _problems._nds_filter(F)
        out = {
            "fe": int(fe),
            "f_best": [float(v) for v in F.min(axis=0)],
            "n_front1": int(len(idx)),       # len, NUNCA count_nonzero (A-8)
        }
    if modelo_hp is not None:
        out["modelo_hp"] = modelo_hp
    if tempo_fit_s is not None:
        out["tempo_fit_s"] = round(float(tempo_fit_s), 6)
    if tempo_busca_s is not None:
        out["tempo_busca_s"] = round(float(tempo_busca_s), 6)
    if dist_min_arquivo is not None:
        out["dist_min_arquivo"] = float(dist_min_arquivo)
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  Buffer das camadas ②③④ (v5.2.1 desde o nascimento)
# ═══════════════════════════════════════════════════════════════════════════

class SnapshotBuffer:
    """Coletor de ② (membership) + ③ (predições) + ④ (timing) por geração.

    Mesma API do buffer do R2-00 — de propósito: um cartão que migre de rodada
    não reaprende nada. As diferenças são de contrato, não de forma: aqui
    `add_timing` já nasce aceitando os 3 tempos da v5.2.1, e `tempo_fit_s`
    aceita `None` (o **piso** offline não treina surrogate — CONTRATO §4:
    "Pisos: ④ por geração com `tempo_geracao_s` (fit=NULL)").
    """

    def __init__(self) -> None:
        self.pop_rows: list[tuple[int, int]] = []
        self.surr_rows: list[dict] = []
        self.timing_rows: list[dict] = []
        #: DI-09/A1: o `fe_treino_max` CORRENTE (maior `fe_index` no treino do
        #: modelo ajustado). Cravado logo após o fit; toda linha ③ emitida daí
        #: em diante o herda — nenhuma predição sai sem o marcador
        #: in-sample × out-of-sample.
        self.fe_treino_max: int | None = None

    def set_fe_treino_max(self, fe_treino_max: int | None) -> None:
        """Crava o marcador A1 da iteração (chamar logo após o fit).

        No OFFLINE o valor é constante e igual a `n_dataset − 1` (o modelo vê o
        dataset inteiro, uma vez só) — o que torna todo o resto da ③
        out-of-sample por construção, exceto os próprios membros do dataset.
        """
        self.fe_treino_max = (None if fe_treino_max is None
                              else int(fe_treino_max))

    def add_pop(self, geracao: int, solution_ids) -> None:
        """Membership do arquivo REAL na geração (② — §17.2).

        **No offline** isto é "os membros do DATASET presentes na população
        selecionada" (DI-03): geração sem nenhum membro real fica sem linha, e
        a série completa (inclusive os zeros) vive no `n_ds_membros` do jsonl.
        """
        self.pop_rows.extend((int(geracao), int(s)) for s in solution_ids)

    def add_surrogate(self, row: dict) -> None:
        """Uma linha ③ montada com `export.surrogate_row(...)`. Herda o
        `fe_treino_max` corrente quando a linha não trouxer o seu."""
        if row.get("fe_treino_max") is None and self.fe_treino_max is not None:
            row = {**row, "fe_treino_max": self.fe_treino_max}
        self.surr_rows.append(row)

    def add_timing(self, geracao: int, n_acumulado: int,
                   tempo_fit_s: float | None,
                   tempo_busca_s: float | None = None,
                   tempo_pred_sonda_s: float | None = None,
                   tempo_geracao_s: float | None = None,
                   tempo_checkpoint_s: float | None = None) -> None:
        """Abre a linha ④ da geração (§17.6 expandida).

        Chame IMEDIATAMENTE após o fit — assim a curva O(n³) retém o fit mesmo
        quando o hard-stop corta a iteração no meio (D61). Os tempos que só
        existem no fim (busca/sonda/geração) entram depois, por `update_timing`.

        `tempo_fit_s=None` é legítimo **só nos pisos** (não há surrogate).
        """
        self.timing_rows.append({
            "geracao": int(geracao), "n_acumulado": int(n_acumulado),
            "tempo_fit_s": (None if tempo_fit_s is None
                            else float(tempo_fit_s)),
            "tempo_busca_s": (None if tempo_busca_s is None
                              else float(tempo_busca_s)),
            "tempo_pred_sonda_s": (None if tempo_pred_sonda_s is None
                                   else float(tempo_pred_sonda_s)),
            "tempo_geracao_s": (None if tempo_geracao_s is None
                                else float(tempo_geracao_s)),
            # [BL-11] I/O do checkpoint DESTA geração (DI-43) — medido à parte
            # pelo mesmo princípio da sonda: `tempo_busca_s`/`tempo_geracao_s`
            # medem o algoritmo, não o instrumento.
            "tempo_checkpoint_s": (None if tempo_checkpoint_s is None
                                   else float(tempo_checkpoint_s)),
        })

    def update_timing(self, geracao: int, **campos) -> None:
        """Completa a linha ④ da geração com os tempos do fim da iteração.

        Geração desconhecida ⇒ KeyError (falha barulhenta: uma ④
        meio-preenchida em silêncio é pior que um aborto). Lembre-se de chamar
        **também no ramo de término** — senão a última geração fica com
        `tempo_busca_s` NULL.
        """
        alvo = int(geracao)
        for row in reversed(self.timing_rows):
            if row["geracao"] == alvo:
                row.update({k: (None if v is None else float(v))
                            for k, v in campos.items()})
                return
        raise KeyError(
            f"update_timing: geração {alvo} não está na série ④ "
            f"(add_timing precisa vir antes). Pára-e-loga (D81).")

    @property
    def fit_series(self) -> list[dict]:
        """Cópia leve p/ o manifesto (§17.6; a canônica é `__timing.parquet`)."""
        return [{"iter": t["geracao"], "n_acumulado": t["n_acumulado"],
                 "tempo_fit_s": t["tempo_fit_s"]} for t in self.timing_rows]

    @property
    def n_geracoes(self) -> int:
        gers = {g for g, _ in self.pop_rows} | {
            int(r["geracao"]) for r in self.timing_rows}
        return len(gers)


# ═══════════════════════════════════════════════════════════════════════════
#  Fechamento do run: 4 camadas + manifesto + dual-write (§17.2/§17.7)
# ═══════════════════════════════════════════════════════════════════════════

def write_failed_manifest(exp: str, alg: str, problema: str, semente, *,
                          motivo: str, regime: str = "offline",
                          maxfe: int | None = None, fe_final: int | None = None,
                          tier: str | None = None, dist: str | None = None,
                          q: int = 1,
                          env: dict | None = None, pinning: dict | None = None,
                          algo_version: str | None = None,
                          detalhe: str | None = None,
                          enable_bucket: bool = False,
                          data_root: str = naming.DEFAULT_DATA_ROOT) -> str:
    """[T7-sweep] Manifesto HONESTO de parada anômala (D23/D60) — nunca silenciosa.

    **Por que existe.** `c311_tgprmo` já capturava toda exceção e fechava com
    `status='failed'`; `b5_prob` e `piso_offline` NÃO — um `try/finally` sem
    `except` deixava a exceção subir e o run terminava **sem manifesto nenhum**.
    Numa bateria isso é pior que um vermelho: `portao.py --varredura` enumera as
    células a partir dos manifestos em disco, então um run assim **desaparece**
    da varredura — o total cai e nada fica vermelho (o ponto cego). Descoberto no
    T7 quando a ① do tier `medium` (n=2000) estourou `LinAlgError` no fit do GPR.

    Não escreve camadas (podem estar parciais/inconsistentes) e não afere CP-init
    — o objetivo é ÚNICO: deixar a certidão de óbito do run em disco. Quem chama
    RE-LEVANTA a exceção em seguida, para o retry D23 do despachante seguir valendo.
    """
    man = _manifest.new_manifest(
        exp, alg, problema, semente, status="failed", regime=regime,
        q=int(q), tier=tier, dist=dist, maxfe=maxfe, fe_final=fe_final,
        algo_version=algo_version,
        env={**(env or {}), "pinning": (pinning or {})},
        data_root=data_root, bucket=None)
    man["motivo_parada"] = motivo
    if detalhe:
        man["stack_trace"] = detalhe
    p = _manifest.write_manifest(man, data_root)
    # [B-09] A evidência do aborto TAMBÉM sobe. Antes, `mirror_run` só rodava
    # dentro de `write_run_outputs` (fim de run bem-sucedido): as ~870 células
    # não-OK de 30 sementes ficavam órfãs no disco de uma VM efêmera e morriam
    # com ela. Só ⑥+⑤ (trilha leve), nunca levanta.
    if enable_bucket:
        man["upload_status"] = _gcs.mirror_evidencia(
            exp, alg, problema, semente, data_root=data_root)
        p = _manifest.write_manifest(man, data_root)
    return p


def write_run_outputs(exp: str, alg: str, problema: str, semente,
                      bud: _budget.FEBudget, buf: SnapshotBuffer, *,
                      D: int, M: int,
                      cp_hashes: dict, env: dict, pinning: dict,
                      n_geracoes: int, algo_version: str,
                      timing_totais: dict, sigma_dict: dict,
                      regime: str = "offline",
                      sonda_info: dict | None = None,
                      params: dict | None = None,
                      fallback_ativado: bool = False,
                      status: str = "ok",
                      motivo_parada: str | None = None,
                      q: int = 1,
                      tier: str | None = None,
                      dist: str | None = None,
                      data_root: str = naming.DEFAULT_DATA_ROOT,
                      enable_bucket: bool = False) -> dict:
    """Fecha o run: as 4 camadas §17.2 (via `src.export` — reuso, não
    duplicação) + o manifesto §17.7 e, se `enable_bucket`, o dual-write.

    O **CP-init é AFIRMADO aqui** (encanamento objetivo — D88; nada de
    fidelidade, D97):
      - ONLINE  → `hash(init_X float64)` == `doe_hash` do sidecar;
      - OFFLINE → `hash(X)` == `x_hash` **E** `hash(F)` == `f_hash` do sidecar
        do dataset (o CP mais forte — o F é insumo do modelo, não resultado).

    `cp_hashes` traz o que conferir: `{"doe_hash": ...}` no online, ou
    `{"x_hash": ..., "f_hash": ...}` no offline.

    `sigma_dict` (DEF-C4) é OBRIGATÓRIO: é o dicionário que diz o que cada
    coluna da ③ significa naquele algoritmo, e a R4 o declara "leitura
    obrigatória antes de usar a ③". Sem ele a tabela é inauditável.

    Retorna `{manifest, cp_init_ok, doe_hash_run, upload_status}`.
    """
    from src import doe as _doe

    _export.write_real(exp, alg, problema, semente, bud.records,
                       data_root=data_root)
    _export.write_pop(exp, alg, problema, semente, buf.pop_rows,
                      data_root=data_root)
    _export.write_surrogate(exp, alg, problema, semente, buf.surr_rows,
                            D=D, M=M, regime=regime, data_root=data_root)
    _export.write_timing(exp, alg, problema, semente, buf.timing_rows,
                         data_root=data_root)

    init_X = bud.init_X()
    doe_hash_run = _doe.decoded_hash(init_X)
    if "x_hash" in cp_hashes:                       # OFFLINE (D90) — X E F
        F_init = np.vstack([r.f for r in bud.records[:init_X.shape[0]]])
        f_hash_run = _decoded_hash(F_init)
        if (doe_hash_run != cp_hashes["x_hash"]
                or f_hash_run != cp_hashes.get("f_hash")):
            raise RuntimeError(
                f"CP-init OFFLINE FALHOU: x {doe_hash_run[:16]}… vs "
                f"{str(cp_hashes['x_hash'])[:16]}… ; f {f_hash_run[:16]}… vs "
                f"{str(cp_hashes.get('f_hash'))[:16]}… — o run NÃO partiu do "
                f"dataset compartilhado (D90). Pára-e-loga (D81).")
    else:                                            # ONLINE (D87/D88) — só X
        if doe_hash_run != cp_hashes.get("doe_hash"):
            raise RuntimeError(
                f"CP-init FALHOU: hash da init X do run ({doe_hash_run[:16]}…) "
                f"!= sidecar do DoE ({str(cp_hashes.get('doe_hash'))[:16]}…) — "
                f"o run NÃO partiu do artefato compartilhado (D88). "
                f"Pára-e-loga (D81).")

    # [DI-23/achado §3.3 do c149] `status` deixou de ser hard-coded: um runner
    # que aborta (teto de wall, cache-cap) passa status='failed'+motivo_parada e
    # o manifesto nasce HONESTO — antes, o c122 prometia `failed` no docstring e
    # o carimbo fixo 'ok' o desmentia (a única rede era o fe_final != maxfe).
    # [T7-sweep] tier/dist são o par LITERAL do token exp (`sweep-<tier>-<dist>`),
    # NÃO a variante de arquivo: um run de `sweep-small-lhs` declara
    # tier='small'/dist='lhs' no manifesto ainda que leia o dataset principal
    # (sem sufixo). Quem consome o manifesto quer saber a CÉLULA do grid; quem
    # escolhe o arquivo usa `naming.dataset_variant`. main/off/batch ⇒ None.
    man = _manifest.new_manifest(
        exp, alg, problema, semente, status=status, q=int(q),
        tier=tier, dist=dist,
        regime=regime, maxfe=bud.maxfe, fe_final=bud.fe,
        n_geracoes=int(n_geracoes), doe_hash=doe_hash_run,
        algo_version=algo_version,
        env={**env, "pinning": pinning},
        timing=timing_totais, fit_series=buf.fit_series,
        fallback_ativado=bool(fallback_ativado),
        data_root=data_root,
        bucket=(_gcs.BUCKET if enable_bucket else None))
    man["cache_hits"] = bud.cache_hits                     # D89 (informativo)
    man["sigma_dict"] = sigma_dict                         # DEF-C4
    if motivo_parada is not None:
        man["motivo_parada"] = motivo_parada
    if params is not None:
        man["params"] = params
    if regime == "offline":
        man["cp_init_offline"] = {"x_hash": cp_hashes.get("x_hash"),
                                  "f_hash": cp_hashes.get("f_hash")}
    if sonda_info is not None:
        man["sonda"] = sonda_info
    _manifest.write_manifest(man, data_root)

    upload_status = None
    if enable_bucket:
        upload_status = dual_write_run(exp, alg, problema, semente,
                                       manifest_dict=man, data_root=data_root)
    return {"manifest": man, "cp_init_ok": True,
            "doe_hash_run": doe_hash_run, "upload_status": upload_status}


def dual_write_run(exp: str, alg: str, problema: str, semente, *,
                   manifest_dict: dict,
                   data_root: str = naming.DEFAULT_DATA_ROOT,
                   client=None) -> dict:
    """Dual-write §17.7 (bucket-only poda a ③ local — D58), **mais a ⑦**.

    `gcs.plan_targets` itera `naming.LAYERS`, que exclui a `final` de propósito
    (senão todo run ONLINE seria cobrado por ela). Consequência: sem o trecho
    abaixo, a ⑦ e o seu sidecar **nunca subiriam** — e numa VM Vertex AI
    destruída sumiriam junto. Subimos aqui, no lado offline, em vez de mexer em
    `gcs.py` (fora da faixa deste cartão) — o que também mantém os 16 online
    exatamente como estavam. No Mac/pilotos nada disto roda
    (`enable_bucket=False`).

    [DI-42.3] BLINDADO: falha de upload NUNCA mata o run (o dado já é local;
    upload re-executável via gcs.sync). Foi exatamente aqui que 7/58 runs do
    c311 morreram na rodada-42 (env_c311 sem google-cloud-storage), truncando
    o ⑥ sem footer DEPOIS do manifesto 'ok'. Falha vira `upload_status.erro`.
    """
    try:
        status = _gcs.mirror_run(exp, alg, problema, semente,
                                 data_root=data_root, client=client)
        for p in (naming.final_path(exp, alg, problema, semente, data_root),
                  naming.final_path(exp, alg, problema, semente,
                                    data_root)[:-len(".parquet")]
                  + ".manifest.json"):
            nome = os.path.basename(p)
            if not os.path.exists(p):
                status[nome] = "absent"
                continue
            _gcs.upload(p, naming.blob_path(exp, alg, nome), client=client)
            status[nome] = "uploaded"
        manifest_dict["upload_status"] = status
        mpath = _manifest.write_manifest(manifest_dict, data_root)
        _gcs.upload(mpath,
                    naming.blob_path(exp, alg,
                                     naming.manifest_filename(exp, alg,
                                                              problema,
                                                              semente)),
                    client=client)
        return status
    except Exception as e:  # noqa: BLE001 — upload é acessório; dado é local
        status = {"erro": f"upload_failed: {e!r}"}
        manifest_dict["upload_status"] = status
        try:
            _manifest.write_manifest(manifest_dict, data_root)
        except Exception:  # noqa: BLE001 — manifesto local anterior permanece
            pass
        return status


# ═══════════════════════════════════════════════════════════════════════════
#  Camada ⑦ `__final.parquet` — o ND final do OFFLINE avaliado 1× (DI-08)
# ═══════════════════════════════════════════════════════════════════════════

def final_schema(D: int, M: int):
    """Schema da camada ⑦ (DI-08). Só os 5 configs offline a possuem.

    Colunas, e o porquê de cada uma:
      - `algoritmo|problema|semente` — identidade, igual às outras 4 camadas;
      - `x0..x{D-1}` — o vetor de decisão do ND final (float32, D53);
      - `f0..f{M-1}` — o **f VERDADEIRO**, avaliado 1× em `src/problems.py`
        (float64) e gravado em float32 como as demais camadas;
      - `origem_solution_id` — o `solution_id` da ① quando o ponto É um membro
        do dataset (nullable: quase todos os finais são candidatos que o MOEA
        gerou sobre o surrogate e nunca foram reais);
      - `origem_geracao` + `origem_linha` — o **link à ③** exigido pelo DI-08:
        a geração de onde os decs vieram e a posição da linha dentro daquele
        bloco. Posicional de propósito — a mesma disciplina do join da sonda
        (R4 regra 5), e imune ao float32 do X (R4 regra 1 proíbe casar por X);
      - `nd_pos_real` — o filtro de não-dominância aplicado **DEPOIS** da
        avaliação real (B7.5: "avaliar os N finais e filtrar pós-real"). É a
        coluna que separa o front verdadeiro do "erro de fantasia": um ponto
        ótimo no modelo pode ser dominado na verdade. Guardamos TODOS os
        finais (D54) e marcamos quais sobreviveram.

    ⚠ Esquema DEFINIDO POR ESTE CARTÃO e SINALIZADO PARA VETO — a DI-08 fixou
    `x*|f*|origem` e delegou o resto ("exige decisão de schema/naming") à torre.
    """
    pa = _export._pa()
    fields = [
        pa.field("algoritmo", pa.string(), nullable=False),
        pa.field("problema", pa.string(), nullable=False),
        pa.field("semente", pa.int32(), nullable=False),
    ]
    fields += [pa.field(c, pa.float32(), nullable=False)
               for c in _export.x_cols(D)]
    fields += [pa.field(c, pa.float32(), nullable=False)
               for c in _export.f_cols(M)]
    fields += [
        pa.field("origem_solution_id", pa.int32(), nullable=True),
        pa.field("origem_geracao", pa.int32(), nullable=False),
        pa.field("origem_linha", pa.int32(), nullable=False),
        pa.field("nd_pos_real", pa.bool_(), nullable=False),
    ]
    return pa.schema(fields)


def write_final(exp: str, alg: str, problema: str, semente,
                X: np.ndarray, F: np.ndarray, *,
                origem_solution_id=None, origem_geracao=None,
                origem_linha=None, nd_pos_real=None,
                origem_precisao: str = "float64 (decs em memória — "
                                       "caminho nativo R3)",
                origem_camada: str = "surrogate (③), última geração da busca",
                data_root: str = naming.DEFAULT_DATA_ROOT) -> str:
    """Escreve a camada ⑦ `__final.parquet` (DI-08), atomicamente.

    `X` (n, D) e `F` (n, M) em float64 — `F` é o resultado da avaliação REAL
    (`problems.evaluate_problem`), feita **fora do orçamento** (a exceção
    contábil do §11: esta é "a única chamada real do offline", e ela é pós-hoc,
    então não entra no `FEBudget` nem na ①, que segue com as 31D−1 do dataset).

    `nd_pos_real` omitido ⇒ calculado aqui sobre a vista **float32** de `F` —
    a MESMA que a ⑦ persiste e que qualquer leitor da R4 terá. Calculá-lo no
    float64 cru criaria uma assimetria dentro da própria camada: empates
    próximos dariam um front na hora de escrever e outro na hora de reler, e o
    `--check` reprovaria uma ⑦ correta.

    `origem_precisao` vai ao sidecar: TODA ⑦ nasce com a sua certidão, tanto
    pelo caminho nativo (decs float64 em memória) quanto pelo retroativo.
    """
    pa = _export._pa()
    X = np.ascontiguousarray(X, dtype=np.float64)
    F = np.ascontiguousarray(F, dtype=np.float64)
    if X.ndim != 2 or F.ndim != 2 or X.shape[0] != F.shape[0]:
        raise ValueError(
            f"__final: shapes incompatíveis X={X.shape} F={F.shape}.")
    if X.shape[0] == 0:
        raise ValueError(
            "__final vazio — o ND final do offline tem de ter ao menos 1 "
            "ponto (§11). Pára-e-loga (D81).")
    n, D, M = X.shape[0], X.shape[1], F.shape[1]

    # A vista float32 é a que fica no arquivo — o front tem de ser computado
    # sobre ELA para a coluna ser reproduzível a partir da ⑦ (ver docstring).
    F_persistido = F.astype(np.float32).astype(np.float64)
    if nd_pos_real is None:
        from src import problems as _problems
        idx = set(int(i) for i in                              # índices (A-8)
                  _problems._nds_filter(F_persistido))
        nd_pos_real = [i in idx for i in range(n)]

    cols: dict = {
        "algoritmo": pa.array([alg] * n, type=pa.string()),
        "problema": pa.array([problema] * n, type=pa.string()),
        "semente": pa.array([int(semente)] * n, type=pa.int32()),
    }
    Xf, Ff = _export._f32(X), _export._f32(F)
    for j, c in enumerate(_export.x_cols(D)):
        cols[c] = pa.array(Xf[:, j], type=pa.float32())
    for j, c in enumerate(_export.f_cols(M)):
        cols[c] = pa.array(Ff[:, j], type=pa.float32())
    cols["origem_solution_id"] = pa.array(
        [None if origem_solution_id is None or origem_solution_id[i] is None
         else int(origem_solution_id[i]) for i in range(n)], type=pa.int32())
    cols["origem_geracao"] = pa.array(
        [int(origem_geracao[i]) if origem_geracao is not None else -1
         for i in range(n)], type=pa.int32())
    cols["origem_linha"] = pa.array(
        [int(origem_linha[i]) if origem_linha is not None else i
         for i in range(n)], type=pa.int32())
    cols["nd_pos_real"] = pa.array([bool(b) for b in nd_pos_real],
                                   type=pa.bool_())

    table = pa.table(cols).cast(final_schema(D, M))
    path = _export._write_table(
        naming.final_path(exp, alg, problema, semente, data_root), table)

    # Certidão da camada — escrita AQUI (e não só no `final_eval`) para que a
    # ⑦ do caminho nativo também a tenha. O `check_final` a exige.
    side = {
        "schema_version": 1, "camada": "final", "decisao": "DI-08",
        "run_id": naming.run_id(exp, alg, problema, semente),
        "n_final": int(n), "n_nd_pos_real": int(sum(bool(b)
                                                    for b in nd_pos_real)),
        "origem_camada": origem_camada,
        "origem_precisao": origem_precisao,
        "avaliador": "src/problems.py::evaluate_problem (float64)",
        "fora_do_orcamento": True,
        "convencao": ("B7.5 — avaliar TODOS os finais e filtrar a "
                      "não-dominância PÓS-real (coluna nd_pos_real, computada "
                      "sobre a vista float32 persistida)"),
    }
    with open(path[:-len(".parquet")] + ".manifest.json", "w",
              encoding="utf-8") as fh:
        json.dump(side, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return path


# ═══════════════════════════════════════════════════════════════════════════
#  Run-STUB `stubr3` — prova de encanamento OFFLINE ponta-a-ponta (SEM algoritmo)
# ═══════════════════════════════════════════════════════════════════════════

#: Token do STUB desta rodada. DISTINTO de propósito dos irmãos: `stub` é o
#: STUB MATLAB do R1-00 e `stubpy` o do R2-00 — cada um tem a sua pasta em
#: `data/experiments/{exp}/{token}/` e nenhum sobrescreve o do outro.
STUB_ALG = "stubr3"

#: Gerações do MOEA interno do STUB (o orçamento interno real de cada config
#: está na §11 — 10k no e103, 40k no b5/piso, 1k gerações no c311).
_STUB_GERACOES = 8


def _stub_surrogate(ds: dict):
    """Surrogate de brinquedo: média do F do dataset ponderada por 1/d².

    NÃO é um algoritmo (D97 não se aplica — isto é encanamento). É só um
    preditor determinístico, sem RNG e sem estado, que produz μ e σ plausíveis
    para exercitar a ③, a sonda e o `__final`. Devolve `predict(Xq)->(mu, sg)`
    com μ **em f de minimização**, como o export exige.
    """
    Xd, Fd = ds["X"], ds["F"]

    def predict(Xq):
        Xq = np.atleast_2d(np.asarray(Xq, dtype=np.float64))
        d2 = ((Xq[:, None, :] - Xd[None, :, :]) ** 2).sum(-1) + 1e-12
        w = 1.0 / d2
        w /= w.sum(axis=1, keepdims=True)
        mu = w @ Fd
        # σ = dispersão ponderada (proxy honesto de incerteza local).
        var = w @ (Fd ** 2) - mu ** 2
        return mu, np.sqrt(np.maximum(var, 0.0))

    return predict


def run_stubr3(exp: str, alg: str, problema: str, semente, *,
               data_root: str = naming.DEFAULT_DATA_ROOT,
               enable_bucket: bool = False, **_kwargs) -> dict:
    """O run-STUB transversal do R3-00 — regime OFFLINE, SEM algoritmo.

    Prova o ENCANAMENTO do contrato N.2 ponta-a-ponta:

      dataset D90 carregado do artefato (CP-init `x_hash` **E** `f_hash`) →
      orçamento ESGOTADO na carga (① = o dataset, 31D−1 exatas) → fit único e
      cronometrado → **sonda offline 1× por modelo treinado** (2000 linhas
      `regime='sonda'`, ZERO FE) → MOEA interno de brinquedo sobre o surrogate,
      com ② (membros do dataset na pop), ③ (`regime='offline'`, `fe_treino_max`)
      e ④ v5.2.1 completa por geração → **`__final` avaliado 1× em problems.py**
      com os decs float64 em memória (DI-08) → 4+1 camadas + jsonl + manifesto.

    Qualquer FE na busca é VIOLAÇÃO (não término): o `offline_guard` a converte
    em `OfflineBudgetViolation` e o run pára-e-loga (D81).

    Assinatura padrão dos runners (o `experiment.run` repassa `**kwargs`).
    Retorna o dict de evidências que o `accept.py R3-00-harness` afere.
    """
    t_run = time.time()
    pinning = pin_runtime()
    env = env_info()
    semente = int(semente)

    bud, ds = load_offline_budget(problema, semente, data_root=data_root)
    D, M, n_ds = ds["D"], ds["M"], ds["n"]
    # [DI-13.5] o STUB do R3-00 é OFFLINE ⇒ lê o artefato INTEIRO (20.000).
    # Os cartões R3 ONLINE (c122/c149/e81) passam regime='online' (fatia 2.000).
    sonda = load_sonda(problema, regime='offline', data_root=data_root)
    buf = SnapshotBuffer()
    log = AuditLogger.for_run(exp, alg, problema, semente,
                              data_root=data_root, append=False)

    sigma_dict = {
        "modelo": "STUB IDW (encanamento — NÃO é algoritmo do estudo)",
        "mu_*": "predição do surrogate, em f de minimização",
        "sigma_*": "dispersão ponderada local (proxy de incerteza)",
        "regime": "offline = candidatos da busca · sonda = a régua fixa §17.2.2",
        "fe_treino_max": f"constante {n_ds - 1} — o modelo vê o dataset inteiro,"
                         f" 1× (offline não retreina)",
    }
    try:
        log.header(alg=alg, versao="stubr3-1.0", problema=problema, D=D, M=M,
                   semente=semente, regime="offline", maxfe=bud.maxfe,
                   n_dataset=n_ds, doe_hash=ds["x_hash"], f_hash=ds["f_hash"],
                   dataset_hash=ds.get("dataset_hash"),
                   ambiente=env, pinning=pinning, sigma_dict=sigma_dict,
                   sonda_x_hash=sonda["x_hash"], sonda_S=sonda["S"])

        # ── fit ÚNICO (offline não retreina) ────────────────────────────────
        t0 = time.time()
        predict = _stub_surrogate(ds)
        t_fit = time.time() - t0
        buf.set_fe_treino_max(n_ds - 1)
        buf.add_timing(geracao=1, n_acumulado=n_ds, tempo_fit_s=t_fit)

        # ── sonda: cadência OFFLINE = 1× por modelo treinado ────────────────
        # Emitida FORA do laço, e de propósito: assim `tempo_geracao_s` NÃO
        # inclui o custo da sonda (a semântica A-2/D-1 que o retrofit R2
        # cravou — instrumentar não pode contaminar a medida do mecanismo, e
        # contaminaria de forma DESIGUAL). O custo vive em `tempo_pred_sonda_s`.
        t_sonda = emit_sonda_block(
            buf, log, geracao=1, fe=bud.fe, sonda=sonda, predict=predict,
            fe_treino_max=n_ds - 1, modelo_flag="STUB-IDW",
            motivo="offline: 1x por modelo treinado")

        # ── MOEA interno sobre o surrogate — ZERO FE ────────────────────────
        rng = np.random.default_rng(
            iteration_seed(seed_base(alg, semente), 99, 0, 0, bits32=True))
        pop = ds["X"].copy()                       # init = o dataset (offline)
        #: A população da ÚLTIMA geração GRAVADA na ③ — e é ela, não a prole
        #: seguinte, que vira a ⑦. INVARIANTE do regime offline: o ND final
        #: tem de ser reconstituível a partir da ③ (é a única fonte para o
        #: e103, que já rodou em MATLAB). Gravar a ⑦ a partir de pontos que a
        #: ③ não viu quebra o `--check` do `final_eval` e a auditoria da R4.
        pop_final = pop
        t_busca_total = 0.0
        with offline_guard(log, alg=alg, problema=problema):
            for g in range(1, _STUB_GERACOES + 1):
                t_g0 = time.time()
                mu, sg = predict(pop)
                # "seleção": mantém os não-dominados NO MODELO + ruído.
                keep = _nds_idx(mu)
                filhos = np.clip(
                    pop[keep][rng.integers(0, len(keep), size=len(pop))]
                    + rng.normal(0, 0.02, size=pop.shape),
                    np.asarray(_bounds(problema)[0]),
                    np.asarray(_bounds(problema)[1]))
                t_busca = time.time() - t_g0

                for i in range(pop.shape[0]):
                    buf.add_surrogate(_export.surrogate_row(
                        g, pop[i], regime="offline",
                        real_solution_id=bud.solution_id_of(pop[i]),
                        mu=mu[i], sigma=sg[i], pred_tipo="valor",
                        modelo_flag="STUB-IDW"))
                # ② offline = os MEMBROS DO DATASET na pop selecionada (DI-03)
                membros = [s for s in (bud.solution_id_of(p) for p in pop)
                           if s is not None]
                buf.add_pop(g, membros)
                if g > 1:
                    buf.add_timing(geracao=g, n_acumulado=n_ds,
                                   tempo_fit_s=0.0)
                buf.update_timing(
                    g, tempo_busca_s=t_busca,
                    tempo_pred_sonda_s=(t_sonda if g == 1 else 0.0),
                    tempo_geracao_s=(time.time() - t_g0))
                log.decision(
                    caminho="stubr3_gen", motivo="selecao ND no surrogate",
                    geracao=g, n_ds_membros=len(membros),
                    **minimo_comum_di10(mu, fe=bud.fe, tempo_fit_s=t_fit,
                                        tempo_busca_s=t_busca))
                t_busca_total += t_busca
                pop_final = pop            # o que a ③ REGISTROU nesta geração
                pop = filhos
                iteration_cleanup()

        # ── ⑦ `__final`: o ND final avaliado 1× na verdade (DI-08) ─────────
        # Caminho NATIVO da R3: os decs estão em float64 na memória, então a
        # ⑦ não passa pelo float32 da ③ (o caveat do `final_eval` só vale para
        # o retroativo do e103).
        from src import problems as _problems
        F_final = np.ascontiguousarray(
            _problems.evaluate_problem(_instantiate(problema), pop_final),
            dtype=np.float64)
        nd_idx = set(int(i) for i in _problems._nds_filter(F_final))
        write_final(exp, alg, problema, semente, pop_final, F_final,
                    origem_solution_id=[bud.solution_id_of(x)
                                        for x in pop_final],
                    origem_geracao=[_STUB_GERACOES] * pop_final.shape[0],
                    origem_linha=np.arange(pop_final.shape[0]),
                    nd_pos_real=[i in nd_idx
                                 for i in range(pop_final.shape[0])],
                    data_root=data_root)

        timing_totais = _export.manifest_timing_block(
            tempo_total_s=time.time() - t_run, tempo_fit_surrogate_s=t_fit,
            # [I-02] NULL, não 0.0: no OFFLINE o orçamento nasce ESGOTADO (a ①
            # é o dataset, D90) e nenhuma avaliação real acontece DENTRO do run —
            # gravar zero afirmaria "avaliar custou zero". `bud.tempo_aval_real_s`
            # devolve None quando nenhuma avaliação passou pelo portão.
            tempo_busca_s=t_busca_total,
            tempo_aval_real_s=bud.tempo_aval_real_s,
            tempo_pred_sonda_s=t_sonda)
        res = write_run_outputs(
            exp, alg, problema, semente, bud, buf, D=D, M=M,
            cp_hashes={"x_hash": ds["x_hash"], "f_hash": ds["f_hash"]},
            env=env, pinning=pinning, n_geracoes=_STUB_GERACOES,
            algo_version="stubr3-1.0", timing_totais=timing_totais,
            sigma_dict=sigma_dict, regime="offline",
            sonda_info={"S": sonda["S"], "cadencia": "offline: 1x por modelo",
                        "n_blocos": 1, "x_hash": sonda["x_hash"],
                        "f_hash": sonda["f_hash"]},
            data_root=data_root, enable_bucket=enable_bucket)
        log.footer(status="ok", fe_final=bud.fe, cp_init=True,
                   cache_hits=bud.cache_hits, n_geracoes=_STUB_GERACOES,
                   n_final=int(pop_final.shape[0]), n_nd_pos_real=len(nd_idx))
    finally:
        log.close()

    return {
        "fe_final": bud.fe, "maxfe": bud.maxfe, "n_dataset": n_ds,
        "cp_init_ok": bool(res["cp_init_ok"]), "n_geracoes": _STUB_GERACOES,
        "n_surrogate_rows": len(buf.surr_rows), "n_pop_rows": len(buf.pop_rows),
        "n_timing_rows": len(buf.timing_rows), "n_sonda_pontos": sonda["S"],
        "n_final": int(pop_final.shape[0]), "n_nd_pos_real": len(nd_idx),
        "regime": "offline", "cache_hits": bud.cache_hits,
        "tempo_pred_sonda_s": t_sonda,
    }


def _instantiate(problema: str):
    from src import experiment as _exp
    return _exp._instantiate_problem(problema)


def _bounds(problema: str):
    p = _instantiate(problema)
    return (np.asarray(p.xl, dtype=np.float64),
            np.asarray(p.xu, dtype=np.float64))


def _nds_idx(F) -> np.ndarray:
    from src import problems as _problems
    return np.asarray(_problems._nds_filter(np.asarray(F, dtype=np.float64)),
                      dtype=np.int64)


__all__ = [
    "D79_THREAD_VARS", "OFFLINE_CONFIGS", "SONDA_K", "SONDA_CHUNK", "STUB_ALG",
    "ROOT", "ENVS_JSON",
    "pin_runtime", "env_info", "load_env_table", "interpreter_for_alg",
    "child_env", "run_in_venv",
    "iteration_seed", "seed_base", "SEED_OFFSET_ALGS",
    "preserve_global_rng", "preserve_all_rng", "guarded_pymoo_minimize",
    "iteration_cleanup",
    "load_doe", "load_dataset", "load_offline_budget", "offline_guard",
    "OfflineBudgetViolation",
    "load_sonda", "sonda_due", "emit_sonda_block",
    "minimo_comum_di10", "SnapshotBuffer",
    "write_run_outputs", "dual_write_run",
    "final_schema", "write_final", "run_stubr3",
]
