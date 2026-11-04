# Cuphead 3-player mod: rough draft and estimate

Cuphead 1.3.7 for Switch (0100A5C00D162000), running as an NX2Apple app on a Mac. Written 2026-11-03,
before any of the mod existed. It is kept as a record of the plan and the spike; `README.md` describes the mod as built.

**Status, 2026-11-04 (later):** the full version replaces it: plane levels, the level audit
(`src/target_sites.h`: 40 calls in 31 methods now pick player two or three; cutscene code keeps the
real player two and P3 follows player one instead), the plane intro, P3's ghost, and a scripted
test pass over the base-game bosses, the run & guns, the DLC bosses and King Dice's mini-bosses
(see `README.md`). The audit found more two-player arrays: `Vibrator` (fixed), Chef Saltbaker's
defrost positions (P3 is moved by following player one instead), the Cowboy level's plane dust
(cosmetic, P3 has none).

**Status, 2026-11-04:** the minimum version is built and installed; see `README.md`. It was tested
with three scripted controllers in Elder Kettle's house, The Root Pack and Forest Follies. Steps 3,
4 and 6 of the build plan below (the level audit, the other modes and the full test pass) are what
remains for the full mod. One finding to add to the table: on Switch, player two joins with L+R
(`NintendoSwitchInputHelper.CheckForEngagement`), and `Vibrator` keeps per-player arrays of 2,
which made player three's first hit throw out of `PlayerStatsManager.TakeDamage`.

## Goal

A third player in co-op levels, on a third controller: boss fights, run & gun levels, plane levels,
and the DLC. P3 joins the same way P2 does, gets a HUD card, can die and be parried back to life,
and counts toward game over. P3 looks like Mugman with a tint (Cuphead has no third character).

## Existing PC mods don't port

The 3-player mods for PC (Nexus "Cuphead 3 Players Multiplayer co-op", GitHub Germanized/CupHeads)
are C# plugins loaded by BepInEx into the PC game's Mono runtime. The Switch build is IL2CPP: the
C# was compiled ahead of time to ARM64 machine code, so there is nothing for a C# plugin to hook.
They are still useful as a list of what has to change. The Switch mod has to make the same changes
as patches to machine code.

## What I found

### Already in place

- **Controllers.** NX2Apple exposes 8 controllers, and Cuphead registers No1–No8 plus Handheld
  (`SetSupportedNpadIdType 0x1ff`). A third pad reaches the game with no host changes.
- **Room for code.** The Mac loader maps everything from the patch area (main+0x3b40000) to the end
  of `main.patched.bin` as executable. New code can be appended after the existing aspect-ratio
  patch, and both mods coexist.
- **A symbol map.** `tools/il2cpp_map.py` is a parser I wrote for the IL2CPP metadata (v24).
  It produces `cuphead_1.3.7_dump.cs`:
  - 9,619 classes with every field offset.
  - Addresses of 62,730 methods.

  Every patch below is located with it. I didn't run the downloaded Il2CppDumper because it is
  external code.
- **Scalable storage.** `PlayerManager.players` and `PlayerManager.playerInputs` are
  `Dictionary<int, …>`, so a third entry fits without resizing anything.

### Two-player assumptions to change

| Area | What's hard-coded | Size |
|---|---|---|
| Player ids | `PlayerId` is {PlayerOne=0, PlayerTwo=1, Any=2, None=3}. P3 needs an id. 2 works mechanically, because `GetPlayer` is a plain dictionary lookup, but menu and input code uses `Any`. The other option is a new id such as 4. | design decision |
| Central helpers | `PlayerManager.GetNext` (toggles P1↔P2), `get_Center`/`get_CameraCenter` (P1/P2 average), `BothPlayersActive`, `GetRandom`, `GetFirst`, `get_Count`, `DoesPlayerExist` | 8 functions; `GetNext` alone has 222 callers in 169 classes, all fixed in one place |
| Bosses and levels that name P2 | `GetPlayer(PlayerTwo)` is hard-coded at 132 sites in 119 methods across 77 classes (69 boss/level, 8 UI, 7 core). Each site is either extended to P3 or left alone, and left alone means that attack ignores P3. | the bulk of the work |
| Save data | `PlayerData` has loadouts, inventories and stats as `playerOne`/`playerTwo` pairs. `GetPlayerLoadout` is called 73 times from 19 classes and is also inlined (spike 2 hit one). P3 can share P2's loadout. | ~20 classes |
| Fixed-size arrays | `PlayerManager.playerSlots[2]`, `playerWasChalice[2]`, `Level.players[2]`, `Level`'s bool[2] | ~6 allocations |
| Join and leave | `PlayerManager.Update` and `SetPlayerCanJoin` handle a P2 join, and `Level.CreatePlayerTwoOnJoin` spawns P2 mid-level | 3–4 functions |
| Death and game over | `Level.OnPlayerDeath` compares against 2 players; parry-revive ghosts | 2–3 functions |
| HUD | `LevelHUD` has a template and two `LevelHUDPlayer` slots (cuphead, mugman) | add a third card |
| Rewired input | The Rewired UserData (resources.assets object 1533) defines System, PlayerOne and PlayerTwo | add PlayerThree; RomFS overlay, same as the PS4 icon mod |
| Cutscene and interaction coroutines | `DialogueInteractionPoint`, `HouseElderKettle` and `Mausoleum` disable and re-enable P1's and P2's motors. Missing P3 can softlock. | ~10 classes |
| Results screen | `WinScreen` has 23 P1/P2 members | 1 class |
| Look | `LevelPlayerAnimationController` has cuphead/mugman/chalice objects | reuse Mugman, tint the sprite renderer |

