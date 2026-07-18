function e103_instrument(fase, Global, varargin)
% e103_instrument — instrumentacao READ-ONLY do IBEA-MS offline (R1-e103).
% Chamada pelo IBEAMS.m patchado (L.15) em 3 pontos, SEMPRE guardada por
% isfield(Global,'inst'): NENHUMA decisao da busca e alterada (D97) — so LE o
% que o ciclo ja computou e emite as camadas de auditoria/analise. O gate
% objetivo (①=dataset/4-saidas/CP-init) NAO depende deste conteudo; ele existe
% p/ a validacao MANUAL do autor (D97).
%
% Pontos de chamada (fase):
%   'setup'      — apos construir os DOIS modelos (treino UNICO — offline):
%                  linha 'e103_setup' no .jsonl (centros k-means D93, spread
%                  5*max(pdist), θ/σ² do DACE por objetivo, tempos de fit,
%                  ultimo warning capturado — a quase-singularidade da RBFN e
%                  ESPERADA: documentada e registrada, nunca silenciada).
%   'gen'        — fim de CADA ciclo (pos-selecao; a "pos :46" da L.15):
%                  ② membership dos MEMBROS DO DATASET na populacao
%                  selecionada (solutionIdOf — bit-exato; candidatos nascidos
%                  do modelo nao tem id real);
%                  ③ (DEF-C2 offline: pop-surrogate selecionada, TODAS as
%                  geracoes) com o μ dos DOIS modelos por membro (C4):
%                  1 linha Kriging-DACE (mu=predictor, sigma=sqrt(max(MSE,0)))
%                  + 1 linha RBFN (mu=RBFN_cal INCONDICIONAL — mesmo quando o
%                  Kriging liderou; RBFN nao produz σ -> NULL). Re-predicao
%                  read-only dos 2 modelos sobre os decs selecionados — as
%                  linhas ③ sao a visao CRUA de cada modelo (membros do
%                  dataset inclusos: DACE interpola ≈exato, MSE≈0);
%                  linha 'e103_gen' no .jsonl: CurGen, KFlag (Kriging↔RBFN),
%                  estatisticas de √MSE do conjunto JULGADO (o input do
%                  JudgeModel) e do subconjunto surrogate, n_ds_membros.
%   'busca_fim'  — apos o laco (99 geracoes): a UNICA linha da serie §17.6
%                  (offline treino-unico): n_acumulado = n_dataset,
%                  tempo_fit_s = kriging+RBFN, tempo_busca_s = laco IBEA.
%
% Fontes (Global.inst, empacotado pelo run_e103): .buf RunBuffer · .bud
% FEBudget (X -> solution_id, D57) · .fid do .jsonl. RNG: NENHUM consumo
% (predictor/RBFN_cal/solutionIdOf/estatisticas sao deterministicos).

    inst = Global.inst;
    buf = inst.buf; bud = inst.bud; fid = inst.fid;

    switch fase
        case 'setup'
            [KModel, Rnets, tempo_krig, tempo_rbfn] = deal(varargin{:});
            [wmsg, wid] = lastwarn;   % run_e103 limpa lastwarn antes do IBEAMS
            th_min = zeros(1, Global.M); th_max = zeros(1, Global.M);
            th_med = zeros(1, Global.M); s2 = zeros(1, Global.M);
            for j = 1:Global.M
                th = KModel(j).md.theta(:).';
                th_min(j) = min(th); th_max(j) = max(th); th_med(j) = mean(th);
                s2(j) = mean(KModel(j).md.sigma2(:));
            end
            if ~isempty(wid) || ~isempty(wmsg)
                guard_line(fid, 'quase_singular_setup', 0, ...
                    'warn_id', string(wid), 'warn_msg', string(wmsg), 'motivo', ...
                    ['warning durante o treino unico (kmeans/dacefit/mldivide da RBFN) — ' ...
                     'ESPERADO com spread 5*max(pdist) (kernel quase-plano); documentado, nao silenciado']);
            end
            rec = struct('ts', iso_now_e103(), 'rec', "e103_setup", ...
                'n_dataset', Global.n_dataset, ...
                'center_num', size(Rnets.centers, 1), ...
                'rbfn_spread', Rnets.sigma, ...
                'rbfn_kernel', string(Rnets.name), ...
                'krig_theta_min', th_min, 'krig_theta_max', th_max, ...
                'krig_theta_media', th_med, 'krig_sigma2', s2, ...
                'tempo_fit_kriging_s', tempo_krig, 'tempo_fit_rbfn_s', tempo_rbfn, ...
                'warn_setup', string(wid));
            jline(fid, rec);

        case 'gen'
            [KModel, Rnets, CurGen, KFlag, Population, MSE, MSE_julgada] = ...
                deal(varargin{:});
            SelDecs = decs(Population);              % N x D (pos-selecao)
            nsel = size(SelDecs, 1);

            % ② membership: SO os membros do DATASET (solucoes reais) na pop.
            sids = -ones(nsel, 1);
            for i = 1:nsel
                sids(i) = bud.solutionIdOf(SelDecs(i, :));
            end
            pop_ids = sids(sids >= 0);

            % ③ μ dos DOIS modelos (re-predicao read-only sobre os decs).
            [KObjs, KMSE] = kriging_cal(SelDecs, KModel, Global);
            KObjs = objs(KObjs);
            n_mse_neg = nnz(KMSE < 0);
            if n_mse_neg > 0
                guard_line(fid, 'mse_neg', CurGen, 'n', n_mse_neg, 'motivo', ...
                    'MSE<0 do predictor DACE (erro float em ponto de treino) -> sqrt(max(mse,0)) so na ③ (mecanismo intocado)');
            end
            sqK = sqrt(max(KMSE, 0));
            RObjs = objs(RBFN_cal(SelDecs, Rnets, Global));
            srows = cell(1, 2*nsel);
            for i = 1:nsel
                rsi = [];
                if sids(i) >= 0, rsi = int32(sids(i)); end
                srows{2*i-1} = RunBuffer.mkSurrogateRow(SelDecs(i, :), ...
                    'real_solution_id', rsi, ...
                    'mu', KObjs(i, :), 'sigma', sqK(i, :), ...
                    'pred_tipo', "valor", 'modelo_flag', "Kriging-DACE");
                srows{2*i} = RunBuffer.mkSurrogateRow(SelDecs(i, :), ...
                    'real_solution_id', rsi, ...
                    'mu', RObjs(i, :), ...
                    'pred_tipo', "valor", 'modelo_flag', "RBFN");
            end

            view = struct('g', double(CurGen), 'pop_ids', pop_ids(:).', ...
                          'srows', {srows});
            buf.addGeneration(view);

            % .jsonl: a linha 'e103_gen' (S.7: CurGen/KFlag/√MSE por geracao).
            sq_all = sqrt(max(MSE_julgada, 0));       % o input do JudgeModel
            surr_mask = sum(MSE_julgada, 2) > 0;      % linhas surrogate (nao-dataset)
            sq_surr = sq_all(surr_mask, :);
            rec = struct('ts', iso_now_e103(), 'rec', "e103_gen", ...
                'geracao', double(CurGen), 'kflag', double(KFlag), ...
                'modelo_lider', tern(KFlag, "Kriging", "RBFN"), ...
                'n_julgados', size(MSE_julgada, 1), ...
                'n_sel', nsel, 'n_ds_membros', numel(pop_ids), ...
                'sqrtmse_julgada_max', max(sq_all(:)), ...
                'sqrtmse_surr_min', min_or_nan(sq_surr(:)), ...
                'sqrtmse_surr_med', med_or_nan(sq_surr(:)), ...
                'sqrtmse_surr_max', max_or_nan(sq_surr(:)), ...
                'sqrtmse_sel_max', max(sqrt(max(MSE(:), 0))), ...
                'n_mse_neg', n_mse_neg, 'fe', bud.fe);
            jline(fid, rec);

        case 'busca_fim'
            [tempo_busca, tempo_krig, tempo_rbfn] = deal(varargin{:});
            timing = struct('n_acumulado', Global.n_dataset, ...
                            'tempo_fit_s', tempo_krig + tempo_rbfn, ...
                            'tempo_busca_s', tempo_busca);
            % geracao 0 = o treino UNICO do setup (nGeracoes conta so o ②).
            buf.addGeneration(struct('g', 0, 'timing', timing));
            rec = struct('ts', iso_now_e103(), 'rec', "e103_busca", ...
                'tempo_busca_s', tempo_busca, ...
                'tempo_fit_s', tempo_krig + tempo_rbfn);
            jline(fid, rec);

        otherwise
            error('e103_instrument:fase', 'fase desconhecida: %s', fase);
    end
end

function jline(fid, rec)
    if isempty(fid) || fid <= 2, return; end
    try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
end

function guard_line(fid, name, g, varargin)
% Evento de guarda no .jsonl (mesmo formato do logger do FEBudget/run).
    if isempty(fid) || fid <= 2, return; end
    s = struct('ts', iso_now_e103(), 'rec', "guard", 'name', string(name), ...
               'geracao', g);
    for i = 1:2:numel(varargin)
        s.(varargin{i}) = varargin{i+1};
    end
    try, fprintf(fid, '%s\n', jsonencode(s)); catch, end
end

function v = tern(c, a, b)
    if c, v = a; else, v = b; end
end
function v = min_or_nan(x)
    if isempty(x), v = NaN; else, v = min(x); end
end
function v = max_or_nan(x)
    if isempty(x), v = NaN; else, v = max(x); end
end
function v = med_or_nan(x)
    if isempty(x), v = NaN; else, v = median(x); end
end

function s = iso_now_e103()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
