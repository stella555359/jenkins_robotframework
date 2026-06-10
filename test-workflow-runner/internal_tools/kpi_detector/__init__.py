# KPI Anomaly Detector Package
# Version: 2.3.0 (ivy0203)
# Date: 2026-02-03
# Features: Reclassified strategies (IQR/Poisson/Relative/Z-Score/KS-Test)
#           Legacy strategies mapped to core strategies

__version__ = "2.3.0"
__all__ = [
    'KPIAnomalyDetector', 
    'ASSETS_DIR',
    'PATHS', 
    'COLORS',
    'configure_runtime_paths',
    'KPIType',
    'DetectionStrategy',
    'KPITypeClassifier',
    'TypeBasedAnomalyDetector',
    'StrategyBasedDetector',
    'StrategyConfig',
    'get_classifier',
    'get_type_based_detector',
    'get_strategy_based_detector',
    'normalize_strategy',
    'LEGACY_STRATEGY_MAP',
    'run_detector_from_payload',
]


def __getattr__(name):
    if name == 'KPIAnomalyDetector':
        from .detector import KPIAnomalyDetector

        return KPIAnomalyDetector
    if name in {'ASSETS_DIR', 'COLORS', 'PATHS', 'configure_runtime_paths'}:
        from . import config

        return getattr(config, name)
    if name in {
        'KPIType',
        'DetectionStrategy',
        'KPITypeClassifier',
        'TypeBasedAnomalyDetector',
        'StrategyBasedDetector',
        'StrategyConfig',
        'get_classifier',
        'get_type_based_detector',
        'get_strategy_based_detector',
        'normalize_strategy',
        'LEGACY_STRATEGY_MAP',
    }:
        from . import kpi_types

        return getattr(kpi_types, name)
    if name == 'run_detector_from_payload':
        from .service import run_detector_from_payload

        return run_detector_from_payload
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
