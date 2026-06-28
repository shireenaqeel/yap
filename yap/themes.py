"""Aesthetic theming engine.

Each theme is a small set of design tokens; `build_css` turns those tokens into
a block of CSS that restyles the whole Streamlit app (background, fonts, buttons,
inputs, tabs, sidebar, cards) plus animations. `suggest_theme` reads the user's
own yaps and asks Groq which aesthetic matches their personality.

Adding a new aesthetic later is just one more entry in THEMES.
"""

from __future__ import annotations

import random

from . import config, patterns
from .storage import UserStore

# --- the aesthetics --------------------------------------------------------
# Each value carries: a display label, a Google-Fonts import URL, body/heading
# font stacks, background, translucent panel colour, text/accent colours, a
# button gradient, corner radius, button-text colour, floating decoration
# emoji, and whether the background gently animates.
THEMES: dict[str, dict] = {
    "bestie": {
        "label": "🌸 Bestie (GWY)",
        "fonts": "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
        "body_font": "'Poppins', sans-serif",
        "head_font": "'Poppins', sans-serif",
        "bg": "linear-gradient(165deg,#fff2f5 0%,#ffe6ee 55%,#ffeede 100%)",
        "panel": "rgba(255,255,255,0.86)",
        "text": "#3a2630",
        "muted": "#8a6b75",
        "primary": "#ff6f91",
        "primary_grad": "linear-gradient(135deg,#ffa9c5,#ff6f91)",
        "btn_text": "#ffffff",
        "radius": "20px",
        "decor": ["✿", "🌸", "💗", "🌷", "✨"],
        "animated_bg": False,
    },
    "ghibli": {
        "label": "🌿 Studio Ghibli",
        "fonts": "https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;700&display=swap",
        "body_font": "'Quicksand', sans-serif",
        "head_font": "'Quicksand', sans-serif",
        "bg": "linear-gradient(165deg,#cfeafe 0%,#e9f6e4 60%,#fdf6e3 100%)",
        "panel": "rgba(255,255,255,0.78)",
        "text": "#33474a",
        "muted": "#5b716b",
        "primary": "#5a9e6f",
        "primary_grad": "linear-gradient(135deg,#86cf97,#5a9e6f)",
        "btn_text": "#ffffff",
        "radius": "18px",
        "decor": ["☁️", "🍃", "🌿", "✨", "🌱"],
        "animated_bg": False,
    },
    "dark_academia": {
        "label": "📜 Dark Academia",
        "fonts": "https://fonts.googleapis.com/css2?family=EB+Garamond:ital@0;1&family=Playfair+Display:wght@600;700&display=swap",
        "body_font": "'EB Garamond', serif",
        "head_font": "'Playfair Display', serif",
        "bg": "linear-gradient(165deg,#241c14 0%,#3a2c1d 100%)",
        "panel": "rgba(60,46,32,0.55)",
        "text": "#ecdfca",
        "muted": "#b9a888",
        "primary": "#c8a25c",
        "primary_grad": "linear-gradient(135deg,#d8b873,#9c7836)",
        "btn_text": "#241c14",
        "radius": "7px",
        "decor": ["📜", "🕯️", "📚", "🖋️", "🦉", "☕"],
        "animated_bg": False,
    },
    "cottagecore": {
        "label": "🌻 Cottagecore",
        "fonts": "https://fonts.googleapis.com/css2?family=Caveat:wght@500;700&family=Nunito:wght@400;600;700&display=swap",
        "body_font": "'Nunito', sans-serif",
        "head_font": "'Caveat', cursive",
        "bg": "linear-gradient(165deg,#fbf3e0 0%,#eef1d8 60%,#e3ecd2 100%)",
        "panel": "rgba(255,250,238,0.82)",
        "text": "#5b4a36",
        "muted": "#7d6a4f",
        "primary": "#8a9a5b",
        "primary_grad": "linear-gradient(135deg,#a8b56e,#7c8a4a)",
        "btn_text": "#ffffff",
        "radius": "20px",
        "decor": ["🌻", "🍄", "🌿", "🐝", "🧺"],
        "animated_bg": False,
    },
    "y2k": {
        "label": "💿 Y2K",
        "fonts": "https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Rajdhani:wght@500;600&display=swap",
        "body_font": "'Rajdhani', sans-serif",
        "head_font": "'Orbitron', sans-serif",
        "bg": "linear-gradient(120deg,#ff5fd2,#5ce1e6,#c46bff,#ffd93b)",
        "panel": "rgba(255,255,255,0.22)",
        "text": "#1a1030",
        "muted": "#4a3a6a",
        "primary": "#ff2fb3",
        "primary_grad": "linear-gradient(135deg,#ff5fd2,#7b2ff7)",
        "btn_text": "#ffffff",
        "radius": "14px",
        "decor": ["💿", "✨", "🦋", "💖", "🌐"],
        "animated_bg": True,
    },
    "goth": {
        "label": "🦇 Goth",
        "fonts": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&display=swap",
        "body_font": "'Cormorant Garamond', serif",
        "head_font": "'Cormorant Garamond', serif",
        "bg": "linear-gradient(165deg,#0d0b10 0%,#1c0f1f 100%)",
        "panel": "rgba(30,20,34,0.6)",
        "text": "#d8cfe0",
        "muted": "#9a8aa6",
        "primary": "#9b3b6a",
        "primary_grad": "linear-gradient(135deg,#7d1128,#3a0a3e)",
        "btn_text": "#f0e6f0",
        "radius": "6px",
        "decor": ["🦇", "🥀", "🕷️", "🌙", "🖤"],
        "animated_bg": False,
    },
    "fairycore": {
        "label": "🧚 Fairycore",
        "fonts": "https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Quicksand:wght@400;600&display=swap",
        "body_font": "'Quicksand', sans-serif",
        "head_font": "'Dancing Script', cursive",
        "bg": "linear-gradient(135deg,#f6e6ff,#e6f0ff,#ffe6f4,#eafff4)",
        "panel": "rgba(255,255,255,0.62)",
        "text": "#4a3a5a",
        "muted": "#7a6a8a",
        "primary": "#b57edc",
        "primary_grad": "linear-gradient(135deg,#c8a2ff,#ff9ed6)",
        "btn_text": "#ffffff",
        "radius": "22px",
        "decor": ["🧚", "✨", "🌸", "🍄", "🦋"],
        "animated_bg": True,
    },
}

