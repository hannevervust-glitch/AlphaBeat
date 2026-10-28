import json, os
L = {k: v for k, v in json.load(open(os.path.join(os.path.dirname(__file__), 'letters.json'))).items() if not k.startswith('_')}
LV = dict(T=750, I=625, X=500, M=250, q=125, B=0, D=-250)
ASC, DESC = set('bdfhklt68'), set('gjpqy34579')
NARROW, WIDE = set('ijlftr'), set('mw')
# which drawing element each anatomy part may use: (kinds, levels)
PART = {
 'ascender stem': ({'line'}, {'T', 'M'}), 'descender stem': ({'line'}, {'D', 'M'}), 'stem': ({'line'}, {'X', 'M'}),
 'short ascender': ({'line'}, {'I', 'M'}), 'hooked ascender': ({'arc'}, {'T'}), 'hooked descender': ({'arc'}, {'D'}),
 'hooked stem': ({'arc'}, {'X'}), 'hooked foot': ({'arc'}, {'q'}),
 'bowl': ({'arc'}, {'X', 'B'}), 'lower bowl': ({'arc'}, {'B'}), 'eye': ({'arc'}, {'X'}), 'aperture': ({'arc'}, {'q'}),
 'arch': ({'arc'}, {'X'}), 'cup': ({'arc'}, {'B'}), 'spine': ({'sq'}, {'X', 'B'}),
 'crossbar': ({'line'}, {'M'}), 'space': ({'line'}, {'M'}), 'tittle': ({'line'}, {'I', 'M'}),
 'arm': ({'line'}, {'X', 'M'}), 'leg': ({'line'}, {'B', 'M'}), 'diagonal': ({'line'}, {'X', 'B', 'M'}),
 'descender diagonal': ({'line'}, {'D', 'M'}),
 'flag': ({'line'}, {'X'}), 'bar': ({'line'}, {'M'}), 'upper bowl': ({'arc'}, {'X', 'T'}),
}
errors = []
def err(c, m): errors.append(f'{c}: {m}')
def parts(c):
    out = []
    for e in L[c]:
        if not out or out[-1] != e[3]: out.append(e[3])
    return out
for c, rec in L.items():
    xs = [e[1] for e in rec]
    if xs != sorted(xs) or len(set(xs)) != len(xs): err(c, 'x positions must increase')
    if xs[-1] != 1 or (rec[-1][0] == 'line' and rec[-1][2] != 'M'): err(c, 'must end on the centre line at x=1')
    for kind, x, lv, part in rec:
        if part not in PART: err(c, f'unknown part {part}'); continue
        kinds, lvs = PART[part]
        if kind not in kinds: err(c, f'{part} must be drawn as {kinds}, got {kind}')
        if lv not in lvs: err(c, f'{part} must reach {lvs}, got {lv}')
    lvls = {e[2] for e in rec}
    if c in ASC and not lvls & {'T', 'I'}: err(c, 'ascender letter never reaches the ascender zone')
    if c in DESC and 'D' not in lvls: err(c, 'descender letter never reaches D')
    if c not in ASC and lvls & {'T'}: err(c, 'body letter reaches the ascender line')
    if c not in DESC and 'D' in lvls: err(c, 'non-descender letter reaches D')
    if 'I' in lvls and not (c in 'ij' or c == 't'): err(c, 'only i, j (tittle) and t (short ascender) may use the I line')
# family & symmetry checks (same parts, mirrored order or flipped stem)
def swap(ps, a, b): return [b if p == a else a if p == b else p for p in ps]
checks = [
 ('d mirrors b', parts('d') == parts('b')[::-1]),
 ('p is b with stem below', parts('p') == swap(parts('b'), 'ascender stem', 'descender stem')),
 ('q mirrors p', parts('q') == parts('p')[::-1]),
 ('q is d with stem below', parts('q') == swap(parts('d'), 'ascender stem', 'descender stem')),
 ('u is n rotated', parts('u') == ['cup'] and parts('n') == ['arch']),
 ('m is two n arches', [e[3] for e in L['m']] == ['arch', 'arch']),
 ('h is ascender stem + n', parts('h') == ['ascender stem'] + parts('n')),
 ('r is a cut-off n arch', parts('r') == ['arch', 'space']),
 ('o, c, e share the bowl top', L['o'][0][1:3] == [0.5, 'X'] and L['c'][0][2] == 'X' and L['e'][0][2] == 'X'),
 ('c and e share the aperture', L['c'][-1][3] == L['e'][-1][3] == 'aperture'),
 ('i and j share the tittle', [e for e in L['i'] if e[3] == 'tittle'] == [e for e in L['j'] if e[3] == 'tittle']),
 ('w is two v', [e[2] for e in L['w']] == ['B', 'X', 'B', 'M']),
 ('0 is o (narrower, tabular)', L['0'] == L['o']),
 ('9 is 6 turned around', [(e[0], {'T':'D','X':'B','B':'X'}[e[2]]) for e in L['6']][::-1] == [(e[0], e[2]) for e in L['9']]),
 ('3 and 5 share the hooked tail', L['3'][-1][2:] == L['5'][-1][2:]),
 ('8 stacks a bowl on the 0 bowl', [e[2] for e in L['8'][1:]] == ['X', 'B']),
 ('bowl reads top first', all(L[c][[e[3] for e in L[c]].index('bowl')][2] == 'X' for c in L if 'bowl' in parts(c))),
]
for name, ok in checks:
    if not ok: errors.append('family: ' + name)
print('letters:', len(L))
print('rule checks:', sum(1 for _ in L) * 5, '| family checks:', len(checks))
print('\n'.join(errors) if errors else 'ALL LETTERS FOLLOW THE SAME RULES')
