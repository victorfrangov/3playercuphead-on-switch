// Cuphead 3-player mod (Switch 1.3.7, 0100A5C00D162000): a third player in the regular levels and the plane levels.
//
// Player three is PlayerId 2 (PlayerId has PlayerOne 0, PlayerTwo 1, Any 2147483646, None 2147483647), with Rewired player 2
// (PlayerThree, added to Rewired's data in resources.assets by tools/rewired_p3.py). Joining: once player two is in and joining is
// allowed (player two's slot can join), a button on a controller no player has makes it player three's. P3 leaves when that
// controller goes away or player two leaves. PlayerManager's two slots are not grown: every loop over them maps slot i to
// PlayerOne or PlayerTwo, so a third slot would act as player two; P3's joining runs here instead, after PlayerManager.Update.
// In a level P3 is created with player two's loadout (PlayerLoadouts.GetPlayerLoadout gives any id > 0 player two's), Mugman's
// sprites (any id but 0) tinted, a HUD card next to player one's, and counts in the target picking, the camera, damage scaling
// and game over. In plane levels P3 flies a plane the same way. Arcade (PlayerMode.Arcade) and custom modes are left as they are.
// Boss and level code that names player two to pick or detect a player (src/target_sites.h) gets player two or P3 instead
// (p3_target_player); in cutscenes that move players one and two or set them inactive, P3 follows player one (p3_follow).
#include "mod.h"

// ---- game code (main offsets, from cuphead_1.3.7_dump.cs) ----
HIDDEN void *G_40ef80(void *, i32 id, void *);                 // PlayerManager.GetPlayer(PlayerId)
HIDDEN void G_42fb10(void *, i32 id, void *player, void *);    // PlayerManager.SetPlayer(PlayerId, AbstractPlayerController)
HIDDEN void G_143e390(void *dict, i32 key, void *value, void *method);   // Dictionary<int, TRef>.Add (shared code, method picks the instantiation)
HIDDEN u32 G_2bd8f0(void *player, void *);                     // AbstractPlayerController.get_IsDead
HIDDEN V3 G_2e0b70(void *player, void *);                      // AbstractPlayerController.get_center
HIDDEN V3 G_2e0df0(void *player, void *);                      // AbstractPlayerController.get_CameraCenter
HIDDEN void *G_2e0480(void *, i32 id, V2 pos, i32 mode, void *);   // AbstractPlayerController.Create(PlayerId, Vector2, PlayerMode)
HIDDEN void G_2e23d0(void *player, V3 pos, void *);            // AbstractPlayerController.LevelJoin(Vector3)
HIDDEN void G_942a90(void *player, i32 id, void *);            // LevelPlayerController.OnLeave(PlayerId)
HIDDEN void G_632600(void *player, i32 id, void *);            // PlanePlayerController.OnLeave(PlayerId)
HIDDEN void G_631e30(void *player, void *);                    // PlanePlayerController.PlayIntro
HIDDEN void *G_941240(void *player, void *);                   // LevelPlayerController.get_animationController
HIDDEN void *G_930b10(void *anim, void *);                     // LevelPlayerAnimationController.get_spriteRenderer
HIDDEN void *G_631700(void *player, void *);                   // PlanePlayerController.get_animationController
HIDDEN void *G_392a30(void *anim, void *);                     // PlanePlayerAnimationController.get_spriteRenderer
HIDDEN void G_1530b50(void *renderer, Color c, void *);        // SpriteRenderer.set_color
HIDDEN Color G_1530a60(void *renderer, void *);                // SpriteRenderer.get_color
HIDDEN void *G_217450(void *, void *);                         // Level.get_Current
HIDDEN u32 G_229360(void *, void *);                           // Level.get_IsTowerOfPowerMain
HIDDEN void *G_601c30(void *, void *);                         // CupheadInput.CheckForUnconnectedControllerPress
HIDDEN void G_bf5510(void *controllers, void *controller, u32 removeFromOthers, void *);   // Rewired.Player.ControllerHelper.AddController
HIDDEN i32 G_bf51d0(void *controllers, void *);                // ControllerHelper.get_joystickCount
HIDDEN void G_bf6740(void *controllers, i32 type, void *);     // ControllerHelper.ClearControllersOfType(ControllerType)
HIDDEN void *G_a620e0(void *, void *);                         // Rewired.ReInput.get_players
HIDDEN i32 G_c356e0(void *players, void *);                    // ReInput.PlayerHelper.get_playerCount
HIDDEN void *G_c35a00(void *players, i32 id, void *);          // ReInput.PlayerHelper.GetPlayer(int)
HIDDEN void G_8e6b30(void *, void *key, void *);               // AudioManager.Play(string)
HIDDEN u32 G_21c9f0(void *, void *);                           // InterruptingPrompt.IsInterrupting
HIDDEN u32 G_1634ab0(void *, void *);                          // SceneLoader.get_CurrentlyLoading
HIDDEN i32 G_116a470(void *, i32 min, i32 max, void *);        // UnityEngine.Random.Range(int, int)
HIDDEN void *G_241450(void *, void *);                         // LevelHUD.get_Current
HIDDEN void G_2418b0(void *card, void *player, u32 startAtOneHealth, void *);   // LevelHUDPlayer.Init
HIDDEN void *G_1166770(void *, void *original, void *);        // UnityEngine.Object.Instantiate(Object)
HIDDEN void G_11659e0(void *, void *obj, void *);              // UnityEngine.Object.Destroy(Object)
HIDDEN u32 G_1159210(void *, void *obj, void *);               // UnityEngine.Object.op_Implicit (alive, not destroyed)
HIDDEN void *G_1162f90(void *obj, void *);                     // UnityEngine.Object.get_name
HIDDEN void G_1165c50(void *obj, void *name, void *);          // UnityEngine.Object.set_name
HIDDEN void *G_114d1a0(void *component, void *);               // Component.get_gameObject
HIDDEN void *G_114d130(void *component, void *);               // Component.get_transform
HIDDEN void G_1156ae0(void *gameObject, u32 active, void *);   // GameObject.SetActive
HIDDEN u32 G_1156b50(void *gameObject, void *);                // GameObject.get_activeSelf
HIDDEN void *G_1538f80(void *transform, void *);               // Transform.get_parent
HIDDEN void G_1539260(void *transform, void *parent, u32 worldPositionStays, void *);   // Transform.SetParent
HIDDEN V3 G_1537bd0(void *transform, void *);                  // Transform.get_localPosition
HIDDEN void G_1537cc0(void *transform, V3 v, void *);          // Transform.set_localPosition
HIDDEN V3 G_15379c0(void *transform, void *);                  // Transform.get_position
HIDDEN void G_1537ad0(void *transform, V3 v, void *);          // Transform.set_position
HIDDEN V3 G_1537db0(void *transform, void *);                  // Transform.get_eulerAngles
HIDDEN void G_1537ed0(void *transform, V3 v, void *);          // Transform.set_eulerAngles
HIDDEN void G_15cab90(void *klass);                            // il2cpp: run a class's static constructor
HIDDEN void *G_15fc440(void *arrayClass, u64 length);          // il2cpp: new array
#ifdef P3_TEST
HIDDEN void *G_2bd9d0(void *player, void *);                   // AbstractPlayerController.get_stats
HIDDEN void G_1635280(void *, i32 level, i32 transition, i32 icon, void *context, void *);   // SceneLoader.LoadLevel
HIDDEN void G_422fc0(void *ghost, void *);                     // PlayerDeathEffect.OnParrySwitch
#endif
// metadata slots, filled before the methods that use them first run
HIDDEN extern void **G_38b8048;   // the PlayerManager class
HIDDEN extern void **G_38d0650;   // Dictionary<int, Rewired.Player>.Add (PlayerManager.Awake's)
HIDDEN extern void **G_38d0718;   // "player_spawn" (PlayerManager.Update's)
HIDDEN extern void **G_38d0728;   // "player_despawn" (PlayerManager.Update's)

