function [PopObj, PopStd, nneg] = Estimate(PopDec, net, Params, M)
% [R1-e7] 3o output nneg (instrumentacao SO-LEITURA, D97): nº de entradas
% s2-mu.^2 < 0 clampadas pelo guard da :26 (erro float da variancia
% populacional das T=100 passagens — PopStd viraria COMPLEXO sem o guard,
% hazard N.3). Nenhuma decisao alterada.

    %tau=Params.tau;
    %interval=Params.interval;
    % Calculate the objective values according to the decision
    % variables, note that here the objective values of multiple
    % solutions are calculated at the same time
    ps=Params.ps;qs=Params.qs;
    x=mapminmax('apply',PopDec',ps);x=x';


        for i=1:100
            sum_y=testNet(x, net, Params);
            sum_y=mapminmax('reverse',sum_y',qs);sum_y=sum_y';
            sum_ysq=sum_y.^2;
            result(i).y=sum_y;
            result(i).ysq=sum_ysq;
        end

    %Take the result of the most recent interval
    array1=[result.y];array2=[result.ysq];
    for i=1:M
        mu(:,i)=mean(array1(:,i:M:end),2);
        s2(:,i)=mean(array2(:,i:M:end),2);
    end
    % [R1-e7] guard (N.3): var populacional pode dar <0 por erro float ->
    % sqrt complexo silencioso. Clamp a 0 + contagem (logada como 'std_neg').
    var_pop=s2-mu.^2;
    nneg=sum(var_pop(:)<0);
    std=sqrt(max(var_pop,0));

    %alpha=2;
    PopObj=mu;%-alpha*std;
    PopStd=std;
end