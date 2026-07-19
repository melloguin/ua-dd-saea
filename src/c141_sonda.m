function c141_sonda(Problem, RModel, mS, tfit_s)
% c141_sonda — bloco da SONDA CANONICA (DI-09/§17.2.2) do c141 MMRAEA.
% Chamado de MMRAEA.main logo APOS o fit dos M+2 RBFs e ANTES de qualquer
% decisao. READ-ONLY: nao altera a busca (D97) e nao gasta FE.
%
% Semantica contratada (CONTRATO_DE_DADOS §3.2): mu POR OBJETIVO, SEM sigma —
% o RBF do c141 e um INTERPOLANTE (rbf_predict devolve 1 escalar por ponto,
% sem estimativa de incerteza). E exatamente a distincao VAR-GP x ERR-EMP do
% eixo de medicao: sigma_* fica NULL.
%
% Por que ESTE ponto (MMRAEA.m, apos :48, antes de :49):
%   1. o fit completo do ciclo terminou (Dmodel :37, RModel :41-42, Fmodel :47);
%   2. e ANTES de EAOptimization (:52) e InfillStrategy (:54) — nada da busca
%      foi consumido, e os UNICOS consumidores de RNG (CSO.m:3/:19-20/:29-30 e
%      OperatorGA) vem depois;
%   3. e ANTES de Problem.Evaluation (:60), onde o FEBudget levanta
%      PlatEMO:Termination no hard-stop — o hook pos-decisao de :75 NAO roda
%      nesse caminho, este roda.
%
% ⚠ PAREAMENTO (RModel{j}, mS) — NAO "consertar": `mS` e reatribuido a cada i
% no laco MMRAEA.m:40 e so o do i=M sobrevive; o codigo oficial usa ESSE unico
% mS como Xtr de TODOS os RModel{j} (EAOptimization.m:24/:44). E consistente
% porque o dsmerge decide so por distancias de S, e S=A1Dec e o mesmo para todo
% i => mS identico para todos os objetivos. A sonda REPLICA o pareamento da
% busca; qualquer "correcao" aqui mediria um modelo que o algoritmo nao usa.
%
% RNG: rbf_predict (:59-94) e pura aritmetica — zero rand/randn. O save/restore
% acontece assim mesmo, dentro do SondaState.

    d = Problem.data;
    if ~isfield(d, 'snd') || isempty(d.snd), return; end
    snd = d.snd;  buf = d.buf;  bud = d.bud;
    g = double(buf.gen);
    if g < 1, g = 1; end

    % ── fe_treino_max (DI-09/A1) ─────────────────────────────────────────────
    % O treino e A1 INTEIRO (UpdataArchive.m:16-20 so faz unique/dedup, NUNCA
    % poda) e solution_id == fe_index (FEBudget.m:90-91) => o maior fe_index no
    % treino e bud.fe-1, lido ANTES da Evaluation deste ciclo (MMRAEA.m:60).
    ftm = bud.fe - 1;
    if ftm < 0, ftm = []; end

    % hp efetivos do RBF (DI-10/B1) — os modelos sao construidos com 2 args, logo
    % valem os defaults do rbf_build: MQ, c=1, poly=0.
    hp = struct('bf_type', string(field_or_c141(RModel{1}, 'bf_type', 'MQ')), ...
                'bf_c',    double(field_or_c141(RModel{1}, 'bf_c', 1)), ...
                'poly',    double(field_or_c141(RModel{1}, 'poly', 0)), ...
                'n',       double(field_or_c141(RModel{1}, 'n', size(mS,1))), ...
                'tempo_fit_s', tfit_s);

    fn = @(Xs) c141_sonda_rows(RModel, mS, Xs, Problem.M);
    snd.probe(g, fn, ftm, 'modelo', "RBF-MQ3", 'hp', hp);
end


function rows = c141_sonda_rows(RModel, mS, Xs, M)
% As S=2000 linhas da ③, NA ORDEM DO ARTEFATO (join por posicao).
% Xs vai DIRETO ao preditor: espaco NATIVO, sem normalizacao — o rbf_build nao
% escala X (so centra Y em meanY), entao o parquet da sonda entra sem conversao.
    n = size(Xs, 1);
    MU = zeros(n, M);
    for j = 1:M
        MU(:, j) = rbf_predict(RModel{j}, mS, Xs);   % lote nativo (rbf_predict.m:55-94)
    end
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'mu', MU, ...                      % sigma ausente => NULL (interpolante)
        'pred_tipo', "valor", 'modelo_flag', "RBF-MQ3", ...
        'espaco_modelo', "nativo");
end


function v = field_or_c141(s, f, d)
    if isstruct(s) && isfield(s, f), v = s.(f); else, v = d; end
end
