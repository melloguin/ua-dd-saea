## MEDIÇÃO DO PISO DE RUÍDO EMPÍRICO — 30 SEMENTES (read-only; nenhum arquivo do repo tocado; nenhum experimento invocado)

### 0. O que a base de duplicatas realmente é (corrige a premissa da tarefa)
Inventário direto dos 6 stagings: **111.866 arquivos → 15.129 células distintas** (bate exatamente com o censo O-21).
- Células presentes em **≥2 VMs: 11.046** — mas a esmagadora maioria é **sombra de manifesto**: a 2ª/3ª VM só tem o `.manifest.json` (padrão dominante: `[①②③④⑤⑥] + [⑤] + [⑤]`, 3.972 casos).
- Células com **camada ① em ≥2 VMs: 762** (766 pares brutos). **A cifra "~2,6 mil duplicatas" não se confirma como par utilizável.**
- Identidade de máquina tomada do **`env.host`/`ambiente.host`**, não da pasta de staging: **13 arquivos dentro do staging da vm5 declaram `host=vm1`** → 14 pares descartados por serem a mesma máquina. **Base final: 752 pares cross-máquina.**

### 1. Deriva medida (métrica oficial §12/D69/D70; ref-point 1,1; orçamento de **FE comum** por O-21)
Âncora D92 reproduzida exatamente antes de medir: `hv_smoke_bbob_f1() = 1,0433`.

- **709/752 (94,3%) têm deriva EXATAMENTE ZERO** — parquets bit-idênticos (md5 e `np.array_equal`).
- **43 pares divergem.** 
- **7 "divergências" eram artefato de orçamento**: c122 (5 pares) e c262 (2 pares) com `fe` diferente entre cópias. Truncando ao FE comum, os arrays ficam **bit-idênticos** (`ARRAY_IDENTICO=True` nos 7) → ΔHV = ΔIGD+ = 0. Sem a correção O-21 eles apareceriam como ΔHV até 8,94% e ΔIGD+ até 76,11%. **Falso positivo puro.**

Condicionado aos 43 que de fato divergem: ΔHV med **3,35%** · p95 **24,69%** · max **100%**; ΔIGD+ med **13,41%** · p95 **47,54%** · max **96,90%**. Em absoluto: ΔHV med 0,0151 / max 0,4108; ΔIGD+ med 0,0117 / max 1,1579.

### 2. A deriva NÃO é uniforme — é um **degrau de hardware** e um **traço de classe de config**

**Corte temporal medido** (primeira divergência da vm5): **2026-08-14T10:26:42Z**. Antes dele, 4 execuções da vm5 naquele dia e 515 pares no total — **zero divergência**. Depois, 168 pares → 43 divergentes (25,6%). O ambiente de **software é idêntico dos dois lados** (MATLAB 25.1.0.2973910 R2025a Update 1, mesma plataforma) — compatível com a troca de shape da vm5, **anterior à janela de swap das ~15:20Z**.

| regime | n pares | divergentes | ΔHV p50/p95/max | ΔIGD+ p50/p95/max |
|---|---|---|---|---|
| **A** vm1×vm5 antes do corte | 515 | **0 (0,0%)** | 0 / 0 / **0** | 0 / 0 / **0** |
| **B** vm1×vm5 depois do corte | 168 | 43 (25,6%) | 0 / **10,60** / **100** | 0 / **28,50** / **96,90** |
| **C** vm1×vm2/3/4, vm10×vm5, vm2×vm3, vm4×vm5 | 69 | **0 (0,0%)** | 0 / 0 / **0** | 0 / 0 / **0** |

**Por config, dentro do regime B — a estratificação que importa:**
- **100% de divergência**: c141 11/11 · e74 10/10 · b1 8/8 · b3 4/4 · c238 4/4 · e7 2/2
- **~6%**: nsga3 2/31 · smsemoa 2/33
- **ZERO**: nsga2 0/26 · moead 0/23 · b4 0/11 · c217 0/5

Ou seja: **as assistidas por surrogate (ajuste de Kriging/GP → BLAS/LAPACK) divergem sempre que o microarquitetura muda; as baselines de EA puro são bit-estáveis mesmo em hardware diferente.** Por M: 2-obj 28% vs 3-obj 20%. Por D: sem padrão monotônico (D=10 e D=22 concentram 36 dos 43).

