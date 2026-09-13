function [net, Params] = trainmodel(tr_x, tr_y, Params)

    V=size(tr_x,2);M=size(tr_y,2);
    neuronN=40;N=size(tr_x,1);bias1=0.1;bias2=0;
    Params.neuronN=neuronN;
    % [R1-e7] dropout 0.1 do PAPER (fidelidade D30 - ARTIGO; codigo shipped
    % usava [0.2,0.5] de Srivastava): entrada+oculta = 0.1, invertido, ATIVO
    % na inferencia (mecanismo da incerteza EDN - altera o sigma que a tese mede).
    Params.dropP=[0.1,0.1];
    Params.decay=1e-05;Params.learnR=0.01;
    batchsize=V;Params.batchsize=batchsize;
    run=80000;Params.round=run;

    %W
    flag=0;
    W{1}=iniA(V,neuronN,flag,bias2);W{2}=iniA(neuronN,neuronN,flag,bias2);
    W{3}=iniA(neuronN,M,flag,bias2);
    %B
    flag=1;
    B{1}=iniA(1,neuronN,flag,bias1);B{2}=iniA(1,neuronN,flag,bias2);
    array=iniA(1,M,flag,bias2);B{3}=array(1:M);
    %net
    net.W=W;net.B=B;
    index=round(1+rand(1,run*batchsize)*(N-1));
    for j=1:run
        x=tr_x(index((j-1)*batchsize+1:j*batchsize),:);
        y=tr_y(index((j-1)*batchsize+1:j*batchsize),:);      
        net=trainNet(x, y, Params, net);
    end
end