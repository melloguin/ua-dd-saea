# -*- coding: utf-8 -*-
"""Constrói o catálogo v2 (aditivo) e o arquivo-companheiro de achados transversais."""
import json, glob, os, re, collections, sys
sys.path.insert(0, '/home/claude/mineracao')
from scores import SCORES, COMPLEMENTOS, CRITERIOS_27
from novas_fichas import NOVAS

BASE = '/home/claude/mineracao'
CAT_IN = '/home/claude/catalogo_analises_cap5.md'
CAT_OUT = '/home/claude/catalogo_analises_cap5.md'
COMP_OUT = '/home/claude/mineracao_definitiva_transversais_06-09-2026.md'
DATA = '06/09/2026'

ids = sorted(os.path.basename(p)[:-5] for p in glob.glob(f'{BASE}/json/*.json'))
meta = json.load(open(f'{BASE}/meta.json'))
J = {i: json.load(open(f'{BASE}/json/{i}.json')) for i in ids}
refs = {int(k): v for k, v in json.load(open(f'{BASE}/refs_full.json')).items()}
novmap = {int(k): v for k, v in json.load(open(f'{BASE}/novas_map.json')).items()}
novas_full = json.load(open(f'{BASE}/novas_full.json'))
GRP38 = "b1 b13 b14 b15 b2 b3 b4 b5 b7 b9 c1 c10 c100 c105 c106 c107 c154 c24 c241 c262 c29 c45 c48 c49 c50 c59 c65 c66 c71 c81 c82 c91 c97 e103 e104 e17 e7 e86".split()
R7 = "c122 c141 c149 c217 c238 e74 e81".split()
N27 = "mtm4 c75 mtm6 jin3 c250 e9 c222 c214 c276 b8 pp6 e3 e4 c261 c123 e102 c131 e40 emo1 e1 e64 e8 e21 e16 f9 wang4 c267".split()
assert len(set(GRP38 + R7 + N27)) == 72 and set(GRP38 + R7 + N27) == set(ids)

def grupo_art(i):
    return '38' if i in GRP38 else ('R7' if i in R7 else '27')

def trunc(s, n=150):
    s = (s or '').replace('\n', ' ').strip()
    if len(s) <= n: return s
    cut = s[:n].rsplit(' ', 1)[0]
    return cut + '…'

def stats(f):
    L = refs.get(f, [])
    arts = sorted(set(e['id'] for e in L))
    return dict(n_an=len(L), n_art=len(arts), n38=sum(a in GRP38 for a in arts), n7=sum(a in R7 for a in arts),
                n27=sum(a in N27 for a in arts), nr=sum(meta[a]['roster'] for a in arts), arts=arts)

def ref_block(f):
    L = refs.get(f, [])
    s = stats(f)
    if not L:
        return (f"**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — "
                f"leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.")
    byart = collections.OrderedDict()
    for e in L: byart.setdefault(e['id'], []).append(e)
    head = (f"**Referências no corpus (mineração definitiva, 72 artigos): {s['n_art']} artigos / {s['n_an']} análises** — "
            f"dos 38 iniciais: {s['n38']} · dos 7 do roster minerados agora: {s['n7']} · dos 27 complementares: {s['n27']} · "
            f"artigos do roster (15): {s['nr']}.")
    lines = [head, '']
    for a, es in byart.items():
        m = meta[a]
        tag = f"{m['sigla']}, {m['ano']}" + ("; roster" if m['roster'] else "")
        parts = []
        for e in es:
            if e.get('nova'):
                desc = f"[nova] {trunc(e.get('nome_sugerido') or e.get('descricao'), 120)}"
            else:
                desc = trunc(e.get('descricao'), 150)
            parts.append(f"{trunc(e.get('localizador'), 90)} — {desc}")
        lines.append(f"- **{a}** ({tag}): " + " · ".join(parts))
    return '\n'.join(lines)

def score_block(f):
    sc, just = SCORES[f]
    return f"**Score (0–10): {sc}.** **Justificativa.** {just}"

