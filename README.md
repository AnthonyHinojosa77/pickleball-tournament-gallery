# Real Estate Pickleball Tournament gallery

A standalone HTML5/CSS/JavaScript gallery for the September 19, 2026 tournament at Corpus Christi Athletic Club. No framework, server, database, remotely loaded code or runtime installation is required. The MIT-licensed PhotoSwipe 5.4.4 viewer is bundled locally.

Production: https://anthonyhinojosa77.github.io/pickleball-tournament-gallery/

The gallery contains the September 19 shoot: 41 RAW-developed JPEGs, a color-graded recap film and all 7 drone clips, trimmed and graded. It also has lightweight responsive WebP previews, a fullscreen keyboard/touch photo viewer, individual downloads and two ZIP downloads. Films play on the page as 1080p H.264; the recap also downloads in 4K. The camera recorded no audio; the recap carries “Enter the Party” by Kevin MacLeod (incompetech.com), licensed under CC BY 4.0 and credited on the page and in the file metadata.

## Files and hosting

- `docs/` is the complete static website served by GitHub Pages from `main`.
- The release asset `pickleball-photos.zip` contains all 41 finished gallery JPEGs.
- The GitHub release `tournament-2026-09-19-redeveloped` hosts both ZIPs, all full-size JPEGs and the 4K recap (`pickleball-film-01-4k.mp4`). `pickleball-complete-gallery.zip` contains the 41 JPEGs plus the recap and the 7 clips in 1080p. Keeping full-size media in the release keeps the Pages site below its size limit.
- The untouched 4K camera masters and RAW photos remain in the original Google Drive upload; they are not part of the public gallery or its ZIPs.
- Full-size photo downloads are the finished deliverables: 41 RAW-developed photos (6,138 × 3,450 pixels before per-photo crops). They are not RAW files.

## Rebuild and deploy

Prerequisites: Python 3.11+, FFmpeg/FFprobe, Node.js (validation only), Git and an authenticated GitHub CLI account with permission to manage the repository and GitHub Pages.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_gallery.py --delivery /path/to/Automated_Delivery
.venv/bin/python scripts/deploy.py
```

The builder reads the media pipeline's `_Pipeline/photos.json`, optional `action-stills.json` and `reels.json` (each film record gives the web `output` and the 4K `download`). It copies the finished assets without changing the source media, creates previews/posters and checks ZIP integrity. The expected photo and film counts come from `config.json`. The scripts and template are editable for future events.

`deploy.py` validates the finished site, creates or updates the configured public repository, uploads both ZIPs as release assets, enables GitHub Pages, waits for publication and verifies the live page and media downloads. It then generates SVG and PNG QR codes beside `platform-posting-copy.txt` in the delivery directory and adds the live gallery URL to that copy. It saves a local `deployment.json` receipt. It never posts captions or messages to social accounts.

If only regenerating the QR code:

```sh
.venv/bin/python scripts/generate_qr.py --url https://anthonyhinojosa77.github.io/pickleball-tournament-gallery/ --output /path/to/Automated_Delivery
```

For a local preview, run `python3 -m http.server 8765 --bind 127.0.0.1 --directory docs`, then open http://127.0.0.1:8765/.

## Verification

`scripts/validate_gallery.py` checks media hashes, dimensions, color profiles, video formats, archive integrity and hosting limits. For presentation-only changes, `scripts/validate_presentation.py` requires unchanged media and verifies local references, counts, JavaScript syntax and hosting size. `scripts/test_lightbox.cjs` checks responsive sources and PhotoSwipe zoom calculations for every photo at four viewport widths. Browser review separately checks layout, zoom, panning, navigation and original download targets. These checks do not emulate physical iPhone gestures.

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

## Selective finishing and tournament emblem

The September 26 finishing pass adds defined subject-region lift for the group, DJ and host photographs, stronger luminance contrast, restrained adaptive contrast, controlled ceiling highlights, slight green-cast reduction and output sharpening. It is a deterministic conventional edit; it does not generate detail or change the photographed scene. The existing profile-aware full-resolution JPEGs were used as the preserved baseline for this pass. Future RAW development applies the same finishing function once after its embedded-profile conversion. Native dimensions are retained.

The attached house-and-paddle emblem appears in the header and footer. Versioned `selective-20260926` media and a separate `tournament-2026-09-19-selective-finish` release ensure previews, originals and ZIP downloads all use this pass. Prior media remains in Git history and the previous release. The review includes side-by-side proofs; image hashes only verify delivery, not artistic quality.


RAW detail revision (26 September 2026): camera stills are freshly redeveloped from 47 DNGs with source/export checksums, lossless TIFF intermediates and tuned capture sharpening. Camera JPEGs use native dimensions, sRGB, quality 96 and 4:4:4 sampling. Five video freeze-frames are identified separately. `photo_asset_base` stores native JPEGs in the versioned GitHub release; the builder stages upload links under `artifacts/photos`, and deployment publishes verified assets before changing the live page. `RAW_SOURCE_AUDIT.csv` accompanies the release.

## September 27 redevelopment

The September 26 exports smeared faces and fabric at full zoom (heavy noise reduction and halo sharpening). All 48 DNGs from the day were redeveloped from scratch with `scripts/raw/develop.sh`: RawTherapee 5.10 with AMaZE demosaicing, capture deconvolution, light noise reduction, the embedded DNG camera profile, gentle local contrast, dehaze, shadow lift and skin-protected vibrance (`scripts/raw/finish.pp3`). `scripts/raw/finalize.py` then area-downscales the 16-bit result to 75% (6,138 × 3,450), applies output sharpening and writes quality-95, 4:4:4 sRGB JPEGs with camera EXIF (GPS removed). The drone's 50 MP quad-Bayer sensor does not resolve 8,192 px of real detail, so the 75% size looks crisp when zoomed.

After the develop, every frame was reviewed individually at full size. `scripts/raw/adjustments.json` records the per-photo decisions: highlight recovery for blown ceilings and the sponsor banner, lifted exposure for the dim DJ-booth frames, crops that remove empty ceiling or an obstructing edge, and an automatic correction of the slight warm-magenta cast measured on neutral walls and court surround. Seven sponsor-banner frames were held back from the gallery because of motion blur, missed focus or camera shake; sharper frames of the same banner are included, and the originals remain in Google Drive.

The gallery holds only what was shot: the five video freeze-frames were removed, the previously omitted photo `DJI_20260919113628_0098_D` was added, and the ten cropped vertical 60-second reels were replaced by a recap film plus all seven clips in their original framing. `scripts/video/edit.py` cuts and grades them from the second-by-second edit decisions in `scripts/video/edl.json` (dead moments such as empty-wall pans, whip pans and the landing removed; same grade intent as the photos). Photos and films are numbered in shooting order, with the group photo first. `config.json` records the expected counts, which the builder and validator enforce.

### Publishing without the GitHub CLI

Cloud sessions that cannot manage releases publish through GitHub Actions instead. `python3 scripts/stage_release.py prepare` copies the full-size JPEGs into `release-staging/`, splits the 4K recap into parts under 100 MB and records the checksum of every release asset. Pushing it runs `.github/workflows/stage-release.yml`, which reassembles the files, rebuilds the ZIPs, rejects any checksum mismatch and uploads everything to a draft release. Merging the gallery update into `main` runs `publish-release.yml`, which publishes that draft as the site goes live. Remove `release-staging/` before merging, and squash-merge so the staged copies stay out of `main`'s history.
