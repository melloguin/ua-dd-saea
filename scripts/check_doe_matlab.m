function nfail = check_doe_matlab(data_root)
% check_doe_matlab — metade MATLAB do CP-init do DoE/dataset (D87/D88).
%
% Prova a **bit-identidade Python<->MATLAB**: o MATLAB lê cada artefato com
% `parquetread`, reconstrói o ARRAY DECODIFICADO (float64, row-major) exatamente
% como o numpy o vê (`np.ascontiguousarray(A,'<f8').tobytes()`), calcula o SHA256
% e compara com o `*_hash` gravado pelo escritor pyarrow no sidecar `.manifest.json`.
% Nenhum algoritmo/harness é necessário — só `parquetread` (independe do R1-00).
%
% Uso (no Mac, com MATLAB):
%   cd <raiz do repo>;  nfail = check_doe_matlab            % usa 'data'
%   nfail = check_doe_matlab('data')
% Sai com contagem de falhas; imprime PASS/FAIL por arquivo (resumo no fim).

    if nargin < 1 || isempty(data_root); data_root = 'data'; end
    npass = 0; nfail = 0;

    specs = { ...
        fullfile(data_root, 'doe',      '*', 'doe_*.parquet'),  'doe_hash'; ...
        fullfile(data_root, 'datasets', '*', 'ds_*.parquet'),   'dataset_hash' };

    for s = 1:size(specs, 1)
        files = dir(specs{s, 1});
        hkey  = specs{s, 2};
        for k = 1:numel(files)
            pq  = fullfile(files(k).folder, files(k).name);
            man = replace(pq, '.parquet', '.manifest.json');
            if ~isfile(man)
                fprintf(2, 'FAIL  %s  (sidecar ausente)\n', pq); nfail = nfail + 1; continue;
            end
            side = jsondecode(fileread(man));
            cols = cellstr(side.columns);               % {'x0','x1',...,'f0',...}
            t    = parquetread(pq);
            M    = t{:, cols};                          % n x numel(cols), na ordem canônica
            got  = sha256_rowmajor_f64(M);
            want = char(side.(hkey));
            if strcmp(got, want)
                npass = npass + 1;
            else
                fprintf(2, 'FAIL  %s\n   got  %s\n   want %s\n', pq, got, want);
                nfail = nfail + 1;
            end
        end
    end

    fprintf('\n[check_doe_matlab] PASS=%d  FAIL=%d  (data_root=%s)\n', npass, nfail, data_root);
    if nfail == 0 && npass > 0
        fprintf('  >>> VERDE: bit-identidade Python<->MATLAB confirmada (D87/D88).\n');
    elseif npass == 0
        fprintf(2, '  >>> nada verificado — gere os artefatos com src/doe.py primeiro.\n');
    else
        fprintf(2, '  >>> VERMELHO — pára-e-loga (D81): hash divergente.\n');
    end
end

function hex = sha256_rowmajor_f64(M)
% SHA256 dos bytes float64 little-endian em ROW-MAJOR (igual ao numpy '<f8').
% M é column-major no MATLAB; M.' lido column-major = M lido row-major.
    bytes_u8 = typecast(reshape(double(M).', 1, []), 'uint8');   % little-endian no arm64/x86
    md = java.security.MessageDigest.getInstance('SHA-256');
    md.update(typecast(bytes_u8, 'int8'));                       % Java byte[] preserva o padrão
    hb  = typecast(md.digest(), 'uint8');
    hex = lower(sprintf('%02x', hb));
end
