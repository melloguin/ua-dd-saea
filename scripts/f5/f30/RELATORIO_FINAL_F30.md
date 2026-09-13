# RELATÓRIO FINAL — validação de fidelidade da campanha de 30 sementes

**Torre de validação de fidelidade · 2026-08-15 · doutrina D97: analiso e recomendo; o veredito é do autor**
**Corpus:** 15.129 células · 22 configs · 25 problemas · 30 sementes ({0–28, 42}) · 66 GB · 7 camadas
**Método:** 25 agentes independentes (21 configs + 4 transversais), 5,68 M tokens, 2h49. Tudo re-medido.

---

## 1. Veredito recomendado

**ACEITAR os 22 configs.** Média **9,21** (T11: 9,48 na semente 42). **Zero bugs de mecanismo** —
pelo terceiro exame consecutivo.

**E o resultado mais forte desta auditoria não é um score: é que o mecanismo é invariante de
semente, e isso agora está medido no censo total, não em amostra.**

| config | query-joia | fração | erro máximo |
|---|---|---|---|
| **b1** | identidade fechada do EI de Jones | **218.168/218.168** | 2,568e-13 |
| **c238** | identidade EIMe (Apêndice A) | 173.413/173.440 | — |
| **c154** | `acqf_escolhido == max` dos finitos | **66.590/66.590** | — |
| **e103** | `KFlag=1 ⟺ …` (A15) | **66.231/66.231** (669/669 células) | — |
| **moead_media** | 35 identidades estruturais | **35/35 em 725/725** | — |
| **nsga2 · nsga3 · e7 · c217 · moead · e81 · e74 · c122 · c141 · c262 · b3 · b4** | as respectivas | **100%** | — |

O b1 sozinho fecha a identidade do EI em **218.168 eventos**, cobrindo 733 células, 25 problemas,
30 sementes, D ∈ {2,7,10,12,20,22,30}, 7 hosts — **e inclui as 32 células que falharam** (a
identidade fecha até no último evento antes do crash). A margem é de **7 ordens de grandeza**
sobre a tolerância.

**Nenhuma semente é exceção em nenhum config.** A hipótese de que a semente 42 fosse um caso
especial está descartada por medição.

---

## 2. 🔬 O RESULTADO CIENTÍFICO — o estudo saiu do sufoco

### 2.1 A conclusividade saltou de 17,7% para 75–80%

Com n=1 semente, só **54 de 305 (17,7%)** das comparações surrogate × piso passavam do piso de
ruído. Com 30 sementes, unidade de aleatorização correta (a semente), Wilcoxon pareado + Holm +
rope 0,05:

| comparador do piso | N | **conclusivas** | pró-SA / pró-piso |
|---|---:|---:|---:|
| C — mín. dos 4 pisos por semente (análogo exato do n=1) | 294 | **234 = 79,6%** | 91 / 143 |
| A — melhor piso pela mediana das 30 | 294 | **221 = 75,2%** | 101 / 120 |
| B — nsga2 pré-fixado | 294 | **204 = 69,4%** | 117 / 87 |

**Fator 4,3×.** E a causa está nomeada: **o piso O-18 era o floor errado.** Ele mede deriva entre
*máquinas*; o que domina é a variância entre *sementes* — **67,3% dos pares têm amplitude entre
sementes maior que o piso O-18 inteiro** (IQR/mediana 22,9%, amplitude/mediana 78,8%, CV 19,6%).
Aplicado às medianas das 30, o O-18 deixaria só 36,1% conclusivas. **Era ele que sufocava o
estudo, não os dados.**

### 2.2 As 5 famílias colapsam em 3 blocos — agora é teste, não descrição

Friedman com config como bloco (12 configs SA): **χ² = 31,53, p = 2,4e-06**. Post-hoc
Wilcoxon+Holm separa 8 dos 10 pares; os que não separam são BBOB~MMF e DTLZ~WFG:

> **{ZDT} ≫ {BBOB, MMF} ≫ {WFG, DTLZ}**

