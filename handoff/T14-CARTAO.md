# CARTÃO T14 — A CALIBRAGEM DOS INSTRUMENTOS (torre, 2026-07-31)

> **Missão:** o micro-cartão final antes da tag — fechar os 9 bloqueadores residuais do
> `bloqueios.json` (BL-11..14, 17..21) + B3 + 2 itens de operação. **~2h, ~15 linhas de
> código + docs.** Nada aqui toca mecanismo de algoritmo; tudo é medição, rótulo e painel.
> **Fontes de detalhe:** `f5/t11/dados/bloqueios.json` (cada BL com arquivo:linha, impacto e
> custo) · `handoff/T12-T13-REPASSE-TORRE.md` §12 (B3 e definições) · REGISTRO A43.
> **Doutrina (herdada do T12, inegociável): controle negativo onde houver comportamento;
> asserção de VALOR onde houver campo.** Regras de operação: `handoff/T11-PROMPT-SESSAO.md`
> §3-§4 (serial · suíte antes de commit com o interpretador
> `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python` ·
> add explícito · NUNCA push · tempdir sempre · D81 em ambiguidade).

## §1 · O CRONÔMETRO (o item que justifica o cartão)

**T14.1 · BL-11 — I/O do checkpoint fora do tempo de busca.** Hoje `tempo_busca_s`/
`tempo_geracao_s` INCLUEM o custo de gravar checkpoints (medido: 53,9% de inflação numa célula
do treed_media). Sítios: `src/treed_media.py:444,:459-462` + **os 8 runners com checkpoint**
(c262 c154 c122 c149 e81 c311 treed_media sobol_batch — o padrão é o mesmo; conserte na
FONTE comum se houver, senão nos 8). Fix: **publicar `tempo_checkpoint_s` como campo PRÓPRIO**
no ④/⑤ (CONTRATO §17.6 atualizado) **e descontá-lo** de `tempo_busca_s`. Controle negativo:
mesma célula com checkpoint FORÇADO (cadência mínima) × sem checkpoint ⇒ `tempo_busca_s`
estatisticamente igual nos dois (hoje difere ~2×), e `tempo_checkpoint_s > 0` no primeiro.
⚠ Timing é resultado de 1ª classe (§17.6/D50) — este item é a razão do T14 existir antes da tag.

## §2 · O PAINEL E OS PONTEIROS

**T14.2 · BL-21 — `progress.py:95` lê `footers[-1]`** em vez da primitiva `footer_fechado()`
(`src/manifest.py:305`) ⇒ o painel pode MENTIR durante a campanha em célula com múltiplos
footers. Fix: 1 linha + corrigir o docstring ('747→767' vira 559→747). **Varra o mesmo padrão
`[-1]`/`recs[-1]` nos demais consumidores do ⑥** (ex.: `scripts/accept.py:794`) e converta os
que encontrar. Controle negativo: ⑥ sintético com footer-espúrio após o footer real ⇒ a versão
antiga lê o errado, a nova lê o certo.

**T14.3 · BL-14 — `frente1_excede_pop` compara com `N_nominal`** em vez de `N_efetivo`
(`src/experiment.m:2419`; erra 2/25 no moead E no nsga3). Fix: 1 token. Controle negativo:
célula com N_efetivo<N_nominal onde a flag antiga dá false e a verdade é true (DTLZ1/DTLZ3).

**T14.4 · BL-17 — o gate G-7 não cobre a linha dos pisos** no `contrato_61.json`
(`ideal`/`nadir_pop`/`nadir_front1` fora da vigilância — mutante removeu os 3 e os portões
seguiram verdes). Fix: 1 linha no artefato, replicada nos 4 pisos. Controle negativo: o
próprio mutante (remover `ideal` de um ⑥ de smoke ⇒ G-7 REPROVA agora).

## §3 · OS RÓTULOS

**T14.5 · BL-12 — números de calibração stale** na `sigma_dict.REGRA_DO_ROTULO` do b4
(`src/experiment.m`, bloco b4): substituir 65,5%/0,350/0,716 pelos MEDIDOS, citando o corpus
(28,43%/0,5743/0,5065 na régua do smoke; 8,32%/0,9035/0,6646 na s42 — conferir no
`f5/t11/relatorios_config/b4.md` antes de gravar).
**T14.6 · BL-13 — string `geracoes_derivadas` dos 4 pisos** (`src/experiment.m:2516-2527`):
ramificar por família de operador (a fórmula única deixa `k` ilegal em 5/25 do moead).
**T14.7 · BL-18 — `espaco_modelo` NULL** nas linhas de busca da ③ do e103
(`src/e103_instrument.m`): 1 literal (`'cru'`), coerente com as linhas de sonda.
**T14.8 · BL-20 — `nota_potencia_de_2` do sobol_batch** (`src/sobol_batch.py:226-228`):
f-string com o `q` real.
**T14.9 · BL-19 — doc do p0/p1 do b4**: CONTRATO §6.1 (linha ~321) + SPEC :803/:1875
(nomes NATIVOS; **NUNCA inverter valores** — trocar move a acurácia 0,35↔0,995) + regen bundle.
**T14.10 · B3 + comentário do `jsonl_open`**: fechar a exceção do writer MATLAB recomendada
no repasse (`handoff/T12-T13-REPASSE-TORRE.md` §12 item 6) e corrigir o comentário que
descreve arquitetura inexistente (item 8). Se o B3 exigir MATLAB engine indisponível, deixar
teste escrito + ⚠ para o autor.

