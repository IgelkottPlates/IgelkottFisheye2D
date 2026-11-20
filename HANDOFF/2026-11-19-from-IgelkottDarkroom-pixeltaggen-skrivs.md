---
from: IgelkottDarkroom
to: IgelkottLiveFXFisheye
date: 2026-11-19
deadline: –
urgency: normal
topic: Darkroom 0.10.102 skriver pixeltaggen — vilka filer som har den
status: acknowledged
---

# Från IgelkottDarkroom till IgelkottLiveFXFisheye: pixeltaggen skrivs

## Vad har hänt

Darkroom 0.10.102 (i `_applaunchers`) skriver pixeltaggen med Motions `PixelTag(mark:)` (`_shared/IgelkottFisheyeLens`, `IgelkottLensMark`) i alla fyra hörnen bredvid hörnmärkets QR-kod. Det gäller varje fil som får hörnmärket: centrerade fisheye-masters (`03_DeChab/To_<maskin>/`, PYXIS 4032², Venice 5760²) och fisheye-proxyer (`02_Proxy/01_Fisheye proxy/`, Venice 2880²). Vit är kodvärde 1 och svart 0 i ACEScct innan Y'CbCr.

**Vilka filer:** bara de som renderas med 0.10.102 eller senare. Ingen befintlig fil har taggen, och Darkroom skriver inte om gamla filer.

**Provat:** A014C006 (Free Demo 2025, X-OCN) master 5760² och proxy 2880² läses tillbaka med `PixelTag.read` i alla fyra hörnen: kamera 2, justerad, och nadir när märket säger nadir. Provfilerna är tillfälliga och ligger inte på NAS:en. Inte provat: PYXIS och Live FX.

**Efter Topaz:** Darkrooms master går till Topaz. Om taggen överlever Topaz-filen är inte mätt; Fisheye to Equi skriver den igen sist enligt Motions handoff.

## Vad jag förväntar mig att du gör

- [ ] Säg till när ni vill ha en riktig fil att prova noden på. Darkroom kan rendera ett kort klipp med taggen till en mapp ni anger.

## Anteckning

IgelkottLiveFXFisheye 2026-11-19: noden 0.14 läser taggen. Ja tack till ett kort klipp med taggen när Eric anger mapp — helst en PYXIS-zenit och en Venice-nadir. Provat hittills bara på plåtar ritade av `tools/make_testplates.py`.
