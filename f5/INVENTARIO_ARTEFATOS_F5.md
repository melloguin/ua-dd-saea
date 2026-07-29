# INVENTÁRIO EXAUSTIVO DOS ARTEFATOS DA VALIDAÇÃO F5

> **O que é.** O catálogo COMPLETO de tudo que a validação de fidelidade da rodada-42
> (F5) produziu: para cada artefato, **o que é, o que contém, qual fase o gerou e para
> que serve**. Diretiva do autor (2026-07-29): *"TUDO de informação que for gerado no F5
> deve ser preservado na forma de artefatos"*.
> **Local canônico:** `ua-dd-saea/f5/` (versionado no git; 19 commits `[F5*]`).
> Os DADOS analisados ficam fora daqui, em
> `~/Documents/python_repos/mestrado/resultados_experimentos/` (organização do autor) e
> no espelho do bucket.

## Visão geral

| grupo | itens | volume | fase que gerou |
|---|---:|---:|---|
| Contratos do método | 3 | 36 KB | pré-F5.1 · F5.3a |
| Registro-mestre | 1 | 25 KB | todas (vivo) |
| Evidência mecânica (fases 1-2) | 8 | 3,4 MB | F5.1 · F5.2 |
| Trajetórias métricas | 664 | 2,6 MB | F5.2c |
| Relatórios por config | 24 | 1,6 MB | F5.3a-v1.1 · F5.3b |
| Vereditos adversariais | 14 | 200 KB | F5.4 |
| Transversais | 6 | 25 KB | F5.5 |
| Consolidação final | 4 | — | F5.6 · F5.7 |
| Baterias (scripts + evidência bruta) | 934 | 99 MB | todas |

---

## 1. CONTRATOS DO MÉTODO — o que define COMO a validação foi feita

### `handoff/F5-FRAMEWORK-v2.md` *(fora de `f5/`, na pasta handoff)*
**Fase:** desenho, antes da F5.1 (commit `7a731ac`).
**O que é:** o contrato da tarefa inteira — as 8 fases (D, F5.1 a F5.7), o protocolo de
execução (relatório por fase, parada dura em resultado fora do esperado), o escopo
(24 configs, 666 células), a régua de score 0-10 e a doutrina herdada (D97, D29, D81).
**Serve para:** saber o que foi combinado e por quê; é o documento que um auditor externo
lê primeiro.

### `f5/PROTOCOLO_ANALISE_FIDELIDADE.md` (10,8 KB)
**Fase:** congelado após a leitura profunda dos 5 pilotos (commit `effc185`); revisado
para **v1.1** por ajuste do autor (commit `c6a0ada`).
**O que é:** o método que CADA agente analisador executou. Contém: a **cadeia de
precedência** (dados → `sigma_dict` → bundle → decisões DI → agente-4 → paper cru — a
regra que evita reprovar run fiel por parâmetro de paper), a ordem de leitura obrigatória,
a **bateria universal U1-U12**, os **4 módulos de família** (GP-BO, NN-ensemble,
classificador par-a-par, offline/treed), a taxonomia de classes (1)/(2)/(3)/T, as
**definições congeladas** de WAPE e cobertura, e o formato do relatório (Etapa 7, versão
rica: um bloco narrativo por aspecto).
**Serve para:** reproduzir a análise; auditar se um relatório seguiu o método; e é o
molde para a validação da próxima rodada.

### `f5/leituras_piloto/leitura_{c217,e81,e7,c311,b1}.md` (5 arquivos, 140 KB)
**Fase:** pré-protocolo (workflow `wf_dca1af2e-045`).
**O que é:** a leitura profunda GROUNDED que originou o protocolo. Cada uma tem: ficha do
mecanismo do artigo, tabela de aspectos verificáveis **com a query já testada contra
células reais**, o grounding executado (schemas reais, eventos reais do ⑥, `sigma_dict` na
íntegra), o setup experimental do paper com o veredito de interseção, as contradições
agente-4 × bundle × artigo, e o teto de verificabilidade.
**Serve para:** mostrar que o protocolo não é teórico — cada checagem nasceu testada.

