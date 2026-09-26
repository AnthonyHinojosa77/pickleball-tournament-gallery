# Real Estate Pickleball Tournament gallery

A standalone HTML5/CSS/JavaScript gallery for the September 19, 2026 tournament at Corpus Christi Athletic Club. No framework, server, database, remotely loaded code or runtime installation is required. The MIT-licensed PhotoSwipe 5.4.4 viewer is bundled locally.

Production: https://anthonyhinojosa77.github.io/pickleball-tournament-gallery/

The gallery contains 52 full-size current JPEG exports (including five 4K action frames), 10 vertical drone films, lightweight responsive WebP previews, a fullscreen keyboard/touch photo viewer, individual downloads and two ZIP downloads. The drone films have an AAC silence track because the camera footage contained no recorded audio.

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

`scripts/validate_gallery.py` checks media hashes, dimensions, color profiles, video formats, archive integrity and hosting limits. For presentation-only changes, `scripts/validate_presentation.py` requires unchanged media and verifies local references, counts, JavaScript syntax and hosting size. `scripts/test_lightbox.cjs` checks responsive sources and PhotoSwipe zoom calculations for all 52 photos at four viewport widths. Browser review separately checks layout, zoom, panning, navigation and original download targets. These checks do not emulate physical iPhone gestures.

The site uses the supplied tournament artwork with a white, pink, green and yellow palette, native video controls, alt text, keyboard navigation, reduced-motion support and lazy-loaded previews. PhotoSwipe supports pinch, double-tap, drag, keyboard navigation and explicit zoom buttons. The viewer requests the native JPEG when zoom requires more detail; Open original and Download JPEG remain available.

For branding or viewer updates that preserve all media and archives:

```sh
python3 scripts/render_site.py
python3 scripts/deploy_presentation.py
```

This validates and publishes the existing Pages site without rebuilding or uploading the large ZIP archives. The production URL and existing QR codes remain valid.

GitHub Pages serves static public content. Its published site limit is 1 GB, and its soft bandwidth limit is 100 GB per month. High traffic with large video downloads may call for moving the media to object storage.

References: [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits), [GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases), [python-qrcode](https://pypi.org/project/qrcode/).

## September 26 color correction

The earlier flat grade has been replaced. The RAW development now explicitly uses the embedded DNG color profile, camera tone curve and HueSatMap, scene-specific exposure and automatic chroma noise reduction. Full-resolution JPEGs and smaller color-managed WebP previews are separate. Versioned media paths prevent the old grade from being reused from browser cache. Highlights clipped in the original sensor capture and capture softness cannot be reconstructed by conventional processing.
