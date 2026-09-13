import pyarrow.parquet as pq, json, glob, os
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
cells=[("q10_ZDT4","exp_batch_c149_ZDT4_42"),("q10_ZDT1","exp_batch_c149_ZDT1_42"),
       ("q10_DTLZ2","exp_batch_c149_DTLZ2_42"),("q10_WFG9","exp_batch_c149_WFG9_42"),
       ("q10_MMF16_20","exp_batch_c149_MMF16_20_42"),("ZDT4","exp_main_c149_ZDT4_42")]
for cell,pref in cells:
    print("###",cell)
    for lay in ["real","surrogate","pop","timing"]:
        p=f"{R}/{cell}/42/{pref}__{lay}.parquet"
        if not os.path.exists(p): print("  MISSING",lay); continue
        f=pq.ParquetFile(p); md=f.metadata
        kv=md.metadata or {}
        cb=md.created_by
        rg=[md.row_group(i).num_rows for i in range(md.num_row_groups)]
        comp=md.row_group(0).column(0).compression
        print(f"  {lay:10s} rows={md.num_rows:7d} rgs={md.num_row_groups} sizes={rg[:4]}{'...' if len(rg)>4 else ''} comp={comp} created_by={cb} kv_keys={[k.decode() for k in kv]}")
    j=f"{R}/{cell}/42/{pref}.jsonl"
    L=[json.loads(l) for l in open(j)]
    print("   jsonl ts: header",L[0]["ts"],"| first decision",[r for r in L if r['rec']=='decision'][0]['ts'],"| footer",L[-1]["ts"])
    m=json.load(open(f"{R}/{cell}/42/{pref}.manifest.json"))
    print("   manifest created_at",m["created_at"],"updated_at",m["updated_at"],"wall(timing)",m.get("timing",{}).get("tempo_total_s") if isinstance(m.get("timing"),dict) else None)
