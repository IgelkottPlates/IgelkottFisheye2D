---
from: IgelkottStage1
to: IgelkottLiveFXFisheye
date: 2026-11-19
deadline: när det passar
urgency: normal
topic: Bygg Auto för kamera och nadir/zenit ur pixeltaggen, en källa för Matchbox och Pixera, och prova i Live FX
status: acknowledged
---

# Från IgelkottStage1 till IgelkottLiveFXFisheye: pixeltaggen för kamera och nadir/zenit

## Vad har hänt

Eric 2026-11-19 vill att shaderpaketet till Live FX och Pixera (IgelkottLiveFXFisheye) blir så nära automatiskt som möjligt för
nadir/zenit och PYXIS/Venice: "ja, skriv förslaget 1 och skicka handoffarna", och ja till att Darkroom och Fisheye to Equi skriver
taggen. "sen ska det testas i live fx".

En shader ser bara pixlar och kan inte läsa QR-koden. Förslaget: bredvid hörnmärkets QR-kod skrivs en **pixeltagg**, två rader om tio
svartvita celler (0,012 av sidan) i hörnrutan 0,14 × 0,14, under QR-koden, i hörnet uppe till vänster och nere till höger. Cell 0 och 1
är vit och svart referens; sedan version, kamera (PYXIS 12K, Sony Venice 2, Z-Cam E2 S6), nadir, justerad, horisonten inbränd och en kontrollsumma.
Hela förslaget, med platser och bitar: `IgelkottLiveFXFisheye/PROJECT.md`, avsnittet "Förslag: kameran och nadir/zenit automatiskt (pixeltaggen, 2026-11-19)".

Allt ligger utanför bildcirkeln och inne i hörnrutan som Stage 1 redan maskar, så Stage 1 behöver ingen ändring. Stage 1 läser fortsatt
QR-koden.

**Z-Cam E2 S6 (Eric 2026-11-19: "den måste stödja Z-Cam E2 S6 också även fast den inte är byggd än"):** taggen och shaders ska ha plats för
en tredje kamera från början: kamerakoden 3 = Z-Cam E2 S6 (0 okänd, 1 PYXIS 12K, 2 Sony Venice 2), i taggen, i `LensMark`-profilen och i
reglaget Camera. Linsmodellen för Z-Cam E2 S6 finns inte än; tills den finns ska en fil med koden 3 inte spelas med en annan kameras modell
tyst (shadern faller tillbaka på valet för hand och Debug säger varför). Koden får inte behöva en ny taggversion när modellen kommer.

## Vad jag förväntar mig att du gör

- [ ] Bygg förslaget i PROJECT.md: Camera och Pointing med Auto (taggen) och reserv för hand, nadirvändningen, Debug-läget, en gemensam källa för Matchbox och Pixera, och `tools/verify.swift` mot Stage 1:s linsmodell (nadir och Venice inräknade).
- [ ] Prova i Live FX (Eric: "sen ska det testas i live fx") på en nadirplåt (A001C016, Free Demo 2025) och en Venice-plåt (A004C002) när de har taggen, och på en fil utan tagg (valet för hand gäller).
- [ ] Vänta med kantutjämningen tills Stage 1:s mätning av moarén i A014C006 finns.

## Bakgrund och länkar

- `IgelkottLiveFXFisheye/PROJECT.md`, avsnittet "Förslag: kameran och nadir/zenit automatiskt (pixeltaggen, 2026-11-19)"
- Hörnmärket och `pointing:`: `_shared/IgelkottFisheyeLens/Sources/IgelkottLensMark/LensMark.swift`, Stage 1 KRAV SPEL1-19.
- Samma handoff gick till IgelkottMotion, IgelkottDarkroom, IgelkottFisheyetoEqui och IgelkottLiveFXFisheye.

## Tillägg 2026-11-19: Erics reglage

Eric har bestämt reglagen och delningen: Mode (se sista raderna), Plate Auto/Manual, Yaw, Pitch, Roll, FOV, Lens Offset X/Y,
Manual med Camera och Pointing, och Split (samma plåt, egen vägg per halva, skarp gräns, för LED). Stab tas bort. Se "Reglagen" i PROJECT.md.
- Saknas taggen i Auto: en liten varningssymbol i bildens hörn, och PYXIS 12K och Zenith gäller. Annars ritas inget (Eric: "gör som du föreslår").
- Mode: Wall och Equirect i båda programmen (Eric: "då ska båda med"); inga 3D_Screens, ingen Tracking view eller Fisheye (stabilize).
- Pixera behåller 3D_Screens för böjda väggar, en omsampling (Eric: "ok, ja den skarpare bilden"). Pixera: Wall, Equirect och 3D_Screens. Live FX: Wall och Equirect.

## Anteckning

IgelkottLiveFXFisheye 2026-11-19 (0.14): byggt — Plate Auto/Manual, Camera (PYXIS, Venice, Z-Cam utan modell → varning), Pointing med nadirvändningen (x, −y, −z), varningstecknet, Mode Wall/Equirect, Split; en källa (`shader/`, `tools/build_shaders.py`) för Matchbox och PIXERA. `tools/verify_windows.py` jämför båda med `FisheyeLens.point` (61 fall, 0,026 px). Inget Debug-läge (Erics reglage). **Kvar:** provet i Live FX på A001C016 och A004C002 med taggen (inga taggade riktiga filer här än), `verify.swift` på Mac, kantutjämningen (väntar på er mätning).

Live FX 2026-11-19 (kväll, Windows): noden sedd. På en `.mov` står väggen rätt, Auto utan tagg ger varningen, Split fungerar.
Taggen läses i Live FX (provplåtar i PNG: PYXIS-zenit och Venice-nadir ger samma vägg). PNG-klipp kommer däremot vridna 180°
(Live FX lägger dem nerifrån); öppet för Eric. Kvar: riktiga taggade filer (A001C016, A004C002).
