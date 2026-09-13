classdef FEBudget < handle
% FEBudget — wrapper de FE: a UNICA fonte do orcamento no stack MATLAB
% (espelho de src/budget.py — D21/D61/D89/D57). NAO usar o obj.FE nativo do
% PlatEMO para governar o termino (D89).
%
% Contrato (identico ao Python, para o pareamento cross-stack):
%   - Conta avaliacoes reais DISTINTAS por X NATIVO bit-a-bit (D89). A chave de
%     identidade e o x no espaco nativo comparado byte-a-byte
%     (`typecast(double(x),'uint8')` = `<f8` little-endian row-major, o mesmo
%     que `np.ascontiguousarray(x,'<f8').tobytes()`).
%   - Cache-hit = 0 FE (D89): reavaliar um X ja avaliado e GRATUITO (devolve a
%     fitness memorizada) e e logado como evento no .jsonl; nao move o saldo,
%     nem sob orcamento esgotado.
%   - solution_id = dedup-por-X (D57): cada X distinto ganha um id inteiro
%     estavel (0-based, na ordem de 1a avaliacao). E a chave de join das 3
%     camadas (§17.1). O cache-hit reusa o id existente.
%   - Hard-stop EXATO em 31D-1 (D21/D61): a 31D-esima X INEDITA levanta
%     MException('PlatEMO:Termination') no ponto unico de avaliacao -> o adapter
%     encerra o run com FE final = 31D-1 cravado (mesmo identificador que o
%     Solve engole no termino normal). Um cache-hit apos o esgotamento continua
%     livre (nao e avaliacao nova).
%
% O catalogo ① (as solucoes reais distintas) e acumulado em DOUBLE (float64) — o
% valor exato avaliado. A ① vai a single/float32 no parquet (D53), mas o
% doe_hash do CP-init (D87/D88) e computado do float64 de init_X() (as 11D-1
% primeiras X, fase 'init' = o DoE), casando bit-a-bit com o sidecar do DoE.

    properties (SetAccess = private)
        D            (1,1) double            % dimensao
        maxfe        (1,1) double            % 31D-1 (D21)
        n_init       (1,1) double            % 11D-1 (§5.2/D87)
        fe           (1,1) double = 0        % saldo consumido (X distintas)
        cache_hits   (1,1) double = 0        % nº de cache-hits (D89, evento)
        % [v5.2.1/§17.6] Cronometro acumulado das avaliacoes REAIS — o
        % `tempo_aval_real_s` do bloco `timing` do manifesto. Mede SO o
        % evalFcn (a funcao verdadeira); cache-hit (D89) nao avalia nada e
        % portanto nao entra. Read-only sobre a decisao: nenhum ramo depende
        % deste valor.
        tempo_aval_real_s (1,1) double = 0
    end

    properties (Access = private)
        keymap                                % containers.Map: hexkey(char) -> sid(double)
        recX  cell = {}                       % {i} = x (1xD double, nativo exato)
        recF  cell = {}                       % {i} = f (1xM double)
        recIdx  double = []                   % fe_index por registro (0-based)
        recFase cell = {}                     % 'init' | 'opt'
        logger = []                           % AuditLogger-like (opcional; struct c/ .guard)
    end

    methods
        function obj = FEBudget(D, maxfe, n_init, logger)
            % FEBudget(D[, maxfe, n_init, logger]) — defaults 31D-1 / 11D-1.
            obj.D = double(D);
            if nargin < 2 || isempty(maxfe),  maxfe  = 31*obj.D - 1; end
            if nargin < 3 || isempty(n_init), n_init = 11*obj.D - 1; end
            if nargin < 4, logger = []; end
            obj.maxfe  = double(maxfe);
            obj.n_init = double(n_init);
            obj.logger = logger;
            obj.keymap = containers.Map('KeyType','char','ValueType','double');
        end

        function f = evaluate(obj, x, evalFcn)
            % evaluate(x, evalFcn) — avalia x sob o orcamento. Cache-hit = 0 FE
            % (D89); X inedita = 1 FE; a 31D-esima X inedita levanta
            % PlatEMO:Termination (hard-stop, D21). evalFcn(x)->(1xM) so e
            % chamado quando x e INEDITO. Devolve f (1xM double).
            x = double(x(:).');                       % linha 1xD, nativo
            if numel(x) ~= obj.D
                error('FEBudget:dim', 'x tem dim %d != D=%d', numel(x), obj.D);
            end
            key = obj.keyOf(x);

            if isKey(obj.keymap, key)
                % Cache-hit: 0 FE (D89). Livre mesmo com o saldo esgotado.
                sid = obj.keymap(key);                % 0-based
                obj.cache_hits = obj.cache_hits + 1;
                obj.logGuard('cache_hit', 'solution_id', sid, ...
                             'x_key', key(1:min(16,numel(key))), 'fe', obj.fe);
                f = obj.recF{sid + 1};
                return;
            end

            % X inedita -> 1 FE. Hard-stop EXATO antes de consumir (D21/D61).
            if obj.fe >= obj.maxfe
                obj.logGuard('hard_stop', 'fe', obj.fe, 'maxfe', obj.maxfe, ...
                             'x_key', key(1:min(16,numel(key))));
                throw(MException('PlatEMO:Termination', ...
                    'orcamento esgotado: %d avaliacoes reais distintas (D21/D61).', ...
                    obj.maxfe));
            end

            t0_aval = tic;                            % [§17.6] so a aval. REAL
            f = double(evalFcn(x));
            obj.tempo_aval_real_s = obj.tempo_aval_real_s + toc(t0_aval);
            f = f(:).';                               % 1xM
            fe_index = obj.fe;                        % 0-based
            sid = fe_index;                           % solution_id = fe_index (D57)
            obj.recX{sid + 1}   = x;
            obj.recF{sid + 1}   = f;
            obj.recIdx(sid + 1) = fe_index;
            obj.recFase{sid + 1} = obj.faseOf(fe_index);
            obj.keymap(key) = sid;
            obj.fe = obj.fe + 1;
        end

        function sid = solutionIdOf(obj, x)
            % solution_id de um X ja avaliado (ou -1) — p/ montar ②③ sem
            % reavaliar (o candidato surrogate que virou infill aponta o id).
            key = obj.keyOf(double(x(:).'));
            if isKey(obj.keymap, key), sid = obj.keymap(key); else, sid = -1; end
        end

        function X = init_X(obj)
            % As 11D-1 primeiras X distintas (fase 'init' = o DoE) em float64, na
            % ordem de avaliacao. Fonte do doe_hash do CP-init (D87/D88).
            mask = strcmp(obj.recFase, 'init');
            idx = find(mask);
            if isempty(idx), X = zeros(0, obj.D); return; end
            X = zeros(numel(idx), obj.D);
            for k = 1:numel(idx)
                X(k,:) = obj.recX{idx(k)};
            end
        end

        function X = arquivoX(obj)
            % [A11/I-6] TODAS as X ja avaliadas de verdade (init + opt), em
            % float64 e na ordem de avaliacao — o "arquivo corrente" que a sonda
            % ESTRATIFICADA usa como centro de amostragem.
            %
            % Por que aqui e nao via `records()`: o `records` monta um struct
            % array de n elementos com x/f/fase por linha, so para o consumidor
            % jogar tudo fora menos o x. Este acessor devolve a matriz direto —
            % o bloco estratificado dispara na cadencia da sonda (a cada k
            % geracoes) e nao pode pagar essa alocacao toda vez.
            %
            % READ-ONLY: nao toca RNG, nao toca orcamento, nao registra nada.
            n = numel(obj.recX);
            if n == 0, X = zeros(0, obj.D); return; end
            X = zeros(n, obj.D);
            for k = 1:n
                X(k,:) = obj.recX{k};
            end
        end

        function R = records(obj)
            % Struct array das linhas do Catalogo REAL ① (ordem = fe_index).
            n = numel(obj.recX);
            R = struct('solution_id', cell(1,n), 'x', [], 'f', [], ...
                       'fe_index', [], 'fase', []);
            for i = 1:n
                R(i).solution_id = i - 1;             % 0-based
                R(i).x = obj.recX{i};
                R(i).f = obj.recF{i};
                R(i).fe_index = obj.recIdx(i);
                R(i).fase = obj.recFase{i};
            end
        end

        function n = numOpt(obj)
            n = sum(strcmp(obj.recFase, 'opt'));
        end
    end

    methods (Access = private)
        function key = keyOf(~, x)
            % Bytes canonicos do X nativo: `<f8` contiguo row-major (D89),
            % em hex (chave char da Map). typecast em arm64/x86 e little-endian,
            % identico ao numpy '<f8'. Uma linha 1xD ja e row-major.
            bytes = typecast(double(x), 'uint8');
            key = reshape(dec2hex(bytes, 2).', 1, []);   % 2*8*D chars hex
        end

        function fase = faseOf(obj, fe_index)
            if fe_index < obj.n_init, fase = 'init'; else, fase = 'opt'; end
        end

        function logGuard(obj, name, varargin)
            if ~isempty(obj.logger) && isfield(obj.logger, 'guard') ...
                    && ~isempty(obj.logger.guard)
                try, obj.logger.guard(name, varargin{:}); catch, end
            end
        end
    end
end
