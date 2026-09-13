# PROMPT — construtor dos 3 PROBLEMAS REAIS (torre → 3ª instância, 2026-07-30)

## §1 · Quem você é

Você constrói os **3 últimos experimentos** de um pipeline de mestrado maduro e validado:
**(P1)** otimização sobre um **dataset fixo** real · **(P2)** uma **caixa-preta** real como
função-objetivo · **(P3)** um **sistema de equações de um problema real**. Eles serão
INCORPORADOS ao repo `ua-dd-saea` — que você recebeu inteiro como contexto — e rodarão sob os
MESMOS 24 algoritmos, gates e contratos das outras 695 células/semente. **Você não inventa
infraestrutura: você produz as peças do contrato de entrada de problemas.**

## §2 · O panorama (o que aconteceu e o que está acontecendo AGORA)

1. **O pipeline está validado em profundidade.** Duas campanhas independentes: (a) validação
   de código com 143 agentes + refutação adversarial (310 achados → 64 confirmados, ZERO bugs
   de algoritmo); (b) análise de fidelidade F5 sobre as 666 células reais da semente 42
   (24/24 configs aprovados pelo autor, média 9,33; 14 céticos adversariais). As duas foram
   CRUZADAS: convergiram, se explicaram mutuamente e se corrigiram (`handoff/
   T11-PLANO-CONSOLIDADO.md` §0 tem o cruzamento; `f5/` tem a evidência).
2. **AGORA roda a campanha T11 — o refinamento final** (outra instância, em série):
   consolidamos TODAS as melhorias das duas validações + pendências históricas em uma SPEC
   (`SPEC_T11_REFINAMENTO_FINAL.md`) e ela está sendo executada fase a fase
   (`T11_STATUS.md` = o rastreador vivo; suíte foi de 394 → 516+ testes). Mudanças que JÁ
   afetam você: `campanha_id` no manifesto (schema v2) · checkpoint atômico + truncamento-com-
   dado no teto de 12h (DI-43/44) · gates de proveniência (3×1, gabarito de camadas) ·
   `iteration_seed` ganhará a célula no M8 (D7). **O repo é um alvo em movimento até o T11
   fechar** — desenvolva entendimento e desenho JÁ, mas rebase a integração no HEAD pós-T11.
3. **Depois do T11**: disparo das 30 sementes (~18.291 h-core, 4 máquinas) — e os SEUS 3
   problemas entram no grid (a decisão de rodá-los nas 30 sementes ou num subconjunto é do
   autor; prepare o desenho para ambos).

## §3 · Como absorver o conhecimento (ordem exata)

1. `CLAUDE.md` (raiz) + `claude_code_context/CLAUDE.md` — regras invioláveis (D81 pare-e-
   pergunte · D97 · precedência · git: NUNCA push, NUNCA add -A).
2. **`MAPA_ARTEFATOS.md` (raiz), em especial a SEÇÃO 8** — o mapa do repo com os scores da SUA missão; siga-o.
3. `CONTRATO_DE_DADOS.md` — o contrato das 7 camadas (inteiro).
4. SPEC §4, §5, §17, §12.1 + bundle `00_fundacao/05_problemas.md` (com S.5).
5. `src/problems.py` (o molde; estude 2 classes: uma analítica e o BBOB mock) + `src/doe.py`
   + `scripts/gen_sonda.py` + `src/budget.py` + `src/naming.py`.
6. `claude_code_context/artifacts/` (runs_matrix, seeds, characteristics, gabarito_camadas).
7. `SPEC_T11_REFINAMENTO_FINAL.md` + `T11_STATUS.md` — o que está mudando sob seus pés.
8. Convenção D90 de datasets (`data/datasets/` + manifests) — vital para o P1.

## §4 · O mapeamento dos seus 3 problemas nos NOSSOS regimes

- **P1 (dataset fixo)** → regime **`off`** (offline): o dataset É a camada ① (convenção D90,
  x_hash/f_hash); os 5 configs offline treinam 1× nele; endpoint = camada ⑦ (ND final
  reavaliado). Molde: e103/b5. Perguntas de desenho: tamanho do dataset (nossos tiers:
  31D−1 / 2.000 / 30-50k) e se entra no sweep.
- **P2 (caixa-preta real)** → regime **`main`** (online, q=1): cada avaliação real passa pelo
  wrapper de FE (D89: pontos bit-idênticos = cache-hit 0 FE — se a caixa-preta for
  NÃO-determinística isso QUEBRA; ver §5). maxFE=31D−1 exige D definido.
- **P3 (sistema de equações real)** → regime **`main`**; se a avaliação for barata, é o mais
  simples dos três (vira um "problema analítico" do ponto de vista do harness).

## §5 · AS 6 PERGUNTAS DE DESENHO que você deve responder AO AUTOR antes de codar

(D81: são decisões dele, não suas — leve opções + recomendação)
1. **Determinismo**: P2/P3 são bit-determinísticos para o mesmo X? Se não → D89, gates de
   determinismo e não-perturbação precisam de exceção DECLARADA (precedente: nenhum; é
   decisão nova).
2. **Custo por avaliação**: quanto custa 1 FE de P2? Isso dimensiona 31D−1, o teto de 12h
   (DI-44) e — crucial — **a SONDA**: 2000 pontos reais por artefato é viável? Alternativas:
   sonda reduzida · sonda só-offline · sem sonda (config fora da régua de surrogates, como os
   pisos). Cada uma tem custo científico distinto.
3. **Front verdadeiro**: P1-P3 não têm frente analítica → front EMPÍRICO pelo precedente
   BBOB/§12.1-D72 (cache NSGA-II longo) — com que orçamento? E `f_min/f_max` (S.5) de onde?
4. **M e D**: quais são os objetivos e a dimensão de cada problema? (define orçamento, DoE,
   lattices dos pisos, e se caem na classe D=12/M=3 onde o c154/c262 estouram teto).
5. **Bounds nativos**: reais e fixos? (o pipeline des-normaliza deterministicamente §5.5).
6. **Escopo no grid**: 3 problemas × quais experimentos (main? off? sweep?) × 30 sementes?
   (cada célula nova multiplica por 30).

## §6 · Regras de operação

- **Você NÃO altera**: harness, despachantes, gates, algoritmos, árvores vendorizadas. Sua
  superfície: `src/problems.py` (+ classes novas), artefatos de dados (doe/sonda/datasets),
  artifacts/ (linhas novas), e os guards de teste do catálogo ("exatamente 25" → 28).
- **Coexistência com o T11 (ativo!)**: trabalhe em faixa DISJUNTA (arquivos novos + os pontos
  acima); `git status` antes de todo add; staged alheio = aguarde, NUNCA dê unstage; add
  explícito por arquivo; suíte ANTES de commitar (interpretador:
  `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`).
- **Entregável em 2 atos**: (1º) **DOCUMENTO DE DESENHO** com as 6 respostas do §5 propostas
  ao autor + o plano das peças do checklist ("contrato de entrada", MAPA_ARTEFATOS.md SEÇÃO 8) — PARE aí e devolva
  ao autor; (2º) após o OK, a implementação + smoke (1 célula real × 1 config barato × cada
  problema, `portao.py` VERDE) + handoff `handoff/PROBLEMAS-REAIS_<n>.md`.
- A validação final da sua entrega será da torre de controle (workflow adversarial) — escreva
  para ser auditado: números medidos, hashes, nada de "funciona na minha máquina".
