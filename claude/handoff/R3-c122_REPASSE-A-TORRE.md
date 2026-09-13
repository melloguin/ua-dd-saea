# R3-c122 — REPASSE À TORRE (o dossiê completo da sessão, para a instância que gerou o cartão)

> **Para quem lê:** a torre central (a instância que monta os prompts e mantém
> SPEC/registros). Este documento é autossuficiente: contexto, cada etapa
> executada com o comando e o resultado, os achados, e — **na §7 — as
> DEFINIÇÕES EM ABERTO que a torre DEVE levantar com o autor**. Os companheiros
> são `handoff/R3-c122.md` (o *o quê*, com os patches por arquivo:linha) e
> `handoff/R3-c122_RELATORIO-EXECUCAO.md` (o *como*, a narrativa com o que deu
> errado). Este repasse não os substitui; ele os indexa e concentra o acionável.

**Data da sessão:** 2026-07-19 → 2026-07-21 · **Cartão:** R3-c122 (θ-DEA-DP),
1º algoritmo da Rodada 3, ONLINE, `env_main` no Mac (DI-14/RI-08).
**Veredito: CARTÃO FECHADO — gate VERDE exit 0 nos 3 problemas, regressão
completa verde, 4 commits `[R3-c122]`, zero pendência de execução.**
**Fidelidade NÃO julgada** (D97 — validação manual do autor, em lote; os
números-guia estão no handoff).

---

## 1. Resposta direta: está 100% pronto? O que foi RODADO para provar?

**Sim, 100% do escopo do cartão.** Toda validação abaixo foi executada de
verdade (nada é estimativa), e a bateria final foi **re-executada em
2026-07-21** no fechamento deste repasse:

| # | Comando executado | Resultado |
|---|---|---|
| 1 | `run_c122('main','c122','MMF1',0)` | `fe_final=61` (=31·2−1 EXATO), 41 ger, `status=ok`, wall 49,3 s |
| 2 | `run_c122('main','c122','DTLZ2',0)` | `fe_final=371` (=31·12−1), 240 ger, `status=ok`, wall 709,4 s |
| 3 | `run_c122('main','c122','ZDT1',0, teto_s=8*3600)` | `fe_final=929` (=31·30−1), 600 ger, `status=ok`, **`motivo_parada='orcamento'`** (o teto de 8 h NÃO disparou), wall **5.060,1 s = 1,41 h** |
| 4 | `accept.py R3-c122 --alg c122 --problema {MMF1,DTLZ2,ZDT1} --semente 0` | **exit 0 nos 3, 11/11 checks cada** (re-rodado 2026-07-21: 3× VERDE) |
| 5 | `python -m unittest discover -s tests -t .` | **228 OK (3 skip)** — 23 testes novos do c122 (re-rodado 2026-07-21) |
| 6 | `C122_SLOW=1 python -m unittest tests.test_c122.TestRunsCompletos` | **2 OK em 194,6 s** — determinismo bit-a-bit (2 runs MMF1 ⇒ ① idêntica) **e** invariante §3.1 (① com sonda ≡ ① sem sonda) |
| 7 | `accept.py {F0-01-harness,F0-02-doe,F0-03-export,F0-04-metrica}` | exit 0 ×4 (re-rodado 2026-07-21) |
| 8 | `accept.py R3-00-harness --problema {MMF1,DTLZ2}` | exit 0 ×2 |
| 9 | `scripts/preflight.py` | exit 0 (re-rodado 2026-07-21) |
| 10 | Auditoria pyarrow dos 3 runs (script ad-hoc, resultados na §4) | limpa nos 3 |

**Gates R1 NÃO rodados** (faixa MATLAB ativa na mesma árvore — instrução do
cartão) **nem R2-c\*** (desnecessário). O que resta no cartão é, por desenho,
de OUTRAS mãos: a validação de fidelidade (autor, D97), a marcação do
`cards/INDEX.md` (torre) e as definições da §7 (autor via torre).

## 2. O que foi entregue (arquivos e commits)

