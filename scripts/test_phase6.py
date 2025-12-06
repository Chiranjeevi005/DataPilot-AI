import sys
import os
import json
import logging
import shutil
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from jobs.process_job import process_job
from lib import storage

# Configure Logging
logging.basicConfig(level=logging.INFO)

class TestPhase6(unittest.TestCase):
    def setUp(self):
        # Setup temp storage
        self.test_job_id = "test_phase6_job"
        self.storage_path = storage.get_storage_path(self.test_job_id, "")
        if os.path.exists(self.storage_path):
            shutil.rmtree(os.path.dirname(self.storage_path))
        
        # Create a dummy CSV
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self.csv_path = os.path.join(os.path.dirname(self.storage_path), "data.csv")
        with open(self.csv_path, "w") as f:
            f.write("id,value,category\n1,100,A\n2,200,B\n3,300,A")
            
        self.redis_mock = MagicMock()
        self.redis_mock.get.return_value = json.dumps({})
        
    def test_happy_path_mock_llm(self):
        print("\n--- Testing Happy Path (Mock LLM) ---")
        os.environ["LLM_MOCK"] = "true"
        
        # Use proper URI generation
        from pathlib import Path
        file_url = Path(self.csv_path).as_uri()
        
        payload = {
            "jobId": self.test_job_id,
            "fileUrl": file_url,
            "fileName": "data.csv"
        }
        
        try:
            process_job(self.redis_mock, payload)
        except Exception as e:
            print(f"Process Job Failed: {e}")
            raise e
        
        # Check result.json
        result_path = storage.get_storage_path(self.test_job_id, "result.json")
        if not os.path.exists(result_path):
            print(f"Result file missing at {result_path}")
            self.fail("Result file missing")
            
        with open(result_path, 'r') as f:
            result = json.load(f)
            
        print("Result Keys:", list(result.keys()))
        if "issues" in result and result['issues']:
            print("Job Issues:", result['issues'])

        self.assertIn("analystInsights", result)
        insights = result["analystInsights"]
        self.assertIn("businessSummary", insights)
        self.assertTrue(len(insights["businessSummary"]) > 0)
        # Check for mock signature
        self.assertIn("MOCK", insights["businessSummary"][0])
        print("Happy path passed: Insights generated.")

    @patch('lib.llm_client.generate_insights')
    def test_llm_failure_handling(self, mock_generate):
        print("\n--- Testing Failure Path ---")
        os.environ["LLM_MOCK"] = "false"
        
        # Simulate LLM returning fallback due to failure
        fallback_response = {
            "businessSummary": ["Fallback summary"],
            "evidence": [],
            "issues": ["Simulated LLM Failure"]
        }
        mock_generate.return_value = fallback_response
        
        # Use proper URI generation
        from pathlib import Path
        file_url = Path(self.csv_path).as_uri()

        payload = {
            "jobId": self.test_job_id + "_fail",
            "fileUrl": file_url,
            "fileName": "data.csv"
        }
        
        process_job(self.redis_mock, payload)
        
        result_path = storage.get_storage_path(self.test_job_id + "_fail", "result.json")
        with open(result_path, 'r') as f:
            result = json.load(f)
            
        self.assertIn("analystInsights", result)
        # Check if issues propagated
        self.assertTrue(any("Simulated LLM Failure" in i for i in result["issues"]))
        print("Failure path passed: Issues recorded.")

if __name__ == '__main__':
    unittest.main()