**Pior célula medida**: `c141 / ZDT6 / seed 11` — HV 0,41076 (vm1) vs **0,00000** (vm5), IGD+ 0,0371 vs 1,1950; mesmo `fe=308`, `n_geracoes` 45 vs 43. Bifurcação total, não ruído de arredondamento.

### 3. Piso empírico proposto — **dois níveis** (o contraste da campanha usa mediana de 30 sementes, não uma célula)

**Nível CÉLULA** (comparação de semente única, hardware heterogêneo — regime B, n=168):
`ΔHV: p50 0 · p95 10,60% · p99 26,24% · max 100%` — `ΔIGD+: p50 0 · p95 28,50% · p99 56,45% · max 96,90%`

**Nível CONTRASTE** (mediana de 30 sementes, 2 braços perturbados; Monte Carlo 1.500 réplicas reamostrando as **razões medidas** cópia-A/cópia-B do regime B, estratificadas surrogate-assistida vs baseline). **Exposição real medida: 404/11.618 = 3,48%** das células `main+ok` saíram da vm5 após o corte.
- exposição **REAL**: `HV p95 = 1,225%` · `IGD+ p95 = 3,238%`
- exposição **TOTAL hipotética** (frota heterogênea em toda célula): `HV p95 = 5,012%` · `IGD+ p95 = 10,876%`

**Contra o O-18 (HV ≤1,55%; IGD+ ≤58,98%):** o O-18 é **otimista para HV no nível de célula** (31 dos 43 pares divergentes o excedem; máximo medido 100% ≈ 65× o declarado) e **fortemente pessimista para IGD+** (só 3 dos 43 o excedem; p95 medido é 28,50% no nível célula e 3,24% no contraste). O O-18 não distingue regime de hardware nem classe de config — as duas variáveis que explicam praticamente toda a variância medida.

### 4. A consequência para a dissertação
**2.983 contrastes config-a-config** (17 configs × 25 problemas, `main`, estado `ok`, ≥15 sementes por braço; contraste = |mediana_a − mediana_b| / max × 100). Distribuição observada: HV med 11,49% · IGD+ med 34,82%.

| endpoint | cenário | inconclusivos (piso por contraste) | inconclusivos (piso único p95) |
|---|---|---|---|
| **HV** | exposição real | **55 / 2.983 = 1,8%** | 685 = 23,0% (piso 1,225%) |
| **HV** | exposição total | 221 = 7,4% | 1.124 = 37,7% (piso 5,012%) |
| **IGD+** (primária, D70) | exposição real | **62 / 2.983 = 2,1%** | 183 = 6,1% (piso 3,238%) |
| **IGD+** | exposição total | 300 = 10,1% | 512 = 17,2% (piso 10,876%) |

**Os números para o texto: com o acervo como está, 1,8% (HV) e 2,1% (IGD+) dos contrastes são inconclusivos por ruído de máquina.** Dos 62 inconclusivos em IGD+, **56 envolvem ao menos uma config surrogate-assistida** (56/2.277) contra 6 entre pares só-baseline (6/706). Se a frota heterogênea fosse total, sobe para 7,4% / 10,1%. Para referência, com o O-18 vigente aplicado como piso único seriam 24,8% (HV, 1,55%) e 75,3% (IGD+, 58,98%) — o piso de IGD+ do O-18 sozinho invalidaria 3 de cada 4 contrastes da campanha.

### 5. 🎯 CONFLITO — escalo, não resolvo (D81)
**c238 × MMF1**: em todo o acervo existe **uma única** célula desse par com ① em duas máquinas — **seed 7, vm1×vm5, executada em 13/08 (regime A)** — e a deriva medida é **ΔHV = 0,000%** (md5 dos parquets idêntico). Todas as demais 29 sementes de c238×MMF1 têm ① em **uma só** máquina (as outras VMs só têm o manifesto). **O ΔHV −9,69% citado não é reproduzível a partir do conjunto de duplicatas deste acervo.** Possíveis fontes do conflito que não pude discriminar: outra semente, outro par de máquinas, cópia de re-run acidental dos discos vm1/vm5, ou outra régua de normalização. Requer o insumo da auditoria paralela.

