---
from: SPL26 (Cowork-planering av Starting Pixel Live 26)
to: IgelkottLiveFXFisheye
date: 2026-10-11
deadline: 2026-10-13
urgency: high
topic: Sfärrotation (Stab Yaw/Pitch/Roll) i IgelkottFisheye2D så att stabilisering korrigerar hela sfären på en gång
status: done
---

# Från SPL26 till IgelkottLiveFXFisheye: sfärrotation för stabilisering

## Vad har hänt

Inför livedemon på Starting Pixel Live (ons 14 okt 10:05) ska Eric visa före/efter-stabilisering av
Offroad-plåten (Mojito, Scene 34, A002C003_250311W6) i Live FX med IgelkottFisheye2D.

- Demoklippet är renderat ur Venice-originalet (X-OCN 8.6K) i Resolve, ACEScct, ProRes 4444, 4096 × 4096 fisheye,
  25 fps, 1 124 frames (källsekund 130–175):
  `~/Movies/SPL26 demo media/Offroad stab/Offroad_Scene34_A002C003_fisheye4096_ACEScct.mov`
- Projektet byggdes med IgelkottLiveFXLoader: `Offroad stab_aces` (Multiproj 16K360-mallen, grenarna Back, Side, Sky,
  Ref TV, Hard Light, LED1–4, var och en med egen IgelkottFisheye2D).
- Stabiliseringskurvan från 2025 (equirect, Pan 360 Pitch) är omräknad till klippets frames 0–1124 och centrerad runt 0:
  `~/Documents/Mall Direction lock csv test/SPL26 Offroad 130-175s/LED1 Pitch stab +.csv` (och `… -.csv` med omvänt
  tecken). Värden ca −0,6° … +1,3°, en nyckel per frame.
- Provad på en enskild gren: kurvan importerades på Pitch i Back-grenens nod. Det är **fel modell** — Pitch där är
  vyns riktning, så bara Back rör sig; övriga väggar får ingen eller fel korrektion.

## Varför du behöver veta

Eric (2026-10-11): stabiliseringen ska ligga först, så att hela sfären korrigeras samtidigt. I dag har noden bara
vyns Yaw/Pitch/Roll per vägg. Det finns ingen gemensam punkt före grenarna där sfären kan roteras: Pan 360 kräver
equirect, och en x/y-förskjutning av fisheyebilden är inte en rotation (vid tippning fram/bak står punkterna rakt åt
sidan still, en förskjutning flyttar dem).

## Vad jag förväntar mig att du gör

- [ ] Lägg till tre reglage i IgelkottFisheye2D: **Stab Yaw, Stab Pitch, Stab Roll** (grader, standard 0, animerbara).
- [ ] Applicera dem som en världsrotation **före** vyns rotation, samma konvention som vyn:
      `S = Ry(stabYaw) · Rx(−stabPitch) · Rz(stabRoll)`, källriktning `d = S · R_vy · ray`
      (där `R_vy = Ry(yaw) · Rx(−pitch) · Rz(roll)` som i dag). Samma S på alla väggar ⇒ hela sfären vrids lika.
- [ ] Bekräfta tecknet: positiv Stab Pitch ska motverka att bilens nos tippar upp. Dokumentera i PROJECT.md vilket håll
      som är vilket, så att CSV-kurvor kan importeras utan gissning.
- [ ] Utöka `tools/verify.swift`: med S ≠ identitet ska vyerna Back, Side, Sky och Ref TV flyttas konsistent
      (samma världspunkt hamnar på samma sfärposition i alla vyer).
- [ ] Bygg, deploya och installera via Suit, starta om Live FX.
- [ ] Prov i `Offroad stab_aces`: importera `LED1 Pitch stab +.csv` på **Stab Pitch** i varje grens nod
      (Animate → Curve Editor → markera parametern → Import; rubrikradens nodnamn behöver inte matcha — importen
      gick på Back med en rubrik exporterad från LED1). Jämför version Black-N[2] (före) och Black-N[3] (efter):
      horisonten ska vara stillare på **alla** väggar. Byt till `-`-filen om det blir värre.
