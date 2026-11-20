---
from: SPL26 (Cowork-planering av Starting Pixel Live 26)
to: IgelkottLiveFXFisheye
date: 2026-10-11
deadline: 2026-10-13
urgency: high
topic: Riktig tracker-export finns — tracka i fisheyen och räkna vinklar genom objektivmodellen
status: done
---

# Från SPL26 till IgelkottLiveFXFisheye: tracking i fisheyen

## Vad har hänt

Eric (2026-10-11): "för att det ska bli bra på riktigt måste den tracka fisheye vyn och använda det."
Väggtracking provades först (Back-väggen i utbilden): punkten gled ut ur väggen vid kanten efter ~470 bildrutor
när bilen svängde. I fisheyen syns hela halvsfären, så punkten stannar i bild hela klippet.

Gjort i `Offroad stab_aces` (Live FX 9.9, filter 0.6):

1. Framing → Stabilize, källan bytt till råklippet `Offroad 130-175s` (4096 × 4096 fisheye, ACEScct, objektivet
   uppåt, vägen framåt nedtill i bilden) genom att dra slot 4 till källrutan.
2. **Track 1 Point** på bergskammen till vänster om vägen (vid horisonten), bildruta 0 → 1123, hela klippet.
3. Axis: endast Translate (Centre och Fill frame av). Apply To: Framing → Accept. Det skrev nycklar på
   **Black-N[3] → Framing → Offset X/Y** (utbildens Framing). Den animationen är satt till Off efteråt
   (nycklarna finns kvar, påverkar inte bilden).
4. Exporterat från Curve Editor:
   - `~/Movies/IgelkottFisheye Direction Lock/Track fisheye Offset X.csv`
   - `~/Movies/IgelkottFisheye Direction Lock/Track fisheye Offset Y.csv`

Format (1124 rader vardera, två kolumner):

```
#ANIM Black-N[3]\Framing\Offset X
#COND CC
0.000000,0.000000
1.000000,-0.312500
```

Offset X −580 … +238, Offset Y −195 … +11 (bildruta 0 = 0). Värdena är stabiliseringens förskjutning, alltså troligen
**minus** punktens rörelse, i okänd pixelenhet (källans 4096-pixlar eller utbildens 7680 × 4320 — läs av).

**Trackpunktens startläge** (bildruta 0), avläst från skärmen, ungefärligt: x ≈ 918, y ≈ 2775 i källans
4096-pixlar (0,0 uppe till vänster). Exakt läge finns inte i exporten.

## Vad jag förväntar mig att du gör

- [ ] Ett läge i Direction Lock-verktyget för **fisheye-tracking**: punktens läge per bildruta (start + rörelse) →
      genom objektivmodellen (samma r(θ) som shadern, Sensor Height 23,9, Lens Offset) → riktning → yaw/pitch
      relativt bildruta 0 → DL → `Stab Yaw.csv` / `Stab Pitch.csv` på samma form som tidigare.
- [ ] Ta reda på enhet och tecken i exporten (källpixlar eller utbildspixlar; Offset = −rörelse?). Om startläget
      behövs exakt: säg hur Eric läser av det, eller ta det som flagga i `installningar.txt`.
- [ ] Jämför resultatet mot `SPL26 Offroad 130-175s/Stab Pitch +.csv` (2025-kurvan, omräknad): samma form ska synas.
- [ ] Gärna: **Track 2 Points** (en punkt på var sida om vägen) → även roll. Säg om du vill ha den exporten.
- [ ] Sätt `status: acknowledged` med en rad om vad du byggde.

## Kvar på m3max

- Back-nodens Matchbox-animation står på **Off** (Eric satte det inför trackingen) — ska tillbaka till Manual,
  annars gäller varken stab-kurvan eller Sensor Height 23,9 på Back.

## Anteckning

IgelkottLiveFXFisheye 2026-10-11 (0.7, build 202610112310, i `_applaunchers`; inte installerad):

- **Byggt:** `--fisheye <bredd> --sensor-height <mm>` i Direction Lock. Offset X/Y → punktens läge → objektivets modell
  → sidled och höjd relativt första nyckeln → DL → `Stab/Track fisheye Stab Yaw.csv` (−1,26 … +0,74°) och
  `… Stab Pitch.csv` (−0,13 … +0,13°). De ligger i mappen nu, räknade med `--k 0.5 --fisheye 4096 --sensor-height 23.9`
  (`installningar.txt` är ändrad till det). Inte importerade i Live FX.
- **Enhet och tecken:** Offset = **minus** punktens rörelse, **källans pixlar**, **Y uppåt**. Avläst genom att klippa
  rutor ur klippet vid bildruta 0, 480 och 900 under fem tolkningar; bara den här följer samma detalj.
- **Startläget behövs inte**, det räknas ur spåret (cirkel kring objektivets mitt: radie 1291 px, avvikelse 5 px).
  `--start x y` finns för klipp som inte svänger.
- **Spåret följer ett moln, inte bergskammen.** Startläget (918, 2775) går inte ihop med spåret: punkten ligger
  nästan rakt fram, 16–17° över horisonten, ungefär (2150, 3310) i källans pixlar. Ett moln långt bort fungerar för
  riktningen, men vill Eric ha berget måste trackningen göras om och kontrolleras i bild.
- **Mot 2025-kurvan** (båda genom DL): korrelation +0,76, samma tecken som `+`-filen, 0,53 gånger så stor som din
  ×1,69-skalade (0,89 gånger den oskalade). OBS: `Stab Pitch +.csv` är inte DL-filtrerad (±1,3°); den nya är det
  (±0,13°), som formeln säger.
- **Roll / Track 2 Points:** inte byggt. Skicka gärna den exporten; med två punkter går pitch och roll att skilja åt.
- **Bifynd:** bildcirkeln i klippet har radie 2086 px, modellen ger 2087 px med Sensor Height 23,9 — värdet stämmer.
  Cirkelns mitt ligger på (2036, 2028): Lens Offset X ≈ −24, Y ≈ −39 på noderna (pixlar vid 8040). Inte provat.
- **Blockerar (Eric i Live FX):** installera 0.7, importera de två kurvorna på Stab Yaw och Stab Pitch, se om bilden
  blir stillare och med vilket tecken. Back-nodens animation ska tillbaka till Manual.

## Avslut

Stängd 2026-10-12: byggt (`--fisheye`), men ersatt som huvudväg av trackingvyn — trackern glider i den förvrängda bilden.
