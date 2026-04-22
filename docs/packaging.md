# Packaging

Bundle pipeline reference. End-user install instructions are in the
top-level [README](../README.md); this doc is for working on the bundle
itself.

## Pipeline

```
icon.svg                                    # checked in
   |  packaging/make_icon.sh
   v
icon.icns                                   # generated, gitignored
   +
src/photo_bomb/                             # absolute imports only
   |  pyinstaller --clean packaging/photo_bomb.spec
   v
build/                                      # PyInstaller intermediates (gitignored)
dist/Photo Bomb.app                         # ad-hoc signed by spec
   |  codesign --force --deep --options runtime --sign -
   |  xattr -cr
   |  "<bundle>/Contents/MacOS/Photo Bomb" --version          # smoke test
   |  create-dmg  (or hdiutil fallback)
   v
dist/Photo-Bomb-<version>-arm64.dmg
```

`scripts/build_macos.sh` runs the whole thing. CI in
`.github/workflows/release.yml` runs the same script on `macos-14`.

## Files

| Path | Role |
|------|------|
| `packaging/photo_bomb.spec` | PyInstaller spec; sets target_arch arm64, ad-hoc `codesign_identity="-"`, `Info.plist` keys, bundle id, version |
| `packaging/entitlements.plist` | Hardened-runtime entitlements; required because `--options runtime` is used |
| `packaging/make_icon.sh` | `rsvg-convert` (or `qlmanage`) -> `sips` per size -> `iconutil` |
| `scripts/build_macos.sh` | Orchestrator. Honors `SKIP_DMG`, `SKIP_VENV`, `PYTHON` env overrides |
| `.github/workflows/release.yml` | Tag-triggered + manual; `gh release create` for tags, artifact upload for dispatch |

## Why each non-obvious thing exists

- **`target_arch="arm64"`** - matches the only runner we ship for.
  Universal2 would require building `pyobjc` + `Pillow` wheels for both
  arches; not worth it for a personal tool.
- **`codesign_identity="-"`** in spec, then **a second `codesign --deep`**
  pass in the script - PyInstaller signs the main binary inline but does
  not always re-sign nested Qt frameworks brought in by `COLLECT`. Without
  the deep pass, `codesign --verify --deep` fails on launch.
- **`--options runtime`** - hardened runtime is required to use Apple's
  `personal-information.photos-library` entitlement.
- **`com.apple.security.cs.disable-library-validation`** - PyInstaller
  bundles third-party Mach-Os (Qt, OpenSSL via `requests`) signed by
  different authorities.
- **`com.apple.security.cs.allow-unsigned-executable-memory`** - CPython's
  bytecode VM uses W+X memory pages; without this the interpreter
  segfaults under hardened runtime.
- **`xattr -cr`** - clears `com.apple.quarantine` xattrs that the build
  environment may have inherited (e.g. from cloned downloads). Without
  this, even a correctly-signed dev DMG triggers Gatekeeper for the
  developer.
- **`--version` smoke test under `QT_QPA_PLATFORM=minimal`** - exits before
  `QApplication` is constructed, which proves the bundle's Python +
  imports work without needing a window server. Catches missing
  `hiddenimports` early.

## Editing the spec

If you add a new top-level dependency that PyInstaller's static analysis
can't see (a dynamic import, a plugin loaded by string name), add it to
`hiddenimports` in `packaging/photo_bomb.spec`. Verify with:

```bash
SKIP_DMG=1 ./scripts/build_macos.sh
"./dist/Photo Bomb.app/Contents/MacOS/Photo Bomb" --version
```

The smoke step inside `scripts/build_macos.sh` already does the second
command; running it manually after a failed CI build is the fastest way
to reproduce.

## Adding a real Developer ID later

When/if a paid Apple Developer account is available:

1. In `packaging/photo_bomb.spec`, change `codesign_identity="-"` to your
   identity hash (or set via env in the spec).
2. In `scripts/build_macos.sh`, replace `--sign -` with the same identity.
3. After DMG creation, add:
   ```bash
   xcrun notarytool submit "$DMG_PATH" --keychain-profile <profile> --wait
   xcrun stapler staple "$DMG_PATH"
   ```
4. In CI, store the signing cert + notarytool credentials as GitHub
   Secrets and import them in the workflow before the build step.

The repo layout, spec structure, entitlements, and `Info.plist` keys all
remain valid. No reorganization needed.

## Reset commands

```bash
rm -rf build dist .venv-build                       # clean slate
rm -rf src/photo_bomb/assets/icons/icon.icns \
       src/photo_bomb/assets/icons/icon.iconset     # force icon regen
tccutil reset Photos com.photobomb.app              # reset Photos permission
```
