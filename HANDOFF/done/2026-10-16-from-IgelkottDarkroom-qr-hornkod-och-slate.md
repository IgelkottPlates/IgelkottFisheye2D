---
from: IgelkottDarkroom
to: IgelkottLiveFXFisheye
date: 2026-10-16
deadline: när det passar
urgency: normal
topic: QR i plåtar — bara hörnkoder är Darkrooms märke, QR inne i bilden är slate (Eric: "viktigt att alla vet")
status: done
---

# Från IgelkottDarkroom till IgelkottLiveFXFisheye: hörnkod = märke, QR i bilden = slate

## Vad har hänt

Darkroom 0.9.43 och senare ritar ett hörnmärke i mastrar, provklipp och fisheye-proxyer: samma QR-kod i alla fyra hörnen med texten
`IGK1|1|<FisheyeLens-profil>|<klipp>` (t.ex. `IGK1|1|sonyVenice2|A007C001_260614VQ`). En sådan fil är redan centrerad mot
linsmodellen. I en PYXIS-proxy läste Apples Vision också slate-QR:n som filmats i scenen ("IGKZIU7U", en mobil i bild).

Eric 2026-10-16: "ja, bara hörnkoder, viktigt att alla vet, samt att qr i mitten är slate".

## Varför du behöver veta

Ni ska läsa hörnmärket (IgelkottMotions handoff 2026-10-15). En QR inne i bilden är slate och aldrig ett märke.

## Vad jag förväntar mig att du gör

- [ ] Ta bara en kod i ett hörn som börjar med `IGK1|` som märke. En märkt fil spelas med linsmodellen som den är, utan offset.
- [ ] Läs regeln och formatet: `_atlas/knowledge/camera-rigs/qr-hornmarke-och-slate.md`.

## Bakgrund och länkar

- `_atlas/knowledge/camera-rigs/qr-hornmarke-och-slate.md`
- Darkroom: `PROJECT.md` avsnitt 0.9.43–0.9.46, `core/mark.hpp`.

## Avslut

IgelkottLiveFXFisheye 0.12 (2026-10-19, build 202610192043, i `_applaunchers`):
- `findCircle` är borttagen ur Auto Stabilize. Ett litat märke (`LensMark.read(movie:)`, `Reading.trusted`) ger kamerans
  modell utan offset; utan märke gäller `--camera` (standard PYXIS 12K) och `FisheyeLens.forClip` (FisheyetoEquis
  kalibrering, annars modellens mitt). Verktyget skriver ut kameran och varifrån mitten kom.
- Noden har fått **Camera**: Custom / PYXIS 12K / Sony Venice 2 med kamerans egen modell ur `_shared/IgelkottFisheyeLens`.
  Shadern kan inte läsa QR, så användaren väljer märkets kamera och låter Lens Offset vara 0. Valet syns i panelen.
- Bara hörnkoder som börjar med `IGK1|` räknas (läsaren tittar bara i hörnen); QR inne i bilden används inte.
- Inte provat på en märkt fil — ingen fanns till hands. Offroad (omärkt Venice) ger samma kurva som förut inom 0,009°.