def adendo_existente(f):
    out = [f"**Adendo {DATA} — mineração definitiva (72 artigos).**", '', ref_block(f), '']
    if f in COMPLEMENTOS:
        out += [f"**Complementos e correções ({DATA}).** {COMPLEMENTOS[f]}", '']
    if f in (15, 63, 64):
        out += [f"**Diretriz (1) de {DATA}.** Sem novos experimentos: esta candidata está **DESCARTADA** (permanece no catálogo como registro; é citada em 61 como limitação).", '']
    out += [score_block(f)]
    return '\n'.join(out)

def ficha_nova(f):
    d = NOVAS[f]; s = stats(f)
    n = s['n_art']
    emq = (f"**Em quantos artigos aparece (dos 72).** {n} artigos ({s['n_an']} análises): dos 38 iniciais {s['n38']}, dos 7 do roster {s['n7']}, "
           f"dos 27 complementares {s['n27']}; do roster (15): {s['nr']}. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.")
    parts = [f"### {f}. {d['nome']}", '',
             f"**Fontes.** {d['fontes']}", '',
             f"**O que analisa.** {d['o_que']}", '',
             f"**Dados.** {d['dados']}", '',
             f"**Objetivo.** {d['objetivo']}", '',
             f"**O que busca revelar.** {d['revela']}", '',
             f"**Como é realizada.** {d['como']}", '',
             f"**Técnicas.** {d['tecnicas']}", '',
             f"**Implementação.** {d['impl']}", '',
             emq, '',
             f"**Estado.** {d['estado']}", '',
             f"**Demais detalhes.** {d['detalhes']}", '',
             f"**Adendo {DATA} — mineração definitiva (72 artigos).**", '', ref_block(f), '', score_block(f)]
    return '\n'.join(parts)

# ---------- parse catálogo v1 ----------
cat = open(CAT_IN, encoding='utf-8').read()
assert '**Versão 1 · 06/09/2026 · 64 candidatas**' in cat
lines = cat.split('\n')
# locate ficha headers
hdr_idx = [(k, int(m.group(1))) for k, l in enumerate(lines) if (m := re.match(r'^### (\d+)\. ', l))]
titles = {int(m.group(1)): m.group(2).strip() for l in lines if (m := re.match(r'^### (\d+)\. (.*)$', l))}
assert len(hdr_idx) == 64
# boundaries: ficha body ends at next '### ' header or at a line starting with '---' or '# ' (group/anexo)
ends = {}
for j, (k, f) in enumerate(hdr_idx):
    end = len(lines)
    for t in range(k + 1, len(lines)):
        if lines[t].startswith('### ') or lines[t].startswith('# ') or lines[t].strip() == '---':
            end = t; break
    # trim trailing blank lines
    while end > k and lines[end - 1].strip() == '': end -= 1
    ends[f] = (k, end)
# group end positions: index of the '---' line that precedes '# Grupo X' / '# Anexo 1'
grp_lines = [(k, l) for k, l in enumerate(lines) if l.startswith('# Grupo ') or l.startswith('# Anexo 1')]
grp_letters = [re.match(r'# Grupo ([A-J])', l).group(1) for k, l in grp_lines if l.startswith('# Grupo ')]
assert grp_letters == list('ABCDEFGHIJ')
# end of group X = line index of '---' just before the next '# Grupo'/'# Anexo 1'
grp_end = {}
for gi, (k, l) in enumerate(grp_lines):
    if not l.startswith('# Grupo '): continue
    nxt = grp_lines[gi + 1][0]
    t = nxt
    while t > k and lines[t].strip() != '---': t -= 1
    assert lines[t].strip() == '---'
    grp_end[grp_letters[gi]] = t

# ---------- assemble insertions ----------
ins = collections.defaultdict(list)  # line index -> list of text blocks to insert BEFORE that line
for f in range(1, 65):
    k, end = ends[f]
    ins[end].append('\n' + adendo_existente(f) + '\n')
for f in range(65, 82):
    g = NOVAS[f]['grupo']
    ins[grp_end[g]].append('\n' + ficha_nova(f) + '\n')

