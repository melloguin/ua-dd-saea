# -*- coding: utf-8 -*-
"""gen_bundles.py — fragmenta a SPEC v5.1 em bundles de contexto para o Claude Code (passo físico do D83).
Bundles são GERADOS: a SPEC segue sendo a única fonte da verdade. Regenerar após qualquer edição na SPEC."""
import os, re, shutil, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # robustez de path (roda da pasta do script)
SPEC = 'SPEC_experimentos_v5.2.md'
# [fix 2026-07-17, torre] O script agora VIVE dentro do pacote instalado -> regeneração é
# IN-PLACE (OUT='.'). O modo antigo (OUT='claude_code_context') criava um pacote ANINHADO
# claude_code_context/claude_code_context/ e os bundles reais nunca eram atualizados.
OUT  = '.'
#: só estas pastas são GERADAS (o rmtree limita-se a elas — NUNCA a raiz, que contém a SPEC/artifacts)
GENERATED_DIRS = ['00_fundacao', '10_rodada1_matlab', '20_rodada2_botorch',
                  '30_rodada3_standalone', '40_subestudos', '50_analise_R4']
text = open(SPEC, encoding='utf-8').read()
lines = text.split('\n')

BANNER = ("> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — "
          "**não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** "
          "(precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).\n")

def find(pat):
    r = re.compile(pat)
    for i, l in enumerate(lines):
        if r.match(l):
            return i
    raise SystemExit("HEADER NAO ENCONTRADO: " + pat)

def sec(start_pat, end_pat):
    a, b = find(start_pat), find(end_pat)
    assert b > a, (start_pat, end_pat)
    return '\n'.join(lines[a:b]).rstrip() + '\n'

def rows(range_start_pat, range_end_pat, tokens, keep_notes=True):
    a, b = find(range_start_pat), find(range_end_pat)
    out, prev_kept = [], False
    for l in lines[a:b]:
        first = l.split('|')[1].strip() if l.startswith('|') and l.count('|') > 2 else None
        if first is not None and any(first == t or first.startswith(t + ' ') for t in tokens):
            out.append(l); prev_kept = True
        elif keep_notes and prev_kept and l.startswith('> **Notas'):
            out.append(l); prev_kept = False
        elif l.strip() == '' :
            prev_kept = prev_kept  # blank keeps state
        else:
            prev_kept = False
    assert out, "SEM LINHAS p/ tokens %s" % tokens
    return '\n'.join(out) + '\n'

def checklist(token):
    out = [l for l in lines if l.startswith('- [ ] **' + token)]
    assert len(out) == 1, "checklist %s -> %d" % (token, len(out))
    return out[0] + '\n'

def strip_alg_items(section_text, tokens):
    keep = []
    for l in section_text.split('\n'):
        if l.startswith('- [ ] **') and any(l.startswith('- [ ] **' + t) for t in tokens):
            continue
        keep.append(l)
    return '\n'.join(keep)

def write(path, title, parts, epigraph=None):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    body = "# " + title + "\n\n" + BANNER + "\n"
    if epigraph:
        body += epigraph.rstrip() + "\n\n---\n\n"
    body += "\n\n---\n\n".join(p.rstrip() for p in parts) + "\n"
    open(full, 'w', encoding='utf-8').write(body)
    print("  %-55s %6.1f KB" % (path, len(body)/1024))

for _d in GENERATED_DIRS:          # limpeza SÓ das pastas geradas (in-place seguro)
    _p = os.path.join(OUT, _d)
    if os.path.isdir(_p):
        shutil.rmtree(_p)
print("== FUNDACAO ==")

d3 = sec(r'^### D\.3 ', r'^## Anexo E ')
write('00_fundacao/01_regras_globais.md', 'Fundação 1/5 — Regras globais, orçamento, sementes e as decisões vinculantes',
      [sec(r'^## §0 ', r'^## 1\. '), sec(r'^## 1\. ', r'^## 2\. '),
       sec(r'^## 5\. ', r'^## 6\. '), sec(r'^## 16\. ', r'^## §16\.5 '), d3])

write('00_fundacao/02_arquitetura_harness.md', 'Fundação 2/5 — Arquitetura A2, harness, ambientes, paralelismo e infra',
      [sec(r'^## 2\. ', r'^## 3\. '), sec(r'^## §16\.5 ', r'^## 17\. '),
       sec(r'^## 18\. ', r'^## 19\. '), sec(r'^## 19\. ', r'^## 20\. '),
       sec(r'^## 21\. ', r'^## 22\. '), sec(r'^### N\.4 ', r'^### N\.5 '),
       sec(r'^### S\.6 ', r'^### S\.7 ')])

