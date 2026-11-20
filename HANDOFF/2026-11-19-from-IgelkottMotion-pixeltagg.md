---
from: IgelkottMotion
to: IgelkottLiveFXFisheye
date: 2026-11-19
deadline: när det passar
urgency: normal
topic: pixeltaggen: reglerna står, läs dem i shaders (PixelTag i _shared)
status: acknowledged
---

# Från IgelkottMotion till IgelkottLiveFXFisheye: pixeltaggen

## Vad har hänt

Stage 1:s förslag om pixeltaggen (handoff 2026-11-19, Eric: "ja, skriv förslaget 1 och skicka handoffarna") är byggt i
`_shared/IgelkottFisheyeLens` som `PixelTag` i målet `IgelkottLensMark` (Motion KRAV AIM-310). Reglerna står bara i
`Sources/IgelkottLensMark/PixelTag.swift`; README:n har en sammanfattning.

- **Platsen ändrad:** längs övre kanten bredvid QR-koden, rutor 0,011 av sidan, x 0,116–0,226, y 0,010–0,032, i **alla fyra**
  hörnen speglade som QR-koderna. Förslagets plats under QR-koden låg inne i PYXIS bildcirkel vid 125° (Fisheye to Equi 1.93).
- **Bitarna:** ruta 0 vit, 1 svart, version 2 bitar (1), kamera 3 bitar (0 okänd, 1 PYXIS 12K, 2 Sony Venice 2, 3 Z-Cam E2 S6,
  4–7 lediga), nadir, justerad, horisonten inbränd, 4 lediga (skrivs 0), CRC-6 (polynom 0x27, start 0x3F, högsta biten först).
- **Skrivaren:** `PixelTag(mark: LensMark)` ger taggen ur samma märke som QR-koden; `drawing(width:height:)` ger pixelrutorna
  (y nedåt, hela pixlar) med vit eller svart, `draw(in: CGContext, …)` ritar. Vit = full nivå, svart = 0, i varje kanal.
- **Läsaren:** `PixelTag.read(_ CGImage)` eller `read(width:height:mean:)`; mitten av varje ruta, tröskeln mitt emellan referenserna.
- **Prov:** `PixelTagRules` (5760², 3216², 2048², nedskalad proxy, LUT före, vänd bild, trasig CRC, version 2, svag kontrast,
  platsen mot båda linsmodellerna); låsta rutor i `theCellsAreLocked`. 6 mutationer fällda. Inte provat i Live FX eller på en riktig fil.

## Vad jag förväntar mig att du gör

- [ ] Läs taggen i shaders efter `PixelTag` (plats, referenser, CRC); provet i `tools/verify.swift` mot de låsta rutorna och mot bilder ritade av `PixelTag.draw`.
- [ ] Ditt PROJECT.md-förslag är rättat för platsen och kodningen (avsnittet om pixeltaggen).

## Anteckning

IgelkottLiveFXFisheye 2026-11-19 (0.14): shaders läser taggen efter `PixelTag` (plats, referenser, kontrast 0,1, CRC-6, majoritet mellan hörnen); källan `shader/core.glsl`. Provet är `tools/verify_windows.py` (Windows): taggen ritad som `PixelTag.rect`, bitarna mot `PixelTagTests` provvektorer, LUT före, trasig CRC, Z-Cam, svag kontrast, ett hörn, majoritet. PROJECT.md:s förslag rättat. **Kvar:** `tools/verify.swift` (Mac) är inte omskrivet och provar inte mot `PixelTag.draw`.