A name scan for `playerOne`/`playerTwo`/`P1`/`P2`-style members found 228 members in 107 classes.
This is the upper bound of what might need a look.

## Feasibility spike

`tools/spike_patch.py` is a throwaway patch. It tests the riskiest assumption, that a level runs
with a third `PlayerController` in it. It:

- Calls `AbstractPlayerController.Create(PlayerId 2, …)` at the end of `Level.CreatePlayers`.
  P3 spawns halfway between the two co-op spawns and is stored in a 3-slot `Level.players`.
- Gives P3 player one's Rewired input (the test harness can only press buttons for P1).
- Points the inlined loadout lookups at P2's loadout.

Each run starts from a fresh save and walks into Elder Kettle's house and then Forest Follies,
using scripted input and screenshots.

| Run | Result | Fix |
|---|---|---|
| spike 1 | Crash on entering the house: `KeyNotFoundException` in `PlayerInput.Init`, which has `GetPlayerInput(id)` inlined | patch that inlined read as well |
| spike 2 | Crash on entering the house: null loadout in `PlayerStatsManager.LevelInit` (inlined `GetPlayerLoadout`: id 0 → playerOne, 1 → playerTwo, otherwise null) | let id ≥ 2 fall through to playerTwo |
| spike 3 | Crash on entering the house: null loadout in `LevelPlayerWeaponManager.LevelInit`, from `GetPlayerLoadout` itself | patch `GetPlayerLoadout` (one branch) |
| spike 4 | Runs the whole route without crashing: the house with P3 in it, exiting, and the overworld map | — |

What spike 4 shows (from screenshots, not included here):

- A third player controller spawns in a level. It gets Mugman's sprites because its id isn't 0.
- It walks with player one's input: at 160 s it has left the chair after P1 walked to the exit.
- It is torn down cleanly when the level unloads.

In the unmodified game, the same frame has nobody behind the chair.

Getting there took four runs and three fixes. Each fix was one instruction, plus a 12-instruction
wrapper for the spawn. That is about the pace the estimate below assumes for the "inlined
two-player code" kind of work.

The spike did not test:

- Combat, damage or bosses (the scripted route from a fresh save only reaches the house and the map).
- P2 and P3 together. This run was single player, so the level had P1 and P3.
- A real third controller.
- The HUD (P3 has no card).

It is not a mod: P3 can't be steered separately.

`tools/` also keeps the analysis scripts:

- `dis.py`: disassembly with method names.
- `where.py`: address to method.
- `scan_init.py` and `scan_switch.py`: id-switch scans.

## Build plan for the full mod

1. **Framework.**
   - Mod logic in C, compiled with Apple clang for freestanding arm64.
   - A small Python linker that appends the result after the aspect patch and writes the branch
     hooks and trampolines, like `spike_patch.py` does.
   - A header generated from the dump: struct offsets, method addresses, IL2CPP helpers
     (`Dictionary.get_Item`, class init, null and range exceptions).
   - One `install.py` for the module patch plus the RomFS overlay files, with an undo step like
     the other mods.
2. **Core.** P3's id and Rewired player; join, leave and spawn (start of level and mid-level);
   the central helpers; arrays resized to 3; save data (P3 uses P2's loadout); HUD card;
   death, revive and game over; P3's look.
3. **Level audit.** Go through the 77 classes that name P2 and the classes that call
   `GetPlayerLoadout`. For each, decide: extend to P3, or treat P3 as P2. Fix the cutscene
   coroutines that freeze specific players.
4. **Other modes.** Plane levels (separate plane controller and spawns), the Ms. Chalice charm,
   the DLC bosses, the Kingdice mini-bosses, and the results screen.
5. **Test harness.** Extend the host's scripted input so it can press buttons for P2 and P3, not
   only P1. Then every level can be smoke-tested with three players from scripts before you play.
6. **Full pass.** Every boss and run & gun with 3 players, fixing what breaks. Then a session with
   three real controllers on your side.

## Time estimate

| Area | Estimate |
|---|---|
| Framework and tooling (C toolchain, linker, header generator, installer, P2/P3 scripted input) | 1–1.5 days |
| Core (input, join and spawn, helpers, arrays, save data, HUD, death, revive and game over, look) | 2–3 days |
| Boss and level audit (77 classes, 172 P2 sites, inlined loadouts, coroutines) | 4–7 days |
| Plane levels, Chalice, DLC, Kingdice, results screen | 1–2 days |
| Full 3-player test pass and fixes | 3–5 days |
| **Total** | **about 2–3.5 weeks of focused work (80–140 h)** |

A **minimum viable version** takes about **1 week (30–45 h)**:

- P3 joins, plays and has a HUD card in the base-game bosses and run & guns.
- Death and game over count P3.
- Some boss attacks still target only P1/P2, and plane levels and the DLC are left out.

Your own testing time with three controllers is on top of both figures.

What could make it slower:

- Inlined two-player code that the scans can't find by name. Each one turns up as a crash, like in
  the spike, and costs about 15–30 minutes.
- Rewired assigning the third controller to PlayerThree.
- A Unity layer limit if P1, P2 and P3 each need their own collision layer.

What could make it faster:

- Most boss scripts go through `GetNext` and `GetRandom`, which are fixed in one place. A good
  share of the 77 classes may need nothing once those are done.
