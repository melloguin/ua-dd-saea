# T14 — A CALIBRAGEM DOS INSTRUMENTOS · HANDOFF FINAL (2026-08-01)

> **Estado: 11/11 itens fechados.** 20 commits (10 de item + 10 de rastreador), do
> `7ecc0d5` ao `92b5cde`. **Suíte 826 OK · 0 falhas · staleness 0.** Nada pushado.
> Zero toques em `algorithms/` (vendorizado), em `f5/` (evidência congelada) e em
> `data/experiments/` — verificado por `git diff --name-only`.

---

## §1 · O PLACAR

| item | bloqueador | commit | o que mudou de fato |
|---|---|---|---|
| T14.1 | BL-11 | `7ecc0d5` | `tempo_checkpoint_s` como campo próprio da ④/⑤ + desconto no treed_media |
| T14.2 | BL-21 | `2fc3e78` | `footer_fechado()` no painel + varredura dos consumidores do ⑥ |
| T14.3 | BL-14 | `73391b1` | `frente1_excede_pop` contra o N EFETIVO (moead+nsga3) |
| T14.4 | BL-17 | `3b101cd` | o G-7 passa a vigiar a linha dos pisos do §6.1 |
| T14.5 | BL-12 | `decebe2` | calibragem do `REGRA_DO_ROTULO` do b4 RE-MEDIDA |
| T14.6 | BL-13 | `c1ed7e4` | `geracoes_derivadas` ramificada por família de operador |
| T14.7 | BL-18 | `1dc9f9e` | `espaco_modelo` nas linhas de busca (e103 **e c217**) |
| T14.8 | BL-20 | `1dc9f9e` | `nota_potencia_de_2` vira f-string do `q` real |
| T14.9 | BL-19 | `9143998` | convenção `p0`/`p1` no CONTRATO + SPEC (3 sítios) + bundle |
| T14.10 | B3 | `92a88c1` | exceção do writer ⑥ do MATLAB fechada **com tripwire** + comentário |
| T14.11 | §12.3 | `d263669` | `mapa_sementes.json` balanceado (6,02% · critério ≤10%) |

**Suíte:** 688 → **826** (+138 testes novos, 8 arquivos). Cada item entrou com
controle negativo ou asserção de valor — nenhum com `assertIn` de texto sozinho.

---

## §2 · ⚠ O QUE O CARTÃO/BLOQUEADOR DIZIA E O DADO DESMENTIU

Quatro vezes. **Em todas o dado prevaleceu, e o teste tranca a versão medida.**

### 2.1 · T14.1 — "o padrão é o mesmo nos 8 runners". Não é.
O cartão manda descontar o I/O do checkpoint nos 8. Auditados um a um: em **7**
o `talvez_gravar` já roda DEPOIS de a ④ da geração fechar — o I/O caía no vão
ENTRE gerações, **fora** do `tempo_geracao_s` mas **sem nome**. Medido em célula
real (`batch/sobol_batch/MMF1`, cadência 1): **4,153 s de checkpoint num run de
5,723 s = 72,6% do wall**, contra Σ`tempo_geracao_s` = 0,109 s. Não era inflação:
era buraco não-atribuível. Só o **`treed_media`** inflava de fato (a ④ dele é 1
linha e fecha depois do laço inteiro).

**Controle negativo, célula real, env_c311** (`sweep-big-mvns/ZDT4/42`):

| | checkpoint OFF | cadência 1 |
|---|---|---|
| `tempo_busca_s` | 3,2089 | 3,2798 (**+2,2%**) |
| `tempo_checkpoint_s` | 0,0 | **2,6632** |

Pré-BL-11 o segundo teria gravado 3,2798+2,6632 = **5,943 s = +85,2%**. O teste
reconstrói esse valor antigo e EXIGE que ele reprovasse a asserção — senão
passaria por vacuidade.

### 2.2 · T14.5 — o AUC do cartão está errado.
O cartão manda gravar `AUC 0,5065` na régua do smoke. Re-medindo das baterias da
F5: **0,5075** — que é o valor publicado na §6.3 do `b4.md`, na regra de leitura
12 e no controle cruzado régua-do-smoke × célula-MMF1-da-s42. O `0,5065` aparece
**uma única vez**, na tabela do §E1 do mesmo relatório. Gravei o medido.
Bônus: caiu também a frase *"elas medem outra coisa e inflam o número"* — em M=2
(**19/25** células do b4) a leitura alternativa é numericamente IDÊNTICA à DI-18,
e o teste prova isso re-medindo (mesma prev/acc/AUC até 9 casas).

### 2.3 · T14.6 — a fórmula que o BL-13 prescreve acerta ZERO.
O BL-13 manda usar `floor((20D+clones)/N_ef) + 1` no moead. **Medido nas 112
células de piso: o `+1` acerta 0/28; sem ele, 28/28.** O BL-13 também afirma que
a fórmula de hoje "erra por +1 determinístico em 28/28" no smsemoa: ela acerta
28/28 — lá `N_ef` é sempre 20 e os dois denominadores coincidem.

