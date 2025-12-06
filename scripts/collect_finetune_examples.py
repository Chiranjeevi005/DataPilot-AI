"""
Collect Fine-Tuning Examples from Human Feedback

Scans data/feedback/ for approved/edited examples and exports them as JSONL
for instruction-tuning fine-tuning workflows.

Usage:
    python collect_finetune_examples.py [--sample N] [--min-score 3]
"""

import os
import sys
import json
import argparse
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.prompt_manager import build_prompt, get_prompt_hash

logger = logging.getLogger(__name__)


def load_feedback_files(feedback_dir: str) -> List[Dict[str, Any]]:
    """
    Load all feedback files from directory.
    
    Args:
        feedback_dir: Path to feedback directory
        
    Returns:
        List of feedback data dictionaries
    """
    feedback_files = []
    
    if not os.path.exists(feedback_dir):
        logger.warning(f"Feedback directory not found: {feedback_dir}")
        return []
    
    for filename in os.listdir(feedback_dir):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(feedback_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                feedback_files.append(data)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
    
    logger.info(f"Loaded {len(feedback_files)} feedback files")
    return feedback_files


def extract_finetune_examples(
    feedback_files: List[Dict[str, Any]],
    min_score: int = 3
) -> List[Dict[str, Any]]:
    """
    Extract fine-tuning examples from feedback files.
    
    Only includes:
    - Approved insights with score >= min_score
    - Edited insights with score >= min_score (using edited version)
    
    Args:
        feedback_files: List of feedback data
        min_score: Minimum human_score to include (1-5)
        
    Returns:
        List of fine-tuning examples
    """
    examples = []
    
    for feedback in feedback_files:
        compact_eda = feedback.get('compact_eda', {})
        llm_output = feedback.get('llm_output', {})
        feedback_items = feedback.get('feedback_items', [])
        job_id = feedback.get('job_id', 'unknown')
        reviewer_id = feedback.get('reviewer_id', 'anonymous')
        overall_score = feedback.get('overall_score', 0)
        
        # Build approved output with human corrections
        approved_insights = []
        
        for item in feedback_items:
            action = item.get('action')
            human_score = item.get('human_score', 0)
            insight_id = item.get('insight_id')
            
            # Skip rejected or low-scored insights
            if action == 'reject' or human_score < min_score:
                continue
            
            # Find original insight
            original_insight = None
            for insight in llm_output.get('analystInsights', []):
                if insight.get('id') == insight_id:
                    original_insight = insight
                    break
            
            if not original_insight:
                continue
            
            # Use edited version if available, otherwise original
            if action == 'edit':
                approved_insight = {
                    "id": insight_id,
                    "text": item.get('edited_text', original_insight.get('text')),
                    "severity": original_insight.get('severity'),
                    "category": original_insight.get('category'),
                    "evidence": item.get('edited_evidence', original_insight.get('evidence')),
                    "recommendation": item.get('edited_recommendation', original_insight.get('recommendation'))
                }
            else:  # approve
                approved_insight = original_insight
            
            approved_insights.append(approved_insight)
        
        # Only create example if we have approved insights
        if approved_insights:
            approved_output = {
                "analystInsights": approved_insights,
                "businessSummary": llm_output.get('businessSummary', []),
                "visualActions": llm_output.get('visualActions', []),
                "metadata": llm_output.get('metadata', {})
            }
            
            examples.append({
                "compact_eda": compact_eda,
                "approved_output": approved_output,
                "metadata": {
                    "job_id": job_id,
                    "reviewer_id": reviewer_id,
                    "overall_score": overall_score,
                    "approved_insight_count": len(approved_insights)
                }
            })
    
    logger.info(f"Extracted {len(examples)} fine-tuning examples")
    return examples


def deduplicate_examples(examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove near-duplicate examples based on compact_eda hash.
    
    Args:
        examples: List of fine-tuning examples
        
    Returns:
        Deduplicated list
    """
    seen_hashes = set()
    deduplicated = []
    
    for example in examples:
        # Hash compact_eda to detect duplicates
        eda_str = json.dumps(example['compact_eda'], sort_keys=True)
        eda_hash = hashlib.sha256(eda_str.encode('utf-8')).hexdigest()
        
        if eda_hash not in seen_hashes:
            seen_hashes.add(eda_hash)
            deduplicated.append(example)
    
    removed = len(examples) - len(deduplicated)
    if removed > 0:
        logger.info(f"Removed {removed} duplicate examples")
    
    return deduplicated


def format_for_finetuning(examples: List[Dict[str, Any]], shot_count: int = 3) -> List[Dict[str, Any]]:
    """
    Format examples for fine-tuning.
    
    Creates instruction-tuning format:
    {
        "prompt": "<system_prompt + few_shots + compact_eda>",
        "completion": "<approved_output_json>",
        "metadata": {...}
    }
    
    Args:
        examples: List of extracted examples
        shot_count: Number of few-shot examples to include in prompt
        
    Returns:
        List of formatted fine-tuning examples
    """
    formatted = []
    
    for example in examples:
        compact_eda = example['compact_eda']
        approved_output = example['approved_output']
        metadata = example['metadata']
        
        # Build prompt using prompt_manager
        try:
            prompt = build_prompt(compact_eda, shot_count=shot_count)
        except Exception as e:
            logger.error(f"Failed to build prompt for job {metadata.get('job_id')}: {e}")
            continue
        
        # Format completion as JSON string
        completion = json.dumps(approved_output, ensure_ascii=False)
        
        formatted.append({
            "prompt": prompt,
            "completion": completion,
            "metadata": {
                "job_id": metadata.get('job_id'),
                "reviewer_id": metadata.get('reviewer_id'),
                "overall_score": metadata.get('overall_score'),
                "approved_insight_count": metadata.get('approved_insight_count'),
                "prompt_length": len(prompt),
                "completion_length": len(completion)
            }
        })
    
    return formatted


def export_jsonl(examples: List[Dict[str, Any]], output_path: str):
    """
    Export examples to JSONL file.
    
    Args:
        examples: List of formatted examples
        output_path: Path to output JSONL file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    logger.info(f"Exported {len(examples)} examples to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Collect fine-tuning examples from human feedback"
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help='Sample N examples for quick experiments (default: all)'
    )
    parser.add_argument(
        '--min-score',
        type=int,
        default=3,
        help='Minimum human score to include (1-5, default: 3)'
    )
    parser.add_argument(
        '--shot-count',
        type=int,
        default=3,
        help='Number of few-shot examples in prompt (default: 3)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSONL path (default: data/finetune_ready/finetune_YYYYMMDD.jsonl)'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    feedback_dir = os.path.join(base_dir, "data", "feedback")
    
    if args.output:
        output_path = args.output
    else:
        output_dir = os.path.join(base_dir, "data", "finetune_ready")
        output_filename = f"finetune_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        output_path = os.path.join(output_dir, output_filename)
    
    # Load feedback
    logger.info("Loading feedback files...")
    feedback_files = load_feedback_files(feedback_dir)
    
    if not feedback_files:
        logger.error("No feedback files found. Exiting.")
        return
    
    # Extract examples
    logger.info(f"Extracting examples (min_score={args.min_score})...")
    examples = extract_finetune_examples(feedback_files, min_score=args.min_score)
    
    if not examples:
        logger.error("No examples extracted. Exiting.")
        return
    
    # Deduplicate
    logger.info("Deduplicating examples...")
    examples = deduplicate_examples(examples)
    
    # Sample if requested
    if args.sample and args.sample < len(examples):
        logger.info(f"Sampling {args.sample} examples...")
        import random
        examples = random.sample(examples, args.sample)
    
    # Format for fine-tuning
    logger.info("Formatting for fine-tuning...")
    formatted = format_for_finetuning(examples, shot_count=args.shot_count)
    
    # Export
    logger.info(f"Exporting to {output_path}...")
    export_jsonl(formatted, output_path)
    
    # Summary
    print("\n" + "="*60)
    print("FINE-TUNING DATASET EXPORT COMPLETE")
    print("="*60)
    print(f"Total examples: {len(formatted)}")
    print(f"Output file: {output_path}")
    print(f"Min score filter: {args.min_score}")
    print(f"Few-shot count: {args.shot_count}")
    
    if formatted:
        avg_prompt_len = sum(ex['metadata']['prompt_length'] for ex in formatted) / len(formatted)
        avg_completion_len = sum(ex['metadata']['completion_length'] for ex in formatted) / len(formatted)
        print(f"\nAverage prompt length: {avg_prompt_len:.0f} chars")
        print(f"Average completion length: {avg_completion_len:.0f} chars")
    
    print("\nNext steps:")
    print(f"  1. Review {output_path}")
    print(f"  2. Run validation: python scripts/validate_finetune_dataset.py {output_path}")
    print("  3. Upload to fine-tuning platform (OpenAI, Anthropic, etc.)")


if __name__ == "__main__":
    main()
