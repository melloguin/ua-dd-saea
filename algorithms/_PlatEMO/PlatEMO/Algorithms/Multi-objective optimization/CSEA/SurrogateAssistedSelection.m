function [Next,info] = SurrogateAssistedSelection(Problem,net,p0,p1,Ref,Input,wmax,tr)
% Surrogate-assisted selection for selecting promising solutions
% [R1-b4] (a) Balde C SUBSTITUI os operadores nativos {1,15,1,5} (eta_c=15,
% eta_m=5) por SBX 1/20 + PM 1/D/20 = {1,20,1,20} (§6.2/§6.4 — b4 NAO esta nas
% excecoes c217/c122); (b) guard do bug latente :30 (randperm(length(Next))
% usaria max(dim) — excederia as linhas se D>|Pop|+6; caso nao-degenerado =
% MESMO sorteio, bit-identico); (c) 2o output `info` (ramo/L dos selecionados/
% guard) p/ a instrumentacao — decisoes INTACTAS (D97).

%------------------------------- Copyright --------------------------------
% Copyright (c) 2026 BIMK Group. You are free to use the PlatEMO for
% research purposes. All publications which use this platform or any code
% in the platform should acknowledge the use of "PlatEMO" and reference "Ye
% Tian, Ran Cheng, Xingyi Zhang, and Yaochu Jin, PlatEMO: A MATLAB platform
% for evolutionary multi-objective optimization [educational forum], IEEE
% Computational Intelligence Magazine, 2017, 12(4): 73-87".
%--------------------------------------------------------------------------

% This function is written by Cheng He

    info  = struct('ramo', 0, 'Lsel', [], 'guard_randperm', false);
    Next  = OperatorGA(Problem,[Input;Ref.decs],{1,20,1,20});
    Label = predict(net,Next);
    a     = tr;
    b     = 1 - tr;
    i     = 0;
    if p0<0.4 || (p1<a&&p0<b)
        while i < wmax
            [~,index] = sort(Label,'descend');
            Input     = Next(index(1:length(Ref)),:);
            Next      = OperatorGA(Problem,[Input;Ref.decs],{1,20,1,20});
            Label = predict(net,Next);
            i = i+size(Next,1);
        end
        info.ramo = 1;                       % confiavel -> maximiza L, gate >0.9
        info.Lsel = Label(Label>0.9);
        Next = Next(Label>0.9,:);
    elseif p0>b && p1<a % Randomly select one to avoid loop
        % [R1-b4] guard: randperm sobre as LINHAS (length() = max dim quebraria
        % se D>|Pop|+6); mesmo sorteio quando linhas >= D (bit-identico).
        info.guard_randperm = length(Next) ~= size(Next,1);
        randindex = randperm(size(Next,1));
        info.ramo = 2;                       % anti-loop -> 1 aleatorio
        info.Lsel = Label(randindex(1));
        Next = Next(randindex(1),:);
    elseif p1 > b
        while i<wmax
            [~,index] = sort(Label);
            Input     = Next(index(1:length(Ref)),:);
            Next      = OperatorGA(Problem,[Input;Ref.decs],{1,20,1,20});
            Label = predict(net,Next);
            i = i+size(Next,1);
        end
        info.ramo = 3;                       % invertido -> minimiza L, gate <0.1
        info.Lsel = Label(Label<0.1);
        Next = Next(Label<0.1,:);
    else
        ii = randi(size(Next,1));            % [R1-b4] == randi(end) (captura idx)
        info.ramo = 4;                       % inconclusivo -> 1 aleatorio
        info.Lsel = Label(ii);
        Next = Next(ii,:);
    end
end