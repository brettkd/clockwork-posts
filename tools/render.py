#!/usr/bin/env python3
"""Render Clockwork Lifestyle post images (1080x1350) from a content JSON file.

Usage: python3 tools/render.py content/2026-11.json [--only POST_ID]

Each post in the JSON has: id, date (YYYY-MM-DD), type ("quote" | "countdown" | "carousel"),
pillar, caption, alt, and type-specific fields:
  quote:     text (use [[word]] to mark the single brass highlight), sub (optional)
  countdown: target ("2026-12-31"), label, line (optional, [[...]] = brass)
  carousel:  slides: list of {kind: "cover"|"step"|"close", title, body, n}
Output: posts/<id>.png for single images, posts/<id>-01.png ... for carousels.
"""
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "posts"
LOGO = ROOT / "assets" / "logo.png"  # optional; wordmark is used when absent

INK = "#0B0B0B"
PAPER = "#F2EFE8"
BRASS = "#B08D57"


def hl(text: str) -> str:
    """Escape text, turn [[word]] into the brass highlight and \n into line breaks."""
    t = html.escape(text)
    t = re.sub(r"\[\[(.+?)\]\]", r'<span class="brass">\1</span>', t)
    if "\n" in t:
        # Explicit line breaks are intentional: keep each line on one line (auto-fit shrinks the font).
        return "".join(f'<span class="ln">{ln}</span>' for ln in t.split("\n"))
    return t


def dial(color: str) -> str:
    """Watch-dial tick row used as the header ornament."""
    ticks = []
    for i in range(13):
        h = 22 if i % 3 == 0 else 11
        ticks.append(f'<i style="height:{h}px"></i>')
    return f'<div class="dial" style="--c:{color}">{"".join(ticks)}</div>'


def footer(color: str) -> str:
    if LOGO.exists():
        mark = f'<img class="logo" src="{LOGO.as_uri()}">'
    else:
        mark = '<span class="word">CLOCKWORK&nbsp;LIFESTYLE</span>'
    return f'<div class="foot" style="color:{color}">{mark}</div>'


BASE_CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:1080px; height:1350px; }}
body {{ font-family:'Inter Display','Inter',sans-serif; -webkit-font-smoothing:antialiased;
        font-feature-settings:'tnum' 1, 'ss01' 1; }}
.card {{ position:relative; width:1080px; height:1350px; padding:132px 128px; overflow:hidden; }}
.dark {{ background:{INK}; color:{PAPER}; }}
.light {{ background:{PAPER}; color:{INK}; }}
.dark::after {{ content:''; position:absolute; inset:0; pointer-events:none;
  background: radial-gradient(ellipse at 50% 35%, rgba(255,255,255,0.045), transparent 60%); }}
.brass {{ color:{BRASS}; }}
.ln {{ display:block; white-space:nowrap; }}
.quote, .steptitle, .line, .sub, .stepbody {{ text-wrap:balance; }}
.numlabel {{ opacity:0.6; }}
.top {{ display:flex; justify-content:space-between; align-items:flex-start;
        font-family:'Inter'; font-weight:500; font-size:22px; letter-spacing:0.22em;
        text-transform:uppercase; opacity:0.55; }}
.dial {{ display:flex; gap:14px; align-items:flex-start; }}
.dial i {{ display:block; width:2px; background:var(--c); }}
.foot {{ position:absolute; left:0; right:0; bottom:96px; display:flex; justify-content:center;
         font-family:'Inter'; font-weight:600; font-size:20px; letter-spacing:0.42em; opacity:0.6; }}
.logo {{ height:56px; }}
.mid {{ position:absolute; left:128px; right:128px; top:50%; transform:translateY(-50%); }}
.quote {{ font-weight:600; font-size:92px; line-height:1.06; letter-spacing:-0.025em; }}
.quote.long {{ font-size:76px; }}
.sub {{ margin-top:44px; font-family:'Inter'; font-weight:400; font-size:34px; line-height:1.4;
        opacity:0.7; max-width:760px; }}
.num {{ font-weight:300; font-size:400px; line-height:0.86; letter-spacing:-0.05em; }}
.numlabel {{ margin-top:36px; font-family:'Inter'; font-weight:500; font-size:30px;
             letter-spacing:0.3em; text-transform:uppercase; }}
.line {{ margin-top:72px; font-weight:600; font-size:56px; line-height:1.12; letter-spacing:-0.02em;
         max-width:780px; }}
