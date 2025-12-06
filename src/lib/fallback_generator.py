"""
Fallback Insight Generator

Responsibilities:
- Generate deterministic, template-based insights when LLM fails
- Produce safe insights with evidence drawn strictly from KPIs and cleanedPreview
- Cover common patterns: missing values, outliers, correlations, duplicates
- Ensure all evidence is valid and verifiable
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generate_fallback_insights(compact_eda: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate deterministic template-based insights from compact EDA.
    
    Creates 1-3 safe insights based on:
    - Missing data percentage
    - Duplicate rows
    - Numeric outliers (max/min ratio)
    - Strong correlations
    
    Args:
        compact_eda: Compact EDA JSON with kpis, schema, cleanedPreview, chartSpecs
        
    Returns:
        Dictionary matching insight schema with template-generated content
    """
    logger.info("Generating fallback insights (deterministic templates)")
    
    kpis = compact_eda.get('kpis', {})
    schema = compact_eda.get('schema', [])
    cleaned_preview = compact_eda.get('cleanedPreview', [])
    chart_specs = compact_eda.get('chartSpecs', [])
    
    insights = []
    insight_counter = 1
    
    # 1. Missing Data Insight
    missing_insight = _generate_missing_data_insight(kpis, schema, insight_counter)
    if missing_insight:
        insights.append(missing_insight)
        insight_counter += 1
    
    # 2. Duplicate Rows Insight
    duplicate_insight = _generate_duplicate_insight(kpis, insight_counter)
    if duplicate_insight:
        insights.append(duplicate_insight)
        insight_counter += 1
    
    # 3. Outlier Insight
    outlier_insight = _generate_outlier_insight(kpis, cleaned_preview, chart_specs, insight_counter)
    if outlier_insight:
        insights.append(outlier_insight)
        insight_counter += 1
    
    # 4. Correlation Insight
    correlation_insight = _generate_correlation_insight(compact_eda, chart_specs, insight_counter)
    if correlation_insight:
        insights.append(correlation_insight)
        insight_counter += 1
    
    # Business Summary
    business_summary = _generate_business_summary(kpis, len(insights))
    
    return {
        "analystInsights": insights,
        "businessSummary": business_summary,
        "visualActions": [],
        "metadata": {
            "total_insights": len(insights),
            "confidence": "low",
            "data_quality_score": _calculate_quality_score(kpis),
            "analysis_timestamp": ""
        },
        "issues": ["llm_fallback_used"],
        "_meta": {
            "model": "fallback-deterministic",
            "latency_seconds": 0.0,
            "timestamp": 0
        }
    }


def _generate_missing_data_insight(kpis: Dict, schema: List[Dict], insight_id: int) -> Dict[str, Any]:
    """Generate insight about missing data if significant."""
    row_count = kpis.get('rowCount', 0)
    col_count = kpis.get('columnCount', 0)
    missing_cells = kpis.get('missingCells', 0)
    
    if row_count == 0 or col_count == 0:
        return None
    
    total_cells = row_count * col_count
    missing_pct = (missing_cells / total_cells) * 100 if total_cells > 0 else 0
    
    # Only create insight if missing > 1%
    if missing_pct < 1:
        return None
    
    # Find column with most missing values
    max_missing_col = None
    max_missing_count = 0
    for col in schema:
        missing = col.get('missing', 0)
        if missing > max_missing_count:
            max_missing_count = missing
            max_missing_col = col.get('column', 'Unknown')
    
    severity = 'high' if missing_pct > 10 else 'medium' if missing_pct > 5 else 'low'
    
    text = f"Missing data detected: {missing_cells} cells ({missing_pct:.1f}%) are missing across the dataset. "
    if max_missing_col:
        col_missing_pct = (max_missing_count / row_count) * 100 if row_count > 0 else 0
        text += f"Column '{max_missing_col}' has the highest missing rate at {col_missing_pct:.1f}% ({max_missing_count} of {row_count} rows). "
    text += "This may impact analysis accuracy and should be investigated."
    
    return {
        "id": f"i{insight_id}",
        "text": text,
        "severity": severity,
        "category": "missing_data",
        "evidence": {
            "aggregates": {
                "Total Cells": total_cells,
                "Missing Cells": missing_cells,
                "Missing %": round(missing_pct, 2)
            },
            "row_indices": [],
            "chart_id": None
        },
        "recommendation": {
            "who": "data_engineer",
            "what": f"Investigate source of missing values in {max_missing_col if max_missing_col else 'affected columns'} and implement data quality checks",
            "priority": "high" if missing_pct > 10 else "medium"
        }
    }


