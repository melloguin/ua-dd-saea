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
%                  ESPERADA: documentada e registrada, nunca silenciada);
%                  + [DI-13.5] dispara a SONDA OFFLINE (e103_sonda): 2 blocos
%                  de 20.000 (1 por modelo, geracao NULL via probeOffline) —
%                  o snd chega por Global.inst.snd (empacotado pelo run_e103)
%                  e a leitura e GUARDADA dentro de e103_sonda (ausente=>no-op).
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
%                  JudgeModel) e do subconjunto surrogate, n_ds_membros;
%                  + DI-10 especificos (CONTRATO §6.1): divergencia_modelos
%                  (mean|μ_Krig−μ_RBFN|, escalar + por objetivo) e
%                  margem_3sigma_stats [DI-13.4 (b)] — replica LITERAL da
%                  aritmetica do JudgeModel sobre (PopObj_julgada, MSE_julgada);
%                  + DI-10 minimo comum (S.7.1): f_best/n_front1 [DI-19.7:
%                  valor DE MODELO da pop selecionada] e fe_treino_max
%                  (= n_dataset-1, tambem nas 2 linhas ③ por membro).
%   'busca_fim'  — apos o laco (99 geracoes): a UNICA linha da serie §17.6
%                  (offline treino-unico): n_acumulado = n_dataset,
%                  tempo_fit_s = kriging+RBFN, tempo_busca_s = laco IBEA,
%                  tempo_pred_sonda_s via takePendingTime [DI-13.10].
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

            % [DI-13.5] SONDA OFFLINE — dispara AQUI (apos o fit UNICO dos 2
            % modelos e ANTES de qualquer decisao da busca): 2 blocos de
            % 20.000 (1 por modelo treinado), geracao NULL, via probeOffline.
            % A leitura de Global.inst.snd (que o run_e103 empacota) e feita
            % COM GUARD dentro de e103_sonda: inst/snd ausentes => no-op
            % (run sem sonda). READ-ONLY: zero FE, zero decisao (D97).
            e103_sonda(Global, KModel, Rnets);

        case 'gen'
            [KModel, Rnets, CurGen, KFlag, Population, MSE, MSE_julgada, ...
             PopObj_julgada] = deal(varargin{:});
            SelDecs = decs(Population);              % N x D (pos-selecao)
            nsel = size(SelDecs, 1);

            % [DI-09/A1] fe_treino_max: treino UNICO sobre o dataset INTEIRO
            % (mesma derivacao do e103_sonda.m:52 — solution_id == fe_index e
            % o orcamento todo foi consumido na carga) => n_dataset-1,
            % CONSTANTE no run. Vai nas 2 linhas ③ por membro e no e103_gen.
            ftm = double(Global.n_dataset) - 1;

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
                    'pred_tipo', "valor", 'modelo_flag', "Kriging-DACE", ...
                    'fe_treino_max', ftm);   % [DI-09/A1] tb nas linhas de busca
                srows{2*i} = RunBuffer.mkSurrogateRow(SelDecs(i, :), ...
                    'real_solution_id', rsi, ...
                    'mu', RObjs(i, :), ...
                    'pred_tipo', "valor", 'modelo_flag', "RBFN", ...
                    'fe_treino_max', ftm);   % [DI-09/A1] tb nas linhas de busca
            end

            view = struct('g', double(CurGen), 'pop_ids', pop_ids(:).', ...
                          'srows', {srows});
            buf.addGeneration(view);

            % [DI-13.4 (b) + rota B30] margem_3sigma_stats: o mecanismo do
            % KFlag e BOOLEANO sobre pares (nao existe UM valor; inventar um
            % escalar = criar grandeza inexistente, proibido por D81). Loga-se
            % a estatistica honesta — quao apertada/folgada foi a decisao —
            % por recompute READ-ONLY de site/Msite sobre o MESMO input do
            % JudgeModel (PopObj_julgada + MSE_julgada, capturados no IBEAMS.m
            % ANTES do ramo KFlag sobrescrever Offspring/OffMSE).
            [m3s, kflag_re] = margem3s_e103(PopObj_julgada, MSE_julgada);
            if logical(kflag_re) ~= logical(KFlag)
                guard_line(fid, 'margem3s_kflag_divergente', CurGen, ...
                    'kflag_mecanismo', double(KFlag), ...
                    'kflag_replica', double(kflag_re), 'motivo', ...
                    ['replica do JudgeModel divergiu do mecanismo — ' ...
                     'margem_3sigma_stats INVALIDA nesta geracao (auditar)']);
            end

            % [DI-10/e103 · CONTRATO §6.1] divergencia_modelos: o desacordo
            % entre as 2 cabecas sobre a pop SELECIONADA — KObjs/RObjs ja
            % existem neste escopo (re-predicao read-only acima).
            div_obj = mean(abs(KObjs - RObjs), 1);         % 1xM, por objetivo
            div_all = mean(abs(KObjs - RObjs), 'all');     % o escalar da SPEC

            % [DI-19.2/DI-19.7] offline: nao ha "arquivo real pos-ciclo" — o
            % f_best e o MINIMO POR OBJETIVO da pop SELECIONADA corrente, um
            % valor DE MODELO (membros do dataset preservam o F real via o
            % marcador MSE=0 do AmendKriCal — mistura documentada); o
            % complemento do superconjunto DI-19.7 (min do dataset) vive no
            % header do run (lado run_e103). n_front1 sobre a MESMA pop.
            PopObjSel = objs(Population);

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
                'n_mse_neg', n_mse_neg, 'fe', bud.fe, ...
                ... % ── DI-10: especificos do e103 (S.7.1/CONTRATO §6.1) ──
                'divergencia_modelos', div_all, ...
                'divergencia_modelos_por_obj', div_obj, ...
                'margem_3sigma_stats', m3s, ...
                ... % ── DI-10: minimo comum dos 21 (S.7.1) ──
                'f_best', min(PopObjSel, [], 1), ...
                'n_front1', n_front1_e103(PopObjSel), ...
                'fe_treino_max', opt_null_e103(ftm));
            jline(fid, rec);

        case 'busca_fim'
            [tempo_busca, tempo_krig, tempo_rbfn] = deal(varargin{:});
            % [DI-13.10] tempo_pred_sonda_s via takePendingTime (guard: run
            % sem sonda => 0). NAO ha desconto a fazer no e103: a sonda
            % offline dispara NO setup, ANTES do t0_busca (IBEAMS.m) — o
            % tempo_busca_s ja nasce SEM o custo dela; e a ④ e agregada
            % (T-8: sem tempo_geracao_s por geracao no e103).
            tps = sonda_tempo_e103(inst);
            timing = struct('n_acumulado', Global.n_dataset, ...
                            'tempo_fit_s', tempo_krig + tempo_rbfn, ...
                            'tempo_busca_s', tempo_busca, ...
                            'tempo_pred_sonda_s', tps);
            % geracao 0 = o treino UNICO do setup (nGeracoes conta so o ②).
            buf.addGeneration(struct('g', 0, 'timing', timing));
            rec = struct('ts', iso_now_e103(), 'rec', "e103_busca", ...
                'tempo_busca_s', tempo_busca, ...
                'tempo_fit_s', tempo_krig + tempo_rbfn, ...
                'tempo_pred_sonda_s', tps);
            jline(fid, rec);

        otherwise
            error('e103_instrument:fase', 'fase desconhecida: %s', fase);
    end
