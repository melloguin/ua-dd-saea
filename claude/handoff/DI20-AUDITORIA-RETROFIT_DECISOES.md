# DI-20 · Auditoria do retrofit DI-09 — as 21 decisões em aberto para o AUTOR

> **De:** a torre (Claude central). **Data:** 2026-07-20.
> **Base:** workflow adversarial de 90 agentes (10 lentes + refutação cética) sobre código, dados,
> docs e gates. 43 achados sobreviveram à refutação. Varredura de TODOS os handoffs/REGISTRO/SPEC/
> CONTRATO/cards: 31 pendências documentadas, **24 já resolvidas**, **21 vivas** (abaixo).
> **Regra:** nenhuma decisão de fidelidade a torre decide sozinha (D97/D81). As recomendações são
> insumo, não escolha.

**Legenda de classe:** 🅕 fidelidade (só o autor) · 🅒 contrato de dados · 🅘 infra · 🅓 doc-sync (a
torre resolve, listada para ciência).

---

## BLOCO 1 — OS 4 QUE BLOQUEIAM A M8 (decidir antes da bateria)

### D-03 🅘 · `is_run_done` bucket-aware — *o mais caro do levantamento*
`manifest.py:168` exige as 4 camadas locais; `gcs.py:150` faz `os.remove` da ③ dos bucket-only após o
upload (D58, deliberado). Na VM com `enable_bucket=True`, todo run completo de **c154/c122/e81/c149/c262**
(os 5 mais caros; c154/DTLZ2=14h37; 3.750 runs) fica "não pronto" **para sempre** → re-execução infinita.
A D58 já prometia "resume dos bucket-only LISTA O BUCKET" — o código nunca foi escrito.
**Rec:** (a) aceitar `gcs.blob_exists(...)` como prova para camadas bucket-only + teste que rode
`is_run_done` com a ③ removida e blob mockado. **~15 linhas.** Não morde no Mac (sem bucket).

### D-06 🅘 · `experiments.py` deve repassar `data_root`/`enable_bucket` ao runner
`experiments.py:97` chama `_adapter.run(alg, problema, semente, exp=exp)` — sem os kwargs que
`experiment.run` aceita. Efeitos: sob `--data-root` a mescla DI-13.1 falha (procura o manifesto no
root errado, regrava o toco com 3 timings None — o defeito que a DI-13.1 tentou matar volta por outra
porta); e o manifesto carimba um `paths.bucket` que nunca recebeu nada.
**Rec:** (a) repassar os dois kwargs + só carimbar `paths.bucket` quando o upload confirmar. **~2 linhas
+ 1 condicional + teste.** Um manifesto que mente sobre persistência é pior que um que se cala (VM efêmera).

### D-01 🅒 · a ④ do piso pode ter `n_acumulado` NULL?
`export.py` declara `n_acumulado` `nullable=False`; os pisos não treinam → gravam NULL. Hoje latente
(o gate R1 não checa schema); **medido:** `cast(timing_schema())` levanta ValueError e
`concat_tables([piso, b1])` levanta ArrowInvalid → a consolidação da ④ não roda. É o irmão exato da
DI-13.2 (`tempo_fit_s` NULLABLE), resolvida para uma coluna e não para a de ao lado.
**Rec:** (a) `nullable=True` + `opt("n_acumulado")` no writer, espelhando a DI-13.2. **2 linhas + 1
regressão.** (Decidir junto o dtype — ver D-02.)

### D-12 🅘 · a camada ⑦ deve entrar no `is_run_done` e na rota de upload?
`is_run_done` itera `naming.LAYERS`, que **exclui** `final`; `gcs.plan_targets:68` idem, embora
`naming.py:57` já defina `OPTIONAL_LAYERS` sem uso. Um run offline SEM a ⑦ conta como pronto e a
esteira não a gera; e a ⑦ sobe por rota paralela improvisada. A ⑦ guarda **a única avaliação real do
ND final do offline** — e a VM que a segura é destruída. Perda silenciosa e irrecuperável.
**Rec:** (b) resume cobra a ⑦ nos 5 offline (1 condicional) + `plan_targets(optional_layers=())`
(1 função). **~20 linhas**, a infra de nomes já existe.

---

## BLOCO 2 — FIDELIDADE (só o autor decide — D97)

### D-04 🅕 · ratificar o `n_acumulado` do b4 (arquivo → treino), como já se fez no c217?
Os dois subamostram o treino e gravavam `|Arc|` contra a §17.6 ("nº de pontos reais no TREINO"). O
c217 foi ratificado na DI-13.10; o fix do b4 veio DEPOIS (76fbbd7), então não está coberto. Ratificar
um só deixa a curva de escalabilidade inconsistente entre os dois. Muda a ④ vs baseline, **não** a ①
(gate bit-a-bit passou). **Rec:** (a) ratificar em bloco; `arc_size` no jsonl preserva o tamanho do arquivo.

