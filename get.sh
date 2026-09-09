#!/usr/bin/env bash
# 경북대학교 규정·예규 DB 꾸러미 원격 설치 (git 없이 한 줄로)
#   curl -fsSL https://raw.githubusercontent.com/knugislee1/knu-regulations/main/get.sh | bash
# 저장소 zip을 받아 $HOME/knu-regulations-kit 에 풀고 install.py 를 실행한다.
# 환경변수: KNU_KIT_URL (다른 zip 주소), KNU_KIT_DIR (다른 설치 폴더)
set -euo pipefail
URL="${KNU_KIT_URL:-https://github.com/knugislee1/knu-regulations/archive/refs/heads/main.zip}"
DEST="${KNU_KIT_DIR:-$HOME/knu-regulations-kit}"
PY="$(command -v python3 || command -v python || true)"
[ -z "$PY" ] && { echo "✗ python3 가 필요합니다."; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
echo "다운로드: $URL"
if command -v curl >/dev/null 2>&1; then curl -fsSL "$URL" -o "$TMP/kit.zip"; else wget -qO "$TMP/kit.zip" "$URL"; fi
"$PY" -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$TMP/kit.zip" "$TMP/x"
SRC="$(find "$TMP/x" -maxdepth 3 -name install.py | head -1)"
[ -z "$SRC" ] && { echo "✗ 받은 zip 안에 install.py 가 없습니다."; exit 1; }
SRC="$(dirname "$SRC")"
mkdir -p "$DEST"; find "$DEST" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cp -R "$SRC"/. "$DEST"/
echo "꾸러미 위치: $DEST"
exec "$PY" "$DEST/install.py"
