#!/usr/bin/env bash
# =============================================================================
# lote3s.sh — disparador MULTI-SEMENTE (v3). Sucessor do lote42.sh.
#
# NOME NOVO DE PROPÓSITO: o lote42.sh pode estar EM EXECUÇÃO nesta máquina.
# Sobrescrever um script que o bash está lendo corrompe a execução. Este arquivo
# convive com aquele.
#
# O que mudou em relação ao lote42.sh (v2):
#   1. LOTE_SEEDS="42 1 2"   — várias sementes numa grade só. A ordem híbrida
#      passa a valer ENTRE sementes: tudo que é barato (nas 3 sementes) roda
#      antes de qualquer coisa cara. É isso que maximiza o nº de células com
#      3 sementes fechadas se o tempo acabar no meio.
#   2. PRÉ-FILTRO: célula com manifesto já gravado não entra na grade. O v2
#      abria um subprocesso (no MATLAB, ~20 s de startup) só pra descobrir que
#      já estava pronta. Com 1035 células no vm3 isso era ~20 min de desperdício.
#      Efeito colateral bom: TOTAL passa a ser trabalho REAL, e o % é honesto.
#   3. ETA CORRIGIDA. No v2 a ETA só creditava célula CONCLUÍDA — com fila
#      híbrida, as caras entram todas de uma vez no fim e o denominador
#      congela: foi por isso que o v5 mostrou "ETA ~260h" rodando normalmente.
#      Agora as células EM VOO são creditadas por tempo decorrido.
#   4. LOTE_PRAZO_H — depois de N horas nenhuma célula NOVA é despachada (as em
#      voo terminam). Para largar rodando e ter certeza de que parou a tempo.
#   5. LOTE_CUSTO_MAX — descarta célula que o modelo diz que não cabe.
#   6. Jitter no arranque do MATLAB — 6 MATLABs subindo juntos deram
#      segmentation violation em MatlabLicensing::getInstance (O-18/vm3).
#   7. CENSO=1 — modo leitura: classifica a grade em (1) ok (2) fila
#      (3) falhou (4) despriorizado. Não roda nada.
#
# NÃO TOCA NO REPO. A grade vem SEMPRE do runs_matrix.csv, nunca digitada.
#
# USO
#   CENSO=1 LOTE_MAQ=v5 bash lote3s.sh                 # só o censo, read-only
#   LOTE_MAQ=v5 bash lote3s.sh                         # DRY-RUN (censo + fila)
#   LOTE=CONFIRMA LOTE_MAQ=v5 bash lote3s.sh           # dispara
#
# VARIÁVEIS
#   LOTE=CONFIRMA      dispara de verdade
#   LOTE_MAQ           v5|v6|vm3|mac  (perfil: pares, jobs, bucket)
#   LOTE_SEEDS="42 1 2"   (o conjunto sancionado é 0..28 e 42 — a 30 NÃO existe)
#   LOTE_PARES         "exp/alg exp/alg ..." — sobrepõe o perfil
#   LOTE_JOBS          processos simultâneos
#   LOTE_PRAZO_H=0     0 = sem prazo (horas a contar de AGORA)
#   LOTE_PRAZO_TS      prazo ABSOLUTO (epoch). Tem precedência sobre PRAZO_H e é o
#                      certo quando se encadeia várias passadas: senão cada passada
#                      ganha um prazo novo e a última estoura o horizonte.
#   LOTE_CUSTO_MAX=0   0 = sem teto por célula (segundos) — filtro de FILA, nao chega ao run
#   LOTE_TETO_S=0      --teto-s repassado ao experiments.py (0 = default 43200 do repo).
#                      Ampliar isto ROMPE a DI-35.5 e exige decisao do autor no REGISTRO.
#   LOTE_DMAX=0        0 = sem limite; N = só problemas com D<=N. É assim que se
#                      corta o c154 nas dimensões em que ele SEMPRE aborta por
#                      projeção (D>=12) sem digitar lista de problema.
#   LOTE_REFAZER=nao|falhas|tudo   default nao
#   LOTE_BUCKET        default do perfil (1 nas VMs, 0 no mac — D80)
#   LOTE_ORDEM=hibrida|barata|cara
#   LOTE_MATLAB_JITTER=12
# =============================================================================
set -uo pipefail

