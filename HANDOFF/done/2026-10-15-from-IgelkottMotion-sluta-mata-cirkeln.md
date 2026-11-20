---
from: IgelkottMotion
to: IgelkottLiveFXFisheye
date: 2026-10-15
deadline: när det passar
urgency: low
topic: Bara Darkroom hittar bildcirkeln; `findCircle` i autoyaw ska bort, mitten och kameran läses ur hörnmärket
status: done
---

# Från IgelkottMotion till IgelkottLiveFXFisheye: sluta mäta bildcirkeln

## Vad har hänt

Eric beslutade 2026-10-15: ett enda program hittar bildcirkeln (IgelkottDarkroom) och alla andra slutar göra det själva.
Darkroom märker en justerad fil med en QR-kod i alla fyra hörnen, utanför bildcirkeln: `IGK1|1|<kamera>|<klipp-id>`.
`1` betyder att objektivets axel ligger där kamerans linsmodell (`_shared/IgelkottFisheyeLens`) har sin mitt. Detaljer:
`IgelkottDarkroom/HANDOFF/2026-10-15-from-IgelkottMotion-bildcirkeln-och-hornmarket.md`.

## Varför du behöver veta

- `tools/autoyaw.swift` har en egen `findCircle`, och er Lens Offset knappas in för hand ur en mätning (Offroad-plåten:
  mitten (2036, 2028) av 4096, Lens Offset X ≈ −24, Y ≈ −39 vid 8040). Det är en egen mätning.
- En märkt fil ska spelas med offset 0 och märkets kamera (Sensor Height enligt er tabell för den kameran).
- Hörnen bär nu en kod. `findCircle` läser bakgrunden ur hörnen; på en märkt fil blir den nivån fel, en anledning till att
  inte mäta där.

## Vad jag förväntar mig att du gör

- [ ] Ta bort `findCircle` ur autoyaw (eller hoppa över den när filen är märkt) och ta mitten ur märket eller ur Fisheye to
      Equis kalibrering för omärkta filer.
- [ ] Visa i sidan/pluginen vilken kamera och offset som gäller och varifrån.

## Bakgrund och länkar

- `IgelkottMotion/docs/plans/2026-10-15-linsfil.md`, `IgelkottMotion/KRAV.md` AIM-94.

## Avslut

IgelkottLiveFXFisheye 0.12 (2026-10-19, build 202610192043, i `_applaunchers`):
- `findCircle` är borttagen ur Auto Stabilize. Ett litat märke (`LensMark.read(movie:)`, `Reading.trusted`) ger kamerans
  modell utan offset; utan märke gäller `--camera` (standard PYXIS 12K) och `FisheyeLens.forClip` (FisheyetoEquis
  kalibrering, annars modellens mitt). Verktyget skriver ut kameran och varifrån mitten kom.
- Noden har fått **Camera**: Custom / PYXIS 12K / Sony Venice 2 med kamerans egen modell ur `_shared/IgelkottFisheyeLens`.
  Shadern kan inte läsa QR, så användaren väljer märkets kamera och låter Lens Offset vara 0. Valet syns i panelen.
- Bara hörnkoder som börjar med `IGK1|` räknas (läsaren tittar bara i hörnen); QR inne i bilden används inte.
- Inte provat på en märkt fil — ingen fanns till hands. Offroad (omärkt Venice) ger samma kurva som förut inom 0,009°.
