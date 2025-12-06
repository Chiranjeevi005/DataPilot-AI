"""
Insight Validator for LLM Output

Responsibilities:
- Validate LLM output JSON against required schema
- Run evidence sanity checks (aggregates, row_indices, chart_id)
- Normalize severity, who, and recommendation fields to canonical values
- Attempt automated repair for common structural issues
- Flag untrusted insights with invalid evidence
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Canonical values for normalization
CANONICAL_SEVERITY = {'high', 'medium', 'low'}
CANONICAL_WHO = {'data_engineer', 'analyst', 'business_user', 'data_scientist'}
CANONICAL_PRIORITY = {'urgent', 'high', 'medium', 'low'}
CANONICAL_CATEGORY = {
    'outlier', 'missing_data', 'correlation', 'trend', 'distribution',
    'quality', 'seasonality', 'duplicate'
}
CANONICAL_VISUAL_ACTIONS = {
    'highlight_outliers', 'add_trendline', 'filter_nulls', 'show_correlation'
}


def _normalize_value(value: str, canonical_set: set, default: str) -> str:
    """Normalize value to canonical set, with fallback to default."""
    if not value:
        return default
    
    value_lower = str(value).lower().strip()
    
    # Exact match
    if value_lower in canonical_set:
        return value_lower
    
    # Fuzzy match (contains)
    for canonical in canonical_set:
        if canonical in value_lower or value_lower in canonical:
            return canonical
    
    # Fallback
    logger.warning(f"Value '{value}' not in canonical set {canonical_set}, using default '{default}'")
    return default


def _validate_evidence(evidence: Dict[str, Any], compact_eda: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and normalize evidence object.
    
    Checks:
    - aggregates keys should map to KPI names or be calculable
    - row_indices should be within [0, len(cleanedPreview)-1]
    - chart_id should exist in chartSpecs
    
    Args:
        evidence: Evidence dict from insight
        compact_eda: Compact EDA JSON for validation
        
    Returns:
        Tuple of (normalized_evidence, issues_list)
    """
    issues = []
    normalized = {
        'aggregates': {},
        'row_indices': [],
        'chart_id': None
    }
    
    # Validate aggregates
    raw_aggregates = evidence.get('aggregates', {})
    if not isinstance(raw_aggregates, dict):
        issues.append("aggregates must be a dictionary")
        raw_aggregates = {}
    
    kpis = compact_eda.get('kpis', {})
    kpi_names = set(kpis.keys())
    numeric_stats = kpis.get('numericStats', {})
    numeric_cols = set(numeric_stats.keys())
    
    for key, value in raw_aggregates.items():
        # Check if key is a known KPI or numeric column
        if key not in kpi_names and not any(col in key for col in numeric_cols):
            issues.append(f"aggregate key '{key}' not found in KPIs or numeric columns")
            # Still include it, but flag as untrusted
        
        # Ensure value is numeric
        try:
            normalized['aggregates'][key] = float(value) if isinstance(value, (int, float)) else value
        except (ValueError, TypeError):
            issues.append(f"aggregate value for '{key}' is not numeric: {value}")
    
    # Validate row_indices
    raw_indices = evidence.get('row_indices', [])
    if not isinstance(raw_indices, list):
        issues.append("row_indices must be a list")
        raw_indices = []
    
    cleaned_preview = compact_eda.get('cleanedPreview', [])
    max_index = len(cleaned_preview) - 1
    
    for idx in raw_indices:
        try:
            idx_int = int(idx)
            if 0 <= idx_int <= max_index:
                normalized['row_indices'].append(idx_int)
            else:
                issues.append(f"row_index {idx_int} out of range [0, {max_index}]")
        except (ValueError, TypeError):
            issues.append(f"row_index '{idx}' is not an integer")
    
    # Validate chart_id
    chart_id = evidence.get('chart_id')
    if chart_id is not None:
        chart_specs = compact_eda.get('chartSpecs', [])
        chart_ids = {chart.get('id') for chart in chart_specs}
        
        if chart_id not in chart_ids:
            issues.append(f"chart_id '{chart_id}' not found in chartSpecs")
            normalized['chart_id'] = None
        else:
            normalized['chart_id'] = chart_id
    
    return normalized, issues


