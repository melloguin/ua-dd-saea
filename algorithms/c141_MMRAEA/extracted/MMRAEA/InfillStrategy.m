function [PopNew, info] = InfillStrategy(PopDec,PopObj,Dmodel,DS,Fmodel,FS,A1)
% [R1-c141] 2o output info = captura da CASCATA de 3 niveis p/ instrumentacao
% (§17.5/S.7: Fit1/2/3, ranks Q/U, nivel de saida, |fronts|, flag do guard L4).
% So LE o que a funcao ja computa — NENHUMA decisao alterada (D97). Niveis
% (I.7/L.7, gatilho = "resta >1 candidato" — sem u=5, v2.2):
%   1 = 1o front ND de pop-predita ∪ arquivo real, restrito a pop (exit se <=1);
%   2 = 1o front ND de [-Fit1, Fit2, -Fit3] (exit se <=1);
%   3 = front ND de (Quality, Uncertainty) ∪ argmax U  ->  batch variavel.
info = struct('nivel',1,'n_front1',0,'n_front2',0,'sde_guard',false, ...
              'Fit1',[],'Fit2',[],'Fit3',[],'Q',[],'U',[],'idx_sel',[]);
N = size(PopDec,1);
CPopObj = [PopObj;A1.objs];
[FN1,~] = NDSort(CPopObj,inf);
[~,index1] = find(FN1 == 1);
index2 = intersect(index1,1:N);
info.n_front1 = length(index2);
PopDec = PopDec(index2,:);
PopObj = PopObj(index2,:);
if length(index2)>1
    N = size(PopDec,1);
    info.nivel = 2;
    [Fit1, info.sde_guard] = calFitness(PopObj);   % [R1-c141] flag do guard L4 (D76)
    Fit2 = zeros(N,1);
    Fit3 = zeros(N,1);
    for i = 1 : N
        Fit2(i) = rbf_predict(Dmodel,DS,PopDec(i,:));
        Fit3(i) = rbf_predict(Fmodel,FS,PopDec(i,:));
    end
    [FN,~] = NDSort([-Fit1,Fit2,-Fit3],inf);
    PopDec = PopDec(FN==1,:);
    PopObj = PopObj(FN==1,:);
    Fit1 = Fit1(FN==1);
    Fit2 = Fit2(FN==1);
    Fit3 = Fit3(FN==1);
    info.n_front2 = size(PopDec,1);
    info.Fit1 = Fit1; info.Fit2 = Fit2; info.Fit3 = Fit3;
    if size(PopDec,1)>1
        info.nivel = 3;
        [~,s1] = sort(Fit1,'descend');
        [~,s2] = sort(Fit2);
        [~,s3] = sort(Fit3,'descend');
        Q1 = inf(size(PopDec,1),1);Q2 = inf(size(PopDec,1),1);Q3 = inf(size(PopDec,1),1);
        for i = 1:size(PopDec,1)
            Q1(s1(i)) = i;
            Q2(s2(i)) = i;
            Q3(s3(i)) = i;
        end
        Quality = Q1 + Q2 + Q3;
        Uncertainty = abs(Q1 - Q2) + abs(Q1 - Q3) + abs(Q2 - Q3);
        info.Q = Quality; info.U = Uncertainty;
        [FN,~] = NDSort([Quality,Uncertainty],inf);
        [~,index1] = find(FN == 1);
        [~,index2] = max(Uncertainty);
        index = unique([index1,index2]);
        info.idx_sel = index;
        PopNew = PopDec(index,:);
    else
        PopNew = PopDec;
    end
else
    PopNew = PopDec;
end

end
