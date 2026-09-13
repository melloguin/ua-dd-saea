function [OffDec,OffVel] = CSO(PopDec,Fitness,PopVel,lower,upper)
if size(PopDec,1) >= 2
    Rank = randperm(size(PopDec,1),floor(size(PopDec,1)/2)*2);
else
    Rank = [1,1];
end
Loser  = Rank(1:end/2);
Winner = Rank(end/2+1:end);
Change = Fitness(Loser) >= Fitness(Winner);
Temp   = Winner(Change);
Winner(Change) = Loser(Change);
Loser(Change)  = Temp;
LoserDec  = PopDec(Loser,:);
WinnerDec = PopDec(Winner,:);
[N,D]     = size(LoserDec);

LoserVel = PopVel(Loser,:);
WinnerVel = PopVel(Winner,:);
r1     = repmat(rand(N,1),1,D);
r2     = repmat(rand(N,1),1,D);
OffVel = r1.*LoserVel + r2.*(WinnerDec-LoserDec);
OffDec = LoserDec + OffVel + r1.*(OffVel-LoserVel);
OffDec = [OffDec;WinnerDec];
OffVel = [OffVel;WinnerVel];
%% Polynomial mutation
Lower  = repmat(lower,2*N,1);
Upper  = repmat(upper,2*N,1);
disM   = 20;
Site   = rand(2*N,D) < 1/D;
mu     = rand(2*N,D);
temp   = Site & mu<=0.5;
OffDec       = max(min(OffDec,Upper),Lower);
OffDec(temp) = OffDec(temp)+(Upper(temp)-Lower(temp)).*((2.*mu(temp)+(1-2.*mu(temp)).*...
    (1-(OffDec(temp)-Lower(temp))./(Upper(temp)-Lower(temp))).^(disM+1)).^(1/(disM+1))-1);
temp  = Site & mu>0.5;
OffDec(temp) = OffDec(temp)+(Upper(temp)-Lower(temp)).*(1-(2.*(1-mu(temp))+2.*(mu(temp)-0.5).*...
    (1-(Upper(temp)-OffDec(temp))./(Upper(temp)-Lower(temp))).^(disM+1)).^(1/(disM+1)));
end

