# CARTÃO DE EXTRAÇÃO — mineração definitiva de análises experimentais (cap. 5)

Você é um leitor de artigos científicos de otimização multiobjetivo assistida por surrogate (SA-MOO). Sua tarefa: ler UM artigo inteiro (arquivo Markdown convertido do PDF) e extrair, de forma exaustiva e literal, **todas as análises experimentais que o artigo realiza**, mapeando cada uma às fichas de um catálogo de análises candidatas (arquivo `tipologia_64.md`). O produto é UM arquivo JSON, gravado em disco, no formato abaixo. Não escreva prosa fora do JSON; ao terminar, responda no chat com no máximo 5 linhas (id, nº de análises encontradas, nº de fichas distintas mapeadas, nº de análises NOVAS, e qualquer problema de leitura).

## Contexto mínimo (para mapear bem)

A dissertação compara 15 algoritmos SA-MOO (13 online + 2 offline) e 4 pisos evolutivos sem surrogate (NSGA-II, MOEA/D, NSGA-III, SMS-EMOA) em 28 problemas (ZDT, DTLZ, WFG, MMF, BBOB e 3 reais), 30 sementes, orçamento 31D−1 avaliações reais com DoE inicial compartilhado, métrica primária IGD+ (também HV). A instrumentação grava, por execução, 7 camadas: ① todas as avaliações reais (x, f, ordem); ② população por geração; ③ todas as predições do surrogate (μ/σ, ou classe/score) incluindo uma **sonda** (2.000 pontos fixos re-preditos a cada retreino, com f verdadeiro conhecido); ④ tempos por geração (ajuste do modelo, busca, sonda); ⑤ manifesto (status, params); ⑥ o "filme" das decisões internas (1 evento por linha); ⑦ (só offline) o ND final reavaliado na função verdadeira. **Não serão executados novos experimentos**: só análises pós-hoc sobre esses dados.

## O que extrair (seja exaustivo — inclua análises de apêndice e material suplementar mencionado)

Para CADA análise experimental do artigo (uma "análise" = um estudo/figura/tabela que responde a uma pergunta: tabela final com teste, curva de convergência, ablação, sensibilidade a parâmetro, estudo de escalabilidade, calibração do modelo, custo, caso real, visualização de fronteira, etc.), registre um item em `analises` com:

- `fichas`: lista de inteiros — as fichas do catálogo (1–64) a que a análise corresponde (pode ser mais de uma; ex.: "tabela IGD média±dp com Wilcoxon rank-sum e símbolos +/=/−" → [1, 3]; "curvas de IGD × avaliações" → [26]; "ablação da variante sem incerteza" → [11, 15]; "sensibilidade ao parâmetro do gate de confiança" → [45] se o parâmetro define o USO da incerteza, senão fichas: [] e `nova` com nome). Se nenhuma ficha cabe, `fichas: []` e `nova: true`.
- `nova`: true/false. Se true, `nome_sugerido` (curto) e `grupo_sugerido` (A–J da tipologia).
- `descricao`: o que o artigo faz nessa análise (2–4 frases, específico: métricas, o que varia, o que compara).
- `literal`: uma citação curta e exata do artigo (≤ 40 palavras) que prove a existência da análise (em inglês, como está no texto).
- `localizador`: seção/figura/tabela/página (ex.: "Sec. V-B, Table III", "Fig. 6", "Appendix C").
- `metricas`: lista (HV, IGD, IGD+, GD, spacing, ε-indicator, RMSE do modelo, cobertura de intervalo, tempo, etc.).
- `testes`: lista (Wilcoxon rank-sum, Friedman, Bayesian signed-rank, nenhum, etc.) e o α, se houver.
- `convencoes`: como os números são apresentados (média±dp; mediana; melhor em negrito; símbolos +/=/−; nº de execuções; execução mediana para figuras; escala log; etc.).
- `achado`: o que a análise revelou no artigo (1–2 frases; se for resultado NEGATIVO ou surpreendente para o uso da incerteza, diga explicitamente).
- `aplicabilidade`: como reproduzir com as 7 camadas da dissertação ("① endpoint", "③ sonda", "⑥ filme", …) ou "não reproduzível — motivo" (ex.: exige rodar variante do algoritmo; exige ruído injetado; exige lote q>1).

Além de `analises`, preencha:

