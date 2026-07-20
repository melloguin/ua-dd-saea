function ftm = b4_sonda(Problem, net, TrainIn)
% b4_sonda — bloco da SONDA CANONICA (DI-09/§17.2.2) do b4 CSEA.
% Chamado da CSEA.main logo APOS o fit da rede e ANTES da 1a decisao.
% READ-ONLY: nao altera a busca (D97) e nao gasta FE.
%
% Devolve `ftm` (fe_treino_max) porque o calculo custa caro e e o MESMO valor
% que as linhas de BUSCA e o `b4_gen` precisam — calcula-se UMA vez por geracao
% aqui e repassa-se ao b4_instrument (ver a nota de CUSTO abaixo).
%
% Semantica contratada (CONTRATO §3.2, linha b4): CLASSIFICADOR DE CLASSE —
% "classe bom/ruim vs o arquivo corrente + L". As S linhas carregam:
%   pred_tipo      = "classe"
%   pred_classe    = "bom" se L>=0.5, "ruim" caso contrario
%   pred_confianca = L (saida escalar da sigmoide, CSEA.m:44)
%   mu_*/sigma_*/pred_score = NULL — o b4 nao tem cabeca-valor nem incerteza.
% A leitura L>=0.5 e a MESMA de b4_instrument.m:57 (as linhas de busca), para
% que sonda e busca fiquem na mesma regua.
%
% ⚠ O ROTULO E RELATIVO AS K REFERENCIAS RADIAIS DAQUELA GERACAO (GetOutput.m:
% "bom" <=> nao-pior em ao menos um objetivo para CADA uma das K refs), NAO ao
% arquivo. Logo o gabarito verdadeiro das S linhas NAO e derivavel so do f do
% artefato: a R4 precisa cruzar cada bloco com os `ref_ids` do `b4_gen` da MESMA
% geracao. Registrado no man.sigma_dict — sem isso as linhas sao inauditaveis.
%
% Por que ESTE ponto (CSEA.m:79, entre :78 e :80):
%   1. o fit terminou (:71 trainNetwork, :72 fecha tfit_s) — `net` e EXATAMENTE
%      o modelo que a busca usa em :83;
%   2. e ANTES da unica decisao do ciclo (SurrogateAssistedSelection, :83).
%      Entre :72 e :83 so ha :75-78 (TestPre/p0/p1), puro calculo de metrica;
%   3. e ANTES do 1o consumo de RNG pos-fit: os consumidores anteriores
%      (2x randperm em DataProcess.m:19-20 e o trainNetwork de :71, Shuffle
%      'every-epoch') ja rodaram; os seguintes (OperatorGA em SAS.m:22/:31/:50,
%      randperm em :42, randi em :58) vem todos de :83 em diante;
%   4. e ANTES de Problem.Evaluation (:85), onde o FEBudget levanta
%      PlatEMO:Termination — o hook pos-decisao (:91) NAO roda nesse caminho.
%
% RNG: `predict` e inferencia DETERMINISTA — a rede (CSEA.m:39-45) nao tem
% dropout e o batchNormalizationLayer usa TrainedMean/TrainedVariance. O
% save/restore acontece assim mesmo, dentro do SondaState (I1 e estrutural).

    % ── fe_treino_max (DI-09/A1) ─────────────────────────────────────────────
    % O treino e `TrainIn` — a subamostra 3/4 ESTRATIFICADA por classe
    % (DataProcess.m:19-21), nao o `Input`/|Arc|. Logo NAO vale o atalho
    % `bud.fe-1` do c141 (la o treino e o arquivo inteiro).
    % ⚠ NAO-MONOTONICO (regra 9 do R4 / DI-13.15): K e re-sorteado a cada
    % geracao, entao o ponto de maior fe_index pode cair no TestIn de uma
    % geracao e voltar ao TrainIn na seguinte — o valor OSCILA.
    % ⚠ CUSTO: `solutionIdOf` -> `keyOf` faz typecast+dec2hex sobre 8*D bytes
    % por linha; no ZDT1 sao ~3,3e5 chamadas/run. Por isso o valor e calculado
    % UMA vez por geracao AQUI e repassado — nunca recalculado no instrument.
    % `solution_id == fe_index` por construcao (FEBudget.m:98-99).
    ftm = [];                       % inicializado ANTES do early-return: o
                                    % b4_instrument usa `ftm` mesmo num run
                                    % SEM artefato de sonda (problema de piloto).
    d = Problem.data;
    bud = d.bud;
    m = -1;
    D = size(Problem.lower, 2);
    for i = 1:size(TrainIn, 1)
        sid = bud.solutionIdOf(TrainIn(i, 1:D));
        if sid > m, m = sid; end
    end
    if m >= 0, ftm = m; end

    if ~isfield(d, 'snd') || isempty(d.snd), return; end
    snd = d.snd;
    g = double(d.buf.gen);
    if g < 1, g = 1; end

    fn = @(Xs) b4_sonda_rows(net, Xs);
    snd.probe(g, fn, ftm, 'modelo', "FNN");
end


function rows = b4_sonda_rows(net, Xs)
% As S linhas da ③, NA ORDEM DO ARTEFATO (join por posicao — §3.1).
% Xs entra DIRETO no predict, espaco NATIVO — exatamente como `Next` entra em
% SAS.m:23. O z-score NAO e transformacao do adapter: e a featureInputLayer
% ('Normalization','zscore', CSEA.m:39), INTERNA a rede, com Mean/Std
% reajustados a cada geracao (rede NOVA por geracao) => espaco_modelo="cru".
    L = double(predict(net, Xs));
    L = L(:);
    classe = repmat("ruim", numel(L), 1);
    classe(L >= 0.5) = "bom";               % MESMA leitura de b4_instrument.m:57
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'pred_tipo', "classe", 'pred_classe', classe, ...
        'pred_confianca', L, 'modelo_flag', "FNN", ...
        'espaco_modelo', "cru");
end
