"""Links the 3-player mod (a clang arm64 Mach-O object) into Cuphead's main module (NX2Apple main.patched.bin) and writes its hooks.

Usage: link_mod.py MOD_O IN_MAIN_PATCHED_BIN OUT

Layout, in main offsets (the module file is the flat image; offsets are main offsets):
- code and read-only data (__TEXT sections) are appended after the input module, 16-aligned: on the Mac the loader maps the whole
  file tail from PATCH_OFF (0x3b40000) read+execute, so the earlier patches there (such as another mod's) stay where they are
- writable data (__DATA sections, bss included) go to main+0x3b37000..0x3b38000: zero, mapped read+write and unused (main's bss ends
  at 0x3b36c88, the host's key page starts at 0x3b38000)
Symbols:
- an undefined _G_<hex> is main+<hex> (a game function or data address)
- an undefined _o_<name> is the trampoline of hook <name>: the game instruction the hook replaced, then a branch back
Hooks: the object's __HOOKS,__hooks section is a list of struct hook {u64 site; u32 expect; u32 kind; u64 target} (mod.h), read here and
not loaded. kind 0: the site is a function entry; its instruction moves to trampoline _o_<name>, the site branches to _h_<name>.
kind 1: the site's word becomes target (a plain instruction patch). kind 2: the site branches to the target (a stub that branches
back itself). kind 3: the site is a bl, which now calls the target instead. Every site must hold the expected word, so a different module (another game version, a hook written twice) is refused.
"""
import struct
import sys

RW_BASE, RW_END = 0x3B37000, 0x3B38000
PATCH_OFF = 0x3B40000

R_UNSIGNED, R_SUBTRACTOR, R_BRANCH26, R_PAGE21, R_PAGEOFF12, R_GOT_PAGE21, R_GOT_PAGEOFF12, R_ADDEND = 0, 1, 2, 3, 4, 5, 6, 10


class Obj:
    def __init__(self, path):
        b = self.b = open(path, 'rb').read()
        magic, cpu, sub, ftype, ncmds, _, _, _ = struct.unpack_from('<8I', b, 0)
        assert magic == 0xFEEDFACF and cpu == 0x0100000C and ftype == 1, 'not an arm64 Mach-O object'
        self.sects, self.syms = [], []
        off = 32
        for _ in range(ncmds):
            cmd, size = struct.unpack_from('<2I', b, off)
            if cmd == 0x19:   # LC_SEGMENT_64
                nsects = struct.unpack_from('<I', b, off + 64)[0]
                for i in range(nsects):
                    s = off + 72 + 80 * i
                    sect = b[s:s + 16].rstrip(b'\0').decode(); seg = b[s + 16:s + 32].rstrip(b'\0').decode()
                    addr, sz, foff, align, reloff, nreloc, flags = struct.unpack_from('<QQ5I', b, s + 32)
                    zero = (flags & 0xFF) in (1, 0xC)   # S_ZEROFILL, S_GB_ZEROFILL
                    data = bytearray(sz) if zero else bytearray(b[foff:foff + sz])
                    relocs = []
                    for r in range(nreloc):
                        a, info = struct.unpack_from('<iI', b, reloff + 8 * r)
                        relocs.append((a, info & 0xFFFFFF, info >> 24 & 1, info >> 25 & 3, info >> 27 & 1, info >> 28 & 0xF))
                    self.sects.append(dict(name=sect, seg=seg, addr=addr, size=sz, align=1 << align, data=data, relocs=relocs, zero=zero))
            elif cmd == 0x2:  # LC_SYMTAB
                symoff, nsyms, stroff, strsize = struct.unpack_from('<4I', b, off + 8)
                for i in range(nsyms):
                    strx, typ, sect, desc, val = struct.unpack_from('<IBBHQ', b, symoff + 16 * i)
                    name = b[stroff + strx:b.index(b'\0', stroff + strx)].decode()
                    self.syms.append(dict(name=name, type=typ, sect=sect, value=val))
            off += size


def w32(img, off):
    return struct.unpack_from('<I', img, off)[0]


def enc_b(pc, to, link=False):
    d = to - pc
    assert -(1 << 27) <= d < (1 << 27) and d % 4 == 0, 'branch out of range %#x -> %#x' % (pc, to)
    return (0x94000000 if link else 0x14000000) | ((d >> 2) & 0x3FFFFFF)


