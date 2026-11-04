#!/bin/zsh
# Installs the 3-player mod into an NX2Apple Cuphead app: the module (built on the app's own) and PlayerThree in the RomFS
# overlay's resources.assets. tools/uninstall.sh undoes it.
# Usage: tools/install.sh /path/to/0100A5C00D162000.app    (PY=<python with UnityPy>, default python3)
#
# The first install keeps what it replaces in backup/: the app's module, the overlay's resources.assets (or a note that there
# was none) and env.txt. Later installs (after changing src/) build on those again.
# The overlay is the folder DM_ROMFS_OVERLAY in the app's env.txt points to. Without one, the mod's romfs/ folder becomes the
# overlay, and resources.assets is taken from the app's romfs.img.
set -euo pipefail
D=${0:A:h:h}; APP=${1:?usage: tools/install.sh /path/to/0100A5C00D162000.app}; APP=${APP:A}
DM=$APP/Contents/Resources/dm; ENV=$DM/env.txt; B=$D/backup
PY=${PY:-python3}   # needs UnityPy
[ -f $DM/main.patched.bin ] && [ -f $APP/Contents/Resources/romfs.img ] || { echo "not an NX2Apple app: $APP"; exit 1; }
if pgrep -qx dmhost; then echo 'Cuphead is running: quit it first'; exit 1; fi
mkdir -p $B $D/build

# The module: the first time, the app's own is the base (the link checks every patched instruction, so a module that already
# has the mod, or a different build, fails here and is not kept).
if [ ! -e $B/main.patched.bin.before_3player ]; then
  cp $DM/main.patched.bin $B/main.patched.bin.new_base
  if ! BASE=$B/main.patched.bin.new_base $D/tools/build.sh; then
    rm -f $B/main.patched.bin.new_base; echo "the app's module isn't the one this mod expects (is the mod already installed? is it Cuphead 1.3.7?)"; exit 1
  fi
  mv $B/main.patched.bin.new_base $B/main.patched.bin.before_3player
else
  $D/tools/build.sh
fi

# The overlay folder, from env.txt or the mod's romfs/ (then added to env.txt).
OV=$( [ -f $ENV ] && sed -n 's/^DM_ROMFS_OVERLAY=//p' $ENV | tail -1 || true )
if [ -z "$OV" ]; then
  OV=$D/romfs
  if [ ! -e $B/env.txt.before_3player ] && [ ! -e $B/env.txt.none ]; then
    if [ -f $ENV ]; then cp -p $ENV $B/env.txt.before_3player; else : > $B/env.txt.none; fi
  fi
  if [ -s $ENV ] && [ -n "$(tail -c 1 $ENV)" ]; then echo >> $ENV; fi
  echo "DM_ROMFS_OVERLAY=$OV" >> $ENV
fi
R=$OV/Data/resources.assets; mkdir -p $OV/Data

# resources.assets: the overlay's (e.g. another mod's), or the game's own from romfs.img.
if [ ! -e $B/resources.assets.before_3player ] && [ ! -e $B/resources.assets.from_romfs ]; then
  if [ -f $R ]; then cp -p $R $B/resources.assets.before_3player
  else $PY -I $D/tools/romfs_extract.py $APP/Contents/Resources/romfs.img /Data/resources.assets $B/resources.assets.from_romfs; fi
fi
SRC=$B/resources.assets.before_3player; [ -e $SRC ] || SRC=$B/resources.assets.from_romfs
$PY -I $D/tools/rewired_p3.py $SRC $D/build/resources.assets

cp $D/build/main.patched.bin $DM/main.patched.bin
cp $D/build/resources.assets $R
echo $APP > $B/app_path
codesign --force --sign - $APP
codesign --verify --deep --strict $APP
cmp $D/build/main.patched.bin $DM/main.patched.bin
echo "installed: $APP"