enum { P1 = 0, P2 = 1, P3 = 2 };
enum { JOINED = 3 };                         // PlayerManager.PlayerSlot.JoinState.Joined
enum { MODE_LEVEL = 0, MODE_PLANE = 1 };     // PlayerMode (Arcade 2, Custom 10000000)
static const float FOLLOW_JUMP = 300.0f;     // player one moved this far in one frame: a cutscene moved it, P3 follows
enum { CONTROLLER_JOYSTICK = 2 };            // Rewired.ControllerType.Joystick
static const Color P3_TINT = {0.55f, 1.0f, 0.55f, 1.0f};
static const float HUD_P3_DX = 260.0f;       // P3's card: player one's moved right by this (HUD canvas units)

// PlayerManager's static fields
#define PM_SLOTS(s) AT(s, 0x00, RefArray *)
#define PM_MULTIPLAYER(s) AT(s, 0x08, u8)
#define PM_WAS_CHALICE(s) AT(s, 0x30, BoolArray *)
#define PM_INPUTS(s) AT(s, 0x38, void *)
#define PM_PLAYERS(s) AT(s, 0x40, void *)
#define PM_CURRENT(s) AT(s, 0x48, i32)
#define SLOT_CANJOIN(p) AT(p, 0x10, u8)
#define SLOT_JOINSTATE(p) AT(p, 0x14, i32)
// Level
#define LV_MODE(l) AT(l, 0x6c, i32)
#define LV_ALLOW_MP(l) AT(l, 0x70, u8)
#define LV_SPAWNS(l) AT(l, 0x80, void *)
#define LV_PLANE_SPAWN1(l) AT(l, 0xf8, V3)
#define LV_PLANE_SPAWN2(l) AT(l, 0x104, V3)
#define LV_PLAYERS(l) AT(l, 0xb0, RefArray *)
#define LV_PLAYERS_CREATED(l) AT(l, 0xce, u8)
#define LV_BLOCK_CHALICE(l) AT(l, 0xd8, BoolArray *)
#define LV_PLAYER_IS_DEAD(l) AT(l, 0x114, u8)
// LevelHUD
#define HUD_CUPHEAD(h) AT(h, 0x58, void *)
#define HUD_TEMPLATE(h) AT(h, 0x60, void *)
// Rewired
#define RW_CONTROLLERS(p) AT(p, 0x38, void *)