# header addendum after version line
ver_idx = next(k for k, l in enumerate(lines) if l.startswith('**Versão 1 · 06/09/2026 · 64 candidatas**'))
# the version paragraph spans ver_idx..(first blank line)
t = ver_idx
while lines[t].strip() != '': t += 1
V2_HEAD = f"""
**Versão 2 · {DATA} (noite) · 81 candidatas** · Mineração definitiva: **72 artigos** (38 iniciais + 7 do roster ainda não minerados + 27 complementares), lidos integralmente por 72 agentes de extração com cartão único (`mineracao/CARTAO.md`), **698 análises** extraídas com literal e localizador, das quais **197 não cabiam nas 64 fichas** e foram consolidadas em **17 fichas novas (65–81)** e em adendos às existentes. Cada ficha recebeu: a lista das referências no corpus (artigo a artigo, com localizador), a contagem "de 72", complementos/correções, e um **score 0–10 com justificativa** (recomendação do agente; regra 5 continua valendo). **Diretriz (1) de {DATA}: não haverá novos experimentos** — as fichas 15 (contrafactual σ = 0), 63 (sweep offline) e 64 (lote q = 10) estão descartadas e permanecem como registro. Tudo é aditivo (regra 2): o texto da v1 não foi alterado."""
ins[t].append(V2_HEAD)

# §0.2 addendum after rule 6 (line starting with '6. **Vocabulário.**')
r6 = next(k for k, l in enumerate(lines) if l.startswith('6. **Vocabulário.**'))
ins[r6 + 1].append(f"""
**Adendo {DATA} (v2) às regras.** (4′) As contagens passam a ser **"de 72"** (mineração definitiva); as contagens "de 38" da v1 permanecem como estão nas fichas, como histórico. (7) **Score.** Cada ficha traz um score 0–10 e uma justificativa (§0.6); é a recomendação do agente, não decisão. (8) **Diretriz (1).** Nenhuma análise que exija executar algoritmos (variantes, sementes novas, ruído, lote) entra; as fichas afetadas ficam marcadas DESCARTADA e são citadas em 61. (9) **Sigla nova:** [MIN] = mineração definitiva de {DATA} (`mineracao/json/{{id}}.json`, um por artigo; campos `analises[]`, `setup`, `calibracao_do_sigma`, `custo`, `resultados_negativos`, `equivalencia_criterios`, `caracteristica_x_desempenho`, `roster_bloco`).
""")

# §0.6 / §0.7 before '## Template da ficha' (insert before the '---' that precedes it)
tpl = next(k for k, l in enumerate(lines) if l.startswith('## Template da ficha'))
t2 = tpl
while lines[t2].strip() != '---': t2 -= 1
S06 = f"""
### 0.6 Critérios do score (v2, {DATA})

O score de 0 a 10 é uma **recomendação de entrada** no capítulo 5 (como análise, seção, figura, apêndice ou nota), atribuída pelo agente a cada uma das 81 fichas e justificada em texto. Critérios, na ordem em que foram aplicados: **G** — gate da diretriz (1): se a análise exige executar algoritmos (variante, semente nova, ruído injetado, lote), o score é 0–2 e a ficha é registro/limitação; **P** — quanto responde à pergunta-guia (uso explícito da incerteza; as seis perguntas do cap. 4; a lei do teto; a contribuição de medida); **D** — dados prontos e custo (feita/torre = pronto; N com dado nas camadas = barato; exige ③ dos 13 ou métrica nova = médio; lacuna = zero); **C** — convenção do corpus (nº de artigos, de 72, em que aparece; ausência não penaliza leituras próprias da tese, mas presença forte obriga a declarar quando não se faz); **V** — vínculos com promessas de outros capítulos (cap. 1 OE e "contribuição de medida"; cap. 4 l.102/117/364/450; cap. 6 ecos) e com as decisões vinculantes de 22/08 (§D9). Leitura das faixas: 9–10 núcleo; 7–8 entra (seção, figura ou apêndice); 5–6 entra se houver espaço (parágrafo/nota/apêndice); 3–4 provavelmente fora, citar como limitação; 0–2 descartada ou não aplicável.

### 0.7 A mineração definitiva ({DATA}) em números

72 artigos (Anexo 7) · 698 análises com literal + localizador · 197 novas → 166 nas 17 fichas novas (65–81) e 37 absorvidas por fichas existentes, 6 em ambas (Anexo 9) · 60 análises "só mencionadas" (conteúdo em material suplementar ausente do corpus) · 19/72 medem alguma qualidade da incerteza (Anexo 8.1) · 60/72 reportam custo (8.2) · 268 passagens de resultados negativos/ressalvas (8.3) · 71 de equivalência de critérios/modelo como limitante (8.4) · 283 afirmações característica × desempenho (8.5) · 15 blocos-roster com o mecanismo próprio e os parâmetros do uso da incerteza (8.6). Rankings: por score (Anexo 5) e por nº de referências (Anexo 6).
"""
ins[t2].append(S06)

