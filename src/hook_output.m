function hook_output(Algorithm, Problem, buf, bud, timing)
% hook_output — hook `outputFcn(Algorithm, Problem)` do PlatEMO, chamado a CADA
% geracao (inclusive a final). Emite as camadas ② (populacao real) e ③
% (surrogate) sincronizadas + a serie de tempo §17.6, SEM editar os algoritmos
% (§17.3/D31: o MESMO hook emite ② e ③ nos MESMOS pontos -> sincronizacao §17.1.3).
%
% >>> R1-00-harness: CORPO REAL transversal, pronto para o c217 (o 1o algoritmo).
% >>> O c217+ o fia via  `algo = <ALGO>('save',-K,'outputFcn',@(A,P) hook_output(A,P,buf,bud,timing))`.
% >>> No run-STUB do R1-00 (sem Algorithm.Solve) a coleta e feita direto pelo
% >>> `RunBuffer.addGeneration` no adapter — o MESMO coletor que este hook usa —,
% >>> entao a mecanica de buffering/schema ② ③/timing e exercitada em R1-00; a
% >>> EXTRACAO a partir de Algorithm/Problem abaixo roda pela 1a vez sob um Solve
% >>> real no c217 (HANDOFF §8: c217 = caso-modelo ponta-a-ponta).
%
% Args:
%   Algorithm  objeto PlatEMO (< ALGORITHM); `Algorithm.result{end,2}` = SOLUTION
%              array da geracao corrente (snapshots equiespacados em FE).
%   Problem    objeto PlatEMO (UserProblem); `Problem.FE`/`Problem.maxFE` p/ a
%              deteccao da geracao final (§18) — mas o orcamento e do WRAPPER (D89).
%   buf        RunBuffer (coletor ② ③/timing do run).
%   bud        FEBudget (mapeia X real -> solution_id por dedup bit-a-bit, D57).
%   timing     (opcional) struct {n_acumulado, tempo_fit_s[, tempo_busca_s]} do
%              retreino desta geracao (o adapter mede §17.6); [] se sem retreino.
%
% Notas da mecanica (§18 v2.2):
%   - O runtime deste hook NAO conta no metric.runtime.
%   - A camada ① (avaliacoes reais) sai do WRAPPER de FE (ponto unico), nao daqui.
%   - `SOLUTION.add` e um campo publico por individuo p/ anexar mu/sigma (③).

    if nargin < 5, timing = []; end
    view = struct('g', buf.bumpGen());

    % ── ② membership: os solution_ids reais da populacao corrente ──────────────
    ids = [];
    try
        pop = Algorithm.result{end, 2};           % SOLUTION array da geracao
        Decs = pop.decs;                          % N x D (espaco nativo)
        for i = 1:size(Decs, 1)
            sid = bud.solutionIdOf(Decs(i, :));   % dedup por X bit-a-bit (D57)
            if sid >= 0, ids(end+1) = sid; end %#ok<AGROW>
        end
    catch
        % geracao sem snapshot legivel -> ② vazia nesta geracao (nao quebra o run).
    end
    view.pop_ids = ids;

    % ── ③ surrogate: mu/sigma anexados aos individuos (SOLUTION.add), se houver ─
    % A instrumentacao POR ALGORITMO (quais candidatos, mu/sigma vs classe/score,
    % espaco transformado C3) e ligada em cada cartao R1-<alg>; aqui fica o gancho
    % generico: se o algoritmo anexou `.add` numerico, emite linhas ③ de regressor.
    srows = {};
    try
        pop = Algorithm.result{end, 2};
        Decs = pop.decs;
        Adds = pop.adds;                          % N x (?) mu/sigma anexados
        if ~isempty(Adds)
            M = Problem.M;
            for i = 1:size(Decs, 1)
                sid = bud.solutionIdOf(Decs(i, :));
                add = Adds(i, :);
                mu = add(1:min(M, numel(add)));
                sg = []; if numel(add) >= 2*M, sg = add(M+1:2*M); end
                rsi = int32([]); if sid >= 0, rsi = int32(sid); end
                srows{end+1} = RunBuffer.mkSurrogateRow(Decs(i, :), ...
                    'real_solution_id', rsi, 'mu', mu, 'sigma', sg, ...
                    'pred_tipo', "valor"); %#ok<AGROW>
            end
        end
    catch
        % sem `.add` (b4/c217 sao classificadores; ③ semantico entra no cartao).
    end
    view.srows = srows;

    % ── §17.6 timing (o adapter mede o retreino desta geracao) ─────────────────
    if ~isempty(timing)
        view.timing = timing;
    end

    buf.addGeneration(view);
end
