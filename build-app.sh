#!/usr/bin/env bash
# Build IgelkottLiveFXFisheye.app — a script app that carries the Matchbox node IgelkottFisheye2D and installs it in Live FX.
#
# Usage:
#   ./build-app.sh            # the test (tools/verify_mac.py), then <build dir>/IgelkottLiveFXFisheye.app
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
# The build dir is outside the Drive-synced folder (house rule).
BUILD_DIR="${IGELKOTT_BUILD_PATH:-$HOME/Library/Caches/Igelkott/$APP_NAME}"
APP_DIR="$BUILD_DIR/$APP_NAME.app"
VERSION="$(cat "$SRC_ROOT/VERSION" 2>/dev/null || echo 0.1)"
BUILD_NUMBER="$(date +%Y%m%d%H%M)"

# The shader must match IgelkottStage before it ships
echo "==> Test: the shader against IgelkottStage's math"
# verify_mac.py runs verify_windows.py's cases with CGL (the Live FX edition; PIXERA is tested only on Windows, GLSL 4.50)
(cd "$SRC_ROOT" && python3 tools/verify_mac.py . | grep -E "PASS|FAIL|All cases|differ|PIXERA|verify_mac"; exit "${PIPESTATUS[0]}") \
    || { echo "ERROR: the test failed"; exit 1; }
xmllint --noout "$SRC_ROOT/matchbox/IgelkottFisheye2D.xml"
echo "==> Test: Direction Lock against the 2025 files"
(cd "$SRC_ROOT" && swift tools/directionlock.swift --test tools/fixtures 2>/dev/null) || { echo "ERROR: the Direction Lock test failed"; exit 1; }


echo "==> Test: Auto Stabilize against a known pan"
AUTOYAW_BIN="$BUILD_DIR/autoyaw-build/release/autoyaw"
mkdir -p "$BUILD_DIR"
# The package depends on _shared/IgelkottFisheyeLens (the lens model and the reader of Darkroom's corner mark); built outside Drive
swift build -c release --package-path "$SRC_ROOT/tools/autoyaw" --build-path "$BUILD_DIR/autoyaw-build" >/dev/null 2>&1 \
    || { echo "ERROR: tools/autoyaw does not build"; exit 1; }
"$AUTOYAW_BIN" --selftest || { echo "ERROR: the Auto Stabilize test failed"; exit 1; }

echo "==> Test: the Stabilizer page against a known pan"
command -v node >/dev/null || { echo "ERROR: node is missing (needed for tools/test-stabilizer.mjs)"; exit 1; }
(cd "$SRC_ROOT" && node tools/test-stabilizer.mjs) || { echo "ERROR: the Stabilizer test failed"; exit 1; }

echo "==> Building the .app bundle ($VERSION, build $BUILD_NUMBER)"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources/Matchbox" "$APP_DIR/Contents/Resources/Resolve"
cp "$SRC_ROOT/app/$APP_NAME.sh" "$APP_DIR/Contents/MacOS/$APP_NAME"
chmod +x "$APP_DIR/Contents/MacOS/$APP_NAME"
swiftc -O "$SRC_ROOT/tools/directionlock.swift" -o "$APP_DIR/Contents/MacOS/directionlock" 2>/dev/null
cp "$AUTOYAW_BIN" "$APP_DIR/Contents/MacOS/autoyaw"
cp "$SRC_ROOT/matchbox/IgelkottFisheye2D.glsl" "$SRC_ROOT/matchbox/IgelkottFisheye2D.xml" "$APP_DIR/Contents/Resources/Matchbox/"
cp "$SRC_ROOT/resolve/IgelkottFisheye.fuse" "$APP_DIR/Contents/Resources/Resolve/"
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
echo "==> Done: $APP_DIR"
[[ $OPEN_AFTER -eq 1 ]] && open "$APP_DIR"
exit 0
