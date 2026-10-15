"""Stima quanti colori usare per un paint by numbers.

Due vincoli opposti, distanze in CIEDE2000 (differenza di colore percepita):
  - FEDELTA' (limite inferiore): con K colori, la quota di area dipinta con un colore
    chiaramente sbagliato (dE00 > 12) deve restare <= 1,2%, sia a K che a K+1
    (cosi' un risultato fortunato del clustering non basta).
  - DISTINGUIBILITA' (limite superiore): la coppia di colori piu' vicina deve avere
    dE00 >= 7, altrimenti due vasetti sono quasi uguali e chi dipinge li confonde.
  - Ogni colore deve coprire almeno lo 0,5% dell'area dipinta.
Consiglio = il limite inferiore; se supera quello superiore, vince il superiore.
Le soglie sono state tarate sul Green Goblin: vanno verificate sulle prossime immagini.
Il bianco quasi puro e' carta e non conta come colore.
Uso: python3 consiglia_colori.py immagine.jpg [Kmin Kmax]
"""
import numpy as np, cv2, sys
from sklearn.cluster import KMeans
from skimage.color import deltaE_ciede2000
from PIL import Image
MIN_PAIR, MIN_SHARE, WRONG_DE, MAX_WRONG = 9.0, 0.005, 12.0, 0.03  # 15/10/2026: 7/0.012 fino a 28 dava troppi colori (Filippo)
K_FLOOR = 12  # almeno 12 colori base: con 11 o meno Filippo li trovava troppo pochi

def prepare(path, height=1200):
    img=np.array(Image.open(path).convert('RGB'))
    s=height/img.shape[0]; big=cv2.resize(img,(int(img.shape[1]*s),height),interpolation=cv2.INTER_LANCZOS4)
    bgr=cv2.cvtColor(big,cv2.COLOR_RGB2BGR); sm=cv2.pyrMeanShiftFiltering(bgr,8,22); sm=cv2.bilateralFilter(sm,7,40,7)
    lab=cv2.cvtColor(sm,cv2.COLOR_BGR2LAB).reshape(-1,3).astype(np.float32)
    paper=(lab[:,0]>238)&(np.abs(lab[:,1]-128)<7)&(np.abs(lab[:,2]-128)<9)
    L=lab[~paper].copy(); L[:,0]*=100/255; L[:,1:]-=128
    return L

def scan(L, kmin=6, kmax=24, seeds=(0,1,2)):
    rng=np.random.default_rng(0); X=L[rng.choice(len(L),min(60000,len(L)),replace=False)]
    rows=[]
    for k in range(kmin,kmax+1):
        err=[];pair=[];share=[];wrong=[]
        for sd in seeds:
            km=KMeans(k,n_init=3,random_state=sd).fit(X); c=km.cluster_centers_
            d=deltaE_ciede2000(X,c[km.labels_]); err.append(d.mean()); wrong.append((d>WRONG_DE).mean())
            pd=deltaE_ciede2000(c[:,None,:].repeat(k,1),c[None,:,:].repeat(k,0)); pd[np.eye(k,dtype=bool)]=1e9
            pair.append(pd.min()); share.append((np.bincount(km.labels_,minlength=k)/len(X)).min())
        rows.append(dict(k=k,err=float(np.median(err)),pair=float(np.median(pair)),share=float(np.median(share)),wrong=float(np.median(wrong))))
    return rows

def recommend(rows):
    byk={r['k']:r for r in rows}
    lo=next((r['k'] for r in rows if r['wrong']<=MAX_WRONG and byk.get(r['k']+1,r)['wrong']<=MAX_WRONG),rows[-1]['k'])
    hi=max([r['k'] for r in rows if r['pair']>=MIN_PAIR and r['share']>=MIN_SHARE] or [rows[0]['k']])
    return max(K_FLOOR, min(lo,hi)), lo, hi

if __name__=='__main__':
    a=sys.argv; L=prepare(a[1]); rows=scan(L,int(a[2]) if len(a)>2 else 6,int(a[3]) if len(a)>3 else 24)
    for r in rows: print(f"K={r['k']:2d}  errore medio dE00={r['err']:5.2f}  coppia piu' vicina dE00={r['pair']:5.2f}  colore piu' piccolo={r['share']*100:4.1f}%  area col colore sbagliato={r['wrong']*100:4.1f}%")
    k,lo,hi=recommend(rows)
    print(f'Fedelta\' ok da K={lo}; distinguibili fino a K={hi}. CONSIGLIATI: {k}')
