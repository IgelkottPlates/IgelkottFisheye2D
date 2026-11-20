---
from: SPL26 (Cowork-planering av Starting Pixel Live 26)
to: IgelkottLiveFXFisheye
date: 2026-10-12
deadline: 2026-10-13
urgency: high
topic: Stabilisering via trackingvy fungerar — bygg in omräkningen i appen
status: done
---

# Från SPL26: trackingvyn fungerar, bygg in den

Eric (2026-10-12): "det ser ut att fungera". Metoden och det som inte fungerade står i
`../../_atlas/knowledge/assimilate/fisheye-stabilisering-trackingvy.md`. Kort: IgelkottFisheye i Mode Wall som
trackingvy (3840 × 2160, FOV 60), Live FX tracker → Framing Offset X/Y i pixlar → vinklar via FOV → väg/skak med
Gauss-utjämning åt båda hållen (~0,5 s) → Stab Yaw på väggarna. Direction Lock k = 0,5 och fisheye-geometriläget
behövs inte för det här.

## Vad jag förväntar mig att du gör

- [ ] Ett läge i appen: `--view <FOV> <bredd> <höjd>` + `--smooth <sekunder>` som gör exakt det
      `tools/vy_stab.py` gör (prototyp, skriven av SPL26). Startpunktens läge: läs ur spåret eller som flagga.
- [ ] Prova mot `~/Movies/IgelkottFisheye Direction Lock/Track vy Offset X/Y.csv` — resultatet ska matcha
      `Stab/Vy Stab Yaw (skak).csv` (±1,59°).
- [ ] PROJECT.md: avsnittet Direction Lock skrivs om till den här metoden som huvudväg.
- [ ] Sätt övriga SPL26-handoffar `done` om du håller med.

## Anteckning

IgelkottLiveFXFisheye 2026-10-12 (0.9, build 202610120033, i `_applaunchers`; 0.8 står installerad på m3max):

- **Byggt:** `--view <FOV> <bredd> <höjd>`, `--start <x> <y>` och `--smooth <sekunder>` (`--fps 25`) i appen. Sigma =
  sekunder · fps avrundat nedåt, så 0,5 s ger 12 bildrutor som i prototypen.
- **Provat:** appen körd på `Track vy Offset X/Y.csv` ger `Stab/Track vy Stab Yaw.csv`, identisk med
  `Vy Stab Yaw (skak).csv` (skillnad 0,0; −1,59 … +1,15°). Provet i `build-app.sh` jämför också Pitch (0,0000005°).
- **Startläget** går inte att räkna ur spåret i en rak vy, så det är en flagga: `--start 1166 793` (pixlar, origo
  uppe till vänster) = dina −754, +287 från mitten. Utan flaggan antas bildens mitt.
- **`installningar.txt`** står nu på `--view 60 3840 2160 --start 1166 793 --smooth 0.5 --yaw-only`. Vill du ha
  Pitch-filen också: ta bort `--yaw-only`.
- **Flyttat:** de äldre fisheye-spåren (`Track bak`, `Track fisheye`) och deras kurvor ligger i undermappen
  `Fisheye-spår (äldre metod, --fisheye)`, annars hade appen räknat dem som trackingvy. Dina `Vy Stab …`-filer är orörda.
- **Borttaget:** `tools/vy_stab.py`; dess kurvor ligger som facit i `tools/fixtures/vy/`.
- **PROJECT.md** är omskrivet med trackingvyn som huvudväg, och kunskapsfilen pekar på appen i stället för prototypen.
- **Övriga SPL26-handoffar** är satta `done` och flyttade.
- **Kvar (Eric):** installera 0.9 via Suit och köra kedjan en gång med appen (export → starta appen → import).

## Avslut

2026-10-12: 0.9 (build 202610120033) är installerad på m3max (appen och shadern i Matchbox-mappen står på 0.9), och
kedjan är körd med appen: `Genomgang Offset X/Y.csv` exporterad 00:41, appen skrev `Stab/Genomgang Stab Yaw.csv` 06:37.
Eric: "klart".