SEEDS="${LOTE_SEEDS:-42 1 2}"
DATA_ROOT="${LOTE_DATA_ROOT:-data}"
ORDEM="${LOTE_ORDEM:-hibrida}"
MAQ="${LOTE_MAQ:-}"
PRAZO_H="${LOTE_PRAZO_H:-0}"
CUSTO_MAX="${LOTE_CUSTO_MAX:-0}"
DMAX="${LOTE_DMAX:-0}"
REFAZER="${LOTE_REFAZER:-nao}"
# [2026-07-28] O worker do v3.0 NAO repassava --teto-s, entao ampliar o teto
# universal (43200s, DI-35.5) exigia sair do driver e disparar experiments.py
# a mao. Fechado aqui. 0 = usa o default do experiments.py.
# ATENCAO: so vale para o stack PYTHON. O stack MATLAB nao tem teto de
# wall-clock nenhum (lacuna declarada e aceita).
TETO_S="${LOTE_TETO_S:-0}"
JITTER="${LOTE_MATLAB_JITTER:-12}"

# ── perfis · alocação ───────────────────────────────────────────────────────
# ⚠ [T13/D1 — 2026-07-31] A REGRA O-16 ("um config, uma máquina") ESTÁ APOSENTADA
# para a campanha das 30 sementes. Ela dizia: "um config NUNCA muda de máquina
# entre sementes", e a justificativa era a tabela de TEMPO do M7 (comparar wall
# entre algoritmos exige a mesma máquina). Continua válida PARA O TEMPO — e é só
# para isso que ela vale.
#
# Para o RESULTADO ela era contraproducente, e a medição mostrou por quê: rodar
# a mesma célula em máquinas diferentes diverge (medido nos 15 pares Mac×vm3:
# 7 batem bit-a-bit, 6 estouram o piso O-18 de HV ≤1,55% — e em IGD+, o endpoint
# PRIMÁRIO, o c238/MMF1 chega a 80,03%). Sob a O-16 a máquina fica CONSTANTE nas
# 30 sementes de um config ⇒ vira um offset sistemático que a mediana das 30
# **não** dilui: média dilui ruído ALEATÓRIO, não viés.
#
# Decisão do autor: alocar POR SEMENTE — cada máquina roda TODOS os pares em
# algumas sementes. Aí a máquina varia DENTRO de cada config ao longo das
# repetições, vira ruído aleatório entre elas, e a mediana das 30 dilui de fato.
#   LOTE_MAQ=<qualquer> LOTE_SEEDS="0 1 2" LOTE_PARES=todos bash lote3s.sh
# `LOTE_PARES=todos` deriva os pares do ARTEFATO (runs_matrix.csv) — nunca de
# uma lista digitada, que envelhece. Os perfis abaixo ficam como estão para
# reprodução da rodada-42; não são mais o caminho da campanha.
case "$MAQ" in
  # 12 jobs · env_main pesado que já morava aqui (c149 e c154)
  v5)  BUCKET_DEF=1; JOBS_DEF=12; PARES="main/c149" ;;
  # 6 jobs · env_main que já morava aqui
  v6)  BUCKET_DEF=1; JOBS_DEF=6;  PARES="main/c262 main/c122 batch/c149 batch/sobol_batch" ;;
  # 6 jobs · TODO o MATLAB (345 células/semente) — única máquina com licença
  vm3) BUCKET_DEF=1; JOBS_DEF=6;  PARES="main/nsga2 main/nsga3 main/moead main/smsemoa
                           main/c141 main/c217 main/b3 main/e74 main/b4 main/b1
                           main/e7 main/c238 off/e103
                           sweep-small-lhs/e103 sweep-small-mvns/e103
                           sweep-medium-lhs/e103 sweep-medium-mvns/e103" ;;
  # 4 jobs · TODO o venv-próprio (230 células/semente) — únicos venvs do projeto
  mac) BUCKET_DEF=0; JOBS_DEF=4;  PARES="off/c311 off/moead_media off/b5r off/b5m
                           main/e81 batch/e81
                           sweep-small-lhs/c311 sweep-small-mvns/c311
                           sweep-medium-lhs/c311 sweep-medium-mvns/c311
                           sweep-big-lhs/c311 sweep-big-mvns/c311
                           sweep-big-lhs/treed_media sweep-big-mvns/treed_media
                           sweep-small-lhs/moead_media sweep-small-mvns/moead_media
                           sweep-medium-lhs/moead_media sweep-medium-mvns/moead_media
                           sweep-small-lhs/b5r sweep-small-mvns/b5r
                           sweep-medium-lhs/b5r sweep-medium-mvns/b5r
                           sweep-small-lhs/b5m sweep-small-mvns/b5m
                           sweep-medium-lhs/b5m sweep-medium-mvns/b5m" ;;
  *)   BUCKET_DEF=1; JOBS_DEF=4;  PARES="" ;;
esac
PARES="${LOTE_PARES:-$PARES}"
USE_BUCKET="${LOTE_BUCKET:-$BUCKET_DEF}"
JOBS="${LOTE_JOBS:-$JOBS_DEF}"
# [T14.11] A checagem de PARES desceu para DEPOIS do mapa: uma maquina da frota
# nova (vm1..vm8) nao tem perfil no `case` acima e recebe os pares do ARTEFATO —
# abortar aqui a mataria antes de o mapa ser lido.