### 6. Tetos ⚪ e "não medido"
- **T1 (desvio declarado)**: refset do DTLZ7 gerado com grade 1200² em vez de 5000². A rotina oficial (`metrics.reference_set`) exige NDS sobre **25 M** pontos; o processo passou de 5,2 GB RSS sem terminar e foi abortado. Afeta o **nível absoluto** de IGD+ do DTLZ7, **não o Δ** (mesmo refset nos dois braços). As divergências DTLZ7 contra a tabela antiga (4/19) estão na média dos demais problemas — indício de que não contaminou, **não provado**.
- **T2**: as células **expostas** ao regime heterogêneo no acervo canônico são majoritariamente seeds 13/17/26; as células onde **medi** a deriva são majoritariamente seeds 10/11/12/20/27. A extrapolação de taxa e magnitude entre os dois conjuntos **não foi validada**.
- **T3**: causa física do corte **não medida** — não tenho `/proc/cpuinfo` das VMs. O que medi é que o env de software é idêntico dos dois lados.
- **T4**: contrastes usam só `ok`; as 501 ⚪ e 209 fail ficam fora. Presença dos parquets das ⚪ do c154 **não conferida** (ressalva do enunciado mantida).
- **T5**: validação cruzada parcial do pipeline — âncora D92 exata; contra `f5/metricas_finais_f52c.csv` (semente 42, safra anterior) 76,6% dos HV e 68,7% dos IGD+ batem a <1e-9. As 118 divergências >1e-6 estão **espalhadas uniformemente por problema**, compatível com diferença de safra de dados; **não investiguei**.
- **T6**: b5m, b5r, e103, moead_media, sobol_batch não têm células `main+ok` → fora dos 2.983 contrastes. Censo: 0 manifestos fora do censo; 80 células do censo sem manifesto (consistente com as 73 `failed` do b1 sem manifesto, O-21).

### 7. Artefatos (scratchpad, absolutos)
- `/private/tmp/claude-501/-Users-gmello/33c29160-6eb6-4277-a041-db4855486063/scratchpad/deriva_pares_crossmaquina.csv` — 752 pares, uma linha por par, com regime A/B/C, hosts, timestamps, fe/fe_comum, n_geracoes, HV/IGD+ de cada braço e os Δ%.
- `/private/tmp/claude-501/-Users-gmello/33c29160-6eb6-4277-a041-db4855486063/scratchpad/metricas_campanha_30sementes.csv` — HV + IGD+ das **15.033** células com camada ① do acervo canônico (0 erros de leitura).
- `/private/tmp/claude-501/-Users-gmello/33c29160-6eb6-4277-a041-db4855486063/scratchpad/contrastes_config.csv` — os 2.983 contrastes config-a-config.
- `/private/tmp/claude-501/-Users-gmello/33c29160-6eb6-4277-a041-db4855486063/scratchpad/refsets.npz` — os 25 reference sets normalizados usados (DTLZ7 com o desvio T1).

### 8. Recomendação (não é veredito — D97)
Substituir o O-18 por um piso **de dois níveis e condicionado**: (i) declarar que em hardware homogêneo a deriva é **exatamente zero** (515+69 = 584 pares, ΔHV = ΔIGD+ = 0 — bit-identidade cross-máquina, mais forte que a doutrina "fidelidade estatística" do RUNBOOK §6.2, que pode ser afrouxada para o caso homogêneo); (ii) usar o piso de contraste sob exposição real (**HV 1,225% · IGD+ 3,238%**) para a leitura da campanha atual; (iii) reportar o piso de exposição total (**HV 5,012% · IGD+ 10,876%**) como limite de generalização; (iv) marcar as 6 configs surrogate-assistidas (c141, e74, b1, b3, c238, e7) como **sensíveis a microarquitetura** e as baselines EA como bit-estáveis — a distinção é 100%/0% no dado medido, não uma gradação. 🔵 versão/plataforma: toca o surrogate ⇒ vai para o artigo como ressalva de reprodutibilidade.