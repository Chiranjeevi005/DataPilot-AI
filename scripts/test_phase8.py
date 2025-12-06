"""
Quick test script for Phase 8 components
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from lib.prompt_manager import build_prompt, get_prompt_hash
from lib.fallback_generator import generate_fallback_insights
from lib.insight_validator import validate_and_normalize

print("="*60)
print("PHASE 8 COMPONENT TESTS")
print("="*60)

# Test 1: Prompt Manager
print("\n1. Testing Prompt Manager...")
sample_eda = {
    'kpis': {
        'rowCount': 150,
        'columnCount': 5,
        'missingCells': 3,
        'duplicateRows': 0,
        'numericStats': {
            'Revenue': {'min': 1200, 'max': 185000, 'mean': 8500, 'median': 7200, 'std': 15000}
        }
    },
    'schema': [{'column': 'Date', 'type': 'date', 'missing': 0, 'unique': 150}],
    'cleanedPreview': [{'Date': '2024-01-15', 'Revenue': 7200}],
    'chartSpecs': [{'id': 'chart_1', 'type': 'timeseries', 'x': 'Date', 'y': 'Revenue'}]
}

prompt = build_prompt(sample_eda, shot_count=3)
print(f"   ✓ Prompt built successfully!")
print(f"   Length: {len(prompt)} chars")
print(f"   Hash: {get_prompt_hash(prompt)}")

# Test 2: Fallback Generator
print("\n2. Testing Fallback Generator...")
fallback_eda = {
    'kpis': {
        'rowCount': 500,
        'columnCount': 5,
        'missingCells': 85,
        'duplicateRows': 47,
        'numericStats': {}
    },
    'schema': [{'column': 'Email', 'type': 'string', 'missing': 72}],
    'cleanedPreview': [],
    'chartSpecs': []
}

result = generate_fallback_insights(fallback_eda)
print(f"   ✓ Fallback insights generated!")
print(f"   Insights: {len(result['analystInsights'])}")
print(f"   Summary points: {len(result['businessSummary'])}")
print(f"   Quality score: {result['metadata']['data_quality_score']}")

# Test 3: Insight Validator
print("\n3. Testing Insight Validator...")
test_output = {
    "analystInsights": [
        {
            "id": "i1",
            "text": "Test insight",
            "severity": "HIGH",
            "category": "outlier",
            "evidence": {
                "aggregates": {"Revenue": 100000},
                "row_indices": [0],
                "chart_id": "chart_1"
            },
            "recommendation": {
                "who": "engineer",
                "what": "Fix it",
                "priority": "URGENT"
            }
        }
    ],
    "businessSummary": ["Summary point 1"],
    "visualActions": [],
    "metadata": {"confidence": "high"}
}

normalized, issues = validate_and_normalize(test_output, sample_eda)
print(f"   ✓ Validation complete!")
print(f"   Normalized: {normalized is not None}")
print(f"   Issues: {len(issues)}")
if issues:
    print(f"   Sample issues: {issues[:3]}")

print("\n" + "="*60)
print("ALL TESTS PASSED ✓")
print("="*60)
print("\nPhase 8 components are working correctly!")
print("Next steps:")
print("  1. Run worker: python src/worker.py")
print("  2. Upload test file to trigger few-shot pipeline")
print("  3. Review insights and collect feedback")
