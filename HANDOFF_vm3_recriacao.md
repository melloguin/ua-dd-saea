# HANDOFF — Recriação da `matlab-vm3` (29/07/2026)

**De:** sessão Cowork "torre" (operação multimáquina da campanha `ua-dd-saea`)
**Para:** a sessão que provisionou a `matlab-vm1` hoje de manhã — que assume também a vm3 e sincroniza os dois provisionamentos
**Operador:** Guilherme (PPGCC/UFMG, defesa ~set/2026, GMT-3). Responda em português, comandos prontos para colar, um por vez, nunca com caminho de saída silencioso.
**Corte:** 29/07/2026 ~09:20 BRT — `parte-a` da vm3 nova disparada (ou prestes; conferir §5).

Você já domina o `provisionar_matlab_vm.sh` — você o escreveu e o executou na vm1 hoje. Este documento traz o que você **não** viu: a história e o estado da vm3, as convenções da operação que a vm3 herda, e as decisões já tomadas pela torre que valem para as duas máquinas.

---

## 1. Resumo executivo do dia

A `matlab-vm3` original (us-central1-a, n2-standard-8, disco 1 TB pd-standard) foi **apagada hoje às ~09:10** e **recriada em us-east1-b** como `n2-standard-16` com disco 300 GB pd-balanced. Motivo: a us-central1 está com stockout crônico de N2 (nem `n2-standard-2` sobe, nas 4 zonas), impedindo o upgrade para 16 vCPU que o operador precisa. A decisão de apagar ficou segura depois que a **sua ativação da vm1 provou que a licença é reproduzível** — e a inspeção de hoje provou mais: o licenciamento é **online (por login)**, sem vaga de ativação nenhuma consumida (§3).

Nada de dado se perdeu: a campanha da semente 42 fechou ontem com **censo do bucket zerando `S/BUCKET`** — tudo que a vm3 velha produziu está em `gs://mestrado_experiments`. O que morreu com o disco foi só o ambiente, que o seu script recria em ~1 h.

---

## 2. Ficha técnica da vm3 nova

| item | valor |
|---|---|
| nome | `matlab-vm3` (mesmo nome de propósito — os scripts da operação detectam por hostname) |
| projeto / conta | `project-2aa33d8c-94a7-488b-89e` / `invest.gdmn@gmail.com` |
| zona | **`us-east1-b`** (mesma da vm1, projetos diferentes) |
| tipo | `n2-standard-16` — 16 vCPU, 64 GB |
| disco | **300 GB `pd-balanced`** — escolha deliberada: o `pd-standard` de 1 TB da antiga estrangulava I/O (achado O-19 da operação). Não "melhorar" para 1 TB de novo |
| IP interno | `10.142.0.2`, **reservado como estático** (`matlab-vm3-ip`, us-east1) |
| IP externo | efêmero (34.75.155.153 no boot de hoje — muda a cada start; acesso é sempre via `gcloud compute ssh`) |
| MAC | `42:01:0a:8e:00:02` — **igual ao da vm1**, porque é o mesmo IP em VPCs de projetos diferentes. Identidade de máquina agora é projeto+nome, nunca MAC |
| usuário SSH | **`gmello`** (o default do gcloud). A vm3 antiga usava `invest_gdmn` — **SSH sempre como `matlab-vm3` sem prefixo de usuário**, senão repo e drivers ficam em homes diferentes |
| proteções | `--deletion-protection` ligada desde o create; IP interno estático reservado |
| escopos da SA | `storage-rw, logging-write, monitoring-write` — **sem escopo de Compute**: `gcloud compute ...` de dentro da VM falha com "insufficient authentication scopes". É deliberado; não conserte |

Flags prontas (o operador vai colocar no `~/.zshrc`; a antiga apontava para us-central1-a):

```bash
INV=(--account=invest.gdmn@gmail.com --project=project-2aa33d8c-94a7-488b-89e)
gcloud compute ssh matlab-vm3 "${INV[@]}" --zone=us-east1-b
```

---

## 3. A descoberta que mudou as regras: licenciamento ONLINE

Toda a documentação antiga da operação diz "a licença do MATLAB ancora no MAC 42:01:0a:80:00:05; stop permitido, delete proibido". **Essa regra foi aposentada hoje por evidência:**

1. A sua ativação na vm1 (segunda máquina, outro MAC) funcionou de primeira.
2. O License Center do operador **não tem** "View current activations" — não há ativações a gerenciar.
3. `ls /opt/matlab/R2025a/licenses/` na vm1 mostrou **só `license_info.xml` (140 bytes)** — nenhum `.lic` com host ID.

