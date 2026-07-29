## moead-M16 — VEREDITO: **REFUTADO**

**Resumo em 3 linhas**
As 30 divergências de `n_front1` (incluindo as 16 ditas "sem mecanismo") são **100% explicadas pela D53**: o ⑥ grava `n_front1 = sum(NDSort(pop.objs,1)==1)` sobre **float64 em memória** (`src/piso_instrument.m:43-44`), enquanto a ① — a única fonte do recomputo — é **float32** (D53), e o colapso f64→f32 tanto **cria** empates de coordenada (log = recomputo+1, 26 casos) quanto **destrói** dominâncias (log = recomputo−1, 5 casos, com X bit-idêntico em float32 entre sids distintos). Testei as 469 gerações com um bracket aritmético de arredondamento: **469/469 dentro, 0 inexplicadas**; nos 4 pisos, **1.634/1.634**. O falso-positivo tem duas causas nomeadas: (a) decisão desconhecida — **D57 item 3** e a **regra R4#1 do CONTRATO** registram literalmente este fenômeno; (b) erro de query — o analista citou no texto a coluna **errada** do seu próprio CSV e nunca testou igualdade exata de coordenada nem usou o `nadir_front1`, que é a testemunha float64 gravada ao lado do campo suspeito.

---

### O que tentei para derrubar (os 4 passos)

**1 · DECISÃO — caiu aqui, sozinho.** Três textos vinculantes cobrem o fenômeno *ipsis litteris*:
- **D57 item 3** (`claude_code_context/REGISTRO_DECISOES_pingpong_v5.md:143`): *"o ① armazena x em float32 (D53); dois x distintos abaixo da resolução float32 = 2 ids com x gravado idêntico — inócuo (join é por id)"*.
- **CONTRATO_DE_DADOS.md §1**: *"dedup/joins por `solution_id`, NUNCA pelo X armazenado (float32 pode colidir pontos float64 distintos — **provado**)"*; e **R4 regra 1** (linha 361) repete a proibição.
- **D53** nota (i): *"o erro relativo ~10⁻⁷ do float32 no ① é aceito e documentado"*.
A cláusula "inócuo (join é por id)" é verdadeira para joins — e é exatamente por isso que ninguém previu que ela **não** é inócua para *recomputo de dominância*. Isso é o buraco de doc (item (d) abaixo), não um desvio de mecanismo.

**2 · QUERY — reproduzi, e a evidência do analista não sobrevive.** Código próprio, do zero (`r1_reproduz.py`): **439/469 batem, 30 divergem — o mesmo conjunto exato** que ele achou. Mas as refutações dele não seguram:
- Ele escreveu *"a folga relativa mínima… é 1,0e−2 a 1,8e−2 — cinco ordens de grandeza acima do ULP float32 (única exceção ZDT6 g3, 9,6e−7)"*. No **seu próprio** `f5/baterias/moead/moead_nfront1_gap.csv`, a coluna `min_rel_gap` nessas 16 gerações vai de **4,76e−07** (DTLZ7 g18 e g19) a **3,61e−03**. O intervalo "1,0e−2 a 1,8e−2" é a coluna **`q01`** (máx. 1,10e−2), não a folga mínima. E ZDT6 g3 não é a única exceção: DTLZ7 g18/g19 são **2× menores**.
- Mesmo `min_rel_gap` mede a grandeza errada: a folga que **decide** a dominância é a da coordenada que **empata**, e ela vale **0,0 exato** (bits iguais). Em **30/30** das gerações divergentes existe pelo menos um par com coordenada bit-idêntica em float32 (de 2 a 49 pares por geração, `r2_bracket.csv`).
- **Testemunha que ele não usou**: `piso_instrument.m:46` grava `nadir_front1 = max(PopObj(fno==1,:))` em **float64** — é o max componentwise da frente-1 *que o MATLAB viu*. Controle positivo: nas 439 gerações que batem, `float32(nadir_front1_log)` é **idêntico** ao max da minha frente-1 em **439/439** — o instrumento é válido. Nas divergentes ele **aponta o indivíduo perdido**: ZDT1 g5 → `nadir_front1[1] = 4.292812775200402` = o `f1` do **sid 381**, que meu recomputo f32 descarta (o max da minha frente-1 é 3,9429, do sid 307). ZDT1 g6→399, g7→414, g8→427, g9→444, g10→460 — as "seis gerações consecutivas misteriosas" são seis offspring sucessivos que colidem, um por geração, com o mesmo incumbente 307.
- Contagem: ele reportou 12(+1)/4(−1) entre as 16; o medido é **13(+1)/3(−1)**.

