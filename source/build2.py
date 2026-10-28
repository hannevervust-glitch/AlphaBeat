import json, os
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.geometry.polygon import orient
import ufoLib2, glyphsLib
from ufo2ft import compileOTF

HERE = os.path.dirname(__file__)
L = json.load(open(os.path.join(HERE, 'letters.json')))
LV = dict(T=750, I=625, X=500, Q=375, M=250, q=125, B=0, D=-250)
OVER = 12  # overshoot: round shapes cross their line slightly so they look the same size
WID = {**{c: 1.4 for c in 'mw'}, **{c: .6 for c in 'ijlftr'}, **{c: 470/520 for c in '0123456789'}}  # digits: one tabular width
DIG = dict(zip('0123456789', ['zero','one','two','three','four','five','six','seven','eight','nine']))
gn = lambda c: DIG.get(c, c)
unis = lambda c: sorted({ord(c), ord(c.upper())})
BASEW, STROKE = 520, 64
K = {'arc': 0.5523, 'sq': 0.85}

def segments(c):
    """Return list of segments in font units: ('line', p1) or ('curve', c1, c2, p) starting at (0,M)."""
    w = round(BASEW * WID.get(c, 1)); x0, y0 = 0, LV['M']; segs = []
    for kind, fx, lv, *_ in L[c]:
        x1 = round(fx * w); peak = LV[lv]
        if kind == 'line':
            segs.append(('line', (x1, peak)))
        else:
            k = K[kind]; xm = round((x0 + x1) / 2); M = LV['M']
            if lv in 'TXBD': peak += OVER if peak > M else -OVER
            segs.append(('curve', (x0, round(M + k * (peak - M))), (round(xm - k * (xm - x0)), peak), (xm, peak)))
            segs.append(('curve', (round(xm + k * (x1 - xm)), peak), (x1, round(M + k * (peak - M))), (x1, M)))
        x0, y0 = segs[-1][-1]
    return w, segs

def bez(p0, c1, c2, p3, n=24):
    out = []
    for i in range(1, n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0[0]+3*u*u*t*c1[0]+3*u*t*t*c2[0]+t**3*p3[0],
                    u**3*p0[1]+3*u*u*t*c1[1]+3*u*t*t*c2[1]+t**3*p3[1]))
    return out

def flatten(segs):
    pts = [(0, LV['M'])]
    for s in segs:
        if s[0] == 'line': pts.append(s[1])
        else: pts += bez(pts[-1], s[1], s[2], s[3])
    return pts

def setup_info(ufo):
    i = ufo.info
    i.familyName = "Alphabeat"; i.styleName = "Regular"; i.unitsPerEm = 1000
    i.ascender = 750; i.descender = -250; i.xHeight = 500; i.capHeight = 750
    i.versionMajor = 2; i.versionMinor = 0
    i.copyright = "The Alphabeat wave alphabet by Hanne Vervust and Lorenzo Bondani"
    i.openTypeNameDesigner = "Hanne Vervust, Lorenzo Bondani"; i.postscriptFontName = "Alphabeat-Regular"
    i.openTypeOS2TypoLineGap = 200

def draw_polys(g, polys):
    pen = g.getPen()
    for poly in polys:
        poly = orient(poly, 1.0)
        for ring in [poly.exterior] + list(poly.interiors):
            pts = list(ring.coords)[:-1]
            pen.moveTo(tuple(round(v) for v in pts[0]))
            for p in pts[1:]: pen.lineTo(tuple(round(v) for v in p))
            pen.closePath()

def stroke(geom_line):
    s = geom_line.buffer(STROKE / 2, quad_segs=8, cap_style='round', join_style='round').simplify(1.0)
    return list(s.geoms) if isinstance(s, MultiPolygon) else [s]

out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
letters = [c for c in L if not c.startswith('_')]

# 1. Editable source: open skeleton paths with a stroke, for Glyphs
src = ufoLib2.Font(); setup_info(src)
for c in letters:
    w, segs = segments(c)
    g = src.newGlyph(gn(c)); g.width = w; g.unicodes = unis(c)
    pen = g.getPen(); pen.moveTo((0, LV['M']))
    for s in segs:
        if s[0] == 'line': pen.lineTo(s[1])
        else: pen.curveTo(s[1], s[2], s[3])
    pen.endPath()
for name, u, w in [('space', 0x20, 260), ('period', 0x2E, 200), ('hyphen', 0x2D, 300)]:
    g = src.newGlyph(name); g.width = w; g.unicodes = [u]
src['hyphen'].getPen().moveTo((0, 250)); p = src['hyphen'].getPen()
src['hyphen'].clearContours(); p = src['hyphen'].getPen(); p.moveTo((0, 250)); p.lineTo((300, 250)); p.endPath()
p = src['period'].getPen(); p.moveTo((100, 250)); p.lineTo((101, 250)); p.endPath()
p = src['space'].getPen(); p.moveTo((0, 250)); p.lineTo((260, 250)); p.endPath()  # space = flat stripe on the centre line
src.glyphOrder = ['space'] + [gn(c) for c in letters] + ['period', 'hyphen']
gs = glyphsLib.to_glyphs([src], minimize_ufo_diffs=False)
gs.format_version = 3
for glyph in gs.glyphs:
    for layer in glyph.layers:
        for path in layer.paths:
            path.closed = False
            for i, n in enumerate(path.nodes):
                # smooth nodes at curve extremes (handles on both sides)
                if n.type == 'curve' and 0 < i < len(path.nodes) - 1 and path.nodes[i-1].type == 'offcurve' and path.nodes[i+1].type == 'offcurve':
                    n.smooth = True
            path.attributes['strokeWidth'] = STROKE
            path.attributes['strokeHeight'] = STROKE
            path.attributes['lineCapStart'] = 1
            path.attributes['lineCapEnd'] = 1
gs.save(os.path.join(out, 'Alphabeat.glyphs'))

# 2. Installable font: same skeletons, stroked into outlines
fnt = ufoLib2.Font(); setup_info(fnt)
for c in letters:
    w, segs = segments(c)
    g = fnt.newGlyph(gn(c)); g.width = w; g.unicodes = unis(c)
    draw_polys(g, stroke(LineString(flatten(segs))))
for name, u, w, polys in [('space', 0x20, 260, stroke(LineString([(0, 250), (260, 250)]))),
                          ('period', 0x2E, 200, [Point(100, 250).buffer(46, quad_segs=8)]),
                          ('hyphen', 0x2D, 300, stroke(LineString([(0, 250), (300, 250)])))]:
    g = fnt.newGlyph(name); g.width = w; g.unicodes = [u]; draw_polys(g, polys)
g = fnt.newGlyph('.notdef'); g.width = 500; draw_polys(g, [Polygon([(50, 0), (450, 0), (450, 700), (50, 700)])])
fnt.glyphOrder = ['.notdef', 'space'] + [gn(c) for c in letters] + ['period', 'hyphen']
compileOTF(fnt, removeOverlaps=True).save(os.path.join(out, 'Alphabeat.otf'))

# 3. Node table for the construction sheet / web page
table = {}
for c in letters:
    w, segs = segments(c)
    table[c] = {'width': w, 'points': [[round(x), round(y)] for x, y in flatten(segs)],
                'nodes': [list(s[-1]) for s in segs]}
json.dump(table, open(os.path.join(out, 'nodes.json'), 'w'))
print('built', len(letters))
