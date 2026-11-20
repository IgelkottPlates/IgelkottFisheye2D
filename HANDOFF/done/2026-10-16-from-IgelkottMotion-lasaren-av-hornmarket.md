---
from: IgelkottMotion
to: IgelkottLiveFXFisheye
date: 2026-10-16
deadline: när det passar
urgency: low
topic: Läsaren av Darkrooms hörnmärke finns (IgelkottLensMark i _shared/IgelkottFisheyeLens); Darkroom 0.9.43 märker filer
status: done
---

# Från IgelkottMotion till IgelkottLiveFXFisheye: läsaren av hörnmärket finns

## Vad har hänt

Uppföljning av handoffen 2026-10-15 ("När läsaren finns"). Darkroom 0.9.43 bränner in centreringen och märket
`IGK1|1|<kamera>|<klipp>[+<klipp>]` i alla fyra hörnen på mastrar, provklipp och fisheye-proxyer (inte equi-proxyer).

Läsaren: `.product(name: "IgelkottLensMark", package: "IgelkottFisheyeLens")`, `LensMark.read(movie:)` eller `read(CGImage)`.
Litat (`Reading.trusted`) = kamerans linsmodell som den är, utan offset, och kameran ur märket. Läst på Darkrooms provfiler i 5760²,
2010 px HEVC och 1600 px 709. IgelkottMotion 0.5.6 använder den (KRAV AIM-102).

## Vad jag förväntar mig att du gör

- [ ] Läs märket enligt handoffen 2026-10-15 och använd ingen offset eller eget kameraval för ett litat märke.

## Bakgrund och länkar

- `_shared/IgelkottFisheyeLens/README.md` (avsnittet Hörnmärket), `IgelkottMotion/KRAV.md` AIM-102.

## Avslut

IgelkottLiveFXFisheye 0.12 (2026-10-19, build 202610192043, i `_applaunchers`):
- `findCircle` är borttagen ur Auto Stabilize. Ett litat märke (`LensMark.read(movie:)`, `Reading.trusted`) ger kamerans
  modell utan offset; utan märke gäller `--camera` (standard PYXIS 12K) och `FisheyeLens.forClip` (FisheyetoEquis
  kalibrering, annars modellens mitt). Verktyget skriver ut kameran och varifrån mitten kom.
- Noden har fått **Camera**: Custom / PYXIS 12K / Sony Venice 2 med kamerans egen modell ur `_shared/IgelkottFisheyeLens`.
  Shadern kan inte läsa QR, så användaren väljer märkets kamera och låter Lens Offset vara 0. Valet syns i panelen.
- Bara hörnkoder som börjar med `IGK1|` räknas (läsaren tittar bara i hörnen); QR inne i bilden används inte.
- Inte provat på en märkt fil — ingen fanns till hands. Offroad (omärkt Venice) ger samma kurva som förut inom 0,009°.
