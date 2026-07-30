function c217_instrument(Problem, Arc, Next, delta, Error1, Error2, TestPre, tfit_s, ...
                         tbusca_s, tger_s, TrainIn, Output, Pmid, ArcDecPre)
% c217_instrument — instrumentacao POS-decisao do c217 PC-SAEA (chamada no fim de
% cada geracao pela PCSAEA.main patchada). NAO altera nenhuma decisao da busca
% (D97): so LE o que a geracao ja computou (Error1/2, estado, lote, TestPre) e
% emite as camadas de auditoria/analise. O gate objetivo (FE/4-saidas/CP-init)
% NAO depende deste conteudo; ele existe para a validacao MANUAL de fidelidade do
% autor (D97) e materializa os requisitos §17.2.1 (log da regra tripla), ③ (score
% ternario da acao corrigida — D17) e a serie de tempo §17.6.
%
% Fontes (via Problem.data, empacotado pelo run_c217):
%   .buf  RunBuffer  — coletor ②③/timing (o MESMO que o hook_output alimenta com ②)
%   .bud  FEBudget   — mapeia X real -> solution_id (dedup bit-a-bit, D57)
%   .log  double     — fid do .jsonl aberto (§17.5); escreve a linha da regra tripla
% Alinhamento de geracao: `g = buf.gen` — o hook (outputFcn) ja fez bumpGen no TOPO
% desta iteracao (NotTerminated), entao ② (hook) e ③/timing (aqui) partilham o mesmo g.

    d = Problem.data;
    buf = d.buf; bud = d.bud; fid = d.log;
    g = double(buf.gen);                        % geracao corrente (bumpada pelo hook)
    if g < 1, g = 1; end
    snd = [];
    if isfield(d, 'snd'), snd = d.snd; end      % [DI-09] pode nao existir

    % ── [DI-09/A1] fe_treino_max: maior fe_index no TREINO deste fit ──────────
    % LITERAL do §17.2 — o treino do c217 e TrainIn (subamostra 3/4 estratificada
    % de Input, DataProcess.m:14-22), nao o arquivo. Vale tanto p/ as linhas da
    % SONDA quanto p/ as da BUSCA (§9: o filtro in-sample x out-of-sample da R4
    % se aplica as DUAS).
    ftm = -1;
    for i = 1:size(TrainIn, 1)
        sid = bud.solutionIdOf(TrainIn(i, 1:Problem.D));
        if sid > ftm, ftm = sid; end
    end
    if ftm < 0, ftm = []; end

    % ── Estado da regra tripla CORRIGIDA (D17), reproduzindo as guardas do SAS ──
    % (so p/ LOG/score; a decisao real ja foi tomada pelo SAS com estas MESMAS
    %  condicoes. NaN>delta = false em ambas -> estado 3, o ramo aleatorio — L6.)
    if Error1 > delta
        estado = 1;  score = 1;  motivo = sprintf('Error1=%.4f > delta=%.2f -> estado 1 (maximiza)', Error1, delta);
    elseif Error2 > delta
        estado = 2;  score = -1; motivo = sprintf('Error2=%.4f > delta=%.2f -> estado 2 (minimiza/inverte)', Error2, delta);
    else
        estado = 3;  score = 0;
        if isnan(Error1) || isnan(Error2)
            motivo = 'regime-NaN (objetivo constante) -> estado 3 (aleatorio)';
        else
            motivo = sprintf('Error1=%.4f, Error2=%.4f <= delta=%.2f (contradicoes) -> estado 3 (aleatorio)', Error1, Error2, delta);
        end
    end
    % [c217-fix-log] UMA quantidade = pares onde a predicao forward==reverse
    % (rotulos iguais) = TestPre==1.5. O SPEC usa TRES nomes para ela: 'contradicao'
    % (M.4: rotulos iguais = erro ALEATORIO -> ignorar), 'empates' (S.3#4/S.7:
    % TestPre==1.5) e 'n_contradicoes' (§17.2.1, a spec DEDICADA do log da regra
    % tripla do c217). NAO ha 2a quantidade distinta definida no SPEC -> emito 1
    % campo so, 'n_contradicoes' (nome do §17.2.1). O `n_empates` duplicado (mesmo
    % valor, 2o nome) foi removido (sem duplicar — decisao do autor).
    n_contradicoes = sum(TestPre(:) == 1.5);
    lote      = size(Next, 1);
    arc_size  = numel(Arc);

    % ── ③ surrogate (schema C1): 1 linha 'score' por candidato SELECIONADO ──────
    % O candidato foi avaliado no ciclo (PCS:53) -> tem solution_id -> real_solution_id
    % SEMPRE presente (int32). pred_score = acao ternaria {-1,0,+1} da regra corrigida
    % (D17); pred_confianca = Error1 (confiabilidade da geracao); modelo = 'PNN-par'.
    srows = {};
    if lote > 0
        Dec = Next;                              % lote x D (nativo)
        for i = 1:lote
            sid = bud.solutionIdOf(Dec(i, :));   % >=0 pois o candidato foi avaliado
            rsi = int32([]);
            if sid >= 0, rsi = int32(sid); end
            srows{end+1} = RunBuffer.mkSurrogateRow(Dec(i, :), ...
                'real_solution_id', rsi, ...
                'pred_tipo', "score", 'pred_score', score, ...
                'pred_confianca', Error1, 'modelo_flag', "PNN-par", ...
                'fe_treino_max', ftm); %#ok<AGROW>
        end
    end

    % ── §17.6 timing: 1 evento de retreino do PNN por geracao ──────────────────
    % [DI-09] n_acumulado CORRIGIDO: o §17.6 define "nº de pontos reais no TREINO
    % naquele retreino" — era `numel(Arc)` (o ARQUIVO), que e outra grandeza e
    % achatava a curva de escalabilidade do c217. Passa a ser size(TrainIn,1).
    % O tamanho do arquivo continua auditavel no `arc_size` da linha c217_gen.
    % [DI-09/B-0b] tempo_geracao_s DESCONTA a sonda: o relogio da geracao mede o
    % custo do ALGORITMO (fit+busca+aval+overhead do proprio algoritmo), nao o
    % da instrumentacao. Incluir a sonda inflaria a analise de custo (§9) com o
    % preco do instrumento. Alinhado com a decisao D-1 do retrofit-R2 (Python) —
    % a MESMA coluna tem de significar a MESMA coisa nos dois stacks.
    tps = sonda_tempo(snd);
    timing = struct('n_acumulado', size(TrainIn, 1), 'tempo_fit_s', tfit_s, ...
                    'tempo_busca_s', tbusca_s, ...
                    'tempo_geracao_s', max(tger_s - tps, 0), ...
                    'tempo_pred_sonda_s', tps);

    % ── Emite ③ + timing no MESMO g do hook (② vem do hook_output) ─────────────
    view = struct('g', g, 'srows', {srows}, 'timing', timing);
    buf.addGeneration(view);

    % ── §17.2.1 + S.7.1/DI-10 — log da regra tripla + o minimo comum ──────────
    if ~isempty(fid) && fid > 2
        % [DI-10] n_best/n_worst do treino. `TrainOut` e DESCARTADO em PCSAEA.m:40
        % (`[TrainIn,~,...]`), mas a contagem e DETERMINISTICA a partir de `Output`,
        % que esta em escopo: DataProcess.m:14-19 mantem ceil(3/4) de cada estrato
        % (rotulo "melhor" = Output>1, vindo de CalFitnessPC.m:69-71). Substituto
        % EXATO, sem tocar no miolo stock. Invariante: n_best+n_worst == |TrainIn|.
        n_best  = ceil(3/4 * sum(Output(:) >  1));
        n_worst = ceil(3/4 * sum(Output(:) <= 1));

        rec = struct('ts', iso_now_c217(), 'rec', "c217_gen", ...
            'geracao', g, 'arc_size', arc_size, 'delta', delta, ...
            'p_mais', num_or_null(Error1), 'p_menos', num_or_null(Error2), ...
            'n_contradicoes', double(n_contradicoes), ...
            'estado', estado, 'motivo', string(motivo), ...
            'lote', double(lote), 'score', double(score), ...
            'tempo_fit_s', tfit_s, ...
            ... % ── DI-10: especificos do c217 (S.7.1) ──
            'n_best', double(n_best), 'n_worst', double(n_worst), ...
            'n_treino', double(size(TrainIn, 1)), ...
            'n_pares_treino', double(size(TrainIn,1)^2 - size(TrainIn,1)), ...
            'n_Pmid', double(size(Pmid, 1)), ...
            ... % [I-1] a IDENTIDADE da referencia, nao so o tamanho. O c217
            ... % logava APENAS `n_Pmid` (0/25 celulas com os ids): sem saber
            ... % QUAIS pontos formavam o Pmid daquela geracao, o rotulo
            ... % verdadeiro dos 2.000 pontos da sonda e irreconstituivel e a
            ... % qualidade do classificador vira NAO-MENSURAVEL — irrecuperavel
            ... % a posteriori. Molde: o b4 (b4_instrument.m:91-95). ~2 linhas,
            ... % `bud.solutionIdOf` e deterministico e nao consome RNG.
            'pmid_ids', pmid_ids_c217(bud, Pmid), ...
            ... % [I-5] prevalencia das classes no TREINO desta geracao — sem
            ... % ela nao se separa "classificador ruim" de "problema
            ... % desbalanceado". O c217 e ternario {-1,0,+1} (Output).
            'y_treino_dist', y_treino_dist_c217(Output), ...
            ... % ── DI-10: minimo comum dos 21 (S.7.1) ──
            'fe', bud.fe, ...
            'f_best', min(Arc.objs, [], 1), ...
            'n_front1', double(n_front1_de(Arc)), ...
            'modelo_hp', struct('spread', 0.1925), ...
            'fe_treino_max', num_or_null(opt_nan(ftm)), ...
            'tempo_busca_s', tbusca_s, 'tempo_geracao_s', tger_s, ...
            'dist_min_arquivo', dist_min_arq(Next, ArcDecPre));
        try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
    end
