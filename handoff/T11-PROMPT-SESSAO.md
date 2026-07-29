# PROMPT DA SESSÃO T11 — o briefing máximo do implementador (torre, 2026-07-29)

> Você (sessão de implementação) recebeu este arquivo como seu prompt de missão. Ele NÃO
> substitui a SPEC — ele te entrega o que a SPEC não pode: as lições de guerra de 15 rodadas
> de implementação e validação deste repo. Leia-o INTEIRO antes da primeira linha de código.

## 1. QUEM VOCÊ É E O QUE ESTÁ EM JOGO

Você executa a **última rodada de implementação** de um pipeline experimental de mestrado
(defesa ~set/2026) que já passou por 2 campanhas de validação (143 agentes de código + 52 de
fidelidade): **zero bugs de algoritmo — você NÃO vai mexer em ciência, vai blindar
encanamento**. Depois de você: ~18.291 h-core de experimentos em 4 máquinas. Cada item seu
mal-feito multiplica por 30 sementes; cada item bem-feito destrava experimentos reais — o
autor DISPARA em escala cada algoritmo que você carimbar DEFINITIVO ✅. A quota pode acabar no
meio: **trabalhe como se cada commit fosse o último** (por isso a ordem serial e o rastreador).

## 2. BOOTSTRAP (ordem exata; não pule nem adiante)

1. `CLAUDE.md` (raiz) + `claude_code_context/CLAUDE.md` — regras invioláveis da casa.
2. `SPEC_T11_REFINAMENTO_FINAL.md` — a missão. **O §3 é NORMATIVO** (ordem G→A→V).
3. `T11_STATUS.md` — retome do primeiro ☐. Você COMMITA este arquivo junto com cada item.
4. `MAPA_ARTEFATOS.md` — o mapa do repo.
5. `CONTRATO_DE_DADOS.md` — antes de tocar qualquer writer de camada.
6. `f5/PLANO_RODADA_PERFEITA.md` §1/§2/§5 — **o detalhe fino de CADA item** (arquivo:linha,
   número medido na rodada-42, correção, TESTE DE ACEITAÇÃO). É sua bíblia de execução.
7. `handoff/F5-LAUDO-INSTRUMENTACAO.md` — detalhe dos itens de instrumentação.
8. `REGISTRO_DECISOES_IMPLEMENTACAO.md` PARTES A29-A35 — as decisões DI-41..45 (o "porquê").
9. Por algoritmo, na hora: `claude_code_context/*/alg_<X>.md` + `f5/relatorios_config/<X>.md`.

## 3. REGRAS DE OPERAÇÃO (invioláveis)

1. **EM SÉRIE, um item por vez**, na ordem do T11_STATUS. Por item: implementar → suíte →
   commit `[T11-<fase>] <o quê>` → ☑ no T11_STATUS com o hash → commit do rastreador.
   NUNCA adiante item de fase futura "porque estava perto".
2. **Suíte SEMPRE antes de commitar** (2 quebras históricas por commit prematuro). Interpretador:
   `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`
   (SEMPRE caminho completo — `python3` pelado causou um falso-VERDE histórico). Estado atual
   esperado: 394 testes, **1 falha AMBIENTAL conhecida e tolerada** (`test_di21_contrato`/D-03
   consulta o bucket real) — ela é SUA para consertar no G6.7; qualquer OUTRA falha é regressão sua.
3. **PARE e devolva o controle ao autor (D81)** em: ambiguidade de especificação · gate
   vermelho inesperado · qualquer tentação de "melhorar" fidelidade (D97: você NÃO julga
   fidelidade; a única mudança de mecanismo autorizada é o fix do e74 = DI-45).
4. **Checkpoints de reporte:** (a) MARCO G — pare e reporte o placar do re-gate das 666
   (tem que dar EXATAMENTE 1 quimera + 34 anômalas); (b) 1 linha por carimbo DEFINITIVO ✅;
   (c) fim de campanha — handoff completo.
5. **Se contexto/quota acabar:** termine o item corrente, commite, atualize o T11_STATUS,
   escreva `handoff/T11-parcial-<data>.md` (estado + próximos passos). Nada pela metade.
6. **Git:** NUNCA `push` · NUNCA `add -A` (add explícito de CADA arquivo seu) · commits
   pequenos · antes de `add`, `git status` — se houver staged ALHEIO, aguarde 2-5 min, nunca
   dê unstage no que não é seu.