Conclusão: TAH em **licenciamento online**, ancorado na conta `mello.guilherme@dcc.ufmg.br`, não no hardware. Cada máquina nova só faz login. Não existe teto de ativações a racionar para as "outras VMs" que o operador planeja.

O que **continua** valendo: `delete` é ato deliberado (custa ~1 h de rito de reprovisionamento), então `--deletion-protection` fica ligada em toda máquina MATLAB — ela protege o tempo do operador, não mais a campanha. E o aviso do próprio script ("licença ancora no MAC") merece ser reescrito quando você tocar nele.

**Teste pendente que decide o M8:** com as duas máquinas provisionadas, rodar MATLAB **nas duas ao mesmo tempo** (`matlab -batch "disp(license)" > /tmp/lic.txt 2>&1` em cada uma, simultaneamente). As duas imprimindo licença = paralelismo de duas máquinas MATLAB confirmado. Se o licenciamento online bloquear sessão simultânea do mesmo login, o plano de frota muda — teste barato, faça cedo.

---

## 4. O que foi preservado do mundo antigo

- **Todos os dados**: censo final da semente 42 = 666/695 OK, `S/BUCKET = 0`. Fonte única: `gs://mestrado_experiments` (projeto `skilled-text-480300-d9`, dono `gdmello.nunes@gmail.com`). Inventário autoritativo em `_censo/censo_bucket_42_FINAL.csv`.
- **Snapshot** `vm3-pre-reinicio-20260727` (16,5 GB reais, rotulado `manter=sim`): última cópia fria do sistema da vm3 antiga. Custa centavos/mês; não apagar.
- **Drivers da operação**: `lote3s.sh` e `plano3s.sh` já foram copiados para a home da vm3 nova (`/home/gmello/`) hoje às 09:15. Fontes canônicas em `scripts/` no repo.
- A instância `vm3-resgate` e o disco `vm3-leitura` (artefatos de um resgate antigo) foram apagados ontem. No projeto restam `mestrado-v6` (parada) e agora a vm3 nova.

---

## 5. Estágio atual e o caminho até "provisionada"

**Checkpoint no corte deste documento:** máquina criada e RUNNING; script `provisionar_matlab_vm.sh` copiado para `~/`; drivers copiados; **`parte-a` disparada (ou prestes)**. Confirme com:

```bash
gcloud compute ssh matlab-vm3 "${INV[@]}" --zone=us-east1-b --command='tail -5 ~/parte_a.log 2>/dev/null || echo "parte-a AINDA NAO DISPARADA"'
```

Se não disparou: dentro da VM, `chmod +x ~/provisionar_matlab_vm.sh && nohup ~/provisionar_matlab_vm.sh parte-a > ~/parte_a.log 2>&1 &`.

Depois, o rito que você conhece melhor que ninguém (é o mesmo da vm1, executado hoje):

1. **`licenca`** — interativo, e-mail `mello.guilherme@dcc.ufmg.br`. Na vm3 original a primeira tentativa deu "Licensing shutdown" e a segunda idêntica passou; na vm1 passou de primeira. Se falhar, repetir antes de investigar.
2. **`parte-b`** — portão D80 (5 toolboxes 25.1 contra o lock), ponte InProcess, A2. Na vm1 passou limpo hoje.
3. **Bucket** — aqui há uma **assimetria importante entre as duas máquinas**: a vm3 está no MESMO projeto da antiga, então a service account default (`PROJECT_NUMBER-compute@...` de `project-2aa33d8c`) é a mesma que já escrevia no bucket durante a campanha — o acesso deve funcionar de cara. A **vm1** está em outro projeto (`core-cascade-341902`) e a SA dela **não** tem grant. Teste em cada uma:

```bash
gcloud storage ls gs://mestrado_experiments/experiments/ 2>&1 | head -3
```

   Se a vm1 der 403, o grant é feito pela conta dona do bucket (não de dentro da VM):

```bash
gcloud compute instances describe matlab-vm1 --project=core-cascade-341902 --account=melloguinn@gmail.com --zone=us-east1-b --format="value(serviceAccounts[0].email)"
gcloud storage buckets add-iam-policy-binding gs://mestrado_experiments --member=serviceAccount:SA_AQUI --role=roles/storage.objectAdmin --account=gdmello.nunes@gmail.com --project=skilled-text-480300-d9
```

4. **Gates de aceite (RUNBOOK §6)** antes de qualquer célula sancionada: suíte ≥328 OK, preflight exit 0, três células reais VERDES no `portao.py`, smoke real do harness. Vale para as duas máquinas. É o que separa "provisionada" de "de produção" (disciplina D97: fidelidade não se assume, se demonstra).

