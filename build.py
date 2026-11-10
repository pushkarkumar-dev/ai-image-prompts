#!/usr/bin/env python3
"""Builds the prompt website from prompts/*.json (stdlib only).

Each prompts/<slug>.json:
  {"slug", "title", "prompt", "date": "YYYY-MM-DD", "image": "images/<slug>.jpg",
   "uses_photo": bool, "tip": optional str}

Writes p/<slug>/index.html for every prompt and index.html (the gallery, newest first).
  python3 build.py            build everything
  python3 build.py --check    validate the JSON files only
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://pushkarkumar-dev.github.io/ai-image-prompts"
HANDLE = "pushkarkrraijada"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

CSS = """
:root{--bg:#0f0d14;--card:#1a1722;--ink:#f4f1fa;--muted:#a59fb5;--line:#2c2738;--accent:#ffb347;--accent-ink:#1a1206}
@media (prefers-color-scheme: light){:root{--bg:#faf8f4;--card:#ffffff;--ink:#1b1724;--muted:#6b6478;--line:#e8e2d8;--accent:#e8890c;--accent-ink:#fff}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
a{color:inherit}
.wrap{max-width:720px;margin:0 auto;padding:20px 16px 48px}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:18px}
header a{text-decoration:none;font-weight:700;letter-spacing:.2px}
header .handle{color:var(--muted);font-size:14px;text-decoration:none}
.hero{width:100%;border-radius:18px;display:block;background:var(--card)}
h1{font-size:26px;line-height:1.2;margin:20px 0 6px}
.meta{color:var(--muted);font-size:14px;margin:0 0 18px}
.box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px}
.box h2{font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 10px}
pre{white-space:pre-wrap;word-wrap:break-word;margin:0;font:15px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace}
button.copy{margin-top:14px;width:100%;border:0;border-radius:12px;padding:14px;font:600 16px/1 inherit;background:var(--accent);color:var(--accent-ink);cursor:pointer}
button.copy:active{transform:scale(.99)}
.steps{margin:18px 0 0;padding-left:20px;color:var(--muted)}
.steps li{margin:4px 0}
.note{margin-top:14px;padding:12px 14px;border-radius:12px;border:1px dashed var(--line);color:var(--muted);font-size:14px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
@media (min-width:560px){.grid{grid-template-columns:repeat(3,1fr)}}
.grid a{display:block;text-decoration:none}
.grid img{width:100%;aspect-ratio:4/5;object-fit:cover;border-radius:12px;display:block;background:var(--card)}
.grid span{display:block;font-size:13px;color:var(--muted);margin-top:6px;line-height:1.3}
footer{margin-top:36px;color:var(--muted);font-size:13px;text-align:center}
"""

COPY_JS = """
document.querySelectorAll('button.copy').forEach(function(b){b.addEventListener('click',function(){
  var t=document.getElementById(b.dataset.target).innerText,l=b.textContent;
  function done(){b.textContent='Copied \\u2713';setTimeout(function(){b.textContent=l},1600)}
  if(navigator.clipboard){navigator.clipboard.writeText(t).then(done,fallback)}else{fallback()}
  function fallback(){var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();
    try{document.execCommand('copy');done()}catch(e){}document.body.removeChild(a)}
})});
"""


def esc(s):
    return html.escape(str(s), quote=True)


def page(title, body, desc="", image="", url=""):
    og = ""
    if image:
        og = (
            f'<meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(desc)}">'
            f'<meta property="og:image" content="{esc(image)}">'
            f'<meta property="og:url" content="{esc(url)}">'
            '<meta name="twitter:card" content="summary_large_image">'
        )
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{esc(title)}</title><meta name=\"description\" content=\"{esc(desc)}\">{og}"
        f"<style>{CSS}</style></head><body><div class=\"wrap\">{body}"
        f"<footer>New prompts every day on Instagram · <a href=\"https://instagram.com/{HANDLE}\">@{HANDLE}</a></footer>"
        f"</div><script>{COPY_JS}</script></body></html>"
    )


def header(home):
    return (
        f'<header><a href="{home}">✨ AI Image Prompts</a>'
        f'<a class="handle" href="https://instagram.com/{HANDLE}">@{HANDLE}</a></header>'
    )


def load():
    items, problems = [], []
    folder = os.path.join(ROOT, "prompts")
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(folder, name)
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:  # noqa: BLE001
            problems.append(f"{name}: not valid JSON ({e})")
            continue
        slug = d.get("slug", "")
        if not SLUG_RE.match(slug) or name != f"{slug}.json":
            problems.append(f"{name}: slug must be lowercase-with-dashes and match the file name")
        for key in ("title", "prompt", "date", "image"):
            if not isinstance(d.get(key), str) or not d[key].strip():
                problems.append(f"{name}: missing {key}")
        if d.get("image") and not os.path.isfile(os.path.join(ROOT, d["image"])):
            problems.append(f"{name}: image {d['image']} not found")
        items.append(d)
    items.sort(key=lambda d: (d.get("date", ""), d.get("slug", "")), reverse=True)
    return items, problems


def build_prompt(d):
    slug = d["slug"]
    url = f"{SITE_URL}/p/{slug}/"
    img = f"{SITE_URL}/{d['image']}"
    if d.get("uses_photo"):
        steps = (
            "<li>Copy the prompt.</li>"
            "<li>Open your AI image tool and attach one clear, front-facing photo of yourself.</li>"
            "<li>Paste the prompt and generate.</li>"
        )
    else:
        steps = "<li>Copy the prompt.</li><li>Paste it into your AI image tool and generate.</li>"
    tip = f'<div class="note">💡 {esc(d["tip"])}</div>' if d.get("tip") else ""
    body = (
        header("../../")
        + f'<img class="hero" src="../../{esc(d["image"])}" alt="{esc(d["title"])}">'
        + f'<h1>{esc(d["title"])}</h1><p class="meta">{esc(d["date"])}</p>'
        + '<div class="box"><h2>The prompt</h2>'
        + f'<pre id="prompt">{esc(d["prompt"].strip())}</pre>'
        + '<button class="copy" data-target="prompt">Copy prompt</button></div>'
        + f'<ol class="steps">{steps}</ol>{tip}'
    )
    out = os.path.join(ROOT, "p", slug)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(f"{d['title']} · AI image prompt", body, "Copy the prompt and make your own.", img, url))


def build_index(items):
    cards = "".join(
        f'<a href="p/{esc(d["slug"])}/"><img loading="lazy" src="{esc(d["image"])}" alt="{esc(d["title"])}">'
        f'<span>{esc(d["title"])}</span></a>'
        for d in items
    )
    body = header("./") + '<p class="meta">Tap any image to copy its prompt.</p>' + f'<div class="grid">{cards}</div>'
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page("AI Image Prompts", body, "Copy-paste prompts for every image I post."))


def main():
    items, problems = load()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)
    if "--check" in sys.argv:
        print(f"ok: {len(items)} prompts")
        return
    for d in items:
        build_prompt(d)
    build_index(items)
    print(f"built {len(items)} prompt pages + index")


if __name__ == "__main__":
    main()
