classdef PCSAEA < ALGORITHM
% <2023> <multi/many> <real> <expensive>
% Pairwise comparison based surrogate-assisted evolutionary algorithm
% delta ---  0.8 --- Threshold of reliability measurement
% gmax  --- 3000 --- Number of solutions evaluated by surrogate model

%------------------------------- Reference --------------------------------
% Y. Tian, J. Hu, C. He, H. Ma, L. Zhang, and X. Zhang. A pairwise
% comparison based surrogate-assisted evolutionary algorithm for expensive
% multi-objective optimization. Swarm and Evolutionary Computation, 2023,
% 80: 101323.
%------------------------------- Copyright --------------------------------
% Copyright (c) 2026 BIMK Group. You are free to use the PlatEMO for
% research purposes. All publications which use this platform or any code
% in the platform should acknowledge the use of "PlatEMO" and reference "Ye
% Tian, Ran Cheng, Xingyi Zhang, and Yaochu Jin, PlatEMO: A MATLAB platform
% for evolutionary multi-objective optimization [educational forum], IEEE
% Computational Intelligence Magazine, 2017, 12(4): 73-87".
%--------------------------------------------------------------------------

    methods
        function main(Algorithm,Problem)
            %% Parameter setting
            [delta,gmax] = Algorithm.ParameterSet(0.8,3000);

            %% [R1-c217] Init = DoE 11D-1 INJETADO do artefato (D63/D87/D94) — NUNCA regenerar.
            % X0 e NATIVO (load_doe): passa DIRETO -> sem re-escala (a dupla-escala D94 nao ocorre).
            % Problem.N=50 governa populacao/lote (EnvironmentalSelection, split 13/12); o init e 11D-1
            % (o LHS nativo :27-29 e substituido pelo artefato pareado por (problema,semente)).
            PopDec     = Problem.data.X0;
            Population = Problem.Evaluation(PopDec);
            Arc        = Population;
            t          = 1;
        
            %% Optimization
            while Algorithm.NotTerminated(Arc)
                % Select a balance sample set by a new fitness
                [Input,Output,Pa,Pmid] = CalFitnessPC(Population.objs,Population.decs,(Problem.FE/Problem.maxFE));   
                % Data process
                [TrainIn,~,TestIn,TestOut] = DataProcess(Input,Output);
                % Construct and update the FNN��global classify surrogate model
                net = RBFNNPC(0.1925);
                tFit_c217 = tic; net.train(TrainIn,Problem.D); tfit_s_c217 = toc(tFit_c217);   % [R1-c217] timing §17.6 (nao altera a decisao — D97)

                % Error rates calculation
                TestPre = net.lastpredict(TestIn,Problem.D,Pmid,1);
                % New and suitble reliability selection
                validIndex = TestPre~=1.5;
                Error1 = sum(TestOut(validIndex)==TestPre(validIndex))/length(TestOut);   
                Error2 = sum(TestOut(validIndex)~=TestPre(validIndex))/length(TestOut);              

                % Surrogate-assisted selection and update the population
                Next = SurrogateAssistedSelectionPC(Problem,net,Error1,Error2,Population.decs,gmax,Pa,Problem.D,0,delta);
                if ~isempty(Next)
                    Arc = [Arc,Problem.Evaluation(Next)];
                end
                % [R1-c217] D89: o obj.FE nativo do PlatEMO NAO governa (infla c/ duplicata:
                % Evaluation soma length(Population) incluindo cache-hits). Re-sincroniza com
                % o SALDO DISTINTO do wrapper (bud.fe) -> NotTerminated para em bud.fe=31D-1 e
                % o rate (=Problem.FE/maxFE) fica fiel. O hard-stop real e o throw do bud (D61).
                Problem.FE = Problem.data.bud.fe;
                Population = EnvironmentalSelection(Arc,min(Problem.N,length(Arc)));   % [R1-c217] fix min(N,|Arc|): evita crash D<=4 (|Arc|<Problem.N=50; PCS:55)
                % [R1-c217] instrumentacao POS-decisao (NAO altera a busca — D97): ③ score + §17.2.1 (.jsonl) + timing §17.6
                c217_instrument(Problem, Arc, Next, delta, Error1, Error2, TestPre, tfit_s_c217);
                t = t + 1;
            end
        end
    end
end