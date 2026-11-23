# IgelkottLiveFXFisheye

DOX-kontrakt för denna mapp. Läs `_atlas/README.md` regel 15 först.

## Syfte

- Matchbox-nod för Assimilate Live FX (IgelkottFisheye2D) och samma effekt för PIXERA, som spelar fisheyen (PYXIS 12K
  eller Sony Venice 2, zenit eller nadir, vilken storlek som helst) direkt på väggarna, som IgelkottStage gör. Kameran
  och riktningen läses ur pixeltaggen (Plate Auto) eller väljs för hand (Plate Manual).

## Ägarskap

- Status, stack och historik: `PROJECT.md`. Arbetsregler för Claude: `CLAUDE.md`.
- `shader/` — källan till båda utgåvorna: `core.glsl` (linsen, nadirvändningen, pixeltaggen, varningstecknet),
  omslagen `matchbox.glsl` och `pixera.glsl`, panelen `IgelkottFisheye2D.xml`. Ändras här, aldrig i de gjorda filerna.
- `matchbox/` och `pixera/IgelkottFisheye.glsl` — gjorda av `tools/build_shaders.py` (kamerornas tal ur
  `_shared/IgelkottFisheyeLens`, versionen ur `VERSION`). `pixera/README.txt` skrivs för hand.
- `stabilizer/` — den publika stabiliseringssidan (en HTML-fil, engelska). Noden har inga Stab-reglage sedan 0.14.
- `README.md` och `CONTRIBUTING.md` — repots framsida och regler för bidrag (engelska, GitHub).
- `shader/cameras.json` — kamerornas tal, kopierade ur `_shared` av `build_shaders.py` så att en klon kan bygga; aldrig
  för hand.
- `docs/MAC-TEST.md` — testlistan för Live FX på Mac (engelska); resultaten skrivs i `PROJECT.md`.
- `docs/THREADRIPPER-TEST.md` — uppspelningstestet (NotchLC, Free Run) på Threadripper-datorn, Windows, 6 GB/s-disk
  (engelska); resultaten skrivs i `PROJECT.md`.
- `docs/PLAYERS.md` — kartan över andra spelare (Nuke, Unreal, disguise, ISF med flera) och hur en ny port läggs till
  (engelska, för bidragsgivare).
- `Ref-Eric/` — referenser från Eric (PIXERA:s egen `Equirectangular.glsl.txt`).
- `app/` — installationsappen (Mac), som också kör Direction Lock. `windows/` — installeraren för Windows (`.cmd` +
  PowerShell, `README.txt`) och `build-package.ps1` → `_releases/IgelkottFisheye/IgelkottFisheye-Windows.zip`.
- `tools/` — `build_shaders.py`, proven `verify_windows.py` (Windows, båda utgåvorna), `bench_windows.py` (Windows, shaderns tid på grafikkortet), `bench_notchlc.py` (Mac och Windows, Store-klippen i NotchLC: storlek, läsning, max bild/s från disken), `compare_eq2d.py` (noden mot FisheyetoEqui + Eq->2D på 8K-duk), `verify_mac.py` (Mac, samma fall för Live FX-utgåvan,
  läser och kör `verify_windows.py` med CGL), `verify.swift` och
  `verify_pixera.swift` (Mac, före 0.14), `make_testplates.py` (provplåtar med och utan tagg), `autoyaw/` (Swift-paket:
  klippet → Stab Yaw), `directionlock.swift` (tracker-CSV → Stab-kurvor), `fixtures/` (facit för Direction Lock).

## Lokala kontrakt

- Räkningen ska stämma med IgelkottStages modell för objektivet (`FisheyeLens.point`, nadir som (x, −y, −z)).
  Kamerornas tal kommer bara ur `_shared/IgelkottFisheyeLens`; proven jämför dem.
- Pixeltaggens regler (plats, bitar, CRC, kontrast) står bara i `PixelTag` i `_shared/IgelkottFisheyeLens`
  (`IgelkottLensMark`); `shader/core.glsl` följer den och `verify_windows.py` provar mot dess provvektorer.
- En plåt utan giltig pixeltagg spelas aldrig, inte heller med Camera/Pointing valda för hand (Eric 2026-11-23): svart,
  NOT AN IGELKOTT CLIP och varningstecknet.
- En kamera utan linsmodell (taggkod 4–7; ingen i listan sedan Z-Cam E2 S6 fick sin modell 2026-11-20) spelas aldrig
  med en annan kameras modell: svart och varningstecknet.
