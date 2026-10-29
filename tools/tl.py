#!/usr/bin/env python3
"""Extrai / valida / remonta os scripts do Play Novel: Silent Hill para PT-BR.
  tl.py extract            -> work/units_<arq>.json
  tl.py show <arq> a b     -> imprime as unidades a..b-1 ("n| texto")
  tl.py merge              -> valida tr/<arq>.tsv e grava scripts/PT-BR/<arq>
  tl.py status
"""
import re, json, sys, os, glob
EN = '/home/claude/shpn_tool-0.1/scripts/EN'
OUT = '/home/claude/ptbr/shpn_tool/scripts/PT-BR'
FILES = ['strtab_menu', 'strtab_script', 'Cybil', 'Harry']
SHOW = re.compile(r'^(ShowText\(\(\d+\)")(.*)("\);.*)$')
CHOICE = re.compile(r'^(Choice\()(.*)(\);.*)$')
ITEM = re.compile(r'\((\d+)\)"')

def split_choice(body):
    """'(0)"a", (1)"b"' -> [(prefix_id, texto), ...] preservando a ordem"""
    items = []
    pos = [(m.start(), m.end(), m.group(1)) for m in ITEM.finditer(body)]
    # só vale "(n)\"" que está no início ou logo após '", '
    good = [p for p in pos if p[0] == 0 or body[:p[0]].endswith('", ')]
    for i, (s, e, idn) in enumerate(good):
        end = good[i+1][0] - 3 if i + 1 < len(good) else len(body) - 1  # remove '", ' ou '"'
        items.append((idn, body[e:end]))
    return items

def parse(fname):
    units = []; lines = open(f'{EN}/{fname}', encoding='utf-8').read().split('\n')
    layout = []   # por linha: ('raw', txt) | ('show', pre, unit, post) | ('choice', pre, [ids], post) | ('tab', num)
    for ln, l in enumerate(lines):
        if fname.startswith('strtab'):
            m = re.match(r'^(\d+): (.*)$', l)
            if m:
                units.append(m.group(2)); layout.append(('tab', m.group(1), len(units)-1)); continue
        else:
            m = SHOW.match(l)
            if m:
                units.append(m.group(2)); layout.append(('show', m.group(1), len(units)-1, m.group(3))); continue
            m = CHOICE.match(l)
            if m:
                items = split_choice(m.group(2)); idx = []
                for idn, t in items:
                    units.append(t); idx.append((idn, len(units)-1))
                layout.append(('choice', m.group(1), idx, m.group(3))); continue
        layout.append(('raw', l))
    return units, layout

def load_tr(fname):
    tr = {}
    for p in sorted(glob.glob(f'/home/claude/ptbr/work/tr/{fname}.*.tsv')):
        for l in open(p, encoding='utf-8').read().split('\n'):
            if not l.strip(): continue
            n, t = l.split('\t', 1); tr[int(n)] = t
    return tr

ALLOWED = set(' !"\'(),-.0123456789:;?ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz¥\\'
              'áàâãçéêíóôõúüÁÀÂÃÇÉÊÍÓÔÕÚ&')

def check(n, en, pt):
    errs = []
    for tok in ('¥"', '\\"', '\\n'):
        if tok == '¥"' and '5001:' in en: continue   # trecho com lixo do patch EN
        if en.count(tok) != pt.count(tok): errs.append(f'{tok!r}: EN {en.count(tok)} PT {pt.count(tok)}')
    bad = sorted(set(c for c in pt if c not in ALLOWED and c not in en))
    if bad: errs.append('caracteres não suportados: ' + ''.join(bad))
    if re.search(r'W\d', pt): errs.append('sequência W<dígito> (comando de espera)')
    if '\t' in pt or '\n' in pt: errs.append('tab/newline')
    if not pt.strip() and en.strip(): errs.append('vazio')
    return errs

def cmd_extract():
    for f in FILES:
        units, _ = parse(f)
        json.dump(units, open(f'/home/claude/ptbr/work/units_{f}.json', 'w', encoding='utf-8'), ensure_ascii=False)
        print(f, len(units), sum(map(len, units)))

def cmd_show(f, a, b):
    units, _ = parse(f)
    for i in range(a, min(b, len(units))): print(f'{i}| {units[i]}')

def cmd_status(strict=False):
    for f in FILES:
        units, _ = parse(f); tr = load_tr(f)
        errs = {n: check(n, units[n], t) for n, t in tr.items() if n < len(units)}
        errs = {n: e for n, e in errs.items() if e}
        print(f'{f}: {len(tr)}/{len(units)} traduzidas, {len(errs)} com problema')
        for n, e in list(errs.items())[:15]: print('   ', n, e)

def cmd_merge():
    os.makedirs(OUT, exist_ok=True)
    for f in FILES:
        units, layout = parse(f); tr = load_tr(f)
        rep = lambda i: tr.get(i, units[i])    # o que falta fica em inglês
        out = []
        for e in layout:
            if e[0] == 'raw': out.append(e[1])
            elif e[0] == 'tab': out.append(f'{e[1]}: {rep(e[2])}')
            elif e[0] == 'show': out.append(f'{e[1]}{rep(e[2])}{e[3]}')
            else: out.append(e[1] + ', '.join(f'({idn})"{rep(i)}"' for idn, i in e[2]) + e[3])
        open(f'{OUT}/{f}', 'w', encoding='utf-8').write('\n'.join(out))
        # round-trip: com as traduções = originais, o arquivo deve ser idêntico ao EN
    print('ok')

def cmd_roundtrip():
    for f in FILES:
        units, layout = parse(f); out = []
        for e in layout:
            if e[0] == 'raw': out.append(e[1])
            elif e[0] == 'tab': out.append(f'{e[1]}: {units[e[2]]}')
            elif e[0] == 'show': out.append(f'{e[1]}{units[e[2]]}{e[3]}')
            else: out.append(e[1] + ', '.join(f'({idn})"{units[i]}"' for idn, i in e[2]) + e[3])
        print(f, '\n'.join(out) == open(f'{EN}/{f}', encoding='utf-8').read())

def cmd_auto():
    for f in FILES:
        units, _ = parse(f)
        p = f'/home/claude/ptbr/work/tr/{f}.zauto.tsv'
        if os.path.exists(p): os.remove(p)
        tr = load_tr(f); by_en = {}
        for n, t in tr.items():
            if n < len(units): by_en.setdefault(units[n], t)
        lines = [f'{n}\t{by_en[u]}' for n, u in enumerate(units) if n not in tr and u in by_en and u.strip()]
        open(p, 'w', encoding='utf-8').write('\n'.join(lines) + ('\n' if lines else ''))
        print(f, 'reaproveitadas:', len(lines))

def cmd_todo(f, start, count):
    units, _ = parse(f); tr = load_tr(f); shown = 0
    for i in range(start, len(units)):
        if i in tr or not units[i].strip(): continue
        print(f'{i}| {units[i]}'); shown += 1
        if shown >= count: break

if __name__ == '__main__':
    a = sys.argv[1:]
    {'auto': cmd_auto, 'extract': cmd_extract, 'status': cmd_status, 'merge': cmd_merge, 'roundtrip': cmd_roundtrip}.get(a[0], lambda: None)() if a[0] not in ('show','todo') else (cmd_show(a[1], int(a[2]), int(a[3])) if a[0]=='show' else cmd_todo(a[1], int(a[2]), int(a[3])))