**Resposta da torre à pergunta que o próprio parte-b deixa aberta** ("quais das 22 configs rodam aqui"): **vm1 e vm3 são máquinas MATLAB puras.** Nenhuma precisa de `env_main`, `env_e81_qpots`, `env_b5` ou `env_c311` — esses venvs pertencem a v5/v6/Mac. A ponte (`env_bridge`) que o parte-a cria + as árvores PlatEMO que vêm no clone são o suficiente.

---

## 6. Regras vinculantes da operação (valem nas duas VMs, sem exceção)

- **NUNCA `git push`.** `git pull` só após congelamento anunciado pelo autor. NUNCA `git add -A`.
- **NUNCA instalar/atualizar nada** (pip, apt, componentes) fora do que o script de provisionamento faz, sem autorização explícita do operador (D80: os locks são a verdade; divergência ⇒ parar e escalar).
- **Saída de execução sempre por redirecionamento** (`> log 2>&1`), **nunca pipe** — o MathWorksServiceHost trava em pipe. Vale até para `matlab -batch "disp(...)"`.
- **DI-34:** `parfor` quebra a ponte InProcess. Execução é sempre 1 processo MATLAB por célula, `'parallel',false`.
- **O-18:** MATLABs subindo simultaneamente disputam o startup de licenciamento (segfault em `MatlabLicensing::getInstance`, visto com 6). O driver tem `LOTE_MATLAB_JITTER` para isso — com 12 jobs na vm3 nova, usar **20–25 s** (o default 12 foi calibrado para 6 jobs).
- **Ocupação 75% dos núcleos físicos:** vm3 (16 vCPU = 8 físicos... atenção: n2-standard-16 = 16 vCPU = 8 núcleos físicos com SMT; a convenção da operação sempre contou em vCPU/2 nas VMs → **12 jobs** na vm3, **9** na vm1 se 12 vCPU).
- **Bucket é read-write só para experimento** (dual-write do `mirror_run`). Nenhum `rsync` com delete, nenhum `rm` no bucket, nunca.
- **D81:** ambiguidade ou conflito ⇒ pare e pergunte ao operador.
- **Fuso:** logs das VMs em UTC; o operador é GMT-3. Converta sempre ao reportar.

---

## 7. Os drivers da operação (já na home da vm3)

**`lote3s.sh`** — disparador de células: N processos de UMA célula cada via `xargs -P`, contador vivo, pré-filtro por manifesto (célula pronta não entra na grade), multi-semente, ordem híbrida, prazo absoluto. A grade vem SEMPRE de `claude_code_context/artifacts/runs_matrix.csv` — nunca digitada. Variáveis principais: `LOTE=CONFIRMA`, `LOTE_MAQ`, `LOTE_SEEDS`, `LOTE_PARES`, `LOTE_JOBS`, `LOTE_MATLAB_JITTER`, `LOTE_TETO_S`, `CENSO=1` (read-only).

- Na vm3, `LOTE_MAQ=vm3` funciona por detecção de hostname e carrega o perfil com o roster MATLAB. O cabeçalho vai imprimir `python=<ausente>` — **correto**, o roster é 100% MATLAB e o driver só exige venv quando há célula Python.
- **A vm1 não tem perfil** no driver. Para rodar lote nela: `LOTE_PARES="main/e7 ..." LOTE_JOBS=9 LOTE=CONFIRMA bash ~/lote3s.sh` (o `LOTE_PARES` sozinho dispensa `LOTE_MAQ`). Se a frota se consolidar, vale adicionar um perfil `vm1` no case do script — mudança de uma linha, com o operador ciente.

**`plano3s.sh`** — operação por verbo, chamável de fora via `gcloud compute ssh --command`: `censo`, `estado`, `placar`, `parar`, `disparar [horas]`. `parar` mata a árvore inteira na ordem certa (Ctrl-C não alcança os workers — process group separado).

---

## 8. O que vem depois (M8) — para vocês dois planejarem

A próxima campanha são as **29 sementes restantes** (0..28; a 42 está fechada). A fatia MATLAB é 345 células/semente ≈ **41,8 h-core/semente**. Com as duas máquinas:

| config (main, salvo indicação) | h-core/semente |
|---|---|
| c238 | 18,4 |
| e7 | 14,5 |
| b1 | 3,2 |
| b4 | 2,2 |
| e74 | 1,8 |
| b3 | 0,8 |
| c217 | 0,4 |
| c141 | 0,3 |
| off/e103 + 4 sweeps de e103 | ~0,1 |
| nsga2, nsga3, moead, smsemoa | ~0 (só startup) |

