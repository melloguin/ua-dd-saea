function e103_sonda(Global, KModel, Rnets)
% e103_sonda — os DOIS blocos da SONDA CANONICA (DI-09/§17.2.2) do e103 IBEA-MS.
% O UNICO config OFFLINE da R1. Chamado de e103_instrument('setup', ...) logo
% APOS o fit dos dois modelos e ANTES de qualquer decisao da busca. READ-ONLY:
% nao altera nenhuma decisao (D97) e nao gasta FE (o orcamento ja foi TODO
% consumido na carga do dataset, experiment.m:1849-1855).
%
% ── SEMANTICA CONTRATADA (CONTRATO_DE_DADOS §3.2, linha "b3, c141, e7, c238,
%    e103, ...") = mu (e sigma ONDE HOUVER) POR OBJETIVO, pred_tipo="valor".
%
% ── CADENCIA: ZERO blocos por ciclo. [DI-13.5, decisao do autor] OFFLINE = 1
%    bloco POR MODELO TREINADO, e o e103 treina DOIS modelos UMA vez cada, antes
%    do laco (IBEAMS.m:43 construct_kriging, :46 construct_Rnets). Logo:
%      BLOCO 1  modelo_flag="Kriging-DACE"  mu=predictor, sigma=sqrt(max(MSE,0))
%      BLOCO 2  modelo_flag="RBFN"          mu=Z*weight,  sigma AUSENTE => NULL
%    Cada bloco = S=20.000 linhas (o artefato INTEIRO — load_sonda(...,'offline')
%    nao fatia; experiment.m:2489-2495), disparadas via `snd.probeOffline(...)`.
%    Esse metodo NAO arma: nao existe hard-stop capaz de matar o laco do e103
%    (nao ha Problem.Evaluation em lugar nenhum; qualquer FE na busca e violacao
%    D90 e o run para-e-loga, experiment.m:1877-1888), logo nao ha "ultima
%    geracao" a recuperar e um finalProbe defensivo e no-op garantido.
%
% ── `geracao` = NULL nos dois blocos. [DI-13.5 + adendo da torre, RATIFICADO]
%    O modelo treina UMA vez, ANTES do laco — nao ha geracao a que pertencer, e
%    NULL e mais honesto que um `0`/`1` inventado. A infra transversal foi
%    adequada para expressa-lo (commit da infra deste cartao):
%      · SondaState.probeOffline dispara com g=NaN, o PORTADOR do NULL;
%      · RunBuffer.addGeneration trata NaN como "geracao nula" e NAO como "sem
%        geracao" (um `[]` cairia no early-return e DESCARTARIA o bloco inteiro);
%      · write_surrogate mantem a coluna em double quando ha qualquer NaN
%        (int32(NaN) = 0 em MATLAB faria o bloco virar "geracao 0" em silencio).
%    Regressao no config `stub`: bloco offline de 20.000 no MESMO arquivo das
%    linhas de busca, conferindo os DOIS lados da coluna apos o export.

    if ~isfield(Global, 'inst') || isempty(Global.inst), return; end
    inst = Global.inst;
    if ~isfield(inst, 'snd') || isempty(inst.snd), return; end   % run sem sonda
    snd = inst.snd;  bud = inst.bud;

    % ── fe_treino_max (DI-09/A1) ─────────────────────────────────────────────
    % LITERAL do §17.2: "maior fe_index no TREINO do modelo no momento do fit".
    % Aqui o atalho `bud.fe-1` VALE (molde c141_sonda.m:40) e nao ha subamostra
    % a percorrer com solutionIdOf: os DOIS modelos treinam sobre o dataset
    % INTEIRO — IBEAMS.m:40-41 monta Population com Global.data.X0/F0 e a passa
    % igual a construct_kriging (:43) e a construct_Rnets (:46); o k-means de
    % construct_Rnets.m:12 escolhe apenas os CENTROS, nao poda o treino (os pesos
    % LSQ de :20 usam o Z da Population inteira). Como solution_id == fe_index
    % (FEBudget.m:98-99) e o orcamento inteiro ja foi consumido na carga, com
    % assert bud.fe == maxfe (experiment.m:1853-1855), o maior fe_index existente
    % e bud.fe-1 = n_ds-1 = 31D-2. CONSTANTE no run e IDENTICO nos dois blocos
    % (trivialmente monotonico) — o inverso do caso b1/b4/c217.
    ftm = bud.fe - 1;
    if ftm < 0, ftm = []; end                      % => NULL na ③

    M = double(Global.M);

    % ── BLOCO 1: Kriging-DACE ────────────────────────────────────────────────
    % probeOffline => geracao NULL, sem armar (ver o cabecalho).
    fnK = @(Xs) e103_sonda_rows_kriging(KModel, Xs, M);
    snd.probeOffline(fnK, ftm, 'modelo', "Kriging-DACE");

    % ── BLOCO 2: RBFN ────────────────────────────────────────────────────────
    fnR = @(Xs) e103_sonda_rows_rbfn(Rnets, Xs, M);
    snd.probeOffline(fnR, ftm, 'modelo', "RBFN");
end


function rows = e103_sonda_rows_kriging(KModel, Xs, M)
% As S=20.000 linhas da ③ do Kriging, NA ORDEM DO ARTEFATO (join por posicao).
% Replica kriging_cal.m:7-9 (loop j=1:M com [Objs(:,j),MSE(:,j)] = predictor)
% SEM o PopStruct de :10.
%
% ⚠ CHUNKING OBRIGATORIO (memoria): o ramo multi-site do predictor materializa
% `dx` de (mx*m) x D (predictor.m:101-105) e o `r` de mesma cardinalidade
% (:108). Com mx=20.000 isso e ~4,5 GB POR OBJETIVO, POR CHAMADA no ZDT1
% (m=929, D=30) — ~200x o que a busca faz (kriging_cal com 100 linhas). Fatiar e
% BIT-EQUIVALENTE: `dx` e montado LINHA A LINHA (:102-105), f=regr(x) e por
% linha, e sy/y/rt=C\r/u=G\(...)/colsum sao todos COLUNA-A-COLUNA (:107-119).
% passo=512 e o mesmo SONDA_CHUNK dos outros stacks (standalone_harness.py:133,
% botorch_harness.py:297) — simetria cross-stack, ~115 MB no pior caso.
%
% ⚠ ARMADILHA DO RAMO SINGLE-SITE: predictor.m:38 (`if min(sx)==1 & n>1`) desvia
% para o ramo de UM ponto quando o chunk tem UMA linha — e nesse ramo o SEGUNDO
% retorno deixa de ser o MSE e passa a ser o Jacobiano des-escalado (:61-63), com
% o MSE virando o TERCEIRO (:73). Isso corromperia sigma EM SILENCIO. Dai o
% absorve-cauda abaixo (nenhum chunk sai com 1 linha) e o assert de entrada.
%
% ⚠ EXATAMENTE 2 outputs: com nargout>2 o ramo batch imprime
% 'WARNING from PREDICTOR' a cada chunk (predictor.m:120-122).
    n = size(Xs, 1);
    assert(n > 1, 'e103_sonda: bloco com %d linha(s) cairia no ramo single-site do predictor', n);
    MU = zeros(n, M);
    SG = zeros(n, M);
    passo = 512;
    for j = 1:M
        md = KModel(j).md;
        a = 1;
        while a <= n
            b = min(a + passo - 1, n);
            if (n - b) == 1, b = n; end            % nunca deixar cauda de 1 linha
            [yb, mseb] = predictor(Xs(a:b, :), md);
            MU(a:b, j) = yb(:);
            % MESMO guard da busca (e103_instrument.m:90 / sigma_dict do
            % manifesto, experiment.m:1951): MSE<0 e erro de float em ponto de
            % treino. O clamp existe SO na ③ — o mecanismo do algoritmo (o
            % JudgeModel, que consome o MSE cru) fica intocado.
            SG(a:b, j) = sqrt(max(mseb(:), 0));
            a = b + 1;
        end
    end
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'mu', MU, 'sigma', SG, ...
        'pred_tipo', "valor", 'modelo_flag', "Kriging-DACE", ...
        'espaco_modelo', "cru");