| Artefato | O quê |
|---|---|
| `src/c122_thetadeadp.py` (novo, ~900 linhas) | O runner: fork instrumentado do laço `scalar_dom_ea_dp` sobre o `standalone_harness` (REUSO das APIs R3-00: `pin_runtime`/`load_doe`/`FEBudget`/`AuditLogger`/`load_sonda`/`sonda_due`/`emit_sonda_block`/`minimo_comum_di10`/`SnapshotBuffer`/`write_run_outputs`/`iteration_seed`/`iteration_cleanup`) |
| `src/experiment.py` | SÓ a linha do c122 descomentada em `_DISPATCH_LOADERS` (conforme a faixa) |
| `tests/test_c122.py` (novo, 23 testes) | Fidelidade do fork (escolha idêntica ao stock), DEF-B11.1, bypass, creator/PerCounter, P2/P3, RNG, dispatch, + 2 provas caras atrás de `C122_SLOW=1` |
| `scripts/accept.py` | Branch **ADITIVO** `R3-c122` + `check_r3_c122` (extensão de faixa **AUTORIZADA pelo autor** — ver §5.2) |
| `handoff/R3-c122.md` · `_RELATORIO-EXECUCAO.md` · este repasse | Documentação |
| Dados: `data/experiments/main/c122/` | Os 3 runs completos (4 camadas + jsonl + manifesto cada) |

Commits (branch `experiment/definitive_algorythms`, ritual anti-mistura com
staged conferido em cada um): `dc40174` (código) → `e921b3d` (handoff) →
`57c52c0` (relatório) → `29e8539` (ZDT1 + fechamento). **`cards/INDEX.md` NÃO
marcado** (a torre marca). Árvore limpa da minha faixa ao fim.

## 3. O processo, etapa a etapa

1. **Verificação de ambiente** (PASSO 0 do prompt): `PY` correto, torch 2.11.0 /
   deap 1.4 / matplotlib 3.11.0 presentes (nada instalado — D80), `c122 →
   env_main` conferido no `envs.json`, `[R3-00]` no log. ✅
2. **Leitura obrigatória**: `CONTRATO_DE_DADOS.md` inteiro, `handoff/
   R3-00-harness.md` (§herança), contrato R3 + cartão `alg_c122_thetadeadp.md`
   inteiros, REGISTRO A3/A4/A5, CLAUDE.md + regras globais. ✅
3. **Recon multi-agente com verificação cética** (4 leitores × 4 verificadores):
   mapeou o repo oficial, a S.5, e a API real do harness. Os verificadores
   corrigiram 5 âncoras e apontaram 8 omissões materiais — duas delas
   evitaram bugs sérios (os DOIS `emit_sonda_block` de assinaturas diferentes;
   o default `regime="offline"` do `write_run_outputs` que carimbaria a ③
   online inteira como offline).
4. **Verificação adversarial da P3** (4 lentes independentes instruídas a
   REFUTAR): **4/4 confirmaram** que a DI-16.3 não tinha referente no código →
   **pára-e-pergunta (D81)** → autor cravou a **opção A+** (§5.1).
5. **Implementação** (`src/c122_thetadeadp.py`) com as decisões do cartão:
   DEF-B11.1 pela assinatura (tabela S.5 REUSADA de `metrics.F_MIN_MAX` +
   margem 10% — uma fonte só), Balde B completo (N=11/15, SBX 1.0/30, PM
   1/n/20, N*=7000, 1 infill, FNN 2×200, Adam 1e-3/32/1e-5, E_init=20,
   T_max=11n+24, γ=0,9 com `>=`, Q_max=300, θ_PBI=5, x∈[−1,1]), cap anti-spin
   (10 + fallback p_sum, cada disparo logado), determinismo (4 sementes
   SeedSequence com `alg_id=5` do `seeds.json`, creator/PerCounter novos por
   run, `use_deterministic_algorithms(True)`, threads=1).
6. **Smoke MMF1 → bug real encontrado e corrigido**: cache-hit D89 × arquivo
   (§5.3) — `IndexError` reproduzido, corrigido, coberto.
7. **Runs MMF1 → DTLZ2 → ZDT1** (este sob teto de 8 h, que não disparou).
8. **Gate**: branch `R3-c122` escrito (após a 2ª autorização D81) e VERDE nos 3.
9. **Testes**: 23 novos; 1 falha inicial era do PRÓPRIO teste (o stock também
   devolve `None` no spin — concordar no `None` é concordar); corrigido para
   percorrer um ciclo completo de clusters com anti-vacuidade.
10. **Provas caras**: determinismo bit-a-bit + não-perturbação da sonda. ✅
11. **Regressão completa** (suíte, F0×4, R3-00×2, preflight). ✅
12. **Auditoria pyarrow dos 3 runs** (§4) — incluiu o episódio instrutivo de
    dois "vermelhos" que eram defeito do meu script de auditoria, não dos dados.
