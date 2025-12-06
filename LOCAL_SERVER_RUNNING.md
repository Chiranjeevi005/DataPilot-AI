# 🚀 DataPilot AI - Local Server Running!

## ✅ All Services Started Successfully!

### Running Services:

1. **✅ Redis** - Running on `localhost:6379`
2. **✅ Worker** - Processing jobs in background
3. **✅ API Server** - Running on `http://localhost:5328`
4. **✅ Frontend** - Running on `http://localhost:3003`

---

## 🌐 Access the Application

**Open your browser and go to:**

```
http://localhost:3003
```

---

## 📤 How to Upload a File and Get Insights

### Step 1: Open the Web App
- Navigate to `http://localhost:3003` in your browser
- You'll see the DataPilot AI landing page

### Step 2: Upload Your File
- Click on the **Upload** or **Get Started** button
- Select a file from your PC:
  - **Supported formats**: CSV, XLSX, JSON, PDF
  - **Max size**: 20 MB
  - **Best results**: CSV or XLSX files with tabular data

### Step 3: Wait for Processing
- The file will be uploaded to the backend
- The worker will process it (usually 10-60 seconds)
- You'll see a loading screen with status updates

### Step 4: View Insights
Once processing is complete, you'll see:

✅ **Data Schema** - Column types, missing values, unique counts
✅ **Key Performance Indicators (KPIs)** - Row/column counts, duplicates, statistics
✅ **Cleaned Preview** - First 20 rows of your data
✅ **AI-Generated Insights** - Business insights from DeepSeek R1
✅ **Visualizations** - Auto-generated charts (time series, distributions)
✅ **Quality Score** - Data quality assessment (0-100)

---

## 🤖 What Insights Will You Get?

DataPilot AI uses **OpenRouter's DeepSeek R1** model to generate:

### 1. **Analyst Insights** (AI-Powered)
- **Outlier Detection**: "Revenue spike of $50,000 on 2024-03-15 (5x normal)"
- **Missing Data**: "Email field has 23% missing values (45 out of 200 rows)"
- **Correlations**: "Marketing spend strongly correlates with revenue (r=0.87)"
- **Trends**: "Sales show 15% decline over last 3 months"
- **Patterns**: "Weekend sales are 40% higher than weekdays"

### 2. **Business Summary** (AI-Powered)
- High-level overview of your data
- Key findings and recommendations
- Actionable next steps

### 3. **Automated Analysis**
- **Schema Inference**: Detects dates, numbers, categories automatically
- **KPI Calculation**: Sum, mean, max, min for numeric columns
- **Chart Generation**: Time series and category distribution charts
- **Quality Score**: Based on missing values, duplicates, consistency

---

## 📊 Example: What You'll See

If you upload a **sales CSV file**, you might get:

### Insights:
1. 🔍 **"Revenue spike detected on 2024-03-15"**
   - Evidence: Revenue = $50,000 (5x average)
   - Severity: High
   - Action: Investigate unusual transaction

2. 📉 **"Sales declining in Q4"**
   - Evidence: Q4 revenue down 15% vs Q3
   - Severity: Medium
   - Action: Review marketing strategy

3. 🔗 **"Strong correlation between ads and sales"**
   - Evidence: Correlation coefficient = 0.87
   - Severity: Low
   - Action: Increase ad spend for higher ROI

### Charts:
- **Line Chart**: Revenue over time
- **Bar Chart**: Sales by region
- **Bar Chart**: Product category distribution

### Quality Score: **85/100**
- ✅ No duplicates
- ⚠️ 5% missing values
- ✅ Consistent date formats

---

## 🧪 Test Files

You can test with the sample files in `dev-samples/`:

```
dev-samples/
  ├── sales_demo.csv      ← Sales data with dates, revenue, regions
  ├── messy_data.csv      ← Data with missing values, duplicates
  └── sample.pdf          ← PDF with tables (if available)
```

---

## 🔧 API Endpoints (For Testing)

You can also test the API directly:

### Upload a File
```bash
curl -F "file=@dev-samples/sales_demo.csv" http://localhost:5328/api/upload
```

**Response**:
```json
{
  "jobId": "job_abc123",
  "status": "submitted",
  "fileName": "sales_demo.csv"
}
```

### Check Job Status
```bash
curl "http://localhost:5328/api/job-status?jobId=job_abc123"
```

**Response**:
```json
{
  "jobId": "job_abc123",
  "status": "completed",
  "resultUrl": "file:///path/to/result.json",
  "createdAt": "2025-12-06T13:25:00Z",
  "updatedAt": "2025-12-06T13:25:15Z"
}
```

### Health Check
```bash
curl http://localhost:5328/api/health
```

---

## 🎯 What Makes the Insights Powerful?

### 1. **AI-Powered** (DeepSeek R1)
- Uses state-of-the-art LLM for business insights
- Temperature = 0.0 for deterministic, reliable results
- Few-shot learning for relevant examples

### 2. **Evidence-Based**
- Every insight includes evidence (aggregates or specific rows)
- Cites chart IDs for visual validation
- Provides severity levels (High, Medium, Low)

### 3. **Actionable**
- Insights include "who should care" (analyst, executive, etc.)
- Suggests next steps
- Prioritizes by importance

### 4. **Automated**
- No manual configuration needed
- Auto-detects data types
- Generates charts automatically

---

## 🛠️ Troubleshooting

### File Upload Fails
- **Check file size**: Max 20 MB
- **Check format**: CSV, XLSX, JSON, PDF only
- **Check API logs**: Look at the terminal running `route.py`

### Processing Takes Too Long
- **Normal time**: 10-60 seconds for most files
- **Large files**: May take up to 10 minutes (timeout)
- **Check worker logs**: Look at the terminal running `worker.py`

### No Insights Generated
- **Check OpenRouter API key**: Must be set in `.env`
- **Check logs**: Worker will show LLM call status
- **Fallback mode**: If LLM fails, you'll get basic insights

### Worker Not Processing
- **Check Redis**: Run `redis-cli ping` (should return PONG)
- **Restart worker**: Stop and restart `python src/worker.py`

---

## 📝 Notes

### OpenRouter API Key
- **Required** for AI insights
- If not set, you'll get fallback insights (basic analysis)
- Get your key from: https://openrouter.ai/

### Data Privacy
- All processing happens **locally** on your machine
- Only the prompt (not raw data) is sent to OpenRouter
- PII is automatically masked before sending to LLM

### Performance
- **Small files** (< 1 MB): ~10 seconds
- **Medium files** (5 MB): ~30 seconds
- **Large files** (20 MB): ~60 seconds

---

## 🎉 Enjoy DataPilot AI!

Your local server is ready to analyze your data and provide AI-powered insights!

**Next Steps**:
1. Open `http://localhost:3003` in your browser
2. Upload a CSV/XLSX file from your PC
3. Wait for processing
4. Explore the insights, charts, and recommendations!

---

**Services Running**:
- ✅ Frontend: http://localhost:3003
- ✅ API: http://localhost:5328
- ✅ Worker: Background (processing jobs)
- ✅ Redis: localhost:6379

**To Stop Services**:
- Press `Ctrl+C` in each terminal window
- Or close the terminals

---

**Happy Analyzing! 📊🚀**
