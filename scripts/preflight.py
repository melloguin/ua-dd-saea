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
    """Hash determinístico do conteúdo de uma árvore de arquivos (ignora .git)."""
    h = hashlib.sha256()
    for dirpath, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for f in sorted(files):
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
            print(f"  {rid:22} content-hash {th[:12]} (sem .git próprio)")
            meta["sha256_tree"] = th
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
        # tenta localizar o arquivo (busca por basename sob a pasta do repo)
        found = None
        for dirpath, _, files in os.walk(ALGO):
            if os.path.basename(f) in files:
                found = os.path.join(dirpath, os.path.basename(f))
                break
        if not found:
            problems.append(f"anchors[{p['id']}]: arquivo '{f}' não encontrado")
            continue
        eb = p.get("expect_before", "")
        if eb and not eb.startswith("<"):  # '<...>' = descrição, não literal
            txt = open(found, errors="ignore").read()
            ok = eb in txt
            print(f"  {p['id']:22} {'OK' if ok else 'DIVERGE'}  {os.path.basename(found)}")
            if not ok:
                problems.append(f"anchors[{p['id']}]: expect_before ausente em {os.path.basename(found)}")
        else:
            print(f"  {p['id']:22} (expect descritivo — resolver no cartão)")

    # 3) placeholders
    print("\n== 3. placeholders remanescentes ==")
    for fn in ["repos.lock", "envs.json", "params.json"]:
        txt = open(os.path.join(ART, fn)).read()
        for ph in ["<SHA>", "<PIN>", "<PIN A CRAVAR"]:
            if ph in txt:
                problems.append(f"{fn}: placeholder '{ph}' pendente")

    print("\n== RESUMO ==")
    if problems:
        print(f"  {len(problems)} pendência(s):")
        for pr in problems:
            print("   -", pr)
        sys.exit(1)
    print("  pré-voo OK ✓")


if __name__ == "__main__":
    main()
