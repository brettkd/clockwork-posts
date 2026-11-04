#!/usr/bin/env python3
"""Render Clockwork Lifestyle posts from a content JSON file.

Usage: python3 tools/render.py content/2026-11.json [--only POST_ID]

Post types
  carousel  slides: list of slide objects (see below) -> posts/<id>-01.png ... (1080x1350)
  quote     single card (legacy; prefer a carousel)  -> posts/<id>.png
  countdown single card (legacy; prefer a carousel)  -> posts/<id>.png
  reel      lines: ["...", ...], end: "..."           -> posts/<id>.mp4 (1080x1920) + posts/<id>-cover.jpg

Slide kinds (carousels)
  quote     text, sub?            dark, the hook card
  countdown label?, line?          dark, days from the post date to Dec 31 (or post "target")
  cover     title, body?           dark, carousel title + "swipe"
  step      n, title, body         light, numbered step
  note      title, body            light, short explanation
  cta       title, body?           dark, send/save/comment prompt
  close     title, body?           dark, closing card

Text rules: [[word]] = the single brass highlight on that card; "\n" = intentional line break
(lines never wrap; the font auto-shrinks to fit).
"""
import datetime as dt
import html
import json
import math
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "posts"
LOGO = ROOT / "assets" / "logo.png"  # optional; wordmark is used when absent

INK = "#0B0B0B"
PAPER = "#F2EFE8"
BRASS = "#B08D57"


def hl(text: str) -> str:
    t = html.escape(text)
    t = re.sub(r"\[\[(.+?)\]\]", r'<span class="brass">\1</span>', t)
    if "\n" in t:
        return "".join(f'<span class="ln">{ln}</span>' for ln in t.split("\n"))
    return t


def dial(color: str) -> str:
    ticks = "".join(f'<i style="height:{22 if i % 3 == 0 else 11}px"></i>' for i in range(13))
    return f'<div class="dial" style="--c:{color}">{ticks}</div>'


def footer(color: str) -> str:
    if LOGO.exists():
        mark = f'<img class="logo" src="{LOGO.as_uri()}">'
    else:
        mark = '<span class="word">CLOCKWORK&nbsp;LIFESTYLE</span>'
    return f'<div class="foot" style="color:{color}">{mark}</div>'


CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:var(--w); height:var(--h); }}
body {{ font-family:'Inter Display','Inter',sans-serif; -webkit-font-smoothing:antialiased;
        font-feature-settings:'tnum' 1; }}
.card {{ position:relative; width:var(--w); height:var(--h); padding:132px 128px; overflow:hidden; }}
.dark {{ background:{INK}; color:{PAPER}; }}
.light {{ background:{PAPER}; color:{INK}; }}
.dark::after {{ content:''; position:absolute; inset:0; pointer-events:none;
  background: radial-gradient(ellipse at 50% 35%, rgba(255,255,255,0.045), transparent 60%); }}
.brass {{ color:{BRASS}; }}
.ln {{ display:block; white-space:nowrap; }}
.quote, .steptitle, .line, .sub, .stepbody {{ text-wrap:balance; }}
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
        opacity:0.72; max-width:780px; }}
.num {{ font-weight:300; font-size:400px; line-height:0.86; letter-spacing:-0.05em; }}
.numlabel {{ margin-top:36px; font-family:'Inter'; font-weight:500; font-size:30px;
             letter-spacing:0.3em; text-transform:uppercase; opacity:0.6; }}
.line {{ margin-top:72px; font-weight:600; font-size:56px; line-height:1.12; letter-spacing:-0.02em;
         max-width:800px; }}
.stepn {{ font-family:'Inter'; font-weight:300; font-size:150px; line-height:1; letter-spacing:-0.04em;
          opacity:0.22; margin-bottom:40px; }}
.steptitle {{ font-weight:600; font-size:74px; line-height:1.06; letter-spacing:-0.025em; }}
.stepbody {{ margin-top:40px; font-family:'Inter'; font-weight:400; font-size:38px; line-height:1.45;
             opacity:0.8; max-width:810px; }}
.kicker {{ font-family:'Inter'; font-weight:500; font-size:24px; letter-spacing:0.3em;
           text-transform:uppercase; opacity:0.5; margin-bottom:40px; }}
.swipe {{ position:absolute; right:128px; bottom:96px; font-family:'Inter'; font-weight:500;
          font-size:20px; letter-spacing:0.3em; opacity:0.5; }}
