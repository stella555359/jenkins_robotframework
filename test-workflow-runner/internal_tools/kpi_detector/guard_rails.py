#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Guard Rails Detection Framework

Implements hard guard rails for anomaly detection:
- GR-M1: Magnitude consistency check (order of magnitude)
- GR-S1: Support interval overlap check (range intersection)
- GR-S2: Extreme value jump detection
- GR-S3: Sigma-to-mean ratio validity check

Alternative detection methods for special data patterns:
- IQR: For high-variance/inconsistent data
- Poisson: For count/discrete data with small values
- RelativeChange: For ratio/percentage data
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from enum import Enum


class GuardRailViolation(Enum):
    """Guard Rail violation types"""
    NONE = "none"
    GR_M1_MAGNITUDE = "GR-M1: Magnitude shift"
    GR_S1_NO_OVERLAP = "GR-S1: No range overlap"
    GR_S2_EXTREME_JUMP = "GR-S2: Extreme value jump"
    GR_S3_SIGMA_INVALID = "GR-S3: Sigma invalid"


@dataclass
class GuardRailResult:
    """Result of Guard Rail check"""
    passed: bool
    violation: GuardRailViolation
    severity: str  # 'Normal', 'Suspicious', 'Regression', 'HardRegression'
    reason: str
    details: Dict[str, Any]


@dataclass
class GuardRailConfig:
    """Configuration for Guard Rail checks"""
    # GR-M1: Magnitude ratio threshold
    magnitude_ratio_R: float = 10.0  # Conservative: 10, Strict: 100
    magnitude_min_value: float = 0.0005  # Skip check if both means below this (changed from 0.01)
    
    # GR-S1: Range overlap
    require_overlap: bool = True
    
    # GR-S2: Extreme value jump
    max_delta_ratio: float = 5.0  # Max acceptable ratio change in extremes
    max_delta_absolute: Optional[float] = None  # Optional absolute threshold
    
    # GR-S3: Sigma validity
    sigma_mean_epsilon: float = 0.001  # σ/|μ| below this is invalid
    min_points_for_sigma: int = 3
    
    # IQR detection thresholds
    iqr_multiplier: float = 1.5  # Standard IQR multiplier
    iqr_strict_multiplier: float = 3.0  # For Regression level
    
    # Poisson detection thresholds
    poisson_alpha: float = 0.05  # Significance level for Suspicious
    poisson_alpha_strict: float = 0.01  # Significance level for Regression
    
    # Relative change detection thresholds
    relative_change_warning: float = 50.0  # % change for Suspicious
    relative_change_critical: float = 100.0  # % change for Regression


