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
    
    st.divider()



    
    st.divider()
    
    # Placeholder for Future Chat History
    # st.subheader("History")
    # st.caption("Chat history features coming soon...")

def show_chat_page():
    # Header
    st.title("🌙 Agent Deen | وكيل الدين")
    st.markdown("**Trilingual AI Shariah Compliance Assistant**")
    st.markdown("Ask questions in *Arabic (العربية)*, *English*, or *Bahasa Melayu*")
    
    st.divider()
    
    # Language and Model selection
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
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
    with col3:
        model = st.selectbox(
            "AI Model",
            options=["ollama", "claude"],
            format_func=lambda x: {
                "ollama": "🆓 Ollama (Free)",
                "claude": "⚡ Claude Haiku"
            }.get(x, x),
            help="Claude Haiku: Faster & better responses (~$0.001/query)",
        )
    
    # Question input
    question = st.text_area(
        "Your Question / سؤالك / Soalan Anda",
        placeholder="E.g., What is Murabaha? / ما هو المرابحة؟ / Apakah itu Murabaha?",
        height=100,
    )
    
    # Example questions
    with st.expander("💡 Example Questions"):
        examples = [
            ("English", "What is the ruling on Tawarruq in Islamic finance?"),
            ("العربية", "ما هو حكم المضاربة في التمويل الإسلامي؟"),
            ("Bahasa Melayu", "Apakah perbezaan antara Takaful dan insurans konvensional?"),
        ]
        for lang, example in examples:
            if st.button(f"{lang}: {example[:50]}...", key=example):
                st.session_state["question"] = example
                st.rerun()
    
    # Submit button
    if st.button("Ask Agent Deen", type="primary", use_container_width=True):
        if not question or not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Consulting Shariah sources... جاري البحث..."):
                try:
                    # Call API
                    response = requests.post(
                        f"{API_URL}/chat",
                        json={
                            "question": question,
                            "language": language,
                            "model": model,
                        },
                        timeout=60,
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Display answer
                        st.markdown("### Answer / الجواب")
                        
                        # Apply RTL for Arabic
                        if data.get("language") == "ar":
                            st.markdown(f'<div class="arabic-text">{data["answer"]}</div>', 
                                       unsafe_allow_html=True)
                        else:
                            st.markdown(data["answer"])
                        
                        # Confidence badge & Model Used
                        confidence = data.get("confidence", "Low")
                        model_used = data.get("model_used", "ollama")
                        
                        conf_class = f"confidence-{confidence.lower()}"
                        model_label = "⚡ Claude Haiku" if "claude" in model_used else "🆓 Ollama"
                        
                        st.markdown(f'''
                            <div style="margin-bottom: 15px;">
                                <div style="margin-bottom: 5px;">
                                    <span class="{conf_class}">Confidence: **{confidence}**</span>
                                </div>
                                <div style="font-size: 13px; color: #888;">
                                    Model: <strong>{model_label}</strong>
                                </div>
                            </div>
                        ''', unsafe_allow_html=True)
                        
                        # Check if this is an out-of-scope response (no sources should be shown)
                        answer_text = data.get("answer", "").lower()
                        is_out_of_scope = any(phrase in answer_text for phrase in [
                            "i am agent deen, specialized only",
                            "saya agent deen, pakar dalam",
                            "أنا وكيل الدين، متخصص فقط",
                            "please ask a question related to islamic finance",
                            "sila tanya soalan berkaitan kewangan islam",
                        ])
                        
                        # Sources (deduplicated) - skip if out of scope
                        if data.get("sources") and not is_out_of_scope:
                            st.markdown("### Sources / المصادر")
                            st.caption("💡 Click on a source to view the PDF at that page")
                            
                            seen_sources = set()
                            for idx, source in enumerate(data["sources"]):
                                # Deduplicate by source + snippet combo
                                source_key = f"{source.get('source', '')}-{source.get('snippet', '')[:50]}"
                                if source_key in seen_sources:
                                    continue
                                seen_sources.add(source_key)
                                
                                # Build source info with file and page
                                source_name = source.get('source', 'Unknown')
                                file_display = source.get('file', '')  # Display name (cleaned)
                                file_name = source.get('filename', '') or file_display  # Fallback to display name
                                page_num = source.get('page', 1)
                                total_pages = source.get('total_pages', '')
                                snippet = source.get('snippet', '')[:200]
                                
                                # Build page display
                                page_display = f"Page {page_num}"
                                if total_pages:
                                    page_display = f"Page {page_num}/{total_pages}"
                                
                                # Create unique key for expander
                                expander_key = f"source_{idx}_{file_name}_{page_num}"
                                
                                # Clickable source card using expander
                                with st.expander(f"📖 {source_name} | {file_display} | 📄 {page_display}"):
                                    st.markdown(f"**Snippet:** {snippet}...")
                                    
                                    # PDF Viewer Link
                                    if file_name:
                                        # URL encode the filename for special characters
                                        from urllib.parse import quote
                                        
                                        # Ensure .pdf extension
                                        if not file_name.lower().endswith('.pdf'):
                                            file_name = file_name + '.pdf'
                                        
                                        encoded_filename = quote(file_name, safe='')
                                        
                                        # Construct PDF URL with page fragment
                                        pdf_url = f"{API_URL}/pdf/{source_name.lower()}/{encoded_filename}#page={page_num}"
                                        
                                        st.markdown("---")
                                        st.markdown(f"**📄 View the original PDF document at page {page_num}**")
                                        st.link_button("📖 Open PDF in Browser ↗", pdf_url, use_container_width=True)
                                        st.caption("💡 The PDF will open in a new tab at the referenced page.")
                                    else:
                                        st.info("ℹ️ PDF preview not available. This document was indexed before file tracking was added.")
                    else:
                        st.error(f"Error: {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("⚠️ Cannot connect to API. Make sure the backend is running:\n\n`uvicorn src.api.main:app --reload`")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def show_sources_page():
    st.title("📚 Manage Sources")
    st.markdown("Add new Shariah documents to the Knowledge Base.")
    st.divider()
    
    # URL Ingestion
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

    st.divider()
    
    # File Upload
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

# Router
if page == "Chat":
    show_chat_page()
else:
    show_sources_page()

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: gray; font-size: 12px;">
    Powered by Ollama llama3.2 (100% Local & Free) | Sources: BNM, AAOIFI, SC Malaysia, JAKIM
</div>
""", unsafe_allow_html=True)