write('00_fundacao/03_contrato_export.md', 'Fundação 3/5 — Contrato de export (§17 completo: 3 camadas, timing, jsonl, persistência)',
      [sec(r'^## 17\. ', r'^## 18\. '), sec(r'^### S\.7 ', r'^### S\.8 ')])

f0 = sec(r'^## 22\. ', r'^### 22\.2 ')
write('00_fundacao/04_plano_F0_piloto_gates.md', 'Fundação 4/5 — Plano de implementação: molde, Fase 0, piloto (gate) e gates de saída',
      [f0, sec(r'^### 22\.5 ', r'^### 22\.6 '), sec(r'^### 22\.6 ', r'^# ANEXOS'),
       sec(r'^### S\.4 ', r'^### S\.5 '), sec(r'^### S\.8 ', r'^> \*\*Registro\.\*\* Auditoria')])

write('00_fundacao/05_problemas.md', 'Fundação 5/5 — Os 25 problemas, f_min/f_max e notas do problems.py',
      [sec(r'^## 4\. ', r'^## 5\. '), sec(r'^### S\.5 ', r'^### S\.6 '),
       sec(r'^### L\.19 ', r'^## Anexo M ')])

print("== RODADA 1 (MATLAB) ==")
R1_TOKENS = ['b1 ', 'b3 ', 'b4 ', 'e7 ', 'c217 ', 'c141 ', 'e74 ', 'c238 ', 'e103 ', 'Pisos ONLINE (']
r1 = strip_alg_items(sec(r'^### 22\.2 ', r'^### 22\.3 '), R1_TOKENS)
write('10_rodada1_matlab/00_contrato_rodada1.md', 'Rodada 1 — contrato transversal MATLAB/PlatEMO (Mac)',
      [r1, sec(r'^### N\.0 ', r'^### N\.1 '), sec(r'^### N\.2 ', r'^### N\.3 '),
       sec(r'^### N\.3 ', r'^### N\.4 '), sec(r'^### L\.0 ', r'^### L\.1 '),
       sec(r'^### E\.8 ', r'^### E\.9 '),
       sec(r'^### S\.1 ', r'^### S\.2 '), sec(r'^### S\.2 ', r'^### S\.3 '), sec(r'^### S\.3 ', r'^### S\.4 ')],
      epigraph=("**📋 LEITURA OBRIGATÓRIA ANTES DE CODAR (correção estrutural 2026-07-19):** este contrato de rodada NÃO contém o contrato de DADOS. Leia **`CONTRATO_DE_DADOS.md` (raiz do repo)** — as camadas ①②③④⑤⑥⑦, a **SONDA canônica** (§17.2.2: artefato de 20.000 pontos; ONLINE lê a fatia de 2.000 a cada k=2 gerações + 1ª/última; OFFLINE lê as 20.000 1× por modelo treinado, com `geracao`=NULL), a camada **⑦ `__final`** (DI-08/DI-13.9 — SÓ offline: TODOS os finais avaliados 1× e o ND filtrado DEPOIS), o **timing v5.2.1** (§17.6: `tempo_fit_s` [NULLABLE nos pisos] · `tempo_busca_s` · `tempo_pred_sonda_s` · `tempo_geracao_s` + bloco `timing` OBRIGATÓRIO no manifesto) e o **`.jsonl` enriquecido** (S.7.1/DI-10). O `REGISTRO_DECISOES_IMPLEMENTACAO.md` (DI-01..DI-14) traz o PORQUÊ de cada uma. Precedência: SPEC > CONTRATO_DE_DADOS > este bundle.\n\n" "**Decisões-chave desta rodada (Anexo D §D.3):** D59 (`parfor` canônico; `rng(seed)` DEPOIS do Problem, probe isolado) · "
                "D60 (watchdog 3 guardas) · D61 (hard-stop no meio do lote, `PlatEMO:Termination`) · D63 (DoE carregado do artefato `.npy`) · "
                "D53 (float32 SEM arredondamento; MATLAB grava **brotli**) · D58 (escrita atômica `tmp→movefile`) · D64 (sem backup automático) · "
                "**D86 (higiene de memória: reset do `Problem` pymoo na ponte ao fim de cada run — N.0.8)** · **D87/D88 (DoE em parquet; invariante de inicialização unificada + CP-init)** · **D89 (cache-hit=0 FE; wrapper como fonte única do orçamento — o `obj.FE` do PlatEMO NÃO governa o término)** · **D97 (validação de fidelidade = análise MANUAL do autor, a posteriori; o gate automático é só encanamento objetivo — FE/saídas/CP-init/guardas; ±3σ é faixa-guia, não limiar)**."))