// The mod's state: the only writable data, at main+0x3b37000 (link_mod.py), so DM_CTL "peek" can read it. Not static, so that clang
// keeps it one struct in this layout
HIDDEN struct p3_state {
    u32 magic;     // 'P3MD' once PlayerManager.Awake ran
    u32 ready;     // PlayerManager has a player three entry and a Rewired player for it
    u32 joined;
    u32 error;     // 1: Rewired has fewer than 3 players (no PlayerThree in resources.assets), 2: GetPlayer(2) gave none
    u32 joins, leaves, spawns, cards;   // counters, for testing
    i32 joystick;  // Rewired id of P3's controller
    u32 tick;      // PlayerManager.Update calls
    void *input;   // Rewired.Player 2
    void *card;    // P3's LevelHUDPlayer in the current level
    void *tinted;  // the P3 object whose sprite has been tinted
    V3 lead_pos;   // +0x40: where the player P3 follows was last frame
    i32 lead;      // that player's id, -1: none
    u32 hidden;    // P3 was set inactive because the player it follows is
    u32 follows;   // counters: P3 moved to the player it follows, target picks that gave P3
    u32 targets;
    u32 _pad;
#ifdef P3_TEST
    i32 test_level;   // +0x60, test build (tools/build.sh test): a Levels value, loaded when test_go is set (DM_CTL poke)
    u32 test_go;
    i32 hp[3];        // +0x68: each player's PlayerStatsManager.Health, IsDead, object; the card's player and shown health
    u32 dead[3];
    void *pl[3];
    void *card_player;
    i32 card_hp;
    u32 frames;
    u32 god;          // +0xa8: bit n set: player n's health kept full; the players' damage multiplied by boost (when not 0)
    u32 boost;
    V3 pos[3];        // +0xb0: players' positions
    u32 stack;        // +0xd4: P3 kept where player one is (its ghost then rises above player one, who can parry it)
    u32 revive;       // +0xd8: set: P3's ghost is parried (PlayerDeathEffect.OnParrySwitch) as if a player had; revives counts them
    u32 revives;
    void *ghost;      // +0xe0: P3's last ghost
#endif
} st;
_Static_assert(__builtin_offsetof(struct p3_state, lead_pos) == 0x40 && __builtin_offsetof(struct p3_state, _pad) == 0x5c, "state layout");
#ifdef P3_TEST
_Static_assert(__builtin_offsetof(struct p3_state, test_level) == 0x60 && __builtin_offsetof(struct p3_state, pl) == 0x80 &&
               __builtin_offsetof(struct p3_state, god) == 0xa8 && __builtin_offsetof(struct p3_state, pos) == 0xb0 &&
               __builtin_offsetof(struct p3_state, stack) == 0xd4 && __builtin_offsetof(struct p3_state, ghost) == 0xe0, "test state layout");
#endif

static int exists(void *o) { return o && (G_1159210(0, o, 0) & 1); }

static void *pm(void) {
    void *k = *G_38b8048;
    if (!k) return 0;
    if ((AT(k, 0x10a, u8) & 1) && !AT(k, 0xbc, u32)) G_15cab90(k);   // has a static constructor that has not finished
    return AT(k, 0xa0, void *);
}

static void *player(int id) { return G_40ef80(0, id, 0); }
static int alive(int id) { void *p = player(id); return exists(p) && !(G_2bd8f0(p, 0) & 1); }
// P3 is in the current level
static int p3_present(void) { return st.ready && exists(player(P3)); }
// the alive players, ids in order
static int alive_list(int *ids) {
    void *s = pm(); int n = 0;
    for (int id = P1; id <= P3; id++) {
        if (id == P2 && !PM_MULTIPLAYER(s)) continue;
        if (alive(id)) ids[n++] = id;
    }
    return n;
}

