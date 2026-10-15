"""Parti comuni a 1_, 2_, 3_, 6_ (impaginazione decisa con Filippo il 15/10/2026).
Tavola su due pagine A4 a 300 dpi:
  pagina 1: solo il disegno, il piu' grande possibile (nome del boss e firma PipSpi gia' stampati);
  pagina 2: titolo, legenda e istruzioni.
Testi in inglese.
"""
import os, numpy as np, cv2, pickle
from PIL import Image

A4W, A4H, MARGIN = 2480, 3508, 110
FB = os.environ.get('PBN_FONT_BOLD', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
FR = os.environ.get('PBN_FONT', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
NOME = os.environ.get('PBN_NOME', 'Subject')
SLUG = os.environ.get('PBN_SLUG', 'soggetto')
TITLE = 'Paint by Numbers – ' + NOME


def drawing_size(h, w):
    """Dimensioni del disegno in px (300 dpi) per riempire la pagina 1 entro i margini."""
    s = min((A4H - 2 * MARGIN) / h, (A4W - 2 * MARGIN) / w)
    return int(round(h * s)), int(round(w * s))


def notes(n, printed):
    """Istruzioni in inglese per pagina 2: (titolo, righe). Come si colora: vedi stile_demo.md."""
    t = [f'Work from colour 1 (lightest) to colour {n} (darkest), one colour at a time.',
         'For each area, first trace its outline with the marker tip, just inside the printed line.',
         'Then fill it with straight, parallel strokes in one direction, each stroke slightly overlapping the last.',
         'Keep a light, even pressure and do not go back over ink that is already dry: that leaves streaks.',
         'Let light colours dry before painting the dark colours next to them.',
         f'Light grey areas take colour {n}. White areas without a number stay unpainted.',
         'Areas too small for a number are shown in the step-by-step guide (HTML file).']
    if printed:
        t.append('The name and the signature are already printed: leave them as they are.')
    return 'How to use your markers', t


def load_state():
    """lbl, pal riordinati chiaro->scuro (1 = piu' chiaro), DARK, offset del disegno, maschera stampata."""
    lbl, pal = pickle.load(open('state.pkl', 'rb')); K = len(pal)
    L = cv2.cvtColor(pal[:-1].reshape(1, -1, 3).astype(np.uint8), cv2.COLOR_RGB2LAB)[0, :, 0].astype(int)
    o = np.argsort(-L, kind='stable'); r = np.empty(K, int); r[o] = np.arange(K - 1); r[K - 1] = K - 1
    lbl = r[lbl]; pal = np.vstack([pal[:-1][o], pal[-1:]])
    H, W = lbl.shape
    OX, OY = (A4W - W) // 2, (A4H - H) // 2
    printed = Image.open('printed.png').convert('RGBA') if os.path.exists('printed.png') else None
    return lbl, pal, K, K - 2, H, W, OX, OY, printed


def legend_grid(n):
    """Riquadri della legenda in pagina 2: (x, y, w, h) per ciascun colore."""
    cols = 4 if n <= 24 else 5
    rows = -(-n // cols)
    x0, top = 160, 420
    cw = (A4W - 2 * x0) // cols
    rh = min(330, (A4H - top - 420) // max(rows, 1))
    return [(x0 + (i % cols) * cw, top + (i // cols) * rh, cw, rh) for i in range(n)], top + rows * rh


MIN_NUM = 20          # corpo minimo leggibile (px a 300 dpi, ~1,7 mm): sotto, il numero non si legge
MIN_R = 9             # zone piu' strette di ~1,5 mm: niente numero, cerchiate nella guida HTML passo passo


def num_style(rgb):
    """Corpo massimo e grigio del numero secondo la chiarezza del colore: sui colori chiari numeri piccoli
    e piu' tenui, altrimenti il pennarello chiaro non li copre."""
    L = float(cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2LAB)[0, 0, 0]) * 100 / 255
    if L > 75: return 30, 140
    if L > 55: return 40, 100
    return 52, 70


def number_positions(lbl, K, DARK, pal):
    """Numeri (n, x, y, corpo, grigio) in px del disegno: uno per zona abbastanza grande, pochi ripetuti
    nelle zone grandi. Le zone troppo piccole tornano in tiny (n, x, y, r) per la guida HTML."""
    out, tiny = [], []
    for i in range(K - 1):
        cap, grey = num_style(pal[i])
        n, cc, st, _ = cv2.connectedComponentsWithStats((lbl == i).astype(np.uint8), connectivity=4)
        for j in range(1, n):
            x, y, w, h, a = st[j]
            m = np.pad((cc[y:y + h, x:x + w] == j).astype(np.uint8), 1)
            dt = cv2.distanceTransform(m, cv2.DIST_L2, 5)
            r = dt.max(); py, px = np.unravel_index(dt.argmax(), dt.shape)
            if r < MIN_R:
                tiny.append((i + 1, int(x + px - 1), int(y + py - 1), float(max(r, 1)))); continue
            out.append((i + 1, x + px - 1, y + py - 1, float(np.clip(r * 1.1, MIN_NUM, cap)), grey))
            dt2 = dt.copy(); yy, xx = np.ogrid[:dt.shape[0], :dt.shape[1]]
            R = 560
            dt2[(yy - py) ** 2 + (xx - px) ** 2 < R * R] = 0
            for _ in range(5):
                v = dt2.max()
                if v < 22: break
                qy, qx = np.unravel_index(dt2.argmax(), dt2.shape)
                out.append((i + 1, x + qx - 1, y + qy - 1, float(np.clip(v * 1.1, MIN_NUM, cap)), grey))
                dt2[(yy - qy) ** 2 + (xx - qx) ** 2 < R * R] = 0
    return out, tiny


def legend_cell(x, y, cw, rh):
    """Dentro un riquadro della legenda: (rettangolo del campione x0,y0,x1,y1), centro numero, centro hex, corpi."""
    sh = int(rh * 0.56)
    return (x + 14, y, x + cw - 14, y + sh), (x + cw / 2, y + sh / 2), (x + cw / 2, y + sh + 48), int(min(78, sh * 0.45)), 34
