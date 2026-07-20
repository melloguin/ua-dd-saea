classdef SondaState < handle
% SondaState — o motor da SONDA CANONICA (DI-09 / SPEC §17.2.2), transversal
% aos configs com surrogate. Carrega o artefato UMA vez por run e dispara os
% blocos de predicao na regua fixa, SEM tocar em nada da busca.
%
% O CONTRATO (o que esta classe garante, para os 9 configs de uma vez):
%   I1  RNG intocado — `rng()` salvo e restaurado por onCleanup em volta de
%       TODA predicao (o MC-dropout do e7 consome ~1,4e7 draws por bloco; sem
%       isto a trajetoria da busca muda e o retrofit REPROVA).
%   I2  ZERO FE — nunca chama bud.evaluate/solutionIdOf. A sonda e avaliacao
%       analitica fora do orcamento (excecao contabil, precedente __final DI-08).
%   I3  ORDEM do artefato preservada — 1 disparo = EXATAMENTE S=2000 linhas
%       contiguas, na ordem do parquet. O join com o gabarito e POR POSICAO
%       (§3.1) — qualquer sort/unique/filtro aqui corromperia o dado.
%   I4  regime='sonda' + real_solution_id=NULL + fe_treino_max carimbados pela
%       CLASSE (nao pelo config) — o invariante nao depende de disciplina local.
%   I5  A sonda NUNCA derruba a busca — try/catch com evento de guarda, e o
%       catch re-lanca PlatEMO:Termination (o hard-stop D21 tem de subir).
%   I6  Cronometro proprio, fora dos tic/toc de fit e de busca (§17.6).
%
% CADENCIA (§17.2.2): ONLINE = a cada k=2 geracoes, SEMPRE a 1a e a ULTIMA.
% A ultima e garantida pelo par arm()/finalProbe(): como o orcamento estoura no
% MEIO do ciclo (o FEBudget lanca PlatEMO:Termination e o laco morre antes do
% bloco rodar), o config ARMA o ultimo modelo treinado e o runner dispara
% `finalProbe` DEPOIS do Algorithm.Solve, fora do laco. [decisao do autor,
% 2026-07-19 — a alternativa "aceitar a ultima amostrada" perderia o ponto
% final da curva, que e o modelo mais treinado e o eixo de comparacao do DI-09.]
%
% USO (por config):
%   snd = SondaState(sd, buf, fid, alg);               % sd = load_sonda(...)
%   ^^ ATENCAO: a assinatura NAO leva `bud` (invariante I2 — a classe nao pode
%      receber o FEBudget, senao teria como gastar orcamento). Ate 2026-07-19
%      este cabecalho documentava `SondaState(sd, buf, bud, fid, alg)`, o que
%      levava quem copiasse daqui a passar o FEBudget na posicao do `fid` — e o
%      .jsonl morria em SILENCIO (`fid > 2` e falso para um objeto). Corrigido.
%   ...apos CADA fit, antes de qualquer decisao:
%   snd.probe(g, @(X) minhas_linhas(X), ftm, 'modelo', "GP-DACE");
%   ...ao montar a linha de timing da geracao:
%   timing.tempo_pred_sonda_s = snd.takePendingTime();
%   ...apos o Algorithm.Solve, no run_*:
%   snd.finalProbe();                                  % ver DI-15.5 abaixo
%
% REGIME OFFLINE (DI-13.5): o artefato tem S=20.000 e o offline le TODAS (1x por
% modelo treinado, fora do laco). Nesses blocos `geracao` = NULL. O disparo e por
% `probeOffline(fn, ftm, ...)` — nao por `probe`, que exige g>=1 e nunca casaria
% a cadencia com um g inexistente.

    properties (SetAccess = private)
        X                        % S x D float64, bounds NATIVOS, ordem do artefato
        F                        % S x M gabarito (NAO vai para a ③ — join por posicao)
        S      (1,1) double      % 2000
        D      (1,1) double
        M      (1,1) double
        x_hash char
        f_hash char
        path   char
        k      (1,1) double = 2  % cadencia (§17.2.2)

        regime char = 'online'   % [DI-13.5] 'online' (S=2000) | 'offline' (S=20000)

        n_blocos      (1,1) double = 0    % disparos concluidos
        n_linhas      (1,1) double = 0    % linhas ③ emitidas com regime='sonda'
        n_falhas      (1,1) double = 0
        tempo_total_s (1,1) double = 0
        gens_sondadas double = []         % geracoes ja sondadas (p/ o manifesto)
        g_armado double = []              % [DI-15.5] a geracao do modelo ARMADO
    end

    properties (Access = private)
        buf                      % RunBuffer (o MESMO coletor da busca)
        fid    = []              % fid do .jsonl
        alg    char = ''
        tempo_pendente (1,1) double = 0   % tempo desde o ultimo takePendingTime
        armado = []              % struct{fn, ftm, meta} do ULTIMO fit visto
    end

    methods
        function obj = SondaState(sd, buf, fid, alg, k)
        % sd = struct do load_sonda (ja com o x_hash CONFERIDO no arranque).
            obj.X = sd.X;  obj.F = sd.F;
            obj.S = size(sd.X, 1);
            obj.D = size(sd.X, 2);
            obj.M = size(sd.F, 2);
            obj.x_hash = sd.x_hash;  obj.f_hash = sd.f_hash;
            obj.path = sd.path;
            obj.buf = buf;
            if nargin >= 3, obj.fid = fid; end
            if nargin >= 4, obj.alg = char(alg); end
            if nargin >= 5 && ~isempty(k), obj.k = double(k); end
            % [DI-13.5] O S esperado depende do REGIME: o artefato tem 20.000 e a
            % sequencia de Sobol e ANINHADA, entao o ONLINE le a fatia [1:2000]
            % (load_sonda ja fatia) e o OFFLINE le as 20.000. O assert continua
            % existindo — mas contra o S DO REGIME, nao contra o literal 2000.
            if isfield(sd, 'regime') && ~isempty(sd.regime)
                obj.regime = char(sd.regime);
            end
            if strcmpi(obj.regime, 'offline')
                assert(obj.S == 20000, ...
                    'sonda offline: S=%d != 20000 (§17.2.2/DI-13.5)', obj.S);
            else
                assert(obj.S == 2000, ...
                    'sonda online: S=%d != 2000 (§17.2.2)', obj.S);
            end
        end

        function tf = due(obj, g)
        % Cadencia §17.2.2: "a cada k=2 geracoes + SEMPRE a 1a e a ultima"
        %   => g = 1, 2, 4, 6, 8, ...
        % [decisao do autor, 2026-07-19] Esta formula e a MESMA do lado Python
        % (`sonda_due`, retrofit-R2), depois que a divergencia entre os stacks
        % foi escalada (D81, commit 652e24d): sob a leitura alternativa
        % (1,3,5,...) a clausula "+SEMPRE a 1a" do §17.2.2 ficaria VAZIA — o
        % texto te-la escrito indica que a cadencia sozinha nao inclui a 1a.
        % A sonda e a regua UNICA, identica para todos os configs: uma cadencia
        % que mudasse por STACK contradiria a propria definicao.
        % A ULTIMA nao e decidida aqui — vem do finalProbe (ver cabecalho).
            g = double(g);
            tf = (g >= 1) && (g == 1 || mod(g, obj.k) == 0);
        end

        function arm(obj, g, fn, ftm, varargin)
        % Registra o ULTIMO modelo treinado SEM predizer nada (custo ~zero),
        % JUNTO COM A GERACAO A QUE ELE PERTENCE. E o que permite ao finalProbe
        % medir o modelo final depois que o hard-stop matou o laco.
            obj.armado  = struct('fn', fn, 'ftm', ftm, 'meta', {varargin});
            obj.g_armado = double(g);
        end

        function probe(obj, g, fn, ftm, varargin)
        % Arma SEMPRE + dispara se a geracao estiver na cadencia.
            obj.arm(g, fn, ftm, varargin{:});
            if obj.due(g)
                obj.fire(g, fn, ftm, 'cadencia', varargin{:});
            end
        end

        function probeOffline(obj, fn, ftm, varargin)
        % [DI-13.5] O disparo do regime OFFLINE: UM bloco por MODELO TREINADO,
        % fora do laco, com `geracao` = NULL (NaN e o portador ate o writer).
        % NAO arma: no offline nao existe hard-stop no meio do ciclo capaz de
        % matar o bloco (o orcamento e o dataset e ja foi esgotado antes da
        % busca), logo nao ha "ultima geracao" a recuperar. Deixar `armado`
        % vazio torna um finalProbe defensivo um no-op garantido.
            obj.fire(NaN, fn, ftm, 'offline', varargin{:});
        end

        function finalProbe(obj, ~)
        % [DECISAO DO AUTOR] A sonda da ULTIMA geracao, disparada pelo run_*
        % DEPOIS do Algorithm.Solve — fora do laco, ja com a excecao de termino
        % engolida. Nao repete se a geracao ja foi sondada pela cadencia.
        %
        % [DI-15.5, autor 2026-07-19] A geracao usada e a do modelo ARMADO
        % (`g_armado`), NAO o `buf.gen` corrente. Motivo: em configs de overshoot
        % ZERO (c238), a PlatEMO:Termination sai do TOPO do ciclo seguinte
        % (ALGORITHM.m:128) DEPOIS de o outputFcn ja ter bumpado a geracao — o
        % `buf.gen` pos-Solve aponta uma geracao que NUNCA foi armada, e o bloco
        % final sairia carimbado com a geracao errada. O argumento posicional
        % legado e aceito e IGNORADO para nao quebrar os call-sites existentes.
            if isempty(obj.armado) || isempty(obj.g_armado), return; end
            g = obj.g_armado;
            if isnan(g) || g < 1, return; end            % run sem geracao alguma
            if any(obj.gens_sondadas == g), return; end
            a = obj.armado;
            obj.fire(g, a.fn, a.ftm, 'final', a.meta{:});
        end

        function t = takePendingTime(obj)
        % Tempo de sonda acumulado desde a ultima chamada -> vai para o
        % `tempo_pred_sonda_s` da linha ④ daquela geracao (0 se nao rodou).
            t = obj.tempo_pendente;
            obj.tempo_pendente = 0;
        end

        function blk = manifestBlock(obj)
        % A certidao da regua usada no run (vai para man.sonda).
            blk = struct( ...
                'artefato',      string(obj.path), ...
                'x_hash',        string(obj.x_hash), ...
                'f_hash',        string(obj.f_hash), ...
                'S',             obj.S, ...
                'k',             obj.k, ...
                'n_blocos',      obj.n_blocos, ...
                'n_linhas',      obj.n_linhas, ...
                'n_falhas',      obj.n_falhas, ...
                'tempo_total_s', obj.tempo_total_s, ...
                'geracoes',      obj.gens_sondadas(:).');
        end
    end

    methods (Access = private)
        function fire(obj, g, fn, ftm, motivo, varargin)
        % UM disparo = UM bloco de EXATAMENTE S linhas na ③, ordem do artefato.
            meta = obj.metaOf(varargin{:});

            % ── I1: RNG salvo e restaurado aconteca o que acontecer ──────────
            st_rng = rng();
            cleanup = onCleanup(@() rng(st_rng)); %#ok<NASGU>

            t0 = tic;
            ok = true;
            try
                rows = fn(obj.X);            % I2/I3: lote unico, ordem preservada
                assert(iscell(rows), 'sonda: predict_fn deve devolver cell de srows');
                assert(numel(rows) == obj.S, ...
                    'sonda: predict_fn devolveu %d linhas != S=%d (%s)', ...
                    numel(rows), obj.S, meta.modelo);

                % ── I4: os invariantes carimbados pela CLASSE ────────────────
                for i = 1:obj.S
                    rows{i}.regime = "sonda";
                    rows{i}.real_solution_id = [];       % NULL por contrato
                    rows{i}.fe_treino_max = ftm;
                end
                obj.buf.addGeneration(struct('g', g, 'srows', {rows}));
                obj.n_blocos = obj.n_blocos + 1;
                obj.n_linhas = obj.n_linhas + obj.S;
                obj.gens_sondadas(end+1) = g;
            catch ME
                % I5: o hard-stop TEM de subir; qualquer outra falha vira guarda.
                if strcmp(ME.identifier, 'PlatEMO:Termination'), rethrow(ME); end
                ok = false;
                obj.n_falhas = obj.n_falhas + 1;
                obj.guard('sonda_falhou', g, 'modelo', meta.modelo, ...
                          'erro', string(ME.identifier), 'msg', string(ME.message));
            end
            dt = toc(t0);                    % I6: cronometro proprio

            obj.tempo_total_s  = obj.tempo_total_s + dt;
            obj.tempo_pendente = obj.tempo_pendente + dt;
            obj.event(g, meta, motivo, dt, ok, ftm);
        end

        function meta = metaOf(~, varargin)
            meta = struct('modelo', "");
            for i = 1:2:numel(varargin)
                meta.(varargin{i}) = varargin{i+1};
            end
        end

        function event(obj, g, meta, motivo, dt, ok, ftm)
        % Evento `sonda` do .jsonl (§6/DI-09): geracao, fe, n_pontos, tempo e o
        % hash-check do artefato. O `fe` e o eixo de comparacao entre algoritmos.
            if isempty(obj.fid) || obj.fid <= 2, return; end
            rec = struct('ts', obj.nowIso(), 'rec', "sonda", ...
                'alg', string(obj.alg), 'geracao', double(g), ...
                'modelo', string(meta.modelo), 'motivo', string(motivo), ...
                'n_pontos', obj.S, 'tempo_pred_sonda_s', dt, ...
                'fe_treino_max', double(opt_or_nan(ftm)), ...
                'x_hash', string(obj.x_hash), 'ok', ok);
            try, fprintf(obj.fid, '%s\n', jsonencode(rec)); catch, end
        end

        function guard(obj, name, g, varargin)
            if isempty(obj.fid) || obj.fid <= 2, return; end
            s = struct('ts', obj.nowIso(), 'rec', "guard", ...
                       'name', string(name), 'geracao', double(g));
            for i = 1:2:numel(varargin), s.(varargin{i}) = varargin{i+1}; end
            try, fprintf(obj.fid, '%s\n', jsonencode(s)); catch, end
        end

        function s = nowIso(~)
            s = string(datetime('now', 'TimeZone', 'UTC', ...
                                'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));
        end
    end
end

function v = opt_or_nan(v)
    if isempty(v), v = NaN; end
end
