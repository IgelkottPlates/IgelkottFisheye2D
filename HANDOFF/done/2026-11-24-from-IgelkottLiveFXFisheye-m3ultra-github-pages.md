---
from: IgelkottLiveFXFisheye (m3ultra)
to: IgelkottLiveFXFisheye (ERIC-DESKTOP, git)
date: 2026-11-24
deadline: när det passar
urgency: normal
topic: Publicera produktsidan docs/index.html på GitHub Pages
status: done
---

# Från m3ultra till ERIC-DESKTOP: produktsidan på GitHub Pages

## Vad har hänt

Eric bad 2026-11-24 om att produktsidan "IgelkottFisheye on the Wall" ska ligga på GitHub ("kan denna sida ligga
på github? isåfall säg till windows datorn med git"). Sidan är byggd på m3ultra med Erics ändringar ur Word-filen
`Ref-Eric/IgelkottFisheye-on-the-Wall.docx` (den ligger utanför git via `.gitignore`, ska inte med).

Nya filer i projektmappen (synkade via Drive):

- `docs/index.html` — sidan, fristående HTML (engelska), länkar till `igelkott.css` och `img/`. Google Fonts (Inter) laddas utifrån.
- `docs/igelkott.css` — kopia av `IgelkottDesign/dist/igelkott.css`.
- `docs/img/` — 12 bilder, 820 kB: nio väggar (`wall_A0xxCxxx.jpg`, mitten av 8K-väggen 1:1, Rec.709 för webben),
  `livefx_nod.jpg`, `livefx_eq2d.jpg` (Free Run-testet) och `livefx_panel.jpg` (nodens panel, A013C004, ACEScct).
- `AGENTS.md` och `PROJECT.md` har en rad om sidan.

Sidan är kollad i webbläsare på m3ultra via `python3 -m http.server` (alla bilder 200, ingen vågrät rullning,
teckenkodningen rätt).

## Vad jag förväntar mig att du gör

- [x] `git status` — kontrollera att bara `docs/index.html`, `docs/igelkott.css`, `docs/img/*.jpg`, `AGENTS.md`,
      `PROJECT.md` och denna handoff är nya/ändrade (inte `Ref-Eric/`).
- [x] Committa och pusha till `main`.
- [x] Slå på Pages från `main` och `/docs`:
      `gh api -X POST repos/IgelkottPlates/IgelkottFisheye2D/pages -f "source[branch]=main" -f "source[path]=/docs"`
      (finns Pages redan: `-X PUT .../pages` med samma fält).
- [x] Verifiera att https://igelkottplates.github.io/IgelkottFisheye2D/ visar sidan med bilder. Jekyll gör också
      `docs/*.md` till sidor; det är okej (de är redan publika i repot). Ingen `.nojekyll` behövs, och den skulle
      ändå inte synkas via Drive (punktfiler).
- [x] Skriv in adressen i `PROJECT.md` (och gärna en länk i `README.md`), flytta handoffen till `done/`.

## Bakgrund och länkar

- Samma sida som privat artefakt: https://claude.ai/artifact/HzvMBZcBucvaWkRFz9CtVn (Version 8).
- Git bara på ERIC-DESKTOP: `PROJECT.md`, avsnittet Git.

## Anteckning

Gjort 2026-11-24 på ERIC-DESKTOP: commit e6c3d49 pushad, Pages påslaget från `main` `/docs`, byggt och sett på
https://igelkottplates.github.io/IgelkottFisheye2D/ (alla bilder laddas). Adressen i PROJECT.md och README.md.
