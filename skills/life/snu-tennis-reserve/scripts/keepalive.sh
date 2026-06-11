#!/bin/bash
# 세션 keepalive — cron에서 10~15분마다 실행해 PHPSESSID 만료 방지.
# crontab 예: */12 * * * * /path/to/scripts/keepalive.sh
cd "$(dirname "$0")"
ts=$(date '+%Y-%m-%d %H:%M:%S')
if python check_session.py >/dev/null 2>&1; then
  echo "$ts OK" >> keepalive.log
else
  echo "$ts EXPIRED - re-login needed (./run.sh login)" >> keepalive.log
fi
