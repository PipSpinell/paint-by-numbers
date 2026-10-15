"""Guida passo passo in HTML (testi in inglese): un passo per colore, dal piu' chiaro al piu' scuro.
Ogni colore ha una casella: spuntata, il colore compare dipinto sul disegno; il colore selezionato
lampeggia dove va steso e le zone troppo piccole per un numero sono cerchiate.
File unico, autonomo (dati incorporati), si apre offline in qualsiasi browser.
Uso: nella cartella del soggetto, dopo 1_.  Scrive SLUG_step_by_step.html
(con --frammento scrive anche SLUG_step_by_step.fragment.html, senza <html>/<head>, per pubblicarlo come Artifact).
"""
import os, sys, io, json, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image
import pbn_common as PC

lbl, pal, K, DARK, H, W, OX, OY, printed = PC.load_state()
nums, tiny = PC.number_positions(lbl, K, DARK, pal)

def b64png(im):
    bio = io.BytesIO(); im.save(bio, 'PNG', optimize=True); return base64.b64encode(bio.getvalue()).decode()

labels = b64png(Image.fromarray(lbl.astype(np.uint8), 'L'))
pr = None
if printed is not None:
    al = np.array(printed.split()[3]); ys, xs = np.nonzero(al)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    pr = dict(x=x0, y=y0, src='data:image/png;base64,' + b64png(printed.crop((x0, y0, x1, y1))))
cols = []
for i in range(K - 1):
    n = cv2.connectedComponents((lbl == i).astype(np.uint8), connectivity=4)[0] - 1
    c = [int(v) for v in pal[i]]
    cols.append(dict(n=i + 1, rgb=c, hex='#%02X%02X%02X' % tuple(c), areas=int(n),
                     tiny=sum(1 for t in tiny if t[0] == i + 1),
                     light=bool(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] > 150)))
data = dict(name=PC.NOME, slug=PC.SLUG, W=W, H=H, dark=K - 1, paper=K - 1,
            colours=cols, nums=[[n, int(x), int(y), round(s), g] for n, x, y, s, g in nums],
            tiny=[[n, x, y, round(r, 1)] for n, x, y, r in tiny], printed=pr)
head_note, steps = PC.notes(K - 1, printed is not None)

