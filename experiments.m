function experiments(varargin)
% experiments.m — despachante MATLAB do harness (raiz) — arquitetura A2 (§16.5/§19).
%
% Recebe {algoritmos} x {problemas} x {sementes} e roda uma task por
% (algoritmo, problema, semente) chamando a *main OFICIAL* do PlatEMO/standalone
% via o adapter src/experiment.m (nada e reimplementado — §2/§20). Paraleliza
% com `parfor` (uma VM grande x vCPUs — §21); esteira idempotente/resumivel
% (manifesto run_id -> status; D58/§19): celulas prontas sao puladas.
%
% >>> ESQUELETO (cartao F0-01-harness). O CORPO REAL do stack MATLAB (ponte
% >>> pyenv, UserProblem, export das 3 camadas, escrita do manifesto) e o
% >>> cartao R1-00-harness. Aqui fica o andaime: assert de toolboxes, montagem
% >>> do grid, laco parfor com a RECEITA N.4 e o placar. Chamar um algoritmo
% >>> agora resulta em status `failed` (adapter nao ligado) — honesto, D23.
%
% Uso:
%   experiments('algorithms', {'c217'}, 'problems', {'MMF1','ZDT1'}, ...
%               'seeds', [0 1 42], 'exp', 'main')
%   experiments('algorithms', {})   % so monta o grid (andaime)
%
% ARMADILHAS DA RECEITA (N.0/§18 v2.2/D59 — R1 NAO pode violar):
%   - Bypass do platemo(): platemo.m:79 roda rng('shuffle') e destruiria a
%     semente -> chamar Algorithm.Solve(Problem) DIRETO.
%   - rng(seed,'twister') DEPOIS de construir o Problem, ANTES de Solve (D59;
%     o probe do construtor nao toca cache/catalogo/FE — hooks ligam no Solve).
%   - Construtor do Algorithm: fixar SEMPRE 'save' (=-K, K snapshots em memoria,
%     sem .mat, sem figura) e 'outputFcn' (=@hook_output). NUNCA 'save'>0
%     (colisao de nome UserProblem + corrida TOCTOU do auto-incremento).
%   - maxRuntime = inf SEMPRE (senao reescala maxFE).
%   - Hard-stop = contador do WRAPPER de FE no evalFcn (D89); o obj.FE nativo
%     do PlatEMO NAO governa o termino. Termino normal = MException(
%     'PlatEMO:Termination') (mesmo id que o Solve engole).
%   - 1 processo por run (A12). e103 e e74 em WORKER DEDICADO (path so com a
%     propria arvore; rmpath do 4.15; smoke `which -all` logado — D95/N.3).
%   - parquetwrite com 'VariableCompression','brotli' + `single`, SEM round
%     (S.6/D53; a consolidacao Python re-encoda p/ zstd).

% ── Parse de argumentos ────────────────────────────────────────────────────
p = inputParser;
p.addParameter('algorithms', {'b1','b3','b4','e7','c217','c141','e74','c238','e103'});
p.addParameter('problems', default_problems());
p.addParameter('seeds', [0:28, 42]);          % 30 sementes (§5.3/D85)
p.addParameter('exp', 'main');                % main|off|batch|sweep-<tier>-<dist>
p.addParameter('dataRoot', 'data');
p.addParameter('force', false);
p.parse(varargin{:});
a = p.Results;

% ── Assert de toolboxes (S.6) ───────────────────────────────────────────────
assert(~isempty(ver('nnet')) && ~isempty(ver('stats')) && ...
       ~isempty(ver('optim')) && ~isempty(ver('parallel')), ...
       'Toolboxes ausentes (Deep Learning/Statistics/Optimization/Parallel — S.6).');

% ── Montagem do grid ────────────────────────────────────────────────────────
algs = a.algorithms; probs = a.problems; seeds = a.seeds;
[A, Pr, S] = ndgrid(1:numel(algs), 1:numel(probs), 1:numel(seeds));
cells = [A(:), Pr(:), S(:)];
nTasks = size(cells, 1);
fprintf('\n[grid] exp=%s | algs=%d x problemas=%d x sementes=%d = %d celulas\n', ...
        a.exp, numel(algs), numel(probs), numel(seeds), nTasks);
if isempty(algs)
    fprintf('[grid] roster vazio — so andaime; nenhum run executado.\n');
    return;
end

% ── Laco parfor (RECEITA N.4) ───────────────────────────────────────────────
status = strings(nTasks, 1);
parfor t = 1:nTasks
    alg  = algs{cells(t,1)};
    prob = probs{cells(t,2)};
    seed = seeds(cells(t,3));
    % Esteira idempotente (D58): pula celula pronta. (Leitura do manifesto em
    % MATLAB via jsondecode — corpo em R1; aqui sempre tenta.)
    try
        status(t) = experiment_run(alg, prob, seed, a.exp, a.dataRoot); %#ok<PFBNS>
    catch e
        status(t) = "failed";
        fprintf(2, '[run FAILED] %s/%s/%d: %s\n', alg, prob, seed, e.message);
    end
end

% ── Placar (D23/§17.5) ──────────────────────────────────────────────────────
nOk   = sum(status == "ok" | status == "retried_ok");
nFail = sum(status == "failed");
fprintf('\n%s\n[placar] ok=%d failed=%d | concluidos=%d\n%s\n', ...
        repmat('=',1,66), nOk, nFail, nTasks, repmat('=',1,66));
end


function probs = default_problems()
% Os 25 problemas canonicos (A2/§4; MMF16_L3 removido). Espelha o catalogo do
% src/experiment.py::PROBLEM_CLASSES (a fonte unica das classes e o problems.py).
probs = {'MMF1','MMF4','MMF11_L','MMF16_20', ...
         'ZDT1','ZDT3','ZDT4','ZDT6', ...
         'DTLZ1','DTLZ2','DTLZ3','DTLZ4','DTLZ7', ...
         'WFG1','WFG2','WFG4','WFG5','WFG9', ...
         'BBOB1','BBOB5','BBOB17','BBOB22','BBOB37','BBOB49','BBOB55'};
end
