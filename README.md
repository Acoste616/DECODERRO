# ULTRA v3.0 - Cognitive Sales Engine

**AI-Powered Sales Assistant with Dual-Path Intelligence & Real-Time Psychometric Analysis**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)

---

## 🎯 Overview

ULTRA v3.0 is an advanced AI-powered sales assistant that combines **real-time conversational AI** with **deep psychological profiling** to help sales professionals engage with clients more effectively. The system uses a dual-path architecture to provide both instant responses and comprehensive behavioral analysis.

### Key Features

- **🚀 Fast Path** - Sub-3-second AI responses using Google Gemini
- **🧠 Slow Path** - Deep 7-module analysis using DeepSeek AI (60-90s)
- **📊 Real-Time Psychometrics** - DISC, Big Five, Schwartz Values
- **🎭 Journey Stage Tracking** - Automatic progression through sales funnel
- **💬 WebSocket Communication** - Live updates and analysis streaming
- **🔍 RAG-Enhanced** - Context-aware responses using knowledge base

---

## 🏗️ Architecture

### Dual-Path System

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT MESSAGE                        │
└────────────┬────────────────────────────────────────────┘
             │
             ├──────────────┬──────────────────────────────┐
             │              │                              │
      ┌──────▼──────┐  ┌───▼──────────┐          ┌────────▼────────┐
      │  FAST PATH  │  │  RAG Search  │          │   SLOW PATH     │
      │  < 3 sec    │  │  (Qdrant)    │          │  60-90 sec      │
      └──────┬──────┘  └───┬──────────┘          └────────┬────────┘
             │              │                              │
      ┌──────▼──────────────▼─────┐               ┌────────▼────────┐
      │   Gemini 1.5 Flash        │               │ DeepSeek v3.1   │
      │   - Direct quote to client│               │ - M1: Client DNA│
      │   - Tactical next steps   │               │ - M2: Indicators│
      │   - Knowledge gaps        │               │ - M3: Psycho    │
      └───────────┬───────────────┘               │ - M4: Motivation│
                  │                               │ - M5: Prediction│
                  │                               │ - M6: Playbook  │
                  │                               │ - M7: Decision  │
                  │                               └────────┬────────┘
                  │                                        │
                  ▼                                        ▼
          ┌───────────────┐                     ┌──────────────────┐
          │   WebSocket   │◄────────────────────┤  WebSocket Queue │
          │   Broadcast   │                     │  (if offline)    │
          └───────┬───────┘                     └──────────────────┘
                  │
                  ▼
          ┌───────────────┐
          │   FRONTEND    │
          │   Dashboard   │
          └───────────────┘
```

### 7-Module Analysis (Slow Path)

1. **M1: Client DNA** - Communication style, core motivations
2. **M2: Tactical Indicators** - Purchase temperature, churn risk
3. **M3: Psychometrics** - DISC, Big Five, Schwartz Values
4. **M4: Deep Motivation** - Key insights, emotional hooks
5. **M5: Predictive Paths** - Future scenarios, timeline estimates
6. **M6: Sales Playbook** - Recommended tactics, scripts
7. **M7: Decision Dynamics** - Decision-maker profile, influencers

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Qdrant (local or cloud)
- API Keys:
  - Google Gemini API
  - Ollama Cloud API

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/ultra-v3.0.git
   cd ultra-v3.0
   ```

2. **Backend setup:**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt

   # Configure environment
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Frontend setup:**
   ```bash
   # Install Node dependencies
   npm install
   ```

4. **Start Qdrant (optional, if running locally):**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

5. **Run the application:**
   ```bash
   # Terminal 1: Backend
   uvicorn backend.main:app --reload

   # Terminal 2: Frontend
   npm run dev
   ```

6. **Access the app:**
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# Gemini API (Fast Path)
GEMINI_API_KEY=your_gemini_api_key_here

# Ollama Cloud (Slow Path)
OLLAMA_API_KEY=your_ollama_api_key_here
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL=deepseek-v3.1:671b-cloud

# Vector Database
QDRANT_URL=http://localhost:6333

