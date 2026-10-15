import os
SLUG=os.environ.get('PBN_SLUG','soggetto')
import numpy as np, cv2, sys, pickle
from sklearn.cluster import KMeans
from PIL import Image, ImageDraw, ImageFont
SRC=sys.argv[1]; OUT=sys.argv[2]
K=int(sys.argv[4]) if len(sys.argv)>4 else 16; W_A4,H_A4=2480,3508
img=np.array(Image.open(SRC).convert('RGB'))
# disegno grande quanto la pagina 1 (vedi pbn_common.py)
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import pbn_common as PC
# ritaglio dei margini bianchi dell'originale: il disegno riempie la pagina 1
_Lo=cv2.cvtColor(img,cv2.COLOR_RGB2LAB).astype(int)
_ink=~((_Lo[...,0]>232)&(np.abs(_Lo[...,1]-128)<8)&(np.abs(_Lo[...,2]-128)<10))
_r=np.nonzero(_ink.sum(1)>2)[0]; _c=np.nonzero(_ink.sum(0)>2)[0]
_p=int(0.015*max(img.shape[:2]))
cy0,cy1=max(_r[0]-_p,0),min(_r[-1]+1+_p,img.shape[0]); cx0,cx1=max(_c[0]-_p,0),min(_c[-1]+1+_p,img.shape[1])
DH,DW=PC.drawing_size(cy1-cy0,cx1-cx0); sc=DH/(cy1-cy0)
bigF=cv2.resize(img,(int(round(img.shape[1]*sc)),int(round(img.shape[0]*sc))),interpolation=cv2.INTER_LANCZOS4)
oy,ox=int(round(cy0*sc)),int(round(cx0*sc))
bigF=np.pad(bigF,((0,max(0,oy+DH-bigF.shape[0])),(0,max(0,ox+DW-bigF.shape[1])),(0,0)),constant_values=255)
big=bigF[oy:oy+DH,ox:ox+DW].copy()
print('ritaglio',(cx0,cy0,cx1,cy1),'disegno',DW,DH)
# PARTI STAMPATE: nome del boss (fascia di testo in fondo) e firma PipSpi restano come nell'originale,
# gia' stampate sulla tavola: niente zone ne' numeri li'. Salvate in printed.png (RGBA, stesse dimensioni del disegno).
def printed_mask(rgb):
    L=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(int)
    paper0=(L[...,0]>232)&(np.abs(L[...,1]-128)<8)&(np.abs(L[...,2]-128)<10)
    ink=~paper0; H_,W_=ink.shape; rows=ink.sum(1)>2
    m=np.zeros((H_,W_),bool); ttop=H_
    nz=np.nonzero(rows)[0]
    if len(nz):
        b=nz[-1]; t=b
        while t>0 and (rows[t-1] or rows[max(t-int(0.006*H_),0):t].any()): t-=1
        gap=t-1
        while gap>0 and not rows[gap]: gap-=1
        if (b-t)<0.16*H_ and (t-gap)>=0.008*H_ and t>0.6*H_:   # fascia del titolo staccata dal disegno
            m[t:b+1]=ink[t:b+1]; ttop=t
    # firma: tratti scuri piccoli in basso a destra, separati dal disegno
    dark=(L[...,0]<90).astype(np.uint8)
    x0,y0,x1,y1=int(0.62*W_),int(0.68*H_),int(0.985*W_),ttop
    if y1>y0:
        sub=dark[y0:y1,x0:x1]; n,cc,st,_=cv2.connectedComponentsWithStats(sub,connectivity=8)
        ker=np.ones((15,15),np.uint8)
        cand=np.zeros(sub.shape,bool); cc_ok=[]
        for j in range(1,n):
            x,y,w,h,a=st[j]
            if x==0 or y==0 or x+w>=sub.shape[1] or y+h>=sub.shape[0]: continue
            if a>0.004*H_*W_ or h>0.08*H_: continue
            c=(cc==j).astype(np.uint8)
            if cv2.distanceTransform(np.pad(c[y:y+h,x:x+w],1),cv2.DIST_L2,3).max()>0.0045*W_: continue  # macchia piena, non tratto di lettera
            ring=cv2.dilate(c,ker).astype(bool)&~cv2.dilate(c,np.ones((5,5),np.uint8)).astype(bool)  # anello oltre l'antialias
            if paper0[y0:y1,x0:x1][ring].mean()<0.55: continue    # pezzo del disegno, non firma
            cand[c.astype(bool)]=True; cc_ok.append(j)
        # la firma e' un gruppo di lettere affiancate: tengo solo il gruppo con piu' componenti (>=3)
        if cc_ok:
            g=cv2.dilate(cand.astype(np.uint8),np.ones((max(3,int(0.006*H_)),max(5,int(0.03*W_))),np.uint8))
            ng,gl=cv2.connectedComponents(g,connectivity=8)
            cnt=np.zeros(ng,int)
            for j in cc_ok: cnt[gl[cc==j][0]]+=1
            best=cnt.argmax()
            if cnt[best]>=3: m[y0:y1,x0:x1]|=cand&(gl==best)
    m=cv2.dilate(m.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)&ink | cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    return m