def _normalize_insight(insight: Dict[str, Any], idx: int, compact_eda: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Normalize a single insight object.
    
    Args:
        insight: Raw insight dict from LLM
        idx: Index for generating stable ID
        compact_eda: Compact EDA for evidence validation
        
    Returns:
        Tuple of (normalized_insight, issues_list)
    """
    issues = []
    
    # ID
    insight_id = insight.get('id', f"i{idx+1}")
    if not insight_id.startswith('i'):
        insight_id = f"i{idx+1}"
    
    # Text
    text = insight.get('text', '')
    if not text or len(text) < 10:
        issues.append(f"insight {insight_id}: text is too short or missing")
        text = "Insight description missing"
    
    # Severity
    severity = _normalize_value(
        insight.get('severity', 'medium'),
        CANONICAL_SEVERITY,
        'medium'
    )
    
    # Category
    category = _normalize_value(
        insight.get('category', 'quality'),
        CANONICAL_CATEGORY,
        'quality'
    )
    
    # Evidence
    raw_evidence = insight.get('evidence', {})
    if not isinstance(raw_evidence, dict):
        issues.append(f"insight {insight_id}: evidence must be a dictionary")
        raw_evidence = {}
    
    evidence, evidence_issues = _validate_evidence(raw_evidence, compact_eda)
    issues.extend([f"insight {insight_id}: {issue}" for issue in evidence_issues])
    
    # Recommendation
    raw_recommendation = insight.get('recommendation', {})
    if not isinstance(raw_recommendation, dict):
        raw_recommendation = {}
    
    recommendation = {
        'who': _normalize_value(
            raw_recommendation.get('who', 'analyst'),
            CANONICAL_WHO,
            'analyst'
        ),
        'what': raw_recommendation.get('what', 'Review and investigate'),
        'priority': _normalize_value(
            raw_recommendation.get('priority', 'medium'),
            CANONICAL_PRIORITY,
            'medium'
        )
    }
    
    normalized = {
        'id': insight_id,
        'text': text,
        'severity': severity,
        'category': category,
        'evidence': evidence,
        'recommendation': recommendation
    }
    
    return normalized, issues


def _normalize_visual_action(action: Dict[str, Any], compact_eda: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Normalize a visual action object.
    
    Args:
        action: Raw visual action dict
        compact_eda: Compact EDA for chart_id validation
        
    Returns:
        Tuple of (normalized_action or None, issues_list)
    """
    issues = []
    
    chart_id = action.get('chart_id')
    if not chart_id:
        issues.append("visual action missing chart_id")
        return None, issues
    
    # Validate chart_id exists
    chart_specs = compact_eda.get('chartSpecs', [])
    chart_ids = {chart.get('id') for chart in chart_specs}
    
    if chart_id not in chart_ids:
        issues.append(f"visual action chart_id '{chart_id}' not found in chartSpecs")
        return None, issues
    
    # Normalize action type
    action_type = _normalize_value(
        action.get('action', ''),
        CANONICAL_VISUAL_ACTIONS,
        'highlight_outliers'
    )
    
    # Params
    params = action.get('params', {})
    if not isinstance(params, dict):
        params = {}
    
    normalized = {
        'chart_id': chart_id,
        'action': action_type,
        'params': params
    }
    
    return normalized, issues


def validate_and_normalize(raw_output: Dict[str, Any], compact_eda: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Validate and normalize LLM output JSON.
    
    Performs:
    1. Schema validation
    2. Evidence sanity checks
    3. Field normalization to canonical values
    4. Structural repair attempts
    
    Args:
        raw_output: Raw JSON output from LLM
        compact_eda: Compact EDA JSON for validation context
        
    Returns:
        Tuple of (normalized_output or None, issues_list)
        - normalized_output is None if unrecoverable errors
        - issues_list contains all validation warnings/errors
    """
    issues = []
    
    if not isinstance(raw_output, dict):
        issues.append("Output is not a dictionary")
        return None, issues
    
    # Handle nested structure (sometimes LLM returns {"insights": {...}})
    if 'insights' in raw_output and 'analystInsights' not in raw_output:
        logger.info("Detected nested structure, extracting insights")
        raw_output = raw_output['insights']
    
    # Normalize analystInsights
    raw_insights = raw_output.get('analystInsights', [])
    if not isinstance(raw_insights, list):
        if isinstance(raw_insights, dict):
            # Single insight returned as dict
            raw_insights = [raw_insights]
        else:
            issues.append("analystInsights must be a list")
            raw_insights = []
    
    normalized_insights = []
    for idx, insight in enumerate(raw_insights):
        if not isinstance(insight, dict):
            issues.append(f"Insight at index {idx} is not a dictionary")
            continue
        
        normalized_insight, insight_issues = _normalize_insight(insight, idx, compact_eda)
        normalized_insights.append(normalized_insight)
        issues.extend(insight_issues)
    
    # Normalize businessSummary
    raw_summary = raw_output.get('businessSummary', [])
    if not isinstance(raw_summary, list):
        issues.append("businessSummary must be a list")
        raw_summary = []
    
    business_summary = [str(item) for item in raw_summary if item]
    
    # Normalize visualActions
    raw_actions = raw_output.get('visualActions', [])
    if not isinstance(raw_actions, list):
        issues.append("visualActions must be a list")
        raw_actions = []
    
    visual_actions = []
    for action in raw_actions:
        if not isinstance(action, dict):
            continue
        
        normalized_action, action_issues = _normalize_visual_action(action, compact_eda)
        if normalized_action:
            visual_actions.append(normalized_action)
        issues.extend(action_issues)
    
    # Normalize metadata
    raw_metadata = raw_output.get('metadata', {})
    if not isinstance(raw_metadata, dict):
        raw_metadata = {}
    
    metadata = {
        'total_insights': len(normalized_insights),
        'confidence': _normalize_value(
            raw_metadata.get('confidence', 'medium'),
            {'high', 'medium', 'low'},
            'medium'
        ),
        'data_quality_score': raw_metadata.get('data_quality_score', 0),
        'analysis_timestamp': raw_metadata.get('analysis_timestamp', '')
    }
    
    # Build normalized output
    normalized_output = {
        'analystInsights': normalized_insights,
        'businessSummary': business_summary,
        'visualActions': visual_actions,
        'metadata': metadata,
        'issues': issues
    }
    
    # Check for critical failures
    if not normalized_insights and not business_summary:
        issues.append("CRITICAL: No insights or summary generated")
        return None, issues
    
    logger.info(f"Validation complete: {len(normalized_insights)} insights, {len(issues)} issues")
    
    return normalized_output, issues


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Test with sample LLM output
    sample_output = {
        "analystInsights": [
            {
                "id": "i1",
                "text": "Test insight",
                "severity": "HIGH",  # Should normalize to 'high'
                "category": "outlier",
                "evidence": {
                    "aggregates": {"Revenue": 100000},
                    "row_indices": [0, 999],  # 999 will be flagged as out of range
                    "chart_id": "chart_1"
                },
                "recommendation": {
                    "who": "engineer",  # Should normalize to 'data_engineer'
                    "what": "Fix it",
                    "priority": "URGENT"  # Should normalize to 'urgent'
                }
            }
        ],
        "businessSummary": ["Summary point 1"],
        "visualActions": [],
        "metadata": {
            "confidence": "high"
        }
    }
    
    sample_eda = {
        "kpis": {"rowCount": 100, "columnCount": 3},
        "cleanedPreview": [{"Revenue": 100000}] * 100,
        "chartSpecs": [{"id": "chart_1", "type": "timeseries"}]
    }
    
    normalized, issues = validate_and_normalize(sample_output, sample_eda)
    
    print(f"\nValidation Issues ({len(issues)}):")
    for issue in issues:
        print(f"  - {issue}")
    
    print(f"\nNormalized Output:")
    import json
    print(json.dumps(normalized, indent=2))
