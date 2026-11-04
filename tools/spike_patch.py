"""Three-player spike for Cuphead 1.3.7 (Switch 0100A5C00D162000) in the NX2Apple app: a third character in every level that allows co-op.

Usage: spike_patch.py IN_MAIN_PATCHED_BIN OUT
  IN:  the app's Contents/Resources/dm/main.patched.bin (any earlier patch, such as the aspect cave, is kept)
  OUT: the module with the spike

Not the mod: a feasibility test of its hardest assumption, that a level runs with a third player controller in it.
- Level.CreatePlayers (main+0x22d0b0) allocates Level.players with 3 slots instead of 2 (main+0x22d258: mov w1, #2 -> #3).
- Its entry jumps to a wrapper: the original function runs, then AbstractPlayerController.Create(PlayerId 2, pos, Level.playerMode)
  (main+0x2e0480) makes the third player, halfway between the level's two co-op spawns (the two plane spawns in a plane level), and
  the wrapper stores it in Level.players[2]. Skipped where the level allows no co-op (Level.allowMultiplayer, +0x70) or has no
  players (playerMode 10000000).
- PlayerData.PlayerLoadouts.GetPlayerLoadout (main+0x421820) and its inlined copies give PlayerId 2 player two's loadout.
- The reads of PlayerManager.playerInputs[id] (PlayerManager.GetPlayerInput, main+0x424f70, and PlayerInput.Init, main+0x424e70, where it
  is inlined) answer PlayerId 2 with player one's Rewired player, so the third character copies player one's input (the host's scripted
  input only drives player one). The mod gives it a Rewired player of its own.
The code is appended after the patch area: on the Mac the loader maps a module file's whole tail from PATCH_OFF as read+execute.
"""
import struct
import sys

CREATE_PLAYERS, PLAYERS_ALLOC = 0x22D0B0, 0x22D258
# The dictionary reads of PlayerManager.playerInputs[id]: (site, its instruction, the register it copies the id to, the id register)
INPUT_READS = [(0x424F88, 0x2A0103F3, 19, 1),   # PlayerManager.GetPlayerInput: mov w19, w1
               (0x424F24, 0x2A1403E1, 1, 20)]   # PlayerInput.Init (GetPlayerInput inlined): mov w1, w20
# PlayerData loadout lookups (id 0 -> playerOne, 1 -> playerTwo, else null) give id 2 playerTwo's: (site, its instruction, the replacement)
WORDS = [(0x421828, 0x350000E1, 0x35000081),   # PlayerLoadouts.GetPlayerLoadout: cbnz w1, null -> cbnz w1, playerTwo
         (0x4339A0, 0x54000161, 0xD503201F)]   # PlayerStatsManager.LevelInit (inlined): cmp w20, #1; b.ne null -> nop
CREATE = 0x2E0480                           # AbstractPlayerController.Create(PlayerId, Vector2, PlayerMode)
PLAYER_MODE, ALLOW_MP, SPAWNS, PLAYERS = 0x6C, 0x70, 0x80, 0xB0
PLANE_P1, PLANE_P2 = 0xF8, 0x104            # Level.player1PlaneSpawnPos, player2PlaneSpawnPos (Vector3)
SPAWN_P1, SPAWN_P2 = 0x10, 0x18             # Level.Spawns.playerOne, playerTwo (Vector2)
NO_PLAYERS = 10000000                       # the playerMode CreatePlayers returns early for

EQ, NE, HS, LO = 0, 1, 2, 3


def w(img, off):
    return struct.unpack_from('<I', img, off)[0]


class Asm:
    def __init__(self, base):
        self.base, self.code, self.fix = base, [], []

    def here(self):
        return self.base + 4 * len(self.code)

    def emit(self, *words):
        self.code.extend(words)

    def label(self):
        return self.here()

    def b(self, to, link=False):
        self.emit((0x94000000 if link else 0x14000000) | (((to - self.here()) >> 2) & 0x3FFFFFF))

    def b_fwd(self, kind, cond=0, reg=0):
        """a forward branch to a label not known yet; returns a handle for bind()"""
        self.fix.append((len(self.code), kind, cond, reg)); self.emit(0)
        return len(self.fix) - 1

    def bind(self, h, to):
        i, kind, cond, reg = self.fix[h]
        d = ((to - (self.base + 4 * i)) >> 2)
        if kind == 'b':
            self.code[i] = 0x14000000 | (d & 0x3FFFFFF)
        elif kind == 'bcond':
            self.code[i] = 0x54000000 | (d & 0x7FFFF) << 5 | cond
        elif kind == 'cbz_w':
            self.code[i] = 0x34000000 | (d & 0x7FFFF) << 5 | reg
        elif kind == 'cbz_x':
            self.code[i] = 0xB4000000 | (d & 0x7FFFF) << 5 | reg

    def bytes(self):
        return struct.pack('<%dI' % len(self.code), *self.code)


