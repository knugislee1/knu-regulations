#!/usr/bin/env bash
# 경북대학교 규정·예규 DB 꾸러미 설치 (install.py 의 셸 래퍼)
#   bash install.sh            (~/.claude 가 있으면 스킬로, 없으면 이 폴더에 설치)
#   bash install.sh --here     (항상 이 폴더에 설치)
#   bash install.sh --dest DIR
set -euo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "✗ python3 를 찾을 수 없습니다. Python 3.8 이상을 설치한 뒤 다시 실행하세요."; exit 1
fi
exec "$PY" "$KIT/install.py" "$@"
