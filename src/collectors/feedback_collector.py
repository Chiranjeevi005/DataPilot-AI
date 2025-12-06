"""
Feedback Collector for Human-in-the-Loop Review

Responsibilities:
- Provide API/CLI for human reviewers to approve, edit, or reject insights
- Store structured feedback in data/feedback/ directory
- Capture human corrections and quality scores
- Enable fine-tuning dataset collection
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """Collect and store human feedback on LLM-generated insights."""
    
    def __init__(self, feedback_dir: Optional[str] = None):
        """
        Initialize feedback collector.
        
        Args:
            feedback_dir: Directory to store feedback files (default: data/feedback/)
        """
        if feedback_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            feedback_dir = os.path.join(base_dir, "data", "feedback")
        
        self.feedback_dir = feedback_dir
        os.makedirs(self.feedback_dir, exist_ok=True)
        logger.info(f"Feedback collector initialized: {self.feedback_dir}")
    
    def collect_feedback(
        self,
        job_id: str,
        compact_eda: Dict[str, Any],
        llm_output: Dict[str, Any],
        feedback_items: List[Dict[str, Any]],
        reviewer_id: str = "anonymous",
        overall_score: Optional[int] = None
    ) -> str:
        """
        Collect and store feedback for a job.
        
        Args:
            job_id: Job identifier
            compact_eda: Original compact EDA input
            llm_output: LLM-generated output
            feedback_items: List of feedback per insight
                [
                    {
                        "insight_id": "i1",
                        "action": "approve" | "edit" | "reject",
                        "edited_text": "...",  # if action == "edit"
                        "edited_evidence": {...},  # if action == "edit"
                        "edited_recommendation": {...},  # if action == "edit"
                        "human_score": 1-5,  # accuracy, actionability, clarity
                        "notes": "..."
                    }
                ]
            reviewer_id: Identifier for reviewer
            overall_score: Overall quality score 1-5
            
        Returns:
            Path to saved feedback file
        """
        feedback_data = {
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reviewer_id": reviewer_id,
            "overall_score": overall_score,
            "compact_eda": compact_eda,
            "llm_output": llm_output,
            "feedback_items": feedback_items,
            "metadata": {
                "total_insights": len(llm_output.get('analystInsights', [])),
                "approved_count": sum(1 for item in feedback_items if item.get('action') == 'approve'),
                "edited_count": sum(1 for item in feedback_items if item.get('action') == 'edit'),
                "rejected_count": sum(1 for item in feedback_items if item.get('action') == 'reject')
            }
        }
        
        # Save to file
        filename = f"feedback_{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.feedback_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Feedback saved: {filepath}")
        logger.info(f"  Approved: {feedback_data['metadata']['approved_count']}, "
                   f"Edited: {feedback_data['metadata']['edited_count']}, "
                   f"Rejected: {feedback_data['metadata']['rejected_count']}")
        
        return filepath
    
    def load_feedback(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Load feedback for a specific job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Feedback data or None if not found
        """
        # Find most recent feedback file for job
        matching_files = [
            f for f in os.listdir(self.feedback_dir)
            if f.startswith(f"feedback_{job_id}_") and f.endswith('.json')
        ]
        
        if not matching_files:
            logger.warning(f"No feedback found for job {job_id}")
            return None
        
        # Sort by timestamp (filename) and get most recent
        matching_files.sort(reverse=True)
        filepath = os.path.join(self.feedback_dir, matching_files[0])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_all_feedback(self) -> List[Dict[str, Any]]:
        """
        List all feedback files with summary metadata.
        
        Returns:
            List of feedback summaries
        """
        summaries = []
        
        for filename in os.listdir(self.feedback_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.feedback_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                summaries.append({
                    "filename": filename,
                    "job_id": data.get('job_id'),
                    "timestamp": data.get('timestamp'),
                    "reviewer_id": data.get('reviewer_id'),
                    "overall_score": data.get('overall_score'),
                    "approved": data.get('metadata', {}).get('approved_count', 0),
                    "edited": data.get('metadata', {}).get('edited_count', 0),
                    "rejected": data.get('metadata', {}).get('rejected_count', 0)
                })
            except Exception as e:
                logger.error(f"Error reading {filename}: {e}")
        
        return summaries


def cli_review_job(job_id: str, result_json_path: str):
    """
    CLI tool for reviewing a job's insights interactively.
    
    Args:
        job_id: Job identifier
        result_json_path: Path to result.json file
    """
    print(f"\n{'='*60}")
    print(f"FEEDBACK REVIEW: Job {job_id}")
    print(f"{'='*60}\n")
    
    # Load result.json
    with open(result_json_path, 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    compact_eda = {
        "kpis": result.get('kpis', {}),
        "schema": result.get('schema', []),
        "cleanedPreview": result.get('cleanedPreview', []),
        "chartSpecs": result.get('chartSpecs', [])
    }
    
    llm_output = {
        "analystInsights": result.get('analystInsights', []),
        "businessSummary": result.get('businessSummary', []),
        "visualActions": result.get('visualActions', []),
        "metadata": result.get('metadata', {})
    }
    
    insights = llm_output.get('analystInsights', [])
    
    if not insights:
        print("No insights to review.")
        return
    
    feedback_items = []
    
    for idx, insight in enumerate(insights):
        print(f"\n--- Insight {idx+1}/{len(insights)} ---")
        print(f"ID: {insight.get('id')}")
        print(f"Category: {insight.get('category')} | Severity: {insight.get('severity')}")
        print(f"\nText:\n{insight.get('text')}\n")
        print(f"Evidence: {json.dumps(insight.get('evidence', {}), indent=2)}")
        print(f"Recommendation: {json.dumps(insight.get('recommendation', {}), indent=2)}")
        
        print("\nActions:")
        print("  [a] Approve")
        print("  [e] Edit")
        print("  [r] Reject")
        print("  [s] Skip")
        
        action = input("\nYour choice: ").strip().lower()
        
        if action == 's':
            continue
        elif action == 'a':
            score = int(input("Score (1-5): ").strip() or "4")
            notes = input("Notes (optional): ").strip()
            
            feedback_items.append({
                "insight_id": insight.get('id'),
                "action": "approve",
                "human_score": score,
                "notes": notes
            })
        elif action == 'e':
            print("\nEditing insight (press Enter to keep original):")
            edited_text = input(f"Text [{insight.get('text')[:50]}...]: ").strip()
            
            feedback_items.append({
                "insight_id": insight.get('id'),
                "action": "edit",
                "edited_text": edited_text or insight.get('text'),
                "edited_evidence": insight.get('evidence'),  # Could allow editing
                "edited_recommendation": insight.get('recommendation'),  # Could allow editing
                "human_score": int(input("Score (1-5): ").strip() or "3"),
                "notes": input("Notes: ").strip()
            })
        elif action == 'r':
            feedback_items.append({
                "insight_id": insight.get('id'),
                "action": "reject",
                "human_score": 1,
                "notes": input("Reason for rejection: ").strip()
            })
    
    # Overall score
    print("\n" + "="*60)
    overall_score = int(input("Overall quality score (1-5): ").strip() or "3")
    reviewer_id = input("Your reviewer ID: ").strip() or "anonymous"
    
    # Save feedback
    collector = FeedbackCollector()
    filepath = collector.collect_feedback(
        job_id=job_id,
        compact_eda=compact_eda,
        llm_output=llm_output,
        feedback_items=feedback_items,
        reviewer_id=reviewer_id,
        overall_score=overall_score
    )
    
    print(f"\n✓ Feedback saved to: {filepath}")


# Example usage
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 3:
        print("Usage: python feedback_collector.py <job_id> <result_json_path>")
        print("\nOr use programmatically:")
        print("  collector = FeedbackCollector()")
        print("  collector.collect_feedback(...)")
        sys.exit(1)
    
    job_id = sys.argv[1]
    result_path = sys.argv[2]
    
    cli_review_job(job_id, result_path)
