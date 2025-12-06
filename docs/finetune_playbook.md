# Fine-Tuning Playbook for DataPilot AI

This guide explains how to collect human feedback, export fine-tuning datasets, and prepare for instruction-tuning of LLMs to improve DataPilot insight generation.

## Table of Contents
1. [Overview](#overview)
2. [Collecting Human Feedback](#collecting-human-feedback)
3. [Exporting Fine-Tuning Dataset](#exporting-fine-tuning-dataset)
4. [Validating Dataset Quality](#validating-dataset-quality)
5. [Fine-Tuning Hyperparameters](#fine-tuning-hyperparameters)
6. [Vendor-Specific Instructions](#vendor-specific-instructions)
7. [Evaluating Performance](#evaluating-performance)

---

## Overview

The DataPilot fine-tuning pipeline follows this workflow:

```
1. LLM generates insights (few-shot prompts)
   ↓
2. Human reviewers approve/edit/reject insights
   ↓
3. Collect approved examples into JSONL dataset
   ↓
4. Validate dataset quality (schema, PII, duplicates)
   ↓
5. Upload to fine-tuning platform
   ↓
6. Fine-tune model with instruction-tuning
   ↓
7. Evaluate fine-tuned vs few-shot performance
```

**Goal**: Improve LLM output quality by learning from human-approved examples, reducing reliance on few-shot prompts over time.

---

## Collecting Human Feedback

### Method 1: CLI Review Tool

Use the interactive CLI tool to review job results:

```bash
cd src/collectors
python feedback_collector.py <job_id> <path_to_result.json>
```

**Example**:
```bash
python feedback_collector.py job_abc123 ../../tmp_uploads/results/result_abc123.json
```

**Workflow**:
1. Tool displays each insight with text, evidence, and recommendation
2. Reviewer chooses action:
   - `[a]` Approve (with quality score 1-5)
   - `[e]` Edit (modify text/evidence, with score)
   - `[r]` Reject (with reason)
   - `[s]` Skip
3. Provide overall quality score (1-5)
4. Feedback saved to `data/feedback/feedback_<job_id>_<timestamp>.json`

### Method 2: Programmatic API

```python
from src.collectors.feedback_collector import FeedbackCollector

collector = FeedbackCollector()

feedback_items = [
    {
        "insight_id": "i1",
        "action": "approve",
        "human_score": 5,
        "notes": "Excellent outlier detection"
    },
    {
        "insight_id": "i2",
        "action": "edit",
        "edited_text": "Corrected insight text...",
        "edited_evidence": {...},
        "edited_recommendation": {...},
        "human_score": 4,
        "notes": "Fixed evidence mapping"
    },
    {
        "insight_id": "i3",
        "action": "reject",
        "human_score": 1,
        "notes": "Hallucinated values not in data"
    }
]

collector.collect_feedback(
    job_id="job_abc123",
    compact_eda=compact_eda_dict,
    llm_output=llm_output_dict,
    feedback_items=feedback_items,
    reviewer_id="analyst_jane",
    overall_score=4
)
```

### Feedback Quality Guidelines

**Approve** insights that:
- ✅ Have accurate evidence (aggregates match KPIs, row_indices valid)
- ✅ Provide actionable recommendations
- ✅ Are clearly written and business-relevant
- ✅ Correctly identify severity and category

**Edit** insights that:
- ⚠️ Have minor text clarity issues
- ⚠️ Need evidence refinement
- ⚠️ Require recommendation adjustments
- ⚠️ Are mostly correct but need polish

**Reject** insights that:
- ❌ Hallucinate values not in data
- ❌ Have invalid evidence mappings
- ❌ Are too generic or not actionable
- ❌ Misidentify severity or category

---

## Exporting Fine-Tuning Dataset

### Basic Export

Export all approved/edited examples with score ≥ 3:

```bash
cd scripts
python collect_finetune_examples.py
```

Output: `data/finetune_ready/finetune_YYYYMMDD.jsonl`

### Advanced Options

```bash
# Export only high-quality examples (score ≥ 4)
python collect_finetune_examples.py --min-score 4

# Sample 50 examples for quick experiment
python collect_finetune_examples.py --sample 50

# Use 5 few-shot examples in prompts (default: 3)
python collect_finetune_examples.py --shot-count 5

# Custom output path
python collect_finetune_examples.py --output /path/to/custom.jsonl
```

### Output Format

Each line in JSONL:

```json
{
  "prompt": "<system_prompt + few_shot_examples + compact_eda>",
  "completion": "<approved_output_json>",
  "metadata": {
    "job_id": "job_abc123",
    "reviewer_id": "analyst_jane",
    "overall_score": 5,
    "approved_insight_count": 3,
    "prompt_length": 4500,
    "completion_length": 850
  }
}
```

---

## Validating Dataset Quality

Before uploading to fine-tuning platform, validate dataset:

```bash
cd scripts
python validate_finetune_dataset.py ../data/finetune_ready/finetune_20241206.jsonl
```

**Validation Checks**:
- ✅ Schema correctness (prompt, completion, metadata fields)
- ✅ No PII leakage (emails, phones, SSNs masked)
- ✅ Size and token estimates
- ✅ Duplicate detection (removes near-duplicates)
- ✅ Quality score (0-100)

**Output**: `reports/finetune_export_report_TIMESTAMP.json`

**Quality Thresholds**:
- **90-100**: Excellent, ready for fine-tuning
- **70-89**: Good, review flagged issues
- **<70**: Poor, fix issues before proceeding

---

## Fine-Tuning Hyperparameters

### Recommended Settings

Based on instruction-tuning best practices for DeepSeek R1 / similar models:

| Parameter | Recommended Value | Notes |
|-----------|------------------|-------|
| **Learning Rate** | `5e-6` to `1e-5` | Lower for larger datasets |
| **Epochs** | `3-5` | Monitor validation loss |
| **Batch Size** | `4-8` | Adjust based on GPU memory |
| **Validation Split** | `10-15%` | Holdout for early stopping |
| **Warmup Steps** | `100-500` | 10% of total steps |
| **Max Sequence Length** | `2048-4096` | Based on prompt+completion length |
| **LoRA Rank** (if using) | `8-16` | For parameter-efficient tuning |

### Training Duration Estimates

| Dataset Size | GPU | Estimated Time |
|--------------|-----|----------------|
| 50 examples | A100 (40GB) | 30-60 min |
| 200 examples | A100 (40GB) | 2-4 hours |
| 500 examples | A100 (40GB) | 6-10 hours |
| 1000+ examples | A100 (40GB) | 12-24 hours |

### Early Stopping

Monitor validation metrics:
- **Validation Loss**: Stop if no improvement for 2 epochs
- **Schema Validation Rate**: Target >95%
- **Evidence Accuracy**: Target >90%

---

## Vendor-Specific Instructions

### OpenAI Fine-Tuning

```bash
# Install OpenAI CLI
pip install openai

# Upload dataset
openai api fine_tunes.create \
  -t data/finetune_ready/finetune_20241206.jsonl \
  -m gpt-3.5-turbo \
  --n_epochs 3 \
  --learning_rate_multiplier 0.1

# Monitor progress
openai api fine_tunes.follow -i <fine_tune_id>

# Use fine-tuned model
# Update .env: LLM_MODEL=ft:gpt-3.5-turbo:<fine_tune_id>
```

### Anthropic (Claude)

```bash
# Contact Anthropic for fine-tuning access
# Upload JSONL via Anthropic Console
# Follow Anthropic's instruction-tuning guidelines
```

### Local Fine-Tuning (Hugging Face)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from datasets import load_dataset

# Load model
model = AutoModelForCausalLM.from_pretrained("deepseek-ai/deepseek-r1")
tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/deepseek-r1")

# Load dataset
dataset = load_dataset("json", data_files="data/finetune_ready/finetune_20241206.jsonl")

# Training arguments
training_args = TrainingArguments(
    output_dir="./models/datapilot-finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=5e-6,
    warmup_steps=100,
    logging_steps=10,
    save_steps=100,
    evaluation_strategy="steps",
    eval_steps=50,
    load_best_model_at_end=True
)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"]
)

trainer.train()
```

---

## Evaluating Performance

### Compare Few-Shot vs Fine-Tuned

```bash
cd scripts

# Create holdout test set (10-20% of feedback data)
# Format: same as seed_examples.jsonl

python eval_fewshot_vs_finetuned.py \
  --holdout ../data/finetune_samples/holdout_test.jsonl \
  --finetuned-endpoint https://api.openai.com/v1/chat/completions
```

**Metrics**:
- **Schema Validation Pass Rate**: % of outputs with valid schema
- **Evidence Mapping Accuracy**: % of insights with valid evidence
- **BLEU/ROUGE** (optional): Similarity to human-approved outputs

**Expected Improvements**:
- Schema pass rate: 95% → 98%+
- Evidence accuracy: 85% → 95%+
- Reduced need for few-shot examples (can use 0-1 instead of 3)

### A/B Testing in Production

1. Route 50% of jobs to few-shot pipeline
2. Route 50% to fine-tuned model
3. Collect feedback on both
4. Compare approval rates and quality scores

---

## Best Practices

### Data Collection
- ✅ Collect feedback from multiple reviewers for diversity
- ✅ Aim for 200+ high-quality examples before first fine-tune
- ✅ Cover diverse scenarios (outliers, missing data, correlations, etc.)
- ✅ Include both simple and complex datasets

### Dataset Curation
- ✅ Remove duplicates (handled automatically by validation script)
- ✅ Balance categories (outlier, correlation, trend, quality, etc.)
- ✅ Ensure PII is masked (validation script checks this)
- ✅ Maintain 10-15% holdout set for evaluation

### Iteration
- ✅ Start with seed examples (10 provided in `data/finetune_samples/`)
- ✅ Fine-tune on 50-100 examples initially
- ✅ Evaluate, collect more feedback, re-train
- ✅ Iterate monthly or when 100+ new examples collected

### Monitoring
- ✅ Track schema validation rate over time
- ✅ Monitor evidence accuracy
- ✅ Collect human approval rates
- ✅ Watch for model drift (re-train quarterly)

---

## Troubleshooting

### Low Quality Score (<70)

**Causes**:
- PII not masked → Check `prompt_manager.py` PII masking
- Schema errors → Review `insight_validator.py` normalization
- Duplicates → Run deduplication in `collect_finetune_examples.py`

**Fix**: Address validation issues, re-export dataset

### Fine-Tuning Overfitting

**Symptoms**:
- Perfect training loss, poor validation loss
- Model memorizes examples instead of generalizing

**Fix**:
- Reduce epochs (3 → 2)
- Increase dataset size (add more diverse examples)
- Use LoRA instead of full fine-tuning

### Fine-Tuned Model Worse Than Few-Shot

**Causes**:
- Insufficient training data (<50 examples)
- Poor quality feedback (low scores, inconsistent edits)
- Hyperparameters too aggressive

**Fix**:
- Collect 200+ high-quality examples
- Review feedback guidelines with reviewers
- Lower learning rate, reduce epochs

---

## Next Steps

1. **Week 1**: Collect feedback on 50-100 jobs using CLI tool
2. **Week 2**: Export dataset, validate quality (target score >80)
3. **Week 3**: Upload to fine-tuning platform, train first model
4. **Week 4**: Evaluate performance, iterate based on results

**Long-term**: Aim for 500+ examples over 3 months, re-train quarterly, maintain >95% schema validation rate.

---

## Support

- **Issues**: Check `data/llm_logs/` for audit logs
- **Validation Errors**: Review `reports/finetune_export_report_*.json`
- **Performance**: Run `eval_fewshot_vs_finetuned.py` on holdout set

For questions, consult the main `README.md` or review source code in `src/lib/`.
