"""
Quick test script to verify LLM client is working
"""
import sys
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lib import llm_client

# Test data
test_file_info = {"name": "test.csv", "type": "csv"}
test_schema = [
    {"name": "Date", "type": "string", "missing": 0},
    {"name": "Amount", "type": "number", "missing": 0}
]
test_kpis = {
    "rowCount": 10,
    "colCount": 2,
    "missingCount": 0
}
test_preview = [
    {"Date": "2023-01-01", "Amount": 100},
    {"Date": "2023-01-02", "Amount": 200}
]

print("=" * 60)
print("Testing LLM Client")
print("=" * 60)

try:
    result = llm_client.generate_insights(
        file_info=test_file_info,
        schema=test_schema,
        kpis=test_kpis,
        preview=test_preview
    )
    
    print("\n✅ LLM call succeeded!")
    print(f"\ninsightsAnalyst count: {len(result.get('insightsAnalyst', []))}")
    print(f"insightsBusiness count: {len(result.get('insightsBusiness', []))}")
    print(f"businessSummary count: {len(result.get('businessSummary', []))}")
    
    if result.get('insightsAnalyst'):
        print("\nFirst Analyst Insight:")
        print(f"  Title: {result['insightsAnalyst'][0].get('title')}")
        print(f"  Summary: {result['insightsAnalyst'][0].get('summary')}")
    
    print(f"\n_meta: {result.get('_meta')}")
    
except Exception as e:
    print(f"\n❌ LLM call failed: {e}")
    import traceback
    traceback.print_exc()