end

function jline(fid, rec)
    if isempty(fid) || fid <= 2, return; end
    try, fprintf(fid, '%s\n', jsonencode(rec)); catch, end
end

function [stats, kflag_re] = margem3s_e103(PopObj, MSE)
% [DI-13.4 (b)] margem_3sigma_stats — a estatistica HONESTA do gate.
% REPLICA LITERAL da aritmetica de JudgeModel.m (loops :7-14, eps=1e-5 e o
% inf/zero de :16-24, site :27-31, relaxacao sum(site,3)>=M-1 e a exclusao da
% diagonal via OR com eye de :38 — a ancora e103-judgemodel FAZ PARTE do
% mecanismo replicado). O ARQUIVO JudgeModel.m NAO e tocado; qualquer
% divergencia da replica vs o KFlag do mecanismo vira guard no .jsonl.
% READ-ONLY: nada daqui volta para a busca (D97).
% Campos:
%   n_pares_ok              nnz(Msite) — INCLUI os N pares i==i forcados pela
%                           ancora (a comparacao de um individuo consigo mesmo
%                           nao informa ordem; entram como "ok" por construcao)
%   n_pares_total           N^2 (o denominador do all(all(Msite)))
%   n_pares_ok_por_objetivo nnz(site(:,:,j)) por objetivo — site PURO
%                           (:27-31), ANTES do OR com a diagonal
    [N, M] = size(PopObj);
    I    = zeros([N,N,M]);
    MSEI = I;
    for objid = 1:M
        for i = 1 : N
            for j = 1 : N
                [I(i,j,objid)] = abs(PopObj(i,objid)-PopObj(j,objid));
                MSEI(i,j,objid)= 3*sqrt(MSE(i,objid))+3*sqrt(MSE(j,objid));
            end
        end
    end
    for objid =1:M
        tempI  = I(:,:,objid);
        tempMSEI = MSEI(:,:,objid);
        infid = find(tempI<=1e-5 & tempMSEI<=1e-5);
        tempI(infid) = inf;
        zeroid= find(tempI<=1e-5 & tempMSEI>1e-5);
        tempI(zeroid)= 0;
        I(:,:,objid)  = tempI;
    end
    site = zeros([N,N,M]);
    n_ok_obj = zeros(1, M);
    for objid = 1:M
        selectid = (I(:,:,objid)>MSEI(:,:,objid));
        site(:,:,objid)  = selectid;
        n_ok_obj(objid)  = double(nnz(selectid));
    end
    Msite = (sum(site,3)>=(M-1)) | logical(eye(N));
    kflag_re = all(all(Msite));
    stats = struct('n_pares_ok', double(nnz(Msite)), ...
                   'n_pares_total', double(N*N), ...
                   'n_pares_ok_por_objetivo', n_ok_obj);
end

function n = n_front1_e103(PopObj)
% [DI-10 minimo comum] rank-1 por filtro ND LOCAL O(N^2 M): NDSort NAO
% resolve no path do e103 (arvore standalone — ensure_paths_e103 exclui a
% _PlatEMO; sombra de path e o hazard N.3). N=100 => trivial. Dominancia
% de Pareto padrao (<= em todos os objetivos, < em pelo menos um).
    N = size(PopObj, 1);
    nd = true(N, 1);
    for i = 1:N
        for j = 1:N
            if j ~= i && all(PopObj(j, :) <= PopObj(i, :)) ...
                      && any(PopObj(j, :) <  PopObj(i, :))
                nd(i) = false;
                break;
            end
        end
    end
    n = double(sum(nd));
end

function t = sonda_tempo_e103(inst)
% [DI-13.10] tempo de sonda pendente (0 em run sem sonda — guard).
    t = 0;
    if isfield(inst, 'snd') && ~isempty(inst.snd), t = inst.snd.takePendingTime(); end
end

function v = opt_null_e103(x)
    if isempty(x), v = []; else, v = double(x); end
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
