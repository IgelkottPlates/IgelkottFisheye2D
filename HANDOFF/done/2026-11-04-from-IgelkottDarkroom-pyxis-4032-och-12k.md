---
from: IgelkottDarkroom
to: IgelkottLiveFXFisheye
date: 2026-11-04
deadline: när det passar
urgency: low
topic: PYXIS-mastrar blir 4032²
status: done
---

# Från IgelkottDarkroom till IgelkottLiveFXFisheye: PYXIS-mastrar blir 4032²

## Vad har hänt

Nytt beslut av Eric 2026-11-04: "Pyxis ska sparas ut 4040 proxy och master och delivery equi delivery i publish och theme ska vara 12k 11 520x5 760".

Rättat samma dag av Eric: "ändra så det passar cineform". Storleken blir **4032 × 4032** (252 × 16), inte 4040. 12K-beslutet står kvar.

- PYXIS fisheye-master och fisheye-proxy: **4032 × 4032** (var 3216²).
- PYXIS leveransequi i Publisher och Theme: **11520 × 5760, 12K** (var 7680 × 3840, "P-serien bara 8K" från 2026-11-03).
- 12K gäller bara PYXIS. Venice ändras inte: master 5760², proxy 2880², och leveransen är fortfarande 16K (Eric 2026-11-04).

Darkroom 0.10.74 renderar 4032². Inget är omrenderat. Redan renderade 3216²-mastrar och 8K/16K-equier finns kvar, så båda storlekarna kommer att finnas samtidigt.

## Varför du behöver veta

Noden beskrivs som spelare av 8040 × 8040-fisheyen. PYXIS-mastrar är nu 4032².

## Vad jag förväntar mig att du gör

- [ ] Kontrollera att noden räknar från bildens storlek och att ett 4032²-klipp hamnar rätt på väggarna.

## Bakgrund och länkar

- Beslutet, räkningen och Erics öppna frågor: `../_atlas/knowledge/camera-rigs/plat-storlekar.md`
- Svara på öppna frågor med Eric, anta inget. Ta inte bort eller rendera om befintligt material utan hans ord.

## Avslut

IgelkottLiveFXFisheye 0.13 (2026-11-11): noden räknar i andelar av bilden, inte i pixlar. Proven (`tools/verify.swift`,
`tools/verify_windows.py`) kör alla fall igen med en källa på 1008² (4032 / 4) — alla går igenom. Ett Darkroom-märkt
4032²-klipp spelas med Camera: PYXIS 12K och Lens Offset 0. Texten "8040 × 8040" i noden och AGENTS.md är rättad.
Inte sett i Live FX med ett riktigt 4032²-klipp.
