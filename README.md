# Photo Bomb

PyQt6 application for **macOS (Apple Silicon)** that helps you organize your
Photos library using vision language models.

- macOS-only (uses `Photos.framework` via PyObjC)
- Distributed as a `.dmg` from [GitHub Releases](https://github.com/yourusername/photo-bomb/releases)
- BYO vision endpoint (any OpenAI-compatible chat-completions API)

---

## Installing the released app

1. Download the latest `Photo-Bomb-<version>-arm64.dmg` from
   [Releases](https://github.com/yourusername/photo-bomb/releases).
2. Open the DMG and drag **Photo Bomb.app** to **Applications**.
3. **First launch only**: because the app is ad-hoc signed but not notarized
   (no Apple Developer ID), Gatekeeper will block a normal double-click. To
   open it the first time:

   - **GUI:** right-click `Photo Bomb.app` in Applications, choose **Open**,
     then click **Open** in the dialog. macOS remembers this choice; future
     launches work normally.
   - **Terminal alternative:**

     ```bash
     xattr -dr com.apple.quarantine "/Applications/Photo Bomb.app"
     open "/Applications/Photo Bomb.app"
     ```

Requires **macOS 12 (Monterey) or newer** on **Apple Silicon (arm64)**.

When the app first asks for access to Photos, click **OK**. The permission is
stored in System Settings - Privacy & Security - Photos.

---

## Running from source

```bash
git clone https://github.com/yourusername/photo-bomb.git
cd photo-bomb

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

python -m photo_bomb
# or, equivalently, the installed entry-point:
photo-bomb
```

Configuration lives in `~/Library/Preferences/photo-bomb/config.json` and is
populated via **File - Settings...** in the app.

---

## Building the .dmg locally

Requires Apple Silicon. From the repo root:

```bash
brew install create-dmg librsvg   # one-time
./scripts/build_macos.sh
```

Outputs:

```
dist/Photo Bomb.app
dist/Photo-Bomb-<version>-arm64.dmg
```

The script handles everything: venv, deps, SVG -> .icns, PyInstaller,
ad-hoc codesigning with hardened runtime, `xattr` cleanup, a `--version`
smoke test against the bundled binary, and DMG packaging.

Useful overrides:

- `SKIP_DMG=1 ./scripts/build_macos.sh` - just produce `Photo Bomb.app`.
- `SKIP_VENV=1 ./scripts/build_macos.sh` - reuse the active Python.
- `PYTHON=python3.12 ./scripts/build_macos.sh` - choose the venv interpreter.

---

## Cutting a release

Releases are built and published automatically by
[`.github/workflows/release.yml`](.github/workflows/release.yml) on the
`macos-14` (Apple Silicon) GitHub Actions runner. To cut one:

```bash
# bump src/photo_bomb/__init__.py __version__
git commit -am "release: 0.2.0"
git tag v0.2.0
git push origin main --tags
```

The workflow builds the DMG, runs the smoke test, and creates a GitHub
Release named after the tag with the DMG attached and install instructions in
the body.

You can also trigger the workflow manually (`workflow_dispatch`) to produce a
DMG artifact without cutting a release.

---

## Repository layout

```
photo-bomb/
|-- src/
|   `-- photo_bomb/                 # importable package
|       |-- __init__.py             # __version__, __app_name__, ...
|       |-- __main__.py             # `python -m photo_bomb`
|       |-- main.py                 # entry point (also `photo-bomb` script)
|       |-- ui/                     # PyQt6 widgets and dialogs
|       |-- core/                   # config, Photos integration, API client
|       |-- utils/                  # helpers + importlib.resources lookup
|       `-- assets/
|           `-- icons/icon.svg      # source for icon.icns (generated)
|-- packaging/
|   |-- photo_bomb.spec             # PyInstaller spec (arm64, ad-hoc signed)
|   |-- entitlements.plist          # hardened-runtime entitlements
|   `-- make_icon.sh                # SVG -> .icns
|-- scripts/
|   `-- build_macos.sh              # one-shot local build
|-- .github/workflows/release.yml   # tag-triggered CI release
|-- docs/                           # design and feature docs
|-- pyproject.toml
|-- requirements.txt                # runtime deps
`-- requirements-dev.txt            # + pyinstaller
```

---

## Why ad-hoc signing (and not notarized)?

Notarization requires a paid Apple Developer ID. We deliberately avoid that.

Ad-hoc signing (`codesign --sign -`) is free, requires no Apple account, and
is genuinely necessary for the app to run on Apple Silicon at all - and for
the macOS TCC subsystem to remember the user's Photos-library permission
across launches. Gatekeeper still requires the one-time bypass described
above for downloaded DMGs.

If you later acquire a Developer ID, swap `--sign -` for your identity in
[`scripts/build_macos.sh`](scripts/build_macos.sh) and add a `notarytool`
step to the workflow - the rest of the pipeline (spec, entitlements, layout)
does not need to change.

---

## Documentation

Docs are written for agentic consumption: terse, accurate, and focused on
contracts and gotchas rather than re-stating obvious UI behavior.

| Document | Read this when you need to know |
|----------|---------------------------------|
| [docs/index.md](docs/index.md) | Repo map, what works vs what's stubbed, common commands |
| [docs/architecture.md](docs/architecture.md) | Module contracts, Qt signal flow, singleton policy, asset-resolution model |
| [docs/features.md](docs/features.md) | Per-subsystem implementation status (real / partial / stub) |
| [docs/api-settings.md](docs/api-settings.md) | Config schema, exact request shape `api_client` sends, known bugs |
| [docs/categorization.md](docs/categorization.md) | Category buttons, how "categorize" persists into Apple Photos albums |
| [docs/photo-access.md](docs/photo-access.md) | Stub surface of `PhotosLibrary` and what a real PyObjC port must implement |
| [docs/packaging.md](docs/packaging.md) | Bundle pipeline: spec, entitlements, signing, smoke test, release workflow |
