"""Visual themes.

Each theme is a small set of design tokens; `build_css` turns those tokens into
a block of CSS that restyles the whole Streamlit app (background, fonts, buttons,
inputs, tabs, sidebar, cards). `backdrop_html` adds the theme's background layer
(paper grain or a slow aurora). `suggest_theme` reads the user's own entries and
asks Groq which theme suits them.
"""

from __future__ import annotations

from . import config, patterns
from .storage import UserStore

_INTER = "'Inter', system-ui, -apple-system, sans-serif"

# Each value carries: a display label, a Google Fonts URL, body / heading /
# writing font stacks, background, card and input colours, border, text colours, the
# accent, the primary button fill and its text colour, corner radius, and the
# background effect ("grain", "aurora" or None).
THEMES: dict[str, dict] = {
    "paper": {
        "label": "Paper",
        "fonts": "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&family=Newsreader:ital,opsz@0,6..72;1,6..72&display=swap",
        "body_font": _INTER,
        "head_font": "'Fraunces', Georgia, serif",
        "write_font": "'Newsreader', Georgia, serif",
        "bg": "#f4efe6",
        "panel": "#fbf8f2",
        "field": "#fbf8f2",
        "border": "#e2d9c8",
        "text": "#1f1b16",
        "muted": "#7a6f62",
        "primary": "#9a3b26",
        "button": "#1f1b16",
        "btn_text": "#fbf8f2",
        "radius": "6px",
        "effect": "grain",
    },
    "aurora": {
        "label": "Aurora",
        "fonts": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        "body_font": _INTER,
        "head_font": _INTER,
        "write_font": _INTER,
        "bg": "#0a0e1a",
        "panel": "rgba(255,255,255,0.05)",
        "field": "#121829",
        "border": "rgba(255,255,255,0.10)",
        "text": "#e7eaf3",
        "muted": "#8f97ab",
        "primary": "#8ea2ff",
        "button": "linear-gradient(135deg,#8ea2ff,#5fd4c4)",
        "btn_text": "#0a0e1a",
        "radius": "12px",
        "effect": "aurora",
    },
    "minimal": {
        "label": "Minimal",
        "fonts": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        "body_font": _INTER,
        "head_font": _INTER,
        "write_font": _INTER,
        "bg": "#ffffff",
        "panel": "#ffffff",
        "field": "#ffffff",
        "border": "#e6e6e6",
        "text": "#141414",
        "muted": "#6b6b6b",
        "primary": "#2f5bea",
        "button": "#141414",
        "btn_text": "#ffffff",
        "radius": "8px",
        "effect": None,
    },
}

DEFAULT_THEME = "paper"

# Fine paper texture: SVG fractal noise, tiled and blended over the background.
_GRAIN = (
    "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' "
    "width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' "
    "baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/></filter>"
    "<rect width='100%' height='100%' filter='url(%23n)' opacity='.55'/></svg>\")"
)


