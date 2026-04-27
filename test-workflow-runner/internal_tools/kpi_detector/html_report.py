# -*- coding: utf-8 -*-
"""
HTML Report Generator Module
Generates interactive HTML reports with trend visualization and filter shortcuts
Uses echarts for professional visualization with dual chart view:
- Data Detail Chart: Shows all historical raw data together
- SPC Control Chart: Shows Shewhart X-bar chart with control limits
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class HTMLReportGenerator:
    """Generate interactive HTML analysis reports with echarts"""
    
    # Color palette for historical series
    COLORS = [
        '#E6E6E6', '#D9D9D9', '#CCCCCC', '#BFBFBF', '#B3B3B3',
        '#A6A6A6', '#999999', '#8C8C8C', '#808080', '#737373',
        '#666666', '#595959', '#4D4D4D', '#404040', '#333333',
        '#1976D2'  # Last color is for current file (blue)
    ]
    
    def __init__(self, output_dir: Path):
        """Initialize HTML report generator
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        self.current_filename = None  # Store current filename (ivy0127)
    
    def generate(self, filename: str, analysis_results: Dict[str, Any],
                 comparison: Optional[Dict] = None,
                 history_records: list = None) -> Path:
        """Generate HTML report
        
        Args:
            filename: Base filename (without extension)
            analysis_results: Analysis results dictionary
            comparison: Comparison with history
            history_records: List of historical records
            
        Returns:
            Path to generated HTML file
        """
        self.current_filename = filename  # Store for use in history series (ivy0127)
        output_file = self.output_dir / f"{filename}_trend_viewer.html"
        
        consistency_df = analysis_results.get('consistency', pd.DataFrame())
        suspicious_df = analysis_results.get('suspicious', pd.DataFrame())
        all_codes_df = analysis_results.get('all_codes', pd.DataFrame())
        
        # Prepare data for JavaScript - includes both SPC and raw data
        kpi_data = self._prepare_kpi_data(all_codes_df, history_records or [])
        
        html_content = self._generate_html(
            filename=filename,
            consistency_df=consistency_df,
            suspicious_df=suspicious_df,
            all_codes_df=all_codes_df,
            comparison=comparison,
            kpi_data=kpi_data
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML report saved to: {output_file}")
        return output_file
    
    def _prepare_kpi_data(self, all_codes_df: pd.DataFrame, 
                          history_records: list) -> Dict:
        """Prepare comprehensive KPI data including history for trend charts"""
        kpi_data = {}
        
        if all_codes_df.empty:
            return kpi_data
        
        for _, row in all_codes_df.iterrows():
            code = row.get('Code', '')
            if not code:
                continue
            
            # Get shewhart chart data
            shewhart_chart = row.get('_shewhart_chart', {})
            if isinstance(shewhart_chart, dict):
                shewhart_data = shewhart_chart
            else:
                shewhart_data = {}
            
            # Calculate historical stats
            hist_mean = row.get('Hist_Mean')
            hist_std = row.get('Hist_Std')
            
            # Prepare historical data series
            history_series = self._extract_history_series(code, history_records, row)
            
            # Calculate CV consistency stats across all batches
            cv_stats = self._calculate_cv_stats(history_series)
            
            # Check for degenerate (zero-variance) case
            is_degenerate = row.get('Is_Degenerate', False)
            degenerate_type = row.get('Degenerate_Type', '')
            
            kpi_data[code] = {
                'kpi_name': row.get('KPI Name', ''),
                'type': row.get('Type', 'Other'),
                'severity': row.get('Severity', 'Unknown'),
                'reasons': row.get('Reasons', ''),
                'cv': self._safe_float(row.get('CV(%)')),
                'z_score': self._safe_float(row.get('Z_Score')),
                'sigma_level': self._safe_float(row.get('Sigma_Level')),
                'trend': row.get('Trend', ''),
                'ttest_result': row.get('TTest_Result', 'N/A'),
                'current_mean': self._safe_float(row.get('Current_Mean')),
                'hist_mean': self._safe_float(hist_mean),
                'hist_std': self._safe_float(hist_std),
                'anomaly_count': int(row.get('Anomaly_Count', 0)) if pd.notna(row.get('Anomaly_Count')) else 0,
                'total_points': int(row.get('Total_Points', 0)) if pd.notna(row.get('Total_Points')) else 0,
                'anomaly_indices': row.get('Anomaly_Indices', []),
                'spc_zone': row.get('SPC_Zone', ''),
                'spc_violations': row.get('SPC_Violations', ''),
                'shewhart_chart': shewhart_data,
                'history': history_series,
                'cv_stats': cv_stats,
                'is_degenerate': is_degenerate,
                'degenerate_type': degenerate_type,
                'hist_stats': {
                    'mean': self._safe_float(hist_mean),
                    'upper_2sigma': self._safe_float(hist_mean + 2 * hist_std) if hist_mean and hist_std else None,
                    'lower_2sigma': self._safe_float(hist_mean - 2 * hist_std) if hist_mean and hist_std else None,
                    'upper_3sigma': self._safe_float(hist_mean + 3 * hist_std) if hist_mean and hist_std else None,
                    'lower_3sigma': self._safe_float(hist_mean - 3 * hist_std) if hist_mean and hist_std else None,
                },
                # Type-based detection fields (ivy0126)
                'kpi_type': row.get('KPI_Type', 'unknown'),
                'detection_strategy': row.get('Detection_Strategy', 'STANDARD_SPC'),
                'custom_rule_applied': row.get('Custom_Rule_Applied', False),
                'units': row.get('Units', ''),
                'formula': row.get('Formula', ''),
                'related_counters': row.get('Related_Counters', '').split(',') if row.get('Related_Counters') else [],
                'related_kpis': row.get('Related_KPIs', '').split(',') if row.get('Related_KPIs') else [],
                'xml_level': row.get('XML_Level', ''),
                'level_shift': row.get('Level_Shift', False),
                'type_anomaly_indices': row.get('Type_Anomaly_Indices', []),
                # Guard Rails fields (ivy0127)
                'guard_rail_violations': row.get('Guard_Rail_Violations', ''),
                'guard_rail_overall': row.get('Guard_Rail_Overall', ''),
            }
        
        return kpi_data
    
    def _calculate_cv_stats(self, history_series: List[Dict]) -> Dict:
        """Calculate CV consistency statistics across all batches"""
        total = len(history_series)
        # Fix: Check for both 'OK' and 'Consistent' as consistent states
        consistent_count = sum(1 for h in history_series 
                               if h.get('consistency') in ('OK', 'Consistent'))
        # Fix: Check for both 'NG' and 'Inconsistent' as inconsistent states
        inconsistent_count = sum(1 for h in history_series 
                                 if h.get('consistency') in ('NG', 'Inconsistent'))
        partial_null_count = sum(1 for h in history_series 
                                 if 'partial' in str(h.get('consistency', '')).lower() 
                                 or 'null' in str(h.get('consistency', '')).lower())
        
        return {
            'total': total,
            'consistent': consistent_count,
            'inconsistent': inconsistent_count,
            'partial_null': partial_null_count,
            'consistent_ratio': f"{consistent_count}/{total}" if total > 0 else "0/0"
        }
    
    def _parse_raw_data_string(self, raw_data) -> List[float]:
        """Parse raw data string (comma-separated values) to list of floats"""
        if raw_data is None or (isinstance(raw_data, float) and np.isnan(raw_data)):
            return []
        if isinstance(raw_data, (list, np.ndarray)):
            return [float(v) for v in raw_data if v is not None and not np.isnan(v)]
        if isinstance(raw_data, str) and raw_data.strip():
            try:
                return [float(x.strip()) for x in raw_data.split(',') if x.strip()]
            except ValueError:
                return []
        return []
    
    def _extract_history_series(self, code: str, history_records: list, 
                                 current_row: pd.Series) -> List[Dict]:
        """Extract historical raw data series for a code"""
        history_series = []

        # Add historical records
        # History record structure: record['kpi_data'][code]['raw_data']
        for i, record in enumerate(history_records):
            kpi_data = record.get('kpi_data', {})
            if code in kpi_data and 'raw_data' in kpi_data[code]:
                raw_values = kpi_data[code]['raw_data']
                # Parse values - could be list or comma-separated string
                values = self._parse_raw_data_string(raw_values)
                if len(values) > 0:
                    # Calculate CV for this batch
                    arr = np.array(values)
                    cv = (np.std(arr) / np.mean(arr) * 100) if len(arr) > 0 and np.mean(arr) != 0 else None
                    hist_consistency = kpi_data[code].get('consistency', '')
                    consistency = 'OK' if cv and cv < 10 else 'NG' if cv else '-'
                    
                    history_series.append({
                        'label': record.get('filename', f'History_{i+1}'),
                        'timestamp': record.get('timestamp', ''),
                        'values': values,
                        'raw_values': values,  # Keep raw values for table display
                        'cv': self._safe_float(cv),
                        'consistency': hist_consistency if hist_consistency else consistency,
                        'is_current': False
                    })
                else:
                    # Code exists but raw_data is empty
                    history_series.append({
                        'label': record.get('filename', f'History_{i+1}'),
                        'timestamp': record.get('timestamp', ''),
                        'values': [],
                        'raw_values': [],
                        'cv': None,
                        'consistency': kpi_data[code].get('consistency', 'NULL'),
                        'is_current': False
                    })
            else:
                # Code not found in this history record - add NULL entry
                history_series.append({
                    'label': record.get('filename', f'History_{i+1}'),
                    'timestamp': record.get('timestamp', ''),
                    'values': [],
                    'raw_values': [],
                    'cv': None,
                    'consistency': 'NULL',
                    'is_current': False
                })
        
        # Add current file data - stored as 'Current_Data' string in detector.py
        current_values = self._parse_raw_data_string(current_row.get('Current_Data'))
        current_consistency = current_row.get('Consistency', '-')
        
        # Use actual filename instead of 'Current' (ivy0127)
        current_label = self.current_filename or 'Current'
        
        if len(current_values) > 0:
            arr = np.array(current_values)
            cv = (np.std(arr) / np.mean(arr) * 100) if len(arr) > 0 and np.mean(arr) != 0 else None
            
            history_series.append({
                'label': current_label,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'values': current_values,
                'raw_values': current_values,
                'cv': self._safe_float(cv),
                'consistency': current_consistency,
                'is_current': True
            })
        else:
            # Current has no data - NULL
            history_series.append({
                'label': current_label,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'values': [],
                'raw_values': [],
                'cv': None,
                'consistency': 'NULL' if not current_consistency or current_consistency == '-' else current_consistency,
                'is_current': True
            })
        
        return history_series

    def _safe_float(self, value) -> Optional[float]:
        """Convert value to float safely, returning None for invalid values"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if np.isnan(value) or np.isinf(value):
                return None
            return float(value)
        try:
            f = float(value)
            if np.isnan(f) or np.isinf(f):
                return None
            return f
        except (ValueError, TypeError):
            return None

    def _generate_html(self, filename: str, consistency_df: pd.DataFrame,
                       suspicious_df: pd.DataFrame, all_codes_df: pd.DataFrame,
                       comparison: Optional[Dict], kpi_data: Dict) -> str:
        """Generate HTML content with echarts visualization"""
        
        # Statistics
        stats = self._calculate_statistics(consistency_df, suspicious_df, all_codes_df)
        
        # Generate KPI list HTML grouped by severity
        kpi_list_html = self._generate_kpi_list_html(all_codes_df)
        
        # Convert data to JSON for JavaScript
        kpi_data_json = json.dumps(kpi_data, ensure_ascii=False, default=str)
        colors_json = json.dumps(self.COLORS)
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KPI Anomaly Trend Viewer - {filename}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f2f5;
        }}
        .container {{
            display: flex;
            height: 100vh;
        }}
        
        /* Left Panel */
        .left-panel {{
            width: 380px;
            background: white;
            border-right: 1px solid #e0e0e0;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        .header {{
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .header h1 {{
            font-size: 18px;
            margin-bottom: 15px;
        }}
        .search-box {{
            width: 100%;
            padding: 10px 15px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            background: rgba(255,255,255,0.9);
        }}
        .search-box:focus {{ outline: none; background: white; }}
        
        /* Summary Panel */
        .summary-panel {{
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }}
        .summary-title {{
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
        }}
        .summary-stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .summary-item {{
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .summary-item:hover {{ transform: translateY(-1px); }}
        .summary-item.active {{ box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
        .summary-item.all {{ background: #e3f2fd; color: #1976d2; }}
        .summary-item.regression {{ background: #ffebee; color: #c62828; }}
        .summary-item.suspicious {{ background: #fff3e0; color: #e65100; }}
        .summary-item.normal {{ background: #e8f5e9; color: #2e7d32; }}
        .summary-item.no-history {{ background: #f5f5f5; color: #666; }}
        
        /* Type Filter Buttons */
        .type-filter {{
            padding: 10px 15px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            gap: 8px;
        }}
        .type-btn {{
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .type-btn.kpi {{ background: #e8f5e9; color: #2e7d32; }}
        .type-btn.counter {{ background: #fff3e0; color: #e65100; }}
        .type-btn.all {{ background: #e3f2fd; color: #1976d2; }}
        .type-btn.active {{ box-shadow: 0 2px 6px rgba(0,0,0,0.2); font-weight: bold; }}
        .shortcut-hint {{ font-size: 9px; opacity: 0.7; margin-left: 3px; }}
        
        /* KPI List */
        .kpi-list {{
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }}
        .severity-group {{
            margin-bottom: 15px;
        }}
        .severity-header {{
            padding: 8px 12px;
            color: white;
            font-size: 12px;
            font-weight: 600;
            border-radius: 6px;
            margin-bottom: 8px;
        }}
        .severity-items {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .kpi-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 12px;
            background: #f8f9fa;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 12px;
        }}
        .kpi-item:hover {{ background: #e3f2fd; }}
        .kpi-item.active {{ background: #1976d2; color: white; }}
        .kpi-item .code {{ font-weight: 500; }}
        .kpi-item .type {{ color: #888; font-size: 11px; }}
        .kpi-item.active .type {{ color: rgba(255,255,255,0.8); }}
        
        /* Right Panel */
        .right-panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #f5f5f5;
            overflow: hidden;
            min-width: 0;
            min-height: 0;
        }}
        .visualization-workspace {{
            flex: 1;
            min-width: 0;
            min-height: 0;
            display: flex;
            flex-direction: column;
            gap: 0;
            padding: 0 16px 16px;
        }}
        .chart-header {{
            flex: 0 0 auto;
            padding: 12px 16px 10px;
            background: white;
            border-bottom: 1px solid #e0e0e0;
        }}
        .title-row {{
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin-bottom: 6px;
            flex-wrap: wrap;
        }}
        .title-row h2 {{
            font-size: 17px;
            color: #333;
        }}
        .kpi-name {{
            color: #e91e63;
            font-size: 15px;
            font-weight: bold;
        }}
        .info-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }}
        .info-item {{
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
        }}
        .stats-row {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 8px;
            min-width: 86px;
        }}
        .stat-box.warning {{ background: #fff3e0; }}
        .stat-box.danger {{ background: #ffebee; }}
        .stat-label {{
            font-size: 10px;
            color: #888;
            margin-bottom: 3px;
        }}
        .stat-value {{
            font-size: 15px;
            font-weight: bold;
            color: #333;
        }}
        .stat-value.good {{ color: #2e7d32; }}
        .stat-value.warning {{ color: #e65100; }}
        .stat-value.danger {{ color: #c62828; }}
        
        /* Judgment Row - Combined Judgment Area and SPC Violations */
        .judgment-row {{
            display: flex;
            gap: 10px;
            margin-top: 8px;
            flex-wrap: wrap;
        }}
        
        /* SPC Violations */
        .spc-violations {{
            flex: 1;
            min-width: 200px;
            padding: 8px 12px;
            background: #ffebee;
            border-radius: 6px;
            font-size: 11px;
            color: #c62828;
            display: flex;
            align-items: center;
        }}
        
        /* Judgment Area */
        .judgment-area {{
            flex: 2;
            min-width: 300px;
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 12px;
            display: flex;
            align-items: center;
        }}
        .judgment-normal {{ background: #e8f5e9; color: #2e7d32; }}
        .judgment-warning {{ background: #fff3e0; color: #e65100; }}
        .judgment-abnormal {{ background: #ffebee; color: #c62828; }}
        
        /* Chart Tabs */
        .chart-tabs {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }}
        .tab-btn {{
            padding: 8px 14px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
            background: #e0e0e0;
            color: #666;
        }}
        .tab-btn:hover {{ background: #d0d0d0; }}
        .tab-btn.active {{
            background: #1976d2;
            color: white;
            box-shadow: 0 2px 8px rgba(25, 118, 210, 0.3);
        }}
        
        /* Chart Container */
        .chart-container {{
            flex: 1 1 auto;
            padding: 16px 16px 12px;
            position: relative;
            min-height: 260px;
            min-width: 0;
            overflow-x: auto;
            overflow-y: hidden;
            scrollbar-gutter: stable both-edges;
            background: white;
            border: 1px solid #e6e8ef;
            border-radius: 16px 16px 0 0;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        }}
        .chart-scroll-container {{
            width: 100%;
            height: 100%;
            min-height: 300px;
            min-width: 0;
            overflow-x: auto;
            overflow-y: hidden;
            padding-bottom: 10px;
            scrollbar-gutter: stable both-edges;
        }}
        .panel-divider {{
            flex: 0 0 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: row-resize;
            background: linear-gradient(180deg, #ffffff 0%, #edf3ff 100%);
            border-left: 1px solid #e6e8ef;
            border-right: 1px solid #e6e8ef;
            border-top: 1px solid #d9e3f4;
            border-bottom: 1px solid #d9e3f4;
            user-select: none;
        }}
        .panel-divider:hover {{
            background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
        }}
        .panel-divider.dragging {{
            background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%);
            box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.18);
        }}
        .panel-divider.hidden {{
            display: none;
        }}
        .panel-divider-grip {{
            width: 84px;
            height: 10px;
            border-radius: 999px;
            background: repeating-linear-gradient(
                90deg,
                #7aa2ff 0,
                #7aa2ff 10px,
                #dbeafe 10px,
                #dbeafe 18px
            );
            box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.22), 0 1px 2px rgba(59, 130, 246, 0.18);
        }}
        body.resizing-legend-panel {{
            cursor: row-resize !important;
            user-select: none;
        }}
        .chart-scroll-inner {{
            position: relative;
            height: 100%;
            min-width: 100%;
            min-height: 300px;
        }}
        #chart, #spcChart {{
            width: 100%;
            height: 100%;
            min-height: 300px;
        }}
        .placeholder {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: #999;
            font-size: 16px;
        }}
        
        /* Legend Area */
        .legend-area {{
            flex: 0 0 160px;
            display: flex;
            flex-direction: column;
            padding: 12px 16px 14px;
            background: white;
            border: 1px solid #e6e8ef;
            border-top: none;
            border-radius: 0 0 16px 16px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            max-height: none;
            min-width: 0;
            min-height: 120px;
            overflow: hidden;
        }}
        .legend-area.collapsed {{
            flex-basis: 58px !important;
            min-height: 58px;
            max-height: 58px;
        }}
        .legend-area.collapsed .legend-subtitle,
        .legend-area.collapsed .legend-items {{
            display: none;
        }}
        .legend-toolbar {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 10px;
        }}
        .legend-title {{
            font-size: 12px;
            font-weight: 700;
            color: #334155;
            margin-bottom: 3px;
        }}
        .legend-subtitle {{
            font-size: 10px;
            color: #64748b;
            line-height: 1.4;
        }}
        .legend-toggle-btn {{
            border: 1px solid #3b82f6;
            background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
            color: #1d4ed8;
            border-radius: 999px;
            padding: 7px 14px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
            box-shadow: 0 2px 6px rgba(59, 130, 246, 0.18);
        }}
        .legend-toggle-btn:hover {{
            background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%);
            border-color: #2563eb;
            color: #1e40af;
        }}
        .legend-items {{
            display: flex;
            flex-direction: column;
            gap: 5px;
            flex: 1;
            min-height: 0;
            overflow: auto;
            padding-right: 4px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 11px;
            padding: 6px 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .legend-item.current {{
            background: #e3f2fd;
            font-weight: bold;
        }}
        .legend-color {{
            width: 24px;
            height: 3px;
            margin-right: 10px;
            border-radius: 2px;
            flex-shrink: 0;
        }}
        
        /* Data Table Styles */
        .data-table-container {{
            margin-top: 10px;
            min-width: 0;
            overflow-x: auto;
            scrollbar-gutter: stable both-edges;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        }}
        .data-table th, .data-table td {{
            padding: 6px 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
            white-space: nowrap;
        }}
        .data-table th {{
            background: #f5f5f5;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        .data-table th.filename {{
            text-align: left;
            min-width: 150px;
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .data-table td.filename {{
            text-align: left;
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .data-table tr.current {{
            background: #e3f2fd;
            font-weight: bold;
        }}
        .data-table tr:hover {{
            background: #f0f7ff;
        }}
        .data-table .cv-ok {{ color: #2e7d32; }}
        .data-table .cv-ng {{ color: #c62828; }}
        .data-table .cv-null {{ color: #9e9e9e; font-style: italic; }}
        .data-table .anomaly-cell {{ 
            background: #ffebee !important; 
            color: #c62828; 
            font-weight: bold;
            border: 2px solid #f44336 !important;
        }}
        .data-table th.anomaly-header {{
            background: #ffcdd2 !important;
            color: #c62828;
        }}
        
        /* All Anomaly Badge */
        .all-anomaly-badge {{
            background: #f44336;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 9px;
            margin-left: 4px;
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
            100% {{ opacity: 1; }}
        }}
        
        /* Anomaly Filter Dropdown */
        .anomaly-filter-container {{
            position: relative;
            display: inline-block;
        }}
        .anomaly-dropdown {{
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 100;
            min-width: 140px;
            max-height: 300px;
            overflow-y: auto;
            padding: 4px 0;
            margin-top: 4px;
        }}
        .anomaly-dropdown.show {{ display: block; }}
        .anomaly-dropdown-item {{
            padding: 6px 12px;
            cursor: pointer;
            font-size: 11px;
            white-space: nowrap;
        }}
        .anomaly-dropdown-item:hover {{ background: #f0f7ff; }}
        .anomaly-dropdown-item.active {{ background: #e3f2fd; color: #1976d2; font-weight: bold; }}
        
        /* Advanced Filter Panel */
        .advanced-filter {{
            padding: 10px 15px;
            border-bottom: 1px solid #e0e0e0;
            background: #fafafa;
        }}
        .filter-title {{
            font-size: 11px;
            color: #666;
            margin-bottom: 8px;
        }}
        .filter-options {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .filter-chip {{
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 10px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid #ddd;
            background: white;
        }}
        .filter-chip:hover {{
            background: #f0f0f0;
        }}
        .filter-chip.active {{
            background: #1976d2;
            color: white;
            border-color: #1976d2;
        }}
        .filter-chip.exclude {{
            background: #ffebee;
            color: #c62828;
            border-color: #ffcdd2;
        }}
        .filter-chip.exclude.active {{
            background: #c62828;
            color: white;
        }}
        
        /* History Management Modal */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        .modal-overlay.active {{ display: flex; }}
        .modal {{
            background: white;
            border-radius: 12px;
            max-width: 700px;
            width: 90%;
            max-height: 80vh;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        .modal-header {{
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .modal-header h3 {{ font-size: 18px; }}
        .modal-close {{
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            opacity: 0.8;
        }}
        .modal-close:hover {{ opacity: 1; }}
        .modal-body {{
            padding: 20px;
            max-height: 60vh;
            overflow-y: auto;
        }}
        .history-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .history-item {{
            display: flex;
            align-items: center;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            gap: 12px;
        }}
        .history-item:hover {{ background: #e3f2fd; }}
        .history-item.current {{ background: #e8f5e9; border: 2px solid #4CAF50; }}
        .history-item.marked-invalid {{ background: #ffebee; opacity: 0.7; }}
        .history-checkbox {{
            width: 18px;
            height: 18px;
            cursor: pointer;
        }}
        .history-info {{
            flex: 1;
        }}
        .history-filename {{
            font-weight: 500;
            font-size: 13px;
            color: #333;
        }}
        .history-time {{
            font-size: 11px;
            color: #666;
        }}
        .history-stats {{
            font-size: 11px;
            color: #888;
        }}
        .history-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 500;
        }}
        .history-badge.current {{ background: #4CAF50; color: white; }}
        .history-badge.invalid {{ background: #f44336; color: white; }}
        .modal-footer {{
            padding: 15px 20px;
            background: #f5f5f5;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .modal-btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .modal-btn.primary {{ background: #1976d2; color: white; }}
        .modal-btn.primary:hover {{ background: #1565c0; }}
        .modal-btn.danger {{ background: #f44336; color: white; }}
        .modal-btn.danger:hover {{ background: #d32f2f; }}
        .modal-btn.secondary {{ background: #e0e0e0; color: #333; }}
        .modal-btn.secondary:hover {{ background: #d0d0d0; }}
        .selected-count {{ font-size: 12px; color: #666; }}
        
        /* Manage History Button */
        .manage-history-btn {{
            margin-top: 10px;
            padding: 8px 12px;
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 6px;
            color: white;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        }}
        .manage-history-btn:hover {{ background: rgba(255,255,255,0.3); }}
        
        /* Command output area */
        .command-output {{
            margin-top: 15px;
            padding: 12px;
            background: #263238;
            border-radius: 6px;
            color: #4CAF50;
            font-family: monospace;
            font-size: 11px;
            white-space: pre-wrap;
            display: none;
        }}
        .command-output.show {{ display: block; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="left-panel">
            <div class="header">
                <h1>KPI Anomaly Trend Viewer</h1>
                <input type="text" class="search-box" id="searchBox" 
                       placeholder="Search Code or KPI Name... (Press /)" oninput="filterList()">
                <button class="manage-history-btn" onclick="openHistoryModal()">📋 Manage History Records (M)</button>
            </div>
            <div class="summary-panel">
                <div class="summary-title">Severity Statistics (based on historical sigma)</div>
                <div class="summary-stats">
                    <div class="summary-item all active" onclick="filterBySeverity('all')">
                        All <b id="statTotal">{stats['total']}</b>
                    </div>
                    <div class="summary-item regression" onclick="filterBySeverity('Regression')">
                        Regression <b id="statRegression">{stats['regression']}</b>
                    </div>
                    <div class="summary-item suspicious" onclick="filterBySeverity('Suspicious')">
                        Suspicious <b id="statSuspicious">{stats['suspicious']}</b>
                    </div>
                    <div class="summary-item normal" onclick="filterBySeverity('Normal')">
                        Normal <b id="statNormal">{stats['normal']}</b>
                    </div>
                    <div class="summary-item no-history" onclick="filterBySeverity('NoHistory')">
                        No History <b id="statNoHistory">{stats['nohistory']}</b>
                    </div>
                </div>
            </div>
            <div class="type-filter">
                <button class="type-btn all active" onclick="filterByType('all')">All</button>
                <button class="type-btn kpi" onclick="filterByType('KPI')">KPI <span class="shortcut-hint">(K)</span></button>
                <button class="type-btn counter" onclick="filterByType('Counter')">Counter <span class="shortcut-hint">(C)</span></button>
                <button class="type-btn other" onclick="filterByType('Other')" style="background:#f5f5f5;color:#616161;">Other <span class="shortcut-hint">(O)</span></button>
                <span style="margin-left:10px;color:#999;">|</span>
                <button class="type-btn" onclick="filterByKpiType('count_type')" data-kpi-type="count_type" style="background:#e3f2fd;color:#1976d2;font-size:10px;">Count</button>
                <button class="type-btn" onclick="filterByKpiType('ratio_type')" data-kpi-type="ratio_type" style="background:#fce4ec;color:#c2185b;font-size:10px;">Ratio</button>
                <button class="type-btn" onclick="filterByKpiType('physical_stable')" data-kpi-type="physical_stable" style="background:#f3e5f5;color:#7b1fa2;font-size:10px;">Physical</button>
                <button class="type-btn" onclick="filterByKpiType('throughput_type')" data-kpi-type="throughput_type" style="background:#e0f7fa;color:#00838f;font-size:10px;">Throughput</button>
            </div>
            <div class="advanced-filter">
                <div class="filter-title">Advanced Filters <span class="shortcut-hint">(Press H for help)</span></div>
                <div class="filter-options">
                    <div class="anomaly-filter-container">
                        <span class="filter-chip" onclick="toggleAnomalyDropdown(event)" data-filter="hasAnomaly" id="anomalyFilterChip">Anomaly (off) <span class="shortcut-hint">(N)</span></span>
                        <div class="anomaly-dropdown" id="anomalyDropdown">
                            <!-- Dynamic options will be populated by JavaScript -->
                        </div>
                    </div>
                    <span class="filter-chip" onclick="toggleAdvancedFilter('hasGuardRail')" data-filter="hasGuardRail" id="grFilterChip">GR Triggered <span class="shortcut-hint">(G)</span></span>
                    <span class="filter-chip exclude" onclick="toggleAdvancedFilter('excludeNull')" data-filter="excludeNull">Exclude NULL <span class="shortcut-hint">(X)</span></span>
                    <span class="filter-chip exclude" onclick="toggleAdvancedFilter('excludePartialNull')" data-filter="excludePartialNull">Exclude Partial NULL <span class="shortcut-hint">(P)</span></span>
                    <span class="filter-chip" onclick="toggleAdvancedFilter('onlyInconsistent')" data-filter="onlyInconsistent">Only Inconsistent <span class="shortcut-hint">(I)</span></span>
                </div>
            </div>
            <div class="kpi-list" id="kpiList">
                {kpi_list_html}
            </div>
        </div>
        
        <div class="right-panel">
            <div class="chart-header" id="chartHeader" style="display: none;">
                <div class="title-row">
                    <h2 id="chartTitle">-</h2>
                    <span class="kpi-name" id="chartKpiName">-</span>
                    <span class="kpi-unit" id="chartKpiUnit" style="font-size:12px;color:#666;margin-left:8px;background:#f5f5f5;padding:2px 6px;border-radius:3px;"></span>
                </div>
                <div class="info-row">
                    <span class="info-item" id="chartSeverity">-</span>
                    <span class="info-item" id="chartConsistency">-</span>
                    <span class="info-item" id="chartCVStats" style="background: #f3e5f5; color: #7b1fa2;">-</span>
                </div>
                <div class="stats-row" id="statsRow">
                    <div class="stat-box">
                        <span class="stat-label">Current Mean</span>
                        <span class="stat-value" id="currentMean">-</span>
                        <span class="stat-unit" id="currentUnit" style="font-size:10px;color:#999;margin-left:4px;"></span>
                    </div>
                    <div class="stat-box history">
                        <span class="stat-label">History Mean</span>
                        <span class="stat-value" id="historyMean">-</span>
                    </div>
                    <div class="stat-box" id="relativeBox">
                        <span class="stat-label">Relative Change</span>
                        <span class="stat-value" id="relativeChange" style="font-size:12px;">-</span>
                    </div>
                    <div class="stat-box zscore" id="zscoreBox">
                        <span class="stat-label">Sigma Level</span>
                        <span class="stat-value" id="sigmaLevel">-</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Anomaly Count</span>
                        <span class="stat-value" id="anomalyCount">-</span>
                    </div>
                    <div class="stat-box spc" id="spcBox">
                        <span class="stat-label">SPC Zone</span>
                        <span class="stat-value" id="spcZone">-</span>
                    </div>
                    <div class="stat-box" id="strategyBox" style="display:block;">
                        <span class="stat-label">Strategy</span>
                        <span class="stat-value" id="strategyValue" style="font-size:11px;">-</span>
                    </div>
                </div>
                <div id="relatedCountersRow" style="display:none;margin-top:10px;padding:8px 12px;background:#f3e5f5;border-radius:6px;font-size:12px;">
                    <div style="margin-bottom:6px;">
                        <b style="color:#7b1fa2;">📐 Formula:</b>
                        <span id="formulaDisplay" style="color:#333;margin-left:8px;font-family:monospace;font-size:12px;line-height:1.8;max-width:600px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle;cursor:pointer;" title="Click to expand/collapse"></span>
                        <button id="formulaExpandBtn" onclick="toggleFormulaExpand()" style="margin-left:8px;padding:2px 8px;font-size:11px;cursor:pointer;border:1px solid #7b1fa2;background:#fff;color:#7b1fa2;border-radius:3px;display:none;">Expand</button>
                    </div>
                    <div id="relatedKpisDiv" style="display:none;margin-top:6px;">
                        <b style="color:#1565c0;">🔗 Used by KPIs:</b>
                        <span id="relatedKpisList" style="color:#333;margin-left:8px;"></span>
                    </div>
                </div>
                <div class="judgment-row" id="judgmentRow">
                    <div class="judgment-area" id="judgmentArea" style="display: none;">
                        <span id="judgmentText">-</span>
                    </div>
                    <div class="spc-violations" id="spcViolations" style="display: none;">
                        <b>Rule Violations:</b> <span id="spcViolationsText"></span>
                    </div>
                </div>
                <div class="chart-tabs" id="chartTabs" style="display: none;">
                    <button class="tab-btn active" onclick="switchChartType('detail')">Data Detail <span class="shortcut-hint">(1)</span></button>
                    <button class="tab-btn" onclick="switchChartType('spc')">SPC Control <span class="shortcut-hint">(2)</span></button>
                    <button class="tab-btn" onclick="switchChartType('iqr')">IQR/Dist <span class="shortcut-hint">(3)</span></button>
                </div>
            </div>
            <div class="visualization-workspace" id="visualizationWorkspace">
                <div class="chart-container">
                    <div class="chart-scroll-container" id="chartScrollContainer">
                        <div class="chart-scroll-inner" id="chartScrollInner">
                            <div id="chart"></div>
                            <div id="spcChart" style="display: none;"></div>
                            <div class="placeholder" id="placeholder">
                                Click a Code on the left to view trend chart
                            </div>
                        </div>
                    </div>
                </div>
                <div class="panel-divider hidden" id="legendResizeHandle" title="Drag to resize the Data Sources panel">
                    <div class="panel-divider-grip"></div>
                </div>
                <div class="legend-area" id="legendArea" style="display: none;">
                    <div class="legend-toolbar">
                        <div>
                            <div class="legend-title">Data Sources (oldest to newest)</div>
                            <div class="legend-subtitle">Use the divider above to resize this section, or collapse it when you want to focus on the chart.</div>
                        </div>
                        <button class="legend-toggle-btn" id="legendToggleBtn" type="button" onclick="toggleLegendPanel()">Collapse</button>
                    </div>
                    <div class="legend-items" id="legendItems"></div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- History Management Modal -->
    <div class="modal-overlay" id="historyModal">
        <div class="modal">
            <div class="modal-header">
                <h3>📋 Manage History Records</h3>
                <button class="modal-close" onclick="closeHistoryModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p style="margin-bottom: 15px; color: #666; font-size: 13px;">
                    Select records to mark as invalid. Invalid records will be excluded from future analysis.<br>
                    <b>Note:</b> This generates a command to run in terminal. Copy and execute it to apply changes.
                </p>
                <div class="history-list" id="historyList">
                    <!-- Populated by JavaScript -->
                </div>
                <div class="command-output" id="commandOutput"></div>
            </div>
            <div class="modal-footer">
                <span class="selected-count" id="selectedCount">0 selected</span>
                <div>
                    <button class="modal-btn secondary" onclick="selectAllHistory()">Select All</button>
                    <button class="modal-btn secondary" onclick="deselectAllHistory()">Deselect All</button>
                    <button class="modal-btn danger" onclick="generateDeleteCommand()">🗑️ Generate Delete Command</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // KPI data from Python
        const kpiData = {kpi_data_json};
        const colors = {colors_json};
        
        // Chart instances
        let chart = null;
        let spcChart = null;
        let currentCode = null;
        let currentChartType = 'detail';
        let currentSeverityFilter = 'all';
        let currentTypeFilter = 'all';
        const DEFAULT_CHART_MIN_WIDTH = 720;
        const DETAIL_MIN_POINT_WIDTH = 28;
        const SPC_MIN_POINT_WIDTH = 56;
        
        // Advanced filters
        let advancedFilters = {{
            hasAnomaly: false,
            anomalyThreshold: 1,  // 1 = at least 1, -1 = all anomaly (all points)
            excludeNull: false,
            excludePartialNull: false,
            onlyInconsistent: false,
            hasGuardRail: false  // GR filter (ivy0127)
        }};
        
        // KPI pattern: NR_XXXXx or SCOUT_NR_XXXXx
        const KPI_PATTERN = /((?:SCOUT_)?NR_\\d{{2,4}})([a-zA-Z])/i;
        // Counter pattern: MxxxxxCxxxxx
        const COUNTER_PATTERN = /^M\\d{{5}}C\\d{{1,5}}$/i;
        
        function isKPICode(code) {{
            return KPI_PATTERN.test(code);
        }}
        
        function isCounterCode(code) {{
            return COUNTER_PATTERN.test(code);
        }}
        
        // Initialize charts
        const LEGEND_PANEL_DEFAULT_HEIGHT = 160;
        const LEGEND_PANEL_MIN_HEIGHT = 120;
        const LEGEND_PANEL_COLLAPSED_HEIGHT = 58;
        const LEGEND_PANEL_MAX_RATIO = 0.5;
        const CHART_MIN_HEIGHT = 240;
        let legendPanelCollapsed = false;
        let lastLegendPanelHeight = LEGEND_PANEL_DEFAULT_HEIGHT;

        function resizeVisibleCharts() {{
            setTimeout(() => {{
                chart && chart.resize();
                spcChart && spcChart.resize();
            }}, 50);
        }}

        function getLegendLayoutElements() {{
            return {{
                workspace: document.getElementById('visualizationWorkspace'),
                legendArea: document.getElementById('legendArea'),
                resizeHandle: document.getElementById('legendResizeHandle'),
                toggleBtn: document.getElementById('legendToggleBtn')
            }};
        }}

        function getLegendPanelMaxHeight() {{
            const elements = getLegendLayoutElements();
            const workspaceHeight = elements.workspace ? elements.workspace.clientHeight : 0;
            if (!workspaceHeight) {{
                return LEGEND_PANEL_DEFAULT_HEIGHT;
            }}

            const ratioLimitedHeight = Math.floor(workspaceHeight * LEGEND_PANEL_MAX_RATIO);
            const chartReservedHeight = Math.max(CHART_MIN_HEIGHT, workspaceHeight - ratioLimitedHeight);
            return Math.max(
                LEGEND_PANEL_DEFAULT_HEIGHT,
                Math.min(ratioLimitedHeight, Math.max(workspaceHeight - chartReservedHeight, LEGEND_PANEL_DEFAULT_HEIGHT))
            );
        }}

        function setLegendPanelHeight(nextHeight) {{
            const elements = getLegendLayoutElements();
            if (!elements.legendArea) {{
                return;
            }}

            const clampedHeight = Math.max(
                LEGEND_PANEL_MIN_HEIGHT,
                Math.min(Number(nextHeight) || LEGEND_PANEL_DEFAULT_HEIGHT, getLegendPanelMaxHeight())
            );
            lastLegendPanelHeight = clampedHeight;
            elements.legendArea.style.flexBasis = `${{clampedHeight}}px`;
            elements.legendArea.style.height = `${{clampedHeight}}px`;
            resizeVisibleCharts();
        }}

        function syncLegendPanelVisibility() {{
            const elements = getLegendLayoutElements();
            const isVisible = !!elements.legendArea && elements.legendArea.style.display !== 'none';
            if (elements.resizeHandle) {{
                elements.resizeHandle.classList.toggle('hidden', !isVisible || legendPanelCollapsed);
            }}
            if (elements.toggleBtn) {{
                elements.toggleBtn.textContent = legendPanelCollapsed ? 'Expand' : 'Collapse';
            }}
        }}

        function setLegendPanelCollapsed(collapsed) {{
            const elements = getLegendLayoutElements();
            if (!elements.legendArea) {{
                return;
            }}

            legendPanelCollapsed = !!collapsed;
            elements.legendArea.classList.toggle('collapsed', legendPanelCollapsed);
            if (legendPanelCollapsed) {{
                elements.legendArea.style.flexBasis = `${{LEGEND_PANEL_COLLAPSED_HEIGHT}}px`;
                elements.legendArea.style.height = `${{LEGEND_PANEL_COLLAPSED_HEIGHT}}px`;
            }} else {{
                setLegendPanelHeight(lastLegendPanelHeight || LEGEND_PANEL_DEFAULT_HEIGHT);
            }}
            syncLegendPanelVisibility();
            resizeVisibleCharts();
        }}

        function toggleLegendPanel() {{
            setLegendPanelCollapsed(!legendPanelCollapsed);
        }}

        function initLegendPanel() {{
            const elements = getLegendLayoutElements();
            if (!elements.resizeHandle || elements.resizeHandle.dataset.bound === 'true') {{
                syncLegendPanelVisibility();
                return;
            }}

            elements.resizeHandle.dataset.bound = 'true';
            elements.resizeHandle.style.touchAction = 'none';
            elements.resizeHandle.addEventListener('pointerdown', function(event) {{
                if (legendPanelCollapsed) {{
                    return;
                }}

                event.preventDefault();
                document.body.classList.add('resizing-legend-panel');
                elements.resizeHandle.classList.add('dragging');

                if (typeof elements.resizeHandle.setPointerCapture === 'function') {{
                    try {{
                        elements.resizeHandle.setPointerCapture(event.pointerId);
                    }} catch (error) {{
                        // Ignore engines without reliable pointer capture support.
                    }}
                }}

                const onPointerMove = function(moveEvent) {{
                    const workspaceRect = elements.workspace.getBoundingClientRect();
                    const nextHeight = workspaceRect.bottom - moveEvent.clientY;
                    setLegendPanelHeight(nextHeight);
                }};
                const onPointerUp = function(moveEvent) {{
                    document.body.classList.remove('resizing-legend-panel');
                    elements.resizeHandle.classList.remove('dragging');
                    document.removeEventListener('pointermove', onPointerMove);
                    document.removeEventListener('pointerup', onPointerUp);
                    document.removeEventListener('pointercancel', onPointerUp);

                    if (typeof elements.resizeHandle.releasePointerCapture === 'function') {{
                        try {{
                            elements.resizeHandle.releasePointerCapture(moveEvent.pointerId);
                        }} catch (error) {{
                            // Ignore engines without reliable pointer capture support.
                        }}
                    }}
                }};

                document.addEventListener('pointermove', onPointerMove);
                document.addEventListener('pointerup', onPointerUp);
                document.addEventListener('pointercancel', onPointerUp);
            }});

            syncLegendPanelVisibility();
        }}

        function ensureLegendPanelVisible() {{
            const elements = getLegendLayoutElements();
            if (!elements.legendArea) {{
                return;
            }}
            elements.legendArea.style.display = 'flex';
            elements.legendArea.style.visibility = 'visible';
            elements.legendArea.style.opacity = '1';
            if (!legendPanelCollapsed) {{
                setLegendPanelHeight(lastLegendPanelHeight || LEGEND_PANEL_DEFAULT_HEIGHT);
            }}
            syncLegendPanelVisibility();
        }}

        function initChart() {{
            const chartDom = document.getElementById('chart');
            const spcChartDom = document.getElementById('spcChart');
            if (typeof echarts === 'undefined') {{
                console.warn('ECharts is unavailable; chart rendering will be skipped.');
                chart = null;
                spcChart = null;
                return;
            }}

            try {{
                chart = echarts.init(chartDom);
                spcChart = echarts.init(spcChartDom);
            }} catch (error) {{
                console.warn('Failed to initialize charts:', error);
                chart = null;
                spcChart = null;
                return;
            }}
            
            window.addEventListener('resize', function() {{
                if (!legendPanelCollapsed) {{
                    setLegendPanelHeight(lastLegendPanelHeight || LEGEND_PANEL_DEFAULT_HEIGHT);
                }}
                resizeVisibleCharts();
            }});
        }}

        function getChartScrollElements() {{
            return {{
                container: document.getElementById('chartScrollContainer'),
                inner: document.getElementById('chartScrollInner')
            }};
        }}

        function applyChartLayout(chartType, pointCount) {{
            const elements = getChartScrollElements();
            if (!elements.container || !elements.inner) {{
                return DEFAULT_CHART_MIN_WIDTH;
            }}

            const safePointCount = Math.max(pointCount || 0, 1);
            let minPointWidth = 0;
            if (chartType === 'detail') {{
                minPointWidth = DETAIL_MIN_POINT_WIDTH;
            }} else if (chartType === 'spc') {{
                minPointWidth = SPC_MIN_POINT_WIDTH;
            }}

            const viewportWidth = Math.max(elements.container.clientWidth || 0, DEFAULT_CHART_MIN_WIDTH);
            const contentWidth = minPointWidth > 0
                ? Math.max(DEFAULT_CHART_MIN_WIDTH, viewportWidth, safePointCount * minPointWidth + 160)
                : Math.max(DEFAULT_CHART_MIN_WIDTH, viewportWidth);

            elements.inner.style.width = `${{contentWidth}}px`;
            return contentWidth;
        }}

        function buildAxisDensity(pointCount, chartType) {{
            const safePointCount = Math.max(pointCount || 0, 1);
            let interval = 0;
            let rotate = 0;

            if (safePointCount > 120) {{
                interval = Math.max(5, Math.ceil(safePointCount / 18) - 1);
                rotate = 60;
            }} else if (safePointCount > 80) {{
                interval = Math.max(3, Math.ceil(safePointCount / 20) - 1);
                rotate = 55;
            }} else if (safePointCount > 40) {{
                interval = Math.max(1, Math.ceil(safePointCount / 24) - 1);
                rotate = 45;
            }} else if (safePointCount > 20) {{
                interval = 1;
                rotate = chartType === 'spc' ? 35 : 30;
            }}

            return {{ interval, rotate }};
        }}

        function collectNumericValues(input) {{
            const result = [];

            function visit(value) {{
                if (value === null || value === undefined) {{
                    return;
                }}
                if (typeof value === 'number' && Number.isFinite(value)) {{
                    result.push(value);
                    return;
                }}
                if (Array.isArray(value)) {{
                    value.forEach(visit);
                    return;
                }}
                if (typeof value === 'object' && typeof value.value === 'number' && Number.isFinite(value.value)) {{
                    result.push(value.value);
                }}
            }}

            visit(input);
            return result;
        }}

        function buildValueAxisRange(values, options) {{
            const settings = options || {{}};
            const numericValues = collectNumericValues(values);
            if (!numericValues.length) {{
                return {{ min: null, max: null }};
            }}

            let minValue = Math.min(...numericValues);
            let maxValue = Math.max(...numericValues);
            let span = maxValue - minValue;

            const minSpanAbsolute = settings.minSpanAbsolute !== undefined ? settings.minSpanAbsolute : 0.02;
            const minSpanRatio = settings.minSpanRatio !== undefined ? settings.minSpanRatio : 0.2;
            const paddingRatio = settings.paddingRatio !== undefined ? settings.paddingRatio : 0.12;

            if (!Number.isFinite(span) || span <= 0) {{
                const center = Number.isFinite(minValue) ? minValue : 0;
                span = Math.max(Math.abs(center) * minSpanRatio, minSpanAbsolute);
                minValue = center - span / 2;
                maxValue = center + span / 2;
            }} else if (span < minSpanAbsolute) {{
                const center = (minValue + maxValue) / 2;
                span = Math.max(Math.abs(center) * minSpanRatio, minSpanAbsolute);
                minValue = center - span / 2;
                maxValue = center + span / 2;
            }}

            const padding = Math.max(span * paddingRatio, minSpanAbsolute * 0.35);
            return {{
                min: Number((minValue - padding).toFixed(6)),
                max: Number((maxValue + padding).toFixed(6))
            }};
        }}

        function buildCategoryDataZoom(pointCount, visiblePointCount) {{
            const safePointCount = Math.max(pointCount || 0, 0);
            if (safePointCount <= 1) {{
                return [];
            }}

            const clampedEndValue = Math.max(Math.min(visiblePointCount - 1, safePointCount - 1), 0);

            return [
                {{
                    type: 'inside',
                    xAxisIndex: 0,
                    startValue: 0,
                    endValue: clampedEndValue,
                    zoomLock: false,
                    moveOnMouseWheel: true,
                    zoomOnMouseWheel: false,
                    filterMode: 'none',
                }},
                {{
                    type: 'slider',
                    xAxisIndex: 0,
                    height: 28,
                    bottom: 12,
                    startValue: 0,
                    endValue: clampedEndValue,
                    borderColor: '#93c5fd',
                    backgroundColor: '#eff6ff',
                    fillerColor: 'rgba(59, 130, 246, 0.22)',
                    handleSize: '92%',
                    moveHandleSize: 10,
                    handleStyle: {{
                        color: '#2563eb',
                        borderColor: '#1d4ed8',
                        shadowBlur: 4,
                        shadowColor: 'rgba(37, 99, 235, 0.28)'
                    }},
                    dataBackground: {{
                        lineStyle: {{ color: '#93c5fd', opacity: 0.9 }},
                        areaStyle: {{ color: 'rgba(147, 197, 253, 0.22)' }}
                    }},
                    selectedDataBackground: {{
                        lineStyle: {{ color: '#2563eb' }},
                        areaStyle: {{ color: 'rgba(37, 99, 235, 0.18)' }}
                    }},
                    textStyle: {{ color: '#1d4ed8' }},
                    brushSelect: false,
                    showDetail: true,
                    labelFormatter: function(value) {{
                        return `${{value + 1}}`;
                    }},
                    filterMode: 'none',
                }}
            ];
        }}

        function getGridBottom(pointCount, chartType) {{
            const needsZoom = chartType !== 'iqr' && pointCount > (chartType === 'spc' ? 14 : 18);
            const density = buildAxisDensity(pointCount, chartType);
            if (needsZoom) {{
                return density.rotate >= 45 ? 95 : 78;
            }}
            return density.rotate >= 45 ? 68 : density.rotate >= 30 ? 54 : 36;
        }}

        function formatCategoryLabel(value, index, pointCount, chartType) {{
            if (chartType === 'detail') {{
                return pointCount > 24 ? `P${{index + 1}}` : value;
            }}

            const text = String(value || '');
            if (pointCount <= 12 || text.length <= 16) {{
                return text;
            }}
            return text.slice(0, 14) + '...';
        }}
        
        // Switch between chart types
        function switchChartType(type) {{
            currentChartType = type;
            
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach((btn, idx) => {{
                btn.classList.remove('active');
                if ((type === 'detail' && idx === 0) || 
                    (type === 'spc' && idx === 1) || 
                    (type === 'iqr' && idx === 2)) {{
                    btn.classList.add('active');
                }}
            }});
            
            const chartEl = document.getElementById('chart');
            const spcChartEl = document.getElementById('spcChart');
            const chartContainer = document.querySelector('.chart-container');
            
            if (type === 'detail') {{
                chartEl.style.display = 'block';
                spcChartEl.style.display = 'none';
                chartEl.style.width = '100%';
                chartEl.style.height = '100%';
                chartContainer.style.flexDirection = 'column';
                // Redraw chart and resize
                if (currentCode) {{
                    const data = kpiData[currentCode];
                    if (data) {{
                        drawDetailChart(currentCode, data);
                    }}
                }}
                resizeVisibleCharts();
            }} else if (type === 'spc') {{
                chartEl.style.display = 'none';
                spcChartEl.style.display = 'block';
                spcChartEl.style.width = '100%';
                spcChartEl.style.height = '100%';
                chartContainer.style.flexDirection = 'column';
                if (currentCode) {{
                    showSPCChart(currentCode);
                }}
                resizeVisibleCharts();
            }} else if (type === 'iqr') {{
                chartEl.style.display = 'none';
                spcChartEl.style.display = 'block';
                spcChartEl.style.width = '100%';
                spcChartEl.style.height = '100%';
                chartContainer.style.flexDirection = 'column';
                if (currentCode) {{
                    showIQRChart(currentCode);
                }}
                resizeVisibleCharts();
            }}
        }}
        
        // Format reasons with color highlighting for different detection results
        // ivy0204: Add color-coded reasons display
        function formatReasons(reasons) {{
            if (!reasons) return '';
            
            // Define patterns and their colors
            // Green (Normal): within bounds, σ-level < 2, passed checks
            // Red (Regression): [HARD], Fail, violations
            // Orange (Suspicious): warnings
            // Blue (Info): dB Floor constraint
            
            let formatted = reasons;
            
            // [dB Floor] ... → blue (physical constraint applied)
            formatted = formatted.replace(
                /(\[dB Floor\][^;]*)/gi,
                '<span style="color:#2196f3;font-weight:500">$1</span>'
            );
            
            // [RELATIVE] ... within bounds → green
            formatted = formatted.replace(
                /(\[RELATIVE\][^;]*within bounds)/gi,
                '<span style="color:#4caf50;font-weight:500">$1</span>'
            );
            
            // [IQR] ... Constant data or within bounds → green  
            formatted = formatted.replace(
                /(\[IQR\][^;]*(Constant data|within bounds|Normal))/gi,
                '<span style="color:#4caf50;font-weight:500">$1</span>'
            );
            
            // Standard SPC: σ-level < 2 → green
            formatted = formatted.replace(
                /Standard SPC: σ-level=([0-9.]+)/g,
                function(match, level) {{
                    const sigmaLevel = parseFloat(level);
                    if (sigmaLevel < 2) {{
                        return '<span style="color:#4caf50;font-weight:500">' + match + '</span>';
                    }} else if (sigmaLevel < 3) {{
                        return '<span style="color:#ff9800;font-weight:500">' + match + '</span>';
                    }} else {{
                        return '<span style="color:#f44336;font-weight:500">' + match + '</span>';
                    }}
                }}
            );
            
            // [HARD] ... → red (this is the regression trigger)
            formatted = formatted.replace(
                /(\[HARD\][^;]*)/g,
                '<span style="color:#f44336;font-weight:bold">$1</span>'
            );
            
            // T-Test Fail → orange (reference only)
            formatted = formatted.replace(
                /(T-Test Fail[^;]*)/g,
                '<span style="color:#ff9800">$1</span>'
            );
            
            // T-Test Pass → green
            formatted = formatted.replace(
                /(T-Test Pass)/g,
                '<span style="color:#4caf50">$1</span>'
            );
            
            // SPC violations → red
            formatted = formatted.replace(
                /(Rule\d+:[^;)]*)/g,
                '<span style="color:#f44336">$1</span>'
            );
            
            return formatted;
        }}
        
        // Show Data Detail Chart
        function showChart(code) {{
            const data = kpiData[code];
            if (!data) {{
                alert('No data available for this code');
                return;
            }}
            
            currentCode = code;
            
            // Update selection
            document.querySelectorAll('.kpi-item').forEach(item => {{
                item.classList.remove('active');
                if (item.dataset.code === code) {{
                    item.classList.add('active');
                }}
            }});
            
            // Show chart area
            document.getElementById('placeholder').style.display = 'none';
            document.getElementById('chartHeader').style.display = 'block';
            document.getElementById('chartTabs').style.display = 'flex';
            ensureLegendPanelVisible();
            updateDataTable(code, data);
            
            // Update header info
            document.getElementById('chartTitle').textContent = code;
            const kpiNameEl = document.getElementById('chartKpiName');
            kpiNameEl.textContent = data.kpi_name || '-';
            kpiNameEl.style.color = '#e91e63';
            kpiNameEl.style.fontSize = '18px';
            kpiNameEl.style.fontWeight = 'bold';
            
            // Update unit display (ivy0127)
            const unitEl = document.getElementById('chartKpiUnit');
            const units = data.units || '';
            unitEl.textContent = units ? `unit: ${{units}}` : '';
            
            // Update severity display
            const sevEl = document.getElementById('chartSeverity');
            const severity = data.severity || '-';
            sevEl.textContent = 'Severity: ' + severity;
            sevEl.className = 'info-item';
            if (severity === 'Regression') {{
                sevEl.style.background = '#ffebee';
                sevEl.style.color = '#c62828';
            }} else if (severity === 'Suspicious') {{
                sevEl.style.background = '#fff3e0';
                sevEl.style.color = '#e65100';
            }} else if (severity === 'Normal') {{
                sevEl.style.background = '#e8f5e9';
                sevEl.style.color = '#2e7d32';
            }} else {{
                sevEl.style.background = '#f5f5f5';
                sevEl.style.color = '#666';
            }}
            
            // Update CV display with stats
            const cvEl = document.getElementById('chartConsistency');
            cvEl.textContent = 'Current CV: ' + (data.consistency || '-');
            
            // Update CV Stats (consistent ratio across all batches)
            const cvStatsEl = document.getElementById('chartCVStats');
            const cvStats = data.cv_stats || {{}};
            cvStatsEl.textContent = `CV Consistency: ${{cvStats.consistent_ratio || '0/0'}} OK`;
            
            // T-Test and Reasons removed (ivy0127) - redundant with judgment area
            
            // Update stats (ivy0210: 3 decimal places + relative change)
            document.getElementById('currentMean').textContent = 
                data.current_mean !== null ? data.current_mean.toFixed(3) : '-';
            document.getElementById('historyMean').textContent = 
                data.hist_mean !== null ? data.hist_mean.toFixed(3) : '-';
            
            // Calculate and display relative change: ((current - history) / history) * 100%
            const relChangeEl = document.getElementById('relativeChange');
            const relBox = document.getElementById('relativeBox');
            if (data.current_mean !== null && data.hist_mean !== null && Math.abs(data.hist_mean) > 1e-10) {{
                const relPct = ((data.current_mean - data.hist_mean) / Math.abs(data.hist_mean)) * 100;
                relChangeEl.textContent = (relPct >= 0 ? '+' : '') + relPct.toFixed(3) + '%';
                relChangeEl.className = 'stat-value';
                relBox.className = 'stat-box';
                if (Math.abs(relPct) < 5) {{
                    relChangeEl.classList.add('good');
                }} else if (Math.abs(relPct) < 20) {{
                    relChangeEl.classList.add('warning');
                    relBox.classList.add('warning');
                }} else {{
                    relChangeEl.classList.add('danger');
                    relBox.classList.add('danger');
                }}
            }} else if (data.hist_mean === null || data.hist_mean === undefined) {{
                relChangeEl.textContent = 'N/A';
                relChangeEl.className = 'stat-value';
                relBox.className = 'stat-box';
            }} else {{
                relChangeEl.textContent = data.current_mean !== null ? '∞' : '-';
                relChangeEl.className = 'stat-value';
                relBox.className = 'stat-box';
            }}
            
            // Update unit display (ivy0126)
            const currentUnitEl = document.getElementById('currentUnit');
            currentUnitEl.textContent = data.units || '';
            
            // Update Strategy display (ivy0203)
            const strategyBox = document.getElementById('strategyBox');
            const strategyValue = document.getElementById('strategyValue');
            const strategy = data.detection_strategy || 'STANDARD_SPC';
            const strategyLabels = {{
                'STANDARD_SPC': '📊 SPC',
                'ABS_THRESHOLD': '🎯 Threshold',
                'IQR': '📦 IQR',
                'POISSON': '🎲 Poisson',
                'RELATIVE': '📐 Relative',
                'Z_SCORE': '📈 Z-Score',
                'KS_TEST': '🔬 KS-Test',
                'SKIP': '⏭️ Skip'
            }};
            let strategyLabel = strategyLabels[strategy] || strategy;
            // Add custom rule indicator
            if (data.custom_rule_applied) {{
                strategyLabel = '✏️ ' + strategyLabel;
            }}
            strategyValue.textContent = strategyLabel;
            // Build tooltip with KPI type info
            let tooltip = `KPI Type: ${{data.kpi_type || 'unknown'}}`;
            if (data.custom_rule_applied) {{
                tooltip += ' | Custom Rule Applied';
            }}
            strategyValue.title = tooltip;
            
            // Update Formula display with colored counters and Related KPIs (ivy0126)
            const relatedCountersRow = document.getElementById('relatedCountersRow');
            const relatedKpisDiv = document.getElementById('relatedKpisDiv');
            const relatedKpisList = document.getElementById('relatedKpisList');
            const formulaDisplay = document.getElementById('formulaDisplay');
            const relatedCounters = data.related_counters || [];
            const relatedKpis = data.related_kpis || [];
            const formula = data.formula || '';
            
            // Severity color mapping
            const severityColors = {{
                'Regression': '#d32f2f',
                'Suspicious': '#f57c00', 
                'Normal': '#388e3c',
                'NoHistory': '#9e9e9e'
            }};
            const severityBgColors = {{
                'Regression': '#ffebee',
                'Suspicious': '#fff3e0', 
                'Normal': '#e8f5e9',
                'NoHistory': '#f5f5f5'
            }};
            
            const hasRelatedKpis = relatedKpis.length > 0 && relatedKpis[0];
            
            // Function to colorize formula with counter severity colors
            function colorizeFormula(formula) {{
                if (!formula) return '';
                
                // Tokenize the formula first to avoid nested replacements
                const tokens = [];
                const counterPattern = /M\\d+C\\d+/g;
                let lastIndex = 0;
                let match;
                
                // Extract counters and non-counter parts
                while ((match = counterPattern.exec(formula)) !== null) {{
                    // Add text before counter
                    if (match.index > lastIndex) {{
                        tokens.push({{type: 'text', value: formula.substring(lastIndex, match.index)}});
                    }}
                    // Add counter
                    tokens.push({{type: 'counter', value: match[0]}});
                    lastIndex = match.index + match[0].length;
                }}
                // Add remaining text
                if (lastIndex < formula.length) {{
                    tokens.push({{type: 'text', value: formula.substring(lastIndex)}});
                }}
                
                // Build HTML from tokens
                let result = '';
                for (const token of tokens) {{
                    if (token.type === 'counter') {{
                        const counterData = kpiData[token.value];
                        if (counterData) {{
                            const severity = counterData.severity || 'Normal';
                            const color = severityColors[severity] || '#7b1fa2';
                            const bgColor = severityBgColors[severity] || '#f5f5f5';
                            result += `<a href="javascript:void(0)" onclick="showChart('${{token.value}}')" style="color:${{color}};text-decoration:none;cursor:pointer;padding:1px 4px;background:${{bgColor}};border-radius:3px;border:1px solid ${{color}}40;font-weight:600;" title="${{severity}}">${{token.value}}</a>`;
                        }} else {{
                            result += `<span style="color:#999;padding:1px 4px;background:#f5f5f5;border-radius:3px;" title="No data">${{token.value}}</span>`;
                        }}
                    }} else {{
                        // Process text: highlight symbols and numbers
                        // Use simple approach: just color operators, skip number coloring to avoid conflicts
                        let text = token.value;
                        // Escape HTML first
                        text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        // Only highlight operators with simple inline style (no nested replacements)
                        text = text.split('').map(ch => {{
                            if ('()+-*/'.includes(ch)) {{
                                return '<b style="color:#1565c0;">' + ch + '</b>';
                            }}
                            return ch;
                        }}).join('');
                        result += text;
                    }}
                }}
                
                return result;
            }}
            
            // Store full formula HTML for expand/collapse
            let fullFormulaHtml = '';
            let isFormulaExpanded = false;
            
            // Toggle formula expand/collapse
            window.toggleFormulaExpand = function() {{
                const formulaDisplay = document.getElementById('formulaDisplay');
                const expandBtn = document.getElementById('formulaExpandBtn');
                isFormulaExpanded = !isFormulaExpanded;
                if (isFormulaExpanded) {{
                    formulaDisplay.style.maxWidth = 'none';
                    formulaDisplay.style.whiteSpace = 'normal';
                    formulaDisplay.style.wordBreak = 'break-all';
                    expandBtn.textContent = 'Collapse';
                }} else {{
                    formulaDisplay.style.maxWidth = '600px';
                    formulaDisplay.style.whiteSpace = 'nowrap';
                    formulaDisplay.style.wordBreak = 'normal';
                    expandBtn.textContent = 'Expand';
                }}
            }};
            
            // Click on formula to toggle
            formulaDisplay.onclick = function() {{
                toggleFormulaExpand();
            }};
            
            if (formula || hasRelatedKpis) {{
                relatedCountersRow.style.display = 'block';
                
                // Display colorized formula
                if (formula) {{
                    fullFormulaHtml = colorizeFormula(formula);
                    formulaDisplay.innerHTML = fullFormulaHtml;
                    formulaDisplay.parentElement.style.display = 'block';
                    // Show expand button if formula is long (> 80 chars)
                    const expandBtn = document.getElementById('formulaExpandBtn');
                    if (formula.length > 80) {{
                        expandBtn.style.display = 'inline-block';
                    }} else {{
                        expandBtn.style.display = 'none';
                    }}
                    // Reset to collapsed state
                    isFormulaExpanded = false;
                    formulaDisplay.style.maxWidth = '600px';
                    formulaDisplay.style.whiteSpace = 'nowrap';
                    expandBtn.textContent = 'Expand';
                }} else {{
                    formulaDisplay.parentElement.style.display = 'none';
                }}
                
                // Make KPI codes clickable with severity colors (for counters)
                if (hasRelatedKpis) {{
                    relatedKpisDiv.style.display = 'block';
                    const kpiLinks = relatedKpis.map(k => {{
                        const kpiDataItem = kpiData[k];
                        if (kpiDataItem) {{
                            const severity = kpiDataItem.severity || 'Normal';
                            const color = severityColors[severity] || '#1565c0';
                            const bgColor = severityBgColors[severity] || '#e3f2fd';
                            return `<a href="javascript:void(0)" onclick="showChart('${{k}}')" 
                                style="color:${{color}};text-decoration:none;cursor:pointer;padding:2px 6px;
                                background:${{bgColor}};border-radius:4px;margin:1px;
                                border:1px solid ${{color}}30;" 
                                title="${{severity}}">${{k}}</a>`;
                        }}
                        return `<span style="color:#999;padding:2px 6px;background:#f5f5f5;border-radius:4px;margin:1px;" title="No data">${{k}}</span>`;
                    }});
                    relatedKpisList.innerHTML = kpiLinks.join(' ');
                }} else {{
                    relatedKpisDiv.style.display = 'none';
                }}
            }} else {{
                relatedCountersRow.style.display = 'none';
            }}
            
            // Sigma level
            const sigmaEl = document.getElementById('sigmaLevel');
            const zscoreBox = document.getElementById('zscoreBox');
            if (data.sigma_level !== null) {{
                sigmaEl.textContent = data.sigma_level.toFixed(3) + 'σ';
                sigmaEl.className = 'stat-value';
                zscoreBox.className = 'stat-box zscore';
                if (data.sigma_level <= 2) {{
                    sigmaEl.classList.add('good');
                }} else if (data.sigma_level <= 3) {{
                    sigmaEl.classList.add('warning');
                    zscoreBox.classList.add('warning');
                }} else {{
                    sigmaEl.classList.add('danger');
                    zscoreBox.classList.add('danger');
                }}
            }} else {{
                sigmaEl.textContent = '-';
            }}
            
            // Anomaly count
            const anomalyEl = document.getElementById('anomalyCount');
            anomalyEl.textContent = data.anomaly_count || 0;
            anomalyEl.className = 'stat-value';
            if (data.anomaly_count === 0) {{
                anomalyEl.classList.add('good');
            }} else if (data.anomaly_count <= 2) {{
                anomalyEl.classList.add('warning');
            }} else {{
                anomalyEl.classList.add('danger');
            }}
            
            // SPC Zone
            const spcZoneEl = document.getElementById('spcZone');
            const spcZone = data.spc_zone || '-';
            spcZoneEl.textContent = spcZone;
            spcZoneEl.className = 'stat-value';
            if (spcZone === 'OutOfControl') {{
                spcZoneEl.classList.add('danger');
                spcZoneEl.textContent = 'Out of Control';
            }} else if (spcZone === 'A') {{
                spcZoneEl.classList.add('warning');
            }} else if (spcZone === 'C' || spcZone === 'B') {{
                spcZoneEl.classList.add('good');
            }}
            
            // SPC Violations
            const violationsDiv = document.getElementById('spcViolations');
            const violations = data.spc_violations || '';
            const isDegenerate = data.is_degenerate || false;
            const degenerateType = data.degenerate_type || '';
            
            if (violations) {{
                violationsDiv.style.display = 'flex';
                document.getElementById('spcViolationsText').textContent = violations;
            }} else if (isDegenerate) {{
                violationsDiv.style.display = 'flex';
                violationsDiv.style.background = '#e3f2fd';
                violationsDiv.style.color = '#1565c0';
                const typeLabel = degenerateType === 'ceiling' ? 'Ceiling (100%)' : 
                                  degenerateType === 'floor' ? 'Floor (0)' : 'Constant';
                document.getElementById('spcViolationsText').textContent = `Zero-variance KPI (${{typeLabel}}) - Rule-based judgment`;
            }} else {{
                violationsDiv.style.display = 'none';
            }}
            
            // Judgment area
            const judgmentArea = document.getElementById('judgmentArea');
            const judgmentText = document.getElementById('judgmentText');
            judgmentArea.style.display = 'flex';
            
            const history = data.history || [];
            if (severity === 'NoHistory' || history.length <= 1) {{
                judgmentArea.className = 'judgment-area judgment-warning';
                judgmentText.innerHTML = '⚠️ <b>No History Data</b> - Cannot compare trends, need more data';
            }} else if (isDegenerate) {{
                // Degenerate case: use rule-based judgment display
                if (severity === 'Normal') {{
                    judgmentArea.className = 'judgment-area judgment-normal';
                    judgmentText.innerHTML = '✅ <b>Normal (Stable)</b> - ' + formatReasons(data.reasons || 'Constant value maintained');
                }} else if (severity === 'Suspicious') {{
                    judgmentArea.className = 'judgment-area judgment-warning';
                    judgmentText.innerHTML = '⚠️ <b>Suspicious</b> - ' + formatReasons(data.reasons || 'Value deviation detected (rule-based)');
                }} else if (severity === 'Regression') {{
                    judgmentArea.className = 'judgment-area judgment-abnormal';
                    judgmentText.innerHTML = '❌ <b>Regression</b> - ' + formatReasons(data.reasons || 'Significant deviation (rule-based)');
                }}
            }} else if (severity === 'Normal') {{
                judgmentArea.className = 'judgment-area judgment-normal';
                judgmentText.innerHTML = '✅ <b>Normal</b> - ' + formatReasons(data.reasons || 'Current mean is within historical ±2σ range');
            }} else if (severity === 'Suspicious') {{
                judgmentArea.className = 'judgment-area judgment-warning';
                judgmentText.innerHTML = '⚠️ <b>Suspicious</b> - ' + formatReasons(data.reasons || 'Beyond ±2σ but within ±3σ');
            }} else if (severity === 'Regression') {{
                judgmentArea.className = 'judgment-area judgment-abnormal';
                judgmentText.innerHTML = '❌ <b>Regression</b> - ' + formatReasons(data.reasons || 'Beyond ±3σ or trending deviation');
            }}
            
            // Draw chart based on current type
            if (currentChartType === 'detail') {{
                drawDetailChart(code, data);
            }} else if (currentChartType === 'spc') {{
                showSPCChart(code);
            }} else if (currentChartType === 'both') {{
                drawDetailChart(code, data);
                showSPCChart(code);
                // Resize after drawing
                resizeVisibleCharts();
            }}
        }}
        
        function drawDetailChart(code, data) {{
            const history = data.history || [];
            // Filter out empty history entries for chart (but keep for table)
            const chartHistory = history.filter(h => h.values && h.values.length > 0);

            if (!chart) {{
                const placeholder = document.getElementById('placeholder');
                if (placeholder) {{
                    placeholder.style.display = 'block';
                    placeholder.textContent = 'Chart rendering is unavailable, but Data Sources remains available below.';
                }}
                updateDataTable(code, data);
                return;
            }}
            
            if (chartHistory.length === 0) {{
                chart.setOption({{
                    title: {{
                        text: 'No Data Available',
                        left: 'center',
                        top: 'center',
                        textStyle: {{ color: '#999' }}
                    }}
                }}, true);
                // Still show the data table even if no chart data
                updateDataTable(code, data);
                return;
            }}
            
            const seriesData = [];
            const legendItems = [];
            
            // Find max points for X-axis
            let maxPoints = 0;
            chartHistory.forEach(h => {{
                if (h.values && h.values.length > maxPoints) maxPoints = h.values.length;
            }});
            
            // X-axis labels
            const xLabels = [];
            for (let i = 0; i < maxPoints; i++) {{
                xLabels.push('Point_' + (i + 1));
            }}
            
            // Add confidence interval bands if history stats available
            if (data.hist_stats && data.hist_stats.upper_2sigma !== null) {{
                const upper = data.hist_stats.upper_2sigma;
                const lower = data.hist_stats.lower_2sigma;
                const mean = data.hist_stats.mean;
                
                // Upper boundary
                seriesData.push({{
                    name: 'History +2σ',
                    type: 'line',
                    data: Array(maxPoints).fill(upper),
                    lineStyle: {{ color: '#81C784', type: 'dashed', width: 1 }},
                    itemStyle: {{ color: '#81C784' }},
                    symbol: 'none',
                    silent: true
                }});
                
                // Lower boundary with area
                seriesData.push({{
                    name: 'History -2σ',
                    type: 'line',
                    data: Array(maxPoints).fill(lower),
                    lineStyle: {{ color: '#81C784', type: 'dashed', width: 1 }},
                    itemStyle: {{ color: '#81C784' }},
                    symbol: 'none',
                    areaStyle: {{
                        color: 'rgba(129, 199, 132, 0.15)',
                        origin: 'start'
                    }},
                    silent: true
                }});
                
                // History mean line
                seriesData.push({{
                    name: 'History Mean',
                    type: 'line',
                    data: Array(maxPoints).fill(mean),
                    lineStyle: {{ color: '#4CAF50', type: 'solid', width: 2 }},
                    itemStyle: {{ color: '#4CAF50' }},
                    symbol: 'none',
                    silent: true
                }});
            }}
            
            // Add all historical series (including current)
            chartHistory.forEach((h, idx) => {{
                const isCurrent = h.is_current;
                const color = isCurrent ? '#1976D2' : colors[Math.min(idx, colors.length - 2)];
                const lineWidth = isCurrent ? 3 : 1.5;
                const opacity = isCurrent ? 1 : 0.6;
                
                // Prepare data points (mark anomalies)
                let seriesValues = (h.values || []).map((v, i) => {{
                    if (isCurrent && data.anomaly_indices && data.anomaly_indices.includes(i)) {{
                        return {{
                            value: v,
                            itemStyle: {{ color: '#f44336', borderColor: '#f44336', borderWidth: 2 }},
                            symbolSize: 12
                        }};
                    }}
                    return v;
                }});
                
                seriesData.push({{
                    name: h.label,
                    type: 'line',
                    data: seriesValues,
                    lineStyle: {{
                        width: lineWidth,
                        color: color,
                        opacity: opacity
                    }},
                    itemStyle: {{
                        color: color,
                        opacity: opacity
                    }},
                    symbol: 'circle',
                    symbolSize: isCurrent ? 8 : 5,
                    emphasis: {{
                        focus: 'series',
                        lineStyle: {{ width: 3 }},
                        itemStyle: {{ borderWidth: 2, borderColor: '#333' }}
                    }}
                }});
                
                legendItems.push({{
                    label: h.label,
                    timestamp: h.timestamp,
                    color: color,
                    cv: h.cv,
                    consistency: h.consistency,
                    isCurrent: isCurrent,
                    values: h.values
                }});
            }});

            applyChartLayout('detail', maxPoints);
            const detailAxisDensity = buildAxisDensity(maxPoints, 'detail');
            const detailDataZoom = buildCategoryDataZoom(maxPoints, 24);
            const detailValueRange = buildValueAxisRange(
                [
                    chartHistory.map(h => h.values || []),
                    data.hist_stats ? [
                        data.hist_stats.mean,
                        data.hist_stats.upper_2sigma,
                        data.hist_stats.lower_2sigma,
                        data.hist_mean
                    ] : []
                ],
                {{
                    paddingRatio: 0.14,
                    minSpanAbsolute: 0.01,
                    minSpanRatio: 0.25
                }}
            );
            
            // Chart options with improved tooltip showing all series values
            const option = {{
                tooltip: {{
                    trigger: 'axis',
                    formatter: function(params) {{
                        const pointIdx = params[0].dataIndex;
                        let html = `<b>${{params[0].axisValue}}</b><br/>`;
                        params.forEach(p => {{
                            if (p.value !== undefined && p.value !== null) {{
                                const val = typeof p.value === 'object' ? p.value.value : p.value;
                                if (val !== undefined && val !== null) {{
                                    html += `<span style="color:${{p.color}}">●</span> ${{p.seriesName}}: <b>${{typeof val === 'number' ? val.toFixed(4) : val}}</b><br/>`;
                                }}
                            }}
                        }});
                        return html;
                    }}
                }},
                grid: {{
                    left: '3%',
                    right: '4%',
                    bottom: getGridBottom(maxPoints, 'detail'),
                    top: '10%',
                    containLabel: true
                }},
                xAxis: {{
                    type: 'category',
                    data: xLabels,
                    axisLine: {{ lineStyle: {{ color: '#ddd' }} }},
                    axisLabel: {{
                        color: '#666',
                        interval: detailAxisDensity.interval,
                        rotate: detailAxisDensity.rotate,
                        hideOverlap: true,
                        formatter: function(value, index) {{
                            return formatCategoryLabel(value, index, maxPoints, 'detail');
                        }}
                    }}
                }},
                yAxis: {{
                    type: 'value',
                    axisLine: {{ show: false }},
                    splitLine: {{ lineStyle: {{ color: '#eee' }} }},
                    axisLabel: {{ color: '#666' }},
                    scale: true,
                    min: detailValueRange.min,
                    max: detailValueRange.max,
                    boundaryGap: [0, 0]
                }},
                dataZoom: detailDataZoom,
                series: seriesData
            }};
            
            chart.setOption(option, true);
        }}
        
        function updateDataTable(code, data) {{
            const history = data.history || [];
            if (history.length === 0) {{
                document.getElementById('legendItems').innerHTML = '<div style="color: #999; padding: 10px;">No data available</div>';
                return;
            }}
            
            // Find max data points for columns
            let maxPoints = 0;
            history.forEach(h => {{
                if (h.raw_values && h.raw_values.length > maxPoints) maxPoints = h.raw_values.length;
            }});
            
            // Get anomaly indices for current data
            const anomalyIndices = data.anomaly_indices || [];
            
            // Build table header - highlight anomaly columns, use Code_CV Value format (ivy0127)
            let headerHtml = `<th class="filename">Filename</th><th>${{code}}_CV Value</th>`;
            for (let i = 0; i < maxPoints; i++) {{
                const isAnomalyCol = anomalyIndices.includes(i);
                headerHtml += `<th class="${{isAnomalyCol ? 'anomaly-header' : ''}}">Data_${{i + 1}}${{isAnomalyCol ? ' ⚠' : ''}}</th>`;
            }}
            
            // Build table rows
            let rowsHtml = '';
            history.forEach((h, idx) => {{
                const isCurrent = h.is_current;
                const color = isCurrent ? '#1976D2' : colors[Math.min(idx, colors.length - 2)];
                const rowClass = isCurrent ? 'current' : '';
                const cvClass = h.consistency === 'OK' ? 'cv-ok' : (h.consistency === 'NULL' || h.consistency === '-') ? 'cv-null' : 'cv-ng';
                
                // CV display with consistency
                const cvDisplay = h.cv !== null ? `${{h.cv.toFixed(2)}}% (${{h.consistency}})` : `NULL (${{h.consistency}})`;
                
                let rowHtml = `<tr class="${{rowClass}}">`;
                rowHtml += `<td class="filename" title="${{h.label}}">
                    <span style="display: inline-block; width: 12px; height: 12px; background: ${{color}}; border-radius: 2px; margin-right: 6px; vertical-align: middle;"></span>
                    ${{h.label}}${{isCurrent ? ' ★' : ''}}
                </td>`;
                rowHtml += `<td class="${{cvClass}}">${{cvDisplay}}</td>`;
                
                // Data values - highlight anomaly cells for current row
                for (let i = 0; i < maxPoints; i++) {{
                    const val = h.raw_values && h.raw_values[i] !== undefined ? h.raw_values[i] : null;
                    const isAnomaly = isCurrent && anomalyIndices.includes(i);
                    if (val !== null) {{
                        rowHtml += `<td class="${{isAnomaly ? 'anomaly-cell' : ''}}">${{typeof val === 'number' ? val.toFixed(4) : val}}</td>`;
                    }} else {{
                        rowHtml += `<td class="cv-null">NULL</td>`;
                    }}
                }}
                rowHtml += '</tr>';
                rowsHtml += rowHtml;
            }});
            
            // Update legend area with table
            document.getElementById('legendItems').innerHTML = `
                <div class="data-table-container">
                    <table class="data-table">
                        <thead><tr>${{headerHtml}}</tr></thead>
                        <tbody>${{rowsHtml}}</tbody>
                    </table>
                </div>
            `;
        }}
        
        function showSPCChart(code) {{
            const data = kpiData[code];
            if (!data) return;

            if (!spcChart) {{
                const placeholder = document.getElementById('placeholder');
                if (placeholder) {{
                    placeholder.style.display = 'block';
                    placeholder.textContent = 'SPC chart rendering is unavailable, but Data Sources remains available below.';
                }}
                updateDataTable(code, data);
                return;
            }}
            
            const shewhart = data.shewhart_chart;
            
            if (!shewhart || !shewhart.batch_values || shewhart.batch_values.length < 2) {{
                spcChart.setOption({{
                    title: {{
                        text: 'SPC Control Chart (X-bar)',
                        subtext: 'Need at least 2 historical batches to display',
                        left: 'center',
                        top: 'center',
                        textStyle: {{ color: '#999' }}
                    }}
                }}, true);
                return;
            }}
            
            const batchLabels = shewhart.batch_labels || [];
            const batchValues = shewhart.batch_values || [];
            const zones = shewhart.zones || [];
            const ucl = shewhart.ucl;
            const uwl = data.hist_mean !== null && data.hist_std !== null ? data.hist_mean + 2 * data.hist_std : null;
            const cl = shewhart.cl;
            const lwl = data.hist_mean !== null && data.hist_std !== null ? data.hist_mean - 2 * data.hist_std : null;
            const lcl = shewhart.lcl;

            applyChartLayout('spc', batchValues.length);
            const spcAxisDensity = buildAxisDensity(batchValues.length, 'spc');
            const spcDataZoom = buildCategoryDataZoom(batchValues.length, 14);
            const spcValueRange = buildValueAxisRange(
                [batchValues, [ucl, uwl, cl, lwl, lcl]],
                {{
                    paddingRatio: 0.12,
                    minSpanAbsolute: 0.01,
                    minSpanRatio: 0.25
                }}
            );
            
            // Prepare data points with zone colors
            const pointData = batchValues.map((v, i) => {{
                const zone = zones[i] || 'C';
                let color = '#4CAF50';
                let symbolSize = 10;
                
                if (zone === 'OutOfControl') {{
                    color = '#f44336';
                    symbolSize = 14;
                }} else if (zone === 'A') {{
                    color = '#FF9800';
                    symbolSize = 12;
                }} else if (zone === 'B') {{
                    color = '#FFC107';
                }}
                
                const isCurrent = i === batchValues.length - 1;
                
                return {{
                    value: v,
                    itemStyle: {{ color: color, borderWidth: isCurrent ? 3 : 1, borderColor: isCurrent ? '#1976D2' : color }},
                    symbolSize: isCurrent ? symbolSize + 4 : symbolSize,
                    label: {{ show: isCurrent, formatter: v.toFixed(2), position: 'top', fontWeight: 'bold' }}
                }};
            }});
            
            const option = {{
                title: {{
                    text: 'SPC Control Chart (X-bar)',
                    subtext: 'Each point represents one test batch mean',
                    left: 'center'
                }},
                tooltip: {{
                    trigger: 'axis',
                    formatter: function(params) {{
                        const idx = params[0].dataIndex;
                        const zone = zones[idx] || '-';
                        let html = `<b>${{batchLabels[idx]}}</b><br/>`;
                        html += `Mean: <b>${{batchValues[idx].toFixed(4)}}</b><br/>`;
                        html += `Zone: <span style="color: ${{zone === 'OutOfControl' ? '#f44336' : zone === 'A' ? '#FF9800' : '#4CAF50'}}">${{zone}}</span>`;
                        return html;
                    }}
                }},
                grid: {{
                    left: '10%',
                    right: '10%',
                    bottom: getGridBottom(batchValues.length, 'spc'),
                    top: '15%'
                }},
                xAxis: {{
                    type: 'category',
                    data: batchLabels,
                    axisLabel: {{
                        rotate: spcAxisDensity.rotate,
                        interval: spcAxisDensity.interval,
                        fontSize: batchValues.length > 24 ? 9 : 10,
                        hideOverlap: true,
                        formatter: function(value, index) {{
                            return formatCategoryLabel(value, index, batchValues.length, 'spc');
                        }}
                    }}
                }},
                yAxis: {{
                    type: 'value',
                    axisLine: {{ show: true }},
                    splitLine: {{ lineStyle: {{ color: '#eee' }} }},
                    scale: true,
                    min: spcValueRange.min,
                    max: spcValueRange.max,
                    boundaryGap: [0, 0]
                }},
                dataZoom: spcDataZoom,
                series: [
                    {{
                        name: 'Batch Mean',
                        type: 'line',
                        data: pointData,
                        lineStyle: {{ color: '#1976D2', width: 2 }},
                        symbol: 'circle'
                    }},
                    {{
                        name: 'UCL (+3σ)',
                        type: 'line',
                        data: Array(batchValues.length).fill(ucl),
                        lineStyle: {{ color: '#f44336', type: 'dashed', width: 2 }},
                        symbol: 'none',
                        label: {{ show: true, position: 'right', formatter: 'UCL', color: '#f44336' }}
                    }},
                    {{
                        name: 'UWL (+2σ)',
                        type: 'line',
                        data: Array(batchValues.length).fill(uwl),
                        lineStyle: {{ color: '#FF9800', type: 'dotted', width: 1.5 }},
                        symbol: 'none'
                    }},
                    {{
                        name: 'CL (Mean)',
                        type: 'line',
                        data: Array(batchValues.length).fill(cl),
                        lineStyle: {{ color: '#4CAF50', type: 'solid', width: 2 }},
                        symbol: 'none',
                        label: {{ show: true, position: 'right', formatter: 'CL', color: '#4CAF50' }}
                    }},
                    {{
                        name: 'LWL (-2σ)',
                        type: 'line',
                        data: Array(batchValues.length).fill(lwl),
                        lineStyle: {{ color: '#FF9800', type: 'dotted', width: 1.5 }},
                        symbol: 'none'
                    }},
                    {{
                        name: 'LCL (-3σ)',
                        type: 'line',
                        data: Array(batchValues.length).fill(lcl),
                        lineStyle: {{ color: '#f44336', type: 'dashed', width: 2 }},
                        symbol: 'none',
                        label: {{ show: true, position: 'right', formatter: 'LCL', color: '#f44336' }}
                    }}
                ]
            }};
            
            spcChart.setOption(option, true);
        }}
        
        // Show IQR/Distribution Chart with Boxplot (ivy0212 - 使用ECharts原生boxplot)
        function showIQRChart(code) {{
            const data = kpiData[code];
            if (!data) return;
            
            // Collect all values from history batches
            const allValues = [];
            const history = data.history || [];
            
            history.forEach(batch => {{
                if (batch.values && batch.values.length > 0) {{
                    batch.values.forEach(v => allValues.push(v));
                }}
            }});
            
            if (allValues.length < 5) {{
                spcChart.setOption({{
                    title: {{
                        text: 'IQR/Distribution Chart',
                        subtext: 'Need at least 5 data points to display',
                        left: 'center',
                        top: 'center',
                        textStyle: {{ color: '#999' }}
                    }}
                }}, true);
                return;
            }}
            
            // Calculate IQR statistics
            const sorted = [...allValues].sort((a, b) => a - b);
            const n = sorted.length;
            const q1Idx = Math.floor(n * 0.25);
            const q2Idx = Math.floor(n * 0.5);
            const q3Idx = Math.floor(n * 0.75);
            const q1 = sorted[q1Idx];
            const q2 = sorted[q2Idx];  // Median
            const q3 = sorted[q3Idx];
            const iqr = q3 - q1;
            const lowerFence = q1 - 1.5 * iqr;
            const upperFence = q3 + 1.5 * iqr;
            
            // Calculate whiskers (min/max within fences)
            const lowerWhisker = sorted.find(v => v >= lowerFence) || sorted[0];
            const upperWhisker = sorted.slice().reverse().find(v => v <= upperFence) || sorted[n - 1];
            const min = sorted[0];
            const max = sorted[n - 1];
            
            // Current batch values
            const currentBatch = history.find(h => h.is_current);
            const currentValues = currentBatch ? (currentBatch.values || []) : [];
            const currentMean = currentValues.length > 0 ? 
                currentValues.reduce((a, b) => a + b, 0) / currentValues.length : null;
            
            // Separate outliers and normal points
            const outliers = [];
            const normalPoints = [];
            allValues.forEach((v, idx) => {{
                if (v < lowerFence || v > upperFence) {{
                    outliers.push([0, v]);  // [category_index, value]
                }} else {{
                    normalPoints.push([0, v]);
                }}
            }});
            
            const strategy = data.detection_strategy || 'STANDARD_SPC';
            
            // Boxplot data format: [min, Q1, median, Q3, max]
            // 使用whisker而不是绝对min/max来符合标准boxplot定义
            const boxData = [[lowerWhisker, q1, q2, q3, upperWhisker]];
            const iqrValueRange = buildValueAxisRange(
                [
                    allValues,
                    [lowerWhisker, q1, q2, q3, upperWhisker, lowerFence, upperFence, currentMean]
                ],
                {{
                    paddingRatio: 0.16,
                    minSpanAbsolute: 0.01,
                    minSpanRatio: 0.25
                }}
            );

            applyChartLayout('iqr', 1);
            
            const option = {{
                title: {{
                    text: `IQR Boxplot (${{strategy}})`,
                    subtext: `N=${{n}}, Q1=${{q1.toFixed(2)}}, Median=${{q2.toFixed(2)}}, Q3=${{q3.toFixed(2)}}, IQR=${{iqr.toFixed(2)}}`,
                    left: 'center'
                }},
                tooltip: {{
                    trigger: 'item',
                    axisPointer: {{
                        type: 'shadow'
                    }},
                    formatter: function(params) {{
                        if (params.componentSubType === 'boxplot') {{
                            const d = params.data;
                            return `Boxplot:<br/>` +
                                   `Lower Whisker: ${{d[0].toFixed(2)}}<br/>` +
                                   `Q1: ${{d[1].toFixed(2)}}<br/>` +
                                   `Median: ${{d[2].toFixed(2)}}<br/>` +
                                   `Q3: ${{d[3].toFixed(2)}}<br/>` +
                                   `Upper Whisker: ${{d[4].toFixed(2)}}<br/>` +
                                   `IQR: ${{(d[3] - d[1]).toFixed(2)}}`;
                        }} else if (params.componentSubType === 'scatter') {{
                            return `${{params.seriesName}}: ${{params.value[1].toFixed(4)}}`;
                        }}
                        return '';
                    }}
                }},
                grid: {{
                    left: '15%',
                    right: '15%',
                    bottom: '15%',
                    top: '20%',
                    containLabel: true
                }},
                xAxis: {{
                    type: 'category',
                    data: ['All Data'],
                    boundaryGap: true,
                    nameGap: 30,
                    splitArea: {{
                        show: false
                    }},
                    splitLine: {{
                        show: false
                    }}
                }},
                yAxis: {{
                    type: 'value',
                    name: 'Value',
                    scale: true,
                    min: iqrValueRange.min,
                    max: iqrValueRange.max,
                    splitArea: {{
                        show: true
                    }}
                }},
                series: [
                    {{
                        name: 'Boxplot',
                        type: 'boxplot',
                        data: boxData,
                        itemStyle: {{
                            color: '#4CAF50',
                            borderColor: '#2E7D32',
                            borderWidth: 2
                        }},
                        boxWidth: [10, 50],  // [min_width, max_width]
                        tooltip: {{
                            formatter: function(param) {{
                                return [
                                    'Boxplot Statistics:',
                                    'Upper Whisker: ' + param.data[4].toFixed(2),
                                    'Q3 (75%): ' + param.data[3].toFixed(2),
                                    'Median (Q2): ' + param.data[2].toFixed(2),
                                    'Q1 (25%): ' + param.data[1].toFixed(2),
                                    'Lower Whisker: ' + param.data[0].toFixed(2),
                                    'IQR (Q3-Q1): ' + (param.data[3] - param.data[1]).toFixed(2)
                                ].join('<br/>');
                            }}
                        }}
                    }},
                    {{
                        name: 'Outliers',
                        type: 'scatter',
                        data: outliers,
                        symbolSize: 8,
                        itemStyle: {{
                            color: '#f44336',
                            opacity: 0.7
                        }},
                        emphasis: {{
                            itemStyle: {{
                                opacity: 1,
                                borderColor: '#d32f2f',
                                borderWidth: 2
                            }}
                        }}
                    }},
                    {{
                        name: 'Normal Points',
                        type: 'scatter',
                        data: normalPoints,
                        symbolSize: 4,
                        itemStyle: {{
                            color: '#2196F3',
                            opacity: 0.3
                        }},
                        emphasis: {{
                            itemStyle: {{
                                opacity: 0.8
                            }}
                        }}
                    }}
                ],
                graphic: [
                    {{
                        type: 'text',
                        right: 20,
                        top: 80,
                        style: {{
                            text: [
                                `Detection: ${{strategy}}`,
                                `Total Points: ${{n}}`,
                                `Outliers: ${{outliers.length}} (${{(outliers.length/n*100).toFixed(1)}}%)`,
                                `Range: [${{min.toFixed(2)}}, ${{max.toFixed(2)}}]`,
                                `Fences: [${{lowerFence.toFixed(2)}}, ${{upperFence.toFixed(2)}}]`,
                                currentMean !== null ? `Current Mean: ${{currentMean.toFixed(4)}}` : ''
                            ].filter(s => s).join('\\n'),
                            fill: '#666',
                            fontSize: 11,
                            lineHeight: 16
                        }}
                    }},
                    {{
                        type: 'text',
                        left: 20,
                        bottom: 30,
                        style: {{
                            text: '💡 Q1/Q3 线显示为箱体边界',
                            fill: '#999',
                            fontSize: 10
                        }}
                    }}
                ]
            }};
            
            spcChart.setOption(option, true);
        }}
        
        // Filter functions
        function filterList() {{
            const keyword = document.getElementById('searchBox').value.toLowerCase();
            document.querySelectorAll('.kpi-item').forEach(item => {{
                const code = item.dataset.code;
                const data = kpiData[code];
                const codeLower = code.toLowerCase();
                const kpiName = (data?.kpi_name || '').toLowerCase();
                const severity = item.dataset.severity || '';
                const type = item.dataset.type || '';
                const consistency = data?.consistency || '';
                const anomalyCount = data?.anomaly_count || 0;
                const kpiType = data?.kpi_type || 'unknown';
                
                let visible = codeLower.includes(keyword) || kpiName.includes(keyword);
                
                // Severity filter
                if (visible && currentSeverityFilter !== 'all') {{
                    visible = severity === currentSeverityFilter;
                }}
                
                // Type filter (KPI/Counter/Other)
                if (visible && currentTypeFilter !== 'all') {{
                    if (currentTypeFilter === 'KPI') {{
                        visible = isKPICode(code);
                    }} else if (currentTypeFilter === 'Counter') {{
                        visible = isCounterCode(code);
                    }} else if (currentTypeFilter === 'Other') {{
                        visible = !isKPICode(code) && !isCounterCode(code);
                    }}
                }}
                
                // KPI Type filter (ceiling_saturated, count_type, etc.)
                if (visible && currentKpiTypeFilter !== 'all') {{
                    visible = kpiType === currentKpiTypeFilter;
                }}
                
                // Advanced filters - Anomaly
                if (visible && advancedFilters.hasAnomaly) {{
                    const threshold = advancedFilters.anomalyThreshold;
                    // A:x - exact match: anomalyCount === threshold
                    visible = anomalyCount === threshold;
                }}
                if (visible && advancedFilters.excludeNull) {{
                    visible = consistency !== 'NULL' && consistency.toLowerCase() !== 'null';
                }}
                if (visible && advancedFilters.excludePartialNull) {{
                    visible = !consistency.toLowerCase().includes('partial') && !consistency.toLowerCase().includes('null');
                }}
                if (visible && advancedFilters.onlyInconsistent) {{
                    visible = consistency === 'Inconsistent' || consistency === 'NG';
                }}
                // Guard Rails filter (ivy0127)
                if (visible && advancedFilters.hasGuardRail) {{
                    const kData = kpiData[code];
                    const grViolations = kData?.guard_rail_violations || '';
                    visible = grViolations && grViolations.length > 0;
                }}
                
                item.style.display = visible ? 'flex' : 'none';
            }});
            
            // Update visible count in severity groups
            updateVisibleCounts();
            
            // Auto-select if only one item visible
            const visibleItems = Array.from(document.querySelectorAll('.kpi-item')).filter(
                item => item.style.display !== 'none'
            );
            if (visibleItems.length === 1) {{
                showChart(visibleItems[0].dataset.code);
            }}
        }}
        
        function updateVisibleCounts() {{
            document.querySelectorAll('.severity-group').forEach(group => {{
                const visibleItems = group.querySelectorAll('.kpi-item[style*="flex"], .kpi-item:not([style*="display"])').length;
                const header = group.querySelector('.severity-header');
                if (header) {{
                    const originalText = header.textContent.split('(')[0].trim();
                    const totalItems = group.querySelectorAll('.kpi-item').length;
                    header.textContent = `${{originalText}} (${{visibleItems}}/${{totalItems}})`;
                }}
            }});
        }}
        
        // Anomaly filter dropdown functions
        function initAnomalyDropdown() {{
            // Scan all KPI data to find anomaly distribution
            const anomalyCounts = {{}};  // count -> number of KPIs with exactly this many anomalies
            let maxAnomaly = 0;
            let maxTotalPoints = 0;
            
            Object.keys(kpiData).forEach(code => {{
                const data = kpiData[code];
                const anomalyCount = data.anomaly_count || 0;
                const totalPoints = data.total_points || 0;
                
                if (anomalyCount > 0) {{
                    anomalyCounts[anomalyCount] = (anomalyCounts[anomalyCount] || 0) + 1;
                    if (anomalyCount > maxAnomaly) maxAnomaly = anomalyCount;
                }}
                if (totalPoints > maxTotalPoints) maxTotalPoints = totalPoints;
            }});
            
            // Build dropdown HTML
            const dropdown = document.getElementById('anomalyDropdown');
            let html = '';
            
            // "Any (off)" option
            html += `<div class="anomaly-dropdown-item active" data-threshold="0" onclick="setAnomalyThreshold(0, event)">Any (off)</div>`;
            
            // Generate A:n options in DESCENDING order (from maxTotalPoints to 1)
            for (let i = maxTotalPoints; i >= 1; i--) {{
                const count = anomalyCounts[i] || 0;
                const countStr = count > 0 ? `(${{count}})` : '';
                html += `<div class="anomaly-dropdown-item" data-threshold="${{i}}" onclick="setAnomalyThreshold(${{i}}, event)">A:${{i}} ${{countStr}}</div>`;
            }}
            
            // Removed "All Anomaly" option - redundant with A:maxpoints
            
            dropdown.innerHTML = html;
        }}
        
        function toggleAnomalyDropdown(event) {{
            event.stopPropagation();
            const dropdown = document.getElementById('anomalyDropdown');
            dropdown.classList.toggle('show');
        }}
        
        function setAnomalyThreshold(threshold, event) {{
            advancedFilters.anomalyThreshold = threshold;
            advancedFilters.hasAnomaly = threshold !== 0;
            
            // Update chip display
            const chip = document.getElementById('anomalyFilterChip');
            if (threshold === 0) {{
                chip.innerHTML = 'Anomaly (off) <span class="shortcut-hint">(N)</span>';
                chip.classList.remove('active');
            }} else {{
                chip.innerHTML = `A:${{threshold}} <span class="shortcut-hint">(N)</span>`;
                chip.classList.add('active');
            }}
            
            // Update dropdown active state
            document.querySelectorAll('.anomaly-dropdown-item').forEach(item => {{
                item.classList.remove('active');
            }});
            if (event && event.target) {{
                event.target.classList.add('active');
            }} else {{
                // Find and activate the correct item
                document.querySelectorAll('.anomaly-dropdown-item').forEach(item => {{
                    if (parseInt(item.dataset.threshold) === threshold) {{
                        item.classList.add('active');
                    }}
                }});
            }}
            
            // Close dropdown
            document.getElementById('anomalyDropdown').classList.remove('show');
            
            filterList();
        }}
        
        function cycleAnomalyFilter() {{
            // Get all available thresholds from dropdown
            const items = document.querySelectorAll('.anomaly-dropdown-item');
            const thresholds = Array.from(items).map(item => parseInt(item.dataset.threshold));
            
            const currentThreshold = advancedFilters.anomalyThreshold;
            const currentIndex = thresholds.indexOf(currentThreshold);
            const nextIndex = (currentIndex + 1) % thresholds.length;
            const newThreshold = thresholds[nextIndex];
            
            advancedFilters.anomalyThreshold = newThreshold;
            advancedFilters.hasAnomaly = newThreshold !== 0;
            
            // Update chip display
            const chip = document.getElementById('anomalyFilterChip');
            if (newThreshold === 0) {{
                chip.innerHTML = 'Anomaly (off) <span class="shortcut-hint">(N)</span>';
                chip.classList.remove('active');
            }} else {{
                chip.innerHTML = `A:${{newThreshold}} <span class="shortcut-hint">(N)</span>`;
                chip.classList.add('active');
            }}
            
            // Update dropdown active state
            document.querySelectorAll('.anomaly-dropdown-item').forEach(item => {{
                const itemThreshold = parseInt(item.dataset.threshold);
                item.classList.toggle('active', itemThreshold === newThreshold);
            }});
            
            filterList();
        }}
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {{
            const dropdown = document.getElementById('anomalyDropdown');
            const container = document.querySelector('.anomaly-filter-container');
            if (dropdown && container && !container.contains(e.target)) {{
                dropdown.classList.remove('show');
            }}
        }});
        
        function toggleAdvancedFilter(filterName) {{
            advancedFilters[filterName] = !advancedFilters[filterName];
            
            // Update UI
            const chip = document.querySelector(`[data-filter="${{filterName}}"]`);
            if (chip) {{
                chip.classList.toggle('active', advancedFilters[filterName]);
            }}
            
            filterList();
        }}
        
        function filterBySeverity(severity) {{
            currentSeverityFilter = severity;
            
            document.querySelectorAll('.summary-item').forEach(btn => btn.classList.remove('active'));
            
            if (severity === 'all') {{
                document.querySelector('.summary-item.all').classList.add('active');
            }} else if (severity === 'Regression') {{
                document.querySelector('.summary-item.regression').classList.add('active');
            }} else if (severity === 'Suspicious') {{
                document.querySelector('.summary-item.suspicious').classList.add('active');
            }} else if (severity === 'Normal') {{
                document.querySelector('.summary-item.normal').classList.add('active');
            }} else if (severity === 'NoHistory') {{
                document.querySelector('.summary-item.no-history').classList.add('active');
            }}
            
            filterList();
        }}
        
        function filterByType(type) {{
            currentTypeFilter = type;
            currentKpiTypeFilter = 'all';  // Reset KPI type filter
            
            document.querySelectorAll('.type-btn').forEach(btn => btn.classList.remove('active'));
            
            if (type === 'all') {{
                document.querySelector('.type-btn.all').classList.add('active');
            }} else if (type === 'KPI') {{
                document.querySelector('.type-btn.kpi').classList.add('active');
            }} else if (type === 'Counter') {{
                document.querySelector('.type-btn.counter').classList.add('active');
            }} else if (type === 'Other') {{
                document.querySelector('.type-btn.other').classList.add('active');
            }}
            
            filterList();
        }}
        
        // KPI Type filter (ivy0126)
        let currentKpiTypeFilter = 'all';
        
        function filterByKpiType(kpiType) {{
            currentKpiTypeFilter = currentKpiTypeFilter === kpiType ? 'all' : kpiType;
            
            document.querySelectorAll('.type-btn[data-kpi-type]').forEach(btn => {{
                btn.classList.toggle('active', btn.dataset.kpiType === currentKpiTypeFilter);
            }});
            
            filterList();
        }}
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {{
            if (e.target.tagName === 'INPUT') {{
                if (e.key === 'Escape') {{
                    e.target.blur();
                }}
                return;
            }}
            
            switch(e.key.toLowerCase()) {{
                case '/':
                    e.preventDefault();
                    document.getElementById('searchBox').focus();
                    break;
                case 'k':
                    filterByType('KPI');
                    break;
                case 'c':
                    filterByType('Counter');
                    break;
                case 'o':
                    filterByType('Other');
                    break;
                case 'a':
                    filterByType('all');
                    break;
                case '1':
                    switchChartType('detail');
                    break;
                case '2':
                    switchChartType('spc');
                    break;
                case '3':
                    switchChartType('iqr');
                    break;
                case 'n':
                    // Cycle through anomaly filter: off → ≥1 → all anomaly → off
                    cycleAnomalyFilter();
                    break;
                case 'x':
                    toggleAdvancedFilter('excludeNull');
                    break;
                case 'p':
                    toggleAdvancedFilter('excludePartialNull');
                    break;
                case 'i':
                    toggleAdvancedFilter('onlyInconsistent');
                    break;
                case 'g':
                    toggleAdvancedFilter('hasGuardRail');
                    break;
                case 'h':
                    showHelp();
                    break;
                case 'arrowdown':
                    e.preventDefault();
                    navigateList(1);
                    break;
                case 'arrowup':
                    e.preventDefault();
                    navigateList(-1);
                    break;
                case 'enter':
                    // Select current item if navigating
                    const activeItem = document.querySelector('.kpi-item.active');
                    if (activeItem) {{
                        showChart(activeItem.dataset.code);
                    }}
                    break;
            }}
        }});
        
        // Navigate through visible KPI list items
        function navigateList(direction) {{
            const visibleItems = Array.from(document.querySelectorAll('.kpi-item')).filter(
                item => item.style.display !== 'none'
            );
            if (visibleItems.length === 0) return;
            
            const currentActive = document.querySelector('.kpi-item.active');
            let currentIndex = currentActive ? visibleItems.indexOf(currentActive) : -1;
            
            // Calculate new index
            let newIndex = currentIndex + direction;
            if (newIndex < 0) newIndex = visibleItems.length - 1;
            if (newIndex >= visibleItems.length) newIndex = 0;
            
            // Select new item
            const newItem = visibleItems[newIndex];
            if (newItem) {{
                showChart(newItem.dataset.code);
                // Scroll into view
                newItem.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
            }}
        }}
        
        function showHelp() {{
            alert(`Keyboard Shortcuts:
            
Navigation:
↑/↓ - Navigate KPI list
Enter - Select current item
/ - Focus search box

Type Filters:
K - Filter KPI only
C - Filter Counter only  
A - Show all types

Chart Views:
1 - Data Detail Chart
2 - SPC Control Chart
3 - IQR/Distribution Chart

Advanced Filters:
N - Cycle Anomaly filter (A:n - exact match)
G - GR Triggered (show Guard Rails violations)
X - Exclude NULL (hide NULL data)
P - Exclude Partial NULL (hide partial null data)
I - Only Inconsistent (show only CV inconsistent items)

Visual Indicators in KPI List:
● Green dot - Consistent (CV OK)
● Red dot - Inconsistent (CV NG)
○ Gray dot - NULL data
A:n - Anomaly count badge

SPC Control Rules:
Rule 1 - One point beyond 3σ (Zone A)
Rule 2 - 2 of 3 points in Zone A or beyond (same side)
Rule 3 - 4 of 5 points in Zone B or beyond (same side)
Rule 4 - 8+ consecutive points on one side of center
Rule 5 - 6+ consecutive points trending (increasing/decreasing)
Rule 6 - 15 consecutive points in Zone C (both sides)
Rule 7 - 14 consecutive alternating points (up/down)
Rule 8 - 8 consecutive points outside Zone C (both sides)

H - Show this help
M - Manage history records`);
        }}
        
        // History Management Functions
        let historyRecords = [];
        let selectedHistoryIndices = new Set();
        
        function openHistoryModal() {{
            // Populate history list from kpiData
            populateHistoryList();
            document.getElementById('historyModal').classList.add('active');
        }}
        
        function closeHistoryModal() {{
            document.getElementById('historyModal').classList.remove('active');
            document.getElementById('commandOutput').classList.remove('show');
        }}
        
        function populateHistoryList() {{
            // Extract history records from kpiData
            historyRecords = [];
            const seen = new Set();
            
            // Get the first KPI that has history data
            for (const code in kpiData) {{
                const data = kpiData[code];
                if (data.history && data.history.length > 0) {{
                    data.history.forEach(h => {{
                        const key = h.timestamp || h.label;
                        if (!seen.has(key)) {{
                            seen.add(key);
                            historyRecords.push({{
                                timestamp: h.timestamp,
                                label: h.label,
                                is_current: h.is_current,
                                index: historyRecords.length
                            }});
                        }}
                    }});
                    break;  // Only need history from one KPI
                }}
            }}
            
            // Sort by timestamp (oldest first)
            historyRecords.sort((a, b) => {{
                if (a.timestamp && b.timestamp) {{
                    return a.timestamp.localeCompare(b.timestamp);
                }}
                return 0;
            }});
            
            // Render list
            const listEl = document.getElementById('historyList');
            if (historyRecords.length === 0) {{
                listEl.innerHTML = '<div style="color:#999; padding:20px; text-align:center;">No history records found</div>';
                return;
            }}
            
            listEl.innerHTML = historyRecords.map((h, idx) => `
                <div class="history-item ${{h.is_current ? 'current' : ''}}" data-index="${{idx}}">
                    <input type="checkbox" class="history-checkbox" id="hist_${{idx}}" 
                           onchange="toggleHistorySelection(${{idx}})" ${{h.is_current ? 'disabled' : ''}}>
                    <div class="history-info">
                        <div class="history-filename">${{h.label}}</div>
                        <div class="history-time">${{h.timestamp || 'No timestamp'}}</div>
                    </div>
                    ${{h.is_current ? '<span class="history-badge current">Current</span>' : ''}}
                </div>
            `).join('');
            
            updateSelectedCount();
        }}
        
        function toggleHistorySelection(idx) {{
            if (selectedHistoryIndices.has(idx)) {{
                selectedHistoryIndices.delete(idx);
            }} else {{
                selectedHistoryIndices.add(idx);
            }}
            updateSelectedCount();
        }}
        
        function selectAllHistory() {{
            historyRecords.forEach((h, idx) => {{
                if (!h.is_current) {{
                    selectedHistoryIndices.add(idx);
                    const checkbox = document.getElementById(`hist_${{idx}}`);
                    if (checkbox) checkbox.checked = true;
                }}
            }});
            updateSelectedCount();
        }}
        
        function deselectAllHistory() {{
            selectedHistoryIndices.clear();
            historyRecords.forEach((h, idx) => {{
                const checkbox = document.getElementById(`hist_${{idx}}`);
                if (checkbox) checkbox.checked = false;
            }});
            updateSelectedCount();
        }}
        
        function updateSelectedCount() {{
            document.getElementById('selectedCount').textContent = `${{selectedHistoryIndices.size}} selected`;
        }}
        
        function generateDeleteCommand() {{
            if (selectedHistoryIndices.size === 0) {{
                alert('Please select at least one record to delete');
                return;
            }}
            
            // Get selected timestamps
            const timestamps = [];
            selectedHistoryIndices.forEach(idx => {{
                const record = historyRecords[idx];
                if (record && record.timestamp) {{
                    timestamps.push(record.timestamp);
                }}
            }});
            
            if (timestamps.length === 0) {{
                alert('Selected records have no valid timestamps');
                return;
            }}
            
            // Generate command
            const commands = timestamps.map(ts => 
                `python scripts/manage_history.py --delete "${{ts}}"`
            ).join('\\n');
            
            const fullCommand = `# Run in project directory (251224_KPI_consistency)\\n# To delete ${{timestamps.length}} selected record(s):\\n\\n${{commands}}\\n\\n# Or use interactive mode:\\npython scripts/manage_history.py --interactive`;
            
            // Show command
            const outputEl = document.getElementById('commandOutput');
            outputEl.textContent = fullCommand;
            outputEl.classList.add('show');
            
            // Copy to clipboard
            navigator.clipboard.writeText(commands).then(() => {{
                alert(`Command copied to clipboard!\\n\\nRun in terminal to delete ${{timestamps.length}} record(s).\\nAfter deletion, re-run analysis to update reports.`);
            }}).catch(err => {{
                console.error('Failed to copy: ', err);
                alert('Command generated! Please copy it manually from the output area below.');
            }});
        }}
        
        // Add M keyboard shortcut
        document.addEventListener('keydown', function(e) {{
            if (e.target.tagName === 'INPUT') return;
            if (e.key.toLowerCase() === 'm') {{
                openHistoryModal();
            }}
            if (e.key === 'Escape') {{
                closeHistoryModal();
            }}
        }});
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            initChart();
            initLegendPanel();
            initAnomalyDropdown();

            const visibleItems = Array.from(document.querySelectorAll('.kpi-item')).filter(
                item => item.style.display !== 'none'
            );
            if (visibleItems.length === 1) {{
                showChart(visibleItems[0].dataset.code);
            }}
        }});
    </script>
</body>
</html>
'''
        return html
    
    def _generate_kpi_list_html(self, all_codes_df: pd.DataFrame) -> str:
        """Generate HTML for KPI list grouped by severity"""
        if all_codes_df.empty:
            return '<div class="severity-group"><div class="severity-header" style="background: #999">No Data</div></div>'
        
        severity_order = ['Regression', 'Suspicious', 'Normal', 'NoHistory']
        severity_colors = {
            'Regression': '#f44336',
            'Suspicious': '#FF9800',
            'Normal': '#4CAF50',
            'NoHistory': '#9E9E9E'
        }
        
        html_parts = []
        
        for severity in severity_order:
            subset = all_codes_df[all_codes_df['Severity'] == severity]
            if subset.empty:
                continue
            
            # Sort by sigma level descending
            if 'Sigma_Level' in subset.columns:
                subset = subset.sort_values('Sigma_Level', ascending=False, na_position='last')
            
            color = severity_colors.get(severity, '#999')
            count = len(subset)
            
            items_html = []
            for _, row in subset.iterrows():
                code = row.get('Code', '')
                code_type = row.get('Type', 'Other')
                sigma = row.get('Sigma_Level')
                consistency = row.get('Consistency', '-')
                anomaly_count = row.get('Anomaly_Count', 0)
                total_points = row.get('Total_Points', 0)
                kpi_type = row.get('KPI_Type', 'unknown')  # Get KPI type for filtering
                sigma_str = f'σ={sigma:.1f}' if sigma is not None and not np.isnan(sigma) else 'σ=-'
                
                # Add consistency and anomaly indicators
                consistency_indicator = ''
                if 'NULL' in str(consistency).upper():
                    consistency_indicator = '<span style="color:#9e9e9e;font-size:10px;">⚪</span>'
                elif consistency == 'Inconsistent' or consistency == 'NG':
                    consistency_indicator = '<span style="color:#f44336;font-size:10px;">●</span>'
                else:
                    consistency_indicator = '<span style="color:#4caf50;font-size:10px;">●</span>'
                
                anomaly_indicator = ''
                if anomaly_count and anomaly_count > 0:
                    # Check if all points are anomalies
                    if total_points > 0 and anomaly_count >= total_points:
                        anomaly_indicator = f'<span class="all-anomaly-badge" title="All {int(total_points)} points are anomalies">⚠️ ALL</span>'
                    else:
                        anomaly_indicator = f'<span style="color:#f44336;font-size:10px;margin-left:3px;">A:{int(anomaly_count)}</span>'
                
                items_html.append(f'''
                    <div class="kpi-item" onclick="showChart('{code}')" data-code="{code}" data-severity="{severity}" data-type="{code_type}" data-consistency="{consistency}" data-kpi-type="{kpi_type}">
                        <span class="code">{consistency_indicator} {code}{anomaly_indicator}</span>
                        <span class="type">[{code_type}] {sigma_str}</span>
                    </div>
                ''')
            
            html_parts.append(f'''
                <div class="severity-group">
                    <div class="severity-header" style="background-color: {color}">
                        {severity} ({count})
                    </div>
                    <div class="severity-items">
                        {"".join(items_html)}
                    </div>
                </div>
            ''')
        
        return "".join(html_parts)
    
    def _calculate_statistics(self, consistency_df: pd.DataFrame, 
                              suspicious_df: pd.DataFrame,
                              all_codes_df: pd.DataFrame) -> Dict[str, int]:
        """Calculate summary statistics"""
        stats = {
            'total': 0,
            'regression': 0,
            'suspicious': 0,
            'normal': 0,
            'nohistory': 0
        }
        
        if not all_codes_df.empty:
            stats['total'] = len(all_codes_df)
            stats['regression'] = int((all_codes_df['Severity'] == 'Regression').sum())
            stats['suspicious'] = int((all_codes_df['Severity'] == 'Suspicious').sum())
            stats['normal'] = int((all_codes_df['Severity'] == 'Normal').sum())
            stats['nohistory'] = int((all_codes_df['Severity'] == 'NoHistory').sum())
        
        return stats
