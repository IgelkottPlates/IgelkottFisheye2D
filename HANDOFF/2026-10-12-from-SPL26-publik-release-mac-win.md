---
from: SPL26 (Cowork-planering av Starting Pixel Live 26)
to: IgelkottLiveFXFisheye
date: 2026-10-12
deadline: öppen (se frågor till Eric nedan)
urgency: medium
topic: Publik release på igelkottstudios.com — Mac och Windows, bra användarupplevelse för främlingar
status: acknowledged
---

# Från SPL26: gör IgelkottFisheye delbar för alla Live FX-användare

## Vad Eric vill (2026-10-12)

> "jag vill dela denna plugin på hemsidan så den måste fungera med mac/win med en bra användarupplevelse"

Målgrupp: Live FX-användare som aldrig hört talas om Igelkott, på Mac **och** Windows, ofta nybörjare
i Live FX. De laddar ner från igelkottstudios.com och ska klara sig utan oss.

## Läget i dag (det som är Igelkott-internt)

- Leverans via IgelkottSuit och `_applaunchers`; appen är ett bash-skript (`app/IgelkottLiveFXFisheye.sh`)
  som kopierar shadern och kör `directionlock` (Swift, macOS).
- Inställningar via `~/Movies/IgelkottFisheye Direction Lock/installningar.txt` med flaggor — svenska,
  textfil, kräver att man vet vad `--start` och `--view` betyder.
- Dialogrutor och PROJECT.md på svenska. Matchbox-filnamnet `IgelkottFisheye2D`, panelen visar IgelkottFisheye.
- Bara provat på m3max (Live FX 9.9.1212, macOS). Windows-sökvägen för Matchbox är inte känd här.

## Vad jag förväntar mig att du gör

### 1. Två delar, båda för Mac och Windows
- [ ] **Filtret** (Matchbox-noden): ta reda på var Live FX på **Windows** läser Matchbox-shaders och om
      GLSL → Metal/DX-översättningen ger samma bild. Prova verify-fallen där om det går; skriv lärdomen i
      `_atlas/knowledge/assimilate/matchbox.md`.
- [ ] **Stabiliseringsverktyget** (dagens `directionlock`): måste köra på Windows också. Välj stack så att
      **en** kodbas ger Mac + Win (motivera valet i PROJECT.md; Swift-skriptet är macOS-bundet).

### 2. Installation som en främling klarar
- [ ] Mac: signerad och **notariserad** installer/app (ingen `xattr`, ingen Suit). Windows: installer
      (gärna signerad så SmartScreen inte skrämmer). Båda: hitta Live FX automatiskt, be om admin bara vid behov,
      säga tydligt "starta om Live FX" efteråt.
- [ ] Avinstallation och uppdatering (versionsnummer synligt i noden eller i appen).

### 3. Stabiliseringen som ett riktigt GUI, inte en textfil
- [ ] Ett litet fönster: dra in (eller välj) Offset X/Y-CSV:erna från Curve Editor → fält för trackingvyns
      FOV/bredd/höjd (förifyllt 60 / 3840 / 2160) → **klicka på startpunkten** i en bild/ruta i stället för
      `--start`-pixlar (eller läs den automatiskt om det går) → reglage "Smoothing" (sekunder) →
      **förhandsvisa kurvan** (väg vs skak, spikar markerade) → Spara `Stab Yaw.csv` där användaren vill.
- [ ] Flaggorna i `installningar.txt` blir inställningar i GUI:t; textfilen behövs inte för vanliga användare.
- [ ] Felmeddelanden som säger vad man ska göra ("Hittar bara Offset X — exportera Offset Y också").

### 4. Engelska och dokumentation
- [ ] All text för användare på **engelska**: nodens tooltips, dialoger, GUI, README.
- [ ] Kameraförval för Sensor Height (PYXIS 12K 23,32; Venice 8.6K 23,9; fält för egen kamera).
- [ ] En kort Quick Start (PDF eller webbsida) med de två flödena: "fisheye on a wall" och "remove the shake".
      Underlag finns: SPL26-genomgångens 17 annoterade skärmbilder i
      `Dokument/SPL26 Keynote/01 Session 10.05/Livedemo Live FX/Genomgang/` (01–16.jpg + 14b.jpg),
      och metoden i `_atlas/knowledge/assimilate/fisheye-stabilisering-trackingvy.md`.
