function [Fitness, sde_guard] = calFitness(PopObj)
% Calculate the fitness by shift-based density
% [R1-c141] guard L4 (D76 — 🟠 obrigatorio): fmax==fmin em algum objetivo do
% subconjunto => 0/0 = NaN no min-max do SDE, que propagaria ao NDSort do nivel 2
% da cascata. Denominador DEGENERADO recebe +eps; nos casos nao-degenerados o
% calculo e BIT-IDENTICO ao stock. O 2o output sde_guard e o flag p/ o log
% (§17.5) — chamadas com 1 output seguem identicas.
N      = size(PopObj,1);
fmax   = max(PopObj,[],1);
fmin   = min(PopObj,[],1);
den    = fmax - fmin;
sde_guard = any(den == 0);
den(den == 0) = eps;
PopObj = (PopObj-repmat(fmin,N,1))./repmat(den,N,1);
Dis    = inf(N);
for i = 1 : N
    SPopObj = max(PopObj,repmat(PopObj(i,:),N,1));
    for j = [1:i-1,i+1:N]
        Dis(i,j) = norm(PopObj(i,:)-SPopObj(j,:));
    end
end
Fitness = min(Dis,[],2);
end

