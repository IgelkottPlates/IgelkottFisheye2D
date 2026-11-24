---
from: IgelkottLiveFXFisheye (m3ultra)
to: IgelkottLiveFXFisheye (ERIC-DESKTOP, git)
date: 2026-11-24
deadline: asap
urgency: normal
topic: Nya bilder på produktsidan (inga tågbilder) — pusha docs/
status: pending
---

# Från m3ultra till ERIC-DESKTOP: nya bilder på GitHub Pages-sidan

## Vad har hänt

Eric 2026-11-24, efter att ha sett sidan: "Första bilden måste va pixelskarp. Jag vill inte ha tågbilder. Alla bilder
måste visa 90 grader med öppna landskap med tydliga motiv i centrum som hus, landskap. Inte dunkel skog eller skymt väg."

`docs/` är omgjord på m3ultra efter commit e6c3d49:

- `docs/index.html` — toppbilden visar hela väggen (32:9, rubriken under bilden), Free Run-avsnittet har en Live
  FX-bild i stället för de två tågbilderna, galleriet har sex hela väggar i två kolumner, panelbilden längre ner är borta.
- `docs/img/` — nu 8 bilder, 1,6 MB: `hero_A011C001.jpg` (3840 × 1080), `g1_A011C001.jpg` … `g6_A014C001.jpg`
  (1600 × 450) och `livefx_A011C001.jpg` (1920 × 1080). **De 12 gamla bilderna (`wall_*.jpg`, `livefx_nod.jpg`,
  `livefx_eq2d.jpg`, `livefx_panel.jpg`) är borttagna** och ska bort ur repot.
- `PROJECT.md` — bildvalet och Erics ord.

Kollad i webbläsare på m3ultra (1280 × 900 och mobil 375): alla 8 bilder 200, ingen vågrät rullning, toppbilden
3840 px på 1265 px bredd.

## Vad jag förväntar mig att du gör

- [ ] `git status` — väntat: `docs/index.html` och `PROJECT.md` ändrade, 8 nya och 12 borttagna i `docs/img/`,
      denna handoff ny. Inget i `Ref-Eric/`.
- [ ] `git add -A docs PROJECT.md HANDOFF` (så att de borttagna bilderna följer med), committa och pusha till `main`.
- [ ] Vänta in Pages-bygget och kolla https://igelkottplates.github.io/IgelkottFisheye2D/ — inga `wall_`- eller
      `livefx_nod`-bilder i källan, toppbilden är snölandskapet.
- [ ] Ändra "alla 13 bilder" i `PROJECT.md` till det du ser, flytta handoffen till `done/`.

## Bakgrund

- Förra handoffen: `HANDOFF/done/2026-11-24-from-IgelkottLiveFXFisheye-m3ultra-github-pages.md` (e6c3d49).
- Samma sida som privat artefakt: https://claude.ai/artifact/HzvMBZcBucvaWkRFz9CtVn (Version 9).
