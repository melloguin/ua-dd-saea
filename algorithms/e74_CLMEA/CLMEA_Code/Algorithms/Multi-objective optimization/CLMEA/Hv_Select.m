function [x_candidates, inst_e74] = Hv_Select(Problem, Arc, N, num_infill, Gen_max1)
x_archive = Arc.decs;    y_archive = Arc.objs;
num_sample = size(x_archive,1);
D = size(x_archive,2);
% Build surrogate model
ghxd=real(sqrt(x_archive.^2*ones(size(x_archive'))+ones(size(x_archive))*(x_archive').^2-2*x_archive*(x_archive')));
spr = max(max(ghxd))/(D*num_sample)^(1/D);
tfit_e74 = tic;              % [R1-e74] §17.6 (fit da RBF global no arquivo INTEIRO —
net = newrbe(x_archive',y_archive',spr);   % o O(n³)/iter da curva de escalabilidade)
tfit_e74 = toc(tfit_e74);
% [DI09-R1c] SONDA s2 (DI-09/§17.2.2): pos-fit, pre-RNG (o 1o consumo sao os
% randperm do laco abaixo; SelectTrainData/sim nao consomem) e pre-Evaluation
% (CLMEA.m); FORA dos tic/toc de fit e de busca. Read-only (D97), 0 FE. O
% fe_treino_max usa o atalho bud.fe-1 (treino = arquivo INTEIRO — e74_sonda) e
% viaja ao e74_instrument dentro do inst_e74 ('ftm').
ftm_e74 = e74_sonda(Problem, 's2', net, x_archive, 'spr', spr, 'tempo_fit_s', tfit_e74);
tbusca_e74 = tic;
[x_parent, ~] = SelectTrainData(Arc, N);
y_parent = sim(net,x_parent')';
i = 0;
while i < Gen_max1
    index1 = randperm(N);    index2 = randperm(N);
    x_offspring = OperatorDE(Problem,x_parent,x_parent(index1,:),x_parent(index2,:),{1,0.5,1,20});
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
    i = i + 1;
end
[FrontNo,~] = NDSort(y_parent,inf);
front_mask_e74 = (FrontNo==1)';      % [R1-e74] marca os membros do pseudo-front na pop final
Pseudo_PS = x_parent(FrontNo==1,:);
Pseudo_PF = y_parent(FrontNo==1,:);
[FrontNo,~] = NDSort(Arc.objs,inf);
Ymin = min(y_archive(FrontNo == 1,:));    Ymax = max(y_archive(FrontNo == 1,:));
% [R1-e74] D74: o CalHV interno roda NORMALIZADO — min-max do front-1 do arquivo
% corrente (Ymin/Ymax acima = ideal/nadir estimados, leitura do D69) e ref-point
% 1,1 por coordenada NO ESPACO NORMALIZADO, a cada chamada. O RefPoint stock
% ((Ymax-Ymin)*1.2, escala CRUA) degenera com objetivos de escala grande/negativa
% (BBOB — hazard PP L: a renormalizacao interna do CalHV descarta coord>1).
% CalHV.m fica INTOCADO. range<=0 (front degenerado, ex. 1 ponto) NAO e
% consertado — so logado (edge fora do paper; e74_instrument emite hv_range0).
range_e74 = Ymax - Ymin;
norm_e74 = @(Y) (Y - repmat(Ymin,size(Y,1),1))./repmat(range_e74,size(Y,1),1);
RefPoint = 1.1*ones(1,size(y_archive,2));
hv_base_e74 = CalHV(norm_e74(y_archive(FrontNo==1,:)),RefPoint);  % HV do arquivo (p/ HV_gain)
x_candidates = [];
score_e74 = [];  chosen_e74 = [];
for i = 1:num_infill
    score = [];
    if ~isempty(Pseudo_PS)
        for j = 1:size(Pseudo_PS,1)
            x_hv = [x_archive; Pseudo_PS(j,:)];    y_hv = [y_archive; Pseudo_PF(j,:)];
            [FrontNo,~] = NDSort(y_hv,inf);
            score(j) = CalHV(norm_e74(y_hv(FrontNo==1,:)),RefPoint);   % [R1-e74] D74
        end
        [~,index] = max(score);
        score_e74 = score;  chosen_e74 = index;   % [R1-e74] leitura (num_infill=1)
        x_candidates(i,:) = Pseudo_PS(index,:);
        x_archive = [x_archive;Pseudo_PS(index,:)];
        y_archive = [y_archive;Pseudo_PF(index,:)];
        Pseudo_PS(index,:) = [];
        Pseudo_PF(index,:) = [];
    end
end
% [R1-e74] instrumentacao POS-decisao (leitura pura — D97): pop final da DE
% interna + μ_RBF + pseudo-front/scores CalHV (D74) + params da normalizacao.
inst_e74 = struct( ...
    'spr', spr, 'n_treino', num_sample, ...
    'tempo_fit_s', tfit_e74, 'tempo_busca_s', toc(tbusca_e74), ...
    'ftm', ftm_e74, ...       % [DI09-R1c/DI-09-A1] fe_treino_max do fit desta estrategia
    'x_pop', x_parent, 'y_pop', y_parent, 'front_mask', front_mask_e74(:), ...
    'Ymin', Ymin, 'Ymax', Ymax, 'range0', any(range_e74 <= 0), ...
    'hv_base', hv_base_e74, 'score', score_e74, 'chosen', chosen_e74);
end
