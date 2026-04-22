# Application Icon

`icon.svg` is the source of truth. `icon.icns` is generated from it and is
**not** checked into git (see repo `.gitignore`).

## Regenerate the .icns

From the repo root:

```bash
./packaging/make_icon.sh
```

The script renders `icon.svg` into a 1024x1024 master PNG, downsamples it into
the standard Apple `.iconset` (16, 32, 64, 128, 256, 512, 1024 plus @2x
variants), and packs the result into `icon.icns` via `iconutil`.

`scripts/build_macos.sh` invokes this automatically when `icon.icns` is
missing, so you usually don't have to run it by hand.

## Tooling

- **Required:** `sips`, `iconutil` (built into macOS).
- **Preferred for SVG -> PNG:** `rsvg-convert` (`brew install librsvg`). If
  unavailable the script falls back to `qlmanage`, which produces a usable
  but lower-quality result.

## Replacing the icon

Drop in any 1024x1024 (or larger, square) `icon.svg` and re-run the script.
The current SVG is a placeholder camera-lens motif matching the original
design spec (#1e40af / #60a5fa).