// ---- PlayerManager ----
HIDDEN void o_PlayerManager_Awake(void *, void *);
HIDDEN void h_PlayerManager_Awake(void *u, void *m) {
    o_PlayerManager_Awake(u, m);
    st.magic = 0x444D3350; st.ready = 0; st.joined = 0; st.card = 0; st.input = 0;
    void *s = pm();
    if (!s || !PM_INPUTS(s) || !PM_PLAYERS(s)) return;
    void *rp = G_a620e0(0, 0);
    if (!rp) return;
    if (G_c356e0(rp, 0) < 3) { st.error = 1; return; }
    void *p3 = G_c35a00(rp, P3, 0);
    if (!p3) { st.error = 2; return; }
    G_143e390(PM_INPUTS(s), P3, p3, *G_38d0650);   // playerInputs.Add(2, ReInput.players.GetPlayer(2))
    G_42fb10(0, P3, 0, 0);                          // players[2] = null (the indexer adds the key)
    BoolArray *wc = PM_WAS_CHALICE(s);              // playerWasChalice: bool[2] -> bool[3] (indexed by player id)
    if (wc && wc->length < 3) {
        BoolArray *n = G_15fc440(wc->klass, 3);
        if (n) { n->v[0] = wc->v[0]; n->v[1] = wc->v[1]; PM_WAS_CHALICE(s) = n; }
    }
    st.input = p3; st.error = 0; st.ready = 1;
}
HOOK_ENTRY(PlayerManager_Awake, 0x427100, 0xa9bd57f6);

#define PC_MODE(p) AT(p, 0x84, i32)   // AbstractPlayerController.mode

// P3's sprite tinted, once per P3 object; a plane's sprite renderer is found in its Start, so this is tried each frame until done
static void p3_tint(void *p) {
    if (p == st.tinted) return;
    void *sr = 0;
    if (PC_MODE(p) == MODE_PLANE) { void *anim = G_631700(p, 0); sr = anim ? G_392a30(anim, 0) : 0; }
    else { void *anim = G_941240(p, 0); sr = anim ? G_930b10(anim, 0) : 0; }
    if (!exists(sr)) return;
    Color c = G_1530a60(sr, 0), t = P3_TINT;
    t.a = c.a;
    G_1530b50(sr, t, 0);
    st.tinted = p;
}

// AbstractPlayerController.Awake destroys every controller whose name contains "PlayerTwo" (a stale player two): player two is
// renamed while P3 is created
static void *p3_create(V2 pos, i32 mode) {
    void *p2 = player(P2), *name = 0;
    if (exists(p2)) { name = G_1162f90(p2, 0); G_1165c50(p2, *G_38d0718, 0); }
    void *p = G_2e0480(0, P3, pos, mode, 0);
    if (name) G_1165c50(p2, name, 0);
    if (p) { st.tinted = 0; st.hidden = 0; st.lead = -1; p3_tint(p); st.spawns++; }
    return p;
}

static void p3_card(void *p, u32 one_health) {
    void *hud = G_241450(0, 0);
    if (!exists(hud) || !exists(HUD_TEMPLATE(hud)) || !exists(HUD_CUPHEAD(hud))) return;
    void *c = G_1166770(0, HUD_TEMPLATE(hud), 0);   // the template is player one's card, inactive
    if (!c) return;
    G_1156ae0(G_114d1a0(c, 0), 1, 0);
    void *t = G_114d130(c, 0);
    G_1539260(t, G_1538f80(G_114d130(HUD_CUPHEAD(hud), 0), 0), 0, 0);
    G_2418b0(c, p, one_health, 0);
    V3 lp = G_1537bd0(t, 0); lp.x += HUD_P3_DX; G_1537cc0(t, lp, 0);
    st.card = c; st.cards++;
}

static int level_takes_p3(void *lv) {
    void *s = pm();
    return lv && PM_MULTIPLAYER(s) && LV_ALLOW_MP(lv) && (LV_MODE(lv) == MODE_LEVEL || LV_MODE(lv) == MODE_PLANE);
}

// P3 joining while a level runs (as Level.CreatePlayerTwoOnJoin does for player two)
static void p3_join_level(void) {
    void *lv = G_217450(0, 0);
    if (!exists(lv) || !LV_PLAYERS_CREATED(lv) || !level_takes_p3(lv)) return;
    RefArray *pl = LV_PLAYERS(lv);
    if (!pl || pl->length < 3 || exists(pl->v[P3]) || !exists(pl->v[P1])) return;
    V3 c = G_2e0b70(pl->v[P1], 0);
    void *p = p3_create((V2){c.x, c.y}, LV_MODE(lv));
    if (!p) return;
    pl->v[P3] = p;
    G_2e23d0(p, c, 0);
    p3_card(p, !(G_229360(0, 0) & 1));
}

