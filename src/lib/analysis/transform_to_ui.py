
from typing import Dict, List, Any
import datetime

def transform_to_ui(
    job_id: str,
    raw_schema: List[Dict],
    raw_kpis: Dict,
    cleaned_preview: List[Dict],
    chart_specs: List[Dict],
    llm_result: Dict[str, Any],
    quality_score: int
) -> Dict[str, Any]:
    """
    Merges all analysis parts into the canonical AnalysisResult UI object.
    Matches types in /types/analysis.ts
    """
    
    # 1. Transform KPIs
    # Expected: { "rowCount": 100, "numericStats": { "col": { ... } } }
    ui_kpis = []
    
    # Standard metadata KPIs
    if 'rowCount' in raw_kpis:
        ui_kpis.append({
            "name": "Total Rows",
            "value": raw_kpis['rowCount'],
            "deltaType": "neutral"
        })
    if 'colCount' in raw_kpis:
        ui_kpis.append({
            "name": "Columns",
            "value": raw_kpis['colCount'],
            "deltaType": "neutral"
        })
    if 'missingCount' in raw_kpis:
         ui_kpis.append({
            "name": "Missing Cells",
            "value": raw_kpis['missingCount'],
            "deltaType": "negative" if raw_kpis['missingCount'] > 0 else "positive"
        })
        
    # Numeric stats to KPIs
    numeric_stats = raw_kpis.get('numericStats', {})
    for col, stats in numeric_stats.items():
        # Maybe add a "Sum" or "Mean" KPI for important cols?
        # For UI simplicity, let's pick "Sum" or "Mean"
        val = stats.get('sum', 0)
        # Format based on magnitude? For now just raw.
        ui_kpis.append({
            "name": f"Total {col}",
            "value": round(val, 2),
            "deltaType": "neutral"
        })

    # 2. Transform Charts
    # Ensure chart specs match ChartSpec interface
    # (They should be close already from analysis.py, but lets be safe)
    valid_charts = []
    for chart in chart_specs:
         if 'id' in chart and 'type' in chart and 'data' in chart:
             valid_charts.append(chart)

    # 3. Construct Final Object
    return {
        "jobId": job_id,
        "kpis": ui_kpis,
        "schema": raw_schema,
        "cleanedPreview": cleaned_preview,
        "insightsAnalyst": llm_result.get('insightsAnalyst', []),
        "insightsBusiness": llm_result.get('insightsBusiness', []),
        "businessSummary": llm_result.get('businessSummary', []),
        "chartSpecs": valid_charts,
        "qualityScore": quality_score,
        "issues": [], # Can populate if we tracked errors
        "processedAt": datetime.datetime.utcnow().isoformat() + "Z",
        "uiOptimized": True,
        "version": "1.0"
    }
