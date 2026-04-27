# -*- coding: utf-8 -*-
"""
Utility functions for KPI Anomaly Detector
"""

import re
import numpy as np
import pandas as pd


def classify_code(code: str) -> str:
    """Classify Code as Counter or KPI type
    
    Args:
        code: The code string to classify
        
    Returns:
        'Counter', 'KPI', or 'Other'
    """
    code = str(code).strip()
    if re.match(r'^M\d{5}C\d{1,5}$', code, re.IGNORECASE):
        return 'Counter'
    elif re.search(r'NR', code, re.IGNORECASE):
        return 'KPI'
    else:
        return 'Other'


def generate_sparkline(raw_data: str) -> str:
    """Generate text-based sparkline using Unicode bar characters
    
    Args:
        raw_data: Comma-separated numeric values
        
    Returns:
        Unicode sparkline string
    """
    if not raw_data:
        return ''
    
    try:
        values = [float(x) for x in raw_data.split(',') if x.strip()]
        if not values:
            return ''
        
        # Unicode bar characters (low to high)
        bars = '\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588'
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            # All values are the same, use middle height
            return bars[4] * len(values)
        
        # Normalize to 0-7 range
        sparkline = ''
        for v in values:
            normalized = (v - min_val) / (max_val - min_val)
            bar_idx = int(normalized * 7)
            bar_idx = min(7, max(0, bar_idx))
            sparkline += bars[bar_idx]
        
        return sparkline
    except:
        return ''


def parse_raw_data(raw_data: str) -> list:
    """Parse comma-separated raw data string to list of floats
    
    Args:
        raw_data: Comma-separated numeric values
        
    Returns:
        List of float values
    """
    if not raw_data:
        return []
    try:
        return [float(x) for x in raw_data.split(',') if x.strip()]
    except:
        return []


def calculate_cv(values: list) -> tuple:
    """Calculate coefficient of variation
    
    Args:
        values: List of numeric values
        
    Returns:
        Tuple of (mean, std, cv_percentage)
    """
    if not values:
        return np.nan, np.nan, np.nan
    
    arr = np.array(values)
    mean_val = np.mean(arr)
    std_val = np.std(arr, ddof=0)
    
    if abs(mean_val) < 0.001:
        cv = np.nan
    else:
        cv = (std_val / mean_val) * 100
    
    return mean_val, std_val, cv


def calculate_trimmed_cv(values: list) -> tuple:
    """Calculate CV after removing min and max values
    
    Args:
        values: List of numeric values (must have >= 5 elements)
        
    Returns:
        Tuple of (trimmed_mean, trimmed_std, trimmed_cv)
    """
    if len(values) < 5:
        return np.nan, np.nan, np.nan
    
    sorted_vals = sorted(values)
    trimmed = sorted_vals[1:-1]  # Remove min and max
    
    return calculate_cv(trimmed)


def is_kpi_pattern(code: str) -> bool:
    """Check if code matches KPI pattern (NR_XXXXx or SCOUT_NR_XXXXx)
    
    Args:
        code: Code string to check
        
    Returns:
        True if matches KPI pattern
    """
    pattern = r'((?:SCOUT_)?NR_\d{2,4})([a-zA-Z])'
    return bool(re.search(pattern, code, re.IGNORECASE))


def is_counter_pattern(code: str) -> bool:
    """Check if code matches Counter pattern (MxxxxxCxxxxx)
    
    Args:
        code: Code string to check
        
    Returns:
        True if matches Counter pattern
    """
    return bool(re.match(r'^M\d{5}C\d{1,5}$', code, re.IGNORECASE))
