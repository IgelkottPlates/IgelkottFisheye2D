---
from: IgelkottFisheyetoEqui
to: IgelkottLiveFXFisheye
date: 2026-11-23
deadline: asap
urgency: high
topic: Hörnmärket (IGK1) har ett nytt valfritt fält |gamma:<namn> — autoyaw läser märket: bygg om; gamman finns nu i QR-koden
status: pending
---

# Från IgelkottFisheyetoEqui till IgelkottLiveFXFisheye: gamma i hörnmärket

## Vad har hänt

Eric 2026-11-23: "Står det i qr koden vilken gamma det är? Annars lägg till", och sedan "Eftersom jag fortfarande jobbar i
r&d så uppdatera allt samtidigt och skicka brådskande handoff till alla". Det stod inte i märket. Nu finns ett nytt valfritt
fält.

- **Fältet:** `|gamma:<namn>`. Det står efter klippet bland de andra valfria fälten (`orient:`, `pointing:`), i valfri
  ordning och högst en gång. Skrivarna sätter det sist: `IGK1|1|sonyVenice2|A007C001_220127SK|pointing:zenith|gamma:acescct-ap1`.
- **Namnet:**
  - gemener, siffror, punkt och bindestreck;
  - 1–32 tecken;
  - börjar med gemen eller siffra.
- **Kända namn** (`LensMark.Gamma`):
  - `acescct-ap1`: Darkroms mastrar, filnamnet `Gamma-ACEScct_AP1`, markörfilen `Gamma = ACES_2.0_cct_Ap1`;
  - `rec709`;
  - `slog3-sgamut3cine`.
- **Läsaren godtar alla giltiga namn,** också okända. Nästa gamma ska inte kasta märket så som `pointing:` gjorde i Stage i sex
  dagar. Ett ogiltigt namn eller ett dubblerat fält gör fortfarande texten till inget märke, som förut.
- **`_shared/IgelkottFisheyeLens` (`IgelkottLensMark`):**
  - `LensMark.gamma`;
  - `LensMark.Gamma`;
  - `LensMark.isValidGammaName(_:)`;
  - `LensMark.gamma(fromFileName:)`: bara kända `Gamma-…`-led, annars nil;
  - `swift test`: 24 av 24 gröna.
- **Fisheye to Equi 2.13** skriver fältet i fisheye ut:
  - källmärkets gamma, annars filnamnets;
  - utelämnat om inget av dem finns.
  Ett prov och två mutanter vaktar det.
- **Pixeltaggen är oförändrad.** Gamman står bara i QR-koden.
- **Märkena blir längre.** QR-koden går ofta en version upp, till exempel 33 → 37 moduler. Vid 1600 px är det fortfarande
  omkring 4 px per modul.

## Vad jag förväntar mig att du gör

- [ ] Bygg om `tools/autoyaw` mot `_shared/IgelkottFisheyeLens`, så att märket med `gamma:` läses.
- [ ] Ni kan läsa gamman i stället för att anta ACEScct. Den står bara i QR-koden, inte i pixeltaggen. Säg till om
      shadern behöver den i taggen.
- [ ] Säg till här om något stoppar.

## Bakgrund och länkar

- Läsaren och reglerna: `_shared/IgelkottFisheyeLens/Sources/IgelkottLensMark/LensMark.swift`.
- Skrivaren i Fisheye to Equi: `Fisheye_to_equi/FisheyeOut.swift` och `FFmpegEngine.sourceGamma`.
- Kunskap: `_atlas/knowledge/camera-rigs/qr-hornmarke-och-slate.md`.
