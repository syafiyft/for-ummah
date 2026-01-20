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
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
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

# Language preference
col1, col2 = st.columns([3, 1])
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
if st.button("🔍 Ask Agent Deen", type="primary", use_container_width=True):
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
                    
                    # Confidence badge
                    confidence = data.get("confidence", "Low")
                    conf_class = f"confidence-{confidence.lower()}"
                    st.markdown(f'<span class="{conf_class}">Confidence: **{confidence}**</span>', 
                               unsafe_allow_html=True)
                    
                    # Sources
                    if data.get("sources"):
                        st.markdown("### Sources / المصادر")
                        for source in data["sources"]:
                            st.markdown(f"""
                            <div class="source-card">
                                📄 <strong>{source.get('source', 'Unknown')}</strong><br>
                                <small>{source.get('snippet', '')[:150]}...</small>
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
    Powered by Claude 3.5 Sonnet | Sources: BNM, AAOIFI, SC Malaysia, JAKIM
</div>
""", unsafe_allow_html=True)