# ── repo / interpretador / MATLAB ───────────────────────────────────────────
REPO=""
for c in "$HOME/ua-dd-saea" "$HOME/Documents/python_repos/mestrado/ua-dd-saea" \
         "/home/jupyter/ua-dd-saea"; do
  [ -d "$c/.git" ] && REPO="$c" && break
done
[ -n "$REPO" ] || { echo "FATAL: repo nao encontrado"; exit 2; }

PY=""
for c in "$HOME/venvs/env_main/bin/python" "$HOME/python_venvs/env_main/bin/python" \
         "$HOME/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python" \
         "/home/jupyter/python_venvs/env_main/bin/python"; do
  [ -x "$c" ] && PY="$c" && break
done

MAT=""
for c in "/Applications/MATLAB_R2025a.app/bin/matlab" "/usr/local/MATLAB/R2025a/bin/matlab" \
         "$(command -v matlab 2>/dev/null)"; do
  [ -n "$c" ] && [ -x "$c" ] && MAT="$c" && break
done

cd "$REPO" || exit 2

# [T13/C4] `LOTE_PARES=todos` = o roster COMPLETO, DERIVADO do artefato do grid.
# É o modo da campanha por semente: a máquina roda TUDO e o recorte é a semente.
# Derivar (em vez de digitar 51 pares) é o que impede a lista de envelhecer em
# silêncio quando o grid mudar. Depende do `cd "$REPO"` acima — por isso mora
# aqui e não junto do `case $MAQ`.
if [ "$PARES" = "todos" ]; then
  PARES="$("${PY:-python3}" -c "
import csv
with open('claude_code_context/artifacts/runs_matrix.csv', encoding='utf-8') as fh:
    pares = sorted({(r['exp'], r['alg']) for r in csv.DictReader(fh)})
print(' '.join('%s/%s' % e for e in pares))")"
  [ -n "$PARES" ] || { echo "FATAL: LOTE_PARES=todos nao derivou par do runs_matrix.csv"; exit 2; }
fi

# [T14.11] MAPA SEMENTE->MAQUINA. Se o artefato existe e LOTE_MAQ esta setado,
# as SEMENTES e os PARES desta maquina saem DELE — nao da linha de comando.
# O mapa e por GRUPO de elegibilidade (stack/env), entao uma maquina pode ter
# sementes diferentes para MATLAB e para Python: por isso alem de SEEDS/PARES
# sai tambem um ALLOWLIST de (exp,alg,semente), que e o recorte de verdade.
# LOTE_MAPA=0 desliga (volta ao modo manual); LOTE_SEEDS explicito tem prioridade.
MAPA_JSON="claude_code_context/artifacts/mapa_sementes.json"
MAPA_ALLOW=""
if [ "${LOTE_MAPA:-1}" != "0" ] && [ -n "$MAQ" ] && [ -f "$MAPA_JSON" ] \
   && [ -z "${LOTE_SEEDS:-}" ]; then
  MAPA_ALLOW="$(mktemp -t lote3s_mapa)"
  MAPA_OUT="$("${PY:-python3}" - "$MAPA_JSON" "$MAQ" "$MAPA_ALLOW" <<'PYMAPA'
import json, sys
mapa, maq, saida = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(mapa, encoding="utf-8"))
seeds, pares, linhas = set(), set(), []
for g in d["mapas"].values():
    meus = g["sementes_por_maquina"].get(maq) or []
    if not meus:
        continue
    seeds.update(meus)
    pares.update(g["pares"])
    for par in g["pares"]:
        exp, alg = par.split("/", 1)
        for s in meus:
            linhas.append("%s %s %s" % (exp, alg, s))
with open(saida, "w", encoding="utf-8") as fh:
    fh.write("\n".join(sorted(linhas)) + ("\n" if linhas else ""))
print(" ".join(str(s) for s in sorted(seeds)))
print(" ".join(sorted(pares)))
print(len(linhas))
PYMAPA
)"
  if [ -n "$MAPA_OUT" ]; then
    SEEDS="$(printf '%s\n' "$MAPA_OUT" | sed -n 1p)"
    PARES="$(printf '%s\n' "$MAPA_OUT" | sed -n 2p)"
    NMAPA="$(printf '%s\n' "$MAPA_OUT" | sed -n 3p)"
    if [ -z "$SEEDS" ]; then
      echo "FATAL: '$MAQ' nao aparece em $MAPA_JSON."
      echo "   Maquinas do mapa: $("${PY:-python3}" -c \
        "import json,sys;d=json.load(open('$MAPA_JSON'));print(' '.join(sorted(d['resumo']['wall_por_maquina_h'])))")"
      echo "   Use LOTE_MAPA=0 para o modo manual."
      exit 2
    fi
    echo "── MAPA T14.11: $MAQ recebeu $NMAPA celulas-semente do artefato"
  else
    rm -f "$MAPA_ALLOW"; MAPA_ALLOW=""
  fi
