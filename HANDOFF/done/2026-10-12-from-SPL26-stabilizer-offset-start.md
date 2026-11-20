---
from: SPL26 (Cowork-planering av Starting Pixel Live 26)
to: IgelkottLiveFXFisheye
date: 2026-10-12
deadline: före publik release; demokopian är redan lagad
urgency: medium
topic: Stabilizer-sidan antar att Offset X/Y är 0 på första bilden
status: done
---

# Från SPL26: bugg i stabilizer/index.html (viewAngles)

## Vad hände
Eric trackade Offroad 130-175s i Live FX (Track 1 Point, Apply Stabilize) och exporterade
Framing Offset X och Y i **en** CSV (`Matchbox.Offroad 130-175s_test1.csv`). Offset X på bild 0 var
**-434.2**, Offset Y **29.8** — inte 0. Trackerns referensbild var alltså inte första bilden (eller Centre var på).

`viewAngles()` räknar `x = x0 - ox[i]` med x0 = punktens position på *första bilden*. Det stämmer bara om
ox[0] = 0. Annars hamnar punkten fel i vyn och vinklarna får fel skala (atan-olinjäritet, ~5 % här).

## Åtgärder
1. I `stabilizer/index.html` rad 181: ändra till
   `const x = x0 - (ox[i] - ox[0]), y = y0 - (oy[i] - oy[0]);`
   (redan gjort i Erics demokopia `~/Movies/IgelkottFisheye for Live FX/IgelkottFisheye Stabilizer.html`).
2. Lägg till ett testfall i `tools/test-stabilizer.mjs` med offsets som inte startar på 0.
3. Sidtexten säger "drop both files" — en export med båda kurvorna i en fil fungerar redan. Skriv "one or two files".
4. Sidans standardvärden 3840 × 2160: Erics tracking-vy var 4096 × 2160. Överväg att påminna om att mata in nodens Media-storlek.

## Avslut

IgelkottLiveFXFisheye 2026-10-12, Stabilizer-sidan 1.1:
- `viewAngles` räknar från första nyckeln (`ox[i] − ox[0]`), samma rättning i `tools/directionlock.swift`.
- Provfall i `tools/test-stabilizer.mjs`: Offset förskjuten −434,2 / +29,8 ger samma vinklar; en fil med båda kurvorna.
- Texten säger "one file with both curves, or two files".
- Punkt 4 (påminnelse om Media-storleken) är ersatt av Auto Stabilize, där inga mått skrivs in.