static void p3_leave(int sound) {
    st.joined = 0; st.leaves++;
    if (st.input) G_bf6740(RW_CONTROLLERS(st.input), CONTROLLER_JOYSTICK, 0);
    void *p = player(P3);
    if (exists(p)) (PC_MODE(p) == MODE_PLANE ? G_632600 : G_942a90)(p, P3, 0);   // OnLeave: the exit puff, then Destroy
    G_42fb10(0, P3, 0, 0);
    void *lv = G_217450(0, 0);
    if (exists(lv)) {
        RefArray *pl = LV_PLAYERS(lv);
        if (pl && pl->length >= 3) pl->v[P3] = 0;
        LV_PLAYER_IS_DEAD(lv) = 1;   // Level.Update checks for game over again (P3 may have been the last one standing)
    }
    if (exists(st.card)) G_11659e0(0, G_114d1a0(st.card, 0), 0);
    st.card = 0;
    if (sound) G_8e6b30(0, *G_38d0728, 0);
}

static void p3_move_to(void *p, V3 pos) { G_1537ad0(G_114d130(p, 0), pos, 0); st.follows++; }

// Cutscenes and phase changes move players one and two, or set them inactive (swallowed, dropped down a pit), by name. P3 follows
// the first alive and active one of them (its lead): when the lead jumps further than a step in one frame, P3 is moved to it; when no
// alive player is active, P3 is set inactive too, and comes back where the lead is. On a tilting platform P3 is kept upright, as the
// platforms do for players one and two.
static void p3_follow(void) {
    void *lv = G_217450(0, 0), *p = player(P3);
    if (!exists(lv) || !LV_PLAYERS_CREATED(lv) || !exists(p) || (G_2bd8f0(p, 0) & 1)) { st.lead = -1; return; }
    p3_tint(p);
    int lead = -1, alive_any = 0;
    for (int id = P1; id <= P2 && lead < 0; id++) {
        if (!alive(id)) continue;
        alive_any = 1;
        if (G_1156b50(G_114d1a0(player(id), 0), 0) & 1) lead = id;
    }
    void *go = G_114d1a0(p, 0);
    if (lead < 0) {
        if (alive_any && (G_1156b50(go, 0) & 1)) { G_1156ae0(go, 0, 0); st.hidden = 1; }
        st.lead = -1;
        return;
    }
    V3 at = G_15379c0(G_114d130(player(lead), 0), 0);
    if (st.hidden) {
        st.hidden = 0;
        G_1156ae0(go, 1, 0);
        p3_move_to(p, at);
    } else if (lead == st.lead) {
        float dx = at.x - st.lead_pos.x, dy = at.y - st.lead_pos.y;
        if (dx * dx + dy * dy > FOLLOW_JUMP * FOLLOW_JUMP) p3_move_to(p, at);
    }
    st.lead = lead; st.lead_pos = at;
    void *t = G_114d130(p, 0);
    if (G_1538f80(t, 0)) {
        V3 e = G_1537db0(t, 0);
        if (e.z != 0.0f) { e.z = 0.0f; G_1537ed0(t, e, 0); }
    }
}

// Boss and level code that reads GetPlayer(PlayerTwo) to pick or detect a player (src/target_sites.h) gets P3 in place of player two
// on every other frame while both are alive, and P3 alone while player two is dead
HIDDEN void *p3_target_player(void *u, i32 id, void *m) {
    void *p = G_40ef80(u, id, m);
    if (id != P2 || !p3_present() || !alive(P3)) return p;
    if (alive(P2) && !(st.tick & 1)) return p;
    st.targets++;
    return player(P3);
}
#include "target_sites.h"

static void p3_update(void) {
    void *s = pm();
    RefArray *slots = s ? PM_SLOTS(s) : 0;
    if (!slots || slots->length < 2 || !slots->v[P2]) return;
    void *slot2 = slots->v[P2];
    int p2_in = SLOT_JOINSTATE(slot2) == JOINED;
    if (!st.joined) {
        if (!p2_in || !SLOT_CANJOIN(slot2)) return;
        if ((G_21c9f0(0, 0) & 1) || (G_1634ab0(0, 0) & 1)) return;   // a prompt is up, or a scene is loading
        void *joy = G_601c30(0, 0);   // a controller with a button down that no player has
        if (!joy) return;
        G_bf5510(RW_CONTROLLERS(st.input), joy, 1, 0);
        st.joined = 1; st.joins++; st.joystick = AT(joy, 0x10, i32);
        G_8e6b30(0, *G_38d0718, 0);
        p3_join_level();
    } else if (!p2_in || G_bf51d0(RW_CONTROLLERS(st.input), 0) == 0) {
        p3_leave(1);
    } else {
        p3_follow();
    }
}