def ldr_w(t, n, off): return 0xB9400000 | (off // 4) << 10 | n << 5 | t
def ldr_x(t, n, off): return 0xF9400000 | (off // 8) << 10 | n << 5 | t
def str_x(t, n, off): return 0xF9000000 | (off // 8) << 10 | n << 5 | t
def ldrb(t, n, off): return 0x39400000 | off << 10 | n << 5 | t
def ldr_s(t, n, off): return 0xBD400000 | (off // 4) << 10 | n << 5 | t
def ldp_s(t, t2, n, off): return 0x2D400000 | ((off // 4) & 0x7F) << 15 | t2 << 10 | n << 5 | t
def fadd_s(d, n, m): return 0x1E202800 | m << 16 | n << 5 | d
def fmul_s(d, n, m): return 0x1E200800 | m << 16 | n << 5 | d
def fmov_s_half(d): return 0x1E2C1000 | d             # fmov sD, #0.5
def movz_w(d, imm, sh=0): return 0x52800000 | (sh // 16) << 21 | imm << 5 | d
def movk_w(d, imm, sh=0): return 0x72800000 | (sh // 16) << 21 | imm << 5 | d
def cmp_w_imm(n, imm): return 0x7100001F | imm << 10 | n << 5
def cmp_w(n, m): return 0x6B00001F | m << 16 | n << 5
def mov_x(d, m): return 0xAA0003E0 | m << 16 | d
def csel_w(d, n, m, cond): return 0x1A800000 | m << 16 | cond << 12 | n << 5 | d


STP_FP_LR_PRE32 = 0xA9BE7BFD     # stp x29, x30, [sp, #-32]!
STP_X19_X20_16 = 0xA90153F3      # stp x19, x20, [sp, #16]
MOV_FP_SP = 0x910003FD           # mov x29, sp
LDP_X19_X20_16 = 0xA94153F3      # ldp x19, x20, [sp, #16]
LDP_FP_LR_POST32 = 0xA8C27BFD    # ldp x29, x30, [sp], #32
RET = 0xD65F03C0
XZR = 31


def main(src, out):
    img = bytearray(open(src, 'rb').read())
    assert w(img, PLAYERS_ALLOC) == 0x321F03E1, 'main+%#x: not mov w1, #2 (orr w1, wzr, #2)' % PLAYERS_ALLOC
    assert w(img, CREATE_PLAYERS) == 0xFC1A0FEA, 'main+%#x: not CreatePlayers\' str d10, [sp, #-0x60]!' % CREATE_PLAYERS
    for site, word, _, _ in INPUT_READS:
        assert w(img, site) == word, 'main+%#x: not %08x' % (site, word)
    for site, word, _ in WORDS:
        assert w(img, site) == word, 'main+%#x: not %08x' % (site, word)
    base = (len(img) + 15) & ~15
    img += b'\0' * (base - len(img))
    a = Asm(base)

    # playerInputs[id] reads: id 2 -> PlayerOne's input (the id register itself keeps 2)
    reads = []
    for site, _, dst, src in INPUT_READS:
        reads.append((site, a.here()))
        a.emit(cmp_w_imm(src, 2), csel_w(dst, XZR, src, EQ))
        a.b(site + 4)

    # Level.CreatePlayers wrapper
    wrap = a.here()
    a.emit(STP_FP_LR_PRE32, STP_X19_X20_16, MOV_FP_SP, mov_x(19, 0))
    body_call = len(a.code); a.emit(0)                    # bl body, bound below
    a.emit(ldr_w(8, 19, PLAYER_MODE), movz_w(9, NO_PLAYERS & 0xFFFF), movk_w(9, NO_PLAYERS >> 16, 16), cmp_w(8, 9))
    done = [a.b_fwd('bcond', EQ)]
    a.emit(ldrb(8, 19, ALLOW_MP)); done.append(a.b_fwd('cbz_w', reg=8))
    a.emit(ldr_w(8, 19, PLAYER_MODE), cmp_w_imm(8, 1)); level = a.b_fwd('bcond', NE)
    a.emit(ldr_s(0, 19, PLANE_P1), ldr_s(1, 19, PLANE_P1 + 4), ldr_s(2, 19, PLANE_P2), ldr_s(3, 19, PLANE_P2 + 4))
    mid = a.b_fwd('b')
    a.bind(level, a.here())
    a.emit(ldr_x(8, 19, SPAWNS)); done.append(a.b_fwd('cbz_x', reg=8))
    a.emit(ldp_s(0, 1, 8, SPAWN_P1), ldp_s(2, 3, 8, SPAWN_P2))
    a.bind(mid, a.here())
    a.emit(fadd_s(0, 0, 2), fadd_s(1, 1, 3), fmov_s_half(4), fmul_s(0, 0, 4), fmul_s(1, 1, 4))
    a.emit(mov_x(0, XZR), movz_w(1, 2), ldr_w(2, 19, PLAYER_MODE), mov_x(3, XZR))
    a.b(CREATE, link=True)
    a.emit(ldr_x(8, 19, PLAYERS)); done.append(a.b_fwd('cbz_x', reg=8))
    a.emit(ldr_w(9, 8, 0x18), cmp_w_imm(9, 3)); done.append(a.b_fwd('bcond', LO))
    a.emit(str_x(0, 8, 0x30))                               # players[2]
    for h in done:
        a.bind(h, a.here())
    a.emit(LDP_X19_X20_16, LDP_FP_LR_POST32, RET)
    body = a.here()
    a.code[body_call] = 0x94000000 | (((body - (wrap + 4 * 4)) >> 2) & 0x3FFFFFF)
    a.emit(w(img, CREATE_PLAYERS))                          # the original first instruction
    a.b(CREATE_PLAYERS + 4)

    img += a.bytes()
    struct.pack_into('<I', img, PLAYERS_ALLOC, movz_w(1, 3))
    for site, _, new in WORDS:
        struct.pack_into('<I', img, site, new)
    for site, to in reads:
        struct.pack_into('<I', img, site, 0x14000000 | (((to - site) >> 2) & 0x3FFFFFF))
    struct.pack_into('<I', img, CREATE_PLAYERS, 0x14000000 | (((wrap - CREATE_PLAYERS) >> 2) & 0x3FFFFFF))
    open(out, 'wb').write(img)
    print('%s: spike code main+%#x..%#x (input reads %s, CreatePlayers wrapper %#x)' % (out, base, a.here(), ' '.join('%#x' % t for _, t in reads), wrap))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
