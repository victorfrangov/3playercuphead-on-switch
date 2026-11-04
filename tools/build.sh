#!/bin/zsh
# Builds the 3-player module: src/mod.c compiled freestanding for arm64 and linked into the app's module as it was before the mod
# (BASE, default backup/main.patched.bin.before_3player, which tools/install.sh keeps).
# Usage: tools/build.sh [test]   -> build/main.patched.bin, or with "test" build/main.patched.test.bin (P3_TEST: DM_CTL poke can load a level)
set -euo pipefail
D=${0:A:h:h}; BASE=${BASE:-$D/backup/main.patched.bin.before_3player}
DEFS=(); OUT=$D/build/main.patched.bin
if [[ ${1:-} == test ]]; then DEFS=(-DP3_TEST); OUT=$D/build/main.patched.test.bin; fi
mkdir -p $D/build
clang -target arm64-apple-macos14 -O2 -std=c11 -Wall -Wextra -Wno-unused-parameter -Werror $DEFS \
  -ffreestanding -fno-builtin -nostdlib -fno-stack-protector -fno-unwind-tables -fno-asynchronous-unwind-tables -fno-exceptions \
  -fno-jump-tables -fno-common -mno-outline-atomics -fno-zero-initialized-in-bss \
  -c $D/src/mod.c -o $D/build/mod${DEFS:+.test}.o
python3 $D/tools/link_mod.py $D/build/mod${DEFS:+.test}.o $BASE $OUT