DEFAULT_THEME = "bestie"


# --- CSS generation --------------------------------------------------------
def build_css(t: dict) -> str:
    """Return a <style> block that restyles the whole app for theme `t`."""
    bg_anim = (
        "background-size:300% 300%;animation:gradientshift 22s ease infinite;"
        if t.get("animated_bg")
        else ""
    )
    return f"""
<style>
@import url('{t["fonts"]}');

[data-testid="stAppViewContainer"], [data-testid="stApp"] {{
  background: {t["bg"]};
  {bg_anim}
}}
[data-testid="stHeader"] {{ background: transparent; }}

.block-container {{
  font-family: {t["body_font"]};
  color: {t["text"]};
  position: relative;
  z-index: 1;
  animation: fadein .6s ease both;
  max-width: 820px;
  padding-top: 2.2rem;
  line-height: 1.6;
}}
/* generous, doradao-style breathing room between widgets */
.block-container [data-testid="stVerticalBlock"] {{ gap: 1.05rem; }}
.block-container p, .block-container li, .block-container label,
[data-testid="stMarkdownContainer"], .stCaption, small {{
  font-family: {t["body_font"]};
  color: {t["text"]};
}}
h1, h2, h3, h4 {{
  font-family: {t["head_font"]} !important;
  color: {t["text"]} !important;
  letter-spacing: .3px;
}}

[data-testid="stSidebar"] {{
  background: {t["panel"]};
  backdrop-filter: blur(10px);
}}
[data-testid="stSidebar"] * {{ color: {t["text"]}; }}

.stButton > button, [data-testid="stDownloadButton"] button {{
  background: {t["primary_grad"]};
  color: {t["btn_text"]} !important;
  border: none;
  border-radius: {t["radius"]};
  font-family: {t["body_font"]};
  font-weight: 600;
  padding: .55rem 1.15rem;
  transition: transform .15s ease, box-shadow .15s ease;
  box-shadow: 0 4px 14px rgba(0,0,0,.18);
}}
.stButton > button:hover, [data-testid="stDownloadButton"] button:hover {{
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 9px 24px rgba(0,0,0,.26);
}}

.stTextInput input, .stTextArea textarea,
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="base-input"],
[data-baseweb="select"] > div {{
  background: {t["panel"]} !important;
  border-radius: {t["radius"]} !important;
  color: {t["text"]} !important;
  font-family: {t["body_font"]} !important;
  border: 1px solid rgba(125,125,125,.25) !important;
}}

[data-baseweb="tab-list"] {{ gap: 4px; }}
[data-baseweb="tab"] {{ font-family: {t["body_font"]}; color: {t["muted"]}; }}
[data-baseweb="tab"][aria-selected="true"] {{ color: {t["primary"]}; }}
[data-baseweb="tab-highlight"] {{ background: {t["primary"]} !important; }}

[data-testid="stMetric"] {{
  background: {t["panel"]};
  border-radius: {t["radius"]};
  padding: 14px 16px;
  box-shadow: 0 3px 12px rgba(0,0,0,.10);
}}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{ color: {t["text"]}; }}

/* expander: the wrapper, the <details>, AND the <summary> header all need the
   panel colour, otherwise the header keeps the dark base-theme background */
[data-testid="stExpander"], [data-testid="stExpander"] details,
[data-testid="stExpander"] summary, [data-testid="stAlert"] {{
  border-radius: {t["radius"]} !important;
  background: {t["panel"]} !important;
}}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p {{
  color: {t["text"]} !important;
}}
[data-testid="stExpander"] summary svg {{ fill: {t["text"]} !important; }}

/* file uploader dropzone + its Browse button were dark by default */
[data-testid="stFileUploaderDropzone"], [data-testid="stFileUploader"] section {{
  background: {t["panel"]} !important;
  border-radius: {t["radius"]} !important;
}}
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] {{
  background: {t["primary_grad"]} !important;
  color: {t["btn_text"]} !important;
  border: none !important;
}}
/* the chip shown after a file is selected (was a dark pill) */
[data-testid="stFileChips"], [data-testid="stFileChip"] {{
  background: {t["panel"]} !important;
  border-radius: {t["radius"]} !important;
}}
[data-testid="stFileChip"], [data-testid="stFileChip"] *, [data-testid="stFileChipName"] {{
  color: {t["text"]} !important;
}}
[data-testid="stFileChip"] svg {{ fill: {t["text"]} !important; }}

/* voice recorder widget */
[data-testid="stAudioInput"], [data-testid="stExpanderDetails"] {{
  background: {t["panel"]} !important;
  border-radius: {t["radius"]} !important;
}}

/* --- robust text contrast --------------------------------------------------
   Streamlit's base theme (light or dark) otherwise leaves widget labels in a
   default colour that can vanish on a light theme. Force the theme's own text
   colour onto every text-bearing widget, and theme the dropdown popovers that
   render in a portal outside the styled container. */
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *,
.stRadio label, .stRadio div, .stCheckbox label, .stSlider label,
[data-testid="stExpander"] summary, details summary, details summary *,
[data-testid="stFileUploaderDropzone"] *,
[data-baseweb="select"] div, [data-baseweb="select"] span {{
  color: {t["text"]} !important;
}}
input::placeholder, textarea::placeholder {{
  color: {t["muted"]} !important; opacity: .85;
}}

/* dropdown / select menus render in a portal outside the themed container */
ul[role="listbox"], [data-baseweb="menu"], [data-baseweb="popover"] li {{
  background: {t["panel"]} !important;
}}
[role="option"], ul[role="listbox"] * {{ color: {t["text"]} !important; }}

/* category pills (Streamlit renders these as a button group) ----------------
   Container is stButtonGroup; buttons are stBaseButton-pills /
   stBaseButton-pillsActive (NOT stPills). Unselected get the light panel,
   the selected one gets the accent. */
[data-testid="stButtonGroup"] button,
[data-testid^="stBaseButton-pills"] {{
  background: {t["panel"]} !important;
  border: 1px solid {t["muted"]} !important;
}}
[data-testid="stButtonGroup"] button,
[data-testid="stButtonGroup"] button p,
[data-testid^="stBaseButton-pills"],
[data-testid^="stBaseButton-pills"] p {{
  color: {t["text"]} !important;
}}
[data-testid="stBaseButton-pillsActive"] {{
  background: {t["primary"]} !important;
  border-color: {t["primary"]} !important;
}}
[data-testid="stBaseButton-pillsActive"],
[data-testid="stBaseButton-pillsActive"] p {{
  color: {t["btn_text"]} !important;
}}

.yap-hero {{
  background: {t["primary_grad"]};
  color: {t["btn_text"]};
  border-radius: {t["radius"]};
  padding: 22px 26px;
  margin: 4px 0 22px;
  box-shadow: 0 8px 24px rgba(0,0,0,.20);
  animation: fadein .6s ease both;
}}
.yap-hero h1 {{ color: {t["btn_text"]} !important; margin: 0; font-size: 2.1rem; }}
.yap-hero p {{ color: {t["btn_text"]}; opacity: .92; margin: .35rem 0 0; font-family: {t["body_font"]}; }}

.yap-callout {{
  background: {t["panel"]};
  border-left: 4px solid {t["primary"]};
  border-radius: {t["radius"]};
  padding: 14px 18px;
  margin: 4px 0 16px;
  font-family: {t["body_font"]};
  color: {t["text"]};
}}
.yap-callout b {{ color: {t["primary"]}; }}

.yap-section {{
  font-family: {t["head_font"]};
  color: {t["text"]};
  font-size: 1.25rem;
  margin: 6px 0 2px;
}}

@keyframes fadein {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:none; }} }}
@keyframes gradientshift {{ 0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}} }}
@keyframes floaty {{ 0%{{transform:translateY(0)}} 50%{{transform:translateY(-24px)}} 100%{{transform:translateY(0)}} }}

.yap-decor {{ position:fixed; inset:0; pointer-events:none; z-index:-1; overflow:hidden; }}
.yap-decor span {{ position:absolute; opacity:.38; animation: floaty 7s ease-in-out infinite; }}
</style>
"""


