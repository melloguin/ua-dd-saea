# PLANO DE IMPLEMENTAÇÃO — do zero até "tudo rodando" (versão didática)

> **Para quem é este documento.** Para o autor (Guilherme) — explica, em linguagem de estudante iniciante, **todo** o caminho de implementação, teste e validação da SPEC v5.2 no repo `ua-dd-saea`, organizado em **15 grandes milestones**. A versão técnica (para a orquestração) é `ORQUESTRACAO_MESTRE.md`. Data: 2026-07-15.

---

## Antes dos milestones: como este projeto funciona (o modelo mental)

Imagine que você vai montar uma **linha de produção** que testa 16 "motores" (os algoritmos) em 25 "pistas" (os problemas), repetindo cada teste 30 vezes (as sementes) para ter estatística. São **16.500 corridas** no total. Ninguém constrói isso de uma vez. A gente trabalha em **4 modos**, nesta ordem:

1. **Construir a bancada** (a base compartilhada onde todo motor pluga). — *Fase 0.*
2. **Plugar e provar cada motor, um a um** — numa corrida-piloto de 1–2 sementes só para ver se funciona e se está fiel ao artigo original. Rápido, interativo. — *Rodadas 1, 2, 3.*
3. **Soltar a bateria completa** — as 30 sementes × 25 problemas rodando sozinhas por semanas. Só fazemos isso **depois** de um teste de tempo/memória que garante que os computadores aguentam. — *as baterias.*
4. **Analisar** os dados que saíram. — *Rodada 4.*

Três conceitos que se repetem o tempo todo:

- **Cartão (`card`) = 1 sessão.** Cada pedaço de trabalho é um cartão; cada cartão é uma sessão nova de Claude Code, com contexto limpo. Isso mantém a qualidade alta.
- **Portão (`gate`) = o critério objetivo de "pronto".** Um script (`accept.py`) confere o **encanamento** (as contas fecham: orçamento exato, arquivos gerados, pontos iniciais idênticos). Verde = pode seguir.
- **Fidelidade = seu julgamento, sempre.** O computador nunca decide se um algoritmo "está fiel ao artigo". Isso é **você** que olha, compara com o paper e aprova. (É a regra D97.)

**Dois ambientes, e por quê:** o **Mac** roda o MATLAB (a Rodada 1) porque o MATLAB só está instalado lá; a **VM na nuvem** roda o Python pesado (Rodadas 2 e 3) e guarda os dados no bucket. "Tudo rodando na VM e no Mac" acontece lá pelo **Milestone 8** — quando as duas baterias disparam ao mesmo tempo.

> **Onde estamos:** o **Milestone 0 (Preparação e pré-voo) está CONCLUÍDO e verificado.** A SPEC v5.2 está pronta, a infra (Mac + VM + bucket) está montada, e as "coordenadas de GPS" dos patches (âncoras) foram validadas. Você está entrando no **Milestone 1**.

---

## Os 15 milestones

### 🟩 M0 — Preparação & pré-voo — ✅ CONCLUÍDO
A SPEC v5.2 (as 14 decisões D87–D100), os artefatos, a infra dos dois ambientes e a validação das âncoras. Já feito e verificado. É a linha de partida.

---

### M1 — A bancada compartilhada (Fase 0) · *no Mac*
**O que é:** construir a base que todos os 16 algoritmos usam. São **4 sessões** (cartões):
- `F0-01-harness` — os despachantes, a esteira que roda/retoma sem duplicar, e o registro de auditoria (manifesto + log).
- `F0-02-doe` — o gerador dos **pontos iniciais** (o mesmo "chute inicial" para cada problema+semente) + o dataset dos algoritmos offline.
- `F0-03-export` — o **contador de orçamento** (para exatamente em 31D−1; ponto repetido custa 0) e o **exportador** que grava tudo em Parquet (3 camadas de dados).
- `F0-04-metrica` — o esqueleto que mede a qualidade dos resultados (IGD, HV, etc.).

**Como sabemos que terminou:** os pontos iniciais saem **bit a bit idênticos** no Python e no MATLAB (prova "CP-init"), e o teste-relâmpago da métrica dá o número-âncora **HV = 1,0433**. Aqui você **ainda não julga fidelidade** (não há algoritmo).

---

