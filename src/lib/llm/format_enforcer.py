
import json
from typing import Dict, Any, List

def get_system_instruction() -> str:
    return """You are a senior Data Analyst AI.
You must output strict, valid JSON only.
No markdown formatting (no ```json blocks).
No explanations outside the JSON.
"""

def get_format_instructions() -> str:
    return """
CRITICAL: You MUST output a SINGLE JSON object confirming to this schema:

{
  "insightsAnalyst": [
    {
      "title": "Short title of the finding",
      "summary": "Detailed explanation (2-3 sentences)",
      "severity": "info" | "warning" | "critical",
      "evidence": [
        {
           "type": "metric" | "row" | "aggregate",
           "key": "Column Name or Metric Name",
           "value": "123.45",
           "description": "Context for this evidence"
        }
      ],
      "recommendation": "Actionable next step"
    }
  ],
  "insightsBusiness": [
    {
      "title": "Business implication",
      "summary": "High-level summary for executives",
      "severity": "info" | "warning" | "critical",
      "evidence": [],
      "recommendation": "Strategic advice"
    }
  ],
  "businessSummary": [
    {
      "text": "Key takeaway 1",
      "evidenceKeys": ["Revenue", "Q3 2024"]
    }
  ]
}

- Ensure all arrays are present even if empty.
- Do not use trailing commas.
- Severity must be lowercase: "info", "warning", "critical".
- Evidence type must be "metric", "row", "aggregate".
- Numbers in evidence should be strings or numbers.
"""

def wrap_prompt(base_prompt: str) -> str:
    return f"{base_prompt}\n\n{get_format_instructions()}"

def enforce_json_format(llm_output: str) -> Dict[str, Any]:
    """
    Cleans and parses LLM output.
    """
    clean_text = llm_output.strip()
    
    # Remove markdown code blocks if present (despite instructions)
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
        
    clean_text = clean_text.strip()
    
    try:
        data = json.loads(clean_text)
        return data
    except json.JSONDecodeError:
        # Simple retry logic could happen here, or let caller handle it.
        # Try to find first { and last }
        try:
            start = clean_text.find('{')
            end = clean_text.rfind('}')
            if start != -1 and end != -1:
                json_part = clean_text[start:end+1]
                return json.loads(json_part)
        except:
            pass
        raise ValueError("Failed to parse JSON from LLM output")
