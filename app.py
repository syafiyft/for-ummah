"""
🌙 Agent Deen - Streamlit Frontend
Trilingual AI Shariah Compliance Assistant
"""


import streamlit as st
import requests
from streamlit_option_menu import option_menu

# Configuration
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Agent Deen | وكيل الدين",
    page_icon="🌙",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for RTL Arabic support and generic styling
st.markdown("""
<style>
    .arabic-text {
        direction: rtl;
        text-align: right;
        font-family: 'Noto Sans Arabic', 'Arial', sans-serif;
    }
    .source-card {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 12px 15px;
        margin: 8px 0;
        border-left: 3px solid #f0a500;
    }
    .source-card .source-title {
        color: #f0a500;
        font-weight: bold;
        font-size: 14px;
    }
    .source-card .source-page {
        color: #888;
        font-size: 12px;
    }
    .source-card .source-snippet {
        color: #ccc;
        font-size: 13px;
        margin-top: 5px;
    }
    .confidence-high { color: #28a745; }
    .confidence-medium { color: #ffc107; }
    .confidence-low { color: #dc3545; }
</style>
""", unsafe_allow_html=True)


# Sidebar Navigation
with st.sidebar:
    # Sidebar Logo/Header (ChatGPT Style: Top Left)
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; padding-bottom: 20px;">
            <div style="font-size: 24px;">🌙</div>
            <div style="font-size: 20px; font-weight: bold; color: white;">Agent Deen</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Modern Sidebar Menu (ChatGPT Style: Subtle Gray Selection)
    page = option_menu(
        menu_title=None, 
        options=["Chat", "Manage Sources"], 
        icons=["chat-left-text", "database-fill"], # Updated icons to match standard app feels
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#fafafa", "font-size": "14px"}, 
            "nav-link": {
                "font-size": "14px", 
                "text-align": "left", 
                "margin": "0px", 
                "margin-bottom": "5px",
                "color": "#fafafa",
                "--hover-color": "#2A2B32"
            },
            "nav-link-selected": {
                "background-color": "#343541", # ChatGPT-like dark gray selection
                "color": "white",
                "font-weight": "500",
                "border": "1px solid #565869" # Subtle border
            },
        }
    )
    
    # --- CHAT HISTORY SECTION (Middle) ---
    if page == "Chat":
        st.divider()
        if st.button("＋ New Chat", use_container_width=True):
            st.session_state["session_id"] = None # Reset session
            st.rerun()
        
        st.caption("Recent Chats")
        
        # Fetch history
        chats = []
        history_resp = None
        try:
            history_resp = requests.get(f"{API_URL}/history/chats", timeout=5)
            if history_resp.status_code == 200:
                chats = history_resp.json()
        except:
             st.caption("⚠️ Connection disconnected")
        
        # Calculate dynamic height: 55px per chat item, max 500px. Min 150px.
        container_height = min(max(len(chats) * 55, 150), 500)
        
        if chats:
            with st.container(height=container_height, border=False):
                for idx, chat in enumerate(chats):
                    chat_id = chat.get("id")
                    if not chat_id: continue

                    chat_title = chat.get("title", "New Chat")[:30]
                    is_active = st.session_state.get("session_id") == chat_id

                    # Simple button - active chat uses primary (red) style
                    if is_active:
                        if st.button(chat_title, key=f"hist_{chat_id}", use_container_width=True, type="primary"):
                            pass  # Already active
                    else:
                        if st.button(chat_title, key=f"hist_{chat_id}", use_container_width=True):
                            st.session_state["session_id"] = chat_id
                            st.rerun()
                                    
        elif history_resp and history_resp.status_code == 200:
             st.info("No recent chats")

    # Sidebar Bottom (Settings)
    # Spacer removed to prevent forcing sidebar scroll
    st.divider()
    
    # Language and Model selection
    language = st.selectbox(
        "Response Language",
        options=[None, "en", "ar", "ms"],
        format_func=lambda x: {
            None: "Auto-detect",
            "en": "English",
            "ar": "العربية (Arabic)",
            "ms": "Bahasa Melayu"
        }.get(x, x),
    )
    model = st.selectbox(
        "AI Model",
        options=["ollama", "claude"],
        format_func=lambda x: {
            "ollama": "Ollama (Free)",
            "claude": "Claude Haiku"
        }.get(x, x),
        help="Claude Haiku: Faster & better responses (~$0.001/query)",
    )

