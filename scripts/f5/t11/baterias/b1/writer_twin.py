"""Gemeo Python do writer do ⑥ — verifica a DIRECAO do fix G1 (B-11).
Escreve SO em tempdir. Nao toca em nada do repo/dados."""
import os, tempfile, json
from multiprocessing import Process
def w(path, mode, tag, n=5000):
    f=open(path, mode)
    for i in range(n):
        f.write(json.dumps({'rec':'x','tag':tag,'i':i})+'\n'); f.flush()
    f.close()
def run(m1,m2):
    d=tempfile.mkdtemp(prefix='b1twin_')
    p=os.path.join(d,'a.jsonl')
    open(p,'w').close()
    ps=[Process(target=w,args=(p,m1,'A')),Process(target=w,args=(p,m2,'B'))]
    [x.start() for x in ps]; [x.join() for x in ps]
    tot=0;ok=0;bad=0;tags={'A':0,'B':0}
    for l in open(p,errors='replace'):
        tot+=1
        try:
            r=json.loads(l); ok+=1; tags[r['tag']]=tags.get(r['tag'],0)+1
        except Exception: bad+=1
    print('  modos %s+%s -> linhas=%5d  validas=%5d  malformadas=%3d  A=%4d B=%4d  PERDIDAS=%4d'%(
        m1,m2,tot,ok,bad,tags.get('A',0),tags.get('B',0),10000-tags.get('A',0)-tags.get('B',0)))
if __name__=='__main__':
    print('2 escritores concorrentes, 5.000 linhas cada (10.000 esperadas):')
    for _ in range(2): run('w','w')
    for _ in range(2): run('w','a')
    for _ in range(2): run('a','a')
