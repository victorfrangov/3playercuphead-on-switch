"""Class, field and method map of Cuphead 1.3.7's IL2CPP code (Switch 0100A5C00D162000, Unity 2017.4.9f1, metadata v24.0).

Usage: il2cpp_map.py MAIN_IMAGE GLOBAL_METADATA OUT
  MAIN_IMAGE:      the main module as a flat image with its MOD0 / dynamic section (the decompressed NSO, the offsets main.patched.bin keeps)
  GLOBAL_METADATA: Data/Managed/Metadata/global-metadata.dat from the RomFS
  OUT:             a text dump: one block per class, its fields with offsets (static ones marked) and its methods with main offsets

The method and field names are in the metadata; the code pointers and field offsets are in two tables in main's data:
- CodeRegistration (v24.0): methodPointersCount, methodPointers, ... The methods' methodIndex index methodPointers.
- MetadataRegistration: ..., typesCount, types, ..., fieldOffsetsCount, fieldOffsets, typeDefinitionsSizesCount, typeDefinitionsSizes, ...
Both are found by their counts, which the metadata gives, followed by a pointer; every pointer in main's data is an R_AARCH64_RELATIVE relocation.
"""
import struct
import sys
from collections import defaultdict

TYPE_NAMES = {1: 'void', 2: 'bool', 3: 'char', 4: 'sbyte', 5: 'byte', 6: 'short', 7: 'ushort', 8: 'int', 9: 'uint', 10: 'long', 11: 'ulong',
              12: 'float', 13: 'double', 14: 'string', 0x18: 'IntPtr', 0x19: 'UIntPtr', 0x1c: 'object'}


def load_image(path):
    b = open(path, 'rb').read()
    mo = struct.unpack_from('<I', b, 4)[0]
    dyn = mo + struct.unpack_from('<i', b, mo + 4)[0]
    d = {}
    i = dyn
    while True:
        t, v = struct.unpack_from('<qQ', b, i); i += 16
        if t == 0:
            break
        d.setdefault(t, v)
    rel = {}
    for j in range(d[7], d[7] + d[8], 24):
        off, info, add = struct.unpack_from('<QQq', b, j)
        if info & 0xffffffff == 1027:   # R_AARCH64_RELATIVE
            rel[off] = add
    return b, rel