def _generate_duplicate_insight(kpis: Dict, insight_id: int) -> Dict[str, Any]:
    """Generate insight about duplicate rows if present."""
    row_count = kpis.get('rowCount', 0)
    duplicate_rows = kpis.get('duplicateRows', 0)
    
    if duplicate_rows == 0 or row_count == 0:
        return None
    
    duplicate_pct = (duplicate_rows / row_count) * 100
    
    # Only create insight if duplicates > 1%
    if duplicate_pct < 1:
        return None
    
    severity = 'high' if duplicate_pct > 10 else 'medium' if duplicate_pct > 5 else 'low'
    
    text = f"Duplicate rows detected: {duplicate_rows} exact duplicate records found ({duplicate_pct:.1f}% of dataset). "
    text += "Duplicates can inflate aggregate metrics and may indicate ETL pipeline issues or double-entry in source systems. "
    text += "Recommend implementing deduplication logic before analysis."
    
    return {
        "id": f"i{insight_id}",
        "text": text,
        "severity": severity,
        "category": "duplicate",
        "evidence": {
            "aggregates": {
                "Total Rows": row_count,
                "Duplicate Rows": duplicate_rows,
                "Duplicate %": round(duplicate_pct, 2)
            },
            "row_indices": [],
            "chart_id": None
        },
        "recommendation": {
            "who": "data_engineer",
            "what": "Implement deduplication logic in ETL pipeline and investigate root cause in source system",
            "priority": "high" if duplicate_pct > 10 else "medium"
        }
    }


def _generate_outlier_insight(kpis: Dict, cleaned_preview: List[Dict], 
                               chart_specs: List[Dict], insight_id: int) -> Dict[str, Any]:
    """Generate insight about numeric outliers if detected."""
    numeric_stats = kpis.get('numericStats', {})
    
    for col_name, stats in numeric_stats.items():
        min_val = stats.get('min', 0)
        max_val = stats.get('max', 0)
        mean_val = stats.get('mean', 0)
        median_val = stats.get('median', 0)
        
        # Check for outliers: max/min ratio > 10
        if min_val > 0 and max_val / min_val > 10:
            ratio = max_val / min_val
            
            # Find row index with max value
            max_row_idx = None
            for idx, row in enumerate(cleaned_preview):
                if row.get(col_name) == max_val:
                    max_row_idx = idx
                    break
            
            # Find chart_id if exists
            chart_id = None
            for chart in chart_specs:
                if chart.get('y') == col_name or chart.get('x') == col_name:
                    chart_id = chart.get('id')
                    break
            
            text = f"Potential outlier detected in '{col_name}': Maximum value ({max_val:,.0f}) is {ratio:.1f}x the minimum value ({min_val:,.0f}). "
            text += f"This is significantly higher than the median ({median_val:,.0f}). "
            text += "Verify whether this represents a legitimate extreme value or a data quality issue."
            
            return {
                "id": f"i{insight_id}",
                "text": text,
                "severity": "medium",
                "category": "outlier",
                "evidence": {
                    "aggregates": {
                        f"{col_name} Max": max_val,
                        f"{col_name} Min": min_val,
                        f"{col_name} Median": median_val,
                        "Max/Min Ratio": round(ratio, 2)
                    },
                    "row_indices": [max_row_idx] if max_row_idx is not None else [],
                    "chart_id": chart_id
                },
                "recommendation": {
                    "who": "analyst",
                    "what": f"Investigate extreme value in '{col_name}' to determine if it's valid or requires correction",
                    "priority": "medium"
                }
            }
    
    return None


