"""Sites in Assembly-CSharp code that branch on a PlayerId-like value: cbz wN followed within 4 instructions by cmp wN, #1 (if id == PlayerOne .. else if id == PlayerTwo)."""
import re, sys, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
img = open(sys.argv[2], 'rb').read()
img_name = None; cls = None; ms = []
for line in open(sys.argv[1]):
    if line.startswith('// '): img_name = line[3:].strip(); continue
    m = re.match(r'class (\S+)', line)
    if m: cls = m.group(1); continue
    m = re.search(r'(\S+)\((.*)\);  // main\+(0x[0-9a-f]+)', line)
    if m: ms.append((int(m.group(3), 16), cls, m.group(1), img_name))
ms.sort()
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
sites = []; calls = Counter(); callers = defaultdict(set)
TARGETS = {0x421820: 'GetPlayerLoadout', 0x229d30: 'GetPlayerStats', 0x2c9420: 'get_id', 0x40ef80: 'GetPlayer', 0x411ad0: 'GetNext'}
for i, (a, c, n, im) in enumerate(ms):
    if im != 'Assembly-CSharp.dll': continue
    end = ms[i + 1][0] if i + 1 < len(ms) else a + 0x1000
    if end - a > 0x20000 or end <= a: continue
    ins = list(md.disasm_lite(img[a:end], a))
    for k, (addr, size, mn, op) in enumerate(ins):
        if mn == 'bl':
            t = int(op.lstrip('#'), 16)
            if t in TARGETS: calls[TARGETS[t]] += 1; callers[TARGETS[t]].add(c)
        if mn == 'cbz' and op.startswith('w'):
            r = op.split(',')[0]
            for k2 in range(k + 1, min(k + 5, len(ins))):
                if ins[k2][2] == 'cmp' and ins[k2][3].replace(' ', '') == r + ',#1':
                    sites.append((addr, c, n)); break
print('id-switch sites (cbz wN .. cmp wN,#1):', len(sites), 'in', len({(c, n) for _, c, n in sites}), 'methods,', len({c for _, c, _ in sites}), 'classes')
for k, v in calls.items(): print('calls to %s: %d from %d classes' % (k, v, len(callers[k])))
by = Counter(c for _, c, _ in sites)
print('top classes:', by.most_common(25))
with open(sys.argv[3], 'w') as f:
    for a, c, n in sites: f.write('%#x\t%s::%s\n' % (a, c, n))
