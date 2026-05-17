"""
app.py
------
Streamlit UI for the Mutual Fund RAG Assistant.
Ask questions in English about Large Cap mutual funds.

Run: streamlit run app.py
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "rag"))
from llm import ask

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title = "MF Assistant",
    page_icon  = "📈",
    layout     = "wide",
)

# ── Header ─────────────────────────────────────────────────
st.title("📈 Mutual Fund Assistant")
st.caption("Large Cap funds · Structured analysis · Data-driven answers")
st.divider()

# ── Suggested questions ────────────────────────────────────
st.markdown("**Quick questions — click to get instant answer:**")
suggestions = [
    "Which large cap fund gave the best 3 year returns?",
    "Which fund has the best risk adjusted returns?",
    "Compare SBI and HDFC large cap fund",
    "Which large cap fund is safest with consistent performance?",
]

cols = st.columns(2)
for i, suggestion in enumerate(suggestions):
    if cols[i % 2].button(suggestion, use_container_width=True):
        with st.spinner("Analyzing funds..."):
            try:
                result = ask(suggestion)
                st.markdown("### 📊 Analysis")
                st.markdown(result["answer"])
                with st.expander("📂 Funds considered"):
                    for fund in result["funds_used"]:
                        st.markdown(f"- {fund}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.divider()

# ── Custom question ────────────────────────────────────────
st.markdown("**Or ask your own question:**")
query = st.text_input(
    label       = "",
    placeholder = "e.g. Which fund has highest Sharpe ratio? / Compare top 3 large cap funds",
)

if st.button("Ask", type="primary", use_container_width=True):
    if query.strip():
        with st.spinner("Analyzing funds..."):
            try:
                result = ask(query.strip())
                st.markdown("### 📊 Analysis")
                st.markdown(result["answer"])
                with st.expander("📂 Funds considered"):
                    for fund in result["funds_used"]:
                        st.markdown(f"- {fund}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
    else:
        st.warning("Please type a question first.")

# ── Footer ─────────────────────────────────────────────────
st.divider()
st.caption(
    "⚠️ This tool is for informational purposes only. "
    "Not financial advice. Consult a SEBI-registered advisor before investing."
)