# ---------- anexos 5–9 + histórico ----------
def all_titles():
    T = dict(titles)
    for f in range(65, 82): T[f] = NOVAS[f]['nome']
    return T
T = all_titles()
STAT = {f: stats(f) for f in range(1, 82)}
estado_flag = {f: ('DESCARTADA' if f in (15, 63, 64) else ('regra/nota' if f in (50, 53, 56, 62) else '')) for f in range(1, 82)}

rows = sorted(range(1, 82), key=lambda f: (-SCORES[f][0], -STAT[f]['n_art'], f))
A5 = [f"# Anexo 5 — Ranking por score ({DATA}; recomendação do agente, não decisão)", '',
      "| Score | Ficha | Nome | Refs (de 72) | Obs. |", "|---|---|---|---|---|"]
for f in rows:
    A5.append(f"| {SCORES[f][0]} | {f} | {trunc(T[f], 90)} | {STAT[f]['n_art']} | {estado_flag[f]} |")
A5 += ['', "**Por faixa.** " + " · ".join(
    f"{lab}: " + ", ".join(str(f) for f in rows if lo <= SCORES[f][0] <= hi)
    for lab, lo, hi in [("9–10", 9, 10), ("7–8", 7, 8), ("5–6", 5, 6), ("3–4", 3, 4), ("0–2", 0, 2)])]

rows2 = sorted(range(1, 82), key=lambda f: (-STAT[f]['n_art'], -STAT[f]['n_an'], f))
A6 = [f"# Anexo 6 — Ranking por número de referências no corpus (de 72 artigos)", '',
      "| Refs | Análises | Ficha | Nome | dos 38 | roster 7 | compl. 27 | roster 15 | Score |", "|---|---|---|---|---|---|---|---|---|"]
for f in rows2:
    s = STAT[f]
    A6.append(f"| {s['n_art']} | {s['n_an']} | {f} | {trunc(T[f], 80)} | {s['n38']} | {s['n7']} | {s['n27']} | {s['nr']} | {SCORES[f][0]} |")
A6 += ['', "Fichas com 0 referências (leituras próprias da tese, regras ou notas): " + ", ".join(str(f) for f in rows2 if STAT[f]['n_art'] == 0) + "."]

# Anexo 7
def sfield(d, k, n=110):
    v = (d.get('setup') or {}).get(k)
    if isinstance(v, list): v = '; '.join(map(str, v))
    return trunc(str(v) if v is not None else '', n)
