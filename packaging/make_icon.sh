#!/usr/bin/env bash
#
# Generate src/photo_bomb/assets/icons/icon.icns from icon.svg.
#
# Required tools (any one for SVG -> PNG):
#   - rsvg-convert (preferred; `brew install librsvg`)
#   - or: qlmanage  (built into macOS, lower quality)
# Required tools (always):
#   - sips        (built into macOS, used for PNG resizing)
#   - iconutil    (built into macOS, packs the .iconset into .icns)
#
# This script is idempotent: re-running it just rebuilds icon.icns in place.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ICON_DIR="${REPO_ROOT}/src/photo_bomb/assets/icons"
SVG="${ICON_DIR}/icon.svg"
ICONSET="${ICON_DIR}/icon.iconset"
ICNS="${ICON_DIR}/icon.icns"
MASTER_PNG="${ICON_DIR}/icon_master.png"

if [[ ! -f "${SVG}" ]]; then
    echo "error: ${SVG} not found" >&2
    exit 1
fi

echo "[icon] rendering ${SVG} -> 1024x1024 PNG"
if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -w 1024 -h 1024 "${SVG}" -o "${MASTER_PNG}"
elif command -v qlmanage >/dev/null 2>&1; then
    # qlmanage is a fallback; quality is decent for placeholder icons.
    tmpdir="$(mktemp -d)"
    qlmanage -t -s 1024 -o "${tmpdir}" "${SVG}" >/dev/null
    mv "${tmpdir}"/icon.svg.png "${MASTER_PNG}"
    rm -rf "${tmpdir}"
else
    echo "error: need rsvg-convert (brew install librsvg) or qlmanage" >&2
    exit 1
fi

echo "[icon] generating .iconset"
rm -rf "${ICONSET}"
mkdir -p "${ICONSET}"

# Required sizes per Apple Human Interface Guidelines for .icns.
# Each entry: <pixel_size> <iconset_filename>
declare -a sizes=(
    "16    icon_16x16.png"
    "32    icon_16x16@2x.png"
    "32    icon_32x32.png"
    "64    icon_32x32@2x.png"
    "128   icon_128x128.png"
    "256   icon_128x128@2x.png"
    "256   icon_256x256.png"
    "512   icon_256x256@2x.png"
    "512   icon_512x512.png"
    "1024  icon_512x512@2x.png"
)

for entry in "${sizes[@]}"; do
    size="${entry%% *}"
    name="${entry##* }"
    sips -z "${size}" "${size}" "${MASTER_PNG}" --out "${ICONSET}/${name}" >/dev/null
done

echo "[icon] packing .icns"
iconutil -c icns "${ICONSET}" -o "${ICNS}"

# Cleanup: keep the .iconset in case someone wants to inspect it, but remove
# the master PNG since it's regenerated on every run.
rm -f "${MASTER_PNG}"

echo "[icon] wrote ${ICNS}"
