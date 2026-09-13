function ftm = b1_sonda(Problem, dmodel, PDec, PCheby, lamda, fmin, fmax, tfit_s)
% b1_sonda — bloco da SONDA CANONICA (DI-09/§17.2.2) do b1 ParEGO.
% Chamado da ParEGO.main logo APOS o fit do GP (dacefit) e ANTES de qualquer
% decisao da busca. READ-ONLY: nao altera a busca (D97) e nao gasta FE.
%
% Devolve `ftm` (fe_treino_max) porque ele SO e calculavel AQUI — ver a secao
% homonima abaixo; o chamador o repassa ao b1_instrument, que roda pos-Evaluation.
%
% Semantica contratada (CONTRATO_DE_DADOS §3.2, linha b1 — CASO ESPECIAL D47):
% o b1 e MONO-OUTPUT: o GP nao modela os objetivos, modela o ESCALAR de
% Tchebycheff aumentado com o λ SORTEADO NA ITERACAO CORRENTE (ParEGO.m:40/:55).
% Logo a sonda responde "o escalar Tcheby DESTA iteracao nos 2000 pontos":
%   mu_0    = y   (PCheby predito)             sigma_0 = sqrt(max(mse,0))
%   mu_1..  = NULL (nao existe μ por objetivo — limitacao INERENTE, §3.2)
% e o C3 (DEF-C3) carrega {λ, min, max, gbest}: SEM eles o escalar e
% ininterpretavel, porque o λ muda a cada iteracao e a normalizacao tambem.
%
% Por que ESTE ponto (ParEGO.m, apos :79, antes de :83):
%   1. o fit do ciclo terminou (:77 dacefit, :78 fecha tfit_s) e o warm-start do
%      theta ja foi lido (:79) — `dmodel` esta completo e a sonda so o LE;
%   2. e ANTES do EvolALG (:84), o UNICO consumidor de RNG do ciclo depois do
%      fit (TournamentSelection/OperatorGA em EvolALG.m:23/:64). O sorteio do λ
%      (randi, :40) acontece ANTES do fit — a sonda nao o alcanca;
%   3. e ANTES de Problem.Evaluation (:86), onde o FEBudget levanta
%      PlatEMO:Termination no hard-stop — o hook pos-decisao (:93) NAO roda
%      nesse caminho, este roda;
%   4. e ANTES do `t0_busca = tic` (:83): a sonda DENTRO da janela da busca
%      contaminaria `tempo_busca_s`, que e o eixo do breakdown do §17.6.
%
% `Gbest` SEM patch: o EvolALG calcula `Gbest = min(PCheby)` (EvolALG.m:26) a
% partir do MESMO PCheby pos-dedup (:71) que ja esta em escopo aqui — logo o
% valor e reconstruivel EXATAMENTE, read-only. Nao patchar o EvolArG por isto.
%
% RNG: `predictor`/`corrgauss`/`regpoly1` sao aritmetica pura — zero rand/randn.
% O save/restore acontece assim mesmo, dentro do SondaState (I1 e estrutural).

    % ── fe_treino_max (DI-09/A1) ─────────────────────────────────────────────
    % O treino do b1 e o `PDec` POS-CAP e POS-DEDUP (:56-71) — exatamente a
    % matriz que entra no dacefit (:77) — e NAO o arquivo inteiro. Por isso o
    % atalho `bud.fe-1-lote` do c141 (c141_instrument.m:47) NAO vale aqui, e
    % por isso o calculo mora NESTE ponto: no b1_instrument (:93) o arquivo ja
    % cresceu com a Evaluation de :86 e o PDec daquele fit nao e reconstruivel.
    % ⚠ NAO-MONOTONICO (regra 9 do R4): o cap top-(11D-1+25) e por PCheby, que e
    % re-escalarizado com um λ novo a cada iteracao => o subconjunto TROCA de
    % composicao, nao so cresce; e o `unique` do dedup mantem a 1a ocorrencia
    % (o fe_index MENOR de cada par).
    bud = Problem.data.bud;
    ftm = -1;
    for i = 1:size(PDec, 1)
        sid = bud.solutionIdOf(PDec(i, :));
        if sid > ftm, ftm = sid; end
    end
    if ftm < 0, ftm = []; end

    d = Problem.data;
    if ~isfield(d, 'snd') || isempty(d.snd), return; end
    snd = d.snd;
    g = double(d.buf.gen);
    if g < 1, g = 1; end

    % C3 (DEF-C3) — IDENTICO ao que o b1_instrument serializa nas linhas de
    % busca (b1_instrument.m:64-65), para que sonda e busca sejam comparaveis.
    gbest = min(PCheby);
    tp = string(jsonencode(struct('lambda', lamda(:).', 'min', fmin(:).', ...
                                  'max', fmax(:).', 'gbest', gbest)));

    hp = struct('theta', dmodel.theta(:).', 'sigma2', dmodel.sigma2(:).', ...
                'n', size(dmodel.S, 1), ...
                'regr', string(func2str_b1(dmodel.regr)), ...
                'corr', string(func2str_b1(dmodel.corr)), ...
                'tempo_fit_s', tfit_s);

    fn = @(Xs) b1_sonda_rows(dmodel, Xs, tp);
    snd.probe(g, fn, ftm, 'modelo', "GP-DACE", 'hp', hp);
end


function rows = b1_sonda_rows(dmodel, Xs, tp)
% As S linhas da ③, NA ORDEM DO ARTEFATO (join por posicao — §3.1).
% Xs entra NATIVO e sem conversao: o `predictor` normaliza internamente por
% dmodel.Ssc (predictor.m:50), exatamente como o EvolALG faz com os decs nativos.
%
% ⚠ CHUNKING: o ramo mx>1 do predictor materializa `dx` de (mx*m) x D
% (predictor.m:92-97) — no ZDT1 (D=30, m~350, mx=2000) sao ~168 MB por chamada.
% As linhas sao INDEPENDENTES (f e r por linha; os solves C\r e G\u sao
% coluna-a-coluna), logo fatiar e BIT-EQUIVALENTE e a concatenacao preserva a
% ordem do artefato (I3). ⚠ EXATAMENTE 2 outputs: com nargout>2 o ramo batch
% imprime 'WARNING from PREDICTOR' a cada bloco (predictor.m:110-112).
    n = size(Xs, 1);
    Y = zeros(n, 1);
    S = zeros(n, 1);
    passo = 250;
    for a = 1:passo:n
        b = min(a + passo - 1, n);
        [yb, mseb] = predictor(Xs(a:b, :), dmodel);
        Y(a:b) = yb(:);
        % MESMO guard da busca (P2/L8, EvolALG.m:43): mse<0 e erro de float.
        S(a:b) = sqrt(max(mseb(:), 0));
    end
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'mu', Y, 'sigma', S, ...
        'pred_tipo', "valor", 'modelo_flag', "GP-DACE", ...
        'espaco_modelo', "transformado", 'transf_tipo', "escalar-tcheby", ...
        'transf_params', tp);
end


function s = func2str_b1(f)
    if isa(f, 'function_handle'), s = func2str(f); else, s = string(f); end
end