---

## 2. REGISTRO-MESTRE

### `f5/RELATORIO_F5.md` (24,9 KB) — **o documento central**
**Fase:** vivo desde a F5.1; atualizado ao fim de cada fase.
**O que é:** o registro exaustivo, fase a fase, do que se comportou como esperado e do que
não — cada "não" com causa provada. Seções: §0 sumário + itens acumulados para a torre
central · §1-3 download/organização/verificação · §4 gates (a causa única dos 44 e os 5
vermelhos dissecados) · §5 integridade/contrato/métricas/sonda/tempo · §6 pilotos · §7
adversarial (vereditos + padrão sistêmico ZDT4 + **auto-reporte do incidente da própria
validação**).
**Serve para:** é o que a torre central de implementação lê para corrigir o harness.

---

## 3. EVIDÊNCIA MECÂNICA — fases F5.1 e F5.2

### `f5/gates_f51.csv` (103,8 KB · 666 linhas)
**Fase:** F5.1. **Conteúdo:** `exp, alg, problema, exit, detalhe` — o veredito do
`portao.py` (accept + auditar + final_eval) célula a célula, com a mensagem do gate.
**Serve para:** rastrear por que qualquer célula passou ou não; é a prova documental de
que os 666 foram gateados (não amostrados).

### `f5/integridade_f52a.csv` (6,9 KB · 111 linhas)
**Fase:** F5.2a. **Conteúdo:** só os NÃO-OK — `alg, exp, problema, camada, veredito,
detalhe`. Vereditos: `VAZIO` (105 ③ de pisos, por desenho), `JSONL_RUIM` (1: b1/WFG1, 49
eventos truncados), `JSONL_1LINHA_RASGADA` (5).
**Serve para:** é o "OK de não-corrompido" que o autor pediu — todo parquet aberto, todo
jsonl parseado linha a linha, todo manifesto lido (~4.490 arquivos).

### `f5/contrato_f52b.csv` (9,5 KB · 197 linhas)
**Fase:** F5.2b. **Conteúdo:** desvios contra o `CONTRATO_DE_DADOS` — todos da mesma
classe: `⑤ CHAVES faltam ['params']` em 7 configs (c217, c262, c154, b5r, b5m,
moead_media, sobol_batch).
**Serve para:** documenta que a estrutura fechou 100% (contagens, fases, schemas, sonda,
⑦, `fe_final`, `q=10`, `sigma_dict`) e isola a única não-conformidade real.

### `f5/metricas_finais_f52c.csv` (75,6 KB · 664 linhas)
**Fase:** F5.2c. **Conteúdo:** `igd_plus, hv, igd, gd, spacing, n_nd` por célula, pelo
`src/metrics.py` oficial (gate D92 = 1,04333 verificado antes).
**Serve para:** base quantitativa comum de TODAS as análises posteriores; é o que a F5.5
e os 24 agentes consumiram (proibido recomputar).

### `f5/trajetorias/{exp}_{alg}_{problema}_42.json` (664 arquivos, 2,6 MB)
**Fase:** F5.2c. **Conteúdo:** 20 checkpoints por célula com as 5 métricas + `n_nd` no
conjunto ND acumulado até cada FE.
**Serve para:** a checagem de monotonicidade da Classe B (saúde) e as curvas
métrica×FE da dissertação.

### `f5/sonda_f52e.csv` (3,1 MB · 44.928 linhas) — **o maior artefato analítico**
**Fase:** F5.2e. **Conteúdo:** por célula × bloco × objetivo: `wape, corr, cobertura95,
n_validas, n_nan, fe_treino_max, modelo_flag`. 461 células regressoras, join posicional
com o gabarito, des-transformação pelo `transf_params`.
**Serve para:** responder "o surrogate aprendeu?" na **régua comum** — é o instrumento-mestre
da Classe B. ⚠ Caveat de leitura: onde σ é NaN por desenho (treed-GP), `cobertura95` só
cobre os pontos com σ válido — ler junto com `n_validas`.