ALGS = {
 # arquivo, título, tokens 6.4, token checklist, I, L, M, E(ou None), token J, epígrafe
 'alg_b1_parego':   ('b1 ParEGO (PlatEMO 4.15)', ['b1'], 'b1 ParEGO', r'I\.1 ', r'L\.1 ', r'M\.1 ', r'E\.10 ', 'b1 ',
                     "D76 registra **L8**: guard `sqrt(max(mse,0))` (mse<0 do dacefit) é 🟠 obrigatório."),
 'alg_b3_krvea':    ('b3 K-RVEA (PlatEMO 4.15)', ['b3'], 'b3 K-RVEA', r'I\.2 ', r'L\.2 ', r'M\.2 ', None, 'b3 ',
                     "Guard do crash latente (`UpdataArchive:61`) + **DoE livre de duplicatas** (1º fit sem dedup)."),
 'alg_b4_csea':     ('b4 CSEA (PlatEMO 4.15)', ['b4'], 'b4 CSEA', r'I\.3 ', r'L\.3 ', r'M\.3 ', None, 'b4 ',
                     "`ExecutionEnvironment='cpu'` obrigatório (N.2.4); N=50 do paper; export semântico (schema C1); stall 0-FE → guarda (c) do D60."),
 'alg_e7_ednarmoea':('e7 EDN-ARMOEA (PlatEMO 4.15 built-in)', ['e7'], 'e7 EDN-ARMOEA', r'I\.4 ', r'L\.4 ', r'M\.5 ', None, 'e7 ',
                     "Built-in 4.15 (N.2.1 — dilema E.8 morto). Sem dedup de infill → guarda (c) do D60 (saldo congelado). Higiene torch não se aplica (MATLAB DLT), mas monitorar RAM do trainNetwork (D86/§22.5.7)."),
 'alg_c217_pcsaea': ('c217 PC-SAEA (PlatEMO 4.15) — caso-modelo da auditoria', ['c217'], 'c217 PC-SAEA', r'I\.5 ', r'L\.5 ', r'M\.4 ', None, 'c217 ',
                     "Patch = **2 guardas** (D17); N=50; **referência de fidelidade (validação MANUAL do autor — D97): IGD≈6,9212e-2, faixa-guia ±3σ=±2,335e-2 @ 2000 FEs** (não é limiar automático; o antigo ±1σ reprovaria 1/3 das corretas; ⚠ nosso orçamento é 31D−1 = 464 em d=15 → IGD acima da faixa é ESPERADO; compare o MECANISMO, não o IGD cru — D97/RI-05); log `.txt` por geração (§17.2.1)."),
 'alg_c141_mmraea': ('c141 MMRAEA (autor, MATLAB — porte 3 linhas)', ['c141'], 'c141 MMRAEA', r'I\.7 ', r'L\.7 ', r'M\.13 ', None, 'c141 ',
                     "D76 registra **L4**: `+eps` no SDE (NaN) é 🟠 obrigatório. Renames defensivos opcionais (colisões same-folder se auto-resolvem — S.8)."),
 'alg_e74_clmea':   ('e74 CLMEA (autor, MATLAB/PlatEMO 4.1)', ['e74'], 'e74 CLMEA', r'I\.8 ', r'L\.8 ', r'M\.14 ', None, 'e74 ',
                     "**D74: CalHV interno NORMALIZADO** (min-max no arquivo corrente, ref 1,1 — obrigatório p/ os 6 BBOB). **D76: máscara `x_offspring(index(Choose),:)` é fix 🔴 OBRIGATÓRIO** (não 'opcional'). **D95: OPÇÃO A DECIDIDA — rodar na árvore PlatEMO 4.1 própria (`CLMEA_Code`), worker dedicado + adendo N.0-4.1 (sem `once`, ponte por indivíduo)**; `SelectTrainData.m` EXISTE (erratum S.8). **D94: injeção do DoE APLICA-SE — o par gera-LHS + re-escala do `CLMEA.m:33-34` é substituído JUNTO** por `Arc = Problem.Evaluation(Problem.data.X0)` (X0 NATIVO = DoE 11D−1 do artefato; injetar só no RHS re-escalaria de novo). O init PRÓPRIO do e74 é `N=100/200` hard-coded (`:28-32`) e é exatamente o que fica substituído — **desvio DELIBERADO do paper, registrado** (D63/D87/D88 + princípio da D94)."),
 'alg_c238_eim':    ('c238 EIM (autor, MATLAB standalone → embrulho ALGORITHM)', ['c238'], 'c238 EIM', r'I\.9 ', r'L\.9 ', r'M\.16 ', r'E\.5 ', 'c238 ',
                     "Embrulho `classdef EIM < ALGORITHM` (N.5, abaixo). Hard-stop usa o MESMO `PlatEMO:Termination` (D61)."),
 'alg_e103_ibeams': ('e103 IBEA-MS (autor, MATLAB standalone — OFFLINE)', ['e103'], 'e103 IBEA-MS', r'I\.15 ', r'L\.15 ', r'M\.6 ', r'E\.9 ', 'e103 ',
                     "⚠ **Worker MATLAB DEDICADO** (poluição de path — D59/N.3). Regime offline (dataset injetado; FE-real=0 na busca). 2 fixes de 1 linha (pm=1/D→paper; diagonal do JudgeModel). **D93: centros da RBFN = `⌈√(n_dataset)⌉` com o n INJETADO (31D−1 / 2k / 50k) — mata o 'patch NO-OP' do Anexo S (premissa falsa: o dataset NÃO é 11D−1); sem isso a RBFN subdimensiona e o eixo do sweep colapsa**. **D90: dataset offline = artefato parquet** (data/datasets/). Roda como config `off_e103_*` e no sweep (D55/D56)."),
}
for fname,(title,t64,tchk,ipat,lpat,mpat,epat,jtok,epi) in ALGS.items():
    parts=[checklist(tchk), rows(r'^### 6\.4 ', r'^### 6\.6 ', t64),
           sec(r'^### '+ipat, r'^### I\.|^## Anexo J ') if False else sec_alg_I(ipat) if False else None]
    # montagem manual (I/L/M/E) com fronteiras corretas:
    def nxt(pref, pat):
        i=find(r'^### '+pat)
        for j in range(i+1,len(lines)):
            if re.match(r'^### |^## ',lines[j]): return '\n'.join(lines[i:j]).rstrip()+'\n'
        raise SystemExit(pat)
    parts=[checklist(tchk), rows(r'^### 6\.4 ', r'^### 6\.6 ', t64), nxt('I',ipat), nxt('L',lpat), nxt('M',mpat)]
    if epat: parts.append(nxt('E',epat))
    parts.append("**Âncora de fidelidade (Anexo J):**\n\n"+rows(r'^## Anexo J ', r'^## Anexo K ', [jtok.strip()], keep_notes=False))
    write('10_rodada1_matlab/%s.md'%fname, title, parts, epigraph="**Decisões específicas:** "+epi)

