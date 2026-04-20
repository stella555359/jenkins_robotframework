#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/opt/jenkins_robotframework"
REPORTING_DIR="$REPO_ROOT/reporting-portal"
AUTOMATION_PORTAL_DIR="$REPO_ROOT/automation-portal"

echo "[deploy] repo root: $REPO_ROOT"

cd "$REPO_ROOT"
git fetch origin
git checkout main
git pull --ff-only origin main

if [ -f "$REPORTING_DIR/requirements.txt" ]; then
    echo "[deploy] install reporting-portal dependencies"
    cd "$REPORTING_DIR"
    python3 -m venv venv
    . venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
fi

if [ -f "$AUTOMATION_PORTAL_DIR/package.json" ]; then
    echo "[deploy] automation-portal exists"
    echo "[deploy] frontend build/publish step will be added separately"
fi

echo "[deploy] restart services"
sudo systemctl restart reporting-portal || true

echo "[deploy] done"