### M2 — O caso-modelo: primeiro algoritmo de ponta a ponta (c217) · *no Mac* 🔑
**O que é:** o milestone **mais importante de todos**. Duas sessões:
- `R1-00-harness` — a "cola" transversal do MATLAB (como o MATLAB conversa com os problemas em Python, o contrato de entrada/saída).
- `R1-c217` — integrar o **PC-SAEA**, o algoritmo escolhido como **modelo**. Rodamos ele de verdade num piloto pequeno.

**Por que importa tanto:** quando o c217 roda inteiro — usa a bancada, avalia problemas, gasta o orçamento certo, exporta os dados e a métrica sai coerente — a gente **provou a linha de produção inteira** com um caso real. Depois disso, plugar os outros algoritmos é repetição do mesmo padrão.

**Como sabemos que terminou:** portão verde (`accept.py`) **+ a sua primeira validação de fidelidade** — você abre os dados, compara com o artigo do PC-SAEA e aprova.

---

### M3 — Todos os outros algoritmos MATLAB (fan-out da Rodada 1) · *no Mac*
**O que é:** com o padrão provado, integramos os **8 algoritmos MATLAB restantes + os pisos**, um cartão por sessão: `b1` (ParEGO), `b3` (K-RVEA), `b4` (CSEA), `e7` (EDN-ARMOEA), `c141` (MMRAEA), `e74` (CLMEA), `c238` (EIM), `e103` (IBEA-MS, offline) e os `pisos` (NSGA-II/III, MOEA/D, SMS-EMOA). Alguns têm particularidades (o `e74` roda numa árvore própria do PlatEMO 4.1; o `e103` tem um ajuste de centros; o `b1` tem um patch que **precisa** ser aplicado só no arquivo certo).

**Como sabemos que terminou:** cada algoritmo com portão verde + sua validação de fidelidade no piloto. Ao fim, **toda a Rodada 1 está pronta para a bateria**.

---

### M4 — A Rodada 2 no BoTorch (na nuvem) · *na VM*
**O que é:** montar a "cola" do BoTorch (`R2-00-harness`, que já grava os dados direto no bucket) e integrar **`c262`** (qNEHVI) e **`c154`** (JES). São algoritmos de otimização bayesiana modernos, em Python/PyTorch.

**Como sabemos que terminou:** os dois com portão verde + sua validação. Esta rodada roda **em paralelo** com a Rodada 1 — enquanto uma bateria roda sozinha, você implementa a outra.

---

### M5 — A Rodada 3 começa: os standalone mais tranquilos (c122, b5, c311) · *na VM*
**O que é:** os algoritmos "avulsos" em Python, cada um no seu **ambiente isolado** (venv) porque têm dependências que brigam entre si. Montamos a cola (`R3-00-harness`) e integramos `c122` (θ-DEA-DP), `b5` (Prob-RVEA/MOEA-D, offline, roda em 2 configs) e `c311` (TGPR-MO, offline). **Aqui acontece o "gate R3.2"**: o momento de fixar (cravar) a versão exata da biblioteca `desdeo-emo` que ficou pendente de propósito no pré-voo.

**Como sabemos que terminou:** os três verdes + validação; o pino do `desdeo-emo` cravado.

---

### M6 — A Rodada 3 fecha: os mais difíceis (c149, e81, piso offline) · *na VM*
**O que é:** as reconstruções mais delicadas: `c149` (LBN-MOBO, onde reconstruímos o laço de aquisição HVI-greedy) e `e81` (qPOTS, no seu próprio ambiente BoTorch antigo), mais o **piso offline** (MOEA/D-média). São os que exigem mais cuidado de fidelidade.

**Como sabemos que terminou:** os três verdes + validação. Ao fim, **os 16 algoritmos estão implementados e provados em piloto**.

---

### M7 — Teste de tempo e memória + dimensionar as máquinas (PORTÃO BLOQUEANTE) · *Mac + VM*
**O que é:** antes de gastar semanas de computação, rodamos **1–2 sementes dos algoritmos mais pesados** (os "curingas": c149, JES, o de custo cúbico c311) e medimos **quanto tempo levam e quanta RAM consomem**. Com esses números, decidimos o tamanho e a quantidade de VMs, se usamos máquinas spot (baratas), e a regra de limpeza do bucket.

**Por que é um portão bloqueante:** se algo estourar memória ou tempo, a gente **conserta a estratégia agora** (já existe um plano de escalonamento pronto) — nunca no meio de 16.500 corridas. **Este é o pré-requisito para soltar as baterias.**

---

