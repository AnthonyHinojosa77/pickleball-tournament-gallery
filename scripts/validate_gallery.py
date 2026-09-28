#!/usr/bin/env python3
"""Validate the complete static site, media hashes, video formats and ZIP contents."""
import hashlib, json, subprocess, zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''): h.update(block)
    return h.hexdigest()

class Document(HTMLParser):
    def __init__(self): super().__init__(); self.tags = []; self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs); self.tags.append((tag, attrs))
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, 'Duplicate element ID'
            self.ids.add(attrs['id'])

def main():
    manifest = json.loads((DOCS/'media-manifest.json').read_text())
    cfg = json.loads((ROOT/'config.json').read_text()); photos_n, films_n = cfg['expected_photos'], cfg['expected_videos']
    build = json.loads((ROOT/'artifacts/build.json').read_text())
    source = (DOCS/'index.html').read_text()
    assert '@@' not in source and '/Users/' not in source
    doc = Document(); doc.feed(source)
    local_links = 0
    for tag, attrs in doc.tags:
        for name in ['href', 'src', 'poster']:
            value = attrs.get(name)
            if not value: continue
            parsed = urlparse(value)
            if parsed.scheme: assert parsed.scheme == 'https'; continue
            if parsed.path:
                path = (DOCS/unquote(parsed.path)).resolve()
                assert path.is_relative_to(DOCS.resolve()) and path.is_file(), value
                local_links += 1
            if parsed.fragment: assert parsed.fragment in doc.ids, value
        if tag == 'img': assert 'alt' in attrs
        if tag == 'video': assert all(k in attrs for k in ['controls', 'playsinline', 'poster']) and attrs['preload'] == 'none'
    assert len([t for t,a in doc.tags if t == 'video']) == films_n
    assert len([a for t,a in doc.tags if 'data-photo-index' in a]) == photos_n
    assert len(manifest['photos']) == photos_n and len(manifest['videos']) == films_n
    for p in manifest['photos']:
        path = ROOT/'artifacts/photos'/p['filename'] if urlparse(p['full']).scheme else DOCS/p['full']
        assert sha(path) == p['sha256']
        with Image.open(path) as im:
            im.load(); assert im.size == (p['width'],p['height']) and im.mode == 'RGB'
            assert im.info.get('icc_profile'), f'Missing sRGB profile: {path}'
        with Image.open(DOCS/p['web']) as im:
            im.load(); assert max(im.size) == 2048 and im.size == (p['web_width'],p['web_height']) and im.info.get('icc_profile'), f"Bad web-size file: {p['web']}"
            assert (DOCS/p['web']).stat().st_size == p['web_bytes']
        assert p['section'] in {'group','courts','dj','sponsors'}
        for size in [480,960,2048]:
            with Image.open(DOCS/Path(p['preview']).with_name(f'photo-{p["id"]:02d}-{size}.webp')) as im:
                im.load(); assert im.width <= size and im.height <= size*2
    for v in manifest['videos']:
        path = DOCS/v['file']; assert sha(path) == v['sha256']
        data = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
        video = next(s for s in data['streams'] if s['codec_type']=='video')
        assert (video['width'],video['height']) == (v['width'],v['height']) and {v['width'],v['height']} == {1920,1080}
        assert video['codec_name']=='h264' and video['pix_fmt']=='yuv420p'
        if urlparse(v['download']).scheme:
            original = ROOT/'artifacts/films'/Path(v['download']).name
            assert sha(original) == v['download_sha256'] and original.stat().st_size < 2*2**30, 'GitHub release asset limit'
            full = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(original)]))
            assert abs(float(full['format']['duration'])-float(data['format']['duration'])) < 0.2, 'Download must match the page film'
        else:
            assert v['download'] == v['file'] and v['download_sha256'] == v['sha256']
        with Image.open(DOCS/v['poster']) as im: im.load(); assert (im.width>im.height) == (v['width']>v['height'])
    for path, count, digest in [(ROOT/'artifacts/pickleball-photos.zip',photos_n,build['photos_zip_sha256']), (ROOT/'artifacts/pickleball-complete-gallery.zip',photos_n+films_n,build['complete_zip_sha256'])]:
        assert sha(path) == digest
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None and len(z.namelist())==count
            assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    files = [p for p in DOCS.rglob('*') if p.is_file()]
    assert all(p.stat().st_size < 100*2**20 for p in files), 'GitHub per-file limit exceeded'
    assert sum(p.stat().st_size for p in files) < 1_000_000_000, 'GitHub Pages site limit exceeded'
    for path, _, _ in [(ROOT/'artifacts/pickleball-photos.zip',0,0),(ROOT/'artifacts/pickleball-complete-gallery.zip',0,0)]: assert path.stat().st_size < 2*2**30, 'GitHub release asset limit'
    subprocess.run(['node','--check',str(DOCS/'app.js')],check=True)
    subprocess.run(['node',str(ROOT/'scripts/test_lightbox.cjs')],check=True)
    result = {'passed':True,'photos':photos_n,'videos':films_n,'checked_local_references':local_links,'published_files':len(files),'published_bytes':sum(p.stat().st_size for p in files),'zip_integrity':'passed','media_sha256':'passed','lightbox_logic':'passed','browser_visual_testing':'not performed'}
    (ROOT/'validation.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__': main()
