#!/bin/bash
# Igelkott Live FX Fisheye — installs / updates the Matchbox node IgelkottFisheye2D in Live FX.
# Runs as the main program of IgelkottLiveFXFisheye.app (installed in /Applications by IgelkottSuit).
# The shader sits in the app's Resources/Matchbox and is copied to Live FX's Matchbox folder, which Live FX reads at
# launch (Settings/Junxion.xml lists the modules from there).
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HERE/Resources/Matchbox"
VER="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$HERE/Info.plist" 2>/dev/null)"
BUILD="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$HERE/Info.plist" 2>/dev/null)"
FILES=(IgelkottFisheye2D.glsl IgelkottFisheye2D.xml)

# IGELKOTT_NO_DIALOG=1 writes the report to stdout instead of a dialog (for tests / scripts);
# IGELKOTT_MATCHBOX_DIR redirects the target (the test)
say_dialog() { if [ -n "$IGELKOTT_NO_DIALOG" ]; then printf "%b\n" "$1"; return; fi; /usr/bin/osascript -e "display dialog \"$1\" with title \"Igelkott Live FX Fisheye $VER\" buttons {\"OK\"} default button 1 with icon $2" >/dev/null 2>&1; }

for f in "${FILES[@]}"; do
    [ -f "$SRC/$f" ] || { say_dialog "Cannot find $f in the app ($SRC). Reinstall the app from IgelkottSuit." stop; exit 1; }
done

DEST="${IGELKOTT_MATCHBOX_DIR:-/Library/Application Support/Assimilator/Plugins/Matchbox/shaders}"
if [ -z "$IGELKOTT_MATCHBOX_DIR" ] && [ ! -d "/Library/Application Support/Assimilator" ]; then
    say_dialog "Cannot find Live FX (/Library/Application Support/Assimilator). Is Live FX installed, and has it been started at least once?" stop; exit 1
fi
N=0
for f in "${FILES[@]}"; do cmp -s "$SRC/$f" "$DEST/$f" 2>/dev/null || N=$((N+1)); done
if [ $N -gt 0 ]; then
    if mkdir -p "$DEST" 2>/dev/null && cp "${FILES[@]/#/$SRC/}" "$DEST/" 2>/dev/null; then :; else
        # The Matchbox folder is not writable for the user: ask for administrator rights once
        /usr/bin/osascript -e "do shell script \"mkdir -p '$DEST' && cp '$SRC'/IgelkottFisheye2D.* '$DEST/' && chmod a+r '$DEST'/IgelkottFisheye2D.*\" with administrator privileges" >/dev/null 2>&1 \
            || { say_dialog "Could not write to $DEST." stop; exit 1; }
    fi
    /usr/bin/xattr -d com.apple.quarantine "$DEST"/IgelkottFisheye2D.* 2>/dev/null
    REPORT="✓ IgelkottFisheye2D updated in $DEST"
    NEXT="Restart Live FX. The node is then under Matchbox → shaders → IgelkottFisheye2D."
else
    REPORT="✓ Already up to date in $DEST"
    NEXT="Nothing to do."
fi
# DaVinci Resolve (0.23): the same effect as a Fuse, copied to the user's Fuses folder when Resolve is installed
RV_REPORT=""
RV_ROOT="${IGELKOTT_RESOLVE_DIR:-$HOME/Library/Application Support/Blackmagic Design/DaVinci Resolve}"
if [ -f "$HERE/Resources/Resolve/IgelkottFisheye.fuse" ] && [ -d "$RV_ROOT" ]; then
    RV_DEST="$RV_ROOT/Fusion/Fuses"
    if cmp -s "$HERE/Resources/Resolve/IgelkottFisheye.fuse" "$RV_DEST/IgelkottFisheye.fuse" 2>/dev/null; then
        RV_REPORT="\n✓ Resolve: IgelkottFisheye.fuse already up to date"
    elif mkdir -p "$RV_DEST" && cp "$HERE/Resources/Resolve/IgelkottFisheye.fuse" "$RV_DEST/"; then
        /usr/bin/xattr -d com.apple.quarantine "$RV_DEST/IgelkottFisheye.fuse" 2>/dev/null
        RV_REPORT="\n✓ Resolve: IgelkottFisheye.fuse updated (restart Resolve; Fusion: Add Tool → Fuses → Igelkott)"
    else
        RV_REPORT="\n✗ Resolve: could not write to $RV_DEST"
    fi
fi
# Direction Lock: tracker CSVs (exported from the Curve Editor) in the folder are converted to Stab curves in the
# subfolder Stab. One click after tracking: start the app. The settings (k, pixels/degrees, signs) are in
# installningar.txt.
DL_DIR="${IGELKOTT_DL_DIR:-$HOME/Movies/IgelkottFisheye Direction Lock}"
DL_REPORT=""
if [ -x "$HERE/MacOS/directionlock" ]; then
    mkdir -p "$DL_DIR/Stab"
    [ -f "$DL_DIR/installningar.txt" ] || cat > "$DL_DIR/installningar.txt" <<'TXT'
