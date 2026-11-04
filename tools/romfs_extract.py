"""Copies one file out of an NX2Apple app's romfs.img (DMROMFS1).

Usage: romfs_extract.py ROMFS_IMG PATH OUT   (PATH as in the RomFS, e.g. /Data/resources.assets)

The header is the magic and three u64s: the index's offset and size, and the entry count. The index is n 24-byte entries
(a, b, name offset, name length, is-file) followed by the names; a file's a/b are its data offset and size, a directory's are
the range of its children's entry numbers. Entry 0 is the root.
"""
import struct
import sys


def romfs_file(img, want):
    f = open(img, 'rb'); h = f.read(0x20)
    assert h[:8] == b'DMROMFS1', 'not a DMROMFS1 image'
    ioff, isz, n = struct.unpack_from('<QQQ', h, 8)
    f.seek(ioff); d = f.read(isz); names = d[n * 24:]
    ents = [struct.unpack_from('<QQIHH', d, i * 24) for i in range(n)]

    def walk(i, path):
        a, b, no, nl, isf = ents[i]
        p = path + '/' + names[no:no + nl].decode() if i else ''
        if isf:
            if p == want:
                f.seek(a); return f.read(b)
            return None
        for c in range(a, a + b):
            r = walk(c, p)
            if r is not None:
                return r
    return walk(0, '')


if __name__ == '__main__':
    data = romfs_file(sys.argv[1], sys.argv[2])
    assert data is not None, '%s not found in %s' % (sys.argv[2], sys.argv[1])
    open(sys.argv[3], 'wb').write(data)