# --- CSS generation --------------------------------------------------------
def build_css(t: dict) -> str:
    """Return a <style> block that restyles the whole app for theme `t`."""
    head_weight = 600 if "Fraunces" in t["head_font"] else 700
    return f"""
<style>
@import url('{t["fonts"]}');

[data-testid="stAppViewContainer"], [data-testid="stApp"] {{
  background: {t["bg"]};
}}
[data-testid="stHeader"] {{ background: transparent; }}

.block-container {{
  font-family: {t["body_font"]};
  color: {t["text"]};
  position: relative;
  z-index: 1;
  max-width: 760px;
  padding-top: 3rem;
  line-height: 1.6;
}}
/* children rise in one after another on first paint */
.block-container > div > [data-testid="stVerticalBlock"] > div {{
  animation: rise .7s cubic-bezier(.2,.7,.2,1) both;
}}
.block-container > div > [data-testid="stVerticalBlock"] > div:nth-child(2) {{ animation-delay: .06s; }}
.block-container > div > [data-testid="stVerticalBlock"] > div:nth-child(3) {{ animation-delay: .12s; }}
.block-container > div > [data-testid="stVerticalBlock"] > div:nth-child(n+4) {{ animation-delay: .18s; }}

.block-container [data-testid="stVerticalBlock"] {{ gap: 1rem; }}
.block-container p, .block-container li, .block-container label,
[data-testid="stMarkdownContainer"], .stCaption, small {{
  font-family: {t["body_font"]};
  color: {t["text"]};
}}
h1, h2, h3, h4 {{
  font-family: {t["head_font"]} !important;
  font-weight: {head_weight} !important;
  color: {t["text"]} !important;
  letter-spacing: -.01em;
}}

[data-testid="stSidebar"] {{
  background: {t["panel"]};
  border-right: 1px solid {t["border"]};
  backdrop-filter: blur(14px);
}}
[data-testid="stSidebar"] * {{ color: {t["text"]}; }}

/* buttons: primary is filled, everything else is a quiet outline */
.stButton > button, [data-testid="stDownloadButton"] button,
[data-testid="stLinkButton"] a {{
  background: transparent;
  color: {t["text"]} !important;
  border: 1px solid {t["border"]};
  border-radius: {t["radius"]};
  font-family: {t["body_font"]};
  font-weight: 500;
  padding: .5rem 1.1rem;
  transition: background .15s ease, border-color .15s ease, transform .15s ease;
}}
.stButton > button:hover, [data-testid="stDownloadButton"] button:hover,
[data-testid="stLinkButton"] a:hover {{
  border-color: {t["text"]};
  transform: translateY(-1px);
}}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"],
[data-testid="stDownloadButton"] button {{
  background: {t["button"]} !important;
  color: {t["btn_text"]} !important;
  border: none !important;
}}
.stButton > button[kind="primary"] p, [data-testid="stBaseButton-primary"] p,
[data-testid="stDownloadButton"] button p {{ color: {t["btn_text"]} !important; }}

[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="base-input"],
[data-baseweb="select"] > div, [data-testid$="RootElement"],
.react-aria-ComboBox [role="group"] {{
  background: {t["field"]} !important;
  border-radius: {t["radius"]} !important;
  border-color: {t["border"]} !important;
}}
/* the inner elements keep the base theme's fill unless cleared */
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div *,
.react-aria-ComboBox input, .react-aria-ComboBox button {{
  background: transparent !important;
  color: {t["text"]} !important;
  font-family: {t["body_font"]} !important;
}}
/* the journal box itself is set in the writing face, a little larger */
.stTextArea textarea {{
  font-family: {t["write_font"]} !important;
  font-size: 1.08rem !important;
  line-height: 1.7 !important;
}}

/* tabs: older Streamlit uses baseweb, newer uses react-aria (stTab) */
[data-baseweb="tab-list"], [role="tablist"] {{ gap: 1.4rem; border-bottom: 1px solid {t["border"]}; }}
[data-baseweb="tab"], [data-testid="stTab"] {{
  background: transparent !important; padding-left: 0; padding-right: 0;
}}
[data-baseweb="tab"], [data-baseweb="tab"] p,
[data-testid="stTab"], [data-testid="stTab"] p {{
  font-family: {t["body_font"]}; color: {t["muted"]} !important;
}}
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] p {{
  color: {t["text"]} !important;
}}
[data-baseweb="tab-highlight"], .react-aria-SelectionIndicator {{
  background: {t["primary"]} !important; height: 2px;
}}
[data-baseweb="tab-border"] {{ display: none; }}

[data-testid="stMetric"] {{
  background: {t["panel"]};
  border: 1px solid {t["border"]};
  border-radius: {t["radius"]};
  padding: 14px 16px;
}}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {{
  color: {t["text"]}; font-family: {t["head_font"]} !important;
}}
[data-testid="stMetricLabel"] {{ color: {t["muted"]}; }}

/* expander: the wrapper, the <details> and the <summary> all need the panel
   colour, otherwise the header keeps the base-theme background */
[data-testid="stExpander"], [data-testid="stExpander"] details,
[data-testid="stExpander"] summary, [data-testid="stAlert"] {{
  border-radius: {t["radius"]} !important;
  background: {t["panel"]} !important;
}}
[data-testid="stExpander"] details {{ border-color: {t["border"]} !important; }}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p {{
  color: {t["text"]} !important;
}}
[data-testid="stExpander"] summary svg {{ fill: {t["text"]} !important; }}

[data-testid="stVerticalBlockBorderWrapper"] {{
  border-color: {t["border"]} !important;
  background: {t["panel"]};
  border-radius: {t["radius"]} !important;
}}

[data-testid="stFileUploaderDropzone"], [data-testid="stFileUploader"] section {{
  background: {t["panel"]} !important;
  border-radius: {t["radius"]} !important;
}}
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] {{
  background: transparent !important;
  color: {t["text"]} !important;
  border: 1px solid {t["border"]} !important;
}}
[data-testid="stFileChips"], [data-testid="stFileChip"] {{
  background: {t["panel"]} !important;
  border-radius: {t["radius"]} !important;
}}
[data-testid="stFileChip"], [data-testid="stFileChip"] *, [data-testid="stFileChipName"] {{
  color: {t["text"]} !important;
}}
[data-testid="stFileChip"] svg {{ fill: {t["text"]} !important; }}

[data-testid="stAudioInput"], [data-testid="stExpanderDetails"] {{
  background: {t["panel"]} !important;
  border-radius: {t["radius"]} !important;
}}

/* --- text contrast ---------------------------------------------------------
   Streamlit's base theme leaves some widget labels in a default colour that
   can vanish on a dark theme. Force the theme's text colour onto every
   text-bearing widget, and theme the dropdowns that render in a portal. */
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
.stRadio label, .stRadio div, .stCheckbox label, .stSlider label,
[data-testid="stExpander"] summary, details summary, details summary *,
[data-testid="stFileUploaderDropzone"] *,
[data-baseweb="select"] div, [data-baseweb="select"] span {{
  color: {t["text"]} !important;
}}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{
  color: {t["muted"]} !important;
}}
input::placeholder, textarea::placeholder {{
  color: {t["muted"]} !important; opacity: .8;
}}

[role="listbox"], div:has(> [role="listbox"]),
[data-baseweb="menu"], [data-baseweb="popover"] li {{
  background: {t["field"]} !important;
}}
[role="option"][data-focused], [role="option"]:hover {{
  background: rgba(125,125,125,.16) !important;
}}
[role="option"], [role="listbox"] * {{ color: {t["text"]} !important; }}

/* category pills: container is stButtonGroup, buttons are
   stBaseButton-pills / stBaseButton-pillsActive */
[data-testid="stButtonGroup"] button,
[data-testid^="stBaseButton-pills"] {{
  background: transparent !important;
  border: 1px solid {t["border"]} !important;
}}
[data-testid="stButtonGroup"] button,
[data-testid="stButtonGroup"] button p,
[data-testid^="stBaseButton-pills"],
[data-testid^="stBaseButton-pills"] p {{
  color: {t["muted"]} !important;
}}
[data-testid="stBaseButton-pillsActive"],
[data-testid="stButtonGroup"] button[aria-checked="true"] {{
  background: {t["text"]} !important;
  border-color: {t["text"]} !important;
}}
[data-testid="stBaseButton-pillsActive"],
[data-testid="stBaseButton-pillsActive"] p,
[data-testid="stButtonGroup"] button[aria-checked="true"],
[data-testid="stButtonGroup"] button[aria-checked="true"] p {{
  color: {t["bg"]} !important;
}}

/* page header: eyebrow, large greeting, quiet meta line */
.yap-hero {{ margin: 0 0 1.6rem; }}
.yap-eyebrow {{
  font-family: {t["body_font"]};
  font-size: .72rem; font-weight: 600;
  letter-spacing: .18em; text-transform: uppercase;
  color: {t["primary"]};
}}
.yap-hero h1 {{
  font-size: 2.6rem; line-height: 1.1; margin: .35rem 0 .4rem; padding: 0;
}}
.yap-hero p {{ color: {t["muted"]}; margin: 0; }}

.yap-callout {{
  border-left: 2px solid {t["primary"]};
  padding: 6px 0 6px 16px;
  margin: 4px 0 12px;
  font-family: {t["write_font"]};
  font-size: 1.08rem;
  font-style: italic;
  color: {t["text"]};
}}

.yap-section {{
  font-family: {t["head_font"]};
  font-weight: {head_weight};
  color: {t["text"]};
  font-size: 1.35rem;
  margin: 6px 0 2px;
}}

blockquote {{
  border-left: 2px solid {t["primary"]} !important;
  font-family: {t["write_font"]};
  font-size: 1.1rem;
}}

/* background layers */
.yap-backdrop {{ position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }}
.yap-grain {{ background-image: {_GRAIN}; mix-blend-mode: multiply; opacity: .35; }}
.yap-blob {{
  position: absolute; width: 46vmax; height: 46vmax; border-radius: 50%;
  filter: blur(90px); opacity: .32;
  animation: drift 28s ease-in-out infinite alternate;
}}
.yap-blob.b1 {{ background: #5b6cff; top: -18%; left: -12%; }}
.yap-blob.b2 {{ background: #2fc4b2; bottom: -22%; right: -14%; animation-duration: 34s; }}
.yap-blob.b3 {{ background: #a35bff; top: 30%; left: 40%; opacity: .18; animation-duration: 40s; }}

@keyframes rise {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes drift {{
  0%   {{ transform: translate(0, 0) scale(1); }}
  50%  {{ transform: translate(8vw, 6vh) scale(1.12); }}
  100% {{ transform: translate(-6vw, 10vh) scale(.94); }}
}}
@media (prefers-reduced-motion: reduce) {{
  .block-container > div > [data-testid="stVerticalBlock"] > div, .yap-blob {{ animation: none; }}
}}
</style>
"""


