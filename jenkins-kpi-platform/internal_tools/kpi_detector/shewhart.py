# -*- coding: utf-8 -*-
"""
Shewhart Control Chart Analysis Module
Implements SPC (Statistical Process Control) rules for small samples
"""

import numpy as np
from typing import Dict, List, Optional, Any


def apply_shewhart_rules(code: str, current_mean: float, 
                         history_records: List[Dict]) -> Dict[str, Any]:
    """Apply Shewhart control chart rules (suitable for small samples, batch mean based)
    
    Control Chart Type: X-bar Chart (based on mean of each batch)
    - Each test's mean is a point on the control chart
    - Uses historical batch means to calculate control limits
    
    Simplified rules (for historical batches >= 2):
    - Rule 1: Single point exceeds +/-3 sigma (UCL/LCL)
    - Rule 2: 3 consecutive points exceed +/-2 sigma (same side)
    - Rule 3: 4 consecutive points monotonically increasing/decreasing
    - Rule 4: 3 consecutive points on same side of CL
    - Zone Rule: Check point distribution across zones
    
    Args:
        code: KPI/Counter code
        current_mean: Current batch mean
        history_records: List of historical records
        
    Returns:
        dict: {
            'violations': list,     # List of violated rules
            'control_limits': dict, # Control limits {UCL, UWL, CL, LWL, LCL}
            'zone': str,           # Current point zone (A/B/C/OutOfControl)
            'batch_means': list,   # Historical batch means
            'chart_data': dict,    # Data for plotting control chart
        }
    """
    result = {
        'violations': [],
        'control_limits': {},
        'zone': None,
        'batch_means': [],
        'chart_data': {}
    }
    
    if current_mean is None:
        return result
    
    # Collect historical batch means
    batch_means = []
    batch_timestamps = []
    
    for record in history_records:
        kpi_data = record.get('kpi_data', {})
        if code in kpi_data:
            hist_raw_data = kpi_data[code].get('raw_data', '')  # ivy0129: renamed for consistency
            if hist_raw_data:
                try:
                    values = [float(x) for x in hist_raw_data.split(',') if x.strip()]
                    if values:
                        batch_means.append(np.mean(values))
                        batch_timestamps.append(record.get('timestamp', ''))
                except:
                    pass
    
    if len(batch_means) < 2:
        # Insufficient historical data to establish control limits
        return result
    
    result['batch_means'] = batch_means.copy()
    
    # Calculate control limits (based on historical batch means)
    cl = np.mean(batch_means)  # Center Line
    
    # For X-bar chart, use standard deviation of batch means
    sigma = np.std(batch_means, ddof=1) if len(batch_means) > 1 else 0
    
    # If sigma is effectively 0 (all historical means identical, or near-zero due to floating-point noise)
    # Use relative threshold to avoid false SPC violations from floating-point rounding artifacts
    SIGMA_NEAR_ZERO_THRESHOLD = max(abs(cl) * 1e-9, 1e-12)
    if sigma < SIGMA_NEAR_ZERO_THRESHOLD:
        # Use relative deviation to decide if current value meaningfully deviates
        rel_dev = abs(current_mean - cl) / (abs(cl) + 1e-10)
        if rel_dev > 1e-6:  # More than 1ppm relative deviation is meaningful
            result['violations'].append('Historical data identical but current value deviates')
            result['zone'] = 'OutOfControl'
        else:
            result['zone'] = 'C'
        result['control_limits'] = {'UCL': cl, 'UWL': cl, 'CL': cl, 'LWL': cl, 'LCL': cl}
        return result
    
    # Control limits
    ucl = cl + 3 * sigma  # Upper Control Limit
    uwl = cl + 2 * sigma  # Upper Warning Limit
    lwl = cl - 2 * sigma  # Lower Warning Limit
    lcl = cl - 3 * sigma  # Lower Control Limit
    
    result['control_limits'] = {
        'UCL': float(ucl),
        'UWL': float(uwl),
        'CL': float(cl),
        'LWL': float(lwl),
        'LCL': float(lcl),
        'sigma': float(sigma)
    }
    
    # Add current mean to sequence
    all_means = batch_means + [current_mean]
    
    # ===== Rule 1: Single point exceeds +/-3 sigma =====
    if current_mean > ucl:
        result['violations'].append('Rule1: Exceeds UCL(+3 sigma)')
    elif current_mean < lcl:
        result['violations'].append('Rule1: Exceeds LCL(-3 sigma)')
    
    # ===== Rule 2: 3 consecutive points exceed +/-2 sigma (same side) =====
    if len(all_means) >= 3:
        last_3 = all_means[-3:]
        # Check upper side
        above_uwl = sum(1 for m in last_3 if m > uwl)
        if above_uwl >= 3:
            result['violations'].append('Rule2: 3 consecutive points exceed +2 sigma')
        # Check lower side
        below_lwl = sum(1 for m in last_3 if m < lwl)
        if below_lwl >= 3:
            result['violations'].append('Rule2: 3 consecutive points exceed -2 sigma')
    
    # ===== Rule 3: 4 consecutive points monotonically increasing/decreasing =====
    if len(all_means) >= 4:
        last_4 = all_means[-4:]
        diffs = [last_4[i+1] - last_4[i] for i in range(len(last_4)-1)]
        if all(d > 0 for d in diffs):
            result['violations'].append('Rule3: 4 consecutive points increasing trend')
        elif all(d < 0 for d in diffs):
            result['violations'].append('Rule3: 4 consecutive points decreasing trend')
    
    # ===== Rule 4: 3 consecutive points on same side of CL =====
    if len(all_means) >= 3:
        last_3 = all_means[-3:]
        above_cl = sum(1 for m in last_3 if m > cl)
        below_cl = sum(1 for m in last_3 if m < cl)
        if above_cl == 3:
            result['violations'].append('Rule4: 3 consecutive points above CL')
        elif below_cl == 3:
            result['violations'].append('Rule4: 3 consecutive points below CL')
    
    # ===== Determine current point Zone =====
    # Zone A: +/-2 sigma ~ +/-3 sigma (Warning Zone)
    # Zone B: +/-1 sigma ~ +/-2 sigma
    # Zone C: 0 ~ +/-1 sigma (Normal Zone)
    z_score = (current_mean - cl) / sigma
    abs_z = abs(z_score)
    
    if abs_z > 3:
        result['zone'] = 'OutOfControl'
    elif abs_z > 2:
        result['zone'] = 'A'  # Warning
    elif abs_z > 1:
        result['zone'] = 'B'
    else:
        result['zone'] = 'C'  # Normal
    
    # Build chart data
    result['chart_data'] = {
        'batch_labels': [f'Test{i+1}' for i in range(len(batch_means))] + ['Current'],
        'batch_values': all_means,
        'timestamps': batch_timestamps + ['Current'],
        'ucl': ucl,
        'uwl': uwl,
        'cl': cl,
        'lwl': lwl,
        'lcl': lcl,
        'zones': calculate_zones_for_series(all_means, cl, sigma)
    }
    
    return result


