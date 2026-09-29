"""Ask the strategist page: Reflect-based conversational Q&A over the brand's memory bank."""

import streamlit as st

from memory.base import HindsightUnavailableError
from ui.styles import render_header


def render_ask() -> None:
    brand_id = st.session_state.get("active_brand_id")
    brand_name = st.session_state.get("active_brand_name", "Unknown brand")
    agent = st.session_state.get("agent")

    if not agent or not brand_id:
        st.info("Select a brand from the sidebar to query the strategist.")
        return

    render_header(
        "Ask the strategist",
        f"Free-form strategy inquiries answered via Hindsight reflection over {brand_name}'s memory bank.",
    )

    if not agent.memory_online:
        st.warning("Memory is unavailable. Reflect-based answers are disabled; deterministic analytics remain available.")
        return

    # Chat history state initialization per brand
    chat_key = f"chat_history_{brand_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Sample Quick Questions
    st.caption("Quick evaluation prompts:")
    q_col1, q_col2, q_col3 = st.columns(3)
    preset_prompt = None
    with q_col1:
        if st.button("What formats perform best?", use_container_width=True):
            preset_prompt = "What formats perform best for our audience, and why?"
    with q_col2:
        if st.button("What are our brand guardrails?", use_container_width=True):
            preset_prompt = "What brand guardrails and taboos must we enforce?"
    with q_col3:
        if st.button("What lessons were learned?", use_container_width=True):
            preset_prompt = "What editorial lessons or beliefs have been consolidated from past feedback?"

    st.markdown("---")

    # Render previous messages
    if not st.session_state[chat_key]:
        st.info("Ask a question to reflect over this brand's stored facts, feedback, and beliefs.")
    for q, a in st.session_state[chat_key]:
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            st.markdown(a)

    user_input = st.chat_input("Ask a question about brand voice, past feedback, or editorial trajectory...")
    question = preset_prompt or user_input

    if question:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Synthesizing reflection across Hindsight memory bank..."):
                try:
                    answer = agent.ask(brand_id, question)
                except HindsightUnavailableError:
                    answer = None
                    st.error("Reflection could not reach the memory backend. The request was not answered.")
                except Exception:
                    answer = None
                    st.error("Reflection failed. Check the System page for backend status.")
            if answer:
                st.markdown(answer)

        if answer:
            st.session_state[chat_key].append((question, answer))
            st.rerun()


if __name__ == "__main__":
    render_ask()
