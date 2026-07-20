function piso_instrument(Algorithm, Problem, buf, bud, fid, alg, tger_s)
% piso_instrument — instrumentacao dos 4 PISOS ONLINE (nsga2/nsga3/moead/smsemoa).
% Chamado pelo `piso_hook` a cada geracao, DEPOIS do hook_output (que ja fez o
% bumpGen e emitiu a ②). READ-ONLY: os pisos sao STOCK do PlatEMO 4.15, com ZERO
% patch por design — nada aqui toca o algoritmo, tudo sai de `Algorithm.result`.
%
% UM arquivo para os 4: o runner tambem e um so (`run_piso`), parametrizado por
% `piso_spec`. O RECORD, porem, e `<alg>_gen` (nsga2_gen, nsga3_gen, ...) porque
% o CONTRATO §6 nomeia o registro assim — a auditoria a jusante espera esse nome.
%
% O QUE O PISO TEM E O QUE NAO TEM (CONTRATO §6.1, linha "pisos", + DI-13.7):
%   NAO TEM  sonda (nao ha modelo a sondar) · modelo_hp · dist_min_arquivo
%            (o campo pressupoe infill guiado por modelo) · camada ③.
%   TEM      camada ④ por geracao, e e o CUSTO-BASELINE do estudo:
%            tempo_geracao_s REAL; tempo_fit_s = NULL [DI-13.2].
%   DI-10    n_front1 · f_best[] · ideal/nadir da pop por geracao · os VETORES
%            de decomposicao do moead/nsga3 no HEADER (deterministicos, 1x —
%            emitidos pelo run_piso, nao aqui).
%
% ⚠ `tempo_busca_s` e `tempo_pred_sonda_s` saem NULL, nao 0. Um MOEA puro nao tem
% fase de "aquisicao" separavel: gravar 0 diria "a busca custou zero", e gravar o
% ciclo inteiro poria OUTRA grandeza numa coluna que os 21 compartilham — a
% mesma armadilha que a DI-13.2 evitou no tempo_fit_s. O breakdown do piso
% continua computavel pelos agregados do manifesto.

    g = double(buf.gen);
    if g < 1, return; end

    PopObj = [];
    try
        pop = Algorithm.result{end, 2};
        PopObj = pop.objs;
    catch
    end
    if isempty(PopObj), return; end

    % ── DI-10: os agregados da populacao real desta geracao ──────────────────
    f_best = min(PopObj, [], 1);          % == ideal (min por objetivo)
    nadir_pop = max(PopObj, [], 1);       % literal do CONTRATO:305 ("da pop")
    n_front1 = NaN;
    nadir_front1 = [];
    try
        fno = NDSort(PopObj, 1);
        n_front1 = sum(fno == 1);
        if any(fno == 1)
            nadir_front1 = max(PopObj(fno == 1, :), [], 1);
        end
    catch
    end

    if isempty(fid) || fid <= 2, return; end
    rec = struct('ts', iso_now_piso(), 'rec', string(alg) + "_gen", ...
        'geracao', g, 'fe', bud.fe, ...
        'n_pop', double(size(PopObj, 1)), ...
        ... % ── DI-10 dos pisos (CONTRATO §6.1) ──
        'n_front1', double(n_front1), ...
        'f_best', f_best, ...
        'ideal', f_best, ...              % identico a f_best por definicao;
        ...                               % emitido sob os DOIS nomes porque o
        ...                               % contrato pede "ideal/nadir" e o
        ...                               % minimo comum pede "f_best[]".
        'nadir_pop', nadir_pop, ...
        'nadir_front1', nadir_front1, ... % superconjunto: a normalizacao/HV da
        ...                               % R4 costuma querer o nadir do FRONT,
        ...                               % nao o da populacao inteira.
        'tempo_geracao_s', tger_s);
    try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
end


function s = iso_now_piso()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