end


function t = sonda_tempo(snd)
% [DI-09] Tempo da sonda desta geracao (0 se nao rodou) -> coluna ④.
    if isempty(snd), t = 0; else, t = snd.takePendingTime(); end
end

function n = n_front1_de(Arc)
% [DI-10] |ND| corrente. Nenhuma variavel do c217 o guarda (a selecao usa o
% fitness SPEA2 do ESCalFitness, nao NDSort) -> derivado. NDSort e determinista,
% nao consome RNG e nao muta estado.
    try
        [FrontNo, ~] = NDSort(Arc.objs, 1);
        n = sum(FrontNo == 1);
    catch
        n = NaN;
    end
end

function dmin = dist_min_arq(Next, ArcDecPre)
% [DI-10/B3] Distancia de CADA infill ao arquivo ANTERIOR (espaco de decisao).
% Usa o snapshot PRE-infill: em PCSAEA.m:64 o `Arc` ja inclui os proprios
% infills, o que daria distancia 0 (degenerada).
    if isempty(Next) || isempty(ArcDecPre), dmin = []; return; end
    try
        dmin = min(pdist2(Next, ArcDecPre), [], 2).';
    catch
        dmin = [];
    end
end

function v = opt_nan(x)
    if isempty(x), v = NaN; else, v = double(x); end
