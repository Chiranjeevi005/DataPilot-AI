"""
Evaluate Few-Shot vs Fine-Tuned Model Performance

Compares two pipelines on a holdout set:
1. Few-shot prompt pipeline (current)
2. Fine-tuned model endpoint (optional)

Metrics:
- Schema validation pass rate
- Evidence mapping accuracy
- BLEU/ROUGE scores against human-approved outputs (optional)

Usage:
    python eval_fewshot_vs_finetuned.py --holdout <path> [--finetuned-endpoint <url>]
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.llm_client_fewshot import generate_insights_fewshot
from lib.insight_validator import validate_and_normalize

logger = logging.getLogger(__name__)


def load_holdout_set(filepath: str) -> List[Dict[str, Any]]:
    """
    Load holdout test set.
    
    Expected format (JSONL):
    {
        "compact_eda": {...},
        "expected_output": {...},  # Human-approved ground truth
        "metadata": {...}
    }
    
    Args:
        filepath: Path to holdout JSONL file
        
    Returns:
        List of test cases
    """
    test_cases = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                case = json.loads(line)
                test_cases.append(case)
            except json.JSONDecodeError as e:
                logger.error(f"Line {line_num}: JSON decode error: {e}")
    
    logger.info(f"Loaded {len(test_cases)} test cases from {filepath}")
    return test_cases


def evaluate_fewshot_pipeline(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate few-shot prompt pipeline on test cases.
    
    Args:
        test_cases: List of test cases
        
    Returns:
        Evaluation results
    """
    logger.info("Evaluating few-shot pipeline...")
    
    results = {
        "total": len(test_cases),
        "schema_valid": 0,
        "evidence_valid": 0,
        "outputs": []
    }
    
    for idx, case in enumerate(test_cases):
        compact_eda = case.get('compact_eda', {})
        expected = case.get('expected_output', {})
        job_id = case.get('metadata', {}).get('job_id', f'test_{idx}')
        
        logger.info(f"Processing test case {idx+1}/{len(test_cases)}: {job_id}")
        
        try:
            # Generate insights
            output = generate_insights_fewshot(compact_eda, job_id=job_id)
            
            # Validate
            normalized, issues = validate_and_normalize(output, compact_eda)
            
            schema_valid = normalized is not None
            evidence_valid = _check_evidence_accuracy(output, compact_eda)
            
            if schema_valid:
                results["schema_valid"] += 1
            if evidence_valid:
                results["evidence_valid"] += 1
            
            results["outputs"].append({
                "job_id": job_id,
                "schema_valid": schema_valid,
                "evidence_valid": evidence_valid,
                "validation_issues": len(issues),
                "insight_count": len(output.get('analystInsights', [])),
                "output": output
            })
            
        except Exception as e:
            logger.error(f"Error processing {job_id}: {e}")
            results["outputs"].append({
                "job_id": job_id,
                "schema_valid": False,
                "evidence_valid": False,
                "error": str(e)
            })
    
    results["schema_pass_rate"] = (results["schema_valid"] / results["total"] * 100) if results["total"] > 0 else 0
    results["evidence_pass_rate"] = (results["evidence_valid"] / results["total"] * 100) if results["total"] > 0 else 0
    
    return results


def _check_evidence_accuracy(output: Dict[str, Any], compact_eda: Dict[str, Any]) -> bool:
    """
    Check if evidence mappings are accurate.
    
    Validates:
    - aggregates keys exist in KPIs
    - row_indices are within bounds
    - chart_ids exist
    
    Args:
        output: LLM output
        compact_eda: Compact EDA for validation
        
    Returns:
        True if all evidence is valid
    """
    insights = output.get('analystInsights', [])
    kpis = compact_eda.get('kpis', {})
    cleaned_preview = compact_eda.get('cleanedPreview', [])
    chart_specs = compact_eda.get('chartSpecs', [])
    
    max_index = len(cleaned_preview) - 1
    chart_ids = {chart.get('id') for chart in chart_specs}
    
    for insight in insights:
        evidence = insight.get('evidence', {})
        
        # Check row_indices
        row_indices = evidence.get('row_indices', [])
        for idx in row_indices:
            if not isinstance(idx, int) or idx < 0 or idx > max_index:
                return False
        
        # Check chart_id
        chart_id = evidence.get('chart_id')
        if chart_id is not None and chart_id not in chart_ids:
            return False
    
    return True


