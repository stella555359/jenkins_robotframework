# -*- coding: utf-8 -*-
"""
Configuration module for KPI Anomaly Detector
"""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PACKAGE_DIR / "assets" / "kpi_xml"
DEFAULT_RUNTIME_ROOT = PACKAGE_DIR / "_runtime"


def _build_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "scripts": PACKAGE_DIR,
        "data": runtime_root / "data",
        "reports": runtime_root / "reports",
        "docs": runtime_root / "docs",
    }


PATHS = _build_paths(DEFAULT_RUNTIME_ROOT)


def configure_runtime_paths(
    *,
    runtime_root: Path | None = None,
    data_dir: Path | None = None,
    reports_dir: Path | None = None,
    docs_dir: Path | None = None,
) -> dict[str, Path]:
    base_root = Path(runtime_root) if runtime_root is not None else DEFAULT_RUNTIME_ROOT
    updated = _build_paths(base_root)
    if data_dir is not None:
        updated["data"] = Path(data_dir)
    if reports_dir is not None:
        updated["reports"] = Path(reports_dir)
    if docs_dir is not None:
        updated["docs"] = Path(docs_dir)

    PATHS.clear()
    PATHS.update(updated)

    for key in ("data", "reports", "docs"):
        PATHS[key].mkdir(parents=True, exist_ok=True)
    return PATHS

# ========== Color Definitions ==========
COLORS = {
    'critical': 'FF0000',      # Red - Critical anomaly
    'warning': 'FFA500',       # Orange - Warning
    'suspicious': '9370DB',    # Purple - Suspicious (CV consistent but T-Test Fail)
    'caution': 'FFFF00',       # Yellow - Caution
    'normal': '90EE90',        # Light green - Normal
    'header': '4472C4',        # Blue - Header
    'light_blue': 'ADD8E6',    # Light blue
    'grey': 'D3D3D3',          # Grey
    'improved': '00FF00',      # Bright green - Improved
    'worsened': 'FF6B6B',      # Light red - Worsened
}

# ========== Analysis Thresholds ==========
DEFAULT_CV_THRESHOLD = 5.0         # CV threshold percentage
DEFAULT_P_VALUE_THRESHOLD = 0.05   # P-value threshold for t-test

# ========== History File ==========
HISTORY_FILENAME = 'kpi_history_records.json'
SCOUT_HISTORY_FILENAME = 'kpi_history_records_scout.json'

# ========== Filename Pattern for Scenario Matching ==========
# Group 1: Version (26R2.0115.2)
# Group 2: Test config (T076.SCF.26R1post5)
# Group 3: UE count (32UEs)
# Group 4: Scenario description (httpDL_bigShort)
FILENAME_PATTERN = r'(\d{2}R\d\.\d{4}\.\d{1,3})_(T\d+\.SCF\.\w+)[._](\d+UEs)[._](.+?)_\d+csv'


configure_runtime_paths()
