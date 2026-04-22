#!/usr/bin/env bash
#
# End-to-end macOS build for Photo Bomb.
#
# Steps:
#   1. Create / reuse a venv under .venv-build/
#   2. pip install -r requirements-dev.txt
#   3. Generate icon.icns from icon.svg if missing
#   4. Run PyInstaller against packaging/photo_bomb.spec
#   5. Re-run codesign --deep --force --options runtime --sign - to catch any
#      nested Qt frameworks PyInstaller didn't sign on its own pass
#   6. Strip any quarantine xattrs picked up from the build environment
#   7. Smoke-test the bundle: `Photo Bomb.app/Contents/MacOS/Photo Bomb --version`
#   8. Build dist/Photo-Bomb-<version>-arm64.dmg via create-dmg (or hdiutil
#      fallback if create-dmg is not installed)
#
# Output:
#   dist/Photo Bomb.app
#   dist/Photo-Bomb-<version>-arm64.dmg
#
# Environment variables:
#   SKIP_DMG=1        skip DMG creation (just produce the .app)
#   SKIP_VENV=1       use the current python without creating .venv-build
#   PYTHON=python3.12 override the python interpreter used to seed the venv

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

ARCH="$(uname -m)"
if [[ "${ARCH}" != "arm64" ]]; then
    echo "error: this build targets arm64 only; current host is ${ARCH}" >&2
    echo "       (run on Apple Silicon, or update target_arch in packaging/photo_bomb.spec)" >&2
    exit 1
fi

PYTHON="${PYTHON:-python3}"
VENV_DIR="${REPO_ROOT}/.venv-build"
SPEC="${REPO_ROOT}/packaging/photo_bomb.spec"
ENTITLEMENTS="${REPO_ROOT}/packaging/entitlements.plist"
ICON_SCRIPT="${REPO_ROOT}/packaging/make_icon.sh"
ICON_PATH="${REPO_ROOT}/src/photo_bomb/assets/icons/icon.icns"
APP_PATH="${REPO_ROOT}/dist/Photo Bomb.app"

# ---------------------------------------------------------------------------
# 1. venv
# ---------------------------------------------------------------------------
if [[ "${SKIP_VENV:-0}" != "1" ]]; then
    if [[ ! -d "${VENV_DIR}" ]]; then
        echo "[venv] creating ${VENV_DIR} with ${PYTHON}"
        "${PYTHON}" -m venv "${VENV_DIR}"
    fi
    # shellcheck source=/dev/null
    source "${VENV_DIR}/bin/activate"
fi

# ---------------------------------------------------------------------------
# 2. dependencies
# ---------------------------------------------------------------------------
echo "[deps] installing requirements-dev.txt"
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements-dev.txt

# ---------------------------------------------------------------------------
# 3. icon
# ---------------------------------------------------------------------------
if [[ ! -f "${ICON_PATH}" ]]; then
    echo "[icon] icon.icns missing - generating"
    bash "${ICON_SCRIPT}"
else
    echo "[icon] reusing ${ICON_PATH}"
fi

# ---------------------------------------------------------------------------
# 4. PyInstaller
# ---------------------------------------------------------------------------
echo "[build] running PyInstaller"
rm -rf build dist
python -m PyInstaller --noconfirm --clean "${SPEC}"

if [[ ! -d "${APP_PATH}" ]]; then
    echo "error: PyInstaller did not produce ${APP_PATH}" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 5. Re-sign (deep) with ad-hoc identity
# ---------------------------------------------------------------------------
echo "[sign] ad-hoc re-signing ${APP_PATH} (deep, hardened runtime)"
codesign \
    --force \
    --deep \
    --options runtime \
    --timestamp=none \
    --entitlements "${ENTITLEMENTS}" \
    --sign - \
    "${APP_PATH}"

echo "[sign] verifying signature"
codesign --verify --deep --strict --verbose=2 "${APP_PATH}"

# ---------------------------------------------------------------------------
# 6. Clear quarantine xattrs
# ---------------------------------------------------------------------------
echo "[xattr] clearing quarantine attributes"
xattr -cr "${APP_PATH}"

# ---------------------------------------------------------------------------
# 7. Smoke test: bundle must launch and print --version
# ---------------------------------------------------------------------------
echo "[smoke] launching bundled app with --version"
SMOKE_BIN="${APP_PATH}/Contents/MacOS/Photo Bomb"
if [[ ! -x "${SMOKE_BIN}" ]]; then
    echo "error: bundle executable missing: ${SMOKE_BIN}" >&2
    exit 1
fi
# QT_QPA_PLATFORM=minimal avoids the bundle trying to grab the windowserver
# in headless / CI environments. main.py exits cleanly on --version before
# any QApplication object is created, but this is belt-and-suspenders.
SMOKE_OUT="$(QT_QPA_PLATFORM=minimal "${SMOKE_BIN}" --version 2>&1)" || {
    echo "error: bundle failed --version smoke test:" >&2
    echo "${SMOKE_OUT}" >&2
    exit 1
}
echo "[smoke] ${SMOKE_OUT}"

# ---------------------------------------------------------------------------
# 8. DMG
# ---------------------------------------------------------------------------
if [[ "${SKIP_DMG:-0}" == "1" ]]; then
    echo "[dmg] SKIP_DMG=1 - skipping DMG creation"
    echo "[done] ${APP_PATH}"
    exit 0
fi

VERSION="$(python -c 'import re,sys; print(next(re.search(r"__version__\s*=\s*[\"\x27]([^\"\x27]+)", l).group(1) for l in open("src/photo_bomb/__init__.py") if l.startswith("__version__")))')"
DMG_PATH="${REPO_ROOT}/dist/Photo-Bomb-${VERSION}-arm64.dmg"
rm -f "${DMG_PATH}"

if command -v create-dmg >/dev/null 2>&1; then
    echo "[dmg] building ${DMG_PATH} via create-dmg"
    create-dmg \
        --volname "Photo Bomb ${VERSION}" \
        --window-pos 200 120 \
        --window-size 540 320 \
        --icon-size 100 \
        --icon "Photo Bomb.app" 140 150 \
        --hide-extension "Photo Bomb.app" \
        --app-drop-link 400 150 \
        --no-internet-enable \
        "${DMG_PATH}" \
        "${APP_PATH}"
else
    echo "[dmg] create-dmg not installed; falling back to hdiutil (no styling)"
    echo "      install with: brew install create-dmg"
    STAGING="$(mktemp -d)"
    cp -R "${APP_PATH}" "${STAGING}/"
    ln -s /Applications "${STAGING}/Applications"
    hdiutil create \
        -volname "Photo Bomb ${VERSION}" \
        -srcfolder "${STAGING}" \
        -ov \
        -format UDZO \
        "${DMG_PATH}"
    rm -rf "${STAGING}"
fi

echo "[done] ${DMG_PATH}"
