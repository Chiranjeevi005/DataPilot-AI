# 🚀 DataPilot AI

> **Transform raw data into actionable insights in seconds** — An intelligent data analysis platform powered by AI that automates exploratory data analysis, generates business insights, and creates interactive visualizations.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://www.typescriptlang.org/)

---

## ✨ Key Features

### 🎯 **Intelligent Data Analysis**
- **Multi-Format Support**: Upload CSV, Excel (XLSX), JSON, and PDF files
- **Automated EDA**: Instant exploratory data analysis with schema inference, quality scoring, and statistical profiling
- **Smart Chart Generation**: Automatically creates relevant visualizations (time-series, distributions, correlations)
- **AI-Powered Insights**: LLM-generated business insights with evidence-backed recommendations

### 🎨 **Beautiful, Responsive UI**
- **Mobile-First Design**: Fully optimized for phones, tablets, and desktops
- **Real-Time Progress**: Live job status tracking with animated loading states
- **Interactive Dashboard**: Dynamic KPI cards, charts, and data previews
- **Dark Mode Ready**: Modern glassmorphism design with smooth animations

### ⚡ **Production-Ready Architecture**
- **Asynchronous Processing**: Redis-based job queue for scalable background processing
- **Robust Error Handling**: Retry logic, circuit breakers, and graceful degradation
- **Job Management**: Real-time status tracking, cancellation, and timeout enforcement
- **Cloud-Native**: Docker support with deployment configurations for major cloud providers