- FOV är den vågräta vinkeln från väggens vänstra till högra kant, med Split varje väggs egen bredd (Eric 2026-11-20:
  "90 grader för mig betyder 90 grader på horisonten"; till och med 0.17 lodrät som Eq->2D).
- Reglagen är Erics (2026-11-19, ändrade 2026-11-20): Camera och Pointing med "Auto (tag)" först (inget Plate-reglage),
  Offset X/Y (flyttar bilden efter projektionen, utbildens pixlar), Yaw, Pitch, Roll, FOV, Mode (Wall, Equirect), Split,
  Split Position, Right Yaw/Pitch/Roll/FOV, Right Offset X/Y (2026-11-20). Equirect: 360° över hela bredden, riktad
  med Yaw/Pitch/Roll, Split ger fönster i samma skala. Nya reglage kräver hans beslut.
- PNG-klipp stöds inte (Eric 2026-11-19: "inge stöd för png"): Live FX lägger dem nerifrån och väggen blir vriden 180°.
  Ingen Flip Vertical. Orienteringen provas på `.mov`.
- Shaders håller sig till det GLSL 1.20 och 4.50 båda läser: inga heltalsoperationer på bitar, inga arrayer.
- Bildcirkeln mäts aldrig här (Eric 2026-10-15: bara Darkroom hittar den).
- Filnamnet `IgelkottFisheye2D` byts inte; i panelen står IgelkottFisheye.
- `DEG_PER_PIXEL` (`stabilizer/index.html`) och `TRACK_SCALE` (`tools/directionlock.swift`) är samma tal;
  `node tools/test-stabilizer.mjs` fäller bygget annars.
- Stabilizer-sidan har inga fält att skriva tal i.
- Allt som en användare utanför Igelkott ser är på engelska.
- Licensen är Erics (2026-11-20): koden får användas, även kommersiellt, bara för att spela upp Igelkott-plåtar
  (Igelkott Film AB). Ingen öppen licens. Bolaget i allt utåt är Igelkott Film AB.
- Erics DL-formel finns kvar oförändrad: `ut[n] = (t[n] − t[n−1]) + k · ut[n−1]`.
- Program: rapporterar till IgelkottSuit och höjer version vid deploy (atlas regel 12 och 13).
- Artefakt: `_applaunchers/IgelkottLiveFXFisheye.app.zip` (Mac); `_releases/IgelkottFisheye/IgelkottFisheye-Windows.zip` (Windows).
- Inga byggresultat i projektmappen: Mac bygger i `~/Library/Caches/Igelkott/IgelkottLiveFXFisheye`, Windows-paketet
  sätts ihop i `%TEMP%` och läggs direkt i `_releases/`. Provplåtar läggs utanför projektmappen.

## Arbetsvägledning

- Före ett steg: sök på webben och läs `_atlas/` (knowledge och reglerna). Efter steget: verifiera visuellt i
  programmets GUI (Live FX, PIXERA), inte bara med provet (Eric 2026-11-19).
- Gamla projekt och gamla reglage behöver inte hållas vid liv (Eric 2026-11-19: "nu byggger vi något nytt").

## Verifiering

- `python tools/build_shaders.py --check` — de gjorda filerna stämmer med `shader/`
- `python tools/verify_windows.py` (Windows) — båda utgåvorna mot linsmodellen och pixeltaggen, plus MTF50 vid FOV 90 på 4K-duken (sned kant, ±0,02 mot modellen)
- `python tools/verify_windows.py . --canvas` (Windows) — LED-dukarna 4K, 8K och 16K × 2160 i full storlek
- `python tools/bench_windows.py` (Windows) — shaderns tid per bild vid 4K, 8K och 15360 × 2160, med och utan tagg
- `python3 tools/bench_notchlc.py --store … --work … --out …` — NotchLC-filernas tyngd; Live FX-delen (Free Run) i `docs/MAC-TEST.md` avsnitt 11
- `python3 tools/verify_mac.py` (Mac) — Live FX-utgåvan mot linsmodellen och pixeltaggen; `. --canvas` för dukarna
- `swift tools/verify.swift` och `swift tools/verify_pixera.swift` (Mac) — provar reglagen före 0.14; används inte längre
- `swift tools/directionlock.swift --test tools/fixtures`
- `autoyaw --selftest` (byggs av `build-app.sh`)
- `node tools/test-stabilizer.mjs`
- `./build-app.sh`

## Barnindex

- Inga barn-`AGENTS.md`.
