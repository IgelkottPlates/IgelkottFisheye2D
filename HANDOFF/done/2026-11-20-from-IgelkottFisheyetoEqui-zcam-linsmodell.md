---
from: IgelkottFisheyetoEqui
to: IgelkottLiveFXFisheye
date: 2026-11-20
urgency: normal
topic: Z CAM E2-S6 har en linsmodell i _shared (FisheyeLens.zcamE2S6)
status: done
---

# Från IgelkottFisheyetoEqui till IgelkottLiveFXFisheye: Z CAM-modellen i det delade biblioteket

## Vad har hänt

Eric 2026-11-20 ("Kör", skalan "Entaniyas tabell", "i det delade biblioteket"): `_shared/IgelkottFisheyeLens` har nu
`FisheyeLens.zcamE2S6` (reference 3872, mitten 1936, 1936, Entaniyas HAL250 3.6-kolumn med 3,748 µm/px, r(125°) = 1902 px) och
`FisheyeLens.cameras` = [pyxis12K, sonyVenice2, zcamE2S6]; `cameraName` "Z CAM E2-S6". Pixeltaggens kod 3 ger därmed en modell
(`PixelTag.camera`). Proven i paketet är ändrade efter det (`theVeniceModelIsItsOwnCamera`: tre kameror;
`theMarkGivesTheTagAndZCamItsModel`: kod 3 ger `.zcamE2S6`); alla 22 går igenom. Kontrollerat: konventionen mot Venice-kartan
(medel 0,00 px) och horisonten i Lund inom ≈ 1°. Underlag: `_atlas/knowledge/camera-rigs/entaniya-hal250-image-height.md`.

## Vad jag förväntar mig att du gör

- [ ] Bygg om mot paketet. En kameraväljare som listar `FisheyeLens.cameras` visar nu också Z CAM E2-S6.
- [ ] Shaders/verktyg som genererar linsens tal ur paketet: ta med kod 3.

## Anteckning

Klart 2026-11-20 i IgelkottLiveFXFisheye 0.18: `build_shaders.py` läser `FisheyeLens.zcamE2S6` som tredje kamera,
Camera Z-Cam och taggkod 3 spelar med sin egen modell. Provat på Mac (CGL-kopian av `verify_windows.py`, 61 fall PASS)
och sett i Live FX. Inget riktigt Z-Cam-klipp provat.
