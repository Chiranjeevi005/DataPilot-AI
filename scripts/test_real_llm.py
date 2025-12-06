import os
import json
import io
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Load .env manually if needed (for local script usage)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, assuming env vars are set or manual load.")
    # Simple .env parser fallback
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    if not os.getenv(k):
                        os.environ[k] = v

from lib import llm_client

def test_real_llm():
    print(f"Testing Real LLM with API Key: {'*' * 4 + os.getenv('GEMINI_API_KEY')[-4:] if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
    print(f"Model: {os.getenv('GEMINI_MODEL', 'default')}")
    
    # Force Mock off
    os.environ["LLM_MOCK"] = "false"
    
    # Mock Data
    file_info = {"name": "real_test.csv", "type": "csv"}
    schema = [
        {"name": "Date", "inferred_type": "datetime"},
        {"name": "Revenue", "inferred_type": "numeric"},
        {"name": "Region", "inferred_type": "categorical"}
    ]
    kpis = {
        "rowCount": 500,
        "colCount": 3,
        "missingCount": 0,
        "numericStats": {
            "Revenue": {"sum": 500000, "mean": 1000, "max": 5000}
        }
    }
    preview = [
        {"Date": "2024-01-01", "Revenue": 1200, "Region": "North"},
        {"Date": "2024-01-02", "Revenue": 900, "Region": "South"},
        {"Date": "2024-01-03", "Revenue": 1500, "Region": "East"}
    ]
    
    print("\nCalling Gemini...")
    try:
        insights = llm_client.generate_insights(file_info, schema, kpis, preview)
        print("\n--- Insights Received ---")
        print(json.dumps(insights, indent=2))
        
        if "issues" in insights:
            print(f"\nIssues found: {insights['issues']}")
        else:
            print("\nSUCCESS: Real LLM worked.")
            
    except Exception as e:
        print(f"\nFAILED: {e}")

if __name__ == "__main__":
    test_real_llm()