def show_chat_page():
    # CSS for Footer and Layout
    st.markdown("""
        <style>
            /* Fixed Footer */
            .footer {
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                background-color: #0e1117;
                color: gray;
                text-align: center;
                font-size: 11px;
                padding: 10px 0;
                z-index: 1000;
                border-top: 1px solid #262730;
            }
            /* Adjust Chat Input to sit above footer */
            [data-testid="stChatInput"] {
                bottom: 40px !important;
                padding-bottom: 0px;
            }
            .block-container {
                padding-bottom: 120px;
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize Session
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = None
    current_session_id = st.session_state["session_id"]

    # Load Chat History Logic
    messages = []
    if current_session_id:
        try:
            resp = requests.get(f"{API_URL}/history/chat/{current_session_id}", timeout=5)
            if resp.status_code == 200:
                messages = resp.json().get("messages", [])
        except: pass
        
    # Answer Container
    answer_container = st.container()

    # Display History
    with answer_container:
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            with st.chat_message(role):
                if role == "assistant":
                    # Check for Arabic content
                    if any("\u0600" <= c <= "\u06FF" for c in content) and "dir=\"rtl\"" not in content:
                        st.markdown(f'<div class="arabic-text">{content}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(content)
                        
                    # Show sources
                    if "sources" in msg and msg["sources"]:
                        st.markdown("---")
                        st.caption("📚 Sources / المصادر (Click to view)")
                        
                        seen_sources = set()
                        for idx, source in enumerate(msg["sources"]):
                            source_key = f"{source.get('filename', '')}_{source.get('page', '')}_{source.get('snippet', '')[:20]}"
                            if source_key in seen_sources: continue
                            seen_sources.add(source_key)
                            
                            source_name = source.get('source', 'Unknown')
                            file_display = source.get('file', '')
                            file_name = source.get('filename', '') or file_display
                            page_num = source.get('page', 1)
                            total_pages = source.get('total_pages', '')
                            snippet = source.get('snippet', '')[:300]
                            page_display = f"Page {page_num}" + (f"/{total_pages}" if total_pages else "")
                            
                            with st.expander(f"📖 {source_name} | {file_display} | 📄 {page_display}"):
                                st.markdown(f"**Snippet:** {snippet}...")
                                if file_name:
                                    from urllib.parse import quote
                                    if not file_name.lower().endswith('.pdf'): file_name += '.pdf'
                                    encoded_filename = quote(file_name, safe='')
                                    pdf_url = f"{API_URL}/pdf/{source_name.lower()}/{encoded_filename}#page={page_num}"
                                    st.markdown(f"**📄 View PDF at page {page_num}**")
                                    st.link_button("Open PDF in Browser ↗", pdf_url)
                                else:
                                    st.info("ℹ️ PDF preview not available.")
                else:
                    st.markdown(content)
            
        if messages:
            st.divider()

    # --- Landing Page OR Fixed Input ---
    if not messages:
        # LANDING PAGE VIEW
        st.title("🌙 Agent Deen | وكيل الدين")
        st.markdown("**Trilingual AI Shariah Compliance Assistant**")
        st.markdown("Ask questions in *Arabic (العربية)*, *English*, or *Bahasa Melayu*")
        st.divider()
        
        # Big Text Area + Red Button logic
        # Use a key to manage state, and default to empty string
        if "chat_input_text" not in st.session_state:
            st.session_state["chat_input_text"] = ""
            
        question = st.text_area(
            "Your Question / سؤالك / Soalan Anda",
            value=st.session_state["chat_input_text"],
            placeholder="E.g., What is Murabaha? / ما هو المرابحة؟ / Apakah itu Murabaha?",
            height=100,
            key="chat_input_widget"
        )
        
        if st.button("Ask", type="primary", use_container_width=True):
            if not question or not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Consulting Shariah sources... جاري البحث..."):
                    # Process Landing Page Question
                    try:
                        # Always create new session for landing page ask
                        c_resp = requests.post(f"{API_URL}/history/chat", params={"title": question[:50], "model": model})
                        if c_resp.status_code == 200:
                            new_session_id = c_resp.json()["id"]
                            st.session_state["session_id"] = new_session_id
                            
                            # Call API
                            requests.post(
                                f"{API_URL}/chat",
                                json={
                                    "question": question,
                                    "language": language,
                                    "model": model,
                                    "session_id": new_session_id
                                },
                                timeout=60,
                            )
                            # Rerun to switch to "Chat View" (messages will exist)
                            st.session_state["chat_input_text"] = ""
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    else:
        # CHAT VIEW (Messages Exist) -> Fixed Input at Bottom
        if prompt := st.chat_input("Your Question / سؤالك / Soalan Anda..."):
            with st.spinner("Consulting..."):
                try:
                    # Use existing session
                    requests.post(
                        f"{API_URL}/chat",
                        json={
                            "question": prompt,
                            "language": language,
                            "model": model,
                            "session_id": current_session_id
                        },
                        timeout=60,
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # Render Footer
    st.markdown("""
        <div class="footer">
            Powered by Ollama llama3.2 (100% Local & Free) | Sources: BNM, AAOIFI, SC Malaysia, JAKIM
        </div>
    """, unsafe_allow_html=True)
def show_sources_page():
    st.title("📚 Manage Sources")
    st.markdown("Add new Shariah documents to the Knowledge Base.")
    st.divider()
    
    # Tabs for Organization
    tab1, tab2, tab3 = st.tabs(["Upload PDF", "Ingest URL", "Ingestion History"])
    
    with tab1:
        st.subheader("📤 Upload PDF")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None:
            if st.button("Upload & Index"):
                with st.spinner("Processing file..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                        response = requests.post(f"{API_URL}/ingest/upload", files=files, timeout=120)
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ Successfully processed: {data['file']}")
                            st.json(data)
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")
    
    with tab2:
        st.subheader("🌐 Add by URL")
        url = st.text_input("Document URL (PDF)", placeholder="https://example.com/document.pdf")
        
        if st.button("Craw & Index URL"):
            if not url:
                st.warning("Please enter a URL")
            else:
                with st.spinner("Downloading and processing..."):
                    try:
                        response = requests.post(f"{API_URL}/ingest/url", json={"url": url}, timeout=120)
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ Successfully processed: {data['file']}")
                            st.json(data)
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

    with tab3:
        st.subheader("� Ingestion History")
        if st.button("🔄 Refresh"):
             st.rerun()
             
        try:
            resp = requests.get(f"{API_URL}/history/sources", timeout=5)
            if resp.status_code == 200:
                history = resp.json()
                if history:
                    st.dataframe(history, use_container_width=True)
                else:
                    st.info("No ingestion history found.")
            else:
                st.error("Failed to load history")
        except:
             st.warning("Backend offline")

# Router
if page == "Chat":
    show_chat_page()
else:
    show_sources_page()


