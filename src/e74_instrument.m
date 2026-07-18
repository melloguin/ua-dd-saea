function e74_instrument(Problem, tag, inst, x_cand, aceito_mask)
% e74_instrument — instrumentacao POS-decisao do e74 CLMEA (chamada pela
% CLMEA.main patchada, na ARVORE 4.1 propria — D95/N.0-4.1). NAO altera decisao
% nenhuma da busca (D97): so LE o que cada bloco ja computou (structs inst_e74
% de leitura pura) e emite ③ + .jsonl §17.5/S.7 + timing §17.6. O gate objetivo
% (FE/4-saidas/CP-init) NAO depende deste conteudo; ele existe p/ a validacao
% MANUAL do autor (D97).
%
% tags (1 chamada por bloco, na ordem do ciclo):
%   'boot' — bootstrap de extremos (M fits RBF + DE no surrogate; ate M FEs).
%   's1'   — ClassifierSelect: pop final do rank-learning + classe PNN por
%            membro; pseudo-σ = dist minima em DECISAO ao arquivo (dist_dec).
%   's2'   — Hv_Select: pop final da DE interna + μ_RBF (rede global no arquivo
%            inteiro); pseudo-σ = HV_gain D74-normalizado (so pseudo-front).
%   's3'   — Local_infill: pop final da busca local + ŷ (RBF local); pseudo-σ =
%            dist minima em OBJETIVOS ao arquivo (Eucli — "incerteza geometrica").
%   'stall'— D60-c: ciclo(s) sem consumir FE (saldo congelado) — SO loga.
%
% ③ (C1/B16.4 — hibrido do e74, 1 tabela): pred_tipo HONESTO por linha ("classe"
% p/ s1/PNN, "valor" p/ boot/s2/s3/RBF — nenhuma linha tem as duas cabecas ao
% mesmo tempo; a estrategia vai no modelo_flag). sigma_0 = o pseudo-σ da
% estrategia da linha (semantica por estrategia — dicionario DEF-C4 no
% manifesto). real_solution_id nullable (double+NaN — fallback R1-00): presente
% p/ membros ja avaliados (pops contem pontos do arquivo) e p/ o candidato
% ACEITO do bloco (instrument roda APOS a Evaluation).
%
% Alinhamento de geracao: g = buf.gen — o hook_output (outputFcn) ja fez o
% bumpGen no NotTerminated que PRECEDE o bloco (padrao c141): ② (hook) e
% ③/timing (aqui) partilham o g.

    d = Problem.data;
    buf = d.buf;  bud = d.bud;  fid = d.log;
    g = double(buf.gen);
    if g < 1, g = 1; end

    switch tag
        case 'stall'
            guard_line(fid, 'saldo_congelado', g, 'ciclos_sem_fe', inst.ciclos, ...
                'fe', bud.fe);
            return;

        case 'boot'
            srows = {};
            M = double(Problem.M);
            for i = 1:size(inst.x_ext, 1)
                mu_v = NaN(1, M);  mu_v(i) = inst.f_ext(i);   % DE minimizou SO o obj i
                srows{end+1} = srow(bud, inst.x_ext(i,:), ...
                    'mu', mu_v, 'pred_tipo', "valor", ...
                    'modelo_flag', "RBF-global(boot)"); %#ok<AGROW>
            end
            view = struct('g', g, 'srows', {srows}, 'timing', struct( ...
                'n_acumulado', inst.n_treino, 'tempo_fit_s', inst.tempo_fit_s, ...
                'tempo_busca_s', inst.tempo_busca_s));
            buf.addGeneration(view);
            if inst.rejeitados > 0
                guard_line(fid, 'extremo_rejeitado', g, 'n', inst.rejeitados, ...
                    'motivo', "dedup eps STOCK: extremo a <1e-5 do arquivo — slot perdido, 0 FE");
            end
            jline(fid, struct('ts', tnow(), 'rec', "e74_boot", 'geracao', g, ...
                'fe', bud.fe, 'aceitos', inst.aceitos, 'rejeitados', inst.rejeitados, ...
                'dist_ext', inst.dist_ext, 'f_ext', inst.f_ext, 'spr', inst.spr, ...
                'n_treino', inst.n_treino, 'tempo_fit_s', inst.tempo_fit_s, ...
                'tempo_busca_s', inst.tempo_busca_s));
            return;
    end

    % ── blocos s1/s2/s3 ──────────────────────────────────────────────────────
    n_cand = size(x_cand, 1);
    n_ok   = sum(aceito_mask);
    slot_perdido = n_cand - n_ok;

    srows = {};
    switch tag
        case 's1'
            for k = 1:size(inst.x_pop, 1)
                srows{end+1} = srow(bud, inst.x_pop(k,:), ...
                    'sigma', inst.dist_dec(k), 'pred_tipo', "classe", ...
                    'pred_classe', "nivel_" + string(inst.classe_pop(k)), ...
                    'modelo_flag', "PNN(s1)"); %#ok<AGROW>
            end
        case 's2'
            % HV_gain so existe p/ os membros do pseudo-front (score CalHV D74).
            gain = NaN(size(inst.x_pop, 1), 1);
            sc   = NaN(size(inst.x_pop, 1), 1);
            if ~isempty(inst.score)
                fidx = find(inst.front_mask);
                m = min(numel(fidx), numel(inst.score));
                sc(fidx(1:m))   = inst.score(1:m);
                gain(fidx(1:m)) = inst.score(1:m) - inst.hv_base;
            end
            for k = 1:size(inst.x_pop, 1)
                srows{end+1} = srow(bud, inst.x_pop(k,:), ...
                    'mu', inst.y_pop(k,:), 'sigma', gain(k), ...
                    'pred_score', sc(k), 'pred_tipo', "valor", ...
                    'modelo_flag', "RBF-global(s2)"); %#ok<AGROW>
            end
        case 's3'
            for k = 1:size(inst.x_pop, 1)
                srows{end+1} = srow(bud, inst.x_pop(k,:), ...
                    'mu', inst.y_pop(k,:), 'sigma', inst.eucli(k), ...
                    'pred_tipo', "valor", 'modelo_flag', "RBF-local(s3)"); %#ok<AGROW>
            end
    end
    view = struct('g', g, 'srows', {srows}, 'timing', struct( ...
        'n_acumulado', inst.n_treino, 'tempo_fit_s', inst.tempo_fit_s, ...
        'tempo_busca_s', inst.tempo_busca_s));
    buf.addGeneration(view);

    % ── guardas §17.5 ────────────────────────────────────────────────────────
    if slot_perdido > 0
        guard_line(fid, 'dedup_slot_perdido', g, 'estrategia', string(tag), ...
            'n', slot_perdido, ...
            'motivo', "dedup eps=1e-5 STOCK rejeitou o candidato SEM gastar FE (slot perdido, nao o orcamento)");
    end
    if n_cand == 0
        guard_line(fid, 'cand_vazio', g, 'estrategia', string(tag), ...
            'motivo', "estrategia nao produziu candidato (edge stock — ex.: rank-learning sem nivel-1)");
    end
    if strcmp(tag, 's2') && inst.range0
        guard_line(fid, 'hv_range0', g, ...
            'motivo', "front-1 do arquivo degenerado em >=1 coordenada (Ymax-Ymin<=0) — norm D74 vira NaN; edge fora do paper, NAO consertado (so logado)");
    end

    % ── linha 'e74_gen' (S.7) por bloco ──────────────────────────────────────
    rec = struct('ts', tnow(), 'rec', "e74_gen", 'geracao', g, ...
        'estrategia', str2double(tag(2)), 'fe', bud.fe, 'arquivo', bud.fe, ...
        'n_cand', n_cand, 'aceito', n_ok, 'slot_perdido', slot_perdido, ...
        'spr', inst.spr, 'n_treino', inst.n_treino, ...
        'tempo_fit_s', inst.tempo_fit_s, 'tempo_busca_s', inst.tempo_busca_s);
    switch tag
        case 's1'
            rec.count = inst.count;
            rec.frac_nivel1 = inst.frac_n1;
            rec.n_desalinhado = inst.n_desalinhado;   % mascara(Offspring)×Parent (fix opcional NAO aplicado)
            rec.flag_copia = inst.flag_copia;
            rec.cand_classe = inst.cand_classe(:).';
            rec.cand_dist_dec = inst.cand_dist(:).';
        case 's2'
            rec.Ymin = inst.Ymin;  rec.Ymax = inst.Ymax;
            rec.range0 = inst.range0;
            rec.hv_base = inst.hv_base;
            rec.n_front = numel(inst.score);
            rec.score = resumo(inst.score);
            if ~isempty(inst.score) && ~isempty(inst.chosen)
                rec.score_best = inst.score(inst.chosen);
                rec.hv_gain = inst.score(inst.chosen) - inst.hv_base;
            end
        case 's3'
            rec.n_front = sum(inst.front_mask);
            rec.cand_eucli = inst.cand_eucli(:).';
    end
    jline(fid, rec);
end


function r = srow(bud, x, varargin)
% Linha ③ com real_solution_id nullable resolvido AQUI (dedup bit-a-bit D57):
% presente so se o x ja e uma solucao real (membro do arquivo / infill aceito).
    sid = bud.solutionIdOf(x);
    rsi = [];
    if sid >= 0, rsi = int32(sid); end
    r = RunBuffer.mkSurrogateRow(x, 'real_solution_id', rsi, varargin{:});
end

function guard_line(fid, name, g, varargin)
% Evento de guarda no .jsonl (formato do logger do FEBudget/c141_instrument).
    if isempty(fid) || fid <= 2, return; end
    s = struct('ts', tnow(), 'rec', "guard", 'name', string(name), 'geracao', g);
    for i = 1:2:numel(varargin)
        s.(varargin{i}) = varargin{i+1};
    end
    try, fprintf(fid, '%s\n', jsonencode(s)); catch, end
end

function jline(fid, rec)
    if isempty(fid) || fid <= 2, return; end
    try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
end

function r = resumo(v)
    if isempty(v)
        r = [];
    else
        r = struct('min', min(v), 'med', median(v), 'max', max(v));
    end
end

function s = tnow()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
