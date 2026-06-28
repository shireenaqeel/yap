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

from yap import (  # noqa: E402
    auth,
    card,
    config,
    connectors,
    db,
    generation,
    ingest,
    patterns,
    prompts,
    speech,
    themes,
    transcribe,
    wrapped,
)
from yap.storage import UserStore  # noqa: E402

st.set_page_config(page_title="Yap", page_icon="💬", layout="centered")


@st.cache_resource
def _bootstrap():
    """Create tables once per process."""
    db.init_schema()
    return True


_bootstrap()

# ---- aesthetic theme (restyles the whole app, incl. the login screen) -----
_theme_key = st.session_state.setdefault("theme", themes.DEFAULT_THEME)
_theme = themes.THEMES.get(_theme_key, themes.THEMES[themes.DEFAULT_THEME])
st.markdown(themes.build_css(_theme), unsafe_allow_html=True)
st.markdown(themes.decor_html(_theme, _theme_key), unsafe_allow_html=True)


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

# Load the user's saved aesthetic once per session, then re-render with it.
if not st.session_state.get("_theme_loaded"):
    st.session_state["_theme_loaded"] = True
    _saved_theme = auth.get_theme(st.session_state["user_id"])
    if _saved_theme in themes.THEMES and _saved_theme != st.session_state["theme"]:
        st.session_state["theme"] = _saved_theme
        st.rerun()

# Load the user's saved profile (bio + social links) once per session.
if "profile" not in st.session_state:
    st.session_state["profile"] = auth.get_profile(st.session_state["user_id"])

# ---- sidebar --------------------------------------------------------------
with st.sidebar:
    st.title("💬 Yap")
    st.caption(f"Signed in as **{st.session_state['username']}**")
    if st.button("Log out", use_container_width=True):
        st.session_state.clear()
        if google_configured() and st.user.is_logged_in:
            st.logout()  # triggers its own rerun/redirect
        else:
            st.rerun()

    st.divider()
    _keys = list(themes.THEMES)
    _picked = st.selectbox(
        "🎨 Aesthetic",
        _keys,
        index=_keys.index(st.session_state["theme"]),
        format_func=lambda k: themes.THEMES[k]["label"],
    )
    if _picked != st.session_state["theme"]:
        st.session_state["theme"] = _picked
        auth.set_theme(st.session_state["user_id"], _picked)
        st.rerun()
    if st.button("✨ Match my vibe", use_container_width=True):
        with st.spinner("Reading your aesthetic…"):
            st.session_state["theme"] = themes.suggest_theme(store)
        auth.set_theme(st.session_state["user_id"], st.session_state["theme"])
        st.rerun()

    with st.expander("⚙️ Account & data"):
        st.caption(f"{store.size} chunks stored.")

        if st.checkbox("I want to clear ALL my entries", key="confirm_clear"):
            if st.button("🧹 Clear everything", key="clear_all", use_container_width=True):
                with st.spinner("Clearing…"):
                    n = store.clear()
                st.success(f"Cleared {n} chunk(s).")
                st.rerun()

        st.divider()
        if st.checkbox("Permanently delete my account", key="confirm_delete"):
            st.warning("This erases your account and every entry. Cannot be undone.")
            if st.button("❌ Delete my account", key="delete_acct", use_container_width=True):
                _was_google = google_configured() and st.user.is_logged_in
                auth.delete_account(st.session_state["user_id"])
                st.session_state.clear()
                if _was_google:
                    st.logout()  # triggers its own redirect
                else:
                    st.rerun()

    if not config.GROQ_API_KEY:
        st.warning("No GROQ_API_KEY set — AI answers/Wrapped disabled.")


# ---- hero banner (themed) -------------------------------------------------
_name = st.session_state["username"].split("@")[0]
st.markdown(
    f'<div class="yap-hero"><h1>💬 Hey {_name}</h1>'
    f"<p>Yap your thoughts · ask yourself anything · wrap your mind"
    f" — {store.size} chunks remembered</p></div>",
    unsafe_allow_html=True,
)

tab_yap, tab_journal, tab_ask, tab_wrapped, tab_patterns = st.tabs(
    ["📝 Yap", "🗂️ Journal", "🪞 Ask Yourself", "🎁 Wrapped", "📊 Patterns"]
)

