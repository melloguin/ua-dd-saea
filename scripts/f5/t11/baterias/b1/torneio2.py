import pandas as pd, numpy as np
d=pd.read_csv('b1_torneio_iters.csv')
ok=d[d.problema!='WFG1']; w=d[d.problema=='WFG1']
print('WFG1: n=%d  1a-venceu=%d  e0_const=%d  (1a venceu e nao-const=%d)'%(len(w),w.e0_arg0.sum(),w.e0_const.sum(),((w.e0_arg0)&(~w.e0_const)).sum()))
print('s42 COM WFG1: 1a-venceu=%d  e0_const=%d'%(d.e0_arg0.sum(),d.e0_const.sum()))
cap=ok.n_arquivo>(ok.nDoE+25)
print('\niteracoes POS-cap (PCheby ORDENADO => torneio vira min(U1,U2) puro): %d/%d = %.1f%%'%(cap.sum(),len(ok),100*cap.mean()))
print('iteracoes PRE-cap: %d ; destas, com dedup>0 (dominio ainda desalinha): calculado a seguir'%((~cap).sum()))
it=pd.read_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b1/b1_iters.csv')
pre=it[it.n_arquivo<=(11*it.D-1+25)]
print('  PRE-cap n=%d ; com n_dedup>0: %d (%.1f%%)'%(len(pre),(pre.n_dedup>0).sum(),100*(pre.n_dedup>0).mean()))
print('\nfrac inalcancavel por D:'); print(ok.groupby('D').frac_inalc.agg(['mean','max']).to_string(float_format=lambda v:'%.3f'%v))
print('\nP(pai=DoE) por D:'); print(ok.groupby('D').p_doe.agg(['mean','min']).to_string(float_format=lambda v:'%.4f'%v))
# ganho de EI quando a 1a geracao NAO venceu (o GA melhora quanto?)
ok2=ok.copy(); ok2['ganho_rel']=ok2.e0_ganho/ok2.ei_best.abs().replace(0,np.nan)
print('\nganho absoluto de EI da 1a ger ate o fim do GA interno: mediana %.3e ; frac com ganho>0: %.3f'%(ok2.e0_ganho.median(),(ok2.e0_ganho>0).mean()))
