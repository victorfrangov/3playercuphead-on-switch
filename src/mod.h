// Cuphead 1.3.7 (Switch 0100A5C00D162000) IL2CPP layouts and the hook table read by tools/link_mod.py.
// Game code is reached by name: an undefined G_<hex> is main+<hex> (link_mod.py). IL2CPP passes a static method an unused first
// argument (0) and every method a trailing MethodInfo* (0 is fine for non-generic code).
#pragma once
#include <stdint.h>

typedef uint8_t u8;
typedef uint32_t u32;
typedef int32_t i32;
typedef uint64_t u64;
typedef struct { float x, y; } V2;
typedef struct { float x, y, z; } V3;
typedef struct { float r, g, b, a; } Color;

#define HIDDEN __attribute__((visibility("hidden")))
#define AT(p, off, type) (*(type *)((u8 *)(p) + (off)))

// IL2CPP arrays: length at +0x18, elements from +0x20
typedef struct { void *klass, *monitor, *bounds; u64 length; void *v[]; } RefArray;
typedef struct { void *klass, *monitor, *bounds; u64 length; u8 v[]; } BoolArray;

// The hook table: kind 0 = function entry hooked by h_<name> (the moved instruction and a branch back are o_<name>),
// 1 = instruction word replaced by `word`, 2 = the site branches to `target` (a stub that branches back itself), 3 = the bl at the site
// calls `target` instead
struct hook { u64 site; u32 expect; u32 kind; const void *target; };
#define HOOK_SECTION __attribute__((used, section("__HOOKS,__hooks")))
#define HOOK_ENTRY(name, site, expect) HOOK_SECTION static const struct hook hk_##name = {site, expect, 0, (const void *)h_##name}
#define HOOK_WORD(tag, site, expect, word) HOOK_SECTION static const struct hook hk_##tag = {site, expect, 1, (const void *)(u64)(word)}
#define HOOK_BRANCH(tag, site, expect, stub) HOOK_SECTION static const struct hook hk_##tag = {site, expect, 2, (const void *)stub}
#define HOOK_CALL(tag, site, expect, fn) HOOK_SECTION static const struct hook hk_##tag = {site, expect, 3, (const void *)fn}