# ---- Yap tab --------------------------------------------------------------
with tab_yap:
    # Clearing / success must happen before the entry widget is instantiated.
    if st.session_state.pop("clear_entry", False):
        st.session_state["entry_box"] = ""
    _saved = st.session_state.pop("last_saved", None)
    if _saved:
        st.success(f"Saved as {_saved[0]} — {_saved[1]} chunk(s) added.")

    head_l, head_r = st.columns([3, 1])
    head_l.markdown('<div class="yap-section">📝 Compose</div>', unsafe_allow_html=True)
    if head_r.button("💭 Prompt me", use_container_width=True):
        with st.spinner("Thinking about what you've written…"):
            st.session_state["reflect"] = prompts.reflection_prompt(store)
    if "reflect" in st.session_state:
        st.markdown(
            f'<div class="yap-callout"><b>Reflect:</b> '
            f"{st.session_state['reflect']}</div>",
            unsafe_allow_html=True,
        )

    category = st.pills(
        "Tag this yap",
        config.CATEGORIES,
        default=config.CATEGORIES[2],
        key="yap_cat",
    ) or config.CATEGORIES[2]

    # Voice is just another way to fill the SAME entry box — not a separate flow.
    with st.expander("🎙️ Prefer to talk? Record and it drops into your entry below"):
        v_audio = st.audio_input("Record", key="yap_audio", label_visibility="collapsed")
        if v_audio is not None and st.button("Transcribe into entry", key="yap_tx"):
            if not config.GROQ_API_KEY:
                st.warning("No GROQ_API_KEY set — voice input needs it.")
            else:
                with st.spinner("Transcribing your voice…"):
                    txt = transcribe.transcribe(v_audio.getvalue())
                prev = st.session_state.get("entry_box", "")
                st.session_state["entry_box"] = f"{prev} {txt}".strip() if prev else txt
                st.rerun()

    entry = st.text_area(
        "What's on your mind?", height=180, key="entry_box",
        placeholder="Type here, or use the mic above…",
    )
    if st.button("Save entry", type="primary"):
        if entry.strip():
            with st.spinner("Embedding & storing…"):
                added = ingest.ingest_text(store, entry, category=category)
            st.session_state["last_saved"] = (category, added)
            st.session_state["clear_entry"] = True
            st.rerun()
        else:
            st.warning("Write something first.")

    with st.expander("🔗 Bring in your world — GitHub, links, bio & docs"):
        st.caption(
            "Import your projects and links so you can ask yourself about them "
            "later — *“what have I built with Python?”*"
        )

        st.markdown("**🐙 GitHub projects**")
        gh = st.text_input(
            "GitHub username", key="gh_user", placeholder="e.g. shireenaqeel",
        )
        if st.button("Import my GitHub", key="gh_btn"):
            if gh.strip():
                try:
                    with st.spinner(f"Reading {gh.strip()}'s repos…"):
                        n_repos, n_chunks = connectors.import_github(store, gh)
                    st.success(f"Imported {n_repos} projects — {n_chunks} chunk(s).")
                except ValueError as e:
                    st.error(str(e))
            else:
                st.warning("Enter your GitHub username first.")

        st.markdown("**🌐 Your socials & bio**")
        _prof = st.session_state.get("profile", {})
        # Pre-fill each box from the saved profile (set defaults before widgets).
        for _wkey, _pkey in [
            ("pf_linkedin", "linkedin"), ("pf_twitter", "twitter"),
            ("pf_instagram", "instagram"), ("pf_website", "website"),
            ("pf_bio", "bio"),
        ]:
            st.session_state.setdefault(_wkey, _prof.get(_pkey, ""))

        fc1, fc2 = st.columns(2)
        fc1.text_input("💼 LinkedIn", key="pf_linkedin", placeholder="linkedin.com/in/…")
        fc2.text_input("🐦 X / Twitter", key="pf_twitter", placeholder="x.com/…")
        fc1.text_input("📸 Instagram", key="pf_instagram", placeholder="instagram.com/…")
        fc2.text_input("🌍 Website / Portfolio", key="pf_website", placeholder="yoursite.com")
        st.text_area("📝 Short bio", key="pf_bio", placeholder="A line or two about you.", height=90)

        if st.button("Save profile", key="pf_save"):
            profile = {
                "linkedin": st.session_state["pf_linkedin"].strip(),
                "twitter": st.session_state["pf_twitter"].strip(),
                "instagram": st.session_state["pf_instagram"].strip(),
                "website": st.session_state["pf_website"].strip(),
                "bio": st.session_state["pf_bio"].strip(),
            }
            auth.set_profile(st.session_state["user_id"], profile)
            st.session_state["profile"] = profile
            # Rebuild the searchable profile entry (replace, don't duplicate).
            store.delete_by_type("profile")
            _lines = []
            if profile["bio"]:
                _lines.append(f"Bio: {profile['bio']}")
            for _label, _key in [
                ("LinkedIn", "linkedin"), ("X/Twitter", "twitter"),
                ("Instagram", "instagram"), ("Website", "website"),
            ]:
                if profile[_key]:
                    _lines.append(f"{_label}: {profile[_key]}")
            if _lines:
                ingest.ingest_text(store, "\n".join(_lines), type_="profile")
            st.success("Profile saved.")

        st.markdown("**📎 Document (PDF)**")
        pdf = st.file_uploader(
            "Resume, a 'how I think' profile, notes…", type="pdf",
            label_visibility="collapsed",
        )
        if pdf is not None and st.button("Ingest PDF"):
            with st.spinner(f"Extracting & embedding {pdf.name}…"):
                added = ingest.ingest_pdf(store, pdf.getvalue(), pdf.name)
            st.success(f"Ingested {pdf.name} — {added} chunk(s) added.")

