---
from: SPL26 (Cowork-planering av Starting Pixel Live 26)
to: IgelkottLiveFXFisheye
date: 2026-10-12
deadline: efter Starting Pixel Live (2026-10-14); punkt 1 gärna före
urgency: low
topic: Uppföljning publik release — leveransen blir en zip, Windows pausat, en bugg i stabilizer-sidan
status: acknowledged
---

# Från SPL26: uppföljning på publik-release-handoffen

## Vad Eric bestämt (2026-10-12)

- "är inte pluginen bara en fil man lägger i en mapp" → **ingen installer, ingen signering/notarisering**.
  Leveransen blir en zip: `IgelkottFisheye2D.glsl` + `.xml` + `IgelkottFisheye Stabilizer.html` + README.
  Stryk installer-kraven i förra handoffen (punkt 2) och blockeraren om Developer ID.
- **Windows pausat till efter London.** Rör inte Windows-sökvägen nu.

## Åtgärder

1. **Bugg i `stabilizer/index.html`:** `#view .hint` har `display: grid`, så `hidden` slår inte igenom —
   hjälptexten ("Click where the tracked point is…") ligger kvar ovanpå skärmbilden när en bild släpps in.
   Lägg till `[hidden] { display: none !important; }` (eller `#view .hint[hidden]{display:none}`).
2. **Quick Start-underlaget finns nu:** 22 annoterade bilder i
   `Dokument/SPL26 Keynote/01 Session 10.05/Livedemo Live FX/Genomgang/01–22.jpg` (engelska):
   1–3 installera (Finder → Go to Folder → `/Library/Application Support/Assimilator/Plugins/Matchbox/shaders`,
   klistra in, starta om Live FX), 4–16 Live FX, 17–19 stabilizer-sidan, 20–22 importera och rensa spikar.
   `14b.jpg` (Suit-appen) är inaktuell.
3. README i zipen: samma tre installationssteg + länk/PDF till Quick Start.

## Noterat vid provet (Genomgang-spåret i sidan)

- 1124 bildrutor, pan −11,3…20,8°, skak −1,58…1,22°, 8 spikar markerade runt bildruta 167 och senare —
  stämmer med vad Eric rensade för hand. Sidan provad i Chromium (Playwright), inte av Eric i Safari.

## Anteckning

IgelkottLiveFXFisheye 2026-10-12:
- **Punkt 1 lagad** (sidan 1.1): `[hidden] { display: none !important; }`.
- Besluten (zip, ingen signering, Windows pausat) är inskrivna i PROJECT.md, Publik release.
- **Kvar efter London:** README och zipen, Quick Start ur de 22 bilderna. Obs: Auto Stabilize (se den andra
  handoffen) är ett kompilerat Mac-program och passar inte i en osignerad zip — Eric behöver avgöra vad publiken får.
