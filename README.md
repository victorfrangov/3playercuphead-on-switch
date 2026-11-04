# Cuphead 3-player mod

Adds a third player to Cuphead's co-op. It is for Cuphead 1.3.7 for Nintendo Switch (title ID
0100A5C00D162000) running as a Mac app built with NX2Apple. Player three plays in boss fights,
plane levels, run & guns, the DLC and King Dice's mini-bosses. It has its own controller, HP card
and green-tinted Mugman look, and is counted for game over.

This repository contains only the mod's source code and tools, no game files. You need your own
copy of the game, and the install builds the mod against your app's files. This is an unofficial
fan mod, not affiliated with or endorsed by Studio MDHR.

## Playing

1. Connect three controllers.
2. Player two joins the Switch way: press **L+R** on the second controller. In a level, the game
   asks first; press L+R again to confirm.
3. Once player two is in, press any button on the third controller. Player three appears at
   player one's position, with the join sound. It looks like Mugman with a green tint and has its
   own HP card to the right of player one's.

Player three can join wherever player two can: on the map, and in a level until it ends. Like
player two, someone who joins mid-level starts with 1 HP; everyone starts the next level with full
health. Player three stays in for the following levels. It leaves when its controller is
disconnected, when player two leaves, or when you go back to the title screen or the save slots.

## What player three takes part in

- **Boss fights, run & guns and plane levels.** In plane levels player three flies its own plane,
  tinted green. It plays the level intro together with player two.
- **Death, revival and game over.** Player three dies like the others: the body disappears and a
  green Mugman ghost rises. Parrying the ghost brings player three back with 1 HP. The level is
  lost only when all three are dead.
- **Boss attacks.** Attacks that pick a target through the game's shared helpers pick from all
  living players. Attacks and level objects that check player two by name (31 places: proximity
  mines, attacks that go for the nearest player, pits, coins, the run & gun finish line, enemy
  spawners) check player three in player two's place on every other frame, and player three alone
  while player two is dead.
