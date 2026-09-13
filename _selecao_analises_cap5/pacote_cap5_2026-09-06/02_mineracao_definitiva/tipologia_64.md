# Tipologia das 64 fichas do catálogo (para mapeamento da mineração)

Formato: `N. nome — o que analisa (resumo)`. Uma análise de artigo pode mapear para VÁRIAS fichas; se não couber em nenhuma, marque como NOVA.


## A · O placar

1. Matrizes de mediana do IGD+ e do HV, algoritmo × problema — O desempenho final de cada configuração em cada problema: a mediana, sobre as sementes, da métrica de endpoint (IGD+ e HV) calculada sobre o conjunto não-dominado de todas as avaliações verdadeiras da célula. É o "quem entrega o quê, onde" — o substrato factua
2. Ranking agregado por rank médio — A posição média de cada configuração quando os algoritmos são ordenados dentro de cada problema pela mediana do IGD+ (ou HV).
3. "Quem empata com o melhor" — teste de postos vs. o melhor de cada problema (+/=/−) — Por problema, se cada algoritmo é estatisticamente distinguível do melhor algoritmo daquele problema (o de menor mediana de IGD+), com base nas 30 sementes.
4. Friedman + Nemenyi + diagrama de diferença crítica (Demšar) — A comparação global dos k algoritmos sobre N problemas, colapsada num ranking com grupos estatisticamente indistinguíveis.
5. Comparação pareada por semente vs. o melhor, com Holm e região de equivalência — A mesma pergunta da ficha 3, mas explorando o desenho pareado: como todas as configurações partem do mesmo DoE por semente, a diferença entre dois algoritmos pode ser medida semente a semente, o que remove a variância do sorteio inicial.
6. Blocos de problemas — a taxa de comparações favoráveis ao surrogate por família de problema — A fração de comparações assistido-vs-piso favoráveis ao assistido dentro de cada família de problema (suíte).
7. Tendência com a dimensão D — o resultado negativo — Se a vantagem do assistido sobre o piso cresce, decresce ou é indiferente à dimensão de decisão D.
8. Dispersão entre sementes — o surrogate adiciona variância? — A variabilidade do endpoint entre sementes (IQR ou desvio) para cada célula, comparando assistidos e pisos: o surrogate torna o resultado mais ou menos previsível?

## B · O surrogate compra?

9. Assistido × piso casado — Δ IGD+ pareado por semente e placar por algoritmo — Para cada algoritmo assistido, a diferença de IGD+ em relação ao piso da sua própria classe de motor (NSGA-II, MOEA/D, NSGA-III ou SMS-EMOA), semente a semente, em cada problema.
10. A banda dos pisos — os BO-especiais contra o melhor dos quatro pisos — O mesmo que a ficha 9 para os três algoritmos sem motor evolutivo casável (JES, qPOTS, LBN-MOBO): a diferença por semente para o melhor piso daquela semente.
11. Ablação exata do σ — Prob-MOEA/D × MOEA/D-média, em duas leituras — O efeito isolado de usar a incerteza (σ do GP) na seleção do Prob-MOEA/D, contra a mesma maquinaria selecionando pela média: a única ablação exata da bateria.
12. A ablação do σ nos problemas reais — o primeiro resultado conclusivo, contra — A ficha 11 estendida a RE21 e ESTOQUE40 (o DDMOP7 offline não tem ⑦ — B2 da torre), incluindo a variante Prob-RVEA.
13. O regime offline pela camada ⑦ — as quatro configurações mais o e103 — O desempenho final dos algoritmos offline (b5m, b5r, moead_media, e103) medido no ND final reavaliado na função verdadeira — porque a ① deles é o mesmo dataset compartilhado e empata por desenho.
14. O ganho sobre o dataset — quanto cada offline melhora (ou piora) o que recebeu — A diferença entre a métrica do dataset inicial (o ND do próprio dataset compartilhado, avaliado como conjunto) e a métrica da ⑦ — o que o algoritmo acrescentou ao que recebeu. Versão online análoga: métrica do DoE (11D−1) vs endpoint.
15. O contrafactual σ = 0 online — cravado, nunca executado — (Analisaria) o efeito isolado da incerteza em cada algoritmo online: a mesma configuração com σ forçado a zero na aquisição/seleção.
16. Os pisos como resultado — onde e por que o piso vence o assistido — O subconjunto do placar da ficha 9 em que o piso vence, com a explicação mecânica de cada caso.

## C · Característica × algoritmo

