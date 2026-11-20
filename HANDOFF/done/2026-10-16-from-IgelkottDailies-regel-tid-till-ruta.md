---
from: IgelkottDailies
to: IgelkottLiveFXFisheye
date: 2026-10-16
deadline: när det passar
urgency: normal
topic: En regel för alla appar — ruta = floor(t × fps + 1e-6), In och Out är spelhuvudets ruta (inkluderade), exklusivt slut = Out + 1
status: done
---

# Från IgelkottDailies till IgelkottLiveFXFisheye: tid → ruta, In och Out

## Vad har hänt

Eric 2026-10-16: "googla branschstandard och bestäm", och "alla appar måste jobba lika inkl hub". Bakgrunden var Fog City
A016C002 del B: hubbens godkännandemejl sa ruta 21723, hubbens XML 21722 och spelaren visade 21721. Alla tre kom ur samma
sparade sekunder, men räknades med avrundning och golv om vartannat.

Regeln är nu skriven i `_atlas/knowledge/video/tid-till-ruta.md`, och hubben följer den från #503:

1. **Ruta vid tiden t = `floor(t × fps + 1e-6)`.** Ruta n täcker [n/fps, (n+1)/fps). Avrunda aldrig till närmaste ruta.
2. **In** är rutan vid spelhuvudet, och den räknas med.
3. **Out** är rutan vid spelhuvudet, och den räknas också med. Ett exklusivt slut (FCP7 `<out>`, hubbens `out_frame`,
   Darkroom) är Out-rutan + 1, klampat till klippets längd.
4. **Tidkod vid t** = starttidkod + regel 1.
5. **Sparade sekunder ligger på rutans början** (`ruta/fps`). För Out är det den sista inkluderade rutan.

## Vad jag förväntar mig att du gör

- [ ] Kontrollera var appen omvandlar tid till ruta eller tidkod, eller ruta till tid, och följ regeln. Leta särskilt efter
      `round`/`lround`/`rint` på `t × fps`.
- [ ] Kontrollsiffror (24 fps): 905,066 s → ruta 21721. 905,125 s → 21723. Out på 200,0 s → exklusivt slut 4801.
- [ ] Säg till om appen av något skäl måste avvika, så skriver vi in undantaget i atlasfilen i stället för att det glider isär.

## Bakgrund och länkar

- `_atlas/knowledge/video/tid-till-ruta.md`
- Hubben: `IgelkottDailies/beta/web/app/davinci_export.py` (`frame_at`, `clip_frames`), test
  `beta/web/tests/test_frame_rule_503.py`.

## Avslut

IgelkottLiveFXFisheye 2026-10-19: ingen ändring behövs. Projektet räknar aldrig om tid till ruta eller tidkod:
`tools/autoyaw.swift` numrerar bildrutorna i den ordning de avkodas (0, 1, 2 …), `tools/directionlock.swift` och
Stabilizer-sidan tar rutorna ur Live FX:s CSV, och sidans `frameAt` räknar en pixel i diagrammet till en ruta (inte en
tid). Ingen `round`/`lround`/`rint` på t × fps finns (sökt i `tools/`, `stabilizer/`, `app/`, `matchbox/`).
