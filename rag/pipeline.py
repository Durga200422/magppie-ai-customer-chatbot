import os
import sys
import time
from dotenv import load_dotenv

# Ensure stdout handles utf-8 characters properly on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Ensure GEMINI_API_KEY is mapped to GOOGLE_API_KEY (required by langchain-google-genai)
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# Import our custom modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.embedder import get_embedding_model
from rag.vector_store import load_or_build_vector_store

print("Initializing RAG Pipeline with Gemini + Groq Fallback...")

# ---------------------------------------------------------------------------
# LLM CONFIGURATION
# ---------------------------------------------------------------------------

# Primary: Gemini 2.5 Flash
_gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2
)

# Fallback: Groq llama-3.3-70b-versatile
_groq_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    api_key=os.environ.get("GROQ_API_KEY", "")
)

# Errors that indicate Gemini is unavailable (quota, rate limit, server issues, auth)
_GEMINI_FALLBACK_ERRORS = (
    "RESOURCE_EXHAUSTED",
    "QUOTA_EXCEEDED",
    "RATE_LIMIT",
    "UNAVAILABLE",
    "DEADLINE_EXCEEDED",
    "INTERNAL",
    "401",
    "403",
    "429",
    "503",
    "504",
)

def _is_fallback_error(exc: Exception) -> bool:
    """Return True if the exception should trigger a Groq fallback."""
    err_str = str(exc).upper()
    return any(marker in err_str for marker in _GEMINI_FALLBACK_ERRORS)


def _invoke_with_fallback(messages: list) -> str:
    """
    Try Gemini first. On quota/rate/availability errors, silently fall back to Groq.
    If both fail, return a graceful error message.
    """
    # --- Attempt Gemini ---
    try:
        response = _gemini_llm.invoke(messages)
        return response.content.strip()
    except Exception as gemini_err:
        if _is_fallback_error(gemini_err):
            print(f"[INFO] Gemini unavailable → switching to Groq fallback...")
        else:
            # Unexpected Gemini error — still try Groq before giving up
            print(f"[WARN] Gemini error (unexpected): {gemini_err} → switching to Groq fallback...")

    # --- Attempt Groq ---
    try:
        response = _groq_llm.invoke(messages)
        return response.content.strip()
    except Exception as groq_err:
        print(f"[ERROR] Groq fallback also failed: {groq_err}")
        return (
            "I'm having trouble accessing information right now. "
            "Please try again in a moment or contact our support team."
        )

# ---------------------------------------------------------------------------
# VECTOR STORE & RETRIEVER
# ---------------------------------------------------------------------------

embeddings = get_embedding_model()
try:
    vector_store = load_or_build_vector_store(embeddings)
except Exception as e:
    print(f"[FATAL] Could not load or build vector store: {e}")
    raise

retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 15}
)

# ---------------------------------------------------------------------------
# CONVERSATION MEMORY
# ---------------------------------------------------------------------------

chat_history = []
MAX_TURNS = 5

# ---------------------------------------------------------------------------
# SYSTEM PROMPT (shared by both providers)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are Maya, Magppie's friendly customer assistant.\n"
    "Answer ONLY using the provided context. Do not make up information.\n"
    "If the answer is not in the context, say: \"I don't have that specific information right now. "
    "Would you like me to connect you with our support team?\"\n"
    "Be concise — 2 to 4 sentences. Use bullet points for lists.\n"
    "Always be warm, professional, and helpful.\n"
)

# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def query(question: str) -> str:
    """
    Retrieves context, maintains conversational memory, and returns an answer.
    Gemini is tried first; Groq is used as a silent fallback.
    """
    global chat_history

    # 1. Rewrite the query using recent history for better retrieval
    standalone_query = question
    if chat_history:
        rewrite_prompt = (
            "Given the following chat history and a follow-up question, rephrase the follow-up "
            "question to be a standalone query that includes relevant keywords from the history.\n"
            "Return ONLY the standalone question text, nothing else.\n\n"
            "History:\n"
        )
        for h_q, h_a in chat_history[-2:]:
            rewrite_prompt += f"User: {h_q}\nMaya: {h_a}\n"
        rewrite_prompt += f"\nFollow-up question: {question}\nStandalone question:"

        try:
            standalone_query = _invoke_with_fallback(
                [HumanMessage(content=rewrite_prompt)]
            )
        except Exception:
            standalone_query = question

    # 2. Retrieve top documents via MMR
    docs = retriever.invoke(standalone_query)
    context_text = "\n\n".join([doc.page_content for doc in docs])

    # 3. Format conversation history for the prompt
    history_text = ""
    if chat_history:
        history_text = "Conversation History (Last 5 turns):\n"
        for q, a in chat_history:
            history_text += f"User: {q}\nMaya: {a}\n\n"

    # 4. Build the full prompt
    full_prompt = (
        f"{history_text}"
        f"Retrieved Context:\n{context_text}\n\n"
        f"Current User Question: {question}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=full_prompt)
    ]

    # 5. Generate answer (with automatic fallback)
    answer = _invoke_with_fallback(messages)

    # 6. Update memory
    chat_history.append((question, answer))
    if len(chat_history) > MAX_TURNS:
        chat_history.pop(0)

    return answer


# ---------------------------------------------------------------------------
# QUICK FALLBACK SIMULATION TEST (run as __main__ only)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import unittest.mock as mock
    import rag.pipeline as _pipeline_module  # reference the module itself for patching

    print("\n" + "=" * 55)
    print("TEST 1 — Normal Gemini query")
    print("=" * 55)
    result = query("What products does Magppie sell?")
    print(f"Maya: {result}")

    print("\n" + "=" * 55)
    print("TEST 2 — Simulating Gemini QUOTA failure → Groq fallback")
    print("=" * 55)

    # Patch the module-level _gemini_llm reference so the fallback helper sees the error
    quota_error = Exception("RESOURCE_EXHAUSTED: 429 quota exceeded for gemini-2.5-flash")

    original_gemini = _pipeline_module._gemini_llm

    class _FakeBrokenLLM:
        def invoke(self, *args, **kwargs):
            raise quota_error

    _pipeline_module._gemini_llm = _FakeBrokenLLM()
    # Reset history so this is treated as a fresh query (no rewrite call)
    _pipeline_module.chat_history = []
    result_fallback = query("Where are your store locations?")
    _pipeline_module._gemini_llm = original_gemini  # restore
    print(f"Maya (via Groq): {result_fallback}")

    print("\n" + "=" * 55)
    print("TEST 3 — Simulating BOTH providers failing → graceful message")
    print("=" * 55)

    class _FakeBothBrokenLLM:
        def invoke(self, *args, **kwargs):
            raise Exception("CONNECTION_ERROR: Service unreachable")

    _pipeline_module._gemini_llm = _FakeBothBrokenLLM()
    _pipeline_module._groq_llm   = _FakeBothBrokenLLM()
    _pipeline_module.chat_history = []
    result_both_fail = query("Tell me about your offers")
    _pipeline_module._gemini_llm = original_gemini  # restore
    print(f"Maya: {result_both_fail}")

