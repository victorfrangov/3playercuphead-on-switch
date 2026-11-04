#!/bin/zsh
# Removes the 3-player mod: puts back the module, the overlay's resources.assets and env.txt that tools/install.sh kept in
# backup/, then re-signs the app and drops those backups.
# Usage: tools/uninstall.sh [/path/to/0100A5C00D162000.app]   (default: the app the last install went to)
set -euo pipefail
D=${0:A:h:h}; B=$D/backup
APP=${1:-$(cat $B/app_path 2>/dev/null || true)}; [ -n "$APP" ] || { echo 'usage: tools/uninstall.sh /path/to/0100A5C00D162000.app'; exit 1; }
APP=${APP:A}; DM=$APP/Contents/Resources/dm; ENV=$DM/env.txt
[ -e $B/main.patched.bin.before_3player ] || { echo "no backup of the module in $B: nothing to undo"; exit 1; }
if pgrep -qx dmhost; then echo 'Cuphead is running: quit it first'; exit 1; fi
OV=$( [ -f $ENV ] && sed -n 's/^DM_ROMFS_OVERLAY=//p' $ENV | tail -1 || true ); R=${OV:+$OV/Data/resources.assets}

cp $B/main.patched.bin.before_3player $DM/main.patched.bin
if [ -e $B/resources.assets.before_3player ]; then cp -p $B/resources.assets.before_3player $R
elif [ -n "$R" ] && [ -f $R ]; then rm $R; fi
if [ -e $B/env.txt.before_3player ]; then cp -p $B/env.txt.before_3player $ENV
elif [ -e $B/env.txt.none ]; then rm -f $ENV; fi
codesign --force --sign - $APP
codesign --verify --deep --strict $APP
# The next install starts from the app as it is then.
rm -f $B/main.patched.bin.before_3player $B/resources.assets.before_3player $B/resources.assets.from_romfs $B/env.txt.before_3player \
  $B/env.txt.none $B/app_path
echo "3-player mod removed: $APP"
