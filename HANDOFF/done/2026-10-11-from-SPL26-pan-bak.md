---
from: SPL26 (Cowork-planering av Starting Pixel Live 26)
to: IgelkottLiveFXFisheye
date: 2026-10-11
deadline: 2026-10-13
urgency: high
topic: Ny trackning (punkt rakt bak) — exporterad som Pan 360 i grader; bara pan (Stab Yaw) ska stabiliseras
status: done
---

# Från SPL26 till IgelkottLiveFXFisheye: ny trackning, bara pan

## Vad har hänt

Eric trackade om (2026-10-11): punkten på horisonten **rakt bak**, eftersom det var svårt att hitta en punkt som syns
fri hela klippet. Trackad på råklippet `Offroad 130-175s` i dess egen slot (slot 4, 4096 × 4096), Track 1 Point,
Translate, bildruta 0–1123.

**Skillnad mot förra exporten:** den här sloten är märkt som 360-material, så Apply Stabilize skrev inte Framing
Offset X/Y utan **Pan 360 Yaw / Pitch / Roll i grader** (manualen: "For 360 media, the stabilize goes to yaw, pitch,
and roll"). Live FX räknar då som om bilden vore en equirect — inte rätt geometri för fisheyen. Exporterat:

- `~/Movies/IgelkottFisheye Direction Lock/Track bak Pan360 Yaw.csv` (−7,4 … +113,4)
- `~/Movies/IgelkottFisheye Direction Lock/Track bak Pan360 Pitch.csv` (−0,18 … +0,48)
- `~/Movies/IgelkottFisheye Direction Lock/Track bak Pan360 Roll.csv` (−3,3 … +1,2)

Rubrik `#ANIM Offroad 130-175s\Pan 360\Yaw`, två kolumner, 1124 rader. Sloten har sin Framing-animation satt
till Off efteråt. Förra exporten (`Track fisheye Offset X/Y.csv`, moln rakt fram) ligger kvar.

## Beslut

Eric (2026-10-11): **det är bara pan vi försöker stabilisera.** Bara Stab Yaw importeras; Stab Pitch och Stab Roll
står på 0. Sessionens talarnoter (slide 15) är ändrade till det.

## Vad jag förväntar mig att du gör

- [ ] Räkna Stab Yaw ur den nya exporten: Pan 360-värdena tillbaka till punktens läge i källan (Live FX:s
      equirect-antagande, troligen dx = Yaw · 4096 / 360, dy = Pitch · 4096 / 180 — läs av), sedan fisheye-läget →
      azimut kring objektivets mitt (2036, 2028) → DL → `Track bak Stab Yaw.csv`. För ren pan behövs bara azimuten.
- [ ] Gärna att appen läser Pan 360-exporten direkt (känner igen rubriken), så att steget på scen blir samma.
- [ ] En flagga eller inställning för **bara yaw** (`--yaw-only`), så att ingen Pitch-fil skapas av misstag.
- [ ] Jämför med Yaw ur förra exporten (moln rakt fram): samma pan ska synas.
- [ ] Sätt `status: acknowledged` med en rad om vad du byggde.

## Tillägg: felet borttaget (2026-10-11, kväll)

Eric: Pan 360-exporten "duger inte". Orsaken hittad: råklippet hade **Metadata → Projection Type: Equirectangular 360**
(troligen satt av mallen/loadern). Ändrat till **Normal** i Live FX (Metadata-fliken för sloten). Framing visar nu
X/Y Offset i stället för Yaw/Pitch/Roll, så Stabilize skriver pixlar igen. Trackningen försvann med bytet och görs om
av Eric; exporten blir `Track bak Offset X/Y.csv` i samma mapp. **Pan 360-filerna ovan ska inte användas.**

Till IgelkottLiveFXLoader (via dig eller egen handoff): fisheye-klipp ska inte få Projection Type Equirectangular 360.

**Ny export klar (efter bytet till Normal):** `Track bak Offset X.csv` (−143 … +1218) och `Track bak Offset Y.csv`
(−319 … +129), rubrik `#ANIM Offroad 130-175s\Framing\Offset X`, 1124 rader. Startvärdet är inte 0 (X −17,5 i
bildruta 0). Pan 360-filerna är flyttade till undermappen `Ogiltiga Pan 360 (använd inte)`. Räkna `Track bak Stab
Yaw.csv` ur Offset-filerna, bara yaw.

## Anteckning

IgelkottLiveFXFisheye 2026-10-11 (0.8, build 202610112338, i `_applaunchers`; inte installerad):

- **`Stab/Track bak Stab Yaw.csv` är räknad** ur `Track bak Offset X/Y.csv`: 1124 nycklar, −1,22 … +0,87°, sex
  kolumner, rubrik `#ANIM Stab\Stab Yaw`. Inte importerad i Live FX.
- **`--yaw-only`** finns och står i `installningar.txt` (`--k 0.5 --fisheye 4096 --sensor-height 23.9 --yaw-only`).
  Ingen Stab Pitch-fil skrivs, och den gamla `Track fisheye Stab Pitch.csv` är borttagen ur `Stab/`.
- **Flera spår i mappen** paras på filnamnet, så `Track bak` och `Track fisheye` räknas var för sig.
- **Startvärdet −17,5:** första nyckeln dras av; spelar ingen roll för resultatet.
- **Spåret:** cirkel kring objektivets mitt med radie 1515 px, avvikelse 2,8 px, båge 56°; punkten 2–3° över
  horisonten, bakom bilen. Rutor ur klippet vid bildruta 0, 560 och 1123 visar läget vid horisonten bakåt.
- **Jämfört med förra exporten** (moln rakt fram): Stab Yaw korrelerar +0,98 och är 1,06 gånger så stor. Samma pan.
- **Pan 360-filerna** är inte använda, och appen läser dem inte (de ligger i en undermapp).
- **Loadern:** handoff skickad om Projection Type
  (`../IgelkottLiveFXLoader/HANDOFF/2026-10-11-from-IgelkottLiveFXFisheye-projection-type.md`).
- **Blockerar (Eric i Live FX):** importera `Track bak Stab Yaw.csv` på Stab Yaw (alla väggar, eller en nod i Mode
  Fisheye (stabilize)), Stab Pitch och Roll på 0, och se om pan blir stillare. Blir det värre: `--yaw-sign -1` i
  `installningar.txt` och starta appen igen. Tecknet är räknat (punkten går åt höger i bilens ram → Stab Yaw +),
  inte sett i Live FX.

## Avslut

Stängd 2026-10-12: `--yaw-only` och `Track bak Stab Yaw.csv` levererade; ersatt som huvudväg av trackingvyn.