### D-11 🅕 · a cadência da sonda do e74: um `SondaState` POR CABEÇA (código) ou k=1 único?
`e74_sonda.m:27` ainda carrega `🟡 PENDENTE DE RATIFICAÇÃO`. O `g` do hook bumpa 4×/ciclo → sob 1
estado com k=2 a **s2 (RBF global) NUNCA dispara**. **Rec:** (iii) um estado por cabeça = o que está
em código (o arquivo aceita ambos; mudar não exige reescrever). **Nenhum run do e74 rodou com sonda —
decisão livre.** Atenção ao volume (até 4 blocos/ciclo; ZDT1 pode explodir).

### D-20 🅕 · a contingência do c149 (DEF-N4) — reconstruir o loop ou dropar?
O c149 é o único BNN do estudo; sua saída derruba junto o sub-estudo batch e encolhe a medição
DISC-ENS/NN. "Reconstruir o loop" (HVI-greedy, D96) é o **maior risco de fidelidade do R3**. **Rec:**
(c) **timebox explícito, decidido ANTES do M7** (o portão). Descobrir isso durante a M8 é o pior mundo.

---

## BLOCO 3 — CONTRATO DE DADOS

### D-02 🅒 · a regra 2 do R4 (tolerar int32 e double+NaN) vale só p/ `real_solution_id` ou vira geral?
A varredura dos 58 parquets mostra a dicotomia em **≥13 colunas, 4 camadas**: `large_string×string` em
todo texto, `int32×double` em `n_acumulado`/`fe_treino_max`/`real_solution_id`. **Rec:** (a) generalizar
por CLASSE no CONTRATO **+** (b) uma função `normalize_schema(table)` obrigatória na entrada da
consolidação (o dado no disco fica como está). (b) é o que de fato destrava a M8 — **~30 linhas + teste**.

### D-08 🅒 · `dist_min_arquivo` e `modelo_hp` existem no regime OFFLINE?
Pressupõem infill guiado por modelo, que o offline não tem. Afeta e103 + os 4 offline do R3
(b5r/b5m/c311/piso-off, ainda não implementados). **Rec:** (a) NULL com exceção declarada na S.7.1 +
(c) o config declara no `sigma_dict` o que fez. Barato agora; caro depois que os 4 rodarem.

### D-09 🅒 · o e103 preenche `tempo_fit_s`/`tempo_busca_s` por geração ou só no agregado?
Treino ÚNICO (offline). Preencher por geração muda a ④ de 1→99 linhas e exige patch no stock + re-lacre.
**Rec:** (a) **1 linha** (o retreino único) + declarar a exceção — a ④ é a série por RETREINO e o e103
tem exatamente um. A curva de busca por geração cabe no jsonl sem tocar o stock.

### D-10 🅒 · rodar o backfill derivado no c262/ZDT1 (timing de um run de ~4h, sem re-executar)?
④ completa mas `tempo_busca_s` NULL; o jsonl do c262 nunca logou busca por iteração → só derivável de
`ts`, tudo rotulado (`timing_backfill`, já ratificado na DI-13.10). **Rec:** (b) rodar, **SE** o custo
do ZDT1 (D=30, ancora a curva de escalabilidade) entrar no R4. 1 comando × 4h de re-execução.

### D-19det 🅒 · fechar as 4 pendências de redação do cartão R3-c122
DI-16.3, perna (ii) da DI-16.2, o "float64 universal" do N.1.1, e o cache-hit×arquivo. **Rec:** fechar
(1)(2) como doc-sync; (3) generalizar N.1.1 para "o dtype que o repo do autor exige, registrado no
manifesto"; (4) **ratificar antes do c149/e81** (a ordem R3 é c122→b5→c311→c149→e81, há folga).

### (novo) 🅒 · re-rodar c141/c217 (DTLZ2+ZDT1) para gravar `"cru"` no lugar de `"nativo"`?
Achado DI-20/A8: **1.050.000 linhas** fora do enum (a DI-19.8 só re-rodou o MMF1). Exige MATLAB.
**Rec:** rodar junto do fechamento dos 4 configs (D-05) OU deixar a normalização de schema (D-02b)
absorver — mas o writer MATLAB não valida, então sem D-02b estoura na consolidação. **Decidir com D-02.**

### (novo) 🅒 · fazer o `run_c217` gravar `sigma_dict`?
c217 tem `sigma_dict=null` nos 3 manifestos (viola DEF-C4/regra 3 — torna a ③ "leitura proibida").
**Rec:** adicionar o `sigma_dict` no `run_c217` + re-rodar (segundos no MMF1; DTLZ2/ZDT1 junto de D-05).

---