- **Cutscenes and phase changes.** When the game moves players one and two (the Devil's second
  phase, Chef Saltbaker's freeze) or sets them inactive (swallowed by Glumstone the Giant), player
  three follows player one: it is moved to player one when player one jumps across the screen in
  one frame, and is set inactive while players one and two are. On a tilting
  platform it is kept upright, as the game does for the other two.
- **Camera, damage and loadout.** The camera centre uses all living players. Each player's damage
  is scaled to 1/3 with three players alive (the game uses 1/2 for two), so a boss lasts about as
  long as it does solo. Player three uses player two's weapons and charm.
- **Rumble.** Player three's hits go through the game's rumble code like the others'.

## Tested

With scripted controllers, from a fresh save, with the test build (see below):

- **Joining and leaving**: players two and three join in Elder Kettle's house. Player
  three leaves when its controller is unplugged and rejoins when it's plugged back in.
- **Death and game over**: The Root Pack is lost only when all three players are dead. Player
  three was killed and revived by the test trigger 7 times in a row. Each time it came back with
  1 HP and kept its tint, and the ghost was a green Mugman.
- **Base-game bosses**: The Root Pack, Goopy Le Grande, Cagney Carnation, Ribby and Croaks,
  Baroness Von Bon Bon, Beppi, Grim Matchstick, Captain Brineybeard, Rumor Honeybottoms, Werner
  Werman, Sally Stageplay and the Devil were played with three players. All but Ribby and Croaks
  were won within the 75 s run. Dr. Kahl's Robot and the Phantom Express were played for 75 s
  without being won.
- **Plane levels**: Hilda Berg, Cala Maria and Djimmi were won with three planes. Wally Warbles
  was played for 75 s.
- **Run & guns**: Forest Follies and Funhouse Frazzle were finished. In Treetop Trouble, Funfair
  Fever, Rugged Ridge and Perilous Piers, the scripted route got all three players stuck on
  terrain partway through, with no errors.
- **DLC**:
  - Won: Glumstone the Giant (including being swallowed), Mortimer Freeze, the Howling Aces and
    Esther Winchester (both in planes), and Chef Saltbaker to the ending cutscene.
  - Played for 75 s: the Moonshine Mob, the Knight and the Bishop.
- **King Dice**: Tipsy Troop, Hopus Pocus, Phear Lap, Pirouletta and Mangosteen were won. Each
  was followed by King Dice's board with all three players. King Dice himself wasn't fought.

None of these runs crashed, and the mod logged no errors. The scripted players only walk, jump
and shoot. They kept full health and dealt 40 times the usual damage, so long fights and the
balance with three players are not covered.

## Limits

- The results screen shows players one and two only.
- Player three can't become Ms. Chalice; it keeps player two's loadout otherwise.
- Player three can't talk to characters or use doors and other interaction points; players one
  and two do that.
- During some cutscenes in which the game locks players one and two in place, player three can
  still walk around.
- The arcade (Retro Arcade) mode and the King Dice board game's player-two choices are as in the
  two-player game.
- Real controllers and rumble on real hardware are untested.

## Requirements

- A Mac with Apple silicon and the Cuphead 1.3.7 Switch app built with NX2Apple
  (`0100A5C00D162000.app`), with the DLC if you want to play it.
- Xcode or the Xcode command-line tools (`xcode-select --install`), for `clang` and `codesign`.
- Python 3 with [UnityPy](https://pypi.org/project/UnityPy/) (`pip install UnityPy`).
- Three controllers the app recognizes.

## Install and undo

Quit Cuphead first. Run the scripts from this folder.

```bash
PY=python3 tools/install.sh /path/to/0100A5C00D162000.app
```

The install script:

1. Builds the mod from `src/` and links it into a copy of the app's `main.patched.bin`. Before
   patching, it checks every instruction it changes against what Cuphead 1.3.7 should have there.
   If your app's module is different (another game version, or another mod in the same places),
   it stops without changing anything.
2. Adds a PlayerThree to the game's input data (Rewired, in `Data/resources.assets`) in the app's
   RomFS overlay:
   - If the app's `Contents/Resources/dm/env.txt` already sets `DM_ROMFS_OVERLAY`, for example for
     another mod, it patches that overlay's `resources.assets`.
   - Otherwise it takes the file from the app's `romfs.img`, writes it to this folder's `romfs/`,
     and adds `DM_ROMFS_OVERLAY` to `env.txt`.
3. Copies both into place and re-signs the app (ad hoc). Re-signing a large app takes a few
   minutes.

The first install keeps everything it replaces in `backup/`. To install again after changing the
source, run the same command.

To undo:

```bash
tools/uninstall.sh
```

It puts back the module, the overlay file and `env.txt` from `backup/`, then re-signs the app.

## Building and the test build

- `tools/build.sh` builds `build/main.patched.bin` from `src/` without installing it.
- `tools/build.sh test` builds a test variant. It can keep the players' health full, multiply the
  damage the players deal, load a level and trigger a revive, all through values the test host
  writes into the mod's memory. That host, a modified NX2Apple `dmhost` with scripted
  controllers, is not part of this repository.
- `src/target_sites.h` is generated by `tools/target_sites.py`. It reads a class and method map of
  the game, which `tools/il2cpp_map.py` makes from your own copy of the game: the main module and
  `global-metadata.dat`. See each script's header for its arguments.

## Files

- `src/mod.c`, `src/mod.h`: the mod, in C. Hooks are declared in the source; `mod.h` explains the
  hook table.
- `src/target_sites.h`: the game's `GetPlayer(PlayerTwo)` calls that pick or detect a player,
  redirected to player two or three. `tools/target_sites.py` lists the methods and why each is
  included.
- `tools/install.sh`, `tools/uninstall.sh`: install and undo, as above.
- `tools/build.sh`: compiles `mod.c` (freestanding arm64) and links it with `tools/link_mod.py`.
- `tools/link_mod.py`: appends the code to the module, writes the hooks, trampolines and
  redirected calls, and checks every patched instruction against what it expects.
- `tools/rewired_p3.py`: adds the PlayerThree record to Rewired's data (object 1533).
- `tools/romfs_extract.py`: copies a file out of the app's `romfs.img`.
- `tools/il2cpp_map.py`, `tools/dis.py`, `tools/where.py`, `tools/scan_*.py`: analysis tools used
  to find what to patch.
- `tools/spike_patch.py`: the throwaway patch from the feasibility spike.
- `DRAFT.md`: the original plan, estimate and spike results.

## License

MIT, see `LICENSE`. The license covers this repository's code only. Cuphead and its files belong
to StudioMDHR Entertainment Inc.