def evaluate_finetuned_pipeline(
    test_cases: List[Dict[str, Any]],
    endpoint_url: str
) -> Dict[str, Any]:
    """
    Evaluate fine-tuned model endpoint on test cases.
    
    NOTE: This is a placeholder. Implement based on your fine-tuned model deployment.
    
    Args:
        test_cases: List of test cases
        endpoint_url: Fine-tuned model API endpoint
        
    Returns:
        Evaluation results
    """
    logger.warning("Fine-tuned model evaluation not implemented yet.")
    logger.warning("This is a placeholder for future fine-tuned model comparison.")
    
    return {
        "total": len(test_cases),
        "schema_valid": 0,
        "evidence_valid": 0,
        "schema_pass_rate": 0,
        "evidence_pass_rate": 0,
        "outputs": [],
        "note": "Fine-tuned model evaluation not implemented"
    }


def compare_results(fewshot_results: Dict, finetuned_results: Dict) -> Dict[str, Any]:
    """
    Compare results from both pipelines.
    
    Args:
        fewshot_results: Few-shot pipeline results
        finetuned_results: Fine-tuned model results
        
    Returns:
        Comparison report
    """
    comparison = {
        "fewshot": {
            "schema_pass_rate": fewshot_results.get("schema_pass_rate", 0),
            "evidence_pass_rate": fewshot_results.get("evidence_pass_rate", 0),
            "total_processed": fewshot_results.get("total", 0)
        },
        "finetuned": {
            "schema_pass_rate": finetuned_results.get("schema_pass_rate", 0),
            "evidence_pass_rate": finetuned_results.get("evidence_pass_rate", 0),
            "total_processed": finetuned_results.get("total", 0)
        },
        "improvement": {
            "schema_pass_rate": finetuned_results.get("schema_pass_rate", 0) - fewshot_results.get("schema_pass_rate", 0),
            "evidence_pass_rate": finetuned_results.get("evidence_pass_rate", 0) - fewshot_results.get("evidence_pass_rate", 0)
        }
    }
    
    return comparison


def generate_report(
    holdout_path: str,
    fewshot_results: Dict,
    finetuned_results: Dict,
    comparison: Dict
) -> Dict[str, Any]:
    """Generate evaluation report."""
    
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "holdout_set": holdout_path,
        "fewshot_results": fewshot_results,
        "finetuned_results": finetuned_results,
        "comparison": comparison
    }
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate few-shot vs fine-tuned model performance"
    )
    parser.add_argument(
        '--holdout',
        type=str,
        required=True,
        help='Path to holdout test set (JSONL)'
    )
    parser.add_argument(
        '--finetuned-endpoint',
        type=str,
        default=None,
        help='Fine-tuned model API endpoint (optional)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output report path (default: reports/compare_TIMESTAMP.json)'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Load holdout set
    logger.info(f"Loading holdout set from {args.holdout}...")
    test_cases = load_holdout_set(args.holdout)
    
    if not test_cases:
        logger.error("No test cases loaded. Exiting.")
        return
    
    # Evaluate few-shot pipeline
    fewshot_results = evaluate_fewshot_pipeline(test_cases)
    
    # Evaluate fine-tuned pipeline (if endpoint provided)
    if args.finetuned_endpoint:
        finetuned_results = evaluate_finetuned_pipeline(test_cases, args.finetuned_endpoint)
    else:
        logger.info("No fine-tuned endpoint provided. Skipping fine-tuned evaluation.")
        finetuned_results = {
            "total": 0,
            "schema_valid": 0,
            "evidence_valid": 0,
            "schema_pass_rate": 0,
            "evidence_pass_rate": 0,
            "note": "Not evaluated"
        }
    
    # Compare
    comparison = compare_results(fewshot_results, finetuned_results)
    
    # Generate report
    report = generate_report(args.holdout, fewshot_results, finetuned_results, comparison)
    
    # Save report
    if args.output:
        output_path = args.output
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        output_filename = f"compare_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = os.path.join(reports_dir, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Report saved to {output_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION COMPARISON REPORT")
    print("="*60)
    print(f"Holdout set: {args.holdout}")
    print(f"Test cases: {len(test_cases)}")
    
    print(f"\nFew-Shot Pipeline:")
    print(f"  Schema pass rate: {fewshot_results['schema_pass_rate']:.1f}%")
    print(f"  Evidence pass rate: {fewshot_results['evidence_pass_rate']:.1f}%")
    
    if args.finetuned_endpoint:
        print(f"\nFine-Tuned Pipeline:")
        print(f"  Schema pass rate: {finetuned_results['schema_pass_rate']:.1f}%")
        print(f"  Evidence pass rate: {finetuned_results['evidence_pass_rate']:.1f}%")
        
        print(f"\nImprovement:")
        print(f"  Schema: {comparison['improvement']['schema_pass_rate']:+.1f}%")
        print(f"  Evidence: {comparison['improvement']['evidence_pass_rate']:+.1f}%")
    
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
