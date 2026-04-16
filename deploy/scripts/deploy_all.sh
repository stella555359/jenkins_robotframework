#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/opt/jenkins_robotframework"
REPORTING_DIR="$REPO_ROOT/reporting-portal"
KPI_DIR="$REPO_ROOT/kpi-portal"

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

if [ -f "$KPI_DIR/requirements.txt" ]; then
    echo "[deploy] install kpi-portal dependencies"
    cd "$KPI_DIR"
    python3 -m venv venv
    . venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
fi

echo "[deploy] restart services"
sudo systemctl restart reporting-portal || true
sudo systemctl restart kpi-portal || true

echo "[deploy] done"