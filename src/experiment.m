function [status, info] = experiment(alg, problema_id, semente, exp, dataRoot)
% experiment — adapter MATLAB (arquitetura A2, §16.5.3): traduz
% run(alg, problema_id, semente) na avaliacao do problema Python pela PONTE, sob
% o orcamento do WRAPPER de FE (FEBudget), gravando as 4 camadas do §17.2.
%
% >>> R1-00-harness (infra TRANSVERSAL — contrato N.0). CORPO REAL das pecas que
% >>> TODOS os algoritmos MATLAB herdam: a ponte de avaliacao, o orcamento pelo
% >>> wrapper (hard-stop 31D-1 EXATO — D89), o DoE carregado do artefato (D63/
% >>> D87, NUNCA regenerado), o export das 4 camadas (parquet brotli+single, SEM
% >>> round — D53; escrita atomica — D58) e o fechamento do CP-init (bit-
% >>> identidade da camada ① com o DoE do F0-02 — D87/D88).
% >>> NENHUM algoritmo dos 16 e implementado aqui: o run-STUB (alg='stub') e um
% >>> AVALIADOR TRIVIAL que exercita a infra ponta-a-ponta (sem Algorithm.Solve,
% >>> sem fidelidade — D97). O 1o algoritmo real e o R1-c217 (caso-modelo).
%
% Retorna status in {"ok","retried_ok","failed"} e (opcional) info do STUB.
%
% Contrato do adapter herdado pelos algoritmos reais (preenchido em R1-c217+):
%   1. Problema de src/problems.py pelo problema_id via PONTE (A2/§2) — o MATLAB
%      NUNCA usa problema nativo; avalia f(x) por py.problems.evaluate_problem.
%   2. Bounds/sinal (§5.5): PlatEMO/EA operam em bounds NATIVOS e minimizam ->
%      identidade nos bounds (CP-bounds/CP-sinal), devolve f.
%   3. DoE 11D-1 carregado do artefato parquet (D87) via parquetread; injecao por
%      patch local (A1: os SAEAs nao usam Problem.Initialization). NUNCA regenerar.
%   4. maxFE = 31D-1 com HARD-STOP EXATO no wrapper (FEBudget) — o obj.FE nativo
%      do PlatEMO NAO governa (D89). Cache-hit bit-a-bit no X nativo = 0 FE.
%   5. Semear (D59): rng(semente,'twister') DEPOIS do Problem, ANTES de Solve.
%   6. Coletar a trajetoria pelo hook_output (②③+timing) e gravar o export §17.

    status = "failed";
    info = struct();
    if nargin < 4 || isempty(exp),      exp = 'main';  end
    if nargin < 5 || isempty(dataRoot), dataRoot = 'data'; end

    switch char(alg)
        case 'stub'
            % Run-STUB do R1-00: infra transversal ponta-a-ponta, sem algoritmo.
            [status, info] = run_stub(alg, problema_id, semente, exp, dataRoot);
        case 'c217'
            % R1-c217 (caso-modelo): 1o algoritmo REAL — PC-SAEA (PlatEMO 4.15)
            % ponta-a-ponta na infra do R1-00 (Solve real + hard-stop do wrapper).
            [status, info] = run_c217(alg, problema_id, semente, exp, dataRoot);
        case 'c141'
            % R1-c141 (1o fan-out): MMRAEA (repo do autor, porte 3 linhas p/ o
            % 4.15 — L.7) no MESMO padrao do caso-modelo c217.
            [status, info] = run_c141(alg, problema_id, semente, exp, dataRoot);
        case 'b1'
            % R1-b1 (fan-out): ParEGO (built-in PlatEMO 4.15) no MESMO padrao
            % do caso-modelo c217 (injecao DoE D94 :29-:30; guard L8; P4).
            [status, info] = run_b1(alg, problema_id, semente, exp, dataRoot);
        case 'b3'
            % R1-b3 (fan-out): K-RVEA (built-in PlatEMO 4.15) no MESMO padrao
            % do caso-modelo c217 (receita N.0 do handoff R1-c217 §4).
            [status, info] = run_b3(alg, problema_id, semente, exp, dataRoot);
        case 'b4'
            % R1-b4 (fan-out): CSEA (built-in PlatEMO 4.15) no MESMO padrao do
            % caso-modelo c217 (cap109 removido; cpu — N.2.4; Balde C).
            [status, info] = run_b4(alg, problema_id, semente, exp, dataRoot);
        case 'e7'
            % R1-e7 (fan-out): EDN-ARMOEA (built-in PlatEMO 4.15, N.2.1) no
            % MESMO padrao do caso-modelo c217 (injecao DoE D94 :31-:32;
            % dropout 0.1 D30; guard Estimate; guarda (c) D60 saldo congelado).
            [status, info] = run_e7(alg, problema_id, semente, exp, dataRoot);
        otherwise
            % Algoritmos reais (b1,b3,b4,e7,c217,c141,e74,c238,e103,pisos):
            % o corpo PlatEMO (UserProblem + Solve) e o cartao R1-c217+.
            % A infra transversal (ponte, FEBudget, DoE, export, hook, manifesto)
            % ja esta pronta neste arquivo para o c217 fiar. Sem algoritmo em
            % R1-00 => falha honesta (D23), nunca silenciosa.
            fprintf(2, ['[TODO R1-c217+] adapter PlatEMO de %s nao ligado ' ...
                        '(R1-00 = infra transversal; sem algoritmo). ' ...
                        'problema=%s semente=%d exp=%s\n'], ...
                    char(alg), char(problema_id), semente, char(exp));
            status = "failed";
    end
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-STUB (avaliador trivial) — prova a infra transversal (D89/D57/D53/D58/
%  §17.2/§17.7 + CP-init D87/D88). Espelho MATLAB do _f0_03_stub_run do accept.py.
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_stub(alg, problema, semente, exp, dataRoot)
    status = "failed";
    ROOT = harness_root();

    % (0) PONTE: repo-root no sys.path do Python embutido; importa src.*.
    ctx = bridge_ctx(ROOT);

    % (1) Problema Python via PONTE -> D, M, bounds (A2/§2).
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl; xu = pp.xu;
    maxfe = 31*D - 1;  n_init = 11*D - 1;

    % (2) DoE 11D-1 do artefato (D63/D87) — CARREGADO, NUNCA regenerado.
    doe = load_doe(problema, semente, D, dataRoot);
    X0 = doe.X;                                   % n_init x D (double, nativo)
    assert(size(X0,1) == n_init, 'DoE tem %d linhas != 11D-1=%d', size(X0,1), n_init);
    % CP-bounds (§5.5): os bounds do problema Python batem com o sidecar do DoE.
    assert(max(abs(xl(:) - doe.xl(:))) == 0 && max(abs(xu(:) - doe.xu(:))) == 0, ...
           'CP-bounds: bounds do problema != bounds do sidecar do DoE');

    % (3) log .jsonl (§17.5) + wrapper de FE (FEBudget) com o logger acoplado.
    jsonl = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    fid = jsonl_open(jsonl);
    logger = struct('guard', @(name, varargin) ...
                    jsonl_line(fid, 'guard', [{'name'}, {name}, varargin]));
    bud = FEBudget(D, maxfe, n_init, logger);
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "online", ...
        'maxfe', maxfe, 'doe_hash', string(doe.hash)});

    % evalFcn: a PONTE (A2) — f(x) por py.problems.evaluate_problem (bounds nativos).
    evalFcn = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));

    % (4a) INIT = os 11D-1 pontos do DoE (fase 'init'), injetados pela PONTE.
    for i = 1:n_init
        bud.evaluate(X0(i,:), evalFcn);
    end

    % (4b) OPT = 20D infills DISTINTOS na diagonal (fase 'opt') -> 31D-1 distintos.
    n_infill = 20*D;
    for i = 1:n_infill
        frac = (i) / (n_infill + 2);
        x = xl(:).' + frac * (xu(:).' - xl(:).');
        if bud.solutionIdOf(x) >= 0                      % colisao (prob~0) -> nudge
            x = x + i * 1e-9 * (xu(:).' - xl(:).');
        end
        bud.evaluate(x, evalFcn);
        jsonl_line(fid, 'decision', {'caminho', "infill", ...
            'motivo', sprintf('frac=%.4f', frac), 'fe', bud.fe});
    end

    % (4c) CACHE-HIT: reavaliar o 1o ponto do DoE = 0 FE (D89).
    fe_antes = bud.fe;
    bud.evaluate(X0(1,:), evalFcn);
    cache_hit_zero_fe = (bud.fe == fe_antes);

    % (4d) HARD-STOP EXATO: a proxima X INEDITA levanta PlatEMO:Termination (D21).
    probe = xu(:).';
    if bud.solutionIdOf(probe) >= 0, probe = probe - 1e-9 * (xu(:).' - xl(:).'); end
    hard_stopped = false;
    try
        bud.evaluate(probe, evalFcn);
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination'), hard_stopped = true;
        else, rethrow(e); end
    end

    % (5) trajetoria ②③+timing (RunBuffer — o coletor que o hook alimenta em
    %     c217). O STUB fabrica geracoes p/ exercitar as camadas e o schema C1/C3.
    R = bud.records();                                    % catalogo ①
    sids = [R.solution_id];                               % 0-based
    buf = RunBuffer();
    G = 3;
    for g = 1:G
        view = struct('g', g);
        % ② membership: primeiros (5+g) solution_ids reais.
        k = min(5 + g, numel(sids));
        view.pop_ids = sids(1:k);
        % ③ surrogate:
        srows = {};
        % regressor: mu/sigma por objetivo, ligando ao ① via real_solution_id.
        for c = 0:3
            sid = sids(mod(g + c, numel(sids)) + 1);
            xk = R(sid + 1).x;
            srows{end+1} = RunBuffer.mkSurrogateRow(xk, ...
                'real_solution_id', int32(sid), ...
                'mu', 0.5 * (g + (0:M-1)), 'sigma', 1e-3 * (g+1) * ones(1,M), ...
                'pred_tipo', "valor", 'modelo_flag', "GP"); %#ok<AGROW>
        end
        % C3: linha em espaco transformado (cru+params), mono-output estilo b1
        % (mu_0 preenchido, mu_1.. NULL — §17.2/D47).
        srows{end+1} = RunBuffer.mkSurrogateRow(R(1).x, ...
            'real_solution_id', int32(sids(1)), 'mu', 0.1 * g, ...
            'pred_tipo', "valor", 'modelo_flag', "GP", ...
            'espaco_modelo', "transformado", 'transf_tipo', "minmax", ...
            'transf_params', struct('min', 0.0, 'max', 1.0)); %#ok<AGROW>
        % classificador: pred_classe/score (mu/sigma NULL) — DEF-C1.
        srows{end+1} = RunBuffer.mkSurrogateRow(R(end).x, ...
            'real_solution_id', int32(sids(end)), ...
            'pred_tipo', "classe", 'pred_classe', "bom", ...
            'pred_confianca', 0.83, 'modelo_flag', "FNN"); %#ok<AGROW>
        view.srows = srows;
        % §17.6 timing: um evento de retreino por geracao.
        view.timing = struct('n_acumulado', n_init + g*5, ...
                             'tempo_fit_s', 0.001*g, 'tempo_busca_s', 0.002);
        buf.addGeneration(view);
        jsonl_line(fid, 'timing', {'n_acumulado', n_init + g*5, 'tempo_fit_s', 0.001*g});
    end

    % (6) EXPORT das 4 camadas (§17.2/§17.3) — parquet brotli+single, atomico.
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (7) CP-init por-run (D87/D88): hash da init X (float64) = sidecar do DoE.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);

    % (8) MANIFESTO (§17.2/§17.7) — status ok, FE final, CP-init, timing.
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', "ok", 'fe_final', bud.fe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok});
    fclose(fid);

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'cache_hits', bud.cache_hits, ...
        'cache_hit_zero_fe', cache_hit_zero_fe, 'hard_stopped', hard_stopped, ...
        'doe_hash_run', string(doe_hash_run), 'doe_hash_sidecar', string(doe.hash), ...
        'cp_ok', cp_ok);
    status = "ok";
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-c217 (PC-SAEA REAL, PlatEMO 4.15) — o CASO-MODELO ponta-a-ponta (R1-c217).
%  Reusa a infra transversal do R1-00 (ponte, FEBudget, DoE, export, CP-init,
%  manifesto). O que e ESPECIFICO do c217: o Solve real (UserProblem+PCSAEA), o
%  embrulho de LOTE do evalFcn com hard-stop no meio (D61), a injecao do DoE pela
%  patch A1 (Problem.data.X0) e a instrumentacao ②③/§17.2.1/timing.
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_c217(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();

    % Garante a arvore PlatEMO 4.15 no path (N.0.1) — rede p/ chamada DIRETA de
    % experiment() (o despachante experiments.m ja faz addpath por worker).
    ensure_platemo_c217(ROOT);

    % (0) PONTE: repo-root no sys.path; importa src.* (A2/§2/§18).
    ctx = bridge_ctx(ROOT);

    % (1) Problema Python via ponte -> D, M, bounds NATIVOS (§5.5).
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl(:).'; xu = pp.xu(:).';
    maxfe = 31*D - 1;  n_init = 11*D - 1;

    % (2) DoE 11D-1 do artefato (D63/D87) — CARREGADO, NUNCA regenerado.
    doe = load_doe(problema, semente, D, dataRoot);
    X0  = doe.X;                                   % n_init x D (float64, nativo)
    assert(size(X0,1) == n_init, 'DoE tem %d linhas != 11D-1=%d', size(X0,1), n_init);
    % CP-bounds (§5.5): bounds do problema == sidecar do DoE (identidade nativa).
    assert(max(abs(xl(:)-doe.xl(:)))==0 && max(abs(xu(:)-doe.xu(:)))==0, ...
           'CP-bounds: bounds do problema != sidecar do DoE');

    % (3) .jsonl (§17.5) + wrapper de FE (FEBudget) com o logger acoplado.
    jsonl  = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    fid    = jsonl_open(jsonl);
    logger = struct('guard', @(name, varargin) ...
                    jsonl_line(fid, 'guard', [{'name'}, {name}, varargin]));
    % bud CRIADO ANTES do Problem: o probe do construtor avalia DoE[0] (via initFcn),
    % que o lote-init reencontra como CACHE-HIT (0 FE, D89) -> obj.FE==bud.fe e a ①
    % fecha com EXATAMENTE 31D-1 linhas, sem poluir o catalogo com ponto aleatorio.
    bud = FEBudget(D, maxfe, n_init, logger);
    buf = RunBuffer();
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "online", 'maxfe', maxfe, ...
        'doe_hash', string(doe.hash), 'algo', "c217-PCSAEA-PlatEMO4.15", 'N', 50, ...
        'delta', 0.8, 'gmax', 3000});

    % (4) evalFcn por-x (a ponte, bounds nativos) + embrulho de LOTE (D61).
    evalFcnPerX = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));
    batchEval   = @(X, varargin) c217_batch_eval(X, bud, evalFcnPerX);

    % (5) UserProblem (contrato N.0/L.0): once=true (lote), bounds nativos, minimiza.
    %   - data = struct: X0 (injecao do DoE — patch A1 em PCSAEA:27-29) + buf/bud/fid
    %     (a instrumentacao c217 le Problem.data.*).
    %   - initFcn = DoE[0] p/ o PROBE (Initialization(1)) do construtor: evita o
    %     ponto aleatorio; o probe avalia DoE[0] pela ponte (absorvido como cache-hit).
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, ...
                  'run_id', string(nm_run_id(exp, alg, problema, semente)), ...
                  'problema', string(problema), 'semente', semente);
    Problem = UserProblem('evalFcn', batchEval, 'initFcn', @(N,varargin) X0(1:N,:), ...
        'D', D, 'lower', xl, 'upper', xu, 'maxFE', maxfe, ...
        'N', 50, 'once', true, 'data', data);           % maxRuntime fica inf (N.0.5)

    % (6) SEMENTE (D59): rng DEPOIS de construir o Problem, ANTES do Solve.
    rng(semente, 'twister');

    % (7) Algoritmo REAL: save=-K (sem .mat/figura — N.0.3/4), outputFcn=hook (②),
    %     parametros posicionais delta=0.8/gmax=3000 (PCSAEA.ParameterSet).
    K = 20;
    algo = PCSAEA('parameter', {0.8, 3000}, 'save', -K, ...
        'outputFcn', @(A,P) hook_output(A, P, buf, bud, []));
    term = "normal";
    try
        algo.Solve(Problem);                           % engole PlatEMO:Termination
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination')
            term = "hard_stop";                        % nunca deveria vazar (Solve engole)
        else
            jsonl_line(fid, 'footer', {'status', "failed", 'erro', string(e.message), ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, '[R1-c217 FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end

    % (8) EXPORT das 4 camadas (§17.2/§17.3): ① do wrapper; ②③/timing do buffer.
    R = bud.records();                                 % catalogo ① (== 31D-1 linhas)
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (9) CP-init por-run (D87/D88): hash da init X (float64) = sidecar do DoE.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);

    % (10) Encanamento objetivo (D89/D21): FE final = 31D-1 EXATO E CP-init OK.
    %      Falha honesta (D23/D81): se o gate objetivo reprova, o manifesto/footer
    %      registram 'failed' (o despachante nao pula um run invalido — is_run_done).
    ok_flag = (bud.fe == maxfe) && cp_ok;
    st_str  = "ok"; if ~ok_flag, st_str = "failed"; end

    % (11) MANIFESTO (§17.2/§17.7).
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    man.algo_version = "c217-PCSAEA-PlatEMO4.15";
    man.status = st_str;
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', st_str, 'fe_final', bud.fe, 'maxfe', maxfe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok, 'termino', string(term)});
    fclose(fid);

    % (12) Higiene de memoria da ponte (D86/N.0.8): solta o Problem pymoo do run.
    try, py.gc.collect(); catch, end

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'termino', string(term), 'doe_hash_run', string(doe_hash_run), ...
        'doe_hash_sidecar', string(doe.hash), 'cp_ok', cp_ok);
    if ~ok_flag
        fprintf(2, ['[R1-c217] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
end


function varargout = c217_batch_eval(X, bud, evalFcnPerX)
% Embrulho de LOTE do evalFcn (D61 — 2a decisao deferida pelo R1-00). O UserProblem
% (once=true) chama com um lote N x D esperando [dec,obj,con]. Itera as linhas pelo
% wrapper de FE (bud.evaluate): cache-hit = 0 FE (D89); quando o saldo zera, o bud
% levanta MException('PlatEMO:Termination') NO MEIO do lote -> a excecao propaga
% (CallFcn do UserProblem preserva o identifier via addCause) -> Solve engole -> FE
% final = 31D-1 EXATO nos 2 stacks. dec = X (o X avaliado = clamp autoritativo do
% wrapper); con = zeros (o problema pymoo e irrestrito).
    n   = size(X, 1);
    dec = X;
    obj = [];
    for i = 1:n
        f = bud.evaluate(X(i, :), evalFcnPerX);   % 1xM; pode levantar PlatEMO:Termination
        if isempty(obj), obj = zeros(n, numel(f)); end
        obj(i, :) = f; %#ok<AGROW>
    end
    con = zeros(n, 1);
    varargout = {dec, obj, con};
end


function ensure_platemo_c217(ROOT)
% addpath(genpath) da arvore PlatEMO 4.15 se o c217 nao estiver no path (N.0.1).
% Rede p/ chamada direta de experiment() (o despachante ja faz isso por worker).
    if isempty(which('PCSAEA')) || isempty(which('UserProblem')) || isempty(which('OperatorGA'))
        pr = fullfile(ROOT, 'algorithms', '_PlatEMO', 'PlatEMO');
        if isfolder(pr), addpath(genpath(pr)); end
    end
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-c141 (MMRAEA REAL, repo do autor em porte 4.15) — 1o FAN-OUT da R1, no
%  padrao do caso-modelo c217 (receita N.0 do handoff R1-c217 §4). O que e
%  ESPECIFICO do c141: N = min(100, 11D-1) por subpopulacao (DEF-A5 — crash
%  pool<N em D<=9), MMRAEA sem 'parameter' (wmax=20 hardcoded = paper), o path
%  da pasta do autor (fora da arvore PlatEMO) e a instrumentacao c141_instrument
%  (③ D45: mu ARBFs + 2 incertezas; .jsonl S.7; timing §17.6).
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_c141(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();

    % Arvore PlatEMO 4.15 (N.0.1) + a pasta do c141 (repo do autor).
    ensure_paths_c141(ROOT);

    % (0) PONTE: repo-root no sys.path; importa src.* (A2/§2/§18).
    ctx = bridge_ctx(ROOT);

    % (1) Problema Python via ponte -> D, M, bounds NATIVOS (§5.5).
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl(:).'; xu = pp.xu(:).';
    maxfe = 31*D - 1;  n_init = 11*D - 1;
    Nsub  = min(100, 11*D - 1);   % DEF-A5: teto 100 (paper/codigo) + piso 11D-1
                                  % (ES_PDR.m:20 estoura se pool ger.1 < N — D<=9)

    % (2) DoE 11D-1 do artefato (D63/D87) — CARREGADO, NUNCA regenerado.
    doe = load_doe(problema, semente, D, dataRoot);
    X0  = doe.X;                                   % n_init x D (float64, nativo)
    assert(size(X0,1) == n_init, 'DoE tem %d linhas != 11D-1=%d', size(X0,1), n_init);
    % CP-bounds (§5.5): bounds do problema == sidecar do DoE (identidade nativa).
    assert(max(abs(xl(:)-doe.xl(:)))==0 && max(abs(xu(:)-doe.xu(:)))==0, ...
           'CP-bounds: bounds do problema != sidecar do DoE');

    % (3) .jsonl (§17.5) + wrapper de FE (FEBudget) com o logger acoplado.
    jsonl  = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    fid    = jsonl_open(jsonl);
    logger = struct('guard', @(name, varargin) ...
                    jsonl_line(fid, 'guard', [{'name'}, {name}, varargin]));
    % bud CRIADO ANTES do Problem: o probe do construtor avalia DoE[0] (initFcn),
    % que o lote-init reencontra como CACHE-HIT (0 FE, D89) -> a ① fecha com
    % EXATAMENTE 31D-1 linhas, sem poluir o catalogo (receita N.0 do c217).
    bud = FEBudget(D, maxfe, n_init, logger);
    buf = RunBuffer();
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "online", 'maxfe', maxfe, ...
        'doe_hash', string(doe.hash), 'algo', "c141-MMRAEA-porte4.15", ...
        'N_subpop', Nsub, 'wmax', 20, ...
        'sigma_dict', "sigma_0=U_ranks_pop_completa(D45 nativa); sigma_1=std_bruto_3_modos(D45 ensemble-proxy)"});

    % (4) evalFcn por-x (a ponte, bounds nativos) + embrulho de LOTE (D61) — o
    %     c217_batch_eval e GENERICO (handoff R1-c217 §7): hard-stop no meio do lote.
    evalFcnPerX = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));
    batchEval   = @(X, varargin) c217_batch_eval(X, bud, evalFcnPerX);

    % (5) UserProblem (contrato N.0/L.0): once=true (lote), bounds nativos, minimiza.
    %     N = Nsub e POR SUBPOPULACAO (B12.6 — pool de infill = 2N).
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, ...
                  'run_id', string(nm_run_id(exp, alg, problema, semente)), ...
                  'problema', string(problema), 'semente', semente);
    Problem = UserProblem('evalFcn', batchEval, 'initFcn', @(N,varargin) X0(1:N,:), ...
        'D', D, 'lower', xl, 'upper', xu, 'maxFE', maxfe, ...
        'N', Nsub, 'once', true, 'data', data);        % maxRuntime fica inf (N.0.5)

    % (6) SEMENTE (D59): rng DEPOIS de construir o Problem, ANTES do Solve.
    rng(semente, 'twister');

    % (7) Algoritmo REAL: save=-K (sem .mat/figura — N.0.3/4), outputFcn=hook (②).
    %     MMRAEA nao tem ParameterSet (wmax=20 hardcoded — paper OK).
    K = 20;
    algo = MMRAEA('save', -K, ...
        'outputFcn', @(A,P) hook_output(A, P, buf, bud, []));
    term = "normal";
    try
        algo.Solve(Problem);                           % engole PlatEMO:Termination
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination')
            term = "hard_stop";                        % nunca deveria vazar (Solve engole)
        else
            jsonl_line(fid, 'footer', {'status', "failed", 'erro', string(e.message), ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, '[R1-c141 FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end

    % (8) EXPORT das 4 camadas (§17.2/§17.3): ① do wrapper; ②③/timing do buffer.
    R = bud.records();                                 % catalogo ① (== 31D-1 linhas)
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (9) CP-init por-run (D87/D88): hash da init X (float64) = sidecar do DoE.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);

    % (10) Encanamento objetivo (D89/D21): FE final = 31D-1 EXATO E CP-init OK.
    %      Falha honesta (D23/D81): gate reprovado -> manifesto/footer 'failed'.
    ok_flag = (bud.fe == maxfe) && cp_ok;
    st_str  = "ok"; if ~ok_flag, st_str = "failed"; end

    % (11) MANIFESTO (§17.2/§17.7) + dicionario de sigma (DEF-C4/D45).
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    man.algo_version = "c141-MMRAEA-porte4.15";
    man.status = st_str;
    man.params = struct('N_subpop', Nsub, 'wmax', 20, 'kernel', "MQ c=1 poly=0 x3", ...
                        'ds_dsmerge', 1e-14);
    man.sigma_dict = struct( ...
        'sigma_0', "U de ranks (|Q1-Q2|+|Q1-Q3|+|Q2-Q3|) na populacao completa — incerteza NATIVA do c141 (D45)", ...
        'sigma_1', "desvio bruto entre os 3 modos (std de [Fit1,Fit2,Fit3]) — proxy de ensemble, escalas incomensuraveis (D45)");
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', st_str, 'fe_final', bud.fe, 'maxfe', maxfe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok, 'termino', string(term)});
    fclose(fid);

    % (12) Higiene de memoria da ponte (D86/N.0.8): solta o Problem pymoo do run.
    try, py.gc.collect(); catch, end

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'N_subpop', Nsub, 'n_geracoes', buf.nGeracoes(), ...
        'cache_hits', bud.cache_hits, 'termino', string(term), ...
        'doe_hash_run', string(doe_hash_run), ...
        'doe_hash_sidecar', string(doe.hash), 'cp_ok', cp_ok);
    if ~ok_flag
        fprintf(2, ['[R1-c141] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
end


function ensure_paths_c141(ROOT)
% PlatEMO 4.15 (N.0.1) + a pasta do c141 (repo do autor, FORA da arvore PlatEMO).
% A pasta do c141 tem nomes que colidem com copias do 4.15 (UpdataArchive [K-RVEA],
% CSO [single-obj], CalFitness [IBEA etc.], dsmerge [AB-SAEA], rbf_build/rbf_predict
% [SAMSO/SACC-EAM-II]) — TODAS as copias PlatEMO sao chamadas de dentro da PROPRIA
% pasta (regra same-folder resolve — S.8; renames defensivos dispensados). Os
% asserts garantem a precedencia da copia do c141 p/ as chamadas VIA PATH do
% c141_instrument (que vive em src/, sem same-folder).
    if isempty(which('UserProblem')) || isempty(which('OperatorGA'))
        pr = fullfile(ROOT, 'algorithms', '_PlatEMO', 'PlatEMO');
        if isfolder(pr), addpath(genpath(pr)); end
    end
    c141root = fullfile(ROOT, 'algorithms', 'c141_MMRAEA', 'extracted', 'MMRAEA');
    if isempty(which('MMRAEA')) || ~contains(which('rbf_predict'), 'c141_MMRAEA')
        assert(isfolder(c141root), 'c141: pasta do repo ausente: %s', c141root);
        addpath(genpath(c141root));          % prepend -> precedencia do c141
    end
    assert(contains(which('rbf_predict'), 'c141_MMRAEA'), ...
           'c141: rbf_predict nao resolve p/ a copia do c141 (precedencia de path)');
    assert(contains(which('calFitness'), 'c141_MMRAEA'), ...
           'c141: calFitness nao resolve p/ a copia do c141 (precedencia de path)');
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-b1 (ParEGO REAL, built-in PlatEMO 4.15) — fan-out da R1 no padrao do
%  caso-modelo c217 (receita N.0 do handoff R1-c217 §4). O que e ESPECIFICO do
%  b1: 'N',100 = nº de ESCALARIZACOES/vetores λ (D20; UniformPoint ajusta p/
%  100 em M=2 / 91 em M=3), ParEGO sem 'parameter' (IFEs=10000 default do
%  codigo = paper), os patches P1 (DoE D94 :29-:30 JUNTAS), P2 (guard L8
%  sqrt(max(mse,0)) SO em ParEGO/EvolALG.m — o mesmo token em EGO/EvolEI.m
%  fica INTOCADO, HANDOFF §11.1) e P4 (NaN-guard DEF-A8 na :39), e a
%  instrumentacao b1_instrument (③ MONO-OUTPUT D47/C3 + S.7 + §17.6).
%  Toolboxes: Statistics (normcdf/normpdf no EI do EvolALG).
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_b1(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();

    % Arvore PlatEMO 4.15 no path (N.0.1) — rede p/ chamada direta.
    ensure_paths_b1(ROOT);

    % (0) PONTE: repo-root no sys.path; importa src.* (A2/§2/§18).
    ctx = bridge_ctx(ROOT);

    % (1) Problema Python via ponte -> D, M, bounds NATIVOS (§5.5).
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl(:).'; xu = pp.xu(:).';
    maxfe = 31*D - 1;  n_init = 11*D - 1;
    % Nº de escalarizacoes/vetores λ (D20: paper usa 11/15 — DIVERGENCIA em
    % CODIGO, registrada; N=100 default). UniformPoint e deterministico (L.0)
    % — so p/ registrar o N_lambda EFETIVO (100 em M=2; NBI 91 em M=3).
    [~, Nlam] = UniformPoint(100, M);

    % (2) DoE 11D-1 do artefato (D63/D87) — CARREGADO, NUNCA regenerado.
    doe = load_doe(problema, semente, D, dataRoot);
    X0  = doe.X;                                   % n_init x D (float64, nativo)
    assert(size(X0,1) == n_init, 'DoE tem %d linhas != 11D-1=%d', size(X0,1), n_init);
    % CP-bounds (§5.5): bounds do problema == sidecar do DoE (identidade nativa).
    assert(max(abs(xl(:)-doe.xl(:)))==0 && max(abs(xu(:)-doe.xu(:)))==0, ...
           'CP-bounds: bounds do problema != sidecar do DoE');

    % (3) .jsonl (§17.5) + wrapper de FE (FEBudget) com o logger acoplado.
    jsonl  = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    fid    = jsonl_open(jsonl);
    logger = struct('guard', @(name, varargin) ...
                    jsonl_line(fid, 'guard', [{'name'}, {name}, varargin]));
    % bud CRIADO ANTES do Problem: o probe do construtor avalia DoE[0] (initFcn),
    % que o lote-init reencontra como CACHE-HIT (0 FE, D89) -> a ① fecha com
    % EXATAMENTE 31D-1 linhas, sem poluir o catalogo (receita N.0 do c217).
    bud = FEBudget(D, maxfe, n_init, logger);
    buf = RunBuffer();
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "online", 'maxfe', maxfe, ...
        'doe_hash', string(doe.hash), 'algo', "b1-ParEGO-PlatEMO4.15", ...
        'N_lambda', Nlam, 'IFEs', 10000, 'rho', 0.05, ...
        'theta0', 10, 'theta_bounds', "[1e-5,20]", ...
        'subset', "top-(11D-1+25) por PCheby + dedup 1e-6 (CODIGO)", ...
        'sigma_dict', "mu_0/sigma_0=escalar PCheby predito (D47 mono-output, lossy); mu_1..=NULL; transf_params={lambda,min,max,gbest}/iter (C3)"});

    % (4) evalFcn por-x (a ponte, bounds nativos) + embrulho de LOTE (D61) — o
    %     c217_batch_eval e GENERICO (handoff R1-c217 §7): hard-stop no meio do lote.
    evalFcnPerX = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));
    batchEval   = @(X, varargin) c217_batch_eval(X, bud, evalFcnPerX);

    % (5) UserProblem (contrato N.0/L.0): once=true (lote), bounds nativos, minimiza.
    %     N=100 governa o nº de escalarizacoes (ParEGO.m:27 ajusta p/ Nlam).
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, ...
                  'run_id', string(nm_run_id(exp, alg, problema, semente)), ...
                  'problema', string(problema), 'semente', semente);
    Problem = UserProblem('evalFcn', batchEval, 'initFcn', @(N,varargin) X0(1:N,:), ...
        'D', D, 'lower', xl, 'upper', xu, 'maxFE', maxfe, ...
        'N', 100, 'once', true, 'data', data);         % maxRuntime fica inf (N.0.5)

    % (6) SEMENTE (D59): rng DEPOIS de construir o Problem, ANTES do Solve.
    rng(semente, 'twister');

    % (7) Algoritmo REAL: save=-K (sem .mat/figura — N.0.3/4), outputFcn=hook (②).
    %     ParEGO sem 'parameter': ParameterSet(10000) = IFEs do paper.
    K = 20;
    algo = ParEGO('save', -K, ...
        'outputFcn', @(A,P) hook_output(A, P, buf, bud, []));
    term = "normal";
    try
        algo.Solve(Problem);                           % engole PlatEMO:Termination
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination')
            term = "hard_stop";                        % nunca deveria vazar (Solve engole)
        else
            jsonl_line(fid, 'footer', {'status', "failed", 'erro', string(e.message), ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, '[R1-b1 FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end

    % (8) EXPORT das 4 camadas (§17.2/§17.3): ① do wrapper; ②③/timing do buffer.
    R = bud.records();                                 % catalogo ① (== 31D-1 linhas)
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (9) CP-init por-run (D87/D88): hash da init X (float64) = sidecar do DoE.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);

    % (10) Encanamento objetivo (D89/D21): FE final = 31D-1 EXATO E CP-init OK.
    %      Falha honesta (D23/D81): gate reprovado -> manifesto/footer 'failed'.
    ok_flag = (bud.fe == maxfe) && cp_ok;
    st_str  = "ok"; if ~ok_flag, st_str = "failed"; end

    % (11) MANIFESTO (§17.2/§17.7) + dicionario de sigma (DEF-C4/D47).
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    man.algo_version = "b1-ParEGO-PlatEMO4.15";
    man.status = st_str;
    man.params = struct('N_lambda', Nlam, 'IFEs', 10000, 'rho', 0.05, ...
        'dace', "regpoly1+corrgauss", 'theta0', 10, ...
        'theta_bounds', "[1e-5,20]", 'warm_theta', true, ...
        'mle', "boxmin SEM restarts (CODIGO; paper: Nelder-Mead 20 restarts)", ...
        'subset', "top-(11D-1+25) por PCheby, deterministico + dedup 1e-6 (CODIGO; paper: 1/2 melhores + 1/2 aleatorias)", ...
        'normalizacao', "min/max do arquivo por iteracao (B1.6 fechada: pelo ARQUIVO, nao por limites conhecidos)", ...
        'ga_interno', "geracional c/ truncamento elitista, torneio bugado (EvolALG:16 — CODIGO K.3, mantido)");
    man.sigma_dict = struct( ...
        'mu_0', "escalar de Tchebycheff aumentado (rho=0.05) PREDITO pelo GP mono-output — LOSSY (D47): nao des-agrega em mu por objetivo; reais por-objetivo via real_solution_id -> ①", ...
        'sigma_0', "sqrt(max(mse,0)) do GP mono-output do escalar (guard P2/L8) — regua muda por iteracao (o lambda muda); interpretar com transf_params", ...
        'transf_params', "{lambda, min, max, gbest} da iteracao (C3/D47) — obrigatorios p/ interpretar mu_0/sigma_0");
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', st_str, 'fe_final', bud.fe, 'maxfe', maxfe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok, 'termino', string(term)});
    fclose(fid);

    % (12) Higiene de memoria da ponte (D86/N.0.8): solta o Problem pymoo do run.
    try, py.gc.collect(); catch, end

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'N_lambda', Nlam, 'n_geracoes', buf.nGeracoes(), ...
        'cache_hits', bud.cache_hits, 'termino', string(term), ...
        'doe_hash_run', string(doe_hash_run), ...
        'doe_hash_sidecar', string(doe.hash), 'cp_ok', cp_ok);
    if ~ok_flag
        fprintf(2, ['[R1-b1] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
end


function ensure_paths_b1(ROOT)
% addpath(genpath) da arvore PlatEMO 4.15 se o ParEGO nao estiver no path
% (N.0.1). Rede p/ chamada direta de experiment() (o despachante ja faz por
% worker). O ParEGO e built-in da arvore — nenhuma pasta externa.
    if isempty(which('ParEGO')) || isempty(which('UserProblem')) || isempty(which('OperatorGA'))
        pr = fullfile(ROOT, 'algorithms', '_PlatEMO', 'PlatEMO');
        if isfolder(pr), addpath(genpath(pr)); end
    end
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-b3 (K-RVEA REAL, built-in PlatEMO 4.15) — fan-out da R1 no padrao do
%  caso-modelo c217 (receita N.0 do handoff R1-c217 §4). O que e ESPECIFICO do
%  b3: 'N',100 = nº de vetores de referencia (D20; UniformPoint ajusta p/
%  100 em M=2 / 91 em M=3 -> delta=0.05*N), KRVEA sem 'parameter' (alpha=2/
%  wmax=20/mu=5 = defaults do codigo = paper), o check dedup-DoE (1o fit DACE
%  sem dedup — L.2) e a instrumentacao b3_instrument (③ DEF-C2/B3.2 + S.7).
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_b3(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();

    % Arvore PlatEMO 4.15 no path (N.0.1) — rede p/ chamada direta.
    ensure_paths_b3(ROOT);

    % (0) PONTE: repo-root no sys.path; importa src.* (A2/§2/§18).
    ctx = bridge_ctx(ROOT);

    % (1) Problema Python via ponte -> D, M, bounds NATIVOS (§5.5).
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl(:).'; xu = pp.xu(:).';
    maxfe = 31*D - 1;  n_init = 11*D - 1;
    % Nº de vetores de referencia (D20: paper nao prescreve N p/ M=2 -> 100).
    % UniformPoint e deterministico (L.0) — so p/ registrar N/delta EFETIVOS.
    [~, Nref] = UniformPoint(100, M);
    delta = 0.05 * Nref;

    % (2) DoE 11D-1 do artefato (D63/D87) — CARREGADO, NUNCA regenerado.
    doe = load_doe(problema, semente, D, dataRoot);
    X0  = doe.X;                                   % n_init x D (float64, nativo)
    assert(size(X0,1) == n_init, 'DoE tem %d linhas != 11D-1=%d', size(X0,1), n_init);
    % CP-bounds (§5.5): bounds do problema == sidecar do DoE (identidade nativa).
    assert(max(abs(xl(:)-doe.xl(:)))==0 && max(abs(xu(:)-doe.xu(:)))==0, ...
           'CP-bounds: bounds do problema != sidecar do DoE');

    % (3) .jsonl (§17.5) + wrapper de FE (FEBudget) com o logger acoplado.
    jsonl  = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    fid    = jsonl_open(jsonl);
    logger = struct('guard', @(name, varargin) ...
                    jsonl_line(fid, 'guard', [{'name'}, {name}, varargin]));

    % Check dedup-DoE (L.2/S.7: "DoE injetado DEVE ser livre de duplicatas" —
    % o 1o fit DACE roda SEM dedup; sites duplicados = falha dura, DEF-A8).
    % Duplicata no artefato = violacao de pre-condicao -> guard + falha honesta.
    if size(unique(X0, 'rows'), 1) ~= n_init
        jsonl_line(fid, 'guard', {'name', "dedup_doe", 'motivo', ...
            "DoE do artefato contem duplicatas — 1o fit DACE exigiria dedup (L.2)"});
        fclose(fid);
        error('b3:dedup_doe', 'DoE %s/%d contem duplicatas (L.2) — para-e-loga (D81)', ...
              char(problema), semente);
    end

    % bud CRIADO ANTES do Problem: o probe do construtor avalia DoE[0] (initFcn),
    % que o lote-init reencontra como CACHE-HIT (0 FE, D89) -> a ① fecha com
    % EXATAMENTE 31D-1 linhas, sem poluir o catalogo (receita N.0 do c217).
    bud = FEBudget(D, maxfe, n_init, logger);
    buf = RunBuffer();
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "online", 'maxfe', maxfe, ...
        'doe_hash', string(doe.hash), 'algo', "b3-KRVEA-PlatEMO4.15", ...
        'N_vetores', Nref, 'alpha', 2, 'wmax', 20, 'mu', 5, 'delta', delta});

    % (4) evalFcn por-x (a ponte, bounds nativos) + embrulho de LOTE (D61) — o
    %     c217_batch_eval e GENERICO (handoff R1-c217 §7): hard-stop no meio do lote.
    evalFcnPerX = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));
    batchEval   = @(X, varargin) c217_batch_eval(X, bud, evalFcnPerX);

    % (5) UserProblem (contrato N.0/L.0): once=true (lote), bounds nativos, minimiza.
    %     N=100 governa o nº de vetores de referencia (KRVEA.m:30 ajusta p/ Nref).
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, ...
                  'run_id', string(nm_run_id(exp, alg, problema, semente)), ...
                  'problema', string(problema), 'semente', semente);
    Problem = UserProblem('evalFcn', batchEval, 'initFcn', @(N,varargin) X0(1:N,:), ...
        'D', D, 'lower', xl, 'upper', xu, 'maxFE', maxfe, ...
        'N', 100, 'once', true, 'data', data);         % maxRuntime fica inf (N.0.5)

    % (6) SEMENTE (D59): rng DEPOIS de construir o Problem, ANTES do Solve.
    rng(semente, 'twister');

    % (7) Algoritmo REAL: save=-K (sem .mat/figura — N.0.3/4), outputFcn=hook (②).
    %     KRVEA sem 'parameter': ParameterSet(2,20,5) = alpha/wmax/mu do paper.
    K = 20;
    algo = KRVEA('save', -K, ...
        'outputFcn', @(A,P) hook_output(A, P, buf, bud, []));
    term = "normal";
    try
        algo.Solve(Problem);                           % engole PlatEMO:Termination
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination')
            term = "hard_stop";                        % nunca deveria vazar (Solve engole)
        else
            jsonl_line(fid, 'footer', {'status', "failed", 'erro', string(e.message), ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, '[R1-b3 FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end

    % (8) EXPORT das 4 camadas (§17.2/§17.3): ① do wrapper; ②③/timing do buffer.
    R = bud.records();                                 % catalogo ① (== 31D-1 linhas)
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (9) CP-init por-run (D87/D88): hash da init X (float64) = sidecar do DoE.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);

    % (10) Encanamento objetivo (D89/D21): FE final = 31D-1 EXATO E CP-init OK.
    %      Falha honesta (D23/D81): gate reprovado -> manifesto/footer 'failed'.
    ok_flag = (bud.fe == maxfe) && cp_ok;
    st_str  = "ok"; if ~ok_flag, st_str = "failed"; end

    % (11) MANIFESTO (§17.2/§17.7) + dicionario de sigma (DEF-C4/B3.2).
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    man.algo_version = "b3-KRVEA-PlatEMO4.15";
    man.status = st_str;
    man.params = struct('N_vetores', Nref, 'alpha', 2, 'wmax', 20, 'mu', 5, ...
                        'delta', delta, 'dace', "regpoly1+corrgauss", ...
                        'theta0', 5, 'theta_bounds', "[1e-5,100]", ...
                        'warm_theta', true);
    man.sigma_dict = struct( ...
        'sigma_j', "sqrt(max(MSE_j,0)) por objetivo do DACE (B3.2 — unidade de export); o criterio INTERNO do switch usa a MEDIA das MSEs SEM raiz (codigo oficial)", ...
        'geracao_3', "TODAS as linhas de um ciclo levam geracao=CICLO (datada pelo retreino, §17.1; join direto com a ②/D31); blocos por geracao interna do RVEA-surrogate em ORDEM de linha, contagens pop_por_w na linha b3_gen do .jsonl");
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', st_str, 'fe_final', bud.fe, 'maxfe', maxfe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok, 'termino', string(term)});
    fclose(fid);

    % (12) Higiene de memoria da ponte (D86/N.0.8): solta o Problem pymoo do run.
    try, py.gc.collect(); catch, end

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'N_vetores', Nref, 'n_geracoes', buf.nGeracoes(), ...
        'cache_hits', bud.cache_hits, 'termino', string(term), ...
        'doe_hash_run', string(doe_hash_run), ...
        'doe_hash_sidecar', string(doe.hash), 'cp_ok', cp_ok);
    if ~ok_flag
        fprintf(2, ['[R1-b3] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
end


function ensure_paths_b3(ROOT)
% addpath(genpath) da arvore PlatEMO 4.15 se o K-RVEA nao estiver no path
% (N.0.1). Rede p/ chamada direta de experiment() (o despachante ja faz por
% worker). O K-RVEA e built-in da arvore — nenhuma pasta externa.
    if isempty(which('KRVEA')) || isempty(which('UserProblem')) || isempty(which('OperatorGA'))
        pr = fullfile(ROOT, 'algorithms', '_PlatEMO', 'PlatEMO');
        if isfolder(pr), addpath(genpath(pr)); end
    end
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-b4 (CSEA REAL, built-in PlatEMO 4.15) — fan-out da R1 no padrao do
%  caso-modelo c217 (receita N.0 do handoff R1-c217 §4). O que e ESPECIFICO do
%  b4: 'N',50 do paper (B4.2 — load-bearing: limita o cap da Population via
%  RefSelect e o nº de geracoes sob orcamento), CSEA sem 'parameter' (K=6/
%  gmax=3000 = defaults do codigo = paper), os patches cap109/cpu/arquivo-
%  inteiro/Balde C (na arvore) e a instrumentacao b4_instrument (③ DEF-C1
%  classe/L + S.7 + §17.6). Toolboxes: Deep Learning (trainNetwork/predict) +
%  Statistics (pdist2) — falha honesta do proprio MATLAB se ausentes.
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_b4(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();

    % Arvore PlatEMO 4.15 no path (N.0.1) — rede p/ chamada direta.
    ensure_paths_b4(ROOT);

    % (0) PONTE: repo-root no sys.path; importa src.* (A2/§2/§18).
    ctx = bridge_ctx(ROOT);

    % (1) Problema Python via ponte -> D, M, bounds NATIVOS (§5.5).
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl(:).'; xu = pp.xu(:).';
    maxfe = 31*D - 1;  n_init = 11*D - 1;

    % (2) DoE 11D-1 do artefato (D63/D87) — CARREGADO, NUNCA regenerado.
    doe = load_doe(problema, semente, D, dataRoot);
    X0  = doe.X;                                   % n_init x D (float64, nativo)
    assert(size(X0,1) == n_init, 'DoE tem %d linhas != 11D-1=%d', size(X0,1), n_init);
    % CP-bounds (§5.5): bounds do problema == sidecar do DoE (identidade nativa).
    assert(max(abs(xl(:)-doe.xl(:)))==0 && max(abs(xu(:)-doe.xu(:)))==0, ...
           'CP-bounds: bounds do problema != sidecar do DoE');

    % (3) .jsonl (§17.5) + wrapper de FE (FEBudget) com o logger acoplado.
    jsonl  = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    fid    = jsonl_open(jsonl);
    logger = struct('guard', @(name, varargin) ...
                    jsonl_line(fid, 'guard', [{'name'}, {name}, varargin]));
    % bud CRIADO ANTES do Problem: o probe do construtor avalia DoE[0] (initFcn),
    % que o lote-init reencontra como CACHE-HIT (0 FE, D89) -> a ① fecha com
    % EXATAMENTE 31D-1 linhas, sem poluir o catalogo (receita N.0 do c217).
    bud = FEBudget(D, maxfe, n_init, logger);
    buf = RunBuffer();
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "online", 'maxfe', maxfe, ...
        'doe_hash', string(doe.hash), 'algo', "b4-CSEA-PlatEMO4.15", ...
        'N', 50, 'K_refs', 6, 'gmax', 3000, ...
        'operadores', "BaldeC {1,20,1,20} substitui {1,15,1,5} (§6.2/§6.4)", ...
        'treino', "arquivo inteiro (B4.6/D30)", 'exec_env', "cpu"});

    % (4) evalFcn por-x (a ponte, bounds nativos) + embrulho de LOTE (D61) — o
    %     c217_batch_eval e GENERICO (handoff R1-c217 §7): hard-stop no meio do lote.
    evalFcnPerX = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));
    batchEval   = @(X, varargin) c217_batch_eval(X, bud, evalFcnPerX);

    % (5) UserProblem (contrato N.0/L.0): once=true (lote), bounds nativos, minimiza.
    %     N=50 do paper (B4.2): cap da Population (RefSelect(Arc,Problem.N)).
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, ...
                  'run_id', string(nm_run_id(exp, alg, problema, semente)), ...
                  'problema', string(problema), 'semente', semente);
    Problem = UserProblem('evalFcn', batchEval, 'initFcn', @(N,varargin) X0(1:N,:), ...
        'D', D, 'lower', xl, 'upper', xu, 'maxFE', maxfe, ...
        'N', 50, 'once', true, 'data', data);          % maxRuntime fica inf (N.0.5)

    % (6) SEMENTE (D59): rng DEPOIS de construir o Problem, ANTES do Solve.
    rng(semente, 'twister');

    % (7) Algoritmo REAL: save=-K (sem .mat/figura — N.0.3/4), outputFcn=hook (②).
    %     CSEA sem 'parameter': ParameterSet(6,3000) = K/gmax do paper.
    K = 20;
    algo = CSEA('save', -K, ...
        'outputFcn', @(A,P) hook_output(A, P, buf, bud, []));
    term = "normal";
    try
        algo.Solve(Problem);                           % engole PlatEMO:Termination
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination')
            term = "hard_stop";                        % nunca deveria vazar (Solve engole)
        else
            jsonl_line(fid, 'footer', {'status', "failed", 'erro', string(e.message), ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, '[R1-b4 FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end

    % (8) EXPORT das 4 camadas (§17.2/§17.3): ① do wrapper; ②③/timing do buffer.
    R = bud.records();                                 % catalogo ① (== 31D-1 linhas)
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (9) CP-init por-run (D87/D88): hash da init X (float64) = sidecar do DoE.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);

    % (10) Encanamento objetivo (D89/D21): FE final = 31D-1 EXATO E CP-init OK.
    %      Falha honesta (D23/D81): gate reprovado -> manifesto/footer 'failed'.
    ok_flag = (bud.fe == maxfe) && cp_ok;
    st_str  = "ok"; if ~ok_flag, st_str = "failed"; end

    % (11) MANIFESTO (§17.2/§17.7) + dicionario (DEF-C4/DEF-C1).
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    man.algo_version = "b4-CSEA-PlatEMO4.15";
    man.status = st_str;
    man.params = struct('N', 50, 'K_refs', 6, 'gmax', 3000, ...
        'rede', "H=2D, 1 oculta; zscore (featureInputLayer, CSEA.m:36) + BatchNorm + ReLU + sigmoide + regressionLayer (MSE)", ...
        'treinador', "adam lr=1e-3, 100 epocas, batch 32, sem early-stop, rede NOVA/Glorot por geracao (divergencia em bloco vs paper LM/T=500 — CODIGO, registrada)", ...
        'operadores', "Balde C {1,20,1,20} SUBSTITUI os nativos {1,15,1,5} (§6.2/§6.4)", ...
        'treino', "arquivo INTEIRO (B4.6/D30 — ARTIGO)", ...
        'gate', "4 ramos, 0.4 hardcoded; L>0.9 avalia / L<0.1 descarta; tr=0.5*min(rr,1-rr)", ...
        'exec_env', "cpu (N.2.4 — repro)");
    man.sigma_dict = struct( ...
        'pred_confianca', "L in (0,1) = saida sigmoide da FNN (pseudo-prob. de 'bom'); pred_classe = leitura binaria L>=0.5; a semantica da SELECAO (ramo 3 seleciona L<0.1 — modelo invertido) esta no campo `ramo` do .jsonl", ...
        'cobertura_3', "lote SELECIONADO p/ avaliacao real por geracao (cartao b4: 'L dos selecionados'); (p0,p1,rr,tr) por geracao no .jsonl (linha b4_gen)");
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', st_str, 'fe_final', bud.fe, 'maxfe', maxfe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok, 'termino', string(term)});
    fclose(fid);

    % (12) Higiene de memoria da ponte (D86/N.0.8): solta o Problem pymoo do run.
    try, py.gc.collect(); catch, end

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'n_geracoes', buf.nGeracoes(), ...
        'cache_hits', bud.cache_hits, 'termino', string(term), ...
        'doe_hash_run', string(doe_hash_run), ...
        'doe_hash_sidecar', string(doe.hash), 'cp_ok', cp_ok);
    if ~ok_flag
        fprintf(2, ['[R1-b4] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
end


function ensure_paths_b4(ROOT)
% addpath(genpath) da arvore PlatEMO 4.15 se o CSEA nao estiver no path
% (N.0.1). Rede p/ chamada direta de experiment() (o despachante ja faz por
% worker). O CSEA e built-in da arvore — nenhuma pasta externa.
    if isempty(which('CSEA')) || isempty(which('UserProblem')) || isempty(which('OperatorGA'))
        pr = fullfile(ROOT, 'algorithms', '_PlatEMO', 'PlatEMO');
        if isfolder(pr), addpath(genpath(pr)); end
    end
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-e7 (EDN-ARMOEA REAL, built-in PlatEMO 4.15 — N.2.1) — fan-out da R1 no
%  padrao do caso-modelo c217 (receita N.0 do handoff R1-c217 §4). O que e
%  ESPECIFICO do e7: 'N',100 = pop interna do ARMOEA (D20; W=UniformPoint ->
%  NW=100 em M=2 / NBI 91 em M=3 — denominador do Ratio; Problem.N NAO e
%  reescrito pelo algoritmo), EDNARMOEA sem 'parameter' (delta=0.05/wmax=20/
%  Ke=3 = defaults do codigo; 4 divergencias vs paper em CODIGO — B6.6), os
%  patches P1 (DoE D94 :31-:32 JUNTAS), dropout 0.1 (D30 — ARTIGO) e guard
%  sqrt(max(var,0)) no Estimate (na arvore), a guarda (c) do D60 (saldo
%  congelado LOGADO — sem dedup de infill) e a instrumentacao e7_instrument
%  (③ DEF-C2 por geracao interna + C3 translacao + S.7 + §17.6 + RAM D86).
%  Toolboxes: Deep Learning (mapminmax; assert nativo do EDNARMOEA) +
%  Statistics (kmeans/pdist2). Custo: ~8e4+8e3*ciclos passos SGD (B6.4 —
%  medir no piloto, NUNCA reduzir orcamento).
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_e7(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();

    % Arvore PlatEMO 4.15 no path (N.0.1) — rede p/ chamada direta.
    ensure_paths_e7(ROOT);

    % (0) PONTE: repo-root no sys.path; importa src.* (A2/§2/§18).
    ctx = bridge_ctx(ROOT);

    % (1) Problema Python via ponte -> D, M, bounds NATIVOS (§5.5).
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl(:).'; xu = pp.xu(:).';
    maxfe = 31*D - 1;  n_init = 11*D - 1;
    % NW = nº de vetores de referencia do ARMOEA (denominador do Ratio):
    % UniformPoint(100,M) -> 100 (M=2) / NBI 91 (M=3). Problem.N fica 100
    % (popsize interna — o EDNARMOEA NAO reescreve Problem.N).
    Wref = UniformPoint(100, M);
    NW   = size(Wref, 1);

    % (2) DoE 11D-1 do artefato (D63/D87) — CARREGADO, NUNCA regenerado.
    doe = load_doe(problema, semente, D, dataRoot);
    X0  = doe.X;                                   % n_init x D (float64, nativo)
    assert(size(X0,1) == n_init, 'DoE tem %d linhas != 11D-1=%d', size(X0,1), n_init);
    % CP-bounds (§5.5): bounds do problema == sidecar do DoE (identidade nativa).
    assert(max(abs(xl(:)-doe.xl(:)))==0 && max(abs(xu(:)-doe.xu(:)))==0, ...
           'CP-bounds: bounds do problema != sidecar do DoE');

    % (3) .jsonl (§17.5) + wrapper de FE (FEBudget) com o logger acoplado.
    jsonl  = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    fid    = jsonl_open(jsonl);
    logger = struct('guard', @(name, varargin) ...
                    jsonl_line(fid, 'guard', [{'name'}, {name}, varargin]));
    % bud CRIADO ANTES do Problem: o probe do construtor avalia DoE[0] (initFcn),
    % que o lote-init reencontra como CACHE-HIT (0 FE, D89) -> a ① fecha com
    % EXATAMENTE 31D-1 linhas, sem poluir o catalogo (receita N.0 do c217).
    bud = FEBudget(D, maxfe, n_init, logger);
    buf = RunBuffer();
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "online", 'maxfe', maxfe, ...
        'doe_hash', string(doe.hash), 'algo', "e7-EDNARMOEA-PlatEMO4.15", ...
        'N_pop', 100, 'NW', NW, 'delta', 0.05, 'wmax', 20, 'Ke', 3, 'T', 100, ...
        'rede', "40/40 ReLU+tanh multi-M", 'dropP', "[0.1,0.1] (D30 ARTIGO)", ...
        'treino', "SGD 8e4 init / 8e3 update, lr=0.01, batch=D", ...
        'sigma_dict', "mu_j/sigma_j=media/desvio POPULACIONAL das T=100 passagens MC-dropout POR OBJETIVO, no ESPACO DO MODELO (cru no ciclo 1; transladado por ymin=min(A.objs) depois — C3 transf_params)"});

    % (4) evalFcn por-x (a ponte, bounds nativos) + embrulho de LOTE (D61) — o
    %     c217_batch_eval e GENERICO (handoff R1-c217 §7): hard-stop no meio do lote.
    evalFcnPerX = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));
    batchEval   = @(X, varargin) c217_batch_eval(X, bud, evalFcnPerX);

    % (5) UserProblem (contrato N.0/L.0): once=true (lote), bounds nativos, minimiza.
    %     N=100 governa a popsize interna E o UniformPoint dos vetores (D20).
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, ...
                  'run_id', string(nm_run_id(exp, alg, problema, semente)), ...
                  'problema', string(problema), 'semente', semente);
    Problem = UserProblem('evalFcn', batchEval, 'initFcn', @(N,varargin) X0(1:N,:), ...
        'D', D, 'lower', xl, 'upper', xu, 'maxFE', maxfe, ...
        'N', 100, 'once', true, 'data', data);         % maxRuntime fica inf (N.0.5)

    % (6) SEMENTE (D59): rng DEPOIS de construir o Problem, ANTES do Solve.
    rng(semente, 'twister');

    % (7) Algoritmo REAL: save=-K (sem .mat/figura — N.0.3/4), outputFcn=hook (②).
    %     EDNARMOEA sem 'parameter': ParameterSet(0.05,20,3) = delta/wmax/Ke.
    K = 20;
    algo = EDNARMOEA('save', -K, ...
        'outputFcn', @(A,P) hook_output(A, P, buf, bud, []));
    term = "normal";
    try
        algo.Solve(Problem);                           % engole PlatEMO:Termination
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination')
            term = "hard_stop";                        % nunca deveria vazar (Solve engole)
        else
            jsonl_line(fid, 'footer', {'status', "failed", 'erro', string(e.message), ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, '[R1-e7 FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end

    % (8) EXPORT das 4 camadas (§17.2/§17.3): ① do wrapper; ②③/timing do buffer.
    R = bud.records();                                 % catalogo ① (== 31D-1 linhas)
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (9) CP-init por-run (D87/D88): hash da init X (float64) = sidecar do DoE.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);

    % (10) Encanamento objetivo (D89/D21): FE final = 31D-1 EXATO E CP-init OK.
    %      Falha honesta (D23/D81): gate reprovado -> manifesto/footer 'failed'.
    ok_flag = (bud.fe == maxfe) && cp_ok;
    st_str  = "ok"; if ~ok_flag, st_str = "failed"; end

    % (11) MANIFESTO (§17.2/§17.7) + dicionario de sigma (DEF-C4/DEF-C3).
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    man.algo_version = "e7-EDNARMOEA-PlatEMO4.15";
    man.status = st_str;
    man.params = struct('N_pop', 100, 'NW', NW, 'delta', 0.05, 'wmax', 20, ...
        'Ke', 3, 'T', 100, 'rede', "40/40, ReLU+tanh, unica multi-M", ...
        'dropP', "[0.1,0.1] entrada+oculta, invertido, ATIVO na inferencia (D30 ARTIGO; codigo shipped [0.2,0.5])", ...
        'treino', "SGD puro 8e4 init/8e3 update, lr=0.01, wd=1e-5 so em W (hardcode), batch=D, sem momentum", ...
        'init_pesos', "N(0,1/fan_in) Marsaglia (CODIGO; paper U[-0.5,0.5])", ...
        'cap_treino', "11D-1 (recentes + max-angulo, SelectTrainData)", ...
        'divergencias_codigo', "delta 0.05 (paper 0.08) · Ke 3 (paper 5) · N 100 (paper P=50, D20) · init pesos — B6.6; dropout CORRIGIDO p/ 0.1 (D30)", ...
        'sem_dedup_infill', "duplicata = cache-hit 0 FE (D89), slot perdido; guarda (c) D60 saldo_congelado LOGA");
    man.sigma_dict = struct( ...
        'mu_j', "media das T=100 passagens MC-dropout por objetivo, no ESPACO DO MODELO: cru (ciclo 1) ou transladado por ymin=min(A.objs) do fim do ciclo anterior (SelectTrainData — C3); cru = mu + ymin (transf_params)", ...
        'sigma_j', "desvio POPULACIONAL das T=100 passagens por objetivo (guard sqrt(max(var,0)) — Estimate.m); invariante a translacao", ...
        'transf_params', "{ymin} da predicao do ciclo (C3) — obrigatorio p/ voltar mu ao cru; geracao_3 = CICLO (datada pelo retreino, precedente b3)");
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', st_str, 'fe_final', bud.fe, 'maxfe', maxfe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok, 'termino', string(term)});
    fclose(fid);

    % (12) Higiene de memoria da ponte (D86/N.0.8): solta o Problem pymoo do run.
    try, py.gc.collect(); catch, end

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'NW', NW, 'n_geracoes', buf.nGeracoes(), ...
        'cache_hits', bud.cache_hits, 'termino', string(term), ...
        'doe_hash_run', string(doe_hash_run), ...
        'doe_hash_sidecar', string(doe.hash), 'cp_ok', cp_ok);
    if ~ok_flag
        fprintf(2, ['[R1-e7] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
end


function ensure_paths_e7(ROOT)
% addpath(genpath) da arvore PlatEMO 4.15 se o EDN-ARMOEA nao estiver no path
% (N.0.1). Rede p/ chamada direta de experiment() (o despachante ja faz por
% worker). O EDN-ARMOEA e built-in da arvore (N.2.1) — nenhuma pasta externa.
%
% ⚠ PRECEDENCIA DE PATH (achado R1-e7; mesmo padrao do ensure_paths_c141/S.8):
% o DRLOS-EMCMO (built-in FORA do estudo) vendoriza um Dropout/ BYTE-IDENTICO
% ao do EDN-ARMOEA e vem ANTES no genpath (D<E) -> Estimate/trainmodel/
% trainNet/testNet/updatemodel/dropout/iniA/MgaussRandom resolveriam p/ as
% copias STOCK do DRLOS (chamadas de EDNARMOEA.m sao via PATH — Dropout/ nao e
% same-folder) e os patches do e7 (dropout 0.1 D30, guard do Estimate) NUNCA
% rodariam, silenciosamente. Prepend da pasta do e7 + asserts de which.
    if isempty(which('EDNARMOEA')) || isempty(which('UserProblem')) || isempty(which('OperatorGA'))
        pr = fullfile(ROOT, 'algorithms', '_PlatEMO', 'PlatEMO');
        if isfolder(pr), addpath(genpath(pr)); end
    end
    e7dir = fullfile(ROOT, 'algorithms', '_PlatEMO', 'PlatEMO', 'Algorithms', ...
                     'Multi-objective optimization', 'EDN-ARMOEA');
    if ~contains(which('Estimate'), [filesep 'EDN-ARMOEA' filesep])
        assert(isfolder(e7dir), 'e7: pasta do EDN-ARMOEA ausente: %s', e7dir);
        addpath(genpath(e7dir));               % prepend -> precedencia do e7
    end
    for fn = ["Estimate","trainmodel","updatemodel","trainNet","testNet", ...
              "dropout","iniA","MgaussRandom"]
        assert(contains(which(char(fn)), [filesep 'EDN-ARMOEA' filesep]), ...
               'e7: %s nao resolve p/ a copia do EDN-ARMOEA (precedencia de path)', char(fn));
    end
end


% ════════════════════════════════════════════════════════════════════════════
%  PONTE Python (pyenv InProcess) — A2/§2/§18
% ════════════════════════════════════════════════════════════════════════════

function ROOT = harness_root()
    % Raiz do repo = pasta-pai de src/ (este arquivo vive em src/).
    ROOT = fileparts(fileparts(mfilename('fullpath')));
end

function ctx = bridge_ctx(ROOT)
    % Garante o repo-root no sys.path do Python embutido e importa src.*.
    if count(py.sys.path, ROOT) == 0
        insert(py.sys.path, int32(0), ROOT);
    end
    ctx.expm = py.importlib.import_module('src.experiment');
    ctx.prm  = py.importlib.import_module('src.problems');
    ctx.inst = py.getattr(ctx.expm, '_instantiate_problem');  % '_' => getattr
end

function pp = py_problem(ctx, problema)
    % Instancia o problema pelo short name e le D/M/bounds (bounds NATIVOS).
    obj = ctx.inst(problema);
    pp.obj = obj;
    pp.D = double(obj.n_var);
    pp.M = double(obj.n_obj);
    pp.xl = double(py.numpy.asarray(obj.xl));
    pp.xu = double(py.numpy.asarray(obj.xu));
end


% ════════════════════════════════════════════════════════════════════════════
%  DoE (D63/D87) — carregado do artefato, NUNCA regenerado
% ════════════════════════════════════════════════════════════════════════════

function doe = load_doe(problema, semente, D, dataRoot)
    pq  = nm_doe_path(problema, semente, dataRoot);
    man = nm_doe_manifest_path(problema, semente, dataRoot);
    assert(isfile(pq),  'DoE ausente: %s', pq);
    assert(isfile(man), 'sidecar do DoE ausente: %s', man);
    side = jsondecode(fileread(man));
    cols = cellstr(side.columns);                          % {'x0',...,'x{D-1}'}
    t = parquetread(pq);
    doe.X = double(t{:, cols});                            % n_init x D (float64)
    doe.hash = char(side.doe_hash);
    doe.xl = double(side.bounds.xl);
    doe.xu = double(side.bounds.xu);
    assert(size(doe.X,2) == D, 'DoE tem %d colunas != D=%d', size(doe.X,2), D);
end


% ════════════════════════════════════════════════════════════════════════════
%  EXPORT §17.2 — 4 camadas parquet (brotli + single, SEM round — D53; atomico)
% ════════════════════════════════════════════════════════════════════════════

function p = write_real(exp, alg, problema, semente, R, D, M, dataRoot)
    % ① Catalogo REAL: uma linha por solution_id (§17.2). Todas nao-nulas.
    n = numel(R);
    X = single(vertcat(R.x));  Fm = single(vertcat(R.f));
    T = table();
    T.algoritmo   = repmat(string(alg), n, 1);
    T.problema    = repmat(string(problema), n, 1);
    T.semente     = repmat(int32(semente), n, 1);
    T.solution_id = int32([R.solution_id].');
    for j = 0:D-1, T.(sprintf('x%d', j)) = X(:, j+1); end
    for j = 0:M-1, T.(sprintf('f%d', j)) = Fm(:, j+1); end
    T.fe_index = int32([R.fe_index].');
    T.fase     = string({R.fase}.');
    p = nm_layer_path(exp, alg, problema, semente, 'real', dataRoot);
    atomic_parquet(p, T);
end

function p = write_pop(exp, alg, problema, semente, pop, dataRoot)
    % ② membership (geracao, solution_id) — §17.2/D31.
    n = size(pop, 1);
    T = table();
    T.algoritmo   = repmat(string(alg), n, 1);
    T.problema    = repmat(string(problema), n, 1);
    T.semente     = repmat(int32(semente), n, 1);
    T.geracao     = int32(pop(:, 1));
    T.solution_id = int32(pop(:, 2));
    p = nm_layer_path(exp, alg, problema, semente, 'pop', dataRoot);
    atomic_parquet(p, T);
end

function p = write_surrogate(exp, alg, problema, semente, srows, D, M, regime, dataRoot)
    % ③ surrogate: schema unico C1/C3 (§17.2). Numericos ausentes => NaN (=NULL
    % no parquet MATLAB); strings ausentes => <missing> (=NULL).
    %
    % [R1-b1 · infra-perf] Montagem das colunas em UMA passada O(n) sobre srows
    % (prealocado), no lugar dos builders arrayfun por coluna: a acumulacao de
    % STRING arrays do arrayfun e O(n^2) e travou o export da ③ do b1/ZDT1
    % (~750k linhas — 100% CPU em libmwstring_* por horas, verificado por
    % sample). Semantica IDENTICA a dos helpers opt_obj/opt_scal/rsi_val
    % (mesmos NaN/missing, mesma ordem de colunas, mesmos tipos, mesmo branch
    % int32/double do rsi) — provada por re-run do MMF1 + comparacao pyarrow.
    n = numel(srows);
    GER = zeros(n, 1);
    X   = zeros(n, D);
    RSI = NaN(n, 1);
    MU  = NaN(n, M);  SG = NaN(n, M);
    PS  = NaN(n, 1);  PCONF = NaN(n, 1);
    tipo   = repmat(string(missing), n, 1);
    classe = repmat(string(missing), n, 1);
    modelo = repmat(string(missing), n, 1);
    espaco = repmat(string(missing), n, 1);
    ttipo  = repmat(string(missing), n, 1);
    tpar   = repmat(string(missing), n, 1);
    for k = 1:n
        r = srows{k};
        GER(k)  = r.geracao;
        X(k, :) = r.x;
        if ~isempty(r.real_solution_id), RSI(k) = double(r.real_solution_id); end
        v = r.mu;
        if ~isempty(v), m = min(numel(v), M); MU(k, 1:m) = v(1:m); end
        v = r.sigma;
        if ~isempty(v), m = min(numel(v), M); SG(k, 1:m) = v(1:m); end
        v = r.pred_score;
        if ~(isempty(v) || (isnumeric(v) && isnan(v))), PS(k) = double(v); end
        v = r.pred_confianca;
        if ~(isempty(v) || (isnumeric(v) && isnan(v))), PCONF(k) = double(v); end
        tipo(k)   = r.pred_tipo;
        classe(k) = r.pred_classe;
        modelo(k) = r.modelo_flag;
        espaco(k) = r.espaco_modelo;
        ttipo(k)  = r.transf_tipo;
        tpar(k)   = r.transf_params;
    end

    T = table();
    T.algoritmo = repmat(string(alg), n, 1);
    T.problema  = repmat(string(problema), n, 1);
    T.semente   = repmat(int32(semente), n, 1);
    T.regime    = repmat(string(regime), n, 1);
    T.geracao   = int32(GER);
    for j = 0:D-1, T.(sprintf('x%d', j)) = single(X(:, j+1)); end
    % real_solution_id: int32 quando TODOS presentes (casa com §17.2/int32); se
    % houver ausentes (candidato nao avaliado — caso do c217), cai p/ double+NaN
    % (a consolidacao re-casta p/ int32 nullable — MATLAB nao expressa int32-NULL).
    if all(~isnan(RSI))
        T.real_solution_id = int32(RSI);
    else
        T.real_solution_id = RSI;    % double com NaN => NULL
    end
    for j = 0:M-1, T.(sprintf('mu_%d', j))    = single(MU(:, j+1)); end
    for j = 0:M-1, T.(sprintf('sigma_%d', j)) = single(SG(:, j+1)); end
    T.pred_tipo      = tipo;
    T.pred_classe    = classe;
    T.pred_score     = single(PS);
    T.pred_confianca = single(PCONF);
    T.modelo_flag    = modelo;
    T.espaco_modelo  = espaco;
    T.transf_tipo    = ttipo;
    T.transf_params  = tpar;
    p = nm_layer_path(exp, alg, problema, semente, 'surrogate', dataRoot);
    atomic_parquet(p, T);
end

function p = write_timing(exp, alg, problema, semente, trows, dataRoot)
    % Camada de tempo §17.6: (run_id, geracao, n_acumulado, tempo_fit_s, tempo_busca_s).
    n = numel(trows);
    rid = nm_run_id(exp, alg, problema, semente);
    T = table();
    T.run_id       = repmat(string(rid), n, 1);
    T.geracao      = int32(arrayfun(@(k) trows{k}.geracao, (1:n).'));
    T.n_acumulado  = int32(arrayfun(@(k) trows{k}.n_acumulado, (1:n).'));
    T.tempo_fit_s  = single(arrayfun(@(k) trows{k}.tempo_fit_s, (1:n).'));
    T.tempo_busca_s = single(arrayfun(@(k) opt_scal(field_or(trows{k}, 'tempo_busca_s')), (1:n).'));
    p = nm_layer_path(exp, alg, problema, semente, 'timing', dataRoot);
    atomic_parquet(p, T);
end

function v = opt_obj(vec, j)
    % mu_j/sigma_j: NaN quando ausente OU mais curto que M (mono-output b1).
    if isempty(vec) || j+1 > numel(vec), v = single(NaN); else, v = single(vec(j+1)); end
end
function v = opt_scal(s)
    if isempty(s) || (isnumeric(s) && isnan(s)), v = single(NaN); else, v = single(s); end
end
function v = rsi_val(s)
    if isempty(s), v = NaN; else, v = double(s); end
end
function v = field_or(s, f)
    if isfield(s, f), v = s.(f); else, v = []; end
end


% ════════════════════════════════════════════════════════════════════════════
%  MANIFESTO (§17.2/§17.7) + escrita atomica
% ════════════════════════════════════════════════════════════════════════════

function man = build_manifest(exp, alg, problema, semente, maxfe, fe_final, ...
                              n_ger, doe_hash, cache_hits, dataRoot)
    rid = nm_run_id(exp, alg, problema, semente);
    local = struct();
    for ly = ["real","pop","surrogate","timing"]
        local.(ly) = nm_layer_path(exp, alg, problema, semente, char(ly), dataRoot);
    end
    local.jsonl    = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    local.manifest = nm_manifest_path(exp, alg, problema, semente, dataRoot);
    man = struct();
    man.schema_version = 1;
    man.run_id = string(rid);
    man.exp = string(exp); man.alg = string(alg);
    man.problema = string(problema); man.semente = semente;
    man.regime = "online"; man.q = 1; man.tier = ""; man.dist = "";
    man.status = "ok"; man.n_retries = 0; man.stack_trace = "";
    man.maxfe = maxfe; man.fe_final = fe_final; man.n_geracoes = n_ger;
    man.doe_hash = string(doe_hash); man.repo_hash = ""; man.algo_version = "stub-R1-00";
    man.env = struct('matlab', string(version), 'stack', "matlab-platemo", ...
                     'pymoo', "0.6.2");
    man.timing = struct('tempo_total_s', 0.0, 'tempo_fit_surrogate_s', 0.0, ...
                        'tempo_busca_s', 0.0, 'tempo_aval_real_s', 0.0);
    man.fit_series = {};
    man.cache_hits = cache_hits;
    man.fallback_ativado = false;
    man.paths = struct('local', local);
    man.created_at = iso_now();
    man.updated_at = iso_now();
end

function write_manifest(man, exp, alg, problema, semente, dataRoot)
    p = nm_manifest_path(exp, alg, problema, semente, dataRoot);
    atomic_write_text(p, jsonencode(man, 'PrettyPrint', true));
end


% ════════════════════════════════════════════════════════════════════════════
%  NAMING §17.7/D55 — espelho de src/naming.py (fonte unica dos caminhos)
% ════════════════════════════════════════════════════════════════════════════

function a = safe_alg(alg)
    a = strrep(strrep(char(alg), '/', '_'), ' ', '_');
end
function r = nm_run_id(exp, alg, problema, semente)
    r = sprintf('%s_%s_%s_%s', char(exp), safe_alg(alg), char(problema), num2str(semente));
end
function b = nm_base(exp, alg, problema, semente)
    b = ['exp_' nm_run_id(exp, alg, problema, semente)];
end
function d = nm_run_dir(exp, alg, dataRoot)
    d = fullfile(char(dataRoot), 'experiments', char(exp), safe_alg(alg));
end
function p = nm_layer_path(exp, alg, problema, semente, layer, dataRoot)
    fn = [nm_base(exp, alg, problema, semente) '__' layer '.parquet'];
    p = fullfile(nm_run_dir(exp, alg, dataRoot), fn);
end
function p = nm_jsonl_path(exp, alg, problema, semente, dataRoot)
    fn = [nm_base(exp, alg, problema, semente) '.jsonl'];
    p = fullfile(nm_run_dir(exp, alg, dataRoot), fn);
end
function p = nm_manifest_path(exp, alg, problema, semente, dataRoot)
    fn = [nm_base(exp, alg, problema, semente) '.manifest.json'];
    p = fullfile(nm_run_dir(exp, alg, dataRoot), fn);
end
function p = nm_doe_path(problema, semente, dataRoot)
    p = fullfile(char(dataRoot), 'doe', char(problema), ...
                 sprintf('doe_%s_%s.parquet', char(problema), num2str(semente)));
end
function p = nm_doe_manifest_path(problema, semente, dataRoot)
    p = fullfile(char(dataRoot), 'doe', char(problema), ...
                 sprintf('doe_%s_%s.manifest.json', char(problema), num2str(semente)));
end


% ════════════════════════════════════════════════════════════════════════════
%  Escrita ATOMICA (D58) — *.tmp -> movefile
% ════════════════════════════════════════════════════════════════════════════

function atomic_parquet(path, T)
    ensure_dir(path);
    tmp = tmp_name(path);
    parquetwrite(tmp, T, 'VariableCompression', 'brotli');  % single/int32, SEM round (D53)
    movefile(tmp, path, 'f');
end

function atomic_write_text(path, txt)
    ensure_dir(path);
    tmp = tmp_name(path);
    fid = fopen(tmp, 'w');  assert(fid > 0, 'nao abriu %s', tmp);
    fwrite(fid, txt, 'char');  fclose(fid);
    movefile(tmp, path, 'f');
end

function tmp = tmp_name(path)
    tmp = sprintf('%s.%d.tmp', path, feature('getpid'));
end

function ensure_dir(path)
    d = fileparts(path);
    if ~isempty(d) && ~isfolder(d), mkdir(d); end
end


% ════════════════════════════════════════════════════════════════════════════
%  Log de auditoria .jsonl (§17.5) — mesma linha {ts, rec, ...} do audit_log.py
% ════════════════════════════════════════════════════════════════════════════

function fid = jsonl_open(path)
    ensure_dir(path);
    fid = fopen(path, 'w');
    assert(fid > 0, 'nao abriu jsonl %s', path);
end

function jsonl_line(fid, rec, kv)
    s = struct('ts', iso_now(), 'rec', string(rec));
    for i = 1:2:numel(kv)
        s.(kv{i}) = kv{i+1};
    end
    fprintf(fid, '%s\n', jsonencode(s));
end


% ════════════════════════════════════════════════════════════════════════════
%  Utilitarios
% ════════════════════════════════════════════════════════════════════════════

function hex = sha256_rowmajor_f64(Mtx)
% SHA256 dos bytes float64 little-endian em ROW-MAJOR (= numpy '<f8'); identico a
% scripts/check_doe_matlab.m e a src/doe.py::decoded_hash. Mtx e column-major no
% MATLAB; Mtx.' lido column-major = Mtx lido row-major.
    bytes_u8 = typecast(reshape(double(Mtx).', 1, []), 'uint8');
    md = java.security.MessageDigest.getInstance('SHA-256');
    md.update(typecast(bytes_u8, 'int8'));
    hb = typecast(md.digest(), 'uint8');
    hex = lower(sprintf('%02x', hb));
end

function s = iso_now()
    s = string(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
end
