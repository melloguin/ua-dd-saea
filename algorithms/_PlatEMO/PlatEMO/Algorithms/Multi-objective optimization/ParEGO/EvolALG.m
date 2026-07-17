function [PopDec,info] = EvolALG(Problem,PCheby,Dec,model,IFEs)
% Solution update in ParEGO, where a solution with the best expected
% improvement is re-evaluated
%
% [R1-b1] 2o output `info` (instrumentacao SO-LEITURA — D97; padrao do
% KrigingSelect do b3): pop FINAL scorada do GA interno + y/s/EI por candidato
% (DEF-C2 §17.4: "a populacao final do otimizador de aquisicao por iteracao de
% BO"), Gbest, trace do melhor EI por geracao interna e contadores dos guards
% (mse<0 — P2/L8; EI NaN). NENHUMA decisao alterada: o bug do torneio (:16)
% fica (CODIGO K.3), sort/selecao/decremento de IFEs intactos.

%------------------------------- Copyright --------------------------------
% Copyright (c) 2026 BIMK Group. You are free to use the PlatEMO for
% research purposes. All publications which use this platform or any code
% in the platform should acknowledge the use of "PlatEMO" and reference "Ye
% Tian, Ran Cheng, Xingyi Zhang, and Yaochu Jin, PlatEMO: A MATLAB platform
% for evolutionary multi-objective optimization [educational forum], IEEE
% Computational Intelligence Magazine, 2017, 12(4): 73-87".
%--------------------------------------------------------------------------

% This function is written by Cheng He

    Off   = [OperatorGA(Problem,Dec(TournamentSelection(2,size(Dec,1),PCheby),:));OperatorGA(Problem,Dec,{0,0,1,20})];
    N     = size(Off,1);
    EI    = zeros(N,1);
    Gbest = min(PCheby);
    E0    = inf;
    % [R1-b1] acumuladores de instrumentacao (so leitura, D97).
    n_mse_neg = 0;                       % guard P2 (L8) disparos: mse<0 do dacefit
    e0_trace  = [];                      % melhor EI por geracao interna
    n_iters   = 0;
    best_y    = NaN;  best_s = NaN;      % mu/sigma do Best selecionado
    last      = struct('dec',[],'y',[],'s',[],'ei',[]);   % pop FINAL scorada
    while IFEs > 0
        drawnow('limitrate');
        ys = zeros(N,1);                 % [R1-b1] mu por candidato (:23-27)
        ss = zeros(N,1);                 % [R1-b1] sigma por candidato
        for i = 1 : N
            [y,~,mse] = predictor(Off(i,:),model);
            if mse < 0                   % [R1-b1] P2/L8: conta o disparo do guard
                n_mse_neg = n_mse_neg + 1;
            end
            s         = sqrt(max(mse,0));
            EI(i)     = -(Gbest-y)*normcdf((Gbest-y)/s)-s*normpdf((Gbest-y)/s);
            ys(i)     = y;               % [R1-b1]
            ss(i)     = s;               % [R1-b1]
        end
        [~,index] = sort(EI);
        if EI(index(1)) < E0
            Best   = Off(index(1),:);
            E0     = EI(index(1));
            best_y = ys(index(1));       % [R1-b1]
            best_s = ss(index(1));       % [R1-b1]
        end
        % [R1-b1] snapshot da pop scorada DESTA geracao interna (sobrescreve: ao
        % sair do while, `last` = a populacao FINAL do otimizador de aquisicao).
        n_iters  = n_iters + 1;
        e0_trace(end+1) = EI(index(1)); %#ok<AGROW>
        % So os candidatos SCORADOS (1:N — o loop stock so avalia os N primeiros;
        % linhas excedentes de um Off re-gerado maior nunca ganham y/s/EI).
        last.dec = Off(1:min(N,size(Off,1)),:);
        last.y   = ys;  last.s = ss;  last.ei = EI;
        Parent = Off(index(1:ceil(N/2)),:);
        Off    = [OperatorGA(Problem,Parent(TournamentSelection(2,size(Parent,1),EI(index(1:ceil(N/2)))),:));OperatorGA(Problem,Parent,{0,0,1,20})];
        IFEs   = IFEs - size(Off,1);
    end
    PopDec = Best;
    % [R1-b1] info p/ o b1_instrument (nada aqui altera a busca).
    info = struct('pop', last, 'gbest', Gbest, 'e0', E0, ...
                  'best_y', best_y, 'best_s', best_s, ...
                  'n_iters', n_iters, 'e0_trace', e0_trace, ...
                  'n_mse_neg', n_mse_neg, 'n_ei_nan', sum(isnan(last.ei)));
end