#!/bin/bash
# Builds IgelkottFisheye.plugin for After Effects (Mac, universal: Apple Silicon and Intel) from ae/ (Rust, the after-effects crate) and
# the kernel in resolve/IgelkottFisheye.fuse (see ae/build.rs). The build goes to ~/Library/Caches (no build output in
# the project folder). Signed with the first "Apple Development" identity, or ad hoc: After Effects 25.2 and later do not
# load an unsigned plugin.
#
#   ae/build-plugin.sh            -> <cache>/IgelkottFisheye.plugin
#   ae/build-plugin.sh --install  -> also copies it to /Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
export PATH="$HOME/.cargo/bin:$PATH"
export CARGO_TARGET_DIR="${IGELKOTT_AE_TARGET:-$HOME/Library/Caches/Igelkott/IgelkottLiveFXFisheye/ae-target}"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
NAME=IgelkottFisheye
python3 "$ROOT/tools/build_shaders.py" --check >/dev/null || { echo "Run python3 tools/build_shaders.py first"; exit 1; }
rustup target add aarch64-apple-darwin x86_64-apple-darwin >/dev/null
for T in aarch64-apple-darwin x86_64-apple-darwin; do (cd "$HERE" && cargo build --release --target $T); done
mkdir -p "$CARGO_TARGET_DIR/release"
B="$CARGO_TARGET_DIR/release/$NAME.plugin"
rm -rf "$B"
mkdir -p "$B/Contents/MacOS" "$B/Contents/Resources"
lipo -create "$CARGO_TARGET_DIR"/{aarch64,x86_64}-apple-darwin/release/libigelkottfisheye.dylib -output "$B/Contents/MacOS/$NAME"
cp "$CARGO_TARGET_DIR/aarch64-apple-darwin/release/build/igelkottfisheye.rsrc" "$B/Contents/Resources/$NAME.rsrc"
printf 'eFKTFXTC' > "$B/Contents/PkgInfo"
cat > "$B/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key><string>English</string>
    <key>CFBundleExecutable</key><string>$NAME</string>
    <key>CFBundleIdentifier</key><string>se.igelkottfilm.aftereffects.$NAME</string>
    <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
    <key>CFBundleName</key><string>$NAME</string>
    <key>CFBundlePackageType</key><string>eFKT</string>
    <key>CFBundleSignature</key><string>FXTC</string>
    <key>CFBundleShortVersionString</key><string>$VERSION</string>
    <key>CFBundleVersion</key><string>$(date +%Y%m%d%H%M)</string>
    <key>NSHumanReadableCopyright</key><string>Igelkott Film AB, https://igelkottplates.com</string>
</dict>
</plist>
PLIST
CERT="$(security find-identity -v -p codesigning | grep -m1 'Apple Development' | awk '{print $2}' || true)"
codesign --force --options runtime --timestamp=none --sign "${CERT:--}" "$B"
codesign --verify --strict "$B"
echo "Built $B ($VERSION, signed ${CERT:+with Apple Development}${CERT:-ad hoc})"
if [ "${1:-}" = "--install" ]; then
    DEST="/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
    /usr/bin/osascript -e "do shell script \"rm -rf '$DEST/$NAME.plugin' && cp -R '$B' '$DEST/'\" with administrator privileges"
    echo "Installed in $DEST: restart After Effects"
fi
