#!/usr/bin/env bash
# Bygg IgelkottLiveFXFisheye.app — en skript-app som bär Matchbox-noden IgelkottFisheye2D och installerar den i Live FX.
#
# Usage:
#   ./build-app.sh            # provet (tools/verify_mac.py) och sedan <byggkatalog>/IgelkottLiveFXFisheye.app
#   ./build-app.sh --open
set -euo pipefail
OPEN_AFTER=0
for arg in "$@"; do
    case "$arg" in
        --open) OPEN_AFTER=1 ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done
APP_NAME="IgelkottLiveFXFisheye"
BUNDLE_ID="se.igelkottstudios.igelkottlivefxfisheye"
SRC_ROOT="$(cd "$(dirname "$0")" && pwd)"
# Byggkatalogen ligger utanför den Drive-synkade mappen (husets regel).
BUILD_DIR="${IGELKOTT_BUILD_PATH:-$HOME/Library/Caches/Igelkott/$APP_NAME}"
APP_DIR="$BUILD_DIR/$APP_NAME.app"
VERSION="$(cat "$SRC_ROOT/VERSION" 2>/dev/null || echo 0.1)"
BUILD_NUMBER="$(date +%Y%m%d%H%M)"

# Shadern måste stämma med IgelkottStage innan den levereras
echo "==> Provet: shadern mot IgelkottStages räkning"
# verify_mac.py kör verify_windows.py:s fall med CGL (Live FX-utgåvan; PIXERA provas bara på Windows, GLSL 4.50)
(cd "$SRC_ROOT" && python3 tools/verify_mac.py . | grep -E "PASS|FAIL|All cases|differ|PIXERA|verify_mac"; exit "${PIPESTATUS[0]}") \
    || { echo "FEL: provet gick inte igenom"; exit 1; }
xmllint --noout "$SRC_ROOT/matchbox/IgelkottFisheye2D.xml"
echo "==> Provet: Direction Lock mot 2025-filerna"
(cd "$SRC_ROOT" && swift tools/directionlock.swift --test tools/fixtures 2>/dev/null) || { echo "FEL: Direction Lock-provet gick inte igenom"; exit 1; }


echo "==> Provet: Auto Stabilize mot en känd pan"
AUTOYAW_BIN="$BUILD_DIR/autoyaw-build/release/autoyaw"
mkdir -p "$BUILD_DIR"
# Paketet beror på _shared/IgelkottFisheyeLens (linsmodellen och läsaren av Darkroms hörnmärke); byggs utanför Drive
swift build -c release --package-path "$SRC_ROOT/tools/autoyaw" --build-path "$BUILD_DIR/autoyaw-build" >/dev/null 2>&1 \
    || { echo "FEL: tools/autoyaw går inte att bygga"; exit 1; }
"$AUTOYAW_BIN" --selftest || { echo "FEL: Auto Stabilize-provet gick inte igenom"; exit 1; }

echo "==> Provet: Stabilizer-sidan mot en känd pan"
command -v node >/dev/null || { echo "FEL: node saknas (behövs för tools/test-stabilizer.mjs)"; exit 1; }
(cd "$SRC_ROOT" && node tools/test-stabilizer.mjs) || { echo "FEL: Stabilizer-provet gick inte igenom"; exit 1; }

echo "==> Bygger .app-bundle ($VERSION, build $BUILD_NUMBER)"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources/Matchbox"
cp "$SRC_ROOT/app/$APP_NAME.sh" "$APP_DIR/Contents/MacOS/$APP_NAME"
chmod +x "$APP_DIR/Contents/MacOS/$APP_NAME"
swiftc -O "$SRC_ROOT/tools/directionlock.swift" -o "$APP_DIR/Contents/MacOS/directionlock" 2>/dev/null
cp "$AUTOYAW_BIN" "$APP_DIR/Contents/MacOS/autoyaw"
cp "$SRC_ROOT/matchbox/IgelkottFisheye2D.glsl" "$SRC_ROOT/matchbox/IgelkottFisheye2D.xml" "$APP_DIR/Contents/Resources/Matchbox/"
cat > "$APP_DIR/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>$APP_NAME</string>
    <key>CFBundleIdentifier</key><string>$BUNDLE_ID</string>
    <key>CFBundleName</key><string>$APP_NAME</string>
    <key>CFBundleDisplayName</key><string>Igelkott Live FX Fisheye</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>$VERSION</string>
    <key>CFBundleVersion</key><string>$BUILD_NUMBER</string>
    <key>LSMinimumSystemVersion</key><string>12.0</string>
    <key>LSUIElement</key><true/>
</dict>
</plist>
PLIST
xattr -cr "$APP_DIR" || true
echo "==> Klart: $APP_DIR"
[[ $OPEN_AFTER -eq 1 ]] && open "$APP_DIR"
exit 0
