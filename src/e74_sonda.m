function ftm = e74_sonda(Problem, cabeca, modelo, x_train, varargin)
% e74_sonda — bloco da SONDA CANONICA (DI-09/§17.2.2) do e74 CLMEA.
% UMA funcao para as QUATRO instancias de modelo do config; a `cabeca` diz qual.
% Chamada de dentro de cada estrategia, logo APOS o fit e ANTES de qualquer
% decisao. READ-ONLY: nao altera nada da busca (D97) e nao gasta FE.
%
% Devolve `ftm` (fe_treino_max) porque TRES das quatro cabecas subamostram o
% treino: o valor so e calculavel no ponto do fit e o e74_instrument (que roda
% POS-Evaluation, com o arquivo ja crescido) precisa do MESMO numero nas linhas
% de busca (resolucao de handoff/DI09-retrofit-R1.md:32-34). Por isso `ftm` e
% inicializado ANTES de todo early-return: num run SEM artefato de sonda
% (problema fora do grid) o instrument continua recebendo o valor certo.
%
% ─── O e74 NAO tem "3 cabecas": tem 4 INSTANCIAS de modelo ────────────────────
%   'boot' RBF-global(boot) — CLMEA.m:65, M redes newrbe MONO-saida (uma por
%          objetivo) sobre o DoE. Roda 1x NO ARRANQUE, FORA do while (:62-83).
%   's1'   PNN(s1)          — ClassifierSelect.m:8, newpnn sobre a subamostra
%          estratificada; devolve o NIVEL de nao-dominancia (1..4).
%   's2'   RBF-global(s2)   — Hv_Select.m:9, newrbe M-dimensional sobre o
%          ARQUIVO INTEIRO (a rede da curva O(n^3)).
%   's3'   RBF-local(s3)    — Local_infill.m:31, newrbe sobre os N vizinhos EM
%          OBJETIVO do RefPoint. LOCAL (ver a advertencia grande abaixo).
% Os literais de modelo_flag sao IDENTICOS aos das linhas de busca
% (e74_instrument.m:64/:111/:128/:135) — o join sonda x busca da R4 e por
% modelo_flag; divergir aqui parte a serie em duas.
%
% ─── CADENCIA: UM SondaState POR CABECA — DI-19.1 CRAVADA ────────────────────
% [DI-19.1 — decisao do autor, 2026-07-19; REGISTRO PARTE A8] UM SondaState POR
% CABECA ('boot'/'s1'/'s2'/'s3'), com `k` proprio e fase deslocada — a saida
% (iii) do PARA-E-LOGA que o recon do e74 tinha escalado (D81). A guarda de
% disparo abaixo continua aceitando TAMBEM o SondaState escalar (molde legado
% dos demais run_*), mas o molde DESTE config e o struct de handles.
% CALIBRACAO (D-11) — escolhida pelo IMPLEMENTADOR e sujeita a ratificacao em
% lote (D97): ROUND-ROBIN
%       s1 k=6  -> c = 2,5,8,...  (g=4c-2: mod(4c-2,6)==0 <=> c ≡ 2 mod 3)
%       s2 k=3  -> c = 1,4,7,...  (g=4c-1: mod(4c-1,3)==0 <=> c ≡ 1 mod 3)
%       s3 k=12 -> c = 3,6,9,...  (g=4c:   mod(4c,12)==0  <=> c ≡ 0 mod 3)
% Cada ciclo sonda EXATAMENTE UMA cabeca e cada cabeca e medida a cada 3
% ciclos — volume ~1 bloco/ciclo (ZDT1 ~211 blocos ~430k linhas na ③, vs os
% 1,27M de linhas que k=1 nas 3 cabecas geraria). O boot dispara em g=1 pela
% clausula da 1a (due(1) e true para QUALQUER k). Os k moram no run_e74 (quem
% constroi os handles — experiment.m), NUNCA aqui: este arquivo so repassa o g
% verdadeiro. (A numeracao correta e DI-19.x: a torre ocupou DI-15.0..15.5,
% DI-16.x E DI-17.1..17.4 (hardening M7) em sessoes concorrentes — o
% retrofit-R1 foi realocado de DI-17.x para DI-19.x pela torre; uma versao
% anterior deste cabecalho citava "DI-15.1", que no REGISTRO e outra coisa.)
%
% O motivo MECANICO pelo qual a questao existe (isto e fato medido, nao
% decisao): ALGORITHM.m:119 chama o outputFcn
% (=hook_output.m:31, bumpGen) DENTRO do NotTerminated, e a CLMEA.main chama
% NotTerminated em :46, :101(while), :114, :129 e :155 => o `g` bumpa 4x POR
% CICLO. O mapa exato e:
%       boot -> g = 1              (apos o bump de :46, antes do while)
%       ciclo c:  s1 -> g = 4c-2   s2 -> g = 4c-1   s3 -> g = 4c
% Sob um UNICO SondaState com k=2 (SondaState.due, :92 -> g==1 || mod(g,k)==0)
% o s1 e o s3 disparariam TODO ciclo (nenhuma subamostragem) e o s2, SEMPRE
% impar e != 1, NUNCA dispararia — justamente a rede cuja escalabilidade a R4
% quer medir. Com um estado por cabeca, cada uma tem `k` proprio e a fase fica
% deslocada. A ESCOLHA dos k mora no run_e74 (quem constroi os handles), NAO
% aqui; para referencia, `due` e mod(g,k)==0 (mais a clausula da 1a), logo:
%       s1 (g=4c-2 == 2 mod 4): k=1,2 -> todo ciclo; k MULTIPLO DE 4 -> NUNCA;
%            demais k -> periodicamente (k=3 -> c=2,5,8...; k=6 -> c=2,5,8...).
%       s2 (g=4c-1, sempre IMPAR): k=1 -> todo ciclo; QUALQUER k PAR -> NUNCA;
%            k impar >1 -> periodicamente (k=3 -> c=1,4,7...).
%       s3 (g=4c):  k=1,2,4 -> todo ciclo;  k=8 -> ciclo sim, ciclo nao.
%       boot (g=1): a clausula "SEMPRE a 1a" dispara para QUALQUER k.
% ⚠ O `arm` tambem e por handle (SondaState.m:99), logo o run_e74 tem de chamar
% `finalProbe` em CADA handle — senao a ULTIMA geracao de duas das cabecas
% desaparece do artefato. (Sob estado UNICO o `arm` e compartilhado: a ultima
% cabeca a rodar sobrescreve as outras e o finalProbe mede so ela.)
% ⚠ Esta funcao passa SEMPRE o `g` VERDADEIRO (buf.gen). Deslocar o g aqui para
% forcar cadencia carimbaria uma geracao inexistente na ③ e quebraria a
% sincronizacao §17.1.3 com a ② e com as linhas de busca do mesmo bloco.
%
% ─── SEMANTICA CONTRATADA por cabeca (CONTRATO_DE_DADOS §3.2 + DI-03) ─────────
% pred_tipo e POR LINHA; nenhuma linha e "hibrido". espaco_modelo="cru" nas
% QUATRO: newpnn/newrbe recebem `.decs` cru, sem escalonamento e sem C3.
%   s1   : pred_tipo="classe", pred_classe="nivel_k" (k=1..4); mu/sigma/score NULL.
%   s2/s3: pred_tipo="valor",  mu = M colunas; sigma NULL.
%   boot : pred_tipo="valor",  mu = M colunas, a coluna i vinda da rede i.
%
% sigma NULL em TODAS: newrbe e INTERPOLANTE EXATO (nao produz variancia) — a
% mesma distincao VAR-GP x ERR-EMP do c141 (c141_sonda.m:6-9).
%
% ⚠ DIVERGENCIA DECLARADA (s2): nas linhas de BUSCA o e74 grava sigma_0=HV_gain
% (e74_instrument.m:126) e pred_score=score CalHV (:127). NENHUM dos dois e saida
% do modelo — sao funcoes da DECISAO sobre o arquivo — e nem sao computaveis
% para 2000 pontos sem 2000 chamadas de CalHV por bloco. Ficam NULL na sonda.
% Consequencia a registrar no sigma_dict: para o modelo_flag "RBF-global(s2)" a
% coluna sigma_0 muda de significado entre regime='online' e regime='sonda'.
%
% ⚠ pred_confianca do PNN e INACESSIVEL read-only: a 2a camada do newpnn e
% `compet` (saida one-hot) e `vec2ind(sim(...))` so devolve o argmax. Nao ha
% margem/softmax sem reimplementar o miolo da rede — mesmo estatuto do
% `loss_treino` do e7 (DI-12.1). Fica NULL; NAO inventar proxy.
%
% ⚠ ARMADILHA DE LEITURA do s1: a PNN e uma soma de radbas com spread
% spr=maxdist/sqrt(2n) (ClassifierSelect.m:6). Para um ponto Sobol MUITO longe
% do treino todas as ativacoes saturam em 0 e o `compet` devolve o PRIMEIRO
% indice por desempate — isto e, "nivel_1". Nao e o modelo "achando otimo": e
% underflow. A R4 tem de olhar a distribuicao de classes junto com a distancia
% ao arquivo antes de concluir qualquer coisa sobre a acuracia do classificador.
%
% ⚠⚠ ADVERTENCIA OBRIGATORIA — o s3 e um modelo LOCAL medido por uma sonda
% GLOBAL. Local_infill.m:27 define a caixa [x_lb,x_ub]=min/max(x_train) sobre os
% N vizinhos e a busca CLAMPA todo offspring dentro dela (:44). O dominio de
% validade da RBF-local e ESSA CAIXA. A sonda nao pode clampar (I3 — a ordem e o
% suporte do artefato sao fixos, SondaState.m:12-14), logo a MAIORIA dos 2000
% pontos cai FORA do dominio e a rede extrapola. O erro (WAPE/RMSE) do
% "RBF-local(s3)" sera estruturalmente pessimo por CONSTRUCAO DA MEDIDA, nao por
% qualidade do modelo. Sem esta nota no sigma_dict/handoff a R4 le "RBF-local e
% pessima" — leitura ERRADA. A comparacao honesta do s3 e restrita ao
% subconjunto de pontos dentro da caixa daquele bloco (que a R4 pode reconstruir
% cruzando com os x_pop do bloco de busca do mesmo g).
%
% ─── POR QUE ESTES PONTOS DE HOOK (WIRED — DI09-R1c; linhas POS-insercao) ────
% Os quatro passam nos quatro testes (pos-fit / pre-1a-decisao / pre-1o consumo
% de RNG / pre-Evaluation) e ficam FORA dos tic/toc de fit e de busca (§17.6):
%   s1   ClassifierSelect.m:15 — fit em :8, `tfit_e74` fechado em :9,
%        `tbusca_e74 = tic` so em :16. O 1o RNG sao os 3 `randi` + OperatorDE
%        de :26; ate la so ha NDSort/find (deterministicos). E ANTES da
%        Evaluation do bloco (CLMEA.m:109).
%   s2   Hv_Select.m:16 — fit em :9, toc em :10, tic da busca em :17. O 1o RNG
%        sao os 2 `randperm(N)` de :22; :18 SelectTrainData e :19 `sim` nao
%        consomem RNG. ANTES da Evaluation (CLMEA.m:124).
%   s3   Local_infill.m:39 — fit em :31, toc em :32, tic da busca em :41. O 1o
%        RNG sao os 2 `randi(k_local,1,N)` de :43; :22-29 sao pdist2/sort/min/
%        max. ANTES da Evaluation (CLMEA.m:139).
%   boot CLMEA.m:91 — depois do sync D89 de :84 e antes da chamada do
%        e74_instrument de :93, com as M redes acumuladas no cell nets_e74
%        (:61, append em :67 FORA do tic/toc do fit de :65). UM bloco com mu
%        M-dimensional, pareado com o UNICO bloco de busca que o boot ja emite
%        (e74_instrument.m:60-66, 1 chamada). Disparar DENTRO do laco daria M
%        blocos de sonda contra 1 de busca no MESMO g=1.
%        ⚠ UNICA excecao a letra da regra "pre-Evaluation": este ponto fica
%        depois das Evaluation dos extremos (:78). E inofensivo — o assert de
%        CLMEA.m:41 garante maxFE > |DoE| e a folga maxfe=31D-1 vs n_init=11D-1
%        cobre com sobra os <=M extremos, entao o hard-stop nao pode disparar
%        ali. (Se disparasse, o `finalProbe` pos-Solve cobriria o modelo armado.)
%
% ─── RNG ──────────────────────────────────────────────────────────────────────
% `sim`, `vec2ind` e `compet` sao aritmetica pura — zero rand/randn/randi. O
% save/restore do estado do RNG acontece assim mesmo, dentro do SondaState
% (I1 e invariante ESTRUTURAL, nao dependencia de auditoria do `sim`).
%
% USO (o que o run_e74 tem de montar):
%   sd = load_sonda(problema, D, M, dataRoot);
%   snd = [];
%   if ~isempty(sd)
%       snd = struct('boot', SondaState(sd, buf, fid, alg, k_boot), ...
%                    's1',   SondaState(sd, buf, fid, alg, k_s1), ...
%                    's2',   SondaState(sd, buf, fid, alg, k_s2), ...
%                    's3',   SondaState(sd, buf, fid, alg, k_s3));
%   end
% Uma cabeca cujo campo NAO exista no struct simplesmente nao e sondada (o ftm
% continua sendo devolvido) — e assim que se desliga uma cabeca sem tocar no
% arquivo stock.

    cabeca = char(cabeca);
    if ~ismember(cabeca, {'boot', 's1', 's2', 's3'})
        error('e74_sonda:cabeca', 'cabeca desconhecida: %s', cabeca);
    end

    % ── fe_treino_max (DI-09/A1) ─────────────────────────────────────────────
    % LITERAL do §17.2: "maior fe_index no TREINO do modelo no momento do fit".
    % `solution_id == fe_index` por construcao (FEBudget.m:98-99).
    % TRES REGIMES DE TREINO NO MESMO RUN — nao existe um ftm unico do config:
    %   boot: x_train = Arc.decs capturado em CLMEA.m:50, ANTES do laco. NAO
    %         cresce dentro dele (os extremos entram em Arc na :78, mas o
    %         snapshot nao) => as M redes veem o DoE INTEIRO e ftm = 11D-2.
    %         ⚠ NAO usar o atalho `bud.fe-1` AQUI: no ponto do hook (:91) o
    %         bud.fe JA INCLUI os ate M extremos avaliados em :78, que
    %         NENHUMA das M redes viu. O atalho superestimaria o treino.
    %   s1  : subamostra ESTRATIFICADA de N=min(100,|Arc|) linhas por camadas ND
    %         com quotas 10/30/40/20% (Data_Process.m:10-22). Copia bit-a-bit de
    %         linhas de Arc.decs (:20), logo solutionIdOf resolve.
    %   s3  : os N vizinhos mais proximos EM OBJETIVO do RefPoint
    %         (Local_infill.m:22-24) — a subamostra mais enviesada das tres.
    %   s2  : o ARQUIVO INTEIRO (Hv_Select.m:2). Arc so cresce (CLMEA.m:78/:109/
    %         :124/:139), nunca e podado, e o dedup eps garante |Arc| == bud.fe
    %         => vale o atalho `bud.fe-1` do c141 (c141_sonda.m:40).
    % ⚠ NAO-MONOTONICO em boot/s1/s3 (regra 9 do R4): o subconjunto TROCA de
    % composicao entre ciclos, nao so cresce — e essa e a semantica pedida, e o
    % que o filtro in-sample x out-of-sample da R4 precisa enxergar.
    % ⚠ CUSTO: solutionIdOf -> keyOf faz typecast+dec2hex sobre 8*D bytes por
    % linha. Por isso o s2 usa o atalho (|Arc| chega a ~929 no ZDT1, x211 ciclos)
    % e por isso o valor e calculado UMA vez aqui e DEVOLVIDO, nunca recalculado
    % no e74_instrument.
    ftm = [];
    d   = Problem.data;
    bud = d.bud;
    if strcmp(cabeca, 's2')
        m = bud.fe - 1;                        % leitura PRE-Evaluation do proprio
        if m >= 0, ftm = m; end                % bloco => sem o "- lote" do c141
    else
        m = -1;
        D = double(Problem.D);
        for i = 1:size(x_train, 1)
            sid = bud.solutionIdOf(x_train(i, 1:D));   % read-only, sem RNG, 0 FE
            if sid > m, m = sid; end
        end
        if m >= 0, ftm = m; end                % ftm < 0 => [] => NULL na ③
    end

    % ── guardas do disparo ───────────────────────────────────────────────────
    if ~isfield(d, 'snd') || isempty(d.snd), return; end       % run sem sonda
    snd_all = d.snd;
    % DUAS formas aceitas de proposito (DI-19.1 CRAVOU a (iii) — struct POR
    % CABECA, o que o run_e74 constroi; o escalar segue aceito p/ o molde
    % legado dos demais run_*):
    %   SondaState escalar -> UM estado para as 4 cabecas (o molde dos outros
    %       run_*: experiment.m:199/378/555/734 poem um handle CRU aqui);
    %   struct de handles  -> um estado por cabeca ('boot','s1','s2','s3').
    % ⚠ Exigir `isstruct` sozinho fazia a sonda virar NO-OP SILENCIOSO sob o
    % molde vigente: sem erro, sem guarda, sem linha — o pior modo de falha para
    % instrumentacao. Uma cabeca AUSENTE do struct continua desligada de
    % proposito (e assim que se desliga uma cabeca sem tocar no arquivo stock).
    if isa(snd_all, 'SondaState')
        snd = snd_all;
    elseif isstruct(snd_all)
        if ~isfield(snd_all, cabeca), return; end
        snd = snd_all.(cabeca);
    else
        return;
    end
    if isempty(snd), return; end
    if isempty(modelo), return; end            % edge: ciclo sem fit (Arc.best vazio)

    g = double(d.buf.gen);                     % g VERDADEIRO (ver DI-19.1 acima)
    if g < 1, g = 1; end

    % hp efetivos (DI-10/modelo_hp) — `spr` e `n_treino` sao os MESMOS que o
    % e74_instrument ja publica na linha e74_gen, para as duas leituras baterem.
    o = e74_opts(varargin{:});
    M = double(Problem.M);

    switch cabeca
        case 's1'
            flag = "PNN(s1)";
            hp = struct('tipo', "newpnn", 'spread', o.spr, ...
                        'n_neuronios', size(x_train, 1), 'M_saidas', 1, ...
                        'tempo_fit_s', o.tempo_fit_s);
            fn = @(Xs) e74_rows_pnn(modelo, Xs, flag);
        case 's2'
            flag = "RBF-global(s2)";
            hp = struct('tipo', "newrbe", 'spread', o.spr, ...
                        'n_neuronios', size(x_train, 1), 'M_saidas', M, ...
                        'tempo_fit_s', o.tempo_fit_s);
            fn = @(Xs) e74_rows_rbf(modelo, Xs, M, flag);
        case 's3'
            flag = "RBF-local(s3)";
            hp = struct('tipo', "newrbe", 'spread', o.spr, ...
                        'n_neuronios', size(x_train, 1), 'M_saidas', M, ...
                        'tempo_fit_s', o.tempo_fit_s);
            fn = @(Xs) e74_rows_rbf(modelo, Xs, M, flag);
        case 'boot'
            flag = "RBF-global(boot)";
            assert(iscell(modelo), ...
                'e74_sonda: boot espera um cell com as M redes mono-saida');
            hp = struct('tipo', "newrbe", 'spread', o.spr, ...
                        'n_neuronios', size(x_train, 1), 'M_saidas', 1, ...
                        'n_redes', numel(modelo), 'tempo_fit_s', o.tempo_fit_s);
            fn = @(Xs) e74_rows_boot(modelo, Xs, M, flag);
    end

    snd.probe(g, fn, ftm, 'modelo', flag, 'hp', hp);