def fix_adrp(word, pc, target):
    d = (target >> 12) - (pc >> 12)
    assert -(1 << 20) <= d < (1 << 20), 'adrp out of range'
    return (word & 0x9F00001F) | (d & 3) << 29 | ((d >> 2) & 0x7FFFF) << 5


def fix_pageoff(word, target):
    lo = target & 0xFFF
    if (word & 0x1F800000) == 0x11000000:       # add/sub (immediate): unscaled
        return (word & ~(0xFFF << 10)) | lo << 10
    if (word & 0x3B000000) == 0x39000000:       # load/store (unsigned immediate): scaled by the access size
        size = word >> 30
        if (word & 0x04800000) == 0x04800000:   # SIMD&FP, opc<1> set: 128-bit
            size = 4
        assert lo % (1 << size) == 0, 'misaligned pageoff %#x for size %d' % (lo, 1 << size)
        return (word & ~(0xFFF << 10)) | (lo >> size) << 10
    raise ValueError('PAGEOFF12 on %08x' % word)


def relocate_moved(word, old_pc, new_pc):
    """a game instruction moved into a trampoline"""
    if (word & 0x9F000000) == 0x90000000:       # adrp
        immlo, immhi = word >> 29 & 3, word >> 5 & 0x7FFFF
        d = (immhi << 2 | immlo); d -= (d & 1 << 20) << 1
        return fix_adrp(word, new_pc, ((old_pc >> 12) + d) << 12)
    if (word & 0x7C000000) == 0x14000000:       # b / bl
        d = word & 0x3FFFFFF; d -= (d & 1 << 25) << 1
        return enc_b(new_pc, old_pc + 4 * d, link=bool(word >> 31))
    pcrel = [(0x9F000000, 0x10000000), (0x3B000000, 0x18000000), (0x7E000000, 0x34000000), (0xFF000010, 0x54000000), (0x7E000000, 0x36000000)]
    assert not any((word & m) == v for m, v in pcrel), 'trampoline: pc-relative instruction %08x at main+%#x' % (word, old_pc)
    return word


