#!/bin/bash
# Igelkott Live FX Fisheye — installerar / uppdaterar Matchbox-noden IgelkottFisheye2D i Live FX.
# Körs som huvudprogram i IgelkottLiveFXFisheye.app (installerad i /Applications av IgelkottSuit).
# Shadern ligger i appens Resources/Matchbox och kopieras till Live FX:s Matchbox-mapp, som Live FX läser vid start
# (Settings/Junxion.xml listar modulerna därifrån).
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HERE/Resources/Matchbox"
VER="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$HERE/Info.plist" 2>/dev/null)"
BUILD="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$HERE/Info.plist" 2>/dev/null)"
FILES=(IgelkottFisheye2D.glsl IgelkottFisheye2D.xml)

# IGELKOTT_NO_DIALOG=1 skriver rapporten till stdout i stället för en dialogruta (för test / skript);
# IGELKOTT_MATCHBOX_DIR pekar om målet (provet)
say_dialog() { if [ -n "$IGELKOTT_NO_DIALOG" ]; then printf "%b\n" "$1"; return; fi; /usr/bin/osascript -e "display dialog \"$1\" with title \"Igelkott Live FX Fisheye $VER\" buttons {\"OK\"} default button 1 with icon $2" >/dev/null 2>&1; }

for f in "${FILES[@]}"; do
    [ -f "$SRC/$f" ] || { say_dialog "Hittar inte $f i appen ($SRC). Installera om appen från IgelkottSuit." stop; exit 1; }
done

DEST="${IGELKOTT_MATCHBOX_DIR:-/Library/Application Support/Assimilator/Plugins/Matchbox/shaders}"
if [ -z "$IGELKOTT_MATCHBOX_DIR" ] && [ ! -d "/Library/Application Support/Assimilator" ]; then
    say_dialog "Hittar inte Live FX (/Library/Application Support/Assimilator). Är Live FX installerat och startat minst en gång?" stop; exit 1
fi
N=0
for f in "${FILES[@]}"; do cmp -s "$SRC/$f" "$DEST/$f" 2>/dev/null || N=$((N+1)); done
if [ $N -gt 0 ]; then
    if mkdir -p "$DEST" 2>/dev/null && cp "${FILES[@]/#/$SRC/}" "$DEST/" 2>/dev/null; then :; else
        # Matchbox-mappen är inte skrivbar för användaren: be om administratörsrätt en gång
        /usr/bin/osascript -e "do shell script \"mkdir -p '$DEST' && cp '$SRC'/IgelkottFisheye2D.* '$DEST/' && chmod a+r '$DEST'/IgelkottFisheye2D.*\" with administrator privileges" >/dev/null 2>&1 \
            || { say_dialog "Kunde inte skriva till $DEST." stop; exit 1; }
    fi
    /usr/bin/xattr -d com.apple.quarantine "$DEST"/IgelkottFisheye2D.* 2>/dev/null
    REPORT="✓ IgelkottFisheye2D uppdaterad i $DEST"
    NEXT="Starta om Live FX. Noden finns sedan under Matchbox → shaders → IgelkottFisheye2D."
else
    REPORT="✓ Redan aktuell i $DEST"
    NEXT="Ingen åtgärd behövs."
fi
# Direction Lock: tracker-CSV:er (exporterade ur Curve Editor) i mappen räknas om till Stab-kurvor i undermappen Stab.
# Ett tryck efter trackingen: starta appen. Inställningarna (k, pixlar/grader, tecken) står i installningar.txt.
DL_DIR="${IGELKOTT_DL_DIR:-$HOME/Movies/IgelkottFisheye Direction Lock}"
DL_REPORT=""
if [ -x "$HERE/MacOS/directionlock" ]; then
    mkdir -p "$DL_DIR/Stab"
    [ -f "$DL_DIR/installningar.txt" ] || cat > "$DL_DIR/installningar.txt" <<'TXT'
