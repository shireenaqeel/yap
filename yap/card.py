"""Render a shareable 'Personality Wrapped' card as a PNG.

Built from the clean structured stats (not the markdown recap), so it always
lays out tidily and on-brand. This is the screenshot people post — it's what
makes Yap spread.
"""

from __future__ import annotations

import io
import re

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1080
TOP = (108, 43, 217)   # purple
BOT = (219, 39, 119)   # pink
WHITE = (255, 255, 255)

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
    return ImageFont.load_default()


def _gradient() -> Image.Image:
    img = Image.new("RGB", (W, H), TOP)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line(
            [(0, y), (W, y)],
            fill=(
                int(TOP[0] + (BOT[0] - TOP[0]) * t),
                int(TOP[1] + (BOT[1] - TOP[1]) * t),
                int(TOP[2] + (BOT[2] - TOP[2]) * t),
            ),
        )
    return img


def render_card(wrapped: dict, username: str) -> bytes:
    """Return PNG bytes for a square, shareable Wrapped card."""
    stats = wrapped.get("stats", {})
    img = _gradient()
    d = ImageDraw.Draw(img)

    period = str(stats.get("period", "month")).title()
    name = _strip_emoji(username.split("@")[0]) or "you"

    def center(text: str, y: int, font: ImageFont.FreeTypeFont) -> None:
        w = d.textlength(text, font=font)
        d.text(((W - w) / 2, y), text, font=font, fill=WHITE)

    center("YAP", 80, _font(54, bold=True))
    center(f"My {period} Wrapped", 165, _font(64, bold=True))
    center(f"@{name}", 255, _font(36))

    center(str(stats.get("entries", 0)), 340, _font(180, bold=True))
    center("yaps written", 545, _font(40))

    top_cat = _strip_emoji(stats.get("top_category") or "") or "—"
    center("TOP CATEGORY", 655, _font(30))
    center(top_cat, 695, _font(56, bold=True))

    kws = [_strip_emoji(k) for k, _ in (stats.get("keywords") or [])[:5]]
    kws = [k for k in kws if k]
    center("TOP THEMES", 805, _font(30))
    center(" · ".join(kws) if kws else "—", 850, _font(40, bold=True))

    center("made with Yap", H - 80, _font(30))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