HIDDEN void o_PlayerManager_Update(void *, void *);
HIDDEN void h_PlayerManager_Update(void *u, void *m) {
    o_PlayerManager_Update(u, m);
    st.tick++;
    if (st.ready) p3_update();
#ifdef P3_TEST
    if (st.test_go && !(G_1634ab0(0, 0) & 1)) { st.test_go = 0; G_1635280(0, st.test_level, 1, 6, 0, 0); }   // Fade, the hourglass icon
    st.frames++;
    if (st.ready) for (int id = P1; id <= P3; id++) {
        void *p = player(id); st.pl[id] = p;
        void *ps = exists(p) ? G_2bd9d0(p, 0) : 0;
        if (ps && (st.god >> id & 1) && !(G_2bd8f0(p, 0) & 1) && AT(ps, 0x74, i32) > 0) AT(ps, 0x74, i32) = AT(ps, 0x70, i32);
        st.hp[id] = ps ? AT(ps, 0x74, i32) : -1;
        st.dead[id] = exists(p) ? (G_2bd8f0(p, 0) & 1) : 9;
        st.pos[id] = exists(p) ? G_15379c0(G_114d130(p, 0), 0) : (V3){0, 0, 0};
    }
    if (st.stack && st.ready && alive(P1) && alive(P3)) G_1537ad0(G_114d130(player(P3), 0), st.pos[P1], 0);
    if (st.revive && st.dead[P3] == 1 && exists(st.ghost)) { st.revive = 0; st.revives++; G_422fc0(st.ghost, 0); }
    st.card_player = exists(st.card) ? AT(st.card, 0x90, void *) : 0;
    st.card_hp = exists(st.card) && AT(st.card, 0x60, void *) ? AT(AT(st.card, 0x60, void *), 0x68, i32) : -1;
#endif
}
HOOK_ENTRY(PlayerManager_Update, 0x428e60, 0xd102c3ff);

HIDDEN void o_PlayerManager_ClearPlayers(void *, void *);
HIDDEN void h_PlayerManager_ClearPlayers(void *u, void *m) {
    o_PlayerManager_ClearPlayers(u, m);
    if (st.ready) G_42fb10(0, P3, 0, 0);
    st.card = 0;
}
HOOK_ENTRY(PlayerManager_ClearPlayers, 0x42fc60, 0xf81d0ff5);

// back to the title screen or the save slots: everyone but player one is dropped
static void p3_drop(void) {
    if (st.joined && st.input) G_bf6740(RW_CONTROLLERS(st.input), CONTROLLER_JOYSTICK, 0);
    st.joined = 0; st.card = 0;
}
HIDDEN void o_PlayerManager_ResetPlayers(void *, void *);
HIDDEN void h_PlayerManager_ResetPlayers(void *u, void *m) { o_PlayerManager_ResetPlayers(u, m); p3_drop(); }
HOOK_ENTRY(PlayerManager_ResetPlayers, 0x42f610, 0xa9bc5ff8);
HIDDEN void o_PlayerManager_goToSlotSelect(void *, void *);
HIDDEN void h_PlayerManager_goToSlotSelect(void *u, void *m) { o_PlayerManager_goToSlotSelect(u, m); p3_drop(); }
HOOK_ENTRY(PlayerManager_goToSlotSelect, 0x42c900, 0xf81d0ff5);

// Target picking and the players' centre: the originals know players one and two; with P3 in the level these count all three
HIDDEN void *o_GetNext(void *, void *);
HIDDEN void *h_GetNext(void *u, void *m) {
    if (!p3_present()) return o_GetNext(u, m);
    int ids[3], n = alive_list(ids);
    if (!n) return player(P1);
    void *s = pm(); int cur = PM_CURRENT(s), k = 0;
    while (k < n && ids[k] < cur) k++;   // the current one, or the next alive after it
    if (k == n) k = 0;
    PM_CURRENT(s) = ids[(k + 1) % n];
    return player(ids[k]);
}
HOOK_ENTRY(GetNext, 0x411ad0, 0xa9be4ff4);

HIDDEN void *o_GetRandom(void *, void *);
HIDDEN void *h_GetRandom(void *u, void *m) {
    if (!p3_present()) return o_GetRandom(u, m);
    int ids[3], n = alive_list(ids);
    return player(n ? ids[G_116a470(0, 0, n, 0)] : P1);
}
HOOK_ENTRY(GetRandom, 0x42fd20, 0xf81d0ff5);

HIDDEN u32 o_BothPlayersActive(void *, void *);
HIDDEN u32 h_BothPlayersActive(void *u, void *m) {
    if (!p3_present()) return o_BothPlayersActive(u, m);
    int ids[3];
    return alive_list(ids) >= 2;
}
HOOK_ENTRY(BothPlayersActive, 0x430030, 0xf81e0ff3);

HIDDEN void *o_GetFirst(void *, void *);
HIDDEN void *h_GetFirst(void *u, void *m) {
    if (!p3_present()) return o_GetFirst(u, m);
    int ids[3];
    return alive_list(ids) ? player(ids[0]) : o_GetFirst(u, m);
}
HOOK_ENTRY(GetFirst, 0x4300d0, 0xf81e0ff3);