13. **Documentação + 4 commits** pelo ritual.

## 4. Auditoria pyarrow — o resultado consolidado

| Verificação | MMF1 | DTLZ2 | ZDT1 |
|---|---|---|---|
| ① linhas (=31D−1) | 61 | 371 | 929 |
| ① fases init/opt | 21/40 ✓ | 131/240 ✓ | 329/600 ✓ |
| ③ blocos sonda (contíguos, ×2000, ORDEM do artefato) | 22 ✓ | 121 ✓ | 301 ✓ |
| ③ linhas de busca (≤100/ger) | 3.632 ✓ | 9.023 ✓ | 44.857 ✓ |
| ③ e(z) ordenado desc (gerações fora de ordem) | 0/41 | 0/240 | 0/600 |
| ③ `fe_treino_max` nulos | 0 | 0 | 0 |
| ③ sonda `real_solution_id` NULL | ✓ | ✓ | ✓ |
| ③ `pred_tipo={'score'}`, μ/σ NULOS | ✓ | ✓ | ✓ |
| ④ 4 colunas de tempo, nulos | 0 | 0 | 0 |
| ⑤ timing + sigma_dict (8 chaves) + bloco sonda | ✓ | ✓ | ✓ |
| cache-hits · spins (cap nunca atingido) | 1 · 5 | 0 · 0 | 0 · 21 |

## 5. As 3 decisões/achados estruturais da sessão

### 5.1 🔴 P3/DI-16.3 era INEXEQUÍVEL → autor cravou a opção A+
A redação pedia "TOP-100 do pool de 7.000 por `e(z)` + agregados de `e(z)` do
pool inteiro". Provado (4 lentes adversariais, 4/4): `e(z)` é grandeza
**INTRA-conjunto**, só existe para a categoria vencedora (≤Q_max=300,
`selection.py:158-168`); sobre os 7.000 o código computa um score **INTER** vs
o representante (`scf`, `selection.py:108`) — sem soma em *j* e sem indicador de
dominância; `e(z)` real sobre 7.000 = C(7000,2)×2 = 49M pares/iteração com
lista Python intermediária (~8–10 GB/rede) — inviável. **A+ implementada:**
③ = TOP-100 por `e(z)` da categoria (a cabeça do ranking, onde a decisão
acontece; `real_solution_id` só no escolhido); jsonl = o que o algoritmo DE
FATO computa sobre os 7.000 (`n_q1/q2/q3`, `n_acordo`/`n_desacordo`,
`pool_scf_{min,med,max}`) + `ez_cat_{min,med,max}`. Custo e perturbação zero.

### 5.2 Extensão de faixa autorizada: o gate não existia
O critério de aceitação (`accept.py R3-c122 … exit 0`) referenciava um branch
inexistente, fora da faixa. Pára-e-pergunta → autor autorizou o branch
**ADITIVO** (`check_r3_c122`, zero branch existente tocado), inserido ANTES do
catch-all F0-01 que engoliria o cartão com um falso VERDE. Diferença de desenho
vs `check_r3_00`: este AFERE um run já gravado (não re-roda — um run de ZDT1
custa 1,4 h).

### 5.3 Bug real: cache-hit D89 × o arquivo do algoritmo — **ATINGE c149/e81**
O laço stock (`algorithms.py:48-50`) anexa ao arquivo incondicionalmente (o
repo não tem dedup). Com o nosso dedup, um cache-hit (0 FE) fazia o arquivo
ultrapassar `maxfe` e estourar o `rel_map` — **`IndexError` MEDIDO na última
geração de MMF1**. Fix: no cache-hit o arquivo NÃO cresce; a ③ continua gravada
(a predição foi decisão-relevante) com `real_solution_id` da solução
preexistente; cap de segurança para cache-hits consecutivos. Ocorreu 1× em
MMF1, 0× nos demais (fenômeno de D baixo).

## 6. Custo medido (o insumo do M7/M8)

- Fit domina e cresce com D: **33% (MMF1) → 78% (DTLZ2) → 87% (ZDT1)** do wall.
- **MAS o custo por geração PLATÔA** quando `|archive| > T_max = 11D+24`
  (=354 em D=30): 8,4 s/ger estável no ZDT1. O c122 **escapa da parede O(n³)
  por construção** (mesmo mecanismo do K-RVEA) — contraste direto com
  c238/c262 para o §17.6.