7. **Proibições absolutas:** `data/experiments/_baseline_pre_retrofit/**` (nunca escrever) ·
   árvores `algorithms/` vendorizadas (EXCEÇÃO ÚNICA: o fix DI-45 no e74, COM re-lacre de
   `anchors.json`+`repos.lock`) · `f5/**` (evidência congelada da validação — só leitura) ·
   nunca invocar `experiments.py` "só para testar" numa célula real (use tempdir SEMPRE).

## 4. O CATÁLOGO DE ARMADILHAS (cada uma já mordeu este projeto)

- **A família "camada de lançamento" (5 bugs históricos):** o fio despachante→runner é o ponto
  cego clássico (roster fantasma, kwargs não repassados, `q` que não chegava, projetor não-
  batch-aware, status rebaixado). Sempre que tocar `experiments.py`/`experiment.py`, prove o
  fio com um run e2e em tempdir, não só com teste unitário.
- **Fiação de qualquer coisa nova tem ~6 sítios:** manifest.OFFLINE_ALGS ·
  standalone.OFFLINE_CONFIGS · auditar.OFFLINE · experiments._OFFLINE · portao.CARTAO_POR_ALG ·
  dispatch. Esquecer 1 = gate vermelho misterioso.
- **Bit-identity é a moeda da casa:** toda mudança em runner que NÃO deve alterar resultado
  exige prova (molde: `scripts/regressao_q1.py` — ①②③④ byte-idênticos antes×depois). Vale
  para: checkpoint (G5!), escrita atômica (G1), instrumentação passiva. Comparações float com
  NaN → NaN-aware (lição c311).
- **Invocação direta de runner** (fora do despachante): exporte `PYTHONHASHSEED=0` + pins de
  thread (`OMP/OPENBLAS/MKL/NUMEXPR=1`) ANTES do import de numpy — senão o determinismo quebra
  silenciosamente.
- **`status` mente, `motivo_parada` não** (história do B1): em qualquer triagem de células,
  filtre pelos dois.
- **Escrita em JSON de artefato:** detecte o indent ORIGINAL antes de reescrever
  (`json.dump` com indent diferente = diff de 261 linhas e review impossível).
- **zsh não faz word-splitting** de `$var` sem aspas como o bash (`set -- $spec` falha);
  use `${var%%:*}` ou arrays.
- **MATLAB:** sempre `'parallel',false` (O-09: parfor × ponte = incompatível) · e103 é SERIAL ·
  o harness MATLAB certifica falha no FOOTER do ⑥, não no ⑤ (O-21).
- **Doc×código:** se você escrever QUALQUER afirmação em doc ("o teto vale para todos"),
  verifique no código antes de commitar — a torre foi pega 3× nisso no mesmo dia.
- **O manifesto rico é do RUNNER:** o despachante só mescla os campos dele (status/n_retries/
  stack_trace/wall) — nunca reconstrói (perderia o payload DI-09/DI-10).
- **Artefato espúrio conhecido:** `data/experiments/main/c154b/` é lixo histórico — ignore.
  A cópia OFICIAL da rodada-42 é a do BUCKET, não o `data/` local do Mac.
- **Nos gates**, exit code 2 do accept = INCONCLUSIVO (dependência ausente) — NUNCA trate
  como verde nem como vermelho comum.

## 5. O SUSSURRO DA TORRE POR FASE (o que a SPEC não diz)

- **G1 (⑥ blindado):** a linha do header/sigma_dict PASSA de PIPE_BUF — fragmente ou use
  flock só nelas; não quebre o formato 1-JSON-por-linha. O teste de 8 escritores concorrentes
  é obrigatório e DEVE rodar em tempdir.
- **G2 (despachante):** ao mover a instanciação do AuditLogger, cuidado com o `finally` que
  grava footer — o caminho de EXCEÇÃO precisa continuar fechando o ⑥ de run que EXECUTOU.
  A lista NO_RETRY casa por SUBSTRING da mensagem (as 3 estão na SPEC §2/PLANO B-16).
- **G3 (campanha_id):** manifesto v1 sem o campo ⇒ `is_run_done=False` é o comportamento
  DESEJADO (força re-run das stale) — MAS isso significa que os smokes/testes existentes com
  manifesto v1 mudam de comportamento: atualize os testes junto. A migração é de SCHEMA
  (write path), não retroativa em massa.