17. Rank médio por característica estressada do problema (a versão-piloto) — Para cada característica de problema, o rank médio de cada algoritmo restrito aos problemas que estressam aquela característica.
18. As escadas de dificuldade — em que degrau cada classe deixa de funcionar — Dentro de cada característica, os problemas ordenados por intensidade (degrau 1 → n); para cada algoritmo (e para cada classe), a curva de desempenho relativo ao longo dos degraus — e o degrau em que ele "deixa de funcionar" (passa a perder do piso, ou cai aba
19. As seis perguntas sobre a incerteza — uma por característica, casando resultado e mecanismo — Cada uma das seis situações como uma mini-análise com duas metades: o resultado (quem vence/perde nos problemas daquela característica — fichas 9, 17, 18) e o mecanismo previsto pela pergunta (a sonda e o filme: fichas 31–38, 45). Por exemplo: em paisagens eng
20. A taxonomia como variável — desempenho agregado por classe de cada eixo — O desempenho (Δ pareado vs piso; rank; taxa de vitórias) agregado pela classe do algoritmo em cada um dos quatro eixos: motor (7 classes), surrogate (4), função da incerteza (6), medição (5) — e cruzado com a característica do problema.
21. As famílias da §3.8 sob teste — o roster cobre 7/7 — O desempenho agregado por família da §3.8 (em vez de por classe de um eixo, como na ficha 20): cada família do survey representada pelos seus algoritmos no roster.
22. O sintético prediz o real? — a transferência do ranking para RE21, ESTOQUE40 e DDMOP7 — Duas coisas distintas: (a) se o ranking agregado muda quando os reais entram (não muda — Spearman 0,990); (b) se a taxa de vitórias do surrogate nos reais é predita pela taxa nos sintéticos (não é — os reais estruturados são mais pró-surrogate do que a média s
23. Os três problemas reais como casos nomeados — Cada problema real como um caso com a sua própria história: o que a formulação exige, como os algoritmos se comportaram, e o que só ali se vê (o quantizado do DDMOP7; o f1 negativo do EST40; a treliça do RE21 como "primeiro degrau da escada de dimensão").
24. DDMOP7 — "que aquisição acha as redes esparsas boas?" — No único problema com objetivos em grade (f1 = k/17, f2 = n/690), quatro medidas que a métrica padrão não dá: |ND| efetivo (após dedup por `x_efetivo`), número de valores distintos de F, melhor f2 alcançado (a ponta), e a fração de coordenadas propostas dentro
25. Métricas no espaço de decisão nos MMF (IGDX / PSP) — Nos quatro problemas multimodais multiobjetivo (MMF), a cobertura dos múltiplos conjuntos de Pareto equivalentes no espaço de decisão — o que o espaço de objetivos esconde por construção (dois pontos distintos de x com o mesmo f).

## D · Quando (trajetórias/orçamento)

26. Trajetórias de convergência — mediana + IQR × fração do orçamento, com a banda dos pisos — A evolução da métrica ao longo do orçamento (IGD+ do ND acumulado das avaliações reais até cada checkpoint), por algoritmo e problema, sobre as sementes.
27. A comparação sob orçamento apertado — o placar recomputado no prefixo — As matrizes, o placar assistido × piso e o ranking (fichas 1, 2, 9) recomputados em cortes do orçamento (por exemplo 25 %, 50 %, 75 %, 100 %).
28. Quem mais melhora na segunda metade — Δ meio → fim — A melhoria relativa da mediana do IGD+ entre a metade e o fim do orçamento, por algoritmo.
29. A lente de prefixo para as células que bateram no teto de parede — O que acontece com as leituras (matrizes, placar, ranking) quando as 615 células do teto entram pela lente de prefixo — no FE comum por problema — em vez de ficarem fora.
30. Monotonicidade das curvas — o teste de sanidade do pipeline — Se as trajetórias (ficha 26) são monotônicas (IGD+ não-crescente; HV não-decrescente) em todas as células — o que é propriedade do ND acumulado e, portanto, um invariante do pipeline.

## E · O modelo por dentro (sonda, fantasia, infill, mecanismo)

31. Sonda, dimensão 1 — a acurácia da média ao longo do orçamento (o modelo aprende? esquece?) — O erro da média predita (RMSE, ou WAPE) nos 2.000 pontos fixos, a cada retreino, em função da fração do orçamento já consumida — a curva de aprendizado do surrogate, comparável entre algoritmos porque os pontos são os mesmos.
32. Sonda, dimensão 2 — a preservação da ordem (μ ordena como f? o classificador acerta a classe?) — Não o valor, mas a ordem: se a ordenação dos 2.000 pontos por μ preserva a ordenação por f (correlação de postos); para os classificadores (b4, c217) e para o preditor de dominância (c122), se a classe/score prevista acerta a classe real (AUC, acurácia, precis
33. Sonda, dimensão 3 — a calibração do σ (a incerteza reportada é confiável?) — Se o σ reportado tem a magnitude certa (cobertura: a fração dos 2.000 pontos cujo f cai em μ ± 2σ, contra 95,4 % nominal) e se ele ordena o erro (ρ entre σ e |μ − f|) — ao longo do orçamento.
34. Sonda, dimensão 4 — a discriminação do σ (a incerteza separa os candidatos de erro grande?) — Distinto da calibração (magnitude certa) e da ordem do erro (ρ): se o σ, usado como detector, separa os pontos em que o modelo erra muito dos pontos em que acerta — a propriedade que uma aquisição exploratória explora (ir onde σ é alto porque lá o erro é alto)
35. A tipologia das curvas da sonda — aprende, plana, degenera — A forma de cada curva da ficha 31 (e das fichas 32–33), classificada em três tipos, por algoritmo × problema: cai (aprende), não cai (plana), sobe/explode (degenera) — e a associação entre o tipo e o resultado (ficha 9).
36. A sonda por classe de medição — a qualidade do σ depende de onde o número vem? — As dimensões 3 e 4 da sonda (fichas 33–34) agregadas pela classe de medição de cada algoritmo: a posterior fechada do GP (VA) é mais calibrada que a dispersão de um ensemble/dropout (DE)? que a saída nativa de um modelo não-GP (VN)?
37. A calibração por objetivo — a "agregação silenciosa de m sigmas" — A calibração e a acurácia por objetivo (não agregadas), e a relação entre a qualidade por objetivo e a regra de agregação que cada algoritmo usa para produzir o número escalar que consome.
38. Heterocedasticidade — o erro do modelo por região do espaço — Se o erro do modelo (e o σ) variam sistematicamente com a região do espaço: proximidade da frente verdadeira, quantil do valor do objetivo, distância ao arquivo de treino, dimensão — em particular nos problemas de densidade não uniforme (ZDT6, DTLZ4, WFG…).
39. A lei do teto relida — quando o modelo é bom o bastante, o teto vem do surrogate, não do critério — A relação entre a qualidade do surrogate (fichas 31–33) e a diferença de desempenho entre critérios de aquisição/seleção que usam esse surrogate: se, quando o RMSE cai abaixo de um nível, os algoritmos com o mesmo tipo de modelo convergem para o mesmo desempen
40. O erro de fantasia por terço do orçamento — quem acredita demais no próprio modelo — O erro da predição μ nos pontos que o algoritmo ESCOLHEU avaliar (não nos pontos fixos da sonda): RMSE entre o μ que motivou a escolha e o f real obtido, por terço do orçamento.
41. A fantasia geracional completa — a fronteira acreditada vs a real, geração a geração — A cada geração, a fronteira que o algoritmo acredita ter (ND da população pelos μ) contra a fronteira real dos mesmos indivíduos (pelo f da ①): o gap de HV/IGD+ ao longo da busca — "o filme".
42. A fantasia offline — |ND acreditado| vs |ND real| depois da reavaliação (⑦) — No regime offline, a fração do ND final acreditado (pelo modelo, sem nenhuma avaliação real durante a busca) que continua não-dominada depois de reavaliada na função verdadeira — e a métrica de cada um dos dois conjuntos.
43. A utilidade do infill — quanto do orçamento de busca vira fronteira — A fração das avaliações reais da fase de busca (fe_index ≥ 11D−1) que entram no conjunto não-dominado corrente no momento em que são avaliadas — o aproveitamento do orçamento.
44. Exploração × explotação — onde os infills caem — A geometria das escolhas: a distância de cada infill ao ponto já avaliado mais próximo (explotação = perto; exploração = longe), a fração de infills no bordo da caixa, e — no DDMOP7 — a fração de coordenadas propostas dentro da zona morta; ao longo do orçament
45. O mecanismo em ação — contar o que o filme (⑥) registra — As contagens das decisões internas em que a incerteza intervém: quantas vezes o ramo "incerteza" foi escolhido (b3, e7), quantas vezes o gate abriu (c217), a fração de FEs em que o surrogate foi usado (b4), quantos warnings/estagnações (c154), a troca de model
46. A parede do retreino — o tempo de ajuste por geração cresce com D (e com n) — O custo de retreinar o surrogate a cada geração, em função da dimensão do problema (o arquivo cresce com 31D−1) e do número de pontos acumulados — a parede O(n³) do GP contra as alternativas.

## F · Custo

47. Tempo × qualidade — o custo se paga? (quadrantes) — A posição de cada configuração no plano (custo, qualidade): tempo de parede mediano por execução contra o rank médio de IGD+ nos 25 sintéticos.
48. O custo com o tempo de ajuste do modelo — a decomposição fit / busca / sonda / avaliação — Quanto do tempo de cada execução é ajuste do modelo, quanto é busca no modelo (otimização da aquisição), quanto é avaliação verdadeira, e quanto é instrumentação (sonda, a descontar) — por algoritmo, problema e ao longo do orçamento.
49. O ganho descontado do custo — qualidade por hora, e a fronteira custo × qualidade — A ficha 47 transformada em número: (a) o conjunto não-dominado dos algoritmos no plano (tempo, IGD+) — quem está na fronteira custo × qualidade; (b) o custo marginal de cada ponto de rank/IGD+ entre vizinhos da fronteira.
50. FE redundante no DDMOP7 — nota de custo, não análise — A fração de avaliações verdadeiras do DDMOP7 gastas em pontos cujo x efetivo (após zona morta) já havia sido avaliado — custo "redundante" por desenho da codificação.

## G · Pares

51. Pares seminal → estado da arte sob o mesmo DoE — o que a evolução da classe comprou — Para os três pares em que o roster tem o canônico e o estado da arte da mesma linhagem, quanto do progresso publicado sobrevive quando os dois rodam sob o mesmo DoE, orçamento e protocolo.
52. Os pares quase-gêmeos experimentais — mesma maquinaria, incerteza distinta, ambos no roster — Os três pares em que a maquinaria é a mesma e o que muda é a incerteza (função e/ou medição): a diferença de desempenho entre eles é a diferença que a incerteza faz, com a maquinaria controlada — a "lupa da incerteza" (a contribuição da dissertação) em ação ex
53. O eco do quadro de equivalências na abertura da §5.1 — moldura, não análise — Nada por si: é um movimento de prosa na abertura do capítulo — avisar que a álgebra das aquisições (EI, EHVI, UCB, Thompson…) tem parentescos que podem aparecer como desempenhos próximos, e que isso é previsto, não descoberta.

## H · Fronteiras/visual

54. As fronteiras da execução mediana contra a frente verdadeira — Qualitativamente, a cobertura e a distribuição do conjunto não-dominado obtido, contra a frente verdadeira, em problemas de geometria difícil.
55. Superfícies de attainment (worst-case) e coordenadas paralelas — (a) Attainment: para cada problema biobjetivo, a região do espaço de objetivos atingida por todas as 30 execuções (worst-case), pela mediana, ou pela melhor — um resumo distribucional das 30 fronteiras que a execução mediana (ficha 54) não dá; (b) coordenadas 
56. Regra editorial das figuras — amostra no texto, o resto no repositório — Nada: é regra de exibição, define quantas figuras de cada ficha entram no corpo do capítulo e onde vive o restante.

## I · Contrato honesto (completude, incapacidades, ruído)

57. A completude do corpus — n efetivo por configuração × problema — Quantas células existem, quantas são válidas, por que as demais não são — por configuração × problema — antes de qualquer resultado.
58. A tabela de incapacidades — falha julgada pela referência; a incapacidade é resultado — As células que não produziram resultado por limitação do algoritmo (não da infraestrutura), organizadas por algoritmo × problema × causa, com o veredito "incapacidade documentada" — e o que cada incapacidade diz sobre o algoritmo diante da característica do pr
59. O piso empírico de ruído — em dois níveis — A magnitude da variação da métrica que se deve à máquina/stack (e não ao algoritmo ou à semente): a mesma célula rodada em máquinas diferentes.
60. A sensibilidade do veredito às políticas de cobertura — P1, P2, FE comum — Quanto as leituras principais (matrizes, placar, ranking, CD) mudam quando a política de inclusão de células muda.
61. "O que a bateria não responde" — os limites declarados — A lista do que a bateria, tal como congelada, não pode responder — e por quê.
62. Avisos de régua e clip — notas de normalização — Os pontos que furam a régua (ideal/nadir) por problema e o efeito do clip do HV — uma nota de rodapé por problema afetado.

## J · Secundários

63. O sweep offline de volume de dados — c311 e treed_media em small/medium/big × LHS/MVNS — Como o tamanho (small/medium/big) e a distribuição (LHS × MVNS) do dataset offline afetam o endpoint (pela ⑦) do TGPR-MO (c311), do piso treed_media (só big) e — nos tiers small/medium — dos quatro offline do roster (b5m, b5r, e103, moead_media).
64. O sub-estudo de lote (q = 10) — sobol_batch e as células `batch` — O desempenho a FEs iguais quando q pontos são escolhidos por iteração (qNEHVI/qPOTS em lote) contra q = 1.