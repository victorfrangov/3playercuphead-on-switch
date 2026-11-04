"""In player-component methods, list cmp wN,#1 / cbz wN branches near a get_id call, an inlined get_id (ldr wN, [x, #0x80]) or GetPlayerLoadout."""
import re, sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
img = open(sys.argv[2], 'rb').read()
cls = None; ms = []
for line in open(sys.argv[1]):
    m = re.match(r'class (\S+)', line)
    if m: cls = m.group(1); continue
    m = re.search(r'(\S+)\((.*)\);  // main\+(0x[0-9a-f]+)', line)
    if m: ms.append((int(m.group(3), 16), cls, m.group(1)))
ms.sort()
pat = re.compile(sys.argv[3])
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
for i, (a, c, n) in enumerate(ms):
    if not pat.search(c + '::' + n): continue
    end = ms[i + 1][0]
    ins = list(md.disasm_lite(img[a:end], a))
    hits = []
    for k, (ad, sz, mn, op) in enumerate(ins):
        src = None
        if mn == 'bl' and op in ('#0x2c9420',): src = 'get_id'
        if mn == 'bl' and op == '#0x421820': src = 'GetPlayerLoadout'
        if mn == 'ldr' and op.startswith('w') and op.endswith('#0x80]'): src = 'ldr id?'
        if src:
            for k2 in range(k + 1, min(k + 8, len(ins))):
                if ins[k2][2] in ('cmp', 'cbz', 'cbnz', 'tbz', 'tbnz') and ins[k2][3].startswith('w') and (',#1' in ins[k2][3].replace(' ','') or ins[k2][2] in ('cbz','cbnz')):
                    hits.append('%#x %s -> %#x %s %s' % (ad, src, ins[k2][0], ins[k2][2], ins[k2][3])); break
    if hits:
        print('%s::%s @%#x' % (c, n, a))
        for h in hits: print('   ', h)