**Regra de ouro ao dividir entre vm1 e vm3 (O-16): um config inteiro numa máquina só — dividir por (exp, alg), nunca espalhar os problemas de um config pelas duas.** Capacidade 12:9 jobs sugere ~24:18 h-core (ex.: vm3 = c238 + b1 + e74 + c217 + baselines ≈ 24; vm1 = e7 + b4 + b3 + c141 + e103 ≈ 18), mas a partição final é decisão do operador — inclusive porque `e7` e parte de `c238` da semente 42 rodaram no **Mac** (recuperação de emergência), o que já exige nota de comparabilidade na tabela de tempo.

O gargalo real do M8 **não é MATLAB**: são as 230 células/semente presas aos venvs que só existem no Mac (`env_b5` py3.7 Rosetta, `env_c311` py3.8 Rosetta, `env_e81_qpots`). Se o operador pedir para atacar isso, é outra frente (provisionar esses venvs em Linux x86_64), com pins travados e validação de equivalência — não improvisar.

---

## 9. Mapa da frota (29/07/2026, ~09:20 BRT)

| máquina | projeto/conta | zona | tipo | estado | papel |
|---|---|---|---|---|---|
| **Mac** (M1 Pro) | — | — | 8c/16GB, 4 jobs | ativo | venvs exclusivos (230 cél/sem) + MATLAB local |
| **v5-mestrado** | skilled-text / gdmello.nunes | us-central1-a | e2-32 (Workbench) | TERMINATED | env_main pesado |
| **mestrado-v6** | 2aa33d8c / invest.gdmn | us-central1-a | e2-16 (Workbench) | TERMINATED | env_main |
| **matlab-vm1** | core-cascade / melloguinn | us-east1-b | ≤12 vCPU (quota global 12) | provisionada hoje, licenciada, parte-b OK | MATLAB |
| **matlab-vm3** | 2aa33d8c / invest.gdmn | us-east1-b | n2-standard-16 | criada hoje, parte-a em curso | MATLAB |

Cuidados com as Workbench (v5/v6): `stop`/`start` só **de dentro** (`sudo shutdown -h now`) ou pela API do Notebooks — a API do Compute recusa mutação nelas. E a v5 pertence à conta `gdmello.nunes`, não à `invest.gdmn`.

Para elevar a vm1 além de 12 vCPU um dia: o bloqueio é `CPUS_ALL_REGIONS=12` do projeto core-cascade — pedido de quota no console, não é questão de zona.

---

## 10. Erros já vistos hoje e o que significam (não redescobrir)

| sintoma | significado | ação |
|---|---|---|
| `ZONE_RESOURCE_POOL_EXHAUSTED` | stockout momentâneo da forma na zona | outra zona da mesma região (us-east1-c/d) ou retry; **nunca** trocar de família de CPU para contornar |
| `QUOTA_EXCEEDED` | quota regional/global do projeto | pedido no console; não é capacidade |
| `Request had insufficient authentication scopes` (dentro da VM) | a SA da VM não tem escopo de Compute | esperado; comandos `gcloud compute` rodam do Mac |
| 403 no bucket com "does not have storage.objects.get" | **conta errada**, não falta de permissão | usar a conta dona (`gdmello.nunes`) ou grant na SA; nunca mexer em IAM às cegas |
| "Licensing shutdown" no passo `licenca` | soluço do licenciamento online | rodar de novo, idêntico |
| `zsh: command not found: #` no Mac | comentário colado em zsh interativo | inofensivo |
| arrays (`INV`, `V3`) "unrecognized arguments" vazios | array não definido no terminal novo | redefinir; zsh expande array vazio como argumento vazio |

---

## 11. Se precisar do contexto completo da campanha

No repo (raiz) e no projeto Agente 8: `HANDOFF_operacao_multimaquina.md` (infra + 20 armadilhas de bash/gcloud pagas com tempo real), `FECHAMENTO_semente42.md` (as 666/695 e as 29 não-OK célula a célula), `INVENTARIO_nao_go_semente42.md` (motivos e aprendizados), `TUTORIAL_censo_bucket.md` + `scripts/censo_bucket.py` (censo do bucket, roda de qualquer máquina só com gcloud CLI). O censo é a fonte da verdade; os documentos são a narrativa.

Boa sincronização — a vm1 e a vm3 estão a um `licenca` + `parte-b` + gates de virarem a frota MATLAB de duas máquinas que o M8 pede.
