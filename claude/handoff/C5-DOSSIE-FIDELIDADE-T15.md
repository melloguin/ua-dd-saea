# DOSSIÊ C5 — FIDELIDADE DOS 3 PROBLEMAS DE DADOS REAIS (para o veredito D97 do autor)

> **O que este documento é:** todo o material de que você precisa para julgar a
> fidelidade da integração T15 (RE21 · DDMOP7 · ESTOQUE40) e liberar a tag.
> A torre MEDIU e ORGANIZOU; **o veredito é seu** (D97: fidelidade é
> demonstrada ao autor, nunca decidida pela máquina). Tempo estimado de
> leitura+conferência: 20–40 min. Cada seção fecha com "COMO CONFERIR VOCÊ
> MESMO" — comandos prontos.

---

## §0 · O veredito pedido

Aprovar (ou reprovar) que: **(i)** os 3 problemas avaliam as funções CERTAS
(fidelidade às fontes); **(ii)** o harness os trata com o MESMO rigor dos 25
(orçamento exato, DoE bit-a-bit, camadas, gates); **(iii)** as exceções do
DDMOP7 são as DECIDIDAS por você (sem sonda, sem front, régua em 2 fases,
⑦ pós-hoc) e nada além. Com o seu "aprovo", destrava-se: tag `t15-problemas-reais`
→ push → provisionamento vm1+vm5 → Processo A → disparo das 1.890.

## §1 · RE21 (treliça de 4 barras, M=2 D=4) — o caso limpo

**Fidelidade à fonte:** a classe foi bit-verificada contra o `reproblem.py`
OFICIAL da suíte RE (diferença = 0,0 exato em toda a caixa; validação do
pacote de fusão) e o front D72 empírico concorda com o front oficial publicado
a IGD⁺ = 4,82e-4 / 1,28e-4 (as duas direções). O front oficial segue no repo
como cross-check citável (`data/real_sources/RE21_reference_front.npy`).

**Âncora de valor viva na suíte:** no canto exato x=(1,√2,√2,1):
f₁ = 1237,8414230005442 (9 casas conferidas) e f₂ = 0,04 exato
(`tests/test_t15_catalogo.py::test_ancora_de_valor_canto_ideal_f1`).

**Célula real + portões:** `main/c154/RE21/s0` (surrogate JES completo, 548 s)
→ **PORTÃO VERDE: 8 gates, 0 vermelhos** (G-1..G-7 + accept + auditar).
Pisos nsga2: ok, 0 vermelhos (G-1 não-aplicável é estrutural de piso — igual
ao corpus s42).

**COMO CONFERIR:**
```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea && /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python scripts/portao.py --exp main --alg c154 --problema RE21 --semente 0
```

## §2 · ESTOQUE40 (reposição de estoque, M=3 D=40) — o dado congelado

**Fidelidade à fonte:** o `.npz` congelado (sha256 `660b5896…`, derivado do
UCI Online Retail II com sha do bruto conferido) está VERSIONADO em
`data/estoque_problem.npz`; a classe carrega e o teste confere a forma
(40 produtos × 106 semanas) e DUAS âncoras de valor contra os exemplos
VERIFICADOS POR PORTÕES do pacote (gerador com escrita diferida, provado por
sabotagem): x=0 ⇒ f=[0,0,0] e x=xu ⇒ f=[−17909,135472; 7492,938906;
3,19911603] (`tests/test_t15_catalogo.py::test_ancora_x_igual_xu`).

**Células reais:** piso nsga2 ok com portão 0 vermelhos. Surrogate c122 rodou
**3h33 LIMPO em D=40** e foi encerrado pela torre por decisão de fluxo (o
ponto do piloto já estava provado: D=40 excede horas ⇒ classe
teto/truncamento-com-dado na campanha, como a sua DI-44 prevê; célula parcial
quarentenada em `data/_quarentena_smokes/`, fora de análise). As células
surrogate OFICIAIS dele nascem nas VMs.