write('10_rodada1_matlab/alg_pisos_online.md', 'Pisos online (NSGA-II, NSGA-III, MOEA/D, SMS-EMOA) + varredura de N',
      [checklist('Pisos ONLINE ('), sec(r'^### 3\.2 ', r'^### 3\.3 '), sec(r'^### 6\.3 ', r'^### 6\.4 '),
       rows(r'^### 6\.4 ', r'^### 6\.6 ', ['Pisos online','NSGA-II, NSGA-III, MOEA/D, SMS-EMOA (online)','NSGA-III','SMS-EMOA (4º piso)','BO-especiais (c154, e81, c149)'])],
      epigraph="**D65:** N dos pisos ONLINE = **varredura pré-registrada** N∈{10,20,30,50} (5 problemas do sweep + 2 reps alta-D, 5 sementes; critério = mediana IGD+ final; 1 N por faixa de D, cravado ANTES da bateria). Supersede o '100' e o '~20'. Pisos = built-ins do PlatEMO; DoE injetado; hard-stop D21.")

print("== RODADA 2 (BoTorch) ==")
R2_TOKENS=['c262 ','c154 ']
r2=strip_alg_items(sec(r'^### 22\.3 ', r'^### 22\.4 '), R2_TOKENS)
write('20_rodada2_botorch/00_contrato_rodada2.md', 'Rodada 2 — contrato transversal BoTorch (Python, Vertex AI)',
      [r2, sec(r'^### N\.1 ', r'^### N\.2 '), sec(r'^### L\.18 ', r'^### L\.19 ')],
      epigraph=("**📋 LEITURA OBRIGATÓRIA ANTES DE CODAR (correção estrutural 2026-07-19):** este contrato de rodada NÃO contém o contrato de DADOS. Leia **`CONTRATO_DE_DADOS.md` (raiz do repo)** — as camadas ①②③④⑤⑥⑦, a **SONDA canônica** (§17.2.2/§3.1: artefato de 20.000 pontos; ONLINE lê a fatia de 2.000 a cada k=2 gerações; OFFLINE lê as 20.000 1× por modelo treinado, com `geracao`=NULL), a camada **⑦ `__final`** (DI-08/DI-13.9 — SÓ offline: TODOS os finais avaliados 1× e o ND filtrado DEPOIS), o **timing v5.2.1** (§17.6: `tempo_fit_s` [NULLABLE nos pisos] / `tempo_busca_s` / `tempo_pred_sonda_s` / `tempo_geracao_s` + bloco `timing` OBRIGATÓRIO no manifesto) e o **`.jsonl` enriquecido** (S.7.1/DI-10). O `REGISTRO_DECISOES_IMPLEMENTACAO.md` (DI-01..DI-14) traz o PORQUÊ de cada uma. Em divergência: SPEC > CONTRATO_DE_DADOS > este bundle."
                "\n\n"
                "**Decisões-chave:** BoTorch **OFICIAL 0.18.1** (nunca o fork do device — N.2.3) · D62 (`SeedSequence((base,alg_id,iter,uso_id))` p/ toda semente interna) · "
                "D79 (subprocess-por-venv; `OMP/OPENBLAS/MKL/NUMEXPR=1`; float64; CPU) · D53/D54 (export float32 sem round; **c262/c154 são bucket-only**) · "
                "D58 (resume dos bucket-only LISTA O BUCKET — agendado no hardening do M7; **até lá, no Mac, `enable_bucket=False` e camadas locais completas, RI-08**) · **D86 (higiene torch: `no_grad` na predição; `del`+`gc.collect()` por iteração — N.1.5)** · D61 (`BudgetExhausted`)."))