class GuardRails:
    """Guard Rails detection framework"""
    
    def __init__(self, config: Optional[GuardRailConfig] = None):
        self.config = config or GuardRailConfig()
    
    def check_all(self, 
                  current_values: List[float],
                  history_values: List[float],
                  hist_mean: float,
                  hist_std: float) -> GuardRailResult:
        """Run all guard rail checks
        
        Returns the most severe violation found, or NONE if all pass.
        """
        current_values = [v for v in current_values if v is not None and not np.isnan(v)]
        history_values = [v for v in history_values if v is not None and not np.isnan(v)]
        
        if not current_values:
            return GuardRailResult(
                passed=True,
                violation=GuardRailViolation.NONE,
                severity='Normal',
                reason='No current data',
                details={}
            )
        
        current_mean = np.mean(current_values)
        current_std = np.std(current_values) if len(current_values) > 1 else 0
        
        # GR-M1: Magnitude consistency (pass history_values for zero-inflated detection)
        gr_m1 = self._check_gr_m1(current_mean, hist_mean, history_values)
        if not gr_m1.passed:
            return gr_m1
        
        # GR-S1: Range overlap
        if history_values:
            gr_s1 = self._check_gr_s1(current_values, history_values)
            if not gr_s1.passed:
                return gr_s1
        
        # GR-S2: Extreme value jump
        if history_values:
            gr_s2 = self._check_gr_s2(current_values, history_values, hist_mean)
            if not gr_s2.passed:
                return gr_s2
        
        # GR-S3: Sigma validity
        gr_s3 = self._check_gr_s3(current_mean, current_std, hist_mean, hist_std)
        # GR-S3 doesn't cause HardRegression, just indicates σ is unreliable
        
        return GuardRailResult(
            passed=True,
            violation=GuardRailViolation.NONE,
            severity='Normal',
            reason='All guard rails passed',
            details={
                'gr_m1': 'passed',
                'gr_s1': 'passed',
                'gr_s2': 'passed',
                'gr_s3': gr_s3.details
            }
        )
    
    def _check_gr_m1(self, current_mean: float, hist_mean: float, 
                      history_values: Optional[List[float]] = None) -> GuardRailResult:
        """GR-M1: Magnitude consistency check
        
        |μ_current| / |μ_history| ∈ [1/R, R]
        
        Special handling for zero-inflated data:
        - If >50% of history values are near-zero, current=0 is considered normal
        """
        R = self.config.magnitude_ratio_R
        min_val = self.config.magnitude_min_value
        
        abs_current = abs(current_mean)
        abs_history = abs(hist_mean)
        
        # Skip if both near zero
        if abs_current < min_val and abs_history < min_val:
            return GuardRailResult(
                passed=True,
                violation=GuardRailViolation.NONE,
                severity='Normal',
                reason='GR-M1: Both means near zero, skip magnitude check',
                details={'current_mean': current_mean, 'hist_mean': hist_mean, 'skipped': True}
            )
        
        # Handle zero history
        if abs_history < min_val:
            if abs_current > min_val:
                return GuardRailResult(
                    passed=False,
                    violation=GuardRailViolation.GR_M1_MAGNITUDE,
                    severity='HardRegression',
                    reason=f'GR-M1: Value appeared from zero (0 -> {current_mean:.4f})',
                    details={'current_mean': current_mean, 'hist_mean': hist_mean, 'ratio': float('inf')}
                )
            return GuardRailResult(
                passed=True,
                violation=GuardRailViolation.NONE,
                severity='Normal',
                reason='GR-M1: Both at zero',
                details={'current_mean': current_mean, 'hist_mean': hist_mean}
            )
        
        # Handle zero current - check for zero-inflated historical data first
        if abs_current < min_val:
            # Check if history is zero-inflated (>50% near-zero values)
            if history_values and len(history_values) > 0:
                near_zero_count = sum(1 for v in history_values if abs(v) < min_val)
                zero_ratio = near_zero_count / len(history_values)
                
                # If history is zero-inflated, current=0 is normal
                if zero_ratio >= 0.5:
                    return GuardRailResult(
                        passed=True,
                        violation=GuardRailViolation.NONE,
                        severity='Normal',
                        reason=f'GR-M1: Zero-inflated data (hist zero ratio={zero_ratio:.0%}), current=0 is normal',
                        details={
                            'current_mean': current_mean, 
                            'hist_mean': hist_mean, 
                            'zero_inflated': True,
                            'hist_zero_ratio': zero_ratio
                        }
                    )
            
            # Not zero-inflated, this is a real drop to zero
            return GuardRailResult(
                passed=False,
                violation=GuardRailViolation.GR_M1_MAGNITUDE,
                severity='HardRegression',
                reason=f'GR-M1: Value dropped to zero ({hist_mean:.4f} -> 0)',
                details={'current_mean': current_mean, 'hist_mean': hist_mean, 'ratio': 0}
            )
        
        # Calculate ratio
        ratio = abs_current / abs_history
        
        if ratio < 1/R or ratio > R:
            return GuardRailResult(
                passed=False,
                violation=GuardRailViolation.GR_M1_MAGNITUDE,
                severity='HardRegression',
                reason=f'GR-M1: Magnitude shift detected (ratio={ratio:.2f}, allowed=[{1/R:.2f}, {R:.2f}])',
                details={'current_mean': current_mean, 'hist_mean': hist_mean, 'ratio': ratio, 'R': R}
            )
        
        return GuardRailResult(
            passed=True,
            violation=GuardRailViolation.NONE,
            severity='Normal',
            reason='GR-M1: Magnitude consistent',
            details={'current_mean': current_mean, 'hist_mean': hist_mean, 'ratio': ratio}
        )
    
    def _check_gr_s1(self, current_values: List[float], history_values: List[float]) -> GuardRailResult:
        """GR-S1: Support interval overlap check
        
        range(current) ∩ range(history) ≠ ∅
        """
        if not self.config.require_overlap:
            return GuardRailResult(
                passed=True,
                violation=GuardRailViolation.NONE,
                severity='Normal',
                reason='GR-S1: Overlap check disabled',
                details={}
            )
        
        curr_min, curr_max = min(current_values), max(current_values)
        hist_min, hist_max = min(history_values), max(history_values)
        
        # Check overlap: [a, b] ∩ [c, d] ≠ ∅ iff max(a,c) <= min(b,d)
        has_overlap = max(curr_min, hist_min) <= min(curr_max, hist_max)
        
        if not has_overlap:
            return GuardRailResult(
                passed=False,
                violation=GuardRailViolation.GR_S1_NO_OVERLAP,
                severity='HardRegression',
                reason=f'GR-S1: No range overlap (current=[{curr_min:.4f}, {curr_max:.4f}], history=[{hist_min:.4f}, {hist_max:.4f}])',
                details={
                    'current_range': [curr_min, curr_max],
                    'history_range': [hist_min, hist_max],
                    'has_overlap': False
                }
            )
        
        # Calculate overlap ratio
        overlap_start = max(curr_min, hist_min)
        overlap_end = min(curr_max, hist_max)
        overlap_size = overlap_end - overlap_start
        
        curr_range = curr_max - curr_min
        hist_range = hist_max - hist_min
        
        # Overlap ratio relative to smaller range
        if min(curr_range, hist_range) > 0:
            overlap_ratio = overlap_size / min(curr_range, hist_range)
        else:
            overlap_ratio = 1.0 if overlap_size >= 0 else 0.0
        
        return GuardRailResult(
            passed=True,
            violation=GuardRailViolation.NONE,
            severity='Normal',
            reason='GR-S1: Ranges overlap',
            details={
                'current_range': [curr_min, curr_max],
                'history_range': [hist_min, hist_max],
                'has_overlap': True,
                'overlap_ratio': overlap_ratio
            }
        )
    
    def _check_gr_s2(self, current_values: List[float], history_values: List[float], 
                     hist_mean: float) -> GuardRailResult:
        """GR-S2: Extreme value jump detection
        
        |max(current) − max(history)| > Δ_max
        """
        curr_max = max(current_values)
        curr_min = min(current_values)
        hist_max = max(history_values)
        hist_min = min(history_values)
        
        max_delta = abs(curr_max - hist_max)
        min_delta = abs(curr_min - hist_min)
        
        # Use ratio-based threshold
        abs_hist_mean = abs(hist_mean) if hist_mean != 0 else 1.0
        max_ratio = max_delta / abs_hist_mean if abs_hist_mean > 0.01 else 0
        min_ratio = min_delta / abs_hist_mean if abs_hist_mean > 0.01 else 0
        
        threshold = self.config.max_delta_ratio
        
        # Check if either extreme jumped significantly
        violation = False
        reason_parts = []
        
        if max_ratio > threshold:
            violation = True
            reason_parts.append(f'max jump ratio={max_ratio:.2f}')
        
        if min_ratio > threshold:
            violation = True
            reason_parts.append(f'min jump ratio={min_ratio:.2f}')
        
        if self.config.max_delta_absolute is not None:
            if max_delta > self.config.max_delta_absolute:
                violation = True
                reason_parts.append(f'max delta={max_delta:.4f}')
            if min_delta > self.config.max_delta_absolute:
                violation = True
                reason_parts.append(f'min delta={min_delta:.4f}')
        
        if violation:
            return GuardRailResult(
                passed=False,
                violation=GuardRailViolation.GR_S2_EXTREME_JUMP,
                severity='Regression',  # Not HardRegression, could be outlier
                reason=f'GR-S2: Extreme value jump ({", ".join(reason_parts)})',
                details={
                    'current_max': curr_max, 'history_max': hist_max, 'max_delta': max_delta,
                    'current_min': curr_min, 'history_min': hist_min, 'min_delta': min_delta,
                    'max_ratio': max_ratio, 'min_ratio': min_ratio
                }
            )
        
        return GuardRailResult(
            passed=True,
            violation=GuardRailViolation.NONE,
            severity='Normal',
            reason='GR-S2: Extremes within bounds',
            details={
                'current_max': curr_max, 'history_max': hist_max,
                'current_min': curr_min, 'history_min': hist_min
            }
        )
    
    def _check_gr_s3(self, current_mean: float, current_std: float,
                     hist_mean: float, hist_std: float) -> GuardRailResult:
        """GR-S3: Sigma-to-mean ratio validity
        
        σ / |μ| < ε indicates σ is below measurement resolution
        """
        epsilon = self.config.sigma_mean_epsilon
        
        details = {
            'current_cv': current_std / abs(current_mean) if abs(current_mean) > epsilon else None,
            'history_cv': hist_std / abs(hist_mean) if abs(hist_mean) > epsilon else None,
            'sigma_valid': True,
            'reason': ''
        }
        
        # Check current
        if abs(current_mean) > epsilon:
            current_cv = current_std / abs(current_mean)
            if current_cv < epsilon:
                details['sigma_valid'] = False
                details['reason'] = f'Current σ/μ={current_cv:.6f} < ε={epsilon}'
        
        # Check history  
        if abs(hist_mean) > epsilon:
            hist_cv = hist_std / abs(hist_mean)
            if hist_cv < epsilon:
                details['sigma_valid'] = False
                details['reason'] = f'History σ/μ={hist_cv:.6f} < ε={epsilon}'
        
        # GR-S3 doesn't block, just warns
        return GuardRailResult(
            passed=True,  # Always passes, but provides info
            violation=GuardRailViolation.GR_S3_SIGMA_INVALID if not details['sigma_valid'] else GuardRailViolation.NONE,
            severity='Normal',
            reason=f'GR-S3: {"Sigma unreliable for SPC" if not details["sigma_valid"] else "Sigma valid"}',
            details=details
        )