// the alive players' average centre, n > 0 (with nobody alive the originals answer)
static V2 average(const int *ids, int n, int camera) {
    V2 r = {0, 0};
    for (int i = 0; i < n; i++) { V3 c = (camera ? G_2e0df0 : G_2e0b70)(player(ids[i]), 0); r.x += c.x; r.y += c.y; }
    r.x /= (float)n; r.y /= (float)n;
    return r;
}
HIDDEN V2 o_get_Center(void *, void *);
HIDDEN V2 h_get_Center(void *u, void *m) {
    int ids[3], n;
    if (!p3_present() || !(n = alive_list(ids))) return o_get_Center(u, m);
    return average(ids, n, 0);
}
HOOK_ENTRY(get_Center, 0x430520, 0x6dba33ed);
HIDDEN V2 o_get_CameraCenter(void *, void *);
HIDDEN V2 h_get_CameraCenter(void *u, void *m) {
    int ids[3], n;
    if (!p3_present() || !(n = alive_list(ids))) return o_get_CameraCenter(u, m);
    return average(ids, n, 1);
}
HOOK_ENTRY(get_CameraCenter, 0x430790, 0x6dba33ed);

// x: the alive players' average, y: the highest
HIDDEN V2 o_get_TopPlayerPosition(void *, void *);
HIDDEN V2 h_get_TopPlayerPosition(void *u, void *m) {
    int ids[3], n;
    if (!p3_present() || !(n = alive_list(ids))) return o_get_TopPlayerPosition(u, m);
    V2 r = {0, -1e30f};
    for (int i = 0; i < n; i++) {
        V3 p = G_15379c0(G_114d130(player(ids[i]), 0), 0);
        r.x += p.x / (float)n; if (p.y > r.y) r.y = p.y;
    }
    return r;
}
HOOK_ENTRY(get_TopPlayerPosition, 0x430a00, 0xd10143ff);

// the players' damage is scaled so that a boss lasts as long: 1 alone, 1/2 for two (the game's), 1/3 for three
HIDDEN float o_get_DamageMultiplier(void *, void *);
HIDDEN float h_get_DamageMultiplier(void *u, void *m) {
#ifdef P3_TEST
    float boost = st.boost ? (float)st.boost : 1.0f;
#else
    const float boost = 1.0f;
#endif
    if (!p3_present()) return o_get_DamageMultiplier(u, m) * boost;
    int ids[3], n = alive_list(ids);
    return (n > 1 ? 1.0f / (float)n : 1.0f) * boost;
}
HOOK_ENTRY(get_DamageMultiplier, 0x430d50, 0xf81e0ff3);

// ---- Level ----
// Level.players and Level.BlockChaliceCharm are made with 3 entries (indexed by player id); P3 never becomes Ms. Chalice
HOOK_WORD(players_alloc, 0x22d258, 0x321f03e1, 0x52800061);         // mov w1, #2 -> #3
HOOK_WORD(block_chalice_alloc, 0x22d27c, 0x321f03e1, 0x52800061);   // mov w1, #2 -> #3

HIDDEN void o_Level_CreatePlayers(void *, void *);
HIDDEN void h_Level_CreatePlayers(void *lv, void *m) {
    o_Level_CreatePlayers(lv, m);
    BoolArray *bc = LV_BLOCK_CHALICE(lv);
    if (bc && bc->length >= 3) bc->v[P3] = 1;
    if (!st.ready || !st.joined || !level_takes_p3(lv)) return;
    RefArray *pl = LV_PLAYERS(lv);
    void *sp = LV_SPAWNS(lv);
    if (!pl || pl->length < 3 || !sp || !pl->v[P2]) return;
    V2 a = AT(sp, 0x10, V2), b = AT(sp, 0x18, V2);   // Level.Spawns.playerOne, playerTwo: P3 starts between them
    if (LV_MODE(lv) == MODE_PLANE) {
        V3 a3 = LV_PLANE_SPAWN1(lv), b3 = LV_PLANE_SPAWN2(lv);
        a = (V2){a3.x, a3.y}; b = (V2){b3.x, b3.y};
    }
    pl->v[P3] = p3_create((V2){(a.x + b.x) * 0.5f, (a.y + b.y) * 0.5f}, LV_MODE(lv));
}
HOOK_ENTRY(Level_CreatePlayers, 0x22d0b0, 0xfc1a0fea);