**COMO CONFERIR:**
```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea && /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python scripts/portao.py --exp main --alg nsga2 --problema ESTOQUE40 --semente 0
```

## §3 · DDMOP7 (rede neural/crédito, M=2 D=17) — a caixa-preta domada

**A cadeia de fidelidade, elo a elo (tudo MEDIDO em 13-14/08):**
1. **Sorteios congelados**: 120 sorteios de `DDMOP7('init')` congelados 1× —
   PF-1 estocástico (max|Δ|=1,89), esparsidade 0,494, validação independente
   da torre no CSV (22.320×17, sorteios mutuamente distintos, bounds [−1,1]).
2. **Derivação**: DoE 30×186 (sha `9fc4268d…`) + dataset 30×526 (sha
   `03056b6e…`), disjunção ponto-a-ponto provada, ida-e-volta bit-a-bit,
   zeros NEGATIVOS preservados no parquet (bit patterns idênticos).
3. **O contrato do `.p`, medido**: exige `init` 1×/processo (a frio morre);
   o init NÃO consome o contador de 600; lote pós-init ≡ chamadas individuais
   ponto-a-ponto; ~6,3 s/avaliação (Mac E VMs).
4. **Âncoras de valor no `.p` REAL**: x=zeros com x₃=0,5/x₇=−0,2 ⇒
   f = [4/17, 307/690] a ≤1e-12; quantizações f₁·17 ∈ ℤ e f₂·690 ∈ ℤ
   (`tests/test_t15_ddmop7_matlab.py`, 22/22 com o `.p`).
5. **B-27 (ponte/orçamento)**: 526/526 com hard-stop EXATO, 526 soluções
   únicas, dedup bit-a-bit, cache-hit = 0 FE.
6. **Células reais nas DUAS rotas, com PORTÃO VERDE (8 gates, 0 vermelhos)**:
   - **R1** `main/nsga2/DDMOP7/s0` (MATLAB → `.p` direto): fe_final 526/526,
     3.290 s, ⑤ completo;
   - **R2** `main/c149/DDMOP7/s0` (Python → ponte Engine sob o FEBudget):
     ok em 8.063 s.
7. **As exceções são EXATAMENTE as suas decisões**: sem sonda (D102.10 —
   opt-out provado em produção), sem front D72 (D102.4 — para-raios de 21,76
   dias-core testado), régua fase-1 = opção A com **errata medida** (nadir
   f₂ = 468/690 = 0,6783; os docs citavam 0,44493 de memória — venceu a
   fonte; selo de fase 2 obrigatória vivo em `REGUAS_PROVISORIAS`), ⑦ offline
   pós-hoc (Processo B/D102.9 no trilho do e103, paridade provada).

**COMO CONFERIR:**
```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea && /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python scripts/portao.py --exp main --alg nsga2 --problema DDMOP7 --semente 0
```
```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea && UA_DD_SAEA_DDMOP_DIR=/Users/gmello/Documents/python_repos/mestrado2/_real_experiments/DDMOP/DDMOP_Exp/Problems /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python -m unittest tests.test_t15_ddmop7_matlab -v
```

## §4 · O bônus da leva: o fix do c238 (sua DEC-8)

Aplicado com o rito completo do precedente e74: 3 tokens `,[],1` no
`Infill_EIM.m` vendorizado + 3 âncoras novas (bússola D29: bug do original →
segue o artigo) + re-lacre da árvore + teste com kriging REAL provando
(i) o comportamento novo, (ii) o bug antigo preservado como evidência
executável, e (iii) **identidade bit-exata para front ≥2 — as 617 células OK
não mudam; só as 28 falhadas re-rodam** (já no briefing da dupla vm1+vm5).

## §5 · Honestidades (o que este dossiê NÃO cobre — leia antes de aprovar)

1. **O f das células DDMOP7 do Mac é arm64** — elas são PROVA DE ENCANAMENTO,
   não células de análise (a sua D102.14: o f-que-vira-dado nasce só nos
   Linux x86-64; as células do Mac ficam locais, nunca espelhadas).
