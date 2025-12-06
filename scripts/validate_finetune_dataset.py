"""
Validate Fine-Tuning Dataset

Validates JSONL fine-tuning dataset for:
- Schema correctness
- No PII leakage
- Size and token estimates
- Duplicate detection
- Quality metrics

Usage:
    python validate_finetune_dataset.py <jsonl_path>
"""

import os
import sys
import json
import re
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

# PII patterns (same as prompt_manager)
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
}


def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
    """Load JSONL file."""
    examples = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                example = json.loads(line)
                examples.append(example)
            except json.JSONDecodeError as e:
                logger.error(f"Line {line_num}: JSON decode error: {e}")
    
    logger.info(f"Loaded {len(examples)} examples from {filepath}")
    return examples


def validate_schema(examples: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    """
    Validate schema of examples.
    
    Expected format:
    {
        "prompt": str,
        "completion": str (valid JSON),
        "metadata": dict
    }
    
    Returns:
        Tuple of (valid_count, issues)
    """
    issues = []
    valid_count = 0
    
    for idx, example in enumerate(examples):
        example_issues = []
        
        # Check required fields
        if 'prompt' not in example:
            example_issues.append("missing 'prompt' field")
        elif not isinstance(example['prompt'], str):
            example_issues.append("'prompt' must be string")
        elif len(example['prompt']) < 100:
            example_issues.append("'prompt' too short (< 100 chars)")
        
        if 'completion' not in example:
            example_issues.append("missing 'completion' field")
        elif not isinstance(example['completion'], str):
            example_issues.append("'completion' must be string")
        else:
            # Validate completion is valid JSON
            try:
                completion_json = json.loads(example['completion'])
                
                # Check for required fields in completion
                if 'analystInsights' not in completion_json:
                    example_issues.append("completion missing 'analystInsights'")
                if 'businessSummary' not in completion_json:
                    example_issues.append("completion missing 'businessSummary'")
            except json.JSONDecodeError:
                example_issues.append("'completion' is not valid JSON")
        
        if 'metadata' not in example:
            example_issues.append("missing 'metadata' field")
        elif not isinstance(example['metadata'], dict):
            example_issues.append("'metadata' must be dict")
        
        if example_issues:
            issues.append(f"Example {idx+1}: {', '.join(example_issues)}")
        else:
            valid_count += 1
    
    return valid_count, issues


def check_pii_leakage(examples: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    """
    Check for PII patterns in prompts and completions.
    
    Returns:
        Tuple of (clean_count, pii_issues)
    """
    pii_issues = []
    clean_count = 0
    
    for idx, example in enumerate(examples):
        example_pii = []
        
        # Check prompt
        prompt = example.get('prompt', '')
        for pii_type, pattern in PII_PATTERNS.items():
            matches = re.findall(pattern, prompt)
            if matches:
                # Filter out masked patterns (e.g., "***@example.com")
                unmasked = [m for m in matches if '***' not in m]
                if unmasked:
                    example_pii.append(f"{pii_type} in prompt: {len(unmasked)} instances")
        
        # Check completion
        completion = example.get('completion', '')
        for pii_type, pattern in PII_PATTERNS.items():
            matches = re.findall(pattern, completion)
            if matches:
                unmasked = [m for m in matches if '***' not in m]
                if unmasked:
                    example_pii.append(f"{pii_type} in completion: {len(unmasked)} instances")
        
        if example_pii:
            pii_issues.append(f"Example {idx+1}: {', '.join(example_pii)}")
        else:
            clean_count += 1
    
    return clean_count, pii_issues


def estimate_tokens(text: str) -> int:
    """Rough token estimate (chars / 4)."""
    return len(text) // 4


def analyze_sizes(examples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze size statistics.
    
    Returns:
        Dictionary with size metrics
    """
    prompt_lengths = []
    completion_lengths = []
    prompt_tokens = []
    completion_tokens = []
    
    for example in examples:
        prompt = example.get('prompt', '')
        completion = example.get('completion', '')
        
        prompt_lengths.append(len(prompt))
        completion_lengths.append(len(completion))
        prompt_tokens.append(estimate_tokens(prompt))
        completion_tokens.append(estimate_tokens(completion))
    
    if not examples:
        return {}
    
    return {
        "total_examples": len(examples),
        "prompt_chars": {
            "min": min(prompt_lengths),
            "max": max(prompt_lengths),
            "avg": sum(prompt_lengths) / len(prompt_lengths),
            "total": sum(prompt_lengths)
        },
        "completion_chars": {
            "min": min(completion_lengths),
            "max": max(completion_lengths),
            "avg": sum(completion_lengths) / len(completion_lengths),
            "total": sum(completion_lengths)
        },
        "prompt_tokens_est": {
            "min": min(prompt_tokens),
            "max": max(prompt_tokens),
            "avg": sum(prompt_tokens) / len(prompt_tokens),
            "total": sum(prompt_tokens)
        },
        "completion_tokens_est": {
            "min": min(completion_tokens),
            "max": max(completion_tokens),
            "avg": sum(completion_tokens) / len(completion_tokens),
            "total": sum(completion_tokens)
        }
    }


def detect_duplicates(examples: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    """
    Detect highly similar duplicates based on prompt hash.
    
    Returns:
        Tuple of (unique_count, duplicate_issues)
    """
    from hashlib import sha256
    
    prompt_hashes = []
    duplicate_issues = []
    
    for idx, example in enumerate(examples):
        prompt = example.get('prompt', '')
        prompt_hash = sha256(prompt.encode('utf-8')).hexdigest()
        prompt_hashes.append((idx, prompt_hash))
    
    # Find duplicates
    hash_counts = Counter(h for _, h in prompt_hashes)
    duplicates = {h: count for h, count in hash_counts.items() if count > 1}
    
    if duplicates:
        for hash_val, count in duplicates.items():
            indices = [idx+1 for idx, h in prompt_hashes if h == hash_val]
            duplicate_issues.append(f"Duplicate prompt hash {hash_val[:8]}... found in examples: {indices}")
    
    unique_count = len(examples) - sum(count - 1 for count in duplicates.values())
    
    return unique_count, duplicate_issues


def generate_report(
    filepath: str,
    examples: List[Dict[str, Any]],
    schema_valid: int,
    schema_issues: List[str],
    pii_clean: int,
    pii_issues: List[str],
    size_stats: Dict[str, Any],
    unique_count: int,
    duplicate_issues: List[str]
) -> Dict[str, Any]:
    """Generate validation report."""
    
    total = len(examples)
    
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dataset_path": filepath,
        "total_examples": total,
        "validation": {
            "schema_valid": schema_valid,
            "schema_pass_rate": round(schema_valid / total * 100, 2) if total > 0 else 0,
            "schema_issues_count": len(schema_issues),
            "pii_clean": pii_clean,
            "pii_pass_rate": round(pii_clean / total * 100, 2) if total > 0 else 0,
            "pii_issues_count": len(pii_issues),
            "unique_examples": unique_count,
            "duplicate_count": total - unique_count
        },
        "size_statistics": size_stats,
        "issues": {
            "schema": schema_issues[:20],  # Limit to first 20
            "pii": pii_issues[:20],
            "duplicates": duplicate_issues[:20]
        },
        "quality_score": _calculate_quality_score(
            schema_valid, pii_clean, unique_count, total
        )
    }
    
    return report


def _calculate_quality_score(schema_valid: int, pii_clean: int, unique: int, total: int) -> int:
    """Calculate overall quality score 0-100."""
    if total == 0:
        return 0
    
    schema_score = (schema_valid / total) * 40
    pii_score = (pii_clean / total) * 30
    unique_score = (unique / total) * 30
    
    return int(schema_score + pii_score + unique_score)


def main():
    parser = argparse.ArgumentParser(
        description="Validate fine-tuning dataset JSONL"
    )
    parser.add_argument(
        'jsonl_path',
        type=str,
        help='Path to JSONL file to validate'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output report path (default: reports/finetune_export_report_TIMESTAMP.json)'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Load examples
    logger.info(f"Loading {args.jsonl_path}...")
    examples = load_jsonl(args.jsonl_path)
    
    if not examples:
        logger.error("No examples loaded. Exiting.")
        return
    
    # Validate schema
    logger.info("Validating schema...")
    schema_valid, schema_issues = validate_schema(examples)
    
    # Check PII
    logger.info("Checking for PII leakage...")
    pii_clean, pii_issues = check_pii_leakage(examples)
    
    # Analyze sizes
    logger.info("Analyzing sizes...")
    size_stats = analyze_sizes(examples)
    
    # Detect duplicates
    logger.info("Detecting duplicates...")
    unique_count, duplicate_issues = detect_duplicates(examples)
    
    # Generate report
    report = generate_report(
        args.jsonl_path,
        examples,
        schema_valid,
        schema_issues,
        pii_clean,
        pii_issues,
        size_stats,
        unique_count,
        duplicate_issues
    )
    
    # Save report
    if args.output:
        output_path = args.output
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        output_filename = f"finetune_export_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = os.path.join(reports_dir, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Report saved to {output_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("FINE-TUNING DATASET VALIDATION REPORT")
    print("="*60)
    print(f"Dataset: {args.jsonl_path}")
    print(f"Total examples: {report['total_examples']}")
    print(f"\nValidation Results:")
    print(f"  Schema valid: {schema_valid}/{report['total_examples']} ({report['validation']['schema_pass_rate']}%)")
    print(f"  PII clean: {pii_clean}/{report['total_examples']} ({report['validation']['pii_pass_rate']}%)")
    print(f"  Unique examples: {unique_count}/{report['total_examples']}")
    print(f"  Duplicates: {report['validation']['duplicate_count']}")
    print(f"\nQuality Score: {report['quality_score']}/100")
    
    if size_stats:
        print(f"\nSize Statistics:")
        print(f"  Avg prompt: {size_stats['prompt_chars']['avg']:.0f} chars ({size_stats['prompt_tokens_est']['avg']:.0f} tokens)")
        print(f"  Avg completion: {size_stats['completion_chars']['avg']:.0f} chars ({size_stats['completion_tokens_est']['avg']:.0f} tokens)")
        print(f"  Total tokens (est): {size_stats['prompt_tokens_est']['total'] + size_stats['completion_tokens_est']['total']:,}")
    
    if schema_issues:
        print(f"\nSchema Issues ({len(schema_issues)}):")
        for issue in schema_issues[:5]:
            print(f"  - {issue}")
        if len(schema_issues) > 5:
            print(f"  ... and {len(schema_issues) - 5} more")
    
    if pii_issues:
        print(f"\n⚠️  PII Issues ({len(pii_issues)}):")
        for issue in pii_issues[:5]:
            print(f"  - {issue}")
        if len(pii_issues) > 5:
            print(f"  ... and {len(pii_issues) - 5} more")
    
    if duplicate_issues:
        print(f"\nDuplicate Issues ({len(duplicate_issues)}):")
        for issue in duplicate_issues[:3]:
            print(f"  - {issue}")
        if len(duplicate_issues) > 3:
            print(f"  ... and {len(duplicate_issues) - 3} more")
    
    print(f"\nFull report: {output_path}")
    
    # Exit code based on quality
    if report['quality_score'] < 70:
        print("\n⚠️  Quality score below 70. Review issues before using for fine-tuning.")
        sys.exit(1)
    else:
        print("\n✓ Dataset validation passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
