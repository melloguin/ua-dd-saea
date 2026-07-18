function [x_train, y_train, y_obj_e74] = DataProcess(tr_xx, tr_yy, N, D)
% [R1-e74] 3o output y_obj_e74 (leitura, NAO altera decisao — D97): os OBJETIVOS
% reais de cada linha de x_train, alinhados linha-a-linha — insumo do fix
% e74-ndsort-obj no ClassifierSelect (o stock perde o pareamento x_train<->obj
% ao devolver so a classe). tr_yy0_e74 preserva os valores antes do Inf-out.
tr_yy0_e74 = tr_yy;
y_obj_e74 = zeros(N,size(tr_yy,2));
y_train = zeros(N,1);
x_train = zeros(N,D);
Level = [0, round(N/10), round(N*2/5), round(N*4/5), N];
for i = 1:4
    Choose = [];
    [FrontNo,MaxFNo] = NDSort(tr_yy,Level(i+1)-Level(i));
    Choose = find(FrontNo < MaxFNo);
    Last_PS = find(FrontNo == MaxFNo);
    CD = CrowdingDistance(tr_yy(Last_PS,:),FrontNo(Last_PS));
    [~,index] = sort(CD,'descend');
    Choose = [Choose, Last_PS(index(1:(Level(i+1)-Level(i)-sum(FrontNo<MaxFNo))))];
    y_train(Level(i)+1:1:Level(i+1)) = i;
    x_train(Level(i)+1:1:Level(i+1),:) = tr_xx(Choose,:);
    y_obj_e74(Level(i)+1:1:Level(i+1),:) = tr_yy0_e74(Choose,:);
    tr_yy(Choose,:) = Inf;
end
end