# IgelkottLiveFXFisheye

> **Bootstrap-check (för Claude):** Om du är på väg att svara utan att
> ha läst denna fil + `CLAUDE.md` + `../_atlas/README.md` —
> stoppa, säg det till användaren, och be om att få göra det. Cowork
> auto-laddar inte projektkontraktet. Se
> `../_atlas/templates/SESSION_START.md` för boot-prompten.

## Syfte

En Matchbox-nod för Assimilate Live FX, **IgelkottFisheye2D**, som spelar 8040 × 8040-fisheyen (PYXIS 12K + Entaniya
HAL 250) direkt på väggarna, som IgelkottStage gör (Eric 2026-10-05: "gör en plugin till livefx som spelar 8040x8040 som
vi gör"). Den ersätter Eq->2D Transformer på varje vägg i ett fisheyeklipp: samma Yaw, Pitch och Roll (FOV är sedan 0.18 vågrät, inte Eq->2D:s lodräta), men
källan samplas genom objektivets modell i stället för en equirect från FisheyetoEqui — en omsampling i stället för två.

## Stack

- Shadern: GLSL 1.20 + Matchbox-XML (`matchbox/`). Live FX 9.9 översätter den till Metal (SpaMatchbox).
- Auto Stabilize: Swift med AVFoundation och Accelerate (`tools/autoyaw/`), kompileras in i appen.
- Provet: Swift-skript med OpenGL (`tools/verify.swift`), kör på vilken Mac som helst.
- Stabilizer för publik release: en HTML-sida med JavaScript (`stabilizer/index.html`), provad med node.
- Leveransen: skript-app (`app/IgelkottLiveFXFisheye.sh`) som kopierar shadern till Live FX:s Matchbox-mapp, via
  IgelkottSuit — samma mönster som [IgelkottPlateDCTL](../IgelkottPlateDCTL/PROJECT.md).
- Kör på: Macarna med Live FX (m3ultra i dag). Hemmamaskin: central (Drive).
- **Git:** publikt repo (sedan 2026-11-20, Erics beslut) [IgelkottPlates/IgelkottFisheye2D](https://github.com/IgelkottPlates/IgelkottFisheye2D)
  (skapat 2026-11-20 på ERIC-DESKTOP, gren `main`). `.git/` ligger i Drive-mappen: committa från en maskin i taget.
  `Ref-Eric/` (PIXERA:s egna filer) och `pixera.zip` är utanför via `.gitignore`. Målet (Eric 2026-11-20): IgelkottFisheye
  i alla stora spelare — Live FX, PIXERA, Nuke med flera — och med hjälp från andra användare. Issues och Discussions på.
  Förberett för publikt 2026-11-20: `README.md`, `CONTRIBUTING.md` (engelska), kamerornas tal som kopia i
  `shader/cameras.json` (skrivs av `build_shaders.py` ur `_shared`; utan `_shared` läser bygget och provet kopian),
  PIXERA-kedjan i provet hoppas över utan `Ref-Eric/`. Licens: egen, `LICENSE` (Eric 2026-11-20: "får använda koden för att spela upp igelkottplates kommerciellt, inget annat"; ej granskad av jurist). Inte gjort: GitHub Actions (gh-inloggningen
  saknar scope `workflow`), ingen Release ännu (README pekar på Releases för Windows-zippen).

## Grundbeslut (Eric 2026-10-05)

- **En nod per vägg, som Stage** — i stället för Eq->2D på varje vägg (inte en nod per klipp till equirect).
- **Loadern senare:** IgelkottLiveFXLoader lär sig bygga projekt med noden först efter Erics prov i Live FX (läs av ett
  projekt där noden ligger, gissa inte formatet). Plattförskjutningen ur FisheyetoEquis kalibrering skrivs då av loadern.
- **Namn och leverans:** IgelkottLiveFXFisheye via Suit.

## Noden

Var: Live FX → Matchbox → shaders → **IgelkottFisheye2D** (filnamnet, som projekt och loadern pekar på; byts inte).
I panelen står **IgelkottFisheye** (fliken, 0.6). I nodträdet på samma plats som Eq->2D: direkt på mediet,
under väggens lager.

Reglagen från 0.14 (Eric 2026-11-19, se "Reglagen" under pixeltaggen; samma i PIXERA-effekten, som har Aspect i stället
för nodens storlek):

| Kolumn | Reglage | Vad |
|---|---|---|
| Plate | Camera | Auto (tag) (standard): taggens kamera; PYXIS 12K, Sony Venice 2, Z-Cam E2 S6 (egen linsmodell sedan 0.18) väljs för hand; en taggkod utan modell (4–7) ger svart och varningen. Auto utan giltig tagg: PYXIS 12K och varningstecknet uppe till vänster (0.15, Eric 2026-11-20: Plate-reglaget borta, Auto i listorna) |
| | Pointing | Auto (tag) (standard), Zenith, Nadir: nadir läses som (x, −y, −z), som Stage 1 och Motion. Auto utan tagg: Zenith och varningen |
| | Offset X/Y | Flyttar den färdiga bilden efter projektionen, utbildens pixlar (+X höger, +Y upp); med Split på bara vänstra väggens bild, Split-gränsen står kvar (0.15, Eric 2026-11-20: "offset ska vara efter projektion"). PIXERA: % av höjden. Objektivets mitt kan inte längre flyttas: plåten ska vara centrerad (Darkroom/Fisheye to Equi) |
| View | Yaw, Pitch, Roll | Som Eq->2D: yaw 0 = mitten av den equirect FisheyetoEqui gör, + = höger; pitch + = upp. Vänster vägg när Split är på |
| | FOV | Den vågräta vinkeln från väggens vänstra till högra kant; med Split varje väggs egen bredd (0.18, Eric 2026-11-20: "90 grader för mig betyder 90 grader på horisonten"). Till och med 0.17 lodrät över höjden, som Eq->2D ([eq2d-fov-framing](../_atlas/knowledge/assimilate/eq2d-fov-framing.md)) |
| | Mode | Wall eller Equirect: 360° över hela nodens bredd, samma grader per pixel på höjden, riktad med Yaw/Pitch/Roll (0.17; före 0.17 användes de inte); 2:1 utan Split och Yaw 0 är hela sfären som FisheyetoEquis equirect, bredare dukar beskärs upptill och nertill, förbi polerna svart. FOV används inte |
| Split | Split, Split Position | Två väggar ur samma plåt bredvid varandra, skarp gräns vid Split Position (% av bredden från vänster); varje halva har egen mitt. I Equirect är varje vägg ett fönster i samma skala riktat med sina egna Yaw/Pitch/Roll (0.17) |
| Right Wall | Right Yaw/Pitch/Roll/FOV, Right Offset X/Y | Högra väggen när Split är på; Right Offset X/Y flyttar dess bild som Offset (0.17, Eric 2026-11-20) |

Fast: 2 × 2 prov per pixel, bilderna uppifrån (Live FX på Mac och Windows). Borta i 0.14: Stab, Sensor Height, Lens Scale,
Quality, Flip Vertical, Custom-kameran, Fisheye (stabilize) och Tracking view. Avsnitten nedan om dem är historik.

Räkningen (samma som IgelkottStage): R = Ry(yaw) · Rx(−pitch) · Rz(roll), f = (höjd / 2) / tan(FOV / 2), riktningen genom
pixeln; objektivet pekar rakt upp, θ från zenit, r(θ) = k1·θ + k2·θ³ + k3·θ⁵ + k4·θ⁷, punkt = mitten + förskjutningen +
(d.x, d.z) · r(θ) / sin θ, svart utanför bildramen. Normerat mot 8040, så en förminskad källa ger samma bild.

### Annan kamera, samma objektiv (0.5)

Objektivets kurva är densamma i millimeter på sensorn. En annan sensor eller beskärning ändrar bara hur många
bildbredder kurvan tar. Två reglage, skalan = 23,32 / Sensor Height · Lens Scale:

- **Sensor Height mm** — höjden i mm av den sensoryta det kvadratiska klippet täcker. Är klippet hela bildens höjd är
  det kamerans inspelade bildhöjd ur databladet (för det inspelningsläge som användes, inte alltid hela sensorn).
  23,32 = PYXIS 12K open gate (8040 rader · 2,9 µm; Blackmagics "36 × 24" är avrundat).
- **Lens Scale** — fintrimning ovanpå, 1 = ingen. En rak linje (horisont, huskant) över skarven mellan två väggar ska
  vara rak och hänga ihop.

Mitten flyttas med Lens Offset X/Y (källpixlar vid 8040, alltså bråkdelar av bildbredden × 8040, oavsett klippets
storlek). Gäller bara kvadratiska klipp med samma objektiv; ett annat objektiv har en annan kurva och ett
icke-kvadratiskt klipp stämmer inte (shadern normerar båda ledderna mot samma tal). Offroad-plåten i SPL26-demon är
Venice 4096 × 4096 och spelas med PYXIS-skalan tills Sensor Height är satt.

| Kamera | Sensor Height mm | Lens Scale | Källa |
|---|---|---|---|
| PYXIS 12K open gate, 8040 × 8040 | 23,32 | 1 | FisheyeLens.pyxis12K |
| Sony Venice (Offroad-plåten, X-OCN 8.6K → 4096 × 4096) | 23,9 | 1 (inte trimmad) | Eric 2026-10-11. Stämmer med bildcirkeln: mätt radie 2086 px i klippet, modellen ger 2087 px vid 125° med 23,9 mm. Cirkelns mitt ligger på (2036, 2028), alltså **Lens Offset X ≈ −24, Y ≈ −39** (pixlar vid 8040) — inte satt eller provat i Live FX |

### Tracking view + Stabilizer-sidan (0.11 / sidan 2.0, huvudvägen)

Eric 2026-10-12: "live fx ska exportera stabiliserade keyframes, det är ok, men hur kan html sidan göra allt det
tekniska lättare tillsammans med pluginen?" och "bygg tracking view och förenklade sidan nu".

Felen kom av att sidan måste räkna om pixlar till grader och därför behövde FOV, bildstorlek och punktens startläge.
Nu gör noden bilden så att en pixel alltid är lika många grader:

- **Mode Tracking view i noden:** fast skala, `TRACK_SCALE` = 0,02° per pixel, lika i hela bilden i sidled och höjd (en
  bit av en equirect kring horisonten). Bara Yaw riktar vyn och horisonten ligger alltid mitt i bilden; Pitch, Roll
  och FOV används inte. 3840 × 2160 visar 76,8° × 43,2°.
- **Sidan (`stabilizer/index.html` 2.0):** pan = −(Offset X − första nyckeln) · 0,02. Inga fält: varken FOV,
  bildstorlek eller startpunkt, eftersom skalan är lika överallt. Släpp exporten, se väg och skak, spara
  `Stab Yaw.csv`. Under Options: Smoothing (i bildrutor, 12 som standard), Invert direction, Also make Stab Pitch.
- **Spikar lagas i sidan (2.1, Eric 2026-10-12: "kan du lägga in ett verktyg som fixar bort spikes?" — "trackern
  fastna på annat i bilden och sen följer ett annat parti på berget").** `fixSlips`: ett hopp i panen mellan två
  bildrutor som är långt större än alla andra är trackern som halkat. Hopp nära varandra (ut och tillbaka) blir en
  sträcka som överbryggas med en rak linje; ett hopp som aldrig går tillbaka (ett annat parti på berget) dras bort ur
  allt efter det. Påslaget som standard ("Fix spikes automatically"); en spik som blir kvar markeras genom att dra över
  den i det nedre diagrammet, "Undo hand fixes" ångrar. De lagade sträckorna är skuggade och kurvan före lagningen
  ligger kvar i grått.
- **0.11 i Live FX (2026-10-12 19:13, Erics export `Matchbox.Offroad 130-175s_test1.csv` ur Tracking view):** skalan
  stämmer utan inmatade tal — mot panen räknad ur klippet är lutningen 0,94 och hela panen −12,4 … +21,4°. Trackern
  halkade på tre ställen (bildruta 155–161, 378–408, 1096–1102); efter lagningen går skaket −1,49 … +0,91° (klippet:
  −1,47 … +0,91°), korrelation 0,96, största skillnad 0,73° inne i den 30 bildrutor långa bryggan. Före: −3,42 … +1,70°.
  Kurvan är inte importerad eller sedd på väggarna.
- **Importen gjord i Live FX 2026-10-12 (Claude, på Erics begäran "prova själv"):** Set Key i Matchbox-panelen gör
  pluginens parametrar synliga i Curve Editor; `Stab Yaw.csv` importerad på Stab Yaw på trackingnoden; fältet följer
  kurvan (−0,82 vid bildruta 1109) och Stab Yaw 10 i Off-läge vrider bilden tydligt. Erics första import hade hamnat på
  Framing → Offset X, därför syntes inget. Steg för steg i
  [fisheye-stabilisering-trackingvy](../_atlas/knowledge/assimilate/fisheye-stabilisering-trackingvy.md).
  Inte gjort: väggarnas noder, och att se stabiliseringen i uppspelning.
- **Pitch i sidan (2.2, Eric 2026-10-13: "kan du lägga till … att den stabiliserar pitch också? blir det lika bra
  resultat?").** "Stabilize pitch too" ger ett tredje diagram och `Stab Pitch.csv`; sträckorna som lagats i panen
  överbryggas i höjdled också. Inte lika bra som pan, av tre skäl: (1) rätt bara när punkten ligger rakt fram — åt
  sidan visar höjden roll, och en punkt kan inte skilja pitch från roll; (2) sidan vet inte åt vilket håll vyn pekar,
  så en punkt bakom bilen kräver "Invert pitch"; (3) rörelsen är liten. På Erics Offroad-spår: pitch-skak
  −0,20 … +0,16° (pan −1,49 … +0,91°, nio gånger större). Mot det andra, oberoende spåret (Mode Wall, annan punkt):
  pitch korrelation 0,96 och lutning 0,89, pan 0,995 och 0,97. Ingen mätning direkt ur klippet finns för pitch.
  Inte importerat eller sett i Live FX.
- **Vilken 360 som helst (sidan 3.0, Eric 2026-10-13: "så generisk så den kan ta emot keys från vilken 360 som
  helst").** Sidan läser själv vad exporten är, på kurvornas namn: **grader** (Pan 360 Yaw / Pitch / Roll, eller andra
  kurvor som slutar på Yaw, Pitch, Roll) används som de är; **pixlar** (Framing Offset X / Y) räknas med Tracking
  views 0,02° per pixel, eller — om man väljer "A 360° equirect picture" — med 360° / bildens bredd, vald i en lista.
  Offset X ensam räcker (då ingen pitch). För annat än fisheye-noden heter filerna "Yaw shake" osv. och importeras på
  samma parameter som nycklarna kom ifrån. Provat: en känd pan kommer tillbaka ur grader och ur en 7680 bred equirect;
  Live FX:s riktiga Pan 360-export (de ogiltiga filerna från fisheyeklippet) läses med Yaw, Pitch och Roll.
  **Inte provat i Live FX på ett riktigt equirect-klipp**, och tecknet åt det hållet är inte belagt.
- **Flödet i Live FX:** nodens Mode → Tracking view, rikta med Yaw mot något långt bort vid horisonten → Framing →
  Stabilize → Track 1 Point → Apply to Framing → exportera Framing Offset X/Y → sidan → importera Stab Yaw på
  väggarna → sätt tillbaka nodens Mode.
- **Samma skala på tre ställen:** shadern (`TRACK_SCALE`), sidan (`DEG_PER_PIXEL`) och `directionlock.swift`
  (`--tracking`). Provet `node tools/test-stabilizer.mjs` fäller bygget om de skiljer sig.
- **Provat:** `tools/verify.swift` (två fall, 0,02 källpixlar; Pitch, Roll och FOV påverkar inte). Sidan ger tillbaka
  en känd pan på 0,00000001°, också när Offset inte börjar på 0. Sedd i webbläsare med ett påhittat spår.
  **Inte provat i Live FX:** hur trackern beter sig i vyn, och hela kedjan.
- **Det som inte går att ta bort:** rätt Mode måste väljas. Sidan kan inte se i exporten vilket läge som användes; den
  varnar bara om panen är bredare än 70°.
- **Utlagt 2026-10-12** (build 202610121905 i `_applaunchers`), sedan Eric sagt att nollställningen i öppna projekt
  "är inget att oroa sig för". Inte installerat. Sidan följer inte med appen; den öppnas ur `stabilizer/`.

### Auto Stabilize: klippet in, Stab Yaw ut (0.10, utan tracker)

Eric 2026-10-12: "detta måste automatiseras, kan inte va ansvarig för detta" och "jag vill att alla data som måste
anges hämtas automatiskt". I trackingvyn skrevs FOV, bildstorlek och startpunkt in för hand, och varje fel gav fel
vinklar utan varning (FOV 90 i stället för 60 ger 41 % för stort skak; startpunkten i mitten 14 %).

**Sättet:** med objektivet rakt upp är pan en vridning av bilden kring objektivets mitt. `tools/autoyaw/` läser
klippet, vecklar ut ett band 3–28° över horisonten (himmel och avlägsna berg, inte marken som rör sig med farten)
till vinkel × radie, och tar vridningen mellan två bildrutor som den förskjutning längs vinkeln som passar bäst.
Summan är panen, skaket = pan − väg (samma Gauss 0,5 s) skrivs som Stab Yaw. Ingen tracker, ingen export, inga tal:

| Förr inskrivet | Nu |
|---|---|
| FOV, trackingvyns bredd och höjd | finns inte i räkningen |
| Punktens startläge | finns inte i räkningen (ingen punkt) |
| Bildtakt, antal bildrutor | läses ur klippet |
| Objektivets mitt | bildcirkelns kant mot det svarta hittas och passas till en cirkel; utan synlig kant antas bildens mitt |

**På scen:** starta IgelkottLiveFXFisheye → **Stabilisera ett klipp …** → välj det kvadratiska råklippet. Appen
skriver `~/Movies/IgelkottFisheye Direction Lock/Stab/<klipp> Stab Yaw.csv` och visar den i Finder. Importera den på
Stab Yaw i varje väggs nod. (`IGELKOTT_CLIP=<klipp>` kör samma sak utan dialogrutor.)

**Mätt på Offroad-plåten 2026-10-12** (1124 bildrutor, 19 s på m3max):

- mot molnspåret genom objektivets modell (`Track fisheye`): korrelation 0,9996, lutning 1,005, största skillnad 0,035°;
- mot trackingvyn utan trakterna kring dess nio spikar: korrelation 0,998, lutning 0,977, största skillnad 0,23°;
- inga spikar (trackern fastnade i förgrunden vid bildruta 167–169 och 392–409);
- bildcirkeln hittad på (2034, 2026), radie 2086 px — samma som mätt för hand.

Kurvan ligger som `tools/fixtures/auto/Offroad 130-175s Stab Yaw.csv` (skak −1,47 … +0,91°) och i `Stab/`.
**Inte importerad eller sedd i Live FX**, och bara mätt på det här klippet.

**Provet:** `autoyaw --selftest` gör ett påhittat klipp med känd pan och ska hitta den (fel under 0,05°, i praktiken
0,001°) och bildcirkeln; `build-app.sh` kör det. Klippet självt ligger inte i repot.

**Gränser:** bara pan (ingen pitch eller roll); kameran rakt upp; kvadratiskt klipp; högst 4° pan mellan två
bildrutor. Stora rörliga saker i himmelsbandet (en buss tätt intill, fladdrande flaggor) är inte prövade. Läser det
AVFoundation läser (ProRes, H.264, HEVC) — bara på Mac.

**Publik release:** verktyget är ett kompilerat program. Osignerat och nedladdat stoppas det av Gatekeeper, och det
går inte på Windows. Stabilizer-sidan (trackad punkt) fungerar överallt men kräver måtten. Vilket som ska ut är Erics
beslut — se Publik release.

### Trackingvy → Stab Yaw (0.9, reservväg)

Reserv när Auto Stabilize inte duger (t.ex. när pitch behövs). Kräver att FOV, bildstorlek och startpunkt skrivs in
rätt. Provad på Offroad-plåten i Live FX 2026-10-12 (Eric: "det ser ut att fungera"). Metoden, fällorna och vägarna som
inte fungerade står i [fisheye-stabilisering-trackingvy](../_atlas/knowledge/assimilate/fisheye-stabilisering-trackingvy.md).
Avsedd för begränsade fall: kameran rakt upp, skakningen mest pan, vägen ganska rak, en punkt vid horisonten synlig
hela klippet.

**På scen:**

1. **Trackingvy:** råklippets slot får en IgelkottFisheye i Mode Wall, riktad rakt fram mot horisonten. Format
   3840 × 2160, FOV 60, kamerans Sensor Height. Slotens Metadata → Projection Type = Normal.
2. **Tracka:** Framing → Stabilize → Track 1 Point på en bergstopp, bara Translate → Apply Stabilize (Framing) →
   Accept. Framing-animationen på Off efteråt.
3. **Exportera** Framing Offset X och Offset Y ur Curve Editor till `~/Movies/IgelkottFisheye Direction Lock/`
   (`<namn> Offset X.csv`, `<namn> Offset Y.csv`).
4. **Starta IgelkottLiveFXFisheye** (Suit, Finder eller en Stream Deck-knapp). `Stab/<namn> Stab Yaw.csv` skrivs.
5. **Importera** kurvan på Stab Yaw i varje väggs nod (Animation Manual). Stab Pitch och Stab Roll på 0.
6. **Städa spikar** för hand i Curve Editor (trackern som fastnat på något i förgrunden): markera nycklarna, Delete.

**Räkningen** (`tools/directionlock.swift`, flaggorna i `installningar.txt` i mappen):

- `--view <FOV> <bredd> <höjd>`: Offset är minus punktens rörelse i vyns pixlar, Y uppåt. f = (höjd / 2) / tan(FOV / 2),
  sidled = atan(x / f), höjd = atan(y / hypot(x, f)), relativt första nyckeln.
- `--start <x> <y>`: punktens läge i vyn vid första bildrutan (pixlar, origo uppe till vänster). Står inte i exporten
  och går inte att räkna ur spåret i en rak vy; utan flaggan antas bildens mitt. Offroad: 1166, 793.
- `--smooth <sekunder>` (`--fps 25`): väg = Gauss-utjämning åt båda hållen, sigma = sekunder · fps bildrutor avrundat
  nedåt; skak = vinkel − väg. Skaket är Stab Yaw.
- `--yaw-only`: bara Stab Yaw (Eric 2026-10-11: "det är bara pan vi försöker stabilisera").
- `--yaw-sign`, `--pitch-sign`, `--strength`.
- Flera spår i mappen hålls isär på filnamnet.

**Provet:** `swift tools/directionlock.swift --test tools/fixtures` — Offroad-spåret (`fixtures/vy/`) ger SPL26:s
prototypkurvor (skak ±1,59° pan, ±0,35° tilt) med skillnad 0,0000005°. `build-app.sh` kör det. Prototypen
`tools/vy_stab.py` är borttagen i 0.9; dess kurvor ligger kvar som facit.

**Varför utanför noden:** skaket beror på bildrutorna före och efter, och en Matchbox-shader har inget minne mellan
bildrutor. REST-API:t kan inte skriva nyckelbilder på en nods reglage. Kurvan måste in genom Curve Editors Import.

**Äldre vägar, kvar i verktyget:**

- **Erics DL** (`--k 0.5`, utan `--smooth`): `ut[n] = (t[n] − t[n−1]) + k · ut[n−1]`, stämmer mot 2025-filerna på
  0,0000014. Klingar av på 2–3 bildrutor och släpper igenom gungandet på 1–3 Hz; på en inspelad plåt är utjämning åt
  båda hållen rätt filter.
- **Tracka i själva fisheyeklippet** (`--fisheye <bredd> --sensor-height <mm>`): punkten genom objektivets modell,
  startläget ur en cirkel passad till spåret. Stämmer matematiskt (två oberoende punkter gav samma pan, korrelation
  +0,98), men trackern glider i den förvrängda bilden. Offroad-spåren ligger i mappens undermapp
  `Fisheye-spår (äldre metod, --fisheye)`.
- **Pixlar i en vägg** (`--pixels <FOV> <höjd>`): punkten åker ur väggen när bilen svänger.
- **Mode Fisheye (stabilize)**: en nod före väggarna som bär Stab-kurvan ensam. Räknad i provet, inte provad i Live FX.
- Klippet får inte vara märkt Equirectangular 360: då skriver Stabilize Pan 360-grader i stället för pixlar
  ([tracker-framing-export](../_atlas/knowledge/assimilate/tracker-framing-export.md)).

### Stabilisering (0.3)

S = Ry(stabYaw) · Rx(−stabPitch) · Rz(stabRoll), källriktning d = S · R · stråle. S ligger före väggens rotation, så
samma värden på alla väggar vrider sfären som en kropp (en förskjutning av fisheyebilden gör inte det).

Vilket håll som är vilket (räknat i `tools/verify.swift`, inte sett i Live FX):

- **Stab Pitch +** = väggen rakt fram (yaw 0) hämtar källan **högre upp**, den rakt bak (yaw 180) lika mycket lägre;
  sidoväggarna vrids runt sin mitt. I bilden rakt fram sjunker alltså horisonten.
- Kameran sitter fast i bilen. Tippar nosen **upp** α° ligger horisonten rakt fram α° lägre i källan, och rättas
  med **Stab Pitch = −α**. Stab Pitch + rättar en nos som tippar **ner**. (SPL26-handoffen bad om formeln ovan och om
  att + ska motverka nos upp; de två går inte ihop. Formeln fick styra, så att reglaget går åt samma håll som Pitch.)
- **Stab Yaw +** = alla väggar hämtar längre åt höger. **Stab Roll +** = som väggens Roll + på väggen rakt fram.
- En CSV-kurvas tecken beror på hur den mättes (2025-kurvorna är Pan 360 Pitch, vars håll inte är avläst). Därför finns
  `LED1 Pitch stab +.csv` och `… -.csv`: den som gör horisonten stillare är rätt, och det skrivs in här med datum.

## Förslag: kameran och nadir/zenit automatiskt (pixeltaggen, 2026-11-19)

Eric 2026-11-19: "funderar på hur vi gör shader paketet till live fx och pixera så enkel som möjligt. så nära automatiskt stöd för
nadir/zenith och pyxis/venice som möjligt", sedan "ja, skriv förslaget 1 och skicka handoffarna" och ja till att Darkroom och Fisheye to
Equi skriver taggen. **Ska provas i Live FX** (Eric: "sen ska det testas i live fx"). Skrivet av Stage 1-sessionen; byggs här.

**Problemet:** en shader ser bara pixlar. Den kan inte läsa filnamnet, metadata eller QR-koden, så i dag väljs kameran för hand och nadir
stöds inte alls (båda shaders antar objektivet uppåt). En nadirplåt eller en Venice-plåt med fel val ger fel geometri utan varning.

**Förslaget:** Darkroom och Fisheye to Equi skriver, bredvid hörnmärkets QR-kod, en pixeltagg som shadern läser själv:

- **Plats och innehåll: reglerna står bara i `PixelTag` (`_shared/IgelkottFisheyeLens`, `IgelkottLensMark`, Motion 2026-11-19).** Förslagets
  plats under QR-koden låg inne i PYXIS bildcirkel vid 125° (Fisheye to Equi 1.93) och ersattes: två rader om tio rutor på 0,011 *s*
  längs övre kanten bredvid QR-koden, x 0,116–0,226, y 0,010–0,032, i **alla fyra** hörnen speglade som QR-koderna. Ruta 0 vit, 1 svart,
  version (2 bitar, 1), kamera (3: 0 okänd, 1 PYXIS 12K, 2 Sony Venice 2, 3 Z-Cam E2 S6), nadir, justerad, horisonten inbränd, 4 lediga,
  CRC-6 (0x27, start 0x3F, högsta biten först). Minsta kontrast mellan referenserna 0,1; taggen som flest hörn har gäller.
- **Shadern (byggd i 0.14):** Plate Auto läser rutornas mitt (80 läsningar), Manual tar Camera och Pointing. Ingen tagg i Auto, eller en
  kamera utan modell: varningstecknet och Manual-valen. Nadir: riktningen (x, y, z) → (x, −y, −z) före objektivet. Inget Debug-läge
  (Eric: Debug bort som eget reglage).
- **En källa (byggd):** `shader/core.glsl` + omslagen `shader/matchbox.glsl`, `shader/pixera.glsl` och `shader/IgelkottFisheye2D.xml`;
  `python tools/build_shaders.py` gör `matchbox/` och `pixera/` och tar kamerornas tal ur `FisheyeLens.swift` som text.
- **Facit:** `tools/verify_windows.py` ritar båda utgåvorna och jämför pixel för pixel med `FisheyeLens.point` (nadir och Venice inräknade),
  ritar taggen som `PixelTag.rect` och kontrollerar bitarna mot `PixelTagTests` provvektorer. `tools/verify.swift` (Mac) är inte omskrivet.
- **Kantutjämning:** förfiltrering vid förminskning (`textureGrad`/mipmaps) i stället för fast 2 × 2; väntar på Stage 1:s mätning av
  moarén i A014C006 (2026-11-19).

**Z-Cam E2 S6 (Eric 2026-11-19: "den måste stödja Z-Cam E2 S6 också även fast den inte är byggd än"):** taggen och shaders ska ha plats för
en tredje kamera från början: kamerakoden 3 = Z-Cam E2 S6 (0 okänd, 1 PYXIS 12K, 2 Sony Venice 2), i taggen, i `LensMark`-profilen och i
reglaget Camera. Linsmodellen för Z-Cam E2 S6 finns inte än; tills den finns ska en fil med koden 3 inte spelas med en annan kameras modell
tyst (shadern faller tillbaka på valet för hand och Debug säger varför). Koden får inte behöva en ny taggversion när modellen kommer.

**Reglagen (Eric 2026-11-19, ersätter listan ovan):** "jag vill att har minimalt med reglare, auto/manual för plate och sen
yaw,pan,pitch" (Pan var fel: "pitch, roll yaw, jag skrev fel"), "stab ska bort, fov ska va kvar", "lens offset ska vara kvar så man kan
justera upp/ner höger/vänster", "jag vill bara ha wall läge, inge 3d screens".
- **Mode: Wall och Equirect**, i Live FX och Pixera (Eric först "jag vill bara ha wall läge, inge 3d screens", sedan, efter skillnaden mot
  Equirect för böjda väggar och kupoler: "då ska båda med"). Wall: en platt vägg, en omsampling. Equirect: hela sfären 2:1, som värdprogrammet
  klipper väggar ur (Eq->2D, Pixeras Equirectangular), två omsamplingar men böjda väggar exakt. Fisheye (stabilize) och Tracking view tas
  bort. Split, Yaw, Pitch, Roll och FOV gäller bara Wall.
- **Pixera behåller 3D_Screens** (Eric 2026-11-19, efter att 3D_Screens ger böjda väggar med en omsampling i stället för Equirects två:
  "ok, ja den skarpare bilden"). Pixera har alltså Wall, Equirect och 3D_Screens; Live FX har Wall och Equirect.
- Panelen: **Plate** (Auto / Manual), **Yaw**, **Pitch**, **Roll**, **FOV**, **Lens Offset X / Y** (flyttar objektivets mitt höger/vänster
  och upp/ner; i Auto ovanpå taggens centrerade mitt, 0 som standard).
- **Plate Auto:** kamera, nadir/zenit och objektivets mitt ur taggen. **Plate Manual** (Eric: "ja"): visar också **Camera** (PYXIS 12K, Sony
  Venice 2, Z-Cam E2 S6) och **Pointing** (Zenith, Nadir).
- **Split** (Eric: "ett läge som delar upp projectionen i två vertikalt så jag kan ha en inställning på höger sida skärmen och en annan på
  vänter med dynamisk split"; på frågorna: "samma plåt, ja, skarp, led"): av eller på, och **Split position** (gränsens plats, 0–100 % av
  bredden). På: samma plåt, och varje halva är en egen vägg med egen mitt och egna **Yaw, Pitch, Roll, FOV** (vänster och höger). Gränsen
  är skarp. För LED-väggen. Av: en uppsättning.
- Bort: Stab Yaw/Pitch/Roll (plåtarna har horisonten inbränd), Sensor Height, Lens Scale, Quality (fast standard), Flip Vertical och Debug
  som eget reglage.
- **Saknas taggen** (Eric 2026-11-19: "gör som du föreslår"): med Plate Auto och ingen giltig tagg i något hörn ritar shadern en liten varning i
  bildens hörn (en symbol, ingen text som ändras), och Camera och Pointing tas som i Manual med standardvärdena (PYXIS 12K, Zenith). Med en
  giltig tagg eller i Manual ritas ingenting. Varningen syns på väggen, så den ska inte kunna stå kvar i en tagning: operatören byter till
  Manual eller till en plåt med tagg.

**Varför inte annat:** att laddaren (IgelkottLiveFXLoader) läser QR-koden och ställer reglagen fungerar bara i program vi skriver en laddare
för, och ett klipp som läggs in för hand får inget. Taggen fungerar i varje program som kör en shader (Live FX, Pixera, senare Resolve och
Unreal).

**Handoffar 2026-11-19:** IgelkottMotion (taggens regler i `LensMark`), IgelkottDarkroom och IgelkottFisheyetoEqui (skriver taggen),
och hit (bygg shaders och prova i Live FX).

**Inte provat:** taggen på en riktig fil, och att den överlever Topaz (den skrivs sist, efter Topaz, som QR-koden). Se Status, 0.14.

## Status

- **0.1 (2026-10-05):** noden och provet. `tools/verify.swift`: sju fall (Back pitch 15 FOV 58,5, Side yaw 90, Sky pitch 70
  roll 12, LED FOV 10, Ref TV yaw 180 med plattförskjutning, 3 × 3 prov, equirect) — största avvikelsen mot IgelkottStages
  räkning **0,02 källpixlar vid 8040**, svart utanför bildramen. **Inte provad i Live FX.**
  Deployad 2026-10-05 (build 202610051632), installerad via Suit och "Aktuell" (Eric). Live FX 9.9.1212 registrerade
  noden vid omstart (Junxion.xml, loggens Module 74: IgelkottFisheye2D).
- **Första provet i Live FX (2026-10-05, projektet `fisheye_test`, klippet A001_09041322_C003):** noden kör, men
  väggen kom **vriden 180°**: Live FX lägger källan och utbilden uppifrån i minnet, 0.1 räknade nerifrån som OpenGL.
  Noden låg dessutom under Eq->2D (media → Matchbox → Eq->2D), alltså två omvandlingar.
- **0.2 (2026-10-05, build 202610051702):** radordningen uppifrån är standard; Flip Vertical byter till OpenGL:s/Flames
  ordning. `tools/verify.swift` kör nu alla fall i båda ordningarna (största fel 0,023 källpixlar), och 0.1 fälls i
  Live FX-ordningen (fel 1 900–7 500 px). Installerad via Suit 2026-10-06 06:47.
- **Prov 2 i Live FX (2026-10-06, `fisheye_test`, Black → Matchbox → A001_09041322_C003, Yaw 0, FOV 90):** väggen står
  rätt — himlen uppåt, STOP-skyltar och registreringsskylt läsbara (inte spegelvänd), yaw 0 tittar i färdriktningen
  (skåpbilen framför). Noden har klippets storlek, 8040 × 8040.

- **0.3 (2026-10-11, build 202610112035):** Stab Yaw, Stab Pitch, Stab Roll — sfärrotation för stabilisering, på
  handoff från SPL26 (demon på Starting Pixel Live 2026-10-14). `tools/verify.swift`: fem nya fall med S (största fel
  0,025 källpixlar) och ett prov där Back, Side, Sky och Ref TV ritas med och utan samma S och varje pixels riktning
  ska ha vridits med just S (största avvikelse 0,05 källpixlar), i båda radordningarna. Deployad till `_applaunchers`
  från m3max. **Inte installerad eller provad i Live FX.** Kvar för Eric: installera via Suit på Live FX-Macen, starta
  om Live FX, provet i `Offroad stab_aces` (handoffen i `HANDOFF/`).

- **0.4 (2026-10-11):** Lens Scale — manuell skala för samma objektiv på en annan kamera (Eric: "en manuell lösning
  när jag filmar med samma lins på olika kameror och teckningen är olika"). Två nya fall i provet. I `_applaunchers`,
  inte installerad eller provad i Live FX.
- **0.5 (2026-10-11):** Sensor Height mm — sensorhöjden skrivs in och ger skalan, Lens Scale blir fintrimning (Eric:
  "ett fält där jag skriver in storlek på sensor, så det blir enkelt för kunder att förstå"). Två nya fall i provet.
  I `_applaunchers`, inte installerad eller provad i Live FX.

- **0.5 i Live FX (2026-10-11, m3max, rapporterat av SPL26-sessionen):** installerad, Stab-kolumnen syns, noderna i
  `Offroad stab_aces` (byggt före 0.3) fick reglagen med 0, och `Stab Pitch +.csv` ligger på Stab Pitch i Back, Sky,
  Ref TV, Hard Light och LED1–4; reglaget följer kurvan per bildruta och bilden tippar. Inte avgjort: om horisonten
  är stillare (rätt tecken).
- **0.6 (2026-10-11, build 202610112137):** panelen heter IgelkottFisheye; Direction Lock-verktyget i appen; Mode
  Fisheye (stabilize). På handoff från SPL26 (Eric: "i demon ska jag tracka en punkt live, pluginen måste kunna göra
  i min enkla formel för trackingdatan. sen ska det stå IgelkottFisheye"). I `_applaunchers`, inte installerad eller
  provad i Live FX.

- **0.7 (2026-10-11, build 202610112310):** Direction Lock tar ett spår trackat i fisheyeklippet (`--fisheye`), på
  handoff från SPL26 med en riktig tracker-export. Enhet och tecken avlästa mot klippets bilder; Stab-kurvorna för
  Offroad ligger i `Stab/`. I `_applaunchers`, inte installerad; kurvorna är inte importerade i Live FX.

- **0.8 (2026-10-11, build 202610112338):** `--yaw-only` och ett spår per filnamn i Direction Lock; `Track bak Stab
  Yaw.csv` räknad ur den nya exporten (punkt rakt bak). I `_applaunchers`, inte installerad.

- **0.9 (2026-10-12, build 202610120033):** trackingvy-läget i appen (`--view`, `--start`, `--smooth`), på handoff
  från SPL26 efter att metoden fungerat i Live FX. Appen ger samma kurva som prototypen på Offroad-spåret
  (`Stab/Track vy Stab Yaw.csv`, skillnad 0,0). Installerad via Suit på m3max 2026-10-12 (appen och shadern i
  Matchbox-mappen på 0.9) och kedjan körd med appen: spåret `Genomgang` exporterat och omräknat till
  `Stab/Genomgang Stab Yaw.csv` (Eric: "klart").

- **Stabilizer-sidan (2026-10-12):** `stabilizer/index.html` 1.0, första steget mot publik release (se Publik
  release). Ingen ny version av appen eller noden är byggd eller lagd i `_applaunchers`.

- **0.10 (2026-10-12, build 202610121705):** Auto Stabilize i appen (`tools/autoyaw/`, knappen "Stabilisera ett
  klipp …"). Shadern är orörd (XML fortfarande 0.9, samma filer som står installerade), så en installation ändrar
  inget i Live FX. Stabilizer-sidan 1.1: Offset som inte börjar på 0, hjälptexten över skärmbilden, "one or two
  files"; samma Offset-rättning i `directionlock.swift`. I `_applaunchers`, inte installerad.

- **0.11 (2026-10-12, build 202610121905):** Mode Tracking view i noden och Stabilizer-sidan 2.0 utan fält. I
  `_applaunchers`, inte installerad, inte provad i Live FX.

- **0.12 (2026-10-19, build 202610192043):** på handoffarna om Darkroms hörnmärke (IgelkottMotion 2026-10-15/16,
  IgelkottDarkroom 2026-10-16).
  - **Camera i noden:** Custom (PYXIS-kurvan skalad med Sensor Height och Lens Scale — som förut och standard, så gamla
    projekt ändras inte), PYXIS 12K och Sony Venice 2 med kamerans egen modell ur `_shared/IgelkottFisheyeLens`.
    Venice-modellen har egen mitt (2848, 2854 av 5760, ~0,5 % från bildens mitt) och motsvarar Sensor Height ~24,0;
    med Custom 23,9 blir en Darkroom-centrerad Venice-fil förskjuten ~30 px vid 5760. En märkt fil spelas med märkets
    kamera och Lens Offset 0. Shadern kan inte läsa QR. Provet jämför kamerornas tal med den delade filen.
  - **Auto Stabilize läser hörnmärket** (`IgelkottLensMark`): litat märke → kamerans modell utan offset; annars `--camera`
    (standard PYXIS 12K) och mitten ur FisheyetoEquis kalibrering (`FisheyeLens.forClip`). Den egna cirkeldetektorn är
    borttagen. Verktyget är nu ett Swift-paket, `tools/autoyaw/`, som beror på `_shared/IgelkottFisheyeLens`. På Offroad
    (omärkt Venice): med Sony Venice 2 skiljer kurvan 0,009° från den med uppmätt cirkel, med PYXIS-standard 0,032°.
    **Inte provat på en märkt fil.**
  - Regeln tid → ruta (IgelkottDailies 2026-10-16): ingen ändring, projektet räknar aldrig om tid till ruta.
  I `_applaunchers`, inte installerad.

- **Windows (2026-10-28, ERIC-DESKTOP, Eric: "denna plugin ska göras för windows" och "det ska fungera på nvidia
  också så gör inget som kräver amd"):** shadern är oförändrad (0.12), ingen ny version.
  - **Var:** Live FX 9.9 build 1214 Win64 läser shaders ur `C:\ProgramData\Assimilator\plugin64\Matchbox\shaders`
    (logik-samlingen ligger där, 320 Matchbox-moduler i `Settings\JunxionX64.xml`). Mappen är skrivbar för alla
    (`Alla:(F)`), så ingen admin behövs; installeraren ber om det bara om kopian misslyckas.
  - **Hur:** Live FX kör OpenGL på Windows (loggen: "OpenGL 4.6.0 Compatibility Profile Context", AMD Radeon RX 9070 XT),
    inte Metal. GLSL 1.20 kompileras alltså av grafikkortets egen drivrutin, inte av SpaMatchbox översättning.
  - **Provet på Windows:** `python tools/verify_windows.py` — samma 25 fall och sfärprov som `verify.swift`, med en
    WGL-kontext via ctypes (bara Python 3, inga paket, inget AMD-specifikt). På RX 9070 XT (drivrutin 26.10.1): alla
    fall går igenom i båda radordningarna, största fel 0,026 källpixlar (Venice Fisheye (stabilize) 0,167, under 0,5).
    **Inte provat på NVIDIA** — kör provet på en NVIDIA-dator innan det sägs fungera där.
  - **Installeraren:** `windows/Install IgelkottFisheye.cmd` (och `Uninstall …`), som kör
    `windows/Install-IgelkottFisheye.ps1`: hittar `%ProgramData%\Assimilator`, kopierar `.glsl`/`.xml` ur sin egen mapp
    (zipen) eller `..\matchbox`, säger "starta om Live FX". Engelska. Provad mot en provmapp (installera, igen = inget
    att göra, avinstallera) och installerad på ERIC-DESKTOP 2026-10-28.
  - **Installationspaketet (2026-10-28):** `windows/build-package.ps1` kör `verify_windows.py` (bygger inte om det
    fallerar) och gör `_releases/IgelkottFisheye/IgelkottFisheye-Windows.zip` (var `dist/` i projektmappen till 2026-11-11): en mapp med de två `.cmd`, `.ps1`, noden,
    `PIXERA/` (effekten + dess README), `VERSION` och `README.txt` (engelska, `windows/README.txt`: installera,
    avinstallera, 0.14-reglagen, PNG stöds inte). Provat: uppackad zip → installera/igen/avinstallera mot provmapp.
    2026-11-19 (0.14): Stabilizer-sidan togs ur paketet — noden har inga Stab-reglage eller Tracking view längre, så
    sidans flöde går inte att följa; den ligger kvar i `stabilizer/`. Lägg tillbaka den om Eric vill.
  - **Prov i Live FX på Windows (2026-10-28, ERIC-DESKTOP, Live FX 9.9.1214, RX 9070 XT; Claude via datorstyrning):**
    `Project1`, klippet `A008C004_260614HB_A_proxy` (2880 × 2880, Fog City), Plug-ins.. → Matchbox → shaders →
    IgelkottFisheye2D → Apply On Node direkt på media; Mode Wall, Yaw 0, FOV 90, Camera Custom (standard). Noden syns i
    listan och ritar. Med **Flip Vertical av** står väggen rätt — himlen uppåt, skyltarna "Phở" och "COCKTAIL" läsbara
    (inte spegelvända), yaw 0 tittar längs gatan i färdriktningen. Med Flip Vertical på blir bilden upp och ner och
    tittar bakåt. **Radordningen är alltså uppifrån, som på Mac — ingen ändring i shadern.** Loggen: inga
    SpaMatchbox-/Igelkott-fel. Noden ligger kvar i `Project1` (Auto-Save på). NVIDIA fortfarande inte provat.
  - **Mac-bundet, inte flyttat:** Auto Stabilize (`tools/autoyaw/`, AVFoundation), Direction Lock-appen och
    `build-app.sh`/Suit. Stabilizer-sidan är en HTML-fil och går i webbläsaren på Windows.

- **PIXERA (2026-11-11, Eric: "gör en 'plugin' för pixera, googla vad dom kräver först. här är en ref för equi från
  pixera"):** `pixera/IgelkottFisheye.glsl`.
  - **Vad PIXERA kräver** (help.pixera.one, "Shadertoy to Pixera GLSL Tutorial"): en `.glsl` där filnamn och `struct`
    heter samma, `//@implements: sampler2D` och `sampler2D sampler` först, reglagen som fält med `//@`-rader (range, enum,
    bool, sampler), och `vec4 texture(<Namn> s, vec2 tex_coords)` i stället för `main`. Läggs i Effects → Custom (dra in
    filen). GPUpad med PIXERA:s startprojekt är deras provmiljö (Windows).
  - **Två lägen:** 3D_Screens = PIXERA:s Equirectangular rad för rad fram till riktningen (Screen Pixel Position-sampler,
    ögats läge och vridning, `u_render_target_id`), sedan genom linsmodellen i stället för en equirect; Wall = vy som
    Live FX-noden (Yaw, Pitch, Roll, vertikal FOV, Aspect). Camera, Sensor Height, Lens Scale, Lens Offset, Stab och
    Flip Vertical som i noden.
  - **Riktningen:** Equirectangular-effektens mitt är +X i PIXERA:s värld (u = atan(n.z, n.x)/2π + 0,5, v uppåt);
    FisheyetoEquis equirect har mitten i d.z och u = atan(d.x, d.z)/2π + 0,5 — samma bild med d = (n.z, n.y, n.x).
  - **Provet** `tools/verify_pixera.swift` (OpenGL 4.1 core på Macen, GPUpad-mallens omskrivning av `texture()`):
    3D_Screens mot räkningen (0,09 px vid 8040), Wall (0,022 px), och **mot PIXERA:s egen Equirectangular** med en equirect
    gjord som FisheyetoEqui gör den ur samma fisheye: 0,03 px. `build-app.sh` kör det. Referensen: `Ref-Eric/`.
  - **Inte provat i PIXERA.** Kvar att se där: att filen läses in, att texturkoordinaterna går uppåt som i
    Equirectangular (annars Flip Vertical), och att Screen Pixel Position-samplern kopplas som i deras effekt.
  - Följer med Windows-paketet i mappen `PIXERA/` med egen `README.txt` (PIXERA kör på Windows). Paketet i `_releases/`
    är byggt före detta och behöver byggas om på Windows.

- **0.13 (2026-11-11, build 202611111156):**
  - **PYXIS 4032² (IgelkottDarkroom 2026-11-04):** noden räknar i andelar av bilden, så storleken spelar ingen roll.
    `tools/verify.swift` och `tools/verify_windows.py` kör nu alla fall en gång till med en källa på 1008 × 1008
    (4032 / 4, inte en tvåpotens): alla går igenom. Ett Darkroom-märkt 4032²-klipp spelas med Camera: PYXIS 12K och
    Lens Offset 0. Beskrivningen i noden säger inte längre "8040 x 8040". **Inte sett i Live FX med ett 4032²-klipp.**
  - **Städning (IgelkottSuit 2026-10-30):** `dist/` (Windows-paketet, 20 KB) flyttad ur projektmappen till
    `_releases/IgelkottFisheye/IgelkottFisheye-Windows.zip`, och `windows/build-package.ps1` lägger paketet där i
    stället (`_releases/` vill ha filnamn utan version; versionen står i `VERSION` i zipen). `tools/__pycache__`
    borttagen. Mac-bygget lämnar inget i projektmappen (52 filer före och efter). Byggmappen
    `~/Library/Caches/Igelkott/IgelkottLiveFXFisheye` (app + autoyaw-build, ~160 MB) används och ligger kvar; inga
    gamla byggmappar för projektet fanns. Appen har inga data i `~/Library`, så ingen `regenerable:` i suite.yaml.
  - **Windows-paketet i `_releases/` är 0.12** (byggt 2026-10-28). Nodens text ändrades i 0.13; paketet byggs om med
    `windows/build-package.ps1` på en Windows-dator (PowerShell finns inte på Macen).
  I `_applaunchers`, inte installerad.

- **0.14 (2026-11-19, ERIC-DESKTOP, Windows): pixeltaggen och Erics nya reglage**, på handoffarna från Stage 1, Motion,
  Darkroom och Fisheye to Equi (2026-11-19). Eric: "ja, bygg taggen" och "oroa dig inte för att ha sönder gamla, nu byggger vi
  något nytt": inget hänsyn till gamla projekt eller gamla reglage.
  - **Byggt:** reglagen i tabellen under Noden; en källa i `shader/` och `tools/build_shaders.py` för Live FX och PIXERA.
    PIXERA-effekten har nu Wall och Equirect (3D_Screens och Eye-reglagen borta), Plate, Camera, Pointing, Split och Aspect.
  - **Provet** `python tools/verify_windows.py` (RX 9070 XT): 61 fall, båda utgåvorna, källa 1024² och 1008², största fel
    0,026 källpixlar vid 8040; varningstecknet pixel för pixel. Taggens bitar = `PixelTagTests` provvektorer.
  - **PIXERA mot deras egen effekt (2026-11-19):** `Ref-Eric/Equirectangular.glsl.txt` läser texturen med v uppåt (`v = 1 −
    acos(n.y)/π`), som vår `igkFetch`. Den definierar en egen `radians()` och använder `u_render_target_id` odeklarerad, så PIXERA
    kompilerar inte strikt GLSL 4.50: `shader/core.glsl` använder därför inte den inbyggda `radians()` (konstanten `IGK_DEG`).
    `verify_windows.py` kör kedjan Mode Equirect → deras Equirectangular med en plan skärm: största fel 0,32 källpixlar (PYXIS
    zenit och Venice nadir, två omsamplingar). `pixera/README.txt` omskriven för 0.14. Inte provat i PIXERA.
  - **Provplåtar:** `python tools/make_testplates.py <mapp>` ritar en påhittad värld genom linsmodellen (fram röd, höger grön,
    bak blå, vänster gul) som PYXIS-zenit med tagg, Venice-nadir med tagg och PYXIS utan tagg. Med Auto, Yaw 0, FOV 90 ska de
    taggade ge samma vägg.
  - **Sett i Live FX (2026-11-19 kväll, 9.9.1214, ERIC-DESKTOP; Claude via datorstyrning, eget projekt `IgelkottFisheye
    tagtest`, Erics `Project1` orört):** panelen visar Plate, View, Split och Right Wall som tänkt.
    - **`.mov` (A008C004_260614HB_A_proxy, Fog City, ingen tagg):** väggen står rätt — bilen framåt, "citibank" och "HOUSE OF
      GIN SUN" läsbara. Plate Auto ger varningstecknet uppe till vänster; Manual tar bort det; Manual + Z-Cam E2 S6 ger svart
      och varningen. Split på, Right Yaw 90: vänstra halvan framåt med egen mitt, högra åt höger, skarp gräns vid 50 %.
    - **PNG (provplåtarna från `make_testplates.py`):** taggen läses — PYXIS-zenit och Venice-nadir ger samma vägg, ingen
      varning; plåten utan tagg ger varningen. **Men väggen kommer vriden 180° (himlen nederst, bak i mitten) och varningen
      nere till vänster upp och ned: Live FX lägger PNG-klipp nerifrån, både källan och utbilden**, medan `.mov` ligger uppifrån.
      Samma fel som 0.1 hade på alla klipp. Flip Vertical, som tog hand om det, är borttaget i 0.14 (Erics reglage).
    - **Popupens Default är ett index i Live FX**, inte ett värde: `Default="1"` på Camera (värdena 1–3) visade Sony Venice 2.
      Shadern får däremot postens Value (Z-Cam gav svart = 3). Rättat till `Default="0"`; efter omstart och Reset står noden
      på Auto, PYXIS 12K, Zenith.
  - **Riktiga taggade klipp (2026-11-20, ERIC-DESKTOP, Live FX 9.9 omstartad med 0.14-shadern):** de nio klippen i
    `W:\2025\Free Demo 2025\Store` (Fisheye to Equi, Venice 2, ProRes 4444 5760², 24/25 fps). Taggen läst med ffmpeg först:
    alla fyra hörnen giltiga i varje klipp, kamera 2, sju zenit och två nadir (A001C016, A011C001). Projekt
    `IgelkottFisheye Store` byggt med mus och tangentbord: Import Clips → släppt på slot 0 (tidslinjen behåller 1920 × 1080)
    → per klipp Plug-ins.. → Matchbox → shaders → IgelkottFisheye2D → Apply On Node, sedan Media → Image Format HD 1080-24
    (HD 1080-25 för A001C016 och A007C001). Alla nio med Plate Auto och nodens standard: väggen upprätt, horisonten rak, inget
    varningstecken; nadirklippen vända rätt. Det svarta överst på nadirklippen är källans egen svarta mask vid drönaren
    (källans nederkant hamnar överst på väggen); det svarta nederst på bilklippen är samma slags mask i källan.
  - **Inte gjort:** `tools/verify.swift` och `tools/verify_pixera.swift` (Mac) provar de gamla reglagen och fäller `build-app.sh`
    tills de skrivs om; ingen deploy till `_applaunchers`. Windows-paketet i `_releases/` är inte ombyggt. Stabilizer-sidan,
    Direction Lock och Auto Stabilize finns kvar men noden har inga Stab-reglage att ta emot deras kurvor. IgelkottLiveFXLoader
    skriver nodens gamla reglage. Inte provat i PIXERA eller på NVIDIA, och inte på en taggad fil från Darkroom 0.10.102
    (Fisheye to Equi-klippen ovan fungerar). **Beslut (Eric 2026-11-19: "inge stöd för png"):** PNG-klipp stöds inte; de kommer vridna
    180° och det är så med flit. Ingen Flip Vertical och ingen hörnbit i taggen för det. DPX, EXR och TIFF är inte provade.
    `tools/make_testplates.py` skriver PNG och duger därför bara för att se att taggen läses, inte orienteringen.

- **0.15 (2026-11-20, ERIC-DESKTOP): Auto i listorna och Offset efter projektionen** (Eric: "camera: deklarerar fel kamera",
  "offset ska vara efter projektion, inte före"). Panelen visade "Camera: PYXIS 12K" fast noden spelade Venice ur taggen (en
  shader kan inte skriva tillbaka till panelen). Nu: Camera och Pointing har "Auto (tag)" först, Plate-reglaget är borta; Lens
  Offset (objektivets mitt) ersatt av Offset X/Y som flyttar väggbilden i utbildens pixlar. Provet: alla fall PASS (största fel
  0,026 källpixlar), nya fall för blandat Auto/handval och offset i Split och Equirect. **Följd:** plåtar med förskjuten
  bildcirkel (Offroad-plåten ovan, Lens Offset ≈ −24, −39) kan inte längre rättas i noden. Noden installerad i Live FX 13:22
  men **inte sedd i Live FX**: programmet var öppet hos Eric och kör den gamla panelen tills det startas om.
  **Sedd i Live FX 2026-11-20 (efter omstart, Store-projektet):** panelen visar Camera: Auto (tag), Pointing: Auto (tag),
  Offset X/Y; A013C004 spelar utan varningstecken. Release v0.15 på GitHub med Windows-zippen (nu med `LICENSE.txt`).
- **Dukstorlekar (Eric 2026-11-20: "4k kanvas och 8k och 16kx2160"):** i Live FX (Media → Image Format; egna mått via
  Custom och sifferfönstret, tangentbordet går till kortkommandon) spelar A013C004 rätt på 4K UHD 3840 × 2160, 8K UHD
  7680 × 4320 och 15360 × 2160, även med Split. `python tools/verify_windows.py . --canvas` ritar 4K UHD, DCI 4K, 8K UHD,
  15360 × 2160 och 16384 × 2160 i full storlek (Live FX och PIXERA; var 7:e/13:e pixel kontrolleras): största fel
  0,016 källpixlar. Pixlar exakt på varningstecknets eller källbildens kant hoppas över (float32 mot double).
- **32:9 med Equirect (Eric 2026-11-20):** 7680 × 2160, A001C016 (nadir), Mode Equirect: hela sfären över hela duken,
  alltså 1,78 × utdragen på bredden mot en 2:1-equirect; plåtens hörn (QR och pixeltagg) syns i himlen överst.
- **0.16 (2026-11-20): Equirect 360° på bredden** (Eric: "Crop to 360° wide"). Mode Equirect lägger 360° över dukens
  bredd och samma grader per pixel på höjden, centrerat på horisonten (0.16:s `igkEquirectUV`, sedan 0.17 `igkEquirectDirection` i `core.glsl`): 2:1 är hela sfären
  som förut, 32:9 visar 101° på höjden (beskuret upptill och nertill), smalare dukar än 2:1 når förbi polerna och det blir
  svart. PIXERA: samma över lagrets Aspect (kedjan med PIXERA:s Equirectangular förutsätter Aspect 2). Provet: nya fall
  32:9 och 16:9, allt PASS. **Sedd i Live FX samma dag** (omstart): A001C016 på 7680 × 2160 visar 360° utan utdragning,
  QR-hörnen bortskurna så när som på spetsarna överst.
- **0.17 (2026-11-20): Split i Equirect och Right Offset** (Eric: "split ska fungera i equi också", valde "same scale,
  own aim"; "offset ska finnas på right också"). Equirect: 360° över hela dukens bredd (inte per vägg), samma grader
  per pixel på höjden; varje vägg är ett fönster centrerat på sina Yaw/Pitch/Roll (också utan Split: Yaw/Pitch/Roll
  riktar Equirect nu, FOV används inte). Offset X/Y är vänstra väggens, nya Right Offset X/Y (Matchbox `offset_xr`,
  `offset_yr`; PIXERA `offsetXR`, `offsetYR` i % av höjden) den högras. Provet: nya fall, allt PASS. **Sedd i Live FX:**
  A001C016 på 7680 × 2160, Equirect, Split 50 %, Right Yaw 180 ger hela 360° i två halvor utan skarv i bilden; Right
  Offset Y 300 flyttar bara högra halvan. **Varning:** när panelen fick nya reglage laddade noden i det sparade projektet
  fel värden (Offset X 213, Offset Y −44, Mode Wall i stället för 0, 0, Equirect), och Reset rättade inte Offset;
  kontrollera nodens värden efter en uppdatering som lägger till reglage.
  Granskning före release (2026-11-20): rotationen byggs en gång per pixel (`igkWallDirection`/`igkEquirectDirection` tar
  en `mat3`); PIXERA-README: Equirectangular-kedjan kräver Split av, noggrannheten "inom 0,1 källpixlar" (riktad
  Equirect mäter 0,069). Mac: se "0.17 i Live FX på Mac" nedan.
  Release v0.17 på GitHub (Windows-zippen) samma dag.
- **Mac, förberett (2026-11-20 kväll, M3Ultra, Live FX 9.9.1212):** 0.17 (`build_shaders.py --check` aktuell) kopierad
  till `/Library/Application Support/Assimilator/Plugins/Matchbox/shaders`; Live FX inte startat sedan dess. Apples
  GLSL 1.20-kompilator (CGL Legacy, M3 Ultra) godtar `IgelkottFisheye2D.glsl` utan varningar — säger inget om
  SpaMatchbox Metal-översättning. Provklipp i `~/Movies/IgelkottFisheye-MacTest/` (`notag.mov`, `pyxis_zenith_tag.mov`,
  `venice_nadir_tag.mov`, ProRes ur `make_testplates.py`); Store-klippen läses från `/Volumes/igelkottstore.com/2025/Free
  Demo 2025/Store`.
- **0.17 i Live FX på Mac (2026-11-20 kväll, M3Ultra, Live FX 9.9 build 1212 macOS, Metal GPUFamily Apple 9; Claude via
  datorstyrning, `docs/MAC-TEST.md` avsnitt 1–9):** eget projekt `IgelkottFisheye MacTest` (A013C004 slot 0, A001C016
  slot 1, `notag.mov` slot 2, `notag_long.mov` slot 3 = `notag.mov` loopad till 60 s). **Allt som provades fungerar som
  på Windows; ingen Mac-rättning behövs.**
  - **Kompilerar:** Junxion.xml registrerar `IgelkottFisheye2D` version 0.17; noden ritar direkt; loggen har inga
    SpaMatchbox-/Metal-fel. Panelen: Plate, View, Split, Right Wall som i listan; tooltips på engelska.
  - **Orientering (HD 1080-24, Wall, FOV 90):** A013C004 upprätt, himmel uppe, motorhuv nere, horisonten rak; Yaw 90
    tittar åt höger, −90 åt vänster, Pitch 30 uppåt. A001C016 (nadir): vatten och land nere, himmel uppe; Yaw 180 visar
    drönarens armar upptill. Provvärlden i `notag.mov`: fram röd i mitten, vänster gul till vänster, höger grön till höger.
  - **Taggen:** Venice-klippen på Auto/Auto utan varningstecken. Camera PYXIS 12K på Venice ändrar bilden; Pointing Zenith
    på A001C016 ger bilden upp och ner; `notag.mov` ger varningstecknet uppe till vänster; Z-Cam E2 S6 ger svart med tecknet.
  - **Offset och Split (Wall):** Offset X 200 åt höger, Offset Y 200 uppåt; Split 50 % + Right Yaw 90 ger två väggar med
    skarp gräns; Offset X flyttar bara vänstra; Right Offset Y bara högra.
  - **Equirect:** 3840 × 1920 hela sfären, framåt i mitten, horisonten rak; Yaw rullar, Pitch tippar, Roll vrider;
    7680 × 2160 360° över bredden utan utdragning; Split 50 % + Right Yaw 180 framåt vänster, bakåt höger, hela 360°;
    HD 1080-24 smala svarta band upptill och nertill.
  - **Uppspelning (`notag_long.mov`, lokalt, ProRes 422 HQ 1536², 25 fps):** 4K UHD, 8K UHD och 15360 × 2160 spelar alla
    i realtid (242–243 bilder på 10 s). **Store-klippen spelar 2–5 bilder/s, men det är nätverket:** ProRes 4444 5760² är
    ~4 Gbit/s (~21 MB per bild) och SMB-monteringen `/Volumes/igelkottstore.com` läser 56 MB/s (`dd`). Lägg dem lokalt
    för att spela dem i realtid.
  - **Sparade värden:** Offset X 50, Yaw 20, Equirect, Split på, Right Offset Y 30 och duken 15360 × 2160 låg kvar efter
    Close Project och ny öppning. Inget äldre projekt med noden i bruk finns på M3Ultra (`fisheye_test` har bara en
    överbliven nod utan ingång: loggen "SpaMatchbox: Input 1 for 'front' not connected!"), så laddningen av gamla
    värden är inte provad på Mac.
  - **Inte gjort:** avsnitt 10 (färg, frivilligt) — det ändrar Monitors → Interface för hela programmet.
  - **Att veta i Live FX på Mac:** ett värdefält öppnar ett sifferfönster som bara tar klick (tangentbordet går till
    kortkommandon, "−" byter panel); minus sätts med +/-. Viewern behåller sin zoom när dukens storlek ändras, så en
    större duk visar bara mitten; "fit" visar hela tidslinjens duk. Kontrollera hörnen (varningstecknet) i den vyn.
    Plug-ins.. lägger noden på spelhuvudets klipp, inte det man dubbelklickat i Construct.
- **0.18 (2026-11-20 kväll, M3Ultra): Z-Cam-modellen och vågrät FOV.**
  - **Z-Cam E2 S6** (handoff från IgelkottFisheyetoEqui 2026-11-20): `FisheyeLens.zcamE2S6` (reference 3872, mitten 1936,
    1936) läses av `build_shaders.py` som tredje kamera; Camera Z-Cam och taggkod 3 spelar nu med sin egen modell.
    Taggkod 4–7 (ingen modell) ger fortfarande svart och varningen. `build_shaders.py` skriver heltal som `1936.0`.
  - **FOV vågrät** (Eric 2026-11-20: "90 grader för mig betyder 90 grader på horisonten"): FOV är vinkeln från väggens
    vänstra till högra kant; med Split varje väggs egen bredd (Right FOV den högras). Till och med 0.17 var den lodrät
    över nodens höjd, som Eq->2D. **Följd:** sparade noder och IgelkottLiveFXLoaders FOV-värden (Eq->2D:s lodräta) ger
    en smalare bild än förut; handoff till Loadern. PIXERA: etiketten "FOV (horizontal)".
  - **Provet på Mac:** `tools/verify_mac.py` (`verify_windows.py` med CGL i stället för WGL, bara Live FX-utgåvan:
    Macens OpenGL har inte GLSL 4.50): 61 fall PASS, största fel 0,02 källpixlar vid 8040, Z-Cam-fallen och taggkod 4
    inräknade; talen stämmer med `_shared`. `. --canvas` (4K–16384 × 2160 i full storlek): allt PASS, största fel 0,010,
    49 s. `verify_mac.py` läser `verify_windows.py` och byter bara kontexten, så fallen finns på ett ställe; ändras
    markeringarna där fäller den med ett besked. **`verify_windows.py` på Windows och PIXERA-utgåvan är inte körda.**
  - **`build-app.sh` kör `verify_mac.py`** i stället för `verify.swift` och `verify_pixera.swift` (reglagen före 0.14,
    används inte längre). Bygget går igenom igen; ett fällt prov stoppar det.
  - **Deployad 2026-11-20 22:44** (build 202611202243) till `_applaunchers`, installerad via Suit på M3Ultra och
    "Aktuell" där (Uppdatera listan behövdes först). Live FX:s Matchbox-mapp har 0.18-shadern.
  - **Sett i Live FX (Mac, efter omstart, Junxion 0.18):** A013C004 4K, FOV 90: smalare vägg än förut; Yaw 45 flyttar bil
    och skylt så som 90° över bredden ger. Camera Z-Cam på ett Venice-klipp ritar (samma Entaniya-objektiv, nästan samma
    bild), ingen varning. Inget riktigt Z-Cam-klipp provat.
  - **Windows (2026-11-20 natt, Live FX 9.9):** `verify_windows.py` på 0.18: alla fall PASS, båda utgåvorna och
    Z-Cam-fallen, största fel 0,056 källpixlar; PIXERA-kedjan 0,32. 0.18 installerad med `Install-IgelkottFisheye.ps1`;
    `--canvas` (4K–16384 × 2160, båda utgåvorna): allt PASS, största fel 0,015. Efter omstart ritar noden i projektet `IgelkottFisheye Store` (natt, Tower Bridge, Split 50 %). Wall med FOV 90:
    varje halva 960 px bred visar 90° på bredden; Camera Z-Cam ritar en bild utan varningstecken. Projektets värden
    (Equirect, Yaw 5, Offset Y −200, Right Yaw −124) låg kvar och är återställda efter provet.
    Release v0.18 på GitHub (Windows-zippen) samma natt.
  - **Prestanda och färg på Windows (2026-11-20 natt, i9-9900KS, Radeon RX 9070 XT, Live FX 9.9):** tågklippet
    A007C001 (ProRes 4444 5760², 25 bilder/s, 19,4 MB per bild). Från NAS:en (`W:`) ~16 bilder/s; kopierat till `D:`
    (`D:\IgelkottFisheye-Test`, Intel 660p) 20 bilder/s utan noden och 22,5 med den (läshastigheten från Live FX
    delad med bildstorleken). Live FX använder 65 % av processorn och disken har 718 MB/s över under uppspelningen:
    **gränsen är avkodningen av ProRes 4444 i 5760² på processorn, inte disken och inte noden.** Klippet ligger som
    slot 9 i projektet `IgelkottFisheye Store`, med noden.
    Färgen: projektet har Color Management på, ACES 1.1, ACEScct. Monitors → Interface Rec709 / Gamma 2.4 utan LUT
    ger nästan exakt samma bild som Resolves egen ACEScct → Rec709 Gamma 2.4 (Stages LUT
    `IgelkottStage/Resources/OutputTransforms/…(Resolve).cube`, prövad som Display LUT med Interface ACEScg/ACEScct).
    Klippets egen nod-miniatyr (utan Matchbox) är lika blek som noden: shadern ändrar inte färgen. Inställningen är
    tillbaka på Rec709 / Gamma 2.4, LUT:en ligger laddad men av.
    **Ett nyimporterat klipp får Data Format Rec709 / Gamma 2.4** (Live FX standard), inte ACEScct: det ser då mjölkigt
    och blekt ut. Med Media → Data Format ACEScg (AP1) / ACEScct ser tågklippet ut som i IgelkottStage (Eric:s
    jämförelsebild från Stage 1 på Mac, 2026-11-20). Sätt det på varje klipp: Project Settings → Media Defaults har bara kamerornas RAW-format (ARRI, BRAW, R3D, ProRes RAW m.fl.), inget för ProRes/QuickTime (sett 2026-11-20). Live FX läser annars färgrymden ur filens taggar.
- **0.19 (2026-11-21, Windows): pixeltaggen kostar mindre.** Shaderns tid mätt på grafikkortet (`tools/bench_windows.py`,
  Radeon RX 9070 XT): taggen lästes i varje pixel, 4 hörn × 20 texturläsningar, och var ~84 % av tiden (15360 × 2160:
  7,2 ms per bild med tagg, 1,2 utan). Nu: (1) hörn 0 och 1 som ger samma giltiga tagg avgör (ingen annan tagg kan få
  fler än två röster och lika röster går till hörn 0, så svaret är detsamma), (2) Camera och Pointing båda valda för hand
  läser inte taggen alls, (3) CRC:ns XOR med 39 i fyra steg. 15360 × 2160: 3,9 ms med tagg, 1,2 med handval; 4K 1,2 ms.
  Kostnaden som är kvar är texturläsningarna (en linjär CRC med vektorer provades och gav inget). Ett eget pass för
  taggen hjälper inte: Matchbox-passen har utbildens storlek. `verify_windows.py` och `--canvas` PASS.
  Prestanda i Live FX (tågklippet, se ovan) begränsas av ProRes-avkodningen, inte av noden.
  Release v0.19 på GitHub (Windows-zippen) 2026-11-21.
  Färgen: Live FX visar tågklippet ljusare än filens värden (ffmpeg-avkodad ruta 361 som jämförelse): med klipp och
  Interface båda Rec709 / Gamma 2.4 är skärmens värden ≈ filens^0,455 i hela tonskalan; med ACEScct → Rec709 / Gamma
  2.4 lyfta skuggor och mellantoner (median 0,60 mot förväntat 0,43). Windows HDR är av (dxdiag G22 P709). Klippets
  `colr` är `nclc` 12-17-2 (P3-D65, ST 428, matris ospecificerad), ingen `gama`-atom. Om det är Apples ProRes-avkodare på
  Windows eller Live FX:s visning är inte avgjort; nästa prov är att rendera en ruta ur Live FX till fil.
  **Löst samma natt: det är visningen.** En 16-stegs gråskala som TIFF lyftes lika mycket som ProRes (Interface Rec709 /
  Gamma 2.4: 0 73 102 … 193 … 255 i stället för 0 17 34 … 136 … 255): Live FX lämnar viewern till Windows som linjärt ljus
  och Windows sRGB-kodar den, så Gamma 2.4 kodar två gånger. **Monitors → Interface: Rec709 / Scene Linear** ger rätt
  gråskala och tågklippet ser ut som i IgelkottStage på Mac. Inställt så på Windows-datorn. Atlas:
  [livefx-windows-interface-eotf](../_atlas/knowledge/assimilate/livefx-windows-interface-eotf.md). Provklippen
  (`D:\IgelkottFisheye-Test\ramp\`) ligger som slot 11–13 i `IgelkottFisheye Store`.
- **Ingen CAS-skärpning i shadern** (Eric 2026-11-21: "vi gör inte det"). Övervägt: AMD CAS som ett andra Matchbox-pass
  efter projektionen, som Fisheye to Equis 16K-filter Film.
- **Spara Live FX-projektet med Close Project** innan programmet stängs (2026-11-20): en omstart med Stop-Process tappade
  det som inte hunnit autosparas (klippens färg, dukens storlek, Mode och Monitors → Interface). Efter Close Project och
  ny öppning låg allt kvar.
- **Färg i Store-projektet (Eric 2026-11-20):** alla nio klipp Media → Data Format Color ACEScg (AP1), EOTF ACEScct;
  Settings → Monitors → Interface Colorspace Rec709, EOTF Gamma 2.4 (bilden får normal kontrast). Split View orörd.

- **Loadern (2026-10-06):** IgelkottLiveFXLoader bygger projekt där varje vägg i en slot med ett 8040 × 8040-klipp
  är IgelkottFisheye2D med mallens vinklar och storlek (se loaderns PROJECT.md). Inte öppnat i Live FX än.

## Publik release (påbörjad 2026-10-12)

Eric: "jag vill dela denna plugin på hemsidan så den måste fungera med mac/win med en bra användarupplevelse".
Målgruppen är Live FX-användare som inte känner Igelkott, på Mac och Windows.

**Stabiliseringsverktyget: en webbsida, `stabilizer/index.html`** (2.0 räknar ur Tracking view och har inga fält —
beskrivningen nedan är 1.0; se Tracking view + Stabilizer-sidan ovan)**.** En fil, ingen installation, samma kodbas på Mac och
Windows, och ingenting att signera eller notarisera — en nedladdad app från en okänd utgivare stoppas av Gatekeeper
och SmartScreen, en HTML-fil gör det inte. Den kan ligga på igelkottstudios.com och sparas ner för bruk utan nät;
inget lämnar datorn. Engelska. Dra in Offset X/Y-filerna, ställ trackingvyns FOV och storlek, klicka på punktens
startläge (i en ruta med vyns proportioner, gärna med en skärmbild av vyn indragen), dra i Smoothing, se väg och skak
med spikarna markerade, spara `Stab Yaw.csv`. Felmeddelandena säger vad man ska göra (bara Offset X, Pan 360-export).

- Räkningen är samma som `tools/directionlock.swift --view --smooth`. Provet `node tools/test-stabilizer.mjs` kör
  sidans skriptblock mot facit i `tools/fixtures/vy/` (skillnad 0,0000005°); `build-app.sh` kör det och kräver node.
- Sedd i webbläsare med ett påhittat spår 2026-10-12: kurvorna ritas, spikarna markeras. **Inte provad av Eric, inte
  på Windows, och importen av en fil sparad från sidan är inte gjord i Live FX.**
- Swift-verktyget och `installningar.txt` finns kvar för Igelkotts eget bruk via Suit.

**Inte gjort, och varför:**

- **Filtret på Windows:** ~~var Live FX läser shaders~~ — avläst 2026-10-28 (se Status, Windows). Noden och
  radordningen i Live FX på Windows provade 2026-10-28 (uppifrån, som på Mac). Kvar: provet på NVIDIA.
- **Installerare:** Mac kräver ett Developer ID-certifikat för signering och notarisering; inget finns i nyckelringen
  på m3max. Windows-installeraren kräver sökvägen ovan.
- **Kameraförval för Sensor Height** och andra ändringar i noden väntar till efter demon 2026-10-14: en ny
  filterversion kan nollställa nodernas Manual-läge, Sensor Height och Stab-kurvor i öppna projekt.
- **Quick Start:** väntar på SPL26:s skärmbilder (görs om) och på svaren nedan.
- **Beslut 2026-10-12 (Eric, via SPL26):** ingen installerare och ingen signering — leveransen blir en zip med
  `.glsl`, `.xml`, Stabilizer-sidan och README. Windows pausat till efter London.
- **Nytt att avgöra:** Auto Stabilize är ett kompilerat Mac-program och passar inte i en osignerad zip. Antingen
  signeras det (Developer ID), eller så får publiken Stabilizer-sidan med måtten, eller så byggs den automatiska
  räkningen i sidan (webbläsare läser inte ProRes utom Safari, och bildrutorna måste läsas exakt en i taget).
- **Frågor till Eric** (ställda 2026-10-12): gratis eller betald och e-post för nedladdning; licens; ute till
  Starting Pixel Live eller senare; namn utåt; vart användare hör av sig.

## Öppna frågor (prövas i Live FX)

1. ~~Nodens utformat~~ — ingångens storlek när noden läggs in; sätts under Media → Image Format (Eric 2026-10-06),
   och loadern ger den väggens storlek.
2. ~~Orienteringen~~ — rätt i 0.2 (Eric 2026-10-06). Kvar att jämföra: samma vy som Eq->2D yaw 0 på klippets
   equirect från FisheyetoEqui, sida vid sida.
3. **Topaz-klippen** (`_2_nyx3.mov`) är fragmenterade MOV-filer; IgelkottStage kunde inte läsa dem före 0.77.30. Läser
   Live FX dem? Annars skrivs de om förlustfritt (en vanlig MOV med hela tabellen i `moov`).
4. **Prestanda:** en vägg spelar 25 fps (GFX 0–2 ms, även med noden på 8040 × 8040 och 3 × 3 prov). Nio väggar
   är inte prövade.
5. **Stream Deck:** reglagen heter Yaw, Pitch, Roll och FOV som Eq->2D — styr IgelkottLiveFXDeck dem via REST
   (`/shot/{uuid}/controls`)?

6. **Stab-reglagen i Live FX:** ~~syns kolumnen, får gamla noder 0, går en CSV att importera~~ — ja (2026-10-11).
   Kvar: är det `+`- eller `-`-kurvan som stillar horisonten?
8. ~~Trackern i Live FX~~ — Framing → Stabilize skriver Framing Offset X/Y: minus rörelsen, källpixlar, Y uppåt
   (2026-10-11). Kvar: stillar `Track fisheye Stab Yaw/Pitch.csv` bilden på väggarna, och med vilket tecken? Går en CSV
   med två kurvor att importera på en gång?
11. **Lens Offset för Offroad-klippet** (X ≈ −24, Y ≈ −39 ur bildcirkeln): blir väggarna rätare med det?
12. ~~0.9 på scen~~ — kedjan körd med appen 2026-10-12. Kvar: hur punktens startläge läses av i Live FX för ett
    nytt spår (`--start` i `installningar.txt` står på Offroad-punktens 1166, 793 och gäller alla spår i mappen).
9. **Stabiliseringsnoden:** går IgelkottFisheye i Mode Fisheye (stabilize) att lägga mellan klippet och alla väggars
   noder i `Offroad stab_aces`, och står panelen som IgelkottFisheye?
10. **Live Links** (Curve Editor): går en väggs Stab Pitch att länka till en annan nods, så att en kurva driver alla?
7. **Sensor Height för Venice** (Offroad-plåten, 4096 × 4096): vilken höjd i mm täcker klippet, och behövs Lens Scale
   ovanpå för att linjerna ska vara raka över väggskarvarna?

## Kör projektet

```bash
swift tools/verify.swift          # provet: shadern mot IgelkottStages räkning
swift tools/directionlock.swift --test tools/fixtures   # provet: Direction Lock mot 2025-filerna
swift build -c release --package-path tools/autoyaw --build-path ~/Library/Caches/Igelkott/IgelkottLiveFXFisheye/autoyaw-build && ~/Library/Caches/Igelkott/IgelkottLiveFXFisheye/autoyaw-build/release/autoyaw --selftest   # provet: Auto Stabilize mot en känd pan
node tools/test-stabilizer.mjs    # provet: Stabilizer-sidan mot samma facit
python3 tools/verify_mac.py       # provet: Live FX-utgåvan mot linsmodellen och taggen (CGL; [. --canvas] för dukarna)
./build-app.sh                    # provet (verify_mac.py) + appen i ~/Library/Caches/Igelkott/IgelkottLiveFXFisheye
./deploy-launcher.sh              # appen som _applaunchers/IgelkottLiveFXFisheye.app.zip
IGELKOTT_NO_DIALOG=1 IGELKOTT_MATCHBOX_DIR=/tmp/x <app>/Contents/MacOS/IgelkottLiveFXFisheye   # installationen mot en provmapp
```

På Windows:

```bash
python tools/verify_windows.py    # provet: shadern på datorns grafikkort (OpenGL, som Live FX på Windows)
powershell -ExecutionPolicy Bypass -File windows/Install-IgelkottFisheye.ps1 -Quiet [-Target <provmapp>] [-Uninstall]
powershell -ExecutionPolicy Bypass -File windows/build-package.ps1   # paketet: _releases/IgelkottFisheye/IgelkottFisheye-Windows.zip
```

## IgelkottSuit

- Artefakt: `_applaunchers/IgelkottLiveFXFisheye.app.zip` (kind: zipApp, `post_install: launch` — Suit startar appen, som
  lägger noden i Live FX:s Matchbox-mapp; starta sedan om Live FX).
- Post i `_atlas/suite.yaml`: `id` = IgelkottLiveFXFisheye.
- Senast verifierad installerad via Suit: 2026-11-20 (0.18, build 202611202243, M3Ultra, "Aktuell")

Kontrakt: [igelkottsuit-contract](../_atlas/knowledge/macos/igelkottsuit-contract.md).

## Delad kunskap det här projektet lutar sig mot

- [Live FX Matchbox](../_atlas/knowledge/assimilate/matchbox.md) — var Live FX läser shaders, vad SpaMatchbox stöder.
- [Eq-2D: FOV lodrät, yaw/pitch](../_atlas/knowledge/assimilate/eq2d-fov-framing.md)
- IgelkottStage: `StageKit/FisheyeLens.swift` (objektivet, plattförskjutningen), `StageProtocol/CameraCost.swift` (kameran).
