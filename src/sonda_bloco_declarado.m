function [b, aplica] = sonda_bloco_declarado(problema)
%SONDA_BLOCO_DECLARADO  O bloco (5) da ausencia de sonda POR PROBLEMA (D102.10).
%
%   [b, aplica] = sonda_bloco_declarado(problema)
%     aplica = true  <=> o problema esta em PROBLEMAS_SEM_SONDA (hoje: DDMOP7)
%     b      = o bloco DECLARADO (mesmos campos de SONDA_AUSENTE_INFO) quando
%              aplica; struct() vazio quando nao.
%
%   [T15.7 §3b] O achado do T15.3: o `build_manifest`/`fill_manifest_timing`
%   gravava `status='artefato_ausente'` para QUALQUER run sem sonda — mas o
%   auditar exige `'sem_sonda_por_problema'` para problemas declarados sem
%   regua (as TRES ausencias tem de ser inconfundiveis: 'nao_se_aplica' =
%   config sem surrogate; 'artefato_ausente' = acidente/piloto;
%   'sem_sonda_por_problema' = opt-out D102.10).
%
%   FONTE UNICA: `src/experiment.py` (PROBLEMAS_SEM_SONDA + SONDA_AUSENTE_INFO)
%   lida pelo Python embutido — a MESMA ponte A2 que o harness R1 ja usa.
%   Nenhum literal duplicado no lado MATLAB: se a constante Python mudar, este
%   arquivo muda junto, sozinho. `persistent` porque o import custa um IPC por
%   processo MATLAB e a constante e imutavel por construcao.

persistent lista info
if isempty(lista)
    raiz = fileparts(fileparts(mfilename('fullpath')));
    if count(py.sys.path, raiz) == 0
        insert(py.sys.path, int32(0), raiz);
    end
    m = py.importlib.import_module('src.experiment');
    lista = cellfun(@char, cell(py.list(py.getattr(m, 'PROBLEMAS_SEM_SONDA'))), ...
                    'UniformOutput', false);
    d = py.getattr(m, 'SONDA_AUSENTE_INFO');
    info = struct( ...
        'status',   string(char(d{'status'})), ...
        'motivo',   string(char(d{'motivo'})), ...
        'n_blocos', double(d{'n_blocos'}), ...
        'n_linhas', double(d{'n_linhas'}), ...
        'S',        double(d{'S'}));
end
aplica = any(strcmp(char(problema), lista));
if aplica
    b = info;
else
    b = struct();
end
end