BODY = r'''<title>__TITLE__</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&display=swap">
<style>
/* Layout: drawing on a sheet of paper (sticky) beside a vertical colour timeline; one column on phones. */
:root {
  --bg: #eef0f3; --sheet: #ffffff; --ink: #1d2230; --muted: #5d6475; --line: #d4d8e0;
  --accent: #d6246e; --accent-soft: #fbe3ee; --done: #2f7d4f;
  --display: "Bricolage Grotesque", "Avenir Next", "Segoe UI", system-ui, sans-serif;
  --body: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #161922; --sheet: #20242f; --ink: #e9ecf2; --muted: #a2a9b8; --line: #343a48;
  --accent: #ff5c9a; --accent-soft: #3a1f2c; --done: #6fcf97; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #161922; --sheet: #20242f; --ink: #e9ecf2; --muted: #a2a9b8; --line: #343a48;
  --accent: #ff5c9a; --accent-soft: #3a1f2c; --done: #6fcf97; color-scheme: dark }
* { box-sizing: border-box }
body { background: var(--bg); color: var(--ink); font: 15px/1.5 var(--body); margin: 0 }
.wrap { max-width: 1320px; margin: 0 auto; padding-block: 20px 40px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 20px }
header h1 { font: 700 clamp(1.5rem, 3.2vw, 2.2rem)/1.15 var(--display); margin: 0; text-wrap: balance }
header p { margin: 4px 0 0; color: var(--muted) }
.main { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); gap: 20px; align-items: start }
@media (max-width: 860px) { .main { grid-template-columns: minmax(0, 1fr) } }
.stage-col { position: sticky; top: env(safe-area-inset-top, 0px); display: grid; gap: 10px; min-width: 0 }
@media (max-width: 860px) { .stage-col { position: static } }
.stage { background: #fff; border: 1px solid var(--line); border-radius: 6px; overflow: auto; max-height: calc(100vh - 120px); }
@media (max-width: 860px) { .stage { max-height: 72vh } }
.layers { position: relative; margin: 0 auto }
.layers canvas { position: absolute; inset: 0; width: 100%; height: 100% }
#glow { filter: drop-shadow(0 0 2px var(--accent)) drop-shadow(0 0 3px var(--accent)); animation: pulse 1.4s ease-in-out infinite }
@keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: .35 } }
@media (prefers-reduced-motion: reduce) { #glow { animation: none } }
.bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center }
.bar label { display: flex; gap: 6px; align-items: center; color: var(--muted); font-size: .9rem }
button { font: 600 .9rem var(--body); color: var(--ink); background: var(--sheet); border: 1px solid var(--line);
  border-radius: 999px; padding: 7px 14px; cursor: pointer }
button.primary { background: var(--accent); border-color: var(--accent); color: #fff }
button:focus-visible, input:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px }
.side { display: grid; gap: 16px; min-width: 0 }
.panel { background: var(--sheet); border: 1px solid var(--line); border-radius: 6px; padding: 16px }
.panel h2 { font: 700 1.05rem var(--display); margin: 0 0 8px; letter-spacing: .01em }
.progress { height: 8px; background: var(--line); border-radius: 99px; overflow: hidden; margin-top: 8px }
.progress span { display: block; height: 100%; background: var(--done); width: 0; transition: width .3s }
.count { font-variant-numeric: tabular-nums; color: var(--muted); font-size: .9rem }
ol.steps { list-style: none; margin: 0; padding: 0; display: grid; gap: 2px }
ol.steps li { display: grid; grid-template-columns: auto auto minmax(0, 1fr); gap: 12px; align-items: center;
  padding: 8px 10px; border-radius: 6px; cursor: pointer; border: 2px solid transparent }
ol.steps li:hover { background: var(--bg) }
ol.steps li.focus { border-color: var(--accent); background: var(--accent-soft) }
ol.steps input { width: 20px; height: 20px; accent-color: var(--done); cursor: pointer }
.sw { width: 46px; height: 32px; border-radius: 5px; border: 1px solid rgba(0,0,0,.35); display: grid; place-items: center;
  font: 700 1rem var(--display); font-variant-numeric: tabular-nums }
.meta { min-width: 0; font-size: .88rem; color: var(--muted); font-variant-numeric: tabular-nums }
.meta b { color: var(--ink); font-weight: 600 }
li.done .meta b { text-decoration: line-through; text-decoration-color: var(--done) }
.how ol { margin: 0; padding-left: 1.3em; display: grid; gap: 4px; max-width: 65ch }
</style>
<div class="wrap">
  <header>
    <h1>__NAME__</h1>
    <p>Step-by-step painting guide · <span id="ncol"></span> colours, lightest to darkest</p>
  </header>
  <div class="main">
    <div class="stage-col">
      <div class="bar">
        <button id="prev">Previous colour</button>
        <button id="next" class="primary">Done, next colour</button>
        <label for="fade"><input type="checkbox" id="fade" checked> Fade the rest</label>
        <label for="zoom">Zoom <input type="range" id="zoom" min="100" max="400" step="25" value="100"></label>
      </div>
      <div class="stage" id="stage"><div class="layers" id="layers">
        <canvas id="base"></canvas><canvas id="fadecv"></canvas><canvas id="glow"></canvas>
      </div></div>
    </div>
    <div class="side">
      <section class="panel">
        <h2 id="nowtitle">Now painting</h2>
        <div class="count" id="nowtext"></div>
        <div class="progress"><span id="prog"></span></div>
        <div class="bar" style="margin-top:12px">
          <button id="all">Show finished</button><button id="reset">Start over</button>
        </div>
      </section>
      <section class="panel">
        <h2>Colours</h2>
        <ol class="steps" id="steps"></ol>
      </section>
      <section class="panel how">
        <h2>__HOWTITLE__</h2>
        <ol>__HOWSTEPS__</ol>
      </section>
    </div>
  </div>
</div>
<script>
const D = __DATA__;
const LABELS = "data:image/png;base64,__LABELS__";
const N = D.colours.length, W = D.W, H = D.H;
const done = new Array(N + 1).fill(false); let focus = 1;
const KEY = 'pbn-steps-' + D.slug;
try { const s = JSON.parse(localStorage.getItem(KEY) || 'null'); if (s) { s.done.forEach((v, i) => done[i] = v); focus = s.focus || 1 } } catch (e) {}
function save() { try { localStorage.setItem(KEY, JSON.stringify({ done, focus })) } catch (e) {} }
document.getElementById('ncol').textContent = N;
const cvs = ['base', 'fadecv', 'glow'].map(id => { const c = document.getElementById(id); c.width = W; c.height = H; return c });
let lab = null, edge = null, printedImg = null;
function load(src) { return new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = src }) }

function prep(img) {
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const x = c.getContext('2d'); x.drawImage(img, 0, 0);
  const d = x.getImageData(0, 0, W, H).data; lab = new Uint8Array(W * H); edge = new Uint8Array(W * H);
  for (let p = 0; p < W * H; p++) lab[p] = d[p * 4];
  for (let y = 0; y < H; y++) for (let x2 = 0; x2 < W; x2++) {
    const p = y * W + x2, l = lab[p];
    if ((x2 + 1 < W && lab[p + 1] !== l) || (y + 1 < H && lab[p + W] !== l) || (x2 > 0 && lab[p - 1] !== l) || (y > 0 && lab[p - W] !== l)) edge[p] = 1;
  }
}

function drawBase() {
  const ctx = cvs[0].getContext('2d'), im = ctx.createImageData(W, H), o = im.data;
  const pal = D.colours.map(c => c.rgb), paper = D.paper, darkL = N - 1;
  for (let p = 0; p < W * H; p++) {
    const l = lab[p]; let r = 255, g = 255, b = 255;
    if (l !== paper && done[l + 1]) { [r, g, b] = pal[l] }
    else if (edge[p]) { r = g = b = 95 }
    else if (l === darkL) { r = g = b = 222 }
    o[p * 4] = r; o[p * 4 + 1] = g; o[p * 4 + 2] = b; o[p * 4 + 3] = 255;
  }
  ctx.putImageData(im, 0, 0);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  for (const [n, x, y, s, gr] of D.nums) {
    if (done[n]) continue;
    ctx.font = s + 'px "DejaVu Sans", Verdana, sans-serif'; ctx.fillStyle = `rgb(${gr},${gr},${gr})`; ctx.fillText(n, x, y);
  }
  if (printedImg) ctx.drawImage(printedImg, D.printed.x, D.printed.y);
}

function drawFocus() {
  const f = cvs[1].getContext('2d'), g = cvs[2].getContext('2d');
  const fi = f.createImageData(W, H), gi = g.createImageData(W, H), fo = fi.data, go = gi.data;
  const k = focus - 1, c = D.colours[k].rgb, fade = document.getElementById('fade').checked;
  // finished: nothing to highlight, the drawing shows its real colours
  if (done.slice(1).every(Boolean)) { f.clearRect(0, 0, W, H); g.clearRect(0, 0, W, H); return }
  for (let p = 0; p < W * H; p++) {
    const l = lab[p];
    if (l === k) { go[p * 4] = c[0]; go[p * 4 + 1] = c[1]; go[p * 4 + 2] = c[2]; go[p * 4 + 3] = 255 }
    else if (fade && !done[l + 1]) { fo[p * 4] = fo[p * 4 + 1] = fo[p * 4 + 2] = 255; fo[p * 4 + 3] = 115 }  // painted colours stay full strength
  }
  f.putImageData(fi, 0, 0); g.putImageData(gi, 0, 0);
  g.lineWidth = 6; g.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#d6246e';
  for (const [n, x, y, r] of D.tiny) if (n === focus) { g.beginPath(); g.arc(x, y, Math.max(26, r * 3), 0, 7); g.stroke() }
}

function renderList() {
  const ol = document.getElementById('steps'); ol.innerHTML = '';
  D.colours.forEach(c => {
    const li = document.createElement('li'); li.className = (c.n === focus ? 'focus ' : '') + (done[c.n] ? 'done' : '');
    const id = 'c' + c.n;
    li.innerHTML = `<input type="checkbox" id="${id}" ${done[c.n] ? 'checked' : ''} aria-label="Colour ${c.n} painted">
      <span class="sw" style="background:${c.hex};color:${c.light ? '#111' : '#fff'}">${c.n}</span>
      <span class="meta"><b>Step ${c.n}</b> · ${c.hex}<br>${c.areas} area${c.areas === 1 ? '' : 's'}${c.tiny ? ` · ${c.tiny} without number` : ''}</span>`;
    li.querySelector('input').addEventListener('click', e => { e.stopPropagation(); done[c.n] = e.target.checked; update(true) });
    li.addEventListener('click', () => { focus = c.n; update(false) });
    ol.appendChild(li);
  });
}

function update(baseToo) {
  if (baseToo) drawBase(); drawFocus(); renderList(); save();
  const c = D.colours[focus - 1], nd = done.filter(Boolean).length;
  document.getElementById('nowtitle').textContent = `Now painting: colour ${focus}`;
  document.getElementById('nowtext').textContent = `${c.hex} · ${c.areas} areas${c.tiny ? `, ${c.tiny} too small for a number (circled)` : ''} · ${nd} of ${N} colours done`;
  document.getElementById('prog').style.width = (100 * nd / N) + '%';
}

function fit() {
  const st = document.getElementById('stage'), z = +document.getElementById('zoom').value / 100;
  const maxH = st.clientHeight > 0 && window.innerWidth > 860 ? window.innerHeight - 130 : Infinity;
  const w = Math.min(st.clientWidth - 2, maxH * W / H) * z;
  const L = document.getElementById('layers'); L.style.width = w + 'px'; L.style.height = (w * H / W) + 'px';
}
document.getElementById('zoom').addEventListener('input', fit);
window.addEventListener('resize', fit);
document.getElementById('fade').addEventListener('change', () => drawFocus());
document.getElementById('next').addEventListener('click', () => { done[focus] = true; if (focus < N) focus++; update(true) });
document.getElementById('prev').addEventListener('click', () => { if (focus > 1) focus--; update(false) });
document.getElementById('all').addEventListener('click', () => { for (let i = 1; i <= N; i++) done[i] = true; update(true) });
document.getElementById('reset').addEventListener('click', () => { done.fill(false); focus = 1; update(true) });

(async () => {
  fit();
  const img = await load(LABELS); prep(img);
  if (D.printed) printedImg = await load(D.printed.src);
  update(true); fit();
})();
</script>
'''
def esc(t): return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
body = (BODY.replace('__TITLE__', esc(PC.NOME) + ' Painting Guide').replace('__NAME__', esc(PC.NOME))
        .replace('__HOWTITLE__', head_note).replace('__HOWSTEPS__', ''.join(f'<li>{esc(t)}</li>' for t in steps))
        .replace('__DATA__', json.dumps(data, separators=(',', ':')).replace('</', '<\\/')).replace('__LABELS__', labels))
full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n</head>\n<body>\n'
        + body + '\n</body>\n</html>\n')
open(PC.SLUG + '_step_by_step.html', 'w').write(full)
if '--frammento' in sys.argv: open(PC.SLUG + '_step_by_step.fragment.html', 'w').write(body)
print('guida html ok', len(full) // 1024, 'KB', 'zone senza numero', len(tiny))