| família | vence na mediana | **conclusivas** (n=1 entre parênteses) |
|---|---:|---:|
| BBOB | 64,8% | **74,7%** (28%) |
| ZDT | 69,4% | **73,5%** (42%) |
| MMF | 56,9% | **47,1%** (**0%**) |
| DTLZ | 27,1% | **81,4%** (14%) |
| WFG | 20,0% | **85,0%** (**2%**) |

O efeito em ZDT é enorme — log₂ razão até **−5,43** no c262 (43× melhor). A taxa de vitória do
n=1 escondia isso porque é adimensional.

### 2.3 "A vantagem do surrogate cresce com D" — segue não sustentada, agora com teste

Spearman de `log₂(IGD+_SA / IGD+_piso)` vs D, por config: **ρ mediano +0,006**; Wilcoxon dos 13 ρ
contra zero: **p = 0,787**; 7/13 positivos. Só o e81 é individualmente significativo (ρ=+0,49,
p=0,012, sem correção).

**E dentro do DTLZ — o único lugar onde D varia com a família fixa em 3 níveis — o sinal é o
CONTRÁRIO: ρ = −0,507, p = 4,2e-05** (o SA melhora com D). O confundimento D×família é **total**
no grid atual: D=7 é só DTLZ1, D=20 é só MMF16_20, D=30 é só ZDT1/ZDT3.

### 2.4 O ranking é estável às sementes e instável ao conjunto de problemas

**Não existe bloco completo 17×25.** Nenhum problema tem os 17 configs do `main` com ≥20 sementes
fora de 8; nenhum config tem os 25 problemas fora de 11. **O quadro de Friedman do §15.1 da SPEC,
"vista única com os 25 problemas e blocos completos", NÃO é executável no corpus atual.**

Bloco A (11 configs × 25 problemas, completo): χ²=84,63, **p=6,2e-14**, CD Nemenyi(0,05)=3,020.
Ordem: `c141 2,92 · b3 3,96 · e74 4,44 · smsemoa 4,80 · nsga2 5,52 · nsga3 6,16 · e7 6,20 ·
b4 7,16 · c217 7,28 · …`

---

## 3. 🔴 A DERIVA É UM DEGRAU DE HARDWARE — e ela é estratificada por classe de config

Este é o achado operacional mais consequente, e ele **corrige a premissa da tarefa**.

**A base de duplicatas não é "~2,6 mil".** Das 11.046 células presentes em ≥2 VMs, a esmagadora
maioria é **sombra de manifesto** (a 2ª VM só tem o `.manifest.json`). Células com camada ① em
≥2 VMs: **762**. Descontando 14 pares que declaram o mesmo `host`: **752 pares cross-máquina reais**.

**709 dos 752 (94,3%) têm deriva EXATAMENTE ZERO** — parquets bit-idênticos.

E os 43 que divergem têm um corte temporal exato:

| regime | pares | divergentes | ΔHV p95 / max |
|---|---:|---:|---|
| **A** vm1×vm5 **antes** de 2026-08-14T10:26:42Z | 515 | **0 (0,0%)** | 0 / **0** |
| **B** vm1×vm5 **depois** do corte | 168 | 43 (25,6%) | **10,60%** / **100%** |
| **C** todos os outros pares de VM | 69 | **0 (0,0%)** | 0 / **0** |

O software é idêntico dos dois lados (MATLAB 25.1.0.2973910, mesmo `repo_hash`). O corte é
**anterior à janela de swap das 15:20Z** — é compatível com a **troca de shape da vm5**.

**E a estratificação por config é o achado dentro do achado:**

- **100% de divergência:** `c141` 11/11 · `e74` 10/10 · `b1` 8/8 · `b3` 4/4 · `c238` 4/4 · `e7` 2/2
- **~6%:** `nsga3` 2/31 · `smsemoa` 2/33
- **ZERO:** `nsga2` 0/26 · `moead` 0/23 · `b4` 0/11 · `c217` 0/5

> **As assistidas por surrogate (ajuste de Kriging/GP ⇒ BLAS/LAPACK) divergem sempre que a
> microarquitetura muda. As baselines de EA puro são bit-estáveis mesmo em hardware diferente.**

**Pior célula medida:** `c141/ZDT6/semente 11` — HV **0,41076** (vm1) contra **0,00000** (vm5);
IGD+ 0,0371 contra 1,1950; mesmo `fe=308`, `n_geracoes` 45 vs 43. **Bifurcação total, não
arredondamento.**

