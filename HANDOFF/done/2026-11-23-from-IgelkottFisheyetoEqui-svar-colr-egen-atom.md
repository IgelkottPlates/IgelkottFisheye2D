---
from: IgelkottFisheyetoEqui
to: IgelkottLiveFXFisheye
date: 2026-11-23
deadline: innan de övriga 17 filerna rättas
urgency: high
topic: Svar på colr-fel-atom — ni hade rätt; en rättad fil finns (A007C001-fisheyen) plus provfil C; koda med BEST MAX och mät tonen, sedan rättas resten
status: done
---

# Från IgelkottFisheyetoEqui till IgelkottLiveFXFisheye: colr rättad i en fil, prova den i Media Encoder

Svar på `IgelkottFisheyetoEqui/HANDOFF/2026-11-23-from-IgelkottLiveFXFisheye-colr-fel-atom.md`. Tack, fyndet stämmer.

## Vad har hänt

- **Bekräftat:**
  - 2.06–2.11 skrev 12-17-2 i den första `colr nclc` de hittade, alltså kopian inuti `glbl`. Provsampelns egen
    `colr` stod kvar på 12-17-1.
  - Provsviten läste på samma sätt och såg därför inget fel.
  - Kontrollerat på A007C001, både fisheye och equi.
- **Erics val (2026-11-23):** den egna atomen får 12-17-2. Den tas inte bort som hos Darkroom. `glbl`-kopian blir också
  12-17-2.
- **Två filer är rättade så,** med `Tools/ratta-colr.py`. Den skriver två byte på plats per atom och rör inga rutor:

| Fil | Egen `colr` | `glbl` | Ramhuvud |
|---|---|---|---|
| `Store/_Demo-watermark/A007C001_220127SK_fisheye_Gamma-ACEScct_AP1_ProRes4444.mov` | 12-17-2 (var 1) | 12-17-2 | 12-17-1 |
| `/Volumes/360_Production/Tester/colr-prov 2026-11-22 FisheyetoEqui/C_colr-12-17-2-i-egen-atom_som-2.12.mov` | 12-17-2 | 12-17-2 | 12-17-1 |

- **C är A med båda atomerna satta till 2.** Pixlarna är identiska med A och B (framemd5), och `LASMIG.txt` är uppdaterad.
  Då har ni alla tre märkningarna på samma bild:
  - A: egen 1, `glbl` 1;
  - B: bara `glbl` 2, som Darkroom;
  - C: egen 2, `glbl` 2, som 2.12 skriver.
- **De övriga 17 filerna är orörda.** De rättas när ni säger att C och A007C001 ger samma ton som B.
- **Appen:** från 2.12 skriver `markColrLikeDarkroom` varje colr i provsampeln. Provsviten läser den egna atomen och
  kräver att alla colr säger 12-17-2. En ny mutant rättar bara den första och ska fällas.

## Vad jag förväntar mig att du gör

- [ ] Kontrollera att båda märkningarna säger 12-17-2 i de två filerna ovan.
- [ ] Koda C och A007C001-fisheyen med BEST MAX och mät tonen mot källan.
      Väntat: C som B (±2 kodvärden), och A007C001 utan tonkurvan.
- [ ] Säg till här, i ett svar i `IgelkottFisheyetoEqui/HANDOFF/`. Blir det som B rättas de övriga 17. Blir det som A tar
      vi bort den egna atomen som Darkroom i stället.

## Bakgrund och länkar

- Rättningsverktyg: `IgelkottFisheyetoEqui/Tools/ratta-colr.py` (`--prov` visar utan att skriva).

## Tillägg 2026-11-23 08:05 (IgelkottFisheyetoEqui): 10 s ur A007C001 att analysera

Eric: "Spara ut 10 sekunder och skicka vidare för analys". Ni slipper då koda hela 45 GB-filen. Utdraget är ruta
500–749 av 2245 (25 fps), så er mätruta 600 är med. Tidkoden är 01:13:12:18. Båda filerna ligger i
`/Volumes/360_Production/Tester/colr-prov 2026-11-22 FisheyetoEqui/`:

| Fil | Vad | Egen `colr` | `glbl` |
|---|---|---|---|
| `A007C001_220127SK_fisheye_ProRes4444_wm_10s_ruta500-749.mov` | den rättade watermark-filen (5,6 GB) | 12-17-2 | 12-17-2 |
| `A007C001_220127SK_fisheye_master_10s_ruta500-749.mov` | Darkroms master, samma rutor (4,7 GB) | saknas, som mastern | 12-17-2 |

- Rutorna är kopierade paket för paket och har samma framemd5 som källfilerna från samma ruta.
- Ramhuvudet är 12-17-1 i båda.
- Kopiorna till servern är kontrollerade med SHA-256.
- ffmpeg skriver om märkningen vid en kopiering. Därför sattes den efteråt så att den är som i originalen:
  - i watermark-utdraget med `Tools/ratta-colr.py`;
  - i master-utdraget genom att den egna colr-atom som ffmpeg lade till togs bort.

- [ ] Koda watermark-utdraget med BEST MAX och mät tonen mot master-utdraget. Väntat: som B, alltså ±2 kodvärden och
      ingen tonkurva.

## Anteckning

- 2026-11-23 (IgelkottLiveFXFisheye): gjort. C = B, watermark-utdraget utan tonkurva. Svar:
  `IgelkottFisheyetoEqui/HANDOFF/2026-11-23-from-IgelkottLiveFXFisheye-colr-c-som-b.md`.
