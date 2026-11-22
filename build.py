#!/usr/bin/env python3
"""Build the Frontier Four Press site.

    python3 build.py               build docs/ and regenerate share image + favicons
    python3 build.py --no-images   build docs/ only (fast; keeps existing images)

Reads site.config.json and src/, writes the deployable site to docs/.
Standard library only. Images are rendered with the local Google Chrome
(headless) and resized with macOS `sips`.
"""
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "docs"
TOOLS = ROOT / "tools"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DOMAIN = "frontierfourpress.com"

# Names that must never appear in visible text. Amazon is allowed only on the
# pre-order button. To check for a name you do not want in this public repo
# (for example an employer), set FFP_EXTRA_BANNED="Name One,Name Two" in your
# shell instead of adding it here.
BANNED = [
    "OpenAI", "ChatGPT", "GPT", "Anthropic", "Claude", "Gemini", "Bard",
    "Google", "DeepMind", "Microsoft", "Copilot", "Meta", "Llama", "Mistral",
    "Perplexity", "DeepSeek", "Grok", "xAI", "Nvidia", "NVIDIA", "Midjourney",
    "Cursor", "Replit", "Lovable", "Salesforce", "Agentforce", "Amazon", "AWS",
]

warnings = []
errors = []


def esc(s):
    return html.escape(str(s), quote=True)


def sips_size(path):
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                         capture_output=True, text=True, check=True).stdout
    w = int(re.search(r"pixelWidth: (\d+)", out).group(1))
    h = int(re.search(r"pixelHeight: (\d+)", out).group(1))
    return w, h


def font_stack(name, fallback):
    first = f'"{name}", ' if name else ""
    parts = []
    for f in fallback.split(","):
        f = f.strip()
        parts.append(f if f in ("serif", "sans-serif") or " " not in f else f'"{f}"')
    return first + ", ".join(parts)


def build_fonts(cfg, dest_prefix):
    """@font-face rules for self-hosted files listed in config.fonts.files.
    Each entry: {"family": "...", "path": "assets/source/fonts/x.woff2",
                 "style": "normal|italic", "weight": "400"}"""
    rules = []
    for f in cfg["fonts"].get("files", []):
        src = ROOT / f["path"]
        if not src.exists():
            errors.append(f"Font file listed in config but missing: {f['path']}")
            continue
        dest = OUT / "assets" / "fonts" / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        fmt = "woff2" if src.suffix == ".woff2" else "woff"
        rules.append(
            "@font-face { font-family: \"%s\"; src: url(\"%s%s\") format(\"%s\"); "
            "font-style: %s; font-weight: %s; font-display: swap; }"
            % (f["family"], dest_prefix, "assets/fonts/" + src.name, fmt,
               f.get("style", "normal"), f.get("weight", "400")))
    return "\n".join(rules)


def chrome_screenshot(url, out_png, w, h):
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([
            CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--no-first-run", "--no-default-browser-check",
            f"--user-data-dir={profile}", "--force-device-scale-factor=1",
            f"--window-size={w},{h}", f"--screenshot={out_png}", url,
        ], check=True, capture_output=True)


