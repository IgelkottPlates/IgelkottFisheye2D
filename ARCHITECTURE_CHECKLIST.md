# Architecture Checklist — IgelkottLiveFXFisheye

**Hard requirement.** Detta dokument måste finnas i varje ny app i
Igelkott-ekosystemet. Brott mot någon punkt blockerar `status: live`
i `projects.yaml`.

Referens (full förklaring per punkt):
[`../_atlas/knowledge/synology/architecture-framework.md`](../_atlas/knowledge/synology/architecture-framework.md)

Fyll i varje ruta: `[x]` om kravet är uppfyllt, eller `[n/a]` med
en kort motivering på samma rad om punkten genuint inte gäller.

---

## 1. Path-arkitektur

- [x] **Auto-resolve atlas-rot.** Om appen läser från Igelkott Appar-
      mappen — testa Drive Client cache (`SynologyDrive-*`) först,
      SMB-mount sen, NAS-fs sist. Inga hårdkodade paths.
- [x] **Hårdkodade paths motiverade.** Om en path är hårdkodad
      (t.ex. `/volume2/igelkottstore.com` för store-walks) finns en
      kommentar eller PROJECT.md-not som motiverar varför.
- [n/a] samma shader på alla Macar — **Maskinspecifik konfig under `Config/<maskin>.json`** om appen
      körs på flera Macar med olika konfig.

## 2. SMB-säkerhet

- [x] **Build-output ALDRIG på SMB.** `.build/`, `DerivedData/`,
      `node_modules/`, `build/`, `dist/`, `target/` ligger lokalt
      eller är gitignore:ade.
- [x] **Inga symlinks i Drive Client-synkade mappar.** Python `.venv`,
      npm shims etc. skapas lokalt på respektive maskin, inte i
      `~/Library/CloudStorage/SynologyDrive-*/...`.
- [x] **xattrs / quarantine-bits hanterade.** Om appen distribuerar
      `.app` / `.bundle` via Drive Client — strippa quarantine efter
      sync (se `knowledge/synology/drive-client-app-bundles.md`).
- [n/a] ingen file-watching — **File-watching kör inte mot SMB-path.** Vite, Webpack, fswatch,
      Xcode incremental — alla pekar på lokal/Drive Client cache.

## 3. Drive Client-säkerhet

- [x] **Sync-delay hanterad.** Appen väntar på sync-spinner-ikonen
      eller forcerar sync innan den deployar/läser data som just
      sparats från en annan maskin.
- [x] **Per-maskin namn-variation hanterad.** Auto-resolve av
      `SynologyDrive-*`-wildcard, inte hårdkodning av `Studios` eller
      `M1Ultra`.

## 4. Container Manager (om appen körs i Docker på NAS)

- [n/a] ingen container — **Bind-mounts identiska in/ut.** `/volume2/X` → `/volume2/X`,
      inte `/data/X`. Felsökning från host vs container blir
      symmetrisk.
- [n/a] ingen container — **Image-build via extern eller verifierad mot Container Manager
      build-DNS-quirks.** Se `knowledge/synology/docker.md`.
- [n/a] ingen container — **Compose-template minimal.** Bara `image`, `restart`,
      `volumes`, `environment`, `network`.
- [n/a] ingen container — **Drift-paths under `/volume1/docker/<container>/`.** Konfig,
      SQLite, persistent state.

## 5. Deploy

- [x] **Ingen rsync MAC→NAS via SSH** för app-filer.
- [n/a] ingen NAS-tjänst — **Deploy via lokal `cp` på NAS** efter Drive Client-sync, eller
      via container-rebuild från synkad source.

## 6. Publik exponering (om appen är publik)

- [n/a] inte publik — **DSM Reverse Proxy konfigurerad** med subdomän + LE-cert.
- [n/a] inte publik — **Cert-rotation noterad i `PROJECT.md`** — vem ansvarar, var
      cert-mapping bor i DSM.

## 7. File Station API (om appen genererar share-länkar)

- [n/a] inga share-länkar — **Använder dedikerad lokal user, inte administrator.**
- [n/a] inga share-länkar — **API-flöde matchar `knowledge/synology/file-station-api.md`.**

## 8. Atlas-integration

- [x] **PROJECT.md + CLAUDE.md finns** (atlas regel #2).
- [x] **`projects.yaml` har en rad för projektet** (atlas regel #6).
- [x] **HANDOFF/-mapp skapad om appen kommer ta emot meddelanden
      från andra projekt** (atlas regel #7).

## 9. Utvecklingsmiljö

- [n/a] inget git-repo, inga byggfiler i mappen (byggkatalogen i ~/Library/Caches) — **`.gitignore` exkluderar build-output, lokala venvs, IDE-shit
      (`.idea/`, `.vscode/`-vissa, `*.user`, etc.)**.
- [n/a] PROJECT.md § Kör projektet — **README.md i projektmappen** beskriver kort hur man kör.
- [x] **CLAUDE.md har bootstrap-check** högst upp (atlas-konvention).

## 10. IgelkottSuit (atlas regel #12)

- [x] **Artefakt i deploy-mapp.** `deploy-launcher.sh` producerar
      `_applaunchers/<Namn>.app.zip` (eller `.app` / `_releases/` /
      `.command` med motivering).
- [x] **`CFBundleVersion` ändras per deploy** (tidsstämpel i
      `build-app.sh`) och **`VERSION`-filen höjs vid synliga ändringar**
      (atlas regel #13).
- [x] **Post i `_atlas/suite.yaml`** med samma `id` som `projects.yaml`
      (validera med ruby -ryaml).
- [x] **Verifierat i Suit:** "Aktuell" efter installation,
      "Uppdatering finns" efter nästa deploy.

---

## Anteckningar / avvikelser

Hårdkodad path: Live FX:s Matchbox-mapp `/Library/Application Support/Assimilator/Plugins/Matchbox/shaders` — Live FX läser
modulerna därifrån (`Settings/Junxion.xml`, 2026-10-05). Verifierat i Suit: "Aktuell" 2026-10-05, build 202610051632 (Eric).

_Senast verifierat: 2026-10-05 av Claude (IgelkottLiveFXLoader-sessionen)_
