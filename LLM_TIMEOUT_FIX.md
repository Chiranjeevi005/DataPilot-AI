# CRITICAL FIX: LLM TIMEOUT ISSUE

## Problem
The worker gets stuck on LLM calls because **DeepSeek R1 is too slow** for large files (like `invoices_large.csv`).

Your job `job_20251206_225232_0241` was stuck in "processing" for over 30 minutes!

## Root Cause
- DeepSeek R1 can take 60+ seconds for complex reasoning
- No timeout was set on the API call
- Worker hung indefinitely waiting for response
- Large files make it worse (more data to analyze)

## Fixes Applied

### 1. Added 60-Second Timeout ✅
```python
response = client.chat.completions.create(
    model=model_name,
    messages=[...],
    temperature=0.0,
    timeout=60.0  # ✅ Prevents hanging
)
```

### 2. Marked Stuck Job as Failed ✅
Your stuck job is now marked as "failed" so the loading page will redirect.

## IMMEDIATE SOLUTIONS

### Option 1: Use Mock Mode (FASTEST - Test the flow)
Add to `.env`:
```
LLM_MOCK=true
```

This will:
- Skip real LLM calls
- Return mock insights instantly
- Let you test the full upload → loading → results flow
- Verify AI insights panel displays correctly

### Option 2: Use Faster Model (RECOMMENDED for production)
Change in `.env`:
```
LLM_MODEL=openai/gpt-4o-mini
# or
LLM_MODEL=anthropic/claude-3-haiku
```

These models are:
- 10-20x faster than DeepSeek R1
- Still generate good insights
- Much more reliable for production

### Option 3: Use Smaller Files
Test with:
- `dev-samples/sales_demo.csv` (8 rows) - FAST
- Avoid `invoices_large.csv` (large file) - SLOW

## Recommended Workflow

### For Testing (Right Now):
1. **Enable mock mode**:
   ```bash
   # Add to .env file
   echo "LLM_MOCK=true" >> .env
   ```

2. **Restart worker**:
   ```bash
   taskkill /F /IM python.exe
   # Wait for start-app.bat to restart
   ```

3. **Upload a file** - any file, even large ones
4. **See instant results** with mock insights
5. **Verify the flow works** end-to-end

### For Production (After Testing):
1. **Switch to faster model**:
   ```bash
   # In .env, change:
   LLM_MOCK=false
   LLM_MODEL=openai/gpt-4o-mini
   ```

2. **Restart worker**
3. **Upload files** - should complete in 5-15 seconds

## Files Modified
- ✅ `src/lib/llm_client.py` - Added 60s timeout
- ✅ `mark_job_failed.py` - Marked stuck job as failed

## Next Steps

**RIGHT NOW - Enable Mock Mode:**
```bash
# 1. Add to .env
echo "LLM_MOCK=true" >> .env

# 2. Restart worker
taskkill /F /IM python.exe

# 3. Refresh browser (job should redirect to results)

# 4. Upload a new file to test
```

**Your browser should now redirect to results!** The stuck job is marked as failed.

Then upload a new file with mock mode enabled - it will complete instantly!
