# F5 FRAMEWORK v2 — validação de fidelidade da rodada-42 (CONGELADO 2026-07-28)

> **O contrato da tarefa F5.** Escrito pela torre de fidelidade, aprovado pelo autor em
> 2026-07-28 (v2: incrementos do autor sobre o desenho de 6 fases). Escopo: **24 configs**
> (17 com artigo — 16 papers, b5 vira b5r+b5m — + 7 controles), **666 células OK** da
> semente 42 (fonte: bucket `gs://mestrado_experiments`, READ-ONLY; 4 VMs TERMINATED).
> Doutrina: D97 (veredito é do AUTOR) · D29 (bússola de divergência) · D81 (ambiguidade ⇒
> pára) · caveats anti-falso-alarme do `handoff/F5-VALIDACAO-FIDELIDADE.md` §6 e do
> `HANDOFF_validacao_fidelidade.md` §3 (piso de ruído: HV ≤1,55% / **IGD+ até 58,98%**
> entre máquinas).

---

## 0. Protocolo de execução (vale para TODAS as fases)

1. **Relatório por fase**: ao fechar cada F5.x, a torre imprime no chat um relatório
   consolidado dos resultados daquela fase.
2. **Expectativa pré-declarada + parada dura**: cada fase declara ANTES o resultado
   esperado. Qualquer resultado fora do esperado ⇒ **PARAR a execução e pedir
   direcionamento do autor**. Pré-registrados como ESPERADOS (não disparam parada):
   as 29 não-OK do `INVENTARIO_nao_go_semente42.md`; células `ok` com
   `motivo_parada≠orcamento` (bug B1; caso provado `sweep-big-mvns/c311/MMF16_20`);
   ⑥ sem footer no bucket (upload precede fechamento); HV>1,1 em BBOB; desvio de
   indicador entre máquinas dentro do piso de ruído; ~1s/célula nos pisos.
3. **Read-only duro**: bucket só leitura (`ls`/`cat`/`cp bucket→local`); dados e código de
   algoritmo intocáveis; nunca `git push`/`git add -A`; nunca instalar sem autorização.
4. **Artefatos da F5**: saídas (tabelas, heatmaps, relatórios) em `f5/` na raiz do repo;
   dados baixados do bucket em `data/experiments/` local (estrutura espelhada).

## F5.1 — Gates de protocolo (666 células)

`portao.py` (accept+auditar+final_eval) sobre as 666, no env_main do Mac (bug B3),
com triagem por `motivo_parada` (bug B1) e conferência manual dos abortos (bug B2).
**Esperado**: verde geral nas 666. **Relatório**: matriz célula×gate + vermelhos novos.

## F5.2 — Régua comum + integridade + contrato + TEMPO

a) **Integridade do bucket (o "OK de não-corrompido" do autor)**: baixar TODAS as
   camadas das 666 células (~3,6 GB), abrir cada parquet (pyarrow, row-count > 0 e
   conforme), parsear cada `.jsonl` linha a linha, cada manifesto. Saída: veredito de
   integridade por arquivo (✅/🔴) — nenhum arquivo ilegível é esperado.
b) **Varredura de contrato**: cada célula × 7 camadas contra o `CONTRATO_DE_DADOS.md`
   (schema, colunas, cadência da sonda, 31D−1 na ①, ⑦ reconstituível, NULLs anotados
   p/ interpretação por config na F5.3) + **mapa "análise da dissertação → dado
   presente?"** (CONTRATO §9, item a item).
c) **Métricas oficiais**: `src/metrics.py` (gate D92 antes; IGD+ primária D70, HV,
   spacing), curvas métrica×FE por célula; sonda: corr/RMSE μ×f-real por bloco →
   curva "o surrogate aprendeu?" por config (a régua comum).
d) **⏱ Análise de TEMPO (incremento do autor)**: colher wall de cada célula
   (⑤ `timing.tempo_total_s` — chave ANINHADA — + ④ fit/busca/sonda) → **matriz
   config × problema×experimento com o tempo** + **heatmap** (fácil ver os caros) +
   **projeção 30 sementes** (M8/M9) por máquina/stack, com caveats: atribuição real de
   máquina via `_logs_lotes/mac/*done.txt` (e7 todo no Mac; c238 DIVIDIDO; b1 parcial),
   wall cross-stack só com ressalva §19. Saída: `f5/tempo_heatmap.html` +
   `f5/projecao_30seeds.md`.

