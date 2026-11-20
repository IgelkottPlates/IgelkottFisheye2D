---
from: IgelkottFisheyetoEqui
to: IgelkottLiveFXFisheye
date: 2026-11-19
deadline: innan pixeltaggens platser låses i LensMark
urgency: normal
topic: Fisheye 1.93 (beskärning 125°) når in i hörnrutan och pixeltaggens innersta cell
status: done
---

# Från IgelkottFisheyetoEqui till IgelkottLiveFXFisheye: hörnrutan och pixeltaggen efter 125°

## Vad har hänt

Fisheye 1.93 (2026-11-19, Eric: "Ändra beskräningen till 125 grader", "125 från axeln") beskär fisheye ut vid θ = 125° från källans
axel i stället för 1.92:s 1,95 rad (≈ 112°). Cirkeln blir större än pixeltaggförslaget räknade med ("värsta punkten 0,517 s från mitten").
Räknat med linsmodellerna i `_shared/IgelkottFisheyeLens` (radie = r(125°), mitten = linsens mitt), andelar av sidan s:

| Kamera | Cirkelns radie | Hörnrutan 0,14 × 0,14 | Taggens celler i bilden |
|---|---|---|---|
| PYXIS 12K | 0,5222 s (104,4 % av bredden) | båda hörnen: bilden når in (innerhörnet 0,5091 s) | rad 2, cell 9 i båda hörnen, 0,0052 s in (≈ 42 px vid 8040) |
| Sony Venice 2 | 0,5075 s (101,5 %) | uppe till vänster når bilden in (innerhörnet 0,5020 s, linsmitten ligger snett); nere till höger inte | ingen (marginal ≈ 0,0024 s, ≈ 14 px vid 5760, uppe till vänster) |

Följder:
- Taggen ritas ovanpå bilden, så den läses ändå, men cell 9 i rad 2 ligger på bildkanten för PYXIS och Venice har nästan ingen marginal.
- Stage 1:s mask av hörnrutan (SPEL1-16) döljer nu en liten flisa av bilden i PYXIS båda hörn och Venice uppe till vänster.
- Hörnmärkets QR (0,01–0,11 s) ligger fortfarande utanför cirkeln för båda kamerorna.

## Vad jag förväntar mig att du gör

- [ ] Bestäm med Eric om taggen flyttas närmare hörnet (t.ex. kortare rader, eller cellerna bredvid QR-koden i stället för under) eller om
      flisan godtas. Räkna med cirkeln vid 125° och linsmittens snedläge för Venice.
- [ ] Om hörnrutans mask (0,14) ska krympas eller formas efter cirkeln: Stage 1:s sak.

## Bakgrund och länkar

- `IgelkottFisheyetoEqui/PROJECT.md` v1.93; `FisheyeOut.sourceMaxTheta`.
- `IgelkottLiveFXFisheye/PROJECT.md`, "Förslag: kameran och nadir/zenit automatiskt (pixeltaggen, 2026-11-19)".
- Samma anteckning gick till IgelkottStage1, IgelkottMotion och IgelkottLiveFXFisheye.

## Anteckning

IgelkottLiveFXFisheye 2026-11-19: löst av Motions plats i `PixelTag` (längs övre kanten bredvid QR-koden, x 0,116–0,226, y 0,010–0,032, alla fyra hörnen), som ligger utanför PYXIS-cirkeln vid 125°. Shadern 0.14 läser den platsen; förslaget i PROJECT.md är rättat. Hörnrutans mask i Stage 1 är Stage 1:s sak.
