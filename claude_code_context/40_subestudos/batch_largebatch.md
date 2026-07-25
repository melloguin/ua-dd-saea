# Sub-estudo LARGE-BATCH (q=10) — Parte V-B [fechado por D66]

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**D66:** q=10; `maxFE_batch = 11D−1 + K·q`, **K=200** (2.000 infills); DoE **pareado com o principal**; roster c149/c262/e81/c154 + **piso Sobol-batch** (scrambled/Owen por semente); **qParEGO FORA**; ~5 problemas × 30 sementes; `run_id` com `exp=batch` (D55). Cada algoritmo usa o modo de lote **NATIVO** — sem fallback livre.

---

## V-B.1 Motivação e origem
A leitura dos papers (Anexo F) mostrou que parte da literatura BO moderna foi desenhada para **lote grande** (q≫1): trocam eficiência amostral por eficiência de *iteração*, assumindo capacidade de avaliação paralela. No regime principal (q=1), o núcleo desses métodos fica desligado — rodá-los *apenas* lá seria avaliar espantalhos. A solução adotada não é dropar o fenômeno, e sim dar a ele um **habitat próprio e bem delimitado**: um sub-estudo com q≫1, onde os mecanismos de lote competem em pé de igualdade. Decisões D11/D12 (Anexo D).

**Distinção conceitual que fundamenta o desenho (registro):** "mais avaliações" tem dois eixos independentes — **orçamento total** (`maxFE`) e **tamanho do lote** (`q`, pontos avaliados por iteração). Aumentar orçamento com q=1 **não** resgata um método large-batch (o lote continua morto); o que o resgata é q≫1. Igualmente, a **cadência u≈5 dos EAs** (Parte IV) não é lote no sentido BO — é model management sequencial.

## V-B.2 Roster [DECIDIDO]
Critério de entrada: **lote como modo nativo do método publicado** (não forçado).

| id | Algoritmo | Papel no sub-estudo | Relação com o principal |
|---|---|---|---|
| c149 | LBN-MOBO | **Batch-only — a razão do sub-estudo** (o lote É a contribuição: aquisição 2MD seleciona um front inteiro; BNN/deep-ensemble) | Roda **nos dois** (D12): no principal q=1 degradado (documentado), aqui no habitat |
| c262 | qNEHVI | Batch-nativo (o "q"; greedy sequencial polinomial em q; paper avalia até q=32) — **âncora GP-BO** | Roda nos dois → contraste sequencial-vs-batch intra-algoritmo |
| e81 | qPOTS | Batch-nativo (lote por maximin sobre amostras de Thompson, "sem custo adicional") | Roda nos dois → idem |
| c154 | JES | Batch-capaz — **[RESOLVIDO v2.1]** qLB-JES batch suportado no BoTorch 0.18.1 (greedy sequencial; submodular, garantia e⁻¹), com caveat documentado de não-monotonicidade do lower bound (B9.4); q=10 extrapola o máximo do paper (q=8) — anotar | Roda nos dois |
| b1* | qParEGO (BoTorch) | **Opcional** — batch por escalarizações Tchebycheff distintas por membro do lote | ⚠ é **variante de implementação** (≠ ParEGO/PlatEMO do principal); se entrar, rotular como **qParEGO** |
| — | **Piso Sobol-batch** | Lote aleatório Sobol de q pontos por iteração | Isola "o surrogate+aquisição compram algo sobre lotear ao acaso?" |

**Fora do sub-estudo:** MORBO (c131) e PDBO (c205) seriam batch-nativos, mas estão **fora dos experimentos por seleção** (D10) — o sub-estudo não os resgata (roster enxuto; o cara-a-cara de mecanismos de lote DPP/multi-TR fica para o survey). Os EAs não entram (cadência ≠ lote). Os offline não se aplicam (sem infill).

## V-B.3 Os dois eixos de análise (o payoff)
1. **Performance batch:** HV/IGD entre os métodos de lote (com pareamento de DoE e sementes) — em particular, o c149 com o mecanismo íntegro vs os GP-BO batch.
2. **⭐ Escalabilidade (o achado-alvo):** tempo de treino/wall-clock vs nº de pontos acumulados — os GP-BO (qNEHVI/qPOTS/JES) sofrem o custo **O(n³)** do GP conforme as avaliações acumulam; o c149 (**BNN — não bate na parede cúbica**) segue com custo ~linear por retreino. É o **espelho online do achado treed-GP do offline** (§11.5) → narrativa unificada da dissertação: *"a parede de escalabilidade do GP aparece nos dois regimes; surrogates não-GP (BNN online, treed-GP offline) a atravessam."* **O lastro quantitativo dessa curva é a série `(n_acumulado, tempo_fit_s)` da §17.6.**