### 3.1 O piso de ruído empírico, em dois níveis

| nível | ΔHV p95 | ΔIGD+ p95 |
|---|---|---|
| **CÉLULA** (semente única, hardware heterogêneo — regime B, n=168) | **10,60%** (p99 26,24%, max 100%) | **28,50%** (p99 56,45%) |
| **CONTRASTE** (mediana de 30 sementes) — exposição REAL medida (404/11.618 = **3,48%**) | **1,225%** | **3,238%** |
| CONTRASTE — exposição total hipotética | 5,012% | 10,876% |

**Contra o O-18 (HV ≤1,55% · IGD+ ≤58,98%):** ele é **otimista para HV no nível de célula** (31 dos
43 pares o excedem; máximo 100% ≈ **65×** o declarado) e **fortemente pessimista para IGD+**. E não
distingue regime de hardware nem classe de config — as duas variáveis que explicam praticamente
toda a variância medida.

**Correção metodológica importante:** 7 "divergências" eram **falso positivo puro** — c122 (5) e
c262 (2) com `fe` diferente entre cópias. Truncando ao FE comum (regra O-21), os arrays ficam
bit-idênticos. Sem a correção apareceriam como ΔHV até 8,94% e ΔIGD+ até 76,11%.

---

## 4. Os 11 achados classe (3) de gravidade ALTA — e o padrão deles

**Nenhum é defeito de mecanismo. Todos são de CUSTÓDIA DO DADO.** Esse é o retrato do estágio em
que a campanha está: o algoritmo está provado; o que precisa de atenção é o caminho do arquivo.

| # | config | achado | escala |
|---|---|---|---|
| 1 | **b1** | **CÉLULA QUIMERA** — `BBOB_F17/semente 8` no canônico é a mistura de duas execuções: ⑥①②③④ de uma (mtime 09/08) e ⑤ de outra | 1 célula |
| 2 | **c122** | **`upload_status = erro 403`** (a service account não tem `storage.objects.delete`) — sob D54 a ③ deveria estar no bucket | **220/738 (29,8%)** |
| 3 | **c149** | mesma assinatura: ③ em estado de existência **não verificável**, e o instrumento que diria onde ela está foi apagado por um `except` genérico | **210/717 (29,3%)** |
| 4 | **c154** | ③ **não está no disco local NEM nos espelhos das 6 VMs**; ⑤ registra o mesmo 403 | **149 (23,3%)** |
| 5 | **e103** | **⑦ ausente em 669/669 (0,0%)** enquanto os outros 3 offline estão em 100% (b5m 679/679, b5r 725/725, moead_media 725/725) | 100% do config |
| 6 | **c141** | ⑥ da célula `ZDT4/9` é **órfão truncado**: 368 bytes, só o header — o espelho da vm5 tem o arquivo íntegro | 1 célula |
| 7 | **c122** | 🔴 **a semente 42 da M8 diverge INTEGRALMENTE da semente 42 que a F5/T11 auditaram** — **0/25 células com IGD idêntico** (razões 0,57×–1,75×), padrão de cache-hit diferente | 25 células |
| 8 | **c154** | **máquina confundida com semente**: 29 das 30 sementes rodaram inteiras num único host, e o ponto de corte das 300 ⚪ é decidido pela máquina | 300 ⚪ |
| 9 | **c141** | deriva cross-shape quantificada — **o O-18 está desatualizado por até 64×** | transversal |
| 10 | **c217** | déficit sistemático e **não declarado** de um bloco de `sonda_estratificada` por célula | **298/750 (39,7%)** |
| 11 | **b5m** | os **pesos de decomposição no header do ⑥ continuam ausentes** — o `CONTRATO_DE_DADOS.md:332` os exige | 686/686 headers |

**O nº 7 é o mais delicado para a escrita:** se a semente 42 da M8 não reproduz a semente 42 da
F5/T11, é preciso decidir **qual corpus é canônico** e se as afirmações numéricas das auditorias
anteriores são re-emitidas sobre o corpus novo. É decisão sua (D81).