fi
[ -n "$PARES" ] || { echo "FATAL: defina LOTE_MAQ (uma maquina do mapa, ou \
v5|v6|vm3|mac) ou LOTE_PARES"; exit 2; }

# ── pino de thread: 1 core por run (D79 / envs.json thread_pin / O-15) ──────
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
       NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONHASHSEED=0

OUT="/tmp/lote3s_${MAQ:-custom}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT/logs"
GRID="$OUT/grid.txt"; DONE="$OUT/done.txt"; INI="$OUT/inicio.txt"; CENSOTXT="$OUT/censo.txt"
: > "$DONE"; : > "$INI"

# ── grade + censo, a partir do ARTEFATO ─────────────────────────────────────
{
python3 - "$REPO" "$SEEDS" "$PARES" "$ORDEM" "$DATA_ROOT" "$CUSTO_MAX" "$REFAZER" \
         "$CENSOTXT" "$DMAX" "$MAPA_ALLOW" > "$GRID" <<'PYEOF'
import csv, sys, os, math, json, collections
repo, seeds, pares, ordem, droot, cmax, refazer, censo_out, dmax = sys.argv[1:10]
mapa_allow = sys.argv[10] if len(sys.argv) > 10 else ""
dmax = int(dmax)
# [T14.11] o recorte de VERDADE da maquina: (exp,alg,semente). Sem ele, SEEDS x
# PARES cruzaria sementes de MATLAB com pares de Python (a maquina tem um
# conjunto de sementes POR GRUPO de elegibilidade, nao um so).
ALLOW = None
if mapa_allow and os.path.exists(mapa_allow):
    ALLOW = set()
    with open(mapa_allow, encoding="utf-8") as fh:
        for ln in fh:
            t = ln.split()
            if len(t) == 3:
                ALLOW.add((t[0], t[1], t[2]))
seeds = seeds.split()
alvo  = {tuple(p.split("/", 1)) for p in pares.split()}
cmax  = float(cmax)
A = os.path.join(repo, "claude_code_context", "artifacts")
D = {r["problema"]: int(r["D"]) for r in
     csv.DictReader(open(os.path.join(A, "characteristics.csv"), encoding="utf-8"))}

# modelo de custo: interpolação log-log entre walls MEDIDOS. Só ordena a fila e
# estima ETA — nunca entra em resultado.
ANC = {"b1":{61:14,371:165,929:2014}, "b3":{61:4,371:40,929:537},
       "b4":{61:41,371:196,929:883},  "c122":{371:709,929:5054},
       "c141":{61:1,371:18,929:169},  "c149":{61:239,371:2632,929:12107},
       "c154":{61:95,371:52596},      "c217":{371:49,929:132},
       "c238":{61:6,371:610,929:14100},
       "c262":{61:34,371:8972,929:15051}, "e103":{61:7,371:10,929:35},
       "e7":{61:317,371:1818,929:4320},
       "e74":{61:21,371:258,929:469}, "e81":{61:10,371:549,929:7167},
       "moead":{61:1,929:1},"nsga2":{61:1,929:1},"nsga3":{61:1,929:1},
       "smsemoa":{61:1,929:1}}
OFF  = {"b5m":2826,"b5r":306,"c311":41,"moead_media":63,"e103":10,"treed_media":9}
TIER = {"small":0.35,"medium":1.10,"big":1.40}
BAT  = {"c149":6972,"e81":2077,"sobol_batch":2,"c262":14400}
TETO, ABORTO = 43200.0, 22632.0

def por_fe(alg, fe):
    a = ANC.get(alg)
    if not a: return 600.0
    p = sorted(a)
    if len(p) == 1: return a[p[0]] * (fe / p[0]) ** 1.5
    if   fe <= p[0]:  lo, hi = p[0], p[1]
    elif fe >= p[-1]: lo, hi = p[-2], p[-1]
    else:
        i = max(j for j in range(len(p) - 1) if p[j] <= fe); lo, hi = p[i], p[i + 1]
    b = (math.log(a[hi]) - math.log(a[lo])) / (math.log(hi) - math.log(lo))
    return a[lo] * (fe / lo) ** b

def custo(exp, alg, prob):
    if exp == "batch": return BAT.get(alg, 3600.0)
    if exp.startswith("sweep-"):
        return OFF.get(alg, 600.0) * TIER.get(exp.split("-")[1], 1.0)
    if exp == "off":   return OFF.get(alg, 600.0)
    fe = 31 * D[prob] - 1
    v = por_fe(alg, fe)
    if alg == "c154" and fe >= 371: v = ABORTO
    return min(v, TETO)

def estado(exp, alg, prob, s):
    p = os.path.join(repo, droot, "experiments", exp, alg,
                     "exp_%s_%s_%s_%s.manifest.json" % (exp, alg, prob, s))
    if not os.path.exists(p): return "ausente", ""
    try: m = json.load(open(p, encoding="utf-8"))
    except Exception: return "ilegivel", ""
    st = m.get("status")
    if st in ("ok", "retried_ok"): return "ok", ""
    mot = str(m.get("motivo_parada") or "")
    if mot == "teto_wall": return "abortou", mot
    tr = (m.get("stack_trace") or "").strip().splitlines()
    return "FALHOU", (tr[-1][:90] if tr else mot or "?")

todas = list(csv.DictReader(open(os.path.join(A, "runs_matrix.csv"), encoding="utf-8")))

# GUARDA: semente que não existe na matriz entraria muda e a grade sairia menor
# do que se pensa. O conjunto sancionado é {0..28, 42} (30 réplicas, SPEC/M8).
disp = {r["semente"] for r in todas}
faltam = [s for s in seeds if s not in disp]
if faltam:
    sys.stderr.write("SEMENTE_INEXISTENTE %s\n" % ",".join(faltam))
    sys.exit(3)

# ── CENSO (semente 42, roster desta máquina) ────────────────────────────────
cen = collections.Counter(); cen_fam = collections.defaultdict(collections.Counter)
falhas = []
DI40 = 0
for r in todas:
    if r["semente"] != "42" or (r["exp"], r["alg"]) not in alvo: continue
    fam = ("main" if r["exp"] == "main" else "off" if r["exp"] == "off"
           else "batch" if r["exp"] == "batch" else "sweep")
    if r["exp"] == "batch" and r["alg"] == "c154":
        cen["despriorizado"] += 1; cen_fam[fam]["despriorizado"] += 1; DI40 += 1; continue
    e, det = estado(r["exp"], r["alg"], r["problema"], "42")
    k = {"ok":"ok", "abortou":"despriorizado", "FALHOU":"falhou",
         "ausente":"fila", "ilegivel":"falhou"}[e]
    cen[k] += 1; cen_fam[fam][k] += 1
    if k == "falhou": falhas.append((r["exp"], r["alg"], r["problema"], det))
with open(censo_out, "w", encoding="utf-8") as fh:
    fh.write("%-8s %6s %6s %6s %6s %6s\n" % ("familia","total","ok","fila","falhou","desprio"))
    for fam in ("main","off","sweep","batch"):
        d = cen_fam.get(fam)
        if not d: continue
        fh.write("%-8s %6d %6d %6d %6d %6d\n" % (fam, sum(d.values()),
                 d["ok"], d["fila"], d["falhou"], d["despriorizado"]))
    fh.write("%-8s %6d %6d %6d %6d %6d\n" % ("TOTAL", sum(cen.values()),
             cen["ok"], cen["fila"], cen["falhou"], cen["despriorizado"]))
    if DI40: fh.write("(inclui %d de batch/c154 fora por DI-40)\n" % DI40)
    for exp, alg, prob, det in falhas:
        fh.write("FALHOU %s/%s/%s :: %s\n" % (exp, alg, prob, det))

# ── grade a rodar ───────────────────────────────────────────────────────────
srank = {s: i for i, s in enumerate(seeds)}
linhas, jaok, caras = [], 0, 0
for r in todas:
    if r["semente"] not in srank or (r["exp"], r["alg"]) not in alvo: continue
    if ALLOW is not None and (r["exp"], r["alg"], r["semente"]) not in ALLOW:
        continue                                                   # [T14.11]
    if r["exp"] == "batch" and r["alg"] == "c154": continue        # DI-40
    e, _ = estado(r["exp"], r["alg"], r["problema"], r["semente"])
    if refazer == "nao"    and e != "ausente":                 jaok += 1; continue
    if refazer == "falhas" and e in ("ok", "abortou"):         jaok += 1; continue
    c = custo(r["exp"], r["alg"], r["problema"])
    if dmax > 0 and D[r["problema"]] > dmax:                    caras += 1; continue
    if cmax > 0 and c > cmax:                                  caras += 1; continue
    linhas.append((c, srank[r["semente"]], r["exp"], r["alg"], r["problema"],
                   r["semente"], r["stack"]))
LIM = 900.0
if   ordem == "barata": linhas.sort()
elif ordem == "cara":   linhas.sort(reverse=True)
else:
    linhas = sorted([l for l in linhas if l[0] <  LIM]) + \
             sorted([l for l in linhas if l[0] >= LIM], key=lambda l: (-l[0], l[1]))
for c, _, e, a, p, s, st in linhas:
    print("%s %s %s %s %s %.0f" % (e, a, p, s, st, c))
sys.stderr.write("PREFILTRO %d %d\n" % (jaok, caras))
PYEOF
PYRC=$?
} 2>"$OUT/pre.txt"
if [ "$PYRC" -ne 0 ]; then
  if grep -q SEMENTE_INEXISTENTE "$OUT/pre.txt" 2>/dev/null; then
    echo "FATAL: semente pedida não existe no runs_matrix.csv:"
    sed 's/SEMENTE_INEXISTENTE/   ->/' "$OUT/pre.txt"
    echo "   O conjunto sancionado é 0..28 e 42 (30 réplicas). Escolha dentro dele."
  else
    echo "FATAL: falha ao montar a grade (python rc=$PYRC)"; cat "$OUT/pre.txt"
  fi
  exit 2
