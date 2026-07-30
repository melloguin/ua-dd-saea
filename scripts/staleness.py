"""T5 — a re-auditoria de STALENESS: nenhum teste pode ser anterior ao código.

Este é o gate que a campanha não tinha e que o autor descobriu por pergunta:
um teste verde sobre código que mudou depois não vale nada. Roda como ÚLTIMO
passo, antes de declarar conformidade.
"""
import ast, os, subprocess, sys, datetime
ROOT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"; os.chdir(ROOT)

def imports(a):
    try: t=ast.parse(open(a,encoding="utf-8").read())
    except Exception: return set()
    o=set()
    for n in ast.walk(t):
        if isinstance(n,ast.ImportFrom) and n.module and n.module.startswith("src"):
            o|={x.name for x in n.names}
        elif isinstance(n,ast.Import):
            o|={x.name.split(".")[1] for x in n.names if x.name.startswith("src.")}
    return {m for m in o if os.path.exists("src/%s.py"%m)}

def fecho(m):
    v,f=set(),[m]
    while f:
        x=f.pop()
        if x in v: continue
        v.add(x); f.extend(imports("src/%s.py"%x)-v)
    return v

def ts_commit(caminho):
    r=subprocess.run(["git","log","-1","--format=%ct","--",caminho],
                     capture_output=True,text=True).stdout.strip()
    return int(r) if r else 0

RUNNER={"c122":"c122_thetadeadp","c149":"c149_lbnmobo","e81":"e81_qpots","c154":"c154_jes",
        "c262":"c262_qnehvi","b5r":"b5_prob","b5m":"b5_prob","moead_media":"piso_offline",
        "c311":"c311_tgprmo","treed_media":"treed_media","sobol_batch":"sobol_batch"}

# hora do teste = mtime do artefato que ele deixou
def hora_teste(alg):
    """A hora do smoke MAIS RECENTE daquele config.

    ⚠ A 1ª versão só olhava os JSON individuais e dava "sem smoke" para os 5
    configs cujo smoke saiu no LOTE (`smokes.log`) — escondendo justamente o
    caso que este gate existe para achar. Agora considera as duas fontes e fica
    com a mais nova; o b5m só tem a prova I-05 (`i05_par.txt`).
    """
    D=os.environ.get("T11_SCRATCH", os.path.dirname(os.path.abspath(__file__)))
    horas=[]
    for n in (f"smk2_{alg}.json", f"smk_{alg}.json"):
        c=os.path.join(D,n)
        if os.path.exists(c): horas.append(int(os.path.getmtime(c)))
    lote=os.path.join(D,"smokes.log")
    if os.path.exists(lote):
        import json as _j
        for ln in open(lote,encoding="utf-8",errors="replace"):
            if ln.startswith("{"):
                try:
                    if _j.loads(ln).get("alg")==alg:
                        horas.append(int(os.path.getmtime(lote))); break
                except Exception: pass
    if alg=="b5m":
        c=os.path.join(D,"i05_par.txt")
        if os.path.exists(c): horas.append(int(os.path.getmtime(c)))
    return max(horas) if horas else None

print("%-14s %-21s %-21s %s" % ("config","teste em","últ. mudança de dep","veredito"))
stale=[]
for alg,mod in sorted(RUNNER.items()):
    t=hora_teste(alg)
    ult=max((ts_commit("src/%s.py"%d) for d in fecho(mod)), default=0)
    fm=lambda x: datetime.datetime.fromtimestamp(x).strftime("%d/%m %H:%M:%S") if x else "—"
    if t is None:
        print("%-14s %-21s %-21s %s" % (alg,"(sem smoke nesta rodada)",fm(ult),"⚪ n/a"))
        continue
    ok = t > ult
    if not ok: stale.append(alg)
    print("%-14s %-21s %-21s %s" % (alg,fm(t),fm(ult),"✅ pós-código" if ok else "🔴 STALE"))
print()
print("STALE:",len(stale), stale if stale else "— nenhum teste é anterior ao código")
sys.exit(1 if stale else 0)
