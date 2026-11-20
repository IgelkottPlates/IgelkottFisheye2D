# Contributing

The goal is IgelkottFisheye in every major media server and compositor. Most of them we don't have, so help from people
who use them is the fastest way there.

## Ways to help

- **Try it in a player and tell us what you see.** Open an issue with the player, its version, the OS, and a
  screenshot. [docs/PLAYERS.md](docs/PLAYERS.md) has first-look tests for Flame and Nuke Stage: a few lines of shader
  that answer what we need to know (row order, pixel size, how parameters are declared).
- **Report a bug.** Say which player, which camera and pointing, and what you expected. A frame of the plate helps.
- **Port it to a new player.** See below.

## Porting to a new player

Read [docs/PLAYERS.md](docs/PLAYERS.md) first. It lists what a host has to offer and how a port is added. In short:

1. Add a wrapper in `shader/` for the player (like `matchbox.glsl` or `pixera.glsl`). The maths stays in `core.glsl`.
2. Teach `tools/build_shaders.py` to write the player's file. Never edit generated files by hand.
3. Add the player to `tools/verify_windows.py`, or explain in the pull request how you checked it. The rule is the same
   for every player: within 0.5 source pixels of the lens model at 8040 px.
4. Check it in the player itself and put a screenshot in the pull request.

## Rules for the code

- `shader/core.glsl` must compile as GLSL 1.20 and 4.50: no bit operations on integers, no arrays.
- Camera numbers come only from `shader/cameras.json`, and that file comes only from Igelkott's lens package. If a lens
  model looks wrong, open an issue rather than changing the numbers.
- Pixel tag rules (where it sits, its bits, the CRC) are fixed. Don't change them, because the tag is written by other
  tools.
- New controls in the panel are decided by the maintainers: open an issue first.
- Everything a user sees is in English.

## Pull requests

Fork the repository, make a branch, and open a pull request against `main`. Before you open it, run:

```
python tools/build_shaders.py --check
python tools/verify_windows.py        # on Windows
```

and say what you ran and what you saw. Small pull requests are easier to review than big ones.
