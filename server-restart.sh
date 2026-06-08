#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_BIN="${PROJECT_DIR}/.venv/bin"
GUNICORN="${VENV_BIN}/gunicorn"
PID_FILE="/tmp/benchflow-gunicorn.pid"
LOG_FILE="/tmp/benchflow-gunicorn.log"
BIND_ADDR="127.0.0.1:8000"
APP_MODULE="wsgi:app"

cd "${PROJECT_DIR}"

if [[ ! -x "${GUNICORN}" ]]; then
  echo "Gunicorn binary not found at ${GUNICORN}" >&2
  exit 1
fi

if [[ -f "${PID_FILE}" ]]; then
  OLD_PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
  if [[ -n "${OLD_PID}" ]] && kill -0 "${OLD_PID}" 2>/dev/null; then
    kill "${OLD_PID}" 2>/dev/null || true
    for _ in {1..20}; do
      if ! kill -0 "${OLD_PID}" 2>/dev/null; then
        break
      fi
      sleep 0.2
    done
    if kill -0 "${OLD_PID}" 2>/dev/null; then
      kill -9 "${OLD_PID}" 2>/dev/null || true
    fi
  fi
  rm -f "${PID_FILE}"
fi

mapfile -t RUNNING_PIDS < <(pgrep -f "gunicorn.*${APP_MODULE}" || true)
if [[ ${#RUNNING_PIDS[@]} -gt 0 ]]; then
  kill "${RUNNING_PIDS[@]}" 2>/dev/null || true
  for _ in {1..20}; do
    mapfile -t RUNNING_PIDS < <(pgrep -f "gunicorn.*${APP_MODULE}" || true)
    if [[ ${#RUNNING_PIDS[@]} -eq 0 ]]; then
      break
    fi
    sleep 0.2
  done
  if [[ ${#RUNNING_PIDS[@]} -gt 0 ]]; then
    kill -9 "${RUNNING_PIDS[@]}" 2>/dev/null || true
  fi
fi
sleep 1

nohup "${GUNICORN}" --workers 2 --bind "${BIND_ADDR}" "${APP_MODULE}" >"${LOG_FILE}" 2>&1 &
NEW_PID=$!
echo "${NEW_PID}" > "${PID_FILE}"

for _ in {1..20}; do
  if ss -ltn | grep -q "${BIND_ADDR}"; then
    echo "BenchFlow listening on ${BIND_ADDR}"
    exit 0
  fi
  sleep 0.3
done

echo "BenchFlow failed to start. Last log lines:" >&2
tail -n 40 "${LOG_FILE}" >&2 || true
exit 1
