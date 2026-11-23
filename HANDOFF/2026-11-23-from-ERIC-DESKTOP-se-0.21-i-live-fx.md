---
from: IgelkottLiveFXFisheye (ERIC-DESKTOP)
to: IgelkottLiveFXFisheye (THREADRIPPER)
date: 2026-11-23
deadline: asap (pushen väntar på det här)
urgency: high
topic: Se 0.21 i Live FX: vägranstexten med IGELKOTTPLATES.COM, beskrivningen och hjälplänken, och att väggen ritar som förut
status: pending
---

# Från ERIC-DESKTOP till THREADRIPPER: se 0.21 i Live FX

## Vad har hänt

Din handoff (committa på ERIC-DESKTOP) är gjord. Den ligger i `HANDOFF/done/`. 0.21 är committad på ERIC-DESKTOP men
inte pushad: Eric vill att den ses i Live FX först ("Be threadripper kolla"). Licensen på ERIC-DESKTOP har gått ut.

Vad 0.21 ändrar (PROJECT.md, "0.21"):

- **PIXERA tar 2 × 2 prov per pixel, som Live FX.** Det förklarar dina 9 MTF50-FAIL. Felet fanns också på ERIC-DESKTOP,
  så det var inte drivrutinen.
- **Märkningen** (Eric: "branding är viktig"):
  - Vägranstexten har fått en rad till, IGELKOTTPLATES.COM. IGELKOTTPLATES är vit och .COM är i accentcyanen #00BCDB.
  - Nodens beskrivning börjar med "IgelkottFisheye by Igelkott Film AB, igelkottplates.com".
  - `HelpLink` är https://igelkottplates.com.
- **Färgerna kommer ur IgelkottDesigns tokens.** Varningsgult är nu #FACC15 (förut #FFC700). Det gäller både texten och
  varningstecknet.
- **Live FX-utgåvan ritar väggen precis som 0.20.** Bara versionen, färgerna och meddelandet skiljer.

## Vad jag förväntar mig att du gör

- [ ] Installera 0.21: kopiera `matchbox/IgelkottFisheye2D.glsl` och `.xml` (version 0.21 i xml-filen) till
      `C:\ProgramData\Assimilator\plugin64\Matchbox\shaders`. Starta om Live FX.
- [ ] `python tools/verify_windows.py` och `python tools/verify_windows.py . --canvas`. Båda ska ge 0 FAIL, nu också med
      PIXERA-utgåvans MTF50. Skriv ned vilken drivrutin du kör.
- [ ] **Ett klipp utan tagg** (till exempel en provplåt utan tagg från `tools/make_testplates.py`, eller vilket klipp som
      helst som inte är en Igelkott-plåt), med noden. Ta en skärmbild av viewern och kontrollera:
  - Bilden är svart.
  - NOT AN IGELKOTT CLIP står i varningsgult.
  - Under den står IGELKOTTPLATES vitt och .COM cyan, och båda raderna är centrerade.
  - Det lilla varningstecknet sitter uppe till vänster.
- [ ] **A007C001 från E:** med noden (Auto/Auto, Wall, FOV 90). Väggen ska se ut som i 11b, utan text och utan
      varningstecken.
- [ ] **Var Live FX visar märkningen.** Leta efter beskrivningen och hjälplänken: nodens info, en tooltip, en ?-knapp
      eller Matchbox-listan. Skriv ned var de syns, eller att de inte syns någonstans.
- [ ] Skriv resultatet och skärmbilderna (en sökväg utanför projektmappen) i PROJECT.md under 0.21, med datum, maskin
      och Live FX-version.
- [ ] Skicka en handoff tillbaka till ERIC-DESKTOP (`HANDOFF/ÅÅÅÅ-MM-DD-from-THREADRIPPER-…md`): sett/inte sett, och om
      något ska ändras innan pushen. Committa inte: `.git/` finns bara på ERIC-DESKTOP (Drive synkar inga punktfiler,
      se PROJECT.md under Git).

## Bakgrund och länkar

- Commits: `79ca605` (PIXERA 2 × 2) och den efter (märkningen och tokens). Det är `main` på ERIC-DESKTOP, inte pushad.
- Bild av vägranstexten, ritad med provets kopia av shaderns räkning och inte i Live FX: Eric har fått den i chatten.
- PIXERA-utgåvan är inte provad i PIXERA. Den är inte heller en del av det här steget.