fi
JAOK=$(awk '/^PREFILTRO/{print $2}' "$OUT/pre.txt"); JAOK="${JAOK:-0}"
CARAS=$(awk '/^PREFILTRO/{print $3}' "$OUT/pre.txt"); CARAS="${CARAS:-0}"

TOTAL=$(wc -l < "$GRID" | tr -d ' ')
CUSTO_TOT=$(awk '{s+=$6} END{printf "%.0f", s+0}' "$GRID")
NPY=$(awk '$5=="python"' "$GRID" | wc -l | tr -d ' ')
NML=$(awk '$5=="matlab"' "$GRID" | wc -l | tr -d ' ')

echo "════════════════════════════════════════════════════════════════════════"
echo " LOTE v3 · máquina=${MAQ:-custom} · sementes=$(echo $SEEDS | tr ' ' ',') · $JOBS processos"
echo " repo=$REPO"
echo " python=${PY:-<ausente>}   matlab=${MAT:-<ausente>}"
echo
echo "── CENSO da semente 42 no roster desta máquina (read-only)"
sed 's/^/   /' "$CENSOTXT"
echo
echo "── A RODAR AGORA (sementes $(echo $SEEDS | tr ' ' ',') · só o que não tem manifesto)"
echo "   células: $TOTAL   (python $NPY · matlab $NML)"
echo "   fora da grade: $JAOK já tinham manifesto · $CARAS descartadas por custo/dimensão"
HCORE=$(awk -v c="$CUSTO_TOT" 'BEGIN{printf "%.1f", c/3600}' </dev/null)
MKSP=$(awk -v c="$CUSTO_TOT" -v j="$JOBS" 'BEGIN{printf "%.1f", c/3600/j}' </dev/null)
printf  "   custo estimado: %s h-core  ->  makespan previsto ~%s h\n" "$HCORE" "$MKSP"
echo "   bucket: $([ "$USE_BUCKET" = 1 ] && echo LIGADO || echo desligado)"
[ "$TETO_S" != "0" ] && echo "   ⚠ --teto-s=${TETO_S}s (o default do repo e 43200 — DI-35.5)"
if [ -n "${LOTE_PRAZO_TS:-}" ] && [ "${LOTE_PRAZO_TS:-0}" != "0" ]; then
  _dt=$(date -r "$LOTE_PRAZO_TS" '+%d/%m %H:%M' 2>/dev/null) \
    || _dt=$(date -d "@$LOTE_PRAZO_TS" '+%d/%m %H:%M' 2>/dev/null) || _dt="epoch $LOTE_PRAZO_TS"
  echo "   prazo ABSOLUTO: nada novo é despachado depois de $_dt"
