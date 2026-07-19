classdef RunBuffer < handle
% RunBuffer — coletor da trajetoria de um run: acumula as camadas ② (populacao
% real / membership, D31), ③ (surrogate, schema unico C1/C3) e a serie de tempo
% (§17.6), por geracao. E alimentado pelo `hook_output` (outputFcn do PlatEMO,
% por geracao) e, no run-STUB do R1-00, diretamente pelo adapter. O
% `experiment_run` fecha o run gravando as camadas a partir daqui (§17.3/D31: o
% MESMO ponto de coleta emite ② e ③ -> sincronizacao §17.1.3).
%
% `view` (o que cada geracao entrega):
%   view.g        (1,1)  indice da geracao (>=1)
%   view.pop_ids  (1,K)  solution_ids reais (0-based) na populacao -> ②
%   view.srows    cell   linhas ③ (structs de RunBuffer.mkSurrogateRow)
%   view.timing   struct|[]  {n_acumulado, tempo_fit_s[, tempo_busca_s]} -> §17.6

    properties (SetAccess = private)
        pop    double = zeros(0,2)    % linhas [geracao, solution_id] (②)
        srows  cell   = {}            % linhas ③ (structs)
        trows  cell   = {}            % linhas timing (structs §17.6)
        gen    double = 0             % contador de geracoes (uso do hook)
    end

    methods
        function g = bumpGen(obj)
            % Proximo indice de geracao (1-based) — usado pelo hook_output do
            % PlatEMO, que e chamado uma vez por geracao (§18).
            obj.gen = obj.gen + 1;
            g = obj.gen;
        end

        function addGeneration(obj, view)
            % Anexa uma geracao (chamado pelo hook a cada geracao, inclusive a
            % final). Robusto a campos ausentes (nao quebra um run — D60).
            if ~isfield(view, 'g') || isempty(view.g)
                return;   % sem indice de geracao nada a coletar
            end
            g = double(view.g);

            % ② membership: (geracao, solution_id) por individuo real.
            if isfield(view, 'pop_ids') && ~isempty(view.pop_ids)
                ids = double(view.pop_ids(:));
                obj.pop = [obj.pop; [repmat(g, numel(ids), 1), ids]];
            end

            % ③ surrogate: as linhas ja montadas (mkSurrogateRow).
            if isfield(view, 'srows') && ~isempty(view.srows)
                for k = 1:numel(view.srows)
                    r = view.srows{k};
                    r.geracao = g;                 % carimba a geracao
                    obj.srows{end+1} = r; %#ok<AGROW>
                end
            end

            % §17.6 timing: 1 evento de retreino por geracao (quando ha retreino).
            if isfield(view, 'timing') && ~isempty(view.timing)
                t = view.timing;
                t.geracao = g;
                if ~isfield(t, 'tempo_busca_s'), t.tempo_busca_s = NaN; end
                % [DI-09/§17.6] tempo_pred_sonda_s = 0 quando a sonda NAO rodou
                % nesta geracao (o contrato §4 diz "0 quando nao roda", nao NULL);
                % tempo_geracao_s = NaN quando o config ainda nao o mede.
                if ~isfield(t, 'tempo_pred_sonda_s'), t.tempo_pred_sonda_s = 0; end
                if ~isfield(t, 'tempo_geracao_s'),    t.tempo_geracao_s = NaN; end
                obj.trows{end+1} = t; %#ok<AGROW>
            end
        end

        function n = nGeracoes(obj)
            if isempty(obj.pop), n = numel(obj.trows); return; end
            n = numel(unique(obj.pop(:,1)));
        end
    end

    methods (Static)
        function rows = mkSurrogateRows(X, varargin)
            % Versao em LOTE de mkSurrogateRow, SEM inputParser — ~150x mais
            % rapida (148 us -> ~1 us por linha, medido no R2025a). Existe por
            % causa do volume da SONDA: 2000 linhas por bloco, ate ~295 blocos
            % num run (c217/ZDT1) => o inputParser sozinho custava ~87 s/run.
            % Mesmo precedente do writer O(n)->O(n^2) do DI-02: o custo por
            % linha e o que decide se a bateria M8 e viavel.
            %
            % Campos que VARIAM por linha entram como matriz N x k (mu, sigma)
            % ou coluna N x 1 (pred_score, pred_classe, pred_confianca,
            % fe_treino_max); os CONSTANTES entram como escalar/string e sao
            % replicados. Semantica IDENTICA a mkSurrogateRow (mesmos defaults,
            % mesmos NaN/missing) — a equivalencia e testada no smoke do stub.
            n = size(X, 1);
            a = struct('mu', [], 'sigma', [], 'pred_tipo', string(missing), ...
                       'pred_classe', string(missing), 'pred_score', [], ...
                       'pred_confianca', [], 'modelo_flag', string(missing), ...
                       'espaco_modelo', string(missing), ...
                       'transf_tipo', string(missing), 'transf_params', [], ...
                       'regime', string(missing), 'fe_treino_max', []);
            for i = 1:2:numel(varargin)
                f = varargin{i};
                if ~isfield(a, f)
                    error('RunBuffer:param', 'parametro desconhecido: %s', f);
                end
                a.(f) = varargin{i+1};
            end
            if ~ismissing(string(a.pred_tipo)) && ...
               ~ismember(string(a.pred_tipo), ["valor","classe","score","hibrido"])
                error('RunBuffer:pred_tipo', 'pred_tipo invalido: %s', a.pred_tipo);
            end
            % transf_params: serializado UMA vez (constante por bloco).
            if isempty(a.transf_params)
                tp = string(missing);
            elseif isstring(a.transf_params) || ischar(a.transf_params)
                tp = string(a.transf_params);
            else
                tp = string(jsonencode(a.transf_params));
            end
            proto = struct('geracao', [], 'x', [], 'real_solution_id', [], ...
                'mu', [], 'sigma', [], 'pred_tipo', string(a.pred_tipo), ...
                'pred_classe', string(missing), 'pred_score', [], ...
                'pred_confianca', [], 'modelo_flag', string(a.modelo_flag), ...
                'espaco_modelo', string(a.espaco_modelo), ...
                'transf_tipo', string(a.transf_tipo), 'transf_params', tp, ...
                'regime', string(a.regime), 'fe_treino_max', a.fe_treino_max);
            pick = @(v, i) sel_row(v, i, n);
            rows = cell(1, n);
            for i = 1:n
                r = proto;
                r.x = double(X(i, :));
                r.mu    = pick(a.mu, i);
                r.sigma = pick(a.sigma, i);
                r.pred_score     = pick(a.pred_score, i);
                r.pred_confianca = pick(a.pred_confianca, i);
                if ~ismissing(string(a.pred_classe))
                    if numel(a.pred_classe) == n
                        r.pred_classe = string(a.pred_classe(i));
                    else
                        r.pred_classe = string(a.pred_classe);
                    end
                end
                rows{i} = r;
            end
        end

        function r = mkSurrogateRow(x, varargin)
            % Espelho de src/export.py::surrogate_row — monta uma linha ③ com
            % defaults ausentes ([] = NULL/NaN no export). x = 1xD (nativo).
            % Pares nome-valor: real_solution_id, mu, sigma, pred_tipo,
            % pred_classe, pred_score, pred_confianca, modelo_flag,
            % espaco_modelo, transf_tipo, transf_params (struct/num -> JSON).
            p = inputParser; p.KeepUnmatched = false;
            % strings ausentes => <missing> (=> NULL no parquet), como o None do
            % Python (src/export.py::surrogate_row); numericos ausentes => [] (NaN).
            p.addParameter('real_solution_id', []);
            p.addParameter('mu', []);
            p.addParameter('sigma', []);
            p.addParameter('pred_tipo', string(missing));
            p.addParameter('pred_classe', string(missing));
            p.addParameter('pred_score', []);
            p.addParameter('pred_confianca', []);
            p.addParameter('modelo_flag', string(missing));
            p.addParameter('espaco_modelo', string(missing));
            p.addParameter('transf_tipo', string(missing));
            p.addParameter('transf_params', []);
            % [DI-09] regime POR LINHA ('sonda' x o regime da busca) e o
            % marcador in-sample/out-of-sample. Ausentes => o write_surrogate
            % aplica o default do arquivo (regime) / NULL (fe_treino_max).
            p.addParameter('regime', string(missing));
            p.addParameter('fe_treino_max', []);
            p.parse(varargin{:});
            a = p.Results;

            PRED_TIPOS = ["valor","classe","score","hibrido"];
            if ~ismissing(string(a.pred_tipo)) && ~ismember(string(a.pred_tipo), PRED_TIPOS)
                error('RunBuffer:pred_tipo', 'pred_tipo invalido: %s', a.pred_tipo);
            end

            r = struct();
            r.geracao = [];                          % carimbado no addGeneration
            r.x = double(x(:).');
            r.real_solution_id = a.real_solution_id;
            r.mu = as_row(a.mu);
            r.sigma = as_row(a.sigma);
            r.pred_tipo = string(a.pred_tipo);
            r.pred_classe = string(a.pred_classe);
            r.pred_score = a.pred_score;
            r.pred_confianca = a.pred_confianca;
            r.modelo_flag = string(a.modelo_flag);
            r.espaco_modelo = string(a.espaco_modelo);
            r.transf_tipo = string(a.transf_tipo);
            r.regime = string(a.regime);              % [DI-09]
            r.fe_treino_max = a.fe_treino_max;        % [DI-09/A1]
            if isempty(a.transf_params)
                r.transf_params = string(missing);
            elseif isstring(a.transf_params) || ischar(a.transf_params)
                r.transf_params = string(a.transf_params);
            else
                r.transf_params = string(jsonencode(a.transf_params));
            end
        end
    end
end

function v = as_row(v)
    if isempty(v), v = []; else, v = double(v(:).'); end
end

function v = sel_row(V, i, n)
% Linha i de um campo do lote: matriz N x k -> linha i; escalar/vetor unico ->
% replicado; vazio -> vazio (=> NULL no export).
    if isempty(V)
        v = [];
    elseif size(V, 1) == n && n > 1
        v = double(V(i, :));
    elseif isscalar(V)
        v = double(V);
    else
        v = double(V(:).');
    end
end