**3 · CÓDIGO — o comportamento é por construção, não anômalo.** `src/experiment.m:2531` (`piso_hook`) chama `hook_output` e depois `piso_instrument` **na mesma invocação**, ambos lendo `Algorithm.result{end,2}` ⇒ a população é bit-idêntica nas duas camadas. O que difere é só a precisão: `hook_output.m:36-45` grava a ② como **solution_id** e nada mais (os objetivos vêm do join com a ① float32); `piso_instrument.m:43` roda `NDSort` sobre `pop.objs` em **double**. E o `NDSort` não tem quirk: `NDSort.m:57` despacha `if M<3 || N<500` → com N∈{15,20} é **sempre ENS_SS**, que é ordenação não-dominada exata (o `unique(...,'rows')`+`FrontNo(Loc)` devolve duplicatas todas à frente 1, igual ao meu recomputo). Nenhum bug: **duas precisões, um mesmo conjunto**.

**4 · CONTROLE POSITIVO/NEGATIVO — aparece em toda parte ⇒ é convenção.** Rodei o mesmo teste nos outros 3 pisos (mesmo `piso_instrument.m`, mesmo writer). Taxa de divergência: **nsga3 72/413 = 17,4% · nsga2 50/376 = 13,3% · smsemoa 44/376 = 11,7% · moead 30/469 = 6,4%** — o moead é o **menos** afetado dos quatro. O "Bônus" que a §8 pediu está respondido: **é transversal aos 4 pisos**, e como convenção de leitura, não como defeito.

---

### Por que caiu — o bracket que fecha 469/469

O arredondamento f64→f32 (round-to-nearest) é **monótono não-decrescente**. Logo:
- `F32[i,m] < F32[j,m]` ⇒ `F64[i,m] < F64[j,m]` (ordem **certa**);
- `F32[i,m] == F32[j,m]` ⇒ ordem em F64 **desconhecida**.

Defini `lo` = ND padrão sobre a ① float32 (o recomputo do analista) e `hi` = ND usando só dominância **certa** (`<` em **todos** os objetivos). Resultado (`r2`, `r7`):
- **26 divergências com Δ>0**: todas com `lo ≤ log ≤ hi`. Ex.: ZDT1 g5 `lo=10, log=11, hi=13`; DTLZ4 g1 `lo=7, log=15, hi=15`.
- **5 divergências com Δ=−1** (DTLZ3 g18, DTLZ7 g30, MMF11_L g3, ZDT1 g34, ZDT3 g34): `lo` deixa de ser limite inferior quando **dois sids distintos têm a linha de objetivos bit-idêntica em f32** — em f64 um pode dominar o outro. Achei **exatamente uma** colisão desse tipo, com **exatamente 2 sids distintos**, em **cada uma das 5** (`r3`): sids `340/351`, `621/625`, `2/38`, `819/837`, `811/829`. Corrigindo `lo` por esse excesso: **`lo' ≤ log ≤ hi` em 469/469 · 0 INEXPLICADAS** (e 1.634/1.634 nos 4 pisos).

E a causa raiz é o **X**, não o F (`r5`): os pares decisivos têm coordenadas de X bit-idênticas em float32 — DTLZ7 g30 sids 621/625 e DTLZ3 g18 sids 340/351 têm o **X inteiro idêntico** nas 22 e 12 coordenadas; ZDT1/ZDT3 g34 idênticos em 29 de 30. Globalmente, **3,3% a 8,6% de todos os pares de sids** compartilham ≥1 coordenada de X bit-idêntica (ZDT1 6,75%, DTLZ7 8,56%). Como `ZDT1.f1 = X[:,0]` (`src/problems.py:308`), ZDT3 idem e DTLZ7 tem `f_i = x_i` para i<M, o empate migra direto do X para o objetivo — **por isso o "resgate em float64" dele era impossível aqui**: reavaliar `problems.py` em f64 a partir do X float32 da ① reproduz o mesmo empate. Reproduzi a bifurcação dele exatamente (`r6`): o recomputo f64 resgata **7/23** casos — DTLZ4 g1,2,3,16,17 + ZDT1 g34 + ZDT3 g34 — e nenhum dos outros 16. No DTLZ4 a perda é no **F** (underflow denormal) e F é função não-linear de X, então reavaliar **restaura** a resolução; nos 16, a perda é no **X** e é irreversível. A bifurcação 14×16 é uma propriedade da estrutura do problema, não um mecanismo desconhecido.

---

### Enquadramento e bússola D29

**Não há divergência artigo×código ⇒ a bússola D29 não se aplica** (nenhuma das cinco cores: não é 🔴 bug do autor original, não é 🔵 versão, não é 🟠 detalhe de implementação, não é 🟣 erratum, não é 🟢 extensão nossa). O MOEA/D stock não computa frentes em ponto algum — `n_front1` é campo do mínimo comum DI-10, puramente descritivo.

