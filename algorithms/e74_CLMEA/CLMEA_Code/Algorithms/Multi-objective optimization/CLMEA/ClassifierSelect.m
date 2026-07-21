function [x_candidate, inst_e74] = ClassifierSelect(Problem, Arc, N, num_infill)
tr_xx = Arc.decs;
tr_yy = Arc.objs;
[x_train, y_train, y_obj_e74] = Data_Process(tr_xx, tr_yy, N, Problem.D);
distance = pdist2(x_train,x_train);
spr = max(max(distance))/sqrt(2*size(x_train,1));
tfit_e74 = tic;               % [R1-e74] §17.6 (fit da PNN; nao altera decisao — D97)
net_pnn = newpnn(x_train',ind2vec(y_train'),spr);
tfit_e74 = toc(tfit_e74);
% [DI09-R1c] SONDA s1 (DI-09/§17.2.2): pos-fit, pre-1a-decisao, pre-RNG (o 1o
% consumo sao os randi/OperatorDE abaixo) e pre-Evaluation (CLMEA.m); FORA dos
% tic/toc de fit e de busca. Read-only (D97), 0 FE. Devolve o fe_treino_max da
% subamostra estratificada (so calculavel AQUI — DI-09/A1) e ele viaja ao
% e74_instrument dentro do inst_e74 ('ftm').
ftm_e74 = e74_sonda(Problem, 's1', net_pnn, x_train, 'spr', spr, 'tempo_fit_s', tfit_e74);
tbusca_e74 = tic;
Parent = x_train;
% [R1-e74] e74-ndsort-obj (fidelidade 🔴 — ARTIGO/D30/D76): o rotulo inicial dos
% pais e o nivel de nao-dominancia dos OBJETIVOS reais (y_obj_e74, alinhado a
% x_train) — o stock rodava o ND-sort sobre os vetores de DECISAO (Parent), um
% espaco sem relacao de dominancia (bug confirmado vs paper; S.2#confirmadas).
[y_label,~] = NDSort(y_obj_e74,inf);
y_label(y_label > 4) = 4;
initial_1st = find(y_label == 1);
initial_2nd = find(y_label <= 2);
Offspring = OperatorDE(Problem, Parent(initial_1st(randi(length(initial_1st),N,1)),:), Parent(initial_1st(randi(length(initial_1st),N,1)),:), Parent(initial_2nd(randi(length(initial_2nd),N,1)),:), {0.5,0.5,1,20});
count = 0;
% Evolve offspring
y_label = vec2ind(sim(net_pnn,Offspring'));
while sum(y_label == 1)<0.9*N
    index_1st = find(y_label == 1);
    index_2nd = find(y_label <= 2);
    if ~isempty(index_1st)
        Offspring = OperatorDE(Problem, Parent(index_1st(randi(length(index_1st),N,1)),:),Parent(index_1st(randi(length(index_1st),N,1)),:), Parent(index_2nd(randi(length(index_2nd),N,1)),:), {0.5,0.5,1,20});
    else
        Offspring = OperatorDE(Problem, x_train(initial_1st(randi(length(initial_1st),N,1)),:), x_train(initial_1st(randi(length(initial_1st),N,1)),:), x_train(initial_2nd(randi(length(initial_2nd),N,1)),:), {0.5,0.5,1,20});
    end
    Offspring_label = vec2ind(sim(net_pnn,Offspring'));
    Parent(Offspring_label<=y_label,:) = Offspring(Offspring_label<=y_label,:);
    y_label = Offspring_label;
    count = count + 1;
    if count > 50
        break;
    end
end
[~,index] = sort(min(pdist2(Parent(y_label==1,:), Arc.decs),[],2),'descend');
if length(index)>=num_infill
    x_candidate = Parent(index(1:num_infill),:);
else
    x_candidate = Parent(index,:);
end
% [R1-e74] instrumentacao POS-decisao (leitura pura — D97; nada acima muda):
% pop final da estrategia 1 + classe PNN por membro (re-sim de leitura, 0 FE) +
% pseudo-σ s1 = dist minima em DECISAO ao arquivo (o criterio da selecao acima) +
% telemetria do desalinhamento mascara(Offspring)×linhas(Parent) — o "fix
% opcional re-sim" do bundle NAO e aplicado (D81): so medimos o efeito.
tbusca_e74 = toc(tbusca_e74);
classe_parent_e74 = vec2ind(sim(net_pnn,Parent'));
dist_dec_e74 = min(pdist2(Parent, Arc.decs),[],2);
if isempty(x_candidate)      % edge STOCK: loop sem nivel-1 -> candidato vazio
    cand_classe_e74 = [];  cand_dist_e74 = [];
else
    cand_classe_e74 = vec2ind(sim(net_pnn,x_candidate'));
    cand_dist_e74 = min(pdist2(x_candidate, Arc.decs),[],2);
end
inst_e74 = struct( ...
    'count', count, 'frac_n1', sum(y_label==1)/numel(y_label), ...
    'spr', spr, 'n_treino', size(x_train,1), ...
    'tempo_fit_s', tfit_e74, 'tempo_busca_s', tbusca_e74, ...
    'ftm', ftm_e74, ...       % [DI09-R1c/DI-09-A1] fe_treino_max do fit desta estrategia
    'x_pop', Parent, 'classe_pop', classe_parent_e74(:), ...
    'dist_dec', dist_dec_e74(:), ...
    'n_desalinhado', sum(classe_parent_e74(:) ~= y_label(:)), ...
    'cand_classe', cand_classe_e74(:), 'cand_dist', cand_dist_e74(:), ...
    'flag_copia', any(cand_dist_e74 == 0));
end