def _generate_correlation_insight(compact_eda: Dict, chart_specs: List[Dict], 
                                   insight_id: int) -> Dict[str, Any]:
    """Generate insight about strong correlations if present."""
    correlations = compact_eda.get('correlations', [])
    
    for corr in correlations:
        col1 = corr.get('col1', '')
        col2 = corr.get('col2', '')
        r = corr.get('r', 0)
        
        # Only report strong correlations (|r| > 0.7)
        if abs(r) > 0.7:
            direction = "positive" if r > 0 else "negative"
            strength = "very strong" if abs(r) > 0.9 else "strong"
            
            # Find relevant chart
            chart_id = None
            for chart in chart_specs:
                if (chart.get('x') in [col1, col2] and chart.get('y') in [col1, col2]):
                    chart_id = chart.get('id')
                    break
            
            text = f"{strength.capitalize()} {direction} correlation detected between '{col1}' and '{col2}' (r={r:.2f}). "
            text += "This relationship may indicate causal connection, shared underlying factors, or opportunity for predictive modeling. "
            text += "Further statistical analysis recommended to understand the nature of this relationship."
            
            return {
                "id": f"i{insight_id}",
                "text": text,
                "severity": "low",
                "category": "correlation",
                "evidence": {
                    "aggregates": {
                        "Correlation Coefficient": round(r, 3),
                        "Column 1": col1,
                        "Column 2": col2
                    },
                    "row_indices": [],
                    "chart_id": chart_id
                },
                "recommendation": {
                    "who": "data_scientist",
                    "what": f"Analyze relationship between '{col1}' and '{col2}' to determine causality and potential for predictive modeling",
                    "priority": "medium"
                }
            }
    
    return None


def _generate_business_summary(kpis: Dict, insight_count: int) -> List[str]:
    """Generate template business summary points."""
    row_count = kpis.get('rowCount', 0)
    col_count = kpis.get('columnCount', 0)
    
    summary = [
        f"Dataset contains {row_count:,} rows and {col_count} columns. Automated analysis generated {insight_count} insights using deterministic templates."
    ]
    
    # Add quality note
    missing_cells = kpis.get('missingCells', 0)
    duplicate_rows = kpis.get('duplicateRows', 0)
    
    if missing_cells == 0 and duplicate_rows == 0:
        summary.append("Data quality is excellent with no missing values or duplicate records detected.")
    else:
        quality_issues = []
        if missing_cells > 0:
            quality_issues.append(f"{missing_cells} missing cells")
        if duplicate_rows > 0:
            quality_issues.append(f"{duplicate_rows} duplicate rows")
        summary.append(f"Data quality issues detected: {', '.join(quality_issues)}. Review insights for details.")
    
    summary.append("For deeper analysis and AI-generated insights, ensure LLM service is properly configured.")
    
    return summary


def _calculate_quality_score(kpis: Dict) -> int:
    """Calculate simple quality score 0-100."""
    row_count = kpis.get('rowCount', 0)
    col_count = kpis.get('columnCount', 0)
    missing_cells = kpis.get('missingCells', 0)
    duplicate_rows = kpis.get('duplicateRows', 0)
    
    if row_count == 0 or col_count == 0:
        return 0
    
    total_cells = row_count * col_count
    
    # Start at 100
    score = 100
    
    # Deduct for missing data
    if total_cells > 0:
        missing_pct = (missing_cells / total_cells) * 100
        score -= min(missing_pct * 2, 40)  # Max 40 point deduction
    
    # Deduct for duplicates
    if row_count > 0:
        duplicate_pct = (duplicate_rows / row_count) * 100
        score -= min(duplicate_pct * 2, 30)  # Max 30 point deduction
    
    return max(0, int(score))


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    sample_eda = {
        "kpis": {
            "rowCount": 500,
            "columnCount": 5,
            "missingCells": 45,
            "duplicateRows": 23,
            "numericStats": {
                "Revenue": {"min": 1000, "max": 50000, "mean": 8000, "median": 7500, "std": 5000}
            }
        },
        "schema": [
            {"column": "Email", "type": "string", "missing": 38},
            {"column": "Revenue", "type": "float", "missing": 0}
        ],
        "cleanedPreview": [
            {"Email": None, "Revenue": 50000},
            {"Email": "test@example.com", "Revenue": 7500}
        ],
        "chartSpecs": [
            {"id": "chart_1", "type": "histogram", "x": "Revenue"}
        ],
        "correlations": []
    }
    
    result = generate_fallback_insights(sample_eda)
    
    import json
    print(json.dumps(result, indent=2))
