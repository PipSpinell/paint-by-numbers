"""Tavola raster a 300 dpi su due pagine A4 (testi in inglese):
  SLUG_paint_by_numbers_A4_p1_drawing.png  solo il disegno numerato, con nome del boss e firma gia' stampati
  SLUG_paint_by_numbers_A4_p2_legend.png   titolo, legenda (campione, numero, hex) e istruzioni
Uso: nella cartella del soggetto, dopo 1_:  python3 2_tavola_png_pdf.py .
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import pbn_common as PC
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
lbl, pal, K, DARK, H, W, OX, OY, printed = PC.load_state()
# pagina 1: linee, zone grigie (colore piu' scuro), numeri
b = np.zeros((H, W), bool); b[:, 1:] |= lbl[:, 1:] != lbl[:, :-1]; b[1:, :] |= lbl[1:, :] != lbl[:-1, :]
b = cv2.dilate(b.astype(np.uint8), np.ones((2, 2), np.uint8)).astype(bool)
g = np.full((H, W), 255, np.uint8); g[lbl == DARK] = 150; g[b] = 95  # grigio medio: occhi, bocca e linee del disegno restano leggibili
g = cv2.GaussianBlur(g, (3, 3), 0.6)
art = Image.fromarray(g).convert('RGB'); d = ImageDraw.Draw(art)
fonts = {}
def F(s, f=PC.FR):
    if (s, f) not in fonts: fonts[s, f] = ImageFont.truetype(f, s)
    return fonts[s, f]
nums, tiny = PC.number_positions(lbl, K, DARK, pal)
for n, x, y, s, gr in nums: d.text((x, y), str(n), fill=(gr, gr, gr), font=F(int(s)), anchor='mm')
if printed is not None: art.paste(printed.convert('RGB'), (0, 0), printed.split()[3])
p1 = Image.new('RGB', (PC.A4W, PC.A4H), 'white'); p1.paste(art, (OX, OY))
p1.save(f'{OUT}/{PC.SLUG}_paint_by_numbers_A4_p1_drawing.png', dpi=(300, 300))
# pagina 2: legenda
n = K - 1
p2 = Image.new('RGB', (PC.A4W, PC.A4H), 'white'); q = ImageDraw.Draw(p2)
q.text((PC.A4W // 2, 190), PC.TITLE, fill=(30, 30, 30), font=F(82, PC.FB), anchor='mm')
q.text((PC.A4W // 2, 300), f'Colour legend – {n} colours', fill=(80, 80, 80), font=F(46), anchor='mm')
cells, bottom = PC.legend_grid(n)
for i, (x, y, cw, rh) in enumerate(cells):
    c = tuple(int(v) for v in pal[i]); sw, nc, hc, ns, hs = PC.legend_cell(x, y, cw, rh)
    q.rounded_rectangle(sw, radius=14, fill=c, outline=(60, 60, 60), width=3)
    lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    q.text(nc, str(i + 1), fill=(255, 255, 255) if lum < 140 else (0, 0, 0), font=F(ns, PC.FB), anchor='mm')
    q.text(hc, '#%02X%02X%02X' % c, fill=(60, 60, 60), font=F(hs), anchor='mm')
head, lines = PC.notes(n, printed is not None)
y = bottom + 110
q.text((160, y), head, fill=(30, 30, 30), font=F(46, PC.FB), anchor='lm'); y += 90
for k, t in enumerate(lines):
    q.text((160, y), f'{k + 1}.', fill=(60, 60, 60), font=F(36, PC.FB), anchor='lm')
    q.text((230, y), t, fill=(60, 60, 60), font=F(36), anchor='lm'); y += 62
p2.save(f'{OUT}/{PC.SLUG}_paint_by_numbers_A4_p2_legend.png', dpi=(300, 300))
print('numeri', len(nums), 'zone senza numero', len(tiny), 'colori', n, 'stampati', printed is not None)
