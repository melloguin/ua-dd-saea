#!/usr/bin/env python3
"""preflight.py — checagens de pré-voo antes da Fase 0 (Higiene v5.2).

Roda a partir da raiz do repo `ua-dd-saea`. NÃO altera código de algoritmo — só:
  1. Preenche o content-hash (sha256 da árvore) de cada repo vendorizado SEM .git no repos.lock (D80).
  2. Valida que cada âncora do anchors.json aponta para um arquivo existente e que o
     `expect_before` está presente nele (o patcher abortaria se divergisse).
  3. Reporta placeholders remanescentes (<PIN>, <SHA>) nos artefatos.

Uso:  python scripts/preflight.py [--write]   (--write persiste os hashes no repos.lock)
"""
import hashlib, json, os, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART  = os.path.join(ROOT, "claude_code_context", "artifacts")
ALGO = os.path.join(ROOT, "algorithms")


def tree_sha256(path):
    """Hash determinístico do conteúdo de uma árvore de arquivos.

    Ignora `.git`, `__pycache__` e `*.pyc/*.pyo` [DI-27]: bytecode é
    gitignorado e nasce dos imports locais, então incluí-lo tornava o hash
    IRREPRODUTÍVEL num checkout limpo (a VM) e "envelhecia" o lock a cada
    import (achado da validação R3-b5/c311). [DI-34] Idem para o lixo de
    SO/editor `.DS_Store`/`.asv`/`.orig` — a metade macOS do MESMO ruído
    (achado do provisionamento F1: 8/9 hashes divergiam Mac×VM por causa
    dos .DS_Store locais; correlação 9/9 provada).
    """
    h = hashlib.sha256()
    for dirpath, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in (".git", "__pycache__"))
        for f in sorted(files):
            if f.endswith((".pyc", ".pyo", ".DS_Store", ".asv", ".orig")):
                continue
            fp = os.path.join(dirpath, f)
            rel = os.path.relpath(fp, path)
            h.update(rel.encode())
            with open(fp, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
    return h.hexdigest()


def git_head(path):
    try:
        return subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"],
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def _manifestos_forasteiros(raiz_dados=None):
    """[B-12] Manifestos em `data/experiments/**` gravados em OUTRA MÁQUINA.

    O discriminador é o HOST, não o venv: `env.executable` que aponta um caminho
    ABSOLUTO INEXISTENTE nesta máquina só pode ter sido escrito em outra. Medido
    no Mac: 58 células com `/home/jupyter/python_venvs/env_main/bin/python` (as
    VMs) são forasteiras, enquanto `env_b5`/`env_c311`/`env_e81_qpots` são venvs
    LEGÍTIMOS do próprio Mac (E-10: 230 células/semente são Mac-only) e não podem
    virar alarme.

    ⚠ O critério literal do B-12 ("`env.executable` ≠ o intérprete da máquina
    corrente") daria 304 falsos-positivos neste checkout, porque a mesma máquina
    roda 4 venvs diferentes por desenho (D79/N.1.2). O que o B-12 quer barrar é
    dado que VIAJOU no provisionamento — e isso é o host.

    Ignora o `_baseline_pre_retrofit` (intocável) e manifestos sem
    `env.executable` (o stack MATLAB não tem intérprete Python — 654 das 666
    células da s42).
    """
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from gates_proveniencia import venv_de
    # `raiz_dados` existe para o TESTE poder plantar um manifesto sintético num
    # tempdir. Antes, o teste do B-12 criava `data/experiments/_teste_b12` na
    # PRODUÇÃO a cada execução da suíte — escrita real em `data/`, proibição
    # absoluta da casa. Em produção o parâmetro fica None e nada muda.
    raiz = raiz_dados or os.path.join(ROOT, "data", "experiments")
    fora = []
    for dirpath, dirs, files in os.walk(raiz):
        dirs[:] = [d for d in dirs if d != "_baseline_pre_retrofit"]
        for f in files:
            if not f.endswith(".manifest.json") or "__final" in f:
                continue
            fp = os.path.join(dirpath, f)
            try:
                with open(fp, encoding="utf-8") as fh:
                    man = json.load(fh)
            except Exception:            # noqa: BLE001 — ilegível é outro gate
                continue
            exe = (man.get("env") or {}).get("executable")
            if not exe or not str(exe).startswith("/"):
                continue
            if not os.path.exists(str(exe)):
                fora.append((os.path.relpath(fp, ROOT), venv_de(exe)))
    return sorted(fora)


def main():
    write = "--write" in sys.argv
    problems = []

    # 1) repos.lock — pins
    print("== 1. repos.lock (pins) ==")
    lock_path = os.path.join(ART, "repos.lock")
    lock = json.load(open(lock_path))
    dir_map = {  # id no repos.lock -> pasta em algorithms/
        "c122_thetadeadp": "c122_θ-DEA-DP", "c141_mmraea": "c141_MMRAEA",
        "e74_clmea": "e74_CLMEA", "c238_eim": "c238_EIM", "e81_qpots": "e81_qPOTS",
        "c149_lbnmobo": "c149_LBN-MOBO", "b5_desdeo": "b5_Prob-RVEA", "c311_tgprmo": "c311_TGPR-MO",
        "e103_ibeams": "e103_IBEA-MS",  # e103 agora é arquivos planos (sem .git) -> content-hash
    }
    for rid, meta in lock.get("repos", {}).items():
        if not isinstance(meta, dict):
            continue
        d = dir_map.get(rid)
        if not d:
            continue
        path = os.path.join(ALGO, d)
        if not os.path.isdir(path):
            problems.append(f"repos.lock: pasta '{d}' não existe para '{rid}'")
            continue
        # só usa git HEAD se o dir tem .git PRÓPRIO (senão rev-parse pega o do repo-mãe → inútil)
        head = git_head(path) if os.path.isdir(os.path.join(path, ".git")) else None
        if head:
            print(f"  {rid:22} git HEAD {head[:12]} (.git próprio)")
            meta["sha"] = head
        else:
            th = tree_sha256(path)
            # CONFERIR, não só recalcular. Sem esta comparacao o "lacre" nao lacra
            # nada: o modo leitura imprimia o hash RECALCULADO, que por construcao
            # sempre bate com o disco, e um patch vendorizado aplicado sem re-lacre
            # passava em silencio (foi o que aconteceu com b5-pwrong-stats em
            # 2026-07-30). Sem `--write`, divergencia e PENDENCIA.
            guardado = meta.get("sha256_tree")
            if write or not guardado:
                print(f"  {rid:22} content-hash {th[:12]} (sem .git próprio)")
            elif guardado == th:
                print(f"  {rid:22} content-hash {th[:12]} LACRE OK")
            else:
                print(f"  {rid:22} content-hash {th[:12]} != lacrado {guardado[:12]} "
                      f"*** DIVERGE ***")
                problems.append(
                    f"repos.lock: '{rid}' DIVERGE do lacre (disco {th[:12]} != "
                    f"lacrado {guardado[:12]}) — a arvore vendorizada mudou sem "
                    f"re-lacre; rode `preflight.py --write` se a mudanca e legitima "
                    f"(patch de ancora) ou reverta se nao e")
            meta["sha256_tree"] = th
            meta["sha"] = None  # repo pinado por content-hash -> não há git sha (limpa o <SHA>)
    if write:
        json.dump(lock, open(lock_path, "w"), ensure_ascii=False, indent=2)
        print("  -> repos.lock atualizado (--write)")

    # 2) anchors.json — validar expect_before contra o arquivo
    print("\n== 2. anchors.json (validação) ==")
    anch = json.load(open(os.path.join(ART, "anchors.json")))
    for p in anch.get("patches", []):
        f = p.get("file", "")
        # âncoras com glob/'...' são marcadores — reportar como pendentes de resolução
        if "*" in f or "..." in f:
            problems.append(f"anchors[{p['id']}]: file não-resolvido ('{f}')")
            continue
        # localiza o arquivo: junta TODOS os candidatos por basename e prefere aquele
        # cujo caminho termina com o `file` (repo-relativo) da âncora. Sem isso, um basename
        # que colide entre libs vendorizadas (ex.: acquisition.py em _BoTorch e em e81_qPOTS)
        # resolveria para o 1º da os.walk — o arquivo errado. Fallback: 1º por basename
        # (compat com âncoras que trazem só o basename).
        base = os.path.basename(f)
        norm = f.replace("\\", "/")
        candidates = []
        for dirpath, _, files in os.walk(ALGO):
            if base in files:
                candidates.append(os.path.join(dirpath, base))
        ends = [c for c in candidates if c.replace("\\", "/").endswith(norm)]
        found = (ends or candidates or [None])[0]
        if not found:
            problems.append(f"anchors[{p['id']}]: arquivo '{f}' não encontrado")
            continue
        eb = p.get("expect_before", "")
        ea = p.get("expect_after", "")
        if eb and not eb.startswith("<"):  # '<...>' = descrição, não literal
            txt = open(found, errors="ignore").read()
            if eb in txt:                                  # árvore em estado STOCK (pré-patch)
                print(f"  {p['id']:22} STOCK    {os.path.basename(found)}")
            elif ea and not ea.startswith("<") and ea in txt:
                # [R1-c217] patch de fidelidade JÁ APLICADO in-place (a implementação
                # aplica os patches ancorados na própria árvore — R1-c217+). expect_after
                # presente = estado patchado esperado -> OK, NÃO é divergência.
                print(f"  {p['id']:22} APLICADO {os.path.basename(found)}")
            else:                                          # nem stock nem aplicado = divergência REAL
                print(f"  {p['id']:22} DIVERGE  {os.path.basename(found)}")
                problems.append(f"anchors[{p['id']}]: nem expect_before nem expect_after em {os.path.basename(found)}")
        else:
            print(f"  {p['id']:22} (expect descritivo — resolver no cartão)")

    # 3) placeholders vs deferimentos intencionais
    #    <SHA>/<PIN> = placeholder NÃO resolvido -> BLOQUEIA (pendência).
    #    '<PIN A CRAVAR ...>' = deferimento EXPLÍCITO a um gate futuro (o próprio texto diz
    #    onde será cravado, ex.: desdeo-emo no gate R3.2) -> NOTA, não bloqueia (§7.4 do handoff).
    print("\n== 3. placeholders remanescentes ==")
    HARD_PH = ["<SHA>", "<PIN>"]
    DEFER_PH = ["<PIN A CRAVAR"]
    deferrals = []
    for fn in ["repos.lock", "envs.json", "params.json"]:
        txt = open(os.path.join(ART, fn)).read()
        for ph in HARD_PH:
            if ph in txt:
                problems.append(f"{fn}: placeholder '{ph}' pendente")
        for ph in DEFER_PH:
            if ph in txt:
                deferrals.append(f"{fn}: deferimento intencional '{ph} ...>' (cravar no gate indicado)")
    for d in deferrals:
        print("  (deferido) -", d)
    if not deferrals:
        print("  (nenhum)")

    # 4) [B-12] MANIFESTO FORASTEIRO em data/experiments — o disparo não pode
    #    começar com dado de OUTRA máquina no disco desta. Padrão medido na s42:
    #    `batch/e81` não está no roster de VM nenhuma (`lote42.sh`: v5=main/c154;
    #    v6=batch/{sobol_batch,c149,c262}+main/c262; vm3=MATLAB+main/{c122,c149}+
    #    off/sweep e103; e81 é Mac-only, venv env_e81_qpots) — e as 3 VMs tinham
    #    `.jsonl` dessa célula. Uma célula cujo host real diverge do dono do
    #    roster fica sem auditoria, e o `repo_hash` do manifesto não cobre isso.
    print("\n== 4. manifestos forasteiros em data/experiments (B-12) ==")
    forasteiros = _manifestos_forasteiros()
    if forasteiros:
        for rel, venv in forasteiros[:12]:
            print(f"  FORASTEIRO {rel} (venv={venv})")
        if len(forasteiros) > 12:
            print(f"  ... +{len(forasteiros) - 12}")
        problems.append(
            f"{len(forasteiros)} manifesto(s) de OUTRA MÁQUINA em "
            f"data/experiments (`env.executable` não existe neste host) — "
            f"consolide/mova ANTES do disparo (B-12). No Mac isto acusa as "
            f"células que voltaram das VMs por rsync: elas já estão no bucket "
            f"e em resultados_experimentos, e o disco local tem de partir limpo")
    else:
        print("  (nenhum)")

    print("\n== RESUMO ==")
    if problems:
        print(f"  {len(problems)} pendência(s):")
        for pr in problems:
            print("   -", pr)
        sys.exit(1)
    if deferrals:
        print(f"  pré-voo OK ✓ ({len(deferrals)} deferimento(s) intencional(is) — ver seção 3)")
    else:
        print("  pré-voo OK ✓")


if __name__ == "__main__":
    main()
