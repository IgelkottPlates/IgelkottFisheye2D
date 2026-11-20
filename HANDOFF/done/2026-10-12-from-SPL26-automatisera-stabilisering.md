---
from: SPL26 (Cowork-planering av Starting Pixel Live 26)
to: IgelkottLiveFXFisheye
date: 2026-10-12
deadline: efter Starting Pixel Live (2026-10-14), före publik release
urgency: high
topic: Stabiliseringen måste automatiseras — Eric ska inte mata in FOV, bildstorlek eller startpunkt
status: done
---

# Från SPL26: automatisera Stab Yaw

## Erics ord (2026-10-12 16:53)
"detta måste automatiseras, kan inte va ansvarig för detta"

## Vad som gick fel i dag
Eric följde flödet Track 1 Point → Apply Stabilize → exportera Offset X/Y → stabilizer-sidan.
Sidan kräver att användaren själv vet och skriver in:
- nodens **FOV** (sidan hade 60, noden stod på 90),
- **bildstorleken** i tracking-vyn (sidan hade 3840 × 2160, vyn var 4096 × 4096),
- **startpunkten** i pixlar (det finns ingen bild att klicka på; Eric gissade X 2813 / Y 1658).
Varje fel ger fel vinklar utan varning. Dessutom startade Offset X på -434 (lagat i demokopian, se handoff `…-stabilizer-offset-start.md`).

## Mål
Plate in → Stab Yaw-kurva ut, utan manuella mått och utan klick på en punkt.

## Förslag att utvärdera
1. **Egen tracker, utan Live FX-steget:** släpp in fisheye-klippet (ProRes/EXR), hitta automatiskt en avlägsen punkt nära horisonten (flera punkter + median), räkna yaw direkt i fisheye-geometrin (linsmodellen finns redan i shadern) och skriv Stab Yaw.csv. Ingen FOV/bildstorlek behövs eftersom spårningen sker i fisheyen.
2. **Om Live FX-tracking behålls:** läs nodens FOV/Media-storlek och trackerns startpunkt ur Live FX-projektet eller metadata i stället för att fråga användaren. (Hittade inga projektfiler under ~/Movies/SPL26 Genomgang — projekten verkar ligga i Assimilates databas; undersök.)
3. **Minsta möjliga nödlösning:** instruera "vrid nodens Yaw/Pitch så att berget ligger mitt i bild innan du trackar" → startpunkt = mitten, sidan behöver bara FOV. Sidan ska då sätta startpunkten till mitten automatiskt när bildstorleken ändras.

## Klart när
Eric kan stabilisera en ny plate utan att skriva in ett enda tal.

## Anteckning

IgelkottLiveFXFisheye 2026-10-12 (0.10, build 202610121705, i `_applaunchers`; inte installerad):

- **Valt: förslag 1, egen räkning utan Live FX-steget** — men utan att leta punkter. Med objektivet rakt upp är pan en
  vridning av bilden kring objektivets mitt, så hela bandet över horisonten jämförs mellan två bildrutor
  (`tools/autoyaw.swift`). Inget FOV, ingen bildstorlek, ingen startpunkt; bildtakten och bildcirkelns mitt läses ur
  klippet.
- **I appen:** starta IgelkottLiveFXFisheye → "Stabilisera ett klipp …" → välj råklippet → `Stab/<klipp> Stab Yaw.csv`.
- **Mätt på Offroad** (19 s för 1124 bildrutor): mot molnspåret genom objektivets modell korrelation 0,9996, största
  skillnad 0,035°; mot trackingvyn utan dess spikar 0,998. Inga spikar, där trackern hade nio.
  Kurvan ligger i `Stab/Offroad 130-175s Stab Yaw.csv`.
- **Shadern är orörd** (samma filer som står installerade), så 0.10 kan installeras utan att Live FX ser ett nytt
  filter.
- **Inte gjort:** importerad eller sedd i Live FX; prövad på något annat klipp; pitch och roll.
- **Gränser:** bara Mac (AVFoundation), bara pan, kvadratiskt klipp med kameran rakt upp.
- **Klart när** Eric har stabiliserat en plåt med knappen. Förslag 2 och 3 är inte byggda; Stabilizer-sidan finns kvar
  som reserv.

## Anteckning 2

2026-10-12 (kväll): Eric vill behålla Live FX-trackingen och exporten ("live fx ska exportera stabiliserade keyframes,
det är ok") och få sidan och pluginen att ta bort det tekniska tillsammans. Byggt, **inte utlagt i `_applaunchers`**:

- **Noden 0.11: Mode Tracking view** — fast skala 0,02° per pixel, lika i hela bilden. Bara Yaw riktar vyn.
- **Stabilizer-sidan 2.0** — inga fält. Pan = −(Offset X − första nyckeln) · 0,02, så varken FOV, bildstorlek eller
  startpunkt behövs. Smoothing och övriga val ligger under Options.
- Prov: shadern (`tools/verify.swift`), sidan mot en känd pan (`node tools/test-stabilizer.mjs`), och att skalan är
  densamma i shadern, sidan och Swift-verktyget.
- **Inte provat i Live FX.** Din demokopia av sidan (`~/Movies/IgelkottFisheye for Live FX/…`) är 1.x med fälten och
  hör ihop med Mode Wall; 2.0 kräver nod 0.11. Blanda inte.
- **Utlagt** samma kväll (build 202610121905), sedan Eric sagt att nollställningen inte är något att oroa sig för.
  **Väntar på:** installation via Suit och Erics prov. Auto Stabilize (0.10) finns kvar som väg utan tracker.

## Anteckning 3

2026-10-12 19:30: 0.11 är installerad och Eric har trackat i Tracking view och släppt exporten i sidan 2.0 — skalan
stämmer utan inmatade tal (lutning 0,94 mot panen räknad ur klippet). Sidan 2.1 lagar spikar själv ("Fix spikes
automatically", plus dra över en spik för hand); på Erics export går skaket från −3,42 … +1,70° till −1,49 … +0,91°.
Kvar: importera kurvan och se den på väggarna.

## Avslut

2026-10-19: klart. Mode Tracking view (0.11, installerad på m3max) och Stabilizer-sidan (3.0) — inga tal skrivs in
för fisheyen; Eric 2026-10-13: "fungerar". Sidan tar dessutom emot Pan 360-grader och pixlar ur en equirect.