PRINTED=printed_mask(bigF)[oy:oy+DH,ox:ox+DW]  # rilevato sull'immagine intera (posizioni relative), poi ritagliato
if PRINTED.any():
    rgba=np.dstack([big,(PRINTED*255).astype(np.uint8)]); Image.fromarray(rgba,'RGBA').save(OUT+'/printed.png')
elif os.path.exists(OUT+'/printed.png'): os.remove(OUT+'/printed.png')
bgr=cv2.cvtColor(big,cv2.COLOR_RGB2BGR)
# smussatura leggera: occhi, bocca e linee sottili non devono sparire
sm=cv2.pyrMeanShiftFiltering(bgr,6,16)
sm=cv2.bilateralFilter(sm,7,30,7)
lab=cv2.cvtColor(sm,cv2.COLOR_BGR2LAB).reshape(-1,3).astype(np.float32)
paper=(lab[:,0]>238)&(np.abs(lab[:,1]-128)<7)&(np.abs(lab[:,2]-128)<9)
paper|=PRINTED.reshape(-1)
rng=np.random.default_rng(0); cand=np.where(~paper)[0]; idx=rng.choice(cand,120000,replace=False)
km=KMeans(K,n_init=6,random_state=0).fit(lab[idx])
cent=km.cluster_centers_
ACCENTI=os.environ.get('PBN_ACCENTI','1')=='1'
MAX_ACC=int(os.environ.get('PBN_MAX_ACC','2'))  # al massimo 2 accenti (i piu' estesi): con 6 i colori erano troppi  # attivi di default: piccoli colori distinti (occhi gialli, braci...) non si perdono
if ACCENTI:
    # colori d'accento: piccole zone (es. una cintura gialla) che nessun colore base rende (dE00>15)
    from skimage.color import deltaE_ciede2000
    def cie(x): x=x.astype(np.float64).copy(); x[:,0]*=100/255; x[:,1:]-=128; return x
    X=lab[idx]; C=cie(cent); XC=cie(X)
    dmin=np.min(np.stack([deltaE_ciede2000(XC,np.repeat(c[None],len(XC),0)) for c in C]),0)
    Wr=X[dmin>15]; acc=[]
    if len(Wr)>=100:
        k2=KMeans(min(8,len(Wr)//50),n_init=4,random_state=0).fit(Wr)
        cand=sorted([(int((k2.labels_==j).sum()),c) for j,c in enumerate(k2.cluster_centers_)],key=lambda t:-t[0])
        groups=[]
        for n,c in cand:
            for g in groups:
                if deltaE_ciede2000(cie(g['c'][None]),cie(c[None]))[0]<12:
                    g['c']=(g['c']*g['n']+c*n)/(g['n']+n); g['n']+=n; break
            else: groups.append(dict(c=c,n=n))
        for g in sorted(groups,key=lambda g:-g['n']):
            share=g['n']/len(X)
            dd=deltaE_ciede2000(np.repeat(cie(g['c'][None]),K,0),C).min()
            if share>=0.0005 and dd>=15 and len(acc)<MAX_ACC: acc.append(g['c']); print('accento',np.round(g['c']).astype(int),'quota %.2f%%'%(share*100),'dE00 %.1f'%dd)
    pass
else: acc=[]
if acc: cent=np.vstack([cent]+acc); K=len(cent)
d2=((lab[:,None,:]-cent[None,:,:].astype(np.float32))**2).sum(-1)
lbl=d2.argmin(1); del d2
lbl[paper]=K; lbl=lbl.reshape(DH,DW)
NL=K+1
def mode_filter(l,k=7):
    acc=np.stack([cv2.boxFilter((l==i).astype(np.float32),-1,(k,k)) for i in range(NL)])
    return acc.argmax(0)
lbl=mode_filter(lbl,3); lbl=mode_filter(lbl,3)
MIN=int(sys.argv[3]) if len(sys.argv)>3 else 1100
ker=np.ones((3,3),np.uint8)
ACC=set(range(K-len(acc),K)) if ACCENTI else set()
# DETTAGLI: una zona piccola che contrasta con la zona che la circonda (dE00>=DET_DE) e' un dettaglio
# (pupilla, dente, riflesso, linea del pugno): resta finche' e' >= MIN_DET px; si fondono solo le zone
# piccole di colore simile al vicino, cioe' rumore. Regola di Filippo: occhi e bocca non si perdono mai.
from skimage.color import deltaE_ciede2000 as _de
MIN_DET=int(os.environ.get('PBN_MIN_DET','90')); DET_DE=float(os.environ.get('PBN_DET_DE','16'))
# ...ma solo se e' abbastanza spessa da colorarla col pennarello (raggio inscritto >= DET_R px, ~0,8 mm):
# le schegge sottili non si colorano e restavano senza numero (Filippo, 15/10: numeri illeggibili)
DET_R=float(os.environ.get('PBN_DET_R','5'))
_c=cent.astype(np.float64).copy(); _c[:,0]*=100/255; _c[:,1:]-=128
_c=np.vstack([_c,[[100,0,0]]])  # carta
DE=_de(np.repeat(_c[:,None],NL,1).reshape(-1,3),np.repeat(_c[None],NL,0).reshape(-1,3)).reshape(NL,NL)
for it in range(8):
    changed=0
    comps=[]
    for i in range(NL):
        n,cc,st,_=cv2.connectedComponentsWithStats((lbl==i).astype(np.uint8),connectivity=4)
        for j in range(1,n):
            if st[j,4]<(MIN//4 if i in ACC else MIN): comps.append((st[j,4],i,j,st[j],cc))
    comps.sort(key=lambda t:t[0])
    for a,i,j,(x,y,w,h,_),cc in comps:
        x0,y0=max(x-2,0),max(y-2,0); x1,y1=min(x+w+2,DW),min(y+h+2,DH)
        m=(cc[y0:y1,x0:x1]==j)&(lbl[y0:y1,x0:x1]==i)
        if not m.any(): continue
        ring=cv2.dilate(m.astype(np.uint8),ker).astype(bool)&~m
        nb=lbl[y0:y1,x0:x1][ring]; nb=nb[nb!=i]
        if len(nb)==0: continue
        tgt=np.bincount(nb,minlength=NL).argmax()
        if a>=MIN_DET and DE[i,tgt]>=DET_DE and cv2.distanceTransform(np.pad(m.astype(np.uint8),1),cv2.DIST_L2,3).max()>=DET_R: continue   # dettaglio contrastato e colorabile: si tiene
        lbl[y0:y1,x0:x1][m]=tgt; changed+=1
    print('pass',it,'merged',changed)
    if changed==0: break
# also remove very thin slivers: regions whose max inscribed radius < 3 px
rgb=cv2.cvtColor(cent.reshape(1,K,3).astype(np.uint8),cv2.COLOR_LAB2RGB)[0]
# ordine chiaro->scuro (numero 1 = piu' chiaro); 2_ e 3_ riordinano comunque per luminanza
lum=cent[:,0]; order=np.argsort(-lum); remap=np.zeros(NL,int); remap[order]=np.arange(K); remap[K]=K
lbl=remap[lbl]; lbl[PRINTED]=K; pal=np.vstack([rgb[order],[[255,255,255]]])
pickle.dump((lbl,pal),open(OUT+'/state.pkl','wb'))
print(pal)
