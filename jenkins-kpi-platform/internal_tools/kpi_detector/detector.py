# -*- coding: utf-8 -*-
"""
KPI Anomaly Detector - Main Detection Module
Integrates consistency check (CV analysis) and t-test comparison
Enhanced with type-based anomaly detection (ivy0126)
Enhanced with alternative detection methods (ivy0202): IQR, Poisson, Relative change
"""

import pandas as pd
import numpy as np
import re
import json
from html import escape
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from scipy import stats

from .config import (PATHS, COLORS, DEFAULT_CV_THRESHOLD, DEFAULT_P_VALUE_THRESHOLD,
                     HISTORY_FILENAME, SCOUT_HISTORY_FILENAME)
from .utils import classify_code, parse_raw_data, calculate_cv, calculate_trimmed_cv
from .shewhart import calculate_severity_from_history
from .excel_report import ExcelReportGenerator
from .html_report import HTMLReportGenerator
from .kpi_types import (get_classifier, get_type_based_detector, get_strategy_based_detector,
                        KPIType, DetectionStrategy)
from .guard_rails import (GuardRails, GuardRailConfig, integrate_guard_rails_with_detection)


class DetectorExecutionError(ValueError):
    """Raised when detector input or history data is not analyzable."""


class KPIAnomalyDetector:
    """KPI Anomaly Detector - Integrates consistency and t-test analysis"""
    _release_pattern = re.compile(r'(?<!\d)(\d{2}R\d)(?!\d)', re.IGNORECASE)
    _environment_pattern = re.compile(r'^(T\d{3,4})(?:\b|[._])', re.IGNORECASE)
    _data_column_pattern = re.compile(r'(^|[._])(T\d{3,4})(?=$|[._])', re.IGNORECASE)
    _ue_token_pattern = re.compile(r'^\d+UEs?$', re.IGNORECASE)
    _csv_token_pattern = re.compile(r'^\d+csv[\w.-]*$', re.IGNORECASE)
    _invalid_filename_token_pattern = re.compile(r'[^A-Za-z0-9._-]+')
    _consistency_columns = [
        'Code', 'KPI Name', 'Type', 'Mean', 'Std', 'CV(%)', 'Consistency',
        'DataCount', 'Trimmed_Mean', 'Trimmed_Std', 'Trimmed_CV(%)',
        'Trimmed_Consistency', 'RawData'
    ]
    
    def __init__(
        self,
        current_file,
        cv_threshold=DEFAULT_CV_THRESHOLD,
        p_value_threshold=DEFAULT_P_VALUE_THRESHOLD,
        *,
        sheet_name: Optional[str] = None,
        history_sheet_name: Optional[str] = None,
        history_filename: Optional[str] = None,
        report_suffix: Optional[str] = None,
        allow_scout_summary: bool = True,
    ):
        """Initialize detector
        
        Args:
            current_file: Path to Excel file to analyze
            cv_threshold: CV threshold percentage (default 5%)
            p_value_threshold: P-value threshold for t-test (default 0.05)
        """
        self.current_file = Path(current_file)
        self.cv_threshold = cv_threshold
        self.p_value_threshold = p_value_threshold
        self.sheet_name = str(sheet_name).strip() if sheet_name not in (None, '') else None
        self.history_sheet_name = str(history_sheet_name or self.sheet_name or '').strip() or None
        self.report_suffix = self._sanitize_report_suffix(report_suffix or self.sheet_name)
        self.allow_scout_summary = allow_scout_summary
        self.portal_current_record: Optional[dict[str, Any]] = None
        self.report_outputs: dict[str, Any] = {}
        self._all_history_records: list[dict[str, Any]] = []
        
        self.current_df = None
        self.data_cols = []
        self.analysis_results = {}
        
        # History records - stored in reports directory
        self.scout_mode = self._is_scout_file(self.current_file.name)
        resolved_history_filename = history_filename or (SCOUT_HISTORY_FILENAME if self.scout_mode else HISTORY_FILENAME)
        self.history_file_path = PATHS['reports'] / resolved_history_filename
        self.history_records = []
        self.previous_record = None
        self.is_base_file = False
        
        # Report output directory
        self.reports_dir = PATHS['reports']
        
        # Deduplication info
        self.dedup_info = {'total_dropped': 0, 'details': []}
        
        # Current file context used for validation and history matching
        self.current_context = self._extract_filename_context(self.current_file.name)
        if not self.current_context['matched']:
            raise ValueError(self._filename_validation_message(self.current_file.name))
        self.current_context['sheet_name'] = self.history_sheet_name
        if self.history_sheet_name and self.current_context.get('environment') and self.current_context.get('scenario'):
            self.current_context['history_key'] = (
                f"{self.current_context['environment']}::{self.current_context['scenario']}::{self.history_sheet_name}"
            )
        self.current_history_group = self._history_group(self.current_context)
        
        # Type-based detection (ivy0126)
        self.kpi_classifier = get_classifier()
        self.type_based_detector = get_type_based_detector()
        
        # Guard Rails detection (ivy0127)
        self.guard_rails = GuardRails()
        
        # Strategy-based detection (ivy0202) - configured via Excel
        self.strategy_detector = get_strategy_based_detector()

    @classmethod
    def _sanitize_report_suffix(cls, value: Optional[str]) -> Optional[str]:
        text = str(value or '').strip()
        if not text:
            return None
        cleaned = cls._invalid_filename_token_pattern.sub('_', text).strip('._-')
        return cleaned or None

    @staticmethod
    def _is_scout_file(filename: str) -> bool:
        return Path(str(filename or '')).stem.lower().endswith('_scout')

    def _workbook_sheet_names(self) -> list[str]:
        try:
            workbook = pd.ExcelFile(self.current_file)
        except Exception:
            return []
        return [str(name).strip() for name in workbook.sheet_names if str(name).strip()]

    def _report_basename(self) -> str:
        if self.report_suffix:
            return f'{self.current_file.stem}_{self.report_suffix}'
        return self.current_file.stem

    def _sheet_history_token(self, record: dict[str, Any]) -> str:
        return str(record.get('sheet_name') or '').strip()
    
    def _filename_validation_message(self, filename):
        return (
            f"Invalid filename: {filename}. Expected format Date_Build_Env_Scenario_otherinfo.xlsx, "
            f"for example exec20260325T120349_SBTS26R3.ENB.9999.260319.000005_T813.SCF.T813.gNB.25R3.20260224_7UE_DL_Burst_1csv.xlsx"
        )

    def _history_group(self, context):
        environment = str(context.get('environment') or '').strip().upper()
        scenario = str(context.get('scenario') or '').strip()
        sheet_name = str(context.get('sheet_name') or '').strip()
        if not environment or not scenario:
            return None
        return (environment, scenario, sheet_name)

    def _extract_filename_context(self, filename):
        raw_name = Path(str(filename or '')).name
        stem = Path(raw_name).stem
        tokens = [token for token in stem.split('_') if token]

        if len(tokens) < 5:
            return {
                'date': None,
                'release': None,
                'build': None,
                'environment': None,
                'scenario': None,
                'otherinfo': None,
                'history_key': None,
                'matched': False,
            }

        date_token = tokens[0]

        environment = None
        env_index = -1
        for index in range(1, len(tokens)):
            environment_match = self._environment_pattern.match(tokens[index])
            if environment_match:
                environment = environment_match.group(1).upper()
                env_index = index
                break

        if env_index <= 1:
            return {
                'date': date_token,
                'release': None,
                'build': None,
                'environment': environment,
                'scenario': None,
                'otherinfo': None,
                'history_key': None,
                'matched': False,
            }

        build = '_'.join(tokens[1:env_index]) if env_index > 1 else None

        csv_index = -1
        for index in range(env_index + 1, len(tokens)):
            if self._csv_token_pattern.match(tokens[index]):
                csv_index = index
                break

        if csv_index < 0:
            return {
                'date': date_token,
                'release': None,
                'build': build,
                'environment': environment,
                'scenario': None,
                'otherinfo': None,
                'history_key': None,
                'matched': False,
            }

        scenario_start = None
        for index in range(env_index + 1, csv_index):
            if self._ue_token_pattern.match(tokens[index]):
                scenario_start = index
                break

        if scenario_start is None:
            scenario_start = env_index + 1 if env_index + 1 < csv_index else None

        scenario = None
        if scenario_start is not None and scenario_start < csv_index:
            scenario = '_'.join(tokens[scenario_start:csv_index])

        otherinfo = '_'.join(tokens[csv_index:]) if csv_index < len(tokens) else None
        release_match = self._release_pattern.search(build or '')
        release = release_match.group(1).upper() if release_match else None
        history_key = f'{environment}::{scenario}' if environment and scenario else None

        return {
            'date': date_token,
            'release': release,
            'build': build,
            'environment': environment,
            'scenario': scenario,
            'otherinfo': otherinfo,
            'history_key': history_key,
            'matched': bool(date_token and build and environment and scenario and otherinfo),
        }

    def _is_same_history_group(self, record):
        if self.current_history_group is None:
            return False

        record_environment = str(record.get('environment') or '').strip().upper()
        record_scenario = str(record.get('scenario') or '').strip()
        record_sheet_name = self._sheet_history_token(record)
        if not record_environment or not record_scenario:
            record_context = self._extract_filename_context(record.get('filename', ''))
            record_environment = str(record_context.get('environment') or '').strip().upper()
            record_scenario = str(record_context.get('scenario') or '').strip()
            if not record_sheet_name:
                record_sheet_name = str(record_context.get('sheet_name') or '').strip()

        if not record_environment or not record_scenario:
            return False

        return (record_environment, record_scenario, record_sheet_name) == self.current_history_group

    def _record_build(self, record):
        record_build = str(record.get('build') or '').strip()
        if record_build:
            return record_build
        record_context = self._extract_filename_context(record.get('filename', ''))
        return str(record_context.get('build') or '').strip()

    def _extract_data_column_prefix(self, column_name):
        match = self._data_column_pattern.search(str(column_name or '').strip())
        if not match:
            return None
        return match.group(2).upper()

    def _is_data_column(self, column_name):
        return self._extract_data_column_prefix(column_name) is not None

    def _fail_analysis(self, message):
        print(f"Error: {message}")
        raise DetectorExecutionError(message)
    
    def load_history(self):
        """Load history records"""
        if self.history_file_path.exists():
            try:
                with open(self.history_file_path, 'r', encoding='utf-8') as f:
                    all_records = json.load(f)

                current_filename = self.current_file.name
                current_build = str(self.current_context.get('build') or '').strip()
                same_group_records = [
                    r for r in all_records
                    if self._is_same_history_group(r)
                    and r.get('filename', '') != current_filename
                ]

                excluded_same_build_count = 0
                if self.is_base_file or not current_build:
                    self.history_records = same_group_records
                else:
                    self.history_records = []
                    for record in same_group_records:
                        if self._record_build(record) == current_build:
                            excluded_same_build_count += 1
                            continue
                        self.history_records.append(record)
                
                print(f"History loaded: {len(all_records)} total records")
                
                if self.current_history_group:
                    group_text = f'Env={self.current_history_group[0]}, Scenario={self.current_history_group[1]}'
                    if self.current_history_group[2]:
                        group_text += f', Sheet={self.current_history_group[2]}'
                    print(f"  Current history group: {group_text}")
                    print(f"  Base file mode: {'YES' if self.is_base_file else 'NO'}")
                    if not self.is_base_file and current_build:
                        print(f"  Excluded same-build history records: {excluded_same_build_count} (Build={current_build})")
                    print(f"  Matching history records (excluding current): {len(self.history_records)}")
                
                # Get most recent same Env + Scenario record for comparison
                if self.history_records:
                    self.previous_record = self.history_records[-1]
                    print(f"  Previous matching analysis: {self.previous_record.get('filename', 'N/A')} @ {self.previous_record.get('timestamp', 'N/A')}")
                else:
                    print(f"  No matching Env + Scenario history")
                
                # Keep all records for saving (don't lose other scenario data)
                self._all_history_records = all_records
                
            except Exception as e:
                print(f"Warning: Failed to load history - {e}")
                self.history_records = []
                self._all_history_records = []
        else:
            print("First run, no history records")
            self.history_records = []
            self._all_history_records = []
    
    def save_history(self, current_result):
        """Save current result to history
        
        If current file already exists in history, update it instead of appending.
        """
        all_records = getattr(self, '_all_history_records', [])
        current_filename = current_result.get('filename', '')
        current_sheet_name = str(current_result.get('sheet_name') or '').strip()
        
        # Remove existing record for current file (if any)
        all_records = [
            r for r in all_records
            if not (
                r.get('filename', '') == current_filename
                and str(r.get('sheet_name') or '').strip() == current_sheet_name
            )
        ]
        
        # Append current result
        all_records.append(current_result)
        
        try:
            with open(self.history_file_path, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, ensure_ascii=False, indent=2)
            
            same_scenario_count = sum(
                1 for r in all_records 
                if self._is_same_history_group(r)
            )
            print(f"History updated (total {len(all_records)}, matching Env + Scenario {same_scenario_count})")
        except Exception as e:
            print(f"Warning: Failed to save history - {e}")
    
    def load_data(self):
        """Load data from Excel file"""
        print(f"\nLoading current file: {self.current_file.name}")
        if self.sheet_name:
            print(f"  Reading sheet: {self.sheet_name}")
            self.current_df = pd.read_excel(self.current_file, sheet_name=self.sheet_name)
        else:
            self.current_df = pd.read_excel(self.current_file)
        print(f"  Original data shape: {self.current_df.shape}")
        
        # Find data columns using any Txxx prefix such as T080.20260403_010203.
        self.data_cols = [
            col for col in self.current_df.columns
            if self._is_data_column(col)
        ]
        detected_prefixes = sorted({
            prefix for prefix in (self._extract_data_column_prefix(col) for col in self.data_cols)
            if prefix
        })
        prefix_summary = ', '.join(detected_prefixes) if detected_prefixes else 'none'
        print(f"  Found {len(self.data_cols)} data columns (prefixes: {prefix_summary})")
        
        # Deduplicate data
        self.deduplicate_data()
        
        # Load history
        self.load_history()
        
        # Auto-detect and register new codes not in kpi_config_unified.xlsx (ivy0210)
        self._register_unknown_codes()

    def _empty_consistency_df(self):
        return pd.DataFrame(columns=self._consistency_columns)

    def _normalize_consistency_df(self, df):
        if df is None or not isinstance(df, pd.DataFrame):
            return self._empty_consistency_df()

        normalized = df.copy()
        for column in self._consistency_columns:
            if column not in normalized.columns:
                normalized[column] = np.nan if column in {'Mean', 'Std', 'CV(%)', 'DataCount', 'Trimmed_Mean', 'Trimmed_Std', 'Trimmed_CV(%)'} else ''

        if 'Type' in normalized.columns and 'Code' in normalized.columns:
            missing_type_mask = normalized['Type'].isna() | (normalized['Type'].astype(str).str.strip() == '')
            if missing_type_mask.any():
                normalized.loc[missing_type_mask, 'Type'] = normalized.loc[missing_type_mask, 'Code'].apply(classify_code)

        return normalized[self._consistency_columns]
    
    def deduplicate_data(self):
        """Remove duplicate Code data
        
        Rule: For codes formatted as NR_Ax or SCOUT_NR_Ax (A is 2-4 digit number, x is letter),
        if NR_A part is same but x differs, keep the one with largest x, remove others.
        Example: NR_5089a, NR_5089b, NR_5089e -> keep NR_5089e
        """
        if self.current_df is None or self.current_df.empty:
            return
        
        print("\n========== Data Deduplication ==========")
        
        # Pattern: NR_number+letter or SCOUT_NR_number+letter
        pattern = r'((?:SCOUT_)?NR_\d{2,4})([a-zA-Z])'
        
        # Find all matching codes and their groups
        code_groups = {}  # {base: [(code, suffix, idx), ...]}
        
        for idx, row in self.current_df.iterrows():
            code = str(row.get('Code', '')).strip() if pd.notna(row.get('Code')) else ''
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                base = match.group(1).upper()
                suffix = match.group(2).upper()
                if base not in code_groups:
                    code_groups[base] = []
                code_groups[base].append((code, suffix, idx))
        
        # Find rows to drop
        rows_to_drop = []
        dedup_details = []
        
        for base, items in code_groups.items():
            if len(items) > 1:
                # Sort by suffix (alphabetical), keep largest
                items.sort(key=lambda x: x[1], reverse=True)
                kept = items[0]
                dropped = items[1:]
                dedup_details.append({
                    'kept': kept[0],
                    'dropped': [d[0] for d in dropped]
                })
                for _, _, idx in dropped:
                    rows_to_drop.append(idx)
        
        if rows_to_drop:
            print(f"  Found {len(dedup_details)} duplicate groups, dropping {len(rows_to_drop)} rows")
            for detail in dedup_details:
                print(f"    Keep: {detail['kept']}, Drop: {detail['dropped']}")
            
            self.current_df = self.current_df.drop(rows_to_drop).reset_index(drop=True)
            print(f"  Data shape after dedup: {self.current_df.shape}")
        else:
            print("  No duplicates found")
        
        self.dedup_info = {
            'total_dropped': len(rows_to_drop),
            'details': dedup_details
        }
    
    def _register_unknown_codes(self):
        """Auto-detect codes not in kpi_config_unified.xlsx and register them (ivy0210)
        
        Searches XML files for the code info, then appends to the unified xlsx.
        """
        if self.current_df is None or self.current_df.empty:
            return
        
        # Collect all codes from current data
        all_codes = []
        if 'Code' in self.current_df.columns:
            for _, row in self.current_df.iterrows():
                code = str(row.get('Code', '')).strip() if pd.notna(row.get('Code')) else ''
                if code:
                    all_codes.append(code)
        
        if not all_codes:
            return
        
        # Filter to codes not in classifier
        unknown_codes = []
        for code in all_codes:
            cls = self.kpi_classifier.get_classification(code)
            if cls is None:
                unknown_codes.append(code)
        
        if unknown_codes:
            print(f"\n========== Auto-Register Unknown Codes (ivy0210) ==========")
            print(f"  Found {len(unknown_codes)} codes not in kpi_config_unified.xlsx")
            new_codes = self.kpi_classifier.register_new_codes(unknown_codes, default_strategy='IQR')
            if new_codes:
                print(f"  Successfully registered {len(new_codes)} new codes")

    def analyze_consistency(self):
        """Analyze consistency (CV analysis)"""
        print("\n========== Consistency Analysis ==========")
        
        if not self.data_cols:
            available_columns = ', '.join(str(col) for col in self.current_df.columns[:20])
            self.analysis_results['consistency'] = self._empty_consistency_df()
            self._fail_analysis(
                'No valid KPI data columns found in input report. '
                'Expected at least one column containing a Txxx or Txxxx prefix, '
                f'for example T813.20260407_123456. Available columns: {available_columns or "none"}'
            )
        
        data_cols = self.current_df[self.data_cols]
        
        results = []
        for idx, row in self.current_df.iterrows():
            code = str(row.get('Code', '')).strip() if pd.notna(row.get('Code')) else ''
            kpi_name = str(row.get('KPI Name', '')).strip() if 'KPI Name' in row.index and pd.notna(row.get('KPI Name')) else ''
            
            row_data = data_cols.iloc[idx]
            non_null = row_data.dropna()
            
            # Initialize Trimmed values
            trimmed_mean = np.nan
            trimmed_std = np.nan
            trimmed_cv = np.nan
            trimmed_status = ''
            use_trimmed = False
            
            if len(non_null) == 0:
                status = 'NULL'
                cv = np.nan
                mean_val = np.nan
                std_val = np.nan
            elif len(non_null) < len(self.data_cols):
                # Partial null values - always label as partial NULL regardless of
                # the remaining values.  A previous special case forced status to
                # 'Consistent' when the only surviving value was 0 or 100, but this
                # is wrong: missing columns means incomplete data, which must be
                # labelled partial NULL so the "Exclude Partial NULL (P)" filter works.
                status = 'partial NULL'
                cv = np.nan
                mean_val = non_null.mean()
                std_val = non_null.std(ddof=0)
            else:
                mean_val = non_null.mean()
                std_val = non_null.std(ddof=0)
                
                if non_null.nunique() == 1:
                    status = 'Consistent'
                    cv = 0
                elif abs(mean_val) < 0.001:
                    # Very small values, use absolute difference
                    if (non_null.max() - non_null.min()) < 0.001:
                        status = 'Consistent'
                        cv = 0
                    else:
                        status = 'Inconsistent'
                        cv = np.nan
                else:
                    cv = (std_val / mean_val) * 100
                    status = 'Consistent' if cv < self.cv_threshold else 'Inconsistent'
                
                # If data >= 5, calculate trimmed results (remove min and max)
                if len(non_null) >= 5:
                    use_trimmed = True
                    sorted_vals = non_null.sort_values()
                    trimmed_vals = sorted_vals.iloc[1:-1]
                    trimmed_mean = trimmed_vals.mean()
                    trimmed_std = trimmed_vals.std(ddof=0)
                    
                    if trimmed_vals.nunique() == 1:
                        trimmed_cv = 0
                        trimmed_status = 'Consistent'
                    elif abs(trimmed_mean) < 0.001:
                        if (trimmed_vals.max() - trimmed_vals.min()) < 0.001:
                            trimmed_cv = 0
                            trimmed_status = 'Consistent'
                        else:
                            trimmed_cv = np.nan
                            trimmed_status = 'Inconsistent'
                    else:
                        trimmed_cv = (trimmed_std / trimmed_mean) * 100
                        trimmed_status = 'Consistent' if trimmed_cv < self.cv_threshold else 'Inconsistent'
            
            results.append({
                'Code': code,
                'KPI Name': kpi_name,
                'Type': classify_code(code),
                'Mean': round(mean_val, 2) if pd.notna(mean_val) else np.nan,
                'Std': round(std_val, 2) if pd.notna(std_val) else np.nan,
                'CV(%)': round(cv, 2) if pd.notna(cv) else np.nan,
                'Consistency': status,
                'DataCount': len(non_null),
                'Trimmed_Mean': round(trimmed_mean, 2) if use_trimmed and pd.notna(trimmed_mean) else np.nan,
                'Trimmed_Std': round(trimmed_std, 2) if use_trimmed and pd.notna(trimmed_std) else np.nan,
                'Trimmed_CV(%)': round(trimmed_cv, 2) if use_trimmed and pd.notna(trimmed_cv) else np.nan,
                'Trimmed_Consistency': trimmed_status if use_trimmed else '',
                'RawData': ','.join([str(v) for v in non_null.tolist()]) if len(non_null) > 0 else ''
            })
        
        self.analysis_results['consistency'] = self._normalize_consistency_df(pd.DataFrame(results, columns=self._consistency_columns))
        
        # Statistics
        consistency_df = self.analysis_results['consistency']
        print(f"  Consistent: {(consistency_df['Consistency'] == 'Consistent').sum()}")
        print(f"  Inconsistent: {(consistency_df['Consistency'] == 'Inconsistent').sum()}")
        print(f"  partial NULL: {(consistency_df['Consistency'] == 'partial NULL').sum()}")
        print(f"  NULL: {(consistency_df['Consistency'] == 'NULL').sum()}")
    
    def analyze_ttest_with_history(self):
        """Analyze t-test (compare with history)"""
        if not self.previous_record:
            print("\nNo history records, skipping t-test analysis")
            return
        
        print("\n========== T-Test Analysis (vs History) ==========")
        print(f"  Comparing with: {self.previous_record.get('filename', 'N/A')}")
        
        prev_data = self.previous_record.get('kpi_data', {})
        
        if not prev_data:
            history_filename = self.previous_record.get('filename', 'N/A')
            self._fail_analysis(f'No KPI data in history record: {history_filename}')
        
        results = []
        consistency_df = self.analysis_results.get('consistency', pd.DataFrame())
        
        for _, row in consistency_df.iterrows():
            code = row['Code']
            if not code or code not in prev_data:
                continue
            
            # Current data
            current_raw = row['RawData']
            if not current_raw:
                continue
            current_values = [float(x) for x in current_raw.split(',') if x.strip()]
            
            # History data
            prev_raw = prev_data[code].get('raw_data', '')
            if not prev_raw:
                continue
            prev_values = [float(x) for x in prev_raw.split(',') if x.strip()]
            
            # Perform t-test
            if len(current_values) >= 2 and len(prev_values) >= 2:
                current_mean = np.mean(current_values)
                prev_mean = np.mean(prev_values)
                
                # Check for zero variance
                if np.std(current_values) == 0 and np.std(prev_values) == 0:
                    if current_mean == prev_mean:
                        p_value = 1.0
                        t_stat = 0
                    else:
                        p_value = 0.0
                        t_stat = float('inf')
                else:
                    try:
                        t_stat, p_value = stats.ttest_ind(current_values, prev_values, equal_var=False)
                    except:
                        t_stat = np.nan
                        p_value = np.nan
                
                diff = current_mean - prev_mean
                diff_pct = (diff / prev_mean * 100) if prev_mean != 0 else (np.nan if diff == 0 else float('inf'))
                
                # Determine result
                if pd.notna(p_value) and p_value < self.p_value_threshold:
                    ttest_result = 'Fail'
                else:
                    ttest_result = 'Pass'
                
                results.append({
                    'Code': code,
                    'KPI Name': row['KPI Name'],
                    'Type': row['Type'],
                    'Current_Mean': round(current_mean, 2),
                    'History_Mean': round(prev_mean, 2),
                    'Diff': round(diff, 2),
                    'Diff(%)': round(diff_pct, 2) if np.isfinite(diff_pct) else np.nan,
                    'T_Stat': round(t_stat, 2) if np.isfinite(t_stat) else np.nan,
                    'P_Value': round(p_value, 4) if pd.notna(p_value) else np.nan,
                    'TTest_Result': ttest_result,
                    'Current_Data': current_raw,
                    'History_Data': prev_raw
                })
        
        self.analysis_results['ttest'] = pd.DataFrame(results)
        
        if len(results) > 0:
            ttest_df = self.analysis_results['ttest']
            print(f"  Compared KPIs: {len(ttest_df)}")
            print(f"  Pass: {(ttest_df['TTest_Result'] == 'Pass').sum()}")
            print(f"  Fail: {(ttest_df['TTest_Result'] == 'Fail').sum()}")
    
    def analyze_all_codes_with_history(self):
        """Analyze all codes based on historical data
        
        Severity judgment (primarily based on historical statistics, T-Test as reference):
        - Normal: Current mean within historical mean +/-2 sigma
        - Suspicious: Exceeds +/-2 sigma but not +/-3 sigma
        - Regression: Exceeds +/-3 sigma or trend deviation
        - NoHistory: Insufficient historical data (<2 records)
        """
        print("\n========== All Codes Analysis (History-based + Type-based) ==========")
        
        all_codes_analysis = []
        
        consistency_df = self.analysis_results.get('consistency', pd.DataFrame())
        ttest_df = self.analysis_results.get('ttest', pd.DataFrame())
        
        if consistency_df.empty:
            self._fail_analysis('No consistency analysis data. Input report has no analyzable KPI rows.')
        
        # Get history data
        prev_data = {}
        if self.previous_record:
            prev_data = self.previous_record.get('kpi_data', {})
        
        # Process all codes
        for _, row in consistency_df.iterrows():
            code = row['Code']
            if not code:
                continue
            
            # Basic info
            kpi_name = row['KPI Name']
            code_type = row['Type']
            cv_value = row['CV(%)']
            consistency = row['Consistency']
            raw_data = row['RawData']
            trimmed_consistency = row.get('Trimmed_Consistency', '')
            data_count = row.get('DataCount', 0)
            
            # Get T-Test result (as reference)
            ttest_result = 'N/A'
            p_value = np.nan
            diff_pct = np.nan
            if not ttest_df.empty:
                ttest_row = ttest_df[ttest_df['Code'] == code]
                if not ttest_row.empty:
                    ttest_result = ttest_row['TTest_Result'].iloc[0]
                    p_value = ttest_row['P_Value'].iloc[0]
                    diff_pct = ttest_row['Diff(%)'].iloc[0]
            
            # Get history data
            history_data = ''
            history_consistency = 'N/A'
            if code in prev_data:
                history_data = prev_data[code].get('raw_data', '')
                history_consistency = prev_data[code].get('consistency', 'N/A')
            
            # Parse current data
            current_values = []
            if raw_data:
                try:
                    current_values = [float(x) for x in raw_data.split(',') if x.strip()]
                except:
                    pass
            
            # Calculate severity based on history (standard method)
            hist_result = calculate_severity_from_history(code, current_values, self.history_records)
            
            # ========== Type-based detection (ivy0126) ==========
            # Get KPI classification info
            kpi_cls = self.kpi_classifier.get_classification(code)
            kpi_type_str = kpi_cls.kpi_type.value if kpi_cls else 'unknown'
            detection_strategy = self.kpi_classifier.get_detection_strategy(code).value
            custom_rule_applied = self.kpi_classifier.is_custom_rule_applied(code)
            units = kpi_cls.units if kpi_cls else ''
            # Use new methods that support SCOUT_NR_ → NR_ lookup
            related_counters = self.kpi_classifier.get_related_counters(code)
            related_kpis = self.kpi_classifier.get_related_kpis(code)  # For counters
            xml_level = kpi_cls.level if kpi_cls else ''
            formula = self.kpi_classifier.get_formula(code)
            
            # Apply type-based detection if we have history
            type_based_result = None
            type_based_severity = None
            if hist_result['hist_mean'] is not None and hist_result['hist_std'] is not None:
                type_based_result = self.type_based_detector.detect_anomaly(
                    code, current_values, 
                    hist_result['hist_mean'], hist_result['hist_std'],
                    self.history_records
                )
                type_based_severity = type_based_result.get('severity')
            
            # Final severity: use type-based for known types, standard for unknown
            # ivy0302: Also use type-based when strategy=ABS_THRESHOLD even if kpi_type is
            # unknown (code not in unified config).  ABS_THRESHOLD means "constant-type KPI":
            # magnitude/relative checks are authoritative; Shewhart Rule4 (consecutive same-
            # side of CL) is meaningless noise for essentially constant data and must NOT
            # escalate severity to Regression when the actual delta is sub-0.5%.
            _is_abs_threshold_strategy = (detection_strategy == 'ABS_THRESHOLD')
            if (kpi_type_str != 'unknown' or _is_abs_threshold_strategy) and type_based_result:
                severity = type_based_severity
                # Merge anomaly indices from type-based detection
                type_anomaly_indices = type_based_result.get('anomaly_indices', [])
                level_shift = type_based_result.get('level_shift_detected', False)
            else:
                severity = hist_result['severity']
                type_anomaly_indices = []
                level_shift = False
            
            # ========== Guard Rails Check (ivy0127) ==========
            # Apply Guard Rails if we have history data
            guard_rail_violations = []
            guard_rail_details = {}
            guard_rail_severity = ''  # ivy0129: track GR severity separately
            strategy_detection_method = ''  # ivy0202: track strategy-based detection method
            strategy_detection_result = None
            
            if hist_result['hist_mean'] is not None and hist_result['hist_std'] is not None:
                # Collect history values for Guard Rails check
                history_values = []
                for record in self.history_records:
                    kpi_data = record.get('kpi_data', {})
                    if code in kpi_data:
                        hist_raw_data = kpi_data[code].get('raw_data', '')
                        if hist_raw_data:
                            try:
                                vals = [float(x) for x in hist_raw_data.split(',') if x.strip()]
                                history_values.extend(vals)
                            except:
                                pass
                
                if current_values and history_values:
                    # ========== Strategy-Based Detection (ivy0203 refactored) ==========
                    # Get detection strategy from Excel configuration
                    strategy = self.kpi_classifier.get_detection_strategy(code)
                    strategy_detection_method = strategy.value
                    
                    # Apply strategy-based detection for non-STANDARD_SPC strategies
                    from .kpi_types import StrategyBasedDetector, DetectionStrategy, normalize_strategy
                    normalized_strategy = normalize_strategy(strategy)
                    
                    if StrategyBasedDetector.is_alternative_strategy(normalized_strategy):
                        strat_sev, strat_reason, strat_details = self.strategy_detector.detect(
                            normalized_strategy, current_values, history_values,
                            hist_result['hist_mean'], hist_result['hist_std']
                        )
                        if strat_sev:
                            strategy_detection_result = {
                                'severity': strat_sev,
                                'reason': strat_reason,
                                'details': strat_details
                            }
                            # ivy0203: Strategy result is PRIMARY when not STANDARD_SPC
                            # Override severity with strategy result (SPC only as reference)
                            severity = strat_sev
                    
                    # Guard Rails apply to ALL strategies as baseline check (ivy0203 pm)
                    # Guard Rails can upgrade severity regardless of strategy type
                    new_severity, guard_upgrade_reason, guard_rail_details = integrate_guard_rails_with_detection(
                        current_values=current_values,
                        history_values=history_values,
                        hist_mean=hist_result['hist_mean'],
                        hist_std=hist_result['hist_std'],
                        base_severity=severity,
                        base_reason=''
                    )
                    
                    # Update severity if upgraded by Guard Rails
                    if new_severity != severity:
                        severity = new_severity
                    
                    # Collect violations
                    if guard_upgrade_reason:
                        guard_rail_violations = [guard_upgrade_reason]
                        guard_rail_details['violation'] = guard_upgrade_reason
                        guard_rail_severity = new_severity
                    
                    # ========== Physical Floor Constraint for dB/dBm KPIs (ivy0204) ==========
                    # For physical_stable KPIs with dB/dBm units:
                    # - If absolute change < 1dB, cap severity at Suspicious (not Regression)
                    # - This prevents statistically significant but physically irrelevant changes
                    #   from being flagged as Regression
                    if kpi_type_str == 'physical_stable' and units and 'dB' in units:
                        current_mean = np.mean(current_values) if current_values else 0
                        abs_delta = abs(current_mean - hist_result['hist_mean'])
                        DB_FLOOR_THRESHOLD = 0.5  # 1dB physical significance threshold
                        
                        if abs_delta < DB_FLOOR_THRESHOLD and severity == 'Regression':
                            # Downgrade to Suspicious - change is statistically but not physically significant
                            severity = 'Suspicious'
                            guard_rail_details['physical_floor_applied'] = True
                            guard_rail_details['abs_delta_db'] = abs_delta
                            guard_rail_details['db_floor_threshold'] = DB_FLOOR_THRESHOLD
            
            # Get Shewhart chart data (always collected for reference/visualization)
            shewhart_data = hist_result.get('shewhart', {})
            shewhart_zone = shewhart_data.get('zone', '')
            shewhart_violations = shewhart_data.get('violations', [])
            control_limits = shewhart_data.get('control_limits', {})
            
            # Build analysis reasons (ivy0203 refactored)
            analysis_reasons = []
            
            # ivy0204: Add physical floor info for dB/dBm KPIs
            if guard_rail_details.get('physical_floor_applied'):
                abs_delta_db = guard_rail_details.get('abs_delta_db', 0)
                analysis_reasons.append(f"[dB Floor] Δ={abs_delta_db:.2f}dB < 1dB, capped at Suspicious")
            
            # ivy0203: Strategy detection result is PRIMARY (shown first)
            if strategy_detection_result and strategy_detection_result.get('reason'):
                analysis_reasons.append(f"[{strategy_detection_method}] {strategy_detection_result['reason']}")
            
            # Guard Rails (may be primary for SPC, or reference for other strategies)
            if guard_rail_violations:
                # For non-SPC strategies, GR reasons already have "(ref)" prefix
                analysis_reasons.append(guard_rail_violations[0])
            
            # Add type-based detection reasons (if applicable)
            if type_based_result and type_based_result.get('reasons'):
                analysis_reasons.extend(type_based_result['reasons'])
            
            # Add consistency info (as reference)
            if consistency == 'Inconsistent':
                if data_count >= 5 and trimmed_consistency == 'Consistent':
                    analysis_reasons.append('CV inconsistent, trimmed consistent')
                else:
                    analysis_reasons.append('CV inconsistent')
            elif consistency == 'partial NULL':
                analysis_reasons.append('Partial null values')
            
            # ivy0203: Add SPC/history reasons only for STANDARD_SPC strategy
            # For other strategies, SPC is reference only
            from .kpi_types import DetectionStrategy, normalize_strategy
            if normalize_strategy(self.kpi_classifier.get_detection_strategy(code)) == DetectionStrategy.STANDARD_SPC:
                if kpi_type_str == 'unknown' and hist_result['judgment_reasons']:
                    analysis_reasons.extend(hist_result['judgment_reasons'])
            else:
                # Add SPC info as reference for non-SPC strategies
                if shewhart_violations:
                    spc_ref = f"(SPC ref: {'; '.join(shewhart_violations[:2])})"
                    if spc_ref not in str(analysis_reasons):
                        analysis_reasons.append(spc_ref)
            
            # T-Test result as reference
            if ttest_result == 'Fail':
                analysis_reasons.append('T-Test Fail (ref)')
            
            all_codes_analysis.append({
                'Code': code,
                'KPI Name': kpi_name,
                'Type': code_type,
                'Severity': severity,
                'Reasons': '; '.join(analysis_reasons) if analysis_reasons else 'Normal',
                'CV(%)': cv_value,
                'Consistency': consistency,
                'Trimmed_Consistency': trimmed_consistency,
                'TTest_Result': ttest_result,
                'P_Value': p_value,
                'Diff(%)': diff_pct,
                'Z_Score': hist_result['z_score'],
                'Sigma_Level': hist_result['sigma_level'],
                'Anomaly_Count': hist_result['anomaly_count'],
                'Total_Points': len(current_values),
                'Anomaly_Ratio(%)': hist_result['anomaly_ratio'] * 100 if hist_result['anomaly_ratio'] else 0,
                'Trend': hist_result['trend_direction'] or '',
                'Hist_Mean': hist_result['hist_mean'],
                'Hist_Std': hist_result['hist_std'],
                'Current_Mean': hist_result['current_mean'],
                # Degenerate case fields
                'Is_Degenerate': hist_result.get('is_degenerate', False),
                'Degenerate_Type': hist_result.get('degenerate_type', ''),
                # Shewhart chart fields
                'SPC_Zone': shewhart_zone,
                'SPC_Violations': '; '.join(shewhart_violations) if shewhart_violations else '',
                'SPC_UCL': control_limits.get('UCL'),
                'SPC_LCL': control_limits.get('LCL'),
                'SPC_CL': control_limits.get('CL'),
                'Current_Data': raw_data,
                'History_Data': history_data,
                # Full Shewhart chart_data for HTML visualization
                '_shewhart_chart': shewhart_data.get('chart_data', {}),
                # Type-based detection fields (ivy0126)
                'KPI_Type': kpi_type_str,
                'Detection_Strategy': detection_strategy,
                'Custom_Rule_Applied': custom_rule_applied,
                'Units': units,
                'Related_Counters': ','.join(related_counters) if related_counters else '',
                'Related_KPIs': ','.join(related_kpis) if related_kpis else '',
                'Formula': formula,
                'XML_Level': xml_level,
                'Level_Shift': level_shift,
                'Type_Anomaly_Indices': type_anomaly_indices,
                # Guard Rails fields (ivy0127, ivy0129: fixed severity tracking)
                'Guard_Rail_Violations': '; '.join(guard_rail_violations) if guard_rail_violations else '',
                'Guard_Rail_Overall': guard_rail_severity if guard_rail_severity else '',
                # Strategy-based detection method fields (ivy0202)
                'Detection_Strategy': strategy_detection_method,
            })
        
        # Create DataFrame and sort
        all_codes_df = pd.DataFrame(all_codes_analysis)
        if not all_codes_df.empty:
            severity_order = {'Regression': 0, 'Suspicious': 1, 'NoHistory': 2, 'Normal': 3}
            all_codes_df['_severity_order'] = all_codes_df['Severity'].map(severity_order)
            all_codes_df = all_codes_df.sort_values(['_severity_order', 'Sigma_Level'], ascending=[True, False])
            all_codes_df = all_codes_df.drop(columns=['_severity_order'])
        
        self.analysis_results['all_codes'] = all_codes_df
        
        # Statistics
        print(f"  Total Codes: {len(all_codes_df)}")
        print(f"  Regression (Performance Degradation): {(all_codes_df['Severity'] == 'Regression').sum()}")
        print(f"  Suspicious: {(all_codes_df['Severity'] == 'Suspicious').sum()}")
        print(f"  Normal: {(all_codes_df['Severity'] == 'Normal').sum()}")
        print(f"  NoHistory: {(all_codes_df['Severity'] == 'NoHistory').sum()}")
        
        # Compatible with old suspicious interface
        suspicious_df = all_codes_df[all_codes_df['Severity'] != 'Normal'].copy()
        self.analysis_results['suspicious'] = suspicious_df
        
        print(f"\n  Codes requiring attention: {len(suspicious_df)}")
    
    def identify_suspicious_kpis(self):
        """Compatible with old interface, calls new analysis method"""
        self.analyze_all_codes_with_history()

    @staticmethod
    def _safe_round_portal_value(value: Any, decimals: int = 3) -> Any:
        if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
            return ''
        try:
            return round(float(value), decimals)
        except (TypeError, ValueError):
            return ''

    @staticmethod
    def _severity_change_flag(current_severity: str, previous_severity: Optional[str]) -> str:
        severity_rank = {'Normal': 0, 'NoHistory': 1, 'Suspicious': 2, 'Regression': 3}
        current_rank = severity_rank.get(str(current_severity or ''), -1)
        previous_rank = severity_rank.get(str(previous_severity or ''), -1)

        if not previous_severity:
            return 'NEW'
        if current_rank > previous_rank:
            return 'WORSENED'
        if current_rank < previous_rank:
            return 'IMPROVED'
        return 'UNCHANGED'

    def _build_portal_severity_tracking_rows(self) -> list[dict[str, Any]]:
        all_codes_df = self.analysis_results.get('all_codes', pd.DataFrame())
        if all_codes_df is None or all_codes_df.empty:
            return []

        previous_severity_map = {}
        if self.previous_record:
            previous_severity_map = self.previous_record.get('code_severity', {}) or {}

        rows: list[dict[str, Any]] = []
        non_normal_df = all_codes_df[all_codes_df['Severity'].isin(['Regression', 'Suspicious'])].copy()
        for _, row in non_normal_df.iterrows():
            code = str(row.get('Code', '') or '').strip()
            current_mean = row.get('Current_Mean')
            history_mean = row.get('Hist_Mean')
            relative_change = ''
            if (
                current_mean is not None and history_mean is not None
                and pd.notna(current_mean) and pd.notna(history_mean)
                and abs(history_mean) > 1e-10
            ):
                relative_change = self._safe_round_portal_value(((current_mean - history_mean) / abs(history_mean)) * 100)

            previous_severity = str(previous_severity_map.get(code, '') or '').strip()
            rows.append({
                'Code': code,
                'KPI Name': row.get('KPI Name', ''),
                'Severity': row.get('Severity', ''),
                'Relative Change(%)': relative_change,
                'Anomaly Count': int(row.get('Anomaly_Count', 0)) if pd.notna(row.get('Anomaly_Count', 0)) else 0,
                'Prev Severity': previous_severity or 'N/A',
                'Change Flag': self._severity_change_flag(str(row.get('Severity', '') or ''), previous_severity or None),
            })

        for code, previous_severity in previous_severity_map.items():
            if previous_severity not in {'Regression', 'Suspicious'}:
                continue
            current_rows = all_codes_df[all_codes_df['Code'] == code]
            if current_rows.empty:
                continue
            current_row = current_rows.iloc[0]
            if str(current_row.get('Severity', '') or '') != 'Normal':
                continue

            rows.append({
                'Code': code,
                'KPI Name': current_row.get('KPI Name', ''),
                'Severity': 'Normal',
                'Relative Change(%)': '',
                'Anomaly Count': int(current_row.get('Anomaly_Count', 0)) if pd.notna(current_row.get('Anomaly_Count', 0)) else 0,
                'Prev Severity': previous_severity,
                'Change Flag': 'IMPROVED',
            })

        return rows
    
    def build_current_record(self):
        """Build current result record for saving to history"""
        if self.portal_current_record is not None:
            return self.portal_current_record

        consistency_df = self._normalize_consistency_df(self.analysis_results.get('consistency'))
        suspicious_df = self.analysis_results.get('suspicious', pd.DataFrame())
        
        # KPI data dictionary (for next t-test comparison)
        kpi_data = {}
        for _, row in consistency_df.iterrows():
            code = row['Code']
            if code:
                kpi_data[code] = {
                    'kpi_name': row['KPI Name'],
                    'type': row['Type'],
                    'mean': float(row['Mean']) if pd.notna(row['Mean']) else None,
                    'cv': float(row['CV(%)']) if pd.notna(row['CV(%)']) else None,
                    'consistency': row['Consistency'],
                    'raw_data': row['RawData']
                }
        
        # Get all_codes analysis results
        all_codes_df = self.analysis_results.get('all_codes', pd.DataFrame())
        
        # Build per-code severity map (ivy0210)
        code_severity_map = {}
        if not all_codes_df.empty:
            for _, row in all_codes_df.iterrows():
                c = row.get('Code', '')
                if c:
                    code_severity_map[c] = row.get('Severity', 'Normal')
        
        # Statistics summary
        kpi_df = consistency_df[consistency_df['Type'] == 'KPI']
        counter_df = consistency_df[consistency_df['Type'] == 'Counter']
        
        stats_summary = {
            'total_codes': len(consistency_df),
            'consistent': int((consistency_df['Consistency'] == 'Consistent').sum()),
            'inconsistent': int((consistency_df['Consistency'] == 'Inconsistent').sum()),
            'inconsistent_kpi': int((kpi_df['Consistency'] == 'Inconsistent').sum()),
            'inconsistent_counter': int((counter_df['Consistency'] == 'Inconsistent').sum()),
            'inconsistent_kpi_trimmed': int(((kpi_df['Consistency'] == 'Inconsistent') & 
                                             ((kpi_df['DataCount'] < 5) | (kpi_df['Trimmed_Consistency'] == 'Inconsistent'))).sum()),
            'inconsistent_counter_trimmed': int(((counter_df['Consistency'] == 'Inconsistent') & 
                                                  ((counter_df['DataCount'] < 5) | (counter_df['Trimmed_Consistency'] == 'Inconsistent'))).sum()),
            'partial_null': int((consistency_df['Consistency'] == 'partial NULL').sum()),
            'null': int((consistency_df['Consistency'] == 'NULL').sum()),
            'severity_regression': int((all_codes_df['Severity'] == 'Regression').sum()) if not all_codes_df.empty else 0,
            'severity_suspicious': int((all_codes_df['Severity'] == 'Suspicious').sum()) if not all_codes_df.empty else 0,
            'severity_normal': int((all_codes_df['Severity'] == 'Normal').sum()) if not all_codes_df.empty else 0,
            'severity_nohistory': int((all_codes_df['Severity'] == 'NoHistory').sum()) if not all_codes_df.empty else 0,
        }
        
        # Inconsistent codes list (considering trimmed data)
        inconsistent_codes = []
        for _, row in consistency_df.iterrows():
            if row['Consistency'] == 'Inconsistent':
                if row['DataCount'] >= 5 and row['Trimmed_Consistency'] == 'Consistent':
                    continue
                inconsistent_codes.append(row['Code'])
        
        comparison = self.analysis_results.get('comparison', None)
        current_context = dict(self.current_context)
        history_key = current_context.get('history_key')
        portal_summary = {
            'report_mode': 'single_sheet',
            'history_file_path': str(self.history_file_path),
            'severity_tracking_rows': self._build_portal_severity_tracking_rows(),
        }
        portal_summary['severity_tracking_count'] = len(portal_summary['severity_tracking_rows'])

        return {
            'filename': self.current_file.name,
            'filepath': str(self.current_file),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_job_id': getattr(self, 'source_job_id', None),
            'date': current_context.get('date'),
            'release': current_context.get('release'),
            'build': current_context.get('build'),
            'environment': current_context.get('environment'),
            'scenario': current_context.get('scenario'),
            'otherinfo': current_context.get('otherinfo'),
            'sheet_name': current_context.get('sheet_name'),
            'is_base_file': bool(self.is_base_file),
            'history_key': history_key,
            'matched_history_count': len(self.history_records),
            'comparison': comparison,
            'stats': stats_summary,
            'inconsistent_codes': inconsistent_codes,
            'kpi_data': kpi_data,
            'code_severity': code_severity_map,  # ivy0210: per-code severity for trend tracking
            'portal_summary': portal_summary,
        }
    
    def compare_with_history(self):
        """Compare with history, generate change analysis"""
        if not self.previous_record:
            return None
        
        current_stats = self.analysis_results.get('consistency', pd.DataFrame())
        prev_stats = self.previous_record.get('stats', {})
        prev_inconsistent = set(self.previous_record.get('inconsistent_codes', []))
        
        # Get current inconsistent codes (considering trimmed data)
        current_inconsistent = set()
        for _, row in current_stats.iterrows():
            if row['Consistency'] == 'Inconsistent':
                if row['DataCount'] >= 5 and row['Trimmed_Consistency'] == 'Consistent':
                    continue
                current_inconsistent.add(row['Code'])
        
        # Calculate changes
        new_inconsistent = current_inconsistent - prev_inconsistent
        fixed = prev_inconsistent - current_inconsistent
        persistent = current_inconsistent & prev_inconsistent
        
        comparison = {
            'previous_file': self.previous_record.get('filename', 'N/A'),
            'previous_time': self.previous_record.get('timestamp', 'N/A'),
            'delta_inconsistent': len(current_inconsistent) - len(prev_inconsistent),
            'new_inconsistent': list(new_inconsistent),
            'fixed': list(fixed),
            'persistent': list(persistent),
            'prev_stats': prev_stats
        }
        
        self.analysis_results['comparison'] = comparison
        
        print("\n========== History Comparison ==========")
        print(f"  Previous file: {comparison['previous_file']}")
        print(f"  Inconsistent change: {comparison['delta_inconsistent']:+d}")
        print(f"  New inconsistent: {len(new_inconsistent)}")
        print(f"  Fixed: {len(fixed)}")
        print(f"  Persistent inconsistent: {len(persistent)}")
        
        return comparison
    
    def generate_report(self, generate_html=True):
        """Generate reports (Excel and optionally HTML)
        
        Args:
            generate_html: Whether to generate HTML report (default True)
            
        Returns:
            Path to generated Excel report
        """
        print("\n========== Generating Reports ==========")
        
        comparison = self.analysis_results.get('comparison', None)
        current_record = self.build_current_record()
        
        # Generate Excel report
        excel_gen = ExcelReportGenerator(self.reports_dir)
        report_basename = self._report_basename()
        excel_file = excel_gen.generate(
            filename=report_basename,
            analysis_results=self.analysis_results,
            comparison=comparison,
            history_records=self.history_records,
            current_record=current_record,
            previous_record=self.previous_record  # ivy0210: for severity change tracking
        )
        
        # Generate HTML report
        html_file = None
        if generate_html:
            html_gen = HTMLReportGenerator(self.reports_dir)
            html_file = html_gen.generate(
                filename=report_basename,
                analysis_results=self.analysis_results,
                comparison=comparison,
                history_records=self.history_records
            )
        
        return {
            'excel': excel_file,
            'html': html_file,
        }

    def _run_single_sheet(self, generate_html=True):
        self.load_data()
        self.analyze_consistency()
        self.analyze_ttest_with_history()
        self.identify_suspicious_kpis()
        self.compare_with_history()

        report_files = self.generate_report(generate_html=generate_html)

        current_record = self.build_current_record()
        self.save_history(current_record)
        self.portal_current_record = current_record
        self.report_outputs = {
            'excel_report_path': report_files.get('excel'),
            'html_report_path': report_files.get('html'),
            'detail_html_paths': [report_files.get('html')] if report_files.get('html') else [],
            'detail_excel_paths': [report_files.get('excel')] if report_files.get('excel') else [],
        }
        return report_files.get('excel')

    def _aggregate_sheet_stats(self, sheet_records: list[dict[str, Any]]) -> dict[str, int]:
        aggregated = {
            'total_codes': 0,
            'consistent': 0,
            'inconsistent': 0,
            'inconsistent_kpi': 0,
            'inconsistent_counter': 0,
            'inconsistent_kpi_trimmed': 0,
            'inconsistent_counter_trimmed': 0,
            'partial_null': 0,
            'null': 0,
            'severity_regression': 0,
            'severity_suspicious': 0,
            'severity_normal': 0,
            'severity_nohistory': 0,
            'sheet_count': len(sheet_records),
        }
        for record in sheet_records:
            stats_summary = record.get('stats') or {}
            for key in aggregated:
                if key == 'sheet_count':
                    continue
                aggregated[key] += int(stats_summary.get(key) or 0)
        return aggregated

    def _generate_scout_summary_html(self, sheet_results: list[dict[str, Any]], stats_summary: dict[str, int]) -> Path:
        output_file = self.reports_dir / f'{self.current_file.stem}_trend_viewer.html'
        rows = []
        for item in sheet_results:
            detail_name = Path(str(item.get('html_report_path') or '')).name if item.get('html_report_path') else ''
            link_html = f'<a href="{escape(detail_name)}" target="_blank">Open</a>' if detail_name else '-'
            rows.append(
                '<tr>'
                f'<td>{escape(str(item.get("sheet_name") or "-"))}</td>'
                f'<td>{escape(str(item.get("history_key") or "-"))}</td>'
                f'<td>{int(item.get("matched_history_count") or 0)}</td>'
                f'<td>{int((item.get("stats") or {}).get("severity_regression") or 0)}</td>'
                f'<td>{int((item.get("stats") or {}).get("severity_suspicious") or 0)}</td>'
                f'<td>{int((item.get("stats") or {}).get("severity_nohistory") or 0)}</td>'
                f'<td>{int((item.get("stats") or {}).get("severity_normal") or 0)}</td>'
                f'<td>{link_html}</td>'
                '</tr>'
            )

        html_content = f"""<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <title>{escape(self.current_file.stem)} scout summary</title>
    <style>
        :root {{ color-scheme: light; --ink:#1f2937; --muted:#6b7280; --line:#d6dde6; --panel:#ffffff; --wash:#f4f7fb; --accent:#0f766e; --warn:#b45309; --bad:#b91c1c; --ok:#166534; }}
        body {{ margin:0; font-family:Segoe UI, Arial, sans-serif; color:var(--ink); background:linear-gradient(180deg, #eef5f4 0%, #f8fafc 100%); }}
        .shell {{ max-width:1200px; margin:0 auto; padding:32px 20px 48px; }}
        .hero, .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:18px; box-shadow:0 18px 42px rgba(15, 23, 42, 0.06); }}
        .hero {{ padding:28px; margin-bottom:20px; }}
        .eyebrow {{ margin:0 0 8px; text-transform:uppercase; letter-spacing:.08em; color:var(--accent); font-size:12px; font-weight:700; }}
        h1 {{ margin:0 0 10px; font-size:32px; }}
        p {{ margin:0; color:var(--muted); line-height:1.6; }}
        .stats {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:12px; margin-top:20px; }}
        .stat {{ background:var(--wash); border-radius:14px; padding:14px 16px; border:1px solid #e5ebf3; }}
        .stat .label {{ font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; }}
        .stat .value {{ margin-top:6px; font-size:26px; font-weight:700; }}
        .panel {{ padding:22px; }}
        table {{ width:100%; border-collapse:collapse; }}
        th, td {{ text-align:left; padding:12px 10px; border-bottom:1px solid #edf2f7; vertical-align:top; }}
        th {{ font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); }}
        a {{ color:var(--accent); text-decoration:none; font-weight:600; }}
        a:hover {{ text-decoration:underline; }}
        .summary-note {{ margin-top:14px; }}
    </style>
</head>
<body>
    <main class=\"shell\">
        <section class=\"hero\">
            <p class=\"eyebrow\">Scout Multi-Sheet Summary</p>
            <h1>{escape(self.current_file.name)}</h1>
            <p>This summary keeps scout detector output separate from standard Compass history. Each sheet is evaluated independently with its own history key and detail HTML report.</p>
            <div class=\"stats\">
                <div class=\"stat\"><div class=\"label\">Sheets</div><div class=\"value\">{int(stats_summary.get('sheet_count') or 0)}</div></div>
                <div class=\"stat\"><div class=\"label\">Regression</div><div class=\"value\">{int(stats_summary.get('severity_regression') or 0)}</div></div>
                <div class=\"stat\"><div class=\"label\">Suspicious</div><div class=\"value\">{int(stats_summary.get('severity_suspicious') or 0)}</div></div>
                <div class=\"stat\"><div class=\"label\">NoHistory</div><div class=\"value\">{int(stats_summary.get('severity_nohistory') or 0)}</div></div>
                <div class=\"stat\"><div class=\"label\">Normal</div><div class=\"value\">{int(stats_summary.get('severity_normal') or 0)}</div></div>
                <div class=\"stat\"><div class=\"label\">Total Codes</div><div class=\"value\">{int(stats_summary.get('total_codes') or 0)}</div></div>
            </div>
            <p class=\"summary-note\">History file: {escape(str(self.history_file_path))}</p>
        </section>
        <section class=\"panel\">
            <p class=\"eyebrow\">Per-Sheet Reports</p>
            <table>
                <thead>
                    <tr>
                        <th>Sheet</th>
                        <th>History Key</th>
                        <th>Matched History</th>
                        <th>Regression</th>
                        <th>Suspicious</th>
                        <th>NoHistory</th>
                        <th>Normal</th>
                        <th>Detail HTML</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows) or '<tr><td colspan="8">No sheet results generated.</td></tr>'}
                </tbody>
            </table>
        </section>
    </main>
</body>
</html>
"""
        output_file.write_text(html_content, encoding='utf-8')
        print(f"Scout summary HTML report saved to: {output_file}")
        return output_file

    def _run_scout_multi_sheet(self, generate_html=True):
        sheet_names = self._workbook_sheet_names()
        if not sheet_names:
            raise ValueError(f'No sheets found in scout workbook: {self.current_file.name}')

        print("=" * 60)
        print("KPI Anomaly Detector (Scout Multi-Sheet Mode)")
        print("=" * 60)
        print(f"Processing {len(sheet_names)} sheet(s) from {self.current_file.name}")

        sheet_records: list[dict[str, Any]] = []
        detail_html_paths: list[Path] = []
        detail_excel_paths: list[Path] = []
        for sheet_name in sheet_names:
            print(f"\n--- Sheet: {sheet_name} ---")
            sheet_detector = KPIAnomalyDetector(
                self.current_file,
                cv_threshold=self.cv_threshold,
                p_value_threshold=self.p_value_threshold,
                sheet_name=sheet_name,
                history_sheet_name=sheet_name,
                history_filename=SCOUT_HISTORY_FILENAME,
                report_suffix=sheet_name,
                allow_scout_summary=False,
            )
            sheet_detector.source_job_id = getattr(self, 'source_job_id', None)
            sheet_detector.is_base_file = self.is_base_file
            sheet_detector._run_single_sheet(generate_html=generate_html)

            sheet_record = dict(sheet_detector.build_current_record())
            sheet_record['html_report_path'] = str(sheet_detector.report_outputs.get('html_report_path')) if sheet_detector.report_outputs.get('html_report_path') else None
            sheet_record['excel_report_path'] = str(sheet_detector.report_outputs.get('excel_report_path')) if sheet_detector.report_outputs.get('excel_report_path') else None
            sheet_records.append(sheet_record)

            if sheet_detector.report_outputs.get('html_report_path'):
                detail_html_paths.append(Path(sheet_detector.report_outputs['html_report_path']))
            if sheet_detector.report_outputs.get('excel_report_path'):
                detail_excel_paths.append(Path(sheet_detector.report_outputs['excel_report_path']))

        stats_summary = self._aggregate_sheet_stats(sheet_records)
        summary_html_path = self._generate_scout_summary_html(sheet_records, stats_summary) if generate_html else None

        self.portal_current_record = {
            'filename': self.current_file.name,
            'filepath': str(self.current_file),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_job_id': getattr(self, 'source_job_id', None),
            'date': self.current_context.get('date'),
            'release': self.current_context.get('release'),
            'build': self.current_context.get('build'),
            'environment': self.current_context.get('environment'),
            'scenario': self.current_context.get('scenario'),
            'otherinfo': self.current_context.get('otherinfo'),
            'sheet_name': None,
            'is_base_file': bool(self.is_base_file),
            'history_key': self.current_context.get('history_key'),
            'matched_history_count': sum(int(record.get('matched_history_count') or 0) for record in sheet_records),
            'comparison': None,
            'stats': stats_summary,
            'inconsistent_codes': [],
            'kpi_data': {},
            'code_severity': {},
            'portal_summary': {
                'report_mode': 'scout_multi_sheet',
                'sheet_count': len(sheet_records),
                'history_file_path': str(self.history_file_path),
                'sheet_results': sheet_records,
            },
        }
        self.report_outputs = {
            'excel_report_path': None,
            'html_report_path': summary_html_path,
            'detail_html_paths': detail_html_paths,
            'detail_excel_paths': detail_excel_paths,
        }
        return summary_html_path
    
    def run(self, generate_html=True):
        """Run full analysis
        
        Args:
            generate_html: Whether to generate HTML report (default True)
            
        Returns:
            Path to generated report file
        """
        if self.scout_mode and self.allow_scout_summary:
            return self._run_scout_multi_sheet(generate_html=generate_html)

        print("=" * 60)
        print("KPI Anomaly Detector (with History Tracking)")
        print("=" * 60)
        return self._run_single_sheet(generate_html=generate_html)