2. **O offline real do DDMOP7 ainda não rodou** (depende do Processo A nas
   VMs, ~27,5 h-core). O que está provado: o mecanismo (mock determinístico +
   paridade e103 ponta-a-ponta + o motor real da ponte com âncoras). A
   primeira célula offline real nas VMs deve passar por portão antes da
   análise.
3. **c122/ESTOQUE40 não terminou** (decisão de fluxo da torre, §2). Zero
   impacto de fidelidade; impacto de cobertura declarado.
4. **A régua fase-1 do DDMOP7 é PROVISÓRIA por desenho** — a fase 2 (pooled
   pós-runs) a substitui e re-roda a §12; o selo impede esquecer.
5. Suíte final da leva: ver a última linha do REGISTRO A49 (número exato
   preenchido no fechamento) — 0 falhas é condição da tag.

## §6 · Se o veredito for APROVO

Diga "aprovo o C5" e eu te devolvo os comandos finais do D2 (tag+push) com o
estado exato do repo. Se houver QUALQUER ponto que você queira ver mais fundo
antes (uma célula, um manifest, um teste), me pede que eu abro.

---

## §7 · ADENDO — janela exaustiva de 14/08 (o que mudou desde a §5)

Você pediu: fechar os gaps 2 e 3 antes da tag + "seja exaustivo". Resultado:

**Gap 3 (offline DDMOP7 real) — FECHADO.** O dataset s0 nasceu do `.p` REAL
neste Mac (526/526; `check_one` de hash VERDE) e a célula b5r/DDMOP7/s0
offline rodou completa no exp canônico `off`: 526/526 exato, ⑦ pós-hoc com
Engine real (47 finais, 2 ND pós-real), `final_eval --check` VERDE, PORTÃO
com **0 vermelhos** (o ⚪ do G-1 é o estrutural sem-sonda do DDMOP7). De
quebra, a mecânica nova inteira provou-se em produção: `is_run_done` aceitou
a célula sem ⑦ SÓ pela declaração do ⑤ (fix nº 7), e o footer veio
NULL-declarado, sem zero fingido. A observação da §5.2 continua válida num
ponto: o f deste Mac é arm64 — a célula foi para a QUARENTENA e as VMs
regeneram tudo (D102.14); o que se aprova aqui é o ENCANAMENTO, agora provado
de ponta a ponta com Engine real também no offline.

**e103/RE21/s0 offline — PORTÃO VERDE 9/9** (MATLAB -batch pela receita do
driver; ⑦ 100 finais/100 ND; G-1 de sonda VERDE).

**Gap 2 (ESTOQUE40 surrogate completo)**: e81/ESTOQUE40/s0 em voo há ~4 h
(pinado, saudável). Portão na aterrissagem; este adendo ganha o veredito dele.

**Validações extra da janela** (detalhe: REGISTRO PARTE A50): bateria pegou 3
gates com literais velhos que teriam REPROVADO células legítimas da campanha
(BL-04 `tempo_aval_real_s`; alg_id 22→24; selo DDMOP7) — corrigidos; revisão
adversarial 39→20 achados confirmados, todos os de runtime corrigidos e
testados (13/13); 244 artefatos RE21/ESTOQUE40 versionados; receita da VM
ganhou a BATELADA DDMOP7 obrigatória; e um bug NOVO medido em produção — o
macOS congela MATLAB de Engine em processos de fundo — virou watchdog de
partida (300 s) que protege também as VMs. 11 células-smoke Mac dos 3
problemas: todas em `data/_quarentena_smokes/`.

**Pendente no fechamento deste adendo**: e81 aterrissar (portão+quarentena) e
a suíte final da leva T15.10 em janela limpa (0 falhas é condição da tag,
como na §5.5). Fora isso, nada mudou no §6: seu fluxo continua "aprovo o C5"
→ eu devolvo os comandos D2 com o estado exato do repo.
