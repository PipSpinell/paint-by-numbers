import sys,re
b=re.sub(r'^\d+_','',sys.argv[1]); STOP={'the','of','and','a','an','in','on','to','for','from','with','at','by'}
parts=b.split('___'); out=[]
for p in parts:
    t=p.split('__') ; seg=[]
    for q in t:
        w=[x for x in q.split('_') if x]; s=w[0] if w else ''
        for x in w[1:]: s+=("'" if x[0].islower() and x.lower() not in STOP else ' ')+x
        seg.append(s)
    out.append(', '.join(seg))
print(' – '.join(out))
