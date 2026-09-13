h=figure;
set(gca,'FontSize',20)
colors = {'[0.9290 0.6940 0.1250]', '[0.4660 0.6740 0.1880]', '[0.1 0.2 0.8]', '[0.8 0.5 0.5]', '[0.5 0.5 0.5]'};


%% GT
opts = delimitedTextImportOptions("NumVariables", 2);

% Specify range and delimiter
opts.DataLines = [2, Inf];
opts.Delimiter = ",";

% Specify column names and types
opts.VariableNames = ["f1", "f2"];
opts.VariableTypes = ["double", "double"];

% Specify file level properties
opts.ExtraColumnsRule = "ignore";
opts.EmptyLineRule = "read";

% Import the data
TrueParetoFront = readtable("Z:\NAGD\DGEMO\DGEMO\result\zdt3-30D-1000B\default\TrueParetoFront.csv", opts);
clear opts
plot(TrueParetoFront.f1,TrueParetoFront.f2,'.','MarkerSize',10,'color','k')
hold on
%% NSGA2

opts = delimitedTextImportOptions("NumVariables", 33);

% Specify range and delimiter
opts.DataLines = [2, Inf];
opts.Delimiter = ",";

% Specify column names and types
opts.VariableNames = ["iterID", "x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9", "x10", "x11", "x12", "x13", "x14", "x15", "x16", "x17", "x18", "x19", "x20", "x21", "x22", "x23", "x24", "x25", "x26", "x27", "x28", "x29", "x30", "Pareto_f1", "Pareto_f2"];
opts.VariableTypes = ["double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double"];

% Specify file level properties
opts.ExtraColumnsRule = "ignore";
opts.EmptyLineRule = "read";

% Import the data
ParetoFrontEvaluated1 = readtable("Z:\NAGD\DGEMO\DGEMO\result\zdt3-30D-1000B\default\nsga2\0\ParetoFrontEvaluated.csv", opts);
clear opts
pareto = [ParetoFrontEvaluated1.Pareto_f1, ParetoFrontEvaluated1.Pareto_f2];
Gen_num = 4;
pareto_ = pareto(ParetoFrontEvaluated1.iterID==Gen_num,:);
plot(pareto_(:,1),pareto_(:,2),'.','MarkerSize',20,'color',colors{2})
for i = 1:10
    pareto_iter = pareto(ParetoFrontEvaluated1.iterID == i, :);
    save(sprintf('NSGA2_pareto_iter_%d.mat', i), 'pareto_iter');
end
%% Plot settings
legend({'GT','NSGA-II'})
xlabel('f2','FontSize',15)
ylabel('f1','FontSize',15)
ylim([-1 1.5])
title('NSGA-II')
% xlim([0 0.6])
legend('Location','northwest')
pbaspect([3 2 1])
set(gca,'FontSize',10)
set(h,'Units','Inches');
pos = get(h,'Position');
set(h,'PaperPositionMode','Auto','PaperUnits','Inches','PaperSize',[pos(3)-0.15, pos(4)])
print(h,'.\data\Progress_NSGA2_ZDT3.pdf','-dpdf','-r0')