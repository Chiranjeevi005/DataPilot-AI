"""
Prompt Manager for Few-Shot Learning Pipeline

Responsibilities:
- Build LLM prompt payloads combining system prompt, few-shot examples, and compact EDA
- Dynamically select most relevant few-shot examples based on input characteristics
- Mask PII before sending to LLM
- Provide deterministic, reproducible prompt construction
"""

import os
import json
import re
import hashlib
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SHOT_COUNT = 3
MAX_SHOT_COUNT = 8
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
}


def _load_system_prompt() -> str:
    """Load system prompt template from prompts directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_dir, "prompts", "system_prompt.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load system_prompt.txt: {e}")
        return ""


def _load_fewshot_examples() -> List[Dict[str, Any]]:
    """Load few-shot examples from JSON file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_dir, "prompts", "fewshot_examples.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            examples = json.load(f)
            logger.info(f"Loaded {len(examples)} few-shot examples")
            return examples
    except Exception as e:
        logger.error(f"Failed to load fewshot_examples.json: {e}")
        return []


def _mask_pii(text: str) -> str:
    """
    Mask PII patterns in text to prevent leakage to LLM.
    
    Args:
        text: Input text potentially containing PII
        
    Returns:
        Text with PII patterns masked
    """
    masked = text
    
    # Email: keep first char and domain
    masked = re.sub(
        PII_PATTERNS['email'],
        lambda m: f"{m.group(0)[0]}***@{m.group(0).split('@')[1]}",
        masked
    )
    
    # Phone: mask middle digits
    masked = re.sub(
        PII_PATTERNS['phone'],
        lambda m: f"{m.group(0)[:3]}-***-{m.group(0)[-4:]}",
        masked
    )
    
    # SSN: mask completely
    masked = re.sub(PII_PATTERNS['ssn'], "***-**-****", masked)
    
    # Credit card: mask middle digits
    masked = re.sub(
        PII_PATTERNS['credit_card'],
        lambda m: f"{m.group(0)[:4]} **** **** {m.group(0)[-4:]}",
        masked
    )
    
    return masked


