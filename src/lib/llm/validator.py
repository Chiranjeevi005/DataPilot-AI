
import logging
import uuid
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def validate_llm_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and partially sanitizes the LLM output.
    Ensures that the structure matches the expected interface for the UI transformer.
    """
    validated = {}

    # 1. Validate insightsAnalyst
    validated['insightsAnalyst'] = _validate_insights(data.get('insightsAnalyst', []))

    # 2. Validate insightsBusiness
    validated['insightsBusiness'] = _validate_insights(data.get('insightsBusiness', []))

    # 3. Validate businessSummary
    raw_summary = data.get('businessSummary', [])
    if not isinstance(raw_summary, list):
        if isinstance(raw_summary, dict):
             raw_summary = [raw_summary] # wrapper
        else:
             raw_summary = []
    
    valid_summary = []
    for item in raw_summary:
        if isinstance(item, str):
            valid_summary.append({"text": item, "evidenceKeys": []})
        elif isinstance(item, dict) and "text" in item:
            valid_summary.append({
                "text": str(item["text"]),
                "evidenceKeys": item.get("evidenceKeys", []) if isinstance(item.get("evidenceKeys"), list) else []
            })
    validated['businessSummary'] = valid_summary

    return validated

def _validate_insights(insights: Any) -> List[Dict[str, Any]]:
    if not isinstance(insights, list):
        return []
    
    valid_list = []
    for item in insights:
        if not isinstance(item, dict):
            continue
            
        # Ensure ID
        if 'id' not in item or not item['id']:
            item['id'] = str(uuid.uuid4())[:8]
            
        # Ensure basic fields
        item['title'] = str(item.get('title', 'Untitled Insight'))
        item['summary'] = str(item.get('summary', 'No summary provided.'))
        
        # Severity Normalization
        sev = str(item.get('severity', 'info')).lower()
        if sev not in ['info', 'warning', 'critical']:
            sev = 'info'
        item['severity'] = sev
        
        # Evidence Normalization
        raw_evidence = item.get('evidence', [])
        if not isinstance(raw_evidence, list):
            raw_evidence = []
        
        valid_evidence = []
        for ev in raw_evidence:
            if isinstance(ev, dict):
                # Ensure type
                ev_type = str(ev.get('type', 'metric')).lower()
                if ev_type not in ['aggregate', 'row', 'pattern', 'metric']:
                     ev_type = 'metric'
                
                valid_evidence.append({
                    "type": ev_type,
                    "key": str(ev.get('key', '')),
                    "value": ev.get('value', None),
                    "description": str(ev.get('description', '')),
                    "rowIndex": ev.get('rowIndex') # Optional, keep as looks
                })
        item['evidence'] = valid_evidence
        
        valid_list.append(item)
        
    return valid_list
