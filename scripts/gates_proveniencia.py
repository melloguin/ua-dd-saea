#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Os gates de PROVENIÊNCIA e INTEGRIDADE por célula — G-1..G-4 + B-15 [T11-G6].

O portão da rodada-42 gateava CONTEÚDO (accept/auditar/final_eval) e não olhava
**de onde o dado veio**. Custo medido: **34 das 666 células (5,1%)** com
assinatura anômala e **1 quimera** (`batch/c149/q10_ZDT4`: ①②④⑤⑥ do run da v6 de
26/07 com a ③ do run do Mac de 24/07, md5 `1269b87f7612`; o cruzamento ③×①
fechou **0/2.000** com max‖ΔX‖ = 9,999830). Em 30 sementes: ~1.020 anômalas e
~30 quimeras em 19.980 — cada uma envenenando tudo que liga ③ a ① (erro de
fantasia, calibração μ/σ, `acq_resF_*`, `transf_params`).

Os 4 gates + o discriminador, todos O(1)-ish por célula (medido: **20,5 s de CPU
nas 666** ⇒ ~10 min nas 19.980):

* **G-1 3×1** — o X da linha da ③ marcada com `real_solution_id` é BIT-IDÊNTICO
  ao X da linha correspondente da ①. É o gate que pega a quimera. Porte do
  `f5/baterias/f54/padrao_zdt4/teste_3x1.py` (não reescrita).
* **G-2 unicidade/integridade do ⑥** — exatamente 1 `header`, o nº de `footer`
  ESPERADO POR CONFIG (lido do `mapa_termino.json`, nunca hard-coded), 0 linhas
  malformadas, e o footer do runner portando `fe_final`.
* **G-3 proveniência** — `env.executable` do ⑤ ∈ roster de intérpretes daquele
  alg em `envs.json`; `campanha_id` presente; `repo_hash` não-vazio.
