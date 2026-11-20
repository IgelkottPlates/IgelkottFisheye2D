---
from: SPL26 (Cowork-planering av Starting Pixel Live 26)
to: IgelkottLiveFXFisheye
date: 2026-10-11
deadline: 2026-10-13
urgency: high
topic: Live-tracking → Stab-reglagen med Erics formel i noden, och visningsnamnet "IgelkottFisheye"
status: done
---

# Från SPL26 till IgelkottLiveFXFisheye: tracka live, formeln i noden, namnet IgelkottFisheye

## Vad har hänt

0.5 är installerad på m3max och provad i `Offroad stab_aces` (2026-10-11):

- Stab-kolumnen syns och noderna från före 0.3 fick reglagen med 0 (öppen fråga 6: ja).
- `Stab Pitch +.csv` (rätt offset 2498 i källklippet, skala ×1,69, centrerad) ligger på **Stab Pitch** i Back, Sky,
  Ref TV, Hard Light och LED1–4. Side är avstängd och tog inga keys. Back hade kurvan kvar på Pitch från före 0.3;
  den är nollad och kurvan flyttad till Stab Pitch.
- Verifierat på Back: Stab Pitch följer kurvan per frame (−0,05 vid 225, −1,38 vid 900, −0,73 vid 1095), och Stab
  Pitch 10 i Off-läge tippar bilden kraftigt. Keys → reglage → bild fungerar.

## Vad Eric vill (2026-10-11)

> "i demon ska jag tracka en punkt live, pluginen måste kunna göra i min enkla formel för trackingdatan. sen ska det
> stå IgelkottFisheye."

1. **Live-tracking:** på scen trackar Eric en punkt (berget vid horisonten) i Live FX. Trackingdatan ska gå in i
   noden, och noden räknar Erics formel och driver Stab Yaw/Pitch, utan export till Numbers och import av CSV.
2. **Namnet:** i panelen ska det stå **IgelkottFisheye** (i dag står fliken "Fisheye" och noden "IgelkottFisheye2D").

## Erics formel ("Direction Lock", DL)

Avläst ur hans 2025-filer i `~/Documents/Mall Direction lock csv test/test/` (`Tracked mountain Yaw.csv` →
`… Yaw_DL.csv`, `Pitch.csv` → `Pitch_DL.csv`, `… _DL1.3.csv`, `VR__X019_2404151127_Yaw_DL-1.3.csv`), stämmer på
sex decimaler:

```
ut[0] = t[0]
ut[n] = (t[n] − t[n−1]) + k · ut[n−1]
```

- t = trackad vinkel (Pan 360 Yaw/Pitch, grader), ut = korrektionen.
- **DL:** k = 1/2. **DL1.3:** k = 1/1,3 ≈ 0,769.
- Betydelse: skakningen (snabb ändring) rättas, men korrektionen klingar av, så att långsamma svängar i vägen inte
  "stabiliseras bort" (riktningen följer bilen). Ett högpassfilter på trackingen.
- Det finns även "DL future"- och "plus difference future frame"-varianter (tittar en frame framåt); de är inte
  avlästa. Inte nödvändiga för demon.
- En annan variant finns i `med formler-Scene 34…csv` (27 rader): `ut[n] = t[n] − 0,5 · t[n−1]`. DL-formeln ovan
  är den som går igen i flera filer.

Föreslagna reglage: **Track X, Track Y** (punktens läge från trackern), **DL Factor** (k, standard 0,5),
**Track Strength** (0–1, för före/efter på scen), och att Stab Yaw/Pitch = ut + det manuella värdet.

## Det jag inte vet och du måste avgöra

- [ ] **En Matchbox-shader har inget minne mellan frames.** `ut[n]` beror på `ut[n−1]`, så formeln kan inte räknas i
      GLSL utan historik. Antingen
      (a) en sluten form som shadern kan räkna ur det den får (t.ex. om Live FX ger trackerns hela kurva eller flera
      frames via en länk), eller
      (b) ett litet hjälpverktyg (REST mot Live FX, port 8080, eller CSV in/ut) som läser trackerkurvan efter
      trackingen, räknar DL och skriver Stab-kurvan på **alla** väggars noder på en gång. Ett knapptryck på Stream
      Deck efter trackingen räcker för demon.
      Välj det som fungerar säkert live; skriv i PROJECT.md vad du valde och varför.