def integrate_guard_rails_with_detection(
    current_values: List[float],
    history_values: List[float],
    hist_mean: float,
    hist_std: float,
    base_severity: str,
    base_reason: str,
    config: Optional[GuardRailConfig] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """Integrate guard rails check with existing detection result
    
    Returns:
        (final_severity, final_reason, guard_rail_details)
    """
    guard_rails = GuardRails(config)
    gr_result = guard_rails.check_all(current_values, history_values, hist_mean, hist_std)
    
    if not gr_result.passed:
        # Guard rail violation overrides base detection
        if gr_result.severity == 'HardRegression':
            return 'Regression', f'[HARD] {gr_result.reason}', gr_result.details
        elif gr_result.severity == 'Regression':
            # If base was Normal, upgrade to Suspicious
            if base_severity == 'Normal':
                return 'Suspicious', f'{base_reason} | {gr_result.reason}', gr_result.details
            else:
                return base_severity, f'{base_reason} | {gr_result.reason}', gr_result.details
    
    return base_severity, base_reason, gr_result.details


# Example usage and testing
if __name__ == '__main__':
    # Test cases
    print("Guard Rails Test Cases")
    print("=" * 60)
    
    gr = GuardRails()
    
    # Test GR-M1: Magnitude shift
    print("\n1. GR-M1: Magnitude Consistency")
    result = gr._check_gr_m1(current_mean=100, hist_mean=1)  # 100x jump
    print(f"   100 vs 1: {result.severity} - {result.reason}")
    
    result = gr._check_gr_m1(current_mean=5, hist_mean=10)  # 0.5x, within range
    print(f"   5 vs 10: {result.severity} - {result.reason}")
    
    # Test GR-M1: Zero-inflated data (SCOUT_C_NR_1003a case)
    print("\n1b. GR-M1: Zero-inflated Data")
    # History has 75% zeros -> current=0 should be Normal
    result = gr._check_gr_m1(current_mean=0.0, hist_mean=0.240375, 
                              history_values=[0.0, 0.9615, 0.0, 0.0])
    print(f"   Zero-inflated (75% zeros): {result.severity} - {result.reason}")
    
    # History has only 25% zeros -> current=0 should be HardRegression
    result = gr._check_gr_m1(current_mean=0.0, hist_mean=0.5,
                              history_values=[0.3, 0.5, 0.7, 0.0])
    print(f"   Not zero-inflated (25% zeros): {result.severity} - {result.reason}")
    
    # Test GR-S1: No overlap
    print("\n2. GR-S1: Range Overlap")
    result = gr._check_gr_s1([100, 110, 120], [10, 20, 30])  # No overlap
    print(f"   [100-120] vs [10-30]: {result.severity} - {result.reason}")
    
    result = gr._check_gr_s1([25, 35, 45], [10, 20, 30])  # Overlap
    print(f"   [25-45] vs [10-30]: {result.severity} - {result.reason}")
    
    # Test GR-S2: Extreme jump
    print("\n3. GR-S2: Extreme Value Jump")
    result = gr._check_gr_s2([10, 15, 100], [10, 12, 14], hist_mean=12)  # Big max jump
    print(f"   max 100 vs 14 (mean=12): {result.severity} - {result.reason}")
    
    # Test GR-S3: Sigma validity
    print("\n4. GR-S3: Sigma Validity")
    result = gr._check_gr_s3(current_mean=1000, current_std=0.0001, 
                             hist_mean=1000, hist_std=0.0001)  # Very small CV
    print(f"   σ=0.0001, μ=1000: {result.reason}")
    print(f"   Details: {result.details}")
