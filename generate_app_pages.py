#!/usr/bin/env python3
"""Generate static per-app landing pages with QR codes from app_index.json.

Each app gets app/<fullname>/index.html at the canonical deep-link URL

    https://apps.micropythonos.com/app/<fullname>

so the same QR code works everywhere: a MicroPythonOS device recognizes the
link and opens the App Store detail screen; a phone lands on the page this
script generates. An overview list is written to app/index.html.

Usage:  python3 generate_app_pages.py       (requires: pip install segno)

Regenerate whenever app_index.json changes.
"""

import html
import json
import os
import shutil

import segno

SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://apps.micropythonos.com"
OUT_DIR = os.path.join(SITE_ROOT, "app")

# Palette matches the existing site (index.html).
CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Roboto', system-ui, sans-serif;
    background: #F8EDE3; color: #1A2E44;
    display: flex; justify-content: center;
    min-height: 100vh; padding: 20px;
}
.box {
    background: #fff; border-radius: 15px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    padding: 32px; max-width: 560px; width: 100%;
    height: fit-content;
}
.head { display: flex; align-items: center; gap: 16px; margin-bottom: 8px; }
.head img { width: 64px; height: 64px; border-radius: 12px; image-rendering: pixelated; }
h1 { font-size: 1.6rem; color: #0A4D68; }
.publisher { color: #5a6b7d; font-size: 0.95rem; }
.meta { color: #5a6b7d; font-size: 0.9rem; margin: 10px 0 16px; }
.meta span { margin-right: 14px; }
p { font-size: 1.05rem; line-height: 1.55; margin-bottom: 12px; overflow-wrap: anywhere; }
.qr-section {
    text-align: center; background: #F8EDE3;
    border-radius: 12px; padding: 20px; margin: 18px 0;
}
.qr-section svg { width: 200px; height: 200px; max-width: 100%; }
.qr-hint { font-size: 0.95rem; color: #1A2E44; margin-top: 10px; }
a { color: #FF6B6B; font-weight: 500; text-decoration: none; }
a:hover { text-decoration: underline; }
.actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 14px; }
.btn {
    display: inline-block; background: #0A4D68; color: #fff;
    padding: 10px 18px; border-radius: 8px; font-size: 0.95rem;
}
.btn.secondary { background: #FF6B6B; }
.foot { margin-top: 20px; font-size: 0.85rem; color: #5a6b7d; }
.foot code { overflow-wrap: anywhere; word-break: break-all; }
.applist { list-style: none; }
.applist li { border-bottom: 1px solid #eee; }
.applist a { display: flex; align-items: center; gap: 12px; padding: 10px 4px; color: #1A2E44; }
.applist img { width: 40px; height: 40px; border-radius: 8px; image-rendering: pixelated; }
.applist .desc { color: #5a6b7d; font-size: 0.85rem; }
"""


def qr_svg(link):
    """Render a QR code for link as a crisp inline SVG (no external assets)."""
    qr = segno.make(link, error="m")
    matrix = [bytearray(row) for row in qr.matrix]
    n = len(matrix)
    border = 2
    size = n + 2 * border
    rects = []
    for y, row in enumerate(matrix):
        x = 0
        while x < n:
            if row[x]:
                run = x
                while run < n and row[run]:
                    run += 1
                rects.append('<rect x="%d" y="%d" width="%d" height="1"/>'
                             % (x + border, y + border, run - x))
                x = run
            else:
                x += 1
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'role="img" aria-label="QR code linking to this app">'
            '<rect width="%d" height="%d" fill="#fff"/>'
            '<g fill="#1A2E44">%s</g></svg>'
            % (size, size, size, size, "".join(rects)))


def site_relative(url, depth):
    """Turn an absolute site URL into a relative one so local previews work."""
    if url and url.startswith(BASE_URL + "/"):
        return "../" * depth + url[len(BASE_URL) + 1:]
    return url


def app_page(app):
    fullname = app["fullname"]
    link = "%s/app/%s" % (BASE_URL, fullname)
    name = html.escape(app.get("name") or fullname)
    publisher = html.escape(app.get("publisher") or "")
    short_desc = html.escape(app.get("short_description") or "")
    long_desc = html.escape(app.get("long_description") or "")
    version = html.escape(app.get("version") or "?")
    category = html.escape(app.get("category") or "")
    icon = html.escape(site_relative(app.get("icon_url") or "", 2))
    mpk = html.escape(site_relative(app.get("download_url") or "", 2))

    icon_tag = '<img src="%s" alt="" width="64" height="64">' % icon if icon else ""
    download = ('<a class="btn secondary" href="%s" download>Download .mpk</a>' % mpk) if mpk else ""
    long_p = "<p>%s</p>" % long_desc if long_desc and long_desc != short_desc else ""

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(name)s — MicroPythonOS App Store</title>
<meta name="description" content="%(short_desc)s">
<meta property="og:title" content="%(name)s — MicroPythonOS App Store">
<meta property="og:description" content="%(short_desc)s">
<meta property="og:type" content="website">
<meta property="og:url" content="%(link)s">
<link rel="canonical" href="%(link)s">
<style>%(css)s</style>
</head>
<body>
<main class="box">
  <div class="head">%(icon_tag)s
    <div><h1>%(name)s</h1><div class="publisher">%(publisher)s</div></div>
  </div>
  <div class="meta"><span>Version %(version)s</span><span>%(category)s</span></div>
  <p>%(short_desc)s</p>
  %(long_p)s
  <div class="qr-section">
    %(qr)s
    <div class="qr-hint">Have a <a href="https://micropythonos.com">MicroPythonOS</a> device?<br>
    Open the <strong>App Store</strong> app and scan this code to install %(name)s.</div>
  </div>
  <div class="actions">
    <a class="btn" href="../">All apps</a>
    %(download)s
  </div>
  <div class="foot">This page is the target of the app's QR deep link:<br><code>%(link)s</code></div>
</main>
</body>
</html>
""" % {
        "name": name, "publisher": publisher, "short_desc": short_desc,
        "long_p": long_p, "version": version, "category": category,
        "icon_tag": icon_tag, "download": download, "link": html.escape(link),
        "qr": qr_svg(link), "css": CSS,
    }


def index_page(apps):
    items = []
    for app in apps:
        fullname = app["fullname"]
        icon = html.escape(site_relative(app.get("icon_url") or "", 1))
        icon_tag = '<img src="%s" alt="" width="40" height="40">' % icon if icon else ""
        items.append(
            '<li><a href="%s/">%s<span><strong>%s</strong>'
            '<div class="desc">%s</div></span></a></li>'
            % (html.escape(fullname), icon_tag, html.escape(app.get("name") or fullname),
               html.escape(app.get("short_description") or "")))
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Apps — MicroPythonOS App Store</title>
<style>%s</style>
</head>
<body>
<main class="box">
  <h1>MicroPythonOS Apps</h1>
  <p class="meta">Each app page shows a QR code you can scan with the App Store on your device.</p>
  <ul class="applist">
  %s
  </ul>
</main>
</body>
</html>
""" % (CSS, "\n  ".join(items))


def main():
    with open(os.path.join(SITE_ROOT, "app_index.json")) as f:
        apps = json.load(f)
    apps.sort(key=lambda a: (a.get("name") or a["fullname"]).lower())

    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    for app in apps:
        fullname = app.get("fullname")
        if not fullname:
            continue
        page_dir = os.path.join(OUT_DIR, fullname)
        os.makedirs(page_dir)
        with open(os.path.join(page_dir, "index.html"), "w") as f:
            f.write(app_page(app))
    with open(os.path.join(OUT_DIR, "index.html"), "w") as f:
        f.write(index_page(apps))
    print("generated %d app pages + index in %s" % (len(apps), OUT_DIR))


if __name__ == "__main__":
    main()