### M8 — Bateria principal ONLINE (12.750 corridas) — "TUDO RODANDO" 🚀 · *Mac + VM*
**O que é:** disparar a bateria grande dos algoritmos online: **17 configurações × 25 problemas × 30 sementes**. A Rodada 1 roda no Mac, as Rodadas 2 e 3 na VM, **ao mesmo tempo**, de forma autônoma, por semanas. Este é o momento que você descreveu como "tudo rodando na VM e no Mac".

**Como sabemos que vai bem:** a esteira retoma sozinha se cair, grava no bucket, e o manifesto marca qualquer corrida que falhe (nunca falha silenciosa). Você monitora e faz backups.

---

### M9 — Bateria principal OFFLINE (3.750 corridas) · *VM (+ Mac p/ e103)*
**O que é:** a bateria dos algoritmos offline (que treinam num dataset fixo, sem pedir novas avaliações no meio): **5 configurações × 25 × 30**. Roda em paralelo/na sequência da online.

**Como sabemos que terminou:** todas as corridas online + offline completas e íntegras. Com M8+M9, **a bateria principal (16.500) está no disco/bucket**.

---

### M10 — Sub-estudo: lote grande q=10 · *VM*
**O que é:** um recorte que testa os algoritmos pedindo **10 candidatos por vez** em vez de 1 (mostra como eles escalam em paralelo). ~750 corridas.

---

### M11 — Sub-estudos: varredura offline + varredura N dos pisos · *VM*
**O que é:** dois recortes finais: o **sweep offline** (varia o tamanho e a distribuição do dataset — ~2.700 corridas) e a **varredura N** (varia o orçamento dos pisos de referência). Fecham a coleta de dados.

---

### M12 — Consolidação e integridade dos dados · *VM*
**O que é:** com tudo rodado, conferimos que **nenhuma corrida faltou** (cada `run_id` presente, cada manifesto OK), juntamos os dados do bucket, e você faz o backup final. É a "auditoria de estoque" antes de analisar.

**Como sabemos que terminou:** contagem bate (16.500 + sub-estudos), zero corridas `failed` sem explicação.

---

### M13 — Análise, parte 1: características + métricas (Rodada 4) · *VM*
**O que é:** a camada de análise começa. Primeiro você **re-deriva a matriz de características** dos 25 problemas (a decisão D98 — é propriedade objetiva, você congela antes de analisar). Depois calculamos as métricas de qualidade sobre todos os dados (IGD+ é a métrica principal).

---

### M14 — Análise, parte 2: testes estatísticos + IGDX · *VM*
**O que é:** os testes estatísticos que comparam os algoritmos (com correção de múltiplas comparações — Holm), e a métrica **IGDX** nos 4 problemas multimodais. Aqui **você refina/implementa** — é a parte da dissertação que é sua autoria analítica (decisão D100).

---

### M15 — Resultados prontos para a dissertação · *VM + escrita*
**O que é:** transformar os números em **tabelas e figuras**, integrar com o texto do survey, e fechar o capítulo experimental. A linha de chegada.

---

## Resumo visual do caminho

```
M0 ✅ Preparação  →  M1 Bancada  →  M2 c217 (PROVA A LINHA) 🔑
                                          │
              ┌───────────────────────────┼───────────────────────────┐
        M3 R1 (MATLAB, Mac)        M4 R2 (BoTorch, VM)         M5–M6 R3 (standalone, VM)
              └───────────────────────────┼───────────────────────────┘
                                          ▼
                               M7 Teste tempo/memória (PORTÃO) 
                                          ▼
                        M8 Bateria ONLINE 🚀 + M9 Bateria OFFLINE   ← "TUDO RODANDO"
                                          ▼
                     M10 lote q=10 · M11 sweep + varredura N
                                          ▼
                          M12 Consolidação/integridade
                                          ▼
                     M13 características+métricas · M14 estatística · M15 dissertação
```

## O ritmo de trabalho (toda sessão, sempre igual)
1. **Eu** monto o prompt do cartão + salvo o contexto no repo.
2. **Você** abre uma instância nova, cola o prompt, ela roda até o fim.
3. Ela fecha o portão objetivo (`accept.py` verde) e escreve `handoff/{cartão}.md`.
4. **Você** faz a validação de fidelidade no piloto (quando há algoritmo) e me traz o handoff.
5. **Eu** verifico, atualizo o plano, e te dou o próximo prompt.

Seu trabalho pesado começa mesmo no **M7/M8**, quando as baterias rodam nos seus recursos. Até lá é implementar + provar, cartão a cartão.