### `f5/tempo_f52d.csv` (27,8 KB · 665 linhas)
**Fase:** F5.2d (corrigido na F5.3a). **Conteúdo:** `exp, alg, problema, label, maquina,
wall_s` — o wall do ⑤ (`timing.tempo_total_s`, chave aninhada), com a coluna `maquina`
já **corrigida** para as 31 células recuperadas no Mac (O-19; roster ≠ real).
**Serve para:** a projeção de custo do M8/M9 e o diagnóstico de célula anômala.

### `f5/tempo_heatmap.html` (54 KB) e `f5/tempo_heatmap_30seeds.html` (59 KB)
**Fase:** F5.2d. **O que são:** heatmaps standalone (sem dependências) config × célula —
o primeiro com o wall da semente 42, o segundo com a **projeção h-core para 30 sementes**,
com totais por config e por problema e o total geral (~10.173 h-core).
**Serve para:** ver num relance quais células dominam o custo da campanha.

### `f5/projecao_30seeds.md` (1,2 KB)
**Fase:** F5.2d. **Conteúdo:** tabela família/config × wall s42 × ×30, ordenada por custo,
com os caveats (wall cross-stack, máquina real, base de 1 semente).

---

## 4. ANÁLISE DE FIDELIDADE POR CONFIG — fase F5.3

### `f5/relatorios_config/{config}.md` (24 arquivos, 1,6 MB)
**Fase:** F5.3b (19 configs) + F5.3a-v1.1 (5 pilotos re-executados).
**O que é:** **o coração da validação.** Cada relatório (51-100 mil caracteres) tem 9
seções: ficha do mecanismo · **dissecação narrativa de 20-31 aspectos** (cada um com: o
que o artigo prescreve + o que nossa SPEC mudou e por quê + o que foi observado nos dados
+ por que aconteceu + a classe) · % por classe com denominador · comparação canônica com
o paper · veredito de contrato · saúde em escala · score + recomendação · achados classe
(3) · teto de verificabilidade e armadilhas.
**Serve para:** é o insumo direto do julgamento D97 do autor, config a config.

### `f5/scores_f53.csv` (0,8 KB · 24 linhas)
**Fase:** F5.3. **Conteúdo:** `config, score, recomendacao, n_classe3, chars_relatorio`.
**Serve para:** a visão de conjunto (média 9,33; 13 achados classe (3); todos "aceitar").

---

## 5. VERIFICAÇÃO ADVERSARIAL — fase F5.4

### `f5/adversarial/{achado}.md` (13 arquivos, ~150 KB)
**Fase:** F5.4. **O que é:** um veredito por achado classe (3), produzido por um cético
com viés de REFUTAR. Cada um traz: o que tentou para derrubar (4 rotas: decisão, query
independente, leitura de código, controle), por que caiu ou não, o enquadramento
(bug (a) / comportamento legítimo (b) / dado corrompido (c) / instrumentação (d)) com a
bússola D29, o impacto e a ação recomendada com custo.
**Serve para:** garantir que nenhum achado entra no dossiê sem contraditório — 5 dos 13
caíram na refutação.

### `f5/adversarial/padrao_zdt4.md` (16,6 KB) — **o achado mais importante da F5**
**Fase:** F5.4. **O que é:** a investigação do padrão sistêmico. Varreu as 666 células,
achou 34 com assinatura anômala e provou a causa-raiz em 6 passos: `is_run_done` pula a
célula quando o smoke deixou artefato + `AuditLogger` abre o ⑥ em append sem guarda
(`src/audit_log.py:55`). Inclui o mapa completo das células afetadas, a prova de que só
1 célula tem dano científico (`batch/c149/ZDT4`, quimera provada 2.000/2.000 × 0/2.000)
e **10 itens de prescrição com custo (~12h, zero re-execução obrigatória)**.
**Serve para:** é a base da F5.7 e o que impede o padrão de se multiplicar por 30.