end


% ══════════════════════════════════════════════════════════════════════════════
function rows = e74_rows_pnn(net, Xs, flag)
% As S=2000 linhas da ③ do s1, NA ORDEM DO ARTEFATO (o join com o gabarito e
% POR POSICAO — §3.1; a ③ nao tem coluna sonda_id). Xs vai DIRETO ao preditor:
% espaco NATIVO, sem normalizacao e sem clamp — o newpnn foi treinado com
% `x_train'` cru (ClassifierSelect.m:8).
% pred_classe = "nivel_k" com a MESMA formatacao das linhas de busca
% (e74_instrument.m:110), senao os dois lados nao juntam por string.
    k = e74_sim_pnn(net, Xs);
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'pred_tipo', "classe", ...
        'pred_classe', "nivel_" + string(k), ...    % mu/sigma/score ausentes => NULL
        'modelo_flag', flag, 'espaco_modelo', "cru");
end


function rows = e74_rows_rbf(net, Xs, M, flag)
% As S linhas da ③ de uma RBF M-dimensional (s2 ou s3). mu = M colunas;
% sigma AUSENTE => NULL (newrbe interpola exatamente, nao ha incerteza).
% Para o s3 lembrar da advertencia do cabecalho: Xs NAO e clampado na caixa
% local — e o contrato I3 que manda, e a extrapolacao e o preco declarado.
    MU = e74_sim_rbf(net, Xs, M);
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'mu', MU, 'pred_tipo', "valor", ...
        'modelo_flag', flag, 'espaco_modelo', "cru");
