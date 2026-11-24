#!/usr/bin/env bash
# Build IgelkottLiveFXFisheye.app and put it in _applaunchers as .app.zip (IgelkottSuit then shows an update).
set -euo pipefail
APP_NAME="IgelkottLiveFXFisheye"
SRC_ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${IGELKOTT_BUILD_PATH:-$HOME/Library/Caches/Igelkott/$APP_NAME}"
APP_DIR="$BUILD_DIR/$APP_NAME.app"
"$SRC_ROOT/build-app.sh"
[[ -d "$APP_DIR" ]] || { echo "ERROR: $APP_DIR is missing"; exit 1; }
DEST=""
for root in "$HOME/Library/CloudStorage/"SynologyDrive-*"/Igelkott Appar/_applaunchers"; do
    [[ -d "$root" ]] && DEST="$root" && break
done
[[ -n "$DEST" ]] || DEST="$(cd "$SRC_ROOT/.." && pwd)/_applaunchers"
[[ -d "$DEST" ]] || { echo "ERROR: cannot find _applaunchers/"; exit 1; }
echo "==> Zipping and deploying to $DEST"
TMPZIP="$DEST/.$APP_NAME.app.zip.tmp.$$"
rm -f "$TMPZIP"
ditto -c -k --sequesterRsrc --keepParent "$APP_DIR" "$TMPZIP"
mv -f "$TMPZIP" "$DEST/$APP_NAME.app.zip"
echo "==> Done: $DEST/$APP_NAME.app.zip"
echo "    IgelkottSuit shows the update once Drive Client has synced. After installing, Suit starts the app"
echo "    (it puts the node in Live FX's Matchbox folder) — then restart Live FX."