## V-B.4 Parâmetros — [FECHADO por D66 (v5.0): q=10, `maxFE = 11D−1 + 200·q`, roster c149/c262/e81/c154 + Sobol-batch]
| Eixo | Proposta registrada (a bater martelo) | Racional |
|---|---|---|
| **q (lote)** | q = 10 (primário; opcional sweep q=20 se o custo couber) | Ativa os mecanismos de lote sem trivializar; um q só contém o custo. Nota honesta: o habitat nativo do c149 é lote ~10³ — q=10 já ativa o mecanismo (seleção diversa de um front), mas registrar que não é o extremo do paper |
| **Orçamento** | ~2.000–3.000 avaliações reais (init `11D−1` + K·q infills) | Fundo o bastante para o GP sentir o O(n³) e o BNN mostrar que não sente — onde vive o achado de escalabilidade |
| **Problemas** | Os mesmos 5 do sweep offline (MMF16_20, ZDT4, DTLZ2*, WFG9, ZDT1) ⟦DI-35.3⟧ | Cobre D 2–30 e geometrias; **reusar os problemas amarra o achado batch-online ao treed-GP-offline** numa história única. DTLZ2 é 3-obj — sem conflito |
| **Sementes / DoE** | Mesmas 30 sementes; mesmo DoE `11D−1` LHS compartilhado | Fairness herdada de graça (§5.2–5.3) |
| **Regra q=1 do c149 no principal** | A definir na nota de adapter (Anexo E.3): 1 ponto do front 2MD (candidatas: máx. incerteza / joelho / aleatório-do-front) | O paper não define modo q=1 — a regra é nossa, precisa ser declarada e justificada |

**⟦DI-37, autor 2026-07-25 — calibração de CUSTO do batch (fecha o cartão T9; medição, não estimativa)⟧.** (i) **c262 = receita CHEIA, sem knob** (DI-37.2): a L.10 vale inalterada em q=10 (`num_restarts=10, raw_samples=512`; lote pelo greedy sequencial — transcrição manual equivalente ao `sequential` do stock) — custo **medido ~2,2 h/run** (a projeção "~56 h" do T6 era artefato do projetor de wall-clock não-batch-aware, corrigido em DI-36). (ii) **c154 = knob per-D, BATCH-ONLY** (DI-37.3): no q=10 o `optimize_acqf` roda com **`num_restarts=1·D, raw_samples=50·D`** (contra os 5D/1000D do paper, que seguem intactos no q=1 do principal — regressão ①②③④ byte-idêntica provada, `scripts/regressao_q1.py`); fonte única `_restarts_raw_for_q` (`src/c154_jes.py`), valores efetivos no manifesto/`params`. (iii) **Mesmo com o knob, o c154 batch tem PISO ≥30 h** (JES-LB ~n^1,6) ⇒ as 5 células estouram o teto universal de 12 h — e, sob o rito BoTorch de aborto (§5.1: projeção antecipada, SEM parquets), hoje **abortam cedo sem produzir ①–⑦**; a materialização do "truncado como dado" ratificado na DI-37.1 é a **decisão DI-38**. (iv) c149/e81/Sobol-batch: receitas nativas, sem knob (baratos — medição T9).

## V-B.5 Fairness e leitura cruzada com o principal
- **Não comparar rankings entre estudos diretamente** — regimes diferentes (q e orçamento).
- **Contraste c149 principal×batch (D12):** mesmo algoritmo, mesmos problemas → quantifica o valor do lote ("sem o L do LBN, o método perde X% de HV"). Para separar o efeito do *lote* do efeito do *orçamento maior*, usar o truncamento a-FEs-iguais: recortar os runs batch em `fe_index ≤ 31D−1` (§5.1/§17) e comparar com o principal no mesmo nº de FEs — só q variando.
- **Enquadramento na dissertação:** a degradação do c149 no principal é **achado**, nunca "LBN-MOBO é ruim" — mesmo tratamento da ressalva do qNEHVI-sem-ruído (§16).
- **⟦DI-37.4, autor 2026-07-25⟧ Caveat vinculante de análise (entra no lote D97): o contraste q=1 × q=10 do c154 NÃO isola o efeito do lote.** Além do q, mudam (a) a receita do `optimize_acqf` (5D/1000D no principal → 1D/50D no batch, DI-37.3) e (b) o término (batch estoura o teto de 12 h, DI-37.1 — e sob o rito BoTorch atual as células abortam **sem camada ①**, logo a lente de prefixo `fe_index ≤ corte` não tem parquet para ler nesses runs; depende da DI-38). Toda leitura cruzada do c154 entre regimes **declara os DOIS confounders**; o contraste **limpo** de lote fica com **c262/e81** (receitas idênticas nos dois regimes) — e com o c149 na direção inversa (habitat no batch, D12).

## V-B.6 Custo e execução
`~5–6 configs × 5 problemas × 30 sementes × ~2–3k FEs` — contido pelo nº de problemas. Os GP-BO batch são os gargalos de wall-clock, e isso é *dado* (eixo de escalabilidade), não desperdício. Grid entra na mesma esteira resumível (§19); os runs batch gravam o mesmo contrato de export (§17), com `q` no manifesto.

---
---

# PARTE VI — MÉTRICAS E ANÁLISE

> **[v5.2 — D100] Fronteira implementação × análise (princípio, decisão do autor).** O export **salvar-tudo** (D53/D54) **desacopla** o experimento da análise: a camada ① guarda 100% das avaliações reais (X e F), a ② as populações, a ③ os snapshots do surrogate — logo **toda** métrica, teste estatístico e caracterização desta PARTE é computável **a posteriori, dos dados salvos, sem re-rodar nada**. Consequência vinculante: **as decisões desta PARTE não bloqueiam nem alteram a implementação dos experimentos** (Fase 0–R3); o trabalho do pipeline é produzir **dados completos e válidos** — a análise é **refinada e implementada pelo autor depois, na fase R4**. Deferimentos registrados do autor (v5.2): a família/controle da correção de multiplicidade (§14) fica **em aberto, a fechar antes do R4**; backup/redundância — **o autor fará backups manualmente à medida que os resultados saírem** (D64 mantida); consolidação/custo/cronograma — o autor trata depois. *(Única exceção que toca a implementação: o smoke-test da métrica no F0 usa a âncora numérica — resolvida na D92.)*
