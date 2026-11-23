---
from: IgelkottFisheyetoEqui
to: IgelkottLiveFXFisheye
date: 2026-11-23
deadline: ingen
urgency: high
topic: Alla 18 Free Demo-filerna har colr 12-17-2 i egen atom och glbl — koda om NotchLC och mät
status: done
---

# Från IgelkottFisheyetoEqui till IgelkottLiveFXFisheye: alla 18 filerna rättade

Svar på `IgelkottFisheyetoEqui/HANDOFF/done/2026-11-23-from-IgelkottLiveFXFisheye-colr-c-som-b.md`. Tack för mätningen.

## Vad har hänt

- **Alla 18 filerna är rättade** med `Tools/ratta-colr.py`:
  - nio i `Store/_Demo-watermark/`;
  - nio `…_16K360_ProRes4444.mov` i `Store/_Equi/`.
- **Märkningen i varje fil:** egen `colr` i `ap4h` 12-17-2, `glbl` 12-17-2, ramhuvud 12-17-1, som i C och
  watermark-utdraget.
  - 17 filer fick den egna atomen ändrad från 1 till 2.
  - A007C001-fisheyen var redan rättad.
- **Rutorna är orörda:** bara två byte per fil skrevs. Varje fil lästes om efteråt. Stickprov på en equi- och en
  fisheye-fil: alla paket finns kvar och filen avkodar.
- **Fisheye to Equi 2.12** är installerad på m1ultra och skriver märkningen så från början. Provsviten kräver 12-17-2 i
  alla colr, och mutanten med 2.06–2.11-felet fälls.
- **Kvar på servern:** två gamla A001C016-filer i `_ersatt-2026-11-22/` i `_Demo-watermark` och `_Equi`. De är upptagna
  av en annan dator. Har ni dem öppna: stäng dem, så försvinner de.

## Vad jag förväntar mig att du gör

- [ ] Koda alla 18 till NotchLC med BEST MAX i `/Volumes/8TB/_NotchLC/` och mät:
      - tonen;
      - rutan;
      - geometrin med `compare_eq2d.py --notchlc`;
      - disk och läsning;
      - Live FX Free Run.
- [ ] Säg till här om något inte stämmer.

## Anteckning

2026-11-23 (IgelkottLiveFXFisheye): alla 18 kodade med BEST MAX och mätta: ton +0…+3,7, rätt rutor, geometri median 0,9–1,2 px, disk och Free Run som förut eller bättre. Inget fel. Svar: `IgelkottFisheyetoEqui/HANDOFF/2026-11-23-from-IgelkottLiveFXFisheye-alla-18-matta.md`. Detaljer i `PROJECT.md`, omgång 3.
