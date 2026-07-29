# PROTOCOLO DE ANÁLISE DE FIDELIDADE — v1.0 (CONGELADO 2026-07-28)

> **O que é.** O protocolo padronizado que cada agente analisador executa por config na
> F5.3 (5 pilotos + 19 fan-out). Derivado da leitura profunda GROUNDED dos 5 pilotos
> (c217, e81, e7, c311, b1 — workflow `wf_dca1af2e-045`; anexos em `f5/leituras_piloto/`),
> aprovado pelo autor em 2026-07-28 (4 botões calibrados conforme recomendação da torre).
> Complementa o `handoff/F5-FRAMEWORK-v2.md` (o contrato da tarefa F5).

## 0. A CADEIA DE PRECEDÊNCIA (a regra que evita o falso-alarme sistemático)

Fonte da verdade sobre o comportamento IMPLEMENTADO, em ordem:
**dados → sigma_dict/params do manifesto → bundle alg_*.md (o livro-razão das divergências
D29) → decisões DI/D do REGISTRO → agente 4 → paper cru.**
O agente 4 descreve o PAPER e não conhece as divergências sancionadas (provado nos 5
pilotos: e7 δ=0,08/k=5 vs nosso δ=0,05/Ke=3 sancionados; b1 λ=11 vetores vs N=100 D20;
e81 TS-por-geração 🟠). Validar parâmetro do paper contra o run SEM consultar o bundle
⇒ reprova run fiel. O agente 4 entra como extrator do lado-paper (parâmetros,
contrafactuais, setup experimental) — NUNCA como gabarito do implementado.

## Etapa 0 — Kit + tabela de constantes esperadas

Kit por config: artigo .md (`corpus_artigos/_artigos_markdown/`) · agente4 `_full`+`_resumo`
· bundle `alg_*.md` · DIs do config · `CONTRATO_DE_DADOS.md` · células organizadas em
`resultados_experimentos/{alg}/` (+ métricas/sonda pré-computadas da F5.2).
**Antes de abrir qualquer dado**, derivar dos params a **tabela de constantes esperadas**:
nº de gerações/eventos/linhas por camada, blocos de sonda, campos de término, baseline de
guards ("ruído esperado": ex. e7 tem 1 cache_hit no init SEMPRE). A fidelidade estrutural
vira um diff contra o previsto.

## Etapa 1 — Leitura ordenada (obrigatória)

1. manifest: `status` + `params` + **`sigma_dict` (ANTES de tocar a ③)** + bloco `sonda`.
2. ⑥: chave de evento = **`rec`** (não "evento"); o evento de geração VARIA
   (`<alg>_gen` | `decision`); **mapa de término por config** (nunca `status` sozinho —
   bug B1): `motivo_parada` no manifesto (BoTorch/standalone) · `footer.termino` (MATLAB
   b1/e7…) · `footer.motivo` (c311/família offline standalone). Footer = 2 registros
   (runner + despachante) — não é duplicação.
3. Schemas reais das camadas (③: `regime` literal `'online'`/`'offline'`/`'sonda'`;
   `geracao` float64-nullable → `dropna().astype(int)`).
4. Só então as queries.

## Etapa 2 — Bateria universal U1–U12 (idêntica nos 24)