// Level.Update, game over in multiplayer: "if players[0].IsDead and players[1].IsDead: _OnLose()". At main+0x22c4d4 w0 is player
// two's IsDead and x19 the level; the stub goes on to _OnLose (main+0x22c518) only when P3 is gone or dead too, else to main+0x22c520
HIDDEN u32 p3_keeps_level_going(void *lv) {
    RefArray *pl = LV_PLAYERS(lv);
    if (!pl || pl->length < 3) return 0;
    void *p = pl->v[P3];
    return exists(p) && !(G_2bd8f0(p, 0) & 1);
}
HIDDEN void s_level_game_over(void);
__asm__(".p2align 2\n"
        "_s_level_game_over:\n"
        "  tbz w0, #0, 1f\n"
        "  mov x0, x19\n"
        "  bl _p3_keeps_level_going\n"
        "  cbnz w0, 1f\n"
        "  b _G_22c518\n"
        "1: b _G_22c520\n");
HOOK_BRANCH(level_game_over, 0x22c4d4, 0x37000220, s_level_game_over);

// The level plays each player's intro (Level.startBattle_cr, startNonBattle_cr: players[0] and players[1]); P3's plays with player
// two's. A plane shows its sprite only from its intro on (PlanePlayerAnimationController.LevelInit hides them all)
HIDDEN void o_PlayIntro(void *, void *);
HIDDEN void h_PlayIntro(void *p, void *m) {
    o_PlayIntro(p, m);
    if (AT(p, 0x80, i32) != P2 || !p3_present()) return;   // AbstractPlayerController.id
    void *p3 = player(P3);
    if (PC_MODE(p3) == MODE_PLANE) G_631e30(p3, 0); else o_PlayIntro(p3, 0);
}
HOOK_ENTRY(PlayIntro, 0x2e1570, 0xf9404c00);   // AbstractPlayerController.PlayIntro (PlanePlayerController's calls it first)

// P3's ghost: PlayerDeathEffect.Init shows Cuphead's ghost for every id but player two's; P3's shows Mugman's, tinted
#define DE_CUPHEAD(e) AT(e, 0x50, void *)
#define DE_MUGMAN(e) AT(e, 0x58, void *)
#define DE_ID(e) AT(e, 0x88, i32)
#define DE_SPRITE(e) AT(e, 0x90, void *)
HIDDEN void o_DeathEffect_Init(void *, i32, void *, V2, i32, i32, u32, void *);
HIDDEN void h_DeathEffect_Init(void *e, i32 id, void *input, V2 pos, i32 deaths, i32 mode, u32 can_parry, void *m) {
    o_DeathEffect_Init(e, id, input, pos, deaths, mode, can_parry, m);
    if (DE_ID(e) != P3 || !exists(DE_MUGMAN(e))) return;
#ifdef P3_TEST
    st.ghost = e;
#endif
    if (DE_SPRITE(e) == DE_CUPHEAD(e)) {
        G_1156ae0(G_114d1a0(DE_CUPHEAD(e), 0), 0, 0);
        G_1156ae0(G_114d1a0(DE_MUGMAN(e), 0), 1, 0);
        DE_SPRITE(e) = DE_MUGMAN(e);
    }
    Color c = G_1530a60(DE_SPRITE(e), 0), t = P3_TINT;
    t.a = c.a;
    G_1530b50(DE_SPRITE(e), t, 0);
}
HOOK_ENTRY(DeathEffect_Init, 0x421aa0, 0xfc190fea);

// ---- HUD ----
HIDDEN void o_LevelHUD_LevelInit(void *, void *);
HIDDEN void h_LevelHUD_LevelInit(void *hud, void *m) {
    o_LevelHUD_LevelInit(hud, m);
    st.card = 0;
    if (p3_present()) p3_card(player(P3), 0);
}
HOOK_ENTRY(LevelHUD_LevelInit, 0x22b3a0, 0xa9bc5ff8);

// ---- rumble ----
// Vibrator keeps a vibration amount and time per player id (Vibrator._Vibrate indexes them with the id): made with 3 entries. With 2,
// P3's first hit threw out of PlayerStatsManager.TakeDamage before OnStatsDeath, so P3 never died (no ghost, no game over check)
HOOK_WORD(vibrator_durations, 0x7472ec, 0x321f03e1, 0x52800061);   // Vibrator..ctor: durationsLeft = new float[2] -> [3]
HOOK_WORD(vibrator_current, 0x747308, 0x321f03e1, 0x52800061);     // currentVibrations = new float[2] -> [3]

// ---- player two's save data for P3 ----
// PlayerData.PlayerLoadouts.GetPlayerLoadout: id 0 -> playerOne, 1 -> playerTwo, else null; any id > 0 now gets playerTwo
HOOK_WORD(loadout, 0x421828, 0x350000e1, 0x35000081);        // cbnz w1, null -> cbnz w1, playerTwo
// the same lookup inlined in PlayerStatsManager.LevelInit
HOOK_WORD(loadout_inline, 0x4339a0, 0x54000161, 0xd503201f);  // cmp w20, #1; b.ne null -> nop
