#!/bin/bash
# 사용법: ./run.sh login | check | reserve
cd "$(dirname "$0")"

# Playwright가 설치된 python을 쓴다. conda env가 활성화돼 있으면 그 env의
# lib을 LD_LIBRARY_PATH에 추가 (일부 환경에서 chromium 구동에 필요).
PY="${TENNIS_PYTHON:-python}"
if [ -n "$CONDA_PREFIX" ]; then
  export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
fi
# WSLg 디스플레이 (헤드 모드 창 표시용) — 비어있으면 기본값 세팅
export DISPLAY=${DISPLAY:-:0}

case "$1" in
  login)   $PY login_setup.py ;;
  check)   $PY check_session.py ;;
  reserve) shift; [ "$1" = "--" ] && shift; $PY -u reserve.py "$@" 2>&1 | tee -a reserve.log ;;
  *) echo "usage: $0 {login|check|reserve}" ;;
esac