- `setup`: {`benchmarks` (suítes e problemas, M e D), `orcamento` (avaliações reais; DoE inicial), `execucoes` (nº de runs independentes), `baselines` (algoritmos comparados; diga se há piso sem surrogate), `metricas_principais`, `testes`, `apresentacao` (convenções gerais), `codigo_plataforma` (PlatEMO, BoTorch, MATLAB, próprio…)}.
- `calibracao_do_sigma`: o artigo mede a QUALIDADE da incerteza que usa (calibração, cobertura, σ vs erro, acurácia do classificador)? {`mede`: true/false, `como`: descrição, `literal`, `localizador`}.
- `custo`: como reporta custo computacional {`reporta`: true/false, `o_que` (tempo total; por iteração; tempo de ajuste do modelo separado?; complexidade), `literal`, `localizador`}.
- `resultados_negativos`: lista de {`descricao`, `literal`, `localizador`} — qualquer passagem em que o uso da incerteza/surrogate NÃO ajudou, atrapalhou, divergiu, ou em que o artigo se defende do σ (ex.: "the uncertainty term may mislead…"). Inclua caveats dos autores sobre calibração ("poorly calibrated…").
- `equivalencia_criterios`: lista de {`descricao`, `literal`, `localizador`} — passagens em que critérios/aquisições diferentes rendem desempenho parecido, ou em que o artigo diz que o modelo (não o critério) é o limitante ("imperfect model", "mostly equivalent").
- `caracteristica_x_desempenho`: lista de {`caracteristica` (multimodalidade, não separabilidade, frente desconexa, frente côncava/degenerada, densidade enviesada, alta dimensão, muitos objetivos, ruído…), `afirmacao` (o que o artigo diz que o método faz/deixa de fazer nessa característica), `literal`, `localizador`}.
- `roster_bloco` (SÓ quando o cabeçalho do pedido disser que o artigo é do ROSTER; senão `null`): {`mecanismo_proprio`: análises que diagnosticam o mecanismo de incerteza do próprio algoritmo (ablação do componente; sensibilidade do parâmetro do mecanismo; contagem de acionamentos; acurácia do classificador; σ do modelo ao longo da busca) com literal+localizador; `reprodutivel_com_camadas`: para cada uma, qual camada permitiria reproduzir na dissertação; `parametros_do_uso_da_incerteza`: nomes e valores dos hiperparâmetros que definem o uso da incerteza (ex.: δ do gate, β do UCB, nº de passagens do dropout)}.
- `observacoes`: qualquer coisa importante que não coube acima (ex.: o artigo compara variantes do próprio método = ablação natural; usa "execução mediana" para figuras; relata falhas do modelo; etc.).

## Regras

1. **Literal + localizador em tudo** (Lei 1 do projeto): nada sem citação exata. Se não achar a citação, escreva `literal: "NÃO LOCALIZADO"` e explique em `observacoes`.
2. **Exaustivo**: é melhor listar 15 análises pequenas do que 5 grandes. Uma tabela com 3 métricas é 1 análise (com 3 métricas), mas uma seção que faz tabela final + ablação + sensibilidade + curvas são 4 análises.
3. **Não invente**: se o artigo não faz a análise, não a liste. Se o artigo só a MENCIONA (material suplementar), liste com `observacoes: "só mencionada"`.
4. Números do artigo podem ser citados dentro de `achado` e `literal`, sem arredondar.
5. Mapeie com generosidade mas com critério: `fichas` deve conter as fichas cujo conteúdo o artigo de fato exemplifica (o campo "o que analisa" da tipologia). Em dúvida entre duas, inclua as duas.
6. Escreva o JSON em UTF-8, válido (use `json.dump` via Python se preferir), no caminho indicado no pedido. Antes de terminar, valide que o arquivo é JSON válido.

## Esqueleto do JSON

```json
{
  "id": "…", "sigla": "…", "titulo": "…", "ano": 0, "roster": false,
  "setup": {"benchmarks": "…", "orcamento": "…", "execucoes": "…", "baselines": "…", "metricas_principais": ["…"], "testes": ["…"], "apresentacao": "…", "codigo_plataforma": "…"},
  "analises": [
    {"fichas": [1, 3], "nova": false, "nome_sugerido": "", "grupo_sugerido": "", "descricao": "…", "literal": "…", "localizador": "…", "metricas": ["…"], "testes": ["…"], "convencoes": "…", "achado": "…", "aplicabilidade": "…"}
  ],
  "calibracao_do_sigma": {"mede": false, "como": "", "literal": "", "localizador": ""},
  "custo": {"reporta": false, "o_que": "", "literal": "", "localizador": ""},
  "resultados_negativos": [],
  "equivalencia_criterios": [],
  "caracteristica_x_desempenho": [],
  "roster_bloco": null,
  "observacoes": ""
}
```