- Sonda: barata e previsível (2,7% do wall no ZDT1). `tempo_geracao_s` a exclui.
- O ~1,25e5 pares/época ×≤20 ×2 redes do cartão em D=30: **confirmado** (354²).
- ⚠ **Dimensionar o M8 pelos walls FINAIS** (49,3 s / 709,4 s / 5.060,1 s), NÃO
  pelas projeções intermediárias do relatório (saíram pessimistas 2–4× porque a
  máquina estava disputada pela minha própria regressão durante a medição).

## 7. 🔴 DEFINIÇÕES EM ABERTO — a torre DEVE levantar estas com o autor

> Nenhuma delas bloqueia o c122 (fechado); as #4 e #5 **bloqueiam ou arriscam
> cartões SEGUINTES** se não forem decididas antes.

1. **Reescrever a DI-16.3 (SPEC + REGISTRO + bundles).** A redação vigente
   ("TOP-100 do pool por e(z) + agregados do pool") é inexequível (§5.1) e o
   autor já cravou a A+ **em sessão** — mas o texto normativo continua o
   antigo. Sem o doc-sync, o próximo leitor (ou a R4, ao ler a ③ do c122)
   reencontra a contradição. Sugestão: cravar com os nomes exatos dos campos
   gravados (`n_q1/n_q2/n_q3`, `n_acordo`/`n_desacordo`, `pool_scf_*`,
   `ez_cat_*`, TOP-100 da categoria). *Território da torre — não editei.*
2. **Corrigir a perna (ii) da justificativa da DI-16.2.** "É o contexto real em
   que o modelo decide" é factualmente errado: a população selecionada nunca é
   referência de dominância no código (a decisão real é rep-do-cluster →
   intra ≤300). A decisão (a) fica — a perna (i) (tamanho fixo ⇒
   comparabilidade) sustenta sozinha —, mas a sonda do c122 deve ser lida como
   **instrumento com referência própria**, não como o score interno da busca.
   Já está no `sigma_dict` dos manifestos; falta o texto normativo.
3. **`teto_wall` × `is_run_done` (infra, M7).** Implementei o teto como
   `status='failed'` + `motivo_parada='teto_wall'` + curva parcial preservada
   (não foi exercitado — ZDT1 fechou em 1,41 h). Mas `is_run_done` não conhece
   `motivo_parada`: um run abortado por teto contaria como "pronto" e a esteira
   não o refaria. Mesmo buraco do item 6 do handoff R3-00; decisão de infra.
4. **Cache-hit D89 × arquivo do algoritmo — ratificar e PROPAGAR (bloqueia
   risco em c149/e81).** A solução da §5.3 está em código e coberta por gate,
   mas é decisão minha de sessão: ratificar, e avisar os cartões c149/e81 no
   contrato transversal (os dois têm arquivo/dataset de treino crescente e o
   mesmo hazard).
5. **N.1.1 "float64" não é universal — generalizar?** O c122 EXIGE float32
   (`prediction.py:24` faz `.float()`; com o default float64 do `pin_runtime`
   o forward levanta `RuntimeError` — MEDIDO). Escopei o float32 ao driver com
   restauração garantida e registro no manifesto. Proposta: N.1.1 passar a
   dizer "o dtype que o repo do autor exige, registrado no manifesto" (o c149
   pode ter o mesmo problema).
6. **Pendências de OUTRAS mãos (não são definições, são fila):** validação de
   fidelidade do c122 pelo autor (D97 — dossiê em lote; números-guia e a
   armadilha do sentinela `acc=1` p/ classe ausente estão no handoff §achados
   5) · marcação do `cards/INDEX.md` (torre).

## 8. Onde está cada coisa

- **Patches por arquivo:linha, contrato de determinismo, materialização
  P2/P3, números-guia da fidelidade:** `handoff/R3-c122.md`
- **Narrativa do processo (o que deu errado e como foi pego):**
  `handoff/R3-c122_RELATORIO-EXECUCAO.md`
- **Dados dos 3 runs:** `data/experiments/main/c122/exp_main_c122_{MMF1,DTLZ2,ZDT1}_0.*`
- **Reprodução:** seção "Como reproduzir" do handoff (comandos literais).
