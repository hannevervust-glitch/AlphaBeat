import os, json
import glyphsLib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.backends.backend_pdf import PdfPages
from shapely.geometry import LineString

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, 'out', 'Letters')
os.makedirs(os.path.join(OUT, 'png'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'svg'), exist_ok=True)
font = glyphsLib.GSFont(os.path.join(HERE, 'out', 'Alphabeat.glyphs'))
REC = {k: v for k, v in json.load(open(os.path.join(HERE, 'letters.json'))).items() if not k.startswith('_')}
DIG = dict(zip('0123456789', ['zero','one','two','three','four','five','six','seven','eight','nine']))
FAM = {'0':'Number · round','1':'Number · stem','2':'Number · arch','3':'Number · descending','4':'Number · descending','5':'Number · descending','6':'Number · ascending','7':'Number · descending','8':'Number · ascending','9':'Number · descending','a':'Bowl and hook','b':'Bowl and stem','c':'Round','d':'Bowl and stem','e':'Round','f':'Stem','g':'Bowl and hook','h':'Arch','i':'Stem','j':'Stem','k':'Diagonal','l':'Stem','m':'Arch','n':'Arch (control letter)','o':'Round (control letter)','p':'Bowl and stem','q':'Bowl and stem','r':'Arch','s':'Round','t':'Stem','u':'Arch','v':'Diagonal','w':'Diagonal','x':'Diagonal','y':'Diagonal','z':'Diagonal'}
LINES = [(750, 'Ascender 750'), (625, 'Dot / t 625'), (500, 'x-height 500'), (250, 'Centre 250'), (125, 'Aperture 125'), (0, 'Baseline 0'), (-250, 'Descender -250')]
ACC, INK, MUTED, GRID = '#000000', '#16191D', '#6B737B', '#D5DADF'
STROKE = 64

def bez(p0, c1, c2, p3, n=30):
    return [((1-t)**3*p0[0]+3*(1-t)**2*t*c1[0]+3*(1-t)*t*t*c2[0]+t**3*p3[0],
             (1-t)**3*p0[1]+3*(1-t)**2*t*c1[1]+3*(1-t)*t*t*c2[1]+t**3*p3[1]) for t in [i/n for i in range(1, n+1)]]

def segments(nodes):
    """Group Glyphs nodes into ('line', p) / ('curve', c1, c2, p) segments."""
    segs, pend = [], []
    for n in nodes[1:]:
        p = (n.position.x, n.position.y)
        if n.type == 'offcurve': pend.append(p)
        elif n.type == 'curve': segs.append(('curve', pend[0], pend[1], p)); pend = []
        else: segs.append(('line', p))
    return segs