elif [ "$PRAZO_H" != "0" ]; then
  echo "   prazo: nada novo é despachado depois de ${PRAZO_H}h"
fi
[ "$CUSTO_MAX" != "0" ] && echo "   teto por célula: ${CUSTO_MAX}s (acima disso, descartada)"
[ "$DMAX" != "0" ] && echo "   só problemas com D<=${DMAX}"
echo "   logs: $OUT/logs/"
echo "════════════════════════════════════════════════════════════════════════"

if [ "${CENSO:-}" = "1" ]; then exit 0; fi
[ "$TOTAL" -gt 0 ] && : || { echo "grade VAZIA — ou está tudo pronto, ou LOTE_PARES está errado."; exit 0; }
[ "$NPY" -eq 0 ] || [ -n "$PY" ]  || { echo "FATAL: há células python e nenhum env_main."; exit 2; }
[ "$NML" -eq 0 ] || [ -n "$MAT" ] || { echo "FATAL: há células matlab e nenhum MATLAB."; exit 2; }

if [ "${LOTE:-}" != "CONFIRMA" ]; then
  echo; echo "DRY-RUN. Para disparar:  LOTE=CONFIRMA LOTE_MAQ=$MAQ bash $0"
  echo; echo "12 PRIMEIRAS da fila:"
  head -12 "$GRID" | awk '{printf "      %-19s %-12s %-11s sem=%-3s %-7s ~%6.1f min\n",$1,$2,$3,$4,$5,$6/60}'
  echo "      ..."
  echo "5 ÚLTIMAS da fila:"
  tail -5  "$GRID" | awk '{printf "      %-19s %-12s %-11s sem=%-3s %-7s ~%6.1f min\n",$1,$2,$3,$4,$5,$6/60}'
  echo
  echo "célula mais cara:"
  sort -k6 -n -r "$GRID" | head -1 | awk '{printf "      %-19s %-12s %-11s sem=%s ~%.1f h\n",$1,$2,$3,$4,$6/3600}'
  exit 0