def nxt2(pat):
    i=find(r'^### '+pat)
    for j in range(i+1,len(lines)):
        if re.match(r'^### |^## ',lines[j]): return '\n'.join(lines[i:j]).rstrip()+'\n'
    raise SystemExit(pat)
write('20_rodada2_botorch/alg_c262_qnehvi.md','c262 qNEHVI (BoTorch 0.18.1)',
      [checklist('c262 qNEHVI'), rows(r'^### 6\.4 ', r'^### 6\.6 ', ['c262']), nxt2(r'I\.10 '), nxt2(r'L\.10 '), nxt2(r'M\.7 '), nxt2(r'E\.2 '),
       "**Âncora de fidelidade (Anexo J):**\n\n"+rows(r'^## Anexo J ', r'^## Anexo K ', ['c262'], keep_notes=False)],
      epigraph="**Específicas:** Matérn 5/2 ARD (🔵 ARTIGO, D30); `train_Yvar=1e-6` (B8.6a); refit from scratch/iteração (D44); ref da AQUISIÇÃO = nadir×1,1 (interno — a MÉTRICA usa o ref normalizado D69); **bucket-only (D54)**.")
write('20_rodada2_botorch/alg_c154_jes.md','c154 JES (BoTorch 0.18.1)',
      [checklist('c154 JES'), rows(r'^### 6\.4 ', r'^### 6\.6 ', ['c154']), nxt2(r'I\.11 '), nxt2(r'L\.11 '), nxt2(r'M\.8 '), nxt2(r'E\.1 '),
       "**Âncora de fidelidade (Anexo J):**\n\n"+rows(r'^## Anexo J ', r'^## Anexo K ', ['c154'], keep_notes=False)],
      epigraph="**D75 (a receita, §6.4 é a DONA):** produção = **`random_search_optimizer`**; `nsgaii(pop=100,gen=500)` SÓ no piloto (1–2 problemas, mede o gap); pop-250 MORTA. Fallback do `RuntimeError` obrigatório. Ruído INFERIDO (não fixar `train_Yvar`). **Bucket-only (D54).**")