pdf = PdfPages(os.path.join(HERE, 'out', 'Alphabeat-letters-1000upm.pdf'))
summary = {}
for c in 'abcdefghijklmnopqrstuvwxyz0123456789':
    layer = font.glyphs[DIG.get(c, c)].layers[0]; W = layer.width; nodes = layer.paths[0].nodes
    start = (nodes[0].position.x, nodes[0].position.y); segs = segments(nodes)
    flat = [start]
    for s in segs: flat += [s[1]] if s[0] == 'line' else bez(flat[-1], s[1], s[2], s[3])

    # ---------- clean SVG (font units, y up) ----------
    d = f'M{start[0]} {start[1]}'
    for s in segs:
        d += f' L{s[1][0]} {s[1][1]}' if s[0] == 'line' else f' C{s[1][0]} {s[1][1]} {s[2][0]} {s[2][1]} {s[3][0]} {s[3][1]}'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="1000" viewBox="0 -750 {W} 1000">\n'
           f'  <!-- Alphabeat "{c}" · 1000 UPM · advance width {W} · baseline at y=0 · stroke {STROKE} round caps -->\n'
           f'  <g transform="scale(1,-1)">\n'
           f'    <path d="{d}" fill="none" stroke="#000" stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round"/>\n'
           f'  </g>\n</svg>\n')
    open(os.path.join(OUT, 'svg', f'{c}.svg'), 'w').write(svg)

    # ---------- reference page ----------
    fig = plt.figure(figsize=(11.69, 8.27), dpi=150)  # A4 landscape
    ax = fig.add_axes([0.05, 0.08, 0.56, 0.80])
    pad = 120
    ax.set_xlim(-pad, max(W, 520) + pad); ax.set_ylim(-330, 830); ax.set_aspect('equal'); ax.axis('off')
    for x in range(-100, int(max(W, 520) + pad) + 1, 50):
        ax.plot([x, x], [-300, 800], color=GRID, lw=0.4 if x % 250 else 0.9, zorder=0)
    for y in range(-300, 801, 50):
        ax.plot([-pad, max(W, 520) + pad], [y, y], color=GRID, lw=0.4 if y % 250 else 0.9, zorder=0)
    for y, lab in LINES:
        ax.plot([-pad, max(W, 520) + pad], [y, y], color=MUTED if y in (0, 250, 500, 750, -250) else '#A9B0B7',
                lw=1.1 if y == 250 else 0.8, ls='-' if y in (0, 250, 500, 750, -250) else '--', zorder=1)
    for x in (0, W):
        ax.plot([x, x], [-300, 800], color=ACC, lw=0.8, ls=':', zorder=1)
    ax.text(0, 812, '0', color=ACC, fontsize=7, ha='center'); ax.text(W, 812, str(W), color=ACC, fontsize=7, ha='center')
    # stroked shape
    poly = LineString(flat).buffer(STROKE/2, quad_segs=10, cap_style='round', join_style='round')
    for g in getattr(poly, 'geoms', [poly]):
        xs, ys = g.exterior.xy; ax.fill(xs, ys, color='#000000', alpha=0.08, lw=0, zorder=2)
    # skeleton
    verts, codes = [start], [Path.MOVETO]
    for s in segs:
        if s[0] == 'line': verts.append(s[1]); codes.append(Path.LINETO)
        else: verts += [s[1], s[2], s[3]]; codes += [Path.CURVE4]*3
    ax.add_patch(PathPatch(Path(verts, codes), fill=False, ec=ACC, lw=2.2, zorder=3))
    # handles and nodes
    rows = []; k = 0
    for i, n in enumerate(nodes):
        x, y = n.position.x, n.position.y
        if n.type == 'offcurve':
            prev = nodes[i-1] if nodes[i-1].type != 'offcurve' else nodes[i+1]
            ax.plot([prev.position.x, x], [prev.position.y, y], color=INK, lw=0.7, zorder=4)
            ax.plot(x, y, 'o', ms=4.5, mfc='white', mec=INK, mew=0.9, zorder=5)
            rows.append(('', 'handle', x, y))
        else:
            k += 1
            kind = 'smooth curve' if n.smooth else ('curve' if n.type == 'curve' else 'corner')
            ax.plot(x, y, 'o' if n.smooth else 's', ms=7, mfc='white', mec=INK, mew=1.4, zorder=6)
            ax.annotate(f'{k}', (x, y), xytext=(6, 6), textcoords='offset points', fontsize=8, color=INK, weight='bold', zorder=7)
            rows.append((str(k), kind, x, y))
    for y, lab in LINES:
        ax.text(-pad + 4, y + 9, lab, fontsize=6.5, color=MUTED)
    # side panel
    fig.text(0.05, 0.93, c, fontsize=40, weight='bold', color=INK, va='center')
    fig.text(0.11, 0.945, 'Alphabeat · ' + (FAM[c] + ' (oldstyle, tabular)' if c.isdigit() else FAM[c] + ' family'), fontsize=11, color=INK)
    fig.text(0.11, 0.915, f'1000 UPM · width {W} · stroke {STROKE}, round caps · grid 50 units', fontsize=8.5, color=MUTED)
    tx = 0.65; ty = 0.88
    fig.text(tx, ty, 'Recipe', fontsize=9, weight='bold', color=INK); ty -= 0.03
    for kind, x, lv, part in REC[c]:
        fig.text(tx, ty, f'{kind}({x:g}, {lv})', fontsize=8, family='monospace', color=INK)
        fig.text(tx + 0.13, ty, part, fontsize=8, color=MUTED); ty -= 0.024
    ty -= 0.02
    fig.text(tx, ty, 'Nodes in drawing order (open path, left to right)', fontsize=9, weight='bold', color=INK); ty -= 0.03
    fig.text(tx, ty, '#', fontsize=7.5, color=MUTED); fig.text(tx + 0.03, ty, 'type', fontsize=7.5, color=MUTED)
    fig.text(tx + 0.15, ty, 'x', fontsize=7.5, color=MUTED, ha='right'); fig.text(tx + 0.21, ty, 'y', fontsize=7.5, color=MUTED, ha='right'); ty -= 0.022
    for num, kind, x, y in rows:
        col = INK if num else MUTED
        fig.text(tx, ty, num, fontsize=8, color=col, weight='bold' if num else 'normal')
        fig.text(tx + 0.03, ty, kind, fontsize=8, color=col)
        fig.text(tx + 0.15, ty, f'{x:g}', fontsize=8, family='monospace', color=col, ha='right')
        fig.text(tx + 0.21, ty, f'{y:g}', fontsize=8, family='monospace', color=col, ha='right'); ty -= 0.0205
    fig.text(0.05, 0.035, 'Squares = corner nodes · circles = smooth nodes · small circles = handles. Round peaks overshoot their line by 12 units.',
             fontsize=7.5, color=MUTED)
    fig.savefig(os.path.join(OUT, 'png', f'{c}.png'), dpi=150); pdf.savefig(fig); plt.close(fig)
    summary[c] = len([r for r in rows if r[0]])
pdf.close()
print(summary)