Reclassificação do aspecto **M16: (3) inexplicado 🎯 → (2) desvio sancionado**, citando **D53 + D57 item 3 + CONTRATO R4#1**.
Fica um resíduo pequeno de **classe (d) — DEFEITO DE INSTRUMENTAÇÃO/DOC para a torre**: o mecanismo está certo e o número do log está *mais* certo que o recomputo, mas o CONTRATO só proíbe *join* por X float32 e nunca advertiu que **recomputo de dominância a partir da ① também é lossy**. Faltou a regra; sem ela, o próximo auditor cai no mesmo buraco (e três dos quatro pisos cairiam com o dobro da frequência).

---

### Impacto

- **Nenhuma célula sai da análise.** Nenhum número publicado muda. `n_front1` não alimenta métrica alguma: a única ocorrência a jusante é `scripts/accept.py:1278`, um teste de **presença** de chave.
- **`f5/relatorios_config/moead.md` muda em quatro pontos**: (i) §2.1 linha M16 e §2.2 bloco M16 → classe **(2)**; (ii) §3 tabela de classes: **(1) 8 = 29,6% (inalterado) · (2) 18→19 = 70,4% · (3) 1→0 = 0,0%**; (iii) §7 item 3 (o único fundamento do desconto de nota) cai ⇒ pelo raciocínio do próprio relatório o **SCORE vai de 9,0 para 10,0 — ACEITAR**; (iv) §9 armadilha #7 é reescrita: *"30/469 divergem, **todas** por float32; use o bracket [ND_f32, ND_certo] corrigido por colisões de linha — ±1 é esperado, o campo NÃO serve de invariante de gate"* — o conselho operacional dele estava certo, a justificativa é que estava errada.
- **A §M9 permanece intacta e é promovida**: ela já tinha diagnosticado a família certa (float32 × problema mal-condicionado) e já registrava que o ⑥ preserva o valor float64; M16 é o **mesmo** fenômeno, e o relatório perdeu por não estender a §M9 do F para o X.
- Sobe de moead-específico para **transversal dos 4 pisos** — como **convenção de leitura**, não como achado.

---

### Ação p/ F5.7 + custo

1. **(torre · doc) Nova regra R4#10 no `CONTRATO_DE_DADOS.md`**: *"`n_front1`/`nadir_front1`/`ideal`/`nadir_pop` do ⑥ são float64 sobre `pop.objs`; a ① é float32 (D53). Recomputo de dominância a partir da ① é LOSSY nos dois sentidos: valide por bracket `[ND_f32, ND_certo]`, corrigido por grupos de linha f32 idêntica com sids distintos. |Δ|=1 é esperado e não é defeito."* — **~20 min, 0 CPU**. Prioridade alta: é o item que impede a recorrência nos relatórios de nsga2/nsga3/smsemoa (que têm 2–3× mais divergências que o moead).
2. **(ferramenta) `nd_bracket_f32()` no toolbox da F5**, portada de `r7_veredito.py` — **~30 min, 0 CPU**.
3. **NÃO fazer: promover a ① a float64.** Resolveria o recomputo, mas exige re-export ⇒ **re-run das 666 células**; a D53 já pesou e rejeitou (o ganho de storage do ①/② é "ilusório", mas o custo de re-rodar não é). Custo proibitivo, benefício nulo para a dissertação.
4. **(opcional, só se houver re-run por outro motivo)** 1 linha em `src/piso_instrument.m` logando `front1_sids` (os ids da frente-1) tornaria o campo exatamente auditável. **Custo marginal ~0 se acoplado à rodada M8/M9 de 30 sementes; caso contrário, não vale.**

**Evidências e scripts** (todos executáveis, dados READ-ONLY) em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/moead-M16/`: `r1_reproduz.py`+`r1_gap.csv`/`r1_nadir.csv` (reprodução independente, 439/469) · `r2_bracket_f32.py`+`r2_bracket.csv` (bracket nos 4 pisos) · `r3_delta_negativo.py`+`r3_delta_negativo.csv` (as 9 colisões de linha inteira) · `r4_testemunha_nadir_front1.py`+`r4_testemunha.csv` (controle positivo 439/439 + o indivíduo nomeado em cada divergência) · `r5_x_float32.py`+`r5_colisao_X.csv`/`r5_pares_decisivos.csv` (colisão no X) · `r6_reaval_f64.py`+`r6_reaval_f64.csv` (por que o resgate f64 salva 7/23) · `r7_veredito.py`+`r7_veredito.csv` (**469/469 · 1.634/1.634 · 0 inexplicadas**).