print("== RODADA 3 (standalone) ==")
R3_TOKENS=['3.1 ','3.2 ','3.3 ','3.4 ','3.5 ']
r3=strip_alg_items(sec(r'^### 22\.4 ', r'^### 22\.5 '), R3_TOKENS)
write('30_rodada3_standalone/00_contrato_rodada3.md', 'Rodada 3 — contrato transversal standalone (Python; offline + BO de autor)',
      [r3, sec(r'^### N\.1 ', r'^### N\.2 '), sec(r'^## 7\. ', r'^## 11\.5 '), sec(r'^### E\.9 ', r'^### E\.10 ')],
      epigraph=("**📋 LEITURA OBRIGATÓRIA ANTES DE CODAR (correção estrutural 2026-07-19):** este contrato de rodada NÃO contém o contrato de DADOS. Leia **`CONTRATO_DE_DADOS.md` (raiz do repo)** — as camadas ①②③④⑤⑥⑦, a **SONDA canônica** (§17.2.2/§3.1: artefato de 20.000 pontos; ONLINE lê a fatia de 2.000 a cada k=2 gerações; OFFLINE lê as 20.000 1× por modelo treinado, com `geracao`=NULL), a camada **⑦ `__final`** (DI-08/DI-13.9 — SÓ offline: TODOS os finais avaliados 1× e o ND filtrado DEPOIS), o **timing v5.2.1** (§17.6: `tempo_fit_s` [NULLABLE nos pisos] / `tempo_busca_s` / `tempo_pred_sonda_s` / `tempo_geracao_s` + bloco `timing` OBRIGATÓRIO no manifesto) e o **`.jsonl` enriquecido** (S.7.1/DI-10). O `REGISTRO_DECISOES_IMPLEMENTACAO.md` (DI-01..DI-14) traz o PORQUÊ de cada uma. Em divergência: SPEC > CONTRATO_DE_DADOS > este bundle."
                "\n\n"
                "**Decisões-chave:** D77 (**piso offline = DESDEO mode 12, GP-média = b5-sem-σ**; a listagem PlatEMO morreu) · D56 (b5 = 2 configs `b5r`/`b5m`) · "
                "D78 (**fallbacks pré-registrados**: c311→treed/sparse-GP substituto 'author-modified'; c149→best-effort, senão narrativa repousa no c311 + nota BNN futuro; flag `fallback_ativado`) · "
                "D68 (ND final SEM cap — salvar completo) · D62 (SeedSequence; base=1000·semente p/ e81/c149 — D22) · D79 (venv PRÓPRIO por repo; b5×c311 NUNCA co-importados — N.1.2) · "
                "**D86 (higiene torch por iteração no c149 — N.1.5)** · D54 (e81/c149/c122 bucket-only — **vale do M8 em diante, na bateria**; no Mac, até o M7, roda `enable_bucket=False` com as camadas LOCAIS COMPLETAS, **sem podar a ③** — RI-08; o resume que lista o bucket [D58] está no hardening do M7) [C122-10/DI-16.8]."))
