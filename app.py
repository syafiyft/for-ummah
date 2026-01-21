"""
🌙 Agent Deen - Streamlit Frontend
Trilingual AI Shariah Compliance Assistant
"""

import streamlit as st
import requests

# Configuration
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Agent Deen | وكيل الدين",
    page_icon="🌙",
    layout="centered",
)

# Custom CSS for RTL Arabic support
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
                        seen_sources = set()
                        for source in data["sources"]:
                            # Deduplicate by source + snippet combo
                            source_key = f"{source.get('source', '')}-{source.get('snippet', '')[:50]}"
                            if source_key in seen_sources:
                                continue
                            seen_sources.add(source_key)
                            
                            # Build source info with file and page
                            source_info = source.get('source', 'Unknown')
                            if source.get('file'):
                                source_info += f" | 📖 {source.get('file')}"
                            if source.get('page'):
                                # Show Page X/Total format if total_pages available
                                if source.get('total_pages'):
                                    source_info += f" | 📄 Page {source.get('page')}/{source.get('total_pages')}"
                                else:
                                    source_info += f" | 📄 Page {source.get('page')}"
                            
                            st.markdown(f"""
                            <div class="source-card">
                                <span class="source-title">{source_info}</span><br>
                                <span class="source-snippet">{source.get('snippet', '')[:200]}...</span>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error(f"Error: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("⚠️ Cannot connect to API. Make sure the backend is running:\n\n`uvicorn src.api.main:app --reload`")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: gray; font-size: 12px;">
    Powered by Ollama llama3.2 (100% Local & Free) | Sources: BNM, AAOIFI, SC Malaysia, JAKIM
</div>
""", unsafe_allow_html=True)
