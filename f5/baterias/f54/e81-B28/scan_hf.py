import json, collections, os, glob, sys, io
root='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
rows=[]
for p in glob.glob(root+'/*/*/*/*.jsonl'):
    parts=p.split('/')
    cfg=parts[-4]; label=parts[-3]; seed=parts[-2]
    c=collections.Counter(); ts_h=[]; ts_f=[]
    hdr_full=0; hdr_disp=0; ftr_run=0; ftr_disp=0
    with open(p, errors='replace') as f:
        for l in f:
            l=l.strip()
            if not l: continue
            try: d=json.loads(l)
            except Exception: c['__bad__']+=1; continue
            r=d.get('rec'); c[r]+=1
            if r=='header':
                if 'run_id' in d and d.get('D') is None: hdr_disp+=1
                else: hdr_full+=1
                ts_h.append(d.get('ts'))
            elif r=='footer':
                if 'fe_final' in d: ftr_run+=1
                else: ftr_disp+=1
                ts_f.append(d.get('ts'))
    rows.append(dict(cfg=cfg,label=label,seed=seed,file=os.path.basename(p),
        n_header=c['header'],n_footer=c['footer'],hdr_full=hdr_full,hdr_disp=hdr_disp,
        ftr_run=ftr_run,ftr_disp=ftr_disp,bad=c['__bad__'],
        ts_h_min=min(ts_h) if ts_h else None, ts_h_max=max(ts_h) if ts_h else None,
        ts_f_max=max(ts_f) if ts_f else None, path=p))
import csv
with open('scan_hf.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('n_files',len(rows))
cnt=collections.Counter((r['n_header'],r['n_footer'],r['hdr_full'],r['hdr_disp'],r['ftr_run'],r['ftr_disp']) for r in rows)
for k,v in sorted(cnt.items(), key=lambda x:-x[1]):
    print('H=%d F=%d (hfull=%d hdisp=%d frun=%d fdisp=%d) -> %d files'%(k+ (v,)))
