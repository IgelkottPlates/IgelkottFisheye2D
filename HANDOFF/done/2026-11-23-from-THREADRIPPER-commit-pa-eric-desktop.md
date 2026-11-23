---
from: IgelkottLiveFXFisheye (THREADRIPPER)
to: IgelkottLiveFXFisheye (ERIC-DESKTOP)
date: 2026-11-23
deadline: när det passar
urgency: normal
topic: Committa och pusha det som ligger ocommittat i Drive-mappen (0.20, Threadripper-testet, 11b) från ERIC-DESKTOP
status: done
---

# Från THREADRIPPER till ERIC-DESKTOP: committa det som ligger ocommittat

## Vad har hänt

Uppspelningstestet 11b kördes på THREADRIPPER 2026-11-23 kväll och står i `PROJECT.md` under "Threadripper
(2026-11-23 kväll)". Eric bad om en commit, men **Drive-mappen på THREADRIPPER saknar `.git/` och `.gitignore`**:
`git status` ger "not a git repository". Eric 2026-11-23: committa på ERIC-DESKTOP.

En klon av `IgelkottPlates/IgelkottFisheye2D` (senaste commit `8372459`, "PROJECT.md: 4K test project for Live FX on
Windows") jämförd med Drive-mappen visar att repot ligger efter med mer än 11b:

- shadern 0.20: `shader/core.glsl`, `shader/matchbox.glsl`, `shader/pixera.glsl`, `shader/IgelkottFisheye2D.xml`,
  `matchbox/IgelkottFisheye2D.glsl` och `.xml`, `pixera/IgelkottFisheye.glsl`, `pixera/README.txt`, `VERSION` (0.20);
- `docs/THREADRIPPER-TEST.md` (ny) och `docs/MAC-TEST.md`;
- `tools/bench_notchlc.py` och `tools/compare_eq2d.py` (nya), `tools/verify_windows.py`;
- `AGENTS.md`, `README.md`, `windows/README.txt`;
- `PROJECT.md` (+213 rader: 0.20, Windows-datorn, Threadripper, 11a, 11b);
- nya filer i `HANDOFF/` och `HANDOFF/done/`.

Ska **inte** med (`.gitignore` håller dem utanför, men den syns inte på THREADRIPPER): `tools/__pycache__/`,
`pixera.zip`, `Ref-Eric/`.

## Varför du behöver veta

GitHub-repot är publikt och den som klonar får 0.19-shadern och en PROJECT.md utan 0.20 och testerna. Release v0.20
finns inte. Om `.git/` bara finns på ERIC-DESKTOP kan ingen annan maskin committa.

## Vad jag förväntar mig att du gör

- [ ] `git status` på ERIC-DESKTOP. Kontrollera att `.git/` och `.gitignore` finns och att listan ovan syns som
      ändrad (och inget av det som ska utanför).
- [ ] `python tools/build_shaders.py --check` och `python tools/verify_windows.py` före committen (CLAUDE.md:
      provet före varje leverans).
- [ ] Committa på engelska i repots stil (t.ex. separata commits för 0.20, verktygen och PROJECT.md) och pusha `main`.
- [ ] Ta reda på varför `.git/` och `.gitignore` inte finns i Drive-mappen på THREADRIPPER (Synology Drive Client
      synkar kanske inte punktfiler, eller inte `.git`). Skriv svaret i PROJECT.md under Stack → Git, och i
      `_atlas/knowledge/` om det gäller alla projekt.
- [ ] Klart när `git status` är rent på ERIC-DESKTOP och GitHub visar commiten.

## Bakgrund och länkar

- 11b-resultaten: `PROJECT.md`, "11b, Live FX med Free Run"; rådata i `%USERPROFILE%\IgelkottBench\11b-*.txt` på
  THREADRIPPER (inte i Drive).
- Testlistan: `docs/THREADRIPPER-TEST.md`.
- Brådskande handoff som också väntar (Mac, inte ERIC-DESKTOP):
  `HANDOFF/2026-11-23-from-IgelkottFisheyetoEqui-gamma-i-hornmarket.md` (bygg om `tools/autoyaw`).

## Anteckning (ERIC-DESKTOP, 2026-11-23)

- `.git/` och `.gitignore` finns här och är rena: `__pycache__/`, `pixera.zip` och `Ref-Eric/` är utanför.
- Shadern 0.20 var redan committad (`a47d6cb`) men inte pushad: Eric sa vänta tills 0.20 var sedd i Live FX.
  11b har nu sett den.
- **Varför repot saknas där:** Drive Client synkar inga namn som börjar med punkt (`black_prefix = "."`). Det står i
  PROJECT.md (Git) och i `_atlas/knowledge/synology/drive-client-punktfiler.md`.
- `build_shaders.py --check`: OK.
- `verify_windows.py`: samma 9 MTF50-FAIL här som på THREADRIPPER, med samma tal. Det är PIXERA-utgåvan, inte
  drivrutinen. Allt annat är PASS.
- Pushen väntar på Erics beslut, eftersom provet inte är grönt.
