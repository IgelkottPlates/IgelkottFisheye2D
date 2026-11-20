@AGENTS.md

# Claude-instruktion för IgelkottLiveFXFisheye

> **Bootstrap-check:** Om du svarar på något innan du har läst
> `PROJECT.md` i denna mapp och `../_atlas/README.md` — säg det till
> användaren först och be om att få göra det. Cowork auto-laddar inte
> projektkontraktet. Den kanoniska första-meddelande-prompten finns i
> `../_atlas/templates/SESSION_START.md`.

Du jobbar med ett Igelkott-projekt som bor under **Synology Drive
Client-mappen**, `~/Library/CloudStorage/SynologyDrive-*/Igelkott Appar/IgelkottLiveFXFisheye/`.

Globba `SynologyDrive-*` — rotnamnet är per maskin och godtyckligt
(`-Studios` på m3max, `-M1Ultra` på m1ultra, `-M4mini` på m4mini) och får
aldrig hårdkodas, varken i paths du skriver eller i build-/deploy-scripts.
Drive Client är single source-of-truth. Använd **INTE** SMB-monteringen
`/Volumes/homes/Igelkott Studios AB/...` — den övergavs 2026-05-02 för att
undvika sync-konflikter och path-divergens mellan Macar. Se
`../_atlas/README.md` och `../_atlas/knowledge/maskiner/README.md`.

## Börja alltid med

1. Läs `PROJECT.md` här i mappen — syfte, stack, status, hemmamaskin.
2. Läs `../_atlas/README.md` om du inte redan har ekosystemets spelregler
   i kontexten.
3. Skanna `../_atlas/knowledge/INDEX.md` för att se vilka delade lärdomar
   som finns. Läs specifikt de filer som `PROJECT.md` länkar till.
4. Om `HANDOFF/` finns och innehåller filer som inte ligger i
   `HANDOFF/done/` — läs dem. Det är meddelanden från andra projekt med
   åtgärder för detta projekt. Sammanfatta för användaren och föreslå
   hanteringsordning innan du går vidare.

## Arbetsregler för det här projektet

- **Räkningen är IgelkottStages.** Shaders ska ge exakt samma källpunkt som IgelkottStages fisheye-väg: väggens kamera
  (`StageProtocol/CameraCost.rotation`; FOV är däremot vågrät över väggens bredd sedan 0.18, Erics beslut) och objektivet (`_shared/IgelkottFisheyeLens`,
  `FisheyeLens.point`, nadir som (x, −y, −z)). Ändras något där — ändra i `shader/`, kör `python tools/build_shaders.py`
  och provet. Redigera aldrig `matchbox/` eller `pixera/IgelkottFisheye.glsl` för hand.
- **Provet före varje leverans:** `python tools/verify_windows.py` (Windows) ritar båda utgåvorna på riktigt och jämför
  varje pixel med Stages formler; gränsen är 0,5 källpixlar vid 8040. `python3 tools/verify_mac.py` (Mac) kör samma fall
  för Live FX-utgåvan (CGL, GLSL 1.20; PIXERA bara på Windows); `build-app.sh` kör det sedan 0.18.
- **GLSL 1.20 och 4.50 samtidigt.** Live FX översätter Matchbox-shaders till Metal på Mac och kör OpenGL på Windows;
  PIXERA kör 4.50. `shader/core.glsl` håller sig till det båda läser (inga bitoperationer på heltal, inga arrayer).
- **Gissa aldrig hur Live FX beter sig.** Det som bara syns i Live FX (nodens utformat, bildens orientering, om ett klipp
  går att läsa) prövas i Live FX och skrivs in i PROJECT.md med datum. Radordningen beror på klippets format (`.mov`
  uppifrån, PNG nerifrån, 2026-11-19); Flip Vertical finns inte sedan 0.14.

## Inkommande handoff (`HANDOFF/`)

Filer i `HANDOFF/` är åtgärder andra projekts Claude/användaren har
skickat hit. Hantering:

1. Läs alla pending-filer (de som inte ligger i `HANDOFF/done/`).
2. För varje meddelande: bekräfta innehåll med användaren, agera på
   `## Vad jag förväntar mig att du gör`, verifiera resultat.
3. Sätt `status: done` i frontmattern.
4. Flytta filen till `HANDOFF/done/<originalnamn>.md`.
5. Om du inte kan slutföra direkt — sätt `status: acknowledged`, lägg
   en `## Anteckning` längst ner med vad som blockerar, och låt filen
   ligga kvar i `HANDOFF/`.

## När du ska skicka en handoff till ett annat projekt

Triggers (skicka när detta händer i detta projekt):

- Du bryter en kontrakt-yta (API, fil-format, namnkonvention) som ett
  annat projekt konsumerar.
- Du deprekerar något som annat projekt använder.
- Du introducerar ett nytt event/anrop/data-flöde som annat projekt
  kommer att se.
- Du upptäcker ett problem i annat projekts data eller drift som du
  själv inte kan fixa.

Hur:

1. Kopiera `../_atlas/templates/HANDOFF.md.template`.
2. Spara som `../<MottagarProjekt>/HANDOFF/ÅÅÅÅ-MM-DD-<detta-projekt>-<topic>.md`.
3. Fyll i frontmatter (urgency, deadline, status: pending) och brödtext.
4. Berätta för användaren att handoffen är skickad — de kan välja att
   öppna mottagarens session direkt eller vid nästa tillfälle.

## När du lär dig något nytt

- **Projektspecifikt** → skriv in i `PROJECT.md` eller kodkommentar.
- **Tidlös fakta för flera projekt** (system, API, maskin, integration)
  → skriv till rätt fil i `../_atlas/knowledge/<domän>/`. Om filen inte
  finns, skapa den. Uppdatera `_sist verifierat: ÅÅÅÅ-MM-DD`.
- **Åtgärd som specifikt projekt måste utföra** → handoff (se ovan), inte
  knowledge.

## När du avslutar en session

- Uppdatera `PROJECT.md` → "Senast migrerat" / "Nuläge" om något ändrats.
- Om projektets rad i `../_atlas/projects.yaml` är inaktuell — uppdatera
  den.
- Om dina ändringar utlöste handoff-triggers — skicka handoff till
  berörda projekt innan du säger "klart".

## Version vid varje deploy (atlas regel #13)

`CFBundleVersion` ändras automatiskt vid varje deploy (tidsstämpel i
`build-app.sh`). `VERSION`-filen i projektroten höjs vid varje
användarsynlig ändring innan du deployar — glöm inte det när du säger
"klart". Ett deploy-skript som inte ändrar build-numret är trasigt.

## IgelkottSuit (atlas regel #12)

Om projektet producerar ett körbart program ska det rapportera till
sviten: `deploy-launcher.sh` → `../_applaunchers/<Namn>.app.zip`,
`CFBundleVersion` som ändras per deploy, rad i `../_atlas/projects.yaml`
och en post i `../_atlas/suite.yaml` (ingen ombyggnad av Suit behövs). Kontrakt + checklista:
`../_atlas/knowledge/macos/igelkottsuit-contract.md`. Säg aldrig "deployat"
förrän programmet syns som "Aktuell" i Suit.

## Vad du INTE ska göra

- Skapa inte en egen `Backup/`-mapp. Synology versionerar nattvis.
- Duplicera inte kunskap som redan finns i `_atlas/knowledge/`. Länka.
- Döp inte projekt efter maskin. Lägg maskinspecifik konfig under
  `Config/<maskin>.json` istället.
