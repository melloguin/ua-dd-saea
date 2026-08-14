function out = ddmop7_value_local(X, acao)
%DDMOP7_VALUE_LOCAL  Avaliador CRU do DDMOP7 na rota R1 (caso 3 da D102.5).
%
%   F = ddmop7_value_local(X)   avalia X (N x 17) no DDMOP7.p oficial e
%   devolve F (N x 2). NAO ha Python nenhum na avaliacao: o harness MATLAB
%   chama o .p DIRETO, no MESMO processo. E o desvio "ANTES da ponte" do
%   cartao T15.7 §2 — para problema=='DDMOP7' o evalFcn dos run_* aponta
%   para ca (ver `eval_fcn_por_x` em experiment.m) em vez de
%   py.problems.evaluate_problem.
%
%   CONTABILIDADE (D89): esta funcao NAO conta FE, NAO deduplica, NAO grava
%   catalogo e NUNCA levanta PlatEMO:Termination — o FEBudget do harness e a
%   UNICA autoridade de orcamento (o molde DDMOP7_evalFcn.m da arvore de
%   fusao tinha contador proprio; ele NAO veio, de proposito). Ficam SO os
%   guards que nao sao contabilidade:
%     * forma/finito da saida do .p (para-e-loga, D81);
%     * teto de 600 chamadas de 'value' por processo (D88.5) — contador local
%       `chamadasP` que PARA com erro claro ANTES de o .p abortar sozinho.
%       Com o FEBudget cortando em 526 + fantasma do construtor (DEF-A3),
%       sobra folga (527 < 600); nao se confia, checa-se.
%
%   SETUP PERSISTENTE DO .p [MEDIDO, B-26 2026-08-13]. O DDMOP7.p EXIGE um
%   DDMOP7('init') por processo antes de qualquer 'value' (estado
%   persistente; 'value' a frio morre num assert interno). O init NAO consome
%   o contador de 600 (medido: 4 inits = 744 draw-points + value OK) e o
%   sorteio devolvido e DESCARTADO — o DoE do run vem BIT-A-BIT do artefato
%   congelado (D63/D88.1), jamais deste init. Mesmo fix da ponte Python
%   (src/ddmop7_bridge.py) — as duas rotas pareadas.
%
%   PASTA DO .p: `getenv('UA_DD_SAEA_DDMOP_DIR')` -> default
%   `~/DDMOP/DDMOP_Exp/Problems`. Recusa `DDMOP_Plat` (essa copia exige o
%   objeto GLOBAL do PlatEMO — D88.5). O .p resolve seus dados relativos ao
%   pwd (validado no probe v6), entao cada chamada faz cd para a pasta e
%   VOLTA (onCleanup) — o pwd do harness nunca fica trocado (os exports com
%   dataRoot relativo continuam caindo no lugar certo).
%
%   ACOES DE TESTE (segundo argumento; NUNCA usadas em producao):
%     ddmop7_value_local([], 'chamadas')          -> contador atual (double)
%     ddmop7_value_local([], 'reset')             -> zera o estado persistente
%     ddmop7_value_local(n,  'forca_contador')    -> crava o contador em n
%   O 'forca_contador' existe para o CONTROLE NEGATIVO do teto de 600
%   (tests/test_t15_ddmop7_matlab.py): forcar >600 tem de dar erro claro.

D          = 17;
M          = 2;
P_CODE_CAP = 600;              % teto interno do DDMOP7.p (medido no probe)

persistent pronto chamadasP dirP

% ── acoes de teste ──────────────────────────────────────────────────────────
if nargin >= 2
    switch char(acao)
        case 'chamadas'
            if isempty(chamadasP), chamadasP = 0; end
            out = chamadasP;
            return
        case 'reset'
            pronto = []; chamadasP = []; dirP = [];
            out = [];
            return
        case 'forca_contador'
            chamadasP = double(X);
            out = chamadasP;
            return
        otherwise
            error('DDMOP7:AcaoDesconhecida', ...
                  'acao desconhecida: %s (esperado chamadas|reset|forca_contador)', ...
                  char(acao));
    end
end

% ── setup por processo (1a chamada): pasta + guards + init descartado ───────
if isempty(pronto)
    d = strtrim(getenv('UA_DD_SAEA_DDMOP_DIR'));
    if isempty(d)
        if ispc, home = getenv('USERPROFILE'); else, home = getenv('HOME'); end
        d = fullfile(home, 'DDMOP', 'DDMOP_Exp', 'Problems');
    end
    dd = dir(d);
    if isempty(dd)
        error('DDMOP7:PastaAusente', ...
            ['pasta do DDMOP7.p nao encontrada: %s -- exporte ' ...
             'UA_DD_SAEA_DDMOP_DIR ou provisione ~/DDMOP/DDMOP_Exp/Problems ' ...
             '(D88.5)'], d);
    end
    dirAbs = dd(1).folder;
    if ~isempty(strfind(dirAbs, 'DDMOP_Plat'))                     %#ok<STREMP>
        error('DDMOP7:PastaErrada', ...
            ['recusando DDMOP_Plat: essa copia exige o objeto GLOBAL do ' ...
             'PlatEMO. Use a interface standalone DDMOP_Exp/Problems (D88.5).']);
    end
    % exist() devolve 2 OU 6 (P-code) para o MESMO .p conforme o pwd --
    % medido no B-26; 6 = "e P-code", exatamente o esperado aqui.
    if ~ismember(exist(fullfile(dirAbs, 'DDMOP7.p'), 'file'), [2 6])
        error('DDMOP7:PCodeAusente', 'DDMOP7.p nao encontrado em %s', dirAbs);
    end
    addpath(dirAbs);
    if isempty(chamadasP), chamadasP = 0; end

    prev = cd(dirAbs);
    volta = onCleanup(@() cd(prev));          % devolve o pwd MESMO em erro
    clear DDMOP7;                             % estado zerado e conhecido
    descarteInit = DDMOP7('init');                                 %#ok<NASGU>
    clear volta;                              % cd(prev) AGORA
    dirP = dirAbs;
    pronto = true;
end

% ── avaliacao ───────────────────────────────────────────────────────────────
X = reshape(X, [], D);
n = size(X, 1);

if chamadasP + n > P_CODE_CAP
    error('DDMOP7:TetoPCode', ...
        ['%d chamadas ao DDMOP7.p neste processo passariam o teto de %d -- ' ...
         'UM processo MATLAB por run (D88.5)'], chamadasP + n, P_CODE_CAP);
end

prev = cd(dirP);
volta = onCleanup(@() cd(prev));              % devolve o pwd MESMO em erro
F = DDMOP7('value', X);
clear volta;                                  % cd(prev) AGORA
chamadasP = chamadasP + n;

if ~isequal(size(F), [n M])
    error('DDMOP7:FormaInesperada', ...
        'DDMOP7(''value'') devolveu %s, esperado [%d %d] -- para-e-loga (D81)', ...
        mat2str(size(F)), n, M);
end
if ~all(isfinite(F(:)))
    error('DDMOP7:NaoFinito', ...
        'DDMOP7(''value'') devolveu nao-finito -- para-e-loga (D81)');
end
out = F;
end