R3ALGS={
 'alg_c122_thetadeadp':('c122 θ-DEA-DP (autor, Python/torch+DEAP)','3.1 ',['c122'],r'I\.6 ',r'L\.6 ',r'M\.12 ',r'E\.7 ','c122 ',
    "f_min/f_max dos fronts VERDADEIROS pela ASSINATURA (vantagem informacional DECLARADA — D73b); driver próprio bypassa o factory (env encolhe — S.8); cap anti-spin (fork do main loop); **bucket-only (D54)**; stub do visualizer."),
 'alg_b5_prob':('b5 Prob-RVEA (b5r, mode 7) / Prob-MOEA-D (b5m, mode 72) — OFFLINE','3.2 ',['b5'],r'I\.16 ',r'L\.16 ',r'M\.15 ',None,'b5 ',
    "**D56: DUAS configs** (`b5r`=mode 7 headline; `b5m`=mode 72 quase-fiel); Hyb fora. Patch :66–75 (bloco KDE morto); sklearn **0.21.3** (D80); venv próprio; `MPLBACKEND=Agg`; ambos entram no sweep (tiers small/medium)."),
 'alg_c311_tgprmo':('c311 TGPR-MO (autor, Python/DESDEO/GPy — OFFLINE)','3.3 ',['c311'],r'I\.17 ',r'L\.17 ',r'M\.17 ',None,'c311 ',
    "σ nas folhas = extensão nossa ('author-modified', D73b); **fallback D78** (treed/sparse-GP substituto se o venv py3.9+GPy não fechar); tier big=50k c311-only; vetorizar predict se o piloto mandar (D84); conferir `*_archive` do Population (fix: copiar do b5 — mesmo fork)."),
 'alg_c149_lbnmobo':('c149 LBN-MOBO (autor, Python/torch+pymoo) — reconstrução do loop','3.4 ',['c149'],r'I\.14 ',r'L\.14 ',r'M\.11 ',r'E\.3 ','c149 ',
    "**D41/D96: q=1 = HVI-greedy FECHADA** — HVI normalizado pelo min/max do arquivo OBSERVADO por iteração (NUNCA a S.5 — vazaria oráculo; cru degenera nos BBOB); ref=nadir-obs×1,1; desempate=maior σ²; fallback=aleatório-do-front (seeds.json). **D78: reconstrução best-effort** (núcleo ~250 linhas; o notebook do loop EXISTE no repo — mais fácil que a SPEC dizia). **D86: higiene torch OBRIGATÓRIA** (retreino a cada FE — caso-teste de RAM do piloto). **Bucket-only (D54)**; offset D22 (+1000·semente); fix `[:, :M]` (linha 46)."),
 'alg_e81_qpots':('e81 qPOTS (autor, sobre BoTorch 0.16.1)','3.5 ',['e81'],r'I\.12 ',r'L\.12 ',r'M\.9 ',r'E\.6 ','e81 ',
    "env BoTorch **0.16.1 PRÓPRIO** (isolamento duro); bounds=[0,1]^D no adapter (mata o bug maximin); offset D22 nos ~6 sítios de seed (D62); **bucket-only (D54)**; kernel 1 linha (Matérn — D30)."),
}
for fname,(title,chk,t64,ipat,lpat,mpat,epat,jtok,epi) in R3ALGS.items():
    parts=[checklist(chk), rows(r'^### 6\.4 ', r'^### 6\.6 ', t64), nxt2(ipat), nxt2(lpat), nxt2(mpat)]
    if epat: parts.append(nxt2(epat))
    parts.append("**Âncora de fidelidade (Anexo J):**\n\n"+rows(r'^## Anexo J ', r'^## Anexo K ', [jtok.strip()], keep_notes=False))
    write('30_rodada3_standalone/%s.md'%fname, title, parts, epigraph="**Específicas:** "+epi)

write('30_rodada3_standalone/alg_piso_offline_moead_media.md','Piso offline — MOEA/D-média (DESDEO mode 12, GP-média) [D77]',
      [sec(r'^### 3\.4 ', r'^### 3\.5 '), sec(r'^## 10\. ', r'^## 11\. '), sec(r'^## 11\. ', r'^## 11\.5 '),
       rows(r'^### 6\.4 ', r'^### 6\.6 ', ['Piso offline (MOEA/D-média)'])],
      epigraph=("**D77 (a casa canônica):** roda no **MESMO motor do b5** — `MOEA_D` (mode 12) do repo DESDEO — sobre **GP-média** (SurrogateKriging só-μ, sem σ) = **a ablação exata do b5** (DEF-E3: o contraste piso-vs-b5 mede exatamente o valor de usar σ). "
                "A antiga listagem 'built-in PlatEMO / Rodada 1' está MORTA. Python, Rodada 3, cartão R3 próprio. N interno = 100 (D65 não se aplica: sem pressão de orçamento). ND final sem cap (D68)."))

print("== SUB-ESTUDOS ==")
write('40_subestudos/batch_largebatch.md','Sub-estudo LARGE-BATCH (q=10) — Parte V-B [fechado por D66]',
      [sec(r'^## V-B\.1 ', r'^## 12\. ')],
      epigraph="**D66:** q=10; `maxFE_batch = 11D−1 + K·q`, **K=200** (2.000 infills); DoE **pareado com o principal**; roster c149/c262/e81/c154 + **piso Sobol-batch** (scrambled/Owen por semente); **qParEGO FORA**; ~5 problemas × 30 sementes; `run_id` com `exp=batch` (D55). Cada algoritmo usa o modo de lote **NATIVO** — sem fallback livre.")
