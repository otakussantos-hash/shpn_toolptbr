#!/usr/bin/env python3
"""Gera glifos 11x11 de letras acentuadas do português e os grava na fonte da ROM de
Silent Hill Play Novel (GBA). Fonte: 11x11 px, 1 bpp, empacotada, 16 bytes/glifo, a partir de
0x215858 (offset no arquivo). Os glifos substituem codepoints gregos (Shift-JIS) que o jogo não usa.

Uso:
  python3 accents_font.py ROM_ENTRADA ROM_SAIDA        # grava na ROM
  python3 accents_font.py --ips accents.ips [ROM_LEITURA]  # só gera um patch IPS
  python3 accents_font.py --preview preview.png [ROM_LEITURA]
"""
import sys, struct
FONT_BASE = 0x215858
GLYPH_BYTES = 16
W = H = 11
CAP_ROWS = 8      # altura das maiúsculas acentuadas (letra em linhas 2..9, acento em 0..1)

# (caractere acentuado, letra base, acento)
ACCENTED = [
 ('á','a','acute'),('à','a','grave'),('â','a','circ'),('ã','a','tilde'),('ç','c','cedilla'),
 ('é','e','acute'),('ê','e','circ'),('í','i','acute'),('ó','o','acute'),('ô','o','circ'),
 ('õ','o','tilde'),('ú','u','acute'),('ü','u','diaer'),
 ('Á','A','acute'),('À','A','grave'),('Â','A','circ'),('Ã','A','tilde'),('Ç','C','cedilla'),
 ('É','E','acute'),('Ê','E','circ'),('Í','I','acute'),('Ó','O','acute'),('Ô','O','circ'),
 ('Õ','O','tilde'),('Ú','U','acute'),
]
GREEK_LO = [chr(0x3b1+i) for i in range(25) if chr(0x3b1+i) != 'ς']  # α..ω (sem ς final)
GREEK_UP = [chr(0x391+i) for i in range(25) if chr(0x391+i) != '\u03a2']  # Α..Ω (sem U+03A2)

def slot_table():
    """acentuado -> (placeholder grego, codigo SJIS)"""
    lo = [c for c in ACCENTED if c[0].islower()]
    up = [c for c in ACCENTED if c[0].isupper()]
    out = {}
    for (ch,_,_), g in zip(lo, GREEK_LO): out[ch] = (g, int.from_bytes(g.encode('cp932'), 'big'))
    for (ch,_,_), g in zip(up, GREEK_UP): out[ch] = (g, int.from_bytes(g.encode('cp932'), 'big'))
    return out

def idx_of(code):
    f, s = code >> 8, code & 255
    o2 = s - 0x40
    if o2 > 0x3f: o2 = s - 0x41
    buf = {1:0xad, 2:0x15e, 3:0x1f4, 6:0x272}
    if ((f-0x88) & 0xffffffff) > 0x17:
        o1 = buf.get(f-0x81, 0) if ((f-0x81) & 0xffffffff) <= 0x5e else 0x140c + 0xbc*(f-0xe0) + 4
    else: o1 = 0xbc*(f-0x88) + 0x270
    return o1 + o2

def read_glyph(rom, code):
    a = FONT_BASE + idx_of(code)*GLYPH_BYTES
    b = ''.join(f'{x:08b}' for x in rom[a:a+GLYPH_BYTES])
    return [[int(b[r*W+c]) for c in range(W)] for r in range(H)]

def pack(g):
    bits = ''.join(str(g[r][c]) for r in range(H) for c in range(W)).ljust(128, '0')
    return bytes(int(bits[i:i+8], 2) for i in range(0, 128, 8))

def base_code(ch):
    return ord(ch) - ord('A') + 0x8260 if ch.isupper() else ord(ch) - ord('a') + 0x8281

def bbox_center(g):
    cols = [c for r in range(H) for c in range(W) if g[r][c]]
    return (min(cols) + max(cols)) // 2

