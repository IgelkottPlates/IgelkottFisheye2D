#!/usr/bin/env bash
# Bygg IgelkottLiveFXFisheye.app och lägg den i _applaunchers som .app.zip (IgelkottSuit visar "Uppdatering finns").
set -euo pipefail
APP_NAME="IgelkottLiveFXFisheye"
SRC_ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${IGELKOTT_BUILD_PATH:-$HOME/Library/Caches/Igelkott/$APP_NAME}"
APP_DIR="$BUILD_DIR/$APP_NAME.app"
"$SRC_ROOT/build-app.sh"
[[ -d "$APP_DIR" ]] || { echo "FEL: $APP_DIR saknas"; exit 1; }
DEST=""
for root in "$HOME/Library/CloudStorage/"SynologyDrive-*"/Igelkott Appar/_applaunchers"; do
    [[ -d "$root" ]] && DEST="$root" && break
done
[[ -n "$DEST" ]] || DEST="$(cd "$SRC_ROOT/.." && pwd)/_applaunchers"
[[ -d "$DEST" ]] || { echo "FEL: hittar inte _applaunchers/"; exit 1; }
echo "==> Zippar och deployar till $DEST"
TMPZIP="$DEST/.$APP_NAME.app.zip.tmp.$$"
rm -f "$TMPZIP"
ditto -c -k --sequesterRsrc --keepParent "$APP_DIR" "$TMPZIP"
mv -f "$TMPZIP" "$DEST/$APP_NAME.app.zip"
echo "==> Klart: $DEST/$APP_NAME.app.zip"
echo "    IgelkottSuit visar 'Uppdatering finns' när Drive Client har synkat. Efter installation: Suit startar appen"
echo "    (den lägger noden i Live FX:s Matchbox-mapp) — starta sedan om Live FX."
