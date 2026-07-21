# DI09-retrofit-R1-cont — RELATÓRIO DE EXECUÇÃO (a narrativa do processo)

> Companheiro do `handoff/DI09-retrofit-R1-cont.md` (o QUE foi entregue); aqui é o COMO,
> na ordem em que aconteceu, com os desvios e o que cada um custou. 2026-07-19 → 21.

## Fase 0 — arranque (na ordem do cartão)
1. **Gate D81**: ponte→6, R2025a U1, venv pyarrow 25 ✓ (nenhum bloqueio).
2. **PASSO 0**: receita §4 do handoff anterior + CONTRATO inteiro + DI-12/DI-13 + SPEC
   (grep §17.2.2/S.7.1/§17.6) + handoffs R1-<alg> dos 11.
3. **Validadores reconstruídos** (a sessão anterior os deixou no scratchpad):
   `naoperturbacao.py` (① bit-a-bit por BYTES) e `auditar.py` (ordem do artefato conferida
   linha a linha, contagens, ④, manifesto, DI-10). **Auto-testados contra o c141** (já verde)
   antes de qualquer confiança neles.
4. **Experimento de CONTROLE**: b1/b4/b3 MMF1 re-rodados com o código intocado → 3 ① idênticas
   ⇒ o harness reproduz as baselines; qualquer divergência futura seria minha.

## Fase 1 — recon e decisões (multi-agente, antes de codar)
- **Recon 16 agentes** (8 recon + 8 verificação adversarial) sobre os 11 configs: ponto de
  hook exato (pós-fit/pré-decisão/pré-RNG/pré-Evaluation) por arquivo:linha, semântica §3.2,
  ftm, riscos. A verificação adversarial corrigiu números de linha errados (+10 no c238, −9 no
  b3) e refutou afirmações ("bit-equivalente" sem prova → "algebricamente equivalente").
- **Triagem das 112 divergências** → 7 bloqueios D81 reais + 35 vetáveis (resolvidas com o
  contrato) + implementação + informativos.
- **7 perguntas ao autor** (2 rodadas) → DI-19.1..19.7. Depois +1 (espaco_modelo) → DI-19.8.

## Fase 2 — infra transversal (1 janela sem MATLAB, batelada)
`geracao` NULLABLE (adendo da torre) · `g_armado` · S por regime · `probeOffline` · docstring
do SondaState · stub +3 regressões. **Bit-neutralidade PROVADA re-rodando c217/c141/b1/b4
MMF1** (4 ① idênticas; `geracao` seguiu int32/0-nulls nos online). O teste do stub pegou meu
próprio erro de contabilidade na 1ª versão (baseline errado nos flags) — corrigido o TESTE,
com os 8 flags verdes na 2ª execução.

## Fase 3 — os 11 configs (ordem do cartão; 3 gates cada; commit por config)
| ordem | config | 1ª auditoria | ação |
|---|---|---|---|
| 1 | b1 | ✅ de primeira | — |
| 2 | b4 | ✅ de primeira | (+fix n_acumulado, pendente R-1) |
| 3 | b3 | ✅ de primeira | — |
| 4 | pisos | ⚠ 2 "erros" DO VALIDADOR | contrato = ③ VAZIA com schema (não ausente); corrigido o validador após conferir o handoff R1-pisos |
| 5 | c238 | ❌ `eim_mediana_pool` faltando | instrument corrigido; **run morto e re-executado do zero** |
| 6 | e7 | ❌ `tempo_busca_s`+`n_clusters` | busca é separável (tic/toc novo); n_clusters=|PopNew| sem patch; re-run completo |
| 7 | e74 | ❌ 2 campos; depois ❌ semântica | 1º re-run: campos; 2º re-run: `k_local_efetivo` gravava |x_train| (≠k_local) — pego por CONFERÊNCIA DE VALOR (100≠20) |
| 8 | e103 | ⚠ 2 "erros" DO VALIDADOR | T-8 (④ agregada) e DI-19.3 (③ filtrada, não ②); validador corrigido COM regressão do caminho online |

**Padrão que se consolidou:** auditoria reprova → decidir PRIMEIRO se o errado é o dado ou o
validador (conferindo handoff/decisão) → se dado, corrigir instrument e **re-executar o run
inteiro** (nunca remendar: o MATLAB recarrega função editada no meio e o jsonl sai
inconsistente) → re-validar os 3 gates.

## Fase 4 — dívidas da auditoria DI-20 da torre (chegou no meio da sessão)
- **DI-20.6#1**: DI-19.8 estava incompleta (1,05M linhas 'nativo' em c141/c217 DTLZ2+ZDT1) →
  6 re-runs, 0 'nativo' restante, ① idênticas.
- **DI-20.6#2**: `run_c217` nunca gravou `man.sigma_dict` → adicionado (DEF-C4) + re-run.
- **Falso bloqueio meu, corrigido**: "pytest ausente" — a suíte é **unittest** (228 OK).

## Fase 5 — encerramento
- Re-lacre `preflight --write` (e103/e74/c238 trees) — âncoras todas APLICADO.
- **Regressão total**: 14 runs MATLAB ×MMF1 (14/14 ok) + F0×4 + 13× accept + 13× não-pert +
  preflight + suíte 228 → **VERDE**.
- Handoff final + este relatório + memória da torre atualizada.

## Números da sessão
- **Commits**: 9 (`f1ef8b8`→`fd4a9c1`), todos com ritual (add explícito + verificação).
- **Runs MATLAB executados**: ~60 (26 de produção validada + controles + re-runs + regressão).
- **Provas de não-perturbação: 40+, 0 falhas** — inclusive o e7 (MC-dropout, ~1,4e7
  draws/bloco), que era o teste de fogo do invariante I1.
- **Subagentes**: ~30 (recon 16 + sondas 10 + wiring 8) + triagem; TODO output de agente foi
  verificado adversarialmente e 2 defeitos que os GATES NÃO pegariam foram corrigidos antes
  de rodar (e74 no-op silencioso do isstruct; e103 probeOffline×geracao=1).

## Lições novas (além das do handoff §7)
1. **zsh não faz word-splitting** em `$var` — o 1º loop de gates deu "0/23 verdes" FALSO;
   refeito em Python. Loops de validação: sempre Python.
2. **`git commit` sem `cd` absoluto** falha silencioso no runner de fundo (cwd não persiste).
3. **Dois MATLABs simultâneos contaminariam a ④** — a serialização foi deliberada (os tempos
   são dado da dissertação), não lentidão acidental.
4. **Conferir VALOR, não presença**: `k_local_efetivo=100` passava no teste de presença; só a
   aritmética (min(20,|Arc|)=20) denunciou a grandeza errada.