def style_plotly(fig, t: dict):
    """Make a Plotly figure blend with the active theme: transparent canvas,
    theme-coloured text and axes (otherwise charts keep a black background)."""
    grid = "rgba(125,125,125,0.18)"
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=t["text"],
        font_family=t["body_font"].split(",")[0].strip("'\""),
        title_font_color=t["text"],
        legend_font_color=t["text"],
        colorway=[t["primary"], t["muted"], "#c9a227", "#4f7c6a", "#6b5ca5", "#b0846a"],
        margin=dict(t=56, l=14, r=20, b=44),
    )
    # automargin so y-axis category labels are never clipped
    fig.update_xaxes(color=t["text"], gridcolor=grid, zerolinecolor=grid, automargin=True)
    fig.update_yaxes(color=t["text"], gridcolor=grid, zerolinecolor=grid, automargin=True)
    return fig


def backdrop_html(t: dict) -> str:
    """The fixed layer behind the content: paper grain or drifting aurora."""
    if t.get("effect") == "grain":
        return '<div class="yap-backdrop yap-grain"></div>'
    if t.get("effect") == "aurora":
        return (
            '<div class="yap-backdrop"><div class="yap-blob b1"></div>'
            '<div class="yap-blob b2"></div><div class="yap-blob b3"></div></div>'
        )
    return ""


# --- theme suggestion ------------------------------------------------------
def suggest_theme(store: UserStore, days: int = 120, n: int = 12) -> str:
    """Ask Groq which theme best suits the user's recent entries. Falls back
    to the default theme when there's nothing written or no API key."""
    chunks = [
        c for c in patterns.recent_chunks(store, days)
        if c.get("type") == "yap_entry"
    ]
    if not chunks or not config.GROQ_API_KEY:
        return DEFAULT_THEME

    blob = "\n".join(f"- {c['text']}" for c in chunks[-n:])
    sys = (
        "You match a person to a visual theme based on how they write. "
        "paper = warm, reflective, literary. aurora = dark, dreamy, night-owl. "
        "minimal = direct, practical, to the point. "
        "Reply with exactly one key: paper, aurora or minimal."
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