## BLOCO 4 — INFRA / ESCOPO

### D-05 🅘 · autorizar o fechamento dos 4 MATLAB restantes (c238, e7, e74, e103) — com qual escopo?
`<alg>_sonda.m` escrito e revisado, **não ligado**; ③ com `fe_treino_max` 100% NULL, 0 sonda. 4 dos 21
configs sem a régua canônica que o DI-09 inteiro existe para prover. **Rec:** (a) fechar com
**MMF1+DTLZ2** (o piloto não precisa do ZDT1: prova não-perturbação + mecânica, que MMF1+DTLZ2 já dão;
custo do ZDT1: c238 3h55, e7 72min). ⚠ o e103 exige patch em `IBEAMS.m:67` → re-lacre por
`preflight.py --write` → janela sem outra sessão MATLAB. **3–5h de wall.**

### D-07 🅘 · o aborto por teto deve gravar manifesto `failed`? (item (a) da DI-13.3, agendado p/ M7)
Hoje `write_run_outputs` não roda no aborto (mantém-o limpo) e nenhum `failed` é gravado; com artefatos
de execução anterior no disco, `is_run_done` leria o run como pronto. **Rec:** (a) gravar `failed` no
caminho de aborto, replicando o padrão que o **c122 já implementou e provou**. + (c) `is_run_done`
cruzar footer do jsonl com o manifesto (rede adicional barata).

### D-16 🅘 · o despachante M8 precisa desligar o kernel fusionado explicitamente (DI-05)?
`grep fused experiments.py` = nada. Risco baixo (os runners chamam `disable_fused_kernel()` no
arranque), mas depende da ordem de importação. **Rec:** (a) chamar no despachante (1 linha) + (c)
preferir VM sem toolchain C++ (a SPEC:2764 já sugere). Registrar `fused_kernel` no manifesto (c262 já faz).

### D-17 🅘 · endurecer o check de RNG do R2-00 (prova mecânica + sentinela de versão do pymoo)
Ratificado em bloco na DI-13, execução distribuída ao M7, **não feito**. "Hoje aquele check não pode
ficar vermelho" = decoração. **Rec:** (a) aplicar o mesmo endurecimento que o R3-00 já escreveu (molde
pronto). Cartão M7.

### D-18 🅘 · extrair `load_sonda` para módulo torch-livre (hoje duplicado standalone×botorch)?
Duplicação necessária hoje (envelopes de dependência distintos), protegida por teste de equivalência.
**Rec:** (b) manter por ora; reavaliar no M7 se aparecer uma 3ª cópia. Editar `botorch_harness.py` é
faixa sensível.

### D-15 🅘 · teste Python para o `geracao` NULL (hoje só no config `stub` MATLAB)?
**Rec:** (c) um teste de contrato amplo que varra `data/experiments/*/*/*.parquet` e confira cada
schema contra `export.*_schema()` — resolve D-15, D-01, D-02 e o `nativo` de uma vez. É o script desta
auditoria virado teste; teria pego os 3 antes. **~40 linhas.**

---

## BLOCO 5 — DOC-SYNC (a torre resolve; listado para ciência)

### D-13 🅓 · colisão de numeração DI-17 — **JÁ RESOLVIDO nesta passada**
Renumeração DI-17.x → DI-19.x em 9 `.m` + handoff (40 citações). Registrado em DI-19. Regra nova: quem
abre um `DI-N` reserva o número no REGISTRO antes de citá-lo no código.

### D-14 🅓 · 5 doc-syncs normativos (3 são contradições ATIVAS texto×código)
(i) `tempo_geracao_s` "wall TOTAL" → **EXCLUI sonda** — **JÁ CORRIGIDO** (CONTRATO §4). (iii) §3.1
"2000 linhas" → **ONLINE 2000/OFFLINE 20.000** — **JÁ CORRIGIDO**. **(ii) FALTA e é prioritária:** a
fórmula da cadência `g=1,2,4,6` **não está em nenhum texto normativo** — a ambiguidade que gerou a
divergência cross-stack segue viva para os **6 configs R3 que faltam** (b5r/b5m/c311/c149/e81/piso-off).
Cravar na SPEC §17.2.2 + CONTRATO §3.1 antes de esses cartões rodarem. + a doc-sync da DI-19.4
(`dist_min_arquivo` nativo na §S.7.1).

### D-21 🅓 · sincronizar `cards/INDEX.md` (R3-c122 → ✅) e a "Agenda" do REGISTRO
O INDEX é a fonte que o PROMPT_MESTRE usa; com c122 em ⬜ uma sessão nova pode reimplementar um runner
de 900 linhas que já passa. A Agenda (linhas 891-923) lista como pendentes itens já resolvidos.
**Rec:** (a) sincronizar os dois. (c122 fechou os 3 problemas — commit 29e8539.)