**Relatório F5.2**: integridade + tabela contrato 666×7 + mapa análise→dado + heatmap
de tempo + projeção.

## F5.3 — Um analista por config (o coração) — em DUAS ondas

### F5.3a — PILOTO de protocolo (5 configs) → calibração com o autor
Antes do fan-out, a torre roda 5 configs-piloto diversos (2 stacks, on/offline,
GP/NN/classificador) com o protocolo-rascunho, entrega os 5 relatórios + o protocolo ao
autor, e **só depois da calibração** (ajustes do autor) dispara os 19 restantes.
O protocolo padronizado vira `f5/PROTOCOLO_ANALISE_FIDELIDADE.md` (como o agente lê o
artigo, o que extrai, como cruza com os dados, como classifica e pontua).

### F5.3b — Fan-out (19 restantes) com o protocolo congelado

**Kit por agente**: artigo `.md` (`corpus_artigos/_artigos_markdown/`; PDF fallback) ·
análise agente 4 (`agente4/<id>/<id>_full.md` + `_resumo.md`) · bundle `alg_<id>.md` ·
receita L.x · DIs do config no REGISTRO · CONTRATO + `sigma_dict` · células do config
(+ métricas/sonda prontas da F5.2) · bloco `comportamento_smoke` do finder da validação
final (journal `wf_c451718a-b88` — pré-leitura, hipóteses a confirmar/refutar).

**Entrega 1 — Dissecação em 3 CLASSES (taxonomia do autor).** O agente enumera a lista
FECHADA de aspectos comportamentais (receita L.x + patches/guardas do bundle + universais:
orçamento, DoE, cadência de retreino, seleção, uso da incerteza…) e classifica CADA um:
- **(1) conforme o artigo** — com evidência (⑥/③/⑤);
- **(2) desvio sancionado pela SPEC** — citando: o que o artigo esperava · o que
  aconteceu · QUAL decisão (D-xx/DI-xx) · como ela produziu o efeito;
- **(3) desvio NÃO explicado** — 🎯 o alvo; vai à segunda avaliação (F5.4).
**% por classe = aspectos na classe / total** (denominador explícito no relatório).
Evidência mínima suficiente: **1 conclusão = 1 tabela ou 1 gráfico** (regra do autor —
sem análises decorativas).

**Entrega 2 — Resultados vs FONTE CANÔNICA** (só os 17 com artigo): o `_full.md` do
agente 4 dá o setup experimental do paper → (a) há interseção com nossos 25 problemas?
(problema E dimensão E orçamento E nº de objetivos); (b) se comparável, comparar
convergência/diversidade; (c) veredito: `nosso melhor` / `empate prático` /
`artigo melhor` / **`sem interseção comparável — orçamentos incomensuráveis`** (decisão
do autor: quando o orçamento do paper é ≫ 31D−1, usa-se este veredito + faixa-guia J
±3σ; nunca "artigo melhor" por comparação incomensurável). Nosso ≥ artigo ⇒ válido.
BBOB nunca compara com literatura (front empírico).

