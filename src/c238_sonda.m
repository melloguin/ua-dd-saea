function c238_sonda(Problem, GP_obj, ymin, yrange)
% c238_sonda — bloco da SONDA CANONICA (DI-09/§17.2.2) do c238 EIM.
% Chamado do embrulho N.5 (EIM.m:99) logo APOS o fit dos M kriging e ANTES de
% qualquer decisao da busca. READ-ONLY: nao altera a busca (D97) e nao gasta FE.
%
% Semantica contratada (CONTRATO_DE_DADOS.md:184, linha "b3, c141, e7, c238"):
% REGRESSOR com mu E sigma POR OBJETIVO. O c238 tem UMA unica cabeca de modelo —
% os M GPs sao as M COLUNAS de uma linha, nao M blocos. Logo: 1 BLOCO por ciclo.
%   mu_j    = u de GP_Predict(Xs, GP_obj{j})           (GP_Predict.m:20)
%   sigma_j = s = sqrt(max(mse,0)), o guard STOCK      (GP_Predict.m:21-22)
%   pred_tipo="valor", modelo_flag="OK-Forrester", pred_classe/score/confianca NULL.
%
% ESPACO: o bloco sai ja invertido para o espaco CRU do gabarito
% [DI-17.6, decisao do autor 2026-07-19]. O modelo do c238 opera sobre y
% min-max-normalizado POR ITERACAO; a sonda existe para comparar o modelo ENTRE
% geracoes e ENTRE algoritmos, e uma regua que muda a cada geracao sabota
% exatamente isso — alem de o gabarito do artefato estar em cru. A inversao
% (mu.*yrange + ymin, sigma.*yrange) e afim e exata, 100% read-only.
% A divergencia com as linhas de BUSCA do c238 (que gravam "transformado" +
% transf_params, c238_instrument.m:77-82) e deliberada e vai declarada no
% sigma_dict do manifesto.
% (Nota de numeracao: as decisoes deste cartao sao DI-17.x — a torre ja ocupou
% DI-15.0..15.5 e DI-16.x numa sessao concorrente.)
%
% ⚠ PENDENCIA TRANSVERSAL (nao resolver so aqui): o VALOR gravado abaixo e
% RESOLVIDO [DI-17.8, autor 2026-07-19]: o valor gravado e "cru", o termo do
% contrato (DEF-C3 "cru+transformado") e o unico que passa na validacao de
% export.py:292. Antes deste cartao os .m gravavam "nativo", FORA do enum de
% export.py:67 — o writer MATLAB nao valida, entao o desvio passava calado ate
% a consolidacao Python. Padronizado nos 21 (o e7 ja estava certo).
%
% Racional da opcao (ii), para embasar a decisao:
% O c238 re-escala Y por MIN-MAX A CADA ITERACAO (EIM.m:66-79), entao o (u,s) que
% sai do GP esta na REGUA DA ITERACAO: dois blocos de geracoes diferentes NAO sao
% comparaveis sem carregar {min,range}. As linhas de BUSCA gravam assim mesmo
% (espaco_modelo="transformado" + C3, c238_instrument.m:77-82); a SONDA, nao — ela
% existe justamente para comparar o modelo ENTRE geracoes e ENTRE algoritmos, e o
% gabarito F do artefato esta em CRU. Por isso invertemos aqui, na origem:
%       mu_cru    = u .* yrange + ymin        (inversa exata de EIM.m:79)
%       sigma_cru = s .* yrange               (escala pura: min nao entra no desvio)
% e gravamos espaco_modelo="cru", SEM transf_tipo/transf_params (o C3 do §3.2 so
% se aplica a espaco transformado; depois da inversao nao ha nada a inverter).
% A transformacao e AFIM e EXATA, 100% read-only — nada realimenta a busca.
% `ymin` e o PRE-guard (EIM.m:66); `yrange` e o POS-guard max(range,eps) (EIM.m:78)
% — o MESMO par que a busca serializa em c238_instrument.m:71. Nao trocar a ordem:
% sob objetivo constante (guard_range, EIM.m:69-77) yrange vira eps, e usar o
% pre-guard aqui dividiria a regua por zero na leitura.
%
% ⚠ X: vai DIRETO ao preditor, espaco NATIVO, sem conversao. O GP_Predict normaliza
% internamente por model.lower_bound/upper_bound (GP_Predict.m:12-13), gravados em
% GP_Train.m:35-36 a partir dos lb/ub do Problem (EIM.m:95) = bounds nativos = o
% espaco do artefato da sonda. Sem sort, sem unique, sem clamp (I3: o join com o
% gabarito e POR POSICAO).
%
% Por que ESTE ponto (EIM.m:99, entre :98 e :100) — as 4 condicoes:
%   1. POS-FIT COMPLETO: os M GP_Train do laco :94-97 terminaram e `tempo_fit`
%      fechou em :98; `GP_obj` e EXATAMENTE o modelo que a busca usa em :103;
%   2. PRE-1a DECISAO: a 1a decisao e o Optimizer_GA (:102) — entre :99 e :102 nao
%      ha nada alem do comentario :100 e do `t1 = tic` :101;
%   3. PRE-1o CONSUMO DE RNG: grep de rand/randn/randi/lhsdesign/randperm em
%      GP_Train.m / GP_Predict.m / Infill_EIM.m / Paretoset.m = ZERO hits (o
%      fmincon sqp de GP_Train.m:11 e single-start deterministico, theta0 fixo em
%      EIM.m:96). O 1o consumidor da iteracao e Optimizer_GA.m:9 (lhsdesign),
%      depois do hook. O save/restore do RNG acontece assim mesmo (SondaState.m:151);
%   4. PRE-Problem.Evaluation: a unica avaliacao real do ciclo e EIM.m:116.
%   + I6: :99 fica APOS `toc(t0)` (:98) e ANTES de `t1 = tic` (:101) — e o UNICO
%     ponto do ciclo que nao contamina nem tempo_fit_s nem tempo_busca_s.
%
% ⚠ Nao passamos 'hp' no probe: o par e um NO-OP (SondaState.metaOf guarda meta.hp,
% mas SondaState.event so emite meta.modelo — SondaState.m:188-204). Os theta/lnL/
% sigma2/n do kriging vao em `modelo_hp` na linha `c238_gen` (S.7.1), nao aqui.

    d = Problem.data;
    if ~isfield(d, 'snd') || isempty(d.snd), return; end     % run sem sonda
    snd = d.snd;  buf = d.buf;  bud = d.bud;
    g = double(buf.gen);                       % o hook ja bumpou no topo do ciclo
    if g < 1, g = 1; end

    % ── fe_treino_max (DI-09/A1) ─────────────────────────────────────────────
    % LITERAL do §17.2: "maior fe_index no TREINO do modelo no momento do fit".
    % O treino do c238 e a Population INTEIRA (train_x = sample_x(ia,:), EIM.m:86-88,
    % sample_x = Population.decs, :62) — NAO ha subamostragem. A unica reducao e o
    % dedup bit-exato `unique(...,'stable')` (:86, guard do chol de GP_Train.m:22), e
    % 'stable' mantem a PRIMEIRA ocorrencia — que, como o FEBudget tambem dedupla por
    % X bit-a-bit (FEBudget.m:73-83), carrega o MESMO solution_id da duplicata. Logo
    % o dedup NAO altera o MAXIMO, e o atalho bud.fe-1 vale (solution_id == fe_index,
    % FEBudget.m:98-99; ids 0-based, presentes = 0..fe-1). Lido ANTES da Evaluation
    % deste ciclo (EIM.m:116) => o ftm do c238 e MONOTONICO (+1 por iteracao).
    % ⚠ Nota p/ a R4: o modelo FINAL do c238 nunca ve o ultimo FE — na iteracao 20D
    % o fit ocorre com bud.fe = maxfe-1, entao o ultimo ftm e 31D-3.
    ftm = bud.fe - 1;
    if ftm < 0, ftm = []; end

    % ── o disparo (cadencia k=2 + arm p/ a sonda final pos-Solve) ────────────
    fn = @(Xs) c238_sonda_rows(GP_obj, Xs, Problem.M, ymin, yrange);
    snd.probe(g, fn, ftm, 'modelo', "OK-Forrester");
