"""Yap — a personal journaling tool with RAG-based self-reflection.

Run with:  streamlit run app.py
"""

import plotly.express as px
import streamlit as st

from yap import config, generation, ingest, patterns
from yap.storage import UserStore

st.set_page_config(page_title="Yap", page_icon="💬", layout="centered")


def get_store() -> UserStore | None:
    """Resolve the active user's store, or None if no user set yet."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None
    return UserStore(user_id)


# ---- sidebar: pick who you are (MVP "auth" = a typed name) ----------------
with st.sidebar:
    st.title("💬 Yap")
    st.caption("Yap your thoughts. Ask yourself anything.")
    name = st.text_input("Your name (your private space)", key="user_name_input")
    if st.button("Enter", use_container_width=True) and name.strip():
        st.session_state["user_id"] = name.strip()
    if st.session_state.get("user_id"):
        store = UserStore(st.session_state["user_id"])
        st.success(f"Signed in as **{store.user_id}**")
        st.metric("Chunks stored", store.size)
    if not config.GROQ_API_KEY:
        st.warning("No GROQ_API_KEY set — answering is disabled. See .env.example.")


store = get_store()

if store is None:
    st.title("Welcome to Yap")
    st.write(
        "Yap is a private journal that learns *your* patterns. Type or upload "
        "entries, then ask yourself questions and get answers grounded only in "
        "your own words."
    )
    st.info("👈 Enter a name in the sidebar to open your private space.")
    st.stop()


tab_yap, tab_ask, tab_patterns = st.tabs(["📝 Yap", "🪞 Ask Yourself", "📊 Patterns"])

# ---- Yap tab: ingest typed entries and PDFs ------------------------------
with tab_yap:
    st.subheader("Yap an entry")
    entry = st.text_area("What's on your mind?", height=180, key="entry_box")
    if st.button("Save entry", type="primary"):
        if entry.strip():
            with st.spinner("Embedding & storing…"):
                added = ingest.ingest_text(store, entry)
            st.success(f"Saved — {added} chunk(s) added to your space.")
        else:
            st.warning("Write something first.")

    st.divider()
    st.subheader("Or upload a document (PDF)")
    pdf = st.file_uploader("Resume, a 'how I think' profile, notes…", type="pdf")
    if pdf is not None and st.button("Ingest PDF"):
        with st.spinner(f"Extracting & embedding {pdf.name}…"):
            added = ingest.ingest_pdf(store, pdf.getvalue(), pdf.name)
        st.success(f"Ingested {pdf.name} — {added} chunk(s) added.")

# ---- Ask Yourself tab: retrieve + generate -------------------------------
with tab_ask:
    st.subheader("Ask yourself")
    st.caption(
        "e.g. *What do I usually do when I'm overwhelmed?* · "
        "*What have I been excited about lately?*"
    )
    question = st.text_input("Your question", key="question_box")
    if st.button("Ask", type="primary"):
        if not question.strip():
            st.warning("Type a question first.")
        else:
            with st.spinner("Looking through your own words…"):
                result = generation.answer(store, question)
            st.markdown(f"> {result['answer']}")
            if result["sources"]:
                with st.expander(f"Grounded in {len(result['sources'])} of your entries"):
                    for s in result["sources"]:
                        meta = f"{s.get('type','entry')} · {s.get('date','')[:10]} · score {s['score']:.2f}"
                        st.markdown(f"**{meta}**")
                        st.write(s["text"])
                        st.divider()

# ---- Patterns tab: lightweight recap -------------------------------------
with tab_patterns:
    st.subheader("Your patterns")
    days = st.slider("Look back over the last N days", 7, 365, 30, step=7)
    data = patterns.summary(store, days=days)

    c1, c2, c3 = st.columns(3)
    c1.metric("Chunks", data["total_chunks"])
    c2.metric("Yap entries", data["yap_chunks"])
    c3.metric("Doc chunks", data["doc_chunks"])

    if data["keywords"]:
        words, counts = zip(*data["keywords"])
        fig = px.bar(
            x=list(counts), y=list(words), orientation="h",
            labels={"x": "Mentions", "y": "Topic"},
            title="Most-mentioned topics",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough written yet to find patterns. Yap a few entries!")

    if data["activity"]:
        adates, acounts = zip(*data["activity"])
        st.plotly_chart(
            px.line(x=list(adates), y=list(acounts),
                    labels={"x": "Date", "y": "Chunks added"},
                    title="Journaling activity"),
            use_container_width=True,
        )
