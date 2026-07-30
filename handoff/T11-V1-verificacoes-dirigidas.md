# T11 · V1 — VERIFICAÇÕES DIRIGIDAS (forense READ-ONLY)

> **Escopo (D13):** SÓ as duas que o autor autorizou — o torneio do b1
> (`EvolALG.m:16`) e o índice do b3 (`UpdataArchive`). **Nada de código foi
> alterado**: a SPEC §3/FASE V manda relatório, e achado 🔴 dispara D81 (parar e
> perguntar). Os dois achados abaixo são 🔴.
> **Data:** 2026-07-30 · **Método:** leitura do vendorizado + medição nos ⑥ da s42.

---

## VD-b1 · o torneio ranqueia um vetor e indexa outro 🔴

### O mecanismo

`ParEGO.m` monta o escalar de Tchebycheff e **corta** a população antes de treinar:

```matlab
PCheby = max(PopObj.*λ,[],2) + 0.05.*sum(PopObj.*λ,2);   % :56
if N > 11*D-1+25
    [~,index] = sort(PCheby);  Next = index(1:11*D-1+25); % :58-59  ← CAP
end
PDec = Population(Next).decs;  PCheby = PCheby(Next);     % :63-64
...
[~,distinct] = unique(round(PCheby*1e6)/1e6);             % :69      ← DEDUP
PCheby = PCheby(distinct);
...
[PopDec,gainfo] = EvolALG(Problem, PCheby, Population.decs, dmodel, IFEs);  % :92
```

Repare no último argumento: o `EvolALG` recebe o **`PCheby` do subconjunto**
(pós-cap e pós-dedup) junto com **`Population.decs` INTEIRO**. Dentro dele:

```matlab
Off = [OperatorGA(Problem, Dec(TournamentSelection(2,size(Dec,1),PCheby),:)); ...]  % :16
```

E o `TournamentSelection`:

```matlab
Parents  = randi(length(varargin{1}), K, N);     % sorteia em [1..|PCheby|]
[~,best] = min(rank(Loc(Parents)),[],1);
index    = Parents(best+(0:N-1)*K);              % índices em [1..|PCheby|]
```

Os índices sorteados vivem em `[1..|PCheby|]` — o tamanho do **subconjunto** — e
são usados como `Dec(index,:)`, isto é, posições da **população inteira**. As
duas listas não são a mesma: o cap ORDENA por PCheby e o dedup REMOVE
duplicatas, então `Dec(i)` e o indivíduo cujo PCheby foi comparado não são o
mesmo indivíduo (exceto por coincidência).

**É a mesma classe do DI-45 do e74** (posição relativa a um subconjunto usada
como índice absoluto), e o comentário do próprio `EvolALG.m:9-10` já a
reconhece: *"o bug do torneio (:16) fica (CODIGO K.3)"*.

### O tamanho do efeito (medido nos 28 ⑥ de `main/b1` da s42)

| | |
|---|---|
| gerações com evento `b1_gen` | **8.443** |
| com `\|PCheby\| < \|Dec\|` (torneio afetado) | **7.850 — 93,0%** |
| fração do `Dec` INALCANÇÁVEL pelo sorteio | **mediana 44,9% · máx 86,5%** |
| células afetadas | **25 de 28** |

Ou seja: em 93% das gerações, **quase metade da população nunca pode ser
sorteada como pai** — e a seleção que acontece é por um valor que pertence a
outro indivíduo.

### Leitura

1. **Não invalida a rodada-42.** O b1 é `ParEGO` e o efeito está no operador de
   variação, não no orçamento nem no export: FE final exato, ①–⑤ íntegras, e o
   segundo termo do `Off` (`OperatorGA(Problem,Dec,{0,0,1,20})`) gera prole a
   partir da população inteira, então a busca não fica presa.
2. **É comportamento do CÓDIGO ORIGINAL** (bloco upstream do PlatEMO), não do
   nosso patch — a bússola **D29** classificaria como 🔴 *bug do código → segue o
   ARTIGO*, o mesmo veredito que produziu a DI-45.
3. **A decisão é do autor**, e é de FIDELIDADE (D97): corrigir muda o
   comportamento do b1 e quebra a comparabilidade s42 × M8, exatamente como no
   e74. Não toquei.

**Opções para a mesa:** (a) documentar como limitação/fidelidade-ao-código e
manter; (b) corrigir como o DI-45 (passar `PCheby` e `PDec` casados ao
`EvolALG`), com re-lacre de âncora e re-validação; (c) corrigir só na M8 e
declarar a descontinuidade.

---

## VD-b3 · o `Next` do `UpdataArchive` mistura dois domínios de índice 🔴 (latente)

### O mecanismo

`UpdataArchive.m`, ramo 1 (`size(Via,1) > NI-mu`):

```matlab
Angle  = acos(1-pdist2(PopObj, Vi, 'cosine'));
[~,associate] = min(Angle,[],2);
Via    = Vi(unique(associate)',:);          % VETORES de referência
Next   = zeros(1, NI-mu);
if size(Via,1) > NI-mu
    [IDX,~] = kmeans(Via, NI-mu);           % clusteriza os VETORES
    for i = unique(IDX)'
        current = find(IDX==i);             % posições em Via
        Next(i) = current(best);            % ← guarda posição de Via
    end
else
    [IDX,~] = kmeans(Total.objs, NI-mu);    % clusteriza as SOLUÇÕES
    ...
    Next(i) = current(best);                % ← guarda posição de Total
end
A1 = [Total(Next(Next~=0)), New];           % ← indexa TOTAL nos dois casos
```

No **ramo 2** (else) o `current` é posição em `Total` e o uso é coerente. No
**ramo 1** o `current` é posição em **`Via`** (vetores de referência) e é usado
para indexar **`Total`** (soluções) — dois domínios diferentes. O arquivo
resultante recebe soluções escolhidas por um índice que não lhes pertence.

### O que os dados dizem

| | |
|---|---|
| ciclos com evento `b3_gen` na s42 | **1.619** |
| `nzero_updata > 0` | **0 / 1.619** |

O `nzero` (clusters vazios) é **sempre 0**, o que confirma que o `kmeans` sempre
preencheu todas as posições — mas **não diz qual ramo rodou**, porque nem
`size(Via,1)` nem `NI-mu` são logados hoje.

### Leitura

1. **Achado ESTRUTURAL, ainda não quantificado.** Diferente do b1, aqui falta a
   medida: sem `size(Via,1)` e `NI−mu` no ⑥ não dá para dizer em quantos ciclos
   o ramo 1 rodou. **Recomendo instrumentar os dois valores antes do M8** (~2
   linhas read-only no `b3_instrument`, custo zero) — é o que transforma este
   item de "suspeita de leitura" em "número".
2. Também é código ORIGINAL do PlatEMO (mesma bússola D29 do VD-b1).
3. Se o ramo 1 nunca rodar no grid, o achado é inócuo na prática e vira nota de
   dossiê. Se rodar, é da mesma família do DI-45 e vai à mesa.

---

## Resumo para a mesa do autor

| verificação | veredito | medida | ação |
|---|---|---|---|
| **VD-b1** torneio | 🔴 confirmado | 93,0% das 8.443 gerações; 44,9% do Dec inalcançável (mediana) | decisão de fidelidade (D97/D29) — 3 opções acima |
| **VD-b3** índice | 🔴 estrutural, não medido | `nzero=0` em 1.619/1.619 (não discrimina o ramo) | instrumentar `size(Via,1)` e `NI−mu` (~2 linhas) e re-medir |

**Nenhuma linha de código foi alterada nesta verificação** (SPEC §3/FASE V).