* **G-4 gabarito NORMATIVO de camadas** — a tabela declarada do
  `gabarito_camadas.json` em vez da assinatura MODAL do censo (que é cega a "0/45
  células têm ⑦").
* **B-15 discriminador O-22** — "footer ausente = morte de máquina" dava
  **21 falsos-positivos** na s42 (9 com ZERO footer), todas com `fe_final==maxfe`
  e hashes iguais aos irmãos de tier: eram smokes fora do despachante.

Uso (módulo importável pelo `portao.py`; CLI para varredura solta):
    python3 scripts/gates_proveniencia.py --varredura
    python3 scripts/gates_proveniencia.py --exp main --alg c149 --problema ZDT4 --semente 42
"""
from __future__ import annotations

import argparse
import functools
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ARTEFATOS = os.path.join(ROOT, "claude_code_context", "artifacts")


# ═══════════════════════════════════════════════════════════════════════════
#  Artefatos (fonte única — nunca literal duplicado)
# ═══════════════════════════════════════════════════════════════════════════

@functools.lru_cache(maxsize=None)
def _artefato(nome: str) -> dict:
    with open(os.path.join(ARTEFATOS, nome), encoding="utf-8") as fh:
        return json.load(fh)


def classifica_motivo(motivo) -> str:
    """[B-06] `motivo_parada` → {'sancionado','falha','normal','desconhecido'}.

    FONTE ÚNICA: `artifacts/motivos_parada.json`. Era um literal em 3 arquivos, e
    em 2026-07-25 o literal foi cravado ERRADO ('cache_cap' em vez de
    'cache_hit_travado' — DI-41.2), o que transformaria todo aborto por cache
    travado em 🔴 (falso alarme em escala).
    """
    if motivo in (None, ""):
        return "normal"
    art = _artefato("motivos_parada.json")
    m = str(motivo)
    ent = art["motivos"].get(m)
    if ent is not None:
        return ent["classe"]
    for pref in art.get("prefixos_de_falha", ()):
        if m.startswith(pref):
            return "falha"
    return "desconhecido"


def motivo_e_sancionado(motivo) -> bool:
    return classifica_motivo(motivo) == "sancionado"


# ═══════════════════════════════════════════════════════════════════════════
#  G-1 · 3×1 (coerência inter-camada) — o gate que pega a quimera
# ═══════════════════════════════════════════════════════════════════════════

def gate_3x1(caminho_terceira: str, caminho_primeira: str) -> tuple[bool, str]:
    """X da ③ (linhas com `real_solution_id`) ≡ X da ① — BIT-A-BIT.

    Porte do `f5/baterias/f54/padrao_zdt4/teste_3x1.py`. Placar que ele tem de
    reproduzir nas 666: **360 aplicáveis, 359 OK a 100%, 1 falha** (a quimera).
    Célula sem `real_solution_id` na ③ (pisos, classificadores puros) é
    NÃO-APLICÁVEL — e não-aplicável nunca é verde nem vermelho.
    """
    try:
        import numpy as np
        import pyarrow.parquet as pq
    except ImportError as e:                        # exit 2 = INCONCLUSIVO
        return None, f"dependência ausente ({e.name}) — INCONCLUSIVO"
    if not (os.path.exists(caminho_terceira) and os.path.exists(caminho_primeira)):
        return None, "sem ③ ou sem ① — não-aplicável"
    cols = pq.ParquetFile(caminho_terceira).schema_arrow.names
    if "real_solution_id" not in cols:
        return None, "③ sem real_solution_id — não-aplicável"
    xs = [c for c in cols if c.startswith("x") and c[1:].isdigit()]
    t3 = pq.read_table(caminho_terceira, columns=["real_solution_id"] + xs)
    ids3 = t3.column("real_solution_id").to_pylist()
    marcadas = [i for i, v in enumerate(ids3) if v is not None]
    if not marcadas:
        return None, "③ sem nenhuma linha marcada — não-aplicável"
    X3 = np.column_stack([np.asarray(t3.column(c).to_pylist(), dtype=np.float64)
                          for c in xs])[marcadas]
    t1 = pq.read_table(caminho_primeira, columns=["solution_id"] + xs)
    pos = {v: i for i, v in enumerate(t1.column("solution_id").to_pylist())}
    X1 = np.column_stack([np.asarray(t1.column(c).to_pylist(), dtype=np.float64)
                          for c in xs])
    alvo = [pos.get(ids3[i], -1) for i in marcadas]
    achados = [k for k, p in enumerate(alvo) if p >= 0]
    if not achados:
        return False, (f"IDS_AUSENTES: as {len(marcadas)} linhas marcadas da ③ "
                       f"apontam ids que não existem na ①")
    d = np.abs(X3[achados] - X1[[alvo[k] for k in achados]]).max(axis=1)
    n_bit = int((d == 0).sum())
    frac = n_bit / len(achados)
    det = (f"{n_bit}/{len(achados)} bit-idênticos (frac={frac:.6f}, "
           f"max|ΔX|={float(d.max()):.6g}, {len(marcadas) - len(achados)} sem id)")
    return (frac == 1.0), det


# ═══════════════════════════════════════════════════════════════════════════
#  G-2 · unicidade e integridade do ⑥
# ═══════════════════════════════════════════════════════════════════════════

def gate_unicidade_sexto(caminho_jsonl: str, alg: str) -> tuple[bool, str]:
    """1 `header`, `n_footers` ESPERADO por config, 0 linha malformada.

    Medido nos 666 ⑥ da s42: 355 com 1+1, 300 com 1+2, 9 sem footer, 1 com 3, 1
    com multiplicidade (`batch/e81/q10_ZDT4`, 95 pares). O gate tem de acusar
    exatamente esses 11.
    """
    if not os.path.exists(caminho_jsonl):
        return False, "⑥ ausente"
    mapa = _artefato("mapa_termino.json")["configs"].get(alg)
    esperado = list(mapa["n_footers_esperado"]) if mapa else [1, 2]
    n_head = n_foot = n_mal = 0
    n_foot_com_fe = 0
    with open(caminho_jsonl, "rb") as fh:
        for raw in fh:
            if not raw.strip():
                continue
            if b'"rec"' not in raw:
                n_mal += 1
                continue
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                n_mal += 1
                continue
            if rec.get("rec") == "header":
                n_head += 1
            elif rec.get("rec") == "footer":
                n_foot += 1
                if rec.get("fe_final") is not None:
                    n_foot_com_fe += 1
    problemas = []
    if n_head != 1:
        problemas.append(f"{n_head} headers (esperado 1)")
    if n_foot not in esperado:
        problemas.append(f"{n_foot} footers (esperado {esperado})")
    if n_mal:
        problemas.append(f"{n_mal} linhas malformadas")
    if n_foot and not n_foot_com_fe:
        problemas.append("nenhum footer porta fe_final (só o do despachante)")
    det = f"header={n_head} footers={n_foot} malformadas={n_mal}"
    return (not problemas), (det if not problemas else det + " → " + "; ".join(problemas))


# ═══════════════════════════════════════════════════════════════════════════
#  G-3 · proveniência (o intérprete, a campanha e o commit)
# ═══════════════════════════════════════════════════════════════════════════

def venv_de(executavel: str) -> str:
    """`/…/python_venvs/env_b5/bin/python` → `env_b5`.

    Compara-se o NOME DO VENV, não o caminho: o mesmo venv vive em
    `/Users/gmello/Documents/python_venvs/<venv>/bin/python` no Mac e em
    `/home/jupyter/python_venvs/<venv>/bin/python` na VM (ambos MEDIDOS na s42).
    Comparar o caminho inteiro reprovaria a VM; comparar o basename (`python`)
    não reprovaria nada.
    """
    p = str(executavel).replace("\\", "/").rstrip("/")
    partes = [x for x in p.split("/") if x]
    if len(partes) >= 3 and partes[-2] in ("bin", "Scripts"):
        return partes[-3]
    return partes[-1] if partes else ""


@functools.lru_cache(maxsize=None)
def _venvs_por_alg() -> dict:
    """alg → {venvs aceitos} declarados em `envs.json` (D79/D80/N.1.2).

    É o roteamento por venv que impede o desastre silencioso do N.1.2: `b5` e
    `c311` vendorizam `desdeo_*` HOMÔNIMOS com código diferente, e rodar um no
    venv do outro faz o `sys.modules` entregar as classes erradas SEM ERRO.
    """
    envs = _artefato("envs.json")
    ambientes = envs.get("environments", {})
    out: dict[str, set] = {}
    for alg, ent in envs.get("alg_to_env", {}).items():
        env_id = ent.get("env") if isinstance(ent, dict) else ent
        out[alg] = set((ambientes.get(env_id) or {}).get("venvs_aceitos") or ())
    return out


def gate_proveniencia(man: dict, alg: str, *, campanha_id=None,
                      modo: str = "campanha") -> tuple[bool, str]:
    """venv do `env.executable` no roster do alg + `campanha_id` + `repo_hash`.

    ⚠ O que este gate NÃO faz: pegar a quimera sozinho. `batch/c149/q10_ZDT4`
    declara `env.executable=/home/jupyter/python_venvs/env_main/bin/python` — um
    intérprete LEGÍTIMO para o c149 — e traz a ③ do Mac. Quem fecha a quimera é o
    **G-1**. Este pega o caso mais comum e mais destrutivo em silêncio: a célula
    que rodou no venv ERRADO (N.1.2) e a que não carrega identidade de campanha
    ou de commit.

    **`modo`** separa duas perguntas que não são a mesma:
    - `'campanha'` (default) — *"esta célula serve à campanha CORRENTE?"*: exige
      `campanha_id` (B-03) e `repo_hash` (I-09).
    - `'historico'` — *"a proveniência desta célula é coerente?"*: só o roster de
      venv. É o modo do re-gate das 666 da rodada-42, cujos ⑤ são schema v1 e
      têm `repo_hash` vazio em 666/666 por construção (os campos NÃO EXISTIAM).
      Rodar o modo estrito ali pintaria o grid inteiro de vermelho e o placar de
      aceitação (1 quimera + 34 anômalas) viraria ruído.
    """
    faltas, avisos = [], []
    env = man.get("env") or {}
    exe = env.get("executable") or ""
    roster = _venvs_por_alg().get(alg)
    if exe and roster:
        if venv_de(exe) not in roster:
            faltas.append(f"venv={venv_de(exe)!r} fora do roster de {alg} "
                          f"({sorted(roster)})")
    elif not exe:
        # MATLAB não tem intérprete Python: 654 das 666 células da s42 não têm o
        # campo, por desenho (o ⑤ do stack matlab traz `env.matlab`).
        avisos.append("⑤ sem env.executable")
    cid = man.get("campanha_id")
    if modo == "campanha":
        if not cid:
            faltas.append("⑤ sem campanha_id (schema v1 — B-03)")
        elif campanha_id and cid != campanha_id:
            faltas.append(f"campanha_id={cid!r} ≠ corrente {campanha_id!r}")
        if not (man.get("repo_hash") or "").strip():
            faltas.append("repo_hash vazio (I-09 — quebra o elo D80 run↔código)")
    else:                                   # histórico: os campos não existiam
        if not cid:
            avisos.append("⑤ v1 sem campanha_id (esperado na s42)")
        if not (man.get("repo_hash") or "").strip():
            avisos.append("repo_hash vazio (esperado na s42 — I-09)")
    det = f"venv={venv_de(exe) or '∅'} campanha={cid or '∅'}"
    if avisos:
        det += " · " + "; ".join(avisos)
    return (not faltas), (det if not faltas else det + " → " + "; ".join(faltas))


# ═══════════════════════════════════════════════════════════════════════════
#  G-4 · gabarito NORMATIVO de camadas
# ═══════════════════════════════════════════════════════════════════════════

def gate_gabarito_camadas(exp: str, alg: str, problema: str, semente,
                          data_root: str = "data") -> tuple[bool, str]:
    """As camadas obrigatórias do config existem? (tabela DECLARADA, não modal)"""
    from src import naming
    gab = _artefato("gabarito_camadas.json")
    ent = gab["configs"].get(alg)
    obrig = (ent or {}).get("obrigatorias") or (
        gab["obrigatorias_offline"] if alg in gab["configs_offline"]
        else gab["obrigatorias_default"])
    raiz = data_root if os.path.isabs(data_root) else os.path.join(ROOT, data_root)
    faltando = []
    for ly in obrig:
        if ly == "jsonl":
            p = naming.jsonl_path(exp, alg, problema, semente, raiz)
        elif ly == "manifest":
            p = naming.manifest_path(exp, alg, problema, semente, raiz)
        else:
            p = naming.layer_path(exp, alg, problema, semente, ly, raiz)
        if not os.path.exists(p):
            faltando.append(ly)
    return (not faltando), (f"{len(obrig) - len(faltando)}/{len(obrig)} camadas"
                            + (f" → FALTA {faltando}" if faltando else ""))


# ═══════════════════════════════════════════════════════════════════════════
#  G-7 · o CONTRATO §6.1 aferido (as chaves do ⑥ e do ⑤ por config)
# ═══════════════════════════════════════════════════════════════════════════

#: `rec` que NÃO são evento de geração (o G-7 só olha o evento da decisão).
_RECS_NAO_GERACAO = frozenset({"header", "footer", "guard", "sonda", "timing",
                               "partial", "retry", "checkpoint"})


def campos_contratados(alg: str) -> tuple[set, set, dict]:
    """(campos do ⑥, campos do ⑤, não-se-aplica) para o config — do artefato."""
    art = _artefato("contrato_61.json")
    ent = art["configs"].get(alg, {"di10": [], "nao_se_aplica": {}})
    nsa = dict(ent.get("nao_se_aplica") or {})
    sexto = (set(art["minimo_comum_di10"]["campos"]) | set(ent.get("di10") or ())) - set(nsa)
    return sexto, set(art["quinto_obrigatorio"]["campos"]), nsa


def gate_contrato_61(alg: str, caminho_jsonl: str, man: dict,
                     *, max_linhas: int = 200_000) -> tuple[bool | None, str]:
    """[G-7] As chaves que o CONTRATO §6.1 promete estão no ⑥ e no ⑤?

    Nenhum gate conferia campo DI-10 de config algum: `auditar.py` NÃO inspeciona
    o ⑥ (zero ocorrências de `jsonl`/`decision`/`_gen`/`f_best` no arquivo) e o
    `accept.py:check_r3_b5` tem 8 itens, todos estruturais. Foi por essa porta que
    I-05 (b5 `p_wrong_stats` 0/N em 30.165 eventos), I-07 (`params` ausente no ⑤
    de 7 configs, ~32% do grid) e I-03 (`n_front1` do sobol_batch) atravessaram
    CINCO gates verdes.

    O que NÃO SE APLICA vem declarado no artefato com o motivo (`tempo_fit_s` nos
    4 pisos online é NULL por contrato — DI-13.2; `n_baseline` no e81 é conceito
    do qLogNEHVI que o qPOTS não tem — P6/DI-16.6), então o gate não inventa
    falso-vermelho onde o contrato já disse "aqui não".
    """
    sexto, quinto, _nsa = campos_contratados(alg)
    if not os.path.exists(caminho_jsonl):
        return None, "⑥ ausente — não-aplicável"
    vistos: set = set()
    n_eventos = 0
    with open(caminho_jsonl, "rb") as fh:
        for i, raw in enumerate(fh):
            if i >= max_linhas:
                break
            if b'"rec"' not in raw:
                continue
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                continue
            if not isinstance(rec, dict) or rec.get("rec") in _RECS_NAO_GERACAO:
                continue
            n_eventos += 1
            vistos |= set(rec.keys())
    if not n_eventos:
        return None, "⑥ sem evento de geração — não-aplicável (ver mapa_termino)"
    falta6 = sorted(sexto - vistos)
    falta5 = sorted(k for k in quinto if man.get(k) in (None, "", {}))
    det = (f"⑥ {len(sexto) - len(falta6)}/{len(sexto)} campos · "
           f"⑤ {len(quinto) - len(falta5)}/{len(quinto)} chaves")
    if falta6 or falta5:
        det += f" → FALTA ⑥{falta6} ⑤{falta5}"
    return (not (falta6 or falta5)), det


# ═══════════════════════════════════════════════════════════════════════════
#  B-15 · discriminador O-22 (footer ausente ≠ morte de máquina)
# ═══════════════════════════════════════════════════════════════════════════

def discriminador_o22(man: dict, caminho_jsonl: str) -> tuple[str, str]:
    """`('morte'|'smoke_fora_do_despachante'|'ok', detalhe)`.

    A regra O-22 ("footer ausente = morte de máquina") deu **21
    falsos-positivos** na s42 (9 com ZERO footer): eram smokes completos, com
    `fe_final==maxfe` em 666/666 e `doe_hash`/`x_hash` iguais aos irmãos de tier.
    Em 30 sementes seriam ~270 falsos alarmes ⇒ re-runs desnecessários.
    Discriminador correto: *footer do runner ausente **E** ⑤ ausente/incompleto*
    = morte; *footer ausente com ⑤ `ok` e `fe_final==maxfe`* = smoke.
    """
    tem_footer = False
    if os.path.exists(caminho_jsonl):
        with open(caminho_jsonl, "rb") as fh:
            tem_footer = any(b'"footer"' in raw for raw in fh)
    if tem_footer:
        return "ok", "footer presente"
    fe, maxfe = man.get("fe_final"), man.get("maxfe")
    completo = (man.get("status") in ("ok", "retried_ok") and fe is not None
                and maxfe is not None and int(fe) == int(maxfe))
    if completo:
        return ("smoke_fora_do_despachante",
                f"sem footer, mas ⑤ {man.get('status')} com fe_final={fe}=={maxfe} "
                f"— NÃO é morte de máquina (B-15)")
    return "morte", (f"sem footer E ⑤ incompleto (status={man.get('status')!r}, "
                     f"fe_final={fe}, maxfe={maxfe})")


# ═══════════════════════════════════════════════════════════════════════════
#  Fachada por célula + CLI
# ═══════════════════════════════════════════════════════════════════════════

def gates_de_proveniencia(exp: str, alg: str, problema: str, semente,
                          data_root: str = "data", *,
                          campanha_id=None,
                          modo: str = "campanha") -> list[tuple[str, bool | None, str]]:
    """G-1..G-4 + B-15 de UMA célula. `None` = INCONCLUSIVO/não-aplicável
    (nunca tratado como verde — a lição do falso-VERDE do B-07)."""
    from src import naming
    raiz = data_root if os.path.isabs(data_root) else os.path.join(ROOT, data_root)
    jp = naming.jsonl_path(exp, alg, problema, semente, raiz)
    mp = naming.manifest_path(exp, alg, problema, semente, raiz)
    man = {}
    if os.path.exists(mp):
        try:
            with open(mp, encoding="utf-8") as fh:
                man = json.load(fh)
        except ValueError:
            man = {}
    out = [
        ("G-1 3x1", *gate_3x1(
            naming.layer_path(exp, alg, problema, semente, "surrogate", raiz),
            naming.layer_path(exp, alg, problema, semente, "real", raiz))),
        ("G-2 sexto", *gate_unicidade_sexto(jp, alg)),
        ("G-3 proveniencia", *gate_proveniencia(man, alg, campanha_id=campanha_id,
                                                modo=modo)),
        ("G-4 camadas", *gate_gabarito_camadas(exp, alg, problema, semente, raiz)),
        ("G-7 contrato61", *gate_contrato_61(alg, jp, man)),
    ]
    veredito, det = discriminador_o22(man, jp)
    out.append(("B-15 O-22", veredito != "morte", f"{veredito}: {det}"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exp"), ap.add_argument("--alg")
    ap.add_argument("--problema"), ap.add_argument("--semente", type=int)
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--varredura", action="store_true")
    ap.add_argument("--exigir-campanha", action="store_true",
                    help="exige o campanha_id CORRENTE (default: só exige presença)")
    ap.add_argument("--historico", action="store_true",
                    help="modo AUDITORIA do passado (re-gate das 666): não cobra "
                         "campanha_id/repo_hash, que não existiam na rodada-42")
    a = ap.parse_args(argv)
    cid = None
    if a.exigir_campanha:
        from src.manifest import campanha_id_corrente
        cid = campanha_id_corrente()
    modo = "historico" if a.historico else "campanha"

    if a.varredura:
        from src import naming
        celulas = []
        raiz = (a.data_root if os.path.isabs(a.data_root)
                else os.path.join(ROOT, a.data_root))
        for mp in sorted(glob.glob(os.path.join(raiz, "experiments", "*", "*",
                                                "*.manifest.json"))):
            if "__final" in os.path.basename(mp) or "_baseline_pre_retrofit" in mp:
                continue
            try:
                with open(mp, encoding="utf-8") as fh:
                    m = json.load(fh)
            except ValueError:
                continue
            if m.get("problema") is None or m.get("semente") is None:
                continue
            celulas.append((m.get("exp"), m.get("alg"), m["problema"], m["semente"]))
    else:
        if not all([a.exp, a.alg, a.problema, a.semente is not None]):
            ap.error("modo 1-célula exige --exp --alg --problema --semente")
        celulas = [(a.exp, a.alg, a.problema, a.semente)]

    n_verm = n_inc = 0
    for exp, alg, prob, sem in celulas:
        res = gates_de_proveniencia(exp, alg, prob, sem, a.data_root,
                                    campanha_id=cid, modo=modo)
        vermelhos = [r for r in res if r[1] is False]
        incs = [r for r in res if r[1] is None]
        n_verm += len(vermelhos)
        n_inc += len(incs)
        marca = "🔴" if vermelhos else ("⚠" if incs else "✅")
        print(f"{marca} {exp}/{alg}/{prob}/s{sem}: " + " · ".join(
            f"{n}={'VERDE' if ok else ('INCONCL' if ok is None else 'FALHOU')}"
            for n, ok, _ in res))
        for n, ok, det in res:
            if ok is False:
                print(f"     🔴 {n}: {det}")
    print(f"\nPROVENIÊNCIA: {len(celulas)} células · {n_verm} vermelho(s) · "
          f"{n_inc} inconclusivo(s)/não-aplicável(is)")
    return 0 if not n_verm else 1


if __name__ == "__main__":
    raise SystemExit(main())
