"""Demo: la pagina 1 della tavola (solo disegno, nome e firma gia' stampati) colorata a mano zona per zona.
Segue /mnt/project-files/tools/stile_demo.md (specifiche di Filippo):
  - per ogni zona: prima il ripasso del perimetro (fascia sottile, un filo piu' carica),
    poi il riempimento con passate parallele leggermente sovrapposte, direzione prevalente per zona;
  - tracce delicate: larghezza della punta costante, piccole variazioni di pressione, minime deviazioni,
    qualche ripresa/giunzione; nessuna texture attraversa zone diverse;
  - colori della legenda, zone grigie col colore piu' scuro, zone bianche = carta; numeri e linee coperti.
Da lanciare dopo 1_, nella cartella del soggetto. Scrive SLUG_demo_A4.png (300 dpi, A4).
Nome e firma restano come stampati (non si colorano).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image
import pbn_common as PC
SLUG = PC.SLUG
lbl, pal, K, DARK, H, W, OX, OY, printed = PC.load_state()
PAPER = K - 1
rng = np.random.default_rng(7)

def smooth_noise(sig, amp):
    n = rng.standard_normal((H, W)).astype(np.float32); n = cv2.GaussianBlur(n, (0, 0), sig)
    return n / (n.std() + 1e-6) * amp
wob = smooth_noise(35, 1.6)          # deviazioni della mano (px, trasversali al tratto)
press_field = smooth_noise(60, 1.0)  # variazione lenta di pressione
edge_n = smooth_noise(6, 1.0)        # irregolarita' della fascia di perimetro

base = pal[lbl].astype(np.float32) / 255.
shade = np.ones((H, W), np.float32)  # moltiplicatore di luminosita' (1 = colore pieno della legenda)

order = list(range(K - 1))  # dal piu' chiaro al piu' scuro, come in legenda
for i in order:
    n, cc, st, _ = cv2.connectedComponentsWithStats((lbl == i).astype(np.uint8), connectivity=4)
    for j in range(1, n):
        x, y, w, h, a = st[j]
        m = cc[y:y + h, x:x + w] == j
        mp = np.pad(m.astype(np.uint8), 1)
        dt = cv2.distanceTransform(mp, cv2.DIST_L2, 3)[1:-1, 1:-1]
        r = float(dt.max())
        # punta: stretta nei dettagli, piu' larga nelle zone ampie
        tip = float(np.clip(r * 0.9, 7, 30))
        pitch = tip * 0.82                           # passate affiancate con leggera sovrapposizione
        over = tip - pitch
        pw = float(np.clip(r * 0.35, 2.5, 7.0))      # larghezza fascia di perimetro
        # direzione prevalente: asse lungo della zona (+/- un po' di mano), casuale nelle zone piccole
        ys, xs = np.nonzero(m)
        if a > 400:
            c = np.cov(np.vstack([xs, ys]).astype(np.float32)); ev, evec = np.linalg.eigh(c)
            th = np.arctan2(evec[1, 1], evec[0, 1]) + rng.normal(0, 0.18)
        else:
            th = rng.uniform(0, np.pi)
        X = xs + x; Y = ys + y
        u = X * np.cos(th) + Y * np.sin(th) + rng.uniform(0, pitch) + wob[Y, X]
        v = -X * np.sin(th) + Y * np.cos(th)
        band = np.floor(u / pitch).astype(int); t = u / pitch - band
        coats = 1 + (t * pitch < over)                # sovrapposizione con la passata precedente
        # riprese lungo la passata: lunghezza dei tratti proporzionale allo spazio disponibile
        nb = band.max() - band.min() + 1; b0 = band - band.min()
        seg = np.clip(r * rng.uniform(5, 12), 40, 520)
        segL = seg * rng.uniform(0.7, 1.3, nb)
        segO = rng.uniform(0, 1, nb) * segL
        q = (v + segO[b0]) / segL[b0]; fq = q - np.floor(q)
        dj = np.minimum(fq, 1 - fq) * segL[b0]
        joint = dj < rng.uniform(1.5, 3.5)            # giunzione/ripartenza appena visibile
        # pressione: per passata e per tratto, piu' una variazione lenta
        pb = rng.normal(0, 0.006, nb)[b0] + rng.normal(0, 0.004, int(np.floor(q).max() - np.floor(q).min() + 2))[(np.floor(q) - np.floor(q).min()).astype(int)]
        fill = 1.0 - 0.02 * (coats - 1) - 0.009 * joint + pb + press_field[Y, X] * 0.004
        # traccia della punta: leggerissimo profilo trasversale (bordi della passata un filo piu' carichi)
        fill -= 0.006 * np.cos(2 * np.pi * t) ** 8
        # perimetro: fascia sottile ripassata per prima, un filo piu' carica; il riempimento la incontra
        d = dt[ys, xs]
        edge = d < pw + 0.8 * edge_n[Y, X]
        stop = d < rng.uniform(0.3, 1.0) * pw         # dove si arresta il riempimento vicino al bordo
        val = np.where(edge, np.where(stop, 0.955, 0.94), fill)
        shade[Y, X] = val

col = base * shade[..., None]
paper = lbl == PAPER
# grana finissima del colore steso (la carta resta bianca come nella tavola stampata)
grain = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.8) * 0.004
col += grain[..., None]
col[paper] = 1.0
out = (np.clip(col, 0, 1) * 255).astype(np.uint8)
art = Image.fromarray(out)
if printed is not None: art.paste(printed.convert('RGB'), (0, 0), printed.split()[3])
page = Image.new('RGB', (PC.A4W, PC.A4H), 'white'); page.paste(art, (OX, OY))
page.save(SLUG + '_demo_A4.png', dpi=(300, 300))
print('demo pennarello ok', W, H)
