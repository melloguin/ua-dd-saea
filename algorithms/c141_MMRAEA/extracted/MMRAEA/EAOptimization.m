function [PopDec,PopObj,nsub] = EAOptimization(PopDec,Problem,wmax,RModel,Fmodel,mS,FS)
% This function is written by Jiangtao Shen
% [R1-c141] 3o output nsub = |subpop1|,|subpop2| pos-ES_PDR (instrumentacao
% §17.5/S.7; so leitura — nenhuma decisao alterada, D97).
N = size(PopDec,1);
w1 = 1;
w2 = 1;
PopDec1 = PopDec;
PopDec2 = PopDec;
PopVel = zeros(N,Problem.D);
while w1 <= wmax
    % Fitness Prediction for Evolution
    Fit = zeros(size(PopDec1,1),1);
    for i = 1: size(PopDec1,1)
        Fit(i) = rbf_predict(Fmodel,FS,PopDec1(i,:));
    end
    [OffDec1,OffVel] = CSO(PopDec1,Fit,PopVel,Problem.lower,Problem.upper);
    PopVel = [PopVel;OffVel];
    PopDec1 = [PopDec1;OffDec1];
    % FN1 and FN2 prediction
    PopObj1 = zeros(size(PopDec1,1),Problem.M);
    for i = 1: size(PopDec1,1)
        for j = 1 : Problem.M
            PopObj1(i,j) = rbf_predict(RModel{j},mS,PopDec1(i,:));
        end
    end
    index1 = ES_PDR(PopObj1,Problem.N);
    PopDec1 = PopDec1(index1,:);
    PopVel = PopVel(index1,:);
    PopObj1 = PopObj1(index1,:);
    w1 = w1 + 1;
end

while w2 <= wmax
    % [R1-c141] porte 4.15 (L.7): era OperatorGA(PopDec2) — API 3.x. A assinatura
    % 4.15 e OperatorGA(Problem,Parent); matriz entra -> matriz sai (sem avaliar).
    % Defaults {1,20,1,20} = SBX proC=1/disC=20 + PM proM=1 (=1/d por variavel) —
    % exatamente o Balde B do c141 (codigo oficial; paper OK).
    OffDec2 = OperatorGA(Problem,PopDec2);
    PopDec2 = [PopDec2;OffDec2];
    PopObj2 = zeros(size(PopDec2,1),Problem.M);
    for i = 1: size(PopDec2,1)
        for j = 1 : Problem.M
            PopObj2(i,j) = rbf_predict(RModel{j},mS,PopDec2(i,:));
        end
    end
    index2 = ES_PDR(PopObj2,Problem.N);
    PopDec2 = PopDec2(index2,:);
    PopObj2 = PopObj2(index2,:);
    w2 = w2 + 1;
end

PopDec = [PopDec1;PopDec2];
PopObj = [PopObj1;PopObj2];
nsub = [size(PopDec1,1), size(PopDec2,1)];   % [R1-c141] |subpops| pos-ES_PDR

end