fi

# ── worker: UMA célula por processo ─────────────────────────────────────────
T0=$(date +%s)
FIMTS="${LOTE_PRAZO_TS:-0}"
if [ "$FIMTS" = "0" ] && [ "$PRAZO_H" != "0" ]; then
  FIMTS=$(awk -v t="$T0" -v h="$PRAZO_H" 'BEGIN{printf "%.0f", t+h*3600}' </dev/null)
fi

BFLAG=""; [ "$USE_BUCKET" = "1" ] && BFLAG="--enable-bucket"
TFLAG=""; [ "$TETO_S" != "0" ] && TFLAG="--teto-s $TETO_S"
cat > "$OUT/worker.sh" <<WEOF
#!/usr/bin/env bash
EXP="\$1"; ALG="\$2"; PROB="\$3"; SEM="\$4"; STACK="\$5"; CUSTO="\$6"
AGORA=\$(date +%s)
if [ "$FIMTS" -gt 0 ] && [ "\$AGORA" -ge "$FIMTS" ]; then
  printf '%s %s %s %s %s %s\n' "\$EXP" "\$ALG" "\$PROB" "\$SEM" prazo 0 >> "$DONE"; exit 0
fi
printf '%s %s %s %s %s %s\n' "\$EXP" "\$ALG" "\$PROB" "\$SEM" "\$AGORA" "\$CUSTO" >> "$INI"
LOG="$OUT/logs/\${EXP}__\${ALG}__\${PROB}__\${SEM}.log"
MAN="$DATA_ROOT/experiments/\${EXP}/\${ALG}/exp_\${EXP}_\${ALG}_\${PROB}_\${SEM}.manifest.json"
cd "$REPO" || exit 1
_mtime(){                      # mtime portável: GNU (-c %Y) ou BSD/macOS (-f %m)
  _m=\$(stat -c %Y "\$1" 2>/dev/null) || _m=""
  case "\$_m" in ''|*[!0-9]*) _m=\$(stat -f %m "\$1" 2>/dev/null) || _m="";; esac
  case "\$_m" in ''|*[!0-9]*) _m=0;; esac
  printf '%s' "\$_m"; }
ANTES=0; [ -f "\$MAN" ] && ANTES=\$(_mtime "\$MAN")
if [ "\$STACK" = "matlab" ]; then
  # 6 MATLABs subindo no mesmo instante deram segmentation violation no
  # MatlabLicensing::getInstance (vm3, O-18). O jitter desempilha o arranque.
  [ "$JITTER" -gt 0 ] && sleep \$(( RANDOM % $JITTER ))
  "$MAT" -batch "maxNumCompThreads(1); experiments('algorithms',{'\$ALG'},'problems',{'\$PROB'},'seeds',\$SEM,'exp','\$EXP','dataRoot','$DATA_ROOT','parallel',false)" > "\$LOG" 2>&1
else
  "$PY" experiments.py --exp "\$EXP" --algorithms "\$ALG" --problems "\$PROB" \\
        --seeds "\$SEM" --n-jobs 1 --data-root "$DATA_ROOT" $BFLAG $TFLAG > "\$LOG" 2>&1
fi
DEPOIS=0; [ -f "\$MAN" ] && DEPOIS=\$(_mtime "\$MAN")
if [ ! -f "\$MAN" ]; then
  ST=sem-manifesto
elif [ "\$ANTES" = "\$DEPOIS" ] && [ "\$ANTES" != "0" ]; then
  ST=pulou