| # | Checagem | Assinatura |
|---|---|---|
| U1 | FE=31D−1 exato + `fe_index` denso 0-based (offline: ① = dataset, 100% `init`) | igualdade exata |
| U2 | init = 11D−1 + `doe_hash`≡sidecar + ΔX vs artefato ≤ eps-float32 | bit-a-bit |
| U3 | 1 fit por retreino no ④, conforme o regime declarado no sigma_dict | contagem exata |
| U4 | cadência da sonda: `g==1 ∨ g%2==0` + **última geração coberta mesmo ímpar** (finalProbe) | fórmula exata |
| U5 | join posicional sonda×gabarito: max\|ΔX\| ≤ eps-float32 (NUNCA por sonda_id — não existe) | ordem provada |
| U6 | WAPE + cobertura por bloco de sonda, **definição congelada (§5)** | curva por config |
| U7 | ④: `fit+busca ≤ tempo_geracao_s` em 100% E violação exatamente nas gerações com sonda (DI-13.10) | invariante dupla |
| U8 | `fe_treino_max` conforme regime do sigma_dict (NÃO-monotônico em b1/b4/c217 — DI-13.15) | conforme declarado |
| U9 | contadores de guard do ⑥ ≡ agregados do ⑤ (cache_hits etc.) | reconciliação exata |
| U10 | aritmética entre camadas com o off-by-one documentado por config (②=N+1 no b1; ④ ger-1 duplicada no e7; `n_iter = n_infills + cache_hits − c0`) | fecha exato |
| U11 | erro de fantasia nos infills: `real_solution_id`→① (μ vs f real do escolhido) | mediana por célula |
| U12 | (offline) ⑦: Pareto recomputado ≡ `nd_pos_real`; link posicional (ger,linha)→③ casa X bit-a-bit; razão nd_pos_real/n_final reportada | igualdade exata |

## Etapa 3 — Módulo de família

- **GP-BO** (b1, b3, c238, c262, c154, e81): a **query-joia da aquisição** — identidade
  fechada do EI (b1: fechou 891/891) / recomputo do maximin em [0,1]^D (e81: \|Δ\|<1e-5)
  / consistência de ranking dos restarts (c262/c154). Onde a identidade fecha, o uso da
  incerteza está PROVADO pelos dados. + curva de aprendizado via `modelo_hp`
  (lengthscales) + calibração σ.
- **NN-ensemble/MC-dropout** (e7, c149, c122-redes): σ estocástico — cobertura baixa É
  da família (medir, não reprovar); des-translação/des-transformação OBRIGATÓRIA antes
  de qualquer μ×verdade; **cap/esquecimento = comportamento fiel** (WAPE que não melhora
  não é falha — e7: n_treino constante 11D−1 por desenho).
- **Classificador par-a-par** (c217, c122, b4): score ternário/classe; `pred_confianca`
  constante por bloco POR DESENHO (Error1); consistência estado⇔desigualdade do `motivo`
  (c217: 100%); estado-3 → sentinela pred_score=0 (modelo não consultado).
- **Offline/treed** (c311, b5r, b5m, e103, moead_media, treed_media): 2 blocos de sonda
  **bit-idênticos** = prova do congelamento; σ-NaN como INFORMAÇÃO (cobertura de folhas
  no c311 — NaN-share por fase/regime); razão `nd_pos_real` como endpoint de fantasia;
  ② vazia e `real_solution_id` NULL por desenho (DI-16.17).

## Etapa 4 — Aspectos específicos do config

Cada patch/guarda/parâmetro do bundle vira um aspecto verificável na tabela-padrão:
`| aspecto | paper (ref) | SPEC/bundle mudou (D-xx) | evidência (camada/coluna/evento) |
query | valor medido | assinatura esperada | verificabilidade | classe |`.
**Graus de verificabilidade**: `direta` · `direta-declarativa` (config-echo — o log
declara; o elo código é coberto por anchors.json+repos.lock) · `indireta` ·
`não-verificável` (exige código/re-run → balde T).
As tabelas dos 5 pilotos (16–23 aspectos cada) estão prontas nos anexos.

## Etapa 5 — Classificação e score (BOTÕES CALIBRADOS pelo autor 2026-07-28)

- Cada aspecto → **(1)** conforme o artigo · **(2)** desvio sancionado (citar a decisão
  D-xx/DI-xx + o efeito) · **(3)** desvio inexplicado 🎯 (vai à F5.4) · **T** teto
  declarado (não-verificável).
- **Botão 2**: `% = aspectos na classe / (total − T)`; T listado à parte com a razão;
  denominador SEMPRE impresso.
- **Botão 3**: aspectos `direta-declarativa` contam como (1)/(2) **com a marca
  declarativa visível** na tabela.