# Database
DATABASE_URL=sqlite:///ultra.db
```

### Critical Configuration Notes

⚠️ **Model Names:**
- Fast Path: Use `gemini-1.5-flash` or `gemini-2.0-flash-thinking-exp-01-21`
- Slow Path: Must include `-cloud` suffix for Ollama Cloud

⚠️ **API Quotas:**
- Gemini: ~60 requests/minute (free tier)
- Ollama DeepSeek: Check your cloud credits

---

## 📖 How It Works

### User Flow

1. **User sends message** → Frontend via WebSocket
2. **Fast Path activates** → Immediate AI response (< 3s)
   - Searches RAG knowledge base
   - Generates contextual response via Gemini
   - Provides tactical next steps + knowledge gaps
3. **Slow Path triggers** → Background analysis (60-90s)
   - Deep psychological profiling
   - 7-module comprehensive analysis
   - Auto-updates journey stage if confidence ≥ 75%
4. **Dashboard updates** → Real-time WebSocket broadcast
   - Psychometric charts update
   - New tactical indicators appear
   - Sales playbook recommendations

### Journey Stages

```
DISCOVERY → CONSIDERATION → INTENT → NEGOTIATION → CLOSING → DELIVERY
```

System automatically progresses stages based on conversation analysis and confidence scores.

---

## 🛠️ Development

### Project Structure

```
ultra-v3.0/
├── backend/
│   ├── main.py              # FastAPI app, WebSocket endpoint
│   ├── ai_core.py           # Gemini Fast Path logic
│   ├── analysis_engine.py   # DeepSeek Slow Path logic
│   ├── rag_engine.py        # RAG retrieval (Qdrant)
│   ├── database.py          # SQLAlchemy setup
│   └── models.py            # Database models
├── src/
│   ├── components/          # React components
│   ├── pages/               # Page components
│   └── types/               # TypeScript definitions
├── .env                     # Environment configuration
├── requirements.txt         # Python dependencies
└── package.json             # Node dependencies
```

### Running Tests

```bash
# Test Gemini API
python test_gemini.py

# Test full conversation flow
python simulate_full_conversation.py
```

### Debugging

**Check backend logs:**
```bash
# Look for these success indicators:
✅ [AI CORE] Gemini model initialized: gemini-1.5-flash
✅ [FAST PATH] Gemini response parsed successfully
✅ [SLOW PATH] Analysis saved to DB and broadcasted
```

**Common issues:**
- `RAG_FALLBACK` in UI → Restart uvicorn (Python cache issue)
- Slow Path never completes → Check Ollama model suffix
- WebSocket disconnects → Verify frontend URL matches backend

---

## 🔧 Troubleshooting

### Issue: System shows `RAG_FALLBACK` instead of AI responses

**Cause:** Python bytecode cache not updating after code changes

**Fix:**
```bash
# Stop uvicorn (Ctrl+C)
rm -rf backend/__pycache__
uvicorn backend.main:app --reload
```

### Issue: Slow Path returns all 50/50 psychometric scores

**Cause:** Ollama model name missing `-cloud` suffix

**Fix:** Update `.env`:
```env
OLLAMA_MODEL=deepseek-v3.1:671b-cloud  # Add -cloud suffix
```

### Issue: Background tasks die before completion

**Cause:** Garbage collector reclaiming unreferenced async tasks

**Fix:** Ensure `main.py` stores task references:
```python
manager.active_tasks[session_id] = task
```

---

## 📊 Performance

- **Fast Path Latency:** 1.5-3 seconds
- **Slow Path Duration:** 60-90 seconds (depends on Ollama quota)
- **WebSocket Throughput:** 100+ concurrent connections
- **Database:** SQLite (suitable for < 10K sessions, upgrade to PostgreSQL for production)

---

## 🚨 Critical Fixes Applied

This repository includes fixes for 6 critical failures identified in forensic audit:

1. ✅ **Gemini Model:** Changed to stable `gemini-1.5-flash`
2. ✅ **Ollama Model:** Added `-cloud` suffix
3. ✅ **GC Protection:** Task references stored in `ConnectionManager`
4. ✅ **WebSocket Queueing:** Messages persisted during disconnects
5. ✅ **Error Logging:** Silent failures replaced with tracebacks
6. ✅ **Fallback Logic:** Exceptions re-raised for proper handling

See [`CRITICAL_FIXES_SUMMARY.md`](CRITICAL_FIXES_SUMMARY.md) for full details.

---

## 📝 Documentation

- [Forensic Audit Report](forensic_audit_report.md) - Technical deep-dive
- [Critical Fixes Summary](CRITICAL_FIXES_SUMMARY.md) - Quick reference
- [Deployment Walkthrough](walkthrough.md) - Step-by-step guide
- [Restart Guide](RESTART_REQUIRED.md) - Cache troubleshooting

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary. All rights reserved.

---

## 🙏 Acknowledgments

- **Gemini API** by Google AI
- **Ollama Cloud** for DeepSeek hosting
- **Qdrant** for vector search
- **FastAPI** framework
- **React** + **Vite** for frontend

---

## 📧 Support

For issues, questions, or feature requests, please open a GitHub issue.

---

**Built with ❤️ for sales professionals who leverage AI**