class Metadata:
    def __init__(self, path):
        m = self.m = open(path, 'rb').read()
        sanity, ver = struct.unpack_from('<Ii', m, 0)
        assert sanity == 0xFAB11BAF and ver == 24, (hex(sanity), ver)
        h = struct.unpack_from('<66i', m, 8)
        names = ['stringLiteral', 'stringLiteralData', 'string', 'events', 'properties', 'methods', 'parameterDefaultValues', 'fieldDefaultValues',
                 'fieldAndParameterDefaultValueData', 'fieldMarshaledSizes', 'parameters', 'fields', 'genericParameters', 'genericParameterConstraints',
                 'genericContainers', 'nestedTypes', 'interfaces', 'vtableMethods', 'interfaceOffsets', 'typeDefinitions', 'rgctxEntries', 'images',
                 'assemblies', 'metadataUsageLists', 'metadataUsagePairs', 'fieldRefs', 'referencedAssemblies', 'attributesInfo', 'attributeTypes',
                 'unresolvedVirtualCallParameterTypes', 'unresolvedVirtualCallParameterRanges', 'windowsRuntimeTypeNames', 'exportedTypeDefinitions']
        self.sec = {n: (h[2 * i], h[2 * i + 1]) for i, n in enumerate(names)}
        self.types = self.table('typeDefinitions', '<20i8H2I')
        self.methods = self.table('methods', '<11iI4H')
        self.fields = self.table('fields', '<4i')
        self.params = self.table('parameters', '<4i')
        self.images = self.table('images', '<8i')

    def table(self, name, fmt):
        off, size = self.sec[name]
        n = struct.calcsize(fmt)
        assert size % n == 0, (name, size, n)
        return [struct.unpack_from(fmt, self.m, off + i * n) for i in range(size // n)]

    def s(self, idx):
        off = self.sec['string'][0] + idx
        return self.m[off:self.m.index(b'\0', off)].decode('utf-8', 'replace')


def find_tables(img, rel, md):
    """offsets of CodeRegistration and MetadataRegistration in main"""
    n_ptrs = max(m[6] for m in md.methods) + 1
    n_types = len(md.types)
    code = meta = None
    for off in sorted(rel):
        o = off - 8
        if o < 0:
            continue
        if struct.unpack_from('<Q', img, o)[0] == n_ptrs and code is None:
            p = rel[off]
            if rel.get(p) is not None and rel.get(p + 8) is not None:
                code = o
        if struct.unpack_from('<Q', img, o)[0] == n_types and struct.unpack_from('<Q', img, o + 16)[0] == n_types and (o + 24) in rel:
            meta = o - 80     # fieldOffsetsCount is the 11th field
    assert code is not None and meta is not None, (code, meta)
    return code, meta, n_ptrs


class Map:
    def __init__(self, img, rel, md):
        self.img, self.rel, self.md = img, rel, md
        self.code, self.meta, n_ptrs = find_tables(img, rel, md)
        mp = rel[self.code + 8]
        self.mptr = [rel.get(mp + 8 * i, 0) for i in range(n_ptrs)]
        self.n_il2cpp_types = struct.unpack_from('<Q', img, self.meta + 48)[0]
        self.types_at = rel[self.meta + 56]
        fo = rel[self.meta + 88]
        self.field_offs = [rel.get(fo + 8 * i) for i in range(len(md.types))]

    def q(self, off):
        return struct.unpack_from('<Q', self.img, off)[0]

    def il2cpp_type(self, idx):
        p = self.rel[self.types_at + 8 * idx]
        return p

    def type_name_at(self, p, depth=0):
        """name of the Il2CppType at main offset p"""
        if depth > 6:
            return '?'
        data = self.q(p); bits = struct.unpack_from('<I', self.img, p + 8)[0]
        t = (bits >> 16) & 0xff
        if t in TYPE_NAMES:
            return TYPE_NAMES[t]
        if t in (0x11, 0x12):   # VALUETYPE, CLASS: data is the type definition index
            return self.td_name(data)
        if t == 0x1d:           # SZARRAY: data points to the element type
            return self.type_name_at(self.rel.get(p, data), depth + 1) + '[]'
        if t == 0x0f:           # PTR
            return self.type_name_at(self.rel.get(p, data), depth + 1) + '*'
        if t == 0x15:           # GENERICINST: data points to Il2CppGenericClass {typeDefinitionIndex, context {class_inst, method_inst}, cached_class}
            gc = self.rel.get(p, data)
            base = self.td_name(struct.unpack_from('<i', self.img, gc)[0])
            inst = self.rel.get(gc + 8)
            args = []
            if inst:
                argc = self.q(inst); argv = self.rel.get(inst + 8)
                for i in range(argc):
                    args.append(self.type_name_at(self.rel[argv + 8 * i], depth + 1))
            return '%s<%s>' % (base.split('`')[0], ', '.join(args))
        if t in (0x13, 0x1e):   # VAR, MVAR
            return '!%d' % data
        return 'type%#x' % t

    def type_name(self, idx):
        return self.type_name_at(self.il2cpp_type(idx))

    def type_attrs(self, idx):
        return struct.unpack_from('<I', self.img, self.il2cpp_type(idx) + 8)[0] & 0xffff

    def td_name(self, i):
        t = self.md.types[i]
        name, ns, decl = self.md.s(t[0]), self.md.s(t[1]), t[5]
        if decl >= 0:
            return self.type_name(decl) + '.' + name
        return (ns + '.' if ns else '') + name


def dump(mp, out):
    md = mp.md
    image_of = {}
    for im in md.images:
        for i in range(im[2], im[2] + im[3]):
            image_of[i] = md.s(im[0])
    with open(out, 'w') as f:
        f.write('# CodeRegistration main+%#x, MetadataRegistration main+%#x, %d methods with code, %d types\n' % (mp.code, mp.meta, sum(1 for p in mp.mptr if p), len(md.types)))
        for i, t in enumerate(md.types):
            name = mp.td_name(i)
            parent = mp.type_name(t[6]) if t[6] >= 0 else ''
            f.write('\n// %s\nclass %s%s  // TypeDefIndex %d\n' % (image_of.get(i, '?'), name, ' : ' + parent if parent else '', i))
            fstart, fcount = t[12], t[22]
            offs = mp.field_offs[i]
            for k in range(fcount):
                fd = md.fields[fstart + k]
                attrs = mp.type_attrs(fd[1])
                o = struct.unpack_from('<i', mp.img, offs + 4 * k)[0] if offs else -1
                kind = 'const ' if attrs & 0x40 else 'static ' if attrs & 0x10 else ''
                f.write('  %s%s %s;  // %#x\n' % (kind, mp.type_name(fd[1]), md.s(fd[0]), o))
            mstart, mcount = t[13], t[20]
            for k in range(mcount):
                m = md.methods[mstart + k]
                ps = []
                for j in range(m[15]):
                    p = md.params[m[3] + j]
                    ps.append('%s %s' % (mp.type_name(p[3]), md.s(p[0])))
                addr = mp.mptr[m[6]] if m[6] >= 0 else 0
                static = 'static ' if m[13] & 0x10 else ''
                f.write('  %s%s %s(%s);  // %s\n' % (static, mp.type_name(m[2]), md.s(m[0]), ', '.join(ps), ('main+%#x' % addr) if addr else '-'))


if __name__ == '__main__':
    img, rel = load_image(sys.argv[1])
    md = Metadata(sys.argv[2])
    mp = Map(img, rel, md)
    dump(mp, sys.argv[3])
    print('CodeRegistration main+%#x, MetadataRegistration main+%#x; wrote %s' % (mp.code, mp.meta, sys.argv[3]))