end


function rows = c238_sonda_rows(GP_obj, Xs, M, ymin, yrange)
% As S=2000 linhas da ③, NA ORDEM DO ARTEFATO (join por posicao — §3.1).
%
% ⚠ CHUNKING OBRIGATORIO (passo=250). GP_Predict.m:24-27 calcula `Corr` e `Cov`
% INCONDICIONALMENTE — nao ha guard de nargout, e o MATLAB executa o corpo inteiro
% mesmo chamado com 2 saidas. Com n_test=2000 isso materializa ~6 temporarios
% 2000x2000 (temp1, temp1', temp2*temp2', o exp, um `eye(2000)` DENSO e a soma) =
% ~32 MB cada, pico transitorio ~190 MB POR CHAMADA e POR OBJETIVO, para descartar
% 100% do resultado. Em FLOPs e so ~7-8% do custo (o grosso util sao os solves
% L\R / L'\(L\R)); o problema e RAM/alocacao — o gate de memoria do M7. Com 250 o
% pico cai para <1 MB e a forma da chamada casa com a da busca (10*D pontos).
% Fatiar e ANALITICAMENTE EXATO: R e n_train x n_test e cada COLUNA de R depende
% so da linha correspondente de x (GP_Predict.m:17-19); u (:20) e mse (:21) sao
% coluna-a-coluna independentes. Logo a concatenacao preserva a ordem (I3).
% Reserva conhecida: o gemm (x.*theta)*X' pode usar blocagem BLAS diferente por
% shape e mudar o ultimo bit — nao perturba a busca (a sonda nao realimenta nada),
% so torna os valores nao-bit-comparaveis contra uma versao nao-chunkada.
    n  = size(Xs, 1);
    MU = zeros(n, M);
    SG = zeros(n, M);
    passo = 250;
    for j = 1:M
        for a = 1:passo:n
            b = min(a + passo - 1, n);
            [u, s] = GP_Predict(Xs(a:b, :), GP_obj{j});   % (test_x, model), 2 saidas
            % DI-17.6: inversao do min-max da ITERACAO -> espaco CRU do gabarito.
            MU(a:b, j) = u(:) .* yrange(j) + ymin(j);
            SG(a:b, j) = s(:) .* yrange(j);
        end
    end
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'mu', MU, 'sigma', SG, ...
        'pred_tipo', "valor", 'modelo_flag', "OK-Forrester", ...
        'espaco_modelo', "cru");     % ja invertido => sem transf_tipo/params
    % [DI-17.8] "cru" e o termo do contrato (DEF-C3), o unico que passa na
    % validacao de export.py:292 contra ESPACOS=("transformado","cru").
end