else
  ST=\$(python3 -c "
import json,sys
try: print(json.load(open(sys.argv[1],encoding='utf-8')).get('status','?'))
except Exception: print('ilegivel')" "\$MAN")
fi
printf '%s %s %s %s %s %s\n' "\$EXP" "\$ALG" "\$PROB" "\$SEM" "\$ST" "\$CUSTO" >> "$DONE"
WEOF
chmod +x "$OUT/worker.sh"

# ── disparo + contador ao vivo ──────────────────────────────────────────────
FIM="$OUT/FIM"; rm -f "$FIM"
( xargs -P "$JOBS" -n6 "$OUT/worker.sh" < "$GRID"; : > "$FIM" ) &
XPID=$!

barra() {  # $1 = fração 0..1
  awk -v f="$1" 'BEGIN{n=int(f*28+0.5); s="";
    for(i=0;i<28;i++) s = s (i<n ? "█" : "░"); printf "%s", s}' </dev/null
}
placar() {
  # ATENÇÃO (macOS bash 3.2): nada de aspas duplas aninhadas dentro de $( ).
  # O bash 3.2 perde as internas, a chave do awk vira brace expansion, o awk
  # perde o programa e TRAVA lendo stdin. Todo valor entra por -v, todo
  # programa é aspa SIMPLES, todo awk BEGIN tem </dev/null.
  D=$(wc -l < "$DONE" | tr -d ' ')
  OK=$(awk '$5=="ok"||$5=="retried_ok"' "$DONE" | wc -l | tr -d ' ')
  FA=$(awk '$5=="failed"' "$DONE" | wc -l | tr -d ' ')
  SM=$(awk '$5=="sem-manifesto"' "$DONE" | wc -l | tr -d ' ')
  NW=$(date +%s); EL=$(( NW - T0 ))
  # custo creditado = concluídas + EM VOO por tempo decorrido (teto 95% do custo)
  CF=$(awk -v now="$NW" -v df="$DONE" '
        FILENAME==df { d[$1"/"$2"/"$3"/"$4]=1; s+=$6; next }
        { k=$1"/"$2"/"$3"/"$4;
          if (!(k in d)) { e=now-$5; m=$6*0.95; if (e>m) e=m; if (e>0) s+=e } }
        END { printf "%.0f", s+0 }' "$DONE" "$INI")
  FR=$(awk -v d="$D" -v t="$TOTAL" 'BEGIN{printf "%.4f", (t>0 ? d/t : 0)}' </dev/null)
  PC=$(awk -v d="$D" -v t="$TOTAL" 'BEGIN{printf "%.1f", (t>0 ? 100*d/t : 0)}' </dev/null)
  BA=$(barra "$FR")
  ET="--"
  if [ "${CF:-0}" -gt 0 ] && [ "$EL" -gt 60 ]; then
    ET=$(awk -v tot="$CUSTO_TOT" -v cf="$CF" -v el="$EL" \
         'BEGIN{r=(tot-cf)/cf*el; if(r<0) r=0; printf "%02dh%02dm", r/3600, (r%3600)/60}' </dev/null)
  fi
  printf '\r  [%s] %s/%s (%s%%) - ok=%s falhou=%s s/man=%s - %02dh%02dm - ETA ~%s   ' \
    "$BA" "$D" "$TOTAL" "$PC" "$OK" "$FA" "$SM" $((EL/3600)) $(((EL%3600)/60)) "$ET"
}

while : ; do
  placar
  [ -f "$FIM" ] && break
  sleep 15
done
wait "$XPID" 2>/dev/null; placar

D=$(wc -l < "$DONE" | tr -d ' ')
OK=$(awk '$5=="ok"||$5=="retried_ok"' "$DONE" | wc -l | tr -d ' ')
FA=$(awk '$5=="failed"' "$DONE" | wc -l | tr -d ' ')
SM=$(awk '$5=="sem-manifesto"' "$DONE" | wc -l | tr -d ' ')
PZ=$(awk '$5=="prazo"' "$DONE" | wc -l | tr -d ' ')
EL=$(( $(date +%s) - T0 ))
printf '\n\n════ FIM · %d/%d · ok=%d falhou=%d sem-manifesto=%d nao-despachadas(prazo)=%d · %02dh%02dm\n' \
       "$D" "$TOTAL" "$OK" "$FA" "$SM" "$PZ" $((EL/3600)) $(((EL%3600)/60))
if [ "$FA" -gt 0 ]; then
  echo "── status failed (log em $OUT/logs/):"
  awk '$5=="failed"{print "   "$1"/"$2"/"$3" sem="$4}' "$DONE"
fi
if [ "$SM" -gt 0 ]; then
  echo "── SEM MANIFESTO (processo morreu antes de gravar; no MATLAB costuma ser"
  echo "   a corrida de licença). Rode o MESMO comando de novo: a grade já"
  echo "   exclui o que ficou pronto, então a 2ª passada só pega estas."
  awk '$5=="sem-manifesto"{print "   "$1"/"$2"/"$3" sem="$4}' "$DONE"
fi
echo "detalhe: $DONE"