**Os nºs 2, 3 e 4 somam ~580 células** cujo ③ pode ou não estar no bucket. O 403 é de
`objects.delete`, o que *sugere* objeto pré-existente — mas **ninguém conferiu**. Um
`gsutil ls` resolve.

---

## 5. Os tetos T que caíram

O ganho mais concreto das 30 sementes, config a config. No b1, por exemplo, **5 tetos caíram**:

- **Fórmula de semeadura** — `doe_hash` do ⑥ ≡ do artefato em **733/733**; `max|ΔX| = 0,0 EXATO`
  em 701/701; os 733 hashes **todos distintos**
- **Determinismo** — 34 pares de duplicatas em máquinas diferentes são **bit-idênticos**
- **Separação código × máquina** — mesmo `repo_hash` em 700/700 ⇒ o eixo código está fixo
- **Taxa de sucesso** — medida por problema, deixou de ser anedota
- **O modo SPLICE do writer** — a T11 o declarou "não provadamente eliminado"; agora: **0 linhas
  malformadas em 442.263 linhas de 733 arquivos**, a ~29× a exposição da s42. A correção T11-G1
  está empiricamente validada.

**E um teto VOLTOU:** o `U5` (não-perturbação da sonda) tinha sido fechado pela T11 num par
`g6_com`/`g6_sem`. A campanha de 30 sementes **não tem nenhum gêmeo sonda-off**
(`sonda.desligada=false` em 700/700) — para este corpus a propriedade é inferência, não medição.

---

## 6. O que verifiquei sobre as afirmações dos artigos

Esta é a camada que **só 30 réplicas permitem**, e ela produziu correções reais. Exemplo do b1
(ParEGO, Knowles TEVC 2006), §VIII:

> *"Not only is the mean higher, but the standard deviation is consistently lower, sometimes by
> several orders of magnitude."*

**Parcialmente confirmada — e o "consistently" não se sustenta.** sd(b1) < sd(nsga2) em **20/24
(83%)**, razão mediana 0,385 (dispersa 2,6× menos). Mas há **4 contraexemplos**: ZDT6 é **2,47×
MAIOR**, ZDT4 1,78×, BBOB_F55 1,17×, MMF11_L 1,17×. E *"several orders of magnitude"* não se
reproduz: a maior redução é ~29× (1,5 ordem), no DTLZ7.

E uma nota dura: **no ZDT6 o b1 tem mediana muito melhor (0,878 × 0,379) e ao mesmo tempo é 2,5×
menos confiável** — há sementes que não entram na bacia boa.

*"Better worst-case performance"*: **CONFIRMADA** — min(HV) do b1 > min(HV) do nsga2 em **20/24
(83%)**, taxa *maior* que a da mediana (19/24), ou seja a vantagem é de fato mais forte na cauda.

---

## 7. Escalações ao autor (D81/D97)

1. **Qual corpus é canônico** — a semente 42 da M8 ou a da F5/T11? (achado nº 7)
2. **Censo do bucket** para as ~580 células com `upload_status: 403` (nºs 2, 3, 4)
3. **A ⑦ do e103** — rodar `final_eval.py --alg e103 --all-seeds` ou declarar a ausência? (nº 5)
4. **Substituir o O-18** pelo piso empírico de dois níveis do §3.1
5. **A célula quimera do b1** e o ⑥ órfão do c141 — repor dos espelhos ou declarar? (nºs 1, 6)
6. **O quadro de Friedman do §15.1 não é executável** — escolher o recorte (§2.4)
7. **A exposição de hardware**: 404/11.618 células (3,48%) saíram da vm5 após o corte, e nos
   configs surrogate a divergência é 100%. Re-rodar essas 404 ou declarar?

---

## 8. Artefatos

| artefato | endereço |
|---|---|
| Este relatório | `f5/f30/RELATORIO_FINAL_F30.md` |
| 21 relatórios por config | `f5/f30/configs/*.json` |
| 4 sínteses transversais | `f5/f30/transversal_{ruido,incap,contrato,ciencia}.md` |
| Censo completo dos 22 | `f5/f30/censo_completo_22.csv` (15.129 linhas) |
| Recenso main sob O-21 | `f5/f30/recenso_main_O21.csv` |
| Placar | `f5/f30/placar.json` |
