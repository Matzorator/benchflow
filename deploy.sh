#!/usr/bin/env bash

set -euo pipefail

SOURCE_DIR="/home/boulette/Projekte/BenchFlow"
TARGET="boulettor@192.168.178.31:~/Projekte/benchflow/BenchFlow/"
REMOTE_DIR="~/Projekte/benchflow/BenchFlow"

DELETE_FLAG=""
if [[ "${1:-}" == "--delete" ]]; then
  DELETE_FLAG="--delete"
fi

rsync -avz ${DELETE_FLAG} \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude 'instance/' \
  --exclude '.env' \
  --exclude '.htaccess' \
  --exclude 'deploy.sh' \
  "${SOURCE_DIR}/app" \
  "${SOURCE_DIR}/requirements.txt" \
  "${SOURCE_DIR}/app.py" \
  "${SOURCE_DIR}/populate_demo_data.py" \
  "${SOURCE_DIR}/wsgi.py" \
  "${SOURCE_DIR}/server-restart.sh" \
  "${TARGET}"

ssh boulettor@192.168.178.31 "cd ${REMOTE_DIR} && chmod +x ./server-restart.sh && ./server-restart.sh"