A7 = [f"# Anexo 7 — Os 72 artigos da mineração definitiva", '',
      "### 7.1 Protocolo", '',
      f"Um agente de extração por artigo (modelo Sonnet), com o cartão `mineracao/CARTAO.md` (contexto mínimo da bateria; campos por análise: fichas, nova, descrição, literal ≤ 40 palavras, localizador, métricas, testes, convenções, achado, aplicabilidade com as 7 camadas; campos por artigo: setup, calibração do σ, custo, resultados negativos, equivalência de critérios, característica × desempenho, bloco-roster) e a tipologia das 64 fichas (`mineracao/tipologia_64.md`). Regras: literal + localizador em tudo (Lei 1), exaustividade, nada inventado (material suplementar ausente = 'só mencionada'), JSON validado. Execução em 9 lotes de 7–9 agentes em paralelo; 72/72 JSONs válidos; consolidação por script (`mineracao/build_v2.py`): mapeamento das 197 novas por leitura integral (Anexo 9), contagens por ficha, e escrita das fichas 65–81 e dos scores pelo agente de sessão. Limitações: (i) 60 análises são 'só mencionadas' (suplementos não convertidos — b3, b8, c261, e7, e74, e102, e103, e104, e86, c267, c82, e3, c100 apêndices); (ii) e8 tem só a Supporting Information no corpus; (iii) b15 sob N15 (nenhum número seu entra na prosa); (iv) c100 sem apêndices (14 páginas); (v) mapeamento ficha ↔ análise é do extrator + revisão do agente de sessão — auditável em `refs_full.json`.", '',
      "### 7.2 Os 27 complementares e os critérios da escolha", '', CRITERIOS_27, '',
      "### 7.3 Tabela dos 72", '',
      "| id | Sigla | Ano | Grupo | Roster | Motor | Função | Surrogate | Medição | Regime | Análises | Novas | Execuções | Testes | Plataforma |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
order_ids = sorted(ids, key=lambda i: (grupo_art(i) != 'R7', grupo_art(i) != '38', i))
for i in order_ids:
    m = meta[i]; d = J[i]
    nan = len(d['analises']); nnov = sum(1 for a in d['analises'] if a.get('nova'))
    A7.append(f"| {i} | {trunc(m['sigla'], 40)} | {m['ano']} | {grupo_art(i)} | {'sim' if m['roster'] else ''} | {trunc(m['motor'], 30)} | {trunc(m['funcao'], 32)} | {trunc(m['surrogate'], 24)} | {trunc(m['medicao'], 28)} | {m['regime']} | {nan} | {nnov} | {sfield(d, 'execucoes', 70)} | {sfield(d, 'testes', 80)} | {sfield(d, 'codigo_plataforma', 60)} |")
A7 += ['', "Legenda: Grupo 38 = artigo das planilhas do processo seletivo; R7 = os 7 do roster minerados agora; 27 = complementares. O `setup` completo (benchmarks, orçamento, baselines, métricas, apresentação) de cada artigo está no arquivo-companheiro `mineracao_definitiva_transversais_06-09-2026.md`, §A.",
       '', "### 7.4 Roster: quem mede o quê sobre o próprio mecanismo (resumo; detalhe no Anexo 8.6)", '']
for i in [x for x in order_ids if meta[x]['roster']]:
    rb = J[i]['roster_bloco'] or {}
    mp = rb.get('mecanismo_proprio') or []
    A7.append(f"- **{i}** ({meta[i]['sigla']}): {len(mp)} análise(s) do mecanismo próprio; calibração medida: {'sim' if (J[i]['calibracao_do_sigma'] or {}).get('mede') else 'não'}; custo reportado: {'sim' if (J[i]['custo'] or {}).get('reporta') else 'não'}; resultados negativos registrados: {len(J[i].get('resultados_negativos') or [])}; equivalências: {len(J[i].get('equivalencia_criterios') or [])}; característica × desempenho: {len(J[i].get('caracteristica_x_desempenho') or [])}.")

# Anexo 8
def lit(e, n=260):
    return trunc(e.get('literal') or '', n)
A8 = [f"# Anexo 8 — Achados transversais da mineração definitiva (com literais; versão completa no arquivo-companheiro)", '',
      "### 8.1 Quem mede a qualidade da incerteza que usa (calibracao_do_sigma.mede = true): 19/72", '']
for i in ids:
    c = J[i]['calibracao_do_sigma'] or {}
    if c.get('mede'):
        A8.append(f"- **{i}** ({meta[i]['sigla']}, {meta[i]['ano']}{'; roster' if meta[i]['roster'] else ''}) — {trunc(c.get('como'), 420)} «{trunc(c.get('literal'), 200)}» [{trunc(c.get('localizador'), 90)}]")
A8 += ['', "Os 53 que NÃO medem incluem 11 do roster (b1, b3, b5, c141, c149, c154, c238, c262, e103, e74, e81) — o σ é insumo operacional, nunca objeto de medição; a única exceção do roster é a acurácia de classificação (b4, c122, c217; e7 mede 'magnitude').", '',
       "### 8.2 Como o corpus reporta custo (custo.reporta = true): 60/72", '']
for i in ids:
    c = J[i]['custo'] or {}
    if c.get('reporta'):
        A8.append(f"- **{i}** ({meta[i]['sigla']}): {trunc(c.get('o_que'), 230)} [{trunc(c.get('localizador'), 70)}]")
A8 += ['', "Sem custo reportado (12): " + ", ".join(i for i in ids if not (J[i]['custo'] or {}).get('reporta')) + ".", '',
       "### 8.3 Resultados negativos e ressalvas dos autores (268 passagens): contagem por artigo e seleção", '']
cnt = {i: len(J[i].get('resultados_negativos') or []) for i in ids}
A8.append("Contagem por artigo: " + " · ".join(f"{i} {cnt[i]}" for i in sorted(ids, key=lambda x: -cnt[x]) if cnt[i]) + ".")
A8 += ['', "Seleção (passagens em que a incerteza/σ/calibração é o objeto — as demais estão no companheiro, §C):", '']
KEY = re.compile(r'(uncertain|σ|sigma|calibr|variance|explor|mislead|noise|imperfect|poorly|overconf|confiden|epistem|dropout|posterior|kriging|gp\b|gaussian)', re.I)
nsel = 0
for i in ids:
    for e in J[i].get('resultados_negativos') or []:
        s = (e.get('descricao') or '') + ' ' + (e.get('literal') or '')
        if KEY.search(s):
            nsel += 1
            A8.append(f"- **{i}** ({meta[i]['sigla']}) [{trunc(e.get('localizador'), 60)}]: {trunc(e.get('descricao'), 260)} «{lit(e, 220)}»")
A8 += ['', f"({nsel} passagens selecionadas por palavra-chave de incerteza/modelo; 268 no total.)", '',
       "### 8.4 Equivalência de critérios / o modelo como limitante (71 passagens — todas)", '']
for i in ids:
    for e in J[i].get('equivalencia_criterios') or []:
        A8.append(f"- **{i}** ({meta[i]['sigla']}) [{trunc(e.get('localizador'), 60)}]: {trunc(e.get('descricao'), 240)} «{lit(e, 200)}»")

# 8.5 característica × desempenho, normalizada
CATS = [
 ('ruído', r'ru[ií]do|noise'),
 ('correlação entre objetivos', r'correla'),
 ('restrições / factibilidade', r'restri|constrain|fact[ií]v|feasib'),
 ('muitos objetivos (M)', r'muitos objetivos|many-?objective|n[uú]mero de objetivos|objectives|m\s*=|k\s*>|objetivos \(k|escalabilidade em m|m crescente'),
 ('alta dimensão (D)', r'dimens|high-?dim|\bd\s*=|d crescente|vari[aá]veis de decis|large.?scale|escala'),
 ('frente desconexa', r'desconex|descont|disconnect|discontinu|desconect'),
 ('frente degenerada / irregular', r'degener|irregular|curva'),
 ('multimodalidade / ótimos locais / enganoso', r'multimodal|[oó]timos locais|local optim|decept|enganos|dif[ií]cil de converg'),
 ('não separabilidade', r'separ'),
 ('geometria da frente (côncava/convexa/mista)', r'c[oô]ncav|concav|convex|geometri|forma|shape|mixed|linear'),
 ('densidade enviesada / cobertura', r'densid|bias|envies|uniform|distribui|cobertura|vi[eé]s'),
 ('orçamento / dados iniciais / DoE', r'or[cç]amento|budget|dataset|amostra|doe|dados|poucos|inicial'),
 ('problema real / domínio', r'real|rede|network|topolog|gradient|dom[ií]nio'),
]
def cat_of(s):
    s = (s or '').lower()
    for name, pat in CATS:
        if re.search(pat, s): return name
    return 'outra'
bycat = collections.defaultdict(list)
for i in ids:
    for e in J[i].get('caracteristica_x_desempenho') or []:
        bycat[cat_of(e.get('caracteristica'))].append((i, e))
A8 += ['', "### 8.5 Característica do problema × desempenho: 283 afirmações, por característica (normalizada por palavra-chave; texto completo no companheiro, §D)", '',
       "| Característica | Afirmações | Artigos |", "|---|---|---|"]
for name in [c[0] for c in CATS] + ['outra']:
    L = bycat.get(name, [])
    if not L: continue
    arts = sorted(set(i for i, e in L))
    A8.append(f"| {name} | {len(L)} | {', '.join(arts)} |")
A8 += ['', "Amostra de afirmações (uma por artigo e característica, as primeiras 60 pelo índice):", '']
seen = set(); k = 0
for name in [c[0] for c in CATS]:
    for i, e in bycat.get(name, []):
        if (i, name) in seen: continue
        seen.add((i, name)); k += 1
        if k > 60: break
        A8.append(f"- [{name}] **{i}** ({meta[i]['sigla']}) [{trunc(e.get('localizador'), 50)}]: {trunc(e.get('afirmacao'), 220)} «{lit(e, 160)}»")

# 8.6 roster blocks (full)
def render_any(v, indent='  '):
    if v is None: return ''
    if isinstance(v, str): return v
    if isinstance(v, list):
        out = []
        for x in v:
            if isinstance(x, dict):
                d = x.get('descricao') or x.get('nome') or x.get('parametro') or ''
                extra = '; '.join(f"{k}: {trunc(str(val), 300)}" for k, val in x.items() if k not in ('descricao', 'nome', 'parametro'))
                if d:
                    out.append(f"{indent}- {d} {('(' + extra + ')') if extra else ''}")
                else:
                    out.append(f"{indent}- {extra}")
            else:
                out.append(f"{indent}- {x}")
        return '\n'.join(out)
    if isinstance(v, dict):
        return '\n'.join(f"{indent}- {k}: {trunc(str(val), 400)}" for k, val in v.items())
    return str(v)
A8 += ['', "### 8.6 Os 15 do roster: o mecanismo próprio, o que o reproduz nas camadas e os parâmetros do uso da incerteza (roster_bloco, íntegra)", '']
for i in [x for x in order_ids if meta[x]['roster']]:
    rb = J[i]['roster_bloco'] or {}
    A8.append(f"#### {i} — {meta[i]['sigla']} ({meta[i]['ano']}) · {meta[i]['funcao']} · {meta[i]['surrogate']} · {meta[i]['medicao']}")
    A8.append('')
    A8.append("**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**")
    A8.append(render_any(rb.get('mecanismo_proprio')) or '  - (nenhuma)')
    A8.append('')
    A8.append("**Reprodutível com as camadas:** " + (render_any(rb.get('reprodutivel_com_camadas')) if not isinstance(rb.get('reprodutivel_com_camadas'), str) else rb.get('reprodutivel_com_camadas')))
    A8.append('')
    A8.append("**Parâmetros do uso da incerteza:**")
    A8.append(render_any(rb.get('parametros_do_uso_da_incerteza')) or '  - (não listados)')
    A8.append('')

# Anexo 9 — mapa das novas
A9 = ["# Anexo 9 — As 197 análises 'novas' e seu destino (índice do JSON consolidado `novas_full.json`)", '',
      "| # | id | Nome sugerido pelo extrator | Localizador | Ficha(s) de destino |", "|---|---|---|---|---|"]
for e in novas_full:
    A9.append(f"| {e['idx']} | {e['id']} | {trunc(e.get('nome_sugerido'), 110)} | {trunc(e.get('localizador'), 60)} | {', '.join(map(str, e['ficha_dest']))} |")
into_existing = sorted(set(f for e in novas_full for f in e['ficha_dest'] if f <= 64))
A9 += ['', f"Novas absorvidas por fichas existentes: {sum(1 for e in novas_full if any(f <= 64 for f in e['ficha_dest']))} análises, nas fichas {', '.join(map(str, into_existing))}. Novas nas fichas 65–81: {sum(1 for e in novas_full if any(f >= 65 for f in e['ficha_dest']))}."]

HIST = f"- **{DATA} (noite) — v2.** Mineração definitiva de 72 artigos (698 análises; 197 novas). Acrescentados, sem alterar a v1: §0.6 (critérios do score), §0.7 (números da mineração), adendo às regras; adendo datado em cada uma das 64 fichas (referências artigo a artigo com localizador; contagem 'de 72'; complementos/correções; score + justificativa); 17 fichas novas (65–81) nos grupos A–I; Anexos 5 (ranking por score), 6 (ranking por referências), 7 (os 72 artigos, os 27 escolhidos e o protocolo), 8 (achados transversais: calibração, custo, resultados negativos, equivalência de critérios, característica × desempenho, blocos-roster) e 9 (mapa das 197 novas). Diretriz (1) aplicada: fichas 15, 63 e 64 descartadas (score 0). Arquivo-companheiro com as íntegras: `mineracao_definitiva_transversais_06-09-2026.md`. Nenhuma decisão tomada."

anexos_txt = '\n'.join(['', '---', ''] + A5 + ['', '---', ''] + A6 + ['', '---', ''] + A7 + ['', '---', ''] + A8 + ['', '---', ''] + A9 + [''])
hist_idx = next(k for k, l in enumerate(lines) if l.startswith('## Histórico (aditivo)'))
# insert anexos before the '---' preceding Histórico
th = hist_idx
while lines[th].strip() != '---': th -= 1
ins[th].append(anexos_txt)

# ---------- write catalog ----------
out = []
for k, l in enumerate(lines):
    if k in ins:
        for blk in ins[k]: out.append(blk)
    out.append(l)
text = '\n'.join(out)
text = text.rstrip('\n') + '\n' + HIST + '\n'
open(CAT_OUT, 'w', encoding='utf-8').write(text)

# ---------- companion file ----------
C = [f"# Mineração definitiva ({DATA}) — íntegras dos achados transversais dos 72 artigos", '',
     "Arquivo-companheiro do `catalogo_analises_cap5.md` (v2). Tudo aqui vem dos JSONs `mineracao/json/{id}.json` (um por artigo), sem edição além de formatação. Seções: A setup dos 72 · B calibração do σ (19) · C resultados negativos (268) · D característica × desempenho (283) · E equivalência de critérios (71) · F observações dos extratores (72).", '']
C += ["## A. Setup experimental dos 72 artigos", '']
for i in order_ids:
    d = J[i]; s = d.get('setup') or {}
    C.append(f"### {i} — {meta[i]['sigla']} ({meta[i]['ano']}) · {meta[i]['titulo']}")
    for k in ['benchmarks', 'orcamento', 'execucoes', 'baselines', 'metricas_principais', 'testes', 'apresentacao', 'codigo_plataforma']:
        v = s.get(k); v = '; '.join(map(str, v)) if isinstance(v, list) else (v or '')
        C.append(f"- **{k}**: {v}")
    C.append('')
C += ["## B. Calibração do σ — os 19 que medem (íntegra) e os 53 que não medem (como o extrator descreveu)", '']
for i in order_ids:
    c = J[i]['calibracao_do_sigma'] or {}
    C.append(f"- **{i}** ({meta[i]['sigla']}) — mede: {'SIM' if c.get('mede') else 'não'}. {c.get('como') or ''} «{c.get('literal') or ''}» [{c.get('localizador') or ''}]")
C += ['', "## C. Resultados negativos e ressalvas (268)", '']
for i in order_ids:
    for e in J[i].get('resultados_negativos') or []:
        C.append(f"- **{i}** ({meta[i]['sigla']}) [{e.get('localizador') or ''}]: {e.get('descricao') or ''} «{e.get('literal') or ''}»")
C += ['', "## D. Característica do problema × desempenho (283)", '']
for name in [c[0] for c in CATS] + ['outra']:
    L = bycat.get(name, [])
    if not L: continue
    C.append(f"### {name} ({len(L)})")
    for i, e in L:
        C.append(f"- **{i}** ({meta[i]['sigla']}) [{e.get('localizador') or ''}] — característica: {e.get('caracteristica') or ''}. {e.get('afirmacao') or ''} «{e.get('literal') or ''}»")
    C.append('')
C += ["## E. Equivalência de critérios / modelo como limitante (71)", '']
for i in order_ids:
    for e in J[i].get('equivalencia_criterios') or []:
        C.append(f"- **{i}** ({meta[i]['sigla']}) [{e.get('localizador') or ''}]: {e.get('descricao') or ''} «{e.get('literal') or ''}»")
C += ['', "## F. Observações dos extratores (72)", '']
for i in order_ids:
    C.append(f"- **{i}** ({meta[i]['sigla']}): {J[i].get('observacoes') or ''}")
open(COMP_OUT, 'w', encoding='utf-8').write('\n'.join(C) + '\n')
print('catalog bytes', len(text), 'companion bytes', os.path.getsize(COMP_OUT))
print('selected negatives', nsel, '| cats', {k: len(v) for k, v in bycat.items()})
