function status = experiment_run(alg, problema_id, semente, exp, dataRoot)
% experiment_run — adapter MATLAB: traduz run(alg, problema_id, semente) numa
% chamada a main OFICIAL do PlatEMO/standalone (arquitetura A2, §16.5.3).
%
% >>> ESQUELETO (F0-01-harness). O CORPO REAL (ponte pyenv, UserProblem com o
% >>> DoE injetado, export das 3 camadas, escrita do manifesto/jsonl) e o
% >>> cartao R1-00-harness. Aqui fica o contrato + a RECEITA N.4, e um retorno
% >>> `failed` honesto enquanto o despacho por algoritmo nao existe (D23).
%
% Retorna status ∈ {"ok","retried_ok","failed"}.
%
% Contrato do adapter (preenchido em R1 — §16.5.3):
%   1. Problema de src/problems.py pelo problema_id via ponte (A2/§2) — o MATLAB
%      NUNCA usa problema nativo; avalia f(x) chamando py.problems.evaluate_problem.
%   2. Bounds/sinal (§5.5): PlatEMO/EA operam em bounds NATIVOS e MINIMIZAM ->
%      identidade nos bounds, devolve f. (CP-bounds/CP-sinal.)
%   3. DoE 11D-1 carregado do artefato parquet (D87): parquetread do
%      data/doe/<prob>/doe_<prob>_<sem>.parquet -> injecao via `initFcn`
%      (A1: os SAEAs nao usam Problem.Initialization). NUNCA regenerar.
%   4. Orcamento maxFE = 31D-1 com HARD-STOP EXATO no wrapper de FE do evalFcn
%      (D21/D89): quando o saldo zera, avaliar os primeiros `saldo` do lote,
%      gravar na ①, e lancar MException('PlatEMO:Termination'). O obj.FE nativo
%      NAO governa (D89). Cache-hit bit-a-bit no X nativo = 0 FE (evento no jsonl).
%   5. Semear (D59): rng(semente,'twister') DEPOIS de construir o Problem e
%      ANTES de Algorithm.Solve. (e103/e74: worker dedicado, D95.)
%   6. Coletar a trajetoria pelo hook_output (②③+timing por geracao) e gravar o
%      export §17 (parquetwrite brotli+single, SEM round — S.6) + manifesto/jsonl.

status = "failed";

% ── Andaime da Fase 0: adapter por algoritmo ainda nao ligado ───────────────
% (Em R1, substituir por: montar UserProblem, semear, Solve, exportar.)
knownMatlab = {'b1','b3','b4','e7','c217','c141','e74','c238','e103', ...
               'nsga2','nsga3','moead','smsemoa','moead_media'};
if ~any(strcmp(alg, knownMatlab))
    warning('experiment:unknownAlg', ...
            'Algoritmo MATLAB desconhecido: %s', alg);
end
% NotImplemented (Fase 0). Registrar como `failed` e retornar — nunca silencioso.
fprintf(2, ['[TODO R1] adapter de %s nao implementado (Fase 0 = andaime). ' ...
            'problema=%s semente=%d exp=%s dataRoot=%s\n'], ...
        alg, problema_id, semente, exp, dataRoot);

% ── ESBOCO da receita N.4 (comentado — R1 liga o corpo) ─────────────────────
%   D = problem_dim(problema_id);
%   maxFE = 31*D - 1;                                  % §5.1 (D21)
%   X0 = parquetread(doe_path(problema_id, semente));  % DoE artefato (D87)
%   prob = UserProblem('D', D, 'maxFE', maxFE, 'maxRuntime', inf, ...
%                      'lower', xl, 'upper', xu, ...
%                      'initFcn', @() table2array(X0), ...        % injeta DoE (A1)
%                      'evalFcn', @(x) fe_wrapper(x, ...), ...     % ponte + hard-stop
%                      'once', false);                            % decidir/fixar
%   rng(semente, 'twister');                           % D59 (depois do Problem)
%   algo = feval(alg_ctor(alg), 'save', -K, 'outputFcn', @(A,P) hook_output(A,P,...));
%   try, algo.Solve(prob); catch e; log_and_rethrow(e); end
%   result = algo.result;                              % snapshots {FE, Population}
%   export_three_layers(result, ...);                  % ①②③ (F0-03)
%   write_manifest(...); status = "ok";
end
