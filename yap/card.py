"""Render a shareable 'Personality Wrapped' card as a PNG.

Built from the clean structured stats (not the markdown recap), so it always
lays out tidily. Styled to match the default "paper" theme.
"""

from __future__ import annotations

import io
import re

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1080
PAPER = (244, 239, 230)
INK = (31, 27, 22)
MUTED = (122, 111, 98)
ACCENT = (154, 59, 38)

# Default PIL/truetype fonts can't render emoji — strip them from drawn text.
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF️]"
)


def _strip_emoji(s: str) -> str:
    return _EMOJI.sub("", s).strip()


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = (["arialbd.ttf"] if bold else ["arial.ttf"]) + ["DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    # Slim Docker images ship no TrueType fonts; Pillow's built-in one scales.
    return ImageFont.load_default(size)


def render_card(wrapped: dict, username: str) -> bytes:
    """Return PNG bytes for a square, shareable Wrapped card."""
    stats = wrapped.get("stats", {})
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, W - 40, H - 40], outline=INK, width=2)

    period = str(stats.get("period", "month")).title()
    name = _strip_emoji(username.split("@")[0]) or "you"

    def center(text: str, y: int, font: ImageFont.FreeTypeFont, fill=INK) -> None:
        w = d.textlength(text, font=font)
        d.text(((W - w) / 2, y), text, font=font, fill=fill)

    center("YAP", 90, _font(34, bold=True), ACCENT)
    center(f"My {period} Wrapped", 165, _font(64, bold=True))
    center(f"@{name}", 255, _font(36), MUTED)

    center(str(stats.get("entries", 0)), 340, _font(180, bold=True))
    center("entries written", 545, _font(40), MUTED)

    top_cat = _strip_emoji(stats.get("top_category") or "") or "—"
    center("TOP CATEGORY", 655, _font(30), ACCENT)
    center(top_cat, 695, _font(56, bold=True))

    kws = [_strip_emoji(k) for k, _ in (stats.get("keywords") or [])[:5]]
    kws = [k for k in kws if k]
    center("TOP THEMES", 805, _font(30), ACCENT)
    center(" · ".join(kws) if kws else "—", 850, _font(40, bold=True))

    center("made with Yap", H - 110, _font(28), MUTED)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
