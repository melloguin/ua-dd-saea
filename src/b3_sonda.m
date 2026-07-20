function ftm = b3_sonda(Problem, Model, A1Dec, tfit_s, pred_h)
% b3_sonda — bloco da SONDA CANONICA (DI-09/§17.2.2) do b3 K-RVEA.
% Chamado da KRVEA.main logo APOS o fit dos M Krigings DACE e ANTES de qualquer
% decisao da busca. READ-ONLY: nao altera nenhuma decisao (D97) e nao gasta FE.
%
% Devolve `ftm` (fe_treino_max) porque ele SO e calculavel AQUI — ver a secao
% homonima abaixo; o chamador o repassa ao b3_instrument, que roda pos-Evaluation
% (quando A1 JA foi reescrito pelo UpdataArchive e o treino deste ciclo sumiu).
%
% Semantica contratada (CONTRATO_DE_DADOS §3.2, linha "b3, c141, e7, ..."):
% REGRESSOR mu + sigma POR OBJETIVO. Sao M Krigings INDEPENDENTES, Model{i}, um
% por objetivo (KRVEA.m:48-56), logo cada linha da ③ carrega
%   mu_j    = y  do predictor para o objetivo j
%   sigma_j = sqrt(max(MSE_j, 0))
% que e EXATAMENTE a convencao de export ja usada nas linhas de busca do b3
% (b3_instrument.m:62) e no man.sigma_dict (experiment.m). ⚠ Nao confundir com o
% criterio INTERNO do switch da selecao, que usa a MEDIA das MSEs SEM raiz
% (KrigingSelect.m:61): a raiz aqui e so UNIDADE de export, nao o criterio.
% pred_tipo = "valor"; pred_classe/pred_score/pred_confianca ficam NULL.
%
% BLOCOS POR CICLO = 1: existe um unico cell `Model` (1 x M), retreinado no topo
% de cada ciclo — nada do multi-cabeca do e74 nem do offline do e103 se aplica.
%
% Por que ESTE ponto (KRVEA.m, apos :57, antes de :58):
%   1. o fit do ciclo terminou por COMPLETO: o laco `for i = 1:Problem.M` abre em
%      :48 e fecha em :56, Model{1..M} esta populado, THETA foi warm-startada
%      (:55) e `tfit_s = toc(t0_fit)` fechou em :57. Entre :57 e :58 nao ha
%      NENHUM statement — a sonda entra num vao vazio;
%   2. e ANTES da 1a decisao: :58 (`PopDec = A1Dec`) e mera inicializacao; a 1a
%      decisao real e o KEnvironmentalSelection de :73;
%   3. e ANTES do 1o consumo de RNG do ciclo. Os consumidores, nesta ordem, sao
%      OperatorGA (KRVEA.m:63, o primeiro), kmeans (KrigingSelect.m:21, via :90)
%      e kmeans+randi (UpdataArchive.m:42/:46 ou :55/:59, ramos if/else, via
%      :95). O hook precede TODOS. dacefit.m e predictor.m sao 100%
%      deterministicos (zero rand/randn/randi/randperm);
%   4. e ANTES de Problem.Evaluation (KRVEA.m:91), onde o FEBudget levanta
%      PlatEMO:Termination no hard-stop (FEBudget.m:89). Nesse caminho o hook
%      POS-decisao (b3_instrument, KRVEA.m:101-102) NAO roda — este roda. A
%      Evaluation do DoE (:36) e pre-laco e sem modelo: sem sonda, correto;
%   5. e ANTES do relogio da busca: a sonda dentro da janela de `tempo_busca_s`
%      contaminaria o breakdown do §17.6. O cronometro da sonda e proprio (I6)
%      e sai por snd.takePendingTime().
%
% ⚠ SOMBRA DE PATH em `predictor` (risco GRAVE, especifico deste arquivo): este
% .m vive em src/ e NAO tem a precedencia same-folder que protege a KRVEA.m. Ha
% ~30 copias de predictor.m na arvore PlatEMO, em variantes NUMERICAMENTE
% distintas (CI-EMO, MOEA-D-PFE, Single-objective/EGO diferem da do K-RVEA), e
% `ensure_paths_b3` (experiment.m:990-998) faz addpath(genpath(arvore inteira))
% sem nenhum assert. Se a sonda predizer com uma copia diferente da que a busca
% usa, o DI-09 mede um modelo que o algoritmo NAO usa — falha silenciosa e
% invisivel no gate. Por isso o 5o argumento `pred_h` = `@predictor` criado no
% ESCOPO da KRVEA.m: o handle resolve no contexto DAQUELE arquivo, garantindo
% K-RVEA/predictor.m. O fallback abaixo (sem pred_h) so aceita seguir se o
% `which` provar a origem — mesmo idioma do assert de ensure_paths_c141.
%
% RNG: o caminho inteiro (predictor/corrgauss/regpoly1) e aritmetica pura. O
% save/restore acontece assim mesmo, dentro do SondaState (I1 e estrutural).

    % ── fe_treino_max (DI-09/A1) ─────────────────────────────────────────────
    % LITERAL do §17.2: "maior fe_index no TREINO do modelo no momento do fit".
    % O treino do b3 e `A1Dec` INTEIRO, sem subamostragem (KRVEA.m:53 usa A1Dec
    % completo — nao ha nada como o TrainIn 3/4 do c217). Mesmo assim o atalho
    % `bud.fe-1` do c141 e PROIBIDO aqui, por dois motivos independentes:
    %   (a) o A1 do b3 TEM TETO NI=11D-1 e e PODADO (UpdataArchive.m:27 e :70) —
    %       diferente do A1 do c141, que nunca poda;
    %   (b) o dedup e `[~,index] = unique(All,'rows')` sobre `All =
    %       [A1.decs;New.decs]` (UpdataArchive.m:21-24), que fica com a PRIMEIRA
    %       ocorrencia: se um infill duplicar um ponto ja no arquivo, e a
    %       solucao VELHA (id antigo) que sobrevive e a nova e descartada. No
    %       ramo `else` (UpdataArchive.m:71-72) o arquivo vira esse `Total` cru,
    %       sem o `New` reanexado. E o b3 PROPOE duplicata de verdade (PopDec
    %       parte de A1Dec, KRVEA.m:58). Logo `bud.fe-1` pode simplesmente NAO
    %       estar em A1 e o atalho daria um ftm ERRADO.
    % => varredura por bud.solutionIdOf (read-only, sem RNG, 0 FE — I2), com
    % |A1| <= NI (21 em MMF1 D=2, 131 em D=12, 329 em ZDT1 D=30): custo
    % desprezivel. solution_id == fe_index por construcao (FEBudget.m:98-99).
    % ⚠ Calculado ANTES do early-return de "run sem sonda": o valor tambem
    % alimenta a linha b3_gen e as linhas ③ de busca, que existem sempre.
    bud = Problem.data.bud;
    D   = Problem.D;
    ftm = -1;
    for i = 1:size(A1Dec, 1)
        sid = bud.solutionIdOf(A1Dec(i, 1:D));
        if sid > ftm, ftm = sid; end
    end
    if ftm < 0, ftm = []; end                      % => NULL na ③

    d = Problem.data;
    if ~isfield(d, 'snd') || isempty(d.snd), return; end     % run sem sonda
    snd = d.snd;
    g = double(d.buf.gen);      % o hook ja bumpou no topo do ciclo (NotTerminated)
    if g < 1, g = 1; end

    % ── handle do preditor (ver a nota de SOMBRA DE PATH no cabecalho) ───────
    if nargin < 5 || isempty(pred_h)
        w = which('predictor');
        assert(~isempty(w) && contains(w, 'K-RVEA'), 'b3_sonda:predictor', ...
            ['`predictor` resolveu para "%s" (nao K-RVEA). Passe pred_h = ' ...
             '@predictor criado no escopo da KRVEA.m.'], w);
        pred_h = @predictor;
    end

    % hp efetivos dos M DACEs (DI-10/B1) — o que torna mu/sigma interpretaveis.
    % regr/corr/bounds sao literais da KRVEA.m:53; theta e MxD (uma linha por
    % objetivo) e vem warm-startada do ciclo anterior (KRVEA.m:55).
    M  = Problem.M;
    TH = zeros(M, D);
    S2 = zeros(1, M);
    for j = 1:M
        TH(j, :) = Model{j}.theta(:).';
        S2(j)    = Model{j}.sigma2(1);
    end
    hp = struct('regr', "regpoly1", 'corr', "corrgauss", ...
                'theta0', 5, 'theta_lb', 1e-5, 'theta_ub', 100, ...
                'warm_theta', true, 'theta', TH, 'sigma2', S2, ...
                'n', size(A1Dec, 1), 'tempo_fit_s', tfit_s);

    fn = @(Xs) b3_sonda_rows(Model, Xs, M, pred_h);
    snd.probe(g, fn, ftm, 'modelo', "GP-DACE", 'hp', hp);