def _compute_eda_features(compact_eda: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract heuristic features from compact EDA for similarity matching.
    
    Features:
    - has_date_column: bool
    - missing_pct_bucket: "none" | "low" | "medium" | "high"
    - has_outliers: bool (max/min ratio > 10)
    - has_strong_correlation: bool (any |r| > 0.7)
    - has_duplicates: bool
    - row_count_bucket: "small" | "medium" | "large"
    
    Args:
        compact_eda: Compact EDA JSON with kpis, schema, cleanedPreview, etc.
        
    Returns:
        Dictionary of extracted features
    """
    features = {
        'has_date_column': False,
        'missing_pct_bucket': 'none',
        'has_outliers': False,
        'has_strong_correlation': False,
        'has_duplicates': False,
        'row_count_bucket': 'small'
    }
    
    # Check schema for date columns
    schema = compact_eda.get('schema', [])
    for col in schema:
        if col.get('type') in ['date', 'datetime', 'timestamp']:
            features['has_date_column'] = True
            break
    
    # Missing percentage bucket
    kpis = compact_eda.get('kpis', {})
    row_count = kpis.get('rowCount', 1)
    col_count = kpis.get('columnCount', 1)
    missing_cells = kpis.get('missingCells', 0)
    
    total_cells = row_count * col_count
    if total_cells > 0:
        missing_pct = (missing_cells / total_cells) * 100
        if missing_pct == 0:
            features['missing_pct_bucket'] = 'none'
        elif missing_pct < 1:
            features['missing_pct_bucket'] = 'low'
        elif missing_pct < 5:
            features['missing_pct_bucket'] = 'medium'
        else:
            features['missing_pct_bucket'] = 'high'
    
    # Outlier detection (max/min ratio > 10)
    numeric_stats = kpis.get('numericStats', {})
    for col, stats in numeric_stats.items():
        min_val = stats.get('min', 0)
        max_val = stats.get('max', 0)
        if min_val > 0 and max_val / min_val > 10:
            features['has_outliers'] = True
            break
    
    # Strong correlation check
    correlations = compact_eda.get('correlations', [])
    for corr in correlations:
        r = corr.get('r', 0)
        if abs(r) > 0.7:
            features['has_strong_correlation'] = True
            break
    
    # Duplicates
    duplicate_rows = kpis.get('duplicateRows', 0)
    features['has_duplicates'] = duplicate_rows > 0
    
    # Row count bucket
    if row_count < 100:
        features['row_count_bucket'] = 'small'
    elif row_count < 1000:
        features['row_count_bucket'] = 'medium'
    else:
        features['row_count_bucket'] = 'large'
    
    return features


def _score_example_similarity(example_features: Dict[str, Any], eda_features: Dict[str, Any]) -> float:
    """
    Score similarity between example and current EDA based on features.
    
    Args:
        example_features: Features extracted from few-shot example input
        eda_features: Features extracted from current compact EDA
        
    Returns:
        Similarity score (0.0 to 1.0, higher is more similar)
    """
    score = 0.0
    total_weight = 0.0
    
    # Boolean feature matches (weighted)
    bool_features = [
        ('has_date_column', 1.5),
        ('has_outliers', 2.0),
        ('has_strong_correlation', 1.5),
        ('has_duplicates', 1.0)
    ]
    
    for feature, weight in bool_features:
        total_weight += weight
        if example_features.get(feature) == eda_features.get(feature):
            score += weight
    
    # Categorical feature matches
    if example_features.get('missing_pct_bucket') == eda_features.get('missing_pct_bucket'):
        score += 1.5
    total_weight += 1.5
    
    if example_features.get('row_count_bucket') == eda_features.get('row_count_bucket'):
        score += 0.5
    total_weight += 0.5
    
    return score / total_weight if total_weight > 0 else 0.0


def get_few_shot_examples(compact_eda: Dict[str, Any], n: int = DEFAULT_SHOT_COUNT) -> List[Dict[str, Any]]:
    """
    Select N most relevant few-shot examples based on similarity to current EDA.
    
    Uses deterministic heuristics to ensure reproducibility:
    - Presence of date column
    - Missing data percentage bucket
    - Outlier presence (max/min ratio > 10)
    - Strong correlation presence (|r| > 0.7)
    - Duplicate presence
    - Row count bucket
    
    Args:
        compact_eda: Current compact EDA JSON
        n: Number of examples to select (default: 3, max: 8)
        
    Returns:
        List of N most similar few-shot examples
    """
    n = min(n, MAX_SHOT_COUNT)
    
    all_examples = _load_fewshot_examples()
    if not all_examples:
        logger.warning("No few-shot examples available")
        return []
    
    # Extract features from current EDA
    eda_features = _compute_eda_features(compact_eda)
    logger.debug(f"EDA features: {eda_features}")
    
    # Score each example
    scored_examples = []
    for example in all_examples:
        example_input = example.get('input', {})
        example_features = _compute_eda_features(example_input)
        similarity = _score_example_similarity(example_features, eda_features)
        
        scored_examples.append({
            'example': example,
            'similarity': similarity
        })
    
    # Sort by similarity (descending) and take top N
    scored_examples.sort(key=lambda x: x['similarity'], reverse=True)
    selected = [item['example'] for item in scored_examples[:n]]
    
    logger.info(f"Selected {len(selected)} few-shot examples with similarities: "
                f"{[round(item['similarity'], 2) for item in scored_examples[:n]]}")
    
    return selected


def build_prompt(compact_eda: Dict[str, Any], shot_count: int = DEFAULT_SHOT_COUNT) -> str:
    """
    Build complete LLM prompt combining system prompt, few-shot examples, and current EDA.
    
    Prompt structure:
    1. System prompt with schema and instructions
    2. Few-shot examples (input + output pairs)
    3. Current compact EDA as user input
    
    Args:
        compact_eda: Compact EDA JSON for current job
        shot_count: Number of few-shot examples to include (default: 3)
        
    Returns:
        Complete prompt string ready for LLM
    """
    # Load system prompt
    system_prompt = _load_system_prompt()
    if not system_prompt:
        logger.error("System prompt is empty, cannot build prompt")
        return ""
    
    # Get relevant few-shot examples
    examples = get_few_shot_examples(compact_eda, n=shot_count)
    
    # Build few-shot section
    fewshot_section = "\n\n---\n\nFEW-SHOT EXAMPLES:\n\n"
    
    for idx, example in enumerate(examples, 1):
        example_input = example.get('input', {})
        example_output = example.get('output', {})
        human_notes = example.get('human_notes', '')
        
        fewshot_section += f"Example {idx}:\n"
        if human_notes:
            fewshot_section += f"// Note: {human_notes}\n\n"
        
        fewshot_section += "INPUT:\n"
        fewshot_section += json.dumps(example_input, indent=2)
        fewshot_section += "\n\nOUTPUT:\n"
        fewshot_section += json.dumps(example_output, indent=2)
        fewshot_section += "\n\n---\n\n"
    
    # Mask PII in compact EDA
    compact_eda_str = json.dumps(compact_eda, indent=2)
    compact_eda_masked = _mask_pii(compact_eda_str)
    
    # Build final prompt
    final_prompt = f"""{system_prompt}

{fewshot_section}

NOW ANALYZE THIS DATASET:

INPUT:
{compact_eda_masked}

OUTPUT (JSON only, no markdown):
"""
    
    return final_prompt


def get_prompt_hash(prompt: str) -> str:
    """
    Generate SHA-256 hash of prompt for logging/auditing.
    
    Args:
        prompt: Full prompt string
        
    Returns:
        Hex digest of SHA-256 hash
    """
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Test with sample compact EDA
    sample_eda = {
        "kpis": {
            "rowCount": 150,
            "columnCount": 5,
            "missingCells": 3,
            "duplicateRows": 0,
            "numericStats": {
                "Revenue": {
                    "min": 1200,
                    "max": 185000,
                    "mean": 8500,
                    "median": 7200,
                    "std": 15000
                }
            }
        },
        "schema": [
            {"column": "Date", "type": "date", "missing": 0, "unique": 150},
            {"column": "Revenue", "type": "float", "missing": 0, "unique": 148}
        ],
        "cleanedPreview": [
            {"Date": "2024-01-15", "Revenue": 7200},
            {"Date": "2024-01-16", "Revenue": 185000}
        ],
        "chartSpecs": [
            {"id": "chart_1", "type": "timeseries", "x": "Date", "y": "Revenue"}
        ]
    }
    
    prompt = build_prompt(sample_eda, shot_count=3)
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Prompt hash: {get_prompt_hash(prompt)}")
    print("\n--- PROMPT PREVIEW (first 500 chars) ---")
    print(prompt[:500])
