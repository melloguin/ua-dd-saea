function nfail = accept_r1_00(problema, semente, dataRoot, exp)
% accept_r1_00 — aceitacao MATLAB do cartao R1-00-harness (D97: so encanamento).
%
% Roda o run-STUB (avaliador trivial, sem algoritmo) ponta-a-ponta pelo adapter
% src/experiment.m e afere os pontos objetivos do cartao:
%   1. FE final = 31D-1 EXATO (linhas da camada ① — D89).
%   2. cache-hit = 0 FE + hard-stop EXATO (PlatEMO:Termination — D89/D21).
%   3. as 4 saidas presentes + schema §17.2 (nomes+tipos das 4 camadas).
%   4. CP-init (D87/D88): a init X injetada bate bit-a-bit com o DoE do F0-02
%      — hash float64 (init_X vs sidecar) E a ① (float32) == single(DoE).
%
% SEM algoritmo => SEM fidelidade (D97). Uso (no Mac, na raiz do repo):
%   addpath('src');  nfail = accept_r1_00            % MMF1/0/'data'
%   nfail = accept_r1_00('MMF1', 0, 'data')

    if nargin < 1 || isempty(problema), problema = 'MMF1'; end
    if nargin < 2 || isempty(semente),  semente  = 0;      end
    if nargin < 3 || isempty(dataRoot), dataRoot = 'data'; end
    if nargin < 4 || isempty(exp),      exp = 'main';      end
    alg = 'stub';
    npass = 0; nfail = 0;
    fprintf('== Aceitacao MATLAB — R1-00-harness (%s/%s/%s/%d) ==\n', ...
            exp, alg, problema, semente);

    % ── roda o STUB ponta-a-ponta ────────────────────────────────────────────
    [status, info] = experiment(alg, problema, semente, exp, dataRoot);
    [npass, nfail] = chk(npass, nfail, 'STUB ponta-a-ponta => status ok', ...
                         status == "ok", char(status));

    D = info.D; M = info.M;

    % (1) FE final = 31D-1 exato (linhas da ①).
    realp = layer_path(exp, alg, problema, semente, 'real', dataRoot);
    T1 = parquetread(realp);
    [npass, nfail] = chk(npass, nfail, 'FE final = 31D-1 exato (linhas ① — D89)', ...
        height(T1) == info.maxfe && info.fe_final == info.maxfe, ...
        sprintf('rows=%d fe_final=%d esperado=%d', height(T1), info.fe_final, info.maxfe));

    % (2) cache-hit = 0 FE + hard-stop exato.
    [npass, nfail] = chk(npass, nfail, 'cache-hit = 0 FE + hard-stop exato (D89/D21)', ...
        info.cache_hit_zero_fe && info.cache_hits >= 1 && info.hard_stopped, ...
        sprintf('cache_hits=%d zero_fe=%d hard_stop=%d', ...
                info.cache_hits, info.cache_hit_zero_fe, info.hard_stopped));

    % (3) as 4 saidas presentes + schema §17.2.
    outs = output_files(exp, alg, problema, semente, dataRoot);
    miss = outs(~cellfun(@isfile, outs));
    [npass, nfail] = chk(npass, nfail, '4 saidas presentes (3 parquet + timing + jsonl)', ...
        isempty(miss), sprintf('faltando: %s', strjoin(miss, ', ')));

    [ok_s, msg_s] = check_schemas(exp, alg, problema, semente, dataRoot, D, M);
    [npass, nfail] = chk(npass, nfail, 'schema §17.2 das 4 camadas (nomes+tipos)', ok_s, msg_s);

    % (4) CP-init: hash float64 (init_X vs sidecar) E ①(float32) == single(DoE).
    [npass, nfail] = chk(npass, nfail, 'CP-init hash: init_X (float64) = sidecar do DoE', ...
        info.cp_ok && info.doe_hash_run == info.doe_hash_sidecar, ...
        sprintf('%s %s sidecar', extractBefore(info.doe_hash_run + "________", 17), ...
                ternary(info.cp_ok, "=", "!=")));

    [ok_c, msg_c] = check_cp_layer1(T1, problema, semente, dataRoot, D);
    [npass, nfail] = chk(npass, nfail, 'CP-init camada ①: X inicial (float32) = single(DoE)', ok_c, msg_c);

    fprintf('\n[accept_r1_00] PASS=%d FAIL=%d\n', npass, nfail);
    if nfail == 0
        fprintf('  >>> VERDE (encanamento objetivo) — R1-00 harness fecha.\n');
    else
        fprintf(2, '  >>> VERMELHO — para-e-loga (D81).\n');
    end
    fprintf('  Lembrete (D97): fidelidade = validacao MANUAL do autor, a posteriori.\n');
end


% ── checagens ───────────────────────────────────────────────────────────────

