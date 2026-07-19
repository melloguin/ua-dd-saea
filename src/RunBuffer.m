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