**Entrega 3 — Veredito de contrato do config**: interpreta os ⚠ da F5.2 ("por desenho,
cite a regra do CONTRATO/sigma_dict" vs "defeito, escale").

**Entrega 4 — Score 0-10 + recomendação** (`aceitar`/`aceitar+caveat`/`investigar`/
`reprovar`), pela régua congelada:

| Score | Critério |
|---|---|
| 10 | tudo (1)/(2), cada (2) ancorado em decisão documentada; contrato perfeito; saúde limpa |
| 9 | idem, com (3) menores já investigados e provados benignos |
| 8 | (3) periférico com explicação plausível não provada; mecanismo central limpo |
| 7 | um (3) em sub-mecanismo não-central, impacto delimitado |
| 5–6 | (3) no laço central OU anomalia de saúde inexplicada — exige decisão do autor |
| 3–4 | divergência de mecanismo confirmada sem sanção da SPEC (bug provável) |
| 1–2 | mecanismo central errado; dados inutilizáveis até correção |
| 0 | a implementação não corresponde ao algoritmo do artigo |

**Controles (7)**: entregas 1, 3 e 4 (entrega 2 = N/A; o "artigo" é a especificação
canônica do método + a receita nossa; moead_media/treed_media = extensões 🟢 declaradas).

## F5.4 — Verificação adversarial + segunda avaliação dos (3)

Todo aspecto (3) e todo 🔴 recebe verificadores independentes com viés de REFUTAR
(default = falso-positivo). Para os (3) sobreviventes, a segunda avaliação do autor:
**bug de implementação** (→ escalar com arquivo:linha + D29) · **comportamento legítimo
sob nosso orçamento** (→ vira resultado) · **dado corrompido** (→ célula sai da análise).
Insumo adicional: os 107 resultados salvos da validação final (32 finders + 75
verificadores, journal `wf_c451718a-b88`) — consumidos como evidência prévia, sem re-rodar.

## F5.5 — Transversais

SA×pisos (vantagem×D — a tese) · online×offline do mesmo algoritmo · sweep small→
medium→big (mais dado → melhor?) · batch q=1×q=10 (caveat DI-37.4: contraste limpo =
c262/e81) · agrupamento por características (`characteristics.csv`, §15).

## F5.6 — O RELATÓRIO FINAL ("ultra mega validação")

Formato para o AUTOR ler, do urgente ao detalhe:
1. **Página 1 — "Onde olhar primeiro"**: só o que NÃO está bem (🔴/⚠), rankeado,
   1 frase + ponteiro por item (se vazio, diz explicitamente).
2. **Página 2 — MATRIZ-MESTRA** dimensões × 24 configs, células ✅/⚠/🔴/⬜/N/A com
   nota de rodapé: P1 protocolo/gates · P2 contrato · P3 mecanismo vs artigo
   (**%1/%2/%3**) · P4 saúde/sonda · P5 vs fonte canônica · P6 vs pisos/transversais ·
   P7 adversarial · **Score final + recomendação**.
3. **24 capítulos por config**: o relatório de fidelidade (dissecação 3 classes +
   evidência mínima + canônica + contrato + score justificado).
4. **Escalações**: tudo que é decisão do autor, com recomendação.
Entregável: atualização do `DOSSIE_FIDELIDADE_R1.md` + `f5/RELATORIO_FINAL_F5.md`.

## F5.7 — PLANO DA RODADA PERFEITA (incremento do autor)

Consolidar TODOS os aprendizados/correções da rodada-42 num plano de reparo para uma
**segunda rodada de fidelidade que rode perfeita**. Entram (lista viva, cresce com a
F5.3/F5.4): bugs do harness **B1** (status mascarado, `experiments.py:209`), **B2**
(token `cache_cap`≠`cache_hit_travado`), **B3** (accept falso-VERDE sem pyarrow) ·
**T10** (rito de truncamento BoTorch — a despriorização custou as células c154/batch
sem parquet) · fallback do amostrador JES (c154/ZDT6+BBOB_F55 — conferir se o paper
prevê degradação graciosa) · condicionamento do GP em WFG1 (c262) · defeito b1/DTLZ4
(mínimos quadrados subdeterminado, determinístico em 2 arquiteturas) · `mirror_run` não
espelha run falho (evidência órfã em disco de VM) · `lote3s.sh --teto-s` (corrigido
28/07) · correção do número da DI-40 (~6,3h → 0,87-2,99h medido) · extensão DI-40
(batch/c262 5/5; main/c154 D≥12) com base empírica · O-20/O-21/O-22 a redigir ·
proveniência de células com host≠roster · nota das 8 células encerradas por decisão ·
+ tudo que a F5 revelar. Saída: `f5/PLANO_RODADA_PERFEITA.md` — item a item com
recomendação, custo e o que re-rodar; decisões do autor.

---

## Ordem de execução e portões de parada

F5.1 → relatório → **F5.2** → relatório → **F5.3a piloto (5)** → calibração do
protocolo COM O AUTOR → **F5.3b fan-out (19)** → **F5.4** → **F5.5** → relatórios →
**F5.6 relatório final** → **F5.7 plano da rodada perfeita**. Parada dura em qualquer
resultado fora do esperado, em qualquer fase.

## Insumos verificados (2026-07-28)

- Bucket: 666 OK confirmadas por censo regenerado (censo_bucket.py v2; conta
  `gdmello.nunes@gmail.com`).
- Planilha `mapa_literatura_v7.xlsx` aba `selecionados`: 16 IDs ≡ nossos configs.
- Artigos: `corpus_artigos/_artigos_markdown/<id>. *.md` (16/16; PDFs nas subpastas).
- Agente 4: `agente4/<id>/<id>_full.md` + `_resumo.md` (16/16).
- Journal da validação final: 107 resultados salvos (32 finders + 75 verificadores).
- Kits por família (fallback de contexto): OneDrive `dissertacao/kits_escritores/`.