---

## 6. COMPARATIVOS TRANSVERSAIS — fase F5.5

### `f5/transversais_f55.md` (8,9 KB) + `f5/transversais_f55_adendo.md` (2,2 KB)
**Fase:** F5.5. **Conteúdo:** (1) a **régua** SA×pisos por dimensão e **por família de
problema** — o adendo mostra que a leitura "a vantagem cresce com D" não se sustenta nos
25 problemas (BBOB 66% · ZDT 62% · MMF 62% · DTLZ 34% · WFG 26%); (2) ranking global;
(3) o **endpoint ⑦ do offline** (as métricas da ① empatam por desenho); (4) sweep de
tiers e LHS×MVNS; (5) batch vs Sobol; (6) as ablações D77 e big.
**Serve para:** os resultados científicos transversais da dissertação.

### `f5/transversal_{regua,offline_camada7,sweep,big_ablacao}.csv` (4 arquivos, 14 KB)
**Fase:** F5.5. **Conteúdo:** os dados por trás de cada seção acima, célula a célula.
**Serve para:** refazer qualquer gráfico ou teste estatístico da fase M13.

---

## 7. CONSOLIDAÇÃO FINAL — fases F5.6 e F5.7

*(preenchido ao fechar as fases)*

---

## 8. BATERIAS — os scripts e a evidência bruta (934 arquivos, 99 MB)

### `f5/baterias/*.py` (9 scripts)
**Fase:** D2 a F5.5. **O que são:** os drivers que a torre executou —
`organizar_666.py` (layout do autor + melhor-fonte do ⑥), `preencher_data.py`,
`gates_f51.py`, `f52a_integridade.py`, `f52b_contrato.py`, `f52c_metricas.py`,
`f52d_tempo.py`, `f52e_sonda.py`, `f55_transversais.py`, `f55b_adendo.py`.
**Serve para:** reproduzir qualquer número das fases mecânicas.

### `f5/baterias/{config}/` (24 pastas)
**Fase:** F5.3. **O que são:** os scripts e CSVs/pickles de evidência que CADA agente
analisador gerou (ex.: `e81_scale_results.csv` com 30 linhas × 57 checks; os pickles de
aspectos do c217).
**Serve para:** auditar qualquer afirmação de qualquer relatório até o dado bruto.

### `f5/baterias/f54/{achado}/` (14 pastas, 25 MB)
**Fase:** F5.4. **O que são:** a evidência dos céticos, incluindo o
`padrao_zdt4/scan_cells.csv` (666 células × 60 campos de assinatura de proveniência),
os testes `teste_3x1.py` / `teste_camadas.py` (prontos para virar gate) e o
`c154_paisagem_reconstruida.csv` (18 MB).
**Serve para:** os testes que a F5.7 recomenda promover a gate automático já estão
escritos aqui.

### `f5/baterias/pilotos/`
**Fase:** F5.3a. **O que são:** os scripts e evidências da primeira leva de pilotos (v1.0),
preservados para rastreabilidade da evolução do protocolo.

---

## 9. RASTRO NO GIT

**19 commits** com prefixo `[F5*]`, do congelamento do framework à consolidação. A
sequência conta a história: `7a731ac` framework → `effc185` protocolo + leituras →
`88b969d` gates → `f3f2eb7` F5.2 → `7a58bcb`/`ca2928e` pilotos v1.0 → `c6a0ada` protocolo
v1.1 → `a6b430c`/`17304de`/`e943c08` fan-out → `fb48f8b` pilotos v1.1 → `ce03939`
transversais → `d42bfb7`/`0bdd235` adversarial.
