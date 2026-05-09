import streamlit as st
import sys
import os
import re
import base64
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

# ── Cloud deployment: inject Streamlit secrets into env vars ──────────────────
# On Streamlit Community Cloud, secrets live in st.secrets.
# Locally, a .streamlit/secrets.toml or .env file is used.
# We guard with hasattr + try/except so no error banner ever appears.
def _inject_secrets():
    try:
        # Only iterate if secrets are actually available
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            for key, value in st.secrets.items():
                if key not in os.environ:
                    os.environ[key] = str(value)
    except Exception:
        pass  # No secrets — local .env will be used instead

_inject_secrets()

# Ensure GEMINI_API_KEY maps to GOOGLE_API_KEY before importing pipeline
if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

# Ensure imports work from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.pipeline import query as rag_query
from chatbot.logic import handle_query
from chatbot.lead_capture import save_lead

# Page Config
st.set_page_config(
    page_title="Magppie Assistant",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Helper function to convert image to base64 for embedding in HTML
def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_b64 = get_base64_image("assets/logo.png")
logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""

# Custom CSS for UI styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
    
    * {
        font-family: 'DM Sans', sans-serif !important;
    }
    
    /* Left Panel Branding */
    .brand-container {
        background-color: #1A1714;
        padding: 25px 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .brand-logo {
        width: 110px;
        margin-bottom: 10px;
    }
    .brand-title {
        color: white;
        font-size: 20px;
        font-weight: 700;
        margin: 0;
        letter-spacing: 1px;
    }
    .brand-subtitle {
        color: #D4A354;
        font-size: 13px;
        font-weight: 500;
        margin-top: 2px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Status & Controls */
    .status-container {
        margin: 15px 0;
        font-size: 14px;
        color: #333;
        display: flex;
        align-items: center;
    }
    .online-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #4CAF50;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 5px #4CAF50;
    }
    
    .quick-title {
        font-size: 14px;
        color: #666;
        margin-bottom: 10px;
        font-weight: 600;
    }
    
    /* Chat Bubbles Layout */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 10px 0 20px 0;
    }
    .chat-row {
        display: flex;
        align-items: flex-end;
        margin-bottom: 5px;
    }
    .chat-row.user {
        flex-direction: row-reverse;
    }
    .chat-row.bot {
        flex-direction: row;
    }
    
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        margin: 0 10px;
        flex-shrink: 0;
    }
    .avatar.user { background-color: #f0f0f0; color: #333; }
    .avatar.bot { background-color: #1A1714; color: #D4A354; border: 1px solid #333; }
    
    .bubble {
        padding: 12px 18px;
        font-size: 15px;
        line-height: 1.5;
        max-width: 75%;
        word-wrap: break-word;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    .user-bubble {
        background-color: #1A1714;
        color: white;
        border-radius: 18px 18px 4px 18px;
    }
    .bot-bubble {
        background-color: #ffffff;
        color: #333333;
        border-radius: 18px 18px 18px 4px;
        border: 1px solid #f2f2f2;
    }
    .escalation-bubble {
        background-color: #FFFDF5; /* Very soft gold background */
        color: #1A1714;
        border-radius: 18px 18px 18px 4px;
        border: 1px solid #D4A354;
        box-shadow: 0 2px 10px rgba(212, 163, 84, 0.15);
    }
    
    /* Right Panel specific */
    .contact-card {
        background-color: #fafafa;
        padding: 20px;
        border-radius: 8px;
        margin-top: 25px;
        border-left: 4px solid #D4A354;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    .contact-card p {
        margin: 5px 0;
        font-size: 14px;
        color: #444;
    }
    
    /* Buttons */
    div[data-testid="stButton"] button {
        background-color: transparent;
        color: #1A1714;
        border: 1px solid #ccc;
        border-radius: 6px;
        transition: all 0.2s;
        padding: 8px 15px;
        font-weight: 500;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #D4A354;
        color: #D4A354;
        background-color: transparent;
    }
    
    /* Clear button special styling */
    .clear-btn div[data-testid="stButton"] button {
        border: none;
        color: #999;
        text-decoration: underline;
    }
    .clear-btn div[data-testid="stButton"] button:hover {
        color: #e74c3c;
    }
    
    /* Submit button special styling */
    div[data-testid="stForm"] div[data-testid="stButton"] button {
        background-color: #1A1714 !important;
        color: #D4A354 !important;
        border: none;
    }
    div[data-testid="stForm"] div[data-testid="stButton"] button:hover {
        background-color: #333 !important;
    }
    
    hr {
        margin: 15px 0;
        border-color: #eee;
    }
</style>
""", unsafe_allow_html=True)

# Cache the RAG pipeline loading
@st.cache_resource
def load_rag():
    return rag_query

query_func = load_rag()

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hi! I'm Maya, Magppie's virtual assistant. I can help you with store locations, products, offers, contact info, and more. What can I help you with today?", "type": "normal"}
    ]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Layout: 1:2:1.2 Ratio
col_left, col_center, col_right = st.columns([1, 2, 1.2], gap="large")

# ================= LEFT PANEL =================
with col_left:
    # Branding Section
    st.markdown(f"""
        <div class="brand-container">
            <img src="{logo_src}" class="brand-logo" alt="Magppie Logo">
            <h1 class="brand-title">MAGPPIE</h1>
            <p class="brand-subtitle">AI Assistant</p>
        </div>
        
        <div class="status-container">
            <span class="online-indicator"></span> 
            <strong>Assistant Online</strong>
        </div>
        <hr>
        <p class="quick-title">Quick Suggestions</p>
    """, unsafe_allow_html=True)
    
    if st.button("🛒 Show products", use_container_width=True):
        st.session_state.quick_query = "What products does Magppie sell?"
    if st.button("📍 Store locations", use_container_width=True):
        st.session_state.quick_query = "Where are your store locations?"
    if st.button("🎁 Current offers", use_container_width=True):
        st.session_state.quick_query = "What are your current offers?"

# ================= CENTER PANEL (CHAT) =================
with col_center:
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown("### Maya – Assistant")
    with col_header2:
        st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "👋 Hi! I'm Maya, Magppie's virtual assistant. I can help you with store locations, products, offers, contact info, and more. What can I help you with today?", "type": "normal"}
            ]
            st.session_state.chat_history = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
            
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    
    # Render Chat History
    chat_html = '<div class="chat-container">'
    for msg in st.session_state.messages:
        content = msg["content"]
        
        # Convert simple markdown to HTML to ensure it renders correctly inside the custom div
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content) # Bold
        
        # Handle bullet points
        lines = content.split('\n')
        formatted_lines = []
        in_list = False
        for line in lines:
            line = line.strip()
            if line.startswith('* ') or line.startswith('- '):
                if not in_list:
                    formatted_lines.append('<ul style="margin-top:5px; margin-bottom:5px; padding-left:20px;">')
                    in_list = True
                formatted_lines.append(f'<li>{line[2:]}</li>')
            else:
                if in_list:
                    formatted_lines.append('</ul>')
                    in_list = False
                if line:
                    formatted_lines.append(f'<p style="margin:0 0 8px 0;">{line}</p>')
                else:
                    formatted_lines.append('<div style="height: 4px;"></div>')
        if in_list:
            formatted_lines.append('</ul>')
            
        content_html = "".join(formatted_lines)

        # Do NOT indent the HTML strings below, otherwise Streamlit parses them as Markdown code blocks!
        if msg["role"] == "user":
            chat_html += f'<div class="chat-row user"><div class="avatar user">👤</div><div class="bubble user-bubble">{content_html}</div></div>'
        else:
            bubble_class = "escalation-bubble" if msg.get("type") == "escalation" else "bot-bubble"
            chat_html += f'<div class="chat-row bot"><div class="avatar bot">✨</div><div class="bubble {bubble_class}">{content_html}</div></div>'
    chat_html += '</div>'
    
    st.markdown(chat_html, unsafe_allow_html=True)
    
    # Input
    user_query = st.chat_input("Type your message here...")
    
    if "quick_query" in st.session_state and st.session_state.quick_query:
        user_query = st.session_state.quick_query
        st.session_state.quick_query = None
        
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.rerun()
        
# ================= PROCESS QUERY =================
if st.session_state.messages[-1]["role"] == "user":
    last_query = st.session_state.messages[-1]["content"]
    
    with col_center:
        with st.spinner("Maya is thinking..."):
            response_data = handle_query(last_query, query_func, history=st.session_state.chat_history)
            
            msg_type = "escalation" if response_data.get("escalation") else "normal"
            if response_data.get("lead_intent"):
                msg_type = "lead"
                
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_data["answer"],
                "type": msg_type
            })
            
            # Update history for next turn (max 5 turns)
            st.session_state.chat_history.append((last_query, response_data["answer"]))
            if len(st.session_state.chat_history) > 5:
                st.session_state.chat_history.pop(0)
                
            st.rerun()

# ================= RIGHT PANEL (LEAD CAPTURE) =================
with col_right:
    st.markdown("### Contact Us")
    st.markdown("<p style='font-size:14px; color:#666;'>Leave your details and we'll get back to you shortly.</p>", unsafe_allow_html=True)
    
    with st.form("lead_form", clear_on_submit=True):
        name = st.text_input("Full Name *")
        email = st.text_input("Email Address *")
        phone = st.text_input("Phone Number *")
        message = st.text_area("How can we help? (Optional)", height=100)
        
        submitted = st.form_submit_button("Submit Request", use_container_width=True)
        
        if submitted:
            success = save_lead(name, email, phone, message)
            if success:
                st.success("Thank you! Your details have been submitted.")
            else:
                st.error("Please fill in all required fields correctly (valid email, 10-digit phone).")
                
    st.markdown("""
        <div class="contact-card">
            <h4 style='margin-top:0; color:#1A1714;'>🏢 Headquarters</h4>
            <p>📞 +91 99999 99999</p>
            <p>📧 support@magppie.com</p>
            <p>⏰ Mon–Sat 9am–6pm</p>
        </div>
    """, unsafe_allow_html=True)
