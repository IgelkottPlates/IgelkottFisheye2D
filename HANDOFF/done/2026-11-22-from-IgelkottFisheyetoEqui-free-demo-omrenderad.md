---
from: IgelkottFisheyetoEqui
to: IgelkottLiveFXFisheye
date: 2026-11-22
deadline: när filerna är klara (raden SLUT i läget nedan)
urgency: normal
topic: Free Demo 2025 renderas om med 2.09 — watermark-fisheye (ruta rätt, colr 12-17-2) och equi 16K (colr 12-17-2, nytt namn utan _fisheye); koda om NotchLC och mät
status: done
---

# Från IgelkottFisheyetoEqui till IgelkottLiveFXFisheye: Free Demo 2025 omrenderad, mät NotchLC igen

Uppföljning av `2026-11-22-from-IgelkottFisheyetoEqui-svar-colr-och-ruta.md`. Eric bad om omrenderingen 2026-11-22
("1."). Den körs nu på m1ultra med Fisheye to Equi **2.09**.

## Vad har hänt

Mastrarna i `igelkottstore.com/2025/Free Demo 2025/Store/*_fisheye_Gamma-ACEScct_AP1.mov` är oförändrade. Det är
Darkroms nio mastrar från 2026-11-20, med colr 12-17-2 och rätt rutantal. Ur dem görs två filer per klipp:

| Fil | Var | Vad som är nytt |
|---|---|---|
| Demo-watermark, fisheye 4444 | `Store/_Demo-watermark/<stam>_ProRes4444.mov` (samma namn som förut) | Ut-ruta n = master-ruta n, ingen dubblerad ruta 0, sista rutan med. colr 12-17-2. |
| Equi 16K, 422 HQ | `Store/_Equi/<klipp>_Gamma-ACEScct_AP1_16K360_ProRes422HQ.mov` (**nytt namn, utan `_fisheye`**) | colr 12-17-2. Samma inställningar som butiksbatchen 2026-11-21: Venice, 15360×7680, film 16K (Gauss 0,45, CAS 50 %), demo-watermark. |

- Före utbytet kontrolleras varje fil:
  - rutantal och tidkod som mastern;
  - colr 12-17-2 och ramhuvud 12-17-1;
  - watermark-filerna: ut-ruta n jämförd med master-ruta n i början och slutet;
  - equi-filerna: bilden jämförd med den gamla equin i första, mittersta och sista rutan (PSNR ≥ 45 dB, väntat i stort
    sett identisk, eftersom bara märkningen ska skilja);
  - kopian till servern kontrollerad med SHA-256.
- De gamla filerna flyttas till `_ersatt-2026-11-22/` i respektive mapp, inte raderade.
- Läget, en rad per klipp och `SLUT` sist, står i
  `IgelkottFisheyetoEqui/docs/loggar/omrendering-free-demo-2026-11-22.state` i Drive.

## Varför du behöver veta

- NotchLC-filerna i `Store/_NotchLC/` och `/Volumes/8TB/_NotchLC/` bygger på de gamla filerna. Fisheye-NotchLC ligger en
  ruta fel, och alla har tonkurvan från 12-17-1.
- Equi-filerna har nytt namn. Era verktyg söker `*_16K360_ProRes422HQ_1.mov` i `_NotchLC`. AME:s namn blir då
  `<klipp>_Gamma-ACEScct_AP1_16K360_ProRes422HQ_1.mov`, vilket fortfarande matchar mönstret, men stammen saknar `_fisheye`.

## Vad jag förväntar mig att du gör

- [ ] När `SLUT` står i läget: koda om NotchLC med BEST MAX ur de nya filerna, både fisheye och equi.
- [ ] Mät med `tools/compare_eq2d.py --notchlc`. Klart när:
      - tonkurvan är borta (NotchLC lika med källan);
      - fisheye och equi visar samma ögonblick;
      - geometrin på alla nio klippen är som A007C001 (median ~1 px, utan spridningen p95 5–19 px).
- [ ] AME-provet på A/B i `/Volumes/360_Production/Tester/colr-prov 2026-11-22 FisheyetoEqui/`, om det inte redan är gjort.
- [ ] Säg till om tonkurvan finns kvar med 12-17-2, eller om fisheye och equi fortfarande ligger isär.

## Anteckning

- 2026-11-22 (IgelkottLiveFXFisheye, M3Ultra): läst. Omrenderingen pågår (läget: START 16:07, första klippet renderas).
- `tools/compare_eq2d.py` hittar nu equi-filen också utan `_fisheye` i namnet.
- Väntar på `SLUT`, sedan NotchLC med BEST MAX och mätning. A/B-provet är nåbart härifrån men inte gjort.
- 2026-11-23: alla 18 filerna kodade till NotchLC (BEST MAX) i `/Volumes/8TB/_NotchLC/`, och A/B-provet är gjort:
  colr är orsaken. Men tonkurvan finns kvar i de nya filerna: 2.06+ rättar colr inuti `glbl`, inte filens egen
  `colr`-atom. Rutan stämmer nu. Svar: `IgelkottFisheyetoEqui/HANDOFF/2026-11-23-from-IgelkottLiveFXFisheye-colr-fel-atom.md`.
  Mätningen av NotchLC väntar på rättade filer (Eric).
- 2026-11-23 (IgelkottLiveFXFisheye, Windows): stängd på Erics ord ("Ja, flytta"). Ersatt av `2026-11-23-from-IgelkottFisheyetoEqui-alla-18-rattade.md`, som har omkodningen och mätningen kvar.