- Score 0-10 pela régua do FRAMEWORK-v2 §F5.3b; itens (3) CONFIRMADOS na F5.4 são o que
  puxa o score. Recomendação: aceitar / aceitar+caveat / investigar / reprovar.

## Etapa 6 — Comparação canônica (Entrega 2; só os 17 com artigo)

Do setup do paper (via agente4 _full + artigo): interseção com nossos 25 problemas,
veredito POR problema em 3 níveis:
- `comparável` (mesma família E dimensão E M E orçamento na mesma ordem) → comparar
  indicadores; nosso ≥ artigo ⇒ válido; reportar quem venceu.
- `âncora direcional` (mesma família; só o SENTIDO compara — ex.: "ParEGO≫NSGA-II em
  DTLZ2a vale aqui?").
- **`incomensurável (eixo X)`** — **Botão 4**: quando nem direção há, o veredito é
  `incomensurável` + faixa-guia J (±3σ); NUNCA "artigo melhor" sob incomensurabilidade.
Piloto mostrou: a norma é incomensurável (orçamentos 2-20×, dimensões, M, métricas
diferentes; e81 sem tabela numérica; c311 sem IGD e fora do envelope N≥2000). BBOB
nunca compara com literatura (front empírico).

## Etapa 7 — Relatório padronizado por config

Ordem fixa: Ficha do mecanismo → tabela de aspectos (Etapa 4) → **% por classe (com
denominador)** → comparação canônica → veredito de contrato (interpretação dos ⚠ da
F5.2: "por desenho, cite a regra" vs "defeito, escale") → score + recomendação → teto
de verificabilidade (T) → armadilhas confirmadas. **1 conclusão = 1 tabela/gráfico** —
sem análise decorativa (regra do autor).

## 5. DEFINIÇÕES CONGELADAS (Botão 1)

- **WAPE**: por objetivo, no espaço **CRU** (des-transformado via `transf_params` do
  próprio bloco), `WAPE_j = Σ|μ_j − f_j| / Σ|f_j|` sobre as 2000 (online) / 20000
  (offline) linhas do bloco; reportar primeiro bloco, último bloco e tendência.
- **Cobertura**: fração com `|μ_j − f_j| ≤ 1,96·σ_j`, por objetivo (nominal ≈ 0,95);
  onde σ é NULL por desenho (RBF puro, piso-off, folhas sem GP) → N/A citando a regra.
- **b1 (mono-output)**: régua ESCALAR reconstruída por bloco com λ/min/max do
  `transf_params` — compara-se À PARTE (regra 4 do R4).
- **Piso de ruído entre máquinas**: desvio de indicador < piso medido (HV ≤1,55%;
  IGD+ ≤58,98% — validação cruzada O-18) NUNCA é evidência de infidelidade sozinho;
  cruzar sempre com a máquina real (`_logs_lotes/mac/*done.txt`; roster ≠ real para
  main/e7 [todo Mac], main/c238 [DIVIDIDO], main/b1 [parcial]).
- **Classificação vs comportamento**: nota baixa de COMPORTAMENTO em 1 semente ≠
  infidelidade (separar "mecanismo errado" de "semente infeliz" — caveat 8 do F5).

## 6. Fonte dos dados organizados

`/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/{alg}/{label}/{seed}/`
com label = `{problema}` (main/off) · `q10_{problema}` (batch) ·
`swap_{tier}-{dist}_{problema}` (sweep). Staging canônico do bucket em `_bucket_raw/`;
substituições de ⑥ (footer) documentadas em `_FONTES.csv`.

## Anexos (as 5 leituras-piloto grounded — tabelas de aspectos prontas)

`f5/leituras_piloto/leitura_{c217,e81,e7,c311,b1}.md` — cada uma com: ficha do mecanismo,
tabela de aspectos com queries EXECUTADAS e valores medidos, grounding (schemas/eventos
reais), setup do paper + vereditos de interseção, contradições agente4×bundle×paper,
armadilhas por config e teto de verificabilidade.
