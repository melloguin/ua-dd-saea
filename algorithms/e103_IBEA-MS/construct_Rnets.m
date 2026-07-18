function Rnets = construct_Rnets(pop, Global)

    PopObj     = objs(pop);
    % [R1-e103 · ancora e103-centros-D93] capacidade da RBFN = f(TAMANHO REAL
    % do dataset), com o n INJETADO pelo wrapper (31D-1 no principal; 2k/50k
    % no sweep). O `Global.D*11-1` stock era o n do PAPER — com o nosso
    % dataset 31D-1 a rede ficava subdimensionada e o eixo do sweep colapsava
    % (capacidade fixa com dado variavel — o "patch NO-OP" do Anexo S partia
    % de premissa falsa; D93 supersede).
    center_num = ceil(sqrt(Global.n_dataset));
    RName      = 'the_gaussian';
    Rnets.centers= get_center(pop, Global, center_num);          %Calculate the center points
    Rnets.sigma  = max(pdist(Rnets.centers))*5;
    Rnets.name   = RName;
    Z = get_Z(pop, RName, Rnets, Global);
    % [R1-e103 · §22-e103] inv(Z'Z)*Z' -> mldivide (quase-singularidade: mesmo
    % LSQ, sem inversa explicita; warnings de rank/singularidade sao ESPERADOS
    % com o spread 5*max(pdist) — documentados e CONTADOS no e103_setup, nunca
    % silenciados).
    Rnets.weight = (Z'*Z)\(Z'*PopObj);
    
end