- [ ] Städa i Black-N[3]: ta bort Pitch-kurvan på Back-grenens nod och den platta 0-kurvan på LED1 (provet ovan).
      Back-noden har dessutom Framing Offset X/Y med 224 nycklar som inte kom från SPL26-sessionen — kontrollera
      ursprunget innan stab-provet, så att de inte krockar.

## Bakgrund och länkar

- CSV-format som Live FX exporterar för en Matchbox-parameter (läst 2026-10-11):
  ```
  #ANIM Matchbox.__<mallens klippnamn>_1[9]\Pitch
  #COND CC
  <frame>,<värde>,<frame>,<värde>,<frame>,<värde>
  ```
  2025-filerna (Pan 360) använder `;` och två kolumner; båda importerade.
- Originalkurvor: `~/Documents/Mall Direction lock csv test/` (`med formler-Scene 34…csv`, `utan formler-…csv`,
  yaw-varianter i `test/` för A001C008).
- Förslag till nästa steg (separat handoff om det blir aktuellt): IgelkottLiveFXLoader tar en stab-CSV och lägger den
  på Stab Yaw/Pitch/Roll i alla grenar när projektet byggs.
- Relaterat: `../_atlas/knowledge/assimilate/matchbox.md`, `../_atlas/knowledge/assimilate/eq2d-fov-framing.md`.

## När du är klar

1. Sätt `status: done` i frontmattern.
2. Flytta filen till `HANDOFF/done/`.
3. Säg till Eric att EFTER-versionen är redo att spelas in som backup till demon.

## Anteckning

IgelkottLiveFXFisheye 2026-10-11 (session på m3max):

- Klart: Stab Yaw / Stab Pitch / Stab Roll i noden (0.3, build 202610112035), S = Ry(stabYaw) · Rx(−stabPitch) ·
  Rz(stabRoll) före vyns rotation. `tools/verify.swift` går igenom, också provet att Back, Side, Sky och Ref TV vrids
  med samma S. Deployad till `_applaunchers/IgelkottLiveFXFisheye.app.zip`.
- Tecknet: med formeln ovan hämtar väggen rakt fram källan högre upp vid Stab Pitch +. Det rättar en nos som tippar
  **ner**; nos upp α° rättas med Stab Pitch −α. Handoffens formel och önskan "+ motverkar nos upp" går inte ihop;
  formeln fick styra. Står i PROJECT.md under Stabilisering. `+`- och `-`-filen avgör i praktiken.
- Blockerar: allt i Live FX är Erics — installera via Suit på Live FX-Macen, starta om Live FX, importera kurvan på
  Stab Pitch i varje gren, jämföra Black-N[2] och Black-N[3], städa Black-N[3] (Pitch-kurvan på Back, 0-kurvan på
  LED1, Framing Offset-nycklarnas ursprung). Okänt tills det är provat: om noderna i det redan byggda projektet får
  de nya reglagen med 0.
- Handoff skickad till IgelkottLiveFXLoader om de tre nya reglagen.
- 2026-10-11 (senare, enligt SPL26:s andra handoff): 0.5 installerad på m3max, Stab-kolumnen syns, gamla noder fick 0,
  kurvan ligger på Stab Pitch på alla aktiva väggar och Back är städad. Kvar innan `done`: Eric bekräftar att
  horisonten är stillare (rätt tecken), LED1:s 0-kurva och Framing Offset-nycklarnas ursprung.

## Avslut

Stängd 2026-10-12: Stab-reglagen är installerade och används (Stab Yaw via trackingvyn, Eric: "det ser ut att fungera"). Bara pan stabiliseras, så frågan om `+`/`-` på Pitch-kurvan föll bort.
