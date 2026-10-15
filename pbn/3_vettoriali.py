"""Tavola vettoriale (testi in inglese):
  SLUG_paint_by_numbers_A4.pdf   2 pagine A4: 1) solo il disegno (zone e linee vettoriali, numeri come testo,
                                 nome e firma gia' stampati come immagine a piena risoluzione, Flate senza perdite);
                                 2) titolo, legenda e istruzioni. Font DejaVu incorporati.
  SLUG_paint_by_numbers_A4_p1_drawing.svg   pagina 1 in SVG
  SLUG_vettoriale_colori.svg     il disegno a colori pieni, vettoriale
Uso: nella cartella del soggetto, dopo 1_.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, base64, io
from reportlab.pdfgen import canvas as rc
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pbn_common as PC
lbl, pal, K, DARK, H, W, OX, OY, printed = PC.load_state()
A4W, A4H = PC.A4W, PC.A4H
def chaikin(p):
    q = np.roll(p, -1, 0); return np.concatenate([0.75 * p + 0.25 * q, 0.25 * p + 0.75 * q], 1).reshape(-1, 2)
# 1. contorni delle zone (per colore, pari-dispari)
paths = {}; frame = None
for i in range(K):
    cs, _ = cv2.findContours((lbl == i).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    for c in cs:
        if len(c) < 3: continue
        a = cv2.approxPolyDP(c, 1.1, True).reshape(-1, 2).astype(float)
        if len(a) < 3: continue
        if i == K - 1 and a[:, 0].min() <= 0 and a[:, 1].min() <= 0 and a[:, 0].max() >= W - 1 and a[:, 1].max() >= H - 1:
            frame = a + [OX + 0.5, OY + 0.5]; continue
        q = []
        for p0, p1 in zip(a, np.roll(a, -1, 0)):
            n = max(1, int(np.hypot(*(p1 - p0)) // 6)); q += [p0 + (p1 - p0) * t for t in np.arange(n) / n]
        polys.append(chaikin(np.array(q)) + [OX + 0.5, OY + 0.5])
    paths[i] = polys
_n, tiny = PC.number_positions(lbl, K, DARK, pal)
nums = [(n, OX + x, OY + y, s, g) for n, x, y, s, g in _n]
hexs = ['#%02X%02X%02X' % tuple(int(v) for v in c) for c in pal]
NOTE_H, NOTE = PC.notes(K - 1, printed is not None)
# area stampata (nome + firma): ritaglio al riquadro utile, a piena risoluzione
pr = None
if printed is not None:
    al = np.array(printed.split()[3]); ys, xs = np.nonzero(al)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    pr = (printed.crop((bx0, by0, bx1, by1)), OX + bx0, OY + by0, bx1 - bx0, by1 - by0)
def d_of(polys): return ' '.join('M' + ' L'.join('%.1f,%.1f' % (x, y) for x, y in p) + ' Z' for p in polys)
# 2. SVG pagina 1
s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="210mm" height="297mm" viewBox="0 0 {A4W} {A4H}" font-family="DejaVu Sans, Arial, sans-serif">',
     f'<rect width="{A4W}" height="{A4H}" fill="#FFFFFF"/>',
     '<g id="zone" fill="none" fill-rule="evenodd" stroke="#5F5F5F" stroke-width="3" stroke-linejoin="round">']
for i in range(K): s.append(f'<path id="{"paper" if i == K - 1 else "colour-%d" % (i + 1)}" data-colour="{hexs[i]}"{" fill=\"#969696\"" if i == DARK else ""} d="{d_of(paths[i])}"/>')
s.append('</g>\n<g id="numbers" text-anchor="middle" dominant-baseline="central">')
for n, x, y, z, g in nums: s.append(f'<text x="{x}" y="{y}" font-size="{z:.0f}" fill="#{g:02X}{g:02X}{g:02X}">{n}</text>')
s.append('</g>')
if pr:
    bio = io.BytesIO(); pr[0].save(bio, 'PNG')
    s.append(f'<image id="printed" x="{pr[1]}" y="{pr[2]}" width="{pr[3]}" height="{pr[4]}" xlink:href="data:image/png;base64,{base64.b64encode(bio.getvalue()).decode()}"/>')
open(PC.SLUG + '_paint_by_numbers_A4_p1_drawing.svg', 'w').write('\n'.join(s) + '\n</svg>\n')
# 3. SVG a colori pieni
c = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{OX} {OY} {W} {H}" width="{W}" height="{H}">', f'<rect x="{OX}" y="{OY}" width="{W}" height="{H}" fill="{hexs[-1]}"/>']
for i in range(K): c.append(f'<path id="colour-{i + 1}" fill="{hexs[i]}" stroke="{hexs[i]}" stroke-width="1.5" stroke-linejoin="round" fill-rule="evenodd" d="{d_of(paths[i] + ([frame] if i == K - 1 and frame is not None else []))}"/>')
open(PC.SLUG + '_vettoriale_colori.svg', 'w').write('\n'.join(c) + '\n</svg>\n')
# 4. PDF vettoriale a due pagine
pdfmetrics.registerFont(TTFont('DV', PC.FR)); pdfmetrics.registerFont(TTFont('DVB', PC.FB))
cv = rc.Canvas(PC.SLUG + '_paint_by_numbers_A4.pdf', pagesize=A4, initialFontName='DV', initialFontSize=10)
cv.setTitle(PC.TITLE); cv.setAuthor('PipSpi'); cv.setPageCompression(1)
k = A4[0] / A4W
def px_page():
    cv.translate(0, A4[1]); cv.scale(k, -k)  # coordinate in px, y verso il basso
def txt(t, x, y, size, font='DV', fill=(0.27, 0.27, 0.27)):
    cv.saveState(); cv.translate(x, y); cv.scale(1, -1); cv.setFillColorRGB(*fill); cv.setFont(font, size)
    cv.drawCentredString(0, -size * 0.36, t); cv.restoreState()
px_page()
cv.setStrokeColorRGB(0.373, 0.373, 0.373); cv.setLineWidth(3); cv.setLineJoin(1)
for i in range(K):
    pa = cv.beginPath()
    for p in paths[i]:
        pa.moveTo(*p[0])
        for x, y in p[1:]: pa.lineTo(x, y)
        pa.close()
    if i == DARK: cv.setFillColorRGB(0.59, 0.59, 0.59)
    cv.drawPath(pa, stroke=1, fill=1 if i == DARK else 0, fillMode=0)
for n, x, y, z, g in nums: txt(str(n), x, y, z, 'DV', (g / 255,) * 3)
if pr:
    cv.saveState(); cv.translate(pr[1], pr[2] + pr[4]); cv.scale(1, -1)
    cv.drawImage(ImageReader(pr[0]), 0, 0, pr[3], pr[4], mask='auto'); cv.restoreState()
cv.showPage()
px_page()
txt(PC.TITLE, A4W / 2, 190, 82, 'DVB', (0.12, 0.12, 0.12))
txt(f'Colour legend – {K - 1} colours', A4W / 2, 300, 46, 'DV', (0.31, 0.31, 0.31))
cells, bottom = PC.legend_grid(K - 1)
for i, (x, y, cw, rh) in enumerate(cells):
    (x0, y0, x1, y1), nc, hc, ns, hs = PC.legend_cell(x, y, cw, rh); cl = pal[i] / 255.
    cv.setFillColorRGB(*cl); cv.setStrokeColorRGB(0.235, 0.235, 0.235); cv.setLineWidth(3)
    cv.roundRect(x0, y0, x1 - x0, y1 - y0, 14, stroke=1, fill=1)
    lum = 0.299 * cl[0] + 0.587 * cl[1] + 0.114 * cl[2]
    txt(str(i + 1), *nc, ns, 'DVB', (1, 1, 1) if lum < 0.55 else (0, 0, 0))
    txt(hexs[i], *hc, hs, 'DV', (0.235,) * 3)
def ltxt(t, x, y, size, font='DV', fill=(0.235,) * 3):
    cv.saveState(); cv.translate(x, y); cv.scale(1, -1); cv.setFillColorRGB(*fill); cv.setFont(font, size)
    cv.drawString(0, -size * 0.36, t); cv.restoreState()
yy = bottom + 110
ltxt(NOTE_H, 160, yy, 46, 'DVB', (0.12,) * 3); yy += 90
for j, t in enumerate(NOTE):
    ltxt(f'{j + 1}.', 160, yy, 36, 'DVB'); ltxt(t, 230, yy, 36); yy += 62
cv.showPage(); cv.save()
print('numeri', len(nums), 'tracciati', sum(len(v) for v in paths.values()))
