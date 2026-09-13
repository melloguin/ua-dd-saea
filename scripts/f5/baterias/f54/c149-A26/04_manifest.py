import json, pyarrow.parquet as pq, os, datetime
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
for cell,pref in [("q10_ZDT4","exp_batch_c149_ZDT4_42"),("q10_ZDT1","exp_batch_c149_ZDT1_42"),("ZDT4","exp_main_c149_ZDT4_42")]:
    m=json.load(open(f"{R}/{cell}/42/{pref}.manifest.json"))
    print("###",cell)
    for k in sorted(m):
        if k in ("params","sigma_dict","fit_series","timing","sonda"): print("   ",k,"-> <big>"); continue
        print("   ",k,"=",json.dumps(m[k])[:400])
    print()
