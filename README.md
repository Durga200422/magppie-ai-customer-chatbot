# Magppie AI Concierge Chatbot

<div align="center">
  <img src="assets/logo.png" alt="Magppie Logo" width="120">
  <br>
  <strong>Maya — Your Magppie Virtual Assistant</strong>
  <br>
  <em>A production-grade RAG-powered AI chatbot with multi-provider fallback</em>
</div>

---

## Overview

**Maya** is a RAG-based (Retrieval-Augmented Generation) AI customer support chatbot built for Magppie. It answers questions about products, store locations, pricing, and more — all grounded in Magppie's own knowledge base, with no hallucinations.

---

## Features

| Feature | Description |
|---|---|
| 🧠 **RAG Pipeline** | Answers sourced from Magppie PDF + website content via ChromaDB |
| 🔄 **Multi-Provider Fallback** | Gemini 2.5 Flash primary → Groq llama-3.3-70b fallback |
| 💬 **Multi-Turn Memory** | Retains last 5 turns of conversation context |
| 🎯 **Intent Routing** | Detects escalation, lead intent, and normal queries |
| 📋 **Lead Capture** | Validates and saves leads to `leads/leads.json` |
| 🏗️ **Auto-Build KB** | Automatically builds vector DB if not present (cloud-safe) |
| 🎨 **Premium UI** | Three-panel Streamlit UI with DM Sans font and gold accents |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        ui/app.py (Streamlit)                     │
│  Left: Brand + Quick Suggestions │ Center: Chat │ Right: Leads  │
└──────────────────┬───────────────────────────────────────────────┘
                   │
           chatbot/logic.py
        (Intent Router: escalation / lead / normal)
                   │
           rag/pipeline.py
        (Query rewrite → MMR retrieval → LLM)
          ┌────────┴────────┐
   Gemini 2.5 Flash    Groq llama-3.3-70b
   (Primary LLM)       (Fallback LLM)
                   │
           rag/vector_store.py
        (ChromaDB — auto-built on first run)
          ┌────────┴────────┐
   ingestion/pdf_loader  ingestion/web_scraper
   (data/magppie.pdf)    (https://magppie.com)
```

---

## Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/magppie-chatbot-antigravity.git
cd magppie-chatbot-antigravity
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure environment variables
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
LANGCHAIN_API_KEY=your_langchain_api_key_here   # optional, for tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=Magppie Chatbot Antigravity
```

### 4. Build the knowledge base (first-time only)
```bash
python build_knowledge_base.py
```

### 5. Run the app
```bash
streamlit run ui/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Deployment on Streamlit Community Cloud

### 1. Push to GitHub
```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

### 2. Create app on Streamlit Cloud
- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect your GitHub repository
- Set **Main file path** to: `ui/app.py`

### 3. Configure Secrets
In the Streamlit Cloud dashboard → **Settings → Secrets**, paste:
```toml
GEMINI_API_KEY = "your_gemini_api_key"
GROQ_API_KEY = "your_groq_api_key"
LANGCHAIN_API_KEY = "your_langchain_api_key"
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "Magppie Chatbot Antigravity"
```

> **Note:** On first deployment, the app will automatically build the knowledge base from the PDF and website. This may take a few minutes. Subsequent loads use the cached ChromaDB.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key (primary LLM) |
| `GROQ_API_KEY` | ✅ Yes | Groq API key (fallback LLM) |
| `LANGCHAIN_API_KEY` | Optional | LangSmith tracing |
| `LANGCHAIN_TRACING_V2` | Optional | Enable LangSmith (`true`/`false`) |
| `LANGCHAIN_PROJECT` | Optional | LangSmith project name |

---

## Project Structure

```
magppie-chatbot-antigravity/
├── assets/
│   └── logo.png                  # Magppie brand logo
├── chatbot/
│   ├── lead_capture.py           # Lead validation + JSON storage
│   └── logic.py                  # Intent routing (escalation/lead/normal)
├── data/
│   └── magppie.pdf               # Source knowledge document
├── ingestion/
│   ├── chunker.py                # Text chunking (RecursiveCharacterTextSplitter)
│   ├── pdf_loader.py             # PDF + OCR extraction (PyMuPDF + Tesseract)
│   └── web_scraper.py            # Web crawling (requests + Playwright fallback)
├── rag/
│   ├── embedder.py               # Local embeddings (all-MiniLM-L6-v2)
│   ├── pipeline.py               # Core RAG + fallback LLM logic
│   └── vector_store.py           # ChromaDB build + load + auto-build
├── ui/
│   └── app.py                    # Streamlit interface
├── .streamlit/
│   └── config.toml               # Streamlit server + theme config
├── build_knowledge_base.py       # One-time KB build orchestrator
├── requirements.txt
└── README.md
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