function [ok, msg] = check_schemas(exp, alg, problema, semente, dataRoot, D, M)
    xs = arrayfun(@(j) sprintf('x%d', j), 0:D-1, 'uni', 0);
    fs = arrayfun(@(j) sprintf('f%d', j), 0:M-1, 'uni', 0);
    mus = arrayfun(@(j) sprintf('mu_%d', j), 0:M-1, 'uni', 0);
    sgs = arrayfun(@(j) sprintf('sigma_%d', j), 0:M-1, 'uni', 0);
    want.real = [{'algoritmo','string','problema','string','semente','int32', ...
        'solution_id','int32'}, kv(xs,'single'), kv(fs,'single'), ...
        {'fe_index','int32','fase','string'}];
    want.pop = {'algoritmo','string','problema','string','semente','int32', ...
        'geracao','int32','solution_id','int32'};
    want.surrogate = [{'algoritmo','string','problema','string','semente','int32', ...
        'regime','string','geracao','int32'}, kv(xs,'single'), ...
        {'real_solution_id','int32'}, kv(mus,'single'), kv(sgs,'single'), ...
        {'pred_tipo','string','pred_classe','string','pred_score','single', ...
         'pred_confianca','single','modelo_flag','string','espaco_modelo','string', ...
         'transf_tipo','string','transf_params','string'}];
    want.timing = {'run_id','string','geracao','int32','n_acumulado','int32', ...
        'tempo_fit_s','single','tempo_busca_s','single'};
    msgs = {};
    for ly = ["real","pop","surrogate","timing"]
        p = layer_path(exp, alg, problema, semente, char(ly), dataRoot);
        inf = parquetinfo(p);
        names = cellstr(inf.VariableNames); types = cellstr(inf.VariableTypes);
        w = want.(ly);
        wn = w(1:2:end); wt = w(2:2:end);
        if ~isequal(names(:), wn(:))
            msgs{end+1} = sprintf('%s: nomes divergem', ly); %#ok<AGROW>
        elseif ~isequal(types(:), wt(:))
            bad = find(~strcmp(types(:), wt(:)), 1);
            msgs{end+1} = sprintf('%s: tipo de %s = %s (esperado %s)', ...
                ly, names{bad}, types{bad}, wt{bad}); %#ok<AGROW>
        end
    end
    ok = isempty(msgs);
    if ok, msg = 'nomes+tipos §17.2 conferem nas 4 camadas'; else, msg = strjoin(msgs, '; '); end
end

function [ok, msg] = check_cp_layer1(T1, problema, semente, dataRoot, D)
    % A ① (float32) da fase 'init' == single(DoE) bit-a-bit.
    init = T1(T1.fase == "init", :);
    xcols = arrayfun(@(j) sprintf('x%d', j), 0:D-1, 'uni', 0);
    Xi = single(init{:, xcols});
    doep = fullfile(char(dataRoot), 'doe', char(problema), ...
                    sprintf('doe_%s_%s.parquet', char(problema), num2str(semente)));
    Td = parquetread(doep);
    Xd = single(Td{:, xcols});
    ok = isequal(size(Xi), size(Xd)) && isequal(Xi, Xd);
    if ok
        msg = sprintf('%d linhas init = single(DoE) bit-a-bit', size(Xi,1));
    else
        msg = sprintf('divergencia ①(init) vs single(DoE): sizes [%s] vs [%s]', ...
            num2str(size(Xi)), num2str(size(Xd)));
    end
end


% ── helpers de naming/plumbing (espelham src/naming.py) ──────────────────────

function outs = output_files(exp, alg, problema, semente, dataRoot)
    outs = { ...
        layer_path(exp, alg, problema, semente, 'real', dataRoot), ...
        layer_path(exp, alg, problema, semente, 'pop', dataRoot), ...
        layer_path(exp, alg, problema, semente, 'surrogate', dataRoot), ...
        layer_path(exp, alg, problema, semente, 'timing', dataRoot), ...
        fullfile(run_dir(exp, alg, dataRoot), [base(exp,alg,problema,semente) '.jsonl'])};
end
function p = layer_path(exp, alg, problema, semente, layer, dataRoot)
    p = fullfile(run_dir(exp, alg, dataRoot), ...
        [base(exp, alg, problema, semente) '__' layer '.parquet']);
end
function d = run_dir(exp, alg, dataRoot)
    a = strrep(strrep(char(alg), '/', '_'), ' ', '_');
    d = fullfile(char(dataRoot), 'experiments', char(exp), a);
end
function b = base(exp, alg, problema, semente)
    a = strrep(strrep(char(alg), '/', '_'), ' ', '_');
    b = sprintf('exp_%s_%s_%s_%s', char(exp), a, char(problema), num2str(semente));
end
function c = kv(names, typ)
    c = cell(1, 2*numel(names));
    c(1:2:end) = names; c(2:2:end) = {typ};
end
function [np, nf] = chk(np, nf, name, ok, msg)
    if ok, mark = 'OK  '; np = np + 1; else, mark = 'FAIL'; nf = nf + 1; end
    fprintf('  [%s] %s: %s\n', mark, name, msg);
end
function v = ternary(c, a, b)
    if c, v = a; else, v = b; end
end
