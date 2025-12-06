# AI Insights Panel Fix - Summary

## Problem
The AI insights panel on the results page was not displaying any insights, even though the LLM was generating them.

## Root Cause
There was a **naming mismatch** between what the LLM was generating and what the validator/frontend expected:

### The Flow:
1. **Prompt** (`prompts/analyst_prompt.txt`) asked LLM to generate: `analystInsights`
2. **Validator** (`src/lib/llm/validator.py`) expected: `insightsAnalyst` and `insightsBusiness`
3. **Frontend** (`src/app/results/page.tsx`) expected: `insightsAnalyst` and `insightsBusiness`

The LLM was generating data with the wrong field names, so the validator couldn't find them and returned empty arrays.

## Changes Made

### 1. Updated Prompt Template (`prompts/analyst_prompt.txt`)
- ✅ Changed `analystInsights` → `insightsAnalyst`
- ✅ Added `insightsBusiness` field (was missing entirely)
- ✅ Updated JSON structure to match `InsightItem` interface:
  - Added `title` field
  - Changed `text` → `summary`
  - Added `severity` field ("info", "warning", "critical")
  - Changed `evidence` from object to array of evidence items
  - Added `recommendation` field
- ✅ Updated `businessSummary` from string array to object array with `text` and `evidenceKeys`
- ✅ Cleaned up duplicate content in the prompt
- ✅ Updated rules to reflect new structure

### 2. Updated Mock Response (`src/lib/llm_client.py`)
- ✅ Changed `_get_mock_response()` to use `insightsAnalyst` and `insightsBusiness`
- ✅ Updated structure to match `InsightItem` interface
- ✅ Added proper evidence array format
- ✅ Updated `businessSummary` structure

### 3. Updated Fallback Response (`src/lib/llm_client.py`)
- ✅ Changed `_get_fallback_response()` to use `insightsAnalyst` and `insightsBusiness`
- ✅ Updated `businessSummary` structure

## Expected Behavior After Fix

### When LLM_MOCK=true (Mock Mode)
The insights panel should display:
- **Analyst Mode**: 1 mock analyst insight with evidence
- **Business Mode**: 1 mock business insight with recommendation

### When LLM_MOCK=false (Real LLM)
The insights panel should display:
- **Analyst Mode**: 3-5 technical/data-focused insights from DeepSeek R1
- **Business Mode**: 2-3 strategic/actionable business insights
- Each insight includes:
  - Title and summary
  - Severity indicator (info/warning/critical)
  - Evidence with row references (clickable to highlight in data preview)
  - Optional recommendations

## Testing Instructions

### Option 1: Test with Mock Mode
1. Ensure `.env` has `LLM_MOCK=true`
2. Upload any CSV file (e.g., `dev-samples/sales_demo.csv`)
3. Navigate to results page
4. Verify insights panel shows mock insights in both tabs

### Option 2: Test with Real LLM
1. Ensure `.env` has:
   - `LLM_MOCK=false`
   - `OPENROUTER_API_KEY=your_key`
   - `LLM_MODEL=deepseek/deepseek-r1`
2. Upload a CSV file
3. Navigate to results page
4. Verify insights panel shows AI-generated insights

## Files Modified
1. `prompts/analyst_prompt.txt` - Updated JSON structure and field names
2. `src/lib/llm_client.py` - Updated mock and fallback responses

## Files Verified (No Changes Needed)
1. `src/lib/llm/validator.py` - Already expecting correct field names
2. `src/lib/analysis/transform_to_ui.py` - Already mapping correctly
3. `src/components/results/InsightsPanel.tsx` - Already expecting correct props
4. `src/app/results/page.tsx` - Already passing correct props
5. `src/types/analysis.ts` - Interface definitions are correct

## Next Steps
1. Restart the application to pick up the new prompt template
2. Test with a sample file upload
3. Verify both Analyst and Business tabs show insights
4. Check that evidence highlighting works when clicking row references
