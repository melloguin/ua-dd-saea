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
        case 'c238'
            % R1-c238 (fan-out): EIM (repo STANDALONE do autor — NAO e Algorithm
            % do PlatEMO) via EMBRULHO classdef N.5 (algorithms/c238_EIM/EIM.m),
            % no MESMO padrao do caso-modelo c217 (DoE injetado D63/D87;
            % FEBudget/ponte D89/D61; ancora c238-hypervolume-rm aplicada).
            [status, info] = run_c238(alg, problema_id, semente, exp, dataRoot);
        case 'e74'
            % R1-e74 (fan-out): CLMEA (repo do autor = arvore PlatEMO 4.1
            % PROPRIA e completa — D95/N.0-4.1). NAO roda na 4.15: worker de
            % path DEDICADO (rmpath 4.15 -> addpath CLMEA_Code -> restaura no
            % onCleanup); ponte POR INDIVIDUO (UserProblem 4.1 nao tem 'once');
            % patches 🔴 e74-mask/e74-ndsort-obj + mins L.8 + D74 aplicados na
            % propria arvore.
            [status, info] = run_e74(alg, problema_id, semente, exp, dataRoot);
        case 'e103'
            % R1-e103 (ULTIMO cartao MATLAB da R1; o UNICO OFFLINE dela):
            % IBEA-MS (repo standalone do autor — funcao IBEAMS(Global) com
            % struct propria, NAO e PlatEMO-API; wrapper L.15/N.3). Treina UMA
            % vez no dataset injetado (D90, 31D-1) e busca SO no surrogate:
            % ZERO FE real na busca (o FEBudget e a rede — orcamento esgotado
            % na carga; qualquer avaliacao nova = violacao offline). Worker de
            % path DEDICADO (molde e74): rmpath 4.15 E CLMEA_Code -> addpath
            % e103 -> asserts which-all -> onCleanup restaura. Sem cd().
            [status, info] = run_e103(alg, problema_id, semente, exp, dataRoot);
        case {'nsga2', 'nsga3', 'moead', 'smsemoa'}
            % R1-pisos: os 4 PISOS ONLINE (NSGA-II, NSGA-III, MOEA/D type=1,
            % SMS-EMOA puro) — MOEAs STOCK do PlatEMO 4.15, SEM surrogate, que
            % sao a REGUA (baseline) do estudo (§3.2/D25). Mesmo padrao do
            % caso-modelo c217, com DUAS especificidades do cartao:
            %   (a) semeadura §3.2/D88 — a evolucao parte dos MELHORES N do DoE
            %       por nao-dominancia + crowding distance (deterministico);
            %   (b) sem surrogate => ③ VAZIA e serie §17.6 VAZIA (S.7: o .jsonl
            %       dos pisos e so o minimo comum).
            % ZERO patch no PlatEMO: os pisos sao stock POR DESIGN.
            [status, info] = run_piso(alg, problema_id, semente, exp, dataRoot);
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
    t0_run = tic;                                  % [§17.6] wall total do run

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

    % ── SONDA DI-09 (§17.2.2): o autoteste da infra transversal ──────────────
    % O stub exercita o caminho INTEIRO (artefato -> CP do x_hash -> SondaState
    % -> ③ regime='sonda' -> ④ tempo_pred_sonda_s -> man.sonda) SEM algoritmo
    % real, para que uma regressao da infra apareca aqui e nao no 1o config.
    sd  = load_sonda(problema, D, M, dataRoot);
    snd = [];
    if ~isempty(sd), snd = SondaState(sd, buf, fid, alg); end
    % predict_fn de mentira (deterministico): mu = x(:,1)*g, sigma constante.
    mk_fn = @(gg) @(Xs) arrayfun(@(i) {RunBuffer.mkSurrogateRow(Xs(i,:), ...
                        'mu', Xs(i,1) * gg * ones(1,M), ...
                        'sigma', 1e-3 * ones(1,M), ...
                        'pred_tipo', "valor", 'modelo_flag', "STUB")}, ...
                        (1:size(Xs,1)).');
    % PROVA de nao-perturbacao do RNG (o gate do e7, exercitado desde o stub):
    rng(12345, 'twister');
    rand_antes = rand();
    st_ref = rng();
    snd_fn = mk_fn(1);
    snd.probe(1, snd_fn, bud.fe - 1, 'modelo', "STUB");
    st_dep = rng();
    rng_intacto = isequal(st_ref.Type, st_dep.Type) && ...
                  isequal(st_ref.Seed, st_dep.Seed) && ...
                  isequal(st_ref.State, st_dep.State);
    rand_depois = rand();                     % tem de ser o MESMO sorteio de
    rng(12345, 'twister'); rand();            % um run sem sonda nenhuma
    rand_sem_sonda = rand();
    rng_mesma_sequencia = (rand_depois == rand_sem_sonda);

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
        % Sonda das geracoes seguintes (a g=1 ja rodou acima, no teste de RNG):
        % k=2 => dispara em g=3; em g=2 so ARMA (custo ~zero).
        if g >= 2
            snd.probe(g, mk_fn(g), bud.fe - 1, 'modelo', "STUB");
        end
        % §17.6 timing: um evento de retreino por geracao + os 2 campos novos.
        view.timing = struct('n_acumulado', n_init + g*5, ...
                             'tempo_fit_s', 0.001*g, 'tempo_busca_s', 0.002, ...
                             'tempo_pred_sonda_s', snd.takePendingTime(), ...
                             'tempo_geracao_s', 0.01*g);
        buf.addGeneration(view);
        jsonl_line(fid, 'timing', {'n_acumulado', n_init + g*5, 'tempo_fit_s', 0.001*g});
    end

    % (5b) SONDA FINAL (§17.2.2 "SEMPRE a ultima"): fora do laco, sobre o modelo
    % ARMADO no ultimo fit — o caminho que no algoritmo real roda depois que o
    % hard-stop matou o `while`.
    %
    % [DI-19.5, autor 2026-07-19] O finalProbe usa a geracao do modelo ARMADO
    % (`g_armado`), NAO um argumento do chamador. Os dois casos testados aqui sao
    % exatamente a dicotomia do algoritmo real:
    %   (i)  o ultimo fit CAIU na cadencia (G=3 ja sondada) => NO-OP;
    %   (ii) o ultimo fit NAO caiu na cadencia (g=5 e impar: `probe` ARMA e nao
    %        dispara) => o finalProbe DISPARA, e o bloco tem de sair carimbado
    %        com g=5 (o modelo armado), nunca com outra geracao.
    % O caso (ii) e a regressao do bug que a DI-19.5 corrige: sob a semantica
    % antiga (`finalProbe(buf.gen)`) um config de overshoot zero carimbava o
    % bloco final com uma geracao que NUNCA existiu.
    % Estado ao sair do laco: a cadencia (g = 1,2,4,...) disparou em g=1 e g=2;
    % o probe de g=3 (impar) apenas ARMOU. Logo g_armado = 3 e INEDITA.
    n0 = snd.n_blocos;                       % 2 blocos
    armou_sem_disparar = (n0 == 2) && isequal(snd.g_armado, 3);

    % (ii) o ultimo fit NAO caiu na cadencia => o finalProbe DISPARA, e o bloco
    % tem de sair carimbado com g_armado=3 (o modelo que de fato existe).
    snd.finalProbe();
    final_disparou = (snd.n_blocos == n0 + 1);
    final_carimbou_armado = ~isempty(snd.gens_sondadas) && ...
                            snd.gens_sondadas(end) == 3;

    % (i) o ultimo fit CAIU na cadencia (g=4 e par => probe dispara e arma) =>
    % o finalProbe seguinte tem de ser NO-OP (nao repete geracao ja sondada).
    snd.probe(4, mk_fn(4), bud.fe - 1, 'modelo', "STUB");
    n1 = snd.n_blocos;
    snd.finalProbe();
    final_foi_noop = (snd.n_blocos == n1);

    % (5c) [DI-13.5 · adendo da torre] REGRESSAO DO WRITER: `geracao` NULLABLE.
    % Um bloco de sonda OFFLINE (geracao = NULL) emitido no MESMO arquivo que as
    % linhas de busca (geracao inteira) exercita o branch int32-x-double do
    % write_surrogate: em MATLAB `int32(NaN)` = 0, entao um cast incondicional
    % faria o bloco offline virar silenciosamente "geracao 0". O stub cobre isso
    % SEM precisar rodar o e103 (que e caro). A conferencia e feita apos o export.
    sd_off = load_sonda(problema, D, M, dataRoot, 'offline');
    n_off  = 0;
    if ~isempty(sd_off)
        snd_off = SondaState(sd_off, buf, fid, alg);
        snd_off.probeOffline(mk_fn(1), bud.fe - 1, 'modelo', "STUB-OFFLINE");
        n_off = snd_off.n_linhas;
    end

    % (6) EXPORT das 4 camadas (§17.2/§17.3) — parquet brotli+single, atomico.
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (6b) [DI-13.5] CONFERE A COLUNA `geracao` NOS DOIS LADOS, relendo o parquet
    % que acabou de ser escrito (nao o buffer — o que importa e o que foi ao disco).
    %   sonda OFFLINE -> NULL (NaN)      ·      linhas de busca -> inteiro >= 1
    % Ler NULL como 0 e o sintoma de `int32(NaN)`; ler a busca como NULL e o
    % sintoma oposto (a coluna caiu para double sem preservar os valores).
    ger_null_ok = true; ger_busca_ok = true;
    if n_off > 0
        Tchk = parquetread(nm_layer_path(exp, alg, problema, semente, 'surrogate', dataRoot));
        eh_sonda = (string(Tchk.regime) == "sonda");
        gg = double(Tchk.geracao);
        % as linhas de sonda ONLINE do stub tem geracao inteira; so as OFFLINE
        % sao nulas — e sao exatamente n_off linhas.
        ger_null_ok  = (sum(isnan(gg)) == n_off);
        ger_busca_ok = ~any(isnan(gg(~eh_sonda))) && all(gg(~eh_sonda) >= 1) && ...
                       all(mod(gg(~eh_sonda), 1) == 0);
    end

    % (7) CP-init por-run (D87/D88): hash da init X (float64) = sidecar do DoE.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);

    % (8) MANIFESTO (§17.2/§17.7) — status ok, FE final, CP-init, timing.
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    % [v5.2.1/§17.6] bloco `timing` OBRIGATORIO + fit_series + man.sonda.
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), snd);
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', "ok", 'fe_final', bud.fe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok});
    fclose(fid);

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'cache_hits', bud.cache_hits, ...
        'cache_hit_zero_fe', cache_hit_zero_fe, 'hard_stopped', hard_stopped, ...
        'doe_hash_run', string(doe_hash_run), 'doe_hash_sidecar', string(doe.hash), ...
        'cp_ok', cp_ok, ...
        'sonda_x_hash_ok', true, ...            % load_sonda aborta se divergir
        'sonda_n_blocos', snd.n_blocos, 'sonda_n_linhas', snd.n_linhas, ...
        'sonda_n_falhas', snd.n_falhas, ...
        'rng_intacto', rng_intacto, 'rng_mesma_sequencia', rng_mesma_sequencia, ...
        'final_foi_noop', final_foi_noop, ...
        'final_armou_sem_disparar', armou_sem_disparar, ...
        'final_disparou', final_disparou, ...
        'final_carimbou_armado', final_carimbou_armado, ...   % [DI-19.5]
        'sonda_off_linhas', n_off, ...                        % [DI-13.5]
        'ger_null_ok', ger_null_ok, 'ger_busca_ok', ger_busca_ok, ...
        'tempo_aval_real_s', bud.tempo_aval_real_s);
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
    t0_run = tic;                                  % [§17.6] wall total do run

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
    %   - [DI-09] snd = SondaState. Entra AQUI porque UserProblem.data e
    %     SetAccess=protected: nao ha como injetar de dentro do algoritmo.
    %     O load_sonda confere o x_hash no arranque e ABORTA em divergencia.
    sd  = load_sonda(problema, D, M, dataRoot);
    snd = [];
    if ~isempty(sd), snd = SondaState(sd, buf, fid, alg); end
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, 'snd', snd, ...
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

    % (7b) [DI-09] SONDA da ULTIMA geracao — FORA do laco. O hard-stop (D61) mata
    % o corpo no meio do ciclo, entao o bloco da ultima geracao nunca rodaria por
    % dentro; aqui ele dispara sobre o modelo ARMADO no ultimo fit. No-op se a
    % geracao corrente ja foi sondada pela cadencia k=2.
    if ~isempty(snd), snd.finalProbe(buf.gen); end

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
    % [v5.2.1/§17.6] bloco `timing` OBRIGATORIO + fit_series + man.sonda (DI-09).
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), snd);
    % [DI-20.6#2] sigma_dict OBRIGATORIO (DEF-C4): estava NULL nos 3 manifestos
    % do c217 — a regra 3 do R4 torna a ③ "leitura proibida" sem ele. O c217 e
    % score par-a-par (DEF-C1): nao ha mu/sigma; o dicionario diz o que as
    % colunas pred_* significam. Semantica do handoff R1-c217 §7 (ja no header
    % do jsonl — aqui e a copia da CERTIDAO, que e o que a R4 le).
    man.sigma_dict = struct( ...
        'pred_score', "score ternario {-1,0,+1} AGREGADO do PNN par-a-par vs a referencia corrente Pmid (nao ha comparacao O(n^2) gravada — DEF-C2)", ...
        'pred_confianca', "Error1 do ciclo (confiabilidade estimada do classificador; CONSTANTE por bloco/geracao — e um atributo do MODELO, nao do ponto)", ...
        'mu_sigma', "NULL SEMPRE (classificador par-a-par puro — nao ha cabeca de valor nem incerteza)", ...
        'REGRA_DO_ROTULO', "[A9] Como recuperar o rotulo VERDADEIRO de uma " + ...
            "linha da sonda. ⚠ O emparelhamento e POSICIONAL E CICLICO, nao " + ...
            "'contra todas as referencias': RBFNNPC.m:59-62 compara a linha i " + ...
            "com Preference(mod(i+numberP,numberP)+1,:), ou seja CADA ponto da " + ...
            "sonda e julgado contra UMA referencia especifica, determinada pela " + ...
            "sua POSICAO no bloco. Logo: (1) leia `pmid_ids` do evento " + ...
            "`c217_gen` da MESMA geracao — e a lista ORDENADA dos solution_id " + ...
            "das referencias Pmid daquele ciclo, na MESMA ordem de `Preference`; " + ...
            "(2) seja n = numel(pmid_ids). Em MATLAB (1-based, como no codigo) a " + ...
            "linha i=1..N pareia com Preference(mod(i,n)+1) — literalmente " + ...
            "mod(i+n,n)+1 de RBFNNPC.m:61, que e o mesmo valor. Em Python/pandas " + ...
            "(0-based), a linha j=0..N-1 pareia com pmid_ids[(j+1) mod n]. " + ...
            "⚠ NAO e pmid_ids[j mod n]: ha um deslocamento de UM, e ele importa " + ...
            "— o comentario do proprio stock diz 'better than a random reference " + ...
            "point', isto e, o pareamento e deliberadamente deslocado; (3) " + ...
            "avalie o f VERDADEIRO do ponto (artefato da sonda) e o f da " + ...
            "referencia (camada ① pelo solution_id) e aplique a mesma leitura " + ...
            "ternaria do preditor: +1 = o candidato e MELHOR que a referencia, " + ...
            "-1 = pior, 0 = indistinguivel. " + ...
            "⚠ NAO agregue contra o conjunto Pmid inteiro: isso mede OUTRA " + ...
            "coisa e infla o numero — e o mesmo erro que as 2 leituras " + ...
            "descartadas do b4 cometiam. " + ...
            "⚠ REORDENAR o bloco muda os PROPRIOS scores (nao so o join), " + ...
            "porque o emparelhamento depende da posicao: qualquer " + ...
            "sort/unique/filtro na ③ antes deste calculo corrompe o rotulo.");
    % [I-07/A9] `params` — a config EFETIVA. O CONTRATO §5 a exige e o c217 era
    % um dos 7 configs sem a chave: 29 celulas medidas na s42 (750 no roster
    % completo). Os valores sao os MESMOS que o header do ⑥ ja declara
    % (PCSAEA('parameter',{0.8,3000}) na linha 448) — quem le a tabela de
    % execucoes nao deve precisar abrir o ⑥ para saber com que delta o run correu.
    man.params = struct( ...
        'delta', 0.8, 'gmax', 3000, ...
        'parameter_posicional', "PCSAEA('parameter', {0.8, 3000}) — delta/gmax", ...
        'N', 50, 'maxfe', maxfe, ...   % o mesmo literal do UserProblem (:440)
        ... % [BL-15] As 3 chaves abaixo eram FALSAS — nao sentinela: afirmacao
        ... % errada, que e pior, porque um leitor do §15.7 cruza o `params` com
        ... % o paper e conclui "confere". Corrigidas contra o codigo:
        ... %  · treino: o Input vem da POPULACAO (CalFitnessPC(Population.objs,
        ... %    Population.decs), PCSAEA.m:39), nao do arquivo;
        ... %  · surrogate: o ALVO do treino e BINARIO {1,2} (CalFitnessPC.m:69-71).
        ... %    O ternario {-1,0,+1} existe, mas e o `pred_score` da regra tripla
        ... %    corrigida (D17) gravado na ③ — outro objeto;
        ... %  · operadores: o c217 roda OperatorGA(...,{1,15,1,5}) nas TRES
        ... %    chamadas de variacao (SurrogateAssistedSelectionPC.m:14/28/46) e
        ... %    a SPEC §567 diz "Balde C NAO se aplica" (eta proprios, K.3).
        ... %    A string antiga era copy-paste byte-a-byte do bloco dos pisos.
        'treino', "TrainIn = subamostra 3/4 estratificada (por estrato) do Input, que vem da POPULACAO corrente (CalFitnessPC(Population.objs,Population.decs) — PCSAEA.m:39), nao do arquivo", ...
        'surrogate', "PNN par-a-par (RBFNNPC, spread 0.1925); alvo de treino BINARIO {1,2} = melhor/pior (CalFitnessPC.m:69-71). O score ternario {-1,0,+1} da ③ e o `pred_score` da regra tripla corrigida (D17), nao o rotulo do modelo", ...
        'operadores', "OperatorGA com {proC=1, dis_c=15, proM=1, dis_m=5} nas 3 chamadas (SurrogateAssistedSelectionPC.m:14/28/46) — Balde C NAO se aplica (SPEC §567; divergencia K.3 declarada vs. o indice 20 do paper)", ...
        'regime', "online", 'q', 1);
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
    t0_run = tic;                                  % [§17.6] wall total do run

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
    %     [DI-09] snd = SondaState (data e SetAccess=protected: so aqui).
    sd  = load_sonda(problema, D, M, dataRoot);
    snd = [];
    if ~isempty(sd), snd = SondaState(sd, buf, fid, alg); end
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, 'snd', snd, ...
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

    % (7b) [DI-09] SONDA da ULTIMA geracao — fora do laco, sobre o modelo ARMADO
    % no ultimo fit. No-op se a geracao ja foi sondada pela cadencia k=2.
    if ~isempty(snd), snd.finalProbe(buf.gen); end

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
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), snd);   % [§17.6/DI-09]
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
    t0_run = tic;                                  % [§17.6] wall total do run

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
    %     [DI-09] snd = SondaState (data e SetAccess=protected: so aqui).
    sd  = load_sonda(problema, D, M, dataRoot);
    snd = [];
    if ~isempty(sd), snd = SondaState(sd, buf, fid, alg); end
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, 'snd', snd, ...
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

    % (7b) [DI-09] SONDA da ULTIMA iteracao — fora do laco, sobre o modelo ARMADO
    % no ultimo fit. No-op se a iteracao ja foi sondada pela cadencia k=2.
    if ~isempty(snd), snd.finalProbe(buf.gen); end

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
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), snd);   % [§17.6/DI-09]
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
    t0_run = tic;                                  % [§17.6] wall total do run

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
    %     [DI-09] snd = SondaState (data e SetAccess=protected: so aqui).
    sd  = load_sonda(problema, D, M, dataRoot);
    snd = [];
    if ~isempty(sd), snd = SondaState(sd, buf, fid, alg); end
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, 'snd', snd, ...
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

    % (7b) [DI-09] SONDA da ULTIMA geracao — fora do laco, sobre o modelo ARMADO
    % no ultimo fit. No-op se aquela geracao ja foi sondada pela cadencia.
    if ~isempty(snd), snd.finalProbe(); end

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
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), snd);   % [§17.6/DI-09]
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
    t0_run = tic;                                  % [§17.6] wall total do run

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
    %     [DI-09] snd = SondaState (data e SetAccess=protected: so aqui).
    sd  = load_sonda(problema, D, M, dataRoot);
    snd = [];
    if ~isempty(sd), snd = SondaState(sd, buf, fid, alg); end
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, 'snd', snd, ...
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

    % (7b) [DI-09] SONDA da ULTIMA geracao — fora do laco, sobre o modelo ARMADO
    % no ultimo fit. No-op se aquela geracao ja foi sondada pela cadencia.
    if ~isempty(snd), snd.finalProbe(); end

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
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), snd);   % [§17.6/DI-09]
    man.params = struct('N', 50, 'K_refs', 6, 'gmax', 3000, ...
        'rede', "H=2D, 1 oculta; zscore (featureInputLayer, CSEA.m:36) + BatchNorm + ReLU + sigmoide + regressionLayer (MSE)", ...
        'treinador', "adam lr=1e-3, 100 epocas, batch 32, sem early-stop, rede NOVA/Glorot por geracao (divergencia em bloco vs paper LM/T=500 — CODIGO, registrada)", ...
        'operadores', "Balde C {1,20,1,20} SUBSTITUI os nativos {1,15,1,5} (§6.2/§6.4)", ...
        'treino', "arquivo INTEIRO (B4.6/D30 — ARTIGO)", ...
        'gate', "4 ramos, 0.4 hardcoded; L>0.9 avalia / L<0.1 descarta; tr=0.5*min(rr,1-rr)", ...
        'exec_env', "cpu (N.2.4 — repro)");
    man.sigma_dict = struct( ...
        'pred_confianca', "L in (0,1) = saida sigmoide da FNN (pseudo-prob. de 'bom'); pred_classe = leitura binaria L>=0.5; a semantica da SELECAO (ramo 3 seleciona L<0.1 — modelo invertido) esta no campo `ramo` do .jsonl", ...
        ... % [I-6] GLOSSARIO p0/p1 — doc-only, e ATIVAMENTE DESTRUTIVO trocar os
        ... % valores: reconstruir o ramo de SurrogateAssistedSelection.m:27-57
        ... % com p0/p1 COMO LOGADOS fecha 6.268/6.268 gerações; TROCADOS cai
        ... % para 1.252/6.268 (19,97%) e desincroniza a string `motivo`, que ja
        ... % imprime "p0=..., p1=...". Sao nomes NATIVOS do PlatEMO, nao indices
        ... % de classe (bloco upstream, md5 fedbabcd0385cdc11351c6b2e38c1485).
        'p0_p1', "p0 = MAE da categoria II (rotulo 1, CSEA.m:78); p1 = MAE da " + ...
                 "categoria I (rotulo 0, CSEA.m:79). NOMES NATIVOS do PlatEMO — " + ...
                 "NAO sao indices de classe e NAO devem ser trocados na leitura", ...
        ... % [I-2 · BL-12/T14.5] A REGRA DO ROTULO VERDADEIRO. Numero em texto se
        ... % MEDE antes de gravar: os 3 valores publicados aqui ate 2026-07-31
        ... % (65,5% / 0,350 / 0,716) NAO reproduzem em corpus NENHUM — nenhuma das
        ... % 5 leituras testadas os produz, e o par "0,40% / 0,995" atribuido a
        ... % uma leitura "errada" e o par que a regra 12 do CONTRATO atribui ao
        ... % c122. Substituidos pelos MEDIDOS, com o corpus E a definicao de cada
        ... % agregado nomeados (prevalencia/acuracia POOLED; AUC = media dos AUC
        ... % por bloco), que e o que faltava para o numero ser conferivel.
        'REGRA_DO_ROTULO', "o b4 (CSEA) classifica um candidato contra as K=6 " + ...
            "REFERENCIAS RADIAIS da geracao, cujos ids estao em `ref_ids` na " + ...
            "linha b4_gen. Rotulo verdadeiro de um ponto da SONDA: avalie o f " + ...
            "verdadeiro do artefato §17.2.2 e aplique a leitura da DI-18 " + ...
            "('nao e pior que TODAS as 6 referencias' — o `GetOutput.m:16-19`, " + ...
            "AND sobre refs e OR sobre objetivos). CALIBRAGEM MEDIDA (⚠ so use " + ...
            "numero com o corpus junto; prevalencia e acuracia POOLED, AUC = " + ...
            "media dos AUC por bloco): regua Sobol do SMOKE (MMF1, 24 blocos, " + ...
            "48.000 linhas) = prevalencia 28,43%, acuracia 0,5743, AUC 0,5075 " + ...
            "(mediana 0,5102); regua da s42 INTEIRA (25 celulas, 3.166 blocos) = " + ...
            "prevalencia 8,32%, acuracia 0,9035, AUC medio 0,6646 (mediana " + ...
            "0,6411). A prevalencia varia ~3,4x entre os dois corpora, entao " + ...
            "calibrar expectativa exige dizer QUAL corpus. " + ...
            "⚠ A leitura 'nao e dominado por nenhuma ref' NAO mede outra coisa " + ...
            "em M=2: ela e NUMERICAMENTE IDENTICA a DI-18 ali (mesmos 28,43% / " + ...
            "0,5743 / 0,5075 na regua do smoke), e 19/25 celulas do b4 sao M=2 — " + ...
            "as duas so divergem em M>=3. A leitura do PAPER (Alg.4, 'domina ao " + ...
            "menos 1 ref') e que difere de fato: 9,85% / 0,6312 na mesma regua. " + ...
            "`pred_confianca` E P(bom) com corte em 0,5 (verificado: max ruim = " + ...
            "0,4999 / min bom = 0,5000). Prevalencia do TREINO por geracao em " + ...
            "`y_treino_dist` (I-5)", ...
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
    t0_run = tic;                                  % [§17.6] wall total do run

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
    %     [DI-09] snd = SondaState. O e7 e o UNICO preditor de fato ESTOCASTICO
    %     (MC-dropout, ~1,4e7 draws/bloco): e AQUI que o save/restore de RNG do
    %     SondaState (I1) deixa de ser redundante e vira o proprio gate.
    sd  = load_sonda(problema, D, M, dataRoot);
    snd = [];
    if ~isempty(sd), snd = SondaState(sd, buf, fid, alg); end
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, 'snd', snd, ...
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

    % (7b) [DI-09] SONDA da ULTIMA geracao — fora do laco, sobre o modelo ARMADO.
    if ~isempty(snd), snd.finalProbe(); end

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
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), snd);   % [§17.6/DI-09]
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
%  RUN-c238 (EIM REAL, repo standalone do autor + EMBRULHO classdef N.5) —
%  fan-out da R1 no padrao do caso-modelo c217. O que e ESPECIFICO do c238: o
%  algoritmo NAO e PlatEMO — e um script standalone (Zhan 2017) convertido p/
%  `classdef EIM < ALGORITHM` (contrato N.5, em algorithms/c238_EIM/EIM.m), que
%  chama as funcoes INTACTAS do repo (GP_Train/Infill_EIM/Optimizer_GA/
%  Paretoset). 'N',100 no UserProblem (N.5-2) e INERTE (GA interno = 10D; init
%  = DoE do artefato). EIM sem 'parameter' (criterion default = 'Euclidean' —
%  EIMe, variante do driver). Patches [IMPL]: guard EIM NaN->0 (Infill_EIM),
%  saidas extras de instrumentacao (Infill_EIM/Optimizer_GA), 2 linhas
%  Hypervolume removidas do script (ancora c238-hypervolume-rm — mex
%  Windows-only). Guard chol = dedup do treino (na EIM.main). A pasta
%  c238_EIM sai do path ao FIM do run (onCleanup — sombra reversa de
%  UniformPoint.m/DTLZ2.m sobre o PlatEMO, licao S.8/R1-e7).
%  Toolboxes: Optimization (fmincon sqp no GP_Train) + Statistics
%  (normcdf/normpdf/lhsdesign).
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_c238(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();
    t0_run = tic;                                  % [§17.6] wall total do run

    % Arvore PlatEMO 4.15 (N.0.1) + a pasta do c238 (repo standalone do autor).
    % O onCleanup REMOVE a pasta do path ao sair (normal OU erro): o proprio
    % ALGORITHM.Solve:81 tambem a PREPENDE (addpath da pasta do classdef) e
    % nunca remove — sem isto, UniformPoint.m/DTLZ2.m do c238_EIM sombreariam
    % os do PlatEMO p/ b1/b3/e7/pisos num run posterior do MESMO processo.
    c238dir = ensure_paths_c238(ROOT);
    pathGuard = onCleanup(@() rmpath_quiet(c238dir)); %#ok<NASGU>

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
        'doe_hash', string(doe.hash), 'algo', "c238-EIM-embrulho-N5", ...
        'criterion', "Euclidean (EIMe — default do driver; paper nao elege)", ...
        'kriging', "OK-Forrester proprio (nao-DACE), kernel gaussiano, ARD 1xD", ...
        'theta0', 1, 'theta_bounds', "[1e-3,1e3]", ...
        'mle', "fmincon sqp em log10(theta), single-start, MaxFunEvals=20D", ...
        'nugget', "(10+n)*eps", 'ga', "pop=10D, 200 ger (CODIGO; paper DE — B10.2)", ...
        'sigma_dict', "mu_j/sigma_j=media/sqrt(max(mse,0)) do kriging proprio POR OBJETIVO, no ESPACO DO MODELO (y min-max por iteracao — paper; C3 transf_params={min,range} -> cru=mu*range+min)"});

    % (4) evalFcn por-x (a ponte, bounds nativos) + embrulho de LOTE (D61) — o
    %     c217_batch_eval e GENERICO (handoff R1-c217 §7): hard-stop no meio do lote.
    evalFcnPerX = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));
    batchEval   = @(X, varargin) c217_batch_eval(X, bud, evalFcnPerX);

    % (5) UserProblem (contrato N.0/L.0): once=true (lote), bounds nativos, minimiza.
    %     'N',100 = N.5-2 (INERTE no c238: o GA interno e 10D e o init e o DoE).
    %     'logger' vai no data p/ a EIM.main emitir guard_range NA DETECCAO
    %     (revisao adversarial R1-c238 — evento nunca perdido por crash do fit).
    %     [DI-09] snd = SondaState (data e SetAccess=protected: so aqui).
    sd  = load_sonda(problema, D, M, dataRoot);
    snd = [];
    if ~isempty(sd), snd = SondaState(sd, buf, fid, alg); end
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, 'snd', snd, ...
                  'logger', logger, ...
                  'run_id', string(nm_run_id(exp, alg, problema, semente)), ...
                  'problema', string(problema), 'semente', semente);
    Problem = UserProblem('evalFcn', batchEval, 'initFcn', @(N,varargin) X0(1:N,:), ...
        'D', D, 'lower', xl, 'upper', xu, 'maxFE', maxfe, ...
        'N', 100, 'once', true, 'data', data);         % maxRuntime fica inf (N.0.5)

    % (6) SEMENTE (D59): rng DEPOIS de construir o Problem, ANTES do Solve.
    rng(semente, 'twister');

    % (7) Algoritmo REAL: save=-K (sem .mat/figura — N.0.3/4), outputFcn=hook (②).
    %     EIM sem 'parameter': criterion default 'Euclidean' (EIMe).
    K = 20;
    algo = EIM('save', -K, ...
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
            fprintf(2, '[R1-c238 FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end

    % (7b) [DI-09] SONDA da ULTIMA iteracao — fora do laco, sobre o modelo ARMADO
    % no ultimo fit. [DI-19.5] usa g_armado: no c238 (overshoot ZERO) o buf.gen
    % pos-Solve aponta uma geracao NUNCA armada — o motivo da propria decisao.
    if ~isempty(snd), snd.finalProbe(); end

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
    man.algo_version = "c238-EIM-embrulho-N5";
    man.status = st_str;
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), snd);   % [§17.6/DI-09]
    man.params = struct('criterion', "Euclidean (EIMe)", ...
        'kriging', "OK-Forrester proprio (nao-DACE): mu constante, kernel gaussiano, ARD theta 1xD", ...
        'theta0', 1, 'theta_bounds', "[1e-3,1e3]", ...
        'mle', "fmincon sqp em log10(theta), single-start, MaxFunEvals=20D, tol 1e-20 (CODIGO)", ...
        'x_norm', "[0,1] pelos bounds (GP_Train)", 'nugget', "(10+n)*eps", ...
        'y_rescaling', "min-max por iteracao (PAPER §V-B(5)a) + guard max(range,eps) [IMPL]", ...
        'ga_interno', "pop=10D, 200 ger, torneio k=2, SBX dis_c=10 por-variavel (p=0.5), PM dis_m=20 pm=1/D, (mu+lambda) elitista -> 2000D aval-aquisicao/iter (CODIGO; paper: DE/rand/1/bin 50x50 F=0.8 CR=0.8 x4 — B10.2/D30, UNICA divergencia material)", ...
        'anti_clustering', "AUSENTE no repo (CODIGO — B10.7); telemetria min_dist_infill no jsonl", ...
        'init_maxfe', "global-override: 11D-1 (artefato) / 31D-1 (repo fixava 100/200)", ...
        'sem_dedup_infill', "duplicata = cache-hit 0 FE (D89), slot perdido (dup_infill); dedup SO no treino (guard chol [IMPL])", ...
        'embrulho', "classdef EIM < ALGORITHM (N.5, 8 pontos) — script oficial nao roda no harness");
    man.sigma_dict = struct( ...
        'mu_j', "media do kriging proprio (OK-Forrester) POR OBJETIVO, no ESPACO DO MODELO (y re-escalado min-max por iteracao — paper); cru = mu*range + min (transf_params)", ...
        'sigma_j', "s = sqrt(max(mse,0)) do GP_Predict STOCK por objetivo, no espaco re-escalado; a regua muda por iteracao — interpretar com transf_params", ...
        'transf_params', "{min, range} da iteracao (C3, leitura D47 — precedente e7: UMA linha por candidato no espaco do modelo); range = POS-guard max(range,eps)");
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
        fprintf(2, ['[R1-c238] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
end


function c238dir = ensure_paths_c238(ROOT)
% PlatEMO 4.15 (N.0.1: ALGORITHM/UserProblem/NDSort) + a pasta do c238 (repo
% STANDALONE do autor — o classdef EIM.m do embrulho N.5 vive nela).
%
% ⚠ VARREDURA DE SOMBRA (obrigatoria — licao R1-e7/S.8): os arquivos que o
% c238 CHAMA por path (GP_Train/GP_Predict/Infill_EIM/Optimizer_GA/Paretoset)
% sao UNICOS em algorithms/ (find 2026-07-17: nenhuma duplicata em outra
% arvore — sem sombra P/ DENTRO do c238). A sombra real e REVERSA: c238_EIM
% traz UniformPoint.m e DTLZ2.m que colidem com os do PlatEMO 4.15 — com a
% pasta prependada, um run posterior de b1/b3/e7/pisos no MESMO processo
% resolveria UniformPoint p/ a copia simplificada do Zhan (silencioso). O
% prepend + asserts abaixo garantem a precedencia DURANTE o run do c238; a
% REMOCAO ao fim do run e responsabilidade do onCleanup no run_c238.
    if isempty(which('UserProblem')) || isempty(which('OperatorGA'))
        pr = fullfile(ROOT, 'algorithms', '_PlatEMO', 'PlatEMO');
        if isfolder(pr), addpath(genpath(pr)); end
    end
    c238dir = fullfile(ROOT, 'algorithms', 'c238_EIM');
    if isempty(which('EIM')) || ~contains(which('GP_Train'), [filesep 'c238_EIM' filesep])
        assert(isfolder(c238dir), 'c238: pasta do repo ausente: %s', c238dir);
        addpath(c238dir);                      % prepend -> precedencia do c238
    end
    for fn = ["EIM","GP_Train","GP_Predict","Infill_EIM","Optimizer_GA","Paretoset"]
        assert(contains(which(char(fn)), [filesep 'c238_EIM' filesep]), ...
               'c238: %s nao resolve p/ a copia do c238_EIM (precedencia de path)', char(fn));
    end
end


function rmpath_quiet(d)
% Remove a pasta do path sem ruido (onCleanup do run_c238 — sombra reversa).
    w = warning('off', 'MATLAB:rmpath:DirNotFound');
    try, rmpath(d); catch, end
    warning(w);
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-e74 (CLMEA — arvore PlatEMO 4.1 PROPRIA, D95/N.0-4.1). O UNICO da R1 que
%  NAO roda na 4.15: a CLMEA_Code e um PlatEMO 4.1 COMPLETO (518 basenames
%  colidem com a 4.15, incluindo as CLASSES do nucleo ALGORITHM/PROBLEM/
%  SOLUTION/UserProblem) -> worker de PATH DEDICADO (ensure_paths_e74: rmpath
%  4.15 -> addpath genpath(CLMEA_Code) -> asserts which -> RESTAURACAO TOTAL
%  no onCleanup). Diferencas do contrato N.0-4.1 vs a receita N.0:
%   - UserProblem 4.1 NAO aceita 'once' (parser filtra em silencio): a ponte
%     avalia POR INDIVIDUO (e74_eval_one, 1xD por chamada; FE/hard-stop por
%     chamada no FEBudget — D89/D61 valem IGUAL).
%   - ALGORITHM 4.1 nao aceita 'run'/'metName' (so parameter/save/outputFcn).
%   - pro.FE=0 no Solve (ALGORITHM.m:74); FE+=n em UserProblem.m:84; o probe do
%     construtor (Initialization(1) -> initFcn=DoE[0]) e absorvido como
%     cache-hit no init em lote — receita N.0 do c217 intacta.
%  O que segue identico ao padrao run_c238: ponte, load_doe, FEBudget ANTES do
%  Problem, rng DEPOIS, save=-K + hook_output, try/catch PlatEMO:Termination,
%  export 4 camadas, CP-init, falha honesta.
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_e74(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();
    t0_run = tic;                                  % [§17.6] wall total do run

    % (0) ISOLAMENTO DE PATH (o risco nº1 do cartao): troca 4.15 -> 4.1 e arma a
    % restauracao TOTAL (run normal OU erro). O smoke `which -all` vai no header.
    [smoke, pathGuard] = ensure_paths_e74(ROOT); %#ok<ASGLU> % guard vive ate o fim do run

    % (1) PONTE + problema Python (bounds NATIVOS, minimiza — §5.5).
    ctx = bridge_ctx(ROOT);
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl(:).'; xu = pp.xu(:).';
    maxfe = 31*D - 1;  n_init = 11*D - 1;

    % (2) DoE 11D-1 do artefato (D63/D87) — CARREGADO, NUNCA regenerado.
    doe = load_doe(problema, semente, D, dataRoot);
    X0  = doe.X;
    assert(size(X0,1) == n_init, 'DoE tem %d linhas != 11D-1=%d', size(X0,1), n_init);
    assert(max(abs(xl(:)-doe.xl(:)))==0 && max(abs(xu(:)-doe.xu(:)))==0, ...
           'CP-bounds: bounds do problema != sidecar do DoE');

    % (3) .jsonl (§17.5) + wrapper de FE. bud ANTES do Problem (probe absorvido).
    jsonl  = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    fid    = jsonl_open(jsonl);
    logger = struct('guard', @(name, varargin) ...
                    jsonl_line(fid, 'guard', [{'name'}, {name}, varargin]));
    bud = FEBudget(D, maxfe, n_init, logger);
    buf = RunBuffer();
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "online", 'maxfe', maxfe, ...
        'doe_hash', string(doe.hash), 'algo', "e74-CLMEA-arvore-4.1-propria (D95/N.0-4.1)", ...
        'ponte', "POR INDIVIDUO (UserProblem 4.1 sem 'once' — N.0-4.1#1)", ...
        'params_balde_B', "num_infill=1, epsilon=1e-5, Gen_max1=200, Gen_max2=50, k_local=min(20,|Arc|) [defaults ParameterSet; sem 'parameter']", ...
        'N_estrategias', "min(100,|Arc|) p/ D<100 (L.8/D20; stock N=100/200)", ...
        'init', "11D-1 do artefato (desvio DELIBERADO do paper 100/200 — registrado)", ...
        'patches', "e74-mask (Local_infill:47 🔴) + e74-ndsort-obj (ClassifierSelect:9 🔴 — NDSort sobre OBJETIVOS reais dos pais via Data_Process) + mins L.8 (CLMEA:56/:66/:76) + D74 (CalHV normalizado, Hv_Select) + syncs D89; fix opcional re-sim do PNN NAO aplicado (telemetria n_desalinhado)", ...
        'd74', "CalHV interno: min-max do front-1 do arquivo corrente + ref 1,1 por coordenada (CalHV.m INTOCADO)", ...
        'divergencias_stock', "CR=1.0 no OperatorDE do Hv_Select:14 (nao-uniforme vs {0.5,0.5,1,20} das demais); DataProcess declara nome != arquivo Data_Process.m (funciona); breaks :62/:72/:82 mortos (NotTerminated lanca, nunca devolve false)", ...
        'sigma_dict', "sigma_0 POR ESTRATEGIA: s1=dist_dec (DECISAO) | s2=HV_gain (CalHV D74 - hv_base; so pseudo-front) | s3=Eucli (OBJETIVOS); mu=μ_RBF (s2 global/s3 local/boot obj-i); pred_classe=nivel_k do PNN (s1)", ...
        'which_smoke', jsonencode(smoke)});

    % (4) evalFcn POR INDIVIDUO (N.0-4.1): [dec,obj,con] por chamada 1xD, sob o
    % FEBudget (cache-hit=0 FE D89; hard-stop D61 propaga pelo CallFcn/addCause).
    evalFcnPerX = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));
    % [DI-09/DI-19.1] UM SondaState POR CABECA ('boot'/'s1'/'s2'/'s3' — o struct
    % que o e74_sonda espera). Motivo: o g do hook bumpa 4x POR CICLO (boot g=1;
    % ciclo c: s1=4c-2, s2=4c-1, s3=4c) — sob UM estado com k=2 o s2 (a RBF
    % global, a curva O(n^3) que a R4 quer) NUNCA dispararia.
    % CALIBRACAO (D-11, do implementador, ratificacao em lote D97): ROUND-ROBIN
    %   s1 k=6  -> c = 2,5,8,...   s2 k=3 -> c = 1,4,7,...   s3 k=12 -> c = 3,6,9,...
    % (aritmetica: mod(4c-2,6)==0 <=> c==2 mod 3; mod(4c-1,3)==0 <=> c==1 mod 3;
    %  mod(4c,12)==0 <=> c==0 mod 3). Cada ciclo sonda EXATAMENTE UMA cabeca e
    % cada cabeca e medida a cada 3 ciclos — volume ~1 bloco/ciclo (ZDT1 ~213
    % blocos ~430k linhas, vs 1,27M do k=1 nas tres). O boot dispara em g=1 pela
    % clausula da 1a (due(1) e true para qualquer k).
    sd  = load_sonda(problema, D, M, dataRoot);
    snd = [];
    if ~isempty(sd)
        snd = struct('boot', SondaState(sd, buf, fid, alg), ...
                     's1',   SondaState(sd, buf, fid, alg, 6), ...
                     's2',   SondaState(sd, buf, fid, alg, 3), ...
                     's3',   SondaState(sd, buf, fid, alg, 12));
    end
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, 'snd', snd, ...
                  'logger', logger, ...
                  'run_id', string(nm_run_id(exp, alg, problema, semente)), ...
                  'problema', string(problema), 'semente', semente);
    % SEM 'once' (o parser 4.1 o ignoraria em silencio) e SEM 'N' (o CLMEA usa o
    % proprio N=100/200 interno; o Problem.N default nao e consumido).
    Problem = UserProblem('evalFcn', @(x, varargin) e74_eval_one(x, bud, evalFcnPerX), ...
        'initFcn', @(N, varargin) X0(1:N,:), ...
        'D', D, 'lower', xl, 'upper', xu, 'maxFE', maxfe, ...
        'data', data);                                 % maxRuntime fica inf (N.0.5)

    % (5) SEMENTE (D59): rng DEPOIS de construir o Problem, ANTES do Solve.
    rng(semente, 'twister');

    % (6) CLMEA da arvore 4.1: save=-K + hook (②); sem 'parameter' (defaults =
    % Balde B). Termino normal E hard-stop = PlatEMO:Termination engolida.
    K = 20;
    algo = CLMEA('save', -K, ...
        'outputFcn', @(A,P) hook_output(A, P, buf, bud, []));
    term = "normal";
    try
        algo.Solve(Problem);
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination')
            term = "hard_stop";                        % nunca deveria vazar (Solve engole)
        else
            jsonl_line(fid, 'footer', {'status', "failed", 'erro', string(e.message), ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, '[R1-e74 FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end

    % (6b) [DI-09] SONDA da ULTIMA geracao de CADA CABECA — fora do laco, sobre
    % o modelo armado de cada handle (DI-19.1: sem isto duas das cabecas
    % perderiam o ponto final da curva). No-op por handle se ja sondada.
    if ~isempty(snd) && isstruct(snd)
        fns_snd = fieldnames(snd);
        for i_snd = 1:numel(fns_snd)
            snd.(fns_snd{i_snd}).finalProbe();
        end
    end

    % (7) EXPORT das 4 camadas (§17.2/§17.3).
    R = bud.records();
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (8) CP-init (D87/D88) + encanamento objetivo (D89/D21) + falha honesta.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);
    ok_flag = (bud.fe == maxfe) && cp_ok;
    st_str  = "ok"; if ~ok_flag, st_str = "failed"; end

    % (9) MANIFESTO (§17.2/§17.7) + dicionarios DEF-C4.
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    man.algo_version = "e74-CLMEA-arvore-4.1-propria";
    man.status = st_str;
    % [§17.6/DI-09] snd e um STRUCT de handles: o fill recebe [] e o bloco
    % man.sonda e montado por cabeca logo abaixo (o tempo total e a SOMA).
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), []);
    if ~isempty(snd) && isstruct(snd)
        heads = struct(); tps_total = 0;
        fns_man = fieldnames(snd);
        for i_man = 1:numel(fns_man)
            heads.(fns_man{i_man}) = snd.(fns_man{i_man}).manifestBlock();
            tps_total = tps_total + snd.(fns_man{i_man}).tempo_total_s;
        end
        man.timing.tempo_pred_sonda_s = tps_total;
        man.sonda = struct('status', "ok_multi_cabeca", 'regime', "online", ...
            'decisao', "[DI-19.1] um SondaState por cabeca; k round-robin s1=6, s2=3, s3=12 (cada cabeca a cada 3 ciclos, fase deslocada); boot 1x em g=1 (clausula da 1a)", ...
            'cabecas', heads);
    end
    man.params = struct( ...
        'arvore', "PlatEMO 4.1 propria (CLMEA_Code) — D95/N.0-4.1; worker de path dedicado (rmpath 4.15 -> addpath 4.1 -> restauracao total no onCleanup); ponte POR INDIVIDUO (sem 'once')", ...
        'parameter_set', "defaults do codigo: num_infill=1, epsilon=1e-5 (dedup, rejeita SEM FE — slot perdido), Gen_max1=200, Gen_max2=50, k_local=20 -> min(20,|Arc|) [L.8]", ...
        'N_estrategias', "stock 100 (D<100) / 200 (D>=100); nas 3 chamadas entra min(N,|Arc|) [L.8/D20 anti-crash D-baixo]", ...
        'init_maxfe', "global-override: DoE 11D-1 do artefato (desvio DELIBERADO do paper, init nativo 100/200) / 31D-1 hard-stop do wrapper", ...
        'bootstrap_extremos', "M FEs reais NO MAXIMO (extremos ACEITOS no dedup eps — e o metodo, Alg. 1; DE 100% no surrogate: NP=100+floor(D/10), F=CR=0.5, 20D gers, early-stop 50)", ...
        'spreads', "PNN spr=max(pdist2(X,X))/sqrt(2n); newrbe spr=dmax/(D*n)^(1/D) (interp exata, rede M-dim unica); classes PNN por camadas ND com quotas 10/30/40/20% (Data_Process)", ...
        'operador', "OperatorDE {0.5,0.5,1,20} (s1/s3/bootstrap); ⚠ s2/Hv_Select:14 usa {1,0.5,1,20} = CR=1.0 (nao-uniforme — CODIGO, registrado)", ...
        'd74_calhv', "CalHV interno NORMALIZADO: min-max do front-1 do arquivo corrente (Ymin/Ymax = ideal/nadir estimados, leitura D69) + ref 1,1 por coordenada; CalHV.m INTOCADO; range<=0 (front degenerado) NAO consertado — guard hv_range0", ...
        'patches_fidelidade', "🔴 e74-mask: Local_infill:47 -> x_offspring(index(Choose),:) [D76/ARTIGO]; 🔴 e74-ndsort-obj: ClassifierSelect:9 -> NDSort sobre os OBJETIVOS reais dos pais (y_obj_e74 do Data_Process, alinhado linha-a-linha) [D30/ARTIGO]", ...
        'fix_opcional_nao_aplicado', "desalinhamento mascara(Offspring)x linhas(Parent) no rank-learning (re-sim do PNN) — OPCIONAL no bundle, NAO aplicado (D81); telemetria n_desalinhado/flag_copia no .jsonl", ...
        'hazards_stock_registrados', "breaks :62/:72/:82 mortos (NotTerminated lanca PlatEMO:Termination, nunca devolve false — termino mid-ciclo via excecao); DataProcess declara nome != arquivo (resolucao por nome de arquivo); loop do rank-learning sem guarda alem de count>50; RefPoint/front degenerado = edge fora do paper (so logado)", ...
        'dlt', "Deep Learning Toolbox OBRIGATORIA (newrbe/newpnn/ind2vec/vec2ind/sim) + Statistics (pdist2)");
    man.sigma_dict = struct( ...
        'sigma_0', "pseudo-σ POR ESTRATEGIA (B16.4/DEF-C4; o e74 nao tem σ de modelo — RBF interp exata + PNN classe): s1 = dist_dec (dist minima em DECISAO ao arquivo — o criterio de selecao do rank-learning); s2 = HV_gain (score CalHV D74-normalizado do membro do pseudo-front MENOS hv_base do arquivo; NaN fora do front); s3 = Eucli/dist_obj (dist minima em OBJETIVOS ao arquivo — a incerteza geometrica da selecao local)", ...
        'mu_j', "μ_RBF (newrbe, interp exata): s2 = rede global (arquivo INTEIRO — o O(n^3)/iter); s3 = rede local (Nw vizinhos em OBJETIVOS do RefPoint); boot = so o objetivo i (rede do extremo i; demais NaN); s1 = NULL (PNN nao preve valor)", ...
        'pred_classe', "s1: nivel_k previsto/atribuido pelo PNN (classes 1..4 por camadas ND, quotas 10/30/40/20%)", ...
        'pred_score', "s2: score CalHV ABSOLUTO (D74-normalizado) do membro do pseudo-front (NaN fora)", ...
        'estrategia', "no modelo_flag: PNN(s1) | RBF-global(s2) | RBF-local(s3) | RBF-global(boot)");
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', st_str, 'fe_final', bud.fe, 'maxfe', maxfe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok, 'termino', string(term)});
    fclose(fid);

    % (10) Higiene de memoria da ponte (D86/N.0.8).
    try, py.gc.collect(); catch, end

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'n_geracoes', buf.nGeracoes(), ...
        'cache_hits', bud.cache_hits, 'termino', string(term), ...
        'doe_hash_run', string(doe_hash_run), ...
        'doe_hash_sidecar', string(doe.hash), 'cp_ok', cp_ok);
    if ~ok_flag
        fprintf(2, ['[R1-e74] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
    % O pathGuard (onCleanup) restaura o path AGORA, na saida da funcao: a 4.1
    % sai, a 4.15 (se estava) volta — prova de nao-contaminacao no cartao.
end


function [dec, obj, con] = e74_eval_one(x, bud, evalFcnPerX)
% Embrulho POR INDIVIDUO do evalFcn (N.0-4.1#1 — o UserProblem 4.1 nao tem
% 'once': Evaluation itera as linhas e chama o evalFcn com 1xD). Cada chamada
% passa pelo wrapper de FE (cache-hit=0 FE D89; a 31D-esima X inedita levanta
% PlatEMO:Termination NO MEIO do lote -> propaga pelo CallFcn (addCause preserva
% o identifier) -> Solve engole -> FE final EXATO — D61). dec = x (clamp
% autoritativo do wrapper); con = 0 (problema pymoo irrestrito).
    dec = double(x(:).');
    obj = bud.evaluate(dec, evalFcnPerX);   % 1xM; pode levantar PlatEMO:Termination
    con = 0;
end


function [smoke, guard] = ensure_paths_e74(ROOT)
% [R1-e74] Worker DEDICADO de path (D95/N.0-4.1#4 — o risco nº1 do projeto
% neste cartao): o processo que roda o e74 enxerga SO a arvore PlatEMO 4.1
% propria (CLMEA_Code). 518 basenames colidem com a _PlatEMO 4.15 — incluindo
% as CLASSES do nucleo (ALGORITHM, PROBLEM, SOLUTION, UserProblem) — e a
% coexistencia no mesmo path = corrupcao silenciosa. Estrategia:
%   1. prev = path (captura INTEGRAL do estado);
%   2. rmpath(genpath(_PlatEMO)) — TODA pasta da 4.15 sai do path;
%   3. addpath(genpath(CLMEA_Code)) — a arvore 4.1 INTEIRA (mesmo idioma do
%      platemo.m 4.1, que faz addpath(genpath(cd)));
%   4. asserts `which -all`: cada simbolo-chave resolve DENTRO da CLMEA_Code e
%      NENHUMA resolucao remanescente aponta p/ _PlatEMO (smoke devolvido ao
%      header do .jsonl — padrao e103/N.0-4.1#4);
%   5. guard = onCleanup(path(prev)): restauracao TOTAL na saida do run_e74
%      (normal OU erro) — a 4.1 sai, a 4.15 (se estava) volta; um run
%      subsequente de outro algoritmo NAO herda a 4.1 (nem vice-versa).
% src/ (FEBudget/RunBuffer/hook_output/e74_instrument) fica: zero colisao de
% basename com a CLMEA_Code (varredura 2026-07-18).
    prev = path;
    p415 = fullfile(ROOT, 'algorithms', '_PlatEMO');
    if isfolder(p415)
        w = warning('off', 'MATLAB:rmpath:DirNotFound');
        try, rmpath(genpath(p415)); catch, end
        warning(w);
    end
    e74root = fullfile(ROOT, 'algorithms', 'e74_CLMEA', 'CLMEA_Code');
    assert(isfolder(e74root), 'e74: arvore CLMEA_Code ausente: %s', e74root);
    addpath(genpath(e74root));
    guard = onCleanup(@() path(prev));
    % Toolboxes em runtime (cartao): DLT (newrbe/newpnn/ind2vec/vec2ind/sim) +
    % Statistics (pdist2).
    assert(~isempty(which('newrbe')) && ~isempty(which('newpnn')), ...
           'e74: Deep Learning Toolbox ausente (newrbe/newpnn)');
    assert(~isempty(which('pdist2')), 'e74: Statistics Toolbox ausente (pdist2)');
    smoke = struct();
    for fn = ["ALGORITHM","PROBLEM","SOLUTION","UserProblem","CLMEA", ...
              "OperatorDE","NDSort","UniformPoint","CalHV","SelectTrainData", ...
              "Local_infill","Hv_Select","ClassifierSelect","Data_Process","DE"]
        allw = which(char(fn), '-all');
        assert(~isempty(allw), 'e74: %s nao resolve no path', char(fn));
        assert(contains(allw{1}, [filesep 'CLMEA_Code' filesep]), ...
               'e74: %s resolve FORA da arvore 4.1: %s', char(fn), allw{1});
        n415 = sum(contains(allw, [filesep '_PlatEMO' filesep]));
        assert(n415 == 0, ...
               'e74: %s ainda tem %d resolucao(oes) na arvore 4.15 (sombra de path!)', ...
               char(fn), n415);
        smoke.(char(fn)) = string(allw{1});
    end
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-e103 (IBEA-MS — repo standalone do autor, OFFLINE — L.15/N.3/D90/D93).
%  O UNICO OFFLINE da R1 e o 2o worker de path dedicado (molde e74):
%   - REGIME OFFLINE: o orcamento E O DATASET. FEBudget(D, 31D-1, n_init=31D-1)
%     e as 31D-1 linhas do artefato D90 entram na carga (fase 'init'; o evalFcn
%     devolve o F DO ARTEFATO — a ponte NUNCA avalia). Saldo esgotado apos a
%     carga: qualquer X inedita na busca levanta PlatEMO:Termination, que aqui
%     NAO e termino normal — e VIOLACAO do regime (pára-e-loga, D81).
%   - ① = o dataset (31D-1 linhas, bit-exatas); CP-init offline = sha256 do X
%     E do F carregados == x_hash/f_hash do sidecar do ds (D88/D90).
%   - Wrapper L.15 no IBEAMS.m: (a) D/M/N/bounds do chamador (N=100);
%     (b) cd()->addpath puro; (c) Population = dataset injetado (MSE=zeros
%     marca "real"); (d) retorno [FinalDec,FinalObj]. Ancoras: pm 1/D (:43),
%     JudgeModel diagonal (:32), centros ceil(sqrt(n_dataset)) D93 (:4) +
%     inv->mldivide (:10).
%   - RNG (D59/D62): rng(semente,'twister') ANTES do IBEAMS (nao ha probe;
%     seeds.json _default — o harness NAO cria semente p/ o e103). Consumidores
%     do stream global: kmeans 1x no setup (k-means++ — a variancia entre
%     sementes do treino), TournamentSelection randi + GA rand/randi por ger.
%   - Instrumentacao (src/e103_instrument.m, read-only): ② membros do DATASET
%     na pop selecionada por geracao; ③ μ dos DOIS modelos (Kriging μ/σ +
%     RBFN_cal incondicional); e103_setup/e103_gen/e103_busca no .jsonl;
%     timing §17.6 = 1 linha (treino unico).
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_e103(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();
    t0_run = tic;                                  % [§17.6] wall total do run

    % (0) ISOLAMENTO DE PATH (hazard N.3 — "o mais perigoso sob parfor"):
    % worker dedicado; smoke `which -all` vai no header do .jsonl.
    [smoke, pathGuard] = ensure_paths_e103(ROOT); %#ok<ASGLU> % guard vive ate o fim do run

    % (1) PONTE: SO metadados (D/M/bounds — CP-bounds §5.5). ZERO avaliacao
    % real neste runner: o F vem exclusivamente do artefato D90.
    ctx = bridge_ctx(ROOT);
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl(:).'; xu = pp.xu(:).';

    % [T7-sweep] A CELULA do grid sai do token exp (`sweep-<tier>-<dist>`).
    % `off`/`main` => ('','') = o dataset PRINCIPAL (comportamento de sempre).
    % Sem isto um run de sweep lia o principal e gravava sob o nome do sweep —
    % erro SILENCIOSO (o CP-init passa: confere contra o arquivo que foi lido).
    [tier, dist] = nm_parse_sweep(exp);

    % (2) DATASET do artefato (D90) — CARREGADO, NUNCA regenerado.
    ds = load_dataset(problema, semente, D, M, dataRoot, tier, dist);
    % [T7] o orcamento E o dataset: o n vem do ARTEFATO, nunca de formula
    % (small=31D-1, medium=2000, big=50000 sao do doe.py — duplicar aqui criaria
    % 2 fontes da verdade). No principal a identidade 31D-1 segue sendo aferida.
    n_ds  = ds.n;
    maxfe = n_ds;
    if nm_is_main_variant(tier, dist)
        assert(n_ds == 31*D - 1, ...
               'dataset principal tem %d linhas != 31D-1=%d', n_ds, 31*D - 1);
    end
    % CP-bounds (§5.5): bounds do problema Python == sidecar do dataset.
    assert(max(abs(xl(:)-ds.xl(:)))==0 && max(abs(xu(:)-ds.xu(:)))==0, ...
           'CP-bounds: bounds do problema != sidecar do dataset');
    % Hazard L.15 (pára-e-loga ANTES): duplicata bit-a-bit no dataset e FATAL
    % no dacefit (repeated design sites) — e furaria a carga (cache-hit).
    assert(size(unique(ds.X, 'rows'), 1) == n_ds, ...
           'e103: dataset com linha duplicada (dacefit fatal — D81 pára-e-loga)');

    % (3) .jsonl (§17.5) + wrapper de FE: n_init = 31D-1 (TODO o dataset e
    % fase 'init' — CP-init offline sobre o dataset inteiro).
    jsonl  = nm_jsonl_path(exp, alg, problema, semente, dataRoot);
    fid    = jsonl_open(jsonl);
    logger = struct('guard', @(name, varargin) ...
                    jsonl_line(fid, 'guard', [{'name'}, {name}, varargin]));
    bud = FEBudget(D, maxfe, n_ds, logger);
    buf = RunBuffer();
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "offline", 'maxfe', maxfe, ...
        'dataset_hash', string(ds.dataset_hash), 'x_hash', string(ds.x_hash), ...
        'f_hash', string(ds.f_hash), 'n_dataset', n_ds, ...
        'algo', "e103-IBEAMS-offline-L15", ...
        'ponte', "metadata-only (D/M/bounds; ZERO avaliacao real — o F e o artefato D90)", ...
        'params_balde_B', "N=100, kappa=0.05, Generations=100 nominais (executa 99 — off-by-one CODIGO/B7.8), pm efetiva 1/D (proM=1 na :43), JudgeModel 3sigma+3sigma eps=1e-5 UF>=M-1 (diagonal i==j excluida)", ...
        'kriging', "DACE regpoly1+corrgauss, theta0=10, bounds [1e-3,1e3] (B7.7); 1 modelo/objetivo, treino UNICO (nunca retreina)", ...
        'rbfn', sprintf("1 rede multi-saida; centros k-means = ceil(sqrt(n_dataset)) = %d (D93, n INJETADO); spread 5*max(pdist(centros)) (kernel quase-plano — warnings esperados); pesos LSQ mldivide (inv-> \\)", ceil(sqrt(n_ds))), ...
        'patches', "L.15(a-d) no IBEAMS.m + ancoras e103-pm-D93a (:43) / e103-judgemodel (JudgeModel:32) / e103-centros-D93 (construct_Rnets:4) + inv->mldivide (:10)", ...
        'sigma_dict', "sigma_j = sqrt(max(MSE,0)) do predictor DACE POR OBJETIVO, SO nas linhas modelo_flag=Kriging-DACE da ③ (re-predicao read-only da pop selecionada); linhas RBFN sem sigma (RBF nao produz incerteza). No MECANISMO o MSE e gate booleano de ORDEM (JudgeModel) e MSE=0 marca membro REAL; o OffMSE=ones do ramo RBFN e MARCADOR, nao sigma. KFlag por geracao no e103_gen", ...
        'which_smoke', jsonencode(smoke)});

    % (4) CARGA do dataset no wrapper de FE: as 31D-1 avaliacoes DO DATASET
    % sao o orcamento inteiro (a ① nasce aqui, bit-exata ao artefato). O
    % evalFcn devolve o F da linha corrente do artefato — nenhuma ponte.
    for i = 1:n_ds
        fi = ds.F(i, :);
        bud.evaluate(ds.X(i, :), @(x) fi);
    end
    assert(bud.fe == maxfe && bud.cache_hits == 0, ...
           'e103: carga do dataset nao fechou 31D-1 distintas (fe=%d, hits=%d)', ...
           bud.fe, bud.cache_hits);
    jsonl_line(fid, 'decision', {'caminho', "carga_dataset", ...
        'motivo', sprintf('%d linhas do artefato D90 carregadas (orcamento esgotado; busca 100%% surrogate)', n_ds), ...
        'fe', bud.fe});

    % (4b) [DI-09/DI-13.5] SONDA OFFLINE: o artefato INTEIRO (S=20.000), 1 bloco
    % POR MODELO TREINADO (Kriging e RBFN => 2 blocos), geracao=NULL, disparado
    % pelo e103_instrument no case 'setup' via snd.probeOffline. Carregar AQUI
    % (antes do rng — a leitura de parquet nao consome RNG, mas a disciplina e a
    % mesma dos runs online: sonda carregada antes da semente).
    sd  = load_sonda(problema, D, M, dataRoot, 'offline');
    snd = [];
    if ~isempty(sd), snd = SondaState(sd, buf, fid, alg); end

    % (5) SEMENTE (D59): antes do IBEAMS — o 1o consumidor de RNG e o kmeans
    % do setup (k-means++); nao ha probe de construtor no e103 (standalone).
    rng(semente, 'twister');

    % (6) Global L.15 (o chamador parametriza D/M/N/bounds + injeta o dataset
    % e o n INJETADO da D93) + inst read-only. lastwarn limpo p/ o e103_setup
    % capturar a quase-singularidade esperada do treino.
    G = struct('D', D, 'M', M, 'N', 100, 'lower', xl, 'upper', xu, ...
               'n_dataset', n_ds, ...
               'data', struct('X0', ds.X, 'F0', ds.F), ...
               'inst', struct('buf', buf, 'bud', bud, 'fid', fid, 'snd', snd));
    lastwarn('');
    term = "normal";
    t0 = tic;
    try
        [FinalDec, FinalObj] = IBEAMS(G);
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination')
            % OFFLINE: nao existe termino por orcamento — se o hard-stop do
            % FEBudget disparou, ALGO TENTOU AVALIAR DE VERDADE na busca.
            % Violacao do regime (D90) -> pára-e-loga (D81), nunca engolir.
            jsonl_line(fid, 'footer', {'status', "failed", ...
                'erro', "FE real tentada durante a busca offline (violacao D90)", ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, ['[R1-e103 FAILED] %s/%s/%d: avaliacao real tentada na ' ...
                        'busca OFFLINE (violacao D90) — pára-e-loga (D81).\n'], ...
                    char(alg), char(problema), semente);
            rethrow(e);
        else
            jsonl_line(fid, 'footer', {'status', "failed", 'erro', string(e.message), ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, '[R1-e103 FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end
    tempo_total_alg = toc(t0);

    % (7) EXPORT das 4 camadas (§17.2/§17.3): ① = o DATASET; ②③/timing do buffer.
    R = bud.records();                                 % catalogo ① (== 31D-1 linhas)
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "offline", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (8) CP-init OFFLINE (D88/D90): X E F da ① bit-a-bit com o sidecar do ds.
    x_hash_run = sha256_rowmajor_f64(bud.init_X());
    f_hash_run = sha256_rowmajor_f64(vertcat(R.f));
    cp_ok = strcmp(x_hash_run, ds.x_hash) && strcmp(f_hash_run, ds.f_hash);
    ok_flag = (bud.fe == maxfe) && cp_ok;
    st_str  = "ok"; if ~ok_flag, st_str = "failed"; end

    % n_geracoes: derivado da ③ FILTRANDO regime=='sonda' [DI-19.3, decisao do
    % autor — SUBSTITUI a instrucao do cartao de derivar da ②]. Medido: a ②
    % offline so lista MEMBROS DO DATASET e no ZDT1 eles somem na g5 => a ②
    % daria 4 geracoes para um run que executa 99. E os blocos de sonda tem
    % geracao=NULL ([] nas srows) — sem o filtro, o cellfun quebraria e cada
    % NaN contaria como geracao distinta.
    if isempty(buf.srows)
        n_ger = 0;
    else
        eh_sonda_e103 = cellfun(@(r) isfield(r, 'regime') && ...
            ~ismissing(string(r.regime)) && string(r.regime) == "sonda", buf.srows);
        n_ger = numel(unique(cellfun(@(r) r.geracao, buf.srows(~eh_sonda_e103))));
    end

    % (9) MANIFESTO (§17.2/§17.7) + dicionarios DEF-C4.
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, n_ger, x_hash_run, bud.cache_hits, dataRoot);
    man.algo_version = "e103-IBEAMS-offline-L15";
    man.status = st_str;
    man.regime = "offline";
    % [T7-sweep -> DI-34] tier/dist do TOPO = a CELULA DO GRID (o token exp),
    % como no stack Python: NULL fora do sweep (o grid off tem tier/dist
    % vazios; gravar o 'small'/'lhs' do sidecar aqui divergia do runs_matrix
    % e do lado Python — achado da validacao final da torre). A proveniencia
    % do artefato LIDO permanece integral em man.dataset.tier/.dist.
    if strlength(string(tier)) > 0
        man.tier = string(tier);
        man.dist = string(dist);
    else
        man.tier = string(missing);    % jsonencode -> null (paridade Python)
        man.dist = string(missing);
    end
    man.dataset = struct('path', string(ds.path), 'n', n_ds, ...
        'tier', string(ds.tier), 'dist', string(ds.dist), ...
        'x_hash', string(ds.x_hash), 'f_hash', string(ds.f_hash), ...
        'dataset_hash', string(ds.dataset_hash), ...
        'cp_x', strcmp(x_hash_run, ds.x_hash), ...
        'cp_f', strcmp(f_hash_run, ds.f_hash));
    % [§17.6/DI-09] O bloco timing COMPLETO (nascia 4/5 NaN — so o total era
    % preenchido, e cobria SO o IBEAMS). tempo_total_s agora e o wall do RUN
    % (ponte + carga do dataset + busca + export), como o CONTRATO §4 define; o
    % wall SO da busca continua no jsonl (busca_fim) e no info.tempo_total_s.
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), snd);
    man.params = struct( ...
        'regime', "OFFLINE (D90): dataset 31D-1 injetado; ZERO FE real na busca; treino UNICO dos 2 modelos; 99 geracoes IBEA no surrogate", ...
        'N', 100, 'kappa', 0.05, ...
        'generations', "100 nominais -> 99 executadas (while CurGen<100 com CurGen=1 — off-by-one CODIGO, registrado)", ...
        'ibea', "I_eps+ (CalFitness normaliza min-max na pop corrente), kappa=0.05; TournamentSelection K=2; GA SBX disC=20 + PM disM=20", ...
        'pm', "proM=1 na chamada (:43) -> pm efetiva 1/D (GA.m:69 divide por D — convencao PlatEMO); stock passava 1/Global.D = 1/D^2 (🔴 ARTIGO, ancora e103-pm-D93a)", ...
        'judgemodel', "gate booleano de ORDEM par-a-par: |f_i-f_j| vs 3sqrt(MSE_i)+3sqrt(MSE_j), eps=1e-5, relaxacao UF>=M-1; diagonal i==j EXCLUIDA (🔴 ARTIGO, ancora e103-judgemodel — stock zerava o teste com qualquer MSE>0); KFlag STATELESS (re-testado por geracao — B7.8)", ...
        'kriging', "DACE dacefit(@regpoly1,@corrgauss), theta0=10*ones(1,D), bounds [1e-3,1e3] (B7.7); 1 modelo/objetivo; treino UNICO (offline — nunca retreina); AmendKriCal preserva o F REAL de quem tem MSE=0 (membros do dataset) e duplica ponto se N==1 (workaround stock)", ...
        'rbfn', "1 rede multi-saida: centros k-means (k-means++ — RNG do setup) = ceil(sqrt(n_dataset)) com o n INJETADO (D93 — ancora e103-centros-D93; stock usava 11D-1 do paper), spread = 5*max(pdist(centros)) (kernel quase-plano — warnings de quase-singularidade ESPERADOS, contados no e103_setup), pesos LSQ via mldivide (inv(Z'Z)Z' -> (Z'Z)\\(Z'PopObj) — §22-e103); kernel despachado por eval() de string (stock, registrado)", ...
        'off_mse_marcador', "no ramo RBFN o OffMSE=ones marca o offspring como 'surrogate' na geracao seguinte — MARCADOR de contabilidade, nao sigma (S.2-e103)", ...
        'rng', "rng(semente,'twister') unico ANTES do IBEAMS (D59; sem probe). Consumidores: kmeans 1x no setup (fonte de variancia entre sementes do treino), TournamentSelection randi + GA rand/randi por geracao. seeds.json _default: NENHUMA semente criada pelo harness (uso_id catalogo vazio p/ e103)", ...
        'watchdog', "guardas D60 de FE nao se aplicam (offline: zero FE na busca); rede = FEBudget esgotado (qualquer avaliacao nova -> PlatEMO:Termination = violacao, pára-e-loga)", ...
        'nd_final', "AVALIACAO REAL DO ND FINAL (§11/B7.5) NAO acontece neste run (a ① = SO o dataset; gate 31D-1): 'avaliado 1x FORA' — os decs finais estao na ③ (ultima geracao) e em FinalDec; DEFINICAO EM ABERTO p/ a torre: onde persiste (recomendacao: pos-hoc Python canonico, uniforme p/ todo o offline, antes do R3)", ...
        'divergencias_stock_mantidas', "off-by-one 99 ger; relaxacao M-1 (custa acuracia em M=2 — M.6/D73); spread 5*max(pdist) quase-plano; CalFitness com min==max -> NaN (hazard stock, nao consertado — falha honesta se disparar); AmendKriCal reordena a pop (dataset p/ o fim)");
    man.sigma_dict = struct( ...
        'mu_j', "μ do modelo da LINHA (modelo_flag): Kriging-DACE = predictor por objetivo; RBFN = RBFN_cal INCONDICIONAL (mesmo quando o Kriging liderou — C4/L.15, o 'μ dos DOIS modelos'). Re-predicao READ-ONLY sobre os decs da pop SELECIONADA por geracao (2 linhas/membro); membros do dataset inclusos (DACE interpola ≈exato, MSE≈0)", ...
        'sigma_j', "sqrt(max(MSE,0)) do predictor DACE por objetivo — SO nas linhas Kriging-DACE (guard mse_neg conta MSE<0 do erro float); linhas RBFN = NULL (RBF sem incerteza). NAO confundir com o papel do MSE no mecanismo: gate booleano de ORDEM (JudgeModel 3sigma) + marcador real/surrogate (0/1)", ...
        'kflag', "a decisao Kriging<->RBFN da geracao esta no .jsonl (e103_gen: kflag/modelo_lider) — nao ha coluna na ③; join por geracao");
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    % [DI-19.7] f_best do regime offline: o min do DATASET vai 1x aqui (e
    % constante — informacao de contexto); o f_best por geracao (pop-surrogate,
    % valores DE MODELO) sai no e103_gen do jsonl.
    jsonl_line(fid, 'f_best_dataset', {'f_best_dataset', min(ds.F, [], 1), ...
        'nota', "min por objetivo do DATASET (constante; DI-19.7) — o f_best por geracao e da pop-surrogate"});
    jsonl_line(fid, 'footer', {'status', st_str, 'fe_final', bud.fe, 'maxfe', maxfe, ...
        'n_geracoes', n_ger, 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok, 'cp_x', strcmp(x_hash_run, ds.x_hash), ...
        'cp_f', strcmp(f_hash_run, ds.f_hash), 'termino', string(term), ...
        'n_final', size(FinalDec, 1), 'tempo_total_s', tempo_total_alg});
    fclose(fid);

    % (10) Higiene de memoria da ponte (D86/N.0.8) — metadados apenas, mesmo assim.
    try, py.gc.collect(); catch, end

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_dataset', n_ds, 'n_geracoes', n_ger, 'cache_hits', bud.cache_hits, ...
        'termino', string(term), 'x_hash_run', string(x_hash_run), ...
        'f_hash_run', string(f_hash_run), 'cp_ok', cp_ok, ...
        'n_final', size(FinalDec, 1), 'final_obj_max', max(FinalObj(:)), ...
        'tempo_total_s', tempo_total_alg);
    if ~ok_flag
        fprintf(2, ['[R1-e103] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
    % O pathGuard (onCleanup) restaura o path na saida: o e103 sai, a 4.15
    % (se estava) volta — nada do e103 sombreia o proximo run do processo.
end


function [smoke, guard] = ensure_paths_e103(ROOT)
% [R1-e103] Worker DEDICADO de path (N.3 — "o mais perigoso sob parfor"): o
% processo que roda o e103 enxerga a arvore e103_IBEA-MS com PRECEDENCIA total
% e NENHUMA resolucao remanescente nas arvores grandes. Varredura de sombra
% (find por basename, 2026-07-18): CalFitness.m x62 e EnvironmentalSelection.m
% x155 na _PlatEMO 4.15; DACE inteiro (dacefit/predictor x29, regpoly*/corr*
% x2); GA.m (single-objective/GA) e TournamentSelection.m (Utility functions +
% CLMEA_Code 4.1) tambem colidem; dsmerge.m colide com c141/AB-SAEA. Zero
% colisao com src/*.m. Estrategia (molde ensure_paths_e74):
%   1. prev = path (captura INTEGRAL);
%   2. rmpath(genpath(_PlatEMO)) E rmpath(genpath(CLMEA_Code)) — as duas
%      arvores-gorila saem (no-op se ausentes);
%   3. addpath(genpath(e103_IBEA-MS)) POR ULTIMO — precedencia sobre qualquer
%      pasta remanescente de outro adapter (c141/c238 nao-removidas);
%   4. asserts `which -all` sobre TODOS os simbolos chamados: 1o hit DENTRO de
%      e103_IBEA-MS E zero resolucoes remanescentes em _PlatEMO/CLMEA_Code —
%      qualquer sombra ABORTA o run em vez de corromper em silencio; o smoke
%      vai no header do .jsonl;
%   5. guard = onCleanup(path(prev)): restauracao TOTAL na saida do run_e103
%      (normal OU erro). O proprio IBEAMS.m patchado (L.15b) faz um addpath
%      puro da propria arvore (sem cd) — redundante e coberto pela restauracao.
    prev = path;
    for tree = {fullfile(ROOT, 'algorithms', '_PlatEMO'), ...
                fullfile(ROOT, 'algorithms', 'e74_CLMEA', 'CLMEA_Code')}
        if isfolder(tree{1})
            w = warning('off', 'MATLAB:rmpath:DirNotFound');
            try, rmpath(genpath(tree{1})); catch, end
            warning(w);
        end
    end
    e103root = fullfile(ROOT, 'algorithms', 'e103_IBEA-MS');
    assert(isfolder(e103root), 'e103: arvore ausente: %s', e103root);
    addpath(genpath(e103root));
    guard = onCleanup(@() path(prev));
    % Toolbox em runtime (S.2-e103): Statistics (kmeans do get_center, pdist do
    % spread, pdist2 do the_gaussian). Sem Deep Learning aqui.
    assert(~isempty(which('kmeans')) && ~isempty(which('pdist')) ...
           && ~isempty(which('pdist2')), ...
           'e103: Statistics Toolbox ausente (kmeans/pdist/pdist2)');
    smoke = struct();
    for fn = ["IBEAMS","JudgeModel","construct_kriging","construct_Rnets", ...
              "kriging_cal","RBFN_cal","AmendKriCal","AmendRBFCal", ...
              "CalFitness","EnvironmentalSelection","Fitness","GA", ...
              "TournamentSelection","LHS_sam","PopStruct","decs","objs", ...
              "get_center","get_Z","the_gaussian", ...
              "dacefit","predictor","regpoly1","corrgauss","dsmerge"]
        allw = which(char(fn), '-all');
        assert(~isempty(allw), 'e103: %s nao resolve no path', char(fn));
        assert(contains(allw{1}, [filesep 'e103_IBEA-MS' filesep]), ...
               'e103: %s resolve FORA da arvore e103: %s', char(fn), allw{1});
        nout = sum(contains(allw, [filesep '_PlatEMO' filesep])) ...
             + sum(contains(allw, [filesep 'CLMEA_Code' filesep]));
        assert(nout == 0, ...
               'e103: %s ainda tem %d resolucao(oes) em _PlatEMO/CLMEA_Code (sombra de path!)', ...
               char(fn), nout);
        smoke.(char(fn)) = string(allw{1});
    end
end


% ════════════════════════════════════════════════════════════════════════════
%  RUN-PISO (os 4 PISOS ONLINE: NSGA-II, NSGA-III, MOEA/D type=1, SMS-EMOA) —
%  MOEAs STOCK do PlatEMO 4.15, SEM surrogate. Sao a REGUA do estudo (§3.2/D25):
%  respondem "o surrogate compra alguma coisa, afinal?". UM runner para os 4 —
%  eles diferem SO na classe PlatEMO e no 'parameter' (piso_spec).
%
%  O que os pisos herdam do caso-modelo c217 (receita N.0): ponte, load_doe,
%  FEBudget ANTES do Problem, rng DEPOIS do Problem, save=-K + outputFcn,
%  try/catch PlatEMO:Termination, export das 4 camadas, CP-init, falha honesta.
%
%  O que e ESPECIFICO deste cartao (e NAO existe nos 7 fan-outs anteriores):
%   (a) SEMEADURA §3.2/D88 — o piso e MOEA puro: nao tem arquivo de surrogate
%       para absorver as 11D-1 do DoE. O protocolo Knowles manda partir dos
%       MESMOS pontos, iniciando a evolucao com os MELHORES por nao-dominancia,
%       desempate por CROWDING DISTANCE deterministico (o criterio nativo do
%       NSGA-II) — dois runs da mesma semente escolhem o mesmo subconjunto.
%   (b) SEM SURROGATE => tabela ③ VAZIA + serie §17.6 VAZIA (bundle dos pisos);
%       o .jsonl e so o MINIMO COMUM (S.7, ultima linha) — sem pisos_instrument.
%   (c) SYNC D89 no hook (ver piso_hook) — aqui e OBRIGATORIO por um motivo a
%       mais que nos outros: o Solve ZERA pro.FE, mas o DoE ja foi gasto FORA
%       dele.
%  ZERO patch no PlatEMO: pisos nao tem patch de fidelidade POR DESIGN.
% ════════════════════════════════════════════════════════════════════════════

function [status, info] = run_piso(alg, problema, semente, exp, dataRoot)
    status = "failed";
    info = struct();
    ROOT = harness_root();
    t0_run = tic;                                  % [§17.6] wall total do run
    spec = piso_spec(alg);

    % Arvore PlatEMO 4.15 no path (N.0.1) — rede p/ chamada direta.
    ensure_paths_piso(ROOT, spec.classe);

    % (0) PONTE: repo-root no sys.path; importa src.* (A2/§2/§18).
    ctx = bridge_ctx(ROOT);

    % (1) Problema Python via ponte -> D, M, bounds NATIVOS (§5.5).
    pp = py_problem(ctx, problema);
    D = pp.D; M = pp.M; xl = pp.xl(:).'; xu = pp.xu(:).';
    maxfe = 31*D - 1;  n_init = 11*D - 1;

    % N = 20 CRAVADO (§3.2/§6.3/§6.4 + adendo D65, 2026-07-18). O piso se
    % calibra REDUZINDO a populacao (Knowles/ParEGO): geracoes = 20D ÷ N.
    % NSGA-III e MOEA/D reajustam N pelo lattice do UniformPoint (M=3, N=20 ->
    % 15) — o N EFETIVO e lido do Problem APOS o Solve e vai no manifesto
    % (precedente §6.3: "todos os N efetivos vao para a dissertacao").
    N_nominal = 20;

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
    bud = FEBudget(D, maxfe, n_init, logger);
    buf = RunBuffer();
    jsonl_line(fid, 'header', {'alg', string(alg), 'problema', string(problema), ...
        'semente', semente, 'D', D, 'M', M, 'regime', "online", 'maxfe', maxfe, ...
        'doe_hash', string(doe.hash), 'algo', spec.algo_version, ...
        'piso', true, 'surrogate', false, ...
        'principio', spec.principio, 'casamento', spec.casamento, ...
        'N_nominal', N_nominal, ...
        'N_origem', "20 CRAVADO 2026-07-18 (Knowles/ParEGO; ponto comum entre ~20-25 do §3.2 e {10,20,30,50} da D65; varredura SUB-varN reconfirma)", ...
        'seeding', "melhores N das 11D-1 do DoE por NDSort + CrowdingDistance (§3.2/D88, deterministico)", ...
        'operadores', "Balde C: SBX proC=1 dis_c=20 + PM proM=1 dis_m=20 (defaults OperatorGA do PlatEMO)"});
    % [DI-10] Os VETORES DE DECOMPOSICAO do moead/nsga3 no HEADER — sao
    % DETERMINISTICOS (UniformPoint(N,M)) e constantes no run, entao vao 1x, nao
    % por geracao. Sem eles a decisao "qual vetor guiou qual escolha" fica
    % inauditavel a jusante. NSGA-II e SMS-EMOA nao decompoem: nada a emitir.
    % [BL-14] `N_lattice` = o N EFETIVO da populacao, conhecido ANTES do Solve:
    % moead/nsga3 reajustam N pelo lattice do UniformPoint (M=3: 20 -> 15);
    % nsga2/smsemoa nao decompoem e ficam no nominal. `Problem.N` (o N_efetivo do
    % manifesto) so existe DEPOIS do Solve, e a flag de seeding e gravada antes.
    N_lattice = N_nominal;
    if any(strcmp(char(alg), {'moead','nsga3'}))
        [Wdec, Nlat] = UniformPoint(N_nominal, M);
        N_lattice = Nlat;
        jsonl_line(fid, 'decomposicao', {'alg', string(alg), ...
            'N_nominal', N_nominal, 'N_lattice', Nlat, 'M', M, ...
            'vetores', Wdec, ...
            'origem', "UniformPoint(N,M) do PlatEMO — deterministico, 1x por run", ...
            'nota', "o N EFETIVO do lattice pode diferir do nominal (M=3, 20 -> 15)"});
    end

    % (4) evalFcn por-x (a ponte, bounds nativos) + embrulho de LOTE (D61) — o
    %     c217_batch_eval e GENERICO (handoff R1-c217 §7): hard-stop no meio do lote.
    evalFcnPerX = @(x) double(ctx.prm.evaluate_problem(pp.obj, py.numpy.array(x)));
    batchEval   = @(X, varargin) c217_batch_eval(X, bud, evalFcnPerX);

    % (4b) ── SEMEADURA DOS PISOS (§3.2 + D88) — o passo NOVO deste cartao ────
    % Ordem obrigatoria (e a unica que fecha CP-init E orcamento ao mesmo tempo):
    %  1. PRE-AVALIA as 11D-1 do DoE pelo bud, NA ORDEM DO ARTEFATO -> fase
    %     'init' da ①, 11D-1 FE gastos, init_X() bit-identico ao artefato
    %     (CP-init D87/D88 fecha exatamente como nos outros 7 algoritmos).
    %  2. NDSort + CrowdingDistance sobre essas 11D-1 -> a ordem canonica do
    %     NSGA-II (frente asc, crowding desc; empate -> indice asc = estavel).
    %  3. O initFcn devolve os N primeiros -> o Solve os re-avalia como
    %     CACHE-HIT (0 FE, D89) => a evolucao fica com EXATAMENTE 20D.
    F0 = zeros(n_init, M);
    for i = 1:n_init
        F0(i,:) = bud.evaluate(X0(i,:), evalFcnPerX);
    end
    assert(bud.fe == n_init, ...
           'semeadura: DoE consumiu %d FE != 11D-1=%d', bud.fe, n_init);
    FrontNo  = NDSort(F0, n_init);
    CrowdDis = CrowdingDistance(F0, FrontNo);
    % -CrowdDis: Inf (extremos da frente) vira -Inf e sobe primeiro = crowding
    % DECRESCENTE. A 3a chave (indice) torna o desempate total e reprodutivel.
    [~, ord] = sortrows([FrontNo(:), -CrowdDis(:), (1:n_init).'], [1 2 3]);
    Xsel = X0(ord, :);
    jsonl_line(fid, 'seeding', {'n_doe', n_init, 'n_frentes', max(FrontNo), ...
        'n_frente1', sum(FrontNo == 1), 'N_nominal', N_nominal, ...
        ... % [BL-14] contra o N EFETIVO, nao o nominal: a D88 nomeia a clausula
        ... % "a frente-1 do DoE excede A POPULACAO", e a populacao do moead/nsga3
        ... % em M=3 e 15 (o proprio `initFcn` corta por ela). Medido nos 112 ⑥ da
        ... % s42: a flag antiga erra 4 celulas — moead e nsga3 em DTLZ1 (|F1|=17)
        ... % e DTLZ3 (|F1|=19), exatamente a faixa 16-20 que so existe com lattice.
        'frente1_excede_pop', sum(FrontNo == 1) > N_lattice, ...
        'criterio', "NDSort + CrowdingDistance (D88) — desempate final por indice"});

    % (5) UserProblem (contrato N.0/L.0): once=true (lote), bounds nativos, minimiza.
    %     initFcn devolve os N MELHORES (nao os N primeiros do artefato) — a
    %     diferenca em relacao aos 7 fan-outs anteriores. O probe do construtor
    %     (Initialization(1)) pega Xsel(1,:), que ja esta no cache => 0 FE.
    data = struct('X0', X0, 'buf', buf, 'bud', bud, 'log', fid, ...
                  'run_id', string(nm_run_id(exp, alg, problema, semente)), ...
                  'problema', string(problema), 'semente', semente);
    Problem = UserProblem('evalFcn', batchEval, ...
        'initFcn', @(N,varargin) piso_init(N, Xsel, n_init, logger), ...
        'D', D, 'lower', xl, 'upper', xu, 'maxFE', maxfe, ...
        'N', N_nominal, 'once', true, 'data', data);   % maxRuntime fica inf (N.0.5)

    % (6) SEMENTE (D59): rng DEPOIS de construir o Problem, ANTES do Solve.
    rng(semente, 'twister');

    % (7) Algoritmo REAL (STOCK): save=-K (sem .mat/figura — N.0.3/4) + hook.
    K = 20;
    % [DI09-R1c] tstate = relogio da geracao (containers.Map e HANDLE: a mutacao
    % dentro do hook persiste, sem `persistent`, que vazaria entre runs).
    tstate = containers.Map('KeyType', 'char', 'ValueType', 'any');
    tstate('t0') = tic;
    algo = feval(spec.classe, 'parameter', spec.parameter, 'save', -K, ...
        'outputFcn', @(A,P) piso_hook(A, P, buf, bud, fid, alg, tstate));
    term = "normal";
    try
        algo.Solve(Problem);                           % engole PlatEMO:Termination
    catch e
        if strcmp(e.identifier, 'PlatEMO:Termination')
            term = "hard_stop";
        else
            jsonl_line(fid, 'footer', {'status', "failed", 'erro', string(e.message), ...
                'identifier', string(e.identifier), 'fe_final', bud.fe});
            fclose(fid);
            fprintf(2, '[R1-pisos FAILED] %s/%s/%d: %s (%s)\n', ...
                    char(alg), char(problema), semente, e.message, e.identifier);
            rethrow(e);                                % erro REAL -> falha honesta (D23)
        end
    end
    N_efetivo = Problem.N;   % NSGA-III/MOEA-D reajustam pelo lattice (UniformPoint)

    % (8) EXPORT das 4 camadas (§17.2/§17.3): ① do wrapper; ② do buffer.
    %     ③ e timing sao VAZIAS por construcao (piso = sem surrogate) — o
    %     invariante e ASSERTADO, nao presumido.
    % [DI-13.7, decisao do autor] O invariante e sobre a camada ③ SO. A trava
    % original conferia TAMBEM `buf.trows` — mas o contrato AGORA EXIGE a ④ dos
    % pisos (§4/DI-13.2: `tempo_fit_s`=NULL, `tempo_geracao_s` normal, o
    % custo-baseline do estudo), entao a trava impedia o proprio contrato.
    if ~isempty(buf.srows)
        jsonl_line(fid, 'guard', {'name', "piso_com_surrogate", ...
            'n_srows', numel(buf.srows), ...
            'motivo', "piso nao deveria emitir a ③ (sem surrogate); a ④ E esperada"});
    end
    R = bud.records();                                 % catalogo ① (== 31D-1 linhas)
    write_real(exp, alg, problema, semente, R, D, M, dataRoot);
    write_pop(exp, alg, problema, semente, buf.pop, dataRoot);
    write_surrogate(exp, alg, problema, semente, buf.srows, D, M, "online", dataRoot);
    write_timing(exp, alg, problema, semente, buf.trows, dataRoot);

    % (9) CP-init por-run (D87/D88): hash da init X (float64) = sidecar do DoE.
    doe_hash_run = sha256_rowmajor_f64(bud.init_X());
    cp_ok = strcmp(doe_hash_run, doe.hash);

    % (10) Encanamento objetivo (D89/D21): FE final = 31D-1 EXATO E CP-init OK.
    ok_flag = (bud.fe == maxfe) && cp_ok;
    st_str  = "ok"; if ~ok_flag, st_str = "failed"; end

    % (11) MANIFESTO (§17.2/§17.7).
    man = build_manifest(exp, alg, problema, semente, ...
        maxfe, bud.fe, buf.nGeracoes(), doe_hash_run, bud.cache_hits, dataRoot);
    man.algo_version = spec.algo_version;
    man.status = st_str;
    man = fill_manifest_timing(man, buf.trows, bud, toc(t0_run), []);   % [§17.6]
    % [DI09-R1c] `fill_manifest_timing` com snd=[] grava man.sonda com status
    % 'artefato_ausente' — o que seria FALSO em dois sentidos no piso: o artefato
    % EXISTE (25/25 problemas do grid) e a ausencia de sonda aqui e por DESIGN,
    % nao por falta. Sobrescreve-se com a verdade.
    man.sonda = struct('status', "nao_se_aplica", ...
        'motivo', "piso ONLINE = MOEA puro, sem surrogate a sondar (CONTRATO §3.2)", ...
        'n_blocos', 0, 'n_linhas', 0);
    % [G-7] `sigma_dict` DECLARADO, nao omitido. O CONTRATO §5 o lista como
    % obrigatorio e a DEF-C4 o chama de "leitura OBRIGATORIA antes de usar a ③";
    % omiti-lo dava 112 celulas (28 x 4 pisos) sem a chave, e quem itera as
    % chaves do §5 nao distingue "nao se aplica" de "esqueceram". E o mesmo
    % argumento do `tempo_fit_s = NULL` da ④ (DI-13.2) e do bloco `sonda` acima:
    % declarar a nao-aplicabilidade e informacao; omitir e silencio.
    man.sigma_dict = struct('status', "nao_se_aplica", ...
        'motivo', "piso ONLINE = MOEA puro: a ③ existe (contrato de camadas) mas " + ...
                  "nasce VAZIA — nao ha modelo cujas colunas descrever", ...
        'terceira', "0 linhas por desenho (sem surrogate)");
    man.params = struct( ...
        'N_nominal', N_nominal, 'N_efetivo', N_efetivo, ...
        'N_decisao', "20 CRAVADO 2026-07-18 (§3.2 — Knowles/ParEGO; ponto comum ~20-25 x D65 {10,20,30,50}); SUB-varN reconfirma antes da bateria", ...
        'N_efetivo_nota', "NSGA-III/MOEA-D reajustam N pelo lattice do UniformPoint (M=3, 20 -> 15); NSGA-II/SMS-EMOA mantem o nominal. Precedente §6.3 (N=100 -> 91 vetores em M=3)", ...
        'seeding', "melhores N das 11D-1 do DoE por NDSort + CrowdingDistance, desempate final por indice (§3.2/D88) — os N entram como cache-hit (0 FE)", ...
        'geracoes_derivadas', "EMERGENTE, nao fechada [I-13/A24 corrigido " + ...
            "contra o dado em 2026-07-30]. O laco roda ate o hard-stop (31D-1 " + ...
            "FE EXATAS) gerando prole em PARES — 2*floor(N_efetivo/2) por " + ...
            "geracao (MatingPool do OperatorGA) — e cada duplicata bit-a-bit " + ...
            "(cache-hit D89, 0 FE) ADIA o fim. Melhor aproximacao MEDIDA: " + ...
            "floor((20D + n_dup) / (2*floor(N_efetivo/2))), que acerta 103/112 " + ...
            "celulas da s42; as 9 restantes erram por 1-2 porque o efeito de um " + ...
            "cache-hit depende de QUANDO ele cai, nao so de quantos sao. A " + ...
            "string antiga (""20D / N_efetivo"") acerta 2/112 e a formula " + ...
            "com ceil do plano F5 acerta 0/112. O valor REAL de cada run esta " + ...
            "em `n_geracoes`, neste mesmo manifesto — nao derive, LEIA.", ...
        'operadores', "Balde C: OperatorGA stock (SBX proC=1 dis_c=20; PM proM=1 dis_m=20)", ...
        'parameter', spec.parameter_desc, ...
        'surrogate', "NENHUM (piso = MOEA puro) -> tabela ③ vazia e serie §17.6 vazia", ...
        'patches', "NENHUM — piso e stock do PlatEMO 4.15 por design", ...
        'principio', spec.principio, 'casamento', spec.casamento);
    write_manifest(man, exp, alg, problema, semente, dataRoot);

    jsonl_line(fid, 'footer', {'status', st_str, 'fe_final', bud.fe, 'maxfe', maxfe, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'cp_init', cp_ok, 'termino', string(term), ...
        'N_nominal', N_nominal, 'N_efetivo', N_efetivo});
    fclose(fid);

    % (12) Higiene de memoria da ponte (D86/N.0.8): solta o Problem pymoo do run.
    try, py.gc.collect(); catch, end

    info = struct('D', D, 'M', M, 'maxfe', maxfe, 'fe_final', bud.fe, ...
        'n_init', n_init, 'N_nominal', N_nominal, 'N_efetivo', N_efetivo, ...
        'n_geracoes', buf.nGeracoes(), 'cache_hits', bud.cache_hits, ...
        'termino', string(term), 'doe_hash_run', string(doe_hash_run), ...
        'doe_hash_sidecar', string(doe.hash), 'cp_ok', cp_ok);
    if ~ok_flag
        fprintf(2, ['[R1-pisos] FALHA HONESTA (D81): FE_final=%d (31D-1=%d) cp_init=%d ' ...
                    '-> manifesto status=failed.\n'], bud.fe, maxfe, cp_ok);
    end
    status = st_str;
end


function spec = piso_spec(alg)
% Os 4 pisos diferem SO na classe PlatEMO e no 'parameter'. O casamento
% piso -> principio de selecao e o §3.2/D25 (da a atribuicao limpa do ganho
% ao surrogate: cada piso espelha o MECANISMO de uma familia de SA-MOEA).
    spec = struct();
    switch char(alg)
        case 'nsga2'
            spec.classe        = 'NSGAII';
            spec.parameter     = {};        % NSGA-II nao tem ParameterSet
            spec.parameter_desc= "nenhum (NSGA-II stock nao expoe parametro)";
            spec.algo_version  = "piso-NSGAII-PlatEMO4.15";
            spec.principio     = "dominancia/Pareto";
            spec.casamento     = "EA-Dominancia (b4, c217, c141, e74) + BO-Melhoria-de-Pareto (c238) — §3.2";
        case 'nsga3'
            spec.classe        = 'NSGAIII';
            spec.parameter     = {};        % NSGA-III nao tem ParameterSet
            spec.parameter_desc= "nenhum (NSGA-III stock nao expoe parametro); N vira |Z| do UniformPoint";
            spec.algo_version  = "piso-NSGAIII-PlatEMO4.15";
            spec.principio     = "referencia/indicador";
            spec.casamento     = "EA-Indicador (e7) — §3.2";
        case 'moead'
            % S.2#19: MOEAD.m:22 `type = ParameterSet(1)` ja e 1 (PBI), mas o
            % contrato manda FIXAR EXPLICITAMENTE e registrar no manifesto.
            spec.classe        = 'MOEAD';
            spec.parameter     = {1};
            spec.parameter_desc= "type=1 (PBI, theta~5) FIXADO EXPLICITAMENTE (S.2#19; coincide com o default do codigo)";
            spec.algo_version  = "piso-MOEAD-PlatEMO4.15-type1-PBI";
            spec.principio     = "decomposicao";
            spec.casamento     = "EA-Decomposicao (b3, c122) + BO-Decomposicao (b1) — §3.2";
        case 'smsemoa'
            % SMS-EMOA PURO (nao o SMS-EMOA-MA, que e variante surrogate — §3.6).
            spec.classe        = 'SMSEMOA';
            spec.parameter     = {};
            spec.parameter_desc= "nenhum (SMS-EMOA PURO stock — nao e o SMS-EMOA-MA surrogate do §3.6)";
            spec.algo_version  = "piso-SMSEMOA-PlatEMO4.15";
            spec.principio     = "contribuicao de hipervolume (S-metric)";
            spec.casamento     = "BO-Hipervolume (c262 qNEHVI) — espelho mecanico exato, D25/§3.2";
        otherwise
            error('piso_spec:desconhecido', 'piso desconhecido: %s', char(alg));
    end
end


function Xi = piso_init(N, Xsel, n_init, logger)
% initFcn dos pisos: os N MELHORES do DoE (ja ordenados por NDSort+crowding).
% Os N sao re-avaliados pelo Solve e batem no cache => 0 FE (D89).
% Teto anti-crash (§6.3, "tetos de seguranca sao implementacao obrigatoria"):
% a populacao nao pode exceder o DoE. Com N=20 e n_init>=21 (D>=2) isto NUNCA
% dispara; se disparar, LOGA e deixa o UserProblem falhar honestamente na
% checagem de forma [N D] (D81 — nunca silencioso).
    if N > n_init
        logger.guard('piso_pop_excede_doe', 'N_pedido', N, 'n_init', n_init, ...
            'motivo', 'populacao do piso > 11D-1 do DoE (teto anti-crash §6.3)');
    end
    Xi = Xsel(1:min(N, n_init), :);
end


function piso_hook(Algorithm, Problem, buf, bud, fid, alg, tstate)
% Hook dos pisos = sync D89 + o hook transversal (② por geracao).
%
% ⚠ O SYNC E OBRIGATORIO AQUI, e por um motivo A MAIS que nos outros runners:
%   (a) [comum] o obj.FE nativo soma cache-hits e correria a frente do saldo
%       DISTINTO do wrapper a primeira duplicata de offspring (o achado do
%       c217: ZDT1 fechava 926 em vez de 929);
%   (b) [ESPECIFICO DO PISO] `ALGORITHM.Solve` ZERA pro.FE (:80), mas as 11D-1
%       do DoE foram gastas ANTES do Solve (semeadura §3.2) -> sem o sync o
%       NotTerminated enxergaria so as 20D da evolucao e o `rate` do save=-K
%       ficaria completamente fora de escala.
% Posicao: ALGORITHM.m:126 chama o outputFcn ANTES da checagem :127
% (`nofinish = pro.FE < pro.maxFE`), entao sincronizar aqui e lido no MESMO
% ciclo — o hard-stop real segue sendo o throw do bud (D61), este e o caminho
% de termino limpo.
    Problem.FE = bud.fe;

    % [DI09-R1c] §17.6: a ④ do piso deixou de ser VAZIA — ela e o CUSTO-BASELINE
    % do estudo (CONTRATO §4 + DI-13.2). Como os pisos sao STOCK (zero patch por
    % design), nao ha onde por um `tic` dentro do algoritmo: o wall da geracao
    % sai do DELTA entre chamadas consecutivas deste hook, que o PlatEMO invoca
    % 1x por geracao (ALGORITHM.m:126). `tstate` e um containers.Map (handle) do
    % run_piso — e o que permite guardar o instante anterior sem `persistent`
    % (que vazaria entre runs no mesmo processo MATLAB).
    tger_s = NaN;
    if nargin >= 7 && ~isempty(tstate)
        try
            if isKey(tstate, 't0'), tger_s = toc(tstate('t0')); end
            tstate('t0') = tic;
        catch
        end
    end
    % tempo_fit_s AUSENTE => NULL (piso nao treina — DI-13.2).
    % tempo_busca_s / tempo_pred_sonda_s = NaN => NULL, nao 0: "nao se aplica"
    % e "nao medido" nao sao "custou zero" (ver o cabecalho do piso_instrument).
    timing = struct('tempo_geracao_s', tger_s, ...
                    'tempo_busca_s', NaN, 'tempo_pred_sonda_s', NaN);
    hook_output(Algorithm, Problem, buf, bud, timing);

    if nargin >= 6
        piso_instrument(Algorithm, Problem, buf, bud, fid, alg, tger_s);
    end
end


function ensure_paths_piso(ROOT, classe)
% addpath(genpath) da arvore PlatEMO 4.15 (N.0.1: Utility functions/ nao entra
% pelo Solve). Os 4 pisos sao built-ins da arvore — nenhuma pasta externa, logo
% nenhuma sombra de path a varrer PARA DENTRO. A varredura de sombra REVERSA
% (c238_EIM traz UniformPoint.m/DTLZ2.m proprios) e neutralizada pelo onCleanup
% do run_c238, que remove aquela pasta do path ao fim do run.
    if isempty(which(classe)) || isempty(which('UserProblem')) || ...
       isempty(which('OperatorGA')) || isempty(which('CrowdingDistance'))
        pr = fullfile(ROOT, 'algorithms', '_PlatEMO', 'PlatEMO');
        if isfolder(pr), addpath(genpath(pr)); end
    end
    % Assert de precedencia: o piso TEM de resolver para a arvore 4.15.
    for fn = string({classe, 'UniformPoint', 'NDSort', 'CrowdingDistance', 'OperatorGA'})
        w = which(char(fn));
        assert(~isempty(w) && contains(w, [filesep '_PlatEMO' filesep]), ...
            'piso: %s nao resolve p/ a arvore _PlatEMO 4.15 (which=%s)', ...
            char(fn), w);
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
%  DATASET OFFLINE (D90) — carregado do artefato, NUNCA regenerado ([R1-e103])
% ════════════════════════════════════════════════════════════════════════════

function ds = load_dataset(problema, semente, D, M, dataRoot, tier, dist)
% Dataset offline (D90): X (n x D) + F (n x M) float64 na ordem do sidecar, +
% os 3 hashes do array decodificado (x_hash / f_hash / dataset_hash) p/ o
% CP-init offline. [T7-sweep] `tier`/`dist` selecionam a VARIANTE do sweep;
% omitidos (ou small/lhs) => o offline PRINCIPAL, nome SEM sufixo.
%
% ⚠ O `n` NAO e' derivado de formula: sai do artefato (espelho do Python, que
% monta FEBudget(maxfe=n) com o n lido). Assim medium=2000/big=50000 nunca
% viram constante duplicada neste arquivo.
    if nargin < 6, tier = ''; end
    if nargin < 7, dist = ''; end
    pq  = nm_dataset_path(problema, semente, dataRoot, tier, dist);
    man = nm_dataset_manifest_path(problema, semente, dataRoot, tier, dist);
    assert(isfile(pq),  'dataset ausente: %s', pq);
    assert(isfile(man), 'sidecar do dataset ausente: %s', man);
    side = jsondecode(fileread(man));
    % [T7] Confere contra o que foi PEDIDO (antes: exigia small/lhs sempre, o
    % que fazia TODA variante do sweep abortar). O principal declara
    % tier='small'/dist='lhs' no proprio sidecar.
    if nm_is_main_variant(tier, dist)
        tier_q = 'small'; dist_q = 'lhs';
    else
        tier_q = char(tier); dist_q = char(dist);
    end
    assert(strcmp(char(side.tier), tier_q) && strcmp(char(side.dist), dist_q), ...
           'dataset %s: sidecar diz tier=%s/dist=%s, pedido tier=%s/dist=%s', ...
           pq, side.tier, side.dist, tier_q, dist_q);
    cols  = cellstr(side.columns);                 % {'x0',...,'f0',...} na ordem
    xcols = cols(startsWith(cols, 'x'));
    fcols = cols(startsWith(cols, 'f'));
    assert(numel(xcols) == D, 'dataset tem %d colunas x != D=%d', numel(xcols), D);
    assert(numel(fcols) == M, 'dataset tem %d colunas f != M=%d', numel(fcols), M);
    t = parquetread(pq);
    ds.X = double(t{:, xcols});                    % n x D (float64, nativo)
    ds.F = double(t{:, fcols});                    % n x M (float64)
    ds.x_hash = char(side.x_hash);
    ds.f_hash = char(side.f_hash);
    ds.dataset_hash = char(side.dataset_hash);
    ds.xl = double(side.bounds.xl);
    ds.xu = double(side.bounds.xu);
    ds.path = pq;
    ds.tier = char(side.tier);          % [T7] o que o ARTEFATO declara
    ds.dist = char(side.dist);
    ds.n    = size(ds.X, 1);            % [T7] o n VEM DO ARTEFATO, nao de formula
end


% ════════════════════════════════════════════════════════════════════════════
%  SONDA CANONICA (DI-09 / §17.2.2) — carregada do artefato, NUNCA gerada
% ════════════════════════════════════════════════════════════════════════════

function sd = load_sonda(problema, D, M, dataRoot, regime)
% Os pontos FIXOS do problema (os MESMOS p/ todos os algoritmos, geracoes e
% sementes — §17.2.2). Molde do load_dataset (D90): le o artefato, confere o CP
% no ARRANQUE e ABORTA em divergencia (disciplina D63/D87).
%
% [DI-13.5, autor 2026-07-19] O artefato tem S=20.000 e serve aos DOIS regimes:
%   regime='online'  (default) -> le as PRIMEIRAS side.S_online (2.000), a cada
%                                 k=2 geracoes;
%   regime='offline'           -> le TODAS as 20.000, UMA vez por modelo treinado
%                                 (o modelo e fixo; sem repeticao geracao-a-geracao
%                                 cabe MUITO mais ponto pela mesma analise).
% Sobol e ANINHADO (provado): a fatia online e BIT-IDENTICA a uma sonda gerada
% com 2.000 -> a regua e a MESMA nos dois regimes na faixa compartilhada, e os
% runs online ja retrofitados NAO precisam ser refeitos.
%
%   sd.X (S x D, float64, bounds NATIVOS)  -> o que se prediz
%   sd.F (S x M, float64)                  -> o GABARITO; NAO vai para a ③
%                                             (§3.1: join por POSICAO)
%   sd.x_hash / sd.f_hash / sd.S
%
% Custo de FE: ZERO — a sonda nunca chama o avaliador real (exceção contabil
% documentada, precedente do __final DI-08).
    if nargin < 5 || isempty(regime), regime = 'online'; end
    pq  = nm_sonda_path(problema, dataRoot);
    man = nm_sonda_manifest_path(problema, dataRoot);

    % [DI-09] O artefato cobre EXATAMENTE os 25 problemas do grid oficial
    % (runs_matrix.csv) — verificado: 25/25. Problemas de PILOTO fora do grid
    % (ex.: DTLZ2_d15, variante dimensional usada so nas checagens de D) NAO
    % tem regua, e nao podem ter: a sonda e Sobol com d=D, entao a variante
    % precisaria de artefato PROPRIO. Nesses casos o run segue SEM sonda — mas
    % o fato fica registrado de forma inconfundivel (o chamador grava
    % man.sonda.status='artefato_ausente' + evento no jsonl), para que "sonda
    % ausente" nunca possa ser confundido com "sonda vazia".
    if ~isfile(pq) || ~isfile(man)
        sd = [];
        warning('experiment:sondaAusente', ...
            ['sonda ausente para o problema %s (%s) — o run segue SEM sonda. ' ...
             'Esperado apenas em problemas FORA do grid dos 25 (piloto).'], ...
            char(problema), pq);
        return;
    end
    side = jsondecode(fileread(man));

    t = parquetread(pq);
    cols  = string(t.Properties.VariableNames);
    % 'sonda_id' NAO casa com os prefixos x/f — a ordem das colunas do artefato
    % e (sonda_id, x0..x{D-1}, f0..f{M-1}), gerada por scripts/gen_sonda.py.
    xcols = cols(startsWith(cols, "x"));
    fcols = cols(startsWith(cols, "f"));
    assert(numel(xcols) == D, 'sonda tem %d colunas x != D=%d', numel(xcols), D);
    assert(numel(fcols) == M, 'sonda tem %d colunas f != M=%d', numel(fcols), M);

    sd.X = double(t{:, cellstr(xcols)});
    sd.F = double(t{:, cellstr(fcols)});
    sd.S = size(sd.X, 1);
    assert(sd.S == double(side.S), 'sonda: S=%d != sidecar %d', sd.S, double(side.S));

    % ── [DI-13.5] fatia por REGIME (ver o cabecalho) ──────────────────────────
    sd.regime = char(regime);
    if strcmpi(regime, 'online')
        nOn = 2000;
        if isfield(side, 'S_online'), nOn = double(side.S_online); end
        sd.X = sd.X(1:nOn, :);
        sd.F = sd.F(1:nOn, :);
        sd.S = nOn;
    end

    % ── CP da sonda (o gate do arranque): sha256 dos bytes float64 row-major ──
    if strcmpi(sd.regime, 'online') && isfield(side, 'x_hash_online')
        sd.x_hash = char(side.x_hash_online);   % o CP da FATIA online
        sd.f_hash = char(side.f_hash_online);
    else
        sd.x_hash = char(side.x_hash);          % o CP do artefato INTEIRO
        sd.f_hash = char(side.f_hash);
    end
    h = sha256_rowmajor_f64(sd.X);
    assert(strcmp(h, sd.x_hash), ...
        'sonda:x_hash DIVERGENTE em %s\n  artefato: %s\n  sidecar : %s', ...
        pq, h, sd.x_hash);
    sd.path = pq;
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
    GER = NaN(n, 1);            % [DI-13.5] NaN = NULL (bloco de sonda offline)
    X   = zeros(n, D);
    RSI = NaN(n, 1);
    MU  = NaN(n, M);  SG = NaN(n, M);
    PS  = NaN(n, 1);  PCONF = NaN(n, 1);
    FTM = NaN(n, 1);                                  % [DI-09/A1] fe_treino_max
    REG = repmat(string(regime), n, 1);               % [DI-09] regime POR LINHA
    tipo   = repmat(string(missing), n, 1);
    classe = repmat(string(missing), n, 1);
    modelo = repmat(string(missing), n, 1);
    espaco = repmat(string(missing), n, 1);
    ttipo  = repmat(string(missing), n, 1);
    tpar   = repmat(string(missing), n, 1);
    for k = 1:n
        r = srows{k};
        if ~isempty(r.geracao), GER(k) = r.geracao; end   % [DI-13.5] vazio => NULL
        X(k, :) = r.x;
        if ~isempty(r.real_solution_id), RSI(k) = double(r.real_solution_id); end
        % [DI-09] regime/fe_treino_max: lidos com field_or — as linhas legadas
        % (montadas antes do retrofit) nao carregam os campos; o argumento
        % `regime` da funcao segue valendo como DEFAULT da linha. Espelha a
        % politica do src/export.py::write_surrogate (regime por linha c/ fallback).
        v = field_or(r, 'regime');
        if ~isempty(v) && ~ismissing(string(v)), REG(k) = string(v); end
        v = field_or(r, 'fe_treino_max');
        if ~(isempty(v) || (isnumeric(v) && isnan(v))), FTM(k) = double(v); end
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
    T.regime    = REG;                    % [DI-09] por linha ('sonda' x busca)
    % [DI-13.5 · adendo da torre] `geracao` e NULLABLE: os blocos de sonda do
    % regime OFFLINE gravam geracao=NULL (o modelo treina ANTES do laco — nao ha
    % geracao a que pertencer). MATLAB nao expressa int32-NULL: `int32(NaN)` = 0,
    % o que faria o bloco offline virar silenciosamente "geracao 0". Aplica-se o
    % MESMO idioma ja usado no `n_acumulado` da ④ (write_timing) e no
    % `real_solution_id` abaixo: mantem-se double (NaN => NULL no parquet) se
    % houver QUALQUER ausente; so casta p/ int32 quando a coluna esta completa.
    % BIT-NEUTRO para todos os configs ONLINE — sem NaN, o branch escolhe int32
    % exatamente como antes. (O lado Python ja foi corrigido pela torre.)
    if all(~isnan(GER))
        T.geracao = int32(GER);
    else
        T.geracao = GER;             % double com NaN => NULL
    end
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
    % [DI-09/A1] fe_treino_max: maior fe_index no TREINO do modelo no momento do
    % fit — o marcador que separa in-sample de out-of-sample na R4 (§9). MESMO
    % branch int32/double-NaN do real_solution_id (o MATLAB nao expressa
    % int32-NULL; a consolidacao Python re-casta p/ int32 nullable).
    if all(~isnan(FTM))
        T.fe_treino_max = int32(FTM);
    else
        T.fe_treino_max = FTM;
    end
    p = nm_layer_path(exp, alg, problema, semente, 'surrogate', dataRoot);
    atomic_parquet(p, T);
end

function p = write_timing(exp, alg, problema, semente, trows, dataRoot)
    % Camada de tempo §17.6 (pos-retrofit DI-09): run_id, geracao, n_acumulado,
    % tempo_fit_s, tempo_busca_s (OBRIGATORIO), tempo_pred_sonda_s, tempo_geracao_s.
    %
    % [DI-09] TODO campo e lido por field_or/opt_scal: uma linha de timing sem
    % retreino (so `tempo_geracao_s`) ou sem sonda e legitima pos-retrofit, e o
    % acesso direto `trows{k}.<campo>` derrubava o export inteiro no fim do run.
    n = numel(trows);
    rid = nm_run_id(exp, alg, problema, semente);
    tcol = @(f) single(arrayfun(@(k) opt_scal(field_or(trows{k}, f)), (1:n).'));
    icol = @(f) arrayfun(@(k) double(opt_scal(field_or(trows{k}, f))), (1:n).');
    T = table();
    T.run_id       = repmat(string(rid), n, 1);
    T.geracao      = int32(icol('geracao'));
    % n_acumulado indefinido numa linha SEM retreino (so wall da geracao): cai
    % p/ double+NaN em vez de virar int32(NaN)=0, que se leria como "treinou
    % com 0 pontos" e envenenaria a curva de escalabilidade (§17.6).
    NAC = icol('n_acumulado');
    if all(~isnan(NAC)), T.n_acumulado = int32(NAC); else, T.n_acumulado = NAC; end
    T.tempo_fit_s        = tcol('tempo_fit_s');
    T.tempo_busca_s      = tcol('tempo_busca_s');
    T.tempo_pred_sonda_s = tcol('tempo_pred_sonda_s');   % [DI-09] 0 quando nao roda
    T.tempo_geracao_s    = tcol('tempo_geracao_s');      % [v5.2.1] wall da geracao
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
    % [B-03] schema v2 = com `campanha_id`. O carimbo distingue celula DA
    % CAMPANHA de celula de smoke/pre-retrofit: sem ele, `is_run_done` absorvia
    % as stale de semente 0 como prontas — e a semente 0 e uma das 30.
    man.schema_version = 2;
    man.campanha_id = string(campanha_id_corrente());
    man.run_id = string(rid);
    man.exp = string(exp); man.alg = string(alg);
    man.problema = string(problema); man.semente = semente;
    man.regime = "online"; man.q = 1; man.tier = ""; man.dist = "";
    man.status = "ok"; man.n_retries = 0; man.stack_trace = "";
    man.maxfe = maxfe; man.fe_final = fe_final; man.n_geracoes = n_ger;
    man.doe_hash = string(doe_hash);
    % [I-09] o elo D80 run<->codigo: era "" em 666/666 celulas da rodada-42,
    % transversal aos 13 configs MATLAB. Sem ele, ~10.350 celulas/campanha ficam
    % sem dizer QUAL codigo as produziu — e e esse elo que sustenta todo o
    % aspecto declarativo (pins, patches, ancoras).
    man.repo_hash = string(repo_hash_corrente());
    man.algo_version = "stub-R1-00";
    % [C2/BL-07] `host`/`plataforma`: a MAQUINA viaja com o dado. Ate aqui nao
    % viajava — a unica atribuicao era a coluna `maquina_dona` do censo,
    % DERIVADA do roster planejado, que rotula errado toda celula recuperada
    % noutra maquina. Com a campanha alocada POR SEMENTE (as 30 repeticoes de um
    % config vindo de maquinas diferentes de proposito), sem estes campos nao ha
    % como DEMONSTRAR a diluicao nem responder "isto e o algoritmo ou a
    % maquina?". `plataforma` importa tanto quanto o host: a divergencia
    % cross-maquina medida nasce no 1o fit do GP e e efeito de BLAS/libm, isto
    % e, de SO+arquitetura. Gemeo do `standalone_harness._host_info`.
    man.env = struct('matlab', string(version), 'stack', "matlab-platemo", ...
                     'host', string(host_curto()), ...
                     'plataforma', string(plataforma_curta()), ...
                     'pymoo', "0.6.2");
    % [v5.2.1/§17.6 — OBRIGATORIO] O bloco `timing` nascia zerado aqui e so o
    % e103 o preenchia (auditoria da torre: ZERADO em 10/12). Agora e derivado
    % da ④ pelo `fill_manifest_timing`, chamado por cada run_* antes do
    % write_manifest; estes defaults so valem se a ④ vier vazia (pisos sem ④).
    man.timing = struct('tempo_total_s', NaN, 'tempo_fit_surrogate_s', NaN, ...
                        'tempo_busca_s', NaN, 'tempo_aval_real_s', NaN, ...
                        'tempo_pred_sonda_s', NaN);
    man.fit_series = {};
    man.cache_hits = cache_hits;
    man.fallback_ativado = false;
    man.paths = struct('local', local);
    man.created_at = iso_now();
    man.updated_at = iso_now();
end

function cid = campanha_id_corrente()
% [B-03] A identidade da campanha corrente — a MESMA fonte do lado Python
% (`src/manifest.py:campanha_id_corrente`): a variavel de ambiente
% UA_DD_SAEA_CAMPANHA_ID e, na ausencia dela, `{commit12}_{data UTC}`.
% A env e o modo NORMATIVO: a campanha das 30 sementes leva ~21 dias, e o
% default derivado da data mudaria de valor no meio (o resume re-rodaria tudo).
% `persistent` porque o `git rev-parse` e um system() por processo MATLAB.
    persistent cache
    if ~isempty(cache), cid = cache; return; end
    v = strtrim(getenv('UA_DD_SAEA_CAMPANHA_ID'));
    if ~isempty(v)
        cache = v; cid = v; return;
    end
    h = 'sem-git';
    try
        raiz = fileparts(fileparts(mfilename('fullpath')));
        [st, out] = system(sprintf('git -C "%s" rev-parse --short=12 HEAD', raiz));
        out = strtrim(out);
        if st == 0 && ~isempty(out), h = out; end
    catch
    end
    dia = char(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd'));
    cache = sprintf('%s_%s', h, dia);
    cid = cache;
end

function h = repo_hash_corrente()
% [I-09] O commit COMPLETO do repo (gemeo de `src/manifest.py:repo_hash_corrente`).
% `persistent` porque e um system() por processo MATLAB.
    persistent cache
    if ~isempty(cache), h = cache; return; end
    h = '';
    try
        raiz = fileparts(fileparts(mfilename('fullpath')));
        [st, out] = system(sprintf('git -C "%s" rev-parse HEAD', raiz));
        out = strtrim(out);
        if st == 0 && ~isempty(out), h = out; end
    catch
    end
    cache = h;
end

function man = fill_manifest_timing(man, trows, bud, tempo_total_s, snd)
% [v5.2.1/§17.6] Preenche o bloco `timing` OBRIGATORIO + a `fit_series`, e (se
% houver sonda) o bloco `man.sonda`. Chamado por cada run_* ANTES do
% write_manifest. Agregacao a partir da MESMA fonte da ④ (as trows) -> o
% manifesto e a camada ④ nunca divergem.
%
%   tempo_total_s      wall do run (tic no topo do run_*)
%   tempo_fit_surrogate_s / tempo_busca_s / tempo_pred_sonda_s  somas da ④
%   tempo_aval_real_s  do cronometro do FEBudget (o portao unico das avaliacoes)
    sum_of = @(f) local_nansum(cellfun(@(t) double(opt_scal(field_or(t, f))), ...
                                       trows(:).', 'UniformOutput', true));
    if isempty(trows)
        tf = NaN; tb = NaN; tps = NaN;
    else
        tf  = sum_of('tempo_fit_s');
        tb  = sum_of('tempo_busca_s');
        tps = sum_of('tempo_pred_sonda_s');
    end
    % [DI-09] O total de sonda vem do SondaState, nao da soma da ④: a sonda
    % FINAL dispara DEPOIS do laco (pos-Solve), quando nenhuma linha ④ nova
    % esta mais sendo criada — somar a ④ sub-reportaria justamente o bloco do
    % modelo final. Regra de leitura: soma da ④ <= manifesto; a diferenca e o
    % bloco final. (A ④ segue com a atribuicao POR GERACAO, que e o seu papel.)
    if nargin >= 5 && ~isempty(snd), tps = snd.tempo_total_s; end
    man.timing = struct( ...
        'tempo_total_s',         double(tempo_total_s), ...
        'tempo_fit_surrogate_s', tf, ...
        'tempo_busca_s',         tb, ...
        'tempo_aval_real_s',     double(bud.tempo_aval_real_s), ...
        'tempo_pred_sonda_s',    tps);

    % ⭐ fit_series (§17.6): (n_acumulado, tempo_fit_s) por RETREINO — a curva
    % da parede O(n³). Linhas sem retreino (so wall da geracao) nao entram.
    fs = {};
    for k = 1:numel(trows)
        na = double(opt_scal(field_or(trows{k}, 'n_acumulado')));
        tk = double(opt_scal(field_or(trows{k}, 'tempo_fit_s')));
        if ~isnan(na) && ~isnan(tk)
            fs{end+1} = struct('geracao', double(opt_scal(field_or(trows{k}, 'geracao'))), ...
                               'n_acumulado', na, 'tempo_fit_s', tk); %#ok<AGROW>
        end
    end
    man.fit_series = fs;

    % Bloco `sonda` (DI-09): a certidao da regua usada neste run. Quando o
    % problema esta FORA do grid dos 25 (piloto), o artefato nao existe e o
    % bloco registra a AUSENCIA explicitamente — "sem sonda" nunca pode ser
    % lido como "sonda vazia".
    if nargin >= 5 && ~isempty(snd)
        man.sonda = snd.manifestBlock();
    else
        man.sonda = struct('status', "artefato_ausente", ...
            'motivo', "problema fora do grid dos 25 (sonda e por problema, Sobol d=D)");
    end
end

function s = local_nansum(v)
    v = v(~isnan(v));
    if isempty(v), s = NaN; else, s = sum(v); end
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
function [tier, dist] = nm_parse_sweep(exp)
    % [T7-sweep] Espelho EXATO de src/naming.py::parse_sweep.
    % `main`/`off`/`batch` e qualquer token nao-sweep => ('','') = o principal.
    % Token COM forma de sweep mas vocabulario invalido => ERRO (D81): devolver
    % o principal recriaria o bug silencioso (rodar sobre o dataset small e
    % gravar sob o nome do sweep).
    tier = ''; dist = '';
    tk = regexp(char(exp), '^sweep-([A-Za-z0-9]+)-([A-Za-z0-9]+)$', ...
                'tokens', 'once');
    if isempty(tk), return; end
    t = tk{1}; d = tk{2};
    assert(any(strcmp(t, {'small','medium','big'})) && ...
           any(strcmp(d, {'lhs','mvns'})), ...
           ['token de sweep com vocabulario invalido: %s (tier=%s, dist=%s). ' ...
            'D38/D67/D90 — para-e-loga (D81).'], char(exp), t, d);
    tier = t; dist = d;
end
function tf = nm_is_main_variant(tier, dist)
    % [T7-sweep] Espelho de src/naming.py::is_main_variant. small+lhs E o
    % offline PRINCIPAL e e gravado SEM sufixo (seeds.json, D90) — nao existe
    % ds_{p}_{s}_small_lhs.parquet em disco.
    tf = (isempty(tier) && isempty(dist)) || ...
         (strcmp(tier, 'small') && strcmp(dist, 'lhs'));
end
function s = nm_dataset_sufixo(tier, dist)
    if nm_is_main_variant(tier, dist)
        s = '';
    else
        s = sprintf('_%s_%s', char(tier), char(dist));
    end
end
function p = nm_dataset_path(problema, semente, dataRoot, tier, dist)
    % Espelho de src/naming.py::dataset_path (principal: tier small/dist lhs
    % -> nome SEM sufixo — D90/seeds.json). [T7] tier/dist opcionais.
    if nargin < 4, tier = ''; end
    if nargin < 5, dist = ''; end
    p = fullfile(char(dataRoot), 'datasets', char(problema), ...
                 sprintf('ds_%s_%s%s.parquet', char(problema), ...
                         num2str(semente), nm_dataset_sufixo(tier, dist)));
end
function p = nm_dataset_manifest_path(problema, semente, dataRoot, tier, dist)
    if nargin < 4, tier = ''; end
    if nargin < 5, dist = ''; end
    p = fullfile(char(dataRoot), 'datasets', char(problema), ...
                 sprintf('ds_%s_%s%s.manifest.json', char(problema), ...
                         num2str(semente), nm_dataset_sufixo(tier, dist)));
end
function p = nm_sonda_path(problema, dataRoot)
    % [DI-09/§17.2.2] A sonda e POR PROBLEMA (nao por semente): os MESMOS 2000
    % pontos p/ todos os algoritmos, geracoes e sementes.
    p = fullfile(char(dataRoot), 'sonda', sprintf('sonda_%s.parquet', char(problema)));
end
function p = nm_sonda_manifest_path(problema, dataRoot)
    p = fullfile(char(dataRoot), 'sonda', sprintf('sonda_%s.manifest.json', char(problema)));
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


function h = host_curto()
% [C2/BL-07] Nome curto da maquina (sem dominio) — mesma convencao do
% scripts/censo42.py. `UA_DD_SAEA_HOST` sobrepoe, p/ o operador rotular a
% maquina com o nome do roster. NUNCA levanta: um ⑤ sem host e ruim; um run
% derrubado por causa disso e pior.
    h = "";
    try
        h = string(getenv('UA_DD_SAEA_HOST'));
        if strlength(h) == 0
            [st, out] = system('hostname');
            if st == 0
                p = split(strtrim(string(out)), ".");
                h = p(1);
            end
        end
    catch
        h = "";
    end
end

function p = plataforma_curta()
% [C2/BL-07] "<SO>/<arquitetura>" — o discriminante que de fato governa a
% divergencia numerica entre maquinas (BLAS/libm), mais informativo que o host.
% A arquitetura e NORMALIZADA para o vocabulario do `platform.machine()` do
% Python (arm64/x86_64): o `computer('arch')` do MATLAB fala 'maca64'/'glnxa64',
% e duas grafias para a MESMA maquina obrigariam a R4 a conhecer dois
% vocabularios so porque a celula mudou de stack.
    p = "";
    try
        if ismac,          so = "Darwin";
        elseif isunix,     so = "Linux";
        else,              so = "Windows";
        end
        a = string(computer('arch'));
        switch a
            case "maca64", arq = "arm64";      % Apple Silicon
            case "maci64", arq = "x86_64";     % Mac Intel
            case "glnxa64", arq = "x86_64";    % Linux x64
            case "win64",  arq = "AMD64";
            otherwise,     arq = a;            % desconhecida: grava como veio
        end
        p = so + "/" + arq;
    catch
        p = "";
    end
end


% ════════════════════════════════════════════════════════════════════════════
%  Log de auditoria .jsonl (§17.5) — mesma linha {ts, rec, ...} do audit_log.py
% ════════════════════════════════════════════════════════════════════════════

function fid = jsonl_open(path)
% [B-11] O dono da celula TRUNCA 1x e passa a escrever em APPEND.
% O handle 'w' escreve no deslocamento PROPRIO: a descarga do buffer dele passa
% por cima do que outro escritor ja pos no fim do arquivo (o footer do
% despachante Python, que mantem o ⑥ aberto em 'a' durante a chamada MATLAB, ou
% um 2o processo da mesma celula). Medido no gemeo Python deste writer: com dois
% escritores 'w' na mesma celula sobram 5.000 de 10.000 linhas; com 'w' + 'a',
% os outros escritores perdem 2.903 de 10.000 e sai 1 linha malformada — a
% familia do main/b1/WFG1 (49 de 931 spliced, 0 footer) e do
% moead_media/swap_small-lhs_ZDT1 (2 escritores, retrocesso de 134,3 s). Em 'a'
% cada fprintf vai para o FIM do arquivo e o pior caso deixa de ser PERDA.
% O anti-append do B-01 nao se aplica aqui: quem abre este handle E o dono do
% run (equivale ao append=false do lado Python — audit_log.py:105).
    ensure_dir(path);
    fid = fopen(path, 'w');
    assert(fid > 0, 'nao abriu jsonl %s', path);
    fclose(fid);
    fid = fopen(path, 'a');
    assert(fid > 0, 'nao reabriu em append o jsonl %s', path);
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
