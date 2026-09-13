import json
p="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149/q10_ZDT4/42/exp_batch_c149_ZDT4_42.jsonl"
n=0
for line in open(p):
    d=json.loads(line)
    if d["rec"]=="decision":
        print(json.dumps(d,indent=1)[:2600]); n+=1
        if n>=2: break
