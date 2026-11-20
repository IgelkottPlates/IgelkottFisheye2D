---
from: IgelkottSuit
to: IgelkottLiveFXFisheye
date: 2026-10-30
deadline: när det passar
urgency: low
topic: Städa byggmappar och sortera projektmappen enligt atlas
status: done
---

# Från IgelkottSuit till IgelkottLiveFXFisheye: städa byggmappar och sortera mappen

## Vad har hänt

Eric 2026-10-30: "skriv handoff till alla appar att städa upp i sina byggmappar och sortera enligt atlas regler".
IgelkottSuit gick igenom alla projektmappar i Drive och byggmapparna i `~/Library/Caches` på **m3max**. Samma
handoff har gått till alla projekt. Fynden nedan gäller bara m3max — kontrollera också maskinen du kör på
(m3ultra, m1ultra, m4mini har egna `~/Library/Caches`).

## Hittat i ditt projekt (m3max, 2026-10-30)

- Byggresultat i Drive: `dist` (0.1 MB)

## Reglerna

1. **Inga byggresultat i Drive.** `.build/`, `build/`, `DerivedData/`, `dist/`, `node_modules/`, `.venv*/`,
   `__pycache__/`, `.pytest_cache/`, Gradles `app/build/` och färdiga `.app`/`.app.zip` ska inte ligga i projektmappen.
   De synkas till alla Macar och ger modulcache-krockar mellan maskiner.
   Se `../_atlas/knowledge/synology/spm-build-dir-in-synced-folder.md` och
   `../_atlas/knowledge/android/gradle-build-out-of-drive.md`.
2. **Byggkatalogen är `~/Library/Caches/Igelkott/<Projekt>`**, en per projekt och maskin. Byggskriptet ska peka dit
   (`--scratch-path`/`--build-path`, `-derivedDataPath`, `GRADLE_USER_HOME`, venv-sökväg). Varianter (prov, grenar)
   som undermappar där, inte som `~/Library/Caches/<Projekt>-build` eller `Igelkott/<Projekt>-test`.
3. **Artefakten bor bara i `_applaunchers/` eller `_releases/`** (regel 12). Deploy-skriptet zippar från byggkatalogen
   i Caches, inte från en `build/` i Drive.
4. **Ingen `Backup/`-mapp** (regel 6) — Synology versionerar nattvis. Gamla kopior tas bort; behövs något ur dem, flytta
   det till rätt plats först.
5. **Projektroten ska gå att läsa** (regel 15, DOX). I roten: `PROJECT.md`, `CLAUDE.md`, `AGENTS.md`,
   `ARCHITECTURE_CHECKLIST.md`, `VERSION`, bygg/deploy-skript, paketfil och källmappar. Provfiler, mätrapporter,
   skärmbilder, loggar och utkast till undermappar (t.ex. `docs/`, `samples/`, `loggar/`, `ref-from-Eric/`).
   Lösa `PROMPT_TO_*`/handoff-utkast flyttas till mottagarens `HANDOFF/` eller till `HANDOFF/done/`.
   Uppdatera `AGENTS.md` (barnindex) och `PROJECT.md` när mappar flyttas.
6. **Inget som behövs får bara finnas i en cache eller i `/tmp`** (regel 14). Provdata som ska sparas
   (mätserier, referensbilder) flyttas till Drive eller NAS innan cachen rensas.
7. **Suit 0.16 sparar appens unika filer i Drive vid avinstallation** (`_archive/avinstallerat/`). Allt appen har
   i `~/Library` som inte är känd cache räknas som unikt. Har appen stora data som den själv kan hämta eller
   återskapa (media, buffertar), ange dem i sin post i `../_atlas/suite.yaml` med
   `regenerable: Library/Caches/<App>/<mapp>, …` — annars kopieras de till Drive. Blanda inte unika filer
   (utkast, läge, mätdata) med återskapbara i samma mapp. Se `../_atlas/knowledge/macos/igelkottsuit-contract.md`.
8. **`.gitignore`/Drive-filter:** lägg till byggmapparna så de inte kommer tillbaka.

## Vad jag förväntar mig att du gör

- [ ] Ändra byggskripten så att inget byggs i Drive (regel 1–3). Bygg en gång och kontrollera att projektmappen är
      oförändrad efteråt.
- [ ] Ta bort byggresultaten i Drive som står under "Hittat" (de återskapas av bygget).
- [ ] Rensa dina egna byggmappar i `~/Library/Caches` som inte längre används. **Bara ditt projekts egna mappar**,
      aldrig `~/Library/Caches/Igelkott` som helhet eller ett annat projekts. Kontrollera först att mappen inte
      innehåller en montering (Stages kamerakort är en SMB-montering i cachen) — `find <mapp> -xdev` och jämför med
      `mount`.
- [ ] Sortera projektroten (regel 5) och ta bort `Backup/`-mappar (regel 4).
- [ ] **Fråga Eric innan** du raderar provdata, mätserier eller något över ~1 GB som inte är ren byggcache.
- [ ] Ange `regenerable:` i suite.yaml om appen har återskapbara data i `~/Library` (regel 7).
- [ ] Skriv i `PROJECT.md` vad som flyttades och raderades, och hur mycket som frigjordes.
- [ ] Klart när: projektmappen innehåller inga byggresultat efter ett bygge, och Suit visar appen som vanligt.

## Bakgrund och länkar

- `../_atlas/README.md` regel 6, 12, 14 och 15
- `../_atlas/knowledge/synology/spm-build-dir-in-synced-folder.md`
- `../_atlas/knowledge/synology/drive-client-modified-during-build.md`
- `../_atlas/knowledge/macos/igelkottsuit-contract.md`

## Avslut

IgelkottLiveFXFisheye 2026-11-11 (m3max):
- `dist/` (Windows-paketet, 20 KB) → `_releases/IgelkottFisheye/IgelkottFisheye-Windows.zip`; `windows/build-package.ps1`
  bygger dit i stället. `tools/__pycache__` borttagen. `_releases/AGENTS.md` har fått raden.
- Mac-bygget (`build-app.sh`, `deploy-launcher.sh`, autoyaw med `--build-path`) bygger i
  `~/Library/Caches/Igelkott/IgelkottLiveFXFisheye`; projektmappen hade 52 filer före och efter bygget av 0.13.
- Caches: bara `Igelkott/IgelkottLiveFXFisheye` (i bruk, ~160 MB). Inga gamla mappar för projektet att ta bort.
- Ingen `Backup/`, roten sorterad, inga data i `~/Library` (ingen `regenerable:`).
- Inte kontrollerat: m3ultra, m1ultra, m4mini.
