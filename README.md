# Real Estate Pickleball Tournament gallery

A standalone HTML5/CSS/JavaScript gallery for the September 19, 2026 tournament at Corpus Christi Athletic Club. No framework, server, database, third-party scripts or runtime installation is required.

Production: https://anthonyhinojosa77.github.io/pickleball-tournament-gallery/

The gallery contains 52 full-size finished JPEGs (including five 4K action frames), 10 vertical drone films, lightweight responsive WebP previews, a fullscreen keyboard/touch photo viewer, individual downloads and two ZIP downloads. The drone films have an AAC silence track because the camera footage contained no recorded audio.

## Files and hosting

- `docs/` is the complete static website served by GitHub Pages from `main`.
- The release asset `pickleball-photos.zip` contains all 52 finished gallery JPEGs.
- The GitHub release `tournament-2026-09-19-color-corrected` hosts `pickleball-complete-gallery.zip`, containing the same 52 JPEGs plus all 10 reels. This avoids GitHub's 100 MiB repository file limit.
- The untouched 4K camera masters and RAW photos remain in the original OneDrive delivery; they are not part of the public gallery or its ZIPs.
- Full-size downloads preserve the finished deliverables: 47 RAW-developed photos at 8,184 × 4,600 pixels and 3,840 × 2,160 action frames. They are not RAW files.

## Rebuild and deploy

Prerequisites: Python 3.11+, FFmpeg/FFprobe, Node.js (validation only), Git and an authenticated GitHub CLI account with permission to manage the repository and GitHub Pages.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_gallery.py --delivery /path/to/Automated_Delivery
.venv/bin/python scripts/deploy.py
```

The builder reads the media pipeline's `_Pipeline/photos.json`, `action-stills.json` and `reels.json`. It copies the finished assets without changing the source media, creates previews/posters and checks ZIP integrity. This event snapshot expects 52 photos and 10 reels. The scripts and template are editable for future events.

`deploy.py` validates the finished site, creates or updates the configured public repository, uploads both ZIPs as release assets, enables GitHub Pages, waits for publication and verifies the live page and media downloads. It then generates SVG and PNG QR codes beside `platform-posting-copy.txt` in the delivery directory and adds the live gallery URL to that copy. It saves a local `deployment.json` receipt. It never posts captions or messages to social accounts.

If only regenerating the QR code:

```sh
.venv/bin/python scripts/generate_qr.py --url https://anthonyhinojosa77.github.io/pickleball-tournament-gallery/ --output /path/to/Automated_Delivery
```

For a local preview, run `python3 -m http.server 8765 --bind 127.0.0.1 --directory docs`, then open http://127.0.0.1:8765/.

## Verification

`scripts/validate_gallery.py` checks all local resource references, 52 photo hashes and dimensions, sRGB profiles, responsive previews, all 10 video hashes/formats/durations, poster dimensions, ZIP CRCs and file counts, hosting size limits and JavaScript syntax. `scripts/test_lightbox.cjs` tests navigation, wrapping, swipe, error/loading behavior, download targeting, focus restoration and exclusive video playback using event doubles. These are automated file and interaction-logic checks; they do not substitute for browser visual testing.

The site uses native video controls and a native modal dialog, provides alt text and keyboard controls, respects reduced-motion settings, lazy-loads photo previews, and does not preload video files. CSS layouts adapt at 430, 760, 1100 and 1900 pixels.

GitHub Pages serves static public content. Its published site limit is 1 GB, and its soft bandwidth limit is 100 GB per month. High traffic with large video downloads may call for moving the media to object storage.

References: [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits), [GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases), [python-qrcode](https://pypi.org/project/qrcode/).

## September 26 color correction

The earlier flat grade has been replaced. The RAW development now explicitly uses the embedded DNG color profile, camera tone curve and HueSatMap, scene-specific exposure and automatic chroma noise reduction. Full-resolution JPEGs and smaller color-managed WebP previews are separate. Versioned media paths prevent the old grade from being reused from browser cache. Highlights clipped in the original sensor capture and capture softness cannot be reconstructed by conventional processing.