end

function v = num_or_null(x)
% NaN -> [] (=> null no jsonencode), mantendo o log parseavel (regime-NaN L6).
    if isnan(x), v = []; else, v = double(x); end
end

function s = iso_now_c217()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end


function ids = pmid_ids_c217(bud, Pmid)
% [I-1] Os solution_id das linhas do Pmid (a referencia do gate). -1 = ponto
% que ainda nao foi avaliado na funcao real (nao tem id).
    ids = [];
    try
        if isempty(Pmid), return; end
        n = size(Pmid, 1);
        ids = -ones(1, n);
        for i = 1:n
            ids(i) = bud.solutionIdOf(Pmid(i, :));
        end
    catch
        ids = [];   % instrumentacao NUNCA derruba o run (D97)
    end
end

function d = y_treino_dist_c217(Output)
% [I-5] Distribuicao das classes no alvo de treino do PNN par-a-par.
% O `Output` do c217 e ternario: -1 (pior), 0 (empate/incomparavel), +1 (melhor).
    d = [];
    try
        y = double(Output(:));
        if isempty(y), return; end
        d = struct('n', numel(y), ...
                   'classe_menos1', sum(y < 0), ...
                   'classe_zero',   sum(y == 0), ...
                   'classe_mais1',  sum(y > 0));
    catch
        d = [];
    end
end