def link(obj_path, src, out):
    o = Obj(obj_path)
    img = bytearray(open(src, 'rb').read())
    assert len(img) > PATCH_OFF, 'module too small'
    rw_used = img[RW_BASE:RW_END]
    assert not any(rw_used), 'main+%#x..%#x is not zero: the mod is already linked into this module' % (RW_BASE, RW_END)
    # lay out
    rx = (len(img) + 15) & ~15
    code_base = rx
    rw = RW_BASE
    hooks_sect = None
    for i, s in enumerate(o.sects):
        if (s['seg'], s['name']) == ('__HOOKS', '__hooks'):
            hooks_sect = i; s['new'] = None; continue
        if s['name'] in ('__compact_unwind', '__eh_frame') or s['seg'] == '__LD':
            raise SystemExit('object has %s,%s: build with -fno-unwind-tables -fno-asynchronous-unwind-tables' % (s['seg'], s['name']))
        if s['seg'] == '__TEXT':
            rx = (rx + s['align'] - 1) & -s['align']; s['new'] = rx; rx += s['size']
        elif s['seg'] == '__DATA':
            rw = (rw + s['align'] - 1) & -s['align']; s['new'] = rw; rw += s['size']
        else:
            raise SystemExit('unexpected section %s,%s' % (s['seg'], s['name']))
    assert rw <= RW_END, 'writable data %#x bytes: more than the %#x free' % (rw - RW_BASE, RW_END - RW_BASE)
    # symbols
    addr = {}
    for sym in o.syms:
        if sym['type'] & 0xE0:   # stabs
            continue
        if (sym['type'] & 0xE) == 0xE and sym['sect']:   # N_SECT
            s = o.sects[sym['sect'] - 1]
            if s.get('new') is not None:
                addr[sym['name']] = s['new'] + sym['value'] - s['addr']
    # hooks (read before resolving the trampolines they define)
    hooks = []
    if hooks_sect is not None:
        hs = o.sects[hooks_sect]
        targets = {}
        for (a, sn, pcrel, ln, ext, typ) in hs['relocs']:
            assert typ == R_UNSIGNED and ln == 3 and ext, 'hook table: unexpected relocation'
            targets[a] = o.syms[sn]['name']
        for k in range(0, hs['size'], 24):
            site, expect, kind = struct.unpack_from('<QII', hs['data'], k)
            tval = struct.unpack_from('<Q', hs['data'], k + 16)[0]
            hooks.append((site, expect, kind, targets.get(k + 16), tval))
    tramp = {}
    tramp_code = []
    tbase = (rx + 15) & ~15
    for site, expect, kind, tname, tval in hooks:
        if kind == 0:
            assert tname and tname.startswith('_h_'), 'entry hook target %r: name it h_<name>' % tname
            name = '_o_' + tname[3:]
            pc = tbase + 4 * len(tramp_code)
            tramp[name] = pc
            tramp_code.append(relocate_moved(expect, site, pc))
            tramp_code.append(enc_b(pc + 4, site + 4))
    for n, a in tramp.items():
        addr[n] = a

    def resolve(name):
        if name in addr:
            return addr[name]
        if name.startswith('_G_'):
            return int(name[3:], 16)
        raise SystemExit('undefined symbol %s' % name)

    # relocations
    for s in o.sects:
        if s.get('new') is None:
            continue
        d = s['data']; addend = 0
        for (a, sn, pcrel, ln, ext, typ) in s['relocs']:
            if typ == R_ADDEND:
                addend = sn - ((sn & 0x800000) << 1); continue
            assert ext, '%s: section-relative relocation type %d at %#x' % (s['name'], typ, a)
            target = resolve(o.syms[sn]['name']) + addend; addend = 0
            pc = s['new'] + a
            if typ == R_BRANCH26:
                wd = w32(d, a); struct.pack_into('<I', d, a, (wd & 0xFC000000) | (enc_b(pc, target) & 0x3FFFFFF))
            elif typ in (R_PAGE21, R_GOT_PAGE21):
                struct.pack_into('<I', d, a, fix_adrp(w32(d, a), pc, target))
            elif typ == R_PAGEOFF12:
                struct.pack_into('<I', d, a, fix_pageoff(w32(d, a), target))
            elif typ == R_GOT_PAGEOFF12:   # ldr xT, [xN, got@pageoff] -> add xT, xN, target@pageoff (no GOT: every address is fixed in the image)
                wd = w32(d, a); assert (wd & 0xFFC00000) == 0xF9400000, 'GOT load %08x' % wd
                struct.pack_into('<I', d, a, 0x91000000 | (target & 0xFFF) << 10 | (wd & 0x3FF))
            else:
                raise SystemExit('%s: relocation type %d at %#x (absolute pointers cannot be linked: the module base is not known)' % (s['name'], typ, a))
    # write
    end = max([tbase + 4 * len(tramp_code)] + [s['new'] + s['size'] for s in o.sects if s.get('new') is not None and s['seg'] == '__TEXT'])
    img += b'\0' * (end - len(img))
    for s in o.sects:
        if s.get('new') is None or s['zero']:
            continue
        img[s['new']:s['new'] + s['size']] = s['data']
    for i, wd in enumerate(tramp_code):
        struct.pack_into('<I', img, tbase + 4 * i, wd)
    for site, expect, kind, tname, tval in hooks:
        have = w32(img, site)
        assert have == expect, 'main+%#x holds %08x, not %08x' % (site, have, expect)
        if kind == 0:
            struct.pack_into('<I', img, site, enc_b(site, resolve(tname)))
        elif kind == 1:
            struct.pack_into('<I', img, site, tval & 0xFFFFFFFF)
        elif kind == 2:
            struct.pack_into('<I', img, site, enc_b(site, resolve(tname)))
        elif kind == 3:
            assert expect >> 26 == 0x25, 'main+%#x: not a bl' % site
            struct.pack_into('<I', img, site, enc_b(site, resolve(tname), link=True))
        else:
            raise SystemExit('hook kind %d' % kind)
    open(out, 'wb').write(img)
    print('%s: mod code main+%#x..%#x, data main+%#x..%#x, %d hooks (%d entry, %d word, %d branch, %d call)' % (
        out, code_base, end, RW_BASE, rw, len(hooks), *(sum(h[2] == k for h in hooks) for k in range(4))))


if __name__ == '__main__':
    link(sys.argv[1], sys.argv[2], sys.argv[3])
