function ftm = e7_sonda(Problem, net, Params, tr_x, ymin_vig, espaco_vig)
% e7_sonda — bloco da SONDA CANONICA (DI-09/§17.2.2) do e7 EDN-ARMOEA.
% Chamado da EDNARMOEA.main logo APOS o retreino da rede (updatemodel) e ANTES
% de qualquer consumo de RNG ou decisao da busca. READ-ONLY: nao altera nenhuma
% decisao (D97) e nao gasta FE.
%
% Devolve `ftm` (fe_treino_max) porque ele SO e calculavel AQUI: no ponto do
% e7_instrument (EDNARMOEA.m:120) o arquivo `A` ja cresceu (:102) e o `tr_x` ja
% foi RE-selecionado (:103), logo um recalculo la daria o ftm do PROXIMO fit.
% O chamador repassa este valor ao e7_instrument, que roda pos-Evaluation e
% precisa do MESMO ftm nas linhas ③ da BUSCA (mesmo treino, mesmo fit).
%
% Semantica contratada (CONTRATO_DE_DADOS §3.2, linha "b3, c141, e7, ..."):
% mu e sigma POR OBJETIVO, UM unico bloco por ciclo (modelo unico, cabeca unica
% — nada de 2 blocos como e74/e103):
%   mu_0..mu_{M-1}    = media das T=100 passagens MC-dropout (Estimate.m:27),
%                       saida PopObj (Estimate.m:37);
%   sigma_0..sigma_{M-1} = desvio POPULACIONAL das T=100 passagens, com o guard
%                       sqrt(max(var_pop,0)) (Estimate.m:32-34), saida PopStd
%                       (Estimate.m:38).
% O e7 e o UNICO config da R1 cujo sigma NAO e analitico: ele vem do proprio
% estocastico do MC-dropout. E, por isso, o unico onde o save/restore de RNG do
% SondaState (I1, SondaState.m:151-152) deixa de ser redundancia estrutural e
% passa a ser LOAD-BEARING — ver a secao RNG abaixo.
% pred_tipo="valor"; pred_classe/pred_score/pred_confianca ficam NULL.
%
% Por que ESTE ponto (EDNARMOEA.m, apos :63, antes de :65):
%   1. POS-FIT — :62 (`updatemodel`) acabou de treinar `net`, e `Params.ps/qs`
%      casam com esse net (ciclo 1: :38-40 + trainmodel; demais: :104-106 do
%      ciclo anterior, EXATAMENTE os tr_xx/tr_yy que alimentaram o :62). Entre
%      :62 e o hook so existe :63 (`toc`) — zero RNG, zero decisao;
%   2. PRE-1o CONSUMO DE RNG DA BUSCA — o primeiro `rand` pos-fit e a PopDec
%      aleatoria de :67, e o segundo e o dropout do Estimate de :68;
%   3. PRE-1a DECISAO — MatingSelection (:79), OperatorGA (:80),
%      EnvironmentalSelection (:87) e IndividualSelect (:97, com kmeans em
%      IndividualSelect.m:13) vem todos depois;
%   4. PRE-`Problem.Evaluation` (:101), a UNICA do ciclo, onde o FEBudget
%      levanta PlatEMO:Termination no hard-stop (FEBudget.m:86-92 via
%      c217_batch_eval, experiment.m:470-479) NO MEIO do lote Ke=3. Este e o
%      UNICO ponto que garante o bloco do ULTIMO ciclo: comprovado no MMF1, cujo
%      ciclo 14 fez o fit de :62 e morreu em :101 (e7_gen ate g=13, guard
%      hard_stop fe=61, n_geracoes=14) — com o hook em :64 e due(14)=true esse
%      ciclo AINDA emite seu bloco. O e7_instrument de :120 nunca roda nele.
%
% ⚠ RNG (I1) — a aritmetica do risco: um bloco consome T=100 passagens x 2
% chamadas de `dropout` cada (testNet.m:7 sobre N x D e :10 sobre N x 40), e
% cada dropout e um `rand(n1,n2)` (dropout.m:4) => 100*2000*(D+40) draws, ou
% ~1,4e7 no ZDT1 (D=30) / ~1,0e7 no DTLZ2 / ~8,4e6 no MMF1. O consumidor
% imediatamente seguinte e o `rand(popsize,Problem.D)` de :67. SEM o save/restore
% do SondaState a PopDec do ciclo muda e a trajetoria inteira diverge — a ①
% deixaria de ser bit-identica a data/experiments/_baseline_pre_retrofit/e7/ e o
% retrofit REPROVA. Nao envolver esta chamada em nenhum rng() local.
%
% ⚠ NAO CAPTURAR excecao: o SondaState re-lanca PlatEMO:Termination
% (SondaState.m:175) — o hard-stop D21 tem de subir. Nada de try/catch aqui.
%
% ⚠ `nneg` (3o output do Estimate) e DESCARTADO de proposito. Somar em
% `n_std_neg` (EDNARMOEA.m:69/:82) inflaria o contador da guarda `std_neg`
% (e7_instrument.m:51-54) com eventos do INSTRUMENTO, mudando a ④ e o .jsonl vs
% a baseline sem que nada da busca tenha mudado.
%
% ⚠ CLOSURE — `net` e reatribuido a cada ciclo (:62) e `Params` em :106, mas
% ambos sao STRUCTS puros (trainmodel.m:23 `net.W=W;net.B=B;` — sem objeto
% handle), e o MATLAB captura por VALOR na criacao do handle. Logo o `arm` do
% SondaState (SondaState.m:99) congela o net do ULTIMO probe, e o finalProbe
% mede esse, nao o corrente. Correto — mas so porque nao ha handle no caminho.

    % ── fe_treino_max (DI-09/A1) ─────────────────────────────────────────────
    % LITERAL do §17.2: "maior fe_index no TREINO do modelo no momento do fit".
    % O treino em vigor e `tr_x`: EDNARMOEA.m:36 (`A.decs`, o DoE inteiro) no
    % ciclo 1; EDNARMOEA.m:103 (`SelectTrainData(A, 11D-1, |New|)`) nos demais —
    % espaco NATIVO (SelectTrainData.m:29-30 fatia `P.decs`), exatamente o que o
    % `bud.solutionIdOf` indexa (FEBudget.m:108-113, keyOf + isKey).
    % O atalho `bud.fe-1` do c141 NAO vale: o SelectTrainData PODA (cap fixo em
    % N1=11D-1 enquanto `A` cresce +3 por ciclo), e o e7 nao deduplica infill
    % (duplicata = cache-hit 0 FE, D89 — solutionIdOf devolve o id ORIGINAL).
    % ⚠ Na PRATICA o ftm coincide com bud.fe-1 quase sempre, porque o
    % `Choose=[false(1,NA-N2),true(1,N2)]` (SelectTrainData.m:20) FORCA as N2=3
    % solucoes mais recentes de `A` dentro do treino. A nao-monotonicidade e um
    % caso de BORDA (ciclo com os 3 infills 100% duplicados, guarda (c) do D60),
    % nao a regra. MESMO ASSIM: MEDIR, nunca assumir — o ponto do §17.2 e que
    % esses ciclos APARECAM no dado em vez de serem presumidos ausentes.
    % Custo: exatamente 11D-1 lookups (329 ZDT1 / 131 DTLZ2 / 21 MMF1). Read-only,
    % sem RNG, ZERO FE (I2 — nunca chamar bud.evaluate).
    % Fica ANTES do early-return porque o `ftm` e devolvido MESMO em run sem sonda
    % (o e7_instrument o usa nas linhas ③ da busca, §4.4 da receita).
    bud = Problem.data.bud;
    ftm = -1;
    for i = 1:size(tr_x, 1)
        sid = bud.solutionIdOf(tr_x(i, :));
        if sid > ftm, ftm = sid; end
    end
    if ftm < 0, ftm = []; end                  % => NULL na ③

    d = Problem.data;
    if ~isfield(d, 'snd') || isempty(d.snd), return; end     % run sem sonda
    snd = d.snd;
    g = double(d.buf.gen);                     % o hook ja bumpou no topo do ciclo
    if g < 1, g = 1; end

    % ── C3 (DEF-C3) — TRANSLACAO ─────────────────────────────────────────────
    % IDENTICO ao que o e7_instrument serializa nas linhas de busca
    % (e7_instrument.m:65/:81-83), para que sonda e busca sejam comparaveis:
    % espaco_modelo = espaco_vig ("cru" no ciclo 1, EDNARMOEA.m:54-55;
    % "transformado" do ciclo 2 em diante, :130); transf_tipo="translacao";
    % transf_params={ymin}. Inversao: cru = mu + ymin. O sigma e INVARIANTE a
    % translacao — nao converter.
    % ⚠ NAO recalcular ymin de `A` aqui. No hook do ciclo k, `ymin_vig` e o
    % gravado no FIM do ciclo k-1 (:129), e e EXATAMENTE a translacao do treino
    % em vigor: o fit de :62 usa tr_yy de :105, vindo do SelectTrainData de :103,
    % cujo `Range(1,:)=min(P.objs,[],1)` (SelectTrainData.m:15,17) roda sobre o
    % MESMO `A` de :102 que gerou o ymin_vig de :129. Recalcular adiantaria o
    % ymin em 1 ciclo e quebraria a inversao.
    % ⚠ No ciclo 1 espaco_vig="cru" com ymin=zeros: mantem-se transf_tipo=
    % "translacao" (translacao identidade), replicando o precedente do
    % e7_instrument, que emite assim incondicionalmente. Nao inventar "nenhuma".
    % O mapminmax (Params.ps/qs) NAO entra no C3: e INTERNO ao Estimate (aplica
    % em x na :13, reverte y na :18), igual a busca.
    tp = string(jsonencode(struct('ymin', ymin_vig(:).')));

    % hp EFETIVOS da EDN (DI-10/B1) — os valores que de fato governam, nao os
    % declarados: `Params.round`=8e4 NAO governa o update (updatemodel.m:5
    % hardcoda run=8000) e `Params.decay` NAO e usado (trainNet.m:42 hardcoda
    % decay=1e-05). T=100 vem de Estimate.m:16; batchsize=V=D (trainmodel.m:11).
    % ⚠ `loss_treino` fica de FORA: BARRADO pelo autor (DI-12.1). A loss esta
    % COMENTADA em trainNet.m:17 — expo-la nao seria "acrescentar um retorno a um
    % numero ja calculado" (a premissa dos casos liberados b3/e103), e sim
    % RE-HABILITAR computacao dentro do laco de 8e4/8e3 passos. Proxy via
    % `testNet` tambem esta barrado: consome RNG (dropout.m:4).
    hp = struct('neuronN',        40, ...
                'dropP',          Params.dropP(:).', ...
                'learnR',         Params.learnR, ...
                'decay_efetivo',  1e-05, ...
                'batchsize',      Params.batchsize, ...
                'T',              100, ...
                'passos_init',    80000, ...
                'passos_update',  8000, ...
                'n_treino',       size(tr_x, 1));

    % ── o disparo (cadencia k=2 + arm p/ a sonda final pos-Solve) ────────────
    % 1 bloco por ciclo. Cadencia g=1,2,4,6,... (SondaState.m:92); o bloco da
    % ULTIMA geracao sai do finalProbe do run_e7, que NAO e no-op no ZDT1 nem no
    % DTLZ2 (o hook_output bumpa a geracao tambem na chamada final de
    % NotTerminated => buf.gen final = 201/81, IMPARES, jamais sondadas pela
    % cadencia). Total: ZDT1 102 blocos · DTLZ2 42 · MMF1 8 (neste ultimo o 8o
    % sai do PROPRIO hook, no ciclo 14 cortado, e ai o finalProbe e que e no-op).
    fn = @(Xs) e7_sonda_rows(net, Params, Xs, Problem.M, espaco_vig, tp);
    snd.probe(g, fn, ftm, 'modelo', "EDN-MCdropout", 'hp', hp);
end


function rows = e7_sonda_rows(net, Params, Xs, M, espaco_vig, tp)
% As S=2000 linhas da ③, NA ORDEM DO ARTEFATO (join por posicao — §3.1).
% Xs entra NATIVO e em LOTE UNICO: o `mapminmax('apply',...,ps)` e interno ao
% Estimate (Estimate.m:13), exatamente como na busca com a PopDec de :67.
%
% ⚠ CHUNKING E PROIBIDO AQUI — e a diferenca em relacao ao molde do b1. No b1 o
% `predictor` e deterministico e as linhas sao independentes, entao fatiar e
% bit-equivalente. Aqui NAO: o `dropout` sorteia UMA mascara `rand(n1,n2)` com
% n1 = numero de linhas do lote (dropout.m:3-4), logo fatiar consumiria o stream
% de RNG em outra geometria e produziria mu/sigma DIFERENTES. Lote unico e parte
% da semantica, nao so da performance. (Custo de RAM: o `array1=[result.y]` do
% Estimate.m:25 e S x (100*M) — 3,2 MB em M=2, 4,8 MB em M=3. Nao e o gargalo;
% o gargalo de RAM e o acumulo das linhas ③ em buf.srows ate o export, D86.)
%
% ⚠ NAO CLAMPAR os 2000 pontos ao range do mapminmax. Eles cobrem a caixa
% inteira e sairao fora do [-1,1] do `ps` (ajustado so sobre as 11D-1 linhas de
% treino) — mas a PopDec da busca (:67) e uniforme na MESMA caixa e sofre a
% MESMA extrapolacao. Clampar criaria uma semantica diferente da que a busca
% usa, alem de violar o I3 (nada de sort/unique/filtro/clamp no X da sonda).
%
% ⚠ O 3o output (`nneg`) e descartado: ver o cabecalho.
    [MU, SIG, ~] = Estimate(Xs, net, Params, M);
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'mu', MU, 'sigma', SIG, ...
        'pred_tipo', "valor", 'modelo_flag', "EDN-MCdropout", ...
        'espaco_modelo', string(espaco_vig), ...
        'transf_tipo', "translacao", ...
        'transf_params', tp);
end