end


function rows = e103_sonda_rows_rbfn(Rnets, Xs, M)
% As S=20.000 linhas da ③ da RBFN, NA ORDEM DO ARTEFATO.
% Replica RBFN_cal.m:6-9 (kernel por NOME, bias de uns, Objs = Z*weight + zeros)
% SEM o PopStruct de :11. O `feval` faz o mesmo despacho por nome que o `eval` de
% RBFN_cal.m:7 — mesma funcao chamada, mesmos argumentos, sem construir codigo.
%
% SEM chunking, e de proposito: Z e S x (center_num+1) com
% center_num = ceil(sqrt(n_dataset)) (construct_Rnets.m:10) — 31 colunas no ZDT1
% (n_ds=929) e 224 no pior caso do sweep (n_ds=50k), i.e. no maximo ~36 MB. Nao
% ha materializacao (mx*m) x D como no DACE. Manter a chamada UNICA mantem a
% aritmetica identica a da busca linha a linha.
%
% sigma AUSENTE: interpolante LSQ, sem incerteza => NULL na ③.
    Z = feval(Rnets.name, Xs, Rnets.centers, Rnets.sigma);
    Z = [Z, ones(size(Z, 1), 1)];
    Objs = zeros(size(Xs, 1), M);
    MU = Z*Rnets.weight + Objs;
    rows = RunBuffer.mkSurrogateRows(Xs, ...
        'mu', MU, ...
        'pred_tipo', "valor", 'modelo_flag', "RBFN", ...
        'espaco_modelo', "cru");
end