"""


def page(body: str, w: int = 1080, h: int = 1350, extra: str = "") -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>:root{{--w:{w}px;--h:{h}px}}{CSS}{extra}"
            f"</style></head><body>{body}</body></html>")


def days_left(p: dict) -> int:
    d = dt.date.fromisoformat(p["date"])
    target = dt.date.fromisoformat(p.get("target", f"{d.year}-12-31"))
    return (target - d).days


def slide_html(p: dict, s: dict, i: int, total: int) -> str:
    kind = s["kind"]
    theme = "light" if kind in ("step", "note") else "dark"
    fg = PAPER if theme == "dark" else INK
    right = f"{i:02d} / {total:02d}" if total > 1 else html.escape(p.get("pillar", ""))
    swipe = ""
    if kind == "quote":
        cls = "quote long" if len(s["text"]) > 70 else "quote"
        sub = f'<div class="sub">{hl(s["sub"])}</div>' if s.get("sub") else ""
        inner = f'<div class="{cls}">{hl(s["text"])}</div>{sub}'
        if total > 1:
            swipe = '<div class="swipe">SWIPE &rarr;</div>'
    elif kind == "countdown":
        n = days_left(p)
        p["computed_days"] = n
        line = f'<div class="line">{hl(s["line"])}</div>' if s.get("line") else ""
        label = s.get("label", f"days left in {dt.date.fromisoformat(p['date']).year}")
        inner = f'<div class="num">{n}</div><div class="numlabel">{html.escape(label)}</div>{line}'
        if total > 1:
            swipe = '<div class="swipe">SWIPE &rarr;</div>'
    elif kind == "step":
        inner = (f'<div class="stepn">{s["n"]:02d}</div><div class="steptitle">{hl(s["title"])}</div>'
                 f'<div class="stepbody">{hl(s["body"])}</div>')
    elif kind == "note":
        kicker = f'<div class="kicker">{html.escape(s["kicker"])}</div>' if s.get("kicker") else ""
        inner = f'{kicker}<div class="steptitle">{hl(s["title"])}</div><div class="stepbody">{hl(s["body"])}</div>'
    else:  # cover, cta, close
        sub = f'<div class="sub">{hl(s["body"])}</div>' if s.get("body") else ""
        inner = f'<div class="quote">{hl(s["title"])}</div>{sub}'
        if kind == "cover":
            swipe = '<div class="swipe">SWIPE &rarr;</div>'
    return page(f"""<div class="card {theme}"><div class="top">{dial(fg)}<span>{right}</span></div>
      <div class="mid">{inner}</div>{swipe}{footer(fg)}</div>""")


# Shrink any no-wrap line that overflows its column (min 52px).
FIT_JS = """
() => {
  for (const el of document.querySelectorAll('.quote, .steptitle, .line, .sub, .stepbody, .rq')) {
    if (!el.querySelector('.ln')) continue;
    let size = parseFloat(getComputedStyle(el).fontSize);
    const max = el.parentElement.clientWidth;
    while (size > 52 && [...el.querySelectorAll('.ln')].some(l => l.scrollWidth > max)) {
      size -= 2; el.style.fontSize = size + 'px';
    }
  }
}
"""

# ---------------------------------------------------------------- reels

REEL_FPS = 30
REEL_EXTRA = """
.reel { position:relative; width:1080px; height:1920px; background:#0B0B0B; color:#F2EFE8; overflow:hidden; }
.reel::after { content:''; position:absolute; inset:0;
  background: radial-gradient(ellipse at 50% 42%, rgba(255,255,255,0.05), transparent 60%); }
.rdial { position:absolute; left:120px; right:120px; top:300px; display:flex; justify-content:space-between; }
.rdial i { display:block; width:3px; background:#F2EFE8; opacity:0.18; height:18px; }
.rdial i.on { opacity:0.85; }
.rdial i.big { height:36px; }
.rmid { position:absolute; left:84px; right:84px; top:50%; transform:translateY(-55%); }
.rq { font-weight:600; font-size:124px; line-height:1.08; letter-spacing:-0.03em; }
.rq .ln { opacity:0; transform:translateY(24px); }
.rend { position:absolute; left:0; right:0; bottom:420px; text-align:center; font-family:'Inter';
        font-weight:600; font-size:24px; letter-spacing:0.42em; opacity:0; }
"""


def reel_html(p: dict) -> str:
    lines = "\n".join(p["lines"])
    ticks = "".join(f'<i class="{"big" if k % 5 == 0 else ""}"></i>' for k in range(31))
    return page(f"""<div class="reel"><div class="rdial">{ticks}</div>
      <div class="rmid"><div class="rq">{hl(lines)}</div></div>
      <div class="rend">{html.escape(p.get('end', 'RUN LIKE CLOCKWORK.')).upper()}</div></div>""",
                1080, 1920, REEL_EXTRA)


REEL_SET_T = """
(t) => {
  const lines = [...document.querySelectorAll('.rq .ln')];
  const start = 0.0, gap = 1.6;  // first line is visible from frame 0 (hook)
  lines.forEach((el, i) => {
    const k = i === 0 ? 1 : Math.min(1, Math.max(0, (t - (start + i * gap)) / 0.45));
    const e = 1 - Math.pow(1 - k, 3);
    el.style.opacity = e; el.style.transform = `translateY(${(1 - e) * 24}px)`;
  });
  const endAt = start + lines.length * gap + 0.4;
  const ke = Math.min(1, Math.max(0, (t - endAt) / 0.6));
  document.querySelector('.rend').style.opacity = ke * 0.65;
  const ticks = [...document.querySelectorAll('.rdial i')];
  const lit = Math.floor(t);  // one tick per second, like a second hand
  ticks.forEach((el, i) => el.classList.toggle('on', i <= lit));
  return endAt;
}
"""


def write_tick_audio(path: Path, seconds: float, line_times: list[float]) -> None:
    """Original audio: a soft clock tick every second, a deeper tock on each text reveal, low hum bed."""
    sr = 44100
    n = int(seconds * sr)
    out = [0.0] * n

    def click(at: float, freq: float, amp: float, decay: float) -> None:
        s0 = int(at * sr)
        for j in range(int(0.08 * sr)):
            if s0 + j >= n:
                break
            tt = j / sr
            out[s0 + j] += amp * math.sin(2 * math.pi * freq * tt) * math.exp(-tt * decay)

    for sec in range(int(seconds) + 1):
        click(sec, 2600, 0.22, 140)
        click(sec + 0.004, 1300, 0.12, 120)
    for lt in line_times:
        click(lt, 180, 0.55, 22)
        click(lt, 90, 0.35, 16)
    for j in range(n):
        tt = j / sr
        fade = min(1.0, tt / 1.0, (seconds - tt) / 1.0)
        out[j] += fade * 0.05 * math.sin(2 * math.pi * 55 * tt) * (0.6 + 0.4 * math.sin(2 * math.pi * 0.25 * tt))
    peak = max(1e-9, max(abs(v) for v in out))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(int(max(-1, min(1, v / peak * 0.8)) * 32767).to_bytes(2, "little", signed=True)
                               for v in out))


def render_reel(tab, p: dict) -> list[str]:
    tab.set_viewport_size({"width": 1080, "height": 1920})
    tab.set_content(reel_html(p), wait_until="load")
    tab.evaluate("document.fonts.ready")
    tab.evaluate(FIT_JS)
    end_at = tab.evaluate(REEL_SET_T, 0)
    duration = math.ceil(end_at + 2.4)
    line_times = [i * 1.6 for i in range(len(p["lines"]))]
    with tempfile.TemporaryDirectory() as td:
        frames = Path(td)
        for f in range(duration * REEL_FPS):
            tab.evaluate(REEL_SET_T, f / REEL_FPS)
            tab.screenshot(path=str(frames / f"{f:05d}.png"), type="png")
        audio = frames / "audio.wav"
        write_tick_audio(audio, duration, line_times)
        mp4 = OUT / f"{p['id']}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(REEL_FPS),
                        "-i", str(frames / "%05d.png"), "-i", str(audio),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(mp4)],
                       check=True)
        cover = OUT / f"{p['id']}-cover.jpg"
        last = sorted(frames.glob("*.png"))[-1]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(last), "-q:v", "2", str(cover)], check=True)
    tab.set_viewport_size({"width": 1080, "height": 1350})
    return [mp4.name, cover.name]


def single_as_slides(p: dict) -> list[dict]:
    if p["type"] == "quote":
        return [{"kind": "quote", "text": p["text"], "sub": p.get("sub")}]
    return [{"kind": "countdown", "label": p.get("label"), "line": p.get("line")}]


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
            if p["type"] == "reel":
                written += render_reel(tab, p)
                continue
            slides = p["slides"] if p["type"] == "carousel" else single_as_slides(p)
            total = len(slides)
            for i, s in enumerate(slides, 1):
                name = f"{p['id']}.png" if total == 1 else f"{p['id']}-{i:02d}.png"
                tab.set_content(slide_html(p, s, i, total), wait_until="load")
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