end


function rows = e74_rows_boot(nets, Xs, M, flag)
% As S linhas da ③ do bootstrap. Cada rede e MONO-saida (CLMEA.m:65 roda dentro
% de `for i = 1:Problem.M`), entao a coluna i de mu vem da rede i — o bloco
% inteiro sai com mu M-dimensional, semantica identica a do c141. Coluna sem
% rede correspondente fica NaN (=> NULL), nunca 0.
    n  = size(Xs, 1);
    MU = NaN(n, M);
    for i = 1:min(numel(nets), M)
        MU(:, i) = e74_sim_rbf(nets{i}, Xs, 1);
    end
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'mu', MU, 'pred_tipo', "valor", ...
        'modelo_flag', flag, 'espaco_modelo', "cru");
end


% ══════════════════════════════════════════════════════════════════════════════
function Y = e74_sim_rbf(net, Xs, M)
% CHUNKING: o newrbe tem UM neuronio por linha de treino — no s2 sao ate ~929
% (|Arc| no ZDT1). `sim(net, Xs')` materializa a matriz de distancias
% neuronios x pontos (929 x 2000 = ~15 MB por chamada) alem da saida. Fatiar
% limita o pico. O que importa para o I3 e que a saida da linha i depende SO da
% linha i (radbas por distancia + combinacao linear), logo a concatenacao
% preserva exatamente a ordem e a contagem do artefato. Nada de
% sort/unique/filtro/clamp.
% ⚠ NAO afirmar "bit-identico a uma chamada unica": o blocking interno do BLAS
% dentro do `sim` pode mudar os ultimos bits conforme o tamanho do lote. Isso e
% INOFENSIVO aqui (a sonda e medida, nao realimenta nenhuma decisao — nada da
% busca depende destes numeros), mas o gate de nao-perturbacao se prova pela ①
% bit-a-bit, nao por uma promessa de bit deste arquivo.
    n = size(Xs, 1);
    Y = zeros(n, M);
    passo = 250;
    for a = 1:passo:n
        b = min(a + passo - 1, n);
        Y(a:b, :) = sim(net, Xs(a:b, :)')';
    end
end


function k = e74_sim_pnn(net, Xs)
% Mesmo chunking, mesma independencia por linha. `vec2ind(sim(...))` e a
% LEITURA EXATA que a busca faz (ClassifierSelect.m:29/:38/:58/:63) — a sonda
% replica o consumo do modelo, nao uma versao "melhorada" dele.
    n = size(Xs, 1);
    k = zeros(n, 1);
    passo = 250;
    for a = 1:passo:n
        b = min(a + passo - 1, n);
        kb = vec2ind(sim(net, Xs(a:b, :)'));
        k(a:b) = double(kb(:));
    end
end


function o = e74_opts(varargin)
% Pares nome-valor opcionais so para o `modelo_hp` (spr / tempo_fit_s). Nao
% influenciam nenhuma linha da ③ — se o chamador nao passar, ficam NaN.
    o = struct('spr', NaN, 'tempo_fit_s', NaN);
    for i = 1:2:numel(varargin)
        o.(varargin{i}) = varargin{i+1};
    end
end
