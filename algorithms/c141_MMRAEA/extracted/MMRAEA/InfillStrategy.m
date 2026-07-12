function PopNew = InfillStrategy(PopDec,PopObj,Dmodel,DS,Fmodel,FS,A1)
N = size(PopDec,1);
CPopObj = [PopObj;A1.objs];
[FN1,~] = NDSort(CPopObj,inf);
[~,index1] = find(FN1 == 1);
index2 = intersect(index1,1:N);
PopDec = PopDec(index2,:);
PopObj = PopObj(index2,:);
if length(index2)>1
    N = size(PopDec,1);
    Fit1 = calFitness(PopObj);
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
    if size(PopDec,1)>1
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
        [FN,~] = NDSort([Quality,Uncertainty],inf);
        [~,index1] = find(FN == 1);
        [~,index2] = max(Uncertainty);
        index = unique([index1,index2]);
        PopNew = PopDec(index,:);
    else
        PopNew = PopDec;
    end
else
    PopNew = PopDec;
end

end

