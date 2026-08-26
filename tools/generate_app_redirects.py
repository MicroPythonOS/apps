#!/usr/bin/env python3
"""Generate browser redirect pages for MPOS app deep links.

The QR app-link format (https://apps.micropythonos.com/app/<app_id>) is
resolved natively by the device camera (MPOS 0.17+), but in a phone browser
those URLs used to 404: this host serves static files and no /app/ tree
existed. This script fetches every published MPOS app from BadgeHub and
writes a tiny redirect page per app so a phone scan lands on the app's
BadgeHub page instead.

Two directories are written per app: the lowercase slug and the all-uppercase
form. QR codes encode the link in uppercase (alphanumeric mode packs ~40%
tighter), the filesystem serving this site is case-sensitive, and BadgeHub's
frontend only resolves lowercase slugs - so both spellings must exist and
both must redirect to the lowercase target.

Re-run after new apps are published, from the repository root:

    python3 tools/generate_app_redirects.py

Output is deterministic; commit the resulting app/ tree.

NOTE: run on a case-sensitive filesystem (any Linux). On macOS the
lowercase and uppercase directories collapse into one and only a
single spelling survives to be committed. The same applies to plain
checkouts: cloning this repo on a case-insensitive filesystem (default
macOS/Windows) collapses the spellings and leaves a permanently dirty
tree - do app/ work from Linux or a case-sensitive volume.
"""

import html
import json
import os
import shutil
import sys
import urllib.request

LIST_URL = "https://badgehub.eu/api/v3/project-summaries?badge=mpos_api_0"
TARGET = "https://badgehub.eu/page/project/{slug}"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} - MicroPythonOS</title>
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}">
<script>location.replace("{target}");</script>
</head>
<body>
<p>{name} lives on <a href="{target}">BadgeHub</a>, the MicroPythonOS app
store. If you are not redirected automatically, follow the link.</p>
<p>Scanned this QR with a MicroPythonOS device? The camera app installs it
directly - no browser needed.</p>
</body>
</html>
"""

INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MicroPythonOS apps</title>
<meta http-equiv="refresh" content="0; url=https://badgehub.eu/">
<link rel="canonical" href="https://badgehub.eu/">
<script>location.replace("https://badgehub.eu/");</script>
</head>
<body>
<p>MicroPythonOS apps live on <a href="https://badgehub.eu/">BadgeHub</a>.</p>
</body>
</html>
"""


def main():
    # The API front-end rejects the default urllib User-Agent.
    req = urllib.request.Request(LIST_URL, headers={"User-Agent": "mpos-app-redirects/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        items = json.load(r)
    by_slug = {p["slug"]: p for p in items}
    slugs = sorted(by_slug)
    if not slugs:
        sys.exit("BadgeHub returned no apps; refusing to empty the tree")

    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    with open(os.path.join(root, "index.html"), "w") as f:
        f.write(INDEX)

    pages = 0
    for slug in slugs:
        target = TARGET.format(slug=slug)
        name = html.escape(by_slug[slug].get("name") or slug)
        for spelling in {slug, slug.upper(), slug.lower()}:
            d = os.path.join(root, spelling)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "index.html"), "w") as f:
                f.write(PAGE.format(name=name, target=target))
            pages += 1
    print(f"{len(slugs)} apps -> {pages} redirect pages under app/")


if __name__ == "__main__":
    main()