# Stabilization from a tracked path. One line of flags at the bottom; lines starting with # are ignored.
#   --view 60 3840 2160        tracked in a tracking view (IgelkottFisheye in Mode Wall): the view's FOV, width, height
#   --start 1166 793           the point's position in the view on the first frame (pixels, origin top left)
#   --smooth 0.5               path = smoothing over 0.5 s, shake = the rest (--fps 25)
#   --yaw-only                 only Stab Yaw (pan); no Stab Pitch file
#   --yaw-sign -1  --pitch-sign -1    flip the direction if the stabilization makes it worse
#   --strength 1               0 = no stabilization, 1 = full
# Older ways: --fisheye 4096 --sensor-height 23.9 (tracked in the fisheye clip itself), --k 0.5 (Eric's DL instead
# of --smooth), --pixels 58.5 2160.
--view 60 3840 2160 --smooth 0.5 --yaw-only
TXT
    DL_ARGS=($(grep -v '^[[:space:]]*#' "$DL_DIR/installningar.txt" | tr '\n' ' '))
    DL_FILES=()
    for f in "$DL_DIR"/*.csv; do [ -f "$f" ] && DL_FILES+=("$f"); done
    DL_N=${#DL_FILES[@]}
    if [ $DL_N -gt 0 ]; then
        # Fisheye mode (--fisheye) takes Offset X and Offset Y together; otherwise each file is converted on its own
        DL_OUT="$("$HERE/MacOS/directionlock" "${DL_FILES[@]}" "${DL_ARGS[@]}" --out "$DL_DIR/Stab" 2>&1)" \
            || DL_REPORT="\n✗ Direction Lock: $(printf '%s' "$DL_OUT" | tr '"' "'" | tail -1)"
    fi
    DL_REPORT="\n\nDirection Lock: $DL_N tracker file(s) converted to Stab curves in $DL_DIR/Stab (${DL_ARGS[*]})$DL_REPORT"
fi
LV="$(/usr/bin/defaults read /Applications/Assimilate.app/Contents/Info CFBundleShortVersionString 2>/dev/null || echo "not found")"
# Auto Stabilize: fisheye clip in, Stab Yaw out — no tracker and no measurements (tools/autoyaw.swift).
# IGELKOTT_CLIP=<clip> runs it without dialogs (test / scripts).
stabilize() {
    local clip="$1" out
    mkdir -p "$DL_DIR/Stab"
    [ -z "$IGELKOTT_NO_DIALOG" ] && /usr/bin/osascript -e "display notification \"Computing the pan from $(basename "$clip") …\" with title \"Igelkott Live FX Fisheye\"" >/dev/null 2>&1
    if out="$("$HERE/MacOS/autoyaw" "$clip" --out "$DL_DIR/Stab" 2>/dev/null)"; then
        local file; file="$(printf '%s\n' "$out" | tail -1)"
        say_dialog "Stab Yaw done\n\n$(printf '%s\n' "$out" | sed '$d' | tr '"' "'" | sed 's/$/\\n/' | tr -d '\n')\n$(basename "$file")\n\nImport it into Stab Yaw on each wall's IgelkottFisheye node (Curve Editor → Import). Leave Stab Pitch and Stab Roll at 0." note
        [ -z "$IGELKOTT_NO_DIALOG" ] && /usr/bin/open -R "$file"
    else
        say_dialog "Could not compute the pan from $(basename "$clip"). It must be the square fisheye clip (ProRes, H.264 or HEVC in a QuickTime file)." stop
    fi
}
if [ -n "$IGELKOTT_CLIP" ]; then stabilize "$IGELKOTT_CLIP"; exit 0; fi

MSG="IgelkottFisheye2D $VER (build $BUILD)\n$REPORT$RV_REPORT\n\nLive FX: $LV\nUse the node instead of Eq->2D Transformer on each wall with an 8040 x 8040 fisheye clip: same Yaw, Pitch, Roll and FOV.\n\n$NEXT$DL_REPORT"
if [ -n "$IGELKOTT_NO_DIALOG" ] || [ ! -x "$HERE/MacOS/autoyaw" ]; then say_dialog "$MSG" note; exit 0; fi
CHOICE="$(/usr/bin/osascript -e "button returned of (display dialog \"$MSG\" with title \"Igelkott Live FX Fisheye $VER\" buttons {\"Stabilize a clip …\", \"OK\"} default button 2 with icon note)" 2>/dev/null)"
if [ "$CHOICE" = "Stabilize a clip …" ]; then
    CLIP="$(/usr/bin/osascript -e 'POSIX path of (choose file with prompt "Choose the fisheye clip (the square raw clip)" of type {"public.movie"})' 2>/dev/null)"
    [ -n "$CLIP" ] && stabilize "$CLIP"
fi
exit 0
