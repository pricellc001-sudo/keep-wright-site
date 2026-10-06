"""Consistency check for the Keep-Wright site. Run before every commit.

    python tools/check.py          report problems, exit 1 if any
    python tools/check.py --fix    also repair what it safely can:
                                   the CSP script hash in index.html,
                                   sitemap <lastmod> dates from git history

Checks: shared header/footer identical on every page, CSP hash matches the
inline script, sitemap lists every indexable page, every referenced asset
exists, scene photos have AVIF and WebP variants, no CRLF line endings,
policy pages carry a version line, and the copyright year is current.
"""
import base64, datetime, hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
FIX = "--fix" in sys.argv
PAGES = ["index.html", "refund.html", "terms.html", "privacy.html", "404.html"]
problems, notes = [], []

def rd(p): return open(p, encoding="utf-8", newline="").read()
def wr(p, s): open(p, "w", encoding="utf-8", newline="").write(s)
def fail(msg): problems.append(msg)
def note(msg): notes.append(msg)

html = {p: rd(p) for p in PAGES}

# 1. line endings
for p, s in html.items():
    if "\r" in s: fail(f"{p}: has CRLF line endings (save as LF)")

# 2. shared header and footer
def block(s, start, end):
    i = s.find(start); j = s.find(end, i)
    return None if i < 0 or j < 0 else s[i:j + len(end)]
def norm(b):
    return re.sub(r"\s+", " ", b.replace('href="#top"', 'href="/"').replace('href="terms', 'href="/terms')
                  .replace('href="privacy', 'href="/privacy').replace('href="refund', 'href="/refund')).strip()
ref_h = norm(block(html["refund.html"], '<header class="top">', "</header>"))
ref_f = norm(block(html["refund.html"], "<footer>", "</footer>"))
for p, s in html.items():
    h = block(s, '<header class="top">', "</header>"); f = block(s, "<footer>", "</footer>")
    if not h or norm(h) != ref_h: fail(f"{p}: header differs from refund.html")
    if not f or norm(f) != ref_f: fail(f"{p}: footer differs from refund.html")

# 3. CSP script hash on index.html
s = html["index.html"]
scripts = re.findall(r"<script>(.*?)</script>", s, re.S)
if len(scripts) != 1:
    fail(f"index.html: expected exactly one plain <script> block, found {len(scripts)}")
else:
    want = "sha256-" + base64.b64encode(hashlib.sha256(scripts[0].encode("utf-8")).digest()).decode()
    m = re.search(r"script-src 'sha256-[^']+'", s)
    if not m: fail("index.html: CSP has no script-src hash")
    elif want not in m.group(0):
        if FIX:
            s = s.replace(m.group(0), f"script-src '{want}'"); wr("index.html", s); html["index.html"] = s
            note("index.html: CSP script hash updated")
        else: fail("index.html: CSP script hash is stale (run with --fix)")
for p in PAGES:
    if 'http-equiv="Content-Security-Policy"' not in html[p]: fail(f"{p}: missing CSP meta")
    if p != "index.html" and "<script" in html[p]: fail(f"{p}: contains a script but its CSP allows none")
    if re.search(r"\son[a-z]+=", html[p]): fail(f"{p}: inline event handler attribute (blocked by CSP)")

# 4. sitemap
sm = rd("sitemap.xml")
for p in PAGES:
    noindex = 'name="robots" content="noindex"' in html[p]
    loc = "https://keep-wright.com/" + ("" if p == "index.html" else p)
    if noindex:
        if loc in sm: fail(f"sitemap.xml: lists noindex page {p}")
        continue
    if loc not in sm: fail(f"sitemap.xml: missing {p}")
    canon = f'<link rel="canonical" href="{loc}">'
    if canon not in html[p]: fail(f"{p}: canonical should be {loc}")
def git_date(p):
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", p], capture_output=True, text=True).stdout.strip()
        return out or None
    except Exception: return None
if FIX:
    new = sm
    for p in PAGES:
        loc = "https://keep-wright.com/" + ("" if p == "index.html" else p)
        d = git_date(p)
        if d and loc in new:
            new = re.sub(rf"(<loc>{re.escape(loc)}</loc><lastmod>)[^<]+", rf"\g<1>{d}", new)
    if new != sm: wr("sitemap.xml", new); note("sitemap.xml: lastmod dates refreshed from git")
today = datetime.date.today().isoformat()
for d in re.findall(r"<lastmod>([^<]+)", sm):
    if d > today: fail(f"sitemap.xml: lastmod {d} is in the future")

# 5. assets referenced exist; scene photos have modern variants
for p, s in html.items():
    for ref in set(re.findall(r'(?:href|src|srcset|imagesrcset|content)="([^"]*assets/[^" ]+)', s)):
        for one in re.split(r",\s*", ref):
            path = one.split()[0].replace("https://keep-wright.com/", "").lstrip("/")
            if not os.path.exists(path): fail(f"{p}: references missing asset {path}")
for jpg in [f for f in os.listdir("assets") if re.match(r"(still|deskphone|bench|lamp)-\d+\.jpg$", f)]:
    for ext in ("avif", "webp"):
        if not os.path.exists("assets/" + jpg[:-3] + ext): fail(f"assets/{jpg}: missing .{ext} variant")
for p in ("favicon.svg", "favicon.ico", "apple-touch-icon.png", "robots.txt", ".well-known/security.txt", "CNAME", ".nojekyll"):
    if not os.path.exists(p): fail(f"missing {p}")

# 6. policy pages: version line, copyright year, leftover placeholders
for p in ("terms.html", "privacy.html"):
    if not re.search(r"Version \d+, effective [A-Z][a-z]+ \d{1,2}, \d{4}", html[p]): fail(f"{p}: no 'Version N, effective <date>' line")
year = str(datetime.date.today().year)
for p, s in html.items():
    if f"© {year}" not in s and f"&copy; {year}" not in s: fail(f"{p}: copyright year is not {year}")
    for ph in re.findall(r"<!--\s*\[([A-Z ]+)\].*?-->", s, re.S): note(f"{p}: placeholder still open: [{ph}]")
if 'data-stripe="audit"' in html["index.html"] and "mailto:" in re.search(r'<a class="btn" href="([^"]+)" data-stripe', html["index.html"]).group(1):
    note("index.html: order buttons still open email (Stripe Payment Links not connected)")
exp = re.search(r"Expires: (\d{4}-\d{2}-\d{2})", rd(".well-known/security.txt"))
if exp and (datetime.date.fromisoformat(exp.group(1)) - datetime.date.today()).days < 60: fail("security.txt expires within 60 days")

for n in notes: print("note ", n)
for f in problems: print("FAIL ", f)
print("OK: no problems" if not problems else f"{len(problems)} problem(s)")
sys.exit(1 if problems else 0)
