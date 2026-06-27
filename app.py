"""Yap — a personal journaling tool with RAG-based self-reflection.

Cloud edition: real accounts (login/signup), per-user data in Postgres+pgvector,
categories, and an AI "Personality Wrapped". Run with: streamlit run app.py
"""

import os

import streamlit as st

# Merge Streamlit secrets into the environment BEFORE importing yap config, so
# the same code works locally (.env) and when deployed (st.secrets).
try:
    for _k, _v in st.secrets.items():
        os.environ.setdefault(_k, str(_v))
except Exception:
    pass

import plotly.express as px  # noqa: E402

from yap import auth, config, db, generation, ingest, patterns, wrapped  # noqa: E402
from yap.storage import UserStore  # noqa: E402

st.set_page_config(page_title="Yap", page_icon="💬", layout="centered")


@st.cache_resource
def _bootstrap():
    """Create tables once per process."""
    db.init_schema()
    return True


_bootstrap()


# ---- auth screen ----------------------------------------------------------
def google_configured() -> bool:
    """True only when real Google OAuth credentials are present in secrets."""
    try:
        cid = st.secrets["auth"]["google"]["client_id"]
        return bool(cid) and not cid.startswith("PASTE_")
    except Exception:
        return False


# If the user just came back from a Google login, turn that into our account.
if (
    "user_id" not in st.session_state
    and google_configured()
    and st.user.is_logged_in
):
    uid = auth.get_or_create_oauth_user(st.user.email)
    st.session_state.update(user_id=uid, username=st.user.email)


def auth_screen():
    st.title("💬 Yap")
    st.caption("Yap your thoughts. Ask yourself anything. Wrap your mind.")

    if google_configured():
        if st.button("🔵  Continue with Google", use_container_width=True):
            st.login("google")
        st.divider()

    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Log in", type="primary", use_container_width=True):
            try:
                uid = auth.log_in(u, p)
                st.session_state.update(user_id=uid, username=u.strip().lower())
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    with tab_signup:
        u2 = st.text_input("Choose a username", key="su_u")
        p2 = st.text_input("Choose a password", type="password", key="su_p")
        if st.button("Create account", use_container_width=True):
            try:
                uid = auth.sign_up(u2, p2)
                st.session_state.update(user_id=uid, username=u2.strip().lower())
                st.success("Account created!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))


if "user_id" not in st.session_state:
    auth_screen()
    st.stop()

store = UserStore(st.session_state["user_id"])

# ---- sidebar --------------------------------------------------------------
with st.sidebar:
    st.title("💬 Yap")
    st.success(f"Signed in as **{st.session_state['username']}**")
    st.metric("Chunks stored", store.size)
    if st.button("Log out", use_container_width=True):
        st.session_state.clear()
        if google_configured() and st.user.is_logged_in:
            st.logout()  # triggers its own rerun/redirect
        else:
            st.rerun()
    if not config.GROQ_API_KEY:
        st.warning("No GROQ_API_KEY set — AI answers/Wrapped disabled.")


tab_yap, tab_ask, tab_wrapped, tab_patterns = st.tabs(
    ["📝 Yap", "🪞 Ask Yourself", "🎁 Wrapped", "📊 Patterns"]
)

# ---- Yap tab --------------------------------------------------------------
with tab_yap:
    st.subheader("Yap an entry")
    category = st.selectbox("Tag this yap", config.CATEGORIES, index=2)
    entry = st.text_area("What's on your mind?", height=180, key="entry_box")
    if st.button("Save entry", type="primary"):
        if entry.strip():
            with st.spinner("Embedding & storing…"):
                added = ingest.ingest_text(store, entry, category=category)
            st.success(f"Saved as {category} — {added} chunk(s) added.")
        else:
            st.warning("Write something first.")

    st.divider()
    st.subheader("Or upload a document (PDF)")
    pdf = st.file_uploader("Resume, a 'how I think' profile, notes…", type="pdf")
    if pdf is not None and st.button("Ingest PDF"):
        with st.spinner(f"Extracting & embedding {pdf.name}…"):
            added = ingest.ingest_pdf(store, pdf.getvalue(), pdf.name)
        st.success(f"Ingested {pdf.name} — {added} chunk(s) added.")

# ---- Ask Yourself tab -----------------------------------------------------
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
                        cat = f" · {s['category']}" if s.get("category") else ""
                        meta = f"{s.get('type','entry')}{cat} · {s.get('date','')[:10]} · score {s['score']:.2f}"
                        st.markdown(f"**{meta}**")
                        st.write(s["text"])
                        st.divider()

# ---- Wrapped tab ----------------------------------------------------------
with tab_wrapped:
    st.subheader("🎁 Your Personality Wrapped")
    span = st.radio("Wrap my…", ["This week", "This month"], horizontal=True)
    days = 7 if span == "This week" else 30
    if st.button("Generate my Wrapped", type="primary"):
        with st.spinner("Reading your mind…"):
            w = wrapped.generate(store, days=days)
        st.session_state["last_wrapped"] = w
    if "last_wrapped" in st.session_state:
        w = st.session_state["last_wrapped"]
        s = w["stats"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Entries", s["entries"])
        c2.metric("Top category", (s["top_category"] or "—"))
        c3.metric("Period", s["period"].title())
        st.markdown(w["recap"])

# ---- Patterns tab ---------------------------------------------------------
with tab_patterns:
    st.subheader("Your patterns")
    days = st.slider("Look back over the last N days", 7, 365, 30, step=7)
    data = patterns.summary(store, days=days)

    c1, c2, c3 = st.columns(3)
    c1.metric("Chunks", data["total_chunks"])
    c2.metric("Yap entries", data["yap_chunks"])
    c3.metric("Doc chunks", data["doc_chunks"])

    if data["categories"]:
        cats, ccounts = zip(*data["categories"])
        st.plotly_chart(
            px.pie(names=list(cats), values=list(ccounts), title="Your categories"),
            use_container_width=True,
        )

    if data["keywords"]:
        words, counts = zip(*data["keywords"])
        fig = px.bar(
            x=list(counts), y=list(words), orientation="h",
            labels={"x": "Mentions", "y": "Topic"},
            title="Most-mentioned topics",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    elif not data["categories"]:
        st.info("Not enough written yet to find patterns. Yap a few entries!")

    if data["activity"]:
        adates, acounts = zip(*data["activity"])
        st.plotly_chart(
            px.line(x=list(adates), y=list(acounts),
                    labels={"x": "Date", "y": "Chunks added"},
                    title="Journaling activity"),
            use_container_width=True,
        )