### 🤖 **Advanced AI Pipeline**
- **Few-Shot Learning**: Context-aware prompt engineering for better insights
- **PII Protection**: Automatic masking of sensitive data (emails, phones, SSNs, credit cards)
- **Validation-First**: Schema validation with automatic fallback to deterministic templates
- **Audit Logging**: Complete observability without exposing sensitive information

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  File Upload │  │   Dashboard  │  │   Results    │          │
│  │   Component  │→ │   (Loading)  │→ │   Viewer     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                      Backend APIs (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   /upload    │  │ /job-status  │  │   /cancel    │          │
│  └──────┬───────┘  └──────────────┘  └──────────────┘          │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │            Redis Job Queue (RQ)                   │          │
│  └──────────────────┬───────────────────────────────┘          │
└────────────────────┬┴──────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                    Worker Process (Python)                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ File Parser  │→ │  EDA Engine  │→ │ Chart Builder│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ LLM Client   │→ │  Validator   │→ │ Result Store │          │
│  │ (Few-Shot)   │  │  (Schema)    │  │  (Blob/Local)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### **Data Flow**

1. **Upload** → User uploads file via drag-and-drop or file picker
2. **Queue** → Backend validates file and enqueues job in Redis
3. **Process** → Worker dequeues job and performs:
   - File parsing with encoding fallback
   - Schema inference and data profiling
   - Quality scoring and KPI calculation
   - Chart specification generation
   - LLM-powered insight generation
4. **Store** → Results saved to blob storage or local filesystem
5. **Display** → Frontend polls for status and renders interactive results

---

## 🛠️ Tech Stack

### **Frontend**
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.0
- **Styling**: TailwindCSS 3.4 with custom design system
- **UI Components**: shadcn/ui (Radix UI primitives)
- **State Management**: Zustand
- **Charts**: Recharts (responsive, accessible)
- **Icons**: Lucide React

### **Backend**
- **Language**: Python 3.11+
- **API Framework**: FastAPI (async/await)
- **Job Queue**: Redis + RQ (Redis Queue)
- **Data Processing**: Pandas, NumPy
- **PDF Extraction**: pdfplumber
- **LLM Integration**: OpenAI SDK (OpenRouter compatible)

### **Infrastructure**
- **Containerization**: Docker + Docker Compose
- **Storage**: Blob storage (cloud) or local filesystem
- **Deployment**: Antigravity (Google Cloud), Vercel-compatible
- **CI/CD**: GitHub Actions workflow included

---

## 🚀 Quick Start

### **Prerequisites**

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Redis** (local or Docker)

### **Installation**

```bash
# Clone the repository
git clone https://github.com/yourusername/datapilot-ai.git
cd datapilot-ai

# Install frontend dependencies
npm install

# Install backend dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### **Running Locally**

#### **Option 1: Quick Start (Batch Script - Windows)**

```bash
# Start all services (Redis, Backend, Frontend, Worker)
./scripts/start-app.bat
```

#### **Option 2: Docker Compose**

```bash
cd deployment
docker-compose up -d
```

#### **Option 3: Manual Setup**

```bash
# Terminal 1: Start Redis
docker run --name redis-server -p 6379:6379 -d redis

# Terminal 2: Start Backend API
cd src
python -m uvicorn api.upload.route:app --host 0.0.0.0 --port 5328

# Terminal 3: Start Worker
python worker.py

# Terminal 4: Start Frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the application.

---

## 📖 Usage

### **1. Upload Your Data**

- Drag and drop a file (CSV, XLSX, JSON, or PDF)
- Or click to browse and select a file
- Supported formats: `.csv`, `.xlsx`, `.json`, `.pdf`
- Max file size: 10MB

### **2. Wait for Processing**

- Real-time progress updates
- Typical processing time: 5-30 seconds
- Cancel anytime if needed

### **3. Explore Results**

- **KPI Cards**: Key metrics (row count, quality score, missing data, duplicates)
- **Data Preview**: First 20 rows with clean formatting
- **Interactive Charts**: Time-series, distributions, and correlations
- **AI Insights**: Business recommendations with evidence citations
- **Download Report**: Export results as PDF

---

## 🎯 Use Cases

### **Business Analytics**
- Sales performance analysis
- Customer behavior insights
- Revenue trend forecasting
- Marketing campaign effectiveness

### **Data Quality Assessment**
- Missing value detection
- Duplicate identification
- Outlier analysis
- Schema validation

### **Quick EDA for Data Scientists**
- Instant statistical profiling
- Correlation discovery
- Distribution visualization
- Feature engineering hints

### **Executive Reporting**
- Automated insight generation
- Visual dashboard creation
- PDF report export
- Non-technical stakeholder communication

---

## 🔒 Security & Privacy

- **PII Masking**: Automatic detection and masking of emails, phone numbers, SSNs, and credit cards
- **No Data Retention**: Uploaded files are automatically cleaned up after processing
- **Configurable TTL**: Set custom retention periods for temporary data
- **Audit Logging**: Complete observability without exposing sensitive information
- **API Key Security**: Environment-based configuration, never committed to version control

---

## 📊 Performance

- **Upload Speed**: < 1 second for files up to 10MB
- **Processing Time**: 
  - CSV (1000 rows): ~3-5 seconds
  - Excel (5000 rows): ~8-12 seconds
  - JSON (nested): ~5-10 seconds
  - PDF (10 pages): ~15-20 seconds
- **LLM Insights**: ~2-5 seconds (with caching and circuit breaker)
- **Concurrent Jobs**: Scales horizontally with worker instances

---

## 🧪 Testing

```bash
# Run frontend tests
npm test

# Run backend tests
pytest

# End-to-end smoke tests
./scripts/run_smoke_tests.sh

# Test specific features
./scripts/test_upload.sh
./scripts/test_worker_flow.sh
```

---

## 📦 Deployment

### **Docker Deployment**

```bash
cd deployment
docker-compose up -d --build
```

### **Cloud Deployment (Antigravity)**

```bash
# Configure deployment
vim deployment/antigravity.yml

# Deploy
./scripts/deploy_antigravity.sh

# Verify
./scripts/verify_deploy.sh
```

See [deployment/README.md](deployment/README.md) for detailed deployment instructions.

---

## 🗂️ Project Structure

```
datapilot-ai/
├── src/                      # Source code
│   ├── app/                  # Next.js app router pages
│   ├── components/           # React components
│   ├── api/                  # Backend API routes
│   ├── lib/                  # Core libraries (analysis, LLM, storage)
│   ├── jobs/                 # Worker job processors
│   ├── maintenance/          # Cleanup and retention scripts
│   └── worker.py             # Background worker process
├── deployment/               # Docker and cloud configs
├── scripts/                  # Utility and deployment scripts
├── docs/                     # Documentation
├── prompts/                  # LLM prompt templates
├── dev-samples/              # Sample data files for testing
├── public/                   # Static assets
└── README.md                 # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LLM Provider**: OpenRouter (DeepSeek R1)
- **UI Components**: shadcn/ui
- **Charts**: Recharts
- **Icons**: Lucide React
- **Deployment**: Antigravity (Google Cloud)

---

## 📞 Support

For questions, issues, or feature requests:

- **Issues**: [GitHub Issues](https://github.com/yourusername/datapilot-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/datapilot-ai/discussions)

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

---

**Built with ❤️ by the DataPilot AI Team**