# Stabilisering ur ett trackat spår. En rad med flaggor längst ner, rader med # räknas inte.
#   --view 60 3840 2160        trackat i en trackingvy (IgelkottFisheye i Mode Wall): vyns FOV, bredd och höjd
#   --start 1166 793           punktens läge i vyn vid första bildrutan (pixlar, origo uppe till vänster)
#   --smooth 0.5               väg = utjämning över 0,5 s, skak = resten (--fps 25)
#   --yaw-only                 bara Stab Yaw (pan); ingen Stab Pitch-fil
#   --yaw-sign -1  --pitch-sign -1    byt håll om stabiliseringen gör det värre
#   --strength 1               0 = ingen stabilisering, 1 = hela
# Äldre vägar: --fisheye 4096 --sensor-height 23.9 (trackat i själva fisheyeklippet), --k 0.5 (Erics DL i stället
# för --smooth), --pixels 58.5 2160.
--view 60 3840 2160 --smooth 0.5 --yaw-only
TXT
    DL_ARGS=($(grep -v '^[[:space:]]*#' "$DL_DIR/installningar.txt" | tr '\n' ' '))
    DL_FILES=()
    for f in "$DL_DIR"/*.csv; do [ -f "$f" ] && DL_FILES+=("$f"); done
    DL_N=${#DL_FILES[@]}
    if [ $DL_N -gt 0 ]; then
        # Fisheye-läget (--fisheye) tar Offset X och Offset Y tillsammans; annars räknas varje fil för sig
        DL_OUT="$("$HERE/MacOS/directionlock" "${DL_FILES[@]}" "${DL_ARGS[@]}" --out "$DL_DIR/Stab" 2>&1)" \
            || DL_REPORT="\n✗ Direction Lock: $(printf '%s' "$DL_OUT" | tr '"' "'" | tail -1)"
    fi
    DL_REPORT="\n\nDirection Lock: $DL_N tracker-fil(er) omräknade till Stab-kurvor i $DL_DIR/Stab (${DL_ARGS[*]})$DL_REPORT"
fi
LV="$(/usr/bin/defaults read /Applications/Assimilate.app/Contents/Info CFBundleShortVersionString 2>/dev/null || echo "hittades inte")"
# Auto Stabilize: fisheyeklippet in, Stab Yaw ut — ingen tracker och inga mått (tools/autoyaw.swift).
# IGELKOTT_CLIP=<klipp> kör det utan dialogrutor (prov / skript).
stabilize() {
    local clip="$1" out
    mkdir -p "$DL_DIR/Stab"
    [ -z "$IGELKOTT_NO_DIALOG" ] && /usr/bin/osascript -e "display notification \"Räknar pan ur $(basename "$clip") …\" with title \"Igelkott Live FX Fisheye\"" >/dev/null 2>&1
    if out="$("$HERE/MacOS/autoyaw" "$clip" --out "$DL_DIR/Stab" 2>/dev/null)"; then
        local file; file="$(printf '%s\n' "$out" | tail -1)"
        say_dialog "Stab Yaw klar\n\n$(printf '%s\n' "$out" | sed '$d' | tr '"' "'" | sed 's/$/\\n/' | tr -d '\n')\n$(basename "$file")\n\nImportera den på Stab Yaw i varje väggs IgelkottFisheye-nod (Curve Editor → Import). Stab Pitch och Stab Roll på 0." note
        [ -z "$IGELKOTT_NO_DIALOG" ] && /usr/bin/open -R "$file"
    else
        say_dialog "Kunde inte räkna pan ur $(basename "$clip"). Det ska vara det kvadratiska fisheyeklippet (ProRes, H.264 eller HEVC i en QuickTime-fil)." stop
    fi
}
if [ -n "$IGELKOTT_CLIP" ]; then stabilize "$IGELKOTT_CLIP"; exit 0; fi

MSG="IgelkottFisheye2D $VER (build $BUILD)\n$REPORT\n\nLive FX: $LV\nAnvänd noden i stället för Eq->2D Transformer på varje vägg i ett 8040 x 8040-fisheyeklipp: samma Yaw, Pitch, Roll och FOV.\n\n$NEXT$DL_REPORT"
if [ -n "$IGELKOTT_NO_DIALOG" ] || [ ! -x "$HERE/MacOS/autoyaw" ]; then say_dialog "$MSG" note; exit 0; fi
CHOICE="$(/usr/bin/osascript -e "button returned of (display dialog \"$MSG\" with title \"Igelkott Live FX Fisheye $VER\" buttons {\"Stabilisera ett klipp …\", \"OK\"} default button 2 with icon note)" 2>/dev/null)"
if [ "$CHOICE" = "Stabilisera ett klipp …" ]; then
    CLIP="$(/usr/bin/osascript -e 'POSIX path of (choose file with prompt "Välj fisheyeklippet (det kvadratiska råklippet)" of type {"public.movie"})' 2>/dev/null)"
    [ -n "$CLIP" ] && stabilize "$CLIP"
fi
exit 0
