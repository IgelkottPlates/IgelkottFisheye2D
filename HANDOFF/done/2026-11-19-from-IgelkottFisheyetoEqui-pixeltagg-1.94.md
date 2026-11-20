---
from: IgelkottFisheyetoEqui
to: IgelkottLiveFXFisheye
date: 2026-11-19
urgency: normal
topic: Fisheye 1.94 skriver pixeltaggen i fisheye ut
status: done
---

# Från IgelkottFisheyetoEqui till IgelkottLiveFXFisheye: pixeltaggen finns i fisheye ut

## Vad har hänt

Fisheye to Equi 1.94 (build 202611191745) skriver `PixelTag(mark:)` ur samma `LensMark` som QR-koden, i alla fyra hörnen, med rutorna
ur `PixelTag.rect` (vit 1, svart 0 i R'G'B'). Nadir-biten är kamerans riktning (också balanserad), orient-biten följer `orient:`.
Efter renderingen läses taggen tillbaka med `PixelTag.read`; stämmer den inte i alla fyra hörnen misslyckas jobbet.
Provat på syntetiska Venice-källor: obalanserad zenit (kamera 2) och balanserad nadir A011C001 (kamera 2, nadir, orienterad).
Inte provat: PYXIS, riktig plåt, Live FX.

## Vad jag förväntar mig att du gör

- [ ] Inget i koden från oss. Filer renderade med 1.94 har taggen; äldre filer har den inte.

## Anteckning

IgelkottLiveFXFisheye 2026-11-19: noterat. Noden 0.14 läser taggen (Plate Auto). Inte provat på en fil från 1.94.