def compress_rows(g, keep):
    """reduz as linhas 0..9 de g para 'keep' linhas removendo as menos informativas"""
    rows = [g[r][:] for r in range(10)]
    while len(rows) > keep:
        best, bi = 1e9, None
        for i in range(1, len(rows)-1):
            cost = sum(a != b for a, b in zip(rows[i], rows[i-1]))
            cost += sum(a != b for a, b in zip(rows[i], rows[i+1])) * 0.5
            cost += 3 if sum(rows[i]) >= 6 else 0           # preserva barras horizontais
            if abs(i - len(rows)*0.6) > len(rows)*0.35: cost += 2
            if cost < best: best, bi = cost, i
        del rows[bi]
    return rows

ACC = {  # (linha, deslocamento da coluna central)
 'acute':  [(0, 1), (1, 0)],
 'grave':  [(0, -1), (1, 0)],
 'circ':   [(0, 0), (1, -1), (1, 1)],
 'tilde':  [(0, -1), (0, 0), (0, 2), (1, -2), (1, 0), (1, 1)],
 'diaer':  [(1, -2), (1, 1)],
}

def build(rom, ch, base, acc):
    g = read_glyph(rom, base_code(base))
    out = [[0]*W for _ in range(H)]
    if base == 'i':                                  # i sem o pingo
        for r in range(3, 11): out[r] = g[r][:]
    elif base.isupper() and acc != 'cedilla':
        rows = compress_rows(g, CAP_ROWS)
        for i, row in enumerate(rows): out[2+i] = row
    else:
        out = [row[:] for row in g]
    c = bbox_center(g)
    if acc == 'cedilla':
        out[10][c] = 1; out[10][c-1] = 1
    else:
        for r, dc in ACC[acc]:
            if 0 <= c+dc < W: out[r][c+dc] = 1
    return out

def build_all(rom):
    res = {}
    for ch, (_, code) in slot_table().items():
        _, base, acc = next(t for t in ACCENTED if t[0] == ch)
        res[code] = build(rom, ch, base, acc)
    return res

def write_rom(rom, glyphs):
    rom = bytearray(rom)
    for code, g in glyphs.items():
        a = FONT_BASE + idx_of(code)*GLYPH_BYTES
        rom[a:a+GLYPH_BYTES] = pack(g)
    return bytes(rom)

def make_ips(glyphs):
    out = bytearray(b'PATCH')
    for code in sorted(glyphs):
        a = FONT_BASE + idx_of(code)*GLYPH_BYTES
        out += a.to_bytes(3, 'big') + (GLYPH_BYTES).to_bytes(2, 'big') + pack(glyphs[code])
    return bytes(out + b'EOF')

def preview(glyphs, path):
    from PIL import Image
    items = sorted(glyphs.items()); cols = 13; sc = 6
    rows = (len(items)+cols-1)//cols
    im = Image.new('RGB', (cols*(W+2)*sc, rows*(H+2)*sc), (30, 30, 30))
    for n, (code, g) in enumerate(items):
        ox, oy = (n % cols)*(W+2)*sc, (n//cols)*(H+2)*sc
        for r in range(H):
            for c in range(W):
                if g[r][c]:
                    for dy in range(sc):
                        for dx in range(sc): im.putpixel((ox+(c+1)*sc+dx, oy+(r+1)*sc+dy), (235, 235, 225))
    im.save(path)

if __name__ == '__main__':
    import glob
    a = sys.argv[1:]
    def rom_default(): return open(glob.glob('/home/claude/rom/*.gba')[0], 'rb').read()
    if a and a[0] == '--ips':
        rom = open(a[2], 'rb').read() if len(a) > 2 else rom_default()
        open(a[1], 'wb').write(make_ips(build_all(rom)))
    elif a and a[0] == '--preview':
        rom = open(a[2], 'rb').read() if len(a) > 2 else rom_default()
        preview(build_all(rom), a[1])
    elif len(a) == 2:
        rom = open(a[0], 'rb').read()
        open(a[1], 'wb').write(write_rom(rom, build_all(rom)))
    else:
        print(__doc__)
