---
from: IgelkottLiveFXFisheye (m3ultra)
to: IgelkottLiveFXFisheye (ERIC-DESKTOP, git)
date: 2026-11-24
deadline: asap
urgency: normal
topic: Galleriet på produktsidan — en bild per demoplåt, pusha docs/
status: done
---

# Från m3ultra till ERIC-DESKTOP: en bild per plåt på GitHub Pages-sidan

## Vad har hänt

Eric 2026-11-24: "Vi gör primärt bil. Se till att varje plate i demon repsenteras en gång."
Galleriet i `docs/index.html` har nu åtta bilder, en per gratisplåt (A011C001 är toppbilden):
`g1_A013C004`, `g2_A014C001`, `g3_A004C006`, `g4_A005C006`, `g5_A004C002`, `g6_A014C006`, `g7_A007C001`,
`g8_A001C016`. De gamla `g1_A011C001` … `g6_A014C001` är borttagna ur `docs/img/`. `PROJECT.md` är uppdaterad.
Sett i webbläsaren på m3ultra: alla bilder laddas, ingen vågrät rullning.

## Vad jag förväntar mig att du gör

1. `git status` — väntat: ändrade `docs/index.html`, `PROJECT.md`; nya och borttagna bilder i `docs/img/`; den här filen.
2. `git add -A docs PROJECT.md HANDOFF` (så att de borttagna bilderna följer med) och commit, t.ex.
   "Product page: one gallery still per demo plate".
3. `git push`.
4. Öppna https://igelkottplates.github.io/IgelkottFisheye2D/ efter någon minut: galleriet ska ha g1_A013C004 … g8_A001C016
   och ingen g1_A011C001 eller g4_A011C001.
5. Skriv commit-hashen i `PROJECT.md` (raden "väntar på push"), sätt `status: done` och flytta filen till `HANDOFF/done/`.

## Anteckning

Gjort 2026-11-24 på ERIC-DESKTOP, commit 332bcaf. m3ultras `docs/index.html` kom aldrig fram via Drive (inga konfliktkopior);
den krockade troligen med f53d1fb kl. 09:32, där första stycket skrevs om på Erics begäran ("IgelkottFisheye is a free plug-in
for Assimilate Live FX and PIXERA ... It replaces the usual route ..."). Galleriet skrevs därför in här efter listan ovan, med
alt-texter ur bilderna, och de sex gamla bilderna togs bort. På sidan: g1_A013C004 … g8_A001C016, alla 10 bilder laddas.
**m3ultra: utgå från filen som den är nu i Drive, inte din lokala kopia.**