| | nsga2 | nsga3 | moead | smsemoa | total |
|---|---|---|---|---|---|
| fórmula única (hoje) | 27/28 | 27/28 | 21/28 | 28/28 | **103/112** |
| ramificada | 27/28 | 27/28 | **28/28** | 28/28 | **110/112** |

O 103/112 reproduz EXATAMENTE o número que a própria string já publicava — é o
que valida a metodologia (n_dup = `cache_hits` do ⑤).

### 2.4 · T14.7 — o BL-18 nomeia 3 configs; só 2 têm o defeito.
O critério do próprio bloqueador é a **assimetria INTRA-run**. Medido na ③:

| config | sonda | busca | veredito |
|---|---|---|---|
| **e103** | `"cru"` 40.000 | **NULL** 19.800 | assimétrico ⇒ corrigido |
| **c217** | `"cru"` 198.000 | **NULL** 201 | assimétrico ⇒ corrigido |
| c262 | NULL 204.000 | NULL 2.010 | **uniforme ⇒ não é defeito** |
| b4 (controle) | `"cru"` 202.000 | `"cru"` 200 | já estava certo |

O **c217 não está no texto do §3 do cartão** (só no campo `configs` do BL-18) —
mas tem a mesma assimetria, medida, e o mesmo fix de 1 literal: fechar o
bloqueador deixando-a de pé tornaria o item falso. O **c262 ficou de fora de
propósito**: não tem o defeito pelo critério do BL-18, e declara a semântica no
`sigma_dict` do ⑤ (DEF-C4). Preencher a coluna lá seria decidir semântica de
config — item novo, do autor (D81).

---

## §3 · A ÚNICA DECISÃO QUE EU TOMEI (e como revertê-la em 1 linha)

