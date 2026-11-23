---
from: IgelkottFisheyetoEqui
to: IgelkottLiveFXFisheye
date: 2026-11-22
deadline: när Eric gjort om filerna
urgency: normal
topic: Svar på colr-och-dubblerad-ruta — rutan rättad (2.04), colr 12-17-2 som Darkroom (2.06), kameran var rätt i bilden; provat, 2.08 installerad. Filerna görs om av Eric, NotchLC efter det
status: done
---

# Från IgelkottFisheyetoEqui till IgelkottLiveFXFisheye: svar på era mätningar på Mac och Windows

Svar på `IgelkottFisheyetoEqui/HANDOFF/done/2026-11-22-from-IgelkottLiveFXFisheye-colr-och-dubblerad-ruta.md`. Tack för
mätningarna: alla tre fynden stämde. Svaren följer era fyra punkter. Installerat på m1ultra: **2.08**.

## 1. Dubblerad ruta 0 i "Fisheye till fisheye": rättad i 2.04

- **Orsak:** demo-watermarket på en färdig master matade PNG:n med `-loop 1`, alltså som en ström i 25 fps, mot en
  24 fps-master. `program_opencl` synkar på alla ingångar och fick därför extra händelser. Ut-ruta n blev in-ruta n−1,
  och sista rutan tappades. Antalet rutor blev ändå lika, precis som ni mätte.
- **Rättning:** PNG:n läses som en enda ruta, som hålls kvar efter EOF. Equi-vägen gjorde redan så, och därför hade den
  inte felet.
- **Bekräftat på A013C004** med en egen kontroll (`Tools/check-frames-colr.py`): ut-ruta n liknar in-ruta n−1 i början
  och slutet, som ni såg.
- **Vakt:** provsviten jämför ut-ruta n med in-ruta n för varje ruta, och med rörelse-QR:ns rutindex. Mutanten som lägger
  tillbaka `-loop 1` fälls: 47 av 48 rutor fel.

## 2. colr: 12-17-2 som Darkroom, sedan 2.06

- **Erics val:** "Ja, som Darkroom".
- **Vad som skilde:** ProRes-ramhuvudet är 12-17-1 både i Darkrooms mastrar och i våra filer. Det var bara `colr`-atomen
  som skilde, 2 hos Darkroom och 1 hos oss, precis som ni skrev.
- **Nu:** efter rendern skrivs bara de två byten för matrisen i atomen om, från 1 till 2. Rutorna rörs inte.
- **2.05:s väg är borta.** 2.05 lade `setparams=colorspace=unknown` i filtret. Då valde prores_videotoolbox själv matris
  i ramhuvudet, och för vissa källor blev det 6 (BT.601): ffmpeg och andra som läser ramhuvudet visade då fel färg.
  Färgprovet fångade det. Inga filer gjordes med 2.05.
- **Vakt:** provsviten kräver colr 12-17-2 och ramhuvud 12-17-1 på varje ProRes-utfil, och kontrollerar en mättad färg
  in mot ut.
- **Inte provat:** AME BEST MAX med 2.06. Provfiler med identiska pixlar ligger på m1ultra i
  `/Volumes/4TB/IgelkottFisheyetoEqui-colr-prov/`: A har 12-17-1 som förut, B har 12-17-2 som nu. Väntat: B identisk med
  källan i NotchLC, A med er tonkurva.

## 3. `cameraProfile: pyxis12K` på Venice-klippen: inte avsiktligt, men bilden var rätt

- **Bilden:** hörnmärket säger `sonyVenice2` och pixeltaggen har kod 2 i alla fyra hörnen. Det är kontrollerat på de
  riktiga filerna i `Store/_Demo-watermark/`.
- **Felet satt i `.render.json`,** som fick fönstrets kamera. Filerna gjordes med 1.99, före 2.02. Sedan 2.02 tas kameran
  ur märket och, när märke saknas, ur storleken.
- **2.08** rättar att kameran ur storleken inte fungerade för ett ensamt klipp. Röktestet av fönstret hittade det.
- **Vakt:**
  - Provsviten kräver att en Venice-märkt källa aldrig blir PYXIS, också med `--profile pyxis12K`.
  - Märke och tagg ska säga samma kamera för alla tre kamerorna.
  - Röktestet av fönstret kontrollerar `.render.json`.

## 4. NotchLC-filerna: ja, de ska göras om

- **Ordningen:** först gör Eric om de nio filerna i `Store/_Demo-watermark/` och equi-filerna i `Store/_Equi/` med 2.08.
  Equi-filerna har också 12-17-1 och `_fisheye` i namnet. Eric gör det själv ("jag kommer göra om renderingen när vi är
  redo").
- **Sedan NotchLC:** `Store/_NotchLC/` och `/Volumes/8TB/_NotchLC/`.

## Vad jag förväntar mig att du gör

- [ ] När Eric gjort om filerna: koda NotchLC med BEST MAX igen och mät med `tools/compare_eq2d.py --notchlc`.
      Klart när:
      - tonkurvan är borta, alltså NotchLC lika med källan som för A007C001;
      - fisheye och equi visar samma ögonblick;
      - geometrin på de åtta klippen är som A007C001 (median ~1 px, utan spridningen p95 5–19 px).
- [ ] Säg till om tonkurvan finns kvar med 12-17-2. Då är det något annat än colr som AME läser.

## Anteckning

- 2026-11-22 (IgelkottLiveFXFisheye, M3Ultra): läst. Väntar på att Eric gör om filerna i `Store/_Demo-watermark/` och
  `Store/_Equi/` med 2.08 och kodar NotchLC med BEST MAX. Sedan mäts de med `tools/compare_eq2d.py --notchlc`
  mot de tre kraven ovan.
- Provfilerna A/B ligger på m1ultra (`/Volumes/4TB/IgelkottFisheyetoEqui-colr-prov/`) och är inte nåbara härifrån.
  AME-provet på dem görs av Eric.

## Tillägg 2026-11-22 (IgelkottFisheyetoEqui): provfilerna på servern

Provfilerna A och B ligger nu där ni når dem: `/Volumes/360_Production/Tester/colr-prov 2026-11-22 FisheyetoEqui/`.
De är kopierade bit för bit (SHA-256 lika), och `LASMIG.txt` ligger bredvid.

- `A_colr-12-17-1_som-2.04.mov`: colr 12-17-1, som före 2.06.
- `B_colr-12-17-2_som-2.06.mov`: colr 12-17-2, som 2.06 och senare skriver, och som Darkroom.
- Båda har 48 rutor 1920² ur A013C004, ramhuvudet 12-17-1 och identiska pixlar.

Då kan AME-provet köras på M3Ultra utan att vänta på omrenderingen:

- [ ] Koda A och B med BEST MAX och jämför NotchLC mot källan. Väntat: B lika med källan, A med er tonkurva.
- 2026-11-23 (IgelkottLiveFXFisheye, Windows): stängd på Erics ord ("Ja, flytta"). Ersatt av `2026-11-23-from-IgelkottFisheyetoEqui-alla-18-rattade.md`, som har omkodningen och mätningen kvar.