def main():
    skip_images = "--no-images" in sys.argv
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))

    # Keep previously generated images when skipping image generation.
    keep = {}
    if skip_images and OUT.exists():
        for name in ("share.png", "favicon-32.png", "apple-touch-icon.png"):
            p = OUT / "assets" / name
            if p.exists():
                keep[name] = p.read_bytes()

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC / "assets", OUT / "assets")
    for name, data in keep.items():
        (OUT / "assets" / name).write_bytes(data)

    divider = (SRC / "assets" / "img" / "divider.svg").read_text(encoding="utf-8").strip()

    # ---- Cover -------------------------------------------------------------
    cover_src = ROOT / cfg["cover"]["path"] if cfg["cover"]["path"] else None
    if cover_src and cover_src.exists():
        dest = OUT / "assets" / "cover.jpg"
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85",
                        "-Z", "1400", str(cover_src), "--out", str(dest)],
                       check=True, capture_output=True)
        cw, ch = sips_size(dest)
        cover_rel = "assets/cover.jpg"
        cover_alt = cfg["cover"]["alt"]
        os.remove(OUT / "assets" / "img" / "cover-placeholder.svg")
    else:
        cover_rel = "assets/img/cover-placeholder.svg"
        cw, ch = 600, 900
        cover_alt = "Placeholder for the cover of Escape Velocity"
        warnings.append(f"COVER: {cfg['cover']['path']} not found. Showing the marked placeholder.")
    cover_html = (f'<img src="{cover_rel}" width="{cw}" height="{ch}" '
                  f'alt="{esc(cover_alt)}" fetchpriority="high">')

    # ---- Logo --------------------------------------------------------------
    logo_src = ROOT / cfg["logo"]["path"] if cfg["logo"]["path"] else None
    if logo_src and logo_src.exists():
        dest = OUT / "assets" / ("logo" + logo_src.suffix.lower())
        shutil.copy2(logo_src, dest)
        logo_html = f'<img class="logo-img" src="assets/{dest.name}" alt="Frontier Four Press">'
    else:
        logo_html = ('<!-- PLACEHOLDER: type-set Stack logo until the designer files arrive -->\n'
                     '    <div class="stack" role="img" aria-label="Frontier Four Press">'
                     '<span>Frontier</span><span class="stack__four">FOUR</span><span>Press</span></div>')
        warnings.append(f"LOGO: {cfg['logo']['path']} not found. Showing a type-set Stack placeholder.")

    # ---- Pre-order ---------------------------------------------------------
    po = cfg["preorder"]
    if po["url"].strip():
        label = "Pre-order" + (f" on {po['retailer']}" if po.get("retailer") else "")
        preorder_html = f'<a class="button" href="{esc(po["url"].strip())}">{esc(label)}</a>'
    else:
        preorder_html = f'<p class="button button--closed">{esc(po["closedText"])}</p>'
        warnings.append("PRE-ORDER: no URL set. Showing the closed state.")

    # ---- Endorsement -------------------------------------------------------
    en = cfg["endorsement"]
    if en["quote"].strip():
        detail = (f'<span class="detail">{esc(en["attributionDetail"])}</span>'
                  if en.get("attributionDetail", "").strip() else "")
        if not en["attribution"].strip():
            errors.append("ENDORSEMENT: quote is set but attribution is empty.")
        endorsement_html = f'''
  <section class="paper endorsement" aria-labelledby="endorsement-heading">
    <div class="column">
      {divider}
      <h2 id="endorsement-heading" class="visually-hidden">Endorsement</h2>
      <figure>
        <blockquote><p>{esc(en["quote"].strip())}</p></blockquote>
        <figcaption class="label">{esc(en["attribution"].strip())}{detail}</figcaption>
      </figure>
    </div>
  </section>
'''
    else:
        endorsement_html = ""
        warnings.append("ENDORSEMENT: empty. Section is hidden.")

    # ---- Contact -----------------------------------------------------------
    email = cfg["contactEmail"].strip()
    if email:
        contact_button = f'<p><a class="button" href="mailto:{esc(email)}">Contact</a></p>'
        contact_text = f'<a href="mailto:{esc(email)}">{esc(email)}</a>'
    else:
        contact_button = ('<p><span class="placeholder">[PLACEHOLDER: Contact button. '
                          'Set contactEmail in site.config.json]</span></p>')
        contact_text = '<span class="placeholder">[PLACEHOLDER: contact email]</span>'
        warnings.append("CONTACT EMAIL: not set. Contact button and footer show placeholders.")

    # ---- Fonts -------------------------------------------------------------
    f = cfg["fonts"]
    display_stack = font_stack(f["display"], f["displayFallback"])
    sans_stack = font_stack(f["sans"], f["sansFallback"])
    font_faces = build_fonts(cfg, "")

    css = (OUT / "assets" / "css" / "site.css").read_bytes()
    build_id = hashlib.sha1(css + json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8]

    meta_desc = (f"Escape Velocity: A Novel About Leading Through AI, by Olawale Oladehin. "
                 f"On sale {cfg['onSaleDate']}. {cfg['formats']}")

    page = (SRC / "index.html").read_text(encoding="utf-8")
    subs = {
        "META_DESCRIPTION": esc(meta_desc),
        "SITE_URL": esc(cfg["siteUrl"].rstrip("/")),
        "BUILD_ID": build_id,
        "COVER_ALT": esc(cover_alt),
        "ISBN_PAPERBACK_DIGITS": cfg["isbnPaperback"].replace("-", ""),
        "FONT_FACES": font_faces,
        "FONT_DISPLAY": display_stack,
        "FONT_SANS": sans_stack,
        "COVER": cover_html,
        "ON_SALE_DATE": esc(cfg["onSaleDate"]),
        "FORMATS": esc(cfg["formats"]),
        "PREORDER": preorder_html,
        "ENDORSEMENT": endorsement_html,
        "DIVIDER": divider,
        "CONTACT_BUTTON": contact_button,
        "CONTACT_TEXT": contact_text,
        "AUTHOR_SITE_URL": esc(cfg["authorSiteUrl"]),
        "LOGO": logo_html,
        "COPYRIGHT": esc(cfg["copyright"]),
        "ISBN_PAPERBACK": esc(cfg["isbnPaperback"]),
        "ISBN_EBOOK": esc(cfg["isbnEbook"]),
    }
    for k, v in subs.items():
        page = page.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if left:
        errors.append(f"Unfilled template slots: {sorted(set(left))}")

    # ---- Copy rules lint ---------------------------------------------------
    check = re.sub(r"<!--.*?-->", "", page, flags=re.S)
    check = re.sub(r"<style>.*?</style>", "", check, flags=re.S)
    if "—" in check:
        errors.append("Em dash found in page text. Remove it (check the config values too).")
    without_button = re.sub(r'<a class="button" href="[^"]*">Pre-order[^<]*</a>', "", check)
    extra = [x.strip() for x in os.environ.get("FFP_EXTRA_BANNED", "").split(",") if x.strip()]
    for word in BANNED + extra:
        if re.search(r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])", without_button):
            errors.append(f"Banned name in page text: {word!r}")

    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        print("Build stopped. docs/index.html was not written.", file=sys.stderr)
        sys.exit(1)
    (OUT / "index.html").write_text(page, encoding="utf-8")

    # ---- GitHub Pages files ------------------------------------------------
    (OUT / "CNAME").write_text(DOMAIN + "\n")
    (OUT / ".nojekyll").write_text("")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n")
    (OUT / "assets" / "img" / "divider.svg").unlink()  # inlined in the page

    # ---- Share image and favicons -----------------------------------------
    if not skip_images:
        if not Path(CHROME).exists():
            errors.append("Google Chrome not found; cannot render share image and favicons.")
        else:
            build_dir = ROOT / "build"
            build_dir.mkdir(exist_ok=True)
            card = (TOOLS / "share-card.html").read_text(encoding="utf-8")
            card = (card.replace("{{FONT_FACES}}", build_fonts(cfg, (OUT.as_uri() + "/")))
                        .replace("{{FONT_DISPLAY}}", display_stack)
                        .replace("{{FONT_SANS}}", sans_stack)
                        .replace("{{COVER_SRC}}", (OUT / cover_rel).as_uri())
                        .replace("{{ON_SALE_DATE}}", esc(cfg["onSaleDate"])))
            card_path = build_dir / "share-card.html"
            card_path.write_text(card, encoding="utf-8")
            chrome_screenshot(card_path.as_uri(), OUT / "assets" / "share.png", 1200, 630)

            fav_path = build_dir / "favicon.html"
            fav_path.write_text(
                '<!doctype html><html><body style="margin:0;background:#DF5555">'
                f'<img src="{(OUT / "assets" / "favicon.svg").as_uri()}" '
                'style="display:block;width:512px;height:512px"></body></html>')
            big = build_dir / "favicon-512.png"
            chrome_screenshot(fav_path.as_uri(), big, 512, 512)
            for size, name in ((180, "apple-touch-icon.png"), (32, "favicon-32.png")):
                subprocess.run(["sips", "-z", str(size), str(size), str(big),
                                "--out", str(OUT / "assets" / name)],
                               check=True, capture_output=True)

    for w in warnings:
        print("  open:", w)
    for e in errors:
        print("ERROR:", e, file=sys.stderr)
    if errors:
        sys.exit(1)
    print(f"Built {OUT.relative_to(ROOT)}/ (build {build_id})")


if __name__ == "__main__":
    main()