# ---- Journal tab ----------------------------------------------------------
with tab_journal:
    st.markdown('<div class="yap-section">🗂️ Your journal</div>', unsafe_allow_html=True)
    _entries = store.list_entries()
    if not _entries:
        st.info("Nothing here yet — go yap something on the 📝 Yap tab!")
    else:
        st.caption(f"{len(_entries)} most recent entries · newest first.")
        for e in _entries:
            with st.container(border=True):
                row_l, row_r = st.columns([6, 1])
                tag = e.get("category") or e.get("type", "entry")
                src = f" · {e['source']}" if e.get("source") else ""
                row_l.markdown(f"**{tag}**{src} · {e.get('date', '')[:10]}")
                text = e["text"]
                row_l.write(text if len(text) <= 400 else text[:400] + "…")
                if row_r.button("🗑️", key=f"del_{e['id']}", help="Delete this entry"):
                    store.delete(e["id"])
                    st.rerun()

# ---- Ask Yourself tab -----------------------------------------------------
with tab_ask:
    st.markdown('<div class="yap-section">🪞 Ask yourself</div>', unsafe_allow_html=True)
    st.caption(
        "e.g. *What do I usually do when I'm overwhelmed?* · "
        "*What have I been excited about lately?*"
    )

    with st.expander("🎙️ Prefer to ask out loud? Record and it fills the question"):
        q_audio = st.audio_input("Record", key="ask_audio", label_visibility="collapsed")
        if q_audio is not None and st.button("Transcribe question", key="ask_tx"):
            if not config.GROQ_API_KEY:
                st.warning("No GROQ_API_KEY set — voice input needs it.")
            else:
                with st.spinner("Transcribing your question…"):
                    st.session_state["question_box"] = transcribe.transcribe(
                        q_audio.getvalue()
                    )
                st.rerun()

    q_col, btn_col = st.columns([4, 1])
    question = q_col.text_input(
        "Your question", key="question_box", label_visibility="collapsed",
        placeholder="Ask yourself anything…",
    )
    if btn_col.button("Ask", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Type a question first.")
        else:
            with st.spinner("Looking through your own words…"):
                st.session_state["last_answer"] = generation.answer(store, question)
            st.session_state.pop("answer_audio", None)  # drop stale read-back

    if "last_answer" in st.session_state:
        result = st.session_state["last_answer"]
        st.markdown(f"> {result['answer']}")
        if st.button("🔊 Read it back to me"):
            with st.spinner("Generating audio…"):
                st.session_state["answer_audio"] = speech.speak(result["answer"])
        if "answer_audio" in st.session_state:
            st.audio(st.session_state["answer_audio"], format="audio/mp3")
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
    st.markdown(
        '<div class="yap-section">🎁 Your Personality Wrapped</div>',
        unsafe_allow_html=True,
    )
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

        st.divider()
        st.markdown('<div class="yap-section">📸 Share it</div>', unsafe_allow_html=True)
        png = card.render_card(w, st.session_state["username"])
        mid = st.columns([1, 3, 1])[1]
        mid.image(png, use_container_width=True)
        mid.download_button(
            "📥 Download card",
            png,
            file_name="yap-wrapped.png",
            mime="image/png",
            use_container_width=True,
        )

# ---- Patterns tab ---------------------------------------------------------
with tab_patterns:
    st.markdown('<div class="yap-section">📊 Your patterns</div>', unsafe_allow_html=True)
    days = st.slider("Look back over the last N days", 7, 365, 30, step=7)
    data = patterns.summary(store, days=days)

    c1, c2, c3 = st.columns(3)
    c1.metric("Chunks", data["total_chunks"])
    c2.metric("Yap entries", data["yap_chunks"])
    c3.metric("Doc chunks", data["doc_chunks"])

    if data["categories"]:
        cats, ccounts = zip(*data["categories"])
        fig = px.pie(names=list(cats), values=list(ccounts), title="Your categories")
        st.plotly_chart(
            themes.style_plotly(fig, _theme), use_container_width=True, theme=None
        )

    if data["keywords"]:
        words, counts = zip(*data["keywords"])
        fig = px.bar(
            x=list(counts), y=list(words), orientation="h",
            labels={"x": "Mentions", "y": "Topic"},
            title="Most-mentioned topics",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        fig.update_traces(marker_color=_theme["primary"])
        st.plotly_chart(
            themes.style_plotly(fig, _theme), use_container_width=True, theme=None
        )
    elif not data["categories"]:
        st.info("Not enough written yet to find patterns. Yap a few entries!")

    if data["activity"]:
        adates, acounts = zip(*data["activity"])
        fig = px.line(
            x=list(adates), y=list(acounts),
            labels={"x": "Date", "y": "Chunks added"},
            title="Journaling activity",
        )
        fig.update_traces(line_color=_theme["primary"])
        st.plotly_chart(
            themes.style_plotly(fig, _theme), use_container_width=True, theme=None
        )