.stepn {{ font-family:'Inter'; font-weight:300; font-size:150px; line-height:1; letter-spacing:-0.04em;
          opacity:0.22; margin-bottom:40px; }}
.steptitle {{ font-weight:600; font-size:74px; line-height:1.06; letter-spacing:-0.025em; }}
.stepbody {{ margin-top:40px; font-family:'Inter'; font-weight:400; font-size:36px; line-height:1.45;
             opacity:0.78; max-width:800px; }}
.swipe {{ position:absolute; right:128px; bottom:96px; font-family:'Inter'; font-weight:500;
          font-size:20px; letter-spacing:0.3em; opacity:0.5; }}
"""


def page(body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE_CSS}</style></head><body>{body}</body></html>"


def quote_card(p: dict) -> list[str]:
    cls = "quote long" if len(p["text"]) > 70 else "quote"
    sub = f'<div class="sub">{hl(p["sub"])}</div>' if p.get("sub") else ""
    body = f"""<div class="card dark">
      <div class="top">{dial(PAPER)}<span>{html.escape(p['pillar'])}</span></div>
      <div class="mid"><div class="{cls}">{hl(p['text'])}</div>{sub}</div>
      {footer(PAPER)}</div>"""
    return [page(body)]


def countdown_card(p: dict) -> list[str]:
    d = dt.date.fromisoformat(p["date"])
    target = dt.date.fromisoformat(p.get("target", f"{d.year}-12-31"))
    days = (target - d).days
    p["computed_days"] = days
    line = f'<div class="line">{hl(p["line"])}</div>' if p.get("line") else ""
    label = p.get("label", f"days left in {target.year}")
    body = f"""<div class="card dark">
      <div class="top">{dial(PAPER)}<span>{html.escape(p['pillar'])}</span></div>
      <div class="mid"><div class="num">{days}</div>
        <div class="numlabel">{html.escape(label)}</div>{line}</div>
      {footer(PAPER)}</div>"""
    return [page(body)]


def carousel(p: dict) -> list[str]:
    pages = []
    total = len(p["slides"])
    for i, s in enumerate(p["slides"], 1):
        theme = "dark" if s["kind"] in ("cover", "close") else "light"
        fg = PAPER if theme == "dark" else INK
        counter = f"{i:02d} / {total:02d}"
        if s["kind"] == "step":
            inner = f"""<div class="stepn">{s['n']:02d}</div>
              <div class="steptitle">{hl(s['title'])}</div>
              <div class="stepbody">{hl(s['body'])}</div>"""
        else:
            sub = f'<div class="sub">{hl(s["body"])}</div>' if s.get("body") else ""
            inner = f'<div class="quote">{hl(s["title"])}</div>{sub}'
        swipe = '<div class="swipe">SWIPE &rarr;</div>' if s["kind"] == "cover" else ""
        body = f"""<div class="card {theme}">
          <div class="top">{dial(fg)}<span>{counter}</span></div>
          <div class="mid">{inner}</div>{swipe}{footer(fg)}</div>"""
        pages.append(page(body))
    return pages


# Shrink any text block whose no-wrap lines overflow the safe area (min 52px).
FIT_JS = """
() => {
  for (const el of document.querySelectorAll('.quote, .steptitle, .line, .sub, .stepbody')) {
    if (!el.querySelector('.ln')) continue;
    let size = parseFloat(getComputedStyle(el).fontSize);
    const max = el.parentElement.clientWidth;
    while (size > 52 && [...el.querySelectorAll('.ln')].some(l => l.scrollWidth > max)) {
      size -= 2; el.style.fontSize = size + 'px';
    }
  }
}
"""

RENDERERS = {"quote": quote_card, "countdown": countdown_card, "carousel": carousel}


def main() -> None:
    src = Path(sys.argv[1])
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    posts = json.loads(src.read_text())
    OUT.mkdir(exist_ok=True)
    written = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        tab = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for p in posts:
            if only and p["id"] != only:
                continue
            pages = RENDERERS[p["type"]](p)
            names = [f"{p['id']}.png"] if len(pages) == 1 else [f"{p['id']}-{i:02d}.png" for i in range(1, len(pages) + 1)]
            for doc, name in zip(pages, names):
                tab.set_content(doc, wait_until="load")
                tab.evaluate("document.fonts.ready")
                tab.evaluate(FIT_JS)
                tab.screenshot(path=str(OUT / name), clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
                written.append(name)
            if "computed_days" in p:
                print(f"{p['id']}: {p['computed_days']} days")
        browser.close()
    print("\n".join(written))


if __name__ == "__main__":
    main()
