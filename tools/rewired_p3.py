"""Adds a PlayerThree to Cuphead's Rewired data (resources.assets object 1533, Rewired.Data.UserData): the mod's player three input.

Usage: rewired_p3.py IN_RESOURCES_ASSETS OUT_RESOURCES_ASSETS   (IN may already have it: then OUT is IN unchanged)

The record is player two's (the same default joystick maps: category 1 and 2, layout 0) with _id 3, the names PlayerThree and
"Player Three", no keyboard at start, and excluded from Rewired's controller auto-assignment: the mod gives it a controller when a
third one presses a button. It goes after player two's, so at runtime it is Rewired player 2 (runtime ids are list positions,
System not counted). The players list count and the editor's player id counter go up by one. Offsets are Cuphead 1.3.7's (Switch);
everything is checked before anything is written.
"""
import struct
import sys

import UnityPy

USERDATA = 1533
PLAYERS_COUNT = 0x1C8   # Rewired players list length (System, PlayerOne, PlayerTwo)
P2 = 0x284              # player two's record: _id, _name, _descriptiveName, then the fields copied below
P2_FIELDS = 0x2A8       # _startPlaying .. _excludeFromControllerAutoAssignment
P2_END = 0x2E4          # the actions list follows
ASSIGN_KB, EXCLUDE = 0x34, 0x38   # in the copied fields: _assignKeyboardOnStart, _excludeFromControllerAutoAssignment
COUNTER_FROM_END = 0x44           # playerIdCounter, the first of the editor's id counters at the end


def u32(d, o):
    return struct.unpack_from('<I', d, o)[0]


def ustr(s):
    b = s.encode()
    return struct.pack('<I', len(b)) + b + b'\0' * (-len(b) % 4)


def main(src, out):
    env = UnityPy.load(src)
    sf = next(iter(env.files.values()))
    obj = sf.objects[USERDATA]
    d = bytearray(obj.get_raw_data())
    if ustr('PlayerThree') in d[PLAYERS_COUNT:P2_END + 0x60]:
        assert u32(d, PLAYERS_COUNT) == 4, 'PlayerThree is there but the players count is %d' % u32(d, PLAYERS_COUNT)
        print('%s: already has PlayerThree' % src)
        open(out, 'wb').write(open(src, 'rb').read())
        return
    assert obj.type.name == 'MonoBehaviour', obj.type.name
    assert u32(d, PLAYERS_COUNT) == 3, 'players count %d' % u32(d, PLAYERS_COUNT)
    assert u32(d, P2) == 2 and bytes(d[P2 + 4:P2 + 20]) == ustr('PlayerTwo') and bytes(d[P2 + 20:P2_FIELDS]) == ustr('Player Two'), \
        'player two record not at %#x' % P2
    assert u32(d, P2_END) == 24, 'actions list not at %#x' % P2_END
    counter = len(d) - COUNTER_FROM_END
    assert u32(d, counter) == 3, 'playerIdCounter %d' % u32(d, counter)
    fields = bytearray(d[P2_FIELDS:P2_END])
    struct.pack_into('<I', fields, ASSIGN_KB, 0)
    struct.pack_into('<I', fields, EXCLUDE, 1)
    rec = struct.pack('<I', 3) + ustr('PlayerThree') + ustr('Player Three') + bytes(fields)
    struct.pack_into('<I', d, counter, 4)
    struct.pack_into('<I', d, PLAYERS_COUNT, 4)
    d[P2_END:P2_END] = rec
    obj.set_raw_data(bytes(d))
    open(out, 'wb').write(sf.save())
    print('%s: PlayerThree added (%d bytes at UserData+%#x)' % (out, len(rec), P2_END))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