## §4 · A OPERAÇÃO

**T14.11 · Mapa semente→máquina balanceado por custo.** Gerar os DOIS mapas (MATLAB em 7
máquinas; Python em 9) balanceando pela projeção de custo medida (`f5/tempo_f52d.csv` /
heatmap ×30), como artefato `claude_code_context/artifacts/mapa_sementes.json` consumido pelo
`lote3s.sh` (`LOTE_SEEDS` derivado de `LOTE_MAQ`). Critério: minimizar o wall da máquina mais
carregada; e103/env_b5/env_c311 respeitam as restrições de env por máquina (`envs.json`
`venvs_aceitos`). Teste: soma das células dos mapas = grid completo, sem interseção, e o
desbalanceamento máximo ≤10%.

## §5 · CHECKLIST (atualizar aqui)

- [x] T14.1 · BL-11 tempo_checkpoint_s próprio + desconto (8 runners + CONTRATO §17.6) — `7ecc0d5`
      ⚠ **o cartão errava a premissa:** só o `treed_media` inflava; nos outros 7 o I/O caía no vão
      ENTRE gerações (fora do `tempo_geracao_s`, mas SEM NOME). Controle negativo em célula real:
      `tempo_busca_s` 3,2089 (ckpt OFF) × 3,2798 (cadência 1) = +2,2%; antes seria +85,2%.
- [x] T14.2 · BL-21 footer_fechado() no progress + varredura do padrão [-1] — `2fc3e78`
      3 sítios: progress ✔ · accept:796 ✔ · export `footer_ts` era CÓDIGO MORTO ⇒ removido.
      Errata do docstring RE-MEDIDA: 559→747 (94 pares × 2 linhas), não 747→767.
- [x] T14.3 · BL-14 N_efetivo (moead+nsga3) — `73391b1`
      Controle = o corpus da s42 (112 células): a flag antiga erra exatamente 4 e reproduz
      `|F1| > N_nominal` em 112/112. A/B em MATLAB real: `n_frente1` idêntico, flag corrigida.
- [x] T14.4 · BL-17 linha dos pisos no contrato_61.json (+mutante como controle) — `3b101cd`
      Mutante reproduzido: antes VERDE com "⑥ 3/3 campos", agora REPROVA. Raiz fechada
      (os 3 nomes em CRASE no §6.1). Corpus: 1.840/1.840 eventos com os 3 ⇒ sem falso-vermelho.
- [x] T14.5 · BL-12 calibração do b4 re-medida — `decebe2`
      ⚠ **errata do cartão:** o AUC do smoke é **0,5075**, não 0,5065 (re-medido das baterias;
      o 0,5065 do §E1 é o outlier). Também caiu a frase falsa "elas medem outra coisa" (em M=2,
      19/25 células, as duas leituras são idênticas). Célula b4 REAL prova a string no ⑤.
- [x] T14.6 · BL-13 string dos pisos ramificada — `c1ed7e4`
      103/112 → **110/112** (medido). ⚠ **o bloqueador estava errado:** o `+1` que ele prescreve
      para o moead acerta **0/28** (sem ele, 28/28), e o "erra +1 em 28/28" do smsemoa não
      reproduz (lá os dois denominadores coincidem, N_ef=20 sempre).
- [x] T14.7 · BL-18 espaco_modelo do e103 **e do c217** — `1dc9f9e`
      Medido: só e103 e c217 têm a assimetria INTRA-run; o c262 é uniforme-NULL ⇒ não é
      defeito pelo critério do próprio BL-18 (e declara o espaço no `sigma_dict`). Ficou fora.
- [x] T14.8 · BL-20 f-string do sobol_batch — `1dc9f9e`
      A nota é conferida contra o comportamento REAL do scipy (avisa só se q não é potência de 2).
- [ ] T14.9 · BL-19 doc p0/p1 + regen bundle
- [ ] T14.10 · B3 + comentário jsonl_open
- [ ] T14.11 · mapa_sementes.json balanceado (2 mapas, ≤10% desbalanceamento)
- [ ] REGISTRO A44 + handoff/T14-FINAL.md

## §6 · DEFINIÇÃO DE PRONTO

Suíte ≥688 + novos, **0 falhas** · staleness 0 · controles negativos demonstrados (T14.1/2/3/4)
· bundle do b4 regenerado · mapa validado (cobertura total, interseção vazia) · handoff.
**Depois do T14: limpeza dos 58 forasteiros (autor) → tag final (autor) → fila D10 → DISPARO.**
