function hook_output(Algorithm, Problem, varargin)
% hook_output — hook `outputFcn(Algorithm, Problem)` do PlatEMO, chamado a CADA
% geracao (inclusive a final). Emite as camadas ② (populacao real) e ③
% (surrogate) sincronizadas + a serie de tempo §17.6, sem editar os algoritmos
% (§17.3/D31: o MESMO hook emite ② e ③ nos MESMOS pontos -> sincronizacao §17.1.3).
%
% >>> ESQUELETO (F0-01-harness). A EMISSAO REAL das camadas (extrair a pop
% >>> selecionada + mu/sigma do surrogate por geracao, acumular e gravar em
% >>> parquet brotli+single) e o cartao R1-00-harness / F0-03. Aqui fica o
% >>> contrato e o ponto de gancho.
%
% Notas da mecanica (§18 v2.2):
%   - O runtime deste hook NAO conta no metric.runtime.
%   - `Algorithm.result` = snapshots {FE, Population} equiespacados em FE.
%   - `SOLUTION.add` e um campo publico por individuo p/ anexar mu/sigma.
%   - A camada real (①) sai do wrapper de FE (ponto unico de avaliacao), nao daqui.
%
% Em R1, acumular por geracao:
%   g   = current_generation(Algorithm);
%   pop = Algorithm.result{end, 2};        % SOLUTION array da geracao
%   - ② membership: (run_id, g, solution_id) por individuo real
%   - ③ surrogate:  (run_id, g, x, real_solution_id, mu/sigma|classe/score, modelo)
%   - §17.6 timing: (g, n_acumulado, tempo_fit_s) por retreino
% e gravar/anexar via um buffer do run (fechado no fim pelo experiment_run).

% Andaime: no-op instrumentado (nao emite nada na Fase 0).
end
