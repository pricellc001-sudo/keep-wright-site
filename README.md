# keep-wright.com

Static site for Keep-Wright, served by GitHub Pages from the `main` branch of this repo.
Custom domain via the `CNAME` file; DNS lives at Squarespace; HTTPS is enforced in the repo's Pages settings.

## Layout

| Path | What it is |
|---|---|
| `index.html` | The one-page site: hero, problem, what we set up, who it's for, calculator, pricing, how it works, contact, policy summaries |
| `terms.html`, `privacy.html`, `refund.html` | Full policy pages, each with a version line and effective date |
| `404.html` | Served by GitHub Pages for any missing URL (uses absolute asset paths for that reason) |
| `assets/` | Scene photos in AVIF, WebP and JPEG at two widths each; share card; self-hosted Archivo font |
| `favicon.svg`, `favicon.ico`, `apple-touch-icon.png` | Icons. Regenerate all three together if the mark changes |
| `robots.txt`, `sitemap.xml` | Crawl hints. The sitemap lists the four indexable pages |
| `.well-known/security.txt` | Security contact (RFC 9116). Has an `Expires` date; renew it yearly |
| `CREDITS.txt` | Photo and font licences |
| `tools/check.py` | Consistency check, see below |

There is no build step. Pages are plain HTML, each with its own inline CSS. The header, footer and policy links
are copied into every page, which is why the check script compares them.

## Editing workflow

1. Edit the HTML. Keep line endings LF (`.gitattributes` enforces this on commit).
2. Run the check and let it repair what it can:

       python tools/check.py --fix

   It verifies the shared header and footer match on every page, recomputes the Content Security Policy
   hash for the inline script in `index.html` (editing that script without this step breaks the page),
   refreshes sitemap dates from git, and confirms every referenced asset exists.
3. Commit and push to `main`. GitHub Pages rebuilds in about a minute.

`main` is protected: no force-pushes, no deletion. Normal pushes are fine.

## Content Security Policy

Every page carries a CSP `<meta>` tag because GitHub Pages cannot send headers.
`index.html` allows exactly one inline script, identified by SHA-256 hash. The policy pages allow no script at all.
Inline event handler attributes (`onclick=` and friends) are blocked; attach handlers inside the script instead.
Images may come from the site or `data:` URLs (the film-grain canvas). Nothing loads from third parties.

## Photos

Each scene has a large and a small JPEG, and matching `.avif` and `.webp` files produced from the JPEGs.
To replace a photo, drop in the two JPEGs and regenerate the variants with Pillow (quality 50 AVIF, 72 WebP),
then update the `<picture>` block and, for the hero, the `<link rel="preload">`.

## Still to swap in

- Stripe Payment Links on the three `data-stripe="audit"` buttons (they open an email until then).
  Their `<small>` text says a card invoice is sent by email, so adjust that wording at the same time.
- Postal address: the `[POSTAL ADDRESS]` comments in `index.html` and `privacy.html` mark where it goes.
- `security.txt` `Expires` date, once a year.

## Policies

Terms and privacy are versioned (`Version N, effective <date>`). Bump the version and date on any change
that affects what a customer agreed to, and keep the work-already-agreed clause in mind: old orders stay under the
terms in force when they were placed.
