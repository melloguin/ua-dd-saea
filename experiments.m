function experiments(varargin)
% experiments.m — despachante MATLAB do harness (raiz) — arquitetura A2 (§16.5/§19).
%
% Recebe {algoritmos} x {problemas} x {sementes} e roda uma task por
% (algoritmo, problema, semente) chamando o adapter src/experiment.m
% (experiment_run). Paraleliza com `parfor` (1 processo por run — A12);
% esteira idempotente/resumivel (manifesto run_id -> status; D58/§19): celulas
% prontas sao puladas.
%
% >>> R1-00-harness: CORPO REAL do despachante transversal. A infra de avaliacao
% >>> (ponte, FEBudget, DoE, export, CP-init) vive em src/experiment.m; aqui fica
% >>> o andaime de despacho: assert de toolboxes, addpath(genpath(PlatEMO)) por
% >>> worker (N.0.1), grid, skip idempotente, placar. O run-STUB (alg='stub')
% >>> roda ponta-a-ponta (sem PlatEMO); os 16 algoritmos reais sao os cartoes
% >>> R1-c217+ (o adapter PlatEMO ainda nao esta ligado — falha honesta, D23).
%
% Uso:
%   experiments('algorithms', {'stub'}, 'problems', {'MMF1'}, 'seeds', 0, ...
%               'exp', 'main', 'parallel', false)
%   experiments('algorithms', {})     % so monta o grid (andaime)
%
% ARMADILHAS DA RECEITA (N.0/§18/D59 — os cartoes R1-<alg> NAO podem violar):
%   - Bypass do platemo(): platemo.m roda rng('shuffle') e destruiria a semente
%     -> chamar Algorithm.Solve(Problem) DIRETO.
%   - rng(seed,'twister') DEPOIS de construir o Problem, ANTES de Solve (D59).
%   - Construtor do Algorithm: fixar SEMPRE 'save'=-K + 'outputFcn'=@hook_output;
%     NUNCA 'save'>0 (colisao UserProblem + corrida TOCTOU). maxRuntime=inf.
%   - Hard-stop = contador do WRAPPER de FE (FEBudget) no evalFcn (D89); o obj.FE
%     nativo do PlatEMO NAO governa. Termino normal = MException('PlatEMO:Termination').
%   - 1 processo por run (A12). e103/e74 em WORKER DEDICADO (path so com a propria
%     arvore; rmpath da 4.15; smoke `which -all` logado — D95/N.3).
%   - parquetwrite 'VariableCompression','brotli' + single, SEM round (S.6/D53).

% ── Parse de argumentos ────────────────────────────────────────────────────
p = inputParser;
% [DI-31] roster default completo: 9 SAEA + 4 pisos ONLINE. Os pisos ficavam de
% fora → a bateria M8 os pulava em silêncio. e103 é OFFLINE (--exp off).
p.addParameter('algorithms', {'b1','b3','b4','e7','c217','c141','e74','c238', ...
                              'nsga2','nsga3','moead','smsemoa','e103'});
p.addParameter('problems', default_problems());
p.addParameter('seeds', [0:28, 42]);          % 30 sementes (§5.3/D85)
p.addParameter('exp', 'main');                % main|off|batch|sweep-<tier>-<dist>
p.addParameter('dataRoot', 'data');
p.addParameter('force', false);
p.addParameter('parallel', true);             % false -> laco serial (p/ smoke)
p.parse(varargin{:});
a = p.Results;

% ── Assert de toolboxes (S.6) ───────────────────────────────────────────────
assert(~isempty(ver('nnet')) && ~isempty(ver('stats')) && ...
       ~isempty(ver('optim')) && ~isempty(ver('parallel')), ...
       'Toolboxes ausentes (Deep Learning/Statistics/Optimization/Parallel — S.6).');

% ── PlatEMO root (addpath por worker, N.0.1) ────────────────────────────────
platemoRoot = platemo_root();
needsPlatEMO = any(~strcmp(a.algorithms, 'stub'));
if needsPlatEMO && isempty(platemoRoot)
    warning('experiments:platemo', ...
        'PlatEMO nao encontrado em algorithms/_PlatEMO — algoritmos reais falharao.');
end

% ── Montagem do grid ────────────────────────────────────────────────────────
algs = a.algorithms; probs = a.problems; seeds = a.seeds;
[A, Pr, S] = ndgrid(1:numel(algs), 1:numel(probs), 1:numel(seeds));
cells = [A(:), Pr(:), S(:)];
nTasks = size(cells, 1);
fprintf('\n[grid] exp=%s | algs=%d x problemas=%d x sementes=%d = %d celulas\n', ...
        a.exp, numel(algs), numel(probs), numel(seeds), nTasks);