**T14.10 · B3.** *"Fechar a exceção do writer MATLAB recomendada no repasse"* foi
lido como **FORMALIZAR a recomendação do T12 §7.3** ("não trocar o writer antes
da tag"), **não** como aplicar o writer Java. Três razões:

1. é literalmente a exceção que o repasse **recomenda**;
2. trocar o writer nos **19 sítios de 13 configs** é o oposto de *"~15 linhas de
   código · nada toca mecanismo"*, que é o cabeçalho deste cartão;
3. o §12.6 do repasse escalou a pergunta ao autor e **ela nunca foi respondida**
   — decidi-la sozinho na véspera da tag é o que a D81 proíbe.

**Se a intenção era aplicar o writer Java: é 1 função, e o caminho está medido e
pronto** em `tests/test_t12_jsonl_matlab.py` (`fprintf` = 30 linhas partidas ·
`fwrite` = 26 · `java.io.FileOutputStream` = **0**).

**O que ficou no lugar** é melhor do que a prosa que havia: a exceção virou
**tripwire**. O escritor único não é promessa — é consequência mecânica de o
`experiments.py` derivar o `KNOWN_ALGORITHMS` dos loaders e a CLI **recusar** os
13 configs MATLAB (aferido por comportamento: `SystemExit`). Se algum dia um
config MATLAB entrar no dispatch Python, o teste fica vermelho e o B3 volta à
mesa **antes** de a campanha gravar ⑥ spliced.

---

## §4 · O QUE PRECISA DO AUTOR (nada bloqueia a tag)

### 4.1 · 🔴 A frota do T14.11 — nomes, `jobs` e `envs` das 5 máquinas NOVAS
O mapa está gerado, validado e consumido pelo driver, **mas** o repo só conhece
`mac`/`v5`/`v6`/`vm3` (perfis do `lote3s.sh`). As outras 5 entraram como
**PLACEHOLDER** (`vm1 vm2 vm4 vm7 vm8`, `jobs=6`, todos os venvs) — é o item
§12.2 do repasse ("quem provisiona?"), nunca respondido. O artefato declara isso
em `_meta.frota._pendente_autor` e um teste cobra que a declaração esteja lá.

**Como corrigir (1 comando):** editar/criar
`claude_code_context/artifacts/frota.json` com a frota real e rodar
```bash
python3 scripts/mapa_sementes.py
```
O mapa inteiro é refeito e os testes seguem valendo. **O `jobs` é a capacidade
(runs simultâneos) e é o que mais move o resultado** — a frota vai de 8 a 32
cores e hoje está declarada como 4/6/12/6 + 6×5.

### 4.2 · 🟠 B3 — aplicar o writer Java ou manter a exceção? (§3 acima)

### 4.3 · 🟡 O `moead_media/ZDT1_42` tem 3 footers, e os dois primeiros discordam
Achado de passagem no T14.2, **fora do escopo do cartão**, não tocado:
```
[0] status='ok'     fe_final=929
[1] status='failed' fe_final=929  motivo='erro_RuntimeError'
[2] status='ok'     fe_final=None
```
A primitiva `footer_fechado` devolve o **[0]** (o primeiro com `fe_final`), e o
⑤ dessa célula diz `ok`. Mas o [1] existe e é `failed`. É a armadilha *"status
mente, `motivo_parada` não"* (B1) numa célula real da s42. **Não mexi**: escolher
entre dois footers fechados é semântica de término (território do
`mapa_termino.json`/O-21), não conserto de leitura. Vale a mesa antes da R4.

### 4.4 · ⚪ Os 58 forasteiros e a tag (já eram do autor)
Preflight anti-forasteiro segue acusando os manifestos das VMs no disco local.
Limpeza + tag → fila D10 → disparo.

---

## §5 · COMO REPRODUZIR

```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY -m unittest discover -s tests     # esperado: Ran 826 · OK (skipped=36)
$PY scripts/staleness.py              # esperado: STALE: 0
$PY scripts/mapa_sementes.py --check  # esperado: OK, desbalanceamento 6,02%
```

O controle negativo do T14.1 no `treed_media` roda **só no env_c311** (as 5
asserções pulam limpo no env-main):
```bash
OMP_NUM_THREADS=1 PYTHONHASHSEED=0 MPLBACKEND=Agg \
  /Users/gmello/Documents/python_venvs/env_c311/bin/python \
  -m unittest tests.test_t14_cronometro     # 24/24 OK, ~65 s
```

Os testes de célula MATLAB real (T14.3/5/6/7) pulam onde não houver MATLAB.
Custo total deles na suíte: ~95 s (8 células de piso + 1 b4 + c217 + e103).

---

## §6 · O QUE APRENDI (reutilizável)

1. **Auditar os 8 antes de consertar os 8.** O cartão dizia "o padrão é o mesmo";
   7 de 8 já estavam certos. Consertar sem auditar teria produzido 7 desconto
   duplos — o oposto do item.
2. **Número de relatório é hipótese até ser re-medido.** Três dos quatro
   desmentidos do §2 vieram de recontar o que já estava escrito (AUC 0,5065; o
   `+1` do BL-13; os 3 configs do BL-18).
3. **O corpus é o melhor mutante.** No T14.3 e no T14.7 o controle negativo não
   precisou ser fabricado: os 112 ⑥ de piso e as ③ da s42 foram gravados pelo
   código antigo e registram o defeito. Melhor que um mutante sintético — não
   tem como ser teatro.
4. **Contar ocorrências acha o sítio que a lista esqueceu.** O teste do T14.9
   afirmava "a SPEC tem 2 sítios" (os que o cartão nomeia) e reprovou: havia um
   **terceiro** com o par inexistente `(p1,p2)`.
5. **Código morto com a semântica errada é um convite.** No T14.2 o 3º sítio do
   padrão `[-1]` era uma variável atribuída e nunca lida. Removê-la vale mais que
   "corrigi-la": corrigida, ela ficaria lá, pronta para alguém fiar de volta.
6. **Guloso por grupo não balanceia.** O LPT sozinho deu 30,6% de
   desbalanceamento; o gargalo nasce da INTERAÇÃO entre grupos (a máquina lenta
   que já levou uma semente cara). Busca local global de 1 movimento: 6,02%.

---

## §7 · O QUE EU FIZ ERRADO (e custou tempo)

1. **Escrevi o teste do painel com o `data_root` errado** — `naming.jsonl_path`
   já acrescenta `experiments/`, e eu passei `<tmp>/experiments`. 4 testes com
   `IndexError` antes de eu ler a função. **Lição:** confira o que o helper
   compõe antes de compor por cima dele.
2. **Assertei sobre uma frase que o MATLAB quebra em linhas.** O comentário do
   `jsonl_open` tem `%` a cada linha; o `assertIn` da frase inteira reprovava com
   o texto CERTO no arquivo. Normalizei antes de afirmar. **Lição:** teste de
   texto multi-linha normaliza primeiro, senão vira refém da quebra.
3. **Contei células multiplicando duas vezes por 30.** No teste do mapa somei
   problemas-por-(exp,alg) sobre as 20.850 atribuições — 625.500 em vez de
   20.850. **Lição:** em grid simétrico, conte numa semente só.
4. **Rodei o e103 sem `datasets` no dataRoot** e levei o `assert dataset ausente`
   — a armadilha O-01, que o A43 registra e eu tinha lido. **Lição:** offline
   precisa de `datasets`, não só de `doe`/`sonda`.

Nenhum dos quatro chegou a commit.

---

## §8 · PRÓXIMO PASSO

**Nada bloqueia a tag.** Caminho crítico: §4.1 (frota — 1 comando depois que o
autor decidir) · §4.2 (B3 — sim/não) · limpeza dos 58 forasteiros (autor) → tag
→ fila D10 → **DISPARO**.

**Nada foi pushado.**