- [ ] Begränsningarna rakt ut: kameran rakt upp, ett objektiv per kurva (Entaniya HAL 250 i dag), kvadratiska
      klipp, pan-stabilisering för rakare vägar.

### 5. När det finns en nedladdningsbar build
- [ ] Skicka handoff till `igelkottstudios-com` (det projektet har ingen `HANDOFF/`-mapp än — skapa den):
      nedladdningssida med Mac/Win-länkar, version, systemkrav, Quick Start, licens.

## Frågor till Eric innan release (ställ dem, gissa inte)

1. Gratis eller betald? E-post för nedladdning (nyhetsbrevet) eller fri länk?
2. Licens/villkor (fri användning, kommersiellt, ingen garanti)?
3. Ska det vara ute till/annonseras på Starting Pixel Live 14 okt (Demo Jam), eller senare?
4. Vilket namn utåt: "IgelkottFisheye" för noden och vad för verktyget?
5. Support: vart hör användare av sig?

## Underlag

- `PROJECT.md` (Stabilisera en plåt: trackingvy → Stab Yaw), `tools/directionlock.swift`, `tools/verify.swift`.
- Testdata: `~/Movies/IgelkottFisheye Direction Lock/` (Track vy / Genomgang Offset X/Y + Stab-facit).
- Live FX-projekten `SPL26 Genomgang` och `Offroad stab_aces` på m3max.

## Anteckning

IgelkottLiveFXFisheye 2026-10-12:

- **Byggt (punkt 3 och delar av 4):** `stabilizer/index.html` 1.0 — stabiliseringen som en webbsida på engelska. Dra
  in Offset X/Y, fält för FOV/bredd/höjd (60 / 3840 / 2160), klicka på startpunkten (skärmbild av vyn kan dras in),
  Smoothing-reglage, förhandsvisning av väg och skak med spikar markerade, Spara Stab Yaw.csv. Felmeddelanden som säger
  vad man ska göra. Samma kurva som appen: `node tools/test-stabilizer.mjs` mot facit, skillnad 0,0000005°.
- **Stackvalet (punkt 1):** en HTML-fil i stället för en app. En kodbas för Mac och Windows, ingen installation, och
  ingenting att signera — motiverat i PROJECT.md, Publik release.
- **Inte provat:** av Eric, på Windows, och importen i Live FX av en fil sparad från sidan.
- **Blockerar:**
  - Filtret på Windows: sökvägen för Matchbox står inte i Assimilates dokumentation; kräver en Windows-dator med
    Live FX. Samma för att pröva bilden där.
  - Mac-installerare: inget Developer ID-certifikat i nyckelringen på m3max.
  - Ändringar i noden (kameraförval för Sensor Height) väntar till efter demon 2026-10-14, så att en ny filterversion
    inte nollställer något i demoprojekten.
  - Quick Start väntar på de omgjorda skärmbilderna.
  - Erics svar på de fem frågorna (ställda 2026-10-12).
- Ingen ny version är lagd i `_applaunchers`.

## Anteckning 2

2026-10-12 (senare): Eric har bestämt zip utan installerare och signering, och Windows är pausat
(`…-zip-leverans-och-hint-bugg.md`). Punkt 2 (installerare) och blockeraren om Developer ID faller därmed. Stabilizer-
sidan är 1.1. Nytt: Auto Stabilize (0.10) tar bort alla inmatningar men är ett Mac-program — om det ska med i den
publika leveransen måste det signeras eller byggas om för webbläsare. Öppet för Eric.

## Anteckning 3

2026-10-28 (ERIC-DESKTOP, Windows): punkt 1 Filtret på Windows delvis gjord. Matchbox-mappen är
`C:\ProgramData\Assimilator\plugin64\Matchbox\shaders`; Live FX kör OpenGL där. `tools/verify_windows.py` går igenom
alla fall på AMD RX 9070 XT. Installerare `windows/Install IgelkottFisheye.cmd`; noden installerad på ERIC-DESKTOP.
Kvar: Erics prov i Live FX på Windows (syns noden, radordningen), provet på NVIDIA.