def style_plotly(fig, t: dict):
    """Make a Plotly figure blend with the active theme: transparent canvas,
    theme-coloured text and axes (otherwise charts keep a black background)."""
    grid = "rgba(125,125,125,0.18)"
    fig.update_layout(
        paper_bgcolor=t["panel"],      # sit on a themed card, like the metrics
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=t["text"],
        font_family=t["body_font"].split(",")[0].strip("'\""),
        title_font_color=t["text"],
        legend_font_color=t["text"],
        margin=dict(t=56, l=14, r=20, b=44),
    )
    # automargin so y-axis category labels are never clipped
    fig.update_xaxes(color=t["text"], gridcolor=grid, zerolinecolor=grid, automargin=True)
    fig.update_yaxes(color=t["text"], gridcolor=grid, zerolinecolor=grid, automargin=True)
    return fig


def decor_html(t: dict, theme_key: str = "") -> str:
    """A field of gently floating emoji, positioned deterministically per theme
    so they stay put across reruns instead of jumping around."""
    emojis = t.get("decor", [])
    if not emojis:
        return ""
    rng = random.Random(theme_key or t.get("label", ""))
    spans = []
    for _ in range(12):
        e = rng.choice(emojis)
        left = rng.randint(2, 94)
        top = rng.randint(4, 92)
        delay = round(rng.uniform(0, 6), 1)
        size = round(rng.uniform(1.3, 2.7), 1)
        spans.append(
            f'<span style="left:{left}%;top:{top}%;'
            f'animation-delay:{delay}s;font-size:{size}rem">{e}</span>'
        )
    return '<div class="yap-decor">' + "".join(spans) + "</div>"


# --- personality-matched theme suggestion ----------------------------------
def suggest_theme(store: UserStore, days: int = 120, n: int = 12) -> str:
    """Ask Groq which aesthetic best matches the user's recent yaps. Falls back
    to the default theme when there's nothing written or no API key."""
    chunks = [
        c for c in patterns.recent_chunks(store, days)
        if c.get("type") == "yap_entry"
    ]
    if not chunks or not config.GROQ_API_KEY:
        return DEFAULT_THEME

    blob = "\n".join(f"- {c['text']}" for c in chunks[-n:])
    keys = ", ".join(THEMES.keys())
    sys = (
        "You match a person to a visual aesthetic based on how they write and "
        f"what they care about. Choose EXACTLY ONE key from this list: {keys}. "
        "Reply with only the key, nothing else."
    )

    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": f"My recent journal entries:\n\n{blob}"},
        ],
        temperature=0.3,
    )
    pick = resp.choices[0].message.content.strip().lower()
    for key in THEMES:
        if key in pick:
            return key
    return DEFAULT_THEME