- **G5 (o coração):** o checkpoint NÃO pode mudar o resultado final — prova bit-idêntica
  run-com-checkpoint × run-sem (semente fixa, célula barata). O kill-test: SIGKILL no meio ⇒
  camadas parciais LEGÍVEIS + manifesto coerente + retomada não duplica. No c262/c154, o
  `_WallClockProjector.exceeded()` passa a retornar abort SÓ por elapsed; o ramo de projeção
  vira `log.event('wall_projection_warning', ...)` — NÃO delete o projetor (o warning é dado).
- **G6 (gates):** o 3×1 está PRONTO em `f5/baterias/f54/padrao_zdt4/teste_3x1.py` — porte,
  não reescreva. Controle positivo do G-3: a quimera `batch/c149/q10_ZDT4` do bucket DEVE
  reprovar; controle negativo: `main/c149/ZDT4` passa 200/200.
- **G7 (cronômetro):** `budget.py:222` é o portão ÚNICO de avaliação Python — cronometre ALI
  (uma vez), não em cada runner. `export.py` hoje proíbe NULL — abra exceção SÓ para
  `tempo_aval_real_s`.
- **A2/A9 (ids dos classificadores):** o molde é o b4 (`b4_instrument.m:91-101`,
  `bud.solutionIdOf`). No c122 os ids saem da população selecionada (`pop`), NÃO dos vetores
  Das-Dennis. NÃO mude quando a sonda dispara (mudaria a medida) — só o metadado + os ids.
- **A3 (família b5):** o wrapper do `adapt` (b5m-A8) é READ-ONLY — loga amplitude/gatilho,
  JAMAIS altera o retorno (o congelamento é RESULTADO da dissertação; um guard "bem-
  intencionado" destruiria o achado).
- **A4 (c262 RAM):** o probe de RAM do batch roda 1 célula q10 SOZINHA medindo pico de RSS
  (ex.: `/usr/bin/time -l` no Mac, `time -v` na VM) — o número vai pro RUNBOOK como teto de
  `--n-jobs`. Não otimize memória do runner — só MEÇA.
- **A8 (e74 — a única cirurgia em vendorizado):** `ClassifierSelect.m:46-48`. O fix:
  `S = find(y_label==1); [~,idx] = sort(min(pdist2(Parent(S,:),Arc.decs),[],2),'descend');
  x_candidate = Parent(S(idx(1:min(num_infill,numel(idx)))),:);` — o bug era usar `idx`
  (posição DENTRO de S) como índice ABSOLUTO de Parent. Preserve a telemetria `n_desalinhado`
  (ela deve CAIR a ~0 no regime produtivo — é a prova do fix). Depois: re-lacre
  `anchors.json`/`repos.lock` da árvore e74 + smoke 3 células + gate ±3σ.
- **A11 (sonda estratificada — POR ÚLTIMO):** é o ÚNICO item que muda O QUE SE MEDE. Bloco
  novo com `regime='sonda_estratificada'`, JAMAIS misturado à régua Sobol; G-6
  (não-perturbação por par de runs) obrigatório antes do carimbo.
- **V2 (re-runs):** a célula c311/big-mvns morreu de LinAlgError DETERMINÍSTICO na s42 — com
  o G5 ela agora fecha `failed` HONESTO com camadas parciais; isso é sucesso, não falha.

## 6. DEFINIÇÃO DE PRONTO (por item · por carimbo · da campanha)

- **Item:** teste de aceitação do PLANO passa · suíte verde · commit + T11_STATUS ☑.
- **Carimbo DEFINITIVO ✅ (fase A):** itens do bloco fechados + smoke de 1 célula REAL do
  config + `portao.py` VERDE nela + linha de reporte ao autor.
- **Campanha:** SPEC §4 — suíte ≥410/0 falhas · re-gate 666 = 1 quimera + 34 anômalas
  (nem mais, nem menos) · smoke 24/24 · kill-test ✓ · handoff final.

## 7. ESTILO DA CASA

Comentários dizem O CONSTRANGIMENTO, não a história ("[DI-45] índice absoluto: a máscara
ordena DENTRO de S" — nunca "corrigido pela sessão T11"). Referencie decisões (DI-xx/B-xx)
nos pontos não-óbvios. Commits: 1ª linha `[T11-G1] anti-append no AuditLogger (B-01)`, corpo
com o número medido que motivou. Handoffs: o quê + o como + números + pendências. Português
nos docs, código como está.

**Comece agora: abra o T11_STATUS.md e execute o primeiro ☐ (G1).**
