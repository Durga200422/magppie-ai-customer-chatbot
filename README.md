# Magppie AI Concierge Chatbot

<div align="center">
  <img src="assets/logo.png" alt="Magppie Logo" width="120">
  <br><br>
  <strong>Maya — Your Magppie Virtual Assistant</strong>
  <br>
  <em>A production-grade RAG chatbot with multi-provider LLM fallback, conversational memory, and lead capture</em>
  <br><br>

  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
  ![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit&logoColor=white)
  ![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-1C3C3C?logo=langchain&logoColor=white)
  ![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-Primary_LLM-4285F4?logo=google&logoColor=white)
  ![Groq](https://img.shields.io/badge/Groq_Llama_3.3-Fallback_LLM-F55036?logoColor=white)

</div>

---

## Overview

**Maya** is a production-ready RAG-based (Retrieval-Augmented Generation) AI customer support chatbot built for [Magppie](https://www.magppie.com). It answers questions about products, store locations, offers, pricing, and more — all grounded in Magppie's own knowledge base, with no hallucinations.

The system retrieves relevant context from Magppie's PDF catalogue and website, then generates warm, concise responses using Gemini 2.5 Flash as the primary LLM, with Groq's Llama 3.3 70B as a fully transparent fallback.

---

## Features

| Feature | Description |
|---|---|
| 🧠 **RAG Pipeline** | Answers grounded in Magppie PDF + live website content via ChromaDB |
| 🔄 **Multi-Provider Fallback** | Gemini 2.5 Flash → Groq Llama 3.3 70B → graceful error message |
| 💬 **Conversational Memory** | Retains last 5 turns; rewrites follow-up queries for better retrieval |
| 🎯 **Intent Routing** | Automatically detects escalation requests, lead intent, and normal queries |
| 📋 **Lead Capture** | Validates and persists leads to `leads/leads.json` with UUID + timestamp |
| 🏗️ **Auto-Build KB** | Automatically builds ChromaDB knowledge base if not found (cloud-safe) |
| 🎨 **Premium UI** | Three-panel Streamlit interface with DM Sans font, gold accents, custom chat bubbles |

---

## Screenshots

> *Add screenshots of the deployed app here before publishing.*

| Chat Interface | Lead Capture | Escalation Flow |
|---|---|---|
| *(screenshot)* | *(screenshot)* | *(screenshot)* |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     ui/app.py  (Streamlit UI)                        │
│  Left Panel: Brand + Quick Suggestions                               │
│  Center Panel: Chat history + input                                  │
│  Right Panel: Lead capture form + contact card                       │
└──────────────────────┬───────────────────────────────────────────────┘
                       │ user query
               chatbot/logic.py
          ┌────────────┴────────────┐
    Escalation             Lead Intent / Normal Query
   (direct reply)               │
                         rag/pipeline.py
                    (query rewrite → retrieval → LLM)
                       ┌──────────┴──────────┐
               Gemini 2.5 Flash       Groq Llama 3.3 70B
               (Primary LLM)          (Silent Fallback)
                                │
                       rag/vector_store.py
                       (ChromaDB — auto-built on first run)
                    ┌──────────┴──────────┐
           ingestion/pdf_loader    ingestion/web_scraper
           (data/magppie.pdf)      (https://magppie.com)
```

### Fallback Chain

```
User Query
    │
    ▼
Gemini 2.5 Flash ──✗ (quota/rate/server error)──▶ Groq Llama 3.3 70B
                                                        │
                                                        ▼ (if also fails)
                                          "I'm having trouble right now..."
                                              (graceful error message)
```

The fallback is **completely transparent to the user** — no error banners, no UI changes, just a seamless handoff between providers.

---

## Project Structure

```
magppie-chatbot-antigravity/
├── assets/
│   └── logo.png                    # Magppie brand logo (embedded as base64)
├── chatbot/
│   ├── lead_capture.py             # Lead validation + JSON persistence (CRM simulation)
│   └── logic.py                    # Intent router: escalation / lead nudge / normal RAG
├── data/
│   └── magppie.pdf                 # Primary source knowledge document (catalogue)
├── ingestion/
│   ├── chunker.py                  # RecursiveCharacterTextSplitter → LangChain Documents
│   ├── pdf_loader.py               # PyMuPDF text extraction + Tesseract OCR fallback
│   └── web_scraper.py              # BFS web crawler (requests + Playwright JS fallback)
├── rag/
│   ├── embedder.py                 # Google gemini-embedding-001 via langchain-google-genai
│   ├── pipeline.py                 # Core RAG: query rewrite → MMR retrieval → LLM → memory
│   └── vector_store.py             # ChromaDB build / load / auto-build orchestration
├── ui/
│   └── app.py                      # Main Streamlit application (three-panel layout)
├── .streamlit/
│   └── config.toml                 # Streamlit theme (gold accents, off-white background)
├── build_knowledge_base.py         # One-time knowledge base builder (PDF + web → ChromaDB)
├── .env.example                    # Environment variable template
├── requirements.txt                # Python dependencies
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.10+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed (for OCR on PDF images)
  - Windows: install to `C:\Program Files\Tesseract-OCR\` (default)
  - Linux/Mac: `sudo apt install tesseract-ocr` / `brew install tesseract`

### 1. Clone the repository
```bash
git clone https://github.com/your-username/magppie-chatbot-antigravity.git
cd magppie-chatbot-antigravity
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

> **Optional:** Install Playwright for JavaScript-rendered page fallback during web scraping:
> ```bash
> pip install playwright
> playwright install chromium
> ```

### 4. Configure environment variables
```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and fill in your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional — only needed if you want LangSmith tracing
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=Magppie Chatbot Antigravity
```

### 5. Build the knowledge base (first-time only)
This step scrapes Magppie's website and processes the PDF to build the ChromaDB vector store.
```bash
python build_knowledge_base.py
```
> ⚠️ This can take **10–30 minutes** on first run due to embedding rate limits on Gemini's free tier. The script includes automatic exponential backoff.

### 6. Run the app
```bash
streamlit run ui/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Deployment on Streamlit Community Cloud

### 1. Push to GitHub
Ensure `chroma_db/` is committed (it is by default — the `.gitignore` intentionally does **not** exclude it so Streamlit Cloud can serve the chatbot without rebuilding on every cold start).

```bash
git add .
git commit -m "feat: production-ready deployment"
git push origin main
```

### 2. Create app on Streamlit Cloud
- Go to [share.streamlit.io](https://share.streamlit.io)
- Click **New app** → connect your GitHub repository
- Set **Main file path** to: `ui/app.py`
- Click **Deploy**

### 3. Configure Secrets
In the Streamlit Cloud dashboard → **App settings → Secrets**, paste:
```toml
GEMINI_API_KEY = "your_gemini_api_key"
GROQ_API_KEY   = "your_groq_api_key"

# Optional
LANGCHAIN_API_KEY      = "your_langchain_api_key"
LANGCHAIN_TRACING_V2   = "true"
LANGCHAIN_PROJECT      = "Magppie Chatbot Antigravity"
```

> **Note:** Secrets are injected into `os.environ` at startup via `_inject_secrets()` in `app.py`, making them available to all modules without any additional configuration.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key — powers primary LLM + embeddings |
| `GROQ_API_KEY` | ✅ Yes | Groq API key — powers the silent fallback LLM |
| `LANGCHAIN_API_KEY` | Optional | LangSmith tracing API key |
| `LANGCHAIN_TRACING_V2` | Optional | Enable LangSmith tracing (`true` / `false`) |
| `LANGCHAIN_PROJECT` | Optional | LangSmith project name for grouping traces |

---

## Troubleshooting

### App fails to start — "GOOGLE_API_KEY not set"
The app maps `GEMINI_API_KEY` → `GOOGLE_API_KEY` automatically. Ensure `GEMINI_API_KEY` is set in your `.env` file or Streamlit secrets. Do **not** use `GOOGLE_API_KEY` directly.

### App hangs on startup / "building knowledge base"
If `chroma_db/` is missing, the app auto-builds the knowledge base on first run. This is expected and can take several minutes. On Streamlit Cloud, ensure `chroma_db/` is committed to the repo to avoid this delay.

### Gemini quota errors (429 / RESOURCE_EXHAUSTED)
The fallback to Groq handles this silently. If you see this during `build_knowledge_base.py`, the script will retry with exponential backoff automatically (up to 6 attempts per batch).

### Tesseract not found / OCR warnings
Tesseract is used for OCR on embedded images in the PDF. If not installed, the PDF text extraction still works — only image-embedded text is missed. Install Tesseract and ensure it's on your `PATH` for full extraction.

### Playwright import warning
```
Warning: Playwright not installed. JS rendering fallback will not be available.
```
This is non-critical. The web scraper falls back to `requests` + BeautifulSoup. Install Playwright with `pip install playwright && playwright install chromium` for full JS page rendering.

### Lead form not saving
Ensure the app has write permission to the `leads/` directory. On Streamlit Cloud, file writes persist only within the same session (ephemeral filesystem). For production CRM integration, replace `save_lead()` in `chatbot/lead_capture.py` with a real database call.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