if isempty(algs) || nTasks == 0
    fprintf('[grid] roster vazio — so andaime; nenhum run executado.\n');
    return;
end

% ── Laco (RECEITA N.4) ───────────────────────────────────────────────────────
status = strings(nTasks, 1);
exp = a.exp; dataRoot = a.dataRoot; force = a.force;
if a.parallel
    parfor t = 1:nTasks
        status(t) = run_cell(cells(t,:), algs, probs, seeds, exp, dataRoot, ...
                             force, platemoRoot); %#ok<PFBNS>
    end
else
    for t = 1:nTasks
        status(t) = run_cell(cells(t,:), algs, probs, seeds, exp, dataRoot, ...
                             force, platemoRoot);
    end
end

% ── Placar (D23/§17.5) ──────────────────────────────────────────────────────
nOk   = sum(status == "ok" | status == "retried_ok");
nFail = sum(status == "failed");
nSkip = sum(status == "skipped");
fprintf('\n%s\n[placar] ok=%d failed=%d skipped=%d | concluidos=%d\n%s\n', ...
        repmat('=',1,66), nOk, nFail, nSkip, nTasks, repmat('=',1,66));
end


function st = run_cell(cell3, algs, probs, seeds, exp, dataRoot, force, platemoRoot)
% Uma celula do grid: skip idempotente -> adapter -> status (nunca silencioso).
    alg  = algs{cell3(1)};
    prob = probs{cell3(2)};
    seed = seeds(cell3(3));
    % Esteira idempotente (D58): pula celula pronta.
    if ~force && is_run_done_m(exp, alg, prob, seed, dataRoot)
        st = "skipped";
        return;
    end
    % addpath(genpath(PlatEMO)) uma vez por worker (N.0.1) p/ algoritmos reais.
    if ~strcmp(alg, 'stub') && ~isempty(platemoRoot)
        ensure_platemo_path(platemoRoot);
    end
    try
        st = experiment(alg, prob, seed, exp, dataRoot);
    catch e
        st = "failed";
        fprintf(2, '[run FAILED] %s/%s/%d: %s\n', alg, prob, seed, e.message);
    end
end


function tf = is_run_done_m(exp, alg, prob, seed, dataRoot)
% Espelho de src/manifest.py::is_run_done (D58): manifesto status in {ok,
% retried_ok} E as 4 camadas presentes. (Footer de parquet: skip — parquetinfo
% valida na consolidacao.)
    a = strrep(strrep(char(alg), '/', '_'), ' ', '_');
    base = sprintf('exp_%s_%s_%s_%s', char(exp), a, char(prob), num2str(seed));
    rundir = fullfile(char(dataRoot), 'experiments', char(exp), a);
    manp = fullfile(rundir, [base '.manifest.json']);
    tf = false;
    if ~isfile(manp), return; end
    try
        man = jsondecode(fileread(manp));
    catch
        return;
    end
    if ~isfield(man, 'status') || ~ismember(string(man.status), ["ok","retried_ok"])
        return;
    end
    for ly = ["real","pop","surrogate","timing"]
        if ~isfile(fullfile(rundir, sprintf('%s__%s.parquet', base, ly)))
            return;
        end
    end
    tf = true;
end


function ensure_platemo_path(platemoRoot)
% addpath(genpath) uma unica vez por processo/worker (N.0.1).
    persistent added
    if isempty(added), added = false; end
    if ~added
        addpath(genpath(platemoRoot));
        added = true;
    end
end


function root = platemo_root()
% Localiza a arvore PlatEMO 4.15 (algorithms/_PlatEMO/PlatEMO). [] se ausente.
    here = fileparts(mfilename('fullpath'));
    cand = fullfile(here, 'algorithms', '_PlatEMO', 'PlatEMO');
    if isfolder(cand), root = cand; else, root = ''; end
end


function probs = default_problems()
% Os 25 problemas canonicos (A2/§4; MMF16_L3 removido) — espelha
% src/experiment.py::PROBLEM_CLASSES (BBOB canonico = BBOB_F1..BBOB_F55).
probs = {'MMF1','MMF4','MMF11_L','MMF16_20', ...
         'ZDT1','ZDT3','ZDT4','ZDT6', ...
         'DTLZ1','DTLZ2','DTLZ3','DTLZ4','DTLZ7', ...
         'WFG1','WFG2','WFG4','WFG5','WFG9', ...
         'BBOB_F1','BBOB_F5','BBOB_F17','BBOB_F22','BBOB_F37','BBOB_F49','BBOB_F55'};
end
