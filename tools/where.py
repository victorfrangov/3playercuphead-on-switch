import re, sys, bisect
cls = None; ms = []
for line in open(sys.argv[1]):
    m = re.match(r'class (\S+)', line)
    if m: cls = m.group(1); continue
    m = re.search(r'(\S+)\((.*)\);  // main\+(0x[0-9a-f]+)', line)
    if m: ms.append((int(m.group(3), 16), cls + '::' + m.group(1)))
ms.sort(); keys = [a for a, _ in ms]
for a in sys.argv[2:]:
    x = int(a, 16); i = bisect.bisect_right(keys, x) - 1
    print('%s  %s+%#x' % (a, ms[i][1], x - ms[i][0]))