- [ ] **Var trackar man i fisheye-kedjan?** 2025 trackades i equirect (Pan 360 gav grader direkt). Nu finns ingen
      equirect: rimligast är Live FX:s tracker på Back-väggens utbild (IgelkottFisheye2D med Stab 0). Den ger pixlar,
      inte grader. Omräkning: vinkel = atan(Δpx / f), f = (höjd / 2) / tan(FOV / 2), med tecknen enligt PROJECT.md
      (nos upp α → Stab Pitch −α). Kontrollera hur Live FX:s tracker exporterar/länkar sina värden (Live Links-fliken
      i Curve Editor finns) innan du bygger.
- [ ] **Namnbytet får inte bryta demoprojektet.** `Offroad stab_aces` och loadern refererar `IgelkottFisheye2D`. Om
      noden döps om (Name i XML / filnamn) försvinner den ur befintliga projekt. Eric vill att det **står**
      IgelkottFisheye; minst är att fliken (`DisplayName="Fisheye"`) och beskrivningen visar "IgelkottFisheye". Ska
      själva nodnamnet bytas: låt den gamla ligga kvar installerad bredvid, och skicka handoff till
      IgelkottLiveFXLoader.

## Vad jag förväntar mig att du gör

- [ ] Panelen visar **IgelkottFisheye**, utan att `Offroad stab_aces` slutar fungera.
- [ ] Live-tracking → DL-formeln → Stab Yaw/Pitch på alla väggar, enligt (a) eller (b) ovan.
- [ ] Prov i `tools/verify.swift` mot Erics 2025-filer: `Tracked mountain Yaw.csv` med k = 0,5 ska ge
      `Tracked mountain Yaw_DL.csv`, k = 1/1,3 ska ge `… _DL1.3.csv`.
- [ ] Ny version via `_applaunchers` och Suit; skriv i PROJECT.md vad Eric gör på scen, steg för steg (tracka →
      knapp/länk → före/efter).
- [ ] Sätt `status: acknowledged` med en rad om vad du byggde, `done` när Eric har provat det i Live FX.

## Var finns underlaget

- Demoklippet: `~/Movies/SPL26 demo media/Offroad stab/Offroad 130-175s.mov` (4096², 1124 frames, ACEScct).
- Projektet: `Offroad stab_aces` (Live FX 9.9 på m3max), N[3] = efter, N[2] = före.
- Formelfilerna: `~/Documents/Mall Direction lock csv test/test/` och
  `~/Documents/Mall Direction lock csv test/SPL26 Offroad 130-175s/`.
- Demon: ons 14 okt 10:05, Rich Mix London. Eric reser 13 okt; det som ska provas måste vara installerat på m3max
  innan dess.

## Anteckning

IgelkottLiveFXFisheye 2026-10-11 (0.6, build 202610112137, i `_applaunchers`; inte installerad eller provad i Live FX):

- **Namnet:** fliken och beskrivningen heter IgelkottFisheye. Filnamnet `IgelkottFisheye2D` är kvar, så
  `Offroad stab_aces` och loadern rörs inte.
- **Valet: (b), ett verktyg.** Shadern har inget minne, och REST-API:t (läst i Live FX:s medföljande dokumentation)
  har nyckelbilder bara för framing och kamera, inte för en nods reglage, och ingen tracker. Direction Lock ligger i
  appen: tracker-CSV i `~/Movies/IgelkottFisheye Direction Lock/` → starta appen → `Stab/… Stab Yaw.csv` och
  `… Stab Pitch.csv`. Formeln stämmer mot 2025-filerna (k = 1/2 → `_DL`, k = 1/1,3 → `_DL1.3`, skillnad 0,0000014).
- **Alla väggar på en gång:** nytt läge, Mode Fisheye (stabilize) — en nod före väggarna bär Stab-kurvan. Räknat i
  provet, inte provat i Live FX.
- **Blockerar (Eric i Live FX):** hur trackern exporterar sin kurva (pixlar/normerat, y-håll, namn) — skicka en
  exporterad tracker-CSV, så ställs `--pixels` och tecknen efter den. Om stabiliseringsnoden går att lägga före alla
  väggar. Hela kedjan på scen (PROJECT.md, "På scen").

## Avslut

Stängd 2026-10-12: panelen heter IgelkottFisheye (sedd i Live FX med 0.6), och trackingen går via trackingvyn i 0.9.
