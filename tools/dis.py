"""dis.py MODULE DUMP START END [START END ...]: disassemble main (MODULE, e.g. backup/main.patched.bin.before_3player) with IL2CPP
method names from DUMP (il2cpp_map.py's output) on branch targets"""
import sys,re,capstone,struct
b=open(sys.argv[1],'rb').read()
names={}; cur=None
for line in open(sys.argv[2]):
    if line.startswith('class '): cur=line.split()[1]
    m=re.search(r'\s(\S+)\((.*)\);\s+//\s+main\+(0x[0-9a-f]+)',line)
    if m and cur: names.setdefault(int(m.group(3),16),'%s::%s'%(cur,m.group(1)))
md=capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
args=[int(x,16) for x in sys.argv[3:]]
for a,e in zip(args[::2],args[1::2]):
    print('----',hex(a),names.get(a,''))
    for i in md.disasm(b[a:e],a):
        s='%x  %-6s %s'%(i.address,i.mnemonic,i.op_str)
        if i.mnemonic in('bl','b') and i.op_str.startswith('#'):
            s+='   ; '+names.get(int(i.op_str[1:],16),'')
        print(s)