write('40_subestudos/sweep_offline.md','Sub-estudo SWEEP offline (tamanho × distribuição) — §11.5 [D38/D51/D67]',
      [sec(r'^## 11\.5 ', r'^## V-B\.1 ')],
      epigraph="**D67 (MVNS):** amostrar em **[0,1]^D**; **μ=0,3·𝟙 FIXO** (viés consistente; semente varia só as amostras); **Σ=diag(0,1)**; clip aos bounds; mapear a nativo. **Roster:** b5r+b5m+e103 (small/medium) e c311 (small/medium/big) — D56. `run_id`: `sweep-{tier}-{dist}` (D55).")
write('40_subestudos/varredura_N_pisos.md','Varredura pré-registrada do N dos pisos online [D65]',
      [sec(r'^### 3\.2 ', r'^### 3\.3 '), sec(r'^### 6\.3 ', r'^### 6\.4 ')],
      epigraph="**D65:** N∈{10,20,30,50} × (5 problemas do sweep + 2 reps alta-D) × 5 sementes; critério = **mediana do IGD+ final (D70)**; escolhe **1 N por faixa de D** (baixa ≤5 / média / alta ≥20) ANTES da bateria. Piso offline mantém N=100.")

print("== ANALISE (R4) ==")
write('50_analise_R4/metricas_estatistica_caracteristicas.md','R4 — Métricas, testes estatísticos e análise por característica (§12–§15 + Anexo O)',
      [sec(r'^## 12\. ', r'^## 13\. '), sec(r'^## 13\. ', r'^## 14\. '), sec(r'^## 14\. ', r'^## 15\. '),
       sec(r'^## 15\. ', r'^## 16\. '), sec(r'^## Anexo O ', r'^## Anexo P ')],
      epigraph=("**Decisões-chave:** D69 (métricas sobre **f′=(f−ideal)/(nadir−ideal)**; ref HV=(1,1,…) normalizado) · D70 (**IGD+ final, mediana das 30** = endpoint primário; α=0,05; Friedman POR MÉTRICA; Nemenyi all-pairs; Holm nas rank-sum; rope=0,05 normalizado; **online × offline SEPARADOS**) · "
                "D71 (matriz 25×8 `characteristics.csv`; unidade=PROBLEMA; Friedman só onde ≥5 problemas — **D98: propriedade objetiva, re-derivada pelo autor**) · D72 (reference set 2-obj POR SEGMENTO; cache BBOB pop200×300gen×5seeds; 'nos 6; F1 analítico') · D73 (3 honestidades) · **D99: IGDX pós-hoc p/ os 4 MMF** · **D100: esta camada é pós-experimento (o autor refina/implementa no R4; não bloqueia a implementação)** · D80 (lib de métrica PINADA). **Aceitação da métrica (D92): HV(F1 analítico, ref 1,1 por coordenada) = 1,0433** (o 0,8333 = sanity do front, ref no nadir)."))

# artifacts + spec + registry + MANUAIS: cópias SÓ no modo pacote-externo (OUT != '.').
# No modo in-place (OUT='.'), SPEC/artifacts/manuais JÁ vivem aqui — auto-cópia daria SameFileError.
if os.path.abspath(OUT) != os.path.abspath('.'):
    os.makedirs(OUT+'/artifacts', exist_ok=True)
    for f in ['runs_matrix.csv','decisions.json','characteristics.csv','envs.json','repos.lock','anchors.json','seeds.json','params.json']:
        shutil.copy('artifacts/'+f, OUT+'/artifacts/'+f)
    shutil.copy(SPEC, OUT+'/SPEC_experimentos_v5.2.md')
    shutil.copy('REGISTRO_DECISOES_pingpong_v5.md', OUT+'/REGISTRO_DECISOES_pingpong_v5.md')
    shutil.copy('gen_bundles.py', OUT+'/gen_bundles.py')
    for m in ['CLAUDE.md', 'PROMPT_MESTRE.md']:
        if os.path.exists(m): shutil.copy(m, OUT+'/'+m)
print("\nTOTAL FILES:")
n=0
for root,_,files in os.walk(OUT):
    for f in sorted(files): n+=1
print(n,"files under",OUT)
EOF_MARKER = None
