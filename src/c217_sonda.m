function c217_sonda(Problem, net, Pmid, Error1, TrainIn)
% c217_sonda — bloco da SONDA CANONICA (DI-09/§17.2.2) do c217 PC-SAEA.
% Chamado de PCSAEA.main ENTRE o calculo do Error2 e a selecao assistida
% (o ultimo ponto apos o fit e ANTES de qualquer decisao ou consumo de RNG).
% READ-ONLY: nao altera nenhuma decisao da busca (D97) e nao gasta FE.
%
% Semantica contratada (CONTRATO_DE_DADOS §3.2, linha c217): o modelo responde
% o SCORE TERNARIO do ponto vs a referencia corrente (Pmid), com
% pred_confianca = Error1 (a confiabilidade da geracao).
%
% Por que ESTE ponto (PCSAEA.m, entre :50 e :53):
%   1. o fit da geracao ja ocorreu (:43) — `net` esta treinado;
%   2. `Pmid` (:38) e a referencia CORRENTE, a mesma que a busca usa em :46;
%   3. `Error1` (:49) ja existe -> pred_confianca disponivel;
%   4. `TrainIn` (:40) ainda em escopo -> fe_treino_max calculavel;
%   5. e o ULTIMO ponto antes da 1a decisao (:53 -> SurrogateAssistedSelectionPC,
%      onde o RNG passa a ser consumido em :14/:28/:46/:57).
%
% RNG: `lastpredict` (RBFNNPC.m:53-82) e 100% deterministico — so `sim`,
% `vec2ind` e aritmetica, zero rand/randn/randperm/randi. Ainda assim o
% save/restore acontece SEMPRE, dentro do SondaState: o invariante e
% estrutural, nao uma dependencia de auditoria do `sim`.

    d = Problem.data;
    if ~isfield(d, 'snd') || isempty(d.snd), return; end     % run sem sonda
    snd = d.snd;  buf = d.buf;  bud = d.bud;
    g = double(buf.gen);                       % o hook ja bumpou no topo do ciclo
    if g < 1, g = 1; end

    % ── fe_treino_max (DI-09/A1) ─────────────────────────────────────────────
    % LITERAL do §17.2: "maior fe_index no TREINO do modelo no momento do fit".
    % O treino do c217 e `TrainIn` — subamostra 3/4 ESTRATIFICADA de Input
    % (DataProcess.m:14-22) —, nao o arquivo; logo o valor NAO e monotonico
    % entre geracoes, e e essa a semantica pedida (o filtro in-sample da R4 tem
    % de refletir o que o modelo de fato viu).
    % solution_id == fe_index por construcao (FEBudget.m:90-91).
    ftm = c217_ftm(bud, TrainIn, Problem.D);

    % ── o disparo (cadencia k=2 + arm p/ a sonda final pos-Solve) ────────────
    fn = @(Xs) c217_sonda_rows(net, Xs, Problem.D, Pmid, Error1);
    snd.probe(g, fn, ftm, 'modelo', "PNN-par");
end


function ftm = c217_ftm(bud, TrainIn, D)
    ftm = -1;
    for i = 1:size(TrainIn, 1)
        sid = bud.solutionIdOf(TrainIn(i, 1:D));   % read-only, sem RNG, 0 FE
        if sid > ftm, ftm = sid; end
    end
    if ftm < 0, ftm = []; end                      % => NULL na ③
end


function rows = c217_sonda_rows(net, Xs, D, Pmid, Error1)
% As S=2000 linhas da ③, NA ORDEM DO ARTEFATO.
%
% ⚠ A ordem aqui e semanticamente carregada por DOIS motivos independentes:
%   (a) o join com o gabarito e POR POSICAO (a ③ nao tem coluna sonda_id);
%   (b) RBFNNPC.m:59-62 empareilha a linha i com Preference(mod(i+numberP,numberP)+1,:)
%       -> reordenar mudaria os PROPRIOS scores, nao so o join.
% Por isso Xs vai DIRETO ao preditor: sem sort, sem unique, sem clamp.
    Ys = net.lastpredict(Xs, D, Pmid, 0);          % flag=0 => ternario {-1,0,+1}
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'pred_tipo', "score", 'pred_score', Ys(:), ...
        'pred_confianca', Error1, ...              % NaN (regime-NaN) => NULL
        'modelo_flag', "PNN-par", 'espaco_modelo', "cru");
end
