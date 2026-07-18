function [x_candidates, inst_e74] = Local_infill(Problem, Arc, num_infill, N, k_local, Gen_max2)
% [R1-e74] 2o output inst_e74 = instrumentacao de leitura (D97) — pop final do
% otimizador local + ŷ (RBF local) + Eucli (dist min em OBJETIVOS ao arquivo =
% pseudo-σ s3, a "incerteza geometrica" da selecao) + timing §17.6.
inst_e74 = struct('tempo_fit_s', 0, 'tempo_busca_s', 0, 'n_treino', 0, ...
    'spr', NaN, 'x_pop', [], 'y_pop', [], 'eucli', [], 'front_mask', [], ...
    'cand_eucli', []);
ParetoSolution = Arc.best.decs;    ParetoFront = Arc.best.objs;
D = size(ParetoSolution,2);
CrowdDis = CrowdingDistance(ParetoFront);
CrowdDis(CrowdDis == inf) = 0; % Need to be proved
[~, index] = sort(CrowdDis,'descend');
if length(index) >= num_infill
    RefPoint = ParetoSolution(index(1:num_infill),:);
    RefObj = ParetoFront(index(1:num_infill),:);
else
    RefPoint = ParetoSolution(index,:);
    RefObj = ParetoFront(index,:);
end
x_candidates = [];
for i = 1:min(length(index),num_infill)
    distance = pdist2(RefObj(i,:), Arc.objs);
    [~,index] = sort(distance);
    x_train = Arc(index(1:N)).decs;
    y_train = Arc(index(1:N)).objs;
    [x_parent, y_parent] = SelectTrainData(Arc, k_local);
    x_lb = min(x_train);    x_ub = max(x_train);
    ghxd = real(sqrt(x_train.^2*ones(size(x_train'))+ones(size(x_train))*(x_train').^2-2*x_train*(x_train')));
    spr = max(max(ghxd))/(D*N)^(1/D);
    tf0_e74 = tic;               % [R1-e74] §17.6 (fit da RBF local; decisao intacta)
    net = newrbe(x_train',y_train',spr);
    inst_e74.tempo_fit_s = inst_e74.tempo_fit_s + toc(tf0_e74);
    inst_e74.n_treino = size(x_train,1);  inst_e74.spr = spr;
    tb0_e74 = tic;
    for j = 1: Gen_max2
        x_offspring = OperatorDE(Problem, repmat(RefPoint(i,:), N, 1), x_parent(randi(k_local,1,N),:), x_parent(randi(k_local,1,N),:), {0.5,0.5,1,20});
        x_offspring = max(min(x_offspring, x_ub),x_lb);
        y_offspring = zeros(k_local, Problem.M);
        y_offspring = sim(net,x_offspring')';
        
        Mediate_dec = [x_parent; x_offspring];
        Mediate_obj = [y_parent; y_offspring];
        [FrontNo,MaxFNo] = NDSort(Mediate_obj,N);
        Choose = find(FrontNo < MaxFNo);
        Last_PS = find(FrontNo == MaxFNo);
        CD = CrowdingDistance(Mediate_obj(Last_PS,:),FrontNo(Last_PS));
        [~,index] = sort(CD,'descend');
        Choose = [Choose, Last_PS(index(1:(N-sum(FrontNo<MaxFNo))))];
        x_parent = Mediate_dec(Choose,:);
        y_parent = Mediate_obj(Choose,:);
    end
    [FrontNo,MaxFNo] = NDSort([y_train; y_offspring],Inf);
    index = find(FrontNo(N+1:end)==1);
    % [R1-e74] instrumentacao POS-loop (leitura pura — D97): pop final + ŷ +
    % Eucli por offspring (mesma convencao do criterio abaixo) + front-mask.
    inst_e74.tempo_busca_s = inst_e74.tempo_busca_s + toc(tb0_e74);
    inst_e74.x_pop = [inst_e74.x_pop; x_offspring];
    inst_e74.y_pop = [inst_e74.y_pop; y_offspring];
    inst_e74.eucli = [inst_e74.eucli; min(pdist2(Arc.objs, y_offspring),[],1)'];
    fmask_e74 = false(size(y_offspring,1),1);  fmask_e74(index) = true;
    inst_e74.front_mask = [inst_e74.front_mask; fmask_e74];
    if ~ isempty(index)
        Eucli = min(pdist2(Arc.objs, y_offspring(index,:)));
        [~, Choose] = max(Eucli);
        % [R1-e74] e74-mask (🔴 D76 — ARTIGO): 'Choose' indexa o SUBCONJUNTO
        % 'index' (front nivel-1 dos offspring), nao as linhas de x_offspring —
        % o stock devolvia a linha errada da matriz de offspring.
        x_candidates = [x_candidates; x_offspring(index(Choose),:)];
        inst_e74.cand_eucli = [inst_e74.cand_eucli; Eucli(Choose)];
    end
end
end