def calculate_zones_for_series(values: List[float], cl: float, sigma: float) -> List[str]:
    """Calculate zone for each point in series
    
    Args:
        values: List of values
        cl: Center line
        sigma: Standard deviation
        
    Returns:
        List of zone strings ('C', 'B', 'A', 'OutOfControl')
    """
    zones = []
    for v in values:
        z = abs((v - cl) / sigma) if sigma > 0 else 0
        if z > 3:
            zones.append('OutOfControl')
        elif z > 2:
            zones.append('A')
        elif z > 1:
            zones.append('B')
        else:
            zones.append('C')
    return zones


def _handle_degenerate_case(result: Dict, hist_mean: float, current_mean: float,
                             current_values: List[float], hist_means: List[float],
                             history_records: List[Dict], code: str) -> Dict:
    """Handle zero-variance (degenerate) KPI cases with rule-based judgment
    
    When σ = 0, SPC-based anomaly detection is invalid. Instead, use semantic
    rules based on the KPI type (ceiling/floor/constant).
    
    Rule definitions:
    - Ceiling KPI (history=100%): Success rate KPIs where 100% is ideal
        * current = 100%: Normal (Stable)
        * current >= 99.8%: Normal (Acceptable)  
        * current >= 99%: Suspicious
        * current < 99%: Regression
    
    - Floor KPI (history=0): Zero-count KPIs where 0 is ideal (e.g., error counts)
        * current = 0: Normal (Stable)
        * current <= 0.2: Normal (Acceptable minor fluctuation)
        * current <= 1: Suspicious
        * current > 1: Regression
    
    - Constant KPI (other fixed values): Non-percentage fixed values
        * current = history: Normal (Stable)
        * abs(delta) <= threshold: Suspicious (minor fluctuation)
        * abs(delta) > threshold: Regression
    
    Args:
        result: Result dict to update
        hist_mean: Historical mean value
        current_mean: Current mean value
        current_values: Current raw values
        hist_means: List of historical batch means
        history_records: Historical records
        code: KPI code
        
    Returns:
        Updated result dict
    """
    delta = current_mean - hist_mean
    
    # Classify degenerate type
    if hist_mean == 100:
        result['degenerate_type'] = 'ceiling'
    elif hist_mean == 0:
        result['degenerate_type'] = 'floor'
    else:
        result['degenerate_type'] = 'constant'
    
    result['judgment_reasons'].append(f'Zero-variance KPI (σ=0, type={result["degenerate_type"]})')
    
    # ===== Ceiling KPI Rules (history = 100%) =====
    if result['degenerate_type'] == 'ceiling':
        if current_mean == 100:
            result['severity'] = 'Normal'
            result['judgment_reasons'].append('Ceiling KPI: current=100% (Stable)')
        elif current_mean >= 99.8:
            result['severity'] = 'Normal'
            result['judgment_reasons'].append(f'Ceiling KPI: current={current_mean:.2f}% >= 99.8% (Acceptable)')
        elif current_mean >= 99:
            result['severity'] = 'Suspicious'
            result['judgment_reasons'].append(f'Ceiling KPI: current={current_mean:.2f}% (99%~99.8%, Minor drop)')
        else:
            result['severity'] = 'Regression'
            result['judgment_reasons'].append(f'Ceiling KPI: current={current_mean:.2f}% < 99% (Significant drop)')
        
        # Check if any individual value dropped significantly
        min_val = min(current_values)
        if min_val < 99 and result['severity'] != 'Regression':
            result['severity'] = 'Suspicious'
            result['judgment_reasons'].append(f'Ceiling KPI: min value {min_val:.2f}% < 99%')
    
    # ===== Floor KPI Rules (history = 0) =====
    elif result['degenerate_type'] == 'floor':
        if current_mean == 0:
            result['severity'] = 'Normal'
            result['judgment_reasons'].append('Floor KPI: current=0 (Stable)')
        elif current_mean <= 0.2:
            result['severity'] = 'Normal'
            result['judgment_reasons'].append(f'Floor KPI: current={current_mean:.3f} <= 0.2 (Minor fluctuation)')
        elif current_mean <= 1:
            result['severity'] = 'Suspicious'
            result['judgment_reasons'].append(f'Floor KPI: current={current_mean:.3f} (0.2~1, Warning)')
        else:
            result['severity'] = 'Regression'
            result['judgment_reasons'].append(f'Floor KPI: current={current_mean:.3f} > 1 (Significant increase)')
        
        # Check if any individual value increased significantly
        max_val = max(current_values)
        if max_val > 2 and result['severity'] != 'Regression':
            result['severity'] = 'Regression'
            result['judgment_reasons'].append(f'Floor KPI: max value {max_val:.3f} > 2')
    
    # ===== Constant KPI Rules (other fixed values) =====
    else:
        # For constant values, use relative difference (percentage) for larger values
        # and absolute difference for smaller values
        if abs(hist_mean) >= 10:
            # Use relative threshold (0.5% tolerance)
            rel_diff = abs(delta / hist_mean) * 100 if hist_mean != 0 else 0
            if current_mean == hist_mean:
                result['severity'] = 'Normal'
                result['judgment_reasons'].append(f'Constant KPI: current={current_mean} = history (Stable)')
            elif rel_diff <= 0.5:
                result['severity'] = 'Normal'
                result['judgment_reasons'].append(f'Constant KPI: Δ={delta:.2f} ({rel_diff:.2f}% <= 0.5%)')
            elif rel_diff <= 2:
                result['severity'] = 'Suspicious'
                result['judgment_reasons'].append(f'Constant KPI: Δ={delta:.2f} ({rel_diff:.2f}%, 0.5%~2%)')
            else:
                result['severity'] = 'Regression'
                result['judgment_reasons'].append(f'Constant KPI: Δ={delta:.2f} ({rel_diff:.2f}% > 2%)')
        else:
            # Use absolute threshold for small values
            if current_mean == hist_mean:
                result['severity'] = 'Normal'
                result['judgment_reasons'].append(f'Constant KPI: current={current_mean} = history (Stable)')
            elif abs(delta) <= 0.1:
                result['severity'] = 'Normal'
                result['judgment_reasons'].append(f'Constant KPI: Δ={delta:.4f} <= 0.1 (Minor)')
            elif abs(delta) <= 1:
                result['severity'] = 'Suspicious'
                result['judgment_reasons'].append(f'Constant KPI: Δ={delta:.4f} (0.1~1, Warning)')
            else:
                result['severity'] = 'Regression'
                result['judgment_reasons'].append(f'Constant KPI: Δ={delta:.4f} > 1')
    
    # Set z_score to None to indicate SPC not applicable
    result['z_score'] = None
    result['sigma_level'] = None
    
    # Apply shewhart rules but mark as limited
    shewhart_result = apply_shewhart_rules(code, current_mean, history_records)
    shewhart_result['degenerate_note'] = 'SPC rules limited due to zero-variance history'
    result['shewhart'] = shewhart_result
    
    return result


