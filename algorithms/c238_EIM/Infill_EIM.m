function [y,u,s,n_nan] = Infill_EIM(x,kriging_obj,non_dominated_front,criterion)
% [R1-c238] saidas extras u,s (ja computadas em :7-11) e n_nan — instrumentacao
% so-leitura (L.9/DEF-C2); o criterio y e as decisoes ficam INTACTOS.
% you can choose criterion as 'Euclidean', 'Maximin', or 'Hypervolume'
num_x = size(x,1);
% number of non-dominated points,number of objectives
[num_pareto,num_obj] = size(non_dominated_front);
% the kriging prediction and varince
u = zeros(num_x,num_obj);
s = zeros(num_x,num_obj);
for ii = 1 : num_obj
    [u(:, ii),s(:, ii)] = GP_Predict(x, kriging_obj{ii});
end
u_matrix = repelem(u,num_pareto,1);
s_matrix = repelem(s,num_pareto,1);
f_matrix = repmat(non_dominated_front,num_x,1);
EIM = (f_matrix - u_matrix).*normcdf((f_matrix - u_matrix)./s_matrix) + s_matrix.*normpdf((f_matrix - u_matrix)./s_matrix);
% [R1-c238] guard [IMPL do cartao c238]: s=0 em ponto de treino & f=u -> 0/0=NaN
% na matriz EIM; NaN=0 (sem melhoria esperada — bundle alg_c238_eim). Contado em
% n_nan p/ o evento `eim_nan` do .jsonl (§17.5) — logado, nunca silencioso.
n_nan = nnz(isnan(EIM));
EIM(isnan(EIM)) = 0;
% [T15.9/DEC-8, autor 2026-08-14] BUG LATENTE do codigo original (bussola D29:
% bug -> segue o artigo): com front NAO-DOMINADO de 1 ponto (num_pareto==1), o
% reshape produz vetor-LINHA 1xnum_x e o `min` SEM dimensao reduzia ao longo da
% linha -> ESCALAR em vez do vetor num_x-por-1 de fitness; o Optimizer_GA
% indexava o escalar e morria em MATLAB:badsubscript (28/28 celulas falhadas
% tinham n_front1==1; 0/617 celulas ok — laudo D0-LAUDO-C238-BADSUBSCRIPT.md).
% O `,[],1` explicita a dimensao: IDENTIDADE para num_pareto>=2 (min de matriz
% ja reduz pela dim 1) — as 617 celulas ok permanecem bit-exatas.
switch criterion
    case 'Euclidean'
        y = min(reshape(sqrt(sum(EIM.^2,2)),[num_pareto,num_x]),[],1)';
    case 'Maximin'
        y = min(reshape(max(EIM,[],2),[num_pareto,num_x]),[],1)';
    case 'Hypervolume'
        ref_point = 1.1*ones(1, num_obj);
        y = min(reshape(prod(ref_point-f_matrix+EIM,2)-prod(ref_point-f_matrix,2),[num_pareto,num_x]),[],1)';
end