end


function rows = b3_sonda_rows(Model, Xs, M, pred_h)
% As S=2000 linhas da ③, NA ORDEM DO ARTEFATO (o join com o gabarito e POR
% POSICAO — §3.1/I3). Xs vai DIRETO ao preditor: sem sort, sem unique, sem
% clamp, sem filtro.
%
% ESPACO: "cru" (o termo do contrato — DI-17.8). O `predictor` normaliza X internamente por dmodel.Ssc
% (predictor.m:50), exatamente como a busca faz com os decs nativos da KRVEA.m:70
% => o parquet da sonda entra sem NENHUMA conversao; transf_tipo/params = NULL.
%
% ⚠ CHUNKING OBRIGATORIO (memoria): o ramo de LOTE materializa `dx` de
% (mx*m) x D (predictor.m:92-97) e o corrgauss aloca um intermediario do mesmo
% tamanho. Em ZDT1 (D=30, m=|A1|<=329, mx=2000) sao ~158 MB POR intermediario,
% ~0,3-0,5 GB transitorio POR OBJETIVO. Fatiar e legitimo porque no ramo de lote
% cada SITIO e uma COLUNA de `r` e os solves sao coluna-a-coluna
% (predictor.m:107-109: rt = C\r; u = G\(Ft.'*rt - f.'); sum(.,1)) => as linhas
% sao matematicamente independentes e a concatenacao preserva a ordem (I3).
% ⚠ NAO afirmar bit-identidade chunk-vs-lote como fato: `C\r` e `G\(...)` sao
% solves multi-RHS com BLAS blocado; a prova (max|delta| == 0) e EMPIRICA.
%
% ⚠ EXATAMENTE 2 SAIDAS: no ramo de lote `or1` E a MSE (predictor.m:106-109), e
% com nargout>2 o codigo IMPRIME 'WARNING from PREDICTOR' (predictor.m:110-112)
% — seriam M warnings por bloco, ate 61 blocos em ZDT1, poluindo o stdout do
% worker. Nunca chamar com 3 saidas aqui.
%
% ⚠ NUNCA deixar um chunk de 1 LINHA: com mx==1 o predictor cai no ramo
% :52-89, onde `or1` e o GRADIENTE (a MSE seria or2) e o caminho numerico e
% outro. O passo divide 2000 exatamente, mas o guard abaixo e explicito.
    n  = size(Xs, 1);
    MU = zeros(n, M);
    SG = zeros(n, M);
    passo = 250;
    a = 1;
    while a <= n
        b = min(a + passo - 1, n);
        if (n - b) == 1, b = n; end          % absorve o resto de 1 linha
        Xb = Xs(a:b, :);
        for j = 1:M
            [yb, mseb] = pred_h(Xb, Model{j});          % 2 saidas: or1 = MSE
            MU(a:b, j) = yb(:);
            % MESMO guard da busca (b3_instrument.m:62): mse<0 e erro de float.
            SG(a:b, j) = sqrt(max(mseb(:), 0));
        end
        a = b + 1;
    end
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'mu', MU, 'sigma', SG, ...
        'pred_tipo', "valor", 'modelo_flag', "GP-DACE", ...
        'espaco_modelo', "cru");
end
