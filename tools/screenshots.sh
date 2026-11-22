#!/bin/zsh
# Full-page screenshots of the local preview.
# Usage: URL=http://127.0.0.1:8766/ tools/screenshots.sh
# Chrome headless will not size a window below ~500 px, so every width is rendered
# inside an iframe of exactly that width and then centre-cropped.
set -e
cd "$(dirname "$0")/.."
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL="${URL:-http://127.0.0.1:8766/}"
mkdir -p preview
run() { local prof=$(mktemp -d); "$CHROME" --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$prof" \
  --force-device-scale-factor=1 --virtual-time-budget=4000 "$@" 2>/dev/null; rm -rf "$prof"; }
shoot() {
  local w=$1 name=$2 h win
  cat > docs/__frame.html <<HTML
<!doctype html><body style="margin:0;background:#888"><iframe id=f src="./" style="display:block;margin:0 auto;border:0;width:${w}px;height:\${H}px"></iframe>
<script>const H=new URLSearchParams(location.search).get('h')||800;f.style.height=H+'px';
f.onload=()=>document.body.setAttribute('data-h',f.contentDocument.documentElement.scrollHeight)</script>
HTML
  win=$(( w < 600 ? 600 : w ))
  h=$(run --window-size=${win},800 --dump-dom "${URL}__frame.html" | sed -n 's/.*data-h="\([0-9]*\)".*/\1/p')
  run --window-size=${win},${h} --screenshot="preview/$name" "${URL}__frame.html?h=${h}" >/dev/null
  sips -c "$h" "$w" "preview/$name" >/dev/null
  echo "preview/$name  ${w} x ${h}"
}
trap 'rm -f docs/__frame.html' EXIT
shoot 1440 desktop-1440.png
shoot 390 mobile-390.png
shoot 360 mobile-360.png
