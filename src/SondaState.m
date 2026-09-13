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
%   snd.finalProbe();                                  % ver DI-19.5 abaixo
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
        g_armado double = []              % [DI-19.5] a geracao do modelo ARMADO

        % [G-6] sonda DESARMADA por `UA_DD_SAEA_SONDA_OFF` — o gemeo MATLAB do
        % `sonda_on`. O objeto existe (o manifesto continua legivel), mas nenhum
        % caminho chega ao `fire`. Vai ao manifesto: a sonda nunca some calada.
        desligada (1,1) logical = false
    end

    % ── [A11/I-6/D11] SONDA ESTRATIFICADA — contadores SEPARADOS ────────────
    % Contadores PROPRIOS, nunca somados aos da regua. A regua Sobol e o unico
    % objeto comparavel ENTRE algoritmos (mesmos S pontos, mesmo x_hash); o bloco
    % estratificado amostra perto do arquivo CORRENTE, que e diferente em cada
    % config. Somar os dois no `man.sonda` destruiria essa comparabilidade — e o
    % plano e explicito: "NUNCA misturado a regua Sobol".
    properties (SetAccess = private)
        n_blocos_estrat  (1,1) double = 0
        n_linhas_estrat  (1,1) double = 0
        n_falhas_estrat  (1,1) double = 0
        tempo_estrat_s   (1,1) double = 0
        gens_estrat      double = []
    end

    properties (Constant)
        N_ESTRAT         (1,1) double = 500     % espelha H.SONDA_ESTRAT_N
        SIGMA_REL_ESTRAT (1,1) double = 0.05    % espelha H.SONDA_ESTRAT_SIGMA_REL
        USO_ESTRAT       (1,1) double = 91      % espelha H.SONDA_ESTRAT_USO
    end

    properties (Access = private)
        buf                      % RunBuffer (o MESMO coletor da busca)
        fid    = []              % fid do .jsonl
        alg    char = ''
        tempo_pendente (1,1) double = 0   % tempo desde o ultimo takePendingTime
        armado = []              % struct{fn, ftm, meta} do ULTIMO fit visto
        tempo_pendente_estrat (1,1) double = 0   % [A11] pendente SEPARADO
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
            % [G-6] O gemeo MATLAB do `sonda_on` dos runners Python. Sem ele o
            % par de nao-perturbacao (§3.1: a ① tem de ser BIT-IDENTICA com e sem
            % sonda) so podia ser provado nos 10 configs Python — os 13 MATLAB
            % ficavam na promessa.
            %
            % DESARMAR, NAO SUMIR. A alternativa obvia — `load_sonda` devolver []
            % — parece mais simples porque os 14 sitios de construcao ja fazem
            % `if ~isempty(sd)`, mas QUEBRA o manifesto: `build_manifest` le
            % `snd.n_blocos`/`n_linhas`/`n_falhas` direto, e `[].n_blocos` e erro.
            % Aqui o objeto existe, os contadores ficam em 0 e o manifesto
            % DECLARA `desligada=true` — a sonda nunca some em silencio.
            obj.desligada = ~isempty(getenv('UA_DD_SAEA_SONDA_OFF')) && ...
                            ~strcmp(getenv('UA_DD_SAEA_SONDA_OFF'), '0');
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
            tf = ~obj.desligada && (g >= 1) && (g == 1 || mod(g, obj.k) == 0);
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
            if obj.desligada, return; end            % [G-6]
            obj.fire(NaN, fn, ftm, 'offline', varargin{:});
        end

        function finalProbe(obj, ~)
        % [DECISAO DO AUTOR] A sonda da ULTIMA geracao, disparada pelo run_*
        % DEPOIS do Algorithm.Solve — fora do laco, ja com a excecao de termino
        % engolida. Nao repete se a geracao ja foi sondada pela cadencia.
        %
        % [DI-19.5, autor 2026-07-19] A geracao usada e a do modelo ARMADO
        % (`g_armado`), NAO o `buf.gen` corrente. Motivo: em configs de overshoot
        % ZERO (c238), a PlatEMO:Termination sai do TOPO do ciclo seguinte
        % (ALGORITHM.m:128) DEPOIS de o outputFcn ja ter bumpado a geracao — o
        % `buf.gen` pos-Solve aponta uma geracao que NUNCA foi armada, e o bloco
        % final sairia carimbado com a geracao errada. O argumento posicional
        % legado e aceito e IGNORADO para nao quebrar os call-sites existentes.
            if obj.desligada, return; end            % [G-6]
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

        function t = takePendingTimeEstrat(obj)
        % [A11] O MESMO rito, em acumulador SEPARADO. Existe para o chamador
        % poder descontar o bloco estratificado do `tempo_geracao_s` (DI-13.10)
        % SEM contaminar o `tempo_pred_sonda_s`, que e a metrica da regua Sobol e
        % tem de continuar comparavel entre algoritmos. Somar os dois faria o
        % custo da regua parecer ~25% maior nos 4 classificadores e em mais
        % nenhum config — um artefato de instrumentacao virando "achado".
            t = obj.tempo_pendente_estrat;
            obj.tempo_pendente_estrat = 0;
        end

        function probeEstratificada(obj, g, arquivoX, xl, xu, fn, ftm, varargin)
        % [A11/I-6/D11] UM bloco `regime='sonda_estratificada'` na ③ + evento ⑥.
        %
        % POR QUE EXISTE. A regua Sobol responde "o modelo e bom GLOBALMENTE?".
        % Ela NAO responde "ele acerta ONDE a decisao acontece?", porque pontos
        % Sobol quase nunca sao bons: a prevalencia MEDIDA da classe positiva e
        % 0,4% => ~8 positivos por bloco de 2.000, e com 8 positivos
        % precision/recall/F1 tem variancia enorme (so o AUC fica estavel).
        % Subir para 3.000 Sobol NAO resolve — a prevalencia nao muda, so o n. A
        % ESTRATIFICACAO e o que resolve: no gemeo Python a prevalencia medida
        % subiu de 0,4% para 7,4% (18x mais positivos).
        %
        % O QUE NAO SE FAZ. Misturar com a regua. Os S pontos Sobol seguem
        % intactos e comparaveis entre TODOS os algoritmos; este bloco sai com
        % `regime='sonda_estratificada'` e NUNCA entra na mesma analise — cada
        % algoritmo tem um arquivo diferente, logo o bloco nao e comparavel ENTRE
        % configs (a ressalva que o autor aceitou ao escolher a opcao (b)).
        %
        % ARGUMENTOS
        %   g         geracao (>=1) ou NaN (NULL, regime offline)
        %   arquivoX  n x D, arquivo CORRENTE em bounds NATIVOS
        %   xl, xu    1 x D bounds nativos (para o ruido e o clip)
        %   fn        @(X) -> cell de srows, MESMO contrato do `fire` da regua
        %   ftm       fe_treino_max (carimbado pela classe, invariante I4)
        %   name-value opcionais:
        %     'true_f'         @(X) -> n x M, avaliado FORA do orcamento (§17.2.2/
        %                      DI-08: problemas analiticos, custo de FE ZERO) —
        %                      so para a PREVALENCIA no ⑥; o f NAO vai a ③.
        %     'semente_bloco'  inteiro; default = derivado de (alg,g,uso=91)
        %     'modelo'         string do modelo (vai ao evento)
        %     'n'              tamanho do bloco (default N_ESTRAT=500)
            if obj.desligada, return; end            % [G-6]
            p = obj.metaOf(varargin{:});
            n = obj.N_ESTRAT;
            if isfield(p, 'n') && ~isempty(p.n), n = double(p.n); end
            semente = obj.sementeBlocoEstrat(g);
            if isfield(p, 'semente_bloco') && ~isempty(p.semente_bloco)
                semente = double(p.semente_bloco);
            end

            % ── I1: RNG global salvo e restaurado aconteca o que acontecer ────
            % Cinto E suspensorio, igual ao gemeo Python (que usa um Generator
            % LOCAL *dentro* de `preserve_all_rng`): a amostragem abaixo usa um
            % RandStream PROPRIO e nao deveria tocar o gerador global, mas o
            % `fn` do chamador pode — e o invariante da §3.1 e que a ① seja
            % bit-identica com e sem a sonda.
            st_rng = rng();
            cleanup = onCleanup(@() rng(st_rng)); %#ok<NASGU>

            t0 = tic;
            ok = true;
            nlin = 0;
            prevalencia = NaN;
            try
                X = obj.amostraEstratificada(arquivoX, xl, xu, n, ...
                                             obj.SIGMA_REL_ESTRAT, semente);
                if isempty(X)
                    dt = toc(t0);
                    obj.tempo_estrat_s = obj.tempo_estrat_s + dt;
                    obj.tempo_pendente_estrat = obj.tempo_pendente_estrat + dt;
                    obj.eventEstrat(g, p, dt, true, ftm, 0, 0, NaN, semente);
                    return;                       % arquivo vazio: no-op honesto
                end
                rows = fn(X);
                assert(iscell(rows), ...
                    'sonda_estrat: predict_fn deve devolver cell de srows');
                assert(numel(rows) == size(X, 1), ...
                    'sonda_estrat: predict_fn devolveu %d linhas != %d pontos', ...
                    numel(rows), size(X, 1));

                % ── I4: os invariantes carimbados pela CLASSE ────────────────
                for i = 1:numel(rows)
                    rows{i}.regime = "sonda_estratificada";
                    rows{i}.real_solution_id = [];      % NULL por contrato
                    rows{i}.fe_treino_max = ftm;
                end
                obj.buf.addGeneration(struct('g', g, 'srows', {rows}));
                nlin = numel(rows);
                obj.n_blocos_estrat = obj.n_blocos_estrat + 1;
                obj.n_linhas_estrat = obj.n_linhas_estrat + nlin;
                obj.gens_estrat(end+1) = g;

                % PREVALENCIA — o unico agregado que justifica o bloco existir.
                % O `f` VERDADEIRO nao vai a ③: o schema dela e contrato (§3) e
                % muda-lo custaria re-run de tudo por ZERO informacao nova (os
                % problemas sao analiticos e deterministicos, a analise recompoe
                % de X). Mesma doutrina do I-12.
                if isfield(p, 'true_f') && ~isempty(p.true_f)
                    try
                        Fv = p.true_f(X);
                        prevalencia = sum(NDSort(Fv, 1) == 1) / size(Fv, 1);
                    catch
                        prevalencia = NaN;          % nunca derruba o run
                    end
                end
            catch ME
                % I5: o hard-stop TEM de subir; o resto vira guarda.
                if strcmp(ME.identifier, 'PlatEMO:Termination'), rethrow(ME); end
                ok = false;
                obj.n_falhas_estrat = obj.n_falhas_estrat + 1;
                obj.guard('sonda_estratificada_falhou', g, ...
                          'erro', string(ME.identifier), ...
                          'msg', string(ME.message));
            end
            dt = toc(t0);                           % I6: cronometro proprio

            obj.tempo_estrat_s = obj.tempo_estrat_s + dt;
            obj.tempo_pendente_estrat = obj.tempo_pendente_estrat + dt;
            obj.eventEstrat(g, p, dt, ok, ftm, nlin, ...
                            size(reshape(arquivoX, [], max(numel(xl),1)), 1), ...
                            prevalencia, semente);
        end

        function blk = manifestBlockEstrat(obj)
        % [A11] A certidao do bloco estratificado — SEPARADA do man.sonda.
        % `comparavel_entre_configs = false` e a linha mais importante daqui: e o
        % que impede alguem, seis meses depois, de por os dois no mesmo grafico.
            blk = struct( ...
                'regime',                  "sonda_estratificada", ...
                'n',                       obj.N_ESTRAT, ...
                'sigma_rel',               obj.SIGMA_REL_ESTRAT, ...
                'uso_id',                  obj.USO_ESTRAT, ...
                'n_blocos',                obj.n_blocos_estrat, ...
                'n_linhas',                obj.n_linhas_estrat, ...
                'n_falhas',                obj.n_falhas_estrat, ...
                'tempo_total_s',           obj.tempo_estrat_s, ...
                'geracoes',                obj.gens_estrat(:).', ...
                'desligada',               obj.desligada, ...   % [G-6]
                'comparavel_entre_configs', false, ...
                'nota', "amostrado PERTO do arquivo corrente (cada config tem " + ...
                        "um arquivo diferente) — NUNCA misturar com regime='sonda'");
        end

        function blk = manifestBlock(obj)
        % A certidao da regua usada no run (vai para man.sonda).
            blk = struct( ...
                'artefato',      string(obj.path), ...
                'x_hash',        string(obj.x_hash), ...
                'f_hash',        string(obj.f_hash), ...
                'regime',        string(obj.regime), ...  % [B34/DI-21] explicito (S ja desambigua; isto poupa a inferencia)
                'S',             obj.S, ...
                'k',             obj.k, ...
                'n_blocos',      obj.n_blocos, ...
                'n_linhas',      obj.n_linhas, ...
                'n_falhas',      obj.n_falhas, ...
                'tempo_total_s', obj.tempo_total_s, ...
                'desligada',     obj.desligada, ...   % [G-6] nunca some calada
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

        function X = amostraEstratificada(~, arquivoX, xl, xu, n, sigma_rel, semente)
        % [A11] `n` pontos PERTO do arquivo corrente, clipados aos bounds.
        %
        % Espelha `standalone_harness.amostra_estratificada`: sorteia com
        % reposicao uma linha-base do arquivo e soma ruido gaussiano de desvio
        % `sigma_rel * (xu - xl)` por dimensao.
        %
        % DETERMINISMO SEM TOCAR O GLOBAL: usa um `RandStream` PROPRIO. Isto e
        % mais forte que o `rng(semente)` que seria o reflexo natural em MATLAB —
        % aquele reposicionaria o gerador global, e mesmo com o onCleanup
        % restaurando depois, qualquer excecao entre o `rng` e o restore deixaria
        % a busca com uma sequencia diferente. Com RandStream proprio o gerador
        % global NUNCA e escrito.
        %
        % ⚠ NAO e bit-identico ao gemeo Python. O Python usa
        % `numpy.random.default_rng` (PCG64) semeado por `SeedSequence`; nao
        % existe equivalente exato em MATLAB e reimplementar o SeedSequence aqui
        % seria custo alto por ZERO ganho: o bloco nao e comparavel ENTRE
        % configs por construcao, entao os pontos do b4 nunca serao confrontados
        % com os do c122. O que o contrato exige e REPRODUTIBILIDADE (mesmo run,
        % mesma semente => mesmos pontos), e isso o RandStream garante.
            X = [];
            A = reshape(arquivoX, [], numel(xl));
            if isempty(A), return; end
            xl = reshape(double(xl), 1, []);
            xu = reshape(double(xu), 1, []);
            n  = max(0, round(double(n)));
            if n == 0, return; end
            rs   = RandStream('mt19937ar', 'Seed', mod(double(semente), 2^32));
            idx  = randi(rs, size(A, 1), n, 1);
            base = double(A(idx, :));
            desv = sigma_rel .* (xu - xl);
            ruido = randn(rs, n, numel(xl)) .* repmat(desv, n, 1);
            X = min(max(base + ruido, repmat(xl, n, 1)), repmat(xu, n, 1));
        end

        function s = sementeBlocoEstrat(obj, g)
        % [A11/D62] Semente do bloco, derivada e DOCUMENTADA.
        %
        % O gemeo Python usa `iteration_seed(base, alg_id, iteracao, uso_id=91)`
        % = `numpy.random.SeedSequence((...))`. Nao ha SeedSequence em MATLAB e
        % nao afirmo paridade bit-a-bit (ver `amostraEstratificada`). Aqui a
        % mistura e explicita e verificavel a olho: FNV-1a de 64 bits sobre a
        % tupla (alg, geracao, uso=91), reduzida a 32 bits.
        %
        % O que importa para o contrato: mesma (alg, g) => mesma semente, e
        % geracoes diferentes => sementes descorrelacionadas (o proposito do
        % uso_id/iteracao do D62 e nao reusar o mesmo fluxo em usos distintos).
        %
        % ⚠ POR QUE **NAO** E UM FNV-1a. A primeira versao deste metodo usava
        % FNV-1a de 64 bits em `uint64`. Em MATLAB a aritmetica de inteiros
        % **SATURA** em vez de dar wrap-around (ao contrario de C/numpy): apos
        % duas multiplicacoes o acumulador crava em `intmax('uint64')` e daí em
        % diante TODA geracao devolveria a MESMA semente — o bloco estratificado
        % sairia identico em todos os ciclos e o `sigma_rel` seria decorativo.
        %
        % O mixer abaixo e o Lehmer/MINSTD (`mod(s*16807, 2^31-1)`), escolhido
        % por uma razao aritmetica verificavel: o produto maximo e
        % (2^31-2)*16807 ~ 3,6e13, **abaixo de 2^53**, logo cada passo e EXATO em
        % ponto flutuante double — sem saturacao e sem perda de bits.
            gg = double(g);
            if isnan(gg), gg = 0; end
            M = 2147483647;                            % 2^31 - 1 (primo)
            s = 1;
            simbolos = [double(char(obj.alg)), gg, obj.USO_ESTRAT];
            for i = 1:numel(simbolos)
                v = mod(round(simbolos(i)), M);
                s = mod(mod(s + v, M) * 16807, M);     % produto < 2^53 => exato
            end
            if s == 0, s = 1; end                      % 0 e ponto fixo do MINSTD
        end

        function eventEstrat(obj, g, p, dt, ok, ftm, nlin, n_arquivo, prev, semente)
        % [A11] Evento `sonda_estratificada` no ⑥ — nome PROPRIO, nunca `sonda`.
        % Se reusasse `rec='sonda'`, todo consumidor que conta blocos da regua
        % (censo, gates G-2/G-4, tabela42) passaria a contar 2x nos 4
        % classificadores e em nenhum outro config.
            if isempty(obj.fid) || obj.fid <= 2, return; end
            modelo = "";
            if isfield(p, 'modelo'), modelo = string(p.modelo); end
            rec = struct('ts', obj.nowIso(), 'rec', "sonda_estratificada", ...
                'alg', string(obj.alg), 'geracao', double(g), ...
                'modelo', modelo, 'n_pontos', double(nlin), ...
                'tempo_pred_s', dt, ...
                'fe_treino_max', double(opt_or_nan(ftm)), ...
                'sigma_rel', obj.SIGMA_REL_ESTRAT, ...
                'semente_bloco', double(semente), ...
                'n_arquivo', double(n_arquivo), ...
                'prevalencia_nd_no_bloco', prev, ...
                'ok', ok, ...
                'nota', "bloco NAO-comparavel entre algoritmos (cada um tem um " + ...
                        "arquivo diferente) — NUNCA misturar com regime='sonda'");
            try, fprintf(obj.fid, '%s\n', jsonencode(rec)); catch, end
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