def calculate_severity_from_history(code: str, current_values: List[float], 
                                     history_records: List[Dict]) -> Dict[str, Any]:
    """Calculate Severity level based on historical data
    
    Severity judgment logic (based on historical statistics):
    - Normal: Current mean within historical mean +/-2 sigma
    - Suspicious: Exceeds +/-2 sigma but not +/-3 sigma, or triggers Shewhart warning rules
    - Regression: Exceeds +/-3 sigma or triggers Shewhart severe rules (trend, consecutive deviation)
    - NoHistory: Insufficient historical data (<2 records)
    
    Special handling for Zero-Variance (Degenerate) KPIs:
    - When σ = 0, SPC rules are invalid; use rule-based/semantic judgment instead
    - For success rate KPIs (value=100%): use threshold-based rules
    - For zero-count KPIs (value=0): use count increase rules
    
    Args:
        code: KPI/Counter code
        current_values: Current data values
        history_records: List of historical records
        
    Returns:
        dict with severity analysis results
    """
    result = {
        'severity': 'NoHistory',
        'z_score': None,
        'anomaly_count': 0,
        'anomaly_ratio': 0.0,
        'trend_direction': None,
        'hist_mean': None,
        'hist_std': None,
        'current_mean': None,
        'sigma_level': None,
        'judgment_reasons': [],
        'shewhart': {},
        'is_degenerate': False,  # Zero-variance flag
        'degenerate_type': None,  # 'ceiling', 'floor', 'constant'
    }
    
    if not current_values:
        result['judgment_reasons'].append('No current data')
        return result
    
    if not history_records:
        result['judgment_reasons'].append('No historical data')
        return result
    
    # Collect historical data (mean of each record)
    hist_all_values = []  # All historical data points
    hist_means = []       # Mean of each test (for trend detection)
    hist_cvs = []
    
    for record in history_records:
        kpi_data = record.get('kpi_data', {})
        if code in kpi_data:
            hist_raw_data = kpi_data[code].get('raw_data', '')  # ivy0129: renamed for consistency
            cv_value = kpi_data[code].get('cv', None)
            mean_value = kpi_data[code].get('mean', None)
            if hist_raw_data:
                try:
                    values = [float(x) for x in hist_raw_data.split(',') if x.strip()]
                    hist_all_values.extend(values)
                    if values:
                        hist_means.append(np.mean(values))
                except:
                    pass
            if cv_value is not None:
                hist_cvs.append(cv_value)
    
    if len(hist_means) < 2:
        result['judgment_reasons'].append('Insufficient history (<2 records)')
        return result
    
    # Calculate historical statistics
    hist_mean = np.mean(hist_all_values)
    hist_std = np.std(hist_all_values)
    
    result['hist_mean'] = float(hist_mean)
    result['hist_std'] = float(hist_std)
    
    # Calculate current mean
    current_mean = np.mean(current_values)
    result['current_mean'] = float(current_mean)
    
    # ========== DEGENERATE CASE DETECTION (σ = 0) ==========
    # Use near-zero threshold to handle floating-point noise (e.g., 7.1e-15 instead of exact 0)
    HIST_STD_NEAR_ZERO = max(abs(hist_mean) * 1e-9, 1e-12)
    if hist_std < HIST_STD_NEAR_ZERO:
        result['is_degenerate'] = True
        return _handle_degenerate_case(result, hist_mean, current_mean, current_values, 
                                        hist_means, history_records, code)
    
    # ========== NORMAL CASE (σ > 0): SPC-based judgment ==========
    # Calculate Z-Score and sigma level
    z_score = (current_mean - hist_mean) / hist_std
    result['z_score'] = float(z_score)
    result['sigma_level'] = float(abs(z_score))
    
    # Anomaly point detection (points exceeding historical +/-2 sigma)
    if hist_std > 0:
        upper_2sigma = hist_mean + 2 * hist_std
        lower_2sigma = hist_mean - 2 * hist_std
        anomaly_count = sum(1 for v in current_values if v > upper_2sigma or v < lower_2sigma)
        result['anomaly_count'] = anomaly_count
        result['anomaly_ratio'] = float(anomaly_count / len(current_values))
    
    # Trend detection (check if recent points have consecutive same-direction deviation)
    if len(hist_means) >= 3:
        all_means = hist_means + [current_mean]
        recent_means = all_means[-min(4, len(all_means)):]
        if len(recent_means) >= 3:
            diffs = [recent_means[i+1] - recent_means[i] for i in range(len(recent_means)-1)]
            if all(d > 0 for d in diffs):
                result['trend_direction'] = 'increasing'
            elif all(d < 0 for d in diffs):
                result['trend_direction'] = 'decreasing'
    
    # ===== Apply Shewhart control chart rules =====
    shewhart_result = apply_shewhart_rules(code, current_mean, history_records)
    result['shewhart'] = shewhart_result
    
    # Determine Severity (combining sigma level and Shewhart rules)
    sigma_level = result.get('sigma_level', 0) or 0
    shewhart_violations = shewhart_result.get('violations', [])
    
    # Base judgment (based on sigma level)
    if sigma_level <= 2:
        result['severity'] = 'Normal'
        result['judgment_reasons'].append(f'Within +/-2 sigma (sigma={sigma_level:.2f})')
    elif sigma_level <= 3:
        result['severity'] = 'Suspicious'
        result['judgment_reasons'].append(f'Exceeds +/-2 sigma but within +/-3 sigma (sigma={sigma_level:.2f})')
    else:
        result['severity'] = 'Regression'
        result['judgment_reasons'].append(f'Exceeds +/-3 sigma (sigma={sigma_level:.2f})')
    
    # Shewhart rule upgrade judgment
    if shewhart_violations:
        # Severe rules (upgrade to Regression)
        severe_rules = ['Rule1', 'Rule3', 'Rule4']  # Out of control, trend, consecutive deviation
        warning_rules = ['Rule2']  # Warning rules
        
        has_severe = any(any(r in v for r in severe_rules) for v in shewhart_violations)
        has_warning = any(any(r in v for r in warning_rules) for v in shewhart_violations)
        
        if has_severe and result['severity'] != 'Regression':
            result['severity'] = 'Regression'
        elif has_warning and result['severity'] == 'Normal':
            result['severity'] = 'Suspicious'
        
        # Add Shewhart violations to reasons
        for v in shewhart_violations:
            result['judgment_reasons'].append(f'SPC:{v}')
    
    # Add Zone information
    if shewhart_result.get('zone'):
        zone = shewhart_result['zone']
        if zone == 'OutOfControl':
            result['judgment_reasons'].append('Zone: OutOfControl')
        elif zone == 'A':
            result['judgment_reasons'].append('Zone: A (Warning)')
    
    # Trend deviation upgrade to Regression (if Shewhart rules didn't detect it)
    if result['trend_direction'] and 'Rule3' not in str(shewhart_violations):
        if result['severity'] != 'Regression':
            result['severity'] = 'Regression'
            result['judgment_reasons'].append(f"Trend deviation ({result['trend_direction']})")
    
    # High anomaly ratio upgrade
    if result['anomaly_ratio'] > 0.5 and result['severity'] == 'Normal':
        result['severity'] = 'Suspicious'
        result['judgment_reasons'].append(f"High anomaly ratio ({result['anomaly_count']}/{len(current_values)})")
    
    return result
