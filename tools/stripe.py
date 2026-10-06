"""Wire the Stripe Payment Link for the Missed-Call Audit into index.html.

    python tools/stripe.py https://buy.stripe.com/xxxxxxxx

Replaces the href on every data-stripe="audit" button (there are three),
updates the small print under the hero and pricing buttons so it no longer
promises an emailed invoice, and refreshes the README swap-in list.
Run tools/check.py --fix afterwards, then commit.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

if len(sys.argv) != 2 or not re.fullmatch(r"https://buy\.stripe\.com/[A-Za-z0-9_\-]+", sys.argv[1]):
    sys.exit("usage: python tools/stripe.py https://buy.stripe.com/<id>   (a Stripe Payment Link URL)")
LINK = sys.argv[1]

def rd(p): return open(p, encoding="utf-8", newline="").read()
def wr(p, s): open(p, "w", encoding="utf-8", newline="").write(s)

s = rd("index.html")
pat = re.compile(r'<a class="btn" href="[^"]*" data-stripe="audit">')
n = len(pat.findall(s))
assert n == 3, f"expected 3 audit buttons, found {n}"
s = pat.sub(f'<a class="btn" href="{LINK}" data-stripe="audit">', s)

swaps = [
    ('<small>Order by email, pay by secure card invoice. Written report within 3 business days.</small>',
     '<small>Pay by card. Written report within 3 business days.</small>'),
    ('<small>Order by email. We reply within one business day with a secure card invoice; never send card details by email.</small>',
     '<small>Pay by card through Stripe. We email you within one business day with what we need to start.</small>'),
]
for old, new in swaps:
    if s.count(old) == 1: s = s.replace(old, new)
    elif new not in s: sys.exit(f"could not find expected small print: {old[:60]}")

old_note = ("  1. Stripe: every link with data-stripe=\"audit\" currently opens an order email.\n"
            "     Replace its href with the real Stripe Payment Link (3 links).\n")
if old_note in s:
    s = s.replace(old_note, "  1. Stripe: the three data-stripe=\"audit\" buttons point at the live Payment Link.\n")
wr("index.html", s)
print(f"index.html: 3 buttons -> {LINK}")

r = rd("README.md")
old = ("- Stripe Payment Links on the three `data-stripe=\"audit\"` buttons (they open an email until then).\n"
       "  Their `<small>` text says a card invoice is sent by email, so adjust that wording at the same time.\n")
if old in r:
    wr("README.md", r.replace(old, "- (Stripe is wired: the three `data-stripe=\"audit\"` buttons use the live Payment Link. "
                                   "To change it, run `python tools/stripe.py <new link>`.)\n"))
    print("README updated")
print("next: python tools/check.py --fix, then commit and push")
